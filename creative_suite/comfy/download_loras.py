"""Download all QUAKE LEGACY style LoRAs from Civitai with resume + auth support.

Usage:
  python -u creative_suite/comfy/download_loras.py
  python -u creative_suite/comfy/download_loras.py --token YOUR_CIVITAI_API_KEY

Get your Civitai API key:
  civitai.com -> Account Settings -> API Keys -> Add API Key
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests

DEST_DIR = Path(r"E:\PersonalAI\ComfyUI\models\loras")
DEST_DIR.mkdir(parents=True, exist_ok=True)

LORAS = [
    {
        "name":     "PhotorealTouch SDXL v3",
        "url":      "https://civitai.com/api/download/models/1740069",
        "filename": "Photov3-000008.safetensors",
        "size_mb":  223,
    },
    {
        "name":     "Photorealistic Slider SDXL v1.0",
        "url":      "https://civitai.com/api/download/models/126807",
        "filename": "sdxl_photorealistic_slider_v1-0.safetensors",
        "size_mb":  144,
    },
    {
        "name":     "Neonify SDXL v2.3 Extreme",
        "url":      "https://civitai.com/api/download/models/135584",
        "filename": "NeonifyV2-4Extreme.safetensors",
        "size_mb":  1820,
    },
]


def _download(item: dict, token: str | None) -> bool:
    dest = DEST_DIR / item["filename"]
    name = item["name"]
    url  = item["url"]
    if token:
        url = url + f"?token={token}"

    existing = dest.stat().st_size if dest.exists() else 0

    if existing > 0:
        # Quick sanity check — if file is within 1% of expected size, skip
        expected = item["size_mb"] * 1024 * 1024
        if existing >= expected * 0.99:
            print(f"  SKIP (complete): {name}  ({existing / 1e6:.1f} MB)")
            return True
        print(f"  Resuming {name} from {existing / 1e6:.1f} MB...")
    else:
        print(f"  Downloading {name}  (~{item['size_mb']} MB)...")

    headers = {"Range": f"bytes={existing}-"} if existing else {}

    try:
        with requests.get(url, headers=headers, stream=True,
                          timeout=60, allow_redirects=True) as r:

            # Civitai returns HTML login page when auth is missing
            ct = r.headers.get("Content-Type", "")
            if r.status_code in (401, 403):
                print(f"  AUTH ERROR {r.status_code}: Civitai requires an API token.")
                print(f"  Run with: --token YOUR_CIVITAI_API_KEY")
                print(f"  Get key:  civitai.com -> Account Settings -> API Keys")
                return False
            if "text/html" in ct:
                print(f"  AUTH ERROR: Got HTML (login page) instead of file.")
                print(f"  Run with: --token YOUR_CIVITAI_API_KEY")
                return False
            if r.status_code == 416:
                print(f"  SKIP (server says complete): {name}")
                return True
            r.raise_for_status()

            total = int(r.headers.get("Content-Length", 0)) + existing
            print(f"  Target: {dest}")
            print(f"  Total:  {total / 1e6:.0f} MB")

            mode = "ab" if existing else "wb"
            downloaded = existing
            with open(dest, mode) as f:
                for chunk in r.iter_content(chunk_size=2 * 1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        pct = 100 * downloaded / total if total else 0
                        bar = "#" * int(pct / 2)
                        print(
                            f"\r    [{bar:<50}] {downloaded / 1e6:>6.0f}/{total / 1e6:.0f} MB  {pct:.0f}%",
                            end="", flush=True,
                        )

        print(f"\n  OK: {dest.stat().st_size / 1e6:.1f} MB written")
        return True

    except requests.RequestException as exc:
        print(f"\n  ERR: {exc}")
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=os.environ.get("CIVITAI_TOKEN", ""),
                    help="Civitai API token (or set CIVITAI_TOKEN env var)")
    args = ap.parse_args()

    token = args.token or None

    print("=" * 64)
    print("QUAKE LEGACY — LoRA Downloads")
    print(f"  Destination: {DEST_DIR}")
    print(f"  Auth token:  {'SET' if token else 'NOT SET — will fail if Civitai requires auth'}")
    print("=" * 64)

    results = []
    for item in LORAS:
        print()
        ok = _download(item, token)
        results.append((item["name"], ok))

    print("\n" + "=" * 64)
    for name, ok in results:
        status = "OK " if ok else "FAIL"
        print(f"  [{status}] {name}")

    failed = [n for n, ok in results if not ok]
    if failed:
        print(f"\n{len(failed)} download(s) failed.")
        print("If auth errors: run with --token YOUR_CIVITAI_API_KEY")
        sys.exit(1)
    print("\nAll LoRAs downloaded. Restart ComfyUI to load them.")


if __name__ == "__main__":
    main()
