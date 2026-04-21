"""SQLite upsert of CatalogEntry rows into assets table. Idempotent."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from creative_suite.config import Config
from creative_suite.db.migrate import connect
from creative_suite.inventory.catalog import CatalogEntry


def ingest(cfg: Config, entries: Iterable[CatalogEntry]) -> int:
    """Upsert entries. Returns the count of NEW rows inserted."""
    cfg.ensure_dirs()
    inserted = 0
    with connect(cfg) as con:
        con.execute("BEGIN")
        try:
            for e in entries:
                cur = con.execute(
                    "INSERT OR IGNORE INTO assets "
                    "(category, subcategory, source_pk3, internal_path, checksum) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (e.category, e.subcategory, e.source_pk3, e.internal_path, e.checksum),
                )
                if cur.rowcount:
                    inserted += 1
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    return inserted


def default_pk3_paths() -> list[Path]:
    """Steam-locked baseq3 candidates, best-first by priority.

    Quake Live pak00.pk3 first (wolfcam native format).
    Quake 3 Arena pak0..pak8 as fallback (where .tga originals live).
    """
    ql = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\pak00.pk3")
    q3a_dir = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Quake 3 Arena\baseq3")
    q3a = [q3a_dir / f"pak{i}.pk3" for i in range(9)]
    return [ql, *q3a]
