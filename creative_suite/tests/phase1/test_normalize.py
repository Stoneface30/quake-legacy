import pytest
from creative_suite.engine.normalize import normalize_clip
from pathlib import Path

def test_normalize_produces_mp4(tmp_clip, cfg, tmp_path):
    out = tmp_path / "normalized.mp4"
    normalize_clip(tmp_clip, out, cfg)
    assert out.exists()
    assert out.stat().st_size > 0

def test_normalize_output_is_cfr_60fps(tmp_clip, cfg, tmp_path):
    import subprocess, json
    out = tmp_path / "normalized.mp4"
    normalize_clip(tmp_clip, out, cfg)
    result = subprocess.run([
        str(cfg.ffprobe_bin), "-v", "quiet",
        "-print_format", "json", "-show_streams", str(out)
    ], capture_output=True, text=True)
    data = json.loads(result.stdout)
    for stream in data["streams"]:
        if stream["codec_type"] == "video":
            fps_str = stream["r_frame_rate"]
            num, den = fps_str.split("/")
            fps = int(num) / int(den)
            assert abs(fps - 60) < 1, f"Expected 60fps, got {fps}"

def test_already_normalized_skips(tmp_clip, cfg, tmp_path, monkeypatch):
    # I8 fix: use monkeypatch to assert subprocess.run is NOT called on second normalize
    out = tmp_path / "norm.mp4"
    normalize_clip(tmp_clip, out, cfg)
    assert out.exists()

    call_count = {"n": 0}
    import subprocess as sp
    original_run = sp.run
    def counting_run(cmd, **kwargs):
        call_count["n"] += 1
        return original_run(cmd, **kwargs)

    monkeypatch.setattr(sp, "run", counting_run)
    normalize_clip(tmp_clip, out, cfg)  # should skip re-encode, only ffprobe validation allowed
    assert call_count["n"] <= 1, "Should skip re-encode when output already exists (ffprobe validation allowed)"
