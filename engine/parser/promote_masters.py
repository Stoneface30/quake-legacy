"""Promoted master pool for the V2 fragmovie (mandate 5-12, 37-39).

Combines the definitive Top 50, top CA round scenes, and category
specialists into ONE deduplicated promotion manifest with capture tiers.
A frag that lives inside a promoted scene is covered by that SCENE_MASTER
(one gameplay moment = one capture); its reasons attach to the scene.

Ledger: rows are inserted into demo_v2.db generated_clips (the proven
capture ledger — capture_batch_run.py consumes CANDIDATE rows by
rank_score), tier S+ encoded as rank boost so S+ captures first.
Manifest: output/demo_v2/promoted_master_pool.json.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"
REC_DIR = REPO_ROOT / "output" / "demo_v2" / "recognition"
POOL_OUT = REPO_ROOT / "output" / "demo_v2" / "promoted_master_pool.json"

TOP_SCENES = 14
CATEGORY_LISTS = ["top_air_rockets", "top_direct_rockets",
                  "top_prediction_projectiles", "top_air_grenades",
                  "top_pixel_shots", "top_lg_tracking",
                  "top_lg_dodge_and_frag", "top_high_speed_frags",
                  "top_fast_multikills"]
SPECIALISTS_PER_LIST = 3
FRAG_PRE_MS, FRAG_POST_MS = 4500, 4000

RENDER_PROOFED_KEYS = {  # top-4 pixel shots with visual proof strips
    "50e15ff20072b57c557f7ac5bda8d0f339690e8849cc56bdf7d45444ae738945",
    "c15c22a2a976024eeaec352eb1920db16a8e58c0780e9f767130e3a2eb39f01c",
    "e64425a4437d30f1ba36475493c0d1e665c179ac9398d8cd6099e73dbde288d3",
    "ce23f4cb2d1eb545fd08d485bc1830d234e5e962576cc5b5d9fc1a231be7a888",
}


def render_proof_key(demo: str, server_time_ms: int) -> str:
    """Stable anonymous identity for a visually proofed demo moment."""
    raw = f"{demo}\0{int(server_time_ms)}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def is_render_proofed(demo: str, server_time_ms: int) -> bool:
    return render_proof_key(demo, server_time_ms) in RENDER_PROOFED_KEYS


def tier_of(kind: str, score: float, classes: set, demo: str, t: int) -> str:
    if kind == "scene":
        return "S+" if score >= 60 else ("S" if score >= 48 else "A")
    if is_render_proofed(demo, t):
        return "S+"
    if score >= 40 or ("CLUTCH_1V4_PLUS" in classes and score >= 28):
        return "S+"
    if score >= 28:
        return "S"
    return "A"


def run() -> dict:
    conn = sqlite3.connect(f"file:{RECOG_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    fconn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    hash_of = {n: (dup or h) for n, h, dup in fconn.execute(
        "SELECT name, content_hash, duplicate_of FROM demos")}
    map_of = dict(fconn.execute("SELECT name, map_name FROM demos"))
    fconn.close()

    def frag_row(demo: str, t: int) -> dict | None:
        r = conn.execute(
            "SELECT * FROM recognized_frags WHERE demo_name=? AND"
            " server_time_ms=?", (demo, t)).fetchone()
        return dict(r) if r else None

    pool: list[dict] = []
    covered: list[tuple[str, int, int]] = []   # (hash, start, end) intervals

    def add_scene(s: dict, reason: str):
        h = hash_of.get(s["demo"])
        covered.append((h, s["capture_start_ms"], s["capture_end_ms"]))
        pool.append({
            "kind": "scene", "demo": s["demo"], "hash": h,
            "map": map_of.get(s["demo"]),
            "round": s["round"], "score": s["scene_score"],
            "capture_start_ms": s["capture_start_ms"],
            "capture_end_ms": s["capture_end_ms"],
            "kills": s["kills"], "weapons": s["weapons"],
            "member_ids": s["member_ids"],
            "reasons": [reason, f"scene {s['scene_score']}"
                        f" ({s['kills']} kills/{s['span_s']}s)"],
            "tier": tier_of("scene", s["scene_score"], set(), s["demo"], 0),
        })

    def add_frag(demo: str, t: int, reason: str) -> bool:
        h = hash_of.get(demo)
        for ch, cs, ce in covered:
            if ch == h and cs - 500 <= t <= ce + 500:
                for p in pool:      # attach reason to the covering record
                    if p["hash"] == h and p["capture_start_ms"] - 500 <= t \
                            <= p["capture_end_ms"] + 500:
                        if reason not in p["reasons"]:
                            p["reasons"].append(reason)
                        return False
                return False
        r = frag_row(demo, t)
        if r is None:
            return False
        a = json.loads(r["attributes"] or "{}")
        classes = {x["name"] if isinstance(x, dict) else x
                   for x in json.loads(r["classes"] or "[]")}
        start, end = t - FRAG_PRE_MS, t + FRAG_POST_MS
        covered.append((h, start, end))
        pool.append({
            "kind": "frag", "demo": demo, "hash": h,
            "map": map_of.get(demo), "round": r["round"],
            "score": r["highlight_score"],
            "capture_start_ms": max(0, start), "capture_end_ms": end,
            "server_time_ms": t, "weapon": r["weapon_name"],
            "classes": sorted(classes),
            "reasons": [reason] + json.loads(r["reasons"] or "[]")[:6],
            "render_proofed": is_render_proofed(demo, t),
            "tier": tier_of("frag", r["highlight_score"] or 0, classes,
                            demo, t),
            "mode_pool": a.get("mode_pool"),
        })
        return True

    # B first: scenes claim their intervals so member frags dedup onto them
    scenes = json.loads((REC_DIR / "top_scenes_ca.json").read_text())
    for s in scenes[:TOP_SCENES]:
        add_scene(s, "top CA scene")

    # A: definitive top 50
    for row in csv.DictReader(open(REC_DIR / "top_50_ca_definitive.csv",
                                   encoding="utf-8")):
        if int(row["rank"]) > 50:
            break
        add_frag(row["demo"], int(row["server_time_ms"]),
                 f"top50 #{row['rank']}")

    # C: category specialists (discovery views — composite score still rules
    # the tier; these only ADD moments the overall list missed)
    for lst in CATEGORY_LISTS:
        p = REC_DIR / f"{lst}.csv"
        if not p.exists():
            continue
        added = 0
        for row in csv.DictReader(open(p, encoding="utf-8")):
            if added >= SPECIALISTS_PER_LIST:
                break
            demo = row.get("demo") or row.get("demo_name")
            t = int(row.get("t") or row.get("server_time_ms"))
            if add_frag(demo, t, f"specialist:{lst}"):
                added += 1

    # D: side-mode specials — only truly exceptional
    for lst, cap in (("top_duel", 1), ("top_other", 1)):
        p = REC_DIR / f"{lst}.csv"
        if not p.exists():
            continue
        for row in list(csv.DictReader(open(p, encoding="utf-8")))[:cap]:
            if float(row["score"]) >= 30:
                add_frag(row["demo"], int(row["server_time_ms"]),
                         f"side-mode special ({lst})")

    conn.close()
    pool.sort(key=lambda p: ({"S+": 0, "S": 1, "A": 2}[p["tier"]],
                             -(p["score"] or 0)))
    tiers = {}
    for p in pool:
        tiers[p["tier"]] = tiers.get(p["tier"], 0) + 1
    manifest = {
        "built_at": "2026-08-31",
        "capture_profile_id": "f41599fcfdee",
        "unique_masters": len(pool),
        "tiers": tiers,
        "scenes": sum(1 for p in pool if p["kind"] == "scene"),
        "frags": sum(1 for p in pool if p["kind"] == "frag"),
        "pool": pool,
    }
    POOL_OUT.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return {k: v for k, v in manifest.items() if k != "pool"}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
