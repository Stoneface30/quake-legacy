"""PANTHEON's presentation evaluator, checked against the ENGINE'S OWN code.

Every previous presentation check compared PANTHEON to PANTHEON. This one
compiles CG_SwingAngles and CG_PlayerAngles -- lifted verbatim from the
WolfcamQL 11.3 source by engine/pantheon_renderer/oracle/extract_oracle.py --
into a standalone harness, feeds it the same state sequence, and diffs.

The oracle never calls PANTHEON, and PANTHEON never calls the oracle.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from engine.pantheon import render_frame as rf

ORACLE_DIR = Path("G:/QUAKE_LEGACY/engine/pantheon_renderer/oracle")
ORACLE_EXE = ORACLE_DIR / "oracle.exe"

LEGS_RUN, LEGS_IDLE, TORSO_STAND = 15, 22, 11
# The axes are unit vectors; this is generous for float32-vs-float64
# and tight enough that a missing lean or twitch cannot hide.
AXIS_TOL = 1e-4


def _oracle(steps):
    """Run the engine's own code over the sequence. Returns per-step
    (legsYaw, torsoYaw, torsoPitch)."""
    if not ORACLE_EXE.exists():
        pytest.skip("oracle not built (engine source tree absent)")
    stdin = "".join(
        "%d %f %f %d %d %d %d %f %f %f %d %d %d %d %d\n" % s for s in steps)
    r = subprocess.run([str(ORACLE_EXE)], input=stdin, capture_output=True,
                       text=True, cwd=str(ORACLE_DIR))
    assert r.returncode == 0, r.stderr
    out = []
    for line in r.stdout.strip().splitlines():
        f = [float(x) for x in line.split()]
        out.append({"swing": (f[0], f[1], f[2]), "legs": f[3:12],
                    "torso": f[12:21], "head": f[21:30]})
    return out


class _Swing:
    """Drive PANTHEON's evaluator over the same sequence, stepwise."""

    def __init__(self, steps):
        self.steps = steps

    def run(self):
        ev = rf.PresentationEvaluator.__new__(rf.PresentationEvaluator)
        st = rf._Swing()
        out = []

        class _A:  # a minimal ActorTruth stand-in
            pass

        for (ft, yaw, pitch, legs, torso, mdir, eflags, vx, vy, vz,
             cgt, pt, pd, fl, fto) in self.steps:
            a = _A()
            a.yaw, a.pitch = yaw, pitch
            a.legs_anim, a.torso_anim, a.move_dir = legs, torso, mdir
            a.e_flags = eflags
            rf.PresentationEvaluator._step(ev, st, a, ft)
            la, ta, ha = rf.player_angles(
                st, view_yaw=yaw, view_pitch=pitch, legs_anim=legs,
                torso_anim=torso, move_dir=mdir, velocity=(vx, vy, vz),
                e_flags=eflags, now_ms=cgt, pain_time=pt, pain_direction=pd,
                fixed_legs=bool(fl), fixed_torso=bool(fto))
            out.append({
                "swing": (st.legs_yaw, st.torso_yaw, st.torso_pitch),
                "legs": [c for row in rf.angles_to_axis(la) for c in row],
                "torso": [c for row in rf.angles_to_axis(ta) for c in row],
                "head": [c for row in rf.angles_to_axis(ha) for c in row],
            })
        return out


def _turn_sequence(n=14, turn_at=2, yaw_to=90.0, legs=LEGS_RUN,
                   torso=TORSO_STAND, pitch=0.0, mdir=0, vel=(0, 0, 0)):
    return [(25, 0.0 if i < turn_at else yaw_to, pitch, legs, torso, mdir, 0,
             vel[0], vel[1], vel[2], 1000 + i * 25, -10000, 0, 0, 0)
            for i in range(n)]


def _compare(steps, tol=0.05):
    want = _oracle(steps)
    got = _Swing(steps).run()
    assert len(want) == len(got)
    worst = 0.0
    bad = []
    for i, (ww, gg) in enumerate(zip(want, got)):
        w, g = ww["swing"], gg["swing"]
        for k, name in enumerate(("legsYaw", "torsoYaw", "torsoPitch")):
            d = abs(((w[k] - g[k]) + 180.0) % 360.0 - 180.0)
            worst = max(worst, d)
            if d > tol:
                bad.append("step %d %s: engine %.4f vs pantheon %.4f (%.4f)"
                           % (i, name, w[k], g[k], d))
        # THE PART AXES, which is what actually gets drawn. Comparing only the
        # swing scalars hid the velocity lean entirely: it lands on legs pitch
        # and roll and never touches yawAngle.
        for part in ("legs", "torso", "head"):
            for k in range(9):
                d = abs(ww[part][k] - gg[part][k])
                worst = max(worst, d)
                if d > AXIS_TOL:
                    bad.append("step %d %s axis[%d]: engine %.6f vs "
                               "pantheon %.6f (%.6f)"
                               % (i, part, k, ww[part][k], gg[part][k], d))
    assert not bad, ("worst %.4f deg\n" % worst) + "\n".join(bad[:12])
    return worst


def test_swing_matches_the_engine_on_a_yaw_turn():
    _compare(_turn_sequence())


def test_swing_matches_the_engine_on_a_pitch_change():
    steps = [(25, 0.0, 0.0 if i < 2 else -40.0, LEGS_RUN, TORSO_STAND, 0, 0,
              0, 0, 0, 1000 + i * 25, -10000, 0, 0, 0) for i in range(14)]
    _compare(steps)


