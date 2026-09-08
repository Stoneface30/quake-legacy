# PART 1 — MOVEMENT & SPEED, VERIFIED

Every constant cited to `engine/engines/`. The tree is SHA-256 deduped:
`_manifest/canonical_map.json` maps `_canonical/code/**` → wolfcamql-src and
`_canonical/trunk/**` → q3mme. That dedup is why a q3mme cvar has been mistaken
for a WolfcamQL one — see §3.

---

## 1. ENGINE CONSTANTS — safe to show

| Fact | Value | Source |
|---|---|---|
| Base run speed | **320 ups** | `_canonical/code/game/g_main.c:152` (`g_speed`) |
| Jump velocity | **270** (assigned to `velocity[2]`) | `bg_local.h:32`, applied `bg_pmove.c:387` |
| Gravity | **800** | `g_main.c:153` |
| Ground acceleration | **10.0** | `bg_pmove.c:38` |
| **Air acceleration** | **1.0** | `bg_pmove.c:39` |
| Friction / stopspeed | 6.0 / 100.0 | `bg_pmove.c:43`, `:34` |
| Rocket speed | **900 ups**, `TR_LINEAR` (no drop) | `g_main.c:194`, `g_missile.c:679` |
| Grenade speed | 700 ups | `g_missile.c:596` |
| Plasma speed | 2000 ups | `g_missile.c:552` |
| **Rail is hitscan** | trace to **8192 units**, resolved in one server frame | `g_weapon.c:437,455,461` |
| Teleport exit | velocity **forced to a flat 400 ups**, 160 ms input lockout | `g_misc.c:79` (`TeleportPlayer`) |
| Jump pad | velocity **assigned**, not added — incoming speed discarded | `BG_TouchJumpPad`, `bg_misc.c`; solved once at spawn by `AimAtTarget`, `g_trigger.c:160-192` |

**The single most filmable constant is `pm_airaccelerate = 1.0` against
`pm_accelerate = 10.0`.** That one ratio is why strafe-jumping exists: you keep
accelerating in the air, slowly, forever, if you steer correctly. It is the
mechanical root of the whole Part 1 thesis and it is one line of source.

### Two facts that read as poetry and are literally true
- **A teleporter throws away your speed.** Exit is a flat 400 ups regardless of
  how fast you arrived, and you cannot steer for 160 ms.
- **A jump pad does not care how fast you were going either.** Its launch
  velocity is a ballistic solution to the map's own geometry, computed once when
  the map loads.

Both are *spatial resets* — perfect Part 2 transition language.

### UNVERIFIED — do not claim
Whether Quake Live's movement constants differ from Q3 defaults. WolfcamQL is a
demo *player*; the `game/` code in this repo is stock Q3 QVM source, not what a
QL server ran. No serverinfo cache in any DB carries `g_speed`. **No on-screen
text may compare QL to Q3.**

---

## 2. MEASURED CORPUS SPEED — 1,333 confirmed

`movement_moments_v1`, run `movement-moments-v1.0.0`, built 2026-09-04 06:40.

```
HIGH_SPEED_MOVEMENT    1,333
JUMPPAD_ACTION        40,342
```

Peak speed across the 1,333 high-speed runs:

| | ups |
|---|---|
| min | 568.8 |
| p25 | 623.2 |
| **median** | **672.1** |
| p75 | 771.2 |
| p90 | 862.7 |
| p99 | 1131.6 |
| max | 1196.9 |

Duration 300 / **1,525** / 5,050 ms (min/median/max). Distance 115 / 1,002 /
2,847 units. All 1,333 carry trait `STRAFE_CHAIN`; **382 end in a frag**, 46 end
in a death, 428 link to a canonical occurrence.

Top maps: campgrounds 494 (max 1164), trinity 251 (1162), overkill 251 (1197),
quarantine 121 (1082), asylum 70 (1181).

### THREE CAVEATS — binding on screen copy
1. **These are not speedometer readings.** `movement_moments.py:141,161-166`
   derives speed as XY displacement between consecutive playerstate JUMP events
   over Δt (0.05 s < Δt ≤ 1.2 s). It is a **segment average over roughly a third
   of a second**, so it *understates* the instantaneous peak the engine would
   print. Frame it as measured movement, never as "top speed".
2. **The distribution is truncated at 1,200.** `IMPLAUSIBLE_UPS = 1200.0`
   (`movement_moments.py:56`) discards anything faster as a discontinuity. Max
   observed (1,196.9) sits 3 ups under the ceiling. Say *"the fastest run the
   detector accepts"*, never *"the fastest run in the archive"*.
3. **Threshold is 566, not 587.** Stored `threshold_ups = 565.996` (p95 of
   172,829 segments). The docstring's 587 is an earlier calibration.

### `frags.db.player_snapshots` — BROKEN, DO NOT USE
It has `vel_x/y/z` and a precomputed `speed`, but from **one demo only** and the
values are an order of magnitude past every engine constant: median 3D speed
2,766 ups, max 31,762. The decode or scaling is wrong. `movement_moments_v1` is
the only measured speed source.

---

## 3. THE SPEEDOMETER — the brief's instruction is inverted

The brief states WolfcamQL uses `cg_drawSpeedometer`, "not `cg_speedometer` and
not `cg_drawSpeed`". **The opposite is true**, and the project's own
`master_profile.py:300-320` carries the same inversion.

- **WolfcamQL registers `cg_drawSpeed`** + 12 siblings —
  `_canonical/code/cgame/cg_main.c:1843-1855`; declared `cg_local.h:3058-3070`;
  drawn by `Wolfcam_DrawSpeed`, `cg_draw.c:784-874`.
- **`cg_drawSpeedometer*` is q3mme** —
  `_forks/q3mme/trunk/code/cgame/cg_main.c:409-413`. Zero matches in the wolfcam
  cgame tree.
- The project's own extracted inventory agrees with the source:
  `wolfcam-knowledge/01-commands-cvars.md:925-936` lists all 12 `cg_drawSpeed*`
  entries and zero `cg_drawSpeedometer`.

**Consequence:** the `_SPEED_REVIEW` capture profile sets a cvar WolfcamQL does
not have. Any burned-in speed readout it was meant to produce was never drawn.
Raised as a separate task against the review session's code — **this workstream
does not edit `master_profile.py`.**

**What the real readout means** (`cg_draw.c:820-841`): following a player it is
**horizontal only** — `sqrt(vx² + vy²)`, Z excluded — printed as integer + `ups`.
Free-cam shows full 3D magnitude. Engine colour bands: **320 / 420 / 520 / 620 /
720 / 820**.

Those bands are the honest source for the brief's `320 → 420 → 520 → 650`
climb — the first three are real engine thresholds. **Use 320 / 420 / 520 / 620**
and the readout matches what the engine would actually colour.

### Ruling for Part 1
Prefer a **PANTHEON speed graphic driven by measured `peak_speed`** over the
Wolfcam HUD: it is styled to the film, it is honest about being a measurement,
and it does not depend on a capture profile that is currently broken. If the
Wolfcam HUD is used instead, the cvar is **`cg_drawSpeed 1`** with
`cg_drawSpeedStyle` / `cg_drawSpeedAlign` / `cg_drawSpeedX` / `cg_drawSpeedY`,
and a grabbed frame must prove the number is on screen before anything ships.
