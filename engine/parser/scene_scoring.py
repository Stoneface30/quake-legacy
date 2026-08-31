"""Round-level SCENE scoring (user 2026-08-30: score whole rounds — the
fragmovie cuts scenes, not isolated kills).

DB-only over the recognition cache. A scene = (demo, round) holding the
recorder's frags. Components (frag skill first, per standing priority):
  peak_score      best member frag highlight_score       (the money shot)
  mass_score      0.35 * sum of other members' scores    (sustained action)
  density_bonus   kills/second of the round's kill span
  variety_bonus   distinct weapons + distinct top-level classes
  clutch_bonus    round carries a clutch label
  fight_intensity ALL-player kill density in the window (user 2026-08-31:
                  big team fights are usable material even beyond the
                  recorder's own kills) — from frags_rebuilt, DB-only
  context         low-HP presence (small, secondary)
Suggested capture window per scene: first kill -5s .. last kill +4s.

Output: output/demo_v2/recognition/top_scenes_ca.csv (+json) and
scene_score attributes back onto member rows.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"
OUT_DIR = REPO_ROOT / "output" / "demo_v2" / "recognition"

PREMIUM = {"CLUTCH_1V2", "CLUTCH_1V3", "CLUTCH_1V4_PLUS"}


def run(top_n: int = 100) -> dict:
    t0 = time.time()
    conn = sqlite3.connect(RECOG_DB)
    conn.row_factory = sqlite3.Row
    # all-player kill times per demo (big-fight evidence)
    fconn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    all_kills: dict[str, list[int]] = {}
    for d, t in fconn.execute("SELECT demo_name, server_time_ms FROM frags"):
        all_kills.setdefault(d, []).append(t)
    fconn.close()
    for v in all_kills.values():
        v.sort()
    scenes: dict[tuple, list[dict]] = {}
    for r in conn.execute(
            "SELECT id, demo_name, round, server_time_ms, weapon_name,"
            " classes, attributes, highlight_score, reasons"
            " FROM recognized_frags"):
        a = json.loads(r["attributes"] or "{}")
        if a.get("mode_pool") != "MAIN_CA" or r["round"] is None:
            continue
        scenes.setdefault((r["demo_name"], r["round"]), []).append({
            "id": r["id"], "t": r["server_time_ms"],
            "score": r["highlight_score"] or 0,
            "weapon": r["weapon_name"],
            "classes": {x["name"] if isinstance(x, dict) else x
                        for x in json.loads(r["classes"] or "[]")},
            "low_hp": (a.get("health_at_frag") or 999) <= 35,
        })

    rows = []
    for (demo, rnd), members in scenes.items():
        if not members:
            continue
        members.sort(key=lambda m: m["t"])
        scores = sorted((m["score"] for m in members), reverse=True)
        peak = scores[0]
        mass = 0.35 * sum(scores[1:])
        span_s = max(1.0, (members[-1]["t"] - members[0]["t"]) / 1000.0)
        density = min(6.0, (len(members) / span_s) * 3.0) if len(members) > 1 else 0.0
        weapons = {m["weapon"] for m in members}
        all_cls = set().union(*(m["classes"] for m in members))
        variety = min(4.0, 0.8 * len(weapons) + 0.4 * len(all_cls & {
            "CLEAN_FLICK", "EXTREME_FLICK", "DIRECT_CONFIRMED_GEO",
            "AIR_ROCKET_GEO", "LG_HIGH_PRESSURE", "RAPID_MULTIKILL"}))
        clutch = 5.0 if all_cls & PREMIUM else 0.0
        w0, w1 = members[0]["t"] - 5000, members[-1]["t"] + 4000
        from bisect import bisect_left, bisect_right
        ak = all_kills.get(demo, [])
        total_kills = bisect_right(ak, w1) - bisect_left(ak, w0)
        fight = min(4.0, max(0, total_kills - len(members)) * 0.5)
        context = 1.5 if any(m["low_hp"] for m in members) else 0.0
        total = round(peak + mass + density + variety + clutch + fight
                      + context, 2)
        rows.append({
            "scene_score": total, "demo": demo, "round": rnd,
            "kills": len(members), "span_s": round(span_s, 1),
            "peak": peak, "mass": round(mass, 1),
            "density": round(density, 1), "variety": round(variety, 1),
            "clutch": clutch, "fight_intensity": fight,
            "total_kills_window": total_kills, "context": context,
            "weapons": ",".join(sorted(w or "" for w in weapons)),
            "capture_start_ms": members[0]["t"] - 5000,
            "capture_end_ms": members[-1]["t"] + 4000,
            "member_ids": json.dumps([m["id"] for m in members]),
        })
    rows.sort(key=lambda r: -r["scene_score"])

    # write scene score back onto member rows (idempotent overwrite)
    for r in rows:
        for mid in json.loads(r["member_ids"]):
            row = conn.execute("SELECT attributes FROM recognized_frags"
                               " WHERE id=?", (mid,)).fetchone()
            a = json.loads(row["attributes"] or "{}")
            if a.get("scene_score") != r["scene_score"]:
                a["scene_score"] = r["scene_score"]
                a["scene_round"] = r["round"]
                conn.execute("UPDATE recognized_frags SET attributes=?"
                             " WHERE id=?", (json.dumps(a), mid))
    conn.commit()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "top_scenes_ca.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows[:top_n])
    (OUT_DIR / "top_scenes_ca.json").write_text(
        json.dumps(rows[:top_n], indent=1), encoding="utf-8")
    conn.close()
    return {"scenes": len(rows), "exported": min(top_n, len(rows)),
            "wall_s": round(time.time() - t0, 1),
            "top3": [(r["scene_score"], r["demo"], r["round"], r["kills"],
                      r["span_s"]) for r in rows[:3]]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
