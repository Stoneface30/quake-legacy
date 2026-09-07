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
import math
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
class ProjectileTruth:
    """One missile at one instant.

    THE RECORDED FIELD IS NOT A POSITION. `origin` in a ProjectileSample is
    `pos.trBase` -- the trajectory's base point, which for a Q3 missile is set
    once at spawn and never changes. Three consecutive snapshots 25 ms apart
    reporting the identical value at ~1000 u/s is the giveaway. The missile's
    actual position is `trBase + trDelta * (t - trTime) / 1000`, and `trTime`
    is not in the demo rows at all.

    So a projectile is renderable only when its launch time can be established
    from something recorded -- the EV_FIRE_WEAPON that spawned it. Where that
    is missing the trajectory is UNDERIVABLE and the missile is not drawn,
    because a straight line through two trBase values is not an observation.
    """
    track_id: str
    entity: int
    weapon: int
    owner_client: int | None
    position: Vec3                  # evaluated, not recorded
    direction: Vec3                 # unit trDelta
    speed: float
    launch_ms: int
    provenance: str                 # DERIVED | RECORDED
    method: str


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
    kind: str                       # fire | damage | kill | round_win | recorded:<ev>
    actor: str | None = None
    target: str | None = None
    weapon: str | None = None
    amount: int = 0
    position: Vec3 | None = None
    # SOUND IS GAME STATE, not a renderer afterthought. Where Quake emits a
    # sound for an event, the intent is named here in game terms; a backend
    # decides which sample, which mix, which reverb.
    sound: str | None = None


# kind (authored or recorded, prefix stripped) -> sound intent. Weapon-bearing
# kinds are formatted with the weapon name.
SOUND_INTENT = {
    "fire": "weapon.fire.{weapon}",
    "fire_weapon": "weapon.fire.{weapon}",
    "jump_pad": "world.jump_pad",
    "jump": "player.jump",
    "missile_hit": "impact.{weapon}",
    "missile_miss": "impact.{weapon}.world",
    "railtrail": "weapon.rail.trail",
    "pain": "player.pain",
    "death": "player.death",
    "kill": "player.death",
    "obituary": "player.death",
    "gib_player": "player.gib",
    "drown": "player.drown",
    "teleport_in": "world.teleport.in",
    "teleport_out": "world.teleport.out",
    "change_weapon": "weapon.change",
    "item_pickup": "item.pickup",
    "noammo": "weapon.noammo",
}



def _missile_segments(trace: dict) -> list[dict]:
    """Recover trajectory segments from a trace's projectile samples.

    THE AUTHORITY IS pos.trTime, AND IT IS IN THE DEMO. An earlier version of
    this function inferred the launch from the nearest EV_FIRE_WEAPON because
    the parser did not read trTime. That inference was wrong by a systematic
    +50 ms on every rocket in this fixture -- a residual of one server frame is
    supporting evidence, never proof. trTime is now parsed (entityState field
    0) and used; the fire-event inference survives only as a fallback for older
    traces, and anything built on it is marked PROVISIONAL.

    SEGMENTATION IS BY trTime, NOT BY trBase. Entity slots are reused: slot 206
    in this fixture holds two different missiles, and grouping by trBase merged
    them into one impossible flight. Two trTimes means two missiles.

    trBase, meanwhile, can be RE-BASED mid-flight while trTime stays put. Those
    later bases are treated as VALIDATION of the spawn trajectory -- they match
    it to a few units -- and never as new origins, because pairing a re-based
    trBase with the original trTime evaluates to nonsense.
    """
    LAUNCH_TOLERANCE_MS = 50
    MAX_RESIDUAL_MS = 100        # four snapshots

    by_key: dict[tuple, list[dict]] = {}
    for smp in trace.get("projectiles", []):
        # trTime is the missile's identity. Without it, fall back to the entity
        # slot and accept that reuse cannot be told apart.
        key = (smp["entity"], smp.get("tr_time"))
        by_key.setdefault(key, []).append(smp)

    fires = [e for e in trace.get("events", [])
             if e.get("kind") == "fire_weapon" and e.get("weapon") is not None]

    segments: list[dict] = []
    for (entity, tr_time), samples in by_key.items():
        samples.sort(key=lambda x: x["t"])
        head = samples[0]

        if tr_time is not None:
            launch, launch_src = tr_time, "RECORDED_TRTIME"
        else:
            launch, launch_src = None, "PROVISIONAL_FIRE_EVENT"
            for e in fires:
                if (e["weapon"] == head["weapon"]
                        and abs(e["t"] - head["t"]) <= LAUNCH_TOLERANCE_MS):
                    launch = e["t"]
                    break

        tr_type = head.get("tr_type")
        base, delta = tuple(head["origin"]), tuple(head["velocity"])
        speed = math.sqrt(sum(v * v for v in delta)) or 1.0

        # Every re-based observation should agree with the spawn trajectory.
        residual = None
        if launch is not None:
            # A re-based trBase is only meaningful at the snapshot where it
            # was FIRST sent; the snapshots after it merely repeat the value
            # unchanged. Comparing those repeats against the trajectory at
            # their own later times inflates the residual by the distance the
            # missile travelled in the meantime.
            worst = 0.0
            seen_other = False
            prev = base
            for smp in samples[1:]:
                cur = tuple(smp["origin"])
                if cur == prev:
                    continue                    # unchanged: no new evidence
                prev = cur
                seen_other = True
                pred = _trajectory_at(base, delta, launch, tr_type, smp["t"])
                if pred is None:
                    continue
                worst = max(worst, max(abs(pred[i] - cur[i]) for i in range(3)))
            residual = worst if seen_other else None
        residual_ms = None if residual is None else residual / speed * 1000.0

        valid = (launch is not None
                 and _trajectory_at(base, delta, launch, tr_type, launch) is not None
                 and (residual_ms is None or residual_ms <= MAX_RESIDUAL_MS))

        segments.append({
            "valid": valid,
            "residual_ms": residual_ms,
            "entity": entity,
            "weapon": head["weapon"],
            "owner": trace.get("client"),
            "base": tuple(float(v) for v in base),
            "delta": tuple(float(v) for v in delta),
            "tr_type": tr_type,
            "launch_ms": launch,
            "launch_source": launch_src,
            "first_seen_ms": head["t"],
            "last_seen_ms": samples[-1]["t"],
        })
    return segments


