"""MD3 writer/reader tests.

The strongest oracle for a model format is the game's own files: if our
reader can parse a real Quake Live player model and agree with what cgame
expects of it, the reader understands the real format, and a round trip
through our writer then means something.
"""
from __future__ import annotations

import math
import zipfile
from pathlib import Path

import pytest

from engine.pantheon.md3_writer import (MD3_IDENT, MD3_VERSION, Surface,
                                        decode_normal, encode_normal, read_md3,
                                        read_obj, write_md3)

PAK = Path("C:/Program Files (x86)/Steam/steamapps/common/Quake Live/baseq3/pak00.pk3")


def _quad(z: float = 0.0, shader: str = "textures/pantheon/stone") -> Surface:
    return Surface(name="quad", shader=shader,
                   verts=[(0, 0, z), (64, 0, z), (64, 128, z), (0, 128, z)],
                   normals=[(0, 0, 1)] * 4,
                   uvs=[(0, 0), (1, 0), (1, 1), (0, 1)],
                   tris=[(0, 1, 2), (0, 2, 3)])


def test_normal_encoding_matches_the_renderers_decode():
    """tr_surface.c: lat is the high byte and is atan2(y,x); lng is the low
    byte and is acos(z). Swapping them still round-trips through OUR pair of
    functions, so the test has to check the packing itself."""
    for n in [(0, 0, 1), (0, 0, -1), (1, 0, 0), (0, 1, 0), (-1, 0, 0),
              (0.577, 0.577, 0.577), (0.6, -0.8, 0)]:
        packed = encode_normal(n)
        lat = (packed >> 8) & 0xFF
        lng = packed & 0xFF
        assert lat == round(math.atan2(n[1], n[0]) * 255 / (2 * math.pi)) & 0xFF
        assert lng == round(math.acos(max(-1, min(1, n[2]))) * 255 / (2 * math.pi)) & 0xFF
        back = decode_normal(packed)
        assert math.dist(back, n) < 0.03           # 8-bit lat/long quantisation


def test_write_then_read_preserves_the_geometry(tmp_path):
    s = _quad()
    p = write_md3(tmp_path / "quad.md3", [s], name="quad")
    m = read_md3(p)
    assert m["num_frames"] == 1 and len(m["surfaces"]) == 1
    got = m["surfaces"][0]
    assert got["shader"] == "textures/pantheon/stone"
    assert got["tris"] == s.tris
    for a, b in zip(got["verts"], s.verts):
        assert math.dist(a, b) <= 1.0 / 64          # MD3_XYZ_SCALE quantisation
    for a, b in zip(got["uvs"], s.uvs):
        assert a == pytest.approx(b)


def test_frame_bounds_cover_every_surface(tmp_path):
    p = write_md3(tmp_path / "two.md3", [_quad(0.0), _quad(200.0, "textures/x/y")])
    f = read_md3(p)["frames"][0]
    assert f["mins"][2] == pytest.approx(0.0)
    assert f["maxs"][2] == pytest.approx(200.0)
    assert f["radius"] >= 200.0


def test_a_surface_with_mismatched_arrays_is_refused():
    s = _quad()
    s.normals = s.normals[:2]
    with pytest.raises(ValueError):
        write_md3("unused.md3", [s])


def test_a_triangle_index_out_of_range_is_refused():
    s = _quad()
    s.tris = [(0, 1, 9)]
    with pytest.raises(ValueError):
        write_md3("unused.md3", [s])


def test_obj_import_splits_by_material_and_flips_v(tmp_path):
    obj = tmp_path / "t.obj"
    obj.write_text(
        "v 0 0 0\nv 1 0 0\nv 1 1 0\n"
        "vt 0 0\nvt 1 0\nvt 1 1\n"
        "vn 0 0 1\n"
        "usemtl textures/pantheon/stone\nf 1/1/1 2/2/1 3/3/1\n"
        "usemtl textures/pantheon/glyph\nf 1/1/1 3/3/1 2/2/1\n", encoding="utf-8")
    surfaces = read_obj(obj)
    assert {s.shader for s in surfaces} == {"textures/pantheon/stone",
                                            "textures/pantheon/glyph"}
    assert all(len(s.tris) == 1 for s in surfaces)
    assert surfaces[0].uvs[0] == (0.0, 1.0)          # OBJ v is bottom-up


@pytest.mark.skipif(not PAK.exists(), reason="Quake Live not installed here")
def test_our_reader_parses_a_real_quake_live_model():
    """crash/upper.md3 is a real three-part player torso: it must have the
    tags cgame hangs the head and weapon from, and a sane vertex count."""
    with zipfile.ZipFile(PAK) as z:
        data = z.read("models/players/crash/upper.md3")
    m = read_md3(data)
    assert m["num_frames"] > 100                     # the animation frame table
    tags = {t["name"] for t in m["tags"]}
    assert {"tag_head", "tag_weapon"} <= tags
    assert m["surfaces"] and all(s["verts"] and s["tris"] for s in m["surfaces"])
    assert m["size"] == len(data)                    # our offsets match the file


@pytest.mark.skipif(not PAK.exists(), reason="Quake Live not installed here")
def test_a_player_models_shader_names_are_empty_because_the_skin_supplies_them():
    """Measured, not assumed: every surface of crash/upper.md3 carries an
    EMPTY shader name. Player materials come from `<part>_<skin>.skin`, which
    maps surface name -> shader, and cgame registers that instead. A PANTHEON
    prop has no .skin, so its MD3 must carry a real shader path itself --
    which is why write_md3 takes one per surface and refuses nothing else."""
    with zipfile.ZipFile(PAK) as z:
        m = read_md3(z.read("models/players/crash/upper.md3"))
    assert all(s["shader"] == "" for s in m["surfaces"])
    assert all(s["name"] for s in m["surfaces"])      # the .skin keys off these


def test_a_normal_whose_latitude_exceeds_127_still_writes(tmp_path):
    """qfiles.h calls the packed normal a `short`, but lat >= 128 puts the
    value past 32767. Writing it signed raises struct.error and takes the
    whole model with it -- which is how this was found, on the first real
    asset with faces pointing at -Y."""
    s = _quad()
    s.normals = [(0, -1, 0)] * 4                 # lat = 192
    assert encode_normal((0, -1, 0)) > 32767
    m = read_md3(write_md3(tmp_path / "n.md3", [s]))
    for got in m["surfaces"][0]["normals"]:
        assert math.dist(got, (0, -1, 0)) < 0.03


def test_a_surface_over_the_vertex_cap_is_split_not_refused():
    """PANTHEON set in Bungee Inline is 19,280 vertices. MD3 allows 4,096 per
    surface, so a hero title either splits or cannot be a model."""
    from engine.pantheon.md3_writer import MD3_MAX_VERTS, split_by_vertex_limit
    n = 9000
    big = Surface(name="word", shader="textures/pantheon/title",
                  verts=[(i * 0.1, 0.0, 0.0) for i in range(n)],
                  normals=[(0, 0, 1)] * n, uvs=[(0.0, 0.0)] * n,
                  tris=[(i, i + 1, i + 2) for i in range(0, n - 2, 3)])
    parts = split_by_vertex_limit(big)
    assert len(parts) > 1
    assert all(len(p.verts) <= MD3_MAX_VERTS for p in parts)
    assert sum(len(p.tris) for p in parts) == len(big.tris)
    assert all(p.shader == big.shader for p in parts)


def test_splitting_leaves_a_small_surface_alone():
    from engine.pantheon.md3_writer import split_by_vertex_limit
    s = _quad()
    assert split_by_vertex_limit(s) == [s]
