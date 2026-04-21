# 06 — Protocol-73 Port Plan: Wolfcamql → q3mme (Tr4sH Quake Track A)

> **Audience.** A Tr4sH Quake engineer who has never read wolfcamql source.
> Following this plan should produce a q3mme fork that plays `.dm_73`
> (QuakeLive transitional protocol) without further reference to the
> wolfcamql tree. After this port lands, `tools/quake-source/wolfcamql-src/`
> can be deleted from the repo.
>
> **Source-of-truth docs.** This plan synthesizes findings from:
> - [02-protocol-73-patches.md](02-protocol-73-patches.md) — what wolfcam patched
> - [04-fragmovie-features.md](04-fragmovie-features.md) — features that already exist in q3mme vs need lifting
> - [05-quirks-and-gotchas.md](05-quirks-and-gotchas.md) — landmines to avoid
> - `docs/reference/dm73-format-deep-dive.md` — byte-format spec
> - `docs/superpowers/specs/2026-04-17-engine-pivot-design.md` — why q3mme is the target
> - `docs/superpowers/specs/2026-04-17-tr4sh-quake-manifesto.md` — SPLIT 2 vision
>
> **License.** Both source and target are GPL-2.0. Headers from wolfcamql files
> must be preserved on any code lifted. ID/ioquake3/wolfcamql credits must
> remain.

---

## Strategic stance

**Goal:** minimum-viable `.dm_73` playback in q3mme. *Not* full QL parity —
only what proto-73 demos actually carry on the wire. Proto-90/91 (modern QL)
is explicitly out of scope for sprint 1. If it works for proto-73, FT-1
(`phase2/dm73parser/`) plus this engine = full coverage of our 948-demo corpus.

**Why this is tractable:** per [02-protocol-73-patches.md](02-protocol-73-patches.md):

- `playerState_t` wire format for proto-73 is **identical** to proto-68.
  q3mme's existing playerState reader is reused unchanged.
- `entityState_t` wire format for proto-73 is proto-68 + **two** new
  trajectory-gravity fields (`pos.gravity`, `apos.gravity`).
- Huffman compression layer is byte-identical between wolfcam and ioquake3 —
  q3mme already has it, leave it alone.
- Network channel is protocol-agnostic — leave it alone.

The total wire-format delta for proto-73 is small. The bulk of the work is
**enum population** (entity events, configstring offsets, weapons, MoD)
which is mechanical, not architectural.

**LOC estimate:** ~800 LOC of real code + constant tables. Single sprint (1–2 weeks).

---

## Pre-flight checklist

Before writing any code:

- [ ] **Read wolfcam's CREDITS-wolfcam.txt** (under `tools/quake-source/wolfcamql-src/CREDITS-wolfcam.txt`). Anyone whose code is lifted needs attribution in the port commit messages.
- [ ] **Confirm q3mme baseline** via `cd tools/quake-source/q3mme/trunk && git status` — port from a clean tree. Branch name suggested: `tr4sh/proto73`.
- [ ] **Set up validation corpus.** Pick 3 demos from `WOLF WHISPERER/WolfcamQL/wolfcam-ql/demos/`. One CA round, one duel, one FFA. UDT_json.exe must accept all three (golden output). Wolfcamql.exe must play all three. Save MD5s.
- [ ] **Confirm FT-1 parser parity.** Each demo must produce identical entity-event sequences in `phase2/dm73parser/dm73dump` vs UDT_json.exe vs wolfcamql gamestate dumps. If FT-1 differs, fix FT-1 first — it is the reference for what proto-73 *should* produce.

---

## Sprint 1: Wire format — read enough proto-73 to advance time

### Task 1.1 — Bump constants in `qcommon/qcommon.h`

**File:** `tools/quake-source/q3mme/trunk/code/qcommon/qcommon.h`
**Wolfcam reference:** `qcommon.h:241-249`

Add (or modify):
```c
// Protocol family — q3mme keeps PROTOCOL_VERSION = 68 as primary.
// Proto 73 is a *demo-only* protocol; we only read it, never write it.
#define PROTOCOL_QL          91   // headline (informational only — not implemented)
#define PROTOCOL_TRANSITIONAL 73  // the one we actually implement
#define PROTOCOL_LEGACY_VERSION 68

// Demo-protocol whitelist for `.dm_NN` file extension matching:
#define NUM_DEMO_PROTOCOLS 5
extern int demo_protocols[NUM_DEMO_PROTOCOLS];
// Defined in common.c as: { 66, 67, 68, 73 }  // skip 43-48 DM3 family

// QL snapshots overflow the original 16384 limit. Wolfcam doubles it.
#undef MAX_MSGLEN
#define MAX_MSGLEN 32768

// New svc/clc opcodes that appear in proto-73 streams. Silent-skip is OK.
#define svc_voip      9   // QL VoIP marker — we ignore the payload
#define svc_extension 10  // future-proofing; ignore
```

