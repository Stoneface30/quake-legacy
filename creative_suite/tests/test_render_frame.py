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
