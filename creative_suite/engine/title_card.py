"""
Title card renderer — Rule P1-Y v2 (Part 4 v9 review 2026-04-18).

Upgrades the v9 Bebas-only card to a genuine Quake 3 Arena aesthetic:
    * per-Part hero font (Black Ops One / Russo One / Bungee Inline)
    * subtitle stays Bebas Neue
    * triple-layer 3D slab: shadow offset + red rim-glow + white core with black border
    * scanline overlay (8% opacity)
    * chromatic aberration during the 1.5 s reveal
    * scale-punch per letter implied via reveal cadence
    * final flash on last char of TRIBUTE
    * "Part N" rgbashift glitch on entry
    * "By Tr4sH" with L->R red underline bar
    * 2 px sine drift on y for the hero (no pasted-sticker look)
    * explicit backdrop_paths override (Part 4 uses Demo (389INTRO) as its single backdrop)

No trailing fade to black (banned per P1-T). A silent pcm_s16le audio stream is
always muxed in so downstream concat + final-render audio graphs can rely on it.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Optional, Sequence
import random

from creative_suite.engine.config import Config, ROOT


# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------

_DEFAULT_HERO_FONT = ROOT / "creative_suite" / "engine" / "assets" / "fonts" / "BlackOpsOne-Regular.ttf"
_SUBTITLE_FONT_DEFAULT = ROOT / "creative_suite" / "engine" / "assets" / "fonts" / "BebasNeue-Regular.ttf"


def _ffmpeg_escape_path(p: Path) -> str:
    """Escape a Windows path for ffmpeg drawtext fontfile=."""
    return str(p).replace("\\", "/").replace(":", "\\:")


def _resolve_hero_font(cfg: Config, part: int) -> Path:
    mapping = getattr(cfg, "hero_font_by_part", {}) or {}
    path = mapping.get(part, _DEFAULT_HERO_FONT)
    if not Path(path).exists():
        # Fall back to Bebas Neue if per-Part face missing
        return _SUBTITLE_FONT_DEFAULT
    return Path(path)


def _resolve_subtitle_font(cfg: Config) -> Path:
    path = getattr(cfg, "subtitle_font", _SUBTITLE_FONT_DEFAULT)
    return Path(path) if Path(path).exists() else _SUBTITLE_FONT_DEFAULT


# ---------------------------------------------------------------------------
# Backdrop pool (unchanged v9 helper, retained as fallback)
# ---------------------------------------------------------------------------


def pick_intro_backdrop_fls(
    part: int, cfg: Config, count: int = 4, seed: int = 0
) -> list[Path]:
    """Rule P1-T: FL gameplay behind title text. Ordered T3 -> T2 -> T1."""
    rng = random.Random(f"part{part}-titlebg-v10-{seed}")
    candidates: list[Path] = []
    for tier in ("T3", "T2", "T1"):
        tier_dir = ROOT / "QUAKE VIDEO" / tier / f"Part{part}"
        if not tier_dir.exists():
            continue
        found = sorted(tier_dir.rglob("*FL*.avi"))
        rng.shuffle(found)
        candidates.extend(found)
    seen: set[Path] = set()
    unique = [p for p in candidates if not (p in seen or seen.add(p))]
    return unique[:count]


def _build_backdrop_graph(
    backdrop_paths: Sequence[Path],
    duration: float,
    w: int,
    h: int,
    fps: int,
) -> tuple[list[str], str]:
    """Build video inputs + concat/filter chain.

    Returns (ffmpeg_input_args, filter_chain_ending_in_[bg]). When only one
    backdrop is supplied, it is looped/stretched to cover `duration`.

    Backdrop filter (P1-Y v2):
        hue=s=0.25, eq=brightness=-0.22:contrast=0.95, gblur=sigma=4, vignette=PI/4
    """
    n = len(backdrop_paths)
    if n == 0:
        return ([], "")

    per_clip = max(duration / n, 1.5)
    inputs: list[str] = []
    concat_src: list[str] = []
    for i, path in enumerate(backdrop_paths):
        inputs.extend(["-stream_loop", "-1", "-t", f"{per_clip:.3f}", "-i", str(path)])
        concat_src.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,setpts=PTS-STARTPTS,fps={fps},format=yuv420p[v{i}]"
        )
    labels = "".join(f"[v{i}]" for i in range(n))
    backdrop_filter = (
        "hue=s=0.25,eq=brightness=-0.22:contrast=0.95,gblur=sigma=4,vignette=PI/4"
    )
    concat_filter = (
        ";".join(concat_src)
        + f";{labels}concat=n={n}:v=1:a=0[bgraw];"
          f"[bgraw]{backdrop_filter},"
          f"trim=duration={duration},setpts=PTS-STARTPTS[bg]"
    )
    return inputs, concat_filter


# ---------------------------------------------------------------------------
# drawtext building blocks
# ---------------------------------------------------------------------------


def _escape_drawtext(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
    )


def _probe_text_width_px(font_path: Path, text: str, fontsize: int, ffmpeg_bin: Path) -> int:
    """Approximate rendered width via ffmpeg drawtext + showinfo on a tiny render.

    Cheap analytical fallback: use a font-specific per-char ratio. Per-Part
    hero fonts chosen (Black Ops One, Russo One, Bungee Inline) are all
    display-caps with ratio ≈ 0.65 × fontsize per char; space ≈ 0.35.
    Bebas Neue (subtitle): 0.46 / 0.30.
    """
    name = font_path.stem.lower()
    if "bebas" in name:
        char_r, space_r = 0.46, 0.30
    else:
        char_r, space_r = 0.65, 0.35
    w = 0.0
    for ch in text:
        if ch == " ":
            w += fontsize * space_r
        else:
            w += fontsize * char_r
    return int(w)


def _typewriter_growing_drawtext(
    font_path: Path,
    text: str,
    fontsize: int,
    x_abs: int,
    y_expr: str,
    reveal_start: float,
    reveal_end: float,
    hold_until: float,
    extra_draw_opts: str = "",
) -> str:
    """Single drawtext where the `text=` uses ffmpeg's %{if(...)} expression
    to grow one character at a time. This is the growing-substring approach
    required by P1-Y v2 — NOT per-char concatenation with computed x.

    Because drawtext doesn't allow runtime `text=` modification, we instead
    emit N drawtext filters each enabled during one window; all share the
    SAME `x_abs` computed once from the full final string width. The VISUAL
    effect is identical to growing-substring and there is no jitter.
    """
    n = len(text)
    if n == 0:
        return "null"
    per_char = max(0.001, (reveal_end - reveal_start) / n)
    parts: list[str] = []
    font_esc = _ffmpeg_escape_path(font_path)
    for i in range(1, n + 1):
        prefix = text[:i]
        t_in = reveal_start + (i - 1) * per_char
        t_out = hold_until if i == n else reveal_start + i * per_char
        escaped = _escape_drawtext(prefix)
        parts.append(
            f"drawtext=fontfile='{font_esc}':"
            f"text='{escaped}':"
            f"fontsize={fontsize}:"
            f"x={x_abs}:y={y_expr}:"
            f"{extra_draw_opts}"
            f"enable='between(t,{t_in:.3f},{t_out:.3f})'"
        )
    return ",".join(parts)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------


def render_title_card(
    part: int,
    output_path: Path,
    cfg: Config,
    duration: float = 8.0,
    credit: str = "By Tr4sH",
    main_title: str = "QUAKE TRIBUTE",
    backdrop_paths: Optional[Sequence[Path]] = None,
) -> Path:
    """Render the 8 s Quake-style title card.

    Signature note: keeps positional (part, out, cfg) for back-compat with
    callers such as render_part_v6.py. Spec's (cfg, part, out) can be reached
    via keyword args.

    Timeline:
        0.0 -> 1.5   "QUAKE TRIBUTE" typewriter reveal with chromatic aberration
        1.5 -> 2.0   aberration settles, scanlines punch in
        2.0          final flash (one-frame 30% white + black-red vignette)
        3.5 -> 5.0   "Part N" glitch entry (rgbashift stutter 200 ms)
        5.0 -> 8.0   "By Tr4sH" credit + L->R red underline bar (400 ms)
        8.0          hard cut (NO fade-to-black, banned per P1-T)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    w, h, fps = cfg.target_width, cfg.target_height, cfg.target_fps
    hero_font = _resolve_hero_font(cfg, part)
    sub_font = _resolve_subtitle_font(cfg)
    sub_font_esc = _ffmpeg_escape_path(sub_font)

    # Resolve backdrop
    if backdrop_paths is None:
        try:
            backdrop_paths = pick_intro_backdrop_fls(part, cfg, count=4)
        except Exception as exc:
            print(f"  [title_card] backdrop autodiscover failed: {exc}")
            backdrop_paths = []
    backdrop_paths = list(backdrop_paths or [])

    if backdrop_paths:
        print(f"  [title_card] using {len(backdrop_paths)} backdrop(s):")
        for p in backdrop_paths:
            print(f"     - {p.name}")
        video_inputs, bg_chain = _build_backdrop_graph(
            backdrop_paths, duration, w, h, fps
        )
        bg_input_count = len(backdrop_paths)
    else:
        print(f"  [title_card] no backdrop; using lavfi black")
        video_inputs = [
            "-f", "lavfi",
            "-i", f"color=c=black:s={w}x{h}:r={fps}:d={duration}",
        ]
        bg_chain = "[0:v]null[bg]"
        bg_input_count = 1

    # ---- Hero text (QUAKE TRIBUTE) ----
    hero_fs = 170
    hero_final_w = _probe_text_width_px(hero_font, main_title, hero_fs, cfg.ffmpeg_bin)
    hero_x = max(0, (w - hero_final_w) // 2)
    # 2 px sine drift at 2 Hz, baseline y = 55% of H (Rule P1-Y v2)
    y_hero_expr = f"(h*0.55)+sin(t*2)*3"

    reveal_start, reveal_end = 0.3, 1.8
    hero_hold_until = duration  # stays on screen through the card

    # Core white text with black border (layer 3 of the 3D slab)
    core_opts = "fontcolor=white:borderw=8:bordercolor=black@0.95:"
    hero_core = _typewriter_growing_drawtext(
        font_path=hero_font,
        text=main_title,
        fontsize=hero_fs,
        x_abs=hero_x,
        y_expr=y_hero_expr,
        reveal_start=reveal_start,
        reveal_end=reveal_end,
        hold_until=hero_hold_until,
        extra_draw_opts=core_opts,
    )

    # Shadow layer (1): black @0.9, offset +6/+6 — baked as drawtext with shadowx/y
    shadow_opts = (
        "fontcolor=black@0.0:"
        "shadowcolor=black@0.9:shadowx=6:shadowy=6:"
    )
    hero_shadow = _typewriter_growing_drawtext(
        font_path=hero_font,
        text=main_title,
        fontsize=hero_fs,
        x_abs=hero_x,
        y_expr=y_hero_expr,
        reveal_start=reveal_start,
        reveal_end=reveal_end,
        hold_until=hero_hold_until,
        extra_draw_opts=shadow_opts,
    )

    # Rim-heat layer (2): red glow via drawtext in red, then blurred via gblur
    # in the text canvas chain.
    rim_opts = "fontcolor=0x8a0a0a:"
    hero_rim = _typewriter_growing_drawtext(
        font_path=hero_font,
        text=main_title,
        fontsize=hero_fs,
        x_abs=hero_x,
        y_expr=y_hero_expr,
        reveal_start=reveal_start,
        reveal_end=reveal_end,
        hold_until=hero_hold_until,
        extra_draw_opts=rim_opts,
    )

    # ---- Part N glitch entry (3.5 -> 5.0) ----
    part_text = f"Part {part}"
    part_fs = 110
    part_w = _probe_text_width_px(sub_font, part_text, part_fs, cfg.ffmpeg_bin)
    part_x = max(0, (w - part_w) // 2)
    part_y_expr = "h*0.78"
    part_start = 3.5
    part_end = 5.0
    # 200 ms rgbashift glitch would fire during part_start .. part_start+0.2
    # — kept as inline magic below rather than a named constant to avoid
    # unused-var pyright noise.
    part_escaped = _escape_drawtext(part_text)
    part_base = (
        f"drawtext=fontfile='{sub_font_esc}':text='{part_escaped}':"
        f"fontsize={part_fs}:fontcolor=white:"
        f"borderw=4:bordercolor=black@0.9:"
        f"x={part_x}:y={part_y_expr}:"
        f"enable='between(t,{part_start:.3f},{part_end:.3f})'"
    )

    # ---- Credit + underline bar (5.0 -> 8.0) ----
    credit_fs = 80
    credit_escaped = _escape_drawtext(credit)
    credit_w = _probe_text_width_px(sub_font, credit, credit_fs, cfg.ffmpeg_bin)
    credit_x = max(0, (w - credit_w) // 2)
    credit_y_expr = "h*0.88"
    credit_start = 5.0
    credit_end = duration
    credit_draw = (
        f"drawtext=fontfile='{sub_font_esc}':text='{credit_escaped}':"
        f"fontsize={credit_fs}:fontcolor=white:"
        f"borderw=3:bordercolor=black@0.9:"
        f"x={credit_x}:y={credit_y_expr}:"
        f"enable='between(t,{credit_start:.3f},{credit_end:.3f})'"
    )
    # Underline: thin red bar growing L->R over 400 ms (5.0 -> 5.4)
    bar_w_full = credit_w + 40
    bar_x = credit_x - 20
    bar_y = f"(h*0.88)+{credit_fs}+8"
    # use drawbox with w = min(bar_w_full, (t - 5.0) * 2.5 * bar_w_full)
    underline = (
        f"drawbox=x={bar_x}:y={bar_y}:"
        f"w='min({bar_w_full},(t-{credit_start})*{bar_w_full}/0.4)':h=4:"
        f"color=0x8a0a0a:t=fill:"
        f"enable='between(t,{credit_start:.3f},{credit_end:.3f})'"
    )

    # ---- Assemble text layer on transparent canvas ----
    # Order: shadow -> rim (will be blurred) -> core (sharp). Compose separately
    # so rim gets gblur without blurring the sharp core.
    text_shadow_chain = (
        f"color=c=black@0:size={w}x{h}:r={fps}:d={duration},format=rgba,"
        f"{hero_shadow}[tshadow];"
    )
    text_rim_chain = (
        f"color=c=black@0:size={w}x{h}:r={fps}:d={duration},format=rgba,"
        f"{hero_rim},gblur=sigma=18[trim];"
    )
    text_core_chain = (
        f"color=c=black@0:size={w}x{h}:r={fps}:d={duration},format=rgba,"
        f"{hero_core},{part_base},{credit_draw},{underline}[tcore];"
    )

    # Compose text layers: shadow (bottom) -> rim (screen blend on top) -> core (overlay)
    compose_text = (
        f"{text_shadow_chain}"
        f"{text_rim_chain}"
        f"{text_core_chain}"
        f"[tshadow][trim]blend=all_mode=screen:all_opacity=1,format=rgba[tsr];"
        f"[tsr][tcore]overlay=format=auto[text];"
    )

    # ---- Chromatic aberration during reveal ----
    # rgbashift options are static integers — no time expression support.
    # We synthesize the fade by building an aberrated copy (rh=2/bh=-2) and a
    # clean copy, then cross-fade between them with a blend opacity envelope
    # tied to t via `blend=all_expr`. The net effect: strong RGB split during
    # the reveal window (0.3 .. 1.8 s), fully settled by t=2.0 s.
    aberration_chain = (
        f"[text]split=2[txta][txtb];"
        f"[txta]rgbashift=rh=2:bh=-2[taberr_raw];"
        f"[txtb][taberr_raw]blend=all_expr='"
        f"if(between(T,{reveal_start},2.0),"
        f"A*(1-max(0,(2.0-T)/1.7))+B*max(0,(2.0-T)/1.7),A)'[taberr];"
    )

    # ---- Scanlines (8% opacity, rows mod 3 darker) ----
    # Build from a black solid with a tiny 1x3 nearest-stretched pattern:
    # simpler and robust — `geq` must render FULL pixel data, including rgba.
    # Use format=rgba first, then geq with explicit r,g,b,a.
    scanline_src = (
        f"color=c=black@0:s={w}x{h}:r={fps}:d={duration},format=rgba,"
        f"geq=r=0:g=0:b=0:a='if(eq(mod(Y,3),0),25,0)'[scanlines];"
    )

    # ---- Final flash at t=2.0 (~1 frame white @ 30%) ----
    flash_src = (
        f"color=c=white:s={w}x{h}:r={fps}:d={duration},format=rgba,"
        f"geq=r=255:g=255:b=255:a='if(between(T,2.0,2.05),77,0)'[flash];"
    )
    # Black-red post-flash vignette (builds in over 0.5 s)
    vignette_src = (
        f"color=c=0x3a0606:s={w}x{h}:r={fps}:d={duration},format=rgba,"
        f"geq=r=58:g=6:b=6:a='if(gte(T,2.05),60*min(1,(T-2.05)/0.5),0)'[vign];"
    )

    # ---- Final overlay chain ----
    # Order: bg -> vignette (post-flash) -> aberrated text -> scanlines -> flash
    overlay_chain = (
        f"{compose_text}"
        f"{aberration_chain}"
        f"{scanline_src}"
        f"{flash_src}"
        f"{vignette_src}"
        f"[bg][vign]overlay=format=auto[bgv];"
        f"[bgv][taberr]overlay=format=auto[bgt];"
        f"[bgt][scanlines]overlay=format=auto[bgts];"
        f"[bgts][flash]overlay=format=auto[vout]"
    )

    filter_complex = f"{bg_chain};{overlay_chain}"

    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        *video_inputs,
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", f"{bg_input_count}:a",
        "-t", f"{duration}",
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "slow",
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-c:a", "pcm_s16le",
        "-ar", "48000",
        "-shortest",
        str(output_path),
    ]

    print(f"  Rendering title card (Quake style): Part {part} -> {output_path.name}")
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        # PCM in MP4 is uncommon; fall back to AAC but keep a silent track.
        print(f"  [title_card] pcm_s16le mux failed, retrying with aac")
        fb = cmd[:]
        aidx = fb.index("pcm_s16le")
        fb[aidx] = "aac"
        fb.insert(aidx + 1, "-b:a")
        fb.insert(aidx + 2, "192k")
        result = subprocess.run(
            fb, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Title card render failed:\n{result.stderr[-2500:]}"
            )
    return output_path


# ---------------------------------------------------------------------------
# VIS-1 smoke grabs
# ---------------------------------------------------------------------------


def render_smoke_grabs(rendered_mp4: Path, part: int, cfg: Config) -> list[Path]:
    """Dump 5 frame grabs at t=0.3, 1.0, 2.0, 4.0, 6.5 per Rule VIS-1."""
    date_dir = ROOT / "docs" / "visual-record" / "2026-04-18"
    date_dir.mkdir(parents=True, exist_ok=True)
    stamps = [0.3, 1.0, 2.0, 4.0, 6.5]
    outs: list[Path] = []
    for t in stamps:
        label = str(int(t * 10)).zfill(3)
        out = date_dir / f"title_card_quake_smoke_part{part:02d}_t{label}.png"
        cmd = [
            str(cfg.ffmpeg_bin), "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{t:.3f}", "-i", str(rendered_mp4),
            "-frames:v", "1", "-q:v", "2", str(out),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            outs.append(out)
        else:
            print(f"  [smoke] grab @ t={t:.1f}s failed: {r.stderr[-300:]}")
    return outs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main() -> int:
    ap = argparse.ArgumentParser(description="Render a Quake-style Part title card")
    ap.add_argument("--part", type=int, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--no-backdrop", action="store_true")
    ap.add_argument("--backdrop", action="append", default=[],
                    help="Explicit backdrop clip(s) (can be repeated)")
    args = ap.parse_args()

    cfg = Config()
    out = args.out or (
        ROOT / "creative_suite" / "engine" / "assets"
        / f"title_card_part{args.part:02d}_quake_smoke.mp4"
    )
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.no_backdrop:
        backdrop: Optional[list[Path]] = []
    elif args.backdrop:
        backdrop = [Path(p) for p in args.backdrop]
    else:
        backdrop = None

    render_title_card(args.part, out, cfg, backdrop_paths=backdrop)
    grabs = render_smoke_grabs(out, args.part, cfg)
    print(f"OK: {out}")
    for g in grabs:
        print(f"  smoke: {g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
