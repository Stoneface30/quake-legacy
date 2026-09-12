"""Capture a small, diverse sample of whole rounds to check boundaries by eye.

At most 12 rounds: the best-scoring round in each weapon lane first, then the
next best overall, skipping partial rounds (cut by the end of the demo). Each
round is filmed as ONE window from the countdown to its hard end, through the
proven headless path (profile TR4SH_FAST_REVIEW_V1: 512x288, 20 fps, bright,
green-Keel enemies). Nothing here is a batch: the full run waits for the
user's approval.

Every result is checked mechanically -- duration against the window, frame
count, focus -- and written to samples/samples.json.
"""
from __future__ import annotations

import collections
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "G:/QUAKE_LEGACY")
from creative_suite.engine import review_proxy as rp              # noqa: E402
from creative_suite.engine import wolfcam_capture as wc           # noqa: E402
from engine.pantheon import offscreen, render_permit              # noqa: E402

HERE = Path("G:/QUAKE_LEGACY/output/demo_v2/round_review_v2")
OUT = HERE / "samples"
OUT.mkdir(exist_ok=True)
FF = Path("G:/QUAKE_LEGACY/creative_suite/tools/ffmpeg/ffmpeg.exe")
FP = FF.parent / "ffprobe.exe"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 12

rounds = json.loads((HERE / "rounds_ranked.json").read_text(encoding="utf-8"))
pool = [u for u in rounds if u["kills"] and not u["partial"]
        and ";" not in u["demo_name"]]
picked, seen_lane = [], set()
for u in pool:                                   # best per lane first
    if u["lane"] not in seen_lane:
        picked.append(u)
        seen_lane.add(u["lane"])
    if len(picked) >= N:
        break
for u in pool:                                   # then best overall
    if len(picked) >= N:
        break
    if u not in picked:
        picked.append(u)

print("permit:", render_permit.check())
results = []
for i, u in enumerate(picked, 1):
    dur_s = (u["end_ms"] - u["start_ms"]) / 1000.0
    src, _h = rp.demo_source(u["demo_name"])
    safe = wc.stage_demo(Path(src))
    name = "round_%02d" % i
    t0 = time.time()
    res = offscreen.capture(
        safe, [{"start_ms": u["start_ms"], "end_ms": u["end_ms"], "clip_name": name}],
        staging=wc.STAGING, profile="TR4SH_FAST_REVIEW_V1",
        timeout=max(180, 60 + dur_s * 4), purpose="round sample %d" % i,
        lock_wait_s=180.0)
    el = time.time() - t0
    avi = (res.get("avis") or {}).get(name)
    rec = {"i": i, "role": u["role"], "score": u["score"], "lane": u["lane"],
           "kills": u["kills"], "end_reason": u["end_reason"],
           "window_s": round(dur_s, 2), "capture_s": round(el, 1),
           "stole_focus": res.get("stole_focus"),
           "frames": res.get("frames_written"), "traits": u["traits"],
           "map": u["map"], "round": u["round"]}
    if avi:
        mp4 = OUT / ("%s.mp4" % name)
        subprocess.run([str(FF), "-v", "error", "-y", "-i", str(avi), "-c:v",
                        "libx264", "-preset", "veryfast", "-crf", "22",
                        "-pix_fmt", "yuv420p", str(mp4)],
                       check=True, capture_output=True, timeout=900)
        Path(avi).unlink(missing_ok=True)
        pr = subprocess.run([str(FP), "-v", "error", "-show_entries",
                             "format=duration", "-of", "csv=p=0", str(mp4)],
                            capture_output=True, text=True, timeout=60)
        got = float(pr.stdout.strip() or 0)
        rec.update(mp4=str(mp4), duration_s=round(got, 2),
                   duration_ok=abs(got - dur_s) <= 1.0)
    else:
        rec.update(mp4=None, error=res.get("detail") or "no AVI")
    results.append(rec)
    print("%2d %-22s %6.1fs window  %5.1fs capture  %s  focus=%s"
          % (i, u["role"], dur_s, el,
             "OK" if rec.get("duration_ok") else "FAIL %s" % rec.get("error", ""),
             rec["stole_focus"]), flush=True)

(OUT / "samples.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
ok = sum(1 for r in results if r.get("duration_ok"))
print("\n%d/%d samples valid; focus stolen on %d"
      % (ok, len(results), sum(1 for r in results if r["stole_focus"])))
