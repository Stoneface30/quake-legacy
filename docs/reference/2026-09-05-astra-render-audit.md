# Render reproducibility audit — 2026-09-05

**Verdict:** the inspected checkout contains a working-shaped Wolfcam preview implementation and substantial planning vocabulary, but not an executable, reproducible multi-backend ShotSpec → PassPlan → FrameTruth pipeline. Preserve the existing camera/capture work. First prove one constrained shot and its requested passes through the actual consumer before adding another architecture layer.

This is a skeptical source audit, not an implementation proposal or visual sign-off. Scope: `/mnt/g/QUAKE_LEGACY`, HEAD observed `bb23f2d4`, including current working files and ignored local engine source trees. A separate checkout may contain additional work; absence here says nothing about that checkout. No engine, renderer, ComfyUI job, batch, installation, database write, or real capture was executed. Two pure Python camera probes ran with bytecode writes disabled. Historical capture claims below are identified as documentary evidence; this audit did not inspect their pixels or re-establish the installed binary's identity.

Read project instructions and the available memory ledger at `.claude/Vault/learnings.md`; relevant project feedback includes effects-never-existed, cvar-silent-noop, and projectile-evidence-contract. Their governing constraint is essential here: a named rule, registered cvar, generated cfg, successful process, and delivered image are different evidence levels.

## What actually exists

| Boundary | Concrete checkout evidence | What it proves |
|---|---|---|
| Creative choreography | `creative_suite/engine/choreography.py:12`, `:120`, `:183` | Lane/evidence/capability plan objects; module explicitly says it is not the renderer. |
| Scene photography | `creative_suite/engine/pantheon_scene.py:299`, `:318`, `:417` | `OutputPasses`, `PantheonScene`, and an FX command compiler exist. FX compiler callers found in the inspected Python tree are tests. |
| Actual preview input | `creative_suite/engine/director_preview.py:452`, `:663` | `PreviewPlan` combines recipe, draft, camera, map, tracks and music. This is the runnable preview consumer's input, not a general ShotSpec. |
| Actual camera emission | `creative_suite/engine/director_preview.py:921`; `camera_compiler_v2.py:450`; `cam10_writer.py:243` | Dense path compilation reaches the real preview path and produces an LF-only `.cam10` plus backend commands. |
| Actual capture/composite | `creative_suite/engine/director_preview.py:1973`, `:2002`, `:2013`, `:2019`, `:1208` | Launch Wolfcam, select an AVI, transcode/trim beauty, separately mux audio. |
| Render treatment | `creative_suite/engine/render_profile.py:720`, `:1259` | Look/keyframe vocabulary and explicit acknowledgement of backend entanglement; the proposed minimum backend seam is described at `:1278`, not implemented there. |
| Synthetic authoring | `creative_suite/engine/cinematic_synthetic.py:56` | Authored-element identity/provenance metadata. No Blender scene/frame emitter was found in the application engine/Comfy Python sources. |

Exact identifier search for `ShotSpec|RenderJob|FrameTruth|PassPlan` in application Python and reference/plans found no implementations. This does **not** mean there are no useful equivalent pieces: the table above is the inventory to consolidate, not discard.

## Material findings

### R1 — ARCHITECTURAL BLOCKER: the advertised boundary is not the execution boundary

The choreography vocabulary can describe effects that are not renderable (`choreography.py:21`). `PantheonScene` carries camera intent, arbitrary FX cues, look, and output passes (`pantheon_scene.py:318`), but the actual preview runs from `PreviewPlan` and a normalized draft (`director_preview.py:452`). `compile_fx_cfg_lines()` at `pantheon_scene.py:417` has test callers, not a discovered production call. The real path writes a fixed intensity script and grade pack at `director_preview.py:1978`, then builds its cfg at `:1985`.

**Consequence:** a plan hash or accepted choreography does not establish that requested lanes, cues, passes, or backend limitations reached the renderer. A second backend added here could merely create a second interpretation of the same intent.

