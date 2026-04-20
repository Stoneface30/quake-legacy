# Engine Folder Unification Plan — 2026-04-19

**Author:** planning agent (read-only survey)
**Status:** Proposed — no files moved yet
**Scope:** Collapse the two-tier scatter (`tools/quake-source/` raw clones vs `engine/engines/` dissection outputs) into **one** unified engine folder. Absorb wolfcam's knowledge, then retire the wolfcam-specific source trees per the user directive:

> *"I'd rather have one folder that contains all the engine all the dissection and that everything work together, wolfcam once ingested need to disappear and we need to suck all the knowledge."*

---

## 0. Executive summary

The user's goal is already **~70% executed** — just never closed out. `engine/engines/_canonical/` (583 MB) + `_diffs/` (5 MB of 513 patch-docs) + `_docs/` (199 KB of per-engine notes) + `_manifest/` (inventory + canonical_map.json + DELETE_READY.md) already represent the unified tree. `tools/quake-source/` still holds the pristine clones (1.15 GB across 18 trees) because the 2026-04-17 `DELETE_READY.md` was never executed — it sits one approval away from deletion.

What's missing to truly be "one folder that contains all the engine all the dissection":

1. `engine/ghidra/` (binary RE) lives next to `engines/` but not inside it — minor, but a merge tightens the "one roof" story.
2. The FT-1 custom C++ parser (`phase2/dm73parser/`) pulls vendored wolfcam `huffman.c` from `tools/quake-source/wolfcamql-src/code/qcommon/huffman.c` (confirmed by `engine-ingestion-state-2026-04-19.md:74`). The vendor copy lives **inside** `phase2/dm73parser/vendor/qcommon/`, so the original source-tree reference is already gone at build-time — but once we retire `tools/quake-source/`, the *spec* pointers (HUMAN-QUESTIONS.md:127, CLAUDE.md:507-508) break unless rewritten to the new path.
3. The `_manifest/build_canonical.py` + `build_inventory.py` scripts still point at `tools/quake-source/` as their `ROOT` constant. If that directory is wiped, those scripts become non-executable — fine as archeology but a footgun for anyone re-running inventory.
4. The wolfcam-specific source trees (`wolfcamql-src`, `wolfcamql-local-src`) are present **both** in `tools/quake-source/` AND as per-tree-variant dirs under `engine/engines/{wolfcamql-src,wolfcamql-local-src}/`. Per `SYNTHESIS.md:38-41`, `wolfcamql-src` is the "GOLDEN TREE for protocol-73 knowledge". We cannot hard-delete it — we must first absorb the delta as a patch series under the unified folder, then delete the whole-tree copy.
5. `engine/wolfcam-knowledge-ingest/` exists only on a sibling worktree (`.claude/worktrees/hopeful-shtern-7fe850/`) with 7 canonical knowledge docs (00-overview through 06-protocol-73-port-plan). This is the "suck all the knowledge" artifact — it needs to land in the unified folder on `main` before wolfcam retires.

The plan below executes exactly those five closings.

---

## 1. Current scatter inventory

