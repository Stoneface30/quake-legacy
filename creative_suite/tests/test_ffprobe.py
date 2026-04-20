import shutil
import subprocess
from pathlib import Path

import pytest

from creative_suite.clips.ffprobe import probe_duration
from creative_suite.config import TOOLS_ROOT, Config
from creative_suite.db.migrate import migrate


def _find_ffmpeg() -> str:
    """Locate ffmpeg: PATH → creative_suite/tools/ffmpeg/ vendored install."""
    on_path = shutil.which("ffmpeg")
    if on_path:
        return on_path
    candidates = [
        TOOLS_ROOT / "ffmpeg" / "ffmpeg.exe",
        Path("G:/QUAKE_LEGACY/creative_suite/tools/ffmpeg/ffmpeg.exe"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return str(candidates[0])  # non-existent; test will skip below


FFMPEG = _find_ffmpeg()


@pytest.mark.skipif(not Path(FFMPEG).exists(), reason="ffmpeg not found")
def test_probe_duration_caches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path))
    cfg = Config()
    migrate(cfg)
    avi = tmp_path / "t.mp4"
    subprocess.check_call(
        [FFMPEG, "-f", "lavfi", "-i", "color=c=black:s=64x64:d=1.5",
         "-y", str(avi)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    d1 = probe_duration(cfg, avi)
    assert 1.3 < d1 < 1.7
    d2 = probe_duration(cfg, avi)
    assert d1 == d2
