# The HUD, the wardrobe, and the voice

Three open items closed on 2026-09-08, plus the honest state of the fourth.

---

## 0. Correction, 2026-09-08: I built the HUD on the wrong surface first

The user pointed out that `drawhud` / `drawweapon` exist and that the capability
ingestion should already have covered them. Checked: **the census did ingest
them** -- 383 `cg_draw*` cvars are in `engine_census_11_3.json`, covering 81
elements, 30 of which carry a full control set (`FragMessage` 20 controls,
`Rewards` and `ItemPickups` 16 each; each with X, Y, Scale, Alpha, Color,
Font, Style, Align, Time).

What went wrong is what happened NEXT. Project profiles set 42 of the 383. The
other **341 were ingested and never offered to the film layer**, and I reached
for the shader layer to control the HUD without checking that the engine has a
dedicated switch for every element. That is the same failure this project has
recorded before: the producer was reviewed, the consumer was assumed.

It also explains why the first HUD capture proved nothing. `cg_draw2D` is 1 in
the REVIEW profile but names, FPS, gun, speed and team overlay are already off,
so a shader pack that hides HUD art was operating on a nearly empty surface.

**The corrected architecture, now in `engine/pantheon/hud.py`:**

| Surface | Controls | Cueable? |
|---|---|---|
| **cvars (primary)** | whether an element draws, where, how big, how faded, what colour, how long it dwells | yes -- set per capture |
| shaders (secondary) | what the art itself looks like | as a pack swap |

`hud.elements()` derives all 81 from the RUNTIME census, never from source, so
a name the 11.3 binary did not register cannot leak in. `hud.hide()` and
`hud.restyle()` emit cvar settings, and asking for a knob the runtime lacks
**raises** instead of silently setting a no-op. 24 elements can be moved, 26
can be faded.

Everything below about the shader layer still stands -- it is simply the second
surface, not the first.

---

## 1. The shader layer: what the art can do

Every 2D element Quake draws over the world is a named shader in
`scripts/gfx.shader`: **281 blocks** — 116 screen 2D, 61 item icons, 18
medals, 14 sprites, 14 powerup skins, 2 telemetry. A shader can scroll its
texture, rotate it, pulse its colour, fade its alpha, flip through frames, or
draw nothing. **43 of the shipped blocks already animate themselves.**

### What the project had already proved without noticing

`zzz_zz_moviehud.pk3` contains exactly one file: a copy of the stock
`gfx.shader` with **one block changed**. The `disconnected` shader — the icon
drawing `gfx/2d/net.tga` — is remapped to `$whiteimage` under
`blendfunc GL_ZERO GL_ONE`, which multiplies the frame by zero and draws
nothing. That icon has been absent from every clip we have ever filmed.

So: the override works, the override point is that file, and **the unit of
override is the whole file** — a later pk3 supplying `scripts/gfx.shader`
replaces the earlier one rather than merging with it. `engine/pantheon/hud.py`
therefore always emits a complete file, and `HUD_STOCK` is tested to be
byte-identical to the input so that every diff shows only intent.

### The vocabulary

| Effect | Intent | Timing |
|---|---|---|
| `HUD_STOCK` | the game as it ships — the control leg | CUEABLE |
| `HUD_CLEAN` | no HUD at all: a clean plate for compositing | CUEABLE |
| `HUD_GHOST` | present but half there, world reading through | CUEABLE |
| `HUD_MEDALS_ONLY` | everything hidden but the medals | CUEABLE |
| `HUD_TELEMETRY_OFF` | lagometer and netgraph gone (supersedes the shipped pack, which leaves the lagometer drawing) | CUEABLE |
| `HUD_BREATHE` | the HUD pulses gently | FREE_RUNNING |
| `HUD_FLARE` | every element glows, hot and additive | FREE_RUNNING |
| `HUD_DRIFT` | a slow scan drifts across the art | FREE_RUNNING |
| `HUD_SHIMMER` | the HUD ripples, as powerup skins already do | FREE_RUNNING |

### The limit, stated before any promise

