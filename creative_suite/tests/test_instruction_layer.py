"""The analysis layer may not contaminate history.

Every test here is an acceptance requirement from the brief, not a code path.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from engine.pantheon.instruction import (AnalysisBreak, Graphic,  # noqa: E402
                                         InstructionScene)
from engine.pantheon.scenario import Layer, RoundScenario, Team, Weapon  # noqa: E402

A = (100.0, 100.0, 0.0)
B = (500.0, 100.0, 0.0)
CAM = (300.0, 400.0, 0.0)


def _scene(hold=5.0, walk=1.6):
    scn = RoundScenario.clan_arena(map_name="overkill", hostname="T")
    scn.observer(CAM, yaw=90.0, team=Team.BLUE)
    k = scn.actor("KEEL", Team.BLUE).appearance("keel", "bright")
    c = scn.actor("CRASH", Team.RED).appearance("crash", "trainer")
    k.spawn(A, yaw=0.0, t=0.0, weapon=Weapon.RAIL)
    c.spawn(B, yaw=180.0, t=0.0, weapon=Weapon.ROCKET)
    k.stand(until=6.8)
    c.stand(until=6.8)
    s = InstructionScene(scn, duration=7.0)
    s.add_break(AnalysisBreak(at_t=4.0, hold_s=hold, presenter="KEEL",
                              walk_to=(250.0, 300.0, 0.0), face=CAM,
                              graphic=Graphic.SHOOTER_TO_TARGET,
                              graphic_from="KEEL", graphic_to="CRASH",
                              walk_s=walk))
    return s


def test_history_resumes_byte_identical():
    s = _scene()
    built, _ = s.build()
    r = s.verify_restoration(built)
    assert r["all_restored"]
    for row in r["breaks"]:
        for st in row["actors"].values():
            assert st["origin_delta"] == [0.0, 0.0, 0.0]
            assert st["yaw_delta"] == 0.0


def test_the_freeze_costs_edit_time_and_no_historical_time():
    s = _scene(hold=5.0)
    s.build()
    assert s.edit_duration == pytest.approx(7.0 + 5.0)
    # history does not advance across the hold
    assert s.historical_at_edit(4.0) == pytest.approx(4.0)
    assert s.historical_at_edit(8.9) == pytest.approx(4.0)
    assert s.historical_at_edit(10.0) == pytest.approx(5.0)


def test_the_walk_out_is_a_separate_client_not_the_historical_actor():
    s = _scene()
    built, rep = s.build()
    assert built.actors["KEEL"].layer is Layer.HISTORICAL
    assert built.actors["KEEL~ANALYSIS"].layer is Layer.ANALYSIS
    # different client slots: the demo can never be read as one man moving
    assert built.actors["KEEL"].client != built.actors["KEEL~ANALYSIS"].client
    assert rep["breaks"][0]["explainer_layer"] == "ANALYSIS"


def test_the_analysis_body_is_not_in_the_round():
    s = _scene()
    built, _ = s.build()
    # BLUE has exactly one fighter; the explaining body must not be counted
    assert built._alive[Team.BLUE] == 1


def test_the_analysis_body_is_gone_before_history_resumes():
    s = _scene(hold=5.0)
    built, _ = s.build()
    ghost = built.actors["KEEL~ANALYSIS"]
    assert ghost._at(9.0).alive is False       # freeze ends at edit 9.0


def test_the_distance_is_derived_not_typed():
    s = _scene()
    _, rep = s.build()
    fact = rep["breaks"][0]["graphic"]["fact"]
    assert fact["value"] == pytest.approx(400.0)      # |A - B|
    assert "FrameTruth" in fact["derivation"]
    assert fact["layer"] == "ANALYSIS"


def test_the_tactical_line_is_labelled_a_reconstruction():
    s = _scene()
    _, rep = s.build()
    g = rep["breaks"][0]["graphic"]
    assert g["reconstruction"] is True
    assert g["nobody_fired_this"] is True
    assert g["layer"] == "ANALYSIS"


def test_a_hold_too_short_to_explain_in_is_refused():
    with pytest.raises(ValueError, match="no time to explain"):
        AnalysisBreak(at_t=1.0, hold_s=2.0, presenter="KEEL",
                      walk_to=A, face=CAM, walk_s=1.6)


def test_two_breaks_at_the_same_instant_are_refused():
    s = _scene()
    with pytest.raises(ValueError, match="same instant"):
        s.add_break(AnalysisBreak(at_t=4.2, hold_s=5.0, presenter="KEEL",
                                  walk_to=A, face=CAM))


def test_the_source_scenario_is_never_mutated():
    s = _scene()
    before = len(s.historical.actors)
    s.build()
    assert len(s.historical.actors) == before       # no ~ANALYSIS added
    assert "KEEL~ANALYSIS" not in s.historical.actors


# ── the analysis look (PROOF B) ───────────────────────────────────────

def test_the_analysis_body_wears_the_only_tintable_skin():
    # PROOF B: the colour family reaches `bright` and not `sarge/default`.
    # Giving the analysis body the bright skin is therefore what makes the
    # tint land on it alone.
    from engine.pantheon.instruction import ANALYSIS_SKIN
    s = _scene()
    built, rep = s.build()
    ghost = built.actors["KEEL~ANALYSIS"]
    assert ghost.skin == ANALYSIS_SKIN
    assert ghost.model == built.actors["KEEL"].model      # same character
    assert rep["breaks"][0]["explainer_appearance"]["skin"] == ANALYSIS_SKIN


def test_the_historical_actor_keeps_the_skin_the_demo_authored():
    s = _scene()
    built, _ = s.build()
    assert built.actors["CRASH"].skin == "trainer"        # untouched
    assert built.actors["KEEL"].skin == "bright"          # as authored


def test_the_analysis_tint_is_written_in_the_measured_format():
    from engine.pantheon.color_format import analysis_visual_cvars
    team = analysis_visual_cvars(same_team_as_pov=True)
    enemy = analysis_visual_cvars(same_team_as_pov=False)
    # 0xRRGGBB, the form PROOF 0 and PROOF B both measured
    assert all(v.startswith('"0x') for v in team.values())
    # the engine classifies by team relation, so only one half is written
    assert set(team) & set(enemy) == set()
    assert len(team) == 3


def test_a_freeze_between_two_keys_holds_the_pose_flat():
    # Proof C: with no keyframe at the freeze instant, the surrounding keys
    # had their interval stretched by the hold and the yaw snap landed inside
    # the freeze. Four frozen actors turned their heads.
    scn = RoundScenario.clan_arena(map_name="overkill", hostname="T")
    scn.observer(CAM, yaw=90.0, team=Team.BLUE)
    k = scn.actor("KEEL", Team.BLUE).appearance("keel", "bright")
    k.spawn(A, yaw=0.0, t=0.0, weapon=Weapon.RAIL)
    k.stand(until=3.0)
    k.look_at_point((100.0, 900.0, 0.0), t=6.0)   # yaw 90 at t=6: snaps at 4.5
    k.stand(until=7.0)
    s = InstructionScene(scn, duration=7.0)
    s.add_break(AnalysisBreak(at_t=4.0, hold_s=5.0, presenter="KEEL",
                              walk_to=(250.0, 300.0, 0.0), face=CAM))
    built, _ = s.build()
    r = s.verify_restoration(built)
    assert r["all_restored"], r
    # and nothing moves DURING the hold either
    keel = built.actors["KEEL"]
    yaws = {round(keel._at(t).yaw, 6) for t in (4.0, 5.0, 6.5, 8.0, 9.0)}
    assert len(yaws) == 1


def test_a_presenter_can_differ_from_every_historical_actor():
    from engine.pantheon.instruction import Mode
    from engine.pantheon.roster import CAST
    scn = RoundScenario.clan_arena(map_name="overkill", hostname="T")
    scn.observer(CAM, yaw=90.0, team=Team.BLUE)
    k = scn.actor("KEEL", Team.BLUE).appearance("keel", "bright")
    k.spawn(A, yaw=0.0, t=0.0, weapon=Weapon.RAIL); k.stand(until=6.8)
    s = InstructionScene(scn, duration=7.0)
    s.add_break(AnalysisBreak(at_t=4.0, hold_s=5.0, mode=Mode.PRESENTER,
                              profile=CAST["GUIDE"], enter_from=(0.0, 0.0, 0.0),
                              walk_to=(250.0, 300.0, 0.0), face=CAM))
    built, rep = s.build()
    ghost = built.actors["GUIDE~PRESENTER"]
    assert ghost.layer is Layer.PRESENTER
    assert (ghost.model, ghost.skin) == ("crash", "trainer")
    assert ghost.client != built.actors["KEEL"].client
    assert built._alive[Team.BLUE] == 1 and built._alive.get(Team.RED, 0) == 0
    assert s.verify_restoration(built)["all_restored"]
    assert rep["breaks"][0]["explainer_layer"] == "PRESENTER"


def test_a_presenter_profile_must_resolve_to_an_installed_skin():
    from engine.pantheon.roster import PresenterProfile
    with pytest.raises(KeyError, match="has no skin"):
        PresenterProfile("X", "crash", "not_a_skin").resolve()
    with pytest.raises(KeyError, match="no player model"):
        PresenterProfile("X", "mascot", "default").resolve()


def test_the_camera_returns_to_the_exact_pov_before_history_resumes():
    scn = RoundScenario.clan_arena(map_name="overkill", hostname="T")
    scn.observer(CAM, yaw=90.0, team=Team.BLUE)
    k = scn.actor("KEEL", Team.BLUE).appearance("keel", "bright")
    k.spawn(A, yaw=0.0, t=0.0, weapon=Weapon.RAIL); k.stand(until=6.8)
    s = InstructionScene(scn, duration=7.0)
    s.add_break(AnalysisBreak(at_t=4.0, hold_s=5.0, presenter="KEEL",
                              walk_to=(250.0, 300.0, 0.0), face=CAM,
                              orbit=[(600.0, 600.0, 0.0), (0.0, 600.0, 0.0)],
                              orbit_look_at=A))
    built, _ = s.build()
    before, after = built.camera_at(4.0), built.camera_at(9.0)
    assert before.origin == after.origin and before.yaw == after.yaw
    mid = built.camera_at(6.5)
    assert mid.origin != before.origin        # it did move in edit time
    assert s.historical_at_edit(6.5) == pytest.approx(4.0)   # history did not


# ── a presenter enters by performing a real recording ──────────────────

def _run_in_template():
    """A hand-built RUN -> STOP -> TURN with the extractor's shape."""
    from engine.pantheon.performance import (AimSample, AnimSample, PerformanceTrace,
                                             TransformSample)
    tr = PerformanceTrace("t", "overkill", "CA", 1, 0, 0)
    t = 0
    x = 0.0
    yaw = 0.0
    for i in range(140):                       # 3.5s at 25ms
        if i < 52:            # run
            v, legs = 320.0, 15
        elif i < 60:          # decelerate
            v, legs = 320.0 * (60 - i) / 8, 15
        else:                 # stopped, turning 90 degrees over 1s
            v, legs = 0.0, 22
            if i < 100:
                yaw += 2.25
        x += v * 0.025
        tr.transform.append(TransformSample(t, (x, 0.0, 24.0), (v, 0.0, 0.0), v, False, 1022))
        tr.aim.append(AimSample(t, yaw % 360, 0.0, 0.0, 0.0))
        tr.animation.append(AnimSample(t, legs, 11, False, False))
        t += 25
    tr.end_ms = t - 25
    return tr


