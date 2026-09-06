"""MapSpatialIndex — behavioural geography of a map, learned from real play.

NOT GEOMETRY. The BSP knows where the walls are; this knows where PLAYERS
were: the cells they walked, where fights happened, where jump pads threw
them and where they came down, where teleporters emptied out, which floors
exist and which cells connect to which because somebody ran between them.
A wall, a line of sight and a collision are BSP questions and stay so; this
index answers "is that a place a performance can be put".

SOURCES, all read-only, all already extracted from the demos:
  * frag_recognition.db::semantic_events_v1   events with XYZ (34.3M rows)
  * frag_recognition.db::teleport_transits_v1 confirmed teleports, out -> in
  * performance_index.db::actions             PerformanceTrace windows, whose
                                              grounded samples are the walked
                                              space and whose jump pads give
                                              launch -> landing pairs
  * frags_rebuilt.db::demos                   content_hash -> map

CELLS. The world is binned into 64-unit cubes. Counts per cell per layer;
adjacency between cells a player crossed in consecutive samples. Nothing is
smoothed: an empty cell is a cell nobody was seen in.

Names never enter this module: a position is three numbers and a client is a
slot.
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

Vec3 = tuple[float, float, float]
Cell = tuple[int, int, int]

from engine.pantheon import performance_index as PI
from engine.pantheon import store as S

FRAGS_DB = S.FRAGS_DB
RECOG_DB = S.RECOG_DB
CACHE = S.map_spatial_dir()

CELL = 64.0
FLOOR_BAND = 96.0            # one level, as NavigationTruth reads it
LAUNCH_VZ = 200.0

EVENT_LAYER = {
    "obituary": "death", "pain": "combat", "missile_hit": "combat",
    "railtrail": "combat", "gib_player": "death",
    "fire_weapon": "fire", "missile_miss": "impact",
    "jump_pad": "jump_pad_launch", "teleport_in": "teleport_in",
    "teleport_out": "teleport_out", "item_pickup": "pickup",
}
LAYERS = ("walked", "combat", "death", "fire", "impact", "jump_pad_launch",
          "jump_pad_landing", "teleport_in", "teleport_out", "pickup")


def cell_of(p: Vec3) -> Cell:
    return (math.floor(p[0] / CELL), math.floor(p[1] / CELL), math.floor(p[2] / CELL))


def cell_center(c: Cell) -> Vec3:
    return ((c[0] + 0.5) * CELL, (c[1] + 0.5) * CELL, (c[2] + 0.5) * CELL)


@dataclass
class MapSpatialIndex:
    map_name: str
    layers: dict[str, Counter] = field(default_factory=lambda: {k: Counter() for k in LAYERS})
    adjacency: Counter = field(default_factory=Counter)       # (cellA, cellB) -> crossings
    encounters: Counter = field(default_factory=Counter)      # (killer_cell, victim_cell) -> kills
    sources: dict = field(default_factory=dict)

    # -- queries -------------------------------------------------------
    def is_walked(self, pos: Vec3, *, radius: int = 1, min_count: int = 1) -> bool:
        """Was any cell within `radius` cells of `pos` walked at least
        `min_count` times? radius=1 tolerates a body standing at a cell edge."""
        c = cell_of(pos)
        w = self.layers["walked"]
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                for dz in range(-radius, radius + 1):
                    if w.get((c[0] + dx, c[1] + dy, c[2] + dz), 0) >= min_count:
                        return True
        return False

    def density(self, layer: str, pos: Vec3, *, radius: int = 1) -> int:
        c = cell_of(pos)
        L = self.layers[layer]
        return sum(L.get((c[0] + dx, c[1] + dy, c[2] + dz), 0)
                   for dx in range(-radius, radius + 1)
                   for dy in range(-radius, radius + 1)
                   for dz in range(-radius, radius + 1))

    def top_cells(self, layer: str, n: int = 10) -> list[tuple[Vec3, int]]:
        return [(cell_center(c), k) for c, k in self.layers[layer].most_common(n)]

    def landing_regions(self, n: int = 10) -> list[tuple[Vec3, int]]:
        return self.top_cells("jump_pad_landing", n)

    def floors(self) -> list[float]:
        """Distinct floor heights, low to high, from walked cell z bands."""
        zs = sorted(c[2] * CELL for c in self.layers["walked"])
        bands: list[list[float]] = []
        for z in zs:
            if not bands or z - bands[-1][0] > FLOOR_BAND:
                bands.append([z])
            else:
                bands[-1].append(z)
        # a floor is a band at least three walked cells wide; a lone cell is
        # a ledge someone stood on once
        return [b[0] for b in bands if len(b) >= 3]

    def connected(self, a: Vec3, b: Vec3) -> bool:
        """Did anyone cross directly between the two cells (either way)?"""
        ca, cb = cell_of(a), cell_of(b)
        return self.adjacency.get((ca, cb), 0) > 0 or self.adjacency.get((cb, ca), 0) > 0

    def nearest_walked(self, pos: Vec3, *, max_cells: int = 8) -> Vec3 | None:
        c = cell_of(pos)
        best = None
        for cell in self.layers["walked"]:
            d = max(abs(cell[0] - c[0]), abs(cell[1] - c[1]), abs(cell[2] - c[2]))
            if d <= max_cells and (best is None or d < best[0]):
                best = (d, cell)
        return cell_center(best[1]) if best else None

    def coverage(self) -> dict:
        return {"map": self.map_name,
                "cells": {k: len(v) for k, v in self.layers.items()},
                "samples": {k: sum(v.values()) for k, v in self.layers.items()},
                "adjacent_pairs": len(self.adjacency),
                "encounter_pairs": len(self.encounters),
                "floors": self.floors(),
                "sources": self.sources}

    # -- construction from samples (no database) ------------------------
    def add_walked_path(self, points: Sequence[Vec3]) -> None:
        prev: Cell | None = None
        for p in points:
            c = cell_of(p)
            self.layers["walked"][c] += 1
            if prev is not None and prev != c:
                self.adjacency[(prev, c)] += 1
            prev = c

    def add_event(self, kind: str, pos: Vec3) -> None:
        layer = EVENT_LAYER.get(kind)
        if layer:
            self.layers[layer][cell_of(pos)] += 1

    def add_landing(self, pos: Vec3) -> None:
        self.layers["jump_pad_landing"][cell_of(pos)] += 1

    def add_encounter(self, killer: Vec3, victim: Vec3) -> None:
        self.encounters[(cell_of(killer), cell_of(victim))] += 1

    # -- io: ONE store, map_geography.db, beside the regions -----------------
    # MapSpatialIndex (cells) and map_geography (regions over those cells)
    # are one authority with one database. JSON export remains for a human
    # to look at; nothing reads it back.
    SPATIAL_SCHEMA = """
    create table if not exists spatial_cells_v1 (
      map text not null, layer text not null, cx integer, cy integer, cz integer, n integer,
      primary key (map, layer, cx, cy, cz));
    create table if not exists spatial_adjacency_v1 (
      map text not null, ax integer, ay integer, az integer, bx integer, by integer, bz integer,
      n integer, primary key (map, ax, ay, az, bx, by, bz));
    create table if not exists spatial_encounters_v1 (
      map text not null, kx integer, ky integer, kz integer, vx integer, vy integer, vz integer,
      n integer, primary key (map, kx, ky, kz, vx, vy, vz));
    create table if not exists spatial_meta_v1 (
      map text primary key, version text, sources_json text, built_at real);
    """
    VERSION = "map-spatial-v2"

    def save(self, db: Path | None = None) -> Path:
        from engine.pantheon import map_geography as mg
        db = db or mg.GEO_DB
        with mg.conn(db) as c:
            c.executescript(self.SPATIAL_SCHEMA)
            for t in ("spatial_cells_v1", "spatial_adjacency_v1", "spatial_encounters_v1",
                      "spatial_meta_v1"):
                c.execute(f"delete from {t} where map=?", (self.map_name,))
            c.executemany("insert into spatial_cells_v1 values (?,?,?,?,?,?)",
                          [(self.map_name, layer, *cell, n)
                           for layer, cnt in self.layers.items() for cell, n in cnt.items()])
            c.executemany("insert into spatial_adjacency_v1 values (?,?,?,?,?,?,?,?)",
                          [(self.map_name, *a, *b, n) for (a, b), n in self.adjacency.items()])
            c.executemany("insert into spatial_encounters_v1 values (?,?,?,?,?,?,?,?)",
                          [(self.map_name, *k, *v, n) for (k, v), n in self.encounters.items()])
            c.execute("insert into spatial_meta_v1 values (?,?,?,?)",
                      (self.map_name, self.VERSION, json.dumps(self.sources), time.time()))
            c.commit()
        return db

    @classmethod
    def load(cls, map_name: str, db: Path | None = None) -> "MapSpatialIndex":
        from engine.pantheon import map_geography as mg
        db = db or mg.GEO_DB
        idx = cls(map_name)
        with mg.conn(db) as c:
            c.executescript(cls.SPATIAL_SCHEMA)
            meta = c.execute("select sources_json from spatial_meta_v1 where map=?",
                             (map_name,)).fetchone()
            if meta is None:
                raise KeyError(f"no spatial index for {map_name!r} in {db}")
            idx.sources = json.loads(meta[0] or "{}")
            for layer, cx, cy, cz, n in c.execute(
                    "select layer, cx, cy, cz, n from spatial_cells_v1 where map=?", (map_name,)):
                idx.layers.setdefault(layer, Counter())[(cx, cy, cz)] = n
            for ax, ay, az, bx, by, bz, n in c.execute(
                    "select ax, ay, az, bx, by, bz, n from spatial_adjacency_v1 where map=?",
                    (map_name,)):
                idx.adjacency[((ax, ay, az), (bx, by, bz))] = n
            for kx, ky, kz, vx, vy, vz, n in c.execute(
                    "select kx, ky, kz, vx, vy, vz, n from spatial_encounters_v1 where map=?",
                    (map_name,)):
                idx.encounters[((kx, ky, kz), (vx, vy, vz))] = n
        return idx

    @classmethod
    def available(cls, db: Path | None = None) -> list[str]:
        from engine.pantheon import map_geography as mg
        with mg.conn(db or mg.GEO_DB) as c:
            c.executescript(cls.SPATIAL_SCHEMA)
            return [r[0] for r in c.execute("select map from spatial_meta_v1 order by map")]

    def export_json(self, path: Path) -> Path:
        """A human-readable copy. Never read back."""
        path.parent.mkdir(parents=True, exist_ok=True)
        enc = lambda c: ",".join(map(str, c))
        path.write_text(json.dumps({
            "version": self.VERSION, "map": self.map_name, "cell": CELL,
            "layers": {k: {enc(c): n for c, n in v.items()} for k, v in self.layers.items()},
            "adjacency": {f"{enc(a)}|{enc(b)}": n for (a, b), n in self.adjacency.items()},
            "encounters": {f"{enc(a)}|{enc(b)}": n for (a, b), n in self.encounters.items()},
            "sources": self.sources, "coverage": self.coverage(),
        }), encoding="utf-8")
        return path

    @classmethod
    def for_map(cls, map_name: str, *, rebuild: bool = False, **kw) -> "MapSpatialIndex":
        if not rebuild and map_name in cls.available():
            return cls.load(map_name)
        idx = build(map_name, **kw)
        idx.save()
        return idx


# ── building from the databases ────────────────────────────────────────────

def map_hashes(map_name: str) -> list[str]:
    con = sqlite3.connect(f"file:{FRAGS_DB.as_posix()}?mode=ro", uri=True)
    rows = [r[0] for r in con.execute(
        "select content_hash from demos where map_name=? and content_hash is not null",
        (map_name,))]
    con.close()
    return rows


def build(map_name: str, *, max_traces: int = 20000, max_demos: int | None = None,
          per_demo_events: int = 3000, verbose: bool = False) -> MapSpatialIndex:
    t0 = time.time()
    idx = MapSpatialIndex(map_name)
    hashes = map_hashes(map_name)
    if max_demos:
        hashes = hashes[:max_demos]
    if not hashes:
        raise ValueError(f"no demos on map {map_name!r}")
    idx.sources["demos"] = len(hashes)

    # semantic events with XYZ
    n_ev = 0
    if RECOG_DB.exists():
        con = sqlite3.connect(f"file:{RECOG_DB.as_posix()}?mode=ro", uri=True)
        kinds = tuple(EVENT_LAYER)
        # ONE DEMO AT A TIME, never a type-filtered scan of the 34M-row
        # table: (content_hash, server_time_ms) is the only useful index
        # (the review geography found the same). Rows past `per_demo` are
        # strided, not truncated, so a match's whole length is sampled.
        for h in hashes:
            rows = con.execute(
                f"select type, x, y, z from semantic_events_v1 where content_hash=? "
                f"and type in ({','.join('?' * len(kinds))}) and x is not null "
                f"and y is not null and z is not null order by server_time_ms",
                (h, *kinds)).fetchall()
            stride = max(1, len(rows) // per_demo_events)
            for kind, x, y, z in rows[::stride]:
                idx.add_event(kind, (x, y, z))
                n_ev += 1
        # confirmed teleports: out and in ends
        for i in range(0, len(hashes), 400):
            chunk = hashes[i:i + 400]
            q = (f"select out_x,out_y,out_z,in_x,in_y,in_z from teleport_transits_v1 "
                 f"where content_hash in ({','.join('?' * len(chunk))}) "
                 f"and outcome like 'TELEPORT_PLAYER_CONFIRMED%'")
            for ox, oy, oz, ix, iy, iz in con.execute(q, chunk):
                if ox is not None:
                    idx.layers["teleport_out"][cell_of((ox, oy, oz))] += 1
                if ix is not None:
                    idx.layers["teleport_in"][cell_of((ix, iy, iz))] += 1
        con.close()
    idx.sources["semantic_events"] = n_ev
    if verbose:
        print(f"  events {n_ev} in {time.time() - t0:.1f}s", flush=True)

    # walked space, landings and encounters from the compact index: every
    # action row carries its grounded path as packed cells, its origin at
    # the anchor tick and, for a jump pad, where the body came down. No
    # trace is reconstructed here.
    n_tr = 0
    if S.index_db().exists():
        con = PI._ro()
        prefixes = {h[:16] for h in hashes}
        q = ("select kind, demo_hash, path_cells, origin_x, origin_y, origin_z, "
             "landing_x, landing_y, landing_z, victim from actions where map=? limit ?")
        for kind, dh, cells, ox, oy, oz, lx, ly, lz, victim in con.execute(q, (map_name, max_traces)):
            if dh not in prefixes:
                continue
            n_tr += 1
            path = PI.unpack_cells(cells)
            prev = None
            for c in path:
                idx.layers["walked"][c] += 1
                if prev is not None and prev != c:
                    idx.adjacency[(prev, c)] += 1
                prev = c
            if kind == "JUMP_PAD" and lx is not None:
                idx.add_landing((lx, ly, lz))
            if kind == "KILL" and ox is not None:
                idx.layers["combat"][cell_of((ox, oy, oz))] += 1
        con.close()
    idx.sources["traces"] = n_tr

    # the navigation routes already mined for this map, if cached
    nav_cache = Path(f"G:/QUAKE_LEGACY/creative_suite/generated/pantheon/nav_{map_name}.json")
    if nav_cache.exists():
        try:
            for r in json.loads(nav_cache.read_text(encoding="utf-8"))["routes"]:
                idx.add_walked_path([tuple(p) for p in r["points"]])
            idx.sources["navigation_routes"] = True
        except Exception:
            pass
    idx.sources["built_in_s"] = round(time.time() - t0, 1)
    if verbose:
        print(f"  traces {n_tr}, total {time.time() - t0:.1f}s", flush=True)
    return idx


def maps_by_demo_count(limit: int = 20) -> list[tuple[str, int]]:
    con = sqlite3.connect(f"file:{FRAGS_DB.as_posix()}?mode=ro", uri=True)
    rows = con.execute("select map_name, count(*) from demos where map_name is not null "
                       "group by 1 order by 2 desc limit ?", (limit,)).fetchall()
    con.close()
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("maps", nargs="*")
    ap.add_argument("--top", type=int, default=0, help="build the N most-played maps")
    ap.add_argument("--max-traces", type=int, default=4000)
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    maps = list(a.maps) or [m for m, _ in maps_by_demo_count(a.top or 5)]
    report = {}
    for m in maps:
        print(f"{m}:", flush=True)
        idx = MapSpatialIndex.for_map(m, rebuild=a.rebuild, max_traces=a.max_traces, verbose=True)
        cov = idx.coverage()
        report[m] = cov
        print(f"  cells {cov['cells']}  floors {len(cov['floors'])}  "
              f"adjacent {cov['adjacent_pairs']}  encounters {cov['encounter_pairs']}")
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "coverage.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    for m in maps:
        MapSpatialIndex.load(m).export_json(CACHE / f"{m}.json")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
