"""Recorder capture windows for V2 clip generation (charter §5, §6, §9, §17).

Groups the ranked recorder kills (master_seek_recorder.csv) into capture
windows with generous context, extends windows to cover whole clutches
(clutch_recorder.csv, joined on canonical demo hash), keeps every kill offset
for hit-to-beat, and emits ranked top-20/50/100 lists plus the full set.
Top-100 candidates are inserted into demo_v2.db as promotion CANDIDATEs.

Usage:
    python -u engine/parser/capture_windows.py
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"
SEEK_CSV = REPO_ROOT / "output" / "master_seek_recorder.csv"
CLUTCH_CSV = REPO_ROOT / "output" / "clutch_recorder.csv"
OUT_DIR = REPO_ROOT / "output" / "demo_v2"

CHAIN_GAP_MS = 5_000
PRE_MS = 5_000
POST_MS = 3_000
POST_CLUTCH_MS = 4_000

ACTION_TAGS = {"airshot", "air_rocket", "airborne_kill", "rocketjump_frag",
               "air_combo", "big_flick", "high_acc_shaft"}


def dedupe_clutches(clutches: list[dict]) -> list[dict]:
    """Drop clutch rows duplicated across duplicate demo files."""
    seen, out = set(), []
    for c in clutches:
        key = (c["canonical_demo_hash"], int(c["round"]), int(c["clutch_start_ms"]))
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def _chain(kills: list[dict]) -> list[list[dict]]:
    kills = sorted(kills, key=lambda k: int(k["server_time_ms"]))
    groups, cur = [], [kills[0]]
    for k in kills[1:]:
        if int(k["server_time_ms"]) - int(cur[-1]["server_time_ms"]) <= CHAIN_GAP_MS:
            cur.append(k)
        else:
            groups.append(cur)
            cur = [k]
    groups.append(cur)
    return groups


def _mk_window(group: list[dict]) -> dict:
    times = [int(k["server_time_ms"]) for k in group]
    return {
        "kills": group,
        "capture_start_ms": times[0] - PRE_MS,
        "capture_end_ms": times[-1] + POST_MS,
        "clutch": None,
    }


def _finalize(w: dict, demo_hash: str | None) -> dict:
    group = sorted(w["kills"], key=lambda k: int(k["server_time_ms"]))
    start = max(0, w["capture_start_ms"])
    end = w["capture_end_ms"]
    best = max(group, key=lambda k: float(k["rank_score"]))
    scores = sorted((float(k["rank_score"]) for k in group), reverse=True)
    score = scores[0] + 0.5 * sum(scores[1:])
    clutch = w["clutch"]
    if clutch:
        score += 2.0 * int(clutch["enemies_alive_at_start"])
    tags = sorted({t for k in group for t in (k.get("tags") or "").split(",") if t})
    return {
        "demo": group[0]["demo"],
        "canonical_demo_hash": demo_hash,
        "map": group[0].get("map_name", ""),
        "round": int(best["round"]) if best.get("round") not in (None, "") else None,
        "server_time_ms": int(best["server_time_ms"]),
        "clock_start": _clock(best, start),
        "clock_end": _clock(best, end),
        "capture_start_ms": start,
        "capture_end_ms": end,
        "duration_s": round((end - start) / 1000.0, 2),
        "n_kills": len(group),
        "weapon": best.get("weapon_name", ""),
        "weapons": ",".join(sorted({k.get("weapon_name", "") for k in group})),
        "tags": ",".join(tags),
        "frag_offsets_ms": json.dumps(
            [int(k["server_time_ms"]) - start for k in group]),
        "score": round(score, 2),
        "clutch_context": json.dumps({
            "enemies_alive_at_start": int(clutch["enemies_alive_at_start"]),
            "kills_during_clutch": int(clutch["kills_during_clutch"]),
            "weapons": clutch["weapons"],
            "outcome": clutch["outcome"],
            "clutch_rank_score": float(clutch["rank_score"]),
        }) if clutch else None,
    }


def _clock(ref_kill: dict, t_ms: int) -> str:
    """Render demo clock at t_ms using the reference kill's clock anchor.

    CA clocks count DOWN, so clock = ref_clock + (ref_time - t) in seconds.
    Falls back to raw seconds if the anchor clock is unparsable.
    """
    ref_t = int(ref_kill["server_time_ms"])
    raw = ref_kill.get("clock") or ""
    try:
        mm, ss = raw.split(":")
        ref_clock_s = int(mm) * 60 + int(ss)
    except ValueError:
        s = max(0, t_ms) // 1000
        return f"~{s // 60}:{s % 60:02d}"
    clock_s = max(0, ref_clock_s + (ref_t - t_ms) // 1000)
    return f"{clock_s // 60}:{clock_s % 60:02d}"


def build_windows(kills: list[dict], clutches: list[dict] | None = None,
                  demo_hash: str | None = None) -> list[dict]:
    """Build finalized capture windows for one demo's recorder kills."""
    if not kills:
        return []
    windows = [_mk_window(g) for g in _chain(kills)]

    for c in clutches or []:
        if demo_hash is None or c["canonical_demo_hash"] != demo_hash:
            continue
        cs, ce = int(c["clutch_start_ms"]), int(c["clutch_end_ms"])
        for w in windows:
            if any(cs <= int(k["server_time_ms"]) <= ce for k in w["kills"]):
                w["capture_start_ms"] = min(w["capture_start_ms"], cs - PRE_MS)
                w["capture_end_ms"] = max(w["capture_end_ms"], ce + POST_CLUTCH_MS)
                w["clutch"] = c

    # Post-extension re-merge of overlapping windows (single pass over sorted)
    windows.sort(key=lambda w: w["capture_start_ms"])
    merged = [windows[0]]
    for w in windows[1:]:
        prev = merged[-1]
        if w["capture_start_ms"] <= prev["capture_end_ms"]:
            prev["kills"].extend(w["kills"])
            prev["capture_start_ms"] = min(prev["capture_start_ms"], w["capture_start_ms"])
            prev["capture_end_ms"] = max(prev["capture_end_ms"], w["capture_end_ms"])
            prev["clutch"] = prev["clutch"] or w["clutch"]
        else:
            merged.append(w)

    return [_finalize(w, demo_hash) for w in merged]


