"""Camera path COVERAGE classification and the collision recovery ladder.

The production defect these tests pin down: ``collision_check_dense`` can
return SHORTENED — a clean prefix of the path survives, the rest is discarded
— but nothing shortens the CAPTURE. The engine reaches the last camera point
and holds that pose for the remainder of the scene. A long static hold in the
middle of a cinematic shot is a visible failure, and before this work the only
trace of it was the string ``"SHORTENED"``.

Two things are asserted here:

* **ITEM A** — ``camera_compiler_v2.classify_coverage`` turns that into
  FULL / PARTIAL_OK / PARTIAL_BAD / INVALID plus the raw numbers, and
  ``compile_dense_camera`` reports them on its result.
* **ITEM B** — ``director_preview.build_camera_artifact`` RECOVERS from a
  PARTIAL_BAD instead of shipping the hold, and whatever it does is visible
  in ``camera_fallback`` / ``camera_recovery``. The invariant that matters is
  the last one in this file: a delivered camera is never both PARTIAL_BAD and
  silent about it.

No demo filenames appear in this file (public repo): frags are synthetic and
addressed by numeric id.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.api import director_draft as dd_mod
from creative_suite.engine import camera_compiler_v2 as v2
from creative_suite.engine import director_preview as dp


def kf(t, pos=(0.0, 0.0, 0.0), angles=(0.0, 0.0, 0.0), fov=90.0):
    return {"t_ms": t, "pos": pos, "angles": angles, "fov": fov}


# ── ITEM A: classify_coverage ───────────────────────────────────────────────

def test_coverage_full_when_path_spans_the_scene():
    path = [kf(0), kf(4000, (100.0, 0.0, 0.0))]
    cov = v2.classify_coverage(path, 0, 4000)
    assert cov["coverage"] == v2.COVERAGE_FULL
    assert cov["hold_ms"] == 0.0
    assert cov["covered_ms"] == 4000.0
    assert cov["scene_ms"] == 4000.0
    assert cov["covered_fraction"] == 1.0


def test_coverage_full_absorbs_sub_frame_shortfall():
    """One frame at 60 fps cannot be displayed, so it is not a hold."""
    path = [kf(0), kf(4000 - 10)]
    assert v2.classify_coverage(path, 0, 4000)["coverage"] == v2.COVERAGE_FULL


def test_coverage_partial_ok_for_a_short_settle():
    """300 ms is shorter than every deliberate hold this project ships
    (clip_boundary.MIN_HOLD_AFTER_ACTION_S = 0.55 s)."""
    cov = v2.classify_coverage([kf(0), kf(3700)], 0, 4000)
    assert cov["coverage"] == v2.COVERAGE_PARTIAL_OK
    assert cov["hold_ms"] == 300.0


def test_coverage_partial_bad_for_a_dead_hold():
    cov = v2.classify_coverage([kf(0), kf(2500)], 0, 4000)
    assert cov["coverage"] == v2.COVERAGE_PARTIAL_BAD
    assert cov["hold_ms"] == 1500.0
    assert cov["covered_fraction"] == pytest.approx(0.625)


def test_coverage_threshold_is_the_measured_550ms_bar():
    """The boundary is ACCEPTABLE_HOLD_MS exactly, and it is inclusive."""
    assert v2.ACCEPTABLE_HOLD_MS == 550.0
    at = v2.classify_coverage([kf(0), kf(4000 - 550)], 0, 4000)
    over = v2.classify_coverage([kf(0), kf(4000 - 551)], 0, 4000)
    assert at["coverage"] == v2.COVERAGE_PARTIAL_OK
    assert over["coverage"] == v2.COVERAGE_PARTIAL_BAD


def test_coverage_invalid_without_a_usable_path():
    assert v2.classify_coverage([], 0, 4000)["coverage"] == v2.COVERAGE_INVALID
    assert (v2.classify_coverage([kf(0)], 0, 4000)["coverage"]
            == v2.COVERAGE_INVALID)
    # A path that exists but supplies no motion inside the scene is INVALID
    # too — it is not a camera move, it is a tripod.
    assert (v2.classify_coverage([kf(0), kf(5)], 0, 4000)["coverage"]
            == v2.COVERAGE_INVALID)


def test_coverage_counts_a_late_start_as_hold_too():
    """A path that starts late freezes the HEAD of the shot — same defect."""
    cov = v2.classify_coverage([kf(1500), kf(4000)], 0, 4000)
    assert cov["hold_ms"] == 1500.0
    assert cov["coverage"] == v2.COVERAGE_PARTIAL_BAD


def test_coverage_ignores_path_outside_the_scene_window():
    """Guard margin either side is trimmed away, so overshoot is not credit
    and undershoot into the guard is not a hold."""
    cov = v2.classify_coverage([kf(-500), kf(4500)], 0, 4000)
    assert cov["covered_ms"] == 4000.0
    assert cov["coverage"] == v2.COVERAGE_FULL


# ── ITEM A: reported by compile_dense_camera ────────────────────────────────

class _WallTracer:
    """A single infinite wall at x=50 blocks anything crossing it."""
    def line_blocked(self, a, b):
        return (a[0] - 50) * (b[0] - 50) < 0 or a[0] == 50 or b[0] == 50


def test_compile_reports_coverage_numbers(tmp_path):
    res = v2.compile_dense_camera(
        [kf(0), kf(4000, (10.0, 0.0, 0.0))], 100000, tmp_path, "cov_ok",
        hz=30.0, tracer=None, scene_start_ms=0.0, scene_end_ms=4000.0)
    assert res["coverage"] == v2.COVERAGE_FULL
    assert res["scene_ms"] == 4000.0
    assert res["hold_ms"] == 0.0
    assert res["covered_fraction"] == 1.0


def test_compile_reports_partial_bad_when_geometry_shortens_the_path(tmp_path):
    """The production defect, end to end through the compiler: the camera
    crosses a wall halfway through, only the prefix survives, and the result
    must say the remainder is a dead hold."""
    res = v2.compile_dense_camera(
        [kf(0), kf(4000, (100.0, 0.0, 0.0))], 100000, tmp_path, "cov_bad",
        hz=30.0, tracer=_WallTracer(), scene_start_ms=0.0, scene_end_ms=4000.0)
    assert res["status"] in (v2.SHORTENED, v2.REJECTED)
    assert res["coverage"] in (v2.COVERAGE_PARTIAL_BAD, v2.COVERAGE_INVALID)
    assert res["hold_ms"] > v2.ACCEPTABLE_HOLD_MS


def test_compile_defaults_scene_window_to_the_authored_span(tmp_path):
    res = v2.compile_dense_camera(
        [kf(0), kf(4000, (10.0, 0.0, 0.0))], 100000, tmp_path, "cov_default",
        hz=30.0, tracer=None)
    assert res["scene_ms"] == 4000.0
    assert res["coverage"] == v2.COVERAGE_FULL


# ── ITEM B: retime_to_span ──────────────────────────────────────────────────

def test_retime_spans_the_target_and_keeps_geometry():
    src = [kf(0, (0.0, 0.0, 0.0)), kf(500, (5.0, 0.0, 0.0)),
           kf(1000, (10.0, 0.0, 0.0))]
    out = v2.retime_to_span(src, -500.0, 4500.0)
    assert out[0]["t_ms"] == -500.0
    assert out[-1]["t_ms"] == 4500.0
    assert out[1]["t_ms"] == 2000.0            # proportional, not resampled
    assert [k["pos"] for k in out] == [k["pos"] for k in src]
    assert [k["angles"] for k in out] == [k["angles"] for k in src]


def test_retime_is_a_no_op_on_a_degenerate_path():
    assert v2.retime_to_span([kf(0)], 0.0, 100.0) == [kf(0)]


def test_retimed_path_covers_the_scene():
    """The point of rung 1: the same clear positions, now covering the whole
    scene instead of stopping 40% in."""
    survivor = [kf(0), kf(1600, (16.0, 0.0, 0.0))]
    assert (v2.classify_coverage(survivor, 0, 4000)["coverage"]
            == v2.COVERAGE_PARTIAL_BAD)
    retimed = v2.retime_to_span(survivor, 0.0, 4000.0)
    assert (v2.classify_coverage(retimed, 0, 4000)["coverage"]
            == v2.COVERAGE_FULL)


# ── ITEM B: the recovery ladder in director_preview ─────────────────────────

WINDOW_START_MS, WINDOW_END_MS = 100_000, 104_000
SCENE_MS = WINDOW_END_MS - WINDOW_START_MS


def _frag() -> dict:
    """A synthetic frag. ``demo_name`` is a placeholder, never a real demo
    filename (public repo rule)."""
    return {"id": 1, "demo_name": "synthetic-coverage-fixture.dm_73",
            "content_hash": "c" * 64, "server_time_ms": 102_000,
            "window": {"start_ms": WINDOW_START_MS, "end_ms": WINDOW_END_MS},
            "attributes": {"projectile_impact_t": 102_000,
                           "projectile_path_confidence": "CONFIRMED"},
            "recognition_version": 2, "weapon_name": "ROCKET", "map": ""}


def _synthetic_path() -> dict:
    """A 1200 ms flight with enough points/flight/displacement to clear the
    projectile evidence contract (MIN_POINTS / MIN_FLIGHT_MS /
    MIN_DISPLACEMENT_U in director_preview)."""
    n = 40
    points = [[int(1200 * i / (n - 1)),
               700.0 + 800.0 * i / (n - 1), 100.0, 640.0] for i in range(n)]
    return {"launch": {"t": 102_000 - 1200, "pos": [700.0, 100.0, 640.0]},
            "impact": {"t": 102_000, "pos": [1500.0, 100.0, 640.0]},
            "points": points, "confidence": "CONFIRMED"}


@pytest.fixture
def plan(monkeypatch):
    monkeypatch.setattr(dp, "_projectile_path", lambda *a, **k: _synthetic_path())
    draft = {"camera": {**dd_mod.DEFAULT_CAMERA, "mode": "PROJECTILE"},
             "fx": {}, "look": {"look": "ORIGINAL", "show_depth": False},
             "music": None}
    p = dp.build_plan(_frag(), draft)
    assert p.camera_mode == "PROJECTILE"      # the evidence contract passed
    return p


class _Stub:
    """Scripted ``compile_dense_camera`` — the ladder is decided by coverage,
    so coverage is what the stub controls. Records every rung's keyframes."""

    def __init__(self, script):
        self.script = list(script)
        self.calls: list[list[dict]] = []

    def __call__(self, keyframes, base, gamedir, name, **kw):
        self.calls.append(list(keyframes))
        spec = self.script[min(len(self.calls) - 1, len(self.script) - 1)]
        coverage, fraction = spec
        hold = 0.0 if coverage == v2.COVERAGE_FULL else SCENE_MS * (1 - fraction)
        cut = max(2, int(len(keyframes) * fraction))
        return {"backend": "NATIVE_CAM10", "status": v2.SHORTENED,
                "coverage": coverage, "covered_fraction": fraction,
                "hold_ms": hold, "scene_ms": float(SCENE_MS),
                "covered_ms": SCENE_MS * fraction,
                "final_keyframes": list(keyframes[:cut]),
                "cam10_hash": "h", "cfg_lines": [], "cam10_path": None,
                "used_sample_count": cut,
                "original_sample_count": len(keyframes)}


