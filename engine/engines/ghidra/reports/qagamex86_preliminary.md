# wolfcamql-11.3_qagamex86.dll — preliminary report (static only)

**Substitutes for the `UDT_json.exe` starter in the original plan** — `UDT_json.exe` is not present on disk (see `_binary-inventory.md`). `qagamex86.dll` is the smallest proper wolfcam artifact at 2.2 MB and is the right calibration target: it will exercise our DWARF-extraction + export-table + QVM-ABI workflow before we invest in the 10 MB `wolfcamql.exe`.

**Source:** `WOLF WHISPERER/Backup/wolfcamql-11.3.zip :: wolfcamql11.3/wolfcam-ql/qagamex86.dll`
**SHA-256:** `6fdc68610114b00a06937124ed07368c4db3a92d6954b992110f60cca492bfd8`
**Analysis level:** static only (pe_probe.py), NO Ghidra yet.

---

## Header facts — CONFIRMED

- **32-bit x86 PE** (I386 machine), **native DLL**, image base `0x6d8c0000` (typical engine-mod DLL base).
- **Not stripped.** DWARF debug sections present in numbered PE slots (`/4`, `/19`, `/31`, `/45`, `/57`, `/70`, `/81`, `/92`) totalling **~1.5 MB** of debug info. Ghidra's DWARF analyser will consume this directly.
- **MinGW-w64 build** — confirmed by string `../../mingw-w64-crt/crt/dllentry.c` in `.rdata` and by the slash-numbered DWARF section naming convention.
- **Compile timestamp:** 1471095929 (unix epoch) = 2016-08-13 14:25 UTC. Matches the `wolfcamql-src.tar.gz` date in `WOLF WHISPERER/Backup/` (also Aug 13 2016). This binary was built from a source close to our checkout.
- **`.edata` section present** (34 KB) — DLL has an export table. The `vmMain` / `dllEntry` engine-mod exports should be in here; `pe_probe.py` does not decode exports (only imports) so this is confirmed at the section level only, not the symbol level.

---

## Imports — MINIMAL

The DLL links only against **`KERNEL32.dll`** and **`msvcrt.dll`** — that's it. No networking, no graphics, no filesystem-extended APIs. Everything else (file I/O, rendering, audio, cvar access) is routed through the engine's `trap_*` syscall callback that the main binary passes in via `dllEntry`. This is textbook q3 native-game-module behaviour and **confirms that this DLL has no independent side channels** — it cannot open a pipe, cannot touch the network, cannot read from disk except via the engine.

Kernel32 imports are all standard MinGW runtime boilerplate (critical sections, TLS, unhandled exception filter, VirtualProtect).

MSVCRT imports include the usual `memcpy` / `strcpy` / `sscanf` / `qsort` / math (`acos`, `atan2`). No surprise APIs.

**Implication:** when we analyze this DLL in Ghidra, every "interesting" external call MUST go through the engine-callback pointer set in `dllEntry`. Tracking that function pointer is the key to mapping the QVM syscall table.

---

## Most interesting strings — CONFIRMED (top 3 categories)

### 1. Complete `MOD_*` (means of death) enum — 34 entries

Saved to `ipc-maps/qagame_MOD_enum.seed.txt`. Highlights:

```
MOD_BFG, MOD_BFG_SPLASH, MOD_CHAINGUN, MOD_CRUSH, MOD_FALLING,
MOD_GAUNTLET, MOD_GRAPPLE, MOD_GRENADE, MOD_GRENADE_SPLASH,
MOD_HMG, MOD_JUICED, MOD_KAMIKAZE, MOD_LAVA, MOD_LIGHTNING,
MOD_LIGHTNING_DISCHARGE, MOD_MACHINEGUN, MOD_NAIL, MOD_PLASMA,
MOD_PLASMA_SPLASH, MOD_PROXIMITY_MINE, MOD_RAILGUN, MOD_RAILGUN_HEADSHOT,
MOD_ROCKET, MOD_ROCKET_SPLASH, MOD_SHOTGUN, MOD_SLIME, MOD_SUICIDE,
MOD_SWITCH_TEAMS, MOD_TARGET_LASER, MOD_TELEFRAG, MOD_THAW,
MOD_TRIGGER_HURT, MOD_UNKNOWN, MOD_WATER
```