def test_swing_matches_the_engine_across_the_yaw_wrap():
    steps = [(25, 359.0 if i < 2 else 5.0, 0.0, LEGS_RUN, TORSO_STAND, 0, 0,
              0, 0, 0, 1000 + i * 25, -10000, 0, 0, 0) for i in range(14)]
    _compare(steps)


@pytest.mark.parametrize("mdir", [0, 1, 2, 3, 4, 5, 6, 7])
def test_movement_direction_offsets_match_the_engine(mdir):
    _compare(_turn_sequence(mdir=mdir))


def test_idle_and_standing_does_not_force_centering():
    """The 'always center' rule only fires when moving or acting."""
    _compare(_turn_sequence(legs=LEGS_IDLE, torso=TORSO_STAND))


def test_variable_frametime_matches_the_engine():
    steps = []
    for i in range(16):
        ft = 8 if i % 3 == 0 else (33 if i % 3 == 1 else 16)
        steps.append((ft, 0.0 if i < 2 else 120.0, 0.0, LEGS_RUN,
                      TORSO_STAND, 0, 0, 0, 0, 0, 1000 + i * 25,
                      -10000, 0, 0, 0))
    _compare(steps)


# ── known gaps, held open by the oracle ────────────────────────────────────
#
# The swing state matches the engine exactly. The FINAL PART AXES do not yet,
# because CG_PlayerAngles does two more things PANTHEON has not implemented.
# These are recorded as expected failures so they stay visible and cannot be
# quietly forgotten -- not skipped, because a skip says "not applicable" and
# these are simply not done.

def _oracle_axes(steps):
    import subprocess
    if not ORACLE_EXE.exists():
        pytest.skip("oracle not built")
    stdin = "".join("%d %f %f %d %d %d %d %f %f %f %d %d %d %d %d\n" % s for s in steps)
    r = subprocess.run([str(ORACLE_EXE)], input=stdin, capture_output=True,
                       text=True, cwd=str(ORACLE_DIR))
    assert r.returncode == 0, r.stderr
    rows = []
    for line in r.stdout.strip().splitlines():
        f = [float(x) for x in line.split()]
        rows.append({"legs": f[3:12], "torso": f[12:21], "head": f[21:30]})
    return rows


def test_velocity_lean_is_present_in_the_engine_and_measurable():
    """CG_PlayerAngles leans the legs by velocity:

        side = speed * DotProduct(velocity, axis[1]);  legsAngles[ROLL] -= side
        side = speed * DotProduct(velocity, axis[0]);  legsAngles[PITCH] += side

    PANTHEON emits legs pitch/roll of zero, so a running player's legs stay
    bolt upright. This test pins the size of the difference; it does not pass
    judgement on it.
    """
    still = [(25, 45.0, 0.0, LEGS_RUN, TORSO_STAND, 0, 0, 0.0, 0.0, 0.0,
              1000 + i * 25, -10000, 0, 0, 0) for i in range(6)]
    moving = [(25, 45.0, 0.0, LEGS_RUN, TORSO_STAND, 0, 0, 320.0, 0.0, 0.0,
               1000 + i * 25, -10000, 0, 0, 0) for i in range(6)]
    a = _oracle_axes(still)[-1]["legs"]
    b = _oracle_axes(moving)[-1]["legs"]
    delta = max(abs(x - y) for x, y in zip(a, b))
    assert delta > 0.01, "the engine really does lean the legs with velocity"


@pytest.mark.parametrize("vel", [(0, 0, 0), (320, 0, 0), (0, -400, 0),
                                 (280, 280, 0), (900, 120, 0),
                                 (200, -200, 300)])
def test_velocity_lean_matches_the_engine(vel):
    """Stationary, forward, sideways, diagonal, high speed, airborne."""
    _compare(_turn_sequence(vel=vel))


@pytest.mark.parametrize("offset", [0, 50, 100, 199, 200, 400])
@pytest.mark.parametrize("direction", [0, 1])
def test_pain_twitch_matches_the_engine(offset, direction):
    """Onset, mid-decay, the last millisecond, and after it has expired --
    in both roll directions, which the engine alternates per pain event."""
    steps = [(25, 45.0, 0.0, LEGS_RUN, TORSO_STAND, 0, 0, 0, 0, 0,
              1000 + i * 25, 1000 + 25 - offset, direction, 0, 0)
             for i in range(6)]
    _compare(steps)


@pytest.mark.parametrize("fixed_legs,fixed_torso",
                         [(0, 0), (1, 0), (0, 1), (1, 1)])
def test_fixedlegs_and_fixedtorso_match_the_engine(fixed_legs, fixed_torso):
    """Both flags are parsed from the MODEL'S animation.cfg by
    CG_ParseAnimationFile -- configstrings only choose which model, and so
    which animation.cfg, applies."""
    steps = [(25, 0.0 if i < 2 else 90.0, -30.0, LEGS_RUN, TORSO_STAND, 2, 0,
              320.0, 0.0, 0.0, 1000 + i * 25, -10000, 0,
              fixed_legs, fixed_torso) for i in range(10)]
    _compare(steps)


def test_dead_actors_take_movement_direction_zero():
    """EF_DEAD forces dir 0 regardless of angles2."""
    steps = [(25, 45.0, 0.0, LEGS_RUN, TORSO_STAND, 5, 1, 0, 0, 0,
              1000 + i * 25, -10000, 0, 0, 0) for i in range(8)]
    _compare(steps)
