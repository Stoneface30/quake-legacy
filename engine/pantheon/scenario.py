"""PANTHEON RoundScenario — author a Clan Arena round as game intent.

THE LAYER BOUNDARY. Above this line you write what happens: who spawns, who
moves where, who shoots whom, when the round is won. Below it, the compiler
turns that into configstrings, packet entities, animation numbers and
obituary temp-entities. Nothing above this line is allowed to know that
`eType 71` is a death or that `cs 664` is the blue alive count.

WHY THAT BOUNDARY IS LOAD-BEARING AND NOT TIDINESS. The teaching round was
being written as direct writer calls with literal field indices, and the
indices were invented. Both the writer and the tests used the same invented
numbers, so every round-trip passed and the engine drew nothing. A scenario
that cannot name a field index cannot get one wrong.

THE GRAMMAR IS OBSERVED, NOT ASSUMED. Round start, the alive-counter ramp and
the reset sequence are compiled from what real CA rounds actually do -- see
`docs/reference/ca_round_grammar.md` and the extractor that produced it. In
particular the alive counters do NOT start at the roster size: they are driven
to zero and counted up, interleaved between teams, and only then count down.

    scenario = RoundScenario.clan_arena(map_name="campgrounds", nav=nav)
    red1 = scenario.actor("RED_1", Team.RED)
    blue1 = scenario.actor("BLUE_1", Team.BLUE)
    scenario.begin_round(countdown=7.0)
    red1.move_to(nav.route(a, b), start=3.0)
    red1.look_at(blue1)
    red1.fire(Weapon.ROCKET, at=blue1)
    blue1.take_damage(80, source=red1)
    red1.kill(blue1, mod=Weapon.ROCKET)
    scenario.round_win(Team.RED)
    scenario.reset_round()
    scenario.compile().save("ca_explainer_v1.dm_73")
"""
from __future__ import annotations

import math

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence

from engine.parser import dm73_write as _codec

Vec3 = tuple[float, float, float]


class Team(Enum):
    RED = 1
    BLUE = 2

    @property
    def label(self) -> str:
        return self.name


class Weapon(Enum):
    """Weapon slots. The numbers are the game's, not ours -- but a scenario
    refers to them by name."""
    GAUNTLET = 1
    MACHINEGUN = 2
    SHOTGUN = 3
    GRENADE = 4
    ROCKET = 5
    LIGHTNING = 6
    RAIL = 7
    PLASMA = 8


@dataclass(frozen=True)
class MotionProfile:
    """How a body moves, in numbers read off real demos.

    docs/reference/motion_reference_<map>.json is mined by
    engine.pantheon.motion_reference from the corpus. The defaults below are
    the overkill CA figures (3 demos, 23 player tracks, 14k snapshots) and are
    only used when no file is present.
    """
    run_speed: float = 320.0        # units/s, p50 while LEGS_RUN
    accel_ms: float = 125.0         # standing -> 90% run speed, p50
    decel_ms: float = 350.0         # 90% run speed -> stopped, p50
    yaw_rate_running: float = 200.0 # deg/s, p90 while moving
    yaw_rate_standing: float = 120.0  # deg/s, a turn on the spot
    anim_lag_ms: float = 25.0       # legs enter/leave RUN this long after

    @classmethod
    def load(cls, map_name: str | None = None) -> "MotionProfile":
        import json
        from pathlib import Path as _P
        if map_name:
            f = _P(f"docs/reference/motion_reference_{map_name}.json")
            if f.exists():
                d = json.loads(f.read_text(encoding="utf-8"))

                def g(k, q="p50"):
                    return (d.get(k) or {}).get(q)
                return cls(
                    run_speed=g("run_speed") or cls.run_speed,
                    accel_ms=g("accel_to_90pct") or cls.accel_ms,
                    decel_ms=g("decel_to_stop") or cls.decel_ms,
                    yaw_rate_running=g("yaw_rate_running", "p90") or cls.yaw_rate_running,
                    anim_lag_ms=g("legs_run_start_lag") or cls.anim_lag_ms)
        return cls()


