"""Choreography: music asks for a visual event, not for a frag."""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (choreography as ch, choreography_proofs as cp,
                                   creative_corpus as cc, demo_truth as dt)

_S = 1_000_000


def _el(**kw):
    base = dict(lane=ch.LANE_FX, action="RHYTHMIC_IMAGE_STUTTER", start_us=0,
                end_us=100_000, purpose="MUSICAL_PUNCTUATION")
    base.update(kw)
    return ch.ChoreographyElement(**base)


# ── an element must mean something ──────────────────────────────────────────

def test_an_element_without_a_purpose_is_refused():
    for bad in ch.BANNED_PURPOSES:
        with pytest.raises(ValueError, match="purpose|not a purpose"):
            _el(purpose=bad)


def test_a_truth_bearing_lane_needs_evidence():
    with pytest.raises(ValueError, match="evidence"):
        _el(lane=ch.LANE_INFORMATION, action="ONE_V_X_COUNT_DISPLAY",
            purpose="SHOW_THREAT")
    ok = _el(lane=ch.LANE_INFORMATION, action="ONE_V_X_COUNT_DISPLAY",
             purpose="SHOW_THREAT",
             evidence=(ch.EvidenceRef("alive_state", "RECORDED"),))
    assert ok.evidence[0].provenance == "RECORDED"
    # a look-only lane needs no evidence: an effect is not a claim
    assert _el(lane=ch.LANE_FX).evidence == ()


def test_peak_must_lie_inside_the_element():
    with pytest.raises(ValueError, match="peak"):
        _el(peak_us=500_000)
    assert _el(peak_us=50_000).anchor_us == 50_000
    assert _el().anchor_us == 0            # no peak: the start is the anchor


# ── the plan ────────────────────────────────────────────────────────────────

def test_elements_must_stay_inside_the_slot():
    with pytest.raises(ValueError, match="outside the slot"):
        ch.ChoreographyPlan("s", 0, 1 * _S, "DROP",
                            elements=(_el(start_us=0, end_us=2 * _S),))


def test_a_plan_serialises_deterministically():
    a, b = cp.one_v_x_enemy_reveal(), cp.one_v_x_enemy_reveal()
    assert a.plan_hash == b.plan_hash
    assert json.dumps(a.to_dict(), sort_keys=True) == json.dumps(b.to_dict(), sort_keys=True)
    changed = replace(a, narrative="something else")
    assert changed.plan_hash != a.plan_hash


def test_one_musical_gesture_drives_several_different_lanes():
    """The whole point: four attacks answered by four lanes, not four kills."""
    plan = cp.rhythmic_image_stutter()
    lanes = {e.lane for e in plan.elements}
    assert len(lanes) >= 3
    assert not plan.lane(ch.LANE_GAMEPLAY)          # no frag anywhere in it
    reveal = cp.one_v_x_enemy_reveal()
    for n in (1, 2, 3):
        assert len(reveal.gesture_responses(f"GESTURE_ATTACK_{n}")) >= 1
    # the three reveals are three elements answering three attacks
    assert len([e for e in reveal.elements if e.action == "ONE_V_X_ENEMY_REVEAL"]) == 3


def test_lanes_used_reports_every_lane_in_play():
    plan = cp.one_v_x_enemy_reveal()
    assert ch.LANE_FX in plan.lanes_used and ch.LANE_INFORMATION in plan.lanes_used
    assert ch.LANE_WORLD in plan.lanes_used and ch.LANE_TIME in plan.lanes_used
    assert len(plan.lanes_used) >= 5


# ── truth gates ─────────────────────────────────────────────────────────────

def test_a_victory_treatment_over_a_lost_round_is_refused():
    with pytest.raises(ValueError, match="not won|WIN"):
        ch.ChoreographyPlan("s", 0, _S, "DROP", round_result_required="WIN",
                            round_result_evidence="LOSS")
    with pytest.raises(ValueError):
        ch.ChoreographyPlan("s", 0, _S, "DROP", round_result_required="WIN",
                            round_result_evidence=ch.UNKNOWN)
    assert ch.ChoreographyPlan("s", 0, _S, "DROP", round_result_required="WIN",
                               round_result_evidence="WIN").duration_us == _S


