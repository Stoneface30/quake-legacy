"""Task 8.1 — PNG→TGA round-trip.

The Quake engine expects 32-bit uncompressed TGA for texture overrides.
We must preserve the full RGBA channel (alpha is LOAD-BEARING — Quake uses
alpha for transparent textures like decals, grates, glass).

Round-trip test: PNG with per-pixel alpha gradient → TGA → reopen → pixel
equality. If Pillow ever changes TGA alpha behavior, this test fails loud.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

pytest.importorskip("PIL")

from PIL import Image  # noqa: E402

from creative_suite.pk3_build.png_to_tga import png_to_tga  # noqa: E402


def _pixels(img: "Image.Image") -> list[tuple[int, int, int, int]]:
    """Cast past Pillow's partially-unknown stubs — getdata() is an
    iterable of tuples for RGBA images."""
    return cast(
        list[tuple[int, int, int, int]],
        list(cast(Any, img.getdata())),
    )


def _make_rgba_png(path: Path, size: int = 64) -> "Image.Image":
    """Build a PNG whose pixels vary in R, G, B AND A so any collapse
    to RGB during convert/save will show up as an alpha mismatch."""
    img = Image.new("RGBA", (size, size))
    px: Any = cast(Any, img).load()
    assert px is not None
    for y in range(size):
        for x in range(size):
            px[x, y] = (x * 4 % 256, y * 4 % 256, (x + y) * 2 % 256, (x * y) % 256)
    img.save(path, format="PNG")
    return img


def test_png_to_tga_preserves_rgba_pixels(tmp_path: Path) -> None:
    src = tmp_path / "in.png"
    dst = tmp_path / "out" / "in.tga"  # nested to prove parents=True
    original = _make_rgba_png(src)

    png_to_tga(src, dst)

    assert dst.exists(), "TGA was not written"
    assert dst.parent.is_dir(), "parent dir should have been created"

    roundtrip = Image.open(dst).convert("RGBA")
    assert roundtrip.size == original.size
    assert _pixels(roundtrip) == _pixels(original), (
        "pixel data diverged through PNG→TGA round-trip"
    )


def test_png_to_tga_forces_rgba_from_rgb(tmp_path: Path) -> None:
    """An RGB-only source should land as RGBA with full opacity — Quake's
    TGA loader expects 32-bit; 24-bit can silently break shader alpha
    assumptions downstream."""
    src = tmp_path / "rgb.png"
    dst = tmp_path / "rgb.tga"
    Image.new("RGB", (32, 32), (200, 100, 50)).save(src, format="PNG")

    png_to_tga(src, dst)

    out = Image.open(dst)
    assert out.mode == "RGBA", f"expected RGBA TGA, got {out.mode}"
    # Every pixel must be (200, 100, 50, 255)
    data = _pixels(out)
    assert data[0] == (200, 100, 50, 255)
    assert all(p == (200, 100, 50, 255) for p in data)


def test_png_to_tga_preserves_alpha_zero(tmp_path: Path) -> None:
    """Fully-transparent pixels must STAY fully transparent — Quake uses
    alpha=0 for cutout masks (grates, fences). A Pillow mode change that
    premultiplied alpha would collapse color channels here."""
    src = tmp_path / "a0.png"
    dst = tmp_path / "a0.tga"
    img = Image.new("RGBA", (8, 8), (255, 0, 255, 0))  # magenta + alpha=0
    img.save(src, format="PNG")

    png_to_tga(src, dst)

    out = Image.open(dst).convert("RGBA")
    # Channel preservation: every pixel == the source, including color-at-alpha-0
    assert all(p == (255, 0, 255, 0) for p in _pixels(out)), (
        "alpha=0 pixels lost their color channel — Pillow premultiplied?"
    )
