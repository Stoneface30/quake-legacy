# Engine Ingestion State — 2026-04-19

**Author:** research agent (fresh-context)
**Scope:** Situational awareness snapshot of Quake engine source ingestion, the custom `dm_73` parser, Steam pak ingestion, and how all of it maps to the TR4SH QUAKE manifesto before the user comes back online.
**Branch observed:** `design/phase1-pantheon-system` @ `805decca` (2026-04-19).

---

## Executive Summary

Engine ingestion is in solid shape on the **data** side and still theoretical on the **fork** side. Eighteen Quake-family source trees sit under `tools/quake-source/` (totalling ~1.3 GB), twelve of them live git clones with a real `origin` remote — including the four that the TR4SH QUAKE manifesto depends on (`q3mme`, `quake3e`, `ioquake3`, `wolfcamql-src`/`wolfcamql-local-src`) and the reference parser sources (`uberdemotools`, `qldemo-python`, `demodumper`). Protocol-version probe confirms id Q3 = 68, ioquake3/OpenArena = 71, quake3e dual-mode = 68/71, wolfcamql = **91** with a commented-out 73 hint on the same line — the exact place the Path-B protocol-73 port into q3mme will tap.

Our FT-1 `dm73parser` is **built and working** at `phase2/dm73parser/build/dm73dump.exe` (68 KB CLI) with the library `dm73parser.lib` (608 KB) and a passing `dm73_tests.exe` — but the source tree (`src/`, `include/`, `tools/`, `tests/`, `CMakeLists.txt`, vendored wolfcam `huffman.c`/`msg.c`) is **not on this branch**; only the build artefacts and `tests/golden_baseline.json` are on disk. The parser sources live on another branch (likely `creative-suite-v2-step2` or `feature/creative-suite-v2`) — the current `design/phase1-pantheon-system` branch is Phase 1 pantheon work and treats `phase2/` as untracked. The compiled binary runs and advertises its CLI, so corpus runs are *possible* today, but re-building from this branch is not.

Steam paks — 962 MB QL `pak00.pk3` + 496 MB of Q3A `pak0-8.pk3` — are **confirmed present** at the canonical paths (mtime May 2023 for QL, April 2026 for Q3A) and are already inventoried into JSON catalogs (`steam-pak-manifest-2026-04-17.json`, 80k lines, 13,358 files). Consumers (`creative_suite/config.py`, `creative_suite/inventory/*`) are wired for them on the `creative-suite-v2` branches but are again absent on this branch's working tree.

Biggest blocker: **engine-pivot Gate ENG-1** still unresolved — user has not yet picked Path A (wolfcam for `.dm_73`, q3mme for everything else), Path B (port protocol 73 into q3mme), or Path C (convert `.dm_73` → `.dm_68`). The manifesto's Track A depends on this decision.

---

## Engine Forks On Disk

All under `G:/QUAKE_LEGACY/tools/quake-source/`.

