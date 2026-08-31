"""Beat/tempo analysis of the song library, and episode-aware track selection.

Two jobs:

  ANALYSE   Every song in the library gets a tempo, beat grid, downbeat grid,
            duration and energy profile, cached in SQLite so the work is done
            once. The cache is keyed on file CONTENT, not path, because this
            library holds the same song under several names.

  SELECT    Given an episode's actual clip pacing, pick the track whose bar
            grid best fits it.

The selection objective is the real one, not "a number near 128 BPM": a cut
lands well when it falls on a DOWNBEAT, so the tempo we want is the one where
the episode's mean clip length is close to a whole number of BARS.

    bars = clip_seconds * bpm / 60 / beats_per_bar

A mean clip of 13.9 s at 128 BPM is 7.41 bars -- it drifts off the grid within
two cuts. At 121 BPM it is 7.01 bars, so every cut lands near a bar line and the
edit breathes with the track. That is the whole idea; everything else here is
bookkeeping.

    python -m creative_suite.engine.music_beatmatch --scan --workers 8
    python -m creative_suite.engine.music_beatmatch --report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "creative_suite" / "database" / "music_analysis.db"

AUDIO_EXT = (".mp3", ".ogg", ".wav", ".flac", ".m4a")
BEATS_PER_BAR = 4

# Analysis loads only this much of a track. Tempo is stable across a song, and
# reading 90 s instead of 6 min is the difference between an overnight job and
# a 15-minute one.
ANALYSE_SECONDS = 90.0
SR = 22050


def library_dirs() -> list[Path]:
    return [
        REPO_ROOT / "engine" / "music" / "library",
        REPO_ROOT / "creative_suite" / "engine" / "music" / "library",
        REPO_ROOT / "creative_suite" / "engine" / "music",
    ]


def all_songs() -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for d in library_dirs():
        if not d.is_dir():
            continue
        for q in sorted(d.rglob("*")):
            if q.is_file() and q.suffix.lower() in AUDIO_EXT:
                k = str(q.resolve()).lower()
                if k not in seen:
                    seen.add(k)
                    out.append(q)
    return out


def content_id(path: Path, head: int = 1 << 20) -> str:
    """Identity by content. The library repeats songs under different names."""
    h = hashlib.sha256()
    try:
        size = path.stat().st_size
        h.update(str(size).encode())
        with path.open("rb") as fh:
            h.update(fh.read(head))
    except OSError:
        return ""
    return h.hexdigest()[:24]


# ------------------------------------------------------------------ storage
def connect(db: Path | None = None) -> sqlite3.Connection:
    p = db or DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(p), timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            content_id   TEXT PRIMARY KEY,
            path         TEXT NOT NULL,
            name         TEXT,
            duration_s   REAL,
            bpm          REAL,
            beat_count   INTEGER,
            beat_times   TEXT,
            downbeats    TEXT,
            rms_mean     REAL,
            rms_p90      REAL,
            onset_rate   REAL,
            centroid     REAL,
            analysed_at  TEXT,
            error        TEXT
        )""")
    con.commit()
    return con


def already_analysed(con: sqlite3.Connection) -> set[str]:
    return {r[0] for r in con.execute(
        "SELECT content_id FROM songs WHERE error IS NULL")}


