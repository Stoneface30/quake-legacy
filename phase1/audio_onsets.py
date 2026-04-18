"""
Game-audio onset detection per Rule P1-Z.

Given a Phase-1 AVI/MP4 clip, extract the time (seconds, clip-relative) of the
loudest transient attack — typically the rocket impact, rail crack, or grenade
detonation that defines the frag moment. Downstream beat-sync will try to land
this peak on a music downbeat.

Recipe: docs/research/audio-montage-2026-04-18.md §B.
Dependency: librosa (already installed), numpy.

Public API:
    find_action_peak(clip_path, sr=48000) -> float | None
    find_action_peaks_per_clip(clip_paths) -> dict[str, float | None]

A __main__ smoke block prints the peak for a single file.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np

try:  # librosa is optional at import time for type-check environments
    import librosa
except Exception:  # pragma: no cover
    librosa = None  # type: ignore[assignment]


def find_action_peak(clip_path: Path | str, sr: int = 48000) -> float | None:
    """Return the time (seconds, clip-relative) of the loudest transient.

    Returns None if no onset crosses the detection threshold (e.g. pure-silence
    clip or analysis failure).
    """
    if librosa is None:
        raise RuntimeError("librosa is required for find_action_peak")
    path = str(clip_path)
    try:
        y, sr_out = librosa.load(path, sr=sr, mono=True)
    except Exception:
        return None
    if y.size == 0:
        return None

    # Pre-emphasis to kill LG hum and rocket rumble (keeps the attack click).
    y = librosa.effects.preemphasis(y, coef=0.97)

    oenv = librosa.onset.onset_strength(
        y=y,
        sr=sr_out,
        hop_length=256,
        aggregate=np.median,
        fmax=8000,
        n_mels=128,
    )
    onsets = librosa.onset.onset_detect(
        onset_envelope=oenv,
        sr=sr_out,
        hop_length=256,
        backtrack=True,
        pre_max=20,
        post_max=20,
        pre_avg=50,
        post_avg=50,
        delta=0.3,
        wait=30,
        units="time",
    )
    if len(onsets) == 0:
        return None
    frames = librosa.time_to_frames(onsets, sr=sr_out, hop_length=256)
    # Guard: clamp frames to oenv range (librosa rounds up at the tail).
    frames = np.clip(frames, 0, len(oenv) - 1)
    peak_idx = int(np.argmax(oenv[frames]))
    return float(onsets[peak_idx])


def find_action_peaks_per_clip(
    clip_paths: Iterable[Path | str],
    sr: int = 48000,
) -> dict[str, float | None]:
    """Batch wrapper — returns {str(path): peak_time_or_None}."""
    return {str(p): find_action_peak(p, sr=sr) for p in clip_paths}


if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) < 2:
        print("usage: python -m phase1.audio_onsets <clip_path>", file=sys.stderr)
        sys.exit(2)
    peak = find_action_peak(sys.argv[1])
    print(f"peak={peak}")
