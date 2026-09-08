"""Gameplay timing comes from the demo. Layers never collapse."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import event_truth as et


def _ev(kind=et.MY_LG_CONTACT, owner=et.OWNER_ME, us=1_000_000,
        layer=et.GAME_EVENT_TRUTH, **kw):
    return et.GameEvent(kind=kind, owner=owner, layer=layer, edit_us=us, **kw)


# ── ownership is identity, never audio ──────────────────────────────────────

def test_ownership_can_never_be_inferred_from_audio():
    with pytest.raises(et.OwnershipFromAudioError):
        et.infer_owner_from_audio(b"any waveform at all")


def test_events_carry_an_explicit_owner():
    mine = _ev(owner=et.OWNER_ME)
    theirs = _ev(kind=et.ENEMY_WEAPON_FIRE, owner=et.OWNER_ENEMY)
    assert mine.owner != theirs.owner
    with pytest.raises(ValueError):
        _ev(owner="SOMEBODY")


def test_unknown_kinds_and_layers_are_rejected():
    with pytest.raises(ValueError):
        _ev(kind="MY_VIBES")
    with pytest.raises(ValueError):
        _ev(layer="PROBABLY")


# ── the layers stay apart ───────────────────────────────────────────────────

def test_only_the_truth_layer_is_authoritative():
    truth = _ev()
    assert truth.is_authoritative
    heard = truth.in_layer(et.FULL_GAME_AUDIO, truth.edit_us + 136_700)
    assert not heard.is_authoritative


def test_observing_an_event_elsewhere_does_not_move_the_truth():
    truth = _ev(us=8_875_000)
    heard = truth.in_layer(et.FULL_GAME_AUDIO, 9_011_700,
                           evidence="strongest transient in the mix")
    assert truth.edit_us == 8_875_000
    assert heard.edit_us == 9_011_700
    assert heard.kind == truth.kind and heard.owner == truth.owner


def test_a_timeline_separates_layers_when_asked():
    truth = _ev(us=1_000)
    tl = et.EventTimeline(1, 0, 10_000, (truth,))
    tl = tl.add(truth.in_layer(et.VISUAL_EVENT_DELIVERY, 1_016))
    assert len(tl.layer(et.GAME_EVENT_TRUTH)) == 1
    assert len(tl.layer(et.VISUAL_EVENT_DELIVERY)) == 1
    assert len(tl.of_kind(et.MY_LG_CONTACT)) == 1        # truth layer only


# ── the hero event ──────────────────────────────────────────────────────────

def test_the_hero_event_is_the_frag_not_a_weapon_firing():
    tl = et.EventTimeline(1, 0, 10_000_000, (
        _ev(kind=et.MY_WEAPON_FIRE, us=1_000_000),
        _ev(kind=et.MY_LG_CONTACT, us=2_000_000),
        _ev(kind=et.MY_FRAG, us=8_875_000)))
    hero = tl.hero_event()
    assert hero.kind == et.MY_FRAG
    assert hero.edit_us == 8_875_000
    assert et.MY_WEAPON_FIRE not in et.HERO_CANDIDATE_KINDS


def test_a_scene_with_nothing_to_pay_off_says_so():
    tl = et.EventTimeline(1, 0, 10_000, (_ev(kind=et.MY_WEAPON_FIRE),))
    with pytest.raises(LookupError):
        tl.hero_event()


# ── filtering by owner ──────────────────────────────────────────────────────

def test_events_can_be_filtered_by_who_did_them():
    tl = et.EventTimeline(1, 0, 10_000_000, (
        _ev(owner=et.OWNER_ME, us=1_000_000),
        _ev(kind=et.ENEMY_WEAPON_FIRE, owner=et.OWNER_ENEMY, us=2_000_000),
        _ev(kind=et.ENEMY_WEAPON_FIRE, owner=et.OWNER_ENEMY, us=3_000_000)))
    assert len(tl.owned_by(et.OWNER_ME)) == 1
    assert len(tl.owned_by(et.OWNER_ENEMY)) == 2


# ── round trip ──────────────────────────────────────────────────────────────

def test_a_timeline_round_trips():
    tl = et.EventTimeline(2340, 0, 10_875_000,
                          (_ev(us=1_000_000, amount=7.0, object_client=5),))
    back = et.EventTimeline.from_dict(tl.to_dict())
    assert back == tl


def test_events_are_immutable():
    e = _ev()
    with pytest.raises((AttributeError, TypeError)):
        e.edit_us = 0                     # type: ignore[misc]


# ── measured layer offsets are never promoted to constants ──────────────────

def test_the_latency_table_reports_a_range_and_warns():
    rows = [et.LayerOffset(et.MY_FRAG, et.FULL_GAME_AUDIO, 8_875_000,
                           9_011_700, "onset"),
            et.LayerOffset(et.MY_FRAG, et.FULL_GAME_AUDIO, 1_000_000,
                           1_075_000, "onset")]
    table = et.latency_table(rows)
    row = table["rows"][0]
    assert row["n"] == 2
    assert row["offset_ms_min"] == 75.0
    assert row["offset_ms_max"] == 136.7
    assert "never reuse as a constant" in table["warning"]


def test_layer_offset_reports_a_signed_difference():
    off = et.LayerOffset(et.MY_FRAG, et.FULL_GAME_AUDIO, 8_875_000,
                         9_011_700, "onset")
    assert off.offset_ms == 136.7


# ── the real scene ──────────────────────────────────────────────────────────

@pytest.mark.skipif(not et.RECOGNITION_DB.exists(),
                    reason="recognition database not on this machine")
def test_frag_2340_loads_its_own_contacts_and_breath():
    tl = et.load_lg_timeline(2340, kill_edit_us=8_875_000,
                             scene_start_us=0, scene_end_us=10_875_000)
    contacts = tl.of_kind(et.MY_LG_CONTACT)
    assert len(contacts) == 33
    assert all(c.owner == et.OWNER_ME for c in contacts)
    hero = tl.hero_event()
    assert hero.kind == et.MY_FRAG
    # the 875 ms breath, from the demo rather than from a detector
    assert hero.edit_us - contacts[-1].edit_us == 875_000
    assert tl.of_kind(et.ENEMY_WEAPON_FIRE)
    assert all(e.owner == et.OWNER_ENEMY
               for e in tl.of_kind(et.ENEMY_WEAPON_FIRE))
