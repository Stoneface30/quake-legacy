"""A RECIPE PLUS A MOMENT BECOMES A PLAN. NOTHING ELSE MAY.

This is the gate the brief insisted on: no proof script may jump from "the
recipe is compatible" to "run the renderer". A recipe compiles into a
ChoreographyPlan -- cues on an edit clock, a TimeMap, a CameraPlan -- and the
plan compiles into a ShotSpec. If a cue has no backend, it stays in the plan
and is reported, because a beat that silently disappears is how a shot ships
without the thing it was for.

WHERE THE X-RAY GOES IS MEASURED, NOT CHOSEN. The recipe says "reveal the
enemy the geometry is hiding". The plan asks the map: it traces the actor's
eye to the other body over the real BSP, sample by sample, and puts the reveal
on the span that is actually OCCLUDED. When the enemy steps into view the
overlay clears, because an X-ray still drawn over a plainly visible player is
decoration and stops being information.

Historical truth is untouched. Nothing here moves a body, re-aims it, changes
a weapon, a time or an outcome. The plan only decides what the CAMERA and the
PRESENTATION do around action that already happened.
"""
from __future__ import annotations

import math

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

VIEW_HEIGHT = 26.0        # q_shared DEFAULT_VIEWHEIGHT
BODY_MID = 20.0           # the middle of a body, not its feet
FOV_X = 90.0              # the capture's horizontal field of view
ASPECT = 16 / 9

# AN X-RAY CANNOT REVEAL WHAT IS NOT IN THE PICTURE.
#
# The first run of this recipe learned it the expensive way: the plan chose the
# longest OCCLUDED stretch, filmed it, and the frame showed nothing, because
# through all 19 samples the hidden body sat 56 to 64 degrees off the centre of
# view and up to 39 degrees below it. Occluded and on-screen are two different
# questions and the reveal needs both.


class Visibility(str, Enum):
    NORMAL_VISIBLE = "NORMAL_VISIBLE"
    OCCLUDED_IN_FRAME = "OCCLUDED_IN_FRAME"      # hidden, and on screen
    OCCLUDED_OFF_SCREEN = "OCCLUDED_OFF_SCREEN"  # hidden, and not on screen
    OFF_SCREEN = "OFF_SCREEN"                    # visible, but outside the view
    UNOBSERVED = "UNOBSERVED"      # the demo did not carry the other body


class CueKind(str, Enum):
    LOOK = "LOOK"                  # what the camera does
    REVEAL = "REVEAL"              # a presentation change, e.g. x-ray on/off
    HOLD = "HOLD"                  # time stops or slows
    GRAPHIC = "GRAPHIC"            # something drawn over the frame


@dataclass
class Cue:
    at_ms: int                     # server time, because the action owns the clock
    kind: CueKind
    semantic: str                  # film words: XRAY_ON, XRAY_OFF, FREEZE
    because: str                   # the measurement that put it here
    capability: str | None = None  # what a backend must have to deliver it
    deliverable: bool = True

    def as_dict(self) -> dict:
        return {"at_ms": self.at_ms, "kind": self.kind.value,
                "semantic": self.semantic, "because": self.because,
                "capability": self.capability, "deliverable": self.deliverable}


@dataclass
class TimeMap:
    """Edit time against server time. 1:1 until something bends it."""
    start_ms: int
    end_ms: int
    rate: float = 1.0

    @property
    def seconds(self) -> float:
        return (self.end_ms - self.start_ms) / 1000.0

    def as_dict(self) -> dict:
        return {"start_ms": self.start_ms, "end_ms": self.end_ms,
                "rate": self.rate, "seconds": round(self.seconds, 2)}


@dataclass
class CameraPlan:
    """Where the eye is. For this recipe it is the recorded eye: the question
    is whether the X-ray reads, not whether we can also invent a camera."""
    mode: str                      # RECORDED_POV | FOLLOW | FREE
    subject_client: int
    note: str = ""

    def as_dict(self) -> dict:
        return {"mode": self.mode, "subject_client": self.subject_client,
                "note": self.note}


