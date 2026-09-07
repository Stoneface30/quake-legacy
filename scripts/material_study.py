"""Render one subject against several materials or UV densities, on one panel.

    python scripts/material_study.py textures --out docs/visual-record/<date>/study
    python scripts/material_study.py uv       --out ...

The point is to stop choosing textures by name. Every candidate is rendered
by the real renderer, from the same camera, in the same light, and the panel
is labelled so a human verdict can name a cell instead of describing a
feeling. Nothing here decides anything -- it makes the choice reviewable.

Each cell records what it actually wore (`study.json`): the resolved image,
its origin (photoreal upscale or pak original) and its hash.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.pantheon.material_adapter import EMISSIVE, Material, build  # noqa: E402

BIN = ROOT / "engine/pantheon_renderer/build/bin"
HOME = ROOT / ".tmp/pantheon_home"
PK3 = HOME / "baseq3" / "zzz_pantheon.pk3"
STAGE = ROOT / ".tmp/study_pk3"
MODELS = ROOT / ".tmp/build3"
QL = "C:/Program Files (x86)/Steam/steamapps/common/Quake Live"
FFMPEG = Path("G:/QUAKE_LEGACY/creative_suite/tools/ffmpeg/ffmpeg.exe")
FONT = ROOT / "creative_suite/engine/assets/fonts/BebasNeue-Regular.ttf"

# bloodrun, a real info_player_deathmatch and the door plane in front of it
SPAWN = (-640.0, -848.0, 408.0)
DOOR_Y = SPAWN[1] + 320.0
CX, Z = SPAWN[0], SPAWN[2]

# Cold, temple-appropriate candidates from the 4x upscale corpus.
TEXTURES = [
    "textures/gothic_block/blocks18c",
    "textures/gothic_block/blocks11b",
    "textures/gothic_block/blocks15_blue",
    "textures/gothic_block/blocks17",
    "textures/gothic_floor/largerblock3b3",
    "textures/gothic_wall/iron01_ndark",
    "textures/gothic_wall/church_brick3",
    "textures/gothic_block/blocks18d",
]
UV_DENSITIES = [32.0, 64.0, 128.0, 256.0]      # Quake units per texture tile


def _look(cam, tgt):
    d = [tgt[i] - cam[i] for i in range(3)]
    return (-math.degrees(math.atan2(d[2], math.hypot(d[0], d[1]))),
            math.degrees(math.atan2(d[1], d[0])))


def _shot(path: Path, out_tga: str, w=1280, h=720, models=("door_leaf_v1",
                                                           "door_leaf_v1_mirror")):
    cam = (CX, DOOR_Y - 330.0, Z + 190.0)
    pitch, yaw = _look(cam, (CX, DOOR_Y, Z + 190.0))
    lines = ["# material study", "map bloodrun", f"size {w} {h}",
             "provenance MATERIAL_STUDY", "lighting CINEMATIC"]
    lines += [f"model models/pantheon/{m}.md3" for m in models]
    # frame 0 is a warm-up: the first buffer still carries the loading screen
    for i in range(2):
        lines.append("frame %d 0 %.3f %.3f %.3f %.3f %.3f 0.000 85.00 %s"
                     % (i, cam[0], cam[1], cam[2], pitch, yaw,
                        "warmup.tga" if i == 0 else out_tga))
        lines.append("prop 0 %.3f %.3f %.3f 0 180 0" % (CX + 128, DOOR_Y + 27, Z))
        lines.append("prop 1 %.3f %.3f %.3f 0 180 0" % (CX - 128, DOOR_Y + 27, Z))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pack(materials, models_dir: Path = MODELS) -> dict:
    if STAGE.exists():
        for p in sorted(STAGE.rglob("*"), reverse=True):
            p.unlink() if p.is_file() else p.rmdir()
    man = build(materials, out_dir=STAGE)
    PK3.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(PK3, "w", zipfile.ZIP_DEFLATED) as z:
        for root in (STAGE, models_dir):
            for p in root.rglob("*"):
                if p.is_file() and p.suffix in (".png", ".tga", ".shader", ".md3"):
                    z.write(p, str(p.relative_to(root)).replace("\\", "/"))
    return man


def _render(shot: Path) -> None:
    subprocess.run([str(BIN / "pantheon_frame.exe"), "--shot", shot.name,
                    "--set", "r_picmip", "0", "--set", "r_ext_max_anisotropy", "16",
                    "--basepath", QL, "--game", "baseq3", "--home", str(HOME)],
                   cwd=BIN, check=True, capture_output=True)


def _label(tga: Path, png: Path, text: str) -> None:
    """Scale the frame down and burn the cell's name into it.

    Labelling happens in PIL rather than ffmpeg's drawtext: passing a Windows
    path into a filter graph means escaping a drive colon inside a
    comma-separated option list, and a mislabelled panel is worse than an
    unlabelled one."""
    from PIL import Image, ImageDraw, ImageFont
    subprocess.run([str(FFMPEG), "-v", "error", "-y", "-i", str(tga),
                    "-vf", "scale=640:360:flags=lanczos", str(png)],
                   check=True, capture_output=True)
    im = Image.open(png).convert("RGB")
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype(str(FONT), 26)
    except OSError:                                  # pragma: no cover - fallback
        font = ImageFont.load_default()
    box = d.textbbox((12, 326), text, font=font)
    d.rectangle([box[0] - 6, box[1] - 4, box[2] + 6, box[3] + 4], fill=(0, 0, 0))
    d.text((12, 326), text, fill=(255, 255, 255), font=font)
    im.save(png)


def _panel(cells: list[Path], out: Path, cols: int = 4) -> Path:
    rows = math.ceil(len(cells) / cols)
    args = []
    for c in cells:
        args += ["-i", str(c)]
    fc = "".join(f"[{i}:v]scale=640:360[c{i}];" for i in range(len(cells)))
    for r in range(rows):
        idx = [f"[c{i}]" for i in range(r * cols, min((r + 1) * cols, len(cells)))]
        fc += "".join(idx) + f"hstack={len(idx)}[r{r}];"
    fc += "".join(f"[r{r}]" for r in range(rows)) + f"vstack={rows}"
    subprocess.run([str(FFMPEG), "-v", "error", "-y", *args,
                    "-filter_complex", fc, str(out)], check=True, capture_output=True)
    return out


def study_textures(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    cells, record = [], []
    for i, src in enumerate(TEXTURES):
        mats = [Material("pantheon/door_body", src),
                Material("pantheon/door_metal", "textures/base_wall/bluemetal3b"),
                Material("pantheon/door_relief", src),
                Material("pantheon/glyph", "textures/base_light/proto_lightblue",
                         kind=EMISSIVE, halo=0.14)]
        man = _pack(mats)
        shot = BIN / "study.shot"
        _shot(shot, f"study_{i}.tga")
        _render(shot)
        png = out_dir / f"tex_{i}_{Path(src).name}.png"
        _label(BIN / f"study_{i}.tga", png, f"{i + 1}  {src.replace('textures/', '')}")
        cells.append(png)
        body = man["materials"][0]
        record.append({"cell": i + 1, "source": src, "origin": body["origin"],
                       "sha256": body["sha256"]})
        print(f"  {i + 1}/{len(TEXTURES)}  {src}  {body['origin']}", flush=True)
    panel = _panel(cells, out_dir / "panel_textures.png")
    return {"kind": "textures", "cells": record, "panel": str(panel)}


def study_uv(out_dir: Path, texture: str) -> dict:
    """Rebuild the leaf at several UV densities and render each."""
    out_dir.mkdir(parents=True, exist_ok=True)
    blender = Path("C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")
    gen = ROOT / "assets/pantheon_world/generated"
    cells, record = [], []
    mats = [Material("pantheon/door_body", texture),
            Material("pantheon/door_metal", "textures/base_wall/bluemetal3b"),
            Material("pantheon/door_relief", texture),
            Material("pantheon/glyph", "textures/base_light/proto_lightblue",
                     kind=EMISSIVE, halo=0.14)]
    for i, density in enumerate(UV_DENSITIES):
        subprocess.run([str(blender), "--background", "--python",
                        str(ROOT / "assets/pantheon_world/build_door_v1.py"), "--",
                        "--uv-units", str(density)], check=True, capture_output=True)
        models = ROOT / f".tmp/study_models_{i}"
        for mirror, name in ((False, "door_leaf_v1"), (True, "door_leaf_v1_mirror")):
            cmd = [sys.executable, str(ROOT / "scripts/obj_to_md3.py"),
                   str(gen / "pantheon_door_leaf_v1.obj"),
                   "--out", str(models / f"models/pantheon/{name}.md3")]
            if mirror:
                cmd.append("--mirror-x")
            subprocess.run(cmd, check=True, capture_output=True)
        _pack(mats, models_dir=models)
        shot = BIN / "study.shot"
        _shot(shot, f"uv_{i}.tga")
        _render(shot)
        png = out_dir / f"uv_{i}_{int(density)}.png"
        _label(BIN / f"uv_{i}.tga", png, f"{i + 1}  1 tile = {int(density)} units")
        cells.append(png)
        record.append({"cell": i + 1, "units_per_tile": density})
        print(f"  UV {int(density)} units/tile", flush=True)
    panel = _panel(cells, out_dir / "panel_uv.png", cols=2)
    return {"kind": "uv", "texture": texture, "cells": record, "panel": str(panel)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("what", choices=["textures", "uv", "both"])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--uv-texture", default="textures/gothic_block/blocks18c")
    a = ap.parse_args()
    results = []
    if a.what in ("textures", "both"):
        results.append(study_textures(a.out))
    if a.what in ("uv", "both"):
        results.append(study_uv(a.out, a.uv_texture))
    (a.out / "study.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    for r in results:
        print("panel:", r["panel"])
    return 0


if __name__ == "__main__":                      # pragma: no cover - CLI
    raise SystemExit(main())