# bg_public.h trType_t. Only the kinds a missile actually uses are supported;
# anything else is refused rather than approximated with the wrong physics.
TR_STATIONARY, TR_INTERPOLATE, TR_LINEAR, TR_LINEAR_STOP, TR_SINE, TR_GRAVITY = range(6)
DEFAULT_GRAVITY = 800.0


def _trajectory_at(base, delta, tr_time, tr_type, t_ms):
    """BG_EvaluateTrajectory, for the kinds a missile uses.

    A rocket is TR_LINEAR; a grenade is TR_GRAVITY and falls. Evaluating a
    grenade linearly would fly it straight through the ceiling, which is why
    trType is consulted rather than assumed.
    """
    dt = (t_ms - tr_time) / 1000.0
    if tr_type in (None, TR_LINEAR, TR_LINEAR_STOP):
        return tuple(base[i] + delta[i] * dt for i in range(3))
    if tr_type == TR_GRAVITY:
        pos = [base[i] + delta[i] * dt for i in range(3)]
        pos[2] -= 0.5 * DEFAULT_GRAVITY * dt * dt
        return tuple(pos)
    if tr_type == TR_STATIONARY:
        return tuple(base)
    return None                      # TR_SINE / TR_INTERPOLATE: not a missile


def _evaluate_missile(seg: dict, t_ms: int) -> ProjectileTruth | None:
    """The missile at one instant, or nothing.

    Outside [launch, last observed] it is not drawn. After the last snapshot
    that saw it we do not know it still exists -- it very likely exploded, but
    "likely" is not a render input.
    """
    launch = seg["launch_ms"]
    if launch is None or not seg.get("valid"):
        return None
    if t_ms < launch or t_ms > seg["last_seen_ms"]:
        return None

    pos = _trajectory_at(seg["base"], seg["delta"], launch,
                         seg.get("tr_type"), t_ms)
    if pos is None:
        return None

    delta = seg["delta"]
    speed = math.sqrt(sum(d * d for d in delta))

    # A body under gravity points along its CURRENT velocity, not its launch
    # velocity, or a falling grenade keeps pointing at the sky.
    if seg.get("tr_type") == TR_GRAVITY:
        dt = (t_ms - launch) / 1000.0
        vel = (delta[0], delta[1], delta[2] - DEFAULT_GRAVITY * dt)
    else:
        vel = delta
    vmag = math.sqrt(sum(v * v for v in vel)) or 1.0
    unit = tuple(v / vmag for v in vel)

    provenance = ("DERIVED" if seg["launch_source"] == "RECORDED_TRTIME"
                  else "DERIVED_PROVISIONAL")
    method = "BG_EvaluateTrajectory(trType=%s, trBase, trDelta, trTime=%s)" % (
        seg.get("tr_type"), seg["launch_source"])

    return ProjectileTruth(
        track_id="P:%d:%d" % (seg["entity"], launch),
        entity=seg["entity"], weapon=seg["weapon"],
        owner_client=seg["owner"], position=pos, direction=unit,
        speed=speed, launch_ms=launch, provenance=provenance, method=method)


