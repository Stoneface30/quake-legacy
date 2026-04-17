"""
Part 4 — 4 Version Generator
Generates 4 distinct 60-second previews at high quality (CRF 18, medium preset).

IMPORTANT: FL clips from the original recordings are already slow-motion.
The game was recorded at reduced timescale. Do NOT add [slow] to FL clips.
[slow] flag is only for post-processing slowdown of FP clips if wanted.

T1/T2/T3 MIX RULE (hard rule, applies to all versions):
  Every version uses ALL THREE tiers together. Never T1-only or T2-only.
  T1 = rare peak frags → climax, 1 per section maximum
  T2 = main meal       → 60-70% of screen time in every version
  T3 = filler/frame    → intro, outro, section breathers

4 Versions:
  V1 — Cinematic   : T3 FL opener → T2 FP+FL main → T1 FL finale
  V2 — Punchy      : FP-only from all tiers, punchy ordering, no FL
  V3 — Zoom Power  : Same as V1 but 5 selected FP kills get 1.15x zoom
  V4 — Hybrid Flow : Punchy FP start → opens into FL cuts → T1 FL climax

Usage:
    python phase1/render_part4.py
    python phase1/render_part4.py --preview-seconds 60
    python phase1/render_part4.py --version 1 2   # only render specific versions
"""
import sys
import argparse
from pathlib import Path
from typing import List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from phase1.config import Config
from phase1.clip_list import parse_clip_entry, ClipEntry
from phase1.normalize import normalize_clip, slow_path, zoom_path, speedup_path
from phase1.pipeline import assemble_part, GradePreset, prepend_intro_sequence
from phase1.experiment import scan_part_frags, FragClip, resolve_clip_path
from phase1.inventory import get_clip_info

PART = 4


# ─── Multi-angle stitch helper ────────────────────────────────────────────────

def all_angles(frag: "FragClip", slow_fl: bool = False) -> str:
    """
    Build a clip entry using ALL available angles for a frag folder.

    For intro clips like Demo (101) - 4 intro/:
      Demo (101) - 4.avi > Demo (101FL1).avi > Demo (101FL2).avi > Demo (101FL3).avi > ...

    FL clips are already slow from recording — no [slow] flag unless slow_fl=True
    (which is for FP clips only when we want software slow-mo on top).

    User rule: the same moment must be consistent — show ALL angles available.
    6 files = 1 FP + 5 FL → stitch them ALL in order for maximum coverage.
    """
    parts = [frag.fp.name]
    for fl in frag.fl:  # fl is already sorted (FL1, FL2, FL3...)
        parts.append(fl.name)
    entry = " > ".join(parts)
    if slow_fl:
        entry += " [slow]"
    return entry


# ─── Clip list builders (one per version) ────────────────────────────────────

