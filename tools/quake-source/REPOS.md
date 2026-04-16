# Quake Legacy Source Knowledge Base
*Generated: 2026-04-16*
*Purpose: Reference repos for QUAKE LEGACY fragmovie automation project*

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
