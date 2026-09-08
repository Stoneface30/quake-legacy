"""Effects are time. Sync is a property of the finished choreography."""
from __future__ import annotations

from fractions import Fraction
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (temporal_operators as t, temporal_proofs as tpf,
                                   temporal_solver as ts)

MS = 1000


def _retime(label="src", src=2_000 * MS, lo=1_000 * MS, hi=4_000 * MS, **kw):
    kw.setdefault("rate_min", Fraction(1, 4))
    kw.setdefault("rate_max", Fraction(2, 1))
    return t.TemporalOperator(t.RETIME, label, lo, hi, src_in_us=0,
                              src_out_us=src, **kw)


# ── each kind's effect on edit time ─────────────────────────────────────────

def test_a_freeze_adds_exactly_its_duration():
    f = t.TemporalOperator(t.FREEZE, "hold", 100 * MS, 600 * MS)
    assert t.OperatorChoice(f, 300 * MS).edit_us == 300 * MS
    assert f.sign == 1 and f.src_span_us == 0      # it shows no new source


def test_a_trim_subtracts_time():
    tr = t.TemporalOperator(t.TRIM, "head", 0, 500 * MS)
    assert tr.sign == -1
    assert t.OperatorChoice(tr, 200 * MS).edit_us == -200 * MS
    assert tr.range_us == (-500 * MS, 0)


def test_a_transition_overlap_removes_net_sequence_time():
    """Two two-second scenes with a 300 ms overlap occupy 3.7 s, not 4.0 s."""
    a, b = _retime("a", 2_000 * MS), _retime("b", 2_000 * MS)
    ov = t.TemporalOperator(t.OVERLAP, "xfade", 0, 500 * MS)
    plan = t.TemporalPlan("s", 3_700 * MS, (
        t.OperatorChoice(a, 2_000 * MS), t.OperatorChoice(b, 2_000 * MS),
        t.OperatorChoice(ov, 300 * MS)))
    assert plan.total_us == 3_700 * MS and plan.exact
    assert plan.removed_us() == {t.OVERLAP: 300 * MS}
    assert plan.source_us == 4_000 * MS            # the source is still all there


def test_retime_occupies_source_over_rate():
    op = _retime(src=1_125 * MS, lo=2_045 * MS, hi=3_750 * MS,
                 rate_min=Fraction(3, 10), rate_max=Fraction(55, 100))
    c = t.OperatorChoice(op, 3_000 * MS)
    assert c.rate == Fraction(1_125, 3_000) == Fraction(3, 8)
    assert op.duration_for_rate(Fraction(3, 8)) == 3_000 * MS
    assert op.rate_for(2_250 * MS) == Fraction(1, 2)


def test_a_rate_outside_the_envelope_is_refused():
    op = _retime(src=1_000 * MS, lo=500 * MS, hi=5_000 * MS,
                 rate_min=Fraction(1, 2), rate_max=Fraction(1, 1))
    assert op.allows(1_500 * MS)                   # rate 2/3
    assert not op.allows(4_000 * MS)               # rate 1/4, below the floor
    with pytest.raises(ValueError, match="outside what"):
        t.OperatorChoice(op, 4_000 * MS)


def test_a_replay_inserts_its_own_time():
    """Shown after the original rather than under it, a replay adds duration."""
    fpv = _retime("fpv", 2_000 * MS, 1_800 * MS, 2_200 * MS)
    rep = t.TemporalOperator(t.REPLAY, "replay", 1_000 * MS, 3_000 * MS,
                             src_in_us=1_000 * MS, src_out_us=2_000 * MS,
                             rate_min=Fraction(1, 4), rate_max=Fraction(1, 1))
    plan = t.TemporalPlan("s", 4_000 * MS, (t.OperatorChoice(fpv, 2_000 * MS),
                                            t.OperatorChoice(rep, 2_000 * MS)))
    assert plan.total_us == 4_000 * MS
    assert plan.added_us()[t.REPLAY] == 2_000 * MS


