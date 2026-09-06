"""Frame generation for the prologue. PIL in, 1920x1080 out, ffmpeg downstream.

WHY PIL AND NOT THE SVG PRIMITIVES. The proof sheet's SVG is for reading; this
is for projecting. A moving picture needs per-frame control of easing, decay
and sub-pixel motion that a static SVG has no way to express, and rasterising
2,500 SVGs would cost more than drawing them.

The two share a palette and a set of rules, not code. Where a number appears in
both, it comes from `facts.py` in both.

EVERYTHING IS DETERMINISTIC. Given the same shot list, this renders the same
frames, because a proof you cannot re-render is a proof you cannot iterate on.
Any randomness is seeded from the shot id.
"""
from __future__ import annotations

import math
import random
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 60

# -- palette -----------------------------------------------------------------
# PANTHEON gold as specified for production. The proof sheet's SVG carries the
# same value; if one moves, both move.
GOLD = (232, 185, 35)
INK = (8, 9, 11)
SILVER = (200, 204, 210)
SILVER_DIM = (107, 114, 128)
DEAD = (38, 41, 47)
TEAM_RED = (200, 57, 47)
TEAM_BLUE = (47, 127, 200)
WHITE = (245, 246, 248)

# Engine speed colour bands, cg_draw.c:844-857.
SPEED_BANDS: tuple[tuple[int, tuple[int, int, int]], ...] = (
    (320, (138, 144, 153)), (420, (200, 204, 210)), (520, (232, 185, 35)),
    (620, (224, 138, 47)), (720, (212, 86, 47)), (820, (224, 47, 47)),
)
BASE_RUN_UPS = 320       # g_main.c:152 -- what the engine gives you for
                         # holding forward, and the number Part 1 is about
                         # beating

FONTS = Path("C:/Windows/Fonts")
_DISPLAY = FONTS / "ariblk.ttf"        # Arial Black -- heavy, and unlike
                                       # Impact it does not split a word into
                                       # "TRI BUTE" at display size (P1-Y v1)
_LABEL = FONTS / "bahnschrift.ttf"     # condensed, for captions and counters
_MONO = FONTS / "consolab.ttf"

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    key = (kind, size)
    if key not in _font_cache:
        path = {"display": _DISPLAY, "label": _LABEL, "mono": _MONO}[kind]
        _font_cache[key] = ImageFont.truetype(str(path), size)
    return _font_cache[key]


def band_for(ups: float) -> tuple[int, int, int]:
    colour = SPEED_BANDS[0][1]
    for threshold, c in SPEED_BANDS:
        if ups >= threshold:
            colour = c
    return colour


# -- easing ------------------------------------------------------------------
# Named rather than inlined so a shot reads as intent: `ease_out` on a counter
# means it decelerates into its final value, which is what makes a number feel
# like it landed rather than stopped.

def clamp01(x: float) -> float:
    return 0.0 if x < 0 else (1.0 if x > 1 else x)


def ease_out(t: float) -> float:
    return 1 - (1 - clamp01(t)) ** 3


def ease_in(t: float) -> float:
    return clamp01(t) ** 3


def ease_io(t: float) -> float:
    t = clamp01(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def pulse(t: float, at: float, width: float = 0.12) -> float:
    """A short spike at `at`, for one-frame flashes and hit accents."""
    d = abs(t - at)
    return 0.0 if d > width else (1 - d / width) ** 2


# -- drawing helpers ---------------------------------------------------------

def blank(colour: tuple[int, int, int] = INK, alpha: bool = False) -> Image.Image:
    if alpha:
        return Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return Image.new("RGB", (W, H), colour)


def tracked_text(d: ImageDraw.ImageDraw, xy: tuple[float, float], text: str,
                 f: ImageFont.FreeTypeFont, fill, *, tracking: int = 0,
                 anchor: str = "lt") -> float:
    """Letter-spaced text. PIL has no tracking, and display type without it
    looks cramped at this size. Returns the drawn width."""
    if not tracking:
        d.text(xy, text, font=f, fill=fill, anchor=anchor)
        return d.textlength(text, font=f)
    total = sum(d.textlength(c, font=f) for c in text) + tracking * (len(text) - 1)
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    va = "t" if len(anchor) < 2 else anchor[1]
    for c in text:
        d.text((x, y), c, font=f, fill=fill, anchor="l" + va)
        x += d.textlength(c, font=f) + tracking
    return total


def fade(img: Image.Image, amount: float) -> Image.Image:
    """Toward black. Used for shot tops and tails, never as a transition
    between parts -- P1-H bans dramatic fades."""
    a = clamp01(amount)
    if a >= 1.0:
        return img
    return Image.blend(Image.new(img.mode, img.size, (0, 0, 0)
                                 if img.mode == "RGB" else (0, 0, 0, 0)),
                       img, a)


def scanlines(img: Image.Image, opacity: int = 16) -> Image.Image:
    """8%-ish scanlines, matching the title-card treatment (P1-Y)."""
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(0, H, 3):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, opacity))
    base = img.convert("RGBA")
    return Image.alpha_composite(base, ov).convert(img.mode)


