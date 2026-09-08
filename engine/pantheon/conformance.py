"""BACKEND A/B CONFORMANCE -- may PANTHEON_QUAKE_OFFSCREEN replace the window?

The question is not "does the offscreen backend produce a file". It is whether
a reviewer looking at its output sees the same event, in the same place, in
the same light, as the reference backend that has been trusted until now. So
the two legs are the SAME capture path (staging, cfg, command line, watcher)
differing in exactly one variable -- the desktop the process lives on:

    A  WOLFCAM_REFERENCE          interactive desktop, a window on the screen
    B  PANTHEON_QUAKE_OFFSCREEN   hidden desktop, no window, no focus

WHY THERE IS A NOISE FLOOR. Two runs of the same Quake client over the same
demo are not bit-identical: particles, marks and lighting carry run-to-run
randomness, and the AVI's first frame can land a tick either side. Declaring
A and B "different" on a delta smaller than that would be a lie dressed as
rigour. CONTROL therefore films the SAME leg twice, and a case only counts as
DIFFERENT when the A/B delta exceeds what the backend does against itself.

Nothing here spells a cvar. The look is a ReviewVisualProfile; the cases come
from the headless performance index; no name, nickname or identifier enters a
case, only a demo hash, a client slot and a serverTime.
"""
from __future__ import annotations

import json
import statistics
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from engine.pantheon import measure as M
from engine.pantheon import offscreen as O
from engine.pantheon import store as S
from engine.pantheon import visual_profile as VP
from engine.pantheon.backends import BackendUse

REFERENCE = "WOLFCAM_REFERENCE"
OFFSCREEN = "PANTHEON_QUAKE_OFFSCREEN"

PRE_MS, POST_MS = 1400, 900          # a shot around the anchor tick
SAMPLES = 6                          # frames compared per case
DIFF_THRESHOLD = 24                  # per channel, out of 255

# The capture seeks to `start - SEEK_SETTLE_MS`. A moment too near the head of
# a demo therefore seeks to a serverTime BEFORE the first snapshot, and the
# engine sits there until the timeout with no AVI and no complaint. Every case
# is drawn from after this mark.
MIN_T_MS = 8000


# -- the ten cases, as selectors over the headless index --------------------
#
# A case says WHAT must be on screen, never which demo -- the demo is resolved
# from the index at run time, so the suite survives a corpus change and the
# report records the exact moment it actually filmed.

@dataclass(frozen=True)
class Case:
    name: str
    why: str
    where: str                       # sql predicate over `actions`
    order: str = "t_ms"


_POV_RAIL = "kind = 'FIRE_RAIL' and outcome = 'KILL' and is_pov = 1"
_POV_LG = "kind = 'KILL' and weapon = 'LG' and is_pov = 1"
_POV_ROCKET_KILL = ("kind = 'FIRE_ROCKET' and outcome = 'KILL' "
                    "and projectile_samples >= 4 and is_pov = 1")
_POV_GRENADE = ("kind = 'FIRE_GRENADE' and projectile_samples >= 4 "
                "and is_pov = 1")
_POV_PAD = "kind = 'JUMP_PAD' and airborne_ms >= 900 and is_pov = 1"
# Not is_pov: the index holds no POV teleport at all -- a teleport is
# attributed from the out/in pair on an OBSERVED client, and the recorder's
# own is not one of them. What matters visually is the same either way.
_TELEPORT = "kind = 'TELEPORT'"
_CROWD = ("kind = 'KILL' and is_pov = 1 and demo_hash in "
          "(select demo_hash from demos where clients >= 10)")
_DARK = "kind = 'KILL' and lower(map) = 'blackcathedral'"
_POV_IMPACT = ("kind = 'FIRE_ROCKET' and outcome = 'HIT' "
               "and projectile_samples >= 4 and is_pov = 1")
_RECORDER_DIES = ("kind = 'KILL' and is_pov = 0 and victim is not null "
                  "and victim = (select recorder_client from demos d "
                  "where d.demo_hash = actions.demo_hash)")

