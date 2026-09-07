"""RenderFrame is the renderer's only input, and it must stay honest.

These tests guard the properties that make it safe to hand to a rasteriser:
recorded provenance survives, nothing is interpolated, an unobserved actor
stays absent, and identity is joined from the cast rather than invented.
"""
import json

import pytest

from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon import render_frame as rf


class _Profile:
    def __init__(self, model, skin="default"):
        self.model = model
        self.skin = skin


def _trace(client, start, step, n, *, x0=0.0, yaw=0.0, legs=15, torso=10,
           map_name="campgrounds"):
    return {
        "demo_hash": "deadbeef", "map": map_name, "gametype": "CA",
        "client": client, "start_ms": start, "end_ms": start + step * (n - 1),
        "transform": [{"t": start + i * step,
                       "origin": [x0 + i, 0.0, 100.0],
                       "velocity": [1.0, 0.0, 0.0], "speed": 1.0,
                       "airborne": False, "ground_entity": 1022}
                      for i in range(n)],
        "aim": [{"t": start + i * step, "yaw": yaw + i, "pitch": -5.0,
                 "yaw_rate": 0.0, "pitch_rate": 0.0} for i in range(n)],
        "animation": [{"t": start + i * step, "legs": legs, "torso": torso,
                       "legs_toggle": False, "torso_toggle": False}
                      for i in range(n)],
        "weapon": [], "projectiles": [], "events": [], "pov": False,
    }


def test_from_traces_keeps_the_demo_clock_and_recorded_provenance():
    t = FrameTruth.from_traces([_trace(5, 1197225, 25, 8)])
    assert t.provenance == "RECORDED_TRACE"
    assert t.snapshot_hz == 40
    # NOT re-based to a synthetic origin -- this is the demo's own serverTime.
    assert t.frames[0].server_time_ms == 1197225
    assert t.frames[-1].server_time_ms == 1197225 + 25 * 7


def test_an_actor_the_demo_did_not_observe_is_absent_not_guessed():
    """HL-6 at the renderer boundary."""
    a = _trace(5, 1000, 25, 8)                 # covers 1000..1175
    b = _trace(7, 1100, 25, 4)                 # only 1100..1175
    t = FrameTruth.from_traces([a, b], names={5: "A", 7: "B"})

    early = t.at_server_time(1000)
    assert "A" in early.actors
    assert "B" not in early.actors, "B was never observed at 1000"

    later = t.at_server_time(1150)
    assert {"A", "B"} <= set(later.actors)


def test_resampling_picks_an_observed_sample_and_never_blends():
    t = FrameTruth.from_traces([_trace(5, 1000, 25, 8)])
    cast = {"CLIENT_5": _Profile("sarge")}
    # 1010 falls between the 1000 and 1025 samples.
    frames = rf.from_frame_truth(t, cast=cast, times_ms=[1010])
    assert len(frames) == 1
    # It carries the sample's own time, not the requested one.
    assert frames[0].server_time_ms == 1000
    observed = {s["t"] for s in _trace(5, 1000, 25, 8)["transform"]}
    assert frames[0].server_time_ms in observed


def test_the_camera_owner_is_not_drawn_and_the_camera_is_his_eyes():
    t = FrameTruth.from_traces([_trace(5, 1000, 25, 4), _trace(7, 1000, 25, 4)],
                               names={5: "SHOOTER", 7: "VICTIM"})
    cast = {"SHOOTER": _Profile("sarge"), "VICTIM": _Profile("visor")}
    frames = rf.from_frame_truth(t, cast=cast, camera_owner="SHOOTER")

    assert frames[0].camera.source == "RECORDED_POV"
    assert frames[0].camera.origin[2] == pytest.approx(100.0 + 26.0)
    drawn = {a.actor_id for a in frames[0].actors}
    assert drawn == {"VICTIM"}, "you do not see your own body"


def test_an_uncast_actor_is_not_given_an_identity_by_the_renderer():
    t = FrameTruth.from_traces([_trace(5, 1000, 25, 4), _trace(7, 1000, 25, 4)],
                               names={5: "A", 7: "B"})
    frames = rf.from_frame_truth(t, cast={"A": _Profile("keel")})
    assert {a.actor_id for a in frames[0].actors} == {"A"}


def test_a_body_yaws_but_does_not_pitch():
    """Pitch belongs to the view. On the legs it tips the character over."""
    t = FrameTruth.from_traces([_trace(5, 1000, 25, 4, yaw=90.0)])
    frames = rf.from_frame_truth(t, cast={"CLIENT_5": _Profile("sarge")})
    a = frames[0].actors[0]
    assert a.angles[1] == pytest.approx(90.0)
    assert a.angles[0] == 0.0 and a.angles[2] == 0.0


