# wolfcamql.exe — analysis plan

**Binaries covered:** `wolfcamql-11.3.exe` (primary), `wolfcamql-11.1.exe` (diff reference).
**Status:** PLAN. No Ghidra run yet — Ghidra not installed.
**Why it's the main event:** this is the shipping engine binary. Everything we need for (a) max-quality capture config, (b) protocol-73 patches, (c) wolfcam IPC surface is inside here.

---

## What we want to learn (ranked)

1. **Full `cl_avi*` / `mme_*` / `r_mme*` cvar list** with types, defaults, min/max. Feeds `phase1/render_part_v6.py` max-quality preset per `CLAUDE.md` spec §4.4.
2. **Protocol-73 demo loader** — where does wolfcam branch off from vanilla q3's demo parser to handle QL's `.dm_73`? Seed hit: string `^5demo parse protocol %d` at some data address, referenced by one function — that function is the dispatcher. Also: `demo_protocols` array contents.
3. **Wolfcam IPC surface** — is there a socket listen? Named pipe? Stdin thread? Seed greps: `CreateNamedPipe`, `socket`, `recv`, `ReadFile` over `GetStdHandle`. Also check for `connect`/`bind` via the imports of `ws2_32.dll` (if imported).
4. **`Cmd_AddCommand` call sites** — full console-command surface. Wolfcam-specific commands (`seekclock`, `video`, `stopvideo`, `writeconfig`, etc.) and their handler functions.
5. **`S_StartCapture` / `S_StopCapture` graph** — audio path for capture mode. Strings already confirm both `S_AL_*Capture` (OpenAL path) and `S_Base_*Capture` (dma path) exist.
6. **Camera file format** — `loadCamera`, `startCamera`, `stopCamera`, `idCameraDef` class. Is this a full q3mme merge? This pays off big for Tr4sH Quake engine (cinematic camera paths without running the game).

---

## Symbol expectations — GOOD NEWS

`pe_probe.py` confirms the binary is **NOT stripped**:

```
.stab        vaddr=0x03417000 vsize=0x79a4        <- STABS debug names
.stabstr     vaddr=0x0341f000 vsize=0x29e4f       <- 171 KB of string table for STABS
/4           vaddr=0x03449000 vsize=0x2718
/19          vaddr=0x0344c000 vsize=0x1cc9
/35          vaddr=0x0344e000 vsize=0x398f7d      <- 3.8 MB <- DWARF .debug_info
/47          vaddr=0x037e7000 vsize=0x37f08
```

The numbered slash-sections are MinGW-gcc's way of storing DWARF past the 8-char section-name limit of PE/COFF. **Ghidra's built-in DWARF analyser handles this** — enable "DWARF" and "DWARF Line Number" in auto-analysis. Expect full function names, local variable names, source-file attribution.

Source-file strings already confirmed visible in `.rdata`:
- `code/qcommon/msg.c`
- `code/qcommon/huffman.c`
- `tr_mme.c`, `tr_mme.h`
- `cl_avi.c`, `cl_avi.h`

So function → source-file mapping will be clean.

---

## Starter Ghidra analysis flags

- Import as: 32-bit x86 PE, image base 0x400000.
- Auto-analysis options:
  - **ENABLE**: Decompiler Parameter ID, DWARF, DWARF Line Number, Stack, Reference, Non-Returning Functions, Data Reference, Embedded Media.
  - **DISABLE (first pass)**: FidDB — MinGW/gcc builds often have false positives against MSVC sigs; re-enable after DWARF pass.
  - **DISABLE**: Shared Return Calls (until after first decompile pass — it can hide useful tail calls).
- After first auto-analysis: run `scripts/name_by_strings.py` (to be written) — walks the string table and, for every xref'd string of form `^cvarname`, names the adjacent `Cvar_Get` call site.

---

## Cross-reference targets (strings to pivot on)

Copied from `symbols/wolfcamql-11.3.exe.probe.txt` + focused greps:

| String | What it locates |
|---|---|
| `^5demo parse protocol %d` | protocol-73 dispatch path (primary entry) |
| `^3unknown protocol %d, trying dm %d` | fallback handler — shows what wolfcam does for non-73 demos |
| `real gamestate protocol %d` | gamestate parser — important for protocol-version negotiation |
| `WP_MAX_NUM_WEAPONS_ALL_PROTOCOLS` | array-bounds constant — where wolfcam accommodates QL's extra weapons |
| `cl_aviCodec` / `cl_aviFrameRate` / `cl_aviExtension` | all `cl_avi*` cvars (17 strings confirmed) |
| `mme_blurFrames` / `mme_blurOverlap` / `mme_depthFocus` | q3mme merge surface |
| `videos/%s-%010d.tga`, `videos/%s-depth-%010d.tga` | frame-dump path — confirms TGA stereo+depth capture is built in |
| `^3Error: per-frame huffman tables are not supported by huffyuv` | AVI codec selection path |
| `Unsupported protocol: %s` | error path in connect logic |
| `loadCamera`, `startCamera`, `stopCamera`, `idCameraDef` | q3mme camera file path |
| `sv_pure` / `WARNING: sv_pure set but no PK3 files loaded` | asset-loading path — relevant to style-pack testing (ENG-3) |
| `seekclock` | (to be confirmed — search the strings table once in Ghidra) |

---

## IPC investigation plan

Static checks, in order:

1. Inspect import table: is `ws2_32.dll` imported? → network IPC candidate. Is `CreateNamedPipeA/W` imported from `kernel32`? → named-pipe candidate. `_pipe` from `msvcrt`? → anonymous pipe.
2. If none of the above: IPC is either file-watcher (look for `FindFirstChangeNotification`) or stdin-thread (look for `GetStdHandle` + `ReadFile` in a thread-proc).
3. Cross-reference `Cmd_AddCommand` calls: if wolfcam registers a command that takes filesystem paths (e.g. `exec gamestart.cfg` per CLAUDE.md's automation pattern), that IS the IPC — it's "write cfg file, wolfcam runs it on launch."

**GUESS**: Based on the CLAUDE.md "WolfcamQL Automation Pattern" snippet (write `gamestart.cfg`, launch with `+exec cap.cfg +demo ...`), the IPC is one-shot: wolfcam reads its config at startup, there is no live IPC. To CONFIRM: look for `CreateNamedPipe` / `ws2_32` imports. If absent → one-shot config IPC is the only channel.

---

## Output artifacts this report will produce (once Ghidra runs)

- `ipc-maps/wolfcam_capture_cvars.md` — canonical cvar table (name, type, default, flags, min/max, source file) for every `cl_avi*`, `mme_*`, `r_mme*` cvar. Feeds `phase1/config.py`.
- `ipc-maps/wolfcam_protocol73.md` — protocol dispatch table, `demo_protocols[]` contents, list of patch sites in `msg.c` vs vanilla q3.
- `ipc-maps/wolfcam_console_cmds.md` — every `Cmd_AddCommand` site: command string → handler function name → source file.
- `ipc-maps/wolfcam_audio_capture.md` — `S_StartCapture` → `S_AL_StartCapture` / `S_Base_StartCapture` graph with buffer-size constants.
- Append to `reports/wolfcamql.md` (this file): §Findings (facts), §Patch-Sites (wolfcam-specific fns not in q3), §Guesses.

---

## Sequencing note

Do **not** start here. Calibrate on `qagamex86.dll` (starter report) first — it confirms DWARF extraction works and teaches us the QVM ABI in a 2 MB binary before tackling the 11 MB one.
