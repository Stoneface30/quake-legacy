# Material / Shader System Audit — How Far Can "ENHANCED QUAKE" Go?

> Research date: 2026-08-31 · Research Agent E, "PANTHEON Engine & AI Asset Overhaul" workstream.
> **Read-only research.** No code changed, nothing built, nothing committed.
> Sibling docs: `docs/reference/model-texture-pipeline-research.md` (geometry + skins),
> `docs/reference/comfyui-texture-pipeline.md` (Phase-5 diffuse generation),
> `docs/reference/moviemaking-feature-matrix.md` (gl1 vs gl2 capture posture).

**User constraint governing every recommendation below:**
> Goal: **ENHANCED QUAKE**. Not: **UNREAL ENGINE IMITATION.**
> Maintain strong silhouettes, high contrast, weapon readability, arena identity.

---

## Evidence classes used in this document

| Tag | Meaning |
|---|---|
| **[VERIFIED]** | Read directly out of source, a binary, or a data file **present in this repo**, with a file:line or a reproducible command. |
| **[MEASURED]** | Produced by a read-only script run against repo data during this audit; the command is included so it can be re-run. |
| **[GENERAL]** | Broader Q3-engine-community knowledge. **Not** verified against our tree. Treat as a hypothesis to test, never as a fact to build on. |

Nothing in this document blurs the three. Where I could not verify something, it says so.

---

## 0. Executive answer

1. **The modern material system exists in our source trees and it is genuinely good** — `renderergl2` carries a full normal / specular / gloss / roughness / parallax / cubemap stage vocabulary plus an optional `r_pbr` metal-roughness mode. **[VERIFIED]**
2. **None of it is reachable from the binary we actually capture with.** The shipped `wolfcamql-11.3.exe` statically links the *classic single* `code/renderer/` (gl1-lineage) — it contains no `cl_renderer` cvar, no renderer DLL loader, and not one material keyword. **[VERIFIED, binary string scan]**
3. **Even if we swapped renderers, Quake Live's maps cannot light a normal map correctly.** QL BSPs ship **no deluxemaps** — measured on `asylum`, `campgrounds`, `bloodrun`. Without deluxemaps, `renderergl2` falls back to the coarse light grid and, when the grid direction disagrees with the surface normal, it *substitutes the surface normal itself* — i.e. normal mapping degenerates to flat head-on lighting. **[MEASURED + VERIFIED]**
4. **Recommendation: Tier 1 now, Tier 2 as the real creative win, Tier 3 explicitly deferred.** Tier 2 ("fake specular" via classic multi-stage `tcGen environment` / `blendfunc` tricks + AI-authored gloss masks) delivers most of the perceived "modernization" *inside the renderer we already ship*, and it is the tier that best protects silhouette and readability. Details in §6.

---

## 1. What our pipeline touches today — the actual current ceiling

The brief assumed `pantheon_ads.py` edits `scripts/gfx.shader` / `scripts/ad_content.shader` inside `pak00.pk3`. **That is not what the code does**, and the real answer matters for tiering.

**[VERIFIED]** `creative_suite/engine/pantheon_ads.py:1-22, 42-48` — the module builds a pk3 containing **only four `textures/ad_content/ad*.jpg` files** and drops it in the wolfcam gamedir as `zzz_zz_pantheon_ads.pk3`. Its own docstring is explicit:

> "The pack contains ONLY the four ad_content jpgs — it cannot override unrelated map textures."

**[VERIFIED]** `creative_suite/api/packs.py:85-95` — the Phase-5 / UHD pack builder works the same way. It swaps the *extension* to `.tga` and relies on the engine's extension-agnostic image resolution so that **existing** shader references pick up the override:

> "we keep the basename and swap the extension so existing shader references pick up our override"

**[VERIFIED]** A repo-wide grep for `.shader` emission in `creative_suite/**/*.py` returns **zero** shader-script writers. Our pipeline has never authored a `.shader` file.

### So the true current ceiling is:

```
Tier 0 (today):  diffuse-texture replacement via pk3 override.
                 Zero shader authoring. Zero engine changes.
```

**The single most important consequence:** we have *never* exercised the shader-authoring path, so the first `.shader` we ever write is also the first chance to break every surface it touches (see the hard failure mode in §4.3). This is a new risk surface, not an incremental one.

**[VERIFIED]** The injection point for shader scripts *does* exist and is already populated by wolfcam itself — `output/demo_v2/_wolfcam_staging/wolfcam-ql/scripts/` contains 9 live `.shader` files (`wcad.shader`, `wcmisc.shader`, `wcmap.shader`, …). Gamedir beats `baseq3`, which is the same precedence `pantheon_ads.py` already exploits. So a future `zzz_zz_pantheon_materials.pk3` carrying `scripts/*.shader` is mechanically straightforward — the risk is semantic, not plumbing.

---

## 2. `renderergl2` material capability — **[VERIFIED]**

