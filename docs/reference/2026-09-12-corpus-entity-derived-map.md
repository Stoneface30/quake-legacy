# Which corpus data depends on DM73Parser's entity state (2026-09-12)

Gate G1 fixed `engine/parser/demo_parse.py` on 2026-09-12 (parser v2; see
`docs/reference/2026-09-12-corpus-parser-v2-status.md`). The following were
wrong in v1:

- the delta-reference history was one frame stale
- full frames seeded every baseline
- entities entering a frame skipped their baseline
- fields changed to zero were dropped
- repeated reliable commands were applied again
- split configstrings (`bcs0/1/2`) were ignored
- `%` and high bytes in strings were wrong
- signed playerstate fields were read unsigned
- the persistant, ammo and powerups arrays were discarded

The fields cgame is handed are now proven equal to the engine's own decoder
(G1).

**The playerstate path was never the problem.** The recorder's origin, health
and weapon rows were already right, except the three signed fields. Obituaries,
though, are entity temp-events, so **every frag, and every table keyed on one,
is entity-derived.**

## Classification

| database | table | builder | class |
|---|---|---|---|
| frags_rebuilt.db | frags | rebuild_corpus.parse_one | ENTITY |
| frags_rebuilt.db | demos | same | mixed: raw_obituaries / accepted_frags ENTITY; catalogue columns clean |
| frag_recognition.db | recognized_frags, scanned_demos | recognition_scan.scan_one | ENTITY |
| frag_recognition.db | kill_events_v1 | derive_kill_events.derive_one | ENTITY |
| frag_recognition.db | semantic_events_v1 | enrich_semantic_events.enrich_one | ENTITY (source='playerstate' rows excepted) |
| frag_recognition.db | missile_samples_v1, teleport_transits_v1 | enrich_semantic_events | ENTITY |
| frag_recognition.db | round_state_v1, server_text_v1, team_changes_v1, player_names_v1, player_teams_v1 | enrich_semantic_events | COMMAND/CONFIGSTRING. v1 had duplicate resent commands and lost bcs strings, so these change too. |
| frag_recognition.db | stage2_visibility, dodge_*, projectile_*, lg_* | stage2_visibility, extract_dodge_events, extract_projectile_paths, extract_lg_engagements | ENTITY |
| frag_recognition.db | view_extracted / recognition_view_timeseries, health_extracted | extract_view_timeseries, extract_health_armor | playerstate values; which frags get rows is ENTITY |
| frag_recognition.db | kill_occurrences_v1, funny_candidates_v1, movement_moments_v1 | kill_occurrences, funny_candidates, movement_moments | ENTITY |
| frag_recognition.db | round_outcome_v1 | round_model.build | COMMAND/CONFIGSTRING |
| frag_recognition.db | match_roster_v1, match_format_v1 | match_roster.build | ENTITY |
| frag_recognition.db | action_moments_v1, aim_events_v1 (promoted copies) | mining_epoch promote | as their sources |
| frag_shapes.db | frag_shapes_v1 | frag_shapes.build | ENTITY |
| mining_epoch.db | action_moments_v1, demo_lineage_v1 | mine_action_moments, demo_lineage | ENTITY |
| mining_epoch.db | aim_events_v1 | mine_aim_events | playerstate (yaw/pitch) |
| map_geography.db | map_*_v1 | map_geography.build_all | ENTITY |
| performance_index_v2.db, performance_traces.db, performance_templates.db | demos/actions, traces, templates | performance_index, trace_cache, performance_templates | ENTITY |

The mapping was done by static reading (file:line citations in the session
record). The following were not read in detail and are treated as ENTITY until
shown otherwise: `reclassify_v2`, `scene_scoring`, `refine_view_metrics`,
`performance_templates`.

## Rebuild order

1. `rebuild_corpus.py` → frags_rebuilt
2. `recognition_scan.py` → scanned_demos, recognized_frags
3. `derive_kill_events.py`, `enrich_semantic_events.py`
4. `full_corpus_v3` stages: extract_*, stage2_visibility, reclassify, frag_shapes
5. `kill_occurrences`, then `funny_candidates` and `movement_moments`
6. `mine_action_moments`, `mine_aim_events` → mining_epoch, then promote
7. `demo_lineage`, `round_model`, `match_roster`, `map_geography`
8. `performance_index` → trace_cache → `performance_templates` (independent: it
   re-parses the demos itself)

Many of these builders hard-code their database path (`derive_kill_events`,
`enrich_semantic_events`, the extract_* scripts, the miners). Rebuilding into
a new versioned corpus therefore needs one store-level switch for the
database directory, not per-script flags.
