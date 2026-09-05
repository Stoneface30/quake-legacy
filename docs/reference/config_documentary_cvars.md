# Configuration documentary — what the FILMED BINARY actually has

Runtime verification, 2026-09-05. This closes the "runtime `cvarlist` remains
pending" item left open by `2026-09-05-wolfcam-command-verification.md`.

**Method.** `python -m engine.pantheon.cvar_probe` launches the staged
WolfcamQL **11.3** binary on a demo, and from inside `cgamepostinit` (so the
cgame VM is loaded and `cg_*` exists at all) runs `cvarlist <wildcard>` for 51
families, then `condump`. `Cvar_List_f` prints nine fixed flag columns —
`S s U R I A L C ?` (`qcommon/cvar.c:1066-1110`) — so the dump carries not just
which names exist but **whether a name is latched, a cheat, or a ghost**.

Machine-readable result: `engine_cvarlist_11_3.json` — 180 distinct cvars.

> The standing project lesson applies to everything below: a registration is
> not a behaviour. This document says what the binary *has*. What each one
> *does to pixels* is a separate proof, and where that proof has not been run
> the row says so.

---

## 1. Names the brief assumed that DO NOT EXIST

These are registered in the canonical **12.7test49** source tree and are absent
from the 11.3 binary we film with. `ab_scene.CvarInventory.check()` refuses
them, so no scene can name one by accident.

| Name | Status | Consequence |
|---|---|---|
| `cg_forceEnemyModel` | not registered | The brief's Scene 03 line. The real route is `cg_enemyModel` + `cg_forceModel`. |
| `cg_useCustomRedBlueRail` | not registered | **Removes a scene design.** Absolute "red team rails are always red" is not available. |
| `cg_redTeamRailColor1` / `2` | not registered | idem |
| `cg_blueTeamRailColor1` / `2` | not registered | idem |
| `cg_useCustomRedBlueModels` | **USER_CREATED** | Present in an archived config, registered by nothing. Setting it is a silent no-op. |
| `cl_aviPipeCommand`, `cl_aviPipeExtension`, `cl_aviFrameRateDivider` | **USER_CREATED** | Same. Anything relying on a pipe-encode capture path is relying on nothing. |

**What this costs Scene 05.** Rail allegiance can only be expressed
*relative to the point of view*: `cg_teamRailColor*` / `cg_enemyRailColor*`
resolve against the POV client's team, not against absolute red/blue. A
spectating camera therefore has to have a team resolved for it, and
`cg_freecam_useTeamSettings` (`2`, ARCHIVE) is the switch that decides whether
it does. **Unproven — needs a frame.**

## 2. LATCHED — a value stored now and applied at `vid_restart`

Setting any of these mid-capture changes the stored value and **nothing on
screen**. A film that fires `set r_picmip 8` at t=5s and shows no change is not
evidence that picmip does nothing; it is evidence that the scene was built
wrong. This is why `ConfigScene` films **one capture per variant**.

`r_picmip`, `r_picmipGreyScale`, `r_picmipGreyScaleValue`, `r_vertexLight`,
`r_mapOverBrightBits`, `r_mapOverBrightBitsCap`, `r_mapOverBrightBitsValue`,
`r_overBrightBits`, `r_overBrightBitsValue`, `r_intensity`, `r_lightmapColor`,
`r_detailtextures`, `r_ext_compressed_textures`, `r_subdivisions`,
`r_swapInterval`.

That covers Scene 01 (picmip), Scene 12 (world lighting) and Scene 13 (map vs
enemy brightness) — every one of them needs separate captures.

`r_picmip` is `Cvar_CheckRange(0, 16, integer)` (`renderergl1/tr_init.c:1810`),
default `0`. Values above 16 are clamped, not rejected.

## 3. Live — safe to vary between captures, and legal to vary within one

All ARCHIVE, none latched:

- **Gun:** `cg_drawGun`
- **Sky:** `r_fastsky`, `r_fastSkyColor`
- **Identity:** `cg_forceModel`, `cg_enemyModel`, `cg_enemyHeadModel`,
  `cg_enemy{Legs,Torso,Head}Skin`, `cg_enemy{Legs,Torso,Head}Color`, and the
  same eleven names again as `cg_team*`
- **Rails:** `cg_railUseOwnColors`, `cg_team{RailColor1,RailColor2}`,
  `cg_enemy{RailColor1,RailColor2}`, `*RailColor1Team` / `*RailColor2Team`,
  `cg_railItemColor`, `cg_teamRailItemColor`, `cg_enemyRailItemColor`,
  `cg_railRings`, `cg_railRadius`, `cg_railSpacing`, `cg_railTrailTime`,
  `cg_railQL`, `cg_railFromMuzzle`, `cg_railNudge`

### `cg_railUseOwnColors` is the chaos lever

