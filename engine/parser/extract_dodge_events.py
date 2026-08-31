"""Targeted extractor: incoming rail/rocket/grenade near-misses on the
RECORDER ("dodge" candidates) + a lightweight strafe-correlation signal.

Scope: this is a NEW signal, distinct from everything already cached.
`lg_extracted`/LG_DODGE_MASTER covers LG contact-RATE dodging (damage-flow
model, no geometry). `projectile_extracted`/recognition_projectile_paths
covers the RECORDER'S OWN fired rockets/grenades that killed someone.
Neither covers incoming rail/rocket/grenade fire from OTHER players that
passed near the recorder WITHOUT hitting them. That is what this module
extracts: "player fired a threat weapon, it came close to me, I lived."

User's own words (the cinematic brief): "when i dodge rails / rocket (when
they go near me) or when i strafe/dodge... a nice slowmo of jumping a rail
and hitting/killing something after is nice cinematically."

Evidence model (honest — measured 2026-08-31, see report):
  - fire_weapon events carry the SHOOTER's own position and raw WP_* weapon
    id (WP_GRENADE=4, WP_ROCKET=5, WP_LIGHTNING=6, WP_RAILGUN=7 — same
    numbering already relied on by extract_lg_engagements.py and
    extract_projectile_paths.py; `weapon_name` on fire events is MOD-table
    mislabeled, same caveat those two modules already document — use the
    raw `weapon` id, never `weapon_name`, on fire_weapon rows).
  - RAILTRAIL GEOMETRY (verified empirically against real obituaries before
    writing this module): `railtrail` events carry a reliable `client_num`
    (the shooter — Q3's TE_RAILTRAIL temp entity carries an owner clientNum)
    AND a position that matches the eventual VICTIM's position at rail
    kills to within ~30-200 units, NOT the shooter's position. i.e.
    railtrail.pos is the beam's IMPACT/END point, fire_weapon.pos is the
    beam's START point. Together a `fire_weapon(weapon=7)` + `railtrail`
    event pair at (nearly) the same server_time_ms from the same shooter
    IS the exact rail beam segment for that shot — no angle reconstruction
    needed. When no matching railtrail is found within tolerance (recorder
    outside the shooter's PVS at the endpoint, or unlucky delta timing),
    this module falls back to an angle-based ray using the shooter's own
    view angles from the entity track (same `angles_to_dir` reconstruction
    extract_projectile_paths.py uses for the recorder's own shots — reused
    here by import, unmodified, because it is generic geometry that takes
    an origin+angles and has never been recorder-specific).
  - ROCKET/GRENADE: unlike the recorder's-own-kill case (extract_projectile_
    paths.py), there is no known impact point to infer a launch snapshot
    from — the launch IS the observed fire_weapon event, position and time
    both known directly. So this module does the reverse of that module:
    it FORWARD-simulates from the known launch (straight line at
    ROCKET_SPEED for rockets; extract_projectile_paths.simulate_grenade,
    reused unmodified, for grenades) and compares the simulated projectile
    position at each sampled instant against the RECORDER's own actually-
    observed position at that same instant (always available — the
    recorder's playerstate stream covers the whole demo). The minimum
    distance over the simulated flight is the closest-approach evidence.
    Grenade bounces are NOT simulated here (tracer=None → gravity-only,
    no BSP): a v1 simplification, since the pre-bounce flight is what
    reads as a threat aimed at the recorder; a rolling/bounced grenade
    is a different (lower-priority) cinematic beat. Documented, not
    hidden.
  - "Survived": a candidate is only ever WRITTEN if the recorder has no
    obituary crediting that same shooter within GRENADE_FUSE_MS after the
    fire event (the widest of the three weapons' flight windows). If the
    recorder actually died to that shot it is a hit, not a dodge, and is
    out of scope for this extractor (the `survived` column is kept in the
    schema per the brief but is always 1 in v1 — see column comment).
  - Thresholds (documented, not forensic — v1 heuristic, "useful cinematic
    signal" not "certainty"): RAIL_NEAR_MISS_U=120 (~4x player half-width
    of 15u, bg_public.h playerMaxs, plus slack for angle/measurement
    noise). SPLASH_NEAR_MISS_U=160 (a bit beyond the ~120u default QL
    rocket/grenade splash radius, so a "near miss" reads as JUST outside
    the blast, not "would have taken splash damage anyway").
  - Strafe-dodge correlation (task item b): recorder's own horizontal
    velocity vector, sampled ~450ms before and ~450ms after each recorded
    near-miss (midpoint of the requested 300-600ms window), vector-
    difference magnitude = `recorder_velocity_change`. Only computed AT a
    near-miss event, not scanned independently across the whole demo.

Candidate scope (targeted, ONE-TIME, resumable — never a full rescan):
  anchor = every recognized_frags row (a recorder KILL) whose attributes
  do not yet carry `dodge_scanned`. For each anchor's demo, opened once,
  scan [-PRE_KILL_WINDOW_MS, +POST_KILL_WINDOW_MS] around the kill for
  qualifying incoming threats. This mirrors the demo-open-once-per-missing-
  feature architecture of extract_health_armor.py / extract_lg_engagements.py
  / extract_view_timeseries.py / extract_projectile_paths.py exactly, with
  the anchor set widened to ALL recorder kills (not a filtered subset)
  because a dodge can precede any kill, not just a high-score one — this is
  the honest reason this module's candidate count is larger than its
  siblings'. Resumable via dodge_extracted(content_hash, version), same
  bookkeeping-table convention as the four sibling extractors.

Persists: a compact summary onto the kill row's attributes (dodge_scanned,
dodge_near_miss_count, dodge_min_closest_approach_units, dodge_best_threat_
type, dodge_max_velocity_change, dodge_to_kill_gap_ms) + one row per
detected near-miss into recognition_dodge_events(demo_name, server_time_ms,
version, ...).

Usage: python -u engine/parser/extract_dodge_events.py [--limit N] [--workers N]
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"

EXTRACTOR_VERSION = 1

# raw WP_* ids on fire_weapon events (bg_public.h weapon_t numbering; the
# LG=6 and ROCKET/GRENADE=4/5 half of this were already relied on by
# extract_lg_engagements.py and extract_projectile_paths.py — RAILGUN=7
# confirmed empirically against real rail obituaries before writing this
# module, see module docstring).
WP_GRENADE, WP_ROCKET, WP_LIGHTNING, WP_RAILGUN = 4, 5, 6, 7
THREAT_WEAPONS = {WP_RAILGUN: "RAIL", WP_ROCKET: "ROCKET", WP_GRENADE: "GRENADE"}

PRE_KILL_WINDOW_MS = 3000       # scan this far before each recorder kill anchor
POST_KILL_WINDOW_MS = 250       # ... and slightly after (snapshot/tick jitter)
RAIL_MATCH_TOL_MS = 120         # fire_weapon <-> railtrail correlation window
ANGLE_TOL_MS = 200              # shooter entity angle-sample tolerance
RECORDER_POS_TOL_MS = 120       # recorder snapshot lookup tolerance
STRAFE_HALF_WINDOW_MS = 450     # velocity-change sample offset either side
ROCKET_SIM_MS = 3000            # cap forward rocket simulation (3000u @ 1000ups)
GRENADE_FUSE_MS = 2500          # QL/Q3 default grenade fuse (PROVISIONAL, matches
                                 # extract_projectile_paths.py's own provisional-
                                 # constants precedent for grenade physics)
SAMPLE_MS = 25                  # matches sibling extractors' cinematic sample step
SURVIVE_CHECK_MS = GRENADE_FUSE_MS   # widest of the three flight windows

RAIL_NEAR_MISS_U = 120.0        # see module docstring for reasoning
SPLASH_NEAR_MISS_U = 160.0      # see module docstring for reasoning


# ── pure geometry helpers (unit-tested) ──────────────────────────────────────

def _snap_time(s: dict) -> int | None:
    for k in ("server_time", "server_time_ms", "serverTime", "t_ms", "t"):
        if s.get(k) is not None:
            return int(s[k])
    return None


def segment_perp(origin, end, point) -> tuple[float, float]:
    """Perpendicular distance from point to the FINITE segment origin->end,
    clamped to the segment (t in [0,1]), plus the raw (unclamped) fractional
    position along the segment. None-safe: any missing coordinate -> inf.

    This is new relative to extract_projectile_paths.py's ray_point_perp,
    which only handles an infinite forward ray — a rail beam is finite
    (it stops at the railtrail endpoint), so the closest point on the beam
    must be clamped, not extrapolated past the impact.
    """
    if any(v is None for v in (*origin[:3], *end[:3], *point[:3])):
        return math.inf, 0.0
    dx, dy, dz = end[0] - origin[0], end[1] - origin[1], end[2] - origin[2]
    seg_len2 = dx * dx + dy * dy + dz * dz
    if seg_len2 < 1e-6:
        return math.dist(origin, point), 0.0
    px, py, pz = point[0] - origin[0], point[1] - origin[1], point[2] - origin[2]
    t = (px * dx + py * dy + pz * dz) / seg_len2
    tc = max(0.0, min(1.0, t))
    closest = (origin[0] + tc * dx, origin[1] + tc * dy, origin[2] + tc * dz)
    return math.dist(closest, point), t


def straight_line_samples(origin, direction, speed: float, duration_ms: int,
                          sample_ms: int = SAMPLE_MS) -> list[tuple[int, tuple]]:
    """Rocket-style constant-velocity path: [(t_rel_ms, (x,y,z)), ...]."""
    pts: list[tuple[int, tuple]] = []
    t = 0
    while t <= duration_ms:
        d = speed * (t / 1000.0)
        pts.append((t, (origin[0] + direction[0] * d,
                        origin[1] + direction[1] * d,
                        origin[2] + direction[2] * d)))
        t += sample_ms
    return pts


def nearest(series: list[tuple], t: int, tol_ms: int):
    """First element of the tuple is a timestamp. Linear scan (per-shooter /
    per-demo series are small — matches the victim_at() style lookup already
    used in extract_projectile_paths.py). Returns the closest row within
    tol_ms, or None."""
    best, best_dt = None, tol_ms + 1
    for row in series:
        dt = abs(row[0] - t)
        if dt < best_dt:
            best, best_dt = row, dt
    return best


# ── per-demo analysis (pure on a parsed dict + injected geometry — unit-
#    tested; the injected callables are extract_projectile_paths.py's own
#    angles_to_dir/simulate_grenade, reused unmodified) ─────────────────────

def analyze_dodges(parsed: dict, kill_times: list[int], recorder_client: int,
                   angles_to_dir, simulate_grenade,
                   rocket_speed: float = 1000.0) -> dict[int, dict]:
    events = parsed.get("events", [])

    recorder_snaps: list[tuple[int, tuple, tuple]] = []
    for sn in parsed.get("snapshots", []):
        t = _snap_time(sn)
        if t is None or sn.get("origin_x") is None:
            continue
        cn = sn.get("client_num")
        if cn is not None and cn != recorder_client:
            continue
        recorder_snaps.append((
            t, (sn["origin_x"], sn["origin_y"], sn["origin_z"]),
            (sn.get("vel_x") or 0.0, sn.get("vel_y") or 0.0)))
    recorder_snaps.sort(key=lambda r: r[0])

    shooter_ent: dict[int, list[tuple[int, tuple, float, float]]] = {}
    for en in parsed.get("entities", []):
        cn = en.get("client_num")
        if (cn is None or cn == recorder_client or en.get("origin_x") is None
                or en.get("angle_yaw") is None or en.get("angle_pitch") is None):
            continue
        shooter_ent.setdefault(cn, []).append((
            en["server_time_ms"],
            (en["origin_x"], en["origin_y"], en["origin_z"]),
            en["angle_yaw"], en["angle_pitch"]))
    for lst in shooter_ent.values():
        lst.sort(key=lambda e: e[0])

    fires = []
    for e in events:
        if e.get("type") != "fire_weapon":
            continue
        cn = e.get("client_num")
        wp = e.get("weapon")
        if cn is None or cn == recorder_client or wp not in THREAT_WEAPONS:
            continue
        fires.append((e["server_time_ms"], cn, wp,
                      (e.get("pos_x"), e.get("pos_y"), e.get("pos_z"))))
    fires.sort(key=lambda f: f[0])

    rails = [(e["server_time_ms"], e.get("client_num"),
             (e.get("pos_x"), e.get("pos_y"), e.get("pos_z")))
             for e in events if e.get("type") == "railtrail"]

    recorder_deaths = [(e["server_time_ms"], e.get("killer_client"))
                       for e in events if e.get("type") == "obituary"
                       and e.get("victim_client") == recorder_client]

    def recorder_origin_at(t: int):
        r = nearest(recorder_snaps, t, RECORDER_POS_TOL_MS)
        return r[1] if r else None

    def survived(shooter: int, t0: int) -> bool:
        return not any(shooter == kc and t0 <= dt <= t0 + SURVIVE_CHECK_MS
                       for dt, kc in recorder_deaths)

    def shooter_origin_dir(shooter: int, t0: int, fallback_pos):
        samp = nearest(shooter_ent.get(shooter, []), t0, ANGLE_TOL_MS)
        origin = fallback_pos if None not in fallback_pos else (
            samp[1] if samp else None)
        direction = angles_to_dir(samp[2], samp[3]) if samp else None
        return origin, direction

    out: dict[int, dict] = {}
    seen: set[tuple] = set()   # (t0, shooter, threat_type) — dedup across
                               # overlapping kill-anchor windows
    for kt in sorted(set(kill_times)):
        w0, w1 = kt - PRE_KILL_WINDOW_MS, kt + POST_KILL_WINDOW_MS
        found: list[dict] = []
        for t0, shooter, wp, spos in fires:
            if not (w0 <= t0 <= w1):
                continue
            key = (t0, shooter, wp)
            if key in seen:
                continue
            rpos = recorder_origin_at(t0)
            if rpos is None:
                continue
            threat_type = THREAT_WEAPONS[wp]

            if threat_type == "RAIL":
                threshold = RAIL_NEAR_MISS_U
                closest_time_ms = t0
                rail = nearest([(r[0], r[1], r[2]) for r in rails
                               if r[1] == shooter], t0, RAIL_MATCH_TOL_MS)
                origin, direction = shooter_origin_dir(shooter, t0, spos)
                if rail is not None and origin is not None:
                    dist, _ = segment_perp(origin, rail[2], rpos)
                    method = "segment"
                elif origin is not None and direction is not None:
                    from extract_projectile_paths import ray_point_perp
                    dist, along = ray_point_perp(origin, direction, rpos)
                    if not math.isfinite(along) or along <= 0.0:
                        continue
                    method = "ray_angle"
                else:
                    continue
            else:
                origin, direction = shooter_origin_dir(shooter, t0, spos)
                if origin is None or direction is None:
                    continue
                if threat_type == "ROCKET":
                    threshold = SPLASH_NEAR_MISS_U
                    samples = straight_line_samples(origin, direction,
                                                    rocket_speed, ROCKET_SIM_MS)
                    method = "sim_straight"
                else:
                    threshold = SPLASH_NEAR_MISS_U
                    sim = simulate_grenade(origin, direction, GRENADE_FUSE_MS,
                                           tracer=None)
                    samples = [(p[0], (p[1], p[2], p[3])) for p in sim["points"]]
                    method = "sim_ballistic"
                best_d, best_t_rel = math.inf, 0
                for t_rel, ppos in samples:
                    rp = recorder_origin_at(t0 + t_rel)
                    if rp is None:
                        continue
                    d = math.dist(ppos, rp)
                    if d < best_d:
                        best_d, best_t_rel = d, t_rel
                dist = best_d
                closest_time_ms = t0 + best_t_rel

            if not math.isfinite(dist) or dist > threshold:
                continue
            if not survived(shooter, t0):
                continue
            seen.add(key)

            v1 = nearest(recorder_snaps, t0 - STRAFE_HALF_WINDOW_MS,
                        RECORDER_POS_TOL_MS)
            v2 = nearest(recorder_snaps, t0 + STRAFE_HALF_WINDOW_MS,
                        RECORDER_POS_TOL_MS)
            vchange = (round(math.hypot(v2[2][0] - v1[2][0],
                                        v2[2][1] - v1[2][1]), 1)
                      if v1 and v2 else None)

            found.append({
                "server_time_ms": t0,
                "threat_type": threat_type,
                "shooter_client": shooter,
                "closest_approach_units": round(dist, 1),
                "closest_time_ms": int(closest_time_ms),
                "recorder_velocity_change": vchange,
                "survived": 1,
                "method": method,
                "kill_anchor_ms": kt,
            })

        if not found:
            out[kt] = {"summary": {"dodge_scanned": 1,
                                   "dodge_near_miss_count": 0},
                      "events": []}
            continue

        best = min(found, key=lambda f: f["closest_approach_units"])
        out[kt] = {
            "summary": {
                "dodge_scanned": 1,
                "dodge_near_miss_count": len(found),
                "dodge_min_closest_approach_units": best["closest_approach_units"],
                "dodge_best_threat_type": best["threat_type"],
                "dodge_max_velocity_change": max(
                    (f["recorder_velocity_change"] for f in found
                    if f["recorder_velocity_change"] is not None), default=None),
                "dodge_to_kill_gap_ms": kt - best["closest_time_ms"],
            },
            "events": found,
        }
    return out


# ── process-boundary-crossing wrapper ────────────────────────────────────────

def extract_one(demo_path: str, kill_times: list[int],
                recorder_client: int) -> dict[int, dict]:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from demo_parse import DM73Parser
    from extract_projectile_paths import angles_to_dir, simulate_grenade, \
        ROCKET_SPEED
    parsed = DM73Parser(Path(demo_path)).parse()
    return analyze_dodges(parsed, kill_times, recorder_client,
                          angles_to_dir=angles_to_dir,
                          simulate_grenade=simulate_grenade,
                          rocket_speed=ROCKET_SPEED)


# ── candidate selection ──────────────────────────────────────────────────────

def candidate_map() -> dict[str, list[int]]:
    """demo_name -> [server_time_ms...] of recorder kills not yet dodge-scanned."""
    c = sqlite3.connect(f"file:{RECOG_DB}?mode=ro", uri=True)
    out: dict[str, list[int]] = {}
    for demo, t, attrs in c.execute(
            "SELECT demo_name, server_time_ms, attributes FROM recognized_frags"):
        a = json.loads(attrs or "{}")
        if a.get("dodge_scanned") is not None:
            continue    # cache hit
        out.setdefault(demo, []).append(t)
    c.close()
    return out


# ── driver ───────────────────────────────────────────────────────────────────

def run(limit: int | None = None, workers: int = 8) -> dict:
    conn = sqlite3.connect(RECOG_DB, timeout=60.0)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("CREATE TABLE IF NOT EXISTS dodge_extracted ("
                 " content_hash TEXT PRIMARY KEY, demo_name TEXT,"
                 " version INTEGER, events INTEGER, status TEXT,"
                 " extracted_at TEXT DEFAULT (datetime('now')))")
    conn.execute("CREATE TABLE IF NOT EXISTS recognition_dodge_events ("
                 " demo_name TEXT, server_time_ms INTEGER, version INTEGER,"
                 " kill_anchor_ms INTEGER, threat_type TEXT,"
                 " shooter_client INTEGER, closest_approach_units REAL,"
                 " closest_time_ms INTEGER, recorder_velocity_change REAL,"
                 " survived INTEGER, method TEXT,"
                 " PRIMARY KEY (demo_name, server_time_ms, shooter_client,"
                 " threat_type))")
    conn.commit()

    fconn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    meta = {n: (p, dup or h, rc) for n, p, h, dup, rc in fconn.execute(
        "SELECT name, path, content_hash, duplicate_of, recorder_client"
        " FROM demos")}
    fconn.close()

    done = {r[0] for r in conn.execute(
        "SELECT content_hash FROM dodge_extracted WHERE version=? AND"
        " status='ok'", (EXTRACTOR_VERSION,))}
    cands = candidate_map()
    # recorder_client must be known — demos where it is NULL can't distinguish
    # the recorder's own shots from enemy shots, so they're skipped (honest
    # edge case; ~4% of the demos table per 2026-08-31 audit).
    todo = [(d, *meta[d], ts) for d, ts in cands.items()
            if d in meta and meta[d][1] not in done and meta[d][2] is not None]
    if limit:
        todo = todo[:limit]

    stats = {"eligible_kill_anchors": sum(len(t) for t in cands.values()),
             "demos_to_open": len(todo), "events_updated": 0,
             "near_misses_written": 0, "failed": 0}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(extract_one, path, ts, rc): (demo, h, ts)
                for demo, path, h, rc, ts in todo}
        n = 0
        for fut in as_completed(futs):
            demo, h, ts = futs[fut]
            n += 1
            try:
                res = fut.result()
            except Exception as e:   # noqa: BLE001 - per-demo isolation
                conn.execute("INSERT OR REPLACE INTO dodge_extracted VALUES"
                             " (?,?,?,?,?,datetime('now'))",
                             (h, demo, EXTRACTOR_VERSION, 0,
                              f"fail: {type(e).__name__}"))
                conn.commit()
                stats["failed"] += 1
                continue
            for kt, payload in res.items():
                row = conn.execute(
                    "SELECT id, attributes FROM recognized_frags WHERE"
                    " demo_name=? AND server_time_ms=?", (demo, kt)).fetchone()
                if row is None:
                    continue
                a = json.loads(row[1] or "{}")
                a.update(payload["summary"])
                conn.execute("UPDATE recognized_frags SET attributes=?"
                             " WHERE id=?", (json.dumps(a), row[0]))
                for ev in payload["events"]:
                    conn.execute(
                        "INSERT OR REPLACE INTO recognition_dodge_events"
                        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (demo, ev["server_time_ms"], EXTRACTOR_VERSION,
                         ev["kill_anchor_ms"], ev["threat_type"],
                         ev["shooter_client"], ev["closest_approach_units"],
                         ev["closest_time_ms"], ev["recorder_velocity_change"],
                         ev["survived"], ev["method"]))
                    stats["near_misses_written"] += 1
                stats["events_updated"] += 1
            conn.execute("INSERT OR REPLACE INTO dodge_extracted VALUES"
                         " (?,?,?,?, 'ok', datetime('now'))",
                         (h, demo, EXTRACTOR_VERSION, len(res)))
            conn.commit()
            if n % 50 == 0:
                print(f"[dodge] {n}/{len(todo)} demos,"
                      f" {stats['events_updated']} anchors,"
                      f" {stats['near_misses_written']} near-misses,"
                      f" {time.time()-t0:.0f}s", flush=True)
    stats["wall_s"] = round(time.time() - t0, 1)
    conn.close()
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    print(json.dumps(run(args.limit, args.workers), indent=1))
