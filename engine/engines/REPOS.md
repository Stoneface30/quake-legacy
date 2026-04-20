# Quake Legacy Source Knowledge Base
*Generated: 2026-04-16, relocated 2026-04-17*
*Purpose: Reference repos for QUAKE LEGACY fragmovie automation project*

> **MOVED 2026-04-17:** All engine source trees were consolidated into
> `G:/QUAKE_LEGACY/engine/engines/` via SHA-256 dedup:
> - Canonical tree (unique files): `engine/engines/_canonical/`
> - Near-duplicate variants (per-tree): `engine/engines/<tree>/`
> - Inventory + stats: `engine/engines/_manifest/`
> - Per-file diffs: `engine/engines/_diffs/`
> - Family tree + migration notes: `engine/engines/SYNTHESIS.md`
>
> Nothing has been lost — every file below is still present in `_canonical/` or
> in the per-tree variant dir. 141 MB of build artifacts and exact-duplicate
> files were freed. See `_manifest/DELETE_READY.md` for the deletion record.

---

## Repository Index

### 1. quake3-source — id Software Quake III Arena (Official)
**Origin:** `https://github.com/id-Software/Quake-III-Arena` (shallow clone)
**Size:** ~31 MB

**Purpose in project:**
The ground truth for the Q3 demo protocol, network message format, and Huffman compression. All demo parsers ultimately derive from this code. Essential reading before touching any demo format work.

**Key files to study:**
- `code/qcommon/huffman.c` — Huffman codec used to compress demo bitstream. Every byte in a .dm_73 file is encoded with this algorithm.
- `code/qcommon/msg.c` — MSG_* functions that serialize/deserialize network messages (entity states, player states, commands). The demo format IS the network protocol recorded to disk.
- `code/client/cl_demo.c` — Demo recording and playback on the client side.
- `code/server/sv_demo.c` — Server-side demo writing.
- `code/qcommon/common.h` — Entity state field definitions, playerState_t, snapshot_t structures.

---

### 2. ioquake3 — Community Q3 Port
**Origin:** `https://github.com/ioquake/ioq3` (shallow clone)
**Size:** ~40 MB

**Purpose in project:**
The best-documented Q3 codebase. Has the same demo format as the original but with cleaner, more readable code and important additions like AVI video output. The cl_avi.c file is the reference implementation for video capture automation.

**Key files to study:**
- `code/client/cl_avi.c` — AVI video capture implementation. Shows exactly how frames are dumped from the renderer to disk. Reference for automating wolfcamql's video output.
- `code/qcommon/huffman.c` — Cleaner version of the Huffman codec (same algorithm).
- `code/client/cl_demo.c` — Demo playback with additional error handling.
- `code/renderer/tr_main.c` — Renderer frame submission — understand where cl_avi hooks in.

---

### 3. wolfcamql-src — WolfcamQL Demo Player (GitHub)
**Origin:** `https://github.com/brugal/wolfcamql` (shallow clone)
**Size:** ~127 MB

**Purpose in project:**
Our primary rendering engine for fragmovie production. Need to understand its internals to automate demo playback, video capture, and camera scripting via command-line or config injection.

**Key files to study:**
- `code/cgame/wolfcam_main.c` — Core wolfcam logic, demo loading entry point.
- `code/cgame/wolfcam_consolecmds.c` — All custom console commands added by wolfcam. Command list for automation scripts.
- `code/cgame/wolfcam_servercmds.c` — Server command handling (score events, configstrings).
- `code/cgame/wolfcam_ents.c` — Entity rendering customizations (model overrides, effects).
- `code/cgame/cg_fx_scripts.c` — FX scripting system for visual effects automation.
- `code/client/cl_avi.c` / `cl_avi.h` — AVI capture (inherited from ioquake3, may have wolfcam patches).

---

### 4. wolfcamql-local-src — WolfcamQL (Exact Installed Version)
**Origin:** Extracted from `G:\QUAKE LEGACY\WOLF WHISPERER\WolfcamQL\wolfcamql-src.tar.gz`
**Size:** ~19 MB (tarball date: 2016-08-13)

**Purpose in project:**
The exact source that matches the `wolfcamql.exe` binary currently installed. Use this — NOT wolfcamql-src — when debugging behavior of the actual executable or when exact command/cvar names matter. Differences from the GitHub repo reveal local patches.

