# Ghidra Sandbox — FT-4 Reverse-Engineering Track

**Status:** prepared (2026-04-19). No live Ghidra sessions yet — Ghidra is not installed on this machine.
**Scope:** funded track FT-4 from `CLAUDE.md` — "Ghidra every executable".
**Strategic goal:** the endgame of the engine split in `CLAUDE.md` — port wolfcam's protocol-73 (QL `.dm_73`) patches into q3mme, then retire wolfcam. This sandbox is where we confirm, at the binary level, what those patches ARE.

---

## Directory layout

```
game-dissection/ghidra/
├── README.md                  <- you are here
├── projects/                  <- Ghidra .gpr project files (GITIGNORED — huge)
├── binaries/                  <- COPIES of analysed .exe/.dll (GITIGNORED — id Software IP)
├── scripts/                   <- Ghidra + helper scripts (committed)
│   └── pe_probe.py            <- dep-free PE header + imports + strings extractor
├── reports/                   <- per-binary markdown reports (committed)
│   ├── _binary-inventory.md   <- every analysed binary with sha256 + provenance
│   ├── _analysis-roadmap.md   <- cross-binary plan + time budget
│   ├── wolfcamql.md           <- wolfcamql.exe analysis plan
│   ├── wolfcamql_qvm.md       <- cgame / qagame / ui QVM DLLs analysis plan
│   ├── qagamex86_preliminary.md  <- first starter report (calibration run)
│   └── (others as binaries are tackled)
├── ipc-maps/                  <- extracted command / cvar tables (committed)
│   └── wolfcamql-11.3_capture_cvars.seed.txt
├── symbols/                   <- FidDB signatures, BSim exports, raw probe dumps (committed)
└── _staging_extract/          <- unzipped archive contents (GITIGNORED)
```

---

## Rules (HARD, copied from CLAUDE.md)

1. **ENG-4**: Steam pak files are READ-ONLY. Never modify. This sandbox imports *copies* from `WOLF WHISPERER/Backup/*.zip` or `tools/…/*.exe`. Nothing under Steam install dirs is touched.
2. **No dynamic execution** — static analysis only. No running wolfcamql.exe or q3mme from Ghidra. No debug-attach. No instrumentation.
3. **No redistribution** — binaries inside `binaries/` are id Software IP (QL / Q3A derivatives). They are referenced here for analysis only and are gitignored. Reports + extracted cvar tables + function signatures are original work and ARE committed.
4. **Ghidra must be a named-project per binary**, not one giant project. Each `projects/<binary>/` gets its own Ghidra project + analysis checkpoint file.
5. **All findings land in a markdown report** in `reports/`. No findings living only inside a `.gpr` file — if it matters, write it down.
6. **Guesses are tagged `GUESS`** in reports. Confirmed facts (matched to strings, confirmed in source, or cross-referenced with call graph) are tagged `CONFIRMED`.

---

## Ghidra installation status

**Installed:** NO.

Not present at any of:
- `C:\ghidra\`
- `C:\Program Files\ghidra\`
- `C:\Users\Stoneface\ghidra\`
- `G:\QUAKE_LEGACY\tools\ghidra\`
- `$GHIDRA_INSTALL_DIR` (unset)
- `where ghidraRun.bat` → not found

### Install steps (DO NOT run without user approval)

Recommended: **Ghidra 11.3** (latest stable as of the cutoff of this plan) with **OpenJDK 21**.

1. Install OpenJDK 21 (Temurin or similar). Confirm with `java --version` (must be ≥ 21).
2. Download `ghidra_11.3_PUBLIC_*.zip` from the official NSA GitHub releases: https://github.com/NationalSecurityAgency/ghidra/releases
3. Verify the SHA-256 published on that release page matches the downloaded ZIP.
4. Extract to `G:\QUAKE_LEGACY\tools\ghidra\ghidra_11.3_PUBLIC\` (project-local, stays off user profile).
5. Set `GHIDRA_INSTALL_DIR` env var to that path and add `tools\ghidra\ghidra_11.3_PUBLIC\support` to PATH (for `analyzeHeadless.bat`).
6. Smoke test: `ghidraRun.bat` → should launch the GUI once. Close it. Then `analyzeHeadless.bat <project_dir> <project_name> -import <binary>` runs analysis without the GUI — that's how this sandbox will be scripted.
7. Optional: install the **GhidraDev** Eclipse plugin only if we plan to write Java scripts. For our Python scripts, the built-in Jython 2.7 is enough.

---

## Quick workflow (per binary, once Ghidra is installed)

1. Copy the binary into `binaries/` with a tier-tagged name (e.g. `wolfcamql-11.3.exe`).
2. Record SHA-256 + provenance in `reports/_binary-inventory.md`.
3. Run `scripts/pe_probe.py <binary>` → save output under `symbols/<binary>.probe.txt`.
4. Open Ghidra, create project under `projects/<binary>/`, import binary, run auto-analysis.
   - For wolfcamql.exe: ENABLE "DWARF Line Number", "DWARF" analyser (binary has `.stab` + `/4` `/19` `/35` `/47` DWARF sections — NOT stripped).
   - For QVM DLLs (cgamex86.dll etc): also ENABLE DWARF.
5. Cross-reference strings (from probe output) to call sites inside Ghidra.
6. Write findings to `reports/<binary>.md` as you go.
7. Export cvar tables, command handlers, function sigs to `ipc-maps/`.
8. Commit only `reports/`, `scripts/`, `ipc-maps/`, `symbols/`, `README.md`. Never commit `projects/` or `binaries/`.

---

## Liaison — how Ghidra outputs feed the rest of the project

This sandbox is NOT standalone. Its outputs flow into three in-flight workstreams:

| Consumer | What it needs from here |
|---|---|
| **`phase1/render_part_v6.py`** — max-quality render config | Confirmed cvar list + defaults + value ranges for `cl_avi*`, `mme_*`, `r_mme*`. Feeds `docs/superpowers/specs/phase1-render-config.md` §4.4. |
| **`creative_suite/engine/supervisor.py`** (Task D4, Cinema Suite) | Wolfcam IPC entry points — is it stdin-only? Named pipe? `ipcWrite`/`ipcRead` symbols? The supervisor needs to know how to talk to whichever engine ships. |
| **`docs/superpowers/specs/2026-04-17-tr4sh-quake-manifesto.md`** (Track 2 engine fork) | Binary-level proof of where wolfcam patches q3mme / vanilla q3 — guides the port plan. Especially: protocol-73 demo loader diff vs q3mme. |

A **parallel Claude Designer chat** may be open alongside this one. The Designer chat is the consumer; this sandbox is the producer. Any reader of this README who is coming from the Designer side: the authoritative data is in `reports/` + `ipc-maps/`, not in the Ghidra project files.

---

## Next concrete actions (for a human opening Ghidra GUI)

See `reports/_analysis-roadmap.md` for the full plan. Top three:

1. **Install Ghidra 11.3 + JDK 21** (see steps above). Blocker for everything below.
2. **Calibrate on `wolfcamql-11.3_qagamex86.dll`** (smallest proper wolfcam artifact: 2.1 MB) — run auto-analysis, confirm DWARF extraction works, write up the QVM ABI.
3. **Analyse `wolfcamql-11.3.exe`** with DWARF on — this is THE binary. Focus order: (a) `demo_protocols` array + protocol-73 dispatcher, (b) `cl_avi*` + `mme_*` cvar registration, (c) `S_StartCapture` / `S_StopCapture` audio path.
