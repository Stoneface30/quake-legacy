"""Rule P1-N: per-Part title card video generator.

Produces phase1/assets/title_card_part{NN}.mp4 — a standalone 1920x1080 60fps
~8 second black-background clip containing:
    0s → 3s   "QUAKE TRIBUTE" letter-by-letter reveal
    3s → 5s   "Part N" number fades in
    5s → 7s   "By Tr4sH" credit fades in
    7s → 8s   fade-to-black into upcoming Part content

See CLAUDE.md Rule P1-N and docs/reviews/part4-review-2026-04-17.md §9.

Design notes
------------
- Rendering is done in a single ffmpeg invocation on a synthesized black source
  (`color` lavfi) with chained `drawtext` filters and a final `fade=out`.
- Per-letter reveal is implemented as one `drawtext` filter per letter with
  precomputed x offsets and per-letter `enable='gte(t,i*step)'` gating.
  Fixed per-glyph advance (~65px at 120pt Impact, 40px for space) — Impact's
  widths vary slightly per glyph, but the visual result is clean enough and
  avoids requiring ffprobe font-metrics introspection. This is the documented
  fallback in the task spec.
- Font: Windows system Impact (`C:/Windows/Fonts/impact.ttf`). If absent, falls
  back to Arial Bold. ffmpeg's drawtext requires forward slashes and an escaped
  colon on Windows: `C\:/Windows/Fonts/impact.ttf`.
- Output is cached: re-render only if the target file is missing or older than
  this module file.
"""
from __future__ import annotations
from pathlib import Path
import subprocess
from phase1.config import Config


# Font resolution — drawtext needs a Windows path with escaped colon
_IMPACT = Path("C:/Windows/Fonts/impact.ttf")
_ARIALBD = Path("C:/Windows/Fonts/arialbd.ttf")


def _font_for_drawtext() -> str:
    font = _IMPACT if _IMPACT.exists() else _ARIALBD
    # drawtext expects "C\:/Windows/Fonts/impact.ttf" on Windows
    p = font.as_posix()
    if len(p) > 1 and p[1] == ":":
        p = p[0] + "\\:" + p[2:]
    return p


# Per-glyph advance at 120pt Impact. Impact is a condensed sans — most caps are
# ~60-70px but "I" is very narrow and "W"/"M" are wide. A fixed advance leaves
# ugly gaps after narrow glyphs, so we approximate real metrics. A small kerning
# pad is added on each side in the lookup value.
_IMPACT_ADVANCE_120: dict = {
    "A": 68, "B": 65, "C": 64, "D": 68, "E": 58, "F": 55, "G": 66,
    "H": 68, "I": 28, "J": 48, "K": 64, "L": 54, "M": 82, "N": 68,
    "O": 72, "P": 62, "Q": 72, "R": 66, "S": 58, "T": 58, "U": 66,
    "V": 64, "W": 94, "X": 64, "Y": 60, "Z": 58,
}
_DEFAULT_ADVANCE_120 = 60
_SPACE_ADVANCE_120 = 36


def _advance_px(ch: str, fontsize: int) -> float:
    scale = fontsize / 120.0
    if ch == " ":
        return _SPACE_ADVANCE_120 * scale
    up = ch.upper()
    base = _IMPACT_ADVANCE_120.get(up, _DEFAULT_ADVANCE_120)
    return base * scale


def _letter_positions(text: str, fontsize: int, canvas_w: int = 1920) -> list[tuple[str, int]]:
    """Compute (letter, x_pixel) positions for a horizontally centered string
    at the given fontsize, using per-glyph advances tuned for Impact."""
    widths = [_advance_px(ch, fontsize) for ch in text]
    total = sum(widths)
    start_x = (canvas_w - total) / 2.0
    out: list[tuple[str, int]] = []
    cursor = start_x
    for ch, w in zip(text, widths):
        if ch != " ":
            out.append((ch, int(round(cursor))))
        cursor += w
    return out


def _drawtext_letter(letter: str, x: int, y_expr: str, fontsize: int, fontfile: str,
                     enable_t: float) -> str:
    # Escape single quote in letter (none of our letters need it, but be safe)
    lit = letter.replace("'", r"\'")
    return (
        f"drawtext=fontfile='{fontfile}'"
        f":text='{lit}'"
        f":fontsize={fontsize}"
        f":fontcolor=white"
        f":shadowcolor=black:shadowx=3:shadowy=3"
        f":x={x}"
        f":y={y_expr}"
        f":enable='gte(t\\,{enable_t:.3f})'"
    )


