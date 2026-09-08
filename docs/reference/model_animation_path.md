# Runtime Model / Animation Format — MD3 vs IQM vs glTF

> Research date: 2026-08-31 | **Read-only research. No code, assets, engine binaries or configs modified.**
> Companion to [`model-texture-pipeline-research.md`](model-texture-pipeline-research.md), which covered the
> MD3 *file format* and the Blender/ComfyUI *authoring* side and explicitly deferred the
> engine-side runtime-format question. This doc answers that question.
>
> Method: direct inspection of the engine trees under `engine/engines/`, the consolidation
> manifest (`engine/engines/_manifest/`), the shipped `wolfcamql-11.3.exe` binary, and
> `output/demo_v2/_wolfcam_staging/baseq3/pak00.pk3`. Every claim below cites the file it
> came from. Nothing here is inferred from general Q3-community folklore.

---

## TL;DR — recommendation

**(a) Stay MD3-runtime — but fix the authoring method, not the format.**

Three findings drive this, and two of them cut *against* the intuitive answer:

1. **IQM is not a porting project.** WolfcamQL has shipped IQM support since **v12.0
   (2018-06-21)**. There is no loader to forward-port. (§2)
2. **But our capture engine is `wolfcamql-11.3`, which has zero IQM support** — verified by
   string-scanning the actual binary the pipeline runs. (§2.2) So "add IQM" really means
   "**re-base the entire capture pipeline from wolfcamql 11.3 to 12.x**", which is a
   pipeline-wide regression risk, not a renderer feature flag. That is the real cost, and it
   buys us almost nothing on its own.
3. **IQM does not give us animation blending.** The ioquake3/wolfcam IQM loader implements
   exactly the same two-pose linear blend that MD3 already does — just in joint space instead
   of vertex space. No blend trees, no additive layers, no per-bone masks, no IK. (§3) The
   "skeletal animation unlocks cinematic flexibility" premise **does not survive reading the
   loader.**

And the decisive one:

4. **The friction the prior doc identified is an authoring problem with an authoring fix.**
   `model-texture-pipeline-research.md` §3.2 named the T2 blocker precisely: a base-mesh edit
   does not propagate across 173/216 existing shape keys. The fix for that is to **author with
   an armature in Blender and bake the armature deformation down to per-frame shape keys on
   export** — topology is then identical across every frame by construction. That is exactly
   the workflow IQM would have given us, obtained **with zero engine change**, because the
   bake target is just MD3 instead of IQM. (§6)

So: **keep MD3 as the runtime format; adopt armature-based authoring with a bake-to-MD3
export step.** Revisit IQM only under the specific trigger in §8.

---

## 1. Does any engine fork we have support IQM?

Yes — five of the eighteen consolidated trees carry an IQM loader. Established by querying
`engine/engines/_manifest/inventory.json` for every path containing `iqm` (the `_canonical/`
tree is content-deduplicated, so per-tree subdirectories are empty skeletons and a naive
`grep` over `_canonical/wolfcamql-src/` returns nothing — the manifest is the authority):

| Tree | IQM files | Notes |
|---|---|---|
| **`wolfcamql-src`** | `code/renderercommon/iqm.h`, `code/renderergl1/tr_model_iqm.c` (49,285 B), `code/renderergl2/tr_model_iqm.c` (58,284 B) | **The one that matters.** See §2. |
| `ioquake3` | same three paths (renderergl1 loader 49,181 B) | Upstream origin of the loader. |
| `quake3e` | `code/renderer/`, `code/renderer2/`, `code/renderervk/` variants | Also has a Vulkan-renderer IQM path. |
| `openarena-engine` | `code/renderer_oa/tr_model_iqm.c` (36,679 B) | Older/smaller variant. |
| `darkplaces` | `model_iqm.h` | Different engine lineage, not relevant. |
| `gtkradiant` | `libs/picomodel/pm_iqm.c` | Editor-side importer, not a runtime. |
| **`q3mme`** | **none** | Flagged in §7 — q3mme is the roadmap's stated future engine. |
| **`wolfcamql-local-src`** | **none** | Old `code/renderer/` layout (34 files, `tr_animation.c` = MDR, no `tr_model_iqm.c`). This is the tree that matches our shipped binary. |

