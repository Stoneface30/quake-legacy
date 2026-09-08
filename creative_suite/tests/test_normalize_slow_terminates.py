"""Regression: slow-mo normalization must terminate.

_audio_filter() appends `apad` for slow clips, which pads audio INDEFINITELY.
`-shortest` was only added on the speedup branch, so a slow normalize never
reached EOF — ffmpeg encoded silence until the disk filled. Observed in the
wild as a single 6.3 s clip consuming 700+ CPU-seconds and a 69 MB .partial.

Video after setpts=2.0*PTS is longer than the natural-rate audio, so `apad`
plus `-shortest` is the correct pair: audio is padded to reach video length,
and the mux stops at the (finite) video stream.
"""
from pathlib import Path

from creative_suite.engine import normalize
from creative_suite.engine.config import Config


def _cmd_for(monkeypatch, tmp_path, **kw) -> list[str]:
    """Capture the ffmpeg argv normalize_clip would run, without running it."""
    captured: dict = {}

    class _R:
        returncode = 0
        stderr = ""

    def fake_run(cmd, **_):
        captured["cmd"] = cmd
        # Emulate ffmpeg writing a valid file so normalize_clip proceeds.
        Path(cmd[-1]).write_bytes(b"\0" * 4096)
        return _R()

    monkeypatch.setattr(normalize.subprocess, "run", fake_run)
    monkeypatch.setattr(normalize, "_ffprobe_valid", lambda *a, **k: True)

    src = tmp_path / "src.avi"
    src.write_bytes(b"\0")
    normalize.normalize_clip(src, tmp_path / "out.mp4", Config(), **kw)
    return captured["cmd"]


def test_slow_uses_apad(monkeypatch, tmp_path):
    cmd = _cmd_for(monkeypatch, tmp_path, slow=True)
    af = cmd[cmd.index("-af") + 1]
    assert "apad" in af, "slow clips pad audio to reach the stretched video length"


def test_slow_passes_shortest(monkeypatch, tmp_path):
    """The bug: apad is infinite, so without -shortest ffmpeg never ends."""
    cmd = _cmd_for(monkeypatch, tmp_path, slow=True)
    assert "-shortest" in cmd, "apad without -shortest never terminates"


def test_speedup_still_passes_shortest(monkeypatch, tmp_path):
    cmd = _cmd_for(monkeypatch, tmp_path, speedup=True)
    assert "-shortest" in cmd


def test_plain_normalize_has_no_apad(monkeypatch, tmp_path):
    """A plain pass must not gain an unbounded pad."""
    cmd = _cmd_for(monkeypatch, tmp_path)
    af = cmd[cmd.index("-af") + 1]
    assert "apad" not in af