# ----------------------------------------------------------------- analysis
def analyse_one(path_str: str) -> dict:
    """Tempo/beat/energy for one track. Runs in a worker process."""
    import numpy as np
    import librosa

    path = Path(path_str)
    rec = {"path": str(path), "name": path.name, "content_id": content_id(path)}
    try:
        y, sr = librosa.load(path_str, sr=SR, mono=True, duration=ANALYSE_SECONDS)
        if y.size < sr:
            raise ValueError("too short to analyse")

        full = librosa.get_duration(path=path_str)
        onset = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr,
                                               trim=False)
        bpm = float(np.atleast_1d(tempo)[0])
        beat_times = librosa.frames_to_time(beats, sr=sr).tolist()

        # Downbeats: librosa gives no metre, so take every 4th beat. Good enough
        # for choosing a track -- the render's own beat grid does the fine work.
        downs = beat_times[::BEATS_PER_BAR]

        rms = librosa.feature.rms(y=y)[0]
        cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        onset_times = librosa.onset.onset_detect(onset_envelope=onset, sr=sr)

        rec.update({
            "duration_s": float(full),
            "bpm": bpm,
            "beat_count": len(beat_times),
            "beat_times": json.dumps([round(t, 4) for t in beat_times[:2000]]),
            "downbeats": json.dumps([round(t, 4) for t in downs[:600]]),
            "rms_mean": float(np.mean(rms)),
            "rms_p90": float(np.percentile(rms, 90)),
            "onset_rate": float(len(onset_times) / max(1e-6, len(y) / sr)),
            "centroid": float(np.mean(cent)),
            "error": None,
        })
    except Exception as exc:                      # noqa: BLE001 - recorded
        rec.update({"duration_s": None, "bpm": None, "beat_count": None,
                    "beat_times": None, "downbeats": None, "rms_mean": None,
                    "rms_p90": None, "onset_rate": None, "centroid": None,
                    "error": "{}: {}".format(type(exc).__name__, exc)[:300]})
    return rec


def store(con: sqlite3.Connection, rec: dict) -> None:
    import time as _t
    con.execute("""
        INSERT INTO songs (content_id, path, name, duration_s, bpm, beat_count,
                           beat_times, downbeats, rms_mean, rms_p90, onset_rate,
                           centroid, analysed_at, error)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(content_id) DO UPDATE SET
            path=excluded.path, name=excluded.name,
            duration_s=excluded.duration_s, bpm=excluded.bpm,
            beat_count=excluded.beat_count, beat_times=excluded.beat_times,
            downbeats=excluded.downbeats, rms_mean=excluded.rms_mean,
            rms_p90=excluded.rms_p90, onset_rate=excluded.onset_rate,
            centroid=excluded.centroid, analysed_at=excluded.analysed_at,
            error=excluded.error
        """, (rec["content_id"], rec["path"], rec["name"], rec["duration_s"],
              rec["bpm"], rec["beat_count"], rec["beat_times"], rec["downbeats"],
              rec["rms_mean"], rec["rms_p90"], rec["onset_rate"],
              rec["centroid"], _t.strftime("%Y-%m-%d %H:%M:%S"), rec["error"]))
    con.commit()


def scan(limit: int | None, workers: int, db: Path | None = None) -> dict:
    con = connect(db)
    done = already_analysed(con)
    todo = [q for q in all_songs() if content_id(q) not in done]
    if limit:
        todo = todo[:limit]

    print("[music] {} song(s) to analyse ({} already cached), {} workers"
          .format(len(todo), len(done), workers), flush=True)
    ok = bad = 0
    if todo:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(analyse_one, str(q)): q for q in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                try:
                    rec = fut.result()
                except Exception as exc:              # noqa: BLE001
                    print("  [music] worker died: {}".format(exc), flush=True)
                    bad += 1
                    continue
                if not rec.get("content_id"):
                    bad += 1
                    continue
                store(con, rec)
                if rec.get("error"):
                    bad += 1
                else:
                    ok += 1
                if i % 50 == 0:
                    print("  [music] {}/{} analysed".format(i, len(todo)),
                          flush=True)
    n = con.execute("SELECT COUNT(*) FROM songs WHERE error IS NULL").fetchone()[0]
    con.close()
    print("[music] analysed OK {}, failed {}, cache now holds {}"
          .format(ok, bad, n), flush=True)
    return {"ok": ok, "failed": bad, "cached": n}


# ---------------------------------------------------------------- selection
def bar_fit(bpm: float, clip_seconds: float) -> float:
    """1.0 when a clip spans a whole number of bars, 0.0 at the worst offset.

    This is the actual beatmatch criterion: cuts land on bar lines.
    """
    if not bpm or bpm <= 0 or clip_seconds <= 0:
        return 0.0
    bars = clip_seconds * bpm / 60.0 / BEATS_PER_BAR
    off = abs(bars - round(bars))          # 0 .. 0.5
    return max(0.0, 1.0 - off / 0.5)


