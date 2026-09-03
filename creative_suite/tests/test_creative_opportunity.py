"""Action creates the opportunity. Time never invents it."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (creative_opportunity as co, effect_templates as et,
                                   temporal_budget as tb, visual_focus as vf)

MS = 1000


def _rocket(**kw):
    base = dict(moment_ref="h@1125", kinds=("frag",), weapon="ROCKET",
                projectile_path=True, projectile_recorded_fraction=0.02,
                relative_speed_u_s=980, round_result="WIN",
                teammates=2, opponents=3, alive_self=1, alive_enemy=2,
                source_useful_us=2_900 * MS)
    base.update(kw)
    return co.MomentEvidence(**base)


def _lg(**kw):
    base = dict(moment_ref="h@980", kinds=("frag",), weapon="LIGHTNING",
                lg_contacts=33, round_result="LOSS", damage_by_user=140)
    base.update(kw)
    return co.MomentEvidence(**base)


def _phased(**kw):
    """A one-versus-three that opens with a reveal, tracks for four seconds,
    then pays off on the kill. Three phases, one moment."""
    base = dict(moment_ref="h@1", kinds=("frag",), weapon="LIGHTNING",
                lg_contacts=33, alive_self=1, alive_enemy=3,
                round_result="WIN", damage_by_user=180,
                victim_effective_hp=200,
                scene_start_us=0, scene_end_us=9_000 * MS,
                hero_us=8_200 * MS,
                lg_track_start_us=3_200 * MS, lg_track_end_us=7_600 * MS,
                source_useful_us=9_000 * MS)
    base.update(kw)
    return co.MomentEvidence(**base)


# ── the invariant ───────────────────────────────────────────────────────────

def test_a_budget_cannot_search_the_library_for_something_to_fill_a_gap():
    """The regression this whole layer exists to prevent."""
    j = tb.Justification("hero", "projectile", ("frag", "projectile_path"))
    with pytest.raises(tb.NoOpportunity, match="creative opportunities the action"):
        tb.build("S", 8_400 * MS, 4_250 * MS, 7_830 * MS, j)


def test_a_deficit_with_no_earned_treatment_does_not_fit():
    """Time is short and the action earned nothing that adds time. The answer
    is that the moment belongs elsewhere."""
    bare = co.MomentEvidence("h@1", kinds=("chat",))
    ops = co.opportunities_for(bare)
    assert ops == ()
    j = tb.Justification("hero", "chat", ())
    b = tb.build("S", 8_400 * MS, 1_000 * MS, 7_830 * MS, j, opportunities=ops)
    assert b.verdict == "DOES_NOT_FIT" and not b.options
    assert "does not fit this slot" in b.explain()


def test_the_budget_only_sees_what_the_action_earned():
    ops = co.opportunities_for(_lg())
    earned = set(co.allowed_templates(ops))
    j = tb.Justification("duel", "duel", ("frag", "lg_engagement", "damage_ledger"))
    b = tb.build("S", 8_400 * MS, 4_250 * MS, 7_830 * MS, j, opportunities=ops)
    assert {o.template_id for o in b.options} == earned
    assert "WORLD_STRIP" not in earned and "ENEMY_REVEAL_STEP" not in earned


# ── evidence decides eligibility ────────────────────────────────────────────

def test_an_opportunity_needs_evidence_and_a_reason():
    with pytest.raises(ValueError, match="what in the action earns it"):
        co.CreativeOpportunity("m", co.HERO_PROJECTILE, "  ", ("frag",), ())
    with pytest.raises(ValueError, match="without evidence is a wish"):
        co.CreativeOpportunity("m", co.HERO_PROJECTILE, "because", (), ())


def test_no_projectile_path_no_projectile_treatments():
    ops = co.opportunities_for(_rocket(projectile_path=False,
                                       projectile_recorded_fraction=None))
    kinds = {o.opportunity_type for o in ops}
    assert co.HERO_PROJECTILE not in kinds and co.PROJECTILE_FLYBY not in kinds


def test_a_flyby_needs_an_actually_close_pass():
    far = co.opportunities_for(_rocket(projectile_close_pass_u=900.0))
    near = co.opportunities_for(_rocket(projectile_close_pass_u=180.0))
    assert co.PROJECTILE_FLYBY not in {o.opportunity_type for o in far}
    assert co.PROJECTILE_FLYBY in {o.opportunity_type for o in near}


def test_a_wall_xray_needs_geometry_that_actually_hides_something():
    plain = co.opportunities_for(_rocket())
    hidden = co.opportunities_for(_rocket(occluded_by_geometry=True))
    assert co.OCCLUDED_SKILL not in {o.opportunity_type for o in plain}
    assert co.OCCLUDED_SKILL in {o.opportunity_type for o in hidden}


def test_a_damage_ledger_needs_damage_worth_showing():
    trivial = co.opportunities_for(_rocket(damage_by_user=7))
    real = co.opportunities_for(_rocket(damage_by_user=170))
    assert co.DAMAGE_STORY not in {o.opportunity_type for o in trivial}
    assert co.DAMAGE_STORY in {o.opportunity_type for o in real}


def test_hero_then_death_needs_the_death_to_be_part_of_the_beat():
    late = co.opportunities_for(_rocket(death_after_us=9_000 * MS))
    soon = co.opportunities_for(_rocket(death_after_us=800 * MS))
    assert co.HERO_THEN_DEATH not in {o.opportunity_type for o in late}
    assert co.HERO_THEN_DEATH in {o.opportunity_type for o in soon}


def test_a_one_v_one_does_not_earn_three_enemy_reveals():
    """Even if the music has three attacks."""
    duel = co.opportunities_for(_rocket(alive_self=1, alive_enemy=1))
    assert co.ONE_VX_REVEAL not in {o.opportunity_type for o in duel}
    outnumbered = co.opportunities_for(_rocket(alive_self=1, alive_enemy=3))
    assert co.ONE_VX_REVEAL in {o.opportunity_type for o in outnumbered}


# ── result truth gates the treatment, not the eligibility ───────────────────

def test_a_lost_one_v_x_is_usable_but_forbids_the_payoff():
    lost = next(o for o in co.opportunities_for(
        _rocket(round_result="LOSS", alive_enemy=3))
        if o.opportunity_type == co.ONE_VX_REVEAL)
    assert "ROUND_WIN_RELEASE" in lost.forbidden_templates
    assert "ROUND_WIN_RELEASE" not in lost.allowed_templates
    assert lost.grammar("REVEAL_AND_PAYOFF") is None
    assert lost.grammar("WORLD_REVEAL") is not None, "the threat still reads"
    won = next(o for o in co.opportunities_for(_rocket(alive_enemy=3))
               if o.opportunity_type == co.ONE_VX_REVEAL)
    assert won.grammar("REVEAL_AND_PAYOFF") is not None


def test_a_round_win_payoff_requires_a_won_round():
    lost = co.opportunities_for(_rocket(round_result="LOSS"))
    unknown = co.opportunities_for(_rocket(round_result="UNKNOWN"))
    won = co.opportunities_for(_rocket(round_result="WIN"))
    assert co.ROUND_WIN_PAYOFF not in {o.opportunity_type for o in lost}
    assert co.ROUND_WIN_PAYOFF not in {o.opportunity_type for o in unknown}
    assert co.ROUND_WIN_PAYOFF in {o.opportunity_type for o in won}


# ── one action, several legitimate treatments ───────────────────────────────

def test_a_moment_offers_several_grammars_of_different_lengths():
    hero = next(o for o in co.opportunities_for(_rocket())
                if o.opportunity_type == co.HERO_PROJECTILE)
    names = [g.name for g in hero.grammars]
    assert "PURE_FPV" in names and "FPV_FREEZE_REPLAY" in names
    pure = hero.grammar("PURE_FPV").elasticity
    full = hero.grammar("FPV_FREEZE_REPLAY").elasticity
    assert full.max_us > pure.max_us, "the fuller treatment reaches further"
    assert hero.grammar("PURE_FPV").fits(2_000 * MS)
    assert not hero.grammar("PURE_FPV").fits(12_000 * MS)


def test_a_slot_selects_among_grammars_rather_than_padding_one():
    ops = co.opportunities_for(_rocket())
    short = co.grammars_fitting(ops, 1_500 * MS)
    long = co.grammars_fitting(ops, 7_200 * MS)
    assert short and long
    assert {g.name for _k, g in short} != {g.name for _k, g in long}


def test_the_same_moment_can_be_refused_by_one_slot_and_accepted_by_another():
    ops = co.opportunities_for(_rocket())
    assert not co.grammars_fitting(ops, 45_000 * MS), "no treatment runs that long"
    assert co.grammars_fitting(ops, 5_800 * MS)


# ── the action decides the vocabulary ───────────────────────────────────────

def test_different_actions_produce_different_vocabularies():
    rocket = co.allowed_templates(co.opportunities_for(_rocket()))
    lg = co.allowed_templates(co.opportunities_for(_lg()))
    assert set(rocket) != set(lg)
    assert "SIDE_REPLAY" in rocket and "SIDE_REPLAY" not in lg
    assert len(rocket) > len(lg), "a projectile kill earns more than tracking"


def test_tracking_protects_only_its_own_interval():
    """The skill is hidden by decoration DURING the tracking. Before and after
    it, the same decoration hides nothing."""
    ev = _phased()
    ops = co.opportunities_for(ev)
    tracking = next(o for o in ops if o.opportunity_type == co.LG_TRACKING)
    focus = next(f for f in tracking.focuses if f.subject == vf.SKILL_TRACKING)
    assert (focus.start_us, focus.end_us) == (3_200 * MS, 7_600 * MS)
    assert tracking.forbidden_templates == ()
    ok, _ = tracking.permits("WORLD_STRIP", 1_500 * MS)
    assert ok, "a world strip before the tracking hides no tracking"
    ok, why = tracking.permits("WORLD_STRIP", 5_000 * MS)
    assert not ok and "SKILL_TRACKING" in why


def test_a_reveal_before_the_tracking_is_allowed():
    """The user's scene: strip the map and show three enemies, THEN go clean."""
    ops = co.opportunities_for(_phased())
    assert "ENEMY_REVEAL_STEP" in co.allowed_templates(ops, at_us=1_500 * MS)
    windows = co.windows_for(ops, "ENEMY_REVEAL_STEP", (0, 9_000 * MS))
    assert windows and windows[0][0] == 0
    assert windows[0][1] <= 3_200 * MS, "the reveal must end when tracking starts"


