# Q3A Source Ingestion & Cross-Reference Report

**Date:** 2026-04-19
**Scope:** Cross-reference id Software's GPL-2 `Quake-III-Arena` source release (github.com/id-Software/Quake-III-Arena) against our local knowledge base and fine-tune what we know. Read-only — produces a patch-list, does NOT apply edits.
**Agent:** Q3A-ingestion (this report)

---

## 1. Upstream verification

### 1.1 GitHub repo state (id-Software/Quake-III-Arena)
- **Branch:** `master` only. No release branches, no tags published.
- **History:** single-commit "initial source drop" repo. id Software uploaded the GPL release and stopped — no further upstream activity in 10+ years.
- **Stars / forks:** ~8k / ~2.1k, **325 watchers**, **3 open PRs** (community, never merged by id).
- **License:** `COPYING.txt` — GNU GPL v2. Several non-GPL side-components with their own notices: zlib-based `.zip` handling, RSA MD4, ADPCM codec, Independent JPEG Group. Matches our local `quake3-source/COPYING.txt` (15,429 bytes).
- **README:** points at VC7 / cons / OSX project files and warns that "this build didn't get any kind of extensive testing so it may not work completely right." Matches the local `README.txt` (9,193 bytes).
- **Top-level tree:** `COPYING.txt`, `README.txt`, `code/`, `common/`, `lcc/`, `libs/`, `q3asm/`, `q3map/`, `q3radiant/`, `ui/`.

### 1.2 Local vendored copy vs upstream
Local tree at `G:/QUAKE_LEGACY/tools/quake-source/quake3-source/`:
- Top-level dirs: **identical** to upstream (same 8 dirs + `COPYING.txt`, `README.txt`, plus a `.git` from our clone).
- No missing branches/tags (upstream has none).
- **Conclusion:** our local copy is current with upstream tip. No re-clone needed. Upstream will almost certainly never receive a commit again — treat as frozen snapshot.

### 1.3 Canonical tree vs vanilla Q3A
`G:/QUAKE_LEGACY/engine/engines/_canonical/` is NOT a vanilla Q3A mirror — it is **wolfcamql-src with ioquake3 stubs grafted in** (SDL2, libcurl, libogg, AL, jpeg-8c side-by-side with the wolfcam-rewritten game/qcommon). Byte-identical to `tools/quake-source/wolfcamql-src/` for the core files I spot-checked (`bg_public.h`, `msg.c`).

🚩 **Finding:** the file names `TECHNICAL_NOTES.md` and `CUSTOM_PARSING.md` at the root of `_canonical/` are **UDT (uberdemotools) docs**, not ioquake3/wolfcam docs. They describe UDT's huffman decoder and its custom parsing API. This is easy to misread — they belong intellectually with `uberdemotools/` not with the engine tree.

---

## 2. Protocol constants — vanilla Q3A ground truth

All line numbers refer to `tools/quake-source/quake3-source/code/...` unless otherwise noted.

| Constant | Value | File:line |
|---|---|---|
| `PROTOCOL_VERSION` | **68** | `qcommon/qcommon.h:222` |
| `MAX_MSGLEN` | 16384 | `qcommon/qcommon.h:169` |
| `MAX_PACKET_USERCMDS` | 32 | `qcommon/qcommon.h:121` |
| `MAX_CLIENTS` | **64** | `game/q_shared.h:1092` |
| `GENTITYNUM_BITS` | 10 | `game/q_shared.h:1095` |
| `MAX_GENTITIES` | `(1<<10) = 1024` | `game/q_shared.h:1096` |
| `ENTITYNUM_NONE` | 1023 | `game/q_shared.h:1101` |
| `ENTITYNUM_WORLD` | 1022 | `game/q_shared.h:1102` |
| `MD3_IDENT` | `'IDP3'` FourCC | `qcommon/qfiles.h:113` |
| `MD3_VERSION` | 15 | `qcommon/qfiles.h:114` |
| `BSP_IDENT` | `'IBSP'` FourCC | `qcommon/qfiles.h:312` |
| `BSP_VERSION` | **46** (vanilla Q3) | `qcommon/qfiles.h:315` |
| `EV_EVENT_BITS` | `0x00000300` | `game/bg_public.h:784-786` |