**Why:** every byte beyond these constants is what enables a proto-73 stream
to be parsed without bounds-checking failure.

**Verify:** `grep -n PROTOCOL_VERSION trunk/code/qcommon/qcommon.h` shows the
new family definitions; `grep -n MAX_MSGLEN` shows 32768.

### Task 1.2 — Add `trajectory_t.gravity` in `qcommon/q_shared.h`

**File:** `tools/quake-source/q3mme/trunk/code/qcommon/q_shared.h`
**Wolfcam reference:** `q_shared.h` near the `trajectory_t` struct

```c
typedef struct {
    trType_t  trType;
    int       trTime;
    int       trDuration;
    vec3_t    trBase;
    vec3_t    trDelta;
    int       gravity;   // NEW — proto-73 carries this for both pos and apos
} trajectory_t;
```

**Why:** the two new entityState fields in proto-73 (`pos.gravity`,
`apos.gravity`) must land somewhere. They land here. Q3 demos zero these.

**Compatibility note:** changing struct size affects every cgame VM compiled
against the old layout. q3mme currently ships native cgame, not a VM — so no
QVM rebuild needed. Confirm at `q3mme/trunk/code/cgame/` that `cg_local.h`
includes `q_shared.h` directly. If a VM build is reintroduced later, all
cgame.qvm/ui.qvm must be rebuilt.

### Task 1.3 — Port `entityStateFieldsQldm73[]` into `qcommon/msg.c`

**File:** `tools/quake-source/q3mme/trunk/code/qcommon/msg.c`
**Wolfcam reference:** see [02-protocol-73-patches.md](02-protocol-73-patches.md) §`qcommon/msg.c` Patch 5 — table reproduced verbatim. This is THE GOLD. Copy it exactly. 52 entries.

Add the table next to q3mme's existing `entityStateFields[]`. Preserve the
GPL-2.0 attribution comment from wolfcam:

```c
/* entityStateFieldsQldm73[] — lifted verbatim from wolfcamql
 * (qcommon/msg.c). Original copyright: 2010-2017 brugal and contributors,
 * GPL-2.0. Carries the proto-68 field set + pos.gravity + apos.gravity. */
netField_t entityStateFieldsQldm73[] = {
    // ... 52 entries — see 02-protocol-73-patches.md Patch 5
};
#define ENTITY_STATE_FIELDS_QLDM73_COUNT \
    (sizeof(entityStateFieldsQldm73)/sizeof(entityStateFieldsQldm73[0]))
```

### Task 1.4 — Add protocol dispatch in `MSG_ReadDeltaEntity`

**File:** `qcommon/msg.c`
**Wolfcam reference:** see [02-protocol-73-patches.md](02-protocol-73-patches.md) §msg.c Patch 6/7

q3mme's current `MSG_ReadDeltaEntity` reads against the single
`entityStateFields[]`. Replace with a dispatcher keyed on `com_protocol`:

```c
void MSG_ReadDeltaEntity(msg_t *msg, entityState_t *from, entityState_t *to,
                         int number) {
    netField_t *fields;
    int         numFields;

    switch (com_protocol->integer) {
    case 73:
        fields    = entityStateFieldsQldm73;
        numFields = ENTITY_STATE_FIELDS_QLDM73_COUNT;
        break;
    default:                            // proto 66/67/68
        fields    = entityStateFields;
        numFields = ENTITY_STATE_FIELDS_COUNT;
        break;
    }
    /* ... existing reader using fields/numFields ... */
}
```

**Why:** at this point a proto-73 demo gets bytes-correct entity reads. No
crashes. Player positions and trajectories should now be sane in spec mode.

**Verify:** load `test_proto73_duel.dm_73`. Run with `+set developer 1`.
Watch for "MSG_ReadDeltaEntity bad bits" warnings — there should be zero.

### Task 1.5 — Add a soft-fail `MSG_Error` path