def build_v1_cinematic(
    t1_multi, t2_multi, t3_multi,
    t1_single, t2_single, t3_single,
) -> List[str]:
    """
    V1 — Cinematic (faithful to your Tribute style)

    Structure:
      INTRO  : 2 T3 FL clips (already slow from recording — no [slow] flag)
      BODY   : T2 FP → FL pairs (main meal, 60%+ of version)
      BRIDGE : 1 T1 FP → FL (first peak reveal)
      MID    : More T2 FP → FL + T2 FP-only singles
      CLIMAX : 2 T1 FP → FL pairs (peak)
      OUTRO  : 1 T3 FL clip
    """
    lines = [
        "# Part 4 — V1: CINEMATIC",
        "# T3 FL atmospheric intro -> T2 main body (FP+FL) -> T1 FL climax",
        "# NOTE: FL clips are already slow from recording. No [slow] flag added.",
        "#",
    ]

    # INTRO: T3 FL clips — use ALL angles for intro clips (Rule: same clip, all angles)
    lines.append("# -- INTRO: T3 atmospheric (all available FL angles — FL already slow from recording) --")
    # Priority: intro-tagged folders first (contain dedicated FL angles for opening)
    t3_intro_frags = [f for f in t3_multi if f.has_intro and f.fl]
    t3_fl_frags = [f for f in t3_multi if not f.has_intro and f.fl]
    t3_fl = (t3_intro_frags + t3_fl_frags)[:2]
    for frag in t3_fl:
        # Use all_angles() — stitches FP → FL1 → FL2 → FL3 → ... for full coverage
        lines.append(all_angles(frag))
    if len(t3_fl) < 2:
        # Fallback to T2 intro frags if T3 is short
        t2_intro_frags = [f for f in t2_multi if f.has_intro and f.fl]
        for frag in t2_intro_frags[:2 - len(t3_fl)]:
            lines.append(all_angles(frag))
    if len(t3_fl) < 1 and not [f for f in t2_multi if f.has_intro]:
        for clip in t3_single[:2]:
            lines.append(clip.fp.name)

    # BODY: T2 pairs (FP + FL) — this is the film
    lines.append("#")
    lines.append("# -- BODY: T2 main meal (FP -> FL) --")
    t2_with_fl = [f for f in t2_multi if f.fl]
    t2_fp_only = [f for f in t2_multi if not f.fl]

    body_count = 0
    single_idx = 0
    for i, frag in enumerate(t2_with_fl[:8]):
        lines.append(f"{frag.fp.name} > {frag.fl[0].name}")
        body_count += 1
        # Insert T2 single every 3 FL clips (breathing room)
        if i % 3 == 2 and single_idx < len(t2_single):
            lines.append(t2_single[single_idx].fp.name)
            single_idx += 1

    # Fill remaining T2 singles
    for clip in t2_single[single_idx:single_idx + 5]:
        lines.append(clip.fp.name)
    single_idx += 5

    # BRIDGE: first T1 reveal (precious — one at a time)
    if t1_multi:
        frag = t1_multi[0]
        lines.append("#")
        lines.append("# -- BRIDGE: T1 first reveal --")
        if frag.fl:
            lines.append(f"{frag.fp.name} > {frag.fl[0].name}")
        else:
            lines.append(frag.fp.name)

    # MID: more T2 + T2 FP-only
    lines.append("#")
    lines.append("# -- MID: T2 continued --")
    for frag in t2_with_fl[8:14]:
        lines.append(f"{frag.fp.name} > {frag.fl[0].name}")
    for clip in t2_single[single_idx:single_idx + 5]:
        lines.append(clip.fp.name)
    for frag in t2_fp_only[:3]:
        lines.append(frag.fp.name)

    # CLIMAX: remaining T1 frags
    lines.append("#")
    lines.append("# -- CLIMAX: T1 peak frags (FL already slow) --")
    for frag in t1_multi[1:3]:
        if frag.fl:
            fl_idx = min(1, len(frag.fl) - 1)
            lines.append(f"{frag.fp.name} > {frag.fl[fl_idx].name}")
        else:
            lines.append(frag.fp.name)
    for clip in t1_single[:3]:
        lines.append(clip.fp.name)

    # OUTRO: T3 closer
    lines.append("#")
    lines.append("# -- OUTRO: T3 frame --")
    t3_remaining = [f for f in t3_multi if f.fl and f not in t3_fl][:1]
    for frag in t3_remaining:
        lines.append(f"{frag.fp.name} > {frag.fl[0].name}")
    if not t3_remaining and len(t3_single) > 2:
        lines.append(t3_single[2].fp.name)

    return lines