@dataclass
class ChoreographyPlan:
    recipe: str
    performance_id: str
    time: TimeMap
    camera: CameraPlan
    cues: list[Cue] = field(default_factory=list)
    visibility: list[dict] = field(default_factory=list)
    measurements: dict = field(default_factory=dict)
    deferred: list[str] = field(default_factory=list)

    @property
    def deliverable(self) -> bool:
        return all(c.deliverable for c in self.cues)

    def as_dict(self) -> dict:
        return {"recipe": self.recipe, "performance_id": self.performance_id,
                "time": self.time.as_dict(), "camera": self.camera.as_dict(),
                "cues": [c.as_dict() for c in self.cues],
                "measurements": self.measurements,
                "deferred": self.deferred,
                "deliverable": self.deliverable}


# -- measuring what the geometry hides -------------------------------------

def _in_frame(eye, look_yaw: float, look_pitch: float, body) -> tuple[bool, float, float]:
    """Is the body inside the camera's view, and by how much is it off?"""
    dx, dy = body[0] - eye[0], body[1] - eye[1]
    dz = body[2] - eye[2]
    bearing = math.degrees(math.atan2(dy, dx))
    yaw_off = (bearing - look_yaw + 180) % 360 - 180
    pitch_to = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    pitch_off = pitch_to - (-look_pitch)      # q3 pitch is inverted
    half_x = FOV_X / 2
    half_y = math.degrees(math.atan(math.tan(math.radians(half_x)) / ASPECT))
    return (abs(yaw_off) <= half_x and abs(pitch_off) <= half_y,
            round(yaw_off, 1), round(pitch_off, 1))


def visibility_track(demo: Path, *, actor: int, other: int, map_name: str,
                     start_ms: int, end_ms: int) -> tuple[list[dict], dict]:
    """Per sample: could the actor SEE the other body?

    Traced over the real map. Where either body was not observed, the answer
    is UNOBSERVED -- never a guess, because a guessed sight-line would put an
    X-ray over something the demo never saw.
    """
    from creative_suite.engine import camera_paths as CP
    from engine.pantheon import performance as PERF

    parsed = PERF._parse_with_anims(demo)
    a = PERF.extract_performance(demo, start_ms, end_ms, actor, parsed=parsed)
    b = PERF.extract_performance(demo, start_ms, end_ms, other, parsed=parsed)
    other_at = {s.t: s for s in b.transform}
    look_at = {x.t: x for x in a.aim}

    try:
        tracer = CP.bsp_tracer(map_name)
        traced = True
    except Exception as exc:                      # no map on this machine
        tracer, traced = None, False
        detail = str(exc)[:160]

    rows: list[dict] = []
    for s in a.transform:
        o, look = other_at.get(s.t), look_at.get(s.t)
        if o is None or look is None or not traced:
            rows.append({"t": s.t, "state": Visibility.UNOBSERVED.value})
            continue
        eye = (s.origin[0], s.origin[1], s.origin[2] + VIEW_HEIGHT)
        body = (o.origin[0], o.origin[1], o.origin[2] + BODY_MID)
        blocked = tracer.line_blocked(eye, body)
        onscreen, yaw_off, pitch_off = _in_frame(eye, look.yaw, look.pitch, body)
        if blocked:
            state = (Visibility.OCCLUDED_IN_FRAME if onscreen
                     else Visibility.OCCLUDED_OFF_SCREEN)
        else:
            state = (Visibility.NORMAL_VISIBLE if onscreen
                     else Visibility.OFF_SCREEN)
        rows.append({
            "t": s.t, "state": state.value, "in_frame": onscreen,
            "yaw_off_deg": yaw_off, "pitch_off_deg": pitch_off,
            "distance_u": round(sum((x - y) ** 2 for x, y in zip(eye, body)) ** 0.5, 1)})

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    meta = {"traced_over_bsp": traced, "map": map_name, "samples": len(rows),
            "counts": counts}
    if not traced:
        meta["why_not"] = detail
    return rows, meta


def occluded_spans(rows: list[dict], *, min_ms: int = 250) -> list[dict]:
    """Contiguous stretches where the body was hidden AND on screen.

    Short flickers are dropped: an overlay that blinks every 100 ms explains
    nothing. Off-screen stretches are dropped outright, because there is
    nothing in the picture for a reveal to reveal.
    """
    spans, cur = [], None
    for r in rows:
        if r["state"] == Visibility.OCCLUDED_IN_FRAME.value:
            cur = cur or {"start_ms": r["t"], "end_ms": r["t"], "samples": 0}
            cur["end_ms"], cur["samples"] = r["t"], cur["samples"] + 1
        elif cur:
            spans.append(cur)
            cur = None
    if cur:
        spans.append(cur)
    return [s for s in spans if s["end_ms"] - s["start_ms"] >= min_ms]