**Where it lives:** the SHA-256 dedup put the winning copies at `engine/engines/_canonical/code/renderergl2/`. Provenance is recorded in `engine/engines/_manifest/canonical_map.json`:

```
code/renderergl2/tr_shader.c         canonical_tree = wolfcamql-src   (118,594 B)
                                     variant: ioquake3                (106,717 B)
code/renderergl2/tr_glsl.c           canonical_tree = wolfcamql-src   ( 49,638 B)
code/renderergl2/glsl/lightall_fp.glsl  canonical_tree = wolfcamql-src, also_in: ioquake3
```

**[VERIFIED]** From `engine/engines/_manifest/inventory.json`, file counts per tree:

| Tree | `code/renderer/` | `code/renderergl1/` | `code/renderergl2/` | `code/renderercommon/` |
|---|---|---|---|---|
| `wolfcamql-src` | — | 24 | **70** | 22 |
| `ioquake3` | — | 24 | 66 | 16 |
| `wolfcamql-local-src` | **34** | — | — | — |
| `quake3e` | 28 (+ `renderer2` 68, `renderervk` 46) | — | — | 15 |
| `quake3-source` | 29 | — | — | — |

Two findings fall straight out of that table:

* The **newer wolfcam source tree is already rebased onto a post-split ioquake3** and carries its own `renderergl2` — 70 files, i.e. *more* than upstream ioquake3's 66. `_diffs/code/renderergl2/tr_shader.c.diff.md` records the delta as **+111 / −437 lines vs ioquake3**, so wolfcam actively modified the gl2 shader parser rather than merely inheriting it.
* `wolfcamql-local-src` — the tree the README calls "exact source matching shipped .exe" — has **only the classic `code/renderer/`, 34 files, and no gl2 at all.** This is the first half of the §3 answer.

### 2.1 Stage-type keywords — `_canonical/code/renderergl2/tr_shader.c`

| Keyword | Line | Effect |
|---|---|---|
| `stage diffuseMap` | `:979-982` | `ST_DIFFUSEMAP` |
| `stage normalMap` / `stage bumpMap` | `:983-987` | `ST_NORMALMAP`, seeds `normalScale` from `r_baseNormalX/Y`, `r_baseParallax` |
| `stage normalParallaxMap` / `stage bumpParallaxMap` | `:988-995` | `ST_NORMALPARALLAXMAP` **if `r_parallaxMapping` is on**, else silently downgrades to `ST_NORMALMAP` |
| `stage specularMap` | `:996-1000` | `ST_SPECULARMAP`, `specularScale = (1,1,1,1)` |
| anything else after `stage` | `:1001-1005` | `WARNING: unknown stage parameter` |

### 2.2 Material scalar keywords

| Keyword | Line | Notes |
|---|---|---|
| `specularReflectance <v>` | `:1010-1030` | under `r_pbr 1`, reinterpreted as a metal/nonmetal switch at `v < 0.5` (`:1019-1023`) |
| `specularExponent <v>` | `:1034-1056` | converted to gloss; comment pins the max exponent at 8190 and warns it must match `lightall_fp.glsl` (`:1052-1054`) |
| `gloss <v>` | `:1060-1077` | |
| `roughness <v>` | `:1081-1103` | |
| `parallaxDepth <v>` | `:1107-1117` | writes `normalScale[3]` |
| `normalScale <xy>` \| `<x> <y>` \| `<x> <y> <height>` | `:1123-1152` | |
| `specularScale <rgb> <gloss>` \| `<metallic> <smoothness>` (r_pbr) \| `<r> <g> <b>` \| `<r> <g> <b> <gloss>` | `:1159-…` | four documented arities, `:1154-1157` |

### 2.3 Implicit suffix conventions — no shader authoring required

**[VERIFIED]** `tr_shader.c::CollapseStagesToLightall` (`:2301-2423`) will *auto-attach* maps by filename suffix when the shader does not declare them, provided the surface is lit:

* `<diffuse>_nh` → normal+height, and **sets `parallax = qtrue` automatically** (`:2352-2361`)
* `<diffuse>_n` → normal only (`:2364-2367`)
* `<diffuse>_s` → specular (`:2398-2401`)

This is significant for the AI-asset workstream: **the modern renderer can consume AI-generated normal/spec maps with zero `.shader` files**, purely by naming convention inside a pk3 — exactly the mechanism `packs.py` already uses for diffuse. If we ever reach a gl2-capable binary, Tier 3 becomes a pure asset-naming problem.

### 2.4 Governing cvars — `_canonical/code/renderergl2/tr_init.c:1988-2002`

