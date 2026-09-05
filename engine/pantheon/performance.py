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
# The RECORDER is not an entity in his own snapshots; his state is the
# playerstate. These ordinals are the ioquake3 playerStateFields table, which
# matches every playerstate index the parser already uses (1,2,4,5,6,7,9,10,
# 13,16,18,20,40), and were VERIFIED on a real overkill demo: legs while
# speed > 250 read RUN/JUMP/BACK, torso reads ATTACK/STAND/DROP/RAISE.
PS_TORSO_ANIM, PS_LEGS_ANIM = 14, 17
PS_ORIGIN = (1, 2, 9)
PS_VELOCITY = (4, 5, 10)
PS_YAW, PS_PITCH, PS_GROUND, PS_CLIENT, PS_WEAPON = 6, 7, 20, 40, 41
ANIM_TOGGLE = 128
ENTITYNUM_NONE = 1023
WP_ROCKET, WP_RAIL = 5, 7
# MOD_ROCKET / MOD_ROCKET_SPLASH, from the parser's own table rather than a
# restated bg_public.h. A first version wrote {3, 4}, which the parser reads
# as MACHINEGUN and GRENADE; the index shows rocket kills at 6 and 7.
MOD_ROCKET = {code for code, name in dp._MOD_NAMES.items() if name.startswith("ROCKET")}


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
    pov: bool = False                 # True when this is the recorder himself
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

    @classmethod
    def from_dict(cls, d: dict) -> "PerformanceTrace":
        """The inverse of as_dict: what the index stored comes back whole."""
        def t3(v):
            return tuple(v) if v is not None else None
        tr = cls(d["demo_hash"], d["map"], d["gametype"], d["client"],
                 d["start_ms"], d["end_ms"], pov=bool(d.get("pov", False)))
        if d.get("authorities"):
            tr.authorities = dict(d["authorities"])
        tr.transform = [TransformSample(x["t"], t3(x["origin"]), t3(x["velocity"]),
                                        x["speed"], x["airborne"], x["ground_entity"])
                        for x in d.get("transform", [])]
        tr.aim = [AimSample(x["t"], x["yaw"], x["pitch"], x["yaw_rate"], x["pitch_rate"])
                  for x in d.get("aim", [])]
        tr.animation = [AnimSample(x["t"], x["legs"], x["torso"], x["legs_toggle"],
                                   x["torso_toggle"]) for x in d.get("animation", [])]
        tr.weapon = [WeaponSample(x["t"], x["weapon"]) for x in d.get("weapon", [])]
        tr.projectiles = [ProjectileSample(x["t"], x["entity"], x["weapon"],
                                           t3(x["origin"]), t3(x["velocity"]))
                          for x in d.get("projectiles", [])]
        tr.events = [ActionEvent(x["t"], x["kind"], x.get("weapon"), t3(x.get("position")),
                                 x.get("other_client"), x.get("parm"))
                     for x in d.get("events", [])]
        return tr

    @classmethod
    def load(cls, path: Path) -> "PerformanceTrace":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


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
    recorder: list[dict] = []          # the POV's own playerstate, per snapshot
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
        ps = parser._ps_state
        if ps:
            l = int(ps.get(PS_LEGS_ANIM, 0) or 0); to = int(ps.get(PS_TORSO_ANIM, 0) or 0)
            g = ps.get(PS_GROUND)
            recorder.append({
                "t": t, "client": ps.get(PS_CLIENT),
                "origin": tuple(float(ps.get(i, 0.0) or 0.0) for i in PS_ORIGIN),
                "velocity": tuple(float(ps.get(i, 0.0) or 0.0) for i in PS_VELOCITY),
                "yaw": float(ps.get(PS_YAW, 0.0) or 0.0),
                "pitch": float(ps.get(PS_PITCH, 0.0) or 0.0),
                "airborne": g == ENTITYNUM_NONE, "ground": g,
                "weapon": ps.get(PS_WEAPON),
                "legs": l & ~ANIM_TOGGLE, "torso": to & ~ANIM_TOGGLE,
                "legs_toggle": bool(l & ANIM_TOGGLE),
                "torso_toggle": bool(to & ANIM_TOGGLE)})

    parser._parse_snapshot = hook
    out = parser.parse()
    out["recorder_track"] = recorder
    return out, anims


def recorder_client(out: dict) -> int | None:
    """The POV client slot, from the playerstate itself."""
    for r in out.get("recorder_track", []):
        if r["client"] is not None:
            return int(r["client"])
    return None