From `cg_weapons.c:620-684`, a rail's colour starts as the FIRING PLAYER's own
`ci->color1` / `color2` — their userinfo `c1`/`c2`. That is the heterogeneous
"before" the documentary needs, and it is the default. The forced team/enemy
colours are applied only when `checkTeammateSettings` is true, which it is for
any player who is not the POV client, and — in freecam — when
`cg_freecam_useTeamSettings` is non-zero.

So the Scene 05 ladder that this binary supports is:

1. every player's own `c1`/`c2` (chaotic),
2. `cg_teamRailColor1/2` set (friendly rails unify),
3. `cg_enemyRailColor1/2` set (hostile rails unify).

## 4. The one thing that must be measured before ANY colour is named

**The colour string format is unresolved, and the source says two incompatible
things.**

- `cg_whColor` goes through `SC_ParseColorFromStr`, which rejects any character
  that is not a digit or a space (`sc_misc.c:44`) — so it takes
  `"40 255 40"`, decimal triples. This is already proven on frames.
- The rail colours go through `SC_Vec3ColorFromCvar` →
  `SC_RedFromCvar`, which reads **`cvar->integer`** (`sc_misc.c:192-202`) and
  masks it as `0xRRGGBB`. `Cvar_Set` computes that integer with plain
  `atoi(var->string)` (`qcommon/cvar.c:468`), and `atoi("0x2a8000")` is **0**.
- Yet `cg_enemyLegsColor` **ships with the default `"0x2a8000"`**.

Those three facts cannot all be true of one code path. Reading further source
to decide which is wrong is exactly the move that has been wrong three times on
this project. **PROOF 0 (colour format)** therefore comes before Proof B and
Proof C: one scene, one rail, four variants — `"0x2a8000"`, `"2752512"`,
`"42 128 0"`, unset — measured as mean RGB inside the rail trail. Whichever
form moves the pixels is the form the documentary is allowed to show.

---

## Consequences for the three requested proofs

| Proof | Verdict | Blocking work |
|---|---|---|
| **A — picmip** | Buildable now. `r_picmip` exists, range 0-16, latched → one capture per value. | none |
| **B — enemy/team models** | Buildable, with `cg_enemyModel` + `cg_forceModel`, **not** `cg_forceEnemyModel`. | Colour half needs PROOF 0. |
| **C — rail team fight** | Buildable only in the **relative** form. The absolute red/blue design in the brief is unavailable in this binary. | PROOF 0, plus a frame proof that a spectating camera resolves team at all. |

Reproduce the inventory: `python -m engine.pantheon.cvar_probe`.

---

# PROOF 0 — CLOSED. The colour format, decided on pixels.

Five variants, one rail, one camera, one timestamp, one demo replayed.
`overkill`, top floor (z=936), 439-unit beam filmed broadside from 186 units
off-axis. Stills: `docs/visual-record/2026-09-05/proof0/`.
Measurements: `.tmp/shots/proof0/measurements.json`.

**Method.** For each capture, a frame at +0.3s (no rail yet) and a frame at
+0.9s (trail is up, `cg_railTrailTime` 600) come straight out of the AVI as raw
RGB24 — no lossy round trip. Pixels differing by more than 60 (sum of channel
deltas) are the beam; the brightest quarter of them is the beam's core, since a
rail has a hot centre and a halo that blends with the wall behind it. Both
frames come from the SAME capture, because wolfcam is not frame-deterministic
across launches and a diff between two captures measures jitter.

| variant | value | pixels | core median RGB | predicted | verdict |
|---|---|---:|---|---|---|
| hex | `0x2a8000` | 7865 | **(44, 110, 6)** | (42,128,0) | **GREEN** |
| decimal_int | `2785280` | 7914 | **(67, 106, 7)** | (42,128,0) | **GREEN** |
| decimal_int_wrong | `2752512` | 1380 | (157, 111, 97) | (42,0,0) | beam collapses |
| decimal_triple | `"42 128 0"` | 1364 | (157, 112, 98) | (0,0,42) | beam collapses |
| unset | `""` | 10006 | (226, 4, 5) | — | shooter's own c1 |

**Answers to the six questions asked:**

1. **Which syntax modifies the rail?** The packed integer. `0x2a8000` and its
   decimal equal `2785280` both render green.
2. **What RGB does each input produce?** The value, read as `0xRRGGBB`.
3. **Does hex work despite the `atoi` concern?** **Yes.** `Cvar_Set` computes
   `var->integer` with plain `atoi`, and `atoi("0x2a8000")` is 0 in C — the
   frame says otherwise, and per the standing rule the film follows runtime.
4. **Does decimal map predictably?** Yes, and the proof caught my own
   arithmetic error doing it: the first run used `2752512`, which is
   `0x2a0000`, not `0x2a8000`. It rendered a near-black beam — exactly what
   `0xRRGGBB` predicts for (42,0,0). A wrong number producing the *predicted
   wrong colour* is a second, independent confirmation of the model, so that
   variant is kept in the proof deliberately.
