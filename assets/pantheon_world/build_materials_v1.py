"""The PANTHEON material set — authored, not borrowed.

    python assets/pantheon_world/build_materials_v1.py --out <dir>

Why this exists: the first door proof textured itself with Quake Live's own
WORLD textures, and the frames came back translucent and neon. The cause is
structural, not aesthetic. `textures/base_light/proto_lightblue` and its
neighbours are *world* shaders whose first stage is `map $lightmap` -- brush
surfaces carry lightmap coordinates and models do not, so a model wearing a
world shader is lit by a lightmap it does not have. Choosing a different QL
texture by name would have produced a different wrong answer.

So PANTHEON authors its own four materials and its own shader script, with
model-appropriate stages (`rgbGen lightingDiffuse`, exactly like every weapon
and player shader in the game):

    pantheon/basalt        cold basalt -- the door's body
    pantheon/metal_deep    dark blue-black metal -- frame and stiles
    pantheon/carved        recessed carved stone -- panel relief
    pantheon/glyph         blue energy -- the PANTHEON mark, narrow core with
                           a restrained additive halo, unlit by design

Every texture is generated here, tileable by construction (the value noise
wraps), so the set is reproducible and diffable rather than a folder of
binaries somebody once made. Colours come from the engine's own table:
Quake Live's ^4 is #3266FE and ^7 is #FEFEFE (`g_color_table_ql`).

This is the CLASSIC-renderer interpretation: one baked diffuse per material.
Normal / roughness / AO belong to a later pass and a renderer that can use
them; nothing here pretends the current fixed-function pipeline reads them.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image

SIZE = 256
PANTHEON_BLUE = np.array([0x32, 0x66, 0xFE], dtype=float)     # ^4
PANTHEON_WHITE = np.array([0xFE, 0xFE, 0xFE], dtype=float)    # ^7


def _wrapped_noise(size: int, period: int, seed: int) -> np.ndarray:
    """Value noise that tiles: the lattice wraps, so the last column is the
    neighbour of the first. A texture that does not tile shows a seam on
    every column of a colonnade."""
    rng = np.random.default_rng(seed)
    lat = rng.random((period, period))
    ys = np.linspace(0, period, size, endpoint=False)
    xs = np.linspace(0, period, size, endpoint=False)
    y0 = np.floor(ys).astype(int) % period
    x0 = np.floor(xs).astype(int) % period
    fy = (ys - np.floor(ys))[:, None]
    fx = (xs - np.floor(xs))[None, :]
    fy = fy * fy * (3 - 2 * fy)                       # smoothstep
    fx = fx * fx * (3 - 2 * fx)
    y1, x1 = (y0 + 1) % period, (x0 + 1) % period
    a = lat[np.ix_(y0, x0)]
    b = lat[np.ix_(y0, x1)]
    c = lat[np.ix_(y1, x0)]
    d = lat[np.ix_(y1, x1)]
    return (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy)
            + c * (1 - fx) * fy + d * fx * fy)


def _fbm(size: int, seed: int, octaves: int = 5, period: int = 4) -> np.ndarray:
    total = np.zeros((size, size))
    amp, p, norm = 1.0, period, 0.0
    for o in range(octaves):
        total += amp * _wrapped_noise(size, p, seed + o)
        norm += amp
        amp *= 0.5
        p *= 2
    return total / norm


def _shade(height: np.ndarray, strength: float = 2.0) -> np.ndarray:
    """A cheap directional cavity term from a height field, wrapped.

    The classic renderer has no normal map, so relief has to live in the
    diffuse. This is the 'baked cavity' interpretation, and it is why the
    stone reads as stone at 1024 units instead of as grey paint."""
    gx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    gy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
    lit = 0.5 + strength * (0.7 * -gx + 0.7 * -gy)
    return np.clip(lit, 0.35, 1.35)


def _grout(size: int, bw: int, bh: int, width: float = 1.5) -> np.ndarray:
    """Block courses with a half-block offset per row -- masonry, not tiles."""
    yy, xx = np.mgrid[0:size, 0:size]
    row = yy // bh
    off = (row % 2) * (bw // 2)
    inx = (xx + off) % bw
    iny = yy % bh
    edge = np.minimum(np.minimum(inx, bw - 1 - inx), np.minimum(iny, bh - 1 - iny))
    return np.clip(edge / width, 0.0, 1.0)


def _save(path: Path, rgb: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").save(path)
    return path


def basalt(size: int = SIZE) -> np.ndarray:
    grain = _fbm(size, seed=11, octaves=6, period=8)
    blocks = _grout(size, bw=size // 2, bh=size // 4, width=2.0)
    height = 0.75 * blocks + 0.25 * grain
    base = np.array([54, 60, 72], dtype=float)            # cold basalt
    warm = np.array([78, 84, 96], dtype=float)
    col = base[None, None, :] + (warm - base)[None, None, :] * grain[..., None]
    return col * _shade(height, 2.4)[..., None]


def metal_deep(size: int = SIZE) -> np.ndarray:
    brushed = _fbm(size, seed=23, octaves=5, period=2)
    streak = _wrapped_noise(size, 64, 31)
    height = 0.3 * brushed + 0.7 * streak
    base = np.array([18, 22, 34], dtype=float)            # blue-black
    hi = PANTHEON_BLUE * 0.32 + 24
    col = base[None, None, :] + (hi - base)[None, None, :] * (streak ** 2)[..., None]
    return col * _shade(height, 1.6)[..., None]


def carved(size: int = SIZE) -> np.ndarray:
    grain = _fbm(size, seed=37, octaves=6, period=6)
    yy, xx = np.mgrid[0:size, 0:size]
    flutes = 0.5 + 0.5 * np.cos(xx / size * 2 * math.pi * 4)   # 4 wrapped flutes
    height = 0.6 * flutes + 0.4 * grain
    base = np.array([62, 66, 74], dtype=float)
    col = base[None, None, :] * (0.75 + 0.5 * grain)[..., None]
    return col * _shade(height, 3.0)[..., None]


def glyph_core(size: int = SIZE) -> np.ndarray:
    """The energy surface itself: a narrow bright core, blue everywhere else.
    Deliberately NOT white across the whole face -- broad white strips were
    what made v1 read as neon tube instead of carved light."""
    yy, xx = np.mgrid[0:size, 0:size]
    v = np.abs((xx / (size - 1)) - 0.5) * 2.0             # 0 at the centre line
    core = np.exp(-(v ** 2) / (2 * 0.10 ** 2))            # narrow
    body = np.exp(-(v ** 2) / (2 * 0.55 ** 2))
    flicker = 0.92 + 0.08 * _fbm(size, seed=5, octaves=4, period=8)
    col = (PANTHEON_BLUE[None, None, :] * (0.45 + 0.55 * body)[..., None]
           + (PANTHEON_WHITE - PANTHEON_BLUE)[None, None, :] * (core ** 2)[..., None])
    return col * flicker[..., None]


def glyph_halo(size: int = SIZE) -> np.ndarray:
    """The additive stage. Restrained on purpose: additive light that reaches
    the frame edges is what turns a glyph into a lamp."""
    yy, xx = np.mgrid[0:size, 0:size]
    v = np.abs((xx / (size - 1)) - 0.5) * 2.0
    halo = np.exp(-(v ** 2) / (2 * 0.30 ** 2)) * 0.42
    return PANTHEON_BLUE[None, None, :] * halo[..., None]


SHADER = """// PANTHEON material set v1 -- authored for MODELS.
//
// Every stage below is a model stage. NOT ONE of them uses $lightmap: a
// model carries no lightmap coordinates, and a world shader worn by a model
// is the defect this set was written to fix.
//
// Colours: Quake Live ^4 = #3266FE, ^7 = #FEFEFE (g_color_table_ql).