**A Quake shader wave is a function of the engine clock.** `rgbGen wave sin`
pulses from the moment the map loads and cannot be told to peak on a rocket
impact. That is what `FREE_RUNNING` means, and it is why the vocabulary is
split rather than presented as nine equivalent effects.

The cueable axis is not inside one render. It is **between** renders — which
is the next section.

---

## 2. The wardrobe: eleven looks, one ever shipped

`assets.db` holds 5,776 source images from the game and **14,413 renders**
across **20 families**. The pack builder only ever packed `upscale_only`.

**8,637 finished renders of the game's own art have never been in a picture.**

| Family | Renders | Packed before today |
|---|---|---|
| `upscale_only` | 5,776 | yes — the only one |
| `depth_realism`, `photoreal` | 1,000 each | no |
| `pixel_art` | 956 | no |
| `chromatic`, `dreamlike`, `edge_chrome`, `isometric`, `neon`, `painterly`, `zavy_depth` | 800 each | no |
| `tile_d35..d80`, `cel_shade`, `cartoon`, `concept_art`, `ink_etching` | 7–11 each | no — E2E samples, too small to dress a scene |

`engine/pantheon/asset_library.py` publishes every substantial family as an
installable `AssetSet`, so `install("NEON", staging)` and
`capture(asset_set="NEON")` mean something. Ten looks registered:
`DEPTH_REALISM`, `PHOTOREAL`, `PIXEL_ART`, `CHROMATIC`, `DREAMLIKE`,
`EDGE_CHROME`, `ISOMETRIC`, `NEON`, `PAINTERLY`, `ZAVY_DEPTH`.

Measured for `NEON`: **800 of 800** renders override a real pak path under the
same extension, all present on disk, 522 MB. An image that lands at a path the
game never asks for overrides nothing, so `plan()` counts only the ones that
do — and reports `not_in_pak` and `missing_on_disk` separately rather than
folding them into a success number.

The families also turn out to respect the project's own routing rule by
construction: **none of the style families touched shape-critical FX art**, so
no alpha edges on explosions or beams were run through diffusion.

### Why this is not "an HD texture pack"

An HD pack is one look, and everybody has it. A database of eleven looks over
the same 5,776 paths is a **wardrobe**: the same moment can be filmed
repeatedly with the art as the only variable.

---

## 3. The morph: one moment, several takes

`engine/pantheon/morph.py`. Film the same instant of the same demo N times,
changing nothing but which look is installed, and you have N frame-for-frame
alternate universes of one moment. Cut between them on a beat and the world
changes identity on the downbeat.

| Plan | Takes | Join | Shootable today |
|---|---|---|---|
| `WORLD_FLIP` | STOCK → NEON | cut | **yes** |
| `ERA_LADDER` | STOCK → UHD → PAINTERLY → NEON | cut | **yes** |
| `HUD_REVEAL` | clean plate → the game as played | cut | **yes** |
| `MEDAL_ISOLATE` | no HUD → medals alone | cut | **yes** |
| `DREAM_BLEED` | real → dream → real | 400 ms dissolve | no |
| `MATERIAL_MORPH` | stone → chrome | 700 ms morph | no |

### Why two of them are blocked, and it is not laziness

**Two runs of the engine do not start on the same tick.** This project
measured that directly: frames from two captures of the *same* configuration
differed in roughly a quarter of their pixels, and the difference was camera
phase, not content.

A cut survives that — a single frame replaced by a single frame reads as an
edit. **A dissolve does not.** Cross-fading two takes that are a few
milliseconds apart shows the world ghosting against itself.

So `alignment_proven` is `False` everywhere and the test suite enforces that
no blend is ever reported ready while it stays False. The alignment step is
named (`align on a world event both takes contain — the same recorded event
tick, not a wall-clock offset`) rather than assumed.

`MATERIAL_MORPH` is the headline effect and the furthest from proven. The
geometry is identical in both takes by construction, so a flow-based morph has
nothing to track except the art — which is either exactly why it works or
exactly why it does nothing. One test answers it.

---

## 4. Voice: it was never "not started", and now it runs

