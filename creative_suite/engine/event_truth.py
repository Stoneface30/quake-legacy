"""Where gameplay timing comes from: the demo, never the soundtrack.

THE RULE THIS MODULE EXISTS TO ENFORCE. The engine already knows, exactly,
when the hit landed. Asking a finished Quake mix to rediscover that instant
is strictly worse: the LG hum is continuous, several weapons overlap, and a
0/33 contact-detection rate is what that approach actually delivered. Full
game audio is PRESENTATION. Semantic game events are TIMING TRUTH.

SIX LAYERS, NEVER COLLAPSED. Each answers a different question, and the gaps
between them are the measurements that matter:

    GAME_EVENT_TRUTH              when the engine says it happened
    VISUAL_EVENT_DELIVERY         the delivered frame where you can see it
    SELECTIVE_GAME_AUDIO_REFERENCE  a clean diagnostic sound for that event
    FULL_GAME_AUDIO               the presentation mix, for feel
    MUSIC_PERCEPTUAL_ANCHOR       where the music is heard to hit
    EDITORIAL_TARGET              the relationship a human asked for

Collapsing any two of these into "the kill time" is how a 137 ms render
latency, or a music anchor 255 ms from the frag, hides in plain sight.

OWNERSHIP COMES FROM ENTITY IDENTITY. Whose weapon fired, who took damage
and who died are read from the demo's own entity streams. Nothing in this
module may infer ownership from a waveform, and `infer_owner_from_audio`
exists only to refuse.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, replace
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Sequence

# ── layers ──────────────────────────────────────────────────────────────────

GAME_EVENT_TRUTH = "GAME_EVENT_TRUTH"
VISUAL_EVENT_DELIVERY = "VISUAL_EVENT_DELIVERY"
SELECTIVE_GAME_AUDIO_REFERENCE = "SELECTIVE_GAME_AUDIO_REFERENCE"
FULL_GAME_AUDIO = "FULL_GAME_AUDIO"
MUSIC_PERCEPTUAL_ANCHOR = "MUSIC_PERCEPTUAL_ANCHOR"
EDITORIAL_TARGET = "EDITORIAL_TARGET"

LAYERS = (GAME_EVENT_TRUTH, VISUAL_EVENT_DELIVERY,
          SELECTIVE_GAME_AUDIO_REFERENCE, FULL_GAME_AUDIO,
          MUSIC_PERCEPTUAL_ANCHOR, EDITORIAL_TARGET)

# Only this layer may be used to say when something HAPPENED.
AUTHORITATIVE_LAYER = GAME_EVENT_TRUTH

# ── ownership ───────────────────────────────────────────────────────────────

OWNER_ME = "ME"
OWNER_ENEMY = "ENEMY"
OWNER_TEAMMATE = "TEAMMATE"
OWNER_OTHER = "OTHER_PLAYER"
OWNER_WORLD = "WORLD"
OWNERS = (OWNER_ME, OWNER_ENEMY, OWNER_TEAMMATE, OWNER_OTHER, OWNER_WORLD)

# ── event kinds ─────────────────────────────────────────────────────────────

MY_WEAPON_FIRE = "MY_WEAPON_FIRE"
MY_LG_CONTACT = "MY_LG_CONTACT"
MY_HIT = "MY_HIT"
MY_DAMAGE_TO_ENEMY = "MY_DAMAGE_TO_ENEMY"
MY_FRAG = "MY_FRAG"
MY_DAMAGE_RECEIVED = "MY_DAMAGE_RECEIVED"
ENEMY_WEAPON_FIRE = "ENEMY_WEAPON_FIRE"
ENEMY_DEATH = "ENEMY_DEATH"
TEAMMATE_WEAPON_FIRE = "TEAMMATE_WEAPON_FIRE"
OTHER_PLAYER_WEAPON_FIRE = "OTHER_PLAYER_WEAPON_FIRE"
OTHER_GAME_SOUND = "OTHER_GAME_SOUND"
ROUND_WIN = "ROUND_WIN"
DODGE_CLOSEST_APPROACH = "DODGE_CLOSEST_APPROACH"

EVENT_KINDS = (MY_WEAPON_FIRE, MY_LG_CONTACT, MY_HIT, MY_DAMAGE_TO_ENEMY,
               MY_FRAG, MY_DAMAGE_RECEIVED, ENEMY_WEAPON_FIRE, ENEMY_DEATH,
               TEAMMATE_WEAPON_FIRE, OTHER_PLAYER_WEAPON_FIRE,
               OTHER_GAME_SOUND, ROUND_WIN, DODGE_CLOSEST_APPROACH)

# Which events a hero payoff may be anchored to. A weapon leaving a barrel
# is not the moment a viewer feels, so firing is deliberately absent.
HERO_CANDIDATE_KINDS = (MY_FRAG, ENEMY_DEATH, MY_HIT, MY_DAMAGE_TO_ENEMY,
                        ROUND_WIN, DODGE_CLOSEST_APPROACH)


class OwnershipFromAudioError(RuntimeError):
    """Raised on any attempt to decide who did something from a waveform."""


def infer_owner_from_audio(*_args: Any, **_kwargs: Any) -> str:
    """Never implemented on purpose.

    Ownership is entity identity. It is recorded in the demo. A sound in the
    mix cannot distinguish my lightning gun from the enemy's, and a system
    that guesses will be confidently wrong at exactly the moments that
    matter most.
    """
    raise OwnershipFromAudioError(
        "ownership comes from demo entity identity, never from audio; "
        "load the event from recognition evidence instead")


# ── one event ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GameEvent:
    """One semantic gameplay event, in ONE layer, with its evidence."""
    kind: str
    owner: str
    layer: str
    edit_us: int
    confidence: float = 1.0
    amount: float | None = None          # damage, health, units -- kind-specific
    subject_client: int | None = None     # entity slot, never a name
    object_client: int | None = None
    evidence: str = ""
    provenance: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in EVENT_KINDS:
            raise ValueError(f"unknown event kind {self.kind!r}")
        if self.owner not in OWNERS:
            raise ValueError(f"unknown owner {self.owner!r}")
        if self.layer not in LAYERS:
            raise ValueError(f"unknown layer {self.layer!r}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")

    @property
    def is_authoritative(self) -> bool:
        return self.layer == AUTHORITATIVE_LAYER

    @property
    def edit_s(self) -> float:
        return self.edit_us / 1e6

    def in_layer(self, layer: str, edit_us: int, *, evidence: str = "",
                 confidence: float | None = None) -> "GameEvent":
        """The SAME event as observed in another layer, at another time.

        This is how a delivered-media measurement is recorded without
        overwriting the truth it is being compared against.
        """
        return replace(self, layer=layer, edit_us=int(edit_us),
                       evidence=evidence or self.evidence,
                       confidence=self.confidence if confidence is None
                       else float(confidence))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["provenance"] = [list(kv) for kv in self.provenance]
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GameEvent":
        return cls(kind=str(d["kind"]), owner=str(d["owner"]),
                   layer=str(d["layer"]), edit_us=int(d["edit_us"]),
                   confidence=float(d.get("confidence", 1.0)),
                   amount=d.get("amount"),
                   subject_client=d.get("subject_client"),
                   object_client=d.get("object_client"),
                   evidence=str(d.get("evidence", "")),
                   provenance=tuple((str(k), str(v))
                                    for k, v in d.get("provenance", ())))


# ── a scene's events ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EventTimeline:
    """Every layer's events for one scene, kept apart."""
    frag_id: int
    scene_start_us: int
    scene_end_us: int
    events: tuple[GameEvent, ...]

    def layer(self, layer: str) -> list[GameEvent]:
        return [e for e in self.events if e.layer == layer]

    def of_kind(self, *kinds: str, layer: str = AUTHORITATIVE_LAYER
                ) -> list[GameEvent]:
        want = set(kinds)
        return [e for e in self.events if e.layer == layer and e.kind in want]

    def owned_by(self, owner: str, *, layer: str = AUTHORITATIVE_LAYER
                 ) -> list[GameEvent]:
        return [e for e in self.events if e.layer == layer and e.owner == owner]

    def hero_event(self) -> GameEvent:
        """The gameplay moment a payoff should be anchored to.

        The frag, if there is one -- 'THE FRAG IS THE POINT'. Never a weapon
        firing, and never something read out of the mix.
        """
        for kind in HERO_CANDIDATE_KINDS:
            hits = self.of_kind(kind)
            if hits:
                return max(hits, key=lambda e: e.edit_us)
        raise LookupError("no hero-candidate event in this scene")

    def add(self, *events: GameEvent) -> "EventTimeline":
        return replace(self, events=self.events + tuple(events))

    def to_dict(self) -> dict[str, Any]:
        return {"frag_id": self.frag_id, "scene_start_us": self.scene_start_us,
                "scene_end_us": self.scene_end_us,
                "events": [e.to_dict() for e in self.events]}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EventTimeline":
        return cls(frag_id=int(d["frag_id"]),
                   scene_start_us=int(d["scene_start_us"]),
                   scene_end_us=int(d["scene_end_us"]),
                   events=tuple(GameEvent.from_dict(e) for e in d["events"]))


