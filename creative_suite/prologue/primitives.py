"""The prologue's visual vocabulary, as SVG that real data drives.

WHY CODE AND NOT MOCKUPS. Every one of these elements states a fact: an alive
counter says how many players are left, a speed readout says how fast someone
was going, an archive counter says how big the archive is. A mockup can show
any number. These take the number from the cache and cannot show a different
one, which is the whole point -- the prologue's credibility rests on the
audience being told true things in large type.

They are also the primitives the main film inherits. An alive counter built
here for a synthetic teaching round is the same counter that will sit over
ClanWar reconstruction later.

PALETTE. PANTHEON is grey/silver with the pTn gold and deep blue (Nauru flag).
Team colours are Quake's own red and blue, kept distinct from the clan blue so
a team marker is never confused with brand.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from html import escape
from typing import Sequence

# -- palette ----------------------------------------------------------------
INK = "#0a0b0d"          # the black everything sits on
SILVER = "#c8ccd2"       # PANTHEON primary
SILVER_DIM = "#6b7280"
GOLD = "#d4a63c"         # pTn gold
CLAN_BLUE = "#123a6b"    # pTn deep blue -- brand only, never a team
TEAM_RED = "#c8392f"
TEAM_BLUE = "#2f7fc8"
DEAD = "#2a2d33"

# Engine speed colour bands, cg_draw.c:844-857. These are the engine's own
# thresholds, so a PANTHEON readout agrees with what Quake would have coloured.
SPEED_BANDS: tuple[tuple[int, str], ...] = (
    (320, "#8a9099"), (420, "#c8ccd2"), (520, "#d4a63c"),
    (620, "#e08a2f"), (720, "#d4562f"), (820, "#e02f2f"),
)
BASE_RUN_UPS = 320       # g_main.c:152


def band_for(ups: float) -> str:
    """The engine's own colour for a speed. Never our invention."""
    colour = SPEED_BANDS[0][1]
    for threshold, c in SPEED_BANDS:
        if ups >= threshold:
            colour = c
    return colour


def _svg(w: int, h: int, body: str, *, bg: str = INK) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" font-family="Bebas Neue, Oswald, '
            f'Impact, sans-serif">'
            f'<rect width="{w}" height="{h}" fill="{bg}"/>{body}</svg>')


# -- alive counter ----------------------------------------------------------

def alive_counter(red: int, blue: int, *, red_start: int = 4,
                  blue_start: int = 4, w: int = 640, h: int = 160) -> str:
    """`4 - 3`, with a pip per player and the dead ones left visibly dark.

    A greyed pip that never comes back is how the audience learns "one life"
    without being told. The pips are why this is not just two numerals.
    """
    mid = w // 2
    out = [f'<text x="{mid}" y="{h * 0.62:.0f}" fill="{SILVER_DIM}" '
           f'font-size="{h * 0.42:.0f}" text-anchor="middle">&#8212;</text>']
    for alive, start, colour, sign in ((red, red_start, TEAM_RED, -1),
                                       (blue, blue_start, TEAM_BLUE, 1)):
        x = mid + sign * w * 0.17
        out.append(f'<text x="{x:.0f}" y="{h * 0.62:.0f}" fill="{colour}" '
                   f'font-size="{h * 0.52:.0f}" text-anchor="middle">{alive}</text>')
        for i in range(start):
            px = mid + sign * (w * 0.10 + i * 22)
            fill = colour if i < alive else DEAD
            out.append(f'<circle cx="{px:.0f}" cy="{h * 0.80:.0f}" r="7" '
                       f'fill="{fill}"/>')
    return _svg(w, h, "".join(out))


# -- speed readout ----------------------------------------------------------

