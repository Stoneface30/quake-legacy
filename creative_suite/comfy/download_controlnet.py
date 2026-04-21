"""Download TTPLanet SDXL Tile ControlNet with progress + resume support."""
import sys
from pathlib import Path

import requests

URL  = "https://huggingface.co/TTPlanet/TTPLanet_SDXL_Controlnet_Tile_Realistic/resolve/main/TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors"
DEST = Path(r"E:\PersonalAI\ComfyUI\models\controlnet\TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors")

DEST.parent.mkdir(parents=True, exist_ok=True)

existing = DEST.stat().st_size if DEST.exists() else 0
headers  = {"Range": f"bytes={existing}-"} if existing else {}

print(f"Target: {DEST}")
print(f"Resuming from: {existing / 1e6:.1f} MB" if existing else "Starting fresh download...")

with requests.get(URL, headers=headers, stream=True, timeout=60) as r:
    if r.status_code == 416:
        print("File already complete.")
        sys.exit(0)
    r.raise_for_status()
    total = int(r.headers.get("Content-Length", 0)) + existing
    print(f"Total size: {total / 1e6:.0f} MB")

    with open(DEST, "ab" if existing else "wb") as f:
        downloaded = existing
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                pct = 100 * downloaded / total if total else 0
                print(f"\r  {downloaded / 1e6:.0f} / {total / 1e6:.0f} MB  ({pct:.0f}%)", end="", flush=True)

print(f"\nDone. {DEST.stat().st_size / 1e6:.1f} MB written.")