```
r_normalMapping    1     CVAR_ARCHIVE|CVAR_LATCH
r_specularMapping  1     CVAR_ARCHIVE|CVAR_LATCH
r_deluxeMapping    1     CVAR_ARCHIVE|CVAR_LATCH
r_parallaxMapping  0     CVAR_ARCHIVE|CVAR_LATCH   <- OFF by default
r_cubeMapping      0     CVAR_ARCHIVE|CVAR_LATCH   <- OFF by default
r_pbr              0     CVAR_ARCHIVE|CVAR_LATCH   <- OFF by default
r_baseNormalX      1.0
r_baseParallax     0.05
r_baseSpecular     0.04
r_baseGloss        0.3
```

`r_cubeMapping` is additionally force-disabled below OpenGL 3.0 (`tr_init.c:920-922`). All of these are **LATCH** — they cannot be toggled mid-capture, which matters given the "do not `vid_restart` mid-capture" rule already recorded in `moviemaking-feature-matrix.md`.

### 2.5 The lighting model — `_canonical/code/renderergl2/glsl/lightall_fp.glsl` (521 lines)

Feature gates: `USE_LIGHTMAP` `:3`, `USE_NORMALMAP` `:7`, `USE_DELUXEMAP` `:11`, `USE_SPECULARMAP` `:15`, `USE_CUBEMAP` `:23`, `USE_PARALLAXMAP` `:74`.

* Specular BRDF is a **GGX-style microfacet term** (`CalcSpecular`, `:201-209`), sourced from an ARM SIGGRAPH 2015 presentation per the in-file comment.
* Diffuse is Lambert by default, optional Burley/Disney under `USE_BURLEY` (`:180-191`).
* Non-PBR mode: "diffuse rgb is diffuse / specular rgb is specular reflectance at normal incidence / specular alpha is gloss", and diffuse is energy-conserved against specular at `:412-413`.
* PBR mode (`USE_PBR`, `:398-405`): "specular red is gloss, specular green is metallicness" — a genuine metal-roughness workflow, plus sRGB-ish squaring of albedo at `:395`.
* Gloss→roughness has four selectable conventions: `GLOSS_IS_GLOSS` / `_SMOOTHNESS` / `_ROUGHNESS` / `_SHININESS` (`:416-424`).
* Cubemap reflection uses Lagarde parallax-corrected cubemaps (`:439-448`).

**This is a real, complete, modern material pipeline.** It is not a toy.

**The readability tell is already in the shader source.** `:363-379`:

```glsl
	ambientColor = lightColor;
	float surfNL = clamp(dot(surfNormal, L), 0.0, 1.0);

	// reserve 25% ambient to avoid black areas on normalmaps
	lightColor *= 0.75;

	// Scale the incoming light to compensate for the baked-in light angle
	// attenuation.
	lightColor /= max(surfNL, 0.25);
```

The engine authors had to **flatten 25% of the directional light into ambient** to stop normal-mapped surfaces from going black. That is a direct, source-level admission that bolting normal mapping onto baked Q3 lighting *costs contrast* — the exact currency the user asked us to protect. Any Tier-3 proposal has to answer this.

---

## 3. Which renderer is actually reachable? — **[VERIFIED]**

### 3.1 The shipped binary

Scanned `engine/engines/ghidra/binaries/wolfcamql-11.3.exe` (10,838,297 bytes) for ASCII strings. Reproducible:

```bash
python - <<'EOF'
d=open(r"G:/QUAKE_LEGACY/engine/engines/ghidra/binaries/wolfcamql-11.3.exe",'rb').read()
for k in [b"normalMap",b"specularMap",b"r_normalMapping",b"cl_renderer",
          b"renderergl2",b"r_useFbo",b"rgbGen",b"code/renderer"]:
    print(k, d.count(k))
EOF
```

| String | Count | Reading |
|---|---|---|
| `rgbGen` | 23 | control — the shader-parser string table **is** readable, so zero-counts are meaningful |
| `r_useFbo` | 4 | wolfcam gl1 FBO capture path is present |
| `mme_blurFrames` | 6 | MME accumulator present |
| `code/renderer` | 123 | `__FILE__` paths: `code/renderer/tr_shader.c`, `tr_mme.c`, `tr_shade.c`, … |
| `code/renderergl1` / `code/renderergl2` | **0 / 0** | the split-renderer layout is not in this build |
| `cl_renderer` | **0** | **no renderer-DLL loader compiled in** |
| `normalMap`, `bumpMap`, `specularMap`, `specularExponent`, `specularScale` | **0** | no material vocabulary |
| `r_normalMapping`, `r_specularMapping`, `r_parallaxMapping`, `r_deluxeMapping`, `r_pbr` | **0** | no material cvars |
| `lightall`, `r_hdr`, `r_toneMap`, `r_ssao` | **0** | no gl2 lighting/post stack |
| `glCreateShader` | 5 | GLSL *is* linked — but only for `R_InitFragmentShader` / `InitGlslShadersAndPrograms`, i.e. the MME post-process helper, **not** a material system |

**[VERIFIED]** `output/demo_v2/_wolfcam_staging/` contains `wolfcamql.exe`, `SDL.dll`, `backtrace.dll` — and **no `renderer_opengl1_*.dll` / `renderer_opengl2_*.dll`**. Consistent with a static single-renderer build.

