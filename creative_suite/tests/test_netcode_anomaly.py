"""Netcode anomalies: evidence, never verdicts."""
from __future__ import annotations

from dataclasses import replace
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (demo_truth as dt, netcode_anomaly as na,
                                   projectile_reconstruction as pr)


def _cont(recorded_pts: int = 2, total: int = 41, end_reason: str = "FUSE"):
    pts = tuple(pr.PathPoint(t * 25_000, (float(t) * 10, 0.0, 0.0), (400.0, 0.0, 0.0),
                             dt.ENTITY_OBSERVED if t < recorded_pts else dt.PHYSICS_RECONSTRUCTED)
                for t in range(total))
    launch = pr.LaunchState(pr.KIND_GRENADE, 0, pts[0].pos, pts[0].vel, dt.ENTITY_OBSERVED)
    return pr.Continuation(pr.KIND_GRENADE, launch, pts, pts[-1].t_us, end_reason, pts[-1].pos)


def _agreeing():
    cont = _cont()
    final, res = pr.truncate_at_event(cont, event_kind="missile_miss",
                                      event_t_us=cont.end_t_us, event_pos=(400.0, 5.7, 0.0))
    return final, res


# ── anomaly is not bug ──────────────────────────────────────────────────────

def test_a_lost_projectile_that_agrees_is_an_observation_gap_not_a_bug():
    final, res = _agreeing()
    a = na.from_projectile(final, res, content_hash="h" * 64, subject_client=0,
                           entity_num=199, weapon_wp=na.WP_GRENADE_LAUNCHER,
                           event_weapon_wp=na.WP_GRENADE_LAUNCHER)
    assert a.anomaly_type == na.CLIENT_OBSERVATION_GAP
    assert a.assessment == na.CLIENT_OBSERVATION_LIMITATION
    assert not a.is_bug_claim
    assert a.confidence == pr.EXACT_DETERMINISTIC
    assert a.snapshot_gap_us == 39 * 25_000            # from the last recorded sample to the end
    assert a.spatial_residual_u == pytest.approx(5.7)
    assert a.provenance_classes == (dt.ENTITY_OBSERVED, dt.PHYSICS_RECONSTRUCTED)


def test_detectors_never_assign_a_bug_assessment():
    assert na.SUSPECTED_BUG not in na.AUTOMATIC_ASSESSMENTS
    assert na.CONFIRMED_BUG not in na.AUTOMATIC_ASSESSMENTS
    assert na.SUSPICIOUS not in na.AUTOMATIC_ASSESSMENTS


def test_suspected_needs_a_reason_and_confirmed_needs_a_name():
    base = dict(content_hash="h" * 64, server_time_ms=1000, anomaly_type=na.SNAPSHOT_GAP)
    with pytest.raises(ValueError):
        na.NetcodeAnomaly(assessment=na.SUSPECTED_BUG, **base)
    with pytest.raises(ValueError):
        na.NetcodeAnomaly(assessment=na.CONFIRMED_BUG, reason="x", **base)
    ok = na.NetcodeAnomaly(assessment=na.SUSPECTED_BUG, reason="hit lands 400u off", **base)
    conf = na.NetcodeAnomaly(assessment=na.CONFIRMED_BUG, reason="…", confirmed_by="director", **base)
    assert ok.is_bug_claim and conf.is_bug_claim
    assert ok.anomaly_id != conf.anomaly_id          # a different state is a different record


def test_a_disagreeing_reconstruction_is_a_disagreement_not_a_bug():
    cont = _cont()
    final, res = pr.truncate_at_event(cont, event_kind="missile_hit",
                                      event_t_us=cont.end_t_us, event_pos=(400.0, 900.0, 0.0))
    a = na.from_projectile(final, res, content_hash="h" * 64, subject_client=0,
                           entity_num=1, weapon_wp=na.WP_GRENADE_LAUNCHER)
    assert a.anomaly_type == na.PROJECTILE_RECONSTRUCTION_DISAGREEMENT
    assert a.assessment == na.RECONSTRUCTION_DISAGREEMENT
    assert a.spatial_residual_u == pytest.approx(900.0)
    assert "not a bug claim" in a.notes[0]


def test_no_gap_means_nothing_was_reconstructed():
    cont = _cont(recorded_pts=41)
    final, res = pr.truncate_at_event(cont, event_kind="missile_miss",
                                      event_t_us=cont.end_t_us, event_pos=(400.0, 0.0, 0.0))
    a = na.from_projectile(final, res, content_hash="h" * 64, subject_client=0,
                           entity_num=1, weapon_wp=4)
    assert a.anomaly_type == na.PROJECTILE_TERMINATION_DISAGREEMENT
    assert a.assessment == na.INSUFFICIENT_EVIDENCE and a.snapshot_gap_us == 0


# ── recorded vs reconstructed timing is preserved ───────────────────────────

def test_recorded_prefix_and_reconstructed_remainder_are_reported_separately():
    final, res = _agreeing()
    a = na.from_projectile(final, res, content_hash="h" * 64, subject_client=0,
                           entity_num=1, weapon_wp=4)
    assert a.recorded_before["t_us"] == 25_000           # observation ends AT the last sample
    assert a.recorded_before["samples"] == 2
    assert a.expected_state["end_t_us"] == 1_000_000 and a.expected_state["end_reason"] == "FUSE"
    assert a.recorded_after["event_t_us"] == 1_000_000
    assert a.temporal_residual_us == 0


# ── code spaces and delta positions ─────────────────────────────────────────

