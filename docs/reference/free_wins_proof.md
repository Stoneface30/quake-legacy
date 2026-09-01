# Free Wins — Proof Log

Empirical verification that a set of "zero / low engine work" cinematic
capabilities are already present in the **shipped, unmodified** WolfcamQL
11.3 capture binary (`engine/engines/ghidra/binaries/wolfcamql-11.3.exe`,
staged to `output/demo_v2/_wolfcam_staging/`).

**Methodology** (per proof): write a custom `capture.cfg` via
`creative_suite/engine/wolfcam_capture.py` (`stage_demo` / `wolfcam_cmd` /
`SEEK_SETTLE_MS`), launch wolfcam once as a subprocess with a timeout, wait
for a clean exit, then pull frames with
`creative_suite/tools/ffmpeg/ffmpeg.exe` and **look at them**. A clean
process exit is not proof — every claim below is backed by an inspected
frame and, where a before/after comparison exists, a numeric per-pixel diff
against a baseline captured at the identical seek point.

Harness: `scratchpad/proof_harness.py` (uncommitted).
Frames: scratchpad `frames/` (uncommitted — QL burns opponent nicknames into
the HUD, so these are **not** promoted to `docs/visual-record/`).
Staging discipline: one wolfcam at a time; every test AVI deleted after
frames are pulled; `cgamepostinit.cfg` reset to `// idle` at the end.

---

## Proof 1 — `runfxat` / `runfx` (native FX DSL) — **PASS**

### What the source says

| Fact | Location |
|---|---|
| `runfx`, `runfxat`, `runfxall`, `listfxscripts`, `fxload` are registered console commands | `cg_consolecmds.c:8578-8581`, `:8534-8535` |
| `CG_RunFx` looks the name up in `EffectScripts.names[]`, prints `couldn't find fx '<name>'` on miss | `cg_consolecmds.c:7633-7660` |
| **Every** parsed script name lands in `EffectScripts.names[]` — hardcoded (`weapon/rocket/impact`) and generic alike | `cg_fx_scripts.c:6786-6789` |
| Scripts load from `cg_fxfile` (default `""` — nothing loaded) at cgame init | `cg_main.c:2391`, `cg_main.c:8447` |
| `fxload <file>` reloads at runtime | `cg_consolecmds.c:6135-6142` |

**`pak00.pk3` ships zero `.fx` files.** The FX DSL scripts are a WolfcamQL
gamedir asset: `engine/engines/_canonical/package-files/wolfcam-ql/scripts/`
ships `q3mme.fx` (61 effects), `dirtest.fx` (11 impact effects),
`alltest.fx`, `flesh.fx`, `q2railcore.fx`, `cpmaRlSmoke.fx`.

### What was run

Demo `CA-Gr0str4sh-overkill-2013_01_08-21_42_32.dm_73`, window
`381575 → 383575` (raw serverTime), fx fired at `382225` (t = 0.65 s into
the clip). Shipped effect used: **`weapon/rocket/impact` from
`scripts/dirtest.fx`** — no authored content.

Baseline `capture.cfg`:

```
exec wolfcam_tr4sh_master_capture.cfg
seekservertime 380975
at 381575 video avi name p1_base
at 383575 stopvideo
at 383875 quit
```

FX `capture.cfg` (launched additionally with `+set cg_fxfile scripts/dirtest.fx`):

```
exec wolfcam_tr4sh_master_capture.cfg
fxload scripts/dirtest.fx
listfxscripts
seekservertime 380975
at 381575 video avi name p1_fx
at 382225 runfx weapon/rocket/impact
at 383575 stopvideo
at 383875 quit
```

`listfxscripts` logged `0: weapon/rocket/impact`; no `couldn't find fx` line.

### Result — PASS

Per-pixel diff, identical timestamps, baseline vs fx run:

| t (s) | base mean | fx mean | Δmean | % px changed >16 |
|---|---|---|---|---|
| 0.50 | 28.10 | 28.04 | −0.06 | 5.7 % |
| 0.63 | 25.92 | 25.97 | +0.04 | 5.8 % |
| 0.66 | 25.57 | 26.09 | +0.52 | 7.8 % |
| **0.70** | 26.64 | **38.46** | **+11.82** | **16.8 %** |
| 0.80 | 33.51 | 34.52 | +1.01 | 8.9 % |
| 1.00 | 41.58 | 53.96 | +12.38 | 26.0 % |
| 1.40 | 31.32 | 54.52 | +23.20 | 44.7 % |