def speed_readout(ups: float, *, w: int = 640, h: int = 200,
                  label: str = "MEASURED") -> str:
    """A measured speed, coloured by the engine's own bands.

    `label` defaults to MEASURED and should stay that way: the value comes
    from `movement_moments_v1`, a ~0.3 s segment average, so it understates the
    instantaneous peak. We are never overclaiming, and the word says so.
    """
    colour = band_for(ups)
    frac = min(1.0, ups / 900.0)
    ticks = "".join(
        f'<line x1="{40 + (w - 80) * t / 900:.0f}" y1="{h * 0.80:.0f}" '
        f'x2="{40 + (w - 80) * t / 900:.0f}" y2="{h * 0.86:.0f}" stroke="{c}" '
        f'stroke-width="2"/>'
        f'<text x="{40 + (w - 80) * t / 900:.0f}" y="{h * 0.97:.0f}" '
        f'fill="{SILVER_DIM}" font-size="15" text-anchor="middle">{t}</text>'
        for t, c in SPEED_BANDS)
    digits = len(str(int(round(ups))))
    body = (
        f'<text x="40" y="{h * 0.46:.0f}" fill="{colour}" '
        f'font-size="{h * 0.44:.0f}">{int(round(ups))}</text>'
        f'<text x="{40 + h * 0.44 * 0.62 * digits:.0f}" y="{h * 0.46:.0f}" '
        f'fill="{SILVER_DIM}" font-size="{h * 0.17:.0f}">ups</text>'
        f'<text x="{w - 40}" y="{h * 0.22:.0f}" fill="{SILVER_DIM}" '
        f'font-size="16" text-anchor="end" letter-spacing="3">'
        f'{escape(label)}</text>'
        f'<line x1="40" y1="{h * 0.70:.0f}" x2="{w - 40}" y2="{h * 0.70:.0f}" '
        f'stroke="{DEAD}" stroke-width="3"/>'
        f'<line x1="40" y1="{h * 0.70:.0f}" x2="{40 + (w - 80) * frac:.0f}" '
        f'y2="{h * 0.70:.0f}" stroke="{colour}" stroke-width="3"/>' + ticks)
    return _svg(w, h, body)


# -- archive counter --------------------------------------------------------

def archive_counter(value: int | str, caption: str, *, w: int = 720,
                    h: int = 240, accent: str = GOLD) -> str:
    """One big true number and what it counts. The Part 3 workhorse.

    The caption carries the denominator, because a number without its
    denominator is how "203,536 player kills" turns into a lie.
    """
    text = f"{value:,}" if isinstance(value, int) else str(value)
    return _svg(w, h,
                f'<text x="{w / 2:.0f}" y="{h * 0.56:.0f}" fill="{SILVER}" '
                f'font-size="{h * 0.46:.0f}" text-anchor="middle" '
                f'letter-spacing="2">{escape(text)}</text>'
                f'<line x1="{w * 0.35:.0f}" y1="{h * 0.68:.0f}" '
                f'x2="{w * 0.65:.0f}" y2="{h * 0.68:.0f}" stroke="{accent}" '
                f'stroke-width="2"/>'
                f'<text x="{w / 2:.0f}" y="{h * 0.84:.0f}" fill="{SILVER_DIM}" '
                f'font-size="{h * 0.11:.0f}" text-anchor="middle" '
                f'letter-spacing="6">{escape(caption.upper())}</text>')


# -- map constellation ------------------------------------------------------

@dataclass(frozen=True)
class MapWeight:
    name: str
    demos: int


def map_constellation(maps: Sequence[MapWeight], *, w: int = 900,
                      h: int = 420) -> str:
    """Every recorded map, each sized by how much of a life happened on it.

    campgrounds at 1,089 demos is genuinely 120x hearth at 9, and the picture
    should say so rather than flattering the long tail.
    """
    if not maps:
        return _svg(w, h, "")
    top = max(m.demos for m in maps)
    n = len(maps)
    ordered = sorted(maps, key=lambda x: -x.demos)
    circles: list[str] = []
    labels: list[str] = []
    # The biggest maps sort first, so a plain sunflower spiral stacks them all
    # on top of each other at the centre and their labels become an unreadable
    # pile. The +4 offset pushes the first few off dead-centre, and a placed-
    # label distance check drops any name that would collide with one already
    # written -- a missing label is recoverable, an illegible one is not.
    placed: list[tuple[float, float]] = []
    for i, m in enumerate(ordered):
        ang = i * 2.399963              # golden angle -- even, non-repeating
        rad = ((i + 4) / (n + 4)) ** 0.5 * min(w, h) * 0.44
        cx, cy = w / 2 + rad * math.cos(ang), h / 2 + rad * math.sin(ang)
        r = 4 + (m.demos / top) ** 0.5 * 26
        op = 0.28 + 0.72 * (m.demos / top) ** 0.4
        circles.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
                       f'fill="{SILVER}" opacity="{op:.2f}"/>')
        if m.demos < top * 0.35:
            continue
        ly = cy + r + 15
        if any(abs(px - cx) < 92 and abs(py - ly) < 15 for px, py in placed):
            continue
        placed.append((cx, ly))
        labels.append(f'<text x="{cx:.1f}" y="{ly:.1f}" fill="{GOLD}" '
                      f'font-size="14" text-anchor="middle" letter-spacing="2">'
                      f'{escape(m.name.upper())}</text>')
    return _svg(w, h, "".join(circles) + "".join(labels))


