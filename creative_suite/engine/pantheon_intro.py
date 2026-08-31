"""PANTHEON animated intro + outro generator.

Rebuilds the series identity lost with `IntroPart2.mp4` (Rule P1-C). The original
asset is gone from disk, so the intro is regenerated procedurally rather than
restored.

The temple mark (docs/brand/pantheon-mark.svg) is redrawn with PIL instead of
rasterised: no SVG rasteriser is installed, and drawing it directly lets each
element animate independently and stay crisp at 1080p.

Intro beat sheet (7.0 s @ 60 fps, over graded FL demo footage):
    0.00-1.10   dark hold, backdrop pushes in
    0.70-2.30   five columns rise from the stylobate, centre-out
    2.10-2.75   entablature draws left -> right
    2.60-3.45   pediment strokes outward from the apex
    3.30-3.90   oculus blooms
    3.70-4.05   light sweep across the mark + one-frame white flash
    4.00-5.40   "PANTHEON" wordmark fades up
    5.40-7.00   push-in settles, hard cut (no fade -- Rule P1-H)

Outro (30 s cooldown): slow FL footage, mark held small and high, stacked
credits, hard cut at the end.

CLI:
    python -m creative_suite.engine.pantheon_intro --part 4 --what both
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from creative_suite.engine.config import Config
from creative_suite.engine.title_card import pick_intro_backdrop_fls

GOLD = (232, 185, 35)

# The original series intro asset, if it ever turns up. Set PANTHEON_INTRO_ASSET
# to its path and it is used verbatim; otherwise the procedural mark below is
# the fallback. No recursive drive scans, and swapping in the real file requires
# no renderer code change.
INTRO_ASSET_ENV = "PANTHEON_INTRO_ASSET"


def original_intro_asset() -> Path | None:
    """Configured original intro asset, or None to use the procedural mark."""
    import os

    raw = os.environ.get(INTRO_ASSET_ENV, "").strip()
    if not raw:
        return None
    p = Path(raw)
    return p if p.is_file() else None

# --- mark geometry, in the SVG's 120x120 space -------------------------------
COLUMN_XS = (22.0, 37.0, 60.0, 83.0, 98.0)
COL_TOP, COL_BOT = 48.0, 90.0
PEDIMENT = ((12.0, 46.0), (60.0, 8.0), (108.0, 46.0))
ENTAB = (8.0, 46.0, 112.0, 46.0)
STYLOBATE = (
    (10.0, 90.0, 110.0, 90.0, 2.0, 1.0),
    (6.0, 96.0, 114.0, 96.0, 1.5, 0.6),
    (4.0, 102.0, 116.0, 102.0, 1.0, 0.35),
)
OCULUS_C = (60.0, 26.0)


def _ease_out(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def _seg(t: float, a: float, b: float) -> float:
    """Normalised 0..1 progress of `t` across the window [a, b]."""
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    return (t - a) / (b - a)


def _gold(alpha: float) -> tuple[int, int, int, int]:
    return (GOLD[0], GOLD[1], GOLD[2], max(0, min(255, int(255 * alpha))))


def draw_mark(t: float, size: int, supersample: int = 2) -> Image.Image:
    """Draw the animated temple mark at time `t` seconds. Returns RGBA."""
    span = size * supersample
    img = Image.new("RGBA", (span, span), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = span / 120.0

    def lw(w: float) -> int:
        return max(1, int(round(w * k)))

    # stylobate fades in with the first column
    base = _ease_out(_seg(t, 0.70, 1.30))
    if base > 0:
        for x1, y1, x2, y2, w, op in STYLOBATE:
            d.line([x1 * k, y1 * k, x2 * k, y2 * k],
                   fill=_gold(op * base), width=lw(w))

    # columns rise, centre column first then outward
    for slot, ci in enumerate((2, 1, 3, 0, 4)):
        a = 0.70 + slot * 0.16
        p = _ease_out(_seg(t, a, a + 0.55))
        if p <= 0:
            continue
        x = COLUMN_XS[ci] * k
        y_bot = COL_BOT * k
        y_top = y_bot - (COL_BOT - COL_TOP) * k * p
        d.line([x, y_bot, x, y_top], fill=_gold(1.0), width=lw(2))

    # entablature draws left -> right
    p = _ease_out(_seg(t, 2.10, 2.75))
    if p > 0:
        x1, y1, x2, _y2 = ENTAB
        d.line([x1 * k, y1 * k, (x1 + (x2 - x1) * p) * k, y1 * k],
               fill=_gold(1.0), width=lw(2))

    # pediment strokes outward from the apex, both sides together
    p = _ease_out(_seg(t, 2.60, 3.45))
    if p > 0:
        (lx, ly), (ax, ay), (rx, ry) = PEDIMENT
        d.line([ax * k, ay * k, (ax + (lx - ax) * p) * k, (ay + (ly - ay) * p) * k],
               fill=_gold(1.0), width=lw(2.5))
        d.line([ax * k, ay * k, (ax + (rx - ax) * p) * k, (ay + (ry - ay) * p) * k],
               fill=_gold(1.0), width=lw(2.5))

    # oculus blooms
    p = _ease_out(_seg(t, 3.30, 3.90))
    if p > 0:
        cx, cy = OCULUS_C[0] * k, OCULUS_C[1] * k
        r = 7 * k * p
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  outline=_gold(0.7 * p), width=lw(1.5))
        r2 = 3 * k * p
        d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=_gold(0.5 * p))

    if supersample > 1:
        img = img.resize((size, size), Image.LANCZOS)
    return img


def add_glow(mark: Image.Image, strength: float = 0.55) -> Image.Image:
    """Gold bloom behind the strokes."""
    if strength <= 0:
        return mark
    radius = max(1, mark.width // 90)
    blur = mark.filter(ImageFilter.GaussianBlur(radius=radius))
    blur.putalpha(blur.getchannel("A").point(
        lambda v: int(v * min(1.0, strength))))
    return Image.alpha_composite(blur, mark)


def add_sweep(mark: Image.Image, t: float) -> Image.Image:
    """Diagonal light sweep, masked to the mark's own strokes."""
    p = _seg(t, 3.70, 4.05)
    if p <= 0 or p >= 1:
        return mark
    w, h = mark.size
    band = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    cx = int(-w * 0.4 + p * w * 1.8)
    bw = max(4, int(w * 0.10))
    for i in range(-bw, bw, 2):
        a = int(150 * (1 - abs(i) / bw))
        bd.line([cx + i, 0, cx + i - int(h * 0.35), h],
                fill=(255, 255, 255, a), width=3)
    band = band.filter(ImageFilter.GaussianBlur(radius=max(1, w // 220)))
    # light only where the mark actually is
    masked = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    masked.paste(band, (0, 0), mask=mark.getchannel("A"))
    return Image.alpha_composite(mark, masked)


def _pick_font(cfg: Config, size: int) -> ImageFont.FreeTypeFont:
    cands = [getattr(cfg, "hero_font_by_part", {}).get(4),
             getattr(cfg, "subtitle_font", None)]
    for cand in cands:
        if cand and Path(cand).exists():
            return ImageFont.truetype(str(cand), size)
    return ImageFont.load_default()


# The beat sheet in draw_mark()/add_sweep() is authored against this length;
# shorter intros replay the same choreography, compressed.
BEATSHEET_LEN = 7.0


def build_overlay_frames(out_dir: Path, cfg: Config, duration: float = 7.0,
                         w: int = 1920, h: int = 1080, fps: int = 60) -> int:
    """Render the RGBA overlay PNG sequence. Returns the frame count.

    Rule P1-N caps the PANTHEON segment at 5 s, so `duration` is scaled onto the
    7 s beat sheet rather than truncating it -- otherwise the wordmark is cut
    mid-fade.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    n = int(round(duration * fps))
    mark_px = int(h * 0.52)
    word_font = _pick_font(cfg, int(h * 0.085))
    tscale = BEATSHEET_LEN / duration

    for i in range(n):
        t = (i / fps) * tscale
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

        scale = 1.0 + 0.10 * _ease_out(_seg(t, 0.0, BEATSHEET_LEN))
        msize = int(mark_px * scale)
        mark = add_sweep(add_glow(draw_mark(t, msize)), t)

        mx = (w - msize) // 2
        my = int(h * 0.20)
        canvas.alpha_composite(mark, (mx, my))

        alpha = _ease_out(_seg(t, 4.00, 5.40))
        if alpha > 0:
            d = ImageDraw.Draw(canvas)
            txt = "PANTHEON"
            bbox = d.textbbox((0, 0), txt, font=word_font)
            tx = (w - (bbox[2] - bbox[0])) // 2
            ty = my + msize + int(h * 0.02)
            d.text((tx, ty), txt, font=word_font, fill=_gold(alpha))

        if abs(t - 4.02) < (0.5 / fps):
            canvas = Image.alpha_composite(
                canvas, Image.new("RGBA", (w, h), (255, 255, 255, 70)))

        canvas.save(out_dir / f"f{i:05d}.png")
    return n


def _graded_backdrop(cfg: Config, part: int, duration: float, w: int, h: int,
                     fps: int, seed: int = 0, slow: bool = False
                     ) -> tuple[list[str], str, int]:
    """Return (ffmpeg inputs, filter chain ending in [bg], input count)."""
    try:
        fls: Sequence[Path] = pick_intro_backdrop_fls(part, cfg, count=3, seed=seed)
    except Exception:
        fls = []

    if not fls:
        return (["-f", "lavfi", "-t", f"{duration}",
                 "-i", f"color=c=0x040610:s={w}x{h}:r={fps}"],
                "[0:v]null[bg]", 1)

    inputs: list[str] = []
    per = max(duration / len(fls), 1.5)
    parts: list[str] = []
    pts = "setpts=1.35*PTS," if slow else "setpts=PTS-STARTPTS,"
    for i, p in enumerate(fls):
        inputs.extend(["-stream_loop", "-1", "-t", f"{per:.3f}", "-i", str(p)])
        parts.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},setsar=1,{pts}fps={fps},format=yuv420p[b{i}]"
        )
    labels = "".join(f"[b{i}]" for i in range(len(fls)))
    # Push the gameplay well down so the gold mark owns the frame.
    chain = (
        ";".join(parts)
        + f";{labels}concat=n={len(fls)}:v=1:a=0[braw];"
        f"[braw]hue=s=0.18,eq=brightness=-0.34:contrast=1.05,"
        f"gblur=sigma=6,vignette=PI/3.5,"
        f"trim=duration={duration},setpts=PTS-STARTPTS[bg]"
    )
    return inputs, chain, len(fls)


def _music_path(cfg: Config, name: str) -> Path | None:
    base = getattr(cfg, "music_dir", None) or Path("creative_suite/engine/music")
    p = Path(base) / name
    return p if p.exists() else None


def render_intro(part: int, out: Path, cfg: Config, duration: float = 7.0,
                 with_music: bool = True) -> Path:
    """Render the animated PANTHEON intro for `part`."""
    w, h, fps = cfg.target_width, cfg.target_height, cfg.target_fps
    out.parent.mkdir(parents=True, exist_ok=True)

    asset = original_intro_asset()
    if asset is not None:
        # Use the real branding asset, trimmed to `duration`, normalised to the
        # reel's format so it drops straight into the segment chain.
        cmd = [str(cfg.ffmpeg_bin), "-y", "-v", "error", "-i", str(asset),
               "-t", f"{duration}",
               "-vf", (f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                       f"crop={w}:{h},setsar=1,fps={fps},format=yuv420p"),
               "-c:v", "libx264", "-crf", "16", "-preset", "medium",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
               str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and out.exists():
            print(f"  [intro] using configured asset {asset.name}")
            return out
        print(f"  [intro] configured asset unusable, falling back to procedural")

    tmp = Path(tempfile.mkdtemp(prefix="pantheon_intro_"))
    try:
        n = build_overlay_frames(tmp, cfg, duration, w, h, fps)
        print(f"  [intro] {n} overlay frames rendered")

        bg_inputs, bg_chain, n_bg = _graded_backdrop(
            cfg, part, duration, w, h, fps)
        ov_idx = n_bg

        # When the intro is bracketed onto a reel that already has a
        # continuous music bed, it must NOT carry its own track -- doing so
        # made the audio swap songs 5 s in with no beat relationship.
        music = _music_path(cfg, "pantheon_intro_music.mp3") if with_music else None

        cmd = [str(cfg.ffmpeg_bin), "-y", "-v", "error"] + bg_inputs
        cmd += ["-framerate", str(fps), "-i", str(tmp / "f%05d.png")]
        if music:
            cmd += ["-i", str(music)]
        else:
            # A music-free intro must still carry a SILENT audio track. With no
            # audio stream at all, any downstream filtergraph referencing [0:a]
            # fails with "matches no streams" and takes the whole render down.
            cmd += ["-f", "lavfi", "-t", f"{duration}",
                    "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]

        # The aberration window is authored in beat-sheet time; map it onto
        # output time so it still lands on the flash when duration != 7 s.
        ab0 = 3.60 * duration / BEATSHEET_LEN
        ab1 = 4.20 * duration / BEATSHEET_LEN

        # Rule P1-G: the PANTHEON segment carries its own audio; music fades in.
        filt = (
            bg_chain
            + f";[{ov_idx}:v]format=rgba[ov];"
            f"[bg][ov]overlay=0:0:format=auto[cmp];"
            f"[cmp]rgbashift=rh=-2:bh=2:enable='between(t,{ab0:.3f},{ab1:.3f})',"
            f"format=yuv420p[vout]"
        )
        cmd += ["-filter_complex", filt, "-map", "[vout]"]
        vol = getattr(cfg, "music_volume", 0.20)
        cmd += ["-map", f"{ov_idx + 1}:a", "-c:a", "aac", "-b:a", "192k"]
        if music:
            cmd += ["-af", f"afade=t=in:st=0:d=1.5,volume={vol}"]
        cmd += ["-t", f"{duration}", "-c:v", "libx264", "-crf", "16",
                "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(fps),
                "-movflags", "+faststart", str(out)]

        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"intro ffmpeg failed:\n{r.stderr[-1500:]}")
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def render_outro(part: int, out: Path, cfg: Config, duration: float = 30.0,
                 with_music: bool = True, label: str | None = None,
                 facts: list | None = None) -> Path:
    """Cooldown outro: slow FL footage, small mark, stacked credits."""
    w, h, fps = cfg.target_width, cfg.target_height, cfg.target_fps
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="pantheon_outro_"))
    try:
        inputs, bg, n_bg = _graded_backdrop(
            cfg, part, duration, w, h, fps, seed=7, slow=True)

        plate = tmp / "mark.png"
        add_glow(draw_mark(6.0, int(h * 0.26)), 0.45).save(plate)
        inputs += ["-i", str(plate)]
        plate_idx = n_bg

        music = _music_path(cfg, "pantheon_outro_music.mp3") if with_music else None
        if music:
            inputs += ["-i", str(music)]
        else:
            inputs += ["-f", "lavfi", "-t", f"{duration}",
                       "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]

        sub = Path(getattr(cfg, "subtitle_font", "") or "")
        font_arg = ""
        if sub.exists():
            esc = str(sub).replace("\\", "/").replace(":", "\\:")
            font_arg = f":fontfile='{esc}'"

        # `part` is the HISTORICAL source folder, not the output number -- the
        # old outro stamped it and so every video credited the wrong Part. The
        # caller now passes the label it wants; nothing is derived here.
        lines = [("QUAKE TRIBUTE", 0.52, int(h * 0.055), 2.0)]
        if label:
            lines.append((label, 0.60, int(h * 0.040), 3.0))
        for i, f in enumerate((facts or [])[:3]):
            lines.append((f, 0.68 + i * 0.055, int(h * 0.026), 3.8 + i * 0.5))
        lines.append(("By Tr4sH", 0.68 + len((facts or [])[:3]) * 0.055 + 0.055,
                      int(h * 0.032), 5.6))
        credits = lines
        draws = ",".join(
            f"drawtext=text='{txt}'{font_arg}:fontsize={fs}:fontcolor=0xe8b923:"
            f"x=(w-text_w)/2:y=h*{yf}:"
            f"alpha='if(lt(t,{st}),0,min((t-{st})/1.2,1))'"
            for txt, yf, fs, st in credits
        )

        filt = (
            bg
            + f";[{plate_idx}:v]format=rgba[mk];"
            f"[bg][mk]overlay=(W-w)/2:H*0.14:format=auto[withmark];"
            f"[withmark]{draws},format=yuv420p[vout]"
        )
        cmd = [str(cfg.ffmpeg_bin), "-y", "-v", "error"] + inputs
        cmd += ["-filter_complex", filt, "-map", "[vout]"]
        vol = getattr(cfg, "music_volume", 0.20)
        cmd += ["-map", f"{plate_idx + 1}:a", "-c:a", "aac", "-b:a", "192k"]
        if music:
            cmd += ["-af", f"volume={vol}"]
        cmd += ["-t", f"{duration}", "-c:v", "libx264", "-crf", "16",
                "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(fps),
                "-movflags", "+faststart", str(out)]

        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"outro ffmpeg failed:\n{r.stderr[-1500:]}")
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    ap.add_argument("--what", choices=["intro", "outro", "both"], default="both")
    ap.add_argument("--out-dir", default="engine/assets")
    a = ap.parse_args()

    cfg = Config()
    od = Path(a.out_dir)
    if a.what in ("intro", "both"):
        print(f"[intro] {render_intro(a.part, od / f'pantheon_intro_part{a.part:02d}.mp4', cfg)}")
    if a.what in ("outro", "both"):
        print(f"[outro] {render_outro(a.part, od / f'pantheon_outro_part{a.part:02d}.mp4', cfg)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
