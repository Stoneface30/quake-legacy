"""
Part 4 v5 — Final render with title-card intro sequence (Rule P1-N).

2026-04-17 post-review render:
    - Clip list: part04_styleb.txt
    - Music: part04_music.mp3 at volume 0.5 (Rule P1-G revised)
    - Game audio: 1.0 foreground (Rule P1-G revised)
    - HARD CUTS only (Rule P1-H, xfade_duration=0.0)
    - Clip trim: 1s head / 2s tail (Rule P1-L)
    - Encoder: NVENC av1_nvenc cq=18 p7 uhq 10-bit (Rule P1-J)
    - Intro: PANTHEON 7s + Title card 8s + content (Rule P1-N + P1-C)

Usage:
    python phase1/render_part4_v5.py
    python phase1/render_part4_v5.py --fallback-x264
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from creative_suite.engine.config import Config
from creative_suite.engine.clip_list import parse_clip_entry
from creative_suite.engine.normalize import normalize_clip
from creative_suite.engine.pipeline import assemble_part, GradePreset, prepend_intro_sequence
from creative_suite.engine.experiment import resolve_clip_path

PART = 4
CLIP_LIST_NAME = "part04_styleb.txt"
OUTPUT_NAME = "Part4_v5_titlecard_2026-04-17.mp4"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fallback-x264", action="store_true")
    parser.add_argument("--limit-clips", type=int, default=None)
    args = parser.parse_args()

    start_time = time.time()
    cfg = Config()

    clip_list_path = cfg.clip_lists_dir / CLIP_LIST_NAME
    if not clip_list_path.exists():
        print(f"[FATAL] Clip list not found: {clip_list_path}")
        sys.exit(1)

    print(f"Reading clip list: {clip_list_path}")
    lines = clip_list_path.read_text(encoding="utf-8").splitlines()

    entries = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        entries.append(parse_clip_entry(s))

    if args.limit_clips:
        entries = entries[: args.limit_clips]

    print(f"  {len(entries)} clip entries")

    norm_dir = cfg.output_dir / "normalized"
    norm_dir.mkdir(parents=True, exist_ok=True)

    normalized: List[Path] = []
    for entry in entries:
        for seg_idx, seg_filename in enumerate(entry.segments):
            src = resolve_clip_path(seg_filename, PART, cfg)
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

    if not normalized:
        print("[FATAL] No clips resolved")
        sys.exit(1)

    print(f"  {len(normalized)} normalized segments")

    music_path = cfg.music_path(PART)
    if music_path is None:
        print("[WARN] No music found — FAILURE CONDITION per task")
    else:
        print(f"  Music: {music_path.name}")

    preset_path = Path(__file__).parent / "presets" / "grade_tribute.json"
    preset = GradePreset.from_file(preset_path) if preset_path.exists() else GradePreset()

    if args.fallback_x264:
        codec = "libx264"
        crf = 17
        enc_preset = "slow"
    else:
        codec = cfg.final_render_nvenc_codec
        crf = cfg.final_render_nvenc_cq
        enc_preset = cfg.final_render_nvenc_preset
    print(f"  Encoder: {codec} cq/crf={crf} preset={enc_preset}")

    body_out = cfg.output_dir / "_part4_v5_body.mp4"
    print(f"\nAssembling body -> {body_out.name}")
    try:
        assemble_part(
            clips=normalized,
            output_path=body_out,
            cfg=cfg,
            music_path=music_path,
            preset=preset,
            preview_seconds=None,
            crf_override=crf,
            preset_override=enc_preset,
            codec_override=codec,
            clip_list_path=clip_list_path,
        )
    except Exception as e:
        if not args.fallback_x264:
            print(f"[ERROR] NVENC failed: {e}")
            print("  Retrying with libx264 fallback...")
            assemble_part(
                clips=normalized,
                output_path=body_out,
                cfg=cfg,
                music_path=music_path,
                preset=preset,
                preview_seconds=None,
                crf_override=17,
                preset_override="slow",
                codec_override="libx264",
                clip_list_path=clip_list_path,
            )
        else:
            raise

    final_out = cfg.output_dir / OUTPUT_NAME
    print(f"\nPrepending intro sequence -> {final_out.name}")
    prepend_intro_sequence(PART, body_out, final_out, cfg)

    body_out.unlink(missing_ok=True)
    (body_out.parent / (body_out.stem + ".filter.txt")).unlink(missing_ok=True)

    elapsed = time.time() - start_time
    size_mb = final_out.stat().st_size / 1024 / 1024
    print(f"\n{'='*60}")
    print(f"  [DONE] {final_out}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"  Elapsed: {elapsed/60:.1f} min")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
