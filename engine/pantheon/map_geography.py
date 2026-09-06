"""Where the fighting actually happens, learned from ten years of play.

THE IDEA IS THE USER'S: "we should also review how to map the map
localisation and everything else while we datamine -- we can know everything
as we have thousands of records on only 10 maps." Six maps carry 96% of the
archive. Every position anyone stood in, fired from, died at, was launched
from or teleported into is already recorded. That is enough to learn a map's
real structure without ever opening one.

NO GEOMETRY IS READ. Not a BSP, not a texture, not an entity lump. A region
here is not a room; it is a volume of space that people repeatedly occupied,
fought in and moved between. That is a stronger claim for editing purposes
than architecture would be -- a corridor nobody uses is not a place, and a
sniper perch that is technically part of a bigger room is.

WHY XY CLUSTERING ALONE WOULD BE WRONG. Quake maps stack. On campgrounds the
RA room sits underneath a walkway that shares its whole footprint; flattened
to XY they are one blob, and every statement about either becomes a lie about
both. So height comes first: the Z histogram of a map has dense bands where
floors are and sparse gaps between them, and those gaps are the layer cuts.
Only inside one layer does XY clustering run. Two places at the same XY and
different heights can therefore never merge.

VERTICAL CONNECTION IS BEHAVIOURAL, NOT GEOMETRIC. Having separated the
layers, we do not reconnect them by guessing where the stairs are. We watch
people move: a client seen in region A and then in region B is an edge, and
a jump pad or a teleporter that carries them is that edge's kind. The route
graph is what players did, not what the level designer drew.

DETERMINISM IS A REQUIREMENT, NOT A NICETY. Region ids appear in the
reviewer's dossier and will appear in human notes. If a rebuild renumbered
them, every note written before it would silently start describing somewhere
else. So: fixed grid, integer arithmetic, components discovered in sorted
order, ids assigned by descending sample count with a coordinate tie-break.
Same events in, same ids out.
"""
from __future__ import annotations

import math
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
GEO_DB = REPO_ROOT / "creative_suite" / "database" / "map_geography.db"

GEOGRAPHY_VERSION = "map-geography-v1.0.0"

# ── the grid ────────────────────────────────────────────────────────────────
# Quake units. A player is 56 tall and about 30 wide; a rocket's kill radius
# is 120. A cell of 192 is therefore comfortably bigger than a fight and
# comfortably smaller than a room, which is the scale a region wants.
CELL_XY = 192

# Z histogram resolution. 32 units is a quarter of a player's jump, fine
# enough to see the gap between two floors and coarse enough not to shatter
# a ramp into bands.
Z_BIN = 32

# A layer boundary is a Z band this much emptier than the floors either side.
# Higher would merge stacked floors; lower would cut ramps in half.
VALLEY_RATIO = 0.35

# A layer must hold this share of a map's samples to be a layer at all.
# Below it, the band is noise (a lift in transit, a rocket-jump apex) and
# joins its neighbour.
MIN_LAYER_SHARE = 0.02

# A cell must be stood in this often to be part of a region. Removes the
# single stray sample from a rocket jump over the void.
MIN_CELL_SAMPLES = 8

# And a region must be more than one such cell.
MIN_REGION_CELLS = 2

# Position-bearing event types, and whether each says "somebody was here"
# (a body) or "something happened here" (a projectile, a trail).
BODY_TYPES = ("death", "gib_player", "fire_weapon", "jump", "jump_pad",
              "item_pickup", "change_weapon", "noammo", "teleport_in",
              "teleport_out")
COMBAT_TYPES = ("death", "gib_player")

# Event types sampled to DISCOVER regions. change_weapon alone is two million
# rows and adds nothing a fire_weapon does not; the discovery set is chosen
# for spatial coverage, not volume.
DISCOVERY_TYPES = ("death", "gib_player", "fire_weapon", "jump", "jump_pad",
                   "item_pickup", "teleport_in", "teleport_out")

