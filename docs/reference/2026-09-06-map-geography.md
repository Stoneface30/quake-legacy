# Map geography — learned from play, not from map files

**Version** `map-geography-v1.0.0` · built 2026-09-06 · headless

## What this is

Where the fighting happens on each map, derived from every position anyone
was ever recorded standing in. No BSP is read, no entity lump is parsed and
no renderer is opened.

A **region** is not a room. It is a volume of space people repeatedly
occupied, fought in and moved between — which is a more useful claim for
editing than architecture would be. A corridor nobody uses is not a place;
a sniper perch inside a bigger room is.

## How it is derived

1. **Height first.** The Z histogram of a map has dense bands where floors
   are and sparse gaps between them. Those gaps are the layer cuts.
   Quake maps stack: on campgrounds the upper walkway shares its entire
   footprint with the floor beneath it, and clustering in XY alone would
   call them one place.
2. **Then XY, inside one layer only.** Two places at the same XY and
   different heights can therefore never merge.
3. **Watershed, not connected components.** Connected components was tried
   first and returned exactly one region per floor — a Quake map is walkable
   end to end, so every occupied cell on a level touches every other.
   What separates two places is not empty space but a *thin* place: a
   doorway, a ramp, a corridor. The density field is flooded from its peaks
   downward; basins whose saddle is nearly as busy as their own peak are
   merged back (prominence 0.55).
4. **Connection is behavioural.** Layers are not reconnected by guessing
   where the stairs are. A client seen in region A and then in region B is
   an edge; a jump pad that carried them is that edge's kind.

Grid: `CELL_XY = 192` units (bigger than a fight, smaller than a room),
`Z_BIN = 32`.

## Result

| map | regions | height layers | demos | discovery samples |
|---|---:|---:|---:|---:|
| quarantine | 25 | 5 | 414 | 1,369,573 |
| asylum | 24 | 8 | 913 | 2,919,096 |
| campgrounds | 20 | 4 | 1,081 | 2,689,244 |
| trinity | 20 | 5 | 420 | 1,260,993 |
| overkill | 16 | 3 | 665 | 2,556,673 |
| hiddenfortress | 12 | 4 | 426 | 1,361,218 |
| thunderstruck | 10 | 4 | 170 | 431,472 |
| hellsgate | 2 | 1 | 34 | 99,760 |

**129 regions · 34 height layers · 2,451 route edges (1,437,417 observed
moves) · 584 jump-pad arcs (128,545 launches) · 11 teleport links (51,329
transits) · 51,461 deaths and 10,642,003 shots placed.**

Plates: `docs/visual-record/2026-09-06/map_regions_*.png`, one panel per
height layer.

## Naming

Regions are `REGION_01…N`. Height layers get LOWER / MID / UPPER, because
that ordering *is* in the data — it is the rank of the layer's Z band.

Community callouts are **not** invented. Nobody has told us that a region is
"the RA room", and printing that guess would put a confident wrong word in
front of the user on every clip. If a reliable source of callouts appears it
maps onto region ids without any of this changing.

## Determinism

Region ids appear in the dossier and will appear in human notes. If a
rebuild renumbered them, every note written before it would silently start
describing somewhere else.

Fixed grid, integer arithmetic, components discovered in sorted order, ids
assigned by descending sample count with a coordinate tie-break. Two
independent full rebuilds of the whole corpus produced identical region
counts and identical ids. Shuffling the input changes nothing.

## What is deliberately absent

- **Teleport edges from position tracks.** `teleport_in` and `teleport_out`
  carry no client number, so a transit cannot be attributed to the person
  walking a track. Teleport geography comes only from the already-validated
  `TELEPORT_PLAYER_CONFIRMED` pairs; `AMBIGUOUS` transits are a guess, and a
  guess is not geography. The backfill was **not** rerun.
- **A position outside every learned cell resolves to `None`**, and the
  dossier simply shows no location. Snapping it to the nearest region would
  be a confident wrong answer.
- **Line of sight.** Nothing here claims what could be seen from where.

## Rebuilding

```bash
python -c "import sys;sys.path.insert(0,'.');from engine.pantheon import map_geography as mg;print(mg.build_all())"
```

~6 minutes for the whole archive. Everything is driven per demo, never per
event type: `semantic_events_v1` holds 34.3M rows and its only useful index
is `(content_hash, server_time_ms)`.
