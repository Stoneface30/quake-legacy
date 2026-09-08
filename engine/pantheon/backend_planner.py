"""WHICH BACKEND DOES WHICH PASS, AND WHY THAT ONE.

PANTHEON is not Wolfcam, or Blender, or FFmpeg. It understands the shot and
then picks whatever has PROVEN it can deliver each part of it. A plan names a
backend per pass, cites the capability that decided it, and says plainly when
no backend can do something rather than routing to one that will fail
quietly.

A pass that nothing can deliver is not dropped from the plan: it is carried as
PASS_UNSUPPORTED, because a missing pass a caller never sees is how a shot
ships without the thing it was for.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from engine.pantheon import capabilities as CAP
from engine.pantheon import effect_recipes as ER

QUAKE = "PANTHEON_QUAKE_OFFSCREEN"
WOLF = "WOLFCAM_REFERENCE"
BLENDER = "BLENDER"
COMPOSITOR = "PANTHEON_COMPOSITOR"
FFMPEG = "FFMPEG"


class PassStatus(str, Enum):
    PLANNED = "PLANNED"
    PASS_UNSUPPORTED = "PASS_UNSUPPORTED"       # nothing can deliver it
    PASS_NOT_PRODUCED = "PASS_NOT_PRODUCED"     # planned, then not made


@dataclass
class RenderPass:
    name: str                       # BEAUTY, ACTOR_MASK, ANALYSIS, FINAL
    backend: str | None
    status: PassStatus
    because: str
    capabilities: tuple[str, ...] = ()
    recipes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {"pass": self.name, "backend": self.backend,
                "status": self.status.value, "because": self.because,
                "capabilities": list(self.capabilities),
                "recipes": list(self.recipes)}


@dataclass
class BackendPlan:
    passes: list[RenderPass] = field(default_factory=list)
    profile: str = "REVIEW"

    @property
    def deliverable(self) -> bool:
        return all(p.status is PassStatus.PLANNED for p in self.passes)

    @property
    def unsupported(self) -> list[RenderPass]:
        return [p for p in self.passes if p.status is PassStatus.PASS_UNSUPPORTED]

    def as_dict(self) -> dict:
        return {"profile": self.profile, "deliverable": self.deliverable,
                "passes": [p.as_dict() for p in self.passes]}


def _first_backend_that_can(caps: tuple[str, ...],
                            candidates: tuple[str, ...]) -> str | None:
    for b in candidates:
        if all(CAP.supports(c, b) for c in caps):
            return b
    return None


def plan(*, recipes: tuple[str, ...] = (), profile: str = "REVIEW",
         beauty_backend: str = QUAKE) -> BackendPlan:
    """Turn a set of chosen recipes into passes and backends.

    The beauty pass is the picture itself and is always planned; the rest
    appear only because a recipe asked for them.
    """
    p = BackendPlan(profile=profile)

    beauty_caps = ("BEAUTY_PASS",)
    b = _first_backend_that_can(beauty_caps, (beauty_backend, WOLF))
    p.passes.append(RenderPass(
        "BEAUTY", b,
        PassStatus.PLANNED if b else PassStatus.PASS_UNSUPPORTED,
        f"{b} has BEAUTY_PASS proven" if b else
        "no backend has a proven beauty pass", beauty_caps, recipes))

    # Every capability the chosen recipes need, and where it can come from.
    for rid in recipes:
        r = ER.get(rid)
        for cap in r.required_capabilities:
            where = _first_backend_that_can((cap,), (QUAKE, WOLF, BLENDER, COMPOSITOR))
            if where in (QUAKE, WOLF) and where == b:
                continue                      # the beauty pass already carries it
            name = f"{rid}:{cap}"
            if where is None:
                p.passes.append(RenderPass(
                    name, None, PassStatus.PASS_UNSUPPORTED,
                    f"{cap} is {CAP.get(cap, QUAKE).evidence.name if cap in CAP.BACKENDS[QUAKE] else 'unknown'} "
                    f"-- no backend has proven it", (cap,), (rid,)))
            else:
                p.passes.append(RenderPass(
                    name, where, PassStatus.PLANNED,
                    f"{where} has {cap}", (cap,), (rid,)))

    p.passes.append(RenderPass(
        "FINAL", FFMPEG, PassStatus.PLANNED,
        "assembly and encode are ffmpeg's job, and always have been"))
    return p


def report(recipes: tuple[str, ...] = ()) -> dict:
    return plan(recipes=recipes).as_dict()