CASES: tuple[Case, ...] = (
    Case("RAIL", "a hitscan beam and its trail, the thinnest thing to compare",
         _POV_RAIL),
    Case("LG", "a continuous beam plus impact sparks over many frames",
         _POV_LG),
    Case("ROCKET", "a projectile crossing the frame, then a blast",
         _POV_ROCKET_KILL),
    Case("GRENADE", "bounce physics and a delayed explosion", _POV_GRENADE),
    Case("JUMP_PAD", "fast camera translation with a large view change",
         _POV_PAD, "airborne_ms desc"),
    Case("TELEPORT", "a hard discontinuity: an observed body is replaced",
         _TELEPORT),
    Case("MULTI_PLAYER_ROUND", "many characters at once -- model and skin work",
         _CROWD),
    Case("LOW_LIGHT_MAP", "a dark map, where a gamma or exposure difference shows",
         _DARK),
    Case("PROJECTILE_IMPACT", "an impact WITHOUT a kill: marks, smoke, no obituary",
         _POV_IMPACT),
    Case("DEATH", "the recorder dies -- death camera, not the shooter's view",
         _RECORDER_DIES),
)


def pick(case: Case, *, seed: int = 0) -> dict | None:
    """One concrete moment for a case. Deterministic: same index, same pick."""
    from engine.pantheon import performance_index as PI
    con = PI._ro()
    keys = ("performance_id", "demo_hash", "client", "kind", "t_ms", "map",
            "weapon", "outcome")
    row = con.execute(
        f"select {', '.join(keys)} from actions "
        f"where t_ms >= {MIN_T_MS} and ({case.where}) "
        f"order by {case.order}, performance_id limit 1 offset ?",
        (seed,)).fetchone()
    if row is None:
        return None
    got = dict(zip(keys, row))
    (path,) = con.execute("select path from demos where demo_hash = ?",
                          (got["demo_hash"],)).fetchone()
    got["demo"] = path
    return got


# -- filming one leg --------------------------------------------------------

def film(moment: dict, *, label: str, desktop: str | None, staging: Path,
         profile: str = "REVIEW",
         use: BackendUse = BackendUse.REFERENCE_RENDER) -> dict:
    """One capture, with a declared purpose from the closed list of uses."""
    from creative_suite.engine import wolfcam_capture as wc
    wc.STAGING = staging
    safe = wc.stage_demo(Path(moment["demo"]), staging=staging)
    t = int(moment["t_ms"])
    win = [{"clip_name": label, "start_ms": t - PRE_MS, "end_ms": t + POST_MS}]
    from creative_suite.engine import master_profile as mp
    res = O.capture(safe, win, staging=staging, profile=mp.REVIEW_PROFILE_NAME,
                    profile_cvars=VP.profile(profile).resolve(),
                    desktop=desktop, purpose=f"{use.value}:{label}")
    res["avi"] = res["avis"].get(label)
    return res


# -- measuring one pair -----------------------------------------------------
#
# WHAT A PER-PIXEL COMPARISON ACTUALLY MEASURES. The first run of this suite
# reported a fifth of the pixels differing between the two legs -- and the
# SAME fifth between two runs of one leg. The stills explain it: both frames
# hold the identical instant (same beam, same two bodies, same explosion) with
# the camera at a fraction of a frame's difference in yaw. A capture starts on
# whichever tick the engine reaches first, so the interpolated view is
# sub-frame out, and every edge in a 1920x1080 frame lands a pixel over.
#
# A reviewer does not see that. What a reviewer would see is a different
# model, a different skin colour, a missing effect, a darker room. So the
# readings below are the ones invariant to a small camera phase and sensitive
# to exactly those: exposure, colour distribution, and the share of the frame
# carrying the review profile's own green. The per-pixel figure is still
# reported, because dropping a measurement because it is inconvenient is how
# a suite starts lying.

