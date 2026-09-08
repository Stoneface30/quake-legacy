# Wolfcam command verification for implementation handoff

Date: 2026-09-05. Read-only source audit; no engine launch, captures, installs or binary modifications. All paths below are repository-relative; line numbers refer to the inspected checkout. Source-supported does **not** mean runtime-proven.

## Version boundary

The configured capture backend is **11.3**: `creative_suite/engine/wolfcam_capture.py:39`, executable copy at `:103`, matching DLL copies at `:116`; `render_profile.py:50` agrees. `master_profile.py:45` labels it `11.3+laa`. Existing staging is reused at `wolfcam_capture.py:90`, so these constants alone do not authenticate the installed executable. Hash the staged EXE and cgame DLL against the intended archive before a future proof.

The inspected canonical source identifies itself as **12.7test49** (`engine/engines/_canonical/version.txt:1`). `engine/engines/_manifest/canonical_map.json` assigns `code/cgame/cg_consolecmds.c`, `cg_main.c`, `wolfcam_consolecmds.c`, and `code/client/cl_main.c` to `wolfcamql-src`, with no `wolfcamql-local-src` entry for those files. Canonical selection deliberately prioritizes that upstream tree (`_manifest/build_canonical.py:11`). Thus it is invalid to equate these registrations with an exact 11.3 build audit.

`docs/reference/model_animation_path.md:102` correctly distinguishes newer IQM source support from the 11.3 binary. Its reported prior binary string scan at `:138` was not repeated here; an absent string is supporting evidence, not a substitute for a loader trial. Its older Python line references have drifted. Do not upgrade engines or promise IQM playback from this audit.

## Source-supported inventory

For compact citations, C = `engine/engines/_canonical/code/cgame/cg_consolecmds.c`, M = `engine/engines/_canonical/code/cgame/cg_main.c`, L = `engine/engines/_canonical/code/client/cl_main.c`.

| Intent | Exact registered names and evidence | Qualification |
|---|---|---|
| Raw demo seek/capture | `seekservertime`, `seek`, `pause` (L:7184,7185,7189); `video`, `stopvideo` (L:7174); `cl_aviFrameRate` (L:6968); `cl_freezeDemo` (L:6961) | Current Python emits `seekservertime <ms>`, `at <ms> video avi name <safe-name>`, then `stopvideo` (`wolfcam_capture.py:173`). Mock capture is not proof of these commands. |
| Scheduling | `at`, `listat`, `clearat` (C:8546); `cg_enableAtCommands` (M:2460) | Use raw server milliseconds for project windows, not CA display clock. `cgamepostinit.cfg` is executed in `cg_snapshot.c:1710`; current Python writes that hook at `wolfcam_capture.py:185`. |
| POV | `follow` (C:8471), `freecam`, `setviewpos`, `setviewangles` (C:8478) | Follow implementation recognizes `killer`, `victim`, and `-1` (`wolfcam_consolecmds.c:169`). POV visibility remains limited by recorded snapshot information. |
| Camera targeting | `view` (C:8490), `chase` (C:8509) | These are camera primitives, not newly reconstructed world data. |
| Camera paths | `playcamera`, `stopcamera`, `loadcamera` (C:8512–8516) | Camera format version is 10 (`cg_camera.h:7`); save/load builds `.cam%d` paths (C:2255,2427). Python's `write_engine_file` documents LF-only camera output (`wolfcam_capture.py:53`). |
| Entity hold / materials | `entityfreeze` (C:8554), `remapshader` (C:8571) | Registration proves neither a complete time-freeze cinematic nor a safe automatic material treatment. |
| Smooth control | `cvarinterp` (C:8564) | Handler at C:7244 explicitly takes **seconds**, optional `real`/`game`; multiplies duration by 1000 internally. Default game clock. A live continuous cvar must be proven separately; latched/discrete controls cannot be assumed smooth. |
| Enemy/team presentation | `cg_enemyModel`, `cg_teamModel` (M:2096,2112); `cg_enemyHeadColor`, `cg_enemyTorsoColor`, `cg_enemyLegsColor` (M:2101); corresponding `cg_team*Color` (M:2117) | Color/model selection depends on POV/team context and available model skins. Verify both sides in the intended POV. |
| Through-wall overlay | `cg_wh` (M:2074) | `cg_players.c:4324` implements overlay, `:4356` adds `RF_DEPTHHACK`; mode 2 filters to enemies and mode 3 filters enemies out (`:4331,4344`). Uses `wc/wallhack` registered at M:3963. This is a concrete candidate for x-ray, **not a runtime-proven shot**. |

## HUD privacy candidates

