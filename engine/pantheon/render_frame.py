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
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable, Sequence

from engine.pantheon.choreography import VIEW_HEIGHT

VERSION = "render-frame-v1"

Vec3 = tuple[float, float, float]


# WP_* (bg_public.h weapon_t) -> the assets that weapon uses. This is ASSET
# knowledge, not game truth: the demo says "weapon 5", the pak says what a
# rocket launcher looks like. Kept in one place so no feature code carries a
# magic weapon number.
WEAPON_ASSETS = {
    4: {"name": "GRENADE", "missile": "models/ammo/grenade1.md3",
        "hand": "models/weapons2/grenadel/grenadel.md3"},
    5: {"name": "ROCKET", "missile": "models/ammo/rocket/rocket.md3",
        "hand": "models/weapons2/rocketl/rocketl.md3"},
    6: {"name": "LIGHTNING", "missile": None,
        "hand": "models/weapons2/lightning/lightning.md3"},
    7: {"name": "RAIL", "missile": None,
        "hand": "models/weapons2/railgun/railgun.md3"},
}


def weapon_assets(weapon: int) -> dict:
    return WEAPON_ASSETS.get(weapon, {"name": "WEAPON_%d" % weapon,
                                      "missile": None, "hand": None})


def vector_to_angles(v) -> tuple[float, float, float]:
    """q_math.c vectoangles. A missile points along its own velocity."""
    x, y, z = v
    if x == 0.0 and y == 0.0:
        return (-90.0 if z > 0 else 90.0, 0.0, 0.0)
    yaw = math.degrees(math.atan2(y, x))
    if yaw < 0:
        yaw += 360.0
    forward = math.sqrt(x * x + y * y)
    pitch = math.degrees(math.atan2(z, forward))
    return (-pitch, yaw, 0.0)



# ── temporal evaluation ────────────────────────────────────────────────────
#
# A demo is 40 Hz. Video is not. Choosing which pose to show at an output time
# is a real decision and it has exactly three honest answers.

SAMPLE_EXACT = "RECORDED_SAMPLE_EXACT"
POV_FAITHFUL = "RECORDED_POV_FAITHFUL"
POV_CINEMATIC = "RECORDED_POV_CINEMATIC"

# Beyond this the bracketing samples are not the same continuous motion, so
# interpolating between them would invent a path. Two snapshots is generous.
MAX_INTERP_GAP_MS = 60

# Angular speed above which a change is a discontinuity rather than a flick.
# The fastest genuine human flick measured in this corpus is 841 deg/s; a
# teleport or a POV switch presents as an instantaneous jump far above that.
MAX_INTERP_RATE_DEG_S = 2000.0


def _short_arc(a: float, b: float) -> float:
    """b - a, taking the short way round. Without this, 359 -> 1 spins 358
    degrees the wrong way in a single frame."""
    return (b - a + 180.0) % 360.0 - 180.0


def _lerp_angles(a, b, f):
    return tuple(a[i] + _short_arc(a[i], b[i]) * f for i in range(3))


def _bracket(truth, t_ms):
    """The observed frames immediately at-or-before and after t_ms."""
    prev = nxt = None
    for fr in truth.frames:
        if fr.server_time_ms <= t_ms:
            prev = fr
        else:
            nxt = fr
            break
    return prev, nxt


def _can_interpolate(prev, nxt, actor_id) -> bool:
    """Is the interval between these two frames one continuous motion?

    Refuses across: an observation gap, an actor missing from either end, a
    teleport, a death, and any angular jump too fast to be a human. Each of
    those is a DISCONTINUITY -- a straight line through it is a path the
    player never took.
    """
    if prev is None or nxt is None:
        return False
    if nxt.server_time_ms - prev.server_time_ms > MAX_INTERP_GAP_MS:
        return False

    a = prev.actors.get(actor_id)
    b = nxt.actors.get(actor_id)
    if a is None or b is None:
        return False                      # UNOBSERVED at one end
    if a.alive != b.alive:
        return False                      # death changes the camera outright

    for fr in (prev, nxt):
        for ev in fr.events:
            kind = ev.kind.split(":", 1)[-1]
            if kind in ("teleport_in", "teleport_out", "death", "obituary"):
                return False

    dt = (nxt.server_time_ms - prev.server_time_ms) / 1000.0
    if dt <= 0:
        return False
    rate = max(abs(_short_arc(a.yaw, b.yaw)), abs(b.pitch - a.pitch)) / dt
    return rate <= MAX_INTERP_RATE_DEG_S


