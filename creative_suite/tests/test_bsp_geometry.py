"""Tests for engine/parser/bsp_geometry.py — BSP loader, tracer, projection.

Uses a REAL map (maps/overkill.bsp) from the WolfcamQL staging pak00.pk3.
Skipped wholesale if the pk3 is not on disk (CI without the 13 GB corpus).
"""

import math
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "engine" / "parser"))

import bsp_geometry as bg  # noqa: E402

PK3 = bg.DEFAULT_PK3
HAVE_PK3 = PK3.exists()

pytestmark_real = pytest.mark.skipif(
    not HAVE_PK3, reason="staging pak00.pk3 not present")


@pytest.fixture(scope="module")
def overkill():
    if not HAVE_PK3:
        pytest.skip("staging pak00.pk3 not present")
    with zipfile.ZipFile(PK3) as z:
        assert "maps/overkill.bsp" in z.namelist()
    return bg.load_map("overkill")


# ── real-map structural checks ───────────────────────────────────────────────

@pytestmark_real
def test_lump_counts_sane(overkill):
    m = overkill
    assert m.version in (46, 47)
    c = m.lump_counts
    assert c["planes"] > 100
    assert c["nodes"] > 100
    assert c["leafs"] > c["nodes"] // 2
    assert c["brushes"] > 50
    assert c["brushsides"] >= c["brushes"] * 4     # every brush has >= 4 sides
    assert c["models"] >= 1
    assert c["visdata_bytes"] > 0
    # worldspawn brush range within brush lump
    lo, hi = m.world_brush_range
    assert 0 <= lo < hi <= c["brushes"]
    # world bounds ordered
    assert all(m.world_mins[i] < m.world_maxs[i] for i in range(3))


@pytestmark_real
def test_load_map_is_cached(overkill):
    assert bg.load_map("overkill") is overkill


@pytestmark_real
def test_ray_clear_same_room(overkill):
    # Two points hovering just above the same spawn pad (short open segment).
    eye = (-80.0, -152.0, 306.0)          # info_player_deathmatch + viewheight
    near = (-30.0, -152.0, 306.0)         # 50 units away, same room
    assert bg.los(overkill, eye, near)
    assert not bg.line_blocked(overkill, eye, near)


@pytestmark_real
def test_ray_through_floor_blocked(overkill):
    eye = (-80.0, -152.0, 306.0)
    below = (-80.0, -152.0, -6000.0)      # far below the world
    assert bg.line_blocked(overkill, eye, below)
    assert not bg.los(overkill, eye, below)


@pytestmark_real
def test_visible_fraction_open_pair(overkill):
    eye = (-80.0, -152.0, 306.0)
    victim = (-30.0, -152.0, 290.0)       # standing right next to the eye
    assert bg.visible_fraction(overkill, eye, victim) == 1.0


@pytestmark_real
def test_visible_fraction_outside_world(overkill):
    eye = (-80.0, -152.0, 306.0)
    far_out = (-80.0, -152.0, -20000.0)   # far outside the world
    assert bg.visible_fraction(overkill, eye, far_out) == 0.0


# ── synthetic math tests (no BSP needed) ─────────────────────────────────────

def test_project_point_straight_ahead_center():
    xy = bg.project((0, 0, 0), (0, 0), 90.0, (512, 0, 0), 1920, 1080)
    assert xy is not None
    assert xy[0] == pytest.approx(960.0)
    assert xy[1] == pytest.approx(540.0)


def test_project_behind_is_none():
    assert bg.project((0, 0, 0), (0, 0), 90.0, (-10, 0, 0)) is None


def test_project_right_of_center():
    # Yaw 0 looks +x; a point at +x with -y offset is to the viewer's RIGHT
    # (q3 right vector at yaw 0 is (0,-1,0)).
    xy = bg.project((0, 0, 0), (0, 0), 90.0, (100, -50, 0), 1920, 1080)
    assert xy is not None and xy[0] > 960.0


def test_project_edge_of_fov():
    # 45 deg off-axis with fov_x 90 lands exactly on the screen edge.
    xy = bg.project((0, 0, 0), (0, 0), 90.0, (100, -100, 0), 1920, 1080)
    assert xy is not None
    assert xy[0] == pytest.approx(1920.0)


def test_angle_vectors_axes():
    f, r, u = bg.angle_vectors((0.0, 0.0, 0.0))
    assert f == pytest.approx((1, 0, 0))
    assert r == pytest.approx((0, -1, 0))
    assert u == pytest.approx((0, 0, 1))
    f, _, _ = bg.angle_vectors((0.0, 90.0))
    assert f == pytest.approx((0, 1, 0), abs=1e-9)
    f, _, _ = bg.angle_vectors((90.0, 0.0))     # pitch down in q3 is +
    assert f == pytest.approx((0, 0, -1), abs=1e-9)


def test_angular_size_known_distance():
    # bbox half-height 28: at distance 28 the size is 2*atan(1) = 90 deg.
    eye = (0.0, 0.0, 4.0)                  # level with bbox center (z+4)
    got = bg.angular_size_deg(eye, (28.0, 0.0, 0.0))
    assert got == pytest.approx(90.0)


def test_angular_size_shrinks_with_distance():
    near = bg.angular_size_deg((0, 0, 4), (100, 0, 0))
    far = bg.angular_size_deg((0, 0, 4), (2000, 0, 0))
    assert near > far > 0


