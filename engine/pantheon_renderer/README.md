# PANTHEON native renderer — the bank

PANTHEON's own executable that turns PANTHEON game truth into Quake frames
with no `wolfcamql.exe` process. What is committed here is everything PANTHEON
wrote, plus the means to reproduce the rest exactly.

| path | what it is | committed |
|---|---|---|
| `host/` | our host: entry point, platform services, GL binding, MD3 actor assembly, shot-script reader | yes |
| `oracle/` | the source-behaviour oracle and `BEHAVIOR_BANK.md` | yes (not `oracle.exe`) |
| `bootstrap_source.sh` | extracts WolfcamQL 11.3 from an archive it verifies against `SOURCE.sha256` | yes |
| `build.sh` | rebuilds `build/pantheon_frame.exe` — 114 translation units, fails loudly | yes |
| `wolfcamql-11.3-src/` | upstream GPL-2.0 source | no — reproducible, hash-pinned |
| `gl_software/bin`, `_pkg`, `out` | Mesa staging and frame dumps (2.3 GB) | no — `PROVENANCE.md` records every package hash |
| `build/` | binaries | no |

## Rebuild

```sh
sh engine/pantheon_renderer/bootstrap_source.sh      # verifies sha256 first
sh engine/pantheon_renderer/build.sh
```

## The bank is verified, not asserted

2026-09-07: `build.sh` compiled 114 units and linked. The rebuilt binary and
the binary the original session left behind were given the same shot script
and produced **pixel-identical** frames (bloodrun, 960x540, sha256 of the
decoded image equal). `BANKED_FROM.sha256` records the hashes of the host and
oracle sources that were copied in, so a later divergence is detectable.

Four symbols had to be added to `pantheon_host_stubs.c` to link
(`CL_VideoRecording`, `Key_KeynameCompletion`, `CON_LogSize`, `CON_LogRead`,
plus `CL_ConsolePrint`, `CL_ShutdownCGame`, `CL_ShutdownUI`,
`CIN_CloseAllVideos`) and the C fallbacks `asm/ftola.c` and
`asm/snapvector.c` are compiled instead of the NASM versions. Those are the
only differences between this build recipe and whatever the original session
ran, and the pixel comparison says they do not change the image.

## Boundaries

The renderer decides nothing about game truth (HL-1). It receives transforms
and identities; it never infers a missing observation and never invents a
projectile path. Software GL (`gl_software/`) is a bring-up tool: hardware GL
on this machine still crashes on `glColor*` — see
`docs/reference/2026-09-07-nvidia-32bit-immediate-mode-blocker/`.
