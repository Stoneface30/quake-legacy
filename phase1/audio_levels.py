"""
Objective audio-level ship gate per Rule P1-G v4 / v5.

Uses ffmpeg's `ebur128` filter to measure integrated LUFS on the music and game
stems extracted from (or feeding) the final render. The render is only shipped
if music integrated loudness is >= 12 LU below game (peak) loudness.

Public API:
    measure_lufs(wav_path) -> float
    extract_music_stem(rendered_mp4, music_src, out_wav) -> Path
    extract_game_stem(rendered_mp4, clip_list, out_wav) -> Path
    measure_music_vs_game(music_stem, game_stem) -> dict
    write_levels_json(part, data, out_dir=None) -> Path
    run_ship_gate(part, out_dir=None) -> bool
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

from phase1.config import Config


LUFS_RE = re.compile(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS")
_CFG = Config()


def _ffmpeg() -> str:
    return str(_CFG.ffmpeg_bin)


def measure_lufs(wav_path: Path | str) -> float:
    """Integrated loudness in LUFS. Raises if ebur128 produces no reading."""
    p = Path(wav_path)
    if not p.exists():
        raise FileNotFoundError(p)
    proc = subprocess.run(
        [
            _ffmpeg(),
            "-nostats",
            "-hide_banner",
            "-i",
            str(p),
            "-filter_complex",
            "ebur128=peak=true",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # ebur128 prints all measurements; last "I:" entry is the final integrated value.
    matches = LUFS_RE.findall(proc.stderr)
    if not matches:
        raise RuntimeError(f"ebur128 produced no LUFS reading for {p}")
    return float(matches[-1])


def extract_music_stem(
    rendered_mp4: Path | str,
    music_src: Path | str,
    out_wav: Path | str,
    music_volume: float = 1.0,
) -> Path:
    """Write a WAV stem of the music track AS IT SITS IN THE MIX.

    Copy-converts `music_src` to PCM WAV while applying `music_volume` (the
    same scalar the renderer mixes in — default 0.20 per Config). Measuring
    the raw source ignores that scaling and produces a +14 dB error
    (20·log10(0.20) ≈ -13.98 dB), which is why early ship-gate readings
    looked like "music 22 LU LOUDER than game" even when the rendered mix
    was fine.

    Caller MUST pass `cfg.music_volume`. Sidechain ducking (~6 dB on game
    events) is NOT modeled here — this over-estimates music loudness
    slightly, which is a conservative direction for the ship gate.
    """
    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        _ffmpeg(),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(music_src),
        "-ac",
        "2",
        "-ar",
        "48000",
    ]
    if music_volume != 1.0:
        cmd += ["-af", f"volume={music_volume}"]
    cmd += ["-c:a", "pcm_s16le", str(out)]
    subprocess.run(cmd, check=True)
    return out


def extract_game_stem(
    rendered_mp4: Path | str,
    clip_list: Iterable[Path | str],
    out_wav: Path | str,
) -> Path:
    """Concatenate the game audio tracks from the listed clips into a WAV.

    This isolates the game-only side of the mix so ebur128 can measure game
    loudness independent of music.
    """
    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    clips = [Path(c) for c in clip_list]
    if not clips:
        raise ValueError("extract_game_stem: empty clip_list")

    list_file = out.with_suffix(".concat.txt")
    # ffmpeg concat demuxer requires files to have identical params; we render
    # each clip's audio to a temp WAV first, then concat.
    tmp_dir = out.with_suffix(".tmp")
    tmp_dir.mkdir(exist_ok=True)
    try:
        wav_entries: list[Path] = []
        for i, clip in enumerate(clips):
            tmp_wav = tmp_dir / f"stem_{i:04d}.wav"
            subprocess.run(
                [
                    _ffmpeg(),
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(clip),
                    "-vn",
                    "-ac",
                    "2",
                    "-ar",
                    "48000",
                    "-c:a",
                    "pcm_s16le",
                    str(tmp_wav),
                ],
                check=True,
            )
            wav_entries.append(tmp_wav)
        lines = [f"file '{p.as_posix()}'\n" for p in wav_entries]
        list_file.write_text("".join(lines))
        subprocess.run(
            [
                _ffmpeg(),
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-c:a",
                "pcm_s16le",
                str(out),
            ],
            check=True,
        )
    finally:
        if list_file.exists():
            list_file.unlink()
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)
    return out


def measure_music_vs_game(
    music_stem: Path | str,
    game_stem: Path | str,
    gate_lu: float | None = None,
) -> dict:
    """Measure both stems + return the ship-gate verdict."""
    if gate_lu is None:
        gate_lu = float(getattr(_CFG, "music_level_gate_lu", 12.0))
    m = measure_lufs(music_stem)
    g = measure_lufs(game_stem)
    delta = g - m
    return {
        "music_lufs": m,
        "game_lufs": g,
        "delta": delta,
        "gate_lu": gate_lu,
        "pass": bool(delta >= gate_lu),
    }


def write_levels_json(
    part: int,
    data: dict,
    out_dir: Path | str | None = None,
) -> Path:
    out_dir = Path(out_dir) if out_dir else _CFG.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"part{part:02d}_levels.json"
    out.write_text(json.dumps(data, indent=2))
    return out


def run_ship_gate(part: int, out_dir: Path | str | None = None) -> bool:
    """Read `output/partNN_levels.json` and return pass/fail.

    Raises if the file is missing (measurement hasn't been run).
    """
    out_dir = Path(out_dir) if out_dir else _CFG.output_dir
    p = out_dir / f"part{part:02d}_levels.json"
    if not p.exists():
        raise FileNotFoundError(f"levels JSON missing for part {part}: {p}")
    data = json.loads(p.read_text())
    return bool(data.get("pass", False))


__all__ = [
    "measure_lufs",
    "extract_music_stem",
    "extract_game_stem",
    "measure_music_vs_game",
    "write_levels_json",
    "run_ship_gate",
]


if __name__ == "__main__":  # pragma: no cover
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--music", required=True)
    ap.add_argument("--game", required=True)
    ap.add_argument("--part", type=int, required=True)
    args = ap.parse_args()
    data = measure_music_vs_game(args.music, args.game)
    path = write_levels_json(args.part, data)
    print(f"wrote {path}")
    print(json.dumps(data, indent=2))
