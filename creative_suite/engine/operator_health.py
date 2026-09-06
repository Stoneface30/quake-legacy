"""One quiet answer to "is the reviewer alright?".

Section 10 says monitor and do not spam. So this is a pull, not a push: it
computes a picture when asked and says nothing on its own. Nothing here
writes, deletes, restarts or repairs.

WHY DISK IS IN HERE. On 2026-09-06 the headless performance index grew to
87.6 GB and took G: to 1.4 MB free -- less than a single SQLite page batch.
Every failure that follows from that looks like something else: a verdict
that silently does not save, a capture that dies mid-write, a WAL that
cannot check point. The drive filling is the root cause and it was invisible
until somebody went looking, so it is now the first thing this reports.

WHAT A THRESHOLD IS FOR. Below `BATCH_FLOOR_GB` a mass capture is refused
before it starts, because a batch that fills the disk halfway through leaves
broken media AND a system that cannot record the fact. Refusal is not
deletion: nothing is ever removed automatically, and what to free is the
user's decision, not this module's.
"""
from __future__ import annotations

import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

# A single capture writes an MJPEG AVI and then an MP4. Below this there is
# not enough room to finish one honestly.
SINGLE_FLOOR_GB = 5.0

# A mass capture run needs headroom for the whole batch, not one clip.
BATCH_FLOOR_GB = 25.0

# Below this the reviewer itself is at risk: SQLite cannot grow, so a human
# verdict can fail to save. This is the number that matters most.
CRITICAL_GB = 1.0

OK = "OK"
WARN = "WARN"
CRITICAL = "CRITICAL"


@dataclass
class Health:
    checked_at: str
    status: str = OK
    disk: dict[str, Any] = field(default_factory=dict)
    permit: dict[str, Any] = field(default_factory=dict)
    media: dict[str, Any] = field(default_factory=dict)
    reviews: dict[str, Any] = field(default_factory=dict)
    alerts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"checked_at": self.checked_at, "status": self.status,
                "disk": self.disk, "permit": self.permit,
                "media": self.media, "reviews": self.reviews,
                "alerts": self.alerts}


def free_gb(path: Path = REPO_ROOT) -> float:
    try:
        return shutil.disk_usage(path).free / (1024 ** 3)
    except OSError:
        return -1.0


def disk_state(path: Path = REPO_ROOT) -> dict[str, Any]:
    try:
        u = shutil.disk_usage(path)
    except OSError as exc:
        return {"readable": False, "error": str(exc)}
    g = 1024 ** 3
    free = u.free / g
    return {"readable": True, "drive": str(Path(path).anchor),
            "free_gb": round(free, 2), "total_gb": round(u.total / g, 1),
            "free_pct": round(100 * u.free / u.total, 2),
            "can_capture_one": free >= SINGLE_FLOOR_GB,
            "can_capture_batch": free >= BATCH_FLOOR_GB,
            "single_floor_gb": SINGLE_FLOOR_GB,
            "batch_floor_gb": BATCH_FLOOR_GB}


def largest_files(path: Path = REPO_ROOT / "creative_suite" / "database",
                  top: int = 5) -> list[dict[str, Any]]:
    """What is actually taking the room, so the user can decide.

    REPORTED, NEVER TOUCHED. Choosing what to move or delete is a decision
    about somebody's data and it is not this module's to make.
    """
    out: list[dict[str, Any]] = []
    try:
        for p in sorted(path.glob("*"), key=lambda q: -q.stat().st_size)[:top]:
            if p.is_file():
                out.append({"name": p.name,
                            "gb": round(p.stat().st_size / 1024 ** 3, 2)})
    except OSError:
        return []
    return out


def media_state() -> dict[str, Any]:
    """Queue depth, the oldest thing still waiting, and what failed."""
    from creative_suite.engine import review_proxy as rp
    try:
        conn = rp.editorial_conn()
    except sqlite3.Error as exc:
        return {"readable": False, "error": str(exc)}
    try:
        rows = {r[0]: r[1] for r in conn.execute(
            "SELECT state, COUNT(*) FROM review_proxies GROUP BY state")}
        oldest = conn.execute(
            "SELECT MIN(updated_at) FROM review_proxies WHERE state IN "
            "('QUEUED','GENERATING')").fetchone()[0]
        recent_fail = [dict(r) for r in conn.execute(
            "SELECT key, error, updated_at FROM review_proxies WHERE "
            "state='FAILED' ORDER BY updated_at DESC LIMIT 3")]
    except sqlite3.Error as exc:
        return {"readable": False, "error": str(exc)}
    finally:
        conn.close()
    worker = getattr(rp, "_worker", None)
    return {"readable": True, "by_state": rows,
            "oldest_waiting": oldest,
            "worker_alive": bool(worker is not None and worker.is_alive()),
            "recent_failures": recent_fail}


def review_state() -> dict[str, Any]:
    from creative_suite.engine import review_corpus as rc
    try:
        p = rc.progress("USER_FRAG")
    except sqlite3.Error as exc:
        return {"readable": False, "error": str(exc)}
    return {"readable": True, "reviewed": p.get("reviewed"),
            "offered": p.get("total"),
            "canonical": p.get("canonical_total")}


def check(path: Path = REPO_ROOT) -> Health:
    """The whole picture. Reads only."""
    h = Health(checked_at=datetime.now(timezone.utc).isoformat(
        timespec="seconds"))
    h.disk = disk_state(path)
    if h.disk.get("readable"):
        free = h.disk["free_gb"]
        if free < CRITICAL_GB:
            h.status = CRITICAL
            h.alerts.append(
                f"{free:.2f} GB free on {h.disk['drive']} -- SQLite cannot "
                f"grow, so a human verdict can fail to SAVE. Nothing has "
                f"been deleted; freeing space is your call.")
            h.disk["largest_databases"] = largest_files()
        elif not h.disk["can_capture_batch"]:
            h.status = WARN
            h.alerts.append(
                f"{free:.1f} GB free -- below the {BATCH_FLOOR_GB} GB batch "
                f"floor, so mass capture is refused")

    try:
        from engine.pantheon import render_permit
        h.permit = render_permit.status()
    except Exception as exc:                                   # noqa: BLE001
        h.permit = {"error": type(exc).__name__}

    h.media = media_state()
    h.reviews = review_state()

    if h.media.get("readable") and h.media["by_state"].get("FAILED"):
        h.alerts.append(f"{h.media['by_state']['FAILED']} media job(s) FAILED")
        if h.status == OK:
            h.status = WARN
    return h


# ── the gate a capture run has to pass ──────────────────────────────────────

class NotEnoughDisk(RuntimeError):
    pass


def require_disk(batch: bool = False, path: Path = REPO_ROOT) -> float:
    """Raise rather than start a run that cannot finish.

    A batch that fills the drive halfway leaves broken media AND a system
    with no room to record that it broke.
    """
    free = free_gb(path)
    floor = BATCH_FLOOR_GB if batch else SINGLE_FLOOR_GB
    if free < 0:
        raise NotEnoughDisk("free space could not be read")
    if free < floor:
        raise NotEnoughDisk(
            f"{free:.1f} GB free, {floor:.0f} GB needed for "
            f"{'a batch' if batch else 'one capture'}")
    return free
