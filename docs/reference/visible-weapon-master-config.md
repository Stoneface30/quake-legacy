# Visible-Weapon Cinematic Master Config — WolfcamQL 11.3

**Status:** Locked research, 2026-08-30. Supersedes the hidden-weapon MASTER_POV_CLEAN
profile in `moviemaking-feature-matrix.md` for gameplay masters (that doc remains
authoritative for capture mechanics, renderer, and FFmpeg pipe).

**Authority:** local canonical source `engine/engines/_canonical/code/` (WolfcamQL 11.3).
All line numbers refer to that tree. All cvars `CVAR_ARCHIVE` unless noted.

---

## 1. Weapon model display

### Core cvars

| Cvar | Default | Recommended | Source |
|---|---|---|---|
| `cg_drawGun` | `1` | `1` | `cgame/cg_main.c:1372` |
| `cg_gunX` | `0` | `0` | `cg_main.c:1636` |
| `cg_gunY` | `0` | `0` | `cg_main.c:1637` |
| `cg_gunZ` | `0` | `0` (see FOV note) | `cg_main.c:1638` |
| `cg_gunSize` | `1.0` | `1.0` | `cg_main.c:1639` |
| `cg_gunSizeThirdPerson` | `1.0` | n/a | `cg_main.c:1640` |
| `cg_gun_frame` | `0` | `0` (dev tool — freezes anim frame) | `cg_main.c` / `cg_weapons.c:2853` |

`cg_drawGun` semantics (from `cg_weapons.c:1671` and `:2523`, `cg_unlagged.c:140-143`):

- `0` — no gun (LG beam still re-emitted, `cg_weapons.c:2805-2811`)
- `1` — gun with full bob + idle drift (**normal QL look**)
- `2` — gun drawn **perfectly steady**: `CG_CalculateWeaponPosition` early-returns before
  any bob/idle-drift math (`cg_weapons.c:1671`) — no walk sway, no idle breathing
- `3` — steady like `2` **plus** ghost/transparent shader (`cg_weapons.c:2523-2529`)

Gun offsets are applied along the view axes in `CG_AddViewWeapon`
(`cg_weapons.c:2846-2848`): `gunX` forward, `gunY` right, `gunZ` up. Wolfcam applies the
identical logic to followed players (`wolfcam_weapons.c:87`), so the profile holds when
`follow`-ing the recorder in a demo.

### Bob cvars — what actually moves

Two independent systems:

1. **View bob** (the camera): `cg_bobup` / `cg_bobpitch` / `cg_bobroll` —
   **all default `0` in this build** (`cg_main.c:1642-1644`; vanilla Q3 values noted in
   source comments: 0.005/0.002/0.002). Applied in `cg_view.c:846-860`.
   `cg_runpitch`/`cg_runroll` are **compiled out** (`#if 0`, `cg_view.c:831-843`) — do
   not bother setting them. The camera is already cinematic-steady out of the box.
2. **Gun bob** (the weapon model): hardcoded constants inside
   `CG_CalculateWeaponPosition` — walk bob `cg_weapons.c:1699-1702`
   (ROLL/YAW/PITCH × 0.005–0.01 × xyspeed) and idle drift `cg_weapons.c:1726-1731`
   (sin-wave on all three angles). **There is no cvar to scale gun bob** — the only
   lever is `cg_drawGun 1` (full bob) vs `2` (zero bob).

**Verdict for cinematic steadiness without sterility:** run `cg_drawGun 1`. Because view
bob is already zeroed, the only motion is the gun's own subtle sway, which reads as
"alive" on a locked camera. If a specific clip needs a dead-steady gun (slow-mo money
shot), flip to `cg_drawGun 2` for that capture — it is a live, non-latched cvar.
Keep `cg_fallKick 1` (default `1`, `cg_main.c:2416`) — the small landing dip
(`cg_weapons.c:1706-1714`) sells impact weight.

---

## 2. Separate gun FOV — verdict: NOT SUPPORTED

