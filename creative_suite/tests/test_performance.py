"""The performance contract: a recorded action compiles back verbatim.

No demo on disk is needed: a small PerformanceTrace is built by hand with the
same shape the extractor produces, performed onto an actor, compiled, and
parsed back with the project's own parser.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from engine.parser.demo_parse import DM73Parser  # noqa: E402
from engine.pantheon.performance import (AimSample, AnimSample,  # noqa: E402
                                         PerformanceTrace, ProjectileSample,
                                         TransformSample, WeaponSample)
from engine.pantheon.scenario import RoundScenario, Team, Weapon  # noqa: E402


def _trace(n: int = 40, start: int = 500_000) -> PerformanceTrace:
    tr = PerformanceTrace(demo_hash="test", map="overkill", gametype="CA",
                          client=5, start_ms=start, end_ms=start + 25 * (n - 1))
    for i in range(n):
        t = start + 25 * i
        o = (100.0 + 8.0 * i, 50.0 - 3.0 * i, 24.0 + (60.0 if 10 <= i < 25 else 0.0))
        v = (320.0, -120.0, 400.0 if 10 <= i < 25 else 0.0)
        tr.transform.append(TransformSample(t, o, v, math.hypot(v[0], v[1]),
                                            10 <= i < 25, 1023 if 10 <= i < 25 else 1022))
        tr.aim.append(AimSample(t, (30.0 + 4.5 * i) % 360.0, -12.0 + 0.5 * i, 0.0, 0.0))
        legs = 18 if 10 <= i < 25 else 15
        tr.animation.append(AnimSample(t, legs, 7 if 18 <= i <= 22 else 11, i % 2 == 0, False))
    tr.weapon.append(WeaponSample(start, 5))
    for i in range(18, 30):
        t = start + 25 * i
        tr.projectiles.append(ProjectileSample(t, 200, 5, (300.0 + 22.0 * i, -20.0, 90.0),
                                               (900.0, 0.0, 0.0)))
    return tr


def _compile(tr: PerformanceTrace, t0: float = 0.6):
    scn = RoundScenario.clan_arena(map_name=tr.map, hostname="T")
    scn.observer((0.0, 0.0, 60.0), yaw=0.0, team=Team.BLUE)
    a = scn.actor("PERF", Team.RED).appearance("sarge", "default")
    a.perform(tr, t0=t0)
    dur = t0 + tr.duration_ms() / 1000.0 + 0.3
    return scn, a, scn.compile(duration=dur)


def test_a_recorded_action_round_trips_exactly(tmp_path):
    tr = _trace()
    scn, a, demo = _compile(tr)
    path = demo.save(tmp_path / "perf.dm_73")
    back = DM73Parser(path, track_missiles=True).parse()
    assert back["packet_errors"] == 0
    rows = {e["server_time_ms"]: e for e in back["entities"] if e["client_num"] == a.client}
    for s, am in zip(tr.transform, tr.aim):
        e = rows[1600 + (s.t - tr.start_ms)]            # base 1000 + t0 600
        assert math.dist(s.origin, (e["origin_x"], e["origin_y"], e["origin_z"])) < 1e-6
        assert math.dist(s.velocity, (e["vel_x"] or 0, e["vel_y"] or 0, e["vel_z"] or 0)) < 1e-6
        assert abs(((e["angle_yaw"] or 0) - am.yaw + 180) % 360 - 180) < 1e-6
        assert abs((e["angle_pitch"] or 0) - am.pitch) < 1e-6
        assert bool(e["airborne"]) == s.airborne
    # every missile sample came back where it was
    ms = {m["server_time_ms"]: m for m in back["missiles"]}
    for p in tr.projectiles:
        m = ms[1600 + (p.t - tr.start_ms)]
        assert math.dist(p.origin, (m["origin_x"], m["origin_y"], m["origin_z"])) < 1e-6
        assert m["weapon"] == 5


def test_recorded_animation_numbers_are_emitted_verbatim(tmp_path):
    from engine.pantheon.performance import _parse_with_anims
    tr = _trace()
    scn, a, demo = _compile(tr)
    path = demo.save(tmp_path / "perf.dm_73")
    _, anims = _parse_with_anims(path)
    got = {x["t"]: x for x in anims if x["client"] == a.client}
    for an in tr.animation:
        x = got[1600 + (an.t - tr.start_ms)]
        assert (x["legs"], x["torso"]) == (an.legs, an.torso)


def test_the_compiler_runs_at_the_real_snapshot_rate():
    from engine.pantheon.scenario import SNAPSHOT_HZ, SNAPSHOT_MS
    assert SNAPSHOT_HZ == 40 and SNAPSHOT_MS == 25      # measured: 25ms p10=p50=p90


def test_an_actor_does_not_exist_before_the_first_recorded_sample():
    tr = _trace()
    scn, a, _ = _compile(tr, t0=2.0)
    assert a._at(1.0).alive is False
    assert a._at(2.0).alive is True


def test_killing_a_recorded_victim_keeps_the_corpse_the_demo_carried():
    tr = _trace()
    scn = RoundScenario.clan_arena(map_name="overkill", hostname="T")
    scn.observer((0.0, 0.0, 60.0), yaw=0.0, team=Team.BLUE)
    v = scn.actor("V", Team.BLUE).appearance("visor", "default"); v.perform(tr, t0=0.6)
    k = scn.actor("K", Team.RED).appearance("sarge", "default")
    k.spawn((0.0, 0.0, 24.0), yaw=0.0, t=0.0, weapon=Weapon.ROCKET); k.stand(until=2.0)
    k.kill(v, mod=Weapon.ROCKET, t=1.0)
    # the recorded samples after the kill are still what the demo said
    late = v._at(1.4)
    assert late.recorded and late.alive
    assert scn._alive[Team.BLUE] == 0                    # the round still counts the kill


def test_an_authored_walk_at_a_third_of_run_speed_is_refused():
    scn = RoundScenario.clan_arena(map_name="overkill", hostname="T")
    scn.observer((0.0, 0.0, 0.0), yaw=0.0)
    a = scn.actor("W", Team.RED).appearance("sarge", "default")
    a.spawn((0.0, 0.0, 0.0), yaw=0.0, t=0.0, weapon=Weapon.RAIL)
    with pytest.raises(ValueError, match="real players run at"):
        a.move_to([(0.0, 0.0, 0.0), (200.0, 0.0, 0.0)], during=(1.0, 3.0))


def _trace_with_events():
    from engine.pantheon.performance import ActionEvent
    tr = _trace()
    s = tr.start_ms
    tr.events = [
        ActionEvent(s + 250, "jump_pad", None, None, None, 0, code=9, carrier="PLAYER"),
        ActionEvent(s + 450, "fire_weapon", 5, None, None, None, code=20, carrier="PLAYER"),
        ActionEvent(s + 475, "fire_weapon", 5, None, None, None, code=20, carrier="PLAYER"),
        ActionEvent(s + 725, "missile_hit", 5, (700.0, -20.0, 90.0), None, 17,
                    code=47, carrier="TEMP", other_entity=3),
    ]
    return tr


def test_recorded_events_come_back_at_their_tick():
    tr = _trace_with_events()
    scn, a, demo = _compile(tr)
    import tempfile
    path = demo.save(Path(tempfile.mkdtemp()) / "ev.dm_73")
    back = DM73Parser(path).parse()
    got = sorted((e["server_time_ms"] - 1600, e["event_code"], e.get("weapon"))
                 for e in back["events"] if e.get("event_code") in (9, 20, 47))
    assert [(t, c) for t, c, _ in got] == [(250, 9), (450, 20), (475, 20), (725, 47)]
    assert [w for _, c, w in got if c != 9] == [5, 5, 5]


def test_identical_consecutive_events_alternate_the_toggle_bit():
    # two fire_weapon 25ms apart: without alternating 0x100/0x200 cgame sees
    # the same value and fires once
    tr = _trace_with_events()
    scn, a, demo = _compile(tr)
    import tempfile
    path = demo.save(Path(tempfile.mkdtemp()) / "ev.dm_73")
    back = DM73Parser(path).parse()
    fires = [e for e in back["events"] if e.get("event_code") == 20]
    assert len(fires) == 2


def test_a_temp_event_carries_position_dir_weapon_and_target():
    tr = _trace_with_events()
    scn, a, demo = _compile(tr)
    import tempfile
    path = demo.save(Path(tempfile.mkdtemp()) / "ev.dm_73")
    back = DM73Parser(path).parse()
    hit = [e for e in back["events"] if e.get("event_code") == 47][0]
    assert (hit["pos_x"], hit["pos_y"], hit["pos_z"]) == (700.0, -20.0, 90.0)
    assert hit["event_parm"] == 17 and hit["weapon"] == 5
