"""Task 3 — thumbnail generation."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("PIL")

from PIL import Image  # noqa: E402

from creative_suite.config import Config  # noqa: E402
from creative_suite.db.migrate import migrate  # noqa: E402
from creative_suite.inventory.catalog import build_catalog  # noqa: E402
from creative_suite.inventory.ingest import ingest  # noqa: E402
from creative_suite.inventory.thumbnails import generate_thumbnails  # noqa: E402


def _make_pk3_with_real_image(path: Path) -> Path:
    """Pk3 containing a tiny real PNG so Pillow can actually open it."""
    img = Image.new("RGB", (16, 16), (128, 64, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        z.writestr("textures/base_wall/basewall01bit.png", png_bytes)
        z.writestr("gfx/2d/backtile.png", png_bytes)
    return path


def test_generate_thumbnails_writes_png(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    cfg = Config()
    cfg.ensure_dirs()
    migrate(cfg)

    pk3 = _make_pk3_with_real_image(tmp_path / "real.pk3")
    ingest(cfg, build_catalog([pk3]))

    n = generate_thumbnails(cfg)
    assert n == 2
    # Second call must be a no-op (already cached via thumbnail_path).
    assert generate_thumbnails(cfg) == 0

    # Thumbnail PNG must open as valid image ≤ 256 px.
    thumbs = list(cfg.thumbnails_dir.glob("*.png"))
    assert len(thumbs) == 2
    opened = Image.open(thumbs[0])
    assert opened.width <= 256 and opened.height <= 256
