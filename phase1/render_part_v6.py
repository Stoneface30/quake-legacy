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
    """
    lines = clip_list_path.read_text(encoding="utf-8").splitlines()
    entries = [parse_clip_entry(l) for l in lines
               if l.strip() and not l.strip().startswith("#")]
    norm_dir = cfg.output_dir / "normalized"
    norm_dir.mkdir(parents=True, exist_ok=True)

    normalized: List[Path] = []
    for entry in entries:
        for seg_idx, seg_filename in enumerate(entry.segments):
            src = resolve_clip_path(seg_filename, part, cfg)
            if src is None:
                print(f"  [WARN] Not found: {seg_filename}")
                continue
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
    head = cfg.clip_head_trim
    tail = cfg.clip_tail_trim

    for i, src in enumerate(normalized):
        chunk = chunks_dir / f"chunk_{i:04d}.mp4"
        chunks.append(chunk)
        if chunk.exists():
            continue
        dur_full = _probe_duration(src, cfg)
        # Apply 1 s head / 2 s tail (Rule P1-L). For very short clips
        # (e.g. slow-mo expansions already pre-trimmed), fall back to a
        # minimum 0.5 s body.
        trim_dur = max(0.5, dur_full - head - tail)
        cmd = [
            str(cfg.ffmpeg_bin), "-y",
            "-ss", f"{head:.3f}",
            "-t",  f"{trim_dur:.3f}",
            "-i",  str(src),
            "-vf", f"scale={cfg.target_width}:{cfg.target_height}:flags=lanczos,fps={cfg.target_fps}",
            "-af", "aresample=async=1",
            "-c:v", "libx264", "-crf", "20", "-preset", "fast",
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
    concat_list: Path,
    music_path: Path,
    final_out: Path,
    cfg: Config,
) -> None:
    """Single ffmpeg invocation:
      inputs: [0]PANTHEON [1]title [2]body-concat [3]stitched music
      audio: game @ body * 1.0 + music @ 0.5 (amix), PANTHEON+title keep own audio
      video: PANTHEON + title + body (hard cuts via concat filter)
      encoder: AV1 NVENC p7 uhq 10-bit cq=18
    """
    filter_complex = (
        f"[3:a]volume={cfg.music_volume}[mus];"
        f"[2:a]volume={cfg.game_audio_volume}[game];"
        f"[game][mus]amix=inputs=2:duration=first:normalize=0[body_a];"
        f"[0:v][0:a][1:v][1:a][2:v][body_a]concat=n=3:v=1:a=1[vout][aout]"
    )

    codec  = cfg.final_render_nvenc_codec
    cq     = cfg.final_render_nvenc_cq
    preset = cfg.final_render_nvenc_preset
    tune   = cfg.final_render_nvenc_tune

    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        "-i", str(pantheon_trim),
        "-i", str(title_card),
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-i", str(music_path),
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
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
    args = ap.parse_args()

    part = args.part
    cfg = Config()
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

    # --- Body duration for music budget ---
    body_dur = _sum_duration(chunks, cfg)
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
    final_out = OUTPUT_DIR / OUTPUT_NAME_TMPL.format(n=part)
    final_render(part, pantheon, title_card, concat_list,
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
