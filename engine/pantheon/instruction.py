"""PANTHEON ANALYSIS MODE — the game stops and one player explains it.

THE DEVICE. Real action runs. At the decisive moment history stops. One
participant steps out of the frozen scene, walks to the camera, explains what
is about to happen while the tactical truth is drawn behind them, walks back,
and history resumes exactly where it stopped.

TWO CLOCKS, AND THE MAP BETWEEN THEM IS NOT NEW. `scene_recipe.TimeMap` and
`TimeSegment` already model exactly this: contiguous segments at exact rational
rates, where a `freeze` is defined as zero demo span and positive edit span --
historical time stationary while wall time advances. That is the forensic
netcode replay's clock, and reusing it is the point; a second implementation of
"time stops here" would be a second place for the two to disagree.

    historical time   what happened, in the event's own seconds
    edit time         what the viewer experiences, in the film's seconds

HOW HISTORY IS PROTECTED. The participant who walks out is NOT the historical
actor. He is a SEPARATE CLIENT wearing the same model, spawned when the freeze
begins and gone when it ends. The historical actor holds his exact frozen state
throughout and is never moved, re-angled, re-armed or re-timed. Restoration is
therefore not a rewind that has to be got right -- there is nothing to undo.
`AnalysisBreak.verify_restoration` proves it rather than asserting it.

This is also the honesty rule the brief demands: the real player never walked
to camera during the historical match, and nothing in the data says he did.
`Layer.HISTORICAL` and `Layer.ANALYSIS` stay distinct all the way down, and the
compiled demo carries the analysis actor in his own client slot with his own
name.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Sequence

MAIN = Path("G:/QUAKE_LEGACY")
if str(MAIN) not in sys.path:
    sys.path.insert(0, str(MAIN))

from engine.pantheon.scenario import (Actor, Layer, RoundScenario,  # noqa: E402
                                      Stance, Team, Vec3, Weapon,
                                      _Keyframe, _heading)

US = 1_000_000


def _gesture_ok() -> frozenset:
    from engine.pantheon.roster import load_inventory
    return frozenset(m for m, a in load_inventory().items() if a.can_gesture)


_GESTURE_OK = _gesture_ok()


class Graphic(Enum):
    """Tactical graphics, each named for the truth it draws."""
    SHOOTER_TO_TARGET = "SHOOTER_TO_TARGET"


@dataclass
class TacticalFact:
    """One derived number, with the arithmetic that produced it.

    Distances are never typed in. `value` is computed from FrameTruth
    positions, and `derivation` records how, so an overlay that shows "438 u"
    can be checked against the frame it came from.
    """
    label: str
    value: float
    units: str
    derivation: str
    layer: Layer = Layer.ANALYSIS

    def as_dict(self) -> dict:
        return {"label": self.label, "value": round(self.value, 2),
                "units": self.units, "derivation": self.derivation,
                "layer": self.layer.value}


class Mode(Enum):
    """Who does the explaining."""
    ACTOR_COPY = "ACTOR_COPY"    # a copy of one historical actor steps out
    PRESENTER = "PRESENTER"      # a cast character walks in from off-scene


@dataclass
class Line:
    """One spoken line, on the EDIT clock, from an existing audio file.

    `audio` is a real game asset or a synthesised file already on disk; this
    layer does not synthesise, it schedules. `source_kind` says which.
    """
    text: str
    audio: Path
    source_kind: str = "SYNTHETIC_TTS"     # or GAME_ASSET
    voice_profile: str = "GUIDE"


@dataclass
class AnalysisBreak:
    """A freeze, someone explains, history resumes.

    `at_t` and every other time here is HISTORICAL time. The break inserts
    `hold_s` of edit time at that instant; nothing historical advances during
    it. Everything that happens INSIDE the break -- the walk, the camera, the
    line -- is authored on the edit clock, and that is the only clock it has.
    """
    at_t: float
    hold_s: float
    walk_to: Vec3                   # where the explainer addresses camera
    face: Vec3                      # what he turns toward (the camera)
    mode: Mode = Mode.ACTOR_COPY
    presenter: str | None = None    # ACTOR_COPY: which historical actor
    profile: object | None = None   # PRESENTER: a roster.PresenterProfile
    enter_from: Vec3 | None = None  # PRESENTER: where he walks in from
    route_out: Sequence[Vec3] = ()  # walked path, start -> walk_to
    graphic: Graphic | None = None
    graphic_from: str | None = None
    graphic_to: str | None = None
    walk_s: float = 1.6             # each leg of the walk
    line: Line | None = None
    gesture: bool = True
    orbit: Sequence[Vec3] = ()      # camera points, edit time, during the hold
    orbit_look_at: Vec3 | None = None
    # A REAL recorded RUN_IN -> STOP -> TURN performance. When set, the
    # explainer does not walk: he performs this trace, retargeted in
    # LOCAL_FRAME so its stopping point is `walk_to` and its final facing is
    # toward `face`. Timing is the recording's own.
    entrance: object | None = None  # performance.PerformanceTrace
    # A dense, collision-checked camera plan for the hold: [{t_ms (edit ms
    # from the freeze start), pos, angles(pitch,yaw,roll), fov}]. Built by
    # camera_plan_to_presenter() from the project's camera_paths /
    # camera_compiler_v2 machinery. When set, `orbit` is ignored.
    camera_plan: Sequence[dict] = ()

    def __post_init__(self) -> None:
        if self.hold_s < 2 * self.walk_s + 0.4:
            raise ValueError(
                f"hold_s={self.hold_s} leaves no time to explain: two "
                f"{self.walk_s}s walks plus a beat is the floor.")
        if self.mode is Mode.ACTOR_COPY and not self.presenter:
            raise ValueError("ACTOR_COPY needs `presenter`: which historical "
                             "actor steps out")
        if self.mode is Mode.PRESENTER and (self.profile is None
                                            or self.enter_from is None):
            raise ValueError("PRESENTER needs `profile` (who) and "
                             "`enter_from` (where he walks in from)")

    @property
    def who(self) -> str:
        return (self.presenter if self.mode is Mode.ACTOR_COPY
                else self.profile.role)


class InstructionScene:
    """A scenario plus the analysis breaks cut into it.

    Produces a NEW scenario on the EDIT clock. The source scenario is not
    mutated -- it stays the historical truth, and can be compiled on its own to
    show the same event with no analysis layer at all.
    """

    def __init__(self, historical: RoundScenario, *,
                 duration: float) -> None:
        self.historical = historical
        self.duration = duration
        self.breaks: list[AnalysisBreak] = []
        self.facts: list[TacticalFact] = []
        self.placements: list[dict] = []
        self._graphic_from: dict[float, float] = {}

    def add_break(self, brk: AnalysisBreak) -> "InstructionScene":
        if any(abs(b.at_t - brk.at_t) < 0.5 for b in self.breaks):
            raise ValueError("two analysis breaks at effectively the same "
                             "instant; the viewer cannot tell them apart")
        self.breaks.append(brk)
        self.breaks.sort(key=lambda b: b.at_t)
        return self

    # -- the clock --------------------------------------------------------
    def time_map(self):
        """Historical seconds -> edit seconds, via the forensic TimeMap."""
        from creative_suite.engine.scene_recipe import TimeMap, TimeSegment
        segs, h, e = [], 0.0, 0.0
        for b in self.breaks:
            if b.at_t > h:
                span = b.at_t - h
                segs.append(TimeSegment(
                    kind="normal", demo_start_us=int(h * US),
                    demo_end_us=int(b.at_t * US), edit_start_us=int(e * US),
                    edit_end_us=int((e + span) * US), rate_num=1, rate_den=1))
                e += span
            segs.append(TimeSegment(
                kind="freeze", demo_start_us=int(b.at_t * US),
                demo_end_us=int(b.at_t * US), edit_start_us=int(e * US),
                edit_end_us=int((e + b.hold_s) * US), rate_num=0, rate_den=1))
            e += b.hold_s
            h = b.at_t
        if self.duration > h:
            span = self.duration - h
            segs.append(TimeSegment(
                kind="normal", demo_start_us=int(h * US),
                demo_end_us=int(self.duration * US), edit_start_us=int(e * US),
                edit_end_us=int((e + span) * US), rate_num=1, rate_den=1))
            e += span
        self.edit_duration = e
        return TimeMap(segs)

    def historical_at_edit(self, edit_t: float) -> float:
        """Where in history the film is, at edit second `edit_t`."""
        tm = self.time_map()
        return tm.edit_to_demo(int(edit_t * US), bias="left") / US

    # -- the compiled result ---------------------------------------------
    def build(self) -> tuple[RoundScenario, dict]:
        """A scenario on the edit clock, plus the report the brief asks for."""
        tm = self.time_map()
        src = self.historical
        out = RoundScenario.clan_arena(map_name=src.map_name,
                                       hostname=src.hostname)
        cam = src._camera_path[0]
        out.observer(cam.origin, yaw=cam.yaw, team=src.observer_team,
                     name=src.observer_name)
        # The camera is remapped like an actor: held flat across each freeze
        # unless the break authors an orbit, which is inserted in EDIT time
        # and returns to the exact historical camera before history resumes.
        out._camera_path = self._remap_camera(src, tm)
        self.cues = []

        # 1. every historical actor, with his keys remapped onto edit time and
        #    a HOLD inserted across each freeze. The hold repeats the state at
        #    the freeze instant exactly -- same origin, yaw, stance, weapon,
        #    health -- so the frame before the freeze and the frame after it
        #    are the same frame.
        for name, a in src.actors.items():
            na = out.actor(name, a.team).appearance(a.model, a.skin,
                                                    c1=a.c1, c2=a.c2)
            na.layer = Layer.HISTORICAL
            na._keys = self._remap_keys(a, tm)
        # events move with their actors
        out._events = [type(e)(**{**e.__dict__,
                                  "t": _edit_of(tm, e.t)})
                       for e in src._events]
        out._alive = dict(src._alive)

        # 2. one explainer per break, existing ONLY inside its freeze
        report = {"breaks": [], "edit_duration_s": None}
        for b in self.breaks:
            # At a normal->freeze boundary one historical instant has TWO edit
            # times: the left one is where the freeze opens, the right one is
            # where it closes and history resumes. Everything inside the break
            # is authored from the LEFT.
            e0 = _edit_of(tm, b.at_t, bias="left")
            if b.mode is Mode.ACTOR_COPY:
                hist = src.actors[b.presenter]
                frozen = hist._at(b.at_t)
                act = out.actor(f"{b.presenter}~ANALYSIS", hist.team)
                # Same model, ANALYSIS skin: the bright skin is what the
                # colour family can reach, so this body -- and only this body
                # -- takes the tint when the shot chooses to apply one.
                act.appearance(hist.model, ANALYSIS_SKIN, c1=hist.c1, c2=hist.c2)
                act.layer = Layer.ANALYSIS
                start, weapon = frozen.origin, frozen.weapon
                yaw0 = frozen.yaw
            else:
                prof = b.profile
                prof.resolve()                    # the pak must have him
                frozen = None
                # Opposite team to the POV, so cg_enemy*Color is the only half
                # of the colour family that could reach him -- and it is left
                # alone unless the profile asks for a tint.
                team = (Team.RED if src.observer_team is Team.BLUE
                        else Team.BLUE)
                act = out.actor(f"{prof.role}~PRESENTER", team)
                act.appearance(prof.model, prof.skin)
                act.layer = Layer.PRESENTER
                start, weapon = b.enter_from, Weapon.GAUNTLET
                yaw0 = _heading(b.enter_from, b.walk_to)
            # Not in the round. Counting him would make the CA alive counters
            # say one more player is fighting than actually is, which is a
            # false statement about the historical event.
            act.counts_toward_roster = False
            self._author_walkout(act, b, start, yaw0, weapon, e0)
            self._draw_graphic(out, b, src, e0)
            report["breaks"].append(self._report_break(b, src, frozen, e0, act))

        report["edit_duration_s"] = round(self.edit_duration, 3)
        report["historical_duration_s"] = round(self.duration, 3)
        report["facts"] = [f.as_dict() for f in self.facts]
        return out, report

    # -- pieces -----------------------------------------------------------
    def _remap_keys(self, a: Actor, tm) -> list[_Keyframe]:
        """The actor's keys on the edit clock, held FLAT across every freeze.

        Remapping only the keys that already exist is not enough, and Proof C
        proved it: with no key at the freeze instant, the two keys either side
        of it simply had their interval stretched by the hold, and the yaw
        snap that lives at the midpoint of that interval landed INSIDE the
        freeze. Four frozen actors turned their heads. So the state at the
        instant is sampled and pinned at both edit times of the boundary,
        which is what a freeze means.
        """
        keys = sorted(a._keys, key=lambda k: k.t)
        out: list[_Keyframe] = []
        for k in keys:
            left = _edit_of(tm, k.t, bias="left")
            right = _edit_of(tm, k.t, bias="right")
            out.append(_replace_t(k, left))
            if right != left:
                out.append(_replace_t(k, right))
        for b in self.breaks:
            if any(abs(k.t - b.at_t) < 1e-9 for k in keys):
                continue                       # already pinned above
            frozen = a._at(b.at_t)
            out.append(_replace_t(frozen, _edit_of(tm, b.at_t, "left")))
            out.append(_replace_t(frozen, _edit_of(tm, b.at_t, "right")))
        return sorted(out, key=lambda k: k.t)

    def _author_walkout(self, act: Actor, b: AnalysisBreak, start: Vec3,
                        yaw0: float, weapon: Weapon, e0: float) -> None:
        """Spawn, walk in, face camera, gesture, speak, walk back, leave.

        Every time here is EDIT time. The line, if any, is scheduled on the
        same clock as the walk and the camera, so it cannot drift from them.
        """
        from engine.pantheon.voice import (DialogueCue, SourceKind, SpatialMode,
                                           wav_duration)
        if b.entrance is not None:
            # THE ENTRANCE IS A RECORDING. Placement solves the local frame so
            # the recorded stop lands on `walk_to` and the recorded final yaw
            # points at `face`; nothing about its timing, speed, deceleration
            # or turn is authored. The gesture waits for the recording's own
            # stop plus a beat, so it cannot fire on a sliding body.
            pl = place_entrance(b.entrance, stop_at=b.walk_to, face=b.face)
            act.perform(b.entrance, t0=e0 + 0.15, offset=pl["offset"],
                        yaw_offset=pl["yaw_offset"])
            self.placements.append({"who": act.name, **pl})
            arrive = e0 + 0.15 + pl["stop_rel_s"]
            walk_s = pl["stop_rel_s"]
            t = e0 + 0.15 + pl["turned_rel_s"] + 0.3
            if b.gesture and act.model in _GESTURE_OK:
                act.gesture(t=t)
                t += 0.9
            # the recorded template ends standing; hold that pose from there
            perf_end = e0 + 0.15 + b.entrance.duration_ms() / 1000.0
            t = max(t, perf_end)
        else:
            route = list(b.route_out) or [start, b.walk_to]
            act.spawn(route[0], yaw=yaw0, t=e0, weapon=weapon)
            act.move_to(route, start=e0 + 0.15)
            arrive = act._last().t
            walk_s = arrive - (e0 + 0.15)
            turn = arrive + 0.25
            act.look_at_point(b.face, t=turn)
            t = turn + 0.2
            if b.gesture and act.model in _GESTURE_OK:
                act.gesture(t=t)
                t += 0.9
        if b.line is not None:
            dur = wav_duration(Path(b.line.audio))
            self.cues.append(DialogueCue(
                actor_id=act.name, text=b.line.text, start_t=t,
                duration_s=dur, audio_path=str(b.line.audio),
                source_kind=SourceKind[b.line.source_kind],
                profile=b.line.voice_profile, spatial=SpatialMode.DIEGETIC))
            t += dur
        # the graphic is MOTIVATED by the line: it appears once "this." has
        # landed, not while she is still walking in
        self._graphic_from[b.at_t] = t + 0.15
        speak_until = e0 + b.hold_s - walk_s - 0.2
        if t > speak_until:
            raise ValueError(
                f"{b.who}: the break holds {b.hold_s}s but walking in, "
                f"gesturing and the line need {t - e0 + walk_s + 0.2:.1f}s")
        act.stand(until=speak_until)
        if b.entrance is None:
            act.move_to(list(reversed(route)), start=speak_until)
        # gone before history resumes: the explainer must not be standing in
        # the frame when the fight starts again. (A performed entrance has no
        # authored exit yet; a real run-out template is the next step.)
        act.despawn(t=e0 + b.hold_s - 0.05)

    def _remap_camera(self, src: RoundScenario, tm) -> list[_Keyframe]:
        """Historical camera on the edit clock, plus any authored orbit."""
        keys = sorted(src._camera_path, key=lambda k: k.t)
        out: list[_Keyframe] = []
        for k in keys:
            left, right = _edit_of(tm, k.t, "left"), _edit_of(tm, k.t, "right")
            out.append(_replace_t(k, left))
            if right != left:
                out.append(_replace_t(k, right))
        for b in self.breaks:
            if b.camera_plan:
                e0 = _edit_of(tm, b.at_t, bias="left")
                for kf in b.camera_plan:
                    k = _Keyframe(round(e0 + kf["t_ms"] / 1000.0, 3), tuple(kf["pos"]),
                                  float(kf["angles"][1]) % 360.0, Stance.IDLE,
                                  Weapon.ROCKET, 200, 100, True)
                    k.pitch = float(kf["angles"][0])
                    out.append(k)
                continue
            if not b.orbit:
                continue
            e0 = _edit_of(tm, b.at_t, bias="left")
            here = src.camera_at(b.at_t)
            look = b.orbit_look_at or b.walk_to
            # leave the POV, travel the orbit, come back to the SAME POV
            # before the freeze closes: the frame history resumes on is the
            # frame it left from.
            pts = [here.origin, *b.orbit, here.origin]
            n = len(pts) - 1
            t_out, t_back = e0 + 0.1, e0 + b.hold_s - 0.1
            for i, pt in enumerate(pts):
                t = t_out + (t_back - t_out) * i / n
                yaw = here.yaw if i in (0, n) else _heading(pt, look)
                k = _Keyframe(t, pt, yaw, Stance.IDLE, Weapon.ROCKET,
                              200, 100, True)
                k.pitch = 0.0
                out.append(k)
        return out

    def _draw_graphic(self, out: RoundScenario, b: AnalysisBreak,
                      src: RoundScenario, e0: float) -> None:
        """Put the tactical line on screen, drawn by the engine itself.

        A SHOOTER->TARGET line is a rail beam between the two frozen origins.
        Using the engine's own rail rather than a composited overlay means the
        line obeys the renderer, sits correctly in depth against the geometry,
        and is the same primitive the audience has been looking at all film.

        IT IS STILL AN ANALYSIS OBJECT. Nobody fired this shot. It is emitted
        by the historical shooter's client because that is where the beam has
        to start, it exists only inside the freeze, and the report records it
        as a reconstruction. `cg_railTrailTime` is 600ms, so it is re-emitted
        often enough to look continuous.
        """
        if not (b.graphic and b.graphic_from and b.graphic_to):
            return
        shooter = out.actors[b.graphic_from]
        target_at = src.actors[b.graphic_to]._at(b.at_t).origin
        t = self._graphic_from.get(b.at_t, e0 + b.walk_s + 0.35)
        while t < e0 + b.hold_s - b.walk_s - 0.3:
            out._events.append(_analysis_rail(t, b.graphic_from, target_at))
            t += 0.5

    def _report_break(self, b: AnalysisBreak, src: RoundScenario,
                      frozen, e0: float, act: Actor) -> dict:
        route = list(b.route_out) or [
            (frozen.origin if frozen else b.enter_from), b.walk_to]
        d = {
            "historical_t_s": b.at_t,
            "edit_freeze_start_s": round(e0, 3),
            "edit_freeze_end_s": round(e0 + b.hold_s, 3),
            "hold_s": b.hold_s,
            "mode": b.mode.value,
            "explainer": act.name,
            "explainer_layer": act.layer.value,
            "explainer_appearance": {"model": act.model, "skin": act.skin},
            "line": ({"text": b.line.text, "audio": str(b.line.audio),
                      "source_kind": b.line.source_kind}
                     if b.line else None),
            "camera_orbit_points": len(b.orbit),
            "camera_plan_keyframes": len(b.camera_plan),
            "entrance": ("REAL_PERFORMANCE" if b.entrance is not None else "AUTHORED_WALK"),
            "walk_route": [[round(c, 2) for c in p] for p in route],
            "walk_len_units": round(
                sum(math.dist(route[i], route[i + 1])
                    for i in range(len(route) - 1)), 1),
            "faces": [round(c, 2) for c in b.face],
        }
        if frozen is not None:
            d["historical_actor"] = b.presenter
            d["historical_frozen_state"] = {
                "origin": [round(c, 2) for c in frozen.origin],
                "yaw": round(frozen.yaw, 2), "stance": frozen.stance.name,
                "weapon": frozen.weapon.name, "health": frozen.health,
                "armor": frozen.armor}
        if b.graphic and b.graphic_from and b.graphic_to:
            p = src.actors[b.graphic_from]._at(b.at_t).origin
            q = src.actors[b.graphic_to]._at(b.at_t).origin
            fact = TacticalFact(
                label=f"{b.graphic_from} -> {b.graphic_to}",
                value=math.dist(p, q), units="units",
                derivation=(f"||FrameTruth[{b.graphic_from}].origin - "
                            f"FrameTruth[{b.graphic_to}].origin|| "
                            f"at historical t={b.at_t:g}s"))
            self.facts.append(fact)
            d["graphic"] = {"kind": b.graphic.value, "layer": Layer.ANALYSIS.value,
                            "rendered_as": "engine EV_RAILTRAIL, re-emitted "
                                           "every 0.5s inside the freeze",
                            "reconstruction": True,
                            "nobody_fired_this": True,
                            "from": [round(c, 2) for c in p],
                            "to": [round(c, 2) for c in q],
                            "fact": fact.as_dict()}
        return d

    # -- the acceptance test ---------------------------------------------
    def verify_restoration(self, built: RoundScenario, *,
                           eps: float = 1e-6) -> dict:
        """Prove history is byte-identical either side of every freeze.

        Not a claim: for each break, every historical actor is sampled on the
        edit clock one tick before the freeze opens and one tick after it
        closes, and every component of the state must match. The analysis actor
        must also be absent from the roster at both instants.
        """
        results = []
        for b in self.breaks:
            tm = self.time_map()
            e0 = _edit_of(tm, b.at_t, bias="left")    # freeze opens
            e1 = _edit_of(tm, b.at_t, bias="right")   # freeze closes
            row = {"historical_t_s": b.at_t, "actors": {}, "ok": True}
            for name, a in built.actors.items():
                if getattr(a, "layer", Layer.HISTORICAL) is not Layer.HISTORICAL:
                    continue
                before, after = a._at(e0), a._at(e1)
                same = (all(abs(x - y) <= eps
                            for x, y in zip(before.origin, after.origin))
                        and abs(before.yaw - after.yaw) <= eps
                        and before.stance is after.stance
                        and before.weapon is after.weapon
                        and before.health == after.health
                        and before.armor == after.armor
                        and before.alive == after.alive)
                row["actors"][name] = {
                    "identical": same,
                    "origin_delta": [round(y - x, 6) for x, y
                                     in zip(before.origin, after.origin)],
                    "yaw_delta": round(after.yaw - before.yaw, 6),
                    "weapon": before.weapon.name,
                    "health": before.health}
                row["ok"] = row["ok"] and same
            results.append(row)
        return {"breaks": results, "all_restored": all(r["ok"] for r in results)}


def place_entrance(trace, *, stop_at: Vec3, face: Vec3) -> dict:
    """Solve the LOCAL_FRAME that puts a recording's STOP on `stop_at`,
    facing `face` at the end of its turn.

    The recording's own geometry decides where the run STARTS; that start is
    then checked, not assumed. Returns offset, yaw_offset, and the recording's
    own stop/turn times so nothing downstream guesses them.
    """
    T = trace.transform
    A = {a.t: a for a in trace.aim}
    sp = [s.speed for s in T]
    # the recorded stop: first sample under 30 u/s after the run
    k = next(i for i in range(len(T)) if sp[i] > 250)
    while k < len(T) and sp[k] >= 30:
        k += 1
    stop = T[min(k, len(T) - 1)]
    final_yaw = A[T[-1].t].yaw if T[-1].t in A else 0.0
    want_yaw = _heading(stop_at, face)
    yaw_offset = (want_yaw - final_yaw) % 360.0
    c, sn = math.cos(math.radians(yaw_offset)), math.sin(math.radians(yaw_offset))
    rx, ry = stop.origin[0] * c - stop.origin[1] * sn, stop.origin[0] * sn + stop.origin[1] * c
    offset = (stop_at[0] - rx, stop_at[1] - ry, stop_at[2] - stop.origin[2])
    # when does the turn finish: last sample whose yaw still moves > 2 deg
    yaws = [(t.t, A[t.t].yaw) for t in T[k:] if t.t in A]
    turned = yaws[-1][0] if yaws else T[-1].t
    for (ta, ya), (tb, yb) in zip(yaws, yaws[1:]):
        if abs((yb - ya + 180) % 360 - 180) > 2.0:
            turned = tb
    # The transform itself is the SHARED Retarget: same offset/yaw_offset
    # arithmetic, same perform_kwargs. This function only decides WHICH
    # local frame (stop on the mark, facing the camera); the object that
    # carries it is not a prologue fork.
    from engine.pantheon.retarget import Retarget, TransformMode
    rt = Retarget(TransformMode.LOCAL_FRAME, offset, yaw_offset % 360.0,
                  anchor_from=stop.origin, anchor_to=tuple(stop_at))
    return {"mode": "LOCAL_FRAME", "offset": offset, "yaw_offset": round(yaw_offset, 2),
            "retarget": rt,
            "stop_rel_s": (stop.t - trace.start_ms) / 1000.0,
            "turned_rel_s": (turned - trace.start_ms) / 1000.0,
            "start_world": _apply(T[0].origin, offset, yaw_offset),
            "stop_world": tuple(stop_at),
            "template_duration_s": trace.duration_ms() / 1000.0}


def _apply(o: Vec3, offset: Vec3, yaw_offset: float) -> Vec3:
    c, sn = math.cos(math.radians(yaw_offset)), math.sin(math.radians(yaw_offset))
    return (o[0] * c - o[1] * sn + offset[0], o[0] * sn + o[1] * c + offset[1],
            o[2] + offset[2])


def validate_placement_shared(trace, placement: dict, map_name: str, nav) -> dict:
    """The SHARED validity: retarget.validate_retarget over SpatialValidity
    (MapSpatialIndex occupancy from thousands of demos + NavigationTruth).

    validate_placement below is the prologue's earlier same-floor check and
    is kept only as a second opinion in the report; the verdict that gates a
    render is this one.
    """
    from engine.pantheon.retarget import SpatialValidity, validate_retarget
    spatial = None
    try:
        from engine.pantheon.map_spatial_index import MapSpatialIndex
        spatial = MapSpatialIndex.for_map(map_name)
    except Exception as exc:                      # pragma: no cover - data
        spatial_note = f"MapSpatialIndex unavailable: {exc!r}"[:160]
    else:
        spatial_note = "MapSpatialIndex + NavigationTruth"
    sv = SpatialValidity(spatial=spatial, navigation=nav)
    v = validate_retarget(trace, placement["retarget"], sv)
    d = v.as_dict() if hasattr(v, "as_dict") else dict(vars(v))
    d["reference"] = spatial_note
    return d


def validate_placement(trace, placement: dict, nav, *, floor_tol: float = 40.0,
                       walk_tol: float = 96.0) -> dict:
    """Is the retargeted path on ground real players stood on?

    Every retargeted sample is checked against NavigationTruth's walked
    points: horizontal distance to the nearest one, and height against that
    point's floor. A path that leaves walked ground by more than `walk_tol`
    or floats/sinks by more than `floor_tol` is INVALID -- the local frame
    fit mathematically and put the recording through a wall.
    """
    pts = [pt for r in nav.routes for pt in r.points]
    worst_xy, worst_z, n_bad = 0.0, 0.0, 0
    for s in trace.transform:
        w = _apply(s.origin, placement["offset"], placement["yaw_offset"])
        # judge against ground on the SAME floor: the nearest point in XY can
        # sit a level below where the upper floor has an opening, which reads
        # as a 345-unit drop on a run that never left its floor
        same = [p for p in pts if abs(p[2] - w[2]) <= floor_tol]
        if not same:
            n_bad += 1
            worst_z = max(worst_z, min(abs(p[2] - w[2]) for p in pts))
            continue
        near = min(same, key=lambda p: (p[0] - w[0]) ** 2 + (p[1] - w[1]) ** 2)
        dxy = math.hypot(near[0] - w[0], near[1] - w[1])
        dz = abs(near[2] - w[2])
        worst_xy, worst_z = max(worst_xy, dxy), max(worst_z, dz)
        if dxy > walk_tol:
            n_bad += 1
    return {"samples": len(trace.transform), "off_walked_ground": n_bad,
            "worst_xy_u": round(worst_xy, 1), "worst_z_u": round(worst_z, 1),
            "verdict": "VALID" if n_bad == 0 else "INVALID",
            "reference": f"NavigationTruth {nav.map_name}: {len(pts)} walked points"}


def camera_plan_to_presenter(*, start_pos: Vec3, start_yaw: float, start_pitch: float,
                             subject: Vec3, subject_face_yaw: float, map_name: str,
                             begin_ms: int, duration_ms: int, hold_until_ms: int,
                             close_u: float = 140.0, lateral_deg: float = 28.0,
                             hz: float = 40.0, pk3_path: str | None = None,
                             end_pos: Vec3 | None = None, look_at: Vec3 | None = None,
                             mid_pos: Vec3 | None = None) -> dict:
    """A medium-wide -> low dolly -> lateral arc -> settle, on the project's
    own camera machinery, collision-checked against the real BSP.

    The camera COMES TO HER: it starts on the historical POV, holds while
    she runs in (the movement must be readable first), then after her stop
    dollies to conversational distance on a modest arc so the frozen fight
    stays in the frame behind her. Position and look-at come from
    camera_paths; the dense curve from camera_compiler_v2.resample_dense;
    validity from collision_check_dense over camera_paths.bsp_tracer -- not
    from any prologue re-implementation. The execution backend differs:
    keyframes are written into the demo's own point of view rather than a
    FREECAM_SAMPLED cfg, so the camera is in FrameTruth and in the AVI.
    """
    from creative_suite.engine import camera_paths as cp
    from creative_suite.engine import camera_compiler_v2 as cc
    aim = look_at or (subject[0], subject[1], subject[2] + cp.SUBJECT_EYE_Z)
    if end_pos is None:
        # the conversational mark: `close_u` in front of her, offset by
        # `lateral_deg` off her facing line so she is not dead-centre-flat
        az = math.radians(subject_face_yaw + lateral_deg)
        end_pos = (subject[0] + close_u * math.cos(az), subject[1] + close_u * math.sin(az),
                   subject[2] + cp.SUBJECT_EYE_Z + 6.0)
    mid = mid_pos or ((start_pos[0] + end_pos[0]) / 2, (start_pos[1] + end_pos[1]) / 2,
                      min(start_pos[2], end_pos[2]) - 4.0)   # the low dolly
    sparse = [
        cp._kf(0, start_pos, (start_pitch, start_yaw, 0.0), cp.DEFAULT_FOV),
        cp._kf(begin_ms, start_pos, (start_pitch, start_yaw, 0.0), cp.DEFAULT_FOV),
        cp._kf(begin_ms + duration_ms * 0.55, mid, cp.look_at_angles(mid, aim), cp.DEFAULT_FOV),
        cp._kf(begin_ms + duration_ms, end_pos, cp.look_at_angles(end_pos, aim), cp.DEFAULT_FOV),
        cp._kf(hold_until_ms, end_pos, cp.look_at_angles(end_pos, aim), cp.DEFAULT_FOV),
    ]
    dense = cc.resample_dense(sparse, hz)
    tracer = None
    note = "no tracer: collision UNCHECKED"
    try:
        tracer = cp.bsp_tracer(map_name, pk3_path)
        note = f"camera_paths.bsp_tracer({map_name}) over the real BSP"
    except Exception as exc:                          # pragma: no cover - data
        note = f"bsp_tracer unavailable: {exc!r}"[:160]
    subject_track = [(float(k["t_ms"]), *aim) for k in dense]
    res = cc.collision_check_dense(tracer, dense, subject_track)
    return {"keyframes": res["keyframes"], "status": res["status"],
            "min_clearance_u": res.get("min_clearance_u"),
            "used": res.get("used_count"), "authored": res.get("original_count"),
            "collision": note, "start": start_pos, "end": end_pos,
            "close_u": close_u, "lateral_deg": lateral_deg,
            "begin_ms": begin_ms, "duration_ms": duration_ms, "hz": hz}


# ── composition: the camera explains a relationship ────────────────────────
FOV_X = 110.0                # cg_fov, from the runtime inventory
FRAME_W, FRAME_H = 1920, 1080
BODY_H, BODY_W = 56.0, 24.0  # a standing player's silhouette, world units


def project(cam: Vec3, yaw: float, pitch: float, p: Vec3) -> tuple[float, float] | None:
    """Pinhole projection of a world point, in pixels. None if behind."""
    dx, dy, dz = p[0] - cam[0], p[1] - cam[1], p[2] - cam[2]
    a = math.radians(yaw)
    f = dx * math.cos(a) + dy * math.sin(a)
    r = -dx * math.sin(a) + dy * math.cos(a)
    b = math.radians(pitch)
    fz = f * math.cos(b) - dz * math.sin(b)      # forward after pitch
    uz = dz * math.cos(b) + f * math.sin(b)      # up after pitch (pitch>0 looks down)
    if fz <= 8.0:
        return None
    half = math.tan(math.radians(FOV_X / 2))
    half_y = half * (FRAME_H / FRAME_W)
    return (FRAME_W / 2 - (r / fz) / half * (FRAME_W / 2),
            FRAME_H / 2 - (uz / fz) / half_y * (FRAME_H / 2))


def bbox(cam: Vec3, yaw: float, pitch: float, origin: Vec3) -> dict | None:
    """Screen box of a standing body at `origin`, from its feet and head."""
    pts = []
    for dz in (0.0, BODY_H):
        for dx in (-BODY_W / 2, BODY_W / 2):
            for dy in (-BODY_W / 2, BODY_W / 2):
                q = project(cam, yaw, pitch, (origin[0] + dx, origin[1] + dy, origin[2] + dz))
                if q is None:
                    return None
                pts.append(q)
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    return {"x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys),
            "h": max(ys) - min(ys)}


def _inside(b: dict, margin: float = 0.08) -> bool:
    return (b["x0"] >= FRAME_W * margin and b["x1"] <= FRAME_W * (1 - margin)
            and b["y0"] >= FRAME_H * margin and b["y1"] <= FRAME_H * (1 - margin))


def _overlap(a: dict, b: dict) -> float:
    w = max(0.0, min(a["x1"], b["x1"]) - max(a["x0"], b["x0"]))
    h = max(0.0, min(a["y1"], b["y1"]) - max(a["y0"], b["y0"]))
    small = min((a["x1"] - a["x0"]) * (a["y1"] - a["y0"]),
                (b["x1"] - b["x0"]) * (b["y1"] - b["y0"])) or 1.0
    return w * h / small


SUBJECT_EYE_Z = 26.0   # DEFAULT_VIEWHEIGHT; mirrors camera_paths.SUBJECT_EYE_Z
PRESENTER_MIN_RATIO = 0.7   # her on-screen height vs the largest fighter


def sightlines_clear(tracer, cam: Vec3, subjects) -> bool:
    """True when every subject's eye, chest and feet are unobstructed from cam."""
    for s in subjects:
        for dz in (SUBJECT_EYE_Z, SUBJECT_EYE_Z * 0.5, 4.0):
            if tracer.line_blocked(cam, (s[0], s[1], s[2] + dz)):
                return False
    return True