def _ease_trapezoid(f: float, ramp_in: float, ramp_out: float) -> float:
    """Distance fraction at time fraction `f`, with linear speed ramps.

    Speed rises over the first `ramp_in` of the interval, holds, and falls
    over the last `ramp_out` -- the shape a player's speed actually has
    between a standing start and a stop, per MotionReference.
    """
    ramp_in = max(1e-6, min(ramp_in, 0.49))
    ramp_out = max(1e-6, min(ramp_out, 0.49))
    area = 1.0 - ramp_in / 2 - ramp_out / 2          # normalising constant
    if f < ramp_in:
        d = f * f / (2 * ramp_in)
    elif f < 1.0 - ramp_out:
        d = ramp_in / 2 + (f - ramp_in)
    else:
        g = 1.0 - f
        d = area - g * g / (2 * ramp_out)
    return max(0.0, min(1.0, d / area))


def _inverse_ease(dist_frac: float, mp: "MotionProfile", span_s: float) -> float:
    """Time fraction at which the eased motion has covered `dist_frac`."""
    ri = (mp.accel_ms / 1000.0) / max(span_s, 1e-6)
    ro = (mp.decel_ms / 1000.0) / max(span_s, 1e-6)
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if _ease_trapezoid(mid, ri, ro) < dist_frac:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _slew(a: float, b: float, max_deg: float) -> float:
    """Turn from yaw a toward yaw b by at most max_deg, the short way."""
    d = (b - a + 180.0) % 360.0 - 180.0
    if abs(d) <= max_deg:
        return b % 360.0
    return (a + max_deg * (1 if d > 0 else -1)) % 360.0


class Layer(Enum):
    """What a body on screen IS.

    HISTORICAL means it happened and the demo says so. ANALYSIS means PANTHEON
    added it to explain, and nobody did it. The two must never merge: the real
    player never walked to camera during the historical match, and no data
    anywhere in this pipeline may imply that he did.
    """
    HISTORICAL = "HISTORICAL"
    ANALYSIS = "ANALYSIS"        # a copy of a historical actor, explaining him
    PRESENTER = "PRESENTER"      # an independent cast character, explaining


class Stance(Enum):
    """What a body is doing. Compiled to real legsAnim/torsoAnim values."""
    IDLE = "idle"
    RUN = "run"
    JUMP = "jump"
    LAND = "land"
    ATTACK = "attack"
    GESTURE = "gesture"
    DEAD = "dead"


# How long the engine itself holds a gesture: TIMER_GESTURE = 34*66+50 ms
# (bg_local.h:35), applied in bg_pmove.c when BUTTON_GESTURE is held. Authoring
# a different duration would desync the pose from what the engine expects.
GESTURE_MS = 2294


# Stance -> the animation numbers real players were observed using.
# `ca_reference` profiled these; the scenario never sees them.
_LEGS = {Stance.IDLE: _codec.LEGS_IDLE, Stance.RUN: _codec.LEGS_RUN,
         Stance.JUMP: _codec.LEGS_JUMP, Stance.LAND: _codec.LEGS_LAND,
         Stance.ATTACK: _codec.LEGS_IDLE, Stance.GESTURE: _codec.LEGS_IDLE,
         Stance.DEAD: _codec.LEGS_IDLE}
_TORSO = {Stance.IDLE: _codec.TORSO_STAND, Stance.RUN: _codec.TORSO_STAND,
          Stance.JUMP: _codec.TORSO_STAND, Stance.LAND: _codec.TORSO_STAND,
          Stance.ATTACK: _codec.TORSO_ATTACK,
          Stance.GESTURE: _codec.TORSO_GESTURE, Stance.DEAD: _codec.TORSO_STAND}

# Structural entity fields every rendered player carries. Observed present in
# 100% of real player samples and never changing. Kept here, once, rather than
# copied into each scenario.
_PLAYER_STRUCTURAL = {17: 1, 24: 1, 28: 4200463}

SNAPSHOT_HZ = 40          # real QL demos: 25ms between snapshots (measured p10=p50=p90=25)
SNAPSHOT_MS = 1000 // SNAPSHOT_HZ


# ── scheduling ──────────────────────────────────────────────────────────────

