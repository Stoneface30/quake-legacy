"""Perceptual musical anchors: onset is not the perceived hit.

Synthetic signals, so the expected answer is known by construction rather
than by listening to a particular track.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import music_anchor_v3 as v3

SR = v3.SR


def _click(at_s: float, dur_s: float = 2.0, rise_ms: float = 1.0,
           freq: float = 90.0, decay_s: float = 0.12,
           amp: float = 0.9) -> np.ndarray:
    """One percussive hit: near-instant rise, exponential decay."""
    y = np.zeros(int(SR * dur_s), dtype=np.float32)
    i = int(at_s * SR)
    n = int(SR * decay_s)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * freq * t) * np.exp(-t / (decay_s / 4))
    rise = int(max(1, SR * rise_ms / 1000.0))
    body[:rise] *= np.linspace(0.0, 1.0, rise)
    y[i:i + n] += (amp * body).astype(np.float32)
    return y


def _swell(at_s: float, dur_s: float = 2.0, rise_ms: float = 180.0,
           freq: float = 220.0, amp: float = 0.9) -> np.ndarray:
    """One slow harmonic attack: a long linear rise to the peak."""
    y = np.zeros(int(SR * dur_s), dtype=np.float32)
    i = int(at_s * SR)
    rise = int(SR * rise_ms / 1000.0)
    hold = int(SR * 0.25)
    t = np.arange(rise + hold) / SR
    tone = np.sin(2 * np.pi * freq * t)
    envelope = np.concatenate([np.linspace(0.0, 1.0, rise),
                               np.linspace(1.0, 0.3, hold)])
    y[i:i + rise + hold] += (amp * tone * envelope).astype(np.float32)
    return y


# ── onset is not the P-center ───────────────────────────────────────────────

def test_fast_attack_puts_the_pcenter_almost_on_the_onset():
    y = _click(0.8)
    a = v3.analyse_samples(y, SR)
    assert a, "a click must be detected"
    hit = min(a, key=lambda x: abs(x.acoustic_onset_us - 800_000))
    assert hit.attack_class == v3.ATTACK_FAST
    assert hit.pcenter_offset_ms <= 10.0
    assert hit.pcenter_confidence >= 0.5


def test_slow_attack_puts_the_pcenter_far_after_the_onset():
    y = _swell(0.8)
    a = v3.analyse_samples(y, SR)
    assert a, "a swell must be detected"
    hit = max(a, key=lambda x: x.attack_rise_us)
    assert hit.attack_class == v3.ATTACK_SLOW
    # This is the whole point of the module: tens of ms, not ~zero.
    assert hit.pcenter_offset_ms >= 25.0


def test_the_two_are_ordered_the_way_the_research_says():
    fast = min(v3.analyse_samples(_click(0.8), SR),
               key=lambda x: abs(x.acoustic_onset_us - 800_000))
    slow = max(v3.analyse_samples(_swell(0.8), SR), key=lambda x: x.attack_rise_us)
    assert fast.pcenter_offset_ms < slow.pcenter_offset_ms
    assert fast.pcenter_confidence > slow.pcenter_confidence


def test_attack_class_boundaries():
    assert v3.attack_class_for(5.0) == v3.ATTACK_FAST
    assert v3.attack_class_for(v3.FAST_MAX_MS) == v3.ATTACK_FAST
    assert v3.attack_class_for(v3.FAST_MAX_MS + 0.1) == v3.ATTACK_MEDIUM
    assert v3.attack_class_for(v3.MEDIUM_MAX_MS + 0.1) == v3.ATTACK_SLOW


def test_pcenter_never_escapes_its_own_bracket():
    env = np.concatenate([np.zeros(100), np.linspace(0, 1, 200), np.ones(50)])
    idx, conf = v3.estimate_pcenter(env.astype(np.float32), SR, 100, 300)
    assert 100 <= idx <= 300
    assert 0.0 <= conf <= 1.0


def test_anchor_rejects_an_impossible_perceptual_time():
    with pytest.raises(ValueError):
        v3.MusicalAnchorV3(
            acoustic_onset_us=1000, attack_rise_us=100, energy_peak_us=1100,
            perceptual_anchor_us=5000,          # after the peak: impossible
            pcenter_method="X", pcenter_confidence=0.5,
            attack_class=v3.ATTACK_FAST, component=v3.COMPONENT_PERCUSSIVE,
            percussive_ratio=0.9, band_energy=(), onset_strength=1.0, salience=1.0)


# ── timbre: bands and components ────────────────────────────────────────────

def test_band_energy_is_normalised_and_finds_the_right_band():
    low = v3.analyse_samples(_click(0.8, freq=60.0), SR)
    high = v3.analyse_samples(_click(0.8, freq=6000.0, decay_s=0.05), SR)
    assert low and high
    lo = min(low, key=lambda x: abs(x.acoustic_onset_us - 800_000))
    hi = min(high, key=lambda x: abs(x.acoustic_onset_us - 800_000))
    assert abs(sum(v for _, v in lo.band_energy) - 1.0) < 0.01
    assert lo.dominant_band == "SUB_LOW"
    assert hi.dominant_band == "HIGH"


def test_component_labels_follow_the_percussive_ratio():
    assert v3.component_for(0.95) == v3.COMPONENT_PERCUSSIVE
    assert v3.component_for(0.5) == v3.COMPONENT_MIXED
    assert v3.component_for(0.1) == v3.COMPONENT_HARMONIC


def test_a_click_reads_more_percussive_than_a_sustained_tone():
    click = min(v3.analyse_samples(_click(0.8), SR),
                key=lambda x: abs(x.acoustic_onset_us - 800_000))
    swell = max(v3.analyse_samples(_swell(0.8), SR), key=lambda x: x.attack_rise_us)
    assert click.percussive_ratio > swell.percussive_ratio


# ── compound accents ────────────────────────────────────────────────────────

def _anchor(onset_ms: float, attack: str = v3.ATTACK_FAST,
            salience: float = 1.0, rise_ms: float = 3.0) -> v3.MusicalAnchorV3:
    on = int(onset_ms * 1000)
    return v3.MusicalAnchorV3(
        acoustic_onset_us=on, attack_rise_us=int(rise_ms * 1000),
        energy_peak_us=on + int(rise_ms * 1000),
        perceptual_anchor_us=on + int(rise_ms * 500),
        pcenter_method="TEST", pcenter_confidence=0.9, attack_class=attack,
        component=v3.COMPONENT_PERCUSSIVE, percussive_ratio=0.8,
        band_energy=(("SUB_LOW", 1.0),), onset_strength=1.0, salience=salience)


def test_near_simultaneous_hits_fuse_into_one_accent():
    acc = v3.cluster_accents([_anchor(0), _anchor(12), _anchor(20)])
    assert len(acc) == 1
    assert acc[0].is_compound
    assert len(acc[0].constituents) == 3


def test_two_sharp_hits_far_enough_apart_stay_separate():
    acc = v3.cluster_accents([_anchor(0), _anchor(v3.SEPARABLE_FAST_MS + 5)])
    assert len(acc) == 2
    assert all(not a.is_compound for a in acc)


def test_a_slow_attack_joins_a_nearby_sharp_edge_and_the_edge_wins():
    acc = v3.cluster_accents([
        _anchor(0, v3.ATTACK_FAST, salience=0.6),
        _anchor(60, v3.ATTACK_SLOW, salience=1.0, rise_ms=120.0)])
    assert len(acc) == 1
    # timing comes from the fast edge even though the slow one is louder
    assert acc[0].dominant.attack_class == v3.ATTACK_FAST


def test_clustering_preserves_every_constituent_and_averages_nothing():
    parts = [_anchor(0), _anchor(10), _anchor(18)]
    acc = v3.cluster_accents(parts)[0]
    assert [c.acoustic_onset_us for c in acc.constituents] == [0, 10_000, 18_000]
    assert acc.perceptual_anchor_us in {c.perceptual_anchor_us for c in parts}


def test_the_fusion_decision_explains_itself():
    acc = v3.cluster_accents([_anchor(0), _anchor(200)])
    assert all(a.reason for a in acc)


# ── negative space ──────────────────────────────────────────────────────────

def _with_hole(hole_s: float = 0.875, event_s: float = 4.0) -> np.ndarray:
    """Drums every 250 ms, silent across the gap, then a hit on the event."""
    y = np.zeros(int(SR * (event_s + 1.0)), dtype=np.float32)
    t = 0.5
    while t < event_s - hole_s:
        y += np.pad(_click(t, dur_s=event_s + 1.0), (0, 0))[:y.size]
        t += 0.25
    y += _click(event_s, dur_s=event_s + 1.0, amp=1.0)[:y.size]
    return y


def test_a_real_hole_is_detected_and_named():
    y = _with_hole()
    ns = v3.negative_space(y, SR, offset_us=0, event_us=4_000_000)
    assert ns.percussive_drop_db <= -6.0
    assert ns.percussive_return_db >= 6.0
    assert ns.is_negative_space
    assert ns.shape != "NO_HOLE"


def test_continuous_drums_are_not_a_hole():
    y = np.zeros(int(SR * 5.0), dtype=np.float32)
    t = 0.5
    while t < 4.6:
        y += _click(t, dur_s=5.0)[:y.size]
        t += 0.25
    ns = v3.negative_space(y, SR, offset_us=0, event_us=4_000_000)
    assert not ns.is_negative_space
    assert ns.shape == "NO_HOLE"


def test_total_energy_alone_would_miss_a_hole_filled_by_a_pad():
    """The canary case: drums stop, a pad holds the level up."""
    y = _with_hole()
    pad = _swell(3.1, dur_s=5.0, rise_ms=400.0, amp=0.5)[:y.size]
    ns = v3.negative_space(y + pad, SR, offset_us=0, event_us=4_000_000)
    # total energy barely moves, but the drums still left
    assert ns.percussive_drop_db <= -6.0
    assert ns.is_negative_space


def test_onset_density_uses_one_scale_for_every_span():
    """A quiet span must not be normalised into looking busy."""
    y = _with_hole()
    ns = v3.negative_space(y, SR, offset_us=0, event_us=4_000_000)
    assert ns.pre_event_onset_density < ns.baseline_onset_density


# ── roles ───────────────────────────────────────────────────────────────────

def test_metrical_role_reads_the_tracks_own_grid_and_invents_nothing():
    beats = [0, 500_000, 1_000_000, 1_500_000]
    bars = [0, 2_000_000]
    assert v3.metrical_role(1_000_010, beats_us=beats, bars_us=bars) == v3.ROLE_BEAT
    assert v3.metrical_role(10_000, beats_us=beats, bars_us=bars) == v3.ROLE_DOWNBEAT
    assert v3.metrical_role(750_000, beats_us=beats, bars_us=bars) == v3.ROLE_SUBDIVISION
    # 1.4 s is 100 ms from the nearest beat and 150 ms from the nearest
    # subdivision: off the grid entirely.
    assert v3.metrical_role(1_400_000, beats_us=beats, bars_us=bars) == v3.ROLE_NONE
    assert v3.metrical_role(1_000_000, beats_us=(), bars_us=()) == v3.ROLE_NONE


def test_structural_role_needs_evidence():
    assert v3.structural_role(1_000_000, ()) == v3.STRUCT_NONE
    rising = [(t, 0.1) for t in range(0, 1_000_000, 100_000)] + \
             [(t, 1.0) for t in range(1_000_000, 3_000_000, 100_000)]
    assert v3.structural_role(1_000_000, rising,
                              boundaries_us=[1_000_000]) == v3.STRUCT_DROP_ENTRY
    falling = [(t, 1.0) for t in range(0, 1_000_000, 100_000)] + \
              [(t, 0.1) for t in range(1_000_000, 3_000_000, 100_000)]
    assert v3.structural_role(1_000_000, falling) == v3.STRUCT_BREAKDOWN


# ── cache and provenance ────────────────────────────────────────────────────

def test_cache_is_keyed_by_analyzer_version_and_params(tmp_path):
    store = v3.AnchorCacheStore(tmp_path / "anchors.db")
    wa = v3.WindowAnalysis(track_hash="a" * 64, start_us=0, end_us=1_000_000,
                           analyzer_version=v3.ANALYZER_VERSION,
                           params_hash=v3.params_hash(**v3.DEFAULT_PARAMS),
                           anchors=(_anchor(10),))
    store.put(wa)
    assert store.get("a" * 64, 0, 1_000_000) is not None
    # a different analyzer version must MISS, never silently reuse
    assert store.get("a" * 64, 0, 1_000_000, analyzer_version="other") is None
    assert store.get("a" * 64, 0, 1_000_000, params="deadbeef") is None
    assert store.get("a" * 64, 0, 2_000_000) is None


def test_analysis_round_trips_through_the_cache(tmp_path):
    store = v3.AnchorCacheStore(tmp_path / "anchors.db")
    wa = v3.WindowAnalysis(track_hash="b" * 64, start_us=5, end_us=1_000_000,
                           analyzer_version=v3.ANALYZER_VERSION,
                           params_hash=v3.params_hash(**v3.DEFAULT_PARAMS),
                           anchors=(_anchor(10), _anchor(200)))
    store.put(wa)
    back = store.get("b" * 64, 5, 1_000_000)
    assert back.anchors == wa.anchors


def test_every_anchor_carries_its_provenance():
    a = v3.analyse_samples(_click(0.8), SR)
    assert a
    assert all(dict(x.provenance).get("analyzer") == v3.ANALYZER_VERSION for x in a)
    assert all(x.pcenter_method == "ENVELOPE_HALF_RISE" for x in a)


def test_anchors_are_immutable():
    a = _anchor(10)
    with pytest.raises((AttributeError, TypeError)):
        a.perceptual_anchor_us = 0        # type: ignore[misc]


def test_silence_yields_no_anchors_rather_than_a_guess():
    assert v3.analyse_samples(np.zeros(SR, dtype=np.float32), SR) == []
