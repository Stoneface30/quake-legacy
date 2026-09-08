"""Teleport attribution: both ends, one client, or no answer."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "engine" / "parser"))

from creative_suite.engine import teleport_attribution as ta

SRC = (100.0, 0.0, 0.0)          # the teleporter pad
DEST = (2000.0, 0.0, 500.0)      # where the map sends everybody


class _Teleporter:
    """Stands in for bsp_geometry.Teleporter: a fixed map source→dest pair."""
    def __init__(self, target="t1", dest=DEST):
        self.target, self.dest = target, dest

    def dest_distance(self, p):
        import math
        return math.dist(self.dest, tuple(p)[:3])


def _ev(kind, t, ent, pos):
    return {"type": kind, "server_time_ms": t, "entity_num": ent,
            "pos_x": pos[0], "pos_y": pos[1], "pos_z": pos[2]}


def _transit(t=1000):
    return ta.TeleportTransit(t, SRC, DEST, 120, 121, "t1")


def _samples(rows):
    return [ta.PositionSample(t, c, p) for t, c, p in rows]


# ── pairing ─────────────────────────────────────────────────────────────────

def test_out_and_in_on_one_tick_pair_by_allocation_order():
    """G_TempEntity allocates OUT then IN inside one TeleportPlayer call, so
    adjacency keeps two simultaneous transits apart."""
    events = [_ev("teleport_out", 1000, 120, SRC),
              _ev("teleport_in", 1000, 121, DEST),
              _ev("teleport_out", 1000, 122, (300.0, 0.0, 0.0)),
              _ev("teleport_in", 1000, 123, DEST)]
    transits, spawns = ta.pair_transits(events, teleporters=[_Teleporter()])
    assert len(transits) == 2 and not spawns
    assert (transits[0].out_entity, transits[0].in_entity) == (120, 121)
    assert (transits[1].out_entity, transits[1].in_entity) == (122, 123)
    assert all(t.teleporter_target == "t1" for t in transits)   # map truth attached


def test_an_in_without_an_out_is_a_spawn_not_a_transit():
    """Quake fires the same event on respawn, which is why teleport_in
    outnumbers teleport_out roughly three to one in the corpus."""
    events = [_ev("teleport_in", 500, 90, (10.0, 10.0, 10.0)),
              _ev("teleport_out", 1000, 120, SRC),
              _ev("teleport_in", 1000, 121, DEST)]
    transits, spawns = ta.pair_transits(events, teleporters=[_Teleporter()],
                                        spawn_points=[(12.0, 10.0, 10.0)])
    assert len(transits) == 1 and len(spawns) == 1
    assert spawns[0].t_ms == 500
    assert spawns[0].near_spawn_point_u == pytest.approx(2.0)


# ── attribution ─────────────────────────────────────────────────────────────

def test_one_client_at_both_ends_is_confirmed():
    s = _samples([(975, 3, (110.0, 0.0, 0.0)),      # client 3 on the pad
                  (1000, 3, (2005.0, 0.0, 500.0)),  # and then at the destination
                  (975, 7, (900.0, 900.0, 0.0)),    # client 7 elsewhere throughout
                  (1000, 7, (905.0, 900.0, 0.0))])
    a = ta.attribute(_transit(), s)
    assert a.outcome == ta.CONFIRMED and a.client == 3
    for c in (ta.EV_SOURCE_AGREEMENT, ta.EV_DEST_AGREEMENT,
              ta.EV_UNIQUE_CANDIDATE, ta.EV_BSP_PAIR, ta.EV_PAIRED_EVENT):
        assert c in a.components
    assert ta.EV_STATE_DISCONTINUITY in a.components


def test_proximity_to_the_destination_alone_cannot_attribute():
    """The real failure mode: somebody is standing AT the exit when another
    player arrives. Nearest-at-destination names the bystander."""
    s = _samples([(975, 3, (2001.0, 0.0, 500.0)),    # 3 loiters ON the pad
                  (1000, 3, (2001.0, 0.0, 500.0)),
                  (975, 5, (105.0, 0.0, 0.0)),       # 5 is the one who walks in
                  (1000, 5, (2040.0, 0.0, 500.0))])  # and lands slightly offset
    a = ta.attribute(_transit(), s)
    assert a.client == 5, "the client seen at BOTH ends is the traveller"
    assert a.nearest_at_destination == 3, "proximity alone names the bystander"
    assert a.proximity_would_disagree


def test_two_clients_supported_at_both_ends_stay_ambiguous():
    s = _samples([(975, 3, (100.0, 0.0, 0.0)), (1000, 3, (2000.0, 0.0, 500.0)),
                  (975, 4, (110.0, 0.0, 0.0)), (1000, 4, (2010.0, 0.0, 500.0))])
    a = ta.attribute(_transit(), s)
    assert a.outcome == ta.AMBIGUOUS and a.client is None
    assert "does not say which one" in a.reason
    assert ta.EV_UNIQUE_CANDIDATE not in a.components


def test_no_position_evidence_is_unknown_not_a_guess():
    assert ta.attribute(_transit(), []).outcome == ta.UNKNOWN
    far = _samples([(975, 9, (5000.0, 5000.0, 0.0)), (1000, 9, (5000.0, 5000.0, 0.0))])
    a = ta.attribute(_transit(), far)
    assert a.outcome == ta.UNKNOWN and a.client is None
    assert a.nearest_at_destination == 9        # proximity would still answer
    assert a.proximity_would_disagree


def test_one_end_alone_is_not_enough():
    """At the source but never seen arriving, or arriving without ever being
    seen at the source: neither is a match."""
    source_only = _samples([(975, 3, (100.0, 0.0, 0.0)), (1000, 3, (150.0, 0.0, 0.0))])
    assert ta.attribute(_transit(), source_only).outcome == ta.UNKNOWN
    dest_only = _samples([(975, 4, (1800.0, 0.0, 500.0)), (1000, 4, (2000.0, 0.0, 500.0))])
    assert ta.attribute(_transit(), dest_only).outcome == ta.UNKNOWN


def test_the_before_sample_must_predate_the_tick():
    """The entity state stamped with the teleport tick already carries the
    arrival. If one sample may serve as both ends, nothing is ever
    attributable -- which is exactly how this failed the first time."""
    only_at_tick = _samples([(1000, 3, (2000.0, 0.0, 500.0))])
    a = ta.attribute(_transit(), only_at_tick)
    assert a.outcome == ta.UNKNOWN
    c = a.candidates[0]
    assert c.before_t_ms is None and c.after_t_ms == 1000


def test_samples_outside_the_window_are_not_evidence():
    stale = _samples([(400, 3, (100.0, 0.0, 0.0)), (1000, 3, (2000.0, 0.0, 500.0))])
    assert ta.attribute(_transit(), stale, window_ms=100).outcome == ta.UNKNOWN
    assert ta.attribute(_transit(), stale, window_ms=700).outcome == ta.CONFIRMED


# ── the recorder ────────────────────────────────────────────────────────────

def test_the_recorder_comes_from_playerstate_not_the_entity_track():
    """A client never receives its own entity, so without playerstate the
    recorder's own teleports can never be confirmed."""
    entities = [{"server_time_ms": 975, "client_num": 2, "origin_x": 900.0,
                 "origin_y": 900.0, "origin_z": 0.0}]
    snapshots = [{"server_time_ms": 975, "client_num": 4, "origin_x": 100.0,
                  "origin_y": 0.0, "origin_z": 0.0},
                 {"server_time_ms": 1000, "client_num": 4, "origin_x": 2000.0,
                  "origin_y": 0.0, "origin_z": 500.0}]
    assert ta.attribute(_transit(), ta.samples_from_entities(entities)).outcome == ta.UNKNOWN
    both = ta.all_samples(entities, snapshots, recorder_client=4)
    a = ta.attribute(_transit(), both)
    assert a.outcome == ta.CONFIRMED and a.client == 4


