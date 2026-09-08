"""Ten planning-only choreographies, to prove the architecture carries the idea.

None of these is a render and none consumes a moment. Each shows the same
thing: one musical interval, several lanes at once, every element anchored in
edit time with a reason, and a truth gate where the presentation makes a
claim about what happened.

Times are edit microseconds relative to the slot. Evidence references are
placeholders in shape but honest in kind: they name the class of recorded
thing the plan needs, so a search can go and look for it.
"""
from __future__ import annotations

from typing import Any

from creative_suite.engine import choreography as ch
from creative_suite.engine import creative_corpus as cc

PROOFS_VERSION = "choreography-proofs-v1.0.0"

_S = 1_000_000  # one second in microseconds


def _ev(kind: str, provenance: str = "RECORDED", ref: str = "",
        **detail: Any) -> ch.EvidenceRef:
    return ch.EvidenceRef(kind, provenance, ref, dict(detail))


# 1 ── team identity morph ──────────────────────────────────────────────────

def team_identity_morph() -> ch.ChoreographyPlan:
    """A real team fight; the player's model takes the clan treatment as the
    section opens. Nothing about who anybody IS changes."""
    team = _ev("team_state", "RECORDED", detail_note=">=1 mate, >=2 opponents")
    return ch.ChoreographyPlan(
        slot_id="PROOF_TEAM_IDENTITY_MORPH", start_us=0, end_us=8 * _S,
        musical_role="BUILD", narrative="pTn takes the field",
        intensity=ch.NORMAL,
        elements=(
            cc.element("TEAM_ROUND_STORY", 0, 8 * _S, lane=ch.LANE_NARRATIVE,
                       evidence=(team,), trigger="SECTION_START"),
            cc.element("TEAM_IDENTITY_MORPH", 1 * _S, 3 * _S, peak_us=2 * _S,
                       trigger="MUSIC_SWELL", musical_relation="ON_SWELL",
                       evidence=(team,)),
            cc.element("MICRO_ACTION_ACCENT", 5 * _S, 5 * _S + 200_000,
                       peak_us=5 * _S, trigger="ATTACK_1",
                       musical_relation="ON_ATTACK",
                       evidence=(_ev("movement"),)),
        ))


# 2 ── rhythmic image stutter ───────────────────────────────────────────────

def rhythmic_image_stutter() -> ch.ChoreographyPlan:
    """A four-attack figure answered by four different lanes. Not four kills."""
    return ch.ChoreographyPlan(
        slot_id="PROOF_RHYTHMIC_STUTTER", start_us=0, end_us=4 * _S,
        musical_role="GESTURE", narrative="the figure takes the picture apart",
        intensity=ch.HERO,
        elements=(
            cc.element("RHYTHMIC_IMAGE_STUTTER", 0, 120_000, peak_us=0,
                       trigger="GESTURE_ATTACK_1", musical_relation="ON_ATTACK"),
            cc.element("MUSIC_REACTIVE_MATERIAL", 600_000, 900_000, peak_us=600_000,
                       trigger="GESTURE_ATTACK_2", musical_relation="ON_ATTACK"),
            cc.element("MOSAIC_TILE_INTERPOLATION", 1_200_000, 1_800_000,
                       peak_us=1_200_000, trigger="GESTURE_ATTACK_3",
                       musical_relation="ON_ATTACK"),
            cc.element("IDENTITY_MATCH_CUT", 1_800_000, 2_000_000, peak_us=1_800_000,
                       trigger="GESTURE_ATTACK_4", musical_relation="ON_ATTACK",
                       lane=ch.LANE_TRANSITION),
        ))


# 3 ── damage ledger ────────────────────────────────────────────────────────

