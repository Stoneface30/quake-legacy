"""Does the active V2 capture path deliver 60 unique frames, or 30 doubled?

The distinction matters because every effect envelope we are about to measure
is quantised by whatever the real cadence is. A duplicated pair looks like
two frames to the encoder and like one frame to the eye.

    TRUE_60_UNIQUE        A B C D E F      adjacent frames all differ
    DUPLICATED_30_TO_60   A A B B C C      every other difference is ~zero

Read straight off the delivered file, with no reference to any other
pipeline. A static stretch is measured too: frames that are identical
because nothing moved are not evidence of duplication, and separating the
two is the whole point of the control.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

FFMPEG = Path("G:/QUAKE_LEGACY/creative_suite/tools/ffmpeg/ffmpeg.exe")
WORK = Path("C:/Users/STONEF~1/AppData/Local/Temp/claude/G--QUAKE-LEGACY/"
            "d45475ae-45f3-46d3-a1c3-d4282ba81b1e/scratchpad/cadence")
# The committed measurement. Written ONLY with --write-reference, so a
# diff here is always a decision and never a side effect of a run.
REFERENCE = (Path(__file__).resolve().parents[3] / "docs" / "reference"
             / "v2_frame_cadence.json")


def thumbs(video: Path, out_dir: Path, count: int, start: int = 0):
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.pgm"):
        old.unlink()
    sel = f"select='gte(n\\,{start})'"
    r = subprocess.run(
        [str(FFMPEG), "-y", "-v", "error", "-i", str(video),
         "-vf", f"{sel},scale=64:36,format=gray", "-vsync", "0",
         "-frames:v", str(count), str(out_dir / "f%05d.pgm")],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-1200:])
    out = []
    for p in sorted(out_dir.glob("*.pgm")):
        raw = p.read_bytes()
        i = raw.index(bytes([50, 53, 53, 10])) + 4
        out.append(np.frombuffer(raw[i:], dtype=np.uint8).astype(np.int16))
    return out


def cadence(fp, label):
    """Classify from the pattern of adjacent differences."""
    d = [float(np.abs(a - b).mean()) for a, b in zip(fp, fp[1:])]
    if not d:
        return {"label": label, "verdict": "NO_DATA"}
    even = d[0::2]       # differences at even indices
    odd = d[1::2]
    near_zero = [x for x in d if x < 0.05]
    moving = [x for x in d if x >= 0.05]
    out = {
        "label": label, "frames": len(fp), "diffs": len(d),
        "median_diff": round(float(np.median(d)), 3),
        "near_zero_pairs": len(near_zero),
        "near_zero_share": round(len(near_zero) / len(d), 3),
        "median_even": round(float(np.median(even)), 3) if even else None,
        "median_odd": round(float(np.median(odd)), 3) if odd else None,
    }
    if not moving:
        out["verdict"] = "STATIC_INTERVAL"
        out["meaning"] = ("nothing moved here, so identical frames say "
                          "nothing about cadence")
        return out
    # Duplication shows as an alternating pattern: one of the two phases is
    # near zero while the other carries all the motion.
    lo = min(out["median_even"] or 0.0, out["median_odd"] or 0.0)
    hi = max(out["median_even"] or 0.0, out["median_odd"] or 0.0)
    if lo < 0.05 and hi > 0.5:
        out["verdict"] = "DUPLICATED_30_TO_60"
        out["meaning"] = (f"one phase of adjacent pairs is flat ({lo}) while "
                          f"the other carries the motion ({hi}): every frame "
                          f"is delivered twice")
    elif out["near_zero_share"] > 0.4:
        out["verdict"] = "MOSTLY_REPEATED"
        out["meaning"] = (f"{out['near_zero_share']:.0%} of adjacent pairs are "
                          f"flat without a clean alternating pattern")
    else:
        out["verdict"] = "TRUE_60_UNIQUE"
        out["meaning"] = (f"adjacent frames differ throughout (median "
                          f"{out['median_diff']}), with no alternating flat "
                          f"phase")
    return out


def main(write_reference: bool = False):
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "G:/QUAKE_LEGACY/output/demo_v2/_bench/clean_pov.avi")
    print(f"file: {target.name}")
    probe = subprocess.run(
        [str(FFMPEG).replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error",
         "-select_streams", "v:0", "-show_entries",
         "stream=r_frame_rate,nb_frames,codec_name", "-of", "csv=p=0",
         str(target)], capture_output=True, text=True).stdout.strip()
    print(f"container: {probe}")

    # Scan for the most and least active stretches, then judge each.
    scan = thumbs(target, WORK / "scan", 480)
    diffs = [float(np.abs(a - b).mean()) for a, b in zip(scan, scan[1:])]
    win = 120
    sums = [sum(diffs[i:i + win]) for i in range(0, max(1, len(diffs) - win))]
    busiest = int(np.argmax(sums))
    quietest = int(np.argmin(sums))
    print(f"busiest window at frame {busiest}, quietest at {quietest}")

    results = []
    for start, label in ((busiest, "moving"), (quietest, "static control")):
        fp = thumbs(target, WORK / f"w{start}", win, start)
        r = cadence(fp, label)
        r["start_frame"] = start
        results.append(r)
        print(f"\n  {label.upper()} (from frame {start})")
        print(f"    median adjacent difference   {r['median_diff']}")
        print(f"    even/odd phase medians       {r['median_even']} / "
              f"{r['median_odd']}")
        print(f"    near-identical adjacent pairs {r['near_zero_pairs']}/"
              f"{r['diffs']}  ({r['near_zero_share']:.0%})")
        print(f"    verdict                      {r['verdict']}")
        print(f"    {r.get('meaning','')}")

    verdict = next((r["verdict"] for r in results if r["label"] == "moving"),
                   "UNKNOWN")
    out = {"file": target.name, "container": probe, "windows": results,
           "cadence": verdict}
    # Committed reference data is overwritten only on purpose.
    #
    # This used to write into docs/reference on every run, against
    # whichever AVI it happened to find, which makes a tracked
    # measurement disagree with itself for reasons nobody can
    # reconstruct. The default is scratch; --write-reference is the
    # explicit act of re-recording the truth.
    dest = REFERENCE if write_reference else WORK / "v2_frame_cadence.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\n  CADENCE OF THE ACTIVE V2 PATH: {verdict}")
    print(f"  written: {dest}")
    if not write_reference:
        print("  (tracked reference left untouched; pass "
              "--write-reference to re-record it)")
    return out


if __name__ == "__main__":
    import sys as _sys
    main(write_reference="--write-reference" in _sys.argv)