def _script(monkeypatch, script):
    stub = _Stub(script)
    monkeypatch.setattr(v2, "compile_dense_camera", stub)
    return stub


def test_ladder_rung0_ships_an_already_good_path(plan, monkeypatch, tmp_path):
    stub = _script(monkeypatch, [(v2.COVERAGE_FULL, 1.0)])
    res = dp.build_camera_artifact(plan, tmp_path, "cam", tracer=object())
    assert res["camera_recovery"] == "NONE"
    assert len(stub.calls) == 1


def test_ladder_retimes_when_enough_of_the_path_survived(plan, monkeypatch,
                                                         tmp_path):
    """Rung 1. 70% survived, so the same proven-clear positions are stretched
    across the whole scene rather than held at the end."""
    stub = _script(monkeypatch, [(v2.COVERAGE_PARTIAL_BAD, 0.7),
                                 (v2.COVERAGE_FULL, 1.0)])
    res = dp.build_camera_artifact(plan, tmp_path, "cam", tracer=object())
    assert res["camera_recovery"] == "RETIMED"
    assert "retimed" in (res["camera_fallback"] or "")
    assert len(stub.calls) == 2
    # rung 1 was handed a path spanning the SAME window as the authored one
    authored, retimed = stub.calls[0], stub.calls[1]
    assert retimed[0]["t_ms"] == pytest.approx(float(authored[0]["t_ms"]))
    assert retimed[-1]["t_ms"] == pytest.approx(float(authored[-1]["t_ms"]))