# -- the one builder this sprint --------------------------------------------

# The shot opens plain. A clip that starts already in X-ray has nothing to
# reveal: the viewer never sees the wall doing its job, so the overlay reads as
# a look rather than as information. This is a presentational choice and is
# recorded as one -- the reveal then covers most of the occluded span, not all
# of it.
OPEN_PLAIN_MS = 700


def plan_xray_actor(moment, *, demo: Path, lead_ms: int = 200) -> ChoreographyPlan:
    """XRAY_ACTOR, staged from the measured occlusion.

    `moment` is a ReviewMoment. The reveal covers the longest hidden stretch
    that ENDS before the decisive event, so the overlay clears as the enemy
    comes into view and the kill itself plays plainly.
    """
    from engine.pantheon import effect_recipes as ER

    recipe = ER.get("XRAY_ACTOR")
    pb = moment.playback
    other = next((p["client"] for p in moment.povs if p["role"] == "victim"),
                 None)
    if other is None:
        raise ValueError(f"{moment.performance_id}: no other body to reveal")

    rows, meta = visibility_track(demo, actor=pb.client, other=other,
                                  map_name=moment.location.map,
                                  start_ms=pb.start_ms, end_ms=pb.end_ms)
    spans = occluded_spans(rows)
    before = [s for s in spans if s["end_ms"] <= pb.server_time_ms]
    chosen = max(before or spans, key=lambda s: s["end_ms"] - s["start_ms"],
                 default=None)

    time = TimeMap(pb.start_ms, pb.end_ms)
    camera = CameraPlan("RECORDED_POV", pb.client,
                        "the recorded eye: this proof asks whether the reveal "
                        "reads, not whether we can also invent a camera")
    plan = ChoreographyPlan(recipe.id, moment.performance_id, time, camera,
                            visibility=rows, measurements=meta)

    if chosen is None:
        plan.deferred.append(
            "no occluded stretch long enough to be worth revealing: this "
            "moment does not need an X-ray")
        return plan

    on = max(pb.start_ms + OPEN_PLAIN_MS, chosen["start_ms"] - lead_ms)
    off = chosen["end_ms"]
    if on >= off:                      # the hidden stretch is shorter than the
        on = chosen["start_ms"]        # opening beat; keep the reveal readable
    plan.cues = [
        Cue(pb.start_ms, CueKind.LOOK, "NORMAL_ACTION",
            f"the shot opens plain for {on - pb.start_ms} ms so the viewer "
            f"sees the wall doing its job before anything is revealed",
            capability="BEAUTY_PASS"),
        Cue(on, CueKind.REVEAL, "XRAY_ON",
            f"the other body is occluded from {chosen['start_ms']} to "
            f"{chosen['end_ms']} ms, traced over the map "
            f"({chosen['samples']} samples)", capability="XRAY_PLAYER"),
        Cue(off, CueKind.REVEAL, "XRAY_OFF",
            "the body comes into normal view here, and an overlay drawn over "
            "a plainly visible player is decoration, not information",
            capability="XRAY_PLAYER"),
        Cue(pb.end_ms, CueKind.LOOK, "END",
            "the decisive event plays plainly, after the reveal has cleared",
            capability="BEAUTY_PASS"),
    ]

    # The freeze beat the grammar would like, and cannot have yet. Recorded as
    # deferred rather than quietly dropped.
    plan.deferred.append(
        "FREEZE at the reveal: the capability to hold the scene is only "
        "SOURCE_REGISTERED, so this beat is planned and not filmed")
    plan.measurements["reveal"] = {
        "on_ms": on, "off_ms": off, "span": chosen,
        "kill_ms": pb.server_time_ms,
        "occluded_spans_considered": spans}
    return plan


# -- plan -> ShotSpec --------------------------------------------------------

# to_shot_spec lives in the backend-facing layer (first_recipe_proof), not
# here: ShotSpec belongs to the render boundary, and a plan that imports the
# renderer is a plan that can launch one.
