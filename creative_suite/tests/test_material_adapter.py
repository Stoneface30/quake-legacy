"""The material adapter: reuse Quake's images, never Quake's world shaders."""
from __future__ import annotations

from pathlib import Path

import pytest

from engine.pantheon.material_adapter import (EMISSIVE, Material, build,
                                              resolve, shader_text)

PAK = Path("C:/Program Files (x86)/Steam/steamapps/common/Quake Live/baseq3/pak00.pk3")


def test_no_generated_stage_ever_samples_the_lightmap():
    """The defect this module exists to prevent: a model cannot sample a
    lightmap, so a model shader that names $lightmap is broken by
    construction."""
    ms = [Material("pantheon/a", "textures/x/y"), Material("pantheon/b", "textures/x/z",
                                                           kind=EMISSIVE)]
    for m in ms:
        m.resolved = {"ext": ".png"}
    text = shader_text(ms)
    assert "$lightmap" not in text
    assert "rgbGen lightingDiffuse" in text
    assert "nopicmip" in text                      # a 4x upscale must not be halved


def test_an_emissive_gets_an_unlit_core_and_a_restrained_halo():
    m = Material("pantheon/glyph", "textures/x/y", kind=EMISSIVE, halo=0.10)
    m.resolved = {"ext": ".png"}
    text = shader_text([m])
    assert "rgbGen identity" in text               # a source does not dim with the room
    assert "blendfunc GL_ONE GL_ONE" in text
    assert "rgbGen wave sin 0.10" in text


def test_a_material_that_exists_nowhere_is_refused(tmp_path):
    with pytest.raises(FileNotFoundError):
        resolve(Material("pantheon/nope", "textures/does/not/exist"),
                pak=tmp_path / "missing.pk3", photoreal_root=tmp_path)


def test_the_photoreal_upscale_is_preferred_and_says_so(tmp_path):
    root = tmp_path / "photoreal"
    (root / "textures/x").mkdir(parents=True)
    (root / "textures/x/y.png").write_bytes(b"\x89PNG-not-really")
    m = resolve(Material("pantheon/a", "textures/x/y"), pak=tmp_path / "no.pk3",
                photoreal_root=root)
    assert m.resolved["origin"] == "PHOTOREAL_UPSCALE_4X"
    assert m.resolved["sha256"]


@pytest.mark.skipif(not PAK.exists(), reason="Quake Live not installed here")
def test_a_real_texture_resolves_and_stages(tmp_path):
    man = build([Material("pantheon/door_body", "textures/gothic_block/blocks15_blue")],
                out_dir=tmp_path)
    assert man["count"] == 1
    staged = list((tmp_path / "textures" / "pantheon").glob("door_body.*"))
    assert staged and staged[0].stat().st_size > 1000
    assert (tmp_path / "scripts" / "pantheon_materials.shader").exists()
