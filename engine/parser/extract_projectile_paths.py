"""Targeted extractor: recorder rocket/grenade projectile paths.

Scope: recorder ROCKET/GRENADE candidate kills (~4.3k events / ~2.3k demos
costed 2026-08-30). Candidates = recognized_frags rows with weapon_name in
ROCKET/ROCKET_SPLASH/GRENADE/GRENADE_SPLASH carrying a
DIRECT_ROCKET / AIR_ROCKET / AIR_GRENADE / PREDICTION_CANDIDATE / CLUTCH_*
label or highlight_score >= 12, skipping attributes.projectile_path cache
hits.

Evidence model (honest, deterministic — verified 2026-08-30):
  - The recorder's own fire_weapon events are ABSENT from the entity event
    stream (own player is playerstate). MISSILE entities are not exported
    by demo_parse either. What IS available:
      * missile_hit / missile_miss temp-entity events (impact pos + time);
      * recorder view snapshots (origin + yaw/pitch per server frame);
      * PLAYER entity samples for the victim (origin/vel per server frame).
  - Launch inference: QL rocket speed is 1000 ups, so
    fire_t ~= impact_t - dist(fire_origin, impact)/1000. We scan recorder
    snapshots in [impact_t-4000, impact_t], project a ray along the view
    angles of each, and pick the snapshot whose ray passes nearest the
    matched impact point (min perpendicular distance, lightly penalised by
    disagreement with the speed-derived fire time). Match quality is stored,
    never hidden.
  - ROCKETS: straight launch->impact path sampled at 25 ms for the cinematic
    camera cache.
  - GRENADES: ballistic sim — v0 = view_dir*700 + (0,0,200) toss, gravity
    800 u/s^2, 10 ms integration, bounce = velocity reflected off the brush
    plane returned by a BSP trace (engine/parser/bsp_geometry.py, imported
    read-only), then damped per-axis by restitution 0.65 xy / 0.45 z
    (PROVISIONAL constants — the Q3 feel, not decompiled values). Sim stops
    at the observed impact time; simulated end within 120 u of the observed
    impact pos => path_confidence CONFIRMED, else LIKELY (both kept, with
    the deviation stored).
  - DIRECT geometric check: impact pos vs victim entity sample at impact
    time against the player bbox (-15,-15,-24)..(15,15,32). Expansion
    needed <= 24 u => DIRECT_CONFIRMED, <= 48 u => DIRECT_LIKELY, else
    SPLASH. The DIRECT_ROCKET class keeps its MOD evidence; the geometry
    verdict is recorded alongside it.
  - AIR enrichment: victim air height + vertical velocity at impact
    (projectile_victim_air_height / projectile_victim_vertical_speed).
  - PREDICTION evidence: victim travel distance between launch and impact
    (victim_travel_during_flight). Fired-before-visible is left for the
    BSP visibility stage.

Persists: attribute summary on the kill row + full sampled path JSON into
recognition_projectile_paths(demo_name, server_time_ms, version, path).
Resumable via projectile_extracted(content_hash, version) like the sibling
extractors (extract_health_armor.py / extract_lg_engagements.py).

Usage: python -u engine/parser/extract_projectile_paths.py [--limit N] [--workers N]
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"

EXTRACTOR_VERSION = 1

ROCKET_WEAPONS = {"ROCKET", "ROCKET_SPLASH"}
GRENADE_WEAPONS = {"GRENADE", "GRENADE_SPLASH"}
CANDIDATE_LABELS = {"DIRECT_ROCKET", "AIR_ROCKET", "AIR_GRENADE",
                    "PREDICTION_CANDIDATE"}
MIN_SCORE = 12.0

WP_GRENADE, WP_ROCKET = 4, 5          # raw WP_* ids on missile temp entities

ROCKET_SPEED = 1000.0                 # ups (QL g_missileSpeed default for RL)
GRENADE_SPEED = 700.0                 # ups
GRENADE_TOSS_Z = 200.0                # upward toss added to muzzle velocity
GRAVITY = 800.0                       # u/s^2 (g_gravity default)
RESTITUTION_XY = 0.65                 # PROVISIONAL — Q3 grenade feel
RESTITUTION_Z = 0.45                  # PROVISIONAL — Q3 grenade feel
SIM_DT = 0.010                        # 10 ms integration step
SAMPLE_MS = 25                        # cinematic path cache sample step

LAUNCH_SEARCH_MS = 4000               # snapshots scanned before the impact
IMPACT_SEARCH_PRE_MS = 4000           # missile events accepted before kill
IMPACT_SEARCH_POST_MS = 500           # ... and just after (obituary lag)
TIME_PENALTY_U_PER_MS = 0.02          # launch score: perp_u + this * |dt_ms|

BBOX_MINS = (-15.0, -15.0, -24.0)     # bg_public.h playerMins
BBOX_MAXS = (15.0, 15.0, 32.0)        # bg_public.h playerMaxs
DIRECT_CONFIRM_U = 24.0
DIRECT_LIKELY_U = 48.0
GRENADE_CONFIRM_U = 120.0
VICTIM_SAMPLE_TOL_MS = 250


# ── geometry helpers (pure — unit-tested) ────────────────────────────────────

def angles_to_dir(yaw_deg: float, pitch_deg: float) -> tuple[float, float, float]:
    """Q3 view angles -> unit forward vector. Pitch positive = down."""
    if pitch_deg > 180.0:
        pitch_deg -= 360.0
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    cp = math.cos(pitch)
    return (cp * math.cos(yaw), cp * math.sin(yaw), -math.sin(pitch))


def ray_point_perp(origin, direction, point) -> tuple[float, float]:
    """(perpendicular distance, along-ray distance) of point vs forward ray.

    Points behind the ray origin get an inf perpendicular distance.
    Partial demo delta rows can carry None coordinates - treat as unusable.
    """
    if any(v is None for v in (*point[:3], *origin[:3])):
        return (math.inf, 0.0)
    dx = point[0] - origin[0]
    dy = point[1] - origin[1]
    dz = point[2] - origin[2]
    t = dx * direction[0] + dy * direction[1] + dz * direction[2]
    if t <= 0.0:
        return (math.inf, t)
    px = dx - t * direction[0]
    py = dy - t * direction[1]
    pz = dz - t * direction[2]
    return (math.sqrt(px * px + py * py + pz * pz), t)


def match_launch_snapshot(snaps: list[dict], impact_pos, impact_t: int,
                          speed: float) -> dict | None:
    """Pick the recorder snapshot whose view ray best explains the impact.

    snaps: [{t, origin(x,y,z), yaw, pitch}] within the search window.
    Score = perpendicular ray distance + TIME_PENALTY * |snap_t - fire_t|,
    where fire_t = impact_t - dist(origin, impact)/speed. Returns the best
    snapshot dict extended with match-quality fields, or None.
    """
    best = None
    for sn in snaps:
        d = angles_to_dir(sn["yaw"], sn["pitch"])
        perp, along = ray_point_perp(sn["origin"], d, impact_pos)
        if not math.isfinite(perp):
            continue
        expected_fire_t = impact_t - (along / speed) * 1000.0
        time_err = abs(sn["t"] - expected_fire_t)
        score = perp + TIME_PENALTY_U_PER_MS * time_err
        if best is None or score < best["score"]:
            best = dict(sn, dir=d, perp=perp, along=along,
                        time_err_ms=time_err, score=score)
    return best


def sample_rocket_path(launch_pos, impact_pos, launch_t: int,
                       impact_t: int) -> list[list[float]]:
    """Straight-line path sampled every SAMPLE_MS: [[t_rel_ms, x, y, z], ...]."""
    flight = max(impact_t - launch_t, SAMPLE_MS)
    pts: list[list[float]] = []
    t = 0
    while t < flight:
        f = t / flight
        pts.append([t,
                    round(launch_pos[0] + f * (impact_pos[0] - launch_pos[0]), 1),
                    round(launch_pos[1] + f * (impact_pos[1] - launch_pos[1]), 1),
                    round(launch_pos[2] + f * (impact_pos[2] - launch_pos[2]), 1)])
        t += SAMPLE_MS
    pts.append([flight, round(impact_pos[0], 1), round(impact_pos[1], 1),
                round(impact_pos[2], 1)])
    return pts


def reflect_bounce(vel, normal) -> tuple[float, float, float]:
    """Reflect velocity off a plane normal, then damp per-axis.

    Restitution constants are PROVISIONAL (0.65 xy / 0.45 z — the Q3 feel).
    """
    dot = vel[0] * normal[0] + vel[1] * normal[1] + vel[2] * normal[2]
    rx = vel[0] - 2.0 * dot * normal[0]
    ry = vel[1] - 2.0 * dot * normal[1]
    rz = vel[2] - 2.0 * dot * normal[2]
    return (rx * RESTITUTION_XY, ry * RESTITUTION_XY, rz * RESTITUTION_Z)


def simulate_grenade(origin, view_dir, flight_ms: int,
                     tracer=None) -> dict:
    """Integrate a grenade from origin along view_dir for flight_ms.

    tracer(p1, p2) -> (fraction, normal) | None — first solid hit on the
    segment. None tracer = gravity-only (no bounce), used when the BSP is
    unavailable. Returns {points (25ms samples), bounces, end, bounce_count}.
    """
    vx = view_dir[0] * GRENADE_SPEED
    vy = view_dir[1] * GRENADE_SPEED
    vz = view_dir[2] * GRENADE_SPEED + GRENADE_TOSS_Z
    px, py, pz = origin
    t_ms = 0.0
    points: list[list[float]] = [[0, round(px, 1), round(py, 1), round(pz, 1)]]
    bounces: list[list[float]] = []
    next_sample = SAMPLE_MS
    while t_ms < flight_ms:
        dt = min(SIM_DT, (flight_ms - t_ms) / 1000.0)
        vz -= GRAVITY * dt
        nx, ny, nz = px + vx * dt, py + vy * dt, pz + vz * dt
        if tracer is not None:
            hit = tracer((px, py, pz), (nx, ny, nz))
            if hit is not None:
                frac, normal = hit
                hx = px + (nx - px) * frac
                hy = py + (ny - py) * frac
                hz = pz + (nz - pz) * frac
                vx, vy, vz = reflect_bounce((vx, vy, vz), normal)
                bounces.append([round(t_ms + dt * frac * 1000.0, 1),
                                round(hx, 1), round(hy, 1), round(hz, 1)])
                # nudge off the plane to avoid re-hitting it next step
                px = hx + normal[0] * 0.25
                py = hy + normal[1] * 0.25
                pz = hz + normal[2] * 0.25
                t_ms += dt * 1000.0
                continue
        px, py, pz = nx, ny, nz
        t_ms += dt * 1000.0
        if t_ms >= next_sample:
            points.append([round(t_ms, 1), round(px, 1), round(py, 1),
                           round(pz, 1)])
            next_sample += SAMPLE_MS
    points.append([round(t_ms, 1), round(px, 1), round(py, 1), round(pz, 1)])
    return {"points": points, "bounces": bounces, "end": (px, py, pz),
            "bounce_count": len(bounces)}


def bbox_expansion_needed(point, center) -> float:
    """How far the player bbox at center must expand (per-axis) to contain
    point. 0.0 = inside the bbox."""
    worst = 0.0
    for a in range(3):
        rel = point[a] - center[a]
        excess = max(BBOX_MINS[a] - rel, rel - BBOX_MAXS[a], 0.0)
        worst = max(worst, excess)
    return worst


def direct_verdict(expansion: float) -> str:
    if expansion <= DIRECT_CONFIRM_U:
        return "DIRECT_CONFIRMED"
    if expansion <= DIRECT_LIKELY_U:
        return "DIRECT_LIKELY"
    return "SPLASH"


# ── BSP trace with plane normal ──────────────────────────────────────────────

def make_tracer(bsp):
    """Wrap a loaded BspMap into tracer(p1, p2) -> (fraction, normal) | None.

    Walks worldspawn CONTENTS_SOLID brushes like bsp_geometry.line_blocked
    but keeps the entering plane of the nearest hit. Bezier patches are
    ignored for bounce (brush-only — evidence-grade, matches the module's
    own approximation notes).
    """
    from bsp_geometry import CONTENTS_SOLID, _EPS  # read-only import

    lo, hi = bsp.world_brush_range

    def _brush_enter(brush_idx, p1, p2):
        first, count, contents = bsp.brushes[brush_idx]
        if not (contents & CONTENTS_SOLID):
            return None
        enter_f, leave_f = -1.0, 2.0
        enter_plane = None
        for si in range(first, first + count):
            plane = bsp.planes[bsp.brushsides[si]]
            nx, ny, nz, dist = plane
            d1 = p1[0] * nx + p1[1] * ny + p1[2] * nz - dist
            d2 = p2[0] * nx + p2[1] * ny + p2[2] * nz - dist
            if d1 > _EPS and d2 > _EPS:
                return None
            if d1 <= _EPS and d2 <= _EPS:
                continue
            f = d1 / (d1 - d2)
            if d1 > d2:
                if f > enter_f:
                    enter_f, enter_plane = f, plane
            else:
                if f < leave_f:
                    leave_f = f
            if enter_f > leave_f:
                return None
        if enter_f <= leave_f and enter_plane is not None and enter_f >= 0.0:
            return (max(enter_f, 0.0), enter_plane[:3])
        return None

    def tracer(p1, p2):
        best = None
        checked: set[int] = set()
        stack = [(0, tuple(p1), tuple(p2))]
        while stack:
            node_idx, a, b = stack.pop()
            while node_idx >= 0:
                plane_idx, c0, c1 = bsp.nodes[node_idx]
                nx, ny, nz, dist = bsp.planes[plane_idx]
                d1 = a[0] * nx + a[1] * ny + a[2] * nz - dist
                d2 = b[0] * nx + b[1] * ny + b[2] * nz - dist
                if d1 >= -_EPS and d2 >= -_EPS:
                    node_idx = c0
                elif d1 < _EPS and d2 < _EPS:
                    node_idx = c1
                else:
                    f = d1 / (d1 - d2)
                    mid = (a[0] + f * (b[0] - a[0]),
                           a[1] + f * (b[1] - a[1]),
                           a[2] + f * (b[2] - a[2]))
                    if d1 >= 0:
                        stack.append((c1, mid, b))
                        node_idx = c0
                        b = mid
                    else:
                        stack.append((c0, mid, b))
                        node_idx = c1
                        b = mid
            lb_first, lb_num = bsp.leafs[-(node_idx + 1)]
            for i in range(lb_first, lb_first + lb_num):
                br = bsp.leafbrushes[i]
                if br in checked or not (lo <= br < hi):
                    continue
                checked.add(br)
                hit = _brush_enter(br, p1, p2)
                if hit is not None and (best is None or hit[0] < best[0]):
                    best = hit
        return best

    return tracer


# ── candidate selection ──────────────────────────────────────────────────────

def candidate_map() -> dict[str, list[tuple[int, str, int]]]:
    """demo_name -> [(server_time_ms, kind, victim_client), ...]."""
    c = sqlite3.connect(f"file:{RECOG_DB}?mode=ro", uri=True)
    out: dict[str, list[tuple[int, str, int]]] = {}
    for demo, t, wn, cl, hs, attrs, vc in c.execute(
            "SELECT demo_name, server_time_ms, weapon_name, classes,"
            " highlight_score, attributes, victim_client FROM recognized_frags"
            " WHERE weapon_name IN"
            " ('ROCKET','ROCKET_SPLASH','GRENADE','GRENADE_SPLASH')"):
        a = json.loads(attrs or "{}")
        if a.get("projectile_path") is not None:
            continue    # cache hit
        names = {x["name"] if isinstance(x, dict) else x
                 for x in json.loads(cl or "[]")}
        if not ((names & CANDIDATE_LABELS)
                or any(n.startswith("CLUTCH_") for n in names)
                or (hs or 0) >= MIN_SCORE):
            continue
        kind = "rocket" if wn in ROCKET_WEAPONS else "grenade"
        out.setdefault(demo, []).append((t, kind, vc))
    c.close()
    return out


# ── per-demo analysis (pure on a parsed dict — unit-tested) ─────────────────

def _snap_time(s: dict) -> int | None:
    for k in ("server_time", "server_time_ms", "serverTime", "t_ms", "t"):
        if s.get(k) is not None:
            return int(s[k])
    return None


def analyze_kills(parsed: dict, kills: list[tuple[int, str, int]],
                  recorder_client: int, tracer=None) -> dict[int, dict]:
    """Core model on one parsed demo. Returns kill_t -> result payload."""
    events = parsed.get("events", [])
    impacts = []
    for e in events:
        if e.get("type") not in ("missile_hit", "missile_miss"):
            continue
        if e.get("pos_x") is None:
            continue
        impacts.append((e["server_time_ms"],
                        (e["pos_x"], e["pos_y"], e["pos_z"]),
                        e.get("weapon"), e["type"]))
    impacts.sort(key=lambda x: x[0])  # ts only; tied rows may carry None fields

    snaps = []
    for sn in parsed.get("snapshots", []):
        t = _snap_time(sn)
        if t is None or sn.get("origin_x") is None:
            continue
        cn = sn.get("client_num")
        if cn is not None and cn != recorder_client:
            continue
        if sn.get("angle_yaw") is None or sn.get("angle_pitch") is None:
            continue
        snaps.append({"t": t,
                      "origin": (sn["origin_x"], sn["origin_y"],
                                 sn["origin_z"]),
                      "yaw": sn["angle_yaw"], "pitch": sn["angle_pitch"]})
    snaps.sort(key=lambda s: s["t"])

    victim_samples: dict[int, list] = {}
    for en in parsed.get("entities", []):
        cn = en.get("client_num")
        if cn is None or en.get("origin_x") is None:
            continue
        victim_samples.setdefault(cn, []).append(en)
    for lst in victim_samples.values():
        lst.sort(key=lambda e: e["server_time_ms"])

    def victim_at(vc: int, t: int) -> dict | None:
        best, best_dt = None, VICTIM_SAMPLE_TOL_MS + 1
        for en in victim_samples.get(vc, []):
            dt = abs(en["server_time_ms"] - t)
            if dt < best_dt:
                best, best_dt = en, dt
        return best

    out: dict[int, dict] = {}
    for kill_t, kind, vc in kills:
        wp = WP_ROCKET if kind == "rocket" else WP_GRENADE
        speed = ROCKET_SPEED if kind == "rocket" else GRENADE_SPEED
        summary: dict = {"projectile_path": 1, "projectile_kind": kind}
        res: dict = {"summary": summary, "path": None, "geometry": None}
        out[kill_t] = res

        # 1. impact = missile event nearest the kill (weapon-filtered)
        cands = [im for im in impacts
                 if kill_t - IMPACT_SEARCH_PRE_MS <= im[0]
                 <= kill_t + IMPACT_SEARCH_POST_MS
                 and (im[2] is None or im[2] == wp)]
        if not cands:
            summary["projectile_status"] = "NO_IMPACT_EVENT"
            continue
        impact_t, impact_pos, _, impact_ev = min(
            cands, key=lambda im: abs(im[0] - kill_t))

        # 2. launch = best-matching recorder view snapshot
        win = [s for s in snaps
               if impact_t - LAUNCH_SEARCH_MS <= s["t"] <= impact_t]
        best = match_launch_snapshot(win, impact_pos, impact_t, speed)
        if best is None:
            summary["projectile_status"] = "NO_LAUNCH_SNAPSHOT"
            continue
        launch_t, launch_pos = best["t"], best["origin"]
        flight_ms = max(int(impact_t - launch_t), SAMPLE_MS)
        dist = math.dist(launch_pos, impact_pos)

        summary.update({
            "projectile_status": "OK",
            "projectile_launch_t": launch_t,
            "projectile_impact_t": impact_t,
            "projectile_flight_ms": flight_ms,
            "projectile_distance": round(dist, 1),
            "projectile_impact_event": impact_ev,
            "projectile_launch_match_perp": round(best["perp"], 1),
            "projectile_launch_time_err_ms": round(best["time_err_ms"], 1),
        })

        # 3. path
        if kind == "rocket":
            points = sample_rocket_path(launch_pos, impact_pos,
                                        launch_t, impact_t)
            path = {"kind": kind, "points": points, "bounces": [],
                    "confidence": "CONFIRMED", "deviation_u": 0.0}
            summary["projectile_path_confidence"] = "CONFIRMED"
            summary["projectile_bounce_count"] = 0
        else:
            sim = simulate_grenade(launch_pos, best["dir"], flight_ms, tracer)
            deviation = math.dist(sim["end"], impact_pos)
            conf = ("CONFIRMED" if deviation <= GRENADE_CONFIRM_U
                    else "LIKELY")
            path = {"kind": kind, "points": sim["points"],
                    "bounces": sim["bounces"], "confidence": conf,
                    "deviation_u": round(deviation, 1)}
            summary["projectile_path_confidence"] = conf
            summary["projectile_deviation_u"] = round(deviation, 1)
            summary["projectile_bounce_count"] = sim["bounce_count"]
        path.update({"launch": {"t": launch_t,
                                "pos": [round(v, 1) for v in launch_pos],
                                "dir": [round(v, 4) for v in best["dir"]]},
                     "impact": {"t": impact_t,
                                "pos": [round(v, 1) for v in impact_pos]}})
        res["path"] = path

        # 4. DIRECT geometric check + AIR enrichment at impact
        v_imp = victim_at(vc, impact_t)
        if v_imp is not None:
            center = (v_imp["origin_x"], v_imp["origin_y"], v_imp["origin_z"])
            exp = bbox_expansion_needed(impact_pos, center)
            verdict = direct_verdict(exp)
            summary["projectile_direct_geometry"] = verdict
            summary["projectile_direct_expansion_u"] = round(exp, 1)
            res["geometry"] = {"verdict": verdict, "expansion_u": round(exp, 1)}
            if v_imp.get("vel_z") is not None:
                summary["projectile_victim_vertical_speed"] = round(
                    v_imp["vel_z"], 1)
            if v_imp.get("airborne") is not None:
                summary["projectile_victim_airborne"] = bool(
                    v_imp["airborne"])
            if tracer is not None:
                hit = tracer(center, (center[0], center[1],
                                      center[2] - 2048.0))
                if hit is not None:
                    summary["projectile_victim_air_height"] = round(
                        (hit[0] * 2048.0) + BBOX_MINS[2], 1)
        else:
            summary["projectile_direct_geometry"] = "NO_VICTIM_SAMPLE"

        # 5. PREDICTION evidence: victim travel during flight
        v_launch = victim_at(vc, launch_t)
        if v_imp is not None and v_launch is not None:
            travel = math.dist(
                (v_launch["origin_x"], v_launch["origin_y"],
                 v_launch["origin_z"]),
                (v_imp["origin_x"], v_imp["origin_y"], v_imp["origin_z"]))
            summary["victim_travel_during_flight"] = round(travel, 1)
    return out


def extract_one(demo_path: str, kills: list[tuple[int, str, int]],
                recorder_client: int, map_name: str | None) -> dict[int, dict]:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from demo_parse import DM73Parser
    parsed = DM73Parser(Path(demo_path)).parse()
    tracer = None
    if map_name and any(k == "grenade" for _, k, _ in kills):
        try:
            from bsp_geometry import load_map
            tracer = make_tracer(load_map(map_name))
        except Exception:   # noqa: BLE001 - BSP is optional evidence
            tracer = None
    return analyze_kills(parsed, kills, recorder_client, tracer)


# ── air-height enrichment via BSP would need ground trace; we reuse the
#    victim sample's airborne flag + cached victim_air_height attr instead.

def _merge_classes(classes_json: str | None, geometry: dict | None) -> str | None:
    """Record the geometry verdict on the DIRECT_ROCKET class, keeping the
    MOD evidence intact. Returns updated JSON or None if unchanged."""
    if not geometry:
        return None
    try:
        classes = json.loads(classes_json or "[]")
    except json.JSONDecodeError:
        return None
    changed = False
    for cl in classes:
        if isinstance(cl, dict) and cl.get("name") == "DIRECT_ROCKET":
            cl["geometry_verdict"] = geometry["verdict"]
            cl["geometry_expansion_u"] = geometry["expansion_u"]
            detail = cl.get("detail", "")
            marker = " | geometry:"
            if marker not in detail:
                cl["detail"] = (f"{detail}{marker} {geometry['verdict']}"
                                f" (expand {geometry['expansion_u']}u)")
            changed = True
    return json.dumps(classes) if changed else None


# ── driver ───────────────────────────────────────────────────────────────────

def run(limit: int | None = None, workers: int = 4) -> dict:
    conn = sqlite3.connect(RECOG_DB, timeout=60.0)
    conn.execute("PRAGMA busy_timeout=60000")   # LG extractor may hold writes
    conn.execute("CREATE TABLE IF NOT EXISTS projectile_extracted ("
                 " content_hash TEXT PRIMARY KEY, demo_name TEXT,"
                 " version INTEGER, events INTEGER, status TEXT,"
                 " extracted_at TEXT DEFAULT (datetime('now')))")
    conn.execute("CREATE TABLE IF NOT EXISTS recognition_projectile_paths ("
                 " demo_name TEXT, server_time_ms INTEGER, version INTEGER,"
                 " path TEXT, PRIMARY KEY (demo_name, server_time_ms))")
    conn.commit()

    fconn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    meta = {n: (p, dup or h, rc, mp) for n, p, h, dup, rc, mp in fconn.execute(
        "SELECT name, path, content_hash, duplicate_of, recorder_client,"
        " map_name FROM demos")}
    fconn.close()

    done = {r[0] for r in conn.execute(
        "SELECT content_hash FROM projectile_extracted WHERE version=? AND"
        " status='ok'", (EXTRACTOR_VERSION,))}
    cands = candidate_map()
    todo = [(d, *meta[d], ks) for d, ks in cands.items()
            if d in meta and meta[d][1] not in done]
    if limit:
        todo = todo[:limit]

    stats = {"eligible_events": sum(len(k) for k in cands.values()),
             "demos_to_open": len(todo), "events_updated": 0,
             "paths_written": 0, "failed": 0}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(extract_one, path, ks, rc, mp): (demo, h, ks)
                for demo, path, h, rc, mp, ks in todo}
        n = 0
        for fut in as_completed(futs):
            demo, h, ks = futs[fut]
            n += 1
            try:
                res = fut.result()
            except Exception as e:   # noqa: BLE001 - per-demo isolation
                conn.execute("INSERT OR REPLACE INTO projectile_extracted"
                             " VALUES (?,?,?,?,?,datetime('now'))",
                             (h, demo, EXTRACTOR_VERSION, 0,
                              f"fail: {type(e).__name__}"))
                conn.commit()
                stats["failed"] += 1
                continue
            for kt, payload in res.items():
                row = conn.execute(
                    "SELECT id, attributes, classes FROM recognized_frags"
                    " WHERE demo_name=? AND server_time_ms=?",
                    (demo, kt)).fetchone()
                if row is None:
                    continue
                a = json.loads(row[1] or "{}")
                a.update(payload["summary"])
                new_classes = _merge_classes(row[2], payload.get("geometry"))
                if new_classes is not None:
                    conn.execute("UPDATE recognized_frags SET attributes=?,"
                                 " classes=? WHERE id=?",
                                 (json.dumps(a), new_classes, row[0]))
                else:
                    conn.execute("UPDATE recognized_frags SET attributes=?"
                                 " WHERE id=?", (json.dumps(a), row[0]))
                if payload.get("path") is not None:
                    conn.execute("INSERT OR REPLACE INTO"
                                 " recognition_projectile_paths VALUES"
                                 " (?,?,?,?)",
                                 (demo, kt, EXTRACTOR_VERSION,
                                  json.dumps(payload["path"])))
                    stats["paths_written"] += 1
                stats["events_updated"] += 1
            conn.execute("INSERT OR REPLACE INTO projectile_extracted VALUES"
                         " (?,?,?,?, 'ok', datetime('now'))",
                         (h, demo, EXTRACTOR_VERSION, len(res)))
            conn.commit()
            if n % 100 == 0:
                print(f"[proj] {n}/{len(todo)} demos,"
                      f" {stats['events_updated']} events,"
                      f" {time.time()-t0:.0f}s", flush=True)
    stats["wall_s"] = round(time.time() - t0, 1)
    conn.close()
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    print(json.dumps(run(args.limit, args.workers), indent=1))
