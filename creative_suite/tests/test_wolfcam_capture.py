"""Capture engine tests: cfg generation, CS-5 guard, mock capture, QA."""
import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import capture_qa, wolfcam_capture as wc


@pytest.fixture()
def staging(tmp_path):
    (tmp_path / "wolfcam-ql").mkdir()
    return tmp_path


def test_cfg_uses_raw_servertime_only(staging):
    cfg = wc.write_capture_cfg(
        [{"clip_name": "c00001", "start_ms": 150000, "end_ms": 165000}],
        staging)
    assert f"seekservertime {150000 - wc.SEEK_SETTLE_MS}" in cfg
    assert "at 150000 video avi name c00001" in cfg
    assert "at 165000 stopvideo" in cfg
    assert "quit" in cfg
    assert "seekclock" not in cfg  # display clock is never capture truth


def test_cfg_chains_multiple_windows(staging):
    cfg = wc.write_capture_cfg(
        [{"clip_name": "c2", "start_ms": 300000, "end_ms": 310000},
         {"clip_name": "c1", "start_ms": 100000, "end_ms": 110000}],
        staging)
    # sorted ascending, second window seeks after the first stops
    assert cfg.index("c1") < cfg.index("c2")
    t = 110000 + wc.INTER_WINDOW_MS
    assert f"at {t} seekservertime {300000 - wc.SEEK_SETTLE_MS}" in cfg
    # exactly one quit, after the last stopvideo
    assert cfg.count("quit") == 1
    assert cfg.rindex("stopvideo") < cfg.rindex("quit")


def test_cfg_injection_rejected(staging):
    with pytest.raises(wc.CfgInjectionError):
        wc.write_capture_cfg(
            [{"clip_name": "x; quit", "start_ms": 0, "end_ms": 1000}], staging)


def test_cgamepostinit_hook_written(staging):
    wc.write_capture_cfg(
        [{"clip_name": "c1", "start_ms": 0, "end_ms": 1000}], staging)
    hook = (staging / "wolfcam-ql" / "cgamepostinit.cfg").read_text()
    assert hook.strip() == "exec capture.cfg"


def test_mock_capture_produces_qa_passing_avi(staging, monkeypatch):
    monkeypatch.setenv("CS_CAPTURE_MOCK", "1")
    windows = [{"clip_name": "c00042", "start_ms": 10000, "end_ms": 16000}]
    res = wc.capture_demo("d0001", windows, staging)
    assert res["ok"], res
    avi = res["avis"]["c00042"]
    tech = capture_qa.technical_qa(avi, 6.0)
    assert tech["pass"], tech["reasons"]


def test_semantic_qa_flags():
    assert capture_qa.semantic_qa(10.0, [5000]) == []
    assert capture_qa.FLAG_START in capture_qa.semantic_qa(10.0, [100])
    assert capture_qa.FLAG_END in capture_qa.semantic_qa(10.0, [9800])
    assert capture_qa.FLAG_OUTSIDE in capture_qa.semantic_qa(10.0, [15000])
    assert capture_qa.FLAG_CLUTCH in capture_qa.semantic_qa(
        10.0, [5000], clutch_span_ms=(0, 12000))


def test_frag_offset_math_roundtrip():
    # charter §13: frag_offset = frag_serverTime - capture_start_serverTime
    capture_start, frag_times = 198275, [203275, 205500]
    offsets = [t - capture_start for t in frag_times]
    assert offsets == [5000, 7225]
    assert [capture_start + o for o in offsets] == frag_times


def test_wolfcam_cmd_uses_readonly_ql_dir(staging):
    cmd = wc.wolfcam_cmd("d0001", staging)
    i = cmd.index("fs_quakelivedir")
    assert "Quake Live" in cmd[i + 1]
    assert "+demo" in cmd and cmd[cmd.index("+demo") + 1] == "d0001"


def test_stage_demo_safe_name(tmp_path):
    (tmp_path / "wolfcam-ql" / "demos").mkdir(parents=True)
    src = tmp_path / "Demo (788) - 341;.dm_73"
    src.write_bytes(b"x" * 100)
    safe = wc.stage_demo(src, 7, tmp_path)
    assert safe.startswith("d") and len(safe) == 11  # content-hash name
    assert ";" not in safe and " " not in safe
    assert (tmp_path / "wolfcam-ql" / "demos" / f"{safe}.dm_73").exists()


def test_capture_lock_blocks_second_writer(tmp_path, monkeypatch):
    from creative_suite.engine import capture_batch_run as cbr
    monkeypatch.setattr(cbr, "LOCK", tmp_path / "_capture.lock")
    cbr.acquire_lock()
    assert (tmp_path / "_capture.lock").read_text() == str(os.getpid())
    with pytest.raises(SystemExit):
        cbr.acquire_lock()      # same live pid counts as a running writer
    cbr.release_lock()
    assert not (tmp_path / "_capture.lock").exists()


def test_stage_demo_names_are_content_derived(tmp_path):
    (tmp_path / "wolfcam-ql" / "demos").mkdir(parents=True)
    a = tmp_path / "A.dm_73"
    b = tmp_path / "B.dm_73"
    a.write_bytes(b"alpha" * 100)
    b.write_bytes(b"bravo" * 100)
    sa = wc.stage_demo(a, 1, tmp_path)
    sb = wc.stage_demo(b, 1, tmp_path)   # same index MUST NOT collide
    assert sa != sb
    assert wc.stage_demo(a, 9, tmp_path) == sa  # stable across runs/indices
