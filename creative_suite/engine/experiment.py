"""
Phase 1 Experiment Generator — auto-generates 3 cut styles for Parts 4 and 5.

Usage:
    python phase1/experiment.py --part 4        # generate + preview Part 4 (all 3 styles)
    python phase1/experiment.py --part 5        # generate + preview Part 5 (all 3 styles)
    python phase1/experiment.py --part 4 5      # both parts
    python phase1/experiment.py --render-only   # skip regeneration, render existing

Styles:
    A — Cinematic:  T3 intro/outro, T2 backbone, T1 climax slow-mo
    B — Punchy:     All FP-only, no slow-mo, sorted by tier density
    C — Showcase:   T2-led with T1 peak moments + T3 filler, 3 strategic slow-mo

Tier hierarchy:
    T1 = RAREST — peak/elite frags. Few clips per Part. Save for climax.
    T2 = MAIN MEAL — most clips per Part. Backbone of every Part.
    T3 = FILLER — atmospheric, cinematic. Intro/outro priority. More numerous.

Output: output/previews/Part{N}_style{A|B|C}_preview.mp4  (30 seconds each)
"""
import argparse
import sys
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Tuple

# Force UTF-8 output on Windows (avoids charmap errors with arrow chars in comments)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from creative_suite.engine.config import Config
from creative_suite.engine.inventory import get_clip_info


# ─── Clip scanning (handles all three tiers + root .avi AND subdir multi-angle) ─

@dataclass
class FragClip:
    """One frag slot: a main FP clip plus zero or more FL alternatives."""
    fp: Path                     # first-person AVI
    fl: List[Path]               # freelook angle AVIs (FL1, FL2, FL3...)
    has_intro: bool = False      # folder name ends with 'intro'
    demo_id: int = 0             # parsed Demo(X) number for sorting
    tier: int = 1                # 1=rare/peak, 2=main meal, 3=filler/cinematic


