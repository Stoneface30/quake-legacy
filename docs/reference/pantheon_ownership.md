# PANTHEON ownership

**Date:** 2026-09-06 · **Rules:** CLAUDE.md HL-1..HL-7

One engine. Four owners. Nothing is implemented twice.

| Owner | Owns | Lives in | May import |
|---|---|---|---|
| **HEADLESS ENGINE** | demo parsing, canonical semantics, `PerformanceTrace` and event authority, retarget, compile, compare, `FrameTruth`, `RoundScenario`, `ActionGraph`, `NavigationTruth`, the map geography (`map_geography` regions/layers/routes + `map_spatial_index` cells, behind `geography.py`), the performance index, library and templates | `engine/parser/`, `engine/pantheon/{performance,performance_index,performance_library,performance_templates,retarget,compare,headless,action_graph,map_spatial_index,navigation,motion_reference,frame_truth,scenario,compiler,instruction,roster,presenter}.py` | the parser, the databases. **Never** a backend, a cvar, a capture cfg, an AVI, a process. |
| **PROLOGUE** | story, choreography, casting, dialogue, voice, `ShotSpec` assembly, proofs that need pixels | `engine/pantheon/{shot,presenter_film,voice,dialogue_mix,ab_scene,cast_proof,presenter_proof,instruction_proof,proofs,proof0_color,proof_b_identity,proof_c_rails,ca_explainer,color_format,cvar_probe,measure}.py`, `creative_suite/prologue/` | the headless engine (consumes it, never forks it), the render backends. |
| **REVIEW** | human curation, discovery UI, verdicts, queues, proxies | `creative_suite/api/`, `creative_suite/frontend/`, `creative_suite/engine/review_*.py`, mining scripts under `engine/parser/` | the headless engine for semantics; the render backends only through `RenderPermit`. |
| **RENDER BACKENDS** | visual output and nothing else: Wolfcam reference/beauty, a future Blender or offscreen renderer | `engine/pantheon/backends.py`, `creative_suite/engine/{wolfcam_capture,director_preview,director_session,supervisor}.py`, `creative_suite/api/_preview_job.py`, `engine/parser/playback_probe.py` | anything; but every launch asks `engine/pantheon/render_permit` first. |

## Enforcement

- `creative_suite/tests/test_pantheon_headless_boundary.py`: every module under `engine/pantheon/` is classified HEADLESS or BACKEND_ALLOWED; a HEADLESS module may not import a backend, `subprocess` or the capture path, and may not carry backend vocabulary in code.
- `creative_suite/tests/test_render_permit.py`: every known Wolfcam launch site calls the permit; a new `Popen` of `wolfcamql` anywhere else fails the suite.
- `creative_suite/tests/conftest.py`: the test suite cannot create a game process, whatever a test tries.

## Render permission (user requirement, 2026-09-05)

One module, `engine/pantheon/render_permit.py`; one setting, `PANTHEON_RENDER=off|auto|on` (default `auto`). `off` never renders. `auto` and `on` render only when no protected game is running; a running game always defers. No force variable exists. Queues keep a refused job `QUEUED` with `RENDER DEFERRED`; user-triggered previews defer through their own worker too. The process scan is psutil or a toolhelp snapshot, never `tasklist`. The capture window is shown minimized and not activated as defence in depth.

## What the prologue consumes

```python
from engine.pantheon import headless as H
trace    = H.extract_performance(demo, client, start_ms, end_ms)
compiled = H.compile_performance({"HERO": trace}, cast={"HERO": PresenterProfile(...)},
                                 retarget=Retarget.local_frame(trace, to=mark, yaw=heading))
report   = H.compare(trace, H.reextract(compiled)["HERO"], retarget=compiled.retarget)
# only then: backends.render("WOLFCAM_REFERENCE", shot=..., use=BackendUse.REFERENCE_RENDER)
```

## Geography (one authority, 2026-09-06)

`engine/pantheon/geography.py` is the only API: `region_for_position`, `location_for_event`, `approach_for_occurrence`, `route_between`, `is_walked`, `GeographyValidity` (LOCAL_FRAME). Underneath: `map_geography.py` (from the review session: height layers first, watershed regions inside a layer, deterministic `REGION_NN` ids, route graph of observed moves, jump-pad arcs, teleport links from `TELEPORT_PLAYER_CONFIRMED` only) and `map_spatial_index.py` (from the headless session: 64-unit walked cells, adjacency, landings, combat density, floors). The reviewer consumes through `map_context` / `geography`; it computes no geography of its own. Derived geography lives in the store (`PANTHEON_PERFORMANCE_STORE/map_geography.db`, `map_spatial/`).

## Storage (2026-09-06)

`PANTHEON_PERFORMANCE_STORE` (default `creative_suite/database`) holds everything PANTHEON derives: `performance_index_v2.db` (lightweight action rows, ~820 bytes each, no trace copies), `performance_traces.db` (content-addressed zlib cache for traces worth keeping), `performance_templates.db`, `map_geography.db`, `map_spatial/`. The 94 GB first-generation `performance_index.db` is evidence and is not read.
