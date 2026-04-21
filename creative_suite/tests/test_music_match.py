# creative_suite/tests/test_music_match.py
"""Unit tests for creative_suite.music_match.compute_match."""
from __future__ import annotations

import pytest

from creative_suite.music_match import compute_match


def test_perfect_match() -> None:
    """Equal durations → 100.0% match, no truncation."""
    result = compute_match(200.0, 200.0)
    assert result["match_pct"] == 100.0
    assert result["full_length_pct"] == 100.0
    assert result["needs_truncation"] is False


def test_short_track() -> None:
    """Track shorter than body → needs_truncation=True, full_length_pct < 100."""
    result = compute_match(120.0, 200.0)
    assert result["needs_truncation"] is True
    assert result["full_length_pct"] < 100.0
    # match_pct = min(120,200)/max(120,200)*100 = 120/200*100 = 60.0
    assert result["match_pct"] == pytest.approx(60.0, abs=0.1)


def test_long_track() -> None:
    """Track longer than body → needs_truncation=False, full_length_pct > 100."""
    result = compute_match(300.0, 200.0)
    assert result["needs_truncation"] is False
    assert result["full_length_pct"] > 100.0
    # match_pct = min(300,200)/max(300,200)*100 = 200/300*100 ≈ 66.7
    assert result["match_pct"] == pytest.approx(66.7, abs=0.1)


def test_zero_body() -> None:
    """body_duration=0 → all values are None."""
    result = compute_match(120.0, 0)
    assert result["match_pct"] is None
    assert result["full_length_pct"] is None
    assert result["needs_truncation"] is None


def test_match_pct_formula() -> None:
    """Verify formula: min(a, b) / max(a, b) * 100 rounded to 1 dp."""
    a, b = 150.0, 180.0
    expected = round(min(a, b) / max(a, b) * 100, 1)
    result = compute_match(a, b)
    assert result["match_pct"] == expected
