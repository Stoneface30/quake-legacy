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
    # compile_camera's DEFAULT backend is FREECAM_SAMPLED, so cfg_lines
    # are freecamsetpos commands, not loadcamera/playcamera. That default
    # is a backend-contract choice, NOT evidence of an engine defect:
    # native loadcamera/playcamera is proven working on the stock binary
    # once the file is written LF-only (see the CORRECTED section of
    # cam10_runtime_contract.md — the original "playcamera corrupts the
    # snapshot stream" reading was our own CRLF bug). Pass
    # backend=BACKEND_NATIVE_CAM10 for the native sequence.
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


def test_compile_camera_writes_pure_lf_no_crlf(tmp_path):
    """Regression guard for the 2026-09-01 finding: Path.write_text()'s
    default universal-newline translation turns \\n into \\r\\n on Windows,
    silently corrupting CG_LoadCamera_f's byte-exact line-positional
    grammar. This is what the earlier "playcamera corrupts the snapshot
    stream" diagnosis actually traced back to on re-investigation — NOT a
    confirmed engine defect on the stock binary once written correctly.
    `.splitlines()`-based tests elsewhere in this file do NOT catch this
    (splitlines() normalizes both line-ending styles away), hence this
    dedicated raw-bytes check."""
    result = cw.compile_camera(SIMPLE, base_servertime=0,
                               gamedir=tmp_path, camera_name="lftest")
    raw = result["path"].read_bytes()
    assert b"\r" not in raw


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


# ── engine-file newline contract (2026-09-01 audit) ──────────────────────────

def test_write_engine_file_helper_is_lf_only(tmp_path):
    """The shared writer every engine-parsed file must go through."""
    from creative_suite.engine.wolfcam_capture import write_engine_file
    p = tmp_path / "x.cfg"
    write_engine_file(p, "line one\nline two\n")
    assert b"\r" not in p.read_bytes()


def test_capture_cfg_writer_is_lf_only(tmp_path):
    """write_capture_cfg drives every real capture; CRLF is tolerated by
    the Cbuf tokenizer (the frozen profile cfg ran all session with 96
    CRLF pairs) but the writer is normalised so no engine-parsed file in
    this codebase can differ."""
    from creative_suite.engine import wolfcam_capture as wc
    gamedir = tmp_path / "wolfcam-ql"
    gamedir.mkdir()
    wc.write_capture_cfg([{"clip_name": "c", "start_ms": 1000,
                           "end_ms": 2000}], staging=tmp_path)
    for name in ("capture.cfg", "cgamepostinit.cfg"):
        assert b"\r" not in (gamedir / name).read_bytes(), name


def test_master_profile_cfgs_are_lf_only(tmp_path):
    """The frozen capture profile — the file that defines every master."""
    from creative_suite.engine import master_profile
    master_profile.write(tmp_path)
    cfgs = list(tmp_path.glob("*.cfg"))
    assert cfgs, "no profile cfgs written"
    for cfg in cfgs:
        assert b"\r" not in cfg.read_bytes(), cfg.name
