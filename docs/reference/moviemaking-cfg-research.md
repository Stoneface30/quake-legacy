# Professional Fragmovie Display Configuration — WolfcamQL 11.3 Research

Date: 2026-08-31 · Status: research deliverable (no code changed)
Primary evidence: `G:\QUAKE_LEGACY\engine\engines\_canonical\code\cgame\cg_main.c` cvar table
(all cg_* line numbers below are registration lines from that file unless another file is named),
renderer registrations from `renderergl1/tr_init.c` (we run gl1), MME from `renderercommon/tr_mme.c`,
client from `client/cl_console.c` / `client/cl_main.c` / `client/snd_main.c`.
Baseline being refined: `creative_suite/engine/master_profile.py::_GAMEPLAY_MASTER_V2`.

Goal: cinematic first-person QL fragmovie look (classic Q3MME-era reference), NOT a competitive
config. Authentic world, lit models, readable minimal information layer.

Legend: **Rec** = recommended movie value. `=` means keep the engine default / current V2 value.

---

## 1. Research Matrix

### 1.1 World FOV

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_fov` | cg_main.c:1377 | `DEFAULT_FOV` (xmstr) | **110** (frozen, V2) | v2fov_grid benchmark: 115 stretches the visible gun; 110 keeps speed feel with readable targets |
| `cg_fovy` | cg_main.c:1378 | `""` | = (empty) | Explicit y-fov override; empty = derived. Leave derived |
| `cg_fovStyle` | cg_main.c:1379 | `1` | = **1** (verify) | 0 = Q3 (x fixed, y derived — zooms in on wide screens), 2 = QL preset-aspect stretch (cg_view.c:1035,1062). Style 1 is the sane widescreen middle; do NOT change without a test frame — it changes projection math vs all existing masters |
| `cg_fovIntermission` | cg_main.c:1382 | `90` | = | We never capture intermission |
| `cg_zoomFov` | cg_main.c:1373 | `60` | = | Demo-taker zoom replays authentically |
| `cg_zoomIgnoreTimescale` | cg_main.c:1375 | `1` | = | Zoom animation stays correct under slow-mo capture |
| `cg_useDemoFov` | cg_main.c:2607 | `0` | = 0 | Protocol >= 91 only — no-op on our .dm_73 corpus (documented in master_profile.py) |

### 1.2 Gun FOV / placement

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_drawGun` | cg_main.c:1372 | `1` | **1** | 1 = gun with natural sway; 2 = gun without sway/bob, 3+ = ghost shader (cg_weapons.c:1671, 2523). Natural sway is the lifelike choice |
| `cg_gunX` / `cg_gunY` / `cg_gunZ` | cg_main.c:1636-1638 | `0/0/0` | = 0/0/0 | Authentic QL placement. (Classic movie-cfg trend of pulling the gun back/down is a taste option — bench `cg_gunZ -4` once, nothing more) |
| `cg_gunSize` | cg_main.c:1639 | `1.0` | = 1.0 | Scaled-down guns read "config-tweaked", not cinematic |
| `cg_gunSizeThirdPerson` | cg_main.c:1640 | `1.0` | = | Only for replay-angle passes |
| `cg_gunFovOffset` | **NOT REGISTERED** | — | — | **UNVERIFIED — does not exist in wolfcamql 11.3.** Do not use |

