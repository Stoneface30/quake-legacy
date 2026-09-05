"""PerformanceTrace — one real player's complete action, read off the demo.

THE TARGET. "This is the guy taking a jump pad and hitting a sick rocket" ->
code. Not an approximation of it: the recorded transform curve, the recorded
aim curve, the recorded animation states, the recorded weapon, fire, missile
flight and impact, all on the demo's own serverTime, ready to be compiled back
into a synthetic demo that the engine plays as the same action.

ONE CLOCK. Every track is keyed on serverTime ms from the .dm_73. Nothing in
this module estimates a time; if the demo did not carry a sample, the track
does not have one.

WHAT IS OBSERVED AND WHAT IS NOT. Per snapshot, a player ENTITY carries
pos.trBase, pos.trDelta, apos yaw/pitch, weapon, groundEntityNum, legsAnim,
torsoAnim and an event field; a MISSILE entity carries pos/trDelta, weapon,
owner. Events (EV_JUMP_PAD, EV_FIRE_WEAPON, EV_MISSILE_HIT/MISS, EV_PAIN,
EV_OBITUARY) are what the server said happened. Between snapshots the client
interpolates; PANTHEON does the same and says so. Damage is NOT observed:
EV_PAIN carries health-at-pain and is throttled, and that limit is kept.

NOTHING IDENTIFIES A PLAYER. Traces are keyed by client slot and demo hash;
names never enter the structure.
"""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

from engine.parser import demo_parse as dp
from engine.parser.demo_parse import DM73Parser

FRAGS_DB = Path("G:/QUAKE_LEGACY/creative_suite/database/frags_rebuilt.db")
ES_TORSO_ANIM, ES_LEGS_ANIM = 13, 15
ANIM_TOGGLE = 128
ENTITYNUM_NONE = 1023
WP_ROCKET, WP_RAIL = 5, 7
MOD_ROCKET = {3, 4}          # MOD_ROCKET, MOD_ROCKET_SPLASH (bg_public.h)


# ── the schema ─────────────────────────────────────────────────────────────

@dataclass
class TransformSample:
    t: int                       # serverTime ms
    origin: tuple[float, float, float]
    velocity: tuple[float, float, float]
    speed: float                 # |velocity| in the horizontal plane
    airborne: bool
    ground_entity: int | None


@dataclass
class AimSample:
    t: int
    yaw: float
    pitch: float
    yaw_rate: float              # deg/s from the previous sample
    pitch_rate: float


@dataclass
class AnimSample:
    t: int
    legs: int                    # animNumber_t, toggle bit stripped
    torso: int
    legs_toggle: bool            # the toggle bit as sent
    torso_toggle: bool


@dataclass
class WeaponSample:
    t: int
    weapon: int


@dataclass
class ProjectileSample:
    t: int
    entity: int
    weapon: int
    origin: tuple[float, float, float]
    velocity: tuple[float, float, float]


@dataclass
class ActionEvent:
    t: int
    kind: str                    # jump_pad | fire_weapon | missile_hit | ...
    weapon: int | None = None
    position: tuple[float, float, float] | None = None
    other_client: int | None = None      # victim for obituary, else None
    parm: int | None = None


