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



# ── original-client angle swing ────────────────────────────────────────────
#
# CG_PlayerAngles does not point the legs straight at their target. It SWINGS
# them, with per-entity state that persists between frames, and that lag is a
# large part of why a Quake player reads as a body rather than a turret.
#
# This was previously omitted with the reasoning that stateful logic "breaks
# determinism". That reasoning was wrong. A stateful evaluator is perfectly
# deterministic: the same initial state plus the same inputs in the same order
# gives the same result every time. What state costs is RANDOM ACCESS, and the
# answer to that is a checkpoint and a replay -- not a different algorithm.
#
# One honest deviation: the original steps by `cg.frametime`, the client's own
# variable render delta, so its exact output depends on the frame rate the
# player happened to be running. We replay at a fixed canonical step instead.
# The behaviour is the original's; the numbers are not bit-identical to any
# particular historical client run, and could not be.

SWING_STEP_MS = 25          # canonical replay step: the demo's snapshot rate
CHECKPOINT_MS = 500         # bounded: replay never exceeds this much history

# CG_PlayerAngles constants, from the source.
LEGS_SWING_TOLERANCE, LEGS_CLAMP = 40.0, 90.0
TORSO_SWING_TOLERANCE, TORSO_CLAMP = 25.0, 90.0
PITCH_SWING_TOLERANCE, PITCH_CLAMP = 15.0, 30.0
SWING_SPEED = 0.3           # cg_swingSpeed default
PITCH_SPEED = 0.1           # the literal in CG_PlayerAngles

LEGS_IDLE, TORSO_STAND, TORSO_STAND2 = 22, 11, 12
MOVEMENT_OFFSETS = (0, 22, 45, -22, 0, 22, -45, -22)


def _angle_mod(a: float) -> float:
    return a % 360.0


def _angle_subtract(a: float, b: float) -> float:
    """AngleSubtract: the short way round."""
    return (a - b + 180.0) % 360.0 - 180.0


def _swing_angles(destination, swing_tolerance, clamp_tolerance, speed,
                  angle, swinging, frametime_ms):
    """CG_SwingAngles, returning (angle, swinging) instead of mutating."""
    if not swinging:
        swing = _angle_subtract(angle, destination)
        if swing > swing_tolerance or swing < -swing_tolerance:
            swinging = True
    if not swinging:
        return angle, swinging

    swing = _angle_subtract(destination, angle)
    scale = abs(swing)
    if scale < swing_tolerance * 0.5:
        scale = 0.5
    elif scale < swing_tolerance:
        scale = 1.0
    else:
        scale = 2.0

    if swing >= 0:
        move = frametime_ms * scale * speed
        if move >= swing:
            move = swing
            swinging = False
        angle = _angle_mod(angle + move)
    else:
        move = frametime_ms * scale * -speed
        if move <= swing:
            move = swing
            swinging = False
        angle = _angle_mod(angle + move)

    # the clamp: never let a part twist further than this off its target
    swing = _angle_subtract(destination, angle)
    if swing > clamp_tolerance:
        angle = _angle_mod(destination - (clamp_tolerance - 1))
    elif swing < -clamp_tolerance:
        angle = _angle_mod(destination + (clamp_tolerance - 1))
    return angle, swinging


class _Swing:
    """One actor's persistent presentation state. Not game truth."""

    __slots__ = ("legs_yaw", "legs_yawing", "torso_yaw", "torso_yawing",
                 "torso_pitch", "torso_pitching", "t_ms", "started")

    def __init__(self):
        self.legs_yaw = self.torso_yaw = self.torso_pitch = 0.0
        self.legs_yawing = self.torso_yawing = self.torso_pitching = False
        self.t_ms = None
        self.started = False

    def copy(self):
        o = _Swing()
        for f in self.__slots__:
            setattr(o, f, getattr(self, f))
        return o


