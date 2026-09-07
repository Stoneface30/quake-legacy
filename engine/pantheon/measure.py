"""Measure what a filmed variant actually put on screen.

WHY A DIFF MASK AND NOT A HAND-DRAWN BOX. The rail is a thin bright line whose
screen position depends on the camera; a fixed rectangle would be a guess, and
a guess that clipped the beam would bias the mean toward the wall behind it.
Diffing the rail frame against a frame from the SAME capture a moment earlier
isolates exactly the pixels the rail added, and nothing else in the shot moves
that hard.

A raw pixel diff between two CAPTURES is noise -- wolfcam is not frame
deterministic across launches, and a previous attempt measured 72k differing
pixels from playback jitter alone. So every diff here is WITHIN one capture,
and the comparison BETWEEN variants is of the measured statistics, never of
the images.
"""
from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path

FFMPEG = Path("G:/QUAKE_LEGACY/creative_suite/tools/ffmpeg/ffmpeg.exe")
W, H = 1920, 1080


def frame_rgb(avi: Path, t: float, size: tuple[int, int] = (W, H), *,
              resample: bool = False) -> bytes:
    """One frame as raw RGB24, straight from the AVI -- no lossy round trip.

    `resample` asks ffmpeg to area-average the frame down to `size` instead of
    demanding the frame already be that shape. A downscaled reading answers a
    different question from a full-resolution one: fine per-pixel jitter
    averages away, so what survives is a difference a viewer would name --
    a different model, a different colour, a missing effect, a gamma shift.
    """
    scale = ["-vf", f"scale={size[0]}:{size[1]}:flags=area"] if resample else []
    out = subprocess.run(
        [str(FFMPEG), "-v", "error", "-ss", f"{t:.3f}", "-i", str(avi),
         "-frames:v", "1", *scale, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, timeout=180)
    if len(out.stdout) != size[0] * size[1] * 3:
        raise RuntimeError(f"{avi.name}: expected {size} frame, got "
                           f"{len(out.stdout)} bytes")
    return out.stdout


def save_still(avi: Path, t: float, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(FFMPEG), "-v", "error", "-y", "-ss", f"{t:.3f}",
                    "-i", str(avi), "-frames:v", "1", str(dest)],
                   check=True, timeout=180)
    return dest


def added_pixels(base: bytes, lit: bytes, *, threshold: int = 60,
                 exclude: tuple[int, int, int, int] | None = None
                 ) -> list[tuple[int, tuple[int, int, int]]]:
    """Pixels `lit` has that `base` does not, as (index, rgb).

    `exclude` is an (x0, y0, x1, y1) box in pixels -- used to drop the shooter,
    whose firing animation also changes between the two frames and is not what
    is being measured.
    """
    out = []
    for i in range(0, len(base), 3):
        d = (abs(lit[i] - base[i]) + abs(lit[i + 1] - base[i + 1])
             + abs(lit[i + 2] - base[i + 2]))
        if d <= threshold:
            continue
        if exclude:
            p = i // 3
            x, y = p % W, p // W
            if exclude[0] <= x <= exclude[2] and exclude[1] <= y <= exclude[3]:
                continue
        out.append((i // 3, (lit[i], lit[i + 1], lit[i + 2])))
    return out


def summarise(pixels, *, top_fraction: float = 0.25) -> dict:
    """Mean / median / count / dominant colours of a measured region.

    The BRIGHTEST quarter is reported separately because a rail trail has a
    hot core and a dim halo that blends with whatever is behind it; the core is
    the colour the cvar set, the halo is the core mixed with the wall.
    """
    if not pixels:
        return {"count": 0}
    rgbs = [p[1] for p in pixels]
    n = len(rgbs)
    core = sorted(rgbs, key=sum, reverse=True)[:max(1, int(n * top_fraction))]

    def stats(rows):
        cols = list(zip(*rows))
        mean = tuple(round(sum(c) / len(c), 1) for c in cols)
        med = tuple(sorted(c)[len(c) // 2] for c in cols)
        return mean, med

    mean, med = stats(rgbs)
    cmean, cmed = stats(core)
    dom = Counter((r // 16 * 16, g // 16 * 16, b // 16 * 16)
                  for r, g, b in core).most_common(4)
    return {"count": n, "mean_rgb": mean, "median_rgb": med,
            "core_count": len(core), "core_mean_rgb": cmean,
            "core_median_rgb": cmed,
            "dominant_core_bins": [{"rgb16": list(k), "n": v} for k, v in dom]}


def hue_family(rgb) -> str:
    """A coarse, honest name for a measured colour."""
    r, g, b = rgb
    if max(rgb) < 40:
        return "near-black"
    if max(rgb) - min(rgb) < 30:
        return "grey/white"
    if r >= g and r >= b:
        return "red/orange" if g >= b else "red/magenta"
    if g >= r and g >= b:
        return "green/yellow" if r >= b else "green/cyan"
    return "blue/cyan" if g >= r else "blue/magenta"
