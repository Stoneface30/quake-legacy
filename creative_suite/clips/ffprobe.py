from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from creative_suite.config import REPO_ROOT, Config
from creative_suite.db.migrate import connect


def _ffprobe_binary() -> str:
    """PATH → repo tools dir → absolute vendored install. Worktrees live
    deeper than the main repo, so `parent.parent.parent` misses the vendored
    install; use `REPO_ROOT` (via config) and a hard-coded fallback."""
    on_path = shutil.which("ffprobe")
    if on_path:
        return on_path
    for cand in (
        REPO_ROOT / "tools" / "ffmpeg" / "ffprobe.exe",
        Path("G:/QUAKE_LEGACY/tools/ffmpeg/ffprobe.exe"),
    ):
        if cand.exists():
            return str(cand)
    return "ffprobe"  # last resort — will raise when subprocess runs


def _run_ffprobe(avi: Path) -> float:
    ffprobe = _ffprobe_binary()
    out = subprocess.check_output([
        ffprobe, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", str(avi),
    ])
    return float(json.loads(out)["format"]["duration"])


def probe_duration(cfg: Config, avi: Path) -> float:
    key = str(avi)
    con = connect(cfg)
    try:
        row = con.execute(
            "SELECT duration_s FROM clip_durations WHERE avi_path = ?",
            (key,),
        ).fetchone()
        if row is not None:
            return float(row["duration_s"])
        d = _run_ffprobe(avi)
        con.execute(
            "INSERT OR REPLACE INTO clip_durations(avi_path, duration_s) VALUES (?, ?)",
            (key, d),
        )
        return d
    finally:
        con.close()
