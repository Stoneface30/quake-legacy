"""Where an editorial boundary may sit instead, and where it may not."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import score_timeline as st


# ── boundary flexibility ────────────────────────────────────────────────────

def _gridded(duration_us=120_000_000, bpm=120.0):
    """A track with a real grid: 0.5 s beats, 2 s bars, 8 s phrases."""
    beats = tuple(range(0, duration_us, 500_000))
    bars = tuple(range(0, duration_us, 2_000_000))
    phrases = tuple(range(0, duration_us, 8_000_000))
    return st.ScoreTimelineV1(
        track_hash="h", track_path="t.mp3", duration_us=duration_us, bpm=bpm,
        beats_us=beats, bars_us=bars, phrases_us=phrases,
        sections_us=(0, 24_000_000, 56_000_000, 88_000_000),
        energy_curve=tuple((t, 0.5) for t in range(0, duration_us, 1_000_000)))


def test_a_boundary_on_a_phrase_edge_may_only_take_another_phrase_edge():
    t = _gridded()
    f = st.boundary_flex(t, 24_000_000)
    assert f.rigidity == st.PHRASE_LOCKED and f.on_phrase
    assert f.candidates_us == (16_000_000, 24_000_000, 32_000_000)
    assert f.may_move_to(32_000_000) and not f.may_move_to(26_000_000)


def test_a_boundary_inside_a_phrase_slides_across_that_phrase_only():
    t = _gridded()
    f = st.boundary_flex(t, 26_000_000)
    assert f.rigidity == st.BAR_FLEXIBLE
    assert f.earliest_us >= 24_000_000 and f.latest_us <= 32_000_000, (
        "it must not escape into the neighbouring phrase")
    assert all(c in t.bars_us or c == 26_000_000 for c in f.candidates_us)


def test_the_track_ends_where_it_ends():
    t = _gridded()
    for at in (0, t.duration_us):
        f = st.boundary_flex(t, at)
        assert f.rigidity == st.RIGID and not f.movable and f.slack_us == 0


def test_a_track_with_no_grid_cannot_pretend_to_be_flexible():
    t = st.ScoreTimelineV1(
        track_hash="h", track_path="t.mp3", duration_us=120_000_000, bpm=None,
        beats_us=(), bars_us=(), phrases_us=(), sections_us=(0, 60_000_000),
        energy_curve=((0, 0.5), (60_000_000, 0.5)))
    f = st.boundary_flex(t, 60_000_000)
    assert f.rigidity == st.RIGID and not f.movable
    assert "no usable grid" in f.reason


def test_a_boundary_stays_one_of_its_own_candidates():
    """Otherwise the metadata is calling the current cut invalid."""
    with pytest.raises(ValueError, match="its own candidates"):
        st.BoundaryFlex(5, st.BAR_FLEXIBLE, 0, 10, (0, 10), False, False, "x")


def test_the_nearest_valid_position_is_never_an_invented_one():
    t = _gridded()
    f = st.boundary_flex(t, 26_000_000)
    got = f.nearest_to(27_400_000)
    assert got in f.candidates_us
    assert got in t.bars_us


def test_derived_slots_carry_where_their_edges_could_move():
    t = _gridded()
    slots = st.derive_slots(t)
    assert slots
    for s_ in slots:
        assert s_.start_flex is not None and s_.end_flex is not None
        assert s_.start_flex.at_us == s_.start_us
        assert s_.end_flex.at_us == s_.end_us
    assert any(s_.boundaries_movable for s_ in slots)
    d = slots[0].to_dict()
    assert d["start_flex"]["candidates_us"] and "boundaries_movable" in d


def test_flexibility_is_metadata_and_changes_no_cut():
    """The boundaries recorded are still exactly the boundaries derived."""
    t = _gridded()
    slots = st.derive_slots(t)
    edges = [(s_.start_us, s_.end_us) for s_ in slots]
    again = [(s_.start_flex.at_us, s_.end_flex.at_us) for s_ in slots]
    assert edges == again