def test_legs_and_torso_run_independent_animation_clocks():
    """Sharing one clock made a torso change restart the legs mid-stride."""
    tr = _trace(5, 1000, 25, 6)
    for smp in tr["animation"][3:]:
        smp["torso"] = 7                        # TORSO_ATTACK partway through
    t = FrameTruth.from_traces([tr])
    frames = rf.from_frame_truth(t, cast={"CLIENT_5": _Profile("sarge")})
    legs = [f.actors[0].legs_anim_ms for f in frames]
    torso = [f.actors[0].torso_anim_ms for f in frames]
    assert legs == [0, 25, 50, 75, 100, 125], "the legs never restarted"
    assert torso[:3] == [0, 25, 50]
    assert torso[3] == 0, "the torso started its own animation"


def test_the_toggle_bit_restarts_an_animation_with_the_same_number():
    """Firing twice from TORSO_ATTACK keeps the number and flips the toggle.
    Watching the number alone never replays the second shot."""
    tr = _trace(5, 1000, 25, 6)
    for smp in tr["animation"]:
        smp["torso"] = 7
    for smp in tr["animation"][3:]:
        smp["torso_toggle"] = True              # same number, restart
    t = FrameTruth.from_traces([tr])
    frames = rf.from_frame_truth(t, cast={"CLIENT_5": _Profile("sarge")})
    torso = [f.actors[0].torso_anim_ms for f in frames]
    assert torso[:3] == [0, 25, 50]
    assert torso[3] == 0, "the toggle bit is a restart"


def test_shot_script_round_trips_the_values_the_host_will_read(tmp_path):
    t = FrameTruth.from_traces([_trace(5, 1000, 25, 4), _trace(7, 1000, 25, 4)],
                               names={5: "SHOOTER", 7: "VICTIM"})
    cast = {"SHOOTER": _Profile("sarge"), "VICTIM": _Profile("visor")}
    frames = rf.from_frame_truth(t, cast=cast, camera_owner="SHOOTER")
    path = rf.save_shot_script(frames, tmp_path / "s.shot")
    text = path.read_text()

    assert "map campgrounds" in text
    assert "provenance RECORDED_TRACE" in text
    assert "player visor default" in text
    # The camera-owner's model is never declared: he is not drawn.
    assert "player sarge" not in text

    frame_lines = [l for l in text.splitlines() if l.startswith("frame ")]
    actor_lines = [l for l in text.splitlines() if l.startswith("actor ")]
    assert len(frame_lines) == len(frames)
    assert len(actor_lines) == len(frames)
    # Every actor line references a declared player index.
    assert all(int(l.split()[1]) == 0 for l in actor_lines)


# ── projectiles ────────────────────────────────────────────────────────────
#
# The recorded field is pos.trBase, not a position, and pos.trTime is not in
# the demo at all. Everything below guards the consequence: a missile is only
# renderable when its launch time is recoverable AND the derivation predicts
# the observations we did get.

def _missile_trace(client, *, entity, weapon, base, delta, launch_ms,
                   observed, fire=True, tr_time=None, tr_type=None):
    """A trace whose missile samples repeat trBase, exactly as demos do."""
    return {
        "demo_hash": "deadbeef", "map": "campgrounds", "gametype": "CA",
        "client": client, "start_ms": launch_ms, "end_ms": observed[-1][0],
        "transform": [{"t": launch_ms, "origin": [0.0, 0.0, 0.0],
                       "velocity": [0.0, 0.0, 0.0], "speed": 0.0,
                       "airborne": False, "ground_entity": 1022}],
        "aim": [{"t": launch_ms, "yaw": 0.0, "pitch": 0.0,
                 "yaw_rate": 0.0, "pitch_rate": 0.0}],
        "animation": [{"t": launch_ms, "legs": 15, "torso": 10,
                       "legs_toggle": False, "torso_toggle": False}],
        "weapon": [{"t": launch_ms, "weapon": weapon}],
        "projectiles": [{"t": t, "entity": entity, "weapon": weapon,
                         "origin": list(o), "velocity": list(delta),
                         "tr_time": tr_time, "tr_type": tr_type}
                        for t, o in observed],
        "events": ([{"t": launch_ms, "kind": "fire_weapon", "weapon": weapon,
                     "position": list(base), "other_client": None, "parm": None}]
                   if fire else []),
        "pov": False,
    }


