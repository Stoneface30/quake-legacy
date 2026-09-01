"""PROJECTILE_BRIDGE candidate matching (directive §25-28).

Shortlists a Scene B to cut to from a given Scene A, using only cached
recognition evidence — no demo re-reads, no manual scrubbing through
thousands of clips.

WHAT ACTUALLY MAKES THIS CUT WORK, and why the obvious metric is wrong:

The naive metric is world-space direction continuity — dot(A_terminal_dir,
B_launch_dir) — i.e. "the rocket was flying north, so the next rocket
should also fly north". That is the wrong axis. In a PROJECTILE_BRIDGE the
camera is riding the projectile, so the projectile's direction IS the
camera's forward vector. A camera flying forward looks like "flying
forward" on screen whether the world direction is north or south. World
heading is invisible to the viewer across a cut; matching it buys nothing.

What the viewer actually perceives across the cut, and what this module
therefore scores:

  * apparent SPEED — a fast flight cutting to a slow one (or vice versa)
    breaks the motion illusion immediately. Matched on world units/sec.
  * PITCH — level flight vs a dive read completely differently on screen
    even at identical speed. Matched on the vertical component of the
    direction unit vector.
  * RUNWAY — Scene B needs enough flight left after the cut to establish
    itself before its own impact, or the transition lands on a cut-to-cut.
  * PAYOFF — Scene B should be worth cutting to (highlight_score), else
    the transition is technically pretty and dramatically pointless.
  * MAP CONTRAST — an optional preference. Cutting to a different arena
    makes the bridge read as a deliberate transition rather than an
    ambiguous jump within one fight; cutting within one map is the safer,
    less showy option. Exposed as a weight, not hardcoded.

Every one of these is computed from `recognition_projectile_paths` +
`recognized_frags`, both already fully populated.
"""
from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
# Authoritative map names live here (read-only; project hard rule).
FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"

# A Scene B needs at least this much flight after the cut to establish.
MIN_RUNWAY_MS = 600
# Below this, a "flight" is a point-blank shot with no ride-along value.
MIN_FLIGHT_MS = 400

# A Quake Live rocket travels at 900 u/s (g_missile.c). Cached paths that
# measure far off that are not rockets we can ride: a camera flown along
# them tracks something that was never there.
#
# Measured across all 2,706 rideable cached paths (2026-09-01), median arc
# speed by flight duration:
#
#     200-700 ms   n=1847   1076 u/s     <- consistent with 900 nominal
#     700-1200 ms  n= 376    993 u/s     <- consistent
#     1200 ms +    n= 288    306 u/s     <- not a rocket
#
# 225 of the 288 paths over 1200 ms (78%) measure under 600 u/s.
#
# The band is not a guess: the arc-speed histogram over all 1,377 loaded
# candidates is plainly bimodal, with a trough between the two modes.
#
#     0- 600   461 paths   <- broad low mode, not projectiles
#   600- 900   106 paths   <- trough
#   900-1200   726 paths   <- sharp peak, centred 1000-1100
#   1200+       84 paths   <- thin tail (short-flight sampling noise)
#
# The floor is placed at the top of the trough rather than at its bottom,
# so the low mode's shoulder is excluded too. The ceiling is left loose
# because a 25 ms sampling tick inflates apparent speed on short flights,
# and over-reading a real rocket is far less damaging than riding a
# fabricated arc.
#
# Note that straightness is NOT a discriminator, though it looks like one:
# 100% of the paths inside the plausible band are perfectly straight
# (arc == chord). Rockets fly straight. Speed is what separates a real
# flight from a bad one.
PLAUSIBLE_SPEED_MIN = 800.0
PLAUSIBLE_SPEED_MAX = 1400.0


def _unit(v: tuple[float, float, float]) -> tuple[float, float, float]:
    n = math.sqrt(sum(c * c for c in v))
    return (0.0, 0.0, 0.0) if n < 1e-9 else (v[0] / n, v[1] / n, v[2] / n)


