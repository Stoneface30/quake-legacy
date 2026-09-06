"""Quake 3 BSP loader + collision ray tracer (pure Python, read-only).

Loads ``maps/<name>.bsp`` entries straight out of the WolfcamQL staging
``pak00.pk3`` (a zip archive) and answers geometric questions the Stage-2
frag-recognition engine needs:

  * ``line_blocked(map, start, end)``   — does world geometry block the segment?
  * ``los(map, eye, point)``            — line of sight boolean
  * ``visible_fraction(map, eye, org)`` — fraction of a player bbox visible
  * ``project(...)``                    — world point -> screen pixel
  * ``angular_size_deg(eye, org)``      — apparent size of a player on screen

Format reference: the well-known id Tech 3 BSP spec (IBSP version 46/47),
cross-checked against ``engine/engines``' ioquake3/wolfcamql sources
(``code/qcommon/cm_load.c``, ``cm_trace.c``) for lump layout and trace
semantics.

APPROXIMATIONS — read before trusting numbers
---------------------------------------------
1. The tracer is a boolean *line* clip against CONTENTS_SOLID brushes of
   model 0 (worldspawn) only.  It does NOT expand brushes by a trace bbox
   (no bevel planes are needed because the trace is a zero-width line, for
   which the stored brush sides are exact — bevels only matter for volume
   traces; see cm_trace.c comments).
2. Q3 maps also contain curved surfaces (Bezier patches, lump Surfaces(13)
   type==2) which have NO brushes.  A pure brush tracer sees straight
   through them.  We tessellate each 3x3 Bezier control cell into a 4x4
   quad grid (32 triangles) and ray-test those triangles exactly, with the
   cell AABB used only for culling.  The chord-vs-curve gap means a ray
   grazing a strongly curved patch can leak (slight under-occlusion) —
   comparable to the game's own tessellated collision.
3. Doors / movers / other submodels (models 1..N) are ignored: their
   position at frag time depends on entity state we do not track.  A frag
   through a closed door will therefore read as *visible*.
4. ``visible_fraction`` point-samples a 3x3x3 grid over the player bbox;
   it is occlusion sampling, not analytic area visibility.

None of this is a physics-grade q3 trace; it is evidence-grade geometry.
"""

from __future__ import annotations

import math
from typing import Sequence
from dataclasses import dataclass
import math
import re
import struct
import zipfile
from functools import lru_cache
from pathlib import Path

# ── constants ────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]


def _pk3_root() -> Path:
    """The checkout that owns the data. The staged pak is gitignored, so it
    exists once; a git worktree of the CODE has no staging under it and every
    map load failed there with a bare FileNotFoundError."""
    try:
        from engine.pantheon.store import PROJECT_ROOT
        return PROJECT_ROOT
    except Exception:
        return REPO_ROOT


DEFAULT_PK3 = _pk3_root() / "output" / "demo_v2" / "_wolfcam_staging" / "baseq3" / "pak00.pk3"

CONTENTS_SOLID = 0x1

# Lump indices (id Tech 3 / cm_load.c)
LUMP_ENTITIES     = 0
LUMP_SHADERS      = 1   # "Textures" in the community spec — carries contents flags
LUMP_PLANES       = 2
LUMP_NODES        = 3
LUMP_LEAFS        = 4
LUMP_LEAFSURFACES = 5
LUMP_LEAFBRUSHES  = 6
LUMP_MODELS       = 7
LUMP_BRUSHES      = 8
LUMP_BRUSHSIDES   = 9
LUMP_VERTICES     = 10
LUMP_SURFACES     = 13
LUMP_VISDATA      = 16

_HEADER_LUMPS = 17

# Player bounding box (bg_public.h: playerMins/playerMaxs) + viewheight
PLAYER_MINS = (-15.0, -15.0, -24.0)
PLAYER_MAXS = ( 15.0,  15.0,  32.0)
EYE_OFFSET_Z = 26.0     # DEFAULT_VIEWHEIGHT

_EPS = 0.03125          # 1/32, the classic q3 DIST_EPSILON


# ── data model ───────────────────────────────────────────────────────────────