def extract_performance(demo: Path, start_ms: int, end_ms: int, client: int,
                        *, parsed=None) -> PerformanceTrace:
    """Everything the demo observed about `client` between start and end."""
    out, anims = parsed if parsed is not None else _parse_with_anims(demo)
    rec = recorder_client(out)
    if client is None:
        client = rec
    tr = PerformanceTrace(demo_hash=demo_hash(demo), map=out["map"],
                          gametype=out["gametype"], client=client,
                          start_ms=start_ms, end_ms=end_ms)
    win = lambda t: start_ms <= t <= end_ms
    tr.pov = (client == rec)

    prev = None
    if client == rec:
        # THE RECORDER. Not in his own entity list; every track comes from the
        # playerstate, sampled at every snapshot.
        tr.authorities["transform"] = "OBSERVED playerstate origin/velocity per snapshot"
        tr.authorities["aim"] = "OBSERVED playerstate viewangles per snapshot"
        tr.authorities["animation"] = "OBSERVED playerstate legsAnim/torsoAnim (PS 17/14, verified)"
        for r in out["recorder_track"]:
            t = r["t"]
            if not win(t):
                continue
            v = r["velocity"]
            tr.transform.append(TransformSample(
                t, r["origin"], v, math.hypot(v[0], v[1]), r["airborne"], r["ground"]))
            yr = pr = 0.0
            if prev and t > prev[0]:
                dt = (t - prev[0]) / 1000.0
                yr = ((r["yaw"] - prev[1] + 180) % 360 - 180) / dt
                pr = (r["pitch"] - prev[2]) / dt
            tr.aim.append(AimSample(t, r["yaw"], r["pitch"], round(yr, 1), round(pr, 1)))
            prev = (t, r["yaw"], r["pitch"])
            tr.animation.append(AnimSample(t, r["legs"], r["torso"],
                                           r["legs_toggle"], r["torso_toggle"]))
            if r["weapon"] is not None and (not tr.weapon or tr.weapon[-1].weapon != r["weapon"]):
                tr.weapon.append(WeaponSample(t, int(r["weapon"])))
    # The parser appends one entity row per DELTA, and a snapshot can carry
    # more than one delta for the same entity (the player and an event on
    # him). Two rows at one serverTime became two keyframes at one time, and
    # the interpolator handed back the first where the differential expected
    # the second. Keep the LAST row per tick: the accumulated state.
    by_t: dict[int, dict] = {}
    for e in ([] if client == rec else out["entities"]):
        if e["client_num"] == client and win(e["server_time_ms"]):
            by_t[e["server_time_ms"]] = e
    for t in sorted(by_t):
        e = by_t[t]
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

    if client != rec:
        an_by_t: dict[int, dict] = {}
        for a in anims:
            if a["client"] == client and win(a["t"]):
                an_by_t[a["t"]] = a
        for t in sorted(an_by_t):
            a = an_by_t[t]
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
        # playerstate events carry no entity clientNum: None means the POV
        mine = ev.get("client_num") == client or (
            ev.get("client_num") is None and client == rec
            and ev["type"] != "obituary")
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
        rec = recorder_client(out)
        evs = out["events"]
        pads = [e for e in evs if e["type"] == "jump_pad"]
        fires = [e for e in evs if e["type"] == "fire_weapon" and e.get("weapon") == WP_ROCKET]
        hits = [e for e in evs if e["type"] == "missile_hit" and e.get("weapon") == WP_ROCKET]
        obits = [e for e in evs if e["type"] == "obituary" and e.get("weapon") in MOD_ROCKET]
        h = demo_hash(path)
        for jp in pads:
            c = jp["client_num"] if jp["client_num"] is not None else rec
            for f in fires:
                fc = f["client_num"] if f["client_num"] is not None else rec
                if fc != c or not 0 < f["server_time_ms"] - jp["server_time_ms"] <= max_gap_ms:
                    continue
                res = None
                for o in obits:
                    if o["killer_client"] == c and 0 < o["server_time_ms"] - f["server_time_ms"] <= max_flight_ms:
                        res = ("obituary", o); break
                if res is None:
                    for hh in hits:
                        hc = hh["client_num"] if hh["client_num"] is not None else rec
                        if hc == c and 0 < hh["server_time_ms"] - f["server_time_ms"] <= max_flight_ms:
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
