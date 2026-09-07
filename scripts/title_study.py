"""Render the word PANTHEON in the engine, as several fonts and materials.

    python scripts/title_study.py --out docs/visual-record/<date>/title

A title that lives inside the world can be judged the same way anything else
in the world is judged: rendered, from a stated camera, in stated light, on a
labelled panel. Row 1 is the same material in four faces; row 2 is the chosen
face in four materials.
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
from scripts.material_study import (BIN, HOME, PK3, STAGE, QL,  # noqa: E402
                                    _label, _look, _panel, _render)

# THE STAGE, found by measurement rather than by opening a map and liking it:
# a sweep of five maps for an enclosed volume big enough for a 734-unit word,
# rejecting the void by requiring a floor below and a ceiling above. theedge
# at this point is 1024 x 1024 clear with 704 units of headroom.
STAGE_MAP = "theedge"
CENTRE = (1280.0, 640.0, 816.0)

EXTERNAL = ROOT / "assets/pantheon_world/external"
FONTS = ["BlackOpsOne-Regular", "RussoOne-Regular", "BebasNeue-Regular",
         "BungeeInline-Regular"]
MATERIALS = [
    ("CC0 Marble012", EXTERNAL / "Marble012.tga"),
    ("CC0 MetalPlates013", EXTERNAL / "MetalPlates013.tga"),
    ("CC0 Metal055A", EXTERNAL / "Metal055A.tga"),
    ("PANTHEON blue glyph", None),          # our own emissive
]
CX = CENTRE[0]
WORD_Y = CENTRE[1] + 300.0
WORD_Z = CENTRE[2] - 120.0


def make_word(font: str, out_models: Path) -> None:
    blender = Path("C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")
    obj = ROOT / ".tmp/title.obj"
    subprocess.run([str(blender), "--background", "--python",
                    str(ROOT / "assets/pantheon_world/build_text_v1.py"), "--",
                    "--font", f"{font}.ttf", # 340 wide: traced against the BSP, all four ends of the word are in
                    # open space and visible from the camera. 560 put the last
                    # letter inside a pillar.
                    "--max-width", "340",
                    "--out", str(obj)],
                   check=True, capture_output=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/obj_to_md3.py"), str(obj),
                    "--out", str(out_models / "models/pantheon/title.md3")],
                   check=True, capture_output=True)


def pack(material, models: Path) -> dict:
    label, src = material
    if src is None:
        mats = [Material("pantheon/title", "textures/base_light/proto_lightblue",
                         kind=EMISSIVE, halo=0.16)]
    else:
        mats = [Material("pantheon/title", "", external=src)]
    if STAGE.exists():
        for p in sorted(STAGE.rglob("*"), reverse=True):
            p.unlink() if p.is_file() else p.rmdir()
    man = build(mats, out_dir=STAGE)
    with zipfile.ZipFile(PK3, "w", zipfile.ZIP_DEFLATED) as z:
        for root in (STAGE, models):
            for p in root.rglob("*"):
                if p.is_file() and p.suffix in (".png", ".tga", ".shader", ".md3"):
                    z.write(p, str(p.relative_to(root)).replace("\\", "/"))
    return man


def shot(path: Path, out_tga: str, back: float = 620.0) -> None:
    cam = (CX, WORD_Y - back, WORD_Z + 40.0)
    pitch, yaw = _look(cam, (CX, WORD_Y, WORD_Z + 40.0))
    lines = ["# title study", f"map {STAGE_MAP}", "size 1920 1080",
             "provenance PANTHEON_TITLE_IN_ENGINE", "lighting CINEMATIC",
             "model models/pantheon/title.md3"]
    for i in range(2):                      # frame 0 warms the back buffer
        lines.append("frame %d 0 %.3f %.3f %.3f %.3f %.3f 0.000 90.00 %s"
                     % (i, cam[0], cam[1], cam[2], pitch, yaw,
                        "warmup.tga" if i == 0 else out_tga))
        lines.append("prop 0 %.3f %.3f %.3f 0 0 0" % (CX, WORD_Y, WORD_Z))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--face", default="BlackOpsOne-Regular",
                    help="the font used for the material row")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    cells, record = [], []

    for i, font in enumerate(FONTS):                    # row 1: the faces
        models = ROOT / f".tmp/title_models_{i}"
        make_word(font, models)
        pack(MATERIALS[0], models)
        shot(BIN / "title.shot", f"title_f{i}.tga")
        _render(BIN / "title.shot")
        png = a.out / f"font_{i}_{font}.png"
        _label(BIN / f"title_f{i}.tga", png, f"{i + 1}  {font.replace('-Regular', '')}")
        cells.append(png)
        record.append({"cell": i + 1, "font": font, "material": MATERIALS[0][0]})
        print(f"  font {font}", flush=True)

    models = ROOT / ".tmp/title_models_face"
    make_word(a.face, models)
    for j, mat in enumerate(MATERIALS):                 # row 2: the materials
        man = pack(mat, models)
        shot(BIN / "title.shot", f"title_m{j}.tga")
        _render(BIN / "title.shot")
        png = a.out / f"mat_{j}_{mat[0].replace(' ', '_')}.png"
        _label(BIN / f"title_m{j}.tga", png, f"{len(FONTS) + j + 1}  {mat[0]}")
        cells.append(png)
        record.append({"cell": len(FONTS) + j + 1, "font": a.face,
                       "material": mat[0], "origin": man["materials"][0]["origin"]})
        print(f"  material {mat[0]}", flush=True)

    panel = _panel(cells, a.out / "panel_title.png", cols=4)
    (a.out / "title_study.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    print("panel:", panel)
    return 0


if __name__ == "__main__":                      # pragma: no cover - CLI
    raise SystemExit(main())
