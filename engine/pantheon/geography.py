"""Geography — the one door to a map's behavioural geography.

Two things were built about where players go, by two sessions:

    map_geography      (review)   height layers first, watershed regions
                                  inside a layer, a route graph of what
                                  players did, jump-pad arcs, confirmed
                                  teleport links. Deterministic region ids.
    map_spatial_index  (headless) fine 64-unit occupancy: walked cells,
                                  adjacency, landings, combat density, floors.

They answer different questions and both survive; this module is the single
API the prologue, the reviewer and the retargeter call, so neither of them
ever computes geography of its own again. Regions are the coarse, named,
stable answer ("REGION_04 on the UPPER layer"); cells are the fine answer
("can a body stand exactly here"). Nothing here reads a BSP: it is where
players actually went and fought, and it says so.

TELEPORTS come only from TELEPORT_PLAYER_CONFIRMED paired transits. Anonymous
`teleport_in` events name a machine, not a traveller; the review session
already caught the false routes that come from them, and they are not read
here.
"""
from __future__ import annotations

import sqlite3
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engine.pantheon import map_context as mc
from engine.pantheon import map_geography as mg
from engine.pantheon import store as S

Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class Location:
    map: str
    region_id: str
    layer: int
    layer_word: str
    walked: bool                  # a body has stood in this exact 64u cell

    def label(self) -> str:
        return f"{self.region_id} ({self.layer_word})"

    def as_dict(self) -> dict[str, Any]:
        return {"map": self.map, "region_id": self.region_id, "layer": self.layer,
                "layer_word": self.layer_word, "walked": self.walked}


class MapGeography:
    """One map: regions (map_geography) and cells (map_spatial_index)."""

    _cache: dict[str, "MapGeography"] = {}

    def __init__(self, map_name: str) -> None:
        self.map = map_name
        self.index = mc.index_for(map_name)            # regions, may be None
        self._spatial = None
        self._spatial_tried = False

    @classmethod
    def for_map(cls, map_name: str) -> "MapGeography":
        if map_name not in cls._cache:
            cls._cache[map_name] = cls(map_name)
        return cls._cache[map_name]

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()
        mc.clear_cache()

    # -- fine occupancy, loaded lazily and only if it was built ----------
    @property
    def spatial(self):
        if not self._spatial_tried:
            self._spatial_tried = True
            try:
                from engine.pantheon.map_spatial_index import MapSpatialIndex
                if self.map in MapSpatialIndex.available():
                    self._spatial = MapSpatialIndex.load(self.map)
            except Exception:
                self._spatial = None
        return self._spatial

    # -- the questions ---------------------------------------------------
    def region_for_position(self, pos: Vec3) -> str | None:
        if self.index is None:
            return None
        return self.index.region_at(pos[0], pos[1], pos[2])

    def location(self, pos: Vec3) -> Location | None:
        rid = self.region_for_position(pos)
        if rid is None:
            return None
        region = self.index.regions[rid]
        walked = bool(self.spatial and self.spatial.is_walked(pos))
        return Location(self.map, rid, region.layer,
                        mc.layer_word(self.index, region.layer), walked)

    def is_walked(self, pos: Vec3) -> bool:
        """Fine answer first; a region cell is the coarse fallback when no
        spatial index was built for this map."""
        if self.spatial is not None:
            return self.spatial.is_walked(pos)
        return self.region_for_position(pos) is not None

    def floors(self) -> list[tuple[float, float]]:
        if self.index is None:
            return []
        return [(la.z_lo, la.z_hi) for la in self.index.layers]

    def routes(self) -> list[dict[str, Any]]:
        with mg.conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT from_region, to_region, kind, n, median_ms FROM map_routes_v1 "
                "WHERE map=? ORDER BY n DESC", (self.map,))]

    def route_between(self, a: str, b: str, *, min_moves: int = 3) -> list[dict[str, Any]] | None:
        """The fewest observed hops from region a to region b, each hop a
        route real players took at least `min_moves` times. None when
        nobody ever connected them."""
        edges: dict[str, list[dict[str, Any]]] = {}
        for r in self.routes():
            if r["n"] >= min_moves:
                edges.setdefault(r["from_region"], []).append(r)
        prev: dict[str, tuple[str, dict[str, Any]] | None] = {a: None}
        q = deque([a])
        while q:
            cur = q.popleft()
            if cur == b:
                break
            for e in edges.get(cur, []):
                if e["to_region"] not in prev:
                    prev[e["to_region"]] = (cur, e)
                    q.append(e["to_region"])
        if b not in prev:
            return None
        path: list[dict[str, Any]] = []
        node = b
        while prev[node] is not None:
            frm, e = prev[node]
            path.append(e)
            node = frm
        return list(reversed(path))

    def teleport_links(self) -> list[dict[str, Any]]:
        with mg.conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT entry_region, exit_region, n FROM map_teleports_v1 WHERE map=?",
                (self.map,))]

    def jump_pad_arcs(self) -> list[dict[str, Any]]:
        with mg.conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT launch_region, land_region, n, median_air_ms FROM map_jump_pads_v1 "
                "WHERE map=? ORDER BY n DESC", (self.map,))]

    def landing_regions(self, n: int = 10) -> list[tuple[Vec3, int]]:
        return self.spatial.landing_regions(n) if self.spatial else []

    def summary(self) -> dict[str, Any]:
        return {"map": self.map,
                "regions": len(self.index.regions) if self.index else 0,
                "layers": len(self.index.layers) if self.index else 0,
                "routes": len(self.routes()) if self.index else 0,
                "teleport_links": len(self.teleport_links()) if self.index else 0,
                "jump_pad_arcs": len(self.jump_pad_arcs()) if self.index else 0,
                "spatial_cells": (len(self.spatial.layers["walked"]) if self.spatial else 0)}


# ── module-level API (what consumers import) ───────────────────────────────

def region_for_position(map_name: str, pos: Vec3) -> str | None:
    return MapGeography.for_map(map_name).region_for_position(pos)


def location_for_event(map_name: str, x: float, y: float, z: float) -> Location | None:
    return MapGeography.for_map(map_name).location((x, y, z))


def approach_for_occurrence(occurrence_id: int) -> dict[str, Any] | None:
    """LOCATION and APPROACH for one kill occurrence (review consumer)."""
    return mc.context_for_kill(occurrence_id)


def route_between(map_name: str, a: str, b: str) -> list[dict[str, Any]] | None:
    return MapGeography.for_map(map_name).route_between(a, b)


def is_walked(map_name: str, pos: Vec3) -> bool:
    return MapGeography.for_map(map_name).is_walked(pos)


def maps_available() -> list[str]:
    with mg.conn() as c:
        return [r[0] for r in c.execute("SELECT DISTINCT map FROM map_regions_v1 ORDER BY map")]


def coverage() -> dict[str, Any]:
    out = {}
    for m in maps_available():
        out[m] = MapGeography.for_map(m).summary()
    return out


# ── LOCAL_FRAME validity through the shared geography ──────────────────────

class GeographyValidity:
    """What `retarget.validate_retarget` consults for LOCAL_FRAME: a grounded
    sample is valid where a body was seen to stand (fine cells), or, when no
    spatial index exists for the map, inside a learned region."""

    def __init__(self, map_name: str) -> None:
        self.geo = MapGeography.for_map(map_name)

    def is_walked(self, pos: Vec3) -> bool:
        return self.geo.is_walked(pos)

    def region(self, pos: Vec3) -> str | None:
        return self.geo.region_for_position(pos)
