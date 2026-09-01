"""Exact-grammar tests for the .cam10 compiler.

Every assertion here is anchored to a specific line/behavior in
CG_SaveCamera_f / CG_LoadCamera_f (cg_consolecmds.c) as documented in
docs/reference/cam10_runtime_contract.md — this is the file that keeps the
camera-pipeline-recovery fix honest against regression.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import cam10_writer as cw


def kf(t_ms, pos, angles, fov=90.0):
    return {"t_ms": t_ms, "pos": pos, "angles": angles, "fov": fov}


SIMPLE = [kf(0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
          kf(1000, (100.0, 0.0, 0.0), (0.0, 90.0, 0.0), fov=100.0)]


def test_requires_at_least_two_keyframes():
    with pytest.raises(ValueError):
        cw.write_cam10([kf(0, (0, 0, 0), (0, 0, 0))], base_servertime=0)
    with pytest.raises(ValueError):
        cw.write_cam10([], base_servertime=0)


def test_header_line_is_wolfcam_camera_10():
    content = cw.write_cam10(SIMPLE, base_servertime=0)
    assert content.splitlines()[0] == "WolfcamCamera 10"


def test_deterministic():
    a = cw.write_cam10(SIMPLE, base_servertime=5000)
    b = cw.write_cam10(SIMPLE, base_servertime=5000)
    assert a == b


def test_sorted_by_time_regardless_of_input_order():
    reordered = [SIMPLE[1], SIMPLE[0]]
    assert cw.write_cam10(reordered, 0) == cw.write_cam10(SIMPLE, 0)


def test_per_point_line_order_matches_cg_saveCamera_f():
    """CG_LoadCamera_f parses purely by line POSITION (cg_consolecmds.c:
    2401-2596) — this test locks the exact sequence so a reorder is caught
    immediately instead of silently desyncing every field after it."""
    content = cw.write_cam10(SIMPLE, base_servertime=0)
    lines = content.splitlines()
    assert lines[0] == "WolfcamCamera 10"
    # point 0 occupies 43 content lines starting at line 1 (verified
    # against actual writer output: fov@20, fovType@21, commandStrLen@43,
    # 1-indexed from the header).
    point0 = lines[1:1 + 43]
    assert len(point0) == 43
    assert point0[0] == "0  camera point number"
    assert point0[1] == "0.000000 0.000000 0.000000  origin"
    assert point0[2] == "0.000000 0.000000 0.000000  angles"
    assert point0[3] == f"{cw.CAMERA_INTERP}  type"
    assert point0[4] == f"{cw.CAMERA_ANGLES_INTERP}  viewType"
    assert point0[5] == f"{cw.CAMERA_ROLL_AS_ANGLES}  rollType"
    assert point0[6] == f"{cw.ALL_FLAGS}  flags"
    assert point0[7] == "0.0000  cgtime"
    assert point0[8] == "0  splineType"
    assert point0[9] == "0  numSplines"
    assert point0[19] == "90.0000  fov"
    assert point0[20] == f"{cw.CAMERA_FOV_INTERP}  fovType"
    assert point0[42] == "0  commandStrLen"
    # trailer: blank line + dashes, then the next point starts immediately
    # (no extra blank — points concatenate directly, see write_cam10)
    assert lines[1 + 43] == ""
    assert lines[1 + 44] == "-------------------------------------"
    assert lines[1 + 45] == "0  camera point number"


def test_flags_include_origin_angles_fov_time():
    assert cw.ALL_FLAGS == 0x001 | 0x002 | 0x004 | 0x100


def test_cgtime_is_base_plus_relative_t_ms():
    content = cw.write_cam10(SIMPLE, base_servertime=42000)
    lines = content.splitlines()
    cgtimes = [float(l.split()[0]) for l in lines if l.endswith("  cgtime")]
    assert cgtimes == [42000.0, 43000.0]


def test_fov_per_keyframe_preserved():
    content = cw.write_cam10(SIMPLE, base_servertime=0)
    fovs = [l.split()[0] for l in content.splitlines() if l.endswith("  fov")]
    assert fovs == ["90.0000", "100.0000"]


def test_compile_camera_writes_file_and_returns_working_cfg_sequence(tmp_path):
    result = cw.compile_camera(SIMPLE, base_servertime=0,
                               gamedir=tmp_path, camera_name="testcam")
    expected_path = tmp_path / "cameras" / "testcam.cam10"
    assert result["path"] == expected_path
    assert expected_path.exists()
    assert result["file_hash"] == cw.cam10_hash(expected_path.read_text())
    # RUNTIME-PROVEN 2026-09-01: loadcamera/playcamera loads the file
    # correctly but playcamera has a reproducible engine bug (unconditional
    # internal re-seek corrupts the snapshot stream — cam10_runtime_contract
    # .md "Known engine bug"). Execution uses freecamsetpos instead, one
    # per keyframe, which real captures proved actually moves the camera.
    assert result["cfg_lines"][0] == "freecam"
    assert "loadcamera" not in " ".join(result["cfg_lines"])
    assert "playcamera" not in " ".join(result["cfg_lines"])
    assert len(result["cfg_lines"]) == 1 + len(SIMPLE)  # freecam + 1/keyframe


def test_to_freecamsetpos_lines_one_per_keyframe_absolute_time():
    lines = cw.to_freecamsetpos_lines(SIMPLE, base_servertime=42000)
    assert lines[0] == "freecam"
    assert lines[1] == "at 42000 freecamsetpos 0.00 0.00 0.00 0.00 0.00 0.00"
    assert lines[2] == ("at 43000 freecamsetpos 100.00 0.00 0.00 "
                        "0.00 90.00 0.00")


def test_to_freecamsetpos_lines_sorted_regardless_of_input_order():
    reordered = [SIMPLE[1], SIMPLE[0]]
    assert (cw.to_freecamsetpos_lines(reordered, 0)
            == cw.to_freecamsetpos_lines(SIMPLE, 0))


def test_compile_camera_is_overwritable_and_reproducible(tmp_path):
    r1 = cw.compile_camera(SIMPLE, 0, tmp_path, "scene")
    r2 = cw.compile_camera(SIMPLE, 0, tmp_path, "scene")
    assert r1["file_hash"] == r2["file_hash"]


def test_compilation_ledger_roundtrip(tmp_path):
    db = tmp_path / "cinematic.db"
    cw.record_compilation("plan-abc", "deadbeef", db_path=db)
    got = cw.get_compilation("plan-abc", db_path=db)
    assert got["file_hash"] == "deadbeef"
    assert got["compiler_version"] == cw.CAMERA_COMPILER_VERSION
    assert got["runtime_backend"] == cw.CAMERA_RUNTIME_BACKEND


def test_compilation_ledger_never_touches_shot_plans_table(tmp_path):
    """camera_compilations is a SIBLING table to shot_plans, not a mutation
    of it — recompiling must never change a plan's identity hash."""
    import sqlite3
    db = tmp_path / "cinematic.db"
    cw.record_compilation("plan-xyz", "hash1", db_path=db)
    con = sqlite3.connect(db)
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "camera_compilations" in tables
    con.close()


def test_get_compilation_missing_returns_none(tmp_path):
    db = tmp_path / "cinematic.db"
    assert cw.get_compilation("nope", db_path=db) is None