def load_catalog(db: Path | None = None) -> list[dict]:
    con = connect(db)
    rows = con.execute("""
        SELECT content_id, path, name, duration_s, bpm, rms_mean, rms_p90,
               onset_rate, centroid
        FROM songs WHERE error IS NULL AND bpm > 0
        """).fetchall()
    con.close()
    cols = ("content_id", "path", "name", "duration_s", "bpm", "rms_mean",
            "rms_p90", "onset_rate", "centroid")
    return [dict(zip(cols, r)) for r in rows]


def score_song(song: dict, mean_clip_s: float, min_duration_s: float,
               want_energy: float) -> float:
    """How well this track suits an episode. Higher is better; <0 disqualifies."""
    if song.get("duration_s") and song["duration_s"] < min_duration_s:
        return -1.0                        # too short to cover its stretch

    fit = bar_fit(song["bpm"], mean_clip_s)

    # Tempo sanity: fragmovies live in a band. Outside it, a perfect bar fit is
    # an artefact of a doubled/halved tempo estimate, not a good track.
    bpm = song["bpm"]
    tempo_ok = 1.0 if 90.0 <= bpm <= 180.0 else 0.35

    energy = song.get("rms_p90") or 0.0
    e_score = 1.0 - min(1.0, abs(energy - want_energy) / max(want_energy, 1e-3))

    return 0.60 * fit + 0.25 * tempo_ok + 0.15 * e_score


def pick_for_episode(mean_clip_s: float, min_duration_s: float,
                     used_ids: set[str], count: int = 2,
                     want_energy: float = 0.12,
                     db: Path | None = None) -> list[dict]:
    """Best unused tracks for an episode with this pacing."""
    cat = [s for s in load_catalog(db) if s["content_id"] not in used_ids]
    scored = [(score_song(s, mean_clip_s, min_duration_s, want_energy), s)
              for s in cat]
    scored = [(sc, s) for sc, s in scored if sc >= 0]
    scored.sort(key=lambda z: -z[0])
    out = []
    for sc, s in scored[:count]:
        s = dict(s)
        s["match_score"] = round(sc, 4)
        s["bar_fit"] = round(bar_fit(s["bpm"], mean_clip_s), 4)
        out.append(s)
    return out


# The curated library. 396 tracks the user actually assembled, rather than the
# 1,483 the analyser found -- the wider set is full of promos, spoken word and
# hardtek that has no business under a fragmovie.
CURATED_DIR = REPO_ROOT / "engine" / "music" / "library"

# Tempo band. The old 90-180 window let 172 BPM hardtek win on bar fit alone:
# 44% of the last series sat at 160+ BPM, which is the "too much bpm" the user
# reported. A fragmovie wants drive, not a gabber set.
BPM_MIN, BPM_MAX = 95.0, 140.0

# Two tracks in one video must sit close enough that the cut across the seam
# does not feel like a channel change.
PAIR_BPM_TOLERANCE = 0.06

# A song that plays for less than this in a 5-6 minute video reads as a
# mistake, not as a second track.
MIN_TRACK_PLAY_S = 75.0
# Never discard more than this share of a song to make it fit.
MAX_CUT_FRACTION = 0.60
# How the valid arrangements are compared. Beat coincidence stays the primary
# criterion -- structure decides which arrangements are ALLOWED, not which is
# best -- so a second song has to be worth roughly two points of match to be
# preferred over a single one, and heavy truncation costs a little too.
PAIR_PENALTY = 0.015
CUT_WEIGHT = 0.05        # +-6%