def build_v2_punchy(
    t1_multi, t2_multi, t3_multi,
    t1_single, t2_single, t3_single,
) -> List[str]:
    """
    V2 — Punchy (FP-only, all tiers mixed)

    Structure:
      All FP clips only — no FL angle cuts.
      T3 FP as quiet opener → T2 FP dense core → T1 FP peak → T2 FP → T1 FP finale
      Hard pace, no breathing room. Every clip is a hit.
      T2 provides the bulk (main meal), T1 punctuates at intervals.
    """
    lines = [
        "# Part 4 — V2: PUNCHY",
        "# FP-only from all tiers. T2 backbone. T1 at peaks. T3 as breathers.",
        "#",
    ]

    t1_all = sorted(list(t1_multi) + list(t1_single), key=lambda f: f.demo_id)
    t2_all = sorted(list(t2_multi) + list(t2_single), key=lambda f: f.demo_id)
    t3_all = sorted(list(t3_multi) + list(t3_single), key=lambda f: f.demo_id)

    # T3 FP opener (atmospheric but FP)
    lines.append("# -- T3 opener (FP only) --")
    for clip in t3_all[:2]:
        lines.append(clip.fp.name)

    # Main body: interleave T2 (backbone) + T1 (peaks) + T3 (breathers)
    # Pattern: 4x T2 → 1x T1 → 4x T2 → 1x T3 → 4x T2 → 1x T1
    lines.append("#")
    lines.append("# -- Main body: T2 backbone + T1 peaks + T3 breathers --")
    t1_idx = 0
    t2_idx = 0
    t3_idx = 2  # skip the 2 openers

    for block in range(5):
        # 4 T2 clips
        for _ in range(4):
            if t2_idx < len(t2_all):
                lines.append(t2_all[t2_idx].fp.name)
                t2_idx += 1

        if block % 2 == 1 and t3_idx < len(t3_all):
            # T3 breather every 2 blocks
            lines.append(t3_all[t3_idx].fp.name)
            t3_idx += 1
        elif t1_idx < len(t1_all):
            # T1 peak
            lines.append(t1_all[t1_idx].fp.name)
            t1_idx += 1

    # Flush remaining T2
    lines.append("#")
    lines.append("# -- T2 remainder --")
    while t2_idx < len(t2_all):
        lines.append(t2_all[t2_idx].fp.name)
        t2_idx += 1

    # T1 finale
    lines.append("#")
    lines.append("# -- T1 FP finale --")
    while t1_idx < len(t1_all):
        lines.append(t1_all[t1_idx].fp.name)
        t1_idx += 1

    return lines


def build_v3_zoom(
    t1_multi, t2_multi, t3_multi,
    t1_single, t2_single, t3_single,
) -> List[str]:
    """
    V3 — Zoom Power (Cinematic base + zoom on 5 FP kills)

    Same structure as V1 but:
      - 3 T1 FP clips get [zoom] → 1.15x center crop zoom
      - 2 T2 FP clips get [zoom] → close-range rail/rocket impact emphasis
      - FL clips never get zoom (they're already cinematic)
      - T3 frame intro/outro same as V1
    """
    lines = [
        "# Part 4 — V3: ZOOM POWER",
        "# Same as V1 but 5 FP kills get 1.15x center zoom [zoom]",
        "# Zoom only on FP close-range kills. FL clips untouched.",
        "#",
    ]

    t2_with_fl = [f for f in t2_multi if f.fl]
    t2_fp_only = [f for f in t2_multi if not f.fl]

    # INTRO: T3 FL atmospheric (same as V1)
    lines.append("# -- INTRO: T3 atmospheric --")
    t3_fl = [f for f in t3_multi if f.fl][:2]
    for frag in t3_fl:
        lines.append(f"{frag.fp.name} > {frag.fl[0].name}")
    if len(t3_fl) < 2:
        for clip in t3_single[:2 - len(t3_fl)]:
            lines.append(clip.fp.name)

    # BODY: T2 FP → FL (main meal), zoom on 2 selected T2 FP clips
    lines.append("#")
    lines.append("# -- BODY: T2 main (2 FP kills with zoom, rest standard) --")
    zoom_budget_t2 = 2
    single_idx = 0
    for i, frag in enumerate(t2_with_fl[:8]):
        if zoom_budget_t2 > 0 and i in [2, 5]:  # position 3rd and 6th for surprise
            lines.append(f"{frag.fp.name} [zoom] > {frag.fl[0].name}")
            zoom_budget_t2 -= 1
        else:
            lines.append(f"{frag.fp.name} > {frag.fl[0].name}")
        if i % 3 == 2 and single_idx < len(t2_single):
            lines.append(t2_single[single_idx].fp.name)
            single_idx += 1

    for clip in t2_single[single_idx:single_idx + 4]:
        lines.append(clip.fp.name)

    # BRIDGE: T1 first peak with zoom
    if t1_multi:
        frag = t1_multi[0]
        lines.append("#")
        lines.append("# -- BRIDGE: T1 peak with zoom --")
        if frag.fl:
            lines.append(f"{frag.fp.name} [zoom] > {frag.fl[0].name}")
        else:
            lines.append(f"{frag.fp.name} [zoom]")

    # MID: more T2
    lines.append("#")
    lines.append("# -- MID: T2 continued --")
    for frag in t2_with_fl[8:13]:
        lines.append(f"{frag.fp.name} > {frag.fl[0].name}")
    for frag in t2_fp_only[:3]:
        lines.append(frag.fp.name)

    # CLIMAX: T1 frags — zoom on FP, FL plays naturally (already slow)
    lines.append("#")
    lines.append("# -- CLIMAX: T1 peak (FP zoom -> FL natural) --")
    for frag in t1_multi[1:4]:
        if frag.fl:
            fl_idx = min(1, len(frag.fl) - 1)
            lines.append(f"{frag.fp.name} [zoom] > {frag.fl[fl_idx].name}")
        else:
            lines.append(f"{frag.fp.name} [zoom]")
    for clip in t1_single[:2]:
        lines.append(f"{clip.fp.name} [zoom]")

    # OUTRO: T3
    lines.append("#")
    lines.append("# -- OUTRO: T3 frame --")
    for frag in [f for f in t3_multi if f.fl and f not in t3_fl][:1]:
        lines.append(f"{frag.fp.name} > {frag.fl[0].name}")
    for clip in t3_single[:1]:
        lines.append(clip.fp.name)

    return lines


