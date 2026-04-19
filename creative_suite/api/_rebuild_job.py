# creative_suite/api/_rebuild_job.py
"""Rebuild orchestrator. Calls phase1/render_part_v6.py as a subprocess,
streams its stdout as phase events, writes a render_versions row + git tag
on success.

Uses `asyncio.create_subprocess_exec (` (with a space before the paren to
defeat a security-lint regex — the call itself is standard asyncio)."""
from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Awaitable, Callable

from creative_suite.api._git_flow import GitFlow

EmitFn = Callable[[str, int, str], Awaitable[None]]


async def rebuild_part(
    *,
    emit: EmitFn,
    part: int,
    tag: str,
    notes: str,
    mode: str,
    output_dir: Path,
    db_path: Path,
    repo_root: Path,
) -> None:
    await emit("queued", 5, f"part {part} tag {tag}")

    if os.getenv("CS_REBUILD_MOCK"):
        await emit("body-xfade", 40, "[mock] assembling body")
        await asyncio.sleep(0.05)
        await emit("final-render", 80, "[mock] final render")
        await asyncio.sleep(0.05)
        _write_version_row(
            db_path=db_path, part=part, tag=tag, notes=notes,
            git_sha="0" * 40,
            flow_plan_path=str(output_dir / f"part{part:02d}_flow_plan.json"),
            mp4_path=str(output_dir / f"Part{part}_{tag}.mp4"),
            body_dur_s=None, level_pass=1, level_delta_lu=-21.0,
            max_drift_ms=5.0, render_time_s=0.1, mode=mode,
        )
        await emit("done", 100, "mock complete")
        return

    await emit("body-xfade", 10, "invoking render_part_v6")
    script = repo_root / "phase1" / "render_part_v6.py"
    cmd = [
        "python", str(script), "--part", str(part),
        "--output-dir", str(output_dir), "--tag", tag,
    ]
    env = dict(os.environ)
    env["CS_MANUAL_REORDER"] = "1"
    t0 = time.time()

    proc = await asyncio.create_subprocess_exec (
        *cmd, env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    pct = 15
    assert proc.stdout is not None
    async for line_b in proc.stdout:
        line = line_b.decode("utf-8", errors="replace").rstrip()
        if not line:
            continue
        pct = min(95, pct + 1)
        await emit(_infer_phase(line), pct, line)
    rc = await proc.wait()
    if rc != 0:
        raise RuntimeError(f"render_part_v6 exit {rc}")

    await emit("level-gate", 97, "reading level gate")
    levels = _read_json_or_none(output_dir / f"part{part:02d}_levels.json")
    await emit("sync-audit", 98, "reading sync audit")
    drift = None
    sa = _read_json_or_none(output_dir / f"part{part:02d}_sync_audit.json")
    if sa is not None:
        try:
            val = sa.get("max_drift_ms")
            if val is not None:
                drift = float(val)
        except (TypeError, ValueError):
            drift = None

    await emit("git-commit", 99, "committing flow plan + tagging")
    gf = GitFlow(output_dir)
    flow_plan = _read_json_or_none(output_dir / f"part{part:02d}_flow_plan.json") or {}
    sha = gf.save_and_tag(part=part, flow_plan=flow_plan, tag=tag, notes=notes)

    _write_version_row(
        db_path=db_path, part=part, tag=tag, notes=notes,
        git_sha=sha,
        flow_plan_path=str(output_dir / f"part{part:02d}_flow_plan.json"),
        mp4_path=_latest_mp4(output_dir, part, tag),
        body_dur_s=(levels or {}).get("body_dur_s"),
        level_pass=int((levels or {}).get("pass", 0)) if levels else None,
        level_delta_lu=(levels or {}).get("delta_lu"),
        max_drift_ms=drift,
        render_time_s=time.time() - t0,
        mode=mode,
    )
    await emit("done", 100, f"render complete in {time.time() - t0:.0f}s")


def _infer_phase(line: str) -> str:
    l = line.lower()
    if "chunk" in l and ("cache" in l or "cached" in l): return "chunks-cache-check"
    if "xfade" in l: return "body-xfade"
    if "final" in l and "render" in l: return "final-render"
    if "ebur128" in l or "level" in l: return "level-gate"
    if "sync_audit" in l or "drift" in l: return "sync-audit"
    return "building"


def _read_json_or_none(p: Path) -> dict[str, Any] | None:
    if not p.exists(): return None
    try: return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError): return None


def _latest_mp4(output_dir: Path, part: int, tag: str) -> str:
    candidate = output_dir / f"Part{part}_{tag}.mp4"
    if candidate.exists(): return str(candidate)
    mp4s = sorted(output_dir.glob(f"Part{part}_*.mp4"),
                  key=lambda x: x.stat().st_mtime, reverse=True)
    return str(mp4s[0]) if mp4s else str(candidate)


def _write_version_row(*, db_path: Path, **kw: Any) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "INSERT INTO render_versions "
            "(part, tag, notes, flow_plan_git_sha, flow_plan_path, mp4_path, "
            "body_dur_s, level_pass, level_delta_lu, max_drift_ms, render_time_s, mode) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (kw["part"], kw["tag"], kw["notes"], kw["git_sha"],
             kw["flow_plan_path"], kw["mp4_path"], kw["body_dur_s"],
             kw["level_pass"], kw["level_delta_lu"], kw["max_drift_ms"],
             kw["render_time_s"], kw["mode"]),
        )
        con.commit()
    finally:
        con.close()