def pick_pair_for_episode(mean_clip_s: float, min_duration_s: float,
                          used_ids: set, want_energy: float = 0.12,
                          db: Path | None = None):
    """Two tracks for one video, chosen to go together.

    Selection happens in two stages for a reason. Picking the two best tracks
    independently gave videos where an 96 BPM soul cut ran into 172 BPM hardtek
    at the seam. Here the FIRST track is chosen on merit, and the second is
    chosen on merit *within the tempo neighbourhood of the first*, so the pair
    holds together.

    Only the curated library is eligible, and only inside the tempo band.
    """
    cat = [c for c in load_catalog(db)
           if c["content_id"] not in used_ids
           and BPM_MIN <= (c.get("bpm") or 0) <= BPM_MAX
           and str(CURATED_DIR).lower() in str(c.get("path", "")).lower()]
    if not cat:
        # curated set exhausted -- widen to the whole analysed library rather
        # than shipping a video with no music at all, but say so
        cat = [c for c in load_catalog(db)
               if c["content_id"] not in used_ids
               and BPM_MIN <= (c.get("bpm") or 0) <= BPM_MAX]
        if cat:
            print("  [beatmatch] curated library exhausted -- widening")
    if not cat:
        return []

    def score(c):
        return score_song(c, mean_clip_s, min_duration_s, want_energy)

    scored = sorted(((score(c), c) for c in cat), key=lambda z: -z[0])
    scored = [(sc, c) for sc, c in scored if sc >= 0]
    if not scored:
        return []

    first = scored[0][1]
    fb = first["bpm"]
    lo, hi = fb * (1 - PAIR_BPM_TOLERANCE), fb * (1 + PAIR_BPM_TOLERANCE)
    near = [(sc, c) for sc, c in scored[1:] if lo <= c["bpm"] <= hi]
    if not near:
        # nothing in the neighbourhood: take the closest tempo instead of the
        # best score, because pairing matters more than a marginal fit
        near = sorted(((sc, c) for sc, c in scored[1:]),
                      key=lambda z: abs(z[1]["bpm"] - fb))[:1]
    out = []
    for sc, c in ([scored[0]] + near[:1]):
        d = dict(c)
        d["match_score"] = round(sc, 4)
        d["bar_fit"] = round(bar_fit(c["bpm"], mean_clip_s), 4)
        out.append(d)
    return out


def action_match_pct(beat_times, action_times, tol_s=0.12):
    """Share of ACTION moments that land on one of the song's beats.

    This is the real matching criterion, replacing the bar-fit prior. Bar fit
    asked "does the average clip length divide into bars" -- a statement about
    an average, not about this footage. This asks the direct question: taking
    the rail shots, shaft hits, rocket blasts and jumps where they actually
    occur, what fraction of them fall on a beat of THIS song?

    The song is never re-timed. Its beat grid is fixed; the score simply
    measures how much of the action already coincides with it, so a video's
    match is a percentage and not a promise of 100%. Slow-motion shifts the
    game audio's rate, so those stretches naturally match less -- that is
    expected, not a defect.
    """
    import bisect
    if not beat_times or not action_times:
        return 0.0
    b = sorted(beat_times)
    hit = 0
    for t in action_times:
        i = bisect.bisect_left(b, t)
        best = 1e9
        for j in (i - 1, i, i + 1):
            if 0 <= j < len(b):
                best = min(best, abs(b[j] - t))
        if best <= tol_s:
            hit += 1
    return hit / float(len(action_times))


def rank_by_action_match(action_times, min_duration_s, used_ids,
                         db: Path | None = None, tol_s=0.12):
    """Every eligible track, ranked by how much of the action lands on its beats.

    Split out of `pick_by_action_match` so a caller that also has to satisfy
    LENGTH constraints can see the whole ranked field instead of just the top
    two. Picking the best-matching pair and only then discovering they cannot
    cover the video without hacking one of them to a stub is how a five-second
    song gets shipped.
    """
    import json as _json
    con = connect(db)
    rows = con.execute("""SELECT content_id, path, name, duration_s, bpm,
                                 beat_times, rms_p90
                          FROM songs WHERE error IS NULL AND bpm > 0""").fetchall()
    con.close()

    cand = []
    for cid, path, name, dur, bpm, beats, rms in rows:
        if cid in used_ids:
            continue
        if not (BPM_MIN <= bpm <= BPM_MAX):
            continue
        if str(CURATED_DIR).lower() not in str(path).lower():
            continue
        if dur and dur < min_duration_s:
            continue
        try:
            bt = _json.loads(beats or "[]")
        except Exception:
            continue
        if not bt:
            continue
        cand.append({"content_id": cid, "path": path, "name": name,
                     "duration_s": dur, "bpm": bpm, "rms_p90": rms,
                     "match_pct": round(action_match_pct(bt, action_times, tol_s), 4)})
    cand.sort(key=lambda c: -c["match_pct"])
    return cand