@dataclass
class _Keyframe:
    t: float                       # seconds from scenario start
    origin: Vec3
    yaw: float
    stance: Stance
    weapon: Weapon
    health: int
    armor: int
    alive: bool
    # A RECORDED sample carries the engine's own numbers, and the compiler
    # emits them verbatim instead of deriving them from `stance`. None means
    # "authored, derive as before".
    legs_anim: int | None = None
    torso_anim: int | None = None
    pitch: float = 0.0
    velocity: Vec3 | None = None
    airborne: bool = False
    weapon_num: int | None = None   # engine slot when it is not in Weapon
    recorded: bool = False


@dataclass
class _RecordedEvent:
    """An EV_* the demo carried, replayed at its tick."""
    t: float
    actor: str
    code: int
    carrier: str                 # PLAYER | TEMP
    weapon: int | None
    parm: int | None
    position: Vec3 | None
    other_entity: int | None


@dataclass
class _ProjectileKey:
    """One observed missile sample, attributed to the actor who fired it."""
    t: float
    actor: str
    entity: int
    weapon: int
    origin: Vec3
    velocity: Vec3


@dataclass
class _Event:
    t: float
    kind: str                      # "kill" | "fire" | "damage"
    actor: str
    target: str | None = None
    weapon: Weapon | None = None
    amount: int = 0
    position: Vec3 | None = None