Source registers `cg_draw2D` (M:1418), `cg_drawCrosshairNames` (M:1531), `cg_drawTeamOverlay` (M:1692), `cg_drawFriend` (M:1747), `cg_drawFollowing` (M:1902), `cg_drawCenterPrint` (M:1993), `wolfcam_drawFollowing` (M:2222), `cg_drawFragMessageTime` (M:2261), `cg_obituaryTime` (M:2276), `cg_drawPlayerNames` (M:2286), and `cg_drawSpecMessages` (M:2419). Disabling these is a source-grounded starting point, not a complete privacy guarantee. Frag-message and obituary gates are durations, not invented boolean names. Review frames and logs locally before sharing; overlays, scoreboards, console and sound may still disclose identity. Current master-profile code contains identity-bearing frag-token settings; do not blindly reuse a review preset for public proof.

Speed readout is `cg_drawSpeed` (M:1843). Do not borrow q3mme's `cg_drawSpeedometer*` family into Wolfcam; this directly follows Vault rule L-ENG-6.

## Reconciliation of existing documents

- `wolfcam-commands.md:548,605` incorrectly labels `cvarinterp` duration milliseconds and gives `2000` for a short ramp. Handler evidence says **seconds**; a two-second test is `cvarinterp timescale 1 0.1 2 real`.
- `wolfcam-commands.md:270` names `.cam8`; current canonical camera version is 10. Confirm the installed binary's format before relying on newer camera fields.
- `engine_moviemaking_commands.md:1` says “what wolfcamql 11.3 actually offers,” but `:3` cites the canonical newer tree. Its explicit source-only caveat at `:5` should govern every feature claim; heading is stronger than its evidence.
- Current automation uses `cgamepostinit.cfg` and raw server-time windows, whereas the older inventory foregrounds `gamestart.cfg` and game clock. Keep older patterns as historical/reference patterns, not a replacement for the current capture contract.

## Next tiny proof, after user authorization

1. Record local EXE and cgame DLL hashes plus console version. In an existing reviewed demo, inspect `cmdlist` and `cvarlist` locally. A console accepting `set nonexistent 1` proves nothing. Do not publish raw lists containing identifiers.
2. In one authorized, sanitized short window, compare `cg_wh 0` against `cg_wh 2` with identical POV, timestamp and camera; show one enemy occluded by a wall and a visible teammate. If both frames are identical, report unsupported/unproven rather than shipping a label that says x-ray.
3. Query `servertime`, apply `seekservertime <approved_start_ms>`, then inspect `listat` after scheduling a harmless `at <approved_ms> echo PROOF_MARKER`. Verify timestamp behavior before capture. Placeholder timestamps must be replaced from an approved existing window.
4. Independently validate `cvarinterp` with one live control and a two-second real-clock interval; independently test camera load/play and freeze behavior. Only then schedule a single tiny `video avi name proof_001` / `stopvideo` run through the existing cancel-safe worker. Never batch, overwrite approved outputs, or modify Steam paks as part of this proof.

No claim in this report establishes installed-binary feature availability or visual quality. It supplies exact candidate names and source evidence for bounded runtime validation.

## Machine-readable registration inventory

`2026-09-05-engine-registrations.csv` contains **2222 source registration rows** from the explicitly scoped files below. Names repeated at distinct file/line locations remain separate. Comments were excluded; conditional compilation was not evaluated. Literal table entries and `Cvar_Get`, `Cmd_AddCommand`, `trap_AddCommand` calls were extracted; computed names, other files and runtime-only registrations are outside scope. Command completion registrations (`trap_AddCommand`) do not independently prove an executable handler. This is not an exhaustive binary inventory.

| Source file | Rows |
|---|---:|
| `engine/engines/_canonical/code/cgame/cg_consolecmds.c` | 203 |
| `engine/engines/_canonical/code/cgame/cg_main.c` | 1038 |
| `engine/engines/_canonical/code/client/cl_main.c` | 151 |
| `engine/engines/_canonical/code/renderergl1/tr_init.c` | 170 |
| `engine/engines/_canonical/code/renderergl2/tr_init.c` | 229 |
| `engine/engines/_forks/q3mme/trunk/code/cgame/cg_consolecmds.c` | 52 |
| `engine/engines/_forks/q3mme/trunk/code/cgame/cg_main.c` | 149 |
| `engine/engines/_forks/q3mme/trunk/code/client/cl_main.c` | 97 |
| `engine/engines/_forks/q3mme/trunk/code/renderer/tr_init.c` | 133 |

The q3mme cgame command table is `engine/engines/_forks/q3mme/trunk/code/cgame/cg_consolecmds.c`; client registrations are in its `code/client/cl_main.c`. Its version macro is `code/game/q_shared.h:29` (`1.9`); this identifies source, not an installed q3mme executable. Renderer-specific registrations are deliberately separated from Wolfcam. **Runtime `cmdlist`, `cvarlist`, and captured on/off proofs remain pending.**
