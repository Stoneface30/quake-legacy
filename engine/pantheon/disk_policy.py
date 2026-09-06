"""Disk policy — three thresholds, because three kinds of write.

The first performance index filled a drive at 94 GB and took every write on
that drive down with it, including a human's review verdicts, which are a
few hundred bytes. One threshold for everything would either let a capture
fill the disk or make the reviewer unusable while a capture merely *could*
not fit. So:

    REVIEW_DB_WRITE_SAFE   a verdict, a note, a tag: tiny; only an almost
                           full disk blocks it
    RENDER_JOB_SAFE        one capture or render job: the job's expected
                           output plus a safety margin must fit, or the job
                           is DEFERRED (not failed)
    LARGE_BUILD_SAFE       an index or geography build: needs real headroom

`free_bytes()` is `shutil.disk_usage`; nothing here spawns a process or
opens a window. Every number is a default that an operator can raise through
the environment; none can be lowered below the review floor.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

MB = 1024 ** 2
GB = 1024 ** 3

# Defaults, overridable by environment (bytes).
REVIEW_DB_WRITE_SAFE = int(os.getenv("PANTHEON_DISK_REVIEW_SAFE", 64 * MB))
RENDER_MARGIN = int(os.getenv("PANTHEON_DISK_RENDER_MARGIN", 2 * GB))
RENDER_EXPECTED_DEFAULT = int(os.getenv("PANTHEON_DISK_RENDER_EXPECTED", 1500 * MB))
LARGE_BUILD_SAFE = int(os.getenv("PANTHEON_DISK_BUILD_SAFE", 20 * GB))


@dataclass(frozen=True)
class DiskVerdict:
    kind: str
    path: str
    free_bytes: int
    required_bytes: int
    ok: bool

    @property
    def reason(self) -> str:
        state = "ok" if self.ok else "unsafe"
        return (f"disk {state} for {self.kind} at {self.path}: "
                f"{self.free_bytes // MB} MB free, {self.required_bytes // MB} MB required")


def free_bytes(path: Path | str) -> int:
    p = Path(path)
    while not p.exists() and p.parent != p:
        p = p.parent
    try:
        return shutil.disk_usage(p).free
    except OSError:
        return 0


def review_db_write_safe(path: Path | str) -> DiskVerdict:
    free = free_bytes(path)
    return DiskVerdict("REVIEW_DB_WRITE", str(path), free, REVIEW_DB_WRITE_SAFE,
                       free >= REVIEW_DB_WRITE_SAFE)


def render_job_safe(path: Path | str, *, expected_output_bytes: int | None = None) -> DiskVerdict:
    """Expected output plus the margin. A caller that knows its size (a clip
    of N seconds at the capture bitrate) passes it; the default covers a
    proxy capture."""
    need = (RENDER_EXPECTED_DEFAULT if expected_output_bytes is None
            else int(expected_output_bytes)) + RENDER_MARGIN
    free = free_bytes(path)
    return DiskVerdict("RENDER_JOB", str(path), free, need, free >= need)


def large_build_safe(path: Path | str, *, required_bytes: int | None = None) -> DiskVerdict:
    need = LARGE_BUILD_SAFE if required_bytes is None else int(required_bytes)
    free = free_bytes(path)
    return DiskVerdict("LARGE_BUILD", str(path), free, need, free >= need)
