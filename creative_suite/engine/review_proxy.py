"""On-demand review proxies for the /frags browser.

Browsers cannot play the MJPEG master AVIs, and most frags have no master
capture at all. This module generates a small H.264 MP4 "review proxy" for a
single frag window on demand:

    stage_demo (frags_rebuilt.db demos table, read-only)
      -> capture_demo one window (wolfcam MJPEG AVI, master profile — it IS
         the review look)
      -> ffmpeg transcode to H.264/AAC MP4 (+faststart)
      -> cache under output/demo_v2/review_proxies/<key>.mp4, delete the AVI

Cache key = sha1(demo content_hash + start_ms + end_ms + profile_id). A READY
key is never regenerated.

Concurrency: wolfcam is one-at-a-time — a single daemon worker thread drains
a module queue, and the existing exclusive marker file
output/demo_v2/_capture.lock is taken while generating (skip-and-requeue if
another writer holds it, same PID convention as capture_batch_run.py).

State lives in creative_suite/database/editorial.db (NEW db). The recognition
databases (frag_recognition.db / demo_v2.db / frags_rebuilt.db) are NEVER
written by this module — editorial state stays separate (project rule).

CS_PROXY_MOCK=1 skips wolfcam entirely and ffmpeg-generates a testsrc MP4 of
the right duration (pattern: CS_CAPTURE_MOCK in wolfcam_capture.py) so tests
run headless.
"""
from __future__ import annotations

import hashlib
import os
import queue
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
_DB_DIR = REPO_ROOT / "creative_suite" / "database"

# Module-level so tests can monkeypatch them.
EDITORIAL_DB_PATH = _DB_DIR / "editorial.db"
FRAGS_REBUILT_DB_PATH = _DB_DIR / "frags_rebuilt.db"
PROXY_DIR = REPO_ROOT / "output" / "demo_v2" / "review_proxies"
LOCK_PATH = REPO_ROOT / "output" / "demo_v2" / "_capture.lock"
FFMPEG = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"

# Window when the frag has no master capture: 4s before, 3s after the kill.
WINDOW_PRE_MS = 4000
WINDOW_POST_MS = 3000

_LOCK_RETRY_S = 5.0        # requeue delay while another writer holds the lock
_MAX_LOCK_WAITS = 240      # give up after ~20 min of a held lock