def test_choreography_cannot_alter_demo_truth():
    """A plan holds references to evidence. It has no writer, and the
    evidence classes it names are read-only demo facts."""
    plan = cp.one_v_x_enemy_reveal()
    refs = [e for el in plan.elements for e in el.evidence]
    assert refs, "the truth-bearing lanes carry evidence"
    assert all(r.provenance in ("RECORDED", "DERIVED") for r in refs)
    assert not any(r.provenance == dt.CINEMATIC_SYNTHETIC for r in refs)
    # nothing on the plan can write: no attribute exposes a connection or path
    assert not [a for a in dir(plan) if a.startswith(("write", "save", "commit"))]


def test_a_reconstructed_pov_is_labelled_and_never_passes_as_recorded():
    plan = cp.enemy_pov_preshot()
    pov = next(e for e in plan.elements if e.action.startswith("ENEMY_POV"))
    assert pov.action == "ENEMY_POV_RECONSTRUCTED"
    assert pov.evidence[0].provenance == "DERIVED"
    real = cc.get("ENEMY_POV_REAL")
    assert "MULTI_DEMO_RECOVERED" in real.gates
    assert cc.get("ENEMY_POV_SYNTHETIC").evidence_required == ()


# ── capability and cost ─────────────────────────────────────────────────────

def test_every_corpus_entry_declares_capability_and_cost():
    for e in cc.CORPUS:
        assert e.capability in ch.CAPABILITIES
        assert e.cost in ch.COSTS
        assert e.purpose in ch.PURPOSES
    rep = cc.capability_report()
    assert rep["entries"] == len(cc.CORPUS) >= 50
    assert rep["by_capability"][ch.PROVEN_RUNTIME] > 0
    assert rep["by_capability"][ch.CREATIVE_SEED] > 0     # honest about the seeds


def test_an_element_inherits_capability_from_the_register():
    """A plan cannot quietly claim an effect is more real than it is."""
    el = cc.element("WORLD_MORPH_TO_NEXT_SCENE", 0, _S)
    assert el.capability == ch.REQUIRES_NEW_TECH and el.cost == ch.COST_RND
    plan = ch.ChoreographyPlan("s", 0, _S, "DROP", elements=(el,))
    assert plan.weakest_capability == ch.REQUIRES_NEW_TECH


def test_the_weakest_element_governs_what_a_plan_can_deliver():
    cheap = cc.element("MICRO_ACTION_ACCENT", 0, _S,
                       evidence=(ch.EvidenceRef("movement", "RECORDED"),))
    hard = cc.element("GRENADE_FOOTBALL_GAG", 0, _S, lane=ch.LANE_ANIMATION)
    plan = ch.ChoreographyPlan("s", 0, _S, "DROP", elements=(cheap, hard))
    assert plan.weakest_capability == ch.CREATIVE_SEED
    assert plan.capability_score < 1.0
    assert plan.cost_profile[ch.COST_RND] == 1


# ── fillability ─────────────────────────────────────────────────────────────

def test_choreography_fillability_is_separate_from_gameplay_fillability():
    """A song whose gameplay exists but whose effects do not is not fillable."""
    dreamy = ch.ChoreographyPlan(
        "dream", 0, _S, "DROP",
        elements=(cc.element("WORLD_MORPH_TO_NEXT_SCENE", 0, _S),))
    grounded = ch.ChoreographyPlan(
        "real", 0, _S, "DROP",
        elements=(cc.element("DEATH_AS_TRANSITION", 0, _S,
                             evidence=(ch.EvidenceRef("death", "RECORDED"),)),))
    strong = ch.ChoreographyFit(dreamy.plan_hash, "frag:1", {"GAMEPLAY_FIT": 0.9})
    also = ch.ChoreographyFit(grounded.plan_hash, "frag:2", {"GAMEPLAY_FIT": 0.9})
    out = ch.fillability([dreamy, grounded], [strong, also])
    assert out["gameplay_fillability"] == 1.0          # the moments are there
    assert out["choreography_fillability"] < 0.6       # the effects are not
    assert out["slots_renderable_today"] == 1
    assert ch.REQUIRES_NEW_TECH in out["weakest_capabilities"]


