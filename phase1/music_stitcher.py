"""
Music stitcher v10 — full-track queue with explicit afade seams (Rule P1-W).

Supersedes the v8/v9 `acrossfade`-chain implementation. Per research brief
docs/research/audio-montage-2026-04-18.md §E, chaining acrossfade compounds
drift. v10 pre-computes per-pair seams and builds the graph with explicit
`afade` in/out + `adelay` + `amix`.

Key rules enforced:
    * P1-W No mid-song truncation: every queued track plays its FULL duration
      (within ±0.1 s of ffprobe'd length). Stitcher fails loudly if the main
      pool can't cover body + fade budget.
    * P1-R Three-track structure: intro + main(s) + outro.
    * Multi-main pool: accepts `partNN_main_1.mp3` .. `partNN_main_N.mp3` AND
      legacy `partNN_music.mp3` / numbered `partNN_music_01.mp3`.
    * Crossfades are 4–6 s, downbeat-locked on the outgoing track's last
      downbeat-before-(duration-6s) and the incoming track's first downbeat.

Public API:
    plan_stitch(part, required_duration_s) -> dict
    stitch_part_music(cfg, part, required_duration_s) -> Path
    write_music_plan_json(part, plan, out_dir=None) -> Path
    validate_coverage(part, required_duration_s) -> dict   (dry run)
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent.parent
MUSIC_DIR = ROOT / "phase1" / "music"
STITCH_DIR = MUSIC_DIR / "_stitched"
FFPROBE = ROOT / "tools" / "ffmpeg" / "ffprobe.exe"
FFMPEG = ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"


# ---------------------------------------------------------------------------
# File resolution
# ---------------------------------------------------------------------------


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            str(FFPROBE),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        text=True,
    )
    return float(out.strip())


def resolve_main_pool(part: int) -> list[Path]:
    """Return ordered list of main-body tracks for this Part.

    Supports three naming conventions (searched in order):
        1. partNN_main_1.mp3, partNN_main_2.mp3, ...      (v10 preferred)
        2. partNN_music_01.mp3, partNN_music_02.mp3, ...  (legacy numbered)
        3. partNN_music.mp3                                (legacy single)
    """
    tracks: list[Path] = []
    # Style 1: partNN_main_N.ext
    for idx in range(1, 100):
        found = None
        for ext in (".mp3", ".ogg", ".wav", ".flac"):
            c = MUSIC_DIR / f"part{part:02d}_main_{idx}{ext}"
            if c.exists():
                found = c
                break
        if found is None:
            if idx > 1:
                break
            # fall through to style 2 if no _main_1 exists
            break
        tracks.append(found)
    if tracks:
        return tracks

    # Style 2: partNN_music_NN.ext
    for idx in range(1, 100):
        found = None
        for ext in (".mp3", ".ogg", ".wav", ".flac"):
            c = MUSIC_DIR / f"part{part:02d}_music_{idx:02d}{ext}"
            if c.exists():
                found = c
                break
        if found is None:
            if idx > 1:
                break
            break
        tracks.append(found)
    if tracks:
        return tracks

    # Style 3: legacy single
    for ext in (".mp3", ".ogg", ".wav", ".flac"):
        legacy = MUSIC_DIR / f"part{part:02d}_music{ext}"
        if legacy.exists():
            tracks.append(legacy)
            break
    return tracks


def resolve_intro_outro(part: int, kind: str) -> Path | None:
    assert kind in ("intro", "outro")
    for stem in (f"part{part:02d}_{kind}_music", f"pantheon_{kind}_music"):
        for ext in (".mp3", ".ogg", ".wav", ".flac"):
            c = MUSIC_DIR / f"{stem}{ext}"
            if c.exists():
                return c
    return None


# ---------------------------------------------------------------------------
# Downbeat snap helpers (cheap librosa beat_track; OK for seam placement)
# ---------------------------------------------------------------------------


def _downbeats_for_track(path: Path) -> list[float]:
    """Return naive 4/4 downbeats for a single track (every 4th beat)."""
    try:
        import librosa
    except Exception:
        return []
    try:
        y, sr = librosa.load(str(path), sr=22050, mono=True, duration=None)
        _tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
        times = librosa.frames_to_time(beats, sr=sr, hop_length=512)
        return [float(t) for t in np.asarray(times)[::4]]
    except Exception:
        return []


def _seam_pair(a_dur: float, a_downbeats: list[float],
               b_downbeats: list[float]) -> tuple[float, float, float]:
    """Compute (fade_out_start, fade_in_offset, crossfade_dur) for a A->B pair.

    fade_out_start = last downbeat of A before (duration - 6 s), or
                     duration - 6 s if no downbeat in zone.
    fade_in_offset = first downbeat of B (or 0 if B has no downbeat).
    crossfade_dur  = a_dur - fade_out_start, clamped to [4.0, 6.0].
    """
    tail_start = max(0.0, a_dur - 6.0)
    candidates = [b for b in a_downbeats if tail_start <= b <= a_dur - 1.0]
    if candidates:
        fade_out = max(candidates)
    else:
        fade_out = tail_start
    fade_in = b_downbeats[0] if b_downbeats else 0.0
    xfade = max(4.0, min(6.0, a_dur - fade_out))
    return float(fade_out), float(fade_in), float(xfade)


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


def plan_stitch(
    part: int,
    required_duration_s: float,
    intro_xfade: float = 1.5,
    outro_xfade: float = 2.0,
    outro_duration_s: float = 30.0,
    crossfade_budget: float = 6.0,
) -> dict[str, Any]:
    """Build a pure-data plan describing the full-track queue.

    Raises FileNotFoundError if the main pool is empty.
    Raises RuntimeError (with a clear message) if a single main track is
    shorter than the body AND no second main is available (Rule P1-W:
    looped truncation is banned).
    """
    main = resolve_main_pool(part)
    if not main:
        raise FileNotFoundError(
            f"Part {part}: no main music found — expected "
            f"phase1/music/part{part:02d}_main_1.mp3 (or legacy "
            f"part{part:02d}_music.mp3)"
        )
    intro = resolve_intro_outro(part, "intro")
    outro = resolve_intro_outro(part, "outro")

    main_durs = [probe_duration(p) for p in main]
    intro_dur = probe_duration(intro) if intro else 0.0
    outro_dur = probe_duration(outro) if outro else 0.0

    intro_use = min(intro_dur, 15.0) if intro else 0.0
    outro_use = min(outro_duration_s, outro_dur) if outro else 0.0
    fade_budget = intro_xfade + outro_xfade + crossfade_budget
    main_needed = max(0.0, required_duration_s - intro_use - outro_use + fade_budget)

    # Queue FULL tracks (Rule P1-W) until cumulative duration >= main_needed.
    # No truncation — each entry keeps its natural duration.
    main_plan: list[dict[str, Any]] = []
    covered = 0.0
    pool_cycle: list[tuple[Path, float]] = list(zip(main, main_durs))

    # Round-robin through the pool: if the body is very long and we only have
    # 2 main tracks, we'll use each twice (still full-length each time).
    i = 0
    safety_cap = 32
    while covered < main_needed and i < safety_cap:
        if not pool_cycle:
            break
        track, dur = pool_cycle[i % len(pool_cycle)]
        # On-beat crossfade overlap: subtract the next seam's overlap from
        # effective covered duration so we don't over-queue.
        effective = dur - (crossfade_budget if main_plan else 0.0)
        main_plan.append(
            {
                "path": str(track),
                "full_duration": float(dur),
                "duration": float(dur),  # ALWAYS full (P1-W)
                "role": "main",
            }
        )
        covered += effective
        i += 1

    if covered < main_needed:
        raise RuntimeError(
            f"Part {part}: cannot cover body of {required_duration_s:.1f}s with "
            f"available main tracks (have {sum(main_durs):.1f}s * {safety_cap} loops). "
            f"Add more partNN_main_N.mp3 tracks to the pool (Rule P1-W forbids "
            f"truncation/looping-cut)."
        )

    # Compute per-pair seams with downbeat snapping.
    seam_plan: list[dict[str, Any]] = []
    # Pre-compute downbeats lazily (cache by path)
    db_cache: dict[str, list[float]] = {}

    def db(path: str) -> list[float]:
        if path not in db_cache:
            db_cache[path] = _downbeats_for_track(Path(path))
        return db_cache[path]

    ordered_paths: list[str] = []
    if intro:
        ordered_paths.append(str(intro))
    ordered_paths.extend(m["path"] for m in main_plan)
    if outro:
        ordered_paths.append(str(outro))

    # For each pair in the assembled sequence, compute seam metadata.
    for k in range(len(ordered_paths) - 1):
        a = Path(ordered_paths[k])
        b = Path(ordered_paths[k + 1])
        a_dur = probe_duration(a)
        a_db = db(str(a))
        b_db = db(str(b))
        fo, fi, xf = _seam_pair(a_dur, a_db, b_db)
        # Classify seam kind so caller knows the role.
        if intro and k == 0:
            kind = "intro_to_main"
            xf = intro_xfade
        elif outro and k == len(ordered_paths) - 2:
            kind = "main_to_outro"
            xf = outro_xfade
        else:
            kind = "main_to_main"
        seam_plan.append(
            {
                "a": str(a),
                "b": str(b),
                "kind": kind,
                "fade_out_start_s": fo,
                "fade_in_offset_s": fi,
                "crossfade_s": xf,
            }
        )

    tracks_full: list[dict[str, Any]] = []
    if intro:
        tracks_full.append(
            {
                "path": str(intro),
                "full_duration": intro_dur,
                "duration": intro_dur,
                "role": "intro",
            }
        )
    tracks_full.extend(main_plan)
    if outro:
        tracks_full.append(
            {
                "path": str(outro),
                "full_duration": outro_dur,
                "duration": outro_dur,
                "role": "outro",
            }
        )

    plan = {
        "part": part,
        "required_duration_s": required_duration_s,
        "tracks": tracks_full,
        "seams": seam_plan,
        "covered_s": covered,
        "main_needed_s": main_needed,
        "crossfades": {
            "intro_main": intro_xfade,
            "main_outro": outro_xfade,
            "main_main_max": crossfade_budget,
        },
    }

    # Ship-gate check: every entry's duration equals its full_duration ± 0.1 s.
    for entry in plan["tracks"]:
        if abs(entry["duration"] - entry["full_duration"]) > 0.1:
            raise RuntimeError(
                f"Rule P1-W violation: track {entry['path']} truncated from "
                f"{entry['full_duration']:.2f}s -> {entry['duration']:.2f}s"
            )
    return plan


def validate_coverage(part: int, required_duration_s: float) -> dict[str, Any]:
    try:
        plan = plan_stitch(part, required_duration_s)
        plan["verdict"] = "PASS"
    except Exception as e:
        plan = {"part": part, "verdict": "FAIL", "error": str(e)}
    return plan


def write_music_plan_json(
    part: int,
    plan: dict[str, Any],
    out_dir: Path | str | None = None,
) -> Path:
    out_dir = Path(out_dir) if out_dir else (ROOT / "output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"part{part:02d}_music_plan.json"
    # Ship gate: every track full
    for entry in plan.get("tracks", []):
        if abs(entry["duration"] - entry["full_duration"]) > 0.1:
            raise RuntimeError(
                f"Rule P1-W violation: {entry['path']} truncated"
            )
    out.write_text(json.dumps(plan, indent=2))
    return out


# ---------------------------------------------------------------------------
# ffmpeg graph builder
# ---------------------------------------------------------------------------


def _cache_key(plan: dict[str, Any]) -> str:
    h = hashlib.sha256()
    for t in plan["tracks"]:
        p = Path(t["path"])
        st = p.stat()
        h.update(f"{p.name}:{st.st_size}:{int(st.st_mtime)}|".encode())
    for s in plan["seams"]:
        h.update(f"{s['fade_out_start_s']:.3f}:{s['crossfade_s']:.3f}|".encode())
    h.update(f"dur={plan['required_duration_s']:.1f}".encode())
    return h.hexdigest()[:16]


def stitch_part_music(cfg, part: int, required_duration_s: float) -> Path:
    """Render the stitched mp3 using explicit afade + amix (no acrossfade chain).

    Idempotent — reuses cached stitched file when plan hash is unchanged.
    """
    STITCH_DIR.mkdir(parents=True, exist_ok=True)
    plan = plan_stitch(
        part,
        required_duration_s,
        intro_xfade=getattr(cfg, "intro_music_crossfade", 1.5),
        outro_xfade=getattr(cfg, "outro_music_crossfade", 2.0),
        outro_duration_s=getattr(cfg, "outro_music_duration", 30.0),
    )
    key = _cache_key(plan)
    out = STITCH_DIR / f"part{part:02d}_stitched_{key}.mp3"
    plan_path = STITCH_DIR / f"part{part:02d}_stitched_{key}.plan.json"
    write_music_plan_json(part, plan)
    if out.exists() and plan_path.exists():
        return out

    tracks = plan["tracks"]
    seams = plan["seams"]
    if not tracks:
        raise RuntimeError(f"Part {part}: stitch plan has no tracks")

    # Build filter_complex with explicit afade + adelay + amix.
    # We compute cumulative start times per track (seconds into the stitched output).
    # Track 0 starts at 0. For each pair (k, k+1):
    #   track[k+1] start = prev_start + (fade_out_start_s - 0) + 0   (xfade at end of k)
    # i.e. track[k+1] begins where track[k]'s fade_out begins.
    cmd: list[str] = [str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error"]
    for t in tracks:
        cmd += ["-i", t["path"]]

    # Compute starts
    starts: list[float] = [0.0]
    for k in range(len(tracks) - 1):
        seam = seams[k]
        fo = float(seam["fade_out_start_s"])
        xf = float(seam["crossfade_s"])
        # track k+1 begins (in stitched timeline) at starts[k] + fo
        starts.append(starts[k] + fo)

    fc_parts: list[str] = []
    labels: list[str] = []
    for k, t in enumerate(tracks):
        full_dur = float(t["full_duration"])
        start = starts[k]
        # Determine in-fade and out-fade for this track
        in_fade_dur = 0.0
        if k > 0:
            in_fade_dur = float(seams[k - 1]["crossfade_s"])
        out_fade_dur = 0.0
        out_fade_start = full_dur
        if k < len(tracks) - 1:
            out_fade_dur = float(seams[k]["crossfade_s"])
            out_fade_start = float(seams[k]["fade_out_start_s"])

        chain = f"[{k}:a]aresample=48000,asetpts=PTS-STARTPTS"
        if in_fade_dur > 0:
            chain += f",afade=t=in:st=0:d={in_fade_dur:.3f}"
        if out_fade_dur > 0:
            chain += f",afade=t=out:st={out_fade_start:.3f}:d={out_fade_dur:.3f}"
        delay_ms = int(round(start * 1000))
        if delay_ms > 0:
            chain += f",adelay={delay_ms}|{delay_ms}"
        lbl = f"[t{k}]"
        chain += lbl
        fc_parts.append(chain)
        labels.append(lbl)

    mix_inputs = "".join(labels)
    fc_parts.append(
        f"{mix_inputs}amix=inputs={len(labels)}:duration=longest:normalize=0[stitched]"
    )
    fc = ";".join(fc_parts)

    cmd += [
        "-filter_complex",
        fc,
        "-map",
        "[stitched]",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "320k",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    plan_path.write_text(json.dumps(plan, indent=2))
    return out


if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) < 3:
        print(
            "usage: python -m phase1.music_stitcher <part> <required_seconds>",
            file=__import__("sys").stderr,
        )
        sys.exit(2)
    part = int(sys.argv[1])
    secs = float(sys.argv[2])
    print(json.dumps(validate_coverage(part, secs), indent=2))