class BspMap:
    """Parsed collision-relevant data of one BSP."""

    __slots__ = ("name", "version", "lump_counts", "planes", "nodes", "leafs",
                 "leafbrushes", "brushes", "brushsides", "patch_cells",
                 "world_brush_range", "world_mins", "world_maxs",
                 "entities", "model_bounds")

    def __init__(self, name: str):
        self.name = name
        self.version = 0
        self.lump_counts: dict[str, int] = {}
        # Entity lump: the map's own list of what stands where. Teleporters,
        # spawn points and jump pads are FIXED map geometry, so a destination
        # is map truth, not something inferred from where a player ended up.
        self.entities: list[dict[str, str]] = []
        self.model_bounds: list[tuple[float, float, float, float, float, float]] = []
        self.planes: list[tuple[float, float, float, float]] = []
        # node: (plane_idx, child0, child1)
        self.nodes: list[tuple[int, int, int]] = []
        # leaf: (leafbrush_first, n_leafbrushes)
        self.leafs: list[tuple[int, int]] = []
        self.leafbrushes: list[int] = []
        # brush: (side_first, n_sides, contents)
        self.brushes: list[tuple[int, int, int]] = []
        # brushside: plane_idx
        self.brushsides: list[int] = []
        # patch cells: (cull_aabb, triangles_or_None). triangles = exact
        # tessellated occluders; None means the aabb itself occludes (fallback).
        self.patch_cells: list[tuple[tuple, list | None]] = []
        self.world_brush_range = (0, 0)
        self.world_mins = (0.0, 0.0, 0.0)
        self.world_maxs = (0.0, 0.0, 0.0)


def _bezier_cell_mesh(ctrl, n: int = 4):
    """Tessellate one 3x3 biquadratic Bezier cell.

    Returns (aabb, triangles): a culling AABB over the (n+1)x(n+1) sample
    grid (padded 1.0) and the 2*n*n surface triangles.  Triangles are the
    actual occluders — thin and exact — so a player standing on/near a big
    curved ramp is not swallowed by a fat bounding box.
    """
    def bez(cp0, cp1, cp2, t):
        a = (1 - t) * (1 - t)
        b = 2 * t * (1 - t)
        c = t * t
        return (a * cp0[0] + b * cp1[0] + c * cp2[0],
                a * cp0[1] + b * cp1[1] + c * cp2[1],
                a * cp0[2] + b * cp1[2] + c * cp2[2])

    grid = []
    for j in range(n + 1):
        v = j / n
        col = [bez(ctrl[0][i], ctrl[1][i], ctrl[2][i], v) for i in range(3)]
        row = [bez(col[0], col[1], col[2], i / n) for i in range(n + 1)]
        grid.append(row)

    pts = [p for row in grid for p in row]
    aabb = (min(p[0] for p in pts) - 1.0, min(p[1] for p in pts) - 1.0,
            min(p[2] for p in pts) - 1.0, max(p[0] for p in pts) + 1.0,
            max(p[1] for p in pts) + 1.0, max(p[2] for p in pts) + 1.0)
    tris = []
    for j in range(n):
        for i in range(n):
            p00 = grid[j][i]
            p10 = grid[j][i + 1]
            p01 = grid[j + 1][i]
            p11 = grid[j + 1][i + 1]
            tris.append((p00, p10, p11))
            tris.append((p00, p11, p01))
    return aabb, tris


def _segment_hits_triangle(p1, p2, a, b, c) -> bool:
    """Two-sided Moller-Trumbore segment/triangle intersection."""
    dx, dy, dz = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]
    e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    px = dy * e2[2] - dz * e2[1]
    py = dz * e2[0] - dx * e2[2]
    pz = dx * e2[1] - dy * e2[0]
    det = e1[0] * px + e1[1] * py + e1[2] * pz
    if -1e-9 < det < 1e-9:
        return False
    inv = 1.0 / det
    tx, ty, tz = p1[0] - a[0], p1[1] - a[1], p1[2] - a[2]
    u = (tx * px + ty * py + tz * pz) * inv
    if u < -1e-6 or u > 1.000001:
        return False
    qx = ty * e1[2] - tz * e1[1]
    qy = tz * e1[0] - tx * e1[2]
    qz = tx * e1[1] - ty * e1[0]
    v = (dx * qx + dy * qy + dz * qz) * inv
    if v < -1e-6 or u + v > 1.000001:
        return False
    t = (e2[0] * qx + e2[1] * qy + e2[2] * qz) * inv
    return -1e-6 <= t <= 1.000001


def _lump_bytes(data: bytes, dirent: tuple[int, int]) -> bytes:
    off, length = dirent
    return data[off:off + length]


_ENT_KV = re.compile(rb'"([^"]*)"\s+"([^"]*)"')