def test_ladder_skips_retime_and_changes_mode_when_too_little_survived(
        plan, monkeypatch, tmp_path):
    """Rung 2. 20% survived: retiming that is a 5x stretch — a dead crawl —
    so the ladder switches to the existing ORBIT fallback instead."""
    stub = _script(monkeypatch, [(v2.COVERAGE_PARTIAL_BAD, 0.2),
                                 (v2.COVERAGE_FULL, 1.0)])
    res = dp.build_camera_artifact(plan, tmp_path, "cam", tracer=object())
    assert res["camera_recovery"] == "ORBIT"
    assert "ORBIT" in (res["camera_fallback"] or "")
    assert len(stub.calls) == 2
    # the ORBIT rung is a genuinely different path, authored over the window
    assert stub.calls[1] != stub.calls[0]
    assert min(k["t_ms"] for k in stub.calls[1]) <= -dp.GUARD_MS
    assert max(k["t_ms"] for k in stub.calls[1]) >= SCENE_MS + dp.GUARD_MS


def test_ladder_reports_honestly_when_nothing_recovers(plan, monkeypatch,
                                                       tmp_path):
    """Rung 3. Every rung fails; the shot still ships, but it says so, and
    the .cam10 left on disk is the authored path it describes."""
    stub = _script(monkeypatch, [(v2.COVERAGE_PARTIAL_BAD, 0.7)])
    res = dp.build_camera_artifact(plan, tmp_path, "cam", tracer=object())
    assert res["camera_recovery"] == "UNRECOVERED"
    assert "holds statically" in (res["camera_fallback"] or "")
    assert stub.calls[-1] == stub.calls[0]      # authored path recompiled last