def path_metrics(path_json: dict) -> dict[str, Any] | None:
    """Speed / pitch / duration / length for one cached projectile path.

    Returns None when the path is too short to ride (see MIN_FLIGHT_MS) or
    is missing the point series entirely.
    """
    pts = path_json.get("points") or []
    if len(pts) < 3:
        return None
    duration_ms = pts[-1][0] - pts[0][0]
    if duration_ms < MIN_FLIGHT_MS:
        return None
    p0 = (pts[0][1], pts[0][2], pts[0][3])
    p1 = (pts[-1][1], pts[-1][2], pts[-1][3])
    length = math.dist(p0, p1)
    speed_ups = length / (duration_ms / 1000.0) if duration_ms else 0.0

    # Arc length, not just the chord. A bouncing grenade covers real ground
    # while its endpoints sit close together, so chord speed alone would
    # call it implausibly slow; path speed does not. (Measured: of 632
    # paths under 600 u/s by chord, 627 are also under 600 by arc — they
    # are not bouncing projectiles, they are bad data. Only 5 bounce.)
    arc = sum(math.dist((a[1], a[2], a[3]), (b[1], b[2], b[3]))
              for a, b in zip(pts, pts[1:]))
    path_speed_ups = arc / (duration_ms / 1000.0) if duration_ms else 0.0

    # terminal direction: last ~25% of the flight, the vector the camera
    # is travelling along at the moment of the cut.
    tail_start = max(0, int(len(pts) * 0.75))
    t0 = (pts[tail_start][1], pts[tail_start][2], pts[tail_start][3])
    terminal = _unit((p1[0] - t0[0], p1[1] - t0[1], p1[2] - t0[2]))
    # launch direction: prefer the engine-recorded launch dir when present
    launch = path_json.get("launch") or {}
    if launch.get("dir"):
        launch_dir = _unit(tuple(launch["dir"]))
    else:
        head_end = max(1, int(len(pts) * 0.25))
        h1 = (pts[head_end][1], pts[head_end][2], pts[head_end][3])
        launch_dir = _unit((h1[0] - p0[0], h1[1] - p0[1], h1[2] - p0[2]))

    return {
        "duration_ms": duration_ms,
        "length_u": round(length, 1),
        "speed_ups": round(speed_ups, 1),
        "path_speed_ups": round(path_speed_ups, 1),
        "speed_plausible": PLAUSIBLE_SPEED_MIN <= path_speed_ups
                           <= PLAUSIBLE_SPEED_MAX,
        "terminal_dir": terminal,
        "launch_dir": launch_dir,
        # vertical component == sin(pitch); level flight ~0, dive negative
        "launch_pitch": round(launch_dir[2], 4),
        "terminal_pitch": round(terminal[2], 4),
        "kind": path_json.get("kind"),
        "confidence": path_json.get("confidence"),
    }


def load_candidates(db_path: Path | str = RECOG_DB,
                    require_confirmed: bool = True,
                    map_names: dict[str, str] | None = None,
                    require_evidence: bool = True) -> list[dict]:
    """Every ride-able cached projectile path with its metrics + frag score.

    ``require_evidence`` applies ``director_preview.projectile_evidence``,
    the single authoritative test of whether a path can carry a camera.
    Without it 51 of 1,377 candidates enter the ranking with less than
    ``MIN_DISPLACEMENT_U`` of travel -- an impact record with no ride to
    photograph. ``path_metrics`` alone does not catch these: it gates on
    duration, and a path can last 400 ms while going nowhere.

    Imported lazily because director_preview pulls in the whole capture
    stack, which this module otherwise does not need.
    """
    if require_evidence:
        from creative_suite.engine.director_preview import projectile_evidence
    else:
        projectile_evidence = None
    if map_names is None:
        map_names = load_map_names()
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT p.demo_name, p.server_time_ms, p.path, "
            "       f.highlight_score, f.classes, f.id "
            "FROM recognition_projectile_paths p "
            "LEFT JOIN recognized_frags f "
            "  ON f.demo_name = p.demo_name "
            " AND f.server_time_ms = p.server_time_ms"
        ).fetchall()
    finally:
        con.close()

    out: list[dict] = []
    for demo, t_ms, blob, score, classes, frag_id in rows:
        try:
            pj = json.loads(blob)
        except (TypeError, json.JSONDecodeError):
            continue
        if require_confirmed and pj.get("confidence") != "CONFIRMED":
            continue
        if projectile_evidence is not None and not projectile_evidence(pj)["usable"]:
            continue
        m = path_metrics(pj)
        if m is None:
            continue
        out.append({
            "frag_id": frag_id, "demo_name": demo, "server_time_ms": t_ms,
            "map": map_names.get(demo, "?"), "highlight_score": score or 0.0,
            "classes": _class_names(classes), **m,
            "launch_t": (pj.get("launch") or {}).get("t"),
            "impact_t": (pj.get("impact") or {}).get("t"),
        })
    return out


def load_map_names(db_path: Path | str = FRAGS_DB) -> dict[str, str]:
    """demo_name -> map_name from the authoritative parse.

    Do NOT infer the map from the filename: demo names are not uniformly
    shaped. Most are ``CA-<player>-<map>-<date>...`` but a real subset is
    ``CA-<map>-<date>...`` with no player field, which a positional split
    misreads as a map called e.g. "2011_07_18" (observed in the first run
    of this shortlister).
    """
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return {}
    try:
        # Case-folded: the corpus records 61 distinct map strings for 54
        # actual maps (asylum / Asylum / AsyLUm, quarantine / Quarantine /
        # qUARanTINe, ...). Compared raw, the same arena reads as two, and
        # a same-arena cut gets scored — and bonused — as cross-arena.
        return {name: (map_name or "?").lower() for name, map_name
                in con.execute("SELECT name, map_name FROM demos")}
    except sqlite3.Error:
        return {}
    finally:
        con.close()


def _class_names(classes_json: str | None) -> list[str]:
    try:
        return [c["name"] if isinstance(c, dict) else c
                for c in json.loads(classes_json or "[]")]
    except json.JSONDecodeError:
        return []


