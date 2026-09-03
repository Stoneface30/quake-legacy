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
from creative_suite.engine import visual_focus as vf

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


# ── heuristics, which are not laws ──────────────────────────────────────────
# A threshold that decides whether a treatment is INTERESTING is a creative
# judgement and must say so. A rule that decides whether a treatment would be
# a LIE is a truth constraint and is not negotiable.

HARD_TRUTH = "HARD_TRUTH"
CREATIVE_HEURISTIC = "CREATIVE_HEURISTIC"

DIRECTOR_STATED = "DIRECTOR_STATED"
OBSERVED = "OBSERVED"
ASSUMED = "ASSUMED"


@dataclass(frozen=True)
class Heuristic:
    """A tunable creative threshold, with its reasoning attached."""
    name: str
    value: float
    unit: str
    reason: str
    provenance: str = ASSUMED
    version: str = "v1"
    override: float | None = None

    @property
    def effective(self) -> float:
        return self.value if self.override is None else self.override

    @property
    def overridden(self) -> bool:
        return self.override is not None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(effective=self.effective, overridden=self.overridden,
                 kind=CREATIVE_HEURISTIC)
        return d


HEURISTICS: dict[str, Heuristic] = {h.name: h for h in (
    Heuristic("flyby_close_pass_u", 220.0, "units",
              "near enough that the pass is felt rather than noticed; a guess "
              "from the splash radius, not a measurement",
              ASSUMED),
    Heuristic("damage_story_min", 60.0, "damage",
              "below roughly a third of a fresh player's effective health the "
              "number explains little; 59 may still tell a story and 70 of "
              "scattered spam may not, which is why strength is reported too",
              ASSUMED),
    Heuristic("hero_death_strong_us", 1_000_000.0, "us",
              "the director's own framing: dying within about a second of the "
              "action makes the death part of the same beat",
              DIRECTOR_STATED),
    Heuristic("hero_death_contextual_us", 2_500_000.0, "us",
              "beyond a second the death is still relatable but weaker; past "
              "this it is usually a different moment",
              DIRECTOR_STATED),
    Heuristic("lg_burst_contacts", 8.0, "contacts",
              "enough sustained contact for tracking to read as tracking",
              ASSUMED),
    Heuristic("fast_relative_u_s", 700.0, "u/s",
              "relative motion above which deeper slow motion still reads",
              ASSUMED),
)}


def heuristic(name: str) -> Heuristic:
    return HEURISTICS[name]


def override_heuristic(name: str, value: float | None) -> Heuristic:
    """The director may move a creative threshold. A hard truth has no such
    door."""
    from dataclasses import replace as _replace
    HEURISTICS[name] = _replace(HEURISTICS[name], override=value)
    return HEURISTICS[name]


