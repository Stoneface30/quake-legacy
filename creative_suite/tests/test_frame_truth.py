"""FrameTruth is the single source of world state for every backend."""
from __future__ import annotations

import pytest

from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.scenario import RoundScenario, Team, Weapon, SNAPSHOT_HZ


def _scn() -> RoundScenario:
    scn = RoundScenario.clan_arena(map_name="campgrounds")
    scn.observer((0.0, 0.0, 100.0), yaw=0.0)
    r = scn.actor("RED_1", Team.RED).spawn((100.0, 0.0, 50.0))
    b = scn.actor("BLUE_1", Team.BLUE).spawn((300.0, 0.0, 50.0))
    scn.begin_round(at=3.0, countdown=2.0)   # pre 0-1, countdown 1-3
    r.move_to([(100.0, 0.0, 50.0), (200.0, 40.0, 50.0)], during=(3.0, 5.0))
    b.take_damage(70, source=r, t=6.0)
    r.kill(b, mod=Weapon.ROCKET, t=7.0)
    scn.round_win(Team.RED, t=8.0)
    scn.reset_round(t=9.0)
    return scn


def test_frame_truth_shares_the_demo_clock():
    """One time basis. A FrameTruth frame and a demo snapshot must be the same
    instant, not two nearby ones -- otherwise an overlay drifts against the
    picture it annotates."""
    ft = FrameTruth.from_scenario(_scn(), duration=10.0)
    assert ft.snapshot_hz == SNAPSHOT_HZ
    assert ft.frames[0].server_time_ms == 1000
    step = ft.frames[1].server_time_ms - ft.frames[0].server_time_ms
    assert step == 1000 // SNAPSHOT_HZ
    for f in ft.frames:
        assert f.server_time_ms == 1000 + round(f.t * 1000)


def test_actor_track_is_world_space_and_moves():
    ft = FrameTruth.from_scenario(_scn(), duration=10.0)
    track = ft.actor_track("RED_1")
    xs = {p[0] for _t, p in track}
    assert len(xs) > 5, "the actor should have travelled"


def test_health_and_alive_state_follow_the_authored_round():
    ft = FrameTruth.from_scenario(_scn(), duration=10.0)
    before = ft.at(5.0).actors["BLUE_1"]
    hurt = ft.at(6.5).actors["BLUE_1"]
    dead = ft.at(7.5).actors["BLUE_1"]
    assert before.health == 200 and before.alive
    assert hurt.health < before.health, "damage must land in the truth"
    assert dead.alive is False


def test_round_phase_and_alive_counts_are_present():
    ft = FrameTruth.from_scenario(_scn(), duration=10.0)
    assert ft.at(0.5).round_state.phase == "pre"
    assert ft.at(2.0).round_state.phase == "countdown"
    assert ft.at(4.0).round_state.phase == "active"
    assert ft.at(8.5).round_state.phase == "over"
    assert ft.at(4.0).round_state.alive_blue == 1
    assert ft.at(7.5).round_state.alive_blue == 0


def test_semantic_events_land_on_a_frame():
    ft = FrameTruth.from_scenario(_scn(), duration=10.0)
    kills = ft.events("kill")
    assert len(kills) == 1
    assert kills[0].actor == "RED_1" and kills[0].target == "BLUE_1"
    assert any(e.kind == "round_win" for e in ft.events())
    assert any(e.kind == "round_reset" for e in ft.events())


def test_lookup_never_interpolates_between_frames():
    """A frame IS the sample. Inventing one between two would be a third
    derivation of a truth that is already authoritative."""
    ft = FrameTruth.from_scenario(_scn(), duration=10.0)
    a = ft.at(3.014)
    assert a in ft.frames


def test_serialises_without_any_player_name():
    """Actor ids are normalized team labels, never nicknames."""
    ft = FrameTruth.from_scenario(_scn(), duration=4.0)
    body = str(ft.to_dict())
    for actor_id in ft.frames[0].actors:
        assert actor_id.startswith(("RED_", "BLUE_")), actor_id
    assert "SYNTHETIC_EXPLAINER" in body