**Wolfcam reference:** [05-quirks-and-gotchas.md](05-quirks-and-gotchas.md) §"broken-demo recovery"

Some demos in our 948-demo corpus are *action extracts* (truncated). Wolfcam
gates a soft-fail behind `com_brokenDemo`. Lift the same pattern: instead of
`Com_Error(ERR_DROP, ...)` on read overflow, jump to a labeled `error:` block
that aborts the snapshot, marks the demo "EOF", and returns cleanly.

Add cvar in `common.c`:
```c
cvar_t *com_brokenDemo;
com_brokenDemo = Cvar_Get("com_brokenDemo", "1", CVAR_ARCHIVE);
```

**Why:** without this, a single corrupt snapshot kills the whole batch
render. Our pipeline cannot tolerate that — Phase 2 batch capture queues
hundreds of demos and skipping one is fine; aborting all is not.

### Task 1.6 — Commit checkpoint

```bash
cd tools/quake-source/q3mme
git checkout -b tr4sh/proto73
git add trunk/code/qcommon/{qcommon.h,q_shared.h,msg.c,common.c}
git commit -m "tr4sh: proto-73 wire-format read support

Lifts entityStateFieldsQldm73 from wolfcamql, adds trajectory gravity field,
bumps MAX_MSGLEN to 32768, adds soft-fail demo recovery path.

Proto-73 entityState wire format = proto-68 + pos.gravity + apos.gravity.
PlayerState format reused from proto-68 (no changes needed).

Refs: engine/wolfcam-knowledge-ingest/02-protocol-73-patches.md"
```

---

## Sprint 2: bg_public.h — make events readable

### Task 2.1 — Add QL `entity_event_t` enum

**File:** `tools/quake-source/q3mme/trunk/code/game/bg_public.h`
**Wolfcam reference:** [02-protocol-73-patches.md](02-protocol-73-patches.md) — full enum reproduction

Wolfcam renumbered every entity event to match QL. EV_OBITUARY is at value
**58** in proto-73 (was 64-ish in Q3). Without this, every kill detection in
our pipeline misfires — our highlight extractor (FT-2) will see "weapon
sound" where it should see "obituary".

Two options:

**Option A — replace q3mme's enum entirely.** Cleanest. Breaks q3mme's own
proto-68 demo support if anyone still uses it for Q3 demos. We don't, so
acceptable.

**Option B — add a parallel enum, dispatch on protocol.** Safer. Slightly
slower, more code. Not recommended for sprint 1.

**Recommendation:** Option A. Preserve old enum as `entityEventQ3_t` /
`EVQ3_*` in a comment block for reference, then replace.

```c
// Q3 baseline event enum preserved for reference:
// typedef enum { EVQ3_NONE = 0, EVQ3_FOOTSTEP, ... } entityEventQ3_t;

// QL/proto-73 event enum — lifted from wolfcamql bg_public.h
typedef enum {
    EV_NONE = 0,
    // ... (95+ values — see 02-protocol-73-patches.md for the full list)
    EV_OBITUARY = 58,
    // ...
    EV_NEW_HIGH_SCORE = 99,
} entity_event_t;
```

**Why:** every consumer downstream (FT-2 highlight scorer, frag-database
ingest, agent training set) keys off these constants. Wrong constants =
wrong dataset.

### Task 2.2 — Add QL `CS_*` configstring offsets

**File:** `qcommon/qcommon.h` (or wherever q3mme keeps `CS_*`)
**Wolfcam reference:** [02-protocol-73-patches.md](02-protocol-73-patches.md) — configstring layout

QL re-indexed configstrings. Player names are at index **529** for proto-73
(was 544 for Q3). Without the new offsets, our pipeline reads garbage where
player names should be.

```c
// QL configstring layout (proto 73, 90, 91)
#define CS_MODELS         17    // QL: 17..272
#define CS_SOUNDS         274   // QL: 274..529
#define CS_PLAYERS        529   // QL: 529..592
#define CS_LOCATIONS      593
#define CS_FLAGSTATUS     658
#define CS_ROUND_STATUS   661
#define CS_ROUND_TIME     662
#define CS_RED_PLAYERS_LEFT  663
#define CS_BLUE_PLAYERS_LEFT 664
```

**Why:** `phase2/dm73parser/` already uses these (FT-1 was written against
the QL spec). Engine must agree.

### Task 2.3 — Extend `weapon_t` and `meansOfDeath_t`

