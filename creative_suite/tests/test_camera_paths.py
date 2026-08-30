"""Camera path generators, collision validation, scoring, candidates."""
import json
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import camera_paths as cp

PK3 = REPO_ROOT / "output" / "demo_v2" / "_wolfcam_staging" / "baseq3" / "pak00.pk3"


def straight_track(n=11, step_ms=100, speed=32.0):
    return [(i * step_ms, i * speed, 0.0, 24.0) for i in range(n)]


class HalfspaceTracer:
    """Synthetic geometry: everything with x > wall_x is solid."""

    def __init__(self, wall_x=100.0):
        self.wall_x = wall_x

    def line_blocked(self, a, b):
        return a[0] > self.wall_x or b[0] > self.wall_x


class OpenTracer:
    def line_blocked(self, a, b):
        return False


# ── geometry ─────────────────────────────────────────────────────────────────

def test_orbit_geometry():
    center = (100.0, -50.0, 20.0)
    kfs = cp.orbit(center, radius=300.0, height=40.0, arc_deg=180.0,
                   duration_ms=2000.0, start_deg=0.0)
    assert kfs[0]["t_ms"] == 0 and kfs[-1]["t_ms"] == 2000
    for kf in kfs:
        dx = kf["pos"][0] - center[0]
        dy = kf["pos"][1] - center[1]
        assert math.hypot(dx, dy) == pytest.approx(300.0, abs=1e-6)
        assert kf["pos"][2] == pytest.approx(center[2] + 40.0)
    # first keyframe at azimuth 0, last at 180
    assert kfs[0]["pos"][0] == pytest.approx(center[0] + 300.0)
    assert kfs[-1]["pos"][0] == pytest.approx(center[0] - 300.0, abs=1e-6)
    # camera looks inward: yaw of first kf points in -x direction (180 deg)
    assert abs(abs(kfs[0]["angles"][1]) - 180.0) < 1.0


def test_look_at_angles_pitch_sign():
    # Q3 convention: positive pitch looks DOWN
    ang = cp.look_at_angles((0, 0, 100), (100, 0, 0))
    assert ang[0] > 0
    ang_up = cp.look_at_angles((0, 0, 0), (100, 0, 100))
    assert ang_up[0] < 0


def test_side_track_perpendicular():
    track = straight_track()
    kfs = cp.side_track(track, lateral_offset=200.0, height=10.0)
    assert len(kfs) == len(track)
    for kf, (t, x, y, z) in zip(kfs, track):
        assert kf["pos"][1] == pytest.approx(-200.0)   # right of +x motion
        assert kf["pos"][0] == pytest.approx(x)


def test_chase_behind():
    track = straight_track()
    kfs = cp.chase(track, behind_dist=150.0, up=30.0)
    mid = len(kfs) // 2
    assert kfs[mid]["pos"][0] == pytest.approx(track[mid][1] - 150.0)
    assert kfs[mid]["pos"][2] == pytest.approx(track[mid][3] + 30.0)


def test_top_down_looks_down():
    kfs = cp.top_down((0, 0, 0), height=800.0, duration_ms=1000.0)
    for kf in kfs:
        assert kf["angles"][0] == pytest.approx(89.0)
        assert kf["pos"][2] == pytest.approx(800.0)


def test_projectile_follow_trails():
    track = straight_track(speed=200.0)
    kfs = cp.projectile_follow(track, trail_dist=80.0)
    assert kfs[5]["pos"][0] == pytest.approx(track[5][1] - 80.0)


def test_vertical_orbit_sweeps_elevation():
    kfs = cp.vertical_orbit((0, 0, 0), radius=300.0, arc_deg=80.0,
                            duration_ms=1000.0, start_elev_deg=0.0)
    assert kfs[0]["pos"][2] == pytest.approx(0.0, abs=1e-6)
    assert kfs[-1]["pos"][2] == pytest.approx(300.0 * math.sin(math.radians(80)))


