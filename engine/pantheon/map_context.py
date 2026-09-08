"""Where a moment happened, in words the reviewer can put on one line.

The geography layer learns a map's structure. This layer answers the only
questions the reviewer actually asks about a single frag:

    LOCATION   which region, on which height layer
    APPROACH   how the actor got there, in the seconds before

Both are read from the same recorded positions the region model was built
from. Nothing here infers, nothing here names a room, and nothing here
opens a renderer.

ON NAMES. Regions are REGION_01, REGION_02. Height layers get LOWER / MID /
UPPER because that ordering IS in the data -- it is the rank of the layer's
Z band, not a guess about architecture. What we do NOT do is print community
callouts: nobody has told us that a region is "the RA room", and inventing
that mapping would put a confident wrong word in front of the user on every
clip. If a reliable source of callouts turns up, it maps onto region ids
without any of this changing.

ON SILENCE. Every function here returns None rather than a guess. A frag on
a map with no learned geography, or at a position nobody else ever occupied,
gets no LOCATION line at all -- which reads as "not known" and is true.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engine.pantheon import map_geography as mg

from engine.pantheon import store as S

REPO_ROOT = S.PROJECT_ROOT
RECOG_DB = S.RECOG_DB

# How far back to look for the move that brought the actor here. Six seconds
# covers a jump-pad arc and a corridor; much more and "approach" becomes
# "somewhere they were earlier", which is not an approach.
APPROACH_WINDOW_MS = 6000

# How close in time a position sample must be to count as the actor's
# position AT the moment. Beyond this they have moved on.
AT_MOMENT_MS = 700

_INDEX_CACHE: dict[str, mg.MapIndex | None] = {}


def index_for(map_name: str) -> mg.MapIndex | None:
    if map_name not in _INDEX_CACHE:
        try:
            _INDEX_CACHE[map_name] = mg.load_index(map_name)
        except sqlite3.Error:
            _INDEX_CACHE[map_name] = None
    return _INDEX_CACHE[map_name]


def clear_cache() -> None:
    _INDEX_CACHE.clear()


def layer_word(index: mg.MapIndex, layer: int) -> str:
    """LOWER / MID / UPPER, from the layer's rank in height. Derived, not
    named: with two layers there is no middle, and with five there are
    three middles, so the word follows the data rather than a fixed set."""
    n = len(index.layers)
    if n <= 1:
        return "GROUND"
    if layer == 0:
        return "LOWER"
    if layer == n - 1:
        return "UPPER"
    return "MID"


@dataclass(frozen=True)
class Place:
    map: str
    region_id: str
    layer: int
    layer_word: str

    @property
    def label(self) -> str:
        return f"{self.layer_word.lower()} {self.region_id.lower()}"

    def to_dict(self) -> dict[str, Any]:
        return {"map": self.map, "region_id": self.region_id,
                "layer": self.layer, "layer_word": self.layer_word,
                "label": self.label}


@dataclass(frozen=True)
class Approach:
    kind: str                 # MOVE | JUMP_PAD | TELEPORT
    from_region: str
    travel_ms: int

    @property
    def label(self) -> str:
        if self.kind == mg.JUMP_PAD:
            return f"jump pad from {self.from_region.lower()}"
        if self.kind == mg.TELEPORT:
            return f"teleport from {self.from_region.lower()}"
        return f"from {self.from_region.lower()}"

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "from_region": self.from_region,
                "travel_ms": self.travel_ms, "label": self.label}


def _ro(db: Path = RECOG_DB) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def place_of(map_name: str, x: float, y: float, z: float) -> Place | None:
    idx = index_for(map_name)
    if idx is None:
        return None
    rid = idx.region_at(x, y, z)
    if rid is None:
        return None
    region = idx.regions[rid]
    return Place(map_name, rid, region.layer, layer_word(idx, region.layer))


def _track(content_hash: str, client: int, t0: int, t1: int,
           db: Path = RECOG_DB) -> list[tuple[int, float, float, float, str]]:
    qs = ",".join("?" * len(mg.BODY_TYPES))
    sql = ("SELECT server_time_ms, x, y, z, type FROM semantic_events_v1 "
           "WHERE content_hash=? AND server_time_ms BETWEEN ? AND ? "
           "AND client_num=? AND type IN (" + qs + ") "
           "AND x IS NOT NULL AND y IS NOT NULL AND z IS NOT NULL "
           "ORDER BY server_time_ms")
    with _ro(db) as c:
        return [(int(r["server_time_ms"]), r["x"], r["y"], r["z"], r["type"])
                for r in c.execute(sql, (content_hash, t0, t1, int(client),
                                         *mg.BODY_TYPES))]


def context_for_kill(occurrence_id: int, db: Path = RECOG_DB) \
        -> dict[str, Any] | None:
    """LOCATION and APPROACH for one kill occurrence.

    The location is the VICTIM's position -- that is where the frag reads as
    having happened, and it is the position the death event actually carries.
    The approach is the KILLER's journey into the fight, which is the part a
    reviewer cannot see from a six second clip and the part that explains it.
    """
    with _ro(db) as c:
        row = c.execute(
            "SELECT k.content_hash, k.map, k.server_time_ms, k.killer_client, "
            "k.victim_client FROM kill_occurrences_v1 o JOIN kill_events_v1 k "
            "ON k.kill_event_id = o.best_observation_id "
            "WHERE o.occurrence_id=?", (int(occurrence_id),)).fetchone()
    if row is None or not row["map"]:
        return None
    idx = index_for(row["map"])
    if idx is None:
        return None

    t = int(row["server_time_ms"])
    ch = row["content_hash"]

    where = None
    if row["victim_client"] is not None:
        near = _track(ch, int(row["victim_client"]), t - AT_MOMENT_MS,
                      t + AT_MOMENT_MS, db)
        if near:
            best = min(near, key=lambda r: abs(r[0] - t))
            where = place_of(row["map"], best[1], best[2], best[3])

    approach = None
    if row["killer_client"] is not None and int(row["killer_client"]) >= 0:
        approach = approach_of(ch, int(row["killer_client"]), t, row["map"],
                               db)

    if where is None and approach is None:
        return None
    return {"map": row["map"],
            "location": where.to_dict() if where else None,
            "approach": approach.to_dict() if approach else None}


def approach_of(content_hash: str, client: int, at_ms: int, map_name: str,
                db: Path = RECOG_DB) -> Approach | None:
    """The last region change this client made before `at_ms`.

    A jump pad or a teleporter in that window wins over walking, because it
    is the thing that explains how somebody appeared where they did.
    """
    idx = index_for(map_name)
    if idx is None:
        return None
    track = _track(content_hash, client, at_ms - APPROACH_WINDOW_MS, at_ms, db)
    if len(track) < 2:
        return None

    seq: list[tuple[int, str, str]] = []
    for t, x, y, z, ty in track:
        rid = idx.region_at(x, y, z)
        if rid is None:
            continue
        if seq and seq[-1][1] == rid:
            continue
        seq.append((t, rid, ty))
    if len(seq) < 2:
        return None

    prev, last = seq[-2], seq[-1]
    kind = (mg.JUMP_PAD if prev[2] == "jump_pad" else
            mg.TELEPORT if last[2] == "teleport_in" else mg.WALK)
    return Approach(kind, prev[1], last[0] - prev[0])


# ── scene-level geography ───────────────────────────────────────────────────

SAME_REGION = "SAME_REGION"
MOVED_ON = "MOVED_ON"
CHASE = "CHASE"


def scene_shape(occurrence_ids: list[int], db: Path = RECOG_DB) \
        -> dict[str, Any] | None:
    """How a run of kills sits on the map.

    Answers the thing the user described: was this one fight in one place,
    a fight that carried around a corner, or a chase across the map? It
    reads existing occurrences and CREATES NOTHING -- no new canonical
    event, no new moment, just a description of the ones already there.
    """
    places: list[str] = []
    map_name = None
    for occ in occurrence_ids:
        ctx = context_for_kill(occ, db)
        if ctx is None or not ctx.get("location"):
            continue
        map_name = ctx["map"]
        places.append(ctx["location"]["region_id"])
    if len(places) < 2:
        return None
    distinct = len(set(places))
    if distinct == 1:
        shape = SAME_REGION
    elif distinct == len(places):
        shape = CHASE
    else:
        shape = MOVED_ON
    return {"map": map_name, "shape": shape, "regions": places,
            "distinct_regions": distinct}


# ── seeding the workshop ────────────────────────────────────────────────────

def reconstruction_context(occurrence_id: int, db: Path = RECOG_DB)         -> dict[str, Any] | None:
    """What geography knows about a moment nobody's camera caught.

    A Workshop request exists because the action happened off screen. That
    is a camera problem, and geography is the part of it we can answer
    without rendering anything: which region the actor was in, which region
    the target was in, and which regions are one move away from the fight --
    the places another camera could plausibly have been.

    NOTHING IS RENDERED HERE and nothing is reconstructed. This is the brief
    a reconstruction would later be built from.
    """
    ctx = context_for_kill(occurrence_id, db)
    if ctx is None:
        return None
    here = (ctx.get("location") or {}).get("region_id")
    if here is None:
        return {**ctx, "neighbours": [], "note":
                "the position itself is outside every learned region"}
    return {**ctx, "neighbours": neighbours_of(ctx["map"], here)}


def neighbours_of(map_name: str, region_id: str, min_moves: int = 25)         -> list[dict[str, Any]]:
    """Regions people actually travel to and from this one.

    Adjacency is behavioural: an edge exists because somebody walked or was
    launched along it, often enough that one stray track cannot invent it.
    """
    import sqlite3 as _sq
    out: list[dict[str, Any]] = []
    try:
        with mg.conn() as c:
            for r in c.execute(
                    "SELECT to_region region, kind, n, median_ms FROM "
                    "map_routes_v1 WHERE map=? AND from_region=? AND n>=? "
                    "UNION ALL SELECT from_region, kind, n, median_ms FROM "
                    "map_routes_v1 WHERE map=? AND to_region=? AND n>=? ",
                    (map_name, region_id, min_moves,
                     map_name, region_id, min_moves)):
                out.append({"region_id": r["region"], "kind": r["kind"],
                            "moves": r["n"], "median_ms": r["median_ms"]})
    except _sq.Error:
        return []
    best: dict[str, dict[str, Any]] = {}
    for e in out:
        k = e["region_id"]
        if k == region_id:
            continue
        if k not in best or e["moves"] > best[k]["moves"]:
            best[k] = e
    return sorted(best.values(), key=lambda e: -e["moves"])