# ── loading truth from recognition evidence ─────────────────────────────────

RECOGNITION_DB = (Path(__file__).resolve().parents[2] / "creative_suite" /
                  "database" / "frag_recognition.db")

_PROV = (("source", "recognition_lg_engagements.series"),
         ("ownership", "demo entity identity, not audio"))


def load_lg_timeline(frag_id: int, *, kill_edit_us: int,
                     scene_start_us: int, scene_end_us: int,
                     db_path: Path | None = None) -> EventTimeline:
    """Build the authoritative timeline for an LG scene.

    ``kill_edit_us`` places the frag on the edit clock; every series entry is
    stored relative to the frag in the demo, so the two agree by construction
    and no audio is consulted at any point.
    """
    path = Path(db_path or RECOGNITION_DB)
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT demo_name, server_time_ms, victim_client, weapon_name "
            "FROM recognized_frags WHERE id=?", (frag_id,)).fetchone()
        if row is None:
            raise LookupError(f"frag {frag_id} not in recognized_frags")
        eng = db.execute(
            "SELECT series FROM recognition_lg_engagements "
            "WHERE demo_name=? AND server_time_ms=?",
            (row["demo_name"], row["server_time_ms"])).fetchone()
    series = json.loads(eng["series"]) if eng else {}

    events: list[GameEvent] = [GameEvent(
        kind=MY_FRAG, owner=OWNER_ME, layer=GAME_EVENT_TRUTH,
        edit_us=int(kill_edit_us), object_client=row["victim_client"],
        evidence=f"recognized_frags row, weapon {row['weapon_name']}",
        provenance=_PROV)]

    for entry in series.get("dealt", ()):
        rel_ms, damage = (entry if isinstance(entry, (list, tuple))
                          else (entry, None))
        events.append(GameEvent(
            kind=MY_LG_CONTACT, owner=OWNER_ME, layer=GAME_EVENT_TRUTH,
            edit_us=int(kill_edit_us + rel_ms * 1000),
            amount=None if damage is None else float(damage),
            object_client=row["victim_client"],
            evidence="damage dealt to the victim entity",
            provenance=_PROV))

    for rel_ms in series.get("enemy_lg_fire", ()):
        events.append(GameEvent(
            kind=ENEMY_WEAPON_FIRE, owner=OWNER_ENEMY, layer=GAME_EVENT_TRUTH,
            edit_us=int(kill_edit_us + int(rel_ms) * 1000),
            evidence="enemy lightning fire, from the enemy's entity stream",
            provenance=_PROV))

    # Health decrements are damage received: the drop is the event, not the
    # sample, so only transitions become events.
    hp = [(int(t), float(v)) for t, v in series.get("my_hp", ())]
    for (t0, v0), (t1, v1) in zip(hp, hp[1:]):
        if v1 < v0:
            events.append(GameEvent(
                kind=MY_DAMAGE_RECEIVED, owner=OWNER_ME,
                layer=GAME_EVENT_TRUTH,
                edit_us=int(kill_edit_us + t1 * 1000), amount=float(v0 - v1),
                evidence=f"health {v0:.0f} -> {v1:.0f}", provenance=_PROV))

    inside = [e for e in events
              if scene_start_us <= e.edit_us <= scene_end_us]
    return EventTimeline(frag_id=frag_id, scene_start_us=int(scene_start_us),
                         scene_end_us=int(scene_end_us),
                         events=tuple(sorted(inside, key=lambda e: e.edit_us)))


# ── measured relationships between layers ───────────────────────────────────

@dataclass(frozen=True)
class LayerOffset:
    """How far one layer's observation sits from the authoritative time."""
    kind: str
    layer: str
    truth_us: int
    observed_us: int
    method: str

    @property
    def offset_ms(self) -> float:
        return round((self.observed_us - self.truth_us) / 1000.0, 2)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["offset_ms"] = self.offset_ms
        return d


def latency_table(pairs: Iterable[LayerOffset]) -> dict[str, Any]:
    """Per event class and layer, what the pipeline was observed to do.

    A reference table, deliberately not a set of constants: the rocket boom
    and the LG kill were measured 60 ms apart, so one measurement must never
    be promoted into a universal offset.
    """
    rows: dict[tuple[str, str], list[float]] = {}
    for p in pairs:
        rows.setdefault((p.kind, p.layer), []).append(p.offset_ms)
    out = []
    for (kind, layer), values in sorted(rows.items()):
        out.append({"event_kind": kind, "layer": layer, "n": len(values),
                    "offset_ms_min": min(values), "offset_ms_max": max(values),
                    "offset_ms_mean": round(sum(values) / len(values), 2)})
    return {"rows": out,
            "warning": "measured per scene; never reuse as a constant"}