# How strongly the evidence supports a treatment. Not every opportunity is
# equally earned, and a weak one should not be mistaken for a strong one.
STRONG, CONTEXTUAL, WEAK = "STRONG", "CONTEXTUAL", "WEAK"
STRENGTHS = (WEAK, CONTEXTUAL, STRONG)


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
    # Where things happen inside the scene. A scene has phases, and a
    # constraint that ignores them either forbids too much or protects
    # nothing.
    scene_start_us: int = 0
    scene_end_us: int = 0
    hero_us: int | None = None            # the payoff instant
    lg_track_start_us: int | None = None  # sustained tracking, if any
    lg_track_end_us: int | None = None
    victim_effective_hp: int | None = None

    def has(self, kind: str) -> bool:
        return kind in self.kinds

    @property
    def span(self) -> tuple[int, int]:
        if self.scene_end_us > self.scene_start_us:
            return (self.scene_start_us, self.scene_end_us)
        return (0, max(self.source_useful_us, 1))

    @property
    def tracking_interval(self) -> tuple[int, int] | None:
        if self.lg_track_start_us is None or self.lg_track_end_us is None:
            return None
        if self.lg_track_end_us <= self.lg_track_start_us:
            return None
        return (self.lg_track_start_us, self.lg_track_end_us)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceWindow:
    """What THIS occurrence actually gives us to work with.

    A grammar is reusable; the duration it can occupy is not. "PURE_FPV is
    0.3 to 8.0 seconds" would eventually mean almost anything fits almost
    anywhere. The real envelope comes from this window: how much usable
    source exists, where the payoff sits inside it, and how much lead-in and
    aftermath the action needs to stay comprehensible.
    """
    useful_us: int                     # total usable source
    hero_offset_us: int = 0            # where the payoff sits inside it
    pre_context_us: int = 0            # usable lead-in before the payoff
    post_context_us: int = 0           # usable aftermath
    replay_source_us: int = 0          # what can be shown again
    min_recognition_us: int = 600_000  # below this the action stops reading
    min_aftermath_us: int = 150_000
    camera_available: bool = False     # is a second angle actually available

    def __post_init__(self) -> None:
        if self.useful_us <= 0:
            raise ValueError("a source window with no usable source is not one")
        if self.min_recognition_us > self.useful_us:
            raise ValueError(
                "this occurrence has less source than the action needs to be "
                "comprehensible; it cannot be trimmed into a slot")

    @property
    def floor_us(self) -> int:
        """The least this action can occupy and still be understood."""
        return max(self.min_recognition_us + self.min_aftermath_us,
                   min(self.useful_us, self.min_recognition_us))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["floor_us"] = self.floor_us
        return d


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
        """The templates' own range, before any particular moment is chosen.
        Useful for library questions; never for deciding whether an
        occurrence fits a slot."""
        return et.combined_envelope(list(self.templates))

    def envelope_for(self, window: "SourceWindow") -> t.TemporalElasticity:
        """What THIS occurrence can honestly occupy under this grammar.

        The templates say how far each operator may stretch. The window says
        how much source there is to stretch, and how much of it the action
        needs in order to remain comprehensible. The answer is the narrower
        of the two, floored by what the action cannot go below.
        """
        base = self.elasticity
        source = window.useful_us
        replay = window.replay_source_us
        uses_replay = any(i in ("SIDE_REPLAY", "PROJECTILE_REPLAY",
                                "PROJECTILE_FOLLOW", "GRENADE_ARC")
                          for i in self.templates)
        if uses_replay and replay <= 0:
            # nothing to replay: this grammar is not available here
            return t.TemporalElasticity(0, 0, 0, 0, len(self.templates))
        # a retime can slow the source but cannot invent more of it
        slowest = 5.0            # the deepest usable rate is about 0.2x
        ceiling = int(source * slowest) + (int(replay * slowest) if uses_replay else 0)
        added = sum(et.get(i).envelope.hard_max_us for i in self.templates
                    if et.get(i).operator in (t.FREEZE, t.INSERT,
                                              t.SYNTHETIC_INSERT, t.REPEAT,
                                              t.STUTTER))
        hi = min(base.max_us, ceiling + added)
        lo = max(window.floor_us, min(base.min_us, hi))
        plo = max(lo, min(base.preferred_min_us, hi))
        phi = max(plo, min(base.preferred_max_us, hi))
        return t.TemporalElasticity(lo, max(hi, lo), plo, phi, len(self.templates))

    @property
    def weakest_provenance(self) -> str:
        return min((et.template_provenance(i) for i in self.templates),
                   key=lambda p: et.PROVENANCE_RANK[p], default=et.DESIGN_ESTIMATE)

    @property
    def heaviest_weight(self) -> str:
        order = {w: i for i, w in enumerate(WEIGHTS)}
        return max((editorial_weight(i)[0] for i in self.templates),
                   key=lambda w: order[w], default=SUPPORT)

    def fits(self, slot_us: int, window: "SourceWindow | None" = None) -> bool:
        el = self.envelope_for(window) if window is not None else self.elasticity
        return el.max_us > 0 and el.fits(slot_us)

    def to_dict(self, window: "SourceWindow | None" = None) -> dict[str, Any]:
        el = self.envelope_for(window) if window is not None else self.elasticity
        return {"name": self.name, "templates": list(self.templates),
                "moment_specific": window is not None,
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
    constraints: tuple[Any, ...] = ()      # visual_focus.ScopedConstraint
    focuses: tuple[Any, ...] = ()          # visual_focus.VisualFocus
    strength: str = STRONG
    forbidden_templates: tuple[str, ...] = ()   # forbidden for the WHOLE moment
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

    def grammars_for(self, slot_us: int,
                     window: "SourceWindow | None" = None) -> tuple[Grammar, ...]:
        return tuple(g for g in self.grammars if g.fits(slot_us, window))

    def permits(self, template_id: str, at_us: int) -> tuple[bool, str]:
        """Whether this opportunity allows a template at an instant."""
        if template_id in self.forbidden_templates:
            return (False, f"{template_id} is refused across this whole moment")
        return vf.permitted_at(template_id, at_us, self.focuses, self.constraints)

    def free_for(self, template_id: str, span: tuple[int, int]
                 ) -> list[tuple[int, int]]:
        """Where inside the scene this template IS allowed."""
        if template_id in self.forbidden_templates:
            return []
        return vf.free_intervals(span, template_id, self.focuses, self.constraints)

    def to_dict(self) -> dict[str, Any]:
        return {"moment_ref": self.moment_ref,
                "opportunity_type": self.opportunity_type, "why": self.why,
                "evidence_used": list(self.evidence_used),
                "result_truth": self.result_truth,
                "narrative_purpose": self.narrative_purpose,
                "rarity": self.rarity, "editorial_weight": self.editorial_weight,
                "strength": self.strength,
                "constraints": [c.to_dict() for c in self.constraints],
                "focuses": [f.to_dict() for f in self.focuses],
                "allowed_templates": list(self.allowed_templates),
                "forbidden_templates": list(self.forbidden_templates),
                "grammars": [g.to_dict() for g in self.grammars],
                "version": OPPORTUNITY_VERSION}


# ── generation: evidence in, opportunities out ──────────────────────────────
#
# Each rule states the signature that earns a treatment. Nothing here consults
# a duration, a slot, or a song.

# The numbers below come from HEURISTICS, so they can be reasoned about and
# overridden. They are creative judgements, not truth constraints.


def _h(name: str) -> float:
    return heuristic(name).effective


def _damage_strength(ev: "MomentEvidence") -> tuple[str, dict[str, Any]]:
    """How strongly the damage tells a story.

    Absolute damage is only one component. A hundred points into a fresh
    player reads differently from a hundred into an almost-dead one, and a
    teammate taking the finish is exactly when the viewer might otherwise
    misread who did the work.
    """
    dmg = ev.damage_by_user or 0
    floor = _h("damage_story_min")
    parts: dict[str, Any] = {"damage": dmg, "threshold": floor}
    score = dmg / max(floor, 1.0)
    if ev.victim_effective_hp:
        share = dmg / max(ev.victim_effective_hp, 1)
        parts["share_of_target"] = round(share, 3)
        score = max(score, share * 2.0)
    if ev.finisher_is_teammate:
        parts["teammate_finished"] = True
        score += 0.5      # the viewer could otherwise misread the contribution
    parts["score"] = round(score, 3)
    return (STRONG if score >= 1.6 else CONTEXTUAL if score >= 1.0 else WEAK,
            parts)


def _flyby_strength(ev: "MomentEvidence") -> tuple[str, dict[str, Any]]:
    """Distance is the obvious component and not the only one. A slow
    projectile drifting past is not the same event as a rocket tearing by."""
    d = ev.projectile_close_pass_u
    parts: dict[str, Any] = {"closest_u": d, "threshold_u": _h("flyby_close_pass_u")}
    if d is None:
        return (WEAK, parts)
    score = max(0.0, 1.0 - d / max(_h("flyby_close_pass_u"), 1.0)) * 2.0
    if ev.relative_speed_u_s:
        parts["relative_speed_u_s"] = ev.relative_speed_u_s
        score += min(ev.relative_speed_u_s / 1000.0, 1.0)
    if ev.projectile_recorded_fraction is not None:
        parts["recorded_fraction"] = ev.projectile_recorded_fraction
    parts["score"] = round(score, 3)
    return (STRONG if score >= 1.6 else CONTEXTUAL if score >= 0.9 else WEAK,
            parts)


def _hero_death_strength(after_us: int) -> tuple[str, dict[str, Any]]:
    """The director's own framing: within about a second the death is part of
    the same beat; beyond that it weakens; past two and a half seconds it is
    usually a different moment."""
    strong = _h("hero_death_strong_us")
    contextual = _h("hero_death_contextual_us")
    parts = {"death_after_us": after_us, "strong_below_us": strong,
             "contextual_below_us": contextual}
    if after_us <= strong:
        return (STRONG, parts)
    if after_us <= contextual:
        return (CONTEXTUAL, parts)
    return (WEAK, parts)


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
        hero_at = ev.hero_us if ev.hero_us is not None else ev.span[1]
        add(HERO_PROJECTILE,
            f"a {ev.weapon or 'projectile'} kill whose flight was recorded, so "
            f"the trajectory can be shown rather than asserted",
            ("frag", "projectile_path"), gr,
            focuses=(vf.projectile_focus(max(ev.span[0], hero_at - 1_500_000),
                                         min(ev.span[1], hero_at + 500_000)),),
            result_truth=ev.round_result, narrative_purpose="hero",
            rarity=OCCASIONAL, editorial_weight=FEATURE)

    # ── a projectile that passes close to the camera ───────────────────────
    if (ev.projectile_path and ev.projectile_close_pass_u is not None
            and ev.projectile_close_pass_u <= _h("flyby_close_pass_u")):
        fly_strength, fly_parts = _flyby_strength(ev)
        add(PROJECTILE_FLYBY,
            f"a projectile passes {ev.projectile_close_pass_u:.0f} units from "
            f"the camera ({fly_strength.lower()}, components {fly_parts})",
            ("projectile_path", "projectile_close_pass_u"),
            [Grammar("FLYBY_BRIDGE", ("ROCKET_FLYBY_BRIDGE",),
                     "the pass carries us into the next scene"),
             Grammar("FLYBY_FOLLOW", ("PROJECTILE_FOLLOW", "ROCKET_FLYBY_BRIDGE"),
                     "follow it in, hand off on the closest approach")],
            strength=fly_strength, narrative_purpose="transition",
            editorial_weight=FEATURE)

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
        track = ev.tracking_interval
        reveal_end = track[0] if track else ev.span[0] + 3_000_000
        add(ONE_VX_REVEAL,
            f"one against {ev.alive_enemy}, from death events inside the round",
            ("alive_self", "alive_enemy", "round_result"), gr,
            focuses=(vf.threat_focus(ev.span[0], max(reveal_end, ev.span[0] + 1)),),
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
            and 0 < ev.death_after_us <= _h("hero_death_contextual_us")):
        strength, parts = _hero_death_strength(ev.death_after_us)
        add(HERO_THEN_DEATH,
            f"the player dies {ev.death_after_us/1000:.0f} ms after the action "
            f"({strength.lower()}: the director's framing puts the same beat "
            f"under {parts['strong_below_us']/1000:.0f} ms)",
            ("frag", "death_after_us"),
            [Grammar("DEATH_AS_CUT", ("DEATH_FREEZE", "DEATH_EXPLOSION_MATCH"),
                     "let the death carry the cut"),
             Grammar("FLASH_REWIND_REPLAY",
                     ("DEATH_FREEZE", "DEATH_FLASH_MONTAGE", "DEATH_REWIND",
                      "SIDE_REPLAY"),
                     "freeze, flash the deaths, rewind, replay it clean")],
            strength=strength, result_truth=ev.round_result,
            narrative_purpose="hero", rarity=RARE, editorial_weight=FEATURE)

    # ── damage that tells a story ──────────────────────────────────────────
    if (ev.damage_by_user or 0) >= _h("damage_story_min"):
        dmg_strength, dmg_parts = _damage_strength(ev)
        gr = [Grammar("LEDGER", ("DAMAGE_LEDGER_TICK",),
                      "show the damage accumulating on the target")]
        if ev.finisher_is_teammate:
            gr.append(Grammar(
                "ASSIST_STORY",
                ("DAMAGE_LEDGER_TICK", "POV_PIP", "ROUND_WIN_RELEASE"
                 if ev.round_result == "WIN" else "DAMAGE_LEDGER_TICK"),
                "the player did the work, a teammate finished it"))
        add(DAMAGE_STORY,
            f"{ev.damage_by_user} damage from the player ({dmg_strength.lower()}, "
            f"components {dmg_parts})",
            ("damage_by_user",), gr, strength=dmg_strength,
            # Only where the numbers are actually on screen. A ledger that
            # claimed the whole scene would ban world effects everywhere,
            # which is the coarse veto this architecture exists to avoid.
            focuses=(vf.damage_focus(
                max(ev.span[0], (ev.hero_us or ev.span[1]) - 1_500_000),
                min(ev.span[1], (ev.hero_us or ev.span[1]) + 500_000)),),
            result_truth=ev.round_result, narrative_purpose="damage",
            editorial_weight=SUPPORT)

    # ── a teammate finishes what the player started ────────────────────────
    if ev.finisher_is_teammate and (ev.damage_by_user or 0) >= _h("damage_story_min"):
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
    if (ev.lg_contacts or 0) >= _h("lg_burst_contacts"):
        track = ev.tracking_interval or ev.span
        add(LG_TRACKING,
            f"{ev.lg_contacts} lightning contacts over "
            f"{(track[1]-track[0])/1000:.0f} ms: the skill is the tracking "
            f"itself, and anything in front of it hides the thing worth "
            f"watching",
            ("lg_contacts",),
            [Grammar("FPV_ONLY", ("SLOW_MOTION",),
                     "first person, restrained; the beam is the story"),
             Grammar("FPV_WITH_PULSES", ("SLOW_MOTION", "MATERIAL_FLASH"),
                     "light pulses off the contact rhythm")],
            # Scoped to the tracking itself. Before and after it, another
            # opportunity may legitimately open the world up.
            focuses=(vf.tracking_focus(*track),),
            result_truth=ev.round_result, narrative_purpose="duel",
            editorial_weight=FEATURE)

    # ── speed ──────────────────────────────────────────────────────────────
    if (ev.relative_speed_u_s or 0) >= _h("fast_relative_u_s"):
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


def allowed_templates(opportunities: Sequence[CreativeOpportunity],
                      at_us: int | None = None) -> tuple[str, ...]:
    """What these opportunities permit, optionally at one instant.

    Without a time this is the scene's whole vocabulary: everything earned,
    minus what is refused across the entire moment. With a time it also
    honours the scoped constraints and visual focuses, which is how a world
    strip can be legal before a tracking interval and refused inside it.
    """
    forbidden = {f for o in opportunities for f in o.forbidden_templates}
    out: list[str] = []
    for o in opportunities:
        for i in o.allowed_templates:
            if i in out or i in forbidden:
                continue
            if at_us is not None:
                blocked = False
                for other in opportunities:
                    ok, _why = other.permits(i, at_us)
                    if not ok:
                        blocked = True
                        break
                if blocked:
                    continue
            out.append(i)
    return tuple(out)


def windows_for(opportunities: Sequence[CreativeOpportunity], template_id: str,
                span: tuple[int, int]) -> list[tuple[int, int]]:
    """Where in the scene this template may run, after every focus and
    constraint from every opportunity has had its say."""
    if any(template_id in o.forbidden_templates for o in opportunities):
        return []
    focuses = [f for o in opportunities for f in o.focuses]
    constraints = [c for o in opportunities for c in o.constraints]
    return vf.free_intervals(span, template_id, focuses, constraints)


def grammars_fitting(opportunities: Sequence[CreativeOpportunity], slot_us: int,
                     window: SourceWindow | None = None
                     ) -> list[tuple[str, Grammar]]:
    """Every legitimate treatment whose envelope contains this slot.

    Pass the occurrence's own source window and the envelopes become
    moment-specific rather than the templates' generic reach.
    """
    out = []
    for o in opportunities:
        for g in o.grammars_for(slot_us, window):
            out.append((o.opportunity_type, g))
    return out
