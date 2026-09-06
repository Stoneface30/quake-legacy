"""Technical + semantic QA for generated capture AVIs (§16-§17).

Technical: ffprobe stream inventory, full decode-to-null with -xerror,
duration tolerance, resolution/fps expectations.
Semantic: every expected frag offset must land inside the captured duration
with a safety margin; clutch windows must contain the full clutch interval.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

# ffprobe lives with the project, not with the checkout. See
# engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
FFMPEG = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
FFPROBE = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffprobe.exe"

EDGE_MARGIN_MS = 700        # frag closer than this to an edge is suspicious
DURATION_TOL_S = 2.0

FLAG_START = "FRAG_TOO_CLOSE_TO_START"
FLAG_END = "FRAG_TOO_CLOSE_TO_END"
FLAG_OUTSIDE = "EXPECTED_FRAG_OUTSIDE_CAPTURE"
FLAG_CLUTCH = "CLUTCH_TRUNCATED"


def probe(avi: Path) -> dict:
    out = subprocess.run(
        [str(FFPROBE), "-v", "error", "-print_format", "json",
         "-show_streams", "-show_format", str(avi)],
        capture_output=True, text=True, timeout=120,
        creationflags=subprocess.CREATE_NO_WINDOW)
    if out.returncode != 0:
        return {"error": out.stderr.strip()[:400]}
    return json.loads(out.stdout)


def technical_qa(avi: Path, expected_duration_s: float,
                 expect_resolution: tuple[int, int] | None = None,
                 expect_fps: int | None = None) -> dict:
    """Returns {pass, reasons[], duration_s, width, height, fps}."""
    reasons: list[str] = []
    info = probe(avi)
    if "error" in info:
        return {"pass": False, "reasons": [f"ffprobe: {info['error']}"],
                "duration_s": 0.0}
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if v is None:
        reasons.append("no video stream")
    if a is None:
        reasons.append("no audio stream")
    duration = float(info.get("format", {}).get("duration") or 0.0)
    if abs(duration - expected_duration_s) > DURATION_TOL_S:
        reasons.append(f"duration {duration:.2f}s vs expected "
                       f"{expected_duration_s:.2f}s (tol {DURATION_TOL_S}s)")
    width = height = fps = None
    if v is not None:
        width, height = v.get("width"), v.get("height")
        num, _, den = (v.get("avg_frame_rate") or "0/1").partition("/")
        try:
            fps = round(float(num) / float(den or 1))
        except (ValueError, ZeroDivisionError):
            fps = None
        if expect_resolution and (width, height) != expect_resolution:
            reasons.append(f"resolution {width}x{height} != "
                           f"{expect_resolution[0]}x{expect_resolution[1]}")
        if expect_fps and fps != expect_fps:
            reasons.append(f"fps {fps} != {expect_fps}")

    if not reasons:  # only pay for full decode when the cheap checks pass
        dec = subprocess.run(
            [str(FFMPEG), "-v", "error", "-xerror", "-i", str(avi),
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=600,
            creationflags=subprocess.CREATE_NO_WINDOW)
        if dec.returncode != 0:
            reasons.append(f"decode: {dec.stderr.strip()[:400]}")

    return {"pass": not reasons, "reasons": reasons, "duration_s": duration,
            "width": width, "height": height, "fps": fps}


def semantic_qa(duration_s: float, frag_offsets_ms: list[int],
                clutch_span_ms: tuple[int, int] | None = None) -> list[str]:
    """Flags per §17. Empty list = clean.

    frag_offsets_ms are relative to capture start; clutch_span_ms is the
    (start, end) of the clutch relative to capture start when applicable.
    """
    flags: list[str] = []
    dur_ms = duration_s * 1000.0
    for off in frag_offsets_ms:
        if off < 0 or off > dur_ms:
            flags.append(FLAG_OUTSIDE)
        elif off < EDGE_MARGIN_MS:
            flags.append(FLAG_START)
        elif dur_ms - off < EDGE_MARGIN_MS:
            flags.append(FLAG_END)
    if clutch_span_ms is not None:
        cs, ce = clutch_span_ms
        if cs < 0 or ce > dur_ms:
            flags.append(FLAG_CLUTCH)
    return sorted(set(flags))
