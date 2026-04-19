"""
Silence detection — Rule P1-V (Part 6 v8, 2026-04-18).

Uses ffmpeg's `silencedetect` filter to find clips whose internal audio is
mostly silent (e.g. pre-warmup lulls, arena countdowns with no gunfire).
Those clips get routed through the existing `speedup=True` path in
`phase1/normalize.py`, which applies 1.6× atempo + setpts for a "fast
forward the dead time" effect.

Usage:
    info = analyze_silence(clip_path, cfg)
    if info.silent_frac > 0.35:  # >35% silent → force fast-forward
        entry.speedup = True
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


_SILENCE_RE = re.compile(
    r"silence_(start|end): ([\d\.]+)"
    r"|silence_duration: ([\d\.]+)"
)


@dataclass
class SilenceReport:
    clip_path: Path
    duration_s: float
    silent_spans: List[Tuple[float, float]]   # (start, end) in seconds
    silent_seconds: float
    silent_frac: float                         # silent_seconds / duration_s
    longest_silence: float

    @property
    def should_speedup(self) -> bool:
        """Fast-forward if >35 % of the clip is silent OR any single silence
        stretch is >= 3.5 s."""
        return self.silent_frac >= 0.35 or self.longest_silence >= 3.5


def analyze_silence(
    clip_path: Path,
    ffmpeg_bin: Path,
    threshold_db: float = -35.0,
    min_silence_dur: float = 1.5,
) -> SilenceReport:
    """Run ffmpeg silencedetect on the clip, return a SilenceReport.

    Invariants: never raises on ffmpeg non-zero; silencedetect writes to
    stderr and exits 0 anyway. A corrupt clip is reported as no-silence.
    """
    cmd = [
        str(ffmpeg_bin), "-i", str(clip_path),
        "-af", f"silencedetect=noise={threshold_db}dB:d={min_silence_dur}",
        "-f", "null", "-",
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stderr = result.stderr or ""
    duration_s = _parse_duration(stderr)
    spans = _parse_silent_spans(stderr)
    silent_seconds = sum(e - s for s, e in spans)
    longest = max((e - s for s, e in spans), default=0.0)
    frac = silent_seconds / duration_s if duration_s > 0 else 0.0
    return SilenceReport(
        clip_path=clip_path,
        duration_s=duration_s,
        silent_spans=spans,
        silent_seconds=silent_seconds,
        silent_frac=frac,
        longest_silence=longest,
    )


def _parse_duration(stderr: str) -> float:
    m = re.search(r"Duration: (\d+):(\d+):([\d\.]+)", stderr)
    if not m:
        return 0.0
    h, mm, ss = m.groups()
    return int(h) * 3600 + int(mm) * 60 + float(ss)


def _parse_silent_spans(stderr: str) -> List[Tuple[float, float]]:
    """silencedetect emits pairs of lines:
        [silencedetect @ ...] silence_start: 12.345
        [silencedetect @ ...] silence_end: 15.678 | silence_duration: 3.333
    We walk them pairwise.
    """
    spans: List[Tuple[float, float]] = []
    cur_start: float | None = None
    for line in stderr.splitlines():
        m_start = re.search(r"silence_start:\s*([\d\.]+)", line)
        m_end = re.search(r"silence_end:\s*([\d\.]+)", line)
        if m_start:
            cur_start = float(m_start.group(1))
        elif m_end and cur_start is not None:
            spans.append((cur_start, float(m_end.group(1))))
            cur_start = None
    return spans


__all__ = ["SilenceReport", "analyze_silence"]