The earlier status report said voice generation had not begun. **That was
wrong.** `engine/pantheon/voice.py` already carried seven character voice
profiles, a game-voice bank over the shipped VO, whisper word-alignment, and
an ffmpeg treatment chain; `dialogue_mix.py` already placed and mixed lines
from FrameTruth positions. A finished proof video exists.

What was missing was **one function**: `synthesize(text, profile) -> Path`.
The `tts_voice` field named a Kokoro voice in seven profiles and **no code
read it**. Four synthesised wavs existed that nobody could reproduce, because
the recipe lived in a session shell rather than the repository.

### Why it appeared broken

Importing Kokoro **crashes** on this machine — an access violation, not an
exception, so nothing catchable happens and the interpreter dies with exit
139. The fault is `torch.cuda.device_count()`, called at import time by
`thinc/compat.py` (spaCy's backend, reached through misaki's g2p). It is the
same driver that already segfaults this machine's OpenGL on `glColor4f`.

`CUDA_VISIBLE_DEVICES` does **not** avoid it; the enumeration still runs.
Replacing the probe before the import does:

```python
torch.cuda.device_count = lambda: 0
torch.cuda.is_available = lambda: False
from kokoro import KPipeline
```

Speech synthesis needs no GPU at this length. Added:

- `voice.tts_available()` — answers by importing, because the failure mode is
  a crash and a file-presence check would report success.
- `voice.synthesize()` — raw speech, out-of-process in the venv that has
  Kokoro.
- `voice.speak()` — synthesise, then apply the character treatment. **This is
  the function whose absence meant `tts_voice` had no consumer.**

Verified end to end: *"You will not reach the rail in time."* through the
`KEEL` profile (`bm_george`, pitched down and darkened, panned left, at
distance) → 2.97 s of treated audio. Load and synthesis together: ~3.5 s.

