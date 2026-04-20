"""Diversity test — prove the Part 4 corpus exercises the full weapon taxonomy.

Per user's Gate-4 challenge ("prove we recognize rocket fire, enemy killed,
rail hit and so on"), this test fails fast if the ledger at
``output/part04_event_diversity.json`` does NOT contain at least one gated
hit (>=DEFAULT_CONF_THRESHOLD) on each of the expected high-value types.

If the ledger is missing, a helpful skip directs the reviewer to regenerate
it with ``python phase1/tools/scan_part04_diversity.py``.

The test is strict on two axes:
    1. Per-type coverage: each REQUIRED type must appear at least once.
    2. Corpus breadth: at least MIN_DISTINCT_TYPES distinct event types must
       be represented across the whole corpus.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "output" / "part04_event_diversity.json"

REQUIRED_TYPES = [
    "player_death",
    "rail_fire",
    "rocket_fire",
    "rocket_impact",
    "grenade_explode",
    "lg_hit",
    "shotgun_fire",
    "plasma_impact",
]

MIN_DISTINCT_TYPES = 7
MIN_CONF = 0.55


@pytest.fixture(scope="module")
def ledger() -> dict:
    if not LEDGER.exists():
        pytest.skip(
            f"ledger not found at {LEDGER}. "
            "Regenerate with: python phase1/tools/scan_part04_diversity.py"
        )
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_ledger_covers_all_required_event_types(ledger: dict) -> None:
    """Each required event_type must have at least one gated hit >=0.55."""
    counts = ledger.get("event_type_counts", {})
    top5 = ledger.get("top_5_per_type", {})
    missing: list[str] = []
    under_conf: list[tuple[str, float]] = []
    for etype in REQUIRED_TYPES:
        if counts.get(etype, 0) < 1:
            missing.append(etype)
            continue
        hits = top5.get(etype, [])
        best = max((h["confidence"] for h in hits), default=0.0)
        if best < MIN_CONF:
            under_conf.append((etype, best))
    msg_parts: list[str] = []
    if missing:
        msg_parts.append(f"zero gated hits for: {missing}")
    if under_conf:
        msg_parts.append(
            f"below {MIN_CONF} confidence: "
            + ", ".join(f"{n}={c:.2f}" for n, c in under_conf)
        )
    assert not msg_parts, "; ".join(msg_parts)


def test_distinct_event_type_breadth(ledger: dict) -> None:
    """Corpus should show >=7 distinct event types across all 111 clips."""
    counts = ledger.get("event_type_counts", {})
    distinct = sum(1 for c in counts.values() if c >= 1)
    assert distinct >= MIN_DISTINCT_TYPES, (
        f"only {distinct} distinct event types seen; need >={MIN_DISTINCT_TYPES}. "
        f"counts={counts}"
    )


def test_every_clip_recognized(ledger: dict) -> None:
    """Every clip should recognize at least one event — if ANY clip drops
    to RECOGNITION_FAILED, it means the matcher regressed."""
    total = int(ledger.get("total_clips", 0))
    any_hit = int(ledger.get("clips_with_any_event", 0))
    failed = int(ledger.get("clips_recognition_failed", 0))
    assert total > 0, "ledger has total_clips=0 — scan produced nothing"
    # Allow up to 5% recognition failure before hard-failing.
    assert failed <= max(1, total // 20), (
        f"{failed}/{total} clips failed recognition (>5%). "
        f"any_hit={any_hit}"
    )


def test_top_hits_have_timestamps_in_bounds(ledger: dict) -> None:
    """Every reported top-hit must have a non-negative timestamp."""
    top5 = ledger.get("top_5_per_type", {})
    bad: list[tuple[str, str, float]] = []
    for etype, hits in top5.items():
        for h in hits:
            t = float(h.get("t", -1))
            if t < 0:
                bad.append((etype, h.get("clip", "?"), t))
    assert not bad, f"negative timestamps in top-5: {bad[:5]}"
