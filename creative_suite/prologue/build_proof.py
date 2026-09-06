"""PROLOGUE_PROOF_01 -- the first moving proof of the three-part opening.

WHAT THIS IS. Roughly forty seconds proving the LANGUAGE of all three parts in
one continuous piece: feel Quake, understand Clan Arena, meet the archive. It
is not the 3:20 prologue and is not a master.

WHAT IT IS HONEST ABOUT.

The speed climb is a real recorded run -- moment 43000, campgrounds, 575 to
1040 ups over 1.85 s, 97.9th percentile, ending in a frag. It is drawn as a
graphic rather than burned over gameplay because the review proxies available
today contain no measured high-speed movement: the fastest thing measured
inside any proxy window is a 109 ups jump-pad hop. Putting a 1040 ups climb
over that footage would be precisely the "animation disconnected from the
footage" the brief forbids, so the number and the picture are kept apart until
a capture exists that carries both.

Every gameplay shot is TEMP. Nothing here is assigned; each carries a slot id
and is replaced when human review says what that moment is for.

    python -m creative_suite.prologue.build_proof
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from creative_suite.prologue import facts, motion as m, name_guard
from creative_suite.prologue.motion import (
    DEAD, GOLD, INK, SILVER, SILVER_DIM, TEAM_BLUE, TEAM_RED, WHITE, H, W,
    Shot, blank, clamp01, draw_alive_counter, draw_card, draw_counter,
    draw_speed_readout, ease_in, ease_io, ease_out, font, fade, pulse,
    rng_for, scanlines, tracked_text, vignette_px)

REPO = Path(__file__).resolve().parents[2]
FFMPEG = Path(os.environ.get(
    "QL_FFMPEG", REPO / "creative_suite/tools/ffmpeg/ffmpeg.exe"))
OUT = Path(os.environ.get("QL_PROOF_OUT", REPO / "output/prologue"))
SOUNDS = REPO / "creative_suite/engine/sound_templates/raw/sound"

# The measured run that drives the Part 1 speed graphic. Not a chosen-looking
# number: it is movement_moments_v1 id 43000, and `verify_speed_moment()`
# re-reads it so the graphic cannot drift from the cache.
ACCEL_MOMENT = 43000
ACCEL = {"entry": 574.8, "peak": 1040.3, "dur_ms": 1850, "map": "campgrounds",
         "pctile": 97.9, "distance": 1377.6}


# ── temp footage ────────────────────────────────────────────────────────────
# Every entry is a placeholder. `slot` is the contract with human review; when
# a verdict names a moment for that slot, the path here is replaced and
# nothing else about the edit changes.

TEMP_SHOTS = [
    # (slot,               frag_id, purpose in the burst)
    ("SLOT_BURST_MOVEMENT", 29041, "movement into a shot"),
    ("SLOT_BURST_PREDICT", 27960, "explosive prediction"),
    ("SLOT_BURST_WARP", None, "spatial discontinuity -- telefrag"),
    ("SLOT_BURST_PRECISION", 36850, "instant precision -- rail"),
    ("SLOT_BURST_IMPACT", 5979, "impact"),
    ("SLOT_BURST_TRACK", 22154, "continuous pressure -- lightning"),
]


# ── name safety ─────────────────────────────────────────────────────────────
# The V2 review proxies still burn the obituary centerprint -- "You fragged
# <name>" -- into the picture around y 210-265. The first build of this proof
# put four real opponent handles on screen.
#
# Blurring the band was tried and rejected: it looked worse than the problem,
# a smeared strip across otherwise clean gameplay. The obituary only lives for
# a few seconds after a kill, so the fix is to find a window without it --
# which is also the approach to the action rather than its aftermath, and
# therefore the better shot. `name_guard` scans candidate windows and the
# build refuses any footage it cannot clear.

def proxy_index() -> dict[int, dict]:
    """READY review proxies, with the weapon the recogniser named.

    Read-only, and from the review workstation's own store: this workstream
    reads what review produced and never writes to it.
    """
    ed = sqlite3.connect(
        f"file:{(facts.DB_ROOT / 'editorial.db').as_posix()}?mode=ro", uri=True)
    rec = sqlite3.connect(
        f"file:{facts.RECOGNITION_DB.as_posix()}?mode=ro", uri=True)
    rows = ed.execute("select frag_id, mp4_path, start_ms, end_ms from "
                      "review_proxies where state='READY'").fetchall()
    ids = [r[0] for r in rows]
    qm = ",".join("?" * len(ids))
    meta = {r[0]: r[1] for r in rec.execute(
        f"select id, weapon_name from recognized_frags where id in ({qm})", ids)}
    out = {}
    for fid, path, s, e in rows:
        if path and Path(path).exists():
            out[fid] = {"path": path, "weapon": meta.get(fid),
                        "start_ms": s, "end_ms": e}
    ed.close()
    rec.close()
    return out


def verify_speed_moment() -> dict:
    """Re-read the run the speed graphic depicts. A graphic that drifts from
    its source is a graphic that lies at 190 point."""
    with sqlite3.connect(
            f"file:{facts.RECOGNITION_DB.as_posix()}?mode=ro", uri=True) as c:
        row = c.execute(
            "select entry_speed, peak_speed, duration_ms, map, speed_pctile, "
            "distance_units, traits from movement_moments_v1 where moment_id=?",
            (ACCEL_MOMENT,)).fetchone()
    if not row:
        raise RuntimeError(f"movement moment {ACCEL_MOMENT} is gone")
    entry, peak, dur, mp, pct, dist, traits = row
    for name, live, claimed in (("entry", entry, ACCEL["entry"]),
                                ("peak", peak, ACCEL["peak"]),
                                ("dur_ms", dur, ACCEL["dur_ms"])):
        if abs(live - claimed) > max(1.0, abs(claimed) * 0.01):
            raise RuntimeError(
                f"speed graphic drifted: {name} is {live}, film says {claimed}")
    return {"moment_id": ACCEL_MOMENT, "entry_speed": entry, "peak_speed": peak,
            "duration_ms": dur, "map": mp, "speed_pctile": pct,
            "distance_units": dist, "traits": traits}


# ══ PART 1 ══════════════════════════════════════════════════════════════════

def s01_black(i, t, sec):
    """Two seconds of nothing. The film starts by refusing to start."""
    img = blank()
    d = ImageDraw.Draw(img)
    if t > 0.55:                       # the first thing on screen is a sound,
        a = clamp01((t - 0.55) / 0.45)  # and then the faintest horizon line
        y = H * 0.5
        wdt = int(W * 0.35 * ease_out(a))
        c = int(40 * a)
        d.line([(W / 2 - wdt, y), (W / 2 + wdt, y)], fill=(c, c, c), width=2)
    return img


def s02_speed(i, t, sec):
    """A real run's speed climb, drawn as data.

    The bars behind are the run's distance accumulating, not decoration: the
    moment covers 1,377 units in 1.85 s, and the field fills at the same rate
    the number climbs.
    """
    img = blank()
    d = ImageDraw.Draw(img)
    hold = 0.62                        # climb, then hold so the peak reads
    k = ease_io(clamp01(t / hold)) if t < hold else 1.0
    ups = ACCEL["entry"] + (ACCEL["peak"] - ACCEL["entry"]) * k
    rng = rng_for("s02")
    # travel field -- horizontal streaks whose speed follows the readout
    for n in range(90):
        base = rng.random()
        y = 120 + rng.random() * (H - 240)
        speed = 0.35 + rng.random() * 0.9
        x = (base + t * speed * (ups / 420.0)) % 1.6 - 0.3
        ln = 40 + rng.random() * 190 * (ups / 700.0)
        v = int(26 + 54 * rng.random())
        d.line([(x * W, y), (x * W + ln, y)], fill=(v, v, v + 4), width=1)
    draw_speed_readout(d, ups, reveal=1.0)
    # provenance, small, always on: this is a specific recorded run
    tracked_text(d, (W - 130, 150), ACCEL["map"].upper(), font("label", 34),
                 SILVER_DIM, tracking=8, anchor="rt")
    tracked_text(d, (W - 130, 196),
                 f"MOMENT {ACCEL_MOMENT} · {ACCEL['pctile']:.0f}TH PERCENTILE",
                 font("label", 22), (90, 95, 104), tracking=4, anchor="rt")
    if t > 0.80:
        a = clamp01((t - 0.80) / 0.20)
        tracked_text(d, (W // 2, H * 0.30), "MOVEMENT IS A WEAPON",
                     font("display", 62), (int(232 * a), int(185 * a),
                                           int(35 * a)), tracking=16,
                     anchor="mm")
    return vignette_px(scanlines(img))


def burst_shot(idx: int, slot: str, path: str, ss: float, dur: float,
               purpose: str, weapon: str | None) -> Shot:
    """One cut of the opening burst.

    The overlay is almost nothing -- a slot stamp and a one-frame flash on the
    cut. The footage is doing the work; the graphics stay out of its way.
    """
    def draw(i, t, sec, _slot=slot, _n=idx):
        ov = blank(alpha=True)
        d = ImageDraw.Draw(ov)
        f = pulse(t, 0.0, 0.22)
        if f > 0:
            d.rectangle([0, 0, W, H], fill=(255, 255, 255, int(70 * f)))
        # TEMP stamp: this frame is a placeholder and says so on itself
        d.text((72, H - 72), f"TEMP · {_slot}", font=font("mono", 22),
               fill=(232, 185, 35, 150), anchor="ls")
        return ov

    return Shot(shot_id=f"S03.{idx}", part="P1", seconds=dur, draw=draw,
                purpose=purpose, source="V2_REVIEW_PROXY",
                provenance="HISTORICAL_UNREVIEWED_TEMP", slot=slot,
                graphics="cut flash + temp stamp",
                footage={"path": path, "ss": ss},
                audio=[("weapon", weapon)])


def s04_silence(i, t, sec):
    """1.2 seconds of nothing at all, picture and sound.

    This is the most important cut in the proof. Seven events land in a second
    and a half and then everything stops, which is what makes the burst read as
    speed rather than noise. If a viewer only remembers one thing about the
    edit, it should be that the film was confident enough to stop.
    """
    return blank()


def s05_quake(i, t, sec):
    img = blank()
    d = ImageDraw.Draw(img)
    draw_card(d, "QUAKE.", reveal=clamp01(t / 0.35), size=176, tracking=22)
    f = pulse(t, 0.36, 0.07)
    if f > 0:
        d.rectangle([0, 0, W, H], fill=(int(255 * f), int(255 * f), int(255 * f)))
    return scanlines(img)


def s06_arena_fps(i, t, sec):
    img = blank()
    d = ImageDraw.Draw(img)
    a = ease_out(clamp01(t / 0.30))
    c = tuple(int(x * a) for x in SILVER)
    tracked_text(d, (W // 2, H // 2), "FAST ARENA FPS", font("display", 96),
                 c, tracking=20, anchor="mm")
    if t > 0.55:
        b = clamp01((t - 0.55) / 0.3)
        wdt = int(300 * ease_out(b))
        d.line([(W // 2 - wdt, H // 2 + 84), (W // 2 + wdt, H // 2 + 84)],
               fill=GOLD, width=3)
    return scanlines(img)


# ══ PART 2 ══════════════════════════════════════════════════════════════════

def _arena_geometry():
    """A small deterministic arena. Not a real BSP -- a legible stand-in whose
    only job is to give the round somewhere to happen."""
    rng = rng_for("arena")
    rooms = []
    for _ in range(9):
        cx = 320 + rng.random() * (W - 640)
        cy = 300 + rng.random() * (H - 560)
        rw = 120 + rng.random() * 240
        rh = 90 + rng.random() * 160
        rooms.append((cx - rw / 2, cy - rh / 2, cx + rw / 2, cy + rh / 2))
    return rooms


ARENA = _arena_geometry()
SPAWNS = [(560, 760), (640, 690), (500, 640), (700, 800),
          (1360, 360), (1280, 430), (1420, 480), (1220, 320)]


def _draw_arena(d, build: float, *, dim: float = 1.0):
    """VOID -> WIREFRAME -> GEOMETRY. The map assembling itself is how Part 2
    introduces the arena without a establishing shot it does not have."""
    for n, (x0, y0, x1, y1) in enumerate(ARENA):
        appear = clamp01((build - n * 0.055) / 0.30)
        if appear <= 0:
            continue
        v = int(118 * appear * dim)
        if build > 0.55:                        # geometry fills in behind
            g = int(34 * clamp01((build - 0.55) / 0.45) * dim)
            d.rectangle([x0, y0, x1, y1], fill=(g, g + 1, g + 3))
        d.rectangle([x0, y0, x1, y1], outline=(v, v + 4, v + 10), width=2)


def _draw_players(d, alive_red, alive_blue, *, appear=1.0, dead_marks=()):
    for n, (x, y) in enumerate(SPAWNS):
        if n / len(SPAWNS) > appear:
            continue
        red = n < 4
        idx = n if red else n - 4
        alive = idx < (alive_red if red else alive_blue)
        col = (TEAM_RED if red else TEAM_BLUE) if alive else DEAD
        r = 13 if alive else 9
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        if not alive:
            d.line([(x - 7, y - 7), (x + 7, y + 7)], fill=(70, 74, 82), width=2)
            d.line([(x - 7, y + 7), (x + 7, y - 7)], fill=(70, 74, 82), width=2)


def s07_arena(i, t, sec):
    img = blank()
    d = ImageDraw.Draw(img)
    _draw_arena(d, ease_out(clamp01(t / 0.75)))
    if t > 0.45:
        a = clamp01((t - 0.45) / 0.3)
        tracked_text(d, (W // 2, 150), "CLAN ARENA", font("display", 78),
                     tuple(int(x * a) for x in SILVER), tracking=20,
                     anchor="mm")
    return vignette_px(img, 0.45)


def s08_teams(i, t, sec):
    img = blank()
    d = ImageDraw.Draw(img)
    _draw_arena(d, 1.0, dim=0.85)
    _draw_players(d, 4, 4, appear=ease_out(clamp01(t / 0.35)))
    if t > 0.30:
        draw_alive_counter(d, 4, 4)
    if t > 0.42:
        a = clamp01((t - 0.42) / 0.22)
        tracked_text(d, (W // 2, H - 210), "USUALLY FOUR A SIDE",
                     font("label", 44), tuple(int(x * a) for x in SILVER_DIM),
                     tracking=12, anchor="mm")
    # the real 7-second countdown, compressed: 3 - 2 - 1
    if t > 0.52:
        k = (t - 0.52) / 0.48
        n = 3 - int(k * 3)
        if 1 <= n <= 3:
            sub = (k * 3) % 1.0
            scale = 1.0 + 0.18 * (1 - ease_out(sub))
            alpha = int(255 * (1 - sub ** 2))
            tracked_text(d, (W // 2, H // 2), str(n),
                         font("display", int(220 * scale)),
                         (alpha, alpha, alpha), anchor="mm")
    return vignette_px(img, 0.45)


def s09_fight(i, t, sec):
    img = blank()
    d = ImageDraw.Draw(img)
    _draw_arena(d, 1.0, dim=0.85)
    _draw_players(d, 4, 4)
    draw_alive_counter(d, 4, 4)
    a = 1 - ease_in(clamp01(t / 0.7))
    tracked_text(d, (W // 2, H // 2), "FIGHT", font("display", 150),
                 (int(232 * a + 200 * (1 - a)), int(185 * a + 200 * (1 - a)),
                  int(35 * a + 200 * (1 - a))), tracking=18, anchor="mm")
    if t < 0.12:
        f = 1 - t / 0.12
        d.rectangle([0, 0, W, H], fill=(int(255 * f),) * 3)
    return vignette_px(img, 0.45)


def s10_first_kill(i, t, sec):
    """The teaching shot: a marker goes dark and stays dark."""
    img = blank()
    d = ImageDraw.Draw(img)
    _draw_arena(d, 1.0, dim=0.85)
    killed = t > 0.34
    _draw_players(d, 4, 3 if killed else 4)
    # the tactical camera: a line travelling from shooter to victim, arriving
    # exactly on the kill
    a, b = SPAWNS[0], SPAWNS[6]
    k = ease_io(clamp01(t / 0.34))
    if t <= 0.42:
        px = a[0] + (b[0] - a[0]) * k
        py = a[1] + (b[1] - a[1]) * k
        d.line([a, (px, py)], fill=(120, 126, 136), width=2)
        d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=WHITE)
    if killed:
        f = pulse(t, 0.36, 0.10)
        r = int(26 + 90 * (1 - clamp01((t - 0.34) / 0.25)))
        d.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r],
                  outline=(200, 90, 80), width=2)
        if f > 0:
            d.rectangle([0, 0, W, H], fill=(int(90 * f),) * 3)
    draw_alive_counter(d, 4, 3 if killed else 4,
                       flash=pulse(t, 0.36, 0.14))
    if t > 0.56:
        a2 = clamp01((t - 0.56) / 0.2)
        tracked_text(d, (W // 2, H - 190), "ONE LIFE", font("display", 66),
                     tuple(int(x * a2) for x in GOLD), tracking=18, anchor="mm")
    return vignette_px(img, 0.45)


def s11_exchanges(i, t, sec):
    img = blank()
    d = ImageDraw.Draw(img)
    _draw_arena(d, 1.0, dim=0.85)
    red, blue = (4, 3)
    if t > 0.30:
        red, blue = 3, 3
    if t > 0.62:
        red, blue = 3, 2
    _draw_players(d, red, blue)
    draw_alive_counter(d, red, blue,
                       flash=max(pulse(t, 0.30, 0.10), pulse(t, 0.62, 0.10)))
    if t > 0.78:
        a = clamp01((t - 0.78) / 0.22)
        tracked_text(d, (W // 2, H - 190), "NO RESPAWN", font("label", 46),
                     tuple(int(x * a) for x in SILVER_DIM), tracking=12,
                     anchor="mm")
    return vignette_px(img, 0.45)


def s12_round_won(i, t, sec):
    """Round resolves, resets, and then the reset multiplies -- which is the
    seam into Part 3. Repetition becomes scale without a wipe."""
    img = blank()
    d = ImageDraw.Draw(img)
    if t < 0.30:
        _draw_arena(d, 1.0, dim=0.85)
        _draw_players(d, 3, 0)
        draw_alive_counter(d, 3, 0, flash=pulse(t, 0.06, 0.12))
        a = clamp01(t / 0.12)
        tracked_text(d, (W // 2, H - 190), "ROUND WON", font("display", 64),
                     tuple(int(x * a) for x in GOLD), tracking=18, anchor="mm")
    elif t < 0.46:                                # the reset snap
        k = clamp01((t - 0.30) / 0.16)
        _draw_arena(d, 1.0, dim=0.85)
        _draw_players(d, 4, 4)
        draw_alive_counter(d, 4, 4)
        f = 1 - ease_out(k)
        d.rectangle([0, 0, W, H], fill=(int(200 * f),) * 3)
    else:                                          # and multiplies
        k = ease_in(clamp01((t - 0.46) / 0.54))
        n = 1 + int(k * 13)
        cols = min(n, 6)
        rows = max(1, (n + cols - 1) // cols)
        cw, ch = W / cols, H / max(rows, 1)
        for idx in range(n):
            cx0, cy0 = (idx % cols) * cw, (idx // cols) * ch
            sc = min(cw / W, ch / H) * 0.92
            d.rectangle([cx0 + 6, cy0 + 6, cx0 + cw - 6, cy0 + ch - 6],
                        outline=(46, 50, 58), width=1)
            for (x0, y0, x1, y1) in ARENA[:6]:
                d.rectangle([cx0 + x0 * sc + cw * 0.04,
                             cy0 + y0 * sc + ch * 0.04,
                             cx0 + x1 * sc + cw * 0.04,
                             cy0 + y1 * sc + ch * 0.04],
                            outline=(34, 38, 44), width=1)
        if t > 0.72:
            a = clamp01((t - 0.72) / 0.28)
            tracked_text(d, (W // 2, H // 2), "AGAIN.", font("display", 92),
                         tuple(int(x * a) for x in SILVER), tracking=20,
                         anchor="mm")
    return vignette_px(img, 0.45)


# ══ PART 3 ══════════════════════════════════════════════════════════════════

DEMO_NAMES = None


def demo_sample(n: int = 400) -> list[str]:
    """Real demo filenames, with the player name removed.

    The archive section shows its own filenames because invented ones would
    look invented -- but a QL demo name carries the recorder's handle and the
    opponents' server, so only the shape is kept.
    """
    global DEMO_NAMES
    if DEMO_NAMES is None:
        with sqlite3.connect(
                f"file:{facts.REBUILT_DB.as_posix()}?mode=ro", uri=True) as c:
            rows = c.execute(
                "select map_name, year from demos order by rowid limit ?",
                (n,)).fetchall()
        DEMO_NAMES = [f"CA-{(mp or 'unknown')[:16]}-{yr}-....dm_73"
                      for mp, yr in rows]
    return DEMO_NAMES


def s13_demos(i, t, sec):
    img = blank()
    d = ImageDraw.Draw(img)
    names = demo_sample()
    k = ease_in(clamp01(t / 0.62))
    count = int(1 + k * 300)
    fm = font("mono", 17)
    rng = rng_for("s13")
    for idx in range(count):
        col = idx % 6
        row = idx // 6
        x = 80 + col * 305
        y = 120 + (row * 26) - k * 1500
        if -30 < y < H:
            v = int(40 + 80 * rng.random())
            d.text((x, y), names[idx % len(names)], font=fm, fill=(v, v, v + 5))
    if t > 0.55:
        # finishes at 0.87 and HOLDS. A counter that is still moving when the
        # shot cuts never shows the audience the figure it was counting to.
        p = clamp01((t - 0.55) / 0.32)
        d.rectangle([0, 0, W, H], fill=None)
        ov = Image.new("RGBA", (W, H), (8, 9, 11, int(215 * ease_out(p))))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        d = ImageDraw.Draw(img)
        draw_counter(d, 4292, "demos", progress=p)
    return vignette_px(img, 0.4)


def _count_shot(value: int, caption: str, sub: str | None = None, *,
                prefix: str = ""):
    def draw(i, t, sec):
        img = blank()
        d = ImageDraw.Draw(img)
        draw_counter(d, value, caption, progress=clamp01(t / 0.78),
                     prefix=prefix)
        if sub and t > 0.80:
            a = clamp01((t - 0.80) / 0.20)
            tracked_text(d, (W // 2, H // 2 + 270), sub, font("label", 27),
                         tuple(int(x * a) for x in (90, 95, 104)), tracking=5,
                         anchor="mm")
        return vignette_px(img, 0.4)
    return draw


def s16_denominator(i, t, sec):
    """203,536 kills; 33,316 were the user's.

    The lit fraction is the true ratio, so the distinction between "every kill
    in the archive" and "the user's own frags" is made by the picture instead
    of by a disclaimer nobody reads.
    """
    img = blank()
    d = ImageDraw.Draw(img)
    cols, rows = 64, 26
    total = cols * rows
    mine = round(total * 33316 / 203536)
    cw, ch = W / cols, (H - 300) / rows
    rng = rng_for("s16")
    sort = ease_io(clamp01((t - 0.22) / 0.5))
    for idx in range(total):
        cx = (idx % cols) * cw
        cy = 190 + (idx // cols) * ch
        is_mine = idx < mine
        if is_mine:
            col = tuple(int(a + (b - a) * sort)
                        for a, b in zip((150, 152, 158), GOLD))
        else:
            v = int((110 - 78 * sort) * (0.5 + 0.5 * rng.random()))
            col = (v, v, v + 3)
        d.rectangle([cx + 1, cy + 1, cx + cw - 2, cy + ch - 2], fill=col)
    if t > 0.62:
        a = clamp01((t - 0.62) / 0.38)
        tracked_text(d, (W // 2, H - 78), "33,316 OF THEM WERE MINE",
                     font("display", 58),
                     tuple(int(x * a) for x in GOLD), tracking=12, anchor="mm")
    tracked_text(d, (W // 2, 96), "203,536 PLAYER KILLS", font("label", 40),
                 SILVER_DIM, tracking=11, anchor="mm")
    return vignette_px(img, 0.4)


ORGANISE_GROUPS = [("RAIL", GOLD), ("ROCKET", (224, 138, 47)),
                   ("LG", (200, 204, 210)), ("AIRSHOT", (120, 190, 220)),
                   ("HIGH SPEED", (150, 220, 170)), ("1vX", (220, 140, 190))]


def s17_machine(i, t, sec):
    """Points settling into groups. The machine's whole job, in one gesture.

    It sorts by what the event IS -- weapon, movement, situation -- because
    that is the only thing it can know. It never sorts by quality.
    """
    img = blank()
    d = ImageDraw.Draw(img)
    rng = rng_for("s17")
    n = 1400
    k = ease_io(clamp01((t - 0.14) / 0.62))
    for idx in range(n):
        g = idx % len(ORGANISE_GROUPS)
        sx, sy = rng.random() * W, 120 + rng.random() * (H - 340)
        col_x = 205 + g * 302
        tx = col_x + (rng.random() - 0.5) * 118
        ty = 322 + ((idx // len(ORGANISE_GROUPS)) % 44) * 13 + rng.random() * 5
        x = sx + (tx - sx) * k
        y = sy + (ty - sy) * k
        base = ORGANISE_GROUPS[g][1]
        v = 0.30 + 0.70 * k
        r = 2 + 1.4 * k
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=tuple(int(c * v) for c in base))
    if t > 0.55:
        a = clamp01((t - 0.55) / 0.25)
        for g, (label, col) in enumerate(ORGANISE_GROUPS):
            tracked_text(d, (205 + g * 302, 268), label, font("label", 30),
                         tuple(int(c * a) for c in col), tracking=4,
                         anchor="mm")
    tracked_text(d, (W // 2, 110), "THE MACHINE ORGANISES", font("display", 54),
                 SILVER, tracking=15, anchor="mm")
    return vignette_px(img, 0.4)


ROLES = [("T1", "FEATURE / FX"), ("T2", "TRANSITION"), ("T3", "RHYTHM"),
         ("T4", "KEEP"), ("T5", "PASS")]


def s18_human(i, t, sec):
    """One moment, five answers, and a person choosing.

    Deliberately not the review website: the buttons are re-expressed as the
    film's own typography, because Part 3 must not look like a software demo.
    """
    img = blank()
    d = ImageDraw.Draw(img)
    tracked_text(d, (W // 2, 110), "THE HUMAN CURATES", font("display", 54),
                 SILVER, tracking=15, anchor="mm")
    # the single moment under consideration
    bx, by, bw, bh = W // 2 - 340, 205, 680, 350
    d.rectangle([bx, by, bx + bw, by + bh], fill=(18, 20, 24),
                outline=(52, 56, 64), width=2)
    rng = rng_for("s18")
    for _ in range(150):
        x = bx + rng.random() * bw
        y = by + rng.random() * bh
        v = int(30 + 50 * rng.random())
        d.line([(x, y), (x + 18, y)], fill=(v, v, v + 3), width=1)
    chosen = t > 0.42
    tw = 344
    for n, (key, label) in enumerate(ROLES):
        x = W // 2 - (tw * len(ROLES)) // 2 + n * tw + tw // 2
        on = chosen and n == 0
        d.rectangle([x - tw // 2 + 8, 626, x + tw // 2 - 8, 800],
                    fill=(18, 34, 62) if on else (16, 18, 22),
                    outline=GOLD if on else (38, 41, 47), width=2 if on else 1)
        tracked_text(d, (x, 682), key, font("display", 54),
                     GOLD if on else SILVER_DIM, tracking=3, anchor="mm")
        tracked_text(d, (x, 758), label, font("label", 25),
                     SILVER if on else (78, 82, 90), tracking=3, anchor="mm")
    if t > 0.58:                       # the annotation, typed
        note = "FREEZE / ENEMY POV / XRAY"
        n_ch = int(len(note) * clamp01((t - 0.58) / 0.32))
        tracked_text(d, (W // 2, 878), note[:n_ch], font("mono", 38), WHITE,
                     tracking=3, anchor="mm")
        if n_ch < len(note) and i % 12 < 6:
            tracked_text(d, (W // 2 + tracked_len(d, note[:n_ch]) / 2 + 12, 878),
                         "_", font("mono", 38), GOLD, anchor="mm")
        tracked_text(d, (W // 2, 940), "PLACEHOLDER ANNOTATION · "
                     "NO HUMAN VERDICT EXISTS YET", font("label", 20),
                     (86, 90, 98), tracking=4, anchor="mm")
    return vignette_px(img, 0.4)


def tracked_len(d, text, f=None, tracking=3) -> float:
    f = f or font("mono", 38)
    if not text:
        return 0.0
    return sum(d.textlength(c, font=f) for c in text) + tracking * (len(text) - 1)


def s19_becomes(i, t, sec):
    """The annotation becomes the effect.

    The single most important idea in Part 3: a human sentence changes what
    the picture does. Freeze, then an x-ray pass, then release.
    """
    ov = blank(alpha=True)
    d = ImageDraw.Draw(ov)
    d.text((72, H - 72), "TEMP · SLOT_ANNOTATION_DEMO", font=font("mono", 22),
           fill=(232, 185, 35, 150), anchor="ls")
    if t < 0.22:
        a = int(255 * (1 - t / 0.22))
        tracked_text(d, (W // 2, 140), "FREEZE / ENEMY POV / XRAY",
                     font("mono", 34), (255, 255, 255, a), tracking=3,
                     anchor="mm")
    # x-ray sweep: a band that reads as the wall going transparent
    if 0.24 < t < 0.78:
        k = (t - 0.24) / 0.54
        bx = int(-300 + k * (W + 600))
        for off in range(0, 260, 4):
            x = bx + off
            if 0 <= x < W:
                a = int(70 * math_sin(off / 260))
                d.line([(x, 0), (x, H)], fill=(150, 210, 255, a), width=4)
        tracked_text(d, (W // 2, H - 150), "XRAY", font("display", 52),
                     (150, 210, 255, 200), tracking=16, anchor="mm")
    return ov


def math_sin(x: float) -> float:
    import math as _m
    return _m.sin(x * _m.pi)


def s20_pantheon(i, t, sec):
    img = blank()
    d = ImageDraw.Draw(img)
    a = ease_out(clamp01(t / 0.35))
    # the temple mark, drawn rather than loaded: columns and an architrave
    cx, cy = W // 2, H // 2 - 60
    span = int(190 * a)
    if a > 0:
        d.line([(cx - span, cy - 62), (cx + span, cy - 62)],
               fill=tuple(int(c * a) for c in SILVER), width=5)
        d.line([(cx - span - 16, cy - 48), (cx + span + 16, cy - 48)],
               fill=tuple(int(c * a) for c in SILVER), width=3)
        for n in range(5):
            x = cx - span + 12 + n * (2 * span - 24) / 4
            k = clamp01((a - n * 0.06) / 0.5)
            d.line([(x, cy - 44), (x, cy - 44 + 96 * k)],
                   fill=tuple(int(c * 0.85 * a) for c in SILVER), width=7)
        d.line([(cx - span, cy + 56), (cx + span, cy + 56)],
               fill=tuple(int(c * a) for c in SILVER), width=5)
    if t > 0.34:
        b = clamp01((t - 0.34) / 0.28)
        tracked_text(d, (cx, cy + 156), "PANTHEON", font("display", 74),
                     tuple(int(c * b) for c in GOLD), tracking=26, anchor="mm")
    if t > 0.56:
        c2 = clamp01((t - 0.56) / 0.3)
        tracked_text(d, (cx, cy + 246), "ONE SEARCHABLE QUAKE CAREER",
                     font("label", 38),
                     tuple(int(x * c2) for x in SILVER_DIM), tracking=12,
                     anchor="mm")
    out = scanlines(vignette_px(img, 0.5))
    if t > 0.86:                                   # out to black, not a wipe
        out = fade(out, 1 - clamp01((t - 0.86) / 0.14))
    return out


# ── the shot list ───────────────────────────────────────────────────────────


def pick_clean_footage(px: dict[int, dict], weapon: str | None, span: float,
                       used: set[int], cache: dict) -> tuple[int, float]:
    """A proxy with a text-free window of `span` seconds, preferring `weapon`.

    Footage is chosen for what it contains and for being safe to show, never
    for being good -- goodness is human review's call, and every clip here is
    a placeholder waiting to be replaced.
    """
    def order():
        if weapon:
            for fid, info in px.items():
                if fid not in used and info.get("weapon") == weapon:
                    yield fid, info
        for fid, info in px.items():
            if fid not in used:
                yield fid, info

    for fid, info in order():
        key = (fid, round(span, 2))
        if key not in cache:
            dur = (info["end_ms"] - info["start_ms"]) / 1000.0
            cache[key] = name_guard.find_clean_window(
                Path(info["path"]), FFMPEG, dur, span,
                preferred=max(0.0, dur * 0.30))
        ss, glyphs = cache[key]
        if glyphs <= name_guard.PICK_MAX_GLYPH:
            used.add(fid)
            return fid, ss
    raise RuntimeError(
        f"no proxy has a {span:.2f}s window free of burned-in player names")


def build_shots(px: dict[int, dict]) -> list[Shot]:
    shots: list[Shot] = [
        Shot("S01", "P1", 2.0, s01_black,
             "refuse to start; the first event is a sound",
             text="", graphics="horizon line",
             audio=[("player/anarki/jump1.wav", 0.9)]),
        Shot("S02", "P1", 3.4, s02_speed,
             "a real recorded run climbing 575 -> 1040 ups",
             text="MOVEMENT IS A WEAPON",
             graphics="PANTHEON speed readout + engine bands + travel field",
             audio=[("world/jumppad.wav", 0.5)]),
    ]
    # the burst -- movement, prediction, warp, precision, impact, tracking
    # movement, prediction, warp, precision, impact, tracking -- a real
    # progression, not six random cuts because the theme is speed
    burst_plan = [
        ("SLOT_BURST_MOVEMENT", "ROCKET_SPLASH", 0.42, "movement into a shot"),
        ("SLOT_BURST_PREDICT", "ROCKET", 0.34, "explosive prediction"),
        ("SLOT_BURST_WARP", "TELEFRAG", 0.26, "spatial discontinuity"),
        ("SLOT_BURST_PRECISION", "RAILGUN", 0.30, "instant precision"),
        ("SLOT_BURST_IMPACT", "ROCKET", 0.34, "impact"),
        ("SLOT_BURST_TRACK", "LIGHTNING", 0.52, "continuous pressure"),
    ]
    used: set[int] = set()
    cache: dict = {}
    for n, (slot, weapon, dur, purpose) in enumerate(burst_plan, start=1):
        fid, ss = pick_clean_footage(px, weapon, dur, used, cache)
        info = px[fid]
        shots.append(burst_shot(n, slot, info["path"], ss, dur, purpose,
                                info.get("weapon")))
    shots += [
        Shot("S04", "P1", 1.2, s04_silence,
             "the silence that makes the burst legible",
             graphics="none -- picture and sound both stop", audio=[]),
        Shot("S05", "P1", 1.3, s05_quake, "name it", text="QUAKE.",
             graphics="card + one-frame flash",
             audio=[("weapons/rocket/rocklx1a.wav", 0.55)]),
        Shot("S06", "P1", 1.4, s06_arena_fps, "classify it",
             text="FAST ARENA FPS", graphics="card + gold rule"),

        Shot("S07", "P2", 2.0, s07_arena,
             "void -> wireframe -> geometry; the arena assembles",
             text="CLAN ARENA", graphics="map build"),
        Shot("S08", "P2", 2.6, s08_teams,
             "teams, and the real 7 s countdown compressed to 3-2-1",
             text="USUALLY FOUR A SIDE",
             graphics="8 markers + alive counter + countdown",
             audio=[("world/telein.wav", 0.4)]),
        Shot("S09", "P2", 1.0, s09_fight, "the round starts", text="FIGHT",
             graphics="flash + counter",
             audio=[("feedback/hit3.wav", 0.5)]),
        Shot("S10", "P2", 2.2, s10_first_kill,
             "a marker goes dark and stays dark",
             text="ONE LIFE", graphics="tactical camera + alive counter 4-3",
             audio=[("weapons/railgun/railgf1a.wav", 0.6)]),
        Shot("S11", "P2", 1.9, s11_exchanges, "two more eliminations",
             text="NO RESPAWN", graphics="alive counter 3-3, 3-2",
             audio=[("weapons/rocket/rocklx1a.wav", 0.45)]),
        Shot("S12", "P2", 2.9, s12_round_won,
             "round resolves, resets, multiplies -- the seam into Part 3",
             text="ROUND WON / AGAIN.", graphics="reset snap + round grid",
             audio=[("feedback/hit.wav", 0.5)]),

        Shot("S13", "P3", 2.6, s13_demos, "filenames become a number",
             text="4,292 DEMOS", graphics="filename cascade + counter"),
        Shot("S14", "P3", 1.9, _count_shot(78730, "rounds",
                                           "ROUNDS CARRYING A CANONICAL KILL"),
             "the rounds behind the archive", text="78,730 ROUNDS",
             graphics="archive counter"),
        # 450 with an OVER, never 453. The derivation is a lower bound --
        # warmup and the tail after the last kill are outside it -- so an
        # exact figure would be the one thing on screen that is not true.
        Shot("S15", "P3", 1.9, _count_shot(
            450, "hours", "LOWER BOUND · FIRST KILL TO LAST, PER DEMO",
            prefix="OVER "),
             "time, stated as the bound it is", text="OVER 450 HOURS",
             graphics="archive counter"),
        Shot("S16", "P3", 2.6, s16_denominator,
             "the denominator beat -- whose kills these are",
             text="33,316 OF THEM WERE MINE",
             graphics="203,536 cells, the user's fraction lit"),
        Shot("S17", "P3", 2.6, s17_machine,
             "points settle into what they ARE, never into quality",
             text="THE MACHINE ORGANISES", graphics="1,400 points sorting"),
        Shot("S18", "P3", 2.8, s18_human,
             "five answers, and a person choosing one",
             text="THE HUMAN CURATES", graphics="role tiles + typed annotation"),
    ]
    # the annotation becoming the effect, over temp footage
    # runs 2.4x slower, so it consumes 2.8/2.4 s of source
    demo_fid, ss19 = pick_clean_footage(px, "LIGHTNING", 2.8 / 2.4, used, cache)
    info = px[demo_fid]
    shots.append(Shot(
        "S19", "P3", 2.8, s19_becomes,
        "a human sentence changes what the picture does",
        source="V2_REVIEW_PROXY", provenance="HISTORICAL_UNREVIEWED_TEMP",
        slot="SLOT_ANNOTATION_DEMO", text="XRAY",
        graphics="freeze + xray sweep",
        footage={"path": info["path"], "ss": ss19, "vf": "setpts=PTS*2.4"},
        audio=[("world/teleout.wav", 0.5)]))
    shots.append(Shot("S20", "P3", 3.0, s20_pantheon, "the mark, and the line",
                      text="PANTHEON / ONE SEARCHABLE QUAKE CAREER",
                      graphics="temple mark"))
    return shots


# ── audio ───────────────────────────────────────────────────────────────────

def build_audio(shots: list[Shot], out: Path) -> Path:
    """Real Quake sounds on the beats, plus an authored percussive guide.

    The guide is synthesised here, on purpose. A temp commercial track would
    shape the cut around music that will never ship, and the brief is explicit
    that nothing gets baked around a temp song. What this bed proves is
    structure only: pulse, the two hard breaks, and the silence at 7.5 s.
    """
    total = sum(s.seconds for s in shots)
    inputs: list[str] = []
    chains: list[str] = []
    idx = 0

    # -- the guide: a low pulse whose density changes per part, and which
    #    STOPS DEAD for the silence beat. Section edges are the two hard breaks.
    p1_end = sum(s.seconds for s in shots if s.part == "P1")
    p2_end = p1_end + sum(s.seconds for s in shots if s.part == "P2")
    sil_start = sum(s.seconds for s in shots
                    if int(s.shot_id.split(".")[0][1:]) < 4 or
                    s.shot_id.startswith("S03"))
    sil_end = sil_start + 1.2

    beats: list[tuple[float, float, int]] = []      # (t, gain, freq)
    t = 2.0
    while t < total:
        if sil_start - 0.05 <= t < sil_end:         # the designed silence
            t += 0.25
            continue
        if t < p1_end:
            step, gain, freq = 0.25, 0.32, 52       # dense, driving
        elif t < p2_end:
            step, gain, freq = 0.50, 0.24, 44       # sparse, legible
        else:
            step, gain, freq = 0.40, 0.20, 38       # low, wide
        beats.append((t, gain, freq))
        t += step
    for bt, gain, freq in beats:
        inputs += ["-f", "lavfi", "-t", "0.30", "-i",
                   f"sine=frequency={freq}:sample_rate=48000"]
        chains.append(f"[{idx}:a]adelay={int(bt*1000)}|{int(bt*1000)},"
                      f"afade=t=out:st=0.02:d=0.26,volume={gain}[b{idx}]")
        idx += 1

    # -- real game sounds on their shots
    at = 0.0
    for s in shots:
        for entry in s.audio:
            rel, gain = entry if isinstance(entry, tuple) else (entry, 0.6)
            if rel is None or not isinstance(rel, str):
                continue
            path = SOUNDS / rel
            if not path.exists():
                continue
            inputs += ["-i", str(path)]
            chains.append(f"[{idx}:a]aresample=48000,adelay="
                          f"{int(at*1000)}|{int(at*1000)},volume={gain}[b{idx}]")
            idx += 1
        at += s.seconds

    mix = "".join(f"[b{n}]" for n in range(idx))
    chains.append(f"{mix}amix=inputs={idx}:duration=longest:normalize=0,"
                  f"alimiter=limit=0.92,aformat=sample_fmts=fltp:"
                  f"channel_layouts=stereo[a]")
    cmd = ([str(FFMPEG), "-v", "error", "-y"] + inputs +
           ["-filter_complex", ";".join(chains), "-map", "[a]",
            "-t", f"{total:.3f}", "-c:a", "aac", "-b:a", "192k", str(out)])
    subprocess.run(cmd, check=True, timeout=600)
    return out


# ── assembly ────────────────────────────────────────────────────────────────

def main() -> int:
    if not FFMPEG.exists():
        print(f"FATAL: ffmpeg not at {FFMPEG}")
        return 1
    speed = verify_speed_moment()
    px = proxy_index()
    if not px:
        print("FATAL: no READY review proxies on disk")
        return 1
    print(f"speed moment verified: {speed['peak_speed']:.1f} ups peak on "
          f"{speed['map']}")
    print(f"temp footage pool: {len(px)} V2 proxies")

    shots = build_shots(px)
    work = OUT / "work"
    work.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    for s in shots:
        dest = work / f"{s.shot_id}.mp4"
        if s.footage:
            m.render_overlay_shot(s, dest, FFMPEG)
        else:
            m.render_shot(s, dest, FFMPEG)
        parts.append(dest)
        print(f"  {s.shot_id:7s} {s.part}  {s.seconds:5.2f}s  {s.purpose[:52]}")

    concat = work / "concat.txt"
    concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts),
                      encoding="utf-8")
    silent = work / "silent.mp4"
    subprocess.run([str(FFMPEG), "-v", "error", "-y", "-f", "concat",
                    "-safe", "0", "-i", str(concat), "-c", "copy",
                    str(silent)], check=True, timeout=600)

    audio = build_audio(shots, work / "bed.m4a")

    master = OUT / "PROLOGUE_PROOF_01.mp4"
    subprocess.run([str(FFMPEG), "-v", "error", "-y", "-i", str(silent),
                    "-i", str(audio), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", str(master)], check=True, timeout=600)

    review = OUT / "PROLOGUE_PROOF_01_review.mp4"
    subprocess.run([str(FFMPEG), "-v", "error", "-y", "-i", str(master),
                    "-vf", "scale=1280:720", "-c:v", "libx264", "-preset",
                    "veryfast", "-crf", "26", "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart", str(review)],
                   check=True, timeout=600)

    manifest = {
        "proof": "PROLOGUE_PROOF_01",
        "built_at": __import__("datetime").datetime.now().isoformat(
            timespec="seconds"),
        "resolution": f"{W}x{H}", "fps": m.FPS,
        "duration_s": round(sum(s.seconds for s in shots), 3),
        "master": str(master), "review_copy": str(review),
        "speed_source": speed,
        "facts_used": [r for r in facts.verify() if r["on_screen"]],
        "shots": [{"shot_id": s.shot_id, "part": s.part,
                   "seconds": round(s.seconds, 3), "purpose": s.purpose,
                   "source": s.source, "provenance": s.provenance,
                   "text": s.text, "graphics": s.graphics, "slot": s.slot,
                   "footage": (Path(s.footage["path"]).name
                               if s.footage else None),
                   "temporary": s.provenance == "HISTORICAL_UNREVIEWED_TEMP"}
                  for s in shots],
    }
    mpath = OUT / "PROLOGUE_PROOF_01_manifest.json"
    mpath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nmaster : {master}")
    print(f"review : {review}")
    print(f"manifest: {mpath}")
    print(f"duration: {manifest['duration_s']}s  "
          f"temp shots: {sum(1 for s in shots if s.slot)}")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
