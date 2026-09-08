"""Measure sync in the DELIVERED file, not in the recipe (directive D).

SceneRecipe mathematics proves what we INTENDED. The viewer experiences an
encoded, muxed, decoded mp4, and every stage between those two facts can
move a transient: AAC priming delay, container edit lists, the resampler,
the trim. A critical hit must not be moved silently by any of them, so the
delivered relationship is measured rather than assumed.

METHOD. Decode a window of the finished file around the intended moment and
find the actual transient, using onset strength on the mixed audio. Because
the mix contains music AND game audio, the music bed can itself produce
onsets, so the search is deliberately narrow: we are asking "did the thing
we placed here move?", not "what is the most interesting sound nearby".

Three deltas are reported and never collapsed into one:

    intended    what the recipe asked for
    rendered    where it sits in the master, before delivery encode
    post_encode where it sits in the file the viewer plays

The gap between rendered and post_encode is the encode's fault; the gap
between intended and rendered is ours.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
from typing import Any

import numpy as np

# TOOLS AND DATA BOTH LIVE WITH THE PROJECT, not with the code. The
# integration worktree resolved ffmpeg beside itself and every
# transient search died on WinError 2. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
FFMPEG = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"

ANALYSIS_SR = 22050
# How far either side of the intended moment to look. Wider than the tiers
# we care about (so a genuine miss is visible) but narrow enough that an
# unrelated musical onset is unlikely to be mistaken for the event.
DEFAULT_WINDOW_MS = 250.0
# Decode padding either side of the search window; must exceed the ~50 ms
# edge artifact by a comfortable margin.
PAD_MS = 300.0


@dataclass(frozen=True)
class DeliveredOnset:
    """A transient actually found in a decoded file."""
    found: bool
    onset_us: int | None
    strength: float
    window_us: tuple[int, int]
    reason: str = ""


def decode_window(path: Path | str, start_us: int, end_us: int,
                  sr: int = ANALYSIS_SR) -> np.ndarray:
    """Decode a mono float32 window from the delivered file."""
    start_s = max(0.0, start_us / 1e6)
    dur_s = max(0.0, (end_us - start_us) / 1e6)
    if dur_s <= 0:
        return np.zeros(0, dtype=np.float32)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "w.wav"
        proc = subprocess.run(
            [str(FFMPEG), "-v", "error", "-ss", f"{start_s:.6f}",
             "-t", f"{dur_s:.6f}", "-i", str(path), "-vn",
             "-ac", "1", "-ar", str(sr), "-c:a", "pcm_f32le", str(wav)],
            capture_output=True, text=True)
        if proc.returncode != 0 or not wav.exists():
            return np.zeros(0, dtype=np.float32)
        import soundfile as sf
        data, _ = sf.read(str(wav), dtype="float32", always_2d=False)
    return np.asarray(data, dtype=np.float32)


def find_transient(path: Path | str, expected_us: int, *,
                   window_ms: float = DEFAULT_WINDOW_MS,
                   sr: int = ANALYSIS_SR) -> DeliveredOnset:
    """The strongest onset near ``expected_us`` in the delivered audio.

    Returns ``found=False`` rather than a guess when the window decodes
    empty or flat -- an invented onset would silently become a measured
    delta of zero, which is the worst possible failure for this module.
    """
    half = int(window_ms * 1000)
    lo, hi = max(0, expected_us - half), expected_us + half
    # Decode WIDER than the window and search only the interior. Spectral
    # flux on a hard-cut window produces a spurious rise ~50 ms after the
    # cut (the flux compares the first frames against nothing), and that
    # artifact reported itself as a real onset at a constant offset from
    # the window start -- observed as -67.8 ms at arbitrary times on both
    # mp3 and mp4, and as -7.8 ms with a 60 ms window. The padding keeps
    # the cut well outside the region that is allowed to win.
    pad = int(PAD_MS * 1000)
    dlo = max(0, lo - pad)
    y = decode_window(path, dlo, hi + pad, sr)
    if y.size < sr // 100:
        return DeliveredOnset(False, None, 0.0, (lo, hi), "window decoded empty")
    import librosa
    hop = 128                                   # ~5.8 ms at 22050 Hz
    env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    if env.size == 0 or float(np.max(env)) <= 0.0:
        return DeliveredOnset(False, None, 0.0, (lo, hi), "no onset energy")
    times_us = dlo + (librosa.frames_to_time(np.arange(env.size), sr=sr,
                                             hop_length=hop) * 1e6)
    inside = (times_us >= lo) & (times_us <= hi)
    if not np.any(inside):
        return DeliveredOnset(False, None, 0.0, (lo, hi), "window too narrow")
    interior = np.where(inside, env, -np.inf)
    peak = int(np.argmax(interior))
    strength = float(env[peak])
    median = float(np.median(env[inside]))
    if strength < median * 2.0:
        return DeliveredOnset(False, None, strength, (lo, hi),
                              "no transient stands out from the bed")
    return DeliveredOnset(True, int(times_us[peak]), strength, (lo, hi))


@dataclass(frozen=True)
class DeliveredComparison:
    """intended vs rendered vs post-encode, never collapsed."""
    label: str
    intended_us: int
    rendered_us: int | None
    post_encode_us: int | None
    rendered_reason: str = ""
    post_encode_reason: str = ""

    def _ms(self, value: int | None) -> float | None:
        return None if value is None else round(
            (value - self.intended_us) / 1000.0, 2)

    @property
    def rendered_delta_ms(self) -> float | None:
        return self._ms(self.rendered_us)

    @property
    def post_encode_delta_ms(self) -> float | None:
        return self._ms(self.post_encode_us)

    @property
    def encode_shift_ms(self) -> float | None:
        """How much the DELIVERY ENCODE alone moved the transient."""
        if self.rendered_us is None or self.post_encode_us is None:
            return None
        return round((self.post_encode_us - self.rendered_us) / 1000.0, 2)

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "intended_us": self.intended_us,
                "rendered_us": self.rendered_us,
                "post_encode_us": self.post_encode_us,
                "rendered_delta_ms": self.rendered_delta_ms,
                "post_encode_delta_ms": self.post_encode_delta_ms,
                "encode_shift_ms": self.encode_shift_ms,
                "rendered_reason": self.rendered_reason,
                "post_encode_reason": self.post_encode_reason}


def compare(label: str, intended_us: int, master: Path | str,
            delivered: Path | str, *,
            window_ms: float = DEFAULT_WINDOW_MS) -> DeliveredComparison:
    """Measure one intended moment in both the master and the delivered file."""
    r = find_transient(master, intended_us, window_ms=window_ms)
    p = find_transient(delivered, intended_us, window_ms=window_ms)
    return DeliveredComparison(
        label=label, intended_us=int(intended_us),
        rendered_us=r.onset_us, post_encode_us=p.onset_us,
        rendered_reason=r.reason, post_encode_reason=p.reason)


def audio_start_offset_us(path: Path | str) -> int:
    """Container start_time for the audio stream, in microseconds.

    A non-zero value is exactly the kind of silent shift this module
    exists to catch: it moves every sample without touching a single
    timestamp in the recipe.
    """
    proc = subprocess.run(
        [str(FFMPEG).replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error",
         "-select_streams", "a:0", "-show_entries", "stream=start_time",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return int(round(float(proc.stdout.strip()) * 1e6))
    except (TypeError, ValueError):
        return 0
