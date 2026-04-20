"""WOLF WHISPERER ingestion — wolfcam inventory + capture scaffolding tests.

Covers:
  - WolfcamInventory scanning (empty dir, demo discovery, binary detection)
  - to_dict contract
  - write_capture_cfg / build_launch_args (delegates to capture.gamestart for
    injection validation — CS-5 rule)
  - capture_stub smoke test
"""
from __future__ import annotations

from pathlib import Path

import pytest

from creative_suite.engine.wolfcam.inventory import WolfcamInventory, scan_wolfcam
from creative_suite.engine.wolfcam.capture import (
    CaptureJob,
    build_launch_args,
    capture_stub,
    write_capture_cfg,
)


# ---------------------------------------------------------------------------
# Inventory tests
# ---------------------------------------------------------------------------


def test_scan_returns_inventory(tmp_path: Path) -> None:
    inv = scan_wolfcam(tmp_path)
    assert isinstance(inv, WolfcamInventory)


def test_scan_empty_dir_demo_count_zero(tmp_path: Path) -> None:
    inv = scan_wolfcam(tmp_path)
    assert inv.demo_count == 0


def test_scan_finds_dm73(tmp_path: Path) -> None:
    (tmp_path / "test.dm_73").write_bytes(b"\x00" * 16)
    inv = scan_wolfcam(tmp_path)
    assert inv.demo_count == 1


def test_scan_finds_dm73_nested(tmp_path: Path) -> None:
    sub = tmp_path / "demos"
    sub.mkdir()
    (sub / "frag.dm_73").write_bytes(b"\x00" * 16)
    inv = scan_wolfcam(tmp_path)
    assert inv.demo_count == 1


def test_scan_binary_not_found(tmp_path: Path) -> None:
    inv = scan_wolfcam(tmp_path)
    assert inv.is_usable is False


def test_scan_finds_binary(tmp_path: Path) -> None:
    exe = tmp_path / "wolfcamql.exe"
    exe.write_bytes(b"MZ")
    inv = scan_wolfcam(tmp_path)
    assert inv.is_usable is True
    assert inv.binary_path == exe


def test_scan_finds_binary_wolfcam_ql_subdir(tmp_path: Path) -> None:
    """Exe inside wolfcam-ql/ subdirectory should be found."""
    inner = tmp_path / "wolfcam-ql"
    inner.mkdir()
    exe = inner / "wolfcamql.exe"
    exe.write_bytes(b"MZ")
    inv = scan_wolfcam(tmp_path)
    assert inv.is_usable is True


def test_to_dict_has_required_keys(tmp_path: Path) -> None:
    inv = scan_wolfcam(tmp_path)
    d = inv.to_dict()
    for key in ("wolfcam_root", "binary_exists", "demo_count", "cfg_count", "script_count"):
        assert key in d, f"missing key: {key!r}"


def test_to_dict_root_is_string(tmp_path: Path) -> None:
    inv = scan_wolfcam(tmp_path)
    assert isinstance(inv.to_dict()["wolfcam_root"], str)


def test_scan_counts_cfg_files(tmp_path: Path) -> None:
    (tmp_path / "cap.cfg").write_text("test", encoding="utf-8")
    (tmp_path / "other.cfg").write_text("test", encoding="utf-8")
    inv = scan_wolfcam(tmp_path)
    assert inv.to_dict()["cfg_count"] == 2


# ---------------------------------------------------------------------------
# Capture cfg tests
# ---------------------------------------------------------------------------


def _make_job(tmp_path: Path, fake_exe: bool = True) -> CaptureJob:
    demo = tmp_path / "frag.dm_73"
    demo.write_bytes(b"\x00" * 16)
    out_dir = tmp_path / "output"
    exe = tmp_path / "wolfcamql.exe"
    if fake_exe:
        exe.write_bytes(b"MZ")
    return CaptureJob(
        demo_path=demo,
        output_dir=out_dir,
        seek_clock="8:52",
        stop_clock="9:05",
        output_name="test",
        wolfcam_binary=exe,
    )


def test_write_capture_cfg_creates_file(tmp_path: Path) -> None:
    job = _make_job(tmp_path)
    cfg_path = write_capture_cfg(job)
    assert cfg_path.exists()


def test_capture_cfg_content(tmp_path: Path) -> None:
    job = _make_job(tmp_path)
    cfg_path = write_capture_cfg(job)
    text = cfg_path.read_text(encoding="utf-8")
    # The oneliner must contain all three commands on one line (wolfcam idiom).
    oneliner = next(ln for ln in text.splitlines() if "seekclock" in ln)
    assert "seekclock 8:52" in oneliner
    assert "video avi name :test" in oneliner
    assert "at 9:05 quit" in oneliner


def test_cfg_injection_rejected_semicolon(tmp_path: Path) -> None:
    """CS-5: semicolon in seek_clock must raise ValueError."""
    job = _make_job(tmp_path)
    job.seek_clock = "8:52; rm -rf /"
    with pytest.raises(ValueError):
        write_capture_cfg(job)


def test_cfg_injection_rejected_newline(tmp_path: Path) -> None:
    """CS-5: newline in output_name must raise ValueError."""
    job = _make_job(tmp_path)
    job.output_name = "test\nmalicious"
    with pytest.raises(ValueError):
        write_capture_cfg(job)


def test_build_launch_args_structure(tmp_path: Path) -> None:
    job = _make_job(tmp_path)
    cfg_path = write_capture_cfg(job)
    args = build_launch_args(job, cfg_path)
    assert args[0] == str(job.wolfcam_binary)
    assert "+set" in args
    assert "fs_homepath" in args
    assert "+exec" in args
    assert "+demo" in args


def test_capture_stub_returns_dict(tmp_path: Path) -> None:
    job = _make_job(tmp_path)
    result = capture_stub(job)
    assert result["status"] == "stub"
    assert "cfg_written" in result
    assert "launch_args" in result


def test_capture_stub_cfg_actually_written(tmp_path: Path) -> None:
    job = _make_job(tmp_path)
    result = capture_stub(job)
    assert Path(result["cfg_written"]).exists()
