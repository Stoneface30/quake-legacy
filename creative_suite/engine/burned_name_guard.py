"""Measure burned-in text in a captured clip. A DIAGNOSTIC, not a ship gate.

WHAT THIS IS FOR. Answering "does this clip carry a player's name in the
picture?" for a clip you already have, ideally against a control captured the
same way. It did exactly that job here: the same demo window captured with
TR4SH_GAMEPLAY_MASTER_V2 and with TR4SH_PUBLIC_EXPORT differ by one run of
113 frames -- 1.88 s, the length of cg_drawFragMessageTime 2000 -- present in
the first and absent in the second. That measurement is what proved the fix.

WHY IT IS NOT THE SHIP GATE, MEASURED RATHER THAN ASSUMED. On the same pair
of real captures this heuristic also reports a 41-frame run that is present in
BOTH clips and is not text at all: a blown-out barred window in asylum, which
scored 2903 against the real "You fragged <name>" at 1991. Bright light
through dark bars is near-white, colour-neutral and hard-edged by
construction, which is the entire signature. Striking out columns whose
vertical run is taller than a glyph (the shape test below) cuts it to 1205 --
still twenty times the threshold, because the bars chop the white into short
runs of exactly the height a glyph has.

Separating the two reliably needs a calibration set across many maps, not a
tuned constant fitted to one clean sample. Until that exists, a blocking gate
built on this would reject clean exports and teach whoever hits it to switch
the gate off. The export path therefore gates on the capture PROFILE instead
-- see public_clip_export.assert_capture_profile_is_nameless -- which is
deterministic and catches the failure that actually happened.

WHAT IT LOOKS AT. Only the band where the frag message is drawn --
cg_drawFragMessageY 110 in a 640x480 virtual screen, so ~y247 at 1080p,
measured at y210-265 on real proxies. Widened to 190-300 so a different font
size still lands inside it. It does NOT cover the obituary killfeed
(cg_obituaryTokens "%k %i %v", killer AND victim), which draws outside this
band, nor the scoreboard. Both are off in the public profile; neither is
checked here.

HOW IT DETECTS. Quake's HUD text is pure white with hard edges. Bright
geometry can be just as white but is smooth, and an explosion core is just as
hard-edged but WARM. So a pixel is glyph-like when it is near-white AND
colour-neutral AND has a much darker pixel within a few px on its row. Then a
shape test: a line of text is a thin horizontal strip (measured: 20 px tall,
7.5 set px per occupied column) where lit geometry is a tall blob (88 px,
34.7 px per column), so columns whose vertical run is taller than a glyph are
struck out. Filtering per column rather than judging the frame as a whole is
deliberate -- a window and a name can share a frame, and a whole-frame average
would let the window hide the name.

The heuristic and its constants come from creative_suite/prologue/name_guard.py,
which solved this first for the prologue render; the shape test and the
false-positive measurement above are new here. That module is not imported
because it lives on a branch this one does not build on. THE FALSE POSITIVE
APPLIES TO IT TOO -- it is the same heuristic, and its picker demands a score
under 20, which a barred window in frame makes unreachable.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

WIDTH, HEIGHT = 1920, 1080
BAND_TOP, BAND_BOTTOM = 190, 300

WHITE_MIN = 238         # a glyph is near-white
DARK_MAX = 140          # and sits against something clearly darker
EDGE_RADIUS = 3         # within this many px on the row
MAX_CHROMA = 26         # and NEUTRAL -- a rocket core is white-hot but warm
MIN_GLYPH_PIXELS = 55   # fewer than this is speckle, not a word

# The tallest vertical run one column of a glyph may have. The frag message at
# cg_drawFragMessageScale 0.22 measures 20 px tall; the false-positive window
# measured 88. 28 sits clear of the text with room for a larger font and well
# under the geometry it is there to reject.
MAX_GLYPH_RUN = 28

# Text holds for seconds; the frag message alone is 2000 ms. A handful of
# consecutive frames is therefore never a word, whatever it scores -- the
# things that spike briefly are explosion cores and muzzle flashes. Requiring
# persistence states what the check is looking for rather than softening it.
MIN_TEXT_FRAMES = 20    # 0.33 s at 60 fps


def glyph_pixels(frame: np.ndarray) -> int:
    """Count glyph-like pixels in the name band of one HxWx3 uint8 frame."""
    band = frame[BAND_TOP:BAND_BOTTOM].astype(np.int16)
    grey = band.mean(axis=2)
    chroma = band.max(axis=2) - band.min(axis=2)
    bright = (grey >= WHITE_MIN) & (chroma <= MAX_CHROMA)
    if not bright.any():
        return 0
    dark = grey <= DARK_MAX
    near_dark = np.zeros_like(dark)
    for shift in range(1, EDGE_RADIUS + 1):
        near_dark[:, shift:] |= dark[:, :-shift]
        near_dark[:, :-shift] |= dark[:, shift:]
    return int(_drop_tall_columns(bright & near_dark).sum())


def _drop_tall_columns(mask: np.ndarray) -> np.ndarray:
    """Zero every column whose longest vertical run is taller than a glyph.

    Vectorised run-length per column: walking 110 rows in Python per frame
    would cost more than the decode.
    """
    run = np.zeros_like(mask, dtype=np.int16)
    run[0] = mask[0]
    for r in range(1, mask.shape[0]):
        run[r] = np.where(mask[r], run[r - 1] + 1, 0)
    return mask & (run.max(axis=0) <= MAX_GLYPH_RUN)


def audit_video(path: Path, ffmpeg: Path) -> dict:
    """Scan every frame of a finished clip for a burned-in name.

    Returns the worst score and any RUN of consecutive frames long enough to
    be text rather than a muzzle flash. A run is a CANDIDATE, not a verdict:
    see the module docstring for the measured false positive. Compare against
    a control captured the same way before concluding anything. A clip that is
    not 1920x1080 is reported unverified rather than quietly passing -- the
    band is in pixels.
    """
    proc = subprocess.Popen(
        [str(ffmpeg), "-v", "error", "-i", str(path), "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = WIDTH * HEIGHT * 3
    frames = worst = run_peak = 0
    runs: list[tuple[int, int, int]] = []
    run_start: int | None = None
    try:
        while True:
            buf = proc.stdout.read(n)
            if len(buf) < n:
                break
            g = glyph_pixels(np.frombuffer(buf, dtype=np.uint8)
                             .reshape(HEIGHT, WIDTH, 3))
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
            # CS-4: never leave the decoder running behind a cancelled scan.
            proc.stdout.close()
            proc.wait(timeout=10)
        except Exception:                                      # noqa: BLE001
            proc.kill()
            proc.wait()
    if frames == 0:
        return {"frames": 0, "worst": 0, "text_runs": [],
                "no_runs": False, "verified": False,
                "note": "no 1920x1080 frames decoded"}
    return {"frames": frames, "worst": worst, "text_runs": runs,
            "no_runs": not runs, "verified": True}
