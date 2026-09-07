"""RenderFrame — what the renderer is allowed to know.

THE POINT OF THIS MODULE IS THE BOUNDARY. FrameTruth is game truth; a renderer
must never read it directly, because a renderer that can see the whole round
will eventually start deciding things about it. RenderFrame is a thin, flat,
one-instant projection of FrameTruth: a camera, some placed actors, a map name
and an output spec. It carries no round, no history, no future, and nothing the
rasteriser could use to infer what happened.

The mapping is deliberately dull, and every field traces to something observed:

    FrameTruth.map_name          -> RenderFrame.map
    Frame.server_time_ms         -> RenderFrame.server_time_ms   (the demo's own clock)
    ActorTruth.position          -> Actor.origin
    ActorTruth.yaw               -> Actor.angles[YAW]
    ActorTruth.legs_anim/torso_anim -> Actor.legs_anim/torso_anim
    PresenterProfile.model/skin  -> Actor.model/skin             (IDENTITY, not performance)

Two things this module refuses to do:

  * It does not interpolate. A frame is a sample. Between two samples there is
    no third truth, and a renderer asking for one gets the sample at-or-before.
  * It does not invent an actor. Where FrameTruth observed nobody -- because
    the demo did not -- the actor is simply absent from the frame (HL-6).

Character identity is joined here and nowhere earlier: a trace says how a body
moved, a PresenterProfile says who is wearing it. The same trace can be
rendered as anybody.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable, Sequence

from engine.pantheon.choreography import VIEW_HEIGHT

VERSION = "render-frame-v1"

Vec3 = tuple[float, float, float]


@dataclass
class RenderActor:
    """One placed body. Performance and identity, joined."""
    actor_id: str
    client: int
    team: str
    model: str                      # identity: "sarge", "keel", ...
    skin: str = "default"
    origin: Vec3 = (0.0, 0.0, 0.0)
    angles: Vec3 = (0.0, 0.0, 0.0)  # pitch, yaw, roll
    legs_anim: int = 0
    torso_anim: int = 0
    weapon: str = "UNKNOWN"
    alive: bool = True
    # How long this actor has been in this animation, in ms. Derived by
    # watching the animation number change across observed frames -- the
    # demo told us when it changed, so the renderer never has to guess
    # where in a cycle a body is.
    anim_time_ms: int = 0


@dataclass
class RenderCamera:
    origin: Vec3
    angles: Vec3                    # pitch, yaw, roll
    fov: float = 90.0
    source: str = "UNKNOWN"         # RECORDED_POV | VALIDATED | AUTHORED
    owner: str | None = None        # actor whose eyes these are; not drawn


@dataclass
class RenderFrame:
    """Everything the renderer may know about one instant, and no more."""
    map: str
    server_time_ms: int
    frame_index: int
    camera: RenderCamera
    actors: list[RenderActor] = field(default_factory=list)
    width: int = 1280
    height: int = 720
    out: str = "frame.tga"
    provenance: str = "UNKNOWN"
    demo_hash: str | None = None
    version: str = VERSION

    def to_dict(self) -> dict:
        d = asdict(self)
        d["camera"] = asdict(self.camera)
        d["actors"] = [asdict(a) for a in self.actors]
        return d


def pov_camera(actor, *, fov: float = 90.0) -> RenderCamera:
    """The camera an actor's own eyes were at.

    Recorded, not composed: the position is his observed origin lifted by the
    engine's own view height, and the angles are his observed aim. No smoothing,
    no lead, no framing. Choosing a *cinematic* camera is a different job in a
    different module, and doing it here would quietly make the renderer a
    director.
    """
    x, y, z = actor.position
    return RenderCamera(
        origin=(x, y, z + VIEW_HEIGHT),
        angles=(actor.pitch, actor.yaw, 0.0),
        fov=fov, source="RECORDED_POV", owner=actor.actor_id)


def from_frame_truth(truth, *, cast: dict[str, Any],
                     camera_owner: str | None = None,
                     camera: RenderCamera | None = None,
                     width: int = 1280, height: int = 720,
                     fov: float = 90.0,
                     out_pattern: str = "frame_%05d.tga",
                     indices: Iterable[int] | None = None,
                     times_ms: Sequence[int] | None = None,
                     demo_hash: str | None = None) -> list[RenderFrame]:
    """Project FrameTruth into RenderFrames.

    `cast` maps actor_id -> PresenterProfile (or anything with .model/.skin).
    An actor with no cast entry is NOT rendered: an unnamed body would be the
    renderer choosing an identity, which is exactly what it must not do.

    `camera_owner` renders that actor's recorded POV and omits his own body,
    the way the engine does in first person. `camera` overrides with a fixed
    one. Exactly one of them, or neither for a still camera at the origin --
    which is a debugging convenience and says so in `source`.
    """
    if camera_owner and camera:
        raise ValueError("give camera_owner or camera, not both")

    # Resampling to an output rate is a LOOKUP, never a blend: each output
    # instant takes the sample at-or-before it, exactly as FrameTruth.at()
    # does. Rendering 30fps from a 40Hz demo must not invent poses that were
    # never observed, so the same source frame may legitimately repeat.
    source = list(enumerate(truth.frames))
    if times_ms is not None:
        picked = []
        for t_ms in times_ms:
            chosen = None
            for i, f in source:
                if f.server_time_ms <= t_ms:
                    chosen = (i, f)
                else:
                    break
            if chosen is not None:
                picked.append(chosen)
        source = picked

    frames: list[RenderFrame] = []
    wanted = None if indices is None else set(indices)
    # actor_id -> (legs, torso, server_time_ms the pair was first seen)
    anim_since: dict[str, tuple[int, int, int]] = {}

    for out_index, (i, f) in enumerate(source):
        if wanted is not None and i not in wanted:
            continue

        if camera_owner:
            who = f.actors.get(camera_owner)
            if who is None:
                # His eyes were not observed here. Skipping is the honest
                # answer; holding the last camera would invent a viewpoint.
                continue
            cam = pov_camera(who, fov=fov)
        elif camera:
            cam = camera
        else:
            cam = RenderCamera(origin=(0.0, 0.0, 0.0), angles=(0.0, 0.0, 0.0),
                               fov=fov, source="AUTHORED")

        actors: list[RenderActor] = []
        for actor_id, a in f.actors.items():
            if actor_id == cam.owner:
                continue                       # you do not see your own body
            profile = cast.get(actor_id)
            if profile is None:
                continue                       # uncast: not the renderer's call
            prev = anim_since.get(actor_id)
            if prev is None or prev[0] != a.legs_anim or prev[1] != a.torso_anim:
                anim_since[actor_id] = (a.legs_anim, a.torso_anim,
                                        f.server_time_ms)
            started = anim_since[actor_id][2]
            actors.append(RenderActor(
                actor_id=actor_id, client=a.client, team=a.team,
                model=getattr(profile, "model", str(profile)),
                skin=getattr(profile, "skin", "default"),
                origin=tuple(float(v) for v in a.position),
                angles=(0.0, float(a.yaw), 0.0),   # a body yaws; it does not pitch
                legs_anim=a.legs_anim, torso_anim=a.torso_anim,
                weapon=a.weapon, alive=a.alive,
                anim_time_ms=f.server_time_ms - started))

        frames.append(RenderFrame(
            map=truth.map_name, server_time_ms=f.server_time_ms,
            frame_index=i, camera=cam, actors=actors,
            width=width, height=height, out=out_pattern % out_index,
            provenance=truth.provenance, demo_hash=demo_hash))

    return frames


def save(frames: Sequence[RenderFrame], path: Path) -> Path:
    """One JSON document: the manifest the native host consumes."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {"version": VERSION, "count": len(frames),
         "frames": [f.to_dict() for f in frames]}, indent=1), encoding="utf-8")
    return path


