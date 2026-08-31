"""PANTHEON in-world ad boards (user 2026-08-31: "ql advertisment surface
need to be used by us to show our video title or information").

QL maps carry advertisement surfaces whose shaders sample
textures/ad_content/ad{1x1,2x1,4x1,8x1}.jpg from pak00 (beige placeholders
in our staged assets — the "map texture issue" in the defect frame).
A zzz_*.pk3 (ENG-2 alphabetical override) replaces them with PANTHEON
branding, so every board in every captured master shows series identity.

Doubled resolution vs pak00 originals (nopicmip shader keeps detail).
Regenerate + repack any time with:  python -m creative_suite.engine.pantheon_ads
Optional custom line (e.g. a Part title) via --line "QUAKE TRIBUTE - PART I".
"""
from __future__ import annotations

import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
LOGO = REPO_ROOT / "PantheonProduction.JPG"
OUT_DIR = REPO_ROOT / "creative_suite" / "engine" / "assets" / "pantheon_ads"
# GAMEDIR, not baseq3: gamedir pk3s override baseq3 entirely, and the UHD
# packs (zzz_uhd_01..05) carry upscaled QL house ads — the name must sort
# after zzz_uhd_* for our boards to win.
PK3 = (REPO_ROOT / "output" / "demo_v2" / "_wolfcam_staging" / "wolfcam-ql"
       / "zzz_zz_pantheon_ads.pk3")

BG = (16, 15, 14)
GOLD = (212, 175, 55)
SILVER = (200, 203, 209)
EDGE = (78, 66, 34)

SIZES = {"ad1x1": (512, 512), "ad2x1": (1024, 512),
         "ad4x1": (2048, 512), "ad8x1": (2048, 256)}


def _font(size: int, bold=True):
    try:
        return ImageFont.truetype(
            f"C:/Windows/Fonts/{'arialbd.ttf' if bold else 'arial.ttf'}", size)
    except OSError:
        return ImageFont.load_default()


def _center_text(d: ImageDraw.ImageDraw, cx, cy, text, font, fill):
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font)
    d.text((cx - (x1 - x0) / 2 - x0, cy - (y1 - y0) / 2 - y0),
           text, font=font, fill=fill)


def build_board(name: str, line: str | None = None) -> Image.Image:
    w, h = SIZES[name]
    im = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(im)
    b = max(6, h // 42)
    d.rectangle([b, b, w - b, h - b], outline=EDGE, width=max(3, b // 2))

    if name == "ad1x1":
        logo = Image.open(LOGO).convert("RGB")
        lw = int(w * 0.82)
        lh = int(logo.height * lw / logo.width)
        im.paste(logo.resize((lw, lh)), ((w - lw) // 2, int(h * 0.10)))
        _center_text(d, w / 2, h * 0.88, line or "pTn.Tr4sH",
                     _font(int(h * 0.11)), GOLD)
    elif name == "ad2x1":
        logo = Image.open(LOGO).convert("RGB")
        lh = int(h * 0.60)
        lw = int(logo.width * lh / logo.height)
        im.paste(logo.resize((lw, lh)), (int(w * 0.06), int(h * 0.12)))
        cx = w * 0.06 + lw / 2 + (w * 0.94 - (w * 0.06 + lw)) / 2 + lw / 2
        cx = (w * 0.06 + lw + w * 0.96) / 2
        _center_text(d, cx, h * 0.34, "PANTHEON", _font(int(h * 0.17)), GOLD)
        _center_text(d, cx, h * 0.55, line or "pTn.Tr4sH",
                     _font(int(h * 0.11)), SILVER)
        _center_text(d, cx, h * 0.72, "QUAKE LIVE  2010-2013",
                     _font(int(h * 0.07), bold=False), SILVER)
    else:  # wide banners
        _center_text(d, w * 0.30, h * 0.45, "PANTHEON",
                     _font(int(h * 0.34)), GOLD)
        _center_text(d, w * 0.70, h * 0.45,
                     line or "pTn.Tr4sH  ·  CLAN ARENA",
                     _font(int(h * 0.18), bold=False), SILVER)
        d.line([w * 0.30, h * 0.72, w * 0.70, h * 0.72], fill=EDGE, width=4)
    return im


def build_pack(line: str | None = None) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PK3.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(PK3, "w", zipfile.ZIP_STORED) as zf:
        for name in SIZES:
            im = build_board(name, line)
            png = OUT_DIR / f"{name}.png"
            im.save(png)
            jpg = OUT_DIR / f"{name}.jpg"
            im.save(jpg, quality=92)
            # original filename + extension (pack-naming lesson from UHD run)
            zf.write(jpg, f"textures/ad_content/{name}.jpg")
    return PK3


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--line", default=None,
                    help="custom board line, e.g. a Part title")
    args = ap.parse_args()
    p = build_pack(args.line)
    print("ad pack:", p, f"{p.stat().st_size/1024:.0f} KB")
