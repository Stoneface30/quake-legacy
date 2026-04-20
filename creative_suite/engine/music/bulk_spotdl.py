"""bulk_spotdl.py — download 1058 Spotify URIs via spotdl (no auth).

WHY
---
zotify's user/pass auth is dead server-side in 2025. spotdl's default
`youtube-music` provider ships 2-min radio edits. Solution: spotdl with
`piped soundcloud bandcamp youtube` priority — pulls full uploads, no auth.

INVARIANTS
----------
  * Output: phase1/music/library/{Artist} - {Title}.mp3 @ 320k
  * Batch size: 20 URIs per spotdl invocation (cli arg-length safe)
  * Per-batch log: library/_spotdl_log.jsonl
  * Idempotent: spotdl --overwrite skip honors pre-existing files
  * Explicit ffmpeg path (tools/ffmpeg/ffmpeg.exe)
  * Never raises on per-batch failure — logs and continues

CLI
---
    python phase1/music/bulk_spotdl.py                # full queue (1058)
    python phase1/music/bulk_spotdl.py --limit 10     # first 10
    python phase1/music/bulk_spotdl.py --batch 20
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = PROJECT_ROOT / "phase1" / "music" / "library"
QUEUE_PATH = PROJECT_ROOT / "phase1" / "music" / "_download_queue.txt"
LOG_PATH = LIB_DIR / "_spotdl_log.jsonl"
FFMPEG_BIN = PROJECT_ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"


def load_queue() -> list[str]:
    if not QUEUE_PATH.exists():
        print(f"[bulk-spotdl] queue missing: {QUEUE_PATH}", file=sys.stderr)
        sys.exit(2)
    return [ln.strip() for ln in QUEUE_PATH.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith("spotify:track:")]


def run_batch(uris: list[str], batch_idx: int, total_batches: int) -> dict:
    cmd = [
        sys.executable, "-m", "spotdl", "download",
        *uris,
        "--audio", "piped", "soundcloud", "bandcamp", "youtube",
        "--format", "mp3",
        "--bitrate", "320k",
        "--ffmpeg", str(FFMPEG_BIN),
        "--output", str(LIB_DIR / "{artist} - {title}.{output-ext}"),
        "--overwrite", "skip",
        "--print-errors",
        "--threads", "4",
    ]
    t0 = time.time()
    print(f"[bulk-spotdl] batch {batch_idx}/{total_batches} "
          f"({len(uris)} URIs)...", flush=True)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=1800)
        rc = proc.returncode
        stdout_tail = (proc.stdout or "").splitlines()[-30:]
        stderr_tail = (proc.stderr or "").splitlines()[-15:]
    except subprocess.TimeoutExpired:
        rc, stdout_tail, stderr_tail = 124, [], ["TIMEOUT after 1800s"]
    elapsed = time.time() - t0
    summary = {
        "batch": batch_idx,
        "uris": uris,
        "returncode": rc,
        "elapsed_s": round(elapsed, 1),
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "ts": datetime.utcnow().isoformat() + "Z",
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")
    status = "OK" if rc == 0 else f"FAIL(rc={rc})"
    files = len(list(LIB_DIR.glob("*.mp3")))
    print(f"[bulk-spotdl] batch {batch_idx} {status} in {elapsed:.1f}s "
          f"({files} mp3 in library)", flush=True)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--offset", type=int, default=0)
    args = ap.parse_args()

    LIB_DIR.mkdir(parents=True, exist_ok=True)
    uris = load_queue()
    if args.offset:
        uris = uris[args.offset:]
    if args.limit:
        uris = uris[:args.limit]

    print(f"[bulk-spotdl] {len(uris)} URIs "
          f"(offset={args.offset}, limit={args.limit or 'all'})")
    print(f"[bulk-spotdl] library: {LIB_DIR}")
    print(f"[bulk-spotdl] log:     {LOG_PATH}")

    batches = [uris[i:i + args.batch] for i in range(0, len(uris), args.batch)]
    print(f"[bulk-spotdl] {len(batches)} batches of ~{args.batch}")

    t_start = time.time()
    fails = 0
    for i, batch in enumerate(batches, 1):
        s = run_batch(batch, i, len(batches))
        if s["returncode"] != 0:
            fails += 1

    total_elapsed = time.time() - t_start
    files = len(list(LIB_DIR.glob("*.mp3")))
    print("")
    print("=" * 60)
    print(f"DONE — {len(batches)} batches, {fails} failed, "
          f"{total_elapsed/60:.1f} min total")
    print(f"mp3 files in library: {files} / {len(uris)} requested "
          f"({100*files/max(len(uris),1):.1f}%)")
    print("=" * 60)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