def vignette_px(img: Image.Image, strength: float = 0.35) -> Image.Image:
    """Cheap radial darkening. Built once and cached -- doing this per frame
    with a Python loop costs more than the rest of the render combined."""
    global _VIG
    if _VIG is None or _VIG[1] != strength:
        m = Image.new("L", (W, H), 255)
        dm = ImageDraw.Draw(m)
        steps = 48
        for i in range(steps):
            k = i / steps
            v = int(255 * (1 - strength * (k ** 2)))
            inset = int(k * min(W, H) * 0.62)
            dm.ellipse([-W * 0.25 + inset, -H * 0.35 + inset,
                        W * 1.25 - inset, H * 1.35 - inset], fill=v)
        _VIG = (m, strength)
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(img.convert("RGB"), dark, _VIG[0])


_VIG: tuple[Image.Image, float] | None = None


# -- reusable graphic primitives (the moving versions) -----------------------

def draw_speed_readout(d: ImageDraw.ImageDraw, ups: float, *,
                       x: int = 130, y: int = 820, reveal: float = 1.0,
                       label: str = "MEASURED") -> None:
    """The PANTHEON speed readout.

    `ups` must be a real measurement of the action on screen. The label says
    MEASURED because the value is a ~0.3 s segment average from
    `movement_moments_v1`, which understates the instantaneous peak -- we are
    never overclaiming, and the word admits it.
    """
    if reveal <= 0:
        return
    colour = band_for(ups)
    fbig = font("display", 132)
    value = str(int(round(ups)))
    wv = tracked_text(d, (x, y), value, fbig, colour, tracking=2, anchor="lb")
    d.text((x + wv + 22, y - 8), "ups", font=font("label", 54),
           fill=SILVER_DIM, anchor="lb")
    d.text((x + 4, y - 152), label, font=font("label", 26), fill=SILVER_DIM,
           anchor="lb")
    # the band ruler -- the engine's own thresholds, so our graphic agrees
    # with what Quake itself would have coloured
    bx, by, bw = x + 4, y + 34, 620
    d.line([(bx, by), (bx + bw, by)], fill=DEAD, width=4)
    frac = min(1.0, ups / 900.0) * reveal
    d.line([(bx, by), (bx + bw * frac, by)], fill=colour, width=4)
    for t, c in SPEED_BANDS:
        tx = bx + bw * t / 900
        d.line([(tx, by + 6), (tx, by + 16)], fill=c, width=2)
        d.text((tx, by + 22), str(t), font=font("label", 20), fill=SILVER_DIM,
               anchor="mt")


def draw_alive_counter(d: ImageDraw.ImageDraw, red: int, blue: int, *,
                       red_start: int = 4, blue_start: int = 4,
                       cx: int = W // 2, cy: int = 130,
                       flash: float = 0.0) -> None:
    """`4 - 3`, with a pip per player.

    The pip is the teaching device: it goes dark on death and stays dark until
    the round resets. That is how one-life-per-round is explained without a
    card -- the card that follows only confirms what was already seen.
    """
    fnum = font("display", 92)
    d.text((cx, cy), "\u2014", font=font("label", 76), fill=SILVER_DIM,
           anchor="mm")
    for alive, start, colour, sign in ((red, red_start, TEAM_RED, -1),
                                       (blue, blue_start, TEAM_BLUE, 1)):
        col = colour
        if flash > 0:
            col = tuple(int(c + (255 - c) * flash) for c in colour)
        d.text((cx + sign * 130, cy), str(alive), font=fnum, fill=col,
               anchor="mm")
        for i in range(start):
            px = cx + sign * (66 + i * 30)
            d.ellipse([px - 8, cy + 62, px + 8, cy + 78],
                      fill=colour if i < alive else DEAD)


