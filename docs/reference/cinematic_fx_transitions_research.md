# Cinematic FX & Transitions — Research

> Research Agent F · PANTHEON Engine & AI Asset Overhaul workstream
> Date: 2026-08-31
> Status: **research only** — no code changes, no commits.
> Scope: what cinematic effects are worth building on the native in-engine FX/camera
> hooks, ranked by wow-factor-per-engineering-cost.

---

## 0. How to read this document

Every claim carries one of three markers. This matters — the whole point of the
exercise is to not oversell complexity that isn't there, and not undersell rendering
work that genuinely is.

| Marker | Meaning |
|---|---|
| **[SRC]** | Read directly out of this repo's engine source or shipped scripts. Absolute path + line given. Highest confidence. |
| **[WEB]** | From an external source. Cited in §9. |
| **[ASSESS]** | My own reasoned engineering assessment, extrapolating from the above. **Not a citation.** Treat as a hypothesis to be proven by a spike, not as fact. |

A working assumption handed down by the workstream lead, adopted here without
re-derivation: **there IS a native FX-script hook of some capability**
(`CG_RunQ3mmeScript` / `EffectScripts.*`). Agent B is doing the engine-level deep
dive on exactly what that hook can do. This document assumes the hook exists and
asks the next question: *what should we build with it?*

Everything below that is marked **[SRC]** was nonetheless verified first-hand while
writing this, because "what to build" is meaningless without knowing what the
primitives actually are.

---

## 1. Verified capability inventory

This is the palette. Everything in §3–§6 is composed from it.

### 1.1 The FX script language is far richer than its shipped documentation

The doc that ships with the engine —
`G:\QUAKE_LEGACY\engine\engines\_canonical\trunk\files\fxScript.txt` — is titled
*"Short Guide on FX Scripting, CaNaBiS Version 0.001"* and documents roughly
**25 tokens**. **[SRC]**

The actual parse table in
`G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_fx_scripts.c:341-560`
registers **well over 200 tokens**. The shipped doc is missing most of the
interesting half of the language. **[SRC]**

Do not plan against `fxScript.txt`. Plan against the parse table.

**Render primitives** (`cg_fx_scripts.c:436-457`) **[SRC]**

| Token | What it draws |
|---|---|
| `sprite` | View-aligned billboard (`cullNear` option) |
| `spark` | View-aligned streak oriented along `velocity`, `width`-controlled |
| `quad` | Surface/`dir`-aligned sprite (not view-aligned) |
| `beam` | Texture stretched between `origin` and `end`, `angle`-repeatable |
| `rings` | Segmented ring chain along a vector, step size from `width` |
| `light` | Dynamic light, radius from `size`, colour from `color` |
| `decal` / `decaltemp` | Persistent / temporary wall mark (`alpha`, `energy` modes) |
| `dirmodel` / `anglesmodel` / `axismodel` | MD3 model oriented by `dir` / `angles` / full 3×3 axis |

**Control flow and emission** **[SRC]**

`emitter <life>` / `emitterf` (spawn a persisting entity that re-runs its block each
frame for `<life>` seconds) · `distance <units>` (fire once per N units of parent
travel) · `interval <seconds>` (fire once per N seconds) · `repeat <n>` ·
`if` / `elif` / `else` · `return` / `continue` · `pushparent` / `pop` ·
`emitterid` (tag emitters so `/clearfx <id>` can kill them).

**Simulation** **[SRC]**

`movegravity` · `movebounce <gravity> <elasticity>` · `sink` · `impact <speed> {…}`
(run a nested block when the emitter hits world geometry) · `trace` (world collision
query from script) · `rotate` · `rotatearound` · `vibrate` (camera shake) ·
`alphafade` · `colorfade` · `shadertime` · `animframe`.

**Audio** **[SRC]** — `sound`, `soundlocal`, `soundweapon`, `loopsound`, and the
`soundlist*` random-pick variants.

**Escape hatches** **[SRC]** — `command` (issue a console command from inside an FX
script), `script` (call another FX script — scripts compose), `echo`, `shaderlist`,
`modellist`.

**Per-element render flags** — attachable to any emitted element
(`cg_fx_scripts.h:109-118`; q3mme parse block `fx_parse.c:388-401`): **[SRC]**
`firstPerson` · `thirdPerson` · `shadow` · `cullNear` · `cullRadius` ·
`depthHack` · **`stencil`** · **`wallhack`**.

The last two are backed by renderfx flags q3mme *added* to stock Quake 3
(`_forks\q3mme\trunk\code\cgame\tr_types.h:41-43`): **[SRC]**
`RF_STENCIL` — *"Stencil whatever is outputted from this model"* — and
`RF_NODEPTH` — *"No depth at all (seeing through walls)"*.

`stencil` is a **per-element matte tag**. Combined with `mme_saveStencil` (§1.6) it
means an FX element can be isolated into its own mask channel at capture time
without touching the renderer. That is the mechanism §3.4 needs. **[ASSESS]**

**Math** **[SRC]** — full expression parser: `+ - * / %`, comparison/boolean
`< > ! = & |`, `sqrt ceil floor sin cos tan asin acos atan atan2 pow wave clip`,
constants `time cgtime loop loopcount lerp life pi rand crand`, per-instance state
`t0..t9` and `v0..v9` vectors, plus `parentOrigin/Velocity/Angles/Dir/End/size`.

The single most under-appreciated line in the whole language, from
`fxScript.txt:123-126`: **[SRC]**

> "if the fx math parser can't find the variable name it'll try to see if there's a
> regular q3 cvar with that name and then it'll use that value"

**Any cvar is a live input to any FX script.** That is the gating mechanism for
"turn this effect on only for this one frag" — see §5.3. **[ASSESS]**

### 1.2 Script hook names (the trigger surface)

Weapon hooks follow `weapon/<name>/<phase>` where phase ∈
`{fire, flash, projectile, trail, impact, impactflesh}`, documented in the header of
`G:\QUAKE_LEGACY\engine\engines\_canonical\trunk\files\scripts\base_weapons.fx:1-6`
**[SRC]**. Weapons present in the shipped scripts: `rocket`, `rail`, `lightning`,
`grenade`, `plasma`, `shotgun`, `machinegun`, `bfg`, `gauntlet`, `grapple`, plus
`weapon/common/*`.

Player hooks include the medal/event set (`player/talk`, `player/excellent`,
`player/impressive`, …) and, critically, three **trail** hooks that are a WolfcamQL
addition and are *not* in upstream q3mme — see §6.

Also registered: `player/teleportIn`, `player/teleportOut`, `player/gibbed`,
`player/haste`, `player/flight`, `player/quad`, `jumpPad`, `headShot`, `thawed`,
`impactFlesh`. **[SRC]**
(`cg_fx_scripts.c:6884-6990`)

