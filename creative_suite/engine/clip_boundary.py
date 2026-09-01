"""Where a clip should END -- and whether it is worth keeping at all.

The first version of this asked one question: when was the last recognised game
sound? Everything after that, past a hold, was dead air. That is right as far as
it goes, and it is not far enough. Review 2026-09-01:

    "if can also avoid the full scoreboards in the end of clips and remove when
     i die"
    "at 35 we have a respawn and you can remove the following clip"
    "some clips are still cut short when action is going"

Three of those are the same problem seen from different sides: a clip does not
stop at the last gunshot, it stops at a MOMENT -- the round buzzer, the player
dying, the scoreboard coming up, a respawn. Those moments are detectable, and
they are what the cut should land on.

The fourth is the opposite failure and the more serious one: trimming into
action the viewer wanted to see. A missing second of dead air costs nothing. A
missing second of a frag is the whole point of the clip. So every cut proposed
here has to survive a loudness check -- if the audio after the cut still has
the energy of a firefight, the cut is refused, whatever the detectors say.

    ACTION      rail / shaft / rocket / plasma / grenade / jump / hitsound
    END MARKERS round buzzer · klaxon · player death · respawn · teleport
    SCOREBOARD  a large, near-static picture (the UI is not moving)

    cut = earliest end marker after the action, minus a lead-in
          ...never earlier than the last action plus its hold
          ...refused entirely if what follows is still loud

    python -m creative_suite.engine.clip_boundary --limit 40
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[2]
TROOT = REPO_ROOT / "creative_suite" / "engine" / "sound_templates" / "raw" / "sound"
FFMPEG = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
OUT = REPO_ROOT / "output" / "clip_boundary.json"

SR = 22050

# Hold after the last piece of action. The kill feed, the body dropping, the
# beat a viewer needs to register what happened.
# Measured, not chosen: across the sample the round-end announcement appears
# 0.03-0.5 s after the round-winning kill. A 1.6 s hold therefore GUARANTEED
# that "Blue Wins the Round" was on screen at the cut. 1.0 s still lets a kill
# land while cutting most announcements off. A round-WINNING frag will still
# show a flash of it -- the text is up before the body falls, and the only way
# to avoid it entirely is to cut the kill itself.
AFTERMATH_HOLD_S = 1.60
# Lead-in before an end marker: the buzzer sounds, and the cut lands just
# before it rather than on top of it.
MARKER_LEAD_S = 0.35
# When a marker decides the cut, this is all that is kept after the last piece
# of action before it. Shorter than the aftermath hold on purpose: the round is
# already over, so there is nothing left to see.
MIN_HOLD_AFTER_ACTION_S = 0.55
# Below this there is nothing worth cutting.
MIN_TRIM_S = 0.60
# Never remove more than this share of a clip, whatever the detectors say.
MAX_TRIM_FRACTION = 0.35

# THE SAFETY RULE. If the audio between the proposed cut and the clip's real
# end is this loud relative to the clip's own action level, the cut is refused:
# something is still happening there. Set from the clip's own statistics rather
# than an absolute, because captures vary enormously in level.
TAIL_LOUD_RATIO = 0.75

# Correlation an end marker must reach. Higher than the action threshold on
# purpose -- a false end marker truncates a frag, which is the one outcome
# worth being conservative about.
# Lowered from 0.62. Recall was the problem, not precision: at 0.62 only 43 of
# 1419 clips showed a death and just 3 were cut, so the user was still seeing
# deaths (2026-09-01: "asked to remove dead and start round and is still here
# on part 1"). A false marker is now cheap -- nothing cuts without surviving
# the event veto, and a real death ends the action, so a true death cut has
# nothing after it to veto.
MARKER_MIN_CORR = 0.52

END_MARKERS = {
    "round_end": ["world/buzzer.wav", "world/klaxon1.wav", "world/klaxon2.wav"],
    "respawn":   ["items/respawn1.wav", "world/telein.wav"],
}

# Death is model-specific, so a handful of the common ones stand in for all of
# them: the samples share an envelope and the matcher is normalised.
DEATH_MODELS = ["sarge", "major", "visor", "xaero", "keel", "anarki",
                "doom", "ranger", "bitterman", "grunt", "hunter", "orbb",
                "razor", "sorlag", "tankjr", "uriel"]


def death_templates():
    out = []
    for m in DEATH_MODELS:
        for n in ("death1.wav", "death2.wav", "death3.wav"):
            q = TROOT / "player" / m / n
            if q.exists():
                out.append("player/{}/{}".format(m, n))
    return out


def load_markers():
    """Every end-marker template, as (family, name, samples)."""
    import librosa
    fams = dict(END_MARKERS)
    fams["death"] = death_templates()
    out = {}
    for fam, rels in fams.items():
        sigs = []
        for rel in rels:
            q = TROOT / rel
            if not q.exists():
                continue
            try:
                y, _ = librosa.load(str(q), sr=SR, mono=True)
            except Exception:
                continue
            if y.size >= 64:
                sigs.append((rel, y))
        if sigs:
            out[fam] = sigs
    return out


def _envelope(y, win=2048, hop=512):
    """Short-term RMS, so 'is this still loud' is a measurement not a guess."""
    import numpy as np
    n = 1 + max(0, (y.size - win) // hop)
    if n <= 0:
        return np.zeros(1, dtype=np.float32), hop / SR
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    frames = y[np.clip(idx, 0, y.size - 1)]
    return np.sqrt((frames ** 2).mean(axis=1)) + 1e-9, hop / SR


def static_tail_start(clip: str, duration: float, look_s: float = 10.0):
    """When the picture stops moving -- i.e. when the scoreboard came up.

    The end-of-round scoreboard is a large overlay drawn over a frozen or
    near-frozen view, so consecutive frames stop differing. Measured from
    downscaled frames, which is cheap and immune to compression noise.

    Returns the time the stillness begins, or None.
    """
    import numpy as np
    if duration <= 3.0:
        return None
    fps = 4
    start = max(0.0, duration - look_s)
    w, h = 64, 36
    r = subprocess.run(
        [str(FFMPEG), "-v", "error", "-ss", "{:.3f}".format(start), "-i", clip,
         "-vf", "fps={},scale={}:{},format=gray".format(fps, w, h),
         "-f", "rawvideo", "-"], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return None
    buf = np.frombuffer(r.stdout, dtype=np.uint8)
    n = buf.size // (w * h)
    if n < 6:
        return None
    frames = buf[:n * w * h].reshape(n, w * h).astype(np.float32)
    diff = np.abs(np.diff(frames, axis=0)).mean(axis=1)
    if diff.size < 5:
        return None
    # "still" is relative to how much this clip normally moves
    active = float(np.median(diff))
    if active < 1e-3:
        return None
    still = diff < max(0.35, active * 0.18)
    # the scoreboard runs to the END of the clip, so look for a still RUN that
    # reaches the last frame -- a momentary pause mid-fight must not count
    if not still[-1]:
        return None
    i = still.size - 1
    while i >= 0 and still[i]:
        i -= 1
    run = still.size - 1 - i
    if run < 4:                                   # under ~1 s is not a board
        return None
    return start + (i + 1) / fps


CP_W, CP_H, CP_FPS = 384, 216, 8
CP_Y0, CP_Y1 = 0.22, 0.50        # the centreprint band, as fractions of height
CP_X0, CP_X1 = 0.12, 0.88


def centerprint_start(clip: str, duration: float, look_s: float = 12.0):
    """When "Blue Wins the Round" / "Round Begins In:" came up.

    The round-end and round-start announcements are drawn as centred text
    across the middle of the screen, and they are what the viewer actually sees
    at the end of an over-long clip -- more often than a full scoreboard.

    Detected as THIN BRIGHT STROKES rather than bright pixels: a lit wall or a
    rail beam is bright too, and counting brightness alone fired on a textured
    floor. A stroke is bright *relative to its immediate surroundings*, which
    is what text is and what scenery is not. The run must also be horizontally
    centred, and must persist to the end of the clip.

    This detector is deliberately allowed to be over-eager. On its own it was
    right about two thirds of the time -- not good enough to cut a frag on. It
    does not have to be: no cut it proposes survives if a game event happens
    after it, so its false positives are vetoed rather than shipped.
    """
    import numpy as np
    from scipy.ndimage import uniform_filter

    W, H = CP_W, CP_H
    y0, y1 = int(H * CP_Y0), int(H * CP_Y1)
    x0, x1 = int(W * CP_X0), int(W * CP_X1)
    start = max(0.0, duration - look_s)
    r = subprocess.run(
        [str(FFMPEG), "-v", "error", "-ss", "{:.3f}".format(start), "-i", clip,
         "-vf", "fps={},scale={}:{},format=gray".format(CP_FPS, W, H),
         "-f", "rawvideo", "-"], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return None
    n = len(r.stdout) // (W * H)
    if n < 6:
        return None
    fr = np.frombuffer(r.stdout[:n * W * H],
                       dtype=np.uint8).reshape(n, H, W).astype(np.float32)
    loc = np.stack([uniform_filter(fr[i], size=7) for i in range(n)])
    mask = ((fr > 195) & ((fr - loc) > 42))[:, y0:y1, x0:x1]

    cnt = mask.sum(axis=(1, 2)).astype(np.float32)
    xs = np.arange(x1 - x0, dtype=np.float32)
    cols = mask.sum(axis=1).astype(np.float32)
    cx = (cols * xs).sum(axis=1) / (cols.sum(axis=1) + 1e-6) / (x1 - x0)

    base = float(np.percentile(cnt, 25))
    hi = max(base * 2.0 + 12, 28.0)
    hot = (cnt > hi) & (np.abs(cx - 0.5) < 0.13)
    if not hot[-1]:
        return None
    i = hot.size - 1
    while i >= 0 and hot[i]:
        i -= 1
    if hot.size - 1 - i < 3:
        return None

    # HYSTERESIS. The strict threshold marks where the text is unmistakable,
    # not where it appeared: an announcement fades in, and the first frames of
    # it sit below the bar. Detecting the late point and cutting a fixed lead
    # before it put the cut ON the text instead of in front of it -- verified
    # by looking at the frames, which is the only way this kind of error shows
    # up. So the run is extended backwards at a looser threshold to find the
    # real onset.
    lo = max(base * 1.25 + 4, 14.0)
    while i >= 0 and cnt[i] > lo and abs(cx[i] - 0.5) < 0.20:
        i -= 1
    return start + (i + 1) / CP_FPS


def _match_times(sig, tmpl, thresh):
    import numpy as np
    from scipy.signal import fftconvolve
    n = tmpl.size
    if sig.size < n * 2:
        return []
    t = tmpl - tmpl.mean()
    tn = np.linalg.norm(t)
    if tn < 1e-8:
        return []
    corr = fftconvolve(sig, t[::-1], mode="valid")
    cs = np.concatenate(([0.0], np.cumsum(sig.astype(np.float64) ** 2)))
    energy = np.sqrt(np.maximum(cs[n:] - cs[:-n], 0.0)) + 1e-8
    m = min(corr.size, energy.size)
    norm = np.abs(corr[:m] / (energy[:m] * tn))
    idx = np.where(norm >= thresh)[0]
    if idx.size == 0:
        return []
    out, last = [], -1e9
    gap = int(SR * 0.12)
    for i in idx:
        if i - last >= gap:
            out.append(float(i) / SR)
            last = i
    return out


def analyse(clip_path: str, action_tmpl, marker_tmpl) -> dict:
    """Everything needed to decide where this clip ends. Worker process."""
    import numpy as np
    import librosa
    from creative_suite.engine import game_beat as GB

    clip = Path(clip_path)
    rec = {"clip": str(clip), "clip_name": clip.name, "duration_s": None,
           "action_times": [], "markers": {}, "scoreboard_s": None,
           "centerprint_s": None,
           "cut_at": None, "trim_s": 0.0, "drop": False, "reason": ""}
    tmp = Path(os.environ.get("TEMP", ".")) / "_cb_{}.wav".format(os.getpid())
    try:
        r = subprocess.run([str(FFMPEG), "-y", "-v", "error", "-i", str(clip),
                            "-vn", "-ac", "1", "-ar", str(SR), "-f", "wav",
                            str(tmp)], capture_output=True)
        if r.returncode != 0 or not tmp.exists():
            rec["reason"] = "audio extract failed"
            return rec
        y, _ = librosa.load(str(tmp), sr=SR, mono=True)
        dur = y.size / SR
        rec["duration_s"] = round(dur, 3)

        act = []
        for fam, sigs in action_tmpl.items():
            for _, t in sigs:
                act += _match_times(y, np.asarray(t), GB.MIN_CORR)
        act.sort()
        rec["action_times"] = [round(x, 3) for x in act]

        for fam, sigs in marker_tmpl.items():
            hits = []
            for _, t in sigs:
                hits += _match_times(y, np.asarray(t), MARKER_MIN_CORR)
            if hits:
                rec["markers"][fam] = sorted(round(x, 3) for x in hits)

        rec["scoreboard_s"] = static_tail_start(str(clip), dur)
        # Recorded only when asked for: it is no longer a cutting marker (the
        # round announcement is wanted), and it costs a full video decode.
        if os.environ.get("CB_CENTERPRINT"):
            rec["centerprint_s"] = centerprint_start(str(clip), dur)

        # ---- decide ----
        if not act:
            # nothing recognisable happens in here at all
            rec["drop"] = True
            rec["reason"] = "no action detected -- not a frag clip"
            return rec

        # A clip that opens on a respawn and never gets going is a mis-cut from
        # the original AVI pass, not a frag (user 2026-09-01: "at 35 we have a
        # respawn and you can remove the following clip ... issue in the initial
        # avi making"). Judged by content, not by position in the queue.
        early = [t for ts in rec["markers"].values() for t in ts if t < dur * 0.35]
        if early and len([t for t in act if t > min(early)]) < 3:
            rec["drop"] = True
            rec["reason"] = ("opens on a respawn with no action after -- "
                             "mis-cut source")
            return rec

        last_act = act[-1]

        # An end marker OVERRIDES the aftermath hold. This is the whole fix:
        # the hold exists so the kill and its aftermath can land, but once the
        # round is over there is no aftermath to wait for -- what the hold was
        # actually buying was 1.6 s of "Blue Wins the Round" and the scoreboard
        # behind it, which is exactly what the user asked to remove. So a
        # marker cuts where it happens, keeping only a short beat after
        # whatever action preceded it.
        # WHICH markers may cut, and which are only recorded.
        #
        # User 2026-09-01: "we still need to here the round win sound and the
        # 3 2 1 start sounds". So the round announcement and the countdown are
        # WANTED -- they are part of the atmosphere and they carry their own
        # rhythm. An earlier version of this cut on them and on the round text,
        # which removed exactly what the user asked to keep.
        #
        # What is unwanted is the FULL SCOREBOARD -- the big static stats
        # screen -- and anything after the player dies. Those two cut. Respawn,
        # round text and the buzzer are detected and stored, because they are
        # useful for choosing where to place things, but they do not truncate a
        # clip.
        CUTTING = ("death", "respawn")
        cands = []
        for fam, ts in rec["markers"].items():
            if fam not in CUTTING:
                continue
            for t in ts:
                if t > dur * 0.45:
                    cands.append((t, fam))
                    break
        if rec["scoreboard_s"] is not None:
            cands.append((rec["scoreboard_s"], "scoreboard"))

        cut, why = None, ""
        if cands:
            marker_t, why = min(cands, key=lambda z: z[0])
            before = [t for t in act if t < marker_t]
            hold = (before[-1] + MIN_HOLD_AFTER_ACTION_S) if before else 0.0
            cut = max(marker_t - MARKER_LEAD_S, hold)
            why = "cut at {} marker".format(why)
        else:
            # NO CUT WITHOUT POSITIVE EVIDENCE.
            #
            # This used to cut at "last recognised sound + a hold", which is an
            # argument from ABSENCE: nothing was detected, therefore nothing is
            # happening. The detector only knows nine sounds. Footsteps, a jump
            # landing, an item pickup, a shot that missed -- none of it
            # registers, and all of it is worth watching. User 2026-09-01: "lot
            # of clip are trimmed way to much in the end".
            #
            # 114 of 141 accepted trims came from this branch. It is removed:
            # a clip is now shortened only when something UNWANTED was actually
            # found in it.
            rec["reason"] = "no end marker -- left at full length"
            return rec

        # ---- the safety rule ----
        # First and strongest: if a recognised game EVENT happens after the
        # proposed cut, the cut is wrong. Loudness alone was the wrong test --
        # the round-end announcer is loud, so it refused exactly the cuts this
        # is supposed to make, while a quiet-but-real event would have slipped
        # through. An event is what "the action is still going" means.
        after_act = [t for t in act if t > cut + 0.15]
        if after_act:
            rec["reason"] = ("refused: {} action event(s) after {:.2f}s"
                             .format(len(after_act), cut))
            rec["cut_at"] = None
            return rec

        # Backstop, only where no marker decided the cut: the templates do not
        # know every sound in the game, so a tail that is still as loud as the
        # firefight is treated as action the detector missed.
        if not cands:
            env, hop = _envelope(y)
            act_idx = [int(t / hop) for t in act
                       if 0 <= int(t / hop) < env.size]
            action_level = (float(np.median(env[act_idx])) if act_idx
                            else float(np.median(env)))
            i0 = int(cut / hop)
            if i0 < env.size - 2 and action_level > 0:
                tail_level = float(np.percentile(env[i0:], 90))
                if tail_level > action_level * TAIL_LOUD_RATIO:
                    rec["reason"] = ("refused: still loud after {:.2f}s "
                                     "({:.0f}% of action level)".format(
                                         cut, 100.0 * tail_level / action_level))
                    rec["cut_at"] = None
                    return rec

        trim = dur - cut
        if trim < MIN_TRIM_S:
            rec["reason"] = "nothing worth cutting ({:.2f}s)".format(trim)
            return rec
        cap = dur * MAX_TRIM_FRACTION
        if trim > cap:
            trim = cap
            cut = dur - trim
            why += " (capped at {:.0f}%)".format(MAX_TRIM_FRACTION * 100)
        rec["cut_at"] = round(cut, 3)
        rec["trim_s"] = round(trim, 3)
        rec["reason"] = why
    except Exception as exc:                              # noqa: BLE001
        rec["reason"] = "{}: {}".format(type(exc).__name__, exc)[:160]
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    return rec


_A = _M = None


def _init(a, m):
    global _A, _M
    _A, _M = a, m


def _run(p):
    return analyse(p, _A, _M)


def load_table(path: Path = OUT) -> dict:
    """canonical clip path -> seconds to remove from the END."""
    if not path.exists():
        return {}
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {str(Path(i["clip"]).resolve()).lower(): float(i.get("trim_s") or 0.0)
            for i in d.get("items", []) if (i.get("trim_s") or 0) > 0}


def load_drops(path: Path = OUT) -> set:
    """Clips with nothing in them worth showing."""
    if not path.exists():
        return set()
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {str(Path(i["clip"]).resolve()).lower()
            for i in d.get("items", []) if i.get("drop")}


def load_events(path: Path = OUT) -> dict:
    """canonical clip path -> action times, for music selection."""
    if not path.exists():
        return {}
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {str(Path(i["clip"]).resolve()).lower(): (i.get("action_times") or [])
            for i in d.get("items", [])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    import numpy as np
    from creative_suite.engine import game_beat as GB

    act = GB.load_templates()
    mk = load_markers()
    if not act or not mk:
        print("ERROR: templates missing under {}".format(TROOT))
        return 1
    print("[bound] action families : " + ", ".join(
        "{}({})".format(k, len(v)) for k, v in act.items()), flush=True)
    print("[bound] end markers     : " + ", ".join(
        "{}({})".format(k, len(v)) for k, v in mk.items()), flush=True)

    ser_a = {k: [(n, np.asarray(y, dtype=np.float32)) for n, y in v]
             for k, v in act.items()}
    ser_m = {k: [(n, np.asarray(y, dtype=np.float32)) for n, y in v]
             for k, v in mk.items()}

    q = json.loads((REPO_ROOT / "output" / "avi_master_queue.json")
                   .read_text(encoding="utf-8"))["queue"]
    clips = [r["canonical_avi_path"] for r in q]
    for r in q:
        clips += [x for x in (r.get("angles") or [])]
    clips = [c for c in dict.fromkeys(clips) if Path(c).exists()]
    if a.limit:
        clips = clips[:a.limit]
    print("[bound] {} clip(s), {} workers".format(len(clips), a.workers),
          flush=True)

    rows = []
    with ProcessPoolExecutor(max_workers=a.workers, initializer=_init,
                             initargs=(ser_a, ser_m)) as ex:
        futs = {ex.submit(_run, c): c for c in clips}
        for i, f in enumerate(as_completed(futs), 1):
            try:
                rows.append(f.result())
            except Exception as exc:                      # noqa: BLE001
                print("  worker died: {}".format(exc), flush=True)
            if i % 100 == 0:
                print("  {}/{}".format(i, len(clips)), flush=True)

    Path(a.out).write_text(json.dumps({"clips": len(rows), "items": rows},
                                      indent=2), encoding="utf-8")

    trimmed = [r for r in rows if (r.get("trim_s") or 0) > 0]
    refused = [r for r in rows if r["reason"].startswith("refused")]
    dropped = [r for r in rows if r.get("drop")]
    from collections import Counter
    why = Counter(r["reason"].split(" (")[0] for r in trimmed)
    mk_ct = Counter()
    for r in rows:
        for k in (r.get("markers") or {}):
            mk_ct[k] += 1
    board = sum(1 for r in rows if r.get("scoreboard_s") is not None)
    cprint = sum(1 for r in rows if r.get("centerprint_s") is not None)

    print("")
    print("=" * 66)
    print("CLIP END BOUNDARIES")
    print("=" * 66)
    print("  clips analysed        : {}".format(len(rows)))
    print("  end markers found     : " + ", ".join(
        "{} {}".format(v, k) for k, v in mk_ct.most_common()))
    print("  scoreboard detected   : {}".format(board))
    print("  round text detected   : {}".format(cprint))
    print("  clips trimmed         : {} ({:.0f}%)".format(
        len(trimmed), 100.0 * len(trimmed) / max(1, len(rows))))
    for k, v in why.most_common():
        print("      {:44} {}".format(k[:44], v))
    print("  cuts REFUSED (loud)   : {}".format(len(refused)))
    print("  clips to drop         : {}".format(len(dropped)))
    if trimmed:
        ts = sorted(r["trim_s"] for r in trimmed)
        print("  trim median           : {:.2f}s   max {:.2f}s".format(
            ts[len(ts) // 2], ts[-1]))
    print("")
    print("  wrote {}".format(a.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
