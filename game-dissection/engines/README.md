# Quake Engine Family — Synthesis

**Last updated:** 2026-04-17 (after engine consolidation).
**Scope:** All 18 engine trees consolidated under `game-dissection/engines/`.

This doc is the master index: family tree, what each engine gives us, and migration
paths for the Tr4sH Quake work (protocol-73 port into q3mme).

---

## Family Tree

```
id Software idtech lineage
└── idtech1 (Quake 1, 1996, GPL)
    │   NIN soundtrack · BSP format · client/server split origin · EV_OBITUARY ancestor
    │
    └── idtech2 (Quake 2, 1997, GPL)
        │   ref_gl renderer · game DLL split · MOD_* kill constants
        │
        ├── Yamagi Quake 2 — community Q2 port (bug-fix + modern OS)
        ├── Darkplaces — Q1 engine with modern renderer (CSQC, DP_*)
        │
        └── idtech3 (Quake 3 Arena, 1999, GPL)
            │   VM system · .dm_48/66 demo protocol · cgame/game/ui split · Huffman msg
            │
            ├── Wolfenstein: Enemy Territory (2003, GPL) — idtech3 + objective MP
            ├── OpenArena engine — ioquake3 + open assets
            │
            ├── ioquake3 — community Q3 port (cleanup + cl_avi.c + SDL)
            │   │
            │   ├── quake3e — modern fork (Vulkan, improved capture, 64-bit)
            │   │
            │   ├── q3mme — Movie Maker's Edition
            │   │      camera splines · DOF · motion blur · demo cut · dynamic FOV
            │   │      TR4SH QUAKE PORT TARGET — becomes our single engine
            │   │
            │   └── wolfcamql-src — Quake Live demo player (protocol 73 support)
            │          Fork of ioquake3 + cgame rewrite for QL .dm_73 demos
            │          GOLDEN TREE for protocol-73 knowledge
            │          ├── wolfcamql-local-src — exact source matching shipped .exe
            │
            └── Q3A-derived tooling
                ├── uberdemotools (C++) — authoritative dm_73/dm_90 parser + analysis
                ├── qldemo-python — pure Python dm_73 parser
                ├── demodumper — Python score-format edge-case companion
                ├── demodumper fork (ours: FT-1 custom C++ parser phase2/dm73parser/)
                └── q3vm — standalone QVM interpreter (for sandboxed game-logic)

Asset tooling
└── gtkradiant — idtech2/3/4 level editor (BSP compilation reference)
```

---

## What Each Engine Gives Us

### Protocol 73 support (Quake Live demos)
| Tree | Role |
|---|---|
| **wolfcamql-src** | **THE** reference. Protocol 73 patches live in `code/qcommon/msg.c`, `cl_parse.c`, `sv_snapshot.c`. Authority tree for msg/net_chan/cl_demo diffs. |
| **wolfcamql-local-src** | Matches the shipped wolfcamql.exe — use for exact-behavior debugging of the binary. |
| **uberdemotools** | Independent dm_73 parser, used for ground-truth validation of FT-1 custom parser. |
| **qldemo-python** / **demodumper** | Python reference implementations, slow but readable. |

### Rendering + capture
| Tree | Role |
|---|---|
| **q3mme** | Target engine for Tr4sH Quake. Camera splines, DOF, motion blur accumulation, demo cut. We port proto-73 INTO this. |
| **quake3e** | Vulkan renderer, modern capture. Fallback if q3mme's OpenGL can't hit 4K60. |
| **ioquake3** | Cleanest `cl_avi.c` implementation — AVI capture reference. |
| **openarena-engine** | Second opinion on AVI capture + community patches. |

### Reference / ancestry
| Tree | Role |
|---|---|
| **quake3-source** | id Software ground truth for Q3 demo/msg/huffman. Anything else is a fork. |
| **quake1-source** / **quake2-source** | Lineage — BSP format, net_chan, EV_OBITUARY ancestor, MOD_* origin. |
| **darkplaces** / **yamagi-quake2** | Not on critical path. Reference for modern renderers on old formats. |
| **wolfet-source** | Structural cross-reference — wolfcam started as an ET mod. |
| **openarena-gamecode** | Alternate MOD_* constants, CC-licensed assets for Phase 4 public CLI. |
| **q3vm** | Standalone QVM interpreter — useful if we want to audit shipped .qvm files. |
| **gtkradiant** | Level editor — BSP compile pipeline reference for Phase 3.5 3D intros. |

---

## Migration Paths — Protocol 73 Port into q3mme

This is **Phase 3.5 Track A** (Tr4sH Quake manifesto). Goal: single engine that does
everything wolfcamql does (dm_73 playback) plus everything q3mme does (camera splines,
motion blur, demo cut).

### Interesting diff files (authoritative list in `_diffs/`)

