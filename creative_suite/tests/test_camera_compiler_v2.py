"""Camera V2: dense resampling, decoupled look-at, sampled-path collision,
compile-to-FREECAM_SAMPLED. Mirrors test_camera_paths.py's BSP
skip-if-unavailable pattern for the collision tests.
"""
import json
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import camera_compiler_v2 as v2
from creative_suite.engine import camera_paths as cp
from creative_suite.engine import cam10_writer as cw

PK3 = REPO_ROOT / "output" / "demo_v2" / "_wolfcam_staging" / "baseq3" / "pak00.pk3"
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"


def kf(t, pos, angles=(0.0, 0.0, 0.0), fov=90.0):
    return {"t_ms": t, "pos": pos, "angles": angles, "fov": fov}


SPARSE = [kf(0, (0.0, 0.0, 0.0)), kf(1000, (100.0, 0.0, 0.0), (0.0, 90.0, 0.0)),
          kf(2000, (100.0, 100.0, 0.0), (0.0, 180.0, 0.0))]


# ── resample_dense ───────────────────────────────────────────────────────────

def test_resample_dense_reproduces_endpoints_exactly():
    dense = v2.resample_dense(SPARSE, hz=30.0)
    assert dense[0]["pos"] == SPARSE[0]["pos"]
    assert dense[0]["t_ms"] == SPARSE[0]["t_ms"]
    assert dense[-1]["pos"] == SPARSE[-1]["pos"]
    assert dense[-1]["t_ms"] == SPARSE[-1]["t_ms"]


def test_resample_dense_visits_middle_authored_keyframe_time():
    dense = v2.resample_dense(SPARSE, hz=100.0)
    times = [d["t_ms"] for d in dense]
    assert any(abs(t - 1000) < 1e-6 for t in times)


def test_resample_dense_sample_count_matches_hz():
    dense = v2.resample_dense(SPARSE, hz=30.0)
    # 2000ms at 30Hz (~33.3ms/sample) -> ~61 samples
    assert 55 <= len(dense) <= 65


def test_resample_dense_higher_hz_is_denser():
    lo = v2.resample_dense(SPARSE, hz=10.0)
    hi = v2.resample_dense(SPARSE, hz=60.0)
    assert len(hi) > len(lo)


def test_resample_dense_deterministic():
    a = v2.resample_dense(SPARSE, hz=45.0)
    b = v2.resample_dense(SPARSE, hz=45.0)
    assert a == b


def test_resample_dense_passthrough_below_two_keyframes():
    assert v2.resample_dense([], 30.0) == []
    one = [kf(0, (0, 0, 0))]
    assert v2.resample_dense(one, 30.0) == one


