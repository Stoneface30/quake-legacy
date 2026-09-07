"""ONE OBJECT THE REVIEWER READS.

The frontend should ask PANTHEON what a moment is, not assemble it from four
databases and hope they agree. A ReviewMoment carries what happened, where it
happened, who could see it, what a person already said about it, and what the
engine could do with it -- in one shape, with every number sourced.

It contains NO player name, nickname or identifier: a moment is a demo hash, a
client slot and a serverTime, and that is a rule of this repository rather
than a preference.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from engine.pantheon import creative_intent as CI
from engine.pantheon import possibilities as POSS


@dataclass
class PlaybackContext:
    """Enough to film or seek it, without deciding to."""
    demo_hash: str
    client: int
    server_time_ms: int
    start_ms: int
    end_ms: int

    def as_dict(self) -> dict:
        return {"demo_hash": self.demo_hash, "client": self.client,
                "server_time_ms": self.server_time_ms,
                "start_ms": self.start_ms, "end_ms": self.end_ms}


@dataclass
class MapLocation:
    map: str
    region: str | None = None
    known_geography: bool = False

    def as_dict(self) -> dict:
        return {"map": self.map, "region": self.region,
                "known_geography": self.known_geography}


@dataclass
class ReviewMoment:
    performance_id: str
    action: dict                       # what the engine read, with its evidence
    playback: PlaybackContext
    location: MapLocation
    povs: list[dict] = field(default_factory=list)
    facts: list[dict] = field(default_factory=list)
    possibilities: dict = field(default_factory=dict)
    human: list[dict] = field(default_factory=list)
    strip: dict = field(default_factory=dict)   # the compact factual line

    def as_dict(self) -> dict:
        return {"performance_id": self.performance_id, "action": self.action,
                "playback": self.playback.as_dict(),
                "location": self.location.as_dict(), "povs": self.povs,
                "facts": self.facts, "strip": self.strip,
                "possibilities": self.possibilities, "human": self.human}


NOT_DERIVABLE = "NOT_DERIVABLE"


def load(performance_id: str, *, backend: str = "PANTHEON_QUAKE_OFFSCREEN",
         profile: str = "REVIEW") -> ReviewMoment:
    m = POSS.moment(performance_id)
    if m is None:
        raise KeyError(f"no indexed moment {performance_id}")
    mp = POSS.for_moment(performance_id, backend=backend, profile=profile)

    region, known = None, False
    try:
        from engine.pantheon import geography as GEO
        known = bool(GEO.coverage(m["map"]))
    except Exception:
        known = False

    # POVs are what the demo OBSERVED, never every slot in the match.
    povs = [{"client": m["client"], "role": "actor",
             "is_recorder": bool(m["is_pov"]), "observed": True}]
    if m.get("victim") is not None:
        povs.append({"client": m["victim"], "role": "victim",
                     "is_recorder": m["victim"] == m.get("recorder_client"),
                     "observed": "OTHER_POV" in mp.truth_available})

    events = json.loads(m.get("events_json") or "[]")
    strip = {
        "weapon": m.get("weapon") or NOT_DERIVABLE,
        "outcome": m.get("outcome") or NOT_DERIVABLE,
        # Health, armour and accuracy are not on an action row. Saying so is
        # the contract: a blank field reads as zero to a human, and a wrong
        # zero is worse than an honest refusal.
        "health": NOT_DERIVABLE,
        "armour": NOT_DERIVABLE,
        "accuracy": NOT_DERIVABLE,
        "round": NOT_DERIVABLE,
        "map_region": region or (m.get("map") if known else NOT_DERIVABLE),
        "povs": len([p for p in povs if p["observed"]]),
        "observation_gap_ms": m.get("gap_ms"),
    }

    return ReviewMoment(
        performance_id=performance_id,
        action={"kind": m["kind"], "events": [e[1] for e in events],
                "samples": m["samples"], "evidence": "performance index row"},
        playback=PlaybackContext(m["demo_hash"], m["client"], m["t_ms"],
                                 m["start_ms"], m["end_ms"]),
        location=MapLocation(m["map"], region, known),
        povs=povs,
        facts=[f.as_dict() for f in mp.facts],
        possibilities=mp.as_dict(),
        human=[n.as_dict() for n in CI.notes(performance_id)],
        strip=strip)
