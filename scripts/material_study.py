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

# THE STAGE. Not a corridor in somebody else's level: qzpractice1 is a
# 4864 x 5184 x 3072 practice hall, and the door stands 300 units in front of
# a real spawn with 736 units of verified headroom -- checked with
# camera_paths.bsp_tracer, because "the roof goes through the door" is a
# staging fault, not a look.
# qzpractice1 crashes this host during R_Init -- the only map of five probed
# that does, and a separate investigation. qzpractice2 is the same practice
# hall shape and loads.
STAGE_MAP = "qzpractice2"
SPAWN = (-960.0, -344.0, 8.0)
FLOOR = SPAWN[2] - 24.0                        # playerMins.z
DOOR_Y = SPAWN[1] + 300.0
CX, Z = SPAWN[0], FLOOR

# Cold, temple-appropriate candidates from the 4x upscale corpus.
EXTERNAL = ROOT / "assets/pantheon_world/external"

# Photo-sourced CC0 materials (ambientCG) alongside the two Quake families
# worth keeping. A tuple is (label, source-or-file).
TEXTURES = [
    # Quake's DOOR families -- textures drawn to be a door, at a door's
    # proportions. q3map2's QuakeTextureVecs uses scale 1 by default and
    # normalises st by shaderWidth/shaderHeight, so a Quake texture is
    # authored at 1 texel = 1 unit: a 128-wide WALL texture on a 384-tall leaf
    # repeats three times down it, which is the pattern the director saw.
    ("QL gothic_door/door02_j", "textures/gothic_door/door02_j"),
    ("QL gothic_door/ornate5", "textures/gothic_door/door02_i_ornate5_fin"),
    ("QL gothic_door/arch_tall2_blue", "textures/gothic_door/arch_tall2_blue"),
    ("QL base_door/talldoormetal", "textures/base_door/kcdm18talldoormetal_combined"),
    ("QL base_door/shinymetaldoor", "textures/base_door/shinymetaldoor_outside3a2"),
    # photo-sourced CC0 (ambientCG), one tile across the whole leaf
    ("CC0 Marble012", EXTERNAL / "Marble012.tga"),
    ("CC0 Travertine009", EXTERNAL / "Travertine009.tga"),
    ("CC0 MetalPlates013", EXTERNAL / "MetalPlates013.tga"),
]
UV_DENSITIES = [32.0, 64.0, 128.0, 256.0]      # Quake units per texture tile


def _look(cam, tgt):
    d = [tgt[i] - cam[i] for i in range(3)]
    return (-math.degrees(math.atan2(d[2], math.hypot(d[0], d[1]))),
            math.degrees(math.atan2(d[1], d[0])))


def _shot(path: Path, out_tga: str, w=1280, h=720, models=("door_leaf_v1",
                                                           "door_leaf_v1_mirror")):
    # the camera stands ON the spawn: 300 units out, all nine corners of the
    # door visible, verified with the tracer rather than hoped for
    # 360 units out, all nine door corners visible (tracer-checked), 90 fov:
    # the whole leaf pair in frame with air around it
    cam = (CX, SPAWN[1] - 60.0, Z + 150.0)
    pitch, yaw = _look(cam, (CX, DOOR_Y, Z + 190.0))
    lines = ["# material study", f"map {STAGE_MAP}", f"size {w} {h}",
             "provenance MATERIAL_STUDY", "lighting CINEMATIC"]
    lines += [f"model models/pantheon/{m}.md3" for m in models]
    # frame 0 is a warm-up: the first buffer still carries the loading screen
    for i in range(2):
        lines.append("frame %d 0 %.3f %.3f %.3f %.3f %.3f 0.000 90.00 %s"
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


def build_leaf(uv_units: float, models: Path) -> None:
    """Rebuild the leaf and its mirror from source at a stated UV density.

    The study does this itself because it must: a stale .md3 left in the
    staging directory silently textured six studies in a row at 64 units per
    tile while the .obj beside it said 384, and the panel showed a repeat
    that no material choice could have fixed."""
    blender = Path("C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")
    obj = ROOT / "assets/pantheon_world/generated/pantheon_door_leaf_v1.obj"
    subprocess.run([str(blender), "--background", "--python",
                    str(ROOT / "assets/pantheon_world/build_door_v1.py"), "--",
                    "--uv-units", str(uv_units)], check=True, capture_output=True)
    for mirror, name in ((False, "door_leaf_v1"), (True, "door_leaf_v1_mirror")):
        cmd = [sys.executable, str(ROOT / "scripts/obj_to_md3.py"), str(obj),
               "--out", str(models / f"models/pantheon/{name}.md3")]
        if mirror:
            cmd.append("--mirror-x")
        subprocess.run(cmd, check=True, capture_output=True)
    from engine.pantheon.md3_writer import read_md3
    m = read_md3(models / "models/pantheon/door_leaf_v1.md3")
    vs = [v for s in m["surfaces"] for _, v in s["uvs"]]
    span = max(vs) - min(vs)
    print(f"  leaf rebuilt at {uv_units:.0f} units/tile -- v spans {span:.2f} tiles",
          flush=True)


def study_textures(out_dir: Path, uv_units: float = 384.0) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    build_leaf(uv_units, MODELS)
    cells, record = [], []
    for i, (label, src) in enumerate(TEXTURES):
        ext = src if isinstance(src, Path) else None
        name = "" if ext else src
        mats = [Material("pantheon/door_body", name, external=ext),
                Material("pantheon/door_metal", "textures/base_wall/bluemetal3b"),
                Material("pantheon/door_relief", name, external=ext),
                Material("pantheon/glyph", "textures/base_light/proto_lightblue",
                         kind=EMISSIVE, halo=0.14)]
        man = _pack(mats)
        shot = BIN / "study.shot"
        _shot(shot, f"study_{i}.tga")
        _render(shot)
        png = out_dir / f"tex_{i}_{Path(str(src)).stem}.png"
        _label(BIN / f"study_{i}.tga", png, f"{i + 1}  {label}")
        cells.append(png)
        body = man["materials"][0]
        record.append({"cell": i + 1, "label": label, "source": str(src),
                       "origin": body["origin"], "sha256": body["sha256"]})
        print(f"  {i + 1}/{len(TEXTURES)}  {label}  {body['origin']}", flush=True)
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
    ap.add_argument("--uv-units", type=float, default=384.0)
    a = ap.parse_args()
    results = []
    if a.what in ("textures", "both"):
        results.append(study_textures(a.out, a.uv_units))
    if a.what in ("uv", "both"):
        results.append(study_uv(a.out, a.uv_texture))
    (a.out / "study.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    for r in results:
        print("panel:", r["panel"])
    return 0


if __name__ == "__main__":                      # pragma: no cover - CLI
    raise SystemExit(main())