def assign_classes(windows: list[dict]) -> None:
    scores = sorted((w["score"] for w in windows), reverse=True)
    if not scores:
        return
    p99 = scores[max(0, len(scores) // 100 - 1)]
    p95 = scores[max(0, len(scores) * 5 // 100 - 1)]
    for w in windows:
        if w["clutch_context"]:
            w["class"] = "CLUTCH_PREMIUM"
        elif w["score"] >= p99:
            w["class"] = "T1_NEW"
        elif w["score"] >= p95:
            w["class"] = "T2_NEW"
        elif set((w["tags"] or "").split(",")) & ACTION_TAGS:
            w["class"] = "ACTION_PREMIUM"
        else:
            w["class"] = ""


def run() -> dict:
    conn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    demo_info = {}
    for name, h, size, rc, dup in conn.execute(
            "SELECT name, content_hash, size_bytes, recorder_client, duplicate_of FROM demos"):
        demo_info[name] = (dup or h, size, rc)
    conn.close()

    with open(SEEK_CSV, newline="", encoding="utf-8") as f:
        seek = list(csv.DictReader(f))
    with open(CLUTCH_CSV, newline="", encoding="utf-8") as f:
        clutches = dedupe_clutches(list(csv.DictReader(f)))

    clutch_by_hash: dict[str, list[dict]] = {}
    for c in clutches:
        clutch_by_hash.setdefault(c["canonical_demo_hash"], []).append(c)

    by_demo: dict[str, list[dict]] = {}
    for k in seek:
        by_demo.setdefault(k["demo"], []).append(k)

    windows: list[dict] = []
    for demo, kills in by_demo.items():
        h = demo_info.get(demo, (None, None, None))[0]
        windows.extend(build_windows(kills, clutch_by_hash.get(h, []), h))

    assign_classes(windows)
    windows.sort(key=lambda w: w["score"], reverse=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(windows[0].keys()) + ["class"] if windows else []
    fields = list(dict.fromkeys([*windows[0].keys()])) if windows else []

    def write_csv(path: Path, rows: list[dict]):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    write_csv(OUT_DIR / "capture_windows_full.csv", windows)
    with open(OUT_DIR / "capture_windows_full.json", "w", encoding="utf-8") as f:
        json.dump(windows, f, indent=1)
    for n in (20, 50, 100):
        write_csv(OUT_DIR / f"capture_windows_top{n}.csv", windows[:n])

    # Insert top-100 as promotion candidates
    sys.path.insert(0, str(REPO_ROOT))
    from creative_suite.database import demo_v2_db
    dconn = demo_v2_db.connect()
    dconn.execute("DELETE FROM generated_clips WHERE promotion_status='CANDIDATE' AND avi_path IS NULL")
    dconn.commit()
    for w in windows[:100]:
        info = demo_info.get(w["demo"], (None, None, None))
        demo_v2_db.insert_candidate(dconn, {
            "demo_name": w["demo"],
            "canonical_demo_hash": w["canonical_demo_hash"],
            "server_time_ms": w["server_time_ms"],
            "round": w["round"],
            "capture_start_ms": w["capture_start_ms"],
            "capture_end_ms": w["capture_end_ms"],
            "frag_offsets_ms": w["frag_offsets_ms"],
            "recorder_client": info[2],
            "weapon": w["weapon"],
            "tags": w["tags"],
            "rank_score": w["score"],
            "class": w["class"] or "T2_NEW",
            "clutch_context": w["clutch_context"],
            "source_size_bytes": info[1],
        })
    dconn.close()

    counts = {}
    for w in windows:
        counts[w["class"] or "UNCLASSED"] = counts.get(w["class"] or "UNCLASSED", 0) + 1
    return {"windows": len(windows), "class_counts": counts,
            "top_score": windows[0]["score"] if windows else 0}


if __name__ == "__main__":
    s = run()
    print(f"windows: {s['windows']}  top_score: {s['top_score']}")
    for k, v in sorted(s["class_counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:16s} {v}")
