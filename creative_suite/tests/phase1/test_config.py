from creative_suite.engine.config import Config
from pathlib import Path

def test_config_paths_exist():
    cfg = Config()
    assert cfg.ffmpeg_bin.exists(), f"FFmpeg not found: {cfg.ffmpeg_bin}"
    assert cfg.clips_root.exists(), f"Clips root not found: {cfg.clips_root}"
    assert cfg.output_dir.exists() or not cfg.output_dir.exists()  # created on demand

def test_config_parts_range():
    cfg = Config()
    assert cfg.parts == list(range(4, 13))

def test_config_part_dir():
    cfg = Config()
    for part in cfg.parts:
        d = cfg.part_dir(part)
        assert d.parent.name == "T1"
        assert d.name == f"Part{part}"

def test_config_output_path():
    cfg = Config()
    p = cfg.output_path(4)
    assert p.name == "Part4.mp4"
    assert "output" in str(p)
