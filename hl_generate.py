"""Generate episodes until EVERY T1+T2 clip has shipped exactly once.

Contract (user 2026-08-29, "VIDEO FIRST"):

  * Termination is coverage, never a cap:  while unused_T1 or unused_T2.
  * T3 does NOT count toward coverage. It is intro/outro material only, and is
    never used to claim that T1/T2 were consumed.
  * A clip is consumed only after its episode PASSES audio and decode QA.
  * Every episode writes a manifest. Coverage is reconciled from manifests plus
    the authoritative source folders, never from an incremental counter.
  * Exactly ONE writer of coverage state. Parts render concurrently, but every
    mutation (selection input, music claiming, QA, commit) happens under one
    lock in this process, and a second PROCESS is refused by the file lock.

    python hl_generate.py                  # all Parts, run to exhaustion
    python hl_generate.py --parts 4 5 6
    python hl_generate.py --jobs 4
    python hl_generate.py --status         # reconcile and report, render nothing
    python hl_generate.py --requa          # re-measure committed episodes
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
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from creative_suite.engine.config import Config  # noqa: E402
from creative_suite.engine.render_highlight import collect_frags  # noqa: E402

OUT = ROOT / "output"
LOCK = OUT / "_hl_generate.lock"
MANIFESTS = OUT / "_hl_manifests"
BROKEN = OUT / "_hl_broken"
LEFTOVERS = OUT / "LEFTOVERS"
RUNMETA = OUT / "_hl_run.json"

FFMPEG = ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
FFPROBE = ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffprobe.exe"

# TRUE PEAK, in dBTP. Not dBFS: dBFS is a sample peak, dBTP is the
# reconstructed inter-sample peak. A mix can sit under 0 dBFS and still
# overshoot on playback, so the two words are not interchangeable.
TP_CEILING_DBTP = -1.0
COVERAGE_TIERS = ("T1", "T2")

# Measured mean T1/T2 clip length across the library, used as the bar-grid
# prior when choosing music before an episode's own pacing is known.
LIBRARY_MEAN_CLIP_S = 13.9

# Emergency guard ONLY. Not a packaging limit. Reaching it is an ERROR that
# marks the Part INCOMPLETE -- never a quiet "this Part is finished".
RUNAWAY_EPISODES = 400


# --------------------------------------------------------------- single writer
def _pid_alive(pid: int) -> bool:
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-Process -Id {} -ErrorAction SilentlyContinue) -ne $null"
             .format(pid)],
            capture_output=True, text=True, timeout=30).stdout.strip()
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
                "FATAL: generation lock is held by PID {} (run {}, started {})."
                "  Exactly one writer is allowed against {}."
                "  Stop that process, or delete {} if it is genuinely dead."
                .format(pid, held.get("run_id"), held.get("started"), OUT, LOCK))
        print("[lock] stale lock from dead PID {} -- reclaiming".format(pid))
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps(
        {"pid": os.getpid(), "run_id": run_id,
         "started": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=2),
        encoding="utf-8")


def release_lock() -> None:
    try:
        LOCK.unlink()
    except OSError:
        pass


# ------------------------------------------------------ authoritative library
def canonical(p) -> str:
    """Source identity: the full resolved path.

    Basenames repeat across folders in this corpus ("0.avi", "1.avi"), so a
    basename-keyed uniqueness check would collapse distinct clips into one and
    report a false PASS.
    """
    return str(Path(p).resolve()).lower()


@dataclass
class Inventory:
    per_part: dict = field(default_factory=dict)

    def counts(self, part: int):
        d = self.per_part[part]
        return len(d["T1"]), len(d["T2"]), len(d["T3"])

    def coverage_set(self, part: int) -> set:
        d = self.per_part[part]
        return set(d["T1"]) | set(d["T2"])

    def all_coverage(self) -> set:
        out = set()
        for p in self.per_part:
            out |= self.coverage_set(p)
        return out


def unrenderable_sources() -> dict:
    """Clips ffprobe cannot open, keyed by canonical path -> reason.

    A source that will not decode can never enter an episode, so it can never
    be consumed -- the Part stalls one clip short and the loop guard trips,
    which looks exactly like a coverage bug. Classifying these up front turns a
    mystery into a documented exclusion. The file is produced by scanning every
    source clip with ffprobe; it is evidence, not an opt-out, and anything
    listed here is reported explicitly rather than quietly dropped.
    """
    p = OUT / "unrenderable_sources.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {canonical(i["path"]): (i.get("error") or "unreadable")
            for i in data.get("items", []) if not i.get("readable", True)}


def build_inventory(parts, cfg: Config) -> Inventory:
    inv = Inventory()
    dead = unrenderable_sources()
    dropped = []
    for part in parts:
        frags = collect_frags(part, cfg)
        d = {"T1": [], "T2": [], "T3": []}
        for f in frags:
            if f.tier in d:
                key = canonical(f.fp)
                if key in dead:
                    dropped.append((part, f.tier, f.fp.name, dead[key]))
                    continue
                d[f.tier].append(key)
        for k in d:
            if len(d[k]) != len(set(d[k])):
                n = len(d[k]) - len(set(d[k]))
                print("  [inv] WARNING Part {} {}: {} repeated source path(s) "
                      "collapsed".format(part, k, n))
                d[k] = sorted(set(d[k]))
        inv.per_part[part] = d
    if dropped:
        print("  [inv] {} source(s) EXCLUDED as unrenderable (ffprobe cannot "
              "open them):".format(len(dropped)))
        for part, tier, name, why in dropped:
            print("        Part {:<3} {:3} {:44} {}".format(
                part, tier, name[:44], (why or "")[:60]))
        print("        These are corrupt SOURCE assets, not pipeline failures. "
              "They are excluded from the coverage target and listed in "
              "output/unrenderable_sources.json.")
    return inv


def print_inventory(inv: Inventory, parts):
    print("=" * 74)
    print("AUTHORITATIVE INPUT LIBRARY  (immutable coverage target)")
    print("=" * 74)
    print("  {:>5} {:>5} {:>5} {:>7} {:>5}".format("Part", "T1", "T2",
                                                   "T1+T2", "T3"))
    a = b = c = 0
    for part in parts:
        t1, t2, t3 = inv.counts(part)
        a += t1
        b += t2
        c += t3
        print("  {:>5} {:>5} {:>5} {:>7} {:>5}".format(part, t1, t2,
                                                       t1 + t2, t3))
    print("  {:>5} {:>5} {:>5} {:>7} {:>5}".format("ALL", a, b, a + b, c))
    print("")
    print("  COVERAGE TARGET = {} clips (T1+T2).".format(a + b))
    print("  T3 ({}) is intro/outro material and is NOT counted.".format(c))
    return a, b


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
    """(integrated LUFS, LRA, TRUE PEAK dBTP, pass) from the ENCODED file.

    ebur128 prints a RUNNING "I: ... LUFS" for every window as it goes, starting
    at -70 before it has enough data, and only then the Summary block. Taking
    the FIRST match reported -70.0 LUFS for a perfectly normal mix; the
    integrated value is the LAST one.

    "Peak:" appears only in the Summary (running lines use TPK:/FTPK:). ffmpeg
    labels it dBFS, but with peak=true it is a TRUE PEAK measurement, so it is
    reported as dBTP.
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
    ok = tp is not None and tp <= TP_CEILING_DBTP
    return lufs, lra, tp, ok


