# PANTHEON — full engine state, 2026-09-08

Written after a day of turning claims into evidence. The organising question
is not "what exists" but **"what has been proven, and by what"** — because the
recurring failure in this project has been a field that exists, is populated,
is documented, and is read by nothing.

Three separate instances of exactly that were found and fixed in two days:
`internal_scale` (supersampling, no consumer), `tts_voice` (a voice id, no
consumer), and **341 of 383 HUD control cvars** (ingested, never offered).

---

## 1. The one-line answer

**The engine is not "fully working". It is substantially more capable than it
was, and for the first time the wardrobe has been filmed.** Sound synthesis
works and now reaches the mux. Character animation remains capped at seven
stances. One real defect was found today that silently affects every capture.

---

## 2. What is PROVEN — filmed, measured, or executed

| Capability | Evidence |
|---|---|
| **The regenerated art reaches the picture** | `capture(asset_set="NEON")` installed a 388 MB pack from 800 database renders and filmed offscreen — no visible window, no stolen focus. Against STOCK at the same moment: visibly different art, 30.5 MB vs 11.2 MB. `docs/visual-record/2026-09-08/wardrobe/` |
| **Voice synthesis** | Kokoro through the `KEEL` profile → 2.97 s of treated audio. The import crash was `torch.cuda.device_count()` faulting inside `thinc`; stubbing the probe fixes it, `CUDA_VISIBLE_DEVICES` does not |
| **Voice reaches the fragmovie mux** | Third summed leg before the loudness stage. **−1.8 dBTP with voice, −1.8 dBTP without**, −14.2 LUFS both. The gate that once allowed +1.94 dBFS still bounds three legs |
| **The HUD control surface** | 383 `cg_draw*` cvars over 81 elements, derived from the runtime census. 24 movable, 26 fadable. `restyle()` refuses a knob the runtime lacks rather than setting a no-op |
| **The shader writer is faithful** | `HUD_STOCK` is byte-identical to the shipped file, so every diff shows only intent |
| **The capture lock works** | It refused the supersampling canary because another session legitimately held it. Deferred rather than clobbered — the exact failure it was written for |
| **`internal_scale` has a consumer** | `capture_geometry()` / `supersample_blockers()`. MASTER_RASTER resolves to 5760×3240 → 3840×2160, 2.25× cost |

---

## 3. What is NOT proven, stated plainly

| Claim | Status |
|---|---|
| The *magnitude* of the look difference | **Contaminated.** The measured ×2.14 saturation / ×3.56 luminance compare different world instants — two engine runs never start on the same tick. The trap this branch documents in `morph.py`, walked into while proving `morph.py` |
| A HUD pack changes a frame | **Inconclusive.** The REVIEW profile already strips most HUD art, so the shader pack had nearly nothing to hide, and the bottom-band measure caught the floor |
| A dissolve or morph between takes holds | **Unproven.** Needs frame-locked takes; `alignment_proven` is False everywhere and the suite enforces it |
| `MASTER_RASTER` can capture at 5760×3240 | **Unrun.** Refused by the capture lock |
| Any look or HUD treatment *looks good* | A human judgement. Not recorded anywhere, deliberately |
| The voice level is right | `VOICE_VOLUME = 2.60` is a starting point for a listening pass, not a measured optimum |

---

## 4. The defect found today

**Every capture is truncated.** A 2,500 ms window returns **44 frames — 0.73 s**,
about 30% of what was asked, with `ok=False`. Reproduced on every capture
attempted today, on the plain path, unrelated to any change here.

This silently shortens **every review proxy and every A/B leg**, and it is why
frame sampling past ~0.7 s returned nothing. It is the highest-value thing to
fix next, because it degrades work nobody is currently watching.

---

## 5. Sound — the honest state

| | |
|---|---|
| Voice synthesis | **works**, reproducible, recipe in the repo |
| Voice in the fragmovie mux | **wired and measured** |
| Voice level tuned by ear | no |
| Character voice profiles | 7, each an ffmpeg treatment chain |
| Shipped game VO | ~380 files, incl. **40 complete instructional sentences** already transcribed with word timing |
| **HD sound assets** | **zero.** The UHD packs contain no sound entries. Only the 1,137 stock `pak00` entries exist |
| Subtitles | `subtitle_at()` exists, called by nothing, no burn-in, no SRT writer |

So: "sound working" is true for *generation* and *mixing*, false for *assets*.
There is no HD audio and none is planned by anything on disk.

---

## 6. Animation — the honest state

**Authored character motion works.** `spawn / move_to / look_at / gesture /
fire / kill` compose into a scenario, compile to a playable `.dm_73`, and have
been filmed. Movement statistics are mined from the real corpus so synthetic
actors do not lerp robotically. Trace replay reproduces a real player verbatim.