def test_a_concurrent_operator_adds_no_time():
    """PIP runs under the main picture, so it costs nothing."""
    pip = t.TemporalOperator(t.REPLACE, "pip_enemy_pov", 500 * MS, 2_000 * MS,
                             src_in_us=0, src_out_us=1_000 * MS)
    assert pip.sign == 0 and pip.range_us == (0, 0)
    assert t.OperatorChoice(pip, 1_500 * MS).edit_us == 0


def test_a_sequential_pov_insert_does_add_time():
    seq = t.TemporalOperator(t.INSERT, "enemy_pov_cut", 500 * MS, 2_000 * MS)
    assert t.OperatorChoice(seq, 1_200 * MS).edit_us == 1_200 * MS


def test_a_duration_range_is_never_negative():
    with pytest.raises(ValueError, match="never negative"):
        t.TemporalOperator(t.FREEZE, "bad", -100, 500)


# ── the plan ────────────────────────────────────────────────────────────────

def test_duration_accounting_is_exact_and_itemised():
    ops = (t.OperatorChoice(_retime("fpv", 2_000 * MS), 2_000 * MS),
           t.OperatorChoice(t.TemporalOperator(t.FREEZE, "f", 0, 900 * MS), 400 * MS),
           t.OperatorChoice(t.TemporalOperator(t.OVERLAP, "ov", 0, 900 * MS), 150 * MS))
    plan = t.TemporalPlan("s", 2_250 * MS, ops)
    assert plan.total_us == 2_000 * MS + 400 * MS - 150 * MS == 2_250 * MS
    assert plan.exact and plan.residual_us == 0
    assert plan.added_us() == {t.RETIME: 2_000 * MS, t.FREEZE: 400 * MS}
    assert plan.removed_us() == {t.OVERLAP: 150 * MS}


def test_a_plan_that_misses_the_slot_says_by_how_much():
    plan = t.TemporalPlan("s", 3_000 * MS,
                          (t.OperatorChoice(_retime("a", 2_000 * MS), 2_000 * MS),))
    assert not plan.exact and plan.residual_us == -1_000 * MS


def test_the_timeline_places_every_operator_and_an_overlap_pulls_back():
    a = _retime("a", 2_000 * MS)
    ov = t.TemporalOperator(t.OVERLAP, "ov", 0, 500 * MS)
    b = _retime("b", 2_000 * MS)
    plan = t.TemporalPlan("s", 3_700 * MS, (
        t.OperatorChoice(a, 2_000 * MS), t.OperatorChoice(ov, 300 * MS),
        t.OperatorChoice(b, 2_000 * MS)))
    rows = plan.timeline()
    assert rows[0]["end_us"] == 2_000 * MS
    assert rows[2]["start_us"] == 1_700 * MS       # b starts inside a's tail
    assert rows[2]["end_us"] == plan.slot_us


# ── sync bias ───────────────────────────────────────────────────────────────

def test_the_hero_preference_puts_the_music_ahead_of_the_frag():
    a = t.AnchorConstraint("frag", 5_000 * MS, "HERO")
    assert a.preferred_delta_us == -15 * MS
    assert a.target_us == 5_015 * MS          # the frag lands into the music
    assert a.residual_us(5_015 * MS) == 0
    assert a.satisfied(5_010 * MS)


def test_a_stutter_frame_wants_the_attack_itself_not_the_hero_bias():
    """The -15 ms preference is the HERO's. Applying it everywhere would drag
    every held frame off its own attack."""
    s = t.AnchorConstraint("stutter#1", 1_000 * MS, "STUTTER_ATTACK")
    assert s.preferred_delta_us == 0 and s.target_us == 1_000 * MS
    for kind in ("CAMERA_CUT", "MATERIAL_FLASH", "MORPH_PEAK",
                 "FREEZE_RELEASE", "TRANSITION_HANDOFF"):
        assert t.PREFERRED_DELTA_US[kind] == 0
    assert t.PREFERRED_DELTA_US["HERO"] == -15 * MS