def parse_entities(raw: bytes) -> list[dict[str, str]]:
    """The entity lump is plain text: { "key" "value" ... } blocks.

    Values stay strings exactly as authored; callers convert. Keys are
    lower-cased because mappers are inconsistent about case.
    """
    out: list[dict[str, str]] = []
    for block in re.findall(rb"\{([^{}]*)\}", raw.split(bytes(1))[0]):
        ent = {k.decode("latin-1").lower(): v.decode("latin-1")
               for k, v in _ENT_KV.findall(block)}
        if ent:
            out.append(ent)
    return out


def _vec(text: str | None) -> tuple[float, float, float] | None:
    if not text:
        return None
    parts = text.split()
    if len(parts) < 3:
        return None
    try:
        return (float(parts[0]), float(parts[1]), float(parts[2]))
    except ValueError:
        return None


# Entity classes that put a player somewhere. From g_spawn.c's spawn table:
# a trigger_teleport targets a target_position / misc_teleporter_dest, and
# a target_teleporter does the same from a target rather than a brush.
TELEPORT_TRIGGERS = ("trigger_teleport", "target_teleporter")
TELEPORT_DESTS = ("misc_teleporter_dest", "target_position", "info_notnull")
SPAWN_POINTS = ("info_player_deathmatch", "info_player_start",
                "team_ctf_redplayer", "team_ctf_blueplayer",
                "team_ctf_redspawn", "team_ctf_bluespawn")
JUMP_PADS = ("trigger_push", "target_push")


@dataclass(frozen=True)
class Teleporter:
    """One fixed source -> destination pair declared by the map."""
    target: str
    dest: tuple[float, float, float]
    source_bounds: tuple[float, float, float, float, float, float] | None
    source_kind: str

    def dest_distance(self, point: Sequence[float]) -> float:
        return math.dist(self.dest, tuple(point)[:3])

    def source_contains(self, point: Sequence[float], slack: float = 32.0) -> bool:
        if self.source_bounds is None:
            return False
        x0, y0, z0, x1, y1, z1 = self.source_bounds
        x, y, z = tuple(point)[:3]
        return (x0 - slack <= x <= x1 + slack and y0 - slack <= y <= y1 + slack
                and z0 - slack <= z <= z1 + slack)


def teleporters(m: BspMap) -> list[Teleporter]:
    """Source/destination pairs from the map's own entity lump."""
    dests: dict[str, tuple[float, float, float]] = {}
    for e in m.entities:
        if e.get("classname", "") in TELEPORT_DESTS:
            origin = _vec(e.get("origin"))
            name = e.get("targetname")
            if origin and name:
                dests.setdefault(name, origin)
    out: list[Teleporter] = []
    for e in m.entities:
        cls = e.get("classname", "")
        if cls not in TELEPORT_TRIGGERS:
            continue
        target = e.get("target", "")
        dest = dests.get(target)
        if dest is None:
            continue
        bounds = None
        model = e.get("model", "")
        if model.startswith("*"):
            try:
                idx = int(model[1:])
            except ValueError:
                idx = -1
            if 0 <= idx < len(m.model_bounds):
                bounds = m.model_bounds[idx]
        elif _vec(e.get("origin")):
            ox, oy, oz = _vec(e.get("origin"))
            bounds = (ox - 16, oy - 16, oz - 24, ox + 16, oy + 16, oz + 32)
        out.append(Teleporter(target, dest, bounds, cls))
    return out


def spawn_points(m: BspMap) -> list[tuple[float, float, float]]:
    """Where players materialise on respawn. A teleport_in at one of these is
    a spawn, not a trip through a teleporter."""
    out = []
    for e in m.entities:
        if e.get("classname", "") in SPAWN_POINTS:
            v = _vec(e.get("origin"))
            if v:
                out.append(v)
    return out


def _read_lump(data: bytes, dirent: tuple[int, int], fmt: str) -> list[tuple]:
    off, length = dirent
    size = struct.calcsize(fmt)
    n = length // size
    return list(struct.iter_unpack(fmt, data[off:off + n * size]))