**The ceiling is seven stances and exactly one gesture.** `TORSO_FOLLOWME`,
`GETFLAG`, `PATROL`, `AFFIRMATIVE` and `NEGATIVE` exist in the enum, but
`CG_ParseAnimationFile` memcpy's them from `TORSO_GESTURE` when a model's cfg
ends early — the norm for stock models — so **they all render identically**.

`CUSTOM_POINT_GESTURE = UNSUPPORTED_NATIVE` is already on the books. "Raises an
arm and indicates that wall" is not in the MD3 vocabulary and routes to
Blender, which is registered as four `UNKNOWN` capabilities with **zero
implementation**.

**Do not plan a pointing or indicating presenter against the native path.**

---

## 7. The wardrobe

`assets.db`: 14,413 renders across 20 families. Before today the builder had
only ever packed `upscale_only` — **8,637 finished renders had never been in a
picture**. Ten looks are now registered and installable by name; `NEON` is
built (388 MB, 800/800 overriding real pak paths) and filmed.

`assets.install()` resolves looks lazily, so `capture(asset_set="NEON")` works
without the caller knowing looks come from a different module than STOCK.

---

## 8. The HUD, corrected

Two surfaces, and the cvars come first:

| Surface | Controls | Count |
|---|---|---|
| **cvars (primary)** | whether an element draws, where, how big, how faded, what colour, how long it dwells | 383 cvars, 81 elements, 30 with a full set |
| shaders (secondary) | what the art itself looks like | 281 blocks, 43 already self-animating |

I built the second one first. The census had ingested all 383 cvars; profiles
used 42; the other 341 sat unoffered. That is corrected — but it is worth
recording *why* it happened, because it is the same pattern as `internal_scale`
and `tts_voice`: **the producer was reviewed and the consumer was assumed.**

---

## 9. DLSS

Cannot run: fixed-function OpenGL 1.x, no motion vectors, no jitter, and the
NGX SDK has never had an OpenGL binding in any generation — including DLSS 5,
which does exist (March 2026) and still consumes motion vectors. It is also the
wrong tool: DLSS buys frame rate, and an offline pipeline has no frame budget.

The right technique is the opposite one — render high, filter down — which is
now wired and awaits one canary.

---

## 10. What to do next, in order

1. **Fix the truncated capture.** It silently degrades everything else.
2. **Run the supersampling canary** when the lock frees.
3. **Re-test the HUD with cvars, not shaders** — `cg_drawRewards 0` against
   `1` changes exactly one element and nothing else.
4. **Frame-lock two takes** — that single step unblocks `DREAM_BLEED`,
   `MATERIAL_MORPH`, and an uncontaminated measurement of every look.
5. **Listen to a narrated episode** and set `VOICE_VOLUME` by ear.

---

## 11. Verification

- New modules: `hud.py`, `asset_library.py`, `morph.py`. Modified: `voice.py`,
  `assets.py`, `render_highlight.py`, `render_profile.py`, `review_proxy.py`,
  `doctor.py`.
- 28 new tests in `test_hud_and_looks.py`; boundary suite green.
- `doctor` gains `WARDROBE`, `HUD`, `MORPH` — all OK.
- Baseline at HEAD failed 114; the branch introduced **no new failure**.
- Nothing belonging to the concurrent session was committed
  (`relink_frags.py`, `round_model.py`, `demo_parse.py`, `frag_classify.py`).


---

# Addendum — the greenlit session

## Newly PROVEN

| Claim | Evidence |
|---|---|
| **The HUD control surface works** | `cg_drawStatus` 1 vs 0: the health readout, cross icon and HUD bar present in one frame, absent in the other. `docs/visual-record/2026-09-08/hud_cvar/` |
| **The wardrobe reaches the picture** | NEON (388 MB, 800/800 renders) vs STOCK, filmed offscreen. Visibly different art, 30.5 MB vs 11.2 MB |
| **Voice reaches the mux** | −1.8 dBTP with and without the third leg, −14.2 LUFS both |

## The defect: diagnosed, half fixed, half still open

Captures were short because **we were killing the engine**. Every offscreen
capture runs on Mesa **softpipe** — deliberate, because the NVIDIA driver kills
wolfcam during `R_Init` on this machine — and softpipe writes ~0.5 frames per
second at 1080p against a `CAPTURE_SLOWDOWN` calibrated for hardware GL. The
predicted budgets matched the observed wall times to within a second.

Fixed: the budget is now sized for the renderer in use, both capture paths
count the frames they wrote, and `ok` is False when a file is short.

