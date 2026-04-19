"""WAV → downsampled peak pairs for browser waveform rendering.

Returns `target` (min, max) tuples. Browser draws two polylines — one for
positive peaks, one for negative. ~6000 pairs is the sweet spot for a
1920-wide canvas (3px per pair).
"""
from __future__ import annotations

import array
import wave
from pathlib import Path


def compute_peaks(wav_path: Path, target: int = 6000) -> list[tuple[float, float]]:
    with wave.open(str(wav_path), "rb") as w:
        n_channels = w.getnchannels()
        sampwidth = w.getsampwidth()
        n_frames = w.getnframes()
        raw = w.readframes(n_frames)
    if sampwidth != 2:
        raise ValueError(f"Only 16-bit PCM supported; got {sampwidth * 8}-bit")
    samples = array.array("h")
    samples.frombytes(raw)
    if n_channels > 1:
        mono = array.array(
            "h",
            [
                sum(samples[i + c] for c in range(n_channels)) // n_channels
                for i in range(0, len(samples), n_channels)
            ],
        )
        samples = mono
    total = len(samples)
    if total == 0:
        return []
    bucket = max(1, total // target)
    peaks: list[tuple[float, float]] = []
    for i in range(0, total, bucket):
        chunk = samples[i : i + bucket]
        if not chunk:
            continue
        peaks.append((min(chunk) / 32768.0, max(chunk) / 32768.0))
        if len(peaks) >= target:
            break
    return peaks
