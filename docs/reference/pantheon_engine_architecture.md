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
   → protocol registry                    engine/parser/protocol.py, checked
                                          against the engine's own tables
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
        ├── PANTHEON_QUAKE_OFFSCREEN  hidden desktop, proven
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
| `performance_traces.db` | content-addressed zlib cache, for traces worth keeping. One copy per distinct trace, one of four declared reasons, a byte budget and eviction that cannot touch a deliberate copy. |
| `performance_templates.db` | real segments, admitted only if physically continuous. |
| `map_geography.db` | regions, layers, routes, jump-pad arcs, teleport links AND the 64u spatial cells, adjacency and encounters. One geography store. |

**Measured 2026-09-06** (`F:\QUAKE_LEGACY_STORE`): the compact index holds
4,292 of 4,292 distinct demos with 0 errors, 4,543,086 actions across 59
maps, 3.32 GB, 786 bytes per action. The v1 index it replaces is 87.64 GB
for 2,097,455 actions on 3,928 demos (44,864 bytes per action) and is marked
`OBSOLETE_REPLACED`; the equivalence evidence is
`F:\QUAKE_LEGACY_STORE\index_equivalence.json` — coverage COMPLETE,
identity IDENTICAL on 60 sampled demos, traces IDENTICAL on 7 rebuilt from
locators. Geography covers 18 maps: 220 regions, 63 layers, 3,214 routes,
659 jump-pad arcs, 15 teleport links, 29,783 walked cells, 472,305 adjacency
pairs, 108,656 encounter pairs. 40 further maps have too few demos to learn
a structure from and are reported, not silently dropped.

**Index actions; do not duplicate performance.** The first index carried a
45 KB trace per action, reached 94 GB and filled a drive. A trace is
reconstructed from its locator through the same extractor that produced it;
`doctor` proves that per kind on every run.

**What the trace cache keeps.** `engine/pantheon/trace_cache.py` answers the
question that produced the 94 GB, which is not "can we cache a trace" but
"which ones". Four declared reasons and no others: TEMPLATE (the template
library points at it), GOLDEN (a proof depends on it not changing), SELECTED
(a human or a director chose it), FREQUENT (rebuilt often enough that
rebuilding is the waste). The first three are deliberate and eviction never
touches them; FREQUENT is earned by use and lost the same way, so the cache
is bounded without a proof's fixture ever vanishing to make room. Use is
counted where a trace is fetched, so "frequent" means frequently REBUILT.

Wired today: TEMPLATE, from the template library, and FREQUENT, from
`trace_cache.trace()`. GOLDEN and SELECTED are fed by `warm()` with an
explicit set; no caller feeds them yet. Measured on this machine: 10,710
traces, 74.5 MB of a 512 MB budget, all TEMPLATE. The vocabulary closing
caught 10,710 rows labelled `template` in free text, written before there was
a list of reasons; `--normalise` brought them in and `doctor` fails on any
reason nobody declared.

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

## PANTHEON_QUAKE_OFFSCREEN

The reviewer must never take the screen. The backend does not rewrite the
renderer: it runs the SAME WolfcamQL 11.3 binary on a **separate Windows
desktop** (`CreateDesktopW`, then `STARTUPINFOW.lpDesktop`). A window created
there cannot reach the interactive desktop, its taskbar or its foreground --
by construction, because those belong to a desktop object the process is not
on. `SW_SHOWMINNOACTIVE` remains defence in depth and is explicitly not this
mechanism: a minimised window is still on the user's desktop.

Proven on this machine, 2026-09-06:

| | Result |
|---|---|
| GUI process isolation (harmless process, not the game) | no visible window, foreground unmoved |
| Engine GL context on the hidden desktop | `GL_RENDERER: NVIDIA GeForce RTX 5060 Ti/PCIe/SSE2`, clean exit |
| Real capture through the project's own staging and cfg | AVI produced, 1920x1080, 8.5 s |
| Visible window / stolen foreground during captures | none / none |

**The pointer, added 2026-09-06.** The operator reported the mouse boxed into
the invisible window while a capture ran. Measured on a real capture:
`GetClipCursor` returned `(107, 130, 2027, 1210)` -- the render window's
rectangle -- for the whole run, on a 3000x1440 desktop. `in_nograb 1` and
`in_mouse 0` each released it and each still filmed; the offscreen launch now
sets both, the watcher samples the clip rectangle every run, and a capture
that confines the pointer is not `ok`. A hidden window that owns the mouse is
worse than a visible one, because nobody can see what has taken it.

