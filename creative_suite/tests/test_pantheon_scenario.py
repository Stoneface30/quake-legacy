"""Tests for the PANTHEON scenario layer.

THE POINT OF THE LAYER is that a round is authored as intent and cannot name a
protocol value. So the first thing tested is the boundary itself: if scenario
code can reach an entity field index, the layer is decorative and the class of
bug it exists to prevent is back.
"""
from __future__ import annotations

import inspect
import re

import pytest

from engine.pantheon import compiler as C
from engine.pantheon import scenario as S
from engine.parser.demo_parse import DM73Parser


# ══ the layer boundary ══════════════════════════════════════════════════════

def test_scenario_never_writes_a_bare_protocol_number():
    """The authoring layer maps stance and weapon names onto codec constants;
    it must never contain a literal field index or configstring number.

    The invented-index bug happened because scenario-level code was writing
    `fields[13] = 7`. A grep is a blunt instrument, but it is exactly the
    instrument that would have caught it.
    """
    src = inspect.getsource(S)
    # strip the docstrings and comments where numbers are legitimately quoted
    body = re.sub(r'"""[\s\S]*?"""', "", src)
    body = "\n".join(l.split("#")[0] for l in body.splitlines())
    offenders = re.findall(r"\bfields?\s*\[\s*\d+\s*\]", body)
    offenders += re.findall(r"\bcs\s*\(\s*\d{3}", body)
    assert not offenders, f"scenario reached for a protocol value: {offenders}"


def test_only_the_compiler_knows_the_configstring_indices():
    assert C.CS_RED_PLAYERS_LEFT == 663 and C.CS_BLUE_PLAYERS_LEFT == 664
    assert not hasattr(S, "CS_RED_PLAYERS_LEFT")
    assert not hasattr(S, "CS_ROUND_STATUS")


def test_mod_table_is_derived_from_the_parser_not_restated():
    """It was restated once and mapped RAIL onto LIGHTNING, so a teaching card
    would have named the wrong weapon."""
    from engine.parser.demo_parse import _MOD_NAMES
    assert _MOD_NAMES[C.MOD_BY_WEAPON[S.Weapon.RAIL.value]] == "RAILGUN"
    assert _MOD_NAMES[C.MOD_BY_WEAPON[S.Weapon.ROCKET.value]] == "ROCKET_SPLASH"
    assert _MOD_NAMES[C.MOD_BY_WEAPON[S.Weapon.LIGHTNING.value]] == "LIGHTNING"


def test_stances_map_onto_real_observed_animation_numbers():
    from engine.parser import dm73_write as W
    assert S._LEGS[S.Stance.RUN] == W.LEGS_RUN
    assert S._LEGS[S.Stance.IDLE] == W.LEGS_IDLE
    assert S._TORSO[S.Stance.ATTACK] == W.TORSO_ATTACK
    assert S._TORSO[S.Stance.IDLE] == W.TORSO_STAND


# ══ authoring semantics ═════════════════════════════════════════════════════

def _round(n_per_team: int = 4) -> S.RoundScenario:
    scn = S.RoundScenario.clan_arena(map_name="campgrounds")
    scn.observer((0.0, 0.0, 100.0), yaw=90.0)
    for i in range(n_per_team):
        scn.actor(f"RED_{i+1}", S.Team.RED).spawn((100.0 + i * 40, 0.0, 100.0))
        scn.actor(f"BLUE_{i+1}", S.Team.BLUE).spawn((-100.0 - i * 40, 0.0, 100.0))
    return scn


def test_roster_is_counted_at_spawn_so_kills_decrement_from_the_right_base():
    """Counting the roster at compile time made every authored kill decrement
    from zero: the timeline read -1, -2, -3."""
    scn = _round()
    assert scn._alive == {S.Team.RED: 4, S.Team.BLUE: 4}
    scn.actors["RED_1"].kill(scn.actors["BLUE_1"], mod=S.Weapon.ROCKET, t=5.0)
    assert scn._alive == {S.Team.RED: 4, S.Team.BLUE: 3}


def test_timeline_reports_semantic_features_in_order():
    scn = _round()
    scn.begin_round(at=2.0, countdown=2.0)
    scn.actors["RED_1"].kill(scn.actors["BLUE_1"], mod=S.Weapon.RAIL, t=5.0)
    scn.round_win(S.Team.RED, t=6.0)
    scn.reset_round(t=8.0)
    feats = [r["feature"] for r in scn.timeline()]
    assert feats == ["round_announced", "round_active", "alive_change", "kill",
                     "round_win", "round_reset"]
    assert [r["t"] for r in scn.timeline()] == sorted(r["t"] for r in scn.timeline())


def test_a_move_needs_a_real_route_and_a_forward_window():
    scn = _round()
    a = scn.actors["RED_1"]
    with pytest.raises(ValueError):
        a.move_to([(0.0, 0.0, 0.0)], during=(1.0, 2.0))      # one point
    with pytest.raises(ValueError):
        a.move_to([(0.0, 0.0, 0.0), (1.0, 1.0, 0.0)], during=(2.0, 1.0))


