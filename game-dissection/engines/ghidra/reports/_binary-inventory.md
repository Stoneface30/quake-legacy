# Binary inventory — Ghidra FT-4

Generated: 2026-04-19. All hashes SHA-256.

## Binaries copied into the sandbox

Located in `game-dissection/ghidra/binaries/` (gitignored). Provenance is the original ZIP archive + relative path within the archive.

| # | Sandbox name | Size (bytes) | SHA-256 | Provenance (source ZIP + path inside) |
|---|---|---:|---|---|
| 1 | `wolfcamql-11.3.exe` | 10,838,297 | `d88c25470918dcb9de83c5e34f91bc73fe634927b82566f7925857197643a13b` | `WOLF WHISPERER/Backup/wolfcamql-11.3.zip :: wolfcamql11.3/wolfcamql.exe` |
| 2 | `wolfcamql-11.1.exe` | 10,829,430 | `39babd09349f92d1d4cab2bba5bd5459b553c5c21df60920cef0aeec94ca8e97` | `WOLF WHISPERER/Backup/wolfcamql-11.1.zip :: wolfcamql11.1/wolfcamql.exe` |
| 3 | `wolfcamql-11.3_cgamex86.dll` | 6,322,796 | `6d4f1db50e812da961464ab6ac6a16b6932a2e51f385441b4d97dd3bba2025c7` | `WOLF WHISPERER/Backup/wolfcamql-11.3.zip :: wolfcamql11.3/wolfcam-ql/cgamex86.dll` |
| 4 | `wolfcamql-11.3_qagamex86.dll` | 2,170,075 | `6fdc68610114b00a06937124ed07368c4db3a92d6954b992110f60cca492bfd8` | `WOLF WHISPERER/Backup/wolfcamql-11.3.zip :: wolfcamql11.3/wolfcam-ql/qagamex86.dll` |
| 5 | `wolfcamql-11.3_uix86.dll` | 1,160,960 | `3e3d1506cd092de638b179ae7e58f8c3b22b2cc78e8686a7221430b729f858e2` | `WOLF WHISPERER/Backup/wolfcamql-11.3.zip :: wolfcamql11.3/wolfcam-ql/uix86.dll` |
| 6 | `wolfcamql-11.3_SDL.dll` | 324,096 | `bafc1b4216d1ac1cf6168f5c26aa94314f7b03afca1462b3df611c016077ee94` | `WOLF WHISPERER/Backup/wolfcamql-11.3.zip :: wolfcamql11.3/SDL.dll` |
| 7 | `wolfcamql-11.3_backtrace.dll` | 6,206,363 | `2b0f03cdcb1f2f2ad105c29c20ed70d6b9773419bd5bd90614c6fb369757e214` | `WOLF WHISPERER/Backup/wolfcamql-11.3.zip :: wolfcamql11.3/backtrace.dll` |

All 7 are **32-bit Windows PE (x86 / I386)**.

## Binaries the CLAUDE.md inventory expected but DID NOT find on disk

Per `CLAUDE.md` "Key Technical Facts", these were expected — they are NOT present at the given paths:

| Expected path | Status |
|---|---|
| `G:\QUAKE_LEGACY\tools\wolfcamql\wolfcamql.exe` | **Missing** — no `tools/wolfcamql/` directory. Binary lives only inside `WOLF WHISPERER/Backup/wolfcamql-11.{1,3}.zip`. CLAUDE.md reference is stale. |
| `G:\QUAKE_LEGACY\tools\uberdemotools\UDT_json.exe` | **Missing** — `tools/uberdemotools/README.md` is a stub (2026-04-19 unification). Source retired from tree. Build via upstream mightycow/uberdemotools. Reference notes at `engines/variants/uberdemotools/`. |
| `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfWhisperer.exe` | **Missing** — `WOLF WHISPERER/` contains only `Backup/` (zips) + `Wolf Whisperer.rar` (unextracted archive, not yet inventoried) + `WolfcamQL/wolfcam-ql/` (demo corpus). `WolfWhisperer.exe` itself is not present. |
| `q3mme.exe` | **Missing** — `engines/_forks/q3mme/` (moved 2026-04-19) is source-only (git checkout). No built binary anywhere in the tree. Only `q3asm.exe` (build tool) was found. |

**Action item for human:** extract `Wolf Whisperer.rar` (or confirm it's obsolete) and re-stage any binaries therein. If that rar contains `WolfWhisperer.exe`, add it to the sandbox as binary #8.

## Binaries DEFERRED (in scope per FT-4 but low priority)

| Binary | Reason to defer |
|---|---|
| `tools/ffmpeg/ffmpeg.exe` (101 MB) | Fully open source (static FFmpeg build). Nothing novel to learn from disassembly vs reading the public FFmpeg source. |
| `tools/ffmpeg/ffprobe.exe` (202 MB) | Same as ffmpeg.exe. |
| `tools/virtualdub2/VirtualDub.exe` (4 MB) + `VirtualDub64.exe` (5 MB) | Open source (GPL). Source is available; disassembly adds no new knowledge. |
| `tools/virtualdub2/vdub.exe` / `vdub64.exe` | Launcher stubs. |
| `engines/variants/quake3-source/lcc/bin/*.exe` (retired — source gone, see _canonical/) | Q3 build tools (LCC compiler). |
| `engines/_forks/q3mme/trunk/code/tools/asm/q3asm.exe` | Build tool. Source is right next to it. |

If FT-4 is ever expanded to cover these, add them to this inventory with SHA-256 + provenance at that time.