`engine/pantheon/offscreen.py` watches the operator's desktop THROUGHOUT a
run, not only afterwards, and attributes a stolen foreground to the render
only when the foreground belongs to the render process -- an operator
switching app mid-capture is not a failure. The render permit still applies:
offscreen removes the stolen screen, not GPU and disk contention.

## The engine inventory

Every command and cvar this project could touch, graded by evidence, from four
inventories kept apart because they are four different programs.

| Source | What it is | Items |
|---|---|---|
| RUNTIME_11_3 | `cvarlist` and `cmdlist` with no filter, asked of the running client in one offscreen session | 1,444 cvars, 307 commands |
| SOURCE_12_7 | a static scan of the wolfcamql source tree, which is a LATER build than the one on disk | 1,718 cvars, 428 commands |
| BINARY_11_3 | strings inside the executable we actually run | 477 names |
| Q3MME | a different engine's vocabulary | 120 cvars, 32 commands |

Grades: RUNTIME_REGISTERED, RUNTIME_ACCEPTED_UNSET, TARGET_BINARY_RECOGNIZED,
SOURCE_REGISTERED, DOCUMENTED_ONLY, UNSUPPORTED_TARGET, UNKNOWN. Only
RUNTIME_REGISTERED may be used in production, because 11.3 runtime outranks
12.7 source.

**Measured 2026-09-06:** 2,345 items graded, of which 1,729 are live in 11.3,
447 exist only in the 12.7 source, 129 belong to q3mme, 22 are silent no-ops
the runtime accepted and never registered, and 3 are named only in this
project's own tables. 102 items map to 34 semantic capabilities. **Zero are
unclassified**, and `doctor` fails if that ever changes, so a command
appearing in a future census cannot pass unnoticed.

### What the census settled

- **`cg_forceTeamModel` does not exist.** Not in the runtime, not in the 12.7
  source scan, not in the binary strings. It was UNKNOWN because the earlier
  family probe never asked a wildcard that could match it. Forcing teammates
  is the `cg_team*` family, which is registered; there is no separate switch.
- **The recorder's own appearance cannot be forced.** There is no `cg_own*`
  or `cg_self*` cvar of any kind. REVIEW leaving self authentic is an engine
  property, not a preference.
- **The actor-id pass has no route.** `mme_saveStencil` is present but
  USER_CREATED, so setting it does nothing at all. That is a reason to build
  the Blender backend, not a switch to try again.
- **The depth switches are real and the pass is unproven.** `mme_saveDepth`,
  `mme_depthFocus` and `mme_depthRange` are registered; whether a depth file
  is written and collected has never been checked, so DEPTH_CAPTURE is
  partial and below the usable bar.
- **Piping capture to an encoder is not available.** `cl_aviPipeCommand` and
  `cl_aviPipeExtension` are USER_CREATED. Capture is the built-in MJPEG AVI
  writer and the transcode happens afterwards in ffmpeg, where it already did.
- **`capture` and `dof` are not 11.3 commands.** `capture` is q3mme's alone;
  `dof` is in the 12.7 wolfcam source too, so the later build imported it and
  the one on disk did not get it.
- **Time has more routes than we thought.** `cl_freezeDemo` and
  `cl_freezeDemoPauseVideoRecording` are registered, so holding the whole demo
  is possible and is a different thing from `entityfreeze`, which holds one
  body while the rest runs. The seek family is round-aware: `seeknextround`
  and `seekprevround` exist alongside `seekservertime`.

### The overlay colour, resolved from code

The X-ray silhouettes filmed blue while the profile asked for PANTHEON green.
`cg_players.c` colours the overlay with `SC_ByteVec3ColorFromCvar`, which
reads `cvar->integer` -- so the family is a PACKED INTEGER, exactly like the
rail family, and `"60 235 90"` went through `atoi` as 60 = `0x00003C`, a dark
blue. That is precisely what the frame showed. `color_format` said
DECIMAL_TRIPLE and is corrected, with the drawing code cited.

