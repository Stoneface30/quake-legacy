"""Build the first capture batch (charter capture-phase §6-§8, §20).

Primary: top-100 windows by corrected ranking with light diversity —
quality first, diversity only breaks near-ties. Supplement: top-50 recorder
clutches not already substantially represented. Tiers S/A/B assigned per the
priority-class rules; exceptional moments flagged ALT_ANGLE_WORTHY for the
later cinematic pass. Result rows land in demo_v2.db as CANDIDATEs with full
provenance (victims/MODs per kill from frags_rebuilt.db).

Usage:
    python -u engine/parser/promotion_batch.py
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"
OUT_DIR = REPO_ROOT / "output" / "demo_v2"
CLUTCH_CSV = REPO_ROOT / "output" / "clutch_recorder.csv"

PRIMARY_N = 100
NEAR_TIE_EPS = 1.5          # score gap treated as a near-tie
DIVERSITY_LOOKAHEAD = 12    # candidates considered inside a near-tie band

PLAYER = "Tr4sH"
CLAN = "pTn"


def _ctx(w: dict) -> dict | None:
    c = w.get("clutch_context")
    if not c:
        return None
    return json.loads(c) if isinstance(c, str) else c


def assign_tier(w: dict) -> str:
    """S/A/B priority classes (capture-phase §8)."""
    ctx = _ctx(w)
    tags = set((w.get("tags") or "").split(","))
    n_kills = int(w["n_kills"])
    weapons = [x for x in (w.get("weapons") or "").split(",") if x]
    score = float(w["score"])
    if ctx and int(ctx["enemies_alive_at_start"]) >= 4:
        return "S"
    if n_kills >= 4:
        return "S"
    if ctx and len([x for x in (ctx.get("weapons") or "").split(",") if x]) >= 3:
        return "S"
    if {"air_rocket", "airshot"} & tags and score >= 25:
        return "S"
    if ctx and int(ctx["enemies_alive_at_start"]) >= 2:
        return "A"
    if n_kills >= 3:
        return "A"
    if "RAILGUN" in weapons and n_kills >= 2:
        return "A"
    if {"shaft_rocket", "rocket_shaft", "big_flick", "air_combo"} & tags:
        return "A"
    if score >= 20:
        return "A"
    return "B"


def alt_angle_worthy(w: dict) -> bool:
    """Exceptional S-tier moments worth a later alternate-angle pass (§20)."""
    if assign_tier(w) != "S":
        return False
    ctx = _ctx(w)
    tags = set((w.get("tags") or "").split(","))
    return bool({"air_rocket", "airshot", "big_flick"} & tags
                or (ctx and int(ctx["enemies_alive_at_start"]) >= 4)
                or int(w["n_kills"]) >= 5)


def _year(w: dict) -> str:
    d = w.get("demo", "")
    for part in d.replace("-", "_").split("_"):
        if part.isdigit() and len(part) == 4 and part.startswith("20"):
            return part
    return "unknown"


def select_diverse(windows: list[dict], n: int = PRIMARY_N) -> list[dict]:
    """Greedy top-N: highest score wins outright; inside a near-tie band the
    candidate adding most variety (map, weapon, class, year) is preferred.
    Never demotes a clearly higher-scored window."""
    remaining = sorted(windows, key=lambda w: -float(w["score"]))
    picked: list[dict] = []
    seen: dict[str, dict] = {"map": {}, "weapon": {}, "class": {}, "year": {}}

    def redundancy(w: dict) -> int:
        return (2 * seen["map"].get(w["map"], 0)
                + 2 * seen["weapon"].get(w["weapon"], 0)
                + seen["class"].get(w["class"], 0)
                + seen["year"].get(_year(w), 0))

    while remaining and len(picked) < n:
        best_score = float(remaining[0]["score"])
        band_end = 1
        while (band_end < len(remaining) and band_end < DIVERSITY_LOOKAHEAD
               and best_score - float(remaining[band_end]["score"]) <= NEAR_TIE_EPS):
            band_end += 1
        band = remaining[:band_end]
        choice = min(band, key=lambda w: (redundancy(w), -float(w["score"])))
        picked.append(choice)
        remaining.remove(choice)
        seen["map"][choice["map"]] = seen["map"].get(choice["map"], 0) + 1
        seen["weapon"][choice["weapon"]] = seen["weapon"].get(choice["weapon"], 0) + 1
        seen["class"][choice["class"]] = seen["class"].get(choice["class"], 0) + 1
        y = _year(choice)
        seen["year"][y] = seen["year"].get(y, 0) + 1
    return picked


def clutch_supplement(picked: list[dict], all_windows: list[dict],
                      clutches: list[dict], top_n_clutches: int = 50) -> list[dict]:
    """Top clutches not substantially represented in the picked set.

    A clutch is represented when a picked window from the same canonical demo
    hash overlaps [clutch_start, clutch_end]. For missing ones, the matching
    CLUTCH_PREMIUM window from the full set is promoted."""
    def covered(c: dict, pool: list[dict]) -> bool:
        for w in pool:
            if w.get("canonical_demo_hash") != c["canonical_demo_hash"]:
                continue
            if (int(w["capture_start_ms"]) <= int(c["clutch_end_ms"])
                    and int(w["capture_end_ms"]) >= int(c["clutch_start_ms"])):
                return True
        return False

    top = sorted(clutches, key=lambda c: -float(c["rank_score"]))[:top_n_clutches]
    extra: list[dict] = []
    for c in top:
        if covered(c, picked) or covered(c, extra):
            continue
        match = [w for w in all_windows
                 if w.get("canonical_demo_hash") == c["canonical_demo_hash"]
                 and int(w["capture_start_ms"]) <= int(c["clutch_end_ms"])
                 and int(w["capture_end_ms"]) >= int(c["clutch_start_ms"])]
        if match:
            extra.append(max(match, key=lambda w: float(w["score"])))
    return extra


def load_kill_details(conn, demo: str, kill_times: list[int]) -> tuple[list, list]:
    """Victim names and MOD ints for the recorder kills at given serverTimes."""
    victims, mods = [], []
    for t in kill_times:
        row = conn.execute(
            "SELECT victim_name, mod FROM frags WHERE demo_name=? AND"
            " server_time_ms=? AND by_recorder=1 LIMIT 1", (demo, t)).fetchone()
        victims.append(row[0] if row else None)
        mods.append(row[1] if row else None)
    return victims, mods


def run() -> dict:
    with open(OUT_DIR / "capture_windows_full.json", encoding="utf-8") as f:
        windows = json.load(f)
    with open(CLUTCH_CSV, newline="", encoding="utf-8") as f:
        raw_clutches = list(csv.DictReader(f))
    # dedupe clutch rows by signature (duplicate demo files)
    seen = set()
    clutches = []
    for c in raw_clutches:
        k = (c["canonical_demo_hash"], c["round"], c["clutch_start_ms"])
        if k not in seen:
            seen.add(k)
            clutches.append(c)

    primary = select_diverse(windows, PRIMARY_N)
    extra = clutch_supplement(primary, windows, clutches)
    batch = primary + extra
    for w in batch:
        w["tier"] = assign_tier(w)
        w["alt_angle_worthy"] = int(alt_angle_worthy(w))

    conn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    demo_meta = {name: (rc, rn) for name, rc, rn in conn.execute(
        "SELECT name, recorder_client, recorder_name FROM demos")}

    from creative_suite.database import demo_v2_db
    dconn = demo_v2_db.connect()
    dconn.execute("DELETE FROM generated_clips WHERE avi_path IS NULL")
    dconn.commit()
    for w in batch:
        offsets = json.loads(w["frag_offsets_ms"])
        kill_times = [int(w["capture_start_ms"]) + o for o in offsets]
        victims, mods = load_kill_details(conn, w["demo"], kill_times)
        rc, rn = demo_meta.get(w["demo"], (None, None))
        w["generated_clip_id"] = demo_v2_db.insert_candidate(dconn, {
            "demo_name": w["demo"],
            "canonical_demo_hash": w["canonical_demo_hash"],
            "server_time_ms": w["server_time_ms"],
            "round": w["round"],
            "map": w["map"],
            "match_group": w.get("match_group"),
            "capture_start_ms": w["capture_start_ms"],
            "capture_end_ms": w["capture_end_ms"],
            "frag_offsets_ms": w["frag_offsets_ms"],
            "primary_frag_offset_ms": int(w["server_time_ms"]) - int(w["capture_start_ms"]),
            "recorder_client": rc,
            "recorder_name": rn,
            "clan": CLAN,
            "weapon": w["weapon"],
            "tags": w["tags"],
            "victims": json.dumps(victims),
            "mods": json.dumps(mods),
            "rank_score": w["score"],
            "class": w["class"],
            "tier": w["tier"],
            "alt_angle_worthy": w["alt_angle_worthy"],
            "clutch_context": w["clutch_context"],
            "promotion_reason": f"batch1 {w['class']} score={w['score']}",
        })
    dconn.close()
    conn.close()

    out = OUT_DIR / "capture_batch.json"
    out.write_text(json.dumps(batch, indent=1), encoding="utf-8")

    tiers = {}
    for w in batch:
        tiers[w["tier"]] = tiers.get(w["tier"], 0) + 1
    report = {
        "primary_requested": PRIMARY_N,
        "clutch_supplement": len(extra),
        "batch_total": len(batch),
        "tiers": tiers,
        "alt_angle_worthy": sum(w["alt_angle_worthy"] for w in batch),
        "distinct_demos": len({w["demo"] for w in batch}),
        "distinct_maps": len({w["map"] for w in batch}),
    }
    (OUT_DIR / "capture_batch_report.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")
    return report


if __name__ == "__main__":
    r = run()
    for k, v in r.items():
        print(f"{k:20s} {v}")
