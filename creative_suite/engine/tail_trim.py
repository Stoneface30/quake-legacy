"""Measure how much dead time sits at the END of each clip, and how much to cut.

The user's report: "the clip have 1.3 second of next round / too much action we
need to trim ... Just end not start!"

A hand-cut capture usually stops a beat late — the frag lands, and then the
recording keeps rolling into the respawn, the next round, or the console. That
tail is what needs removing, and only from the end.

The measurement is the game's own audio. Rail shots, lightning hits, rocket
explosions, jumps and weapon switches are known sounds shipped in pak00, so the
LAST one of them in a clip marks the last thing worth watching. Everything after
it is the tail.

    dead_tail = clip_duration - time_of_last_game_event

Cutting is deliberately conservative: a fixed hold is left after the last event
so the impact, the kill feed and the immediate aftermath all survive. Only what
is left beyond that hold is removed, and only when there is enough of it to be
worth cutting.

    python -m creative_suite.engine.tail_trim --limit 60
    python -m creative_suite.engine.tail_trim            # whole queue
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "output" / "tail_trim.json"

# Keep this much after the final game event: the kill feed, the body dropping,
# the beat a viewer needs to register what happened.
AFTERMATH_HOLD_S = 1.60

# Below this there is nothing worth cutting.
MIN_TRIM_S = 0.60

# Never remove more than this share of a clip, whatever the detector says. A
# quiet clip with no recognised sounds must not be truncated to nothing.
MAX_TRIM_FRACTION = 0.35


def analyse(path_str: str, templates) -> dict:
    from creative_suite.engine import game_beat as GB
    r = GB.clip_events(path_str, templates)
    d = r.get("duration_s")
    ev = [t for v in (r.get("events") or {}).values() for t in v]
    # The event TIMES are kept, not just the count. Music selection needs to
    # score a song's beat grid against where the action actually happens, and
    # detecting these sounds is the expensive part -- computing it twice would
    # double the cost of a run for no reason.
    out = {"clip": path_str, "clip_name": Path(path_str).name,
           "duration_s": d, "events": len(ev), "last_event_s": None,
           "dead_tail_s": None, "trim_s": 0.0, "reason": "",
           "event_times": sorted(round(x, 3) for x in ev),
           "events_by_family": {k: v for k, v in (r.get("events") or {}).items()}}
    if not d:
        out["reason"] = "unreadable"
        return out
    if not ev:
        out["reason"] = "no recognised game audio -- left untouched"
        return out
    last = max(ev)
    out["last_event_s"] = round(last, 3)
    tail = d - last
    out["dead_tail_s"] = round(tail, 3)

    trim = tail - AFTERMATH_HOLD_S
    if trim < MIN_TRIM_S:
        out["reason"] = "tail {:.2f}s is within the aftermath hold".format(tail)
        return out
    cap = d * MAX_TRIM_FRACTION
    if trim > cap:
        trim = cap
        out["reason"] = "capped at {:.0f}% of the clip".format(
            MAX_TRIM_FRACTION * 100)
    else:
        out["reason"] = "dead tail after last game event"
    out["trim_s"] = round(trim, 3)
    return out


_T = None


def _init(t):
    global _T
    _T = t


def _run(p):
    return analyse(p, _T)


def load_events(path: Path = OUT) -> dict:
    """canonical clip path -> sorted event times, from the same cached scan."""
    if not path.exists():
        return {}
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {str(Path(i["clip"]).resolve()).lower(): (i.get("event_times") or [])
            for i in d.get("items", [])}


def load_table(path: Path = OUT) -> dict:
    """canonical clip path (lowercased) -> seconds to remove from the end."""
    if not path.exists():
        return {}
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {str(Path(i["clip"]).resolve()).lower(): float(i.get("trim_s") or 0.0)
            for i in d.get("items", []) if (i.get("trim_s") or 0) > 0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int,
                    default=max(2, (os.cpu_count() or 4) // 2))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    import numpy as np
    from creative_suite.engine import game_beat as GB
    tmpl = GB.load_templates()
    ser = {k: [(n, np.asarray(y, dtype=np.float32)) for n, y in v]
           for k, v in tmpl.items()}

    q = json.loads((REPO_ROOT / "output" / "avi_master_queue.json")
                   .read_text(encoding="utf-8"))["queue"]
    clips = [r["canonical_avi_path"] for r in q]
    # the FL angles need it too -- they are the ones that end on the console
    for r in q:
        clips += [a2 for a2 in (r.get("angles") or [])]
    clips = [c for c in dict.fromkeys(clips) if Path(c).exists()]
    if a.limit:
        clips = clips[:a.limit]
    print("[tail] {} clip(s), {} workers".format(len(clips), a.workers),
          flush=True)

    rows = []
    with ProcessPoolExecutor(max_workers=a.workers, initializer=_init,
                             initargs=(ser,)) as ex:
        futs = {ex.submit(_run, c): c for c in clips}
        for i, f in enumerate(as_completed(futs), 1):
            try:
                rows.append(f.result())
            except Exception as exc:                  # noqa: BLE001
                print("  worker died: {}".format(exc), flush=True)
            if i % 100 == 0:
                print("  {}/{}".format(i, len(clips)), flush=True)

    Path(a.out).write_text(json.dumps({"clips": len(rows), "items": rows},
                                      indent=2), encoding="utf-8")
    trimmed = [r for r in rows if r["trim_s"] > 0]
    tails = sorted(r["dead_tail_s"] for r in rows if r["dead_tail_s"] is not None)
    print("")
    print("=" * 64)
    print("END-TRIM ANALYSIS")
    print("=" * 64)
    print("  clips analysed      : {}".format(len(rows)))
    print("  no game audio found : {}".format(
        sum(1 for r in rows if r["events"] == 0)))
    if tails:
        print("  dead tail  median {:.2f}s   p75 {:.2f}s   p95 {:.2f}s   max {:.2f}s"
              .format(tails[len(tails)//2], tails[int(len(tails)*.75)],
                      tails[int(len(tails)*.95)], tails[-1]))
    print("  clips to trim       : {} ({:.0f}%)".format(
        len(trimmed), 100.0 * len(trimmed) / max(1, len(rows))))
    if trimmed:
        ts = sorted(r["trim_s"] for r in trimmed)
        print("  trim amount median  : {:.2f}s   max {:.2f}s".format(
            ts[len(ts)//2], ts[-1]))
        print("")
        print("  worst offenders:")
        for r in sorted(trimmed, key=lambda z: -z["trim_s"])[:8]:
            print("    {:44} dur {:>6.2f}  last evt {:>6.2f}  trim {:>5.2f}s"
                  .format(r["clip_name"][:44], r["duration_s"],
                          r["last_event_s"], r["trim_s"]))
    print("")
    print("  wrote {}".format(a.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
