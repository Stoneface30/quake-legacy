"""Tests for the VIS-1 post-render capture hook.

The module render_part_v6 imports was never written, so every render logged
"[visual-record] import failed ... skipping". These tests pin both the import
contract and the privacy constraint that keeps opponent nicknames out of the
public repo.
"""
from pathlib import Path

import pytest

from creative_suite.engine import visual_record
from creative_suite.engine.config import Config


def test_render_pipeline_import_path_resolves():
    """render_part_v6 imports exactly this symbol; it must exist."""
    from creative_suite.engine.visual_record import safe_capture
    assert callable(safe_capture)


def test_never_samples_into_body_content():
    """Rule P1-N: content starts at 13 s. Sampling past it grabs HUD nicknames."""
    assert visual_record.PRE_CONTENT_OFFSET_S == 13.0
    assert all(t < visual_record.PRE_CONTENT_OFFSET_S
               for t in visual_record.SAFE_GRAB_TIMES), (
        "a grab time reaching body content would put an opponent nickname "
        "into the public repo"
    )


def test_safe_capture_swallows_missing_file(tmp_path, capsys):
    out = visual_record.safe_capture(tmp_path / "nope.mp4", 4, Config())
    assert out == []
    assert "capture failed" in capsys.readouterr().out


def test_capture_raises_on_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        visual_record.capture(tmp_path / "nope.mp4", 4, Config())


def test_capture_writes_frames_and_note(tmp_path, monkeypatch):
    src = tmp_path / "part.mp4"
    src.write_bytes(b"\0")
    out_dir = tmp_path / "vr"

    def fake_run(cmd, **_):
        Path(cmd[-1]).write_bytes(b"png")

        class _R:
            returncode = 0
            stderr = ""
        return _R()

    monkeypatch.setattr(visual_record.subprocess, "run", fake_run)
    written = visual_record.capture(src, 4, Config(), out_dir=out_dir)

    assert len(written) == len(visual_record.SAFE_GRAB_TIMES)
    assert all(p.exists() for p in written)
    note = (out_dir / "AUTO_part04.md").read_text(encoding="utf-8")
    assert "public repo" in note
