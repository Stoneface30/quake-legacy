"""Three questions about an effect, and none of them answers the others.

    DELIVERY_VERIFIED     Does the operator produce the milliseconds it was
                          asked for? A machine question, settled by a canary.

    VISUALLY_APPROVED     Does this duration look good on real Quake footage?
                          A human question, and it cannot be answered on
                          synthetic counters -- there is no frag, no target,
                          no camera, no tension to judge against.

    SEMANTICALLY_APPROVED Does the complete effect grammar work where it is
                          meant to be used? A human question about a whole
                          construction, not a parameter.

The freeze sweep proved the pipeline holds a frame for exactly as long as it
is told, including a systematic one-frame overshoot that is now compensated.
It proved nothing about whether 300 ms is the right hold before a rocket
lands. So a primitive can be fully DELIVERY_VERIFIED and carry no visual
approval at all, and this module refuses to let one become the other.

Approval is granted to a PRIMITIVE at a duration range, on named footage.
Approving the freeze envelope says nothing about whether the danger-cross gag
is a good idea; that is a separate, semantic judgement.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Iterable, Sequence

APPROVAL_VERSION = "effect-approval-v1.0.0"
MS = 1000

DELIVERY_VERIFIED = "DELIVERY_VERIFIED"
VISUALLY_APPROVED = "VISUALLY_APPROVED"
SEMANTICALLY_APPROVED = "SEMANTICALLY_APPROVED"
LEVELS = (DELIVERY_VERIFIED, VISUALLY_APPROVED, SEMANTICALLY_APPROVED)

SYNTHETIC_FOOTAGE = "SYNTHETIC"     # generated counters: never enough for the eye
REAL_GAMEPLAY = "REAL_GAMEPLAY"
FOOTAGE_KINDS = (SYNTHETIC_FOOTAGE, REAL_GAMEPLAY)


class ApprovalRefused(ValueError):
    """Raised when an approval is claimed without the evidence it requires."""


@dataclass(frozen=True)
class DeliveryEvidence:
    """A canary that showed the pipeline obeys."""
    canary: str                        # which script produced it
    calibration_key: str               # fps / encoder / timebase / pipeline
    swept_points_us: tuple[int, ...]
    max_error_us: int
    finding: str = ""

    def __post_init__(self) -> None:
        if not self.swept_points_us:
            raise ApprovalRefused("delivery evidence needs the durations swept")
        if not self.calibration_key:
            raise ApprovalRefused(
                "delivery evidence belongs to a render configuration; without "
                "the key it cannot be reused safely")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualVerdict:
    """What a person said after watching, on footage that could show it."""
    reviewer: str
    footage: str                       # the clip that was judged
    footage_kind: str
    preferred_min_us: int
    preferred_max_us: int
    hard_min_us: int | None = None
    hard_max_us: int | None = None
    notes: str = ""
    reviewed_on: str = ""

    def __post_init__(self) -> None:
        if self.footage_kind not in FOOTAGE_KINDS:
            raise ApprovalRefused(f"unknown footage kind {self.footage_kind!r}")
        if self.footage_kind != REAL_GAMEPLAY:
            raise ApprovalRefused(
                f"{self.footage} is {self.footage_kind} footage. A generated "
                f"counter has no frag, no target, no camera and no tension, so "
                f"it cannot answer whether a duration looks good. Visual "
                f"approval needs real gameplay.")
        if not self.reviewer:
            raise ApprovalRefused("a verdict needs whose verdict it is")
        if self.preferred_min_us > self.preferred_max_us:
            raise ApprovalRefused("preferred range is inverted")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticVerdict:
    """A judgement about a whole effect grammar, in its intended context."""
    reviewer: str
    effect: str
    context: str                       # what it was judged inside
    accepted: bool
    notes: str = ""
    reviewed_on: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Approval:
    """Everything known about one primitive's standing, on three axes."""
    subject: str
    delivery: DeliveryEvidence | None = None
    visual: VisualVerdict | None = None
    semantic: SemanticVerdict | None = None

    @property
    def delivery_verified(self) -> bool:
        return self.delivery is not None

    @property
    def visually_approved(self) -> bool:
        return self.visual is not None

    @property
    def semantically_approved(self) -> bool:
        return self.semantic is not None and self.semantic.accepted

    @property
    def levels(self) -> tuple[str, ...]:
        out = []
        if self.delivery_verified:
            out.append(DELIVERY_VERIFIED)
        if self.visually_approved:
            out.append(VISUALLY_APPROVED)
        if self.semantically_approved:
            out.append(SEMANTICALLY_APPROVED)
        return tuple(out)

    @property
    def state(self) -> str:
        """The highest level reached, or what is missing."""
        if self.semantically_approved:
            return SEMANTICALLY_APPROVED
        if self.visually_approved:
            return VISUALLY_APPROVED
        if self.delivery_verified:
            return DELIVERY_VERIFIED
        return "UNVERIFIED"

    def blocking(self) -> str:
        """What has not been answered yet, in words."""
        if not self.delivery_verified:
            return "no canary has shown the pipeline delivers this duration"
        if not self.visually_approved:
            return ("the pipeline obeys, but nobody has judged this on real "
                    "gameplay; the sweep used synthetic footage")
        if not self.semantically_approved:
            return ("the duration is approved, but the complete effect grammar "
                    "has not been judged in its intended context")
        return ""

    def to_dict(self) -> dict[str, Any]:
        return {"subject": self.subject, "state": self.state,
                "levels": list(self.levels),
                "delivery_verified": self.delivery_verified,
                "visually_approved": self.visually_approved,
                "semantically_approved": self.semantically_approved,
                "blocking": self.blocking(),
                "delivery": self.delivery.to_dict() if self.delivery else None,
                "visual": self.visual.to_dict() if self.visual else None,
                "semantic": self.semantic.to_dict() if self.semantic else None,
                "version": APPROVAL_VERSION}