There is **no** `cg_gunFov` / `mme_gunFov` / weapon-fov cvar in this build (verified by
full-tree grep of `cgame/`). The hand/gun entity is added to the **same refdef** as the
world (`CG_AddViewWeapon`, `cg_weapons.c:2772-2871`; `RF_FIRST_PERSON | RF_DEPTHHACK`,
`:2866`) and is therefore projected at the world FOV. The only FOV-awareness is a
position compensation, not a projection fix:

```c
// cg_weapons.c:2829-2833  — drop gun lower at higher fov
if ( fov > 90 ) { fovOffset = -0.2 * ( fov - 90 ); }
```

(`fov` comes from `cg_fov`, or `cg.demoFov` only when `cgs.realProtocol >= 91` +
`cg_useDemoFov 1` — a no-op on our protocol-73 corpus, see feature-matrix §2.)

**Proportionate range estimate:** default is `cg_fov 110` (`DEFAULT_FOV`,
`cg_local.h:22`). The perspective stretch on the gun (it lives at the screen edge, where
wide-angle distortion is worst) is invisible ≤ 100, mild and period-correct at 105–110,
and visibly rubbery from ~115 up. **Recommended shipping window: 100–110.** Do not
exceed 115 with the gun visible. If the gun sits too low at 110, counter the built-in
`fovOffset` (−4 units at 110) with `cg_gunZ` up to `+2` — do not exceed that or clipping
through the hand model appears.

---

## 3. Point crosshair

### Shape inventory

`NUM_CROSSHAIRS` = 30, indices 1-29 (`ui/ui_common.h:6` — "there are 29 in ql");
registered as `gfx/2d/crosshair%d` (`cg_main.c:3950`). Shapes verified by rendering all
29 pak00 assets (indices 20-29 are TGA-with-alpha in pak00.pk3 — the repo PNG mirror
lost their alpha; inspect the pk3 originals):