def build_v4_hybrid(
    t1_multi, t2_multi, t3_multi,
    t1_single, t2_single, t3_single,
) -> List[str]:
    """
    V4 — Hybrid Flow (evolves from FP-only → opens into FL angle cuts)

    Structure:
      ACT 1 (0:00-0:20): T3 FL opener (cinematic frame) + T2 FP-only (punchy)
      ACT 2 (0:20-0:40): T2 FP → FL (angle cuts begin, energy escalates)
                          1x T1 peak with FL
      ACT 3 (0:40-1:00): Full T1 FL climax + T3 FL outro

    The transition from FP-only to FL cuts creates a natural escalation arc.
    T1 clips always appear at the ACT 2→3 boundary and in ACT 3.
    All tiers present: T3 frames the film, T2 drives it, T1 punctuates the peak.
    """
    lines = [
        "# Part 4 — V4: HYBRID FLOW",
        "# ACT1: T3 frame + T2 FP-only (punchy) -> ACT2: T2 FP+FL -> ACT3: T1 climax",
        "# Evolves from punchy to cinematic. All tiers active throughout.",
        "#",
    ]

    t2_with_fl = [f for f in t2_multi if f.fl]
    t2_fp_only = [f for f in t2_multi if not f.fl]
    t3_fl = [f for f in t3_multi if f.fl]

    # ACT 1: T3 FL frame + T2 FP-only block (no FL reveals yet)
    lines.append("# -- ACT 1: T3 frame + T2 FP punchy (no FL yet) --")
    for frag in t3_fl[:1]:  # single T3 FL opener (already slow)
        lines.append(f"{frag.fp.name} > {frag.fl[0].name}")

    # T2 FP-only — mixed from singles + multi FP (no FL cuts yet)
    t2_fp_pool = [f.fp for f in t2_with_fl[:6]] + [f.fp for f in t2_fp_only[:4]]
    for path in t2_fp_pool[:8]:
        lines.append(path.name)

    # T3 breather (single)
    if t3_single:
        lines.append(t3_single[0].fp.name)

    # ACT 2: T2 FP → FL (angle cuts begin)
    lines.append("#")
    lines.append("# -- ACT 2: T2 FP -> FL (angle cuts open up) --")
    for frag in t2_with_fl[6:14]:
        lines.append(f"{frag.fp.name} > {frag.fl[0].name}")

    # Mid T2 singles
    for clip in t2_single[:5]:
        lines.append(clip.fp.name)

    # T1 bridge (first peak, FP → best FL)
    if t1_multi:
        lines.append("#")
        lines.append("# -- ACT 2→3 BRIDGE: first T1 peak --")
        frag = t1_multi[0]
        if frag.fl:
            fl_idx = min(1, len(frag.fl) - 1)
            lines.append(f"{frag.fp.name} > {frag.fl[fl_idx].name}")
        else:
            lines.append(frag.fp.name)

    # More T2 after bridge (don't exhaust T1 too early)
    lines.append("#")
    lines.append("# -- ACT 2 continued: T2 --")
    for frag in t2_with_fl[14:]:
        lines.append(f"{frag.fp.name} > {frag.fl[0].name}")
    for clip in t2_single[5:10]:
        lines.append(clip.fp.name)

    # ACT 3: T1 climax (remaining T1 frags — FL already slow)
    lines.append("#")
    lines.append("# -- ACT 3: T1 climax (FL already slow from recording) --")
    for frag in t1_multi[1:]:
        if frag.fl:
            fl_idx = min(len(frag.fl) - 1, 1)
            lines.append(f"{frag.fp.name} > {frag.fl[fl_idx].name}")
        else:
            lines.append(frag.fp.name)
    for clip in t1_single:
        lines.append(clip.fp.name)

    # OUTRO: T3 frame closer
    lines.append("#")
    lines.append("# -- OUTRO: T3 frame closer --")
    for frag in t3_fl[1:2]:
        lines.append(f"{frag.fp.name} > {frag.fl[0].name}")
    for clip in t3_single[1:3]:
        lines.append(clip.fp.name)

    return lines