def test_the_same_effect_during_the_tracking_is_refused():
    ops = co.opportunities_for(_phased())
    assert "ENEMY_REVEAL_STEP" not in co.allowed_templates(ops, at_us=5_000 * MS)
    assert "WORLD_STRIP" not in co.allowed_templates(ops, at_us=5_000 * MS)


def test_an_effect_after_the_tracking_is_valid_again():
    """The payoff on the kill is not forbidden by a duel that already ended."""
    ops = co.opportunities_for(_phased())
    late = co.allowed_templates(ops, at_us=8_500 * MS)
    assert "MATERIAL_FLASH" in late
    flash = co.windows_for(ops, "MATERIAL_FLASH", (0, 9_000 * MS))
    assert any(a >= 7_600 * MS for a, _b in flash)


def test_a_veto_that_covered_the_whole_moment_would_lose_the_scene():
    """Regression. The scene has a legal treatment in all three phases; a
    blanket veto collapses that to one."""
    ops = co.opportunities_for(_phased())
    phases = [co.allowed_templates(ops, at_us=t * MS)
              for t in (1_500, 5_000, 8_500)]
    assert all(p for p in phases), "every phase keeps a vocabulary"
    assert phases[0] != phases[1], "the phases are not interchangeable"


# ── editorial weight and repetition ─────────────────────────────────────────

