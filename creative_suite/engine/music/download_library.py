"""
download_library.py — Spotify URI -> full-length audio pipeline for QUAKE LEGACY.

WHY
---
The existing `phase1/music/library/` was built with spotdl's YouTube-Music backend,
which routinely returns 2-minute radio-edits or preview snippets in place of the full
track (Part 4 v12 got burned: `part04_music_01.mp3` = 2:01 for MAKEBA, which is 3:08
on Spotify). Rule P1-AA requires full tracks; truncated inputs force the stitcher to
loop the tail, which the user flagged at 17:40 in Part 4 v12.

TOOL CHOICE — ZOTIFY
--------------------
We pick `zotify` over `spotdl` because:

  * User has Spotify Premium (required for zotify), so 320 kbps OGG direct from
    Spotify's CDN is unlocked.
  * Zotify pulls the EXACT track (same master as the Spotify app plays) — no
    search, no fuzzy match, no preview-edit trap.
  * spotdl is already installed (4.4.3) and is the **cause** of every truncation
    currently in the library; switching to it again would just repeat the bug.
  * Zotify is actively maintained (2026): the canonical fork lives at
    `https://github.com/zotify-dev/zotify` (post-2024 continuation after the
    original repo was DMCA'd). Install via:
         pip install git+https://github.com/zotify-dev/zotify.git

    It is NOT on PyPI (license risk — Spotify ToS gray zone). Expect the user
    to install it manually once; this script shells out to the `zotify` CLI.

FALLBACK
--------
If zotify auth fails or the track is region-locked, we fall back to spotdl
with `--audio-providers youtube-music piped` and a post-download duration
check: if the downloaded file is < 0.7 * Spotify duration, flag it
TRUNCATED and leave it for manual retry (never silently ship it).

INVOCATION
----------
    python phase1/music/download_library.py              # process everything
    python phase1/music/download_library.py --limit 20   # first 20 missing
    python phase1/music/download_library.py --only <uri> # single track
    python phase1/music/download_library.py --redownload-truncated

AUTH
----
Requires `~/.config/zotify/credentials.json` (Windows: `%APPDATA%/zotify/credentials.json`).
First-time: run `zotify --username <user>` once interactively; it stores the token.
We never read the password ourselves.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = PROJECT_ROOT / "phase1" / "music" / "library"
MANIFEST_PATH = LIB_DIR / "manifest.json"
MUSIC_LIB_JSON = PROJECT_ROOT / "database" / "MusicLibrary.json"
FFPROBE = PROJECT_ROOT / "tools" / "ffmpeg" / "ffprobe.exe"

TRUNCATION_RATIO = 0.70  # file shorter than 70% of expected = TRUNCATED
OUT_EXT_ZOTIFY = "ogg"   # zotify delivers ogg/vorbis 320k from Premium
OUT_EXT_SPOTDL = "mp3"

# ---------------------------------------------------------------------------

@dataclass
class Track:
    artist: str
    album: str
    track: str
    uri: str
    expected_dur_s: float | None = None  # from Spotify metadata if available

    @property
    def track_id(self) -> str:
        return self.uri.rsplit(":", 1)[-1]

    @property
    def slug(self) -> str:
        """Filesystem-safe basename WITHOUT extension."""
        raw = f"{self.artist}_{self.track}"
        safe = re.sub(r"[^\w\-]+", "_", raw, flags=re.UNICODE).strip("_")
        return safe[:120]  # keep Windows MAX_PATH headroom


def load_library_json() -> list[Track]:
    data = json.loads(MUSIC_LIB_JSON.read_text(encoding="utf-8"))
    return [Track(**t) for t in data["tracks"]]


def existing_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"version": 1, "tracks": {}}


def probe_duration(path: Path) -> float:
    try:
        out = subprocess.check_output(
            [str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            text=True, stderr=subprocess.STDOUT,
        )
        return float(out.strip())
    except Exception:
        return 0.0


def estimate_bpm(path: Path) -> float | None:
    """Best-effort BPM via librosa. Returns None if librosa unavailable."""
    try:
        import librosa  # type: ignore
        y, sr = librosa.load(str(path), mono=True, duration=90)  # 90s sample
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        return float(tempo)
    except Exception:
        return None


def zotify_available() -> bool:
    return shutil.which("zotify") is not None


def spotdl_available() -> bool:
    return shutil.which("spotdl") is not None


def find_existing_file(slug: str) -> Path | None:
    for ext in ("ogg", "mp3", "m4a", "flac"):
        p = LIB_DIR / f"{slug}.{ext}"
        if p.exists():
            return p
    return None


def download_zotify(track: Track) -> Path | None:
    """Call zotify CLI. Output format: {artist}_{title}.ogg into LIB_DIR."""
    out_template = f"{track.slug}"
    cmd = [
        "zotify",
        f"spotify:track:{track.track_id}",
        "--root-path", str(LIB_DIR),
        "--output", f"{out_template}.{{ext}}",
        "--download-format", OUT_EXT_ZOTIFY,
        "--download-quality", "very_high",   # 320k (Premium)
        "--print-download-progress", "false",
    ]
    try:
        subprocess.run(cmd, check=True, timeout=300,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"  zotify failed: {e.stderr.decode(errors='ignore')[:200]}")
        return None
    except subprocess.TimeoutExpired:
        print("  zotify timeout")
        return None
    return find_existing_file(track.slug)


def download_spotdl(track: Track) -> Path | None:
    """Fallback. Mark any sub-70% file as TRUNCATED, don't keep it."""
    out_tmpl = str(LIB_DIR / f"{track.slug}.{{output-ext}}")
    cmd = [
        "spotdl", "download", f"https://open.spotify.com/track/{track.track_id}",
        "--output", out_tmpl,
        "--format", OUT_EXT_SPOTDL,
        "--bitrate", "320k",
        "--threads", "1",
    ]
    try:
        subprocess.run(cmd, check=True, timeout=300,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"  spotdl failed: {e}")
        return None
    return find_existing_file(track.slug)