The same reading gives the population rules: mode 1 draws everyone the client
has, mode 2 only enemies, mode 3 only non-enemies; enemies take
`cg_whEnemyColor` and **everyone else**, teammates and self alike, takes
`cg_whColor`.

## The layer contract

One authority per layer. A layer may read the one below it and must not know
the one above exists.

| Layer | Module | Owns |
|---|---|---|
| DemoProtocolRegistry | `engine/parser/protocol.py` | every wire number, from the engine's own tables |
| CanonicalTruth | `engine/parser/` | what the demo says, decoded |
| PerformanceTrace | `performance.py` | how a body moved, aimed and fought |
| FrameTruth | `frame_truth.py` | one clock, recorded pose, sound intent |
| ActionGraph | `action_graph.py` | the semantic reading, with evidence |
| Scene / RoundScenario | `scenario.py` | what is being authored |
| MapSpatialIndex | `map_spatial_index.py`, `geography.py` | where things happen |
| ReviewMoment | `review_moment.py` | the one object a reviewer reads |
| HumanDirection | `creative_intent.py`, `director_notes.py`, `ideas.py` | what the director said, verbatim |
| MomentPossibilities | `possibilities.py` | what could be done, and why |
| EffectRecipe | `effect_recipes.py` | the film grammar, as semantics |
| ChoreographyPlan / TimeMap / CameraPlan | *not built* | how it would be staged |
| VisualProfile | `visual_profile.py` | film words to backend values, in one function |
| FilmProfile | `defaults.py` | the project's versioned defaults |
| ShotSpec / RenderJob | `shot.py`, `backends.py` | what to film |
| BackendPlanner | `backend_planner.py` | which backend takes which pass |
| CapabilityRegistry | `capabilities.py` | what a backend can do, and how we know |
| VisualProofRegistry | `visual_proof.py` | what a person judged, and when it expired |

Three classes of module, enforced by
`creative_suite/tests/test_pantheon_headless_boundary.py`:

- **HEADLESS** — may not import a backend and may not name one.
- **NAMES_BACKENDS_AS_DATA** — may name a backend (a planner must; a proof is
  only valid for the backend it was taken on) but may not import or launch one.
- **BACKEND_ALLOWED** — may spawn the engine, through the render permit.

## VisualProofRegistry

Some questions are settled by arithmetic and some only by a person with eyes.
`visual_proof.py` keeps the second kind, so they are asked once.

    UNTESTED · AUTOMATED_PASS · NEEDS_VISUAL_CONFIRMATION ·
    VISUALLY_PROVEN · VISUALLY_REJECTED · REGRESSION

A proof is banked against the three things that can invalidate it -- the
backend, the profile and the engine version. Ask for it with those and you get
the banked answer; ask with a different profile and you get REGRESSION, not a
stale yes. No automated result promotes itself: only `judge()` produces
VISUALLY_PROVEN, and it records what the person said.

Seeded 2026-09-06 with nine capabilities: four proven (the green Keel review
enemy, no visible window, no stolen focus, no burned name on a public export)
and five waiting on a person -- among them the X-ray overlay, which was filmed
under the old window backend and has not been re-shot.

**Do not ask the user to confirm** parser fields, timestamps, identity hashes
or collision maths. **Do ask** whether the enemy is visibly Keel, whether a
camera feels right, whether an effect communicates the action.

## EffectRecipeRegistry

`effect_recipes.py` holds the film grammar as semantics: what a treatment is,
what truth it needs, when a director would reach for it, and which
capabilities a backend would have to have. It contains no cvar, no command and
no camera maths -- a test enforces that.

    CONCEPT · SEMANTICALLY_SUPPORTED · BACKEND_SUPPORTED ·
    VISUALLY_PROVEN · PRODUCTION_READY

Status is DERIVED on every call from the capability and proof registries, so
it cannot go stale and cannot be declared. Twenty recipes are registered; ten
have a backend for every capability they need; none is PRODUCTION_READY,
because that needs a run through the pipeline rather than a registry entry.

## The director's list

`ideas.py` holds all 306 consolidated ideas verbatim, and `director_notes.py`
holds the 28 original free-form notes they were consolidated from -- typos
included, because a cleaned-up note is a different note. The columns the
director asked for (required truth, best backend, status, visual proof) are
derived per row; storing them would mean 306 stale rows the first time a
capability moved.