def test_a_missile_with_no_fire_event_is_not_renderable():
    """Without EV_FIRE_WEAPON there is no trTime, so there is no position."""
    from engine.pantheon.frame_truth import _missile_segments
    tr = _missile_trace(5, entity=200, weapon=4, base=(0, 0, 0),
                        delta=(100, 0, 0), launch_ms=1000,
                        observed=[(1000, (0, 0, 0)), (1025, (0, 0, 0))],
                        fire=False)
    seg = _missile_segments(tr)[0]
    assert seg["launch_ms"] is None
    assert not seg["valid"]


def test_a_derivation_that_contradicts_its_observations_is_refused():
    """Entity slots are reused and a stale trDelta can survive delta
    compression. The corpus contains one such segment, off by 1.9 seconds."""
    from engine.pantheon.frame_truth import _missile_segments
    # second observed base is nowhere near base + delta*dt
    tr = _missile_trace(5, entity=206, weapon=5, base=(0, 0, 0),
                        delta=(1000, 0, 0), launch_ms=1000,
                        observed=[(1000, (0, 0, 0)), (1025, (0, 0, 0)),
                                  (1500, (9999, 0, 0))])
    seg = _missile_segments(tr)[0]
    assert seg["launch_ms"] == 1000
    assert seg["residual_ms"] > 100
    assert not seg["valid"], "a contradicted trajectory must not be drawn"


def test_a_consistent_missile_is_evaluated_linearly_from_its_launch():
    from engine.pantheon.frame_truth import FrameTruth
    tr = _missile_trace(5, entity=211, weapon=5, base=(0.0, 0.0, 0.0),
                        delta=(1000.0, 0.0, 0.0), launch_ms=1000,
                        observed=[(1000, (0, 0, 0)), (1025, (0, 0, 0)),
                                  (1500, (500.0, 0.0, 0.0))])
    t = FrameTruth.from_traces([tr])
    seg_frames = [f for f in t.frames if f.projectiles]
    assert seg_frames, "a valid missile should appear"
    m = seg_frames[0].projectiles[0]
    # No trTime in this fixture, so the launch was inferred from the fire
    # event. That inference was measured wrong by a systematic +50 ms on real
    # data, so anything built on it must say so.
    assert m.provenance == "DERIVED_PROVISIONAL"
    # No trType either, so the evaluator says so rather than implying it knew.
    assert "BG_EvaluateTrajectory" in m.method
    assert "PROVISIONAL_FIRE_EVENT" in m.method
    assert m.speed == pytest.approx(1000.0)


def test_a_missile_is_not_drawn_after_the_last_snapshot_that_saw_it():
    """It very likely exploded. 'Likely' is not a render input."""
    from engine.pantheon.frame_truth import _evaluate_missile
    seg = {"entity": 211, "weapon": 5, "owner": 5, "valid": True,
           "base": (0.0, 0.0, 0.0), "delta": (1000.0, 0.0, 0.0),
           "tr_type": 2, "launch_source": "RECORDED_TRTIME",
           "launch_ms": 1000, "first_seen_ms": 1000, "last_seen_ms": 1500,
           "residual_ms": 0.0}
    assert _evaluate_missile(seg, 1200) is not None
    assert _evaluate_missile(seg, 1501) is None, "past the last observation"
    assert _evaluate_missile(seg, 999) is None, "before it was launched"


def test_a_missile_points_along_its_own_velocity():
    from engine.pantheon import render_frame as rf
    assert rf.vector_to_angles((1.0, 0.0, 0.0))[1] == pytest.approx(0.0)
    assert rf.vector_to_angles((0.0, 1.0, 0.0))[1] == pytest.approx(90.0)
    # straight up is negative pitch in Quake
    assert rf.vector_to_angles((0.0, 0.0, 1.0))[0] == pytest.approx(-90.0)


def test_a_weapon_with_no_missile_asset_is_not_given_one():
    from engine.pantheon import render_frame as rf
    assert rf.weapon_assets(7)["missile"] is None       # railgun is hitscan
    assert rf.weapon_assets(5)["missile"].endswith("rocket.md3")
    assert rf.weapon_assets(999)["missile"] is None     # unknown, not guessed


def test_recorded_trTime_is_used_and_is_not_provisional():
    """pos.trTime is in the demo (entityState field 0). Using it is the whole
    difference between a measurement and a guess."""
    from engine.pantheon.frame_truth import FrameTruth
    tr = _missile_trace(5, entity=211, weapon=5, base=(0.0, 0.0, 0.0),
                        delta=(1000.0, 0.0, 0.0), launch_ms=1000,
                        observed=[(1050, (0, 0, 0))],
                        fire=False, tr_time=1000, tr_type=2)
    t = FrameTruth.from_traces([tr])
    m = [f for f in t.frames if f.projectiles][0].projectiles[0]
    assert m.provenance == "DERIVED"           # not PROVISIONAL
    assert "trType=2" in m.method


