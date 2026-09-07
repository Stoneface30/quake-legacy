"""MD3 — read and write Quake III model files, in PANTHEON's own code.

Custom PANTHEON geometry (doors, plinths, banners, glyphs) has to reach the
native renderer as something the engine already knows how to draw, and MD3 is
that thing: the format every player, weapon and prop in the game already uses.
Writing it ourselves means the world assets are generated, diffable and
reproducible rather than binary blobs nobody can regenerate.

Every constant and layout here is taken from the engine we ship against,
`code/qcommon/qfiles.h` of the banked WolfcamQL 11.3 source, and the normal
encoding from `tr_surface.c` where the renderer decodes it:

    lat = (normal >> 8) & 0xff        X = cos(lat) * sin(lng)
    lng = (normal     ) & 0xff        Y = sin(lat) * sin(lng)
    angle = byte * 2*pi / 256         Z = cos(lng)

so `lat` is the azimuth atan2(y, x) and `lng` is the polar angle acos(z).
Getting that pair the wrong way round produces a model that renders with
plausible but wrong lighting, which is exactly the kind of defect that
survives a screenshot.

The writer is deliberately small: one static frame unless told otherwise, no
tags unless given, positions quantised to 1/64 unit like the engine's own
`MD3_XYZ_SCALE`. Vertex animation is possible (pass several frames) and is how
a door leaf could deform, but a door does not deform -- it moves, and movement
belongs to the trajectory, not the mesh.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

# ── qfiles.h ───────────────────────────────────────────────────────────────
MD3_IDENT = (ord('3') << 24) + (ord('P') << 16) + (ord('D') << 8) + ord('I')
MD3_VERSION = 15
MD3_XYZ_SCALE = 1.0 / 64
MAX_QPATH = 64
MD3_MAX_TRIANGLES = 8192        # per surface
MD3_MAX_VERTS = 4096            # per surface
MD3_MAX_SURFACES = 32           # per model

_HEADER = struct.Struct("<ii64si4i4i")          # ident..ofsEnd
_FRAME = struct.Struct("<10f16s")
_TAG = struct.Struct("<64s12f")
_SURFACE = struct.Struct("<i64si4i5i")
_SHADER = struct.Struct("<64si")

Vec3 = tuple[float, float, float]
Vec2 = tuple[float, float]


def _qpath(s: str, size: int = MAX_QPATH) -> bytes:
    b = s.encode("ascii", "replace")[: size - 1]
    return b + b"\0" * (size - len(b))


def encode_normal(n: Vec3) -> int:
    """Pack a unit normal the way the renderer unpacks it."""
    x, y, z = n
    length = math.sqrt(x * x + y * y + z * z)
    if length < 1e-9:
        return 0
    x, y, z = x / length, y / length, z / length
    lat = int(round(math.atan2(y, x) * 255.0 / (2 * math.pi))) & 0xFF
    lng = int(round(math.acos(max(-1.0, min(1.0, z))) * 255.0 / (2 * math.pi))) & 0xFF
    return (lat << 8) | lng


def decode_normal(packed: int) -> Vec3:
    """The renderer's own decode, for verification."""
    lat = ((packed >> 8) & 0xFF) * 2 * math.pi / 256.0
    lng = (packed & 0xFF) * 2 * math.pi / 256.0
    return (math.cos(lat) * math.sin(lng),
            math.sin(lat) * math.sin(lng),
            math.cos(lng))


@dataclass
class Surface:
    """One shader's worth of triangles. A surface is the unit of material."""

    name: str
    shader: str
    verts: list[Vec3]                       # world units, frame 0
    normals: list[Vec3]
    uvs: list[Vec2]
    tris: list[tuple[int, int, int]]
    extra_frames: list[list[Vec3]] = field(default_factory=list)

    def validate(self) -> None:
        n = len(self.verts)
        if not (len(self.normals) == len(self.uvs) == n):
            raise ValueError(f"{self.name}: verts/normals/uvs disagree "
                             f"({n}/{len(self.normals)}/{len(self.uvs)})")
        if n > MD3_MAX_VERTS:
            raise ValueError(f"{self.name}: {n} verts exceeds MD3_MAX_VERTS")
        if len(self.tris) > MD3_MAX_TRIANGLES:
            raise ValueError(f"{self.name}: too many triangles")
        for t in self.tris:
            if any(i < 0 or i >= n for i in t):
                raise ValueError(f"{self.name}: triangle index out of range {t}")
        for f in self.extra_frames:
            if len(f) != n:
                raise ValueError(f"{self.name}: animation frame has {len(f)} verts, not {n}")


