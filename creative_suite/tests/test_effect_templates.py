"""Effects are measured temporal tools, and we say which numbers we measured."""
from __future__ import annotations

from fractions import Fraction
import sys
from dataclasses import replace
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (creative_corpus as cc, effect_templates as et,
                                   temporal_operators as t, temporal_solver as ts)

MS = 1000


# ── coverage ────────────────────────────────────────────────────────────────

def test_every_creative_idea_has_timing_or_a_stated_exemption():
    """No creative concept may be invisible to the temporal solver."""
    cov = et.coverage(cc.BY_NAME)
    assert cov["missing"] == [], f"no temporal template: {cov['missing']}"
    assert cov["covered"] + cov["exempt"] == len(cc.CORPUS)
    for name, reason in et.NO_TEMPLATE_REQUIRED.items():
        assert name in cc.BY_NAME, f"{name} is exempt from nothing"
        assert len(reason) > 20, f"{name}'s exemption needs a real reason"


def test_every_template_maps_to_a_real_operator_and_family():
    for tpl in et.TEMPLATES:
        assert tpl.operator in t.KINDS
        assert tpl.family in et.FAMILIES
        assert tpl.temporal_power in et.POWERS
        for name in tpl.corpus_entries:
            assert name in cc.BY_NAME, f"{tpl.id} claims unknown idea {name}"


def test_all_fifteen_families_are_represented():
    cov = et.coverage(cc.BY_NAME)
    empty = [f for f, n in cov["by_family"].items() if n == 0]
    assert not empty, f"families with no template: {empty}"


# ── provenance ──────────────────────────────────────────────────────────────

def test_an_estimate_cannot_masquerade_as_a_measurement():
    with pytest.raises(ValueError, match="claims measurement but no durations"):
        et.DurationEnvelope(100 * MS, 200 * MS, 300 * MS, 400 * MS,
                            et.RUNTIME_MEASURED)
    with pytest.raises(ValueError, match="unknown timing provenance"):
        et.DurationEnvelope(100 * MS, 200 * MS, 300 * MS, 400 * MS, "TRUST_ME")


def test_only_swept_envelopes_are_trusted_by_the_solver():
    guess = et.DurationEnvelope(100 * MS, 200 * MS, 300 * MS, 400 * MS)
    assert guess.provenance == et.DESIGN_ESTIMATE and not guess.solver_trusted
    swept = et.DurationEnvelope(100 * MS, 200 * MS, 300 * MS, 400 * MS,
                                et.SYNTHETIC_TEST, swept_points_us=(100 * MS,))
    assert swept.solver_trusted


def test_the_library_reports_how_much_of_it_is_measured():
    cov = et.coverage(cc.BY_NAME)
    assert cov["by_provenance"][et.SYNTHETIC_TEST] >= 5
    assert cov["by_provenance"][et.DESIGN_ESTIMATE] > 0, "we are not pretending"
    assert 0 < cov["measured_share"] < 1


def test_a_choreography_reports_which_of_its_timings_are_guesses():
    conf = et.solver_confidence(["FREEZE_HOLD", "MODEL_MORPH"])
    assert conf["measured"] == ["FREEZE_HOLD"]
    assert conf["estimated"] == ["MODEL_MORPH"]
    assert not conf["trusted"]
    assert "reasoning, not measurement" in conf["note"]
    allm = et.solver_confidence(["FREEZE_HOLD", "MATCH_CUT_OVERLAP"])
    assert allm["trusted"] and "swept" in allm["note"]


# ── envelopes ───────────────────────────────────────────────────────────────

def test_envelope_bounds_must_nest():
    with pytest.raises(ValueError, match="must nest"):
        et.DurationEnvelope(400 * MS, 200 * MS, 300 * MS, 500 * MS)


def test_hard_limits_and_preferred_band_are_different_things():
    f = et.get("FREEZE_HOLD").envelope
    assert f.hard_min_us < f.preferred_min_us
    assert f.preferred_max_us < f.hard_max_us
    assert f.preferred_min_us <= f.preferred_us <= f.preferred_max_us


def test_temporal_power_bounds_the_envelope():
    """A MICRO effect cannot reach for four seconds to solve a deficit."""
    for tpl in et.TEMPLATES:
        assert tpl.envelope.hard_max_us <= et.POWER_CEILING_US[tpl.temporal_power]
    with pytest.raises(ValueError, match="tops out at"):
        et.TemporalEffectTemplate(
            "X", et.F_CUTTING, (), t.FREEZE,
            et.DurationEnvelope(0, 100 * MS, 4_000 * MS, 5_000 * MS), et.MICRO)