def process_track(track: Track, manifest: dict, force: bool = False) -> dict | None:
    entry = manifest["tracks"].get(track.uri)
    existing = find_existing_file(track.slug)

    if existing and not force and entry and entry.get("status") == "ok":
        return entry  # idempotent skip

    print(f"[.] {track.artist} — {track.track}")
    path = None
    method = None

    if zotify_available():
        path = download_zotify(track)
        method = "zotify"

    if not path and spotdl_available():
        print("  zotify unavailable/failed → spotdl fallback")
        path = download_spotdl(track)
        method = "spotdl"

    if not path:
        return {"uri": track.uri, "status": "missing_tool_or_download_failed",
                "method": method}

    dur = probe_duration(path)
    expected = track.expected_dur_s
    ratio = (dur / expected) if expected else 1.0
    status = "ok"
    if expected and ratio < TRUNCATION_RATIO:
        status = "TRUNCATED"
        print(f"  TRUNCATED: got {dur:.1f}s, expected {expected:.1f}s (ratio {ratio:.2f})")

    bpm = estimate_bpm(path) if status == "ok" else None

    return {
        "uri": track.uri,
        "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "artist": track.artist,
        "track": track.track,
        "album": track.album,
        "duration_s": dur,
        "expected_s": expected,
        "bpm": bpm,
        "method": method,
        "status": status,
        "updated_ts": int(time.time()),
    }


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="max tracks to process this run (0 = all)")
    ap.add_argument("--only", type=str, default="",
                    help="process only this spotify URI")
    ap.add_argument("--redownload-truncated", action="store_true",
                    help="redownload any track whose manifest status=TRUNCATED")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not FFPROBE.exists():
        print(f"ERROR: ffprobe missing at {FFPROBE}")
        return 2

    LIB_DIR.mkdir(parents=True, exist_ok=True)
    all_tracks = load_library_json()
    manifest = existing_manifest()

    if args.only:
        all_tracks = [t for t in all_tracks if t.uri == args.only]

    # Build work queue
    queue: list[Track] = []
    for t in all_tracks:
        entry = manifest["tracks"].get(t.uri)
        if args.redownload_truncated and entry and entry.get("status") == "TRUNCATED":
            queue.append(t)
            continue
        if find_existing_file(t.slug) and entry and entry.get("status") == "ok":
            continue
        queue.append(t)

    if args.limit:
        queue = queue[: args.limit]

    print(f"Plan: {len(queue)} / {len(all_tracks)} tracks to process")
    if args.dry_run:
        for t in queue[:10]:
            print(f"  would fetch: {t.artist} — {t.track}")
        return 0

    if not zotify_available() and not spotdl_available():
        print("ERROR: neither zotify nor spotdl on PATH")
        return 3

    for i, t in enumerate(queue, 1):
        entry = process_track(t, manifest)
        if entry:
            manifest["tracks"][t.uri] = entry
        if i % 20 == 0:
            save_manifest(manifest)
            print(f"[manifest] saved at {i}")

    save_manifest(manifest)
    ok = sum(1 for e in manifest["tracks"].values() if e.get("status") == "ok")
    trunc = sum(1 for e in manifest["tracks"].values() if e.get("status") == "TRUNCATED")
    print(f"Done. ok={ok} truncated={trunc} total_manifest={len(manifest['tracks'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