**Conclusion: the engine we capture with has exactly one renderer, and it is the classic gl1-lineage one. `renderergl2` is unreachable from it — not "off by default", but absent.**

### 3.2 Why the "gl1 vs gl2" note in our existing docs is *also* right

`creative_suite/engine/master_profile.py:26` says `renderer: gl1 (cl_renderer default)`, and `docs/reference/moviemaking-feature-matrix.md:251-258` cites `client/cl_main.c:5951` for `cl_renderer` defaulting to `"opengl1"`. Both are accurate **about the newer `wolfcamql-src` tree**:

**[VERIFIED]** `_canonical/code/client/cl_main.c:5951-5960` (canonical_tree `wolfcamql-src`):

```c
cl_renderer = Cvar_Get("cl_renderer", "opengl1", CVAR_ARCHIVE | CVAR_LATCH);
Com_sprintf(dllName, sizeof(dllName), "renderer_%s" DLL_EXT, cl_renderer->string);
if(!(rendererLib = Sys_LoadDll(dllName, qfalse)) && strcmp(...))
    Cvar_ForceReset("cl_renderer");   // falls back to opengl1
```

**[VERIFIED]** `_canonical/Makefile:247-248` `USE_RENDERER_DLOPEN=1` by default; `:46-47` `BUILD_RENDERER_OPENGL2=` (empty, i.e. *not* 0); `:1250-1270` therefore emits both `renderer_opengl1` and `renderer_opengl2` shared libs.

**So there are two distinct truths and they must not be conflated:**

| | Our shipped `wolfcamql-11.3.exe` | The newer `wolfcamql-src` tree in our repo |
|---|---|---|
| Renderer layout | single `code/renderer/` | `renderercommon` + `renderergl1` + `renderergl2` |
| `cl_renderer` | absent | present, default `"opengl1"` |
| gl2 available at runtime | **no** | yes, via `cl_renderer opengl2` + shipping the DLL |
| Material keywords | **none** | full set (§2) |

Reaching gl2 therefore requires **building wolfcam from `wolfcamql-src`** — the "bigger, separate undertaking" the earlier build-audit already flagged. This audit does not re-litigate that; it just prices what you'd get (§6, Tier 3).

**[VERIFIED, and a genuinely good sign if we ever do it]** `_canonical/code/qcommon/qfiles.h:309` defines `BSP_VERSION 47` and both `renderergl1/tr_bsp.c:2240` and `renderergl2/tr_bsp.c:2972` accept `i <= BSP_VERSION`. QL maps are IBSP **47** (measured, §5). So the wolfcam tree's gl2 has already been patched to load Quake Live maps — that particular blocker does **not** exist.

### 3.3 Correction to a repo doc

**[VERIFIED]** `engine/engines/dissection/wolfcamql-src/RENDERER_NOTES.md` describes the wolfcam renderer as a single `code/renderer/` containing `tr_bloom.c` and `tr_glsl.c`. That description matches **`wolfcamql-local-src`** (the shipped build), **not** `wolfcamql-src` (which has the three-way split, per the inventory table in §2). The doc is not wrong about the binary — it is mislabelled about which tree it describes. Worth a one-line fix in a later pass; flagging rather than editing, since this task is read-only.

---

## 4. Real shader syntax for what IS reachable

### 4.1 Reachable today (classic renderer, shipped exe) — **[VERIFIED]**

These are lifted verbatim from shader scripts **on disk in our own staging dir**, `output/demo_v2/_wolfcam_staging/wolfcam-ql/scripts/`. They are not invented.

`wcad.shader` — lightmap modulation + a scrolling environment sheen, i.e. the classic "fake specular":

```
adbox1x1xxxxxxx
{
        qer_editorimage textures/ad_content/ad1x1.jpg
        nopicmip

        {
                map textures/ad_content/ad1x1.jpg
        }

        {
                map $lightmap
                rgbGen identity
                blendfunc gl_dst_color gl_zero
        }

        {
                map $lightmap
                tcgen environment
                tcmod scale .5 .5
                rgbGen wave sin .15 0 0 0
                blendfunc add
        }
}
```

`wcmisc.shader` — a pure environment-mapped additive pass (this is the Q3 "shiny metal" idiom):

```
wc/defragItemShader
{
        {
                map textures/effects/quadmap2.tga
                blendfunc gl_one gl_one
                tcgen environment
        }
}
```

`wcmisc.shader` — a detail/contrast multiply pass:

```
wc/levelShotDetail
{
        nopicmip
        {
                map gfx/wc/detail2.tga
                blendfunc GL_DST_COLOR GL_SRC_COLOR
                rgbgen identity
        }
}
```

