"""FrameTruth — what was true in the world at one instant.

WHY IT IS EMITTED, NOT RECONSTRUCTED. A RoundScenario knows every actor's
position, health and animation exactly, because it authored them. Writing that
to a demo and then parsing it back would lose precision and, worse, would make
the overlay's idea of the world a SECOND derivation that can disagree with the
first. Camera targets, world-space arrows, HP labels, alive counters, masks and
any future Blender transform all read from here, so there is exactly one answer
to "where was BLUE_2 at 6.4 seconds".

ONE TIME BASIS. `server_time_ms` is the authority, and it is the demo's own
clock -- the same number the .dm_73 snapshot carries. `t` is a convenience in
seconds from scenario start. Nothing downstream is allowed to invent a third
clock: an overlay drawn at "frame 384" must resolve that to a server_time
through this file, not through its own arithmetic.

NO BACKEND INVENTS GAME STATE. Wolfcam renders beauty, Blender may render
masks, ComfyUI may stylise -- none of them decides where a player was.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

Vec3 = tuple[float, float, float]


@dataclass
class ActorTruth:
    """One player at one instant. Every field is authored, none is inferred."""
    actor_id: str
    client: int
    team: str
    position: Vec3
    yaw: float
    pitch: float = 0.0
    velocity: Vec3 = (0.0, 0.0, 0.0)
    health: int = 200
    armor: int = 100
    weapon: str = "ROCKET"
    alive: bool = True
    legs_anim: int = 0
    torso_anim: int = 0
    target: str | None = None


@dataclass
class RoundStateTruth:
    phase: str                      # "pre" | "countdown" | "active" | "over"
    round_number: int
    alive_red: int
    alive_blue: int
    winner: str | None = None


@dataclass
class SemanticEvent:
    """Something that happened, in game terms. The overlay's cue sheet."""
    t: float
    server_time_ms: int
    kind: str                       # fire | damage | kill | round_win | ...
    actor: str | None = None
    target: str | None = None
    weapon: str | None = None
    amount: int = 0
    position: Vec3 | None = None


@dataclass
class Frame:
    t: float
    server_time_ms: int
    actors: dict[str, ActorTruth]
    round_state: RoundStateTruth
    events: list[SemanticEvent] = field(default_factory=list)
    camera: dict[str, Any] | None = None


