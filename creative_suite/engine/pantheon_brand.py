"""PANTHEON brand assets — logo, wordmark, lockups, channel art.

The procedural mark in `pantheon_intro.py` was built to animate, and it shows:
thin strokes that vanish at small sizes, no fixed proportions, nothing that
survives being put next to text. This is the static identity instead — drawn to
a grid, weighted to hold at 32 px, and exported at the sizes a channel and a
Reddit post actually need.

Design brief, from the series itself:

    the mark      a temple front reduced to its load-bearing parts: pediment,
                  entablature, six columns, stylobate. Six because the pediment
                  reads cleanly over six and gets muddy over eight at small
                  sizes.
    the metal     brushed silver with a warm gold edge. The gold is a rim light,
                  never a fill -- filled gold reads as a casino, lit gold reads
                  as an award.
    the ground    near-black, not black. Pure #000 kills the rim light and looks
                  like a hole on dark YouTube.
    the type      Black Ops One for PANTHEON, Bebas Neue for everything else.
                  Wide tracking on the wordmark; the mark is heavy, so the type
                  has to breathe or the lockup turns into a brick.

    python -m creative_suite.engine.pantheon_brand
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
FONTS = REPO_ROOT / "creative_suite" / "engine" / "assets" / "fonts"
OUTDIR = REPO_ROOT / "output" / "brand"

INK = (9, 10, 12)
SILVER_HI = (236, 240, 245)
SILVER = (198, 205, 214)
SILVER_LO = (108, 116, 126)
GOLD = (206, 168, 92)
GOLD_HI = (238, 208, 140)
SS = 4                      # supersample factor; everything is drawn 4x then down


def font(name: str, size: int):
    try:
        return ImageFont.truetype(str(FONTS / name), size)
    except Exception:
        return ImageFont.load_default()


def _grad_v(size, top, bottom):
    """Vertical gradient — the base of the brushed-metal look."""
    w, h = size
    g = Image.new("RGB", (1, h))
    d = ImageDraw.Draw(g)
    for y in range(h):
        t = y / max(1, h - 1)
        d.point((0, y), fill=tuple(int(top[i] + (bottom[i] - top[i]) * t)
                                   for i in range(3)))
    return g.resize((w, h), Image.BILINEAR)


def _brushed(size):
    """Silver with fine horizontal grain, so flat fills do not look like plastic."""
    import random
    w, h = size
    base = _grad_v(size, SILVER_HI, SILVER_LO)
    px = base.load()
    rnd = random.Random(7)                  # fixed seed: the brand must not shift
    for y in range(h):
        j = rnd.randint(-6, 6)
        for x in range(w):
            r, g, b = px[x, y]
            px[x, y] = (max(0, min(255, r + j)), max(0, min(255, g + j)),
                        max(0, min(255, b + j)))
    return base


def temple_mask(size: int) -> Image.Image:
    """The mark as a mask, drawn on a proportional grid.

    Every measurement is a fraction of the canvas, so the mark is identical at
    any export size -- which is the thing the animated version never had.
    """
    S = size * SS
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)

    left, right = 0.10 * S, 0.90 * S
    ped_top = 0.14 * S                      # apex of the pediment
    ped_base = 0.36 * S                     # underside of the pediment
    ent_base = 0.45 * S                     # underside of the entablature
    col_base = 0.80 * S                     # top of the stylobate
    sty_top, sty_base = 0.80 * S, 0.90 * S

    # pediment: a solid triangle, with the tympanum cut out so it reads as a
    # frame rather than a wedge
    d.polygon([(S / 2, ped_top), (right, ped_base), (left, ped_base)], fill=255)
    inset = 0.055 * S
    d.polygon([(S / 2, ped_top + inset * 1.7),
               (right - inset * 1.5, ped_base - inset * 0.55),
               (left + inset * 1.5, ped_base - inset * 0.55)], fill=0)

    # entablature — the horizontal beam the pediment sits on
    d.rectangle([left, ped_base, right, ent_base], fill=255)

    # six columns, evenly spaced, with the outer pair slightly heavier so the
    # silhouette has weight at its edges
    n = 6
    span = (right - left) - 0.09 * S
    x0 = left + 0.045 * S
    gap = span / n
    cw = gap * 0.46
    for i in range(n):
        cx = x0 + gap * (i + 0.5)
        w = cw * (1.18 if i in (0, n - 1) else 1.0)
        d.rectangle([cx - w / 2, ent_base, cx + w / 2, col_base], fill=255)
        # capital and base: tiny flares that stop the columns reading as bars
        d.rectangle([cx - w * 0.78, ent_base, cx + w * 0.78,
                     ent_base + 0.022 * S], fill=255)
        d.rectangle([cx - w * 0.78, col_base - 0.022 * S, cx + w * 0.78,
                     col_base], fill=255)

    # stylobate, two steps
    d.rectangle([left - 0.02 * S, sty_top, right + 0.02 * S,
                 sty_top + 0.045 * S], fill=255)
    d.rectangle([left - 0.05 * S, sty_base - 0.045 * S, right + 0.05 * S,
                 sty_base], fill=255)
    return m.resize((size, size), Image.LANCZOS)


def mark(size: int = 512, glow: bool = True) -> Image.Image:
    """The finished mark: brushed silver body, gold rim, soft ground shadow."""
    m = temple_mask(size)
    metal = _brushed((size, size))

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    if glow:
        halo = m.filter(ImageFilter.GaussianBlur(size * 0.045))
        g = Image.new("RGBA", (size, size), GOLD + (0,))
        g.putalpha(halo.point(lambda v: int(v * 0.42)))
        out = Image.alpha_composite(out, g)

    body = metal.convert("RGBA")
    body.putalpha(m)
    out = Image.alpha_composite(out, body)

    # gold rim: the mask minus an eroded copy of itself -- a light catching an
    # edge, never a fill
    er = m.filter(ImageFilter.MinFilter(3 if size < 256 else 5))
    rim = Image.new("L", (size, size))
    rim.paste(m, (0, 0))
    rim = Image.composite(Image.new("L", (size, size), 0), rim, er)
    rim = rim.filter(ImageFilter.GaussianBlur(max(0.6, size * 0.0022)))
    gold = Image.new("RGBA", (size, size), GOLD_HI + (0,))
    gold.putalpha(rim.point(lambda v: int(v * 0.95)))
    out = Image.alpha_composite(out, gold)
    return out


def on_ground(img: Image.Image, pad_ratio=0.18) -> Image.Image:
    s = img.size[0]
    pad = int(s * pad_ratio)
    canvas = Image.new("RGB", (s + pad * 2, s + pad * 2), INK)
    canvas.paste(img, (pad, pad), img)
    return canvas


def wordmark(width=1600, sub="QUAKE LIVE  ·  CLAN ARENA") -> Image.Image:
    """Horizontal lockup: mark, then PANTHEON over a gold rule and a subtitle.

    The type is MEASURED and fitted before it is drawn. A first version set the
    size from the canvas height and tracked it manually, which pushed the final
    N past the right edge -- a lockup that clips its own name is worse than no
    lockup. Now the font size is solved for the space that is actually left
    after the mark, so it fits at any width.
    """
    h = int(width * 0.34)
    im = Image.new("RGB", (width, h), INK)
    d = ImageDraw.Draw(im)

    ms = int(h * 0.72)
    mk = mark(ms)
    mx = int(h * 0.14)
    im.paste(mk, (mx, int((h - ms) / 2)), mk)

    x = mx + ms + int(h * 0.18)
    avail = width - x - int(h * 0.14)
    word = "PANTHEON"

    # solve the largest size whose tracked width fits `avail`
    size = int(h * 0.40)
    while size > 8:
        f = font("BlackOpsOne-Regular.ttf", size)
        track = max(1, int(size * 0.09))
        w = sum(d.textlength(c, font=f) for c in word) + track * (len(word) - 1)
        if w <= avail:
            break
        size -= 2
    f = font("BlackOpsOne-Regular.ttf", size)
    track = max(1, int(size * 0.09))
    tw = sum(d.textlength(c, font=f) for c in word) + track * (len(word) - 1)

    y = int(h * 0.26)
    cx = x
    for ch in word:
        d.text((cx + 3, y + 3), ch, font=f, fill=(0, 0, 0))
        d.text((cx, y), ch, font=f, fill=SILVER_HI)
        cx += d.textlength(ch, font=f) + track

    rule_y = y + int(size * 1.06)
    d.line([(x, rule_y), (x + tw, rule_y)], fill=GOLD,
           width=max(2, int(h * 0.014)))

    fs_size = max(10, int(size * 0.40))
    fs = font("BebasNeue-Regular.ttf", fs_size)
    while d.textlength(sub, font=fs) > avail and fs_size > 8:
        fs_size -= 1
        fs = font("BebasNeue-Regular.ttf", fs_size)
    d.text((x, rule_y + int(h * 0.035)), sub, font=fs, fill=SILVER_LO)
    return im


def banner(w=2560, h=1440) -> Image.Image:
    """YouTube channel art. Safe area is the middle 1546x423."""
    im = Image.new("RGB", (w, h), INK)
    d = ImageDraw.Draw(im)
    for i in range(int(h * 0.5)):               # soft vertical lift
        t = i / (h * 0.5)
        d.line([(0, h / 2 - i), (w, h / 2 - i)],
               fill=tuple(int(INK[k] + (26 - INK[k]) * (1 - t) * 0.5)
                          for k in range(3)))
    ms = int(h * 0.30)
    mk = mark(ms)
    im.paste(mk, (int(w / 2 - ms / 2), int(h / 2 - ms * 0.80)), mk)

    f = font("BlackOpsOne-Regular.ttf", int(h * 0.075))
    word, track = "PANTHEON", int(h * 0.008)
    tw = sum(d.textlength(c, font=f) for c in word) + track * (len(word) - 1)
    cx = (w - tw) / 2
    y = int(h / 2 + ms * 0.28)
    for ch in word:
        d.text((cx + 3, y + 3), ch, font=f, fill=(0, 0, 0))
        d.text((cx, y), ch, font=f, fill=SILVER_HI)
        cx += d.textlength(ch, font=f) + track
    d.line([(w / 2 - tw * 0.42, y + int(h * 0.098)),
            (w / 2 + tw * 0.42, y + int(h * 0.098))], fill=GOLD, width=3)
    fs = font("BebasNeue-Regular.ttf", int(h * 0.032))
    s2 = "QUAKE LIVE  ·  CLAN ARENA  ·  FRAGMOVIES FROM A DECADE OF DEMOS"
    d.text(((w - d.textlength(s2, font=fs)) / 2, y + int(h * 0.115)), s2,
           font=fs, fill=SILVER_LO)
    return im


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUTDIR))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    made = []

    for s in (1024, 512, 256, 128, 64, 32):
        p = out / "pantheon_mark_{}.png".format(s)
        mark(s).save(p)
        made.append(p)
    p = out / "pantheon_mark_1024_onblack.png"
    on_ground(mark(1024)).save(p)
    made.append(p)

    p = out / "pantheon_avatar_800.png"
    on_ground(mark(660), pad_ratio=0.106).resize((800, 800), Image.LANCZOS).save(p)
    made.append(p)

    p = out / "pantheon_wordmark_1600.png"
    wordmark(1600).save(p)
    made.append(p)
    p = out / "pantheon_wordmark_project.png"
    wordmark(1600, "QUAKE LEGACY  ·  DEMOS IN, FRAGMOVIES OUT").save(p)
    made.append(p)

    p = out / "pantheon_channel_banner_2560x1440.png"
    banner().save(p)
    made.append(p)

    print("brand assets:")
    for m in made:
        print("  {:44} {:>8.0f} KB".format(m.name, m.stat().st_size / 1024))
    print("\n  {}".format(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
