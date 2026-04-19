# Cross-binary analysis roadmap

This file is the plan. Executable work lives in per-binary reports; this file
coordinates the ORDER and the HANDOFFS between them.

---

## Strategic question this track answers

From `CLAUDE.md`:
> Endgame: port wolfcamql's protocol-73 patches into q3mme (Phase 3.5 research track), then retire wolfcam entirely.

To port wolfcam's patches into q3mme we need to know **exactly what wolfcam patches, at what call sites, in what order**. The vanilla-Q3 source we have is the BEFORE; the wolfcam source checkout (`tools/quake-source/wolfcamql-src/`) is the ALLEGED AFTER. Ghidra on the shipped `wolfcamql.exe` is the ORACLE — it tells us whether the source checkout drifted from the shipped binary, and where any build-time deltas live.

Secondary question: **what is the max-quality wolfcam capture cvar set?** This feeds `phase1/render_part_v6.py` spec §4.4.

Tertiary question: **what IPC surface does wolfcam expose?** (stdin commands? named pipe? socket? file watcher?) This feeds `creative_suite/engine/supervisor.py` (Task D4) — the Cinema Suite supervisor has to talk to whatever engine ships.

---

## Dependency graph — analyze in this order

```
  (0)  Ghidra install + JDK 21                        <- BLOCKER for everything below
   │
   ▼
  (1)  wolfcamql-11.3_SDL.dll                         <- calibration run, known public API
   │     goal: verify DWARF extractor + FidDB match on SDL1 symbols
   │     output: confidence that our Ghidra flow is sound
   │
   ▼
  (2)  wolfcamql-11.3_qagamex86.dll                   <- starter QVM DLL (2.1 MB, smallest wolfcam artifact)
   │     goal: nail the QVM ABI — entry point syscall table, vmMain dispatcher
   │     output: reports/wolfcamql_qvm.md
   │
   ▼
  (3)  wolfcamql-11.3_cgamex86.dll                    <- cgame (6.3 MB) — client-side rendering hooks
   │     goal: confirm MME patches in cgame (camera paths, free-cam state)
   │     output: reports/wolfcamql_qvm.md (merged section)
   │
   ▼
  (4)  wolfcamql-11.3_uix86.dll                       <- UI module (1.1 MB) — menu system
   │     goal: verify menu-system hooks for wolfcam's in-game recorder UI
   │     output: reports/wolfcamql_qvm.md (merged section)
   │
   ▼
  (5)  wolfcamql-11.3.exe                             <- MAIN EVENT (10.8 MB, has .stab + DWARF!)
   │     focus 1: demo_protocols[] + protocol-73 dispatcher        -> ipc-maps/wolfcam_protocol73.md
   │     focus 2: cl_avi* + mme_* cvar registration                -> ipc-maps/wolfcam_capture_cvars.md
   │     focus 3: S_StartCapture / S_StopCapture                   -> ipc-maps/wolfcam_audio_capture.md
   │     focus 4: Cmd_AddCommand surface (seekclock, video, quit)  -> ipc-maps/wolfcam_console_cmds.md
   │     output: reports/wolfcamql.md (primary)
   │
   ▼
  (6)  wolfcamql-11.1.exe                             <- DIFF target (prior release)
   │     goal: BinDiff 11.1 vs 11.3 to spot any security/parser changes
   │     output: reports/wolfcamql_diff_11_1_vs_11_3.md
   │
   ▼
  (7)  wolfcamql-11.3_backtrace.dll                   <- crash handler (6.2 MB, likely boring)
   │     goal: verify it's just libbacktrace bundled — not a wolfcam patch surface
   │     output: reports/wolfcamql_backtrace.md (short)
   │
   ▼
  (8)  WolfWhisperer.exe (when recovered)             <- IPC commander (supposed anchor binary)
        goal: extract its command surface into wolfcam
        output: reports/wolfwhisperer.md
```

---

## Shared data structures we expect to find in ALL wolfcam binaries

These are the q3/QL structs hardcoded by the engine; they are the "spine" that the QVM DLLs and the main exe must agree on. Finding them in each binary independently is a cross-check.