def plan_for_body(cands, body_s, xfade_s=2.0,
                  min_play_s=MIN_TRACK_PLAY_S,
                  max_cut_frac=MAX_CUT_FRACTION,
                  bpm_tol=PAIR_BPM_TOLERANCE,
                  search=24):
    """Choose ONE or TWO songs that actually fit a body of `body_s` seconds.

    User 2026-08-31: "try to use correct song length / dont cut song too much
    and no 5 sec song", and "overall its 1 or 2 song per video as target is 5/6
    min". Selection used to hand back exactly two tracks ranked purely on beat
    coincidence, and the mux then trimmed whatever was left to the body. When
    the first song nearly covered the video by itself, the second one played
    for a few seconds and read as a mistake.

    Length is therefore a constraint on selection, not an afterthought of the
    mux:

      * one song, if a single track covers the body without discarding more
        than `max_cut_frac` of itself -- the cleanest result, and the one a
        5-6 minute video usually wants
      * otherwise two, where the first plays in full and the second plays the
        remainder. The remainder must be at least `min_play_s` (no stubs) and
        must not throw away more than `max_cut_frac` of the second track
      * the pair stays close in tempo, so the crossfade between them is a
        blend rather than a jolt

    Ranking inside the valid set is by beat coincidence, so the musical choice
    is unchanged -- this only refuses the arrangements that sound broken.
    Returns candidates annotated with `play_s`, or [] when nothing fits.
    """
    if body_s <= 0 or not cands:
        return []
    pool = cands[:max(2, search)]

    def cut_frac(dur, play):
        return 0.0 if not dur else max(0.0, (dur - play) / dur)

    best = None
    # --- one song ---
    for c in pool:
        dur = c.get("duration_s") or 0.0
        if dur < body_s - 0.5:
            continue
        cf = cut_frac(dur, body_s)
        if cf > max_cut_frac:
            continue
        score = -c["match_pct"] + CUT_WEIGHT * cf
        if best is None or score < best[0]:
            best = (score, [dict(c, play_s=round(body_s, 2))])

    # --- two songs ---
    for a in pool:
        da = a.get("duration_s") or 0.0
        if da <= 0 or da >= body_s:
            continue                       # a alone already reaches the end
        rest = body_s - da + xfade_s
        if rest < min_play_s:
            continue                       # second song would be a stub
        lo, hi = a["bpm"] * (1 - bpm_tol), a["bpm"] * (1 + bpm_tol)
        for b in pool:
            if b["content_id"] == a["content_id"]:
                continue
            db_ = b.get("duration_s") or 0.0
            if db_ + 0.5 < rest:
                continue                   # cannot reach the end
            if not (lo <= b["bpm"] <= hi):
                continue
            cf = cut_frac(db_, rest)
            if cf > max_cut_frac:
                continue
            score = (-(a["match_pct"] + b["match_pct"]) / 2.0
                     + PAIR_PENALTY + CUT_WEIGHT * cf)
            if best is None or score < best[0]:
                best = (score, [dict(a, play_s=round(da, 2)),
                                dict(b, play_s=round(rest, 2))])
    return best[1] if best else []


def pick_by_action_match(action_times, min_duration_s, used_ids, count=2,
                         db: Path | None = None, tol_s=0.12):
    """Choose the song whose OWN beat grid best coincides with the action.

    Candidates are still restricted to the curated library and the sane tempo
    band -- a track that matches well but is unlistenable is not a win. Within
    that, ranking is by measured coincidence, and the second track is chosen
    near the first's tempo so the seam between them holds.
    """
    import json as _json
    con = connect(db)
    rows = con.execute("""SELECT content_id, path, name, duration_s, bpm,
                                 beat_times, rms_p90
                          FROM songs WHERE error IS NULL AND bpm > 0""").fetchall()
    con.close()

    cand = []
    for cid, path, name, dur, bpm, beats, rms in rows:
        if cid in used_ids:
            continue
        if not (BPM_MIN <= bpm <= BPM_MAX):
            continue
        if str(CURATED_DIR).lower() not in str(path).lower():
            continue
        if dur and dur < min_duration_s:
            continue
        try:
            bt = _json.loads(beats or "[]")
        except Exception:
            continue
        if not bt:
            continue
        pct = action_match_pct(bt, action_times, tol_s)
        cand.append({"content_id": cid, "path": path, "name": name,
                     "duration_s": dur, "bpm": bpm, "rms_p90": rms,
                     "match_pct": round(pct, 4)})
    if not cand:
        return []
    cand.sort(key=lambda c: -c["match_pct"])
    first = cand[0]
    lo, hi = first["bpm"] * (1 - PAIR_BPM_TOLERANCE), first["bpm"] * (1 + PAIR_BPM_TOLERANCE)
    near = [c for c in cand[1:] if lo <= c["bpm"] <= hi]
    if not near:
        near = sorted(cand[1:], key=lambda c: abs(c["bpm"] - first["bpm"]))
    out = [first] + near[:max(0, count - 1)]
    return out