Frames before the fire time are identical within the ~±0.5 MJPEG/dither
noise floor; frames after diverge hard. The `t=0.70` frame
(`cmpF_t0.7.png`) shows a large blue-white `flareShader` particle burst
filling a corridor that is empty and dark in `cmpB_t0.7.png`.

**Attribution caveat, stated honestly:** this canary window contains a
*natural* rocket kill at ≈ t = 1.35 s — `cmpB_t1.4.png` (baseline) already
has an explosion. The `t=1.4` row above is therefore contaminated and is
**not** the evidence. The clean evidence is **t = 0.70**, 0.65 s before any
natural impact, where the baseline is dark and the fx run is not.

### Finding — `runfxat` resolves origin at ISSUE time, not at target time

`CG_RunFxAt_f` (`cg_consolecmds.c:7746-7817`) snapshots the current view
origin **when the command is parsed**, then bakes those literal floats into
a deferred string:

```c
trap_SendConsoleCommand(va("at %s runfx %s %f %f %f %f %f %f %f %f %f\n",
                           timeString, script, origin[0], ...));
```

Issued from `cgamepostinit.cfg` — before the demo has been seeked — the
snapshot is the map origin. Verified empirically:

```
runfxat 382225 weapon/rocket/impact      # issued at postinit
```

| t (s) | base mean | runfxat mean | Δmean |
|---|---|---|---|
| 0.63 | 25.92 | 25.97 | +0.04 |
| 0.70 | 26.64 | 27.17 | +0.53 |
| 0.80 | 33.51 | 33.63 | +0.12 |

All within the noise floor — the effect fired, at `(0,0,0)`, off camera.

**Authoring rule for this pipeline:** use **`at <t> runfx <name>`** (origin
resolved live at fire time, which is what produced the PASS above), or
`runfxat <t> <name> <x> <y> <z>` with explicit world coordinates. Do not use
bare `runfxat <t> <name>` from an init-time cfg.

### Frames
`cmpB_t{0.5,0.63,0.66,0.7,0.8,1.0,1.4}.png` (baseline),
`cmpF_t*.png` (runfx), `cmpA_t*.png` (runfxat), `p1_base_*`, `p1_fx_*`.
All test AVIs deleted.

---

## Proof 2 — Ghost trail (player trail FX hook) — **PASS**

### What the source says

The WolfcamQL-specific player trail hook is **not gated by a cvar**. It is:

```c
if (*EffectScripts.playerTorsoTrail) {
    CG_ResetScriptVars();
    CG_CopyPlayerDataToScriptData(cent);
    ScriptVars.animFrame = torso.frame;
    VectorCopy(torso.axis[0], ScriptVars.axis[0]);   // + axis[1], axis[2]
    VectorCopy(torso.origin,  ScriptVars.origin);
    trap_R_GetModelName(torso.hModel, ScriptVars.model, sizeof(ScriptVars.model));
    VectorCopy(cent->lastTorsoIntervalPosition, ScriptVars.lastIntervalPosition);
    ScriptVars.lastIntervalTime = cent->lastTorsoIntervalTime;
    ...
    CG_RunQ3mmeScript(EffectScripts.playerTorsoTrail, NULL);
    ... // interval/distance state written back to the centity
}
```

`cg_players.c` torso block (~:7134-7166); matching head and legs blocks
exist. Script names bind at `cg_fx_scripts.c:6961-6969`
(`player/head/trail`, `player/torso/trail`, `player/legs/trail`).

**Enabling it = defining the script.** No cvar, no engine change. The
shipped `scripts/q3mme.fx` even carries ready-made examples, **commented
out**, at `q3mme.fx:163-180` — with a comment block documenting the extra
inputs wolfcam feeds these scripts (`origin, angles, velocity, dir, axis,
animFrame, model, team, clientnum, enemy, teammate, ineyes, pw*`).

### What was run

DB-sourced moment (`creative_suite/database/frag_recognition.db`,
`recognized_frags`): `CA-pTnTr4sH-trinity-2012_01_28-14_26_22.dm_73`
@ `server_time_ms = 954950` — `EXTREME_SPEED p99.5`, `DODGE_STRAFE p99.5`,
`AIR_ROCKET_GEO (victim vz 755)`, `highlight_score 66.66`. Window
`954700 → 956700`; the airborne, dodging victim is in frame from t ≈ 0.1 s.