class Actor:
    """One player in the round. Authored in world terms only."""

    def __init__(self, scenario: "RoundScenario", name: str, team: Team,
                 client: int) -> None:
        self._s = scenario
        self.name = name
        self.team = team
        self.client = client
        self._keys: list[_Keyframe] = []
        self.health = 200
        self.armor = 100
        self.weapon = Weapon.ROCKET
        self.alive = True
        # Appearance is authored INTO the demo's configstring, so the character
        # is correct from the file rather than from a playback-time override.
        # `cg_ignoreClientHeadModel` defaults to 2, which makes the head follow
        # `model` for protocol-QL demos, so this one key covers the whole body.
        self.model = "sarge"
        self.skin = "default"
        # Q3 player colour indices, overridable per actor via `appearance`.
        self.c1, self.c2 = "4", "5"
        # HISTORICAL by default: an actor is something that happened until a
        # caller says otherwise. engine.pantheon.instruction sets ANALYSIS on
        # the bodies PANTHEON adds to explain, and the two never merge.
        self.layer = Layer.HISTORICAL
        # An analysis body is on screen but not in the round; the alive
        # counters must not learn about him.
        self.counts_toward_roster = True
        self._spawned = False
        self._recorded_events: list = []

    # -- state ---------------------------------------------------------
    def spawn(self, at: Vec3, *, yaw: float = 0.0, t: float = 0.0,
              weapon: Weapon = Weapon.ROCKET) -> "Actor":
        self.weapon = weapon
        self._keys.append(_Keyframe(t, at, yaw, Stance.IDLE, weapon,
                                    self.health, self.armor, True))
        # The roster is counted as actors spawn, not at compile time. Counting
        # it later made every authored kill decrement from zero, so the
        # timeline read -1, -2, -3 instead of 3, 2, 1.
        if self.counts_toward_roster:
            self._s._alive[self.team] += 1
        return self

    def perform(self, trace, *, t0: float = 0.0,
                offset: Vec3 = (0.0, 0.0, 0.0), yaw_offset: float = 0.0
                ) -> "Actor":
        """Play a PerformanceTrace: the recorded samples BECOME the keyframes.

        Nothing is eased, snapped or derived. Every snapshot the demo carried
        for the real player -- origin, velocity, yaw, pitch, legs and torso
        animation, weapon, ground state -- is written as one keyframe on this
        actor's timeline, and the compiler emits those numbers as they are.
        The demo is the animation system.

        `offset`/`yaw_offset` are LOCAL_FRAME retargeting; (0,0,0)/0 is
        EXACT_WORLD. Timing is never scaled.
        """
        base = trace.start_ms
        anims = {a.t: a for a in trace.animation}
        weap = sorted(trace.weapon, key=lambda w: w.t)

        def weapon_at(t):
            w = None
            for x in weap:
                if x.t <= t:
                    w = x.weapon
            return w

        cy, sy = math.cos(math.radians(yaw_offset)), math.sin(math.radians(yaw_offset))

        def place(o):
            x, y = o[0] * cy - o[1] * sy, o[0] * sy + o[1] * cy
            return (x + offset[0], y + offset[1], o[2] + offset[2])

        def turn(v):
            return (v[0] * cy - v[1] * sy, v[0] * sy + v[1] * cy, v[2])

        aim = {a.t: a for a in trace.aim}
        for smp in trace.transform:
            a = anims.get(smp.t)
            am = aim.get(smp.t)
            wn = weapon_at(smp.t)
            try:
                wp = Weapon(wn) if wn is not None else self.weapon
            except ValueError:
                wp = self.weapon
            # rounded to the millisecond: 0.6 + 1.1 is 1.7000000000000002 in
            # a double, which sits past the 40Hz frame at 1.7 and hands the
            # interpolator the PREVIOUS sample's yaw and velocity
            k = _Keyframe(round(t0 + (smp.t - base) / 1000.0, 3), place(smp.origin),
                          ((am.yaw if am else 0.0) + yaw_offset) % 360.0,
                          Stance.RUN if smp.speed > 50 else Stance.IDLE,
                          wp, self.health, self.armor, True,
                          legs_anim=a.legs if a else None,
                          torso_anim=a.torso if a else None,
                          pitch=am.pitch if am else 0.0,
                          velocity=turn(smp.velocity), airborne=smp.airborne,
                          weapon_num=wn, recorded=True)
            self._keys.append(k)
        if not any(k.t == t0 for k in self._keys) and self._keys:
            pass
        self._s._alive[self.team] += 1 if self.counts_toward_roster and not self._spawned else 0
        self._spawned = True
        # the projectiles the real player fired travel with him
        for pr in trace.projectiles:
            self._s._projectiles.append(_ProjectileKey(
                t0 + (pr.t - base) / 1000.0, self.name, pr.entity, pr.weapon,
                place(pr.origin), turn(pr.velocity)))
        # THE EVENT CHAIN, verbatim. Player-carried events (jump pad, fire,
        # pain, death) go on this actor's entity at their tick; temp-entity
        # events (impacts, obituary) get their own entity. cgame turns them
        # into the smoke puff, muzzle flash, explosion and every sound -- so
        # emitting the right codes IS the effects and IS the audio.
        for ev in trace.events:
            if ev.code is None:
                continue
            pos = (place(ev.position) if ev.position and None not in ev.position
                   else None)
            self._recorded_events.append(_RecordedEvent(
                round(t0 + (ev.t - base) / 1000.0, 3), self.name, ev.code,
                ev.carrier, ev.weapon, ev.parm, pos, ev.other_entity))
        return self

    def arm(self, weapon: Weapon, *, t: float | None = None) -> "Actor":
        """Change weapon deliberately, at a time the audience can see."""
        last = self._last()
        when = last.t if t is None else t
        self.weapon = weapon
        self._keys.append(_Keyframe(when, last.origin, last.yaw, Stance.IDLE,
                                    weapon, last.health, last.armor, True))
        return self

    def appearance(self, model: str, skin: str = "default", *,
                   c1: str | None = None, c2: str | None = None) -> "Actor":
        """Which character this actor IS, baked into the demo.

        `keel` / `bright` is a real shipped skin -- every one of the 26 player
        models has an `icon_bright`, and wolfcam's own `cg_enemyModel` defaults
        to `keel/bright`.
        """
        self.model, self.skin = model, skin
        if c1 is not None:
            self.c1 = c1
        if c2 is not None:
            self.c2 = c2
        return self

    def gesture(self, *, t: float | None = None) -> "Actor":
        """The greeting/taunt animation. TORSO_GESTURE, held for the engine's
        own TIMER_GESTURE, then back to standing."""
        last = self._last()
        when = last.t if t is None else t
        self._keys.append(_Keyframe(when, last.origin, last.yaw, Stance.GESTURE,
                                    last.weapon, last.health, last.armor, True))
        self._keys.append(_Keyframe(when + GESTURE_MS / 1000.0, last.origin,
                                    last.yaw, Stance.IDLE, last.weapon,
                                    last.health, last.armor, True))
        return self

    def stand(self, *, until: float) -> "Actor":
        """Hold the current position and pose until `until`."""
        last = self._last()
        self._keys.append(_Keyframe(until, last.origin, last.yaw, Stance.IDLE,
                                    last.weapon, last.health, last.armor,
                                    last.alive))
        return self

    def move_to(self, path: Sequence[Vec3], *,
                during: tuple[float, float] | None = None,
                start: float | None = None, speed: float | None = None,
                yaw: float | None = None) -> "Actor":
        """Run a route. `path` comes from NavigationTruth -- never literals.

        TIMING COMES FROM DISTANCE, NOT FROM THE AUTHOR. A real player covers
        ground at ~320 units/s (MotionReference, mined). Give `start` and the
        arrival time follows; give `during` and the implied speed is checked
        against the measured one, because a body run-animating at a third of
        run speed is the thing that read as "sliding" on the cast sheet.

        Keyframe times follow cumulative path distance, eased with the
        measured accel/decel ramps, instead of a constant lerp.
        """
        if len(path) < 2:
            raise ValueError("a route needs at least two points")
        mp = self._s.motion
        length = sum(math.dist(path[i], path[i + 1]) for i in range(len(path) - 1))
        v = speed or mp.run_speed
        if during is None:
            if start is None:
                start = self._last().t
            t0 = start
            t1 = start + length / v + (mp.accel_ms + mp.decel_ms) / 2000.0
        else:
            t0, t1 = during
            if t1 <= t0:
                raise ValueError(f"{self.name}: move window must advance ({during})")
            implied = length / (t1 - t0)
            if not 0.6 * v <= implied <= 1.25 * v:
                raise ValueError(
                    f"{self.name}: {length:.0f} units in {t1 - t0:.2f}s is "
                    f"{implied:.0f} units/s; real players run at ~{v:.0f}. "
                    f"Pass start= and let the distance set the time.")
        last = self._last()
        n = len(path) - 1
        cum = [0.0]
        for i in range(n):
            cum.append(cum[-1] + math.dist(path[i], path[i + 1]))
        for i, point in enumerate(path):
            frac = cum[i] / length if length else 0.0
            t = t0 + (t1 - t0) * _inverse_ease(frac, mp, t1 - t0)
            heading = yaw if yaw is not None else _heading(
                path[max(0, i - 1)], path[min(n, i + 1)])
            # A keyframe's stance governs the segment AFTER it (_at reads
            # a.stance). IDLE on the first point made the actor slide to the
            # second, and RUN on the last made him run on the spot after
            # arriving -- seen live on the cast sheet. So: RUN on every point
            # he leaves from, IDLE on the one he arrives at.
            stance = Stance.RUN if i < n else Stance.IDLE
            self._keys.append(_Keyframe(t, point, heading, stance, last.weapon,
                                        last.health, last.armor, True))
        # settle: stop running the moment the route ends
        end = path[-1]
        self._keys.append(_Keyframe(t1 + 0.05, end,
                                    yaw if yaw is not None else self._last().yaw,
                                    Stance.IDLE, last.weapon, last.health,
                                    last.armor, True))
        return self

    def look_at_point(self, where: Vec3, *, t: float | None = None) -> "Actor":
        """Turn to face a position -- the camera, a door, a jump pad."""
        last = self._last()
        when = last.t if t is None else t
        self._keys.append(_Keyframe(when, last.origin, _heading(last.origin,
                                                                where),
                                    last.stance, last.weapon, last.health,
                                    last.armor, last.alive))
        return self

    def despawn(self, *, t: float) -> "Actor":
        """Leave the world. Used by the analysis layer, which must not be
        standing in the frame when historical time resumes."""
        last = self._last()
        self._keys.append(_Keyframe(t, last.origin, last.yaw, Stance.DEAD,
                                    last.weapon, last.health, last.armor,
                                    False))
        return self

    def look_at(self, other: "Actor", *, t: float | None = None) -> "Actor":
        last = self._last()
        when = last.t if t is None else t
        target = other._at(when)
        self._keys.append(_Keyframe(when, last.origin,
                                    _heading(last.origin, target.origin),
                                    last.stance, last.weapon, last.health,
                                    last.armor, last.alive))
        return self

    # -- combat --------------------------------------------------------
    def fire(self, weapon: Weapon, *, at: "Actor | None" = None,
             impact: Vec3 | None = None, t: float | None = None) -> "Actor":
        """Fire. `impact` is where the shot LANDS -- a wall, not a player.

        A rail needs an end point to draw between, and a documentary shot that
        wants a clean trail against geometry has no victim to aim at.
        """
        last = self._last()
        when = last.t if t is None else t
        aim = impact or (at._at(when).origin if at else None)
        yaw = _heading(last.origin, aim) if aim else last.yaw
        # THE ACTOR MUST ALREADY BE HOLDING IT. Silently assigning the weapon
        # here meant an actor who spawned with the rocket launcher was still
        # holding it on the frame before the shot and holding a railgun on the
        # frame of the shot -- a weapon swap and a shot on the same tick, which
        # reads on screen as a glitch. Arm the actor, or spawn him armed.
        if last.weapon is not weapon:
            raise ValueError(
                f"{self.name} fires {weapon.name} at t={when:g}s while holding "
                f"{last.weapon.name}. Spawn with weapon={weapon.name} or call "
                f"arm({weapon.name}) before the shot, so the swap is authored "
                f"and visible rather than happening on the firing frame.")
        self._keys.append(_Keyframe(when, last.origin, yaw, Stance.ATTACK,
                                    weapon, last.health, last.armor, True))
        self._keys.append(_Keyframe(when + 0.35, last.origin, yaw, Stance.IDLE,
                                    weapon, last.health, last.armor, True))
        self._s._events.append(_Event(when, "fire", self.name,
                                      at.name if at else None, weapon,
                                      position=aim))
        return self

    def take_damage(self, amount: int, *, source: "Actor | None" = None,
                    t: float | None = None) -> "Actor":
        last = self._last()
        when = last.t if t is None else t
        armor = max(0, last.armor - amount // 2)
        health = max(1, last.health - (amount - (last.armor - armor)))
        self.health, self.armor = health, armor
        self._keys.append(_Keyframe(when, last.origin, last.yaw, last.stance,
                                    last.weapon, health, armor, True))
        self._s._events.append(_Event(when, "damage", source.name if source
                                      else self.name, self.name, None, amount))
        return self

    def kill(self, victim: "Actor", *, mod: Weapon, t: float | None = None
             ) -> "Actor":
        when = self._last().t if t is None else t
        victim._die(when)
        self._s._events.append(_Event(when, "kill", self.name, victim.name, mod,
                                      position=victim._at(when).origin))
        self._s._alive[victim.team] -= 1
        self._s._alive_log.append((when, dict(self._s._alive)))
        return self

    def credit_kill(self, victim: "Actor", *, t: float | None = None) -> "Actor":
        """Count a kill the demo already carries as a recorded obituary.

        The obituary temp entity is replayed verbatim by perform(); authoring
        a second one through kill() put two obituaries in the synthetic demo.
        This updates the round (alive counters, the victim's state) and emits
        nothing.
        """
        when = self._last().t if t is None else t
        victim._die(when)
        self._s._alive[victim.team] -= 1
        self._s._alive_log.append((when, dict(self._s._alive)))
        return self

    def _die(self, t: float) -> None:
        self.alive = False
        if any(k.recorded for k in self._keys):
            # A RECORDED actor already carries his death: the demo kept
            # sending his body with the death animation, and the trace has
            # those samples. Authoring a DEAD key here removed the corpse the
            # real demo still shows and shadowed every recorded sample after
            # it. The obituary event is enough.
            return
        last = self._last()
        self._keys.append(_Keyframe(t, last.origin, last.yaw, Stance.DEAD,
                                    last.weapon, 0, 0, False))

    # -- internals -----------------------------------------------------
    def _last(self) -> _Keyframe:
        if not self._keys:
            raise RuntimeError(f"{self.name} has not spawned")
        return self._keys[-1]

    def _at(self, t: float) -> _Keyframe:
        """Interpolated state at `t`. Position lerps; pose does not."""
        keys = sorted(self._keys, key=lambda k: k.t)
        first = keys[0]
        if t < first.t:
            # NOT YET SPAWNED. Returning the first key here made every actor
            # exist from t=0: the cast sheet stacked twelve characters on one
            # mark, and a presenter authored to walk in mid-freeze was already
            # standing in the fight from the first frame.
            return _Keyframe(t, first.origin, first.yaw, Stance.DEAD,
                             first.weapon, first.health, first.armor, False)
        if t == first.t:
            return first
        for a, b in zip(keys, keys[1:]):
            if a.t <= t <= b.t:
                span = b.t - a.t
                f = 0.0 if span <= 0 else (t - a.t) / span
                origin = tuple(a.origin[i] + (b.origin[i] - a.origin[i]) * f
                               for i in range(3))
                if a.recorded:
                    # between two recorded snapshots the CLIENT interpolates
                    # position linearly; everything else holds the earlier
                    # sample, exactly as cgame does. ON a sample it is that
                    # sample: returning a's yaw at b's time lagged every
                    # recorded aim by one snapshot while position was exact.
                    if f >= 1.0 - 1e-9:
                        return b
                    k = _Keyframe(t, origin, a.yaw, a.stance, a.weapon,
                                  a.health, a.armor, a.alive,
                                  legs_anim=a.legs_anim, torso_anim=a.torso_anim,
                                  pitch=a.pitch, velocity=a.velocity,
                                  airborne=a.airborne, weapon_num=a.weapon_num,
                                  recorded=True)
                    return k
                mp = self._s.motion
                moving = a.stance is Stance.RUN
                rate = mp.yaw_rate_running if moving else mp.yaw_rate_standing
                yaw = _slew(a.yaw, b.yaw, rate * max(0.0, t - a.t))
                return _Keyframe(t, origin, yaw,
                                 a.stance, a.weapon, a.health, a.armor, a.alive)
        return keys[-1]


def _heading(a: Vec3, b: Vec3) -> float:
    import math
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360


# ── the scenario ────────────────────────────────────────────────────────────

class RoundScenario:
    """A Clan Arena round, authored as intent and compiled to a demo."""

    def __init__(self, *, map_name: str, hostname: str, roster: int = 4) -> None:
        self.map_name = map_name
        self.hostname = hostname
        self.motion = MotionProfile.load(map_name)
        self._projectiles: list[_ProjectileKey] = []
        self.roster = roster
        self.actors: dict[str, Actor] = {}
        self._events: list[_Event] = []
        self._alive = {Team.RED: 0, Team.BLUE: 0}
        self._alive_log: list[tuple[float, dict]] = []
        self._round_begin: float | None = None
        self._countdown = 7.0
        self._win: tuple[float, Team] | None = None
        self._reset_at: float | None = None
        self.camera: Actor | None = None
        self._camera_path: list[_Keyframe] = []

    @classmethod
    def clan_arena(cls, *, map_name: str, hostname: str = "PANTHEON EXPLAINER",
                   roster: int = 4) -> "RoundScenario":
        return cls(map_name=map_name, hostname=hostname, roster=roster)

    # -- authoring -----------------------------------------------------
    observer_team = Team.RED
    observer_name = "POV"

    def actor(self, name: str, team: Team) -> Actor:
        if name in self.actors:
            return self.actors[name]
        client = len(self.actors) + 1          # client 0 is the camera
        a = Actor(self, name, team, client)
        self.actors[name] = a
        return a

    def observer(self, at: Vec3, *, yaw: float = 0.0,
                 team: Team = Team.RED, name: str = "POV") -> None:
        """The demo's own viewpoint. A recorded demo always has one.

        THE POV NEEDS A TEAM, and for a long time it did not have one. Every
        "is this shooter my teammate or my enemy" decision in cgame reads
        cgs.clientinfo[povClientNum], which is populated from the CS_PLAYERS
        configstring for that slot. Client 0 had no such configstring, so it
        had no team, so neither cg_teamRailColor* nor cg_enemyRailColor* ever
        applied -- and a colour proof measured four different values rendering
        the same colour, because none of them was being consulted at all.
        """
        self.observer_team = team
        self.observer_name = name
        self._camera_path = [_Keyframe(0.0, at, yaw, Stance.IDLE,
                                       Weapon.ROCKET, 200, 100, True)]

    def camera_move(self, points: Sequence[Vec3], *,
                    during: tuple[float, float], look_at: Vec3 | None = None,
                    pitch: float = 0.0) -> None:
        """Move the point of view along `points` over `during`.

        Keyframed like an actor: the compiler interpolates position between
        consecutive points. `look_at` fixes the yaw on one world point for the
        whole move, which is what an orbit needs; without it the camera looks
        along its own path.
        """
        if len(points) < 1:
            raise ValueError("camera_move needs at least one point")
        t0, t1 = during
        if t1 < t0:
            raise ValueError(f"camera move window must advance ({during})")
        n = max(1, len(points) - 1)
        for i, pt in enumerate(points):
            t = t0 + (t1 - t0) * i / n
            if look_at is not None:
                yaw = _heading(pt, look_at)
            elif i < n:
                yaw = _heading(pt, points[i + 1])
            else:
                yaw = self._camera_path[-1].yaw if self._camera_path else 0.0
            k = _Keyframe(t, pt, yaw, Stance.IDLE, Weapon.ROCKET, 200, 100, True)
            k.pitch = pitch
            self._camera_path.append(k)

    def camera_hold(self, *, until: float) -> None:
        last = self._camera_path[-1]
        k = _Keyframe(until, last.origin, last.yaw, Stance.IDLE, Weapon.ROCKET,
                      200, 100, True)
        k.pitch = getattr(last, "pitch", 0.0)
        self._camera_path.append(k)

    def follow(self, actor: "Actor", *, t0: float, t1: float,
               eye: float = 46.0) -> None:
        """First-person: the point of view IS this actor, from t0 to t1.

        The camera keys are copied from the actor's own, lifted to eye height.
        Nothing about the actor changes -- the camera reads him, it does not
        move him.
        """
        for k in sorted(actor._keys, key=lambda k: k.t):
            if t0 <= k.t <= t1:
                o = (k.origin[0], k.origin[1], k.origin[2] + eye)
                c = _Keyframe(k.t, o, k.yaw, Stance.IDLE, Weapon.ROCKET,
                              200, 100, True)
                c.pitch = 0.0
                self._camera_path.append(c)

    def camera_at(self, t: float) -> _Keyframe:
        """Interpolated camera state at `t`. Position lerps; yaw snaps at
        the midpoint like actors do; pitch lerps."""
        keys = sorted(self._camera_path, key=lambda k: k.t)
        if t <= keys[0].t:
            return keys[0]
        for a, b in zip(keys, keys[1:]):
            if a.t <= t <= b.t:
                span = b.t - a.t
                f = 0.0 if span <= 0 else (t - a.t) / span
                o = tuple(a.origin[i] + (b.origin[i] - a.origin[i]) * f
                          for i in range(3))
                k = _Keyframe(t, o, a.yaw if f < 0.5 else b.yaw, a.stance,
                              a.weapon, a.health, a.armor, a.alive)
                pa, pb = getattr(a, "pitch", 0.0), getattr(b, "pitch", 0.0)
                k.pitch = pa + (pb - pa) * f
                return k
        return keys[-1]

    def begin_round(self, *, at: float = 1.0, countdown: float = 7.0) -> None:
        self._round_begin = at
        self._countdown = countdown

    def round_win(self, team: Team, *, t: float) -> None:
        self._win = (t, team)

    def reset_round(self, *, t: float) -> None:
        self._reset_at = t

    # -- compilation ---------------------------------------------------
    def compile(self, *, duration: float | None = None) -> _codec.DemoWriter:
        from engine.pantheon.compiler import compile_scenario
        return compile_scenario(self, duration=duration)

    def timeline(self) -> list[dict]:
        """The authored semantics, for the real-vs-synthetic differential."""
        out: list[dict] = []
        if self._round_begin is not None:
            out.append({"t": self._round_begin - self._countdown,
                        "feature": "round_announced"})
            out.append({"t": self._round_begin, "feature": "round_active"})
        for t, alive in self._alive_log:
            out.append({"t": t, "feature": "alive_change",
                        "red": alive[Team.RED], "blue": alive[Team.BLUE]})
        for e in self._events:
            out.append({"t": e.t, "feature": e.kind, "actor": e.actor,
                        "target": e.target,
                        "weapon": e.weapon.name if e.weapon else None})
        if self._win:
            out.append({"t": self._win[0], "feature": "round_win",
                        "team": self._win[1].label})
        if self._reset_at is not None:
            out.append({"t": self._reset_at, "feature": "round_reset"})
        return sorted(out, key=lambda r: r["t"])
