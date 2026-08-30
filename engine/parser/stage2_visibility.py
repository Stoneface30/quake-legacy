"""Stage-2 geometric visibility evidence for candidate frags.

For each candidate frag (from ``frag_recognition.db`` / ``recognized_frags``,
read-only) this re-parses the demo with ``demo_parse.DM73Parser``, rebuilds the
attacker + victim position/angle time series from the entity stream, loads the
map's BSP out of the staging pak00.pk3, and computes real occlusion evidence:

  * visible_fraction at shot time and at -100 / -200 / -300 ms
  * los_open_duration_ms  — how long LOS had been open before the shot
                            (walk back in 25 ms steps until closed, cap 2000)
  * angular_size_deg      — apparent size of the victim on screen
  * corner_prefire        — victim was <15% visible 200 ms before the kill but
                            clearly visible at kill time (LOS opened at the
                            last instant — the attacker was pre-aimed)

TIMING NOTE (honesty): for hitscan weapons (rail/LG/MG/SG) the fire time IS
the kill time, so "shot time" below == obituary server_time_ms and the column
``fire_time_basis`` records 'kill_time_hitscan'.  For projectile kills the
fire happened earlier and is NOT reconstructed here; rows are still computed
at kill time and labelled 'kill_time_projectile_approx'.

Positions come from the demo entity stream at snapshot granularity; samples
are linearly interpolated between snapshots.  Geometry approximations are
documented in ``bsp_geometry.py``.

Results land in frag_recognition.db table ``stage2_visibility``
(CREATE TABLE IF NOT EXISTS, INSERT OR REPLACE keyed on
demo_name+server_time_ms+victim_client → resumable).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bsp_geometry as bg          # noqa: E402
from demo_parse import DM73Parser  # noqa: E402

REPO_ROOT = HERE.parents[1]
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
REBUILT_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"

HITSCAN_WEAPONS = {"RAILGUN", "LIGHTNING", "MACHINEGUN", "SHOTGUN", "GAUNTLET",
                   "HMG", "CHAINGUN"}

DDL = """
CREATE TABLE IF NOT EXISTS stage2_visibility (
    demo_name        TEXT NOT NULL,
    server_time_ms   INTEGER NOT NULL,
    victim_client    INTEGER NOT NULL,
    map_name         TEXT,
    weapon_name      TEXT,
    fire_time_basis  TEXT,     -- 'kill_time_hitscan' | 'kill_time_projectile_approx'
    visible_fraction        REAL,
    visible_fraction_m100   REAL,
    visible_fraction_m200   REAL,
    visible_fraction_m300   REAL,
    los_open_duration_ms    INTEGER,
    angular_size_deg        REAL,
    corner_prefire          INTEGER,   -- 1 = evidence present
    distance_units          REAL,
    error            TEXT,
    computed_at      TEXT,
    PRIMARY KEY (demo_name, server_time_ms, victim_client)
)
"""


# ── time series helpers ──────────────────────────────────────────────────────

class Track:
    """Sorted (t, x, y, z, yaw, pitch) samples for one client."""

    def __init__(self):
        self.t: list[int] = []
        self.rows: list[tuple] = []

    def add(self, t, x, y, z, yaw, pitch):
        if x is None or y is None or z is None:
            return
        self.t.append(t)
        self.rows.append((x, y, z, yaw, pitch))

    def sample(self, t_ms: float):
        """Linear interp position (hold angles) at t_ms; None if out of range."""
        import bisect
        if not self.t:
            return None
        i = bisect.bisect_right(self.t, t_ms)
        if i == 0:
            return None
        if i >= len(self.t):
            r = self.rows[-1]
            # tolerate up to 300 ms extrapolation-by-hold
            return r if t_ms - self.t[-1] <= 300 else None
        t0, t1 = self.t[i - 1], self.t[i]
        r0, r1 = self.rows[i - 1], self.rows[i]
        if t1 == t0:
            return r0
        f = (t_ms - t0) / (t1 - t0)
        return (r0[0] + f * (r1[0] - r0[0]),
                r0[1] + f * (r1[1] - r0[1]),
                r0[2] + f * (r1[2] - r0[2]),
                r0[3], r0[4])


def build_tracks(stream: dict) -> dict[int, Track]:
    tracks: dict[int, Track] = {}
    for e in stream["entities"]:
        c = e.get("client_num")
        if c is None:
            continue
        tracks.setdefault(c, Track()).add(
            e["server_time_ms"], e.get("origin_x"), e.get("origin_y"),
            e.get("origin_z"), e.get("angle_yaw"), e.get("angle_pitch"))
    # Playerstate covers the recorder with better fidelity — merge it in.
    for s in stream["snapshots"]:
        c = s.get("client_num")
        if c is None:
            continue
        tracks.setdefault(c, Track()).add(
            s["server_time_ms"], s.get("origin_x"), s.get("origin_y"),
            s.get("origin_z"), s.get("angle_yaw"), s.get("angle_pitch"))
    # Ensure sorted (entity + snapshot merge can interleave)
    for tr in tracks.values():
        order = sorted(range(len(tr.t)), key=lambda i: tr.t[i])
        tr.t = [tr.t[i] for i in order]
        tr.rows = [tr.rows[i] for i in order]
    return tracks


# ── per-frag computation ─────────────────────────────────────────────────────

def compute_frag(m, atk: Track, vic: Track, t_kill: int) -> dict:
    out: dict = {}

    def vf_at(t):
        a = atk.sample(t)
        v = vic.sample(t)
        if a is None or v is None:
            return None
        eye = bg.eye_point(a[:3])
        return bg.visible_fraction(m, eye, v[:3])

    out["visible_fraction"] = vf_at(t_kill)
    out["visible_fraction_m100"] = vf_at(t_kill - 100)
    out["visible_fraction_m200"] = vf_at(t_kill - 200)
    out["visible_fraction_m300"] = vf_at(t_kill - 300)

    a = atk.sample(t_kill)
    v = vic.sample(t_kill)
    if a is not None and v is not None:
        eye = bg.eye_point(a[:3])
        out["angular_size_deg"] = round(bg.angular_size_deg(eye, v[:3]), 4)
        import math
        out["distance_units"] = round(math.dist(a[:3], v[:3]), 1)
    else:
        out["angular_size_deg"] = None
        out["distance_units"] = None

    # LOS-open duration: walk back in 25 ms steps until visible_fraction == 0
    los_open = None
    if out["visible_fraction"] is not None and out["visible_fraction"] > 0:
        los_open = 0
        t = t_kill
        while los_open < 2000:
            t -= 25
            f = vf_at(t)
            if f is None or f == 0.0:
                break
            los_open += 25
    out["los_open_duration_ms"] = los_open

    # Corner-prefire evidence: nearly invisible 200 ms before the kill,
    # clearly visible at kill time.
    vfk = out["visible_fraction"]
    vfp = out["visible_fraction_m200"]
    out["corner_prefire"] = int(
        vfk is not None and vfp is not None and vfp < 0.15 and vfk >= 0.5)
    return out


# ── candidate selection ──────────────────────────────────────────────────────

def pick_candidates(limit: int) -> list[dict]:
    """Read-only query of recognized_frags for stage-2 worthy frags."""
    con = sqlite3.connect(f"file:{RECOG_DB}?mode=ro", uri=True)
    try:
        rows = con.execute(
            """SELECT demo_name, content_hash, server_time_ms, victim_client,
                      weapon_name, json_extract(attributes,'$.distance') AS d,
                      classes
               FROM recognized_frags
               WHERE classes LIKE '%PIXEL_SHOT_CANDIDATE%'
                  OR json_extract(attributes,'$.distance') > 1500
               ORDER BY d DESC LIMIT ?""", (limit,)).fetchall()
    finally:
        con.close()
    src = sqlite3.connect(f"file:{REBUILT_DB}?mode=ro", uri=True)
    try:
        paths = dict(src.execute("SELECT content_hash, path FROM demos"))
        names = dict(src.execute("SELECT name, path FROM demos"))
    finally:
        src.close()
    out = []
    for demo_name, chash, t, vic, weap, dist, classes in rows:
        p = paths.get(chash) or names.get(demo_name)
        out.append({"demo_name": demo_name, "path": p, "server_time_ms": t,
                    "victim_client": vic, "weapon_name": weap,
                    "distance": dist, "classes": classes})
    return out


# ── main ─────────────────────────────────────────────────────────────────────

def run(candidates: list[dict], db_path: Path = RECOG_DB, verbose=True) -> list[dict]:
    con = sqlite3.connect(db_path, timeout=60)
    con.execute(DDL)
    con.commit()

    parsed_cache: dict[str, dict] = {}
    results = []
    for c in candidates:
        key = (c["demo_name"], c["server_time_ms"], c["victim_client"])
        row = {"demo_name": key[0], "server_time_ms": key[1],
               "victim_client": key[2], "weapon_name": c.get("weapon_name"),
               "map_name": None, "error": None}
        try:
            if not c.get("path") or not Path(c["path"]).exists():
                raise FileNotFoundError(f"demo path missing: {c.get('path')}")
            if c["path"] not in parsed_cache:
                stream = DM73Parser(c["path"]).parse()
                parsed_cache[c["path"]] = {
                    "map": stream["map"], "tracks": build_tracks(stream),
                    "events": [e for e in stream["events"]
                               if e["type"] == "obituary"]}
                # keep memory bounded
                if len(parsed_cache) > 4:
                    parsed_cache.pop(next(iter(parsed_cache)))
            pc = parsed_cache[c["path"]]
            row["map_name"] = pc["map"]
            m = bg.load_map(pc["map"])
            # find killer for this obituary
            killer = None
            best_dt = 51
            for e in pc["events"]:
                if e.get("victim_client") != key[2]:
                    continue
                dt = abs(e["server_time_ms"] - key[1])
                if dt < best_dt:            # exact match normally; ±50ms tolerated
                    best_dt = dt
                    killer = e.get("killer_client")
            if killer is None:
                raise LookupError("obituary not found in re-parse")
            atk = pc["tracks"].get(killer)
            vic = pc["tracks"].get(key[2])
            if atk is None or vic is None or not atk.t or not vic.t:
                raise LookupError(f"no track (killer={killer} vic={key[2]})")
            row.update(compute_frag(m, atk, vic, key[1]))
            hits = (c.get("weapon_name") or "").upper() in HITSCAN_WEAPONS
            row["fire_time_basis"] = ("kill_time_hitscan" if hits
                                      else "kill_time_projectile_approx")
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        row["computed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        con.execute(
            """INSERT OR REPLACE INTO stage2_visibility
               (demo_name, server_time_ms, victim_client, map_name, weapon_name,
                fire_time_basis, visible_fraction, visible_fraction_m100,
                visible_fraction_m200, visible_fraction_m300,
                los_open_duration_ms, angular_size_deg, corner_prefire,
                distance_units, error, computed_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (row["demo_name"], row["server_time_ms"], row["victim_client"],
             row.get("map_name"), row.get("weapon_name"),
             row.get("fire_time_basis"), row.get("visible_fraction"),
             row.get("visible_fraction_m100"), row.get("visible_fraction_m200"),
             row.get("visible_fraction_m300"), row.get("los_open_duration_ms"),
             row.get("angular_size_deg"), row.get("corner_prefire"),
             row.get("distance_units"), row.get("error"), row["computed_at"]))
        con.commit()
        results.append(row)
        if verbose:
            if row.get("error"):
                print(f"[s2] {key[0]} t={key[1]} ERROR {row['error']}")
            else:
                print(f"[s2] {key[0]} t={key[1]} vic={key[2]} "
                      f"vf={row['visible_fraction']:.2f} "
                      f"vf-200={row['visible_fraction_m200']} "
                      f"los_open={row['los_open_duration_ms']}ms "
                      f"ang={row['angular_size_deg']}deg "
                      f"prefire={row['corner_prefire']}")
    con.close()
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int, default=20,
                    help="max candidate frags to process")
    ap.add_argument("--db", default=str(RECOG_DB),
                    help="frag_recognition.db path (stage2 table is created here)")
    a = ap.parse_args()
    cands = pick_candidates(a.limit)
    print(f"[s2] {len(cands)} candidates")
    res = run(cands, Path(a.db))
    ok = [r for r in res if not r.get("error")]
    print(f"[s2] done: {len(ok)}/{len(res)} computed")


if __name__ == "__main__":
    main()