def _parse_demo_id(name: str) -> int:
    """Extract the Demo(X) number from a filename like 'Demo (104) - 8.avi'."""
    import re
    m = re.search(r'Demo\s*\((\d+)\)', name, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def _scan_tier_dir(part_dir: Path, tier: int) -> Tuple[List[FragClip], List[FragClip]]:
    """
    Scan one tier's Part directory.
    Returns (multi_angle, singles) — both as FragClip with fl=[] for singles.
    """
    multi: List[FragClip] = []
    singles: List[FragClip] = []

    for entry in sorted(part_dir.iterdir()):
        if entry.is_file() and entry.suffix.lower() == ".avi":
            singles.append(FragClip(
                fp=entry,
                fl=[],
                has_intro=False,
                demo_id=_parse_demo_id(entry.name),
                tier=tier,
            ))
        elif entry.is_dir():
            avis = sorted(entry.glob("*.avi"))
            if not avis:
                continue

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

            multi.append(FragClip(
                fp=fp_clip,
                fl=sorted(fl_clips),
                has_intro="intro" in entry.name.lower(),
                demo_id=_parse_demo_id(entry.name),
                tier=tier,
            ))

    return multi, singles


def scan_part_frags(
    part: int,
    cfg: Config,
) -> Tuple[List[FragClip], List[FragClip]]:
    """
    Scan ALL THREE TIERS (T1+T2+T3) for a Part.

    HARD RULE P1-A: every Part combines T1+T2+T3. T1-only is wrong.
    HARD RULE P1-B: T3 multi-angle subdirs = priority intro/outro.
                    T2 multi-angle = secondary. T1 = last resort for intros.

    Tier semantics:
      T1 (tier=1): rarest, peak/elite frags — use for climax moments
      T2 (tier=2): main meal — bulk of the Part, most screen time
      T3 (tier=3): filler/cinematic — intro/outro, atmospheric, more numerous

    Returns:
      multi: all multi-angle frags (have FL alternatives), sorted by tier then demo_id
      singles: all FP-only clips, sorted by tier then demo_id
    """
    all_multi: List[FragClip] = []
    all_singles: List[FragClip] = []

    for tier in [1, 2, 3]:
        part_dir = cfg.part_dir(part, tier=tier)
        if not part_dir.exists():
            continue
        m, s = _scan_tier_dir(part_dir, tier)
        all_multi.extend(m)
        all_singles.extend(s)

    # Sort: by tier first, then demo_id within tier
    all_multi.sort(key=lambda f: (f.tier, f.demo_id))
    all_singles.sort(key=lambda f: (f.tier, f.demo_id))

    return all_multi, all_singles


# ─── Clip list line builders ──────────────────────────────────────────────────

def _fp_only(clip: FragClip) -> str:
    return clip.fp.name


def _fp_to_fl(frag: FragClip, fl_index: int = 0) -> str:
    """FP clip -> freelook cut."""
    if frag.fl and fl_index < len(frag.fl):
        return f"{frag.fp.name} > {frag.fl[fl_index].name}"
    return frag.fp.name


def _fp_to_fl_slow(frag: FragClip, fl_index: int = 0) -> str:
    """FP clip -> freelook in slow-mo (reserved for T1 peak moments)."""
    if frag.fl and fl_index < len(frag.fl):
        return f"{frag.fp.name} > {frag.fl[fl_index].name} [slow]"
    return f"{frag.fp.name} [slow]"


def _intro_entry(frag: FragClip) -> str:
    """Intro frag with hard cut — T3 FL clips get priority here."""
    if frag.fl:
        return f"{frag.fp.name} [intro] > {frag.fl[0].name}"
    return f"{frag.fp.name} [intro]"


# ─── Style generators ─────────────────────────────────────────────────────────

def generate_style_a(
    multi: List[FragClip],
    singles: List[FragClip],
    part: int,
) -> List[str]:
    """
    Style A — Cinematic
    Structure:
      - T3 FL clips (slow-mo) as atmospheric intro section
      - T2 singles + T2 multi FP->FL as main body
      - T1 frags reserved for slow-mo climax finale
      - T3 singles as quiet filler between sections

    Transitions: minimal — hard cuts mostly, xfade only at major section breaks.
    """
    lines = [
        f"# Part {part} — Style A: CINEMATIC",
        "# T3 atmospheric intro -> T2 main body -> T1 climax slow-mo",
        "# Transitions: hard cuts. xfade only at section breaks.",
        "#",
    ]

    # Split by tier
    t1_multi = [f for f in multi if f.tier == 1]
    t2_multi = [f for f in multi if f.tier == 2]
    t3_multi = [f for f in multi if f.tier == 3]
    t1_single = [f for f in singles if f.tier == 1]
    t2_single = [f for f in singles if f.tier == 2]
    t3_single = [f for f in singles if f.tier == 3]

    # ── INTRO: T3 FL clips in slow-mo (cinematic atmosphere) ──
    lines.append("# -- T3 atmospheric intro (FL slow-mo) --")
    t3_intro_pool = [f for f in t3_multi if f.fl and f.has_intro]
    t3_non_intro = [f for f in t3_multi if f.fl and not f.has_intro]

    # Use up to 3 T3 FL clips as slow intro
    intro_clips = (t3_intro_pool + t3_non_intro)[:3]
    for frag in intro_clips:
        lines.append(_fp_to_fl_slow(frag, fl_index=0))

    if not intro_clips:
        # Fallback: first 2 T3 singles as quiet opener
        for clip in t3_single[:2]:
            lines.append(_fp_only(clip))

    lines.append("#")
    lines.append("# -- T2 main body --")

    # ── MAIN BODY: T2 clips (the film's backbone) ──
    # Mix T2 singles and T2 multi (FP->FL) together
    t2_used_multi = 0
    for i, clip in enumerate(t2_single[:15]):
        lines.append(_fp_only(clip))
        if t2_used_multi < len(t2_multi) - len(t1_multi):  # save last for climax bridge
            frag = t2_multi[t2_used_multi]
            lines.append(_fp_to_fl(frag))
            t2_used_multi += 1

    # Remaining T2 multi not yet used
    for frag in t2_multi[t2_used_multi:]:
        lines.append(_fp_to_fl(frag))

    # Mid-section: T3 singles as breathing room
    lines.append("#")
    lines.append("# -- T3 filler (breather between sections) --")
    for clip in t3_single[:5]:
        lines.append(_fp_only(clip))

    # Remaining T2 singles
    for clip in t2_single[15:]:
        lines.append(_fp_only(clip))

    # ── CLIMAX: T1 frags — each one is precious, slow-mo ──
    lines.append("#")
    lines.append("# -- T1 climax (peak frags, slow-mo FL) --")
    slow_budget = min(len(t1_multi), 4)
    for i, frag in enumerate(t1_multi):
        if i < slow_budget and frag.fl:
            fl_idx = min(1, len(frag.fl) - 1)  # prefer FL2 for slow-mo
            lines.append(_fp_to_fl_slow(frag, fl_index=fl_idx))
        else:
            lines.append(_fp_to_fl(frag))

    # T1 singles with slow-mo
    for clip in t1_single:
        lines.append(f"{clip.fp.name} [slow]")

    # ── OUTRO: remaining T3 material ──
    for clip in t3_single[5:]:
        lines.append(_fp_only(clip))

    return lines


def generate_style_b(
    multi: List[FragClip],
    singles: List[FragClip],
    part: int,
) -> List[str]:
    """
    Style B — Punchy
    FP-only clips, no slow-mo. Maximum energy.
    Order: T2 density core, T1 sprinkled at peaks, T3 as rest beats.
    Hard cuts only — no fades.
    """
    lines = [
        f"# Part {part} — Style B: PUNCHY",
        "# FP-only, no slow-mo. T2 backbone, T1 peaks, T3 rest beats.",
        "#",
    ]

    # Collect all FP clips with tier info, sort by (tier, demo_id)
    all_fp: List[FragClip] = []
    for frag in multi:
        all_fp.append(frag)  # use FP only (ignore FL)
    for clip in singles:
        all_fp.append(clip)

    # Interleave: T2 forms the body, T1 slots in at 1/3 and 2/3 marks, T3 fills rest
    t1 = sorted([f for f in all_fp if f.tier == 1], key=lambda f: f.demo_id)
    t2 = sorted([f for f in all_fp if f.tier == 2], key=lambda f: f.demo_id)
    t3 = sorted([f for f in all_fp if f.tier == 3], key=lambda f: f.demo_id)

    result: List[FragClip] = []

    # Interleave: 1 T3 filler → 3 T2 → 1 T3 → 3 T2 → T1 peak → repeat
    t1_idx = t2_idx = t3_idx = 0
    pattern_count = 0

    while t2_idx < len(t2) or t1_idx < len(t1):
        # T3 opener every 4 blocks
        if pattern_count % 4 == 0 and t3_idx < len(t3):
            result.append(t3[t3_idx])
            t3_idx += 1

        # 3 T2 clips
        for _ in range(3):
            if t2_idx < len(t2):
                result.append(t2[t2_idx])
                t2_idx += 1

        # 1 T1 peak if available
        if t1_idx < len(t1):
            result.append(t1[t1_idx])
            t1_idx += 1

        pattern_count += 1

    # Remaining T3
    result.extend(t3[t3_idx:])

    for clip in result:
        lines.append(clip.fp.name)

    return lines


def generate_style_c(
    multi: List[FragClip],
    singles: List[FragClip],
    part: int,
) -> List[str]:
    """
    Style C — Showcase
    Strategic: T2-led with T1 reserved for 3 peak slow-mo moments.
    T3 used for intro and outro only.
    FL cuts used for variety, not overused.
    """
    lines = [
        f"# Part {part} — Style C: SHOWCASE",
        "# T2 backbone. T1 = 3 reserved peak moments (slow-mo). T3 = frame.",
        "#",
    ]

    t1_multi = [f for f in multi if f.tier == 1]
    t2_multi = [f for f in multi if f.tier == 2]
    t3_multi = [f for f in multi if f.tier == 3]
    t1_single = [f for f in singles if f.tier == 1]
    t2_single = [f for f in singles if f.tier == 2]
    t3_single = [f for f in singles if f.tier == 3]

    # ── FRAME: 1-2 T3 FL clips as intro ──
    lines.append("# -- T3 frame (intro) --")
    t3_intro = [f for f in t3_multi if f.fl][:2]
    for frag in t3_intro:
        lines.append(f"{frag.fp.name} [intro] > {frag.fl[0].name}")
    if not t3_intro:
        for clip in t3_single[:1]:
            lines.append(_fp_only(clip))

    lines.append("#")
    lines.append("# -- T2 main body (first half: FP, build anticipation) --")

    # ── T2 first half: FP only (no FL yet — save the reveal) ──
    t2_first = t2_multi[: len(t2_multi) // 2]
    t2_second = t2_multi[len(t2_multi) // 2:]

    for frag in t2_first:
        lines.append(_fp_only(frag))

    # Mid: T2 singles
    for clip in t2_single[:10]:
        lines.append(_fp_only(clip))

    lines.append("#")
    lines.append("# -- T2 second half (FL cuts begin) --")

    # ── T2 second half: FP->FL (angle reveals) ──
    for frag in t2_second:
        lines.append(_fp_to_fl(frag))

    # ── T1 PEAK MOMENTS: 3 slow-mo climax shots ──
    lines.append("#")
    lines.append("# -- T1 peak moments (3 slow-mo highlights -- PRECIOUS) --")
    slow_budget = min(len(t1_multi) + len(t1_single), 3)
    used = 0
    for frag in t1_multi:
        if used < slow_budget:
            fl_idx = min(len(frag.fl) - 1, 1) if frag.fl else 0
            lines.append(_fp_to_fl_slow(frag, fl_index=fl_idx))
            used += 1
        else:
            lines.append(_fp_to_fl(frag))

    for clip in t1_single:
        if used < slow_budget:
            lines.append(f"{clip.fp.name} [slow]")
            used += 1
        else:
            lines.append(_fp_only(clip))

    # ── OUTRO: remaining T2 singles + T3 frame ──
    for clip in t2_single[10:]:
        lines.append(_fp_only(clip))

    lines.append("#")
    lines.append("# -- T3 frame (outro) --")
    outro_pool = [f for f in t3_multi if f.fl and f not in t3_intro][:2]
    for frag in outro_pool:
        lines.append(_fp_to_fl(frag))
    for clip in t3_single[:3]:
        lines.append(_fp_only(clip))

    return lines


# ─── Path resolver (handles both root and subdir clips, all tiers) ────────────

def resolve_clip_path(filename: str, part: int, cfg: Config) -> Optional[Path]:
    """Find the full path for a clip filename, checking all tier roots and subdirs."""
    for tier in [1, 2, 3]:
        part_dir = cfg.part_dir(part, tier=tier)
        if not part_dir.exists():
            continue
        # Check root of this tier's part dir
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

def _emit_beat_plan(
    part: int, style: str, cfg: Config, normalized_clips: List[Path],
) -> Optional[Path]:
    """
    Rule P1-I (Golden Rule): emit a beat-alignment plan for the render.

    Loads part{NN}_music.*.beats.json, measures actual clip durations,
    and produces a JSON report mapping each clip cut point to the nearest beat.
    This is a *plan* artifact — the current render does not trim to beats yet;
    once style-lock is confirmed, the plan becomes input to a trim pass.

    Returns the plan JSON path or None if no music / no beat grid available.
    """
    import json
    from creative_suite.engine.beat_sync import load_beat_grid, plan_beat_cuts
    music_path = cfg.music_path(part)
    if not music_path:
        return None
    beats_json = music_path.with_suffix(music_path.suffix + ".beats.json")
    if not beats_json.exists():
        print(f"  [beat-sync] no beat grid at {beats_json.name} -- skipping plan")
        return None

    # Measure clip durations via ffprobe
    import subprocess
    durations: List[float] = []
    for p in normalized_clips:
        r = subprocess.run(
            [str(cfg.ffmpeg_bin).replace("ffmpeg", "ffprobe"),
             "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(p)],
            capture_output=True, text=True,
        )
        durations.append(float(r.stdout.strip() or 0.0))

    grid = load_beat_grid(beats_json)
    plan = plan_beat_cuts(grid, durations, min_clip_spacing=1.2)

    out_dir = cfg.output_dir / "beat_maps"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"part{part:02d}_style{style.lower()}_beatplan.json"
    report = {
        "part": part, "style": style,
        "music_file": music_path.name,
        "tempo_bpm": grid.tempo,
        "clip_count": len(durations),
        "original_durations": durations,
        "planned_starts": plan.clip_start_times,
        "planned_durations": plan.clip_durations,
        "on_beat_cuts": plan.on_beat_count,
        "off_beat_cuts": plan.off_beat_count,
        "planned_total_seconds": plan.total_duration,
        "raw_total_seconds": sum(durations),
    }
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"  [beat-sync] plan: {plan.on_beat_count} on-beat / "
        f"{plan.off_beat_count} off-beat cuts, "
        f"{plan.total_duration:.1f}s planned vs {sum(durations):.1f}s raw -> {out_path.name}"
    )
    return out_path


def render_experiment_preview(
    part: int,
    style: str,
    clip_lines: List[str],
    cfg: Config,
    preview_seconds: int = 30,
    beat_sync: bool = False,
) -> Path:
    """Normalize + assemble an experiment style preview, then prepend PANTHEON intro.

    If beat_sync=True, also emits a beat-alignment plan JSON alongside the render
    (artifact only — does not trim clips; Rule P1-I Golden Rule scaffolding).
    """
    from creative_suite.engine.clip_list import parse_clip_entry, ClipEntry
    from creative_suite.engine.normalize import normalize_clip, slow_path
    from creative_suite.engine.pipeline import assemble_part, GradePreset, prepend_intro
    from creative_suite.engine.inventory import get_clip_info

    # Rule P1-C: always prepend PANTHEON intro. body_output = temp, output = final.
    body_output = cfg.preview_dir / f"Part{part}_style{style}_body.mp4"
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
    all_normalized: List[Path] = []
    hard_cut_before: List[bool] = []

    norm_dir = cfg.output_dir / "normalized"
    norm_dir.mkdir(parents=True, exist_ok=True)

    for entry in entries:
        group_paths = []
        for seg_filename in entry.segments:
            src = resolve_clip_path(seg_filename, part, cfg)
            if src is None:
                print(f"  [WARN] Not found: {seg_filename} -- skipping")
                continue

            is_slow = entry.slow and seg_filename == entry.segments[-1]
            base_dst = norm_dir / (src.stem + "_cfr60.mp4")
            dst = slow_path(base_dst) if is_slow else base_dst

            if not dst.exists():
                print(f"  Normalizing: {src.name}{' [slow]' if is_slow else ''}")
                normalize_clip(src, dst, cfg, slow=is_slow)

            group_paths.append(dst)

        for i, p in enumerate(group_paths):
            all_normalized.append(p)
            hard_cut_before.append(entry.intro and i == 0)

    if not all_normalized:
        raise ValueError(f"No clips resolved for Part {part} Style {style}")

    # Load grade preset
    preset_path = Path(__file__).parent / "presets" / "grade_tribute.json"
    preset = GradePreset.from_file(preset_path) if preset_path.exists() else GradePreset()

    # Check for music
    music_path = cfg.music_path(part)
    if music_path:
        print(f"  Music: {music_path.name}")
    else:
        print(f"  No music found for Part {part} (place part{part:02d}_music.mp3 in phase1/music/)")

    print(f"  Assembling {len(all_normalized)} segments -> {body_output.name}")
    assemble_part(
        clips=all_normalized,
        output_path=body_output,
        cfg=cfg,
        music_path=music_path,
        preset=preset,
        preview_seconds=preview_seconds,
        crf_override=23,
        preset_override="veryfast",
    )

    # Rule P1-I (Golden Rule): optional beat-alignment plan
    if beat_sync:
        _emit_beat_plan(part, style, cfg, all_normalized)

    # Rule P1-C: ALWAYS prepend PANTHEON intro (7s) to every Part
    prepend_intro(body_output, output, cfg)
    body_output.unlink(missing_ok=True)

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

def run_experiments(parts: List[int], cfg: Config, render_only: bool = False, preview_seconds: int = 30, beat_sync: bool = False):
    for part in parts:
        print(f"\n{'='*60}")
        print(f"  PART {part} EXPERIMENTS")
        print(f"{'='*60}")

        multi, singles = scan_part_frags(part, cfg)

        t1_multi = [f for f in multi if f.tier == 1]
        t2_multi = [f for f in multi if f.tier == 2]
        t3_multi = [f for f in multi if f.tier == 3]
        t1_s = [f for f in singles if f.tier == 1]
        t2_s = [f for f in singles if f.tier == 2]
        t3_s = [f for f in singles if f.tier == 3]

        print(f"  T1 (peak/rare):  {len(t1_multi)} multi + {len(t1_s)} single = {len(t1_multi)+len(t1_s)}")
        print(f"  T2 (main meal):  {len(t2_multi)} multi + {len(t2_s)} single = {len(t2_multi)+len(t2_s)}")
        print(f"  T3 (filler):     {len(t3_multi)} multi + {len(t3_s)} single = {len(t3_multi)+len(t3_s)}")
        print(f"  Total:           {len(multi)+len(singles)} clips across all tiers")

        styles = {
            "A": generate_style_a(multi, singles, part),
            "B": generate_style_b(multi, singles, part),
            "C": generate_style_c(multi, singles, part),
        }

        for style, lines in styles.items():
            clip_count = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
            print(f"\n  Style {style}: {clip_count} clip lines")
            list_path = save_experiment_list(part, style, lines, cfg)
            print(f"  Saved: {list_path.name}")

            try:
                out = render_experiment_preview(part, style, lines, cfg, preview_seconds=preview_seconds, beat_sync=beat_sync)
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
    parser.add_argument("--beat-sync", action="store_true",
                        help="Emit beat-alignment plan JSON per style (Rule P1-I)")
    args = parser.parse_args()

    cfg = Config()
    run_experiments(args.part, cfg, preview_seconds=args.preview_seconds, beat_sync=args.beat_sync)


if __name__ == "__main__":
    main()