Also fixed in passing: `voice.FFMPEG` was a hardcoded `G:\` path. It now
resolves from `store.PROJECT_ROOT`, the same defect class that once made every
review proxy fail on a missing ffmpeg inside a worktree.

### Sound assets — the standing fact is unchanged

There are still **zero HD sound assets**. The UHD packs contain no sound
entries and the only audio in the install is the 1,137 stock entries in
`pak00.pk3`.

But that install is richer than "stock" suggests: ~380 VO files, including
**40 complete instructional sentences** spoken by Crash, the tutorial trainer,
already transcribed with word-level timing. For instructional video that is
more diegetic than anything synthesis can produce, and it is already usable.

---

## 5. Character animation: the wall is real and already named

Authored character motion **works** — `spawn / move_to / look_at / gesture /
fire / kill` compose into a scenario, compile to a playable demo, and have
been filmed. Movement statistics are mined from the real corpus so synthetic
actors do not lerp robotically.

The ceiling is the vocabulary: **7 stances, and exactly one gesture.**
`TORSO_FOLLOWME`, `GETFLAG`, `PATROL`, `AFFIRMATIVE` and `NEGATIVE` exist in
the enum, but `CG_ParseAnimationFile` memcpy's them from `TORSO_GESTURE` when
a model's cfg ends early — the norm for stock models — so **they all render
identically**.

The project already registered the verdict: **`CUSTOM_POINT_GESTURE =
UNSUPPORTED_NATIVE`**. "Raises an arm and indicates that wall" is not in the
MD3 vocabulary, and it is the specific thing that routes to Blender as a
character-performance backend. Blender is registered as four `UNKNOWN`
capabilities and has **no implementation** — deliberately, so that naming it
is not mistaken for having it.

**Do not plan a pointing or indicating presenter against the native path.**

One correction to the funded-track table: **FT-3's `intro_lab` directory does
not exist.** `creative_suite/comfy/assets/` contains only `phase5_png`. FT-3
is a table row and nothing on disk.

---

## What is proven and what is not

**Proven today:** Kokoro synthesis end to end in a character voice. The HUD
inventory and the shader writer (identity is byte-exact). The wardrobe
measured against the pak. `internal_scale` finally has a consumer.

**Not proven, and not claimed:** that any HUD pack changes a frame — that is a
pixel question needing one capture and one human. That any look changes a
frame — same. That a dissolve between two takes holds. That `MASTER_RASTER`
can capture at 5760×3240.

Every builder in this work returns `proven: False` alongside `how_to_prove`,
because the alternative is a system that reports its own intentions as
results.

---

# Addendum, 2026-09-08 evening — what was actually filmed

Four things were attempted against the running engine. Two produced evidence,
one produced a defect, one was refused.

## PROVEN — the wardrobe reaches the picture

`capture(asset_set="NEON")` resolved the look through the library, installed a
388 MB pack built from 800 database renders, and filmed offscreen with **no
visible window and no stolen focus**. Filmed the same moment again as `STOCK`.

Artefacts: `docs/visual-record/2026-09-08/wardrobe/`.

The two frames are unmistakably different art — flat dark brick against
detailed brick, and the NEON capture is **30.5 MB against STOCK's 11.2 MB** for
the same window and codec. The regenerated art is in the picture. That is the
claim that had never been tested, and it holds.

**What is NOT claimed: the size of the difference.** The measured ratios
(x2.14 saturation, x3.56 luminance) are **contaminated**. The two legs do not
cover the same world instants — two engine runs do not start on the same tick,
so a comparison at matched *timestamps* compares different *content*. The exact
trap this repository documents in `morph.py`, walked into while proving
`morph.py`. Averaging 14 frames did not fix it because the clip is short. A
clean magnitude needs frame-locked takes, which is the same unproven alignment
step the blend plans are waiting on.

## DEFECT FOUND, DIAGNOSED AND FIXED — captures were being killed mid-write

Both legs asked for 2,500 ms and produced **44 frames, 0.73 s**, with
`ok=False`. A probe across four window lengths found the shape:

| asked | expected @60 | delivered | wall time | predicted budget |
|---|---|---|---|---|
| 1,000 ms | 60 | **0** | 121.5 s | 208 s (finished early, wrote nothing) |
| 2,500 ms | 150 | 42 | 223.4 s | **223 s** |
| 5,000 ms | 300 | 74 | 248.7 s | **248 s** |
| 10,000 ms | 600 | 84 | 298.1 s | **298 s** |

The wall times match the computed timeouts to within a second. **The clips
were not short because the engine stopped; they were short because we killed
it.**

### The root cause is the NVIDIA blocker, one layer down

The console says it plainly:

    GL_VENDOR:   Mesa
    GL_RENDERER: softpipe
    GL_VERSION:  3.3 (Compatibility Profile) Mesa 24.3.3

Every offscreen capture runs on a **CPU rasteriser**. That is deliberate and
documented — the NVIDIA driver kills wolfcam during `R_Init` on this machine,
the same blocker recorded for PANTHEON's own renderer, so Mesa is staged beside
`wolfcamql.exe` and only this process is affected.

What nobody had connected is the cost. Softpipe writes about **half a frame per
second** at 1920×1080, i.e. ~120 wall-seconds per second of 60 fps footage.
`CAPTURE_SLOWDOWN = 10` was calibrated against hardware GL. Every capture was
therefore terminated at its own deadline part-way through — and a terminated
engine never releases its cursor clip, which is why `ok` was False as well:
`pointer_left_confined` and the short clip are the same event.

### What was fixed

- `SOFTWARE_CAPTURE_SLOWDOWN = 150` (measured ~120, plus margin), selected by
  `software_gl()`. A 2.5 s window now budgets 573 s instead of 223 s.
- Both capture paths now **count the frames they wrote** and report
  `truncated`, `frames_expected`, `frames_written`. A truncated capture is a
  well-formed AVI whose header claims 60 fps — nothing about the file
  announces that it holds a quarter of the action, which is exactly why every
  clip filmed before today was short and nothing said so.
- `ok` is False when the file is short, in both paths.

### The retest: better, and still not right

Same 2.5 s window, corrected budget:

| | before | after |
|---|---|---|
| frames written | 42 / 150 | **77 / 150** |
| wall time | 223.4 s (killed at 223 s budget) | 303.4 s (finished on its own, 573 s budget) |

So the timeout was real and fixing it nearly doubled the delivered footage —
but **the clip is still half length**, and this time the engine was not killed:
it reached `quit` by itself. 77 frames over 2,500 ms is ~30.8 fps, against the
60 the master cfg asks for. Something is halving the capture rate, and that is
a separate defect still open.

### A latent bug the retest exposed

The retest came back `truncated: true, ok: true`. `ok` was never actually
computed: `**run.as_dict()` was spread LAST in the return dict and carries its
own process-level `"ok"`, so it silently overwrote the verdict built from
windows, quiet and truncation. **That was true before this change too** — a
capture that opened a visible window would still have reported the engine's
exit status as `ok`. The spread now goes first and the process result is kept
as `engine_ok`.

**This affected every review proxy and every A/B leg ever filmed offscreen.**
The real fix remains hardware GL, which is the NVIDIA blocker and is not
addressed here.

## INCONCLUSIVE — the HUD shader proof could not discriminate

`HUD_STOCK` against `HUD_CLEAN`, art fixed. The measured difference ran the
wrong way (clean showed *more* ink) for two reasons, both mine:

1. The REVIEW profile already turns off names, FPS, gun, speed and team
   overlay, so there was almost no HUD art left for a shader pack to hide.
2. The bottom-band measure caught the floor, not just the HUD, so it measured
   scene brightness across two different camera phases.

The mechanism is not disproven; the test was incapable of answering. With the
cvar surface now exposed (§0) the right test is `cg_drawRewards 0` against
`cg_drawRewards 1`, which changes exactly one element and nothing else.

## THE REMAINING HALF — the engine writes 30 fps when asked for 60

77 frames over 2,500 ms is **32.5 ms per written frame**. 60 fps is 16.67 ms;
30 fps is 33.3 ms. The capture is writing at almost exactly half the rate the
configuration asks for.

Ruled out by measurement, not by argument:

- `cl_aviFrameRate` is **60**, registered, in the runtime census.
- `cl_aviFrameRateDivider` is 1 — and unregistered, so it is a silent no-op
  anyway.
- `mme_blurFrames` is **0**, so there is no accumulation halving the output.
- The REVIEW visual profile sets no capture-rate cvar at all.
- The written cfg execs `wolfcam_tr4sh_master_capture.cfg`, which sets 60.

So every knob that could explain it says 60, and the file says 30. This is a
separate defect from the timeout, it is still open, and it is the reason a
clip is half length rather than full even when the engine is allowed to finish.

## NOT ANSWERABLE TODAY — the supersampling canary

Blocked first by another session holding the capture lock. But there is a
better reason not to run it now: **while capture is on softpipe, the canary
would measure what Mesa allows, not what the hardware allows.** A software
rasteriser will happily allocate a 5760×3240 framebuffer. The question worth
answering is whether the NVIDIA path grants one, and that path currently
crashes wolfcam during `R_Init`.

The canary is therefore blocked on the same NVIDIA blocker as everything else
in this section, and running it under softpipe would produce a reassuring
number that means nothing.

`MASTER_RASTER` at 5760×3240 was blocked: another session held
`output/demo_v2/_capture.lock` for a legitimate clip regeneration run. The lock
behaved exactly as designed — it deferred rather than clobbering, which is the
failure it was written for after two renderers once overwrote each other's
`capture.cfg`. **The canary remains unrun and 5760×3240 remains unproven.**

## PROVEN — voice reaches the fragmovie mux

`mux_music(..., voice=stem)` adds a third summed leg before the loudness and
true-peak stage. Measured on a real encode: **−1.8 dBTP with voice and −1.8
dBTP without**, integrated loudness −14.2 LUFS in both. The safety gate that
once let a mix reach +1.94 dBFS still bounds the sum with three legs.

No ducking: P1-G v6 forbids level-following, so the voice sits above a music
bed that never moves. `VOICE_VOLUME = 2.60` (about +6.4 dB over music) is a
**starting point for a listening pass**, not a measured optimum — nobody has
judged a narrated episode by ear.
