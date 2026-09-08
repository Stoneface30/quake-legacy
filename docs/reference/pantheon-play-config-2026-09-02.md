# PANTHEON Quake Live Play Configuration — 2026-09-02

## Outcome

The live Quake Live configuration now loads `pantheon_play.cfg` as its final
effective command. The profile is tuned for the detected 240 Hz Alienware
AW2521HF, RTX 5060 Ti, enabled G-Sync Compatible mode, and wired Ethernet.

All existing keybinds, weapon sensitivities, weapon FOVs, and per-weapon
crosshairs remain in the original `autoexec.cfg` and were not changed.

## Change table

| Area | Previous | New | Reason |
|---|---|---|---|
| Download rate | `rate 25000` | `rate 25000` | Retains Quake Live's useful retail ceiling. |
| Server snapshots | Unspecified (engine default `20`) | `snaps 20` | Restores the engine default. Bundled engine documentation warns that 40 commonly reaches the rate limit faster; the live 8-player CA test showed local 999 while the followed player remained smooth. |
| Command packets | Unspecified (engine default `30`) | `cl_maxPackets 30` | Restores the known-working engine default after the live profile produced local 999 interruptions at 125. Higher packet cadence is not useful when it destabilizes the actual route/server combination. |
| Packet redundancy | `cl_packetdup 1` | `cl_packetdup 1` | Retains one older command for resilience to isolated packet loss. |
| Visual time nudge | `cl_timeNudge -10` | `cl_timeNudge 0` | Removes extrapolation; time nudge does not improve server hit registration. |
| Prediction | Implicit/default | Explicitly enabled | Keeps local movement and item prediction active. |
| Mouse input | Raw, no filter/accel | Preserved explicitly | Maintains direct input without changing personal sensitivity. |
| FPS cap | `com_maxfps 140` | `com_maxfps 250` | Replaces the stale 144 Hz-era cap and increases input-frame opportunities. |
| Display refresh | `r_displayRefresh 144` | `r_displayRefresh 240` | Matches the detected AW2521HF mode. |
| In-game VSync | Off | Off | Avoids the engine's swap-interval latency; NVIDIA VRR remains enabled. |
| Picmip | `r_picmip 6` | `r_picmip 6` | Preserves the preferred low-detail visual style. |
| Texture filtering | Trilinear | Bilinear with nearest mip | Removes the blended/smeared transition between already reduced mip levels. |
| World lighting | Vertex lighting | Vertex lighting | Restored after the live recording showed lightmaps were too dark for this competitive profile. |
| Fullbright | Ambiguous `0.5` | `0` | Removes a conflicting fractional value and preserves model/background contrast. |
| Map overbright | `6` | `2` | Brightens the world while avoiding the old extreme value. |
| Texture intensity | `2` | `2` | Restores the brighter texture response requested in the live review. |
| Gamma | `0.5` | `1.25` | Produces controlled brightness without the previous contradictory stack. |
| Self model | `xaero/sport_blue`, Visor head | `xaero/bright` | Uses the requested bright/white Xaero identity. |
| Enemy model | Keel bright, dark-green tint | Keel bright, full-green `0x00FF00FF` | Makes every enemy body region the brightest pure green available through the colour cvars. |
| Team model | Forced Crash | Sarge default | Uses the requested team model without forced team-colour overrides. |
| Alternate team | None | `vstr team_doom` | Provides Doom without editing the profile. |
| LG orientation | `cg_trueLightning 1` | Preserved | Keeps the local shaft aligned to the immediate view angle. |
| LG artwork | Thin style 4 | Clean default style 1 | Removes the animated/shiny thin-shaft presentation suspected of looking delayed. |
| LG impact/sparks | Disabled | Disabled | Keeps the target and beam endpoint unobscured. |
| Spark lifetime | `1000 ms` | `250 ms` | Normalizes the dormant value in case sparks are enabled later. |
| Muzzle flash | Disabled | Disabled | Preserves the uncluttered weapon view. |
| Marks | Enabled for `10000 ms` | Disabled | Removes persistent impact clutter. |
| Sound mix-ahead | `140 ms` | `140 ms` | Preserves the known-working device buffer after the 50 ms live test produced effectively silent captured audio (`−73.9 dB` mean). |

## Runtime switches

```cfg
vstr team_sarge
vstr team_doom
vstr shaft_clean
vstr shaft_thin
vstr audio_fast
vstr audio_safe
```

## Recovery

The three pre-change configuration files are stored in a timestamped
`baseq3/backups/pantheon-2026-09-02-1538/` directory. Restoring its
`autoexec.cfg` removes the final profile loader and returns the prior behavior.

## Verification boundary

Static verification confirms the load order, preserved controls, retail binary
cvar names, and required model assets. A 2026-09-03 gameplay recording then
validated the reported dark rendering. During its `999` interruption the local
client was spectating a player who remained smooth; comparison with the original
configuration isolated the newly forced `snaps 40`, so the engine-default 20 was
restored. The remaining human checks are the revised brightness, network
stability, and restored game sound after a full restart or `snd_restart`.
