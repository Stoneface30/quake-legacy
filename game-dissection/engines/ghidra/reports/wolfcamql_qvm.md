# Wolfcam QVM DLLs — analysis plan

**Binaries covered:**
- `wolfcamql-11.3_cgamex86.dll` (6.3 MB) — client game module
- `wolfcamql-11.3_qagamex86.dll` (2.2 MB) — server game module
- `wolfcamql-11.3_uix86.dll` (1.2 MB) — menu / UI module

**Status:** PLAN. Calibration target is `qagamex86.dll` (smallest wolfcam artifact).

---

## The QVM ABI question

The Q3 engine supports game modules in two forms:
- **QVM bytecode** (`.qvm`) — interpreted / JIT'd by the engine
- **Native DLL** (`.dll` / `.so` / `.dylib`) — direct C ABI

These three DLLs being on disk means wolfcam ships **native-DLL mode**. Each DLL exports:
- `dllEntry(syscallptr)` — engine passes the engine-side syscall function pointer
- `vmMain(command, arg0..argN)` — engine calls this to dispatch every game-logic event

We need to confirm those exports exist and map the `command` enum to its handlers.

**`pe_probe.py` on qagamex86.dll confirms `.edata` section** (`vaddr=0x004b9000 vsize=0x853f`) → DLL has an export table. The two exports above should be visible.

---

## What we want to learn

1. `vmMain` command enum — the full list of events cgame / qagame / ui receive.
2. `dllEntry` syscall table — the engine-side functions each DLL can call (trap_Cvar_Get, trap_Cmd_Args, trap_Print, etc.).
3. Wolfcam-specific functions visible in the exported symbols / DWARF that don't exist in the vanilla q3 cgame source. These are the patch sites.
4. Whether `trap_R_AddPolyToScene`, `trap_CIN_PlayCinematic` and other video-related traps have wolfcam-specific arg layouts vs vanilla.

---

## Symbol expectations

Like wolfcamql.exe, these DLLs are MinGW-gcc builds with DWARF in numbered slash-sections (`/4`, `/19`, `/31` etc in qagamex86.dll per `symbols/wolfcamql-11.3_qagamex86.dll.probe.txt`). DWARF auto-analysis will give function names + source files.

The `debug_dir` rva=0 in all three — no Microsoft PDB references. That's fine; DWARF is what we want here.

---

## Cross-references to check

- `g_main.c` / `cg_main.c` / `ui_main.c` — source file strings will be visible in `.rdata`; grep for them to confirm.
- `trap_*` calls — each one is a thin wrapper that pushes the syscall-id and calls the engine-provided function pointer. Hundreds of them. DWARF should name every one.
- Wolfcam-specific sources visible in the binary: the checkout has `wolfcam_consolecmds.c`, `wolfcam_main.c`, `wolfcam_ents.c`, `wolfcam_event.c`, `wolfcam_info.c`, `wolfcam_playerstate.c`, `wolfcam_predict.c`. Expect strings like `code/cgame/wolfcam_*.c` in the cgamex86.dll .rdata. Each source file = one patch surface.

---

## Ghidra analysis flags (per DLL)

Same flags as wolfcamql.exe:
- ENABLE DWARF + DWARF Line Number + Decompiler Parameter ID + Stack
- DISABLE FidDB first pass (re-enable after DWARF pass)
- 32-bit x86 PE, image base from probe output (qagame = 0x6d8c0000)

---

## Output artifacts

Per DLL:
- Section in this report: exports list, wolfcam-specific function list, DWARF source-file inventory.
- `ipc-maps/qvm_syscall_table.md` (consolidated): `trap_*` id → C signature → source file. Cross-checked between all 3 DLLs for consistency.

---

## Calibration checklist — do this on qagamex86.dll first

Minimum bar before moving to cgamex86.dll:

- [ ] Binary imports OK in Ghidra (no load errors).
- [ ] DWARF auto-analysis completes; function list shows >50 named functions (not `FUN_0040xxxx`).
- [ ] At least one `wolfcam_*.c` source file appears in the function-name attribution.
- [ ] `vmMain` export is named and decompiles to a switch-on-first-arg.
- [ ] `dllEntry` export is named and stores the passed callback to a global.

If any of those checkboxes fails → fix the workflow before investing in the 10 MB wolfcamql.exe analysis. That's the whole point of starting here.