`svc_ops_e` — vanilla Q3A has **9 opcodes only** (0..8), see `qcommon/qcommon.h:253-263`:
`svc_bad, svc_nop, svc_gamestate, svc_configstring, svc_baseline, svc_serverCommand, svc_download, svc_snapshot, svc_EOF`.
No `svc_extension`, no `svc_voip` — those are ioquake3/QL additions.

Weapons: `weapon_t` in vanilla is 11 base + 3 MISSIONPACK + `WP_NUM_WEAPONS` = **14** enum entries (`game/bg_public.h:305-324`). No `WP_HEAVY_MACHINEGUN`.

---

## 3. MOD_* enum — vanilla vs QL delta

Vanilla Q3A: `tools/quake-source/quake3-source/code/game/bg_public.h:572-604`.
QL (wolfcamql-src / canonical): `_canonical/code/game/bg_public.h:1293-1339`.

### Counts
| Build | Count | Max enum value |
|---|---|---|
| Vanilla Q3, **no MISSIONPACK** | 24 | `MOD_GRAPPLE = 23` |
| Vanilla Q3, **MISSIONPACK on** | 29 | `MOD_GRAPPLE = 28` |
| Quake Live (proto-73 / 91) | **34** | `MOD_RAILGUN_HEADSHOT = 33` |

### QL delta (over Q3 MISSIONPACK)
| Value | Name | Notes |
|---|---|---|
| 28 | `MOD_GRAPPLE` | kept, same slot |
| 29 | `MOD_SWITCH_TEAMS` | new in QL |
| 30 | `MOD_THAW` | FT (freeze tag) |
| 31 | `MOD_LIGHTNING_DISCHARGE` | QL-only; commented "demo?" in source |
| 32 | `MOD_HMG` | Heavy Machine Gun (QL exclusive) |
| 33 | `MOD_RAILGUN_HEADSHOT` | QL headshot distinction |

🚩 **Our deep-dive doc at `dm73-format-deep-dive.md` §0 TL;DR (line 44) cites `bg_public.h:1294-1339`** — that citation is to the **wolfcamql-src tree**, not the vanilla Q3A tree, and it is correct. Patch-list §8 below adds the vanilla comparison explicitly.

**CLAUDE.md §"Key Technical Facts" claims "34-entry MOD_* enum seed … protocol-73 confirmed via `MOD_HMG` + `MOD_RAILGUN_HEADSHOT`"** — ✅ verified exact on both counts.

---

## 4. EV_* enum — vanilla vs QL delta

Vanilla: `quake3-source/code/game/bg_public.h:347-452` (sequential 0..n).
QL: `_canonical/code/game/bg_public.h:791-923` (sparse with numeric annotations, protocol-aware renumbering).

### Counts
- **Vanilla Q3A:** 76 entries, `EV_NONE=0` through `EV_TAUNT_PATROL=75`.
- **QL / protocol 73:** at least **100+ populated values** plus a secondary `EV_STEP_*` block starting at **196**. Concrete numeric markers from the source:
  - `EV_POI = 90`, `EV_RACE_START = 93`, `EV_RACE_END = 95`
  - `EV_DAMAGEPLUM = 96`, `EV_AWARD = 97`, `EV_INFECTED = 98`, `EV_NEW_HIGH_SCORE = 99`
  - `EV_STEP_4 = 196` … `EV_STEP_24`