def load_map_bytes(name: str, data: bytes) -> BspMap:
    """Parse BSP bytes into a BspMap (collision lumps only)."""
    if data[:4] != b"IBSP":
        raise ValueError(f"{name}: not an IBSP file (magic={data[:4]!r})")
    version = struct.unpack_from("<i", data, 4)[0]
    if version not in (46, 47):
        raise ValueError(f"{name}: unsupported IBSP version {version}")

    dirents = [struct.unpack_from("<ii", data, 8 + 8 * i) for i in range(_HEADER_LUMPS)]

    m = BspMap(name)
    m.version = version

    # shaders (72 bytes: name[64], surfaceFlags, contentFlags)
    shaders = _read_lump(data, dirents[LUMP_SHADERS], "<64sii")
    shader_contents = [s[2] for s in shaders]

    # planes (normal[3], dist)
    m.planes = [tuple(p) for p in _read_lump(data, dirents[LUMP_PLANES], "<ffff")]

    # nodes (planeNum, children[2], mins[3], maxs[3]) = 9 ints
    m.nodes = [(n[0], n[1], n[2]) for n in _read_lump(data, dirents[LUMP_NODES], "<9i")]

    # leafs (cluster, area, mins[3], maxs[3], firstLeafSurface, numLeafSurfaces,
    #        firstLeafBrush, numLeafBrushes) = 12 ints
    m.leafs = [(l[10], l[11]) for l in _read_lump(data, dirents[LUMP_LEAFS], "<12i")]

    m.leafbrushes = [b[0] for b in _read_lump(data, dirents[LUMP_LEAFBRUSHES], "<i")]

    # models (mins[3]f, maxs[3]f, firstSurface, numSurfaces, firstBrush, numBrushes)
    models = _read_lump(data, dirents[LUMP_MODELS], "<6f4i")
    if not models:
        raise ValueError(f"{name}: no models lump")
    m.model_bounds = [(mo[0], mo[1], mo[2], mo[3], mo[4], mo[5]) for mo in models]
    w = models[0]
    m.world_mins = (w[0], w[1], w[2])
    m.world_maxs = (w[3], w[4], w[5])
    m.world_brush_range = (w[8], w[8] + w[9])

    # brushes (firstSide, numSides, shaderNum)
    raw_brushes = _read_lump(data, dirents[LUMP_BRUSHES], "<3i")
    m.brushes = [
        (b[0], b[1], shader_contents[b[2]] if 0 <= b[2] < len(shader_contents) else 0)
        for b in raw_brushes
    ]

    # brushsides (planeNum, shaderNum)
    m.brushsides = [s[0] for s in _read_lump(data, dirents[LUMP_BRUSHSIDES], "<2i")]

    # patches -> AABB occluders.
    # drawVert = position[3]f, st[2]f, lightmap[2]f, normal[3]f, color[4]B = 44B
    # surface  = 26 ints (104 bytes); type at index 2, firstVert 3, numVerts 4
    verts_off, verts_len = dirents[LUMP_VERTICES]
    n_verts = verts_len // 44
    surfaces = _read_lump(data, dirents[LUMP_SURFACES], "<26i")
    for s in surfaces:
        if s[2] != 2:               # MST_PATCH
            continue
        first, num = s[3], s[4]
        pw, ph = s[24], s[25]       # patchWidth, patchHeight (control grid)
        if num <= 0 or first < 0 or first + num > n_verts:
            continue
        pts = [struct.unpack_from("<3f", data, verts_off + vi * 44)
               for vi in range(first, first + num)]
        if pw >= 3 and ph >= 3 and pw * ph == num:
            # Tessellate each 3x3 biquadratic Bezier cell at 5x5 samples and
            # box each sample quad (slightly inflated).  Tight boxes that hug
            # the actual curved surface — a single AABB around a large curved
            # patch (dome/bowl) can wall off an entire room.
            for cy in range(0, ph - 2, 2):
                for cx in range(0, pw - 2, 2):
                    ctrl = [[pts[(cy + j) * pw + (cx + i)] for i in range(3)]
                            for j in range(3)]
                    m.patch_cells.append(_bezier_cell_mesh(ctrl))
        else:
            xs2 = [p[0] for p in pts]
            ys2 = [p[1] for p in pts]
            zs2 = [p[2] for p in pts]
            m.patch_cells.append(((min(xs2), min(ys2), min(zs2),
                                   max(xs2), max(ys2), max(zs2)), None))

    m.entities = parse_entities(_lump_bytes(data, dirents[LUMP_ENTITIES]))

    m.lump_counts = {
        "entities": len(m.entities),
        "shaders": len(shaders),
        "planes": len(m.planes),
        "nodes": len(m.nodes),
        "leafs": len(m.leafs),
        "leafbrushes": len(m.leafbrushes),
        "models": len(models),
        "brushes": len(m.brushes),
        "brushsides": len(m.brushsides),
        "patch_cells": len(m.patch_cells),
        "visdata_bytes": dirents[LUMP_VISDATA][1],
        "entities_bytes": dirents[LUMP_ENTITIES][1],
    }
    return m


