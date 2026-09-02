"""Everything visible occupies score time. Effects are not post-processing.

THE PRINCIPLE. An effect pasted onto a finished clip cannot be part of the
music, because by the time it is applied every timing decision has already
been made. A world-strip that begins 300 ms before the drop, peaks on the
musical anchor and releases on the frag is not decoration -- it is composition,
and it changes how long the scene is, where the transition can start, and what
the neighbouring scene may do. So every ingredient declares a temporal
footprint, and the planner adds them up.

    pre_roll   the lead-in before anything is "on"
    active     the visible body
    peak       where the ingredient's own moment lands, inside active
    release    the tail after the peak

A freeze that adds 350 ms adds 350 ms to the movie. That is allowed, and it
is NOT a debt: nothing afterwards speeds up to pay it back unless a human
authored that speed-up. That rule was learned the hard way and is enforced
here as well as in edit_qa.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from fractions import Fraction
from typing import Any, Sequence

FOOTPRINT_VERSION = "temporal-footprint-v1.0.0"

# Effect intensities reuse the score's vocabulary.
from creative_suite.engine.score_timeline import (INTENSITIES,  # noqa: E402
                                                  INTENSITY_NORMAL)


@dataclass(frozen=True)
class TimeFootprint:
    """How much score time an ingredient occupies, and where its moment is."""
    pre_roll_us: int = 0
    active_us: int = 0
    peak_offset_us: int = 0        # from the start of active
    release_us: int = 0

    def __post_init__(self) -> None:
        for name in ("pre_roll_us", "active_us", "release_us"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if not 0 <= self.peak_offset_us <= max(0, self.active_us):
            raise ValueError("the peak must fall inside the active span")

    @property
    def total_occupied_us(self) -> int:
        return self.pre_roll_us + self.active_us + self.release_us

    def place_at_peak(self, peak_us: int) -> dict[str, int]:
        """Position the footprint so its peak lands on a musical moment.

        This is the usual direction of the calculation: the music says WHEN
        the moment is, and the ingredient arranges itself around it.
        """
        active_start = peak_us - self.peak_offset_us
        return {"start_us": active_start - self.pre_roll_us,
                "active_start_us": active_start,
                "peak_us": peak_us,
                "active_end_us": active_start + self.active_us,
                "end_us": active_start + self.active_us + self.release_us}

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["total_occupied_us"] = self.total_occupied_us
        return d


# ── retime ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RetimeEnvelope:
    """How far a scene may be slowed before it stops looking good.

    Music may CHOOSE the rate -- that is the accepted principle -- but only
    inside what the footage can carry. A rate outside the hard bounds is not
    a musical decision, it is a broken shot.
    """
    min_preferred_rate: float = 0.35
    max_preferred_rate: float = 1.0
    hard_min_rate: float = 0.20
    hard_max_rate: float = 1.0

    def __post_init__(self) -> None:
        if not (self.hard_min_rate <= self.min_preferred_rate
                <= self.max_preferred_rate <= self.hard_max_rate):
            raise ValueError("retime bounds must be ordered")
        if self.hard_min_rate <= 0:
            raise ValueError("rate must be positive")

    def allows(self, rate: float) -> bool:
        return self.hard_min_rate <= float(rate) <= self.hard_max_rate

    def prefers(self, rate: float) -> bool:
        return self.min_preferred_rate <= float(rate) <= self.max_preferred_rate

    def clamp(self, rate: float) -> float:
        return min(max(float(rate), self.hard_min_rate), self.hard_max_rate)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RetimeSegment:
    """One piece of a piecewise retime, at an exact requested rate.

    ``requested_rate`` is a Fraction so it stays exact -- the difference
    between what was asked for and what the encoder delivered is a
    measurement, and conflating the two is how a 1/1 became a 0.995.
    """
    src_in_us: int
    src_out_us: int
    requested_rate: Fraction
    label: str = ""
    authored_speedup: bool = False

    def __post_init__(self) -> None:
        if self.src_out_us <= self.src_in_us:
            raise ValueError("a retime segment needs positive source span")
        if self.requested_rate <= 0:
            raise ValueError("rate must be positive")

    @property
    def src_span_us(self) -> int:
        return self.src_out_us - self.src_in_us

    @property
    def edit_span_us(self) -> int:
        """How much SCORE time this piece occupies once retimed."""
        return int(round(self.src_span_us / float(self.requested_rate)))

    def to_dict(self) -> dict[str, Any]:
        return {"src_in_us": self.src_in_us, "src_out_us": self.src_out_us,
                "requested_rate": str(self.requested_rate),
                "edit_span_us": self.edit_span_us, "label": self.label,
                "authored_speedup": self.authored_speedup}


UNINTENDED_POST_SLOW_SPEEDUP = "UNINTENDED_POST_SLOW_SPEEDUP"


def check_no_temporal_debt(segments: Sequence[RetimeSegment]) -> list[dict]:
    """Slow motion never has to be paid back.

    A segment faster than 1.0 after a slow one is the exact defect the
    director rejected outright. Authored speed-ups are allowed and must say
    so; everything else is an error.
    """
    out: list[dict] = []
    seen_slow = False
    for seg in segments:
        rate = float(seg.requested_rate)
        if rate < 1.0:
            seen_slow = True
        if rate > 1.0 and not seg.authored_speedup:
            out.append({
                "check": UNINTENDED_POST_SLOW_SPEEDUP, "severity": "ERROR",
                "label": seg.label,
                "detail": f"{seg.label or 'segment'} runs at {rate:.3f}x "
                          f"without an authored speed-up" +
                          (" -- repaying slow-motion time" if seen_slow else "")})
    return out


def total_edit_span_us(segments: Sequence[RetimeSegment]) -> int:
    return sum(s.edit_span_us for s in segments)


def rate_for_span(src_span_us: int, target_edit_us: int) -> Fraction:
    """The exact rate that makes a source span occupy a musical interval."""
    if target_edit_us <= 0 or src_span_us <= 0:
        raise ValueError("spans must be positive")
    return Fraction(int(src_span_us), int(target_edit_us))


# ── effects, as schedulable things ──────────────────────────────────────────

OVERLAP_NONE = "NONE"
OVERLAP_ADJACENT = "ADJACENT"
OVERLAP_ANY = "ANY"
OVERLAP_MODES = (OVERLAP_NONE, OVERLAP_ADJACENT, OVERLAP_ANY)


@dataclass(frozen=True)
class EffectProfile:
    """What an effect needs, how long it takes, and where it belongs.

    This is the contract that turns an effect catalogue into something a
    score can SCHEDULE. Nothing here renders anything: it describes the
    footprint and the evidence an effect would require, so the planner can
    reason about it before a single frame exists.
    """
    effect_type: str
    semantic_trigger: str
    required_evidence: tuple[str, ...]
    footprint: TimeFootprint
    musical_roles: tuple[str, ...]
    intensity: str = INTENSITY_NORMAL
    allowed_overlap: str = OVERLAP_ADJACENT
    purpose: str = "NONE"
    min_duration_us: int = 0
    max_duration_us: int = 0
    notes: str = ""

    def __post_init__(self) -> None:
        if self.intensity not in INTENSITIES:
            raise ValueError(f"unknown intensity {self.intensity!r}")
        if self.allowed_overlap not in OVERLAP_MODES:
            raise ValueError(f"unknown overlap mode {self.allowed_overlap!r}")

    def fits_slot(self, slot_role: str, slot_duration_us: int) -> bool:
        if self.musical_roles and slot_role not in self.musical_roles:
            return False
        if self.min_duration_us and slot_duration_us < self.min_duration_us:
            return False
        return True

    def has_evidence(self, available: Sequence[str]) -> bool:
        return set(self.required_evidence) <= set(available)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["footprint"] = self.footprint.to_dict()
        d["required_evidence"] = list(self.required_evidence)
        d["musical_roles"] = list(self.musical_roles)
        return d


# ── transitions ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TransitionFootprint:
    """A transition occupies score time and belongs to two scenes at once."""
    family: str
    outgoing_anchor_us: int
    incoming_anchor_us: int
    start_us: int
    peak_us: int
    handoff_us: int
    end_us: int
    music_relationship: str = "NONE"
    purpose: str = "TRANSITION_TO_NEXT_SCENE"

    def __post_init__(self) -> None:
        if not (self.start_us <= self.peak_us <= self.handoff_us
                <= self.end_us):
            raise ValueError("transition moments must be ordered: "
                             "start <= peak <= handoff <= end")

    @property
    def duration_us(self) -> int:
        return self.end_us - self.start_us

    @property
    def outgoing_overlap_us(self) -> int:
        return self.handoff_us - self.start_us

    @property
    def incoming_overlap_us(self) -> int:
        return self.end_us - self.handoff_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(duration_us=self.duration_us,
                 outgoing_overlap_us=self.outgoing_overlap_us,
                 incoming_overlap_us=self.incoming_overlap_us)
        return d


# ── a small reference library, as evidence not implementation ───────────────
# These describe how known effect families WOULD participate in a score.
# Nothing renders them; the Pandora atlas remains unimplemented.

WORLD_STRIP_1VX = EffectProfile(
    effect_type="WORLD_STRIP_1VX",
    semantic_trigger="1vX context entering its payoff",
    required_evidence=("multi_enemy_positions", "one_v_x_context"),
    footprint=TimeFootprint(pre_roll_us=300_000, active_us=900_000,
                            peak_offset_us=700_000, release_us=200_000),
    musical_roles=("BUILD", "BREATH", "CLIMAX"),
    intensity="SPECTACLE", allowed_overlap=OVERLAP_NONE,
    purpose="SHOW_1VX_THREATS", min_duration_us=1_400_000,
    max_duration_us=2_500_000,
    notes="world thins before the drop, enemies reveal on accents, "
          "restores on the hero event")

BLOOD_WIPE = EffectProfile(
    effect_type="BLOOD_WIPE",
    semantic_trigger="player death or gib",
    required_evidence=("enemy_death",),
    footprint=TimeFootprint(active_us=350_000, peak_offset_us=120_000),
    musical_roles=("TRANSITION", "HERO", "CLIMAX"),
    intensity="HERO", allowed_overlap=OVERLAP_ADJACENT,
    purpose="TRANSITION_TO_NEXT_SCENE", min_duration_us=150_000,
    max_duration_us=500_000,
    notes="the death itself becomes the wipe into the next scene")

MODEL_MORPH = EffectProfile(
    effect_type="MODEL_MORPH",
    semantic_trigger="hero moment or low health",
    required_evidence=("player_entity",),
    footprint=TimeFootprint(pre_roll_us=200_000, active_us=1_200_000,
                            peak_offset_us=900_000, release_us=300_000),
    musical_roles=("BUILD",),
    intensity="HERO", allowed_overlap=OVERLAP_ADJACENT,
    purpose="EMPHASIZE_LOW_HP", min_duration_us=500_000,
    max_duration_us=2_000_000,
    notes="needs a sustained harmonic rise; a transient-only section is a "
          "bad fit because the morph has no arrival to land on")

REFERENCE_EFFECTS = (WORLD_STRIP_1VX, BLOOD_WIPE, MODEL_MORPH)
