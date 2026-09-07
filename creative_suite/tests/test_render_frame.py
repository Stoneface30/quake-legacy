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


def test_animation_clock_restarts_only_when_the_animation_changes():
    tr = _trace(5, 1000, 25, 6)
    for s in tr["animation"][3:]:
        s["legs"] = 19                          # a change partway through
    t = FrameTruth.from_traces([tr])
    frames = rf.from_frame_truth(t, cast={"CLIENT_5": _Profile("sarge")})
    times = [f.actors[0].anim_time_ms for f in frames]
    assert times[:3] == [0, 25, 50]
    assert times[3] == 0, "a new animation starts its own clock"


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
                   observed, fire=True):
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
                         "origin": list(o), "velocity": list(delta)}
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
    assert m.provenance == "DERIVED"
    assert "TR_LINEAR" in m.method
    assert m.speed == pytest.approx(1000.0)


def test_a_missile_is_not_drawn_after_the_last_snapshot_that_saw_it():
    """It very likely exploded. 'Likely' is not a render input."""
    from engine.pantheon.frame_truth import _evaluate_missile
    seg = {"entity": 211, "weapon": 5, "owner": 5, "valid": True,
           "base": (0.0, 0.0, 0.0), "delta": (1000.0, 0.0, 0.0),
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