def _drawtext_block(text: str, fontsize: int, fontfile: str, y_expr: str,
                    fade_in_at: float, fade_dur: float = 0.5,
                    x_expr: str = "(w-text_w)/2") -> str:
    lit = text.replace("'", r"\'")
    alpha = f"if(gte(t\\,{fade_in_at:.2f})\\,min((t-{fade_in_at:.2f})/{fade_dur:.2f}\\,1)\\,0)"
    return (
        f"drawtext=fontfile='{fontfile}'"
        f":text='{lit}'"
        f":fontsize={fontsize}"
        f":fontcolor=white"
        f":shadowcolor=black:shadowx=3:shadowy=3"
        f":x={x_expr}"
        f":y={y_expr}"
        f":alpha='{alpha}'"
    )


def _module_mtime() -> float:
    return Path(__file__).stat().st_mtime


def render_title_card(part: int, cfg: Config) -> Path:
    """Render the per-Part title card video. Returns output path.

    Caches: skips render if output exists and is newer than this module file.
    """
    assets_dir = Path(__file__).parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    out = assets_dir / f"title_card_part{part:02d}.mp4"

    if out.exists() and out.stat().st_mtime >= _module_mtime():
        print(f"  [title_card] cached: {out.name}")
        return out

    duration = cfg.title_card_duration
    series = cfg.title_card_series_name
    credit = cfg.title_card_credit
    fontfile = _font_for_drawtext()

    # Type-sizes (spec §9)
    tribute_size = 120
    part_size = 180
    credit_size = 50

    # Vertical placement
    # TRIBUTE slightly above center, Part number below TRIBUTE, credit bottom-right-ish
    tribute_y = "(h/2-160)"
    part_y = "(h/2+60)"
    credit_y = "(h-140)"

    # --- TRIBUTE per-letter reveal -------------------------------------
    letters = _letter_positions(series, fontsize=tribute_size)
    # 2.6s to reveal all letters (0.20s per letter for 13 glyphs)
    step = 0.20
    tribute_drawtexts = [
        _drawtext_letter(ch, x, tribute_y, tribute_size, fontfile, i * step)
        for i, (ch, x) in enumerate(letters)
    ]

    # --- "Part N" block ------------------------------------------------
    part_block = _drawtext_block(
        text=f"Part {part}",
        fontsize=part_size,
        fontfile=fontfile,
        y_expr=part_y,
        fade_in_at=3.0,
        fade_dur=0.5,
    )

    # --- Credit block (bottom-right) -----------------------------------
    credit_block = _drawtext_block(
        text=credit,
        fontsize=credit_size,
        fontfile=fontfile,
        y_expr=credit_y,
        fade_in_at=5.0,
        fade_dur=0.5,
        x_expr="(w-text_w-80)",  # right-aligned with 80px margin
    )

    # --- Final fade-out ------------------------------------------------
    fade_out = f"fade=t=out:st={duration - 1.0:.2f}:d=1.0"

    vf = ",".join(tribute_drawtexts + [part_block, credit_block, fade_out])

    # --- ffmpeg invocation --------------------------------------------
    # Black video source + silent audio source, short-mixed to duration.
    base_cmd = [
        str(cfg.ffmpeg_bin), "-y",
        "-f", "lavfi", "-i", f"color=c=black:s={cfg.target_width}x{cfg.target_height}:r={cfg.target_fps}:d={duration}",
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
        "-vf", vf,
        "-t", f"{duration}",
        "-shortest",
    ]

    # Encode with NVENC (spec §"Encode with same NVENC settings as main pipeline")
    nvenc_enc = [
        "-c:v", cfg.final_render_nvenc_codec,
        "-preset", cfg.final_render_nvenc_preset,
        "-tune", cfg.final_render_nvenc_tune,
        "-rc", "vbr",
        "-cq", str(cfg.final_render_nvenc_cq),
        "-pix_fmt", cfg.final_render_nvenc_pix_fmt if cfg.final_render_nvenc_highbitdepth else "yuv420p",
    ]
    if cfg.final_render_nvenc_highbitdepth:
        nvenc_enc += ["-highbitdepth", "1"]

    audio_enc = ["-c:a", "aac", "-ar", "48000", "-b:a", "192k"]
    tail = ["-movflags", "+faststart", str(out)]

    cmd = base_cmd + nvenc_enc + audio_enc + tail
    print(f"  [title_card] rendering Part {part} -> {out.name}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        # NVENC fallback: libx264 CRF 15 slow (still re-encoded downstream)
        print(f"  [title_card] NVENC failed, falling back to libx264...")
        cmd_fallback = base_cmd + [
            "-c:v", "libx264",
            "-crf", "15",
            "-preset", "slow",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
        ] + audio_enc + tail
        result = subprocess.run(cmd_fallback, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(
                f"Title card render failed:\n"
                f"  filter: {vf[:400]}...\n"
                f"  stderr: {result.stderr[-800:]}"
            )

    size_kb = out.stat().st_size / 1024
    print(f"  [title_card] [DONE] {out.name} ({size_kb:.0f} KB)")
    return out


if __name__ == "__main__":
    import sys
    part = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    render_title_card(part, Config())