**Key files to study:**
- Same file structure as `wolfcamql-src` above.
- Compare `code/cgame/wolfcam_main.c` between this and wolfcamql-src to find local patches.
- Check `code/client/cl_avi.c` for any AVI format or timing changes.

---

### 5. q3mme — Quake 3 Movie Maker's Edition
**Origin:** `https://github.com/entdark/q3mme` (shallow clone)
**Size:** ~70 MB

**Purpose in project:**
Reference implementation for advanced fragmovie features: motion blur, depth-of-field, FOV animation, camera path scripting, demo cutting, and HUD control. These systems are what wolfcamql was originally inspired by and partially implements.

**Key files to study:**
- `trunk/code/cgame/cg_demos_camera.c` — Camera path splines, keyframe interpolation. Reference for smooth camera automation.
- `trunk/code/cgame/cg_demos_capture.c` — Frame capture pipeline: multi-sample, motion blur accumulation buffer.
- `trunk/code/cgame/cg_demos_dof.c` — Depth-of-field blur implementation.
- `trunk/code/cgame/cg_demos_effects.c` — Per-demo visual effects system.
- `trunk/code/cgame/cg_demos_cut.c` — Demo cut/trim logic (start/end frame selection).
- `trunk/code/cgame/cg_demos_fov.c` — Dynamic FOV control.
- `trunk/code/cgame/cg_demos_hud.c` — HUD visibility scripting.
- `trunk/code/cgame/cg_demos.c` / `cg_demos.h` — Core demo scripting engine.

---

### 6. uberdemotools — C++ Demo Parser + JSON Exporter
**Origin:** `https://github.com/mightycow/uberdemotools` (FULL clone)
**Size:** ~619 MB (includes pre-built binaries and test demo files)

**Purpose in project:**
PRIMARY Phase 2 tool. Parses .dm_73 demos and extracts structured data (frags, captures, chat, player positions) as JSON. The `app_demo_json.cpp` and `analysis_obituaries.cpp` are the core of our frag extraction pipeline.

**Key files to study:**
- `UDT_DLL/include/uberdemotools.h` — Public C API. All integration starts here.
- `UDT_DLL/src/apps/app_demo_json.cpp` — Full demo-to-JSON export. Maps all demo events to JSON objects.
- `UDT_DLL/src/analysis_obituaries.cpp` — Frag/kill event extraction. The kill feed parser.
- `UDT_DLL/src/analysis_pattern_frag_run.cpp` — Multi-frag sequence detection ("frag run" patterns).
- `UDT_DLL/src/analysis_pattern_mid_air.cpp` — Mid-air rocket/rail kill detection.
- `UDT_DLL/src/analysis_pattern_multi_rail.cpp` — Multi-rail (two kills one rail) detection.
- `UDT_DLL/src/analysis_captures.cpp` — CTF flag capture events.
- `UDT_DLL/src/api.cpp` — Core API implementation connecting all analysis modules.
- `research/Huffman/huffman.cpp` — Reference Huffman implementation with explanatory comments.
- `TECHNICAL_NOTES.md` — Protocol documentation. READ THIS FIRST.
- `CUSTOM_PARSING.md` — Guide for extending the parser with custom event handlers.

---

### 7. qldemo-python — Python .dm_73 Parser
**Origin:** `https://github.com/Quakecon/qldemo-python` (FULL clone)
**Size:** ~419 KB

**Purpose in project:**
PRIMARY Phase 2 parsing tool. Pure Python parser for Quake Live .dm_73 demo files. Handles the QL-specific protocol extensions on top of Q3. `qldemo2json.py` is the immediate-use script for extracting demo data.

**Key files to study:**
- `qldemo/` — Parser library package. The core protocol implementation.
- `huffman/` — Python Huffman module (likely C extension for speed).
- `qldemo2json.py` — Demo to JSON conversion script. Entry point for Phase 2 pipeline.
- `qldemosummary.py` — Summarize demo metadata (players, scores, map, duration).

---

### 8. demodumper — Python Demo JSON Dumper
**Origin:** `https://github.com/syncore/demodumper` (FULL clone)
**Size:** ~340 KB