Seventy-four ideas are carried by a recipe. Two hundred and thirty-two are
not, and that list is the backlog. Reading the original notes turned up
twenty-three requirements the numbered list had lost, sixteen of which no
recipe carries -- the rail beam building along its path like Wanted, the
scoreboard rendered into the map's ad space, damage staying above the enemy's
head, the out-shaft statistic, the mishap corpus. Four carry a caution because
building them naively would produce a false claim: the rail is hitscan, so a
"beam building" shot is a reconstruction and must be labelled one.

## MomentPossibilities

`possibilities.py` answers "what could we do with this moment" from the
indexed evidence, with a reason attached to every answer, and it renders
nothing. Compatibility is DERIVED; a recommendation is a MACHINE_SUGGESTION;
the choice is HUMAN. Those three never merge.

A "no" names what is missing -- the truth the demo does not carry, or the
capability no backend has proven -- which is why the output is useful rather
than discouraging.

## Backend A/B conformance

Before the offscreen backend became the default, it was compared against the
one that has been trusted: `engine/pantheon/conformance.py` films ten
representative moments twice, through the same staging, the same capture cfg,
the same command line and the same watcher, differing in exactly one
variable -- the desktop the process lives on. The moments come from the
headless performance index and carry a demo hash, a client slot and a
serverTime; no name, nickname or identifier enters a case.

RAIL · LG · ROCKET · GRENADE · JUMP_PAD · TELEPORT · MULTI_PLAYER_ROUND ·
LOW_LIGHT_MAP · PROJECTILE_IMPACT · DEATH.

**What is measured, and why not pixels.** Two runs of the client are not
reproducible to the pixel. The stills say why: both legs hold the same
instant -- same beam, same bodies, same explosion -- with the camera a
fraction of a frame apart in yaw, so every edge in a 1920x1080 frame lands a
pixel over. The first run of this suite duly reported a fifth of the pixels
differing between the two legs, and the SAME fifth between two runs of one
leg. A per-pixel test therefore cannot tell a backend apart from a rerun.

What a reviewer would notice is measured instead, on an area-averaged
thumbnail after the frames are matched to the same instant: colour
distribution (a 32-bin per-channel histogram intersection), exposure, the
share of the frame carrying the review profile's forced green, and the length
of the clip. Each is read as the MEDIAN across sampled frames -- the worst of
six samples is the noisiest statistic available, and one control run scored
0.09 on its worst frame and 0.007 on its median.

**Three offscreen captures, not one.** With a single control the noise floor
is one number drawn from a noisy quantity, and the verdict moved between runs
of this suite: two cases came out EQUIVALENT on one run and DIFFERENT on the
next, on readings around 0.01 where the control also sat. So B is filmed three
times: three A-against-B readings, three B-against-B readings, and the
question becomes one a reader can check -- is A further from a B than the Bs
are from each other? A reading inside that spread passes; one inside a fixed
tolerance a reviewer would accept passes and says so; anything else is a
difference. A case whose CONTROL exceeds the tolerance is INCONCLUSIVE, not
DIFFERENT: the backend disagreeing with itself is not the desktop's fault.

The suite can fail: `creative_suite/tests/test_backend_conformance.py` drives
a washed-out backend, an enemy that lost its green, a short clip and a wild
control through the verdict and requires DIFFERENT for each.

**State of the evidence, 2026-09-06.** Three full runs were filmed under the
earlier single-control method; the last is
`docs/reference/2026-09-06-backend-ab-conformance.json` (7 of 10 EQUIVALENT)
and its A/B stills are under
`docs/visual-record/2026-09-06/backend_ab/`. Those runs are what showed the
single-control method to be unstable, which is why the method changed; the
three-capture method has been filmed on one case so far. The suite is not a
thing to run repeatedly for reassurance -- film it once and look at the
frames:

```
python -m engine.pantheon.conformance                  # all ten
python -m engine.pantheon.conformance --only RAIL LG   # a couple
```

## The review path films offscreen

`creative_suite/engine/review_proxy.py` -- the provider behind every clip in
the /frags control room -- now films through `PANTHEON_QUAKE_OFFSCREEN`. The
UI is unchanged: the same states, the same cache keys, the same windows. The
backend is deliberately NOT part of the cache key, so every proxy already
READY stays READY and stays served.