def test_signature_effects_are_marked_so_they_are_not_spent_casually():
    for tid in ("PLAYER_FREEZE_POSE", "MAP_CONSTRUCTION", "WORLD_MORPH_BRIDGE"):
        weight, policy = co.editorial_weight(tid)
        assert weight == co.SIGNATURE and policy == co.ONCE_PER_EPISODE
        assert co.POLICY_BUDGET[policy] == 1
    for tid in ("FREEZE_HOLD", "MOVEMENT_ACCENT", "MATERIAL_FLASH"):
        assert co.editorial_weight(tid)[1] == co.FREQUENT


def test_a_grammar_reports_its_heaviest_editorial_weight():
    hero = next(o for o in co.opportunities_for(_rocket(alive_enemy=3))
                if o.opportunity_type == co.ONE_VX_REVEAL)
    plain = hero.grammar("THREAT_PLAIN")
    heavy = hero.grammar("WORLD_REVEAL")
    order = {w: i for i, w in enumerate(co.WEIGHTS)}
    assert order[heavy.heaviest_weight] > order[plain.heaviest_weight]


def test_a_budget_prefers_the_lighter_tool_among_equals():
    ops = co.opportunities_for(_rocket(alive_enemy=3))
    j = tb.Justification("1vx", "projectile",
                         ("frag", "projectile_path", "alive_state",
                          "round_result", "team_state", "movement"))
    b = tb.build("S", 9_000 * MS, 3_000 * MS, 8_700 * MS, j, opportunities=ops)
    if b.solutions:
        order = {w: i for i, w in enumerate(co.WEIGHTS)}
        first = max(order[co.editorial_weight(i)[0]] for i in b.solutions[0].options)
        last = max(order[co.editorial_weight(i)[0]] for i in b.solutions[-1].options)
        assert first <= last, "signature effects are not reached for first"