def sound_intent(kind: str, weapon: str | None) -> str | None:
    base = kind.split(":", 1)[1] if kind.startswith("recorded:") else kind
    fmt = SOUND_INTENT.get(base)
    if fmt is None:
        return None
    if "{weapon}" in fmt:
        return fmt.format(weapon=weapon or "UNKNOWN")
    return fmt


@dataclass
class Frame:
    t: float
    server_time_ms: int
    actors: dict[str, ActorTruth]
    round_state: RoundStateTruth
    events: list[SemanticEvent] = field(default_factory=list)
    camera: dict[str, Any] | None = None
    projectiles: list[ProjectileTruth] = field(default_factory=list)


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
                 "camera": f.camera,
                 "projectiles": [asdict(pr) for pr in f.projectiles]}
                for f in self.frames],
        }

    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=1), encoding="utf-8")
        return path

    # -- construction --------------------------------------------------
    @classmethod
    def from_traces(cls, traces: Sequence[dict], *,
                    names: dict[int, str] | None = None,
                    teams: dict[int, str] | None = None) -> "FrameTruth":
        """Build FrameTruth from RECORDED PerformanceTraces.

        `from_scenario` samples something we authored. This samples what the
        demo actually contained, so the provenance is RECORDED_TRACE and the
        serverTime is the demo's own -- not re-based to a synthetic origin.
        That distinction is the whole point: a renderer fed a re-timed
        explainer is not rendering history.

        Each trace is a PerformanceTrace as saved to JSON, carrying `transform`,
        `aim` and `animation` tracks that share a sample clock.

        NOTHING IS INTERPOLATED. A sample is taken at-or-before the frame's
        serverTime, exactly as `at()` does, and a trace that does not cover an
        instant contributes no actor there rather than a guessed one -- the
        UNOBSERVED rule (HL-6), applied at the point the renderer would
        otherwise be handed a plausible fiction.
        """
        if not traces:
            raise ValueError("from_traces: no traces")

        maps = {t["map"] for t in traces}
        if len(maps) != 1:
            raise ValueError("from_traces: traces disagree on the map: %s" % maps)

        # Every distinct serverTime any trace observed, in order.
        segments = [(tr, seg) for tr in traces for seg in _missile_segments(tr)]

        stamps = sorted({s["t"] for tr in traces for s in tr["transform"]})
        if not stamps:
            raise ValueError("from_traces: no transform samples")
        base_ms = stamps[0]

        deltas = sorted(b - a for a, b in zip(stamps, stamps[1:]))
        step = deltas[len(deltas) // 2] if deltas else 25
        hz = int(round(1000.0 / step)) if step else 40

        def at_or_before(track: list[dict], t_ms: int) -> dict | None:
            found = None
            for s in track:
                if s["t"] <= t_ms:
                    found = s
                else:
                    break
            return found

        ft = cls(map_name=maps.pop(), snapshot_hz=hz,
                 provenance="RECORDED_TRACE")

        for t_ms in stamps:
            actors: dict[str, ActorTruth] = {}
            for tr in traces:
                client = tr["client"]
                if not (tr["start_ms"] <= t_ms <= tr["end_ms"]):
                    continue                      # UNOBSERVED: contribute nothing
                xf = at_or_before(tr["transform"], t_ms)
                if xf is None:
                    continue
                aim = at_or_before(tr.get("aim", []), t_ms) or {}
                anim = at_or_before(tr.get("animation", []), t_ms) or {}
                wpn = at_or_before(tr.get("weapon", []), t_ms) or {}

                # A death observed at or before this instant ends the actor.
                dead = any(e.get("kind") in ("obituary", "death")
                           and e.get("t", 0) <= t_ms
                           and e.get("other_client") == client
                           for e in tr.get("events", []))

                actor_id = (names or {}).get(client, "CLIENT_%d" % client)
                actors[actor_id] = ActorTruth(
                    actor_id=actor_id, client=client,
                    team=(teams or {}).get(client, "UNKNOWN"),
                    position=tuple(float(v) for v in xf["origin"]),
                    yaw=float(aim.get("yaw", 0.0)),
                    pitch=float(aim.get("pitch", 0.0)),
                    velocity=tuple(float(v) for v in xf.get("velocity",
                                                            (0.0, 0.0, 0.0))),
                    weapon=str(wpn.get("weapon", "UNKNOWN")),
                    alive=not dead,
                    legs_anim=int(anim.get("legs", 0)),
                    torso_anim=int(anim.get("torso", 0)))

            events = [SemanticEvent(
                          t=(e["t"] - base_ms) / 1000.0,
                          server_time_ms=e["t"],
                          kind="recorded:" + e.get("kind", "unknown"),
                          actor=(names or {}).get(tr["client"]),
                          weapon=str(e.get("weapon")) if e.get("weapon") is not None else None,
                          position=tuple(e["position"]) if e.get("position") else None,
                          sound=sound_intent("recorded:" + e.get("kind", ""),
                                             str(e.get("weapon"))))
                      for tr in traces for e in tr.get("events", [])
                      if e.get("t") == t_ms]

            missiles = [m for m in (_evaluate_missile(seg, t_ms)
                                    for _tr, seg in segments) if m]

            ft.frames.append(Frame(
                t=(t_ms - base_ms) / 1000.0,
                server_time_ms=t_ms,
                actors=actors,
                projectiles=missiles,
                round_state=RoundStateTruth(
                    phase="active", round_number=1,
                    alive_red=sum(1 for a in actors.values() if a.alive),
                    alive_blue=0),
                events=events))
        return ft

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
        from engine.pantheon.scenario import Weapon
        for e in scn._events:
            tick = int(round(e.t * SNAPSHOT_HZ))
            weapon = e.weapon.name if e.weapon else None
            wn = getattr(e, "weapon_num", None)
            if weapon is None and wn is not None:
                try:
                    weapon = Weapon(int(wn)).name
                except ValueError:
                    weapon = f"WP_{wn}"
            buckets.setdefault(tick, []).append(SemanticEvent(
                t=e.t, server_time_ms=base_ms + tick * SNAPSHOT_MS,
                kind=e.kind, actor=e.actor, target=e.target,
                weapon=weapon, amount=e.amount, position=e.position,
                sound=sound_intent(e.kind, weapon)))
        # recorded EV_* replayed verbatim by perform(): the cue sheet names
        # them in game terms with their sound intent
        from engine.parser.demo_parse import _EV_NAMES
        for a in scn.actors.values():
            for re_ in getattr(a, "_recorded_events", []):
                tick = int(round(re_.t * SNAPSHOT_HZ))
                name = _EV_NAMES.get(re_.code, f"ev_{re_.code}")
                weapon = None
                if re_.weapon is not None:
                    try:
                        weapon = Weapon(int(re_.weapon)).name
                    except ValueError:
                        weapon = f"WP_{re_.weapon}"
                buckets.setdefault(tick, []).append(SemanticEvent(
                    t=re_.t, server_time_ms=base_ms + tick * SNAPSHOT_MS,
                    kind=f"recorded:{name}", actor=a.name, weapon=weapon,
                    amount=re_.parm or 0, position=re_.position,
                    sound=sound_intent(name, weapon)))
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
                # A RECORDED sample carries the engine's own pose; the stance
                # tables are the fallback for authored keys only.
                legs = k.legs_anim if getattr(k, "legs_anim", None) is not None                     else _LEGS[k.stance]
                torso = k.torso_anim if getattr(k, "torso_anim", None) is not None                     else _TORSO[k.stance]
                vel = tuple(round(v, 3) for v in (k.velocity or (0.0, 0.0, 0.0)))
                actors[a.name] = ActorTruth(
                    actor_id=a.name, client=a.client, team=a.team.label,
                    position=tuple(round(v, 3) for v in k.origin),
                    yaw=round(k.yaw, 2), pitch=round(getattr(k, "pitch", 0.0), 2),
                    velocity=vel, health=k.health, armor=k.armor,
                    weapon=k.weapon.name, alive=k.stance is not Stance.DEAD and k.alive,
                    legs_anim=legs, torso_anim=torso)

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
