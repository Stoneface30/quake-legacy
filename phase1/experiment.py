"""
Phase 1 Experiment Generator — auto-generates 3 cut styles for Parts 4 and 5.

Usage:
    python phase1/experiment.py --part 4        # generate + preview Part 4 (all 3 styles)
    python phase1/experiment.py --part 5        # generate + preview Part 5 (all 3 styles)
    python phase1/experiment.py --part 4 5      # both parts
    python phase1/experiment.py --render-only   # skip regeneration, render existing

Styles:
    A — Cinematic:  All multi-angle frags, FP→FL cuts, slow-mo on best moments
    B — Punchy:     Fast single-angle cuts only, no slow-mo, tight pacing
    C — Showcase:   Balanced mix, strategic angle changes, 3 slow-mo highlights

Output: output/previews/Part{N}_style{A|B|C}_preview.mp4  (30 seconds each)
"""
import argparse
import sys
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Tuple

# Force UTF-8 output on Windows (avoids charmap errors with arrow chars in comments)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from phase1.config import Config
from phase1.inventory import get_clip_info


# ─── Clip scanning (handles root .avi AND subdir multi-angle frags) ──────────

@dataclass
class FragClip:
    """One frag slot: a main FP clip plus zero or more FL alternatives."""
    fp: Path                     # first-person AVI
    fl: List[Path]               # freelook angle AVIs (FL1, FL2, FL3...)
    has_intro: bool = False      # folder name ends with 'intro'
    demo_id: int = 0             # parsed Demo(X) number for sorting