def draw_counter(d: ImageDraw.ImageDraw, value: int, caption: str, *,
                 progress: float = 1.0, cy: int = H // 2,
                 accent=GOLD, prefix: str = "") -> None:
    """One big true number and what it counts.

    The caption carries the denominator, because a number without its
    denominator is how "203,536 player kills" becomes a lie about one player.
    """
    # round, not truncate: int() spent the last frames of every counter one
    # short of the true figure, and a number that reads 4,291 for 4,292 is a
    # wrong number no matter how briefly it is up
    shown = round(value * ease_out(progress))
    text = f"{prefix}{shown:,}"
    tracked_text(d, (W // 2, cy), text, font("display", 190), SILVER,
                 tracking=4, anchor="mm")
    if progress > 0.55:
        a = clamp01((progress - 0.55) / 0.45)
        lw = int(340 * a)
        d.line([(W // 2 - lw, cy + 132), (W // 2 + lw, cy + 132)],
               fill=accent, width=3)
        tracked_text(d, (W // 2, cy + 196), caption.upper(),
                     font("label", 40), SILVER_DIM, tracking=11, anchor="mm")


def draw_card(d: ImageDraw.ImageDraw, text: str, *, reveal: float = 1.0,
              size: int = 150, cy: int = H // 2, fill=WHITE,
              tracking: int = 14, sub: str | None = None) -> None:
    """A word on black. Revealed per character, never faded up as a block."""
    n = max(1, int(len(text) * clamp01(reveal) + 0.999))
    tracked_text(d, (W // 2, cy), text[:n], font("display", size), fill,
                 tracking=tracking, anchor="mm")
    if sub and reveal >= 1.0:
        tracked_text(d, (W // 2, cy + size * 0.78), sub, font("label", 38),
                     SILVER_DIM, tracking=10, anchor="mm")


# -- the render loop ---------------------------------------------------------

@dataclass
class Shot:
    """One shot. `draw` gets (frame_index, t01, seconds) and returns an image.

    `footage` names a clip this shot composites over; when set, `draw` must
    return RGBA and the caller overlays it.
    """
    shot_id: str
    part: str
    seconds: float
    draw: Callable[[int, float, float], Image.Image]
    purpose: str
    source: str = "SYNTHETIC_GRAPHIC"
    provenance: str = "SYNTHETIC_EXPLAINER"
    text: str = ""
    graphics: str = ""
    slot: str | None = None
    footage: dict | None = None
    audio: list = field(default_factory=list)

    @property
    def frames(self) -> int:
        return max(1, round(self.seconds * FPS))


def render_shot(shot: Shot, out: Path, ffmpeg: Path, *,
                crf: int = 16) -> Path:
    """Render one graphic shot straight into ffmpeg over a pipe.

    Frames are never written to disk. A 40-second proof is 2,400 frames, and
    round-tripping those through PNG costs more time than generating them.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(ffmpeg), "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-profile:v", "high", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        n = shot.frames
        for i in range(n):
            img = shot.draw(i, i / max(1, n - 1), i / FPS)
            if img.mode != "RGB":
                img = img.convert("RGB")
            p.stdin.write(img.tobytes())
        p.stdin.close()
        rc = p.wait(timeout=300)
    except BaseException:
        # CS-4: a pipe left open leaves an ffmpeg holding the output file.
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            p.kill()
            p.wait()
        raise
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed on {shot.shot_id} (rc={rc})")
    return out


def render_overlay_shot(shot: Shot, out: Path, ffmpeg: Path, *,
                        crf: int = 16) -> Path:
    """Render a shot that composites generated graphics over real footage.

    The footage is cut and normalised (CFR, 1080p) by the same ffmpeg call
    that does the overlay, so there is no intermediate file to go stale.
    """
    f = shot.footage or {}
    src, ss = f["path"], float(f.get("ss", 0.0))
    vf = f.get("vf", "")
    # ORDER MATTERS. A shot's own filter goes in BEFORE `fps`, never after.
    # `setpts=PTS*2.4` placed after the frame-rate lock rewrites timestamps on
    # an already-normalised stream, so the shot rendered its 168 frames across
    # 6.68 s at ~25 fps -- and concat then carried that wrong duration into the
    # master, pushing every later shot out of place. Filtering first and
    # locking the rate last means a shot is always exactly `seconds` long at
    # exactly FPS, whatever it does to time internally.
    chain = "[0:v]setpts=PTS-STARTPTS"
    if vf:
        chain += "," + vf
    chain += (f",fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H},trim=duration={shot.seconds},setpts=PTS-STARTPTS")
    chain += "[base];[base][1:v]overlay=0:0:format=auto[v]"
    cmd = [str(ffmpeg), "-v", "error", "-y",
           "-ss", f"{ss}", "-i", str(src),
           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-",
           "-filter_complex", chain, "-map", "[v]",
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-frames:v", str(shot.frames), str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        n = shot.frames
        for i in range(n):
            img = shot.draw(i, i / max(1, n - 1), i / FPS)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            p.stdin.write(img.tobytes())
        p.stdin.close()
        rc = p.wait(timeout=300)
    except BaseException:
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            p.kill()
            p.wait()
        raise
    if rc != 0:
        raise RuntimeError(f"ffmpeg overlay failed on {shot.shot_id} (rc={rc})")
    return out


def rng_for(shot_id: str) -> random.Random:
    """Seeded per shot, so a re-render is identical."""
    return random.Random(shot_id)