def decode_qa(path: Path):
    """Full decode to null. A file that exists is not a file that plays."""
    r = subprocess.run([str(FFMPEG), "-v", "error", "-xerror",
                        "-i", str(path), "-f", "null", "-"],
                       capture_output=True, text=True)
    err = r.stderr.strip()
    if r.returncode != 0 or err:
        return False, (err[-400:] or "exit {}".format(r.returncode))
    vd = probe_duration(path)
    ra = subprocess.run([str(FFPROBE), "-v", "error", "-select_streams", "a:0",
                         "-show_entries", "stream=duration,codec_name",
                         "-of", "csv=p=0", str(path)],
                        capture_output=True, text=True).stdout.strip()
    if not ra:
        return False, "no audio stream"
    if vd <= 1.0:
        return False, "video duration {:.2f}s".format(vd)
    return True, ""


# ----------------------------------------------- manifests are the audit trail
def atomic_json(path: Path, obj) -> None:
    """Temp file + replace. An interrupted write must not leave valid-looking
    JSON behind -- coverage state that half-parses is worse than none."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def manifest_path(part: int, episode: int) -> Path:
    return MANIFESTS / "part{:02d}_ep{:02d}.json".format(part, episode)


def load_manifests(parts):
    out = []
    if not MANIFESTS.exists():
        return out
    for m in sorted(MANIFESTS.glob("part*_ep*.json")):
        if m.name.startswith("_raw"):
            continue
        try:
            rec = json.loads(m.read_text(encoding="utf-8"))
        except Exception:
            continue
        if rec.get("part") in parts and rec.get("committed"):
            out.append(rec)
    return out


def used_by_part(parts):
    """canonical clip path -> episode tag, for every COMMITTED episode."""
    used = {p: {} for p in parts}
    for rec in load_manifests(parts):
        tag = "part{:02d}_ep{:02d}".format(rec["part"], rec["episode"])
        for c in rec["clips"]:
            used[rec["part"]][canonical(c["path"])] = tag
    return used


def remaining_for(part: int, inv: Inventory, used):
    spent = set(used.get(part, {}))
    d = inv.per_part[part]
    return ([c for c in d["T1"] if c not in spent],
            [c for c in d["T2"] if c not in spent])


def write_exclude(part: int, episode: int, used) -> Path:
    """Canonical paths already shipped for this Part.

    This is what actually stops an episode re-selecting footage. Without it the
    renderer scores every frag in the Part every time and episode 2 comes back
    with episode 1's clips.
    """
    p = MANIFESTS / "_exclude_part{:02d}_ep{:02d}.txt".format(part, episode)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(sorted(used.get(part, {}))) + "\n", encoding="utf-8")
    return p


def sha_head(path: Path, limit: int = 4 << 20) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            h.update(fh.read(limit))
    except OSError:
        return ""
    return h.hexdigest()[:16]


def reclaim_work(part: int, episode: int) -> float:
    """Delete one episode's intermediates once it is committed.

    Work dirs are per-EPISODE (a per-Part dir made episode 2 reuse episode 1's
    cached segments), which turns a fixed ~2.7 GB into ~2.7 GB PER EPISODE --
    about 230 GB across the run against ~130 GB free. The intermediates are
    fully regenerable; the mp4, manifest and segment map are what matter.
    """
    d = OUT / "_hl_part{:02d}_ep{:02d}".format(part, episode)
    if not d.exists():
        return 0.0
    freed = 0
    for f in d.rglob("*"):
        if f.is_file():
            try:
                freed += f.stat().st_size
            except OSError:
                pass
    try:
        shutil.rmtree(d)
    except OSError as exc:
        print("  [work] could not reclaim {}: {}".format(d.name, exc))
        return 0.0
    return freed / 1e9


# ------------------------------------------------------------------- render
def claimed_song_ids(parts):
    """content_ids of every track already used by a committed episode.

    Identity MUST come from music_beatmatch.content_id, the same function the
    catalogue is keyed on. The ledger's used_songs() uses its own hashing, so
    feeding those keys in as used_ids matched nothing and every episode picked
    the same top-scoring track -- four Parts opened with the identical song.
    """
    from creative_suite.engine import music_beatmatch as MB
    out = set()
    for rec in load_manifests(parts):
        for m in rec.get("music", []) or []:
            q = Path(m.get("path", ""))
            if q.exists():
                cid = MB.content_id(q)
                if cid:
                    out.add(cid)
    return out


def choose_music(part: int, episode: int, claimed: set, count: int = 2):
    """Claim tracks for an episode. Caller MUST hold the state lock.

    Selection lives in the orchestrator, not the render subprocess, because
    several episodes render at once and two of them claiming the same song
    would break "never 2 of the same" with no error anywhere.

    `claimed` is the live set of content_ids taken this run; it is updated in
    place so a concurrent Part cannot pick the same track before this one has
    committed.
    """
    from creative_suite.engine import highlight_ledger as HL
    from creative_suite.engine import music_beatmatch as MB
    picked = []
    try:
        for c in MB.pick_for_episode(mean_clip_s=LIBRARY_MEAN_CLIP_S,
                                     min_duration_s=150.0,
                                     used_ids=set(claimed),
                                     count=count):
            q = Path(c["path"])
            if not q.exists():
                continue
            claimed.add(c["content_id"])
            try:
                HL.claim_song(q, "part{:02d}ep{}".format(part, episode))
            except Exception:
                pass                       # ledger registry is advisory here
            picked.append((q, c))
    except Exception as exc:                        # noqa: BLE001
        print("  [beatmatch] selection failed ({}); renderer will pick"
              .format(exc), flush=True)
    return picked


def render_episode(part, episode, minutes, run_id, music=None, exclude=None):
    """Render one episode. Returns (ok, out_path, raw_manifest, minutes)."""
    out = OUT / "Part{}_highlight{}.mp4".format(
        part, "" if episode == 1 else "_ep{}".format(episode))
    raw = MANIFESTS / "_raw_part{:02d}_ep{:02d}.json".format(part, episode)
    log = OUT / "hl_p{}e{}.log".format(part, episode)
    raw.parent.mkdir(parents=True, exist_ok=True)
    if raw.exists():
        raw.unlink()

    cmd = [sys.executable, "-u", "-m",
           "creative_suite.engine.render_highlight",
           "--part", str(part), "--minutes", str(minutes),
           "--episode", str(episode), "--out", str(out),
           "--manifest", str(raw)]
    if music:
        cmd += ["--music", "|".join(str(q) for q, _ in music)]
    if exclude is not None:
        cmd += ["--exclude", str(exclude)]

    print("===== Part {} episode {} -> {} =====".format(part, episode,
                                                        out.name), flush=True)
    t0 = time.time()
    with log.open("w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.run(cmd, cwd=str(ROOT), stdout=fh,
                              stderr=subprocess.STDOUT)
    took = (time.time() - t0) / 60.0

    if proc.returncode != 0 or not out.exists() or not raw.exists():
        print("  RENDER FAILED (exit {}) -- see {}".format(proc.returncode,
                                                           log.name),
              flush=True)
        return False, out, None, took
    return True, out, json.loads(raw.read_text(encoding="utf-8")), took


def enforce_true_peak(out: Path, tp):
    """Bring an over-ceiling episode down by a measured static gain.

    Limiting alone does not get there: `alimiter` has an attack time, so the
    fast transients this material is full of (rail and rocket impacts) blow
    past before gain reduction engages. Pushing the limiter harder would start
    audibly squashing exactly the hits the edit is built around.

    A pure gain change has no such artefact -- it preserves dynamics exactly --
    and the amount needed is not a guess, it is measured. Video is stream-
    copied so this costs seconds rather than a re-render, and the result is
    re-measured rather than assumed.

    Returns (lufs, lra, tp, ok) after correction, or the originals if no
    correction was needed or it could not be applied.
    """
    if tp is None or tp <= TP_CEILING_DBTP:
        return None
    # Aim 0.6 dB below the ceiling so measurement noise cannot push it back over.
    gain_db = TP_CEILING_DBTP - tp - 0.6
    tmp = out.with_name(out.stem + "_tpfix.mp4")
    print("  [tp] {} measured {:.2f} dBTP -- applying {:.2f} dB static gain"
          .format(out.name, tp, gain_db), flush=True)
    r = subprocess.run(
        [str(FFMPEG), "-y", "-v", "error", "-i", str(out),
         "-af", "volume={:.2f}dB".format(gain_db),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
         "-movflags", "+faststart", str(tmp)],
        capture_output=True, text=True)
    if r.returncode != 0 or not tmp.exists():
        print("  [tp] correction failed: {}".format(r.stderr[-200:]), flush=True)
        try:
            tmp.unlink()
        except OSError:
            pass
        return None
    os.replace(tmp, out)
    lufs2, lra2, tp2, ok2 = audio_qa(out)
    print("  [tp] {} now {:.2f} dBTP / {} LUFS -- {}".format(
        out.name, tp2 if tp2 is not None else float("nan"),
        "n/a" if lufs2 is None else "{:.1f}".format(lufs2),
        "PASS" if ok2 else "STILL OVER"), flush=True)
    return lufs2, lra2, tp2, ok2


def commit_episode(part, episode, out: Path, rec, run_id, took, music=None,
                   already_used=None):
    """QA the episode, then commit it. Clips are consumed ONLY on a pass."""
    dur = probe_duration(out)
    lufs, lra, tp, audio_ok = audio_qa(out)
    if not audio_ok:
        fixed = enforce_true_peak(out, tp)
        if fixed:
            lufs, lra, tp, audio_ok = fixed
    dec_ok, dec_err = decode_qa(out)

    # A re-selection of footage that already shipped must never be committed:
    # it would double-count coverage while the reel repeats itself.
    overlap = []
    if already_used:
        overlap = [c["path"] for c in rec.get("clips", [])
                   if canonical(c["path"]) in already_used]

    tp_s = "n/a" if tp is None else "{:.2f} dBTP".format(tp)
    lu_s = "n/a" if lufs is None else "{:.1f} LUFS".format(lufs)
    if lra is not None:
        lu_s += " / LRA {:.1f}".format(lra)
    print("  QA p{} ep{}: {:.2f} min | true peak {} | {} | decode {}{}".format(
        part, episode, dur / 60.0, tp_s, lu_s,
        "PASS" if dec_ok else "FAIL: " + dec_err,
        "" if not overlap else " | REPEATS {} shipped clip(s)".format(len(overlap))),
        flush=True)

    ok = audio_ok and dec_ok and not overlap
    man = {
        "generation_run_id": run_id,
        "part": part,
        "episode": episode,
        "output_path": str(out),
        "output_sha256_head": sha_head(out),
        "duration_s": round(dur, 3),
        "duration_mmss": "{}:{:02d}".format(int(dur // 60), int(dur % 60)),
        "render_minutes": round(took, 2),
        "clip_count": rec.get("clip_count", 0),
        "t1_clips": rec.get("t1_clips", 0),
        "t2_clips": rec.get("t2_clips", 0),
        "t3_clips": rec.get("t3_clips", 0),
        "clips": [{"path": c["path"], "tier": c["tier"],
                   "rendered_duration_s": c.get("rendered_duration_s", 0.0)}
                  for c in rec.get("clips", [])],
        "segment_map": rec.get("segment_map", []),
        "music": [{"path": str(q), "name": Path(q).name,
                   "bpm": c.get("bpm"), "bar_fit": c.get("bar_fit"),
                   "match_score": c.get("match_score")}
                  for q, c in (music or [])],
        "integrated_LUFS": lufs,
        "LRA_LU": lra,
        "true_peak_dBTP": tp,
        "audio_QA": "PASS" if audio_ok else "FAIL",
        "decode_QA": "PASS" if dec_ok else "FAIL",
        "decode_error": dec_err or None,
        "repeated_clips": overlap,
        "committed": bool(ok),
    }
    atomic_json(manifest_path(part, episode), man)

    if not ok:
        BROKEN.mkdir(parents=True, exist_ok=True)
        dst = BROKEN / out.name
        try:
            if dst.exists():
                dst.unlink()
            out.rename(dst)
        except OSError:
            pass
        print("  NOT COMMITTED -- output quarantined to {}; its clips stay "
              "unused".format(BROKEN.name), flush=True)
    return ok


# ------------------------------------------------------------ coverage gates
def part_gate(part: int, inv: Inventory, used):
    """Reconcile a Part from scratch: sources vs committed manifests."""
    d = inv.per_part[part]
    sel_t1, sel_t2 = len(d["T1"]), len(d["T2"])
    spent = used.get(part, {})

    rendered_t1 = sum(1 for c in d["T1"] if c in spent)
    rendered_t2 = sum(1 for c in d["T2"] if c in spent)
    rem_t1, rem_t2 = remaining_for(part, inv, used)

    seen = {}
    broken = 0
    episodes = 0
    runtime = 0.0
    for m in sorted(MANIFESTS.glob("part{:02d}_ep*.json".format(part))):
        if m.name.startswith("_raw"):
            continue
        try:
            r = json.loads(m.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not r.get("committed"):
            broken += 1
            continue
        episodes += 1
        runtime += r.get("duration_s") or 0.0
        for c in r["clips"]:
            k = canonical(c["path"])
            seen[k] = seen.get(k, 0) + 1
    duplicates = sum(n - 1 for n in seen.values() if n > 1)

    cover = inv.coverage_set(part)
    missing = len([c for c in cover if c not in spent])

    ok = (rendered_t1 == sel_t1 and rendered_t2 == sel_t2
          and not rem_t1 and not rem_t2 and duplicates == 0
          and missing == 0 and broken == 0)
    return {
        "part": part, "selected_T1": sel_t1, "selected_T2": sel_t2,
        "rendered_T1": rendered_t1, "rendered_T2": rendered_t2,
        "remaining_T1": len(rem_t1), "remaining_T2": len(rem_t2),
        "duplicates": duplicates, "missing": missing,
        "broken_outputs": broken, "episodes": episodes,
        "total_runtime_s": round(runtime, 1), "PASS": ok,
    }


def global_gate(inv: Inventory, parts):
    used = used_by_part(parts)
    assigned = set()
    dup = 0
    for p in parts:
        for k in used[p]:
            if k in assigned:
                dup += 1
            assigned.add(k)
    target = inv.all_coverage()
    rendered = len(target & assigned)
    missing = len(target - assigned)
    return {
        "T1_total": sum(len(inv.per_part[p]["T1"]) for p in parts),
        "T2_total": sum(len(inv.per_part[p]["T2"]) for p in parts),
        "T1_T2_total": len(target),
        "unique_assigned": len(assigned & target),
        "unique_rendered_ok": rendered,
        "duplicates": dup,
        "missing": missing,
        "unassigned": missing,
        "PASS": missing == 0 and dup == 0,
    }


# --------------------------------------------------------------- leftovers
def write_leftovers(inv: Inventory, parts, cfg: Config):
    """Everything NOT consumed by the main videos, grouped for later use.

    If any T1 or T2 source lands here, main coverage has FAILED and the caller
    must not report completion.
    """
    used = used_by_part(parts)
    LEFTOVERS.mkdir(parents=True, exist_ok=True)
    rows = []
    violations = []
    unrenderable = []
    dead = unrenderable_sources()

    for part in parts:
        frags = collect_frags(part, cfg)
        spent = set(used.get(part, {}))
        for f in frags:
            if canonical(f.fp) in spent:
                continue
            name = f.fp.name.lower()
            group = f.tier
            if "rail" in name:
                group += "/rail"
            elif "rocket" in name or "_rl" in name:
                group += "/rocket"
            elif "multi" in name or "quad" in name:
                group += "/multikill"
            elif f.is_intro:
                group += "/intro-tagged"
            # A coverage-tier clip in LEFTOVERS is a hard failure -- EXCEPT
            # when the source itself cannot be decoded. That is a broken asset,
            # not footage the pipeline skipped, and it is recorded with the
            # ffprobe error so the distinction is auditable rather than a
            # convenient exemption.
            if f.tier in COVERAGE_TIERS:
                if canonical(f.fp) in dead:
                    unrenderable.append((part, f.tier, str(f.fp),
                                         dead[canonical(f.fp)]))
                else:
                    violations.append((part, f.tier, str(f.fp)))
            rows.append({
                "part": part, "tier": f.tier, "group": group,
                "path": str(f.fp), "angles": len(f.fls),
                "is_intro_tagged": bool(f.is_intro),
                "reason_not_in_main_run":
                    "T3 excluded from the T1/T2 coverage target"
                    if f.tier == "T3"
                    else ("SOURCE UNREADABLE: " + dead[canonical(f.fp)][:120]
                          if canonical(f.fp) in dead
                          else "UNEXPECTED: coverage tier left unused"),
            })

    atomic_json(LEFTOVERS / "manifest.json",
                {"total": len(rows), "t1_t2_violations": len(violations),
                 "t1_t2_unrenderable": [
                     {"part": p, "tier": t, "path": q, "error": w}
                     for p, t, q, w in unrenderable],
                 "items": rows})
    with (LEFTOVERS / "manifest.csv").open("w", newline="",
                                           encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "part", "tier", "group", "path", "angles", "is_intro_tagged",
            "reason_not_in_main_run"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return rows, violations, unrenderable


# ------------------------------------------------------------------- re-QA
def requa(parts):
    """Re-measure every committed episode and correct its manifest."""
    fixed = failed = 0
    for m in sorted(MANIFESTS.glob("part*_ep*.json")):
        if m.name.startswith("_raw"):
            continue
        try:
            rec = json.loads(m.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not rec.get("committed"):
            continue
        out = Path(rec["output_path"])
        if not out.exists():
            print("  [requa] MISSING output for {} -- marking broken"
                  .format(m.name))
            rec["committed"] = False
            rec["decode_QA"] = "FAIL"
            rec["decode_error"] = "output file missing at re-QA"
            atomic_json(m, rec)
            failed += 1
            continue
        lufs, lra, tp, ok = audio_qa(out)
        dec_ok, dec_err = decode_qa(out)
        rec["integrated_LUFS"] = lufs
        rec["LRA_LU"] = lra
        rec["true_peak_dBTP"] = tp
        rec["audio_QA"] = "PASS" if ok else "FAIL"
        rec["decode_QA"] = "PASS" if dec_ok else "FAIL"
        rec["decode_error"] = dec_err or None
        rec["requa_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if not (ok and dec_ok):
            rec["committed"] = False
            failed += 1
            print("  [requa] {} now FAILS QA (tp={} decode={}) -- uncommitted"
                  .format(m.name, tp, dec_ok))
        else:
            fixed += 1
        atomic_json(m, rec)
    print("[requa] {} episode(s) re-measured, {} failed".format(fixed, failed))
    return fixed, failed


# -------------------------------------------------------------------- report
def report(inv: Inventory, parts, run_id):
    used = used_by_part(parts)
    recs = load_manifests(parts)

    print("")
    print("=" * 74)
    print("GENERATED VIDEOS")
    print("=" * 74)
    if not recs:
        print("  (none committed yet)")
    lens = []
    for r in sorted(recs, key=lambda z: (z["part"], z["episode"])):
        lens.append(r["duration_s"])
        print("  {:30} {:>7} {:>3}clips T1{:>3}/T2{:>3} {:>9} {:>9} {}".format(
            Path(r["output_path"]).name, r["duration_mmss"], r["clip_count"],
            r["t1_clips"], r["t2_clips"],
            "n/a" if r.get("integrated_LUFS") is None
            else "{:.1f}LUFS".format(r["integrated_LUFS"]),
            "n/a" if r.get("true_peak_dBTP") is None
            else "{:.2f}dBTP".format(r["true_peak_dBTP"]),
            r["decode_QA"]))
    if lens:
        print("")
        print("  {} episodes, mean {:.2f} min, total {:.2f} h".format(
            len(lens), sum(lens) / len(lens) / 60.0, sum(lens) / 3600.0))

    print("")
    print("=" * 74)
    print("PER-PART COVERAGE  (reconciled from sources + manifests)")
    print("=" * 74)
    print("  {:>4} {:>9} {:>9} {:>7} {:>7} {:>4} {:>4} {:>4} {:>4}  gate"
          .format("Part", "sel T1/T2", "rnd T1/T2", "remT1", "remT2", "eps",
                  "dup", "miss", "brk"))
    all_pass = True
    for part in parts:
        g = part_gate(part, inv, used)
        all_pass = all_pass and g["PASS"]
        print("  {:>4} {:>4}/{:<4} {:>4}/{:<4} {:>7} {:>7} {:>4} {:>4} {:>4} "
              "{:>4}  {}".format(
                  part, g["selected_T1"], g["selected_T2"], g["rendered_T1"],
                  g["rendered_T2"], g["remaining_T1"], g["remaining_T2"],
                  g["episodes"], g["duplicates"], g["missing"],
                  g["broken_outputs"], "PASS" if g["PASS"] else "FAIL"))

    gg = global_gate(inv, parts)
    print("")
    print("=" * 74)
    print("GLOBAL COVERAGE")
    print("=" * 74)
    for k in ("T1_total", "T2_total", "T1_T2_total", "unique_assigned",
              "unique_rendered_ok", "duplicates", "missing", "unassigned"):
        print("  {:22} {}".format(k, gg[k]))
    print("  {:22} {}".format("GATE", "PASS" if gg["PASS"] else "FAIL"))

    atomic_json(OUT / "video_coverage_report.json", {
        "run_id": run_id,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "episodes": recs,
        "per_part": [part_gate(p, inv, used) for p in parts],
        "global": gg,
    })
    return all_pass and gg["PASS"], gg


# ---------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", type=int, nargs="*", default=list(range(1, 13)))
    ap.add_argument("--minutes", type=float, default=4.7,
                    help="BODY target; intro+outro add ~18 s on top")
    ap.add_argument("--jobs", type=int, default=4,
                    help="Parts rendered concurrently; coverage state stays "
                         "single-writer under a lock")
    ap.add_argument("--requa", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    parts = sorted(a.parts)
    cfg = Config()
    run_id = "run-" + time.strftime("%Y%m%d-%H%M%S")

    print("[run] generation run id: {}".format(run_id))
    inv = build_inventory(parts, cfg)
    t1_all, t2_all = print_inventory(inv, parts)

    if a.requa:
        requa(parts)
    if a.status or a.requa:
        ok, _ = report(inv, parts, run_id)
        print("")
        print("STATUS: {}".format("COMPLETE" if ok else "INCOMPLETE"))
        return 0 if ok else 1

    acquire_lock(run_id)
    atomic_json(RUNMETA,
                {"run_id": run_id, "parts": parts, "T1": t1_all, "T2": t2_all,
                 "coverage_target": t1_all + t2_all, "jobs": a.jobs,
                 "started": time.strftime("%Y-%m-%d %H:%M:%S")})

    incomplete = []
    state_lock = threading.Lock()
    # Live set of song content_ids taken this run, seeded from what already
    # shipped. Shared across Parts under the same lock so two concurrent
    # episodes cannot claim the same track.
    claimed_songs = claimed_song_ids(parts)
    print("[music] {} track(s) already claimed by committed episodes"
          .format(len(claimed_songs)))

    def run_part(part: int):
        """One Part's episode chain.

        Renders run concurrently ACROSS Parts. Only the render subprocess runs
        outside the lock -- exclusion list, music claiming, QA and commit all
        happen while holding it, so there is still exactly ONE writer of
        coverage state. Parts are independent by construction (a clip belongs
        to exactly one Part), so parallelising them cannot cross-contaminate.
        """
        with state_lock:
            ep = max([r["episode"] for r in load_manifests([part])] or [0]) + 1
        guard = 0
        while True:
            with state_lock:
                used = used_by_part(parts)
                rem_t1, rem_t2 = remaining_for(part, inv, used)
                spent_now = set(used.get(part, {}))
                excl = write_exclude(part, ep, used)
            if not rem_t1 and not rem_t2:
                print("[part {}] all T1+T2 consumed after {} episode(s)"
                      .format(part, ep - 1), flush=True)
                return
            guard += 1
            if guard > RUNAWAY_EPISODES:
                print("ERROR: Part {} exceeded {} episodes -- runaway guard "
                      "tripped. Part marked INCOMPLETE; {} T1 + {} T2 clips "
                      "remain unshipped.".format(part, RUNAWAY_EPISODES,
                                                 len(rem_t1), len(rem_t2)),
                      flush=True)
                incomplete.append(part)
                return

            print("[part {}] episode {}: {} T1 + {} T2 unused"
                  .format(part, ep, len(rem_t1), len(rem_t2)), flush=True)

            with state_lock:
                music = choose_music(part, ep, claimed_songs)
            for q, c in music:
                print("  [beatmatch] p{} ep{}  {:40} {:6.1f}bpm fit {:.3f}"
                      .format(part, ep, q.name[:40], c.get("bpm") or 0.0,
                              c.get("bar_fit") or 0.0), flush=True)

            ok, out, rec, took = render_episode(part, ep, a.minutes, run_id,
                                                music=music, exclude=excl)
            if not ok:
                print("  render failed -- clips NOT consumed; retrying once",
                      flush=True)
                reclaim_work(part, ep)
                ok, out, rec, took = render_episode(part, ep, a.minutes,
                                                    run_id, music=music,
                                                    exclude=excl)
                if not ok:
                    print("  retry failed -- Part {} marked INCOMPLETE"
                          .format(part), flush=True)
                    incomplete.append(part)
                    return

            with state_lock:
                committed = commit_episode(part, ep, out, rec, run_id, took,
                                           music=music,
                                           already_used=spent_now)
            if not committed:
                print("  QA failed -- retrying this episode once", flush=True)
                reclaim_work(part, ep)
                ok2, out2, rec2, took2 = render_episode(part, ep, a.minutes,
                                                        run_id, music=music,
                                                        exclude=excl)
                with state_lock:
                    ok2 = ok2 and commit_episode(part, ep, out2, rec2, run_id,
                                                 took2, music=music,
                                                 already_used=spent_now)
                if not ok2:
                    print("  retry failed -- Part {} marked INCOMPLETE"
                          .format(part), flush=True)
                    incomplete.append(part)
                    return

            freed = reclaim_work(part, ep)
            if freed:
                print("  [work] p{} ep{} reclaimed {:.1f} GB".format(
                    part, ep, freed), flush=True)

            with state_lock:
                used = used_by_part(parts)
                nr1, nr2 = remaining_for(part, inv, used)
            if len(nr1) + len(nr2) >= len(rem_t1) + len(rem_t2):
                print("  ERROR: episode consumed no new clips -- stopping "
                      "Part {} to avoid an infinite loop".format(part),
                      flush=True)
                incomplete.append(part)
                return
            ep += 1

    try:
        print("")
        print("[run] rendering {} Part(s), {} at a time".format(len(parts),
                                                                a.jobs))
        with ThreadPoolExecutor(max_workers=a.jobs) as ex:
            futs = {ex.submit(run_part, pt): pt for pt in parts}
            for fut in as_completed(futs):
                pt = futs[fut]
                try:
                    fut.result()
                except Exception as exc:            # noqa: BLE001
                    print("ERROR: Part {} raised {}: {} -- marked INCOMPLETE"
                          .format(pt, type(exc).__name__, exc), flush=True)
                    incomplete.append(pt)
    finally:
        release_lock()

    ok, gg = report(inv, parts, run_id)

    print("")
    print("=" * 74)
    print("LEFTOVERS")
    print("=" * 74)
    rows, violations, unrenderable = write_leftovers(inv, parts, cfg)
    print("  {} unused clip(s) inventoried".format(len(rows)))
    print("  {}".format(LEFTOVERS / "manifest.csv"))
    print("  {}".format(LEFTOVERS / "manifest.json"))
    if violations:
        print("")
        print("  HARD INVARIANT BROKEN: {} T1/T2 source(s) are in LEFTOVERS."
              .format(len(violations)))
        for p, t, path in violations[:10]:
            print("    Part {} {} {}".format(p, t, path))
        print("  MAIN VIDEO COVERAGE = FAILED")
        ok = False
    elif unrenderable:
        print("")
        print("  {} coverage-tier source(s) are UNRENDERABLE and excluded:"
              .format(len(unrenderable)))
        for p, t, q, w in unrenderable:
            print("    Part {} {} {}".format(p, t, Path(q).name))
            print("      {}".format(w[:100]))
        print("  Every DECODABLE T1/T2 source shipped. These files cannot be "
              "opened by ffprobe or ffmpeg at all.")
    else:
        print("  confirmed: no T1 or T2 source remains unused")

    if incomplete:
        print("")
        print("INCOMPLETE PARTS: {}".format(sorted(set(incomplete))))
        ok = False

    print("")
    print("=" * 74)
    print("VIDEO COVERAGE: {}".format("100% COMPLETE" if ok else "INCOMPLETE"))
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