# ── grammars carry their honesty forward ────────────────────────────────────

def test_a_grammar_reports_its_weakest_timing_provenance():
    hero = next(o for o in co.opportunities_for(_rocket())
                if o.opportunity_type == co.HERO_PROJECTILE)
    pure = hero.grammar("PURE_FPV")
    assert pure.weakest_provenance in (et.SYNTHETIC_TEST, et.RUNTIME_MEASURED)
    full = hero.grammar("FPV_FREEZE_REPLAY")
    assert et.PROVENANCE_RANK[full.weakest_provenance] \
        <= et.PROVENANCE_RANK[pure.weakest_provenance]


# ── moment-specific envelopes ────────────────

def test_the_same_grammar_gets_different_envelopes_on_two_moments():
    """A grammar is reusable; the time it may occupy is not. Nine seconds of
    source and one second of source cannot offer the same range."""
    ops = co.opportunities_for(_phased())
    g = next(g for o in ops for g in o.grammars)
    long_w = co.SourceWindow(useful_us=9_000 * MS, hero_offset_us=8_200 * MS,
                             replay_source_us=1_200 * MS)
    short_w = co.SourceWindow(useful_us=1_000 * MS, hero_offset_us=700 * MS,
                              min_recognition_us=600 * MS)
    assert g.envelope_for(long_w).max_us > g.envelope_for(short_w).max_us
    generic = g.elasticity
    assert g.envelope_for(short_w).max_us < generic.max_us, (
        "the library range must not survive contact with a short source")


def test_source_context_stops_a_destructive_trim():
    """An action needs time to be recognised. A window cannot be asked for
    less than that, and one that has less than the floor refuses outright."""
    w = co.SourceWindow(useful_us=2_000 * MS, min_recognition_us=600 * MS,
                        min_aftermath_us=150 * MS)
    assert w.floor_us == 750 * MS
    with pytest.raises(ValueError, match="comprehensible"):
        co.SourceWindow(useful_us=400 * MS, min_recognition_us=600 * MS)


def test_a_replay_grammar_is_unavailable_without_replay_source():
    ops = co.opportunities_for(_rocket())
    g = next((g for o in ops for g in o.grammars
              if any("REPLAY" in i for i in g.templates)), None)
    assert g is not None
    none_w = co.SourceWindow(useful_us=2_900 * MS, replay_source_us=0)
    assert g.envelope_for(none_w).max_us == 0
    assert not g.fits(4_000 * MS, none_w)


# ── heuristics are not laws ──────────────────

def test_a_creative_threshold_says_it_is_a_judgement():
    h = co.heuristic("flyby_close_pass_u")
    assert h.provenance == co.ASSUMED
    assert h.to_dict()["kind"] == co.CREATIVE_HEURISTIC
    assert h.reason and not h.overridden