def test_ladder_preserves_the_plans_own_fallback_note(monkeypatch, tmp_path):
    """A plan that already fell back (no usable projectile) must not have that
    note overwritten by the ladder's note."""
    monkeypatch.setattr(dp, "_projectile_path", lambda *a, **k: {
        "launch": {"t": 102_000, "pos": [0.0, 0.0, 0.0]},
        "impact": {"t": 102_000, "pos": [10.0, 0.0, 0.0]},
        "points": [[0, 0.0, 0.0, 0.0], [0, 10.0, 0.0, 0.0]]})
    draft = {"camera": {**dd_mod.DEFAULT_CAMERA, "mode": "PROJECTILE"},
             "fx": {}, "look": {"look": "ORIGINAL", "show_depth": False},
             "music": None}
    p = dp.build_plan(_frag(), draft)
    assert p.camera_fallback                       # the evidence contract fired
    _script(monkeypatch, [(v2.COVERAGE_PARTIAL_BAD, 0.7)])
    res = dp.build_camera_artifact(p, tmp_path, "cam", tracer=object())
    assert p.camera_fallback in res["camera_fallback"]
    assert "holds statically" in res["camera_fallback"]


def test_delivered_camera_is_never_a_silent_dead_hold(plan, monkeypatch,
                                                      tmp_path):
    """THE INVARIANT. Whatever the ladder ends up doing, a PARTIAL_BAD or
    INVALID result must carry an explanation — never a silent degrade."""
    for script in ([(v2.COVERAGE_FULL, 1.0)],
                   [(v2.COVERAGE_PARTIAL_BAD, 0.7), (v2.COVERAGE_FULL, 1.0)],
                   [(v2.COVERAGE_PARTIAL_BAD, 0.2), (v2.COVERAGE_FULL, 1.0)],
                   [(v2.COVERAGE_PARTIAL_BAD, 0.7)],
                   [(v2.COVERAGE_INVALID, 0.0)]):
        _script(monkeypatch, script)
        res = dp.build_camera_artifact(plan, tmp_path, "cam", tracer=object())
        if res["coverage"] not in (v2.COVERAGE_FULL, v2.COVERAGE_PARTIAL_OK):
            assert res["camera_fallback"], f"silent dead hold for {script}"
            assert res["camera_recovery"] == "UNRECOVERED"