### QL delta (over vanilla)
| Value | Name | File:line |
|---|---|---|
| 19 | `EV_DROP_WEAPON` | `_canonical/bg_public.h:815` |
| 57 | `EV_DROWN` | :863 |
| 62 | `EV_POWERUP_ARMOR_REGEN` | :870 (added post-2010-12-26) |
| 81 | `EV_FOOTSTEP_SNOW` | :893 |
| 82 | `EV_FOOTSTEP_WOOD` | :894 |
| 83 | `EV_ITEM_PICKUP_SPEC` | :895 |
| 84 | `EV_OVERTIME` | :896 |
| 85 | `EV_GAMEOVER` | :897 |
| 87 | `EV_THAW_PLAYER` | :899 |
| 88 | `EV_THAW_TICK` | :900 |
| 89 | `EV_HEADSHOT` | :901 |
| 90 | `EV_POI` | :902 |
| 93 | `EV_RACE_START` | :904 |
| 94 | `EV_RACE_CHECKPOINT` | :905 |
| 95 | `EV_RACE_END` | :906 |
| 96 | `EV_DAMAGEPLUM` | :908 |
| 97 | `EV_AWARD` | :909 |
| 98 | `EV_INFECTED` | :910 |
| 99 | `EV_NEW_HIGH_SCORE` | :911 |
| 196-201 | `EV_STEP_4..24` | :914-919 (moved from vanilla 6-9 to 196+) |

🚩 `EV_OBITUARY = 58` in QL (canonical:865), was **76** in vanilla sequence — it is **renumbered**, not just "same slot." This is load-bearing for any parser that hardcodes the value.

🚩 CLAUDE.md §"Key Technical Facts" says "103-entry EV_* enum seed" — the exact count depends on how you count the `/*guess*/` gaps and the 196-block. Raw populated labels in `_canonical/bg_public.h:791-923` total ~62 explicit + 6 `EV_STEP_*` = ~68 distinct names (not 103). The "103" appears to be from a PE-probe count including padding — patch-list §8 proposes clarifying.

---

## 5. weapon_t enum — vanilla vs QL delta

Vanilla Q3A: `quake3-source/code/game/bg_public.h:305-324` (14 entries).
QL: `_canonical/code/game/bg_public.h:741-765` (15 entries).

| Slot | Vanilla | QL |
|---|---|---|
| 0 | `WP_NONE` | `WP_NONE` |
| 1 | `WP_GAUNTLET` | `WP_GAUNTLET` |
| 2 | `WP_MACHINEGUN` | `WP_MACHINEGUN` |
| 3 | `WP_SHOTGUN` | `WP_SHOTGUN` |
| 4 | `WP_GRENADE_LAUNCHER` | `WP_GRENADE_LAUNCHER` |
| 5 | `WP_ROCKET_LAUNCHER` | `WP_ROCKET_LAUNCHER` |
| 6 | `WP_LIGHTNING` | `WP_LIGHTNING` |
| 7 | `WP_RAILGUN` | `WP_RAILGUN` |
| 8 | `WP_PLASMAGUN` | `WP_PLASMAGUN` |
| 9 | `WP_BFG` | `WP_BFG` |
| 10 | `WP_GRAPPLING_HOOK` | `WP_GRAPPLING_HOOK` |
| 11 | `WP_NAILGUN` (MPACK) | `WP_NAILGUN` |
| 12 | `WP_PROX_LAUNCHER` (MPACK) | `WP_PROX_LAUNCHER` |
| 13 | `WP_CHAINGUN` (MPACK) | `WP_CHAINGUN` |
| 14 | `WP_NUM_WEAPONS` (sentinel) | **`WP_HEAVY_MACHINEGUN`** ← new in QL |
| 15 | — | `WP_MAX_NUM_WEAPONS_ALL_PROTOCOLS` (sentinel) |

🚩 **Gotcha:** vanilla slot 14 is the count sentinel `WP_NUM_WEAPONS`; QL slot 14 is a **real weapon**. A parser that hardcodes slot 14 as "invalid/sentinel" will mis-label every HMG frag. Our FT-1 custom C++ parser must key weapons off explicit enum values, not `< WP_NUM_WEAPONS`.

QL adds the comment `// all possible weapons for any demo protocol type, real max is a separate int WP_NUM_WEAPONS` (`_canonical/bg_public.h:739`) and keeps `extern int WP_NUM_WEAPONS;` (:767) so the *effective* weapon count varies per connected server.