def test_presenter_entrance_is_placed_so_the_recorded_stop_lands_on_the_mark():
    from engine.pantheon.instruction import place_entrance, _apply
    tr = _run_in_template()
    pl = place_entrance(tr, stop_at=(500.0, 500.0, 24.0), face=(500.0, 900.0, 24.0))
    assert pl["mode"] == "LOCAL_FRAME"
    # the recorded stop sample, moved into the frame, IS the mark
    stop = next(s for s in tr.transform if s.speed < 30)
    w = _apply(stop.origin, pl["offset"], pl["yaw_offset"])
    assert abs(w[0] - 500.0) < 1e-6 and abs(w[1] - 500.0) < 1e-6
    # and the run started ~500 units away, where the recording says
    assert 400 < ((pl["start_world"][0] - 500) ** 2 + (pl["start_world"][1] - 500) ** 2) ** 0.5 < 700
    assert pl["stop_rel_s"] == pytest.approx(1.5, abs=0.05)


def test_entrance_faces_the_camera_at_the_end_of_the_recorded_turn():
    from engine.pantheon.instruction import place_entrance
    tr = _run_in_template()
    pl = place_entrance(tr, stop_at=(500.0, 500.0, 24.0), face=(500.0, 900.0, 24.0))
    final = (tr.aim[-1].yaw + pl["yaw_offset"]) % 360
    assert final == pytest.approx(90.0, abs=1e-6)          # +y is toward the camera


