# XRAY — the engine already does it

**Status: the overlay is VISUALLY PROVEN. The through-wall case is not yet.**

## What was found

`cg_wh` re-adds each player's legs, torso and head as an extra pass with a
custom shader, `shaderRGBA` from `cg_whColor`/`cg_whAlpha`, and
`renderfx |= RF_DEPTHHACK`. The wall keeps rendering; the silhouette
composites over it. That is the requested effect, and it ships.

`RF_DEPTHHACK` remaps the entity into `glDepthRange(0, 0.3)` with a projection
matrix that differs from the normal one **only in the Z row**, so the overlay
lands pixel-exact on the player's real screen position. It does not move
anything.

Modes: `1` all players, `2` enemies only, `3` non-enemies only. All nine cvars
are plain `CVAR_ARCHIVE` — no cheat gate, no latch, settable mid-demo.

## Evidence

| Claim | Grade | How |
|---|---|---|
| `cg_wh` is registered in the binary we run | **C** | `cg_wh` ×45, `cg_whShader`/`cg_whEnemyShader`/`cg_whColor`/`cg_whAlpha` ×5 each in the shipped `cgamex86.dll`. Control: `cg_drawSpeedometer` ×0 — the same scan that caught the last silent no-op. |
| `wc/wallhack` shader is on disk | **C** | `_wolfcam_staging/wolfcam-ql/scripts/wcmisc.shader:141`, `blendFunc GL_SRC_ALPHA GL_ONE_MINUS_SRC_ALPHA`, `rgbGen entity`, `alphaGen entity` |
| **The overlay actually draws** | **E** | A/B capture of `ca_explainer_v1` at t=12 s, identical demo, seek and camera, `cg_wh 0` vs `cg_wh 1`. Saturated-red pixels **19,360 → 34,711 (x1.8)**; 10 new red pixels appear in a far-background band that has zero without it. Frames: `docs/visual-record/2026-09-05/cg_wh_ab_overlay_proof.png` |
| The overlay colour is driveable | **E** | `cg_whEnemyColor "255 40 40"` at alpha 200: max red-excess 132, 10,232 px. Frames: `cg_wh_colour_proof.png` |
| A player *behind geometry* shows through | **NOT PROVEN** | No frame yet has a definitively occluded player. This is the remaining gate. |

## The colour format — derived from source, then confirmed on pixels

`cg_whColor "0x00ff00"` produced nothing, and the reason is in
`SC_ParseColorFromStr` (`sc_misc.c:24`): it **rejects any character that is not
a space or a digit 0-9**, prints `invalid color string`, and returns -1. Hex is
not a supported syntax. Note the cvar table's own default, `"0xffffff"`
(`cg_main.c:2079`), is itself unparseable.

**The syntax is space-separated decimal RGB: `"255 40 40"`.** Confirmed on
frames: max red-excess 132, 10,232 pixels above threshold, against zero in the
baseline.

**Which cvar depends on the branch.** `cg_players.c:4335-4352` splits on
`CG_IsEnemyTeam(team)`:

| the player is | colour cvar | alpha cvar | shader cvar |
|---|---|---|---|
| an enemy | `cg_whEnemyColor` | `cg_whEnemyAlpha` | `cg_whEnemyShader` |
| anything else | `cg_whColor` | `cg_whAlpha` | `cg_whShader` |

Setting `cg_whColor` while the actors resolve as enemies changes nothing, which
is exactly the dead end this cost. All four are registered in the shipped 11.3
DLL (5 hits each). Alpha default is **30** -- nearly transparent -- so a first
attempt with default alpha reads as "not working".

**A raw pixel-difference count proves nothing here.** The A/B frames differ by
up to 72,000 pixels at other timestamps purely from playback jitter — Wolfcam
is not frame-deterministic across launches. The x1.8 saturated-red measurement
is the evidence; the bulk diff is noise.

## Route

Use `cg_wh`. Do **not** build the multi-pass composite
(`THROUGH_WALL - VISIBLE`) that was previously planned: the cgame does this in
one pass, and the composite would be paying multi-pass cost for it.

`render_profile.py` grades `WALL_XRAY` as `FUTURE_BACKEND` requiring surface
suppression. That is an accurate read of *wall removal*, which does not exist —
but the brief asks for a silhouette **with the wall still visible**, which is an
overlay, and the overlay ships.

## Caveats for whoever wires it in

1. **PVS is a hard ceiling.** `cg.refdef.areamask` is copied unconditionally
   from the recorder's snapshot with no override, and a player the recording
   client never received is not in the demo at all. XRAY only works on players
   the demo-taker's server was already sending. For a SYNTHETIC round this is
   moot — we send every entity ourselves.
2. **Enemy/teammate split is meaningless outside team games.** `CG_IsEnemyTeam`
   returns true for everyone when the gametype is not a team game, so `cg_wh 2`
   in a duel is `cg_wh 1`.
3. **Body only.** The overlay covers legs/torso/head and missiles. The held
   weapon goes through a different path and gets no treatment.
4. **Version gap.** The source describing the behaviour is 12.7test49; the
   binary is 11.3. The cvar names are confirmed in 11.3; the exact mode
   semantics are grade B.