def _evaluate_actor(truth, actor_id, t_ms, intent):
    """(position, yaw, pitch, provenance) for one actor at an output time.

    SAMPLE_EXACT returns the sample at-or-before: no invention at all, but it
    is not what the player saw, and over a 40 Hz source at 30 fps it holds
    some poses and skips others, which reads as judder.

    POV_FAITHFUL interpolates between the bracketing observations -- which is
    precisely what the game client does between snapshots, and what this
    trace's own `authorities` field already records as the intended treatment.
    It is closer to the original view, and it is still DERIVED.
    """
    prev, nxt = _bracket(truth, t_ms)
    if prev is None:
        return None

    a = prev.actors.get(actor_id)
    if a is None:
        return None

    if intent == SAMPLE_EXACT or not _can_interpolate(prev, nxt, actor_id):
        return (a.position, a.yaw, a.pitch, "RECORDED_SAMPLE")

    b = nxt.actors[actor_id]
    span = nxt.server_time_ms - prev.server_time_ms
    f = (t_ms - prev.server_time_ms) / span
    pos = tuple(a.position[i] + (b.position[i] - a.position[i]) * f
                for i in range(3))
    yaw = a.yaw + _short_arc(a.yaw, b.yaw) * f
    pitch = a.pitch + (b.pitch - a.pitch) * f
    return (pos, yaw, pitch, "DERIVED_INTERPOLATED")


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
    # The third-person weapon hanging off tag_weapon. Recorded state; the
    # model is asset knowledge resolved from it.
    weapon_model: str = ""
    alive: bool = True
    # How long each part has been in ITS animation. Legs and torso run
    # independent clocks in the original client, so sharing one made a
    # torso change restart the legs mid-stride.
    legs_anim_ms: int = 0
    torso_anim_ms: int = 0
    # angles2[YAW] 0-7: how far the legs are turned off the view.
    move_dir: int = 0
    # The view pitch. The torso takes 0.75 of it and the legs none,
    # per CG_PlayerAngles; pitching the whole body tips the character.
    view_pitch: float = 0.0


