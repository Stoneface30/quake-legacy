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


# ── fillability and readiness ───────────────────────────────────────────────

def test_temporal_effect_fillability_is_its_own_measure():
    from creative_suite.engine import choreography as ch
    f = ch.temporal_effect_fillability()
    assert f["templates"] == len(et.TEMPLATES)
    assert 0 < f["measured"] < f["templates"], "some measured, some not"
    assert f["human_approved"] == 0, "nobody has reviewed the envelopes yet"
    assert f["measured_scales"] >= 2
    assert sum(f["by_power"].values()) == f["templates"]


def test_ranking_songs_on_estimated_envelopes_is_blocked():
    from creative_suite.engine import (choreography as ch, choreography_proofs as cp,
                                       temporal_proofs as tpf)
    common = dict(corpus_entries=len(cc.CORPUS), lanes_covered=len(ch.LANES),
                  proofs_built=len(cp.PROOFS), gameplay_truth_ready=True,
                  music_library_ready=True, temporal_proofs_built=len(tpf.PROOFS))
    guessing = ch.assess_readiness(measured_templates=0, measured_scales=0, **common)
    assert not guessing.may_shortlist_songs and not guessing.effect_library_ready
    assert any("false precision" in b for b in guessing.blockers)
    f = ch.temporal_effect_fillability()
    now = ch.assess_readiness(measured_templates=f["measured"],
                              measured_scales=f["measured_scales"], **common)
    assert now.effect_library_ready == (f["measured"] >= 6 and f["measured_scales"] >= 3)


def test_a_vocabulary_measured_at_only_one_scale_is_not_enough():
    from creative_suite.engine import (choreography as ch, choreography_proofs as cp,
                                       temporal_proofs as tpf)
    r = ch.assess_readiness(
        corpus_entries=len(cc.CORPUS), lanes_covered=len(ch.LANES),
        proofs_built=len(cp.PROOFS), gameplay_truth_ready=True,
        music_library_ready=True, temporal_proofs_built=len(tpf.PROOFS),
        measured_templates=20, measured_scales=1)
    assert not r.may_shortlist_songs
    assert any("temporal scales" in b for b in r.blockers)


# ── second canary batch ─────────────────────────────────────────────────────

def test_pip_and_a_cut_to_the_same_material_cost_differently():
    """Measured: an overlay adds 0.0 ms at 600-2400 ms; cutting to the same
    material adds its whole duration."""
    pip, cut = et.get("POV_PIP"), et.get("ENEMY_POV_INSERT")
    assert pip.envelope.provenance == et.SYNTHETIC_TEST
    assert cut.envelope.provenance == et.SYNTHETIC_TEST
    assert pip.envelope.swept_points_us == cut.envelope.swept_points_us
    for ms in (600, 1200, 2400):
        assert t.OperatorChoice(pip.operator_for(), ms * MS).edit_us == 0
        assert t.OperatorChoice(cut.operator_for(), ms * MS).edit_us == ms * MS


def test_a_rewind_costs_twice_the_slice_it_rewinds():
    """It runs the slice backwards and then forwards again. Budgeting the
    slice length would leave the composition short by the same amount."""
    assert et.REWIND_COST_FACTOR == 2
    tpl = et.get("DEATH_REWIND")
    assert tpl.envelope.provenance == et.SYNTHETIC_TEST
    assert "twice the slice" in tpl.envelope.rationale
    # the envelope is the delivered cost, so a 450 ms slice sits at 900 ms
    assert tpl.envelope.hard_min_us <= 900 * MS <= tpl.envelope.hard_max_us


# ── the loop closes ─────────────────────────────────────────────────────────

