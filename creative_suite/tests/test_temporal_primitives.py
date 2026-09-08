"""Measure the primitive once; the effects that compose it inherit that."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import effect_templates as et, temporal_operators as t

MS = 1000


# ── the primitive registry ──────────────────────────────────────────────────

def test_a_primitive_cannot_claim_measurement_without_a_sweep():
    with pytest.raises(ValueError, match="claims measurement without a sweep"):
        et.PrimitiveTiming("X", et.RUNTIME_MEASURED)
    ok = et.PrimitiveTiming("X", et.SYNTHETIC_TEST, swept_points_us=(100 * MS,))
    assert ok.measured and not ok.approved


def test_the_measured_primitives_are_the_ones_a_canary_actually_swept():
    measured = {n for n, p in et.PRIMITIVES.items() if p.measured}
    for name in (et.P_FREEZE, et.P_STUTTER, et.P_OVERLAP, et.P_REVERSE,
                 et.P_SEQUENTIAL_INSERT, et.P_SIMULTANEOUS_OVERLAY,
                 et.P_CAMERA_CUT):
        assert name in measured, name
    for name in (et.P_MORPH, et.P_WORLD_TRANSFORM, et.P_MATERIAL_TRANSFORM,
                 et.P_INFORMATION_REVEAL, et.P_CAMERA_SPLINE,
                 et.P_SYNTHETIC_ANIMATION):
        assert name not in measured, f"{name} has no runtime yet"
        assert et.PRIMITIVES[name].finding, f"{name} should say why"


def test_every_measured_primitive_carries_its_calibration_and_finding():
    for name, p in et.PRIMITIVES.items():
        if p.measured:
            # A measurement belongs to the pipeline that produced it. The
            # cut proof ran at the footage's native rate, not at 60.
            assert p.calibration is not None, name
            assert p.calibration.fps in (30, 60), name
            assert p.swept_points_us and p.finding, name
        else:
            assert p.calibration is None, name


def test_nothing_is_human_approved_until_somebody_watches():
    assert not any(p.approved for p in et.PRIMITIVES.values())
    assert et.coverage_split()["primitives"]["human_approved"] == []


# ── composition and inheritance ─────────────────────────────────────────────

def test_every_template_declares_the_primitives_it_composes():
    for tpl in et.TEMPLATES:
        comps = et.components_of(tpl.id)
        assert comps, tpl.id
        for c in comps:
            assert c in et.PRIMITIVES, f"{tpl.id} names unknown primitive {c}"


def test_a_composite_is_partially_measured_not_wholly_estimated():
    """The danger-cross gag: its freeze is measured, its custom animation is
    not. Calling the whole effect an estimate throws away what we know."""
    provs = et.component_provenance("PLAYER_FREEZE_POSE")
    assert provs[et.P_FREEZE] == et.SYNTHETIC_TEST
    assert provs[et.P_SYNTHETIC_ANIMATION] == et.DESIGN_ESTIMATE
    assert et.template_provenance("PLAYER_FREEZE_POSE") == et.PARTIALLY_MEASURED


def test_a_template_whose_every_component_is_measured_is_measured():
    assert et.template_provenance("DEATH_REWIND") == et.SYNTHETIC_TEST
    assert set(et.component_provenance("DEATH_REWIND").values()) == {et.SYNTHETIC_TEST}


def test_a_template_with_no_measured_component_stays_an_estimate():
    assert et.template_provenance("MODEL_MORPH") == et.DESIGN_ESTIMATE
    assert not any(
        et.PRIMITIVES[c].measured for c in et.components_of("MODEL_MORPH"))


def test_measuring_one_primitive_lifts_every_effect_that_uses_it():
    """This is the whole point of the split: nine primitives carry seventeen
    fully measured effects and eighteen partially measured ones."""
    users = [tpl.id for tpl in et.TEMPLATES
             if et.P_FREEZE in et.components_of(tpl.id)]
    assert len(users) >= 4, "the freeze primitive is reused widely"
    for tid in users:
        assert et.component_provenance(tid)[et.P_FREEZE] == et.SYNTHETIC_TEST


def test_approval_of_a_primitive_would_not_approve_a_whole_effect():
    """Approving the freeze envelope says nothing about whether the danger
    cross gag is a good idea."""
    prov = et.template_provenance("PLAYER_FREEZE_POSE")
    assert prov != et.HUMAN_APPROVED
    assert et.PROVENANCE_RANK[et.PARTIALLY_MEASURED if False else prov] \
        < et.PROVENANCE_RANK[et.HUMAN_APPROVED] or prov == et.PARTIALLY_MEASURED


# ── two denominators ────────────────────────────────────────────────────────

def test_primitive_coverage_and_template_coverage_are_different_numbers():
    s = et.coverage_split()
    p, tm = s["primitives"], s["semantic_templates"]
    assert p["total"] == len(et.PRIMITIVES) == 16
    assert tm["total"] == len(et.TEMPLATES) == 50
    assert p["measured_share"] != tm["fully_measured_share"], (
        "quoting one share without naming its denominator is how a number "
        "stops meaning anything")
    buckets = (len(tm["fully_measured"]) + len(tm["partially_measured"])
               + len(tm["design_only"]))
    assert buckets == tm["total"], "every template lands in exactly one bucket"


def test_the_split_names_what_still_needs_new_technology():
    tm = et.coverage_split()["semantic_templates"]
    assert tm["requires_new_tech_or_seed"], "some ideas are not buildable yet"
    for tid in tm["requires_new_tech_or_seed"]:
        assert et.get(tid).capability in ("REQUIRES_NEW_TECH", "CREATIVE_SEED")


def test_measured_only_range_is_withheld_when_a_component_is_unbuilt():
    """Future R&D must not contaminate today's solver."""
    partial = et.measured_only_envelope("WORLD_STRIP")
    assert partial["provenance"] == et.PARTIALLY_MEASURED
    assert partial["measured_only_range_ms"] is None
    assert "unmeasured" in partial["note"]
    whole = et.measured_only_envelope("DEATH_REWIND")
    assert whole["measured_only_range_ms"] == whole["full_design_range_ms"]
    assert whole["note"] == "every component is measured"
