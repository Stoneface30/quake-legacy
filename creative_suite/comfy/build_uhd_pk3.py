"""Build zzz_uhd_*.pk3 override packs from the upscale_only photoreal renders.

The trap this avoids (capture mandate §1): shipping .png at a path whose
original is .jpg/.tga silently loses the engine's extension-priority lookup —
assets would "exist" but never load. Every replacement is therefore written
at the ORIGINAL in-pak filename and extension, so zzz_* pak precedence
(ENG-2) decides deterministically.

Scope: any category passed via --categories; upscale_only renders are
shape-safe (pure CNN, no diffusion) so PH5-7 permits them even for
FX-routed categories. True FX sheets (gfx/weaphits/sprites/ui) are still
left stock for the master profile: alpha-edge fidelity on explosions and
beams outranks resolution.

Usage:
    python -u creative_suite/comfy/build_uhd_pk3.py [--categories textures players weapons2]
Writes staging wolfcam-ql/zzz_uhd_NN.pk3 (split under 1.8 GB each — the
engine's zip reader has no zip64) and output/demo_v2/uhd_pk3_manifest.json.
"""
from __future__ import annotations

import argparse
import io
import json
import sqlite3
import zipfile
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DB = REPO_ROOT / "creative_suite" / "comfy" / "photoreal" / "assets.db"
PHOTOREAL = REPO_ROOT / "creative_suite" / "comfy" / "photoreal"
STAGING_GAMEDIR = (REPO_ROOT / "output" / "demo_v2" / "_wolfcam_staging"
                   / "wolfcam-ql")
PAK00 = (REPO_ROOT / "output" / "demo_v2" / "_wolfcam_staging" / "baseq3"
         / "pak00.pk3")
MANIFEST_OUT = REPO_ROOT / "output" / "demo_v2" / "uhd_pk3_manifest.json"  # overwritten per run; offset keeps pk3 names distinct
SPLIT_BYTES = 1_800_000_000
MAX_DIM = 2048   # engine texture cap (glconfig scaling caps at 2048)


def pak00_index() -> dict[str, str]:
    """in-pak path WITHOUT extension -> actual pak00 name (with extension)."""
    idx: dict[str, str] = {}
    with zipfile.ZipFile(PAK00) as z:
        for name in z.namelist():
            p = Path(name)
            if p.suffix.lower() in (".tga", ".jpg", ".jpeg", ".png"):
                idx[str(p.with_suffix("")).replace("\\", "/").lower()] = name
    return idx


def convert(png_path: Path, target_ext: str) -> bytes | None:
    try:
        img = Image.open(png_path)
        img.load()
    except OSError:
        return None
    if max(img.size) > MAX_DIM:
        scale = MAX_DIM / max(img.size)
        img = img.resize((max(1, int(img.width * scale)),
                          max(1, int(img.height * scale))),
                         Image.LANCZOS)
    buf = io.BytesIO()
    ext = target_ext.lower()
    if ext in (".jpg", ".jpeg"):
        img.convert("RGB").save(buf, "JPEG", quality=95, subsampling=0)
    elif ext == ".tga":
        (img.convert("RGBA") if img.mode in ("RGBA", "LA", "P") else
         img.convert("RGB")).save(buf, "TGA")
    elif ext == ".png":
        img.save(buf, "PNG")
    else:
        return None
    return buf.getvalue()


def run(categories: list[str], offset: int = 0) -> dict:
    idx = pak00_index()
    conn = sqlite3.connect(f"file:{ASSETS_DB}?mode=ro", uri=True)
    rows = conn.execute(
        """SELECT a.rel_path, r.output_path FROM assets a
           JOIN renders r ON r.asset_id = a.id
           WHERE r.pipeline='upscale_only' AND r.status='ok'
             AND a.category IN (%s)"""
        % ",".join("?" * len(categories)), categories).fetchall()
    conn.close()

    manifest = {"included": [], "skipped": [], "pk3s": []}
    pk3_n, written = 1, 0
    zf = zipfile.ZipFile(STAGING_GAMEDIR / f"zzz_uhd_{pk3_n + offset:02d}.pk3", "w",
                         zipfile.ZIP_DEFLATED)
    manifest["pk3s"].append(zf.filename)

    for rel_path, output_path in rows:
        inpak_noext = str(Path(rel_path.split("pak00/", 1)[-1]
                               ).with_suffix("")).replace("\\", "/").lower()
        orig = idx.get(inpak_noext)
        if orig is None:
            manifest["skipped"].append({"asset": rel_path,
                                        "reason": "not in pak00"})
            continue
        src = PHOTOREAL / output_path
        if not src.exists():
            manifest["skipped"].append({"asset": rel_path,
                                        "reason": "render missing on disk"})
            continue
        data = convert(src, Path(orig).suffix)
        if data is None:
            manifest["skipped"].append({"asset": rel_path,
                                        "reason": "convert failed"})
            continue
        if written + len(data) > SPLIT_BYTES:
            zf.close()
            pk3_n += 1
            written = 0
            zf = zipfile.ZipFile(
                STAGING_GAMEDIR / f"zzz_uhd_{pk3_n + offset:02d}.pk3", "w",
                zipfile.ZIP_DEFLATED)
            manifest["pk3s"].append(zf.filename)
        zf.writestr(orig, data)
        written += len(data)
        manifest["included"].append({"pak_path": orig, "from": output_path})
    zf.close()

    manifest["counts"] = {"included": len(manifest["included"]),
                          "skipped": len(manifest["skipped"])}
    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--categories", nargs="+",
                    default=["textures", "players", "weapons2"])
    ap.add_argument("--offset", type=int, default=0,
                    help="pk3 numbering offset (avoid clobbering earlier packs)")
    args = ap.parse_args()
    m = run(args.categories, args.offset)
    print("included:", m["counts"]["included"],
          "skipped:", m["counts"]["skipped"])
    for p in m["pk3s"]:
        p = Path(p)
        print(" ", p.name, f"{p.stat().st_size/1e6:.0f} MB")
    reasons = {}
    for s in m["skipped"]:
        reasons[s["reason"]] = reasons.get(s["reason"], 0) + 1
    print("skip reasons:", reasons)
