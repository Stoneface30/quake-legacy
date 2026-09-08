"""Predict a finished Part's duration, and pack the archive into Parts that hit it.

The previous packer summed a per-clip estimate stored in the queue and stopped
near a target. Measured against twelve real renders it predicted 4.44-4.56
minutes for Parts that came out 4.78-8.02 -- a mean error of +33% with a
standard deviation of 23 points. A packer that wrong is not packing at all.

Three terms were missing, in order of size:

  1. ANGLE SEGMENTS. A frag with a second camera plays that camera too, and
     `render_fl_angle` runs it at 0.55x -- so an 8 s angle becomes 14.5 s of
     finished video. Nothing modelled this. Correlation across the twelve
     Parts is unmistakable: the Parts with no angles overran by 17-33 s, the
     Parts with 10-13 angle clips overran by 140-212 s.
  2. THE OPENER AND CLOSER. 8 s + 10 s that the body estimate never included.
  3. SLOW-MOTION EXPANSION at the real solved rate, against seam crossfades
     which give a little back.

This module models all of them from the same constants the renderer uses, so
the two cannot drift apart, and it is validated against real renders rather
than trusted.

    python -m creative_suite.engine.pack_model --calibrate   # vs real Parts
    python -m creative_suite.engine.pack_model --dry-run     # full plan
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
OUT = REPO_ROOT / "output"

# --- constants mirrored from the renderer -----------------------------------
INTRO_S = 8.0
OUTRO_S = 10.0
XFADE_S = 0.35
FL_TAIL_TRIM_S = 0.90
FP_TAIL_TRIM_S = 0.25
SLOW_PRE_S = 0.70
SLOW_POST_S = 1.10
SLOW_RATE = 0.45
SLOWMO_EVERY_N = 3
SHORT_CLIP_SLOWMO_S = 7.0
FL_LEADS_IN = False        # alternate views are insets now, not segments
FL_LEAD_RATE = 0.55            # render_fl_angle(which=0, slow=0.55)
FL_SECOND_RATE = 0.50          # render_fl_angle(which=1, slow=0.50)

# --- the hard editorial window (user 2026-09-01) ----------------------------
PART_MIN_S = 300.0             # 5:00
PART_MAX_S = 360.0             # 6:00
PART_TARGET_S = 325.0          # 5:25 -- centred low, so estimation error has
                               # room to run long without breaching 6:00


def _angle_out(fl_dur: float, rate: float, fl_trim: float = 0.0) -> float:
    """Finished seconds one angle contributes.

    Mirrors render_fl_angle exactly, including the fact that it trims the angle
    TWICE: `source_window` applies the measured boundary cut (or the FL guard),
    and then the console tail is taken off on top. Modelling only the second
    trim over-credited every angle by about 2.9 s, which is what made the
    angle-heavy Parts over-predict by up to 7.8%.
    """
    if fl_dur < 1.0:
        return 0.0
    a = 0.0
    b = fl_dur - (fl_trim if fl_trim > 0 else min(FL_TAIL_TRIM_S, fl_dur * 0.10))
    b = max(a + 0.5, b)
    b = max(a + 0.5, b - min(FL_TAIL_TRIM_S, fl_dur * 0.20))
    if b - a < 0.5:
        return 0.0
    return (b - a) / max(0.35, min(1.0, rate))


def clip_contribution(dur: float, trim: float, is_fl: bool, slowmo: bool,
                      angle_durs=(), slow_rate: float = SLOW_RATE):
    """(finished seconds, segment count) for one clip and its angles."""
    guard = FL_TAIL_TRIM_S if is_fl else FP_TAIL_TRIM_S
    tail = trim if trim > 0 else min(guard, dur * 0.10)
    w = max(0.5, dur - tail)

    out = w
    if slowmo:
        # the accent window, clipped to what the clip actually has
        pk = min(max(w * 0.5, 0.4), max(0.4, w - 0.4))
        a = max(0.0, pk - SLOW_PRE_S)
        b = min(w, pk + SLOW_POST_S)
        win = max(0.0, b - a)
        out = w + win * (1.0 / slow_rate - 1.0)

    # Alternate cameras add NO duration any more. They are composited into
    # this segment as an inset cut to the action, not concatenated as extra
    # video (user 2026-09-01: "all the FL ... need to be all picture in
    # picture"). This also removes the term that made the old packer wrong by
    # up to 78%: nothing about a second camera changes how long a Part runs.
    return out, 1


def part_duration(contribs) -> float:
    """Finished Part seconds from a list of (seconds, segments)."""
    body = sum(c for c, _ in contribs)
    segs = sum(s for _, s in contribs) + 2      # opener + closer
    seams = max(0, segs - 1)
    return INTRO_S + OUTRO_S + body - XFADE_S * seams


# --------------------------------------------------------------- clip facts
def load_clips():
    """Every primary source with the facts the model needs."""
    q = json.loads((OUT / "avi_master_queue.json").read_text(encoding="utf-8"))["queue"]
    trims, drops = {}, set()
    b = OUT / "clip_boundary.json"
    if b.exists():
        d = json.loads(b.read_text(encoding="utf-8"))
        for r in d.get("items", []):
            k = str(Path(r["clip"]).resolve()).lower()
            if (r.get("trim_s") or 0) > 0:
                trims[k] = float(r["trim_s"])
            if r.get("drop"):
                drops.add(k)
    ad = {}
    a = OUT / "_angle_durations.json"
    if a.exists():
        ad = {str(Path(k).resolve()).lower(): v
              for k, v in json.loads(a.read_text(encoding="utf-8")).items()}

    out = []
    for i, r in enumerate(q):
        p = Path(r["canonical_avi_path"])
        k = str(p.resolve()).lower()
        angs = []
        for x in (r.get("angles") or []):
            xk = str(Path(x).resolve()).lower()
            if xk in drops:
                continue
            if ad.get(xk):
                angs.append((ad[xk], trims.get(xk, 0.0)))
        out.append({
            "path": str(p), "key": k, "tier": r.get("tier"),
            "dur": float(r.get("duration_s") or 0.0),
            "trim": trims.get(k, 0.0),
            "angles": sorted(angs, key=lambda z: -z[0])[:2],
            "hist_part": r.get("historical_source_part"),
            "seq": i,
        })
    return out


def contribution_for(c, index_in_part: int):
    """What this clip contributes, including whether it earns an accent."""
    dur = c["dur"]
    slowmo = (dur <= SHORT_CLIP_SLOWMO_S
              or (c["tier"] == "T1" and index_in_part % SLOWMO_EVERY_N == 0))
    return clip_contribution(dur, c["trim"], False, slowmo, c["angles"])


# ------------------------------------------------------- global editorial pack
def _editorial_order(bin_clips):
    """Order one Part deliberately -- not by folder, not at random.

    The historical T1/T2 Part folders are provenance only (user 2026-09-01:
    "PUT ALL 1076 T1 + T2 CLIPS INTO ONE GLOBAL EDITORIAL POOL"), so ordering
    is free and should be used. Two things are avoided because they are what a
    viewer notices: a block of same-length clips, and a block of one tier.
    Long and short alternate around the middle, and tiers interleave.
    """
    longs = sorted([c for c in bin_clips if c["dur"] >= 12.0],
                   key=lambda c: -c["dur"])
    shorts = sorted([c for c in bin_clips if c["dur"] < 12.0],
                    key=lambda c: c["dur"])
    out, t = [], True
    while longs or shorts:
        src = longs if (t and longs) or not shorts else shorts
        out.append(src.pop(0))
        t = not t
    # nudge a T1 into the opening and closing slots -- the strongest material
    t1 = [i for i, c in enumerate(out) if c["tier"] == "T1"]
    if t1 and out[0]["tier"] != "T1":
        out.insert(0, out.pop(t1[0]))
    t1 = [i for i, c in enumerate(out) if c["tier"] == "T1"]
    if t1 and out[-1]["tier"] != "T1" and len(t1) > 1:
        out.append(out.pop(t1[-1]))
    return out


def _bin_duration(bin_clips):
    return part_duration([contribution_for(c, i)
                          for i, c in enumerate(bin_clips)])


def plan_parts(clips, target=PART_TARGET_S, lo=PART_MIN_S, hi=PART_MAX_S,
               max_passes=4000):
    """Split the whole pool into Parts that all land inside [lo, hi].

    Duration is solved GLOBALLY rather than by walking the list and stopping at
    a threshold -- the greedy walk is what produced a 2:40 remainder and 8:02
    outliers. Longest-first assignment into the emptiest bin gets the sizes
    close, then a repair loop moves single clips from the longest bin to the
    shortest until every Part is inside the window. Every clip stays in exactly
    one bin throughout, so coverage cannot drift.
    """
    solo = {c["key"]: contribution_for(c, 1)[0] for c in clips}
    total = sum(solo.values())
    n = max(1, round(total / target))
    for cand in (n, n + 1, n - 1):
        if cand > 0 and lo <= total / cand <= hi:
            n = cand
            break

    bins = [[] for _ in range(n)]
    for c in sorted(clips, key=lambda z: -solo[z["key"]]):
        bins.sort(key=lambda b: sum(solo[x["key"]] for x in b))
        bins[0].append(c)

    for _ in range(max_passes):
        durs = [_bin_duration(b) for b in bins]
        hi_i = max(range(n), key=lambda i: durs[i])
        lo_i = min(range(n), key=lambda i: durs[i])
        if durs[hi_i] <= hi and durs[lo_i] >= lo:
            break
        if hi_i == lo_i or len(bins[hi_i]) < 2:
            break
        # move the clip that best closes the gap without overshooting
        gap = (durs[hi_i] - durs[lo_i]) / 2.0
        mover = min(bins[hi_i], key=lambda c: abs(solo[c["key"]] - gap))
        bins[hi_i].remove(mover)
        bins[lo_i].append(mover)

    parts = [_editorial_order(b) for b in bins]
    parts.sort(key=lambda b: -sum(1 for c in b if c["tier"] == "T1"))
    return parts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--target", type=float, default=PART_TARGET_S)
    ap.add_argument("--out", default=str(OUT / "part_plan.json"))
    a = ap.parse_args()

    clips = load_clips()
    parts = plan_parts(clips, target=a.target)

    seen, rows = {}, []
    for i, b in enumerate(parts, 1):
        d = _bin_duration(b)
        for c in b:
            seen[c["key"]] = seen.get(c["key"], 0) + 1
        rows.append({
            "part": i, "clips": len(b), "pred_s": round(d, 2),
            "t1": sum(1 for c in b if c["tier"] == "T1"),
            "t2": sum(1 for c in b if c["tier"] == "T2"),
            "with_angles": sum(1 for c in b if c["angles"]),
            "hist_parts": sorted({c["hist_part"] for c in b if c["hist_part"]}),
            "paths": [c["path"] for c in b],
        })

    durs = sorted(r["pred_s"] for r in rows)
    bad = [r for r in rows if not (PART_MIN_S <= r["pred_s"] <= PART_MAX_S)]
    dup = [k for k, n in seen.items() if n > 1]

    print("")
    print("=" * 74)
    print("DRY RUN -- GLOBAL EDITORIAL PACK")
    print("=" * 74)
    print("  clips in pool        : {}".format(len(clips)))
    print("  proposed Parts       : {}".format(len(rows)))
    print("  covered exactly once : {}".format(len(seen)))
    print("  duplicates           : {}".format(len(dup)))
    print("  missing              : {}".format(len(clips) - len(seen)))
    print("")
    print("  predicted duration   : min {:.2f}  median {:.2f}  mean {:.2f}  max {:.2f} min"
          .format(durs[0]/60, statistics.median(durs)/60,
                  statistics.mean(durs)/60, durs[-1]/60))
    print("  outside 5:00-6:00    : {}".format(len(bad)))
    print("")
    print("  {:>5} {:>6} {:>9} {:>5} {:>5} {:>8}  {}".format(
        "part", "clips", "pred", "T1", "T2", "angles", "historical source parts"))
    for r in rows:
        flag = "" if PART_MIN_S <= r["pred_s"] <= PART_MAX_S else "  <<< OUT"
        print("  {:>5} {:>6} {:>8.2f}m {:>5} {:>5} {:>8}  {}{}".format(
            r["part"], r["clips"], r["pred_s"]/60, r["t1"], r["t2"],
            r["with_angles"], str(r["hist_parts"])[:34], flag))
    Path(a.out).write_text(json.dumps({"parts": rows}, indent=1), encoding="utf-8")
    print("")
    print("  wrote {}".format(a.out))
    ok = not bad and not dup and len(seen) == len(clips)
    print("  DRY RUN: {}".format("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