**Purpose in project:**
Companion to qldemo-python. Handles all score command formats and edge cases that qldemo-python may miss. Particularly useful for extracting warmup vs. match data and handling malformed demos gracefully.

**Key files to study:**
- `demodumper.py` — Main entry point. Handles all score command format variants.
- `qldemo/` — May include patches to the base qldemo-python parser.
- `NOTE` — Read first — documents known quirks and limitations.

---

### 9. quake3e — Modern Q3 Fork (Vulkan Renderer)
**Origin:** `https://github.com/ec-/Quake3e` (shallow clone)
**Size:** ~79 MB

**Purpose in project:**
Reference for modern capture pipeline. Quake3e has a Vulkan renderer and improved video capture (native mp4/webm via ffmpeg integration). Useful if wolfcamql's AVI pipeline proves too slow or limited for high-quality output.

**Key files to study:**
- `code/renderer/` — Vulkan renderer implementation. Compare with wolfcamql's OpenGL renderer to understand capture hooks.
- `docs/` — Configuration documentation for video capture options.
- `CMakeLists.txt` — Build system reference (wolfcamql uses Makefile — compare).

---

## Size Summary

| Repo | Size | Clone Type |
|---|---|---|
| quake3-source | 31 MB | Shallow |
| ioquake3 | 40 MB | Shallow |
| wolfcamql-src | 127 MB | Shallow |
| wolfcamql-local-src | 19 MB | Tarball extract |
| q3mme | 70 MB | Shallow |
| uberdemotools | 619 MB | Full |
| qldemo-python | <1 MB | Full |
| demodumper | <1 MB | Full |
| quake3e | 79 MB | Shallow |
| **TOTAL** | **~986 MB** | |

---

## Study Order for Phase 2 (Demo Parsing)

1. **Start here:** `quake3-source/code/qcommon/huffman.c` + `msg.c` — understand the wire format
2. **Then:** `uberdemotools/TECHNICAL_NOTES.md` + `CUSTOM_PARSING.md` — highest-quality protocol docs
3. **Then:** `qldemo-python/qldemo/` — Python implementation you'll modify
4. **Then:** `demodumper/demodumper.py` — cross-reference for score format handling
5. **Frag extraction:** `uberdemotools/UDT_DLL/src/analysis_obituaries.cpp` + `analysis_pattern_*.cpp`

## Study Order for Phase 3 (Rendering Automation)

1. **Start here:** `wolfcamql-local-src/code/cgame/wolfcam_consolecmds.c` — full command list
2. **Then:** `wolfcamql-local-src/code/cgame/wolfcam_main.c` — demo loading and playback loop
3. **Then:** `q3mme/trunk/code/cgame/cg_demos_camera.c` — camera scripting reference
4. **Then:** `ioquake3/code/client/cl_avi.c` — AVI capture reference
5. **Reference:** `quake3e/code/renderer/` — modern capture pipeline if needed

---

## Phase 2 Downloads
*Cloned: 2026-04-16 — idtech engine lineage, tooling, and asset-open forks*

### 10. quake1-source — id Software Quake 1 (idtech1, GPL)
**Origin:** `https://github.com/id-Software/Quake` (shallow, ~16 MB)

**Why it's here:**
The root of the lineage. idtech1 established the renderer architecture, BSP world format, and client/server split that every subsequent id engine inherits. Useful for understanding how the entity event system and obituary detection originated — the EV_OBITUARY pattern in Q3/QL traces directly back here. Also reference for the NIN soundtrack integration (Quake 1 music was NIN, directly relevant to Phase 1 music catalog).

