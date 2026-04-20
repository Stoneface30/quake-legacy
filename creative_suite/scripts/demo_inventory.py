"""Walk G:\\ for *.dm_73 files; emit inventory JSON with sha256."""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path("G:/")
OUT = Path("G:/QUAKE_LEGACY/docs/research/demo-inventory-2026-04-17.json")
SKIP_PREFIXES = (
    "C:/Program Files (x86)/Steam",
    "C:/Program Files/Steam",
)

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    items = []
    t0 = time.time()
    n = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # System / recycle bin skips
        low = dirpath.lower().replace("\\", "/")
        if "$recycle.bin" in low or "/system volume information" in low:
            dirnames[:] = []
            continue
        for fn in filenames:
            if not fn.lower().endswith(".dm_73"):
                continue
            p = Path(dirpath) / fn
            try:
                st = p.stat()
                sha = sha256_file(p)
            except (OSError, PermissionError) as e:
                print(f"SKIP {p}: {e}", file=sys.stderr)
                continue
            items.append({
                "path": str(p).replace("\\", "/"),
                "size": st.st_size,
                "mtime": st.st_mtime,
                "sha256": sha,
            })
            n += 1
            if n % 100 == 0:
                print(f"  scanned {n} demos ({time.time()-t0:.1f}s)", file=sys.stderr)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, indent=2))
    print(f"DONE: {len(items)} demos in {time.time()-t0:.1f}s -> {OUT}")

if __name__ == "__main__":
    main()
