# 00 — Wolfcamql Knowledge Ingest: Overview

> **Purpose of this directory.** Wolfcamql is being retired from QUAKE LEGACY in favor
> of a single Tr4sH Quake engine fork (q3mme-derived, see `docs/superpowers/specs/2026-04-17-tr4sh-quake-manifesto.md`).
> Before its source tree is removed from `tools/quake-source/`, every fact we still
> need from it lives here.
>
> **Bar set by L94:** *"if we leave wolfcam we will need to cleanup our repo from it
> meaning we need to extract all the knowledge from it and ingest it in our dissector."*
> If a Tr4sH Quake engineer can read this directory and not need the wolfcamql
> source, the extraction succeeded.

## Project identity

| Field | Value |
|---|---|
| Name | WolfcamQL |
| Upstream repo | https://github.com/brugal/wolfcamql |
| Local mirror | `tools/quake-source/wolfcamql-src/` (origin = brugal/wolfcamql, master) |
| Local secondary | `tools/quake-source/wolfcamql-local-src/wolfcamql-src/` (mirror, possibly an older snapshot) |
| Maintainer | brugal (primary) — see `CREDITS-wolfcam.txt` |
| Notable contributors | em92 (Eugene Molotov) — many bugfixes; Cyrax (screenMap shader); agkr234 (timescale stutter fix) |
| License | GPL-2.0 (`COPYING.txt`) — id Software Quake 3 source under GPL, wolfcamql additions inherit |
| Lineage | id Quake 3 → ioquake3 → wolfcamql; pulls camera/blur/DoF from q3mme |

## Purpose

WolfcamQL is a `.dm_73` (QuakeLive demo) replay engine + fragmovie capture tool.
From its README:

> WolfcamQL is a quakelive/quake3 demo player with some hopefully helpful options for
> demo viewing and movie making:
> - demo pause/rewind/fast forward
> - demo viewing without needing an internet connection
> - viewing demos from other player's point of view or in freecam mode
> - compatibility with all the client features that have been added to quakelive on top of the original quake3
> - backwards compatibility with older quake live demos
> - adjust player and projectile positions to match more closely what occurred on the
>   demo taker's screen (demo treated as what the 'client saw' not what the 'server
>   saw' and will also compensate for demo taker's ping)
> - camera system
> - q3mme style scripting to customize graphics and effects
> - raise/remove limits for video rendering and also options like motion blur

The two pieces that make wolfcamql irreplaceable as a stepping stone:
1. **Protocol 73 support** — stock Quake 3 / ioquake3 speak protocol 68 and cannot
   parse `.dm_73` snapshots. Wolfcamql ships the patched `msg.c` / struct definitions
   that decode them. (See [02-protocol-73-patches.md](02-protocol-73-patches.md).)
2. **Client-side perspective correction** — wolfcamql treats the demo as *what the
   client saw* (with ping compensation), not *what the server saw* — closer to what
   actually appeared on the original demo-taker's screen. This is non-trivial logic
   that lives in `wolfcam_predict.c` / `wolfcam_snapshot.c`.

## Why wolfcamql vs alternatives

| Engine | Plays `.dm_73`? | Fragmovie capture | Camera system | Verdict for our use |
|---|---|---|---|---|
| **WolfcamQL** | **Yes** (only one in our toolchain) | Yes (HuffYUV/AVI, q3mme-derived camera) | Yes (q3mme-style) | Currently our only path to render `.dm_73`. |
| q3mme | No (protocol 68 only) | Yes (excellent) | Yes (canonical implementation) | Better fragmovie tool, can't read our demos. |
| ioquake3 | No (protocol 68) | Limited | No camera system | Baseline only. |
| quake3e | No (protocol 68) | Limited | No | Modern engine, irrelevant for our demos. |
| UberDemoTools (`UDT_json.exe`) | Yes (parser only) | No (no renderer) | No | Reference implementation we validate FT-1 against. |

## Endgame: why we are retiring it

Wolfcamql's protocol-73 patches are valuable but the surrounding engine is dated
(SDL1.2 fallback, jpeg-6b, pthread-win32, custom freetype build). Tr4sH Quake's
plan is to lift just the protocol-73 deltas into q3mme and let q3mme drive
everything else (capture, camera, asset pipeline). See
[06-protocol-73-port-plan.md](06-protocol-73-port-plan.md).

## Document index

| File | Coverage |
|---|---|
| `00-overview.md` | This file — project identity, lineage, retirement rationale |
| `01-commands-cvars.md` | Every `Cmd_AddCommand` and cvar registration, sourced from grep |
| `02-protocol-73-patches.md` | Diff hunks vs ioquake3 baseline for `msg.c`, `q_shared.h`, `bg_public.h`, etc. — the gold |
| `03-ipc-commands.md` | What WolfWhisperer.exe sends to a wolfcamql child process (cmd-line + cfg surface; Ghidra RE pending) |
| `04-fragmovie-features.md` | Freecam, kill-cam, AVI/HuffYUV writer, MSAA, timescale, demo nav |
| `05-quirks-and-gotchas.md` | Platform-specific paths, hardcoded limits, QL bug workarounds |
| `06-protocol-73-port-plan.md` | Concrete sprint plan to lift proto-73 into q3mme as Tr4sH Quake Track A |

## Cross-references inside QUAKE LEGACY

- `docs/reference/dm73-format-deep-dive.md` — 1,337-line authoritative dm_73 byte-format
  spec (FT-1's source of truth). This directory cites it; do not duplicate.
- `docs/superpowers/specs/2026-04-17-engine-pivot-design.md` — the engine pivot spec
  that decided wolfcam → q3mme.
- `docs/superpowers/specs/2026-04-17-tr4sh-quake-manifesto.md` — the unifying SPLIT 2 vision.
- `phase2/dm73parser/` — FT-1 native parser. Validates against `UDT_json.exe`, *not*
  against wolfcamql (wolfcamql's parser is in C VM-bytecode form, hard to extract cleanly).
- `game-dissection/wolfcam-game/` — graphify-output (call-graph) of the game VM.
- `game-dissection/wolfwhisperer-scripts/` — graphify-output of the Python-side helpers.

## License posture

All code references in this directory are under GPL-2.0. Where diff hunks reproduce
wolfcamql source, original copyright headers are preserved or pointed to. Tr4sH
Quake (the eventual port destination) inherits GPL-2.0 — no relicensing needed.

---
*Generated 2026-04-17. Companion docs 01–05 are produced by parallel extraction
agents reading `tools/quake-source/wolfcamql-src/code/`.*