def test_anchor_residuals_are_measured_on_the_finished_composition():
    fpv = _retime("fpv", 2_000 * MS, peak_ratio=1.0)
    freeze = t.TemporalOperator(t.FREEZE, "hold", 0, 900 * MS)
    frag = _retime("frag", 1_000 * MS, 500 * MS, 2_000 * MS, peak_ratio=0.5)
    anchor = t.AnchorConstraint("frag", 3_015 * MS, "HERO", 25 * MS)
    plan = t.TemporalPlan("s", 4_000 * MS, (
        t.OperatorChoice(fpv, 2_000 * MS), t.OperatorChoice(freeze, 500 * MS),
        t.OperatorChoice(frag, 1_500 * MS)), (anchor,))
    # peak = 2000 + 500 + 0.5*1500 = 3250; target = 3015 + 15 = 3030
    assert plan.event_us("frag") == 3_250 * MS
    assert plan.anchor_report()[0]["residual_us"] == 220 * MS
    assert plan.anchor_report()[0]["delta_us"] == -235 * MS
    assert not plan.anchors_satisfied


def test_inserting_a_freeze_before_the_hero_moves_it():
    """The regression this whole model exists to prevent: syncing the hero and
    THEN adding a freeze in front of it silently breaks the sync."""
    fpv = _retime("fpv", 2_000 * MS, peak_ratio=1.0)
    frag = _retime("frag", 1_000 * MS, 500 * MS, 2_000 * MS, peak_ratio=0.5)
    anchor = t.AnchorConstraint("frag", 2_735 * MS, "HERO", 25 * MS)
    synced = t.TemporalPlan("s", 3_500 * MS, (
        t.OperatorChoice(fpv, 2_000 * MS), t.OperatorChoice(frag, 1_500 * MS)),
        (anchor,))
    assert synced.anchors_satisfied
    freeze = t.TemporalOperator(t.FREEZE, "hold", 0, 900 * MS)
    later = t.TemporalPlan("s", 3_900 * MS, (
        t.OperatorChoice(fpv, 2_000 * MS), t.OperatorChoice(freeze, 400 * MS),
        t.OperatorChoice(frag, 1_500 * MS)), (anchor,))
    assert not later.anchors_satisfied, "a freeze before the hero moves the hero"
    assert later.anchor_report()[0]["residual_us"] == 400 * MS


# ── composed time map ───────────────────────────────────────────────────────

def test_the_composed_map_preserves_demo_truth():
    fpv = _retime("fpv", 2_000 * MS, peak_ratio=1.0)
    freeze = t.TemporalOperator(t.FREEZE, "hold", 0, 900 * MS)
    plan = t.TemporalPlan("s", 2_500 * MS, (t.OperatorChoice(fpv, 2_000 * MS),
                                            t.OperatorChoice(freeze, 500 * MS)))
    cm = t.compose(plan)
    assert cm.total_us == plan.slot_us and cm.song_locked
    # source instants are read back through the rate; demo time is unchanged
    assert cm.demo_at(0) == (0, t.SOURCE_TRUTH)
    assert cm.demo_at(1_000 * MS) == (1_000 * MS, t.SOURCE_TRUTH)
    assert cm.spans[0].src_in_us == 0 and cm.spans[0].src_out_us == 2_000 * MS
    # the freeze shows no new source at all
    assert cm.demo_at(2_200 * MS)[1] == t.PRESENTATION


def test_the_map_refuses_an_unresolved_plan():
    plan = t.TemporalPlan("s", 5_000 * MS,
                          (t.OperatorChoice(_retime("a", 2_000 * MS), 2_000 * MS),))
    with pytest.raises(ValueError, match="finished choreography"):
        t.compose(plan)


def test_a_slowed_span_maps_edit_time_back_to_source_time():
    op = _retime("slow", 1_000 * MS, 1_000 * MS, 4_000 * MS)
    plan = t.TemporalPlan("s", 2_000 * MS, (t.OperatorChoice(op, 2_000 * MS),))
    cm = t.compose(plan)
    assert cm.spans[0].rate == Fraction(1, 2)
    assert cm.demo_at(1_000 * MS) == (500 * MS, t.SOURCE_TRUTH)   # half speed


# ── elasticity ──────────────────────────────────────────────────────────────