_queue: "queue.Queue[dict[str, Any] | None]" = queue.Queue()
_worker: threading.Thread | None = None
_worker_mutex = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS review_proxies (
    key TEXT PRIMARY KEY,
    frag_id INT,
    demo_name TEXT,
    start_ms INT,
    end_ms INT,
    profile_id TEXT,
    state TEXT,
    error TEXT,
    mp4_path TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS editorial_reviews (
    frag_id INT PRIMARY KEY,
    verdict TEXT CHECK(verdict IN ('LOVE','KEEP','MAYBE','DROP')),
    user_tier TEXT CHECK(user_tier IN ('S_PLUS','S','A','B','')),
    notes TEXT,
    updated_at TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def editorial_conn() -> sqlite3.Connection:
    """Writable connection to editorial.db (the ONLY db this module writes)."""
    EDITORIAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(EDITORIAL_DB_PATH, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    table_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' "
        "AND name='editorial_reviews'"
    ).fetchone()
    if table_sql and "'B'" not in str(table_sql[0]):
        conn.executescript(
            "ALTER TABLE editorial_reviews RENAME TO editorial_reviews_legacy;"
            "CREATE TABLE editorial_reviews ("
            "frag_id INT PRIMARY KEY,"
            "verdict TEXT CHECK(verdict IN ('LOVE','KEEP','MAYBE','DROP'))," 
            "user_tier TEXT CHECK(user_tier IN ('S_PLUS','S','A','B',''))," 
            "notes TEXT, updated_at TEXT);"
            "INSERT INTO editorial_reviews "
            "SELECT frag_id, verdict, user_tier, notes, updated_at "
            "FROM editorial_reviews_legacy;"
            "DROP TABLE editorial_reviews_legacy;"
        )
        conn.commit()
    return conn


def demo_source(demo_name: str) -> tuple[Path | None, str | None]:
    """(path, content_hash) for a demo, from frags_rebuilt.db — read-only."""
    if not FRAGS_REBUILT_DB_PATH.exists():
        return None, None
    conn = sqlite3.connect(
        f"file:{FRAGS_REBUILT_DB_PATH.as_posix()}?mode=ro", uri=True
    )
    try:
        row = conn.execute(
            "SELECT path, content_hash FROM demos WHERE name = ? "
            "ORDER BY demo_id LIMIT 1",
            (demo_name,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None, None
    return Path(row[0]), row[1]


def _profile_id() -> str:
    if os.getenv("CS_PROXY_MOCK"):
        return "mockprofile"
    from creative_suite.engine import master_profile
    return master_profile.profile_id()


def proxy_key(content_hash: str, start_ms: int, end_ms: int, profile_id: str) -> str:
    h = hashlib.sha1()
    h.update(f"{content_hash}|{start_ms}|{end_ms}|{profile_id}".encode())
    return h.hexdigest()


def get_state(frag_id: int) -> dict[str, Any]:
    """Latest proxy state for a frag. MISSING when never requested."""
    conn = editorial_conn()
    try:
        row = conn.execute(
            "SELECT * FROM review_proxies WHERE frag_id = ? "
            "ORDER BY updated_at DESC, key DESC LIMIT 1",
            (frag_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"state": "MISSING"}
    d = dict(row)
    if d["state"] == "READY":
        mp4 = d.get("mp4_path")
        if not mp4 or not Path(str(mp4)).exists():
            d["state"] = "FAILED"
            d["error"] = "cached mp4 missing on disk"
    return d


def get_states(frag_ids: list[int]) -> dict[int, dict[str, Any]]:
    """Latest proxy state for each requested frag, in one database read."""
    if not frag_ids:
        return {}
    conn = editorial_conn()
    try:
        marks = ",".join("?" * len(frag_ids))
        rows = conn.execute(
            "SELECT * FROM review_proxies WHERE frag_id IN (" + marks + ") "
            "ORDER BY updated_at DESC, key DESC",
            frag_ids,
        ).fetchall()
    finally:
        conn.close()
    out: dict[int, dict[str, Any]] = {}
    for row in rows:
        frag_id = int(row["frag_id"])
        if frag_id in out:
            continue
        data = dict(row)
        if data["state"] == "READY":
            mp4 = data.get("mp4_path")
            if not mp4 or not Path(str(mp4)).exists():
                data["state"] = "FAILED"
                data["error"] = "cached mp4 missing on disk"
        out[frag_id] = data
    return out


def request_proxy(
    frag_id: int, demo_name: str, start_ms: int, end_ms: int
) -> dict[str, Any]:
    """Queue proxy generation (idempotent). Returns the current state row."""
    demo_path, content_hash = demo_source(demo_name)
    if content_hash is None:
        return {"state": "FAILED",
                "error": f"demo not found in frags_rebuilt.db: {demo_name}"}
    # V1 is closed. demo_source returns whatever path a row holds, and a row
    # is not a guarantee -- so the source is checked here, where it is about
    # to become a capture, rather than trusted.
    from creative_suite.engine import media_provenance as mprov
    try:
        mprov.assert_demo_source(demo_path, "review proxy source")
    except mprov.LegacySourceRefused as exc:
        return {"state": "FAILED", "error": str(exc)}
    profile = _profile_id()
    key = proxy_key(content_hash, start_ms, end_ms, profile)
    conn = editorial_conn()
    try:
        row = conn.execute(
            "SELECT * FROM review_proxies WHERE key = ?", (key,)
        ).fetchone()
        if row is not None:
            d = dict(row)
            if d["state"] == "READY" and d["mp4_path"] and Path(d["mp4_path"]).exists():
                return d  # never regenerate a READY key
            if d["state"] in ("QUEUED", "GENERATING"):
                return d
            # FAILED (or READY with missing file): requeue below.
        now = _now()
        conn.execute(
            "INSERT INTO review_proxies (key, frag_id, demo_name, start_ms,"
            " end_ms, profile_id, state, error, mp4_path, created_at,"
            " updated_at) VALUES (?,?,?,?,?,?,'QUEUED',NULL,NULL,?,?) "
            "ON CONFLICT(key) DO UPDATE SET state='QUEUED', error=NULL,"
            " updated_at=excluded.updated_at",
            (key, frag_id, demo_name, start_ms, end_ms, profile, now, now),
        )
        conn.commit()
        state = dict(conn.execute(
            "SELECT * FROM review_proxies WHERE key = ?", (key,)).fetchone())
    finally:
        conn.close()
    _queue.put({
        "key": key, "frag_id": frag_id, "demo_name": demo_name,
        "demo_path": str(demo_path), "start_ms": int(start_ms),
        "end_ms": int(end_ms), "lock_waits": 0,
    })
    _ensure_worker()
    return state


def _set_state(key: str, state: str, error: str | None = None,
               mp4_path: str | None = None) -> None:
    conn = editorial_conn()
    try:
        conn.execute(
            "UPDATE review_proxies SET state=?, error=?, mp4_path=?,"
            " updated_at=? WHERE key=?",
            (state, error, mp4_path, _now(), key),
        )
        conn.commit()
    finally:
        conn.close()


def _try_acquire_lock() -> bool:
    """Existing PID/lock convention (capture_batch_run.acquire_lock), but
    non-fatal: returns False when another live process holds the lock."""
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if LOCK_PATH.exists():
        pid_text = LOCK_PATH.read_text().strip()
        try:
            pid = int(pid_text)
        except ValueError:
            pid = None
        if pid is not None and pid != os.getpid():
            try:
                os.kill(pid, 0)
                return False  # live holder — skip and requeue
            except OSError:
                pass  # stale lock — take over
    LOCK_PATH.write_text(str(os.getpid()))
    return True


def _release_lock() -> None:
    try:
        if LOCK_PATH.exists() and LOCK_PATH.read_text().strip() == str(os.getpid()):
            LOCK_PATH.unlink()
    except OSError:
        pass


def _run_ffmpeg(args: list[str], timeout: int = 600) -> None:
    proc = subprocess.Popen(
        [str(FFMPEG), "-y", "-loglevel", "error", *args],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    try:
        _, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # CS-4 cascade
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except (subprocess.TimeoutExpired, OSError):
            try:
                proc.kill()
                proc.wait(timeout=10)
            except (subprocess.TimeoutExpired, OSError):
                pass
        raise RuntimeError(f"ffmpeg timeout after {timeout}s")
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg rc={proc.returncode}: {(err or b'')[:400].decode(errors='replace')}")


def _generate(job: dict[str, Any]) -> None:
    """Produce the cached MP4 for one job. Runs on the worker thread with the
    capture lock held."""
    key = job["key"]
    start_ms, end_ms = job["start_ms"], job["end_ms"]
    PROXY_DIR.mkdir(parents=True, exist_ok=True)
    final_mp4 = PROXY_DIR / f"{key}.mp4"
    tmp_mp4 = PROXY_DIR / f"{key}.tmp.mp4"

    if os.getenv("CS_PROXY_MOCK"):
        dur = max(0.5, (end_ms - start_ms) / 1000.0)
        _run_ffmpeg([
            "-f", "lavfi", "-i", "testsrc=size=320x180:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440",
            "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "160k",
            str(tmp_mp4),
        ], timeout=180)
        tmp_mp4.replace(final_mp4)
        _set_state(key, "READY", mp4_path=str(final_mp4))
        return

    from creative_suite.engine import wolfcam_capture as wc
    from creative_suite.engine import media_provenance as mprov
    wc.ensure_install()
    demo_path = Path(job["demo_path"])
    # Checked again at capture time: the queue is crossed by a job dict, and
    # the guard belongs next to the thing it protects.
    mprov.assert_demo_source(demo_path, "review proxy capture")
    if not demo_path.exists():
        raise RuntimeError(f"demo file missing: {demo_path}")
    safe = wc.stage_demo(demo_path)
    clip_name = f"rp_{key[:16]}"
    res = wc.capture_demo(
        safe, [{"clip_name": clip_name, "start_ms": start_ms, "end_ms": end_ms}]
    )
    if not res["ok"]:
        raise RuntimeError(res.get("error") or "wolfcam capture failed")
    avi = Path(res["avis"][clip_name])
    try:
        _run_ffmpeg([
            "-i", str(avi),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "160k",
            str(tmp_mp4),
        ], timeout=1800)
        tmp_mp4.replace(final_mp4)
    finally:
        try:
            if avi.exists():
                avi.unlink()  # AVI is scratch — the MP4 is the deliverable
        except OSError:
            pass
    _set_state(key, "READY", mp4_path=str(final_mp4))


def _worker_loop() -> None:
    while True:
        job = _queue.get()
        if job is None:  # test hook / shutdown sentinel
            _queue.task_done()
            return
        try:
            if not _try_acquire_lock():
                job["lock_waits"] = job.get("lock_waits", 0) + 1
                if job["lock_waits"] > _MAX_LOCK_WAITS:
                    _set_state(job["key"], "FAILED",
                               error="capture lock held too long")
                else:
                    time.sleep(_LOCK_RETRY_S)
                    _queue.put(job)  # skip-and-requeue
                continue
            try:
                _set_state(job["key"], "GENERATING")
                _generate(job)
            finally:
                _release_lock()
        except Exception as exc:  # worker must never die
            _set_state(job["key"], "FAILED", error=str(exc)[:500])
        finally:
            _queue.task_done()


def _ensure_worker() -> None:
    global _worker
    with _worker_mutex:
        if _worker is None or not _worker.is_alive():
            _worker = threading.Thread(
                target=_worker_loop, name="review-proxy-worker", daemon=True
            )
            _worker.start()


# ---------------------------------------------------------------- reviews

def get_review(frag_id: int) -> dict[str, Any] | None:
    conn = editorial_conn()
    try:
        row = conn.execute(
            "SELECT * FROM editorial_reviews WHERE frag_id = ?", (frag_id,)
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def get_reviews(frag_ids: list[int]) -> dict[int, dict[str, Any]]:
    if not frag_ids:
        return {}
    conn = editorial_conn()
    try:
        marks = ",".join("?" * len(frag_ids))
        rows = conn.execute(
            f"SELECT * FROM editorial_reviews WHERE frag_id IN ({marks})",
            frag_ids,
        ).fetchall()
    finally:
        conn.close()
    return {r["frag_id"]: dict(r) for r in rows}


def count_reviews(verdict: str) -> int:
    conn = editorial_conn()
    try:
        return int(conn.execute(
            "SELECT COUNT(*) FROM editorial_reviews WHERE verdict = ?", (verdict,)
        ).fetchone()[0])
    finally:
        conn.close()


def reviewed_frag_ids(verdict: str) -> list[int]:
    conn = editorial_conn()
    try:
        return [int(row[0]) for row in conn.execute(
            "SELECT frag_id FROM editorial_reviews WHERE verdict = ?", (verdict,)
        )]
    finally:
        conn.close()


def put_review(
    frag_id: int,
    verdict: str | None = None,
    user_tier: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Upsert editorial fields — only the ones provided. Machine scores are
    never touched (they live in frag_recognition.db, which we never write)."""
    conn = editorial_conn()
    try:
        existing = conn.execute(
            "SELECT * FROM editorial_reviews WHERE frag_id = ?", (frag_id,)
        ).fetchone()
        cur = dict(existing) if existing else {
            "verdict": None, "user_tier": None, "notes": None}
        if verdict is not None:
            cur["verdict"] = verdict
        if user_tier is not None:
            cur["user_tier"] = user_tier
        if notes is not None:
            cur["notes"] = notes
        conn.execute(
            "INSERT INTO editorial_reviews (frag_id, verdict, user_tier,"
            " notes, updated_at) VALUES (?,?,?,?,?) "
            "ON CONFLICT(frag_id) DO UPDATE SET verdict=excluded.verdict,"
            " user_tier=excluded.user_tier, notes=excluded.notes,"
            " updated_at=excluded.updated_at",
            (frag_id, cur["verdict"], cur["user_tier"], cur["notes"], _now()),
        )
        conn.commit()
        return dict(conn.execute(
            "SELECT * FROM editorial_reviews WHERE frag_id = ?", (frag_id,)
        ).fetchone())
    finally:
        conn.close()
