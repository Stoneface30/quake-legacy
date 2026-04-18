"""
Part v6 — Direct-render path parameterised over Part number.

Applies ALL post-Part-4-review + 2026-04-18 rules:
  * Rule P1-N: PANTHEON 7 s + Title Card 8 s
  * Rule P1-G revised: game audio 1.0, music 0.5
  * Rule P1-H: hard cuts only
  * Rule P1-K revised: FP backbone + ONE FL 0.5× slow cut (already in styleb clip list)
  * Rule P1-L: 1 s head / 2 s tail trim (applied in chunk builder)
  * Rule P1-O: music continuous, no silence gaps
  * Rule P1-P: full-length clip contract (no sub-clip fragments)
  * Rule P1-R: three-track music (intro + playlist + outro) via music_stitcher
  * Rule P1-S: beat-sync may NEVER shorten a clip — we just concat chunks

Usage:
    python phase1/render_part_v6.py --part 4
    python phase1/render_part_v6.py --part 5

Output:
    output/Part{N}_v6_newrules_2026-04-18.mp4
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from phase1.config import Config
from phase1.title_card import render_title_card
from phase1.clip_list import parse_clip_entry
from phase1.normalize import normalize_clip
from phase1.experiment import resolve_clip_path
from phase1.music_stitcher import stitch_part_music, validate_coverage
from phase1.beat_sync import (
    load_beats, snap_xfade_offsets, find_beats_file,
)
from phase1.silence_detect import analyze_silence

ROOT = Path("G:/QUAKE_LEGACY")
OUTPUT_DIR = ROOT / "output"
ASSETS_DIR = ROOT / "phase1" / "assets"

# Target output filename convention.
OUTPUT_NAME_TMPL = "Part{n}_v6_newrules_2026-04-18.mp4"

# Part 4 already has body chunks under this legacy v5 folder — reuse them
# (they were built by phase1.pipeline._assemble_via_concat_demuxer using the
# same trim+scale params we would use here, so semantically identical).
LEGACY_CHUNK_DIRS = {
    4: OUTPUT_DIR / "_part4_v5_body_chunks",
}


def _probe_duration(path: Path, cfg: Config) -> float:
    out = subprocess.check_output(
        [str(cfg.ffprobe_bin), "-v", "error",
         "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        text=True,
    )
    return float(out.strip())


def _sum_duration(paths: List[Path], cfg: Config) -> float:
    t = 0.0
    for p in paths:
        t += _probe_duration(p, cfg)
    return t


def normalize_and_expand(part: int, clip_list_path: Path, cfg: Config) -> List[Path]:
    """Parse clip list, resolve + normalize each segment with slow/zoom/fast flags.
    Returns ordered list of normalized mp4s (one per segment).

    Clip list is passed through tier-interleave (Rule P1-U) so T1/T2/T3
    alternate — prevents "5 long T1 clips in a row" pacing regression.
    """
    lines = clip_list_path.read_text(encoding="utf-8").splitlines()
    entries = [parse_clip_entry(l) for l in lines
               if l.strip() and not l.strip().startswith("#")]
    norm_dir = cfg.output_dir / "normalized"
    norm_dir.mkdir(parents=True, exist_ok=True)

    # Rule P1-U (Part 5 v7 review 2026-04-18): tier-interleave the ordered list.
    def _tier_of(entry) -> str:
        first = entry.segments[0] if entry.segments else ""
        src = resolve_clip_path(first, part, cfg)
        if src is None:
            return "?"
        s = str(src).upper()
        if "\\T1\\" in s or "/T1/" in s: return "T1"
        if "\\T2\\" in s or "/T2/" in s: return "T2"
        if "\\T3\\" in s or "/T3/" in s: return "T3"
        return "?"
    pre_order = [_tier_of(e) for e in entries]
    entries = interleave_clips_by_tier(entries, _tier_of)
    post_order = [_tier_of(e) for e in entries]
    print(f"  [tier-interleave] {pre_order[:15]}... → {post_order[:15]}...")

    normalized: List[Path] = []
    silence_forced = 0
    short_t1_forced = 0
    for entry in entries:
        entry_tier = _tier_of(entry)
        # Rule P1-Q: short-T1 auto-slowmo (user 2026-04-18 "check for t1 auto
        # slowmo when the clip is short"). Probe the first segment's duration;
        # if the post-trim body is under threshold AND the entry has no speed
        # mod yet AND the clip is tier T1, flip entry.slow.
        if (entry_tier == "T1"
                and not (entry.slow or entry.speedup or entry.zoom)
                and entry.segments):
            first_src = resolve_clip_path(entry.segments[0], part, cfg)
            if first_src is not None:
                try:
                    is_fl = "FL" in first_src.stem.upper()
                    head = (cfg.clip_head_trim_fl if is_fl
                            else cfg.clip_head_trim_fp)
                    dur_full = _probe_duration(first_src, cfg)
                    post_trim = dur_full - head - cfg.clip_tail_trim
                    if 0 < post_trim < cfg.short_t1_slowmo_threshold:
                        entry.slow = True
                        short_t1_forced += 1
                        print(f"  [short-T1-slow] {first_src.name} "
                              f"(post-trim={post_trim:.2f}s)")
                except Exception:
                    pass

        for seg_idx, seg_filename in enumerate(entry.segments):
            src = resolve_clip_path(seg_filename, part, cfg)
            if src is None:
                print(f"  [WARN] Not found: {seg_filename}")
                continue
            # Rule P1-V: silence-detect auto-forces fast-forward on dead-time clips.
            # Only inspect if entry didn't already request a speed mod and the
            # review mode hasn't opted out of the slow per-clip probe.
            if (not (entry.slow or entry.speedup or entry.zoom)
                    and not (cfg.review_mode and cfg.review_skip_silence_detect)):
                try:
                    rep = analyze_silence(src, cfg.ffmpeg_bin)
                    if rep.should_speedup:
                        entry.speedup = True
                        silence_forced += 1
                        print(f"  [silence-ff] {src.name} "
                              f"(frac={rep.silent_frac:.2f} "
                              f"longest={rep.longest_silence:.1f}s)")
                except Exception as exc:
                    pass  # analyzer is advisory; don't block render
            is_slow    = entry.slow    and seg_idx == len(entry.segments) - 1
            is_zoom    = entry.zoom    and seg_idx == 0
            is_speedup = entry.speedup and seg_idx == 0
            base_dst = norm_dir / (src.stem + "_cfr60.mp4")
            if is_slow:
                dst = base_dst.parent / (base_dst.stem + "_slow.mp4")
            elif is_zoom:
                dst = base_dst.parent / (base_dst.stem + "_zoom.mp4")
            elif is_speedup:
                dst = base_dst.parent / (base_dst.stem + "_fast.mp4")
            else:
                dst = base_dst
            if not dst.exists():
                print(f"  Normalizing: {src.name}")
                normalize_clip(src, dst, cfg,
                               slow=is_slow, zoom=is_zoom, speedup=is_speedup)
            normalized.append(dst)
    if silence_forced:
        print(f"  [silence-ff] {silence_forced} clips auto-speedup "
              f"due to internal silence")
    return normalized


def build_body_chunks(
    part: int,
    normalized: List[Path],
    chunks_dir: Path,
    cfg: Config,
) -> tuple[Path, List[Path]]:
    """Pre-encode each normalized clip as a CRF 20 fast libx264 chunk with
    Rule P1-L trim (1 s head / 2 s tail). Returns (concat_list_path, chunks).

    Idempotent — skips chunks that already exist.
    """
    chunks_dir.mkdir(parents=True, exist_ok=True)
    chunks: List[Path] = []
    tail = cfg.clip_tail_trim

    for i, src in enumerate(normalized):
        chunk = chunks_dir / f"chunk_{i:04d}.mp4"
        chunks.append(chunk)
        if chunk.exists():
            continue
        # Rule P1-L v2: FL clips have ~2s of console/loading header;
        # FP clips only ~1s. Detect via substring — normalized filenames encode
        # angle in the stem (e.g. "Demo100FL-0000_cfr60"). Earlier token-split
        # detection was broken because "FL" was never a standalone token after
        # normalization.
        is_fl = "FL" in src.stem.upper()
        head = cfg.clip_head_trim_fl if is_fl else cfg.clip_head_trim_fp
        dur_full = _probe_duration(src, cfg)
        # Fallback min 0.5s body for pre-trimmed slow-mo expansions.
        trim_dur = max(0.5, dur_full - head - tail)

        # Rule P1-D (review burn-in): bottom-left clip-stem watermark so the
        # user can reference specific clips by name during review. Strip
        # normalization suffixes so the watermark matches the source .avi.
        vf = f"scale={cfg.target_width}:{cfg.target_height}:flags=lanczos,fps={cfg.target_fps}"
        if cfg.review_burn_clip_name:
            stem = src.stem
            for suf in ("_cfr60_slow", "_cfr60_zoom", "_cfr60_fast", "_cfr60"):
                if stem.endswith(suf):
                    stem = stem[: -len(suf)]
                    break
            # Escape ffmpeg drawtext specials.
            safe = (stem.replace("\\", "\\\\\\\\").replace(":", "\\:")
                        .replace("'", "\\'").replace("%", "\\%"))
            alpha = cfg.review_watermark_opacity
            vf += (
                f",drawtext=fontfile='C\\:/Windows/Fonts/consola.ttf':"
                f"text='{safe}':"
                f"fontsize={cfg.review_watermark_fontsize}:"
                f"fontcolor=white@{alpha}:"
                f"borderw=2:bordercolor=black@{alpha}:"
                f"x=24:y=h-th-24"
            )

        cmd = [
            str(cfg.ffmpeg_bin), "-y",
            "-ss", f"{head:.3f}",
            "-t",  f"{trim_dur:.3f}",
            "-i",  str(src),
            "-vf", vf,
            "-af", "aresample=async=1",
            "-c:v", "libx264",
            "-crf", str(cfg.review_chunk_crf if cfg.review_mode else 20),
            "-preset", (cfg.review_chunk_preset if cfg.review_mode else "fast"),
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-r", str(cfg.target_fps),
            "-g", str(cfg.target_fps * 2),
            "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
            "-movflags", "+faststart",
            str(chunk),
        ]
        print(f"  [chunk {i+1}/{len(normalized)}] {src.name}")
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise RuntimeError(f"chunk build failed on {src.name}:\n{r.stderr[-500:]}")

    concat_list = chunks_dir / "_concat.txt"
    concat_list.write_text(
        "".join(f"file '{p.as_posix()}'\n" for p in chunks),
        encoding="utf-8",
    )
    return concat_list, chunks


def assemble_body_with_xfades(
    chunks: List[Path],
    out_path: Path,
    cfg: Config,
    beat_snapped_offsets: Optional[List[float]] = None,
) -> Path:
    """Concat all body chunks into one mp4 with short xfade seams between every
    chunk. Replaces the concat-demuxer hard-cut body for Part 5 v8+.

    Xfade duration = cfg.seam_xfade_duration (default 0.15s). Each xfade eats
    the last 0.15s of chunk N and first 0.15s of chunk N+1 — net body length
    shrinks by (N-1) * xfade unless offsets are beat-snapped (then the math
    is the supplied offsets directly).

    If `beat_snapped_offsets` is given, it must be a list of length N-1 with
    body-absolute xfade start times from beat_sync.snap_xfade_offsets.
    Otherwise naive cumulative offsets are used (hard rhythm, no beat align).

    Uses one giant filter_complex across all N chunk inputs. Practical up to
    ~140 chunks on 32 GB RAM.
    """
    if out_path.exists():
        print(f"  [cache] {out_path.name}")
        return out_path

    N = len(chunks)
    if N == 0:
        raise RuntimeError("assemble_body_with_xfades: zero chunks")
    if N == 1:
        # Nothing to xfade — just copy
        subprocess.run([str(cfg.ffmpeg_bin), "-y", "-i", str(chunks[0]),
                        "-c", "copy", str(out_path)], check=True)
        return out_path

    x = cfg.seam_xfade_duration
    durs = [_probe_duration(c, cfg) for c in chunks]

    # Decide xfade offsets: beat-snapped or naive cumulative.
    if beat_snapped_offsets is not None:
        if len(beat_snapped_offsets) != N - 1:
            raise ValueError(
                f"beat_snapped_offsets length {len(beat_snapped_offsets)} "
                f"!= N-1 ({N-1})"
            )
        offsets = list(beat_snapped_offsets)
        print(f"  [xfade] using beat-snapped offsets ({N-1} seams)")
    else:
        offsets = []
        cum = 0.0
        for i in range(N - 1):
            cum += durs[i] - x
            offsets.append(sum(durs[:i+1]) - (i+1) * x)
        print(f"  [xfade] naive cumulative offsets ({N-1} seams)")

    # Build filter_complex
    v_parts = []
    a_parts = []
    # Normalize every input first so SAR/fps match exactly (defensive)
    for i in range(N):
        v_parts.append(
            f"[{i}:v]setsar=1,fps={cfg.target_fps},format=yuv420p[v{i}]"
        )
        a_parts.append(f"[{i}:a]aresample=async=1[a{i}]")

    prev_v = "v0"
    prev_a = "a0"
    xchain = []
    achain = []
    for i in range(1, N):
        out_v = f"vx{i}"
        out_a = f"ax{i}"
        seam_offset = offsets[i - 1]
        xchain.append(
            f"[{prev_v}][v{i}]xfade=transition=fade:duration={x:.3f}:"
            f"offset={seam_offset:.3f}[{out_v}]"
        )
        achain.append(
            f"[{prev_a}][a{i}]acrossfade=d={x:.3f}[{out_a}]"
        )
        prev_v = out_v
        prev_a = out_a

    filter_complex = ";".join(v_parts + a_parts + xchain + achain)
    final_v = prev_v
    final_a = prev_a

    input_args: List[str] = []
    for c in chunks:
        input_args += ["-i", str(c)]

    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        *input_args,
        "-filter_complex", filter_complex,
        "-map", f"[{final_v}]", "-map", f"[{final_a}]",
        "-c:v", "libx264",
        "-crf", str(cfg.review_body_crf if cfg.review_mode else 18),
        "-preset", (cfg.review_body_preset if cfg.review_mode else "fast"),
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-r", str(cfg.target_fps),
        "-g", str(cfg.target_fps * 2),
        "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
        "-movflags", "+faststart",
        str(out_path),
    ]
    print(f"  [body-xfade] {N} chunks → {out_path.name} (xfade={x}s"
          f"{', review=fast' if cfg.review_mode else ''})")
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"body xfade assembly failed:\n{r.stderr[-1500:]}")
    return out_path


def interleave_clips_by_tier(entries, resolver):
    """Rebalance ordered clip-list entries so clips from the same tier don't
    cluster. Round-robin by tier bucket (T1/T2/T3) while preserving local
    ordering within each bucket.

    `resolver(entry) -> str` returns a tier tag ("T1"/"T2"/"T3"/"?") — looked up
    from the first segment's resolved path.
    """
    from collections import defaultdict, deque
    buckets: dict[str, deque] = defaultdict(deque)
    for e in entries:
        buckets[resolver(e)].append(e)

    # Priority order: T2 (main meal) first, T1 (rare/peak) sprinkled,
    # T3 (filler) woven between. Ratio roughly matches their weight.
    order = ["T2", "T1", "T3", "T2", "T3", "T1", "T2"]
    result = []
    # Round-robin until all buckets empty
    while any(buckets[t] for t in ("T1", "T2", "T3", "?")):
        progress = False
        for tier in order:
            if buckets[tier]:
                result.append(buckets[tier].popleft())
                progress = True
        # drain unknowns last, but keep the loop alive if no named-tier clips left
        if buckets["?"]:
            result.append(buckets["?"].popleft())
            progress = True
        if not progress:
            break
    return result


def ensure_title_card(part: int, cfg: Config) -> Path:
    out = ASSETS_DIR / f"title_card_part{part:02d}.mp4"
    if out.exists():
        print(f"  [cache] {out.name}")
        return out
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    render_title_card(part, out, cfg)
    return out


def ensure_pantheon_trim(cfg: Config) -> Path:
    out = OUTPUT_DIR / "_pantheon_trim_7s.mp4"
    if out.exists():
        print(f"  [cache] {out.name}")
        return out
    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        "-ss", "0", "-t", str(cfg.intro_clip_duration),
        "-i", str(cfg.intro_source),
        "-c:v", "libx264", "-crf", "17", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-r", str(cfg.target_fps),
        "-vf", f"scale={cfg.target_width}:{cfg.target_height}:flags=lanczos",
        "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


def final_render(
    part: int,
    pantheon_trim: Path,
    title_card: Path,
    body_path: Path,
    music_path: Path,
    final_out: Path,
    cfg: Config,
) -> None:
    """Single ffmpeg invocation:
      inputs: [0]PANTHEON [1]title [2]body (pre-xfaded single mp4) [3]stitched music
      audio: music layers across ENTIRE video (Rule P1-G v3). PANTHEON keeps its
             own foreground audio. Body keeps game audio foreground. Music
             at cfg.music_volume under all three.
      video: PANTHEON + title + body (hard cuts at intro seams; seam xfades
             inside body were already baked in by assemble_body_with_xfades).
      encoder: AV1 NVENC p7 uhq 10-bit cq=18.
    """
    filter_complex = (
        # Video: plain concat of 3 files (body already has internal xfades)
        f"[0:v][1:v][2:v]concat=n=3:v=1:a=0[vout];"
        # Build a "foreground" audio track: PANTHEON audio + silent title + body game
        f"[0:a]aresample=48000:async=1,volume=1.0[pa];"
        f"[1:a]aresample=48000:async=1,volume=1.0[ta];"
        f"[2:a]aresample=48000:async=1,volume={cfg.game_audio_volume}[ga];"
        f"[pa][ta][ga]concat=n=3:v=0:a=1[fgtrack];"
        # Music layer across entire output
        f"[3:a]volume={cfg.music_volume},aresample=48000:async=1[mus];"
        # Amix foreground + music. duration=first keeps video length as-is
        f"[fgtrack][mus]amix=inputs=2:duration=first:normalize=0[aout]"
    )

    # Review mode = libx264 veryfast draft. Final mode = AV1 NVENC UHQ 10-bit.
    if cfg.review_mode:
        codec  = "libx264"
        cq     = cfg.review_final_crf
        preset = cfg.review_final_preset
        tune   = "review"
    else:
        codec  = cfg.final_render_nvenc_codec
        cq     = cfg.final_render_nvenc_cq
        preset = cfg.final_render_nvenc_preset
        tune   = cfg.final_render_nvenc_tune

    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        "-i", str(pantheon_trim),
        "-i", str(title_card),
        "-i", str(body_path),
        "-i", str(music_path),
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
    ]
    if cfg.review_mode:
        cmd += [
            "-c:v", "libx264",
            "-crf", str(cfg.review_final_crf),
            "-preset", cfg.review_final_preset,
            "-profile:v", "main", "-pix_fmt", "yuv420p",
        ]
    else:
        cmd += [
            "-c:v", codec,
            "-preset", preset,
            "-tune", tune,
            "-multipass", "fullres",
            "-spatial-aq", "1",
            "-temporal-aq", "1",
            "-rc-lookahead", "32",
            "-b_ref_mode", "middle",
            "-bf", "4",
            "-rc", "vbr", "-b:v", "0", "-cq", str(cq),
        ]
        if cfg.final_render_nvenc_highbitdepth and codec in ("av1_nvenc", "hevc_nvenc"):
            cmd += ["-highbitdepth", "1", "-pix_fmt", cfg.final_render_nvenc_pix_fmt]
        else:
            cmd += ["-pix_fmt", "yuv420p"]

    cmd += [
        "-r", str(cfg.target_fps),
        "-g", str(cfg.target_fps * 2),
        "-c:a", "aac", "-ar", "48000", "-b:a", cfg.audio_bitrate,
        "-movflags", "+faststart",
        str(final_out),
    ]

    print(f"Final render ({codec} cq={cq} preset={preset} tune={tune})")
    print(f"  Output: {final_out.name}")
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("[ERROR] NVENC final render failed. Tail of stderr:")
        print(r.stderr[-2500:])
        # libx264 CRF 17 slow fallback — mirrors v5_direct path.
        print("\n  Retrying with libx264 CRF 17 slow fallback...")
        fb = cmd[:]
        nvenc_start = fb.index("-c:v")
        r_idx = fb.index("-r", nvenc_start)
        fb[nvenc_start:r_idx] = [
            "-c:v", "libx264", "-crf", "17", "-preset", "slow",
            "-profile:v", "high", "-pix_fmt", "yuv420p", "-bf", "2",
        ]
        r2 = subprocess.run(fb, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
        if r2.returncode != 0:
            print("[FATAL] libx264 fallback also failed:")
            print(r2.stderr[-2500:])
            raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    ap.add_argument("--clip-list",
                    help="Override clip list name (default: partNN_styleb.txt)")
    ap.add_argument("--chunks-dir",
                    help="Override chunks dir (default: output/_part{N}_v6_body_chunks)")
    ap.add_argument("--output",
                    help="Override final output file path (absolute or relative to project)")
    ap.add_argument("--review", action="store_true",
                    help="Draft/review mode: fast libx264 encoders, skip "
                         "silence-detect probe, watermark stays on. For 5-min "
                         "iteration cycles with the user. Final build drops "
                         "the flag for AV1 NVENC UHQ 10-bit quality ceiling.")
    ap.add_argument("--no-watermark", action="store_true",
                    help="Disable clip-name burn-in (use for final public render).")
    args = ap.parse_args()

    part = args.part
    cfg = Config()
    if args.review:
        cfg.review_mode = True
        print("[MODE] review/draft — fast encoders, silence-detect skipped, "
              "watermark ON")
    if args.no_watermark:
        cfg.review_burn_clip_name = False
        print("[MODE] clip-name watermark OFF")
    started = time.time()

    clip_list_name = args.clip_list or f"part{part:02d}_styleb.txt"
    clip_list_path = cfg.clip_lists_dir / clip_list_name
    if not clip_list_path.exists():
        print(f"[FATAL] clip list missing: {clip_list_path}")
        return 1

    # Pick chunk dir. Reuse legacy v5 folder for Part 4 if caller didn't override.
    if args.chunks_dir:
        chunks_dir = Path(args.chunks_dir)
    elif part in LEGACY_CHUNK_DIRS and LEGACY_CHUNK_DIRS[part].exists():
        chunks_dir = LEGACY_CHUNK_DIRS[part]
        print(f"[reuse] legacy chunk dir {chunks_dir.name}")
    else:
        chunks_dir = OUTPUT_DIR / f"_part{part:02d}_v6_body_chunks"

    concat_list = chunks_dir / "_concat.txt"

    # --- Body chunks ---
    if concat_list.exists() and any(chunks_dir.glob("chunk_*.mp4")):
        chunks = sorted(chunks_dir.glob("chunk_*.mp4"))
        print(f"[reuse] {len(chunks)} existing chunks in {chunks_dir.name}")
    else:
        print(f"Normalizing + expanding clip list {clip_list_name}...")
        normalized = normalize_and_expand(part, clip_list_path, cfg)
        if not normalized:
            print("[FATAL] no clips resolved")
            return 1
        print(f"  {len(normalized)} segments → building chunks at {chunks_dir}")
        concat_list, chunks = build_body_chunks(part, normalized, chunks_dir, cfg)

    # --- Intro assets ---
    title_card   = ensure_title_card(part, cfg)
    pantheon     = ensure_pantheon_trim(cfg)

    # --- Beat-snap seam offsets (Rule P1-V) ---
    # We need chunk durs first, then consult the main music track's pre-computed
    # beat grid. If no beats sidecar exists (or part skipped), fall back to naive.
    beat_snapped: Optional[List[float]] = None
    main_music = ROOT / "phase1" / "music" / f"part{part:02d}_music.mp3"
    beats_file = find_beats_file(main_music) if main_music.exists() else None
    if beats_file is not None and cfg.seam_xfade_duration > 0 and len(chunks) > 1:
        durs = [_probe_duration(c, cfg) for c in chunks]
        beats = load_beats(beats_file)
        beat_snapped, stats = snap_xfade_offsets(
            durs=durs,
            beats=beats,
            xfade=cfg.seam_xfade_duration,
            intro_offset=cfg.intro_clip_duration + 8.0,  # PANTHEON + title
            max_shift=0.300,
        )
        print(f"  [beat-sync] {stats['snapped']}/{stats['n_seams']} seams "
              f"snapped ({stats['snap_rate']*100:.0f} %), "
              f"total shift {stats['total_shift']:.2f} s")

    # --- Body assembly: single mp4 with seam xfades (Rule P1-H v3) ---
    body_xfaded = chunks_dir / "_body_xfaded.mp4"
    if cfg.seam_xfade_duration > 0:
        assemble_body_with_xfades(chunks, body_xfaded, cfg,
                                  beat_snapped_offsets=beat_snapped)
    else:
        # hard-cut fallback via concat demuxer → remux into a single mp4
        if not body_xfaded.exists():
            subprocess.run([
                str(cfg.ffmpeg_bin), "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_list),
                "-c", "copy", str(body_xfaded)
            ], check=True)

    # --- Body duration for music budget (post-xfade) ---
    body_dur = _probe_duration(body_xfaded, cfg)
    total_video_dur = cfg.intro_clip_duration + 8.0 + body_dur  # PANTHEON + title + body
    # Music must cover the whole thing (intro under PANTHEON+title, main under body,
    # outro stretched across body tail; stitcher picks the crossfade points).
    required_music = total_video_dur + 2.0  # small tail pad
    print(f"\nBody duration : {body_dur:.1f} s ({body_dur/60:.1f} min)")
    print(f"Total video   : {total_video_dur:.1f} s ({total_video_dur/60:.1f} min)")
    print(f"Music budget  : {required_music:.1f} s")

    # --- Music stitch ---
    plan = validate_coverage(part, required_music)
    print(f"Music plan verdict: {plan['verdict']} "
          f"(main avail {plan['total_main_available_s']:.0f}s / "
          f"needed {plan['main_needed_s']:.0f}s)")
    if plan["verdict"] != "PASS":
        print("  [note] stitcher will loop the tail track to cover coverage gap.")
    music_path = stitch_part_music(cfg, part, required_music)
    print(f"Stitched music: {music_path}")

    # --- Final render ---
    if args.output:
        final_out = Path(args.output)
        if not final_out.is_absolute():
            final_out = ROOT / final_out
        final_out.parent.mkdir(parents=True, exist_ok=True)
    else:
        final_out = OUTPUT_DIR / OUTPUT_NAME_TMPL.format(n=part)
    final_render(part, pantheon, title_card, body_xfaded,
                 music_path, final_out, cfg)

    elapsed = time.time() - started
    size_mb = final_out.stat().st_size / 1024 / 1024
    print("\n" + "=" * 60)
    print(f"  [DONE] {final_out}")
    print(f"  Size : {size_mb:.1f} MB")
    print(f"  Time : {elapsed/60:.1f} min")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