| Index | Shape |
|---|---|
| 1, 4 | dot inside filled disc |
| 2 | plus/cross (thick) |
| 3, 9, 19 | small cross variants |
| 5 | thick ring |
| 6 | large filled circle |
| 7 | cross-in-disc |
| 8 | hash (#) |
| 10, 16 | brackets |
| 11 | small square |
| 12, 14, 17 | circle-cross / reticle |
| 13 | dot, speckled halo |
| 15 | small circle |
| 18 | four diagonal ticks |
| 20, 24 | faint ring + center dot |
| 21, 26 | plus (soft) |
| 22 | broken cross |
| 23 | dot on dark disc |
| **25** | **pure small dot — nothing else** |
| 27 | soft plus (small) |
| 28 | thin cross |
| 29 | broken ring |

**The point crosshair is `cg_drawCrosshair 25`** (build default is `5`,
`cg_main.c:1528`).

### Crosshair cvars

| Cvar | Default | Recommended | Source (`cg_main.c`) |
|---|---|---|---|
| `cg_drawCrosshair` | `5` | `25` | :1528 |
| `cg_crosshairSize` | `32` | `24` | :1580 |
| `cg_crosshairColor` | `0xffffff` | `0xffffff` | :1581 |
| `cg_crosshairAlpha` | `255` | `255` | :1590 |
| `cg_crosshairBrightness` | `1.0` | `1.0` | :1589 |
| `cg_crosshairPulse` | `0` | `0` | :1582 |
| `cg_crosshairHealth` | `0` | `0` (color-by-health = noise) | :1583 |
| `cg_crosshairX` / `Y` | `0` / `0` | `0` / `0` | :1587-1588 |
| `cg_crosshairHitStyle` | `0` | `0` (or `1` for hit-flash) | :1584 |
| `cg_crosshairHitColor` | `0xff0000` | — | :1585 |
| `cg_crosshairHitTime` | `200` | — | :1586 |

**Smallest clean dot at 1920×1080:** sizes are 640-virtual units, so on a 1920-wide
frame the image is scaled ×3. The dot inside crosshair25's 32×32 canvas is ~4 px, so
`cg_crosshairSize 24` → ~9 px on-screen dot — visible on 1080p60 YouTube after
re-encode, still unobtrusive. `16` (≈6 px) is the floor before compression eats it;
`32` if the master will be viewed at 4K-upscale.

Wolfcam extension: freecam has its own toggle `cg_freecam_crosshair` — irrelevant for
first-person masters but zero it in freecam B-roll passes.

---

## 4. Frag feed (obituaries) + frag message

Two independent systems. The **obituary feed** (everyone's kills, killfeed) is a QL-HUD
ownerdraw element (`CG_PLAYER_OBIT`, drawn in `cg_newdraw.c:5971-6009`; position comes
from the hud file `ui/hud.txt` via `cg_qlhud 1`, `cg_main.c:1929`). The **frag message**
("You fragged X") is the recorder's own kill confirmation (`CG_DrawFragMessage`,
`cg_draw.c:8340`).

### Obituary cvars (`cg_main.c`)

| Cvar | Default | Recommended | Line |
|---|---|---|---|
| `cg_obituaryTokens` | `"%k %i %v"` | `"%k %i %v"` (killer icon victim — old-school) | :2274 |
| `cg_obituaryIconScale` | `1.5` | `1.2` | :2275 |
| `cg_obituaryTime` | `3000` | `2500` | :2276 |
| `cg_obituaryFadeTime` | `1000` | `600` | :2277 |
| `cg_obituaryStack` | `5` | `3` (recorder's kill never buried) | :2278 |

Setting `cg_obituaryTime 0` disables the feed entirely (gate `cg_newdraw.c:6004`).

### Frag message cvars (`cg_main.c:2250-2271`)

Defaults: `cg_fragMessageStyle 1`, `cg_drawFragMessageX 320`, `Y 120`, `Align 1`
(center), `Style 6`, `PointSize 24`, `Scale 0.25`, `Time 3000`, `Color 0xffffff`,
`Alpha 255`, `Fade 1`, `FadeTime 200`,
`Tokens "You fragged %v"`, `IconScale 1.5`, `cg_drawFragMessageSeparate 0`.

**Tuned old-school layout (recorder's kills front and center):**

```
cg_fragMessageStyle 1
cg_drawFragMessageX 320
cg_drawFragMessageY 110            // just above center-screen, clear of the dot
cg_drawFragMessageAlign 1
cg_drawFragMessageStyle 6          // drop-shadowed
cg_drawFragMessageScale 0.28       // slightly larger than stock
cg_drawFragMessageTime 2000        // punchy — gone before the next fight
cg_drawFragMessageFade 1
cg_drawFragMessageFadeTime 250
cg_drawFragMessageTokens "You fragged %v"
cg_drawFragMessageColor 0xffffff
```

Reward medals (`cg_drawRewards 1`, X 320 / Y 56, `cg_main.c:1561-1578`) stack directly
above the frag message — keep them, they are the old-school hype layer.

---

## 5. Minimal HUD keeps

Start from MASTER_POV_CLEAN (feature-matrix §1) and re-enable only:

| Element | Cvar | Value | Why |
|---|---|---|---|
| Crosshair | `cg_drawCrosshair` | `25` | §3 |
| Killfeed | `cg_obituaryTime` | `2500` | context on multi-frags |
| Frag message | `cg_drawFragMessageTime` | `2000` | kill confirmation |
| Reward medals | `cg_drawRewards` | `1` | excellent/impressive punch |

Deliberately **left off**: `cg_drawStatus` (HP/armor/ammo bar — there is no standalone
ammo-only element; the status bar is all-or-nothing per `cg_drawStatus`,
`cg_main.c:1419`, and it dates the frame), `cg_drawAmmoWarning` (`cg_main.c:1479` —
"LOW AMMO" text mid-screen kills drama), attacker portrait, timers, scores, FPS
(default **1** in wolfcam — must zero), lagometer, pickup text, chat, vote, center-print.

---

## 6. Audio — hit feedback vs kill confirmation

**Clean cvar separation exists. No pk3 override needed.**

### Kill confirmation chime — OFF

The kill beep fires in `CG_Obituary` only for the recorder's own kills
(`cg_event.c:120-124`): gate is `cg_killBeep.integer > 0`, played on the dedicated
`CHAN_KILLBEEP_SOUND` channel.

- **`cg_killBeep` — default `7`, set `0`** (`cg_main.c:2449`). This is the primary
  switch: with `0` the sound is never started. Registered chime files
  (`cg_main.c:3707-3710`), for the record:
  - values 1-6 → `sound/feedback/impact1.ogg` … `impact6.ogg`
  - value 7 (default) → `sound/world/bell_01.ogg`  ← the stock "kill bell"
  - value 8 → `sound/misc/chaching.ogg`
- Belt-and-braces mixer mute: **`s_killBeepVolume` — default `1.0`, set `0`**
  (engine cvar, `client/snd_main.c:571`; applied per-channel in
  `client/snd_mix.c:868-872`). Only touches `CHAN_KILLBEEP_SOUND` — hit beeps ride
  `CHAN_LOCAL_SOUND` and are unaffected.

### Hit beeps — KEPT

`cg_hitBeep` — default `2`, **keep `2`** (`cg_main.c:1956`). Logic in
`CG_CheckLocalSounds` (`cg_playerstate.c:845-922`):

- `1` = single classic `sound/feedback/hit.wav`
- `2` = **QL damage-tiered tones** — damage tier from `ps->generic1 / 64` selects
  `sound/feedback/hit0.ogg` … `hit3.ogg` (registered `cg_main.c:3587-3591`)
- `3` = same, tier order reversed
- `0` = off. Teammate-hit warning `sound/feedback/hit_teammate.wav` also honours
  `cg_hitBeep` (`cg_playerstate.c:927`).

Weapon fire, impacts, world sounds are ordinary entity-channel sounds — untouched by
any of the above.

### Announcer

Per-category cvars (`cg_main.c:2203-2218`): keep `cg_audioAnnouncer 1` +
`cg_audioAnnouncerRewards 1` (EXCELLENT/IMPRESSIVE — old-school hype), zero the noise:
`cg_audioAnnouncerVote 0`, `cg_audioAnnouncerTimeLimit 0`, `cg_audioAnnouncerFragLimit 0`,
`cg_audioAnnouncerLead 0` ("taken the lead" spam). Global gain: `s_announcerVolume`
(default `1.0`, `client/snd_main.c:570`).

### zsilence.pk3 note

`engine/engines/_canonical/package-files/wolfcam-ql/zsilence.pk3` contains a single
root-level `silence.wav` (1,044 bytes) — it is a **silent-wav template** shipped with
wolfcam, not an active override (a root-level file shadows nothing). If a future need
arises to silence a sound that has *no* cvar, copy that wav into a `zzz_silence.pk3`
under the exact pak path of the target sound (e.g. `sound/world/bell_01.ogg` →
re-encode silence as ogg). For the kill chime this is unnecessary — `cg_killBeep 0`
is the supported path.

---

## 7. TR4SH_GAMEPLAY_MASTER_V2 — paste-ready

```
// ===== TR4SH_GAMEPLAY_MASTER_V2 — visible weapon, cinematic FP =====
// Renderer + capture: use the mezzanine skeleton from moviemaking-feature-matrix.md.

// --- weapon display ---
cg_drawGun 1                      // full gun w/ natural sway; flip to 2 for dead-steady shots
cg_gunX 0; cg_gunY 0; cg_gunZ 0   // raise gunZ to +2 max if fov 110 sits low
cg_gunSize 1.0
cg_fallKick 1
cg_bobup 0; cg_bobpitch 0; cg_bobroll 0   // build defaults — camera stays level

// --- fov (no separate gun fov in this build; keep <= 110 with gun visible) ---
cg_fov 105

// --- point crosshair ---
cg_drawCrosshair 25               // pure dot
cg_crosshairSize 24               // ~9px at 1080p; 16 = floor, 32 = 4K-safe
cg_crosshairColor 0xffffff
cg_crosshairAlpha 255
cg_crosshairBrightness 1.0
cg_crosshairPulse 0
cg_crosshairHealth 0
cg_crosshairHitStyle 0

// --- HUD: everything off, then the four keeps ---
// (paste MASTER_POV_CLEAN from moviemaking-feature-matrix.md §1 FIRST, minus cg_draw2D 0
//  and minus cg_drawGun 0, then re-enable:)
cg_draw2D 1
cg_drawRewards 1
cg_obituaryTokens "%k %i %v"
cg_obituaryIconScale 1.2
cg_obituaryTime 2500
cg_obituaryFadeTime 600
cg_obituaryStack 3
cg_fragMessageStyle 1
cg_drawFragMessageX 320
cg_drawFragMessageY 110
cg_drawFragMessageAlign 1
cg_drawFragMessageStyle 6
cg_drawFragMessageScale 0.28
cg_drawFragMessageTime 2000
cg_drawFragMessageFade 1
cg_drawFragMessageFadeTime 250
cg_drawFragMessageTokens "You fragged %v"
cg_drawFragMessageColor 0xffffff

// --- audio: kill chime OFF, hit beeps ON, everything else natural ---
cg_killBeep 0                     // primary: kill confirmation never plays
seta s_killBeepVolume 0           // belt-and-braces mixer mute (engine cvar)
cg_hitBeep 2                      // QL damage-tiered hit tones (hit0-3.ogg)
cg_audioAnnouncer 1
cg_audioAnnouncerRewards 1
cg_audioAnnouncerVote 0
cg_audioAnnouncerTimeLimit 0
cg_audioAnnouncerFragLimit 0
cg_audioAnnouncerLead 0
```

---

## 8. Benchmark plan — world FOV with visible gun

Capture the same 15-second frag sequence (rocket + LG + rail in one demo segment) once
per variant; A/B in the studio player at 100% zoom.

```
// bench_fov.cfg — run 4 passes, one seekclock each
// Pass A: cg_fov 100 ; video pipe name fovA :demoname
// Pass B: cg_fov 105 ; video pipe name fovB :demoname
// Pass C: cg_fov 110 ; video pipe name fovC :demoname
// Pass D: cg_fov 115 ; video pipe name fovD :demoname
```

Rationale per value:

- **100** — zero visible gun distortion, tighter framing; risk: movement speed reads slower
- **105** — sweet-spot candidate: near-zero distortion, speed still reads
- **110** — build default (`DEFAULT_FOV`, `cg_local.h:22`), period-correct QL duel feel;
  gun stretch first becomes detectable, built-in −4u gun drop kicks in
- **115** — upper bound; expect visible gun stretch at screen edge — included to prove
  the ceiling, not to ship

Secondary axes on the winning FOV (2 extra passes each):

- `cg_drawGun 1` vs `2` — does gun sway help or hurt on speed-ramped clips?
- `cg_crosshairSize 16` vs `24` — dot survival after YouTube 1080p re-encode (VIS-1:
  frame-grab both into `docs/visual-record/`).

Judge on: gun proportion at screen edge, perceived movement speed, rocket arc
readability, dot visibility over bright skies.

---

*Sources: `engine/engines/_canonical/code/cgame/{cg_main.c, cg_weapons.c, cg_view.c,
cg_event.c, cg_playerstate.c, cg_newdraw.c, cg_draw.c, cg_unlagged.c, wolfcam_weapons.c}`,
`code/client/{snd_main.c, snd_mix.c}`, `code/ui/ui_common.h`, pak00.pk3 crosshair
assets (read-only inspection per ENG-4), `package-files/wolfcam-ql/zsilence.pk3`.*
