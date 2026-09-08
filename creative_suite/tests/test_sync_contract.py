"""Millisecond sync: tiers, signed deltas, and what may not move.

The properties that matter: a delta is always signed and always tiered by
CLASS, gameplay can never be moved to manufacture a match, fine alignment
actually lands the event (a sign error here reports a plausible REVIEW and
hides), and a "payoff" cannot be a score.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import sync_contract as sc
from creative_suite.engine.scene_recipe import MusicPlacement


def _place(source_start_us=20_000_000, program_edit_start_us=0):
    return MusicPlacement(track_id="a" * 64, source_start_us=source_start_us,
                          program_edit_start_us=program_edit_start_us,
                          source_end_us=source_start_us + 30_000_000)


# ── tiers are per class ─────────────────────────────────────────────────────

@pytest.mark.parametrize("ms,tier", [
    (0.0, sc.TIER_TARGET), (15.0, sc.TIER_TARGET), (-15.0, sc.TIER_TARGET),
    (15.1, sc.TIER_GOOD), (25.0, sc.TIER_GOOD),
    (25.1, sc.TIER_REVIEW), (40.0, sc.TIER_REVIEW),
    (40.1, sc.TIER_BAD), (-49.0, sc.TIER_BAD), (2048.0, sc.TIER_BAD),
])
def test_hard_sync_tiers(ms, tier):
    assert sc.classify_delta(ms, sc.CLASS_HARD) == tier


def test_a_49ms_miss_is_never_target_for_a_hard_sync():
    """The specific framing the directive rules out: 49 ms described as
    essentially placed, when a visual is meant to hit that exact event."""
    assert sc.classify_delta(49.0, sc.CLASS_HARD) == sc.TIER_BAD


def test_phrase_placement_tolerates_more_than_a_hard_hit():
    assert sc.classify_delta(100.0, sc.CLASS_PHRASE) == sc.TIER_TARGET
    assert sc.classify_delta(100.0, sc.CLASS_HARD) == sc.TIER_BAD


def test_unknown_class_rejected():
    with pytest.raises(ValueError):
        sc.classify_delta(1.0, "VIBES")


def test_search_tolerance_is_not_an_edit_tolerance():
    """750 ms is a discovery budget; it must never be mistaken for a tier."""
    assert sc.SEARCH_TOLERANCE_MS == 750.0
    assert sc.classify_delta(sc.SEARCH_TOLERANCE_MS,
                             sc.CLASS_HARD) == sc.TIER_BAD


# ── event priority ──────────────────────────────────────────────────────────

def test_impacts_and_frags_are_primary():
    for e in ("FRAG", "ROCKET_IMPACT", "RAIL_HIT", "COUNTERFRAG"):
        assert sc.is_primary(e)


def test_weapon_fire_is_not_the_event_that_gets_the_punch():
    assert not sc.is_primary("WEAPON_FIRE")
    assert not sc.is_primary("PROJECTILE_LAUNCH")


# ── measurement ─────────────────────────────────────────────────────────────

def test_delta_is_signed_and_says_which_way():
    place = _place()
    late = sc.measure_against_placement(
        game_event="ROCKET_IMPACT", game_edit_us=1_000_000,
        music_event="BEAT", music_us=place.edit_to_music(1_000_000) + 20_000,
        placement=place)
    assert late.signed_delta_ms == 20.0      # music AFTER the game event
    early = sc.measure_against_placement(
        game_event="ROCKET_IMPACT", game_edit_us=1_000_000,
        music_event="BEAT", music_us=place.edit_to_music(1_000_000) - 20_000,
        placement=place)
    assert early.signed_delta_ms == -20.0


def test_describe_never_says_matched():
    place = _place()
    m = sc.measure_against_placement(
        game_event="ROCKET_IMPACT", game_edit_us=1_000_000,
        music_event="ACCENT", music_us=place.edit_to_music(1_000_000) + 11_000,
        placement=place)
    line = m.describe()
    assert "+11.0 ms" in line and "[TARGET]" in line
    assert "MATCHED" not in line.upper()


def test_measurement_rejects_float_microseconds():
    with pytest.raises(ValueError):
        sc.SyncMeasurement(game_event="FRAG", music_event="BEAT",
                           game_edit_us=1.5, music_us=1, resolved_edit_us=1)


def test_measure_inverts_the_placement_mapping_exactly():
    """If this ever disagrees with edit_to_music, every delta is fiction."""
    place = _place(source_start_us=7_777_777, program_edit_start_us=250_000)
    for edit_us in (250_000, 1_000_000, 9_999_999):
        music_us = place.edit_to_music(edit_us)
        m = sc.measure_against_placement(
            game_event="FRAG", game_edit_us=edit_us, music_event="BEAT",
            music_us=music_us, placement=place)
        assert m.signed_delta_us == 0


# ── only music may move (directive E) ───────────────────────────────────────

def test_nudge_moves_music_and_leaves_the_programme_clock_alone():
    place = _place()
    moved = sc.nudge_placement(place, -10)
    # -10 means "arrive 10 ms earlier", which moves the SOURCE window later
    assert moved.source_start_us == place.source_start_us + 10_000
    assert sc.measure_against_placement(
        game_event="FRAG", game_edit_us=1_000_000, music_event="BEAT",
        music_us=place.edit_to_music(1_000_000), placement=moved
    ).signed_delta_ms == -10.0
    assert moved.program_edit_start_us == place.program_edit_start_us


def test_nudge_requires_whole_milliseconds():
    with pytest.raises(ValueError):
        sc.nudge_placement(_place(), 0.5)


def test_no_api_exists_to_move_a_game_event():
    """Gameplay is authoritative. If a helper ever appears that shifts a
    game event to fix music, this is the test that should fail."""
    exported = {n for n in dir(sc) if not n.startswith("_")}
    for forbidden in ("nudge_game_event", "shift_game_event",
                      "move_gameplay", "retime_event"):
        assert forbidden not in exported


def test_best_nudge_only_suggests_offered_steps():
    place = _place()
    m = sc.measure_against_placement(
        game_event="ROCKET_IMPACT", game_edit_us=1_000_000,
        music_event="BEAT", music_us=place.edit_to_music(1_000_000) + 9_000,
        placement=place)
    step = sc.best_nudge(m, place)
    assert step in sc.NUDGE_STEPS_MS
    assert step == -10 or step == -5


def test_best_nudge_returns_zero_when_nothing_helps():
    place = _place()
    m = sc.measure_against_placement(
        game_event="ROCKET_IMPACT", game_edit_us=1_000_000,
        music_event="BEAT", music_us=place.edit_to_music(1_000_000),
        placement=place)
    assert sc.best_nudge(m, place) == 0


# ── fine alignment actually lands (the sign bug) ────────────────────────────

def test_fine_align_puts_the_event_on_the_beat():
    """A sign error here still produces a plausible REVIEW tier instead of an
    obvious failure, which is exactly how it survives review."""
    place = _place()
    beat = place.edit_to_music(1_000_000) + 37_000     # 37 ms late
    aligned, shift = sc.fine_align(place, game_edit_us=1_000_000,
                                   music_events=[beat])
    m = sc.measure_against_placement(
        game_event="ROCKET_IMPACT", game_edit_us=1_000_000,
        music_event="BEAT", music_us=beat, placement=aligned)
    assert m.signed_delta_us == 0
    assert m.tier == sc.TIER_TARGET
    assert shift == 37_000


def test_fine_align_refuses_to_leave_the_search_budget():
    place = _place()
    far = place.edit_to_music(1_000_000) + 5_000_000
    aligned, shift = sc.fine_align(place, game_edit_us=1_000_000,
                                   music_events=[far])
    assert shift == 0 and aligned is place


def test_fine_align_with_no_events_is_a_no_op():
    place = _place()
    aligned, shift = sc.fine_align(place, game_edit_us=1, music_events=[])
    assert shift == 0 and aligned is place


# ── payoff must be named (directive M) ──────────────────────────────────────

def _m():
    place = _place()
    return sc.measure_against_placement(
        game_event="ROCKET_IMPACT", game_edit_us=1_000_000,
        music_event="BEAT", music_us=place.edit_to_music(1_000_000),
        placement=place)


def test_a_score_is_not_a_payoff():
    with pytest.raises(ValueError):
        sc.SyncPayoff(payoff="scene matched score 0.82", measurement=_m())


def test_vague_payoff_rejected():
    with pytest.raises(ValueError):
        sc.SyncPayoff(payoff="good", measurement=_m())


def test_a_concrete_payoff_is_accepted():
    p = sc.SyncPayoff(payoff="rocket impact lands on the snare transient",
                      measurement=_m())
    assert p.measurement.tier == sc.TIER_TARGET


# ── corrections are recorded, never overwritten (directive P, Q) ────────────

def test_correction_keeps_both_placements():
    c = sc.SyncCorrection(
        event_type="ROCKET_IMPACT", music_event_type="BEAT",
        track_hash="a" * 64, region_start_us=1_000_000,
        matcher_placement_us=20_000_000, editorial_placement_us=20_042_000,
        original_delta_ms=42.0, final_delta_ms=-1.0)
    assert c.manual_adjustment_ms == 42.0
    assert c.improved
    d = c.to_dict()
    assert d["original_tier"] == sc.TIER_BAD
    assert d["final_tier"] == sc.TIER_TARGET
    # the matcher's recommendation survives in the record
    assert d["matcher_placement_us"] == 20_000_000


def test_a_correction_that_made_it_worse_is_recorded_as_such():
    c = sc.SyncCorrection(
        event_type="FRAG", music_event_type="ACCENT", track_hash="a" * 64,
        region_start_us=0, matcher_placement_us=0,
        editorial_placement_us=50_000,
        original_delta_ms=5.0, final_delta_ms=55.0)
    assert not c.improved


# ── report refuses to average away a bad primary ────────────────────────────

def test_report_surfaces_the_worst_primary():
    place = _place()

    def mk(event, off_ms):
        return sc.measure_against_placement(
            game_event=event, game_edit_us=1_000_000, music_event="BEAT",
            music_us=place.edit_to_music(1_000_000) + int(off_ms * 1000),
            placement=place)

    rep = sc.report([mk("ROCKET_IMPACT", 2.0), mk("FRAG", -60.0),
                     mk("WEAPON_FIRE", 300.0)])
    assert rep["worst_primary_ms"] == -60.0
    assert not rep["all_primary_acceptable"]
    # the secondary miss must not be what gets reported as the worst
    assert "WEAPON_FIRE" not in (rep["worst_primary"] or "")


# ── delivered media (directive D) ───────────────────────────────────────────

from creative_suite.engine import delivered_sync as dsy  # noqa: E402


def test_three_deltas_are_never_collapsed_into_one():
    c = dsy.DeliveredComparison(label="impact", intended_us=10_400_000,
                                rendered_us=10_399_610,
                                post_encode_us=10_399_610)
    assert c.rendered_delta_ms == -0.39
    assert c.post_encode_delta_ms == -0.39
    assert c.encode_shift_ms == 0.0          # the encode moved nothing


def test_encode_shift_is_isolated_from_our_own_error():
    """A 20 ms authoring error and a 5 ms encode shift must not be reported
    as a single 25 ms number -- they have different owners."""
    c = dsy.DeliveredComparison(label="x", intended_us=1_000_000,
                                rendered_us=1_020_000,
                                post_encode_us=1_025_000)
    assert c.rendered_delta_ms == 20.0
    assert c.post_encode_delta_ms == 25.0
    assert c.encode_shift_ms == 5.0


def test_missing_measurement_is_none_not_zero():
    """A failed detection reported as 0 ms would read as perfect sync."""
    c = dsy.DeliveredComparison(label="x", intended_us=1_000_000,
                                rendered_us=None, post_encode_us=None,
                                rendered_reason="window decoded empty")
    assert c.rendered_delta_ms is None
    assert c.post_encode_delta_ms is None
    assert c.encode_shift_ms is None
    assert c.to_dict()["rendered_reason"] == "window decoded empty"


def test_transient_search_on_a_missing_file_reports_why(tmp_path):
    out = dsy.find_transient(tmp_path / "nope.mp4", 1_000_000)
    assert out.found is False
    assert out.onset_us is None
    assert out.reason


def test_find_transient_reports_a_click_where_it_is_not_at_the_window_edge(tmp_path):
    """Regression for a window-edge artifact: spectral flux on a hard-cut
    window produced a spurious onset ~50 ms after the cut, which reported
    itself as a real transient at a CONSTANT offset from the window start
    (-67.8 ms with a 120 ms window, -7.8 ms with a 60 ms window). A padded
    decode with an interior-only search must find the real click instead."""
    import numpy as np, soundfile as sf
    sr = 22050
    y = np.zeros(sr * 4, dtype=np.float32)
    click_s = 2.137
    i = int(click_s * sr)
    y[i:i + 40] = np.linspace(1.0, 0.0, 40, dtype=np.float32)     # a sharp click
    wav = tmp_path / "click.wav"
    sf.write(str(wav), y, sr)
    for window in (60.0, 120.0, 250.0):
        # ask slightly OFF the click so a lazy detector cannot echo the input
        out = dsy.find_transient(wav, int((click_s - 0.020) * 1e6), window_ms=window)
        assert out.found, out.reason
        err_ms = (out.onset_us - click_s * 1e6) / 1000.0
        assert abs(err_ms) <= 12.0, (window, err_ms)        # within ~2 hops
        # and specifically NOT the old artifact position
        lo = (click_s - 0.020) * 1e6 - window * 1000
        assert abs((out.onset_us - lo) / 1000.0 - 52.0) > 5.0


def test_find_transient_on_silence_does_not_invent_an_onset(tmp_path):
    import numpy as np, soundfile as sf
    sr = 22050
    wav = tmp_path / "silence.wav"
    sf.write(str(wav), np.zeros(sr * 2, dtype=np.float32), sr)
    out = dsy.find_transient(wav, 1_000_000, window_ms=120)
    assert out.found is False
    assert out.onset_us is None
