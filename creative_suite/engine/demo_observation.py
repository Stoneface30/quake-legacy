"""What the recorder saw, kept separate from what happened.

WHY THIS EXISTS. A Quake client demo is not a recording of the match. It is a
recording of the network messages that reached one client. The server builds
each snapshot from that client's viewpoint and filters entities through BSP
area and PVS visibility before transmitting, so state belonging to a remote
player in another part of the map may never be sent at all. The demo then
preserves exactly what arrived and nothing else.

The consequence is a trap that looks like data:

    SERVER WORLD STATE
            |  per-client snapshot selection
            |  BSP area / PVS / broadcast flags
            v
    NETWORK MESSAGE TO ONE CLIENT
            v
    THE DEMO

Everything absent from that last line has two possible explanations, and they
are not equally likely to be the one we want:

    it did not happen        <- a claim about the world
    it was not transmitted   <- a claim about one viewpoint

Nothing in a client demo can tell those apart on its own. So this module
holds the second reading as the default and makes the first one something a
caller has to earn.

The teleport closeout is what made this concrete. On one map, 906 real
departures were recorded and not a single arrival, because the destination
sits far enough away in the map's topology that the recorder was never sent
the remote player's arrival. The teleport was complete. Our view of it was
not. Distance correlates with that but does not cause it -- another map moves
players nearly as far and records both ends -- so the honest classification
is "unobserved", never "unobserved because of PVS", unless something actually
proves the cause.

    THE DEMO IS AN OBSERVER'S RECORD, NOT THE SERVER'S HISTORY.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Sequence

OBSERVATION_VERSION = "demo-observation-v1.0.0"
MS = 1000

# ── where a piece of evidence came from ─────────────────────────────────────
# These are not equally strong and must never be averaged together. The
# server does not need to send the recorder its own entity, because the
# client regenerates it from playerState, so self evidence is continuous in a
# way remote evidence structurally cannot be.

SELF_PLAYERSTATE = "SELF_PLAYERSTATE"
REMOTE_SNAPSHOT_ENTITY = "REMOTE_SNAPSHOT_ENTITY"
MAP_GEOMETRY = "MAP_GEOMETRY"            # BSP: true of the map, not of a player
SERVER_BROADCAST = "SERVER_BROADCAST"    # reaches every client regardless of view
EVIDENCE_SOURCES = (SELF_PLAYERSTATE, REMOTE_SNAPSHOT_ENTITY, MAP_GEOMETRY,
                    SERVER_BROADCAST)

# Whether absence of this kind of evidence can ever mean the thing did not
# happen. Only for evidence the recorder would necessarily have received.
ABSENCE_IS_INFORMATIVE = {
    SELF_PLAYERSTATE: True,
    SERVER_BROADCAST: True,
    REMOTE_SNAPSHOT_ENTITY: False,
    MAP_GEOMETRY: False,
}


# ── how well one thing was observed ─────────────────────────────────────────

OBSERVED = "OBSERVED"
PARTIALLY_OBSERVED = "PARTIALLY_OBSERVED"
UNOBSERVED = "UNOBSERVED"
RECONSTRUCTABLE = "RECONSTRUCTABLE"      # unobserved, but constrained enough to derive
AMBIGUOUS = "AMBIGUOUS"                  # observed, but which entity is unclear
OBSERVATION_STATES = (OBSERVED, PARTIALLY_OBSERVED, UNOBSERVED,
                      RECONSTRUCTABLE, AMBIGUOUS)


# ── gaps in a remote entity's record ────────────────────────────────────────

OBSERVED_CONTINUOUSLY = "OBSERVED_CONTINUOUSLY"
OBSERVATION_GAP_SHORT = "OBSERVATION_GAP_SHORT"
OBSERVATION_GAP_PVS = "OBSERVATION_GAP_PVS"      # only when actually proven
OBSERVATION_GAP_UNKNOWN = "OBSERVATION_GAP_UNKNOWN"
REOBSERVED = "REOBSERVED"
GAP_CLASSES = (OBSERVED_CONTINUOUSLY, OBSERVATION_GAP_SHORT,
               OBSERVATION_GAP_PVS, OBSERVATION_GAP_UNKNOWN, REOBSERVED)

# Below this, a gap is short enough that ordinary snapshot jitter explains it
# and physics can usually bridge it. A judgement, not a measurement.
SHORT_GAP_US = 250_000


@dataclass(frozen=True)
class ObservationGap:
    """A stretch where a remote entity was not in the recorder's snapshots.

    The gap is a fact about the recording. What the entity was doing inside
    it is not in this demo, and seeing the entity again afterwards does not
    fill it in.
    """
    entity: int
    last_observed_us: int | None
    next_observed_us: int | None
    source: str = REMOTE_SNAPSHOT_ENTITY
    proven_cause: str = ""      # only set when something actually proves it

    def __post_init__(self) -> None:
        if self.source not in EVIDENCE_SOURCES:
            raise ValueError(f"unknown evidence source {self.source!r}")
        if (self.last_observed_us is not None
                and self.next_observed_us is not None
                and self.next_observed_us < self.last_observed_us):
            raise ValueError("a gap cannot end before it starts")

    @property
    def duration_us(self) -> int | None:
        if self.last_observed_us is None or self.next_observed_us is None:
            return None
        return self.next_observed_us - self.last_observed_us

    @property
    def gap_class(self) -> str:
        d = self.duration_us
        if d is None:
            return OBSERVATION_GAP_UNKNOWN
        if d <= 0:
            return OBSERVED_CONTINUOUSLY
        if self.proven_cause == "PVS":
            return OBSERVATION_GAP_PVS
        if d <= SHORT_GAP_US:
            return OBSERVATION_GAP_SHORT
        return OBSERVATION_GAP_UNKNOWN

    @property
    def bridgeable(self) -> bool:
        """Whether physics may reasonably span this. Never a claim that it
        did; only that a derivation would not be a fantasy."""
        d = self.duration_us
        return d is not None and 0 < d <= SHORT_GAP_US

    def covers(self, us: int) -> bool:
        if self.last_observed_us is None or self.next_observed_us is None:
            return False
        return self.last_observed_us < us < self.next_observed_us

    def what_we_know(self) -> str:
        d = self.duration_us
        if d is None or d <= 0:
            return "no gap"
        return (f"entity {self.entity} was not in the recorder's snapshots for "
                f"{d/1000:.0f} ms. What it did in that time is not in this "
                f"demo, and its reappearance afterwards is not evidence about "
                f"the gap")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(duration_us=self.duration_us, gap_class=self.gap_class,
                 bridgeable=self.bridgeable)
        return d


def gaps_from_samples(entity: int, sample_times_us: Sequence[int],
                      *, source: str = REMOTE_SNAPSHOT_ENTITY,
                      tick_us: int = 50_000) -> list[ObservationGap]:
    """Every stretch where this entity stopped appearing in snapshots."""
    ts = sorted(int(t) for t in sample_times_us)
    out: list[ObservationGap] = []
    for a, b in zip(ts, ts[1:]):
        if b - a > tick_us * 2:
            out.append(ObservationGap(entity, a, b, source))
    return out


# ── the negative-evidence gate ──────────────────────────────────────────────

def may_conclude_absence(source: str, *, would_have_been_transmitted: bool = False,
                         reason: str = "") -> tuple[bool, str]:
    """Whether "we did not record it" may be read as "it did not happen".

    The only honest yes comes from evidence the recorder would necessarily
    have received: its own playerstate, or something the server broadcasts to
    everyone. For a remote entity the answer is no unless the caller can show
    the thing would have been transmitted -- and showing that is a real
    argument about map topology and snapshot rules, not an assumption.
    """
    if source not in EVIDENCE_SOURCES:
        raise ValueError(f"unknown evidence source {source!r}")
    if ABSENCE_IS_INFORMATIVE[source]:
        return (True, f"{source} reaches the recorder regardless of where it "
                      f"is looking, so its absence is informative")
    if would_have_been_transmitted:
        if not reason.strip():
            raise ValueError(
                "claiming a remote entity would have been transmitted is an "
                "argument about topology and snapshot rules; it must be "
                "stated, not assumed")
        return (True, reason)
    return (False, f"{source} is filtered by the recorder's viewpoint, so its "
                   f"absence means it was not observed, never that it did not "
                   f"happen")


# ── teleports, as truth and as observation ──────────────────────────────────

BOTH_ENDPOINTS_OBSERVED = "BOTH_ENDPOINTS_OBSERVED"
SOURCE_ONLY_OBSERVED = "SOURCE_ONLY_OBSERVED"
DESTINATION_ONLY_OBSERVED = "DESTINATION_ONLY_OBSERVED"
NEITHER_ENDPOINT_OBSERVED = "NEITHER_ENDPOINT_OBSERVED"
TELEPORT_OBSERVATIONS = (BOTH_ENDPOINTS_OBSERVED, SOURCE_ONLY_OBSERVED,
                         DESTINATION_ONLY_OBSERVED, NEITHER_ENDPOINT_OBSERVED)

# Transition ports. A scene's exit and another scene's entry do not have to
# come from one fully observed event, which is exactly why a one-ended
# observation is still worth keeping.
TELEPORT_EXIT_PORT = "TELEPORT_EXIT_PORT"
TELEPORT_ENTRY_PORT = "TELEPORT_ENTRY_PORT"
CONFIRMED_TELEPORT_PAIR = "CONFIRMED_TELEPORT_PAIR"


@dataclass(frozen=True)
class TeleportTruth:
    """What the map says, which is true whether or not anyone was looking."""
    target: str
    source_bounds: tuple[float, ...] | None = None
    dest: tuple[float, float, float] | None = None
    source_kind: str = "trigger_teleport"

    @property
    def evidence_source(self) -> str:
        return MAP_GEOMETRY

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TeleportObservation:
    """How much of one trip this recorder actually saw.

    The distinction that matters: a departure with no arrival is a complete
    teleport we half-watched, not half a teleport.
    """
    t_ms: int
    observation: str
    out_pos: tuple[float, float, float] | None = None
    in_pos: tuple[float, float, float] | None = None
    truth: TeleportTruth | None = None
    attribution: str = "UNKNOWN"
    client: int | None = None

    def __post_init__(self) -> None:
        if self.observation not in TELEPORT_OBSERVATIONS:
            raise ValueError(f"unknown teleport observation {self.observation!r}")
        if self.observation == BOTH_ENDPOINTS_OBSERVED and (
                self.out_pos is None or self.in_pos is None):
            raise ValueError(
                "both endpoints observed, but one of them has no position")
        if self.observation == SOURCE_ONLY_OBSERVED and self.in_pos is not None:
            raise ValueError(
                "a source-only observation must not carry an arrival position; "
                "the map may say where the teleporter leads, but that is not "
                "the same as having seen the player get there")

    @property
    def arrival_observed(self) -> bool:
        return self.observation in (BOTH_ENDPOINTS_OBSERVED,
                                    DESTINATION_ONLY_OBSERVED)

    @property
    def departure_observed(self) -> bool:
        return self.observation in (BOTH_ENDPOINTS_OBSERVED,
                                    SOURCE_ONLY_OBSERVED)

    @property
    def is_complete_transit(self) -> bool:
        """Whether this record may be presented as one witnessed trip."""
        return self.observation == BOTH_ENDPOINTS_OBSERVED

    @property
    def known_destination(self) -> tuple[float, float, float] | None:
        """Where the map says this teleporter leads.

        Map truth. It is not where we saw anybody arrive, and callers that
        confuse the two will invent a player state that was never recorded.
        """
        return self.truth.dest if self.truth else None

    def ports(self) -> tuple[str, ...]:
        """What this observation can legitimately offer an edit.

        A half-seen teleport is still a real departure or a real arrival, and
        either one is a genuine place to leave or enter a scene.
        """
        if self.observation == BOTH_ENDPOINTS_OBSERVED:
            return (CONFIRMED_TELEPORT_PAIR, TELEPORT_EXIT_PORT,
                    TELEPORT_ENTRY_PORT)
        if self.observation == SOURCE_ONLY_OBSERVED:
            return (TELEPORT_EXIT_PORT,)
        if self.observation == DESTINATION_ONLY_OBSERVED:
            return (TELEPORT_ENTRY_PORT,)
        return ()

    def what_we_know(self) -> str:
        if self.observation == BOTH_ENDPOINTS_OBSERVED:
            return "the departure and the arrival were both recorded"
        if self.observation == SOURCE_ONLY_OBSERVED:
            where = ("; the map says it leads to "
                     f"{self.known_destination}" if self.known_destination
                     else "")
            return ("the departure was recorded and the arrival was not sent "
                    "to this recorder" + where + ". The player did arrive; we "
                    "did not see it")
        if self.observation == DESTINATION_ONLY_OBSERVED:
            return ("the arrival was recorded and the departure was not sent "
                    "to this recorder")
        return "neither end of this trip reached the recorder"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(is_complete_transit=self.is_complete_transit,
                 arrival_observed=self.arrival_observed,
                 departure_observed=self.departure_observed,
                 ports=list(self.ports()),
                 what_we_know=self.what_we_know())
        return d


def coverage_is_not_activity(demos_with_records: int, demos_scanned: int
                             ) -> dict[str, Any]:
    """A reminder in executable form.

    The number of demos carrying confirmed transits is a floor on how many
    demos contain teleporting, never a measure of it. Anything that reads it
    as coverage will conclude that players stopped using a teleporter that
    they in fact used all match.
    """
    return {
        "demos_scanned": demos_scanned,
        "demos_with_confirmed_records": demos_with_records,
        "is_activity_coverage": False,
        "meaning": (f"{demos_with_records} of {demos_scanned} demos recorded "
                    f"both ends of at least one trip. The rest may contain "
                    f"any amount of teleporting whose far end was never sent "
                    f"to the recorder"),
    }
