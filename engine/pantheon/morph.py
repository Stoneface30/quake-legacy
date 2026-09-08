"""ONE MOMENT, FILMED SEVERAL TIMES, WITH THE ART AS THE ONLY VARIABLE.

A shader wave animates on the engine clock and cannot be told to peak on a
rocket impact. A texture cannot dissolve into another texture inside a Quake
frame. So the cueable axis is not inside one render -- it is BETWEEN renders.

Film the same instant of the same demo N times, changing nothing but which
look is installed, and you have N frame-for-frame alternate universes of one
moment. Cut between them on a beat and the world changes identity on the
downbeat. Dissolve and it becomes a morph. That is an effect nobody can
download, because it needs a demo, a deterministic seek, and eleven finished
render families over the same 5,776 paths -- which is exactly what this
project has and a texture pack is not.

THE THING THAT MAKES THIS HARD, STATED BEFORE ANY PROMISE. Two runs of the
engine do not start on the same tick. This project measured that directly:
comparing frames between two captures of the SAME configuration showed roughly
a quarter of pixels differing, and the difference was camera phase, not
content. A cut can survive that. A DISSOLVE CANNOT -- cross-fading two takes
that are a few milliseconds apart shows a ghost of the world sliding against
itself.

So every plan here carries an explicit alignment requirement, and
`alignment_proven` is False everywhere until a human has looked at a dissolve
and said it holds. Nothing in this module reports otherwise.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

# ── how takes are joined ───────────────────────────────────────────────────

CUT = "CUT"
DISSOLVE = "DISSOLVE"
MORPH = "MORPH"

#: What each join needs from the takes underneath it, and what it costs if the
#: takes are not aligned. The ladder is deliberate: a cut is safe today, a
#: dissolve is the thing to prove next, a morph is the thing to prove after.
JOIN_REQUIREMENTS: dict[str, dict] = {
    CUT: {
        "needs": "takes of the same moment, each individually correct",
        "tolerates_phase_error": True,
        "why": "a single frame is replaced by a single frame; a few "
               "milliseconds of camera phase reads as an edit, not an error",
        "ready": True,
    },
    DISSOLVE: {
        "needs": "frame-aligned takes: the same world instant on both sides "
                 "of every blended frame",
        "tolerates_phase_error": False,
        "why": "blending two instants that are milliseconds apart shows the "
               "world ghosting against itself",
        "ready": False,
    },
    MORPH: {
        "needs": "frame-aligned takes AND correspondence between them",
        "tolerates_phase_error": False,
        "why": "a morph warps one image toward another; without alignment it "
               "warps toward the wrong instant, and the geometry is identical "
               "anyway, so optical flow has nothing to track but the art",
        "ready": False,
    },
}

#: The alignment step every non-cut join depends on. Named so a plan can point
#: at it instead of implying it happened.
ALIGNMENT = (
    "Align the takes on a world event both of them contain -- the same "
    "recorded event tick, not a wall-clock offset -- then trim both to a "
    "common frame grid before any blend.")


@dataclass(frozen=True)
class Take:
    """One capture of the moment. The look is the only thing that varies."""
    look: str                     # an asset set name, e.g. STOCK or NEON
    hud: str = "HUD_STOCK"        # a HUD effect name
    label: str = ""

    def as_dict(self) -> dict:
        return {"look": self.look, "hud": self.hud,
                "label": self.label or self.look}


@dataclass(frozen=True)
class MorphPlan:
    """N takes of one moment and how to join them. A plan, never a render."""
    name: str
    intent: str
    takes: tuple[Take, ...]
    join: str = CUT
    join_ms: int = 0              # 0 for a cut; the blend length otherwise
    note: str = ""

    def __post_init__(self) -> None:
        if self.join not in JOIN_REQUIREMENTS:
            raise ValueError(f"unknown join: {self.join}")
        if len(self.takes) < 2:
            raise ValueError("a morph plan needs at least two takes; "
                             "one take is just a render")
        if self.join == CUT and self.join_ms:
            raise ValueError("a cut has no duration")
        if self.join != CUT and self.join_ms <= 0:
            raise ValueError(f"a {self.join} needs a duration in ms")

    @property
    def requirement(self) -> dict:
        return JOIN_REQUIREMENTS[self.join]

    @property
    def alignment_required(self) -> bool:
        return not self.requirement["tolerates_phase_error"]

    @property
    def alignment_proven(self) -> bool:
        """Always False. It becomes a question for `visual_proof` the moment
        somebody films a dissolve and looks at it -- and this module must not
        answer a question it did not ask."""
        return False

    @property
    def ready(self) -> bool:
        """Whether this plan can be shot today with what has been proven."""
        return bool(self.requirement["ready"])

    @property
    def blockers(self) -> tuple[str, ...]:
        if self.ready:
            return ()
        return (f"{self.join} needs {self.requirement['needs']}", ALIGNMENT)

    def as_dict(self) -> dict:
        return {
            "name": self.name, "intent": self.intent, "join": self.join,
            "join_ms": self.join_ms,
            "takes": [t.as_dict() for t in self.takes],
            "captures_required": len(self.takes),
            "alignment_required": self.alignment_required,
            "alignment_proven": self.alignment_proven,
            "ready": self.ready, "blockers": list(self.blockers),
            "note": self.note,
        }


# ── the vocabulary ─────────────────────────────────────────────────────────

RECIPES: dict[str, MorphPlan] = {}


def _add(p: MorphPlan) -> MorphPlan:
    RECIPES[p.name] = p
    return p


_add(MorphPlan(
    "WORLD_FLIP",
    "The world changes identity on the downbeat: stock Quake becomes neon, "
    "hard, on the beat.",
    (Take("STOCK", label="the game as it was"),
     Take("NEON", label="the game as we see it")),
    join=CUT,
    note="The safe one. A cut survives the phase difference between two "
         "engine runs, so this is shootable with what is already proven."))

_add(MorphPlan(
    "ERA_LADDER",
    "The same frag walks forward through four treatments, one cut per bar.",
    (Take("STOCK", label="1999"), Take("UHD", label="remastered"),
     Take("PAINTERLY", label="painted"), Take("NEON", label="ours")),
    join=CUT,
    note="Four captures of one moment. Cut on the bar and the history of the "
         "game plays out inside a single frag."))

_add(MorphPlan(
    "HUD_REVEAL",
    "The HUD arrives: a clean plate becomes the played game.",
    (Take("UHD", hud="HUD_CLEAN", label="clean plate"),
     Take("UHD", hud="HUD_STOCK", label="the game as played")),
    join=CUT,
    note="The look is fixed and the HUD is the variable, which is the same "
         "trick pointed at the other surface."))

_add(MorphPlan(
    "MEDAL_ISOLATE",
    "Only the medal survives the cut, floating over otherwise clean play.",
    (Take("UHD", hud="HUD_CLEAN", label="no HUD"),
     Take("UHD", hud="HUD_MEDALS_ONLY", label="the medal alone")),
    join=CUT,
    note="Two takes composited rather than cut, if the compositor prefers -- "
         "the plan says which frames exist, not what the editor does."))

_add(MorphPlan(
    "DREAM_BLEED",
    "The world softens into a dream and comes back.",
    (Take("UHD", label="real"), Take("DREAMLIKE", label="dream"),
     Take("UHD", label="real again")),
    join=DISSOLVE, join_ms=400,
    note="NOT SHOOTABLE YET. This is the first plan that needs the takes "
         "frame-aligned, and alignment is unproven."))

_add(MorphPlan(
    "MATERIAL_MORPH",
    "The surfaces themselves transmute -- stone into chrome -- while the "
    "action continues underneath.",
    (Take("UHD", label="stone"), Take("EDGE_CHROME", label="chrome")),
    join=MORPH, join_ms=700,
    note="The headline effect and the furthest from proven. The geometry is "
         "identical in both takes by construction, so a flow-based morph has "
         "nothing to track except the art -- which is either the reason this "
         "works beautifully or the reason it does nothing. One test answers "
         "it."))


def ready_now() -> tuple[str, ...]:
    """Plans that can be shot with what has already been proven."""
    return tuple(sorted(n for n, p in RECIPES.items() if p.ready))


def blocked() -> dict[str, tuple[str, ...]]:
    """Plans that cannot, and exactly what each is waiting on."""
    return {n: p.blockers for n, p in sorted(RECIPES.items()) if not p.ready}


def captures_for(plan_name: str) -> tuple[dict, ...]:
    """The capture list a plan implies: one entry per take, in order.

    This is the whole interface to the render side. It says WHAT to film and
    with which art; it does not film, choose a backend, or name one.
    """
    if plan_name not in RECIPES:
        raise KeyError(f"no such morph plan: {plan_name}; "
                       f"known: {sorted(RECIPES)}")
    plan = RECIPES[plan_name]
    return tuple({"index": i, "look": t.look, "hud": t.hud,
                  "label": t.label or t.look}
                 for i, t in enumerate(plan.takes))


def validate(plan_name: str, known_looks: Sequence[str],
             known_hud_effects: Sequence[str]) -> dict:
    """Check a plan against what actually exists, and say what is missing.

    The caller supplies the vocabularies rather than this module importing
    them, so a plan can be checked against a staging area that has only some
    of the looks built.
    """
    plan = RECIPES[plan_name]
    looks, huds = set(known_looks), set(known_hud_effects)
    missing_looks = sorted({t.look for t in plan.takes} - looks)
    missing_huds = sorted({t.hud for t in plan.takes} - huds)
    return {
        "plan": plan_name,
        "ok": not missing_looks and not missing_huds and plan.ready,
        "missing_looks": missing_looks,
        "missing_hud_effects": missing_huds,
        "ready": plan.ready,
        "blockers": list(plan.blockers),
    }


def report() -> dict:
    """The morph vocabulary and its honest state."""
    return {
        "plans": {n: p.as_dict() for n, p in sorted(RECIPES.items())},
        "ready_now": list(ready_now()),
        "blocked": {k: list(v) for k, v in blocked().items()},
        "joins": JOIN_REQUIREMENTS,
        "alignment": ALIGNMENT,
        "why_alignment_matters":
            "Two runs of the engine do not start on the same tick. This was "
            "measured on this project: frames from two captures of the same "
            "configuration differed in about a quarter of their pixels, and "
            "the difference was camera phase, not content. A cut survives "
            "that; a blend does not.",
    }