# ─── Renderer ─────────────────────────────────────────────────────────────────

def render_version(
    version: int,
    lines: List[str],
    cfg: Config,
    preset: GradePreset,
    preview_seconds: int = 60,
    crf: int = 18,
    encode_preset: str = "medium",
) -> Path:
    """Normalize and assemble one version preview, then prepend PANTHEON intro."""
    # Rule P1-C: PANTHEON intro ALWAYS prepended. We assemble body first, then prepend.
    body_output = cfg.preview_dir / f"Part4_v{version}_body.mp4"
    output = cfg.preview_dir / f"Part4_v{version}_preview.mp4"
    print(f"\n{'='*60}")
    print(f"  Part 4 — Version {version}")
    print(f"  Output: {output.name}")
    print(f"  Quality: CRF {crf}, preset {encode_preset}, {preview_seconds}s")
    print(f"{'='*60}")

    norm_dir = cfg.output_dir / "normalized"
    norm_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(parse_clip_entry(stripped))

    if not entries:
        raise ValueError(f"Version {version} produced no entries")

    all_normalized: List[Path] = []

    for entry in entries:
        for seg_idx, seg_filename in enumerate(entry.segments):
            src = resolve_clip_path(seg_filename, PART, cfg)
            if src is None:
                print(f"  [WARN] Not found: {seg_filename} -- skipping")
                continue

            # Determine effect flags
            is_slow    = entry.slow    and seg_idx == len(entry.segments) - 1
            is_zoom    = entry.zoom    and seg_idx == 0   # zoom only on FP (first segment)
            is_speedup = entry.speedup and seg_idx == 0

            # Build destination path based on active effects
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
                effect_label = ""
                if is_slow:    effect_label = " [slow]"
                if is_zoom:    effect_label = " [zoom]"
                if is_speedup: effect_label = " [fast]"
                print(f"  Normalizing: {src.name}{effect_label}")
                normalize_clip(
                    src, dst, cfg,
                    slow=is_slow, zoom=is_zoom, speedup=is_speedup,
                )
            else:
                print(f"  Cached: {dst.name}")

            all_normalized.append(dst)

    if not all_normalized:
        raise ValueError(f"No clips resolved for version {version}")

    # Check for music
    music_path = cfg.music_path(PART)
    if music_path:
        print(f"  Music: {music_path.name}")
    else:
        print(f"  [WARN] No music found. Place part04_music.mp3 in phase1/music/")
        print(f"         Suggested: 'Bucky Don Gun' by SHFTR (see available_tracks.txt)")

    print(f"\n  Assembling {len(all_normalized)} segments...")
    assemble_part(
        clips=all_normalized,
        output_path=body_output,
        cfg=cfg,
        music_path=music_path,
        preset=preset,
        preview_seconds=preview_seconds,
        crf_override=crf,
        preset_override=encode_preset,
    )

    # Rule P1-C + P1-N: PANTHEON logo (7s) + title card (8s) + content
    print(f"\n  Prepending PANTHEON intro + title card...")
    prepend_intro_sequence(body_output, output, part, cfg)

    # Clean up body temp file
    body_output.unlink(missing_ok=True)

    size_mb = output.stat().st_size / 1024 / 1024
    print(f"\n  [DONE] {output.name} ({size_mb:.1f}MB)")
    return output


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Part 4 — Generate 4 versions")
    parser.add_argument("--version", type=int, nargs="+", default=[1, 2, 3, 4],
                        help="Versions to render (default: 1 2 3 4)")
    parser.add_argument("--preview-seconds", type=int, default=60,
                        help="Preview length in seconds (default: 60)")
    args = parser.parse_args()

    cfg = Config()

    print(f"\nScanning Part {PART} — all tiers (T1+T2+T3)...")
    multi, singles = scan_part_frags(PART, cfg)

    t1_multi  = [f for f in multi   if f.tier == 1]
    t2_multi  = [f for f in multi   if f.tier == 2]
    t3_multi  = [f for f in multi   if f.tier == 3]
    t1_single = [f for f in singles if f.tier == 1]
    t2_single = [f for f in singles if f.tier == 2]
    t3_single = [f for f in singles if f.tier == 3]

    print(f"  T1 (peak/rare):  {len(t1_multi)} multi + {len(t1_single)} single")
    print(f"  T2 (main meal):  {len(t2_multi)} multi + {len(t2_single)} single")
    print(f"  T3 (filler):     {len(t3_multi)} multi + {len(t3_single)} single")

    # Load grade preset
    preset_path = Path(__file__).parent / "presets" / "grade_tribute.json"
    preset = GradePreset.from_file(preset_path) if preset_path.exists() else GradePreset()

    # Version definitions
    version_builders = {
        1: ("Cinematic",   build_v1_cinematic,  18, "medium"),
        2: ("Punchy",      build_v2_punchy,      18, "medium"),
        3: ("Zoom Power",  build_v3_zoom,        17, "medium"),  # CRF 17: zoom needs more detail
        4: ("Hybrid Flow", build_v4_hybrid,      18, "medium"),
    }

    rendered = []
    for v in args.version:
        if v not in version_builders:
            print(f"  [SKIP] Unknown version {v}")
            continue

        name, builder, crf, enc_preset = version_builders[v]
        lines = builder(t1_multi, t2_multi, t3_multi, t1_single, t2_single, t3_single)

        # Save clip list for reference
        list_path = cfg.clip_lists_dir / f"part04_v{v}_{name.lower().replace(' ', '_')}.txt"
        list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nVersion {v} ({name}): {sum(1 for l in lines if l.strip() and not l.strip().startswith('#'))} clips")
        print(f"  List: {list_path.name}")

        try:
            out = render_version(
                version=v,
                lines=lines,
                cfg=cfg,
                preset=preset,
                preview_seconds=args.preview_seconds,
                crf=crf,
                encode_preset=enc_preset,
            )
            rendered.append((v, name, out))
        except Exception as e:
            print(f"  [ERROR] Version {v} failed: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"  DONE — {len(rendered)}/{len(args.version)} versions rendered")
    print(f"{'='*60}")
    for v, name, path in rendered:
        size = path.stat().st_size / 1024 / 1024
        print(f"  V{v} {name:15} -> {path.name} ({size:.1f}MB)")
    print(f"\n  Previews in: {cfg.preview_dir}")
    print(f"\n  Clip lists in: {cfg.clip_lists_dir}")
    print(f"  Review each list to see exact clip order and make manual adjustments.")


if __name__ == "__main__":
    main()