---

## 6. BSP / MD3 format facts

### 6.1 BSP version
- Vanilla Q3A: `BSP_VERSION 46` (`qcommon/qfiles.h:315`).
- **QL / canonical: `BSP_VERSION 47`** (`_canonical/qcommon/qfiles.h:309`).
- `BSP_IDENT 'IBSP'` unchanged.

🚩 **Claim audit:** `docs/reference/map-catalog.md` and `weapon-models-catalog.md` do NOT mention a BSP version — safe. But any Phase 3.5 3D-intro work that loads QL maps must expect **IBSP v47**, not v46. A vanilla Q3A loader will reject every QL `.bsp`.

### 6.2 MD3 version
- Both trees: `MD3_IDENT 'IDP3'`, `MD3_VERSION 15`. Unchanged from 1999.
- `weapon-models-catalog.md` references "MD3 models: N" counts per part but does not cite the version — no drift to correct.

### 6.3 svc_ops_e
- Vanilla: 9 opcodes (0..8). `_canonical/qcommon/qcommon.h:281-296` adds `svc_extension = 9` and `svc_voip = 10`.
- `dm73-format-deep-dive.md` §1 table (lines 107-120) correctly lists 11 entries including extension + voip.

---

## 7. Knowledge gaps our docs have

1. **`playerStateFieldsQldm73[]` does not exist.** The deep-dive doc says "protocol 73 reuses `playerStateFieldsQ3[]` (msg.c:2990-2991)". Actual behavior in `_canonical/qcommon/msg.c:2470-2492`: for any `com_protocol >= 49` (which includes 73, 90, 91), the `DM3` writer falls back to `playerStateFieldsQ3dm48` with a FIXME log: `"FIXME MSG_WriteDeltaPlayerstateDM3 unknown field for protocol %d"`. Dedicated tables exist for **Qldm90 (msg.c:2190)** and **Qldm91 (msg.c:2123)** but NOT for proto-73. This is deliberate — wolfcam inherits the Q3dm48 playerstate layout for 73.
2. **QL adds `MOD_LIGHTNING_DISCHARGE = 31`**, flagged "demo?" in comment. Never documented in our reference set — may fire on demos of discharge kills in water. Worth a grep of our demo corpus to see its frequency.
3. **`EV_OBITUARY` value collision**: vanilla = 76, QL = 58. Any code referencing a literal integer for obituary is brittle. Deep-dive doc currently cites `bg_public.h:865` (QL = 58) — correct for wolfcam but does not note the renumbering.
4. **`EV_STEP_*` block at 196-201 in QL** is a protocol-aware renumber (vanilla placed them at 6-11). Our docs don't mention this.
5. **Protocol-91 field tables are present** in `_canonical/qcommon/msg.c:2123` (`playerStateFieldsQldm91`) and `:640+` (entityStateFieldsQldm91, per earlier `// 91` protocol gates). Future-proofs us for dm_91 demos without extra RE work. Our docs (deep-dive, SYNTHESIS.md) focus on 73/90 only.
6. **svc_extension mechanism** (qcommon.h:292-295) is undocumented in our deep-dive. It's how ioquake3/QL added `svc_voip` without breaking proto-68 legacy — a `svc_EOF` followed by `svc_extension` + another svc-op. Relevant if any demo we read was captured from a VoIP-enabled server.
7. **Upstream GitHub has 3 open pull requests** — nothing we can merge (id has no active maintainer), but worth a one-time skim in case any PR patches a known bug we'd benefit from (e.g. the Travis/64-bit fixes). Non-urgent.
8. **`TECHNICAL_NOTES.md` / `CUSTOM_PARSING.md` at `_canonical/` root are UDT docs**, not ioquake3 docs. They don't describe our actual engine — they describe the uberdemotools parser. Mis-filed.

---

## 8. Proposed doc updates — patch-list (DO NOT APPLY; user review first)