| Location | Purpose | Size / files | Retention decision |
|---|---|---:|---|
| `tools/quake-source/REPOS.md` | 186-line hand-written rationale per fork | 20 KB | **Move** → `engine/engines/REPOS.md` (already redirects there; cut out the middleman) |
| `tools/quake-source/darkplaces/` | Q1 engine w/ modern renderer | 11 MB / 303 files | **Delete** after confirming variant dir `engine/engines/darkplaces/` carries near-dup diffs |
| `tools/quake-source/demodumper/` | Python .dm_73 score-format parser | 340 KB / 16 files | **Delete** after variant check |
| `tools/quake-source/gtkradiant/` | Map editor (reference) | 57 MB / 1,317 files | **Delete** after variant check |
| `tools/quake-source/ioquake3/` | Clean Q3 baseline | 40 MB / 1,084 files | **Delete** — canonical copy is primary authority for `cl_avi.c` |
| `tools/quake-source/openarena-engine/` | OA engine fork | 36 MB / 1,183 files | **Delete** after variant check |
| `tools/quake-source/openarena-gamecode/` | OA game VM | 8.5 MB / 314 files | **Delete** after variant check |
| `tools/quake-source/q3mme/` | Movie-maker's edition (Track A fork base) | 70 MB / 1,000 files | **KEEP as working fork base**, but move under unified folder — `engines/_forks/q3mme/` — because engine-fork worktree needs a writable source tree |
| `tools/quake-source/q3vm/` | Standalone QVM interpreter | 2.7 MB / 127 files | **Delete** after variant check |
| `tools/quake-source/qldemo-python/` | Python dm_73 parser | 419 KB / 35 files | **Delete** after variant check |
| `tools/quake-source/quake1-source/` | id Q1 source | 16 MB / 626 files | **Delete** after variant check |
| `tools/quake-source/quake2-source/` | id Q2 source | 8.1 MB / 371 files | **Delete** after variant check |
| `tools/quake-source/quake3-source/` | id Q3 ground truth | 31 MB / 1,551 files | **Delete** — canonical authority for Huffman + msg.c ancestor |
| `tools/quake-source/quake3e/` | Modern Q3 fork (Vulkan, dual-protocol) | 79 MB / 653 files | **Delete** after variant check |
| `tools/quake-source/uberdemotools/` | Reference .dm_73 parser + prebuilt UDT_json.exe | 619 MB / 879 files | **Split:** source → delete, prebuilt binaries → `tools/uberdemotools/` (new slim dir) — uberdemotools ships ~600 MB of tests + old builds we don't need, but the x86 `UDT_json.exe` binaries are active tooling |
| `tools/quake-source/wolfcamql-src/` | **Protocol-73 golden tree** | 127 MB / 1,725 files | **Absorb then delete** — extract proto-73 patch series (§4 below) before whole-tree removal |
| `tools/quake-source/wolfcamql-local-src/` (not git) | Exact source matching shipped wolfcamql.exe | 19 MB / 1,071 files | **Absorb then delete** — diff against wolfcamql-src, preserve deltas as `shipped-binary-deltas.patch` |
| `tools/quake-source/wolfet-source/` | W:ET (cross-ref only) | 33 MB / 1,357 files | **Delete** after variant check |
| `tools/quake-source/yamagi-quake2/` | Modern Q2 fork | 13 MB / 320 files | **Delete** after variant check |
| **`tools/quake-source/` total** | | **1,174 MB / 13,932 files** | |
| `engine/REPOS.md` | Index (duplicates tools/quake-source/REPOS.md scope?) | 20 KB | Review vs `engines/SYNTHESIS.md`, merge or delete |
| `engine/engines/_canonical/` | SHA-256-deduped merged tree (authority order wolfcamql-src > quake3e > q3mme > ioquake3 > quake3-source > ...) | 583 MB / 9,895 src files | **KEEP** — this is the target canonical tree |
| `engine/engines/_diffs/` | 513 per-file `.diff.md` for near-dup files across variants | 5 MB | **KEEP** — patch-series source of truth for proto-73 port |
| `engine/engines/_docs/` | Per-engine architecture notes (6 docs for porting targets, 3 docs for ref-only) | 199 KB | **KEEP**, rename → `engines/dissection/` (clearer intent) |
| `engine/engines/_manifest/` | inventory.json, canonical_map.json, build_*.py, DELETE_READY.md, summary.md | 7.6 MB | **KEEP**, rewrite `ROOT` constants to new layout |
| `engine/engines/{darkplaces,demodumper,…yamagi-quake2}/` | 18 per-engine variant dirs holding only the files that DIFFER from `_canonical/` | 24 MB total | **KEEP** — cheap cross-reference |
| `engine/engines/SYNTHESIS.md` | Master synthesis (family tree, authority order, migration paths) | 11 KB | **KEEP**, becomes the unified folder's README |
| `engine/ghidra/` | FT-4 Ghidra RE outputs (binaries/, reports/, symbols/, ipc-maps/, scripts/, projects/) | ~350 MB (binaries staged) | **Move** → `engines/ghidra/` (already under engine, but unify under engines) |
| `engine/assets/` | asset dissection (not engine-specific) | — | **Leave in place** — out of engine scope |
| `engine/graphify-out/` | Knowledge graphs for engine trees (wolfcam/cgame, q3mme/cgame, canonical, …) | — | **Leave in place** — graphify is a tool output, not engine source |
| `engine/.graphify_*.json` | Graphify working files (analysis, detect, extract, labels, semantic, chunk3/5/6) | 3 MB | **Leave in place** — already under engine root |
| `phase2/dm73parser/` (sibling branches, not current) | FT-1 custom C++ parser; vendors `huffman.c`, `huff_table.c` from wolfcamql-src/code/qcommon/ | 608 KB lib + sources | **Leave in phase2/**, rewrite vendor SOURCES.md to reference new engine-tree path |
| `docs/reference/dm73-format-deep-dive.md` | 1,337-line authoritative spec, line 1180 references `tools/quake-source/` | 37 KB | **Keep in docs/reference/**, rewrite line 1180 |
| `docs/reference/wolfcam-commands.md` | 789 lines — cvar/cmd inventory derived from wolfcam source | 28 KB | **Keep in docs/reference/** |
| `docs/INDEX.md` (lines 152, 184, 230) | top-level index, references `tools/quake-source/` | 11 KB | **Keep**, rewrite 3 lines |
| `.claude/worktrees/engine-fork/` | Engine-fork worktree for q3mme proto-73 port (Gate ENG-1 Path A approved per CLAUDE.md context) | — | **Leave as-is during migration**; re-sync after main lands the new layout so the worktree's q3mme source pointer updates |
| `.claude/worktrees/hopeful-shtern-7fe850/engine/wolfcam-knowledge-ingest/` | 7 canonical knowledge docs (00-overview..06-proto-73-port-plan) | — | **Cherry-pick into main** at unified folder `engines/wolfcam-knowledge/` |
| `tools/quake-source/wolfcamql-src/make-package.py` | wolfcam build script (the only non-manifest .py hit for `quake-source`) | — | Deleted together with `wolfcamql-src/` |

---

## 2. Target folder layout

Chosen root name: **`engine/engines/`** (existing — no rename). Rationale:
- It's already the consolidation target. Everything merged into it over 2026-04-17.
- `engine/` is the right semantic home for "we took binaries/source apart to understand them".
- Renaming it now (e.g. to `engine/`) would churn hundreds of cross-refs with no functional gain.

```
G:/QUAKE_LEGACY/engine/
├── README.md                      # ← was engines/SYNTHESIS.md, promoted; links to every subsection
├── engines/
│   ├── README.md                  # ← was SYNTHESIS.md, family tree + authority order + per-file diffs
│   ├── REPOS.md                   # ← moved from tools/quake-source/REPOS.md (186-line rationale)
│   ├── _canonical/                # UNCHANGED — 583 MB SHA-256-deduped merged tree
│   ├── _diffs/                    # UNCHANGED — 513 .diff.md patch docs for near-dup files
│   ├── dissection/                # RENAMED from _docs/ (clearer: per-engine ARCHITECTURE/QUIRKS/etc)
│   │   ├── wolfcamql-src/         # 6-doc treatment (ARCHITECTURE, EXTENSION_POINTS, PROTOCOL_LAYER, …)
│   │   ├── q3mme/                 # 6-doc treatment
│   │   ├── quake3e/               # 6-doc treatment
│   │   └── {ioquake3, quake3-source, uberdemotools, …}/  # 3-doc treatment
│   ├── _manifest/                 # UNCHANGED contents, rewrite ROOT constant (§5)
│   │   ├── build_inventory.py     # ROOT = engine/engines/variants/
│   │   ├── build_canonical.py     # ROOT = engine/engines/variants/
│   │   ├── inventory.json, canonical_map.json, summary.md, DELETE_READY.md (updated)
│   │   └── generate_light_docs.py
│   ├── variants/                  # RENAMED container for per-tree near-dup variant dirs
│   │   ├── darkplaces/            # moved from engines/darkplaces/
│   │   ├── demodumper/
│   │   ├── gtkradiant/
│   │   ├── ioquake3/
│   │   ├── openarena-engine/
│   │   ├── openarena-gamecode/
│   │   ├── q3vm/
│   │   ├── qldemo-python/
│   │   ├── quake1-source/
│   │   ├── quake2-source/
│   │   ├── quake3-source/
│   │   ├── quake3e/
│   │   ├── uberdemotools/
│   │   ├── wolfet-source/
│   │   └── yamagi-quake2/
│   │       (note: q3mme and wolfcamql-{src,local-src} removed from variants/ — see _forks/ and wolfcam-knowledge/)
│   ├── _forks/                    # LIVE source trees we intend to build / patch / ship
│   │   └── q3mme/                 # MOVED from tools/quake-source/q3mme/ — writable, engine-fork worktree points here
│   ├── wolfcam-knowledge/         # CHERRY-PICKED from hopeful-shtern worktree wolfcam-knowledge-ingest/
│   │   ├── 00-overview.md
│   │   ├── 01-commands-cvars.md
│   │   ├── 02-protocol-73-patches.md     # the protocol-73 deltas, extracted AS DOCUMENTATION
│   │   ├── 03-ipc-commands.md
│   │   ├── 04-fragmovie-features.md
│   │   ├── 05-quirks-and-gotchas.md
│   │   ├── 06-protocol-73-port-plan.md
│   │   ├── patches/                      # NEW: proto-73 deltas AS GIT-FORMAT-PATCH files
│   │   │   ├── 0001-msg.c-protocol-73-entity-playerstate-fields.patch
│   │   │   ├── 0002-cl_parse.c-gamestate-configstring-indexing.patch
│   │   │   ├── 0003-cl_demo.c-demo-read-loop.patch
│   │   │   ├── 0004-qcommon.h-PROTOCOL_VERSION-91-with-73-alias.patch
│   │   │   ├── 0005-bg_public.h-MOD-EV-table-QL-extensions.patch
│   │   │   ├── 0006-huffman.c-table-verification.patch
│   │   │   └── 0007-cgame-wolfcam_*.c-scoreboard-and-FX.patch
│   │   ├── shipped-binary-deltas.patch   # diff(wolfcamql-src, wolfcamql-local-src) — the deltas between
│   │   │                                  # the GitHub mirror and the tarball that matches the shipped .exe
│   │   └── _scripts/                      # gen.py and helpers for re-building the knowledge docs
│   ├── ghidra/                    # MOVED from engine/ghidra/
│   │   ├── README.md              # binary-to-source mapping (which source tree each RE'd binary derives from)
│   │   ├── binaries/              # wolfcamql-11.{1,3}.exe, DLLs, WolfWhisperer.exe, StartupWizard.exe
│   │   ├── reports/               # qagamex86_preliminary.md, wolfcamql-11.3.*, _analysis-roadmap.md, _binary-inventory.md
│   │   ├── ipc-maps/              # qagame_MOD_enum.seed.txt, qagame_EV_enum.seed.txt, wolfcamql_capture_cvars.seed.txt
│   │   ├── projects/              # (empty today — Ghidra .gpr projects once they exist)
│   │   ├── scripts/               # pe_probe.py
│   │   └── symbols/               # .probe.txt files per DLL/exe
│   └── parsers/                   # NEW pointer-hub for dm_73 parsers (docs only, sources stay put)
│       └── README.md              # links to phase2/dm73parser/ (FT-1) + variants/uberdemotools (reference) + variants/qldemo-python (reference)
├── assets/                        # UNCHANGED — not engine-specific
├── graphify-out/                  # UNCHANGED — tool output, not engine source
└── .graphify_*.json               # UNCHANGED
```

**Endgame of `tools/quake-source/`:** the directory does NOT exist. After the final deletion step, the only thing left under `tools/` is the tool binaries (`ffmpeg/`, `wolfcamql/`, `ghidra/`, `comfyui/`, `md3viewer/`, etc.), never source trees.

**Endgame of `tools/uberdemotools/`:** new slim dir holding ONLY the prebuilt x86/x64 `UDT_json.exe` + `UDT.dll` binaries (currently shipped inside `tools/quake-source/uberdemotools/UDT_DLL/`). Created by the migration, not currently existing.

---

## 3. Migration steps — atomic, ordered, verifiable

Every step is a single commit on a feature branch `feature/engine-folder-unification-2026-04-19` (never `main` directly, per Git Golden Rule). Each step has a verification hook; if verification fails, rollback = `git reset --hard HEAD~1` and the previous step remains intact.

### Pre-flight (step 0)
- Branch from `main` at `78709e98`.
- `pytest tests/ creative_suite/tests/ phase1/tests/` captures baseline: expect 133 green.
- `pyright creative_suite phase1 phase35 tools scripts` captures baseline: expect 176 errors.
- `git ls-files | grep -E "quake-source|wolfcamql-src|quake3-source"` captures full cross-ref baseline.
- User approval checkpoint: **user must confirm this plan before any `git mv` runs**.

### Step 1 — Promote `SYNTHESIS.md` to top-level READMEs
- `git mv engine/engines/SYNTHESIS.md engine/engines/README.md`
- **New file** `engine/README.md` linking to `engines/README.md`, `ghidra/README.md` (forward-ref), `assets/`, `graphify-out/`.
- Verification: `pytest` + `pyright` both unchanged (no code touched).

### Step 2 — Cherry-pick wolfcam-knowledge-ingest from sibling worktree
- Source: `.claude/worktrees/hopeful-shtern-7fe850/engine/wolfcam-knowledge-ingest/` (7 docs + `_scripts/gen.py`).
- Target: `engine/engines/wolfcam-knowledge/`.
- `git checkout hopeful-shtern-branch -- engine/wolfcam-knowledge-ingest/` then `git mv` into final path.
- Verification: all 7 `.md` files present; `gen.py` imports resolve.
- Creates the container for the proto-73 patches BEFORE we generate them (step 6).

### Step 3 — Move `tools/quake-source/REPOS.md` into engines/
- `git mv tools/quake-source/REPOS.md engine/engines/REPOS.md`
- Verification: `grep -r "tools/quake-source/REPOS.md" . --exclude-dir=.git` → must return 0 matches after step 9 rewrites.
- Note: this is the only file we move *out* of `tools/quake-source/` during migration. Everything else either stays (nothing stays), deletes, or was already copied into `_canonical/` back on 2026-04-17.

### Step 4 — Rename `engines/_docs/` → `engines/dissection/`
- `git mv engine/engines/_docs engine/engines/dissection`
- Update `engines/README.md` (was SYNTHESIS) references from `_docs/` to `dissection/`.
- Verification: `grep -r "_docs/" engine/engines/` → no hits.

### Step 5 — Move per-engine variant dirs under `engines/variants/`
- For each of {darkplaces, demodumper, gtkradiant, ioquake3, openarena-engine, openarena-gamecode, q3vm, qldemo-python, quake1-source, quake2-source, quake3-source, quake3e, uberdemotools, wolfet-source, yamagi-quake2, wolfcamql-src, wolfcamql-local-src}: `git mv engine/engines/<name> engine/engines/variants/<name>`.
- Note: `q3mme` is NOT moved here — it's a live fork target (step 7).
- Note: `wolfcamql-src` and `wolfcamql-local-src` ARE moved here temporarily; they're retired in step 8 after the proto-73 patches are extracted.
- Verification: `ls engine/engines/variants/ | wc -l` = 17 (16 pure variants + the two wolfcam trees transiting).

### Step 6 — Extract protocol-73 patch series (the "absorb wolfcam knowledge" step)
- This is the pivotal step. Wolfcam source → patch series under `engines/wolfcam-knowledge/patches/`.
- Authoritative file list (from SYNTHESIS.md §Interesting diff files + proto73-port-review-2026-04-17.md):
  - `code/qcommon/msg.c` — 85 KB — entity/PS field tables, huffman seed
  - `code/qcommon/net_chan.c` — QL channel framing
  - `code/qcommon/huffman.c` — verify no QL-specific table changes
  - `code/qcommon/common.c` — shared helpers, CVAR_/Cmd_ additions
  - `code/qcommon/q_shared.h` — MAX_CLIENTS, MOD_*, EV_*, PROTOCOL_VERSION
  - `code/qcommon/qcommon.h` — line 246 `#define PROTOCOL_VERSION 91` + commented 73
  - `code/client/cl_parse.c` — protocol detection, gamestate parse (71 KB)
  - `code/client/cl_demo.c` — demo file read loop
  - `code/client/cl_cgame.c` — trap_ dispatch into cgame VM
  - `code/client/cl_main.c` — top-level state machine
  - `code/server/sv_snapshot.c` — snapshot entity selection
  - `code/server/sv_game.c` — game VM trap interface
  - `code/game/bg_public.h` — 40 KB QL configstring indices + MOD + EV table
  - `code/cgame/wolfcam_*.c` — wolfcam's QL-aware cgame modules (kept whole as new modules, not a patch)
- For each file, generate `diff -u <quake3-source>/<file> <wolfcamql-src>/<file> > patches/NNNN-<file>.patch` using the already-built `_diffs/` as the input corpus (the hard work is done — these files already have `.diff.md` at `engines/_diffs/code/qcommon/msg.c.diff.md` etc).
- **Plus** `diff -u <wolfcamql-src>/<file> <wolfcamql-local-src>/<file>` for the shipped-binary delta, combined into `shipped-binary-deltas.patch`.
- Each patch keeps GPL-2.0 attribution in a header comment block noting upstream file + commit.
- Verification: `git apply --check patches/*.patch` against a checked-out copy of `_canonical/code/qcommon/` — must apply cleanly (this is the sanity check that the patch series is syntactically sound; it does NOT mean q3mme builds with it applied — that's Phase 3.5 Track A work).
- **Outcome:** wolfcam's unique proto-73 knowledge now lives as `engines/wolfcam-knowledge/patches/*.patch` + the 7 curated `.md` docs. The 146 MB `wolfcamql-{src,local-src}` directories become purely archival.

### Step 7 — Promote q3mme to `engines/_forks/q3mme/`
- `git mv tools/quake-source/q3mme engine/engines/_forks/q3mme`
- **New file** `engine/engines/_forks/README.md` declaring `_forks/` contains writable source trees, not reference clones, and listing q3mme as the proto-73 port target per `docs/research/gate-eng-1-decision-2026-04-19.md`.
- Update the engine-fork worktree (`.claude/worktrees/engine-fork/`) — it should continue tracking the same branch; after this commit lands, the worktree's next `git pull` picks up the new path. No manual worktree surgery needed.
- Verification: `ls engine/engines/_forks/q3mme/trunk/code/cgame/demos_*.c` → 5 files (demos_camera, demos_capture, demos_cut, demos_effects, demos_fov).

### Step 8 — Retire wolfcam source trees
- Prerequisite: step 6 complete, patches verified, wolfcam-knowledge/ cherry-picked.
- `git rm -r engine/engines/variants/wolfcamql-src`
- `git rm -r engine/engines/variants/wolfcamql-local-src`
- `_canonical/` ALREADY contains the authority-order merge (wolfcamql-src is rank 1 per SYNTHESIS.md:145) — the QL files that made it into `_canonical/` stay there. This is the whole point of `_canonical/`: wolfcam's contribution is preserved as the merged source, not as a separate tree.
- Update `engines/README.md` "Cleanup record" section: "2026-04-19 Phase A3: wolfcam source trees retired. Knowledge preserved as patch series + docs."
- Verification: `grep -r "wolfcamql-src\|wolfcamql-local-src" engine/engines/` → hits only in `_canonical/` (expected — the canonical files originated there) + `_diffs/` (patch docs reference the original tree), zero hits in `variants/`.
- **This is "wolfcam disappears"** — the user's directive executed.

### Step 9 — Slim uberdemotools to binaries-only + delete the rest of tools/quake-source/
- Create `tools/uberdemotools/`:
  - Copy `tools/quake-source/uberdemotools/UDT_DLL/.build_vs2022/x86-Release/UDT_json.exe` (and x64, and UDT.dll equivalents) into `tools/uberdemotools/`.
  - Add `tools/uberdemotools/README.md` pointing at `engine/engines/variants/uberdemotools/` for source and at upstream mightycow/uberdemotools GitHub.
- **Bulk deletion** — execute `engine/engines/_manifest/DELETE_READY.md` rm-rf list:
  - `rm -rf tools/quake-source/darkplaces`
  - `rm -rf tools/quake-source/demodumper`
  - `rm -rf tools/quake-source/gtkradiant`
  - `rm -rf tools/quake-source/ioquake3`
  - `rm -rf tools/quake-source/openarena-engine`
  - `rm -rf tools/quake-source/openarena-gamecode`
  - `rm -rf tools/quake-source/q3vm`
  - `rm -rf tools/quake-source/qldemo-python`
  - `rm -rf tools/quake-source/quake1-source`
  - `rm -rf tools/quake-source/quake2-source`
  - `rm -rf tools/quake-source/quake3-source`
  - `rm -rf tools/quake-source/quake3e`
  - `rm -rf tools/quake-source/uberdemotools`
  - `rm -rf tools/quake-source/wolfet-source`
  - `rm -rf tools/quake-source/yamagi-quake2`
  - (wolfcamql-src, wolfcamql-local-src already gone after step 8's `git rm`; q3mme already moved in step 7; REPOS.md already moved in step 3)
- **Final:** `rmdir tools/quake-source/` — the directory disappears entirely.
- Verification: `ls tools/quake-source/ 2>&1 | grep "No such file"` — success.
- Size accounting:
  - Before: 1,174 MB
  - After: 0 MB (directory gone)
  - Newly created `tools/uberdemotools/`: ~1.5 MB (binaries only)
  - `engines/_forks/q3mme/`: 70 MB (moved, not copied — no size change to repo total)
  - `engines/wolfcam-knowledge/patches/`: ~200 KB (the absorbed knowledge)
  - **Net repo reduction: ~1,100 MB** (primarily uberdemotools test corpora and wolfcamql-src duplication)

### Step 10 — Rewrite cross-references
See §5 below for the exhaustive table. One commit, touching 6 files.

### Step 11 — Rewrite `_manifest/` ROOT constants
- `engine/engines/_manifest/build_inventory.py:17`: `ROOT = Path(r"G:/QUAKE_LEGACY/tools/quake-source")` → `ROOT = Path(r"G:/QUAKE_LEGACY/engine/engines/variants")`
- `engine/engines/_manifest/build_canonical.py:19`: same change
- `build_canonical.py:200`: comment update (`Sum up the bytes currently in tools/quake-source/` → `... in engines/variants/`)
- `build_canonical.py:223`: `f.write(f"rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/{t}'\n")` → `f.write(f"rm -rf 'G:/QUAKE_LEGACY/engine/engines/variants/{t}'\n")` (for future DELETE_READY regeneration; operates on variants/ now)
- Update `DELETE_READY.md` itself to reflect new paths + add a "DONE" section noting the 2026-04-19 execution.
- Verification: dry-run `python engine/engines/_manifest/build_inventory.py` — should emit inventory against variants/ and not crash (it scans dirs that still exist).

### Step 12 — Move ghidra/ under engines/
- `git mv engine/ghidra engine/engines/ghidra`
- **New** `engine/engines/ghidra/README.md` with binary-to-source mapping:
  - `binaries/wolfcamql-11.3.exe` → built from `engines/variants/...` (wolfcam retired — these were source trees that are gone after step 8; map to `engines/wolfcam-knowledge/patches/` instead)
  - `binaries/qagamex86.dll` → built from `engines/_canonical/code/game/`
  - etc.
- Update `engine/ghidra/reports/qagamex86_preliminary.md:90` and `_analysis-roadmap.md:13`:
  - `tools/quake-source/wolfcamql-src/code/game/` → `engine/engines/_canonical/code/game/` + cross-ref to `engines/wolfcam-knowledge/patches/`
- Verification: `pytest` + `pyright` still baseline.

### Step 13 — Update `docs/INDEX.md`
- Line 152: `tools/quake-source/ — see REPOS.md` → `engine/engines/ — see README.md`
- Line 184 (graphify table): `tools/quake-source/wolfcamql-local-src/code/game/graphify-out/graph.html` — this path is gone after step 8. Options:
  - (a) Delete the row (the graph was regenerated against `_canonical/` in the "canonical engine tree (2026-04-17)" row).
  - (b) Regenerate against `_canonical/code/game/` and update path.
  - **Recommended:** (a) delete; the canonical-tree row covers the same ground at higher scope.
- Line 230: `tools/quake-source/.../game/graphify-out/GRAPH_REPORT.md ← wolfcam/game` → delete (same reason).

### Step 14 — Final verification + PR
- `pytest tests/ creative_suite/tests/ phase1/tests/` → expect 133 green (no code change impacted tests).
- `pyright creative_suite phase1 phase35 tools scripts` → expect 176 (or fewer if any broken import resolves by removal).
- `git ls-files | grep -E "tools/quake-source"` → 0 hits.
- `grep -r "tools/quake-source" . --exclude-dir=.git --exclude-dir=.claude/worktrees` → 0 hits (worktrees excluded because they sync on next pull).
- Open PR targeting `main`, require user approval per Git Golden Rule.

---

## 4. Wolfcam absorption recipe

This is the critical "suck all the knowledge" mechanic. The 146 MB of `wolfcamql-{src,local-src}` source compresses to ~200 KB of patches + 7 curated docs. Here's the exact recipe:

### (a) Files that contribute unique knowledge
From `SYNTHESIS.md` §Interesting diff files and `proto73-port-review-2026-04-17.md`:

| Wolfcam file | Why it's unique | Ancestor to diff against | Destination |
|---|---|---|---|
| `code/qcommon/msg.c` | Proto-73 entity/playerstate field tables, Huffman seed modifications | `quake3-source/code/qcommon/msg.c` | `patches/0001-msg.c-protocol-73-entity-playerstate-fields.patch` |
| `code/qcommon/net_chan.c` | QL channel framing | `quake3-source/code/qcommon/net_chan.c` | patch-by-inclusion in 0001 |
| `code/qcommon/qcommon.h` | `PROTOCOL_VERSION 91` + commented 73 | `quake3-source/code/qcommon/qcommon.h` | `patches/0004-qcommon.h-PROTOCOL_VERSION-91-with-73-alias.patch` |
| `code/qcommon/common.c` | CVAR_*, Cmd_* additions | quake3-source | included in 0004 |
| `code/qcommon/q_shared.h` | MAX_CLIENTS bump, MOD_* additions, EV_* additions | quake3-source | included in 0005 |
| `code/qcommon/huffman.c` | Verify NO table changes (expect empty diff) | quake3-source | `patches/0006-huffman.c-table-verification.patch` (often empty — that's valuable confirmation) |
| `code/client/cl_parse.c` | gamestate parse, configstring indexing for QL | quake3-source | `patches/0002-cl_parse.c-gamestate-configstring-indexing.patch` |
| `code/client/cl_demo.c` | Demo read loop edits | quake3-source | `patches/0003-cl_demo.c-demo-read-loop.patch` |
| `code/client/cl_cgame.c` | trap_ dispatch additions | quake3-source | included in 0002 |
| `code/client/cl_main.c` | State machine edits | quake3-source | included in 0002 |
| `code/server/sv_snapshot.c` | Snapshot entity selection | quake3-source | included in 0003 (demo-side ref only) |
| `code/server/sv_game.c` | Game VM trap surface | quake3-source | included in 0003 |
| `code/game/bg_public.h` | QL configstring indices, MOD table, EV table | quake3-source | `patches/0005-bg_public.h-MOD-EV-table-QL-extensions.patch` |
| `code/cgame/wolfcam_*.c` (wolfcam_main, wolfcam_consolecmds, wolfcam_servercmds, wolfcam_ents, cg_fx_scripts) | No Q3 ancestor — these are wholly new modules | — (new files) | `patches/0007-cgame-wolfcam_*.c-scoreboard-and-FX.patch` as file-additions |

### (b) Where each piece lands
- **Patches** → `engines/wolfcam-knowledge/patches/` (git-format-patch style, GPL-2.0 header preserved in each).
- **Whole-file wolfcam modules** (wolfcam_*.c that have no Q3 ancestor) → emitted as file-addition patches in 0007, keeping GPL-2.0 headers.
- **Conceptual knowledge** → `engines/wolfcam-knowledge/00..06-*.md` (already written on the hopeful-shtern worktree; cherry-pick carries them as-is).
- **Cvar/cmd inventory** → `docs/reference/wolfcam-commands.md` (already exists, 789 lines — stays in docs/reference/, referenced from 01-commands-cvars.md).
- **Shipped-binary deltas** → `engines/wolfcam-knowledge/shipped-binary-deltas.patch` (single patch; small — wolfcamql-src vs wolfcamql-local-src differ only in local build patches).

### (c) What gets deleted after absorption
- `engine/engines/variants/wolfcamql-src/` (the per-tree variant dir holding near-dup files — already thin because `_canonical/` got the authoritative copy)
- `engine/engines/variants/wolfcamql-local-src/` (same)
- `tools/quake-source/wolfcamql-src/` (original source tree — 127 MB)
- `tools/quake-source/wolfcamql-local-src/` (19 MB)
- Total deleted after step 8: ~165 MB of wolfcam source redundancy
- **Preserved:** the `_canonical/` tree (wolfcam is authority rank 1 → many files came from wolfcam in the merge), the 7 knowledge docs, the 7 patch files, the Ghidra binary artifacts of wolfcamql-11.x.exe

### (d) Verification the absorption is sound
After step 6:
- Every patch in `patches/` applies cleanly via `git apply --check` against `_canonical/code/`.
- Every wolfcam-unique symbol (grep for `PROTOCOL_VERSION`, `wolfcam_*`, `CG_Wolfcam*`, `WC_*`) appears in either `_canonical/` (merged) or `patches/` (delta) or `00..06-*.md` (concept).
- `wolfcam-knowledge/00-overview.md` lists one-to-one which original `wolfcamql-src/code/*.c` files each patch derives from; any file not accounted for = bug.

---

## 5. Cross-reference rewrites

Every file containing `tools/quake-source` outside of `tools/quake-source/` itself, worktrees, and the `_manifest/build_*.py` files (which get their own step 11):

| File | Line | Current | New |
|---|---:|---|---|
| `CLAUDE.md` | 507 | `tools/quake-source/wolfcamql-local-src/code/cgame/wolfcam_consolecmds.c` | `engine/engines/wolfcam-knowledge/patches/0007-cgame-wolfcam_*.c-scoreboard-and-FX.patch` (+ narrative pointer) |
| `CLAUDE.md` | 508 | `tools/quake-source/wolfcamql-src/code/cgame/wolfcam_consolecmds.c` | same |
| `CLAUDE.md` | 545 | `tools/quake-source/quake3-source/` | `engine/engines/variants/quake3-source/` |
| `CLAUDE.md` | 546 | `tools/quake-source/q3mme/` | `engine/engines/_forks/q3mme/` |
| `CLAUDE.md` | 547 | `tools/quake-source/quake3e/` | `engine/engines/variants/quake3e/` |
| `CLAUDE.md` | 548 | `tools/quake-source/uberdemotools/` | `engine/engines/variants/uberdemotools/` + `tools/uberdemotools/` (binaries) |
| `docs/INDEX.md` | 152 | `tools/quake-source/` — see REPOS.md | `engine/engines/` — see README.md |
| `docs/INDEX.md` | 184 | wolfcam/game row | DELETE row (canonical-tree row supersedes) |
| `docs/INDEX.md` | 230 | `tools/quake-source/.../game/graphify-out/GRAPH_REPORT.md` | DELETE line |
| `HUMAN-QUESTIONS.md` | 102 | `tools/quake-source/uberdemotools/UDT_DLL/premake/` | `engine/engines/variants/uberdemotools/UDT_DLL/premake/` |
| `HUMAN-QUESTIONS.md` | 127 | `tools/quake-source/wolfcamql-src/code/` | `engine/engines/_canonical/code/` (authoritative merged copy; + note wolfcam-knowledge/patches/ for the deltas) |
| `docs/reference/dm73-format-deep-dive.md` | 1180 | `G:/QUAKE_LEGACY/tools/quake-source/` | `G:/QUAKE_LEGACY/engine/engines/` |
| `docs/research/proto73-port-review-2026-04-17.md` | 323-325 | three `tools/quake-source/wolfcamql-src/code/...` refs | `engine/engines/_canonical/code/...` (or `engines/variants/wolfcamql-src/code/...` if reader needs wolfcam-specific view) |
| `docs/research/engine-ingestion-state-2026-04-19.md` | 11, 23, 46, 133, 175, 204 | `tools/quake-source/` refs | same rewrite pattern |
| `docs/research/ghidra-rip-state-2026-04-19.md` | 43, 77, 85 | `tools/quake-source/uberdemotools/` / `tools/quake-source/wolfcamql-src/` | `engines/variants/uberdemotools/` / `engines/wolfcam-knowledge/patches/` |
| `docs/sessions/2026-04-17-wrapup-TOMORROW.md` | 38, 146, 152-154, 175-176 | historical context, keep as-is? | Add a footnote: "As of 2026-04-19 these paths moved to `engine/engines/` — see engine-folder-unification-plan-2026-04-19.md" |
| `docs/specs/highlight-criteria-v1.md` | 197 | `tools/quake-source/uberdemotools/UDT_DLL/` | `engine/engines/variants/uberdemotools/UDT_DLL/` |
| `docs/visual-record/2026-04-17/steam-paks-proof/README.md` | 48 | `tools/quake-source/quake3-source/` | `engine/engines/variants/quake3-source/` |
| `engine/ghidra/reports/qagamex86_preliminary.md` | 90 | `tools/quake-source/wolfcamql-src/code/game/` | `engine/engines/_canonical/code/game/` |
| `engine/ghidra/reports/_analysis-roadmap.md` | 13 | `tools/quake-source/wolfcamql-src/` | `engine/engines/wolfcam-knowledge/patches/` (+ note that source tree is retired, patches are the oracle now) |
| `engine/ghidra/reports/_binary-inventory.md` | 28, 30, 42, 43 | `tools/quake-source/...` | path rewrites per above table |
| `engine/engines/_manifest/build_inventory.py` | 17 | `ROOT = Path(r"G:/QUAKE_LEGACY/tools/quake-source")` | `ROOT = Path(r"G:/QUAKE_LEGACY/engine/engines/variants")` |
| `engine/engines/_manifest/build_canonical.py` | 19, 200, 223 | same + rm-rf template | `ROOT = variants/`; rm-rf template writes to variants/ |
| `engine/engines/_manifest/DELETE_READY.md` | 20-37 | rm-rf list | Keep as archival section; add "DONE 2026-04-19" header above; add new section for the post-migration state |

Total: **23 files touched** in the cross-reference rewrite commit. Zero consumer Python code affected (confirmed by the `grep` in §6 below).

---

## 6. Dependency chain — buildability at every intermediate state

**Critical insight from the survey:** no real consumer code (`creative_suite/`, `phase1/`, `phase35/`, `tests/`, `tools/download_tools.py`, `pyproject.toml`) references `tools/quake-source/`. The only Python files that reference it are the three `_manifest/*.py` scripts, all of which run *offline* against the engine tree; they are not called by pytest or by any runtime code path. Confirmed by:

```
grep "quake-source" **/*.py → 3 files (all _manifest/*.py) + 1 file (wolfcamql-src/make-package.py, deleted with wolfcam)
grep "quake-source" **/CMakeLists.txt → 0 hits
grep "quake-source" **/*.json → only in manifest-generated .json files
```

So the buildability invariant reduces to:
1. **pytest stays 133/133** at every step (no consumer code depends on these paths).
2. **pyright stays at 176 errors** at every step (documentation path changes don't affect typing).
3. **`phase2/dm73parser/` stays compilable** — it vendors `huffman.c` into `phase2/dm73parser/vendor/qcommon/`, which is already local to phase2. The only linkage to wolfcamql-src is a comment in `SOURCES.md` (rewritten in step 10 via the CLAUDE.md/HUMAN-QUESTIONS.md pattern).
4. **engine-fork worktree stays valid** — it references `tools/quake-source/q3mme/` via `docs/research/gate-eng-1-decision-2026-04-19.md`. After step 7 moves q3mme to `engines/_forks/q3mme/`, the worktree's next `git pull origin feature/engine-folder-unification-2026-04-19` picks up the move automatically (git tracks the rename). No manual surgery. If the worktree is actively editing q3mme source mid-migration, pause migration until worktree work lands.

**Ordering constraint** — step 6 (extract patches) MUST run BEFORE step 8 (delete wolfcam trees) because the patch extraction reads from `engines/variants/wolfcamql-src/` and `engines/variants/wolfcamql-local-src/`.

**Ordering constraint** — step 5 (move variants under variants/) MUST run BEFORE steps 6 and 8 because they reference `variants/wolfcamql-src/`.

**Ordering constraint** — step 9 (rm-rf tools/quake-source/*) is the *last* destructive step. It happens after all moves + patch extraction.

---

## 7. Risk & rollback

| Risk | Likelihood | Impact | Mitigation | Rollback |
|---|---|---|---|---|
| Step 6 patch extraction misses a wolfcam-unique file → knowledge loss after step 8 deletion | Medium | High | Before step 8, run a completeness check: `grep -rI "wolfcam\|WOLFCAM\|wc_" engines/variants/wolfcamql-src/code/ | wc -l` and confirm every unique symbol appears in either `_canonical/`, `patches/`, or `wolfcam-knowledge/*.md`. If < 100% coverage, skip step 8, iterate on step 6. | `git revert` step 8's commit; `git checkout <prev-sha> -- engines/variants/wolfcamql-*` restores the trees |
| GPL-2.0 header loss on vendored patches | Low | Legal/ethical | Each patch's file header preserves the `Copyright (C) id Software / wolfcam authors + GNU GPL v2` block verbatim (per FT-1 spirit rule in CLAUDE.md) | Git history has the original tree; re-extract if needed |
| CMakeLists hardcoded to `tools/quake-source/` | None observed | High if present | Grep confirmed zero hits in any CMakeLists.txt (dm73parser's vendor copy is internal to phase2/) | N/A |
| git history churn on 1.1 GB of moved trees | Certain | Minor — repo size grows because git keeps both old + new paths in history | Accept the churn; `git gc --aggressive` after merge to pack. Alternative = interactive rebase squash (not recommended — loses attribution of the 2026-04-17 canonicalization work). | N/A |
| engine-fork worktree has uncommitted q3mme edits when step 7 runs | Medium | High — edits lost if worktree is reset | User confirms worktree state before step 7 begins; if dirty, stash + apply after move | Worktree has its own reflog; `git reflog` recovers |
| DELETE_READY.md rm-rf runs before user approves the plan | High if skipped sign-off | Catastrophic (unrecoverable delete) | Pre-flight checkpoint: plan review by user is the gate. No `rm -rf` runs without step 0 acknowledgment. | Source trees exist on GitHub (shallow clones) + on upstream remotes in `.git/config` for the twelve live git checkouts — re-clone if needed |
| Two wolfcamql-* trees overlap in history → `git mv` conflict | Low | Low | Move is file-by-file per tree, not bulk | `git mv --reset` on failure |
| Worktrees hold stale copies of moved files | Certain but benign | None — worktrees self-sync on pull | Document in migration PR that worktree users should `git pull --rebase` post-merge | N/A |
| FT-1 dm73parser vendor `huffman.c` references SOURCES.md that points at wolfcam source | Low | Medium — docs-only drift | Step 10 rewrites SOURCES.md path; vendor/qcommon/huffman.c itself is self-contained | Revert SOURCES.md, keep code as-is |

---

## 8. Ghidra integration

FT-4 Ghidra work is the live RE track. Per `engine/ghidra/reports/_binary-inventory.md`, 9 binaries are staged under `binaries/` — wolfcamql-11.1.exe + 11.3.exe + 5 DLLs + StartupWizard.exe + WolfWhisperer.exe.

**Where FT-4 outputs land in the unified folder:**

```
engine/engines/ghidra/
├── README.md                      # NEW — binary→source mapping table:
│                                  #   wolfcamql-11.3.exe          → _canonical/code/client/ (Q3 base) + wolfcam-knowledge/patches/
│                                  #   wolfcamql-11.3_qagamex86.dll → _canonical/code/game/
│                                  #   wolfcamql-11.3_cgamex86.dll  → _canonical/code/cgame/ + wolfcam-knowledge/patches/0007
│                                  #   WolfWhisperer.exe           → (no source — RE target)
│                                  #   StartupWizard.exe           → (RCData 101 extracts WolfWhisperer — companion binary)
│                                  # Plus: this is also where FT-1 custom dm73parser cross-validates its
│                                  # parser output against Ghidra-decoded UDT_json.exe behavior.
├── binaries/                      # UNCHANGED paths — wolfcamql-*, qagamex86.dll, WolfWhisperer.exe
├── reports/
│   ├── _analysis-roadmap.md       # UPDATED: replaces tools/quake-source/ refs with engines/ paths
│   ├── _binary-inventory.md       # UPDATED: same
│   ├── qagamex86_preliminary.md   # UPDATED: cross-check section points at _canonical/code/game/
│   ├── wolfcamql-11.3.*           # PRESERVED — decompiled.c, functions.txt, strings.txt, symbols.json
│   ├── wolfcamql.md               # PRESERVED
│   └── wolfcamql_qvm.md           # PRESERVED
├── ipc-maps/                      # UNCHANGED — enum seeds
├── projects/                      # UNCHANGED — empty, awaits .gpr files
├── scripts/
│   └── pe_probe.py                # UNCHANGED
└── symbols/                       # UNCHANGED — .probe.txt per binary
```

**How Ghidra integrates with the rest of the unified folder:**

- When a Ghidra decompilation (e.g. wolfcamql-11.3.decompiled.c already exists) drifts from the source-tree truth, the drift becomes a new entry in `wolfcam-knowledge/shipped-binary-deltas.patch`. This is the `FT-4` → `FT-1` feedback loop the manifesto promises: Ghidra is the oracle, source + patches are the truth, drift = a compile-time build patch we didn't yet capture.
- `engines/parsers/README.md` links Ghidra's UDT_json.exe functions.txt to our `phase2/dm73parser/` implementation — the custom parser's golden baseline can be re-derived by cross-referencing Ghidra's understanding of the reference parser.
- `ipc-maps/qagame_MOD_enum.seed.txt` and `ipc-maps/qagame_EV_enum.seed.txt` feed FT-5 (nickname dictionary + notable-player regex) and the highlight-criteria v2 weapon weights in `docs/specs/highlight-criteria-v2.md`.

---

## 9. Endgame — does `tools/quake-source/` disappear?

**Yes, completely.** After step 9:

- `tools/quake-source/` directory **does not exist**.
- `ls tools/` shows: `README.md, TOOLS.md, blur/, comfy-pilot/, comfyui/, davinci/, download_tools.py, game-assets/, ghidra/, index_rules_to_qdrant.py, md3viewer/, query_rules.py, uberdemotools/ (NEW), vendored-src/, virtualdub2/, wolfcamql/`.
- `tools/` holds only binaries/tooling, never source trees.
- Every reference in CLAUDE.md, HUMAN-QUESTIONS.md, docs/INDEX.md, reference docs, research docs, session docs, and the two `_manifest/*.py` scripts points at `engine/engines/...`.

**Final state verification script:**
```bash
# after migration, these must ALL return clean:
test ! -d tools/quake-source                                      # 1. directory gone
git ls-files | grep -E "^tools/quake-source/" | wc -l            # 2. zero tracked files
grep -rI "tools/quake-source" . --exclude-dir=.git \
     --exclude-dir=.claude/worktrees | wc -l                      # 3. zero text refs
pytest tests/ creative_suite/tests/ phase1/tests/                 # 4. 133 green
pyright creative_suite phase1 phase35 tools scripts              # 5. ≤176 errors
ls engine/engines/_forks/q3mme/trunk/code/cgame/        # 6. q3mme live fork present
ls engine/engines/wolfcam-knowledge/patches/*.patch | wc -l  # 7. ≥7 patches
ls engine/engines/ghidra/                                # 8. ghidra moved under engines
```

All 8 must pass before merging to main.

---

## 10. TL;DR

1. **One folder:** `engine/engines/` becomes the single unified home for all engine source, dissection docs, binary RE, patches, and knowledge. `tools/quake-source/` disappears entirely.
2. **Already 70% done:** `_canonical/` + `_diffs/` + `_docs/` + `_manifest/` from the 2026-04-17 work are the unification target; we're closing out a plan that was approved then paused.
3. **Wolfcam disappears, knowledge survives:** 146 MB of wolfcamql-{src,local-src} source → ~200 KB of patches in `engines/wolfcam-knowledge/patches/` + 7 curated `.md` docs + authoritative files already in `_canonical/`.
4. **Ghidra moves under engines/:** `engine/ghidra/` → `engine/engines/ghidra/` with a binary-to-source map linking decompilation to source+patch truth.
5. **q3mme stays live:** promoted to `engines/_forks/q3mme/` so the engine-fork worktree keeps its writable fork base for Phase 3.5 Track A (proto-73 port, Gate ENG-1 Path A approved).
6. **Zero consumer code affected:** no Python/CMakeLists/config in `creative_suite/`, `phase1/`, `phase35/`, `tests/`, or `pyproject.toml` references `tools/quake-source/`. Only the three `_manifest/*.py` scripts + 23 doc/spec/CLAUDE files rewrite paths.
7. **pytest 133/133 preserved, pyright 176 preserved** at every intermediate commit — migration is pure move+rewrite, zero logic change.
8. **Net disk reduction ~1.1 GB:** uberdemotools test corpora + wolfcamql duplication drop out; prebuilt `UDT_json.exe` promoted to slim `tools/uberdemotools/`.
9. **GPL-2.0 preserved:** every patch in `wolfcam-knowledge/patches/` carries the original copyright + GPL block (FT-1 spirit rule).
10. **One PR, feature branch, user-approved merge:** `feature/engine-folder-unification-2026-04-19` → `main`, 14 atomic commits, final verification checklist blocks merge until all 8 checks pass.

---

*End of plan. Status: READY FOR USER REVIEW. No files moved. No commits made. Awaits approval before step 0 pre-flight runs.*
