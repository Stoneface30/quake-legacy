"""The one door the reviewer knocks on for spatial truth.

WHY THIS EXISTS. Map truth belongs to the shared headless engine, and the
review site consumes it rather than forking it. Today two implementations
sit side by side in this package:

    map_spatial_index.MapSpatialIndex   64-unit cells, per-layer occupancy
                                        counters, cell adjacency, floors,
                                        `is_walked`, `nearest_walked`
    map_geography                       height-first layering, a density
                                        watershed over those cells, stable
                                        REGION_NN ids, region-level routes,
                                        jump-pad arcs and teleport links

THEY ARE NOT RIVALS. The first answers "is that a place a performance can be
put" at cell resolution. The second answers "which PLACE is this, and how do
people get to it" -- which is a layer ON TOP of an occupancy grid, not a
second copy of one. The reconciliation is therefore not a choice between
them: regions become a derivation over the shared index, and the shared
index stops being read twice.

WHAT THIS MODULE IS FOR. Everything outside the engine -- the reviewer, the
dossier, the workshop brief -- calls THIS, and never the mathematics. When
the merge lands, `map_geography`'s data access is replaced by
`MapSpatialIndex` and this file is the only other one that changes. The
review UI has never known what a watershed is and must not learn.

STATE: STILL RECONCILING. The merge is blocked on two things outside this
package, and doing it early would be worse than waiting:

  1. `performance_index.db` is 87.6 GB and MapSpatialIndex reads it. The
     storage architecture is being corrected and the compact index is not
     validated yet.
  2. G: has no free space, so nothing can be rebuilt or re-cached anyway.

Until then this delegates to `map_geography`, whose data is already built
and already correct. Nothing downstream has to know which day that changes.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ALIAS_DB = REPO_ROOT / "creative_suite" / "database" / "map_geography.db"

# Which implementation is answering right now. Reported so an operator can
# tell at a glance whether the handoff has happened.
BACKEND_REGIONS = "map_geography"
BACKEND_SHARED = "map_spatial_index"

_ALIAS_SCHEMA = """
CREATE TABLE IF NOT EXISTS map_region_aliases_v1 (
    map        TEXT NOT NULL,
    region_id  TEXT NOT NULL,
    alias      TEXT NOT NULL,
    provenance TEXT NOT NULL DEFAULT 'HUMAN_USER',
    added_at   TEXT NOT NULL,
    PRIMARY KEY (map, region_id)
);
"""


def backend() -> str:
    """Which implementation is behind these answers today."""
    return BACKEND_REGIONS


# ── the interface the reviewer consumes ─────────────────────────────────────

def location_of(occurrence_id: int) -> dict[str, Any] | None:
    """Where a kill happened and how the killer got there."""
    from engine.pantheon import map_context as mc
    return _with_aliases(mc.context_for_kill(occurrence_id))


def workshop_brief(occurrence_id: int) -> dict[str, Any] | None:
    """Actor region, target region and the regions one move away."""
    from engine.pantheon import map_context as mc
    return _with_aliases(mc.reconstruction_context(occurrence_id))


def regions_of(map_name: str) -> dict[str, Any] | None:
    from engine.pantheon import map_context as mc
    from engine.pantheon import map_geography as mg
    idx = mg.load_index(map_name)
    if idx is None:
        return None
    al = aliases(map_name)
    return {"map": map_name, "backend": backend(),
            "layers": [{"layer": la.layer, "z_lo": la.z_lo, "z_hi": la.z_hi,
                        "samples": la.samples,
                        "word": mc.layer_word(idx, la.layer)}
                       for la in idx.layers],
            "regions": [{**r.to_dict(), "alias": al.get(r.region_id)}
                        for r in sorted(idx.regions.values(),
                                        key=lambda r: r.region_id)]}


# ── aliases: a name the user gave, never an identity we invented ────────────

@dataclass(frozen=True)
class Alias:
    map: str
    region_id: str
    alias: str
    provenance: str
    added_at: str


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(ALIAS_DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.executescript(_ALIAS_SCHEMA)
    return c


def set_alias(map_name: str, region_id: str, alias: str,
              provenance: str = "HUMAN_USER") -> Alias:
    """Record what the user calls a region.

    THE STABLE KEY DOES NOT MOVE. `REGION_04` stays `REGION_04` forever --
    it is what every derived table, every route edge and every human note
    refers to. The alias is a separate column the UI may show INSTEAD of the
    id, and deleting every alias in this table would change nothing about
    the geography.

    We never write one of these ourselves. Community callouts are not
    inferred: nobody has told us which region is the RA room, and a guess
    printed on every clip is worse than a machine label.
    """
    alias = alias.strip()
    if not alias:
        raise ValueError("an empty alias is not a name")
    if not region_id.startswith("REGION_"):
        raise ValueError(f"not a machine region id: {region_id}")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    c = _conn()
    try:
        c.execute(
            "INSERT INTO map_region_aliases_v1(map, region_id, alias, "
            "provenance, added_at) VALUES(?,?,?,?,?) ON CONFLICT(map, "
            "region_id) DO UPDATE SET alias=excluded.alias, "
            "provenance=excluded.provenance, added_at=excluded.added_at",
            (map_name, region_id, alias, provenance, now))
        c.commit()
    finally:
        c.close()
    return Alias(map_name, region_id, alias, provenance, now)


def aliases(map_name: str) -> dict[str, str]:
    try:
        c = _conn()
    except sqlite3.Error:
        return {}
    try:
        return {r["region_id"]: r["alias"] for r in c.execute(
            "SELECT region_id, alias FROM map_region_aliases_v1 WHERE map=?",
            (map_name,))}
    except sqlite3.Error:
        return {}
    finally:
        c.close()


def _with_aliases(ctx: dict[str, Any] | None) -> dict[str, Any] | None:
    if not ctx or not ctx.get("map"):
        return ctx
    al = aliases(ctx["map"])
    if not al:
        return ctx
    loc = ctx.get("location")
    if loc and loc.get("region_id") in al:
        loc["alias"] = al[loc["region_id"]]
        loc["label"] = al[loc["region_id"]]
    ap = ctx.get("approach")
    if ap and ap.get("from_region") in al:
        ap["alias"] = al[ap["from_region"]]
    for n in ctx.get("neighbours", []) or []:
        if n.get("region_id") in al:
            n["alias"] = al[n["region_id"]]
    return ctx