### 8.1 `docs/reference/dm73-format-deep-dive.md`

**Patch A — line 21-45 TL;DR block.** Add a second line under the existing citations making vanilla-vs-QL explicit:

```
Protocol values:          43..48 = Q3 era (non-huffman for 43, huffman from 46)
                          66..71 = Q3 standard                         (protocol constants: q_shared.h:29-32)
                          73, 90, 91 = Quake Live eras
                          Vanilla Q3 GPL = 68 (quake3-source/qcommon/qcommon.h:222)
Field tables (QL dm_73):  entityStateFieldsQldm73[] (msg.c:1081) — 58 fields
                          playerStateFieldsQldm73 DOES NOT EXIST. Proto-73 playerstate
                            reuses playerStateFieldsQ3dm48 with a FIXME log
                            (_canonical/qcommon/msg.c:2470-2492).
```

**Patch B — §1 after line 56 add a sentence:**

> Vanilla Q3A ships only 9 `svc_ops_e` opcodes (0..8, quake3-source/qcommon/qcommon.h:253-263).
> `svc_extension (9)` and `svc_voip (10)` are ioquake3/QL additions — a parser that hard-fails on unknown opcodes 9/10 will break on any demo captured against an ioquake3-derived server, not just QL.

**Patch C — new subsection §0.5 after line 45** (new 10-line block explaining `EV_OBITUARY` renumbering):

> ### EV_OBITUARY value is protocol-dependent
> | Protocol | `EV_OBITUARY` literal | Source |
> |---|---|---|
> | Vanilla Q3 (68) | 76 | quake3-source/bg_public.h sequential count |
> | QL (73/90/91) | **58** | _canonical/bg_public.h:865 |
>
> Any code keying on a literal integer rather than the enum symbol is brittle across protocols.

**Patch D — §2 Huffman init citation.** Deep-dive cites `qcommon/msg.c:3126-3383` — verify this is wolfcamql-src (which is 3433 lines total, so the range fits). Vanilla Q3A msg.c is only 1757 lines; its `msg_hData[]` is at `qcommon/msg.c:1537-1794` and `MSG_initHuffman` at `:1709`. Adding a one-line clarification:

> Vanilla Q3 equivalents (for cross-reference): `msg_hData[]` at `quake3-source/qcommon/msg.c:1537-1794`, `MSG_initHuffman` at `:1709`. The 256-entry frequency table bytes are byte-identical between vanilla Q3 and wolfcamql — the huffman seed survived unchanged into protocol 73.

### 8.2 `engine/engines/SYNTHESIS.md`

**Patch E — after line 71 "ioquake3" row**, add:

> **quake3-source (id GPL release)** — dormant upstream. Single-commit repo, id has not pushed since 2005. Our local `tools/quake-source/quake3-source/` is a frozen mirror. All modern Q3 work lives in ioquake3 or downstream forks.

**Patch F — §"Interesting diff files" (line 99) add a one-liner warning:**

> **Protocol-73 playerstate has no dedicated field table.** Wolfcam/canonical msg.c falls back to `playerStateFieldsQ3dm48` for proto=73 (`_canonical/qcommon/msg.c:2470-2492`). When porting to q3mme, do NOT invent a `playerStateFieldsQldm73[]` — match the fallback semantics.

### 8.3 `engine/engines/_canonical/TECHNICAL_NOTES.md` and `CUSTOM_PARSING.md`

**Patch G — prepend a header note (do not rewrite body):**

```markdown
> **Provenance note (added 2026-04-19):** These files are the UDT (uberdemotools)
> technical docs, copied into the canonical tree for convenience. They describe
> UDT's parser, NOT our ioquake3/wolfcamql engine. For engine-level docs see
> `docs/reference/dm73-format-deep-dive.md` and `engine/engines/SYNTHESIS.md`.
> Source: https://github.com/mightycow/uberdemotools
```

### 8.4 `CLAUDE.md` §"Key Technical Facts"

**Patch H — Frag Detection block clarifies protocol dependency:**

