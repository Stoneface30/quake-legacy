"""Audit: old simplified-key dedup vs match-fingerprint dedup.

The v1 key (map, server_time_ms, n_kills, frag_offsets_ms) could merge
unrelated matches that coincide on map + serverTime. This audit rebuilds the
pre-dedup window set, applies BOTH strategies, reports the delta, and samples
previously-removed pairs with the fingerprint evidence for each.

Usage:
    python -u engine/parser/dedup_audit.py
Writes output/demo_v2/dedup_audit.json and prints a summary.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import capture_windows as cw


def old_key(w: dict) -> tuple:
    return (w["map"], w["server_time_ms"], w["n_kills"], w["frag_offsets_ms"])


def run() -> dict:
    windows, match_group, _ = cw.prepare()

    # --- old strategy: global signature key ---
    old_groups: dict[tuple, list[dict]] = defaultdict(list)
    for w in windows:
        old_groups[old_key(w)].append(w)
    old_removed_pairs = []       # (kept_demo, removed_demo, key)
    for key, group in old_groups.items():
        if len(group) > 1:
            group_sorted = sorted(
                group, key=lambda w: (w["demo"].startswith("Demo ("), -w["score"]))
            keeper = group_sorted[0]
            for loser in group_sorted[1:]:
                old_removed_pairs.append((keeper, loser, key))
    old_removed = len(old_removed_pairs)

    # --- new strategy: match-fingerprint dedup ---
    new_windows = cw.dedupe_windows(windows, match_group)
    new_removed = len(windows) - len(new_windows)

    # --- classification of every old-removed pair ---
    samples = []
    restored = 0
    confirmed = 0
    for keeper, loser, key in old_removed_pairs:
        gk = match_group.get(keeper["demo"])
        gl = match_group.get(loser["demo"])
        same_match = gk is not None and gk == gl
        if same_match:
            confirmed += 1
        else:
            restored += 1
        samples.append({
            "verdict": "TRUE_DUPLICATE" if same_match else "RESTORED_DISTINCT_MATCH",
            "kept_demo": keeper["demo"],
            "removed_demo": loser["demo"],
            "map": key[0],
            "server_time_ms": key[1],
            "n_kills": key[2],
            "match_group_kept": gk,
            "match_group_removed": gl,
            "evidence": ("same match fingerprint (>=3 shared exact kill tuples "
                         "across all players)" if same_match else
                         "no shared kill tuples between these demos — different "
                         "matches that coincide on map+serverTime signature"),
        })

    # sample: prioritize restored pairs, pad with confirmed duplicates to 20
    samples.sort(key=lambda s: s["verdict"] != "RESTORED_DISTINCT_MATCH")
    sample_20 = samples[:20]

    report = {
        "original_windows": len(windows),
        "old_dedup_removed": old_removed,
        "old_final": len(windows) - old_removed,
        "new_dedup_removed": new_removed,
        "restored_as_distinct_matches": restored,
        "confirmed_true_duplicates": confirmed,
        "final_unique_windows": len(new_windows),
        "note": ("new dedup can remove MORE than old on true duplicates: it "
                 "also merges same-moment windows whose offset signatures "
                 "differ (partial recordings truncating a chain), which the "
                 "old exact-signature key missed."),
        "sampled_pairs": sample_20,
        "all_old_pairs_classified": {
            "TRUE_DUPLICATE": confirmed,
            "RESTORED_DISTINCT_MATCH": restored,
        },
    }
    out = Path(cw.OUT_DIR) / "dedup_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    return report


if __name__ == "__main__":
    r = run()
    for k in ("original_windows", "old_dedup_removed", "new_dedup_removed",
              "restored_as_distinct_matches", "confirmed_true_duplicates",
              "final_unique_windows"):
        print(f"{k:32s} {r[k]}")
    print("\nSampled pairs:")
    for s in r["sampled_pairs"]:
        print(f"  [{s['verdict']}] {s['removed_demo']} vs {s['kept_demo']} "
              f"@ {s['map']}/{s['server_time_ms']}")
