# PANTHEON engine synthesis — responsibility matrix (2026-09-01)

Grounded in runtime evidence, not source-reading alone, per the
2026-09-01 directive's own gate: written only after the camera backend,
engine-patch investigation, and all six free-win proofs actually ran on
real captures. Source docs this synthesizes: `cam10_runtime_contract.md`,
`camera_v2_report.md`, `free_wins_proof.md`, `dodge_quality_report.md`,
`replay-runtime-feasibility.md`, `engine_renderer_audit.md`,
`q3mme_cinematic_audit.md`, `material_system_audit.md`,
`cinematic_fx_transitions_research.md`, `model_animation_path.md`,
`model-texture-pipeline-research.md`, `comfyui_pipeline_audit.md`.

## Responsibility matrix

| Capability | Owner today | Evidence |
|---|---|---|
| `.dm_73` playback / protocol-73 correctness | **Wolfcam 11.3 (stock, shipped binary)** | Every capture this session; `why-wolfcam.md` |
| Seek | **Wolfcam 11.3**, `seekservertime` | Hundreds of proven captures |
| Camera — path execution | **Wolfcam 11.3**, dual backend: `NATIVE_CAM10` (default, up to 512 pts/file) + `FREECAM_SAMPLED` (per-sample `at`, ≤120 pts, independent fallback) | `cam10_runtime_contract.md`, `camera_v2_report.md` — both runtime-proven |
| Camera — path authoring, dense sampling, look-at, collision | **Python** (`camera_paths.py`, `camera_compiler_v2.py`) | Catmull-Rom resample, `retarget_lookat`, `collision_check_dense` — 22 tests, 2 real capture canaries |
| Camera — human-flown recording | **Wolfcam 11.3** `viewpos`+`logfile 2` → Python tail | `director_session.py`, this session's Path A work |
| FX (impact accents, trails) | **Wolfcam 11.3**, native `runfx`/`runfxat` + `.fx` script DSL | `free_wins_proof.md` proofs 1-2, both PASS |
| Materials — texture swap, color grade, live hot-reload | **Wolfcam 11.3** (`R_RemapShader`) + pk3 overrides (Python-built) | `free_wins_proof.md` proofs 3-4, PASS |
| Materials — normal/specular/PBR | **Not owned by anything reachable.** `renderergl2` in `_canonical/code/` has full PBR support but is unreachable from the shipped gl1-only 11.3 binary; QL maps lack deluxemaps so it wouldn't pay off on world geometry even if reachable | `material_system_audit.md` |
| Models — runtime format | **MD3, unchanged.** Wolfcam 12.6+ has IQM, but re-basing off 12.x to get it costs re-validating the entire capture-profile foundation for a format that doesn't add animation blending MD3 lacks anyway | `model_animation_path.md` |
| Models — authoring / reskinning | **Blender** (author) → **MD3 export** (existing addons) → **pk3 override** (no engine change) | `model-texture-pipeline-research.md` |
| Textures — AI generation | **ComfyUI** (existing SDXL/SD1.5 tile-controlnet pipelines) → pk3 → **Wolfcam** (live review via hot-swap) | `free_wins_proof.md` proof 5, PASS end-to-end once |
| Depth / analysis passes | **Wolfcam 11.3**, `mme_saveDepth` (real, MJPEG-lossy) | `free_wins_proof.md` proof 6, PASS |
| Demo intelligence (frags, projectiles, dodges, scenes) | **Python** (`engine/parser/`), cached once, queried forever | 36,607 recognized frags, 634 hero-tier dodges |
| Live control / director | **Python** (`director_session.py`, `/frags`) driving Wolfcam as a subprocess | No IPC exists (confirmed); relaunch-and-drive is the only remote-control shape available |
| Final render / compositing | **Not yet owned by anything** — ffmpeg-side assembly exists for V1 (`render_part_v6.py`, untouched) and V2 has `part01_assemble.py`; neither yet consumes a camera-v2 recipe end-to-end | Deferred |
| Music timing authority | **SceneRecipeV2** (separate concurrent workstream), Python | Not touched this cycle |
| q3mme (the fork, not wolfcam's inherited features) | **Reference/donor only.** Its camera math (`posBezier`) is a non-interpolating B-spline we deliberately avoid; its FX DSL and `.cam10` format are already inherited into wolfcam 11.3 and don't need porting | `q3mme_cinematic_audit.md` |
| ioquake3 (the variant, not wolfcam's `renderergl2`) | **Reference/donor + easiest smoke-test build target**, not itself a runtime | `replay-runtime-feasibility.md`, `engine_renderer_audit.md` |

## The corrected story of this cycle, briefly

1. Built a real camera compiler: Catmull-Rom dense resampling, decoupled
   look-at with damping, collision-checking that runs on the dense
   curve. Found and fixed a real, confirmed ceiling
   (`MAX_AT_COMMANDS=128`) along the way.
2. Attempted a source patch for what was believed to be an engine bug in
   `playcamera`. The investigation itself was excellent — it found the
   repo's wolfcamql source is a different major version (12.7) from the
   shipped binary (11.3), recovered the exact ABI diff via DWARF, built
   a working shim, and successfully produced a patched, loading,
   rendering DLL via a freshly-installed mingw-w64 toolchain.
3. That investigation's own regression testing then surfaced the real
   root cause: **our own `.cam10` writer was corrupting every file it
   produced** (CRLF from `Path.write_text()`). Fixed with one keyword
   argument. Personally re-verified, not taken on faith: the original
   failing scenario now runs clean on the stock, unpatched binary.
4. Net result: `NATIVE_CAM10` is a real, working, higher-capacity backend
   requiring **zero engine modification**. The patch investigation is
   preserved as documentation of a real (much smaller) 12.7-only
   regression, not deployed.
5. All six "free win" cinematic capabilities (FX DSL, ghost trail,
   color grade, shader hot-swap, ComfyUI-to-engine loop, depth pass)
   proved PASS on the unmodified binary — the actual biggest lever for
   the "wow factor" ask turns out to need no engine work at all.
6. Dodge/near-miss data went from a 100%-complete but 38%-too-common
   broad detector to a validated, evidence-scored hero tier (634 rows,
   88.8% precision vs 25.3% in the broad population).

## What's still open, explicitly

- **Timescale/A-V drift measurement** (directive §23-24) — not run this
  cycle. Camera stability was the prerequisite and is now met.
- **First `PROJECTILE_BRIDGE` transition** (directive §42) — the
  building blocks (real cached projectile tracks, camera-follow, native
  playback) all exist and are proven individually; the actual two-scene
  match-cut has not been assembled.
- **`/frags` Director controls** (directive §43) — deliberately last per
  the directive; nothing here blocks it, but it hasn't been started.
- **Final render/compositing consuming a camera-v2 recipe end-to-end** —
  the compiler produces a capturable cfg; nothing yet stitches that into
  `part01_assemble.py`'s segment-list model.
- **Chained multi-window capture** for shots exceeding even
  `NATIVE_CAM10`'s 512-point ceiling — unlikely to matter soon, noted for
  completeness.

No bulk V2 master rendering was performed. V1 was not touched.