def _bounds(frames: Sequence[Sequence[Vec3]]) -> list[tuple[Vec3, Vec3, float]]:
    out = []
    for verts in frames:
        if not verts:
            out.append(((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.0))
            continue
        lo = tuple(min(v[i] for v in verts) for i in range(3))
        hi = tuple(max(v[i] for v in verts) for i in range(3))
        radius = max(math.dist((0, 0, 0), v) for v in verts)
        out.append((lo, hi, radius))
    return out


def write_md3(path: Path | str, surfaces: Sequence[Surface], *,
              name: str = "pantheon", tags: Sequence[tuple[str, Vec3]] = ()) -> Path:
    """Write one MD3. Returns the path.

    `tags` are per-frame attachment points with identity axes -- enough for
    "the door's hinge is here", not enough for a rotating child.
    """
    if not surfaces:
        raise ValueError("an MD3 with no surface is not a model")
    if len(surfaces) > MD3_MAX_SURFACES:
        raise ValueError(f"{len(surfaces)} surfaces exceeds MD3_MAX_SURFACES")
    for s in surfaces:
        s.validate()

    n_frames = 1 + len(surfaces[0].extra_frames)
    if any(1 + len(s.extra_frames) != n_frames for s in surfaces):
        raise ValueError("every surface must have the same frame count")

    # frame bounds are over ALL surfaces at that frame
    per_frame: list[list[Vec3]] = []
    for f in range(n_frames):
        acc: list[Vec3] = []
        for s in surfaces:
            acc.extend(s.verts if f == 0 else s.extra_frames[f - 1])
        per_frame.append(acc)
    frame_info = _bounds(per_frame)

    frames = b"".join(
        _FRAME.pack(lo[0], lo[1], lo[2], hi[0], hi[1], hi[2], 0.0, 0.0, 0.0, r,
                    _qpath(f"frame{i}", 16))
        for i, (lo, hi, r) in enumerate(frame_info))
    tag_blob = b"".join(
        _TAG.pack(_qpath(tname), o[0], o[1], o[2], 1, 0, 0, 0, 1, 0, 0, 0, 1)
        for _ in range(n_frames) for tname, o in tags)

    surf_blobs = []
    for s in surfaces:
        shaders = _SHADER.pack(_qpath(s.shader), 0)
        tris = b"".join(struct.pack("<3i", *t) for t in s.tris)
        st = b"".join(struct.pack("<2f", u, v) for u, v in s.uvs)
        xyz = bytearray()
        for f in range(n_frames):
            verts = s.verts if f == 0 else s.extra_frames[f - 1]
            for (x, y, z), n in zip(verts, s.normals):
                # xyz are SIGNED shorts; the packed normal is not. qfiles.h
                # declares it `short`, but lat >= 128 makes the value exceed
                # 32767 -- the engine reads the byte back with (n >> 8) & 0xff
                # either way, so it is written unsigned and read unsigned.
                xyz += struct.pack("<3hH", int(round(x / MD3_XYZ_SCALE)),
                                   int(round(y / MD3_XYZ_SCALE)),
                                   int(round(z / MD3_XYZ_SCALE)), encode_normal(n))
        head = _SURFACE.size
        ofs_shaders = head
        ofs_tris = ofs_shaders + len(shaders)
        ofs_st = ofs_tris + len(tris)
        ofs_xyz = ofs_st + len(st)
        ofs_end = ofs_xyz + len(xyz)
        surf_blobs.append(
            _SURFACE.pack(MD3_IDENT, _qpath(s.name), 0, n_frames, 1,
                          len(s.verts), len(s.tris),
                          ofs_tris, ofs_shaders, ofs_st, ofs_xyz, ofs_end)
            + shaders + tris + st + bytes(xyz))

    ofs_frames = _HEADER.size
    ofs_tags = ofs_frames + len(frames)
    ofs_surfaces = ofs_tags + len(tag_blob)
    ofs_end = ofs_surfaces + sum(len(b) for b in surf_blobs)
    header = _HEADER.pack(MD3_IDENT, MD3_VERSION, _qpath(name), 0,
                          n_frames, len(tags), len(surfaces), 0,
                          ofs_frames, ofs_tags, ofs_surfaces, ofs_end)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + frames + tag_blob + b"".join(surf_blobs))
    return path