| Name | Origin | Size | Protocol | Last-touched | Buildable | Purpose |
|---|---|---:|---:|---|---|---|
| `quake3-source` | github.com/id-Software/Quake-III-Arena (shallow) | 31 MB | 68 | 2012-01-31 | Makefile-era, unlikely on MSVC 2022 | id's GPL release — ground truth for protocol + Huffman |
| `ioquake3` | github.com/ioquake/ioq3 (shallow) | 40 MB | 71 | 2026-03-09 | CMake present (`CMakeLists.txt`) | Cleaned-up Q3, cl_avi reference |
| `wolfcamql-src` | github.com/brugal/wolfcamql (shallow) | 127 MB | **91** (73 commented) | 2026-03-28 | Makefile (GCC/MinGW) | Github wolfcam mirror |
| `wolfcamql-local-src` | tarball 2016-08-13 (WolfWhisperer bundle) | 19 MB | **91** (73 commented) | (not git) | Makefile (GCC/MinGW) | Matches the installed wolfcamql.exe — use for local-patch diffs |
| `q3mme` | github.com/entdark/q3mme (shallow) | 70 MB | 68 | 2022-10-03 | custom Makefile under `trunk/` | Movie-maker's edition — manifesto's chosen fork base |
| `uberdemotools` | github.com/mightycow/uberdemotools (FULL) | 619 MB | — (parser) | 2024-01-08 | Premake5 + prebuilt binaries shipped | Reference .dm_73/.dm_68 parser + analysis modules |
| `quake3e` | github.com/ec-/Quake3e (shallow) | 79 MB | 68 + 71 (dual) | 2026-04-16 | `CMakeLists.txt` + Makefile | Modern Q3 fork, Vulkan renderer |
| `qldemo-python` | github.com/Quakecon/qldemo-python (FULL) | 419 KB | 68 (in vendored qcommon.h) | 2015-07-14 | `setup.py` | Python .dm_73 parser |
| `demodumper` | github.com/syncore/demodumper (FULL) | 340 KB | 68 (vendored) | 2021-12-26 | `setup.py` | Companion to qldemo-python, score-format handling |
| `darkplaces` | github.com/DarkPlacesEngine/darkplaces (shallow) | 11 MB | Q1 (net 3) | 2026-01-22 | BSDmakefile + Xcode | Q1 engine — FT-3/3D-intro reference, not on critical path |
| `quake1-source` | github.com/id-Software/Quake (shallow) | 16 MB | 15 / NetQuake 3 | 2012-01-31 | historical | Q1 source — reference only |
| `quake2-source` | github.com/id-Software/Quake-2 (shallow) | 8.1 MB | 34 | 2012-01-31 | historical | Q2 source — reference only |
| `yamagi-quake2` | github.com/yquake2/yquake2 (shallow) | 13 MB | 34 | 2026-04-16 | CMake | Modern Q2 fork — off critical path |
| `openarena-engine` | github.com/OpenArena/engine (shallow) | 36 MB | 71 | 2026-04-12 | Makefile | OA engine fork |
| `openarena-gamecode` | github.com/OpenArena/gamecode (shallow) | 8.5 MB | 71 | 2025-12-20 | Makefile | OA game VM |
| `wolfet-source` | github.com/id-Software/Enemy-Territory (shallow) | 33 MB | 72 / 84 | 2012-01-31 | historical | W:ET — cross-ref only |
| `gtkradiant` | github.com/TTimo/GtkRadiant (shallow) | 57 MB | — (editor) | 2024-08-18 | SConstruct | Map editor — future FT-3 use |
| `q3vm` | github.com/jnz/q3vm (shallow) | 2.7 MB | — | 2026-03-06 | Makefile + msvc dir | Standalone Q3 VM executor |

Everything in that table has the full `REPOS.md` rationale at `tools/quake-source/REPOS.md` (lines 1-186).

**Notes:**
- `wolfcamql-src` and `wolfcamql-local-src` both declare `PROTOCOL_VERSION 91` as the active define with `// #define PROTOCOL_VERSION 73` right above it. The "73" in `.dm_73` is a filename-era historical — the demos we parse are in practice negotiated per-gamestate. This is the surface we graft onto q3mme for Path B.
- `quake3e` is the only fork shipping **both** 68 and 71 toggleable at runtime (`OLD_PROTOCOL_VERSION 68` / `NEW_PROTOCOL_VERSION 71`). It's the cleanest template for "q3mme with multiple protocols" patterning.
- `uberdemotools` ships its own prebuilt binaries (x86/x64 under `UDT_DLL/` and `UDT_GUI/`) — we can invoke `UDT_json.exe` today without compiling a thing.
- None of these forks has had a local build run inside `phase2/` or `creative_suite/` yet. All evidence of "buildable on this machine" is circumstantial (presence of `CMakeLists.txt`, Makefiles, MSVC projects) rather than observed.

---

## Our C++ Parser (FT-1)

**Path:** `G:/QUAKE_LEGACY/phase2/dm73parser/`

### Binary state (on current branch)
- `build/dm73dump.exe` — 68 096 bytes, built 2026-04-19, MSVC 14.44 + CMake 3.31 (Ninja, MSVC2022). Runs and prints usage: `dm73dump <demo.dm_73> [--output out.jsonl] [--filter kinds]` with kinds `summary,server_command,config_string,snapshot`.
- `build/dm73_tests.exe` — 241 664 bytes (GoogleTest-shape unit tests).
- `build/dm73parser.lib` — 622 888 bytes (static library).
- `build/dm73_vendor_huffman.lib` — 14 768 bytes (vendored wolfcam `huffman.c` + local `huff_table.c`).
- `build/dm73_vendor_headers_probe.lib` — 1 158 bytes (compile-time probe of vendored wolfcam headers).
- `tests/golden_baseline.json` — golden obituary-count baseline on five demos (`Demo (1|28|103|500|900).dm_73`, obit counts 140/6/33/103/63). Header says `all_counts_match: true`.