### 1.3 View bob / weapon sway

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_bobup` | cg_main.c:1642 | `0` (source comment: q3 was 0.005) | **0.005** (verify) | Wolfcam ships bob OFF (QL competitive convention). A slight vertical bob restores the human, filmed-from-the-eyes feel of classic Q3 movies |
| `cg_bobpitch` | cg_main.c:1643 | `0` (q3 0.002) | **0.002** (verify) | Same — micro pitch bob while running |
| `cg_bobroll` | cg_main.c:1644 | `0` (q3 0.002) | **0.002** (verify) | Same — micro roll; the three together are the classic Q3 gait |
| `cg_swingSpeed` | cg_main.c:1645 | `0.3` (CVAR_CHEAT) | = | Third-person torso swing only |
| `cg_fallKick` | cg_main.c:2416 | `1` | = **1** (V2) | Landing dip sells verticality |
| `cg_runpitch` / `cg_runroll` | **NOT REGISTERED** | — | — | **UNVERIFIED — not in this fork** (stock Q3 cvars, removed). Do not use |
| `cg_gunBob*` family | **NOT REGISTERED** | — | — | **UNVERIFIED — no such family in cg_main.c.** Gun sway is bound to cg_drawGun value (1 vs 2), not a cvar family |

### 1.4 Crosshair (minimal dot)

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_drawCrosshair` | cg_main.c:1528 | `5` | **25** (V2) | Shape 25 = pure dot |
| `cg_crosshairSize` | cg_main.c:1580 | `32` | **24** (V2) | ~9 px dot at 1080p — present, never dominant |
| `cg_crosshairColor` | cg_main.c:1581 | `0xffffff` | = **0xffffff** | Neutral white; never tints the grade |
| `cg_crosshairAlpha` | cg_main.c:1590 | `255` | **255** (V2) — option 210 | Full is fine for a dot; 210 softens it into the frame if a test frame reads harsh |
| `cg_crosshairBrightness` | cg_main.c:1589 | `1.0` | = | — |
| `cg_crosshairPulse` | cg_main.c:1582 | `0` | = 0 (V2) | Pickup pulse is game-UI noise |
| `cg_crosshairHealth` | cg_main.c:1583 | `0` | = 0 (V2) | Color-by-health fights the grade |
| `cg_crosshairHitStyle` | cg_main.c:1584 | `0` | = 0 | Hit-color flash is a gaming tell; hit BEEP carries the info (1.14) |
| `cg_crosshairX` / `Y` | cg_main.c:1587-1588 | `0/0` | = | Centered |
| `cg_drawCrosshairNames` | cg_main.c:1531 | `1` | **0** (V2) | THE oversized floating-name defect — consecutive fading names ghost into a jumble |
| `cg_drawCrosshairTeammateHealth` | cg_main.c:1546 | `1` | **0** (V2) | Spectator UI |
| `cg_freecam_crosshair` | cg_main.c:1971 | `1` | **0** | No crosshair on free-cam/cinematic passes |

