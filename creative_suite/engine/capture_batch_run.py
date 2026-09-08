"""Capture-batch orchestrator: candidates -> wolfcam -> QA -> provenance.

Single controlled writer (PID lock, pattern from the V1 highlight run).
Groups candidate rows by source demo so each demo needs ONE wolfcam launch.
Retries a failed capture once, then records the failure. Never touches V1.

Usage:
    python -u creative_suite/engine/capture_batch_run.py --canary
    python -u creative_suite/engine/capture_batch_run.py            # full batch
    python -u creative_suite/engine/capture_batch_run.py --limit 10
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.database import demo_v2_db
from creative_suite.engine import capture_qa, wolfcam_capture as wc
from creative_suite.engine.process_liveness import process_alive


def _profile_id() -> str:
    from creative_suite.engine import master_profile
    return master_profile.profile_id()

FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"
LOCK = REPO_ROOT / "output" / "demo_v2" / "_capture.lock"
REPORT = REPO_ROOT / "output" / "demo_v2" / "capture_run_report.json"


def acquire_lock() -> None:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        pid = LOCK.read_text().strip()
        try:
            if process_alive(int(pid)):
                print(f"FATAL: capture already running (pid {pid})")
                raise SystemExit(1)
        except (OSError, ValueError):
            pass  # stale lock
    LOCK.write_text(str(os.getpid()))


def release_lock() -> None:
    try:
        if LOCK.exists() and LOCK.read_text().strip() == str(os.getpid()):
            LOCK.unlink()
    except OSError:
        pass


def demo_paths() -> dict[str, Path]:
    conn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    out = {name: Path(p) for name, p in
           conn.execute("SELECT name, path FROM demos")}
    conn.close()
    return out


def load_candidates(conn, limit: int | None = None,
                    ids: list[int] | None = None) -> list[dict]:
    q = ("SELECT * FROM generated_clips WHERE avi_path IS NULL "
         "AND promotion_status='CANDIDATE'")
    if ids:
        q += f" AND generated_clip_id IN ({','.join('?' * len(ids))})"
    q += " ORDER BY rank_score DESC"
    if limit:
        q += f" LIMIT {int(limit)}"
    conn.row_factory = sqlite3.Row
    return [dict(r) for r in conn.execute(q, ids or [])]


def pick_canary(cands: list[dict], sizes: dict[str, int]) -> list[dict]:
    """5 representative candidates (§15): rail multikill, rocket/direct,
    clutch, small (<800KB) demo, longest multi-kill window."""
    chosen: list[dict] = []
    used = set()

    def take(pred, label):
        for c in cands:
            if c["generated_clip_id"] in used:
                continue
            if pred(c):
                c["_canary_role"] = label
                chosen.append(c)
                used.add(c["generated_clip_id"])
                return

    take(lambda c: "RAILGUN" in (c["weapon"] or "") and
         len(json.loads(c["frag_offsets_ms"])) >= 3, "rail_multikill")
    take(lambda c: "ROCKET" in (c["weapon"] or ""), "rocket")
    take(lambda c: c["clutch_context"], "clutch")
    take(lambda c: sizes.get(c["demo_name"], 1 << 30) < 800 * 1024, "small_demo")
    take(lambda c: (c["capture_end_ms"] - c["capture_start_ms"]) >= 20000,
         "long_action")
    # backfill to 5 if a category was empty
    for c in cands:
        if len(chosen) >= 5:
            break
        if c["generated_clip_id"] not in used:
            c["_canary_role"] = "backfill"
            chosen.append(c)
            used.add(c["generated_clip_id"])
    return chosen


def run(limit: int | None = None, canary: bool = False,
        ids: list[int] | None = None) -> dict:
    acquire_lock()
    try:
        return _run(limit, canary, ids)
    finally:
        release_lock()


def _run(limit, canary, ids) -> dict:
    wc.ensure_install()
    paths = demo_paths()
    dconn = demo_v2_db.connect()
    cands = load_candidates(dconn, limit=limit, ids=ids)
    if canary:
        conn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
        sizes = {n: s for n, s in
                 conn.execute("SELECT name, size_bytes FROM demos")}
        conn.close()
        cands = pick_canary(cands, sizes)

    by_demo: dict[str, list[dict]] = {}
    for c in cands:
        by_demo.setdefault(c["demo_name"], []).append(c)

    results = {"requested": len(cands), "captured": 0, "qa_pass": 0,
               "qa_fail": 0, "capture_fail": 0, "clips": []}
    demo_idx = 0
    for demo_name, group in by_demo.items():
        demo_idx += 1
        src = paths.get(demo_name)
        if src is None or not src.exists():
            for c in group:
                _mark_fail(dconn, c, "SOURCE_DEMO_MISSING")
                results["capture_fail"] += 1
            continue
        safe = wc.stage_demo(src, demo_idx)
        windows = [{"clip_name": f"c{c['generated_clip_id']:05d}",
                    "start_ms": c["capture_start_ms"],
                    "end_ms": c["capture_end_ms"]} for c in group]
        res = wc.capture_demo(safe, windows)
        if not res["ok"] and not res["avis"]:
            res = wc.capture_demo(safe, windows)   # one retry (§16)
        cmd = " ".join(wc.wolfcam_cmd(safe))
        for c in group:
            name = f"c{c['generated_clip_id']:05d}"
            avi = res["avis"].get(name)
            if avi is None:
                _mark_fail(dconn, c, f"CAPTURE_FAILED: {res['error']}")
                results["capture_fail"] += 1
                continue
            _qa_and_publish(dconn, c, avi, cmd, results)
        print(f"[{demo_idx}/{len(by_demo)}] {demo_name}: "
              f"{len(res['avis'])}/{len(group)} in {res['elapsed_s']:.0f}s",
              flush=True)

    results["qa_pass_rate"] = (results["qa_pass"] / results["captured"]
                               if results["captured"] else 0.0)
    dconn.close()
    REPORT.write_text(json.dumps(results, indent=1, default=str),
                      encoding="utf-8")
    return results


def _mark_fail(dconn, c, reason: str) -> None:
    dconn.execute(
        "UPDATE generated_clips SET qa_status='FAIL', promotion_status="
        "'REJECTED', promotion_reason=? WHERE generated_clip_id=?",
        (reason, c["generated_clip_id"]))
    dconn.commit()


def _qa_and_publish(dconn, c, avi: Path, cmd: str, results: dict) -> None:
    name = f"c{c['generated_clip_id']:05d}"
    expected_s = (c["capture_end_ms"] - c["capture_start_ms"]) / 1000.0
    mock = bool(os.getenv("CS_CAPTURE_MOCK"))
    tech = capture_qa.technical_qa(
        avi, expected_s,
        expect_resolution=None if mock else (wc.WIDTH, wc.HEIGHT),
        expect_fps=None if mock else wc.FPS)
    offsets = json.loads(c["frag_offsets_ms"])
    clutch_span = None
    if c["clutch_context"]:
        # clutch interval relative to capture start is bounded by the window
        clutch_span = (0, int(tech.get("duration_s", 0) * 1000))
    sem = capture_qa.semantic_qa(tech.get("duration_s", 0.0), offsets,
                                 clutch_span)
    results["captured"] += 1
    tier = c["tier"] or "B"
    if tech["pass"]:
        dest = wc.publish_avi(avi, tier, name)
        status = "PASS"
        results["qa_pass"] += 1
        promotion = "CAPTURED"
    else:
        quarantine = wc.CLIPS_DIR / "_qa_failed"
        quarantine.mkdir(parents=True, exist_ok=True)
        dest = quarantine / f"{name}.avi"
        if dest.exists():
            dest.unlink()
        avi.replace(dest)
        status = "FAIL"
        results["qa_fail"] += 1
        promotion = "CANDIDATE"     # eligible for retry run
    dconn.execute(
        "UPDATE generated_clips SET avi_path=?, qa_status=?, "
        "promotion_status=?, semantic_qa=?, capture_cmd=?, wolfcam_version=?, "
        "capture_profile_id=?, "
        "source_quality=? WHERE generated_clip_id=?",
        (str(dest), status, promotion, json.dumps(sem), cmd,
         wc.WOLFCAM_VERSION, _profile_id(),
         f"{tech.get('width')}x{tech.get('height')}@{tech.get('fps')}",
         c["generated_clip_id"]))
    dconn.commit()
    results["clips"].append({
        "clip": name, "tier": tier, "qa": status, "semantic": sem,
        "duration_s": tech.get("duration_s"), "path": str(dest),
        "reasons": tech["reasons"]})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canary", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--ids", type=str, help="comma-separated clip ids")
    args = ap.parse_args()
    ids = [int(x) for x in args.ids.split(",")] if args.ids else None
    t0 = time.time()
    r = run(limit=args.limit, canary=args.canary, ids=ids)
    print(json.dumps({k: v for k, v in r.items() if k != "clips"}, indent=1))
    print(f"elapsed {time.time() - t0:.0f}s")
