"""PANTHEON round-start "3-2-1-FIGHT" cinematic intro treatment system.

Mirrors the architecture of ``creative_suite.engine.pantheon_ads`` (N designs,
deterministic assignment, repetition control, preview sheet) but applies it to
the CA round-countdown moment instead of in-world ad banners: when a captured
clip begins during a round's countdown, it gets ONE of several distinct
cinematic treatments (a camera move from ``camera_paths`` + a styled
"3...2...1...FIGHT" graphic overlay) instead of always looking the same.

Chosen DETERMINISTICALLY from (map, demo_hash, round_num) with repetition
control (same shape as ``pantheon_ads.assign_set()``'s ``recent`` demotion) —
never random at runtime, never the same treatment on back-to-back rounds.
Every assignment is recorded to output/demo_v2/round_intro_assignments.json
for reproducibility.

Rendering technology (PH-style decision, mirrors P1-Y): PIL compositing burned
into the render pipeline, same as title_card.py's approach — NOT a live
engine change, so this works TODAY without the Path C native-engine research
track. Font files and color palette are shared with title_card.py / the
pantheon_ads catalog so every on-screen PANTHEON graphic (ads, title card,
round intros) reads as one visual series.

Camera moves are picked from the FOUR existing constructions in camera_paths
(orbit / vertical_orbit / side_track / top_down) — never a new camera
primitive. Variation comes from genuinely different camera function + params
per treatment, not palette swaps alone (pantheon_ads's parody/mono designs
proved palette-only variation feels thin — see banner-design-directions.md).

ROUND-START TIMING — DOCUMENTED APPROXIMATION, NOT A VERIFIED VALUE:
    This codebase has no corpus-wide round-boundary timestamp today.
    `frags.db`'s `demo_rounds` table (id/demo_id/round_num/start_ms/end_ms)
    only covers an old 11-demo legacy subset; `frags_rebuilt.db` (the full
    4,292-demo corpus) has no round-start table at all (confirmed 2026-08-31
    session). `docs/reference/highlight-criteria.md` only documents a scene
    pre-roll convention ("first kill -5s .. last kill +4s") which is a
    capture-window heuristic anchored to the first KILL, not to round start
    — it does not tell us when the countdown itself began. No CA countdown
    duration is documented anywhere in `engine/engines/wolfcam-knowledge/`.

    QL's on-screen CA round-start sequence is visually four beats:
    "3", "2", "1", "FIGHT". This module assumes each beat holds the screen
    for DEFAULT_BEAT_MS (1000 ms), for a DEFAULT_COUNTDOWN_MS total of 4000 ms
    ending exactly when "FIGHT" clears and players can act. This is a
    DEFENSIBLE DEFAULT, not a value extracted from game code or the corpus —
    callers that later locate the real per-beat timing (cgame countdown
    message cadence, or timing analysis across the corpus) should override
    it via explicit countdown_start_ms/countdown_end_ms rather than relying
    on these constants. Do not treat DEFAULT_COUNTDOWN_MS as ground truth.

CLI:
  python -m creative_suite.engine.round_intro                 # default treatment
  python -m creative_suite.engine.round_intro --sheet          # preview sheet, all treatments
  python -m creative_suite.engine.round_intro --map asylum --demo-hash abc123 --round-num 3
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

from creative_suite.engine import camera_paths
from creative_suite.engine import timeline as tl
from creative_suite.engine.pantheon_ads import (
    INK, GOLD, GOLD_HI, BONE, BRONZE, BRONZE_INK, STONE,
    _laurel, _marble, _logo_glyph,
)

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
FONTS_DIR = REPO_ROOT / "creative_suite" / "engine" / "assets" / "fonts"
OUT_DIR = REPO_ROOT / "creative_suite" / "engine" / "assets" / "round_intro"
ASSIGN_LOG = REPO_ROOT / "output" / "demo_v2" / "round_intro_assignments.json"

# Same red used by title_card.py's rim-glow layer (fontcolor=0x8a0a0a) — keep
# the round-intro graphics visually part of the same PANTHEON title-card series.
BLOOD = (0x8A, 0x0A, 0x0A)

# ---------------------------------------------------------------------------
# Round-start timing — see module docstring: DOCUMENTED APPROXIMATION.
# ---------------------------------------------------------------------------
DEFAULT_BEAT_MS = 1000.0
COUNTDOWN_WORDS = ("3", "2", "1", "FIGHT")
DEFAULT_COUNTDOWN_MS = DEFAULT_BEAT_MS * len(COUNTDOWN_WORDS)  # 4000.0


def default_countdown_window(round_start_ms: float) -> tuple[float, float]:
    """(start, end) ms for the countdown given an approximate round-start
    timestamp, using the DEFAULT_COUNTDOWN_MS approximation documented above.
    """
    return (float(round_start_ms), float(round_start_ms) + DEFAULT_COUNTDOWN_MS)


# ---------------------------------------------------------------------------
# Font loading (shares the exact TTF files title_card.py uses for hero text —
# BlackOpsOne / RussoOne / BungeeInline / BebasNeue — so the round-intro
# graphics read as the same series, not a new competing aesthetic).
# ---------------------------------------------------------------------------

def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONTS_DIR / name
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        for fallback in ("BebasNeue-Regular.ttf",):
            try:
                return ImageFont.truetype(str(FONTS_DIR / fallback), size)
            except OSError:
                continue
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# PIL layering helpers (PIL equivalent of title_card.py's ffmpeg filter-graph
# glow/scanline/chromatic-aberration effects — those are drawtext/geq filter
# strings and don't apply to a single PIL frame, so these are re-implemented
# here for the static graphic, following the SAME visual recipe).
# ---------------------------------------------------------------------------

def _ctext_bordered(d, cx, cy, text, font, fill, border=None, border_w=0,
                     tracking=0):
    """Centered text with an optional multi-offset outline (title_card.py's
    3D-slab border, minus the ffmpeg-specific shadowx/y syntax)."""
    if tracking:
        text = (" " * tracking).join(list(text))
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font)
    x = cx - (x1 - x0) / 2 - x0
    y = cy - (y1 - y0) / 2 - y0
    if border and border_w:
        for ox in (-border_w, 0, border_w):
            for oy in (-border_w, 0, border_w):
                if ox == 0 and oy == 0:
                    continue
                d.text((x + ox, y + oy), text, font=font, fill=border)
    d.text((x, y), text, font=font, fill=fill)


def _glow(alpha_source: Image.Image, color: tuple, radius: int) -> Image.Image:
    """Colored, blurred glow from the alpha channel of a text layer — PIL
    analog of title_card.py's rim-glow (`gblur=sigma=18` on a red text copy)."""
    if radius <= 0:
        return Image.new("RGBA", alpha_source.size, (0, 0, 0, 0))
    alpha = alpha_source.split()[-1]
    glow = Image.new("RGBA", alpha_source.size, color + (0,))
    glow.putalpha(alpha)
    return glow.filter(ImageFilter.GaussianBlur(radius))