def detect_drops(path, sr=22050, max_s=420.0):
    """Moments where the track's energy jumps -- drops, entries, breakdowns.

    A slow-motion accent lands best on the music's own structural events, not
    on an arbitrary beat. This finds them the simple way: a rising-energy
    novelty curve over the RMS envelope, with peaks taken where the jump is
    large relative to the track's own variation. No genre assumptions, and it
    degrades to "no drops found" rather than inventing them.
    """
    import numpy as np
    import librosa
    try:
        y, _ = librosa.load(str(path), sr=sr, mono=True, duration=max_s)
    except Exception:
        return []
    if y.size < sr:
        return []
    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    if rms.size < 8:
        return []
    # rising energy only: a drop is a jump UP
    d = np.diff(rms, prepend=rms[0])
    d = np.maximum(d, 0.0)
    if d.max() <= 0:
        return []
    # A first pass at mean + 2.2 sigma with a 1.5 s guard returned 69 "drops"
    # in one four-minute track -- that is not structure, that is every loud
    # bar. A drop is rare and it is a jump against the track's RECENT level,
    # not its global mean, so compare each frame to the ~4 s before it and
    # require a genuinely large excursion.
    win = max(4, int(4.0 * sr / hop))
    kern = np.ones(win) / win
    local = np.convolve(rms, kern, mode="same") + 1e-9
    ratio = rms / local
    thr = max(1.35, float(np.percentile(ratio, 99.0)))
    idx = np.where((ratio >= thr) & (d > 0))[0]
    if idx.size == 0:
        return []
    times = librosa.frames_to_time(idx, sr=sr, hop_length=hop)
    # one drop, not forty frames of one drop -- and drops are seconds apart
    out, last = [], -1e9
    for t in times:
        if t - last >= 6.0:
            out.append(round(float(t), 2))
            last = t
    return out


FULL_GRID_DIR = REPO_ROOT / "output" / "_beat_grids"


def full_grid(path, db: Path | None = None):
    """Beat and downbeat grid for the WHOLE track.

    The ingest analyses only the first ANALYSE_SECONDS (90 s) of every song --
    plenty to establish tempo and to rank tracks, and cheap across a 396-track
    library. It is NOT enough to land an edit: a five-minute video scored by a
    145 s song has no grid past its first ninety seconds, so every accent in
    the back two thirds silently found nothing to land on.

    This analyses the file end to end, once, and caches the result. Cost is a
    few seconds for the one or two tracks a video actually uses, against a
    render measured in tens of minutes.
    """
    import json as _json
    q = Path(path).resolve()
    FULL_GRID_DIR.mkdir(parents=True, exist_ok=True)
    cache = FULL_GRID_DIR / (content_id(q) + ".json")
    if cache.exists():
        try:
            d = _json.loads(cache.read_text(encoding="utf-8"))
            return d.get("beats") or [], d.get("downbeats") or []
        except Exception:
            pass
    try:
        import numpy as np
        import librosa
        y, sr = librosa.load(str(q), sr=SR, mono=True)
        onset = librosa.onset.onset_strength(y=y, sr=sr)
        _tempo, frames = librosa.beat.beat_track(onset_envelope=onset, sr=sr,
                                                 trim=False)
        beats = [round(float(t), 4)
                 for t in librosa.frames_to_time(frames, sr=sr)]
        downs = beats[::BEATS_PER_BAR]
    except Exception:                                  # noqa: BLE001
        # fall back to the truncated cache rather than returning nothing
        b, d, _ = track_grid(q, db)
        return b, d
    cache.write_text(_json.dumps({"beats": beats, "downbeats": downs}),
                     encoding="utf-8")
    return beats, downs