FRAME_S = 1 / 60.0
SEARCH_FRAMES = 3        # measured offsets were 0 in 55 of 60 samples
COARSE = (240, 135)      # area-averaged: fine jitter cancels, shapes survive
BINS = 32


def _luma(buf: bytes) -> float:
    tot, n = 0.0, 0
    for i in range(0, len(buf) - 3, 3):
        tot += 0.299 * buf[i] + 0.587 * buf[i + 1] + 0.114 * buf[i + 2]
        n += 1
    return tot / max(n, 1)


def _histogram(buf: bytes) -> list[float]:
    """Normalised 32-bin histogram per channel. Where a thing sits in frame
    changes this not at all; what colour it is changes it immediately."""
    h = [0] * (BINS * 3)
    n = 0
    for i in range(0, len(buf) - 3, 3):
        for ch in range(3):
            h[ch * BINS + (buf[i + ch] * BINS) // 256] += 1
        n += 1
    return [c / max(n, 1) for c in h]


def _hist_distance(a: list[float], b: list[float]) -> float:
    """1 - intersection, averaged over the three channels. 0 is identical."""
    inter = sum(min(x, y) for x, y in zip(a, b))
    return round(1 - inter / 3.0, 4)


def _green_share(buf: bytes) -> float:
    """The REVIEW profile's own signature: how much of the frame is the
    forced enemy. Measured with the predicate the green Keel proof used."""
    hits, n = 0, 0
    for i in range(0, len(buf) - 3, 3):
        r, g, b = buf[i], buf[i + 1], buf[i + 2]
        if g > 90 and g - r > 55 and g - b > 55:
            hits += 1
        n += 1
    return round(hits / max(n, 1), 5)


def _pixel_share(a: bytes, b: bytes, *, step: int = 13) -> float:
    differing, n = 0, 0
    for i in range(0, len(a) - 3, 3 * step):
        if (abs(a[i] - b[i]) > DIFF_THRESHOLD
                or abs(a[i + 1] - b[i + 1]) > DIFF_THRESHOLD
                or abs(a[i + 2] - b[i + 2]) > DIFF_THRESHOLD):
            differing += 1
        n += 1
    return round(differing / max(n, 1), 4)


def _frame(avi: Path, t: float, cache: dict | None, *, coarse: bool = False) -> bytes:
    """One frame, remembered. A case now runs six comparisons over four
    clips; without this each one re-decodes the same frames."""
    key = (str(avi), round(t, 4), coarse)
    if cache is not None and key in cache:
        return cache[key]
    buf = (M.frame_rgb(avi, t, COARSE, resample=True) if coarse
           else M.frame_rgb(avi, t))
    if cache is not None:
        cache[key] = buf
    return buf


def _aligned_delta(avi_a: Path, avi_b: Path, t: float, cache: dict | None = None) -> dict:
    """Compare the same INSTANT, not the same timecode: the legs can start a
    frame apart. A's frame is matched against B's nearest few and the best
    match is the reading; the offset it needed is reported, because a
    systematic offset would itself be a finding."""
    a = _frame(avi_a, t, cache)
    best_share, best_k = None, 0
    for k in range(-SEARCH_FRAMES, SEARCH_FRAMES + 1):
        u = t + k * FRAME_S
        if u <= 0:
            continue
        try:
            share = _pixel_share(a, _frame(avi_b, u, cache))
        except Exception:
            continue
        if best_share is None or share < best_share:
            best_share, best_k = share, k
    if best_share is None:
        raise RuntimeError(f"no comparable frame near t={t}")

    u = max(t + best_k * FRAME_S, FRAME_S)
    ca = _frame(avi_a, t, cache, coarse=True)
    cb = _frame(avi_b, u, cache, coarse=True)
    la, lb = _luma(ca), _luma(cb)
    ga, gb = _green_share(ca), _green_share(cb)
    return {"pixel_share": best_share, "aligned_frames": best_k,
            "luma_a": round(la, 2), "luma_b": round(lb, 2),
            "luma_delta": round(abs(la - lb), 2),
            "hist_distance": _hist_distance(_histogram(ca), _histogram(cb)),
            "green_a": ga, "green_b": gb,
            "green_delta": round(abs(ga - gb), 5)}


def duration_s(avi: Path) -> float:
    """How long the file actually is. A capture can stop early -- the first
    run of this suite sampled a 2.3s window in a clip that held 0.7s, and
    four of the six readings were errors nobody had to look at."""
    out = subprocess.run(
        [str(M.FFMPEG.with_name("ffprobe.exe")), "-v", "error",
         "-show_entries", "format=duration", "-of", "csv=p=0", str(avi)],
        capture_output=True, timeout=120)
    try:
        return float(out.stdout.decode().strip())
    except ValueError:
        return 0.0


def compare(avi_a: Path, avi_b: Path, *, span_s: float,
            cache: dict | None = None) -> dict:
    # Sample inside what BOTH legs actually hold, leaving room for the
    # alignment search at either end.
    edge = (SEARCH_FRAMES + 1) * FRAME_S
    have = min(duration_s(avi_a), duration_s(avi_b))
    usable = min(span_s, have) - edge
    if usable <= edge:
        return {"comparable": False, "seconds_a": round(duration_s(avi_a), 2),
                "seconds_b": round(duration_s(avi_b), 2),
                "errors": [f"only {have:.2f}s of common footage"]}
    stamps = [round(edge + usable * i / (SAMPLES + 1), 2)
              for i in range(1, SAMPLES + 1)]
    frames, errors = [], []
    for t in stamps:
        try:
            frames.append((t, _aligned_delta(avi_a, avi_b, t, cache)))
        except Exception as exc:                    # a short leg, a bad frame
            errors.append(f"t={t}: {str(exc)[:90]}")
    if not frames:
        return {"comparable": False, "errors": errors}

    def worst(key: str) -> float:
        return round(max(f[key] for _, f in frames), 5)

    def mid(key: str) -> float:
        return round(statistics.median(f[key] for _, f in frames), 5)

    return {"comparable": True, "sampled": stamps,
            "seconds_a": round(duration_s(avi_a), 2),
            "seconds_b": round(duration_s(avi_b), 2),
            "frames_compared": len(frames),
            "per_frame": {str(t): f for t, f in frames},
            "max_hist_distance": worst("hist_distance"),
            "median_hist_distance": mid("hist_distance"),
            "max_luma_delta": worst("luma_delta"),
            "median_luma_delta": mid("luma_delta"),
            "max_green_delta": worst("green_delta"),
            "median_green_delta": mid("green_delta"),
            "max_pixel_share": worst("pixel_share"),
            "median_pixel_share": mid("pixel_share"),
            "alignment_frames": [f["aligned_frames"] for _, f in frames],
            "errors": errors}


@dataclass
class CaseResult:
    case: str
    why: str
    moment: dict = field(default_factory=dict)
    verdict: str = "NOT_RUN"
    detail: str = ""
    legs: dict = field(default_factory=dict)
    ab: list = field(default_factory=list)       # A against each B
    control: list = field(default_factory=list)  # each B against each other B
    readings: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"case": self.case, "why": self.why, "verdict": self.verdict,
                "detail": self.detail, "moment": self.moment,
                "legs": self.legs, "readings": self.readings,
                "ab": self.ab, "control": self.control}


