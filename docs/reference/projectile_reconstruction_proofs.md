# Projectile reconstruction — proofs on real demos (2026-09-02)

Module: `creative_suite/engine/projectile_reconstruction.py` (`projectile-recon-v1.1.0`).
Rules come from the game source (`g_missile.c`, `bg_misc.c`, `g_main.c`): rocket
`TR_LINEAR` at `g_weapon_rocket_speed`, 15 s life, 120 u splash; grenade 700 u/s,
gravity 800, `EF_BOUNCE_HALF` reflect ×0.65, rest when `normal.z > 0.2 && speed < 40`,
2500 ms fuse, 150 u splash. Nothing is fitted toward the kill: the path is propagated
from the last recorded sample, then checked against what the demo recorded later.

Identity everywhere is `(content_hash, server_time_ms)`. Frags are named by numeric id.

## Rocket — frag 24326

- Recorded: 2 samples, 25 ms apart; measured speed 998.8 u/s (QL, not the 900 canonical default).
- World-only continuation: 1,824 ms to a wall.
- The demo's `missile_hit` at the frag tick sits 49 u from the path → cut at 1,125 ms,
  `DYNAMIC_CONTACT`, confidence `DETERMINISTIC_UNTIL_UNOBSERVED_DYNAMIC_CONTACT`.
  The victim's collision itself was **not** observed; the cut is where a recorded hit says it stopped.
- Corpus: 164 lost recorder rockets → 153 predicted impacts, median residual 2.0 u, 135/153 within splash.
- Figure: `docs/visual-record/2026-09-02/projectile_reconstruction_frag24326.png`.

## Grenade — frag 28557 (trinity)

- Recorded: 2 samples, 25 ms. Unobserved: 2,475 ms.
- World-only continuation: 5 bounces (curved-surface normals from patch triangles,
  `_triangle_entry`, added in v1.1.0), fuse at 2,500 ms.
- The demo's recorded explosion lies **5.7 u** from the predicted position at the fuse tick →
  `FUSE`, confidence `EXACT_DETERMINISTIC` (an event that lands where and when the world-only
  physics already ended confirms it; `CONFIRM_WINDOW_US = 50_000`).
- The same event exists in a second, trimmed demo (frag 33576); it is one proof, not two.
- Figure: `docs/visual-record/2026-09-02/grenade_reconstruction_frag28557.png`.

### The other real-gap grenades (honest)

Of the corpus' twelve highest-gap recorder grenades (kills 300–2,500 ms after the last sample;
no hand-picked ids), one distinct event reconstructs; the rest are `AMBIGUOUS`:
spatial misses of 700–1,970 u after 1–3 bounces, or no explosion recorded within 300 ms of
the frag. The world trace sees only the static BSP: a player body, a mover (door, platform)
or a jump pad that the grenade touched in the gap changes everything after it, and the module
reports the disagreement instead of bending the path. Fully-recorded grenades (last sample =
hit tick) are **not** reconstructions and are never counted as proof; on 8 of them the physics
step reproduces the final recorded sample with median residual 15.7 u (validation only).

## Code spaces (easy to get wrong)

- `missile_samples_v1.weapon` is the **WP_** space (4 = grenade launcher, 5 = rocket launcher).
- Event `weapon` on `missile_hit` / `missile_miss` is the **MOD_** space
  (4 = `MOD_GRENADE` direct, 5 = `MOD_GRENADE_SPLASH`, 6/7 rocket).
- Delta-coded event positions: a missing `pos_z` means *unchanged*, not unknown.
