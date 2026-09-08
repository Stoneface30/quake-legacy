"""Part01 rough-cut assembler — executes a part01_plan edit plan.

Resumable by design: the plan is FIXED (edit_plan_id-hashed); segments whose
master AVI has not been captured yet are skipped with a logged placeholder and
assembly simply re-runs as more masters land.

Audio contract (P1-G): the music is ONE fixed-level bed for the whole body —
no sidechain, no ducking, no level-following. Post-encode the file is measured
with ebur128 (true peak); if it exceeds -1.0 dBTP a measured STATIC gain
re-mux is applied (a constant gain is not level-following, so P1-G holds).

This module builds every ffmpeg command as pure data first (testable without
execution); run_assembly() is the only place subprocesses are spawned.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
DEFAULT_FFMPEG = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
PART01_DIR = REPO_ROOT / "output" / "demo_v2" / "part01"

# Rough-cut encode ladder (final renders use the P1-J ceiling, not this).
ROUGH_CRF = 20
ROUGH_PRESET = "veryfast"
ROUGH_FPS = 60
ROUGH_SIZE = "1920x1080"

TRUE_PEAK_CEILING_DBTP = -1.0
STATIC_GAIN_HEADROOM_DB = 0.2   # land slightly under the ceiling

_PEAK_RE = re.compile(r"Peak:\s*(-?\d+(?:\.\d+)?)\s*dBFS")


def segment_cut_cmd(avi_path: str | Path, in_ms: int, out_ms: int,
                    seg_path: str | Path,
                    ffmpeg: str | Path = DEFAULT_FFMPEG) -> list[str]:
    """One segment cut: stream-level -ss/-t, re-encoded for the rough cut.

    Intermediates are MKV with PCM audio (P1-BB: never AAC intermediates —
    AAC priming delay compounds into drift across a concat chain).
    """
    dur_s = (out_ms - in_ms) / 1000.0
    return [
        str(ffmpeg), "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{in_ms / 1000.0:.3f}",
        "-t", f"{dur_s:.3f}",
        "-i", str(avi_path),
        "-vf", f"scale={ROUGH_SIZE.replace('x', ':')}:flags=lanczos,fps={ROUGH_FPS}",
        "-vsync", "cfr",
        "-c:v", "libx264", "-crf", str(ROUGH_CRF), "-preset", ROUGH_PRESET,
        "-pix_fmt", "yuv420p",
        "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
        str(seg_path),
    ]


def build_segment_jobs(plan: dict, out_dir: Path | str = PART01_DIR,
                       ffmpeg: str | Path = DEFAULT_FFMPEG,
                       ) -> tuple[list[dict], list[dict]]:
    """Turn plan segments into (jobs, placeholders).

    A job = {clip_id, seg_path, cmd}. A placeholder is logged for any segment
    whose avi_path is missing on disk — the plan itself is untouched.
    """
    seg_dir = Path(out_dir) / "segments"
    jobs: list[dict] = []
    placeholders: list[dict] = []
    for i, seg in enumerate(plan["segments"]):
        avi = seg.get("avi_path")
        if not avi or not Path(avi).exists():
            placeholders.append({
                "index": i,
                "clip_id": seg["clip_id"],
                "phase": seg.get("phase"),
                "avi_path": avi,
                "status": "SKIPPED_AVI_MISSING",
            })
            continue
        seg_path = seg_dir / f"seg{i:03d}_c{seg['clip_id']:05d}.mkv"
        jobs.append({
            "index": i,
            "clip_id": seg["clip_id"],
            "seg_path": str(seg_path),
            "cmd": segment_cut_cmd(avi, seg["in_ms"], seg["out_ms"],
                                   seg_path, ffmpeg),
        })
    return jobs, placeholders


def concat_cmd(list_file: str | Path, body_path: str | Path,
               ffmpeg: str | Path = DEFAULT_FFMPEG) -> list[str]:
    """Concat the re-encoded segments (identical params -> stream copy)."""
    return [
        str(ffmpeg), "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy", str(body_path),
    ]


def music_mux_cmd(body_path: str | Path, music_path: str | Path,
                  out_path: str | Path, body_duration_s: float,
                  music_offset_s: float = 0.0,
                  music_gain: float = 0.55, game_audio_gain: float = 0.9,
                  ffmpeg: str | Path = DEFAULT_FFMPEG) -> list[str]:
    """Lay the fixed-level music bed under the game audio.

    P1-G: `volume={music_gain}` is applied ONCE — a constant for the whole
    body. The only level moves are the head fade-in and tail fade-out.
    amix runs with normalize=0 so neither stream is rescaled dynamically.
    """
    delay_ms = int(round(max(0.0, music_offset_s) * 1000.0))
    fade_out_st = max(0.0, body_duration_s - 3.0)
    filt = (
        f"[0:a]volume={game_audio_gain}[g];"
        f"[1:a]volume={music_gain},"
        f"afade=t=in:st=0:d=1.0,"
        f"afade=t=out:st={fade_out_st:.3f}:d=3.0,"
        f"adelay={delay_ms}|{delay_ms},apad[m];"
        f"[g][m]amix=inputs=2:duration=first:dropout_transition=0:"
        f"normalize=0[mix]"
    )
    return [
        str(ffmpeg), "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(body_path), "-i", str(music_path),
        "-filter_complex", filt,
        "-map", "0:v:0", "-map", "[mix]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "320k",
        "-movflags", "+faststart",
        str(out_path),
    ]


def static_gain_cmd(in_path: str | Path, out_path: str | Path,
                    gain_db: float,
                    ffmpeg: str | Path = DEFAULT_FFMPEG) -> list[str]:
    """Measured STATIC gain re-mux (constant — not level-following)."""
    return [
        str(ffmpeg), "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(in_path),
        "-af", f"volume={gain_db:.2f}dB",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
        str(out_path),
    ]


def parse_true_peak_dbfs(ebur128_stderr: str) -> float | None:
    """Highest per-channel Peak reading from `ebur128=peak=true` output."""
    vals = [float(v) for v in _PEAK_RE.findall(ebur128_stderr)]
    return max(vals) if vals else None


def measure_true_peak(path: str | Path,
                      ffmpeg: str | Path = DEFAULT_FFMPEG) -> float:
    """True peak (dBTP) of the ENCODED file via ebur128=peak=true."""
    proc = subprocess.run(
        [str(ffmpeg), "-nostats", "-hide_banner", "-i", str(path),
         "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    peak = parse_true_peak_dbfs(proc.stderr)
    if peak is None:
        raise RuntimeError(f"ebur128 produced no peak reading for {path}")
    return peak


def decode_qa(path: str | Path,
              ffmpeg: str | Path = DEFAULT_FFMPEG) -> list[str]:
    """Full decode QA — returns decoder error lines (empty = clean)."""
    proc = subprocess.run(
        [str(ffmpeg), "-v", "error", "-i", str(path), "-f", "null", "-"],
        capture_output=True, text=True, check=False,
    )
    return [ln for ln in proc.stderr.splitlines() if ln.strip()]


def run_assembly(plan: dict | str | Path,
                 out_dir: Path | str = PART01_DIR,
                 ffmpeg: str | Path = DEFAULT_FFMPEG) -> dict:
    """Execute the rough cut. Resumable; missing masters are skipped + logged.

    NOT run by the planner or the test suite — the orchestrator calls this
    once captures land.
    """
    if not isinstance(plan, dict):
        plan = json.loads(Path(plan).read_text())
    out_dir = Path(out_dir)
    (out_dir / "segments").mkdir(parents=True, exist_ok=True)

    jobs, placeholders = build_segment_jobs(plan, out_dir, ffmpeg)
    log: dict = {
        "edit_plan_id": plan.get("edit_plan_id"),
        "placeholders": placeholders,
        "segments_cut": [],
        "true_peak_dbtp": None,
        "static_gain_db": None,
        "decode_errors": None,
    }
    for job in jobs:
        subprocess.run(job["cmd"], check=True)
        log["segments_cut"].append(job["seg_path"])

    if not log["segments_cut"]:
        log["status"] = "NO_SEGMENTS_AVAILABLE"
        _write_log(out_dir, log)
        return log

    list_file = out_dir / "segments" / "concat.txt"
    list_file.write_text("".join(
        f"file '{Path(p).as_posix()}'\n" for p in log["segments_cut"]))
    body = out_dir / "Part01_body.mkv"
    subprocess.run(concat_cmd(list_file, body, ffmpeg), check=True)

    audio = plan["audio"]
    body_dur = sum(
        s["est_duration"] for s in plan["segments"]
        if not any(p["clip_id"] == s["clip_id"] for p in placeholders))
    out = out_dir / "Part01_roughcut.mp4"
    subprocess.run(music_mux_cmd(
        body, plan["music"]["path"], out, body_dur,
        music_offset_s=plan["music"].get("offset_s", 0.0),
        music_gain=audio["music_gain"],
        game_audio_gain=audio["game_audio_gain"],
        ffmpeg=ffmpeg), check=True)

    peak = measure_true_peak(out, ffmpeg)
    log["true_peak_dbtp"] = peak
    if peak > TRUE_PEAK_CEILING_DBTP:
        gain_db = (TRUE_PEAK_CEILING_DBTP - STATIC_GAIN_HEADROOM_DB) - peak
        fixed = out_dir / "Part01_roughcut_tp.mp4"
        subprocess.run(static_gain_cmd(out, fixed, gain_db, ffmpeg),
                       check=True)
        fixed.replace(out)
        log["static_gain_db"] = round(gain_db, 2)
        log["true_peak_dbtp"] = measure_true_peak(out, ffmpeg)

    log["decode_errors"] = decode_qa(out, ffmpeg)
    log["status"] = "OK" if not log["decode_errors"] else "DECODE_ERRORS"
    log["output"] = str(out)
    _write_log(out_dir, log)
    return log


def _write_log(out_dir: Path, log: dict) -> None:
    (out_dir / "assembly_log.json").write_text(json.dumps(log, indent=1))


__all__ = [
    "segment_cut_cmd", "build_segment_jobs", "concat_cmd", "music_mux_cmd",
    "static_gain_cmd", "parse_true_peak_dbfs", "measure_true_peak",
    "decode_qa", "run_assembly", "TRUE_PEAK_CEILING_DBTP",
]


if __name__ == "__main__":  # pragma: no cover
    import sys
    plan_path = sys.argv[1] if len(sys.argv) > 1 \
        else PART01_DIR / "part01_edit_plan.json"
    result = run_assembly(plan_path)
    print(json.dumps({k: v for k, v in result.items()
                      if k != "segments_cut"}, indent=1))
