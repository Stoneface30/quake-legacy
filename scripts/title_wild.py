"""Eight WILDLY different treatments of the same word, in the engine.

    python scripts/title_wild.py --out docs/visual-record/<date>/wild

The material panel came back "they all look the same", and it was right: four
faces and four stones at the same distance in the same light is one shot eight
times. A treatment is not a texture -- it is shader behaviour, camera, scale
and light together. So each cell here changes all four.

Every effect used is a real Quake shader feature, verified present in this
renderer's own `tr_shader.c`: `tcGen environment`, `deformVertexes wave/bulge`,
`tcMod scroll/turb/rotate`, `blendfunc GL_ONE GL_ONE`, `sort`, `cull`,
`alphaGen`. Nothing here is post-production -- if it is in the frame, the game
drew it.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.pantheon.material_adapter import Material, resolve  # noqa: E402
from scripts.material_study import BIN, PK3, QL, _label, _look, _panel, _render  # noqa: E402

EXTERNAL = ROOT / "assets/pantheon_world/external"
STAGE = ROOT / ".tmp/wild_pk3"
HALL = ("theedge", (1280.0, 940.0, 696.0))          # traced: 1024x1024, 704 head


@dataclass
class Treatment:
    """One cell: its own shader, camera, scale and word."""

    name: str
    shader: str                       # the full shader body for textures/pantheon/title
    images: dict                      # local name -> pak/photoreal source or file
    font: str = "BlackOpsOne-Regular"
    width: float = 340.0              # traced clearance in the hall
    cam: tuple = (0.0, -620.0, 40.0)  # offset from the word's origin
    fov: float = 90.0
    roll: float = 0.0
    lighting: str = "CINEMATIC"
    note: str = ""
    resolved: list = field(default_factory=list)


def T(name, shader, images, **kw):
    return Treatment(name=name, shader=shader, images=images, **kw)


# ── the eight ─────────────────────────────────────────────────────────────
TREATMENTS = [
    T("1 CHROME", """	nopicmip
	{
		map textures/pantheon/env.tga
		tcGen environment
		rgbGen identity
	}""", {"env": "textures/base_wall/bluemetal3b"},
      note="tcGen environment: the room reflected off the letters"),

    T("2 MOLTEN", """	nopicmip
	cull disable
	deformVertexes wave 64 sin 0 1.5 0 0.6
	{
		map textures/pantheon/stone.tga
		rgbGen lightingDiffuse
	}
	{
		map textures/pantheon/fire.tga
		blendfunc GL_ONE GL_ONE
		tcMod scroll 0 -1.4
		tcMod turb 0 0.22 0 0.9
		rgbGen identity
	}""", {"stone": EXTERNAL / "Marble012.tga", "fire": "textures/sfx/b_flame4"},
      note="the letters ripple and burn: deformVertexes wave + scrolling additive fire"),

    T("3 VOID GLOW", """	nopicmip
	{
		map textures/pantheon/glow.tga
		rgbGen identity
	}
	{
		map textures/pantheon/glow.tga
		blendfunc GL_ONE GL_ONE
		tcMod scale 3 3
		tcMod scroll 0.05 0
		rgbGen identity
	}""", {"glow": "textures/base_light/proto_lightblue"},
      lighting="QUAKE_AUTHENTIC", cam=(0.0, -520.0, 10.0), fov=70.0,
      note="unlit blue in the darkest render profile: a source, not a surface"),

    T("4 MACRO", """	nopicmip
	{
		map textures/pantheon/stone.tga
		rgbGen lightingDiffuse
	}""", {"stone": EXTERNAL / "Travertine009.tga"},
      width=340.0, cam=(-120.0, -110.0, 25.0), fov=60.0,
      note="110 units from the P: the bevel, the depth and the grain"),

    T("5 TOWER", """	nopicmip
	{
		map textures/pantheon/stone.tga
		rgbGen lightingDiffuse
	}
	{
		map textures/pantheon/env.tga
		blendfunc GL_DST_COLOR GL_ONE
		tcGen environment
		rgbGen identity
	}""", {"stone": "textures/gothic_block/blocks18c",
             "env": "textures/base_wall/bluemetal3b"},
      cam=(0.0, -300.0, -95.0), fov=100.0, roll=8.0,
      note="floor level looking up, tilted: stone with an environment sheen"),

    T("6 HOLOGRAM", """	nopicmip
	cull disable
	sort additive
	{
		map textures/pantheon/glow.tga
		blendfunc GL_ONE GL_ONE
		tcMod scale 1 8
		tcMod scroll 0 -0.7
		rgbGen identity
	}
	{
		map textures/pantheon/beam.tga
		blendfunc GL_ONE GL_ONE
		tcMod rotate 12
		rgbGen identity
	}""", {"glow": "textures/base_light/proto_lightblue",
             "beam": "textures/sfx/beam_blue4"},
      font="BebasNeue-Regular",
      note="additive only, scanlines scrolling, no depth write: it is projected"),

    T("7 GOLD LEAF", """	nopicmip
	{
		map textures/pantheon/gold.tga
		rgbGen lightingDiffuse
	}
	{
		map textures/pantheon/env.tga
		blendfunc GL_DST_COLOR GL_SRC_COLOR
		tcGen environment
		rgbGen identity
	}""", {"gold": "textures/gothic_trim/goldsupport_a",
             "env": "textures/base_wall/bluemetal3b"},
      font="RussoOne-Regular", cam=(60.0, -420.0, 60.0), fov=80.0, roll=-4.0,
      note="warm metal with a doubled environment pass: heavier, older"),

    T("8 SHATTER", """	nopicmip
	cull disable
	deformVertexes bulge 12 6 2.5
	{
		map textures/pantheon/stone.tga
		rgbGen lightingDiffuse
	}
	{
		map textures/pantheon/glow.tga
		blendfunc GL_ONE GL_ONE
		tcMod turb 0 0.6 0 1.6
		rgbGen identity
	}""", {"stone": EXTERNAL / "MetalPlates013.tga",
             "glow": "textures/base_light/proto_lightblue"},
      font="BungeeInline-Regular", cam=(0.0, -560.0, 60.0), fov=85.0,
      note="deformVertexes bulge: the word is coming apart, energy through it"),
]


# geometry variants: what the LETTER is, before any shader touches it
# MEASURED, not guessed: a bevel of 0.04-0.05 em swallows the letterforms --
# the counters of P, A and O fill in and PANTHEON becomes a slab. The radius
# has to stay under ~0.015 em; DEPTH is what makes it an object, and
# bevel_resolution is what makes the edge roll a highlight.
GEOMETRY = [
    ("A flat 18u", ["--bevel", "0.004", "--bevel-res", "0", "--depth", "18"]),
    ("B round 28u", ["--bevel", "0.008", "--bevel-res", "4", "--depth", "28"]),
    ("C round 44u", ["--bevel", "0.012", "--bevel-res", "4", "--depth", "44"]),
    ("D round 28u + 28deg arc", ["--bevel", "0.008", "--bevel-res", "4",
                                 "--depth", "28", "--arc", "28"]),
]


def make_word(font: str, width: float, models: Path, geom: list | None = None) -> None:
    blender = Path("C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")
    obj = ROOT / ".tmp/wild.obj"
    subprocess.run([str(blender), "--background", "--python",
                    str(ROOT / "assets/pantheon_world/build_text_v1.py"), "--",
                    "--font", f"{font}.ttf", "--max-width", str(width),
                    *(geom or ["--depth", "26"]), "--out", str(obj)],
                   check=True, capture_output=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/obj_to_md3.py"), str(obj),
                    "--out", str(models / "models/pantheon/title.md3")],
                   check=True, capture_output=True)


def pack(t: Treatment, models: Path) -> None:
    if STAGE.exists():
        for p in sorted(STAGE.rglob("*"), reverse=True):
            p.unlink() if p.is_file() else p.rmdir()
    (STAGE / "textures/pantheon").mkdir(parents=True, exist_ok=True)
    for local, src in t.images.items():
        m = Material(f"pantheon/{local}", "" if isinstance(src, Path) else src,
                     external=src if isinstance(src, Path) else None)
        resolve(m)
        data = (Path(m.resolved["path"]).read_bytes()
                if m.resolved["origin"] != "PAK00_ORIGINAL"
                else zipfile.ZipFile(
                    "C:/Program Files (x86)/Steam/steamapps/common/Quake Live/"
                    "baseq3/pak00.pk3").read(m.source + m.resolved["ext"]))
        # one extension for every image so the shader text can be literal
        (STAGE / f"textures/pantheon/{local}.tga").write_bytes(
            _as_tga(data, m.resolved["ext"]))
        t.resolved.append({"local": local, "source": str(src),
                           "origin": m.resolved["origin"], "sha256": m.resolved["sha256"]})
    (STAGE / "scripts").mkdir(parents=True, exist_ok=True)
    (STAGE / "scripts/pantheon_wild.shader").write_text(
        "// generated by scripts/title_wild.py\n"
        "textures/pantheon/title\n{\n" + t.shader + "\n}\n", encoding="utf-8")
    with zipfile.ZipFile(PK3, "w", zipfile.ZIP_DEFLATED) as z:
        for root in (STAGE, models):
            for p in root.rglob("*"):
                if p.is_file() and p.suffix in (".tga", ".shader", ".md3"):
                    z.write(p, str(p.relative_to(root)).replace("\\", "/"))


def _as_tga(data: bytes, ext: str) -> bytes:
    """Everything reaches the engine as 24-bit TGA. PNG and JPEG both loaded
    as white at some point; one format, converted here, removes the class."""
    if ext == ".tga":
        return data
    import io

    from PIL import Image
    buf = io.BytesIO()
    Image.open(io.BytesIO(data)).convert("RGB").save(buf, format="TGA")
    return buf.getvalue()


def shot(path: Path, t: Treatment, out_tga: str) -> None:
    mapname, centre = HALL
    wx, wy, wz = centre[0], centre[1], centre[2] - 120.0
    cam = (wx + t.cam[0], wy + t.cam[1], wz + t.cam[2])
    pitch, yaw = _look(cam, (wx, wy, wz + 40.0))
    lines = ["# wild title study", f"map {mapname}", "size 1280 720",
             "provenance PANTHEON_TITLE_TREATMENT", f"lighting {t.lighting}",
             "model models/pantheon/title.md3"]
    for i in range(2):
        lines.append("frame %d 0 %.3f %.3f %.3f %.3f %.3f %.3f %.2f %s"
                     % (i, cam[0], cam[1], cam[2], pitch, yaw, t.roll, t.fov,
                        "warmup.tga" if i == 0 else out_tga))
        lines.append("prop 0 %.3f %.3f %.3f 0 0 0" % (wx, wy, wz))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def study_geometry(out_dir: Path) -> list:
    """The same two treatments over four letterforms. The question is not
    which texture -- it is whether the letter has an edge worth lighting."""
    cells, record = [], []
    chosen = [t for t in TREATMENTS if t.name.startswith(("7", "3"))]
    for t in chosen:
        t.cam, t.fov, t.roll = (0.0, -430.0, 50.0), 75.0, 0.0
        for gi, (glabel, gargs) in enumerate(GEOMETRY):
            models = ROOT / f".tmp/geom_{t.name[0]}_{gi}"
            make_word(t.font, t.width, models, gargs)
            pack(t, models)
            tag = f"g{t.name[0]}{gi}"
            shot(BIN / "wild.shot", t, f"{tag}.tga")
            _render(BIN / "wild.shot")
            png = out_dir / f"{tag}.png"
            _label(BIN / f"{tag}.tga", png, f"{t.name.split()[1]}  {glabel}")
            cells.append(png)
            record.append({"treatment": t.name, "geometry": glabel, "args": gargs})
            print(f"  {t.name} / {glabel}", flush=True)
    return cells, record


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--geometry", action="store_true",
                    help="sweep letterform depth/bevel/arc instead of treatments")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if a.geometry:
        cells, record = study_geometry(a.out)
        panel = _panel(cells, a.out / "panel_geometry.png", cols=4)
        (a.out / "geometry.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
        print("panel:", panel)
        return 0
    cells, record = [], []
    for i, t in enumerate(TREATMENTS):
        models = ROOT / f".tmp/wild_models_{i}"
        make_word(t.font, t.width, models)
        pack(t, models)
        shot(BIN / "wild.shot", t, f"wild_{i}.tga")
        _render(BIN / "wild.shot")
        png = a.out / f"wild_{i}.png"
        _label(BIN / f"wild_{i}.tga", png, t.name)
        cells.append(png)
        record.append({"cell": t.name, "font": t.font, "fov": t.fov,
                       "lighting": t.lighting, "note": t.note,
                       "images": t.resolved})
        print(f"  {t.name}  {t.note}", flush=True)
    panel = _panel(cells, a.out / "panel_wild.png", cols=4)
    (a.out / "wild.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    print("panel:", panel)
    return 0


if __name__ == "__main__":                      # pragma: no cover - CLI
    raise SystemExit(main())