def test_two_trTimes_in_one_entity_slot_are_two_missiles():
    """Slot reuse. Grouping by trBase merged them into one impossible flight."""
    from engine.pantheon.frame_truth import _missile_segments
    tr = _missile_trace(5, entity=206, weapon=5, base=(0.0, 0.0, 0.0),
                        delta=(1000.0, 0.0, 0.0), launch_ms=1000,
                        observed=[(1000, (0, 0, 0))], tr_time=1000, tr_type=2)
    tr["projectiles"].append({"t": 2000, "entity": 206, "weapon": 5,
                              "origin": [500.0, 0.0, 0.0],
                              "velocity": [-800.0, 0.0, 0.0],
                              "tr_time": 1950, "tr_type": 2})
    segs = _missile_segments(tr)
    assert len(segs) == 2, "two trTimes means two missiles"
    assert {s["launch_ms"] for s in segs} == {1000, 1950}


def test_a_grenade_falls_because_its_trType_says_so():
    """trType 5 is TR_GRAVITY. Evaluating a grenade linearly flies it through
    the ceiling."""
    from engine.pantheon.frame_truth import _trajectory_at
    lin = _trajectory_at((0, 0, 0), (0, 0, 100), 0, 2, 1000)
    grav = _trajectory_at((0, 0, 0), (0, 0, 100), 0, 5, 1000)
    assert lin[2] == pytest.approx(100.0)
    assert grav[2] == pytest.approx(100.0 - 0.5 * 800.0)
    assert grav[2] < lin[2]


# ── camera evaluation ──────────────────────────────────────────────────────

def test_yaw_interpolation_takes_the_short_way_round():
    """359 -> 1 is two degrees, not 358."""
    assert rf._short_arc(359.0, 1.0) == pytest.approx(2.0)
    assert rf._short_arc(1.0, 359.0) == pytest.approx(-2.0)


def test_faithful_intent_interpolates_between_observed_samples():
    t = FrameTruth.from_traces([_trace(5, 1000, 25, 6, yaw=0.0)])
    cast = {"CLIENT_5": _Profile("sarge")}
    exact = rf.from_frame_truth(t, cast=cast, camera_owner="CLIENT_5",
                                times_ms=[1010], intent=rf.SAMPLE_EXACT)
    faith = rf.from_frame_truth(t, cast=cast, camera_owner="CLIENT_5",
                                times_ms=[1010], intent=rf.POV_FAITHFUL)
    assert exact[0].camera_provenance == "RECORDED_SAMPLE"
    assert faith[0].camera_provenance == "DERIVED_INTERPOLATED"
    # the source yaw advances 1 deg per 25 ms sample; 1010 is 40% between
    assert faith[0].camera.angles[1] == pytest.approx(0.4, abs=1e-6)
    # SOURCE time stays the sample's; EDIT time is the output instant
    assert faith[0].server_time_ms == 1000
    assert faith[0].edit_time_ms == 1010


def test_interpolation_refuses_to_cross_an_observation_gap():
    tr = _trace(5, 1000, 25, 4)
    # blow a hole in the middle: next observation is 500 ms later
    for track in ("transform", "aim", "animation"):
        tr[track].append(dict(tr[track][-1], t=1575))
    tr["end_ms"] = 1575
    t = FrameTruth.from_traces([tr])
    ev = rf._evaluate_actor(t, "CLIENT_5", 1200, rf.POV_FAITHFUL)
    assert ev[3] == "RECORDED_SAMPLE", "a gap is held, never bridged"


def test_interpolation_refuses_to_cross_a_teleport():
    from engine.pantheon.frame_truth import SemanticEvent
    t = FrameTruth.from_traces([_trace(5, 1000, 25, 4)])
    t.frames[1].events.append(SemanticEvent(t=0.0, server_time_ms=1025,
                                            kind="recorded:teleport_in"))
    ev = rf._evaluate_actor(t, "CLIENT_5", 1010, rf.POV_FAITHFUL)
    assert ev[3] == "RECORDED_SAMPLE", "a teleport is a discontinuity"


def test_interpolation_preserves_a_genuine_flick():
    """A real 800 deg/s flick must survive; only impossible jumps are cut."""
    tr = _trace(5, 1000, 25, 3)
    tr["aim"][1]["yaw"] = 20.0        # 20 deg in 25 ms = 800 deg/s
    tr["aim"][2]["yaw"] = 20.0
    t = FrameTruth.from_traces([tr])
    ev = rf._evaluate_actor(t, "CLIENT_5", 1012, rf.POV_FAITHFUL)
    assert ev[3] == "DERIVED_INTERPOLATED"
    assert 5.0 < ev[1] < 15.0, "the flick is carried through, not flattened"