def damage_ledger() -> ch.ChoreographyPlan:
    dmg = _ev("damage_ledger", "RECORDED", detail_note="confirmed hits only")
    return ch.ChoreographyPlan(
        slot_id="PROOF_DAMAGE_LEDGER", start_us=0, end_us=6 * _S,
        musical_role="BUILD", narrative="the cost accumulates",
        elements=(
            cc.element("DAMAGE_LEDGER_OVER_TARGET", 0, 6 * _S, evidence=(dmg,),
                       trigger="FIRST_HIT", musical_relation="FOLLOWS_ACTION"),
            cc.element("ROUND_DAMAGE_COUNTER", 4 * _S, 6 * _S, peak_us=5 * _S,
                       evidence=(dmg, _ev("round_context")),
                       trigger="PHRASE_END", musical_relation="ON_PHRASE_END"),
        ))


# 4 ── hero, then death, then rewind ────────────────────────────────────────

def hero_then_death_rewind() -> ch.ChoreographyPlan:
    """The player does something extraordinary and dies a second later. The
    death becomes material; the action is replayed clean."""
    frag = _ev("frag", "RECORDED", ref="<frag id>")
    death = _ev("death", "RECORDED")
    return ch.ChoreographyPlan(
        slot_id="PROOF_HERO_THEN_DEATH_REWIND", start_us=0, end_us=12 * _S,
        musical_role="DROP", narrative="brilliance, punished, restated",
        intensity=ch.HERO,
        elements=(
            cc.element("COMMIT_1VX", 0, 3 * _S, lane=ch.LANE_NARRATIVE,
                       evidence=(_ev("round_context"), _ev("alive_state")),
                       trigger="BUILD"),
            cc.element("HERO_THEN_DEATH_REWIND", 3 * _S, 12 * _S, peak_us=3 * _S,
                       evidence=(frag, death), trigger="DROP",
                       musical_relation="ON_DROP", intensity=ch.HERO),
            cc.element("DEATH_MOTIF_BANK", 5 * _S, 8 * _S, peak_us=5 * _S,
                       evidence=(death, _ev("motif_group")),
                       trigger="GESTURE_RUN", musical_relation="ON_ATTACK"),
            cc.element("DEATH_AS_TRANSITION", 8 * _S, 8_500_000, peak_us=8 * _S,
                       evidence=(death,), trigger="PHRASE_END"),
        ))


# 5 ── rocket flyby transition ──────────────────────────────────────────────

def rocket_flyby_transition() -> ch.ChoreographyPlan:
    path = _ev("projectile_path", "RECORDED", detail_note="close pass, real geometry")
    return ch.ChoreographyPlan(
        slot_id="PROOF_ROCKET_FLYBY", start_us=0, end_us=5 * _S,
        musical_role="TRANSITION", narrative="the rocket carries us out",
        elements=(
            cc.element("ROCKET_FLYBY_AUDIO_ANCHOR", 0, 2 * _S, peak_us=1_500_000,
                       evidence=(path,), trigger="PRE_DROP",
                       musical_relation="LEADS_DROP"),
            cc.element("PROJECTILE_CINEMATIC", 2 * _S, 4 * _S, peak_us=3 * _S,
                       lane=ch.LANE_CAMERA, evidence=(path,), trigger="DROP"),
            cc.element("MOVEMENT_TRANSITION", 4 * _S, 5 * _S, peak_us=4 * _S,
                       lane=ch.LANE_TRANSITION, evidence=(_ev("movement"),),
                       trigger="DROP", musical_relation="ON_DROP"),
        ))


# 6 ── wall x-ray and rebuild ───────────────────────────────────────────────

def wall_xray_rebuild() -> ch.ChoreographyPlan:
    return ch.ChoreographyPlan(
        slot_id="PROOF_WALL_XRAY", start_us=0, end_us=9 * _S,
        musical_role="BREAK", narrative="what the wall was hiding",
        elements=(
            cc.element("WALL_XRAY_REBUILD", 0, 6 * _S, peak_us=2 * _S,
                       trigger="BREAK_START", musical_relation="IN_NEGATIVE_SPACE"),
            cc.element("PROJECTILE_CINEMATIC", 2 * _S, 4 * _S, peak_us=3 * _S,
                       lane=ch.LANE_CAMERA, evidence=(_ev("projectile_path"),),
                       trigger="BREAK_START"),
            cc.element("WORLD_REBUILD", 6 * _S, 7 * _S, peak_us=6 * _S,
                       trigger="DROP", musical_relation="ON_DROP"),
            cc.element("ROUND_WIN_PAYOFF", 7 * _S, 9 * _S, peak_us=7 * _S,
                       lane=ch.LANE_NARRATIVE,
                       evidence=(_ev("round_result", "RECORDED", detail_note="WIN"),),
                       trigger="DROP"),
        ),
        round_result_required="WIN", round_result_evidence="WIN")