**Key files:**
- `WinQuake/` — Windows renderer + sound, shows original BSP loading
- `Quake/world.c` — Entity/physics world state management (ancestor of Q3's entity system)
- `Quake/sv_main.c` — Server loop origin

---

### 11. quake2-source — id Software Quake 2 (idtech2, GPL)
**Origin:** `https://github.com/id-Software/Quake-2` (shallow, ~8 MB)

**Why it's here:**
Direct ancestor of Q3. idtech2 introduced the modular renderer (ref_gl/), the game DLL split, and refined the network protocol that Q3 evolved into the .dm_73 format. The game/g_combat.c kill/damage logic is the lineage ancestor of Q3's obituary system. Sonic Mayhem composed the Q2 soundtrack — relevant for Phase 1 music licensing research.

**Key files:**
- `ref_gl/` — OpenGL renderer (direct ancestor of Q3's renderer)
- `game/g_combat.c` — Damage/kill logic, origin of MOD_* constants
- `qcommon/net_chan.c` — Network channel, ancestor of Q3's demo protocol
- `client/cl_demo.c` — Demo recording (compare with Q3's version to trace format evolution)

---

### 12. openarena-gamecode — OpenArena Game Logic (CC-licensed assets)
**Origin:** `https://github.com/OpenArena/gamecode` (shallow, ~8.5 MB)

**Why it's here:**
OpenArena is a Q3A fork with fully open-licensed assets (CC-BY-SA weapon models, textures, sounds). If Phase 4 (public CLI tool) needs bundled assets for testing or default visuals, OpenArena's assets are legally redistributable. The gamecode also shows how community forks extend Q3's weapon/item system — useful for understanding alternate MOD_* weapon constants seen in non-standard QL mods.

**Key files:**
- `code/game/g_combat.c` — Kill/damage system with OpenArena weapon additions
- `code/game/g_weapon.c` — Weapon fire logic
- `code/game/bg_misc.c` — Item/powerup definitions

---

### 13. openarena-engine — OpenArena Engine Fork
**Origin:** `https://github.com/OpenArena/engine` (shallow, ~36 MB)

**Why it's here:**
Engine companion to openarena-gamecode. Contains renderer and client patches on top of ioquake3. Useful as a second reference point for AVI capture and demo playback modifications — shows what community maintained Q3 engines look like vs. wolfcamql's approach.

**Key files:**
- `code/client/cl_avi.c` — AVI capture (compare with ioquake3 and wolfcamql versions)
- `code/renderer/` — Renderer modifications
- `code/client/cl_demo.c` — Demo playback patches

---

### 14. wolfet-source — Wolfenstein: Enemy Territory (idtech3, GPL)
**Origin:** `https://github.com/id-Software/Enemy-Territory` (shallow, ~33 MB)

**Why it's here:**
GPL release of another idtech3 derivative (same engine family as Q3/QL). ET added significant multiplayer features: class system, objective modes, and extended network protocol. The renderer and client code is structurally identical to Q3 but with additional features. Useful for cross-referencing wolfcamql internals — wolfcam originally started as an ET modification before being ported to QL.

**Key files:**
- `src/cgame/` — Client game module (compare structure with wolfcamql's cgame)
- `src/client/cl_avi.c` — AVI capture in ET variant
- `src/renderer/` — idtech3 renderer in ET form
- `src/game/g_combat.c` — Combat/kill system (ET variant of Q3's)

---

### 15. q3vm — Quake 3 QVM Bytecode Compiler/Assembler
**Origin:** `https://github.com/jnz/q3vm` (shallow, ~2.7 MB)

**Why it's here:**
WolfcamQL's game logic runs as compiled .qvm bytecode (the cgame.qvm). Understanding how .qvm files are structured is essential for Phase 3 automation — specifically for injecting custom commands or understanding how wolfcam's cgame module loads and executes. q3vm documents the QVM instruction set, calling conventions, and syscall interface that all cgame modules use.

**Key files:**
- `src/vm.c` — QVM interpreter implementation
- `src/vm_x86.c` — x86 JIT compiler for QVM
- `README.md` — QVM architecture overview
- `tools/` — Assembler and disassembler tools (useful for RE of cgame.qvm)

---

### 16. gtkradiant — Q3BSP Level Editor (GPL)
**Origin:** `https://github.com/TTimo/GtkRadiant` (shallow, ~57 MB)

**Why it's here:**
The authoritative reference for Q3's BSP map format. Phase 3 AI cinematography needs to reason about map geometry (spawn points, routes, sightlines) to generate intelligent camera paths. GtkRadiant's map compiler (q3map2) and its BSP loading code document every field of the .bsp format. Also contains the Q3 shader system spec — relevant if Phase 4 does any map-aware rendering.

**Key files:**
- `tools/quake3/q3map2/` — Q3MAP2 BSP compiler (full BSP format implementation)
- `radiant/` — Editor core (BSP entity parsing)
- `docs/` — BSP format documentation
- `include/` — Shared BSP structure definitions

---

### 17. darkplaces — DarkPlaces (Modern idtech1 Engine)
**Origin:** `https://github.com/DarkPlacesEngine/darkplaces` (shallow, ~11 MB)

**Why it's here:**
Shows how idtech1 (Quake 1) evolved into a modern engine with GLSL shaders, real-time lighting, and advanced video capture. DarkPlaces has a mature demo playback and video output system that predates wolfcamql — its capture pipeline (`cl_video.c`, `r_textures.c`) is a useful reference for understanding how to hook into an id-engine renderer for frame extraction without using AVI.

**Key files:**
- `cl_demo.c` — Demo playback (idtech1 lineage)
- `cl_video.c` — Video frame capture system
- `gl_rmain.c` — OpenGL renderer main, frame submission hooks
- `r_shadow.c` — Real-time lighting (shows how far idtech1 can be extended)

---

### 18. yamagi-quake2 — Yamagi Quake 2 (Best-Documented Q2 Fork)
**Origin:** `https://github.com/yquake2/yquake2` (shallow, ~13 MB)

**Why it's here:**
The best-documented Q2 fork. Yamagi Q2's source has extensive comments explaining the network protocol, entity delta compression, and renderer pipeline — things the original Q2 source leaves implicit. Since idtech2 is the direct ancestor of Q3's network/demo format, reading Yamagi's annotated version of the protocol code clarifies design decisions that carried forward into .dm_73. Also has SDL2-based audio/video that's useful as a reference for cross-platform capture.

**Key files:**
- `src/common/` — Network protocol with comments (ancestor of Q3's protocol)
- `src/client/cl_parse.c` — Demo/network packet parsing (compare with Q3 version)
- `src/client/cl_download.c` — Client state machine reference
- `src/game/g_combat.c` — Annotated combat/obituary system

---

## Updated Size Summary (All Repos)

| Repo | Size | Clone Type | Added |
|---|---|---|---|
| quake3-source | 31 MB | Shallow | Phase 1 |
| ioquake3 | 40 MB | Shallow | Phase 1 |
| wolfcamql-src | 127 MB | Shallow | Phase 1 |
| wolfcamql-local-src | 19 MB | Tarball extract | Phase 1 |
| q3mme | 70 MB | Shallow | Phase 1 |
| uberdemotools | 619 MB | Full | Phase 1 |
| qldemo-python | <1 MB | Full | Phase 1 |
| demodumper | <1 MB | Full | Phase 1 |
| quake3e | 79 MB | Shallow | Phase 1 |
| quake1-source | 16 MB | Shallow | Phase 2 |
| quake2-source | 8 MB | Shallow | Phase 2 |
| openarena-gamecode | 8.5 MB | Shallow | Phase 2 |
| openarena-engine | 36 MB | Shallow | Phase 2 |
| wolfet-source | 33 MB | Shallow | Phase 2 |
| q3vm | 2.7 MB | Shallow | Phase 2 |
| gtkradiant | 57 MB | Shallow | Phase 2 |
| darkplaces | 11 MB | Shallow | Phase 2 |
| yamagi-quake2 | 13 MB | Shallow | Phase 2 |
| **TOTAL** | **~1,171 MB** | | |

---

## Engine Lineage Map

```
idtech1 (Quake 1) ──────────────────────────── quake1-source, darkplaces
    │
idtech2 (Quake 2) ──────────────────────────── quake2-source, yamagi-quake2
    │
idtech3 (Quake 3) ──────────────────────────── quake3-source
    ├── ioquake3 (community port) ───────────── ioquake3
    ├── OpenArena (open assets fork) ────────── openarena-gamecode, openarena-engine
    ├── Wolf: Enemy Territory (id, GPL) ─────── wolfet-source
    ├── WolfcamQL (fragmovie tool) ──────────── wolfcamql-src, wolfcamql-local-src
    ├── q3mme (movie maker's edition) ───────── q3mme
    └── Quake3e (Vulkan fork) ───────────────── quake3e
         │
    Quake Live (.dm_73) ─────────────────────── uberdemotools, qldemo-python, demodumper
         
Tooling:
    QVM bytecode system ─────────────────────── q3vm
    BSP map format ──────────────────────────── gtkradiant
```