### What the loader actually is

`engine/engines/_canonical/code/renderergl1/tr_model_iqm.c` (1,495 lines) implements:

- `R_LoadIQM` — parser with bounds checking, `IQM_MAX_JOINTS` cap, IQM v1 and v2, byte or
  float blend weights, meshes with joints-and-no-poses, and meshes with no joints at all.
- `R_AddIQMSurfaces` / `RB_IQMSurfaceAnim` — CPU skinning into `tess`.
- `ComputePoseMats` / `ComputeJointMats` — the animation math (§3).
- `R_IQMLerpTag` — tag/attachment resolution (§5).
- `.skin` file support: `R_AddIQMSurfaces` honours `ent->ePtr->customSkin` and matches
  `skin->surfaces[j].name` against the IQM mesh name (lowercased at load time,
  `tr_model_iqm.c:705`, `:1120–1129`).

**What IQM buys over MD3, verified from the code, not assumed:**

| Property | MD3 (measured) | IQM (from loader) |
|---|---|---|
| Animation model | Per-vertex morph; every frame stores every vertex absolutely | Skeletal; vertices stored once, per-frame joint poses |
| Vertex precision | **Quantized to 1/64 unit** (`MD3_XYZ_SCALE (1.0/64)`, `code/qcommon/qfiles.h:86`) | Float positions + float/byte blend weights |
| Normals | 2-byte lat/long encoded | Full precision, re-derived from joint matrices |
| File size | `upper.md3` = 741,796 B, of which **664,320 B (89.6%) is per-frame vertex data** and 58,128 B is per-frame tags — only ~19 KB is topology + UV. `lower.md3` = 583,020 B, **92.5% per-frame vertex data** | Vertex data once (~21 KB for 480 verts) + per-frame joint channels. For a ~30-joint rig at 173 frames that is order-100 KB → roughly a **5–6× reduction**, and it scales with joint count rather than vertex count |
| LOD chain | `upper.md3` / `upper_1.md3` / `upper_2.md3` auto-selected | **None** — `R_RegisterIQM` (`tr_model.c:155`) never populates `mod->numLods`. See §7. |
| `.skin` file support | Yes | **Yes** — same mechanism |
| Tag / attachment | `R_LerpTag` over `md3Tag_t` | `R_IQMLerpTag` over named joints — same `orientation_t` out (§5) |

The size argument is real but not decisive for us: 3.07 MB of MD3 for the whole Xaero LOD set
is irrelevant on a 13 GB corpus. The **precision** argument is the one with cinematic teeth —
1/64-unit quantization is ~0.0156 Quake units of positional snap, which at 1080p60 slow-motion
close-up can read as faint surface swim. It is a real but subtle win, and it is the only
image-quality difference the code supports.

---

## 2. Does WolfcamQL support IQM? (the question that actually matters)

### 2.1 The source tree: yes, since v12.0

`engine/engines/_canonical/version.txt` is WolfcamQL's own changelog. Line 460, under the
`12.0  2018-06-21` heading, in the "ioquake3 fixes and patches" block:

```
12.0  2018-06-21
...
* ioquake3 fixes and patches
    - third person player sounds don't play at full volume
    - OpenAL fixes (crash, ogg fallback)
    - IQM model support
    - SDL audio capture
```

So IQM arrived in wolfcam as a **free side-effect of an upstream ioquake3 sync**, not as
bespoke wolfcam work. The diff confirms it:
`engine/engines/_diffs/code/renderergl1/tr_model_iqm.c.diff.md` reports the wolfcam vs.
ioquake3 delta as **+24 / −24 lines, and all 24 are the same mechanical substitution**
(`ent->e.frame` → `ent->ePtr->frame`, etc.) reflecting wolfcam's `trRefEntity_t` indirection.
There is no wolfcam-specific renderer entanglement in this file at all.