def save_shot_script(frames: Sequence[RenderFrame], path: Path) -> Path:
    """Write the shot script the native host reads.

    This is the SAME RenderFrame data in a flat, line-oriented form, because
    the host is C and a JSON parser there would be a place for meaning to get
    invented. The JSON remains the contract; this is its wire form, generated
    from it and never hand-edited.

    Grammar, one record per line:

        map <name>
        size <w> <h>
        provenance <token>
        demo <hash>
        player <model> <skin>                     # declared once, in order
        frame <idx> <serverTimeMs> <cx cy cz> <pitch yaw roll> <fov> <out>
        actor <playerIdx> <x y z> <pitch yaw roll> <legs> <torso> <animMs>

    The host treats an unknown keyword as fatal, so this writer and that
    parser cannot drift apart quietly.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Players are declared once and referenced by index, so identity is stated
    # in exactly one place.
    roster: list[tuple[str, str]] = []
    for f in frames:
        for a in f.actors:
            if (a.model, a.skin) not in roster:
                roster.append((a.model, a.skin))

    first = frames[0]
    out = ["# pantheon shot script v1 -- generated from RenderFrame, do not edit",
           "map %s" % first.map,
           "size %d %d" % (first.width, first.height),
           "provenance %s" % (first.provenance or "UNKNOWN"),
           "demo %s" % (first.demo_hash or "UNKNOWN")]
    out += ["player %s %s" % (m, sk) for m, sk in roster]

    for f in frames:
        c = f.camera
        out.append("frame %d %d %.3f %.3f %.3f %.3f %.3f %.3f %.2f %s" % (
            f.frame_index, f.server_time_ms,
            c.origin[0], c.origin[1], c.origin[2],
            c.angles[0], c.angles[1], c.angles[2], c.fov, f.out))
        for a in f.actors:
            out.append("actor %d %.3f %.3f %.3f %.3f %.3f %.3f %d %d %d" % (
                roster.index((a.model, a.skin)),
                a.origin[0], a.origin[1], a.origin[2],
                a.angles[0], a.angles[1], a.angles[2],
                a.legs_anim, a.torso_anim, a.anim_time_ms))

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path
