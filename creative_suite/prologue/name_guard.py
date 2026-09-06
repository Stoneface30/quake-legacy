"""Refuse to show a frame with a player's name burned into it.

WHY THIS EXISTS. The V2 review proxies still carry the obituary centerprint --
"You fragged <name>" -- rendered into the picture around y 210-265. The first
build of PROLOGUE_PROOF_01 put four real opponent handles on screen. This
project's rule is that no personal identifier reaches an output, and a rule
that depends on someone remembering to look is not a rule.

WHY DETECTION AND NOT A BLUR. Blurring the band was tried first and it looked
worse than the problem: a smeared horizontal strip across otherwise clean
gameplay. The obituary only exists for a few seconds after a kill, and a
review proxy is several seconds long, so there is almost always a clean window
-- the fix is to find it rather than to deface the frame.

HOW IT DETECTS. Quake's HUD text is pure white with hard edges. Game geometry
at 1080p with motion blur can be just as bright, but it is smooth. So a
pixel counts as glyph-like when it is near-white AND has a much darker pixel
within a few px. Blown-out walls fail the second test; text passes it easily.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

# Where Quake Live draws the obituary centerprint at 1920x1080. Generous on
# both sides of the measured 210-265 so a different font size still lands
# inside it.
BAND_TOP, BAND_BOTTOM = 190, 300

WHITE_MIN = 238         # a glyph is near-white
DARK_MAX = 140          # and sits against something clearly darker
EDGE_RADIUS = 3         # within this many px
MAX_CHROMA = 26         # and NEUTRAL: a rocket's core is white-hot but warm,
                        # and it was the only thing that ever fooled this
MIN_GLYPH_PIXELS = 55   # fewer than this is speckle, not a word

# The audit threshold above is where "this is text" begins. The PICKER uses a
# stricter one, because choosing a window that merely scrapes under the bar
# leaves no margin: an explosion core is white-hot, hard-edged and close
# enough to neutral to score in the fifties without being text at all. Clean
# windows normally score 0-15, so demanding that costs nothing and means an
# audit failure is always worth investigating rather than shrugging at.
PICK_MAX_GLYPH = 20


def glyph_pixels(frame: np.ndarray) -> int:
    """Count glyph-like pixels in the obituary band.

    `frame` is HxWx3 uint8, full frame. Returns the number of near-white,
    colour-neutral pixels that have a much darker pixel within EDGE_RADIUS on
    the same row -- the signature of rendered text over a scene. The
    neutrality test is what separates a glyph from an explosion core, which is
    just as bright and just as hard-edged but warm.
    """
    band = frame[BAND_TOP:BAND_BOTTOM].astype(np.int16)
    grey = band.mean(axis=2)
    chroma = band.max(axis=2) - band.min(axis=2)
    bright = (grey >= WHITE_MIN) & (chroma <= MAX_CHROMA)
    if not bright.any():
        return 0
    # a dark neighbour anywhere within EDGE_RADIUS on the row
    dark = grey <= DARK_MAX
    near_dark = np.zeros_like(dark)
    for shift in range(1, EDGE_RADIUS + 1):
        near_dark[:, shift:] |= dark[:, :-shift]
        near_dark[:, :-shift] |= dark[:, shift:]
    return int((bright & near_dark).sum())


def has_burned_text(frame: np.ndarray) -> bool:
    return glyph_pixels(frame) >= MIN_GLYPH_PIXELS


def scan_video(path: Path, ffmpeg: Path, ss: float, duration: float,
               samples: int = 6) -> int:
    """Worst glyph-pixel count across a segment.

    Sampled rather than exhaustive: the centerprint holds for seconds, so it
    cannot hide between samples spaced a few hundred milliseconds apart.
    """
    import subprocess
    worst = 0
    for n in range(samples):
        t = ss + duration * n / max(1, samples - 1)
        out = subprocess.run(
            [str(ffmpeg), "-v", "error", "-ss", f"{t:.3f}", "-i", str(path),
             "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            capture_output=True, timeout=120)
        if out.returncode != 0 or len(out.stdout) < 1920 * 1080 * 3:
            continue
        frame = np.frombuffer(out.stdout[:1920 * 1080 * 3],
                              dtype=np.uint8).reshape(1080, 1920, 3)
        worst = max(worst, glyph_pixels(frame))
    return worst


def find_clean_window(path: Path, ffmpeg: Path, duration: float,
                      span: float, *, preferred: float | None = None,
                      steps: int = 9) -> tuple[float, int]:
    """A start time whose whole segment is free of burned-in text.

    Tries the preferred point first, then walks earlier -- the obituary
    follows the kill, so earlier is where the clean footage is, and earlier is
    also the approach to the action rather than its aftermath.

    Returns (start, worst_glyph_pixels). The caller decides what to do when
    nothing is clean; this never silently returns a dirty window.
    """
    usable = max(0.0, duration - span)
    order: list[float] = []
    if preferred is not None:
        order.append(max(0.0, min(preferred, usable)))
    for n in range(steps):
        order.append(usable * (1 - n / max(1, steps - 1)) * 0.62)
    best = (order[0], 10 ** 9)
    for ss in order:
        worst = scan_video(path, ffmpeg, ss, span)
        if worst < best[1]:
            best = (ss, worst)
        if worst <= PICK_MAX_GLYPH:
            return ss, worst
    return best


# A centerprint is up for seconds -- QL holds the obituary for roughly three.
# A handful of consecutive frames is therefore never text, whatever it scores:
# the only things that spike this briefly are explosion cores and muzzle
# flashes. Requiring persistence is not a softening of the rule, it is a
# statement of what the rule is actually looking for.
MIN_TEXT_FRAMES = 20            # 0.33 s at 60 fps


def audit_video(path: Path, ffmpeg: Path) -> dict:
    """Scan every frame of a finished render for burned-in player names.

    Returns the worst score, and any RUN of consecutive frames long enough to
    be real text. A run is the finding; an isolated spike is reported but not
    treated as a failure.
    """
    import subprocess
    proc = subprocess.Popen(
        [str(ffmpeg), "-v", "error", "-i", str(path), "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = 1920 * 1080 * 3
    frames = 0
    worst = 0
    runs: list[tuple[int, int, int]] = []
    run_start: int | None = None
    run_peak = 0
    try:
        while True:
            buf = proc.stdout.read(n)
            if len(buf) < n:
                break
            g = glyph_pixels(np.frombuffer(buf, dtype=np.uint8)
                             .reshape(1080, 1920, 3))
            worst = max(worst, g)
            if g >= MIN_GLYPH_PIXELS:
                if run_start is None:
                    run_start, run_peak = frames, g
                run_peak = max(run_peak, g)
            elif run_start is not None:
                if frames - run_start >= MIN_TEXT_FRAMES:
                    runs.append((run_start, frames - run_start, run_peak))
                run_start = None
            frames += 1
        if run_start is not None and frames - run_start >= MIN_TEXT_FRAMES:
            runs.append((run_start, frames - run_start, run_peak))
    finally:
        try:
            proc.stdout.close()
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
            proc.wait()
    return {"frames": frames, "worst": worst, "text_runs": runs,
            "clean": not runs}