def test_the_weakest_required_dimension_decides_a_fit():
    fit = ch.ChoreographyFit("h", "frag:9", {"GAMEPLAY_FIT": 0.95,
                                             "CAMERA_FIT": 0.9,
                                             "RESULT_TRUTH_FIT": 0.2})
    assert fit.score == 0.2                       # one spectacular lane saves nothing
    assert fit.weakest[0] == "RESULT_TRUTH_FIT"
    blocked = ch.ChoreographyFit("h", "frag:9", {"GAMEPLAY_FIT": 1.0},
                                 blocked="round was not won")
    assert not blocked.eligible and blocked.score == 0.0


def test_an_empty_slot_counts_as_empty_not_weak():
    plan = cp.damage_ledger()
    out = ch.fillability([plan], [])
    assert out["candidate_depth"]["empty"] == 1 and out["gameplay_fillability"] == 0.0


# ── the ten proofs ──────────────────────────────────────────────────────────

def test_ten_choreography_proofs_exist_and_build():
    plans = cp.all_plans()
    assert len(plans) >= 10
    assert len({p.slot_id for p in plans}) == len(plans)
    for p in plans:
        assert p.elements and p.lanes_used
        assert p.density()["visual_events_per_s"] > 0


def test_the_proofs_cover_the_named_creative_ideas():
    actions = {e.action for p in cp.all_plans() for e in p.elements}
    for required in ("TEAM_IDENTITY_MORPH", "RHYTHMIC_IMAGE_STUTTER",
                     "DAMAGE_LEDGER_OVER_TARGET", "HERO_THEN_DEATH_REWIND",
                     "ROCKET_FLYBY_AUDIO_ANCHOR", "WALL_XRAY_REBUILD",
                     "ONE_V_X_ENEMY_REVEAL", "DIEGETIC_SCOREBOARD",
                     "STRAFE_JUMP_AUDIO_MATCH", "ENEMY_POV_RECONSTRUCTED"):
        assert required in actions, required


def test_gated_proofs_declare_the_round_result_they_need():
    gated = [p for p in cp.all_plans() if p.round_result_required]
    assert gated, "at least one proof is a victory treatment"
    for p in gated:
        assert p.round_result_evidence == p.round_result_required


# ── readiness ───────────────────────────────────────────────────────────────

def test_the_song_shortlist_stays_shut_until_choreography_is_ready():
    blocked = ch.assess_readiness(corpus_entries=0, lanes_covered=3, proofs_built=0,
                                  gameplay_truth_ready=False, music_library_ready=False)
    assert not blocked.may_shortlist_songs
    assert blocked.state == ch.SHORTLIST_BLOCKED and len(blocked.blockers) >= 4
    from creative_suite.engine import temporal_proofs as tpf
    ready = ch.assess_readiness(corpus_entries=len(cc.CORPUS), lanes_covered=len(ch.LANES),
                                proofs_built=len(cp.PROOFS), gameplay_truth_ready=True,
                                music_library_ready=True,
                                temporal_proofs_built=len(tpf.PROOFS))
    assert ready.may_shortlist_songs and ready.state == ch.SHORTLIST_READY


def test_music_defects_alone_still_block_the_shortlist():
    from creative_suite.engine import temporal_proofs as tpf
    r = ch.assess_readiness(corpus_entries=len(cc.CORPUS), lanes_covered=len(ch.LANES),
                            proofs_built=len(cp.PROOFS), gameplay_truth_ready=True,
                            music_library_ready=False,
                            temporal_proofs_built=len(tpf.PROOFS))
    assert not r.may_shortlist_songs
    assert r.choreography_scoring_ready       # the composer is ready; the library is not