def test_incomplete_rows_are_dropped_rather_than_guessed():
    rows = [{"server_time_ms": 1, "client_num": None, "origin_x": 1.0,
             "origin_y": 1.0, "origin_z": 1.0},
            {"server_time_ms": 2, "client_num": 3, "origin_x": None,
             "origin_y": 1.0, "origin_z": 1.0},
            {"server_time_ms": 3, "client_num": 3, "origin_x": 1.0,
             "origin_y": 1.0, "origin_z": 1.0}]
    out = ta.samples_from_entities(rows)
    assert len(out) == 1 and out[0].t_ms == 3


def test_summary_counts_outcomes_and_the_proximity_disagreement():
    good = ta.attribute(_transit(), _samples(
        [(975, 3, (100.0, 0.0, 0.0)), (1000, 3, (2000.0, 0.0, 500.0))]))
    bad = ta.attribute(_transit(2000), [])
    s = ta.summary([good, bad])
    assert s["total"] == 2 and s[ta.CONFIRMED] == 1 and s[ta.UNKNOWN] == 1
    assert s["version"] == ta.ATTRIBUTION_VERSION


# ── map truth ───────────────────────────────────────────────────────────────

def test_the_map_declares_the_destination():
    """Teleporters are fixed map entities; the destination is read from the
    BSP entity lump, not inferred from where a player ended up."""
    from engine.parser import bsp_geometry as bg
    m = bg.load_map("asylum")
    tps = bg.teleporters(m)
    assert tps, "asylum has a teleporter"
    assert any(t.dest == (-776.0, -32.0, 680.0) for t in tps)
    assert all(t.source_bounds is not None for t in tps)
    assert len(bg.spawn_points(m)) > 5
