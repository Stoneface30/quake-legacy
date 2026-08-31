"""Re-mix a finished Part at a different game/music balance, without re-rendering.

The finished mp4 carries one stream where game and music are already summed and
loudnorm'd, so it cannot be un-mixed. What makes a cheap remix possible is the
preserved GAME STEM: `D:\\QUAKE_LEGACY_OUTPUT\\stems\\PartNN_game.flac`, saved
from body.mov before the work directory is reclaimed.

Given that stem, a remix is: take the finished video (stream copy, untouched),
take the game stem, re-fetch the same music the manifest recorded, mix at the
new gains, and run the same safety chain. Seconds instead of half an hour, and
the picture is bit-identical to what was reviewed.

Parts rendered before stem preservation existed have no stem. Those genuinely
need a re-render; this tool reports them rather than pretending otherwise.

    python remix_audio.py --parts 46 47 --game 2.90
    python remix_audio.py --all --game 2.90 --music 1.24
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "output"
MANIFESTS = OUT / "_series_manifests"
STEMS = Path(os.environ.get("QL_STEMS_DIR", r"D:\QUAKE_LEGACY_OUTPUT\stems"))
FFMPEG = ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"

TP_CEILING_DBTP = -1.0
TARGET_LUFS = -14.0
TARGET_TP = -2.0
TP_LIMIT_LINEAR = 0.794


def audio_qa(path: Path):
    r = subprocess.run([str(FFMPEG), "-v", "info", "-i", str(path),
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    t = r.stderr
    peaks = [float(x) for x in re.findall(r"Peak:\s+(-?\d+\.?\d*)", t)]
    lu = re.findall(r"I:\s+(-?\d+\.?\d*)\s+LUFS", t)
    lra = re.findall(r"LRA:\s+(-?\d+\.?\d*)\s+LU", t)
    tp = max(peaks) if peaks else None
    return ((float(lu[-1]) if lu else None), (float(lra[-1]) if lra else None),
            tp, tp is not None and tp <= TP_CEILING_DBTP)


def remix(part: int, game: float, music: float, suffix: str) -> bool:
    man = MANIFESTS / "Part{:02d}.json".format(part)
    if not man.exists():
        print("  Part{:02d}: no manifest".format(part))
        return False
    rec = json.loads(man.read_text(encoding="utf-8"))
    src = Path(rec["output_path"])
    stem = STEMS / "Part{:02d}_game.flac".format(part)
    if not src.exists():
        print("  Part{:02d}: output missing".format(part))
        return False
    if not stem.exists():
        print("  Part{:02d}: NO GAME STEM -- rendered before stem preservation; "
              "needs a full re-render".format(part))
        return False

    tracks = [Path(m["path"]) for m in (rec.get("music") or [])
              if Path(m["path"]).exists()]
    if not tracks:
        print("  Part{:02d}: music files unavailable".format(part))
        return False

    dur = rec["duration_s"]
    inputs = ["-i", str(src), "-i", str(stem)]
    for t in tracks:
        inputs += ["-i", str(t)]

    # music chain: crossfade the tracks, fade the ends, then sum with the game
    n = len(tracks)
    parts_f = []
    for i in range(n):
        parts_f.append("[{}:a]aresample=48000[m{}];".format(i + 2, i))
    if n == 1:
        chain = "[m0]anull[mraw];"
    else:
        cur = "[m0]"
        for i in range(1, n):
            chain_lbl = "[mx{}]".format(i)
            parts_f.append("{}[m{}]acrossfade=d=6.0:c1=tri:c2=tri{};"
                           .format(cur, i, chain_lbl))
            cur = chain_lbl
        chain = "{}anull[mraw];".format(cur)

    filt = ("[1:a]volume={:.3f}[g];".format(game)
            + "".join(parts_f) + chain
            + "[mraw]volume={:.3f},afade=t=in:st=0:d=1.0,"
              "afade=t=out:st={:.3f}:d=4.0[m];".format(music, max(0.0, dur - 4.0))
            + "[g][m]amix=inputs=2:duration=first:dropout_transition=0:"
              "normalize=0[mixed];"
            + "[mixed]loudnorm=I={}:TP={}:LRA=11,"
              "aresample=192000,alimiter=limit={}:level=false,"
              "aresample=48000[aout]".format(TARGET_LUFS, TARGET_TP,
                                             TP_LIMIT_LINEAR))

    dst = src.with_name("Part{:02d}{}.mp4".format(part, suffix))
    cmd = ([str(FFMPEG), "-y", "-v", "error"] + inputs
           + ["-filter_complex", filt, "-map", "0:v", "-map", "[aout]",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
              "-t", "{:.3f}".format(dur), "-movflags", "+faststart", str(dst)])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not dst.exists():
        print("  Part{:02d}: remix failed: {}".format(part, r.stderr[-200:]))
        return False

    lufs, lra, tp, ok = audio_qa(dst)
    # same measured, iterative correction the series uses
    tries = 0
    while not ok and tp is not None and tries < 3:
        tries += 1
        gain = TP_CEILING_DBTP - tp - 1.2
        tmp = dst.with_name(dst.stem + "_fix.mp4")
        subprocess.run([str(FFMPEG), "-y", "-v", "error", "-i", str(dst),
                        "-af", "volume={:.2f}dB".format(gain), "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", str(tmp)],
                       capture_output=True, text=True)
        if tmp.exists():
            os.replace(tmp, dst)
            lufs, lra, tp, ok = audio_qa(dst)

    print("  Part{:02d}: {} | {} LUFS | {} -> {}".format(
        part, "{:.2f} dBTP".format(tp) if tp is not None else "n/a",
        "{:.1f}".format(lufs) if lufs is not None else "n/a",
        "PASS" if ok else "FAIL", dst.name))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", type=int, nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--game", type=float, default=2.90,
                    help="game gain (series default 1.45; 2.90 is 2x)")
    ap.add_argument("--music", type=float, default=1.24)
    ap.add_argument("--suffix", default="_gx2")
    a = ap.parse_args()

    parts = a.parts or []
    if a.all:
        parts = sorted(int(p.stem[4:6]) for p in MANIFESTS.glob("Part*.json")
                       if p.stem[4:6].isdigit())
    if not parts:
        print("nothing to do -- pass --parts or --all")
        return 1
    print("remix: game {:.2f} (was 1.45), music {:.2f}".format(a.game, a.music))
    ok = sum(1 for p in parts if remix(p, a.game, a.music, a.suffix))
    print("\n{}/{} remixed".format(ok, len(parts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