@lru_cache(maxsize=8)
def load_map(map_name: str, pk3_path: str | None = None) -> BspMap:
    """Load ``maps/<map_name>.bsp`` from the staging pak00.pk3 (read-only)."""
    pk3 = Path(pk3_path) if pk3_path else DEFAULT_PK3
    entry = f"maps/{map_name.lower()}.bsp"
    with zipfile.ZipFile(pk3, "r") as z:
        data = z.read(entry)
    return load_map_bytes(map_name, data)


# ── trace ────────────────────────────────────────────────────────────────────

def _segment_hits_brush(m: BspMap, brush_idx: int, p1, p2) -> bool:
    """Zero-width line vs convex brush: slab clip over the brush's planes."""
    first, count, contents = m.brushes[brush_idx]
    if not (contents & CONTENTS_SOLID):
        return False
    enter_f = -1.0
    leave_f = 2.0
    for si in range(first, first + count):
        nx, ny, nz, dist = m.planes[m.brushsides[si]]
        d1 = p1[0] * nx + p1[1] * ny + p1[2] * nz - dist
        d2 = p2[0] * nx + p2[1] * ny + p2[2] * nz - dist
        if d1 > _EPS and d2 > _EPS:
            return False                       # fully outside this side
        if d1 <= _EPS and d2 <= _EPS:
            continue                            # fully inside this side
        f = d1 / (d1 - d2)
        if d1 > d2:                             # entering the halfspace
            if f > enter_f:
                enter_f = f
        else:                                   # leaving
            if f < leave_f:
                leave_f = f
        if enter_f > leave_f:
            return False
    return enter_f <= leave_f


def _segment_hits_aabb(box, p1, p2) -> bool:
    """Segment vs axis-aligned box (slab method)."""
    t0, t1 = 0.0, 1.0
    for a in range(3):
        lo, hi = box[a], box[a + 3]
        d = p2[a] - p1[a]
        if abs(d) < 1e-9:
            if p1[a] < lo or p1[a] > hi:
                return False
            continue
        inv = 1.0 / d
        ta = (lo - p1[a]) * inv
        tb = (hi - p1[a]) * inv
        if ta > tb:
            ta, tb = tb, ta
        if ta > t0: t0 = ta
        if tb < t1: t1 = tb
        if t0 > t1:
            return False
    return True


def line_blocked(m: BspMap, start, end) -> bool:
    """True if world geometry blocks the segment start->end.

    Walks the BSP tree iteratively gathering leaves the segment touches,
    tests their CONTENTS_SOLID worldspawn brushes, then tests patch AABBs.
    """
    lo, hi = m.world_brush_range
    checked: set[int] = set()
    # stack of (node_idx, p1, p2)
    stack = [(0, tuple(start), tuple(end))]
    while stack:
        node_idx, p1, p2 = stack.pop()
        while node_idx >= 0:
            plane_idx, c0, c1 = m.nodes[node_idx]
            nx, ny, nz, dist = m.planes[plane_idx]
            d1 = p1[0] * nx + p1[1] * ny + p1[2] * nz - dist
            d2 = p2[0] * nx + p2[1] * ny + p2[2] * nz - dist
            if d1 >= -_EPS and d2 >= -_EPS:
                node_idx = c0
            elif d1 < _EPS and d2 < _EPS:
                node_idx = c1
            else:
                # spans the plane: split so each side gets its sub-segment
                f = d1 / (d1 - d2)
                mid = (p1[0] + f * (p2[0] - p1[0]),
                       p1[1] + f * (p2[1] - p1[1]),
                       p1[2] + f * (p2[2] - p1[2]))
                if d1 >= 0:
                    stack.append((c1, mid, p2))
                    node_idx = c0
                    p2 = mid
                else:
                    stack.append((c0, mid, p2))
                    node_idx = c1
                    p2 = mid
        # leaf
        lb_first, lb_num = m.leafs[-(node_idx + 1)]
        for i in range(lb_first, lb_first + lb_num):
            b = m.leafbrushes[i]
            if b in checked or not (lo <= b < hi):
                continue
            checked.add(b)
            if _segment_hits_brush(m, b, start, end):
                return True
    for aabb, tris in m.patch_cells:
        if not _segment_hits_aabb(aabb, start, end):
            continue
        if tris is None:
            return True
        for a, b, c in tris:
            if _segment_hits_triangle(start, end, a, b, c):
                return True
    return False


