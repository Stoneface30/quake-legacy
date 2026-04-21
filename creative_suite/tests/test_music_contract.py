"""creative_suite/tests/test_music_contract.py

Unit tests for the music full-length contract (Rules P1-R + P1-AA).
Tests validate_music_coverage() in isolation using monkeypatched durations
so that no real audio files or mutagen are required.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from creative_suite.engine.music_contract import validate_music_coverage


# ── helpers ──────────────────────────────────────────────────────────────────

def _fake_paths(*names: str) -> list[Path]:
    """Return dummy Path objects for named tracks."""
    return [Path(f"/fake/music/{n}") for n in names]


def _mock_duration_map(mapping: dict[str, float]):
    """Return a side_effect function that maps filename -> duration."""
    def _side_effect(path: Path):
        return mapping.get(path.name)
    return _side_effect


# ── tests ─────────────────────────────────────────────────────────────────────

def test_full_coverage_single_track() -> None:
    """One 300s track, body=200s → covered=True, needs_truncation=True."""
    files = _fake_paths("track01.mp3")
    with patch(
        "creative_suite.engine.music_contract.get_track_duration",
        side_effect=_mock_duration_map({"track01.mp3": 300.0}),
    ):
        result = validate_music_coverage(files, body_duration_s=200.0)

    assert result["covered"] is True
    assert result["needs_truncation"] is True
    assert result["coverage_gap_s"] == 0.0
    assert result["total_music_s"] == pytest.approx(300.0, abs=0.01)
    assert result["body_duration_s"] == 200.0
    assert result["full_length_pct"] == pytest.approx(150.0, abs=0.1)
    assert len(result["tracks"]) == 1
    assert result["warnings"] == []


def test_no_coverage_empty() -> None:
    """No tracks → covered=False, gap == body_duration."""
    result = validate_music_coverage([], body_duration_s=120.0)

    assert result["covered"] is False
    assert result["needs_truncation"] is False
    assert result["coverage_gap_s"] == pytest.approx(120.0, abs=0.01)
    assert result["total_music_s"] == pytest.approx(0.0, abs=0.01)
    assert result["full_length_pct"] == pytest.approx(0.0, abs=0.1)
    assert result["tracks"] == []
    assert result["warnings"] == []


def test_multi_track_coverage() -> None:
    """Two 100s tracks, body=180s → covered=True, total=200s, truncation=True."""
    files = _fake_paths("a.mp3", "b.mp3")
    with patch(
        "creative_suite.engine.music_contract.get_track_duration",
        side_effect=_mock_duration_map({"a.mp3": 100.0, "b.mp3": 100.0}),
    ):
        result = validate_music_coverage(files, body_duration_s=180.0)

    assert result["covered"] is True
    assert result["needs_truncation"] is True
    assert result["total_music_s"] == pytest.approx(200.0, abs=0.01)
    assert result["coverage_gap_s"] == 0.0
    assert len(result["tracks"]) == 2
    assert result["warnings"] == []


def test_short_gap() -> None:
    """One 90s track, body=100s → covered=False, gap=10s."""
    files = _fake_paths("short.mp3")
    with patch(
        "creative_suite.engine.music_contract.get_track_duration",
        side_effect=_mock_duration_map({"short.mp3": 90.0}),
    ):
        result = validate_music_coverage(files, body_duration_s=100.0)

    assert result["covered"] is False
    assert result["needs_truncation"] is False
    assert result["coverage_gap_s"] == pytest.approx(10.0, abs=0.01)
    assert result["total_music_s"] == pytest.approx(90.0, abs=0.01)


def test_full_length_pct_calculation() -> None:
    """Verify formula: 200s / 150s = 133.3%."""
    files = _fake_paths("long.mp3")
    with patch(
        "creative_suite.engine.music_contract.get_track_duration",
        side_effect=_mock_duration_map({"long.mp3": 200.0}),
    ):
        result = validate_music_coverage(files, body_duration_s=150.0)

    assert result["full_length_pct"] == pytest.approx(133.3, abs=0.1)
    assert result["covered"] is True


def test_unreadable_track_generates_warning() -> None:
    """A track whose duration is None produces a warning entry."""
    files = _fake_paths("broken.mp3")
    with patch(
        "creative_suite.engine.music_contract.get_track_duration",
        return_value=None,
    ):
        result = validate_music_coverage(files, body_duration_s=60.0)

    assert result["covered"] is False
    assert len(result["warnings"]) == 1
    assert "broken.mp3" in result["warnings"][0]


def test_tracks_starts_at_accumulates() -> None:
    """starts_at_s for each track reflects cumulative offset."""
    files = _fake_paths("t1.mp3", "t2.mp3", "t3.mp3")
    with patch(
        "creative_suite.engine.music_contract.get_track_duration",
        side_effect=_mock_duration_map(
            {"t1.mp3": 50.0, "t2.mp3": 60.0, "t3.mp3": 70.0}
        ),
    ):
        result = validate_music_coverage(files, body_duration_s=200.0)

    starts = [t["starts_at_s"] for t in result["tracks"]]
    assert starts[0] == pytest.approx(0.0, abs=0.01)
    assert starts[1] == pytest.approx(50.0, abs=0.01)
    assert starts[2] == pytest.approx(110.0, abs=0.01)


def test_exact_coverage_no_truncation() -> None:
    """Track duration exactly equals body duration → covered=True, no truncation."""
    files = _fake_paths("exact.mp3")
    with patch(
        "creative_suite.engine.music_contract.get_track_duration",
        side_effect=_mock_duration_map({"exact.mp3": 180.0}),
    ):
        result = validate_music_coverage(files, body_duration_s=180.0)

    assert result["covered"] is True
    assert result["needs_truncation"] is False
    assert result["coverage_gap_s"] == pytest.approx(0.0, abs=0.001)