def test_elasticity_is_the_range_a_moment_can_honestly_occupy():
    ops = [_retime("fpv", 2_150 * MS, 1_800 * MS, 2_300 * MS),
           t.TemporalOperator(t.FREEZE, "f", 100 * MS, 500 * MS),
           t.TemporalOperator(t.OVERLAP, "ov", 0, 500 * MS)]
    el = t.elasticity(ops)
    assert el.min_us == 1_800 * MS + 100 * MS - 500 * MS
    assert el.max_us == 2_300 * MS + 500 * MS - 0
    assert el.fits(2_500 * MS) and not el.fits(3_500 * MS)
    assert el.span_us == el.max_us - el.min_us


def test_a_slot_search_uses_the_envelope_not_the_raw_duration():
    """2.9 s of source can honestly fill 5.85 s, which raw duration would
    have rejected outright."""
    rep = tpf.double_air_rocket()
    assert rep.elasticity.min_us < 5_850 * MS < rep.elasticity.max_us
    assert rep.elasticity.min_us > 0
    raw = rep.best.plan.source_us
    assert raw < 5_850 * MS, "the source is shorter than the slot it fills"


# ── the solver ──────────────────────────────────────────────────────────────

def test_the_solver_hits_the_slot_exactly():
    rep = tpf.double_air_rocket()
    assert rep.feasible and rep.best is not None
    assert rep.best.plan.total_us == rep.slot_us
    assert rep.best.plan.exact


def test_the_solver_is_deterministic():
    a, b = tpf.double_air_rocket(), tpf.double_air_rocket()
    assert a.best.plan.plan_hash == b.best.plan.plan_hash
    assert json.dumps(a.to_dict(), sort_keys=True) == json.dumps(b.to_dict(), sort_keys=True)


def test_a_slot_outside_the_envelope_is_refused_with_a_reason():
    ops = [t.TemporalOperator(t.FREEZE, "f", 100 * MS, 300 * MS)]
    rep = ts.solve("s", 9_000 * MS, ops)
    assert not rep.feasible
    assert "can only occupy" in rep.reason
    assert rep.best is None


def test_the_solver_never_leaves_the_hard_limits():
    for rep in tpf.all_reports():
        if not rep.best:
            continue
        for c in rep.best.plan.choices:
            assert c.operator.hard_min_us <= c.duration_us <= c.operator.hard_max_us


def test_the_objective_keeps_its_components():
    rep = tpf.double_air_rocket()
    o = rep.best.objective.to_dict()
    for k in ("hero_residual_us", "preferred_deviation", "effect_density",
              "complexity", "unsatisfied_anchors", "total"):
        assert k in o


def test_an_unreachable_anchor_is_reported_not_fudged():
    """Duration can fit while the musical relationship cannot. The solver says
    so instead of stretching an effect past its limits."""
    ops = [t.TemporalOperator(t.FREEZE, "hold", 500 * MS, 500 * MS),
           _retime("frag", 1_000 * MS, 1_500 * MS, 1_500 * MS, peak_ratio=1.0)]
    rep = ts.solve("s", 2_000 * MS, ops,
                   anchors=(t.AnchorConstraint("frag", 500 * MS, "HERO", 20 * MS),))
    assert rep.feasible                      # the duration closes
    assert not rep.anchors_reachable         # the anchor does not
    assert "musical relationship does not" in rep.reason
    assert rep.best.objective.unsatisfied_anchors == 1


# ── music-derived effect duration ───────────────────────────────────────────

def test_a_stutters_duration_comes_from_the_musical_figure():
    attacks = (0, 180 * MS, 360 * MS, 540 * MS)
    op = ts.stutter_from_gesture("stutter", attacks, release_us=720 * MS)
    assert op.hard_min_us == op.hard_max_us == 720 * MS, "the figure fixes it"
    assert op.repeats_min == op.repeats_max == 4
    assert op.dwell_min_us == 120 * MS       # clamped to the max dwell
    assert op.anchor_kind == "STUTTER_ATTACK"
    with pytest.raises(ValueError, match="at least two attacks"):
        ts.stutter_from_gesture("x", (0,))


def test_gesture_anchors_want_the_attacks_themselves():
    attacks = (0, 180 * MS, 360 * MS)
    anchors = ts.gesture_anchors("stutter", attacks)
    assert [a.anchor_us for a in anchors] == list(attacks)
    assert all(a.target_us == a.anchor_us for a in anchors)   # no hero bias
    assert all(a.kind == "STUTTER_ATTACK" for a in anchors)