**[VERIFIED]** The classic parser accepts these: `tcGen environment` → `TCGEN_ENVIRONMENT_MAPPED` at `_canonical/code/renderergl1/tr_shader.c:1060-1062`; `tcGen lightmap` at `:1064`; the `detail` stage keyword at `:865`.

**This is the whole Tier-2 toolkit**, and it is more expressive than it looks — a gloss/spec mask authored by ComfyUI can be *multiplied into* an `tcGen environment` additive pass so the sheen appears only where the artist wants it. No engine change. See §6.

### 4.2 Would become reachable on a gl2 build — **[VERIFIED against `tr_shader.c` grammar, §2]**

```
textures/pantheon/plate_metal
{
	qer_editorimage textures/pantheon/plate_metal.tga

	{
		map textures/pantheon/plate_metal.tga
		stage diffuseMap
	}
	{
		map textures/pantheon/plate_metal_n.tga
		stage normalMap
		normalScale 1.0 1.0
	}
	{
		map textures/pantheon/plate_metal_s.tga
		stage specularMap
		specularScale 1 1 1 0.65
	}
	{
		map $lightmap
		stage diffuseMap
		tcGen lightmap
	}
}
```

Parallax variant (requires `r_parallaxMapping 1`, which is **off by default**, `tr_init.c:1991`):

```
	{
		map textures/pantheon/floor_nh.tga
		stage normalParallaxMap
		normalScale 1.0 1.0 0.03
		parallaxDepth 0.03
	}
```

Metal-roughness variant (requires `r_pbr 1`, off by default, `tr_init.c:1997`; note `specularScale` reinterprets its arguments as `<metallic> <smoothness>` under PBR, `tr_shader.c:1154-1157`):

```
	{
		map textures/pantheon/plate_metal_s.tga
		stage specularMap
		specularScale 1.0 0.7
	}
```

**Or no shader at all** — drop `plate_metal_n.tga` / `plate_metal_s.tga` next to the diffuse and let `CollapseStagesToLightall` (`:2352-2401`) find them by suffix.

### 4.3 ⚠ The hard failure mode — **[VERIFIED]** — this is the single most important line in this document

The two parsers are **mutually intolerant, and they fail destructively, not gracefully.**

`_canonical/code/renderergl1/tr_shader.c:1124-1128`:

```c
		else
		{
			ri.Printf( PRINT_WARNING, "WARNING: unknown parameter '%s' in shader '%s'\n", token, shader.name );
			return qfalse;
		}
```

and its caller, `:1572-1575`:

```c
			if ( !ParseStage( &stages[s], text ) )
			{
				return qfalse;
			}
```

An unknown stage keyword does **not** skip the stage. `ParseStage` returns false → `ParseShader` returns false → **the entire shader is discarded and the surface falls back to the default shader.** `renderergl2/tr_shader.c:1860` has the identical structure, so the breakage is symmetric.

**Operational rule this implies (proposed for CLAUDE.md if we ever author shaders):**

> **Never ship a single pk3 whose `.shader` scripts contain gl2-only keywords to a gl1 binary.** One stray `stage normalMap` does not degrade a surface — it *deletes* the whole shader. gl1 and gl2 material packs must be separate pk3s, selected at staging time by which binary is being launched.

Because our shipped exe is gl1-only (§3.1), **today that rule reduces to: any `.shader` we author must use only §4.1 vocabulary.**

---

## 5. Lightmap / deluxemap interaction — the readability question

### 5.1 The mechanism — **[VERIFIED]**

`_canonical/code/renderergl2/glsl/lightall_fp.glsl:315-321`:

```glsl
	L = var_LightDir.xyz;
  #if defined(USE_DELUXEMAP)
	L += (texture2D(u_DeluxeMap, var_TexCoords.zw).xyz - vec3(0.5)) * u_EnableTextures.y;
  #endif
```

A **deluxemap is a second lightmap that stores light *direction* per texel.** It is what supplies `L` — the incident light vector — for lightmapped world surfaces. Without it, normal mapping has nothing accurate to be lit *by*.

Deluxemaps are detected at load time by a **lightmap-count parity trick**, `_canonical/code/renderergl2/tr_bsp.c:237-254`: a q3map2 `-deluxe` compile writes lightmaps in interleaved pairs (light, direction, light, direction…), so every surface's `lightmapNum` is even. If **any** surface has an odd `lightmapNum`, `tr.worldDeluxeMapping` is set false.

Without deluxemaps, the fallback path is `R_CalcVertexLightDirs` (`tr_bsp.c:2832-2862`) → `R_LightDirForPoint` (`tr_light.c:465-483`):

```c
	R_SetupEntityLightingGrid( &ent, world );

	if (DotProduct(ent.lightDir, normal) > 0.2f)
		VectorCopy(ent.lightDir, lightDir);
	else
		VectorCopy(normal, lightDir);
```

Two degradations stack here:

1. Light direction comes from the **light grid** — a coarse volumetric probe grid, far lower resolution than the lightmap, and per-*vertex* rather than per-texel. On large flat Q3 brushes (which is most of an arena) that is a handful of samples across an entire wall.
2. When the grid direction is more than ~78° off the surface normal, the engine **replaces it with the surface normal**. Head-on light. A normal map lit head-on shows almost no relief — the bumps flatten out and you have paid a full texture-fetch and lighting-branch cost for close to nothing.

### 5.2 What Quake Live actually ships — **[MEASURED]**

I applied the engine's own parity test to real QL maps, read-only, out of `output/demo_v2/_wolfcam_staging/baseq3/pak00.pk3` (9,285 entries, 149 `.bsp`, 147 `.shader`):

| Map | BSP | Surfaces | Lightmaps | Surfaces with odd `lightmapNum` | `worldDeluxeMapping` |
|---|---|---|---|---|---|
| `asylum` | IBSP 47 | 2952 | 10 | 1280 | **FALSE** |
| `campgrounds` | IBSP 47 | 3919 | 12 | 1464 | **FALSE** |
| `bloodrun` | IBSP 47 | 2733 | 10 | 1099 | **FALSE** |

External lightmap files (`maps/<name>/lm_*.tga`, the HDR/external path at `tr_bsp.c:339`): **0 found in pak00.**

Reproduce:

```bash
python - <<'EOF'
import zipfile, struct
z=zipfile.ZipFile("output/demo_v2/_wolfcam_staging/baseq3/pak00.pk3")
for mp in ["maps/asylum.bsp","maps/campgrounds.bsp","maps/bloodrun.bsp"]:
    d=z.read(mp)
    lumps=[struct.unpack_from("<ii",d,8+i*8) for i in range(17)]
    so,sl=lumps[13]; lo,ll=lumps[14]
    nsurf=sl//104; nlm=ll//(128*128*3)
    odd=sum(1 for i in range(nsurf)
            if (n:=struct.unpack_from("<i",d,so+i*104+28)[0])>=0 and n&1)
    print(mp, nsurf, nlm, odd, "deluxe:", nlm>1 and odd==0)
EOF
```

**[MEASURED]** pak00 also contains **zero** `*_n.*` and **zero** `*_nh.*` textures. The four `*_s.*` hits (`models/players/mynx/blue_s.png`, two `textures/electrocution/…_s.jpg`) are incidental filenames, not authored specular maps. **Quake Live ships no PBR-adjacent art whatsoever.**

### 5.3 Verdict — does normal-mapped specular fight the lightmap?

**Under our actual data: yes, it fights it, and the lightmap loses.**

* **Lightmaps are the arena's identity.** They carry the hand-placed contrast that makes a QL map readable at 125 fps — dark corridors, bright rocket-launcher alcoves, the silhouette-separating value structure the user explicitly asked to preserve.
* **Adding normal-mapped diffuse costs contrast by construction.** `lightall_fp.glsl:367-372` reserves 25% of the directional light as ambient specifically so normal maps don't produce black patches. That is a global contrast reduction applied to every lit surface — bought to protect a feature we'd be adding.
* **And with no deluxemaps, we don't even get the payoff.** Per §5.1 the light direction collapses to the light-grid probe or to the surface normal. The relief we paid contrast for is largely invisible.

**[GENERAL — flagged, not verified]** The community-standard fix is to recompile maps with `q3map2 -light -deluxe`. I want to be blunt about why I am **not** recommending that: recompiling 149 QL BSPs would (a) require the original `.map` sources, which we do not have and which were never released, (b) change the baked lighting of every arena, destroying exactly the identity the constraint protects, and (c) produce maps that no longer match the demos — our `.dm_73` corpus references the shipped BSPs. This is a dead end for this project regardless of engineering appetite.

**[GENERAL — flagged]** A second community path is engine-side normal-map *generation* from diffuse (ioquake3 exposes `IMGFLAG_GENNORMALMAP`, referenced at `tr_shader.c:2350`). I did not audit its quality. Height-from-luminance normals are notoriously unreliable on Q3 art, where the diffuse already has baked-in lighting and painted highlights — the generator reads painted shadow as geometry. Treat as low-confidence.

**What *complements* the lightmap instead:** a **specular/gloss pass that respects the lightmap rather than replacing its direction.** The `wcad.shader` idiom in §4.1 does exactly this — `map $lightmap; blendfunc gl_dst_color gl_zero` multiplies the baked lighting in, and a separate `tcGen environment` additive pass adds view-dependent sheen *on top of* it, without touching the light direction the lightmap already encodes. The lightmap stays the boss. That is the Tier-2 thesis.

---

## 6. Practical modernization tiers

Cost read is honest, including the parts I can't price precisely.

### **Tier 1 — Better albedo only. Zero shader changes. Works today.**

**What:** keep doing exactly what `packs.py` / Phase-5 already do — AI-upscale and restyle the *diffuse* texture, ship it in a `zzz_*` pk3, let the existing shader references resolve it by basename.