**Smallest falsification:** construct one synthetic in-memory plan containing one uniquely identifiable FX cue plus one pass request. Trace it through the existing preview cfg builder with side effects stubbed. Require either an emitted instruction tied to that cue or an explicit unsupported-capability result. A cue disappearing while a ready result remains possible falsifies end-to-end compilation. Do this before designing new class names.

### R2 — CORRECTNESS BUG: missing collision evidence becomes `VALID`

`director_preview.py:1039` describes missing geometry as non-fatal, and `:1051` catches every exception while constructing the tracer. `camera_compiler_v2.py:288` then returns `status=VALID` with no tracer. The underlying report says `tracer=False`, but even its `checked` field is the number of supplied points (`camera_paths.py:305`), not a count of actual tests. The real capture rejects only `REJECTED` (`director_preview.py:1974`).

**Executed pure probe:** two arbitrary points, no tracer → `{'status': 'VALID', 'min_clearance_u': None, 'report': {'solid_keyframes': [], 'blocked_segments': [], 'checked': 2, 'tracer': False}}`.

**Consequence:** a missing map, import failure, corrupted geometry or unexpected tracer exception can still authorize a supposedly collision-checked camera. A diagnostic flag is not a validity gate. This does not prove existing captured shots collided; it proves validation can be absent while the top-level result says valid.

**Smallest falsification:** the no-tracer call below already establishes the false validity state. Next make the geometry loader raise in a preview-builder test and require an explicit unverified/rejected camera state. Keep geometry-free synthetic previews separately labelled if needed.

### R3 — CORRECTNESS BUG: recovery preserves geometry while losing moving-target timing

`camera_compiler_v2.py:400` rescales times while preserving positions **and angles**. The recovery ladder invokes it for surviving path prefixes (`director_preview.py:953`, `:976`), then recompiles with collision/coverage checks. Retargeting exists (`camera_compiler_v2.py:220`) but is not called by that recovery. The compiler itself resamples and collision-checks at `:499`; it does not re-aim a clear path toward a subject at its new timestamps.

**Executed pure probe:** an orientation authored at 1000 ms reappears unchanged at 2000 ms after retiming. A static target can tolerate this; a moving projectile/player need not. Reaching `FULL` coverage proves camera supply duration, not subject visibility or alignment with the same action peak.

**Consequence:** a geometrically successful recovery can destroy the intended projectile-follow or reveal shot while retaining an acceptable coverage label. The manifest does record that recovery occurred; it does not prove the semantic camera contract survived.

**Smallest falsification:** synthetic camera fixed at the origin, subject turning a corner between 1000 and 2000 ms; retime a clear prefix from 0–1000 to 0–2000. Compare each resulting angle with `look_at_angles(position, subject(new_time))`. Measure the angular error. No demo, BSP, DB or capture is needed. Require re-aiming and protected-anchor checks before calling recovery equivalent to the authored shot.

### R4 — MISSING CAPABILITY: depth exists, but a synchronized pass bundle does not

The source does implement depth output: Wolfcam `engine/engines/_canonical/code/renderercommon/inc_tr_init.c:837` writes named depth TGAs, and `:886` reads `GL_DEPTH_COMPONENT`. The application exposes `show_depth` and sets `mme_saveDepth` (`director_preview.py:1072`). However, the production consumer enumerates **only AVI** at `:2013`, transcodes that file at `:2019`, and returns a camera hash/status at `:2038`. No matching collection, time-map application, missing-frame validation or manifest binding of the depth sequence was found in that path. `OutputPasses` has only beauty/depth parameters (`pantheon_scene.py:308`), not entity IDs, normals, motion vectors or alpha/matte contracts.

**Consequence:** setting `show_depth` can request extra files without delivering a usable synchronized compositing input. A depth cvar is not a PassPlan execution result. In particular, independent retime/trim of beauty while leaving raw depth in staging breaks frame correspondence.

**Smallest falsification:** use a stub backend directory containing a four-frame beauty artifact and three identifiable depth files. Exercise the existing collector with no renderer. Ask it to enumerate paired frame IDs, reject the missing fourth depth sample, and return a pass manifest. The current AVI-only collector cannot satisfy that contract. Prove this before promising depth-based post effects.

