"""
FFmpeg assembly pipeline: concat + xfade + color grade + bloom + music.
All in a single -filter_complex. No shell=True anywhere.

Audio rule: game audio is ALWAYS preserved under music.
In-game sounds (grenade hits, rocket impacts, rail cracks) are the texture of the film.
Music at full volume, game audio at cfg.game_audio_volume (default 0.30).
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import json, subprocess
from phase1.config import Config
from phase1.inventory import get_clip_info
from phase1.transitions import Transition, TransitionKind


@dataclass
class GradePreset:
    """Color grade and effect parameters."""
    contrast:       float = 1.4
    saturation:     float = 1.7
    brightness:     float = 0.0
    gamma_r:        float = 1.08
    gamma_b:        float = 0.92
    bloom_sigma:    int   = 18
    bloom_opacity:  float = 0.3    # matches spec exactly
    sharpen_amount: float = 0.5

    @classmethod
    def from_file(cls, path: Path) -> "GradePreset":
        data = json.loads(path.read_text())
        valid = {k for k in data if k in cls.__dataclass_fields__}
        return cls(**{k: data[k] for k in valid})


def get_real_durations(clips: List[Path], cfg: Config) -> List[float]:
    """Probe each clip for actual duration. Required for correct xfade offsets."""
    durations = []
    for clip in clips:
        info = get_clip_info(clip, cfg)
        if info.duration_s <= 0:
            raise RuntimeError(f"Could not probe duration of {clip.name} — may be corrupt")
        durations.append(info.duration_s)
    return durations


def build_filter_complex(
    clips: List[Path],
    durations: List[float],
    preset: GradePreset,
    cfg: Config,
    music_input_index: Optional[int] = None,
    game_audio_volume: Optional[float] = None,
    trim_starts: Optional[List[float]] = None,
    trim_durations: Optional[List[float]] = None,
    per_clip_vf: Optional[List[str]] = None,
    transition_plan: Optional[List[Transition]] = None,
) -> str:
    """
    Build ONE unified filter_complex string for N clips + optional music.

    Pipeline:
      1. xfade cross-dissolve between consecutive clips (video + audio)
      2. Color grade (eq filter)
      3. Bloom (gblur + screen blend)
      4. Sharpen (unsharp)
      5. Fade in / fade out
      6. Audio: game audio (vol=game_audio_volume) + music mixed → [aout]

    Outputs: [vout] and [aout] always.
    When music present: [aout] = amix(game_audio_lowered, music_faded).
    When no music: [aout] = game_audio_faded only.
    """
    if game_audio_volume is None:
        game_audio_volume = cfg.game_audio_volume
    n = len(clips)
    assert n == len(durations)
    parts = []

    xfade_dur = cfg.xfade_duration

    # If any per-clip trimming or per-clip VF chains are requested, build a
    # per-input preprocessing stage so each input is trimmed + filtered independently
    # before concatenation. This is how we implement:
    #   - beat-sync duration override (trim_durations)
    #   - multi-angle interleave (trim_starts + trim_durations select a window
    #     inside each input)
    #   - per-clip variety effects (per_clip_vf)
    needs_preprocess = bool(trim_starts) or bool(trim_durations) or bool(per_clip_vf)

    if needs_preprocess:
        starts  = trim_starts     or [0.0] * n
        trimdur = trim_durations  or durations
        vfs     = per_clip_vf     or [""] * n
        assert len(starts) == n and len(trimdur) == n and len(vfs) == n

        for i in range(n):
            s = max(0.0, float(starts[i]))
            d = max(0.05, float(trimdur[i]))
            vf = vfs[i]
            # Video: trim window, reset PTS, then optional per-clip VF
            v_filter = f"trim=start={s:.3f}:duration={d:.3f},setpts=PTS-STARTPTS"
            if vf:
                v_filter = f"{v_filter},{vf}"
            parts.append(f"[{i}:v]{v_filter}[v{i}]")
            # Audio: mirrored trim, reset PTS
            parts.append(
                f"[{i}:a]atrim=start={s:.3f}:duration={d:.3f},"
                f"asetpts=PTS-STARTPTS[a{i}]"
            )

        if n == 1:
            v_chain = "[v0]"
            a_chain = "[a0]"
        elif transition_plan and any(t.kind != TransitionKind.HARD_CUT for t in transition_plan):
            # TransitionPlanner routed: use xfade chain for non-HARD_CUT boundaries.
            # Hard cuts are realized as 1-frame xfade=fade (invisible) so the whole
            # graph stays a uniform pairwise xfade chain — keeps offsets predictable.
            assert len(transition_plan) == n - 1, "transition_plan must be N-1"
            trim = [max(0.05, float(trimdur[i])) for i in range(n)]
            prev_label = "v0"
            prev_a     = "a0"
            accum_len  = trim[0]
            for i in range(1, n):
                tr = transition_plan[i - 1]
                kind = tr.kind
                dur  = max(0.033, float(tr.duration)) if kind != TransitionKind.HARD_CUT else 0.033
                # Map TransitionKind -> xfade transition name
                xfade_name = {
                    TransitionKind.HARD_CUT:    "fade",
                    TransitionKind.FLASH_CUT:   "fade",
                    TransitionKind.XFADE:       "dissolve",
                    TransitionKind.SECTION:     "dissolve",
                    TransitionKind.FADE_BLACK:  "fadeblack",
                    TransitionKind.WHITE_FLASH: "fadewhite",
                }.get(kind, "fade")
                offset = max(0.0, accum_len - dur)
                out_v = f"xv{i}"
                out_a = f"xa{i}"
                parts.append(
                    f"[{prev_label}][v{i}]xfade=transition={xfade_name}"
                    f":duration={dur:.3f}:offset={offset:.3f}[{out_v}]"
                )
                parts.append(
                    f"[{prev_a}][a{i}]acrossfade=d={dur:.3f}[{out_a}]"
                )
                prev_label = out_v
                prev_a     = out_a
                accum_len += trim[i] - dur
            v_chain = f"[{prev_label}]"
            a_chain = f"[{prev_a}]"
        else:
            inputs_v = "".join(f"[v{i}]" for i in range(n))
            inputs_a = "".join(f"[a{i}]" for i in range(n))
            parts.append(f"{inputs_v}concat=n={n}:v=1:a=0[concat_v]")
            parts.append(f"{inputs_a}concat=n={n}:v=0:a=1[concat_a]")
            v_chain = "[concat_v]"
            a_chain = "[concat_a]"

        # Effective durations for total_duration calc below are the trim dirs
        effective_durations = [max(0.05, float(trimdur[i])) for i in range(n)]
    elif n == 1:
        # Single-clip: no concat needed
        v_chain = "[0:v]"
        a_chain = "[0:a]"
        effective_durations = durations
    else:
        # Hard-cut concat — fragmovie rule: chain quality > visible transitions.
        # xfade created visible glitches at fast cuts. concat gives clean hard cuts.
        # xfade is reserved only for PANTHEON intro prepend (handled in prepend_intro).
        inputs_v = "".join(f"[{i}:v]" for i in range(n))
        inputs_a = "".join(f"[{i}:a]" for i in range(n))
        parts.append(
            f"{inputs_v}concat=n={n}:v=1:a=0[concat_v]"
        )
        parts.append(
            f"{inputs_a}concat=n={n}:v=0:a=1[concat_a]"
        )
        v_chain = "[concat_v]"
        a_chain = "[concat_a]"
        effective_durations = durations

    # Color grade
    eq = (
        f"eq=contrast={preset.contrast}"
        f":saturation={preset.saturation}"
        f":brightness={preset.brightness}"
        f":gamma_r={preset.gamma_r}"
        f":gamma_b={preset.gamma_b}"
    )
    parts.append(f"{v_chain}{eq}[graded]")

    # Bloom (gblur + screen blend)
    parts.append(f"[graded]split[orig][forbloom]")
    parts.append(f"[forbloom]gblur=sigma={preset.bloom_sigma}[blurred]")
    parts.append(
        f"[orig][blurred]blend=all_mode=screen:all_opacity={preset.bloom_opacity}[bloomed]"
    )

    # Sharpen
    parts.append(
        f"[bloomed]unsharp=luma_msize_x=5:luma_msize_y=5"
        f":luma_amount={preset.sharpen_amount}[sharp]"
    )

    # Total video duration after xfade overlaps
    total_duration = sum(effective_durations) - xfade_dur * max(0, n - 1)
    # I2 fix: clamp fade_out_start so it never goes before intro_fade_in
    fade_out_start = max(cfg.intro_fade_in, total_duration - cfg.outro_fade_out)

    parts.append(
        f"[sharp]fade=t=in:st=0:d={cfg.intro_fade_in},"
        f"fade=t=out:st={fade_out_start:.4f}:d={cfg.outro_fade_out}[vout]"
    )

    if music_input_index is not None:
        # Game audio: lower volume, fade in/out
        parts.append(
            f"{a_chain}volume={game_audio_volume:.2f},"
            f"afade=t=in:st=0:d={cfg.intro_fade_in},"
            f"afade=t=out:st={fade_out_start:.4f}:d={cfg.outro_fade_out}[game_faded]"
        )
        # Music: fade in/out (full volume — game audio rides underneath)
        parts.append(
            f"[{music_input_index}:a]"
            f"afade=t=in:st=0:d={cfg.intro_fade_in},"
            f"afade=t=out:st={fade_out_start:.4f}:d={cfg.outro_fade_out}[music_faded]"
        )
        # Mix: game audio texture + music backbone
        # normalize=0 prevents amix from halving volume levels
        parts.append(
            f"[game_faded][music_faded]amix=inputs=2:duration=first:normalize=0[aout]"
        )
    else:
        parts.append(
            f"{a_chain}afade=t=in:st=0:d={cfg.intro_fade_in},"
            f"afade=t=out:st={fade_out_start:.4f}:d={cfg.outro_fade_out}[aout]"
        )

    return ";\n".join(parts)


def _validate_music_path(music_path: Path) -> Path:
    """C3 fix: validate music_path before passing to subprocess."""
    allowed_ext = {".mp3", ".ogg", ".wav", ".flac", ".aac", ".m4a"}
    if not music_path.exists():
        raise FileNotFoundError(f"Music file not found: {music_path}")
    if music_path.suffix.lower() not in allowed_ext:
        raise ValueError(f"Unsupported music format: {music_path.suffix}. Use: {allowed_ext}")
    return music_path.resolve()


# Empirical ceiling: ffmpeg's filter_complex concat filter chokes with
# `-22 Invalid argument` / "Could not open encoder before EOF" once the
# input count × per-clip filter chain overwhelms the graph allocator.
# Observed failure at 52 inputs even with -filter_complex_script sidecar.
# Above this threshold we pre-encode each clip then use the `concat` demuxer
# (no filter-graph concat hit). Grade/bloom/sharpen/music-mix run as a final
# 1-input pass over the stitched file — small graph, no ceiling issue.
CONCAT_FILTER_CLIP_LIMIT = 40


def _assemble_via_concat_demuxer(
    clips: List[Path],
    output_path: Path,
    cfg: Config,
    music_path: Optional[Path],
    preset: GradePreset,
    preview_seconds: Optional[int],
    crf_override: Optional[int],
    preset_override: Optional[str],
    codec_override: Optional[str],
    trim_starts: Optional[List[float]],
    trim_durations: Optional[List[float]],
    per_clip_vf: Optional[List[str]],
    durations: List[float],
) -> Path:
    """
    High-clip-count assembly path that sidesteps ffmpeg's filter_complex concat
    ceiling. Pre-encodes each clip (trim + per-clip VF baked in) to H.264
    intermediates, then uses the `concat` demuxer to stitch, then runs a single
    final pass for grade/bloom/sharpen/fade + music mix.

    Transitions are all hard cuts in this path (matches Style B, see Rule P1-H).
    Cross-fades between clips are NOT supported here — if a transition_plan
    with xfade is required, chunk the clips into groups <= CONCAT_FILTER_CLIP_LIMIT
    and use the filter-complex path per group.
    """
    import shutil as _shutil
    n = len(clips)
    starts  = trim_starts    or [0.0] * n
    trimdur = trim_durations or durations
    vfs     = per_clip_vf    or [""]  * n

    # Preflight disk-space check: ~20MB per clip intermediate at CRF 20 fast,
    # plus ~500MB final. Bail early if we're obviously going to run out.
    free_bytes = _shutil.disk_usage(output_path.parent).free
    est_need = (n * 20 + 800) * 1024 * 1024  # generous estimate
    if free_bytes < est_need:
        raise RuntimeError(
            f"Insufficient disk space for concat-demuxer render: "
            f"{free_bytes/1e9:.1f}GB free, ~{est_need/1e9:.1f}GB needed "
            f"for {n} intermediates + final. Free up space on {output_path.drive} first."
        )

    work_dir = output_path.parent / (output_path.stem + "_chunks")
    work_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: encode each clip to an intermediate with trim + per-clip VF applied.
    # Use identical codec/params across all chunks so the concat demuxer can stream-copy.
    print(f"  [concat-demuxer] pre-encoding {n} clips to intermediates...")
    intermediates: List[Path] = []
    for i, clip in enumerate(clips):
        chunk_path = work_dir / f"chunk_{i:04d}.mp4"
        intermediates.append(chunk_path)
        if chunk_path.exists():
            continue
        s = max(0.0, float(starts[i]))
        d = max(0.05, float(trimdur[i]))
        vf = f"scale={cfg.target_width}:{cfg.target_height}:flags=lanczos,fps={cfg.target_fps}"
        if vfs[i]:
            vf = f"{vfs[i]},{vf}"
        cmd = [
            str(cfg.ffmpeg_bin), "-y",
            "-ss", f"{s:.3f}",
            "-t",  f"{d:.3f}",
            "-i", str(clip),
            "-vf", vf,
            "-af", "aresample=async=1",
            # Intermediates are lossy-but-cheap: they'll be re-encoded in the
            # final grade pass anyway. CRF 20 preset fast = ~3x smaller and
            # faster than CRF 15 medium, no visible difference after final encode.
            "-c:v", "libx264",
            "-crf", "20",
            "-preset", "fast",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
            "-r", str(cfg.target_fps),
            "-g", str(cfg.target_fps * 2),
            "-c:a", "aac",
            "-ar", "48000",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(chunk_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(
                f"Concat-demuxer pre-encode failed on {clip.name}:\n{result.stderr[-500:]}"
            )

    # Step 2: write concat list. No separate stitch pass — the final pass reads
    # the concat demuxer directly as its input, saving 3-5GB of temp disk.
    concat_list = work_dir / "_concat.txt"
    concat_list.write_text(
        "".join(f"file '{p.as_posix()}'\n" for p in intermediates),
        encoding="utf-8",
    )

    # Step 3: final grade/bloom/sharpen/fade + music mix. Small graph: 1-2 inputs.
    effective_durations = [max(0.05, float(trimdur[i])) for i in range(n)]
    total_duration = sum(effective_durations)
    fade_out_start = max(cfg.intro_fade_in, total_duration - cfg.outro_fade_out)

    eq = (
        f"eq=contrast={preset.contrast}"
        f":saturation={preset.saturation}"
        f":brightness={preset.brightness}"
        f":gamma_r={preset.gamma_r}"
        f":gamma_b={preset.gamma_b}"
    )
    fc_parts = [
        f"[0:v]{eq}[graded]",
        f"[graded]split[orig][forbloom]",
        f"[forbloom]gblur=sigma={preset.bloom_sigma}[blurred]",
        f"[orig][blurred]blend=all_mode=screen:all_opacity={preset.bloom_opacity}[bloomed]",
        f"[bloomed]unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount={preset.sharpen_amount}[sharp]",
        f"[sharp]fade=t=in:st=0:d={cfg.intro_fade_in},"
        f"fade=t=out:st={fade_out_start:.4f}:d={cfg.outro_fade_out}[vout]",
    ]
    game_vol = cfg.game_audio_volume
    if music_path is not None:
        fc_parts.append(
            f"[0:a]volume={game_vol:.2f},"
            f"afade=t=in:st=0:d={cfg.intro_fade_in},"
            f"afade=t=out:st={fade_out_start:.4f}:d={cfg.outro_fade_out}[game_faded]"
        )
        fc_parts.append(
            f"[1:a]afade=t=in:st=0:d={cfg.intro_fade_in},"
            f"afade=t=out:st={fade_out_start:.4f}:d={cfg.outro_fade_out}[music_faded]"
        )
        fc_parts.append(
            f"[game_faded][music_faded]amix=inputs=2:duration=first:normalize=0[aout]"
        )
    else:
        fc_parts.append(
            f"[0:a]afade=t=in:st=0:d={cfg.intro_fade_in},"
            f"afade=t=out:st={fade_out_start:.4f}:d={cfg.outro_fade_out}[aout]"
        )

    filter_complex = ";\n".join(fc_parts)
    fc_script = output_path.parent / (output_path.stem + ".filter.txt")
    fc_script.write_text(filter_complex, encoding="utf-8")

    cmd_final = [
        str(cfg.ffmpeg_bin), "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
    ]
    if music_path:
        cmd_final += ["-i", str(music_path)]
    cmd_final += [
        "-filter_complex_script", str(fc_script),
        "-map", "[vout]",
        "-map", "[aout]",
    ]

    encode_crf    = crf_override    if crf_override    is not None else cfg.crf
    encode_preset = preset_override if preset_override is not None else cfg.preset
    encode_codec  = codec_override  if codec_override  is not None else "libx264"

    NVENC_CODECS = {"av1_nvenc", "hevc_nvenc", "h264_nvenc"}
    nvenc_highbitdepth = False
    nvenc_pix_fmt = "yuv420p"
    if encode_codec in NVENC_CODECS:
        nvenc_preset = encode_preset if encode_preset.startswith("p") else "p7"
        nvenc_tune   = getattr(cfg, "final_render_nvenc_tune", "hq")
        cmd_final += [
            "-c:v", encode_codec,
            "-preset", nvenc_preset,
            "-tune", nvenc_tune,
            "-multipass", "fullres",
            "-spatial-aq", "1",
            "-temporal-aq", "1",
            "-rc-lookahead", "32",
            "-b_ref_mode", "middle",
            "-bf", "4",
        ]
        # Blackwell gen-9 NVENC: 10-bit internal at zero speed cost, kills bloom banding.
        if getattr(cfg, "final_render_nvenc_highbitdepth", False) and encode_codec in ("av1_nvenc", "hevc_nvenc"):
            cmd_final += ["-highbitdepth", "1"]
            nvenc_highbitdepth = True
            nvenc_pix_fmt = getattr(cfg, "final_render_nvenc_pix_fmt", "p010le")
        if encode_codec == "hevc_nvenc":
            cmd_final += ["-rc", "constqp", "-qp", str(encode_crf), "-refs", "4"]
        else:
            cmd_final += ["-rc", "vbr", "-b:v", "0", "-cq", str(encode_crf)]
            if encode_codec == "h264_nvenc":
                cmd_final += ["-refs", "8"]
    else:
        cmd_final += ["-c:v", encode_codec, "-crf", str(encode_crf), "-preset", encode_preset]
        if encode_codec == "libx264":
            cmd_final += ["-profile:v", "high"]
        elif encode_codec == "libx265":
            cmd_final += ["-x265-params", "log-level=error"]
        cmd_final += ["-bf", "2"]

    cmd_final += [
        "-pix_fmt", nvenc_pix_fmt,
        "-r", str(cfg.target_fps),
        "-g", str(cfg.target_fps * 2),
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", cfg.audio_bitrate,
        "-movflags", "+faststart",
    ]
    if preview_seconds:
        cmd_final += ["-t", str(preview_seconds)]
    cmd_final.append(str(output_path))

    print(f"Rendering (concat-demuxer path): {output_path.name}")
    print(f"  Clips: {n}, CRF: {encode_crf}, preset: {encode_preset}, codec: {encode_codec}")
    result = subprocess.run(cmd_final, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(
            f"Final pass (concat-demuxer) failed for {output_path.name}:\n{result.stderr[-1000:]}"
        )

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"  [DONE] {output_path} ({size_mb:.0f}MB)")

    # Cleanup: intermediates can be 5-10GB per Part. Remove on success.
    # Kept on failure so the user can inspect / resume.
    try:
        for p in intermediates:
            p.unlink(missing_ok=True)
        concat_list.unlink(missing_ok=True)
        work_dir.rmdir()
        print(f"  [cleanup] removed intermediates dir {work_dir.name}")
    except OSError as e:
        print(f"  [cleanup] could not fully remove {work_dir}: {e}")

    return output_path


def assemble_part(
    clips: List[Path],
    output_path: Path,
    cfg: Config,
    music_path: Optional[Path] = None,
    preset: Optional[GradePreset] = None,
    preview_seconds: Optional[int] = None,
    crf_override: Optional[int] = None,
    preset_override: Optional[str] = None,
    codec_override: Optional[str] = None,
    trim_starts: Optional[List[float]] = None,
    trim_durations: Optional[List[float]] = None,
    per_clip_vf: Optional[List[str]] = None,
    transition_plan: Optional[List[Transition]] = None,
) -> Path:
    """
    Assemble clips -> single MP4 with grade, bloom, xfade, optional music.

    Args:
        clips:            Ordered list of normalized MP4 paths
        output_path:      Output .mp4 path
        cfg:              Config object
        music_path:       Optional audio track (validated before use)
        preset:           GradePreset (uses grade_tribute.json if None)
        preview_seconds:  Limit output duration (fast preview mode)
        crf_override:     Override CRF for preview quality
        preset_override:  Override FFmpeg preset for preview speed

    Returns: output_path
    """
    if not clips:
        raise ValueError("clips list is empty — nothing to assemble")  # S2 fix

    if preset is None:
        preset_file = Path(__file__).parent / "presets" / "grade_tribute.json"
        preset = GradePreset.from_file(preset_file) if preset_file.exists() else GradePreset()

    if music_path is not None:
        music_path = _validate_music_path(music_path)  # C3 fix

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # I1 fix: get real durations from ffprobe, not hardcoded estimate
    durations = get_real_durations(clips, cfg)

    # High-clip-count fallback: ffmpeg's filter_complex concat ceiling (~40-50
    # inputs) breaks the unified-graph path above. Switch to concat-demuxer
    # (pre-encode chunks → stream-copy stitch → 1-input final grade pass).
    # Safe to use whenever transition_plan has no xfade (Style B is hard-cut).
    has_xfade = bool(transition_plan) and any(
        t.kind != TransitionKind.HARD_CUT for t in transition_plan
    )
    if len(clips) > CONCAT_FILTER_CLIP_LIMIT and not has_xfade:
        if preset is None:
            preset_file = Path(__file__).parent / "presets" / "grade_tribute.json"
            preset = GradePreset.from_file(preset_file) if preset_file.exists() else GradePreset()
        return _assemble_via_concat_demuxer(
            clips=clips,
            output_path=output_path,
            cfg=cfg,
            music_path=music_path,
            preset=preset,
            preview_seconds=preview_seconds,
            crf_override=crf_override,
            preset_override=preset_override,
            codec_override=codec_override,
            trim_starts=trim_starts,
            trim_durations=trim_durations,
            per_clip_vf=per_clip_vf,
            durations=durations,
        )

    music_input_index = len(clips) if music_path else None

    filter_complex = build_filter_complex(
        clips, durations, preset, cfg,
        music_input_index=music_input_index,
        trim_starts=trim_starts,
        trim_durations=trim_durations,
        per_clip_vf=per_clip_vf,
        transition_plan=transition_plan,
    )

    # C1 fix: single -filter_complex call, music handled inside it
    cmd = [str(cfg.ffmpeg_bin), "-y"]
    for clip in clips:
        cmd += ["-i", str(clip)]
    if music_path:
        cmd += ["-i", str(music_path)]

    # Windows command-line max length ~32KB. Large filter_complex strings
    # (many inputs + per-clip trim + effects) exceed this. Write to a script
    # file and use -filter_complex_script instead.
    fc_script = output_path.parent / (output_path.stem + ".filter.txt")
    fc_script.write_text(filter_complex, encoding="utf-8")
    cmd += ["-filter_complex_script", str(fc_script)]
    cmd += ["-map", "[vout]"]
    cmd += ["-map", "[aout]"]  # always [aout] — game audio + music mixed inside filter_complex

    encode_crf    = crf_override    if crf_override    is not None else cfg.crf
    encode_preset = preset_override if preset_override is not None else cfg.preset
    encode_codec  = codec_override  if codec_override  is not None else "libx264"

    # Codec-specific flag stacks:
    #   libx264 / libx265 = CPU encoders (use -crf + -preset).
    #   av1_nvenc / hevc_nvenc / h264_nvenc = NVIDIA GPU encoders.
    #     Benchmarked in docs/research/nvenc-tuning-2026.md (2026-04-17).
    #     Use `-preset p7 -tune hq -multipass fullres -spatial-aq 1 -temporal-aq 1
    #     -rc-lookahead 32 -b_ref_mode middle -bf 4`. Rate-control mode differs:
    #       av1_nvenc  → -rc vbr -b:v 0 -cq N (works correctly)
    #       hevc_nvenc → -rc constqp -qp N   (vbr+cq caps at ~16 Mbps, broken)
    #       h264_nvenc → -rc vbr -b:v 0 -cq N (works; skip -weighted_pred with bframes)
    NVENC_CODECS = {"av1_nvenc", "hevc_nvenc", "h264_nvenc"}
    pix_fmt = "yuv420p"
    if encode_codec in NVENC_CODECS:
        # NVENC path — encode_crf reused as CQ/QP, encode_preset overridden to p1..p7.
        nvenc_preset = encode_preset if encode_preset.startswith("p") else "p7"
        nvenc_tune   = getattr(cfg, "final_render_nvenc_tune", "hq")
        cmd += [
            "-c:v", encode_codec,
            "-preset", nvenc_preset,
            "-tune", nvenc_tune,
            "-multipass", "fullres",
            "-spatial-aq", "1",
            "-temporal-aq", "1",
            "-rc-lookahead", "32",
            "-b_ref_mode", "middle",
            "-bf", "4",
        ]
        # Blackwell gen-9 NVENC 10-bit internal (Rule P1-J, encoder-recommendation-2026-04-17).
        if getattr(cfg, "final_render_nvenc_highbitdepth", False) and encode_codec in ("av1_nvenc", "hevc_nvenc"):
            cmd += ["-highbitdepth", "1"]
            pix_fmt = getattr(cfg, "final_render_nvenc_pix_fmt", "p010le")
        if encode_codec == "hevc_nvenc":
            cmd += ["-rc", "constqp", "-qp", str(encode_crf), "-refs", "4"]
        else:
            # av1_nvenc + h264_nvenc: VBR + CQ works, b:v 0 disables bitrate cap
            cmd += ["-rc", "vbr", "-b:v", "0", "-cq", str(encode_crf)]
            if encode_codec == "h264_nvenc":
                cmd += ["-refs", "8"]  # do NOT add -weighted_pred (conflicts with bf>0)
    else:
        # CPU path (libx264 / libx265)
        # x265 emits info to stderr by default; silence with -x265-params log-level=error.
        cmd += [
            "-c:v", encode_codec,
            "-crf", str(encode_crf),
            "-preset", encode_preset,
        ]
        if encode_codec == "libx264":
            cmd += ["-profile:v", "high"]
        elif encode_codec == "libx265":
            cmd += ["-x265-params", "log-level=error"]
        cmd += ["-bf", "2"]
    cmd += [
        "-pix_fmt", pix_fmt,
        "-r", str(cfg.target_fps),
        "-g", str(cfg.target_fps * 2),
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", cfg.audio_bitrate,
        "-movflags", "+faststart",
    ]
    if preview_seconds:
        cmd += ["-t", str(preview_seconds)]
    cmd.append(str(output_path))

    print(f"Rendering: {output_path.name}")
    print(f"  Clips: {len(clips)}, CRF: {encode_crf}, preset: {encode_preset}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(
            f"Assembly failed for {output_path.name}:\n{result.stderr[-1000:]}"
        )

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"  [DONE] {output_path} ({size_mb:.0f}MB)")  # S7 fix: no emoji
    return output_path


def prepend_intro(
    part_path: Path,
    output_path: Path,
    cfg: Config,
    intro_duration: Optional[float] = None,
) -> Path:
    """
    Prepend the first N seconds of IntroPart2.mp4 to a rendered Part.

    Rule P1-C: PANTHEON intro prepends to EVERY Part. First 7 seconds only
    (PANTHEON logo animation). The in-game CA Tribute billboard scene that
    follows is NOT used — that was the original editor's personal branding shot.

    Uses ffmpeg concat demuxer (no re-encode of the Part — stream copy where possible).
    Re-encodes intro segment to match Part codec settings.

    Args:
        part_path:      Path to the assembled Part MP4
        output_path:    Path for the final output with intro prepended
        cfg:            Config (provides intro_source, ffmpeg_bin)
        intro_duration: Seconds to use from IntroPart2.mp4 (default: cfg.intro_clip_duration = 7.0)

    Returns: output_path
    """
    if intro_duration is None:
        intro_duration = cfg.intro_clip_duration

    if not cfg.intro_source.exists():
        raise FileNotFoundError(
            f"PANTHEON intro not found: {cfg.intro_source}\n"
            "Place IntroPart2.mp4 at: FRAGMOVIE VIDEOS/IntroPart2.mp4"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: trim intro to N seconds → temp file
    intro_trimmed = output_path.parent / f"_intro_trim_{intro_duration:.0f}s.mp4"
    if not intro_trimmed.exists():
        cmd_trim = [
            str(cfg.ffmpeg_bin), "-y",
            "-ss", "0",
            "-t", str(intro_duration),
            "-i", str(cfg.intro_source),
            "-c:v", "libx264",
            "-crf", "17",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-r", str(cfg.target_fps),
            "-vf", f"scale={cfg.target_width}:{cfg.target_height}:flags=lanczos",
            "-c:a", "aac",
            "-ar", "48000",
            "-b:a", "192k",
            str(intro_trimmed),
        ]
        result = subprocess.run(cmd_trim, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(f"Intro trim failed:\n{result.stderr[-500:]}")

    # Step 2: concat intro + Part using concat filter (re-encode both for seamless join)
    cmd_concat = [
        str(cfg.ffmpeg_bin), "-y",
        "-i", str(intro_trimmed),
        "-i", str(part_path),
        "-filter_complex",
        "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[vout][aout]",
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "slow",
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-r", str(cfg.target_fps),
        "-g", str(cfg.target_fps * 2),
        "-bf", "2",
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", cfg.audio_bitrate,
        "-movflags", "+faststart",
        str(output_path),
    ]

    print(f"  Prepending PANTHEON intro ({intro_duration:.0f}s) -> {output_path.name}")
    result = subprocess.run(cmd_concat, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"Intro prepend failed:\n{result.stderr[-500:]}")

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"  [DONE] {output_path.name} with intro ({size_mb:.0f}MB)")
    return output_path
