#!/usr/bin/env python3
"""Generate ARCHITECTURE/EXTENSION_POINTS/QUIRKS docs for the 15 'light treatment' trees."""
from pathlib import Path

DOCS_ROOT = Path(r"G:/QUAKE_LEGACY/engine/engines/_docs")

TREES = {
    "quake3-source": {
        "upstream": "https://github.com/id-Software/Quake-III-Arena",
        "size": "31 MB (shallow)",
        "role": "id Software ground-truth for Q3. Authority for Q3 demo protocol, Huffman compression, and the entityState/playerState structs that every Q3 fork inherits.",
        "module_map": """
code/
├── qcommon/       — msg.c, huffman.c, net_chan.c, common.c (THE reference)
├── client/        — cl_demo.c, cl_parse.c, cl_main.c
├── server/        — full authoritative server
├── game/, cgame/, ui/ — VM sources
├── renderer/      — OpenGL renderer
└── botlib/        — bot AI
""",
        "key_files": [
            ("code/qcommon/huffman.c", "Huffman codec — every byte in dm_68/66 is encoded with this"),
            ("code/qcommon/msg.c", "MSG_* read/write and entityState/playerState field tables — foundation of the protocol"),
            ("code/client/cl_demo.c", "Demo record/playback, client side"),
            ("code/server/sv_demo.c", "Demo write, server side"),
            ("code/qcommon/q_shared.h", "Entity state fields, playerState_t, snapshot_t, MOD_*, EV_*, WP_*"),
        ],
        "ext_points": """
- Engine is shipped read-only reference — do not modify. Any extension happens in a fork.
- For Q3-native demos: the dm_68/dm_66 formats defined here are what every Q3 fork reads.
- For Quake Live work: use this as the baseline, apply wolfcamql's deltas via `_diffs/`.
""",
        "quirks": """
- **Reference tree only** — we do not build or run this, we only read it.
- Source is release-1999 C; some constructs are pre-C99 (no stdint.h).
- `cgame/g_*.c` and similar files are NOT in this tree — Q3A was the first id release to ship only the engine source + gamecode separately; gamecode lives in `code/game/` not under `code/`.
- Licensing: GPL-2.0. Our forks must preserve headers.
""",
    },
    "ioquake3": {
        "upstream": "https://github.com/ioquake/ioq3",
        "size": "40 MB (shallow)",
        "role": "Best-documented community Q3 baseline. Ancestor of wolfcamql, q3mme, quake3e, openarena-engine. Canonical cl_avi.c implementation.",
        "module_map": """
Same layout as quake3-source but with significant cleanups:
- SDL2 platform layer (code/sdl/)
- AVI capture: code/client/cl_avi.c (THE reference AVI writer)
- OpenGL 2 renderer stages (code/renderer/tr_glsl.c, bloom.c)
- 64-bit clean, modern C compatibility
""",
        "key_files": [
            ("code/client/cl_avi.c", "AVI video capture — inherited by wolfcam, replaced by quake3e's ffmpeg pipe"),
            ("code/qcommon/huffman.c", "Cleaner, better-commented variant of the Huffman codec"),
            ("code/client/cl_demo.c", "Demo playback with additional error handling"),
            ("code/renderer/tr_main.c", "Renderer frame submission, hook site for cl_avi capture"),
        ],
        "ext_points": """
- cl_avi.c call sites are the canonical place to add capture automation
- SDL2 platform layer is the template for any OS-specific work
- Build system is Makefile-driven; quake3e modernized to CMake — consider for our work
""",
        "quirks": """
- Shader pipeline uses both fixed-function and GLSL depending on r_ext_framebuffer_object
- VM cgame vs native cgame — ioquake3 supports both; our port decisions follow
- cl_avi.c AVI writer hits RIFF 4 GB limit at ~40 seconds of 1080p60 — that's why quake3e replaced it
""",
    },
    "uberdemotools": {
        "upstream": "https://github.com/mightycow/uberdemotools",
        "size": "298 MB (full clone, includes test binaries and demos)",
        "role": "C++ demo parser with JSON export. Authoritative ground-truth for our FT-1 custom parser's correctness.",
        "module_map": """
UDT_DLL/
├── include/uberdemotools.h      — public C API
├── src/
│   ├── apps/
│   │   └── app_demo_json.cpp    — full demo → JSON export
│   ├── analysis_obituaries.cpp  — kill feed parser
│   ├── analysis_captures.cpp    — CTF captures
│   ├── analysis_pattern_frag_run.cpp
│   ├── analysis_pattern_mid_air.cpp
│   ├── analysis_pattern_multi_rail.cpp
│   └── api.cpp                  — C API implementation
├── TECHNICAL_NOTES.md           — protocol docs (READ FIRST)
└── CUSTOM_PARSING.md            — extension guide
research/Huffman/huffman.cpp     — reference impl with explanatory comments
""",
        "key_files": [
            ("UDT_DLL/TECHNICAL_NOTES.md", "Best-in-class Q3/QL protocol docs. Read before writing any parser."),
            ("UDT_DLL/CUSTOM_PARSING.md", "Extension guide — how to add a new event analyzer"),
            ("UDT_DLL/src/apps/app_demo_json.cpp", "Full-demo JSON export — shape of our output"),
            ("UDT_DLL/src/analysis_obituaries.cpp", "Frag extraction reference"),
            ("UDT_DLL/src/analysis_pattern_*.cpp", "Multi-kill / airshot / mid-air / multi-rail pattern detection"),
        ],
        "ext_points": """
- Public C API (`uberdemotools.h`) is stable — we can link this into Python via ctypes
- JSON output schema is our de-facto JSONL format spec
- Pattern analyzers (`analysis_pattern_*.cpp`) are direct templates for FT-2 highlight criteria
""",
        "quirks": """
- **Pre-built binaries ship in the repo** (UDT_DLL_*.dll, UDT_json.exe) — these inflate the tree size to 619 MB originally.
- Most of the size is test .dm_73 / .dm_90 fixtures under tests/ — we can cull these in our dedup if we don't run UDT's own tests
- C++ API uses raw pointers + caller-manages-memory; Python wrapper must be careful
- Supports proto-66 (Q3 1.16n), proto-68 (Q3 1.32), proto-73 (QL 2010), proto-90 (QL 2015+)
- Our focus is proto-73, but UDT handles all of them — use for validation of FT-1 custom parser
""",
    },
    "quake1-source": {
        "upstream": "https://github.com/id-Software/Quake",
        "size": "11.8 MB (shallow)",
        "role": "Root of the idtech lineage. Reference for EV_OBITUARY ancestry and BSP format origin.",
        "module_map": """
WinQuake/      — Windows renderer + sound
Quake/         — engine core (game logic, world, sv_main)
QW/            — QuakeWorld client/server (early network split)
""",
        "key_files": [
            ("Quake/world.c", "Entity/physics world state — ancestor of Q3's entity system"),
            ("Quake/sv_main.c", "Server loop origin — all idtech servers descend from this"),
            ("WinQuake/bspfile.h", "BSP format — ancestor of Q3's BSP structure"),
        ],
        "ext_points": "Not used at runtime. Reference only.",
        "quirks": """
- Pre-C99 code; compiles with surprisingly old compilers
- NIN soundtrack is licensed separately — cannot redistribute the music; the source just calls mediated track names
- BSP format is very different from Q3's — don't conflate
""",
    },
    "quake2-source": {
        "upstream": "https://github.com/id-Software/Quake-2",
        "size": "6.2 MB (shallow)",
        "role": "Direct ancestor of Q3. Introduced modular renderer (ref_gl/), game DLL split, MOD_* constants.",
        "module_map": """
ref_gl/        — OpenGL renderer (direct ancestor of Q3's)
game/          — gamecode (separated from engine)
qcommon/       — shared code (ancestor of Q3's qcommon)
client/, server/
""",
        "key_files": [
            ("ref_gl/", "OpenGL renderer — direct ancestor of Q3"),
            ("game/g_combat.c", "Damage/kill logic, origin of MOD_* constants"),
            ("qcommon/net_chan.c", "Network channel, ancestor of Q3's demo protocol"),
            ("client/cl_demo.c", "Demo recording — compare with Q3's to trace format evolution"),
        ],
        "ext_points": "Reference only.",
        "quirks": """
- Q2 protocol is proto-34. Completely different bitstream from Q3's proto-66+.
- Sonic Mayhem composed the soundtrack — relevant for music-licensing research.
- MOD_* enum here is the ORIGIN of Q3's MOD_* — same names, similar values.
""",
    },
    "yamagi-quake2": {
        "upstream": "https://github.com/yquake2/yquake2",
        "size": "8.9 MB (shallow)",
        "role": "Modern Q2 community port. Reference for how a legacy engine is modernized without losing compatibility.",
        "module_map": "Structurally similar to quake2-source with extensive modernization layers.",
        "key_files": [
            ("src/", "Modernized src tree — CMake-driven"),
            ("CMakeLists.txt", "Build reference"),
            ("README.md", "Extensive porting notes"),
        ],
        "ext_points": "Reference only. Useful for 'how to modernize a legacy id engine' patterns if we ever upstream to darkplaces.",
        "quirks": """
- Q2-only, not relevant for Q3/QL protocol work
- But their CMake build and platform-abstraction approach is cleaner than q3mme's Makefile — stylistic reference
""",
    },
    "darkplaces": {
        "upstream": "https://icculus.org/twilight/darkplaces/",
        "size": "8.5 MB (shallow)",
        "role": "Modern Q1 engine with CSQC, advanced renderer, DP_* extensions.",
        "module_map": "Custom idtech1 fork with heavy renderer modifications. Not a Q3 ancestor — separate branch.",
        "key_files": [
            ("cl_demo.c", "Demo format for Q1, not relevant to dm_73"),
            ("csprogs.c", "CSQC — client-side QuakeC, interesting for custom game logic"),
            ("model_brush.c", "BSP loader"),
        ],
        "ext_points": "Reference only. CSQC might inspire our in-demo scripting for Phase 3.5.",
        "quirks": """
- Off-trunk from our main line — Q1 descendant, not Q3
- Useful if we ever want to render Q1 demos as part of a 'pan-id-tribute' video
- Renderer is far more advanced than stock Q1 — dynamic lights, realtime shadows, normal mapping
""",
    },
    "openarena-engine": {
        "upstream": "https://github.com/OpenArena/engine",
        "size": "26.9 MB (shallow)",
        "role": "OpenArena engine fork of ioquake3. Second reference point for AVI capture and demo playback.",
        "module_map": "Same as ioquake3 with community patches layered on top.",
        "key_files": [
            ("code/client/cl_avi.c", "AVI capture (compare with ioquake3 and wolfcamql)"),
            ("code/renderer/", "Renderer modifications (minor)"),
            ("code/client/cl_demo.c", "Demo playback patches"),
        ],
        "ext_points": "Mostly same as ioquake3. Some community patches worth cherry-picking case-by-case.",
        "quirks": """
- Engine is CC-BY-SA-friendly but still GPL-licensed (engine itself)
- The 'friendly' part is the openarena-gamecode + assets
- Useful primarily as a 'how have others patched ioquake3' diff reference
""",
    },
    "openarena-gamecode": {
        "upstream": "https://github.com/OpenArena/gamecode",
        "size": "6.4 MB (shallow)",
        "role": "Q3-compatible gamecode with open-licensed weapons/items. Relevant for Phase 4 public CLI bundled-asset fallback.",
        "module_map": """
code/game/         — server game VM
code/cgame/        — client game VM
code/ui/           — menu VM
code/game/bg_*.c   — shared between game/cgame
""",
        "key_files": [
            ("code/game/g_combat.c", "Kill/damage with OpenArena weapon additions"),
            ("code/game/g_weapon.c", "Weapon fire logic"),
            ("code/game/bg_misc.c", "Item/powerup definitions"),
        ],
        "ext_points": "Gamecode only — extensions happen via new weapons/items in bg_*.c + g_weapon.c.",
        "quirks": """
- OpenArena's MOD_* may differ from standard Q3 MOD_* — do NOT assume exact match
- Assets (models, textures) are under CC-BY-SA — redistributable
- For Phase 4 public tool: if we need a default asset pack, this is the legal source
""",
    },
    "wolfet-source": {
        "upstream": "https://github.com/id-Software/Enemy-Territory",
        "size": "24.7 MB (shallow)",
        "role": "Wolfenstein: Enemy Territory — idtech3 derivative. Structural reference since wolfcam started as an ET mod.",
        "module_map": """
src/
├── cgame/        — client game (compare structure with wolfcamql's cgame)
├── client/       — cl_avi.c in ET variant
├── renderer/     — idtech3 renderer in ET form
├── game/         — server game, ET-specific classes and objectives
└── qcommon/      — shared code
""",
        "key_files": [
            ("src/cgame/", "Compare structure with wolfcamql's cgame"),
            ("src/client/cl_avi.c", "AVI capture in ET variant"),
            ("src/game/g_combat.c", "Combat/kill system, ET variant of Q3's"),
        ],
        "ext_points": "Reference only for our purposes.",
        "quirks": """
- ET uses a different demo protocol — NOT compatible with Q3 dm_68 / QL dm_73
- But the cgame/client structure is very close to Q3; wolfcam inherited a lot from here
- ET-specific objective/class system — ignore that code, focus on rendering/demo paths
""",
    },
    "demodumper": {
        "upstream": "https://github.com/syncore/demodumper",
        "size": "0.2 MB",
        "role": "Python companion to qldemo-python. Handles score-format edge cases.",
        "module_map": """
demodumper.py     — main entry, handles score format variants
qldemo/           — may include patches to base qldemo-python
NOTE              — quirks and limitations (read first)
""",
        "key_files": [
            ("demodumper.py", "Main entry — handles all score command format variants"),
            ("NOTE", "Known quirks and limitations — read first"),
        ],
        "ext_points": "Small Python codebase — fork and extend directly.",
        "quirks": """
- Pure Python, slow for bulk processing (thousands of demos)
- Handles malformed demos gracefully where qldemo-python crashes
- Our FT-1 custom C++ parser replaces this for bulk work, but demodumper is a good fallback for weird demos
""",
    },
    "qldemo-python": {
        "upstream": "https://github.com/Quakecon/qldemo-python",
        "size": "0.6 MB (full)",
        "role": "Pure-Python dm_73 parser. Reference implementation for FT-1's custom C++ parser.",
        "module_map": """
qldemo/           — parser library package
huffman/          — Huffman module (may be C extension for speed)
qldemo2json.py    — demo → JSON conversion script
qldemosummary.py  — summarize demo metadata
""",
        "key_files": [
            ("qldemo/", "Parser library — the core protocol implementation"),
            ("qldemo2json.py", "Entry point for demo-to-JSON conversion"),
            ("qldemosummary.py", "Summary: players, scores, map, duration"),
        ],
        "ext_points": "Python package — fork and extend directly.",
        "quirks": """
- Pure Python parsing is SLOW (~60 seconds per 3 MB demo on a modern CPU)
- Huffman decoder is the hot path; reimplemented in C it's 10-100x faster
- Missing some edge cases (proto-73 extensions past 2015 QL updates — FT-1 must handle)
""",
    },
    "q3vm": {
        "upstream": "https://github.com/jnz/q3vm",
        "size": "1.8 MB",
        "role": "Standalone Q3 VM (virtual machine) interpreter. Useful for sandboxed game-logic analysis.",
        "module_map": """
src/vm_*.c        — VM core (stack, opcodes, syscalls)
src/tools/        — q3asm, q3lcc for compiling to .qvm
examples/         — small VM programs
""",
        "key_files": [
            ("src/vm_*.c", "VM interpreter core"),
            ("src/tools/q3asm/", "q3asm assembler"),
            ("src/tools/q3lcc/", "q3lcc C-to-VM compiler"),
        ],
        "ext_points": "Embeddable — link into any C program to execute .qvm files.",
        "quirks": """
- Useful if we want to execute shipped .qvm files (QL gamecode) in isolation — e.g. to dump weapon stats or item definitions that aren't in public source
- Not needed for our primary port path (we build cgame native)
- Could become relevant if FT-4 Ghidra work finds .qvm-only logic
""",
    },
    "gtkradiant": {
        "upstream": "https://github.com/TTimo/GtkRadiant",
        "size": "50.5 MB",
        "role": "idtech2/3/4 level editor. Reference for BSP compile pipeline.",
        "module_map": """
radiant/          — editor core
tools/            — q3map2 (BSP compiler), q3data, q3map
plugins/          — format plugins for various id games
""",
        "key_files": [
            ("tools/quake3/q3map2/", "BSP compiler — how .map files become .bsp"),
            ("radiant/", "Editor main"),
        ],
        "ext_points": "Complete editor — unlikely we modify. Useful if Phase 3.5 3D intros need custom maps.",
        "quirks": """
- GTK-based GUI, cross-platform
- q3map2 is THE tool for BSP compilation — accepts Q3 and QL BSP formats
- Not on our critical path. Reference for Phase 3.5 map work.
""",
    },
    "wolfcamql-local-src": {
        "upstream": "Extracted tarball from G:\\QUAKE LEGACY\\WOLF WHISPERER\\WolfcamQL\\wolfcamql-src.tar.gz",
        "size": "19.4 MB (tarball 2016-08-13)",
        "role": "Exact source matching the shipped wolfcamql.exe binary. Use for debugging the .exe behavior.",
        "module_map": "Near-identical to wolfcamql-src. Deltas are mostly local patches + version timestamps.",
        "key_files": [
            ("Same structure as wolfcamql-src", "See `_docs/wolfcamql-src/ARCHITECTURE.md`"),
        ],
        "ext_points": "Same as wolfcamql-src. Differences highlighted in `_diffs/`.",
        "quirks": """
- Close to wolfcamql-src but not identical — tarball freezes an earlier state
- The shipped wolfcamql.exe is LATER than this tarball — there are patches in the binary that exist nowhere in source (see FT-4 Ghidra work)
- For "what does my .exe do?" questions, start here, not wolfcamql-src
- For "what's the latest proto-73 understanding?" use wolfcamql-src
""",
    },
}