# WHY THREE OFFSCREEN CAPTURES AND NOT ONE. With a single control the noise
# floor is one number drawn from a noisy quantity, and the verdict moved
# between runs of this suite: LG and the crowded round came out EQUIVALENT on
# one run and DIFFERENT on the next, on readings around 0.01 where the control
# also sat. Filming B three times gives three A-against-B readings and three
# B-against-B readings, and the question becomes one a reader can check: is A
# further from a B than the Bs are from each other?
REPEATS = 3

# What a reviewer would accept whatever the noise says. A reading above this
# is a difference even if the backend is unstable; a CONTROL above it means
# the case cannot decide anything.
TOLERANCE = {
    "hist": (0.02, "colour distribution"),
    "luma": (3.0, "exposure"),
    "green": (0.01, "the forced enemy on screen"),
    "seconds": (0.25, "clip length"),
}


def _reading(cmp: dict, measure: str) -> float:
    """The median across sampled frames, not the worst.

    The worst of six samples is the noisiest statistic available: one control
    run scored 0.09 on its worst frame and 0.007 on its median. A backend that
    really renders differently moves every frame, so the median is both
    steadier and the thing actually claimed.
    """
    if measure == "seconds":
        return round(abs(cmp["seconds_a"] - cmp["seconds_b"]), 3)
    return cmp[f"median_{ {'hist': 'hist_distance', 'luma': 'luma_delta', 'green': 'green_delta'}[measure] }"]


