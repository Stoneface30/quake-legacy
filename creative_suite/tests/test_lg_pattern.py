"""LG pattern matching: the gameplay pattern is truth, music adapts to it."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import lg_pattern as lg
from creative_suite.engine.music_features_v2 import MusicFeatureV2, MusicRegionV2, MusicEventV2
from creative_suite.engine.scene_recipe import MusicPlacement

# Frag 2340, verified from recognition_lg_engagements.series["dealt"]
CONTACTS = (-7875, -7800, -7525, -7125, -7050, -6875, -6800, -6500, -6400,
            -6050, -5975, -5825, -5750, -5600, -5200, -4875, -4750, -4375,
            -4025, -3800, -3750, -3700, -3475, -3125, -2975, -2900, -2400,
            -2250, -2175, -2050, -1525, -900, -875)


def _pat():
    return lg.GameplayPattern(contacts_rel_ms=CONTACTS)


# ── exact contact preservation ──────────────────────────────────────────────

def test_contacts_are_kept_exactly():
    p = _pat()
    assert p.contacts_rel_ms == CONTACTS
    assert len(p.contacts_rel_ms) == 33


def test_pattern_is_immutable():
    p = _pat()
    with pytest.raises((AttributeError, TypeError)):
        p.contacts_rel_ms = (0,)        # type: ignore[misc]


def test_contacts_must_precede_the_kill_and_be_ordered():
    with pytest.raises(ValueError):
        lg.GameplayPattern(contacts_rel_ms=(-100, 10))
    with pytest.raises(ValueError):
        lg.GameplayPattern(contacts_rel_ms=(-100, -200))
    with pytest.raises(ValueError):
        lg.GameplayPattern(contacts_rel_ms=())


# ── burst grouping ──────────────────────────────────────────────────────────

def test_bursts_group_at_the_documented_gap():
    p = _pat()
    assert [len(b) for b in p.bursts] == [3, 6, 5, 1, 2, 1, 5, 3, 4, 1, 2]
    assert p.gaps_ms == (400, 350, 400, 325, 375, 350, 350, 500, 525, 625)
    assert p.breath_ms == 875
    assert p.span_ms == 7875


def test_notation_is_a_separate_representation():
    p = _pat()
    assert p.notation() == "xxx | xxxxxx | xxxxx | x | xx | x | xxxxx | xxx | xxxx | x | xx | ... | KILL"
    # notation never feeds back into the timestamps
    assert p.contacts_rel_ms == CONTACTS


def test_pattern_id_tracks_the_exact_contacts():
    a = _pat()
    b = lg.GameplayPattern(contacts_rel_ms=CONTACTS[:-1] + (-870,))   # one tick moved 5 ms
    assert a.pattern_id != b.pattern_id


# ── no quantization, no gameplay warping ────────────────────────────────────

def _feature(onsets_us, accents_us, duration_us=60_000_000, bpm=120.0):
    return MusicFeatureV2(
        track_hash="a" * 64, path="t.mp3", duration_us=duration_us,
        sample_rate=44100, channels=2, extractor_version="test", schema_version=2,
        status="OK", bpm=bpm, bpm_confidence=None,
        beats_us=tuple(range(0, duration_us, 500_000)), beat_confidence=None,
        onset_curve=tuple((t, 1.0) for t in onsets_us),
        energy_curve=tuple((t, 0.5) for t in range(0, duration_us, 1_000_000)),
        loudness_curve=(), spectral_curve=(), bar_grid_estimate_us=(),
        section_boundary_estimates_us=(), phrase_boundary_estimates_us=(),
        regions=(MusicRegionV2("HIGH_ENERGY_REGION", 0, duration_us, None),),
        salient_events=tuple(MusicEventV2("ACCENT", t, 1.0, 1.0) for t in accents_us))


def test_search_only_moves_music_and_puts_the_kill_on_the_event():
    p = _pat()
    # present but sparse: one onset a second (the gate requires music to exist)
    f = _feature(onsets_us=list(range(0, 60_000_000, 1_000_000)),
                 accents_us=[20_000_000, 30_000_000])
    top = lg.search(p, [f], kill_edit_us=8_875_000, scene_start_us=0,
                    scene_end_us=10_875_000, philosophy=lg.HIT_RHYTHM_FORWARD)
    assert top
    c = top[0]
    pl = c.placement(0, 10_875_000)
    assert pl.edit_to_music(8_875_000) == c.kill_music_us        # kill ON the event
    assert p.contacts_rel_ms == CONTACTS                          # gameplay untouched
    assert dict(c.components)["KILL_DELTA_MS"] == 0.0


def test_search_never_places_the_window_outside_the_track():
    p = _pat()
    f = _feature(onsets_us=[], accents_us=[1_000_000], duration_us=20_000_000)
    assert lg.search(p, [f], kill_edit_us=8_875_000, scene_start_us=0,
                     scene_end_us=10_875_000, philosophy=lg.BUILD_AND_PAYOFF) == []


# ── components say what they mean ───────────────────────────────────────────

def test_sparse_music_scores_high_on_hit_rhythm_and_space():
    p = _pat()
    sparse = _feature(onsets_us=[], accents_us=[20_000_000])
    busy = _feature(onsets_us=list(range(11_000_000, 22_000_000, 100_000)),
                    accents_us=[20_000_000])
    pl = MusicPlacement(track_id="a" * 64, source_start_us=20_000_000 - 8_875_000,
                        program_edit_start_us=0, source_end_us=20_000_000 + 2_000_000)
    cs = lg.component_scores(p, sparse, pl, 8_875_000, 0, 10_875_000)
    cb = lg.component_scores(p, busy, pl, 8_875_000, 0, 10_875_000)
    assert cs["HIT_RHYTHM_FIT"] > cb["HIT_RHYTHM_FIT"]
    assert cs["MUSIC_ONSET_DENSITY"] < cb["MUSIC_ONSET_DENSITY"]


def test_burst_pattern_fit_rewards_onsets_at_boundaries_not_every_tick():
    p = _pat()
    # onsets exactly at every burst boundary, nothing else
    bounds = [20_000_000 + b * 1000 for b in p.burst_boundaries_ms]
    f = _feature(onsets_us=bounds, accents_us=[20_000_000])
    pl = MusicPlacement(track_id="a" * 64, source_start_us=20_000_000 - 8_875_000,
                        program_edit_start_us=0, source_end_us=22_000_000)
    c = lg.component_scores(p, f, pl, 8_875_000, 0, 10_875_000)
    assert c["BURST_PATTERN_FIT"] == 1.0
    # and it is not asking for one onset per contact: 33 contacts, ~20 boundaries
    assert len(p.burst_boundaries_ms) < len(p.contacts_rel_ms)


def test_three_philosophies_weigh_the_same_facts_differently():
    comp = {"HIT_RHYTHM_FIT": 1.0, "MUSIC_SPACE_FIT": 1.0, "GAME_AUDIO_FOREGROUND_FIT": 1.0,
            "BREATH_SPACE_FIT": 0.0, "FINAL_KILL_FIT": 0.0, "ENERGY_SHAPE_FIT_FLAT": 0.0,
            "BURST_PATTERN_FIT": 0.0, "PHRASE_PAYOFF_FIT": 0.0, "ENERGY_SHAPE_FIT_BUILD": 0.0}
    assert lg.total(comp, lg.HIT_RHYTHM_FORWARD) > lg.total(comp, lg.BUILD_AND_PAYOFF)
    for w in lg.WEIGHTS.values():
        assert abs(sum(w.values()) - 1.0) < 1e-9


def test_every_philosophy_names_its_head_nod():
    for p in lg.PHILOSOPHIES:
        assert len(lg.HEAD_NOD[p]) > 12


# ── mix states are section-level and persist ────────────────────────────────

def test_mix_states_have_gains_and_hit_rhythm_forward_is_the_quietest():
    assert set(lg.MIX_MUSIC_GAIN_DB) == set(lg.MIX_STATES)
    assert lg.MIX_MUSIC_GAIN_DB[lg.MIX_HIT_RHYTHM_FORWARD] < lg.MIX_MUSIC_GAIN_DB[lg.MIX_BALANCED]


def test_silence_cannot_win_hit_rhythm_forward():
    """The degenerate winner the gate exists for: a near-silent stretch."""
    p = _pat()
    silent = _feature(onsets_us=[], accents_us=[20_000_000])
    assert lg.search(p, [silent], kill_edit_us=8_875_000, scene_start_us=0,
                     scene_end_us=10_875_000, philosophy=lg.HIT_RHYTHM_FORWARD) == []


# ── mix-state persistence + canary invariants (directive 17, 21, 24, 31) ────

REVIEW = REPO_ROOT / "output" / "demo_v2" / "review"


@pytest.fixture(scope="module")
def selection():
    p = REVIEW / "EDITORIAL_CANARY_V3_LG_selection.json"
    if not p.exists():
        pytest.skip("LG canary selection not rendered on this machine")
    import json
    return json.loads(p.read_text(encoding="utf-8"))


def test_mix_states_persist_and_validate(selection):
    for v in selection["variants"].values():
        assert v["mix_state"] in lg.MIX_STATES
    assert selection["variants"]["A"]["mix_state"] == lg.MIX_HIT_RHYTHM_FORWARD
    assert selection["per_hit_ducking"] is False


def test_all_variants_share_one_visual_capture(selection):
    assert selection["visual_key"]
    assert selection["requested_rate"] == "1"          # exactly 1/1, no retime
    assert selection["camera"] == "FPV"


def test_canary_does_not_consume_the_frag(selection):
    assert selection["moment_state"].startswith("SHORTLISTED")


def test_every_variant_names_its_head_nod(selection):
    for v in selection["variants"].values():
        assert len(v["head_nod"]) > 12