def test_the_three_feasibility_questions_stay_apart():
    freeze = et.get("FREEZE_HOLD")           # swept
    morph = et.get("MODEL_MORPH")            # estimated
    assert freeze.feasibility(250 * MS) == et.VISUALLY_FEASIBLE
    assert morph.feasibility(400 * MS) == et.MATHEMATICALLY_FEASIBLE
    assert freeze.feasibility(50 * MS) == "INFEASIBLE"
    approved = replace(freeze, envelope=replace(freeze.envelope,
                                                provenance=et.HUMAN_APPROVED))
    assert approved.feasibility(250 * MS) == et.DIRECTOR_APPROVED


def test_human_approval_is_a_separate_rung_nobody_has_climbed_yet():
    assert et.PROVENANCE_RANK[et.HUMAN_APPROVED] > et.PROVENANCE_RANK[et.RUNTIME_MEASURED]
    assert not any(tpl.envelope.provenance == et.HUMAN_APPROVED
                   for tpl in et.TEMPLATES), "nobody has reviewed these yet"


# ── measured delivery ───────────────────────────────────────────────────────

def test_the_freeze_delivery_bias_is_compensated_not_absorbed():
    """The canary showed a freeze comes back one frame long, every time.
    Asking for what you want and accepting what arrives is how a composition
    drifts."""
    e = et.get("FREEZE_HOLD").envelope
    assert e.delivery_bias_us == et.FRAME_US
    assert e.request_for(300 * MS) == 300 * MS - et.FRAME_US
    assert e.quantisation_us == et.FRAME_US


def test_swept_templates_carry_the_points_that_were_rendered():
    for tid in ("FREEZE_HOLD", "RHYTHMIC_IMAGE_STUTTER", "MATCH_CUT_OVERLAP"):
        e = et.get(tid).envelope
        assert e.provenance == et.SYNTHETIC_TEST
        assert e.swept_points_us, tid
        assert e.rationale, tid


# ── operators built from templates ──────────────────────────────────────────

def test_a_template_yields_an_operator_with_its_own_envelope():
    tpl = et.get("FREEZE_HOLD")
    op = tpl.operator_for("hold")
    assert op.kind == t.FREEZE and op.label == "hold"
    assert op.hard_min_us == tpl.envelope.hard_min_us
    assert op.preferred_min_us == tpl.envelope.preferred_min_us
    assert op.anchor_kind == "FREEZE_RELEASE"
    assert et.SYNTHETIC_TEST in op.notes, "the operator carries its provenance"


def test_sign_follows_the_operator_kind_not_the_wish():
    assert et.get("MATCH_CUT_OVERLAP").sign == -1
    assert et.get("FREEZE_HOLD").sign == 1
    assert et.get("POV_PIP").sign == 0


def test_sequential_pov_adds_time_and_pip_does_not():
    """The same creative idea, two temporal behaviours."""
    seq, pip = et.get("ENEMY_POV_INSERT"), et.get("POV_PIP")
    assert seq.operator == t.INSERT and seq.sign == 1
    assert pip.operator == t.REPLACE and pip.sign == 0
    assert t.OperatorChoice(pip.operator_for(), 1_500 * MS).edit_us == 0
    assert t.OperatorChoice(seq.operator_for(), 1_500 * MS).edit_us == 1_500 * MS
    assert "SEQUENTIAL" in seq.notes and "SIMULTANEOUS" in pip.notes


def test_effect_specific_sync_anchors_survive_into_the_operator():
    assert et.get("RHYTHMIC_IMAGE_STUTTER").operator_for().anchor_kind == "STUTTER_ATTACK"
    assert et.get("SIDE_REPLAY").operator_for().anchor_kind == "HERO"
    assert et.get("MODEL_MORPH").operator_for().anchor_kind == "MORPH_PEAK"
    assert t.BIAS_US["STUTTER_ATTACK"] == 0 and t.BIAS_US["HERO"] == -15 * MS


# ── combinations ────────────────────────────────────────────────────────────

def test_competing_effects_are_flagged():
    problems = et.check_combination(["WORLD_STRIP", "MOSAIC_TILE_STEP"])
    assert any("compete" in p for p in problems)
    assert et.check_combination(["WORLD_STRIP", "ENEMY_REVEAL_STEP",
                                 "FREEZE_HOLD"]) == []


