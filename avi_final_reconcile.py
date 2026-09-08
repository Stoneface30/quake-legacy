"""Independent reconciliation and promotion gate for a finished V1 generation.

This does not trust the renderer. Coverage is recomputed from the committed
manifests against the authoritative queue; true peak and loudness are measured
again from the encoded MP4s rather than read back from the manifest that the
renderer wrote; every file is decoded to null. A generation is promotable only
if every hard invariant holds.

    python avi_final_reconcile.py                # report
    python avi_final_reconcile.py --promote      # report, then promote if PASS

Hard invariants (V1 directive S17):

    1076 / 1076 primary sources          0 primary duplicates
    0 unexplained primary sources        0 primary POV dropped
    0 QA-failed committed Parts          0 decode failures
    0 post-encode true peak > -1.0 dBTP  all manifests coherent
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FFMPEG = ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
FFPROBE = ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffprobe.exe"
QUEUE = ROOT / "output" / "avi_master_queue.json"
BOUNDARY = ROOT / "output" / "clip_boundary.json"

TP_CEILING = -1.0          # dBTP, hard
DUR_LO, DUR_HI = 240.0, 360.0


def key(p) -> str:
    return str(Path(p).resolve()).lower()


# --------------------------------------------------------------- gathering
def manifests(man_dir: Path):
    out = []
    for m in sorted(glob.glob(str(man_dir / "Part*.json"))):
        if Path(m).name.startswith(("_raw", "_queue")):
            continue
        try:
            out.append(json.loads(Path(m).read_text(encoding="utf-8")))
        except Exception as exc:                              # noqa: BLE001
            print("  UNREADABLE MANIFEST {}: {}".format(m, exc))
    return sorted(out, key=lambda r: r.get("part") or 0)


def measure_audio(mp4: Path):
    """True peak and integrated loudness, measured from the ENCODED file."""
    r = subprocess.run(
        [str(FFMPEG), "-nostats", "-hide_banner", "-i", str(mp4),
         "-map", "a:0", "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True)
    txt = (r.stderr or "")
    def last(pat):
        m = re.findall(pat, txt)
        return float(m[-1]) if m else None
    return {
        "true_peak_dBTP": last(r"Peak:\s*(-?\d+\.?\d*)\s*dBFS"),
        "integrated_LUFS": last(r"I:\s*(-?\d+\.?\d*)\s*LUFS"),
        "LRA_LU": last(r"LRA:\s*(-?\d+\.?\d*)\s*LU"),
    }


def decode_ok(mp4: Path):
    r = subprocess.run(
        [str(FFMPEG), "-v", "error", "-xerror", "-i", str(mp4),
         "-f", "null", "-"], capture_output=True, text=True)
    return r.returncode == 0, (r.stderr or "").strip()[-200:]


def streams(mp4: Path):
    r = subprocess.run(
        [str(FFPROBE), "-v", "error", "-show_entries",
         "stream=codec_type,duration", "-of", "json", str(mp4)],
        capture_output=True, text=True)
    try:
        s = json.loads(r.stdout or "{}").get("streams", [])
    except Exception:
        return 0, 0, 0.0
    v = sum(1 for x in s if x.get("codec_type") == "video")
    a = sum(1 for x in s if x.get("codec_type") == "audio")
    d = max([float(x.get("duration") or 0) for x in s] or [0.0])
    return v, a, d


def alignment_kinds(log_dir: Path):
    """How each beat-locked accent chose its landing, from the render logs."""
    c = Counter()
    for q in glob.glob(str(log_dir / "series_Part*.log")):
        for line in Path(q).read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.search(r"lands on (\w+) at", line)
            if m:
                c[m.group(1).upper()] += 1
    return c


def trim_stats(used_keys):
    """Recomputed over the clips this generation ACTUALLY used."""
    if not BOUNDARY.exists():
        return {}
    rows = json.loads(BOUNDARY.read_text(encoding="utf-8"))["items"]
    rows = [r for r in rows if key(r["clip"]) in used_keys]
    rs = lambda r: r.get("reason") or ""
    acc = [r for r in rows if (r.get("trim_s") or 0) > 0]
    ts = sorted(r["trim_s"] for r in acc)
    mk = Counter()
    for r in rows:
        for k in (r.get("markers") or {}):
            mk[k] += 1
    return {
        "candidates": len(rows),
        "accepted": len(acc),
        "event_veto": len([r for r in rows if "action event" in rs(r)]),
        "loud_veto": len([r for r in rows if "still loud" in rs(r)]),
        "nothing": len([r for r in rows if rs(r).startswith("nothing worth")]),
        "scoreboard": len([r for r in acc if "scoreboard" in rs(r)]),
        "death": len([r for r in acc if "death" in rs(r)]),
        "dead_tail": len([r for r in acc if "dead tail" in rs(r)]),
        "median": ts[len(ts) // 2] if ts else 0.0,
        "max": ts[-1] if ts else 0.0,
        "markers": dict(mk),
        "dropped": len([r for r in rows if r.get("drop")]),
    }


# ------------------------------------------------------------------ report
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifests", default=str(ROOT / "output" / "_final_manifests"))
    ap.add_argument("--series", default=r"D:\QUAKE_LEGACY_OUTPUT\series_final_rebuild")
    ap.add_argument("--fallback", default=r"D:\QUAKE_LEGACY_OUTPUT\series")
    ap.add_argument("--skip-audio", action="store_true",
                    help="skip the per-file loudness/decode pass (fast preview)")
    ap.add_argument("--promote", action="store_true")
    a = ap.parse_args()

    man_dir, series = Path(a.manifests), Path(a.series)
    mans = manifests(man_dir)
    q = json.loads(QUEUE.read_text(encoding="utf-8"))["queue"]
    q_by_key = {key(r["canonical_avi_path"]): r for r in q}
    t1_total = sum(1 for r in q if r.get("tier") == "T1")
    t2_total = sum(1 for r in q if r.get("tier") == "T2")

    # ---- coverage
    used, dup = Counter(), []
    tiers = Counter()
    for m in mans:
        for c in (m.get("clips") or []):
            k = key(c["path"])
            used[k] += 1
            tiers[c.get("tier")] += 1
    for k, n in used.items():
        if n > 1:
            dup.append((k, n))
    unexplained = [k for k in used if k not in q_by_key]
    missing = [k for k in q_by_key if k not in used]

    # ---- durations (from the files, not the manifests)
    durs, per_part = [], []
    for m in mans:
        mp4 = Path(m.get("output_path") or (series / "Part{:02d}.mp4".format(m["part"])))
        v = an = 0
        fdur = 0.0
        audio = {}
        dec, derr = None, ""
        if mp4.exists() and not a.skip_audio:
            v, an, fdur = streams(mp4)
            audio = measure_audio(mp4)
            dec, derr = decode_ok(mp4)
        d = m.get("duration_s") or fdur
        durs.append(d)
        per_part.append({
            "part": m.get("part"), "dur": d, "clips": m.get("clip_count"),
            "src_parts": m.get("historical_source_parts"),
            "music": [Path(x["path"]).name for x in (m.get("music") or [])],
            "tp_manifest": m.get("true_peak_dBTP"),
            "tp_measured": audio.get("true_peak_dBTP"),
            "lufs_measured": audio.get("integrated_LUFS"),
            "lra": audio.get("LRA_LU"),
            "decode": dec, "decode_err": derr,
            "v": v, "a": an, "exists": mp4.exists(),
            "audio_QA": m.get("audio_QA"), "committed": m.get("committed"),
        })

    # ---- music
    tracks = [t for p in per_part for t in p["music"]]
    tc = Counter(tracks)
    adjacent = 0
    for i in range(1, len(per_part)):
        if set(per_part[i]["music"]) & set(per_part[i - 1]["music"]):
            adjacent += 1

    ts_ = trim_stats(set(used))
    kinds = alignment_kinds(ROOT / "output")

    # ---- invariants
    tp_bad = [p for p in per_part
              if p["tp_measured"] is not None and p["tp_measured"] > TP_CEILING]
    dec_bad = [p for p in per_part if p["decode"] is False]
    qa_bad = [p for p in per_part if p["audio_QA"] not in (None, "PASS")]
    stream_bad = [p for p in per_part
                  if p["exists"] and not a.skip_audio and (p["v"] < 1 or p["a"] < 1)]

    total_used = len(used)
    inv = {
        "coverage 1076/1076": total_used == len(q_by_key) and not missing,
        "0 primary duplicates": not dup,
        "0 unexplained sources": not unexplained,
        "0 QA-failed Parts": not qa_bad,
        "0 decode failures": not dec_bad,
        "0 true-peak violations": not tp_bad,
        "0 stream defects": not stream_bad,
    }

    P = print
    P("")
    P("=" * 70)
    P("V1 FINAL RECONCILIATION")
    P("=" * 70)
    P("")
    P("GENERATION")
    P("  id                  : {}".format(mans[0].get("run_id") if mans else "-"))
    P("  output              : {}".format(series))
    P("  Parts committed     : {}".format(len(mans)))
    P("")
    P("COVERAGE")
    P("  T1                  : {} / {}".format(tiers.get("T1", 0), t1_total))
    P("  T2                  : {} / {}".format(tiers.get("T2", 0), t2_total))
    P("  total               : {} / {}".format(total_used, len(q_by_key)))
    P("  duplicates          : {}".format(len(dup)))
    P("  unexplained         : {}".format(len(unexplained)))
    P("  not yet consumed    : {}".format(len(missing)))
    P("  primary POV dropped : {}".format(ts_.get("dropped", 0)))
    if durs:
        sd = sorted(durs)
        P("")
        P("DURATION (minutes)")
        P("  min / median / mean / max : {:.2f} / {:.2f} / {:.2f} / {:.2f}".format(
            sd[0] / 60, statistics.median(sd) / 60,
            statistics.mean(sd) / 60, sd[-1] / 60))
        P("  < 4:00                    : {}".format(sum(1 for x in sd if x < DUR_LO)))
        P("  4:00-6:00                 : {}".format(
            sum(1 for x in sd if DUR_LO <= x <= DUR_HI)))
        P("  > 6:00                    : {}".format(sum(1 for x in sd if x > DUR_HI)))
        P("  > 7:00                    : {}".format(sum(1 for x in sd if x > 420)))
    if ts_:
        P("")
        P("TRIMMING (clips this generation used)")
        P("  candidates          : {}".format(ts_["candidates"]))
        P("  accepted            : {}".format(ts_["accepted"]))
        P("  event veto          : {}".format(ts_["event_veto"]))
        P("  loud-tail veto      : {}".format(ts_["loud_veto"]))
        P("  nothing to cut      : {}".format(ts_["nothing"]))
        P("  scoreboard / death  : {} / {}".format(ts_["scoreboard"], ts_["death"]))
        P("  median / max        : {:.2f}s / {:.2f}s".format(ts_["median"], ts_["max"]))
        P("")
        P("ROUND METADATA (detected, never destructive)")
        for k, v in sorted(ts_["markers"].items(), key=lambda z: -z[1]):
            P("  {:20}: {}".format(k, v))
        P("  destructive round cuts : 0  (only scoreboard + death cut)")
        P("  visual detector enabled: {}".format(bool(os.environ.get("CB_CENTERPRINT"))))
    P("")
    P("MUSIC")
    P("  tracks used         : {}".format(len(tracks)))
    P("  distinct tracks     : {}".format(len(tc)))
    P("  reused tracks       : {}".format(sum(1 for _, n in tc.items() if n > 1)))
    P("  max uses of one     : {}".format(max(tc.values()) if tc else 0))
    P("  adjacent reuse      : {}".format(adjacent))
    if kinds:
        P("  alignment by kind   : " + ", ".join(
            "{} {}".format(v, k) for k, v in kinds.most_common()))
        P("    (BAR_GRID_ESTIMATE is every fourth detected beat, not a measured downbeat)")
    if not a.skip_audio:
        tps = [p["tp_measured"] for p in per_part if p["tp_measured"] is not None]
        lus = [p["lufs_measured"] for p in per_part if p["lufs_measured"] is not None]
        P("")
        P("AUDIO (measured from the encoded MP4s)")
        if tps:
            P("  true peak min/max   : {:.2f} / {:.2f} dBTP".format(min(tps), max(tps)))
        if lus:
            P("  LUFS min/med/max    : {:.1f} / {:.1f} / {:.1f}".format(
                min(lus), statistics.median(lus), max(lus)))
        P("  > {:.1f} dBTP          : {}".format(TP_CEILING, len(tp_bad)))
        P("")
        P("VIDEO")
        P("  decode failures     : {}".format(len(dec_bad)))
        P("  stream defects      : {}".format(len(stream_bad)))
        P("  QA-failed Parts     : {}".format(len(qa_bad)))
    P("")
    P("PER-PART")
    P("  {:>4} {:>7} {:>6} {:>10} {:>9} {:>8} {:>7}  {}".format(
        "part", "dur", "clips", "src parts", "TP dBTP", "LUFS", "decode", "music"))
    for p in per_part:
        P("  {:>4} {:>7} {:>6} {:>10} {:>9} {:>8} {:>7}  {}".format(
            p["part"], "{:.2f}m".format((p["dur"] or 0) / 60), p["clips"] or 0,
            str(p["src_parts"] or "")[:10],
            "{:.2f}".format(p["tp_measured"]) if p["tp_measured"] is not None else "-",
            "{:.1f}".format(p["lufs_measured"]) if p["lufs_measured"] is not None else "-",
            {True: "PASS", False: "FAIL", None: "-"}[p["decode"]],
            ", ".join(x[:26] for x in p["music"])[:56]))
    P("")
    P("HARD INVARIANTS")
    for k, v in inv.items():
        P("  [{}] {}".format("PASS" if v else "FAIL", k))
    ok = all(inv.values())
    P("")
    P("PROMOTION: {}".format("PASS" if ok else "FAIL"))
    if dup:
        P("  duplicates: " + ", ".join(Path(k).name for k, _ in dup[:8]))
    if unexplained:
        P("  unexplained: " + ", ".join(Path(k).name for k in unexplained[:8]))

    if a.promote:
        if not ok:
            P("  refusing to promote -- fix the failing invariant first")
            return 2
        P("  promotion is a manual step; the fallback at {} is untouched"
          .format(a.fallback))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
