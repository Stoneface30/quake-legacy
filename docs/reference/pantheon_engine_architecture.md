# PANTHEON — engine architecture

**The one architecture document.** Everything else that described ownership,
boundaries or storage has been folded in here; there are no competing copies.
The enforceable rules live in `CLAUDE.md` under `HARD RULES — PANTHEON
HEADLESS` (HL-1..HL-8) and the tests named below. Last revised 2026-09-06.

## What PANTHEON is

PANTHEON is our own headless engine for Quake Live demos. It reads `.dm_73`,
owns every statement about what happened, authors new game state, writes
`.dm_73` back, and compares the two — with no game process anywhere in the
loop. A renderer is something PANTHEON hands finished work to, not something
it asks for the truth.

```
RAW .dm_73
   → DM73 parser                          engine/parser/
   → canonical game state                 players, movement, aim, animation,
                                          weapons, projectiles, events, round
                                          state, POV
   → PerformanceTrace                     one player, one window, every track
   → ActionGraph                          the semantic sentence, with evidence
   → FrameTruth                           what was true at each instant
   → RoundScenario                        authored intent
   → compiler                             intent → the observed CA grammar
   → .dm_73                               synthetic, parses back identically
   → ShotSpec → RenderJob
        ├── WOLFCAM_REFERENCE   shipped
        ├── BLENDER             planned
        └── OFFSCREEN_QUAKE     planned
```

Everything above the backend row runs headless. `python -m
engine.pantheon.doctor` proves it on this machine, layer by layer, with
`subprocess.Popen` replaced so that "nothing was spawned" is a measurement.

## Wolfcam is not PANTHEON

WolfcamQL is a replaceable backend with exactly four jobs, declared per
launch through `engine/pantheon/backends.py`:

    REFERENCE_RENDER · EXTERNAL_DM73_VALIDATION
    RUNTIME_CAPABILITY_PROOF · FINAL_QUAKE_BEAUTY

No truth generation may depend on it. `creative_suite/tests/test_pantheon_headless_boundary.py`
enforces this on the import graph and on the vocabulary: a headless module
that imports `subprocess`, the capture path or a backend module — or that
merely names a cvar, a capture cfg, an AVI or `cam10` in code — fails the
suite. Every module under `engine/pantheon/` must be classified HEADLESS or
BACKEND_ALLOWED there.

## Ownership

| Owner | Owns | Lives in |
|---|---|---|
| **HEADLESS ENGINE** | dm_73 semantics, game truth, `PerformanceTrace`, event authority, `ActionGraph`, `FrameTruth`, `RoundScenario`, retarget, compile, compare, `NavigationTruth`, map geography (regions + cells), spatial validity, the performance index, library and templates | `engine/parser/`, `engine/pantheon/{performance,performance_index,performance_library,performance_templates,retarget,compare,headless,action_graph,frame_truth,scenario,compiler,geography,map_geography,map_context,map_spatial_index,navigation,motion_reference,instruction,roster,presenter,store,disk_policy,doctor}.py` |
| **PROLOGUE** | story, choreography, casting, dialogue, voice, `ShotSpec` assembly, proofs that need pixels | `engine/pantheon/{shot,presenter_film,voice,dialogue_mix,ab_scene,*_proof,ca_explainer,color_format,cvar_probe,measure}.py`, `creative_suite/prologue/` |
| **REVIEW** | human curation, discovery UI, verdicts, queues, proxies | `creative_suite/api/`, `creative_suite/frontend/`, `creative_suite/engine/review_*.py`, mining under `engine/parser/` |
| **RENDER BACKENDS** | visual output only | `engine/pantheon/backends.py`, `creative_suite/engine/{wolfcam_capture,director_preview,director_session,supervisor}.py`, `creative_suite/api/_preview_job.py`, `engine/parser/playback_probe.py` |

The prologue and the reviewer CONSUME the engine; neither forks it. Neither
computes geography, event semantics or performance truth of its own.

## Truth layers

**PerformanceTrace** is one player over one window: transform, aim,
animation, weapon, projectile samples and the `EV_*` chain, all on the
demo's own serverTime, each track naming its authority (OBSERVED /
INTERPOLATED / NOT OBSERVED). Where the recorder saw nothing, the trace has
nothing and the comparison says `UNOBSERVED`; gaps stay gaps.