def test_ordering_requirements_are_enforced():
    assert et.check_combination(["WORLD_STRIP", "WORLD_REBUILD"]) == []
    backwards = et.check_combination(["WORLD_REBUILD", "WORLD_STRIP"])
    assert any("must come after" in p or "must come before" in p for p in backwards)


def test_a_combination_has_its_own_duration_envelope():
    el = et.combined_envelope(["SLOW_MOTION", "FREEZE_HOLD", "SIDE_REPLAY",
                               "MODEL_MORPH", "MATCH_CUT_OVERLAP"])
    assert el.min_us < el.max_us
    assert el.preferred_min_us >= el.min_us and el.preferred_max_us <= el.max_us
    assert el.fits(5_850 * MS)


# ── the search question ─────────────────────────────────────────────────────

SPEC = [{"template": "SLOW_MOTION", "label": "fpv",
         "src_in_us": 0, "src_out_us": 2_150 * MS},
        {"template": "FREEZE_HOLD", "label": "freeze"},
        {"template": "SIDE_REPLAY", "label": "side_replay",
         "src_in_us": 1_025 * MS, "src_out_us": 2_150 * MS},
        {"template": "MODEL_MORPH", "label": "morph"},
        {"template": "MATCH_CUT_OVERLAP", "label": "transition_overlap"}]


def test_a_slot_verdict_uses_template_envelopes_not_raw_duration():
    v = et.slot_verdict(5_850 * MS, SPEC)
    assert v["verdict"] == "PREFERRED_FEASIBLE"
    assert v["hard_ms"][0] < 5_850 < v["hard_ms"][1]
    assert v["preferred_ms"][0] <= 5_850 <= v["preferred_ms"][1]
    assert v["combination_problems"] == []
    assert v["timing_confidence"]["estimated"], "it admits what it guessed"


def test_a_slot_outside_the_template_envelope_is_refused():
    v = et.slot_verdict(60_000 * MS, SPEC)
    assert v["verdict"] == "INFEASIBLE"


def test_the_solver_runs_on_template_envelopes():
    anchors = (t.AnchorConstraint("side_replay", 4_600 * MS, "HERO", 40 * MS),)
    rep, conf, problems = et.solve_from_templates(
        "DOUBLE_AIR_ROCKET_TEMPLATED", 5_850 * MS, SPEC, anchors=anchors)
    assert rep.feasible and rep.best is not None
    assert rep.best.plan.exact and rep.best.plan.total_us == 5_850 * MS
    assert rep.best.plan.anchors_satisfied
    assert problems == []
    assert set(conf["measured"]) == {"SLOW_MOTION", "FREEZE_HOLD", "MATCH_CUT_OVERLAP"}
    # every chosen duration lies inside its own template's hard range
    for choice in rep.best.plan.choices:
        tpl = next(x for x in et.TEMPLATES
                   if x.id in choice.operator.notes.split()[0])
        assert tpl.envelope.hard_min_us <= choice.duration_us <= tpl.envelope.hard_max_us


# ── gesture-derived timing ──────────────────────────────────────────────────

def test_a_gesture_sets_the_stutters_duration_and_uneven_spacing_survives():
    """The canary rendered 110/230/170 ms and delivered it within 6.7 ms, so
    a figure is never forced onto an even grid."""
    uneven = ts.stutter_from_gesture("s", (0, 110 * MS, 340 * MS, 510 * MS))
    assert uneven.hard_min_us == uneven.hard_max_us      # the figure fixes it
    assert uneven.repeats_min == 4
    even = ts.stutter_from_gesture("s", (0, 150 * MS, 300 * MS, 450 * MS))
    assert even.hard_max_us != uneven.hard_max_us, "different figures, different lengths"
    tpl = et.get("RHYTHMIC_IMAGE_STUTTER")
    assert tpl.envelope.hard_min_us <= uneven.hard_max_us <= tpl.envelope.hard_max_us


# ── the atlas ───────────────────────────────────────────────────────────────

def test_the_atlas_says_which_rows_are_measured():
    rows = et.atlas_rows()
    assert len(rows) == len(et.TEMPLATES)
    assert any(r["measured"] for r in rows) and any(not r["measured"] for r in rows)
    for r in rows:
        assert r["hard_ms"][0] <= r["preferred_ms"][0]
        assert r["preferred_ms"][1] <= r["hard_ms"][1]
        assert r["provenance"] in et.PROVENANCE


def test_the_atlas_renders(tmp_path):
    p = et.render_atlas(tmp_path / "atlas.png")
    assert p.exists() and p.stat().st_size > 10_000