def test_a_performed_entrance_never_uses_move_to():
    from engine.pantheon.instruction import AnalysisBreak, InstructionScene, Mode
    from engine.pantheon.roster import CAST
    tr = _run_in_template()
    scn = RoundScenario.clan_arena(map_name="overkill", hostname="T")
    scn.observer(CAM, yaw=90.0, team=Team.BLUE)
    k = scn.actor("KEEL", Team.RED).appearance("keel", "bright")
    k.spawn(A, yaw=0.0, t=0.0, weapon=Weapon.RAIL); k.stand(until=9.0)
    s = InstructionScene(scn, duration=9.0)
    s.add_break(AnalysisBreak(at_t=4.0, hold_s=7.0, mode=Mode.PRESENTER,
                              profile=CAST["GUIDE"], enter_from=(0.0, 0.0, 24.0),
                              walk_to=(250.0, 300.0, 24.0), face=CAM,
                              entrance=tr, walk_s=1.5))
    built, rep = s.build()
    pres = built.actors["GUIDE~PRESENTER"]
    assert rep["breaks"][0]["entrance"] == "REAL_PERFORMANCE"
    from engine.pantheon.scenario import Stance
    # every moving key is a recorded sample; the only authored keys are the
    # standing ones (gesture, hold, despawn) -- nothing here ran a lerp
    assert all(k.recorded for k in pres._keys if k.stance is Stance.RUN)
    assert not any((not k.recorded) and k.stance is Stance.RUN for k in pres._keys)
    assert s.verify_restoration(built)["all_restored"]
    assert built._alive[Team.RED] == 1 and built._alive.get(Team.BLUE, 0) == 0