class PresentationEvaluator:
    """Deterministic, checkpointed replay of the original angle behaviour.

    `pose_at` may be called in any order and returns the same answer for the
    same time, because it always replays forward from a checkpoint at or
    before that time rather than from wherever the last call happened to stop.
    """

    def __init__(self, truth, *, step_ms: int = SWING_STEP_MS,
                 checkpoint_ms: int = CHECKPOINT_MS):
        self.truth = truth
        self.step = step_ms
        self.checkpoint_ms = checkpoint_ms
        self._t0 = truth.frames[0].server_time_ms if truth.frames else 0
        self._checkpoints: dict[str, dict[int, _Swing]] = {}

    def _advance(self, actor_id, st, from_ms, to_ms):
        """Replay the swing forward, one canonical step at a time."""
        t = from_ms
        while t < to_ms:
            nxt = min(t + self.step, to_ms)
            dt = nxt - t
            fr = self.truth.at_server_time(nxt)
            a = fr.actors.get(actor_id) if fr else None
            if a is not None:
                self._step(st, a, dt)
            t = nxt
        st.t_ms = to_ms
        return st

    def _step(self, st, a, dt_ms):
        head_yaw = _angle_mod(a.yaw)
        dir_ = a.move_dir if 0 <= a.move_dir < 8 else 0

        if not st.started:
            # CG_PlayerEntity's first sight of an actor centres him rather
            # than swinging in from zero, which would look like a spin.
            st.legs_yaw = st.torso_yaw = head_yaw
            st.torso_pitch = a.pitch * 0.75
            st.started = True
            return

        # "always center" while moving or acting, straight from the original
        if (a.legs_anim != LEGS_IDLE
                or a.torso_anim not in (TORSO_STAND, TORSO_STAND2)):
            st.legs_yawing = st.torso_yawing = st.torso_pitching = True

        legs_dest = head_yaw + MOVEMENT_OFFSETS[dir_]
        torso_dest = head_yaw + 0.25 * MOVEMENT_OFFSETS[dir_]

        st.torso_yaw, st.torso_yawing = _swing_angles(
            torso_dest, TORSO_SWING_TOLERANCE, TORSO_CLAMP, SWING_SPEED,
            st.torso_yaw, st.torso_yawing, dt_ms)
        st.legs_yaw, st.legs_yawing = _swing_angles(
            legs_dest, LEGS_SWING_TOLERANCE, LEGS_CLAMP, SWING_SPEED,
            st.legs_yaw, st.legs_yawing, dt_ms)

        pitch = a.pitch
        dest = (-360.0 + pitch) * 0.75 if pitch > 180 else pitch * 0.75
        st.torso_pitch, st.torso_pitching = _swing_angles(
            dest, PITCH_SWING_TOLERANCE, PITCH_CLAMP, PITCH_SPEED,
            st.torso_pitch, st.torso_pitching, dt_ms)

    def pose_at(self, actor_id: str, t_ms: int):
        """(legs_yaw, torso_yaw, torso_pitch) at t_ms. Order-independent."""
        marks = self._checkpoints.setdefault(actor_id, {})
        want = self._t0 + ((t_ms - self._t0) // self.checkpoint_ms) * self.checkpoint_ms
        base_ms = max((m for m in marks if m <= want), default=None)

        if base_ms is None:
            st, base_ms = _Swing(), self._t0
        else:
            st = marks[base_ms].copy()

        # fill in checkpoints up to `want` so later seeks are bounded
        while base_ms + self.checkpoint_ms <= want:
            nxt = base_ms + self.checkpoint_ms
            st = self._advance(actor_id, st, base_ms, nxt)
            marks[nxt] = st.copy()
            base_ms = nxt

        st = self._advance(actor_id, st, base_ms, t_ms)
        return st.legs_yaw, st.torso_yaw, st.torso_pitch


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
    # PRESENTATION angles, produced by the swing evaluator. These are what the
    # renderer draws; `angles` above remains the raw recorded view.
    legs_yaw: float = 0.0
    torso_yaw: float = 0.0
    torso_pitch: float = 0.0
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

    swing = PresentationEvaluator(truth)

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
            _lyaw, _tyaw, _tpitch = swing.pose_at(actor_id, out_t)
            actors.append(RenderActor(
                actor_id=actor_id, client=a.client, team=a.team,
                model=getattr(profile, "model", str(profile)),
                skin=getattr(profile, "skin", "default"),
                origin=tuple(float(v) for v in _apos),
                angles=(0.0, float(_ayaw), 0.0),   # a body yaws; it does not pitch
                legs_anim=a.legs_anim, torso_anim=a.torso_anim,
                weapon=a.weapon, alive=a.alive,
                move_dir=a.move_dir, view_pitch=float(a.pitch),
                legs_yaw=_lyaw, torso_yaw=_tyaw, torso_pitch=_tpitch,
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
              <legsMs> <torsoMs> <legsYaw> <torsoYaw> <torsoPitch> <viewPitch>
              <weaponModelIdx|-1>
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
                "actor %d %.3f %.3f %.3f %.3f %.3f %.3f %d %d %d %d "
                "%.3f %.3f %.3f %.3f %d"
                % (roster.index((a.model, a.skin)),
                   a.origin[0], a.origin[1], a.origin[2],
                   a.angles[0], a.angles[1], a.angles[2],
                   a.legs_anim, a.torso_anim,
                   a.legs_anim_ms, a.torso_anim_ms,
                   a.legs_yaw, a.torso_yaw, a.torso_pitch, a.view_pitch,
                   models.index(a.weapon_model) if a.weapon_model else -1))
        for pr in f.projectiles:
            out.append("projectile %d %.3f %.3f %.3f %.3f %.3f %.3f" % (
                models.index(pr.model),
                pr.origin[0], pr.origin[1], pr.origin[2],
                pr.angles[0], pr.angles[1], pr.angles[2]))

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path