The 513 near-duplicate files at `game-dissection/engines/_diffs/` are ranked by
porting importance. Hot list:

**Protocol layer (must port wolfcamql deltas into q3mme):**
- `code/qcommon/msg.c` — dm_73 field parsing, bitstream quirks
- `code/qcommon/net_chan.c` — QL channel framing
- `code/qcommon/huffman.c` — shared, verify no QL-specific table changes
- `code/qcommon/common.c` — shared helpers; check CVAR_* and Cmd_* additions
- `code/qcommon/q_shared.h` — constants (MAX_CLIENTS, MOD_*, EV_*)

**Client demo pipeline:**
- `code/client/cl_parse.c` — entity/playerstate deserialization from dm_73
- `code/client/cl_demo.c` — demo file read loop
- `code/client/cl_cgame.c` — trap_ dispatch into cgame VM
- `code/client/cl_main.c` — top-level state machine

**Server snapshots (ref only for playback, but needed for demo correctness):**
- `code/server/sv_snapshot.c` — snapshot entity selection
- `code/server/sv_game.c` — game VM trap interface

**cgame (biggest divergence between trees):**
- `code/cgame/cg_*.c` — wolfcam's QL-aware cgame vs. q3mme's movie-oriented cgame
  — these merge: keep q3mme's camera/capture/demos_* files, graft wolfcam's
  QL scoring/powerup/chat/config-string handlers

### Step plan (high-level, details in Tr4sH Quake manifesto)

1. **Baseline:** check q3mme builds clean against current toolchain (MSYS2 + MinGW)
2. **Protocol module:** port `msg.c` + `cl_parse.c` deltas from wolfcamql-src into
   q3mme/trunk/code/qcommon and code/client (use `_diffs/` as the patch roadmap)
3. **cgame merge:** start from q3mme cgame (keep demos_*.c), splice in wolfcam's
   `wolfcam_*.c` files as new modules; resolve duplicate symbols by namespacing
4. **Demo format test:** play back a known dm_73 in the merged engine — expect
   scoreboard garbled until configstring handlers are wired in
5. **FT-4:** reverse-engineer wolfcamql.exe (Ghidra) to find any binary-only patches
   that aren't in wolfcamql-local-src (there WILL be some — vendor-shipped tarballs
   always lag the compiled binary)
6. **Retire wolfcam:** once merged engine can play every demo in our corpus with
   byte-identical snapshots, wolfcam/* canonical tree drops to "archived" status

---

## Authority Order (used by `build_canonical.py`)

When an exact-duplicate file exists in multiple trees, the canonical copy comes from
the highest-authority tree per this order:

1. **wolfcamql-src** — authority for protocol 73 + QL extensions
2. **quake3e** — authority for modern renderer + capture
3. **q3mme** — authority for movie-maker features + target engine
4. **ioquake3** — authority for clean Q3 baseline
5. **quake3-source** — authority for id Software ground truth
6. others (wolfcamql-local-src, openarena-*, q3vm, demodumper, uberdemotools, id Q1/Q2, yamagi, darkplaces, wolfet, qldemo-python, gtkradiant)

This reflects the Tr4sH Quake porting priorities: protocol-73 knowledge > modern
renderer > movie engine > clean baseline > ground truth.

---

## Per-Engine Docs

### Full treatment (6 docs each) — porting targets
- `dissection/wolfcamql-src/` — ARCHITECTURE, EXTENSION_POINTS, PROTOCOL_LAYER, CLIENT_SERVER_SPLIT, RENDERER_NOTES, QUIRKS
- `dissection/q3mme/` — same 6
- `dissection/quake3e/` — same 6

### Light treatment (3 docs each) — reference only
- `dissection/quake3-source/` — ARCHITECTURE, EXTENSION_POINTS, QUIRKS
- `dissection/ioquake3/` — same 3
- `dissection/uberdemotools/` — same 3
- `dissection/quake1-source/`, `quake2-source/`, `darkplaces/`, `yamagi-quake2/`
- `dissection/openarena-engine/`, `openarena-gamecode/`
- `dissection/wolfet-source/`, `demodumper/`, `qldemo-python/`, `q3vm/`, `gtkradiant/`
- `dissection/wolfcamql-local-src/` (nearly identical to wolfcamql-src, doc just notes deltas)

### Where to look for per-file diffs
- `_diffs/<rel_path>.diff.md` — every near-dup C/H/CPP/PY file has one of these,
  showing canonical-vs-variant with diff stats + inline diff for small files

---

## Cleanup record

- **2026-04-17** Phase A0: inventory (13,932 files, 0.72 GB across 18 trees)
- **2026-04-17** Phase A1: canonical tree + variants + DIFFS (141 MB freed)
- **2026-04-17** Phase A2: this SYNTHESIS + per-engine docs

See `_manifest/DELETE_READY.md` for exact deletion log.