ARCH_TMPL = """# {tree} — Architecture

**Upstream:** {upstream}
**Size (original):** {size}
**Role in our project:** {role}

## Module map
{module_map}

## Key files
{key_files_list}

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `engine/engines/{tree}/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
"""

EXT_TMPL = """# {tree} — Extension Points

{ext_points}

## See also
- `_docs/{tree}/ARCHITECTURE.md`
- `_docs/{tree}/QUIRKS.md`
"""

QUIRKS_TMPL = """# {tree} — Quirks and Gotchas

{quirks}

## See also
- `_docs/{tree}/ARCHITECTURE.md`
- `_docs/{tree}/EXTENSION_POINTS.md`
"""

def main():
    for tree, cfg in TREES.items():
        d = DOCS_ROOT / tree
        d.mkdir(parents=True, exist_ok=True)
        key_files_list = "\n".join(f"- `{p}` — {d}" for p, d in cfg["key_files"])
        (d / "ARCHITECTURE.md").write_text(ARCH_TMPL.format(
            tree=tree, upstream=cfg["upstream"], size=cfg["size"], role=cfg["role"],
            module_map=cfg["module_map"].strip(),
            key_files_list=key_files_list,
        ), encoding="utf-8")
        (d / "EXTENSION_POINTS.md").write_text(EXT_TMPL.format(
            tree=tree, ext_points=cfg["ext_points"].strip(),
        ), encoding="utf-8")
        (d / "QUIRKS.md").write_text(QUIRKS_TMPL.format(
            tree=tree, quirks=cfg["quirks"].strip(),
        ), encoding="utf-8")
        print(f"wrote {tree}")

if __name__ == "__main__":
    main()
