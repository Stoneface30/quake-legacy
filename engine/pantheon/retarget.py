"""Retarget — where and which way a recorded performance is replayed.

A PerformanceTrace is a fact about one player on one map at one place. A film
wants that same action performed by ANOTHER character, possibly somewhere
else on the map. Two things must never change on the way: TIME (the trace's
own serverTime spacing is the action) and the SHAPE of the motion (a rigid
transform in the horizontal plane, nothing scaled, nothing eased).

    EXACT_WORLD  same map, same coordinates, same heading. The default.
    LOCAL_FRAME  the trace's own anchor (its first grounded sample) is moved
                 to a target point and heading; everything else follows
                 rigidly. Valid only where the map allows it, which is a
                 question for MapSpatialIndex, not for this module.

This module holds the arithmetic. `Actor.perform` applies it; nothing here
knows a renderer exists.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.pantheon.performance import PerformanceTrace

Vec3 = tuple[float, float, float]


class TransformMode(Enum):
    EXACT_WORLD = "exact_world"
    LOCAL_FRAME = "local_frame"


@dataclass(frozen=True)
class Retarget:
    """A rigid transform in the horizontal plane: rotate about the world
    origin by `yaw_offset`, then translate by `offset`. Identical to the
    arithmetic in `Actor.perform`, held here so the comparison side can apply
    the same one to the real trace."""
    mode: TransformMode = TransformMode.EXACT_WORLD
    offset: Vec3 = (0.0, 0.0, 0.0)
    yaw_offset: float = 0.0
    anchor_from: Vec3 | None = None
    anchor_to: Vec3 | None = None

    # -- constructors --------------------------------------------------
    @classmethod
    def exact_world(cls) -> "Retarget":
        return cls()

    @classmethod
    def local_frame(cls, trace: "PerformanceTrace", *, to: Vec3,
                    yaw: float | None = None) -> "Retarget":
        """Move the trace so its anchor lands on `to`, optionally facing `yaw`.

        The anchor is the first GROUNDED sample: a performance is placed by
        where the player stood before the action, not by a point in the air.
        """
        anchor = _anchor(trace)
        base_yaw = trace.aim[0].yaw if trace.aim else 0.0
        yaw_offset = 0.0 if yaw is None else (yaw - base_yaw)
        cy, sy = math.cos(math.radians(yaw_offset)), math.sin(math.radians(yaw_offset))
        rx = anchor[0] * cy - anchor[1] * sy
        ry = anchor[0] * sy + anchor[1] * cy
        offset = (to[0] - rx, to[1] - ry, to[2] - anchor[2])
        return cls(TransformMode.LOCAL_FRAME, offset, yaw_offset % 360.0,
                   anchor_from=anchor, anchor_to=to)

    # -- the arithmetic ------------------------------------------------
    def _cs(self) -> tuple[float, float]:
        r = math.radians(self.yaw_offset)
        return math.cos(r), math.sin(r)

    def place(self, o: Vec3) -> Vec3:
        cy, sy = self._cs()
        x, y = o[0] * cy - o[1] * sy, o[0] * sy + o[1] * cy
        return (x + self.offset[0], y + self.offset[1], o[2] + self.offset[2])

    def turn(self, v: Vec3) -> Vec3:
        cy, sy = self._cs()
        return (v[0] * cy - v[1] * sy, v[0] * sy + v[1] * cy, v[2])

    def yaw(self, y: float) -> float:
        return (y + self.yaw_offset) % 360.0

    def perform_kwargs(self) -> dict:
        """What `Actor.perform` takes."""
        return {"offset": self.offset, "yaw_offset": self.yaw_offset}

    def is_identity(self) -> bool:
        return self.offset == (0.0, 0.0, 0.0) and self.yaw_offset % 360.0 == 0.0

    def as_dict(self) -> dict:
        return {"mode": self.mode.value, "offset": list(self.offset),
                "yaw_offset": self.yaw_offset,
                "anchor_from": list(self.anchor_from) if self.anchor_from else None,
                "anchor_to": list(self.anchor_to) if self.anchor_to else None}


def _anchor(trace: "PerformanceTrace") -> Vec3:
    for s in trace.transform:
        if not s.airborne:
            return s.origin
    if trace.transform:
        return trace.transform[0].origin
    raise ValueError("a trace with no transform samples has no anchor")


# ── map validity ───────────────────────────────────────────────────────────

@dataclass
class RetargetValidation:
    """Does the transformed performance stay inside space real players used?"""
    grounded_samples: int
    grounded_in_walked: int
    landing_in_walked: bool | None       # None when the trace never lands
    fraction_walked: float
    ok: bool
    notes: list[str]

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def validate_retarget(trace: "PerformanceTrace", rt: Retarget, spatial,
                      *, min_fraction: float = 0.9) -> RetargetValidation:
    """Check every GROUNDED sample of the transformed trace against the
    map's walked space, and the first landing after any airborne stretch.

    `spatial` is anything with `is_walked(pos) -> bool` -- MapSpatialIndex in
    practice. Airborne samples are not checked: the air is not walked, and a
    trajectory through it is the physics' business, not the floor's.

    EXACT_WORLD is valid by construction (the real player was there) and is
    reported as such without consulting the index.
    """
    notes: list[str] = []
    grounded = [s for s in trace.transform if not s.airborne]
    if rt.mode is TransformMode.EXACT_WORLD and rt.is_identity():
        return RetargetValidation(len(grounded), len(grounded), None, 1.0, True,
                                  ["EXACT_WORLD: the real player stood here"])
    inside = 0
    for s in grounded:
        if spatial.is_walked(rt.place(s.origin)):
            inside += 1
    frac = (inside / len(grounded)) if grounded else 0.0

    landing_ok: bool | None = None
    prev_air = False
    for s in trace.transform:
        if prev_air and not s.airborne:
            landing_ok = bool(spatial.is_walked(rt.place(s.origin)))
            if not landing_ok:
                notes.append(f"landing at t={s.t} falls outside walked space")
            break
        prev_air = s.airborne

    ok = frac >= min_fraction and landing_ok is not False
    if frac < min_fraction:
        notes.append(f"only {frac:.0%} of grounded samples inside walked space "
                     f"(need {min_fraction:.0%}) -- the performance would pass "
                     "through geometry nobody walked")
    return RetargetValidation(len(grounded), inside, landing_ok, round(frac, 3),
                              ok, notes)
