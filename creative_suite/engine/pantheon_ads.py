"""PANTHEON in-world ad-board system (Phase-2 charter §36-§45).

QL maps carry advertisement surfaces whose shaders sample
textures/ad_content/ad{1x1,2x1,4x1,8x1}.jpg. We replace them with a
20-design PANTHEON banner catalog (docs/reference/banner-design-directions.md
— research-derived: gold-leaf marble, war banner, bronze plaque, neon
sponsor, minimal monogram, fake-sponsor parody, stats board, archive
callout).

One pk3 build = one BANNER SET: one design per aspect, chosen
DETERMINISTICALLY from (map, frag_class, event_hash) with repetition
control (charter §41/§42 — never random at runtime, never the same set
five clips running). Every assignment is recorded to
output/demo_v2/banner_assignments.json for reproducibility (§57).

Search path (§45): pk3 goes to the wolfcam GAMEDIR as
zzz_zz_pantheon_ads.pk3 — gamedir beats baseq3, and zzz_zz sorts after the
zzz_uhd_* packs whose upscaled house ads otherwise win. The pack contains
ONLY the four ad_content jpgs — it cannot override unrelated map textures.

Quality (§40): render at 2x then LANCZOS downscale; baseline JPEG q92
(progressive JPEG crashes QL-era clients).

CLI:
  python -m creative_suite.engine.pantheon_ads                    # default set
  python -m creative_suite.engine.pantheon_ads --sheet            # preview sheet, all 20
  python -m creative_suite.engine.pantheon_ads --map asylum --frag-class AIR_ROCKET_GEO --event-hash abc123
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
LOGO = REPO_ROOT / "PantheonProduction.JPG"
OUT_DIR = REPO_ROOT / "creative_suite" / "engine" / "assets" / "pantheon_ads"
PK3 = (REPO_ROOT / "output" / "demo_v2" / "_wolfcam_staging" / "wolfcam-ql"
       / "zzz_zz_pantheon_ads.pk3")
ASSIGN_LOG = REPO_ROOT / "output" / "demo_v2" / "banner_assignments.json"

# final texture sizes (2x pak00 originals; nopicmip shader keeps detail)
FINAL = {"1x1": (512, 512), "2x1": (1024, 512),
         "4x1": (2048, 512), "8x1": (2048, 256)}

# palettes (research doc)
INK = (13, 13, 16)
GOLD = (212, 175, 55)
GOLD_HI = (240, 217, 140)
BONE = (232, 226, 208)
BLUE = (36, 62, 122)
BRONZE = (168, 128, 60)
BRONZE_INK = (36, 26, 8)
NEON_BG = (11, 13, 20)
NEON = (63, 111, 216)
NEON_TXT = (223, 227, 234)
STONE = (192, 192, 200)
PARODY_Y = (232, 192, 32)
PARODY_R = (176, 35, 24)
SLATE = (26, 29, 34)
AMBER = (230, 180, 60)


def _font(size: int, face: str = "arialbd"):
    for name in (f"{face}.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except OSError:
            continue
    return ImageFont.load_default()


# faces: serif (Roman-capital register), cond (Bebas analog), sans
F_SERIF = "palab"        # Palatino Linotype Bold
F_COND = "bahnschrift"   # Bahnschrift (condensed weights)
F_SANS = "arialbd"


def _ctext(d, cx, cy, text, font, fill, tracking=0, max_w=None):
    if tracking:
        text = (" " * tracking).join(text)
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font)
    if max_w and (x1 - x0) > max_w:
        # shrink to fit the safe area (charter: no clipped copy)
        size = getattr(font, "size", 20)
        while size > 8 and (x1 - x0) > max_w:
            size = int(size * 0.94)
            font = _font(size, getattr(font, "path", "").split("\\")[-1].split("/")[-1].replace(".ttf", "") or "arialbd")
            x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font)
    d.text((cx - (x1 - x0) / 2 - x0, cy - (y1 - y0) / 2 - y0),
           text, font=font, fill=fill)


def _logo_glyph(color, size):
    """Temple logo extracted from the JPG (dark strokes -> colorized mask)."""
    g = ImageOps.grayscale(Image.open(LOGO))
    mask = g.point(lambda p: 255 if p < 128 else 0).convert("L")
    mask = mask.filter(ImageFilter.MaxFilter(3))
    bbox = mask.getbbox()
    mask = mask.crop(bbox)
    mask.thumbnail(size, Image.LANCZOS)
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    out.paste(Image.new("RGBA", mask.size, color + (255,)), mask=mask)
    return out


def _frame(d, w, h, color, inset=None, width=None):
    b = inset if inset is not None else max(10, h // 36)
    d.rectangle([b, b, w - b, h - b], outline=color,
                width=width or max(4, b // 2))


def _marble(w, h):
    im = Image.new("RGB", (w, h), INK)
    d = ImageDraw.Draw(im)
    seed = 7
    for i in range(14):
        seed = (seed * 1103515245 + 12345) % 2**31
        x = seed % w
        seed = (seed * 1103515245 + 12345) % 2**31
        y = seed % h
        d.line([x, y, x + w // 6, y + h // 8], fill=(28, 27, 32), width=2)
    return im


def _laurel(d, cx, cy, r, color):
    for side in (-1, 1):
        for i in range(7):
            a = 25 + i * 18
            import math
            x = cx + side * r * math.cos(math.radians(a - 90)) * 0.9
            y = cy - r * 0.05 + r * math.sin(math.radians(a - 90))
            d.ellipse([x - r * 0.09, y - r * 0.16, x + r * 0.09, y + r * 0.16],
                      fill=color)


@dataclass(frozen=True)
class Banner:
    bid: str
    direction: str
    aspect: str
    classes: tuple = ()      # frag classes this design is themed for


def _render(bid: str, w: int, h: int) -> Image.Image:
    im, d = None, None

    def new(bg):
        nonlocal im, d
        im = Image.new("RGB", (w, h), bg) if not isinstance(bg, Image.Image) else bg
        d = ImageDraw.Draw(im)

    if bid == "pan_logo_1x1":
        new(_marble(w, h)); _frame(d, w, h, GOLD)
        g = _logo_glyph(GOLD, (int(w * .62), int(h * .58)))
        im.paste(g, ((w - g.width) // 2, int(h * .14)), g)
        _ctext(d, w / 2, h * .84, "PANTHEON", _font(int(h * .11), F_SERIF), GOLD)
    elif bid == "pan_word_2x1":
        new(_marble(w, h)); _frame(d, w, h, GOLD)
        g = _logo_glyph(GOLD, (int(w * .26), int(h * .68)))
        im.paste(g, (int(w * .07), (h - g.height) // 2), g)
        _ctext(d, w * .62, h * .40, "PANTHEON", _font(int(h * .26), F_SERIF), GOLD)
        _ctext(d, w * .62, h * .66, "QUAKE TRIBUTE", _font(int(h * .10), F_COND), GOLD_HI)
    elif bid == "pan_word_4x1":
        new(_marble(w, h)); _frame(d, w, h, GOLD)
        _ctext(d, w / 2, h * .46, "PANTHEON", _font(int(h * .34), F_SERIF), GOLD, max_w=w * .58)
        _laurel(d, w * .09, h * .5, h * .30, GOLD)
        _laurel(d, w * .91, h * .5, h * .30, GOLD)
    elif bid == "pan_track_8x1":
        new(_marble(w, h)); _frame(d, w, h, GOLD, inset=max(6, h // 24))
        _ctext(d, w / 2, h * .48, "PANTHEON", _font(int(h * .52), F_SERIF), GOLD, tracking=2)
    elif bid == "tribute_2x1":
        new(_marble(w, h)); _frame(d, w, h, GOLD)
        _ctext(d, w / 2, h * .32, "QUAKE", _font(int(h * .30), F_SERIF), BONE)
        _ctext(d, w / 2, h * .62, "TRIBUTE", _font(int(h * .30), F_SERIF), GOLD)
        d.line([w * .25, h * .82, w * .75, h * .82], fill=GOLD, width=max(3, h // 80))
    elif bid == "banner_ptn_1x1":
        new(BLUE); _frame(d, w, h, BONE)
        d.polygon([(w * .5, h * .16), (w * .74, h * .30), (w * .74, h * .62),
                   (w * .5, h * .80), (w * .26, h * .62), (w * .26, h * .30)],
                  outline=BONE, width=max(4, h // 60))
        _ctext(d, w / 2, h * .46, "pTn", _font(int(h * .22), F_SERIF), BONE)
    elif bid == "banner_trash_2x1":
        new(BLUE); _frame(d, w, h, BONE)
        d.polygon([(w * .17, h * .22), (w * .29, h * .32), (w * .29, h * .58),
                   (w * .17, h * .70), (w * .05, h * .58), (w * .05, h * .32)],
                  outline=GOLD, width=max(4, h // 70))
        _ctext(d, w * .17, h * .45, "pTn", _font(int(h * .14), F_SERIF), GOLD)
        _ctext(d, w * .62, h * .44, "pTn.Tr4sH", _font(int(h * .24), F_COND), BONE)
        _ctext(d, w * .62, h * .68, "CLAN ARENA", _font(int(h * .10), F_COND), GOLD)
    elif bid == "banner_pennant_4x1":
        new(BLUE); _frame(d, w, h, GOLD, inset=max(8, h // 30))
        step = w // 10
        for i in range(10):
            d.polygon([(i * step + step * .1, h * .12), (i * step + step * .9, h * .12),
                       (i * step + step * .5, h * .30)], fill=GOLD if i % 2 else BONE)
        _ctext(d, w / 2, h * .62, "PANTHEON  ·  pTn", _font(int(h * .26), F_SERIF), BONE, max_w=w * .80)
    elif bid == "plaque_est_4x1":
        new(BRONZE); _frame(d, w, h, BRONZE_INK)
        _ctext(d, w / 2, h * .44, "EST. 2010  —  CLAN ARENA",
               _font(int(h * .30), F_SERIF), BRONZE_INK, max_w=w * .86)
        _ctext(d, w / 2, h * .74, "PANTHEON PRODUCTION", _font(int(h * .12), F_COND), BRONZE_INK)
    elif bid == "plaque_honors_8x1":
        new(BRONZE); _frame(d, w, h, BRONZE_INK, inset=max(6, h // 24))
        _ctext(d, w / 2, h * .48, "TR4SH  ·  #39 WORLD CA  ·  ELO 2326",
               _font(int(h * .38), F_SERIF), BRONZE_INK, max_w=w * .90)
    elif bid == "plaque_laurel_1x1":
        new(BRONZE); _frame(d, w, h, BRONZE_INK)
        _laurel(d, w / 2, h * .5, h * .34, BRONZE_INK)
        _ctext(d, w / 2, h * .47, "39", _font(int(h * .34), F_SERIF), BRONZE_INK)
        _ctext(d, w / 2, h * .82, "WORLD  CLAN ARENA", _font(int(h * .08), F_COND), BRONZE_INK)
    elif bid == "neon_glyph_1x1":
        new(NEON_BG)
        g = _logo_glyph(NEON, (int(w * .7), int(h * .64)))
        glow = g.filter(ImageFilter.GaussianBlur(h // 40))
        im.paste(glow, ((w - g.width) // 2, int(h * .12)), glow)
        im.paste(g, ((w - g.width) // 2, int(h * .12)), g)
        d = ImageDraw.Draw(im)
        _ctext(d, w / 2, h * .86, "PANTHEON", _font(int(h * .10), F_COND), NEON)
    elif bid == "neon_partner_2x1":
        new(NEON_BG); _frame(d, w, h, NEON)
        _ctext(d, w / 2, h * .38, "PANTHEON", _font(int(h * .30), F_COND), NEON_TXT)
        _ctext(d, w / 2, h * .66, "OFFICIAL ARENA PARTNER", _font(int(h * .11), F_COND), NEON)
    elif bid == "neon_ticker_8x1":
        new(NEON_BG)
        d.line([0, h * .12, w, h * .12], fill=GOLD, width=max(2, h // 60))
        d.line([0, h * .88, w, h * .88], fill=GOLD, width=max(2, h // 60))
        _ctext(d, w / 2, h * .48, "PANTHEON  ·  QUAKE TRIBUTE  ·  pTn.Tr4sH  ·  2010-2013",
               _font(int(h * .30), F_COND), NEON_TXT, max_w=w * .92)
    elif bid == "mono_glyph_2x1":
        new(STONE)
        g = _logo_glyph(GOLD, (int(w * .46), int(h * .86)))
        im.paste(g, ((w - g.width) // 2, (h - g.height) // 2), g)
    elif bid == "mono_ptn_1x1":
        new(INK)
        _ctext(d, w / 2, h * .46, "pTn", _font(int(h * .44), F_SERIF), GOLD)
    elif bid == "parody_rockets_2x1":
        new(PARODY_Y); _frame(d, w, h, INK)
        _ctext(d, w / 2, h * .40, "EAT ROCKETS", _font(int(h * .28), F_SANS), INK, max_w=w * .84)
        _ctext(d, w / 2, h * .70, "direct hits guaranteed or your armor back",
               _font(int(h * .07), F_SANS), INK)
    elif bid == "parody_lg_1x1":
        new(PARODY_R); _frame(d, w, h, BONE)
        d.ellipse([w * .18, h * .14, w * .82, h * .66], outline=BONE,
                  width=max(4, h // 60))
        _ctext(d, w / 2, h * .34, "LG\u2122", _font(int(h * .18), F_SANS), BONE)
        _ctext(d, w / 2, h * .52, "40%", _font(int(h * .12), F_SANS), BONE)
        _ctext(d, w / 2, h * .80, "ACCURACY GUARANTEED", _font(int(h * .08), F_COND), BONE)
    elif bid == "stats_elo_2x1":
        new(SLATE)
        d.rectangle([0, 0, w, h * .22], fill=BLUE)
        _ctext(d, w / 2, h * .11, "QLRANKS  ·  ARCHIVE VERIFIED", _font(int(h * .09), F_COND), BONE)
        _ctext(d, w * .30, h * .58, "ELO", _font(int(h * .26), F_COND), AMBER)
        _ctext(d, w * .68, h * .58, "2326", _font(int(h * .34), F_COND), AMBER)
        d.line([w * .5, h * .34, w * .5, h * .84], fill=(60, 64, 72), width=3)
    elif bid == "callout_archive_8x1":
        new(BONE); _frame(d, w, h, BLUE, inset=max(6, h // 24))
        _ctext(d, w / 2, h * .48, "THE PANTHEON ARCHIVE  ·  6,465 DEMOS  ·  2010-2013",
               _font(int(h * .34), F_SERIF), BLUE, max_w=w * .90)
    else:
        raise KeyError(bid)
    return im


CATALOG = [
    Banner("pan_logo_1x1", "gold_leaf", "1x1"),
    Banner("pan_word_2x1", "gold_leaf", "2x1"),
    Banner("pan_word_4x1", "gold_leaf", "4x1"),
    Banner("pan_track_8x1", "gold_leaf", "8x1"),
    Banner("tribute_2x1", "gold_leaf", "2x1"),
    Banner("banner_ptn_1x1", "war_banner", "1x1"),
    Banner("banner_trash_2x1", "war_banner", "2x1"),
    Banner("banner_pennant_4x1", "war_banner", "4x1"),
    Banner("plaque_est_4x1", "bronze", "4x1"),
    Banner("plaque_honors_8x1", "bronze", "8x1"),
    Banner("plaque_laurel_1x1", "bronze", "1x1"),
    Banner("neon_glyph_1x1", "neon", "1x1"),
    Banner("neon_partner_2x1", "neon", "2x1"),
    Banner("neon_ticker_8x1", "neon", "8x1"),
    Banner("mono_glyph_2x1", "monogram", "2x1"),
    Banner("mono_ptn_1x1", "monogram", "1x1"),
    Banner("parody_rockets_2x1", "parody", "2x1",
           ("DIRECT_ROCKET", "DIRECT_CONFIRMED_GEO", "AIR_ROCKET",
            "AIR_ROCKET_GEO", "ROCKET_JUMP_FRAG")),
    Banner("parody_lg_1x1", "parody", "1x1",
           ("LG_TRACKING", "LG_HIGH_PRESSURE", "LG_DODGE_MASTER",
            "LG_HIGH_ACCURACY", "DAMAGE_BURST")),
    Banner("stats_elo_2x1", "stats", "2x1"),
    Banner("callout_archive_8x1", "callout", "8x1"),
]
BY_ASPECT = {}
for b in CATALOG:
    BY_ASPECT.setdefault(b.aspect, []).append(b)


def render_banner(bid: str) -> Image.Image:
    """Render at 2x, LANCZOS down to final (charter §40)."""
    b = next(x for x in CATALOG if x.bid == bid)
    fw, fh = FINAL[b.aspect]
    return _render(bid, fw * 2, fh * 2).resize((fw, fh), Image.LANCZOS)


def assign_set(map_name: str = "", frag_class: str = "",
               event_hash: str = "", history: list[dict] | None = None) -> dict:
    """Deterministic aspect->banner_id choice (§41) with repetition
    control (§42): a design used in the previous 2 assignments is demoted."""
    seed = hashlib.sha256(
        f"{map_name}|{frag_class}|{event_hash}".encode()).digest()
    recent = {bid for a in (history or [])[-2:] for bid in a["set"].values()}
    chosen = {}
    for i, aspect in enumerate(("1x1", "2x1", "4x1", "8x1")):
        pool = BY_ASPECT[aspect]
        themed = [b for b in pool if frag_class in b.classes]
        ranked = sorted(pool, key=lambda b: (
            b.bid in recent,                      # repetition demotion
            b not in themed,                      # class-themed first
            seed[i] % len(pool) != pool.index(b) % len(pool),
            b.bid))
        chosen[aspect] = ranked[0].bid
    return chosen


def build_pack(banner_set: dict | None = None, record: dict | None = None) -> Path:
    banner_set = banner_set or assign_set()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PK3.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(PK3, "w", zipfile.ZIP_STORED) as zf:
        for aspect, bid in banner_set.items():
            im = render_banner(bid)
            jpg = OUT_DIR / f"set_ad{aspect}.jpg"
            # baseline JPEG only — progressive crashes QL-era clients
            im.save(jpg, quality=92, progressive=False)
            zf.write(jpg, f"textures/ad_content/ad{aspect}.jpg")
    if record is not None:
        log = []
        if ASSIGN_LOG.exists():
            log = json.loads(ASSIGN_LOG.read_text())
        log.append({**record, "set": banner_set})
        ASSIGN_LOG.write_text(json.dumps(log, indent=1))
    return PK3


def load_history() -> list[dict]:
    if ASSIGN_LOG.exists():
        return json.loads(ASSIGN_LOG.read_text())
    return []


def build_sheet() -> Path:
    """Preview sheet of all 20 designs for user sign-off (VIS-1)."""
    tiles = [(b.bid, render_banner(b.bid)) for b in CATALOG]
    cols, pad, tw = 4, 24, 480
    rows = (len(tiles) + cols - 1) // cols
    th = 300
    sheet = Image.new("RGB", (cols * (tw + pad) + pad,
                              rows * (th + pad) + pad), (20, 20, 24))
    d = ImageDraw.Draw(sheet)
    f = _font(18)
    for i, (bid, im) in enumerate(tiles):
        im = im.copy()
        im.thumbnail((tw, th - 30), Image.LANCZOS)
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + pad)
        sheet.paste(im, (x + (tw - im.width) // 2, y))
        d.text((x, y + th - 26), bid, font=f, fill=(200, 203, 209))
    out = OUT_DIR / "banner_sheet.png"
    sheet.save(out)
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--map", default="")
    ap.add_argument("--frag-class", default="")
    ap.add_argument("--event-hash", default="")
    args = ap.parse_args()
    if args.sheet:
        print("sheet:", build_sheet())
    else:
        s = assign_set(args.map, args.frag_class, args.event_hash,
                       load_history())
        p = build_pack(s, record={"map": args.map, "frag_class": args.frag_class,
                                  "event_hash": args.event_hash})
        print("set:", json.dumps(s))
        print("pk3:", p, f"{p.stat().st_size/1024:.0f} KB")