**Engine changes:** none. **Shader authoring:** none. **New risk surface:** none.

**Cost:** already built. Marginal cost is ComfyUI GPU time per asset. `full_overnight.py` is resumable and DB-backed.

**Constraint fit:** ★★★★★. Silhouette untouched (geometry and UVs unchanged), contrast untouched (lighting path unchanged), readability governed entirely by art direction — and `PH5-7` already encodes which categories tolerate diffusion (`weaphits`, `gfx`, `icons`, `ui`, `powerups`, `sprites` are upscale-only precisely because diffusion destroys shape-critical reads).

**Honest limit:** this is a *resolution and style* upgrade, not a *material* upgrade. Surfaces stay matte. Metal will not look like metal.

---

### **Tier 2 — Classic multi-stage material fakery. Reachable on the shipped binary. ★ RECOMMENDED NEXT STEP ★**

**What:** author `.shader` scripts for a curated set of surfaces using **only §4.1 vocabulary** — `tcGen environment` sheen passes, `blendfunc` multiply/add stacking, `$lightmap` modulation, `rgbGen wave` for slow animated sheen, detail passes. Pair each with a ComfyUI-generated **gloss/sheen mask** that gates *where* the sheen lands. Ship as `zzz_zz_pantheon_materials.pk3` into the wolfcam gamedir alongside the existing ad pack.

This is not a compromise version of Tier 3. It is **the technique Quake III itself used for every shiny surface in the game**, and it is the reason Q3 metal still reads as metal 25 years later. It is stylistically *native*.

**Why it protects the constraint better than Tier 3 does:**
* It **adds** contrast (additive sheen on top of a multiplied lightmap) instead of spending 25% of directional light on ambient.
* It is **per-surface opt-in** — we choose exactly which 30–60 surfaces get treatment. Weapons, armor, powerups, rail slugs. Not every wall.
* The lightmap remains the primary lighting authority. Arena identity is structurally preserved, not preserved by tuning.

**Engine changes:** none. **New capability required of us:** shader authoring, which we have never done (§1).

**Cost — the honest read:**
* Plumbing (pk3 with `scripts/`, gamedir precedence): **hours.** `pantheon_ads.py` is a working template.
* Getting the *first* shader to render correctly instead of silently falling back to the default shader: this is where the time goes. §4.3 means a typo deletes a surface rather than degrading it, and the only feedback channel is `PRINT_WARNING` in the console — which our automated capture path does not currently scrape.
* **Prerequisite I'd insist on: a shader-lint step.** Parse our authored `.shader` against the gl1 keyword set extracted from `renderergl1/tr_shader.c` and reject anything unknown *before* packing. Cheap to write, and it converts a class of silent, hard-to-diagnose visual corruption into a build-time error. Roughly a day.
* Per-surface art direction: this is a creative loop, not an engineering one — genuinely unbounded, and correctly gated behind the user's judgment (Gate R-2/R-3 style).
* **Estimate: ~1 focused session for the plumbing + linter, then iterative art sessions.**

**Constraint fit:** ★★★★☆. The one real risk is over-application — sheen on every wall would flatten reads and look cheap. Mitigated by keeping the surface list short and reviewed.

**Verification I'd require before calling it done (VIS-1):** side-by-side frame grabs of the same demo timestamp, stock vs material pack, at the same `capture_profile_id`. Plus a console-log scrape confirming zero `unknown parameter` warnings.

---

### **Tier 3 — True normal + specular + parallax. Requires a renderer swap AND does not pay off on our maps.**

**What:** build wolfcam from `wolfcamql-src`, ship `renderer_opengl2`, launch with `cl_renderer opengl2`, generate `_n` / `_nh` / `_s` maps with ComfyUI and let §2.3's suffix auto-attach do the rest.

**Cost:**
* **Engine build.** Already flagged by the earlier build-audit as a separate undertaking. On top of that: `wolfcamql-src` is a *different tree* from the one our exe was built from, so this is not "rebuild what we have" — it's adopting a different wolfcam version and re-qualifying **everything** downstream: protocol-73 demo playback across our 6,465-demo corpus, `wolfcam_*` cvar names, the MME blur/DoF accumulator, `r_useFbo` capture (which per `moviemaking-feature-matrix.md:251-258` is **mature in gl1 and not in gl2** — gl2's FBO path is the stock ioq3 one with its own tonemapping that *alters the QL look*), and the LAA patch. Every frozen `capture_profile_id` in `master_profile.py` is invalidated.
* **Asset generation.** Normal/spec maps for the pak00 surfaces we care about. This part is genuinely cheap — the Phase-5 ComfyUI infrastructure exists and §2.3 means no shader authoring at all.
* **Payoff.** Per §5: **QL maps have no deluxemaps** (measured), so world-surface normal mapping degrades to light-grid or head-on lighting, while every lit surface still pays the 25%-ambient contrast tax at `lightall_fp.glsl:367`. Models and weapons (`LIGHTDEF_USE_LIGHT_VECTOR`, lit from the light grid with a real direction) would fare better than world geometry — that is the *only* part of Tier 3 I'd call promising.
* `r_parallaxMapping` and `r_pbr` are both **off by default** and both **LATCH**; parallax on Q3-scale geometry is [GENERAL] widely reported to swim at grazing angles, which is most of a strafe-jump.

