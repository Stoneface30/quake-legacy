"""concat_copy must copy only when the inputs genuinely agree.

Stream-copying mismatched H.264 is what silently lost 78 s of a 290 s reel
("Invalid NAL unit size"). The copy path is safe for the xfade GROUP files
because they all come from one fixed encoder setting -- so the uniformity test
is the whole safety argument, and it has to be checked rather than assumed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from creative_suite.engine import render_highlight as rh


class _Cfg:
    ffmpeg_bin = "ffmpeg"
    ffprobe_bin = "ffprobe"


def test_mismatched_streams_fall_back_to_reencode(monkeypatch, tmp_path):
    sigs = {"a.mov": "h264,High,1920,1080,yuv420p,60/1",
            "b.mov": "h264,Main,1280,720,yuv420p,30/1"}
    monkeypatch.setattr(rh, "_stream_sig", lambda p, c: sigs[Path(p).name])

    called = {}

    def fake_hard(segments, dst, cfg):
        called["hard"] = [Path(s).name for s in segments]
        return dst

    monkeypatch.setattr(rh, "concat_hard", fake_hard)
    monkeypatch.setattr(rh.subprocess, "run",
                        lambda *a, **k: pytest.fail("must not stream-copy"))

    out = tmp_path / "body.mov"
    rh.concat_copy([tmp_path / "a.mov", tmp_path / "b.mov"], out, _Cfg())
    assert called["hard"] == ["a.mov", "b.mov"]


def test_unprobeable_input_falls_back(monkeypatch, tmp_path):
    """A stream we cannot probe is not proof of a match."""
    monkeypatch.setattr(rh, "_stream_sig", lambda p, c: None)
    called = {}
    monkeypatch.setattr(rh, "concat_hard",
                        lambda s, d, c: called.setdefault("hard", True) or d)
    monkeypatch.setattr(rh.subprocess, "run",
                        lambda *a, **k: pytest.fail("must not stream-copy"))
    rh.concat_copy([tmp_path / "a.mov", tmp_path / "b.mov"],
                   tmp_path / "o.mov", _Cfg())
    assert called["hard"]


def test_uniform_streams_use_stream_copy(monkeypatch, tmp_path):
    monkeypatch.setattr(rh, "_stream_sig",
                        lambda p, c: "h264,High,1920,1080,yuvj420p,60/1")
    monkeypatch.setattr(rh, "concat_hard",
                        lambda s, d, c: pytest.fail("should not re-encode"))

    seen = {}

    class _R:
        returncode = 0

    def fake_run(cmd, **k):
        seen["cmd"] = cmd
        Path(cmd[-1]).write_bytes(b"x")
        return _R()

    monkeypatch.setattr(rh.subprocess, "run", fake_run)
    out = tmp_path / "body.mov"
    rh.concat_copy([tmp_path / "a.mov", tmp_path / "b.mov"], out, _Cfg())

    assert "-c" in seen["cmd"] and "copy" in seen["cmd"]
    assert "libx264" not in seen["cmd"]
    listed = (tmp_path / "_concat_copy.txt").read_text(encoding="utf-8")
    assert listed.count("file '") == 2


def test_copy_failure_falls_back_rather_than_shipping_nothing(monkeypatch,
                                                              tmp_path):
    monkeypatch.setattr(rh, "_stream_sig", lambda p, c: "same")
    called = {}
    monkeypatch.setattr(rh, "concat_hard",
                        lambda s, d, c: called.setdefault("hard", True) or d)

    class _R:
        returncode = 1

    monkeypatch.setattr(rh.subprocess, "run", lambda *a, **k: _R())
    rh.concat_copy([tmp_path / "a.mov"], tmp_path / "o.mov", _Cfg())
    assert called["hard"]
