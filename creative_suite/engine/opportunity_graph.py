"""What we have, what the score needs, and which pairs are compatible.

THE IDEA. A score slot is a question -- "eight seconds, sparse, one hard
anchor at the end: what fits here?" -- and the moment library is the set of
possible answers. This module projects both sides into comparable shapes and
scores the match componentwise, so the planner can propose and a human can
overrule with the reasons in front of them.

IT IS A PROJECTION, NOT A NEW DATABASE. Nothing here rescans demos or invents
evidence. It reads what recognition already established and reshapes it into
creative properties. Anything the evidence does not support stays UNKNOWN
rather than becoming a default that later reads as a fact.

NO SINGLE OPAQUE SCORE. A ranking exists because something has to be first,
but every candidate carries its components: duration, energy, rhythm, hero
anchor, negative space, camera, retime, transition, narrative, intensity and
availability. A planner that answers only with a number cannot be argued
with, and this project has already learned what confident unexplained numbers
cost.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Sequence

UNKNOWN = "UNKNOWN"
PROJECTION_VERSION = "opportunity-graph-v1.0.0"

# ── what a moment offers ────────────────────────────────────────────────────

# Scene kinds the planner can reason about. Extend as recognition grows.
KIND_LG_TRACKING = "LG_TRACKING"
KIND_ROCKET_IMPACT = "ROCKET_IMPACT"
KIND_RAIL_HIT = "RAIL_HIT"
KIND_DODGE = "DODGE"
KIND_MOVEMENT = "MOVEMENT"
KIND_MULTIKILL = "MULTIKILL"
KIND_ONE_V_X = "ONE_V_X"
KIND_TEAM_ROUND = "TEAM_ROUND"
KIND_TELEFRAG = "TELEFRAG"
KIND_GAUNTLET = "GAUNTLET"

SCENE_KINDS = (KIND_LG_TRACKING, KIND_ROCKET_IMPACT, KIND_RAIL_HIT, KIND_DODGE,
               KIND_MOVEMENT, KIND_MULTIKILL, KIND_ONE_V_X, KIND_TEAM_ROUND,
               KIND_TELEFRAG, KIND_GAUNTLET)

# Which kinds suit which slot roles. Preference, not a gate: an unusual pairing
# is allowed to score low rather than be forbidden.
ROLE_AFFINITY: dict[str, tuple[str, ...]] = {
    "TRACKING": (KIND_LG_TRACKING, KIND_DODGE),
    "BREATH": (KIND_MOVEMENT, KIND_DODGE),
    "SETUP": (KIND_MOVEMENT, KIND_TEAM_ROUND),
    "BUILD": (KIND_DODGE, KIND_MOVEMENT, KIND_ONE_V_X),
    "HERO": (KIND_ROCKET_IMPACT, KIND_RAIL_HIT, KIND_TELEFRAG, KIND_MULTIKILL),
    "CLIMAX": (KIND_MULTIKILL, KIND_ONE_V_X, KIND_ROCKET_IMPACT, KIND_RAIL_HIT),
    "MULTIKILL": (KIND_MULTIKILL, KIND_ONE_V_X),
    "MONTAGE": (KIND_MOVEMENT, KIND_GAUNTLET, KIND_RAIL_HIT),
    "MOVEMENT": (KIND_MOVEMENT, KIND_DODGE),
    "INTRO": (KIND_MOVEMENT, KIND_TEAM_ROUND),
    "OUTRO": (KIND_TEAM_ROUND, KIND_MOVEMENT),
    "TRANSITION": (KIND_MOVEMENT, KIND_TELEFRAG),
}

# Scenes whose payoff is one instant, versus ones that need room to read.
INSTANT_PAYOFF = (KIND_ROCKET_IMPACT, KIND_RAIL_HIT, KIND_TELEFRAG,
                  KIND_GAUNTLET)
SUSTAINED = (KIND_LG_TRACKING, KIND_TEAM_ROUND, KIND_ONE_V_X, KIND_MOVEMENT)


@dataclass(frozen=True)
class MomentCandidate:
    """One gameplay moment, projected into creative properties.

    Every field the evidence does not support is None or UNKNOWN. That is
    deliberate: a default that looks like data is how a planner ends up
    confidently placing a scene on something nobody ever measured.
    """
    frag_id: int
    scene_kind: str
    useful_duration_us: int
    hero_event_kind: str
    hero_offset_us: int                  # from the scene start
    weapon: str = UNKNOWN
    map_name: str = UNKNOWN
    game_mode: str = UNKNOWN
    hero_confidence: float | None = None
    enemy_count: int | None = None
    teammate_count: int | None = None
    round_result: str = UNKNOWN
    damage_dealt: float | None = None
    damage_received: float | None = None
    attacker_speed: float | None = None
    victim_speed: float | None = None
    has_projectile_path: bool = False
    one_v_x: bool = False
    clutch: bool = False
    team_fight: bool = False
    camera_options: tuple[str, ...] = ("FPV",)
    clean_camera_feasible: bool = False
    retime_min_rate: float = 1.0         # 1.0 = no slow motion supported
    retime_max_rate: float = 1.0
    transition_options: tuple[str, ...] = ()
    motif_key: str | None = None         # for montage grouping
    moment_state: str = "AVAILABLE"
    evidence: tuple[tuple[str, str], ...] = ()

    @property
    def available(self) -> bool:
        return self.moment_state in ("AVAILABLE", "SHORTLISTED")

    @property
    def supports_slow_motion(self) -> bool:
        return self.retime_min_rate < 1.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["camera_options"] = list(self.camera_options)
        d["transition_options"] = list(self.transition_options)
        d["evidence"] = [list(kv) for kv in self.evidence]
        d["available"] = self.available
        return d


# ── movement speed widens what slow motion may do ───────────────────────────

def retime_envelope_for_speed(relative_speed: float | None, *,
                              base_min: float = 0.55,
                              floor: float = 0.25) -> tuple[float, float]:
    """Faster relative motion earns a DEEPER slow-motion envelope.

    Speed does not choose the rate -- the music still does that. It widens
    the range the footage can carry, because fast motion survives being
    slowed and slow motion of slow motion is just a still frame.
    """
    if relative_speed is None:
        return base_min, 1.0
    speed = max(0.0, float(relative_speed))
    # 400 u/s is ordinary; 1200+ is exceptional.
    widen = min(1.0, max(0.0, (speed - 400.0) / 800.0))
    return round(base_min - (base_min - floor) * widen, 3), 1.0


# ── fit components ──────────────────────────────────────────────────────────

FIT_COMPONENTS = ("DURATION_FIT", "ENERGY_FIT", "RHYTHM_FIT",
                  "HERO_ANCHOR_FIT", "NEGATIVE_SPACE_FIT", "CAMERA_FIT",
                  "RETIME_FIT", "TRANSITION_FIT", "NARRATIVE_FIT",
                  "INTENSITY_FIT", "CONSUMPTION_AVAILABILITY")

# What each component is worth. Availability is a gate, not a weight.
WEIGHTS = {"DURATION_FIT": 0.22, "ENERGY_FIT": 0.12, "RHYTHM_FIT": 0.12,
           "HERO_ANCHOR_FIT": 0.20, "NEGATIVE_SPACE_FIT": 0.08,
           "CAMERA_FIT": 0.06, "RETIME_FIT": 0.08, "TRANSITION_FIT": 0.04,
           "NARRATIVE_FIT": 0.08, "INTENSITY_FIT": 0.00}


@dataclass(frozen=True)
class CandidateFit:
    """One moment measured against one slot, with the reasons kept."""
    frag_id: int
    slot_role: str
    slot_start_us: int
    components: tuple[tuple[str, float], ...]
    total: float
    eligible: bool
    why: str
    blocked_reason: str = ""

    def component(self, name: str) -> float:
        return dict(self.components).get(name, 0.0)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["components"] = {k: v for k, v in self.components}
        return d


def _duration_fit(slot_us: int, moment_us: int) -> float:
    """A moment that does not fit the interval is the commonest bad match."""
    if slot_us <= 0 or moment_us <= 0:
        return 0.0
    ratio = moment_us / slot_us
    if ratio > 1.15:                       # too long for the slot
        return max(0.0, 1.0 - (ratio - 1.15))
    if ratio < 0.35:                       # leaves the slot mostly empty
        return max(0.0, ratio / 0.35 * 0.6)
    return 1.0 - abs(1.0 - ratio) * 0.4


def _clip(x: float) -> float:
    return round(min(1.0, max(0.0, float(x))), 4)


def score_candidate(candidate: MomentCandidate, slot: Any, *,
                    narrative_beat: str | None = None,
                    narrative_wants: Sequence[str] = ()) -> CandidateFit:
    """Measure one moment against one slot. Components first, total second."""
    ev = slot.evidence
    comps: dict[str, float] = {}

    comps["DURATION_FIT"] = _clip(
        _duration_fit(slot.duration_us, candidate.useful_duration_us))

    # Sustained gameplay wants calm music; instant payoffs want energy.
    if candidate.scene_kind in SUSTAINED:
        comps["ENERGY_FIT"] = _clip(1.0 - ev.mean_energy)
        comps["RHYTHM_FIT"] = _clip(1.0 - min(1.0, ev.onset_density_per_s / 4.0))
    else:
        comps["ENERGY_FIT"] = _clip(ev.mean_energy)
        comps["RHYTHM_FIT"] = _clip(min(1.0, ev.percussive_density_per_s / 2.0))

    # An instant payoff needs something sharp to land on.
    if candidate.scene_kind in INSTANT_PAYOFF:
        comps["HERO_ANCHOR_FIT"] = _clip(min(1.0, ev.hard_anchor_count / 2.0))
    else:
        comps["HERO_ANCHOR_FIT"] = _clip(0.5 + 0.5 * min(1.0, ev.hard_anchor_count))

    comps["NEGATIVE_SPACE_FIT"] = _clip(
        1.0 if ev.negative_space_us > 0 and candidate.scene_kind in INSTANT_PAYOFF
        else 0.5)

    affinity = ROLE_AFFINITY.get(slot.role, ())
    comps["INTENSITY_FIT"] = _clip(1.0 if candidate.scene_kind in affinity else 0.35)

    comps["CAMERA_FIT"] = _clip(
        1.0 if len(candidate.camera_options) > 1 or
        candidate.clean_camera_feasible else 0.6)

    # Slow motion is only worth something where the slot gives room for it.
    wants_slow = slot.role in ("HERO", "CLIMAX", "BUILD")
    comps["RETIME_FIT"] = _clip(
        1.0 if candidate.supports_slow_motion and wants_slow
        else 0.7 if not wants_slow else 0.3)

    comps["TRANSITION_FIT"] = _clip(
        1.0 if candidate.transition_options else 0.5)

    if narrative_beat and narrative_wants:
        comps["NARRATIVE_FIT"] = _clip(
            1.0 if candidate.scene_kind in narrative_wants else 0.2)
    else:
        comps["NARRATIVE_FIT"] = 0.5

    comps["CONSUMPTION_AVAILABILITY"] = 1.0 if candidate.available else 0.0

    total = round(sum(WEIGHTS[k] * v for k, v in comps.items()
                      if k in WEIGHTS), 4)
    eligible = candidate.available
    blocked = "" if eligible else (
        f"frag {candidate.frag_id} is {candidate.moment_state} and cannot be "
        f"planned again without an explicit reuse override")

    bits = [f"{candidate.useful_duration_us / 1e6:.1f}s into a "
            f"{slot.duration_us / 1e6:.1f}s {slot.role.lower()} slot"]
    if candidate.scene_kind in INSTANT_PAYOFF:
        bits.append(f"{ev.hard_anchor_count} hard anchors for the payoff")
    else:
        bits.append(f"{ev.onset_density_per_s:.1f} onsets/s leaves the "
                    f"gameplay audible")
    if candidate.supports_slow_motion and wants_slow:
        bits.append(f"retime down to {candidate.retime_min_rate:.2f}x available")
    return CandidateFit(candidate.frag_id, slot.role, slot.start_us,
                        tuple(sorted(comps.items())), total, eligible,
                        "; ".join(bits), blocked)


def rank_candidates(candidates: Sequence[MomentCandidate], slot: Any, *,
                    top_n: int = 5, include_blocked: bool = False,
                    narrative_beat: str | None = None,
                    narrative_wants: Sequence[str] = ()) -> list[CandidateFit]:
    """Best answers to one slot's question, reasons attached."""
    fits = [score_candidate(c, slot, narrative_beat=narrative_beat,
                            narrative_wants=narrative_wants)
            for c in candidates]
    if not include_blocked:
        fits = [f for f in fits if f.eligible]
    return sorted(fits, key=lambda f: f.total, reverse=True)[:top_n]


def montage_groups(candidates: Sequence[MomentCandidate], *,
                   min_size: int = 4) -> dict[str, list[MomentCandidate]]:
    """Distinct short moments sharing a motif: the montage's raw material.

    This is where ordinary footage becomes valuable. Eight unremarkable
    rocket jumps through the same doorway are worth more to a high-density
    bar than one elite frag would be.
    """
    groups: dict[str, list[MomentCandidate]] = {}
    for c in candidates:
        if c.motif_key and c.available:
            groups.setdefault(c.motif_key, []).append(c)
    return {k: v for k, v in groups.items() if len(v) >= min_size}