### R5 — MISSING CAPABILITY: silhouette XRAY is real source capability; wall removal and entity mattes are different jobs

Wolfcam has meaningful underused hooks: `cg_players.c:4324` selects wallhack treatments; `:4330` distinguishes enemy team; `:4337` chooses enemy shader; `:4356` uses `RF_DEPTHHACK`. That supports stylized through-wall player display at the source level. It is not a mesh operation or an entity-ID pass.

Wolfcam stencil registration is commented out (`engine/engines/_canonical/code/renderercommon/tr_mme.c:381`), and the accumulation path is disabled (`renderercommon/inc_tr_init.c:223`). Conversely, local Q3MME source registers `mme_saveStencil` (`engine/engines/_forks/q3mme/trunk/code/renderer/tr_mme.c:847`) and marks selected player entities `RF_STENCIL` (`cgame/cg_players.c:2221`). These are **different engine trees**, not interchangeable installed capabilities. The older audit correctly separates them (`docs/reference/q3mme_cinematic_audit.md:761`). Entity filtering/remapping capabilities in Wolfcam should still be reused where suitable; they do not automatically provide the missing matte output.

`render_profile.py:481` calls depth-plus-mask XRAY a partial route; `effect_templates.py:1176` says geometry strip/rebuild has no runtime. Both can be true. The visible depth buffer records the frontmost surface; it cannot reconstruct the hidden subject/world surface behind that wall by itself. A mask also needs a defined producer. Do not promote this partial route to true wall removal, an arbitrary selected wall dissolve, or hidden-entity reconstruction.

**Smallest falsification:** before any capture, name the exact target interpretation: silhouette, entity-class hide, selected BSP-surface removal, or isolated matte. For each, resolve one literal emitter and one output consumer. For the missing matte, a later authorized canary should use one occluded subject and one unoccluded control, same camera/timestamps, with an actual mask image as required output. Source reads alone cannot close its installed-binary or pixel-proof gates.

### R6 — FALSELY CLAIMED OR NOT PROVEN: FX predicate availability is not per-target cue context

The engine really parses `enemy` and `teammate` (`engine/engines/_canonical/code/cgame/cg_fx_scripts.c:2299`, `:2305`). `CG_CopyPlayerDataToScriptData` supplies team/client predicates at `:7677`. This enables enemy/team-conditioned effects **at hooks that populate that context**.

A generic `runfx` first resets all script variables (`cg_consolecmds.c:7637`; reset is `cg_fx_scripts.c:7648`) and copies origin/direction/velocity, not a selected player's relationship. Projectile handling is also not uniform: in `cg_ents.c:1935`, owner-to-player-context copying is in the grenade branch (`:1947`); the rocket projectile hook reaches the common invocation at `:1984` after reset without that grenade-specific population. A numeric client slot alone is not a stable entity lifetime or proof of projectile ownership.

**Consequence:** the context list in `q3mme_cinematic_audit.md:475` must not become a promise that an arbitrary timeline cue or every weapon hook can condition itself on enemy/team. `pantheon_fx.py:13` correctly describes its rocket trail hook as running for **every rocket**. That is a real effect, but not a proven hero-projectile isolation route.

**Smallest falsification:** source-derived predicate matrix: trigger = player hook / grenade projectile / rocket projectile / console runfx; columns = client, enemy, teammate, in-eyes. Trace reset and assignments for each. For a later pixel canary, use two simultaneous distinguishable projectiles and require only the chosen one to change. No ownership or isolation claim should pass on a single-projectile shot.

### R7 — ARCHITECTURAL BLOCKER: asset generation is not deterministic replay-state rendering

ComfyUI's texture path is real, but `_run_one()` chooses a fresh random seed (`creative_suite/comfy/full_overnight.py:419`). Its ledger writes asset, pipeline, denoise and output path (`:244`); this call does not persist seed, resolved graph, model bytes, node versions or source-type identity. Resume accepts an existing output path (`:715`) before resolving the optional upscale source (`:727`). The prior audit already documented mixed provenance on resume (`docs/reference/comfyui_pipeline_audit.md:339`) and explicitly did not check runtime model presence (`:475`).

