"""What the action justifies. Time never gets a vote here.

THE INVARIANT. A creative treatment becomes available because of what
happened in the game, not because a score slot is 570 ms short. This module
reads recorded evidence and produces the treatments that evidence entitles us
to. Nothing downstream may add to that list -- the temporal budget evaluates
these opportunities and may reject them, but it can never discover a new one
to close a gap.

    ACTION CREATES THE OPPORTUNITY.
    MUSIC SHAPES THE OPPORTUNITY.
    TIME PERFECTS THE OPPORTUNITY.
    TIME NEVER INVENTS THE OPPORTUNITY.

WHY IT MATTERS. A wall x-ray is worth doing when geometry actually hides
something worth seeing. A one-versus-three reveal is worth doing when there
really were three of them. Neither becomes worth doing because a phrase needs
filling, and a system that cannot tell the difference will quietly become an
intelligent-looking padding machine.

GRAMMARS. One action usually supports several legitimate treatments of very
different lengths -- pure first person, first person plus a slowed replay,
the same with a freeze and a world treatment. Those are the durations a score
slot should be compared against, rather than the raw source length.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Iterable, Sequence

from creative_suite.engine import effect_templates as et
from creative_suite.engine import temporal_operators as t

OPPORTUNITY_VERSION = "creative-opportunity-v1.0.0"
MS = 1000

# ── opportunity types ───────────────────────────────────────────────────────

HERO_PROJECTILE = "HERO_PROJECTILE"
HIGH_SPEED_CONTACT = "HIGH_SPEED_CONTACT"
ONE_VX_REVEAL = "1VX_REVEAL"
TEAM_IDENTITY = "TEAM_IDENTITY"
DAMAGE_STORY = "DAMAGE_STORY"
HERO_THEN_DEATH = "HERO_THEN_DEATH"
OCCLUDED_SKILL = "OCCLUDED_SKILL"
MOVEMENT_MATCH = "MOVEMENT_MATCH"
PROJECTILE_FLYBY = "PROJECTILE_FLYBY"
ASSISTED_FINISH = "ASSISTED_FINISH"
ROUND_WIN_PAYOFF = "ROUND_WIN_PAYOFF"
LG_TRACKING = "LG_TRACKING"
MICRO_ACTION = "MICRO_ACTION"
ENEMY_POV = "ENEMY_POV"
TELEPORT_GLITCH = "TELEPORT_GLITCH"
DANGEROUS_DIVE = "DANGEROUS_DIVE"

TYPES = (HERO_PROJECTILE, HIGH_SPEED_CONTACT, ONE_VX_REVEAL, TEAM_IDENTITY,
         DAMAGE_STORY, HERO_THEN_DEATH, OCCLUDED_SKILL, MOVEMENT_MATCH,
         PROJECTILE_FLYBY, ASSISTED_FINISH, ROUND_WIN_PAYOFF, LG_TRACKING,
         MICRO_ACTION, ENEMY_POV, TELEPORT_GLITCH, DANGEROUS_DIVE)

# ── editorial weight and how often a thing may recur ────────────────────────
# Some treatments are so strong that using them twice would spend them.

MICRO, SUPPORT, FEATURE, HERO, SIGNATURE = (
    "MICRO", "SUPPORT", "FEATURE", "HERO", "SIGNATURE")
WEIGHTS = (MICRO, SUPPORT, FEATURE, HERO, SIGNATURE)

FREQUENT, OCCASIONAL, RARE, ONCE_PER_EPISODE = (
    "FREQUENT", "OCCASIONAL", "RARE", "ONCE_PER_EPISODE")
POLICIES = (FREQUENT, OCCASIONAL, RARE, ONCE_PER_EPISODE)
POLICY_BUDGET = {FREQUENT: 99, OCCASIONAL: 6, RARE: 2, ONCE_PER_EPISODE: 1}

# What each template is worth editorially, and how often it may appear. A
# template with no entry is SUPPORT / OCCASIONAL.
EDITORIAL: dict[str, tuple[str, str]] = {
    "PLAYER_FREEZE_POSE": (SIGNATURE, ONCE_PER_EPISODE),
    "GRENADE_GAG": (SIGNATURE, ONCE_PER_EPISODE),
    "MAP_CONSTRUCTION": (SIGNATURE, ONCE_PER_EPISODE),
    "WORLD_STRIP": (HERO, RARE),
    "WORLD_REBUILD": (HERO, RARE),
    "WORLD_MORPH_BRIDGE": (SIGNATURE, ONCE_PER_EPISODE),
    "MODEL_MORPH": (HERO, RARE),
    "ENEMY_REVEAL_STEP": (HERO, RARE),
    "WALL_XRAY": (HERO, RARE),
    "DEATH_REWIND": (FEATURE, RARE),
    "ENEMY_POV_INSERT": (FEATURE, RARE),
    "PROJECT_IDENTITY": (SIGNATURE, ONCE_PER_EPISODE),
    "TRIBUTE_OUTRO": (SIGNATURE, ONCE_PER_EPISODE),
    "CA_EXPLAINER_CARD": (FEATURE, RARE),
    "DIEGETIC_SCOREBOARD": (FEATURE, OCCASIONAL),
    "SIDE_REPLAY": (FEATURE, OCCASIONAL),
    "PROJECTILE_FOLLOW": (FEATURE, OCCASIONAL),
    "PROJECTILE_REPLAY": (FEATURE, OCCASIONAL),
    "GRENADE_ARC": (FEATURE, OCCASIONAL),
    "ROCKET_FLYBY_BRIDGE": (FEATURE, OCCASIONAL),
    "FREEZE_DECOMPOSITION": (FEATURE, RARE),
    "MOSAIC_TILE_STEP": (FEATURE, RARE),
    "ROUND_WIN_RELEASE": (FEATURE, OCCASIONAL),
    "DEATH_FLASH_MONTAGE": (SUPPORT, OCCASIONAL),
    "RHYTHMIC_IMAGE_STUTTER": (SUPPORT, FREQUENT),
    "FREEZE_HOLD": (SUPPORT, FREQUENT),
    "SLOW_MOTION": (SUPPORT, FREQUENT),
    "MATCH_CUT_OVERLAP": (SUPPORT, FREQUENT),
    "MOVEMENT_MATCH_OVERLAP": (SUPPORT, FREQUENT),
    "DEATH_EXPLOSION_MATCH": (SUPPORT, FREQUENT),
    "MOVEMENT_ACCENT": (MICRO, FREQUENT),
    "MATERIAL_FLASH": (MICRO, FREQUENT),
    "MODEL_PULSE": (MICRO, FREQUENT),
    "CAMERA_JOLT": (MICRO, FREQUENT),
    "FRAME_REPEAT": (MICRO, FREQUENT),
    "DAMAGE_LEDGER_TICK": (SUPPORT, OCCASIONAL),
    "ENEMY_COUNT_TICK": (SUPPORT, OCCASIONAL),
}


def editorial_weight(template_id: str) -> tuple[str, str]:
    return EDITORIAL.get(template_id, (SUPPORT, OCCASIONAL))


# ── evidence ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MomentEvidence:
    """What the demo actually recorded about one moment.

    Every field is a fact or a None. Nothing here is inferred from what would
    be convenient, and an absent field means the demo did not say -- which is
    a reason to withhold a treatment, never to invent one.
    """
    moment_ref: str                        # content_hash + server_time
    kinds: tuple[str, ...] = ()            # frag, death, movement, chat, ...
    weapon: str = ""
    projectile_path: bool = False
    projectile_recorded_fraction: float | None = None
    projectile_close_pass_u: float | None = None
    relative_speed_u_s: float | None = None
    alive_self: int | None = None
    alive_enemy: int | None = None
    teammates: int | None = None
    opponents: int | None = None
    round_result: str = "UNKNOWN"          # WIN | LOSS | UNKNOWN
    damage_by_user: int | None = None
    finisher_is_teammate: bool | None = None
    death_after_us: int | None = None      # user's own death, after the action
    occluded_by_geometry: bool = False
    lg_contacts: int | None = None
    movement_events: int = 0
    teleport_confirmed: bool = False
    netcode_anomaly: str = ""
    enemy_state_known: bool = False
    multi_demo_recovered: bool = False
    source_useful_us: int = 0

    def has(self, kind: str) -> bool:
        return kind in self.kinds

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── a grammar: one legitimate treatment of the action ───────────────────────

@dataclass(frozen=True)
class Grammar:
    """A named way of presenting this action, and how long it can run.

    Several grammars usually exist for one moment. They are not ranked here:
    a score slot compares its own duration against these envelopes and the
    composer decides which treatment the film wants at that point.
    """
    name: str
    templates: tuple[str, ...]
    rationale: str = ""

    @property
    def elasticity(self) -> t.TemporalElasticity:
        return et.combined_envelope(list(self.templates))

    @property
    def weakest_provenance(self) -> str:
        return min((et.template_provenance(i) for i in self.templates),
                   key=lambda p: et.PROVENANCE_RANK[p], default=et.DESIGN_ESTIMATE)

    @property
    def heaviest_weight(self) -> str:
        order = {w: i for i, w in enumerate(WEIGHTS)}
        return max((editorial_weight(i)[0] for i in self.templates),
                   key=lambda w: order[w], default=SUPPORT)

    def fits(self, slot_us: int) -> bool:
        return self.elasticity.fits(slot_us)

    def to_dict(self) -> dict[str, Any]:
        el = self.elasticity
        return {"name": self.name, "templates": list(self.templates),
                "rationale": self.rationale,
                "hard_ms": [el.min_us // MS, el.max_us // MS],
                "preferred_ms": [el.preferred_min_us // MS,
                                 el.preferred_max_us // MS],
                "weakest_provenance": self.weakest_provenance,
                "editorial_weight": self.heaviest_weight}


@dataclass(frozen=True)
class CreativeOpportunity:
    """Something in the gameplay that justifies a visual treatment."""
    moment_ref: str
    opportunity_type: str
    why: str                               # what in the action earns this
    evidence_used: tuple[str, ...]
    grammars: tuple[Grammar, ...]
    forbidden_templates: tuple[str, ...] = ()
    result_truth: str = "UNKNOWN"
    narrative_purpose: str = ""
    rarity: str = OCCASIONAL
    editorial_weight: str = SUPPORT

    def __post_init__(self) -> None:
        if self.opportunity_type not in TYPES:
            raise ValueError(f"unknown opportunity {self.opportunity_type!r}")
        if not self.why.strip():
            raise ValueError(f"{self.opportunity_type}: an opportunity must say "
                             f"what in the action earns it")
        if not self.evidence_used:
            raise ValueError(f"{self.opportunity_type}: an opportunity without "
                             f"evidence is a wish")

    @property
    def allowed_templates(self) -> tuple[str, ...]:
        seen: list[str] = []
        for g in self.grammars:
            for i in g.templates:
                if i not in seen and i not in self.forbidden_templates:
                    seen.append(i)
        return tuple(seen)

    def grammar(self, name: str) -> Grammar | None:
        return next((g for g in self.grammars if g.name == name), None)

    def grammars_for(self, slot_us: int) -> tuple[Grammar, ...]:
        return tuple(g for g in self.grammars if g.fits(slot_us))

    def to_dict(self) -> dict[str, Any]:
        return {"moment_ref": self.moment_ref,
                "opportunity_type": self.opportunity_type, "why": self.why,
                "evidence_used": list(self.evidence_used),
                "result_truth": self.result_truth,
                "narrative_purpose": self.narrative_purpose,
                "rarity": self.rarity, "editorial_weight": self.editorial_weight,
                "allowed_templates": list(self.allowed_templates),
                "forbidden_templates": list(self.forbidden_templates),
                "grammars": [g.to_dict() for g in self.grammars],
                "version": OPPORTUNITY_VERSION}


# ── generation: evidence in, opportunities out ──────────────────────────────
#
# Each rule states the signature that earns a treatment. Nothing here consults
# a duration, a slot, or a song.

MEANINGFUL_DAMAGE = 60          # below this a ledger explains nothing
CLOSE_PASS_U = 220.0            # a projectile near enough for the camera to feel
FAST_U_S = 700.0                # relative speed that widens the slow envelope
DEATH_SOON_US = 2_500_000       # a death this close still belongs to the action
LG_BURST = 8                    # contacts that make a tracking story


def opportunities_for(ev: MomentEvidence) -> tuple[CreativeOpportunity, ...]:
    """Every treatment this evidence entitles us to, and no others."""
    out: list[CreativeOpportunity] = []

    def add(kind, why, used, grammars, **kw):
        out.append(CreativeOpportunity(ev.moment_ref, kind, why, tuple(used),
                                       tuple(grammars), **kw))

    # ── a projectile kill worth examining ──────────────────────────────────
    if ev.has("frag") and ev.projectile_path:
        gr = [Grammar("PURE_FPV", ("SLOW_MOTION",),
                      "the original skill, unadorned"),
              Grammar("FPV_REPLAY", ("SLOW_MOTION", "SIDE_REPLAY"),
                      "the action, then the trajectory examined"),
              Grammar("FPV_FREEZE_REPLAY",
                      ("SLOW_MOTION", "FREEZE_HOLD", "SIDE_REPLAY"),
                      "a held breath before the replay")]
        if ev.projectile_recorded_fraction is not None:
            gr.append(Grammar(
                "PROJECTILE_CAMERA",
                ("SLOW_MOTION", "FREEZE_HOLD", "PROJECTILE_FOLLOW",
                 "MATCH_CUT_OVERLAP"),
                "the camera rides the shot itself"))
        add(HERO_PROJECTILE,
            f"a {ev.weapon or 'projectile'} kill whose flight was recorded, so "
            f"the trajectory can be shown rather than asserted",
            ("frag", "projectile_path"), gr,
            result_truth=ev.round_result, narrative_purpose="hero",
            rarity=OCCASIONAL, editorial_weight=FEATURE)

    # ── a projectile that passes close to the camera ───────────────────────
    if (ev.projectile_path and ev.projectile_close_pass_u is not None
            and ev.projectile_close_pass_u <= CLOSE_PASS_U):
        add(PROJECTILE_FLYBY,
            f"a projectile passes {ev.projectile_close_pass_u:.0f} units from "
            f"the camera, close enough to be felt",
            ("projectile_path", "projectile_close_pass_u"),
            [Grammar("FLYBY_BRIDGE", ("ROCKET_FLYBY_BRIDGE",),
                     "the pass carries us into the next scene"),
             Grammar("FLYBY_FOLLOW", ("PROJECTILE_FOLLOW", "ROCKET_FLYBY_BRIDGE"),
                     "follow it in, hand off on the closest approach")],
            narrative_purpose="transition", editorial_weight=FEATURE)

    # ── being outnumbered, truthfully ──────────────────────────────────────
    if (ev.alive_self == 1 and (ev.alive_enemy or 0) >= 2):
        forbidden = () if ev.round_result == "WIN" else ("ROUND_WIN_RELEASE",)
        gr = [Grammar("THREAT_PLAIN", ("SLOW_MOTION", "ENEMY_COUNT_TICK"),
                      "state the odds and let the play speak"),
              Grammar("WORLD_REVEAL",
                      ("WORLD_STRIP", "ENEMY_REVEAL_STEP", "ENEMY_COUNT_TICK",
                       "WORLD_REBUILD"),
                      "strip the map, reveal them one at a time, restore")]
        if ev.round_result == "WIN":
            gr.append(Grammar(
                "REVEAL_AND_PAYOFF",
                ("WORLD_STRIP", "ENEMY_REVEAL_STEP", "ENEMY_COUNT_TICK",
                 "WORLD_REBUILD", "ROUND_WIN_RELEASE"),
                "the full escalation, earned by a won round"))
        add(ONE_VX_REVEAL,
            f"one against {ev.alive_enemy}, from death events inside the round",
            ("alive_self", "alive_enemy", "round_result"), gr,
            forbidden_templates=forbidden, result_truth=ev.round_result,
            narrative_purpose="1vx", rarity=RARE, editorial_weight=HERO)

    # ── action the geometry hides ──────────────────────────────────────────
    if ev.occluded_by_geometry and (ev.has("frag") or ev.projectile_path):
        add(OCCLUDED_SKILL,
            "the geometry hides the relationship between the shot and its "
            "target, so revealing it explains something the viewer cannot see",
            ("occluded_by_geometry", "frag"),
            [Grammar("XRAY_REBUILD",
                     ("FREEZE_HOLD", "WALL_XRAY", "WORLD_REBUILD"),
                     "freeze, ghost the wall, show the line, put it back")],
            narrative_purpose="geometry", rarity=RARE, editorial_weight=HERO)

    # ── brilliance, punished ───────────────────────────────────────────────
    if (ev.has("frag") and ev.death_after_us is not None
            and 0 < ev.death_after_us <= DEATH_SOON_US):
        add(HERO_THEN_DEATH,
            f"the player dies {ev.death_after_us/1000:.0f} ms after the action, "
            f"so the death is part of the same beat rather than a failure",
            ("frag", "death_after_us"),
            [Grammar("DEATH_AS_CUT", ("DEATH_FREEZE", "DEATH_EXPLOSION_MATCH"),
                     "let the death carry the cut"),
             Grammar("FLASH_REWIND_REPLAY",
                     ("DEATH_FREEZE", "DEATH_FLASH_MONTAGE", "DEATH_REWIND",
                      "SIDE_REPLAY"),
                     "freeze, flash the deaths, rewind, replay it clean")],
            result_truth=ev.round_result, narrative_purpose="hero",
            rarity=RARE, editorial_weight=FEATURE)

    # ── damage that tells a story ──────────────────────────────────────────
    if (ev.damage_by_user or 0) >= MEANINGFUL_DAMAGE:
        gr = [Grammar("LEDGER", ("DAMAGE_LEDGER_TICK",),
                      "show the damage accumulating on the target")]
        if ev.finisher_is_teammate:
            gr.append(Grammar(
                "ASSIST_STORY",
                ("DAMAGE_LEDGER_TICK", "POV_PIP", "ROUND_WIN_RELEASE"
                 if ev.round_result == "WIN" else "DAMAGE_LEDGER_TICK"),
                "the player did the work, a teammate finished it"))
        add(DAMAGE_STORY,
            f"{ev.damage_by_user} damage from the player, enough for the number "
            f"to mean something",
            ("damage_by_user",), gr, result_truth=ev.round_result,
            narrative_purpose="damage", editorial_weight=SUPPORT)

    # ── a teammate finishes what the player started ────────────────────────
    if ev.finisher_is_teammate and (ev.damage_by_user or 0) >= MEANINGFUL_DAMAGE:
        add(ASSISTED_FINISH,
            "the player did the damage and a teammate took the kill; the kill "
            "is never credited to the player",
            ("damage_by_user", "finisher_is_teammate"),
            [Grammar("ASSIST_PAYOFF", ("DAMAGE_LEDGER_TICK", "POV_PIP"),
                     "show the work, then where it ended")],
            result_truth=ev.round_result, narrative_purpose="assist",
            editorial_weight=SUPPORT)

    # ── a round actually won ───────────────────────────────────────────────
    if ev.round_result == "WIN":
        gr = [Grammar("RELEASE", ("ROUND_WIN_RELEASE",), "the payoff")]
        if (ev.teammates or 0) >= 1 and (ev.opponents or 0) >= 2:
            gr.append(Grammar("TEAM_RELEASE",
                              ("ROUND_WIN_RELEASE", "MODEL_MORPH"),
                              "the team takes its colours after the win"))
        add(ROUND_WIN_PAYOFF,
            "the demo's own score configstrings say this round was won",
            ("round_result",), gr, result_truth="WIN",
            narrative_purpose="victory", editorial_weight=FEATURE)

    # ── a team, present and outnumbered or not ─────────────────────────────
    if (ev.teammates or 0) >= 1 and (ev.opponents or 0) >= 2:
        add(TEAM_IDENTITY,
            f"{ev.teammates} teammates against {ev.opponents}, from the team "
            f"tables; a team round is a different story from a duel",
            ("teammates", "opponents"),
            [Grammar("TEAM_STORY", ("SLOW_MOTION",), "let the shape read"),
             Grammar("IDENTITY_MORPH", ("MODEL_MORPH",),
                     "the clan treatment, in a real team fight")],
            result_truth=ev.round_result, narrative_purpose="team",
            rarity=RARE, editorial_weight=HERO)

    # ── tracking, which wants to be watched not decorated ──────────────────
    if (ev.lg_contacts or 0) >= LG_BURST:
        add(LG_TRACKING,
            f"{ev.lg_contacts} lightning contacts: the skill is the tracking "
            f"itself, which decoration would hide",
            ("lg_contacts",),
            [Grammar("FPV_ONLY", ("SLOW_MOTION",),
                     "first person, restrained; the beam is the story"),
             Grammar("FPV_WITH_PULSES", ("SLOW_MOTION", "MATERIAL_FLASH"),
                     "light pulses off the contact rhythm")],
            forbidden_templates=("WORLD_STRIP", "MOSAIC_TILE_STEP",
                                 "MODEL_MORPH", "ENEMY_REVEAL_STEP"),
            result_truth=ev.round_result, narrative_purpose="duel",
            editorial_weight=FEATURE)

    # ── speed ──────────────────────────────────────────────────────────────
    if (ev.relative_speed_u_s or 0) >= FAST_U_S:
        add(HIGH_SPEED_CONTACT,
            f"{ev.relative_speed_u_s:.0f} u/s of relative motion, which widens "
            f"how far the moment can be slowed before it stops reading",
            ("relative_speed_u_s",),
            [Grammar("SPEED_HOLD", ("HIGH_SPEED_HOLD",), "hold the velocity")],
            narrative_purpose="movement", editorial_weight=SUPPORT)

    # ── movement as a seam ─────────────────────────────────────────────────
    if ev.movement_events >= 3 or ev.teleport_confirmed:
        gr = [Grammar("MOVEMENT_SEAM", ("MOVEMENT_MATCH_OVERLAP",),
                      "the landing is the cut")]
        if ev.movement_events >= 6:
            gr.append(Grammar("MOVEMENT_ACCENTS",
                              ("MOVEMENT_ACCENT", "MOVEMENT_MATCH_OVERLAP"),
                              "tick the jumps, cut on the last"))
        add(MOVEMENT_MATCH,
            f"{ev.movement_events} movement events"
            + (" including a confirmed teleport" if ev.teleport_confirmed else ""),
            ("movement_events",), gr, narrative_purpose="movement",
            editorial_weight=MICRO)

    # ── another point of view, only where one exists ───────────────────────
    if ev.multi_demo_recovered or ev.enemy_state_known:
        add(ENEMY_POV,
            "another recording of this same occurrence exists"
            if ev.multi_demo_recovered else
            "enough enemy state was recorded to approximate their viewpoint",
            ("multi_demo_recovered" if ev.multi_demo_recovered else "enemy_state_known",),
            [Grammar("POV_CUT", ("ENEMY_POV_INSERT",), "cut to their side"),
             Grammar("POV_CORNER", ("POV_PIP",), "keep both at once")],
            narrative_purpose="hero", rarity=RARE, editorial_weight=FEATURE)

    # ── a recorded netcode oddity ──────────────────────────────────────────
    if ev.netcode_anomaly:
        add(TELEPORT_GLITCH,
            f"a recorded {ev.netcode_anomaly}; the anomaly stays factual and "
            f"the treatment is authored",
            ("netcode_anomaly",),
            [Grammar("GLITCH", ("GLITCH_INSERT",), "stylise the discontinuity")],
            narrative_purpose="comedy", rarity=RARE, editorial_weight=SUPPORT)

    return tuple(out)


def allowed_templates(opportunities: Sequence[CreativeOpportunity]) -> tuple[str, ...]:
    """The union of what these opportunities permit, minus anything any one of
    them forbids. A tracking sequence that forbids world effects forbids them
    for the whole moment."""
    forbidden = {f for o in opportunities for f in o.forbidden_templates}
    out: list[str] = []
    for o in opportunities:
        for i in o.allowed_templates:
            if i not in out and i not in forbidden:
                out.append(i)
    return tuple(out)


def grammars_fitting(opportunities: Sequence[CreativeOpportunity],
                     slot_us: int) -> list[tuple[str, Grammar]]:
    """Every legitimate treatment whose envelope contains this slot."""
    out = []
    for o in opportunities:
        for g in o.grammars_for(slot_us):
            out.append((o.opportunity_type, g))
    return out
