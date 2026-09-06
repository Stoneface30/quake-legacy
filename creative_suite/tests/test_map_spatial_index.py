"""MapSpatialIndex: behavioural geography, built from samples, no database."""
from __future__ import annotations

from creative_suite.tests.pantheon_fixtures import jumppad_rocket_trace
from engine.pantheon.map_spatial_index import CELL, MapSpatialIndex, cell_of
from engine.pantheon.retarget import Retarget, validate_retarget


def _index() -> MapSpatialIndex:
    idx = MapSpatialIndex("campgrounds")
    idx.add_walked_path([(x, 0.0, 24.0) for x in range(0, 2000, 40)])          # a corridor
    idx.add_walked_path([(x, 0.0, 24.0 + 512.0) for x in range(0, 2000, 40)])  # a floor above
    for _ in range(5):
        idx.add_event("obituary", (640.0, 0.0, 24.0))
        idx.add_event("jump_pad", (100.0, 0.0, 24.0))
    idx.add_landing((900.0, 0.0, 536.0))
    idx.add_encounter((100.0, 0.0, 24.0), (640.0, 0.0, 24.0))
    return idx


def test_walked_cells_floors_and_connectivity():
    idx = _index()
    assert idx.is_walked((1000.0, 10.0, 30.0))
    assert not idx.is_walked((1000.0, 900.0, 30.0))
    assert idx.floors() == [0.0, 512.0]
    assert idx.connected((0.0, 0.0, 24.0), (64.0, 0.0, 24.0))
    assert not idx.connected((0.0, 0.0, 24.0), (0.0, 0.0, 536.0))     # nobody crossed floors
    assert idx.density("death", (640.0, 0.0, 24.0)) == 5
    assert idx.landing_regions(1)[0][1] == 1
    assert idx.coverage()["cells"]["jump_pad_launch"] == 1


def test_round_trips_through_the_geography_store(tmp_path):
    idx = _index()
    db = idx.save(tmp_path / "map_geography.db")
    assert MapSpatialIndex.available(db) == ["campgrounds"]
    back = MapSpatialIndex.load("campgrounds", db)
    assert back.layers["walked"] == idx.layers["walked"]
    assert back.adjacency == idx.adjacency and back.encounters == idx.encounters
    assert back.coverage()["floors"] == idx.coverage()["floors"]


def test_local_frame_retarget_is_refused_off_the_walked_space():
    idx = _index()
    tr = jumppad_rocket_trace()
    into_corridor = Retarget.local_frame(tr, to=(200.0, 0.0, 24.0), yaw=0.0)
    into_void = Retarget.local_frame(tr, to=(200.0, 3000.0, 24.0), yaw=0.0)
    assert validate_retarget(tr, into_corridor, idx, min_fraction=0.5).fraction_walked > 0
    assert not validate_retarget(tr, into_void, idx).ok


def test_cells_are_64_units():
    assert CELL == 64.0
    assert cell_of((63.9, -0.1, 128.0)) == (0, -1, 2)
