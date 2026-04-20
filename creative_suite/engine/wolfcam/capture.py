"""
WolfcamQL capture automation — wolfcam subpackage entry point.

For the max-quality cfg writer (§4.4 cvars, CS-5 injection guard) see
``creative_suite.capture.gamestart``.  This module provides the higher-level
``CaptureJob`` dataclass and launch-arg builder that the Phase 2 per-frag
launcher will use, plus a ``capture_stub`` for offline testing.

Recording window pattern (CLAUDE.md):
    Write gamestart.cfg:
      seekclock 8:52; video avi name :demoname; at 9:05 quit
    Launch:
      wolfcamql.exe +set fs_homepath <out_dir> +exec cap.cfg +demo demo.dm_73
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Delegate cfg writing + injection validation to the authoritative module.
from creative_suite.capture.gamestart import write_gamestart_cfg


@dataclass
class CaptureJob:
    demo_path: Path
    output_dir: Path
    seek_clock: str      # e.g. "8:52"
    stop_clock: str      # e.g. "9:05"
    output_name: str     # filename stem (no extension, injected as demo_name)
    wolfcam_binary: Path
    fp_view: bool = True


def write_capture_cfg(job: CaptureJob) -> Path:
    """Write the wolfcamql capture cfg and return its path.

    Delegates to ``creative_suite.capture.gamestart.write_gamestart_cfg``
    which enforces CS-5 injection guards on all user-influenced strings.
    """
    job.output_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = job.output_dir / "cap.cfg"
    write_gamestart_cfg(
        cfg_path,
        demo_name=job.output_name,
        seek_clock=job.seek_clock,
        quit_at=job.stop_clock,
        fp_view=job.fp_view,
    )
    return cfg_path


def build_launch_args(job: CaptureJob, cfg_path: Path) -> list[str]:
    """Return the wolfcamql argv list for this job."""
    return [
        str(job.wolfcam_binary),
        "+set", "fs_homepath", str(job.output_dir),
        "+exec", cfg_path.name,
        "+demo", str(job.demo_path),
    ]


def capture_stub(job: CaptureJob) -> dict:
    """Write the cfg but do NOT launch wolfcamql.

    Used for offline testing and CI (CS_PREVIEW_MOCK pattern).
    Returns a summary dict for logging.
    """
    cfg_path = write_capture_cfg(job)
    args = build_launch_args(job, cfg_path)
    return {
        "status": "stub",
        "cfg_written": str(cfg_path),
        "launch_args": args,
        "message": "Stub capture — wolfcamql launch skipped",
    }
