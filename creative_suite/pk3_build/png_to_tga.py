"""PNG → 32-bit uncompressed TGA (Task 8.1).

Quake 3 / Quake Live load TGA textures natively; PNG support was always
optional and pk3 overrides historically ship as .tga. We force RGBA so
the output is always 32-bit — the engine's TGA loader handles 24/32-bit
but shader alpha tests (transparent decals, grates) REQUIRE alpha.

Pillow saves TGA uncompressed by default, which is what pk3 shipping
expects (RLE-compressed TGA is accepted by the engine but many mod tools
stumble on it — uncompressed is the lowest-friction format).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image


def png_to_tga(src: Path, dst: Path) -> None:
    """Open a PNG, force RGBA, and save as TGA at ``dst``.

    Creates ``dst.parent`` if missing. No-op hinting at color profile —
    Pillow's TGA writer drops any ICC metadata, which is fine because
    the Quake engine ignores it anyway.
    """
    img = Image.open(src).convert("RGBA")  # force 32-bit
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, format="TGA")