```diff
-entity.event & ~0x300 == EV_OBITUARY   # (0x300 masks the toggle bits)
+entity.event & ~0x300 == EV_OBITUARY
+  # QL / proto-73: EV_OBITUARY == 58 (_canonical/bg_public.h:865)
+  # Vanilla Q3 / proto-68: EV_OBITUARY == 76 (sequential from bg_public.h:422)
+  # ALWAYS resolve via the protocol's own enum table, never a literal
```

**Patch I — FT-4 section, "EV_* enum seed" line:**

```diff
-- 103-entry EV_* enum seed
+- ~68 named EV_* entries across two blocks (0-99 main + 196-201 footstep),
+  higher values are `/* guess */` placeholders. Older PE-probe count of 103
+  over-counted padding.
```

### 8.5 New doc to create (follow-up work, not in this pass): `docs/reference/q3-protocol-matrix.md`

Single table: for each protocol (43, 46, 48, 68, 73, 90, 91), list what field tables apply (entityState, playerState), which `svc_ops_e` values are valid, which `EV_OBITUARY` literal fires, and which `MOD_*` max index is legal. This is the dictionary any generic parser needs.

---

## 9. Q3mme port graft points — protocol-73 into q3mme

Gate **ENG-1 APPROVED** (Tr4sH Quake Track A). The goal: make q3mme load `.dm_73` demos without crashing, then progressively add field-level correctness until identical frame output to wolfcamql.

### 9.1 q3mme tree locations (`tools/quake-source/q3mme/trunk/code/qcommon/`)

| Target | q3mme file:line | Wolfcam source | Notes |
|---|---|---|---|
| `entityStateFields[]` (single table) | `msg.c:786` | `_canonical/msg.c:1081 entityStateFieldsQldm73` + `:1144 entityStateFieldsQ3` | Needs split into `Q3` + `Qldm73` + `Qldm90` + `Qldm91` tables, each gated by `com_protocol->integer` |
| `numFields = sizeof(entityStateFields)/sizeof(entityStateFields[0])` | `msg.c:866, :1013` | `_canonical/msg.c:1640-1660` branches on protocol | Replace 4 sites with a helper `getEntityFields(protocol)` |
| `playerStateFields[]` | `msg.c:1100` | `_canonical/msg.c:2244 playerStateFieldsQ3 + 2297/2346/2398 dm43/46/48 + 2123/2190 Qldm91/90` | Add 5 new tables and a protocol dispatcher. Proto-73 falls back to `Q3dm48` (FIXME in wolfcam). |
| `PROTOCOL_VERSION 68` | `qcommon/qcommon.h:219` | `_canonical/qcommon/qcommon.h:241-243` | Add `PROTOCOL_LEGACY_VERSION 68` + bump `PROTOCOL_VERSION 73` (or 91 for full coverage) |
| `demo_protocols[]` | `common.c:33` | Canonical has it live at `common.c` with same name | Add 73/90/91 to the compatible-protocols list |
| `svc_ops_e` (9 entries) | `qcommon.h:250` | `_canonical/qcommon.h:281-296` | Add `svc_extension`, `svc_voip` at positions 9, 10 |
| Huffman seed `msg_hData[]` | `msg.c:1515-1696` | identical | **No patch needed** — the seed table byte "73 → 1140" comment at `q3mme/msg.c:1523` is a huffman-frequency annotation for byte value 73, NOT a protocol marker. Previous speculation that it's a stray proto-73 reference is wrong. |

### 9.2 Game-header graft (`q3mme/trunk/code/game/`)

