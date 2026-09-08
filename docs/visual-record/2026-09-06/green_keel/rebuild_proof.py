"""GREEN KEEL, decided on pixels.

One real POV kill, filmed twice offscreen through the same backend at the
same server time with the same camera, differing only in the VisualProfile.
Then the frames are measured. Nothing here reads a cfg or a cvar echo.
"""
import json, os, sqlite3, sys
os.chdir("G:/QUAKE_LEGACY/.claude/worktrees/pantheon-headless")
sys.path.insert(0, ".")
os.environ["PANTHEON_PERFORMANCE_STORE"] = "F:/QUAKE_LEGACY_STORE"

from pathlib import Path
from collections import Counter
from creative_suite.engine import wolfcam_capture as wc
from engine.pantheon import offscreen as O, visual_profile as VP, measure as M

STAGING = Path("G:/QUAKE_LEGACY/output/demo_v2/_wolfcam_staging")
wc.STAGING = STAGING
OUT = Path("G:/QUAKE_LEGACY/docs/visual-record/2026-09-06/green_keel")
OUT.mkdir(parents=True, exist_ok=True)

# The chosen moment: a POV kill whose victim is observed within 1.5 s, so an
# enemy body is on screen at the kill.
# a POINT-BLANK kill: killer and victim 81 units apart, so the enemy body
# fills a real share of the frame and a silhouette can be judged.
DEMO_HASH, CLIENT, VICTIM, T_MS = "e4bd2a36495928d0", 2, 1, 579825
PRE, POST = 1600, 900

from engine.pantheon import performance_index as PI
con = PI._ro()
(path,) = con.execute("select path from demos where demo_hash=?", (DEMO_HASH,)).fetchone()
demo = Path(path)
print(f"demo   : {demo.name[:40]}  client {CLIENT} kills {VICTIM} at {T_MS}")
safe = wc.stage_demo(demo, staging=STAGING)

runs = {}
for label, prof in (("A_authentic", "AUTHENTIC"), ("B_review", "REVIEW")):
    win = [{"clip_name": label, "start_ms": T_MS - PRE, "end_ms": T_MS + POST}]
    res = O.capture(safe, win, staging=STAGING,
                    profile_cvars=VP.profile(prof).resolve(),
                    purpose=f"green keel proof {label}")
    runs[label] = res
    print(f"{label:12s} ok={res['ok']} visible_windows={res['visible_windows']} "
          f"stole_focus={res['stole_focus']} {res['seconds']:.0f}s")
    if not res["avis"]:
        print("  NO AVI:", res.get("detail"), res.get("missing")); raise SystemExit(1)

# SAMPLE THE WHOLE CLIP. A single guessed instant may hold no enemy body at
# all -- the first attempt grabbed a corridor. The same timestamps are read
# from both captures, so every comparison is like for like.
def green_pixels(buf):
    n, hits = 0, []
    for i in range(0, len(buf), 3):
        r, g, b = buf[i], buf[i + 1], buf[i + 2]
        if g > 90 and g - r > 55 and g - b > 55:
            n += 1
            hits.append((r, g, b))
    return n, hits


span = (PRE + POST) / 1000.0
stamps = [round(span * i / 13, 2) for i in range(1, 13)]
per_frame = {"A_authentic": {}, "B_review": {}}
for label, r in runs.items():
    avi = Path(r["avis"][label])
    for t in stamps:
        try:
            buf = M.frame_rgb(avi, t)
        except Exception as exc:
            per_frame[label][t] = {"error": str(exc)[:60]}
            continue
        n, hits = green_pixels(buf)
        avg = tuple(round(sum(c[k] for c in hits) / len(hits)) for k in range(3)) if hits else None
        per_frame[label][t] = {"green": n, "mean": avg}

best_t, best_n = None, -1
for t in stamps:
    n = per_frame["B_review"].get(t, {}).get("green", 0)
    if n > best_n:
        best_t, best_n = t, n
a_at_best = per_frame["A_authentic"].get(best_t, {}).get("green", 0)
print(f"peak green in REVIEW at t={best_t}s: {best_n} px   (AUTHENTIC at the same t: {a_at_best} px)")
for t in stamps:
    print(f"   t={t:5.2f}  A={per_frame['A_authentic'].get(t, {}).get('green', 0):6d}"
          f"  B={per_frame['B_review'].get(t, {}).get('green', 0):6d}"
          f"  B_mean={per_frame['B_review'].get(t, {}).get('mean')}")

for label, r in runs.items():
    M.save_still(Path(r["avis"][label]), best_t, OUT / f"{label}.png")
frames = {label: M.frame_rgb(Path(r["avis"][label]), best_t) for label, r in runs.items()}
res = {label: {"strong_green_pixels": per_frame[label].get(best_t, {}).get("green", 0),
               "mean_rgb_of_those": per_frame[label].get(best_t, {}).get("mean")}
       for label in runs}
changed = M.added_pixels(frames["A_authentic"], frames["B_review"])
summary = M.summarise(changed)
report = {
    "moment": {"demo_hash": DEMO_HASH, "client": CLIENT, "victim": VICTIM,
               "server_time_ms": T_MS},
    "profiles": {"A": "AUTHENTIC", "B": "REVIEW"},
    "window_focus": {label: {"visible_windows": r["visible_windows"],
                             "stole_focus": r["stole_focus"]}
                     for label, r in runs.items()},
    "sampled_timestamps": stamps,
    "green_per_frame": per_frame,
    "compared_at_s": best_t,
    "pixels": res,
    "changed_pixels_summary": summary,
    "verdict": ("GREEN_ENEMY_PROVEN"
                if res["B_review"]["strong_green_pixels"] >
                   max(50, res["A_authentic"]["strong_green_pixels"] * 3)
                else "NOT_PROVEN"),
}
(OUT / "green_keel_proof.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
print(json.dumps({k: report[k] for k in ("pixels", "verdict")}, indent=1))
print("stills + report ->", OUT)
