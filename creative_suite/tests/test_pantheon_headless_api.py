"""The headless loop: extract -> retarget -> compile -> reextract -> compare.

No demo on disk, no game process. A hand-built trace in the extractor's own
shape is compiled to a synthetic demo, read back with the same extractor, and
compared track by track.
"""
from __future__ import annotations

import math

import pytest

from creative_suite.tests.pantheon_fixtures import jumppad_rocket_trace, victim_trace
from engine.pantheon import headless as H
from engine.pantheon.compare import Status, Tolerances, compare
from engine.pantheon.performance import PerformanceTrace
from engine.pantheon.retarget import Retarget, TransformMode, validate_retarget


# ── retarget arithmetic ────────────────────────────────────────────────────

def test_exact_world_is_the_identity():
    rt = Retarget.exact_world()
    assert rt.mode is TransformMode.EXACT_WORLD and rt.is_identity()
    assert rt.place((1.0, 2.0, 3.0)) == (1.0, 2.0, 3.0)
    assert rt.turn((4.0, 5.0, 6.0)) == (4.0, 5.0, 6.0)
    assert rt.yaw(350.0) == 350.0


def test_local_frame_moves_the_anchor_onto_the_target_and_turns_the_heading():
    tr = jumppad_rocket_trace()
    rt = Retarget.local_frame(tr, to=(-1000.0, 400.0, 88.0), yaw=90.0)
    anchor = next(s.origin for s in tr.transform if not s.airborne)
    placed = rt.place(anchor)
    assert all(abs(a - b) < 1e-6 for a, b in zip(placed, (-1000.0, 400.0, 88.0)))
    assert abs(rt.yaw(tr.aim[0].yaw) - 90.0) < 1e-6
    # rigid: distances between samples are preserved
    a, b = tr.transform[3].origin, tr.transform[40].origin
    assert abs(math.dist(rt.place(a), rt.place(b)) - math.dist(a, b)) < 1e-6
    assert rt.perform_kwargs() == {"offset": rt.offset, "yaw_offset": rt.yaw_offset}


class _Everywhere:
    def is_walked(self, pos):
        return True


class _Nowhere:
    def is_walked(self, pos):
        return False


def test_retarget_validation_checks_grounded_samples_and_the_landing():
    tr = jumppad_rocket_trace()
    rt = Retarget.local_frame(tr, to=(0.0, 0.0, 0.0))
    ok = validate_retarget(tr, rt, _Everywhere())
    assert ok.ok and ok.fraction_walked == 1.0 and ok.landing_in_walked is True
    bad = validate_retarget(tr, rt, _Nowhere())
    assert not bad.ok and bad.grounded_in_walked == 0 and bad.landing_in_walked is False
    assert any("landing" in n for n in bad.notes)
    # EXACT_WORLD never consults the map: the real player stood there
    assert validate_retarget(tr, Retarget.exact_world(), _Nowhere()).ok


# ── compare semantics ──────────────────────────────────────────────────────

def test_a_trace_compared_with_itself_is_matched_on_every_track():
    tr = jumppad_rocket_trace()
    d = compare(tr, tr)
    assert d.semantic_fidelity == "PASS"
    assert all(t.status is Status.MATCHED for t in d.tracks.values()), d.statuses()


def test_an_observation_gap_is_reported_and_never_filled():
    v = victim_trace(gap=(20, 40))
    d = compare(v, v)
    assert d.tracks["position"].unobserved_spans_ms == [(500_000 + 25 * 19, 500_000 + 25 * 40)]
    assert d.tracks["position"].status is Status.MATCHED       # every OBSERVED sample matched
    assert d.tracks["projectiles"].status is Status.UNOBSERVED  # nothing to compare


def test_missing_and_invalid_are_told_apart():
    tr = jumppad_rocket_trace()
    short = PerformanceTrace.from_dict(tr.as_dict())
    short.transform = short.transform[:-5]
    assert compare(tr, short).tracks["position"].status is Status.MISSING

    wrong = PerformanceTrace.from_dict(tr.as_dict())
    o = wrong.transform[7].origin
    wrong.transform[7].origin = (o[0] + 5.0, o[1], o[2])
    d = compare(tr, wrong)
    assert d.tracks["position"].status is Status.INVALID
    assert d.semantic_fidelity == "FAIL"
    assert compare(tr, wrong, tol=Tolerances(position_u=10.0)).tracks["position"].status \
        is Status.WITHIN_TOLERANCE


def test_intentional_differences_are_declared_not_judged():
    tr = jumppad_rocket_trace()
    other = PerformanceTrace.from_dict(tr.as_dict())
    other.events = []
    d = compare(tr, other, intentional=["events"])
    assert d.tracks["event:fire_weapon"].status is Status.INTENTIONAL_DIFFERENCE
    assert d.semantic_fidelity == "PASS"
    assert compare(tr, other).tracks["event:fire_weapon"].status is Status.MISSING


def test_compare_applies_the_retarget_to_the_real_side():
    tr = jumppad_rocket_trace()
    rt = Retarget.local_frame(tr, to=(-500.0, 250.0, 24.0), yaw=123.0)
    moved = PerformanceTrace.from_dict(tr.as_dict())
    for s in moved.transform:
        s.origin, s.velocity = rt.place(s.origin), rt.turn(s.velocity)
    for a in moved.aim:
        a.yaw = rt.yaw(a.yaw)
    for p in moved.projectiles:
        p.origin = rt.place(p.origin)
    assert compare(tr, moved).tracks["position"].status is Status.INVALID
    d = compare(tr, moved, retarget=rt)
    assert d.tracks["position"].status in (Status.MATCHED, Status.WITHIN_TOLERANCE)
    assert d.tracks["yaw"].status in (Status.MATCHED, Status.WITHIN_TOLERANCE)