No executable Blender replay-state/camera/pass adapter was found in the inspected application engine and Comfy Python sources. `SyntheticElement` (`cinematic_synthetic.py:56`) is metadata, not a deterministic Blender scene. Blender authoring/export options discussed in `docs/reference/model-texture-pipeline-research.md:179` are useful research, not evidence that action state, projection, animation, materials and pass timestamps agree with Wolfcam.

**Consequence:** regenerating an asset is not guaranteed to reproduce it, and a style checkpoint does not make AI-generated frames historical truth. Existing immutable generated assets can still be used reproducibly if their content hashes are pinned. This finding does not require discarding ComfyUI or forbidding authored inserts.

**Smallest falsification:** stub Comfy submission and call `_run_one` twice with identical inputs; record submitted seeds/graphs instead of generating anything. Separately demand a command that consumes a tiny anonymous state+camera fixture and emits Blender color/depth/entity-ID frames and provenance; absence of that command is the current integration boundary. If another checkout has it, audit that exact artifact before creating a duplicate.

### R8 — DUPLICATED AUTHORITY: readiness taxonomies already disagree; another catalog would worsen it

`effect_templates.py:1169` describes material transformation as an asset swap waiting for a timed `zzz_` pack test. `render_profile.py:386` explicitly corrects that old premise: `remapshader`/`clearremappedshader` provide a live source-level route. Choreography has `PROVEN_RUNTIME`/`PROTOTYPE`/`DESIGNABLE` (`choreography.py:76`), while render profiles separately distinguish availability, source evidence, timing and delivery (`render_profile.py:1208`). These are useful axes, but no single execution result here binds all of them to backend+binary+asset+pass identity.

Camera documentation has similar drift: the header of `camera_compiler_v2.py:26` says sampled freecam is the default, while its actual entry point defaults to native CAM10 at `:455`; the lower-level writer still defaults to sampled (`cam10_writer.py:209`). The older cinematic audit's original camera-no-op finding (`q3mme_cinematic_audit.md:25`) is superseded by the current timeline writer (`timeline.py:284`) and documented LF repair (`cam10_writer.py:216`). Do not resurrect that repaired diagnosis.

**Consequence:** an auditor can honestly select the wrong status or backend by reading the wrong authority. New broad capability schemas are safe to defer until one renderer result can reference the existing plan, exact backend, requested operation, effective operation and evidence artifact together.

**Smallest falsification:** produce a read-only join for just three operations—material swap, camera spline, XRAY—across creative template, render route, emitter, consumer and proof. Any row without a consumer or artifact remains unproven even if a source capability exists. Correct conflicting documentary entries rather than adding a fourth readiness table.

## Executed no-write probe

From repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from creative_suite.engine import camera_compiler_v2 as c
k = [
    {'t_ms': 0, 'pos': (0, 0, 0), 'angles': (0, 0, 0), 'fov': 90},
    {'t_ms': 1000, 'pos': (0, 0, 0), 'angles': (0, 90, 0), 'fov': 90},
]
r = c.collision_check_dense(None, k)
print({x: r[x] for x in ('status', 'min_clearance_u', 'report')})
print(c.retime_to_span(k, 0, 2000))
PY
```

This proves R2's classification and R3's unchanged-angle retiming mechanically. It does not establish their frequency in the private corpus or assess cinematic quality. All other falsifications above are proposed bounded tests, not claimed completed runs.

## Decision before major implementation

Keep the architecture pause. Prove one existing preview with one clear action anchor, one directed camera move and explicitly enumerated beauty/depth outputs. First close the no-geometry validity hole and test recovered-camera subject alignment. Then require a pass collector that can reject a missing or misaligned frame. Only after that evidence should a Blender/backend boundary be shaped around demonstrated inputs and outputs. Selective wall removal, entity-ID mattes, projectile isolation, AI scene rendering and richer backend features remain individually gated capabilities; a single successful beauty shot cannot prove all of them.
