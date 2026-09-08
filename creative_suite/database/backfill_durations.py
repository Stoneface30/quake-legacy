"""Backfill NULL duration_s on clip_arrangements via ffprobe.

Rule T5 (2026-04-23 NLE plan) populates duration_s only on *new* arrangement
import, so every row that predates that commit is still NULL. A NULL duration
makes the NLE timeline draw uniform-width blocks and leaves beatmatch with no
real clip lengths to work from.

Usage:
    python -m creative_suite.database.backfill_durations [--part N] [--dry-run]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from creative_suite.api.studio import _ffprobe_duration
from creative_suite.engine.config import Config


def backfill(db_path: Path, ffprobe_bin: str, part: int | None = None,
             dry_run: bool = False) -> tuple[int, int, int]:
    """Return (examined, updated, failed)."""
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    q = "SELECT id, part, clip_path FROM clip_arrangements WHERE duration_s IS NULL"
    args: tuple = ()
    if part is not None:
        q += " AND part = ?"
        args = (part,)
    rows = con.execute(q, args).fetchall()

    examined = len(rows)
    updated = failed = 0
    for r in rows:
        cp = r["clip_path"]
        dur = _ffprobe_duration(cp, ffprobe_bin) if Path(cp).exists() else None
        if dur is None:
            failed += 1
            print(f"  [MISS] part {r['part']}: {Path(cp).name}")
            continue
        if not dry_run:
            con.execute("UPDATE clip_arrangements SET duration_s = ? WHERE id = ?",
                        (dur, r["id"]))
        updated += 1
    if not dry_run:
        con.commit()
    con.close()
    return examined, updated, failed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    cfg = Config()
    db = Path("creative_suite/database/studio_nle.db").resolve()
    print(f"DB: {db}\nffprobe: {cfg.ffprobe_bin}")
    examined, updated, failed = backfill(db, str(cfg.ffprobe_bin), a.part, a.dry_run)
    print(f"\nexamined={examined} updated={updated} failed={failed}"
          f"{' (DRY RUN)' if a.dry_run else ''}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