def test_camera_status_line_surfaces_coverage_and_recovery():
    line = dp.camera_status_line({
        "status": v2.SHORTENED, "used_sample_count": 40,
        "original_sample_count": 100, "coverage": v2.COVERAGE_PARTIAL_BAD,
        "hold_ms": 1450.0, "camera_recovery": "UNRECOVERED",
        "camera_fallback": "camera holds statically"})
    assert "SHORTENED 40/100" in line
    assert f"cov={v2.COVERAGE_PARTIAL_BAD}" in line
    assert "hold=1450ms" in line
    assert "recovery=UNRECOVERED" in line
    assert "camera holds statically" in line


def test_no_camera_plan_reports_invalid_coverage(monkeypatch, tmp_path):
    monkeypatch.setattr(dp, "_projectile_path", lambda *a, **k: None)
    draft = {"camera": {**dd_mod.DEFAULT_CAMERA, "mode": "ORBIT"},
             "fx": {}, "look": {"look": "ORIGINAL", "show_depth": False},
             "music": None}
    p = dp.build_plan(_frag(), draft)
    assert p.camera_mode == "FPV" and not p.keyframes
    res = dp.build_camera_artifact(p, tmp_path, "cam")
    assert res["coverage"] == v2.COVERAGE_INVALID
    assert res["status"] == "NO_CAMERA"


# ── real BSP geometry ───────────────────────────────────────────────────────
# The ladder above is exercised against a scripted compiler stub and a
# synthetic wall tracer, which proves the rung ORDER but not that the rungs
# clear real Quake geometry. These run the unstubbed compiler against a map
# loaded from the staging pak00.pk3, and skip when it is unavailable.

from creative_suite.engine import camera_paths as cp

PK3 = REPO_ROOT / "output" / "demo_v2" / "_wolfcam_staging" / "baseq3" / "pak00.pk3"


@pytest.fixture(scope="module")
def real_tracer():
    if not PK3.exists():
        pytest.skip("staging pak00.pk3 not present")
    try:
        return cp.bsp_tracer("asylum", str(PK3))
    except Exception as e:
        pytest.skip(f"bsp_geometry unusable: {e}")


def test_ladder_never_ships_a_silent_dead_hold_on_real_geometry(
        plan, real_tracer, tmp_path):
    """The invariant that matters, against geometry rather than a stub: the
    delivered camera either covers the scene, settles briefly, or says why
    not. What must never happen is PARTIAL_BAD with nothing reported."""
    res = dp.build_camera_artifact(plan, tmp_path, "cam", tracer=real_tracer)
    assert res["coverage"] in (v2.COVERAGE_FULL, v2.COVERAGE_PARTIAL_OK,
                               v2.COVERAGE_PARTIAL_BAD, v2.COVERAGE_INVALID)
    if res["coverage"] in (v2.COVERAGE_FULL, v2.COVERAGE_PARTIAL_OK):
        assert res["hold_ms"] <= v2.ACCEPTABLE_HOLD_MS
    else:
        assert res.get("camera_fallback"), "a bad hold must be explained"
        assert res.get("camera_recovery") not in (None, "NONE")


def test_real_geometry_compile_reports_the_full_coverage_contract(
        plan, real_tracer, tmp_path):
    res = dp.build_camera_artifact(plan, tmp_path, "cam", tracer=real_tracer)
    for key in ("coverage", "covered_ms", "scene_ms", "hold_ms",
                "covered_fraction"):
        assert key in res, f"{key} missing from a real-geometry compile"
    assert res["scene_ms"] > 0
    assert 0.0 <= res["covered_fraction"] <= 1.0
    # hold and covered time must account for the whole scene
    assert res["covered_ms"] + res["hold_ms"] == pytest.approx(
        res["scene_ms"], abs=1.0)


def test_real_geometry_camera_status_line_is_populated(
        plan, real_tracer, tmp_path):
    res = dp.build_camera_artifact(plan, tmp_path, "cam", tracer=real_tracer)
    line = dp.camera_status_line(res)
    assert line and res["coverage"] in line
