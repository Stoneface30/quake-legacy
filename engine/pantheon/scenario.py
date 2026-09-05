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
    red1.move_to(nav.route(a, b), during=(3.0, 6.0))
    red1.look_at(blue1)
    red1.fire(Weapon.ROCKET, at=blue1)
    blue1.take_damage(80, source=red1)
    red1.kill(blue1, mod=Weapon.ROCKET)
    scenario.round_win(Team.RED)
    scenario.reset_round()
    scenario.compile().save("ca_explainer_v1.dm_73")
"""
from __future__ import annotations

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

SNAPSHOT_HZ = 20
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

    # -- state ---------------------------------------------------------
    def spawn(self, at: Vec3, *, yaw: float = 0.0, t: float = 0.0,
              weapon: Weapon = Weapon.ROCKET) -> "Actor":
        self.weapon = weapon
        self._keys.append(_Keyframe(t, at, yaw, Stance.IDLE, weapon,
                                    self.health, self.armor, True))
        # The roster is counted as actors spawn, not at compile time. Counting
        # it later made every authored kill decrement from zero, so the
        # timeline read -1, -2, -3 instead of 3, 2, 1.
        self._s._alive[self.team] += 1
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

    def move_to(self, path: Sequence[Vec3], *, during: tuple[float, float],
                yaw: float | None = None) -> "Actor":
        """Walk a route. `path` comes from NavigationTruth -- never literals.

        Emitting a keyframe per path point rather than only the endpoints is
        what lets the compiler interpolate along real navigable geometry
        instead of cutting a straight line through a wall.
        """
        if len(path) < 2:
            raise ValueError("a route needs at least two points")
        t0, t1 = during
        if t1 <= t0:
            raise ValueError(f"{self.name}: move window must advance ({during})")
        last = self._last()
        n = len(path) - 1
        for i, point in enumerate(path):
            t = t0 + (t1 - t0) * i / n
            heading = yaw if yaw is not None else _heading(
                path[max(0, i - 1)], path[min(n, i + 1)])
            stance = Stance.IDLE if i == 0 else Stance.RUN
            self._keys.append(_Keyframe(t, point, heading, stance, last.weapon,
                                        last.health, last.armor, True))
        # settle: stop running the moment the route ends
        end = path[-1]
        self._keys.append(_Keyframe(t1 + 0.05, end,
                                    yaw if yaw is not None else self._last().yaw,
                                    Stance.IDLE, last.weapon, last.health,
                                    last.armor, True))
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
             t: float | None = None) -> "Actor":
        last = self._last()
        when = last.t if t is None else t
        yaw = _heading(last.origin, at._at(when).origin) if at else last.yaw
        self.weapon = weapon
        self._keys.append(_Keyframe(when, last.origin, yaw, Stance.ATTACK,
                                    weapon, last.health, last.armor, True))
        self._keys.append(_Keyframe(when + 0.35, last.origin, yaw, Stance.IDLE,
                                    weapon, last.health, last.armor, True))
        self._s._events.append(_Event(when, "fire", self.name,
                                      at.name if at else None, weapon))
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

    def _die(self, t: float) -> None:
        last = self._last()
        self.alive = False
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
        if t <= keys[0].t:
            return keys[0]
        for a, b in zip(keys, keys[1:]):
            if a.t <= t <= b.t:
                span = b.t - a.t
                f = 0.0 if span <= 0 else (t - a.t) / span
                origin = tuple(a.origin[i] + (b.origin[i] - a.origin[i]) * f
                               for i in range(3))
                return _Keyframe(t, origin, a.yaw if f < 0.5 else b.yaw,
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
    def actor(self, name: str, team: Team) -> Actor:
        if name in self.actors:
            return self.actors[name]
        client = len(self.actors) + 1          # client 0 is the camera
        a = Actor(self, name, team, client)
        self.actors[name] = a
        return a

    def observer(self, at: Vec3, *, yaw: float = 0.0) -> None:
        """The demo's own viewpoint. A recorded demo always has one."""
        self._camera_path = [_Keyframe(0.0, at, yaw, Stance.IDLE,
                                       Weapon.ROCKET, 200, 100, True)]

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