Effect file written to
`output/demo_v2/_wolfcam_staging/wolfcam-ql/scripts/pantheon_trail_proof.fx`
(copy kept in scratchpad; **uncommitted**), loaded with
`+set cg_fxfile scripts/pantheon_trail_proof.fx` plus an explicit
`fxload scripts/pantheon_trail_proof.fx`.

```
exec wolfcam_tr4sh_master_capture.cfg
fxload scripts/pantheon_trail_proof.fx
seekservertime 954100
at 954700 video avi name p2_trail2
at 956700 stopvideo
at 957000 quit
```

Final effect (v2):

```
player/torso/trail {
	interval 0.04 {
		shader	hasteSmokePuff
		color	0.25 0.7 1.0
		emitter 0.55 {
			size		14 + 30 * lerp
			alphaFade	0
			sprite		cullNear
		}
	}
}
```

`listfxscripts` logged the trail scripts as loaded effects.

### Result — PASS

| t (s) | base mean | trail mean | Δmean | % px changed >16 |
|---|---|---|---|---|
| 0.15 | 94.76 | 113.40 | +18.64 | 61.1 % |
| 0.30 | 111.25 | 121.16 | +9.91 | 40.2 % |
| 0.45 | 89.59 | 93.25 | +3.66 | 21.4 % |

`p2_trail2_t0.3.png` shows a coherent blue plume streaming behind the
airborne player and tracing his dodge arc. `p2_baseC_t0.3.png` (same
timestamp, same seek) has none.

### Findings worth carrying forward

1. **The trail draws on rendered PLAYER MODELS, so in a first-person master
   capture it appears on OTHER players, not the recorder.** The recorder's
   own model is not drawn in FP (`cg_drawGun` shows the weapon only). To get
   a ghost trail on the recorder, the shot must be third-person / chase /
   freecam. This is a real constraint on how the effect can be used.
2. **v1 failed usefully.** v1 used the shipped commented-out example
   verbatim (`shader sprites/balloon3`) plus an `axismodel` model-copy
   ghost. The hook fired — stamps appeared behind the moving player, absent
   in baseline — but rendered degenerately (blue placeholder quads + RGB
   axis lines). Two causes: `sprites/balloon3` is a Quake3 asset **absent
   from QL `pak00.pk3`**, and the `axismodel` path
   (`re->hModel = trap_R_RegisterModel(ScriptVars.model)`,
   `cg_fx_scripts.c:3655`) did not resolve the QL player model name returned
   by `trap_R_GetModelName` into a usable handle.
   **The true model-copy ghost (`axismodel`) is therefore NOT yet proven —
   only the sprite-emitter trail is.** Anyone picking this up should verify
   the `GetModelName → RegisterModel` round-trip for QL player models first.
3. Shipped fx scripts assume Quake3 asset names. Any authored fx must be
   checked against QL `pak00.pk3`, not against the q3mme originals.

### Frames
`p2_base_t{0.3,0.9,1.4,1.8}.png`, `p2_baseC_t{0.15,0.3,0.45}.png`,
`p2_trail_t*.png` (v1, degenerate), `p2_trail2_t*.png` (v2, PASS).
All test AVIs deleted.

---

## Proof 3 — Color-grade override via pk3 — **PASS**

### What the source says

`scripts/colorcorrect.fs` ships inside `pak00.pk3` (926 bytes, verified by
listing the archive) and is compiled **from the game VFS at renderer init**:

```c
R_InitFragmentShader("scripts/colorcorrect.fs", &tr.colorCorrectFs,
                     &tr.colorCorrectSp, tr.mainVs);   // tr_init.c:610
```

`RB_ColorCorrect` (`renderergl1/tr_backend.c:1092`, called at `:2046`) is
gated on `r_enablePostProcess` (default `1`), `r_enableColorCorrect`
(default `1`) and `glConfig.qlGlsl` — all satisfied by the frozen master
profile. It then resolves **four** uniforms and calls
`ri.Error(ERR_FATAL, ...)` if any of them fails:
`p_gammaRecip`, `p_overbright`, `p_contrast`, `backBufferTex`.

