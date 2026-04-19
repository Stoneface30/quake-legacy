from __future__ import annotations

import struct
import wave
from pathlib import Path

from creative_suite.api._waveform import compute_peaks


def _write_test_wav(path: Path, seconds: float = 2.0, sr: int = 48000) -> None:
    n = int(seconds * sr)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        for i in range(n):
            v = int(32767 * (0.5 if i % 2 == 0 else -0.5))
            w.writeframes(struct.pack("<h", v))


def test_compute_peaks_returns_target_count(tmp_path: Path) -> None:
    wav = tmp_path / "test.wav"
    _write_test_wav(wav, seconds=2.0)
    peaks = compute_peaks(wav, target=600)
    assert len(peaks) == 600
    for mn, mx in peaks:
        assert -1.0 <= mn <= mx <= 1.0


def test_compute_peaks_handles_short_files(tmp_path: Path) -> None:
    wav = tmp_path / "tiny.wav"
    _write_test_wav(wav, seconds=0.05)
    peaks = compute_peaks(wav, target=600)
    assert len(peaks) <= 600
