"""Assemble EDITORIAL_CANARY_V3_IMPACT from two captures (directive 7-11, 17-25).

Inputs are two READY director captures of the same frag and window:

    fpv     FPV_GAMEPLAY   the player's own view, gameplay HUD
    insert  CINEMATIC_CLEAN the PROJECTILE ride, zero HUD

Both share the edit clock (guard already trimmed by the preview path), so
T = impact is the same file time in each. The ImpactClock says which
camera owns which span and where the slow treatment sits; this module only
executes that, and prints every cut point it chose so the report can quote
them rather than describe them.

WHY THE SLOW IS A POST TREATMENT HERE. The preview path deliberately does
not render TimeMap rates (director_preview: "slow motion is the single
most expensive knob"). The canary applies the T-500..T-150 slow with
setpts/atempo on the FPV master, which is the same time relationship the
TimeMap would express -- gameplay events keep their order and spacing,
only the playback rate of that span changes.

MUSIC A/B/C reuse one visual master with -c:v copy. Loudness is measured
after the fact rather than normalised in advance: if the three already
land within the fairness band, adding a normaliser is dead code.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from creative_suite.engine import director_preview as dp
from creative_suite.engine import impact_canary as ic
from creative_suite.engine.scene_recipe import MusicPlacement
from creative_suite.engine import sync_contract as sc

MUSIC_LIBRARY = dp.REPO_ROOT / "engine" / "music" / "library"
REVIEW_DIR = dp.REPO_ROOT / "output" / "demo_v2" / "review"

# The audio chain proven on the micro-sequence: static trim + true-peak
# ceiling. Static because P1-G forbids level-following. 0.66 measured
# -1.9 dBTP post-AAC on a 31 s programme; the canary is re-measured anyway.
MIX_TRIM = 0.62
TP_CEILING = 0.66
# Review size target (directive 24): short, 720p60, comfortably transferable.
CRF = "22"
PRESET = "medium"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])
    return r


@dataclass(frozen=True)
class CanaryCut:
    """Every file-time cut the assembly made, in seconds."""
    T_s: float
    scene_in_s: float
    insert_in_s: float | None
    insert_out_s: float | None
    slow_in_s: float
    slow_out_s: float
    scene_out_s: float
    slow_rate: Fraction

    @property
    def edit_duration_s(self) -> float:
        """Programme length after the slow span is stretched."""
        base = self.scene_out_s - self.scene_in_s
        stretch = (self.slow_out_s - self.slow_in_s) * (1 / float(self.slow_rate) - 1)
        return round(base + stretch, 3)

    @property
    def impact_edit_s(self) -> float:
        """Where T lands in the DELIVERED file, after the slow stretch."""
        pre = self.T_s - self.scene_in_s
        stretch = (self.slow_out_s - self.slow_in_s) * (1 / float(self.slow_rate) - 1)
        return round(pre + stretch, 3)

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["slow_rate"] = str(self.slow_rate)
        d["edit_duration_s"] = self.edit_duration_s
        d["impact_edit_s"] = self.impact_edit_s
        return d


def cuts_for(clock: ic.ImpactClock, T_ms: float) -> CanaryCut:
    T = T_ms / 1000.0
    rel = lambda us: T + us / 1e6
    return CanaryCut(
        T_s=T, scene_in_s=rel(clock.scene_start_us),
        insert_in_s=(rel(clock.insert_start_us) if clock.has_insert else None),
        insert_out_s=((rel(clock.fpv_return_us) if clock.return_to_fpv
                       else rel(clock.tail_us)) if clock.has_insert else None),
        slow_in_s=rel(clock.slow_span_us[0]), slow_out_s=rel(clock.slow_span_us[1]),
        scene_out_s=rel(clock.tail_us), slow_rate=clock.slow_rate)


def _atempo_chain(rate: float) -> str:
    """ffmpeg's atempo is bounded to [0.5, 100]; slower rates are a chain.

    A beat-locked rate is often below 0.5 (7 beats at 161.5 BPM is 0.433),
    so 0.433 becomes atempo=0.5,atempo=0.866. Each stage is tempo-only, so
    pitch is untouched and the product is exact to float precision.
    """
    parts = []
    r = float(rate)
    while r < 0.5:
        parts.append(",atempo=0.5")
        r /= 0.5
    parts.append(f",atempo={r:.6f}")
    return "".join(parts)


def build_visual_master(fpv_mp4: Path, insert_mp4: Path | None,
                        cut: CanaryCut, dst: Path) -> Path:
    """FPV lead -> [insert] -> FPV (slowed T-500..T-150) -> FPV tail.

    Video and game audio are cut together from the same sources so the
    game transients keep their relationship to the frames. The slow span
    uses setpts on video and atempo on audio -- the same rate on both.
    """
    rate = float(cut.slow_rate)
    f = []
    n_in = 0
    # segment list: (source index, in, out, rate)
    if cut.insert_in_s is not None:
        segs = [(0, cut.scene_in_s, cut.insert_in_s, 1.0),
                (1, cut.insert_in_s, cut.insert_out_s, 1.0),
                (0, cut.insert_out_s, cut.scene_out_s, 1.0)]
    else:
        segs = [(0, cut.scene_in_s, cut.scene_out_s, 1.0)]
    # split any segment that overlaps the slow span so the slow is its own piece
    pieces = []
    for src, a, b, _ in segs:
        bounds = sorted({a, b, max(a, min(b, cut.slow_in_s)), max(a, min(b, cut.slow_out_s))})
        for x, y in zip(bounds, bounds[1:]):
            if y - x <= 1e-6:
                continue
            slow = (x >= cut.slow_in_s - 1e-6) and (y <= cut.slow_out_s + 1e-6)
            pieces.append((src, x, y, rate if slow else 1.0))
    labels = []
    for i, (src, a, b, r) in enumerate(pieces):
        vf = f"[{src}:v]trim={a:.6f}:{b:.6f},setpts=(PTS-STARTPTS)/{r}"
        af = f"[{src}:a]atrim={a:.6f}:{b:.6f},asetpts=PTS-STARTPTS"
        if r != 1.0:
            af += _atempo_chain(r)
        f.append(f"{vf},fps=60,scale=1280:720,setsar=1[v{i}];")
        f.append(f"{af},aresample=48000[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    f.append("".join(labels) + f"concat=n={len(pieces)}:v=1:a=1[v][a]")
    cmd = [str(dp.FFMPEG), "-y", "-v", "error", "-i", str(fpv_mp4)]
    if insert_mp4 is not None:
        cmd += ["-i", str(insert_mp4)]
    cmd += ["-filter_complex", "".join(f), "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", PRESET, "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", "60",
            "-c:a", "pcm_s16le", "-ar", "48000", str(dst)]
    _run(cmd)
    return dst


def music_excerpt_lufs(track_path: Path, placement: MusicPlacement,
                       duration_s: float) -> float | None:
    """Integrated loudness of exactly the excerpt a variant will use."""
    ss = placement.source_start_us / 1e6
    o = subprocess.run([str(dp.FFMPEG), "-i", str(track_path), "-af",
                        f"atrim={ss:.6f}:{ss + duration_s:.6f},asetpts=PTS-STARTPTS,"
                        f"ebur128", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = re.search(r"I:\s*(-?[\d.]+) LUFS", o.split("Summary:")[-1])
    return float(m.group(1)) if m else None


def mux_music(master: Path, track_path: Path, placement: MusicPlacement,
              duration_s: float, dst: Path, *,
              music_gain_db: float = 0.0) -> Path:
    """Music under the visual master, -c:v copy, static mix bus.

    ``music_gain_db`` is the A/B/C fairness trim (directive 23): a STATIC
    per-variant gain on the music stem only, so the game audio -- identical
    across variants -- stays identical and "louder" cannot read as "better".
    """
    ss = placement.source_start_us / 1e6
    flt = (f"[1:a]atrim={ss:.6f}:{ss + duration_s:.6f},asetpts=PTS-STARTPTS,"
           f"volume={dp.MUSIC_VOLUME},volume={music_gain_db:.2f}dB,"
           f"afade=t=in:st=0:d=0.15,"
           f"afade=t=out:st={max(0.0, duration_s - 0.60):.3f}:d=0.60[m];"
           f"[0:a]volume={dp.GAME_AUDIO_VOLUME}[g];"
           f"[g][m]amix=inputs=2:duration=first:normalize=0,"
           f"volume={MIX_TRIM},alimiter=limit={TP_CEILING}:level=disabled[out]")
    _run([str(dp.FFMPEG), "-y", "-v", "error", "-i", str(master),
          "-i", str(track_path), "-filter_complex", flt,
          "-map", "0:v", "-map", "[out]", "-c:v", "copy",
          "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
          "-movflags", "+faststart", "-t", f"{duration_s:.3f}", str(dst)])
    return dst


def deliver(master: Path, dst: Path) -> Path:
    """Delivery encode of the master (used for the music-free control)."""
    _run([str(dp.FFMPEG), "-y", "-v", "error", "-i", str(master),
          "-c:v", "libx264", "-preset", PRESET, "-crf", CRF,
          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
          "-movflags", "+faststart", str(dst)])
    return dst


def loudness(path: Path) -> dict[str, float | None]:
    o = subprocess.run([str(dp.FFMPEG), "-i", str(path), "-af",
                        "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    s = o.split("Summary:")[-1]
    g = lambda pat: (float(m.group(1)) if (m := re.search(pat, s)) else None)
    return {"lufs": g(r"I:\s*(-?[\d.]+) LUFS"),
            "lra": g(r"LRA:\s*(-?[\d.]+) LU"),
            "true_peak_dbtp": g(r"Peak:\s*(-?[\d.]+) dBFS")}


def decode_ok(path: Path) -> bool:
    r = subprocess.run([str(dp.FFMPEG), "-v", "error", "-xerror", "-i",
                        str(path), "-f", "null", "-"],
                       capture_output=True, text=True)
    return r.returncode == 0 and not r.stderr.strip()


def placement_on_impact(track_hash: str, accent_music_us: int,
                        impact_edit_us: int, duration_us: int) -> MusicPlacement:
    """Place so the chosen transient lands exactly on the delivered impact."""
    src = accent_music_us - impact_edit_us
    return MusicPlacement(track_id=track_hash, source_start_us=src,
                          program_edit_start_us=0,
                          source_end_us=src + duration_us)
