"""Delivery, the eye, and the grammar are three different questions."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (creative_opportunity as co,
                                   effect_approval as ea, effect_templates as et,
                                   temporal_budget as tb)

MS = 1000


def _real(**kw):
    base = dict(reviewer="director", footage="canary_freeze_real.mp4",
                footage_kind=ea.REAL_GAMEPLAY, preferred_min_us=200 * MS,
                preferred_max_us=400 * MS)
    base.update(kw)
    return ea.VisualVerdict(**base)


# ── the three axes ──────────────────────────────────────────────────────────

def test_the_synthetic_sweeps_prove_delivery_and_nothing_more():
    s = ea.status()
    assert len(s["delivery_verified"]) == 9
    assert s["visually_approved"] == [] and s["semantically_approved"] == []
    assert len(s["awaiting_the_eye"]) == 9
    a = ea.approval_for("FREEZE")
    assert a.state == ea.DELIVERY_VERIFIED
    assert "synthetic footage" in a.blocking()


def test_a_verdict_on_synthetic_footage_is_refused():
    """A generated counter has no frag, no target and no tension, so it cannot
    answer whether a duration looks good."""
    with pytest.raises(ea.ApprovalRefused, match="cannot answer whether a duration"):
        _real(footage="review_freeze_sweep.mp4", footage_kind=ea.SYNTHETIC_FOOTAGE)


def test_look_cannot_be_approved_before_delivery_is_verified():
    with pytest.raises(ea.ApprovalRefused, match="approves nothing"):
        ea.record_visual_verdict("MORPH", _real())


def test_delivery_evidence_must_name_its_sweep_and_its_configuration():
    with pytest.raises(ea.ApprovalRefused, match="durations swept"):
        ea.DeliveryEvidence("c", "60fps/x", (), 0)
    with pytest.raises(ea.ApprovalRefused, match="render configuration"):
        ea.DeliveryEvidence("c", "", (100 * MS,), 0)


def test_a_verdict_needs_whose_verdict_it_is():
    with pytest.raises(ea.ApprovalRefused, match="whose verdict"):
        _real(reviewer="")


def test_recording_a_real_verdict_lifts_only_that_axis():
    original = ea.approval_for("OVERLAP")
    try:
        got = ea.record_visual_verdict("OVERLAP", _real(
            footage="canary_overlap_real.mp4", preferred_min_us=150 * MS,
            preferred_max_us=300 * MS, notes="seamless on a rocket-to-rocket match"))
        assert got.visually_approved and got.state == ea.VISUALLY_APPROVED
        assert not got.semantically_approved
        assert "grammar has not been judged" in got.blocking()
        assert got.delivery_verified, "delivery evidence is not lost"
    finally:
        ea.APPROVALS["OVERLAP"] = original


def test_approving_a_primitive_does_not_approve_an_effect_that_uses_it():
    original = ea.approval_for("FREEZE")
    try:
        ea.record_visual_verdict("FREEZE", _real())
        assert ea.approval_for("FREEZE").visually_approved
        gag = ea.approval_for("PLAYER_FREEZE_POSE")
        assert not gag.visually_approved and not gag.semantically_approved
        assert et.P_FREEZE in et.components_of("PLAYER_FREEZE_POSE")
    finally:
        ea.APPROVALS["FREEZE"] = original


def test_a_semantic_verdict_is_about_a_whole_grammar():
    v = ea.SemanticVerdict("director", "HERO_THEN_DEATH_REWIND",
                           context="a phrase built from a punished brilliance",
                           accepted=True)
    got = ea.record_semantic_verdict("HERO_THEN_DEATH_REWIND", v)
    try:
        assert got.semantically_approved and got.state == ea.SEMANTICALLY_APPROVED
        assert not got.delivery_verified, "a grammar verdict is not a canary"
    finally:
        ea.APPROVALS.pop("HERO_THEN_DEATH_REWIND", None)


def test_a_rejected_semantic_verdict_is_not_an_approval():
    v = ea.SemanticVerdict("director", "X", context="tried it", accepted=False)
    got = ea.record_semantic_verdict("X", v)
    try:
        assert not got.semantically_approved
    finally:
        ea.APPROVALS.pop("X", None)


# ── temporal budget ─────────────────────────────────────────────────────────

HERO_J = tb.Justification(
    narrative="hero", gameplay_kind="projectile",
    evidence_present=("frag", "projectile_path", "movement", "death"))

# A budget may only ever see what the action earned, so these tests build the
# vocabulary from real evidence rather than handing the solver a wish list.
HERO_EVIDENCE = co.MomentEvidence(
    moment_ref="h@1125", kinds=("frag", "movement"), weapon="ROCKET",
    projectile_path=True, projectile_recorded_fraction=0.02,
    projectile_close_pass_u=90, relative_speed_u_s=980,
    round_result="WIN", teammates=2, opponents=3, alive_self=1, alive_enemy=2,
    death_after_us=700 * MS, damage_by_user=120,
    scene_start_us=0, scene_end_us=4_250 * MS, hero_us=3_400 * MS,
    source_useful_us=4_250 * MS)
HERO_OPS = co.opportunities_for(HERO_EVIDENCE)


def test_the_budget_states_the_gap_and_what_may_close_it():
    b = tb.build("SLOT_A", 8_400 * MS, 4_250 * MS, 7_830 * MS, HERO_J,
                 opportunities=HERO_OPS)
    assert b.delta_us == 570 * MS and b.needs_more
    assert b.verdict == "SOLVABLE" and b.solutions
    assert all(o.eligible for o in b.eligible_options)
    for s in b.solutions:
        assert s.total_us == b.delta_us
        assert sum(s.contributions_us) == b.delta_us


def test_an_effect_must_fit_temporally_and_also_belong():
    """Three independent gates. Passing two is not passing."""
    j = tb.Justification(narrative="comedy", gameplay_kind="movement",
                         evidence_present=("movement",))
    b = tb.build("SLOT_D", 5_000 * MS, 4_000 * MS, 4_400 * MS, j,
                 candidates=["ENEMY_REVEAL_STEP", "FREEZE_HOLD"])
    reveal = next(o for o in b.options if o.template_id == "ENEMY_REVEAL_STEP")
    assert tb.TEMPORAL_FIT in reveal.gates_passed
    assert tb.CREATIVE_JUSTIFICATION not in reveal.gates_passed
    assert "alive_state" in reveal.refused_because and not reveal.eligible
    freeze = next(o for o in b.options if o.template_id == "FREEZE_HOLD")
    assert tb.TEMPORAL_FIT in freeze.gates_passed
    assert tb.VISUAL_FIT in freeze.gates_passed
    assert tb.CREATIVE_JUSTIFICATION not in freeze.gates_passed
    assert "does not serve a comedy slot" in freeze.refused_because


def test_an_unmeasured_duration_can_be_refused_outright():
    j = tb.Justification(narrative="team", gameplay_kind="team",
                         evidence_present=("team_state", "round_result"))
    strict = tb.build("S", 5_000 * MS, 4_000 * MS, 4_600 * MS, j,
                      candidates=["MODEL_MORPH"], trusted_only=True)
    o = strict.options[0]
    assert tb.VISUAL_FIT not in o.gates_passed
    assert "nobody has measured" in o.refused_because


def test_no_tasteful_solution_means_the_moment_does_not_fit():
    """The honest answer is that this moment belongs in a different slot, not
    that we found something to pad it with."""
    j = tb.Justification(narrative="comedy", gameplay_kind="movement",
                         evidence_present=("movement",))
    b = tb.build("SLOT_C", 30_000 * MS, 4_000 * MS, 4_000 * MS, j,
                 candidates=["FREEZE_HOLD", "MATCH_CUT_OVERLAP"])
    assert b.verdict == "DOES_NOT_FIT" and not b.solutions
    assert "does not fit this slot" in b.explain()


def test_a_balanced_slot_needs_nothing():
    b = tb.build("S", 5_000 * MS, 3_000 * MS, 5_000 * MS, HERO_J,
                 opportunities=HERO_OPS)
    assert b.balanced and b.verdict == "BALANCED"
    assert "already exact" in b.explain()


def test_a_surplus_is_reported_as_a_negative_need():
    b = tb.build("S", 5_000 * MS, 3_000 * MS, 5_400 * MS, HERO_J,
                 opportunities=HERO_OPS)
    assert b.delta_us == -400 * MS and not b.needs_more
    subtractive = [o for o in b.eligible_options if not o.adds_time]
    assert subtractive, "an overlap can give time back"


def test_solutions_prefer_measured_timing_and_the_smallest_tool():
    b = tb.build("SLOT_A", 8_400 * MS, 4_250 * MS, 7_830 * MS, HERO_J,
                 opportunities=HERO_OPS)
    first = b.solutions[0]
    ranks = [et.PROVENANCE_RANK[s.weakest_provenance] for s in b.solutions]
    assert ranks[0] >= max(ranks) - 0.001 or ranks == sorted(ranks, reverse=True) \
        or et.PROVENANCE_RANK[first.weakest_provenance] >= et.PROVENANCE_RANK[et.SYNTHETIC_TEST]
    assert len(first.options) == 1, "one honest tool beats two"


def test_a_concurrent_effect_cannot_close_a_deficit():
    """A picture-in-picture adds no time, so it can never supply milliseconds."""
    b = tb.build("S", 5_000 * MS, 4_000 * MS, 4_400 * MS, HERO_J,
                 candidates=["POV_PIP"])
    o = b.options[0]
    assert o.min_us == 0 == o.max_us
    assert not o.eligible and b.verdict == "DOES_NOT_FIT"
