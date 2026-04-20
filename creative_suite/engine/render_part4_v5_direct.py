"""
Part 4 v5 — DIRECT render path.

Uses already-encoded chunks from output/_part4_v5_body_chunks/ plus:
  - PANTHEON intro (first 7s of IntroPart2.mp4)
  - Title card (phase1/assets/title_card_part04.mp4)
  - Music (looped to cover entire body length, volume 0.5)
  - Game audio from chunks (volume 1.0)

Sidesteps phase1.pipeline.assemble_part because the ambient environment has
lost ffprobe.exe / transitions.py during concurrent cleanup operations.

Strategy: build the entire output in one ffmpeg invocation with filter_complex:
    [0] PANTHEON video+audio (7s)
    [1] Title card video+audio (8s)
    [2] concat-demuxer of body chunks — video
    [3] music (stream_loop -1) — audio
    concat (PANTHEON v+a, Title v+a, Body v+ mixed audio(body-audio+music)) → output
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from phase1.config import Config
from phase1.title_card import render_title_card

ROOT = Path("G:/QUAKE_LEGACY")
CHUNKS_DIR = ROOT / "output" / "_part4_v5_body_chunks"
CONCAT_LIST = CHUNKS_DIR / "_concat.txt"
FINAL_OUT = ROOT / "output" / "Part4_v5_titlecard_2026-04-17.mp4"
PANTHEON_TRIM = ROOT / "output" / "_pantheon_trim_7s.mp4"


def main():
    cfg = Config()
    start = time.time()

    # 1) Ensure title card exists
    title_card = ROOT / "phase1" / "assets" / "title_card_part04.mp4"
    if not title_card.exists():
        print("Rendering title card...")
        render_title_card(4, title_card, cfg)
    else:
        print(f"  [cache] {title_card.name}")

    # 2) Ensure PANTHEON trim exists
    if not PANTHEON_TRIM.exists():
        print("Trimming PANTHEON intro (first 7s)...")
        cmd = [
            str(cfg.ffmpeg_bin), "-y",
            "-ss", "0", "-t", str(cfg.intro_clip_duration),
            "-i", str(cfg.intro_source),
            "-c:v", "libx264", "-crf", "17", "-preset", "fast",
            "-pix_fmt", "yuv420p", "-r", str(cfg.target_fps),
            "-vf", f"scale={cfg.target_width}:{cfg.target_height}:flags=lanczos",
            "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
            str(PANTHEON_TRIM),
        ]
        subprocess.run(cmd, check=True)
    else:
        print(f"  [cache] {PANTHEON_TRIM.name}")

    # 3) Sanity checks
    music_path = cfg.music_path(4)
    if music_path is None or not music_path.exists():
        print("[FATAL] Music file missing — aborting (music is a hard requirement)")
        return 1
    if not CONCAT_LIST.exists():
        print(f"[FATAL] Concat list missing: {CONCAT_LIST}")
        return 1

    # 4) Build the final render with one ffmpeg call
    #    Inputs:
    #      0: PANTHEON trim (v+a)
    #      1: title card (v+a)
    #      2: body via concat demuxer (v+a, already has game audio)
    #      3: music (audio only, looped)
    #
    #    Audio mix for the body portion: game audio (a=2) at 1.0, music at 0.5.
    #    PANTHEON and title card keep their own audio (PANTHEON has game bg,
    #    title card is silent anullsrc).
    #
    #    We build: pantheon_v + title_v + body_v → concat video
    #             pantheon_a + title_a + body_mixed_a → concat audio
    body_duration_hint = 1800.0  # >29min, safe upper bound; -shortest trims

    filter_complex = (
        # Body audio mixed with music (music trimmed to body duration via -shortest)
        f"[3:a]volume={cfg.music_volume}[mus];"
        f"[2:a]volume={cfg.game_audio_volume}[game];"
        f"[game][mus]amix=inputs=2:duration=first:dropout_transition=0[body_a];"
        # Three-way concat of v+a
        f"[0:v][0:a][1:v][1:a][2:v][body_a]concat=n=3:v=1:a=1[vout][aout]"
    )

    codec = cfg.final_render_nvenc_codec          # av1_nvenc
    cq    = cfg.final_render_nvenc_cq             # 18
    preset = cfg.final_render_nvenc_preset        # p7
    tune   = cfg.final_render_nvenc_tune          # uhq

    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        "-i", str(PANTHEON_TRIM),
        "-i", str(title_card),
        "-f", "concat", "-safe", "0", "-i", str(CONCAT_LIST),
        "-stream_loop", "-1", "-i", str(music_path),
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
    # Blackwell 10-bit
    if cfg.final_render_nvenc_highbitdepth and codec in ("av1_nvenc", "hevc_nvenc"):
        cmd += ["-highbitdepth", "1", "-pix_fmt", cfg.final_render_nvenc_pix_fmt]
    else:
        cmd += ["-pix_fmt", "yuv420p"]

    cmd += [
        "-r", str(cfg.target_fps),
        "-g", str(cfg.target_fps * 2),
        "-c:a", "aac", "-ar", "48000", "-b:a", cfg.audio_bitrate,
        "-movflags", "+faststart",
        str(FINAL_OUT),
    ]

    print(f"Rendering final with {codec} cq={cq} preset={preset} tune={tune}...")
    print(f"  Output: {FINAL_OUT.name}")
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print(f"[ERROR] NVENC final render failed:")
        print(result.stderr[-2000:])
        # Try libx264 fallback
        print("\n  Retrying with libx264 CRF 17 slow fallback...")
        fallback_cmd = cmd[:]
        # Replace NVENC codec block with libx264
        nvenc_start = fallback_cmd.index("-c:v")
        # Find where the video output starts — it's at -r
        r_idx = fallback_cmd.index("-r", nvenc_start)
        fallback_cmd[nvenc_start:r_idx] = [
            "-c:v", "libx264", "-crf", "17", "-preset", "slow",
            "-profile:v", "high", "-pix_fmt", "yuv420p", "-bf", "2",
        ]
        result = subprocess.run(fallback_cmd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        if result.returncode != 0:
            print("[FATAL] libx264 fallback also failed:")
            print(result.stderr[-2000:])
            return 1

    elapsed = time.time() - start
    size_mb = FINAL_OUT.stat().st_size / 1024 / 1024
    print(f"\n{'='*60}")
    print(f"  [DONE] {FINAL_OUT}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"  Elapsed: {elapsed/60:.1f} min")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