# 7 ── 1vX enemy reveal ─────────────────────────────────────────────────────

def one_v_x_enemy_reveal() -> ch.ChoreographyPlan:
    """The canonical example: a three-attack figure answered by three reveals,
    a count that decrements, the map stripped in the silence, and the frag on
    the hero transient."""
    ctx = _ev("round_context", "RECORDED")
    alive = _ev("alive_state", "RECORDED", detail_note="1 v 3 at the hero moment")
    return ch.ChoreographyPlan(
        slot_id="PROOF_1VX_REVEAL", start_us=0, end_us=14 * _S,
        musical_role="BUILD -> NEGATIVE_SPACE -> DROP",
        narrative="1v3 escalation, won", intensity=ch.SPECTACLE,
        elements=(
            cc.element("WORLD_STRIP", 1 * _S, 3 * _S, peak_us=2 * _S,
                       trigger="BUILD", musical_relation="IN_BUILD"),
            cc.element("ONE_V_X_ENEMY_REVEAL", 3 * _S, 3_400_000, peak_us=3 * _S,
                       lane=ch.LANE_FX, evidence=(ctx, alive),
                       trigger="GESTURE_ATTACK_1", musical_relation="ON_ATTACK"),
            cc.element("ONE_V_X_ENEMY_REVEAL", 4 * _S, 4_400_000, peak_us=4 * _S,
                       lane=ch.LANE_FX, evidence=(ctx, alive),
                       trigger="GESTURE_ATTACK_2", musical_relation="ON_ATTACK"),
            cc.element("ONE_V_X_ENEMY_REVEAL", 5 * _S, 5_400_000, peak_us=5 * _S,
                       lane=ch.LANE_FX, evidence=(ctx, alive),
                       trigger="GESTURE_ATTACK_3", musical_relation="ON_ATTACK"),
            cc.element("ONE_V_X_COUNT_DISPLAY", 3 * _S, 11 * _S,
                       evidence=(alive,), trigger="GESTURE_ATTACK_1",
                       musical_relation="FOLLOWS_ACTION",
                       notes="3 -> 2 -> 1, each decrement on a real death"),
            cc.element("WORLD_REBUILD", 9 * _S, 10 * _S, peak_us=9 * _S,
                       trigger="DROP", musical_relation="ON_DROP"),
            cc.element("SPEED_SCALED_SLOWMO", 9 * _S, 11 * _S,
                       lane=ch.LANE_TIME, evidence=(_ev("movement"),),
                       trigger="DROP"),
            cc.element("ROUND_WIN_PAYOFF", 11 * _S, 14 * _S, peak_us=11 * _S,
                       lane=ch.LANE_NARRATIVE,
                       evidence=(_ev("round_result", "RECORDED", detail_note="WIN"),),
                       trigger="RELEASE", intensity=ch.SPECTACLE),
        ),
        round_result_required="WIN", round_result_evidence="WIN")


# 8 ── diegetic scoreboard ──────────────────────────────────────────────────

def diegetic_scoreboard() -> ch.ChoreographyPlan:
    score = _ev("score_state", "RECORDED", detail_note="configstring scores")
    return ch.ChoreographyPlan(
        slot_id="PROOF_DIEGETIC_SCOREBOARD", start_us=0, end_us=7 * _S,
        musical_role="BREAK", narrative="the arena states the score itself",
        elements=(
            cc.element("DIEGETIC_SCOREBOARD", 0, 5 * _S, peak_us=1 * _S,
                       lane=ch.LANE_INFORMATION, evidence=(score,),
                       trigger="BREAK_START"),
            cc.element("TEXTURE_COUNTDOWN_TEXT", 5 * _S, 7 * _S, peak_us=6 * _S,
                       lane=ch.LANE_MATERIAL, trigger="PHRASE_END"),
            cc.element("CA_EXPLAINER", 0, 7 * _S, lane=ch.LANE_NARRATIVE,
                       evidence=(_ev("round_context"),), trigger="BREAK_START"),
        ))