def _parse_demo_id(name: str) -> int:
    """Extract the Demo(X) number from a filename like 'Demo (104) - 8.avi'."""
    import re
    m = re.search(r'Demo\s*\((\d+)\)', name, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def scan_part_frags(part: int, cfg: Config) -> Tuple[List[FragClip], List[Path]]:
    """
    Scan a Part folder and return:
      - multi: list of FragClip (frags with FL alternatives, from subdirectories)
      - single: list of Path (root-level .avi files, FP-only)
    """
    part_dir = cfg.part_dir(part)
    multi: List[FragClip] = []
    single: List[Path] = []

    for entry in sorted(part_dir.iterdir()):
        if entry.is_file() and entry.suffix.lower() == ".avi":
            single.append(entry)
        elif entry.is_dir():
            avis = sorted(entry.glob("*.avi"))
            if not avis:
                continue
            # Find FP clip (matches folder name without FL suffix)
            folder_stem = entry.name.replace(" intro", "").strip()
            fp_clip = None
            fl_clips = []
            for avi in avis:
                stem = avi.stem
                if "FL" in stem.upper() and any(c.isdigit() for c in stem[stem.upper().rfind("FL") + 2:]):
                    fl_clips.append(avi)
                else:
                    fp_clip = avi

            if fp_clip is None and avis:
                fp_clip = avis[0]

            frag = FragClip(
                fp=fp_clip,
                fl=sorted(fl_clips),
                has_intro="intro" in entry.name.lower(),
                demo_id=_parse_demo_id(entry.name),
            )
            multi.append(frag)

    # Sort multi by demo_id
    multi.sort(key=lambda f: f.demo_id)
    return multi, single


# ─── Clip list line builders ──────────────────────────────────────────────────

def _rel(path: Path, cfg: Config) -> str:
    """Return path relative to the part directory, resolved for clip list lookup."""
    return path.name


def _fp_only(clip: Path) -> str:
    return clip.name


def _fp_to_fl(frag: FragClip, fl_index: int = 0) -> str:
    """FP clip → freelook cut."""
    if frag.fl and fl_index < len(frag.fl):
        return f"{frag.fp.name} > {frag.fl[fl_index].name}"
    return frag.fp.name


def _fp_to_fl_slow(frag: FragClip, fl_index: int = 0) -> str:
    """FP clip → freelook in slow-mo."""
    if frag.fl and fl_index < len(frag.fl):
        return f"{frag.fp.name} > {frag.fl[fl_index].name} [slow]"
    return f"{frag.fp.name} [slow]"


def _intro_entry(frag: FragClip) -> str:
    """Intro frag with hard cut."""
    if frag.fl:
        return f"{frag.fp.name} [intro] > {frag.fl[0].name}"
    return f"{frag.fp.name} [intro]"


# ─── Style generators ─────────────────────────────────────────────────────────

def generate_style_a(multi: List[FragClip], single: List[Path], part: int) -> List[str]:
    """
    Style A — Cinematic
    All multi-angle frags with FP→FL cuts. Slow-mo on 4 best FL shots.
    Intro frags used as section breaks. Single clips fill between.
    Order: single opener → multi block (with intros) → climax slow-mo finale.
    """
    lines = [
        f"# Part {part} — Style A: CINEMATIC",
        "# All multi-angle frags. FP→FL cuts. Slow-mo on highlight moments.",
        "#",
    ]

    # Opener: 5 single clips (early warmup)
    opener_singles = single[:5]
    for clip in opener_singles:
        lines.append(_fp_only(clip))

    lines.append("#")
    lines.append("# -- multi-angle section --")

    # Mark intro frags for section breaks
    intro_frags = [f for f in multi if f.has_intro]
    non_intro = [f for f in multi if not f.has_intro]

    # Interleave non-intro multi frags with remaining singles
    mid_singles = single[5:15]
    multi_idx = 0
    for i, clip in enumerate(mid_singles):
        lines.append(_fp_only(clip))
        if multi_idx < len(non_intro) - 4:  # save last 4 for finale
            frag = non_intro[multi_idx]
            lines.append(_fp_to_fl(frag))
            multi_idx += 1

    # Intro frags as section breaks (hard cuts)
    for frag in intro_frags:
        lines.append(_intro_entry(frag))

    # Remaining singles
    for clip in single[15:22]:
        lines.append(_fp_only(clip))

    # Finale: last 4 multi frags with slow-mo on FL
    lines.append("#")
    lines.append("# -- slow-mo finale --")
    finale_multi = non_intro[multi_idx:] + (non_intro[-4:] if len(non_intro) > multi_idx + 4 else [])
    slow_count = 0
    for frag in finale_multi:
        if slow_count < 4 and frag.fl:
            lines.append(_fp_to_fl_slow(frag, fl_index=min(1, len(frag.fl) - 1)))
            slow_count += 1
        else:
            lines.append(_fp_to_fl(frag))

    # Closer singles
    for clip in single[22:]:
        lines.append(_fp_only(clip))

    return lines


def generate_style_b(multi: List[FragClip], single: List[Path], part: int) -> List[str]:
    """
    Style B — Punchy
    Single-angle clips only. Fast pace. No slow-mo.
    Includes FP clips from multi-angle frags (ignores FL).
    Every clip is a hard first-person hit.
    """
    lines = [
        f"# Part {part} — Style B: PUNCHY",
        "# First-person only. No slow-mo. Maximum energy.",
        "#",
    ]

    # Collect all FP clips (single + multi FP)
    all_fp = list(single) + [f.fp for f in multi]
    all_fp.sort(key=lambda p: _parse_demo_id(p.stem))

    for clip in all_fp:
        lines.append(clip.name)

    return lines


def generate_style_c(multi: List[FragClip], single: List[Path], part: int) -> List[str]:
    """
    Style C — Showcase
    Best of both: strategic angle changes, 3 slow-mo highlights.
    Uses FL2/FL3 when available for the slow-mo moments (best angles saved for slow-mo).
    Paces build: quick start → multi-angle highlights → slow-mo climax.
    """
    lines = [
        f"# Part {part} — Style C: SHOWCASE",
        "# Strategic mix. Best angles for slow-mo. Builds to climax.",
        "#",
    ]

    # Quick opener: first 6 single clips
    for clip in single[:6]:
        lines.append(_fp_only(clip))

    lines.append("#")
    lines.append("# -- angle switches begin --")

    # First half of multi: FP only (build anticipation)
    first_half = multi[:len(multi) // 2]
    second_half = multi[len(multi) // 2:]

    for frag in first_half:
        if frag.has_intro:
            lines.append(f"{frag.fp.name} [intro]")
        else:
            lines.append(_fp_only(frag.fp))

    # Mid section: some singles
    for clip in single[6:16]:
        lines.append(_fp_only(clip))

    lines.append("#")
    lines.append("# -- freelook cuts --")

    # Second half of multi: FP→FL cuts (pay off the setups)
    slow_budget = 3
    for i, frag in enumerate(second_half):
        # Use the best FL angle for slow-mo: prefer FL1 for switch, FL2+ for slow
        if slow_budget > 0 and frag.fl:
            best_slow_idx = min(len(frag.fl) - 1, 1)  # prefer FL2 if exists
            lines.append(_fp_to_fl_slow(frag, fl_index=best_slow_idx))
            slow_budget -= 1
        elif frag.fl:
            lines.append(_fp_to_fl(frag))
        else:
            lines.append(_fp_only(frag.fp))

    # Finale singles
    for clip in single[16:]:
        lines.append(_fp_only(clip))

    return lines


# ─── Path resolver (handles both root and subdir clips) ──────────────────────

def resolve_clip_path(filename: str, part: int, cfg: Config) -> Optional[Path]:
    """Find the full path for a clip filename, checking root and all subdirectories."""
    part_dir = cfg.part_dir(part)

    # Check root first
    root_path = part_dir / filename
    if root_path.exists():
        return root_path

    # Check subdirectories
    for subdir in part_dir.iterdir():
        if subdir.is_dir():
            candidate = subdir / filename
            if candidate.exists():
                return candidate

    return None


# ─── Rendering ────────────────────────────────────────────────────────────────

def render_experiment_preview(
    part: int,
    style: str,
    clip_lines: List[str],
    cfg: Config,
    preview_seconds: int = 30,
) -> Path:
    """Normalize + assemble a 30s preview for one experiment style."""
    from phase1.clip_list import parse_clip_entry, ClipEntry
    from phase1.normalize import normalize_clip, slow_path
    from phase1.pipeline import assemble_part, GradePreset
    from phase1.inventory import get_clip_info

    output = cfg.preview_dir / f"Part{part}_style{style}_preview.mp4"
    print(f"\n[Style {style}] Rendering {output.name}...")

    # Parse entries
    entries = []
    for line in clip_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(parse_clip_entry(stripped))

    if not entries:
        raise ValueError(f"Style {style} produced no clip entries")

    # Resolve and normalize all segments
    all_normalized: List[Path] = []       # flat list for assembler
    hard_cut_before: List[bool] = []      # True = no xfade before this segment group

    norm_dir = cfg.output_dir / "normalized"
    norm_dir.mkdir(parents=True, exist_ok=True)

    for entry in entries:
        group_paths = []
        for seg_filename in entry.segments:
            src = resolve_clip_path(seg_filename, part, cfg)
            if src is None:
                print(f"  [WARN] Not found: {seg_filename} — skipping")
                continue

            is_slow = entry.slow and seg_filename == entry.segments[-1]
            base_dst = norm_dir / (src.stem + "_cfr60.mp4")
            dst = slow_path(base_dst) if is_slow else base_dst

            if not dst.exists():
                print(f"  Normalizing: {src.name}{' [slow]' if is_slow else ''}")
                normalize_clip(src, dst, cfg, slow=is_slow)

            group_paths.append(dst)

        # Record hard cut: intro flag = hard cut before first segment of this entry
        for i, p in enumerate(group_paths):
            all_normalized.append(p)
            # Hard cut before first segment of intro entries
            hard_cut_before.append(entry.intro and i == 0)

    if not all_normalized:
        raise ValueError(f"No clips resolved for Part {part} Style {style}")

    # Load grade preset
    preset_path = Path(__file__).parent / "presets" / "grade_tribute.json"
    preset = GradePreset.from_file(preset_path) if preset_path.exists() else GradePreset()

    print(f"  Assembling {len(all_normalized)} segments → {output.name}")
    assemble_part(
        clips=all_normalized,
        output_path=output,
        cfg=cfg,
        preset=preset,
        preview_seconds=preview_seconds,
        crf_override=23,
        preset_override="veryfast",
    )

    size_mb = output.stat().st_size / 1024 / 1024
    print(f"  [DONE] {output.name} ({size_mb:.1f}MB)")
    return output


# ─── Save clip list ────────────────────────────────────────────────────────────

def save_experiment_list(part: int, style: str, lines: List[str], cfg: Config) -> Path:
    """Save an experiment clip list to disk for reference."""
    path = cfg.clip_lists_dir / f"part{part:02d}_style{style.lower()}.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ─── Main ─────────────────────────────────────────────────────────────────────

def run_experiments(parts: List[int], cfg: Config, render_only: bool = False):
    for part in parts:
        print(f"\n{'='*60}")
        print(f"  PART {part} EXPERIMENTS")
        print(f"{'='*60}")

        multi, single = scan_part_frags(part, cfg)
        print(f"  Multi-angle frags: {len(multi)}  (subdirs with FL clips)")
        print(f"  Single clips:      {len(single)}  (root .avi files)")
        print(f"  Total frags:       {len(multi) + len(single)}")

        styles = {
            "A": generate_style_a(multi, single, part),
            "B": generate_style_b(multi, single, part),
            "C": generate_style_c(multi, single, part),
        }

        for style, lines in styles.items():
            clip_count = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
            print(f"\n  Style {style}: {clip_count} clip lines")
            list_path = save_experiment_list(part, style, lines, cfg)
            print(f"  Saved: {list_path.name}")

            try:
                out = render_experiment_preview(part, style, lines, cfg)
                print(f"  Preview: {out}")
            except Exception as e:
                print(f"  [ERROR] Style {style} failed: {e}")

        print(f"\nPart {part} experiments complete.")
        print(f"Previews in: {cfg.preview_dir}")


def main():
    parser = argparse.ArgumentParser(description="QUAKE LEGACY Experiment Generator")
    parser.add_argument("--part", type=int, nargs="+", default=[4, 5],
                        help="Part numbers to experiment with (default: 4 5)")
    parser.add_argument("--render-only", action="store_true",
                        help="Skip list generation, just render existing")
    parser.add_argument("--preview-seconds", type=int, default=30,
                        help="Preview length in seconds (default: 30)")
    args = parser.parse_args()

    cfg = Config()
    run_experiments(args.part, cfg)


if __name__ == "__main__":
    main()