# Ceiling on discovery samples per map. Regions converge long before this;
# the cap keeps a rebuild to minutes rather than an evening.
MAX_DISCOVERY_SAMPLES = 1_500_000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS map_layers_v1 (
    map        TEXT NOT NULL,
    layer      INTEGER NOT NULL,
    z_lo       REAL NOT NULL,
    z_hi       REAL NOT NULL,
    samples    INTEGER NOT NULL,
    version    TEXT NOT NULL,
    PRIMARY KEY (map, layer)
);
CREATE TABLE IF NOT EXISTS map_regions_v1 (
    map        TEXT NOT NULL,
    region_id  TEXT NOT NULL,
    layer      INTEGER NOT NULL,
    samples    INTEGER NOT NULL,
    cells      INTEGER NOT NULL,
    x_lo REAL, x_hi REAL, y_lo REAL, y_hi REAL, z_lo REAL, z_hi REAL,
    cx_centre REAL, cy_centre REAL, cz_centre REAL,
    movement_samples INTEGER NOT NULL DEFAULT 0,
    combat_samples   INTEGER NOT NULL DEFAULT 0,
    version    TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    PRIMARY KEY (map, region_id)
);
CREATE TABLE IF NOT EXISTS map_region_cells_v1 (
    map       TEXT NOT NULL,
    layer     INTEGER NOT NULL,
    cx        INTEGER NOT NULL,
    cy        INTEGER NOT NULL,
    region_id TEXT NOT NULL,
    PRIMARY KEY (map, layer, cx, cy)
);
CREATE TABLE IF NOT EXISTS map_routes_v1 (
    map        TEXT NOT NULL,
    from_region TEXT NOT NULL,
    to_region   TEXT NOT NULL,
    kind        TEXT NOT NULL,
    n           INTEGER NOT NULL,
    median_ms   INTEGER,
    PRIMARY KEY (map, from_region, to_region, kind)
);
CREATE TABLE IF NOT EXISTS map_region_combat_v1 (
    map          TEXT NOT NULL,
    region_id    TEXT NOT NULL,
    deaths       INTEGER NOT NULL DEFAULT 0,
    shots        INTEGER NOT NULL DEFAULT 0,
    weapons_json TEXT,
    PRIMARY KEY (map, region_id)
);
CREATE TABLE IF NOT EXISTS map_jump_pads_v1 (
    map           TEXT NOT NULL,
    launch_region TEXT NOT NULL,
    land_region   TEXT,
    n             INTEGER NOT NULL,
    median_air_ms INTEGER,
    PRIMARY KEY (map, launch_region, land_region)
);
CREATE TABLE IF NOT EXISTS map_teleports_v1 (
    map           TEXT NOT NULL,
    entry_region  TEXT NOT NULL,
    exit_region   TEXT NOT NULL,
    n             INTEGER NOT NULL,
    PRIMARY KEY (map, entry_region, exit_region)
);
CREATE INDEX IF NOT EXISTS ix_geo_region ON map_region_cells_v1(map, region_id);
"""


# ── data classes ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Layer:
    map: str
    layer: int
    z_lo: float
    z_hi: float
    samples: int


@dataclass(frozen=True)
class Region:
    map: str
    region_id: str
    layer: int
    samples: int
    cells: int
    bounds: tuple[float, float, float, float, float, float]
    centre: tuple[float, float, float]
    movement_samples: int = 0
    combat_samples: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"map": self.map, "region_id": self.region_id,
                "layer": self.layer, "samples": self.samples,
                "cells": self.cells, "centre": list(self.centre),
                "bounds": list(self.bounds),
                "movement_samples": self.movement_samples,
                "combat_samples": self.combat_samples}


# ── connections ─────────────────────────────────────────────────────────────

def conn(db: Path = GEO_DB) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(db, timeout=180)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(_SCHEMA)
    return c


def _ro(db: Path) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=180)
    c.row_factory = sqlite3.Row
    return c


# ── which demos belong to which map ─────────────────────────────────────────

def map_of_demos(db: Path = RECOG_DB) -> dict[str, str]:
    """content_hash -> map. The demo header does not carry it; the kill
    events do, and every demo we care about has kills."""
    with _ro(db) as c:
        return {r["content_hash"]: r["map"] for r in c.execute(
            "SELECT content_hash, MIN(map) map FROM kill_events_v1 "
            "WHERE map IS NOT NULL GROUP BY content_hash")}


def dominant_maps(db: Path = RECOG_DB, min_demos: int = 20) -> list[str]:
    """Maps with enough recordings to learn a structure from.

    Below a couple of dozen demos the samples cluster around whatever those
    few matches happened to do, and a region would describe one evening
    rather than a map.
    """
    with _ro(db) as c:
        return [r["map"] for r in c.execute(
            "SELECT map, COUNT(DISTINCT content_hash) d FROM kill_events_v1 "
            "WHERE map IS NOT NULL GROUP BY map HAVING d >= ? "
            "ORDER BY d DESC, map", (min_demos,))]


# ── layers: height comes first ──────────────────────────────────────────────

def z_histogram(zs: Iterable[float]) -> dict[int, int]:
    h: dict[int, int] = defaultdict(int)
    for z in zs:
        h[int(math.floor(z / Z_BIN))] += 1
    return dict(h)


def layers_from_histogram(hist: dict[int, int], map_name: str = "") \
        -> list[Layer]:
    """Cut the map into floors at the empty bands between them.

    A "valley" is a bin markedly emptier than the busiest bin on each side.
    Real floors are separated by air nobody stands in for long; a ramp shows
    as a shallow dip and is deliberately not deep enough to cut.
    """
    if not hist:
        return []
    lo, hi = min(hist), max(hist)
    counts = [hist.get(b, 0) for b in range(lo, hi + 1)]
    total = sum(counts)
    if total == 0:
        return []

    peak_left = 0
    cuts: list[int] = []
    for i, n in enumerate(counts):
        if i == 0 or i == len(counts) - 1:
            peak_left = max(peak_left, n)
            continue
        peak_right = max(counts[i + 1:]) if i + 1 < len(counts) else 0
        floor_ref = min(peak_left, peak_right)
        if floor_ref > 0 and n <= floor_ref * VALLEY_RATIO:
            # Only cut once per valley: extend through the whole dip.
            if not cuts or i - cuts[-1] > 1:
                cuts.append(i)
            else:
                cuts[-1] = i
        peak_left = max(peak_left, n)

    edges = [0] + [c + 1 for c in cuts] + [len(counts)]
    raw: list[tuple[int, int, int]] = []
    for a, b in zip(edges, edges[1:]):
        if b <= a:
            continue
        n = sum(counts[a:b])
        if n:
            raw.append((a, b, n))

    # Merge layers too thin to mean anything into their larger neighbour.
    merged = True
    while merged and len(raw) > 1:
        merged = False
        for i, (a, b, n) in enumerate(raw):
            if n / total >= MIN_LAYER_SHARE:
                continue
            j = i - 1 if i > 0 and (i == len(raw) - 1
                                    or raw[i - 1][2] >= raw[i + 1][2]) else i + 1
            lo_i, hi_i = min(i, j), max(i, j)
            a2, b2 = raw[lo_i][0], raw[hi_i][1]
            raw = (raw[:lo_i] + [(a2, b2, raw[lo_i][2] + raw[hi_i][2])]
                   + raw[hi_i + 1:])
            merged = True
            break

    return [Layer(map_name, i, (lo + a) * Z_BIN, (lo + b) * Z_BIN, n)
            for i, (a, b, n) in enumerate(raw)]


def layer_of(layers: list[Layer], z: float) -> int:
    """Which floor is this height on? Clamped, never unknown -- a point above
    the top layer belongs to the top layer, which is what a rocket-jump apex
    over the highest walkway actually means."""
    if not layers:
        return 0
    for lay in layers:
        if z < lay.z_hi:
            return lay.layer
    return layers[-1].layer


# ── regions: connected components inside one layer ──────────────────────────

def _watershed(density: dict[tuple[int, int], int]) -> dict[tuple[int, int],
                                                            int]:
    """Split one layer into places, at the thin bits between them.

    WHY NOT CONNECTED COMPONENTS. Tried first, and it produced exactly one
    region per floor: a Quake map is walkable end to end, so every occupied
    cell on a level touches every other and the whole storey comes back as
    one blob. "REGION_01, the upper floor" localises nothing.

    What separates two places is not empty space but a THIN place -- a
    doorway, a ramp, a corridor -- where far fewer people stand than in the
    rooms either side. So the density field is flooded from its peaks
    downward: every local maximum starts a basin, cells join the basin of
    their densest labelled neighbour, and where two basins meet is a
    watershed line. Rooms become regions and the corridor between them
    becomes the border.

    Basins that are not really separate are merged back by PROMINENCE: if
    the saddle where a basin meets its neighbour is nearly as busy as the
    basin's own peak, there was no chokepoint, just a bumpy plateau.

    Deterministic throughout: cells are processed in descending density with
    a coordinate tie-break, so the same counts always give the same labels.
    """
    order = sorted(density.items(), key=lambda kv: (-kv[1], kv[0]))
    label: dict[tuple[int, int], int] = {}
    peak: dict[int, int] = {}
    # Highest saddle at which basin A has so far touched any other basin.
    saddle: dict[tuple[int, int], int] = {}
    nxt = 0

    for (cx, cy), d in order:
        neigh = [label[n] for n in ((cx + 1, cy), (cx - 1, cy),
                                    (cx, cy + 1), (cx, cy - 1))
                 if n in label]
        distinct = sorted(set(neigh))
        if not distinct:
            nxt += 1
            label[(cx, cy)] = nxt
            peak[nxt] = d
            continue
        # Join the basin whose peak is highest -- deterministic, and it keeps
        # a cell with the room it most plausibly belongs to.
        home = max(distinct, key=lambda g: (peak[g], -g))
        label[(cx, cy)] = home
        for other in distinct:
            if other == home:
                continue
            key = (min(home, other), max(home, other))
            if d > saddle.get(key, -1):
                saddle[key] = d

    return _merge_shallow(label, peak, saddle)


# A basin whose saddle sits above this fraction of its own peak was never a
# separate place: the two rooms are one room with a dip in the middle.
PROMINENCE = 0.55


def _merge_shallow(label: dict[tuple[int, int], int], peak: dict[int, int],
                   saddle: dict[tuple[int, int], int]) \
        -> dict[tuple[int, int], int]:
    parent = {g: g for g in peak}

    def find(g: int) -> int:
        while parent[g] != g:
            parent[g] = parent[parent[g]]
            g = parent[g]
        return g

    # Shallowest basins first: merging one can make another shallower still,
    # and doing the obvious ones first keeps the result order-independent.
    for (a, b), s in sorted(saddle.items(), key=lambda kv: (-kv[1], kv[0])):
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        weak, strong = ((ra, rb) if peak[ra] < peak[rb] else (rb, ra))
        if peak[weak] and s >= peak[weak] * PROMINENCE:
            parent[weak] = strong
    return {c: find(g) for c, g in label.items()}


def build_regions(points: list[tuple[float, float, float]], map_name: str,
                  combat_flags: list[bool] | None = None) \
        -> tuple[list[Layer], list[Region], dict[tuple[int, int, int], str]]:
    """Layers, regions and the cell lookup, from one map's position samples.

    Returns (layers, regions, {(layer, cx, cy): region_id}).
    """
    layers = layers_from_histogram(z_histogram(p[2] for p in points),
                                   map_name)
    if not layers:
        return [], [], {}

    cell_n: dict[tuple[int, int, int], int] = defaultdict(int)
    cell_combat: dict[tuple[int, int, int], int] = defaultdict(int)
    cell_xyz: dict[tuple[int, int, int], list[float]] = {}
    for i, (x, y, z) in enumerate(points):
        lay = layer_of(layers, z)
        key = (lay, int(math.floor(x / CELL_XY)), int(math.floor(y / CELL_XY)))
        cell_n[key] += 1
        if combat_flags is not None and combat_flags[i]:
            cell_combat[key] += 1
        acc = cell_xyz.get(key)
        if acc is None:
            cell_xyz[key] = [x, x, y, y, z, z]
        else:
            acc[0] = min(acc[0], x); acc[1] = max(acc[1], x)
            acc[2] = min(acc[2], y); acc[3] = max(acc[3], y)
            acc[4] = min(acc[4], z); acc[5] = max(acc[5], z)

    candidates: list[tuple[int, int, list[tuple[int, int]]]] = []
    for lay in layers:
        dens = {(cx, cy): n for (l, cx, cy), n in cell_n.items()
                if l == lay.layer and n >= MIN_CELL_SAMPLES}
        if not dens:
            continue
        basins: dict[int, list[tuple[int, int]]] = {}
        for cell, g in _watershed(dens).items():
            basins.setdefault(g, []).append(cell)
        for g in sorted(basins):
            comp = sorted(basins[g])
            if len(comp) >= MIN_REGION_CELLS:
                candidates.append((lay.layer, sum(
                    cell_n[(lay.layer, cx, cy)] for cx, cy in comp), comp))

    # THE ID RULE. Biggest first, ties broken by layer then by the component's
    # lowest cell. Nothing here depends on dict or set iteration order, so the
    # same events always produce the same REGION_NN.
    candidates.sort(key=lambda t: (-t[1], t[0], t[2][0]))

    regions: list[Region] = []
    lookup: dict[tuple[int, int, int], str] = {}
    for i, (lay_no, n, comp) in enumerate(candidates, start=1):
        rid = f"REGION_{i:02d}"
        xs_lo = min(cell_xyz[(lay_no, cx, cy)][0] for cx, cy in comp)
        xs_hi = max(cell_xyz[(lay_no, cx, cy)][1] for cx, cy in comp)
        ys_lo = min(cell_xyz[(lay_no, cx, cy)][2] for cx, cy in comp)
        ys_hi = max(cell_xyz[(lay_no, cx, cy)][3] for cx, cy in comp)
        zs_lo = min(cell_xyz[(lay_no, cx, cy)][4] for cx, cy in comp)
        zs_hi = max(cell_xyz[(lay_no, cx, cy)][5] for cx, cy in comp)
        combat = sum(cell_combat.get((lay_no, cx, cy), 0) for cx, cy in comp)
        regions.append(Region(
            map_name, rid, lay_no, n, len(comp),
            (xs_lo, xs_hi, ys_lo, ys_hi, zs_lo, zs_hi),
            ((xs_lo + xs_hi) / 2, (ys_lo + ys_hi) / 2, (zs_lo + zs_hi) / 2),
            movement_samples=n - combat, combat_samples=combat))
        for cx, cy in comp:
            lookup[(lay_no, cx, cy)] = rid
    return layers, regions, lookup


# ── point -> region, the operation everything else is built on ──────────────

class MapIndex:
    """One map's geography, ready to answer `region_at(x, y, z)`."""

    def __init__(self, map_name: str, layers: list[Layer],
                 regions: list[Region],
                 lookup: dict[tuple[int, int, int], str]) -> None:
        self.map = map_name
        self.layers = layers
        self.regions = {r.region_id: r for r in regions}
        self._lookup = lookup

    def region_at(self, x: float, y: float, z: float) -> str | None:
        """None is an honest answer. A point in a cell nobody occupied often
        enough is nowhere in particular, and saying so beats snapping it to
        whichever region happens to be nearest."""
        lay = layer_of(self.layers, z)
        return self._lookup.get(
            (lay, int(math.floor(x / CELL_XY)), int(math.floor(y / CELL_XY))))

    def __len__(self) -> int:
        return len(self.regions)


