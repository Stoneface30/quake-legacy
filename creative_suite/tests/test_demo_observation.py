"""Absence from a client demo is not negative game truth."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import demo_observation as do

MS = 1000


# ── the invariant ───────────────────────────────────────────────────────────

def test_a_missing_remote_entity_is_not_proof_it_did_nothing():
    ok, why = do.may_conclude_absence(do.REMOTE_SNAPSHOT_ENTITY)
    assert not ok
    assert "not observed" in why and "did not happen" in why


def test_self_state_is_the_one_place_absence_speaks():
    """The server does not send the recorder its own entity because the
    client rebuilds it from playerstate, so it is continuous in a way remote
    evidence structurally cannot be."""
    ok, _ = do.may_conclude_absence(do.SELF_PLAYERSTATE)
    assert ok
    ok, _ = do.may_conclude_absence(do.SERVER_BROADCAST)
    assert ok


def test_claiming_a_remote_thing_would_have_been_seen_requires_the_argument():
    with pytest.raises(ValueError, match="must be stated, not assumed"):
        do.may_conclude_absence(do.REMOTE_SNAPSHOT_ENTITY,
                                would_have_been_transmitted=True)
    ok, why = do.may_conclude_absence(
        do.REMOTE_SNAPSHOT_ENTITY, would_have_been_transmitted=True,
        reason="the entity stayed inside the recorder's own area all match")
    assert ok and "recorder's own area" in why


def test_map_geometry_absence_says_nothing_about_players():
    ok, _ = do.may_conclude_absence(do.MAP_GEOMETRY)
    assert not ok


# ── observation gaps ────────────────────────────────────────────────────────

def test_reappearing_does_not_fill_the_gap():
    g = do.ObservationGap(7, 1_000 * MS, 9_000 * MS)
    assert g.duration_us == 8_000 * MS
    assert g.gap_class == do.OBSERVATION_GAP_UNKNOWN
    assert not g.bridgeable
    assert "is not evidence about the gap" in g.what_we_know()


def test_a_short_gap_may_be_bridged_and_a_long_one_may_not():
    short = do.ObservationGap(7, 0, 200 * MS)
    long = do.ObservationGap(7, 0, 4_000 * MS)
    assert short.gap_class == do.OBSERVATION_GAP_SHORT and short.bridgeable
    assert long.gap_class == do.OBSERVATION_GAP_UNKNOWN and not long.bridgeable


def test_a_gap_is_only_pvs_caused_when_something_proves_it():
    """Distance correlates with observability; it does not establish cause."""
    guess = do.ObservationGap(7, 0, 4_000 * MS)
    assert guess.gap_class == do.OBSERVATION_GAP_UNKNOWN
    proven = do.ObservationGap(7, 0, 4_000 * MS, proven_cause="PVS")
    assert proven.gap_class == do.OBSERVATION_GAP_PVS


def test_gaps_are_found_from_the_sample_stream():
    ts = [0, 50 * MS, 100 * MS, 5_000 * MS, 5_050 * MS]
    gaps = do.gaps_from_samples(3, ts)
    assert len(gaps) == 1
    assert gaps[0].last_observed_us == 100 * MS
    assert gaps[0].next_observed_us == 5_000 * MS


def test_a_continuous_stream_has_no_gaps():
    ts = list(range(0, 1_000 * MS, 50 * MS))
    assert do.gaps_from_samples(3, ts) == []


def test_a_gap_cannot_masquerade_as_continuous_tracking():
    g = do.ObservationGap(7, 1_000 * MS, 9_000 * MS)
    assert g.covers(5_000 * MS)
    assert g.gap_class != do.OBSERVED_CONTINUOUSLY


# ── teleports: truth against observation ────────────────────────────────────

def _truth():
    return do.TeleportTruth("t45", dest=(1184.0, 2080.0, 280.0))


def test_a_departure_with_no_arrival_is_a_whole_teleport_half_seen():
    o = do.TeleportObservation(12_000, do.SOURCE_ONLY_OBSERVED,
                               out_pos=(-1317.0, -933.0, 192.0),
                               truth=_truth(), attribution="CONFIRMED",
                               client=3)
    assert o.departure_observed and not o.arrival_observed
    assert not o.is_complete_transit
    assert "The player did arrive; we did not see it" in o.what_we_know()


def test_map_truth_is_not_an_observed_arrival():
    o = do.TeleportObservation(12_000, do.SOURCE_ONLY_OBSERVED,
                               out_pos=(-1317.0, -933.0, 192.0), truth=_truth())
    assert o.known_destination == (1184.0, 2080.0, 280.0)
    assert o.in_pos is None, "the map knowing where it leads is not a sighting"
    assert not o.arrival_observed


def test_a_source_only_record_cannot_carry_an_invented_arrival():
    with pytest.raises(ValueError, match="not the same as having seen"):
        do.TeleportObservation(1, do.SOURCE_ONLY_OBSERVED,
                               out_pos=(0.0, 0.0, 0.0),
                               in_pos=(1184.0, 2080.0, 280.0))


def test_both_endpoints_must_actually_have_both():
    with pytest.raises(ValueError, match="no position"):
        do.TeleportObservation(1, do.BOTH_ENDPOINTS_OBSERVED,
                               out_pos=(0.0, 0.0, 0.0))


def test_destination_only_keeps_the_real_arrival():
    o = do.TeleportObservation(9_000, do.DESTINATION_ONLY_OBSERVED,
                               in_pos=(1184.0, 2080.0, 280.0))
    assert o.arrival_observed and not o.departure_observed
    assert not o.is_complete_transit


# ── one-ended observations are still useful ─────────────────────────────────

def test_a_half_seen_teleport_still_offers_a_transition_port():
    out_only = do.TeleportObservation(1, do.SOURCE_ONLY_OBSERVED,
                                      out_pos=(0.0, 0.0, 0.0))
    in_only = do.TeleportObservation(2, do.DESTINATION_ONLY_OBSERVED,
                                     in_pos=(0.0, 0.0, 0.0))
    assert out_only.ports() == (do.TELEPORT_EXIT_PORT,)
    assert in_only.ports() == (do.TELEPORT_ENTRY_PORT,)


def test_only_a_fully_seen_trip_offers_the_confirmed_pair():
    half = do.TeleportObservation(1, do.SOURCE_ONLY_OBSERVED,
                                  out_pos=(0.0, 0.0, 0.0))
    whole = do.TeleportObservation(2, do.BOTH_ENDPOINTS_OBSERVED,
                                   out_pos=(0.0, 0.0, 0.0),
                                   in_pos=(10.0, 0.0, 0.0))
    assert do.CONFIRMED_TELEPORT_PAIR not in half.ports()
    assert do.CONFIRMED_TELEPORT_PAIR in whole.ports()


def test_nothing_seen_offers_nothing():
    o = do.TeleportObservation(1, do.NEITHER_ENDPOINT_OBSERVED)
    assert o.ports() == () and not o.is_complete_transit


# ── the closeout number means less than it looks ────────────────────────────

def test_records_are_a_floor_not_coverage():
    """The finding that produced this module: one map recorded 906 real
    departures and zero arrivals, and reporting that as no teleport activity
    would have been wrong."""
    c = do.coverage_is_not_activity(1_807, 4_292)
    assert c["is_activity_coverage"] is False
    assert "may contain any amount of teleporting" in c["meaning"]


def test_self_and_remote_evidence_are_not_interchangeable():
    assert do.ABSENCE_IS_INFORMATIVE[do.SELF_PLAYERSTATE]
    assert not do.ABSENCE_IS_INFORMATIVE[do.REMOTE_SNAPSHOT_ENTITY]
    g = do.ObservationGap(0, 0, 4_000 * MS, source=do.SELF_PLAYERSTATE)
    assert g.source == do.SELF_PLAYERSTATE