### 1.3 Scripts can be fired without a game event

WolfcamQL adds `/runfx <fx name>`, `/runfxat`, `/runfxall <script>`, `/clearfx [id]`
and `/localents`. **[WEB — `README-wolfcam.txt`]**

This is the difference between "FX are decoration on gameplay" and "FX are a
director's tool". `/runfxat` lets you detonate an arbitrary effect at an arbitrary
world position at an arbitrary time, driven by a camera point's `command` field.
**[ASSESS]**

### 1.4 The camera system is a full keyframe animation system

From `G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_camera.h:61-242`
and `README-wolfcam.txt:1084-1207`: **[SRC]**

- **Origin types**: `interp`, `jump`, `spline`, `curve`, `splineBezier`, `splineCatmullRom`
- **Angle types**: `interp`, `spline`, `fixed`, `interpuseprevious`, `fixeduseprevious`,
  `viewpointinterp`, `viewpointfixed`, `viewpointpass`, and **`ent <entity number>`**
  — *the camera can be aimed at a live entity, including a missile*
- **FOV**: `current`, `interp`, `fixed`, `pass`, `spline` — i.e. FOV is animatable
  independently of position (dolly-zoom / vertigo shot is free)
- **Roll**: independent of angles (`interp`/`fixed`/`pass`) or folded into them (`angles`)
- **XYZ offset**: separate animatable channel on top of the path
- **Per-channel initial/final velocity**: real ease-in/ease-out per channel
- **`command`**: an arbitrary console command executed when the camera point is hit
  (`CEF_COMMAND`, `cg_camera.h:57`; enabled at playback by `cg_cameraQue 2`)
- `cg_cameraRewindTime` seeks *before* the path start so local entities (rail trails,
  marks, smoke) exist and are correctly aged by the time the shot begins

`README-wolfcam.txt:1181` explains the `*useprevious` angle modes exist precisely
"when you want to transition from following an entity (player, **missile**, etc.)
and want to transition the viewangles without jumping." **[SRC]** — projectile
follow-cam is an anticipated use case of the existing system, not an exotic one.

### 1.5 Camera files are plain text — this is the linchpin

`cg_consolecmds.c:2255-2333` writes `cameras/<name>.cam10` as line-oriented ASCII:
a `WolfcamCamera 10` header then, per point, labelled lines
(`origin`, `angles`, `type`, `viewType`, `rollType`, `flags`, `cgtime`, `splineType`,
`numSplines`, `viewPointOrigin`, `viewEnt`, `offsetType`, `x/y/zoffset`, `fov`,
`fovType`, the twelve `use*Velocity` / `*InitialVelocity` / `*FinalVelocity` fields,
then `commandStrLen` + the raw command string). `WOLFCAM_CAMERA_VERSION` is `10`
(`cg_camera.h:7`). **[SRC]**

**Camera paths are therefore generatable offline from Python.** A SceneRecipeV2
recipe can emit a `.cam10` file directly from parsed demo data — no in-game camera
authoring, no GUI, fully reproducible, diffable in git. **[ASSESS]**

This is the single highest-leverage fact in this document. Nearly every transition
in §3 reduces to "write the right `.cam10` file".

### 1.6 Capture-side channels we already own

From `cvars.txt` in the q3mme upstream and mirrored in Wolfcam **[WEB]**:

- `mme_blurFrames` / `mme_blurType` / `mme_blurOverlap` / `mme_blurStrength` /
  `mme_blurJitter` — true accumulation motion blur (not a post filter)
- `mme_dofFrames` / `mme_dofRadius` / `mme_depthFocus` / `mme_depthRange` —
  accumulation depth of field
- `mme_saveDepth` — **writes a depth mask as a separate output stream**
- `mme_saveStencil` — **writes a stencil mask as a separate output stream**
- `mme_skykey` — chroma-key colour for the skybox
- `mme_worldShader` — replace all world textures with one shader

The last four are matte-generation tools. They mean compositing tricks that would
normally require new render code can instead be done in FFmpeg against an
engine-produced matte. See §3.4. **[ASSESS]**

> ⚠ **Caveat that changes the §3.4 estimate.** In upstream q3mme these are all
> registered together (`_forks\q3mme\trunk\code\renderer\tr_mme.c:814-851`, with
> `mme_saveStencil` at L847 and `mme_saveDepth` at L848). In the **WolfcamQL port**
> — `_canonical\code\renderercommon\tr_mme.c:367-382` — `mme_saveDepth` survives but
> **`mme_saveStencil` is commented out at line 381**, and `mme_blurGamma` is absent
> entirely. **[SRC]**
>
> So on the build we actually run today: depth matte = yes, stencil matte = **no,
> until someone un-comments one line and rebuilds**. That is a ~1-line change, not a
> feature, but it is a rebuild — worth knowing before scoping §3.4 variant (b).

### 1.7 What is genuinely NOT there

- **No screen-space distortion / refraction / heat-haze shader keyword.** The Q3
  shader language deforms *geometry* (`deformVertexes wave|normal|move|bulge|
  autoSprite|autoSprite2|projectionShadow|text`) and animates *texture coordinates*
  (`tcMod turb|scroll|scale|stretch|rotate|transform`), but has no way to sample the
  framebuffer. Verified against the keyword tables in
  `code/renderer/tr_shader.c:367,1059,1182-1189,1877` **[SRC]**, consistent with the
  official shader manual **[WEB]**. A real heat-haze/refraction is a **new render
  pass**, full stop.