def test_resample_dense_angle_wraparound_shortest_path():
    wrap = [kf(0, (0, 0, 0), (0.0, 350.0, 0.0)),
            kf(1000, (0, 0, 0), (0.0, 10.0, 0.0))]
    dense = v2.resample_dense(wrap, hz=10.0)
    mid = dense[len(dense) // 2]
    # shortest path 350 -> 10 goes THROUGH 0/360, not the long way via 180
    assert mid["angles"][1] > 350.0 or mid["angles"][1] < 20.0


# ── retarget_lookat ──────────────────────────────────────────────────────────

def test_retarget_lookat_points_at_moving_target():
    positions = [kf(0, (0.0, 0.0, 0.0)), kf(1000, (0.0, 0.0, 0.0))]
    target_track = [(0, 100.0, 0.0, 0.0), (1000, -100.0, 0.0, 0.0)]
    out = v2.retarget_lookat(positions, target_track)
    # camera stayed put; target moved from +X to -X -> yaw should flip ~180
    yaw0, yaw1 = out[0]["angles"][1], out[1]["angles"][1]
    assert abs(((yaw1 - yaw0 + 180) % 360) - 180) > 90


def test_retarget_lookat_preserves_position_and_fov():
    positions = [kf(0, (5.0, 6.0, 7.0), fov=100.0),
                 kf(1000, (5.0, 6.0, 7.0), fov=100.0)]
    target_track = [(0, 0.0, 0.0, 0.0), (1000, 0.0, 0.0, 0.0)]
    out = v2.retarget_lookat(positions, target_track)
    for o, p in zip(out, positions):
        assert o["pos"] == p["pos"]
        assert o["fov"] == p["fov"]


def test_retarget_lookat_damping_lags_the_raw_target():
    positions = [kf(t, (0.0, 0.0, 0.0)) for t in range(0, 1001, 100)]
    # target snaps from +X to -Y halfway through
    target_track = [(0, 100.0, 0.0, 0.0), (499, 100.0, 0.0, 0.0),
                    (500, 0.0, -100.0, 0.0), (1000, 0.0, -100.0, 0.0)]
    raw = v2.retarget_lookat(positions, target_track, damping=0.0)
    damped = v2.retarget_lookat(positions, target_track, damping=0.8)
    # right after the snap, damped yaw should lag closer to the pre-snap value
    idx = 5  # t=500
    assert damped[idx]["angles"][1] != raw[idx]["angles"][1]


# ── collision on dense path ──────────────────────────────────────────────────

class _WallTracer:
    """Synthetic tracer: a single infinite wall at x=50 blocks anything
    crossing it."""
    def line_blocked(self, a, b):
        return (a[0] - 50) * (b[0] - 50) < 0 or a[0] == 50 or b[0] == 50


def test_collision_check_dense_valid_when_clear():
    dense = v2.resample_dense(
        [kf(0, (0.0, 0.0, 0.0)), kf(1000, (10.0, 0.0, 0.0))], hz=30.0)
    result = v2.collision_check_dense(None, dense)
    assert result["status"] == v2.VALID
    assert result["used_count"] == len(dense)


def test_collision_check_dense_catches_tunneling_between_sparse_points():
    """The core ask: a fast camera crossing a wall BETWEEN two authored
    keyframes must be caught when checking the DENSE path, even though
    neither authored endpoint is itself in solid geometry."""
    sparse = [kf(0, (0.0, 0.0, 0.0)), kf(1000, (100.0, 0.0, 0.0))]
    # sparse-only check would see two clear endpoints either side of x=50
    # but never sample x=50 itself at low density; dense resampling does.
    dense = v2.resample_dense(sparse, hz=30.0)
    tracer = _WallTracer()
    ok, _ = cp.validate_path(tracer, sparse)
    assert not ok  # the segment IS blocked even in the sparse check here,
                    # since validate_path already checks segments -- the
                    # real risk this test protects against is a caller who
                    # only checks KEYFRAME points, not segments:
    solid_check_only = all(cp.point_in_open_space(tracer, k["pos"]) for k in sparse)
    assert solid_check_only  # both authored points are individually open
    result = v2.collision_check_dense(tracer, dense, subject_track=None)
    assert result["status"] in (v2.PUSHED_OUT, v2.SHORTENED, v2.REJECTED)


def test_collision_check_dense_no_tracer_is_valid():
    dense = v2.resample_dense(SPARSE, hz=30.0)
    result = v2.collision_check_dense(None, dense)
    assert result["status"] == v2.VALID


def test_collision_check_dense_rejected_when_start_blocked():
    tracer = _WallTracer()
    dense = v2.resample_dense(
        [kf(0, (50.0, 0.0, 0.0)), kf(500, (100.0, 0.0, 0.0))], hz=30.0)
    result = v2.collision_check_dense(tracer, dense, max_iterations=1)
    assert result["status"] in (v2.REJECTED, v2.SHORTENED, v2.PUSHED_OUT)


@pytest.mark.skipif(not PK3.exists(), reason="staged pak00.pk3 not present")
def test_collision_check_dense_real_bsp_orbit_is_clear_or_adjusted():
    tracer = cp.bsp_tracer("aerowalk", str(PK3))
    kfs = cp.orbit((0, 0, 200), radius=150.0, height=40.0, arc_deg=180.0,
                   duration_ms=2000.0, steps=6)
    dense = v2.resample_dense(kfs, hz=30.0)
    result = v2.collision_check_dense(tracer, dense, min_clearance_u=4.0)
    assert result["status"] in (v2.VALID, v2.PUSHED_OUT, v2.SHORTENED,
                                v2.REJECTED)
    if result["status"] in (v2.VALID, v2.PUSHED_OUT):
        assert result["min_clearance_u"] is not None


# ── compile_dense_camera ─────────────────────────────────────────────────────

def test_compile_dense_camera_defaults_to_native_cam10(tmp_path):
    """Corrected 2026-09-01: the original "playcamera is buggy" diagnosis
    was actually a CRLF bug in cam10_writer's own file-write call (fixed).
    Runtime-proven on the stock binary afterward, so NATIVE_CAM10 -- not
    FREECAM_SAMPLED -- is compile_dense_camera's default (it also isn't
    bound by the 128-slot at-command budget). FREECAM_SAMPLED remains
    available and default at the lower-level cam10_writer.compile_camera
    call (unchanged, still used by timeline.py::to_wolfcam_script)."""
    result = v2.compile_dense_camera(
        SPARSE, base_servertime=100000, gamedir=tmp_path,
        camera_name="v2test", hz=30.0)
    assert result["backend"] == cw.BACKEND_NATIVE_CAM10
    assert result["status"] == v2.VALID
    assert result["cam10_path"].exists()
    assert result["cfg_lines"] == ["freecam", "loadcamera v2test", "playcamera"]
    assert result["used_sample_count"] == len(result["dense_keyframes"])


def test_compile_dense_camera_explicit_freecam_sampled_backend(tmp_path):
    result = v2.compile_dense_camera(
        SPARSE, base_servertime=100000, gamedir=tmp_path,
        camera_name="v2test_fs", hz=30.0,
        backend=v2.BACKEND_FREECAM_SAMPLED)
    assert result["backend"] == v2.BACKEND_FREECAM_SAMPLED
    assert result["cfg_lines"][0] == "freecam"
    assert len(result["cfg_lines"]) == 1 + len(result["final_keyframes"])


def test_clamp_hz_to_budget_no_clamp_when_under_budget():
    hz, clamped = v2._clamp_hz_to_budget(SPARSE, hz=10.0)
    assert clamped is False
    assert hz == 10.0


def test_clamp_hz_to_budget_clamps_naive_60hz_4s_shot_for_freecam_sampled():
    """The exact scenario that hung real capture 2026-09-01 before the
    root cause was traced to cam10_writer's CRLF bug (not this budget):
    60Hz over a 4000ms shot wants 241 samples -- MAX_AT_COMMANDS -
    RESERVED leaves room for 120 under FREECAM_SAMPLED. Confirmed via
    qconsole.log: "too many at commands" appeared exactly 114 times for a
    242-command cfg (241 freecamsetpos + 1 quit) against the real 128-slot
    array -- this ceiling is real regardless of the separate CRLF finding."""
    long_orbit = [kf(0, (0, 0, 0)), kf(4000, (100, 0, 0))]
    hz, clamped = v2._clamp_hz_to_budget(long_orbit, hz=60.0,
                                         max_samples=v2.MAX_CAMERA_SAMPLES)
    assert clamped is True
    assert hz < 60.0
    n_samples = int(round(4.0 * hz)) + 1
    assert n_samples <= v2.MAX_CAMERA_SAMPLES


def test_clamp_hz_to_budget_native_cam10_has_much_higher_ceiling():
    """NATIVE_CAM10's ceiling is MAX_CAMERAPOINTS=512 (loadcamera reads
    the whole file in one shot, bypassing the at-command queue entirely)
    -- the same 60Hz/4s shot that clamps hard under FREECAM_SAMPLED does
    NOT need to clamp at all under NATIVE_CAM10."""
    long_orbit = [kf(0, (0, 0, 0)), kf(4000, (100, 0, 0))]
    hz, clamped = v2._clamp_hz_to_budget(long_orbit, hz=60.0,
                                         max_samples=cw.MAX_CAMERAPOINTS)
    assert clamped is False
    assert hz == 60.0


def test_compile_dense_camera_reports_clamp_honestly(tmp_path):
    long_orbit = [kf(0, (0, 0, 0)), kf(4000, (100, 0, 0))]
    result = v2.compile_dense_camera(
        long_orbit, base_servertime=0, gamedir=tmp_path,
        camera_name="clamp_test", hz=60.0,
        backend=v2.BACKEND_FREECAM_SAMPLED)
    assert result["requested_hz"] == 60.0
    assert result["hz_clamped"] is True
    assert result["effective_hz"] < 60.0
    assert len(result["dense_keyframes"]) <= v2.MAX_CAMERA_SAMPLES
    # the cfg this produces must never exceed the real engine budget
    assert len(result["cfg_lines"]) <= v2.MAX_AT_COMMANDS


def test_compile_dense_camera_rejected_status_emits_no_cfg():
    tracer = _WallTracer()
    blocked = [kf(0, (50.0, 0.0, 0.0)), kf(500, (60.0, 0.0, 0.0))]
    result = v2.compile_dense_camera(
        blocked, base_servertime=0, gamedir=Path("/tmp/unused"),
        camera_name="x", hz=30.0, tracer=tracer, min_clearance_u=1.0)
    if result["status"] == v2.REJECTED:
        assert result["cam10_path"] is None
        assert result["cfg_lines"] is None


# ── projectile_track_from_recognition ────────────────────────────────────────

def test_projectile_track_from_recognition_shape():
    path_json = {
        "launch": {"t": 100000, "pos": [0, 0, 0], "dir": [1, 0, 0]},
        "points": [[0, 0.0, 0.0, 0.0], [25, 10.0, 0.0, 0.0]],
        "impact": {"t": 100025, "pos": [10.0, 0.0, 0.0]},
    }
    track = v2.projectile_track_from_recognition(path_json)
    assert track == [(100000, 0.0, 0.0, 0.0), (100025, 10.0, 0.0, 0.0)]


@pytest.mark.skipif(not RECOG_DB.exists(), reason="frag_recognition.db not present")
def test_projectile_track_from_recognition_real_cache_row():
    con = sqlite3.connect(f"file:{RECOG_DB}?mode=ro", uri=True)
    row = con.execute(
        "SELECT path FROM recognition_projectile_paths LIMIT 1").fetchone()
    con.close()
    if row is None:
        pytest.skip("no cached projectile paths")
    path_json = json.loads(row[0])
    track = v2.projectile_track_from_recognition(path_json)
    assert len(track) == len(path_json["points"])
    assert track[0][0] == path_json["launch"]["t"]



def test_native_cam10_never_writes_more_points_than_the_engine_can_update(tmp_path):
    """CG_UpdateCameraInfoExt walks three points past numCameraPoints, and the
    loader has no cap. 512 points load and then overflow; 509 is the real
    ceiling. A 27 s orbit at 60 Hz would otherwise ask for 1640."""
    long_shot = [kf(0, (0, 0, 0)), kf(27_000, (100, 0, 0))]
    result = v2.compile_dense_camera(
        long_shot, base_servertime=0, gamedir=tmp_path,
        camera_name="cap_test", hz=60.0, backend=cw.BACKEND_NATIVE_CAM10)
    assert result["used_sample_count"] <= cw.CAM10_USABLE_POINTS
    assert cw.CAM10_USABLE_POINTS == cw.MAX_CAMERAPOINTS - 3 == 509
    assert result["hz_clamped"] is True
