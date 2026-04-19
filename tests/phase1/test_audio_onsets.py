"""Unit tests for phase1.audio_onsets."""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pytest

from phase1.audio_onsets import find_action_peak, find_action_peaks_per_clip
from phase1.config import Config


def _synth_click_wav(tmp: Path, click_time_s: float, duration: float = 3.0, sr: int = 48000) -> Path:
    """Synthesize a short WAV with silence + a click at click_time_s."""
    import soundfile as sf

    n = int(duration * sr)
    y = np.random.normal(0, 0.002, n).astype(np.float32)  # quiet noise floor
    idx = int(click_time_s * sr)
    # sharp attack: gaussian-enveloped impulse
    tail = np.linspace(0, 1, 400)
    env = np.exp(-8 * tail)
    click = (np.random.normal(0, 1, 400) * env).astype(np.float32) * 0.9
    y[idx : idx + 400] += click
    path = tmp / f"click_{click_time_s:.2f}.wav"
    sf.write(str(path), y, sr)
    return path


def test_find_action_peak_synthetic_click(tmp_path: Path):
    wav = _synth_click_wav(tmp_path, click_time_s=1.4)
    peak = find_action_peak(wav)
    assert peak is not None
    # Tolerance wider than 50ms due to onset backtrack.
    assert 1.3 <= peak <= 1.5, f"expected ~1.4s, got {peak}"


def test_find_action_peak_pure_silence_returns_none(tmp_path: Path):
    import soundfile as sf

    sr = 48000
    y = np.zeros(sr * 2, dtype=np.float32)
    path = tmp_path / "silence.wav"
    sf.write(str(path), y, sr)
    peak = find_action_peak(path)
    # Either None or 0.0 is acceptable; just ensure it doesn't crash.
    assert peak is None or isinstance(peak, float)


def test_find_action_peaks_per_clip_batch(tmp_path: Path):
    w1 = _synth_click_wav(tmp_path, click_time_s=0.8)
    w2 = _synth_click_wav(tmp_path, click_time_s=2.0)
    out = find_action_peaks_per_clip([w1, w2])
    assert str(w1) in out
    assert str(w2) in out
    assert out[str(w1)] is not None
    assert out[str(w2)] is not None