def run_case(case: Case, *, staging: Path, out_dir: Path,
             repeats: int = REPEATS) -> CaseResult:
    r = CaseResult(case.name, case.why)
    moment = pick(case)
    if moment is None:
        r.verdict = "NO_SUCH_MOMENT"
        r.detail = "the index holds no moment matching this case"
        return r
    # Identity never travels: a hash, a slot and a serverTime describe the
    # moment completely and name nobody.
    r.moment = {k: moment[k] for k in
                ("performance_id", "demo_hash", "client", "kind", "t_ms",
                 "map", "weapon", "outcome")}

    span = (PRE_MS + POST_MS) / 1000.0
    legs: dict[str, dict] = {}
    plan = [("A", O.INTERACTIVE)] + [(f"B{i + 1}", O.DESKTOP_NAME)
                                     for i in range(max(1, repeats))]
    for leg, desktop in plan:
        res = film(moment, label=f"ab_{case.name}_{leg}", desktop=desktop,
                   staging=staging)
        legs[leg] = {"backend": REFERENCE if leg == "A" else OFFSCREEN,
                     "ok": res["ok"], "seconds": res.get("seconds"),
                     "visible_windows": res.get("visible_windows"),
                     "stole_focus": res.get("stole_focus"),
                     "returncode": res.get("returncode"), "avi": res.get("avi")}
        if not res.get("avi"):
            r.legs = legs
            r.verdict = f"{leg}_PRODUCED_NOTHING"
            r.detail = str(res.get("detail") or res.get("missing"))
            return r
    r.legs = legs

    bs = [k for k in legs if k != "A"]
    cache: dict = {}
    r.ab = [dict(compare(Path(legs["A"]["avi"]), Path(legs[b]["avi"]),
                         span_s=span, cache=cache), pair=f"A:{b}")
            for b in bs]
    r.control = [dict(compare(Path(legs[x]["avi"]), Path(legs[y]["avi"]),
                              span_s=span, cache=cache), pair=f"{x}:{y}")
                 for i, x in enumerate(bs) for y in bs[i + 1:]]
    cache.clear()

    if not all(c.get("comparable") for c in r.ab):
        r.verdict = "NOT_COMPARABLE"
        r.detail = "; ".join(e for c in r.ab for e in c.get("errors", []))[:200]
        return r

    # The still is what a human judges: A and the first B, at the frame where
    # they disagree most.
    first = r.ab[0]
    worst = max(first["per_frame"],
                key=lambda t: first["per_frame"][t]["hist_distance"])
    for leg, what in (("A", "reference"), (bs[0], "offscreen")):
        M.save_still(Path(legs[leg]["avi"]), float(worst),
                     out_dir / f"{case.name}_{leg[0]}_{what}.png")
    first["still_at_s"] = float(worst)

    failed, undecidable, said = [], [], []
    usable_control = [c for c in r.control if c.get("comparable")]
    for measure, (tol, what) in TOLERANCE.items():
        ab = max(_reading(c, measure) for c in r.ab)
        ct = (max(_reading(c, measure) for c in usable_control)
              if usable_control else None)
        r.readings[measure] = {"a_vs_b": ab, "b_vs_b": ct, "tolerance": tol}
        if ct is not None and ct > tol:
            undecidable.append(f"{what}: the backend differs from itself by "
                               f"{ct:g}, past the {tol:g} anyone would accept")
        elif ct is not None and ab <= ct:
            said.append(f"{what} {ab:g}, inside the backend's own {ct:g}")
        elif ab <= tol:
            said.append(f"{what} {ab:g} within tolerance {tol:g}"
                        + (f" (its own spread {ct:g})" if ct is not None else ""))
        else:
            failed.append(f"{what}: {ab:g} over tolerance {tol:g}"
                          + (f" and over its own spread {ct:g}" if ct is not None else ""))

    if failed:
        r.verdict, r.detail = "DIFFERENT", "; ".join(failed)
    elif undecidable:
        r.verdict, r.detail = "INCONCLUSIVE", "; ".join(undecidable)
    elif usable_control:
        r.verdict, r.detail = "EQUIVALENT", "; ".join(said)
    else:
        r.verdict, r.detail = "EQUIVALENT_NO_CONTROL", "; ".join(said)
    return r