def test_compiling_without_an_observer_is_refused():
    scn = S.RoundScenario.clan_arena(map_name="campgrounds")
    scn.actor("RED_1", S.Team.RED).spawn((0.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="observer"):
        scn.compile(duration=1.0)


# ══ the compiled grammar ════════════════════════════════════════════════════

def _compile_full_round(tmp_path):
    scn = _round()
    scn.begin_round(at=2.0, countdown=2.0)
    scn.actors["RED_1"].kill(scn.actors["BLUE_1"], mod=S.Weapon.ROCKET, t=5.0)
    scn.actors["BLUE_2"].kill(scn.actors["RED_2"], mod=S.Weapon.RAIL, t=7.0)
    scn.round_win(S.Team.RED, t=9.0)
    scn.reset_round(t=11.0)
    path = scn.compile(duration=14.0).save(tmp_path / "round.dm_73")
    parser = DM73Parser(path)
    seen: list[tuple[int, int, str]] = []
    orig = parser._absorb_cs

    def hook(idx, val):
        if idx in (C.CS_ROUND_STATUS, C.CS_RED_PLAYERS_LEFT,
                   C.CS_BLUE_PLAYERS_LEFT, C.CS_ROUND_WINNERS):
            seen.append((parser._last_server_time, idx, val))
        orig(idx, val)
    parser._absorb_cs = hook
    return parser.parse(), seen


def test_alive_counters_ramp_up_before_they_count_down(tmp_path):
    """The observed grammar, not a simplification of it. Real rounds drive
    both counters to 0 and count UP one at a time; emitting the final level
    starts the HUD wrong."""
    _out, seen = _compile_full_round(tmp_path)
    red = [int(v) for _t, i, v in seen if i == C.CS_RED_PLAYERS_LEFT]
    blue = [int(v) for _t, i, v in seen if i == C.CS_BLUE_PLAYERS_LEFT]
    assert red[:6] == [0, 0, 1, 2, 3, 4], red[:6]
    assert blue[:6] == [0, 0, 1, 2, 3, 4], blue[:6]
    assert 3 in blue and 3 in red          # deaths brought them down
    assert red[-1] == 4 and blue[-1] == 4  # the reset rebuilt the ramp


def test_round_is_announced_with_a_future_timestamp(tmp_path):
    """661 carries `\\time\\<future>\\round\\<N>` -- the countdown window."""
    _out, seen = _compile_full_round(tmp_path)
    announces = [(t, v) for t, i, v in seen if i == C.CS_ROUND_STATUS
                 and r"\round\1" in v and r"\time\-1" not in v]
    assert announces, "the round was never announced"
    t, value = announces[0]
    future = int(re.search(r"\\time\\(-?\d+)", value).group(1))
    assert future > t, f"announcement at {t} must name a later start, got {future}"


def test_the_round_resolves_and_resets(tmp_path):
    _out, seen = _compile_full_round(tmp_path)
    assert any(i == C.CS_ROUND_WINNERS and v == str(S.Team.RED.value)
               for _t, i, v in seen)
    assert any(i == C.CS_ROUND_STATUS and r"\round\2" in v
               for _t, i, v in seen), "the reset must announce the next round"


def test_kills_become_obituaries_with_the_right_teams(tmp_path):
    out, _seen = _compile_full_round(tmp_path)
    assert out["packet_errors"] == 0
    obits = [e for e in out["events"] if e["type"] == "obituary"]
    assert len(obits) == 2
    assert obits[0]["killer_team"] == "RED" and obits[0]["victim_team"] == "BLUE"
    assert obits[0]["weapon_name"] == "ROCKET_SPLASH"
    assert obits[1]["killer_team"] == "BLUE" and obits[1]["victim_team"] == "RED"
    assert obits[1]["weapon_name"] == "RAILGUN"


def test_a_dead_actor_stops_being_sent(tmp_path):
    """Elimination removes the body. If it kept streaming, the round would
    look like nobody died however the counters read."""
    scn = _round(n_per_team=1)
    scn.begin_round(at=1.0, countdown=0.5)
    scn.actors["RED_1"].kill(scn.actors["BLUE_1"], mod=S.Weapon.ROCKET, t=3.0)
    path = scn.compile(duration=6.0).save(tmp_path / "dead.dm_73")
    parser = DM73Parser(path)
    present: list[tuple[int, set]] = []
    orig = parser._parse_snapshot

    def hook(s, e, sn):
        orig(s, e, sn)
        present.append((parser._last_server_time,
                        {n for n, st in parser._entity_states.items()
                         if n < 64 and st.get(12) == 1}))
    parser._parse_snapshot = hook
    parser.parse()
    victim = scn.actors["BLUE_1"].client
    before = [p for t, p in present if t < 3500]
    after = [p for t, p in present if t > 4000]
    assert any(victim in p for p in before), "victim should exist before dying"
    assert all(victim not in p for p in after), "victim must be gone after"


def test_an_actor_does_not_exist_before_it_spawns():
    # The cast sheet stacked twelve characters on one mark because _at()
    # returned the first keyframe, alive, for every t before it.
    from engine.pantheon.scenario import RoundScenario, Team, Weapon
    scn = RoundScenario.clan_arena(map_name="overkill", hostname="T")
    scn.observer((0.0, 0.0, 0.0), yaw=0.0)
    a = scn.actor("LATE", Team.RED).appearance("orbb", "default")
    a.spawn((100.0, 0.0, 0.0), yaw=0.0, t=24.0, weapon=Weapon.RAIL)
    a.stand(until=30.0)
    assert a._at(0.8).alive is False
    assert a._at(23.99).alive is False
    assert a._at(24.0).alive is True
    assert a._at(27.0).alive is True