### 1.5 Frag feed (killfeed / obituaries)

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_obituaryTime` | cg_main.c:2276 | `3000` | **2500** (V2) | Brisk feed; gate is a TIME cvar, 0 = off |
| `cg_obituaryFadeTime` | cg_main.c:2277 | `1000` | **600** (V2) | Snappier exit |
| `cg_obituaryStack` | cg_main.c:2278 | `5` | **3** (V2) | Max 3 lines — CA rounds otherwise wall-of-text |
| `cg_obituaryTokens` | cg_main.c:2274 | `"%k %i %v"` | = (V2) | killer icon victim — the classic format |
| `cg_obituaryIconScale` | cg_main.c:2275 | `1.5` | **1.2** (V2) | Weapon icons slightly under-scaled = elegant |
| position / text scale | HUD menu | — | via qlhud rect | **No cg_obituaryX/Y cvar exists.** `CG_DrawObit(rect, scale, ...)` (cg_newdraw.c:5960) is an ownerdraw — the qlhud .menu rect controls position, the menu item's textscale controls text size. Repositioning requires a HUD file, not a cvar |

### 1.6 Frag message ("You fragged X") — CURRENT DEFECT ROOT CAUSE

**Finding (the defect):** the frag message has TWO draw paths (cg_event.c:465,490,516):

- Default (`cg_drawFragMessageSeparate 0`): routed through **CENTER PRINT** (`CG_CenterPrintFragMessage`,
  cg_draw.c:7054). In that path it is **gated by `cg_drawCenterPrint`** (cg_draw.c:8065) and sized by
  **`cg_drawCenterPrintScale`** (default 0.35, cg_draw.c:8234) — NOT by `cg_drawFragMessageScale`.
- Separate (`cg_drawFragMessageSeparate 1`): dedicated `CG_DrawFragMessage` (cg_draw.c:8340) which
  honors `cg_drawFragMessageX/Y/Align/Scale/Style/Font/PointSize/Color/Alpha/Fade*`.

**V2 sets all the cg_drawFragMessage* styling cvars but leaves Separate at its default 0 AND sets
`cg_drawCenterPrint 0` — so the tuned styling never applies; the message is either suppressed
entirely (centerprint off) or, when centerprint is on, drawn at the giant 0.35 centerprint scale.
That is the exact "text too large" defect.**

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_drawFragMessageSeparate` | cg_main.c:2253 | `0` | **1** | Activates the dedicated path where all the tuning below actually applies |
| `cg_drawFragMessageTime` | cg_main.c:2261 | `3000` | **2000** (V2) | Short confirmation |
| `cg_drawFragMessageScale` | cg_main.c:2260 | `0.25` | **0.22** | Elegant small text (with qlhud textFont; V2's 0.28 was tuned against the wrong path) |
| `cg_drawFragMessagePointSize` | cg_main.c:2259 | `24` | **32** if a FreeType font is set, else = | PointSize is the FreeType raster size used ONLY when `cg_drawFragMessageFont` is non-empty (cg_main.c:2965); higher raster + small scale = crisp small glyphs at 1080p |
| `cg_drawFragMessageFont` | cg_main.c:2258 | `""` | = "" first; bench one FreeType face second | Empty = qlhud textFont (clean). A dedicated face is the "pro" upgrade if the default rasters soft |
| `cg_drawFragMessageX` / `Y` | cg_main.c:2254-2255 | `320/120` | **320 / 110** (V2) | Upper-center, above crosshair sightline, below feed |
| `cg_drawFragMessageAlign` | cg_main.c:2256 | `1` | = 1 | Centered on X |
| `cg_drawFragMessageStyle` | cg_main.c:2257 | `6` | = 6 | Dropshadowed style — legible on bright maps without a box |
| `cg_drawFragMessageColor` | cg_main.c:2262 | `0xffffff` | = | Neutral |
| `cg_drawFragMessageAlpha` | cg_main.c:2263 | `255` | = | Fade handles the exit |
| `cg_drawFragMessageFade` / `FadeTime` | cg_main.c:2264-2265 | `1 / 200` | **1 / 250** (V2) | Soft out |
| `cg_drawFragMessageTokens` | cg_main.c:2266 | `"You fragged %v"` | = (V2) | The classic line |
| `cg_drawFragMessageIconScale` | cg_main.c:2271 | `1.5` | **1.2** | Match obituary icon proportion |

### 1.7 Reward medals

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_drawRewards` | cg_main.c:1561 | `1` | **1** (V2) | Excellent/Impressive medals are fragmovie candy — keep |
| `cg_drawRewardsImageScale` | cg_main.c:1570 | `1.0` | **0.8** | Slightly under-scaled medal = premium, not arcade |
| `cg_drawRewardsTime` | cg_main.c:1571 | `3000` | **2000** | On, celebrated, gone |
| `cg_drawRewardsScale` | cg_main.c:1569 | `0.25` | **0** counter text: set `cg_drawRewardsMax` low instead | Reward count text; keep default, rely on short time |
| `cg_drawRewardsMax` | cg_main.c:1562 | `10` | **3** | Caps stacked-medal spam in multi-frag runs |
| `cg_drawRewardsX/Y/Align/Style` | cg_main.c:1563-1566 | `320/56/1/3` | = | Top-center is the classic slot |
| `cg_drawRewardsFade/FadeTime` | cg_main.c:1574-1575 | `1/200` | = 1 / **250** | Match frag-message fade |

### 1.8 Damage feedback

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_screenDamage` / `cg_screenDamageAlpha` | cg_main.c:2231 / 2230 | `0x700000` / `200` | = color / **120** | The classic red directional blend (CG_DamageBlendBlob, cg_view.c:1224) tells the story of taking damage; alpha 200 blows out the grade on rocket spam — 120 keeps it felt, not blinding |
| `cg_screenDamage_Self` / `Alpha_Self` | cg_main.c:2228-2229 | `0x000000` / `0` | = | Self-damage flash already off — correct (rocket-jump-heavy footage) |
| `cg_screenDamage_Team` / `Alpha_Team` | cg_main.c:2226-2227 | `0x700000` / `200` | = / **120** | Match main |
| `cg_damageFeedbackInterval` | cg_main.c:2415 | `800` | = | — |
| `cg_kickScale` | cg_main.c:2413 | `0` | = **0** | Wolfcam ships view-kick OFF. Keep — stable master footage; post-pipeline speed-ramps supply impact (P1-Q). (1.0 = authentic Q3 shake, taste option only) |
| `cg_viewKick` | **NOT REGISTERED** | — | — | **UNVERIFIED — the real cvar is cg_kickScale.** Do not use |
| `com_blood` (var `cg_blood`) | cg_main.c:1772 | `1` | = 1 | World blood puffs/gibs are authentic Q3; note wolfcam does NOT gate the screen blend on it (cg_view.c:1232-1237 #if 0) |
| `cg_gibs` | cg_main.c:1387 | `15` | = | Gib count — default already generous |

### 1.9 Player-model & weapon lighting (authentic lit models)

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_enemyModel` | cg_main.c:2096 | **`"keel/bright"`** | **`""`** (V2) | Wolfcam's DEFAULT is forced bright keel — the single biggest de-gaming lever. Empty restores each player's authentic model + lightmap-lit skin |
| `cg_teamModel` | cg_main.c:2112 | `""` | = "" (V2) | Authentic |
| `cg_forceModel` | cg_main.c:1683 | `0` | = 0 (V2) | Authentic |
| `cg_useDefaultTeamSkins` | cg_main.c:2164 | `1` | = (verify) | In team modes keeps red/blue readable; only revisit if a CA clip looks wrong |
| `cg_deadBodyColor` | cg_main.c:2198 | `0x101010` | = | QL-style corpse darkening — authentic and reads well |
| `r_fullbright` | tr_init.c:1846 | `0` | = 0 | Flat-lit debug mode — never |
| `r_vertexLight` | tr_init.c (1828 area) | `0` | = 0 (in _QUALITY) | Lightmaps ON is the whole "lit models/world" mandate |
| `cg_brightSkins` / `r_lightmap` as toggles | **NOT REGISTERED** as such | — | — | **UNVERIFIED — bright skins in this fork are done via model strings (`/bright` suffix), not a cvar.** r_lightmap exists in stock renderers as debug; do not touch |
| `cg_muzzleFlash` | cg_main.c:2340 | `1` | = 1 | Weapon light interplay with the world |
| `r_dynamiclight` | renderergl1/tr_init.c:1874 | `1` | = 1 (in _QUALITY) | Rocket glow lighting walls IS the classic fragmovie look |

### 1.10 Rail beam

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_railQL` | cg_main.c:1625 | `1` | = 1 (V2) | QL-style beam+spiral — the era-correct look for QL demos |
| `cg_railTrailTime` | cg_main.c:1624 | `400` | **600** (gameplay) / 1200 (cinematic profile, already set) | Slightly longer persistence lets the beam register on a 60fps cut without turning into laser-decor |
| `cg_railQLRailRingWhiteValue` | cg_main.c:1626 | `0.45` | = | — |
| `cg_railRings` | cg_main.c:1628 | `0` | = 0 | QL style already handles rings |
| `cg_railRadius` | cg_main.c:1629 | `4` | = | — |
| `cg_railRotation` / `cg_railSpacing` | cg_main.c:1630-1631 | `1 / 5` | = | — |
| `cg_railFromMuzzle` | cg_main.c:1634 | `1` | = 1 | Beam originates at the visible gun — critical with cg_drawGun 1 |
| `cg_railNudge` | cg_main.c:1627 | `1` | = | — |
| `cg_railUseOwnColors` | cg_main.c:1633 | `0` | = 0 | Players' real rail colors = authentic variety |
| `cg_enemyRailColor1/2` | cg_main.c:2104-2105 | `""` | = "" (V2) | No forced enemy colors |
| `r_railWidth` | renderergl1/tr_init.c:1883 | `16` | = 16 | Only used by the old q3 rail path — with cg_railQL 1 leave alone |
| `r_railCoreWidth` | tr_init.c:1884 | `6` | = 6 | Same |
| `r_railSegmentLength` | tr_init.c:1885 | `32` | = 32 | Same |
| `cg_oldRail` | cg_main.c:1836 **commented out** | — | — | **UNVERIFIED — registration is commented out in this fork.** Do not use |

### 1.11 Lightning gun beam

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_lightningStyle` | cg_main.c:2306 | `1` | = 1 | 1-5 select `lightningBolt%d` shaders (cg_weapons.c:2014); 1 is the QL bolt |
| `cg_lightningRenderStyle` | cg_main.c:2307 | `1` | = 1 | 1 = RF_DEPTHHACK in first person (cg_weapons.c:2020) — beam never clips through the gun |
| `cg_lightningAngleOriginStyle` | cg_main.c:2308 | `1` | = | — |
| `cg_lightningSize` | cg_main.c:2310 | `8` | = | — |
| `cg_lightningImpact` / `Size` / `Cap` / `CapMin` / `Project` | cg_main.c:2300-2305 | `1 / 1.0 / 192 / 60 / 1` | = | Impact sparks at authentic scale. Reminder: cg_drawGun 0 preserves LG beam explicitly (cg_weapons.c:2800-2811) — clean profile unaffected |
| `cg_fxLightningGunImpactFps` | cg_main.c:2397 | `125` | = | — |

### 1.12 Rocket trail / explosions / smoke

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_smokeRadius_RL` | cg_main.c:1821 | `64` | = 64 | Full rocket smoke — trails ARE the choreography of a rocket fight |
| `cg_smokeRadius_GL` | cg_main.c:1819 | `32` | = | — |
| `cg_smokeRadius_SG` / `_NG` / `_PL` | cg_main.c:1818/1820/1822 | `32/16/32` | = | — |
| `cg_noProjectileTrail` | cg_main.c:1834 | `0` | = 0 | Never strip trails |
| `cg_smokeRadius_breath/dust/flight/haste` | cg_main.c:1823-1828 | `16/24/8/8` | = | Ambient life |

### 1.13 Particles / marks / decals / shadows

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_marks` | cg_main.c:1600 | `1` | = 1 (in _QUALITY) | Burn marks tell the fight's history |
| `cg_markTime` | cg_main.c:1601 | `10000` | **20000** | Marks persisting through a 15-20s clip = battle-scarred arena (classic movie-cfg convention) |
| `cg_shadows` | cg_main.c:1385 | `1` | = 1 (in _QUALITY) | 1 = blob (stable); 2/3 stencil/projected are artifact-prone in gl1 — do not raise without a proof frame |

### 1.14 Audio confirmation (kept from V2 — source-verified)

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_hitBeep` | cg_main.c:1956 | `2` | = 2 (V2) | Hit confirmation audible (damage-pitch variant) |
| `cg_killBeep` | cg_main.c:2449 | `7` | **0** (V2) | Kill chime off — the frag message + medal carry it |
| `s_killBeepVolume` | client/snd_main.c:571 | `1.0` | **0** (V2) | Belt-and-suspenders with cg_killBeep 0 |

### 1.15 Motion blur (MME accumulation)

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `mme_blurFrames` | renderercommon/tr_mme.c:367 | `0` | **0** gameplay master / **8** cinematic (V2 already) | Accumulation blur only runs during `video` capture; blurFrames+blurOverlap <= BLURMAX (tr_mme.c:130-135). 8 sub-frames at 60fps ~ 180° shutter feel |
| `mme_blurType` | tr_mme.c:369 | `gaussian` | = gaussian | — |
| `mme_blurOverlap` | tr_mme.c:368 | `0` | = 0 | Rolling-window blend across output frames — leave off |
| `mme_blurJitter` | tr_mme.c:370 | `1` | = 1 | Sub-pixel jitter doubles as extra AA during accumulation |
| `mme_blurStrength` | tr_mme.c:371 | `0` | = | — |
| `cl_aviFrameRateDivider` | client (cl_main.c:6968 area) | `1` | = **1** | DECIMATION, not blur control (master_profile.py audit) — leave 1 |
| Interplay | — | — | — | Capture time scales linearly with blurFrames (8x slower). Gameplay masters stay blur-free (post pipeline owns speed ramps); blur belongs to TR4SH_CINEMATIC_REPLAY only |

### 1.16 AA / supersampling

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `r_useFbo` | renderergl1/tr_init.c:1974 | `0` | **1** (LAUNCH_SETS) | FBO path = MSAA in capture + structurally excludes external overlay contamination (NVIDIA toast finding) |
| `r_fboAntiAlias` | tr_init.c:1975 | `0` | **4** (LAUNCH_SETS) | 4x MSAA proven in bench; higher may silently cap (knowledge 05, glconfig note) |
| `r_ext_multisample` | tr_init.c:1816 | `0` | = 0 | Window-framebuffer MSAA — redundant/conflicting with the FBO path |
| True supersampling | — | — | not available | No SSAA cvar in this fork; only r_mode -1 + custom res + external downscale |

### 1.17 In-engine color / saturation / brightness

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `mme_saturation` | **NOT REGISTERED** | — | — | **UNVERIFIED — q3mme-only, absent from wolfcamql's tr_mme.c (verified: no hit in tree).** Saturation grading happens in our ffmpeg post pipeline, not in-engine |
| `r_mapOverBrightBits` | tr_init.c:1847 | `2` | = **2** (LATCH) | Wolfcam's default already matches the classic movie-cfg push (stock q3 was lower); raising to 3 clips highlights — verify only if a map reads flat |
| `r_mapOverBrightBitsValue` / `Cap` | tr_init.c:1848-1849 | `1.0 / 255` | = | Cap 255 prevents blowout |
| `r_overBrightBits` | tr_init.c:1818 | `1` | = 1 | With r_ignorehwgamma 1 this is baked into frames correctly |
| `r_gamma` | tr_init.c:1880 | `1` | = **1.0** | Neutral capture; grade in post (P1 render pipeline). r_ignorehwgamma 1 (LAUNCH_SETS) bakes software gamma into pixels — keep gamma neutral so masters are grade-clean |
| `r_intensity` | tr_init.c:1852 | `1` | = 1 (LATCH) | Texture brightness multiplier — >1 clips texel data permanently |
| `r_greyscale` / `r_mapGreyScale` | tr_init.c:1833/1836 | `0/0` | = 0 | Stylization belongs to post |
| `r_ignorehwgamma` | tr_init.c (1820 area) | `0` | **1** (LAUNCH_SETS) | Bakes gamma into captured pixels — deterministic across machines |

### 1.18 Console / notify suppression

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `con_notifytime` | client/cl_console.c:496 | `3` | **0** (V2) | No console lines bleeding into frames |
| `con_notifylines` | client/cl_console.c:497 | `3` | **0** (V2) | Both real, both needed |
| `cl_noprint` | client/cl_main.c:6950 | `0` | **1** (_QUALITY) | Suppresses print traffic entirely |
| `developer` | common | `0` | = 0 | — |
| `cg_chatTime` / `cg_chatLines` | cg_main.c:1977-1978 | `5000 / 10` | **0 / 0** (V2) | Chat area dark |

### 1.19 Scoreboard suppression (all REAL registered cvars + real draw gates)

| Cvar | Registered | Default | Rec | Draw-path gate |
|---|---|---|---|---|
| `cg_scoreBoardWhenDead` | cg_main.c:1945 | `1` | **0** (V2) | cg_draw.c:9586, 10957 — auto-scoreboard on death (CA!) |
| `cg_scoreBoardAtIntermission` | cg_main.c:1946 | `1` | **0** (V2) | cg_draw.c:9560, 9586, 10959 |
| `cg_scoreBoardWarmup` | cg_main.c:1947 | `1` | **0** (V2) | cg_draw.c:9565 |
| `cg_roundScoreBoard` | cg_main.c:2539 | `1` | **0** (V2) | cg_draw.c:10669 — CA round-end board |
| `cg_drawScores` | cg_main.c:1869 | `1` | **0** (V2) | cg_draw.c:5851 — persistent score strip |
| `cg_scoreBoardStyle` / `Old` / `SpectatorScroll` | cg_main.c:1943/1948/1944 | `1/0/0` | = | Irrelevant once suppressed |

### 1.20 Spectator / follow text & remaining HUD blocks

| Cvar | Registered | Default | Rec | Reason |
|---|---|---|---|---|
| `cg_drawFollowing` | cg_main.c:1902 | `1` | **0** (V2) | Gate cg_draw.c:9802 |
| `wolfcam_drawFollowing` | cg_main.c:2222 | `2` | **0** (V2) | Second, wolfcam-specific gate (cg_draw.c:1174) — BOTH must be 0 |
| `wolfcam_drawFollowingOnlyName` | cg_main.c:2223 | `0` | = | Moot at 0 |
| `cg_drawSpecMessages` | cg_main.c:2419 | `1` | **0** (V2) | — |
| `cg_drawStatus` | cg_main.c:1419 | `1` | **0** (V2) | Health/armor/ammo block off — recorder-first aesthetic |
| `cg_drawTimer` | cg_main.c:1421 | `1` | **0** (V2) | — |
| `cg_drawAmmoWarning` | cg_main.c:1479 | `1` | **0** (V2) | — |
| `cg_drawAttacker` | cg_main.c:1512 | `1` | **0** (V2) | — |
| `cg_lagometer` | cg_main.c:1605 | `1` | **0** (V2) | — |
| `cg_drawFPS` / `cg_drawSpeed` | cg_main.c:1448/1843 | `1/1` | **0/0** (V2) | — |
| `cg_weaponBar` / `cg_drawFullWeaponBar` | cg_main.c:1935/1942 | `1/1` | **0/0** (V2) | — |
| `cg_drawItemPickups` | cg_main.c:1885 | `3` | **0** (V2) | — |
| `cg_drawCenterPrint` | cg_main.c:1993 | `1` | **0** (V2) | Kills center kill-notices; safe now because the frag message moves to the Separate path (1.6) |
| `cg_drawTeamOverlay` | (registered; V2 verified) | — | **0** (V2) | — |
| `cg_drawFriend` | cg_main.c:1747 | `3` | **0** (V2) | Oversized friend sprites |
| `cg_drawPlayerNames` | cg_main.c:2286 | `0` | = 0 (V2) | — |
| `cg_drawVote` / `cg_drawTeamVote` | cg_main.c:2010 / (adjacent) | `1` | **0** (V2) | — |
| `cg_adShaderOverride` | cg_main.c:2466 | `0` | = 0 (V2) | Ads render with PANTHEON pack (zzz_pantheon_ads.pk3) |
| `cg_scorePlums` | cg_main.c:1794 | `1` | = 1 (verify) | Floating +score plums on frag — era-authentic QL flourish; verify it reads well, set 0 if it fights the frag message |

---

## 2. Proposed MOVIE_CANDIDATE_V3 — diff vs `_GAMEPLAY_MASTER_V2`

```python
# MOVIE_CANDIDATE_V3 = { **_GAMEPLAY_MASTER_V2, ... }   # changes only:

_V3_DIFF = {
    # --- FRAG MESSAGE: fix the too-large-text defect at its root -------------
    # V2 tuned cg_drawFragMessage* but left Separate=0, so the message rendered
    # through CENTER PRINT at cg_drawCenterPrintScale 0.35 (cg_draw.c:8234) --
    # or not at all once cg_drawCenterPrint was set 0. Flip to the dedicated
    # path (cg_draw.c:8340) where every styling cvar actually applies.
    "cg_drawFragMessageSeparate": 1,        # was absent (default 0)
    "cg_drawFragMessageScale": 0.22,        # was 0.28 -- tuned for the REAL path
    "cg_drawFragMessageIconScale": 1.2,     # new -- match obituary icon weight

    # --- REWARDS: keep the candy, shrink the arcade -------------------------
    "cg_drawRewardsImageScale": 0.8,        # new (default 1.0) -- premium scale
    "cg_drawRewardsTime": 2000,             # new (default 3000) -- on, gone
    "cg_drawRewardsMax": 3,                 # new (default 10) -- cap medal spam
    "cg_drawRewardsFadeTime": 250,          # new -- match frag message fade

    # --- LIFELIKE CAMERA: restore the classic Q3 gait -----------------------
    # wolfcam ships all bob at 0 (competitive convention); the q3 values are
    # preserved as comments at cg_main.c:1642-1644. Subtle bob = filmed-from-
    # the-eyes feel of the Q3MME era. VERIFY with A/B strafe capture first.
    "cg_bobup": 0.005,                      # was 0 (default 0)
    "cg_bobpitch": 0.002,                   # was 0
    "cg_bobroll": 0.002,                    # was 0

    # --- WORLD PERSISTENCE ---------------------------------------------------
    "cg_markTime": 20000,                   # new (default 10000) -- scarred arena
    "cg_railTrailTime": 600,                # new (default 400) -- beam registers
                                            # on 60fps cuts; cinematic stays 1200

    # --- DAMAGE FEEDBACK: felt, not blinding --------------------------------
    "cg_screenDamageAlpha": 120,            # new (default 200) -- protect grade
    "cg_screenDamageAlpha_Team": 120,       # new (default 200)

    # --- FREECAM HYGIENE (cinematic/replay captures share the cfg) ----------
    "cg_freecam_crosshair": 0,              # new (default 1)
}
```

Everything else in `_GAMEPLAY_MASTER_V2` survives review unchanged: FOV 110, dot crosshair
25/24/white/255, visible gun at origin, obituary 2500/600/stack 3/icon 1.2, hit beep 2 +
kill beep 0, de-gaming block (`cg_enemyModel ""` overriding wolfcam's **default `keel/bright`**),
full scoreboard/follow/notify suppression (all verified as real cvars with real draw gates),
and the _QUALITY + LAUNCH_SETS render stack (FBO+4xMSAA, picmip 0, mapOverBrightBits 2,
dynamiclight 1, marks 1, shadows 1).

---

## 3. Verify Empirically (5s bisect captures)

Ordered by risk of surprising interaction:

1. **`cg_drawFragMessageSeparate 1` + scale 0.22** — confirm the message appears at all with
   `cg_drawCenterPrint 0`, at the tuned position/size; check overlap with rewards at Y 56 vs frag msg Y 110.
2. **Bob triplet 0.005/0.002/0.002** — A/B strafe-run capture vs bob 0. Reject if it reads
   like camera wobble at 110 FOV (bob amplitude scales with speed; CPMA-era players ran higher).
3. **`cg_screenDamageAlpha 120`** — rocket-spam CA round; confirm red never dominates a frame.
4. **`cg_railTrailTime 600`** — rail duel clip; confirm beams don't stack into decor with 2+ rails/sec.
5. **`cg_markTime 20000`** — long CA round; confirm no decal z-fighting shimmer under MSAA.
6. **`cg_drawRewardsImageScale 0.8` / Max 3** — multi-frag run; confirm medal stack behavior.
7. **`cg_scorePlums`** (currently default 1) — decide keep/kill after seeing it next to the frag message.
8. **`cg_fovStyle 1`** (unchanged) — one frame vs style 0 and 2 to document projection choice;
   any change invalidates screen-space measurements shared with ANALYSIS_HEADLESS.
9. **Frag-message FreeType upgrade** (optional round 2): `cg_drawFragMessageFont` + PointSize 32,
   scale re-tuned — only if the default textFont rasters soft at scale 0.22 on 1080p.
10. **`cg_obituary` position** — if the feed must move, it needs a qlhud .menu rect edit
    (no X/Y cvar exists); prototype the rect before committing to a HUD file.

## 4. UNVERIFIED — not registered in this fork; excluded from V3

| Name | Finding |
|---|---|
| `mme_saturation` | q3mme-only; absent from wolfcam's tr_mme.c registrations (tr_mme.c:367-382 is the full list) |
| `cg_gunFovOffset` | No registration anywhere in cgame |
| `cg_runpitch` / `cg_runroll` | Stock-Q3 cvars, removed from this fork's cg_main.c |
| `cg_gunBob*` family | Does not exist; gun sway is selected by cg_drawGun value (1 sway / 2 static) |
| `cg_viewKick` | Real control is `cg_kickScale` (cg_main.c:2413, default 0) |
| `cg_oldRail` | Registration commented out (cg_main.c:1836) |
| `cg_brightSkins` | Bright skins are model-string suffixes (`keel/bright`), not a cvar |
| `cg_obituaryX/Y` | No such cvars — killfeed position is the qlhud ownerdraw rect (cg_newdraw.c:5960) |

## 5. Secondary sources (web)

Community wolfcam movie-cfg references consulted for conventions (picmip 0, HUD-off,
overbright push, high-fps capture): [KittenIgnition's WolfcamQL movie configs (ESR)](https://esreality.com/post/2199387/wolfcamql-movie-configs/),
[ESR "Wolfcam movie cfg" thread](https://www.esreality.com/index.php?a=post&id=2127768),
[brugal/wolfcamql README](https://github.com/brugal/wolfcamql/blob/master/README-wolfcam.txt),
[entdark/q3mme (mme_* reference — confirms saturation is q3mme-side)](https://github.com/entdark/q3mme),
[Gamingcfg WolfcamQL configs](https://www.gamingcfg.com/config/WolfcamQL).
Local source always wins over web claims; every recommendation in §2 is registration-verified.