@dataclass
class RenderProjectile:
    """One missile, placed. Derived from recorded trajectory parameters."""
    track_id: str
    weapon: str
    model: str
    origin: Vec3
    angles: Vec3
    provenance: str
    method: str


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
    server_time_ms: int             # SOURCE: the demo's own clock
    frame_index: int
    camera: RenderCamera
    # EDIT: where this frame sits in the output. Kept separate on purpose --
    # an event happens at its source time, and moving it to the nearest
    # convenient output frame would rewrite when it happened.
    edit_time_ms: int = 0
    camera_intent: str = POV_FAITHFUL
    camera_provenance: str = "RECORDED_SAMPLE"
    actors: list[RenderActor] = field(default_factory=list)
    projectiles: list[RenderProjectile] = field(default_factory=list)
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
        d["projectiles"] = [asdict(p) for p in self.projectiles]
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
                     intent: str = POV_FAITHFUL,
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
    source = [(i, f, f.server_time_ms) for i, f in enumerate(truth.frames)]
    if times_ms is not None:
        picked = []
        for t_ms in times_ms:
            chosen = None
            for i, f, _ in source:
                if f.server_time_ms <= t_ms:
                    chosen = (i, f, t_ms)      # keep the OUTPUT time too
                else:
                    break
            if chosen is not None:
                picked.append(chosen)
        source = picked

    frames: list[RenderFrame] = []
    wanted = None if indices is None else set(indices)
    # actor_id -> {'legs': (anim, toggle, started_ms), 'torso': ...}
    anim_since: dict[str, dict[str, tuple[int, bool, int]]] = {}

    for out_index, (i, f, out_t) in enumerate(source):
        if wanted is not None and i not in wanted:
            continue

        cam_prov = "RECORDED_SAMPLE"
        if camera_owner:
            ev = _evaluate_actor(truth, camera_owner, out_t, intent)
            if ev is None:
                # His eyes were not observed here. Skipping is the honest
                # answer; holding the last camera would invent a viewpoint.
                continue
            pos, yaw, pitch, cam_prov = ev
            cam = RenderCamera(
                origin=(pos[0], pos[1], pos[2] + VIEW_HEIGHT),
                angles=(pitch, yaw, 0.0), fov=fov,
                source="RECORDED_POV", owner=camera_owner)
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
            clocks = anim_since.setdefault(actor_id, {})
            for part, num, tog in (("legs", a.legs_anim, a.legs_toggle),
                                   ("torso", a.torso_anim, a.torso_toggle)):
                was = clocks.get(part)
                # A restart is a change of NUMBER **or** of TOGGLE.
                if was is None or was[0] != num or was[1] != tog:
                    clocks[part] = (num, tog, f.server_time_ms)
            # The body is evaluated at the same output instant as the camera,
            # or actor and world drift apart by up to one snapshot.
            _ev = _evaluate_actor(truth, actor_id, out_t, intent)
            _apos, _ayaw = (_ev[0], _ev[1]) if _ev else (a.position, a.yaw)
            actors.append(RenderActor(
                actor_id=actor_id, client=a.client, team=a.team,
                model=getattr(profile, "model", str(profile)),
                skin=getattr(profile, "skin", "default"),
                origin=tuple(float(v) for v in _apos),
                angles=(0.0, float(_ayaw), 0.0),   # a body yaws; it does not pitch
                legs_anim=a.legs_anim, torso_anim=a.torso_anim,
                weapon=a.weapon, alive=a.alive,
                move_dir=a.move_dir, view_pitch=float(a.pitch),
                weapon_model=(weapon_assets(int(a.weapon)).get("hand") or "")
                              if str(a.weapon).lstrip('-').isdigit() else "",
                legs_anim_ms=out_t - clocks["legs"][2],
                torso_anim_ms=out_t - clocks["torso"][2]))

        # A missile has a continuous trajectory, so it is evaluated at the
        # OUTPUT time rather than snapped to the source sample -- otherwise it
        # advances in 25 ms steps while the camera moves smoothly.
        proj_source = f
        if intent != SAMPLE_EXACT:
            _pf = truth.at_server_time(out_t)
            proj_source = _pf if _pf is not None else f

        missiles = []
        for m in getattr(proj_source, "projectiles", []):
            assets = weapon_assets(m.weapon)
            if not assets["missile"]:
                continue          # no model for this weapon: not drawn
            missiles.append(RenderProjectile(
                track_id=m.track_id, weapon=assets["name"],
                model=assets["missile"],
                origin=tuple(round(v, 3) for v in m.position),
                angles=vector_to_angles(m.direction),
                provenance=m.provenance, method=m.method))

        frames.append(RenderFrame(
            map=truth.map_name, server_time_ms=f.server_time_ms,
            frame_index=i, edit_time_ms=out_t,
            camera_intent=intent, camera_provenance=cam_prov,
            camera=cam, actors=actors, projectiles=missiles,
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


def save_shot_script(frames: Sequence[RenderFrame], path: Path,
                     *, lighting: str = "QUAKE_AUTHENTIC") -> Path:
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
        model <md3 path>                          # declared once, in order
        actor <playerIdx> <x y z> <pitch yaw roll> <legs> <torso>
              <legsMs> <torsoMs> <moveDir> <viewPitch> <weaponModelIdx|-1>
        projectile <modelIdx> <x y z> <pitch yaw roll>

    The host treats an unknown keyword as fatal, so this writer and that
    parser cannot drift apart quietly.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Players are declared once and referenced by index, so identity is stated
    # in exactly one place.
    roster: list[tuple[str, str]] = []
    models: list[str] = []          # md3 paths referenced by index
    for f in frames:
        for a in f.actors:
            if (a.model, a.skin) not in roster:
                roster.append((a.model, a.skin))
            if a.weapon_model and a.weapon_model not in models:
                models.append(a.weapon_model)
        for pr in f.projectiles:
            if pr.model not in models:
                models.append(pr.model)

    first = frames[0]
    out = ["# pantheon shot script v1 -- generated from RenderFrame, do not edit",
           "map %s" % first.map,
           "size %d %d" % (first.width, first.height),
           "provenance %s" % (first.provenance or "UNKNOWN"),
           "demo %s" % (first.demo_hash or "UNKNOWN"),
           "lighting %s" % lighting]
    out += ["player %s %s" % (m, sk) for m, sk in roster]
    out += ["model %s" % m for m in models]

    for f in frames:
        c = f.camera
        out.append("frame %d %d %.3f %.3f %.3f %.3f %.3f %.3f %.2f %s" % (
            f.frame_index, f.server_time_ms,
            c.origin[0], c.origin[1], c.origin[2],
            c.angles[0], c.angles[1], c.angles[2], c.fov, f.out))
        for a in f.actors:
            out.append(
                "actor %d %.3f %.3f %.3f %.3f %.3f %.3f %d %d %d %d %d %.3f %d"
                % (roster.index((a.model, a.skin)),
                   a.origin[0], a.origin[1], a.origin[2],
                   a.angles[0], a.angles[1], a.angles[2],
                   a.legs_anim, a.torso_anim,
                   a.legs_anim_ms, a.torso_anim_ms,
                   a.move_dir, a.view_pitch,
                   models.index(a.weapon_model) if a.weapon_model else -1))
        for pr in f.projectiles:
            out.append("projectile %d %.3f %.3f %.3f %.3f %.3f %.3f" % (
                models.index(pr.model),
                pr.origin[0], pr.origin[1], pr.origin[2],
                pr.angles[0], pr.angles[1], pr.angles[2]))

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path
