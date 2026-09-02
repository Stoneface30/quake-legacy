"""The deterministic plan: what the movie intends to be, before it exists.

A SequenceScorePlanV1 is editorial INTENT laid onto a fixed musical canvas.
It is not a render and it is not evidence of anything delivered -- the
diagnostic sheet's job is to put intent and delivery side by side, and that
only works if the two are different objects.

WHY IT HASHES. The plan identity is a hash of its own content, so the same
editorial decisions always produce the same identity and any change produces
a new one. Volatile state -- when it was generated, which machine, what was
selected in a UI -- is deliberately excluded, because a plan that changes
identity without changing the film is useless for comparing two films.

EVERY PLACEMENT EXPLAINS ITSELF. A scene carries the reason it sits where it
sits: "low transient density, long enough interval, payoff anchor at the
end". A planner that cannot say why is a planner nobody can overrule.

UNRESOLVED SPACE IS A FEATURE. Most of a prototype score should stay empty.
Filling a whole song with mediocre material to look finished is the failure
mode this field exists to make visible.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from fractions import Fraction
import hashlib
import json
from typing import Any, Sequence

from creative_suite.engine.score_timeline import (
    INTENSITIES, INTENSITY_NORMAL, ScoreSlot, ScoreTimelineV1,
    spectacle_saturation)
from creative_suite.engine.temporal_footprint import (
    RetimeSegment, TimeFootprint, TransitionFootprint, check_no_temporal_debt,
    total_edit_span_us)

PLAN_SCHEMA_VERSION = 1
PLAN_VERSION = "sequence-score-plan-v1.0.0"

# States that consume a canonical moment. SHORTLISTED does not.
CONSUMING_STATES = ("VALIDATED", "ASSIGNED", "USED")

PLAN_DURATION_MISMATCH = "PLAN_DURATION_MISMATCH"
PLAN_OVERLAP = "PLAN_OVERLAP"
PLAN_CONSUMED_MOMENT = "PLAN_CONSUMED_MOMENT"
PLAN_OUT_OF_SCORE = "PLAN_OUT_OF_SCORE"


@dataclass(frozen=True)
class PlannedScene:
    """One gameplay scene cast into an interval of the score."""
    slot_role: str
    frag_id: int
    scene_kind: str
    score_start_us: int
    score_end_us: int
    hero_event_kind: str
    hero_score_us: int
    music_anchor_us: int | None = None
    target_delta_ms: float | None = None
    retime: tuple[RetimeSegment, ...] = ()
    camera_mode: str = "FPV"
    moment_state: str = "SHORTLISTED"
    why: str = ""

    def __post_init__(self) -> None:
        if self.score_end_us <= self.score_start_us:
            raise ValueError("a scene needs positive duration")
        if not self.score_start_us <= self.hero_score_us <= self.score_end_us:
            raise ValueError("the hero event must fall inside its own scene")

    @property
    def duration_us(self) -> int:
        return self.score_end_us - self.score_start_us

    @property
    def delivered_delta_ms(self) -> float | None:
        if self.music_anchor_us is None:
            return None
        return round((self.music_anchor_us - self.hero_score_us) / 1000.0, 2)

    @property
    def consumes(self) -> bool:
        return self.moment_state in CONSUMING_STATES

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["retime"] = [r.to_dict() for r in self.retime]
        d["duration_us"] = self.duration_us
        d["delivered_delta_ms"] = self.delivered_delta_ms
        return d


@dataclass(frozen=True)
class PlannedEffect:
    """An effect with a real position on the score, not a note to self."""
    effect_type: str
    score_start_us: int
    score_peak_us: int
    score_end_us: int
    trigger_event: str
    purpose: str
    intensity: str = INTENSITY_NORMAL
    footprint: TimeFootprint | None = None
    why: str = ""

    def __post_init__(self) -> None:
        if not (self.score_start_us <= self.score_peak_us <= self.score_end_us):
            raise ValueError("effect moments must be ordered")
        if self.intensity not in INTENSITIES:
            raise ValueError(f"unknown intensity {self.intensity!r}")

    @property
    def duration_us(self) -> int:
        return self.score_end_us - self.score_start_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["footprint"] = (self.footprint.to_dict() if self.footprint else None)
        d["duration_us"] = self.duration_us
        return d


@dataclass(frozen=True)
class PlannedTransition:
    """A transition, occupying score time between two scenes."""
    footprint: TransitionFootprint
    from_scene: int | None = None
    to_scene: int | None = None
    why: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"footprint": self.footprint.to_dict(),
                "from_scene": self.from_scene, "to_scene": self.to_scene,
                "why": self.why}


@dataclass(frozen=True)
class PlannedCamera:
    """A camera segment. Cameras have timing like everything else."""
    mode: str
    score_start_us: int
    score_end_us: int
    subject: str = ""
    why: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SyncRelationship:
    """One intended hard relationship between gameplay and music."""
    label: str
    game_score_us: int
    music_score_us: int
    target_delta_ms: float
    event_class: str

    @property
    def intended_delta_ms(self) -> float:
        return round((self.music_score_us - self.game_score_us) / 1000.0, 2)

    @property
    def error_ms(self) -> float:
        return round(self.intended_delta_ms - self.target_delta_ms, 2)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["intended_delta_ms"] = self.intended_delta_ms
        d["error_ms"] = self.error_ms
        return d


@dataclass(frozen=True)
class UnresolvedSlot:
    """A slot nobody has filled, and what it is waiting for."""
    slot_role: str
    score_start_us: int
    score_end_us: int
    wants: str = ""

    @property
    def duration_us(self) -> int:
        return self.score_end_us - self.score_start_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["duration_us"] = self.duration_us
        return d


@dataclass(frozen=True)
class SequenceScorePlanV1:
    """A whole film's editorial intent, locked to one song's duration."""
    track_hash: str
    score_duration_us: int
    slots: tuple[ScoreSlot, ...] = ()
    scenes: tuple[PlannedScene, ...] = ()
    transitions: tuple[PlannedTransition, ...] = ()
    effects: tuple[PlannedEffect, ...] = ()
    cameras: tuple[PlannedCamera, ...] = ()
    sync: tuple[SyncRelationship, ...] = ()
    intensity_curve: tuple[tuple[int, str], ...] = ()
    unresolved: tuple[UnresolvedSlot, ...] = ()
    schema_version: int = PLAN_SCHEMA_VERSION
    plan_version: str = PLAN_VERSION

    # ── identity ────────────────────────────────────────────────────────────

    def canonical(self) -> dict[str, Any]:
        """Content that decides the film. No timestamps, no UI state."""
        return {
            "track_hash": self.track_hash,
            "score_duration_us": self.score_duration_us,
            "schema_version": self.schema_version,
            "plan_version": self.plan_version,
            "slots": [[s.start_us, s.end_us, s.role, s.intensity]
                      for s in self.slots],
            "scenes": [s.to_dict() for s in self.scenes],
            "transitions": [t.to_dict() for t in self.transitions],
            "effects": [e.to_dict() for e in self.effects],
            "cameras": [c.to_dict() for c in self.cameras],
            "sync": [s.to_dict() for s in self.sync],
            "intensity_curve": [list(x) for x in self.intensity_curve],
            "unresolved": [u.to_dict() for u in self.unresolved]}

    @property
    def plan_hash(self) -> str:
        payload = json.dumps(self.canonical(), sort_keys=True,
                             separators=(",", ":"), default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    # ── coverage ────────────────────────────────────────────────────────────

    @property
    def occupied_us(self) -> int:
        return sum(s.duration_us for s in self.scenes)

    @property
    def unresolved_us(self) -> int:
        return max(0, self.score_duration_us - self.occupied_us)

    @property
    def coverage(self) -> float:
        return (round(self.occupied_us / self.score_duration_us, 4)
                if self.score_duration_us else 0.0)

    @property
    def duration_timecode(self) -> str:
        s = self.score_duration_us / 1e6
        return f"{int(s // 60)}:{s % 60:06.3f}"

    # ── validation ──────────────────────────────────────────────────────────

    def check(self, *, timeline: ScoreTimelineV1 | None = None
              ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        if timeline is not None and timeline.duration_us != self.score_duration_us:
            out.append({"check": PLAN_DURATION_MISMATCH, "severity": "ERROR",
                        "detail": f"the plan is {self.score_duration_us} us but "
                                  f"the song is {timeline.duration_us} us; the "
                                  f"movie must be exactly the song's length"})
        for s in self.scenes:
            if s.score_start_us < 0 or s.score_end_us > self.score_duration_us:
                out.append({"check": PLAN_OUT_OF_SCORE, "severity": "ERROR",
                            "detail": f"scene for frag {s.frag_id} lies outside "
                                      f"the score"})
            if s.consumes:
                out.append({"check": PLAN_CONSUMED_MOMENT, "severity": "ERROR",
                            "detail": f"frag {s.frag_id} is {s.moment_state} and "
                                      f"cannot be planned again without an "
                                      f"explicit reuse override"})
        ordered = sorted(self.scenes, key=lambda s: s.score_start_us)
        for a, b in zip(ordered, ordered[1:]):
            if b.score_start_us < a.score_end_us:
                overlap = a.score_end_us - b.score_start_us
                covered = any(
                    t.footprint.start_us <= b.score_start_us
                    and t.footprint.end_us >= a.score_end_us
                    for t in self.transitions)
                if not covered:
                    out.append({
                        "check": PLAN_OVERLAP, "severity": "ERROR",
                        "detail": f"frags {a.frag_id} and {b.frag_id} overlap by "
                                  f"{overlap / 1000:.0f} ms with no transition "
                                  f"claiming that time"})
        out.extend(check_no_temporal_debt(
            [r for s in self.scenes for r in s.retime]))
        out.extend(spectacle_saturation(self.slots))
        return out

    @property
    def valid(self) -> bool:
        return not any(f["severity"] == "ERROR" for f in self.check())

    # ── explanation ─────────────────────────────────────────────────────────

    def explain(self) -> list[str]:
        """Why each placement is where it is, in words."""
        lines: list[str] = []
        for s in sorted(self.scenes, key=lambda x: x.score_start_us):
            lines.append(
                f"{s.score_start_us / 1e6:7.3f}s {s.slot_role:<9} "
                f"frag {s.frag_id} ({s.scene_kind}): {s.why}")
        for e in sorted(self.effects, key=lambda x: x.score_start_us):
            lines.append(
                f"{e.score_start_us / 1e6:7.3f}s {'EFFECT':<9} "
                f"{e.effect_type}: {e.why}")
        for t in sorted(self.transitions,
                        key=lambda x: x.footprint.start_us):
            lines.append(
                f"{t.footprint.start_us / 1e6:7.3f}s {'TRANSIT':<9} "
                f"{t.footprint.family}: {t.why}")
        return lines

    def to_dict(self) -> dict[str, Any]:
        d = self.canonical()
        d.update(plan_hash=self.plan_hash, occupied_us=self.occupied_us,
                 unresolved_us=self.unresolved_us, coverage=self.coverage,
                 duration_timecode=self.duration_timecode,
                 findings=self.check(), explain=self.explain())
        return d


def unresolved_from(slots: Sequence[ScoreSlot],
                    scenes: Sequence[PlannedScene]) -> tuple[UnresolvedSlot, ...]:
    """Slots with nothing in them. Emptiness is reported, not hidden."""
    filled = [(s.score_start_us, s.score_end_us) for s in scenes]
    out: list[UnresolvedSlot] = []
    for slot in slots:
        if any(a < slot.end_us and b > slot.start_us for a, b in filled):
            continue
        out.append(UnresolvedSlot(
            slot.role, slot.start_us, slot.end_us,
            wants=f"{slot.role.lower()} material, "
                  f"{slot.duration_us / 1e6:.1f}s, "
                  f"{slot.evidence.hard_anchor_count} hard anchors"))
    return tuple(out)
