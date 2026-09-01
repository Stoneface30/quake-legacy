"""Render the historical T1/T2 AVI library as ONE continuous PartNN series.

There are no episodes. A single master queue walks the historical source Parts
in order, and output Parts are numbered continuously across them: when
historical Part 1 runs out mid-video, that same output Part simply continues
into historical Part 2.

Packing rule, and it is the whole design: take complete clips in queue order,
keep adding while the Part stays near five minutes, and when the next COMPLETE
clip would push it too long, that clip goes forward to the next Part untouched.
A frag is never chopped to hit a running time.

    output/series/Part01.mp4, Part02.mp4, ...

Safety carried over from V1, because each one was learned from a real failure:

  * one writer only -- a PID lock, and a second process fails loudly
  * per-Part work directory -- a shared one made Part N reuse Part N-1's
    cached seg000.mov and ship footage it never selected
  * clips are consumed only after the Part passes audio AND decode QA
  * coverage is reconciled from manifests plus the queue, never from a counter

    python hl_series.py
    python hl_series.py --status
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "output"

# Video output and the big transient work directories live on a roomier drive.
# G: was down to ~120 GB with the frozen V1 archive occupying 55 GB of it, and
# the series needs comparable space; D: has ~670 GB. Manifests, the queue and
# every audit artifact stay with the repo on G: -- they are small and belong
# next to the code that produced them. Override with QL_SERIES_DIR.
SERIES = Path(os.environ.get("QL_SERIES_DIR",
                             r"D:\QUAKE_LEGACY_OUTPUT\series"))
WORKROOT = Path(os.environ.get("QL_WORK_DIR",
                               r"D:\QUAKE_LEGACY_OUTPUT\work"))
# Manifests are per-RUN. A regeneration writes to its own directory so the
# finished series' records stay intact and coverage for the two runs can never
# be confused with each other.
MANIFESTS = Path(os.environ.get("QL_MANIFEST_DIR", str(OUT / "_series_manifests")))
BROKEN = Path(os.environ.get("QL_BROKEN_DIR", str(OUT / "_series_broken")))
LOCK = Path(os.environ.get("QL_LOCK", str(OUT / "_hl_series.lock")))
QUEUE = OUT / "avi_master_queue.json"

FFMPEG = ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
FFPROBE = ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffprobe.exe"

TP_CEILING_DBTP = -1.0

# Packing bounds around the ~5 min target, applied to the BODY (intro + outro
# add ~18 s). Soft by design: below the floor we keep adding, above it a clip
# is only taken if it still fits under the ceiling.
# Calibrated against Parts 01-04 rather than assumed. Even with a slow-mo
# aware estimate the finished Parts ran 0.95x to 1.40x their predicted body
# (aggregate 1.149) -- accents and beat-snapping move a clip's real screen time
# more than any static model captures. Targeting 245 s of estimated body puts
# the CENTRE of that spread at roughly a five-minute finished Part, inside the
# 4-6 minute editorial goal. The spread itself remains; a Part landing at 4:15
# or 6:30 is expected and is not a defect, because a whole clip is always worth
# more than a tidy running time.
BODY_TARGET_S = 245.0
# The hard finished-duration window. Enforced at commit, not hoped for.
# Windows exit codes that mean "the OS is shutting you down", not "the render
# failed": STATUS_CONTROL_C_EXIT and STATUS_DLL_INIT_FAILED_LOGOFF.
SHUTDOWN_EXITS = frozenset({0xC000013A - (1 << 32), 0xC000026B - (1 << 32),
                            3221225786, 3221226091})
PART_MIN_S = 300.0
PART_MAX_S = 360.0
BODY_FLOOR = 0.88
BODY_CEIL = 1.12

# Measured mean T1/T2 clip length; the bar-grid prior for track selection.
LIBRARY_MEAN_CLIP_S = 13.9

RUNAWAY_PARTS = 400

# Implied tempo of the footage itself, measured from game audio (rail, shaft,
# rocket, jump, weapon swap). Loaded if game_beat has been run; a low
# confidence means it is ignored.
def _load_action_tempo():
    p = OUT / "game_beat.json"
    if not p.exists():
        return None, 0.0
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d.get("implied_action_bpm"), float(d.get("confidence") or 0.0)
    except Exception:
        return None, 0.0


ACTION_BPM, ACTION_CONF = _load_action_tempo()


# ------------------------------------------------------------- single writer
def _pid_alive(pid: int) -> bool:
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-Process -Id {} -ErrorAction SilentlyContinue) -ne $null"
             .format(pid)], capture_output=True, text=True,
            timeout=30).stdout.strip()
        return out.lower().startswith("true")
    except Exception:
        return False


def acquire_lock(run_id: str) -> None:
    if LOCK.exists():
        try:
            held = json.loads(LOCK.read_text(encoding="utf-8"))
        except Exception:
            held = {}
        pid = int(held.get("pid", -1))
        if pid > 0 and _pid_alive(pid):
            raise SystemExit(
                "FATAL: series lock held by PID {} (run {}). Exactly one writer "
                "is allowed against {}. Stop it, or delete {} if it is dead."
                .format(pid, held.get("run_id"), SERIES, LOCK))
        print("[lock] stale lock from dead PID {} -- reclaiming".format(pid))
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps({"pid": os.getpid(), "run_id": run_id,
                                "started": time.strftime("%Y-%m-%d %H:%M:%S")},
                               indent=2), encoding="utf-8")


def release_lock() -> None:
    try:
        LOCK.unlink()
    except OSError:
        pass


def canonical(p) -> str:
    return str(Path(p).resolve()).lower()


def atomic_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    os.replace(tmp, path)


# ------------------------------------------------------------------------ QA
def probe_duration(path: Path) -> float:
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def audio_qa(path: Path):
    """(LUFS, LRA, TRUE PEAK dBTP, pass) measured on the ENCODED file.

    ebur128 prints a running "I:" for every window starting at -70 before it has
    data; the integrated value is the LAST match, never the first.
    """
    r = subprocess.run([str(FFMPEG), "-v", "info", "-i", str(path),
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    peaks = [float(x) for x in re.findall(r"Peak:\s+(-?\d+\.?\d*)", txt)]
    lufs_all = re.findall(r"I:\s+(-?\d+\.?\d*)\s+LUFS", txt)
    lra_all = re.findall(r"LRA:\s+(-?\d+\.?\d*)\s+LU", txt)
    lufs = float(lufs_all[-1]) if lufs_all else None
    lra = float(lra_all[-1]) if lra_all else None
    tp = max(peaks) if peaks else None
    return lufs, lra, tp, (tp is not None and tp <= TP_CEILING_DBTP)


def enforce_true_peak(out: Path, tp):
    """Bring an over-ceiling Part under the ceiling by MEASURED static gain.

    Limiting alone does not get there -- alimiter has an attack time and this
    material is all fast transients, so pushing it harder squashes the very hits
    the edit is built on. A pure gain change has no such artefact and the amount
    is measured rather than guessed.

    It has to LOOP, though, and that is what Part26 taught. A single open-loop
    step from -0.60 dBTP with -1.00 dB of gain came back at -0.80, not -1.60:
    re-encoding AAC to AAC gives roughly 0.2-0.3 dB of inter-sample peak back on
    transient-heavy material. Measured on that exact file, a further -1.50 dB
    moved it -0.8 -> -2.1, so the correction is sound and only the open loop was
    wrong. Now each pass re-measures and another runs if it is still over.

    Passes are capped at three because every pass is another AAC generation;
    beyond that the right answer is to fail the Part, not to keep squashing it.
    Video is stream-copied throughout, so a pass costs seconds.
    """
    if tp is None or tp <= TP_CEILING_DBTP:
        return None
    lufs = lra = None
    ok = False
    for attempt in range(1, 4):
        # 1.2 dB of headroom, not 0.6: enough to absorb the AAC give-back in one
        # pass for the common case.
        gain = TP_CEILING_DBTP - tp - 1.2
        tmp = out.with_name(out.stem + "_tpfix.mp4")
        print("  [tp] pass {}: {} at {:.2f} dBTP -- applying {:.2f} dB"
              .format(attempt, out.name, tp, gain), flush=True)
        r = subprocess.run([str(FFMPEG), "-y", "-v", "error", "-i", str(out),
                            "-af", "volume={:.2f}dB".format(gain),
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                            "-movflags", "+faststart", str(tmp)],
                           capture_output=True, text=True)
        if r.returncode != 0 or not tmp.exists():
            print("  [tp] correction failed: {}".format(r.stderr[-200:]),
                  flush=True)
            try:
                tmp.unlink()
            except OSError:
                pass
            return None
        os.replace(tmp, out)
        lufs, lra, tp, ok = audio_qa(out)
        print("  [tp] pass {} -> {:.2f} dBTP  {}".format(
            attempt, tp if tp is not None else float("nan"),
            "PASS" if ok else "still over"), flush=True)
        if ok:
            break
    return lufs, lra, tp, ok


def decode_qa(path: Path):
    r = subprocess.run([str(FFMPEG), "-v", "error", "-xerror", "-i", str(path),
                        "-f", "null", "-"], capture_output=True, text=True)
    err = r.stderr.strip()
    if r.returncode != 0 or err:
        return False, (err[-400:] or "exit {}".format(r.returncode))
    if probe_duration(path) <= 1.0:
        return False, "video duration too short"
    a = subprocess.run([str(FFPROBE), "-v", "error", "-select_streams", "a:0",
                        "-show_entries", "stream=codec_name", "-of",
                        "csv=p=0", str(path)],
                       capture_output=True, text=True).stdout.strip()
    if not a:
        return False, "no audio stream"
    return True, ""


# --------------------------------------------------------------- coverage
def load_queue():
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    return data["queue"], data


def committed():
    """canonical clip path -> PartNN, from committed manifests only."""
    used = {}
    parts = []
    if not MANIFESTS.exists():
        return used, parts
    for m in sorted(MANIFESTS.glob("Part*.json")):
        try:
            rec = json.loads(m.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not rec.get("committed"):
            continue
        parts.append(rec)
        for c in rec["clips"]:
            used[canonical(c["path"])] = rec["part"]
    return used, parts


def sha_head(path: Path, limit: int = 4 << 20) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            h.update(fh.read(limit))
    except OSError:
        return ""
    return h.hexdigest()[:16]


STEMS = Path(os.environ.get("QL_STEMS_DIR",
                            r"D:\QUAKE_LEGACY_OUTPUT\stems"))


def preserve_game_stem(part: int, work: Path) -> bool:
    """Keep the game-audio-only track before the work dir is reclaimed.

    Without this a remix is a full re-render. The finished mp4 carries ONE
    stream where game and music are already summed at fixed gains and then run
    through loudnorm in dynamic mode -- time-varying gain, so the mix cannot be
    reliably inverted and the stems are gone for good.

    body.mov holds the picture plus the GAME audio alone, before music is muxed
    in. Saving just its audio as FLAC costs a few tens of MB per Part instead of
    the ~700 MB of the whole intermediate, and it is lossless, so a later remix
    at a different game/music balance is a stream-copy of the finished video
    plus a fresh mix -- seconds, not half an hour.
    """
    body = work / "body.mov"
    if not body.exists():
        return False
    STEMS.mkdir(parents=True, exist_ok=True)
    dst = STEMS / "Part{:02d}_game.flac".format(part)
    r = subprocess.run([str(FFMPEG), "-y", "-v", "error", "-i", str(body),
                        "-vn", "-c:a", "flac", "-compression_level", "5",
                        str(dst)], capture_output=True, text=True)
    return r.returncode == 0 and dst.exists()


def reclaim(work: Path) -> float:
    if not work.exists():
        return 0.0
    n = 0
    for f in work.rglob("*"):
        if f.is_file():
            try:
                n += f.stat().st_size
            except OSError:
                pass
    try:
        shutil.rmtree(work)
    except OSError:
        return 0.0
    return n / 1e9


# ----------------------------------------------------------------- packing
# Mirrors render_highlight: an accent fires on every Nth T1 clip, and on ANY
# clip short enough to be almost entirely money shot. The slowed window plays at
# SLOW_RATE, so a slowed clip occupies materially more screen time than its
# source length.
SLOWMO_EVERY_N = 3
SHORT_CLIP_SLOWMO_S = 7.0
SLOW_RATE = 0.45
# Only the window around the action is slowed, not the whole clip. Measured
# against Parts 01-03: modelling roughly a third of a slowed clip at SLOW_RATE
# reproduces their finished durations.
SLOW_WINDOW_FRACTION = 0.33


def slowmo_aware_estimate(r, index_in_part: int) -> float:
    """Screen time this clip will actually occupy, accents included.

    Packing on raw source length was the reason Part03 finished at 7:42 while
    its body estimate said 5.06 min: ten of its twenty-two clips were slowed and
    nothing in the estimate knew that. The body estimate itself was only 4% off
    -- the miss was entirely slow-motion.
    """
    base = r.get("final_rendered_duration_estimate_s") or 0.0
    if base <= 0:
        return 0.0
    dur = r.get("duration_s") or base
    slowed = (dur <= SHORT_CLIP_SLOWMO_S
              or (r.get("tier") == "T1" and index_in_part % SLOWMO_EVERY_N == 0))
    if not slowed:
        return base
    win = base * SLOW_WINDOW_FRACTION
    return (base - win) + win / SLOW_RATE


PLAN = OUT / "part_plan.json"
_PLAN_CACHE = None


def plan_rows(part_no, queue, used):
    """The clips this Part is supposed to contain, from the global plan.

    The greedy walk this replaces is what produced 8:02 Parts: it stepped
    through the queue in order and stopped at a threshold computed from an
    estimate that was wrong by up to 78%. The plan is solved GLOBALLY instead --
    all 1076 clips as one pool, each in exactly one Part, every Part predicted
    inside 5:00-6:00 before a frame is rendered. Historical T1/T2 folders are
    provenance only; a planned Part draws from six to twelve of them.

    Returns (rows, predicted_seconds), or (None, 0.0) when there is no plan.
    """
    global _PLAN_CACHE
    if _PLAN_CACHE is None:
        try:
            _PLAN_CACHE = {r["part"]: r for r in
                           json.loads(PLAN.read_text(encoding="utf-8"))["parts"]}
        except Exception as exc:                       # noqa: BLE001
            print("  [plan] unavailable ({}) -- greedy fallback".format(exc))
            _PLAN_CACHE = {}
    entry = _PLAN_CACHE.get(part_no)
    if not entry:
        return None, 0.0
    by_key = {canonical(r["canonical_avi_path"]): r for r in queue}
    rows = [by_key[canonical(x)] for x in entry["paths"]
            if canonical(x) in by_key and canonical(x) not in used]
    if not rows:
        return None, 0.0
    return rows, float(entry.get("pred_s") or 0.0)


def pack(remaining):
    """Take complete clips until the Part sits near five minutes.

    Below the floor we add unconditionally. Above it, a clip is taken only if
    it still fits under the ceiling; otherwise it goes forward WHOLE. The last
    Part simply takes whatever is left, however short.
    """
    picked, total = [], 0.0
    for i, r in enumerate(remaining):
        est = slowmo_aware_estimate(r, i)
        if picked and total >= BODY_TARGET_S * BODY_FLOOR:
            if total + est > BODY_TARGET_S * BODY_CEIL:
                break
        picked.append(r)
        total += est
        if total >= BODY_TARGET_S * BODY_CEIL:
            break
    return picked, total


def action_timeline(rows):
    """Where the action happens across this Part, in finished-video seconds.

    Each clip's game events are cached from the tail-trim scan (the detection is
    the expensive step and it already ran). Laying the clips end to end and
    offsetting each clip's events by its start position gives the moments the
    edit will actually contain -- which is what a song has to coincide with.

    Positions are approximate: crossfades overlap seams and slow-motion stretches
    a segment. That is fine. This picks a song, and the score it produces is
    reported as a percentage precisely because it is not exact.
    """
    # Prefer the boundary scan's events: same detector, but it covers the whole
    # corpus and is the same data the trim decisions were made from, so the
    # music is matched against exactly the action the edit will contain.
    ev_map = {}
    try:
        from creative_suite.engine.clip_boundary import load_events as _cb_events
        ev_map = _cb_events()
    except Exception:
        ev_map = {}
    if not ev_map:
        from creative_suite.engine.tail_trim import load_events
        ev_map = load_events()
    if not ev_map:
        return []
    out, t = [], 0.0
    for r in rows:
        key = str(Path(r["canonical_avi_path"]).resolve()).lower()
        d = r.get("final_rendered_duration_estimate_s") or 0.0
        for x in ev_map.get(key, []):
            if x <= d:
                out.append(t + x)
        t += d
    out.sort()
    return out


# What the music actually has to cover. `pack()` estimates the BODY -- the sum
# of clip lengths -- but the finished video is longer: slow-mo accents stretch
# it, the opener and closer are added, and the seam crossfades shave a little
# back. Measured on Part01: 267s of clips -> 295s of video. The music target is
# deliberately set a touch above that, because running the music SHORT ends the
# video in silence, while running it long only means the last song is trimmed a
# few seconds earlier.
MUSIC_BODY_GROWTH = 1.08
MUSIC_BOOKEND_S = 20.0


def choose_music(part: int, claimed: set, count: int = 2, rows=None,
                 body_s: float | None = None):
    """Pick the song whose OWN beat grid coincides most with this Part's action.

    User 2026-08-31: "we dont use fix bpm we use the song bpm that has the most
    % match with the clip actions without changing speed of sound."

    So there is no target tempo any more. Every curated track in the sane band
    is scored by what fraction of this Part's rail shots, shaft hits, rocket
    blasts, jumps and weapon switches land within 120 ms of one of its beats,
    and the best-scoring track wins. Playback speed is never altered.

    The second track is chosen near the first's tempo so the seam between them
    is not a jolt. If the action cache is missing the old bar-fit pairing is
    used, and that is stated rather than hidden.
    """
    from creative_suite.engine import music_beatmatch as MB
    out = []
    try:
        acts = action_timeline(rows or [])
        if acts and body_s:
            # Rank on beat coincidence, then let LENGTH decide how many songs
            # this video gets. A five-minute video that one song covers should
            # get one song; the second track exists to finish the video, not to
            # appear for five seconds (user 2026-08-31).
            cands = MB.rank_by_action_match(acts, min_duration_s=60.0,
                                            used_ids=set(claimed))
            pair = MB.plan_for_body(cands, body_s)
            if not pair:
                print("  [match] no arrangement fits {:.0f}s without hacking a "
                      "song -- falling back to best two".format(body_s),
                      flush=True)
                pair = MB.pick_by_action_match(acts, min_duration_s=150.0,
                                               used_ids=set(claimed),
                                               count=count)
            for c in pair:
                play = c.get("play_s")
                print("  [match] {:42} {:6.1f} bpm   {:.1f}% of action on beat"
                      "   plays {}"
                      .format(Path(c["path"]).name[:42], c["bpm"],
                              c["match_pct"] * 100,
                              "{:.0f}s of {:.0f}s".format(play, c["duration_s"] or 0)
                              if play else "full"), flush=True)
        elif acts:
            pair = MB.pick_by_action_match(acts, min_duration_s=150.0,
                                           used_ids=set(claimed), count=count)
            for c in pair:
                print("  [match] {:42} {:6.1f} bpm   {:.1f}% of action on beat"
                      .format(Path(c["path"]).name[:42], c["bpm"],
                              c["match_pct"] * 100), flush=True)
        else:
            print("  [match] no cached action events -- falling back to bar fit",
                  flush=True)
            pair = MB.pick_pair_for_episode(mean_clip_s=LIBRARY_MEAN_CLIP_S,
                                            min_duration_s=150.0,
                                            used_ids=set(claimed))
        for c in pair:
            q = Path(c["path"])
            if q.exists():
                claimed.add(c["content_id"])
                out.append((q, c))
    except Exception as exc:                          # noqa: BLE001
        print("  [music] selection failed ({})".format(exc), flush=True)
    return out


# ------------------------------------------------------------------- render
def render_part(part: int, rows, music, run_id: str):
    SERIES.mkdir(parents=True, exist_ok=True)
    out = SERIES / "Part{:02d}.mp4".format(part)
    work = WORKROOT / "Part{:02d}".format(part)
    qf = MANIFESTS / "_queue_Part{:02d}.json".format(part)
    raw = MANIFESTS / "_raw_Part{:02d}.json".format(part)
    log = OUT / "series_Part{:02d}.log".format(part)
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    qf.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    if raw.exists():
        raw.unlink()

    cmd = [sys.executable, "-u", "-m",
           "creative_suite.engine.render_highlight",
           "--part", str(rows[0]["historical_source_part"]),
           "--minutes", str(BODY_TARGET_S / 60.0),
           "--episode", str(part),
           "--out", str(out), "--manifest", str(raw),
           "--queue", str(qf), "--work", str(work)]
    if music:
        cmd += ["--music", "|".join(str(q) for q, _ in music)]

    print("===== Part{:02d}  ({} clips, hist parts {}) =====".format(
        part, len(rows),
        sorted({r["historical_source_part"] for r in rows})), flush=True)
    t0 = time.time()
    with log.open("w", encoding="utf-8", errors="replace") as fh:
        p = subprocess.run(cmd, cwd=str(ROOT), stdout=fh,
                           stderr=subprocess.STDOUT)
    took = (time.time() - t0) / 60.0
    if p.returncode != 0 or not out.exists() or not raw.exists():
        if p.returncode in SHUTDOWN_EXITS:
            # The OS is tearing this process tree down -- a logoff, a restart,
            # a console interrupt. Nothing is wrong with the render, and
            # spending a retry on it just burns the budget and declares the
            # series INCOMPLETE for no reason. Seen 2026-09-01: a machine
            # restart killed Part18 twice with 0xC000013A then 0xC000026B, and
            # the run stopped at 17 of 51 Parts with nothing actually broken.
            print("  RENDER INTERRUPTED BY SHUTDOWN (exit 0x{:08X}) -- not a "
                  "render failure; resume picks this Part up again"
                  .format(p.returncode & 0xFFFFFFFF), flush=True)
            raise SystemExit(0)
        print("  RENDER FAILED (exit {}) -- see {}".format(p.returncode,
                                                           log.name), flush=True)
        return False, out, None, took, work
    return True, out, json.loads(raw.read_text(encoding="utf-8")), took, work


def commit(part, out: Path, rec, rows, music, run_id, took, already):
    dur = probe_duration(out)
    lufs, lra, tp, ok_a = audio_qa(out)
    if not ok_a:
        fixed = enforce_true_peak(out, tp)
        if fixed:
            lufs, lra, tp, ok_a = fixed
    ok_d, err = decode_qa(out)

    shipped = [c["path"] for c in rec.get("clips", [])]
    repeats = [p for p in shipped if canonical(p) in already]

    print("  QA Part{:02d}: {:.2f} min | {} | {} | decode {}{}".format(
        part, dur / 60.0,
        "n/a" if tp is None else "{:.2f} dBTP".format(tp),
        "n/a" if lufs is None else "{:.1f} LUFS".format(lufs),
        "PASS" if ok_d else "FAIL: " + err,
        "" if not repeats else " | REPEATS {}".format(len(repeats))), flush=True)

    # HARD EDITORIAL WINDOW (user 2026-09-01: "5-6 minutes is now
    # a HARD editorial constraint ... NO >6:00 OUTPUT MAY COMMIT").
    # A Part outside it is not consumed, so its clips return to the
    # pool instead of shipping in a video that breaks the rule.
    ok_dur = PART_MIN_S <= dur <= PART_MAX_S
    if not ok_dur:
        print("    DURATION GATE: {:.2f} min outside 5:00-6:00 -- NOT COMMITTED".format(dur / 60.0), flush=True)
    ok = ok_a and ok_d and ok_dur and not repeats
    by_path = {canonical(r["canonical_avi_path"]): r for r in rows}
    man = {
        "run_id": run_id, "part": part,
        "output_path": str(out),
        "output_sha256_head": sha_head(out),
        "duration_s": round(dur, 3),
        "duration_mmss": "{}:{:02d}".format(int(dur // 60), int(dur % 60)),
        "render_minutes": round(took, 2),
        "clip_count": rec.get("clip_count", 0),
        "t1_clips": rec.get("t1_clips", 0),
        "t2_clips": rec.get("t2_clips", 0),
        "t3_clips": rec.get("t3_clips", 0),
        "historical_source_parts": sorted({r["historical_source_part"]
                                           for r in rows}),
        "clips": [{
            "path": c["path"], "tier": c["tier"],
            "historical_source_part": (by_path.get(canonical(c["path"])) or {})
                .get("historical_source_part"),
            "rendered_duration_s": c.get("rendered_duration_s", 0.0),
            "slowmo": next((sm.get("slowmo") for sm in rec.get("segment_map", [])
                            if canonical(sm.get("canonical_source_path", ""))
                            == canonical(c["path"])), None),
        } for c in rec.get("clips", [])],
        "segment_map": rec.get("segment_map", []),
        "music": [{"path": str(q), "name": Path(q).name, "bpm": c.get("bpm"),
                   "bar_fit": c.get("bar_fit"),
                   "action_match_pct": c.get("match_pct")}
                  for q, c in (music or [])],
        "integrated_LUFS": lufs, "LRA_LU": lra, "true_peak_dBTP": tp,
        "audio_QA": "PASS" if ok_a else "FAIL",
        "decode_QA": "PASS" if ok_d else "FAIL",
        "decode_error": err or None,
        "repeated_clips": repeats,
        "committed": bool(ok),
    }
    atomic_json(MANIFESTS / "Part{:02d}.json".format(part), man)

    if not ok:
        BROKEN.mkdir(parents=True, exist_ok=True)
        dst = BROKEN / out.name
        try:
            if dst.exists():
                dst.unlink()
            out.rename(dst)
        except OSError:
            pass
        print("  NOT COMMITTED -- quarantined; its clips stay unused",
              flush=True)
    return ok


# ------------------------------------------------------------------- report
def report(queue, meta):
    used, parts = committed()
    total = len(queue)
    t1 = [r for r in queue if r["tier"] == "T1"]
    t2 = [r for r in queue if r["tier"] == "T2"]
    used_t1 = sum(1 for r in t1 if canonical(r["canonical_avi_path"]) in used)
    used_t2 = sum(1 for r in t2 if canonical(r["canonical_avi_path"]) in used)

    seen = {}
    for p in parts:
        for c in p["clips"]:
            k = canonical(c["path"])
            seen[k] = seen.get(k, 0) + 1
    dups = sum(n - 1 for n in seen.values() if n > 1)
    missing = [r for r in queue
               if canonical(r["canonical_avi_path"]) not in used]

    print("")
    print("=" * 70)
    print("CONTINUOUS SERIES")
    print("=" * 70)
    lens = [p["duration_s"] for p in parts]
    for p in sorted(parts, key=lambda z: z["part"]):
        print("  {:10} {:>7} {:>3} clips (T1 {:>2}/T2 {:>2})  hist {:<10} "
              "{:>9} {:>9} {}".format(
                  Path(p["output_path"]).name, p["duration_mmss"],
                  p["clip_count"], p["t1_clips"], p["t2_clips"],
                  ",".join(str(x) for x in p["historical_source_parts"]),
                  "n/a" if p.get("integrated_LUFS") is None
                  else "{:.1f}LUFS".format(p["integrated_LUFS"]),
                  "n/a" if p.get("true_peak_dBTP") is None
                  else "{:.2f}dBTP".format(p["true_peak_dBTP"]),
                  p["decode_QA"]))
    if lens:
        print("")
        print("  {} Parts, mean {:.2f} min, total {:.2f} h".format(
            len(lens), sum(lens) / len(lens) / 60.0, sum(lens) / 3600.0))

    print("")
    print("=" * 70)
    print("COVERAGE")
    print("=" * 70)
    print("  T1 selected {:>5}   used {:>5}".format(len(t1), used_t1))
    print("  T2 selected {:>5}   used {:>5}".format(len(t2), used_t2))
    print("  total       {:>5}   used {:>5}".format(total, used_t1 + used_t2))
    print("  duplicates  {:>5}".format(dups))
    print("  missing     {:>5}".format(len(missing)))
    ok = (not missing) and dups == 0 and parts
    print("  GATE        {}".format("PASS" if ok else "FAIL"))

    for r in queue:
        r["used_in_final_part"] = used.get(canonical(r["canonical_avi_path"]))
    meta["queue"] = queue
    meta["coverage"] = {"T1_selected": len(t1), "T1_used": used_t1,
                        "T2_selected": len(t2), "T2_used": used_t2,
                        "total": total, "used": used_t1 + used_t2,
                        "duplicates": dups, "missing": len(missing),
                        "parts": len(parts)}
    atomic_json(QUEUE, meta)
    return ok, parts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--max-parts", type=int, default=RUNAWAY_PARTS)
    a = ap.parse_args()

    queue, meta = load_queue()
    run_id = "series-" + time.strftime("%Y%m%d-%H%M%S")
    print("[run] {}   queue: {} clips".format(run_id, len(queue)))

    if a.status:
        ok, _ = report(queue, meta)
        print("")
        print("STATUS: {}".format("COMPLETE" if ok else "INCOMPLETE"))
        return 0 if ok else 1

    acquire_lock(run_id)
    incomplete = False
    try:
        from creative_suite.engine import music_beatmatch as MB
        claimed = set()
        used, parts = committed()
        for p in parts:
            for m in p.get("music", []) or []:
                q = Path(m.get("path", ""))
                if q.exists():
                    cid = MB.content_id(q)
                    if cid:
                        claimed.add(cid)
        part_no = (max((p["part"] for p in parts), default=0)) + 1
        print("[run] resuming at Part{:02d}; {} clip(s) already shipped"
              .format(part_no, len(used)))

        guard = 0
        while True:
            used, _ = committed()
            remaining = [r for r in queue
                         if canonical(r["canonical_avi_path"]) not in used]
            if not remaining:
                print("\n[run] every queued clip has shipped after {} Part(s)"
                      .format(part_no - 1), flush=True)
                break
            guard += 1
            if guard > a.max_parts:
                print("\nERROR: exceeded {} Parts -- runaway guard. {} clip(s) "
                      "remain unshipped; series INCOMPLETE."
                      .format(a.max_parts, len(remaining)), flush=True)
                incomplete = True
                break

            rows, est = plan_rows(part_no, queue, used)
            if rows is None:
                rows, est = pack(remaining)
                print("[run] Part{:02d}: NO PLAN ENTRY -- greedy fallback".format(part_no), flush=True)
            print("\n[run] Part{:02d}: {} clip(s), predicted {:.2f} min, "
                  "{} remaining after".format(part_no, len(rows), est / 60.0,
                                              len(remaining) - len(rows)),
                  flush=True)
            music = choose_music(
                part_no, claimed, rows=rows,
                body_s=est * MUSIC_BODY_GROWTH + MUSIC_BOOKEND_S)
            for q, c in music:
                print("  [music] {:44} {:6.1f} bpm".format(
                    q.name[:44], c.get("bpm") or 0.0), flush=True)

            ok, out, rec, took, work = render_part(part_no, rows, music, run_id)
            if not ok:
                reclaim(work)
                ok, out, rec, took, work = render_part(part_no, rows, music,
                                                       run_id)
                if not ok:
                    print("  retry failed -- series INCOMPLETE", flush=True)
                    incomplete = True
                    break
            if not commit(part_no, out, rec, rows, music, run_id, took, used):
                reclaim(work)
                ok2, out2, rec2, took2, work = render_part(part_no, rows, music,
                                                           run_id)
                if not (ok2 and commit(part_no, out2, rec2, rows, music, run_id,
                                       took2, used)):
                    print("  retry failed -- series INCOMPLETE", flush=True)
                    incomplete = True
                    break
            if preserve_game_stem(part_no, work):
                print("  [stem] game audio kept for later remix", flush=True)
            freed = reclaim(work)
            if freed:
                print("  [work] reclaimed {:.1f} GB".format(freed), flush=True)

            after, _ = committed()
            if len(after) <= len(used):
                print("  ERROR: Part consumed no new clips -- stopping",
                      flush=True)
                incomplete = True
                break
            part_no += 1
    finally:
        release_lock()

    ok, parts = report(queue, meta)
    if incomplete:
        ok = False
    print("")
    print("=" * 70)
    print("SERIES: {}".format("COMPLETE" if ok else "INCOMPLETE"))
    print("=" * 70)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