def event_signature(cand: dict) -> tuple:
    """Identity of the MOMENT, independent of which file recorded it.

    The corpus contains the same kill saved under two filenames with two
    different content hashes, so neither the name nor the hash dedupes
    them. Frags 19639 and 34346 are one overkill rocket at server_time
    465350; unguarded, ``score_pair`` rates that pair 0.875 with a perfect
    speed match and the shortlister offers a frag a cut to itself.

    ``duplicate_of`` in frags_rebuilt.demos would be the natural source,
    but it is unpopulated (0 of 4,292 rows), so the moment is identified
    positionally instead: same arena, same server clock, same flight.
    """
    return (cand.get("map"), cand.get("server_time_ms"),
            cand.get("duration_ms"), round(cand.get("length_u") or 0.0))


def score_pair(scene_a: dict, scene_b: dict, *,
               prefer_different_map: float = 0.15) -> dict:
    """Compatibility of cutting from scene_a's impact into scene_b's launch.

    All components are in [0,1]; the total is a weighted sum. See the
    module docstring for why world-heading continuity is deliberately NOT
    a component.
    """
    # apparent speed match — ratio-based so it is scale-free
    sa, sb = scene_a["speed_ups"], scene_b["speed_ups"]
    speed_match = min(sa, sb) / max(sa, sb) if max(sa, sb) > 0 else 0.0

    # pitch match — compares the screen-relevant vertical component of
    # A's terminal travel against B's launch travel
    pitch_delta = abs(scene_a["terminal_pitch"] - scene_b["launch_pitch"])
    pitch_match = max(0.0, 1.0 - pitch_delta)   # both in [-1,1]

    # runway — B must have flight left to establish after the cut
    runway = min(1.0, scene_b["duration_ms"] / (MIN_RUNWAY_MS * 2))

    # payoff — normalised against a 50-point highlight scale
    payoff = min(1.0, (scene_b["highlight_score"] or 0.0) / 50.0)

    different_map = scene_a["map"] != scene_b["map"]
    map_bonus = prefer_different_map if different_map else 0.0

    total = (0.35 * speed_match + 0.20 * pitch_match
             + 0.20 * runway + 0.25 * payoff + map_bonus)
    return {
        "total": round(total, 4),
        "speed_match": round(speed_match, 3),
        "pitch_match": round(pitch_match, 3),
        "runway": round(runway, 3),
        "payoff": round(payoff, 3),
        "different_map": different_map,
    }


def shortlist_scene_b(scene_a: dict, candidates: list[dict], *,
                      top_n: int = 20,
                      prefer_different_map: float = 0.15) -> list[dict]:
    """Rank candidates as the Scene B for a given Scene A.

    Excludes scene_a itself, anything from the same demo (cutting within
    one demo is a jump cut, not a bridge), anything that is the SAME
    MOMENT re-saved under a different filename, and anything without
    enough runway.
    """
    a_sig = event_signature(scene_a)
    ranked = []
    for cand in candidates:
        if cand["demo_name"] == scene_a["demo_name"]:
            continue
        if event_signature(cand) == a_sig:
            continue
        if cand["duration_ms"] < MIN_RUNWAY_MS:
            continue
        s = score_pair(scene_a, cand, prefer_different_map=prefer_different_map)
        ranked.append({**cand, "match": s})
    ranked.sort(key=lambda r: -r["match"]["total"])

    # Collapse duplicate MOMENTS within the shortlist, keeping the
    # best-scoring representative. Excluding scene_a's own signature is not
    # enough: the corpus stores the same kill under several filenames, so a
    # naive top-10 spends slots on the same shot twice (measured: 2 of 10
    # for the top Scene A -- Frags 27622/34632 are one trinity rocket at
    # server_time 165975, as are 7491/34699 on asylum at 886150).
    seen: set[tuple] = set()
    unique = []
    for r in ranked:
        sig = event_signature(r)
        if sig in seen:
            continue
        seen.add(sig)
        unique.append(r)
        if len(unique) >= top_n:
            break
    return unique


def pick_scene_a(candidates: list[dict], *, min_duration_ms: int = 1200,
                 require_plausible_speed: bool = True) -> dict | None:
    """The strongest ride-along Scene A: long flight, high payoff.

    The duration floor alone is actively harmful, which is why the speed
    filter defaults on. Long flights in this corpus are mostly *not* long
    rocket flights — 78% of paths over 1200 ms measure under 600 u/s,
    against a nominal rocket speed of 900. Selecting purely for duration
    therefore selects almost exclusively for bad data, and the camera then
    rides an arc no projectile ever flew.

    Pass ``require_plausible_speed=False`` only to reproduce the old,
    unfiltered ranking.
    """
    pool = [c for c in candidates if c["duration_ms"] >= min_duration_ms]
    if require_plausible_speed:
        pool = [c for c in pool if c.get("speed_plausible")]
    if not pool:
        return None
    return max(pool, key=lambda c: (c["highlight_score"] or 0.0,
                                    c["duration_ms"]))
