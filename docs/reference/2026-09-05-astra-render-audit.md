# Render reproducibility audit — 2026-09-05

**Refreshed verdict:** real `ShotSpec`, `FrameTruth`, a synthetic demo compiler, instruction proof, presenter film and roster work **do exist in the ignored `pantheon-prologue` worktree**. The initial main-checkout-only absence finding is superseded. This is a partially executed native pipeline, not merely a schema proposal. Its remaining blockers are pass requests that do not drive outputs, incomplete frame provenance across frozen history, and proof-specific capture behavior. Preserve and audit that implementation before creating another architecture.

This is a skeptical source audit, not an implementation proposal or visual sign-off. Scope: `/mnt/g/QUAKE_LEGACY`, initially HEAD `bb23f2d4`, refreshed at main HEAD `430645e0`, plus `.claude/worktrees/pantheon-prologue/engine/pantheon`, its tests and existing `.tmp` artifacts. The project was changing concurrently; line references are to files read during this audit. No engine, renderer, ComfyUI job, batch, installation, database write, or real capture was executed. Pure Python camera and AST probes ran with bytecode writes disabled. Existing files were inventoried, not played; pixel acceptance below is attributed to supplied history rather than newly claimed by this auditor.

In references below, **P/** means `.claude/worktrees/pantheon-prologue/engine/pantheon/`, **W/** means `.claude/worktrees/pantheon-prologue/`. Unprefixed application paths refer to the main checkout.

## Attachment history and current direction

The supplied attachment, lines 2301–4602, records **Proof B accepted**: demo-authored model identity works; bright-skin tint depends on team relation to POV; exposure settings that are latched must enter at launch. The later user correction explicitly supersedes the earlier universal green/gold analysis-skin proposal. Use recognizable Quake roster characters as separate authored presenters, vary casting across films, and preserve historical appearance. Both ACTOR_COPY and PRESENTER are allowed; neither requires replacing historical actors.

Proof C is the requested next controlled 3v3 proof with a separate presenter, frozen history, moving camera, dialogue and exact restoration; real-event Proof 02 follows it. These requests are not statements that those proofs were completed. Current files include `P/roster.py`, `P/cast_proof.py`, `W/docs/reference/character_roster.json`, and cast metadata/FrameTruth. A cast AVI was present in main shared staging. No completed Proof C artifact or implementation was found in the searched worktree. The working session remains **PANTHEON PROLOGUE INTRODUCTION**; this audit does not take ownership of its casting work.

Existing evidence located: `W/.tmp/shots/proofb/PROOF_B_IDENTITY__authored.avi` and control variants; `W/.tmp/shots/INSTRUCTION_LAYER_PROOF_01.mp4`; `W/.tmp/shots/DIEGETIC_PRESENTER_PROOF_01.mp4`; instruction report and FrameTruth under `W/.tmp/synthetic/`. The instruction report says `all_restored=true` for its one two-actor break. That is an existing authored-state check, not proof of six-actor historic replay restoration or of all rendered pixels.

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
| Native synthetic execution | `P/scenario.py`, `P/compiler.py:1`, `P/shot.py:132`, `:167` | RoundScenario → authored `.dm_73` → actual ShotSpec render consumer reusing Wolfcam capture helpers. |
| Synthetic frame state | `P/frame_truth.py:81`, `:150` | FrameTruth emitted from the authored scenario at its snapshot rate. Real implementation; not a universal historical replay-state exporter. |
| Instruction and casting | `P/instruction.py:161`, `P/presenter_film.py:29`, `P/roster.py:125`, `P/cast_proof.py:165` | Concrete consumers and presenter roster/profile work. Proof C integration remains unproven. |

The initial exact-identifier search covered main application Python and missed an ignored worktree. Refresh found executable `ShotSpec` and `FrameTruth` there. No `RenderJob` or `PassPlan` implementation was found in the refreshed P/ Python tree, but `ShotSpec.passes` is already a concrete pass-intent surface. Missing names are not the issue; missing behavior is.

## Material findings

### R1 — ARCHITECTURAL BLOCKER: native proof architecture exists, but historical/frame/backend integration is incomplete

The prologue now has a runnable source→film route: `P/compiler.py:1` emits synthetic demos; `P/frame_truth.py:150` samples their authoring scenario; `P/shot.py:167` films them through existing capture helpers. This supersedes the initial absence conclusion. However, `ShotSpec` at `P/shot.py:132` stores a source path, time range, visual profile, passes and a truth-reference path. Its render function never consumes `truth_reference` or any frame state. An AST read found only these `spec` attributes in `render`: `end_s`, `shot_id`, `source`, `start_s`, `unsupported_passes`, `visual`.

Instruction building is currently synthetic scenario rewriting: `P/instruction.py:161` builds a new scenario on the edit clock, repeats actor keyframes through a freeze (`:171`), adds a separate analysis client (`:197`), and uses the first source camera (`:167`). It does not establish literal original demo serverTime frozen while an independent native camera/presenter clock advances. It can legitimately *depict* frozen action, but that mechanism must be distinguished from direct historical replay.

`ActorTruth` (`P/frame_truth.py:31`) lacks layer, model/skin and actor-lifetime identity, although all three matter to the requested historical/presenter distinction. Its single `Frame.actors` dictionary at `:75` does not itself provide separate immutable HistoricalFrameTruth and AnalysisFrameTruth collections. Scene objects mark `Layer.ANALYSIS` and exclude it from roster counts; that is useful, but the exported frame type does not preserve every necessary distinction. Main preview and PantheonScene remain separate consumers; arbitrary choreography FX still have no discovered production call to `pantheon_scene.compile_fx_cfg_lines`.

**Consequence:** a correct synthetic teaching clip does not establish that a real source event can be replayed with immutable appearance/clock/provenance and interchangeable pass backends. Another new abstraction should not duplicate this work.

**Smallest falsification:** anonymous two-history-plus-one-presenter fixture. Require serialized frame data to identify layer and appearance for every actor and map each edit sample back to one historical instant throughout the hold; then round-trip it and verify counters, camera target and resumed historical state. Deliberately swap the truth-reference file while keeping the demo path unchanged: the current render consumer cannot detect the mismatch because it does not read that reference. No capture is needed.

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

### R4 — CORRECTNESS BUG / MISSING CAPABILITY: new ShotSpec passes do not drive the renderer

The new `P/shot.py:36` declares BEAUTY, ACTOR_XRAY, DEPTH, ACTOR_ID, ENEMY_MASK, NORMAL and MOTION. Unsupported IDs/masks/normals/motion are honestly rejected at `:176`. But supported pass intent does not control emission: `spec.passes` is used only in the unsupported check, and actual XRAY depends independently on `spec.visual.xray` at `:108`. DEPTH is accepted as `SUPPORTED_UNPROVEN` at `:52`; no pass-driven `mme_saveDepth` setting appears in `render`. The collector takes the first AVI at `:261` and returns a single Path at `:268`, not requested pass outputs. A requested ACTOR_XRAY pass with an ordinary visual profile can therefore return ordinary beauty.

The older main preview separately sets `mme_saveDepth` (`director_preview.py:1072`) but also collects only AVI (`:2013`). Canonical source reads `GL_DEPTH_COMPONENT` (`renderercommon/inc_tr_init.c:886`) and includes named depth TGA output (`:837`); other formats depend on active capture flags. The P/ support comment describes a second AVI. That is not an established format contract for the installed binary. Neither path validates matching depth frame count/time-map/camera identity.

**Consequence:** the new names are valuable but do not yet prevent silently dropped supported requests. ACTOR_XRAY also means a relation-wide silhouette treatment, not an entity-ID mask.

**Smallest falsification:** stub stage/config/process/move helpers and render `passes=(ACTOR_XRAY,)` with `VisualProfile(xray=False)`, then DEPTH. Inspect emitted cvars and returned output list. Require explicit rejection or the requested stream. Follow with four beauty frames/three depth frames and require the collector to reject the mismatch. The read-only AST inspection already confirmed pass intent has no render consumer beyond the unsupported check.

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

The prologue has already fixed an important native determinism defect: `P/shot.py:211` loads the cvar inventory, classifies values as latched/live, and passes latched values at launch (`:229`). This is implemented behavior, supported by the accepted Proof B account, not pending architecture. However, unknown inventory names default to live (`:216`), no observed effective-cvar manifest is returned, and `ShotSpec.as_dict()` stores the visual profile **name and xray boolean** (`:152`), not its full `extra`/`unpin` values or a hash. Thus different render settings can have the same serialized shot description. `render()` returns one path, not a request/effective-state/output proof bundle. The smallest no-capture check is two same-named profiles with different exposure extras: compare serialized shot descriptions and emitted launch settings.

ComfyUI's texture path is real, but `_run_one()` chooses a fresh random seed (`creative_suite/comfy/full_overnight.py:419`). Its ledger writes asset, pipeline, denoise and output path (`:244`); this call does not persist seed, resolved graph, model bytes, node versions or source-type identity. Resume accepts an existing output path (`:715`) before resolving the optional upscale source (`:727`). The prior audit already documented mixed provenance on resume (`docs/reference/comfyui_pipeline_audit.md:339`) and explicitly did not check runtime model presence (`:475`).

No executable Blender replay-state/camera/pass adapter was found in the inspected application engine/Comfy or P/ Python sources. The new native synthetic compiler **does exist** and is useful. Blender authoring/export options discussed in `docs/reference/model-texture-pipeline-research.md:179` remain research, not evidence that action state, projection, animation, materials and pass timestamps agree with Wolfcam. The attachment explicitly defers Blender for the native Proof C; an absent Blender adapter is therefore safe to defer for that milestone, while remaining a blocker to claims of completed multi-backend reproduction.

**Consequence:** regenerating an asset is not guaranteed to reproduce it, and a style checkpoint does not make AI-generated frames historical truth. Existing immutable generated assets can still be used reproducibly if their content hashes are pinned. This finding does not require discarding ComfyUI or forbidding authored inserts.

**Smallest falsification:** stub Comfy submission and call `_run_one` twice with identical inputs; record submitted seeds/graphs instead of generating anything. Separately demand a command that consumes a tiny anonymous state+camera fixture and emits Blender color/depth/entity-ID frames and provenance; absence of that command is the current integration boundary. If another checkout has it, audit that exact artifact before creating a duplicate.

### R8 — DUPLICATED AUTHORITY: readiness taxonomies already disagree; another catalog would worsen it

The latest casting direction has begun landing in `P/roster.py:125` (`PresenterProfile`) and `P/cast_proof.py:165` (ShotSpec consumer). The inventory reads actual pak entries (`P/roster.py:65`), while `can_gesture` at `:53` is only a frame-count heuristic, not a pixel-tested gesture guarantee. Proof C is not yet established by these files. Existing instruction authoring still chooses the historical actor's model plus forced `bright` skin (`P/instruction.py:201`) and writes relation-wide tint (`:418`). Its comment that analysis is the **only** bright actor (`:399`) is not enforced and does not hold for arbitrary historical scenes. This can recolor unrelated historical bright actors in the same relation group, exactly the collision the latest user direction avoids. Preserve this as a controlled ACTOR_COPY prototype; do not call independent roster-selected PRESENTER integration complete until the instruction consumer resolves that profile and preserves historical appearance.

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

Keep the pause on **major new architecture**, and continue auditing the existing PANTHEON PROLOGUE INTRODUCTION work rather than rebuilding it. Bank accepted Proof B and the actual ShotSpec/FrameTruth/native compiler. Finish the already requested cast evidence; treat Proof C as pending until a separate selected presenter, edit-time camera/dialogue, frozen historical state, original appearance and followed-POV restoration are demonstrated together. In the existing runner, make supported pass requests executable or explicitly rejected, and bind effective settings and output identities to their source/frame truth. Keep Blender deferred for native Proof C. Selective wall removal, entity-ID mattes, projectile isolation and AI scene rendering remain individually gated capabilities; a successful beauty shot cannot prove them.

Refresh verification: files above were re-read after discovering the worktree; existing artifact paths were listed; the AST consumer probe completed without importing execution modules or writing runtime data. No new capture was performed and no Proof C completion is asserted.