| Struct | Where first defined | Why it matters |
|---|---|---|
| `msg_t` (bitstream reader/writer) | `code/qcommon/msg.c` (string literal found in wolfcamql.exe) | Core of the demo parser — the whole protocol-73 patch lives here |
| `huffman_t` + `generate_bits_table` | `code/qcommon/huffman.c` (string found) | Demo compression; wolfcam may have table tweaks |
| `playerState_t` | qcommon | Shape differs per protocol; protocol-73 adds QL fields |
| `entityState_t` | qcommon | Same as above |
| `vmCvar_t` | QVM ABI | Cvar sharing between exe and QVM DLLs |
| `gameImport_t` / `gameExport_t` | QVM ABI | qagame syscall table — confirms QVM is DLL-native not .qvm |
| `usercmd_t` | qcommon | Input replay — wolfcam's free-cam patches touch this |
| `cinematic_t` / idCameraDef | q3mme merge | Camera path .camera file format (relevant to our engine fork!) |
| `videoFrameCommand_t` | q3mme merge (confirmed in strings) | Frame-dump queue structure for AVI output |

Binary-independent tests:
- `msg_t` size and field layout should match across all 3 QVM DLLs and the main exe.
- `demo_protocols[]` array (seen as string in exe) should be a compile-time constant — find its address + dump contents.
- `cl_aviCodec` cvar default string should match between exe and what q3mme source claims.

---

## Time budget

| Binary | Estimated analyst-hours (GUI + notes) |
|---|---:|
| (1) SDL.dll calibration | 1 |
| (2) qagamex86.dll | 3 |
| (3) cgamex86.dll | 6 |
| (4) uix86.dll | 2 |
| (5) wolfcamql.exe | 16 (2 focused days) |
| (6) wolfcamql 11.1 diff | 4 |
| (7) backtrace.dll | 1 |
| (8) WolfWhisperer.exe | 4 (pending recovery) |
| **Total** | **~37 hours** |

This fits the "side quest, not critical path" framing the user gave. Split 1 (Parts 4–12 renders) stays primary. This work can be parallelized on a secondary chat.

---

## Handoff matrix — where each finding lands

| Finding | Destination file | Who consumes it |
|---|---|---|
| Canonical `cl_avi*` cvar list with defaults + types | `ipc-maps/wolfcam_capture_cvars.md` + `phase1/config.py` | `phase1/render_part_v6.py` (max-quality preset) |
| `demo_protocols[]` array contents + dispatcher fn address | `ipc-maps/wolfcam_protocol73.md` | Tr4sH Quake engine fork spec (§3 protocol support) |
| Wolfcam IPC mechanism (stdin / pipe / socket / file-watch) | `reports/wolfcamql.md` §IPC | `creative_suite/engine/supervisor.py` (Task D4) |
| Console cmd table (`Cmd_AddCommand` call sites) | `ipc-maps/wolfcam_console_cmds.md` | `docs/reference/wolfcam-commands.md` (merge in) |
| QVM syscall table (gameExport_t layout) | `reports/wolfcamql_qvm.md` | Engine fork: vanilla q3 ABI compat layer |
| Wolfcam-vs-q3 patch sites (functions present in wolfcam but not in q3 source) | `reports/wolfcamql.md` §Patch-Sites | Port plan (§4 of Tr4sH Quake manifesto) |

---

## Known unknowns — flag as `GUESS` in reports until confirmed

1. Whether wolfcam uses QVM `.qvm` bytecode at all or only native DLLs. (The presence of `cgamex86.dll` etc. suggests native-only, but Ghidra will confirm by checking for `VM_Create` with `.qvm` path strings.)
2. Whether `backtrace.dll` contains any wolfcam-specific code or is just libbacktrace / SDL extra. (6 MB is suspiciously large for pure libbacktrace.)
3. Whether wolfcam's free-cam (`wolfcam_main.c` in source) has binary-level delta vs the source checkout — i.e. whether the shipped binary was built from the source we have, or a drifted fork.
4. Whether `WolfWhisperer.exe` (when found) talks to wolfcam via stdin, named pipe, `postmessage` (HWND), or TCP.