def test_event_weapon_is_the_missile_launcher_only_when_entity_sourced():
    ent = {"type": "missile_hit", "weapon": 5, "source": "entity"}
    ps = {"type": "missile_hit", "weapon": 6, "source": "playerstate"}   # held weapon, not the missile
    assert na.missile_event_matches(ent, na.WP_ROCKET_LAUNCHER)
    assert not na.missile_event_matches(ps, na.WP_LIGHTNING)
    assert not na.event_weapon_is_missile(ps)
    assert not na.missile_event_matches({"type": "death", "weapon": 5}, 5)


def test_mod_and_wp_are_different_enumerations():
    assert na.wp_for_mod(na.MOD_GRENADE) == na.WP_GRENADE_LAUNCHER == 4
    assert na.wp_for_mod(na.MOD_GRENADE_SPLASH) == 4
    assert na.wp_for_mod(na.MOD_ROCKET) == na.WP_ROCKET_LAUNCHER == 5
    assert na.wp_for_mod(na.MOD_ROCKET_SPLASH) == 5
    assert na.mod_matches_wp(na.MOD_ROCKET, 5) and not na.mod_matches_wp(na.MOD_ROCKET, 4)
    assert na.wp_for_mod(None) is None


def test_missing_delta_component_means_unchanged_not_unknown():
    assert na.merge_delta_pos((723.0, 115.0, 40.0), (None, 120.0, None)) == (723.0, 120.0, 40.0)
    assert na.merge_delta_pos(None, (1.0, None, 3.0)) == (1.0, None, 3.0)


# ── synthetic evidence is refused ───────────────────────────────────────────

def test_synthetic_provenance_cannot_enter_an_anomaly():
    with pytest.raises(ValueError):
        na.NetcodeAnomaly("h" * 64, 1, na.SNAPSHOT_GAP, na.INSUFFICIENT_EVIDENCE,
                          provenance_classes=(dt.CINEMATIC_SYNTHETIC,))


# ── deterministic identity ──────────────────────────────────────────────────

def test_identical_records_share_an_id_and_notes_do_not_change_it():
    a = na.NetcodeAnomaly("h" * 64, 500, na.SNAPSHOT_GAP, na.CLIENT_OBSERVATION_LIMITATION,
                          snapshot_gap_us=200_000)
    b = na.NetcodeAnomaly("h" * 64, 500, na.SNAPSHOT_GAP, na.CLIENT_OBSERVATION_LIMITATION,
                          snapshot_gap_us=200_000, notes=("seen twice",),
                          creative_utility=na.UTILITY_INTERLUDE)
    c = replace(a, content_hash="g" * 64)               # another recording, same numbers
    assert a.anomaly_id == b.anomaly_id
    assert a.anomaly_id != c.anomaly_id
    assert a.to_dict()["subject_client"] == na.UNKNOWN  # unsupported fields stay UNKNOWN


# ── detectors ───────────────────────────────────────────────────────────────

def test_snapshot_gaps_report_duration_and_stay_client_side():
    out = na.snapshot_gaps("h" * 64, [0, 25, 50, 275, 300], subject_client=3)
    assert len(out) == 1
    assert out[0].snapshot_gap_us == 225_000 and out[0].server_time_ms == 50
    assert out[0].assessment == na.CLIENT_OBSERVATION_LIMITATION


def test_remote_jump_with_a_teleport_event_is_expected_without_one_it_is_unknown():
    s = [(0, 0.0, 0.0, 0.0), (25, 10.0, 0.0, 0.0), (50, 2000.0, 0.0, 0.0)]
    tp = na.remote_discontinuities("h" * 64, 7, s, teleport_times_ms=[45])
    assert tp[0].anomaly_type == na.REMOTE_TELEPORT
    assert tp[0].assessment == na.EXPECTED_NETCODE_BEHAVIOR
    no = na.remote_discontinuities("h" * 64, 7, s)
    assert no[0].anomaly_type == na.REMOTE_STATE_DISCONTINUITY
    assert no[0].assessment == na.INSUFFICIENT_EVIDENCE
    assert no[0].spatial_residual_u == pytest.approx(1990.0)


def test_archive_is_json_lines_sorted_and_reloadable(tmp_path):
    a = na.snapshot_gaps("h" * 64, [0, 500])[0]
    p = tmp_path / "anomalies.jsonl"
    assert na.write_archive([a, a], p) == 2
    rows = [json.loads(l) for l in p.read_text().splitlines()]
    assert rows[0]["anomaly_id"] == a.anomaly_id and rows[0]["detector_version"] == na.ANOMALY_VERSION


def test_a_re_observed_terminal_point_fed_as_input_is_not_a_proof():
    """Rocket 24326 lesson: the entity re-appears at the hit tick; if that
    sample enters the continuation the residual is 0.0 by construction."""
    pts = tuple(pr.PathPoint(t * 25_000, (float(t) * 10, 0.0, 0.0), (400.0, 0.0, 0.0),
                             dt.ENTITY_OBSERVED if t < 2 or t == 40 else dt.PHYSICS_RECONSTRUCTED)
                for t in range(41))
    launch = pr.LaunchState(pr.KIND_ROCKET, 0, pts[0].pos, pts[0].vel, dt.ENTITY_OBSERVED)
    cont = pr.Continuation(pr.KIND_ROCKET, launch, pts, pts[-1].t_us, "IMPACT", pts[-1].pos)
    final, res = pr.truncate_at_event(cont, event_kind="missile_hit", event_t_us=pts[-1].t_us,
                                      event_pos=pts[-1].pos)
    assert res.space_residual_u == 0.0                     # by construction
    a = na.from_projectile(final, res, content_hash="h" * 64, subject_client=0,
                           entity_num=174, weapon_wp=na.WP_ROCKET_LAUNCHER)
    assert a.assessment == na.INSUFFICIENT_EVIDENCE
    assert a.anomaly_type == na.PROJECTILE_TERMINATION_DISAGREEMENT
    assert "PREFIX" in a.notes[0]