### Source state (on current branch: MISSING)
The CMake build log references these translation units:
- `src/container.cpp`, `src/entitystate.cpp`, `src/events.cpp`, `src/gamestate.cpp`, `src/huffman.cpp`, `src/message.cpp`, `src/parser.cpp`, `src/playerstate.cpp`, `src/rounds.cpp`, `src/servercommands.cpp`, `src/snapshot.cpp`
- `src/huff_table.c`
- `tools/dm73dump.cpp`
- `tests/test_container.cpp`, `tests/test_huffman.cpp`, `tests/test_main.cpp`, `tests/test_obits.cpp`
- `vendor/qcommon/huffman.c` (lifted from wolfcamql-src under GPL-2.0, headers preserved per FT-1 contract)
- `vendor/code/header_probe.cpp`

None of those `.cpp/.c/.h` files is present in the working tree — only `build/` and `tests/golden_baseline.json`. `git status` reports `phase2/` as **untracked**. `git ls-files phase2/` returns empty. This branch is Phase 1 pantheon work; the parser's sources exist on a sibling branch.

### Branches likely holding the sources
`feature/creative-suite-v2`, `creative-suite-v2-step2`, or the worktree at `.claude/worktrees/creative-suite-v2/` (grep confirms `creative_suite/inventory/catalog.py` and `creative_suite/api/packs.py` live in that worktree). Recommend `git show creative-suite-v2-step2:phase2/dm73parser/CMakeLists.txt` to confirm before any attempt to rebuild from this branch.

### Corpus-run readiness
- **Can run NOW:** `dm73dump.exe <demo>` works as-is against any `.dm_73` on disk. The primary corpus at `WOLF WHISPERER/WolfcamQL/wolfcam-ql/demos/` (948 files per CLAUDE.md) is directly consumable.
- **Cannot rebuild on this branch:** source files are absent — switching branches or checking out `phase2/dm73parser/` from a sibling branch is required before any edit/compile iteration.
- **Golden baseline coverage:** 5 demos, obituary counts only — not a full field-agreement baseline. `summary.mean_field_agreement_pct` is `null`, indicating field-by-field diffing vs UDT isn't wired yet.

### Relationship to vendored wolfcamql-src code
The CMake target `dm73_vendor_huffman` compiles `vendor/qcommon/huffman.c` (wolfcam lift, GPL-2.0 headers preserved per FT-1 contract) alongside our own `src/huff_table.c`. The `dm73_vendor_headers_probe` library compiles `vendor/code/header_probe.cpp` — a sentinel that verifies the lifted wolfcam headers still parse under our compiler flags. Everything else (`src/*.cpp`) is ours.

---

## Steam Pak Ingestion

### Paks confirmed on disk (2026-04-19 verify)
| Pak | Path | Size | mtime |
|---|---|---:|---|
| QL `pak00.pk3` | `C:/Program Files (x86)/Steam/steamapps/common/Quake Live/baseq3/pak00.pk3` | 962 052 238 B (917 MiB) | 2023-05-05 |
| QL `bin.pk3` | same dir | 1 381 099 B | 2023-05-05 |
| Q3A `pak0.pk3` | `C:/Program Files (x86)/Steam/steamapps/common/Quake 3 Arena/baseq3/pak0.pk3` | 479 493 658 B (457 MiB) | 2026-04-16 |
| Q3A `pak1-8.pk3` | same dir | ~25 MiB combined | mixed |

Combined authoritative asset corpus: **1.4 GiB** across 13 358 catalogued files.

### Extraction + catalog tooling
- `docs/research/steam-pak-manifest-2026-04-17.json` — every file enumerated, 80 261 lines, 1.6 MB
- `docs/research/steam-pak-summary-2026-04-17.json` — category roll-ups
- `docs/research/steam-pak-inventory-2026-04-17.md` — human narrative (113 lines)
- `docs/visual-record/2026-04-17/steam-paks-proof/README.md` — ENG-1 visual-record proof

### Consumers
Grep for `pak00` / `extracted/baseq3` / `FULL_CATALOG` finds these in-tree consumers (most are on the `creative-suite-v2` worktree/branch, not on this branch):

- `creative_suite/config.py` — declares `wolfcam_baseq3 = tools/wolfcamql/baseq3` and `full_catalog_json = tools/game-assets/FULL_CATALOG.json` properties. Present on this branch.
- `tools/game-assets/q3a-extracted/` — extracted Q3A subset (wolfcam-era cache, should be deprecated per Rule ENG-1).
- `.claude/worktrees/creative-suite-v2/creative_suite/inventory/{catalog.py,ingest.py}` — the inventory ingestion pipeline that reads Steam paks directly (per ENG-1). Not on this branch.
- `.claude/worktrees/creative-suite-v2/creative_suite/api/packs.py` — API serving pack catalog. Not on this branch.
- `.claude/worktrees/creative-suite-v2/phase1/sound_templates/pak00_sound_inventory.txt` — one pre-extracted category list.