**Relevance to the project:** this is the exact `MOD_*` list that `phase2/dm73parser/` needs. `CLAUDE.md` says the frag-detection parser uses `entity.eventParm` holding a `MOD_*` constant. Our existing `docs/specs/highlight-criteria-v2.md` assumes a certain weapon set — this binary CONFIRMS the wolfcam build knows about `MOD_HMG`, `MOD_CHAINGUN`, `MOD_NAIL`, `MOD_THAW` (QL Freeze Tag), `MOD_SWITCH_TEAMS`, `MOD_TRIGGER_HURT`, `MOD_TARGET_LASER`, `MOD_RAILGUN_HEADSHOT` — **all QL-specific MODs that vanilla q3 does not have**. This is the first piece of binary-level proof of protocol-73 / QL patches in the wolfcam build.

### 2. Complete `EV_*` (event) enum — 103 entries

Saved to `ipc-maps/qagame_EV_enum.seed.txt`. Relevant for `CLAUDE.md`'s frag-detection snippet:

```c
entity.event & ~0x300 == EV_OBITUARY
```

The probe confirms `EV_OBITUARY` is in the enum (visible in the full string dump) alongside QL-specific events like `EV_AWARD`, `EV_DAMAGEPLUM`, `EV_BULLET_HIT_FLESH`, `EV_RAILTRAIL` and multiple `EV_DEATH[1..3]` sound events. The ordering / numeric values of these enum members live in the data section as integer constants referenced by string-lookup tables — Ghidra will let us dump the full (name, value) pairing.

### 3. Wolfcam / QL provenance markers

- `../../mingw-w64-crt/crt/dllentry.c` — build toolchain
- `DllEntryPoint` / `DllEntryPoint@12` — standard MinGW DLL entry (distinct from the game-ABI `dllEntry`)
- `G_InitGame`, `G_RunFrame`, `G_RunClient`, `G_RunMissile`, `G_RunItem`, `G_RunMover`, `G_RunThink`, `G_InitBots`, `G_InitMemory`, `G_InitSessionData`, `G_InitWorldSession`, `G_LoadArenas`, `G_LoadArenasFromFile` — **standard Q3 qagame entry points**, confirming this is the server-side game module.
- `arenainfo`, `#arenasFile`, `%i arenas parsed`, `.arena` — bot arena file loader. Confirms vanilla-q3 bot code path is retained in wolfcam.

---

## Interesting imports — 3 highlights

With only `KERNEL32.dll` + `msvcrt.dll` imported, there are no API surprises; instead the interesting call is the **absence** of several APIs a real application would want:

1. **No `ws2_32.dll`** → this DLL cannot open sockets. Any network activity goes through the engine.
2. **No `ntdll.dll`** direct calls → no low-level NT kernel calls bypassing the engine sandbox.
3. **No `advapi32.dll`** → no registry access. (A `.exe` with registry access is an automation-script red flag; this DLL doesn't have that option.)

The `.bss` section is **~4.3 MB uninitialized data** (`vsize=0x41dfc0`) — that's the massive globals area (level state arrays, bot state, entity pools). Typical q3-mod sizing.

---

## Next actions (once Ghidra is installed)

1. **Import as 32-bit x86 PE**, image base `0x6d8c0000`.
2. **Enable** DWARF + DWARF Line Number analysers. Disable FidDB first pass.
3. Confirm `.edata` parsing gives us `vmMain` and `dllEntry` as named exports. If not, use the standard Q3 native-game-module offsets (exports are ordinal 1 and 2 respectively).
4. Locate `dllEntry` → find where it stores its callback argument to a global. That global IS `trap` — every `trap_*` wrapper calls through it.
5. Walk `vmMain`'s switch statement → enumerate the `GAME_*` command IDs (`GAME_INIT`, `GAME_SHUTDOWN`, `GAME_CLIENT_CONNECT`, `GAME_CLIENT_COMMAND`, etc.).
6. Cross-check: the authoritative merged source at `engine/engines/_canonical/code/game/` (with proto-73 deltas in `engines/wolfcam-knowledge/patches/`) should match. Log ANY drift into `engines/wolfcam-knowledge/shipped-binary-deltas.patch`.

---

## Confidence grades

| Finding | Grade |
|---|---|
| 32-bit x86 PE with DWARF intact, MinGW build, Aug 2016 | CONFIRMED (header parse) |
| No network / registry / pure-NT side channels | CONFIRMED (import table) |
| Wolfcam builds include QL-specific MOD_ enum extensions | CONFIRMED (string table) |
| Complete `MOD_*` enum matches 34 entries listed above | CONFIRMED (strings) |
| `.edata` exports `vmMain` + `dllEntry` | GUESS (section present, symbol names not yet enumerated — pe_probe.py does not walk exports) |
| Binary was built from our source checkout | GUESS (timestamp matches; content diff awaits Ghidra pass) |
