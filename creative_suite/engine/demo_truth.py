"""Gameplay truth as numbers, decoded once from the demo and cached.

THE CORRECTION THIS ENCODES. Asking a finished mp4 when a hit happened is
backwards: the demo already recorded it exactly. Rendered audio and video are
DELIVERY VERIFICATION -- they answer "when does the viewer see and hear it?" --
and they never establish what happened or when. Whenever authoritative demo
evidence exists, it wins, and this module is where that evidence becomes a
plain numeric timeline the composer can do arithmetic on.

THE DEMO IS NOT OMNISCIENT. A demo holds what the recording client was SENT.
Remote entities the client never received are simply absent, and the honest
response to absence is UNKNOWN, never a plausible reconstruction. Every event
therefore carries an evidence class on a ladder with three rungs of trust:

    RECORDED   POV_AUTHORITATIVE, SNAPSHOT_OBSERVED, ENTITY_OBSERVED,
               MULTI_DEMO_RECOVERED -- the demo stream carried it
    DERIVED    PHYSICS_RECONSTRUCTED, EVENT_CONSTRAINED_RECONSTRUCTION,
               GEOMETRY_RECONSTRUCTED, AI_CONSTRAINED_RECONSTRUCTION --
               computed from recorded facts, never equal to them
    AUTHORED   CINEMATIC_SYNTHETIC -- presentation, not history; refused here

A fact may move down the ladder as it is re-derived. It never moves up.

NOTHING HERE RE-PARSES. It reads permanent recognition caches that already
exist. Where a field is missing at corpus scale, this module says so through
`coverage_audit` rather than inventing it -- targeted enrichment is a decision
for a human, not a silent fallback.

PRIVACY. Demo filenames embed player aliases, so nothing here returns or
stores them. Frags are addressed by numeric id and players by client slot.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Sequence

from creative_suite.engine import event_truth as et

DEMO_TRUTH_VERSION = "demo-truth-v1.0.0"
PROTOCOL = "dm_73"

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

# ── evidence classes ────────────────────────────────────────────────────────
# Two families, deliberately kept apart. RECORDED means the demo stream
# carried it; everything below was DERIVED, and the class says from what. A
# derived fact must never be relabelled upward: the point of the ladder is
# that a reconstruction stays visibly a reconstruction.

# Recorded
POV_AUTHORITATIVE = "POV_AUTHORITATIVE"          # the recorder's own state
SNAPSHOT_OBSERVED = "SNAPSHOT_OBSERVED"          # read from a received snapshot
ENTITY_OBSERVED = "ENTITY_OBSERVED"              # a remote entity actually received
MULTI_DEMO_RECOVERED = "MULTI_DEMO_RECOVERED"    # recorded, in another demo
# Derived
PHYSICS_RECONSTRUCTED = "PHYSICS_RECONSTRUCTED"  # propagated by game rules + BSP
EVENT_CONSTRAINED = "EVENT_CONSTRAINED_RECONSTRUCTION"  # fitted to later evidence
GEOMETRY_RECONSTRUCTED = "GEOMETRY_RECONSTRUCTED"       # derived from positions + map
AI_CONSTRAINED = "AI_CONSTRAINED_RECONSTRUCTION"        # ranked among possibilities
# Authored
CINEMATIC_SYNTHETIC = "CINEMATIC_SYNTHETIC"      # presentation; not history at all

RECORDED_CLASSES = (POV_AUTHORITATIVE, SNAPSHOT_OBSERVED, ENTITY_OBSERVED,
                    MULTI_DEMO_RECOVERED)
DERIVED_CLASSES = (PHYSICS_RECONSTRUCTED, EVENT_CONSTRAINED,
                   GEOMETRY_RECONSTRUCTED, AI_CONSTRAINED)
EVIDENCE_CLASSES = RECORDED_CLASSES + DERIVED_CLASSES + (CINEMATIC_SYNTHETIC,)

# Older names, kept so nothing that spelled them breaks; same meaning.
EVENT_RECONSTRUCTED = EVENT_CONSTRAINED
MULTI_DEMO_AUGMENTED = MULTI_DEMO_RECOVERED

# How much a class may be trusted when two sources disagree. Lower wins.
EVIDENCE_RANK = {c: i for i, c in enumerate(EVIDENCE_CLASSES)}


def is_recorded(evidence: str) -> bool:
    return evidence in RECORDED_CLASSES


def may_relabel(old: str, new: str) -> bool:
    """A fact may only ever move DOWN the ladder, never up.

    Reconstructions get re-derived, refined and downgraded. They do not
    become recorded because a later pass felt confident.
    """
    return EVIDENCE_RANK[new] >= EVIDENCE_RANK[old]

# ── extra event kinds this module can produce ───────────────────────────────

PROJECTILE_CREATE = "PROJECTILE_CREATE"
PROJECTILE_IMPACT = "PROJECTILE_IMPACT"

# Kinds beyond event_truth's own vocabulary, kept here so event_truth stays
# the layer model and this stays the demo reader.
EXTRA_KINDS = (PROJECTILE_CREATE, PROJECTILE_IMPACT)
ALL_KINDS = et.EVENT_KINDS + EXTRA_KINDS


@dataclass(frozen=True)
class DemoEvent:
    """One gameplay fact, in demo time, with how well it is known."""
    demo_us: int
    kind: str
    owner: str
    evidence: str
    subject_client: int | None = None
    object_client: int | None = None
    entity_id: int | None = None
    weapon: str = et.OWNER_WORLD and ""      # empty means unknown
    amount: float | None = None
    position: tuple[float, float, float] | None = None
    velocity: tuple[float, float, float] | None = None
    view_angles: tuple[float, float] | None = None
    round_index: int | None = None
    confidence: float = 1.0
    source: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ALL_KINDS:
            raise ValueError(f"unknown event kind {self.kind!r}")
        if self.owner not in et.OWNERS:
            raise ValueError(f"unknown owner {self.owner!r}")
        if self.evidence not in EVIDENCE_CLASSES:
            raise ValueError(f"unknown evidence class {self.evidence!r}")

    @property
    def is_authoritative(self) -> bool:
        return is_recorded(self.evidence)

    @property
    def is_synthetic(self) -> bool:
        return self.evidence == CINEMATIC_SYNTHETIC

    def to_edit(self, *, hero_demo_us: int, hero_edit_us: int) -> et.GameEvent:
        """Cast onto the edit clock, keeping the layer model intact."""
        return et.GameEvent(
            kind=self.kind if self.kind in et.EVENT_KINDS
            else et.OTHER_GAME_SOUND,
            owner=self.owner, layer=et.GAME_EVENT_TRUTH,
            edit_us=hero_edit_us + (self.demo_us - hero_demo_us),
            confidence=self.confidence, amount=self.amount,
            subject_client=self.subject_client,
            object_client=self.object_client,
            evidence=f"{self.evidence}: {self.source}",
            provenance=(("protocol", PROTOCOL),
                        ("reader", DEMO_TRUTH_VERSION)))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for key in ("position", "velocity", "view_angles"):
            if d[key] is not None:
                d[key] = list(d[key])
        d["is_authoritative"] = self.is_authoritative
        return d


@dataclass(frozen=True)
class ProjectileTrack:
    """A projectile's flight as the cache holds it -- and how it got there.

    READ `evidence` BEFORE TRUSTING THE POINTS. The cache's projectile paths
    are NOT recorded trajectories: dm_73 demo_parse does not export missile
    entities, so the extractor inferred the launch from the impact and the
    recorder's view rays, drew rockets as a straight line and simulated
    grenades with constants it calls provisional. Every cached path is
    therefore EVENT_CONSTRAINED_RECONSTRUCTION. This module said
    ENTITY_OBSERVED for a day; it does not any more.
    """
    entity_kind: str
    launch_us: int
    impact_us: int
    launch_pos: tuple[float, float, float]
    impact_pos: tuple[float, float, float]
    points: tuple[tuple[int, float, float, float], ...]
    confidence: str
    bounces: int = 0
    evidence: str = EVENT_CONSTRAINED
    method: str = ("extract_projectile_paths: launch inferred from impact "
                   "+ view rays; rocket drawn straight, grenade simulated")

    @property
    def flight_us(self) -> int:
        return self.impact_us - self.launch_us

    @property
    def distance_units(self) -> float:
        dx = self.impact_pos[0] - self.launch_pos[0]
        dy = self.impact_pos[1] - self.launch_pos[1]
        dz = self.impact_pos[2] - self.launch_pos[2]
        return round((dx * dx + dy * dy + dz * dz) ** 0.5, 2)

    @property
    def speed_units_per_s(self) -> float | None:
        """Speed from the POINT SERIES, which is what actually flew.

        Not launch-to-impact over the scalar times: those can coincide at a
        single tick, and dividing by zero there is how a rocket once appeared
        to travel infinitely fast.
        """
        if len(self.points) < 2:
            return None
        span_us = self.points[-1][0] - self.points[0][0]
        if span_us <= 0:
            return None
        total = 0.0
        for a, b in zip(self.points, self.points[1:]):
            total += ((b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2
                      + (b[3] - a[3]) ** 2) ** 0.5
        return round(total / (span_us / 1e6), 1)

    def to_dict(self) -> dict[str, Any]:
        return {"entity_kind": self.entity_kind, "launch_us": self.launch_us,
                "impact_us": self.impact_us, "flight_us": self.flight_us,
                "distance_units": self.distance_units,
                "speed_units_per_s": self.speed_units_per_s,
                "confidence": self.confidence, "bounces": self.bounces,
                "evidence": self.evidence, "method": self.method,
                "points": len(self.points)}


@dataclass(frozen=True)
class DemoTruthTimeline:
    """Every numeric gameplay fact known about one moment."""
    frag_id: int
    hero_demo_us: int
    hero_kind: str
    weapon: str
    victim_client: int | None
    round_index: int | None
    events: tuple[DemoEvent, ...] = ()
    projectile: ProjectileTrack | None = None
    view_samples: tuple[tuple[int, float, float], ...] = ()
    derived: tuple[tuple[str, Any], ...] = ()
    protocol: str = PROTOCOL
    version: str = DEMO_TRUTH_VERSION

    def __post_init__(self) -> None:
        # Authored presentation lives in the recipe / Pandora domain. It
        # cannot land here even by accident, because this object is what the
        # composer treats as history.
        if any(e.is_synthetic for e in self.events):
            raise ValueError("CINEMATIC_SYNTHETIC events cannot enter a "
                             "DemoTruthTimeline")

    def of_kind(self, *kinds: str) -> list[DemoEvent]:
        want = set(kinds)
        return [e for e in self.events if e.kind in want]

    def authoritative(self) -> list[DemoEvent]:
        return [e for e in self.events if e.is_authoritative]

    def value(self, name: str) -> Any:
        return dict(self.derived).get(name)

    def to_edit_timeline(self, *, hero_edit_us: int, scene_start_us: int,
                         scene_end_us: int) -> et.EventTimeline:
        """Cast into edit time for the composer, layers preserved."""
        cast = [e.to_edit(hero_demo_us=self.hero_demo_us,
                          hero_edit_us=hero_edit_us) for e in self.events]
        inside = [e for e in cast if scene_start_us <= e.edit_us <= scene_end_us]
        return et.EventTimeline(self.frag_id, scene_start_us, scene_end_us,
                                tuple(sorted(inside, key=lambda e: e.edit_us)))

    def to_dict(self) -> dict[str, Any]:
        return {"frag_id": self.frag_id, "hero_demo_us": self.hero_demo_us,
                "hero_kind": self.hero_kind, "weapon": self.weapon,
                "victim_client": self.victim_client,
                "round_index": self.round_index, "protocol": self.protocol,
                "version": self.version,
                "events": [e.to_dict() for e in self.events],
                "projectile": (self.projectile.to_dict()
                               if self.projectile else None),
                "view_samples": len(self.view_samples),
                "derived": dict(self.derived)}


# ── loading from the permanent caches ───────────────────────────────────────

def load(frag_id: int, *, db_path: Path | None = None) -> DemoTruthTimeline:
    """Assemble every cached numeric fact for one frag. No demo is re-read."""
    path = Path(db_path or RECOGNITION_DB)
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        frag = db.execute(
            "SELECT id, demo_name, server_time_ms, round, weapon_name, "
            "victim_client, classes, attributes FROM recognized_frags "
            "WHERE id=?", (frag_id,)).fetchone()
        if frag is None:
            raise LookupError(f"frag {frag_id} is not in recognized_frags")
        demo_name, t_ms = frag["demo_name"], frag["server_time_ms"]
        lg = db.execute(
            "SELECT series FROM recognition_lg_engagements WHERE demo_name=? "
            "AND server_time_ms=?", (demo_name, t_ms)).fetchone()
        proj = db.execute(
            "SELECT path FROM recognition_projectile_paths WHERE demo_name=? "
            "AND server_time_ms=?", (demo_name, t_ms)).fetchone()
        view = db.execute(
            "SELECT samples FROM recognition_view_timeseries WHERE demo_name=? "
            "AND server_time_ms=?", (demo_name, t_ms)).fetchone()
        dodges = db.execute(
            "SELECT * FROM recognition_dodge_events WHERE demo_name=? AND "
            "kill_anchor_ms=?", (demo_name, t_ms)).fetchall()

    hero_us = int(t_ms) * 1000
    attrs = json.loads(frag["attributes"] or "{}")
    weapon = frag["weapon_name"] or ""
    events: list[DemoEvent] = [DemoEvent(
        demo_us=hero_us, kind=et.MY_FRAG, owner=et.OWNER_ME,
        evidence=POV_AUTHORITATIVE, object_client=frag["victim_client"],
        weapon=weapon, round_index=frag["round"],
        source="recognized_frags")]

    if lg is not None:
        series = json.loads(lg["series"])
        for entry in series.get("dealt", ()):
            rel, dmg = (entry if isinstance(entry, (list, tuple))
                        else (entry, None))
            events.append(DemoEvent(
                demo_us=hero_us + int(rel) * 1000, kind=et.MY_LG_CONTACT,
                owner=et.OWNER_ME, evidence=POV_AUTHORITATIVE,
                object_client=frag["victim_client"], weapon="LIGHTNING",
                amount=None if dmg is None else float(dmg),
                source="lg_engagements.dealt"))
        for rel in series.get("enemy_lg_fire", ()):
            events.append(DemoEvent(
                demo_us=hero_us + int(rel) * 1000, kind=et.ENEMY_WEAPON_FIRE,
                owner=et.OWNER_ENEMY, evidence=ENTITY_OBSERVED,
                weapon="LIGHTNING", source="lg_engagements.enemy_lg_fire"))
        hp = [(int(t), float(v)) for t, v in series.get("my_hp", ())]
        for (t0, v0), (t1, v1) in zip(hp, hp[1:]):
            if v1 < v0:
                events.append(DemoEvent(
                    demo_us=hero_us + t1 * 1000, kind=et.MY_DAMAGE_RECEIVED,
                    owner=et.OWNER_ME, evidence=POV_AUTHORITATIVE,
                    amount=float(v0 - v1), source="lg_engagements.my_hp"))

    track: ProjectileTrack | None = None
    if proj is not None and weapon.upper().startswith(("ROCKET", "GRENADE")):
        p = json.loads(proj["path"])
        launch, impact = p.get("launch") or {}, p.get("impact") or {}
        pts = tuple((int(x[0]) * 1000, float(x[1]), float(x[2]), float(x[3]))
                    for x in p.get("points", ()))
        kind_ok = str(p.get("kind", "")).upper() in weapon.upper()
        if launch and impact and kind_ok:
            track = ProjectileTrack(
                entity_kind=str(p.get("kind", "")),
                launch_us=int(launch["t"]) * 1000,
                impact_us=int(impact["t"]) * 1000,
                launch_pos=tuple(float(v) for v in launch["pos"]),
                impact_pos=tuple(float(v) for v in impact["pos"]),
                points=pts, confidence=str(p.get("confidence", "")),
                bounces=len(p.get("bounces", ())))
            # The launch is INFERRED (view ray + speed back from the impact).
            # The impact is a missile_hit temp-entity the client did receive.
            events.append(DemoEvent(
                demo_us=track.launch_us, kind=PROJECTILE_CREATE,
                owner=et.OWNER_ME, evidence=EVENT_CONSTRAINED, weapon=weapon,
                position=track.launch_pos, confidence=0.7,
                source="projectile_paths.launch (inferred from impact + view)"))
            events.append(DemoEvent(
                demo_us=track.impact_us, kind=PROJECTILE_IMPACT,
                owner=et.OWNER_ME, evidence=ENTITY_OBSERVED, weapon=weapon,
                position=track.impact_pos,
                source="projectile_paths.impact (missile_hit temp entity)"))

    for d in dodges:
        events.append(DemoEvent(
            demo_us=int(d["closest_time_ms"]) * 1000,
            kind=et.DODGE_CLOSEST_APPROACH, owner=et.OWNER_ME,
            evidence=GEOMETRY_RECONSTRUCTED,
            subject_client=d["shooter_client"],
            weapon=str(d["threat_type"] or ""),
            amount=float(d["closest_approach_units"] or 0.0),
            source=f"dodge_events.{d['method']}"))

    views = tuple((int(s[0]) * 1000, float(s[1]), float(s[2]))
                  for s in json.loads(view["samples"])) if view else ()

    derived = derive(attrs, track, events)
    return DemoTruthTimeline(
        frag_id=int(frag["id"]), hero_demo_us=hero_us, hero_kind=et.MY_FRAG,
        weapon=weapon, victim_client=frag["victim_client"],
        round_index=frag["round"],
        events=tuple(sorted(events, key=lambda e: e.demo_us)),
        projectile=track, view_samples=views, derived=derived)


def derive(attrs: dict[str, Any], track: ProjectileTrack | None,
           events: Sequence[DemoEvent]) -> tuple[tuple[str, Any], ...]:
    """Deterministic projections from game truth. Never from media."""
    out: dict[str, Any] = {}
    for src, dst in (("killer_speed", "ATTACKER_SPEED"),
                     ("victim_speed", "VICTIM_SPEED"),
                     ("distance", "ENGAGEMENT_DISTANCE"),
                     ("flick_degrees", "FLICK_DEGREES"),
                     ("deg_per_sec", "FLICK_DEG_PER_SEC"),
                     ("victim_air_height", "VICTIM_AIR_HEIGHT"),
                     ("dodge_min_closest_approach_units", "DODGE_CLEARANCE"),
                     ("dodge_near_miss_count", "DODGE_NEAR_MISS_COUNT"),
                     ("visibility_ms", "TARGET_VISIBLE_MS")):
        if attrs.get(src) is not None:
            out[dst] = attrs[src]
    if attrs.get("killer_speed") is not None and attrs.get("victim_speed") is not None:
        out["RELATIVE_SPEED"] = round(float(attrs["killer_speed"])
                                      + float(attrs["victim_speed"]), 1)
    if track is not None:
        out["PROJECTILE_FLIGHT_US"] = track.flight_us
        out["PROJECTILE_DISTANCE"] = track.distance_units
        if track.speed_units_per_s is not None:
            out["PROJECTILE_SPEED"] = track.speed_units_per_s
    contacts = [e for e in events if e.kind == et.MY_LG_CONTACT]
    if contacts:
        out["CONTACT_COUNT"] = len(contacts)
        dealt = [e.amount for e in contacts if e.amount is not None]
        if dealt:
            out["DAMAGE_LEDGER"] = round(sum(dealt), 1)
        out["CONTACT_SPAN_US"] = contacts[-1].demo_us - contacts[0].demo_us
        hero = next((e.demo_us for e in events if e.kind == et.MY_FRAG), None)
        if hero is not None:
            out["LAST_CONTACT_TO_FRAG_US"] = hero - contacts[-1].demo_us
    received = [e for e in events if e.kind == et.MY_DAMAGE_RECEIVED]
    if received:
        out["DAMAGE_RECEIVED"] = round(
            sum(e.amount for e in received if e.amount is not None), 1)
    return tuple(sorted(out.items()))


# ── coverage audit ──────────────────────────────────────────────────────────

COMPLETE = "COMPLETE"
PARTIAL = "PARTIAL"
MISSING = "MISSING"

# Above this share of frags a stream counts as complete.
COMPLETE_AT = 0.95
PARTIAL_AT = 0.02


def coverage_audit(db_path: Path | None = None) -> dict[str, Any]:
    """What the permanent caches already answer, and what they do not.

    This exists so that "we need a new parser" is a conclusion rather than an
    assumption. Re-mining 4,292 demos to recover a field that is already
    cached would be the most expensive possible way to learn nothing.
    """
    path = Path(db_path or RECOGNITION_DB)
    checks = {
        "FRAG_EVENT": "SELECT COUNT(*) FROM recognized_frags WHERE "
                      "server_time_ms IS NOT NULL AND weapon_name IS NOT NULL",
        "SEMANTIC_CLASSES": "SELECT COUNT(*) FROM recognized_frags WHERE "
                            "classes IS NOT NULL AND classes != '[]'",
        "DERIVED_NUMERICS": "SELECT COUNT(*) FROM recognized_frags WHERE "
                            "attributes IS NOT NULL AND attributes != '{}'",
        "LG_CONTACT_SERIES": "SELECT COUNT(*) FROM recognized_frags f JOIN "
                             "recognition_lg_engagements e ON "
                             "e.demo_name=f.demo_name AND "
                             "e.server_time_ms=f.server_time_ms",
        "PROJECTILE_PATH": "SELECT COUNT(*) FROM recognized_frags f JOIN "
                           "recognition_projectile_paths p ON "
                           "p.demo_name=f.demo_name AND "
                           "p.server_time_ms=f.server_time_ms",
        "VIEW_TIMESERIES": "SELECT COUNT(*) FROM recognized_frags f JOIN "
                           "recognition_view_timeseries v ON "
                           "v.demo_name=f.demo_name AND "
                           "v.server_time_ms=f.server_time_ms",
        "DODGE_GEOMETRY": "SELECT COUNT(*) FROM recognized_frags f JOIN "
                          "recognition_dodge_events d ON "
                          "d.demo_name=f.demo_name AND "
                          "d.kill_anchor_ms=f.server_time_ms",
        "VISIBILITY": "SELECT COUNT(*) FROM recognized_frags f JOIN "
                      "stage2_visibility s ON s.demo_name=f.demo_name AND "
                      "s.server_time_ms=f.server_time_ms",
    }
    with sqlite3.connect(path) as db:
        total = db.execute("SELECT COUNT(*) FROM recognized_frags").fetchone()[0]
        rows = {}
        for name, sql in checks.items():
            try:
                have = db.execute(sql).fetchone()[0]
            except sqlite3.Error:
                have = 0
            share = (have / total) if total else 0.0
            rows[name] = {
                "frags_with_evidence": min(have, total),
                "share": round(min(share, 1.0), 4),
                "status": (COMPLETE if share >= COMPLETE_AT else
                           PARTIAL if share >= PARTIAL_AT else MISSING)}
    return {"protocol": PROTOCOL, "reader": DEMO_TRUTH_VERSION,
            "total_frags": total, "streams": rows,
            "note": "shares are of recognised frags; a PARTIAL stream is "
                    "present for some frags and genuinely absent for others"}


# ── round and team truth from the enrichment tables ─────────────────────────
# dm_73 never sends a "winner" event. CS_ROUND_TIME (662) drops to -1 when a
# round ends, and CS_SCORES1/CS_SCORES2 (6/7) carry the red and blue totals.
# The winner of a round is the side whose total rose at that end. That is a
# derivation from two recorded configstrings, so it is EVENT_CONSTRAINED, and
# a round where neither total moved is reported as UNKNOWN rather than as a
# draw the demo never said happened.

ROUND_WIN = "WIN"
ROUND_LOSS = "LOSS"
ROUND_UNKNOWN = "UNKNOWN"

CS_SCORES_RED = 6
CS_SCORES_BLUE = 7
from engine.parser.protocol import ConfigString as _CS

CS_ROUND_TIME = int(_CS.ROUND_TIME)


@dataclass(frozen=True)
class RoundOutcome:
    """One round's result, from the recorder's point of view."""
    round_index: int
    end_us: int
    winner_team: str                  # RED | BLUE | UNKNOWN
    recorder_team: str                # RED | BLUE | UNKNOWN
    evidence: str = EVENT_CONSTRAINED

    @property
    def result(self) -> str:
        if ROUND_UNKNOWN in (self.winner_team, self.recorder_team):
            return ROUND_UNKNOWN
        return ROUND_WIN if self.winner_team == self.recorder_team else ROUND_LOSS

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["result"] = self.result
        return d


def round_outcomes(state_rows: Sequence[tuple[int, int, str]], *,
                   recorder_team: str,
                   attribution_window_ms: int = 3000) -> tuple[RoundOutcome, ...]:
    """Derive per-round results from (server_time_ms, cs, value) rows.

    A round ends when 662 becomes -1. The winner is whichever of 6 or 7
    increased for that round. The score string can arrive shortly BEFORE or
    AFTER the end mark, so a rise within ``attribution_window_ms`` of a mark
    is credited to that round. If both sides rose, or neither, the demo does
    not say who won, and neither do we.
    """
    rows = sorted(state_rows, key=lambda r: r[0])
    ends: list[int] = []
    rises: list[tuple[int, str]] = []       # (t_ms, side)
    red = blue = None
    for t_ms, cs, value in rows:
        v = str(value).strip().strip(chr(34))
        if cs in (CS_SCORES_RED, CS_SCORES_BLUE) and v.lstrip("-").isdigit():
            n = int(v)
            if cs == CS_SCORES_RED:
                if red is not None and n > red:
                    rises.append((int(t_ms), "RED"))
                red = n
            else:
                if blue is not None and n > blue:
                    rises.append((int(t_ms), "BLUE"))
                blue = n
        elif cs == CS_ROUND_TIME and v == "-1":
            ends.append(int(t_ms))
    team = recorder_team if recorder_team in ("RED", "BLUE") else ROUND_UNKNOWN
    out: list[RoundOutcome] = []
    consumed: set[int] = set()          # rises a settled round already accounts for
    first: list[str] = []
    for end_ms in ends:
        window = [i for i, (t, _) in enumerate(rises)
                  if abs(t - end_ms) <= attribution_window_ms]
        sides = {rises[i][1] for i in window}
        if len(sides) == 1:
            first.append(next(iter(sides)))
            consumed.update(window)
        else:
            # Two sides rising is a CONFLICT, not a gap: the demo is genuinely
            # ambiguous and no later evidence may cast the deciding vote.
            first.append(ROUND_UNKNOWN if not sides else CONFLICTED)
    for index, (end_ms, winner) in enumerate(zip(ends, first), 1):
        if winner is ROUND_UNKNOWN:
            winner = _recover_bounded(index - 1, ends, rises, consumed)
        elif winner == CONFLICTED:
            winner = ROUND_UNKNOWN
        out.append(RoundOutcome(index, end_ms * 1000, winner, team))
    return tuple(out)


CONFLICTED = "CONFLICTED"            # internal: both sides rose in the window
RECOVERY_BOUNDED_BY_NEIGHBOURS = "BOUNDED_BY_NEIGHBOURING_ROUNDS"
BOUNDED_RECOVERY_TAIL_MS = 120_000   # the last round has no next round to bound it


def _recover_bounded(pos: int, ends: Sequence[int],
                     rises: Sequence[tuple[int, str]],
                     consumed: set[int]) -> str:
    """Second pass for a round the fixed window could not attribute at all.

    A score can land well before or well after its own end mark. The bound
    that is always true is the neighbouring rounds: a rise between the
    previous round's end and the next round's end can only belong to this one
    or to a round that already accounted for it. Rises a settled round
    consumed are excluded, so nothing that was attributed changes; exactly one
    remaining side is a recovery, anything else stays UNKNOWN.
    """
    lo = ends[pos - 1] if pos > 0 else -1
    hi = ends[pos + 1] if pos + 1 < len(ends) else ends[pos] + BOUNDED_RECOVERY_TAIL_MS
    sides = {side for i, (t, side) in enumerate(rises)
             if i not in consumed and lo < t <= hi}
    return next(iter(sides)) if len(sides) == 1 else ROUND_UNKNOWN


def load_round_outcomes(content_hash: str, recorder_client: int, *,
                        db_path: Path | None = None) -> tuple[RoundOutcome, ...]:
    """Read the enrichment tables for one demo. Empty if not enriched."""
    path = Path(db_path or RECOGNITION_DB)
    with sqlite3.connect(path) as db:
        try:
            team_row = db.execute(
                "SELECT team FROM player_teams_v1 WHERE content_hash=? AND client=?",
                (content_hash, recorder_client)).fetchone()
            rows = db.execute(
                "SELECT server_time_ms, cs, value FROM round_state_v1 "
                "WHERE content_hash=? AND cs IN (?,?,?)",
                (content_hash, CS_SCORES_RED, CS_SCORES_BLUE, CS_ROUND_TIME)
            ).fetchall()
        except sqlite3.OperationalError:
            return ()
    team = str(team_row[0]).upper() if team_row and team_row[0] else ROUND_UNKNOWN
    if team not in ("RED", "BLUE"):
        team = ROUND_UNKNOWN
    return round_outcomes(rows, recorder_team=team)


def outcome_at(outcomes: Sequence[RoundOutcome], demo_us: int) -> RoundOutcome | None:
    """The round a moment belongs to: the first round ending at or after it."""
    for o in sorted(outcomes, key=lambda x: x.end_us):
        if o.end_us >= demo_us:
            return o
    return None