| Target | q3mme file:line | Wolfcam source | Action |
|---|---|---|---|
| `meansOfDeath_t` | `bg_public.h:570-601` (29 entries MPACK) | `_canonical/bg_public.h:1294-1339` (34 entries) | Add `MOD_SWITCH_TEAMS=29`, `MOD_THAW=30`, `MOD_LIGHTNING_DISCHARGE=31`, `MOD_HMG=32`, `MOD_RAILGUN_HEADSHOT=33` |
| `weapon_t` | `bg_public.h:305-324` (14 entries) | `_canonical/bg_public.h:741-765` | Insert `WP_HEAVY_MACHINEGUN = 14` before the sentinel; rename sentinel to `WP_MAX_NUM_WEAPONS_ALL_PROTOCOLS`; introduce `extern int WP_NUM_WEAPONS` |
| `entity_event_t` | `bg_public.h:347-452` | `_canonical/bg_public.h:789-924` | Full renumber — EV_OBITUARY moves 76→58, EV_STEP_* block moves to 196, add 20+ QL events |

### 9.3 Client demo path (`q3mme/trunk/code/client/`)

Files to diff against wolfcam's equivalents (do a full file-level diff before merging):
- `cl_parse.c` — entity/playerstate deserialization paths. Hot zone.
- `cl_demo.c` — demo read loop. wolfcam adds `.dm_73` opening heuristics.
- `cl_main.c:1566 CL_ReadDemoMessage` — per deep-dive §1, load-bearing for all protocol versions.
- `cl_cgame.c` — trap_ dispatch. q3mme has heavy camera/capture traps; wolfcam has QL cgame hooks. Merge carefully.

### 9.4 Verification gates after port

1. **Proto-68 regression test:** q3mme with patches must still play vanilla Q3 demos bit-identical to pre-patch output. Snapshot a frame diff at t=10s on a known demo.
2. **Proto-73 first light:** a single QL `.dm_73` opens without crash, outputs at least one frame. No field-level correctness required for this gate.
3. **Proto-73 entity parity:** compare q3mme-patched frame at t=30s against wolfcamql at same seek. Position + weapon + model index must match to within float epsilon.
4. **Proto-73 frag detection:** run FT-1 parser against 10 demos, and run a patched q3mme dump-every-EV_OBITUARY mode against the same 10 demos. Frag counts must agree ±0.

---

## 10. TL;DR

1. **Upstream is dormant.** id-Software/Quake-III-Arena has 1 commit ever; our local copy is current and will stay current indefinitely. No re-clone needed.
2. **Vanilla Q3 = protocol 68, BSP 46.** QL = protocol 73/90/91, BSP 47.
3. **MOD_* enum grew from 24/29 (vanilla) to 34 (QL)** — the 5 QL additions are `SWITCH_TEAMS, THAW, LIGHTNING_DISCHARGE, HMG, RAILGUN_HEADSHOT`. Confirmed by source.
4. **EV_* enum was renumbered across protocols, not just extended.** `EV_OBITUARY = 76` in vanilla vs `58` in QL. Any literal is a bug.
5. **weapon_t slot 14 changed meaning** — sentinel in vanilla, real weapon (HMG) in QL. FT-1 parser must not use `< WP_NUM_WEAPONS` as a validity check.
6. **`playerStateFieldsQldm73[]` does not exist** — proto-73 reuses `playerStateFieldsQ3dm48` via explicit FIXME fallback in `_canonical/msg.c:2470-2492`. Our deep-dive doc currently implies a dedicated table exists; patch-list fixes that.
7. **`svc_ops_e` has 9 entries in vanilla, 11 in QL** (adds `svc_extension=9`, `svc_voip=10`). Plain deep-dive coverage is correct; just needs the vanilla counterpoint added.
8. **The "// 73" in q3mme/msg.c:1523 is NOT a protocol marker** — it's a huffman-seed-table comment for byte value 73 (frequency 1140). No hidden proto-73 code to rediscover here.
9. **Canonical-tree docs `TECHNICAL_NOTES.md`/`CUSTOM_PARSING.md` are UDT docs**, not engine docs. Add a provenance header.
10. **Q3mme protocol-73 port is well-scoped:** ~6 field tables, 2 enum expansions, 2 opcode additions, and a `demo_protocols[]` list entry. All locations cited in §9 — no RE work remaining on the q3mme side.

---

*End of report. No source or doc files were modified by this pass.*