def test_bullet_time_arc_starts_opposite_view():
    kfs = cp.bullet_time_arc((0, 0, 0), start_angles=(0.0, 90.0, 0.0),
                             arc_deg=90.0, radius=100.0, height=0.0)
    # view yaw 90 -> camera starts at azimuth 270 (behind the shooter's view)
    assert kfs[0]["pos"][1] == pytest.approx(-100.0, abs=1e-6)


def test_reverse_track_remaps_time():
    kfs = cp.orbit((0, 0, 0), 100.0, 0.0, 90.0, 1000.0)
    rev = cp.reverse_track(kfs)
    assert rev[0]["t_ms"] == kfs[0]["t_ms"]
    assert rev[-1]["t_ms"] == kfs[-1]["t_ms"]
    assert rev[0]["pos"] == kfs[-1]["pos"]


# ── determinism ──────────────────────────────────────────────────────────────

def _ctx(tracer=None):
    return {"subject_track": straight_track(), "tracer": tracer,
            "impact_point": (320.0, 0.0, 24.0), "impact_t_ms": 1000,
            "view_angles": (0.0, 0.0, 0.0), "ideal_distance": 300.0}


def test_generate_candidates_deterministic():
    a = json.dumps(cp.generate_candidates(_ctx(OpenTracer())), sort_keys=True)
    b = json.dumps(cp.generate_candidates(_ctx(OpenTracer())), sort_keys=True)
    assert a == b


def test_orbit_deterministic():
    k1 = cp.orbit((5, 5, 5), 250.0, 30.0, 270.0, 3000.0)
    k2 = cp.orbit((5, 5, 5), 250.0, 30.0, 270.0, 3000.0)
    assert k1 == k2


# ── collision validation + adjustment (synthetic) ────────────────────────────

def test_validate_path_flags_solid_keyframes():
    track = straight_track()
    kfs = cp.follow_entity(track, (200.0, 0.0, 0.0))   # pushes past wall
    ok, report = cp.validate_path(HalfspaceTracer(150.0), kfs)
    assert not ok
    assert report["solid_keyframes"]


def test_validate_path_open_space_passes():
    kfs = cp.orbit((0, 0, 0), 100.0, 20.0, 90.0, 1000.0)
    ok, report = cp.validate_path(OpenTracer(), kfs)
    assert ok
    assert report["solid_keyframes"] == [] and report["blocked_segments"] == []


def test_adjust_path_converges_toward_subject():
    track = [(0, 0.0, 0.0, 24.0), (1000, 0.0, 0.0, 24.0)]
    kfs = [cp._kf(0, (400.0, 0.0, 24.0), (0, 180, 0), 90.0),
           cp._kf(1000, (400.0, 50.0, 24.0), (0, 180, 0), 90.0)]
    tracer = HalfspaceTracer(100.0)     # subject at x=0 open, kfs at 400 solid
    ok, adjusted, report = cp.adjust_path(tracer, kfs, track,
                                          max_iterations=60)
    assert ok, report
    for kf in adjusted:
        assert kf["pos"][0] <= 100.0


def test_adjust_path_noop_when_valid():
    kfs = cp.orbit((0, 0, 0), 100.0, 20.0, 90.0, 1000.0)
    ok, adjusted, report = cp.adjust_path(OpenTracer(), kfs, None)
    assert ok and adjusted == kfs and report["iterations"] == 0


# ── collision on a real map ──────────────────────────────────────────────────

@pytest.fixture(scope="module")
def real_tracer():
    if not PK3.exists():
        pytest.skip("staging pak00.pk3 not present")
    try:
        tracer = cp.bsp_tracer("aerowalk", str(PK3))
    except Exception as e:
        pytest.skip(f"bsp_geometry unusable: {e}")
    return tracer


_ENCLOSURE_RAYS = ((8000, 0, 0), (-8000, 0, 0), (0, 8000, 0),
                   (0, -8000, 0), (0, 0, 8000), (0, 0, -8000))