**Not yet present:** a single in-process Python consumer on `design/phase1-pantheon-system` that both reads paks and exposes them. The loader lives on the other branch(es).

### `tools/game-assets/` state
Currently contains only `q3a-extracted/demos/`. The manifesto's `tools/game-assets/FULL_CATALOG.json` is referenced by `creative_suite/config.py` but is **not present** on this branch.

---

## Relationship to TR4SH QUAKE Manifesto

Authoritative spec: `docs/superpowers/specs/2026-04-17-tr4sh-quake-manifesto.md` (244 lines). Prior specs `2026-04-17-command-center-design.md` and `2026-04-17-engine-pivot-design.md` are declared as merging into the manifesto but not yet renamed.

### Track A — Engine Fork (~25 build-days)
| Sprint | Uses | Status |
|---|---|---|
| A1 Fork q3mme, build clean | `tools/quake-source/q3mme/` | **Not started.** Last upstream commit 2022-10-03. No local `tr4sh-quake/engine/` tree exists. |
| A2 Port wolfcamql protocol 73 patches | `wolfcamql-src/code/qcommon/{msg.c,qcommon.h}` + `wolfcamql-local-src/code/qcommon/qcommon.h:246` | Not started. Source-side patch surface identified (PROTOCOL_VERSION 91 with commented 73). |
| A3 Validate .dm_73 playback vs wolfcam golden | `phase2/dm73parser/` + `tools/wolfcamql/wolfcamql.exe` | Parser built, wolfcam reference on disk. Harness absent. |
| A4 Scene export module | new C module `cg_scene_export.c` | Not started. |
| A5 Capture-bus hooks | q3mme `cg_demos_capture.c` + quake3e renderer | Not started. |

### Track B — Command Center (~25 build-days, parallel)
- Relocated from `2026-04-17-command-center-design.md`. SQLite + FastAPI + Three.js.
- Working code exists on `creative-suite-v2-step2` / worktree, not on this branch.
- Sprint 8 "engine-abstraction layer" vanishes under the manifesto (since engine is owned).

### Track C — Agent (~20 build-days, starts after A4)
- Free cam, kill cam, image reader. Gemma3:4b-vision / LLaVA loop.
- Specs only. No code.

### Gates T1-T5 (manifesto §8)
None reached. T1 (engine fork builds clean) is the first unlock and requires the Gate ENG-1 decision from the merged engine-pivot spec.

---

## Open Decisions / Blockers

1. **Gate ENG-1 — protocol 73 path still unresolved.** `docs/superpowers/specs/2026-04-17-engine-pivot-design.md:64-99` recommends Path A now + Path B as Phase 3.5. User has not approved. Blocks all Track A work.
2. **Phase 2/parser source sync.** `phase2/dm73parser/src/*` is absent on this branch but the binary+tests are built. Needs explicit merge from `creative-suite-v2-step2` or equivalent before the manifesto's Track A sprint 3 (validation harness) can land on this branch.
3. **`creative_suite` source sync.** `config.py` on this branch points at `tools/game-assets/FULL_CATALOG.json` and pak catalogs that live on sibling branches only. The inventory ingest layer (Steam-pak reader) is not in this branch's working tree.
4. **q3mme upstream age.** Last commit 2022-10-03. Fork base is not actively maintained — any divergence we introduce is on us to carry forward. Manifesto acknowledges this implicitly but the fork-forward policy isn't written down.
5. **Ghidra track (FT-4).** `game-dissection/ghidra/projects/` is empty. Seven wolfcam binaries are staged in `game-dissection/ghidra/binaries/` (wolfcamql-11.1.exe, -11.3.exe + five DLLs) but no `.gpr` project exists. See the companion Ghidra-state research agent report for deeper detail. FT-4 commits "Ghidra every executable" but work hasn't begun on any binary.
6. **Spec rename overdue.** Manifesto §6 promises to rename the two prior specs with `-merged-into-tr4sh-quake-manifesto` suffix "next commit" (dated 2026-04-17). Two days later the rename hasn't happened — low risk but a readability debt.
7. **Golden baseline coverage thin.** Parser's `tests/golden_baseline.json` tests obituary counts on 5 demos only, no field-level diff vs UDT. FT-1 spec demands field-agreement before trust; `mean_field_agreement_pct: null` signals that's unmet.

