"""Task 9.3 — gamestart.cfg writer (§4.4 max-quality cvars).

If the wolfcam launcher silently drops one of these cvars the capture
falls back to 1920×1080 / stock aniso / HUD on, and we don't find out
until we re-render 300 demos. Test every cvar appears verbatim + in
spec order.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from creative_suite.capture.gamestart import (
    MAX_QUALITY_CVARS,
    write_gamestart_cfg,
)


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def test_every_spec_cvar_written_in_order(tmp_path: Path) -> None:
    out = tmp_path / "gamestart.cfg"
    write_gamestart_cfg(
        out,
        demo_name="frag_001",
        seek_clock="8:52",
        quit_at="9:05",
        fp_view=True,
    )
    lines = _read_lines(out)

    # Every §4.4 cvar appears verbatim.
    for cvar in MAX_QUALITY_CVARS:
        assert cvar in lines, f"missing cvar: {cvar!r}"

    # And in the spec-declared order.
    indices = [lines.index(c) for c in MAX_QUALITY_CVARS]
    assert indices == sorted(indices), "cvars reordered vs spec §4.4"


def test_fp_view_writes_draw_gun_1(tmp_path: Path) -> None:
    out = tmp_path / "fp.cfg"
    write_gamestart_cfg(
        out, demo_name="d", seek_clock="0:00", quit_at="0:05", fp_view=True
    )
    assert "cg_drawGun 1" in _read_lines(out)
    assert "cg_drawGun 0" not in _read_lines(out)


def test_fl_view_writes_draw_gun_0(tmp_path: Path) -> None:
    out = tmp_path / "fl.cfg"
    write_gamestart_cfg(
        out, demo_name="d", seek_clock="0:00", quit_at="0:05", fp_view=False
    )
    assert "cg_drawGun 0" in _read_lines(out)
    assert "cg_drawGun 1" not in _read_lines(out)


def test_seekclock_video_quit_oneliner_present(tmp_path: Path) -> None:
    out = tmp_path / "s.cfg"
    write_gamestart_cfg(
        out,
        demo_name="ref_basewall",
        seek_clock="1:23",
        quit_at="1:30",
        fp_view=True,
    )
    text = out.read_text(encoding="utf-8")
    assert "seekclock 1:23" in text
    assert "video avi name :ref_basewall" in text
    assert "at 1:30 quit" in text
    # The three commands share one line (wolfcam console parses ;-separated
    # statements on one line — splitting them would skip the middle ones).
    oneliner = [ln for ln in text.splitlines() if "seekclock" in ln][0]
    assert "video avi" in oneliner and "quit" in oneliner


def test_writer_creates_missing_parent_dir(tmp_path: Path) -> None:
    nested = tmp_path / "does" / "not" / "exist" / "gamestart.cfg"
    write_gamestart_cfg(
        nested, demo_name="d", seek_clock="0:00", quit_at="0:05"
    )
    assert nested.exists()


def test_writer_rejects_injection_via_semicolon(tmp_path: Path) -> None:
    """Defensive: if the launcher is ever called with untrusted input,
    a `;` in quit_at would let the caller chain arbitrary console
    commands. Reject at the writer."""
    out = tmp_path / "bad.cfg"
    with pytest.raises(ValueError):
        write_gamestart_cfg(
            out, demo_name="d", seek_clock="0:00", quit_at="0:05; fs_game baseq3"
        )


def test_writer_rejects_empty_demo_name(tmp_path: Path) -> None:
    out = tmp_path / "bad.cfg"
    with pytest.raises(ValueError):
        write_gamestart_cfg(
            out, demo_name="", seek_clock="0:00", quit_at="0:05"
        )
