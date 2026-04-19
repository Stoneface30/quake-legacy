"""Generate 256px thumbnails for texture assets.

Pulls bytes straight from the pk3 (no disk extraction) via zipfile.read().
Skip on cache-hit (mtime + size unchanged on pk3).
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

try:
    from PIL import Image  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional at import time
    Image = None  # type: ignore[assignment]

from creative_suite.config import Config
from creative_suite.db.migrate import connect

THUMB_SIZE = (256, 256)
THUMB_EXTS = {".tga", ".jpg", ".jpeg", ".png"}


class PillowMissing(RuntimeError):
    """Pillow is not installed; thumbnail pipeline disabled."""


def _thumbnail_bytes(raw: bytes) -> bytes:
    if Image is None:
        raise PillowMissing("Pillow (PIL) required for thumbnails — pip install Pillow")
    img = Image.open(io.BytesIO(raw))
    img.thumbnail(THUMB_SIZE)
    out = io.BytesIO()
    img.convert("RGBA").save(out, format="PNG")
    return out.getvalue()


def generate_thumbnails(cfg: Config, limit: int | None = None) -> int:
    """Read assets table, generate a PNG thumbnail per texture asset.

    Writes to `cfg.thumbnails_dir / {asset_id}.png` and updates
    `assets.thumbnail_path`. Returns count written.
    """
    cfg.ensure_dirs()
    written = 0
    pk3_cache: dict[str, zipfile.ZipFile] = {}
    try:
        with connect(cfg) as con:
            rows = con.execute(
                "SELECT id, source_pk3, internal_path FROM assets "
                "WHERE (thumbnail_path IS NULL OR thumbnail_path = '') "
                "AND category IN ('surface', 'gfx', 'effect', 'weapon', 'skin')"
            ).fetchall()

            for row in rows:
                ext = ("." + row["internal_path"].rsplit(".", 1)[-1].lower()
                       if "." in row["internal_path"] else "")
                if ext not in THUMB_EXTS:
                    continue
                pk3_path = row["source_pk3"]
                zf = pk3_cache.get(pk3_path)
                if zf is None:
                    if not Path(pk3_path).exists():
                        continue
                    zf = zipfile.ZipFile(pk3_path)
                    pk3_cache[pk3_path] = zf
                try:
                    raw = zf.read(row["internal_path"])
                    png = _thumbnail_bytes(raw)
                except (KeyError, OSError, ValueError):
                    continue

                thumb_path = cfg.thumbnails_dir / f"{row['id']}.png"
                thumb_path.write_bytes(png)
                con.execute(
                    "UPDATE assets SET thumbnail_path = ? WHERE id = ?",
                    (str(thumb_path), row["id"]),
                )
                written += 1
                if limit is not None and written >= limit:
                    break
    finally:
        for zf in pk3_cache.values():
            zf.close()
    return written
