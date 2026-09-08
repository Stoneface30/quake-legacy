"""ANIMATION_PHASE, checked against the ENGINE'S OWN CG_RunLerpFrame.

The oracle harness (engine/pantheon_renderer/oracle/oracle_anim.exe) compiles
CG_RunLerpFrame, CG_SetAnimFrame, CG_SetLerpFrameAnimation and
CG_ClearLerpFrame verbatim out of the WolfcamQL 11.3 tree and runs them over a
declared schedule. PANTHEON is fed the identical schedule and every field that
reaches the renderer is diffed.

This is what retired the closed form. `frame = time / frameLerp` agrees with
the engine only when the render schedule happens to match the animation's own
frame rate; the engine advances one frame per RENDER CALL and clamps, which is
history-dependent and cannot be written as a function of time alone.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from engine.pantheon import render_frame as rf

ORACLE_DIR = Path("G:/QUAKE_LEGACY/engine/pantheon_renderer/oracle")
ORACLE_EXE = ORACLE_DIR / "oracle_anim.exe"

# float32 in the engine, float64 here; tight enough that a frame-time error
# of even one millisecond shows up.
BACKLERP_TOL = 2e-6

# A stand-in animation set with one entry per shape we care about.
#   idx 0  ordinary looping run
#   idx 1  non-looping one-shot (loop_frames 0) -- sticks at the end
#   idx 2  reversed
#   idx 3  flipflop
#   idx 4  a slow animation (long frameLerp) with a long initialLerp
#   idx 5  partial loop (loops only the tail frames)
ANIMS = [
    rf.Animation(0, 10, 10, 100, 100, False, False),
    rf.Animation(100, 8, 0, 50, 50, False, False),
    rf.Animation(200, 6, 6, 80, 80, True, False),
    rf.Animation(300, 5, 5, 60, 60, False, True),
    rf.Animation(400, 4, 4, 250, 400, False, False),
    rf.Animation(500, 12, 4, 40, 40, False, False),
]


def _anim_lines():
    return "anims %d\n" % len(ANIMS) + "".join(
        "%d %d %d %d %d %d %d\n" % (a.first_frame, a.num_frames,
                                    a.loop_frames, a.frame_lerp,
                                    a.initial_lerp, int(a.reversed_),
                                    int(a.flipflop))
        for a in ANIMS)


def _oracle(script):
    """script: list of ('clear'|'step', anim, speed_scale, time)."""
    if not ORACLE_EXE.exists():
        pytest.skip("animation oracle not built (engine source tree absent)")
    lines = [_anim_lines()]
    for kind, anim, scale, t in script:
        if kind == "clear":
            lines.append("clear %d %d\n" % (anim, t))
        else:
            lines.append("step %d %f %d\n" % (anim, scale, t))
    r = subprocess.run([str(ORACLE_EXE)], input="".join(lines),
                       capture_output=True, text=True, cwd=str(ORACLE_DIR))
    assert r.returncode == 0, r.stderr
    out = []
    for line in r.stdout.strip().splitlines():
        f = line.split()
        out.append({
            "animation_number": int(f[0]), "animation_time": int(f[1]),
            "frame_time": int(f[2]), "old_frame_time": int(f[3]),
            "old_frame": int(f[4]), "frame": int(f[5]),
            "backlerp": float(f[6]),
        })
    return out


def _pantheon(script):
    lf = rf._LerpFrame()
    out = []
    for kind, anim, scale, t in script:
        if kind == "clear":
            rf.clear_lerp_frame(ANIMS, lf, anim, t)
            continue
        rf.run_lerp_frame(ANIMS, lf, anim, scale, t)
        out.append({
            "animation_number": lf.animation_number,
            "animation_time": lf.animation_time,
            "frame_time": lf.frame_time,
            "old_frame_time": lf.old_frame_time,
            "old_frame": lf.old_frame, "frame": lf.frame,
            "backlerp": lf.backlerp,
        })
    return out


def _compare(script):
    want, got = _oracle(script), _pantheon(script)
    assert len(want) == len(got), "%d oracle steps vs %d pantheon" % (
        len(want), len(got))
    bad = []
    for i, (w, g) in enumerate(zip(want, got)):
        for k in ("animation_number", "animation_time", "frame_time",
                  "old_frame_time", "old_frame", "frame"):
            if w[k] != g[k]:
                bad.append("step %d %s: engine %s vs pantheon %s"
                           % (i, k, w[k], g[k]))
        d = abs(w["backlerp"] - g["backlerp"])
        if d > BACKLERP_TOL:
            bad.append("step %d backlerp: engine %.9f vs pantheon %.9f (%.2e)"
                       % (i, w["backlerp"], g["backlerp"], d))
    assert not bad, "\n".join(bad[:15])
    return want


def _schedule(anim, times, scale=1.0, clear_at=None):
    script = []
    if clear_at is not None:
        script.append(("clear", anim, 1.0, clear_at))
    script += [("step", anim, scale, t) for t in times]
    return script


def _at(start, step, n):
    return [start + i * step for i in range(n)]


# -- render schedules ------------------------------------------------------

@pytest.mark.parametrize("step_ms,label", [
    (25, "25ms snapshot rate"), (33, "30fps"), (16, "60fps"),
    (100, "matches frameLerp exactly"), (250, "coarser than the animation"),
])
@pytest.mark.parametrize("anim", [0, 1, 2, 3, 4, 5])
def test_animation_phase_matches_the_engine_on_a_fixed_schedule(
        step_ms, label, anim):
    _compare(_schedule(anim, _at(1000, step_ms, 40)))


def test_variable_frametime_matches_the_engine():
    """A real render clock is not uniform. The engine's frameTime carries the
    history of every previous interval, so an uneven schedule is the case a
    closed form gets wrong."""
    t, times = 1000, []
    for i in range(48):
        t += (8, 33, 16, 120, 41)[i % 5]
        times.append(t)
    _compare(_schedule(0, times))


# -- the animation shapes --------------------------------------------------

def test_initial_lerp_offsets_where_the_animation_starts():
    """animationTime = frameTime + initialLerp at the moment of the switch --
    not an absolute clock. Index 4 declares a 400ms initialLerp against a
    250ms frameLerp so the offset cannot hide."""
    _compare(_schedule(4, _at(1000, 25, 60)))


def test_non_looping_animation_sticks_at_the_end():
    """loop_frames 0: f clamps to numFrames-1 AND frameTime is set to `time`,
    so the animation can transition away on the very next call."""
    rows = _compare(_schedule(1, _at(1000, 25, 60)))
    last = ANIMS[1].first_frame + ANIMS[1].num_frames - 1
    assert rows[-1]["frame"] == last, "the engine should be stuck at the end"


def test_reversed_animation_counts_backwards():
    rows = _compare(_schedule(2, _at(1000, 25, 40)))
    a = ANIMS[2]
    assert all(a.first_frame <= r["frame"] < a.first_frame + a.num_frames
               for r in rows)


def test_flipflop_animation_bounces():
    rows = _compare(_schedule(3, _at(1000, 25, 60)))
    frames = [r["frame"] for r in rows]
    assert max(frames) > min(frames), "a flipflop must actually move"


def test_partial_loop_returns_into_the_tail():
    """loop_frames < num_frames: the wrap lands at numFrames-loopFrames, not
    at frame 0."""
    a = ANIMS[5]
    rows = _compare(_schedule(5, _at(1000, 25, 90)))
    late = [r["frame"] for r in rows[40:]]
    assert min(late) >= a.first_frame + a.num_frames - a.loop_frames


# -- switching -------------------------------------------------------------

def test_switching_animation_mid_sequence_matches_the_engine():
    script = ([("step", 0, 1.0, t) for t in _at(1000, 25, 12)]
              + [("step", 1, 1.0, t) for t in _at(1300, 25, 12)]
              + [("step", 0, 1.0, t) for t in _at(1600, 25, 12)])
    _compare(script)


def test_the_toggle_bit_restarts_an_animation_of_the_same_number():
    """A repeated gesture reuses the animation number and flips
    ANIM_TOGGLEBIT; the engine treats that as a different number and
    restarts. Dropping the bit would silently swallow the second gesture."""
    tb = rf.ANIM_TOGGLEBIT
    script = ([("step", 1, 1.0, t) for t in _at(1000, 25, 8)]
              + [("step", 1 | tb, 1.0, t) for t in _at(1200, 25, 8)]
              + [("step", 1, 1.0, t) for t in _at(1400, 25, 8)])
    _compare(script)


def test_switching_every_single_step_matches_the_engine():
    script = [("step", 0 if i % 2 == 0 else 2, 1.0, 1000 + i * 25)
              for i in range(24)]
    _compare(script)


# -- clocks and jumps ------------------------------------------------------

def test_clear_lerp_frame_seeds_the_state():
    _compare(_schedule(0, _at(5000, 25, 24), clear_at=5000))


def test_a_large_forward_jump_matches_the_engine():
    """Seeking forward: the engine clamps frameTime up to `time` rather than
    catching up frame by frame."""
    script = ([("step", 0, 1.0, t) for t in _at(1000, 25, 8)]
              + [("step", 0, 1.0, t) for t in (60000, 60025, 60050, 60075)])
    _compare(script)


def test_a_backward_jump_matches_the_engine():
    """Scrubbing backwards. The engine has two guards -- frameTime more than
    200ms ahead of `time`, and oldFrameTime ahead of `time` -- and both fire
    here."""
    script = ([("step", 0, 1.0, t) for t in _at(60000, 25, 8)]
              + [("step", 0, 1.0, t) for t in _at(1000, 25, 8)])
    _compare(script)


def test_a_repeated_time_does_not_advance():
    script = [("step", 0, 1.0, t) for t in
              (1000, 1000, 1000, 1100, 1100, 1200, 1200, 1200)]
    _compare(script)


# -- speed scale -----------------------------------------------------------

@pytest.mark.parametrize("scale", [0.5, 1.0, 1.3, 2.0, 3.0])
def test_speed_scale_matches_the_engine(scale):
    """speedScale multiplies the frame INDEX after an integer division, not
    the clock -- so it is not the same as running the animation faster."""
    _compare(_schedule(0, _at(1000, 25, 40), scale=scale))


# -- independence ----------------------------------------------------------

def test_legs_and_torso_are_independent_lerp_frames():
    """Two body parts on the same clock, different animations, must not share
    state. Run each as its own sequence and require both to match."""
    times = _at(1000, 25, 30)
    _compare(_schedule(0, times))
    _compare(_schedule(3, times, scale=1.0))


def test_the_closed_form_really_does_disagree():
    """The proof that this was worth doing: on a schedule coarser than the
    animation's own frame rate, `frame = time / frameLerp` and the engine
    part company. Recorded here so nobody re-derives the closed form."""
    a = ANIMS[0]
    times = _at(1000, 250, 12)          # 250ms steps, 100ms frameLerp
    rows = _oracle(_schedule(0, times))
    closed = [a.first_frame + ((t - 1000) // a.frame_lerp) % a.num_frames
              for t in times]
    engine = [r["frame"] for r in rows]
    assert engine != closed, ("if these ever agree the schedule stopped "
                              "exercising the difference")


# -- constants, checked against the header rather than from memory ---------

BG_PUBLIC = Path("G:/QUAKE_LEGACY/engine/pantheon_renderer/wolfcamql-11.3-src/"
                 "wolfcamql-src/code/game/bg_public.h")


def test_anim_constants_match_the_header():
    """ANIM_TOGGLEBIT and MAX_TOTALANIMATIONS were both wrong when written
    from memory (256 and 44 against a real 128 and 37), and the oracle threw
    "Bad animation number: 257" rather than quietly agreeing. Read them."""
    if not BG_PUBLIC.exists():
        pytest.skip("engine source tree absent")
    text = BG_PUBLIC.read_text(encoding="utf-8", errors="replace")

    m = re.search(r"#define\s+ANIM_TOGGLEBIT\s+(\d+)", text)
    assert m, "ANIM_TOGGLEBIT not found in bg_public.h"
    assert rf.ANIM_TOGGLEBIT == int(m.group(1))

    block = next((c.split("}", 1)[0] for c in text.split("typedef enum {")
                  if "MAX_TOTALANIMATIONS" in c), None)
    assert block, "animNumber_t enum not found"
    names = [n.strip().rstrip(",")
             for n in re.sub(r"//.*", "", block).splitlines() if n.strip()]
    assert names[-1] == "MAX_TOTALANIMATIONS", names[-3:]
    assert rf.MAX_TOTALANIMATIONS == len(names) - 1, names