QL added weapons (Heavy MG, Chain LG variants) and MoDs that don't exist in
Q3. For proto-73 specifically, only a subset is in use; check
[02-protocol-73-patches.md](02-protocol-73-patches.md) for the exact list.

Add the missing entries. Keep numerical values identical to wolfcamql's enum
(downstream pipeline encodes weapon-id → weight via FT-2 weapon weights:
Rocket 2.0, Rail 1.5, Grenade-direct 2.5, LG 40/50/56-banded by accuracy).
A drift here breaks FT-2's frag scoring.

### Task 2.4 — Commit checkpoint

```bash
git add trunk/code/game/bg_public.h trunk/code/qcommon/qcommon.h
git commit -m "tr4sh: proto-73 event/configstring/weapon enums

Replaces Q3 entity_event_t with QL enum (EV_OBITUARY=58).
Adds QL configstring offsets (CS_PLAYERS=529).
Preserves Q3 enum as comment for reference.

Refs: 02-protocol-73-patches.md, FT-2 highlight criteria"
```

---

## Sprint 3: cl_parse.c — wire it together

### Task 3.1 — Protocol sniff from gamestate

**File:** `tools/quake-source/q3mme/trunk/code/client/cl_parse.c`
**Wolfcam reference:** [02-protocol-73-patches.md](02-protocol-73-patches.md) §cl_parse.c

The first message in a `.dm_73` stream is a gamestate. Parse the
`CS_SERVERINFO` configstring, extract the `\\protocol\\NN\\` key, set
`com_protocol`. q3mme currently hard-assumes proto-68; teach it to switch.

```c
// In CL_ParseGamestate, after reading CS_SERVERINFO:
const char *protoStr = Info_ValueForKey(serverInfo, "protocol");
int proto = atoi(protoStr);
if (proto != PROTOCOL_LEGACY_VERSION && proto != PROTOCOL_TRANSITIONAL) {
    Com_Printf(S_COLOR_YELLOW "Unknown protocol %d in demo, assuming 68\n", proto);
    proto = PROTOCOL_LEGACY_VERSION;
}
Cvar_SetValue("com_protocol", proto);
```

### Task 3.2 — Configstring dispatch

For each configstring index access, branch on `com_protocol`:

```c
int CL_PlayersConfigStringIndex(int playerNum) {
    if (com_protocol->integer == 73)
        return CS_PLAYERS + playerNum;       // QL: 529 + N
    return CSQ3_PLAYERS + playerNum;          // Q3: 544 + N
}
```

Apply the same pattern to `CS_MODELS`, `CS_SOUNDS`, `CS_LOCATIONS`, etc.

### Task 3.3 — `svc_voip` / `svc_extension` silent skip

In the snapshot opcode dispatch, add cases that read length-prefixed payloads
and discard. No interpretation.

### Task 3.4 — Commit checkpoint

```bash
git add trunk/code/client/cl_parse.c
git commit -m "tr4sh: proto-73 gamestate sniff + configstring dispatch

Reads protocol from CS_SERVERINFO at gamestate parse, sets com_protocol.
Routes configstring offsets through proto-aware accessors.
Silent-skips svc_voip, svc_extension opcodes.

Refs: 02-protocol-73-patches.md cl_parse.c section"
```

---

## Sprint 4: validation gate (BEFORE feature lifts)

**Do not proceed past this point until all four checks pass.**

- [ ] `tr4sh-q3mme +demo test_proto73_ca.dm_73 +set com_protocol 73` plays the demo end-to-end with no `Com_Error`.
- [ ] Player names render correctly (CS_PLAYERS offset works).
- [ ] Frag obituaries fire (EV_OBITUARY=58 wired through).
- [ ] Entity-event sequence from a 60s spec recording matches the entity-event sequence from `dm73dump` (FT-1 parser) and from `UDT_json.exe`. Allow ±1 frame jitter.
- [ ] Same three checks pass on the duel demo and the FFA demo.

If any fail, root-cause before continuing. Per `Vault/learnings.md` L94:
*don't bury knowledge mismatches; capture-lesson and fix.*

---

## Sprint 5: lift fragmovie features (only what q3mme lacks)

