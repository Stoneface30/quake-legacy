"""bulk_sc.py — download 1058 tracks via yt-dlp + SoundCloud search.

WHY
---
* Spotify killed librespot user/pass auth (zotify dead)
* spotdl hit Spotify API rate-limit (24h lockout)
* YouTube/YT-Music returns 2-min radio edits for electronic music

SoundCloud has full-length uploads (artists post real masters there), and
yt-dlp's `scsearch{N}:QUERY` hits SoundCloud search API directly — no Spotify
auth, no rate limit, no preview-edit trap.

PIPELINE
--------
For each track in MusicLibrary.json:
  1. query = "{artist} {track}"
  2. yt-dlp "scsearch5:{query}" with duration filter 150-600s
  3. take first result that passes filter
  4. transcode to mp3 320k via our ffmpeg
  5. save to library/{artist}_{track}.mp3 (sanitized)

INVARIANTS
----------
* Output: phase1/music/library/{ARTIST}_{TRACK}.mp3 (slug, 320k)
* Per-track log: library/_sc_log.jsonl
* Idempotent: skips files that already exist
* Per-track timeout: 120s (kills stuck downloads)
* Never raises on per-track failure — logs + continues

CLI
---
    python phase1/music/bulk_sc.py                # full 1058
    python phase1/music/bulk_sc.py --limit 10
    python phase1/music/bulk_sc.py --only "spotify:track:XXX"
    python phase1/music/bulk_sc.py --parts 4      # only Part 4's tracks
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = PROJECT_ROOT / "phase1" / "music" / "library"
MUSIC_LIB_JSON = PROJECT_ROOT / "database" / "MusicLibrary.json"
LOG_PATH = LIB_DIR / "_sc_log.jsonl"
FFMPEG_BIN = PROJECT_ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"

MIN_DUR_S = 150   # 2:30 — reject preview clips
MAX_DUR_S = 900   # 15:00 — reject podcasts/DJ-sets that might match artist
PER_TRACK_TIMEOUT = 120


def slugify(s: str, maxlen: int = 120) -> str:
    """Filesystem-safe slug. Preserves unicode, strips filesystem-hostile chars."""
    safe = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", s)
    safe = re.sub(r"\s+", "_", safe).strip("_")
    return safe[:maxlen]


def load_tracks() -> list[dict]:
    with MUSIC_LIB_JSON.open(encoding="utf-8") as f:
        data = json.load(f)
    tracks = data.get("tracks", [])
    seen = set()
    out = []
    for t in tracks:
        uri = t.get("uri", "")
        if not uri.startswith("spotify:track:") or uri in seen:
            continue
        seen.add(uri)
        out.append(t)
    return out


def expected_filename(t: dict) -> Path:
    artist = slugify(t.get("artist", "Unknown"), 60)
    track = slugify(t.get("track", "Unknown"), 80)
    return LIB_DIR / f"{artist}__{track}.mp3"


def already_have(t: dict) -> bool:
    return expected_filename(t).exists()


def download_one(t: dict) -> dict:
    """Try to fetch `t` via yt-dlp/scsearch. Return result dict."""
    dst = expected_filename(t)
    if dst.exists():
        return {"uri": t["uri"], "status": "skip_existing", "path": str(dst)}
    artist = t.get("artist", "")
    track = t.get("track", "")
    query = f"{artist} {track}".strip()
    tmp_stem = LIB_DIR / ("_dl_" + slugify(f"{artist}_{track}", 80))
    tmp_pattern = str(tmp_stem) + ".%(ext)s"
    cmd = [
        "yt-dlp",
        f"scsearch5:{query}",
        "--ffmpeg-location", str(FFMPEG_BIN),
        "-x", "--audio-format", "mp3", "--audio-quality", "0",
        "-o", tmp_pattern,
        "--no-playlist",
        "--match-filter", f"duration>={MIN_DUR_S} & duration<={MAX_DUR_S}",
        "--playlist-items", "1-5",
        "--break-on-existing",
        "--no-warnings",
        "--quiet",
        "--no-progress",
    ]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=PER_TRACK_TIMEOUT)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        return {"uri": t["uri"], "query": query, "status": "timeout",
                "elapsed_s": PER_TRACK_TIMEOUT}
    elapsed = round(time.time() - t0, 1)

    # yt-dlp writes <stem>.mp3 after ExtractAudio postprocessing
    out_mp3 = Path(str(tmp_stem) + ".mp3")
    if not out_mp3.exists():
        # Try any file matching the stem (different ext possible on edge)
        matches = list(LIB_DIR.glob(tmp_stem.name + ".*"))
        matches = [m for m in matches if m.suffix in (".mp3", ".m4a", ".opus", ".webm")]
        if matches:
            out_mp3 = matches[0]
    if not out_mp3.exists() or out_mp3.stat().st_size < 50_000:
        # clean up any partial
        for m in LIB_DIR.glob(tmp_stem.name + ".*"):
            m.unlink(missing_ok=True)
        tail = (proc.stderr or proc.stdout or "")[-300:]
        return {"uri": t["uri"], "query": query, "status": "no_result",
                "rc": rc, "elapsed_s": elapsed, "err_tail": tail}
    # Rename to canonical
    out_mp3.replace(dst)
    # Cleanup any siblings
    for m in LIB_DIR.glob(tmp_stem.name + ".*"):
        m.unlink(missing_ok=True)
    dur = probe_dur(dst)
    return {"uri": t["uri"], "query": query, "status": "ok",
            "path": str(dst), "duration_s": dur, "elapsed_s": elapsed}


def probe_dur(p: Path) -> float:
    try:
        r = subprocess.run(
            [str(PROJECT_ROOT / "tools" / "ffmpeg" / "ffprobe.exe"),
             "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
            capture_output=True, text=True, timeout=20)
        return round(float(r.stdout.strip() or "0"), 2)
    except Exception:
        return 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", type=str, default="",
                    help="Single URI to download, skip all others.")
    ap.add_argument("--offset", type=int, default=0)
    args = ap.parse_args()

    LIB_DIR.mkdir(parents=True, exist_ok=True)
    tracks = load_tracks()
    if args.only:
        tracks = [t for t in tracks if t["uri"] == args.only]
        if not tracks:
            print(f"[bulk-sc] --only {args.only} not in playlist", file=sys.stderr)
            return 2
    if args.offset:
        tracks = tracks[args.offset:]
    if args.limit:
        tracks = tracks[:args.limit]

    print(f"[bulk-sc] {len(tracks)} tracks to process "
          f"(offset={args.offset}, limit={args.limit or 'all'})")
    print(f"[bulk-sc] library: {LIB_DIR}")
    print(f"[bulk-sc] log:     {LOG_PATH}")
    print("")

    t_start = time.time()
    counts = {"ok": 0, "skip_existing": 0, "no_result": 0, "timeout": 0}
    for i, t in enumerate(tracks, 1):
        artist = t.get("artist", "?")[:40]
        track = t.get("track", "?")[:50]
        # L151: encode-safe print (cp1252 console chokes on unicode)
        _safe = f"[{i}/{len(tracks)}] {artist} - {track}"
        try:
            print(_safe, flush=True)
        except UnicodeEncodeError:
            print(_safe.encode("ascii", "replace").decode("ascii"), flush=True)
        result = download_one(t)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps({**result,
                                "ts": datetime.utcnow().isoformat() + "Z"}) + "\n")
        status = result["status"]
        counts[status] = counts.get(status, 0) + 1
        if status == "ok":
            try:
                print(f"    OK  {result['duration_s']}s  ({result['elapsed_s']}s)",
                      flush=True)
            except UnicodeEncodeError:
                print("    OK", flush=True)
        elif status == "skip_existing":
            print(f"    SKIP (already present)", flush=True)
        else:
            print(f"    FAIL  status={status}", flush=True)

    total = time.time() - t_start
    print("")
    print("=" * 60)
    for k, v in counts.items():
        print(f"  {k:15s}: {v}")
    print(f"  elapsed       : {total/60:.1f} min")
    print(f"  library count : {len(list(LIB_DIR.glob('*.mp3')))} mp3s")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
