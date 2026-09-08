# The HUD, the wardrobe, and the voice

Three open items closed on 2026-09-08, plus the honest state of the fourth.

---

## 1. The HUD is an animation system, and it always was

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