def _scanlines(w: int, h: int, alpha: int) -> Image.Image:
    """PIL analog of title_card.py's 8%-opacity scanline overlay."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if alpha <= 0:
        return im
    d = ImageDraw.Draw(im)
    for y in range(0, h, 3):
        d.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    return im


def _aberration(base: Image.Image, px: int) -> Image.Image:
    """PIL analog of title_card.py's `rgbashift` chromatic-aberration pass
    (static offset here since this is a single frame, not an animated ramp)."""
    if px <= 0:
        return base
    r, g, b, a = base.split()
    r2 = ImageChops.offset(r, px, 0)
    b2 = ImageChops.offset(b, -px, 0)
    return Image.merge("RGBA", (r2, g, b2, a))


def _vignette_bg(w: int, h: int, color: tuple) -> Image.Image:
    im = Image.new("RGB", (w, h), color)
    d = ImageDraw.Draw(im)
    for i in range(6):
        pad = i * (min(w, h) // 14)
        shade = max(0, color[0] - i * 4), max(0, color[1] - i * 2), max(0, color[2] - i * 2)
        d.rectangle([pad, pad, w - pad, h - pad], outline=shade, width=2)
    return im


def _streak_bg(w: int, h: int, color: tuple) -> Image.Image:
    im = Image.new("RGB", (w, h), color)
    d = ImageDraw.Draw(im)
    for i in range(0, w, 24):
        d.line([(i, 0), (i - h * 0.4, h)], fill=(color[0] + 6, color[1] + 6, color[2] + 8), width=2)
    return im


def _beam_bg(w: int, h: int, color: tuple) -> Image.Image:
    im = Image.new("RGB", (w, h), color)
    d = ImageDraw.Draw(im)
    cx, cy = w / 2, h * 1.15
    for i in range(-4, 5):
        ang_w = 4
        x0 = cx + i * (w / 10)
        d.polygon([(cx, cy), (x0 - w * 0.03, 0), (x0 + w * 0.03, 0)],
                  fill=(min(255, color[0] + 10), min(255, color[1] + 8), color[2]))
    return im


def _stone_glyph_bg(w: int, h: int, color: tuple) -> Image.Image:
    im = Image.new("RGB", (w, h), color)
    try:
        g = _logo_glyph((color[0] - 40, color[1] - 40, color[2] - 40), (int(w * 0.5), int(h * 0.5)))
        im.paste(g, ((w - g.width) // 2, (h - g.height) // 2), g)
    except Exception:
        pass
    return im


# ---------------------------------------------------------------------------
# Graphic styles — genuinely distinct font + layering recipes, not palette
# swaps (pantheon_ads's parody/mono designs proved palette-only variation
# feels thin). Each style is keyed by a Treatment.graphic_style name.
# ---------------------------------------------------------------------------

GRAPHIC_STYLES: dict[str, dict] = {
    "gold_slab": dict(font="BlackOpsOne-Regular.ttf", fill=BONE, border=INK,
                       border_w=6, glow=GOLD, glow_radius=26, aberration_px=3,
                       scanline_alpha=18, tracking=0, laurel=True, bg="marble",
                       bg_color=INK),
    "crimson_hard": dict(font="RussoOne-Regular.ttf", fill=BONE, border=INK,
                          border_w=5, glow=BLOOD, glow_radius=10,
                          aberration_px=1, scanline_alpha=30, tracking=0,
                          laurel=False, bg="vignette", bg_color=(24, 9, 9)),
    "dramatic_bloom": dict(font="BlackOpsOne-Regular.ttf", fill=(255, 255, 255),
                            border=INK, border_w=6, glow=GOLD, glow_radius=44,
                            aberration_px=5, scanline_alpha=22, tracking=0,
                            laurel=False, bg="marble", bg_color=INK),
    "skyfall_streak": dict(font="BungeeInline-Regular.ttf", fill=BONE,
                            border=INK, border_w=4, glow=BLOOD, glow_radius=14,
                            aberration_px=2, scanline_alpha=14, tracking=2,
                            laurel=False, bg="streak", bg_color=(11, 11, 15)),
    "sharp_condensed": dict(font="BungeeInline-Regular.ttf", fill=(255, 255, 255),
                             border=BLOOD, border_w=5, glow=BLOOD, glow_radius=8,
                             aberration_px=6, scanline_alpha=10, tracking=4,
                             laurel=False, bg="plain", bg_color=(8, 8, 10)),
    "bronze_plaque": dict(font="RussoOne-Regular.ttf", fill=BRONZE_INK,
                           border=None, border_w=0, glow=None, glow_radius=0,
                           aberration_px=0, scanline_alpha=0, tracking=0,
                           laurel=True, bg="plain", bg_color=BRONZE),
    "arena_stone": dict(font="BebasNeue-Regular.ttf", fill=GOLD, border=INK,
                         border_w=4, glow=GOLD, glow_radius=16,
                         aberration_px=0, scanline_alpha=12, tracking=6,
                         laurel=False, bg="stone_glyph", bg_color=STONE),
    "ceremonial_marble": dict(font="BlackOpsOne-Regular.ttf", fill=GOLD,
                               border=INK, border_w=6, glow=GOLD_HI,
                               glow_radius=36, aberration_px=1,
                               scanline_alpha=16, tracking=0, laurel=True,
                               bg="marble", bg_color=INK),
    "low_menace": dict(font="RussoOne-Regular.ttf", fill=(230, 60, 50),
                        border=INK, border_w=5, glow=BLOOD, glow_radius=20,
                        aberration_px=4, scanline_alpha=26, tracking=0,
                        laurel=False, bg="vignette", bg_color=(7, 5, 5)),
    "ascension_beam": dict(font="BebasNeue-Regular.ttf", fill=BONE, border=INK,
                            border_w=4, glow=GOLD, glow_radius=30,
                            aberration_px=2, scanline_alpha=14, tracking=8,
                            laurel=True, bg="beam", bg_color=INK),
}

_BG_BUILDERS = {
    "marble": lambda w, h, c: _marble(w, h),
    "vignette": _vignette_bg,
    "streak": _streak_bg,
    "beam": _beam_bg,
    "stone_glyph": _stone_glyph_bg,
    "plain": lambda w, h, c: Image.new("RGB", (w, h), c),
}


def _fontsize_for(number_or_word: str, h: int) -> int:
    # single digits render bigger than the word "FIGHT"
    return int(h * (0.62 if len(number_or_word) <= 1 else 0.30))


def _tracked_text(text: str, tracking: int) -> str:
    return (" " * tracking).join(list(text)) if tracking else text


def _fit_font(font_name: str, text: str, tracking: int, start_size: int,
              max_w: float) -> ImageFont.FreeTypeFont:
    """Shrink-to-fit (same spirit as pantheon_ads._ctext's max_w guard) so
    tracked/wide treatments never clip off-canvas at any render size."""
    size = start_size
    scratch = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    font = _font(font_name, size)
    tracked = _tracked_text(text, tracking)
    bbox = scratch.textbbox((0, 0), tracked, font=font)
    while (bbox[2] - bbox[0]) > max_w and size > 10:
        size = int(size * 0.92)
        font = _font(font_name, size)
        bbox = scratch.textbbox((0, 0), tracked, font=font)
    return font


def render_countdown_graphic(treatment: "Treatment", number_or_word: str,
                              size: tuple[int, int] = (1920, 1080)) -> Image.Image:
    """Render one PIL frame for a countdown beat ("3"/"2"/"1"/"FIGHT") in the
    treatment's graphic_style, following title_card.py's visual language:
    metallic/gold-red fill, glow, scanlines, chromatic aberration on reveal,
    PANTHEON brand consistency (shared fonts + palette with the title card
    and ad-banner systems).
    """
    style = GRAPHIC_STYLES[treatment.graphic_style]
    w, h = size

    bg_builder = _BG_BUILDERS[style["bg"]]
    bg = bg_builder(w, h, style["bg_color"]).convert("RGBA")

    if style["laurel"]:
        d_bg = ImageDraw.Draw(bg)
        r = h * 0.28
        laurel_color = style["fill"] if isinstance(style["fill"], tuple) else GOLD
        _laurel(d_bg, w * 0.14, h * 0.54, r, laurel_color)
        _laurel(d_bg, w * 0.86, h * 0.54, r, laurel_color)

    text_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    td = ImageDraw.Draw(text_layer)
    font = _fit_font(style["font"], number_or_word, style["tracking"],
                      _fontsize_for(number_or_word, h), max_w=w * 0.86)
    _ctext_bordered(td, w / 2, h / 2, number_or_word, font, style["fill"],
                     border=style["border"], border_w=style["border_w"],
                     tracking=style["tracking"])

    glow_layer = _glow(text_layer, style["glow"], style["glow_radius"]) if style["glow"] else \
        Image.new("RGBA", (w, h), (0, 0, 0, 0))
    text_composite = Image.alpha_composite(glow_layer, text_layer)
    text_composite = _aberration(text_composite, style["aberration_px"])

    out = Image.alpha_composite(bg, text_composite)
    out = Image.alpha_composite(out, _scanlines(w, h, style["scanline_alpha"]))
    return out.convert("RGB")


# ---------------------------------------------------------------------------
# Treatment catalog
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Treatment:
    name: str
    camera_fn_name: str          # one of: orbit, vertical_orbit, side_track, top_down
    camera_params: dict = field(default_factory=dict)
    graphic_style: str = "gold_slab"
    slowmo: float | None = None  # target timescale rate during the hold, or None
    description: str = ""


CATALOG: list[Treatment] = [
    Treatment(
        "orbit_wide_gold", "orbit",
        {"radius": 420.0, "height": 90.0, "arc_deg": 140.0, "start_deg": 200.0, "fov": 100.0},
        "gold_slab", None,
        "Wide gold-lit orbit around the spawn circle; ceremonial slab numerals with laurel flourish.",
    ),
    Treatment(
        "orbit_tight_crimson", "orbit",
        {"radius": 170.0, "height": 36.0, "arc_deg": 260.0, "start_deg": 15.0, "fov": 72.0},
        "crimson_hard", 0.55,
        "Tight, fast orbit easing into a slow-mo crawl on FIGHT; hard-edged crimson numerals.",
    ),
    Treatment(
        "vertical_arc_dramatic", "vertical_orbit",
        {"radius": 300.0, "arc_deg": 70.0, "azimuth_deg": 45.0, "start_elev_deg": -8.0, "fov": 85.0},
        "dramatic_bloom", 0.4,
        "Low-to-high dramatic vertical sweep with heavy glow bloom and a slow ceremonial reveal.",
    ),
    Treatment(
        "vertical_arc_skyfall", "vertical_orbit",
        {"radius": 260.0, "arc_deg": -95.0, "azimuth_deg": 120.0, "start_elev_deg": 58.0, "fov": 95.0},
        "skyfall_streak", None,
        "High-to-low swooping descent; condensed streak typography suggests a falling camera.",
    ),
    Treatment(
        "side_track_tension", "side_track",
        {"lateral_offset": 260.0, "height": 48.0, "look_at": True, "fov": 80.0},
        "sharp_condensed", None,
        "Lateral dolly locked on the spawn point; razor-edged condensed lettering, heavy RGB split.",
    ),
    Treatment(
        "side_track_glide", "side_track",
        {"lateral_offset": 440.0, "height": 18.0, "look_at": False, "fov": 90.0},
        "bronze_plaque", None,
        "Wide gliding dolly looking forward past the arena; bronze plaque numerals, no glow.",
    ),
    Treatment(
        "top_down_arena", "top_down",
        {"height": 760.0, "fov": 90.0, "steps": 8},
        "arena_stone", None,
        "Static overhead shot of the full spawn area; tracked-out stone numerals over the temple glyph.",
    ),
    Treatment(
        "top_down_slow_reveal", "top_down",
        {"height": 1100.0, "fov": 80.0, "steps": 10},
        "ceremonial_marble", 0.3,
        "Very high overhead hold with a slow-motion ease; marble-and-gold numerals, laurel wreath.",
    ),
    Treatment(
        "orbit_low_menace", "orbit",
        {"radius": 140.0, "height": 18.0, "arc_deg": 100.0, "start_deg": -40.0, "fov": 68.0},
        "low_menace", None,
        "Low, close-radius ground-level orbit; blood-red backlit numerals for a menacing feel.",
    ),
    Treatment(
        "vertical_arc_ascension", "vertical_orbit",
        {"radius": 320.0, "arc_deg": 85.0, "azimuth_deg": 250.0, "start_elev_deg": -20.0, "fov": 90.0},
        "ascension_beam", 0.5,
        "Bottom-to-top ascension sweep with a slow-mo hold on FIGHT; tall tracked gold beam typography.",
    ),
]
BY_NAME = {t.name: t for t in CATALOG}


# ---------------------------------------------------------------------------
# Deterministic assignment with repetition control (same shape as
# pantheon_ads.assign_set()'s `recent` demotion logic).
# ---------------------------------------------------------------------------

def assign_treatment(map_name: str = "", demo_hash: str = "",
                      round_num: int = 0,
                      history: list[dict] | None = None) -> str:
    """Deterministic (map, demo_hash, round_num) -> treatment name, with
    repetition control: a treatment used in either of the previous 2
    assignments is demoted (mirrors pantheon_ads.assign_set §42)."""
    seed = hashlib.sha256(
        f"{map_name}|{demo_hash}|{round_num}".encode()).digest()
    recent = {a["treatment"] for a in (history or [])[-2:]}
    n = len(CATALOG)
    idx = seed[0] % n
    ranked = sorted(CATALOG, key=lambda t: (
        t.name in recent,                          # repetition demotion
        idx != CATALOG.index(t) % n,                # hash-preferred first
        t.name))                                    # stable tiebreak
    return ranked[0].name


def load_history() -> list[dict]:
    if ASSIGN_LOG.exists():
        return json.loads(ASSIGN_LOG.read_text())
    return []


def record_assignment(record: dict, treatment_name: str) -> None:
    ASSIGN_LOG.parent.mkdir(parents=True, exist_ok=True)
    log = load_history()
    log.append({**record, "treatment": treatment_name})
    ASSIGN_LOG.write_text(json.dumps(log, indent=1))


def assign_and_log(map_name: str = "", demo_hash: str = "",
                    round_num: int = 0) -> str:
    name = assign_treatment(map_name, demo_hash, round_num, load_history())
    record_assignment({"map": map_name, "demo_hash": demo_hash,
                        "round_num": round_num}, name)
    return name


# ---------------------------------------------------------------------------
# Camera plan — dispatches to ONE of camera_paths' four constructions.
# Keyframes are shot-relative (t_ms starts at 0), matching the convention
# every other camera_paths generator + timeline.to_wolfcam_script's
# base_servertime parameter already use (see director_session.save_recipe).
# ---------------------------------------------------------------------------

def build_camera_plan(treatment: Treatment, countdown_start_ms: float,
                       countdown_end_ms: float,
                       spawn_center: tuple[float, float, float]) -> dict:
    """Build keyframes + an optional slow-mo Timeline for one countdown.

    Returns {"keyframes": [...], "timeline": Timeline, "base_servertime": int}
    — consumable via
    timeline.to_wolfcam_script(plan["timeline"], plan["keyframes"],
                                plan["base_servertime"]).
    """
    duration_ms = float(countdown_end_ms) - float(countdown_start_ms)
    if duration_ms <= 0:
        raise ValueError(
            f"countdown_end_ms ({countdown_end_ms}) must be after "
            f"countdown_start_ms ({countdown_start_ms})")

    params = dict(treatment.camera_params)
    fn = treatment.camera_fn_name
    if fn == "orbit":
        keyframes = camera_paths.orbit(spawn_center, duration_ms=duration_ms,
                                        t0_ms=0.0, **params)
    elif fn == "vertical_orbit":
        keyframes = camera_paths.vertical_orbit(spawn_center, duration_ms=duration_ms,
                                                  t0_ms=0.0, **params)
    elif fn == "top_down":
        keyframes = camera_paths.top_down(spawn_center, duration_ms=duration_ms,
                                           t0_ms=0.0, **params)
    elif fn == "side_track":
        track = [(0.0, *spawn_center), (duration_ms, *spawn_center)]
        keyframes = camera_paths.side_track(track, **params)
    else:
        raise KeyError(f"unknown camera_fn_name {fn!r} on treatment {treatment.name!r}")

    timeline = tl.Timeline()
    if treatment.slowmo:
        rate = float(treatment.slowmo)
        ramp = min(400.0, duration_ms / 4.0)
        timeline.slow_to(0, rate, ramp_ms=ramp, easing="ease_out")
        timeline.resume(max(ramp, duration_ms - ramp), ramp_ms=ramp, easing="ease_in")

    return {"keyframes": keyframes, "timeline": timeline,
            "base_servertime": int(round(countdown_start_ms))}


# ---------------------------------------------------------------------------
# Preview sheet (VIS-1)
# ---------------------------------------------------------------------------

def build_sheet() -> Path:
    """Preview grid of all treatments' FIGHT graphic, for user sign-off."""
    tiles = [(t.name, render_countdown_graphic(t, "FIGHT", size=(640, 360)))
             for t in CATALOG]
    cols, pad, tw, th = 3, 24, 640, 400
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + pad) + pad),
                       (20, 20, 24))
    d = ImageDraw.Draw(sheet)
    f = _font("BebasNeue-Regular.ttf", 20)
    for i, (name, im) in enumerate(tiles):
        im2 = im.copy()
        im2.thumbnail((tw, th - 30), Image.LANCZOS)
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + pad)
        sheet.paste(im2, (x + (tw - im2.width) // 2, y))
        d.text((x, y + th - 26), name, font=f, fill=(200, 203, 209))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "round_intro_sheet.png"
    sheet.save(out)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--map", default="")
    ap.add_argument("--demo-hash", default="")
    ap.add_argument("--round-num", type=int, default=0)
    args = ap.parse_args()

    if args.sheet:
        print("sheet:", build_sheet())
    else:
        name = assign_and_log(args.map, args.demo_hash, args.round_num)
        print("treatment:", name)
