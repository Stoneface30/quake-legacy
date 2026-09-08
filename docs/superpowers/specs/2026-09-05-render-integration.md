# Render integration blueprint — all three follow-ups

Status: concrete design and prerequisites; not a claim of implemented backends.
User direction: cover shared render contracts, Blender calibration, and both
explainers. The supplied research establishes the direction. Existing
`production_contract.py`, `action_truth.py`, `scene.py`, `render_profile.py`,
`director_preview.py` and `cinematic_synthetic.py` remain the starting points.

## 1. Shared ShotSpec, RenderJob and FrameTruth

Add a versioned shot specification above existing backend plans, with:

- Source identity: demo content hash, source kind (historical, reconstructed,
  synthetic), server-time interval in integer milliseconds, and local source
  reference kept separate from public metadata.
- Evidence references: Scene ID, ActionTruth occurrence IDs and optional
  RoundScenario ID. Reuse the production provenance classes; preserve absent
  health, armor and other unknown values as unavailable.
- Time mapping: rational output FPS and explicit piecewise output-frame to
  source-time mapping. Trims, freeze holds, retimes and replay repetitions
  must remain reproducible without changing the canonical event time.
- Camera: source coordinate system, position/orientation/FOV, collision policy
  and versioned CameraPlan reference. Camera authorship is not historical
  actor truth.
- Visual profile: actual resolved profile hash, assets and effect protocol.
- Pass plan: requested output passes, dimensions, pixel/depth conventions and
  backend capabilities. An unsupported pass fails explicitly; it never
  silently substitutes beauty or an estimated depth map.
- FrameTruth sidecar: camera, actor transforms, projectiles and round state
  at each output frame, linked back to source time and provenance. Unknown
  actor state stays unknown; interpolation is labelled derived/reconstructed.
- Generative treatment: optional conditioning inputs and outputs carrying
  generative provenance. Such output never writes game evidence tables.
- Output provenance: canonical serialized spec hash, backend/version, asset
  hashes, resolution, color space, frame count and validation results.

RenderJob adds job ID and terminal lifecycle to the immutable spec:
MISSING → QUEUED → RENDERING → READY, or FAILED/CANCELLED. Retry is explicit,
idempotent, and refers to the same spec. Queue capacity remains one capture;
status polling must not schedule repeated failed work. READY requires actual
files, expected dimensions/frame count and successful output validation.

Integration order:

1. Introduce validation and serialization tests for the contract.
2. Adapt the existing director preview plan into ShotSpec without changing
   captures; compare generated configs and frame mapping against the current
   canary. This is the compatibility gate before new backends.
3. Attach FrameTruth and PassPlan references to output provenance.
4. Add backend capability registration and one explicit execution entry point.
   Keep existing API routes as adapters; do not create a second queue/store.

Tests must cover stable hashes, unknown evidence, synthetic/historical
separation, repeated source times during freezes, cancellation, retry,
unsupported passes and incomplete outputs. No corpus extraction is needed.

## 2. Minimal Blender–Wolfcam calibration proof

Prerequisite: locate an installed Blender runtime and the other session's
compiler/CameraPlan sources. Verify an importer revision compatible with that
runtime. No unreviewed package installation is part of this blueprint.

Use local read-only Campgrounds BSP assets and one MD3 actor. Produce the same
known camera and actor positions with both renderers. Test multiple points
across the frame and multiple camera orientations, not only a centered point.

Lock and record:

- Quake world axes and units versus Blender world axes and units.
- Quake view angles versus Blender camera local axes.
- Horizontal/vertical FOV conversion, aspect ratio and pixel aspect.
- Camera origin and clipping conventions.
- Server milliseconds versus output frame timestamps and animation samples.

Deliver the two images, a comparison sheet, point-coordinate residuals and
the reproducible scene/spec. Proposed acceptance is ≤1 pixel error for test
markers at the target resolution; report every residual rather than only the
best point. This is geometric calibration, not shader-fidelity certification.

Only after calibration passes: generate a visible beauty pass, isolated actor
pass with world occlusion disabled, and world depth. XRAY compositing needs
those visibility controls. Cryptomatte alone cannot reveal an occluded actor.

## 3. Separate Quake and Clan Arena explainers

Prerequisite: reconcile the other Claude session's RoundScenario/compiler
work before building a competing synthetic protocol implementation.

Deliver two standalone review proofs:

1. **Quake:** real engine footage establishing movement, vertical space,
   weapons and readable action. Any claimed effect must actually appear.
2. **Clan Arena:** demonstrate team/round structure, alive-state changes,
   elimination and victory using observed real-round transitions as the
   protocol oracle. Synthetic staging must be explicitly labelled and never
   enter historical evidence tables.

For each synthetic behavior, compare several real rounds, canonicalize the
state transition, generate the corresponding transition, and validate it in
Wolfcam. Pin round-time semantics, alive counters, animation toggle bits,
obituary fields and frame identity before composing explanatory overlays.

Each proof needs its own video, contact sheet, source/spec references and
human review. Keep shots long enough to understand; no abstract 2D game
replacement and no rapid fragments pretending to demonstrate a mechanic.
Combine the two sections only after each is accepted independently.

## Prerequisite information still needed

- The working directory or handoff files from the other Claude synthetic-demo
  session. These named components were not found in this checkout.
- Blender executable/location if already installed outside the checked paths.
- Existing approved shot lists or cuts for the two explainers, if that session
  has them. Preserve prior creative decisions rather than invent replacements.

These are concrete missing inputs, not a request to re-approve the direction.
