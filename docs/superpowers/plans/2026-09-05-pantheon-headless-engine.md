# PANTHEON headless performance engine — sprint plan

**Date:** 2026-09-05 · **Branch:** `feature/pantheon-headless` (cut from `feature/pantheon-prologue` @ 96b4e422)
**Owner:** this session (deterministic headless semantics). The prologue session owns visual A/B.
**Laws:** CLAUDE.md HL-1..HL-7. No Wolfcam launch in this sprint.

## Ownership reconciliation (done first)

| Piece | Lives in | Status |
|---|---|---|
| `PerformanceTrace` + `extract_performance` | `engine/pantheon/performance.py` (prologue branch) | shared authority; this sprint adds `from_dict`, never a second copy |
| `Actor.perform(trace)` | `scenario.py` | the verbatim retarget; `retarget.py` wraps it, does not fork it |
| REAL_ACTION_TRACE_PROOF_01 | `real_action_proof.py` | its differential is promoted into `compare.py`; the proof becomes a caller |
| corpus index | `performance_index.py`, `performance_index.db` | run PID 26280 (prologue session) alive at 2,409/4,292 — NOT restarted here |
| semantic events, 34.3M rows with XYZ | `frag_recognition.db::semantic_events_v1` | read-only source for `MapSpatialIndex` |
| character profiles | `roster.py::PresenterProfile` | IS the CharacterProfile; no new class |

## Units (each: tests first, then code, then commit)

1. `retarget.py` — `TransformMode {EXACT_WORLD, LOCAL_FRAME}`, `Retarget` (offset, yaw), `validate_retarget` against `MapSpatialIndex`.
2. `compare.py` — `PerformanceDiff` with per-track `MATCHED | WITHIN_TOLERANCE | INTENTIONAL_DIFFERENCE | UNOBSERVED | MISSING | INVALID`; gaps are never filled.
3. `headless.py` — facade: `extract_performance`, `compile_performance`, `reextract`, `compare`, `run` (with timings).
4. compiler event emission — recorded `fire_weapon`, `jump_pad`, `jump`, `pain`, `death`, `teleport_*` on the player entity; `missile_hit/miss`, `railtrail` as temp entities. FrameTruth carries sound intent and recorded anim/pitch/velocity.
5. `action_graph.py` — nodes with evidence (`OBSERVED_EVENT | STATE_TRANSITION | DERIVED`), transform validation, projectile tracks (rocket/grenade/plasma), rail and LG represented on their own terms, semantic categories.
6. `map_spatial_index.py` — behavioural geography per map from the semantic events + index traces; cached JSON; feeds LOCAL_FRAME validity.
7. `performance_library.py` — anonymous `PERF:` references over the index; category counts in SQL where possible.
8. `headless_bench.py` + golden regression tests over real demos (skip when the corpus is absent).
9. Boundary audit extension (token scan, not only imports); CLAUDE.md HL-5..HL-7; spec update; final report.