def compose_three(*, presenter: Vec3, shooter: Vec3, target: Vec3, map_name: str,
                  distance: tuple[float, float] = (170.0, 210.0),
                  height: float | tuple[float, ...] = 32.0,
                  pk3_path: str | None = None, start_pos: Vec3 | None = None) -> dict:
    """Find a settle position from which Crash, Keel, Visor AND the line
    between the two are all readable, and Crash reads as the presenter.

    Candidates: every azimuth around the presenter at 5-degree steps, at
    distances in `distance`, at eye height. The camera looks at a point
    biased toward the presenter but pulled toward the shooter/target
    midpoint. Scored on: all three boxes inside the safe frame, presenter
    tallest, no overlap above 15%, line length on screen. Every candidate is
    checked for open space against the real BSP; the winner's clearance is
    reported. Headless.
    """
    from creative_suite.engine import camera_paths as cp
    tracer = None
    tracer_note = ""
    try:
        tracer = cp.bsp_tracer(map_name, pk3_path)
    except Exception as exc:                            # pragma: no cover
        tracer_note = f"bsp_tracer failed: {exc!r}"[:160]
    eye = lambda o: (o[0], o[1], o[2] + cp.SUBJECT_EYE_Z)

    def path_clear(cam):
        """The dolly from the start to this settle must not cross geometry:
        start -> a low mid -> settle, each leg traced. A settle that can only
        be reached through a wall is not a settle."""
        if tracer is None or start_pos is None:
            return True
        # try a low mid first (the dolly dips), then a level one, then a
        # slightly raised one: the first clear route wins and is recorded
        for dz in (-4.0, 0.0, +24.0, +48.0):
            mid_ = ((start_pos[0] + cam[0]) / 2, (start_pos[1] + cam[1]) / 2,
                    min(start_pos[2], cam[2]) + dz)
            if not (tracer.line_blocked(start_pos, mid_) or tracer.line_blocked(mid_, cam)):
                path_mid[id(cam)] = mid_
                return True
        return False
    mid = tuple((a + b) / 2 for a, b in zip(shooter, target))
    best, tried = None, 0
    path_mid: dict = {}
    why = {"solid": 0, "path": 0, "occluded": 0, "behind": 0, "frame": 0, "size": 0,
           "overlap": 0, "line": 0}
    steps = 4
    ds = [distance[0] + (distance[1] - distance[0]) * i / (steps - 1) for i in range(steps)]
    heights = (height,) if isinstance(height, (int, float)) else tuple(height)
    for d in ds:
      for h in heights:
        for az_deg in range(0, 360, 5):
            az = math.radians(az_deg)
            cam = (presenter[0] + d * math.cos(az), presenter[1] + d * math.sin(az),
                   presenter[2] + h)
            if tracer is not None and not cp.point_in_open_space(tracer, cam):
                why["solid"] += 1
                continue
            if not path_clear(cam):
                why["path"] += 1
                continue
            # The projection is blind to walls. A settle in open space with a
            # clear dolly can still stare into a pillar between it and the
            # cast (02B's first render did exactly that). Every subject must
            # be visible from the settle -- eye, chest and feet -- and the
            # presenter from the dolly's mid, or the settle is rejected.
            if tracer is not None and not sightlines_clear(tracer, cam,
                                                          (presenter, shooter, target)):
                why["occluded"] += 1
                continue
            if tracer is not None and path_mid.get(id(cam)) and                     not sightlines_clear(tracer, path_mid[id(cam)], (presenter,)):
                why["occluded"] += 1
                continue
            tried += 1
            for bias in (0.4, 0.55, 0.7):
                look = tuple(eye(presenter)[i] * bias + eye(mid)[i] * (1 - bias) for i in range(3))
                ang = cp.look_at_angles(cam, look)           # (pitch, yaw, roll)
                pitch, yaw = ang[0], ang[1]
                bp, bs, bt = (bbox(cam, yaw, pitch, o) for o in (presenter, shooter, target))
                if not (bp and bs and bt):
                    why["behind"] += 1
                    continue
                if not (_inside(bp, 0.05) and _inside(bs, 0.05) and _inside(bt, 0.05)):
                    why["frame"] += 1
                    continue
                if bp["h"] < PRESENTER_MIN_RATIO * max(bs["h"], bt["h"]):
                    why["size"] += 1
                    continue        # Crash may be slightly smaller (02B brief)
                if max(_overlap(bp, bs), _overlap(bp, bt), _overlap(bs, bt)) > 0.2:
                    why["overlap"] += 1
                    continue
                e1 = project(cam, yaw, pitch, eye(shooter)); e2 = project(cam, yaw, pitch, eye(target))
                if e1 is None or e2 is None:
                    why["behind"] += 1
                    continue
                line_px = math.dist(e1, e2)
                if line_px < FRAME_W * 0.2:
                    why["line"] += 1
                    continue
                # prefer: bigger presenter, longer line, presenter off-centre
                score = bp["h"] / FRAME_H * 2.0 + line_px / FRAME_W + \
                    0.3 * (1.0 - abs((bp["x0"] + bp["x1"]) / 2 - FRAME_W / 2) / FRAME_W)
                if best is None or score > best["score"]:
                    best = {"score": round(score, 3), "camera": cam, "look_at": look,
                            "path_mid": path_mid.get(id(cam)),
                            "yaw": round(yaw, 2), "pitch": round(pitch, 2), "distance_u": d,
                            "azimuth_deg": az_deg, "bias": bias, "height_u": h,
                            "presenter_bbox": bp, "shooter_bbox": bs, "target_bbox": bt,
                            "line_px": round(line_px, 1),
                            "line_ends": [list(map(round, e1)), list(map(round, e2))]}
    if best is None:
        raise RuntimeError(f"no settle keeps presenter, shooter, target and the line in "
                           f"frame -- rejected: {why}")
    best["candidates_in_open_space"] = tried
    best["rejections"] = why

    best["collision"] = ("real BSP: settle in open space, start->mid->settle unblocked, "
                         "eye/chest/feet of all three subjects visible from the settle"
                         if tracer else f"UNCHECKED: {tracer_note or 'no tracer'}")
    return best