**Consequence: "forward-port the IQM loader to wolfcamql" is not a task that exists.** It was
done upstream eight years ago and wolfcam already carries it.

### 2.2 The binary we actually run: no

Our capture pipeline is pinned to a specific prebuilt:

- `creative_suite/engine/wolfcam_capture.py:39` — `WOLFCAM_VERSION = "wolfcamql-11.3"`
- `:66–79` — copies `wolfcamql-11.3.exe`, `wolfcamql-11.3_SDL.dll`,
  `wolfcamql-11.3_backtrace.dll`, and the `cgamex86.dll` / `qagamex86.dll` / `uix86.dll` set
  into the staging dir
- `creative_suite/engine/master_profile.py:43` — `WOLFCAM_VERSION = "wolfcamql-11.3+laa"`
  (the `+laa` is our own large-address-aware patch, per `docs/reference/why-wolfcam.md`)

String-scanning that exact binary (`engine/engines/ghidra/binaries/wolfcamql-11.3.exe`, byte
size 10,838,297 — **identical to the staged `output/demo_v2/_wolfcam_staging/wolfcamql.exe`**):

| Probe | Occurrences |
|---|---|
| `md3` | 54 |
| `IDP3` | 1 |
| `R_LerpTag` | 2 |
| `RB_SurfaceAnim` | 2 |
| `MDR` | 1 |
| **`iqm` / `IQM` / `INTERQUAKEMODEL`** | **0** |