def test_segment_hits_aabb():
    box = (-10, -10, -10, 10, 10, 10)
    assert bg._segment_hits_aabb(box, (-50, 0, 0), (50, 0, 0))
    assert not bg._segment_hits_aabb(box, (-50, 50, 0), (50, 50, 0))
    # segment ending before the box
    assert not bg._segment_hits_aabb(box, (-50, 0, 0), (-20, 0, 0))
    # degenerate axis: ray in plane of box face
    assert bg._segment_hits_aabb(box, (0, 0, -50), (0, 0, 50))


def test_eye_point_offset():
    assert bg.eye_point((1, 2, 3)) == (1, 2, 3 + 26.0)


# ── synthetic brush trace via a hand-built map ───────────────────────────────

def _cube_map(cube_min=-16.0, cube_max=16.0):
    """A BspMap with a single solid axis-aligned cube brush and one leaf."""
    m = bg.BspMap("synthetic")
    # planes: +x,-x,+y,-y,+z,-z faces (normal pointing OUT, dist = plane offset)
    m.planes = [
        (1, 0, 0, cube_max), (-1, 0, 0, -cube_min),
        (0, 1, 0, cube_max), (0, -1, 0, -cube_min),
        (0, 0, 1, cube_max), (0, 0, -1, -cube_min),
    ]
    m.brushsides = [0, 1, 2, 3, 4, 5]
    m.brushes = [(0, 6, bg.CONTENTS_SOLID)]
    m.leafs = [(0, 1)]
    m.leafbrushes = [0]
    m.nodes = [(0, -1, -1)]     # root sends everything to the single leaf
    m.world_brush_range = (0, 1)
    return m


def test_synthetic_brush_blocks_through_cube():
    m = _cube_map()
    assert bg.line_blocked(m, (-100, 0, 0), (100, 0, 0))


def test_synthetic_brush_clear_beside_cube():
    m = _cube_map()
    assert not bg.line_blocked(m, (-100, 100, 0), (100, 100, 0))
    assert not bg.line_blocked(m, (-100, 0, 100), (100, 0, 100))


def test_synthetic_brush_segment_stops_short():
    m = _cube_map()
    assert not bg.line_blocked(m, (-100, 0, 0), (-50, 0, 0))


def test_synthetic_nonsolid_brush_ignored():
    m = _cube_map()
    m.brushes = [(0, 6, 0)]     # contents 0 = not solid
    assert not bg.line_blocked(m, (-100, 0, 0), (100, 0, 0))


def test_synthetic_patch_triangles_occlude():
    m = _cube_map()
    m.brushes = [(0, 6, 0)]     # disable the brush
    # vertical square at x=0 spanning y,z in [-16,16], as two triangles
    a, b, c, d = (0, -16, -16), (0, 16, -16), (0, 16, 16), (0, -16, 16)
    m.patch_cells = [((-1, -17, -17, 1, 17, 17), [(a, b, c), (a, c, d)])]
    assert bg.line_blocked(m, (-100, 0, 0), (100, 0, 0))
    assert not bg.line_blocked(m, (-100, 100, 0), (100, 100, 0))
    # ray inside the cull AABB but missing the triangles
    assert not bg.line_blocked(m, (-100, 0, 20), (100, 0, 20))


def test_synthetic_patch_aabb_fallback_occludes():
    m = _cube_map()
    m.brushes = [(0, 6, 0)]
    m.patch_cells = [((-16, -16, -16, 16, 16, 16), None)]   # aabb IS occluder
    assert bg.line_blocked(m, (-100, 0, 0), (100, 0, 0))
    assert not bg.line_blocked(m, (-100, 100, 0), (100, 100, 0))


def test_bezier_cell_mesh_flat_square():
    # Flat 3x3 control grid over [0,32]^2 at z=0 -> triangles lie in z=0.
    ctrl = [[(x * 16.0, y * 16.0, 0.0) for x in range(3)] for y in range(3)]
    aabb, tris = bg._bezier_cell_mesh(ctrl)
    assert len(tris) == 32
    assert aabb[2] == pytest.approx(-1.0) and aabb[5] == pytest.approx(1.0)
    # a ray straight down through the middle must hit the mesh
    assert any(bg._segment_hits_triangle((16, 16, 50), (16, 16, -50), *t)
               for t in tris)


def test_segment_hits_triangle_basic():
    tri = ((0, -10, -10), (0, 10, -10), (0, 0, 10))
    assert bg._segment_hits_triangle((-5, 0, 0), (5, 0, 0), *tri)
    assert not bg._segment_hits_triangle((-5, 50, 0), (5, 50, 0), *tri)
    # segment ending before the plane
    assert not bg._segment_hits_triangle((-5, 0, 0), (-1, 0, 0), *tri)


def test_synthetic_visible_fraction_partial():
    # Wall covering z <= 0 between eye and victim: lower bbox samples blocked.
    m = bg.BspMap("wall")
    m.planes = [
        (1, 0, 0, 1.0), (-1, 0, 0, 1.0),
        (0, 1, 0, 1000.0), (0, -1, 0, 1000.0),
        (0, 0, 1, 28.0), (0, 0, -1, 1000.0),
    ]
    m.brushsides = [0, 1, 2, 3, 4, 5]
    m.brushes = [(0, 6, bg.CONTENTS_SOLID)]
    m.leafs = [(0, 1)]
    m.leafbrushes = [0]
    m.nodes = [(0, -1, -1)]
    m.world_brush_range = (0, 1)
    frac = bg.visible_fraction(m, (-200, 0, 30), (200, 0, 30))
    assert 0.0 < frac < 1.0