def load_index(map_name: str, db: Path = GEO_DB) -> MapIndex | None:
    with conn(db) as c:
        layers = [Layer(map_name, r["layer"], r["z_lo"], r["z_hi"],
                        r["samples"]) for r in c.execute(
            "SELECT * FROM map_layers_v1 WHERE map=? ORDER BY layer",
            (map_name,))]
        if not layers:
            return None
        regions = [Region(
            map_name, r["region_id"], r["layer"], r["samples"], r["cells"],
            (r["x_lo"], r["x_hi"], r["y_lo"], r["y_hi"], r["z_lo"], r["z_hi"]),
            (r["cx_centre"], r["cy_centre"], r["cz_centre"]),
            r["movement_samples"], r["combat_samples"])
            for r in c.execute(
                "SELECT * FROM map_regions_v1 WHERE map=?", (map_name,))]
        lookup = {(r["layer"], r["cx"], r["cy"]): r["region_id"]
                  for r in c.execute(
                      "SELECT * FROM map_region_cells_v1 WHERE map=?",
                      (map_name,))}
    return MapIndex(map_name, layers, regions, lookup)


# ── reading the corpus ──────────────────────────────────────────────────────


# ── reading the corpus ──────────────────────────────────────────────────────
#
# EVERYTHING IS DRIVEN PER DEMO, never per event type. `semantic_events_v1`
# holds 34.3 million rows and its only useful index is (content_hash,
# server_time_ms); a query filtered by type alone scans a partition of up to
# 15.8 million rows and then throws away every demo of a different map. Asked
# one demo at a time it reads a few thousand rows and uses the index.