@dataclass
class PerformanceTrace:
    """One player, one interval, every observed track."""
    demo_hash: str
    map: str
    gametype: str
    client: int
    start_ms: int
    end_ms: int
    transform: list[TransformSample] = field(default_factory=list)
    aim: list[AimSample] = field(default_factory=list)
    animation: list[AnimSample] = field(default_factory=list)
    weapon: list[WeaponSample] = field(default_factory=list)
    projectiles: list[ProjectileSample] = field(default_factory=list)
    events: list[ActionEvent] = field(default_factory=list)
    authorities: dict = field(default_factory=lambda: {
        "transform": "OBSERVED entity pos.trBase/trDelta per snapshot",
        "aim": "OBSERVED entity apos yaw/pitch per snapshot",
        "animation": "OBSERVED entity legsAnim/torsoAnim per snapshot",
        "weapon": "OBSERVED entity weapon per snapshot",
        "projectiles": "OBSERVED missile entity per snapshot (owner via otherEntityNum)",
        "events": "OBSERVED server events (EV_*)",
        "between_samples": "INTERPOLATED by the client; PANTHEON does the same",
        "damage": "NOT OBSERVED -- EV_PAIN is health-at-pain and throttled",
    })

    # -- derived, never typed ------------------------------------------
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    def speed_profile(self) -> dict:
        s = [x.speed for x in self.transform]
        if not s:
            return {}
        return {"max": round(max(s), 1), "mean": round(sum(s) / len(s), 1),
                "samples": len(s),
                "airborne_ms": sum(
                    b.t - a.t for a, b in zip(self.transform, self.transform[1:])
                    if a.airborne)}

    def anim_sequence(self) -> list[dict]:
        """Run-length: (t, legs, torso) only where a state changes."""
        out, last = [], None
        for a in self.animation:
            cur = (a.legs, a.torso)
            if cur != last:
                out.append({"t": a.t, "legs": a.legs, "torso": a.torso})
                last = cur
        return out

    def of_kind(self, kind: str) -> list[ActionEvent]:
        return [e for e in self.events if e.kind == kind]

    def as_dict(self) -> dict:
        d = asdict(self)
        d["derived"] = {"duration_ms": self.duration_ms(),
                        "speed": self.speed_profile(),
                        "anim_sequence": self.anim_sequence()}
        return d

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.as_dict(), indent=1), encoding="utf-8")
        return path


# ── extraction ─────────────────────────────────────────────────────────────

def demo_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _parse_with_anims(path: Path):
    """Full parse, plus per-snapshot legs/torso anim for every player entity."""
    parser = DM73Parser(path, track_missiles=True)
    anims: list[dict] = []
    orig = parser._parse_snapshot

    def hook(s, events, snapshots):
        orig(s, events, snapshots)
        t = parser._last_server_time
        for num, st in parser._entity_states.items():
            if num < 64 and st.get(dp._F_ETYPE) == 1:
                l = int(st.get(ES_LEGS_ANIM, 0)); to = int(st.get(ES_TORSO_ANIM, 0))
                anims.append({"t": t, "client": st.get(dp._F_CLIENT, num),
                              "legs": l & ~ANIM_TOGGLE, "torso": to & ~ANIM_TOGGLE,
                              "legs_toggle": bool(l & ANIM_TOGGLE),
                              "torso_toggle": bool(to & ANIM_TOGGLE)})

    parser._parse_snapshot = hook
    out = parser.parse()
    return out, anims


def extract_performance(demo: Path, start_ms: int, end_ms: int, client: int,
                        *, parsed=None) -> PerformanceTrace:
    """Everything the demo observed about `client` between start and end."""
    out, anims = parsed if parsed is not None else _parse_with_anims(demo)
    tr = PerformanceTrace(demo_hash=demo_hash(demo), map=out["map"],
                          gametype=out["gametype"], client=client,
                          start_ms=start_ms, end_ms=end_ms)
    win = lambda t: start_ms <= t <= end_ms

    prev = None
    for e in out["entities"]:
        if e["client_num"] != client or not win(e["server_time_ms"]):
            continue
        t = e["server_time_ms"]
        o = (e["origin_x"] or 0.0, e["origin_y"] or 0.0, e["origin_z"] or 0.0)
        v = (e["vel_x"] or 0.0, e["vel_y"] or 0.0, e["vel_z"] or 0.0)
        tr.transform.append(TransformSample(
            t, o, v, math.hypot(v[0], v[1]), bool(e["airborne"]),
            e["ground_entity"]))
        yaw, pitch = float(e["angle_yaw"] or 0.0), float(e["angle_pitch"] or 0.0)
        yr = pr = 0.0
        if prev and t > prev[0]:
            dt = (t - prev[0]) / 1000.0
            yr = ((yaw - prev[1] + 180) % 360 - 180) / dt
            pr = (pitch - prev[2]) / dt
        tr.aim.append(AimSample(t, yaw, pitch, round(yr, 1), round(pr, 1)))
        prev = (t, yaw, pitch)
        if e["weapon"] is not None:
            if not tr.weapon or tr.weapon[-1].weapon != e["weapon"]:
                tr.weapon.append(WeaponSample(t, int(e["weapon"])))

    for a in anims:
        if a["client"] == client and win(a["t"]):
            tr.animation.append(AnimSample(a["t"], a["legs"], a["torso"],
                                           a["legs_toggle"], a["torso_toggle"]))

    for m in out["missiles"]:
        if m.get("other") == client and win(m["server_time_ms"]):
            tr.projectiles.append(ProjectileSample(
                m["server_time_ms"], m["entity_num"], m["weapon"] or 0,
                (m["origin_x"] or 0.0, m["origin_y"] or 0.0, m["origin_z"] or 0.0),
                (m["vel_x"] or 0.0, m["vel_y"] or 0.0, m["vel_z"] or 0.0)))

    for ev in out["events"]:
        t = ev["server_time_ms"]
        if not win(t):
            continue
        mine = ev.get("client_num") == client
        killer = ev.get("killer_client") == client
        if not (mine or killer):
            continue
        pos = (None if ev.get("pos_x") is None
               else (ev["pos_x"], ev["pos_y"], ev["pos_z"]))
        tr.events.append(ActionEvent(
            t, ev["type"], ev.get("weapon"), pos,
            ev.get("victim_client") if killer else None, ev.get("event_parm")))
    tr.events.sort(key=lambda e: e.t)
    return tr