# ── the planning sheet ──────────────────────────────────────────────────────

def test_the_sheet_groups_lanes_for_the_whole_view_and_opens_them_when_zoomed():
    from creative_suite.engine import choreography_sheet as cs
    plans = cp.all_plans()
    s = cs.sheet_summary(plans)
    assert s["slots"] == len(plans) and s["elements"] > 20
    assert len(s["bands"]) <= 7, "the whole view must fit on one page"
    assert set(s["lanes_in_play"]) <= set(ch.LANES)
    assert "PROOF_1VX_REVEAL" in s["gated_slots"]
    assert sum(s["capability_counts"].values()) == s["elements"]
    zoom_rows = cs._rows(plans, zoom=True)
    assert len(zoom_rows) > len(s["bands"]), "zoom exposes more than the bands"
    assert all(len(lanes) == 1 for _, lanes in zoom_rows)


def test_the_sheet_renders_both_views(tmp_path):
    from creative_suite.engine import choreography_sheet as cs
    plans = cp.all_plans()
    whole = cs.render_sheet(plans, tmp_path / "whole.png", title="t")
    zoom = cs.render_sheet(plans[6:7], tmp_path / "zoom.png", zoom=True)
    assert whole.exists() and whole.stat().st_size > 5000
    assert zoom.exists() and zoom.stat().st_size > 5000


# ── reconciliation with the user's own list ─────────────────────────────────

USER_CONCEPTS = {
    "live texture/skin/model transformation": "TEAM_IDENTITY_MORPH",
    "seamless world transformation": "WORLD_MORPH_TO_NEXT_SCENE",
    "rocket/background morph into next scene": "PROJECTILE_MORPH_BRIDGE",
    "fly into an eye/rocket/object": "FLY_INTO_OBJECT",
    "world disappears/rebuilds": "WORLD_STRIP",
    "1vX map removal and enemy reveals": "ONE_V_X_ENEMY_REVEAL",
    "display X count and decrement it": "ONE_V_X_COUNT_DISPLAY",
    "countdown/text on world textures": "TEXTURE_COUNTDOWN_TEXT",
    "low-HP reactive materials/world": "LOW_HP_REACTIVE_WORLD",
    "grenade football/chest/headbutt gag": "GRENADE_FOOTBALL_GAG",
    "victory-only payoff gating": "ROUND_WIN_PAYOFF",
    "a loss needs a different ending": "ROUND_LOSS_CONTINUATION",
    "full pTn team-round storytelling": "TEAM_ROUND_STORY",
    "freeze and match-cut into a similar pose": "IDENTITY_MATCH_CUT",
    "map wireframe to geometry to material": "MAP_CONSTRUCTION_INTRO",
    "PIP on advertisement/world surfaces": "PIP_WORLD_SURFACE",
    "chat bubbles / rage / gg / memes": "CHAT_REACTION",
    "rapid motif montages": "RHYTHMIC_MOTIF_MONTAGE",
    "doors / teleports / rocket jumps as transitions": "MOVEMENT_TRANSITION",
    "telefrag grammar": "TELEFRAG_GRAMMAR",
    "gauntlet grammar": "GAUNTLET_GRAMMAR",
    "multi-exposure": "MULTI_EXPOSURE",
    "time echoes": "FRAME_ECHO",
    "freeze decomposition": "TEMPORAL_DECOMPOSITION",
    "music-reactive world/material changes": "MUSIC_REACTIVE_MATERIAL",
    "death as transition material": "DEATH_AS_TRANSITION",
    "wall removal/x-ray/rebuild": "WALL_XRAY_REBUILD",
    "team identity skin morphs": "TEAM_IDENTITY_MORPH",
    "teammate model transformation after victory": "POST_WIN_TEAMMATE_MODEL_REVEAL",
    "rhythmic image stutter": "RHYTHMIC_IMAGE_STUTTER",
    "tiled/mosaic interpolation": "MOSAIC_TILE_INTERPOLATION",
    "gauntlet/item micro accents": "MICRO_ACTION_ACCENT",
    "rail cooldown visualization": "RAIL_COOLDOWN_TELEGRAPH",
    "cumulative enemy damage ledger": "DAMAGE_LEDGER_OVER_TARGET",
    "round total damage": "ROUND_DAMAGE_COUNTER",
    "Episode 1 CA explanation": "CA_EXPLAINER",
    "semantic compression of long rounds": "SEMANTIC_COMPRESSION",
    "cross-sign danger dive gag": "DANGER_CROSS_SIGN",
    "jump-to-jump audio match": "STRAFE_JUMP_AUDIO_MATCH",
    "good frag, death, montage, rewind": "HERO_THEN_DEATH_REWIND",
    "rocket flyby audio/geometry": "ROCKET_FLYBY_AUDIO_ANCHOR",
    "diegetic scoreboard": "DIEGETIC_SCOREBOARD",
    "assisted round payoff": "ASSISTED_ROUND_FINISH",
    "jump-pad/double-jump/plasma/grenade movement": "VELOCITY_SIGNATURE",
    "NOPE retreat": "NOPE_RETREAT",
    "1vX commit": "COMMIT_1VX",
    "speed-scaled slow-motion envelope": "SPEED_SCALED_SLOWMO",
    "damage chase into enemy death": "DAMAGE_CHASE_ASSIST",
    "lag/teleport ragebait": "LAG_TELEPORT_STYLIZATION",
    "useless deaths as montage material": "DEATH_MOTIF_BANK",
    "outshaft statistics": "SHAFT_DUEL_STAT",
    "enemy POV, real": "ENEMY_POV_REAL",
    "enemy POV, reconstructed": "ENEMY_POV_RECONSTRUCTED",
    "enemy POV, synthetic": "ENEMY_POV_SYNTHETIC",
    "projectile cinematic": "PROJECTILE_CINEMATIC",
    "reconstructed projectile cinematic": "RECONSTRUCTED_PROJECTILE_CINEMATIC",
    "teleporter as a world pass": "TELEPORTER_WORLD_PASS",
    "project intro": "PROJECT_INTRO",
    "Quake tribute outro": "QUAKE_TRIBUTE_OUTRO",
}