The renderer is compiled into the exe (the MD3 loader's strings are present), so this is
conclusive: **the engine binary the pipeline runs cannot load an IQM file.** It also matches
the source layout — `wolfcamql-local-src` (the tree the manifest describes as matching the
shipped exe) has the pre-split `code/renderer/` directory with no `tr_model_iqm.c`.

### 2.3 So what would "add IQM" actually cost?

Not a port. **An engine re-base.** The honest scope:

| Work item | Estimate | Risk |
|---|---|---|
| Obtain a ≥12.0 build. Latest stable release is **v12.6 (2024-05-22, `wolfcamql-12.6.zip`, 49.3 MB)**; newest test tag is `v12.7test52`. Our source tree is `12.7test49`, which matches a real release tag. | hours | low — but **verify 32- vs 64-bit**; if still 32-bit, the LAA patch and `com_zoneMegs`/`com_hunkMegs` tuning from `why-wolfcam.md` must be redone |
| Re-validate the capture contract: `seekclock` / `seekservertime`, the `at <serverTime>` scheduler, `cg_enableAtCommands`, `r_useFbo`, `cl_aviCodec` MJPEG q90, `fs_quakelivedir` behaviour (broken in 11.3, may be *fixed* in 12.x — which is itself a behaviour change), the full `LAUNCH_SETS` latch-cvar block in `master_profile.py` | 1–2 days | **medium-high** — this is the entire pixel-truth foundation of the project |
| Re-validate HUD/cgame: 12.x ships its own `cgamex86.dll`; every HUD-element cvar and the visible-weapon config (`docs/reference/visible-weapon-master-config.md`) must be re-checked | 1 day | medium |
| Full-Part render regression to prove A/V parity against a shipped Part | 1 day + render time | — |
| **Then**, separately, the asset work: rig a mesh with an armature, author/retarget all 30 `animation.cfg` states, place `tag_*` joints, export IQM | **unchanged from the T2/T3 estimate in the prior doc — weeks** | high |

The last row is the point. **IQM does not reduce the asset cost at all.** It changes which
Blender exporter you invoke at the end of an identical modelling and animation project.

---

## 3. Animation blending — what each format actually does

This section is the one that changes the answer, so it is quoted from source.

### 3.1 MD3 blends. It is not a hard frame-to-frame cut.

Two distinct blends are already happening in the stock pipeline.

**Within an animation** — linear vertex interpolation between consecutive frames.
`renderergl1/tr_surface.c:977–1113`, `LerpMeshVertexes_scalar`:

```c
newXyzScale = MD3_XYZ_SCALE * (1.0 - backlerp);
newNormalScale = 1.0 - backlerp;
...
oldXyzScale = MD3_XYZ_SCALE * backlerp;
oldNormalScale = backlerp;
```

**Across animation states** — also blended, contrary to the common assumption.
`cgame/cg_players.c:2107–2126`, `CG_SetLerpFrameAnimation`:

```c
lf->animation = (animation_t *)anim;
lf->animationTime = lf->frameTime + anim->initialLerp;
```

`initialLerp` is set from the animation's own fps at `cg_players.c:273`
(`animations[i].initialLerp = 1000 / fps`). When the state switches, `lf->oldFrame` still
holds the **last frame of the outgoing animation** while `lf->frame` becomes the **first frame
of the incoming one**, and `CG_RunLerpFrame` (`:2183–2242`) drives `backlerp` linearly across
that window:

```c
lf->backlerp = 1.0 - (float)( time - lf->oldFrameTime ) / ( lf->frameTime - lf->oldFrameTime );
```

So a state transition is a **~50–66 ms linear crossfade** (1000/20 to 1000/15 ms, from the
per-state fps in `animation.cfg`), not a snap.

**What MD3 genuinely cannot do:**
- Blend more than two poses at once.
- Additive or layered animation (e.g. an aim offset laid over a run cycle).
- Per-bone / per-region masking — Q3's only "masking" is the coarse two-model
  upper/lower split joined at `tag_torso`.
- Blend durations decoupled from the target animation's frame rate.
- Any procedural pose modification: IK, look-at, lean, foot planting.
- Rotational correctness on large joint deltas — vertex-space lerp shortcuts through the arc,
  so fast limb rotations lose volume ("candy-wrapper").

### 3.2 IQM blends. Identically.

`renderergl1/tr_model_iqm.c:1165–1221`, `ComputePoseMats` — the entire animation blend:

```c
if ( oldframe == frame ) {
    /* copy pose verbatim */
} else {
    lerp = 1.0f - backlerp;
    ...
    relativeJoint->translate[i] = oldpose->translate[i] * backlerp + pose->translate[i] * lerp;
    relativeJoint->scale[i]     = oldpose->scale[i]     * backlerp + pose->scale[i]     * lerp;
    QuatSlerp( oldpose->rotate, pose->rotate, lerp, relativeJoint->rotate );
}
```

That is **two poses, one scalar `backlerp`, linear on translate/scale and slerp on rotation.**
Nothing else. And the driver is unchanged — `RB_IQMSurfaceAnim:1270–1272` reads the same
`ePtr->frame` / `ePtr->oldframe` / `ePtr->backlerp` the MD3 path reads, which are still set by
`CG_RunLerpFrame` from the same flat `animation.cfg` frame ranges.

**The honest summary:** switching MD3 → IQM upgrades the interpolation from *vertex-space
lerp* to *joint-space lerp with quaternion slerp*. That is a genuine quality improvement on
fast rotations (no candy-wrapper, no volume loss) and it removes 1/64-unit quantization. It
adds **exactly zero** new blending capability. Any blend tree, additive layer, bone mask or IK
we might want would have to be written by us in `cgame` — and that work is **format-agnostic**;
it is no easier to write against IQM than against MD3's two-model split, because both expose
the same `frame/oldframe/backlerp` triple to the renderer.

---

## 4. glTF: authoring-only. Confirmed.

Confirmed, not assumed. There is no glTF loader in any of the eighteen trees — a search of
`inventory.json` for `gltf`/`glb` returns nothing, and the runtime loader table is exhaustive
(`renderergl1/tr_model.c:193–198`):

```c
static modelExtToLoaderMap_t modelLoaders[ ] =
{
	{ "iqm", R_RegisterIQM },
	{ "mdr", R_RegisterMDR },
	{ "md3", R_RegisterMD3 }
};
```

Three formats. That is the complete set the engine will ever load. So the pipeline is
necessarily **author in a modern tool → bake to an engine-native format**, exactly as the
prior doc's Blender findings implied.

**Exporters, by name:**

| Target | Tool | Status |
|---|---|---|
| glTF/GLB (interchange) | Blender built-in `io_scene_gltf2` | First-party, ships with Blender |
| **IQM** | **`iqm_export.py` from `lsalzman/iqm`** — the format author's own dev kit, with per-Blender-version scripts up to `blender-4.1/iqm_export.py` | First-party to the format. Exports `.iqm` directly, or `.iqe` text for the IQM compiler. Toggles for Meshes / Skeleton / per-frame Bounding boxes. **Exporter only — there is no IQM importer**, so there is no MD3 → IQM round-trip |
| MD3 | community addons — `neumond/blender-md3`, `hypov8/blender-md3_2.7-3.2`, `SomaZ/Blender_BSP_Importer` (best Blender 4.x bet) | Per prior doc §3.1. Import **and** export |

Two consequences worth stating plainly:

- **glTF is never a runtime format here.** It is an interchange step between AI-mesh
  generators / DCC tools and Blender. It never reaches a pk3.
- **The IQM exporter's "Skeleton" toggle exports joints from a Blender armature.** An animated
  IQM therefore *requires* an armature. You cannot mechanically transcode Xaero's 173/216
  shape keys into an IQM — there is no skeleton to derive, and no importer to meet you halfway.
  Going IQM means **rigging the model**, which is the expensive half of the T2/T3 estimate.

---

## 5. Weapon / tag attachment — and one finding that removes a blocker

### 5.1 The dependency

Our capture pipeline depends on tags working. `pak00.pk3` gives Xaero `tag_weapon`,
`tag_torso`, `tag_head` on `upper.md3` and `tag_torso` on `lower.md3` (prior doc §2.2), and
that chain is what puts the visible weapon in the hand — the thing
`docs/reference/visible-weapon-master-config.md` and the FOV-110 benchmark are built around.

### 5.2 IQM preserves the tag API exactly

`renderergl1/tr_model.c:1056–1105`, `R_LerpTag` dispatches on model type and IQM is a
first-class branch:

```c
else if( model->type == MOD_IQM ) {
        return R_IQMLerpTag( tag, model->modelData, startFrame, endFrame, frac, tagName );
}
```

And `tr_model_iqm.c:1460–1495`, `R_IQMLerpTag`, **resolves tags by joint name**:

```c
// get joint number by reading the joint names
for( joint = 0; joint < data->num_joints; joint++ ) {
    if( !strcmp( tagName, names ) )
        break;
    names += strlen( names ) + 1;
}
```

then fills the same `orientation_t` (`tag->axis[3][3]`, `tag->origin[3]`) from the blended
joint matrix. **`cgame` cannot tell the difference.** Name three joints `tag_weapon`,
`tag_torso`, `tag_head` and every existing attachment call site works untouched.

The risk is therefore **not an API break — it is an authoring correctness problem**: those
joints must be named exactly and oriented with the same axis convention MD3 tags use, through
all 30 states, or the weapon sits wrong in the hand in every captured frame. That is a
silent, visual failure mode; it will not error, it will just look wrong in the footage.

### 5.3 The `.md3` hardcoding is NOT a blocker (surprising finding)

`cgame/cg_players.c:735–770`, `CG_RegisterClientModelname`, hardcodes the extension:

```c
Com_sprintf( filename, sizeof( filename ), "models/players/%s/lower.md3", modelName );
ci->legsModel = trap_R_RegisterModel( filename );
```

Wolfcam has **no** MDR/IQM fallback here (stock ioq3 does; wolfcam dropped it — QL has no use
for it). That looks like a hard blocker requiring a `cgamex86.dll` rebuild. It is not, because
`RE_RegisterModel` (`renderergl1/tr_model.c:321–382`) strips the failed extension and retries
every loader in preference order, **IQM first**:

```c
// Loader failed, most likely because the file isn't there;
// try again without the extension
orgNameFailed = qtrue;
orgLoader = i;
COM_StripExtension( name, localName, MAX_QPATH );
...
Com_sprintf( altName, sizeof (altName), "%s.%s", localName, modelLoaders[ i ].ext );
hModel = modelLoaders[ i ].ModelLoader( altName, mod );
```

So a request for `models/players/pantheon/lower.md3` that misses will transparently load
`models/players/pantheon/lower.iqm`. **No cgame change, no DLL rebuild.**

One caveat that matters operationally: the fallback only fires when the `.md3` request
*fails*. `pak00.pk3` already contains `models/players/xaero/lower.md3`, and a pk3 override can
add files but cannot delete one — so dropping `xaero/lower.iqm` into a `zzz_*.pk3` would be
ignored, the stock MD3 would still win. The workable route is a **new model directory**
(`models/players/pantheon/` containing only `.iqm`) selected via the existing cvars
`cg_forceModel` / `cg_enemyModel` / `cg_teamModel` (`cgame/cg_main.c:1683`, `:2096`, `:2112`),
which are already settable from our capture cfg.

---

## 6. The alternative that is actually the unlock

`model-texture-pipeline-research.md` §3.2 named the T2 blocker exactly:

> every other shape key (every other animation frame) must be updated to be topologically
> identical (same vertex count, same vertex order) to the edited base, or export will fail or
> produce garbage

That is presented as an MD3 limitation. **It is not** — it is a consequence of *editing a
shape-key stack directly.* Author the model the way any modern character is authored and the
problem disappears:

1. Model the mesh once, in a single neutral pose. One topology, by definition.
2. Build an armature. Add bones named `tag_weapon`, `tag_torso`, `tag_head` at the positions
   the MD3 tags occupy today (recoverable — the addons import MD3 tags as Empty objects).
3. Skin the mesh to the armature.
4. Author or retarget the 30 `animation.cfg` states as **skeletal** actions. Retargeting
   skeletal motion between armatures is a standard, supported Blender workflow — unlike
   retargeting vertex-morph animation across differing topology, which the prior doc correctly
   identified as needing custom scripting.
5. **Bake the armature deformation down to one shape key per MD3 frame** and export MD3.
   Every frame is generated from the same base mesh, so topology and vertex order are
   identical across all 173/216 frames *by construction* — the exact failure mode that makes
   T2 painful today cannot occur.
6. Re-derive `tag_*` transforms per frame from the corresponding bones.

Steps 1–4 are **identical whether the export target is MD3 or IQM.** The only difference is
step 5: bake-to-shape-keys (MD3) versus export-the-armature-directly (IQM). Step 5 is by a
wide margin the cheapest step in the list, and choosing MD3 there costs us **nothing but disk
space and 1/64-unit quantization** — while saving the entire §2.3 engine re-base.

This is why the recommendation is (a): the format was never the bottleneck.

---

## 7. What breaks if we switch — risk register

Ordered by severity. Anything above the line is a project-level risk, not a bug.

| # | Risk | Severity | Detail |
|---|---|---|---|
| R1 | **Whole capture pipeline re-based 11.3 → 12.x** | **High** | Every finding in `why-wolfcam.md` was established against 11.3: the `fs_quakelivedir` workaround, the LAA/zone/hunk tuning, MJPEG q90 as master, `r_useFbo` determinism, the `at`-scheduler semantics. All of it needs re-proving. A behaviour *fix* in 12.x (e.g. `fs_quakelivedir` starting to work) is as disruptive as a regression. |
| R2 | **`tag_*` joint orientation is a silent visual failure** | **High** | §5.2 — the API is identical, so nothing errors. A mis-oriented `tag_weapon` produces a weapon floating beside the hand in every captured frame of every Part. Detectable only by watching footage, i.e. after render time is spent. |
| R3 | **Rigging is mandatory and non-trivial** | **High** | §4 — no IQM importer, `iqm_export.py` needs an armature. Full skin-weighting + 30-state authoring on a Q3-era mesh. Weeks, per the prior doc's T3 estimate. |
| R4 | **32-bit / LAA status of the 12.x build is unverified** | Medium | Our `+laa` patch exists because 11.3 is a 32-bit binary that `Z_Malloc`-crashed on the UHD texture set. If 12.6 is still 32-bit the patch must be reapplied to a new exe; if it is 64-bit, `com_zoneMegs`/`com_hunkMegs` tuning changes. Either way `master_profile.py:43`'s version pin and any profile hash derived from it change. |
| R5 | **cgame/HUD contract shifts with the new `cgamex86.dll`** | Medium | 12.x ships its own cgame DLL. Visible-weapon config, HUD element cvars, and the FOV-110 benchmark all live on that side. |
| — | — | — | — |
| R6 | **IQM models get no LOD chain** | Low | `R_RegisterIQM` (`tr_model.c:155`) never sets `mod->numLods`; the `_1`/`_2` LOD files have no IQM analogue. For hero close-ups this is arguably *desirable* (always LOD0). For crowded scenes it is a small perf regression. |
| R7 | **q3mme has no IQM loader** | Low now, Medium later | `engine/engines/README.md` names q3mme the eventual single-engine target. Committing player assets to IQM adds a loader port to that future migration. Cheap, though — the ioquake3 variant of `tr_model_iqm.c` uses the `ent->e.*` form q3mme expects, so it is close to a two-file copy (`iqm.h` + `tr_model_iqm.c`) plus a `modelLoaders[]` entry. |
| R8 | **Override-pk3 shadowing does not work for format swaps** | Low | §5.3 — you cannot hide `pak00.pk3`'s `xaero/lower.md3`. Requires a new model directory + `cg_forceModel`. A constraint to design around, not a blocker. |
| — | **Not a risk: `.skin` files** | — | `tr_model_iqm.c:1120–1129` implements `customSkin` by surface name. **The entire T1 ComfyUI reskin pipeline is runtime-format-agnostic** and survives either choice untouched. |

---

## 8. Decision, and the trigger to revisit it

**Now — option (a), MD3 runtime, with the §6 authoring change.**

- Engine cost: **zero.** No re-base, no R1/R4/R5.
- Asset cost: unchanged from the prior doc's T2/T3 estimates, but the §6 method removes the
  single worst source of friction in T2 (shape-key propagation).
- Cinematic cost of *not* going IQM: 1/64-unit vertex quantization, and vertex-lerp instead of
  quaternion-slerp on fast limb rotations. Both are subtle. Neither is a blending capability
  we would gain (§3.2).
- The T1 ComfyUI reskin loop — the thing actually shipping today — is unaffected either way.

**Revisit IQM if and only if all three of these become true:**

1. We commit to a **T3 full custom PANTHEON player model** (at which point we are rigging an
   armature regardless, so IQM export becomes a one-line change of exporter rather than a
   project), **and**
2. We have an **independent reason** to move off wolfcamql 11.3 (a 12.x-only capture feature,
   a 64-bit build we want for the UHD texture set, or the q3mme migration landing) — so the
   R1 re-base cost is being paid anyway and IQM rides along free, **and**
3. Close-up slow-motion review shows the 1/64-unit quantization is **actually visible** in
   graded footage. Test this cheaply first: frame-grab an existing slow-mo close-up and look
   for surface swim before spending anything.

**Explicitly rejected:** option (b) as a standalone project — "add IQM support to one engine
fork." It misnames the work. There is nothing to add; there is an engine version to adopt, and
adopting it for the sake of a format that does not change our blending capability inverts the
cost/benefit.

### Verification checklist if the trigger ever fires

- [ ] Download `wolfcamql-12.6.zip` and confirm 32- vs 64-bit, and whether `+laa` is still needed.
- [ ] String-scan the 12.6 exe for `iqm` to confirm the loader is compiled into the shipped build (11.3 scanned clean at 0 — do not assume 12.6 differs without checking).
- [ ] Confirm 12.x still plays our protocol-73 corpus and that `seekservertime` / `at` semantics are unchanged.
- [ ] Byte-compare a full Part render 11.3 vs 12.6 before migrating any asset.
- [ ] Only then: prototype one IQM body part with `tag_weapon` and eyeball weapon attachment across all 30 states.

---

## Sources

**In-repo (primary evidence, all read-only):**
- `engine/engines/_manifest/inventory.json`, `canonical_map.json` — per-tree file inventory; authority for which tree owns which file (the `_canonical/` tree is content-deduplicated, so per-tree subdirs are empty and direct `grep` is misleading)
- `engine/engines/_canonical/version.txt` — WolfcamQL changelog; `12.0  2018-06-21` → "IQM model support"
- `engine/engines/_canonical/track-ioq3.txt` — upstream ioquake3 IQM commit history
- `engine/engines/_diffs/code/renderergl1/tr_model_iqm.c.diff.md` — wolfcam vs ioquake3 IQM loader, +24/−24 lines, all mechanical
- `engine/engines/_canonical/code/renderergl1/tr_model_iqm.c` — `R_LoadIQM`, `ComputePoseMats:1165`, `ComputeJointMats:1223`, `RB_IQMSurfaceAnim:1253`, `R_IQMLerpTag:1460`, skin handling `:705`/`:1120`
- `engine/engines/_canonical/code/renderergl1/tr_model.c` — `modelLoaders[]:193`, `RE_RegisterModel` extension fallback `:321–382`, `R_RegisterIQM:155`, `R_LerpTag:1056`
- `engine/engines/_canonical/code/renderergl1/tr_surface.c` — `LerpMeshVertexes:977–1113`
- `engine/engines/_canonical/code/qcommon/qfiles.h:86` — `MD3_XYZ_SCALE (1.0/64)`
- `engine/engines/_canonical/code/cgame/cg_players.c` — `CG_RegisterClientModelname:721`, `CG_SetLerpFrameAnimation:2107`, `CG_RunLerpFrame:2183`, `initialLerp:273`
- `engine/engines/_canonical/code/cgame/cg_main.c` — `cg_forceModel:1683`, `cg_enemyModel:2096`, `cg_teamModel:2112`
- `engine/engines/ghidra/binaries/wolfcamql-11.3.exe` — binary string scan (0 IQM strings); byte-identical to `output/demo_v2/_wolfcam_staging/wolfcamql.exe`
- `output/demo_v2/_wolfcam_staging/baseq3/pak00.pk3` — MD3 header parse for the size/frame accounting in §1
- `creative_suite/engine/wolfcam_capture.py:39,66–79`, `creative_suite/engine/master_profile.py:43` — the 11.3 pin
- `docs/reference/why-wolfcam.md`, `docs/reference/replay-runtime-feasibility.md`, `docs/reference/model-texture-pipeline-research.md`, `engine/engines/README.md`

**External:**
- [lsalzman/iqm](https://github.com/lsalzman/iqm) — IQM format development kit; [`blender-4.1/iqm_export.py`](https://github.com/lsalzman/iqm/blob/master/blender-4.1/iqm_export.py); [README.txt](https://github.com/lsalzman/iqm/blob/master/README.txt)
- [Inter-Quake Model (IQM) Format](http://sauerbraten.org/iqm/) — format specification
- [brugal/wolfcamql](https://github.com/brugal/wolfcamql) and [its releases](https://github.com/brugal/wolfcamql/releases) — latest stable `v12.6` (2024-05-22, `wolfcamql-12.6.zip`, 49.3 MB); newest test tag `v12.7test52`
- [neumond/blender-md3](https://github.com/neumond/blender-md3), [SomaZ/Blender_BSP_Importer](https://github.com/SomaZ/Blender_BSP_Importer) — MD3 import/export addons (per prior doc)
