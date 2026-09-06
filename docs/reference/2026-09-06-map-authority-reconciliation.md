# Map authority — reconciliation plan

**Status: STILL RECONCILING.** The review site already consumes a single
interface; the two implementations behind it have not merged yet, and the
merge is deliberately blocked. See *Blockers*.

## The two implementations

| | `map_spatial_index.MapSpatialIndex` (headless) | `map_geography` (this session) |
|---|---|---|
| unit | 64-unit cube cells | 192-unit XY cells inside a height layer |
| holds | per-layer occupancy counters (walked / combat / death / fire / impact / jump-pad launch + landing / teleport in+out / pickup), cell adjacency, killer→victim encounters | named REGION_NN, height layers, region routes, jump-pad arcs, teleport links, per-region combat |
| answers | "is that a place a performance can be put" | "which PLACE is this, and how do people get to it" |
| sources | semantic_events, teleport_transits, **performance_index.db**, frags_rebuilt | semantic_events, teleport_transits, kill_events |
| cache | JSON per map under `creative_suite/generated/pantheon/map_spatial` | `creative_suite/database/map_geography.db` |

**They are not rivals.** One is an occupancy grid; the other is a
segmentation *over* an occupancy grid. There is no version of this where we
pick a winner — the duplication is only in the data access underneath them,
and that is what the merge removes.

## Target: one MapSpatialIndex

```
MapSpatialIndex          cells, adjacency, encounters, floors   [SHARED]
        │
        └── regions()    height-first layering + density watershed
                         → REGION_NN, routes, pad arcs, teleport links
```

`map_geography` keeps its derivation and loses its reader: `discovery_points`,
`demo_positions`, `routes_for_demo`, `teleport_links` and `combat_for_map`
all become functions over `MapSpatialIndex.layers` / `.adjacency` /
`.encounters` instead of separate SQL passes over `semantic_events_v1`.

## What reconciliation must NOT lose

These are the findings that cost the most to get right, and each has a test:

1. **Height first.** Layers are cut at the sparse Z bands between floors
   *before* any XY work. `MapSpatialIndex.floors()` already bands Z at
   `FLOOR_BAND = 96`; the region layer needs the valley-cut version
   (`VALLEY_RATIO = 0.35`, `MIN_LAYER_SHARE = 0.02`), because a floor is a
   band with a *gap* either side, not merely a gap of 96 units.
   → `test_two_heights_never_merge_into_one_region`
2. **Density watershed, not connected components.** Connected components was
   tried and returned one region per floor: a Quake map is walkable end to
   end. Places are separated by *thin* places. `PROMINENCE = 0.55`.
   → `test_a_thin_corridor_separates_two_rooms`
3. **Deterministic ids.** Sorted iteration, ids by descending sample count
   with a coordinate tie-break. Two full rebuilds gave identical ids.
   Region ids will appear in human notes; renumbering would silently
   re-point every note written before it.
   → `test_region_ids_do_not_depend_on_input_order`
4. **Teleport edges only from `TELEPORT_PLAYER_CONFIRMED`.** `teleport_in`
   and `teleport_out` carry no client number, so a transit cannot be
   attributed to a track. 8 such artifact edges were found and removed.
   → `test_teleports_come_only_from_validated_pairs`
5. **The fragment source ladder** (`demo_lineage.canonical_source_for`):
   complete source → the user's own POV → a fragment only when nothing
   fuller saw the moment. Fragments are never deleted; the occurrence id
   never moves.
   → `test_the_source_ladder_is_stable_for_the_reviewed_items`

## The seam that is already in place

`engine/pantheon/map_authority.py` is the only door anything outside the
engine knocks on:

- `location_of(occurrence_id)` — region, layer, approach
- `workshop_brief(occurrence_id)` — actor/target region + neighbours
- `regions_of(map_name)` — the whole map
- `backend()` — which implementation is answering

`creative_suite/api/review.py` imports **only** `map_authority`; a test
fails if it reaches past it, and another fails if the frontend learns the
word "watershed". When the merge lands, `map_authority` is the one file
outside the engine that changes.

## Blockers (why not now)

1. **`performance_index.db` is 87.6 GB** and `MapSpatialIndex.build()` reads
   it. The storage architecture is being corrected and the compact index is
   not validated.
2. **G: has ~0 GB free** (1.4 MB at time of writing), so nothing can be
   rebuilt or re-cached regardless.

Merging early would mean rebuilding 129 regions against an index that is
about to change shape, on a disk that cannot hold the result.

## Region callouts

Machine ids stay: `REGION_01…N`. A name the user supplies is stored in
`map_region_aliases_v1` **as a separate column** — the stable key never
changes, and deleting every alias would change nothing about the geography.
Nothing writes an alias by itself; community callouts are not inferred.
