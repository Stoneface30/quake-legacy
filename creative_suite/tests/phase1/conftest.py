import pytest
from pathlib import Path
from creative_suite.engine.config import Config

@pytest.fixture
def cfg():
    return Config()

@pytest.fixture
def tmp_clip(tmp_path):
    """Create a minimal valid MP4 test clip using FFmpeg (1 second, color bar)."""
    import subprocess, shutil
    cfg = Config()
    out = tmp_path / "test_clip.mp4"
    subprocess.run([
        str(cfg.ffmpeg_bin), "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=1920x1080:r=60:d=1",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-c:v", "libx264", "-crf", "30", "-preset", "ultrafast",
        "-c:a", "aac", "-shortest", str(out)
    ], check=True, capture_output=True)
    return out