def test_every_idea_the_user_named_is_registered():
    """The corpus is the promise that nothing was dropped. If an idea stops
    being represented, this fails rather than quietly disappearing."""
    missing = {phrase: name for phrase, name in USER_CONCEPTS.items()
               if name not in cc.BY_NAME}
    assert not missing, f"unregistered ideas: {missing}"
    assert len(set(USER_CONCEPTS.values())) >= 55


def test_the_hard_ideas_are_registered_as_hard():
    """Honest capability: the ideas that need new tooling say so, and the
    ones that already ship say that too."""
    assert cc.get("WORLD_MORPH_TO_NEXT_SCENE").capability == ch.REQUIRES_NEW_TECH
    assert cc.get("GRENADE_FOOTBALL_GAG").capability == ch.CREATIVE_SEED
    assert cc.get("SHAFT_DUEL_STAT").capability == ch.CREATIVE_SEED
    assert cc.get("DEATH_AS_TRANSITION").capability == ch.PROVEN_RUNTIME
    assert cc.get("TEAM_ROUND_STORY").capability == ch.PROVEN_RUNTIME


def test_gated_ideas_carry_their_gate():
    assert "ROUND_WIN" in cc.get("POST_WIN_TEAMMATE_MODEL_REVEAL").gates
    assert "ROUND_WIN" in cc.get("ROUND_WIN_PAYOFF").gates
    assert "MANUAL_VERIFIED_TEAM_IDENTITY" in cc.get("TEAM_IDENTITY_MORPH").gates
    assert "PRESENTABLE_RECONSTRUCTION" in cc.get("RECONSTRUCTED_PROJECTILE_CINEMATIC").gates