# ── finding the moment ─────────────────────────────────────────────────────

@dataclass
class Candidate:
    demo: str
    demo_hash: str
    map: str
    client: int
    jump_pad_ms: int
    fire_ms: int
    result_ms: int
    result: str                  # missile_hit | obituary
    victim: int | None
    is_recorder: bool
    score: float

    def as_dict(self) -> dict:
        d = asdict(self); d["demo"] = Path(self.demo).name[:12] + "..."
        return d


def find_jumppad_rocket(demos: Iterable[Path], *, max_gap_ms: int = 1500,
                        max_flight_ms: int = 2500) -> list[Candidate]:
    """JUMP_PAD -> rocket FIRE while airborne -> MISSILE_HIT or rocket obituary."""
    found = []
    for path in demos:
        try:
            out, _ = _parse_with_anims(path)
        except Exception:
            continue
        rec = None
        for c, p in out["players"].items():
            if p.get("is_recorder"):
                rec = c
        evs = out["events"]
        pads = [e for e in evs if e["type"] == "jump_pad"]
        fires = [e for e in evs if e["type"] == "fire_weapon" and e.get("weapon") == WP_ROCKET]
        hits = [e for e in evs if e["type"] == "missile_hit" and e.get("weapon") == WP_ROCKET]
        obits = [e for e in evs if e["type"] == "obituary" and e.get("weapon") in MOD_ROCKET]
        h = demo_hash(path)
        for jp in pads:
            c = jp["client_num"]
            for f in fires:
                if f["client_num"] != c or not 0 < f["server_time_ms"] - jp["server_time_ms"] <= max_gap_ms:
                    continue
                res = None
                for o in obits:
                    if o["killer_client"] == c and 0 < o["server_time_ms"] - f["server_time_ms"] <= max_flight_ms:
                        res = ("obituary", o); break
                if res is None:
                    for hh in hits:
                        if hh["client_num"] == c and 0 < hh["server_time_ms"] - f["server_time_ms"] <= max_flight_ms:
                            res = ("missile_hit", hh); break
                if res is None:
                    continue
                kind, r = res
                score = (3.0 if kind == "obituary" else 1.5) \
                    + (2.0 if c == rec else 0.0) \
                    - (f["server_time_ms"] - jp["server_time_ms"]) / 3000.0
                found.append(Candidate(
                    str(path), h, out["map"], c, jp["server_time_ms"],
                    f["server_time_ms"], r["server_time_ms"], kind,
                    r.get("victim_client"), c == rec, round(score, 2)))
    return sorted(found, key=lambda x: -x.score)


def corpus_demos(map_name: str, limit: int) -> list[Path]:
    con = sqlite3.connect(f"file:{FRAGS_DB.as_posix()}?mode=ro", uri=True)
    rows = con.execute(
        """select path from demos where map_name=? and gametype='CA'
           and accepted_frags > 8 order by size_bytes limit ?""",
        (map_name, limit)).fetchall()
    con.close()
    return [Path(r[0]) for r in rows if Path(r[0]).exists()]
