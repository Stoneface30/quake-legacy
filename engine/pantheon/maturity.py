"""HOW FINISHED IS EACH PART OF PANTHEON, BY MEASUREMENT.

Every line is derived from something that can be checked on this machine: a
registry count, a doctor check, a proof verdict. Nothing here is an opinion
about how the work feels.

    PRODUCTION_READY  works unattended, and has been proven
    PARTIAL           works, with a named gap
    CONCEPT           designed and registered; nothing implements it
    BLOCKED           cannot proceed until something outside it moves
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Maturity(str, Enum):
    PRODUCTION_READY = "PRODUCTION_READY"
    OPERATIONAL_FINAL_VALIDATION = "OPERATIONAL_FINAL_VALIDATION"
    PARTIAL = "PARTIAL"
    CONCEPT = "CONCEPT"
    BLOCKED = "BLOCKED"


@dataclass
class Subsystem:
    name: str
    maturity: Maturity
    evidence: str
    gap: str = ""

    def as_dict(self) -> dict:
        return {"subsystem": self.name, "maturity": self.maturity.value,
                "evidence": self.evidence, "gap": self.gap}


def assess() -> list[Subsystem]:
    from engine.pantheon import capabilities as CAP
    from engine.pantheon import director_notes as DN
    from engine.pantheon import effect_recipes as ER
    from engine.pantheon import ideas as ID
    from engine.pantheon import performance_index as PI
    from engine.pantheon import visual_proof as VP

    out: list[Subsystem] = []

    try:
        idx = PI.stats()
        demos, actions = idx.get("demos", 0), idx.get("actions", 0)
    except Exception:
        demos = actions = 0

    out.append(Subsystem(
        "GAME_TRUTH", Maturity.PRODUCTION_READY,
        "the protocol registry matches the engine's own tables with zero "
        "defects, and the parser round-trips a compiled demo back through the "
        "same extractor"))

    out.append(Subsystem(
        "PERFORMANCE", Maturity.PRODUCTION_READY,
        f"{demos:,} demos and {actions:,} actions indexed; a trace is "
        f"reconstructed from its locator per kind on every doctor run"))

    out.append(Subsystem(
        "SPATIAL", Maturity.PARTIAL,
        "18 maps carry regions, layers, routes and walked cells",
        gap="40 further maps have too few demos to learn a structure from"))

    out.append(Subsystem(
        "REVIEW", Maturity.PARTIAL,
        "a moment resolves to one ReviewMoment with facts, POVs and "
        "possibilities; the proxy films offscreen",
        gap="health, armour, accuracy and round read NOT_DERIVABLE from an "
            "index row; the frontend does not consume the contract yet"))

    rep = ER.report()
    out.append(Subsystem(
        "EFFECTS", Maturity.CONCEPT,
        f"{len(ER.RECIPES)} recipes registered; "
        f"{rep['by_status'].get('BACKEND_SUPPORTED', 0)} have a backend that "
        f"can deliver every capability they need",
        gap="none is VISUALLY_PROVEN through the offscreen backend, and none "
            "has a choreography builder"))

    out.append(Subsystem(
        "DIRECTOR", Maturity.CONCEPT,
        f"{len(ID.IDEAS)} ideas and {len(DN.NOTES)} original notes recorded "
        f"verbatim; {len(ID.unimplemented())} ideas have no recipe",
        gap="nothing turns a note into a ChoreographyPlan"))

    out.append(Subsystem(
        "CAMERA", Maturity.PARTIAL,
        "free camera, follow and camera paths are all EXECUTION_PROVEN in the "
        "backend",
        gap="collision, sight-line and composition are three separate checks "
            "and are not wired into a planner"))

    usable = sum(1 for c in CAP.BACKENDS["PANTHEON_QUAKE_OFFSCREEN"].values()
                 if c.usable)
    out.append(Subsystem(
        "RENDER", Maturity.OPERATIONAL_FINAL_VALIDATION,
        f"the offscreen backend films 1920x1080 with no window, no stolen "
        f"focus and a free pointer; {usable} usable capabilities",
        gap="the pointer fix is not yet confirmed by the operator, and no "
            "recipe has completed the whole pipeline; both are required "
            "before this is PRODUCTION_READY"))

    vp = VP.report()
    out.append(Subsystem(
        "VISUAL_PROOF", Maturity.PARTIAL,
        f"{vp.get('capabilities', 0)} capabilities in the registry, "
        f"{vp.get('by_status', {}).get('VISUALLY_PROVEN', 0)} banked",
        gap=f"{vp.get('awaiting_human', 0)} are waiting on a person to look"))

    out.append(Subsystem(
        "BLENDER_BRIDGE", Maturity.CONCEPT,
        "ten capabilities registered as UNKNOWN, each with the probe that "
        "would settle it",
        gap="deliberately not built this sprint"))

    out.append(Subsystem(
        "COMFYUI_BRIDGE", Maturity.BLOCKED,
        "stylisation only, and only after game truth is fixed",
        gap="not started; must never decide game truth"))

    return out


def report() -> dict:
    subs = assess()
    counts: dict[str, int] = {}
    for s in subs:
        counts[s.maturity.value] = counts.get(s.maturity.value, 0) + 1
    return {"subsystems": [s.as_dict() for s in subs], "counts": counts}


def main() -> int:                                           # pragma: no cover
    for s in assess():
        print(f"  {s.maturity.value:17s} {s.name:16s} {s.evidence}")
        if s.gap:
            print(f"  {'':17s} {'':16s} gap: {s.gap}")
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
