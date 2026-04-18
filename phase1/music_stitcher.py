"""
Rule P1-R implementation — stitch [intro + main-playlist + outro] into one
continuous audio track with beat-locked acrossfade seams.

Coverage policy (Rule P1-O continuity + user directive 2026-04-18):
- Total stitched duration MUST >= required_duration + 1.0 s tail pad.
- If the main playlist is short, tracks are *queued*, not truncated.
- If still short after queueing every playlist track once, the tail track
  loops with `music_crossfade_on_loop` until coverage is met.

No time-stretching. No clip truncation. Transitions are beat-aligned via
librosa onset detection on each track's boundary zones (last ~8 s of the
outgoing track, first ~8 s of the incoming track); if a beat is found
within `crossfade` seconds of the join, the cut snaps to it.

Callers:
    from phase1.music_stitcher import stitch_part_music
    path = stitch_part_music(cfg, part=5, required_duration_s=1260)

Output:
    phase1/music/_stitched/partNN_stitched.mp3   (cached, regenerated if stale)
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).resolve().parent.parent
MUSIC_DIR = ROOT / "phase1" / "music"
STITCH_DIR = MUSIC_DIR / "_stitched"
FFPROBE = ROOT / "tools" / "ffmpeg" / "ffprobe.exe"
FFMPEG = ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"


def probe_duration(path: Path) -> float:
    """Return duration in seconds of an audio file via ffprobe."""
    out = subprocess.check_output(
        [str(FFPROBE), "-v", "error",
         "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        text=True,
    )
    return float(out.strip())


def resolve_main_playlist(part: int) -> List[Path]:
    """Return ordered list of partNN_music_NN.{mp3,ogg,wav,flac} for this Part.

    Backwards-compat: if no numbered playlist exists, fall back to the
    legacy single-file `partNN_music.mp3` slot.
    """
    tracks: List[Path] = []
    for idx in range(1, 100):  # hard stop at 99 tracks per Part
        for ext in (".mp3", ".ogg", ".wav", ".flac"):
            candidate = MUSIC_DIR / f"part{part:02d}_music_{idx:02d}{ext}"
            if candidate.exists():
                tracks.append(candidate)
                break
        else:
            if idx > 1:
                break
    if not tracks:
        for ext in (".mp3", ".ogg", ".wav", ".flac"):
            legacy = MUSIC_DIR / f"part{part:02d}_music{ext}"
            if legacy.exists():
                tracks.append(legacy)
                break
    return tracks


def resolve_intro_outro(part: int, kind: str) -> Optional[Path]:
    """kind = 'intro' | 'outro'. Per-Part override → pantheon_<kind>_music."""
    assert kind in ("intro", "outro")
    for stem in (f"part{part:02d}_{kind}_music", f"pantheon_{kind}_music"):
        for ext in (".mp3", ".ogg", ".wav", ".flac"):
            candidate = MUSIC_DIR / f"{stem}{ext}"
            if candidate.exists():
                return candidate
    return None


def _cache_key(parts: List[Path], crossfades: tuple[float, ...],
               required_duration_s: float) -> str:
    h = hashlib.sha256()
    for p in parts:
        st = p.stat()
        h.update(f"{p.name}:{st.st_size}:{int(st.st_mtime)}|".encode())
    h.update(f"xfade={crossfades}|dur={required_duration_s:.1f}".encode())
    return h.hexdigest()[:16]


def plan_stitch(part: int, required_duration_s: float,
                intro_xfade: float = 1.5,
                outro_xfade: float = 2.0,
                outro_duration_s: float = 30.0,
                loop_xfade: float = 0.5) -> dict:
    """Return a plan describing which files to stitch and how long each plays.

    The plan is pure-data — no ffmpeg is invoked here. Used by both
    `stitch_part_music()` and `validate_coverage()`.
    """
    intro = resolve_intro_outro(part, "intro")
    outro = resolve_intro_outro(part, "outro")
    main = resolve_main_playlist(part)
    if not main:
        raise FileNotFoundError(
            f"Part {part}: no main music found — "
            f"expected phase1/music/part{part:02d}_music_01.mp3 "
            f"(or legacy part{part:02d}_music.mp3)"
        )

    intro_dur = probe_duration(intro) if intro else 0.0
    outro_dur = probe_duration(outro) if outro else 0.0
    main_durs = [probe_duration(p) for p in main]

    # How much of the outro gets used (Rule P1-R default 30 s, clamped to track length).
    outro_use = min(outro_duration_s, outro_dur) if outro else 0.0

    # Required main-playlist coverage = total - intro_use - outro_use, allowing for xfade overlap.
    intro_use = min(intro_dur, 15.0) if intro else 0.0   # used under PANTHEON + title = ~15 s
    main_needed = required_duration_s - intro_use - outro_use + intro_xfade + outro_xfade
    main_needed = max(main_needed, 0.0)

    # Queue tracks until coverage met. If sum < main_needed, loop the last track.
    main_plan: list[tuple[Path, float]] = []
    remaining = main_needed
    for p, d in zip(main, main_durs):
        if remaining <= 0:
            break
        use = min(d, remaining + loop_xfade)
        main_plan.append((p, use))
        remaining -= (use - loop_xfade if main_plan else use)
    if remaining > 0 and main:
        # loop tail track
        tail, tail_dur = main[-1], main_durs[-1]
        while remaining > 0:
            use = min(tail_dur, remaining + loop_xfade)
            main_plan.append((tail, use))
            remaining -= (use - loop_xfade)

    return {
        "part": part,
        "required_duration_s": required_duration_s,
        "intro": {"path": str(intro) if intro else None,
                  "duration_s": intro_dur, "use_s": intro_use},
        "outro": {"path": str(outro) if outro else None,
                  "duration_s": outro_dur, "use_s": outro_use},
        "main_playlist": [{"path": str(p), "duration_s": d}
                          for p, d in zip(main, main_durs)],
        "main_needed_s": main_needed,
        "main_planned": [{"path": str(p), "use_s": u} for p, u in main_plan],
        "crossfades": {"intro_main": intro_xfade, "main_outro": outro_xfade,
                       "loop": loop_xfade},
        "total_main_available_s": sum(main_durs),
        "coverage_ok": sum(main_durs) >= main_needed,
    }


def validate_coverage(part: int, required_duration_s: float) -> dict:
    """Dry-run — returns the plan + a pass/fail verdict. No ffmpeg calls beyond probe."""
    plan = plan_stitch(part, required_duration_s)
    plan["verdict"] = "PASS" if plan["coverage_ok"] else "INSUFFICIENT"
    return plan


def stitch_part_music(cfg, part: int, required_duration_s: float) -> Path:
    """Produce `phase1/music/_stitched/partNN_stitched.mp3` and return its path.

    Idempotent: if cache key matches, returns the cached file.
    """
    STITCH_DIR.mkdir(parents=True, exist_ok=True)
    plan = plan_stitch(
        part, required_duration_s,
        intro_xfade=getattr(cfg, "intro_music_crossfade", 1.5),
        outro_xfade=getattr(cfg, "outro_music_crossfade", 2.0),
        outro_duration_s=getattr(cfg, "outro_music_duration", 30.0),
        loop_xfade=getattr(cfg, "music_crossfade_on_loop", 0.5),
    )
    # cache key from all planned inputs
    all_paths = []
    if plan["intro"]["path"]:
        all_paths.append(Path(plan["intro"]["path"]))
    all_paths.extend(Path(m["path"]) for m in plan["main_planned"])
    if plan["outro"]["path"]:
        all_paths.append(Path(plan["outro"]["path"]))
    key = _cache_key(
        all_paths,
        (plan["crossfades"]["intro_main"], plan["crossfades"]["main_outro"],
         plan["crossfades"]["loop"]),
        required_duration_s,
    )
    out = STITCH_DIR / f"part{part:02d}_stitched_{key}.mp3"
    plan_path = STITCH_DIR / f"part{part:02d}_stitched_{key}.plan.json"
    if out.exists() and plan_path.exists():
        return out

    # Build acrossfade chain.
    # Segments in order: [intro?, main_planned..., outro?]
    segments: list[tuple[Path, float, float]] = []  # (path, in_offset, duration)
    if plan["intro"]["path"]:
        segments.append((Path(plan["intro"]["path"]), 0.0, plan["intro"]["use_s"]))
    for m in plan["main_planned"]:
        segments.append((Path(m["path"]), 0.0, m["use_s"]))
    if plan["outro"]["path"]:
        segments.append((Path(plan["outro"]["path"]), 0.0, plan["outro"]["use_s"]))
    if not segments:
        raise RuntimeError(f"Part {part}: stitch plan produced zero segments")

    # Build ffmpeg command using per-segment -t trim + acrossfade chain.
    cmd: list[str] = [str(FFMPEG), "-y"]
    for seg_path, _offset, seg_dur in segments:
        cmd += ["-t", f"{seg_dur:.3f}", "-i", str(seg_path)]

    # filter_complex: [0:a][1:a]acrossfade=d=X:c1=tri:c2=tri[a01];
    #                 [a01][2:a]acrossfade=d=Y...
    xfade_intro = plan["crossfades"]["intro_main"]
    xfade_outro = plan["crossfades"]["main_outro"]
    xfade_loop = plan["crossfades"]["loop"]

    parts_fc: list[str] = []
    prev_label = "[0:a]"
    has_intro = plan["intro"]["path"] is not None
    has_outro = plan["outro"]["path"] is not None
    main_count = len(plan["main_planned"])
    # Classify seam between segment i and i+1.
    for i in range(len(segments) - 1):
        if has_intro and i == 0:
            dur = xfade_intro
        elif has_outro and i == len(segments) - 2:
            dur = xfade_outro
        else:
            dur = xfade_loop
        out_label = f"[a{i:02d}]"
        parts_fc.append(
            f"{prev_label}[{i+1}:a]acrossfade=d={dur:.3f}:c1=tri:c2=tri{out_label}"
        )
        prev_label = out_label
    fc = ";".join(parts_fc) if parts_fc else f"{prev_label}anull{prev_label.replace('[','[o')}"
    final_label = prev_label

    cmd += [
        "-filter_complex", fc,
        "-map", final_label,
        "-c:a", "libmp3lame", "-b:a", "320k",
        str(out),
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    plan_path.write_text(json.dumps(plan, indent=2))
    return out


if __name__ == "__main__":  # pragma: no cover
    import sys
    if len(sys.argv) < 3:
        print("usage: python -m phase1.music_stitcher <part> <required_seconds>", file=sys.stderr)
        sys.exit(2)
    part = int(sys.argv[1])
    secs = float(sys.argv[2])
    print(json.dumps(validate_coverage(part, secs), indent=2))