# ── POV attribution ────────────────────────────────────────────────────────

def test_the_pov_client_is_a_function_of_time_not_a_constant():
    """In Clan Arena a dead player follows his team-mates, so the
    playerstate's clientNum changes mid-demo. Treating it as constant made
    the recorder's own full-precision playerstate get ignored for the very
    interval he was playing, and every actor fell back to server-snapped
    entity angles."""
    from engine.pantheon.performance import pov_spans, pov_rows, recorder_client
    out = {"recorder_track": [
        {"t": 1000, "client": 7}, {"t": 1025, "client": 7},
        {"t": 1050, "client": 1}, {"t": 1075, "client": 1},
        {"t": 1100, "client": 3},
    ]}
    assert recorder_client(out) == 7          # the first, and not the whole truth
    assert pov_spans(out) == [(7, 1000, 1025), (1, 1050, 1075), (3, 1100, 1100)]
    assert [r["t"] for r in pov_rows(out, 1, 0, 9999)] == [1050, 1075]
    assert pov_rows(out, 5, 0, 9999) == [], "a client who never held the POV"


# ── stateful presentation, deterministically replayed ──────────────────────
#
# CG_SwingAngles carries per-entity state between frames. That is NOT a
# obstacle to determinism -- same initial state plus same inputs in the same
# order gives the same result. It only costs random access, and a checkpoint
# plus replay buys that back.

def _swing_truth():
    tr = _trace(5, 1000, 25, 40, yaw=0.0)
    for i, smp in enumerate(tr["aim"]):
        smp["yaw"] = 0.0 if i < 10 else 90.0     # a hard 90 degree turn
    for smp in tr["animation"]:
        smp["legs"] = 15                          # LEGS_RUN: "always center"
    return FrameTruth.from_traces([tr])


def test_swing_lags_the_view_instead_of_snapping_to_it():
    t = _swing_truth()
    ev = rf.PresentationEvaluator(t)
    before = ev.pose_at("CLIENT_5", 1240)
    during = ev.pose_at("CLIENT_5", 1260)
    later = ev.pose_at("CLIENT_5", 1500)
    assert before[0] == pytest.approx(0.0, abs=1e-6)
    # mid-turn the legs are somewhere between: they have not snapped
    assert 0.0 < during[0] < 90.0, "the legs swing, they do not teleport"
    assert later[0] == pytest.approx(90.0, abs=1.0), "and they get there"


def test_seeking_agrees_with_sequential_evaluation():
    """Frame N evaluated after a seek must equal frame N evaluated in order."""
    t = _swing_truth()
    seq = rf.PresentationEvaluator(t)
    ordered = [seq.pose_at("CLIENT_5", ms) for ms in range(1000, 1900, 33)]

    jump = rf.PresentationEvaluator(t)
    picked = list(range(1000, 1900, 33))
    # deliberately out of order: late, early, late again
    a = jump.pose_at("CLIENT_5", picked[-1])
    jump.pose_at("CLIENT_5", picked[3])
    b = jump.pose_at("CLIENT_5", picked[-1])
    assert a == b, "evaluating the same time twice must agree"
    assert a == pytest.approx(ordered[-1]), "and must match sequential replay"


def test_a_direct_seek_matches_the_sequential_answer_at_every_frame():
    t = _swing_truth()
    seq = rf.PresentationEvaluator(t)
    ordered = {ms: seq.pose_at("CLIENT_5", ms) for ms in range(1000, 1900, 33)}
    for ms in sorted(ordered, reverse=True):       # reverse order on purpose
        fresh = rf.PresentationEvaluator(t)
        assert fresh.pose_at("CLIENT_5", ms) == pytest.approx(ordered[ms])


def test_checkpoints_are_bounded_not_one_per_frame():
    t = _swing_truth()
    ev = rf.PresentationEvaluator(t)
    ev.pose_at("CLIENT_5", 1900)
    marks = ev._checkpoints["CLIENT_5"]
    assert len(marks) <= 4, "bounded checkpoints, not a per-frame cache"


def test_short_arc_is_used_for_the_swing_destination():
    """359 -> 1 must swing 2 degrees forward, not 358 backward."""
    ang, swinging = rf._swing_angles(1.0, 40.0, 90.0, 0.3, 359.0, True, 25.0)
    assert ang > 359.0 or ang < 10.0, "moved the short way"
    assert rf._angle_subtract(1.0, 359.0) == pytest.approx(2.0)