**Constraint fit:** ★★☆☆☆. Highest risk of drifting toward "Unreal imitation" — tonemapping, cubemaps, and PBR albedo squaring all pull the palette away from QL's flat high-contrast look. And it buys the *least* on the surfaces that dominate screen time.

**Recommendation: defer.** If it is ever revisited, revisit it **scoped to weapons and player models only** — where light direction is real — and never for world geometry.

---

### Tier comparison

| | Tier 1 | **Tier 2** | Tier 3 |
|---|---|---|---|
| Engine rebuild | no | no | **yes, + full recapture requalification** |
| Reachable on shipped exe | ✅ | ✅ | ❌ |
| Shader authoring | none | §4.1 vocabulary only | none (suffix auto-attach) |
| Lightmap relationship | untouched | **multiplied in, sheen added on top** | direction *replaced*; −25% directional contrast |
| Works on QL maps as shipped | ✅ | ✅ | ⚠ no deluxemaps → degraded |
| Silhouette / readability risk | none | low (bounded by surface count) | moderate–high |
| Status | **shipping today** | **recommended next** | **defer; weapons/models only if revived** |

---

## 7. Open items — things I could not verify

1. **`wolfcamql-src` version and protocol-73 parity with our exe.** The tree carries the split renderer, so it is a newer wolfcam than our build — but I did not establish *which* version, nor whether its demo playback matches our corpus frame-for-frame. **Blocking for any Tier-3 discussion.**
2. **`wolfcamql-local-src` renderer sources are no longer on disk.** `_manifest/canonical_map.json` records `wolfcamql-src/code/renderer/tr_shader.c` (sha `f389bd43…`, 96,807 B, canonical_tree `wolfcamql-local-src`), but `_canonical/wolfcamql-src/code/renderer/` is an **empty directory**, and no copy survives under `game-dissection/`. The dedup/DELETE pass appears to have dropped them. My gl1 claims are therefore grounded in `_canonical/code/renderergl1/tr_shader.c` **plus the binary string scan**, which agree — but the exact shipped source is not currently inspectable. Worth re-fetching.
3. **Does our capture path surface engine console warnings?** Tier 2's failure mode is a `PRINT_WARNING` followed by a silently wrong frame. I did not check whether `stderr.txt` in the staging dir captures these. **Prerequisite for Tier 2.**
4. **`IMGFLAG_GENNORMALMAP` quality** (engine-side normal generation) — not audited. [GENERAL] low confidence on Q3 art with baked-in lighting.
5. **`RENDERER_NOTES.md` mislabel** (§3.3) — one-line doc fix, deliberately not made here.

---

## Appendix — files touched during this audit (all read-only)

| Path | Used for |
|---|---|
| `engine/engines/_canonical/code/renderergl2/tr_shader.c` | §2.1, §2.2, §2.3, §4.2, §4.3 |
| `engine/engines/_canonical/code/renderergl2/tr_init.c` | §2.4 |
| `engine/engines/_canonical/code/renderergl2/tr_bsp.c` | §5.1 |
| `engine/engines/_canonical/code/renderergl2/tr_light.c` | §5.1 |
| `engine/engines/_canonical/code/renderergl2/glsl/lightall_fp.glsl` | §2.5, §5.3 |
| `engine/engines/_canonical/code/renderergl2/glsl/lightall_vp.glsl` | §5.1 |
| `engine/engines/_canonical/code/renderergl1/tr_shader.c` | §4.1, §4.3 |
| `engine/engines/_canonical/code/client/cl_main.c` | §3.2 |
| `engine/engines/_canonical/code/qcommon/qfiles.h` | §3.2 |
| `engine/engines/_canonical/Makefile` | §3.2 |
| `engine/engines/_manifest/{canonical_map,inventory}.json` | §2 provenance |
| `engine/engines/_diffs/code/renderergl2/tr_shader.c.diff.md` | §2 |
| `engine/engines/ghidra/binaries/wolfcamql-11.3.exe` | §3.1 (string scan) |
| `output/demo_v2/_wolfcam_staging/baseq3/pak00.pk3` | §5.2 (zipfile read) |
| `output/demo_v2/_wolfcam_staging/wolfcam-ql/scripts/*.shader` | §4.1 |
| `creative_suite/engine/pantheon_ads.py`, `creative_suite/api/packs.py`, `creative_suite/engine/master_profile.py` | §1, §3.2 |
| `docs/reference/moviemaking-feature-matrix.md` | §3.2, Tier 3 |