**Consequence for authoring:** a replacement shader must genuinely *consume*
all four. GLSL compilers strip unused uniforms, and a stripped uniform is a
hard engine abort, not a silent no-op.

Search-path check: only `pak00.pk3` provides the file. `wc-glsl.pk3` in the
gamedir carries `glsl/cameraline.fs` only. A gamedir pk3 therefore wins
outright.

### What was run

`zzz_zz_pantheon_grade.pk3` written into the wolfcam **gamedir** containing
exactly one file, `scripts/colorcorrect.fs` — the same override mechanism
`creative_suite/engine/pantheon_ads.py` uses for ad boards (gamedir beats
baseq3; `zzz_zz_` sorts after the `zzz_uhd_*` packs). Builder:
`scratchpad/build_grade_pk3.py` (uncommitted).

Demo `CA-Gr0str4sh-overkill-2013_01_08-21_42_32.dm_73`, window
`381575 → 382775`, identical cfg for all three runs; the only variable is
whether the pk3 is present and which variant it holds.

```
exec wolfcam_tr4sh_master_capture.cfg
seekservertime 380975
at 381575 video avi name p3_<variant>
at 382775 stopvideo
at 383075 quit
```

Both variants keep the stock preamble (all four uniforms consumed) and only
change the final colour math.

### Result — PASS

**Grade A — deliberately unmistakable** (oversaturate ×1.6, hard magenta
cast `vec3(1.55, 0.55, 1.70)`):

| t (s) | base mean RGB | grade A mean RGB | % px changed >8 |
|---|---|---|---|
| 0.30 | 30.48 / 26.52 / 22.19 | **49.00 / 13.96 / 29.61** | 81.6 % |
| 0.60 | 32.48 / 28.36 / 23.84 | **51.46 / 15.11 / 30.66** | 81.8 % |

Green is more than halved while red rises ~60 % — the whole scene turns
magenta/violet in `p3_gradeA_t0.6.png`. No `ERR_FATAL`, clean exit.

**Grade B — `PANTHEON_GRADE_TEST`, restrained. This is a TEST, not a final
grade** (slight desaturate 0.92, cool shadows, warm highlights, ×1.06
contrast):

| t (s) | base mean RGB | grade B mean RGB | % px changed >8 |
|---|---|---|---|
| 0.30 | 30.28 / 25.68 / 21.03 | 23.54 / 20.10 / 16.71 | 44.4 % |
| 0.60 | 31.64 / 25.81 / 20.40 | 24.96 / 20.39 / 16.22 | 48.4 % |

Visibly deeper and cooler, still reads as Quake. Colour ratios move
consistently rather than being crushed. Confirms the hook is usable for a
real look, not just a stunt.

### Finding — `cg_fxfile` is `CVAR_ARCHIVE` and leaks between runs

The first Proof-3 baseline came back **with the Proof-2 ghost trail still
on**. Cause: `cg_fxfile` is declared `CVAR_ARCHIVE` (`cg_main.c:2391`), so
the Proof-2 value was written into `q3config.cfg` on quit and inherited by
the next launch.

This did **not** invalidate Grade A — baseline and Grade A both carried the
trail, so the only difference between them was the grade — and the Grade A
frame doubles as an independent re-confirmation of Proof 2 on a *second*
demo. But it is a real trap: **any capture harness must explicitly reset
archived cvars it set in a previous run.** The harness now always passes
`+set cg_fxfile ""` unless a caller overrides it; the Grade B run used a
fresh, trail-free baseline captured under that fix.

### Frames
`p3_base_t{0.3,0.6}.png` (trail-contaminated baseline, matched to Grade A),
`p3_gradeA_t{0.3,0.6}.png`, `p3_base2_t{0.3,0.6}.png` (clean baseline),
`p3_gradeB_t{0.3,0.6}.png`.
Grade pk3 removed from the gamedir; all test AVIs deleted.

---

## Proof 4 — Live shader replacement (`remapshader`) — **PASS (true hot-swap, no restart)**

### The console-reachable path

Two mechanisms exist; only one is reachable from the console.