# Per-demo ceiling on discovery samples. A cap on the MAP would let the first
# few matches define its whole shape; a cap per demo spreads the sample over
# every recording instead, which is the point of having a thousand of them.
PER_DEMO_DISCOVERY = 4000


def demo_positions(content_hash: str, types: tuple[str, ...],
                   db: sqlite3.Connection) -> list[tuple[int, int, float,
                                                         float, float, str]]:
    """(time, client, x, y, z, type) for one demo, ordered by time."""
    qs = ",".join("?" * len(types))
    sql = ("SELECT server_time_ms, client_num, x, y, z, type "
           "FROM semantic_events_v1 WHERE content_hash=? "
           "AND type IN (" + qs + ") AND x IS NOT NULL AND y IS NOT NULL "
           "AND z IS NOT NULL ORDER BY server_time_ms")
    return [(int(r["server_time_ms"]),
             -1 if r["client_num"] is None else int(r["client_num"]),
             r["x"], r["y"], r["z"], r["type"])
            for r in db.execute(sql, (content_hash, *types))]


def discovery_points(hashes: list[str], db: Path = RECOG_DB,
                     per_demo: int = PER_DEMO_DISCOVERY) \
        -> tuple[list[tuple[float, float, float]], list[bool]]:
    """Positions to learn one map's shape from, and which were a death.

    Sub-sampled with a fixed stride rather than a head slice: the first four
    thousand events of a match are its first two minutes, and a map is not
    shaped like its opening rounds.
    """
    pts: list[tuple[float, float, float]] = []
    combat: list[bool] = []
    with _ro(db) as c:
        for h in sorted(hashes):
            rows = demo_positions(h, DISCOVERY_TYPES, c)
            stride = max(1, len(rows) // per_demo) if per_demo else 1
            for r in rows[::stride]:
                pts.append((r[2], r[3], r[4]))
                combat.append(r[5] in COMBAT_TYPES)
    return pts, combat


def _median(xs: list[int]) -> int | None:
    if not xs:
        return None
    s = sorted(xs)
    return s[len(s) // 2]


# ── the route graph: what people actually did ───────────────────────────────

# A move quicker than this is two event types firing on one position, not
# travel between two places.
MIN_MOVE_MS = 150
# A gap longer than this is not one journey: the player died, or the demo
# skipped. Joining across it would invent a route nobody took.
MAX_MOVE_MS = 12_000

WALK = "MOVE"
JUMP_PAD = "JUMP_PAD"
TELEPORT = "TELEPORT"


def routes_for_demo(content_hash: str, index: "MapIndex",
                    db: sqlite3.Connection):
    """Region transitions in one demo: routes, and jump-pad arcs.

    Returns (routes, pads) where routes maps (from, to, kind) to the travel
    times observed and pads maps (launch, landing) to airtimes.
    """
    routes: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    pads: dict[tuple[str, str], list[int]] = defaultdict(list)

    rows = demo_positions(content_hash, BODY_TYPES, db)
    by_client: dict[int, list[tuple[int, float, float, float, str]]] \
        = defaultdict(list)
    for t, cl, x, y, z, ty in rows:
        if cl >= 0:
            by_client[cl].append((t, x, y, z, ty))

    for _cl, track in sorted(by_client.items()):
        prev: tuple[int, str, str] | None = None    # (time, region, type)
        launch: tuple[int, str] | None = None       # pending jump pad
        for t, x, y, z, ty in track:
            reg = index.region_at(x, y, z)
            if reg is None:
                continue
            if ty == "jump_pad":
                launch = (t, reg)
            elif launch is not None:
                air = t - launch[0]
                if air > MAX_MOVE_MS:
                    launch = None
                elif air > 0 and reg != launch[1]:
                    pads[(launch[1], reg)].append(air)
                    launch = None
            if prev is not None:
                dt = t - prev[0]
                if reg != prev[1] and MIN_MOVE_MS <= dt <= MAX_MOVE_MS:
                    # NEVER labelled TELEPORT here. `teleport_in` and
                    # `teleport_out` carry no client number, so a transit
                    # cannot be attributed to the person walking this track;
                    # any TELEPORT edge derived from it would be an artifact
                    # of two unrelated positions landing next to each other.
                    # Teleport geography comes from the validated pairs in
                    # teleport_transits_v1 and from nowhere else.
                    kind = JUMP_PAD if prev[2] == "jump_pad" else WALK
                    routes[(prev[1], reg, kind)].append(dt)
            prev = (t, reg, ty)
    return routes, pads


def teleport_links(hashes: list[str], index: "MapIndex",
                   db: Path = RECOG_DB) -> dict[tuple[str, str], int]:
    """Entry -> exit regions, from the already-validated paired transits.

    The teleport backfill is NOT rerun; `teleport_transits_v1` is read as it
    stands, and only CONFIRMED pairs are used -- an AMBIGUOUS transit is a
    guess about which teleporter fired, and a guess is not geography.
    """
    out: dict[tuple[str, str], int] = defaultdict(int)
    if not hashes:
        return {}
    with _ro(db) as c:
        for h in sorted(hashes):
            for r in c.execute(
                    "SELECT out_x, out_y, out_z, in_x, in_y, in_z FROM "
                    "teleport_transits_v1 WHERE content_hash=? AND "
                    "outcome='TELEPORT_PLAYER_CONFIRMED' AND "
                    "out_x IS NOT NULL AND in_x IS NOT NULL", (h,)):
                a = index.region_at(r["out_x"], r["out_y"], r["out_z"])
                b = index.region_at(r["in_x"], r["in_y"], r["in_z"])
                if a and b:
                    out[(a, b)] += 1
    return dict(out)


# ── combat geography ────────────────────────────────────────────────────────

def combat_for_map(hashes: list[str], index: "MapIndex",
                   db: Path = RECOG_DB) -> dict[str, dict[str, Any]]:
    """Deaths, shots and the weapon mix, per region."""
    stats: dict[str, dict[str, Any]] = {}
    if not hashes:
        return {}
    with _ro(db) as c:
        for h in sorted(hashes):
            for r in c.execute(
                    "SELECT type, weapon, x, y, z FROM semantic_events_v1 "
                    "WHERE content_hash=? AND type IN "
                    "('death','gib_player','fire_weapon') "
                    "AND x IS NOT NULL AND y IS NOT NULL AND z IS NOT NULL",
                    (h,)):
                reg = index.region_at(r["x"], r["y"], r["z"])
                if reg is None:
                    continue
                s = stats.setdefault(
                    reg, {"deaths": 0, "shots": 0, "weapons": {}})
                if r["type"] == "fire_weapon":
                    s["shots"] += 1
                    if r["weapon"] is not None:
                        w = int(r["weapon"])
                        s["weapons"][w] = s["weapons"].get(w, 0) + 1
                else:
                    s["deaths"] += 1
    return stats


# ── the build ───────────────────────────────────────────────────────────────

def build_map(map_name: str, hashes: list[str], recog: Path = RECOG_DB,
              geo: Path = GEO_DB, with_routes: bool = True) -> dict[str, Any]:
    """Learn one map and persist it. Reads demo records; opens nothing."""
    import json

    pts, combat_flags = discovery_points(hashes, recog)
    layers, regions, lookup = build_regions(pts, map_name, combat_flags)
    if not regions:
        return {"map": map_name, "demos": len(hashes), "samples": len(pts),
                "regions": 0, "reason": "no stable clusters"}

    index = MapIndex(map_name, layers, regions, lookup)

    routes: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    pads: dict[tuple[str, str], list[int]] = defaultdict(list)
    if with_routes:
        with _ro(recog) as c:
            for h in sorted(hashes):
                r_, p_ = routes_for_demo(h, index, c)
                for k, v in r_.items():
                    routes[k].extend(v)
                for k, v in p_.items():
                    pads[k].extend(v)
    tele = teleport_links(hashes, index, recog) if with_routes else {}
    combat = combat_for_map(hashes, index, recog) if with_routes else {}

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with conn(geo) as c:
        for table in ("map_layers_v1", "map_regions_v1", "map_region_cells_v1",
                      "map_routes_v1", "map_region_combat_v1",
                      "map_jump_pads_v1", "map_teleports_v1"):
            c.execute("DELETE FROM " + table + " WHERE map=?", (map_name,))
        c.executemany(
            "INSERT INTO map_layers_v1(map,layer,z_lo,z_hi,samples,version) "
            "VALUES(?,?,?,?,?,?)",
            [(map_name, la.layer, la.z_lo, la.z_hi, la.samples,
              GEOGRAPHY_VERSION) for la in layers])
        c.executemany(
            "INSERT INTO map_regions_v1(map,region_id,layer,samples,cells,"
            "x_lo,x_hi,y_lo,y_hi,z_lo,z_hi,cx_centre,cy_centre,cz_centre,"
            "movement_samples,combat_samples,version,computed_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [(map_name, r.region_id, r.layer, r.samples, r.cells, *r.bounds,
              *r.centre, r.movement_samples, r.combat_samples,
              GEOGRAPHY_VERSION, now) for r in regions])
        c.executemany(
            "INSERT INTO map_region_cells_v1(map,layer,cx,cy,region_id) "
            "VALUES(?,?,?,?,?)",
            [(map_name, lay, cx, cy, rid)
             for (lay, cx, cy), rid in sorted(lookup.items())])
        c.executemany(
            "INSERT INTO map_routes_v1(map,from_region,to_region,kind,n,"
            "median_ms) VALUES(?,?,?,?,?,?)",
            [(map_name, a, b, k, len(v), _median(v))
             for (a, b, k), v in sorted(routes.items())])
        c.executemany(
            "INSERT INTO map_jump_pads_v1(map,launch_region,land_region,n,"
            "median_air_ms) VALUES(?,?,?,?,?)",
            [(map_name, a, b, len(v), _median(v))
             for (a, b), v in sorted(pads.items())])
        c.executemany(
            "INSERT INTO map_teleports_v1(map,entry_region,exit_region,n) "
            "VALUES(?,?,?,?)",
            [(map_name, a, b, n) for (a, b), n in sorted(tele.items())])
        c.executemany(
            "INSERT INTO map_region_combat_v1(map,region_id,deaths,shots,"
            "weapons_json) VALUES(?,?,?,?,?)",
            [(map_name, rid, v["deaths"], v["shots"],
              json.dumps({str(k): n for k, n in sorted(v["weapons"].items())}))
             for rid, v in sorted(combat.items())])
        c.commit()

    return {"map": map_name, "demos": len(hashes), "samples": len(pts),
            "layers": len(layers), "regions": len(regions),
            "routes": len(routes), "jump_pad_arcs": len(pads),
            "teleport_links": len(tele),
            "regions_with_combat": len(combat)}


def build_all(recog: Path = RECOG_DB, geo: Path = GEO_DB,
              maps: list[str] | None = None, min_demos: int = 20,
              with_routes: bool = True) -> list[dict[str, Any]]:
    demo_map = map_of_demos(recog)
    wanted = maps or dominant_maps(recog, min_demos)
    by_map: dict[str, list[str]] = defaultdict(list)
    for h, m in demo_map.items():
        if m in wanted:
            by_map[m].append(h)
    return [build_map(m, by_map.get(m, []), recog, geo, with_routes)
            for m in wanted]
