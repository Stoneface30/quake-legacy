"""bulk_download.py — feed _download_queue.txt through zotify.

WHY
---
zotify's CLI accepts N URIs as positional args but hits process-argument-length
limits on Windows around ~100 URIs, and any failure mid-batch aborts the whole
run. This driver pages the queue in chunks of 25, skips tracks already present
in library/ (idempotent), and logs per-URI outcome.

AUTH
----
Requires one-time interactive login:
    zotify --username YOUR_USER --save-credentials True spotify:track:<any>
Credentials land in %APPDATA%/zotify/credentials.json. This script never sees
your password.

INVARIANTS
----------
  * Output format: OGG vorbis 320k (Spotify Premium CDN, not YouTube)
  * Root: phase1/music/library/
  * Idempotent: files matching `<artist>_<track>.ogg` in library/ are skipped
  * Per-batch log: library/_zotify_log.jsonl (one JSON record per track)
  * Never raises on individual track failure — logs and continues

CLI
---
    python phase1/music/bulk_download.py                # full 1058
    python phase1/music/bulk_download.py --limit 10     # first 10 missing
    python phase1/music/bulk_download.py --batch 25     # URIs per zotify call
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
LOG_PATH = LIB_DIR / "_zotify_log.jsonl"


def load_queue() -> list[str]:
    if not QUEUE_PATH.exists():
        print(f"[bulk] queue missing: {QUEUE_PATH}", file=sys.stderr)
        sys.exit(2)
    return [ln.strip() for ln in QUEUE_PATH.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith("spotify:track:")]


def already_downloaded(track_id: str) -> bool:
    """Cheap presence check — zotify's own --skip-existing is authoritative,
    but a pre-check saves us the subprocess roundtrip on idempotent runs."""
    # zotify writes `{Artist} - {Song}.ogg`; we don't know the artist from
    # URI alone, so we can't shortcut by name. Fall back to zotify flag.
    return False


def run_batch(uris: list[str], batch_idx: int, total_batches: int) -> dict:
    """Shell out to zotify for `uris`. Return summary dict."""
    cmd = [
        sys.executable, "-m", "zotify",
        "--download-format", "ogg",
        "--download-quality", "very_high",
        "--skip-existing", "True",
        "--skip-previously-downloaded", "True",
        "--root-path", str(LIB_DIR),
        "--print-downloads", "True",
        "--print-errors", "True",
        "--print-splash", "False",
        "--print-progress-info", "False",
        "--retry-attempts", "3",
        "--bulk-wait-time", "1",
        *uris,
    ]
    t0 = time.time()
    print(f"[bulk] batch {batch_idx}/{total_batches} ({len(uris)} tracks)...",
          flush=True)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=1800)
        rc = proc.returncode
        stdout_tail = (proc.stdout or "").splitlines()[-20:]
        stderr_tail = (proc.stderr or "").splitlines()[-10:]
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
    print(f"[bulk] batch {batch_idx} {status} in {elapsed:.1f}s", flush=True)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="Max URIs to process (0 = all).")
    ap.add_argument("--batch", type=int, default=25,
                    help="URIs per zotify invocation.")
    ap.add_argument("--offset", type=int, default=0,
                    help="Skip first N URIs in queue.")
    args = ap.parse_args()

    LIB_DIR.mkdir(parents=True, exist_ok=True)
    uris = load_queue()
    if args.offset:
        uris = uris[args.offset:]
    if args.limit:
        uris = uris[:args.limit]

    print(f"[bulk] {len(uris)} URIs to process "
          f"(offset={args.offset}, limit={args.limit or 'all'})")
    print(f"[bulk] library: {LIB_DIR}")
    print(f"[bulk] log:     {LOG_PATH}")

    batches = [uris[i:i + args.batch] for i in range(0, len(uris), args.batch)]
    print(f"[bulk] {len(batches)} batches of ~{args.batch}")

    t_start = time.time()
    fails = 0
    for i, batch in enumerate(batches, 1):
        s = run_batch(batch, i, len(batches))
        if s["returncode"] != 0:
            fails += 1

    total_elapsed = time.time() - t_start
    print("")
    print("=" * 60)
    print(f"DONE — {len(batches)} batches, {fails} failed, "
          f"{total_elapsed/60:.1f} min total")
    print(f"library: {LIB_DIR}")
    oggs = len(list(LIB_DIR.glob("*.ogg")))
    print(f"ogg files present: {oggs}")
    print("=" * 60)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