# ── the full headless loop ─────────────────────────────────────────────────

def _loop(tmp_path, retarget=None, **kw):
    shooter, victim = jumppad_rocket_trace(), victim_trace()
    compiled = H.compile_performance({"SHOOTER": shooter, "VICTIM": victim},
                                     cast={"SHOOTER": ("anarki", "default"),
                                           "VICTIM": ("visor", "default")},
                                     retarget=retarget, **kw)
    compiled.save(tmp_path / "perf.dm_73")
    back = H.reextract(compiled)
    diffs = {n: compare(compiled.traces[n], back[n], retarget=compiled.retarget)
             for n in compiled.traces}
    return compiled, back, diffs


def test_exact_world_round_trip_matches_every_observed_track(tmp_path):
    compiled, back, diffs = _loop(tmp_path)
    s = diffs["SHOOTER"]
    for track in ("position", "velocity", "airborne", "yaw", "pitch", "animation",
                  "weapon", "projectiles"):
        assert s.tracks[track].status is Status.MATCHED, (track, s.tracks[track])
    v = diffs["VICTIM"]
    assert v.tracks["position"].status is Status.MATCHED
    assert v.tracks["position"].unobserved_spans_ms      # the gap survived the trip
    assert back["VICTIM"].transform[0].t == compiled.window("VICTIM")[0]


def test_events_come_back_from_the_synthetic_game_state(tmp_path):
    """fire_weapon, jump_pad, missile_hit and the obituary are GAME STATE:
    the compiler emits them and the parser reads them back at the same tick."""
    compiled, back, diffs = _loop(tmp_path)
    s = diffs["SHOOTER"]
    for kind in ("jump_pad", "fire_weapon", "missile_hit", "obituary"):
        assert s.tracks[f"event:{kind}"].status is Status.MATCHED, s.tracks[f"event:{kind}"]
    assert diffs["VICTIM"].tracks["event:pain"].status is Status.MATCHED
    assert s.semantic_fidelity == "PASS" and diffs["VICTIM"].semantic_fidelity == "PASS"


def test_local_frame_round_trip_holds_under_the_same_comparison(tmp_path):
    shooter = jumppad_rocket_trace()
    rt = Retarget.local_frame(shooter, to=(-1200.0, 640.0, 200.0), yaw=270.0)
    compiled, back, diffs = _loop(tmp_path, retarget=rt)
    s = diffs["SHOOTER"]
    assert s.tracks["position"].status in (Status.MATCHED, Status.WITHIN_TOLERANCE)
    assert s.tracks["yaw"].status in (Status.MATCHED, Status.WITHIN_TOLERANCE)
    assert s.tracks["projectiles"].status in (Status.MATCHED, Status.WITHIN_TOLERANCE)
    # the reproduction really sits at the target, not at the source
    first = back["SHOOTER"].transform[0].origin
    assert math.dist(first, rt.place(shooter.transform[0].origin)) < 1.0


def test_character_is_cast_separately_from_the_performance(tmp_path):
    compiled, _, _ = _loop(tmp_path)
    a = compiled.scenario.actors["SHOOTER"]
    assert (a.model, a.skin) == ("anarki", "default")
    # the trace never carried an identity, and the cast never touched the motion
    assert "name" not in compiled.traces["SHOOTER"].as_dict()
    from engine.pantheon.roster import PresenterProfile
    m = H.CastMember.coerce("X", PresenterProfile("X", "slash", "default"), H.Team.RED)
    assert (m.model, m.skin) == ("slash", "default")


def test_frame_truth_carries_the_recorded_pose_and_the_sound_intent(tmp_path):
    compiled, _, _ = _loop(tmp_path)
    ft = compiled.frame_truth
    shooter = compiled.traces["SHOOTER"]
    # a frame in the airborne stretch carries the recorded legs animation
    t_air = compiled.t0["SHOOTER"] + (shooter.transform[20].t - shooter.start_ms) / 1000.0
    f = ft.at(t_air)
    assert f.actors["SHOOTER"].legs_anim == 18
    assert f.actors["SHOOTER"].velocity != (0.0, 0.0, 0.0)
    sounds = {e.kind: e.sound for e in ft.events() if e.sound}
    assert sounds["recorded:fire_weapon"] == "weapon.fire.ROCKET"
    assert sounds["recorded:jump_pad"] == "world.jump_pad"
    assert sounds["recorded:missile_hit"] == "impact.ROCKET"
    assert "kill" in sounds


def test_run_reports_timings_without_a_parse_of_anything_real(tmp_path, monkeypatch):
    """`run` is timed per stage; here the demo is the synthetic one itself."""
    compiled, _, _ = _loop(tmp_path)
    lo, hi = compiled.window("SHOOTER")
    res = H.run(compiled.path, {"S": (compiled.clients["SHOOTER"], lo, hi)},
                out_dir=tmp_path / "out", label="self")
    assert res.semantic_fidelity == "PASS", res.diffs["S"].summary()
    assert set(res.timings_ms) >= {"parse", "extract", "compile", "reextract", "compare"}
    assert (tmp_path / "out" / "self.S.diff.json").exists()