def _find_open_point(tracer):
    """An INTERIOR open point: in open space and walled in on >= 5 of 6
    far rays (distinguishes playable rooms from the exterior void, where
    point_in_open_space is vacuously true)."""
    for z in range(-256, 769, 128):
        for x in range(-768, 769, 128):
            for y in range(-768, 769, 128):
                p = (float(x), float(y), float(z))
                if not cp.point_in_open_space(tracer, p):
                    continue
                enclosed = sum(
                    1 for d in _ENCLOSURE_RAYS
                    if tracer.line_blocked(
                        p, (p[0] + d[0], p[1] + d[1], p[2] + d[2])))
                if enclosed >= 5:
                    return p
    return None


def test_real_map_long_segment_blocked(real_tracer):
    assert real_tracer.line_blocked((-8000.0, -8000.0, -8000.0),
                                    (8000.0, 8000.0, 8000.0))


def test_real_map_has_open_and_solid_space(real_tracer):
    open_pt = _find_open_point(real_tracer)
    assert open_pt is not None, "no open point found on aerowalk sample grid"
    # a tiny epsilon segment at the open point must not clip
    assert not real_tracer.line_blocked(
        open_pt, (open_pt[0], open_pt[1], open_pt[2] + 0.25))


def test_real_map_validate_and_adjust(real_tracer):
    open_pt = _find_open_point(real_tracer)
    assert open_pt is not None
    subject = [(0, *open_pt), (1000, *open_pt)]
    # 2-step orbit: chords are diameters straight through the map interior
    big = cp.orbit(open_pt, radius=3000.0, height=0.0, arc_deg=360.0,
                   duration_ms=1000.0, steps=2)
    ok_big, rep_big = cp.validate_path(real_tracer, big)
    assert not ok_big
    ok, adjusted, report = cp.adjust_path(real_tracer, big, subject,
                                          max_iterations=80)
    # adjustment must strictly reduce violations even if not fully clear
    ok2, rep2 = cp.validate_path(real_tracer, adjusted)
    v_before = len(rep_big["solid_keyframes"]) + len(rep_big["blocked_segments"])
    v_after = len(rep2["solid_keyframes"]) + len(rep2["blocked_segments"])
    assert v_after < v_before


# ── scoring ──────────────────────────────────────────────────────────────────

def test_score_monotonic_visibility():
    track = straight_track()
    kfs = cp.side_track(track, 200.0)

    class BlockAim:
        def line_blocked(self, a, b):
            return True
    open_score = cp.score_path(OpenTracer(), kfs, track)
    blocked_score = cp.score_path(BlockAim(), kfs, track)
    assert blocked_score["target_visibility"] < open_score["target_visibility"]
    assert blocked_score["total"] < open_score["total"]


def test_score_monotonic_smoothness():
    smooth = cp.orbit((0, 0, 0), 300.0, 40.0, 120.0, 2000.0, steps=20)
    jagged = [dict(kf) for kf in smooth]
    for i, kf in enumerate(jagged):
        p = kf["pos"]
        kf["pos"] = (p[0], p[1], p[2] + (60.0 if i % 2 else -60.0))
    s1 = cp.score_path(None, smooth, None)
    s2 = cp.score_path(None, jagged, None)
    assert s2["smoothness"] < s1["smoothness"]


def test_score_distance_fit_prefers_ideal():
    track = straight_track()
    near_ideal = cp.side_track(track, 300.0)
    far = cp.side_track(track, 1500.0)
    extras = {"ideal_distance": 300.0}
    s1 = cp.score_path(None, near_ideal, track, extras)
    s2 = cp.score_path(None, far, track, extras)
    assert s1["mean_distance_fit"] > s2["mean_distance_fit"]


def test_generate_candidates_ranking():
    cands = cp.generate_candidates(_ctx(OpenTracer()))
    names = [c["name"] for c in cands]
    assert "pov" in names and "side_track" in names and "target_orbit" in names
    scores = [(c["valid"], c["score"]) for c in cands]
    assert scores == sorted(scores, reverse=True)
    # every valid candidate outranks every invalid one
    seen_invalid = False
    for c in cands:
        if not c["valid"]:
            seen_invalid = True
        assert not (seen_invalid and c["valid"])


def test_generate_candidates_requires_track():
    with pytest.raises(ValueError):
        cp.generate_candidates({"subject_track": []})
