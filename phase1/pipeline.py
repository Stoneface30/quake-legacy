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

    if n == 1:
        # Single-clip: no concat needed
        v_chain = "[0:v]"
        a_chain = "[0:a]"
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
    total_duration = sum(durations) - xfade_dur * max(0, n - 1)
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


def assemble_part(
    clips: List[Path],
    output_path: Path,
    cfg: Config,
    music_path: Optional[Path] = None,
    preset: Optional[GradePreset] = None,
    preview_seconds: Optional[int] = None,
    crf_override: Optional[int] = None,
    preset_override: Optional[str] = None,
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
    music_input_index = len(clips) if music_path else None

    filter_complex = build_filter_complex(
        clips, durations, preset, cfg,
        music_input_index=music_input_index
    )

    # C1 fix: single -filter_complex call, music handled inside it
    cmd = [str(cfg.ffmpeg_bin), "-y"]
    for clip in clips:
        cmd += ["-i", str(clip)]
    if music_path:
        cmd += ["-i", str(music_path)]

    cmd += ["-filter_complex", filter_complex]
    cmd += ["-map", "[vout]"]
    cmd += ["-map", "[aout]"]  # always [aout] — game audio + music mixed inside filter_complex

    encode_crf    = crf_override    if crf_override    is not None else cfg.crf
    encode_preset = preset_override if preset_override is not None else cfg.preset

    cmd += [
        "-c:v", "libx264",
        "-crf", str(encode_crf),
        "-preset", encode_preset,
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-r", str(cfg.target_fps),
        "-g", str(cfg.target_fps * 2),
        "-bf", "2",
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
    result = subprocess.run(cmd, capture_output=True, text=True)
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
        result = subprocess.run(cmd_trim, capture_output=True, text=True)
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
    result = subprocess.run(cmd_concat, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Intro prepend failed:\n{result.stderr[-500:]}")

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"  [DONE] {output_path.name} with intro ({size_mb:.0f}MB)")
    return output_path