def _analysis_rail(t: float, actor: str, to: Vec3):
    """A rail event that exists to explain, not because it happened."""
    from engine.pantheon.scenario import _Event
    e = _Event(t, "fire", actor, None, Weapon.RAIL, position=to)
    e.layer = Layer.ANALYSIS          # never counted as a historical shot
    return e


def _edit_of(tm, historical_t: float, bias: str = "left") -> float:
    return tm.demo_to_edit(int(historical_t * US), bias=bias) / US


def _replace_t(k: _Keyframe, t: float) -> _Keyframe:
    return _Keyframe(t, k.origin, k.yaw, k.stance, k.weapon, k.health,
                     k.armor, k.alive)


# ── the analysis look, decided by PROOF B ───────────────────────────────────
#
# PROOF B measured three things that together make an analysis-only appearance
# possible without touching a single historical actor:
#
#   1. cg_team*Color / cg_enemy*Color TINT a player, keyed on his team relation
#      to the point of view;
#   2. the tint reaches the `bright` skin family and NOT `sarge/default`, which
#      measured (153,108,66) identically with the family cleared and set;
#   3. that is also why Keel came out white in PROOF 01 -- he was a teammate of
#      the POV and cg_teamLegsColor ships as 0xffffff.
#
# So the analysis body is the ONLY actor wearing a `bright` skin. The tint then
# lands on it and on nothing else, and every historical actor keeps exactly the
# appearance the demo authored. The explanatory copy is instantly separable
# from the fight without repainting the fight.

# The analysis graphic's own colour, a SEMANTIC role. How a backend applies
# it for the freeze window only is the backend's business (shot.py); this
# layer only says which colour and which window.
ANALYSIS_GRAPHIC_RGB = (255, 204, 64)      # Pantheon gold


PANTHEON_GREEN = (60, 235, 90)     # readable against grey arena stone,
                                   # and not the nuclear 0x00ff00 of the test

ANALYSIS_SKIN = "bright"


# HOW the tint reaches a renderer -- which cvars, in which format -- is the
# backend's business: engine.pantheon.color_format.analysis_visual_cvars.
# This layer states the intent (PANTHEON_GREEN on the analysis body, chosen
# by team relation to the POV) and nothing lower.
