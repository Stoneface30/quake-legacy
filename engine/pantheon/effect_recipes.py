"""THE FILM GRAMMAR, AS SEMANTICS -- NEVER AS BACKEND CODE.

A recipe says what a treatment IS, what truth it needs, when it is worth
using, and what a backend would have to be able to do. It contains no cvar,
no command, no camera maths. The backend planner reads the requirements; the
capability registry says whether anything can meet them; the visual proof
registry says whether a person has ever seen it work.

WHY THIS IS A REGISTRY AND NOT A PILE OF ONE-OFFS. Every effect built so far
arrived as a script with its own cvars, and the vocabulary lived in chat.
Registering the grammar means a moment can be asked "what could we do with
you" without anything being rendered, and an idea can be honestly labelled
CONCEPT instead of quietly implemented twice.

    CONCEPT                 named and understood; nothing implements it
    SEMANTICALLY_SUPPORTED  the truth it needs exists in the engine
    BACKEND_SUPPORTED       a backend can also deliver the picture
    VISUALLY_PROVEN         a person has seen it work
    PRODUCTION_READY        proven, and the pipeline can run it unattended

A recipe is never PRODUCTION_READY because someone wrote the word. The status
is derived from the registries, every time it is asked.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    CONCEPT = "CONCEPT"
    SEMANTICALLY_SUPPORTED = "SEMANTICALLY_SUPPORTED"
    BACKEND_SUPPORTED = "BACKEND_SUPPORTED"
    VISUALLY_PROVEN = "VISUALLY_PROVEN"
    PRODUCTION_READY = "PRODUCTION_READY"


ORDER = [Status.CONCEPT, Status.SEMANTICALLY_SUPPORTED, Status.BACKEND_SUPPORTED,
         Status.VISUALLY_PROVEN, Status.PRODUCTION_READY]


# What a recipe can ask the engine for. These are TRUTH names, checked against
# a moment's evidence -- not fields, not tables.
TRUTH = {
    "ACTION",            # an ActionGraph reading of what happened
    "TRANSFORM",         # where a body was, sample by sample
    "AIM",               # where it was looking
    "PROJECTILE_PATH",   # observed missile samples
    "EVENTS",            # the recorded EV_* chain
    "OTHER_POV",         # another client observed at the same serverTime
    "ENEMY_POV",         # specifically the other side of the kill
    "MAP_GEOGRAPHY",     # regions, layers, routes for this map
    "ROUND",             # the round this moment sits in
    "HEALTH",            # health/armour over the window
    "WEAPON_STATE",      # what was held and switched
    "SCOREBOARD",        # the match state
    "ROSTER",            # who performs, as characters not names
}


@dataclass(frozen=True)
class EffectRecipe:
    id: str
    description: str                       # one line, in film words
    required_truth: tuple[str, ...]
    useful_when: str                       # when a director would reach for it
    required_capabilities: tuple[str, ...] = ()
    optional_capabilities: tuple[str, ...] = ()
    preferred_backends: tuple[str, ...] = ()
    choreography_builder: str | None = None   # dotted name, when one exists
    visual_proof: str | None = None           # capability in the proof registry
    note: str = ""

    def truth_gap(self, available: set[str]) -> tuple[str, ...]:
        return tuple(t for t in self.required_truth if t not in available)


R = EffectRecipe
QUAKE = "PANTHEON_QUAKE_OFFSCREEN"
WOLF = "WOLFCAM_REFERENCE"
BLENDER = "BLENDER"
COMPOSITOR = "PANTHEON_COMPOSITOR"

RECIPES: tuple[EffectRecipe, ...] = (
    R("XRAY_ACTOR",
      "The enemy reads through the walls as a coloured silhouette, so the "
      "viewer sees the shot the player could not.",
      ("TRANSFORM", "OTHER_POV"),
      "A kill through geometry, or a fight the viewer cannot follow because "
      "the bodies are hidden.",
      required_capabilities=("XRAY_PLAYER",),
      preferred_backends=(QUAKE, WOLF), visual_proof="XRAY_PLAYER"),

    R("WALL_REMOVE_XRAY",
      "The wall itself is taken away rather than drawn through, revealing the "
      "room as a diagram.",
      ("TRANSFORM", "MAP_GEOGRAPHY"),
      "Explaining a position to someone who does not know the map.",
      required_capabilities=("WALL_REMOVAL",),
      preferred_backends=(BLENDER,),
      note="No proven route in the Quake backend: substituting a material is "
           "not the same as deleting geometry. See the WALL_REMOVAL "
           "capability for what would have to exist."),

    R("FREEZE_AND_EXPLAIN",
      "The action stops on the decisive frame and the picture is annotated "
      "while nothing moves.",
      ("ACTION", "TRANSFORM", "EVENTS"),
      "A moment whose skill is invisible at speed.",
      required_capabilities=("FREEZE_ENTITY", "TIME_SCALE"),
      optional_capabilities=("ANALYSIS_OVERLAY",),
      preferred_backends=(QUAKE, COMPOSITOR),
      note="The Quake backend can hold ONE body, not the scene; a whole-scene "
           "hold is a time change or a held frame in the compositor. See "
           "FREEZE_ENTITY and HELD_FRAME."),

    R("FREEZE_KILLER",
      "Everything holds except the killer, who keeps moving.",
      ("ACTION", "TRANSFORM"),
      "Isolating one player's movement from a crowded round.",
      required_capabilities=("FREEZE_ENTITY",),
      preferred_backends=(QUAKE,)),

    R("PROJECTILE_FOLLOW",
      "The camera rides the rocket from the muzzle to the body.",
      ("PROJECTILE_PATH", "TRANSFORM"),
      "A long-range or airborne projectile kill.",
      required_capabilities=("CHASE_ENTITY", "CAMERA_FREE"),
      preferred_backends=(QUAKE, WOLF),
      note="The path must be OBSERVED, not extended by physics: a derived "
           "path filmed as if recorded is a lie about the demo."),

    R("PROJECTILE_FLYTHROUGH",
      "The camera flies the projectile's line through the room and past the "
      "impact, without stopping.",
      ("PROJECTILE_PATH", "MAP_GEOGRAPHY"),
      "Showing the geometry a shot threaded.",
      required_capabilities=("CAMERA_PATH", "CAMERA_FREE"),
      preferred_backends=(QUAKE,)),

    R("ENEMY_POV_REPLAY",
      "The same second again, from the eyes of the player who died.",
      ("ENEMY_POV", "ACTION"),
      "A kill whose meaning is what the victim saw coming, or did not.",
      required_capabilities=("CAMERA_FOLLOW",),
      preferred_backends=(QUAKE, WOLF),
      note="Only where the demo actually observed that client at that time. "
           "An unobserved POV stays unobserved."),

    R("PIP_ALT_POV",
      "A second angle sits inside the frame while the main shot plays.",
      ("OTHER_POV",),
      "Two things worth watching at once.",
      required_capabilities=("CAMERA_FOLLOW",),
      optional_capabilities=("PICTURE_IN_PICTURE",),
      preferred_backends=(QUAKE, COMPOSITOR)),

    R("HIGH_SPEED_RETIME",
      "Time compresses into the approach and stretches over the hit.",
      ("ACTION", "EVENTS"),
      "A frag with dead air before it and one decisive instant.",
      required_capabilities=("TIME_SCALE",),
      preferred_backends=(QUAKE, COMPOSITOR),
      note="The project rule is that the VIDEO bends to the music, never the "
           "music to the video."),

    R("REPLAY_STUTTER",
      "The decisive frames repeat in a short stutter, locked to the beat.",
      ("EVENTS",),
      "A beat landing exactly on an impact.",
      preferred_backends=(COMPOSITOR,)),

    R("MULTI_FRAG_ROUND",
      "The round plays as one continuous piece, each kill given its weight.",
      ("ROUND", "ACTION", "EVENTS"),
      "A round with more than one kill by the same player.",
      preferred_backends=(QUAKE,)),

    R("TACTICAL_ROUND_STORY",
      "The round is told as a story of positions: who went where, who met "
      "whom, and why it ended.",
      ("ROUND", "MAP_GEOGRAPHY", "TRANSFORM", "OTHER_POV"),
      "A round whose interest is the shape of the fight, not one shot.",
      optional_capabilities=("ANALYSIS_OVERLAY", "MAP_DIAGRAM"),
      preferred_backends=(COMPOSITOR, QUAKE)),

    R("GRENADE_SEQUENCE",
      "The grenade's bounces are followed to the explosion.",
      ("PROJECTILE_PATH", "EVENTS"),
      "A grenade kill, where the throw is the skill.",
      required_capabilities=("CHASE_ENTITY",),
      preferred_backends=(QUAKE,)),

    R("LOW_HP_REACTION",
      "The picture carries how close the player was to dying.",
      ("HEALTH", "ACTION"),
      "A frag won from almost nothing.",
      optional_capabilities=("ANALYSIS_OVERLAY",),
      preferred_backends=(COMPOSITOR,)),

    R("MAP_WIREFRAME_REVEAL",
      "The room resolves from a wireframe into the real map.",
      ("MAP_GEOGRAPHY",),
      "Opening a section, or introducing a map.",
      required_capabilities=("SHADER_REMAP",),
      preferred_backends=(QUAKE,),
      note="Materials can be substituted; whether a usable wireframe material "
           "exists in the QL asset set at all is unproven. See SHADER_REMAP."),

    R("WORLD_HIDE_REVEAL",
      "The world drops away, leaving the players, then returns.",
      ("TRANSFORM",),
      "Turning a fight into a diagram for a moment.",
      required_capabilities=("SHADER_REMAP",),
      optional_capabilities=("WALL_REMOVAL",),
      preferred_backends=(QUAKE, BLENDER)),

    R("MODEL_MORPH",
      "A character becomes another character on screen.",
      ("ROSTER",),
      "A title card, or a joke the series has earned.",
      required_capabilities=("CUSTOM_GEOMETRY",),
      preferred_backends=(BLENDER,)),

    R("DIEGETIC_PRESENTER",
      "A character in the world presents the moment, standing in the map.",
      ("ROSTER", "MAP_GEOGRAPHY"),
      "Chaptering, or explaining across several frags.",
      required_capabilities=("SYNTHETIC_PERFORMANCE",),
      optional_capabilities=("CUSTOM_POINTING", "VOICE"),
      preferred_backends=(QUAKE, BLENDER),
      visual_proof="SYNTHETIC_KEEL_MODEL"),

    R("ANALYSIS_ACTOR_WALKOUT",
      "The presenter walks the route the player took, at walking pace.",
      ("MAP_GEOGRAPHY", "TRANSFORM", "ROSTER"),
      "Explaining a rotation or a route.",
      required_capabilities=("SYNTHETIC_PERFORMANCE",),
      preferred_backends=(QUAKE,),
      visual_proof="TORSO_GESTURE"),

    R("DIEGETIC_SCOREBOARD",
      "The score appears as part of the world rather than as an overlay.",
      ("SCOREBOARD", "ROUND"),
      "Chapter ends, or a round that turned the match.",
      required_capabilities=("CUSTOM_GEOMETRY",),
      preferred_backends=(BLENDER, COMPOSITOR)),
)

BY_ID = {r.id: r for r in RECIPES}


def get(recipe_id: str) -> EffectRecipe:
    try:
        return BY_ID[recipe_id]
    except KeyError:
        raise KeyError(f"no such recipe: {recipe_id}") from None


def status(recipe_id: str, *, backend: str | None = None,
           profile: str | None = None, engine_version: str | None = None) -> Status:
    """Derived, never declared.

    SEMANTICALLY_SUPPORTED as soon as the truth it needs is something this
    engine produces; BACKEND_SUPPORTED when every required capability is
    usable; VISUALLY_PROVEN when a person has seen it. PRODUCTION_READY is
    deliberately not reachable from a registry alone -- it needs a run
    through the pipeline, and nothing claims it yet.
    """
    from engine.pantheon import capabilities as CAP
    from engine.pantheon import visual_proof as VP

    r = get(recipe_id)
    if any(t not in TRUTH for t in r.required_truth):
        return Status.CONCEPT
    if r.required_capabilities and not all(CAP.supports(c) for c in r.required_capabilities):
        return Status.SEMANTICALLY_SUPPORTED
    if r.visual_proof and VP.proven(r.visual_proof, backend=backend,
                                    profile=profile,
                                    engine_version=engine_version):
        return Status.VISUALLY_PROVEN
    return Status.BACKEND_SUPPORTED


def missing_capabilities(recipe_id: str) -> tuple[str, ...]:
    from engine.pantheon import capabilities as CAP
    return tuple(c for c in get(recipe_id).required_capabilities
                 if not CAP.supports(c))


def report(**inputs) -> dict:
    out: dict = {"recipes": len(RECIPES), "by_status": {}, "detail": []}
    for r in RECIPES:
        st = status(r.id, **inputs)
        out["by_status"][st.value] = out["by_status"].get(st.value, 0) + 1
        out["detail"].append({"id": r.id, "status": st.value,
                              "missing_capabilities": list(missing_capabilities(r.id)),
                              "backends": list(r.preferred_backends)})
    return out


def main() -> int:                                           # pragma: no cover
    import json
    print(json.dumps(report(), indent=1))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