def test_the_director_may_move_a_heuristic_but_not_a_truth():
    original = co.heuristic("lg_burst_contacts").effective
    try:
        co.override_heuristic("lg_burst_contacts", 40)
        kinds = {o.opportunity_type for o in co.opportunities_for(_lg())}
        assert co.LG_TRACKING not in kinds, "33 contacts no longer clears 40"
    finally:
        co.override_heuristic("lg_burst_contacts", None)
    assert co.heuristic("lg_burst_contacts").effective == original
    lost = co.opportunities_for(
        _lg(round_result="LOSS", alive_self=1, alive_enemy=3))
    assert any("ROUND_WIN_RELEASE" in o.forbidden_templates for o in lost), (
        "a lost round refuses a victory release no matter what the director "
        "sets, because it would be a lie rather than a preference")


def test_an_opportunity_reports_strength_not_just_existence():
    strong = co.opportunities_for(_rocket(death_after_us=400 * MS))
    weakish = co.opportunities_for(_rocket(death_after_us=2_000 * MS))
    a = next(o for o in strong if o.opportunity_type == co.HERO_THEN_DEATH)
    b = next(o for o in weakish if o.opportunity_type == co.HERO_THEN_DEATH)
    assert a.strength == co.STRONG and b.strength == co.CONTEXTUAL
    assert "strong" in a.why.lower() and "contextual" in b.why.lower()


def test_a_death_long_after_the_action_earns_nothing():
    ops = co.opportunities_for(_rocket(death_after_us=4_000 * MS))
    assert co.HERO_THEN_DEATH not in {o.opportunity_type for o in ops}


def test_damage_strength_uses_more_than_the_raw_number():
    """A hundred into a fresh player and a hundred into an almost-dead one are
    not the same story."""
    plain = co.opportunities_for(_lg(damage_by_user=70))
    whole = co.opportunities_for(_lg(damage_by_user=70, victim_effective_hp=75,
                                     finisher_is_teammate=True))
    a = next(o for o in plain if o.opportunity_type == co.DAMAGE_STORY)
    b = next(o for o in whole if o.opportunity_type == co.DAMAGE_STORY)
    assert b.strength == co.STRONG and a.strength != co.STRONG
    assert "share_of_target" in b.why


def test_flyby_strength_uses_more_than_distance():
    near_fast = co.opportunities_for(
        _rocket(projectile_close_pass_u=40, relative_speed_u_s=980))
    far_slow = co.opportunities_for(
        _rocket(projectile_close_pass_u=210, relative_speed_u_s=120))
    a = next(o for o in near_fast if o.opportunity_type == co.PROJECTILE_FLYBY)
    b = next(o for o in far_slow if o.opportunity_type == co.PROJECTILE_FLYBY)
    assert a.strength == co.STRONG and b.strength == co.WEAK
    assert "relative_speed_u_s" in a.why


# ── visual focus ─────────────────────

def test_a_focus_names_what_it_refuses_and_why():
    f = vf.tracking_focus(0, 1_000 * MS)
    assert not vf.focus_permits(f, "MOSAIC_TILE_STEP")
    why = vf.why_refused(f, "MOSAIC_TILE_STEP")
    assert "occlusion" in why or "transformation" in why
    assert vf.focus_permits(f, "SLOW_MOTION"), "time effects hide nothing"
    assert vf.why_refused(f, "SLOW_MOTION") == ""


def test_a_projectile_focus_wants_the_camera_to_leave():
    f = vf.projectile_focus(0, 1_000 * MS)
    assert vf.focus_permits(f, "SIDE_REPLAY")
    assert vf.focus_permits(f, "PROJECTILE_FOLLOW")
    t = vf.tracking_focus(0, 1_000 * MS)
    assert not vf.focus_permits(t, "SIDE_REPLAY"), (
        "a tracking duel cannot survive the camera walking away")


def test_a_damage_ledger_does_not_freeze_the_rest_of_the_film():
    """Numbers need to be readable. That is weaker than protecting a skill."""
    f = vf.damage_focus(0, 1_000 * MS)
    assert vf.focus_permits(f, "SIDE_REPLAY")
    assert vf.focus_permits(f, "MODEL_PULSE")


def test_a_scoped_constraint_must_say_why_it_exists():
    with pytest.raises(ValueError, match="why"):
        vf.ScopedConstraint(0, 10, ("WORLD_STRIP",), vf.FORBID, "  ")
