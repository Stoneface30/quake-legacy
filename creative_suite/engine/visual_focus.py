"""What the viewer must be able to understand, and for how long.

WHY THIS EXISTS. A mosaic during a lightning-gun duel is not forbidden
because it is semantically false. It is forbidden because it hides the thing
the viewer is supposed to appreciate. That is a different kind of constraint
from "this effect claims something untrue", and it needs its own name.

WHY IT IS SCOPED IN TIME. A scene has phases. A one-versus-three can strip
the map and reveal three enemies, then go completely clean while the player
actually tracks somebody, then explode again on the kill. A veto that covers
the whole moment would forbid the reveal because tracking happens later,
which is exactly the wrong answer. So a constraint owns an interval, not a
moment.

    Ask not only "is this effect true?"
    Ask "is this effect true HERE, during THESE milliseconds?"
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable, Sequence

FOCUS_VERSION = "visual-focus-v1.0.0"
MS = 1000

# ── what the viewer is meant to follow ──────────────────────────────────────

SKILL_TRACKING = "SKILL_TRACKING"
PROJECTILE_TRAJECTORY = "PROJECTILE_TRAJECTORY"
DODGE_CLEARANCE = "DODGE_CLEARANCE"
TEAM_THREAT = "TEAM_THREAT"
DAMAGE_STORY_FOCUS = "DAMAGE_STORY"
MOVEMENT_TECH = "MOVEMENT_TECH"
ROUND_INFORMATION = "ROUND_INFORMATION"
CINEMATIC_REVEAL = "CINEMATIC_REVEAL"
SUBJECTS = (SKILL_TRACKING, PROJECTILE_TRAJECTORY, DODGE_CLEARANCE, TEAM_THREAT,
            DAMAGE_STORY_FOCUS, MOVEMENT_TECH, ROUND_INFORMATION, CINEMATIC_REVEAL)

HIGH, MEDIUM, LOW, NONE = "HIGH", "MEDIUM", "LOW", "NONE"
LEVELS = (NONE, LOW, MEDIUM, HIGH)
_ORDER = {v: i for i, v in enumerate(LEVELS)}

FORBID, DISCOURAGE, ALLOW = "FORBID", "DISCOURAGE", "ALLOW"
STRENGTHS = (FORBID, DISCOURAGE, ALLOW)


@dataclass(frozen=True)
class ScopedConstraint:
    """A rule that owns an interval, not a scene."""
    start_us: int
    end_us: int
    templates: tuple[str, ...]
    strength: str
    reason: str
    lane: str = ""

    def __post_init__(self) -> None:
        if self.strength not in STRENGTHS:
            raise ValueError(f"unknown constraint strength {self.strength!r}")
        if self.end_us < self.start_us:
            raise ValueError("a constraint cannot end before it starts")
        if not self.reason.strip():
            raise ValueError("a constraint must say why it exists")

    def covers(self, at_us: int) -> bool:
        return self.start_us <= at_us < self.end_us

    def overlaps(self, start_us: int, end_us: int) -> bool:
        return start_us < self.end_us and end_us > self.start_us

    def applies_to(self, template_id: str) -> bool:
        return template_id in self.templates

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualFocus:
    """What must stay legible across one interval, and what that costs.

    A tracking duel needs the beam, the crosshair and the target visible, so
    it tolerates almost no occlusion and no camera departure. A projectile
    replay is the opposite: the camera should leave, the world may be opened
    up, and slow motion is the point.
    """
    subject: str
    start_us: int
    end_us: int
    required_visibility: str = HIGH
    max_occlusion: str = LOW
    camera_freedom: str = LOW
    information_density_limit: str = LOW
    transformation_tolerance: str = LOW
    purpose: str = ""

    def __post_init__(self) -> None:
        if self.subject not in SUBJECTS:
            raise ValueError(f"unknown visual focus {self.subject!r}")
        for f in (self.required_visibility, self.max_occlusion,
                  self.camera_freedom, self.information_density_limit,
                  self.transformation_tolerance):
            if f not in LEVELS:
                raise ValueError(f"unknown level {f!r}")
        if self.end_us < self.start_us:
            raise ValueError("a focus interval cannot end before it starts")

    @property
    def duration_us(self) -> int:
        return self.end_us - self.start_us

    def covers(self, at_us: int) -> bool:
        return self.start_us <= at_us < self.end_us

    def tolerates(self, *, occlusion: str = NONE, camera_change: str = NONE,
                  information: str = NONE, transformation: str = NONE) -> bool:
        """Whether an effect with these demands can run inside this focus."""
        return (_ORDER[occlusion] <= _ORDER[self.max_occlusion]
                and _ORDER[camera_change] <= _ORDER[self.camera_freedom]
                and _ORDER[information] <= _ORDER[self.information_density_limit]
                and _ORDER[transformation] <= _ORDER[self.transformation_tolerance])

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["duration_us"] = self.duration_us
        return d


# ── what each template demands of the frame ─────────────────────────────────
# occlusion / camera change / information density / transformation.
# A template with no entry is assumed to demand nothing.

DEMANDS: dict[str, dict[str, str]] = {
    "WORLD_STRIP": dict(occlusion=HIGH, transformation=HIGH),
    "WORLD_REBUILD": dict(occlusion=HIGH, transformation=HIGH),
    "WALL_XRAY": dict(occlusion=MEDIUM, transformation=HIGH),
    "MAP_CONSTRUCTION": dict(occlusion=HIGH, transformation=HIGH),
    "MOSAIC_TILE_STEP": dict(occlusion=HIGH, transformation=HIGH),
    "MODEL_MORPH": dict(occlusion=MEDIUM, transformation=HIGH),
    "MODEL_PULSE": dict(occlusion=LOW, transformation=LOW),
    "MATERIAL_FLASH": dict(occlusion=LOW, transformation=LOW),
    "LOW_HP_WORLD": dict(occlusion=LOW, transformation=MEDIUM),
    "TEXTURE_TEXT_REVEAL": dict(occlusion=MEDIUM, information=MEDIUM),
    "ENEMY_REVEAL_STEP": dict(occlusion=HIGH, transformation=HIGH,
                              information=MEDIUM),
    "SIDE_REPLAY": dict(camera_change=HIGH),
    "PROJECTILE_FOLLOW": dict(camera_change=HIGH),
    "PROJECTILE_REPLAY": dict(camera_change=HIGH),
    "GRENADE_ARC": dict(camera_change=HIGH),
    "ENEMY_POV_INSERT": dict(camera_change=HIGH),
    "POV_PIP": dict(occlusion=LOW, information=MEDIUM),
    "CAMERA_JOLT": dict(camera_change=MEDIUM),
    "FREEZE_HOLD": dict(),
    "SLOW_MOTION": dict(),
    "FRAME_REPEAT": dict(),
    "RHYTHMIC_IMAGE_STUTTER": dict(occlusion=MEDIUM),
    "TIME_ECHO": dict(occlusion=MEDIUM),
    "FREEZE_DECOMPOSITION": dict(occlusion=MEDIUM, transformation=MEDIUM),
    "DEATH_FLASH_MONTAGE": dict(occlusion=HIGH, camera_change=HIGH),
    "DEATH_REWIND": dict(camera_change=MEDIUM),
    "DAMAGE_LEDGER_TICK": dict(information=LOW),
    "ROUND_DAMAGE_TOTAL": dict(information=MEDIUM),
    "ENEMY_COUNT_TICK": dict(information=LOW),
    "RAIL_COOLDOWN_BAR": dict(information=LOW),
    "DIEGETIC_SCOREBOARD": dict(information=MEDIUM),
    "CA_EXPLAINER_CARD": dict(information=HIGH, occlusion=MEDIUM),
    "CHAT_BUBBLE": dict(information=LOW),
    "GLITCH_INSERT": dict(occlusion=MEDIUM, transformation=MEDIUM),
    "MOVEMENT_ACCENT": dict(),
    "MATCH_CUT_OVERLAP": dict(camera_change=MEDIUM),
    "MOVEMENT_MATCH_OVERLAP": dict(camera_change=MEDIUM),
    "DEATH_EXPLOSION_MATCH": dict(camera_change=MEDIUM),
    "ROCKET_FLYBY_BRIDGE": dict(camera_change=HIGH),
    "WORLD_MORPH_BRIDGE": dict(occlusion=HIGH, transformation=HIGH,
                               camera_change=HIGH),
}


def demands_of(template_id: str) -> dict[str, str]:
    d = dict(occlusion=NONE, camera_change=NONE, information=NONE,
             transformation=NONE)
    d.update(DEMANDS.get(template_id, {}))
    return d


def focus_permits(focus: VisualFocus, template_id: str) -> bool:
    return focus.tolerates(**demands_of(template_id))


def why_refused(focus: VisualFocus, template_id: str) -> str:
    """Which demand exceeded which tolerance, in words."""
    d = demands_of(template_id)
    limits = {"occlusion": focus.max_occlusion,
              "camera_change": focus.camera_freedom,
              "information": focus.information_density_limit,
              "transformation": focus.transformation_tolerance}
    over = [f"{k} {d[k]} exceeds {limits[k]}" for k in d
            if _ORDER[d[k]] > _ORDER[limits[k]]]
    if not over:
        return ""
    return (f"{template_id} would hide what the viewer is meant to follow "
            f"({focus.subject}): " + ", ".join(over))


# ── ready-made focus profiles ───────────────────────────────────────────────

@dataclass(frozen=True)
class ReturnPlan:
    """When a camera must leave a cinematic view to be back in time.

    A protected interval does not begin the moment the camera arrives. The
    viewer needs the first-person view established before the skill starts,
    or the tracking reads as something that happened while we were still
    settling. How much lead that takes is a question for the Effect Lab; the
    geometry is not.
    """
    focus_start_us: int
    handoff_us: int
    establish_us: int
    feasible: bool
    latest_start_us: int
    latest_arrival_us: int
    shortfall_us: int = 0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def plan_return(focus: "VisualFocus", handoff_us: int, establish_us: int,
                earliest_us: int = 0) -> ReturnPlan:
    """Where a return-to-FPV handoff has to start, and whether it can.

    `establish_us` is how long the first-person view must be settled before
    the protected interval opens. It is currently an unmeasured judgement --
    the camera sweep exists to replace it with a number.
    """
    arrival = focus.start_us - establish_us
    start = arrival - handoff_us
    ok = start >= earliest_us
    return ReturnPlan(
        focus_start_us=focus.start_us, handoff_us=handoff_us,
        establish_us=establish_us, feasible=ok,
        latest_start_us=start, latest_arrival_us=arrival,
        shortfall_us=(0 if ok else earliest_us - start),
        reason=("" if ok else
                f"a {handoff_us/1000:.0f} ms move plus "
                f"{establish_us/1000:.0f} ms to settle needs to begin "
                f"{(earliest_us - start)/1000:.0f} ms earlier than the scene "
                f"allows; either the move is shorter or the cinematic view "
                f"is entered sooner"))


def tracking_focus(start_us: int, end_us: int) -> VisualFocus:
    """A sustained aim duel. The beam, the crosshair and the target are the
    story, so nothing may sit in front of them and the camera stays put."""
    return VisualFocus(SKILL_TRACKING, start_us, end_us,
                       required_visibility=HIGH, max_occlusion=NONE,
                       camera_freedom=NONE, information_density_limit=LOW,
                       transformation_tolerance=NONE,
                       purpose="the tracking itself is the skill; anything in "
                               "front of it hides the thing worth watching")


def projectile_focus(start_us: int, end_us: int) -> VisualFocus:
    """A shot worth examining. The camera should leave, and opening the world
    up is the point rather than a distraction."""
    return VisualFocus(PROJECTILE_TRAJECTORY, start_us, end_us,
                       required_visibility=HIGH, max_occlusion=MEDIUM,
                       camera_freedom=HIGH, information_density_limit=MEDIUM,
                       transformation_tolerance=HIGH,
                       purpose="the flight and its impact are the subject, and "
                               "showing them may require leaving first person")


def threat_focus(start_us: int, end_us: int) -> VisualFocus:
    """Establishing what the player is up against. Transformation is welcome:
    that is how the odds become legible."""
    return VisualFocus(TEAM_THREAT, start_us, end_us,
                       required_visibility=MEDIUM, max_occlusion=HIGH,
                       camera_freedom=MEDIUM, information_density_limit=HIGH,
                       transformation_tolerance=HIGH,
                       purpose="the viewer must grasp the odds, which is what "
                               "stripping and revealing is for")


def movement_focus(start_us: int, end_us: int) -> VisualFocus:
    return VisualFocus(MOVEMENT_TECH, start_us, end_us,
                       required_visibility=HIGH, max_occlusion=LOW,
                       camera_freedom=MEDIUM, information_density_limit=LOW,
                       transformation_tolerance=LOW,
                       purpose="the route and the speed are the subject")


def damage_focus(start_us: int, end_us: int) -> VisualFocus:
    """Numbers on a target need to be readable, which is a far weaker claim
    than protecting a skill. It asks for a legible background, not for the
    rest of the film to hold still, and it covers only the interval where the
    numbers are actually on screen."""
    return VisualFocus(DAMAGE_STORY_FOCUS, start_us, end_us,
                       required_visibility=MEDIUM, max_occlusion=MEDIUM,
                       camera_freedom=HIGH, information_density_limit=HIGH,
                       transformation_tolerance=MEDIUM,
                       purpose="the numbers must stay readable against the "
                               "action, without freezing the rest of the film")


# ── evaluating a plan against focuses and constraints ───────────────────────

def permitted_at(template_id: str, at_us: int,
                 focuses: Sequence[VisualFocus] = (),
                 constraints: Sequence[ScopedConstraint] = ()) -> tuple[bool, str]:
    """Whether this template may run at this instant, and why not."""
    for c in constraints:
        if c.covers(at_us) and c.applies_to(template_id) and c.strength == FORBID:
            return (False, c.reason)
    for f in focuses:
        if f.covers(at_us) and not focus_permits(f, template_id):
            return (False, why_refused(f, template_id))
    return (True, "")


def permitted_over(template_id: str, start_us: int, end_us: int,
                   focuses: Sequence[VisualFocus] = (),
                   constraints: Sequence[ScopedConstraint] = ()
                   ) -> tuple[bool, str]:
    """Whether it may run across a whole span. An effect that would intrude on
    any protected instant is refused for the span."""
    for c in constraints:
        if (c.strength == FORBID and c.applies_to(template_id)
                and c.overlaps(start_us, end_us)):
            return (False, c.reason)
    for f in focuses:
        if f.overlaps_span(start_us, end_us) if hasattr(f, "overlaps_span") else (
                start_us < f.end_us and end_us > f.start_us):
            if not focus_permits(f, template_id):
                return (False, why_refused(f, template_id))
    return (True, "")


def free_intervals(span: tuple[int, int], template_id: str,
                   focuses: Sequence[VisualFocus] = (),
                   constraints: Sequence[ScopedConstraint] = ()
                   ) -> list[tuple[int, int]]:
    """Where inside a scene this template IS allowed.

    This is the whole point of scoping: a world strip refused during a
    tracking interval is still perfectly good in the seconds before it.
    """
    blocked: list[tuple[int, int]] = []
    for c in constraints:
        if c.strength == FORBID and c.applies_to(template_id):
            blocked.append((c.start_us, c.end_us))
    for f in focuses:
        if not focus_permits(f, template_id):
            blocked.append((f.start_us, f.end_us))
    if not blocked:
        return [span]
    blocked.sort()
    merged: list[list[int]] = []
    for s, e in blocked:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    out: list[tuple[int, int]] = []
    cursor = span[0]
    for s, e in merged:
        if s > cursor:
            out.append((cursor, min(s, span[1])))
        cursor = max(cursor, e)
        if cursor >= span[1]:
            break
    if cursor < span[1]:
        out.append((cursor, span[1]))
    return [(a, b) for a, b in out if b > a]
