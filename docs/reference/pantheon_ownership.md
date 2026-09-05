# PANTHEON ownership

**Date:** 2026-09-06 · **Rules:** CLAUDE.md HL-1..HL-7

One engine. Four owners. Nothing is implemented twice.

| Owner | Owns | Lives in | May import |
|---|---|---|---|
| **HEADLESS ENGINE** | demo parsing, canonical semantics, `PerformanceTrace` and event authority, retarget, compile, compare, `FrameTruth`, `RoundScenario`, `ActionGraph`, `NavigationTruth`, `MapSpatialIndex`, the performance index and library | `engine/parser/`, `engine/pantheon/{performance,performance_index,performance_library,performance_templates,retarget,compare,headless,action_graph,map_spatial_index,navigation,motion_reference,frame_truth,scenario,compiler,instruction,roster,presenter}.py` | the parser, the databases. **Never** a backend, a cvar, a capture cfg, an AVI, a process. |
| **PROLOGUE** | story, choreography, casting, dialogue, voice, `ShotSpec` assembly, proofs that need pixels | `engine/pantheon/{shot,presenter_film,voice,dialogue_mix,ab_scene,cast_proof,presenter_proof,instruction_proof,proofs,proof0_color,proof_b_identity,proof_c_rails,ca_explainer,color_format,cvar_probe,measure}.py`, `creative_suite/prologue/` | the headless engine (consumes it, never forks it), the render backends. |
| **REVIEW** | human curation, discovery UI, verdicts, queues, proxies | `creative_suite/api/`, `creative_suite/frontend/`, `creative_suite/engine/review_*.py`, mining scripts under `engine/parser/` | the headless engine for semantics; the render backends only through `RenderPermit`. |
| **RENDER BACKENDS** | visual output and nothing else: Wolfcam reference/beauty, a future Blender or offscreen renderer | `engine/pantheon/backends.py`, `creative_suite/engine/{wolfcam_capture,director_preview,director_session,supervisor}.py`, `creative_suite/api/_preview_job.py`, `engine/parser/playback_probe.py` | anything; but every launch passes `creative_suite/engine/render_permit.require()` first. |

## Enforcement

- `creative_suite/tests/test_pantheon_headless_boundary.py`: every module under `engine/pantheon/` is classified HEADLESS or BACKEND_ALLOWED; a HEADLESS module may not import a backend, `subprocess` or the capture path, and may not carry backend vocabulary in code.
- `creative_suite/tests/test_render_permit.py`: every known Wolfcam launch site calls the permit; a new `Popen` of `wolfcamql` anywhere else fails the suite.
- `creative_suite/tests/conftest.py`: the test suite cannot create a game process, whatever a test tries.

## Render permission (user requirement, 2026-09-05)

`PANTHEON_RENDER_ALLOWED=1` is the one operator setting. Without it every launch site raises `RenderDenied`; queues keep the job `QUEUED` with `RENDER DEFERRED: ...` and offer it again later; a READY proxy keeps playing. With it, a launch still defers while a protected game (`quakelive*.exe`, plus `PANTHEON_PROTECTED_GAMES`) is running; `PANTHEON_RENDER_FORCE=1` is the separate explicit override. The process scan is a toolhelp snapshot, not `tasklist`: the gate must not itself open a console window.

## What the prologue consumes

```python
from engine.pantheon import headless as H
trace    = H.extract_performance(demo, client, start_ms, end_ms)
compiled = H.compile_performance({"HERO": trace}, cast={"HERO": PresenterProfile(...)},
                                 retarget=Retarget.local_frame(trace, to=mark, yaw=heading))
report   = H.compare(trace, H.reextract(compiled)["HERO"], retarget=compiled.retarget)
# only then: backends.render("WOLFCAM_REFERENCE", shot=..., use=BackendUse.REFERENCE_RENDER)
```
