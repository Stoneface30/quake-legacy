# Ghidra RE State — 2026-04-19

## Executive Summary

FT-4 ("Ghidra every executable") is **blocked on two user actions**: (1) install Ghidra 11.3 + JDK 21, (2) extract `WOLF WHISPERER/Wolf Whisperer.rar`. The sandbox scaffold is **fully committed** on branch `creative-suite-v2-step2` (commit `bdf96d29`, "feat(ghidra): FT-4 sandbox scaffold + preliminary binary inventory") under `engine/ghidra/` with 7 wolfcamql PE binaries staged, PE-probe static analysis run on all of them, and 4 markdown reports + 3 IPC-map seed files written. The current branch `design/phase1-pantheon-system` is missing the scaffold — only the gitignored `binaries/` + `projects/` directories exist. **One unblocking action:** install Ghidra 11.3 + JDK 21 per `engine/ghidra/README.md` §Install; everything downstream is waiting on that.

## Ghidra Install Status

**Installed:** NO.

Verified absent at all expected locations:
- `G:\QUAKE_LEGACY\tools\ghidra\` — directory does not exist
- `C:\ghidra\`, `C:\Program Files\ghidra\`, `C:\Users\Stoneface\ghidra\` — absent per sandbox README
- `$GHIDRA_INSTALL_DIR` — unset
- `ghidraRun.bat` not on PATH

No installer zip, no `.gpr` project files, no `analyzeHeadless.bat` artifacts anywhere on `G:\`.

**Install procedure** is documented in the worktree README (`.claude/worktrees/creative-suite-v2/engine/ghidra/README.md` lines 44–67): install OpenJDK 21, download `ghidra_11.3_PUBLIC_*.zip` from https://github.com/NationalSecurityAgency/ghidra/releases, extract to `G:\QUAKE_LEGACY\tools\ghidra\ghidra_11.3_PUBLIC\`, set `GHIDRA_INSTALL_DIR`, smoke-test `ghidraRun.bat`, then drive analysis via `analyzeHeadless.bat`.

## Wolf Whisperer .rar Blocker

- File: `G:\QUAKE_LEGACY\WOLF WHISPERER\Wolf Whisperer.rar`
- Size: **1.83 GB** (1,834,057,069 bytes), mtime 2019-05-15
- Status: **UNEXTRACTED** — no sibling directory, no extracted `WolfWhisperer.exe` anywhere in the tree
- Impact: the CLAUDE.md-stated anchor binary `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfWhisperer.exe` **does not exist on disk**. That path is stale. The binary is (presumed) inside this rar.

## Target Binaries

Inventory of all `.exe` / DLL RE candidates per FT-4, verified against disk 2026-04-19:

| Binary | Path | Size | Probe done? | Report? | Ghidra project? |
|---|---|---:|---|---|---|
| wolfcamql-11.3.exe | `engine/ghidra/binaries/wolfcamql-11.3.exe` | 10.8 MB | yes | `reports/wolfcamql.md` (plan) | NO |
| wolfcamql-11.1.exe | `engine/ghidra/binaries/wolfcamql-11.1.exe` | 10.8 MB | yes | (diff target) | NO |
| wolfcamql-11.3_cgamex86.dll | same dir | 6.3 MB | yes | `reports/wolfcamql_qvm.md` (plan) | NO |
| wolfcamql-11.3_qagamex86.dll | same dir | 2.2 MB | yes | `reports/qagamex86_preliminary.md` | NO |
| wolfcamql-11.3_uix86.dll | same dir | 1.2 MB | yes | `reports/wolfcamql_qvm.md` (plan) | NO |
| wolfcamql-11.3_SDL.dll | same dir | 324 KB | yes | (calibration) | NO |
| wolfcamql-11.3_backtrace.dll | same dir | 6.2 MB | yes | (deferred) | NO |
| WolfWhisperer.exe | inside `Wolf Whisperer.rar` (1.83 GB) | unknown | NO | NO | NO |
| `tools/wolfcamql/wolfcamql.exe` | **MISSING** (CLAUDE.md ref is stale — dir does not exist) | — | — | — | — |
| `tools/uberdemotools/UDT_json.exe` | **MISSING** (no prebuilt — source-only at `tools/quake-source/uberdemotools/`) | — | — | — | — |
| `q3mme.exe` | **MISSING** (source-only checkout; never built) | — | — | — | — |

Deferred (scope call): ffmpeg.exe (101 MB), ffprobe.exe (202 MB), VirtualDub*.exe, q3asm.exe, lcc.exe — all open-source with available source, marginal RE value.

## Outputs / Reports On Disk

All outputs live in the `creative-suite-v2-step2` branch at `engine/ghidra/`:

**Reports** (`reports/`):
- `_binary-inventory.md` — SHA-256 + provenance for all 7 staged binaries, plus "expected but missing" table
- `_analysis-roadmap.md` — 8-stage dependency graph, ~37 analyst-hour time budget, handoff matrix to phase1/creative_suite/manifesto
- `qagamex86_preliminary.md` — calibration starter: confirmed MinGW-w64 build, DWARF intact (~1.5 MB), 32-bit PE, image base `0x6d8c0000`, compile timestamp 2016-08-13
- `wolfcamql.md` — primary analysis plan (101 lines): cvar pivot strings, protocol-73 dispatcher hypothesis, IPC search strategy
- `wolfcamql_qvm.md` — QVM DLL (cgame/qagame/ui) analysis plan (80 lines)

**IPC seed maps** (`ipc-maps/`, already harvested from strings, pre-Ghidra):
- `qagame_MOD_enum.seed.txt` — **34-entry MOD_* enum** including QL-specific `MOD_HMG`, `MOD_RAILGUN_HEADSHOT`, `MOD_THAW`, `MOD_TARGET_LASER`, `MOD_SWITCH_TEAMS`, `MOD_TRIGGER_HURT` (first binary-level proof of protocol-73 patches)
- `qagame_EV_enum.seed.txt` — **103-entry EV_* enum** (`EV_OBITUARY`, `EV_AWARD`, `EV_DAMAGEPLUM`, `EV_RAILTRAIL`, etc.)
- `wolfcamql-11.3_capture_cvars.seed.txt` — capture-cvar seed (`r_mode`, `com_maxfps`, `video avi`, `seekclock`, ...)

**PE probes** (`symbols/`): 7 files, one per staged binary, produced by `scripts/pe_probe.py` (dep-free PE header + imports + strings extractor).

**Tooling** (`scripts/`): `pe_probe.py` — committed, reusable.

**Source-verified command reference**: `docs/reference/wolfcam-commands.md` is **789 lines** — comprehensive cvar + console-command inventory from `cl_main.c` + `cg_consolecmds.c` source reading. Rule P3-B's main deliverable is effectively done from source; Ghidra cross-check remains pending.

## Protocol 73 Knowledge

From pre-Ghidra static work (string + PE header analysis):

- **CONFIRMED**: `qagamex86.dll` contains the complete QL-extended MOD_* set. Vanilla Q3 does not have `MOD_HMG`, `MOD_THAW`, `MOD_RAILGUN_HEADSHOT`, `MOD_TARGET_LASER`. Their presence in the shipped wolfcam DLL proves the binary carries protocol-73-era game-type extensions.
- **CONFIRMED**: `wolfcamql.exe` is **not stripped** — STABS (171 KB) + DWARF (3.8 MB `.debug_info`) sections intact. Ghidra's DWARF analyser will recover function names, locals, source-file attribution (`code/qcommon/msg.c`, `code/qcommon/huffman.c`, `cl_avi.c`, `tr_mme.c` strings already visible in `.rdata`).
- **GUESS** (pending Ghidra): the `demo_protocols[]` array + protocol-73 dispatcher function sits near the `^5demo parse protocol %d` format string in `.rdata`; the dispatcher is the one-reference function in its xref chain.
- **GUESS**: wolfcam was built from the source checkout at `tools/quake-source/wolfcamql-src/` — timestamps match (Aug 2016), content diff requires Ghidra.

Destination per handoff matrix: `ipc-maps/wolfcam_protocol73.md` (to be written), feeds `docs/superpowers/specs/2026-04-17-tr4sh-quake-manifesto.md` Track A §3 "port wolfcam protocol 73 patches into cg_servercmds.c + msg.c" (manifesto line 185).

## Blockers For User

1. **Install Ghidra 11.3 + OpenJDK 21** at `G:\QUAKE_LEGACY\tools\ghidra\ghidra_11.3_PUBLIC\`. Set `GHIDRA_INSTALL_DIR`. Smoke-test `ghidraRun.bat`. See `engine/ghidra/README.md` §44–67 (on branch `creative-suite-v2-step2`). **Blocker for all 8 analyses on the roadmap.**
2. **Extract `WOLF WHISPERER/Wolf Whisperer.rar`** (1.83 GB). Needs WinRAR or 7-Zip. If it contains `WolfWhisperer.exe`, stage it into the sandbox as binary #8 and update `_binary-inventory.md` with SHA-256 + provenance. If the rar is obsolete, confirm that so the anchor-binary line in CLAUDE.md can be deleted.
3. **Scope call**: is `UDT_json.exe` worth building from source (`tools/quake-source/uberdemotools/`) for RE? Current roadmap substitutes `qagamex86.dll` as the calibration target. Confirm `UDT_json` can be deprioritized.
4. **Branch merge**: the Ghidra scaffold lives on `creative-suite-v2-step2` (commit `bdf96d29`). It is NOT on `main` and NOT on the current working branch `design/phase1-pantheon-system`. Decide whether to merge/rebase the scaffold to a shared base so FT-4 work can proceed independently of the Cinema Suite branch.

## Files of Note

Absolute paths. All Ghidra scaffold files currently live in the `creative-suite-v2` worktree because the scaffold commit is not on the current branch:

- `G:\QUAKE_LEGACY\.claude\worktrees\creative-suite-v2\engine\ghidra\README.md`
- `G:\QUAKE_LEGACY\.claude\worktrees\creative-suite-v2\engine\ghidra\reports\_binary-inventory.md`
- `G:\QUAKE_LEGACY\.claude\worktrees\creative-suite-v2\engine\ghidra\reports\_analysis-roadmap.md`
- `G:\QUAKE_LEGACY\.claude\worktrees\creative-suite-v2\engine\ghidra\reports\qagamex86_preliminary.md`
- `G:\QUAKE_LEGACY\.claude\worktrees\creative-suite-v2\engine\ghidra\reports\wolfcamql.md`
- `G:\QUAKE_LEGACY\.claude\worktrees\creative-suite-v2\engine\ghidra\reports\wolfcamql_qvm.md`
- `G:\QUAKE_LEGACY\.claude\worktrees\creative-suite-v2\engine\ghidra\ipc-maps\qagame_MOD_enum.seed.txt`
- `G:\QUAKE_LEGACY\.claude\worktrees\creative-suite-v2\engine\ghidra\ipc-maps\qagame_EV_enum.seed.txt`
- `G:\QUAKE_LEGACY\.claude\worktrees\creative-suite-v2\engine\ghidra\ipc-maps\wolfcamql-11.3_capture_cvars.seed.txt`
- `G:\QUAKE_LEGACY\.claude\worktrees\creative-suite-v2\engine\ghidra\scripts\pe_probe.py`
- `G:\QUAKE_LEGACY\.claude\worktrees\creative-suite-v2\engine\ghidra\symbols\wolfcamql-11.3.exe.probe.txt` (and 6 siblings)

Binaries (gitignored — present in both branches' `engine/ghidra/binaries/` since that dir is shared outside git):
- `G:\QUAKE_LEGACY\engine\ghidra\binaries\wolfcamql-11.3.exe`
- `G:\QUAKE_LEGACY\engine\ghidra\binaries\wolfcamql-11.1.exe` + 5 DLLs

Blocker artifact:
- `G:\QUAKE_LEGACY\WOLF WHISPERER\Wolf Whisperer.rar` (1.83 GB, 2019-05-15, unextracted)

Cross-link targets (where Ghidra output feeds):
- `G:\QUAKE_LEGACY\docs\superpowers\specs\2026-04-17-tr4sh-quake-manifesto.md` (Track A lines 110–186)
- `G:\QUAKE_LEGACY\docs\reference\wolfcam-commands.md` (789-line source-level reference, awaits Ghidra cross-check)
- `G:\QUAKE_LEGACY\docs\specs\2026-04-18-directing-vocabulary-and-pattern-extraction.md` (line 264: "Research blocker: FT-4 (Ghidra) must surface the exact wolfcam cmd set")
- `G:\QUAKE_LEGACY\creative_suite\engine\supervisor.py` (Task D4 — needs wolfcam IPC surface)
- `G:\QUAKE_LEGACY\phase1\render_part_v6.py` (needs confirmed `cl_avi*`/`mme_*` cvar defaults)
