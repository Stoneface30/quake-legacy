"""
Main Phase 1 orchestrator: clips -> finished MP4.
Usage:
  python phase1/assembler.py --part 4 --preview     # preview only
  python phase1/assembler.py --part 4               # full render
  python phase1/assembler.py --all --preview        # preview all parts
  python phase1/assembler.py --all                  # render all parts (LONG!)
"""
import argparse
from pathlib import Path
from typing import Optional
from phase1.config import Config
from phase1.clip_list import get_clip_paths
from phase1.normalize import normalize_part
from phase1.pipeline import assemble_part, GradePreset
from phase1.preview import render_preview


def render_part(
    part: int,
    cfg: Config,
    music_path: Optional[Path] = None,
    force: bool = False,
) -> Path:
    """Full render of a single Part. Returns output MP4 path."""
    output = cfg.output_path(part)

    if output.exists() and not force:
        print(f"Part {part} already rendered: {output}")
        print("  Use --force to re-render.")
        return output

    print(f"\n{'='*60}")
    print(f"  RENDERING PART {part}")
    print(f"{'='*60}")

    # 1. Load clip list
    clips = get_clip_paths(part, cfg)
    print(f"  Clips: {len(clips)}")

    # 2. Normalize all clips
    normalized = normalize_part(part, clips, cfg)

    # 3. Load grade preset
    preset_path = Path(__file__).parent / "presets" / "grade_tribute.json"
    preset = GradePreset.from_file(preset_path) if preset_path.exists() else GradePreset()

    # 4. Auto-detect music if not provided
    if music_path is None:
        music_path = cfg.music_path(part)
        if music_path:
            print(f"  Music: {music_path.name}")
        else:
            print(f"  Music: none (game audio only)")

    # 5. Assemble
    assemble_part(
        clips=normalized,
        output_path=output,
        cfg=cfg,
        music_path=music_path,
        preset=preset,
    )

    # 6. Prepend intro if available
    if cfg.intro_source.exists():
        from phase1.intro import prepend_intro
        final = prepend_intro(output, cfg)
        print(f"  Intro prepended: {final}")
    else:
        print(f"  [WARN] No intro source found at {cfg.intro_source}")

    size_mb = output.stat().st_size / 1024 / 1024
    print(f"\nPart {part} complete: {output} ({size_mb:.0f}MB)")
    return output


def main():
    parser = argparse.ArgumentParser(description="QUAKE LEGACY Phase 1 Assembler")
    parser.add_argument("--part", type=int, help="Part number (4-12)")
    parser.add_argument("--all", action="store_true", help="Render all parts 4-12")
    parser.add_argument("--preview", action="store_true", help="Render 30s preview only")
    parser.add_argument("--music", type=str, help="Path to music file (MP3/OGG/WAV)")
    parser.add_argument("--force", action="store_true", help="Re-render even if output exists")
    args = parser.parse_args()

    cfg = Config()
    music_path = Path(args.music) if args.music else None

    if args.preview:
        parts = cfg.parts if args.all else ([args.part] if args.part else [4])
        for part in parts:
            render_preview(part, cfg)
    elif args.all:
        print("Rendering all Parts 4-12. This will take a long time.")
        print("Ctrl+C to abort at any time.\n")
        confirm = input("Proceed? (yes/no): ")
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            return
        for part in cfg.parts:
            render_part(part, cfg, music_path=music_path, force=args.force)
    elif args.part:
        render_part(args.part, cfg, music_path=music_path, force=args.force)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