def test_a_solved_plan_renders_to_exactly_the_duration_it_promised(tmp_path):
    """Arithmetic is not delivery. This renders a solved plan and measures
    the file: planned duration, delivered duration, and the difference."""
    import json
    import subprocess
    ff = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
    fp = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffprobe.exe"
    if not (ff.exists() and fp.exists()):
        pytest.skip("ffmpeg not on disk")
    FPS = 60

    src = tmp_path / "src.mp4"
    r = subprocess.run([str(ff), "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        f"testsrc=size=320x180:rate={FPS}:duration=4", "-c:v",
                        "libx264", "-preset", "ultrafast", "-crf", "28",
                        "-pix_fmt", "yuv420p", str(src)], capture_output=True,
                       text=True, timeout=300)
    assert r.returncode == 0, r.stderr[:300]

    slot = 3_000 * MS
    spec = [{"template": "SLOW_MOTION", "label": "a",
             "src_in_us": 0, "src_out_us": 1_000 * MS},
            {"template": "FREEZE_HOLD", "label": "hold"},
            {"template": "SLOW_MOTION", "label": "b",
             "src_in_us": 1_000 * MS, "src_out_us": 2_000 * MS}]
    report, conf, problems = et.solve_from_templates("RENDER_CANARY", slot, spec)
    assert report.feasible, report.reason
    plan = report.best.plan
    assert plan.exact and plan.total_us == slot

    freeze_tpl = et.get("FREEZE_HOLD")
    filters, order = [], []
    for i, c in enumerate(plan.choices):
        op = c.operator
        if op.kind == t.FREEZE:
            ask = freeze_tpl.envelope.request_for(c.duration_us)
            filters.append(f"[0:v]trim=2:{2 + 1/FPS},setpts=PTS-STARTPTS,"
                           f"tpad=stop_mode=clone:stop_duration={ask/1e6:.6f},"
                           f"fps={FPS},settb=AVTB[s{i}]")
        else:
            filters.append(f"[0:v]trim={op.src_in_us/1e6}:{op.src_out_us/1e6},"
                           f"setpts=(PTS-STARTPTS)/{float(c.rate):.8f},"
                           f"fps={FPS},settb=AVTB[s{i}]")
        order.append(f"[s{i}]")
    filters.append("".join(order) + f"concat=n={len(order)}:v=1:a=0[v]")
    dst = tmp_path / "out.mp4"
    r = subprocess.run([str(ff), "-y", "-loglevel", "error", "-i", str(src),
                        "-filter_complex", ";".join(filters), "-map", "[v]",
                        "-r", str(FPS), "-c:v", "libx264", "-preset", "ultrafast",
                        "-crf", "28", "-pix_fmt", "yuv420p", str(dst)],
                       capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr[:400]

    pr = subprocess.run([str(fp), "-v", "error", "-count_frames", "-select_streams",
                         "v:0", "-show_entries",
                         "stream=nb_read_frames:format=duration", "-of", "json",
                         str(dst)], capture_output=True, text=True, timeout=300)
    probe = json.loads(pr.stdout)
    delivered_us = int(round(float(probe["format"]["duration"]) * 1e6))
    frames = int(probe["streams"][0]["nb_read_frames"])

    # one frame of tolerance: the plan is exact, the encoder works in frames
    assert abs(delivered_us - slot) <= 16_667, (
        f"planned {slot} us, delivered {delivered_us} us")
    assert abs(frames - round(slot / 1e6 * FPS)) <= 1


# ── delivery calibration belongs to its pipeline ────────────────────────────

def test_a_compensation_is_keyed_to_the_configuration_that_produced_it():
    e = et.get("FREEZE_HOLD").envelope
    assert e.calibration is not None and e.calibration.fps == 60
    assert e.calibration.frame_us == et.FRAME_US
    assert "effect_canaries" in e.calibration.pipeline
    assert e.request_for(300 * MS) == 300 * MS - et.FRAME_US


def test_a_stale_calibration_is_refused_rather_than_reused():
    """A 60 fps frame is not a 120 fps frame."""
    e = et.get("FREEZE_HOLD").envelope
    future = et.DeliveryCalibration(fps=120, encoder="libx264", pipeline="next")
    with pytest.raises(et.StaleCalibration, match="re-measure"):
        e.request_for(300 * MS, calibration=future)
    same = et.DeliveryCalibration(fps=60, encoder="libx264", pipeline="other")
    assert e.request_for(300 * MS, calibration=same) == 300 * MS - et.FRAME_US


def test_an_estimated_envelope_carries_no_calibration():
    assert et.get("MODEL_MORPH").envelope.calibration is None
    assert et.get("MODEL_MORPH").envelope.request_for(400 * MS) == 400 * MS


def test_desired_requested_and_delivered_stay_three_different_numbers():
    e = et.get("FREEZE_HOLD").envelope
    desired = 300 * MS
    requested = e.request_for(desired)
    assert requested < desired, "the request compensates for the known bias"
    assert "desired" in e.desired_vs_requested and "delivered" in e.desired_vs_requested


# ── capability states ───────────────────────────────────────────────────────

def test_an_unmeasured_primitive_must_name_its_blocker():
    """"Unmeasured" on its own is a shrug. It has to say what is missing and
    what would let a sweep run."""
    for name, p in et.PRIMITIVES.items():
        if p.measured:
            continue
        assert p.blocked_by, f"{name} does not say what blocks it"
        assert p.measurable_when, f"{name} does not say what would unblock it"
        assert p.capability != et.MEASURED


def test_a_primitive_cannot_claim_measured_without_a_measurement():
    with pytest.raises(ValueError, match="claims to be measured"):
        et.PrimitiveTiming("X", et.DESIGN_ESTIMATE, capability=et.MEASURED)


def test_an_unmeasured_primitive_cannot_shrug():
    with pytest.raises(ValueError, match="just a shrug"):
        et.PrimitiveTiming("X", et.DESIGN_ESTIMATE,
                           capability=et.RUNTIME_MISSING)


def test_the_report_ranks_gaps_by_how_close_and_how_costly_they_are():
    r = et.capability_report()
    rows = r["unmeasured"]
    assert len(rows) == 6
    # nearest first: a runtime that exists but is unswept beats missing tech
    assert rows[0]["capability"] in (et.RUNTIME_EXISTS_UNSWEPT,
                                     et.POST_COMPOSITOR_EXISTS_UNSWEPT)
    distances = [x["distance"] for x in rows]
    assert distances == sorted(distances), "gaps are ordered by how far away"
    # reach alone would start somewhere else, and the report says so instead
    # of letting the sort win an argument it was never given
    assert r["derived_disagrees"] is True
    assert et.next_gap() == et.P_CAMERA_SPLINE
    assert r["director_priority"][0] == et.P_CAMERA_SPLINE
    spline = next(x for x in rows if x["primitive"] == et.P_CAMERA_SPLINE)
    assert spline["templates_waiting_count"] >= 9 and spline["distance"] == 1
    # an authored duration is not a gap a sweep could close, so it sorts last
    assert rows[-1]["capability"] == et.AUTHOR_DEFINED


def test_every_waiting_template_really_depends_on_that_primitive():
    for row in et.capability_report()["unmeasured"]:
        for tid in row["templates_waiting"]:
            assert row["primitive"] in et.components_of(tid)


# ── the camera is two primitives ────────────────────────────────────────────

def test_a_cut_and_a_spline_move_are_not_the_same_operator():
    """A cut has no duration to discover. A spline move is the whole
    question."""
    cut = et.PRIMITIVES[et.P_CAMERA_CUT]
    spline = et.PRIMITIVES[et.P_CAMERA_SPLINE]
    # They needed different evidence and got different answers: the cut is
    # settled by four frame identities, the spline still owes a whole
    # motion envelope.
    assert cut.measured and not spline.measured
    assert "four semantic situations" in spline.measurable_when


def test_cinematic_moves_use_the_spline_and_an_insert_uses_the_cut():
    for tid in ("SIDE_REPLAY", "PROJECTILE_REPLAY", "PROJECTILE_FOLLOW",
                "GRENADE_ARC", "ROCKET_FLYBY_BRIDGE", "WALL_XRAY"):
        assert et.P_CAMERA_SPLINE in et.components_of(tid), tid
        assert et.P_CAMERA_CUT not in et.components_of(tid), tid
    assert et.P_CAMERA_CUT in et.components_of("ENEMY_POV_INSERT")


def test_the_spline_sweep_must_vary_the_situation_not_only_the_duration():
    spline = et.PRIMITIVES[et.P_CAMERA_SPLINE]
    assert "four semantic situations" in spline.measurable_when, (
        "the sweep must vary the situation, not only the duration")


# ── the compositor already exists ───────────────────────────────────────────

def test_information_reveal_is_unswept_not_missing():
    """The compositor already draws information. Calling it missing sent the
    work to the wrong queue."""
    p = et.PRIMITIVES[et.P_INFORMATION_REVEAL]
    assert p.capability == et.POST_COMPOSITOR_EXISTS_UNSWEPT
    assert p.distance == et.CAPABILITY_DISTANCE[et.RUNTIME_EXISTS_UNSWEPT]
    assert p.distance < et.CAPABILITY_DISTANCE[et.RUNTIME_MISSING]
    for phase in ("reveal", "hold", "update", "hide"):
        assert phase in p.blocked_by or phase in p.measurable_when


def test_world_transform_really_is_missing():
    """The contrast that makes the reclassification meaningful."""
    assert et.PRIMITIVES[et.P_WORLD_TRANSFORM].capability == et.RUNTIME_MISSING


# ── authored duration is not discovered ─────────────────────────────────────

def test_authored_animation_has_no_primitive_envelope_to_find():
    p = et.PRIMITIVES[et.P_SYNTHETIC_ANIMATION]
    assert p.capability == et.AUTHOR_DEFINED and p.author_defined
    assert not et.AUTHORED_ANIMATIONS, "nothing has been authored yet"
    with pytest.raises(KeyError, match="not an oversight"):
        et.animation_envelope("XAERO_CROSS_SIGN")


def test_an_authored_piece_supplies_its_own_range():
    a = et.AuthoredAnimation("XAERO_CROSS_SIGN", authored_us=450 * MS,
                             musical_structure="two beats")
    env = a.envelope()
    assert env.hard_min_us == env.hard_max_us == 450 * MS, (
        "an animation does not stretch")
    assert env.provenance == et.DESIGN_ESTIMATE and not a.verified
    assert a.delivery_error_us is None


def test_what_the_primitive_verifies_is_fidelity_not_a_range():
    a = et.AuthoredAnimation("XAERO_CROSS_SIGN", authored_us=450 * MS,
                             delivered_us=450 * MS + et.FRAME_US)
    assert a.verified and a.delivery_error_us == et.FRAME_US
    assert a.envelope().provenance == et.RUNTIME_MEASURED


def test_two_pieces_of_the_same_kind_may_want_different_durations():
    """The reason a global envelope would be a fiction."""
    short = et.AuthoredAnimation("SIGN_SHORT", authored_us=450 * MS)
    long = et.AuthoredAnimation("SIGN_LONG", authored_us=1_200 * MS)
    assert short.envelope().hard_max_us != long.envelope().hard_max_us


# ── the director outranks the sort ──────────────────────────────────────────

def test_reach_does_not_get_to_choose_the_first_move():
    r = et.capability_report()
    assert r["derived_order"][0] != r["director_priority"][0]
    assert r["derived_disagrees"] is True
    assert et.next_gap() == r["director_priority"][0]
    assert r["director_priority_reason"]


# ── the cut is not proven by duration alone ─────────────────────────────────

def test_the_cut_is_proven_by_frame_identity_not_by_duration():
    """Duration evidence was never enough: two equal and opposite boundary
    offsets preserve the total while putting both cuts on the wrong frame.
    Four frame identities settle it."""
    cut = et.PRIMITIVES[et.P_CAMERA_CUT]
    assert cut.measured and cut.capability == et.MEASURED
    assert "identity the edit asked for" in cut.finding
    assert "active capture path produced" in cut.finding
    assert "never the part in doubt" in cut.finding
    assert et.P_CAMERA_CUT in ea_delivery_verified()


def ea_delivery_verified():
    from creative_suite.engine import effect_approval as ea
    return ea.status()["delivery_verified"]


def test_the_cut_was_measured_on_the_path_we_actually_ship():
    """Not on archive footage. A proxy's frame rate is not the pipeline's,
    and an earlier run of this proof proved only the proxy."""
    cal = et.PRIMITIVES[et.P_CAMERA_CUT].calibration
    assert cal is not None and cal.fps == 60
    assert cal is et.CALIBRATION_60_V2_CAPTURE
    assert "cut_identity" in cal.pipeline
    assert "active-path capture media" in cal.notes


def test_the_spline_needs_a_motion_envelope_not_a_duration_one():
    """300 ms across a small displacement and 300 ms across a large one are
    not the same shot."""
    m = et.PRIMITIVES[et.P_CAMERA_SPLINE].measurable_when
    for feature in ("translation distance", "path length",
                    "angular displacement", "field-of-view",
                    "subject screen displacement", "peak translational",
                    "smoothness", "coverage"):
        assert feature in m, feature
    assert "not the same shot" in m


def test_a_proxys_frame_rate_is_not_the_pipelines():
    """The regression this cost a wrong conclusion. Delivery calibration
    belongs to the path that produced it, and archive media is not that
    path."""
    cal = et.PRIMITIVES[et.P_CAMERA_CUT].calibration
    assert cal.fps == 60, "the active capture path delivers 60 distinct frames"
    assert not hasattr(et, "CALIBRATION_30_X264_CONCAT"), (
        "the 30 fps calibration described archive footage chosen for a "
        "canary, never a pipeline, and must not survive as one")