class FrameTruth:
    """The whole round, frame by frame, in the demo's own clock."""

    VERSION = "frame-truth-v1"

    def __init__(self, *, map_name: str, snapshot_hz: int,
                 provenance: str = "SYNTHETIC_EXPLAINER") -> None:
        self.map_name = map_name
        self.snapshot_hz = snapshot_hz
        self.provenance = provenance
        self.frames: list[Frame] = []

    # -- lookup --------------------------------------------------------
    def at(self, t: float) -> Frame:
        """The frame covering `t`. Nearest-at-or-before, never interpolated:
        a frame IS the sample, and inventing one between two would be a third
        derivation of the truth."""
        if not self.frames:
            raise RuntimeError("no frames")
        best = self.frames[0]
        for f in self.frames:
            if f.t <= t + 1e-9:
                best = f
            else:
                break
        return best

    def at_server_time(self, server_time_ms: int) -> Frame:
        return min(self.frames,
                   key=lambda f: abs(f.server_time_ms - server_time_ms))

    def actor_track(self, actor_id: str) -> list[tuple[float, Vec3]]:
        """A world-space path, for arrows and camera targets."""
        return [(f.t, f.actors[actor_id].position)
                for f in self.frames if actor_id in f.actors]

    def events(self, kind: str | None = None) -> list[SemanticEvent]:
        out = [e for f in self.frames for e in f.events]
        return [e for e in out if kind is None or e.kind == kind]

    @property
    def duration(self) -> float:
        return self.frames[-1].t if self.frames else 0.0

    # -- io ------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "version": self.VERSION,
            "map": self.map_name,
            "snapshot_hz": self.snapshot_hz,
            "provenance": self.provenance,
            "duration_s": round(self.duration, 3),
            "frames": [
                {"t": round(f.t, 4), "server_time_ms": f.server_time_ms,
                 "round_state": asdict(f.round_state),
                 "actors": {k: asdict(v) for k, v in f.actors.items()},
                 "events": [asdict(e) for e in f.events],
                 "camera": f.camera}
                for f in self.frames],
        }

    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=1), encoding="utf-8")
        return path

    # -- construction --------------------------------------------------
    @classmethod
    def from_scenario(cls, scn, *, duration: float) -> "FrameTruth":
        """Sample the scenario at its own snapshot rate.

        Deliberately the same rate and the same serverTime mapping the
        compiler uses, so a FrameTruth frame and a demo snapshot are the same
        instant rather than two nearby ones.
        """
        from engine.pantheon.scenario import SNAPSHOT_HZ, SNAPSHOT_MS, Stance, \
            Team, _LEGS, _TORSO

        ft = cls(map_name=scn.map_name, snapshot_hz=SNAPSHOT_HZ)
        base_ms = 1000
        frames = int(duration * SNAPSHOT_HZ)

        # events bucketed onto the tick they land on, so an overlay asking
        # "what happened this frame" gets an answer aligned to the picture
        buckets: dict[int, list[SemanticEvent]] = {}
        for e in scn._events:
            tick = int(round(e.t * SNAPSHOT_HZ))
            buckets.setdefault(tick, []).append(SemanticEvent(
                t=e.t, server_time_ms=base_ms + tick * SNAPSHOT_MS,
                kind=e.kind, actor=e.actor, target=e.target,
                weapon=e.weapon.name if e.weapon else None,
                amount=e.amount, position=e.position))
        if scn._win:
            tick = int(round(scn._win[0] * SNAPSHOT_HZ))
            buckets.setdefault(tick, []).append(SemanticEvent(
                t=scn._win[0], server_time_ms=base_ms + tick * SNAPSHOT_MS,
                kind="round_win", actor=None, target=scn._win[1].label))
        if scn._reset_at is not None:
            tick = int(round(scn._reset_at * SNAPSHOT_HZ))
            buckets.setdefault(tick, []).append(SemanticEvent(
                t=scn._reset_at, server_time_ms=base_ms + tick * SNAPSHOT_MS,
                kind="round_reset"))

        # alive counts as a running level, from the authored log
        def alive_at(t: float) -> tuple[int, int]:
            red = sum(1 for a in scn.actors.values() if a.team is Team.RED)
            blue = sum(1 for a in scn.actors.values() if a.team is Team.BLUE)
            for when, snapshot in scn._alive_log:
                if when <= t:
                    red, blue = snapshot[Team.RED], snapshot[Team.BLUE]
            return red, blue

        for i in range(frames):
            t = i / SNAPSHOT_HZ
            actors: dict[str, ActorTruth] = {}
            for a in scn.actors.values():
                k = a._at(t)
                actors[a.name] = ActorTruth(
                    actor_id=a.name, client=a.client, team=a.team.label,
                    position=tuple(round(v, 3) for v in k.origin),
                    yaw=round(k.yaw, 2), health=k.health, armor=k.armor,
                    weapon=k.weapon.name, alive=k.stance is not Stance.DEAD,
                    legs_anim=_LEGS[k.stance], torso_anim=_TORSO[k.stance])

            red, blue = alive_at(t)
            if scn._round_begin is None:
                phase = "pre"
            elif t < scn._round_begin - scn._countdown:
                phase = "pre"
            elif t < scn._round_begin:
                phase = "countdown"
            elif scn._win and t >= scn._win[0]:
                phase = "over"
            else:
                phase = "active"
            rnd = 2 if (scn._reset_at is not None and t >= scn._reset_at) else 1

            ft.frames.append(Frame(
                t=t, server_time_ms=base_ms + i * SNAPSHOT_MS, actors=actors,
                round_state=RoundStateTruth(
                    phase=phase, round_number=rnd, alive_red=red,
                    alive_blue=blue,
                    winner=scn._win[1].label if (scn._win and phase == "over")
                    else None),
                events=buckets.get(i, [])))
        return ft
