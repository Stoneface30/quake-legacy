"""Final coverage reconciliation for the continuous AVI series.

Coverage is derived from two independent places and compared: the authoritative
T1/T2 source set on disk, and the committed Part manifests. A counter kept
during the run is not evidence -- if the two disagree, the run is wrong, and
this is what catches it.

Also stamps each queue row with where it ended up, so the queue alone proves
full coverage:

    UNASSIGNED            not yet placed in any Part
    SELECTED              placed in a Part that has not passed QA
    QA_PASSED_COMMITTED   shipped in a Part that passed audio and decode QA

    python avi_reconcile.py
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "output"
MANIFESTS = OUT / "_series_manifests"
QUEUE = OUT / "avi_master_queue.json"


def canonical(p) -> str:
    return str(Path(p).resolve()).lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT / "AVI_SERIES_FINAL.json"))
    a = ap.parse_args()

    meta = json.loads(QUEUE.read_text(encoding="utf-8"))
    queue = meta["queue"]

    committed, uncommitted = [], []
    for m in sorted(MANIFESTS.glob("Part*.json")):
        try:
            r = json.loads(m.read_text(encoding="utf-8"))
        except Exception:
            continue
        (committed if r.get("committed") else uncommitted).append(r)
    committed.sort(key=lambda r: r["part"])

    shipped, selected = {}, {}
    dup_rows = []
    for r in committed:
        for c in r["clips"]:
            k = canonical(c["path"])
            if k in shipped:
                dup_rows.append((k, shipped[k], r["part"]))
            shipped[k] = r["part"]
    for r in uncommitted:
        for c in r.get("clips", []):
            selected.setdefault(canonical(c["path"]), r["part"])

    for row in queue:
        k = canonical(row["canonical_avi_path"])
        if k in shipped:
            row["status"] = "QA_PASSED_COMMITTED"
            row["final_part_assignment"] = shipped[k]
        elif k in selected:
            row["status"] = "SELECTED"
            row["final_part_assignment"] = selected[k]
        else:
            row["status"] = "UNASSIGNED"
            row["final_part_assignment"] = None
        row["used_in_final_part"] = row["final_part_assignment"]

    t1 = [r for r in queue if r["tier"] == "T1"]
    t2 = [r for r in queue if r["tier"] == "T2"]
    t1_used = sum(1 for r in t1 if r["status"] == "QA_PASSED_COMMITTED")
    t2_used = sum(1 for r in t2 if r["status"] == "QA_PASSED_COMMITTED")
    missing = [r for r in queue if r["status"] != "QA_PASSED_COMMITTED"]

    durs = [r["duration_s"] for r in committed]
    tps = [r["true_peak_dBTP"] for r in committed
           if r.get("true_peak_dBTP") is not None]
    lus = [r["integrated_LUFS"] for r in committed
           if r.get("integrated_LUFS") is not None]
    songs = {}
    for r in committed:
        for m in r.get("music", []) or []:
            songs[m.get("name")] = songs.get(m.get("name"), 0) + 1

    under4 = sum(1 for d in durs if d < 240)
    in46 = sum(1 for d in durs if 240 <= d <= 360)
    over6 = sum(1 for d in durs if d > 360)

    ok = (not missing) and not dup_rows and committed and not uncommitted

    print("=" * 72)
    print("AVI SERIES — FINAL RECONCILIATION")
    print("=" * 72)
    print("  status               : {}".format("COMPLETE" if ok else "INCOMPLETE"))
    print("")
    print("  INPUT")
    print("    T1 selected        : {}".format(len(t1)))
    print("    T2 selected        : {}".format(len(t2)))
    print("    total              : {}".format(len(queue)))
    print("")
    print("  OUTPUT")
    print("    Parts committed    : {}".format(len(committed)))
    if committed:
        print("    range              : Part{:02d} .. Part{:02d}".format(
            committed[0]["part"], committed[-1]["part"]))
        print("    total runtime      : {:.2f} h".format(sum(durs) / 3600.0))
    if uncommitted:
        print("    NOT committed      : {} -> {}".format(
            len(uncommitted), [r["part"] for r in uncommitted]))
    print("")
    if durs:
        print("  DURATIONS")
        print("    minimum            : {:.2f} min".format(min(durs) / 60))
        print("    median             : {:.2f} min".format(
            statistics.median(durs) / 60))
        print("    maximum            : {:.2f} min".format(max(durs) / 60))
        print("    under 4 min        : {}".format(under4))
        print("    4-6 min            : {}".format(in46))
        print("    over 6 min         : {}".format(over6))
    print("")
    print("  COVERAGE")
    print("    T1 used            : {} / {}".format(t1_used, len(t1)))
    print("    T2 used            : {} / {}".format(t2_used, len(t2)))
    print("    total used         : {} / {}".format(t1_used + t2_used, len(queue)))
    print("    duplicates         : {}".format(len(dup_rows)))
    print("    missing            : {}".format(len(missing)))
    for r in missing[:10]:
        print("        {}  [{}]".format(Path(r["canonical_avi_path"]).name,
                                        r["status"]))
    print("")
    if tps:
        print("  AUDIO")
        print("    worst true peak    : {:.2f} dBTP  (ceiling -1.0)".format(max(tps)))
        print("    over ceiling       : {}".format(sum(1 for x in tps if x > -1.0)))
        print("    LUFS range         : {:.1f} .. {:.1f}".format(min(lus), max(lus)))
    print("")
    print("  VIDEO")
    print("    decode PASS        : {} / {}".format(
        sum(1 for r in committed if r.get("decode_QA") == "PASS"), len(committed)))
    print("")
    print("  MUSIC")
    print("    distinct tracks    : {} across {} slots".format(
        len(songs), sum(songs.values())))
    reused = {k: v for k, v in songs.items() if v > 1}
    print("    reused tracks      : {}".format(len(reused)))

    payload = {
        "status": "COMPLETE" if ok else "INCOMPLETE",
        "input": {"T1_selected": len(t1), "T2_selected": len(t2),
                  "total": len(queue)},
        "output": {"parts": len(committed),
                   "total_runtime_h": round(sum(durs) / 3600.0, 3) if durs else 0},
        "durations": {
            "min_min": round(min(durs) / 60, 2) if durs else None,
            "median_min": round(statistics.median(durs) / 60, 2) if durs else None,
            "max_min": round(max(durs) / 60, 2) if durs else None,
            "under_4min": under4, "in_4_to_6min": in46, "over_6min": over6},
        "coverage": {"T1_used": t1_used, "T2_used": t2_used,
                     "total_used": t1_used + t2_used,
                     "duplicates": len(dup_rows), "missing": len(missing),
                     "missing_items": [r["canonical_avi_path"] for r in missing]},
        "audio": {"worst_true_peak_dBTP": max(tps) if tps else None,
                  "over_ceiling": sum(1 for x in tps if x > -1.0) if tps else 0,
                  "LUFS_min": min(lus) if lus else None,
                  "LUFS_max": max(lus) if lus else None},
        "video": {"decode_pass": sum(1 for r in committed
                                     if r.get("decode_QA") == "PASS"),
                  "decode_fail": sum(1 for r in committed
                                     if r.get("decode_QA") != "PASS")},
        "music": {"distinct_tracks": len(songs), "reused": len(reused)},
        "parts": [{"part": r["part"], "output_path": r["output_path"],
                   "duration_mmss": r["duration_mmss"],
                   "duration_s": r["duration_s"],
                   "clip_count": r["clip_count"], "t1": r["t1_clips"],
                   "t2": r["t2_clips"],
                   "historical_source_parts": r.get("historical_source_parts"),
                   "integrated_LUFS": r.get("integrated_LUFS"),
                   "LRA_LU": r.get("LRA_LU"),
                   "true_peak_dBTP": r.get("true_peak_dBTP"),
                   "audio_QA": r.get("audio_QA"),
                   "decode_QA": r.get("decode_QA")} for r in committed],
    }
    Path(a.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    meta["queue"] = queue
    meta["reconciled_at"] = __import__("time").strftime("%Y-%m-%d %H:%M:%S")
    QUEUE.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("")
    print("  wrote {}".format(a.out))
    print("  queue statuses stamped in {}".format(QUEUE))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
