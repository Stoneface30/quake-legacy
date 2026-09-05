"""DiegeticPresenter — a character who explains the game from inside it.

THE IDEA. The narrator is not a voice over footage; he is a player standing in
Campgrounds who turns to the camera and talks. Everything he does is authored
as game intent -- walk, turn, gesture, speak -- and compiles down to the same
demo the engine plays and the same FrameTruth the overlay reads.

WHAT THIS LAYER MAY NOT CONTAIN. No `torsoAnim = 6`, no configstring numbers,
no sound commands, no cam10. `presenter.say(...)` schedules a DialogueCue on
the scenario's clock and turns the body toward the camera; how that becomes an
animation number is the compiler's problem.

ONE CLOCK. A cue's `start_t` is seconds from scenario start -- the same basis
the demo's serverTime and FrameTruth use. Dialogue cannot drift against the
picture because there is no second timeline for it to drift on.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from engine.pantheon.scenario import Actor, RoundScenario, Team, Vec3
from engine.pantheon.voice import (
    DialogueCue, GameVoiceBank, PROFILES, SourceKind, SpatialMode, VoiceLine,
    wav_duration)


@dataclass
class Presenter:
    """A speaking character. Wraps an Actor; adds voice and performance."""
    actor: Actor
    profile_name: str
    stage: "Stage"

    # -- movement and attention ----------------------------------------
    def stand_at(self, where: Vec3, *, facing: Vec3 | None = None,
                 t: float = 0.0) -> "Presenter":
        yaw = 0.0 if facing is None else _yaw(where, facing)
        self.actor.spawn(where, yaw=yaw, t=t)
        return self

    def walk_to(self, route: Sequence[Vec3], *, during: tuple[float, float]
                ) -> "Presenter":
        self.actor.move_to(list(route), during=during)
        return self

    def look_at_camera(self, *, t: float) -> "Presenter":
        self.actor.look_at(self.stage.camera_actor, t=t)
        return self

    def look_at(self, other: "Presenter", *, t: float) -> "Presenter":
        self.actor.look_at(other.actor, t=t)
        return self

    def gesture(self, *, t: float) -> "Presenter":
        self.actor.gesture(t=t)
        return self

    def hold(self, *, until: float) -> "Presenter":
        self.actor.stand(until=until)
        return self

    # -- speech ---------------------------------------------------------
    def say_line(self, line: VoiceLine, *, t: float,
                 to_camera: bool = True) -> float:
        """Speak a REAL recorded line. Returns when it finishes."""
        if to_camera:
            self.look_at_camera(t=max(0.0, t - 0.3))
        self.stage.cues.append(DialogueCue(
            actor_id=self.actor.name, text=line.text, start_t=t,
            duration_s=line.duration_s, audio_path=line.path,
            source_kind=SourceKind.GAME_ASSET, profile=self.profile_name,
            words=line.words, spatial=SpatialMode.DIEGETIC))
        return t + line.duration_s

    def say_synth(self, text: str, audio: Path, *, t: float,
                  to_camera: bool = True) -> float:
        """Speak a synthesised line -- for things the game never recorded."""
        if to_camera:
            self.look_at_camera(t=max(0.0, t - 0.3))
        dur = wav_duration(audio)
        self.stage.cues.append(DialogueCue(
            actor_id=self.actor.name, text=text, start_t=t, duration_s=dur,
            audio_path=str(audio), source_kind=SourceKind.SYNTHETIC_TTS,
            profile=self.profile_name, spatial=SpatialMode.DIEGETIC))
        return t + dur


class Stage:
    """A scenario with speaking characters and a camera they play to."""

    def __init__(self, scn: RoundScenario, *, camera_at: Vec3,
                 looking_at: Vec3) -> None:
        self.scn = scn
        self.cues: list[DialogueCue] = []
        self.camera_pos = camera_at
        scn.observer(camera_at, yaw=_yaw(camera_at, looking_at))
        # A stand-in the presenters can turn toward. It is never rendered --
        # actors need something in world space to face, and "the camera" has
        # to be a position for `look_at` to mean anything.
        from engine.pantheon.scenario import _Keyframe, Stance, Weapon
        self.camera_actor = Actor(scn, "__CAMERA__", Team.RED, client=99)
        self.camera_actor._keys.append(
            _Keyframe(0.0, camera_at, 0.0, Stance.IDLE, Weapon.ROCKET,
                      200, 100, True))

    def presenter(self, name: str, team: Team, *, model: str, skin: str,
                  profile: str, c1: str | None = None, c2: str | None = None
                  ) -> Presenter:
        a = self.scn.actor(name, team).appearance(model, skin, c1=c1, c2=c2)
        return Presenter(actor=a, profile_name=profile, stage=self)

    def dialogue_track(self) -> list[dict]:
        return [c.as_dict() for c in sorted(self.cues, key=lambda c: c.start_t)]

    def subtitle_at(self, t: float) -> tuple[str, str] | None:
        """(speaker, text) for whatever is being said at `t`."""
        for c in self.cues:
            s = c.subtitle_at(t)
            if s:
                return c.actor_id, s
        return None

    def pan_and_distance(self, cue: DialogueCue, frame_truth) -> tuple[float, float]:
        """Where the speaker is relative to the camera, for the mix.

        Taken from FrameTruth rather than guessed, so a voice moves in the
        stereo field because the character moved -- not because someone
        keyframed it.
        """
        fr = frame_truth.at(cue.start_t + cue.duration_s / 2)
        who = fr.actors.get(cue.actor_id)
        if who is None:
            return 0.0, 0.0
        cx, cy, _ = self.camera_pos
        ax, ay, _ = who.position
        # the camera's facing, so "left" means left of frame
        look = math.radians(self.scn._camera_path[0].yaw)
        rel = math.atan2(ay - cy, ax - cx) - look
        pan = max(-1.0, min(1.0, math.sin(rel) * 1.4))
        dist = min(1.0, math.dist((cx, cy), (ax, ay)) / 900.0)
        return pan, dist


def _yaw(a: Vec3, b: Vec3) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360
