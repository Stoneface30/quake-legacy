"""Who actually teleported -- from constrained evidence, never proximity alone.

WHAT THE DEMO RECORDS. A teleport fires two temp entities: EV_PLAYER_TELEPORT_OUT
at the player's old position and EV_PLAYER_TELEPORT_IN at the new one
(g_misc.c TeleportPlayer). Measured on real Quake Live demos, those temp
entities carry ONLY a position and an eType -- the clientNum the id source
sets is not transmitted. So the demo says a teleport happened and exactly
where, but not to whom.

WHY PROXIMITY IS NOT IDENTITY. Teleporters are FIXED map entities: a
trigger_teleport brush targeting a target_position / misc_teleporter_dest.
Every player who uses one arrives at the same coordinates. On asylum three
players went through the one teleporter inside 275 ms and all three arrived
at (-776, -32, 680). "Nearest player to the destination" is ambiguous there
by construction, and picking the closest would attribute all three to
whoever happened to be standing nearest.

WHAT IDENTIFIES A PLAYER. One client whose last recorded position before the
tick sits at the OUT point AND whose first recorded position after it sits at
the IN point. Both ends, one client, nobody else -- that is a unique match.
Anything less is AMBIGUOUS or UNKNOWN, and both are valid answers.

RESPAWNS. Quake also fires EV_PLAYER_TELEPORT_IN when a player spawns
(g_client.c ClientSpawn), which is why teleport_in outnumbers teleport_out
roughly three to one in the corpus. An IN with no OUT partner at the same
tick is a SPAWN, not a trip through a teleporter, and is classified as such
rather than attributed as movement.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import math
from typing import Any, Iterable, Sequence

ATTRIBUTION_VERSION = "teleport-attribution-v1.0.0"

# ── outcomes ────────────────────────────────────────────────────────────────

CONFIRMED = "TELEPORT_PLAYER_CONFIRMED"
AMBIGUOUS = "AMBIGUOUS"
UNKNOWN = "UNKNOWN"

# ── evidence components (kept individually; never collapsed to one score) ────

EV_SOURCE_AGREEMENT = "SOURCE_AGREEMENT"          # last position before ≈ OUT point
EV_DEST_AGREEMENT = "DESTINATION_AGREEMENT"       # first position after ≈ IN point
EV_STATE_DISCONTINUITY = "STATE_DISCONTINUITY"    # the move is non-physical for the gap
EV_BSP_PAIR = "BSP_TELEPORTER_PAIR"               # map declares this source→dest pair
EV_PAIRED_EVENT = "PAIRED_OUT_IN"                 # OUT and IN allocated on the same tick
EV_UNIQUE_CANDIDATE = "UNIQUE_CANDIDATE"          # exactly one client satisfies both ends
EV_SNAPSHOT_PRESENCE = "SNAPSHOT_PRESENCE"        # the client was actually being received

# Tolerances. A player's recorded entity position is the trajectory base at the
# snapshot, so it is a few units off the exact event origin, and the sample may
# be one server frame away from the teleport tick.
SOURCE_RADIUS = 90.0        # units between the last position and the OUT point
DEST_RADIUS = 90.0          # units between the first position after and the IN point
SAMPLE_WINDOW_MS = 200      # how far either side a position sample may sit
MIN_DISCONTINUITY = 200.0   # a teleport moves further than running ever could
PLAYER_RUN_SPEED = 1000.0   # generous cap (u/s) for "could have run there"


@dataclass(frozen=True)
class PositionSample:
    """One recorded position of one client at one tick."""
    t_ms: int
    client: int
    pos: tuple[float, float, float]


@dataclass(frozen=True)
class TeleportTransit:
    """An OUT/IN pair: one trip through a fixed map teleporter."""
    t_ms: int
    out_pos: tuple[float, float, float]
    in_pos: tuple[float, float, float]
    out_entity: int | None = None
    in_entity: int | None = None
    teleporter_target: str = ""          # the map's own target name, when matched

    @property
    def distance(self) -> float:
        return math.dist(self.out_pos, self.in_pos)


@dataclass(frozen=True)
class SpawnIn:
    """A teleport_in with no OUT partner: a respawn, not a transit."""
    t_ms: int
    pos: tuple[float, float, float]
    entity: int | None = None
    near_spawn_point_u: float | None = None


@dataclass(frozen=True)
class CandidateEvidence:
    """Why one client is or is not the player who teleported."""
    client: int
    source_distance_u: float | None
    dest_distance_u: float | None
    before_t_ms: int | None
    after_t_ms: int | None
    jump_distance_u: float | None
    implied_speed_u_s: float | None

    @property
    def source_ok(self) -> bool:
        return self.source_distance_u is not None and self.source_distance_u <= SOURCE_RADIUS

    @property
    def dest_ok(self) -> bool:
        return self.dest_distance_u is not None and self.dest_distance_u <= DEST_RADIUS

    @property
    def both_ends(self) -> bool:
        return self.source_ok and self.dest_ok

    @property
    def discontinuous(self) -> bool:
        return (self.jump_distance_u is not None
                and self.jump_distance_u >= MIN_DISCONTINUITY
                and (self.implied_speed_u_s or 0.0) > PLAYER_RUN_SPEED)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(source_ok=self.source_ok, dest_ok=self.dest_ok,
                 both_ends=self.both_ends, discontinuous=self.discontinuous)
        return d


@dataclass(frozen=True)
class TeleportAttribution:
    """The answer plus the evidence that produced it."""
    transit: TeleportTransit
    outcome: str
    client: int | None
    components: tuple[str, ...]
    candidates: tuple[CandidateEvidence, ...]
    reason: str
    nearest_at_destination: int | None = None   # what proximity ALONE would have said
    version: str = ATTRIBUTION_VERSION

    @property
    def proximity_would_disagree(self) -> bool:
        """True when picking the client nearest the destination would have
        given a different answer than the constrained match."""
        return (self.nearest_at_destination is not None
                and self.nearest_at_destination != self.client)

    def to_dict(self) -> dict[str, Any]:
        return {"transit": asdict(self.transit), "outcome": self.outcome,
                "client": self.client, "components": list(self.components),
                "candidates": [c.to_dict() for c in self.candidates],
                "reason": self.reason,
                "nearest_at_destination": self.nearest_at_destination,
                "proximity_would_disagree": self.proximity_would_disagree,
                "version": self.version}


# ── pairing events into transits ────────────────────────────────────────────

def pair_transits(events: Sequence[dict[str, Any]], *,
                  teleporters: Sequence[Any] = (),
                  spawn_points: Sequence[Sequence[float]] = (),
                  ) -> tuple[list[TeleportTransit], list[SpawnIn]]:
    """Split teleport events into transits (OUT+IN) and spawns (IN alone).

    G_TempEntity allocates the OUT entity and then the IN entity inside one
    TeleportPlayer call, so a transit is an OUT and an IN on the same server
    tick with adjacent entity numbers. Several players may transit on one
    tick; adjacency keeps their pairs apart.
    """
    outs = [e for e in events if e.get("type") == "teleport_out"]
    ins = [e for e in events if e.get("type") == "teleport_in"]
    dest_of = {}
    for t in teleporters:
        dest_of[tuple(t.dest)] = t
    used_in: set[int] = set()
    transits: list[TeleportTransit] = []
    for o in sorted(outs, key=lambda e: (e["server_time_ms"], e.get("entity_num") or 0)):
        t_ms = o["server_time_ms"]
        oe = o.get("entity_num")
        same_tick = [e for i, e in enumerate(ins)
                     if e["server_time_ms"] == t_ms and id(e) not in used_in]
        if not same_tick:
            continue
        # nearest allocation above the OUT entity wins; wrap to the first
        # remaining IN when entity numbers are unavailable.
        def rank(e):
            ie = e.get("entity_num")
            if oe is None or ie is None:
                return (2, 0)
            return (0, ie - oe) if ie > oe else (1, oe - ie)
        partner = min(same_tick, key=rank)
        used_in.add(id(partner))
        in_pos = (_f(partner.get("pos_x")), _f(partner.get("pos_y")), _f(partner.get("pos_z")))
        out_pos = (_f(o.get("pos_x")), _f(o.get("pos_y")), _f(o.get("pos_z")))
        if None in in_pos or None in out_pos:
            continue
        tp = _nearest_teleporter(in_pos, teleporters)
        transits.append(TeleportTransit(t_ms, out_pos, in_pos, oe,
                                        partner.get("entity_num"),
                                        tp.target if tp else ""))
    spawns: list[SpawnIn] = []
    for e in ins:
        if id(e) in used_in:
            continue
        pos = (_f(e.get("pos_x")), _f(e.get("pos_y")), _f(e.get("pos_z")))
        if None in pos:
            continue
        near = min((math.dist(pos, tuple(s)[:3]) for s in spawn_points), default=None)
        spawns.append(SpawnIn(e["server_time_ms"], pos, e.get("entity_num"), near))
    return transits, spawns


def _f(v: Any) -> float | None:
    return None if v is None else float(v)


def _nearest_teleporter(point: Sequence[float], teleporters: Sequence[Any],
                        radius: float = 64.0):
    best, best_d = None, radius
    for t in teleporters:
        d = t.dest_distance(point)
        if d <= best_d:
            best, best_d = t, d
    return best


# ── attribution ─────────────────────────────────────────────────────────────

def attribute(transit: TeleportTransit, samples: Iterable[PositionSample], *,
              teleporters: Sequence[Any] = (),
              window_ms: int = SAMPLE_WINDOW_MS) -> TeleportAttribution:
    """Attribute one transit to a client, or refuse to.

    Every client that was being received near the tick is evaluated at BOTH
    ends. Only a single client supported at both ends is an answer.
    """
    by_client: dict[int, list[PositionSample]] = {}
    for s in samples:
        if abs(s.t_ms - transit.t_ms) <= window_ms:
            by_client.setdefault(s.client, []).append(s)
    candidates: list[CandidateEvidence] = []
    for client, rows in sorted(by_client.items()):
        rows.sort(key=lambda s: s.t_ms)
        # The event fires during the server frame and the entity state stamped
        # with that tick ALREADY carries the arrival. So "before" is strictly
        # the previous frame; letting one sample serve as both ends makes every
        # client look continuous and nothing is ever attributable.
        before = [s for s in rows if s.t_ms < transit.t_ms]
        after = [s for s in rows if s.t_ms >= transit.t_ms]
        b = before[-1] if before else None
        a = after[0] if after else None
        jump = math.dist(b.pos, a.pos) if (b and a) else None
        dt_s = ((a.t_ms - b.t_ms) / 1000.0) if (b and a) else None
        speed = (jump / dt_s) if (jump is not None and dt_s and dt_s > 0) else None
        candidates.append(CandidateEvidence(
            client=client,
            source_distance_u=(math.dist(b.pos, transit.out_pos) if b else None),
            dest_distance_u=(math.dist(a.pos, transit.in_pos) if a else None),
            before_t_ms=(b.t_ms if b else None), after_t_ms=(a.t_ms if a else None),
            jump_distance_u=jump, implied_speed_u_s=speed))

    supported = [c for c in candidates if c.both_ends]
    nearest_dest = min((c for c in candidates if c.dest_distance_u is not None),
                       key=lambda c: c.dest_distance_u, default=None)
    nearest_client = nearest_dest.client if nearest_dest else None

    components: list[str] = []
    if transit.out_entity is not None and transit.in_entity is not None:
        components.append(EV_PAIRED_EVENT)
    if transit.teleporter_target:
        components.append(EV_BSP_PAIR)
    if candidates:
        components.append(EV_SNAPSHOT_PRESENCE)

    if len(supported) == 1:
        c = supported[0]
        components += [EV_SOURCE_AGREEMENT, EV_DEST_AGREEMENT, EV_UNIQUE_CANDIDATE]
        if c.discontinuous:
            components.append(EV_STATE_DISCONTINUITY)
        reason = (f"client {c.client} was {c.source_distance_u:.0f}u from the exit "
                  f"point before the tick and {c.dest_distance_u:.0f}u from the "
                  f"arrival point after it; no other received client satisfies "
                  f"both ends")
        return TeleportAttribution(transit, CONFIRMED, c.client, tuple(components),
                                   tuple(candidates), reason, nearest_client)
    if len(supported) > 1:
        who = ", ".join(str(c.client) for c in supported)
        return TeleportAttribution(
            transit, AMBIGUOUS, None, tuple(components), tuple(candidates),
            f"clients {who} are each supported at both ends; the demo does not "
            f"say which one made this trip", nearest_client)
    partial = [c for c in candidates if c.source_ok or c.dest_ok]
    detail = ("no received client sits at both the exit and the arrival point"
              if partial else
              "no client position was being received within the window")
    return TeleportAttribution(transit, UNKNOWN, None, tuple(components),
                               tuple(candidates), detail, nearest_client)


def attribute_all(transits: Sequence[TeleportTransit],
                  samples: Sequence[PositionSample], *,
                  teleporters: Sequence[Any] = ()
                  ) -> list[TeleportAttribution]:
    return [attribute(t, samples, teleporters=teleporters) for t in transits]


def samples_from_entities(rows: Iterable[dict[str, Any]]) -> list[PositionSample]:
    """Position samples from the parser's per-entity snapshot track. Only rows
    that carry a client number and a full position become evidence."""
    out: list[PositionSample] = []
    for r in rows:
        c = r.get("client_num")
        x, y, z = r.get("origin_x"), r.get("origin_y"), r.get("origin_z")
        if c is None or None in (x, y, z):
            continue
        out.append(PositionSample(int(r["server_time_ms"]), int(c),
                                  (float(x), float(y), float(z))))
    return out


def samples_from_snapshots(rows: Iterable[dict[str, Any]],
                           recorder_client: int | None = None
                           ) -> list[PositionSample]:
    """Position samples for the RECORDER, from playerstate.

    A client never receives its own entity in a snapshot -- its position lives
    in playerState. Without this the recorder is invisible to attribution and
    its own teleports can never be confirmed, which is exactly how they were
    missing from the corpus.
    """
    out: list[PositionSample] = []
    for r in rows:
        c = r.get("client_num", recorder_client)
        x, y, z = r.get("origin_x"), r.get("origin_y"), r.get("origin_z")
        if c is None or None in (x, y, z):
            continue
        out.append(PositionSample(int(r["server_time_ms"]), int(c),
                                  (float(x), float(y), float(z))))
    return out


def all_samples(entities: Iterable[dict[str, Any]],
                snapshots: Iterable[dict[str, Any]],
                recorder_client: int | None = None) -> list[PositionSample]:
    """Every client's recorded positions: remote players from the entity
    track, the recorder from playerstate. Sorted, duplicates kept out."""
    seen: set[tuple[int, int]] = set()
    out: list[PositionSample] = []
    for s in (samples_from_entities(entities)
              + samples_from_snapshots(snapshots, recorder_client)):
        key = (s.t_ms, s.client)
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    out.sort(key=lambda s: (s.t_ms, s.client))
    return out


def summary(attributions: Sequence[TeleportAttribution]) -> dict[str, Any]:
    counts = {CONFIRMED: 0, AMBIGUOUS: 0, UNKNOWN: 0}
    disagree = 0
    for a in attributions:
        counts[a.outcome] = counts.get(a.outcome, 0) + 1
        if a.proximity_would_disagree:
            disagree += 1
    return {"total": len(attributions), **counts,
            "proximity_would_disagree": disagree, "version": ATTRIBUTION_VERSION}