Per [04-fragmovie-features.md](04-fragmovie-features.md), q3mme **already** has:
- Camera path system (in fact, wolfcam ported q3mme's — we'd be re-importing it)
- DoF / motion blur (`mme_*` cvars — same code)
- AVI writer with timescale awareness
- Demo seek (more polished than wolfcam's)

q3mme **lacks** these wolfcam features that we want:

### Task 5.1 — `seekclock` (wall-clock demo seek)

**Why this matters:** WolfWhisperer's entire automation pattern is
`seekclock 8:52; video name :demoname; at 9:05 quit`
(see [03-ipc-commands.md](03-ipc-commands.md)). Without `seekclock`, our
existing batch-render scripts don't work.

q3mme has `demoSeek` (snapshot-index based). Wrap it with a wall-clock
helper that converts `MM:SS` → `serverTime`. Source in
[04-fragmovie-features.md](04-fragmovie-features.md) §6 names the file:
`cgame/cg_consolecmds.c:838` in wolfcam.

### Task 5.2 — `at <time> <cmd>` (timed command queue)

**Why this matters:** the canonical fragmovie recipe ends with
`at 9:05 quit` to terminate capture at the right frame. Without `at`, we'd
need a wall-clock Python watchdog killing the engine — fragile.

Wolfcam source: `cg_consolecmds.c:6783-6825`, gated by `cg_enableAtCommands`.
Lift the queue + tick-driven dispatcher. Add the gating cvar.

### Task 5.3 — `video pipe` (ffmpeg pipe mode)

**Why this matters:** [04-fragmovie-features.md](04-fragmovie-features.md)
calls this out as wolfcam's killer feature. Spawns ffmpeg as a child,
streams uncompressed frames over stdin → ffmpeg encodes directly to the
target format (av1_nvenc, h264, anything). Eliminates the
write-AVI-then-transcode round trip. q3mme writes AVI to disk; we want
direct ffmpeg pipe.

Source: `client/cl_main.c` near the `video` cmd handler. Lift the pipe-mode
branch (the rest is q3mme-equivalent).

**Per Rule P1-J** the project has locked AV1_NVENC UHQ 10-bit as the
final-render encoder — pipe mode lets the engine drive that directly
without intermediate disk I/O.

### Task 5.4 — `cg_freecam_useServerView`

**Why this matters:** with this set, freecam ignores PVS and sees ALL
entities. Critical for cinematic establishing shots where the camera flies
through walls and we still want to see the action on the other side.
Wolfcam-unique. Source: `cg_main.c:728-737` registers the cvar; consumer in
`cgame/wolfcam_view.c`.

### Task 5.5 — `Wolfcam_Follow_f` smart-follow modes

`follow killer` / `follow victim` auto-follow the next/previous obituary
participant. Useful for our agent training pipeline (Phase 3 — auto-frame
the action). Source: `wolfcam_consolecmds.c:150`. Modest port (~80 LOC).

### Task 5.6 — Skip these (q3mme already wins)

- Camera-path system (q3mme has the canonical implementation)
- DoF / motion blur (same `mme_*` code in both)
- MSAA (q3mme handles it; trivial cvar)
- Screenshot commands (both engines have them)
- Camera rewrite to be done at q3mme baseline — wolfcam's own author
  flagged its camera as *"viewpoint stuff is fucked"* per
  [05-quirks-and-gotchas.md](05-quirks-and-gotchas.md). Do not lift.

### Task 5.7 — Commit checkpoint

```bash
git add trunk/code/cgame/* trunk/code/client/*
git commit -m "tr4sh: lift wolfcam fragmovie features (seekclock, at, pipe, freecam)

Adds seekclock (wall-clock seek), at (timed cmd queue, gated by
cg_enableAtCommands), video pipe (ffmpeg child), cg_freecam_useServerView
(PVS bypass), follow killer|victim modes.

Skipped: camera paths (q3mme is canonical), DoF/blur (same code),
MSAA (q3mme equivalent), wolfcam camera (broken per author).

Refs: 04-fragmovie-features.md priority ranking"
```

---

## Sprint 6: validation gate #2 (end-to-end fragmovie)

- [ ] Build runs the full Phase 1 pipeline against tr4sh-q3mme as the
      capture engine instead of wolfcamql. (Update `WolfWhisperer.exe`
      replacement script — see [03-ipc-commands.md](03-ipc-commands.md)
      for the cfg pattern.)
- [ ] Render a Part 4 clip via the new engine. Compare frame-by-frame
      against the wolfcam-rendered version of the same clip. SSIM ≥ 0.95
      on a 60-second sample.
- [ ] Game audio + music mix per Rule P1-G (game 1.0, music 0.5) reproduces.
- [ ] Title card prepend per Rule P1-N still composes correctly downstream.
- [ ] Music-coverage rule (P1-O) still holds.

Per `Vault/rules/`, all rule numbers are gates. If any breaks, fix before
removing wolfcamql from the repo.

---

## Sprint 7: retire wolfcamql

Once Sprint 6 passes:

- [ ] `git rm -r tools/quake-source/wolfcamql-src tools/quake-source/wolfcamql-local-src`
- [ ] `git rm tools/wolfcamql/` (binary)
- [ ] Update `CLAUDE.md`:
  - Remove "WolfcamQL: G:\QUAKE_LEGACY\tools\wolfcamql\wolfcamql.exe"
  - Replace with "Tr4sH-q3mme: G:\QUAKE_LEGACY\tools\tr4sh-q3mme\tr4sh-q3mme.exe"
  - Update Rule P3-B (WolfcamQL command inventory) to point at this directory.
- [ ] Update `phase2/dm73parser/` if it cross-references wolfcam source paths.
- [ ] Update `WOLF WHISPERER/` Python helpers — rename, repoint at new engine.
- [ ] Final commit:
  ```bash
  git commit -m "engine: retire wolfcamql, tr4sh-q3mme is now the capture engine

  All proto-73 knowledge captured under
  engine/wolfcam-knowledge-ingest/.
  Tr4sH-q3mme now reads .dm_73 demos with full Phase 1 pipeline parity.

  Closes engine-pivot Track A. SPLIT 2 unblocked."
  ```

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `entityStateFieldsQldm73[]` table has a typo when copy-pasted | Med | High (silent data corruption) | Diff against [02-protocol-73-patches.md](02-protocol-73-patches.md) byte-for-byte. Validate against `UDT_json.exe`. |
| q3mme's cgame VM (if active) breaks from `trajectory_t` size change | Low | High (won't load) | q3mme native cgame, no VM in our build. Verify before Task 1.2. |
| Some demos in our corpus are protocol 90/91, not 73 | Med | Med (those won't play) | Run a corpus survey first: `for f in *.dm_73; do udt_json $f \| jq .protocol; done \| sort -u`. If 90/91 appear, scope sprint 8. |
| `at` command race condition (timed cmd fires after `quit` ran) | Low | Low (cosmetic) | Use wolfcam's exact dispatcher — they fixed this. |
| Wolfcam credit attribution missed in commit messages | Low | Low (license, but small) | Pre-flight task: read CREDITS-wolfcam.txt, list contributors in the umbrella PR description. |
| Tr4sH-q3mme renders look subtly different (lighting, colors) | Med | Med (regression vs wolfcam batch) | Render identical clip both engines, SSIM compare; if drift > 0.05, freeze on wolfcam-equivalent renderer settings. |

---

## What this plan does NOT do

- Does not implement proto-90/91 (modern QL). Our 948-demo corpus is proto-73; deferred.
- Does not port wolfcam's camera system (q3mme already has the canonical one).
- Does not port the q3mme-style scripting layer separately (q3mme already has it).
- Does not ship dm_73 *recording* — playback only. We never need to record proto-73.
- Does not solve Phase 2 demo-corpus extraction. That uses FT-1 (`phase2/dm73parser/`),
  which is independent of the engine.

---

## Success criteria (the bar)

When all of the following are true, wolfcamql can be deleted from the repo:

1. `tr4sh-q3mme +demo any-demo-from-our-corpus.dm_73` plays without errors.
2. WolfWhisperer-equivalent batch render (or its Python replacement) produces
   capture frames identical-within-tolerance to current wolfcam output.
3. Phase 1 pipeline (Parts 4-12) renders end-to-end against tr4sh-q3mme,
   passing all rule gates (P1-A through P1-Q).
4. FT-2 highlight scorer reads the same entity events from tr4sh-q3mme
   gamestate as it did from wolfcam gamestate (same MD5 on the JSON dump).
5. This document and 00–05 are sufficient to answer any "why does proto-73
   work this way?" question that comes up during the port — without
   re-reading wolfcamql source.

If criterion 5 is violated during the port (an engineer needs to crack open
wolfcamql), capture-lesson the gap and append to the relevant 0X- doc here.
That's the L94 contract.

---

*Plan authored 2026-04-17 from the four parallel extraction-agent reports.
Companion docs 00-05 contain the source material this plan synthesizes.*