def test_placement_validity_rejects_a_path_off_walked_ground():
    from engine.pantheon.instruction import place_entrance, validate_placement
    from engine.pantheon.navigation import NavigationTruth, Route
    tr = _run_in_template()
    pl = place_entrance(tr, stop_at=(500.0, 500.0, 24.0), face=(500.0, 900.0, 24.0))
    # walked ground that covers the whole retargeted run
    pts = tuple((500.0 - i * 10.0, 500.0, 24.0) for i in range(60))
    good = NavigationTruth("overkill", [Route(pts, 24.0)])
    assert validate_placement(tr, pl, good)["verdict"] == "VALID"
    # the same ground one floor down: every sample is off the floor
    bad = NavigationTruth("overkill", [Route(tuple((x, y, z - 300) for x, y, z in pts), -276.0)])
    assert validate_placement(tr, pl, bad)["verdict"] == "INVALID"


# ── compose_three: the projection is blind to walls; the tracer is not ────
class _PillarTracer:
    """A pillar: the wall segment x = 100, |y| <= 60. Any segment crossing it is blocked."""

    def line_blocked(self, a, b):
        if (a[0] - 100.0) * (b[0] - 100.0) >= 0:
            return False
        t = (100.0 - a[0]) / (b[0] - a[0])
        return abs(a[1] + t * (b[1] - a[1])) <= 60.0


def test_compose_three_rejects_settles_that_cannot_see_the_cast(monkeypatch):
    """02B's first render stared into a pillar: the settle was open space with
    a clear dolly, but geometry stood between it and all three subjects.
    Settles whose sight-line to the presenter crosses the pillar must be
    rejected as `occluded`, and the winner must see all three."""
    from creative_suite.engine import camera_paths as cp
    from engine.pantheon import instruction as ins
    pillar = _PillarTracer()
    monkeypatch.setattr(cp, "bsp_tracer", lambda *_a, **_k: pillar)
    P, K, V = (0.0, 0.0, 0.0), (-150.0, 220.0, 0.0), (-150.0, -220.0, 0.0)
    best = ins.compose_three(presenter=P, shooter=K, target=V, map_name="x",
                             distance=(150.0, 260.0), height=(32.0, 120.0),
                             start_pos=(200.0, 200.0, 0.0))
    assert best["rejections"]["occluded"] > 0
    assert ins.sightlines_clear(pillar, best["camera"], (P, K, V))
    assert "visible from the settle" in best["collision"]
    # the pillar hides her from straight ahead: the winner is off that axis
    assert not (abs(best["camera"][1]) <= 60.0 and best["camera"][0] > 100.0)


def test_sightlines_check_eye_chest_and_feet():
    class Low:                                            # a waist-high parapet
        def line_blocked(self, a, b):
            return b[2] < 10.0                            # feet hidden, eye visible
    assert not __import__("engine.pantheon.instruction", fromlist=["x"]).sightlines_clear(
        Low(), (100.0, 0.0, 40.0), ((0.0, 0.0, 0.0),))
