"""Rule P1-Z v2 + P1-DD real-audio event recognition gate.

Validates the template-matching recognizer against 5 real Wolfcam body-chunk
clips (committed fixtures at ``phase1/tests/fixtures/clip_audio/``).

History:
    v1 recognizer reported ~0 events on Part 4 (111/111 SKIP_ALIGN) because
    ``librosa.load`` could not decode the pipeline's .mp4 body chunks on
    Windows (soundfile rejected the container, audioread had no backend).
    v2.1 added an ffmpeg→s16le fallback in ``_load_audio_any``, CMVN-ish
    mean-subtraction on the mel-envelope, and a realistic 0.55 default
    threshold — demo-vs-clean-pak00 cross-correlation rarely clears 0.72.

This test is the regression gate: if either the decode path or the
normalization regresses, it trips here before it ships.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from phase1 import audio_onsets as ao

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "clip_audio"
EXPECTED_CLIPS = [
    "chunk_0005.wav",
    "chunk_0010.wav",
    "chunk_0020.wav",
    "chunk_0030.wav",
    "chunk_0050.wav",
]


def _have_fixtures() -> bool:
    return FIXTURES.exists() and all(
        (FIXTURES / name).exists() for name in EXPECTED_CLIPS
    )


pytestmark = pytest.mark.skipif(
    ao.librosa is None or not _have_fixtures(),
    reason="librosa missing or fixture WAVs not present",
)


@pytest.fixture(scope="module")
def clip_events() -> dict[str, List[ao.GameEvent]]:
    # Reset the process-wide cache so threshold/preproc tweaks take effect
    # even when pytest shares a worker with earlier tests.
    ao.SoundLibrary._instance = None  # type: ignore[reportPrivateUsage]
    out: dict[str, List[ao.GameEvent]] = {}
    for name in EXPECTED_CLIPS:
        path = FIXTURES / name
        out[name] = ao.recognize_game_events(path)
    return out


def test_every_clip_has_at_least_one_event(
    clip_events: dict[str, List[ao.GameEvent]],
) -> None:
    """Gate 1: every real clip must recognize at least one event at ≥ 0.40."""
    for name, events in clip_events.items():
        assert events, f"{name}: recognizer returned no events"
        top = events[0]
        assert top.confidence >= ao.DEFAULT_FALLBACK_CONF, (
            f"{name}: top event {top.event_type} conf={top.confidence:.3f} "
            f"below fallback threshold {ao.DEFAULT_FALLBACK_CONF}"
        )


def test_majority_clear_tight_threshold(
    clip_events: dict[str, List[ao.GameEvent]],
) -> None:
    """Gate 2: at least 3 of 5 clips must clear the new 0.55 tight threshold."""
    tight = sum(
        1 for events in clip_events.values()
        if events and events[0].confidence >= ao.DEFAULT_CONF_THRESHOLD
    )
    assert tight >= 3, (
        f"only {tight}/5 clips cleared conf ≥ {ao.DEFAULT_CONF_THRESHOLD}; "
        "recognizer is under-performing on real Wolfcam audio"
    )


def test_event_type_distribution_is_diverse(
    clip_events: dict[str, List[ao.GameEvent]],
) -> None:
    """Gate 3: top event_type must not collapse to a single label across all clips.

    The v1 bug produced player_death/gasp.wav as winner on 100% of clips —
    symptom of the missing CMVN + inflated cosine. A healthy recognizer sees
    at least 2 distinct top event_types across 5 random clips.
    """
    tops = {
        events[0].event_type for events in clip_events.values() if events
    }
    assert len(tops) >= 2, (
        f"all 5 clips collapsed to a single top event_type {tops} — "
        "the recognizer is not discriminating between templates"
    )


def test_mp4_chunks_decode_via_ffmpeg_fallback() -> None:
    """Gate 4: the actual pipeline path — recognize straight from .mp4 chunks.

    Regression guard for the v1 root cause (librosa fails on mp4, exception
    swallowed, 0 events). The ffmpeg fallback in ``_load_audio_any`` must
    make at least 3/5 mp4 chunks return non-empty event lists.
    """
    ao.SoundLibrary._instance = None  # type: ignore[reportPrivateUsage]
    mp4_dir = ROOT / "output" / "_part04_v6_body_chunks"
    if not mp4_dir.exists():
        pytest.skip("part 4 body chunks not available on this workstation")
    chunks = sorted(mp4_dir.glob("chunk_*.mp4"))[:5]
    if len(chunks) < 5:
        pytest.skip("fewer than 5 mp4 chunks available for regression gate")
    hits = 0
    for c in chunks:
        events = ao.recognize_game_events(c)
        if events and events[0].confidence >= ao.DEFAULT_FALLBACK_CONF:
            hits += 1
    assert hits >= 3, (
        f"only {hits}/5 .mp4 chunks produced recognized events — ffmpeg "
        "decode fallback is broken or not found on PATH"
    )
