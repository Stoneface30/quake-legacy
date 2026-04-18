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
    plan_beat_cuts, write_beats_json,
)
from phase1.silence_detect import analyze_silence
from phase1 import music_structure as _music_structure
from phase1 import audio_onsets as _audio_onsets
from phase1 import audio_levels as _audio_levels
from phase1 import sidechain as _sidechain
from phase1.effects import event_localized as _event_localized

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


# ---------------------------------------------------------------------------
# Rule B1: Per-clip override loader
# ---------------------------------------------------------------------------


def load_clip_overrides(part: int, cfg: Config) -> dict[str, dict[str, object]]:
    """Parse phase1/clip_lists/partNN_overrides.txt.

    Grammar per line:
        <filename>: key=value[, key=value ...]
    Supported keys: head_trim, tail_trim (float) — slow (float rate) — pair_with
    (str filename) — flag (str).
    Missing file returns an empty dict (not an error).
    """
    path = cfg.clip_lists_dir / f"part{part:02d}_overrides.txt"
    if not path.exists():
        return {}
    out: dict[str, dict[str, object]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        fname, rest = line.split(":", 1)
        fname = fname.strip()
        kv: dict[str, object] = {}
        for tok in rest.split(","):
            tok = tok.strip()
            if not tok or "=" not in tok:
                continue
            k, v = tok.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k in ("head_trim", "tail_trim", "slow", "slow_window"):
                try:
                    kv[k] = float(v)
                except ValueError:
                    pass
            else:
                kv[k] = v
        if kv:
            out[fname] = kv
    return out


def _resolve_part_backdrop_override(part: int) -> Optional[list[Path]]:
    """Rule B8: when part==4, use Demo (389INTRO)* from T2 or T3 Part4."""
    if part != 4:
        return None
    for tier in ("T2", "T3"):
        tier_dir = ROOT / "QUAKE VIDEO" / tier / f"Part{part}"
        if not tier_dir.exists():
            continue
        found = list(tier_dir.rglob("Demo (389INTRO)*.avi"))
        if found:
            return [found[0]]
    print(f"  [title_card] WARN: Part 4 Demo (389INTRO) not found; "
          f"falling back to FL auto-pick")
    return None


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


def _stem_to_src_avi_name(norm_path: Path) -> str:
    """Recover the original .avi filename from a normalized mp4 stem.

    build_body_chunks operates on *_cfr60(_slow|_zoom|_fast)?.mp4 files. We
    strip those suffixes to look up per-clip overrides keyed by src .avi name.
    """
    stem = norm_path.stem
    for suf in ("_cfr60_slow", "_cfr60_zoom", "_cfr60_fast", "_cfr60"):
        if stem.endswith(suf):
            stem = stem[: -len(suf)]
            break
    return f"{stem}.avi"


def build_body_chunks(
    part: int,
    normalized: List[Path],
    chunks_dir: Path,
    cfg: Config,
    overrides: Optional[dict[str, dict[str, object]]] = None,
) -> tuple[Path, List[Path]]:
    """Pre-encode each normalized clip as a CRF 20 fast libx264 chunk with
    Rule P1-L trim (1 s head / 2 s tail). Returns (concat_list_path, chunks).

    Idempotent — skips chunks that already exist.
    """
    chunks_dir.mkdir(parents=True, exist_ok=True)
    chunks: List[Path] = []
    tail_default = cfg.clip_tail_trim
    overrides = overrides or {}
    skipped_short = 0

    def _trims_for(src: Path) -> tuple[float, float, Optional[dict[str, object]]]:
        is_fl = "FL" in src.stem.upper()
        head = cfg.clip_head_trim_fl if is_fl else cfg.clip_head_trim_fp
        tail = tail_default
        src_name = _stem_to_src_avi_name(src)
        ov = overrides.get(src_name)
        if ov is not None:
            if "head_trim" in ov:
                head = float(ov["head_trim"])
            if "tail_trim" in ov:
                tail = float(ov["tail_trim"])
        return head, tail, ov

    kept_normalized: List[Path] = []
    for src in normalized:
        head, tail, ov = _trims_for(src)
        dur_full = _probe_duration(src, cfg)
        post_trim = dur_full - head - tail
        # Rule P1-L v3 (Part 6 v8 draft review 2026-04-18): short-clip protection.
        # If the post-trim body would fall below the minimum playable floor,
        # DROP the clip from the Part. No compression, no stretching.
        # Slow-mo'd clips get a pass — their normalized file is already
        # time-stretched (setpts) so the floor check would incorrectly drop them.
        is_slow_variant = src.stem.endswith("_slow")
        if (not is_slow_variant) and post_trim < cfg.min_playable_duration_s:
            skipped_short += 1
            print(f"  [SKIP_TOO_SHORT] {src.name} "
                  f"(post-trim={post_trim:.2f}s < {cfg.min_playable_duration_s}s)")
            continue
        kept_normalized.append(src)
    normalized = kept_normalized
    if skipped_short:
        print(f"  [P1-L v3] skipped {skipped_short} clip(s) below "
              f"min_playable_duration_s ({cfg.min_playable_duration_s}s)")

    for i, src in enumerate(normalized):
        chunk = chunks_dir / f"chunk_{i:04d}.mp4"
        chunks.append(chunk)
        if chunk.exists():
            continue
        head, tail, ov = _trims_for(src)
        dur_full = _probe_duration(src, cfg)
        trim_dur = max(0.5, dur_full - head - tail)
        # Override: `slow=<rate>` applies setpts=(1/rate)*PTS, atempo=rate
        slow_rate: Optional[float] = None
        if ov is not None and "slow" in ov:
            try:
                slow_rate = float(ov["slow"])
                if slow_rate <= 0 or abs(slow_rate - 1.0) < 1e-3:
                    slow_rate = None
            except Exception:
                slow_rate = None
        if ov is not None and "pair_with" in ov:
            partner = ov["pair_with"]
            adjacent = False
            if i > 0:
                adjacent = partner in _stem_to_src_avi_name(normalized[i - 1])
            if not adjacent and i + 1 < len(normalized):
                adjacent = partner in _stem_to_src_avi_name(normalized[i + 1])
            if not adjacent:
                print(f"  [override] WARN: {src.name} pair_with={partner} "
                      f"not adjacent in normalized list")

        # Rule P1-D (review burn-in): bottom-left clip-stem watermark so the
        # user can reference specific clips by name during review. Strip
        # normalization suffixes so the watermark matches the source .avi.
        # Rule P1-BB: force CFR at ingest (Wolfcam AVIs can be VFR).
        vf = (
            f"scale={cfg.target_width}:{cfg.target_height}:flags=lanczos,"
            f"fps={cfg.target_fps}"
        )
        af_parts: list[str] = []
        # Rule P1-EE: event-localized slow. When enabled AND the clip has a
        # recognized game event (Rule P1-Z v2), apply slow around the event
        # peak ± slow_window instead of the entire clip. When NO event is
        # recognized, log a warning and SKIP the slow effect rather than
        # falling back to the v10 whole-clip setpts (P1-EE explicitly
        # deprecates that behavior).
        use_event_localized = bool(getattr(cfg, "event_localized_slow", False))
        if slow_rate is not None and use_event_localized:
            window_s = float(
                (ov.get("slow_window") if ov is not None else None)
                or getattr(cfg, "slow_window_default", 0.8)
            )
            try:
                events = _audio_onsets.recognize_game_events(src, cfg=cfg)
            except Exception:
                events = []
            eligible = [e for e in events if e.confidence >= 0.55]
            if eligible:
                top = eligible[0]
                # Remap event peak to post-trim clip timeline.
                event_t = float(top.t) - float(head)
                if event_t < 0:
                    event_t = 0.0
                if event_t > trim_dur:
                    event_t = trim_dur
                audio_mode = _event_localized.select_audio_mode(top.event_type)
                v_filt, a_filt = _event_localized.build_event_localized_slow_filter(
                    event_t=event_t,
                    slow_rate=slow_rate,
                    window_s=window_s,
                    audio_mode=audio_mode,
                    clip_duration=trim_dur,
                )
                vf += f",{v_filt}"
                af_parts.append(a_filt)
                print(
                    f"  [P1-EE] {src.name} event={top.event_type} "
                    f"t={top.t:.2f}s conf={top.confidence:.2f} "
                    f"window=±{window_s:.2f}s mode={audio_mode}"
                )
            else:
                print(
                    f"  [P1-EE] {src.name} NO recognized event "
                    f"(slow skipped per P1-EE)"
                )
        elif slow_rate is not None:
            # Legacy whole-clip slow (used when cfg.event_localized_slow=False).
            vf += f",setpts=(1/{slow_rate:.4f})*PTS"
            af_parts.append(f"atempo={slow_rate:.4f}")
        af_parts.append("aresample=async=1")
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

        # Rule P1-BB: intermediates encode audio as pcm_s16le (not AAC) to avoid
        # AAC priming delay compounding across N chunks. Final render transcodes
        # once to AAC. Container switched to .mkv-compatible mov for WAV-in-mp4
        # quirks — we keep .mp4 but use pcm_s16le which ffmpeg muxes via mov.
        cmd = [
            str(cfg.ffmpeg_bin), "-y",
            "-ss", f"{head:.3f}",
            "-t",  f"{trim_dur:.3f}",
            "-vsync", "cfr", "-r", str(cfg.target_fps),
            "-i",  str(src),
            "-vf", vf,
            "-af", ",".join(af_parts),
            "-c:v", "libx264",
            "-crf", str(cfg.review_chunk_crf if cfg.review_mode else 20),
            "-preset", (cfg.review_chunk_preset if cfg.review_mode else "fast"),
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-r", str(cfg.target_fps),
            "-g", str(cfg.target_fps * 2),
            "-c:a", "pcm_s16le", "-ar", "48000",
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
    # Rule P1-H v4 audio-drift fix: every chunk enters the chain with PTS reset
    # to zero and async=1:first_pts=0. The v8 chain compounded ~40 ms drift per
    # N seams because acrossfade preserves upstream PTS wobble — pinning every
    # chunk's PTS origin kills the drift before it starts.
    for i in range(N):
        v_parts.append(
            f"[{i}:v]setpts=PTS-STARTPTS,setsar=1,fps={cfg.target_fps},format=yuv420p[v{i}]"
        )
        a_parts.append(
            f"[{i}:a]asetpts=PTS-STARTPTS,aresample=async=1:first_pts=0[a{i}]"
        )

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
        # Rule P1-BB: keep PCM through the body master so AAC priming delay
        # never enters the chain. Final render transcodes to AAC once.
        "-c:a", "pcm_s16le", "-ar", "48000",
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
    # Rule P1-Y v2: suffix "_quake_v10" busts the v9 Bebas caches so every
    # Part picks up the Quake-style metallic/scanline/aberration card.
    out = ASSETS_DIR / f"title_card_part{part:02d}_quake_v10.mp4"
    if out.exists():
        print(f"  [cache] {out.name}")
        return out
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    backdrop = _resolve_part_backdrop_override(part)
    render_title_card(part, out, cfg, backdrop_paths=backdrop)
    return out


def ensure_pantheon_trim(cfg: Config) -> Path:
    # Rule P1-X (Part 6 v8 draft review): PANTHEON = 5 s, not 7 s. Cache key is
    # parameterised on duration so the 7 s v8 trim stays as-is and the new 5 s
    # trim lives next to it. Changing cfg.intro_clip_duration auto-busts.
    dur_tag = f"{int(cfg.intro_clip_duration)}s"
    out = OUTPUT_DIR / f"_pantheon_trim_{dur_tag}.mp4"
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
    # Rule P1-G v5 (Part 4 v9 review 2026-04-18) — segmented audio graph:
    #   Segment A (0 .. intro_clip_duration): PANTHEON own audio, NO music
    #   Segment B (intro .. intro+8):         music fades in 0 -> music_volume
    #                                         over 1.5 s, NO game audio
    #   Segment C (intro+8 ..):               game@game_audio_volume + ducked
    #                                         music@music_volume via sidechain
    #
    # Previously (v3) music amix'd across ALL three segments — user said that
    # swallowed the PANTHEON opening and provided no fade-in. v5 builds each
    # segment independently then concat=a=1.
    intro_dur = float(cfg.intro_clip_duration)
    title_dur = 8.0
    mus_vol = cfg.music_volume
    game_vol = cfg.game_audio_volume
    fadein = min(1.5, cfg.music_fadein_s)

    # Sidechain the music under game audio for segment C.
    sidechain_frag = _sidechain.build_sidechain_filter_chain(
        "segC_mus", "segC_game"
    )

    filter_complex = (
        # Video: plain concat of 3 files (body already has internal xfades)
        f"[0:v][1:v][2:v]concat=n=3:v=1:a=0[vout];"

        # --- Segment A: PANTHEON audio, no music ---
        f"[0:a]aresample=48000:async=1,"
        f"apad=whole_dur={intro_dur},atrim=0:{intro_dur},"
        f"asetpts=PTS-STARTPTS,volume=1.0[segA];"

        # --- Segment B: title card — music only, fading in from 0 ---
        # Title card's own audio is silent (we muxed anullsrc/pcm) so ignore [1:a].
        f"[3:a]atrim=0:{title_dur},asetpts=PTS-STARTPTS,"
        f"volume={mus_vol},afade=t=in:st=0:d={fadein:.3f},"
        f"aresample=48000:async=1[segB];"

        # --- Segment C: body game audio + ducked music ---
        f"[2:a]aresample=48000:async=1,"
        f"asetpts=PTS-STARTPTS,volume={game_vol}[segC_game];"
        f"[3:a]atrim=start={title_dur},asetpts=PTS-STARTPTS,"
        f"volume={mus_vol},apad,"
        f"aresample=48000:async=1[segC_mus];"
        f"{sidechain_frag}"
        # sidechain helper emits [mix]; rename to [segC]
        f"[mix]anull[segC];"

        # Concat A | B | C
        f"[segA][segB][segC]concat=n=3:v=0:a=1[aout]"
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
        overrides = load_clip_overrides(part, cfg)
        if overrides:
            print(f"  [overrides] loaded {len(overrides)} entries from "
                  f"part{part:02d}_overrides.txt")
        concat_list, chunks = build_body_chunks(
            part, normalized, chunks_dir, cfg, overrides=overrides,
        )

    # --- Intro assets ---
    title_card   = ensure_title_card(part, cfg)
    pantheon     = ensure_pantheon_trim(cfg)

    # --- Beat-snap seam offsets (Rule P1-V) ---
    # We need chunk durs first, then consult the main music track's pre-computed
    # beat grid. If no beats sidecar exists (or part skipped), fall back to naive.
    beat_snapped: Optional[List[float]] = None
    # Beats sidecar is named `<music>.beats.json`. For Parts whose music ships
    # as multi-file chunks (e.g. part06_music_01.mp3 + _02.mp3) the canonical
    # <partNN_music>.mp3 may not exist on disk even though the beats JSON was
    # pre-computed against the merged track. Look for the beats sidecar
    # directly rather than requiring the mp3 file.
    music_dir = ROOT / "phase1" / "music"
    beats_candidates = [
        music_dir / f"part{part:02d}_music.mp3.beats.json",
        music_dir / f"part{part:02d}_music.ogg.beats.json",
        music_dir / f"part{part:02d}_music.wav.beats.json",
    ]
    beats_file = next((p for p in beats_candidates if p.exists()), None)
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

    # ── Rule B5: Music plan ship gate ──
    # music_stitcher already writes partNN_music_plan.json and raises
    # RuntimeError if any track was truncated — nothing more to do here.

    # ── Rule B4: Music structure + beat sync (P1-Z, P1-CC) ──
    try:
        struct_out = OUTPUT_DIR / f"part{part:02d}_music_structure.json"
        structure = _music_structure.analyze_music(music_path, struct_out)
        print(f"  [music-structure] bpm={structure.get('bpm_global', 0):.1f}  "
              f"downbeats={len(structure.get('downbeats', []))}  "
              f"drops={len(structure.get('drops', []))}")
    except Exception as exc:
        print(f"  [music-structure] WARN: analysis failed ({exc}); "
              f"skipping beat-sync plan")
        structure = None

    if structure is not None:
        try:
            # Build clip metadata for beat_sync
            def _tier_tag(p: Path) -> str:
                s = str(p).upper()
                if "\\T1\\" in s or "/T1/" in s: return "T1"
                if "\\T2\\" in s or "/T2/" in s: return "T2"
                if "\\T3\\" in s or "/T3/" in s: return "T3"
                return "T2"
            # Map chunks back to their src .avi paths via normalized sidecar when
            # possible. Here we use the chunk itself as a proxy for analysis.
            clip_paths = [str(c) for c in chunks]
            peaks = _audio_onsets.find_action_peaks_per_clip(clip_paths)
            clips_meta: list[dict[str, object]] = []
            for c in chunks:
                dur = _probe_duration(c, cfg)
                clips_meta.append({
                    "path": str(c),
                    "tier": _tier_tag(c),
                    "duration": dur,
                    "head_trim": 0.0,   # chunks already trimmed
                    "tail_trim": 0.0,
                })
            seams = plan_beat_cuts(
                structure, peaks, clips_meta,
                intro_offset=cfg.intro_clip_duration + 8.0,
            )
            beats_path = write_beats_json(seams, part, OUTPUT_DIR)
            tight = sum(1 for s in seams if s["tag"] == "TIGHT")
            print(f"  [beat-plan] wrote {beats_path.name}  tight={tight}/"
                  f"{len(seams)}")
        except Exception as exc:
            print(f"  [beat-plan] WARN: plan_beat_cuts failed ({exc})")

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

    # ── Rule B6: Objective audio ship gate (P1-G v4) ──
    try:
        stem_dir = OUTPUT_DIR / f"_part{part:02d}_stems"
        stem_dir.mkdir(parents=True, exist_ok=True)
        mus_stem = _audio_levels.extract_music_stem(
            final_out, music_path, stem_dir / "music.wav",
        )
        game_stem = _audio_levels.extract_game_stem(
            final_out, chunks, stem_dir / "game.wav",
        )
        level_data = _audio_levels.measure_music_vs_game(mus_stem, game_stem)
        _audio_levels.write_levels_json(part, level_data, OUTPUT_DIR)
        print(f"  [level-gate] music={level_data['music_lufs']:.1f} LUFS  "
              f"game={level_data['game_lufs']:.1f} LUFS  "
              f"delta={level_data['delta']:.1f} LU  "
              f"pass={level_data['pass']}")
        if not level_data["pass"]:
            failed_name = final_out.with_name(
                final_out.stem + "_FAILED_LEVEL_GATE" + final_out.suffix
            )
            try:
                final_out.rename(failed_name)
                final_out = failed_name
                print(f"  [level-gate] ERROR: renamed output to {failed_name.name}")
            except Exception as mv:
                print(f"  [level-gate] ERROR: could not rename output: {mv}")
    except Exception as exc:
        print(f"  [level-gate] WARN: measurement failed ({exc})")

    # ── Rule B7: Post-render sync audit (P1-BB) ──
    try:
        audit: dict[str, object] = {"part": part, "checks": []}
        checks: list[dict[str, float]] = []
        for t_mark in (60.0, 180.0, 300.0):
            # Probe video & audio stream durations up to t_mark via ffprobe
            def _stream_dur(stream_idx: str) -> float:
                r = subprocess.run(
                    [str(cfg.ffprobe_bin), "-v", "error",
                     "-select_streams", stream_idx,
                     "-show_entries", "stream=duration",
                     "-of", "csv=p=0", str(final_out)],
                    capture_output=True, text=True,
                )
                try:
                    return float(r.stdout.strip())
                except Exception:
                    return 0.0
            vdur = _stream_dur("v:0")
            adur = _stream_dur("a:0")
            if vdur <= t_mark or adur <= t_mark:
                continue
            drift_ms = abs(vdur - adur) * 1000.0
            checks.append({
                "t_mark_s": t_mark,
                "video_dur_s": vdur,
                "audio_dur_s": adur,
                "drift_ms": drift_ms,
            })
        audit["checks"] = checks
        max_drift = max((c["drift_ms"] for c in checks), default=0.0)
        audit["max_drift_ms"] = max_drift
        audit["pass"] = max_drift <= 40.0
        (OUTPUT_DIR / f"part{part:02d}_sync_audit.json").write_text(
            __import__("json").dumps(audit, indent=2)
        )
        print(f"  [sync-audit] max drift {max_drift:.1f} ms  pass={audit['pass']}")
        if not audit["pass"]:
            raise RuntimeError(
                f"sync-audit FAILED: max drift {max_drift:.1f} ms > 40 ms"
            )
    except RuntimeError:
        raise
    except Exception as exc:
        print(f"  [sync-audit] WARN: audit failed ({exc})")

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