5. **Does a space-separated triple work here?** **No.** `"42 128 0"` reads as
   42 = `0x00002a` and collapses the beam to the same dim residual as the wrong
   decimal — 1364 pixels against 7865.
6. **Is the shipped default special-cased?** No special path is needed:
   `0x2a8000` is simply a value this parser reads correctly.

**DOCUMENTARY_COLOR_FORMAT = `0xRRGGBB` for the rail family.**
Enforced by `engine/pantheon/color_format.py::format_for`, which refuses any
cvar whose syntax has not been measured.

**The format is per-family, not global.** `cg_whColor` goes through
`SC_ParseColorFromStr`, which rejects any non-digit character, and takes
`"40 255 40"` — proven on frames in an earlier sprint. Two colour cvars in one
cgame, two incompatible syntaxes, and writing one in the other's form is
silent. The model colour family (`cg_enemyLegsColor` et al.) is recorded as
packed-int **by inference from its shipped default only**, and is flagged
`is_inferred` until PROOF B measures it.

## A second thing PROOF 0 settled by accident

The first run of this proof returned **the same colour for all four variants**.
The cvar was not reaching the rail at all: client 0, the point of view, had no
`CS_PLAYERS` configstring, therefore no team, therefore neither
`cg_teamRailColor*` nor `cg_enemyRailColor*` ever applied. Every
teammate/enemy decision in cgame reads `cgs.clientinfo[povClientNum]`.

`RoundScenario.observer()` now takes a team and the compiler writes that
configstring. **This is also most of the freecam question**: team relation is a
property of the POV client's configstring, so a followed-player POV resolves it
by construction. Proof C will use a followed POV and not depend on
`cg_freecam_useTeamSettings` at all.

---

# PROOF B — CLOSED. Who decides what a player looks like.

Four actors, one frame, three captures. `overkill` high floor band, clustered
so all four are mutually visible; camera, lighting, position and time are
shared by construction because the cells are ACTORS, not captures. Only the
global client cvars vary between captures.
Stills: `docs/visual-record/2026-09-05/proofb/`.

| cell | authored | client colours set | verdict |
|---|---|---|---|
| A1 `keel/bright` **teammate** | (203, 201, 163) | **(102, 225, 98)** | tinted by `cg_team*Color 0x00ff00` |
| A2 `keel/bright` **enemy** | (213, 185, 161) | **(251, 83, 249)** | tinted by `cg_enemy*Color 0xff00ff` |
| A3 `sarge/default` teammate | (153, 108, 66) | (153, 109, 66) | **untouched** |

**1. Tint authority is `cg_team*Color` / `cg_enemy*Color`, keyed on the
subject's TEAM RELATION to the point of view.** Not the model, not the demo's
`c1`/`c2`, not `cg_forceModel`.

**2. The tint reaches the `bright` skin family and not `sarge/default`.** A3
measured within one unit of itself across the cleared and set captures.

**3. That is why Keel rendered white in INSTRUCTION_LAYER_PROOF_01.** He was
BLUE, the same team as the POV, so `cg_teamLegsColor` applied — and it ships as
`0xffffff`. The hypothesis was reachable from the default value; it is now
measured.

**4. `0xRRGGBB` is confirmed for the model colour family too.** `format_for`
emitted `"0x00ff00"` and `"0xff00ff"` and both landed exactly. `color_format`
no longer flags any family as inferred.

**5. Forced model remains UNPROVEN, not disproven.** `cg_forceModel 1` +
`cg_enemyModel "keel/bright"` changed nothing on the cells measured — but the
only cell that could have shown it, A4 (enemy Sarge), sat too far right to
measure. Do not put that command on screen yet.

## The analysis look falls out of this

The analysis body is the **only** actor wearing a `bright` skin. The tint then
lands on it and on nothing else, so the explanatory copy is instantly separable
from the fight **without repainting the fight**. Historical actors keep exactly
what the demo authored. `instruction.analysis_visual_cvars()` writes the half
of the family that matches the body's team relation to the POV, because that is
what the engine classifies on.

## A capture trap PROOF B found

The first PROOF B run came out with capture 1 visibly darker than captures 2
and 3, at 39.9 MB against 48 MB. The exposure cvars are **LATCHED**: set from
`capture.cfg` they are stored, archived to `q3config.cfg`, and read at the
**next** startup. So run N filmed at the old value and run N+1 at the new one —
consecutive captures differing by a variable nobody declared, which is the one
thing a controlled A/B cannot survive.

`shot.render` now splits the profile against the runtime inventory and sends
every latched cvar to the **command line**, where `Com_StartupVariable` applies
it before the renderer initialises. After the fix the three captures came out
at 86.8 / 87.5 / 87.0 MB.