- **The rend2 renderer IS present in this tree** —
  `G:\QUAKE_LEGACY\engine\engines\_canonical\code\renderergl2\` with `tr_fbo.c`,
  `tr_postprocess.c` and a `glsl/` directory. Existing post passes are
  `RB_ToneMap`, `RB_BokehBlur`, `RB_RadialBlur`, `RB_SunRays`, `RB_GaussianBlur`,
  plus SSAO and shadow GLSL. **[SRC]** There is **no** distortion pass today, but
  the FBO plumbing to add one exists. *This is Agent A's territory — noted as a
  dependency, not resolved here.*
- **No portal rendering.** No stencil-portal or render-to-texture-portal machinery
  in the cgame or renderer. **[SRC]**
- **No afterimage/ghost system exists today.** No `afterimage`, `ghostTrail` or
  `trailEnt` symbols anywhere in the cgame. **[SRC]** §6 builds one out of the FX
  emitter primitives — that's construction from parts, not use of a feature.

**One clarification so nothing gets confused later**: there is *also* a conventional
Q3/Team-Arena particle system in `cg_particles.c` (`P_SMOKE`, `P_SPARK`-family types,
a fixed `particles[MAX_PARTICLES]` pool, `CG_ParticleExplosion` / `CG_ParticleSparks`
/ `CG_ParticleBulletDebris` etc.). **[SRC]** It is **separate from and unrelated to**
the FX script system, is not scriptable, and is not what §5 refers to. Everything in
§5 goes through `.fx`, not through `cg_particles.c`. Touching the particle system
means writing C; touching the FX system means writing a text file. Prefer the latter.

---

## 2. Historical precedent: what the community achieved in-engine vs. in post

Worth stating because it explains *why* the native set matters so much to this
project.

The defining innovation of Quake-era moviemaking was **recamming**: recording to the
engine's demo format rather than to video, then manipulating cameras, timing and
lighting afterwards without re-enacting anything. Keygrip 2.0 introduced recamming
for Quake and Paul Marino called it "a defining moment for machinima."
**[WEB — Machinima/Lowood, Quake done Quick]**

That is exactly the architecture we already have: `.dm_73` corpus → Wolfcam camera
paths → capture. Our pipeline *is* the recamming pipeline; we're just automating the
camera-authoring step that the community did by hand.

The practical division of labour in the Q3/QL fragmovie scene, as far as I can
reconstruct it:

| Done in-engine | Done in post |
|---|---|
| Camera paths, splines, jump cuts, FOV ramps | Colour grading |
| FX scripts (weapon trails, impacts, rail styling) | Text/titles/logo animation |
| Motion blur (`mme_blurFrames` accumulation) | Music sync, beat-cut assembly |
| Depth of field (`mme_dofFrames` accumulation) | Speed ramps applied to captured footage |
| Timescale slow-motion at capture time | Any screen-space distortion or glow |
| Player/weapon model and skin replacement | Compositing multiple captures |

**[ASSESS, informed by WEB]** The important asymmetry: in-engine effects are
*parameterised and reproducible* — a `.fx` file and a `.cam10` file fully determine
the output. Post-production effects in a fragmovie were historically hand-keyframed
per shot and are not reproducible across a 12-Part series. Since SceneRecipeV2 wants
determinism, **every effect we can push left into the engine is worth
disproportionately more than the same effect achieved in post.** That is the thesis
this whole document serves.

Note also that motion blur and DOF are *accumulation* effects here — the engine
renders N sub-frames and merges them **[WEB — `cvars.txt`]**. That is physically
correct, unlike a post-hoc blur filter, and it is genuinely not reproducible in
FFmpeg. It is a real capability advantage we should be exploiting more.

`README-wolfcam.txt:1240-1249` carries an important warning that will bite us:
camera path playback speed interacts with capture framerate and blur frame count —
"if you have a camera that looks like you want it at 125fps and then you try to
render a video at 30fps the camera will slow down." **[SRC]** Any generated camera
path must be authored against the *capture* framerate, not the preview framerate.

---

## 3. The four transition primitives — honest verdicts

**Headline conclusion, stated up front: three of the four require no new rendering
whatsoever. They are camera-path-and-cut-timing problems — classic match cuts. The
fourth is optional-scope: the cheap version is also free, and only a literal
see-through-portal version would need real render work, which I do not recommend
building.** **[ASSESS]**

A match cut is "a transition between a pair of shots that uses similar framing,
composition, or action to fluidly bring the viewer from one scene to the next" and
can key on "framing, motion, action, subject matter, audio, lighting, and color."
**[WEB — StudioBinder / Wikipedia]** The related *invisible cut* "hides your cut by
making the end frame of your first clip, and the beginning frame of your second
clip, exactly the same." **[WEB — Motion Array]** Whip-pan match cuts in particular
are noted as *not* achieved practically on set but assembled in post from a shot
that whips away and a shot that whips in, with motion blur being "integral to making
the transition work since it helps to hide the cut." **[WEB — StudioBinder /
NoFilmSchool]**

Every one of our four primitives is a variant of one of those two patterns. We
already have engine-accumulated motion blur, which is the exact ingredient the
film-side technique says is load-bearing.

---

### 3.1 PROJECTILE BRIDGE — camera follows a rocket into the next scene

**Verdict: camera + cut. No new rendering. Medium build cost, all of it in tooling.**

**How it decomposes** **[ASSESS]**
1. Scene A: camera accelerates onto the rocket's flight path, travelling with it,
   FOV widening (`fovType spline`) so the world streaks past.
2. At impact — or just before frame-fill — motion blur peaks. Cut.
3. Scene B opens on a matching forward dolly at matching velocity and matching FOV,
   decelerating.

The audience reads it as one continuous flight. This is a whip/velocity match cut,
and the technique explicitly relies on blur to conceal the seam **[WEB]** — which
`mme_blurFrames` gives us for free at capture time.

**Why it's cheap on the engine side**
- The camera never needs to *be* the rocket. It needs to be *near* the rocket
  travelling at rocket speed. A `splineCatmullRom` origin path with a handful of
  points does this. **[ASSESS]**
- Aiming is already solved natively: `/ecam angles ent <entity number>` locks
  view angles to a live entity, and `interpuseprevious` / `fixeduseprevious` exist
  specifically to let you *stop* following an entity without the angles snapping
  (`README-wolfcam.txt:1181`). **[SRC]**

**Where the actual work is** **[ASSESS]**
The origin path has to come from somewhere. Missile entities in `.dm_73` use
`trType`/`trBase`/`trDelta`/`trTime` trajectory fields, so a rocket's position at
any time is closed-form — no simulation needed. The build is:

`parsed missile trajectory → offset/lead the path → emit .cam10 points`

That is a pure-Python component in the existing parser + recipe stack, plus one
`.cam10` writer (§1.5). No C. No renderer. The `.cam10` writer is a shared
dependency of nearly everything else in this document, so its cost amortises.

**Honest caveats**
- Two demos means two separate Wolfcam captures joined in FFmpeg. That is already
  how the pipeline works, so it's not new cost — but the two captures must agree on
  framerate, blur settings and FOV at the seam or the cut will read as a cut. **[ASSESS]**
- Rockets are slow enough (~900ups) that a naive "camera exactly on the rocket" shot
  looks sluggish. Expect to over-crank FOV and add a speed ramp. **[ASSESS]**
- `com_timescalesafe` warning at `README-wolfcam.txt:646`: high timescales skip demo
  snapshots and "will break things like camera paths that are synced to server
  times." **[SRC]** Do slow-motion via capture framerate, not timescale, on any shot
  carrying a camera path.

---

### 3.2 TELEPORTER PASS — camera enters a teleporter, exits into another scene

**Verdict: pure match cut. Genuinely the cheapest of the four, and arguably the most
striking. No new rendering. Recommended as a first build.**

**Why no portal rendering is needed** **[ASSESS]**
The shot is: dolly into the teleporter until the teleport shader fills the frame →
cut on the full-frame wash → dolly *out* of a teleporter in scene B. At the moment
of the cut both frames are ~100% teleport-swirl, which is the textbook invisible cut
condition — identical end and start frames **[WEB — Motion Array]**. Nobody ever
sees through the portal, so nothing ever needs to be rendered through it.

A real see-through portal is a genuinely different animal — stencil-buffer masking
or render-to-texture, with the virtual camera placed where the main camera would be
after teleporting, plus an oblique clip plane **[WEB — Ilett / GameDev.net]**. That
work is real and this shot does not need one gram of it.

**What we already have** **[SRC]**
- `player/teleportIn` and `player/teleportOut` scripts ship, using
  `models/misc/telep.md3` with the `teleportEffect` shader and a `colorFade 0`
  emitter (`base_player.fx:66-90`). The QL variant swaps in `models/powerups/pop.md3`
  (`q3mme.fx:183-196`).
- `EffectScripts.playerTeleportIn/Out` are dispatched from `cg_event.c:2454-2471`.

**Build** **[ASSESS]**
1. `.cam10` path: three points, `splineCatmullRom`, accelerating into the teleporter
   volume, `fovType spline` narrowing slightly (adds the "pulled through" feel).
2. Optionally `/runfxat` a `telep.md3` + `teleportEffect` emitter at an arbitrary
   position via the camera point's `command` field — meaning **the map doesn't even
   need a teleporter where you want the transition**. This is the trick that makes
   the primitive general rather than map-dependent.
3. Mirror the path in scene B, reversed.
4. Cut on the peak-white frame in FFmpeg.

**Caveats** — the QL teleport shader is short (~0.5s emitter life) and may need a
custom longer-lived variant for a slower, more deliberate pass. Trivial `.fx`
edit. **[ASSESS]**

---

### 3.3 GEOMETRY MATCH — matching an arch/door/corridor across two scenes

**Verdict: 100% a classic match cut. Zero engine work. But the cost is real and it
is *all* in finding the pairs — this is a tooling problem, not an FX problem.**

This is the graphic match, the oldest trick in the book **[WEB — Wikipedia/Match
cut]**. Two shots framing a similar shape at a similar screen position, cut between.
Nothing renders differently; the camera just has to be in the right place with the
right FOV in both maps.

**Why I'd rank this last of the four despite it being technically free** **[ASSESS]**
Getting engine-side is trivial (two `.cam10` files). Getting *good* requires knowing,
for every map in the corpus, where the arches and doorways are and what they look
like from what angle. Three routes:

| Route | Cost | Quality |
|---|---|---|
| Hand-curated shape library (director picks ~20 arch/door framings across the top maps, stored as camera presets) | **LOW** | High, but doesn't scale |
| BSP-derived: extract portal/door brushes from the `.bsp`, score for aspect and openness | HIGH | Unknown until tried |
| Visual: render candidate framings, embed, nearest-neighbour match | HIGH | Plausible, needs a render sweep |

The hand-curated route is the honest recommendation. Twenty good framings across
`campgrounds`, `bloodrun`, `aerowalk`, `furiousheights` etc. covers the series, and
the resulting camera presets are reusable data, not throwaway. Attempting automated
geometry matching before the manual version has proven the shot works would be
premature. **[ASSESS]**

Note the map catalog at `G:\QUAKE_LEGACY\docs\reference\map-catalog.md` is the
natural home for such a shape library.

---

### 3.4 IMPACT PORTAL — an explosion becomes the transition mask

**Verdict: split it. Variant (a) is free and I'd ship it. Variant (b) is a
compositing job, not a rendering job, and is cheaper than it sounds because the
engine already emits mattes. Neither needs new render code.**

**Variant (a) — explosion fills frame, cut on the flash. FREE.** **[ASSESS]**
The existing rocket impact script already does most of it
(`base_weapons.fx:60-74`) **[SRC]**:

```
weapon/rocket/impact {
    vibrate 70
    sound   sound/weapons/rocket/rocklx1a.wav
    shader gfx/damage/burn_med_mrk
    size    64
    Decal
    shader rocketExplosion
    size 40
    color 1 0.75 0
    emitter 1 {
        Sprite
        size 300 * clip(2 - 2*lerp)
        Light
    }
}
```

Put the camera close, scale that `size` term up hard, and the sprite blows out the
frame. Cut there. The `vibrate` token even shakes the camera into the cut for free —
and per `README-wolfcam.txt:1230`, vibration is recorded into and replayed from
camera points **[SRC]**, so it's deterministic. This is one `.fx` variant plus a
close camera point. Hours, not days.

**Variant (b) — scene B revealed *through* the explosion's shape.**
This is a matte/luma-key composite, and the good news is that the matte machinery is
designed in, not improvised: **[SRC]**

- the FX language has a per-element **`stencil`** render flag, backed by q3mme's
  `RF_STENCIL` — *"Stencil whatever is outputted from this model"* (§1.1);
- `mme_saveStencil` writes that stencil out as a separate stream;
- `mme_saveDepth` and `mme_skykey` give two more independent matte sources.

So: tag the explosion sprite `stencil`, capture, and the engine hands you a clean
alpha for exactly that element — then `alphamerge`/`maskedmerge` the two scene
captures in FFmpeg. **[ASSESS]**

**The one gotcha**: per the §1.6 caveat, `mme_saveStencil` is commented out in the
WolfcamQL port of `tr_mme.c` (L381) even though the `stencil` render flag survives
on the FX side. Enabling it is a one-line change plus a rebuild. Until then, fall
back to `mme_skykey`/`mme_worldShader` chroma-keying, or capture the explosion
element as a separate pass against a keyed background. **[ASSESS]**

Either way this is FFmpeg work in a pipeline that is already an FFmpeg pipeline
(P1-BB, P1-H). It is *not* a renderer change. Scope it as a follow-on to (a), only
if (a) proves the shot lands.

**What I would NOT build**: a literal in-engine portal that renders scene B through
the explosion silhouette. That requires stencil-portal or RTT machinery that does
not exist in this tree (§1.7), gives a result the audience cannot distinguish from
variant (b), and would be weeks of renderer work. **[ASSESS]**

---

## 4. Summary table — transitions

| Primitive | New rendering? | Engine work | Tooling work | Wow | Verdict |
|---|---|---|---|---|---|
| **Teleporter pass** | None | None (one `.fx` tweak) | `.cam10` writer | High | **Build first** |
| **Impact portal (a)** | None | One `.fx` variant | `.cam10` writer | High | **Build first** |
| **Projectile bridge** | None | None | `.cam10` writer + trajectory solver | Very high | Build second |
| **Impact portal (b)** | None | None | FFmpeg matte composite | High | Follow-on to (a) |
| **Geometry match** | None | None | Shape library (manual) | Medium-high | Build when curated |
| *Literal portal render* | **Yes, weeks** | Stencil/RTT | — | Same as (b) | **Do not build** |

---

## 5. Impact FX (spec §30) — particle/shader vs. new render pass

The eight requested effects. **Seven of the eight are pure FX-script work with zero
new rendering.** The eighth is the one that genuinely needs a render pass, and it
isn't on the list by that name — it's hiding inside "energy ripple" if you interpret
it as heat-haze.

| # | Effect | Mechanism | New render pass? | Cost |
|---|---|---|---|---|
| 1 | **Beam accent** (rail) | `beam` + `rings` + spiral via `repeat`/`rotatearound`/`perpendicular` | No | **Trivial** |
| 2 | **Impact flare** | `sprite` + flare shader + `colorFade`/`alphaFade` emitter | No | **Trivial** |
| 3 | **Energy ripple** | `quad` (surface-aligned) or `dirModel` on `ring02.md3`, radius driven by `lerp` | No | **Trivial** |
| 4 | **Shockwave** | as #3, larger, + `vibrate` for camera shake | No | **Trivial** |
| 5 | **Debris** | `repeat` + `modellist` + `moveGravity` + `moveBounce` + `impact{}` + `sink` | No | **Low** |
| 6 | **Light pulse** | `light` with `size` driven by `clip(2-2*lerp)` | No | **Trivial** |
| 7 | **Arc enhancement** (LG) | multiple `beam` at stepped `angle`, endpoints jittered via `wobble`/`trace` | No | **Low** |
| 8 | **Bounce sparks** | `spark` primitive + `moveBounce` + nested `impact{}` | No | **Trivial** |
| — | *Heat haze / refraction* | *framebuffer sampling* | **YES** | **High — Agent A dependency** |

### 5.1 Why I'm confident these are trivial — they're already demonstrated

Every mechanism above appears in scripts that **already ship in this repo**. This
isn't extrapolation.

**Beam accent + rings + spiral** — `q3mme.fx:715-778` **[SRC]** builds the rail trail
as a `railCore` `beam` inside a `colorFade` emitter, then `Rings` stepped by
`r_railSegmentLength`, then a full procedural helix: take beam length in `t0`,
`normalize dir`, `perpendicular dir v0`, `scale v0 v0 5`, then
`repeat (t0/5) { rotatearound v0 dir v1 t1; t1 t1+10.1; addScale v1 dir origin loop*t0; add parentOrigin origin origin; emitter … { Sprite } }`.
That is a parameterised spiral around an arbitrary beam. Every knob you'd want for a
"beam accent" is already exposed.

**Impact flare + debris-ish spray** — `base_weapons.fx:394-419` **[SRC]** does the LG
impact: `soundList` random pick, `decal`, then
`repeat 3 { wobble dir velocity 10+rand*20; scale velocity velocity 200+rand*50; emitter "0.6+rand*0.3" { moveGravity 300; colorFade 0.7; Sprite } }`.

**Energy ripple / expanding disc** — `q3mme.fx:696-714` **[SRC]** rail impact:
`rotate rand*360`, `shader railExplosion`, `model models/weaphits/ring02.md3`,
`emitter 0.6 { dirModel }`. The expanding-ring primitive is already an asset.

**Debris with collision** — `base_player.fx:95-144` **[SRC]** gib script:
`modellist` of 11 body parts, randomised `yaw/pitch/roll`, then
`emitter 5+rand*3 { sink 0.9 50; moveBounce 800 0.6; anglesModel; impact 50 { … decal alpha }; distance 20 { … } }`.
Swap the model list for debris chunks and you have weapon debris. Same script,
different assets.

**Arc enhancement** — `base_weapons.fx:366-390` **[SRC]** LG trail: `beam` with
`angle 45` (the beam is repeated every 45°), then a conditional
`if (t0 < 768) { … anglesModel crackle.md3 with random angles }` for the impact
crackle. Adding more stepped beams with wobbled endpoints is an edit, not a feature.

### 5.2 The genuine render-pass dependency

If "energy ripple" is meant as a *screen-space* ripple — the world visibly warping
around the blast — that cannot be done with Q3 shaders. The shader language deforms
geometry and animates texture coordinates but never samples the framebuffer (§1.7,
verified against `tr_shader.c`). **[SRC]**

The path if we want it: `renderergl2/tr_postprocess.c` already has FBO-based passes
(`RB_BokehBlur`, `RB_RadialBlur`, `RB_GaussianBlur`, `RB_SunRays`) and a `glsl/`
directory. A radial-displacement pass keyed to a screen-space centre + radius would
slot in beside `RB_RadialBlur`. **[ASSESS]** Whether that renderer is the one we
actually ship is **Agent A's finding, not mine** — flagged as a dependency, not
resolved here, and explicitly not blocking anything in §5.

**Cheap substitute that needs no render pass**: a large `quad` with an animated
`tcMod turb` shader placed at the blast, oriented at the camera. It's a fake — it
warps its own texture, not the scene behind it — but at 4–6 frames of screen time
during an explosion, at 60fps, under motion blur, I would expect it to read
correctly. Worth a spike before committing to renderer work. **[ASSESS]**

### 5.3 The trigger problem, and its native solution

An impact FX pack that fires on *every* rocket in a 12-minute Part is noise, not
cinema. We learned this the expensive way already — CLAUDE.md rule **P1-Q-AUTO**
records that effects gated on hand-written per-clip overrides simply never fired
(Part 4 had one `slow=` line across 120 clips).

The native gate: FX scripts read arbitrary cvars (§1.1), and camera points carry a
`command` string (§1.4). So: **[ASSESS]**

```
# in the .cam10, on the point one beat before the frag:
command "set pth_impact_boost 1"
# and on the point after:
command "set pth_impact_boost 0"
```

```
# in the .fx:
weapon/rocket/impact {
    ...
    if pth_impact_boost {
        size 900 * clip(2 - 2*lerp)
        vibrate 120
        ...
    }
}
```

The recipe generator writes both files. The effect fires exactly on the frags the
recipe chose and nowhere else, deterministically, with no hand-authored overrides
anywhere. This satisfies P1-Q-AUTO's "verify the trigger, not just the code" by
construction.

---

## 6. Player trails (spec §29)

**Verdict: the strongest single finding in this research. Native hooks exist, they
carry exactly the data an afterimage needs, and MD3 frame-based animation is not a
blocker. This is a `.fx` file, not an engine change.**

### 6.1 The classic technique

The standard motion-trail/afterimage across engines is "a character leaves behind
faded copies as it moves" — spawn N transparent duplicates at recent positions and
fade them out, whether via a particle system (UE5 Niagara), pooled sprite/mesh
clones (Unity), or framebuffer accumulation. **[WEB]** The mesh-clone variant is the
one that maps onto Q3.

### 6.2 The hooks exist, and they are a WolfcamQL addition

`player/head/trail`, `player/torso/trail`, `player/legs/trail` — plus
`player/flight` — are documented as Wolfcam additions not present in upstream q3mme
**[WEB — `README-wolfcam.txt`]**, registered at
`cg_fx_scripts.c:6961-6967` **[SRC]**, and commented-out example stubs ship in
`q3mme.fx:155-181` **[SRC]**.

### 6.3 What the hook actually hands the script — this is the decisive part

`G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_players.c:7134-7166`
**[SRC]**:

```c
if (*EffectScripts.playerTorsoTrail) {
    CG_ResetScriptVars();
    CG_CopyPlayerDataToScriptData(cent);
    ScriptVars.animFrame = torso.frame;
    VectorCopy(torso.axis[0], ScriptVars.axis[0]);
    VectorCopy(torso.axis[1], ScriptVars.axis[1]);
    VectorCopy(torso.axis[2], ScriptVars.axis[2]);
    VectorCopy(torso.origin, ScriptVars.origin);
    trap_R_GetModelName(torso.hModel, ScriptVars.model, sizeof(ScriptVars.model));
    VectorCopy(cent->lastTorsoIntervalPosition, ScriptVars.lastIntervalPosition);
    ScriptVars.lastIntervalTime = cent->lastTorsoIntervalTime;
    VectorCopy(cent->lastTorsoDistancePosition, ScriptVars.lastDistancePosition);
    ScriptVars.lastDistanceTime = cent->lastTorsoDistanceTime;
    CG_RunQ3mmeScript(EffectScripts.playerTorsoTrail, NULL);
    /* …state written back to cent… */
}
```

Four things matter here:

1. **`ScriptVars.animFrame = torso.frame`** — the live animation frame is passed in,
   and `cg_fx_scripts.c:3741` does `re->frame = ScriptVars.animFrame;` when the FX
   system builds a `refEntity_t` for a model render. **[SRC]** So an emitted ghost
   renders **in the same animation pose** as the player was in at emission. This is
   the thing I expected to be a blocker and it simply isn't — MD3's frame-based
   animation is handled.
2. **`ScriptVars.axis[0..2]`** — the full 3×3 orientation, consumed by the
   `axisModel` render command (`TOKEN_AXISMODEL`, `cg_fx_scripts.c:457,4435`).
   **[SRC]** Exact orientation, not just yaw.
3. **`trap_R_GetModelName(torso.hModel, …)`** — the ghost uses the player's *actual
   current model*, resolved at runtime. Works with any player model. **[SRC]**
4. **`lastIntervalPosition/Time` and `lastDistancePosition/Time` round-trip through
   `cent`** — per-entity persistent state, which is what makes `interval` and
   `distance` emission work correctly per player. **[SRC]**

### 6.4 The script, as I'd write it

**[ASSESS]** — untested, offered as the shape of the thing, not as working code:

```
player/torso/trail {
    if pth_ghost {
        interval 0.04 {
            emitter 0.35 {
                alphaFade 0
                axisModel
            }
        }
    }
}
```

`interval 0.04` → 25 ghosts/sec; `emitter 0.35` → each lives 350ms; `alphaFade 0` →
fades to nothing over its life. Net effect: a ~9-copy fading afterimage trailing the
player, correctly posed and oriented. Repeat for `head` and `legs` for a full body.

Variations worth trying:
- Set an explicit `shader` before `axisModel` for a solid-colour silhouette ghost
  (more stylised, reads better at speed) vs. `shaderClear` to keep the player's own
  skin (more "speed blur", subtler).
- Drive `alpha` off `1 - lerp` squared for a sharper falloff.
- Use `distance 24 { … }` instead of `interval` so trail density scales with *speed*
  rather than time — fast movement leaves more ghosts, standing still leaves none.
  This is almost certainly the better default. **[ASSESS]**
- Add the `wallhack` render flag (§1.1, backed by `RF_NODEPTH`) to make the ghosts
  visible *through* geometry. On a rail frag through a wall that is a genuinely
  striking shot — the victim's ghost trail readable through the architecture — and
  it costs one keyword. **[ASSESS]**

### 6.5 Do we need `player_snapshots` replay data for this?

**No — and that's good news.** The emitter approach captures positions *live during
demo playback*; each emitted ghost persists on its own. There is no need to look up
past positions, because the ghosts *are* the past positions, left behind. **[ASSESS]**

Where our replay data *is* needed is **deciding when the trail is on**. Per §5.3,
the recipe generator writes `command "set pth_ghost 1"` into the camera point at
frag-time minus ~0.8s and `0` after. `player_snapshots` tells the generator where
that moment is. That's the integration point — scoring and timing, not geometry.

### 6.6 Caveats

- Three hooks = three model parts. A full-body ghost needs all three scripted, and
  they must use matching `interval`/`life` or the parts will separate visibly. **[ASSESS]**
- Cost scales as `players × (life / interval)`. At 25/s × 0.35s × 8 players that's
  ~70 extra model draws — fine for offline capture, and we are always offline. **[ASSESS]**
- **Throttle cvars will clamp the trail and must be checked first.** WolfcamQL
  registers `cg_fxinterval`, `cg_fxratio`, `cg_fxScriptMinEmitter`,
  `cg_fxScriptMinDistance` and `cg_fxScriptMinInterval` (`cg_main.c:2391-2399`)
  **[SRC]**. Community sources put `cg_fxinterval` at 50ms and `cg_fxratio` at 0.002
  by default **[WEB]**. A 40ms trail interval sits *under* a 50ms script-run
  interval, and `cg_fxScriptMinInterval` may floor it outright. Set these explicitly
  in the capture cfg rather than assuming defaults.
- `cullDistance` / `cullDistanceValue` exist to drop distant FX entities
  **[WEB — `README-wolfcam.txt`]**; may need tuning so ghosts don't vanish at range.
- The wolfcamql `FIXME` file reportedly contains a known issue about player trail
  scripts and null models **[WEB]**. Worth reading before building — flagged, not
  investigated.

---

## 7. Prioritised build list — wow-factor per engineering cost

Ranked. Cost is my estimate of engineering effort, not calendar time. **[ASSESS
throughout]**

### Tier 1 — build these first

| # | Build | Cost | Wow | Why it's first |
|---|---|---|---|---|
| **1** | **Player ghost trail** (§6) | **XS** — one `.fx` file, three blocks | **Very high** | Hooks verified to carry origin+axis+animFrame+model. No C. No new assets. Nothing else in this document has a better ratio. |
| **2** | **`.cam10` writer** (§1.5) | **S** — one Python module | *(enabler)* | Not a visible feature, but §3.1/3.2/3.3/5.3 all depend on it. Plain-text format fully mapped. Build it once, unlock four transitions. |
| **3** | **Teleporter pass transition** (§3.2) | **S** — given #2 | **Very high** | Pure match cut. Teleport FX already ship. `/runfxat` means it works on any map, teleporter or not. |

### Tier 2 — build once Tier 1 lands

| # | Build | Cost | Wow | Notes |
|---|---|---|---|---|
| 4 | **Impact FX pack** (§5 items 1–4, 6) | **S** | High | Every mechanism already demonstrated in shipped scripts. Mostly parameter work. |
| 5 | **Impact portal (a)** — explosion fills frame (§3.4) | **XS** given #2 | High | One `.fx` variant + a close camera point. `vibrate` shakes into the cut for free. |
| 6 | **Cvar gating via camera-point `command`** (§5.3) | **XS** | *(enabler)* | The P1-Q-AUTO fix, done natively. Do this alongside #4/#5 or they'll fire on everything. |
| 7 | **Projectile bridge** (§3.1) | **M** — trajectory solver + path shaping | **Very high** | Highest wow of the transitions, but needs the missile trajectory→camera-path component. Worth it. |

### Tier 3 — worthwhile, later

| # | Build | Cost | Wow | Notes |
|---|---|---|---|---|
| 8 | **Debris + bounce sparks** (§5 items 5, 8) | S–M | Medium | Gib script is the template; needs debris model assets. |
| 9 | **LG arc enhancement** (§5 item 7) | S | Medium | Reads well only in close/slow shots. |
| 10 | **Impact portal (b)** — matte composite (§3.4) | M | High | FFmpeg work, not renderer work. The FX `stencil` render flag + `mme_saveStencil` supply a clean per-element matte — but `mme_saveStencil` is commented out in the Wolfcam port (§1.6), so budget a 1-line change + rebuild. Only after (a) proves the shot. |
| 11 | **Geometry match library** (§3.3) | M (manual curation) | Medium-high | Free technically; cost is entirely in finding good pairs. Start with ~20 hand-picked framings. |

### Tier 4 — needs a decision we don't own

| # | Build | Cost | Notes |
|---|---|---|---|
| 12 | **Screen-space heat haze / refraction** (§5.2) | **High** | Genuinely requires a new render pass. `renderergl2/tr_postprocess.c` is the hook point. **Blocked on Agent A's renderer findings.** Try the `tcMod turb` fake (§5.2) first — it may be indistinguishable at 4 frames under motion blur. |
| 13 | **Literal portal rendering** | Very high | **Recommend against.** Variant (b) is visually equivalent for our shots at a fraction of the cost. |

---

## 8. Open questions and dependencies

1. **Agent A (renderer)** — is `renderergl2` the renderer we actually ship, or
   `renderer` (GL1)? Everything in Tier 4 hinges on this. Nothing in Tiers 1–3 does.
2. **Agent B (FX hook depth)** — my §1 inventory is from the parse table and shipped
   scripts. If B finds constraints on `CG_RunQ3mmeScript` (recursion limits, entity
   caps, `cg_fxinterval`/`cg_fxratio` throttling) that would tighten §6.6's cost
   estimate.
3. **FX throttle cvars** — `cg_fxinterval`, `cg_fxratio`, `cg_fxScriptMinEmitter`,
   `cg_fxScriptMinDistance`, `cg_fxScriptMinInterval` (`cg_main.c:2391-2399`)
   **[SRC]**, defaults reported as 50ms / 0.002 **[WEB]**. Directly clamps §6.4's
   proposed 40ms ghost interval. **Resolve before building #1** — it's a cfg line if
   the clamps are cvar-settable, a rebuild if they're hard floors.
3b. **Should we run the WolfcamQL cgame interpreter or the q3mme engine VM?** The
   two implementations differ materially: q3mme compiles `.fx` to a bytecode opcode
   stream in the client (`_forks\q3mme\trunk\code\client\fx_parse.c` + `fx_main.c`)
   and exposes it to cgame via `trap_FX_Run`; WolfcamQL reimplements it as a
   string-walking interpreter inside cgame (`cg_fx_scripts.c:4050`) with an optional
   per-token JIT cache behind `cg_fxCompiled`. **[SRC]** WolfcamQL's token set is
   substantially larger (`t0..t9`/`v0..v9` vs `t0..t3`/`v0..v3`, plus `cross`,
   `rings`, `trace`, `command`, `animframe`, `return`/`continue`, the `pw*` powerup
   predicates, `clientnum`/`enemy`/`teammate`/`ineyes`/`surfacetype`/`gametype`) —
   but q3mme has `mme_saveStencil` wired and a demo-keyframe FX editor WolfcamQL
   lacks (see #7). **This choice gates §5.3 and §3.4 and is not mine to make.**
3c. **q3mme's demo module is a second, independent trigger surface.** It has
   `demo camera` with add/del/lock/target/shift/pos/angles/fov subcommands, bezier
   and linear interpolation, plus `demo effect` / `demo script` edit modes that
   attach an FX script to a demo keyframe and fire it via
   `trap_FX_Run(parent->script, …)` (`cg_demos_effects.c:641`). **[SRC]** If we end
   up on q3mme rather than WolfcamQL, §5.3's cvar-gating trick is replaced by
   something cleaner and native. Worth knowing before committing to the cvar approach.
4. **wolfcamql `FIXME`** — reported known issue re: player trail scripts + null
   models **[WEB]**. Read before building #1.
5. **Camera framerate coupling** — `README-wolfcam.txt:1240-1249` **[SRC]**: camera
   paths are framerate-sensitive and blur frames multiply effective fps. Generated
   `.cam10` files must be authored against capture settings. Affects everything in
   Tier 1–2.
6. **`.cam10` version drift** — format is version 10 and the loader falls back to
   version 9 (`cg_consolecmds.c:2427-2429`) **[SRC]**. Pin the writer to 10 and
   assert the header on load.

---

## 9. Sources

**Primary — this repository (verified first-hand)**

- `G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_fx_scripts.c` — FX token
  parse table (`fxTokens[]`, L341-560), `animFrame`→`refEntity` (L3741),
  `TOKEN_AXISMODEL` (L457, L4435), script-hook registration (L6884-6990)
- `G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_players.c` — trail hook
  dispatch and ScriptVars population (L7042-7071 legs, L7134-7166 torso, L7521-7544 head)
- `G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_camera.h` — `cameraPoint_t`,
  camera/angle/roll/fov/offset enums, `CEF_COMMAND`, `WOLFCAM_CAMERA_VERSION 10`
- `G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_consolecmds.c` — `.cam10`
  text writer (L2255-2333), loader + v9 fallback (L2427-2429), `/runfx` dispatch (L7652)
- `G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_event.c` — teleport/jumppad/
  headshot script dispatch (L1997, L2454-2471, L3850)
- `G:\QUAKE_LEGACY\engine\engines\_canonical\code\renderer\tr_shader.c` — shader keyword
  tables; `deformVertexes` subtypes (L1182-1189), `tcMod`/`turb` (L367, L1059)
- `G:\QUAKE_LEGACY\engine\engines\_canonical\code\renderergl2\tr_postprocess.c` +
  `glsl/` — existing FBO post passes
- `G:\QUAKE_LEGACY\engine\engines\_canonical\trunk\files\fxScript.txt` — shipped FX doc
  (v0.001, incomplete — see §1.1)
- `G:\QUAKE_LEGACY\engine\engines\_canonical\trunk\files\scripts\base_weapons.fx`,
  `base_player.fx` — reference FX scripts
- `G:\QUAKE_LEGACY\engine\engines\_canonical\package-files\wolfcam-ql\scripts\q3mme.fx`
  — WolfcamQL reference FX scripts incl. rail spiral and player-trail stubs
- `G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_fx_scripts.h` — `ScriptVars_t`
  render flags incl. `stencil` / `wallhack` / `depthHack` / `cullRadius` (L109-118),
  `effectScripts_t` (L214-271)
- `G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_main.c:2391-2399` — FX
  throttle cvars (`cg_fxinterval`, `cg_fxratio`, `cg_fxScriptMin*`, `cg_fxCompiled`)
- `G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_particles.c` — the separate,
  non-scriptable legacy particle system (see §1.7)
- `G:\QUAKE_LEGACY\engine\engines\_canonical\code\renderercommon\tr_mme.c:367-382` —
  WolfcamQL mme cvar registration; **`mme_saveStencil` commented out at L381**
- `G:\QUAKE_LEGACY\engine\engines\_canonical\README-wolfcam.txt` — camera system,
  `/ecam` reference, fx additions, capture notes

**Primary — q3mme fork in this repo** (`G:\QUAKE_LEGACY\engine\engines\_forks\q3mme\trunk\`)

- `code\client\fx_parse.c` / `fx_main.c` / `fx_local.h` — the *engine-side* FX
  compiler + VM (`fxCommand_t` opcodes; keyword dispatch `fx_parse.c:1288-1970`;
  `.fx` discovery at L2105)
- `code\cgame\tr_types.h:41-43` — `RF_STENCIL`, `RF_CULLRADIUS`, `RF_NODEPTH`
  (q3mme additions over stock Q3)
- `code\renderer\tr_mme.c:814-851` — full mme cvar block incl. working
  `mme_saveStencil` (L847) / `mme_saveDepth` (L848)
- `code\cgame\cg_demos*.c` — demo camera/keyframe system, `demo camera|effect|script|
  dof|cut` edit modes, FX-on-keyframe via `cg_demos_effects.c:641`

**Web**

- [q3mme — Quake 3 Movie Maker's Edition (entdark)](https://github.com/entdark/q3mme)
- [q3mme `cvars.txt`](https://github.com/entdark/q3mme/blob/master/cvars.txt) — mme
  blur / DOF / saveDepth / saveStencil / skykey / worldShader
- [q3mme `cmds.txt`](https://github.com/entdark/q3mme/blob/master/cmds.txt)
- [wolfcamql — `README-wolfcam.txt` (brugal)](https://github.com/brugal/wolfcamql/blob/master/README-wolfcam.txt)
- [wolfcamql — `q3mme.fx`](https://github.com/brugal/wolfcamql/blob/master/package-files/wolfcam-ql/scripts/q3mme.fx)
- [wolfcamql — `FIXME`](https://github.com/brugal/wolfcamql/blob/master/FIXME)
- [ESR — Jump Cuts in Wolfcam](http://www.esreality.com/post/2485795/re-jump-cuts-in-wolfcam) — camera type semantics, jump-cut setup
- [ESR — WolfcamQL Complete Tutorial](https://www.esreality.com/post/2525022/wolfcamql-complete-tutorial/)
- [Quake III Arena Shader Manual — General Shader Keywords](https://icculus.org/gtkradiant/documentation/Q3AShader_Manual/ch02/pg2_1.htm)
- [Quake III Arena Shader Manual (PDF, Stanford mirror)](https://graphics.stanford.edu/courses/cs448-00-spring/q3ashader_manual.pdf)
- [Match cut — Wikipedia](https://en.wikipedia.org/wiki/Match_cut)
- [The Whip Pan Shot in Film — StudioBinder](https://www.studiobinder.com/camera-shots/camera-movements/whip-pan-shot/)
- [3 Creative In-Camera Transitions — Motion Array](https://motionarray.com/learn/filmmaking/in-camera-transitions/) — invisible cut
- [How to Do a Whip Pan — NoFilmSchool](https://nofilmschool.com/how-to-do-a-whip-pan)
- [High-Performance Play: The Making of Machinima — Henry Lowood (Stanford)](https://web.stanford.edu/~lowood/Texts/highperformanceplay_finaldraft.pdf) — recamming
- [Quake done Quick — Wikipedia](https://en.wikipedia.org/wiki/Quake_done_Quick)
- [Quad God — Wikipedia](https://en.wikipedia.org/wiki/Quad_God_(film))
- [Portals Part 2: Stencil-based Portals — Daniel Ilett](https://danielilett.com/2019-12-14-tut4-2-portal-rendering/)
- [Portals and effects in OpenGL — GameDev.net](https://gamedev.net/forums/topic/404473-portals-and-effects-in-opengl-like-prey/3687430/)
- [Customizable Afterimage VFX in Unreal Engine 5 — 80.lv](https://80.lv/articles/creating-versatile-afterimage-vfx-with-unreal-engine-5-s-niagara)
- [How To Enable The Q3MME FX Script Included With Wolfcam](https://qlff.board-directory.net/t1-how-to-enable-the-q3mme-fx-script-included-with-wolfcam-and-start-editing-it)