| Mechanism | Reachable? | Where |
|---|---|---|
| `R_RemapShader` / `RE_RemapShader` (`renderer/tr_shader.c:54`) | **YES** — `remapshader` + `clearremappedshader` console commands | `cg_consolecmds.c:7437` / `:7464`, registered at `:8571-8572` |
| `RE_ReplaceShaderImage` (raw pixel upload, `trap_ReplaceShaderImage`) | **NO** | `CG_TestReplaceShaderImage_f` exists at `cg_consolecmds.c:1215` but its table entry is **commented out**: `//{ "testreplace", CG_TestReplaceShaderImage_f },  // debugging` (`:8494`). Only cgame-internal callers use it (crosshair / HUD recolour, `cg_draw.c:2516, 2760, 8612, 8698`). |

Usage (from the source's own help string):

```
remapshader <original shader> <new shader> [time offset: usually 0] [keep original shader lightmap -- 0: no, 1: yes (default)]
clearremappedshader <shader name>
```

`CG_RemapShader_f` calls `trap_R_RemapShader(..., userSet=qtrue)`, which is
what distinguishes a user remap from the server-driven `remapShader` server
command (`cg_servercmds.c:5817`, not reachable while playing back a demo).

### Target selection

Read the Q3 BSP texture lump (lump 1, 72-byte entries) straight out of
`pak00.pk3` to get the shaders a map actually references:

- `maps/trinity.bsp` — 54 textures; **exactly one** ad surface:
  `textures/ad_content/2x1`
- `maps/overkill.bsp` — 69 textures; same single ad surface

### What was run

Demo `CA-pTnTr4sH-trinity-2012_01_28-14_26_22.dm_73`, window
`954700 → 956700`. **One capture, one running session** — the swap and the
revert both happen inside it, no restart:

```
exec wolfcam_tr4sh_master_capture.cfg
seekservertime 954100
at 954700 video avi name p4b_remap
at 955300 remapshader textures/base_wall/concrete_dark        textures/sfx/flameanim_blue 0 0
at 955300 remapshader textures/proto2/asylum2                 textures/sfx/flameanim_blue 0 0
at 955300 remapshader textures/proto2/asylum2a                textures/sfx/flameanim_blue 0 0
at 955300 remapshader textures/proto2/grit01                  textures/sfx/flameanim_blue 0 0
at 955300 remapshader textures/base_wall/cobaltborder_orange  textures/sfx/flameanim_blue 0 0
at 955300 remapshader textures/proto2/grimy_ceiling           textures/sfx/flameanim_blue 0 0
at 956200 clearremappedshader textures/base_wall/concrete_dark
at 956200 clearremappedshader textures/proto2/asylum2
at 956200 clearremappedshader textures/proto2/asylum2a
at 956200 clearremappedshader textures/proto2/grit01
at 956200 clearremappedshader textures/base_wall/cobaltborder_orange
at 956200 clearremappedshader textures/proto2/grimy_ceiling
at 956700 stopvideo
at 957000 quit
```

15 at-commands; `MAX_AT_COMMANDS` is 128 (`cg_local.h:923`), so no overflow.
Remap fires at t = 0.60 s, clear at t = 1.50 s.

### Result — PASS

Fraction of pixels that are strongly blue (`B > R+30` and `B > 60`),
sampled from the **single** output AVI:

| t (s) | blue px | state |
|---|---|---|
| 0.20 | 0.64 % | original |
| 0.40 | 0.14 % | original |
| 0.55 | 0.11 % | original |
| **0.70** | **11.13 %** | **remapped** |
| **0.90** | **6.42 %** | **remapped** |
| **1.10** | **4.64 %** | **remapped** |
| 1.30 | 0.66 % | remapped (camera facing untargeted geometry) |
| **1.45** | **12.50 %** | **remapped** |
| 1.60 | 0.03 % | reverted |
| 1.80 | 0.05 % | reverted |
| 1.95 | 0.06 % | reverted |

`p4b_t0.9.png` shows the concrete walls and ceiling replaced by animated
blue flame; `p4b_t1.8.png` shows normal orange wall again. **The swap and
the revert both happen inside one running wolfcam session — this is a
genuine hot-swap, not a reload.**

### Honest note on the first attempt

The first run targeted the ad board (`textures/ad_content/2x1` →
`textures/sfx/flameanim_blue`). It produced **no visible change** and no
`RE_RemapShader: shader not found` warning. The reason is target visibility,
not mechanism failure: the large yellow "EAT ROOM" sign dominating that
frame is a map decal on a different shader, and the map's single ad surface
was simply not in view at that moment. The wall-shader run above proves the
mechanism; **ad-board remapping specifically was not visually confirmed**
and would need a frame where an ad surface is actually on screen.

### Frames
`p4_t{0.3,0.55,0.9,1.1,1.75}.png` (ad-board attempt, no visible change),
`p4b_t{0.5,0.9,1.2,1.8}.png`, `p4q_t*.png` (the blue-fraction series).
All test AVIs deleted.

---

## Proof 5 — ComfyUI mini-loop (GAME → AI VARIANT → LIVE ENGINE) — **PASS**

Scope: one loop, once. No asset pipeline was built.

### Setup

ComfyUI was **not** running. Started per Rule PH5-5 equivalent
(`E:\PersonalAI\ComfyUI\main.py --port 8188 --disable-cuda-malloc` via the
repo venv; the `Start-Process run_comfyui_api.bat` form exits before the
server binds, and full custom-node import takes several minutes).
`comfyui_version 0.3.76`, torch 2.8.0+cu129. Several optional API nodes
(`nodes_runway`, `nodes_sora`, `nodes_gemini`, …) fail to import for missing
deps — unrelated to this workflow, which ran fine. **ComfyUI was left
running.**

| Item | Value |
|---|---|
| Source texture | `creative_suite/comfy/photoreal/assets/pak00/textures/base_wall/concrete_dark.png` (256×256 RGB) |
| Workflow (existing, audited — **not** invented) | `creative_suite/comfy/workflows/tile_controlnet_sd15.json` |
| Path | 4x-UltraSharp → `ImageScaleBy 0.5` → `dreamshaper_8` SD1.5 + `control_v11f1e_sd15_tile` (the PH5-1 correct pipeline) |
| Variants | A seed 101 denoise 0.35 · B seed 202 denoise 0.35 · C seed 303 denoise 0.50 |

Generator: `scratchpad/gen_variants.py` (uncommitted), driving
`creative_suite/comfy/client.py`.

### Technical validation — all 3 PASS

Source: 256×256, mean 61.4, std 10.6.

| Variant | Size | Scale | mean | std | near-black px | flat? | struct. corr vs source |
|---|---|---|---|---|---|---|---|
| A | 512×512 | 2× | 59.68 | 10.02 | 0.00 % | no | 0.553 |
| B | 512×512 | 2× | 59.08 | 10.05 | 0.00 % | no | 0.553 |
| C | 512×512 | 2× | 60.11 | 10.16 | 0.00 % | no | 0.503 |

All decode cleanly (`PIL.Image.verify()`), none black, none flat. 2× (not
4×) is correct for this workflow — `ImageScaleBy 0.5` follows the 4×
upscale. Structural correlation 0.50–0.55 is **below** the ≥0.87 the
pipeline audit reports for production settings; the aggressive prompt used
here trades layout fidelity for detail. Fine for a wall, would **not** be
acceptable for a UV sheet (PH5-7).

### Live swap

Variant A staged into the wolfcam gamedir as loose files
`wolfcam-ql/textures/pantheon_ai/aiwall.{tga,jpg}` (the gamedir itself is in
the search path — confirmed in the engine's own search-path dump), then
hot-swapped with the Proof-4 mechanism inside one running session:

```
exec wolfcam_tr4sh_master_capture.cfg
seekservertime 954100
at 954700 video avi name p5_ai3
at 955300 remapshader textures/base_wall/concrete_dark        textures/pantheon_ai/aiwall 0 0
at 955300 remapshader textures/proto2/asylum2                 textures/pantheon_ai/aiwall 0 0
at 955300 remapshader textures/proto2/asylum2a                textures/pantheon_ai/aiwall 0 0
at 955300 remapshader textures/proto2/grit01                  textures/pantheon_ai/aiwall 0 0
at 955300 remapshader textures/base_wall/cobaltborder_orange  textures/pantheon_ai/aiwall 0 0
at 955300 remapshader textures/proto2/grimy_ceiling           textures/pantheon_ai/aiwall 0 0
at 956700 stopvideo
at 957000 quit
```

vs an identical no-remap baseline (`p5_base`):

| t (s) | Δmean | % px changed >16 | state |
|---|---|---|---|
| 0.30 | −4.11 | 43.8 % | before |
| 0.50 | −0.89 | 22.4 % | before |
| **0.90** | **−17.94** | **50.2 %** | **AFTER** |
| **1.20** | **−18.52** | **53.6 %** | **AFTER** |

The high "before" percentage is run-to-run particle nondeterminism in this
explosion-heavy scene — note Δmean stays near zero before the swap and steps
to ≈ −18 after it. `p5_ai3_t0.9.png` shows the mottled green-grey rock and
white concrete of the baseline replaced by the AI-generated grey concrete.

**GAME → AI VARIANT → LIVE ENGINE REVIEW proven end to end, once.**

### Findings

1. **`remapshader` will silently no-op on a shader that is not on screen.**
   The first two attempts remapped only `textures/base_wall/concrete_dark`
   and produced a 0.00 %–1.13 % diff — because that shader is not in view in
   this window. Proof 4's blue came from the *other five* shaders remapped
   alongside it. Always confirm the target is actually rendered before
   concluding the mechanism failed.
2. **`Warning: using default shader for '<name>'` is benign here.**
   `R_RemapShader` first calls `R_FindShaderByName`
   (`renderergl1/tr_shader.c:2612-2643`), which only searches the already-loaded
   hash table and warns when it misses; it then falls back to
   `RE_RegisterShaderLightMap`, which does load from disk. The failure
   message to watch for is the *other* one:
   `WARNING: R_RemapShader: new shader %s not found`. That never appeared.
3. A bare image path (no shader script) is a valid remap target — the
   renderer builds an implicit shader from the image file.

### Frames / artifacts
`scratchpad/variants/concrete_dark_{A,B,C}.png` + `manifest.json`;
`p5_base_t*.png`, `p5_ai_t*.png`, `p5_ai2_t*.png` (the two no-op attempts),
`p5_ai3_t{0.3,0.5,0.9,1.2,1.8}.png`.
Staged textures left at `wolfcam-ql/textures/pantheon_ai/` so the proof is
reproducible (≈2 MB); all test AVIs deleted.

---

## Proof 6 — Depth pass (`mme_saveDepth`) — **PASS**

### What the source says

`mme_saveDepth` (`renderercommon/tr_mme.c:382`, default `0`, `CVAR_ARCHIVE`)
gated by `mme_depthRange > 0` (default `2000`) and `mme_depthFocus`
(default `0`). On `video`, `CL_Video_f` allocates a depth buffer and opens a
**second** output stream alongside the beauty pass
(`client/cl_main.c:6212-6223`); the renderer names it
`videos/<name>-depth-%010d.tga` in per-frame mode
(`renderercommon/inc_tr_init.c:846-858`) or, in AVI mode, as a companion AVI.
Depth is read with `qglReadPixels(..., GL_DEPTH_COMPONENT, GL_FLOAT, ...)`
and linearised against `zFar`/`r_znear` before being written.

### What was run

```
exec wolfcam_tr4sh_master_capture.cfg
seekservertime 380975
at 381575 video avi name p6_depth
at 382575 stopvideo
at 382875 quit
```

launched with `+set mme_saveDepth 1 +set mme_depthRange 2000 +set mme_depthFocus 0`.
Demo `CA-Gr0str4sh-overkill-2013_01_08-21_42_32.dm_73`.

### Result — PASS

Two files produced:

| File | Size | Streams |
|---|---|---|
| `p6_depth-0000.avi` (beauty) | 16,252,928 B | 1920×1080 MJPEG 60 fps + PCM audio |
| `p6_depth-depth-0000.avi` (**depth**) | 4,741,120 B | 1920×1080 MJPEG 60 fps, video only |

**Resolution matches the beauty pass exactly.** Both 0.98 s @ 60 fps.

Per-pixel data is real, not constant:

| Frame | min | max | mean | std | unique values |
|---|---|---|---|---|---|
| t = 0.30 | 123 | 255 | 142.55 | 20.11 | 116 |
| t = 0.60 | 123 | 255 | 144.83 | 19.07 | 123 |

Percentiles at t = 0.30: 1 % = 127, 25 % = 131, 50 % = 134, 75 % = 152,
99 % = 245. The centre pixel moves 176 → 241 between the two frames as the
camera advances — the field tracks the scene, it is not a static pattern.

**Near/far polarity is correct (near = dark, far = light):**

| Region (t = 0.30) | depth mean |
|---|---|
| far doorway (open sky beyond the arch) | **166.7** |
| near right wall | 133.3 |
| near left wall | 130.8 |
| **near gun model** (closest geometry) | **127.7** |

Visualisation `p6_beauty_vs_depth_t0.3.png` (beauty left, normalised depth
right) confirms it by eye: the doorway reads white, the viewmodel reads
black, the floor recedes as a smooth gradient, and the airborne player is a
correctly-placed silhouette at his own depth.

### Caveat — the depth pass is MJPEG-compressed, i.e. LOSSY

The companion stream inherits the master profile's codec
(`cl_aviCodec mjpeg`, `r_jpegCompressionQuality 90`). A 1920×1080 depth
field arrives with only ~116-123 distinct 8-bit levels and JPEG ringing on
depth discontinuities. That is fine for the sanity check above and probably
fine for a coarse ControlNet-depth hint, but it is **not** a precision depth
buffer. Anything needing clean edges should capture depth through the
per-frame TGA path (`mme_saveDepth` with a tga/png video mode) rather than
the AVI companion.

No bulk ControlNet work was run — this proof establishes only that the pass
produces real per-pixel data.

### Documentation — metadata a depth frame would need to travel with

(For the record only. **Not implemented, no code written for this.**)
For a depth frame to be usable later for AI-conditioned generation, the
frame alone is insufficient; it would need to carry:

1. **Camera pose** — world `origin` + `viewangles` (or the full 3×3 axis),
   per frame. Available from the same `ScriptVars`/`cg.refdef` data the FX
   hooks already receive.
2. **Projection parameters** — `cg_fov` (the master profile freezes 115),
   aspect, `r_znear`, and `viewParms.zFar`. Without `zNear`/`zFar` the 8-bit
   value cannot be inverted back to world units.
3. **Depth encoding parameters** — `mme_depthRange` and `mme_depthFocus` at
   capture time, plus the codec/quality actually used, since those define
   the value→distance mapping and its error bar.
4. **Demo identity and time** — `content_hash` of the demo (the
   `frags_rebuilt.db` `demos.content_hash`, not the filename) plus raw
   `serverTime` in ms, so the frame is re-derivable.
5. **Scene recipe id** — the `capture_profile_id` already minted by
   `creative_suite/engine/master_profile.py` (sha256 of cfg + launch sets),
   extended to cover any remapped shaders, loaded `cg_fxfile`, and grade pk3
   present. Without this, two depth frames from visually different scenes
   are indistinguishable in a dataset.
6. **Frame index / fps** so depth and beauty frames can be paired exactly.

Items 4 and 5 are the ones with no current carrier — 1-3 are all readable
from cvars at capture time.

### Findings
`mme_saveDepth` is `CVAR_ARCHIVE`, the same trap as `cg_fxfile` in Proof 3:
it persisted into `q3config.cfg` and would have silently added a depth
companion AVI to every later capture. It was reset to `"0"` explicitly
during cleanup.

### Frames
`p6_depth_t{0.3,0.6}.png`, `p6_beauty_t{0.3,0.6}.png`,
`p6_depth_vis_t0.3.png`, `p6_beauty_vs_depth_t0.3.png`.
Both test AVIs deleted.

---

## Summary

| # | Capability | Verdict |
|---|---|---|
| 1 | `runfx` / `runfxat` native FX DSL | **PASS** (`at <t> runfx` works; bare `runfxat` from an init cfg fires at world origin) |
| 2 | Ghost trail via the player trail FX hook | **PASS** (sprite trail; the `axismodel` model-copy variant is **not** proven) |
| 3 | Colour-grade override via pk3 | **PASS** (obvious + restrained variants both applied, no `ERR_FATAL`) |
| 4 | Live shader replacement | **PASS** — true hot-swap and revert inside one running session |
| 5 | ComfyUI mini-loop → live engine | **PASS** — 3 valid variants, variant A hot-swapped into the running scene |
| 6 | Depth pass `mme_saveDepth` | **PASS** — full-res, non-constant, correct near/far polarity; MJPEG-lossy |

### Cross-cutting lesson

Two of the six proofs were nearly derailed by the same class of bug:
**`CVAR_ARCHIVE` cvars leak between capture runs** via `q3config.cfg`
(`cg_fxfile` in Proof 3, `mme_saveDepth` in Proof 6). A capture harness must
explicitly reset every archived cvar it sets, or a later "baseline" silently
inherits the previous experiment. Both were caught only by looking at
frames — neither produced an error, a warning, or a non-zero exit code.
