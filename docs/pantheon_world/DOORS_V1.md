# THE PANTHEON DOORS — v1 design

The signature reusable asset: the way into the PANTHEON, and later a
transition primitive (`PANTHEON_DOOR_TRANSITION`).

## The colours, taken from the engine rather than assumed

The director's colours are Quake's own `^4` and `^7`. In **Quake Live**'s
table (`g_color_table_ql`, `code/qcommon/q_math.c`) those are:

| code | RGB (float) | hex | role |
|---|---|---|---|
| `^4` | 0.196, 0.400, 0.996 | **`#3266FE`** | PANTHEON blue — emissives, glyph, light strips |
| `^7` | 0.996, 0.996, 0.996 | **`#FEFEFE`** | PANTHEON white — inlay, edge light, typography |

Note `^4` is **not** pure `#0000FF`; that is the Quake 3 table
(`g_color_table_q3`). We are a Quake Live project, so `#3266FE` is the blue.
Neutral ground: dark stone and dark metal. Gold is retired for the world
modules — `docs/brand/pantheon-mark.svg` is currently gold `#e8b923` and needs
a recolour, not a redesign.

## The mark

`docs/brand/pantheon-mark.svg` is the visual authority: a temple pediment over
five columns on a stylobate. The door glyph is that mark, cut into the leaves
so the pediment spans both and splits when they open. Also present:
`creative_suite/frontend/icons/pantheon.svg` (`#i-ped`, the same pediment as a
UI symbol).

*Open question for the director: if there is another set of PANTHEON images
from Claude Design, point me at it — the only marks in the repo are these two,
and the design-contractor export folder holds unrelated screenshots.*

## Geometry (Quake units — a player is 56 tall, eye at 26)

| element | size | why |
|---|---|---|
| doorway opening | 256 W × 384 H | monumental: 6.8× a player's height. A 128×256 door reads as a corridor door |
| leaf | 128 W × 384 H × 24 D | two leaves, centre parting |
| frame / architrave | +48 all round | gives the pediment somewhere to sit |
| pediment above | 352 W × 96 H | the mark, spanning both leaves |
| glyph inlay depth | 4 | shallow — `^4` emissive shader in the recess |

## The real Quake door mechanism — quoted, not guessed

`code/game/g_mover.c`, `SP_func_door`, WolfcamQL 11.3:

* defaults: `speed 400`, `wait 2` (seconds → ms), `lip 8`, `dmg 2`
* `pos1` = spawn origin; `pos2 = pos1 + movedir × (dot(|movedir|, size) − lip)`
* `angle` / `angles` set `movedir` via `G_SetMovedir`
* `START_OPEN` (spawnflag 1) swaps pos1 and pos2
* motion is set by `SetMoverState`: `trTime = time`,
  `trDelta = delta × 1000/trDuration`, **`trType = TR_LINEAR_STOP`**

That last line matters: a door is a brush model on the *same* trajectory type
PANTHEON already evaluates for missiles. We do not need to invent door motion;
we need to evaluate a trajectory we already honour.

## Which mover the game actually has — checked, not assumed

`g_mover.c` of the banked 11.3 source spawns exactly these:
`func_door` · `func_plat` · `func_button` · `func_train` · `func_static` ·
`func_rotating` · `func_bobbing` · `func_pendulum`.

**There is no `func_door_rotating`.** `func_rotating` sets
`s.apos.trType = TR_LINEAR` — it spins forever around an axis; it is not a
hinge that opens and stops. So:

* **A sliding split door is the native, correct design.** Two `func_door`
  leaves with opposite `angle`s, `speed 400`, `lip 8`, `TR_LINEAR_STOP` — real
  collision, real blocked-policy (`dmg 2`), deterministic at any timestamp.
  This is what PANTHEON_TEMPLE_V1 will use.
* **A hinged door is authorable but not stock.** Entities carry an angular
  trajectory (`s.apos`) that the engine evaluates with the same law, so
  PANTHEON can author `TR_LINEAR_STOP` on `apos` and get a deterministic
  hinge. It would have **no stock spawn function and no pusher collision**,
  and must be labelled that way wherever it appears.

## The door state contract

A door is not an animation; it is a function of time, and PANTHEON renders
frames out of order.

| | |
|---|---|
| closed | `pos1`, the authored spawn origin |
| open | `pos2 = pos1 + movedir · (dot(abs(movedir), size) − lip)` |
| law | `trType TR_LINEAR_STOP`, `trTime`, `trDuration = |delta| / speed · 1000`, `trDelta = delta · 1000 / trDuration` |
| leaves | one team; both leaves derive from the same `trTime`, never from two clocks |
| blocked | `dmg 2` per `SP_func_door`; a blocked leaf reverses, and that is part of the state |
| seek | `state(t)` is pure in `t`. Rendering frame 900 then frame 12 must give the same two poses as playing forward |

**The decorative MD3 leaves are driven BY the mover transform, never beside
it.** One evaluation per frame, feeding both the collision brush and the
drawn model; if they are ever computed twice, they will disagree, and the
disagreement will show up as a door whose picture is open and whose collision
is shut.

## Two honest routes, and what each may claim
**D1 — MD3 leaves on the real mover law** *(Phase 2, no map compiler)*
Door leaves are `.md3` props placed by the shot script; their origin follows
`TR_LINEAR_STOP` with `speed 400` and the real `pos1`/`pos2` arithmetic.
May be described as: *"door geometry authored by PANTHEON, moving on Quake's
own mover law, rendered in-world."* May **not** be described as a `func_door`:
there is no map entity and no collision. It is in-world motion, not post.

**R2 — a real `func_door`** *(Phase 3)*
A tiny compiled map with one `func_door` brush; the renderer already supports
it — `R_LoadSubmodels` names each submodel `*N`, `RE_RegisterModel` returns it
by that name, and `R_AddBrushModelSurfaces` draws it as a transformed entity.
The only missing piece is in **our host**: the shot script has no keyword for
a brush model. That is the minimal engine extension:

```
brush <submodelIndex> <x y z> <pitch yaw roll>
```

plus registering `"*N"` and adding an `RT_MODEL` refEntity. Small, and it
unlocks every mover in every map (doors, platforms, lifts) for free.

## Transition semantics to bank once it works

`PANTHEON_DOOR_TRANSITION` — doors open → reveal; doors close → cut; camera
through the doorway → another scene; leaf face as an analysis surface. Bank it
as a semantic in the effect grammar, not as an ad-hoc edit.