def salient_onsets(path, max_per_min=14.0):
    """The moments in a track a listener would actually point at.

    User 2026-09-01: "all the sync with video can be done with vocals beat or
    any channel/type of match from the music. for example the bell at 28 and
    the bell at 32 land on one."

    That is the right instinct and the beat grid alone cannot express it. A
    downbeat is a position in the metre; a bell, a vocal entry or a synth stab
    is an EVENT, and it is what the ear latches onto. They are found here as
    the strongest peaks in the onset-strength envelope -- deliberately few, so
    what comes back is the handful of moments that stand out rather than every
    note in the track.

    Cached alongside the full beat grid; costs one analysis per track.
    """
    import json as _json
    q = Path(path).resolve()
    FULL_GRID_DIR.mkdir(parents=True, exist_ok=True)
    cache = FULL_GRID_DIR / (content_id(q) + "_onsets.json")
    if cache.exists():
        try:
            return _json.loads(cache.read_text(encoding="utf-8"))
        except Exception:
            pass
    try:
        import numpy as np
        import librosa
        y, sr = librosa.load(str(q), sr=SR, mono=True)
        dur = y.size / sr
        env = librosa.onset.onset_strength(y=y, sr=sr)
        frames = librosa.onset.onset_detect(onset_envelope=env, sr=sr,
                                            backtrack=True)
        if frames.size == 0:
            out = []
        else:
            times = librosa.frames_to_time(frames, sr=sr)
            strength = env[np.clip(frames, 0, env.size - 1)]
            keep = max(4, int(dur / 60.0 * max_per_min))
            idx = np.argsort(strength)[::-1][:keep]
            out = sorted(round(float(times[i]), 3) for i in idx)
    except Exception:                                  # noqa: BLE001
        out = []
    cache.write_text(_json.dumps(out), encoding="utf-8")
    return out


def track_grid(path, db: Path | None = None):
    """(beats, downbeats, drops) for one track, from cache plus drop analysis."""
    import json as _json
    con = connect(db)
    # the cache stores resolved absolute paths; a relative one silently misses
    row = con.execute("SELECT beat_times, downbeats FROM songs WHERE path=?",
                      (str(Path(path).resolve()),)).fetchone()
    if row is None:
        row = con.execute("SELECT beat_times, downbeats FROM songs WHERE name=?",
                          (Path(path).name,)).fetchone()
    con.close()
    beats, downs = [], []
    if row:
        try:
            beats = _json.loads(row[0] or "[]")
            downs = _json.loads(row[1] or "[]")
        except Exception:
            pass
    return beats, downs, detect_drops(path)


def report(db: Path | None = None) -> None:
    con = connect(db)
    n_ok = con.execute("SELECT COUNT(*) FROM songs WHERE error IS NULL").fetchone()[0]
    n_bad = con.execute("SELECT COUNT(*) FROM songs WHERE error IS NOT NULL").fetchone()[0]
    print("cached songs : {} analysed, {} failed".format(n_ok, n_bad))
    rows = con.execute("""SELECT bpm FROM songs
                          WHERE error IS NULL AND bpm > 0""").fetchall()
    con.close()
    if rows:
        b = sorted(r[0] for r in rows)
        print("bpm          : min {:.0f}  median {:.0f}  max {:.0f}".format(
            b[0], b[len(b) // 2], b[-1]))
    for cs in (10.0, 13.9, 18.0):
        picks = pick_for_episode(cs, 180.0, set(), count=3, db=db)
        print("\nmean clip {:.1f}s -> best fits:".format(cs))
        for p in picks:
            print("   {:52} {:6.1f} bpm  fit {:.3f}  score {:.3f}".format(
                p["name"][:52], p["bpm"], p["bar_fit"], p["match_score"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int,
                    default=max(2, (os.cpu_count() or 4) // 2))
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.scan:
        scan(a.limit, a.workers)
    if a.report or not a.scan:
        report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
