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
    # With no grid at all the confidence gate refuses first, which is the
    # same answer arrived at earlier.
    assert f.confidence == 0.0
    assert "not trustworthy enough" in f.reason or "no usable grid" in f.reason


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


# ── a boundary must earn its flexibility ────────────────────────────────────

def _sparse(bars=(0, 2_000_000, 41_000_000)):
    return st.ScoreTimelineV1(
        track_hash="h", track_path="t.mp3", duration_us=120_000_000, bpm=None,
        beats_us=tuple(range(0, 120_000_000, 500_000)), bars_us=bars,
        phrases_us=(), sections_us=(0, 40_000_000),
        energy_curve=((0, 0.5), (40_000_000, 0.5)))


def test_a_grid_we_cannot_vouch_for_proposes_nothing():
    """Cached grids have been truncated before. A thin local grid must not
    become a reason to move a good scene."""
    f = st.boundary_flex(_sparse(), 40_000_000)
    assert f.confidence < st.MIN_GRID_CONFIDENCE
    assert not f.movable and f.candidates_us == (40_000_000,)
    assert f.kind == st.STRUCTURAL_BOUNDARY_ESTIMATE
    assert "not trustworthy enough" in f.reason


def test_confidence_is_read_off_the_grid_not_asserted():
    good = _gridded()
    conf, basis = st.grid_confidence(good, 26_000_000)
    assert conf >= st.MIN_GRID_CONFIDENCE
    assert "bar lines either side" in basis and "spacing" in basis
    thin, why = st.grid_confidence(_sparse(), 40_000_000)
    assert thin < st.MIN_GRID_CONFIDENCE and "bar lines within" in why


def test_a_one_sided_grid_is_not_enough():
    t = _sparse(bars=tuple(range(0, 30_000_000, 2_000_000)))
    conf, why = st.grid_confidence(t, 39_000_000)
    assert conf < st.MIN_GRID_CONFIDENCE
    assert "one side" in why or "within" in why


def test_an_anchor_is_evidence_and_does_not_move():
    class _A:
        def __init__(self, us): self.t_us = us
    t = _gridded()
    t = st.ScoreTimelineV1(
        track_hash=t.track_hash, track_path=t.track_path,
        duration_us=t.duration_us, bpm=t.bpm, beats_us=t.beats_us,
        bars_us=t.bars_us, phrases_us=t.phrases_us, sections_us=t.sections_us,
        energy_curve=t.energy_curve, anchors=(_A(26_000_000),))
    f = st.boundary_flex(t, 26_000_000)
    assert f.kind == st.MUSICAL_HARD_ANCHOR
    assert not f.movable and f.candidates_us == (26_000_000,)
    assert "evidence about the song" in f.reason


def test_an_anchor_cannot_be_given_alternatives():
    with pytest.raises(ValueError, match="does not get"):
        st.BoundaryFlex(5, st.BAR_FLEXIBLE, 0, 10, (0, 5, 10), False, False,
                        "x", st.MUSICAL_HARD_ANCHOR, 1.0, "y")


def test_alternatives_alone_are_not_permission_to_move():
    """A structural estimate over a weak grid has candidates and still may
    not use them."""
    f = st.BoundaryFlex(5, st.BAR_FLEXIBLE, 0, 10, (0, 5, 10), False, False,
                        "x", st.STRUCTURAL_BOUNDARY_ESTIMATE, 0.4, "thin")
    assert len(f.candidates_us) > 1 and not f.movable


def test_only_an_editorial_boundary_is_freely_movable():
    t = _gridded()
    mid = st.boundary_flex(t, 26_000_000)
    assert mid.kind == st.EDITORIAL_BOUNDARY and mid.movable
    edge = st.boundary_flex(t, 0)
    assert edge.kind == st.MUSICAL_HARD_ANCHOR and not edge.movable
