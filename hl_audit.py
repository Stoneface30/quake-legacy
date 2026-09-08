"""Acceptance audit for the highlight episodes.

Two gates, both hard:

  COVERAGE  every selected T1/T2 source clip appears exactly once across all
            episodes -- remaining == 0, duplicates == 0, missing == 0.
  AUDIO     every shipped episode measures at or below -1.0 dBTP true peak.
            Measured on the ENCODED FILE with ebur128, not predicted from the
            filter graph, because AAC can nudge peaks up after loudnorm.

    python hl_audit.py            # audit everything under output/
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from creative_suite.engine import highlight_ledger as L  # noqa: E402
from creative_suite.engine.config import Config  # noqa: E402
from creative_suite.engine.render_highlight import collect_frags  # noqa: E402

FFPROBE = ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffprobe.exe"
FFMPEG = ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
TP_CEILING = -1.0          # dBTP. Above this the episode is rejected.


def duration(path: Path) -> float:
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def true_peak(path: Path) -> float | None:
    """Measured true peak of the encoded file, in dBTP."""
    r = subprocess.run([str(FFMPEG), "-v", "info", "-i", str(path),
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    peaks = re.findall(r"Peak:\s*(-?\d+\.?\d*)", r.stderr)
    return max(float(p) for p in peaks) if peaks else None


def main() -> int:
    cfg = Config()
    vids = sorted(glob.glob(str(ROOT / "output" / "Part*_highlight*.mp4")))

    print("=" * 74)
    print("EPISODES")
    print("=" * 74)
    print(f"  {'file':34} {'length':>8} {'true peak':>11}  gate")
    bad_audio = []
    lens = []
    for v in vids:
        p = Path(v)
        d = duration(p)
        tp = true_peak(p)
        lens.append(d)
        if tp is None:
            gate = "NO AUDIO"
            bad_audio.append(p.name)
        elif tp > TP_CEILING:
            gate = "REJECT"
            bad_audio.append(p.name)
        else:
            gate = "ok"
        tps = "n/a" if tp is None else f"{tp:.2f} dBTP"
        print(f"  {p.name:34} {d/60:7.2f}m {tps:>11}  {gate}")
    if lens:
        print(f"\n  {len(lens)} episodes, mean {sum(lens)/len(lens)/60:.2f} min "
              f"(target 5.0), total {sum(lens)/3600:.2f} h")

    print("\n" + "=" * 74)
    print("COVERAGE  (every T1/T2 clip exactly once)")
    print("=" * 74)
    gt1 = gt2 = gused = gtot = gdup = 0
    for part in range(1, 13):
        frags = collect_frags(part, cfg)
        rem = L.remaining(part, frags)
        t1 = sum(1 for f in rem if f.tier == "T1")
        t2 = sum(1 for f in rem if f.tier == "T2")
        cov = L.coverage(part, frags)
        # A real duplicate check: load_used() returns a SET, which would hide
        # the very thing we are testing for. Count each key across episodes.
        seen: dict[str, int] = {}
        for ep in L._read(part).get("episodes", []):
            for k in ep.get("clips", []):
                seen[k] = seen.get(k, 0) + 1
        dup = sum(n - 1 for n in seen.values() if n > 1)
        gt1 += t1; gt2 += t2; gused += cov.used; gtot += cov.total; gdup += dup
        flag = "OK" if (t1 + t2 + dup) == 0 else f"{t1} T1 + {t2} T2 left"
        print(f"  Part {part:2d}: {cov.used:3d}/{cov.total:3d} burned  "
              f"{cov.episodes} ep  dup {dup}  {flag}")
    print(f"\n  TOTAL {gused}/{gtot} burned  |  remaining {gt1} T1 + {gt2} T2  "
          f"|  duplicates {gdup}")

    print("\n" + "=" * 74)
    ok = (gt1 + gt2 == 0) and gdup == 0 and not bad_audio and vids
    if bad_audio:
        print(f"AUDIO GATE FAILED on {len(bad_audio)} episode(s): "
              f"{', '.join(bad_audio[:5])}")
    if gt1 + gt2:
        print(f"COVERAGE INCOMPLETE: {gt1 + gt2} clips never shipped")
    if gdup:
        print(f"COVERAGE BROKEN: {gdup} clips shipped more than once")
    print("ACCEPTANCE: " + ("PASS" if ok else "NOT YET"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