def run(*, cases: tuple[Case, ...] = CASES, staging: Path | None = None,
        out_dir: Path | None = None, repeats: int = REPEATS) -> dict:
    # The Wolfcam install and the visual record belong to the checkout that
    # owns the data, not to a worktree of the code: a worktree has no engine
    # staged under it, and a still is not a source file.
    staging = staging or (S.PROJECT_ROOT / "output" / "demo_v2" / "_wolfcam_staging")
    out_dir = out_dir or (S.PROJECT_ROOT / "docs" / "visual-record"
                          / time.strftime("%Y-%m-%d") / "backend_ab")
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    results = []
    for i, case in enumerate(cases):
        res = run_case(case, staging=staging, out_dir=out_dir, repeats=repeats)
        results.append(res)
        print(f"{case.name:20s} {res.verdict:22s} {res.detail[:70]}", flush=True)

    verdicts = [r.verdict for r in results]
    passed = {"EQUIVALENT", "EQUIVALENT_NO_CONTROL"}
    report = {
        "what": "backend A/B conformance: WOLFCAM_REFERENCE vs PANTHEON_QUAKE_OFFSCREEN",
        "at": time.strftime("%Y-%m-%d %H:%M"),
        "minutes": round((time.time() - t0) / 60, 1),
        "profile": "REVIEW",
        "window_ms": {"pre": PRE_MS, "post": POST_MS},
        "samples_per_case": SAMPLES,
        "offscreen_captures_per_case": repeats,
        "tolerances": {k: v[0] for k, v in TOLERANCE.items()},
        "diff_threshold": DIFF_THRESHOLD,
        "cases": [r.as_dict() for r in results],
        "equivalent": sum(1 for v in verdicts if v in passed),
        "total": len(results),
        "inconclusive": verdicts.count("INCONCLUSIVE"),
        # A case the comparison could not decide does not license the change
        # on its own, but neither does it block one: what would block it is a
        # difference the offscreen backend can be held responsible for.
        "may_become_default": ("DIFFERENT" not in verdicts
                               and sum(1 for v in verdicts if v in passed) >= 8),
        "stills": str(out_dir),
    }
    dest = (S.REPO_ROOT / "docs" / "reference"
            / f"{time.strftime('%Y-%m-%d')}-backend-ab-conformance.json")
    dest.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"\n{report['equivalent']}/{report['total']} equivalent -> {dest}")
    return report


if __name__ == "__main__":                                   # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description="backend A/B conformance")
    ap.add_argument("--only", nargs="*", help="case names to run")
    ap.add_argument("--repeats", type=int, default=REPEATS,
                    help="offscreen captures per case; 3 gives the backend a "
                         "spread to be judged against")
    a = ap.parse_args()
    chosen = tuple(c for c in CASES if not a.only or c.name in a.only)
    run(cases=chosen, repeats=a.repeats)
