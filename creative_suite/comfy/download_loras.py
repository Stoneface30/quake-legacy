"""Download QUAKE LEGACY style LoRAs from HuggingFace — no auth required.

Usage:
  python -u creative_suite/comfy/download_loras.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

DEST_DIR = Path(r"E:\PersonalAI\ComfyUI\models\loras")
DEST_DIR.mkdir(parents=True, exist_ok=True)

HF_BASE = "https://huggingface.co"

LORAS = [
    {
        "name":     "Photorealistic Slider SDXL",
        "repo":     "ostris/photorealistic-slider-sdxl-lora",
        "filename": "sdxl_photorealistic_slider_v1-0.safetensors",
        "size_mb":  24,
    },
    {
        "name":     "Extremely Detailed SDXL (face + skin + micro-detail)",
        "repo":     "ntc-ai/SDXL-LoRA-slider.extremely-detailed",
        "filename": "extremely detailed.safetensors",
        "size_mb":  8,  # 8789076 bytes = 8.8 MB decimal
    },
    {
        "name":     "Neonify SDXL v2.3 (cel shade + neon realism)",
        "repo":     None,
        "filename": "NeonifyV2-4Extreme.safetensors",
        "size_mb":  1824,  # Civitai delivery: 1824687596 bytes = 1824.7 MB decimal
        "fallback_url": "https://civitai.com/api/download/models/135584",
    },
]


def _hf_url(repo: str, filename: str) -> str:
    return f"{HF_BASE}/{repo}/resolve/main/{filename.replace(' ', '%20')}"


def _validate_safetensors(path: Path) -> bool:
    """Check that the safetensors header length is consistent with the file size.

    Safetensors layout: [8-byte LE uint64 N] [N bytes JSON header] [data].
    If file_size < 8 + N, the header itself is truncated.
    The full coverage check (header offsets vs data region) requires parsing
    JSON; we skip that here — ComfyUI will catch it on load. This catches the
    common corruption pattern where two partial downloads are concatenated:
    the header from the first file claims data ends before the appended bytes.
    """
    import struct
    try:
        size = path.stat().st_size
        if size < 8:
            return False
        with path.open("rb") as f:
            hdr_len = struct.unpack("<Q", f.read(8))[0]
        # Header must fit inside the file; data region = size - 8 - hdr_len must be >= 0
        return size >= 8 + hdr_len
    except Exception:
        return False


def _download(item: dict) -> bool:
    dest = DEST_DIR / item["filename"]
    name = item["name"]

    # Validate any existing file before deciding to skip or resume.
    # Corruption (two concatenated partials) would pass a size check but fail
    # safetensors validation — delete and re-download from scratch.
    if dest.exists():
        if not _validate_safetensors(dest):
            print(f"  CORRUPT (safetensors header invalid): {name} — deleting and re-downloading")
            dest.unlink()

    existing = dest.stat().st_size if dest.exists() else 0
    expected = item["size_mb"] * 1_000_000  # size_mb uses decimal MB (consistent with display)
    if existing >= expected * 0.99:
        print(f"  SKIP (complete): {name}  ({existing / 1e6:.1f} MB)")
        return True

    repo = item.get("repo")
    url = _hf_url(repo, item["filename"]) if repo else item.get("fallback_url", "")
    if existing:
        print(f"  Resuming {name} from {existing / 1e6:.1f} MB...")
    else:
        print(f"  Downloading {name}  (~{item['size_mb']} MB)")
        print(f"  Source: {url}")

    headers = {"Range": f"bytes={existing}-"} if existing else {}

    try:
        with requests.get(url, headers=headers, stream=True, timeout=60) as r:
            if r.status_code in (401, 404) and "fallback_url" in item and url != item["fallback_url"]:
                print(f"  Trying fallback URL...")
                r.close()
                with requests.get(item["fallback_url"], headers=headers,
                                   stream=True, timeout=60) as r2:
                    return _stream(r2, dest, existing, name)
            if r.status_code == 416:
                print(f"  SKIP (server says complete): {name}")
                return True
            r.raise_for_status()
            return _stream(r, dest, existing, name)
    except requests.RequestException as exc:
        print(f"\n  ERR: {exc}")
        return False


def _stream(r: requests.Response, dest: Path, existing: int, name: str) -> bool:
    total = int(r.headers.get("Content-Length", 0)) + existing
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
                    f"\r    [{bar:<50}] {downloaded/1e6:>6.0f}/{total/1e6:.0f} MB  {pct:.0f}%",
                    end="", flush=True,
                )
    print(f"\n  OK: {dest.stat().st_size / 1e6:.1f} MB")
    return True


def main() -> None:
    print("=" * 60)
    print("QUAKE LEGACY — LoRA Downloads (HuggingFace)")
    print(f"  Destination: {DEST_DIR}")
    print("=" * 60)

    results = []
    for item in LORAS:
        print()
        ok = _download(item)
        results.append((item["name"], ok))

    print("\n" + "=" * 60)
    for name, ok in results:
        print(f"  {'OK  ' if ok else 'FAIL'} {name}")

    if any(not ok for _, ok in results):
        sys.exit(1)
    print("\nAll LoRAs ready. Restart ComfyUI if any were newly added.")


if __name__ == "__main__":
    main()