Three columns record what made each file: `backend`, `engine_version` (the
review profile id) and `source_demo`. A row that predates the migration reads
NULL, which is the truth -- it was filmed by the visible window.

There is no silent fallback. Where a hidden desktop cannot be created at all,
the job FAILS and says so; opening a window instead is how a rule stops being
true without anyone noticing. `CS_PROXY_WINDOW=1` asks for the old visible
capture explicitly, for an operator who wants to watch one.

Two corrections came out of this. The offscreen capture was passing no master
profile name, which does not mean "no profile" -- it means the BATCH master,
the one that once burned an opponent's name into a public clip; the review
path now names the review master in the cfg AND on the launch line, where the
latched exposure cvars are applied. And `review_proxy` resolved ffmpeg
relative to the code rather than the project, so every proxy in a git
worktree failed on a missing binary; the tools resolve the way the databases
already do.

## Capabilities and visual profiles

A caller asks for a capability or a named profile, never a cvar.
`engine/pantheon/capabilities.py` records what each backend can do and the
strongest evidence for it (DOCUMENTED / SOURCE_REGISTERED / BINARY_REGISTERED
/ EXECUTION_PROVEN / VISUALLY_PROVEN); only EXECUTION_PROVEN or better may be
used, because the engine accepts an unregistered cvar and silently does
nothing. `engine/pantheon/visual_profile.py` is the one place film words
become engine values. `REVIEW` forces the enemy to Keel, the bright skin and
PANTHEON green, and leaves teammates and self alone -- three separate
mechanisms, proven on pixels at
`docs/visual-record/2026-09-06/green_keel/`.

## Self-test

```
python -m engine.pantheon.doctor          # human-readable
python -m engine.pantheon.doctor --json   # machine-readable
```

PARSER · EXTRACT · ACTION_GRAPH · RETARGET · COMPILE · PARSE_BACK · COMPARE ·
FRAME_TRUTH · INDEX · RECONSTRUCT · GEOGRAPHY · TEMPLATES · TRACE_CACHE ·
RECIPES · VISUAL_PROOF · IDEAS · PROFILES · PLANNER · PROTOCOL ·
CAPABILITIES · VISUAL_PROFILE · OFFSCREEN · RENDER_PERMIT · NO_RENDERER.

24 checks, all green on this machine. The OFFSCREEN check probes the desktop
mechanism with a harmless GUI process; the doctor never launches the game.

## Project default profiles

`defaults.py`. No magic numbers anywhere else; a profile's id is a hash of its
contents, so anything cached against it can tell when it is stale.

| Profile | For | Picture | Enemy |
|---|---|---|---|
| REVIEW_V1 | judging, including on a phone | 1280x720 30 | forced green Keel |
| FPV_FILM_V1 | the delivered first-person image | 1920x1080 60 | as the demo authored |
| CINEMATIC_CLEAN_V1 | free camera, follow, projectile camera | 1920x1080 60 | as authored, no HUD |
| ANALYSIS_V1 | explaining: frozen action, presenters | 1920x1080 60 | forced, for readability |
| PUBLIC_EXPORT_V1 | anything that leaves this machine | 1920x1080 60 | as authored, no name in frame |

## Subsystem maturity

Derived from the registries and the doctor, not from how the work feels.
`python -m engine.pantheon.maturity`.

| Subsystem | Maturity | Gap |
|---|---|---|
| GAME_TRUTH | PRODUCTION_READY | -- |
| PERFORMANCE | PRODUCTION_READY | -- |
| RENDER | PRODUCTION_READY | -- |
| SPATIAL | PARTIAL | 40 maps have too few demos to learn a structure |
| REVIEW | PARTIAL | health, armour, accuracy and round are NOT_DERIVABLE from an index row; the frontend does not consume the contract yet |
| CAMERA | PARTIAL | collision, sight-line and composition are not wired into a planner |
| VISUAL_PROOF | PARTIAL | five capabilities waiting on a person |
| EFFECTS | CONCEPT | no recipe is visually proven through the offscreen backend; none has a choreography builder |
| DIRECTOR | CONCEPT | nothing turns a note into a ChoreographyPlan |
| BLENDER_BRIDGE | CONCEPT | deliberately not built |
| COMFYUI_BRIDGE | BLOCKED | not started; must never decide game truth |