def los(m: BspMap, eye, point) -> bool:
    """Line-of-sight boolean between two world points."""
    return not line_blocked(m, eye, point)


def visible_fraction(m: BspMap, eye, victim_origin) -> float:
    """Fraction of a 3x3x3 sample grid over the victim bbox with clear LOS."""
    ox, oy, oz = victim_origin
    xs = [ox + PLAYER_MINS[0], ox, ox + PLAYER_MAXS[0]]
    ys = [oy + PLAYER_MINS[1], oy, oy + PLAYER_MAXS[1]]
    zs = [oz + PLAYER_MINS[2], oz + (PLAYER_MINS[2] + PLAYER_MAXS[2]) / 2.0,
          oz + PLAYER_MAXS[2]]
    clear = 0
    total = 0
    for x in xs:
        for y in ys:
            for z in zs:
                total += 1
                if not line_blocked(m, eye, (x, y, z)):
                    clear += 1
    return clear / total


def eye_point(origin) -> tuple[float, float, float]:
    """Attacker eye position: origin + viewheight."""
    return (origin[0], origin[1], origin[2] + EYE_OFFSET_Z)


# ── projection math (no BSP needed) ─────────────────────────────────────────

def angle_vectors(angles_deg):
    """Q3 AngleVectors: angles = (pitch, yaw, roll) degrees -> forward, right, up."""
    pitch = math.radians(angles_deg[0])
    yaw   = math.radians(angles_deg[1])
    roll  = math.radians(angles_deg[2]) if len(angles_deg) > 2 else 0.0
    sp, cp = math.sin(pitch), math.cos(pitch)
    sy, cy = math.sin(yaw),   math.cos(yaw)
    sr, cr = math.sin(roll),  math.cos(roll)
    forward = (cp * cy, cp * sy, -sp)
    # Q3 q_math.c AngleVectors: right = (-sr*sp*cy + cr*sy, -sr*sp*sy - cr*cy, -sr*cp)
    right = (-sr * sp * cy + cr * sy,
             -sr * sp * sy - cr * cy,
             -sr * cp)
    up = (cr * sp * cy + sr * sy,
          cr * sp * sy - sr * cy,
          cr * cp)
    return forward, right, up


def project(view_origin, view_angles_deg, fov_x_deg, point,
            screen_w: int = 1920, screen_h: int = 1080):
    """Project a world point to screen pixels. None if at/behind the near plane.

    view_angles_deg = (pitch, yaw[, roll]).  fov_x is horizontal; vertical fov
    follows the Q3 aspect relation tan(fovy/2) = tan(fovx/2) * h/w.
    """
    fwd, right, up = angle_vectors(view_angles_deg)
    lx = point[0] - view_origin[0]
    ly = point[1] - view_origin[1]
    lz = point[2] - view_origin[2]
    f = lx * fwd[0] + ly * fwd[1] + lz * fwd[2]
    if f <= 1e-6:
        return None
    r = lx * right[0] + ly * right[1] + lz * right[2]
    u = lx * up[0] + ly * up[1] + lz * up[2]
    tan_hx = math.tan(math.radians(fov_x_deg) / 2.0)
    tan_hy = tan_hx * screen_h / screen_w
    x = screen_w / 2.0 + (r / f) * (screen_w / 2.0) / tan_hx
    y = screen_h / 2.0 - (u / f) * (screen_h / 2.0) / tan_hy
    return (x, y)


def angular_size_deg(eye, victim_origin) -> float:
    """Apparent angular height (degrees) of the player bbox from the eye.

    Uses the 56-unit bbox height as the subtended chord: 2*atan(28/d) where
    d is eye->bbox-center distance.  0 if the eye is inside the bbox.
    """
    cx = victim_origin[0]
    cy = victim_origin[1]
    cz = victim_origin[2] + (PLAYER_MINS[2] + PLAYER_MAXS[2]) / 2.0
    d = math.dist(eye, (cx, cy, cz))
    if d < 1e-6:
        return 180.0
    half_h = (PLAYER_MAXS[2] - PLAYER_MINS[2]) / 2.0   # 28 units
    return math.degrees(2.0 * math.atan(half_h / d))
