"""Build the authoritative AVI master queue for the continuous PartNN series.

The historical folders `T1/PartN` and `T2/PartN` are ORDERING METADATA, not
output structure. This flattens them into one continuous queue that the series
walks straight through: when historical Part 1 runs out mid-video, the same
output Part simply continues into historical Part 2. There are no episodes.

Ordering within the queue interleaves the two tiers so a video is not five
minutes of T1 followed by five minutes of T2 -- T1 leads, T2 fills, which is
the balance the reviewed archive already uses.

One source is damaged: `Demo (100) - 3.avi` lost its 28 KB RIFF header. A
header graft recovered 9.97 s of clean MJPEG (the lost payload is 15,688 bytes,
about 3% of a single frame, and the duration sits inside the 8-14 s range of its
batch siblings), so the RECOVERED file is queued in its place and the original
is recorded as the substitution reason.

    python avi_queue.py            # writes output/avi_master_queue.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent
CLIP_ROOT = ROOT / "QUAKE VIDEO"
FFPROBE = ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffprobe.exe"

RECOVERED = {
    (ROOT / "QUAKE VIDEO" / "T2" / "Part3" / "Demo (100) - 3" /
     "Demo (100) - 3.avi").resolve():
        ROOT / "SOURCE_EXCEPTIONS" / "recovered" / "Demo (100) - 3 [RECOVERED].avi",
}

# The renderer's own trims (P1-L, frozen): FP loses 0.25 s of tail, and the
# console head is cut. Used only to ESTIMATE packing; the real duration is
# measured after the render.
CONSOLE_TRIM_S = 2.00
FP_TAIL_TRIM_S = 0.25


def canonical(p) -> str:
    return str(Path(p).resolve()).lower()


def probe(path: Path) -> float:
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()), 3)
    except ValueError:
        return 0.0


def collect():
    """Every T1/T2 POV clip, with its historical source Part.

    A folder holding several files is ONE frag shot from several angles; the
    POV is the file matching the folder name (or the non-FL one). The other
    angles are not separate coverage items -- counting them would inflate the
    denominator with material that is never the spine of a cut.
    """
    items = []
    for tier in ("T1", "T2"):
        for part in range(1, 13):
            d = CLIP_ROOT / tier / "Part{}".format(part)
            if not d.exists():
                continue
            # loose clips
            for q in sorted(d.glob("*.avi")):
                items.append((tier, part, q, []))
            # folder frags: pick the POV, keep the rest as angles
            for sub in sorted(x for x in d.iterdir() if x.is_dir()):
                avis = sorted(sub.glob("*.avi"))
                if not avis:
                    continue
                pov = next((a for a in avis if a.stem.lower() == sub.name.lower()),
                           None)
                if pov is None:
                    pov = next((a for a in avis if "fl" not in a.stem.lower()),
                               avis[0])
                items.append((tier, part, pov, [a for a in avis if a != pov]))
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "output" / "avi_master_queue.json"))
    a = ap.parse_args()

    raw = collect()
    print("[queue] {} T1/T2 POV clip(s) discovered".format(len(raw)), flush=True)

    # substitute the recovered file for the damaged original
    subs = 0
    resolved = []
    for tier, part, q, angles in raw:
        rec = RECOVERED.get(q.resolve())
        if rec and rec.exists():
            resolved.append((tier, part, q, angles, rec))
            subs += 1
        else:
            resolved.append((tier, part, q, angles, None))
    print("[queue] {} damaged source(s) substituted with a recovered file"
          .format(subs), flush=True)

    paths = [(r[4] or r[2]) for r in resolved]
    print("[queue] probing durations...", flush=True)
    with ThreadPoolExecutor(max_workers=8) as ex:
        durs = list(ex.map(probe, paths))

    rows = []
    for (tier, part, q, angles, rec), dur in zip(resolved, durs):
        use = rec or q
        est = max(0.0, dur - CONSOLE_TRIM_S - FP_TAIL_TRIM_S) if dur else 0.0
        rows.append({
            "tier": tier,
            "historical_source_part": part,
            "canonical_avi_path": str(use.resolve()),
            "original_avi_path": str(q.resolve()) if rec else None,
            "substituted": bool(rec),
            "angles": [str(x.resolve()) for x in angles],
            "duration_s": dur,
            "final_rendered_duration_estimate_s": round(est, 3),
            "readable": dur > 0.0,
            "used_in_final_part": None,
        })

    # Interleave T1 and T2 within each historical Part, then run the Parts in
    # order. T1 leads because it is the stronger material.
    ordered = []
    for part in range(1, 13):
        t1 = [r for r in rows if r["historical_source_part"] == part and r["tier"] == "T1"]
        t2 = [r for r in rows if r["historical_source_part"] == part and r["tier"] == "T2"]
        i = j = 0
        while i < len(t1) or j < len(t2):
            if i < len(t1):
                ordered.append(t1[i]); i += 1
            if j < len(t2):
                ordered.append(t2[j]); j += 1
            if j < len(t2) and len(t2) > len(t1):
                ordered.append(t2[j]); j += 1
    for n, r in enumerate(ordered, 1):
        r["sequence_index"] = n

    bad = [r for r in ordered if not r["readable"]]
    good = [r for r in ordered if r["readable"]]
    t1n = sum(1 for r in ordered if r["tier"] == "T1")
    t2n = sum(1 for r in ordered if r["tier"] == "T2")
    est_total = sum(r["final_rendered_duration_estimate_s"] for r in good)

    payload = {
        "built_at": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
        "clip_root": str(CLIP_ROOT),
        "counts": {"T1": t1n, "T2": t2n, "total": len(ordered),
                   "readable": len(good), "unreadable": len(bad),
                   "substituted": subs},
        "estimated_body_seconds": round(est_total, 1),
        "estimated_parts_at_5min": max(1, round(est_total / (4.7 * 60))),
        "unreadable_sources": [
            {"path": r["canonical_avi_path"], "tier": r["tier"],
             "historical_source_part": r["historical_source_part"]} for r in bad],
        "queue": ordered,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("")
    print("=" * 62)
    print("AVI MASTER QUEUE")
    print("=" * 62)
    print("  T1 clips          : {}".format(t1n))
    print("  T2 clips          : {}".format(t2n))
    print("  total             : {}".format(len(ordered)))
    print("  readable          : {}".format(len(good)))
    print("  unreadable        : {}".format(len(bad)))
    for r in bad:
        print("      {}".format(Path(r["canonical_avi_path"]).name))
    print("  substituted       : {} (recovered file used)".format(subs))
    print("  estimated body    : {:.1f} min".format(est_total / 60.0))
    print("  estimated Parts   : ~{} at ~5 min each".format(
        payload["estimated_parts_at_5min"]))
    print("  wrote {}".format(a.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