# ── the five proofs ─────────────────────────────────────────────────────────

def test_all_five_proofs_fit_exactly_and_land_their_anchors():
    s = tpf.summary()
    assert len(s["proofs"]) == 5
    for row in s["proofs"]:
        assert row["feasible"], row["slot"]
        assert row["exact"], row["slot"]
        assert row["final_ms"] == row["slot_ms"], row["slot"]
        for a in row["anchors"]:
            assert a["satisfied"], (row["slot"], a)


def test_the_overlap_proof_removes_time_without_accelerating_anything():
    rep = tpf.transition_overlap()
    d = rep.best.plan.to_dict()
    assert d["removed_us"] == {t.OVERLAP: 150 * MS}
    assert d["source_us"] == 4_000 * MS and d["total_us"] == 3_850 * MS
    for c in d["choices"]:
        if c["rate"]:
            assert Fraction(c["rate"]) == 1, "neither scene was sped up"


def test_the_rocket_proof_fills_a_slot_longer_than_its_source():
    rep = tpf.double_air_rocket()
    d = rep.best.plan.to_dict()
    assert d["total_us"] == 5_850 * MS
    assert sum(d["added_us"].values()) - sum(d["removed_us"].values()) == 5_850 * MS
    assert d["anchors"][0]["satisfied"]


def test_no_temporal_debt_is_repaid_by_acceleration():
    """Time a freeze or a slow replay spends is spent. Nothing later runs fast
    to claw it back."""
    for rep in tpf.all_reports():
        if not rep.best:
            continue
        for c in rep.best.plan.choices:
            r = c.rate
            if r is not None and c.operator.kind in (t.REPLAY,):
                assert r <= 1, "a replay never runs faster than life to repay time"


# ── song-locked mode ────────────────────────────────────────────────────────

def test_the_song_cannot_be_moved_to_fit_the_picture():
    lock = t.SongLock("h" * 64, 258_000 * MS, "4:18.000")
    assert lock.duration_us == 258_000 * MS
    with pytest.raises(t.SongMoved, match="stays"):
        lock.retimed(260_000 * MS)
    with pytest.raises(t.SongMoved, match="does not fit inside the song"):
        lock.slot(250_000 * MS, 260_000 * MS)
    assert lock.slot(0, 5_850 * MS) == (0, 5_850 * MS)


def test_slots_must_tile_the_song_without_gap_or_overlap():
    lock = t.SongLock("h" * 64, 10_000 * MS)
    assert lock.check_tiling([(0, 4_000 * MS), (4_000 * MS, 10_000 * MS)]) == []
    gap = lock.check_tiling([(0, 4_000 * MS), (4_500 * MS, 10_000 * MS)])
    assert any("gap of" in c for c in gap)
    over = lock.check_tiling([(0, 4_500 * MS), (4_000 * MS, 10_000 * MS)])
    assert any("overlap" in c for c in over)
    short = lock.check_tiling([(0, 4_000 * MS)])
    assert any("the song ends at" in c for c in short)


def test_song_locked_verification_catches_a_plan_that_misses_its_slot():
    lock = t.SongLock("h" * 64, 4_000 * MS)
    good = t.TemporalPlan("a", 4_000 * MS,
                          (t.OperatorChoice(_retime("a", 4_000 * MS), 4_000 * MS),))
    assert t.verify_song_locked(lock, [good]) == []
    bad = t.TemporalPlan("a", 4_000 * MS,
                         (t.OperatorChoice(_retime("a", 2_000 * MS), 2_000 * MS),))
    problems = t.verify_song_locked(lock, [bad])
    assert any("occupies 2000000 us of a 4000000 us slot" in p for p in problems)


# ── the two layers meet ─────────────────────────────────────────────────────