---

## Files of Note

Absolute paths (tracked OR present on disk, current branch unless noted):

**Specs & plans**
- `G:/QUAKE_LEGACY/docs/superpowers/specs/2026-04-17-tr4sh-quake-manifesto.md` (authoritative vision)
- `G:/QUAKE_LEGACY/docs/superpowers/specs/2026-04-17-engine-pivot-design.md` (merged-in, Path A/B/C)
- `G:/QUAKE_LEGACY/docs/superpowers/specs/2026-04-17-command-center-design.md` (merged-in)
- `G:/QUAKE_LEGACY/docs/specs/2026-04-16-quake-legacy-design.md` (overall architecture)

**Engine source trees (all under `G:/QUAKE_LEGACY/tools/quake-source/`)**
- `q3mme/trunk/code/cgame/` (manifesto's fork base — demos_camera.c, demos_capture.c, demos_cut.c, demos_effects.c, demos_fov.c)
- `wolfcamql-local-src/code/qcommon/qcommon.h` (line 246 — PROTOCOL_VERSION define, 73 sitting commented)
- `wolfcamql-src/code/qcommon/msg.c` (protocol-73 parse patches to lift)
- `wolfcamql-local-src/code/cgame/wolfcam_consolecmds.c` (full wolfcam CVAR/cmd inventory surface for FT-4)
- `quake3e/code/qcommon/qcommon.h:289-294` (clean dual-protocol pattern — 68/71 toggleable)
- `uberdemotools/UDT_DLL/src/analysis_obituaries.cpp` (reference for our obit parser)

**Custom parser (FT-1)**
- `G:/QUAKE_LEGACY/phase2/dm73parser/build/dm73dump.exe` (CLI, 68 KB, runs)
- `G:/QUAKE_LEGACY/phase2/dm73parser/build/dm73_tests.exe` (GTest binary, 242 KB)
- `G:/QUAKE_LEGACY/phase2/dm73parser/build/dm73parser.lib` (608 KB static lib)
- `G:/QUAKE_LEGACY/phase2/dm73parser/tests/golden_baseline.json` (5-demo obit baseline)
- (sources absent on this branch — recover from `creative-suite-v2-step2`)

**Steam pak ingestion**
- `C:/Program Files (x86)/Steam/steamapps/common/Quake Live/baseq3/pak00.pk3` (QL, 962 MB, READ-ONLY per Rule ENG-4)
- `C:/Program Files (x86)/Steam/steamapps/common/Quake 3 Arena/baseq3/pak0.pk3` (Q3A, 479 MB)
- `G:/QUAKE_LEGACY/docs/research/steam-pak-manifest-2026-04-17.json` (full enumeration, 13 358 files)
- `G:/QUAKE_LEGACY/docs/research/steam-pak-inventory-2026-04-17.md` (narrative)
- `G:/QUAKE_LEGACY/docs/visual-record/2026-04-17/steam-paks-proof/README.md` (ENG-1 proof)
- `G:/QUAKE_LEGACY/creative_suite/config.py` (consumer config — present on branch)
- `.claude/worktrees/creative-suite-v2/creative_suite/inventory/{catalog.py,ingest.py}` (ingestion implementation — NOT on this branch)

**Reference docs**
- `G:/QUAKE_LEGACY/docs/reference/dm73-format-deep-dive.md` (1 337 lines — FT-1 authoritative spec)
- `G:/QUAKE_LEGACY/docs/reference/wolfcam-commands.md` (789 lines)
- `G:/QUAKE_LEGACY/docs/reference/quake-asset-sources.md` (HD pack sourcing)
- `G:/QUAKE_LEGACY/docs/reference/game-asset-catalog.md` (785 lines)
- `G:/QUAKE_LEGACY/tools/quake-source/REPOS.md` (186-line rationale per fork)

**Ghidra (cross-ref only — see companion agent report)**
- `G:/QUAKE_LEGACY/game-dissection/ghidra/binaries/wolfcamql-11.{1,3}.exe` + DLLs (staged, no project yet)
- `G:/QUAKE_LEGACY/game-dissection/ghidra/projects/` (empty)

---

*End of report. Status: parser binary green; parser sources off-branch; steam paks catalogued; engine-fork work blocked on Gate ENG-1 user decision.*