# -- round grid -------------------------------------------------------------

def round_grid(total: int, *, cols: int = 60, rows: int = 24, w: int = 900,
               h: int = 380, lit: int = 0) -> str:
    """One cell per round, until the frame runs out and the point is made.

    The caption states honestly how small a sample of the whole the frame is.
    `lit` cells carry the gold, for "and this many were yours".
    """
    cell_w, cell_h = w / cols, (h - 40) / rows
    shown = min(total, cols * rows)
    out = []
    for i in range(shown):
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_h
        fill = GOLD if i < lit else SILVER
        op = 0.85 if i < lit else 0.20 + 0.5 * ((i * 37) % 11) / 11
        out.append(f'<rect x="{cx + 1:.1f}" y="{cy + 1:.1f}" '
                   f'width="{cell_w - 2:.1f}" height="{cell_h - 2:.1f}" '
                   f'fill="{fill}" opacity="{op:.2f}"/>')
    out.append(f'<text x="{w / 2:.0f}" y="{h - 10:.0f}" fill="{SILVER_DIM}" '
               f'font-size="15" text-anchor="middle" letter-spacing="5">'
               f'{shown:,} OF {total:,} ROUNDS</text>')
    return _svg(w, h, "".join(out))


# -- role tiles -------------------------------------------------------------

ROLE_TILES: tuple[tuple[str, str], ...] = (
    ("T1", "FEATURE / FX"), ("T2", "TRANSITION"), ("T3", "RHYTHM / MONTAGE"),
    ("T4", "KEEP / NORMAL"), ("T5", "PASS / FILLER"),
)


def role_tiles(active: str | None = None, *, w: int = 900, h: int = 150) -> str:
    """The five human answers, in the film's language -- never a screenshot.

    Part 3 must not look like a software demo, so the review workstation's
    buttons are re-expressed as typography.
    """
    tw = w / len(ROLE_TILES)
    out = []
    for i, (key, label) in enumerate(ROLE_TILES):
        on = key == active
        x = i * tw
        out.append(f'<rect x="{x + 6:.0f}" y="6" width="{tw - 12:.0f}" '
                   f'height="{h - 12}" fill="{CLAN_BLUE if on else "#16181c"}" '
                   f'stroke="{GOLD if on else DEAD}" '
                   f'stroke-width="{2 if on else 1}"/>')
        out.append(f'<text x="{x + tw / 2:.0f}" y="{h * 0.42:.0f}" '
                   f'fill="{GOLD if on else SILVER_DIM}" font-size="34" '
                   f'text-anchor="middle">{key}</text>')
        out.append(f'<text x="{x + tw / 2:.0f}" y="{h * 0.70:.0f}" '
                   f'fill="{SILVER if on else SILVER_DIM}" font-size="14" '
                   f'text-anchor="middle" letter-spacing="2">'
                   f'{escape(label)}</text>')
    return _svg(w, h, "".join(out))


# -- weapon glyph row -------------------------------------------------------

def weapon_row(counts: Sequence[tuple[str, int]], *, w: int = 900,
               h: int = 200) -> str:
    """The eight spawn weapons, bar-weighted by what actually killed people.

    The gauntlet's 904 next to lightning's 77,688 is the honest shape of Clan
    Arena, and it is funnier than any line we could write.
    """
    if not counts:
        return _svg(w, h, "")
    top = max(c for _, c in counts)
    bw = w / len(counts)
    out = []
    for i, (name, c) in enumerate(counts):
        x = i * bw
        bh = (h - 80) * (c / top) ** 0.55
        out.append(f'<rect x="{x + bw * 0.22:.0f}" y="{h - 60 - bh:.0f}" '
                   f'width="{bw * 0.56:.0f}" height="{bh:.0f}" fill="{SILVER}" '
                   f'opacity="0.85"/>')
        out.append(f'<text x="{x + bw / 2:.0f}" y="{h - 38:.0f}" fill="{GOLD}" '
                   f'font-size="14" text-anchor="middle" letter-spacing="1">'
                   f'{escape(name.upper())}</text>')
        out.append(f'<text x="{x + bw / 2:.0f}" y="{h - 18:.0f}" '
                   f'fill="{SILVER_DIM}" font-size="13" text-anchor="middle">'
                   f'{c:,}</text>')
    return _svg(w, h, "".join(out))