def test_choreography_elements_take_their_times_from_the_composed_timeline():
    from creative_suite.engine import choreography as ch
    plan = tpf.double_air_rocket().best.plan
    els = ch.elements_from_temporal(plan)
    assert els, "the solved plan yields elements"
    assert all(e.peak_us is not None for e in els)
    # the last element ends where the composition ends, overlaps excluded
    spans = [(e.start_us, e.end_us) for e in els]
    assert spans[0][0] == 0
    assert all(a[1] <= b[1] for a, b in zip(spans, spans[1:]))
    # and every one of them fits in a plan built on the same slot
    cp = ch.ChoreographyPlan("s", 0, max(e.end_us for e in els), "DROP",
                             elements=els)
    assert cp.lanes_used and cp.density()["visual_events_per_s"] > 0
    replay = next(e for e in els if e.action == "side_replay")
    assert replay.peak_us == plan.event_us("side_replay")


def test_readiness_now_requires_the_temporal_solver():
    from creative_suite.engine import (choreography as ch, choreography_proofs as cp2,
                                       creative_corpus as cc)
    without = ch.assess_readiness(
        corpus_entries=len(cc.CORPUS), lanes_covered=len(ch.LANES),
        proofs_built=len(cp2.PROOFS), gameplay_truth_ready=True,
        music_library_ready=True, temporal_proofs_built=0)
    assert not without.may_shortlist_songs and not without.temporal_solver_ready
    assert any("temporal" in b for b in without.blockers)
    f = ch.temporal_effect_fillability()
    with_solver = ch.assess_readiness(
        corpus_entries=len(cc.CORPUS), lanes_covered=len(ch.LANES),
        proofs_built=len(cp2.PROOFS), gameplay_truth_ready=True,
        music_library_ready=True, temporal_proofs_built=len(tpf.PROOFS),
        measured_templates=f["measured"], measured_scales=f["measured_scales"])
    assert with_solver.may_shortlist_songs and with_solver.temporal_solver_ready


# ── accuracy and direction are different axes ───────────────────────────────

def test_the_hero_delta_follows_the_projects_convention():
    """delta = music_anchor - gameplay_event. Negative means the music leads
    and the frag lands into it, which is what the director asked for."""
    a = t.AnchorConstraint("frag", 5_000 * MS, "HERO")
    assert a.preferred_delta_us == -15 * MS
    assert a.target_us == 5_015 * MS, "the frag lands AFTER the anchor"
    assert a.delta_us(5_015 * MS) == -15 * MS
    assert a.residual_us(5_015 * MS) == 0


def test_a_millisecond_off_on_the_wrong_side_loses_to_fourteen_on_the_right():
    """+1 ms can be mathematically excellent and still be the wrong side."""
    a = t.AnchorConstraint("frag", 5_000 * MS, "HERO")
    late = 4_999 * MS          # delta +1 ms: the frag arrives before the music
    good = 5_014 * MS          # delta -14 ms: the music leads into it
    assert a.delta_us(late) == 1 * MS and a.direction_grade(late) == t.WRONG_SIDE
    assert a.delta_us(good) == -14 * MS and a.direction_grade(good) == t.PREFERRED
    assert abs(a.residual_us(late)) > abs(a.residual_us(good))


def test_the_direction_band_is_per_event_class():
    hero = t.AnchorConstraint("frag", 5_000 * MS, "HERO")
    stut = t.AnchorConstraint("s#1", 5_000 * MS, "STUTTER_ATTACK")
    assert hero.band_us == (-20 * MS, 0)
    assert stut.band_us is None and stut.preferred_delta_us == 0
    assert stut.direction_grade(5_000 * MS) == t.NO_PREFERENCE
    assert hero.direction_grade(5_005 * MS) == t.ACCEPTABLE   # -5 ms, in band
    assert hero.direction_grade(5_030 * MS) == t.WRONG_SIDE   # -30 ms, past it


def test_the_solver_reports_both_axes_and_penalises_the_wrong_side():
    rep = tpf.double_air_rocket()
    o = rep.best.objective
    assert o.hero_direction == t.PREFERRED
    assert -20 * MS <= o.hero_delta_us <= 0, o.hero_delta_us
    assert o.wrong_side == 0
    d = o.to_dict()
    assert "hero_delta_us" in d and "hero_residual_us" in d


def test_every_proof_lands_its_hero_on_the_preferred_side():
    for rep in tpf.all_reports():
        if not rep.best:
            continue
        for row in rep.best.plan.anchor_report():
            if row["kind"] == "HERO" and row["required"]:
                assert row["direction"] == t.PREFERRED, (rep.slot_id, row)