# 9 ── movement audio match ─────────────────────────────────────────────────

def movement_audio_match() -> ch.ChoreographyPlan:
    mv = _ev("movement", "RECORDED", detail_note="jump and landing in both scenes")
    return ch.ChoreographyPlan(
        slot_id="PROOF_MOVEMENT_AUDIO_MATCH", start_us=0, end_us=4 * _S,
        musical_role="TRANSITION", narrative="two arenas, one landing",
        elements=(
            cc.element("VELOCITY_SIGNATURE", 0, 2 * _S, lane=ch.LANE_TIME,
                       evidence=(mv,), trigger="PHRASE"),
            cc.element("STRAFE_JUMP_AUDIO_MATCH", 1_800_000, 2_200_000,
                       peak_us=2 * _S, evidence=(mv,), trigger="LANDING",
                       musical_relation="ON_DOWNBEAT"),
            cc.element("MOVEMENT_TRANSITION", 2 * _S, 4 * _S, peak_us=2 * _S,
                       lane=ch.LANE_TRANSITION, evidence=(mv,), trigger="LANDING"),
        ))


# 10 ── enemy POV ───────────────────────────────────────────────────────────

def enemy_pov_preshot() -> ch.ChoreographyPlan:
    """A preshot: the player fires before the enemy appears, then we watch it
    arrive from the other side. Which POV we may use is a provenance question."""
    frag = _ev("frag", "RECORDED", ref="<frag id>")
    return ch.ChoreographyPlan(
        slot_id="PROOF_ENEMY_POV", start_us=0, end_us=8 * _S,
        musical_role="DROP", narrative="the shot was already in the air",
        intensity=ch.HERO,
        elements=(
            cc.element("RAIL_COOLDOWN_TELEGRAPH", 0, 2 * _S, peak_us=1 * _S,
                       lane=ch.LANE_INFORMATION,
                       evidence=(_ev("weapon_state"),), trigger="BUILD"),
            cc.element("ENEMY_POV_RECONSTRUCTED", 3 * _S, 6 * _S, peak_us=5 * _S,
                       lane=ch.LANE_CAMERA,
                       evidence=(_ev("enemy_state", "DERIVED",
                                     detail_note="approximate, labelled"),),
                       trigger="DROP", musical_relation="ON_DROP"),
            cc.element("PIP_WORLD_SURFACE", 3 * _S, 6 * _S, lane=ch.LANE_PIP,
                       trigger="DROP"),
            cc.element("HERO_THEN_DEATH_REWIND", 6 * _S, 8 * _S, peak_us=6 * _S,
                       lane=ch.LANE_TIME, evidence=(frag, _ev("death")),
                       trigger="RELEASE"),
        ))


PROOFS = (team_identity_morph, rhythmic_image_stutter, damage_ledger,
          hero_then_death_rewind, rocket_flyby_transition, wall_xray_rebuild,
          one_v_x_enemy_reveal, diegetic_scoreboard, movement_audio_match,
          enemy_pov_preshot)


def all_plans() -> tuple[ch.ChoreographyPlan, ...]:
    return tuple(f() for f in PROOFS)


def report() -> dict[str, Any]:
    plans = all_plans()
    return {"version": PROOFS_VERSION, "plans": len(plans),
            "by_plan": [{"slot_id": p.slot_id, "lanes": list(p.lanes_used),
                         "elements": len(p.elements),
                         "weakest_capability": p.weakest_capability,
                         "capability_score": p.capability_score,
                         "cost_profile": p.cost_profile,
                         "density": p.density(),
                         "gated_on": p.round_result_required or "",
                         "hash": p.plan_hash}
                        for p in plans]}
