"""Lay a DialogueCue track against a filmed shot, on the scenario's clock.

ONE CLOCK, NO NUDGING. A cue's `start_t` is scenario seconds; the shot knows
which scenario second it began on. The delay is arithmetic, so a line cannot
drift against the picture and there is no per-line offset to hand-tune.

STEMS STAY SEPARATE. Dialogue is rendered as its own track and only meets the
picture at the final mux, so the mix can be re-balanced without refilming.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

FFMPEG = Path("G:/QUAKE_LEGACY/creative_suite/tools/ffmpeg/ffmpeg.exe")
SR = 48000


def build_dialogue_stem(dialogue_json: Path, dest: Path, *, shot_start_s: float,
                        duration_s: float) -> Path:
    """Render every cue, placed and panned, into one stereo stem."""
    from engine.pantheon.voice import PROFILES

    cues = json.loads(dialogue_json.read_text(encoding="utf-8"))["cues"]
    live = [c for c in cues
            if shot_start_s <= c["start_t"] < shot_start_s + duration_s]
    if not live:
        raise ValueError(f"no cue lands inside {shot_start_s}..+{duration_s}s")

    ins, chains, labels = [], [], []
    for i, c in enumerate(live):
        prof = PROFILES[c["profile"]]
        delay_ms = int(round((c["start_t"] - shot_start_s) * 1000))
        ins += ["-i", str(Path(c["audio_path"]).resolve())]
        chains.append(
            f"[{i}:a]aresample={SR},"
            f"{prof.ffmpeg_chain(pan=c['pan'], distance=c['distance'])},"
            f"adelay={delay_ms}|{delay_ms}[d{i}]")
        labels.append(f"[d{i}]")
    graph = (";".join(chains) + ";" + "".join(labels)
             + f"amix=inputs={len(live)}:normalize=0:duration=longest,"
               f"alimiter=limit=0.95,apad[out]")

    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(FFMPEG), "-v", "error", "-y", *ins,
                    "-filter_complex", graph, "-map", "[out]",
                    "-t", f"{duration_s:.3f}", "-ar", str(SR),
                    "-c:a", "pcm_s16le", str(dest)],
                   check=True, timeout=300)
    return dest


def mux(video: Path, dialogue: Path, dest: Path, *, crf: int = 17) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(FFMPEG), "-v", "error", "-y", "-i", str(video),
                    "-i", str(dialogue), "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", str(dest)], check=True, timeout=1800)
    return dest