# ── the register ────────────────────────────────────────────────────────────
# Delivery evidence from the synthetic canaries of 2026-09-03. No visual or
# semantic verdicts exist: the sweeps used generated counters, which cannot
# answer what looks good.

_CAL = "60fps/libx264/AVTB/scratchpad/effect_canaries.py"
# The cut proof ran on media the active capture path produced, at 60 fps.
# Same rate as the sweeps but a different graph, so it stays its own string.
_CAL_CUT = "60fps/libx264/AVTB/concat/engine/canaries/cut_identity.py"


def _d(canary, swept, err, finding, cal=None):
    """Delivery evidence. `cal` overrides the default pipeline, because a
    measurement belongs to the pipeline that produced it -- the cut proof ran
    at the footage's native rate, not at the 60 fps the sweeps used."""
    return DeliveryEvidence(canary, cal or _CAL, tuple(v * MS for v in swept),
                            err, finding)


APPROVALS: dict[str, Approval] = {a.subject: a for a in (
    Approval("FREEZE", _d("effect_canaries.py",
                          (50, 100, 133, 150, 200, 250, 300, 400, 500, 650, 900),
                          17_000,
                          "exact to the frame, and always one frame long; the "
                          "request is compensated")),
    Approval("RETIME", _d("effect_canaries.py", (200, 250, 300, 400, 500, 550, 700, 1000),
                          19_000,
                          "3/10, 2/5 and 1/1 land exactly; 1/4, 1/2, 55/100 and "
                          "7/10 lose one frame")),
    Approval("FRAME_REPEAT", _d("effect_canaries.py", (33, 45, 60, 90, 110, 120), 2_000,
                                "a 33 ms hold survives; two frames is the floor")),
    Approval("STUTTER", _d("effect_canaries.py", (110, 230, 170, 60, 90, 45, 120), 6_700,
                           "unequal figures survive; nothing is forced onto an "
                           "even grid")),
    Approval("REVERSE", _d("effect_canaries2.py", (150, 300, 450, 600, 900, 1200), 0,
                           "reverse plus forward replay costs exactly twice the "
                           "slice")),
    Approval("REPLAY", _d("effect_canaries.py", (200, 250, 300, 400, 500, 550, 700, 1000),
                          19_000, "shares the retime primitive")),
    Approval("SEQUENTIAL_INSERT", _d("effect_canaries2.py", (600, 900, 1200, 1800, 2400), 0,
                                     "adds exactly its own duration")),
    Approval("SIMULTANEOUS_OVERLAY", _d("effect_canaries2.py",
                                        (600, 900, 1200, 1800, 2400), 0,
                                        "adds exactly nothing")),
    Approval("OVERLAP", _d("effect_canaries.py", (50, 100, 150, 200, 250, 300, 400, 500),
                           0, "removes exactly the time requested")),
    Approval("MORPH"),
    # The cut is proven by frame identity, not by duration. The spline still
    # needs its whole motion envelope.
    Approval("CAMERA_CUT", _d("cut_identity.py", (30, 54), 0,
                              "all four boundary frames carry the identity "
                              "the edit asked for",
                              cal=_CAL_CUT)),
    Approval("CAMERA_SPLINE_HANDOFF"),
    Approval("MATERIAL_TRANSFORM"),
    Approval("WORLD_TRANSFORM"),
    Approval("INFORMATION_REVEAL"),
    Approval("SYNTHETIC_ANIMATION_INSERT"),
)}


def approval_for(subject: str) -> Approval:
    return APPROVALS.get(subject, Approval(subject))


def record_visual_verdict(subject: str, verdict: VisualVerdict) -> Approval:
    """Store a director's verdict. Refused unless the primitive already
    delivers what it is asked for -- approving the look of a duration the
    pipeline cannot produce would approve nothing."""
    current = approval_for(subject)
    if not current.delivery_verified:
        raise ApprovalRefused(
            f"{subject} has no delivery evidence yet; approving how it looks "
            f"before knowing the pipeline can produce it approves nothing")
    from dataclasses import replace as _replace
    updated = _replace(current, visual=verdict)
    APPROVALS[subject] = updated
    return updated


def record_semantic_verdict(effect: str, verdict: SemanticVerdict) -> Approval:
    """A judgement about a whole grammar. Independent of any primitive's
    visual approval: approving the freeze envelope does not approve the gag
    that uses it."""
    current = approval_for(effect)
    from dataclasses import replace as _replace
    updated = _replace(current, semantic=verdict)
    APPROVALS[effect] = updated
    return updated


def status() -> dict[str, Any]:
    """Where every primitive stands on all three axes."""
    rows = [approval_for(s) for s in APPROVALS]
    return {
        "subjects": len(rows),
        "delivery_verified": sorted(a.subject for a in rows if a.delivery_verified),
        "visually_approved": sorted(a.subject for a in rows if a.visually_approved),
        "semantically_approved": sorted(a.subject for a in rows
                                        if a.semantically_approved),
        "unverified": sorted(a.subject for a in rows if not a.delivery_verified),
        "awaiting_the_eye": sorted(a.subject for a in rows
                                   if a.delivery_verified and not a.visually_approved),
        "version": APPROVAL_VERSION,
    }
