"""Scan all Part 4 body chunks and build a diversity ledger.

Writes:
  output/part04_event_diversity.json
  output/part04_recognition_report.md
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phase1.audio_onsets import (  # noqa: E402
    DEFAULT_CONF_THRESHOLD,
    EVENT_WEIGHTS,
    SoundLibrary,
    _compute_clip_envelope,
    _match_template,
    recognize_game_events,
)

CHUNK_DIR = ROOT / "output" / "_part04_v6_body_chunks"
LEDGER_PATH = ROOT / "output" / "part04_event_diversity.json"
REPORT_PATH = ROOT / "output" / "part04_recognition_report.md"

FOCUS_TYPES = [
    "player_death",
    "rail_fire",
    "rocket_fire",
    "rocket_impact",
    "grenade_explode",
    "grenade_direct",
    "grenade_throw",
    "lg_hit",
    "shotgun_fire",
    "plasma_impact",
]


def main() -> int:
    chunks = sorted(p for p in CHUNK_DIR.glob("chunk_*.mp4"))
    if not chunks:
        print(f"no chunks at {CHUNK_DIR}", file=sys.stderr)
        return 2

    lib = SoundLibrary.get()
    print(f"Loaded {len(lib.templates)} templates from library", file=sys.stderr)
    by_type: dict[str, list[str]] = defaultdict(list)
    for tpl in lib.templates:
        by_type[tpl.event_type].append(tpl.path)
    for et, paths in sorted(by_type.items()):
        print(f"  {et}: {len(paths)} variants", file=sys.stderr)

    # Per-clip scan — capture ALL template matches at a LOW floor so we can
    # see raw score distributions per event type even when nothing clears
    # the TIGHT threshold. We still compute the "official" events list at
    # the canonical threshold for the primary counts.
    RAW_FLOOR = 0.30

    clips_any = 0
    clips_failed = 0
    event_counts: Counter[str] = Counter()
    per_type_top: dict[str, list[dict]] = defaultdict(list)
    raw_scores_per_type: dict[str, list[float]] = defaultdict(list)
    per_clip: list[dict] = []

    total = len(chunks)
    for i, clip in enumerate(chunks):
        if i % 10 == 0:
            print(f"[{i}/{total}] {clip.name}", file=sys.stderr)

        # Official (threshold-gated) events
        events = recognize_game_events(clip)
        if events:
            clips_any += 1
        else:
            clips_failed += 1
        for e in events:
            event_counts[e.event_type] += 1
            per_type_top[e.event_type].append({
                "clip": clip.name,
                "confidence": round(e.confidence, 4),
                "t": round(e.t, 3),
            })

        # Raw score collection — one row per template match above RAW_FLOOR.
        # This is what lets us diagnose why a type "fails": we see the raw
        # best score per clip per type regardless of the gate.
        env = _compute_clip_envelope(clip)
        best_per_type: dict[str, tuple[float, float]] = {}
        if env is not None and env.size >= 4:
            for tpl in lib.templates:
                t, conf = _match_template(env, tpl)
                if conf <= 0:
                    continue
                prev = best_per_type.get(tpl.event_type)
                if prev is None or conf > prev[1]:
                    best_per_type[tpl.event_type] = (t, conf)
        for et, (t, conf) in best_per_type.items():
            raw_scores_per_type[et].append(conf)

        per_clip.append({
            "clip": clip.name,
            "n_events_gated": len(events),
            "top_event": events[0]._asdict() if events else None,
            "best_per_type_raw": {k: {"t": round(v[0], 3), "conf": round(v[1], 4)}
                                  for k, v in best_per_type.items()},
        })

    # Build top-5 per event type (by confidence)
    top5 = {}
    for et, hits in per_type_top.items():
        top5[et] = sorted(hits, key=lambda x: -x["confidence"])[:5]

    # Raw score diagnostics (max / mean / p90 per type across corpus)
    import statistics
    raw_stats = {}
    for et, scores in raw_scores_per_type.items():
        if not scores:
            continue
        raw_stats[et] = {
            "max": round(max(scores), 4),
            "mean": round(statistics.mean(scores), 4),
            "p90": round(sorted(scores)[int(0.9 * len(scores))], 4) if len(scores) >= 10 else round(max(scores), 4),
            "n_clips_scored": len(scores),
            "n_over_055": sum(1 for s in scores if s >= 0.55),
            "n_over_045": sum(1 for s in scores if s >= 0.45),
            "n_over_040": sum(1 for s in scores if s >= 0.40),
        }

    ledger = {
        "total_clips": total,
        "clips_with_any_event": clips_any,
        "clips_recognition_failed": clips_failed,
        "gate_threshold": DEFAULT_CONF_THRESHOLD,
        "event_type_counts": dict(event_counts),
        "top_5_per_type": top5,
        "raw_score_stats_per_type": raw_stats,
        "templates_loaded_per_type": {k: len(v) for k, v in by_type.items()},
        "event_weights": EVENT_WEIGHTS,
    }
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    print(f"\nLedger → {LEDGER_PATH}", file=sys.stderr)

    # Markdown report
    lines: list[str] = []
    lines.append("# Part 4 recognition audit")
    lines.append("")
    lines.append(f"Total clips scanned: {total}")
    lines.append(f"Clips with >=1 event at conf>={DEFAULT_CONF_THRESHOLD}: {clips_any}")
    lines.append(f"Clips recognition-failed: {clips_failed}")
    lines.append("")
    lines.append("## Event type counts (gated)")
    for et, c in sorted(event_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {et}: {c}")
    lines.append("")
    lines.append("## Top-5 examples per event type")
    for et in FOCUS_TYPES:
        hits = top5.get(et, [])
        lines.append(f"### {et}")
        if not hits:
            stats = raw_stats.get(et)
            if stats:
                lines.append(
                    f"- (no gated hits) raw max={stats['max']} mean={stats['mean']} "
                    f"n_over_0.45={stats['n_over_045']} n_over_0.40={stats['n_over_040']}"
                )
            else:
                lines.append("- (no templates loaded for this type)")
        else:
            for h in hits:
                lines.append(f"- {h['clip']} @ {h['t']}s conf={h['confidence']}")
        lines.append("")
    lines.append("## Raw score diagnostics per type (across full corpus)")
    for et, stats in sorted(raw_stats.items(), key=lambda x: -x[1]["max"]):
        lines.append(
            f"- **{et}**: max={stats['max']}  mean={stats['mean']}  p90={stats['p90']}  "
            f"n>=0.55:{stats['n_over_055']}  n>=0.45:{stats['n_over_045']}  "
            f"n>=0.40:{stats['n_over_040']}"
        )
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report → {REPORT_PATH}", file=sys.stderr)

    # Concise stdout summary
    print("\n=== SUMMARY ===")
    print(f"{clips_any}/{total} clips had >=1 gated event; {clips_failed} failed")
    print(f"Gated event_type counts: {dict(event_counts)}")
    print(f"Raw-score max per type:")
    for et, stats in sorted(raw_stats.items(), key=lambda x: -x[1]["max"]):
        print(f"  {et}: max={stats['max']}  n>=0.55={stats['n_over_055']}  n>=0.45={stats['n_over_045']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
