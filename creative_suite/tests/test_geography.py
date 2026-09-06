"""One geography: deterministic regions, one API, and LOCAL_FRAME through it."""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from engine.pantheon import geography as G
from engine.pantheon import map_geography as mg
from engine.pantheon.map_spatial_index import MapSpatialIndex


def _two_floor_map(seed: int = 7) -> list[tuple[float, float, float]]:
    """Two rooms on a low floor joined by a thin corridor, and one room on
    an upper floor sharing the left room's footprint."""
    rnd = random.Random(seed)
    pts = []
    for _ in range(3000):
        pts.append((rnd.uniform(0, 600), rnd.uniform(0, 600), 24 + rnd.uniform(0, 20)))
    for _ in range(3000):
        pts.append((rnd.uniform(1200, 1800), rnd.uniform(0, 600), 24 + rnd.uniform(0, 20)))
    for _ in range(120):
        pts.append((rnd.uniform(600, 1200), rnd.uniform(250, 350), 24 + rnd.uniform(0, 20)))
    for _ in range(2500):
        pts.append((rnd.uniform(0, 600), rnd.uniform(0, 600), 520 + rnd.uniform(0, 20)))
    return pts


def test_height_layers_come_first_and_regions_are_deterministic():
    pts = _two_floor_map()
    layers, regions, lookup = mg.build_regions(pts, "synthetic")
    assert len(layers) == 2, [(la.z_lo, la.z_hi) for la in layers]
    assert len(regions) >= 3
    # the upper room shares XY with the lower-left room and must not merge
    idx = mg.MapIndex("synthetic", layers, regions, lookup)
    assert idx.region_at(300, 300, 30) != idx.region_at(300, 300, 530)
    # rebuild from the same points, and from the same points shuffled
    again = mg.build_regions(pts, "synthetic")
    shuffled = list(pts)
    random.Random(3).shuffle(shuffled)
    third = mg.build_regions(shuffled, "synthetic")
    for other in (again, third):
        assert [(la.z_lo, la.z_hi, la.samples) for la in other[0]] == \
               [(la.z_lo, la.z_hi, la.samples) for la in layers]
        assert [(r.region_id, r.layer, r.samples, r.cells) for r in other[1]] == \
               [(r.region_id, r.layer, r.samples, r.cells) for r in regions]
        assert other[2] == lookup


def test_the_facade_answers_from_regions_and_cells(tmp_path, monkeypatch):
    pts = _two_floor_map()
    layers, regions, lookup = mg.build_regions(pts, "synthetic")
    fake = mg.MapIndex("synthetic", layers, regions, lookup)
    monkeypatch.setattr(G.mc, "index_for", lambda m: fake if m == "synthetic" else None)
    monkeypatch.setattr(G.S, "map_spatial_dir", lambda: tmp_path)
    sp = MapSpatialIndex("synthetic")
    sp.add_walked_path([(x, 300.0, 30.0) for x in range(0, 600, 40)])
    sp.save(tmp_path / "synthetic.json")
    G.MapGeography.clear_cache()

    loc = G.location_for_event("synthetic", 300.0, 300.0, 30.0)
    assert loc is not None and loc.region_id.startswith("REGION_") and loc.walked
    upper = G.location_for_event("synthetic", 300.0, 300.0, 530.0)
    assert upper is not None and upper.region_id != loc.region_id and not upper.walked
    assert G.is_walked("synthetic", (300.0, 300.0, 30.0))
    assert not G.is_walked("synthetic", (1500.0, 300.0, 30.0))      # region only, no cell
    assert G.location_for_event("synthetic", 5000.0, 5000.0, 30.0) is None
    v = G.GeographyValidity("synthetic")
    assert v.is_walked((100.0, 300.0, 30.0)) and v.region((100.0, 300.0, 30.0))
    assert G.MapGeography.for_map("nowhere").region_for_position((0, 0, 0)) is None


def test_route_between_walks_observed_edges_only(monkeypatch):
    rows = [{"from_region": "REGION_01", "to_region": "REGION_02", "kind": "MOVE", "n": 40, "median_ms": 900},
            {"from_region": "REGION_02", "to_region": "REGION_03", "kind": "JUMP_PAD", "n": 12, "median_ms": 1400},
            {"from_region": "REGION_01", "to_region": "REGION_04", "kind": "MOVE", "n": 1, "median_ms": 500}]
    geo = G.MapGeography.__new__(G.MapGeography)
    geo.map = "synthetic"; geo.index = None; geo._spatial = None; geo._spatial_tried = True
    monkeypatch.setattr(G.MapGeography, "routes", lambda self: rows)
    path = geo.route_between("REGION_01", "REGION_03")
    assert [e["kind"] for e in path] == ["MOVE", "JUMP_PAD"]
    assert geo.route_between("REGION_01", "REGION_04") is None      # one crossing is not a route
    assert geo.route_between("REGION_03", "REGION_01") is None      # nobody went back that way


def test_teleport_geography_reads_only_confirmed_transits():
    src = Path(mg.__file__).read_text(encoding="utf-8")
    i = src.index("def teleport_links")
    block = src[i:i + 1600]
    assert "TELEPORT_PLAYER_CONFIRMED" in block
    assert "teleport_in" not in block
    # and the route walker never labels a teleport from anonymous events
    j = src.index("def routes_for_demo")
    assert "kind = JUMP_PAD if prev[2] == \"jump_pad\" else WALK" in src[j:j + 4000]
