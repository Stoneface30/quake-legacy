"""Find the frag impact inside an existing AVI, by matching real game sounds.

This is the V2 blocker. Filename archaeology took clip provenance as far as it
goes (the demo is knowable for ~78% of clips, the frag inside it is not), so the
remaining way to know WHEN the money shot happens is to hear it.

The method is template matching against sounds extracted from the game's own
pak00, not generic loudness. That distinction is the whole point: a waveform
spike is any loud thing -- a jump pad, a door, the music bed. A normalised
cross-correlation peak against `sound/feedback/hit.wav` is the specific noise
Quake Live makes when YOUR shot lands, and nothing else in the mix sounds like
it.

Three cue families, in descending trustworthiness:

    hitsound    sound/feedback/hit*.wav -- fires only when the recorder damages
                someone. The single most valuable cue: it is already
                recorder-scoped by construction.
    impact      weapon_impact/* -- rail and rocket landing
    death       player_death/* -- the kill itself

Confidence is earned by CORROBORATION, never by one loud moment:

    HIGH_AV     >= 2 independent cue families agree within 250 ms
    MEDIUM_AV   one strong templated cue
    LOW_AV      only a broadband transient, no template agreement
    UNRESOLVED  nothing above floor

LOW_AV deliberately does not qualify for hit-to-beat. An anchor that is merely
"something loud happened" would put the cut on the wrong frame, which is worse
than not cutting to the beat at all.

    python -m creative_suite.engine.hit_anchors --limit 20
    python -m creative_suite.engine.hit_anchors --workers 8
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

warnings.filterwarnings("ignore")

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
TEMPLATE_ROOT = REPO_ROOT / "creative_suite" / "engine" / "sound_templates" / "raw" / "sound"
FFMPEG = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"

SR = 22050
CORROBORATION_MS = 250      # two cues this close are the same event
MIN_CORR = 0.30             # normalised correlation floor for a templated cue
STRONG_CORR = 0.45          # a single cue this strong stands on its own

# Templates worth matching, grouped by what they tell us. Kept small on purpose:
# every extra template costs a full correlation pass over every clip.
CUES = {
    "hitsound": ["feedback/hit.wav", "feedback/hit1.wav", "feedback/hit2.wav",
                 "feedback/hit3.wav"],
    "impact": ["feedback/impact1.wav", "feedback/impact2.wav",
               "feedback/impact3.wav"],
}


def _find(rel: str) -> Path | None:
    p = TEMPLATE_ROOT / rel
    return p if p.exists() else None


def load_templates():
    import librosa
    out = {}
    for fam, rels in CUES.items():
        sigs = []
        for rel in rels:
            p = _find(rel)
            if not p:
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


def extract_audio(clip: Path, dst: Path) -> bool:
    r = subprocess.run(
        [str(FFMPEG), "-y", "-v", "error", "-i", str(clip),
         "-vn", "-ac", "1", "-ar", str(SR), "-f", "wav", str(dst)],
        capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 1024


def match(sig, tmpl):
    """Normalised cross-correlation peaks of one template over the signal.

    FFT-based, not direct. A direct O(n*m) correlate over a 14 s clip against a
    5,000-sample template is ~1.5 billion operations PER TEMPLATE, which put the
    full 1,419-clip pass at roughly four hours. fftconvolve computes the same
    quantity in O(n log n); the arithmetic is identical, only the cost changes.
    """
    import numpy as np
    from scipy.signal import fftconvolve

    n = tmpl.size
    if sig.size < n * 2:
        return np.array([]), np.array([])
    t = tmpl - tmpl.mean()
    tn = np.linalg.norm(t)
    if tn < 1e-8:
        return np.array([]), np.array([])

    # correlation == convolution with the reversed kernel
    corr = fftconvolve(sig, t[::-1], mode="valid")
    # local signal energy over the template window, so a loud passage cannot
    # fake a match -- same rolling sum, via cumulative sums
    cs = np.concatenate(([0.0], np.cumsum(sig.astype(np.float64) ** 2)))
    energy = np.sqrt(np.maximum(cs[n:] - cs[:-n], 0.0)) + 1e-8
    m = min(corr.size, energy.size)
    norm = corr[:m] / (energy[:m] * tn)
    return np.abs(norm), np.arange(m) / float(SR)


def analyse(clip_path: str, templates_ser) -> dict:
    """Locate the primary impact in one clip. Runs in a worker process."""
    import numpy as np
    import librosa

    clip = Path(clip_path)
    rec = {"clip": str(clip), "clip_name": clip.name,
           "anchor_ms": None, "anchor_type": None, "confidence": "UNRESOLVED",
           "secondary_anchor_ms": None, "evidence": "", "duration_s": None,
           "cue_detail": []}

    tmp = Path(os.environ.get("TEMP", ".")) / ("_ha_{}.wav".format(os.getpid()))
    try:
        if not extract_audio(clip, tmp):
            rec["evidence"] = "audio extraction failed"
            return rec
        y, _ = librosa.load(str(tmp), sr=SR, mono=True)
        rec["duration_s"] = round(float(y.size) / SR, 3)
        if y.size < SR // 2:
            rec["evidence"] = "audio too short"
            return rec

        hits = []           # (family, time_s, score, which template)
        for fam, sigs in templates_ser.items():
            best = None
            for rel, t in sigs:
                norm, times = match(y, np.asarray(t))
                if norm.size == 0:
                    continue
                i = int(np.argmax(norm))
                s = float(norm[i])
                if best is None or s > best[2]:
                    best = (fam, float(times[i]), s, rel)
            if best and best[2] >= MIN_CORR:
                hits.append(best)

        # A broadband transient is only ever supporting evidence.
        onset_env = librosa.onset.onset_strength(y=y, sr=SR)
        if onset_env.size:
            oi = int(np.argmax(onset_env))
            ot = float(librosa.frames_to_time([oi], sr=SR)[0])
            opk = float(onset_env[oi] / (onset_env.mean() + 1e-8))
        else:
            ot, opk = None, 0.0

        rec["cue_detail"] = [{"family": f, "time_s": round(t, 3),
                              "score": round(s, 3), "template": w}
                             for f, t, s, w in hits]

        if hits:
            hits.sort(key=lambda z: -z[2])
            primary = hits[0]
            agree = [h for h in hits[1:]
                     if abs(h[1] - primary[1]) * 1000 <= CORROBORATION_MS]
            onset_agrees = (ot is not None
                            and abs(ot - primary[1]) * 1000 <= CORROBORATION_MS
                            and opk > 2.0)
            rec["anchor_ms"] = int(primary[1] * 1000)
            rec["anchor_type"] = primary[0]
            if agree:
                rec["confidence"] = "HIGH_AV"
                rec["evidence"] = ("{} + {} agree within {} ms".format(
                    primary[0], ",".join(a[0] for a in agree),
                    CORROBORATION_MS))
                rec["secondary_anchor_ms"] = int(agree[0][1] * 1000)
            elif primary[2] >= STRONG_CORR and onset_agrees:
                rec["confidence"] = "HIGH_AV"
                rec["evidence"] = ("{} corr {:.2f} with a coincident "
                                   "transient".format(primary[0], primary[2]))
            elif primary[2] >= STRONG_CORR:
                rec["confidence"] = "MEDIUM_AV"
                rec["evidence"] = "{} corr {:.2f}, uncorroborated".format(
                    primary[0], primary[2])
            else:
                rec["confidence"] = "MEDIUM_AV"
                rec["evidence"] = "{} corr {:.2f}".format(primary[0], primary[2])
        elif ot is not None and opk > 3.0:
            rec["anchor_ms"] = int(ot * 1000)
            rec["anchor_type"] = "transient_only"
            rec["confidence"] = "LOW_AV"
            rec["evidence"] = ("broadband transient {:.1f}x mean, no template "
                               "agreement -- NOT safe for hit-to-beat"
                               .format(opk))
        else:
            rec["evidence"] = "no cue above floor"
    except Exception as exc:                         # noqa: BLE001 - recorded
        rec["evidence"] = "error: {}: {}".format(type(exc).__name__, exc)[:180]
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    return rec


_TEMPLATES = None


def _init(payload):
    global _TEMPLATES
    _TEMPLATES = payload


def _run(path):
    return analyse(path, _TEMPLATES)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", default=str(REPO_ROOT / "QUAKE VIDEO"))
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "output"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int,
                    default=max(2, (os.cpu_count() or 4) // 2))
    ap.add_argument("--tiers", nargs="*", default=["T1", "T2"])
    a = ap.parse_args()

    tmpl = load_templates()
    if not tmpl:
        print("ERROR: no sound templates found under {}".format(TEMPLATE_ROOT))
        return 1
    print("[anchors] templates: " + ", ".join(
        "{} x{}".format(k, len(v)) for k, v in tmpl.items()), flush=True)

    clips = []
    root = Path(a.clips)
    for tier in a.tiers:
        for part in range(1, 13):
            d = root / tier / "Part{}".format(part)
            if d.exists():
                clips += sorted(d.rglob("*.avi"))
    if a.limit:
        clips = clips[:a.limit]
    print("[anchors] {} clip(s) to analyse, {} workers".format(len(clips),
                                                               a.workers),
          flush=True)

    rows = []
    ser = {k: [(rel, y.tolist()) for rel, y in v] for k, v in tmpl.items()}
    import numpy as np
    ser = {k: [(rel, np.asarray(y, dtype=np.float32)) for rel, y in v]
           for k, v in ser.items()}

    with ProcessPoolExecutor(max_workers=a.workers, initializer=_init,
                             initargs=(ser,)) as ex:
        futs = {ex.submit(_run, str(q)): q for q in clips}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                rows.append(fut.result())
            except Exception as exc:                 # noqa: BLE001
                print("  [anchors] worker died: {}".format(exc), flush=True)
            if i % 50 == 0:
                print("  [anchors] {}/{}".format(i, len(clips)), flush=True)

    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = ["clip", "clip_name", "duration_s", "anchor_ms", "anchor_type",
            "confidence", "secondary_anchor_ms", "evidence"]
    with (out_dir / "hit_anchors.csv").open("w", newline="",
                                            encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    (out_dir / "hit_anchors.json").write_text(
        json.dumps({"total": len(rows), "items": rows}, indent=2),
        encoding="utf-8")

    import collections
    c = collections.Counter(r["confidence"] for r in rows)
    print("")
    print("=" * 62)
    print("AUDIOVISUAL HIT ANCHORS")
    print("=" * 62)
    for k in ("EXACT_METADATA", "HIGH_AV", "MEDIUM_AV", "LOW_AV", "UNRESOLVED"):
        n = c.get(k, 0)
        print("  {:15} {:>5}  {:5.1f}%".format(k, n,
                                               100.0 * n / max(1, len(rows))))
    usable = c.get("EXACT_METADATA", 0) + c.get("HIGH_AV", 0)
    print("")
    print("  hit-to-beat usable (EXACT+HIGH): {}/{}  {:.1f}%".format(
        usable, len(rows), 100.0 * usable / max(1, len(rows))))
    print("  {}".format(out_dir / "hit_anchors.csv"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