textures/pantheon/basalt
{
	{
		map textures/pantheon/basalt.tga
		rgbGen lightingDiffuse
	}
}

textures/pantheon/metal_deep
{
	{
		map textures/pantheon/metal_deep.tga
		rgbGen lightingDiffuse
	}
}

textures/pantheon/carved
{
	{
		map textures/pantheon/carved.tga
		rgbGen lightingDiffuse
	}
}

// The mark's energy. Unlit by design -- it is a source, not a surface, so it
// must not dim when the room does. The halo is a separate, restrained
// additive stage so the core stays readable in a lit room and the glow never
// washes the stone beside it.
textures/pantheon/glyph
{
	nopicmip
	{
		map textures/pantheon/glyph.tga
		rgbGen identity
	}
	{
		map textures/pantheon/glyph_halo.tga
		blendfunc GL_ONE GL_ONE
		rgbGen wave sin 0.72 0.10 0 0.13
	}
}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path,
                    default=Path("assets/pantheon_world/generated/pk3"))
    ap.add_argument("--size", type=int, default=SIZE)
    a = ap.parse_args()
    tex = a.out / "textures" / "pantheon"
    made = [
        _save(tex / "basalt.tga", basalt(a.size)),
        _save(tex / "metal_deep.tga", metal_deep(a.size)),
        _save(tex / "carved.tga", carved(a.size)),
        _save(tex / "glyph.tga", glyph_core(a.size)),
        _save(tex / "glyph_halo.tga", glyph_halo(a.size)),
    ]
    shader = a.out / "scripts" / "pantheon.shader"
    shader.parent.mkdir(parents=True, exist_ok=True)
    shader.write_text(SHADER, encoding="utf-8")
    for p in made + [shader]:
        print(f"  {p}  {p.stat().st_size} bytes")
    return 0


if __name__ == "__main__":                      # pragma: no cover - CLI
    raise SystemExit(main())