def read_md3(src: Path | str | bytes) -> dict:
    """Parse an MD3 -- ours or the game's. Used to verify what we wrote and to
    read real assets rather than assuming what is in them."""
    data = src if isinstance(src, bytes) else Path(src).read_bytes()
    (ident, version, name, _flags, n_frames, n_tags, n_surf, _n_skins,
     ofs_frames, ofs_tags, ofs_surf, ofs_end) = _HEADER.unpack_from(data, 0)
    if ident != MD3_IDENT:
        raise ValueError("not an MD3 (bad ident)")
    if version != MD3_VERSION:
        raise ValueError(f"MD3 version {version}, expected {MD3_VERSION}")

    frames = []
    for i in range(n_frames):
        f = _FRAME.unpack_from(data, ofs_frames + i * _FRAME.size)
        frames.append({"mins": f[0:3], "maxs": f[3:6], "origin": f[6:9],
                       "radius": f[9], "name": f[10].split(b"\0")[0].decode()})
    tags = []
    for i in range(n_tags * n_frames):
        t = _TAG.unpack_from(data, ofs_tags + i * _TAG.size)
        tags.append({"name": t[0].split(b"\0")[0].decode(), "origin": t[1:4]})

    surfaces, off = [], ofs_surf
    for _ in range(n_surf):
        (s_ident, s_name, _f, s_frames, s_shaders, s_verts, s_tris,
         o_tris, o_shaders, o_st, o_xyz, o_end) = _SURFACE.unpack_from(data, off)
        if s_ident != MD3_IDENT:
            raise ValueError("surface ident mismatch")
        shader = _SHADER.unpack_from(data, off + o_shaders)[0].split(b"\0")[0].decode()
        tris = [struct.unpack_from("<3i", data, off + o_tris + i * 12)
                for i in range(s_tris)]
        uvs = [struct.unpack_from("<2f", data, off + o_st + i * 8)
               for i in range(s_verts)]
        verts, normals = [], []
        for i in range(s_verts):                      # frame 0 only
            x, y, z, n = struct.unpack_from("<3hH", data, off + o_xyz + i * 8)
            verts.append((x * MD3_XYZ_SCALE, y * MD3_XYZ_SCALE, z * MD3_XYZ_SCALE))
            normals.append(decode_normal(n))
        surfaces.append({"name": s_name.split(b"\0")[0].decode(), "shader": shader,
                         "num_frames": s_frames, "num_shaders": s_shaders,
                         "verts": verts, "normals": normals, "uvs": uvs, "tris": tris})
        off += o_end
    return {"name": name.split(b"\0")[0].decode(), "num_frames": n_frames,
            "tags": tags, "frames": frames, "surfaces": surfaces,
            "size": ofs_end}


def read_obj(path: Path | str, *, scale: float = 1.0,
             default_shader: str = "textures/pantheon/stone") -> list[Surface]:
    """Read a Wavefront OBJ into surfaces, one per material.

    This is the seam where Blender's output becomes a game asset. OBJ is used
    rather than a Blender-specific format on purpose: it is text, it diffs,
    and nothing about the pipeline depends on a Blender version.
    """
    positions: list[Vec3] = []
    uvs: list[Vec2] = []
    normals: list[Vec3] = []
    groups: dict[str, dict] = {}
    current = None

    def group(mat: str) -> dict:
        if mat not in groups:
            groups[mat] = {"verts": [], "normals": [], "uvs": [], "tris": [],
                           "index": {}}
        return groups[mat]

    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.split()
        if not parts:
            continue
        tag = parts[0]
        if tag == "v":
            positions.append(tuple(float(v) * scale for v in parts[1:4]))
        elif tag == "vt":
            uvs.append((float(parts[1]), float(parts[2])))
        elif tag == "vn":
            normals.append(tuple(float(v) for v in parts[1:4]))
        elif tag == "usemtl":
            current = group(parts[1])
        elif tag == "f":
            g = current if current is not None else group(default_shader)
            face = []
            for tok in parts[1:]:
                bits = (tok.split("/") + ["", ""])[:3]
                vi = int(bits[0]) - 1
                ti = int(bits[1]) - 1 if bits[1] else None
                ni = int(bits[2]) - 1 if bits[2] else None
                key = (vi, ti, ni)
                if key not in g["index"]:
                    g["index"][key] = len(g["verts"])
                    g["verts"].append(positions[vi])
                    g["uvs"].append(uvs[ti] if ti is not None and ti < len(uvs) else (0.0, 0.0))
                    g["normals"].append(normals[ni] if ni is not None and ni < len(normals)
                                        else (0.0, 0.0, 1.0))
                face.append(g["index"][key])
            for i in range(1, len(face) - 1):          # fan-triangulate
                g["tris"].append((face[0], face[i], face[i + 1]))

    out = []
    for mat, g in groups.items():
        # OBJ v is bottom-up, MD3/Quake t is top-down
        st = [(u, 1.0 - v) for u, v in g["uvs"]]
        out.append(Surface(name=mat.split("/")[-1][:31], shader=mat,
                           verts=g["verts"], normals=g["normals"], uvs=st,
                           tris=g["tris"]))
    return out