**Event authority** is single. Player-carried events ride the body's entity
with alternating toggle bits; temp-entity events (impacts, rail trails,
obituaries, teleports) are fresh entities — `eType` is 8 bits on the wire, so
toggle bits there are truncated and a reused slot swallows the second of two
identical events. Attribution is by what an event IS, never by slot: his
missile in that slot on the previous tick; the entity naming him; him as the
killer; for a teleport, the confirmed pair AND his own discontinuity.

**ActionGraph** is the smallest semantic reading above the trace: nodes and
edges that each cite `OBSERVED_EVENT`, `STATE_TRANSITION` or `DERIVED`. An
event the transform contradicts is `rejected` with a reason, never a node.

**FrameTruth** is what was true at each instant, emitted from the scenario
that authored it, on the demo's clock, carrying the recorded pose and a
sound intent per event. No backend invents game state.

## Authoring layers

`RoundScenario` authors intent; `Actor.perform(trace)` makes a recorded
performance the animation; `compiler.py` is the only place protocol values
appear above the codec. `Retarget` is a rigid horizontal transform —
`EXACT_WORLD` or `LOCAL_FRAME` — that never scales time or bends the motion,
and `compare()` applies the same transform to both sides so the two are
measured by one instrument.

## Storage

`PANTHEON_PERFORMANCE_STORE` (default `creative_suite/database`) is the root
for everything derived; no drive letter appears in engine code, and
`QUAKE_LEGACY_ROOT` resolves the project above a worktree.

| File | Holds |
|---|---|
| `performance_index_v2.db` | discovery rows: identity, window, kind, outcome, summary movement/aim/projectile features, event chain, grounded path as packed 64u cells, provenance, `trace_locator`. ~800 bytes per action. |
| `performance_traces.db` | content-addressed zlib cache, for traces worth keeping (templates, golden cases, chosen performances). One copy per distinct trace. |
| `performance_templates.db` | real segments, admitted only if physically continuous. |
| `map_geography.db` | regions, layers, routes, jump-pad arcs, teleport links AND the 64u spatial cells, adjacency and encounters. One geography store. |

**Index actions; do not duplicate performance.** The first index carried a
45 KB trace per action, reached 94 GB and filled a drive. A trace is
reconstructed from its locator through the same extractor that produced it;
`doctor` proves that per kind on every run.

## Spatial authority

One authority, two resolutions, one store:

- **`map_spatial_index`** — 64-unit occupancy: walked cells, adjacency,
  landings, combat density, floors. The fine answer: can a body stand here.
- **`map_geography`** — height layers FIRST (Quake maps stack; XY clustering
  alone merges a walkway with the room beneath it), then a density watershed
  inside each layer, giving deterministic `REGION_NN` ids, a route graph of
  observed moves, jump-pad arcs, and teleport links from
  `TELEPORT_PLAYER_CONFIRMED` pairs only. The coarse, nameable answer.
- **`geography.py`** — the one API every consumer calls:
  `region_for_position`, `location_for_event`, `approach_for_occurrence`,
  `route_between`, `is_walked`, `GeographyValidity` (LOCAL_FRAME validity).

None of this is BSP geometry. It is behavioural geography: where players
actually went and fought, and it says so.

## Render boundary

One permit, `engine/pantheon/render_permit.py`; one setting,
`PANTHEON_RENDER=off|auto|on`, default `auto`. `off` never renders; `auto`
and `on` render only when no protected game is running; **a running game
always defers**, whatever the setting says, and there is no force variable a
background session can inherit. Three disk thresholds
(`engine/pantheon/disk_policy.py`) keep a tiny review write from being held
to a capture's requirements: `REVIEW_DB_WRITE_SAFE`, `RENDER_JOB_SAFE`
(expected output + margin), `LARGE_BUILD_SAFE`. A refused queue job stays
`QUEUED` with `RENDER DEFERRED`, never FAILED.

Every launch site asks the permit; `creative_suite/tests/test_render_permit.py`
fails if one stops asking, if a second permit module appears, or if a new
`Popen` of wolfcamql shows up anywhere. `creative_suite/tests/conftest.py`
fails any test that tries to create a game process.

## Self-test

```
python -m engine.pantheon.doctor          # human-readable
python -m engine.pantheon.doctor --json   # machine-readable
```

PARSER · EXTRACT · ACTION_GRAPH · RETARGET · COMPILE · PARSE_BACK · COMPARE ·
FRAME_TRUTH · INDEX · RECONSTRUCT · GEOGRAPHY · TEMPLATES · RENDER_PERMIT ·
NO_RENDERER.
