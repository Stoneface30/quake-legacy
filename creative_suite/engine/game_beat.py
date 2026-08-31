"""Derive an episode's rhythm from GAME AUDIO, and pick the song that fits it.

Until now music was chosen from a statistical prior: "the average clip is 13.9 s
long, so find a tempo whose bars divide 13.9 s". That is a guess about pacing
made without listening to the footage.

This listens. Rail shots, lightning hits, rocket explosions, jumps and weapon
switches are all distinct, known sounds -- they ship inside `pak00.pk3` and the
project already extracted them. Template-matching those against a clip's audio
gives the actual times things HAPPEN, and the spacing between those times is the
episode's real rhythm. A song whose bar grid lines up with that rhythm will feel
matched; one chosen from an average will not.

    events        -> onset times per family, per clip
    inter-onset   -> the intervals between consecutive events
    implied tempo -> the BPM whose beat period best divides those intervals
    match         -> score a candidate track against that, not against a prior

Deliberately NOT doing hit-to-beat here. This picks the song; moving a cut onto
an impact is a separate job that needs the A/V sync defect fixed first.

    python -m creative_suite.engine.game_beat --clips <n>
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

SR = 22050
MIN_CORR = 0.32
MERGE_MS = 90          # two detections this close are one event

# The events the user named, plus the feedback hit -- each is a distinct sound
# and each marks a moment an edit could land on.
EVENTS = {
    "rail":       ["weapons/railgun/railgf1a.wav"],
    "shaft_hit":  ["weapons/lightning/lg_hit.wav", "weapons/lightning/lg_hit2.wav"],
    "shaft_fire": ["weapons/lightning/lg_fire.wav"],
    "rocket":     ["weapons/rocket/rocklx1a.wav", "weapons/rocket/rocklf1a.wav"],
    "plasma":     ["weapons/plasma/plasmx1a.wav"],
    "weapon_swap": ["weapons/change.wav"],
    "jump":       ["player/ranger/jump1.wav", "player/major/jump1.wav"],
    "hitsound":   ["feedback/hit.wav", "feedback/hit1.wav"],
    # Grenades have no explosion sound of their own -- the blast reuses the
    # rocket's. The launcher firing and the shell bouncing are what identify a
    # grenade play, and the bounce is the part that makes a second camera worth
    # showing: the shell travels, and the POV cannot see where it lands.
    "grenade":    ["weapons/grenade/grenlf1a.wav",
                   "weapons/grenade/hgrenb1a.wav",
                   "weapons/grenade/hgrenb2a.wav"],
}

# Tempo search range for the implied grid. Wider than the music band on
# purpose: this is the rhythm of the ACTION, and it is then used to choose a
# musical tempo, possibly at half or double time.
TEMPO_LO, TEMPO_HI = 70.0, 190.0


def load_templates():
    import librosa
    out = {}
    for fam, rels in EVENTS.items():
        sigs = []
        for rel in rels:
            p = TROOT / rel
            if not p.exists():
                continue
            try:
                y, _ = librosa.load(str(p), sr=SR, mono=True)
            except Exception:
                continue
            if y.size >= 64:
                sigs.append((rel, y))
        if sigs:
            out[fam] = sigs
    return out


def _match(sig, tmpl, thresh):
    """All normalised-correlation peaks above `thresh`, as times in seconds."""
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
    # collapse runs into single events
    out, last = [], -1e9
    gap = int(SR * MERGE_MS / 1000.0)
    for i in idx:
        if i - last >= gap:
            out.append(float(i) / SR)
            last = i
    return out


def clip_events(clip_path: str, templates) -> dict:
    """Every recognised game event in one clip, by family. Worker process."""
    import numpy as np
    import librosa
    clip = Path(clip_path)
    rec = {"clip": str(clip), "clip_name": clip.name, "events": {},
           "event_count": 0, "duration_s": None, "error": None}
    tmp = Path(os.environ.get("TEMP", ".")) / "_gb_{}.wav".format(os.getpid())
    try:
        r = subprocess.run([str(FFMPEG), "-y", "-v", "error", "-i", str(clip),
                            "-vn", "-ac", "1", "-ar", str(SR), "-f", "wav",
                            str(tmp)], capture_output=True, text=True)
        if r.returncode != 0 or not tmp.exists():
            rec["error"] = "audio extract failed"
            return rec
        y, _ = librosa.load(str(tmp), sr=SR, mono=True)
        rec["duration_s"] = round(y.size / SR, 3)
        for fam, sigs in templates.items():
            times = []
            for _, t in sigs:
                times += _match(y, np.asarray(t), MIN_CORR)
            times.sort()
            merged, last = [], -1e9
            for x in times:
                if x - last >= MERGE_MS / 1000.0:
                    merged.append(round(x, 3))
                    last = x
            if merged:
                rec["events"][fam] = merged
        rec["event_count"] = sum(len(v) for v in rec["events"].values())
    except Exception as exc:                          # noqa: BLE001
        rec["error"] = "{}: {}".format(type(exc).__name__, exc)[:160]
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    return rec


def implied_tempo(all_times):
    """The BPM whose beat period best explains the gaps between events.

    The naive version of this is biased and produced a degenerate answer. Score
    every candidate purely on "how close is each interval to a whole number of
    beats" and a SLOW tempo always wins: a longer beat period means each gap
    spans fewer beats, and fewer beats are easier to land near. Run unguarded it
    pinned to exactly the search floor, 70 BPM, which is not a tempo anyone
    chose -- it is the edge of the range.

    Two corrections:

      * only count an interval when it maps to a SMALL whole number of beats
        (1-4). A gap explained as "11.3 beats" explains nothing.
      * weight by coverage -- the fraction of intervals the grid actually
        explains -- so a tempo that fits three gaps out of forty cannot win.
    """
    import numpy as np
    t = np.array(sorted(all_times), dtype=float)
    if t.size < 4:
        return None, 0.0
    gaps = np.diff(t)
    gaps = gaps[(gaps > 0.08) & (gaps < 6.0)]
    if gaps.size < 3:
        return None, 0.0

    best, best_s = None, -1.0
    for bpm in np.arange(TEMPO_LO, TEMPO_HI + 0.01, 0.5):
        period = 60.0 / bpm
        k = gaps / period
        near = np.round(k)
        usable = (near >= 1) & (near <= 4)            # a gap of 1-4 beats
        if usable.sum() < 3:
            continue
        err = np.abs(k[usable] - near[usable])
        fit = float(np.mean(1.0 - np.clip(err / 0.5, 0, 1)))
        coverage = float(usable.sum()) / float(gaps.size)
        score = fit * (0.35 + 0.65 * coverage)
        if score > best_s:
            best, best_s = float(bpm), score
    return best, round(best_s, 4)


def musical_candidates(bpm):
    """The tempo and its musically equivalent half/double."""
    if not bpm:
        return []
    return [bpm, bpm / 2.0, bpm * 2.0, bpm / 1.5, bpm * 1.5]


def score_track_against_action(track_bpm, action_bpm, action_conf):
    """How well a track's tempo matches the action's implied grid."""
    if not track_bpm or not action_bpm:
        return 0.0
    best = 0.0
    for c in musical_candidates(action_bpm):
        if c <= 0:
            continue
        ratio = track_bpm / c
        # distance to the nearest simple relationship (1:1, 2:1, 1:2)
        d = min(abs(ratio - 1.0), abs(ratio - 2.0) / 2.0,
                abs(ratio - 0.5) / 0.5)
        best = max(best, max(0.0, 1.0 - d / 0.12))
    return round(best * max(0.25, action_conf), 4)


_T = None


def _init(t):
    global _T
    _T = t


def _run(p):
    return clip_events(p, _T)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", type=int, default=40)
    ap.add_argument("--workers", type=int,
                    default=max(2, (os.cpu_count() or 4) // 2))
    ap.add_argument("--out", default=str(REPO_ROOT / "output" / "game_beat.json"))
    a = ap.parse_args()

    tmpl = load_templates()
    if not tmpl:
        print("ERROR: no event templates under {}".format(TROOT))
        return 1
    print("[gamebeat] event families: " + ", ".join(
        "{}({})".format(k, len(v)) for k, v in tmpl.items()), flush=True)

    q = json.loads((REPO_ROOT / "output" / "avi_master_queue.json")
                   .read_text(encoding="utf-8"))["queue"]
    clips = [r["canonical_avi_path"] for r in q][:a.clips]
    print("[gamebeat] analysing {} clip(s)".format(len(clips)), flush=True)

    rows = []
    import numpy as np
    ser = {k: [(n, np.asarray(y, dtype=np.float32)) for n, y in v]
           for k, v in tmpl.items()}
    with ProcessPoolExecutor(max_workers=a.workers, initializer=_init,
                             initargs=(ser,)) as ex:
        futs = {ex.submit(_run, c): c for c in clips}
        for i, f in enumerate(as_completed(futs), 1):
            try:
                rows.append(f.result())
            except Exception as exc:                  # noqa: BLE001
                print("  worker died: {}".format(exc), flush=True)
            if i % 20 == 0:
                print("  {}/{}".format(i, len(clips)), flush=True)

    allt = []
    import collections
    fam = collections.Counter()
    for r in rows:
        for k, v in (r.get("events") or {}).items():
            fam[k] += len(v)
            allt += v
    bpm, conf = implied_tempo(allt)

    payload = {"clips": len(rows), "events_by_family": dict(fam),
               "implied_action_bpm": bpm, "confidence": conf, "items": rows}
    Path(a.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("")
    print("=" * 60)
    print("GAME-AUDIO BEAT PROFILE")
    print("=" * 60)
    for k, n in fam.most_common():
        print("  {:14} {:>6} events".format(k, n))
    print("  total events   {:>6}".format(sum(fam.values())))
    print("")
    if bpm:
        print("  implied action tempo : {:.1f} BPM  (confidence {:.3f})"
              .format(bpm, conf))
        print("  musical equivalents  : " + ", ".join(
            "{:.0f}".format(x) for x in musical_candidates(bpm)))
    else:
        print("  not enough events to imply a tempo")
    print("  wrote {}".format(a.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