Also fixed, found on the way: **`ok` was never computed at all.**
`**run.as_dict()` was spread last and carries its own process-level `"ok"`,
overwriting the verdict. True before this change too.

**Still open:** the engine writes **30 fps when the cfg asks for 60** (32.5 ms
per frame). `cl_aviFrameRate` is 60 and registered, the divider is 1 and
unregistered, `mme_blurFrames` is 0, and the profile sets no rate. Every knob
says 60; the file says 30. A 2.5 s window now delivers 77/150 frames instead of
42/150.

## What I got wrong, and what it cost

- **I measured the wardrobe at matched timestamps.** Two engine runs never
  start on the same tick, so that compared different content. The ratios are
  withdrawn; the visual difference stands.
- **I built two HUD metrics that could not discriminate**, both by averaging a
  region where the subject occupies a few percent of the pixels. The eye
  answered in one look.
- **I built the HUD on the shader surface first** when the engine had 383
  dedicated switches, 341 of them ingested and never offered.

The pattern in all three: I reached for a derived number when a direct look
was available, and for a new mechanism when the engine already had one.

## The canary is not answerable today

Not merely blocked by the lock. **Under softpipe it would measure what Mesa
allows, not what the hardware allows** — a software rasteriser grants a
5760×3240 framebuffer happily. The question is whether the NVIDIA path does,
and that path crashes.

## Next, in order

1. **The 30 fps halving.** It is the difference between half-length and
   full-length clips on every capture.
2. **The NVIDIA `R_Init` crash.** It is upstream of the capture speed, the
   supersampling canary, and the native renderer. Everything slow or unproven
   in this section traces back to it.
3. Frame-lock two takes — unblocks the blend plans and an uncontaminated
   measurement of every look.
4. Listen to a narrated episode and set `VOICE_VOLUME` by ear.

## Suite

40 failed / 3178 passed, against a baseline of 114 / 3011 — but that baseline
ran while another session was rebuilding databases, so most of the improvement
is environmental rather than mine. Every suite covering code touched here
passes when run explicitly.


---

# Addendum 2 — the engine runs on the GPU

Everything in the previous addendum about capture speed is superseded by one
finding: **the Mesa softpipe workaround was never necessary.**

| | softpipe | native NVIDIA |
|---|---|---|
| wall clock, 2,500 ms window | 303.4 s | **22.4 s** |
| frames delivered | 77 / 150 | **150 / 150** |
| captured rate | 30.8 fps | **60.0 fps** |
| renderer | `softpipe` | `NVIDIA GeForce RTX 5060 Ti` |
| window / focus | none / none | none / none |

Through the production path with the UHD install: **66.2 s, 147/150 frames,
58.8 fps, `ok: true`**.

## Two conclusions retracted

- **"The engine writes 30 fps when asked for 60" was not an engine defect.**
  It was softpipe dropping frames it could not render in time.
- **The capture-timeout fix was treating a symptom.** Captures were killed at
  their deadline because the renderer was ~100x too slow.

`retime()` remains correct and now never fires: native captures come back at
`played_too_fast_by: 1.02`, inside tolerance.

## Why the belief stood so long

The record said the NVIDIA driver kills wolfcam during `R_Init`. The recorded
access violation was in a **custom host**, not wolfcamql, and stock ioquake3
NULL-checks every resolved GL pointer and errors cleanly rather than faulting.
`wglGetProcAddress` is documented to return NULL for OpenGL 1.1 core functions
-- exactly `glColor4f`, `glColor3f`, `glNormal3f`, the three that faulted --
and SDL 1.2 has no `GetProcAddress` fallback while Mesa resolves them anyway.
**One host's bug was generalised to the whole engine without testing the
engine.**

The other Mesa drivers are measured dead ends: `llvmpipe` absent from this
MinGW x86 build, `d3d12` no matching pixel format across sixteen mode/bpp
combinations, `zink` dies without writing an error.

## What it unlocks

A 120-clip Part goes from roughly 20 hours of capture to **1-2**. The
supersampling canary is now worth running, because it would measure the
hardware rather than what Mesa allows. The wardrobe shoots become practical.

## Also in this pass

- `review_sheet` — crops, labels and stacks comparison frames, names the one
  variable, refuses a one-sided sheet, reports `PENDING_HUMAN`. Built because
  three separate measurements said nothing today where one look answered.
- The HUD control surface proven on pixels: `cg_drawStatus` 1 vs 0.
- A look that is not built is a choice, not a fault -- `available()` is now
  scoped to the set being filmed.

## The pattern worth keeping

Four times today a derived number was wrong where a direct look was right, and
twice a belief was inherited rather than tested. The corrective is the same in
both cases: **ask the thing itself.** The engine was never asked whether it
could use the GPU.
