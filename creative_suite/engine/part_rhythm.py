"""HITS ARE BEATS — per-clip beat-anchor extraction from the demo_v2 ledger.

The generated_clips ledger carries `frag_offsets_ms`: exact per-kill offsets
INSIDE the captured AVI, straight from the parser (charter §13). These offsets
ARE the beat-anchor input — no audio inference, no onset detection. This module
turns ledger rows into anchor records and exports them for the Part01 planner.

Output: output/demo_v2/part01/scene_beat_anchors.json
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from creative_suite.database import demo_v2_db

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_PATH = REPO_ROOT / "output" / "demo_v2" / "part01" / "scene_beat_anchors.json"

# Ledger rows eligible for planning — the promoted pool plus already-captured
# batch rows. Anything without frag offsets is un-anchorable and excluded.
_ELIGIBLE_STATUSES = ("CANDIDATE", "CAPTURED", "PROMOTED")


def scene_beat_anchors(ledger_row: dict) -> dict:
    """Extract the beat-anchor record for one generated_clips row.

    Returns {clip_id, anchors_ms, primary_ms}. `anchors_ms` are the per-kill
    offsets inside the (future) AVI, ascending. `primary_ms` is the ledger's
    primary_frag_offset_ms when present and a member of the offsets, else the
    LAST kill (the payoff hit of the chain).
    """
    raw = ledger_row.get("frag_offsets_ms")
    if isinstance(raw, str):
        offsets = json.loads(raw)
    else:
        offsets = list(raw or [])
    if not offsets:
        raise ValueError(
            f"clip {ledger_row.get('generated_clip_id')}: no frag offsets"
        )
    offsets = sorted(int(o) for o in offsets)
    primary = ledger_row.get("primary_frag_offset_ms")
    if primary is None or int(primary) not in offsets:
        primary = offsets[-1]
    return {
        "clip_id": int(ledger_row["generated_clip_id"]),
        "anchors_ms": offsets,
        "primary_ms": int(primary),
    }


def load_pool_rows(db_path: Path | str | None = None) -> list[dict]:
    """All eligible ledger rows as dicts, ordered by clip id (deterministic)."""
    conn = demo_v2_db.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        marks = ", ".join("?" for _ in _ELIGIBLE_STATUSES)
        rows = conn.execute(
            "SELECT * FROM generated_clips "
            f"WHERE promotion_status IN ({marks}) "
            "AND frag_offsets_ms IS NOT NULL AND frag_offsets_ms != '[]' "
            "ORDER BY generated_clip_id",
            _ELIGIBLE_STATUSES,
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def export_scene_beat_anchors(
    db_path: Path | str | None = None,
    out_path: Path | str | None = None,
) -> Path:
    """Write scene_beat_anchors.json for every eligible ledger row."""
    out = Path(out_path) if out_path else DEFAULT_OUT_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    records = [scene_beat_anchors(r) for r in load_pool_rows(db_path)]
    doc = {
        "source": "demo_v2.db generated_clips (frag_offsets_ms — parser truth)",
        "count": len(records),
        "anchors": records,
    }
    out.write_text(json.dumps(doc, indent=1, sort_keys=True))
    return out


__all__ = ["scene_beat_anchors", "load_pool_rows", "export_scene_beat_anchors"]


if __name__ == "__main__":  # pragma: no cover
    path = export_scene_beat_anchors()
    print(f"wrote {path}")
