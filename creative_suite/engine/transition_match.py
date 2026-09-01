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
                    map_names: dict[str, str] | None = None) -> list[dict]:
    """Every ride-able cached projectile path with its metrics + frag score."""
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
        return {name: (map_name or "?") for name, map_name in con.execute(
            "SELECT name, map_name FROM demos")}
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

    Excludes scene_a itself and anything from the same demo (cutting
    within one demo is a jump cut, not a bridge), and anything without
    enough runway.
    """
    ranked = []
    for cand in candidates:
        if cand["demo_name"] == scene_a["demo_name"]:
            continue
        if cand["duration_ms"] < MIN_RUNWAY_MS:
            continue
        s = score_pair(scene_a, cand, prefer_different_map=prefer_different_map)
        ranked.append({**cand, "match": s})
    ranked.sort(key=lambda r: -r["match"]["total"])
    return ranked[:top_n]


def pick_scene_a(candidates: list[dict], *, min_duration_ms: int = 1200
                 ) -> dict | None:
    """The strongest ride-along Scene A: long flight, high payoff."""
    pool = [c for c in candidates if c["duration_ms"] >= min_duration_ms]
    if not pool:
        return None
    return max(pool, key=lambda c: (c["highlight_score"] or 0.0,
                                    c["duration_ms"]))
