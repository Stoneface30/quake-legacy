# PANTHEON Production Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `pantheon_cgame.exe` the engine that renders production demo clips, behind a switch, replacing `wolfcamql.exe` only after four measured parity gates pass and the user signs off.

**Architecture:** The host gains a demo reader (`pantheon_demo_feed.c`) that decodes `.dm_73` with the engine's *own* `msg.c`/`huffman.c` — the exact decoder that produces cgame's snapshots inside wolfcam — and pushes the recorded gamestate, snapshots and server commands through the existing feed seam (`pantheon_cg_feed.c`). A Python backend (`engine/pantheon/pantheon_capture.py`) implements `capture_demo`'s return contract exactly; `wolfcam_capture.capture_demo` dispatches on `PANTHEON_CAPTURE_BACKEND` (default `wolfcam`). Audio is produced from cgame's own sound calls, logged by the host and mixed offline. Wolfcam stays as the oracle (HL-2).

**Tech Stack:** C (MinGW i686, `gcc -m32`, WolfcamQL 11.3 sources), Python 3 (`E:/PersonalAI/venv`), pytest, ffmpeg (`store.PROJECT_ROOT/creative_suite/tools/ffmpeg/ffmpeg.exe`).

---

## Constraints (user decisions, 2026-09-12 — do not relitigate)

1. **The 64×64 WGL device-context window stays.** Output size is independent of the monitor (proven: 5120×2880, commit `cf27b8ac`). It still needs a valid interactive Windows graphics session; that is acceptable. Windowless context creation (EGL/pbuffer) is **out of scope** unless the renderer must run as a service.
2. **No supersampling merge until accumulation is linear-light.** Averaging display-encoded RGB darkens edges. Our own motion-blur accumulator has the same flaw and is fixed here (Task 10); `codex/capture-supersampling` must adopt the same resolve before it merges.
3. **No HDR/EXR, floating-point targets or asset work in this plan.** Task 11 is a *measurement* of whether values above 1.0 survive the renderer before tonemap/gamma/clamp. Its result decides whether an HDR plan is written at all.

## Rollout gates

| Gate | Proves | Pass condition |
|---|---|---|
| **G1** decoder agreement | The C reader decodes demos the same as `DM73Parser` | 3 demos, every snapshot: same `serverTime`, `ps.origin` within 0.5 u, same entity count |
| **G2** frame parity | PANTHEON pictures the same moment wolfcam does | 10 frags, review sheet per frag, **human PASS** recorded |
| **G3** audio parity | cgame's own sounds, mixed offline, land where wolfcam's do | 10 frags: envelope cross-correlation lag ≤ 40 ms and correlation ≥ 0.6 |
| **G4** contract parity | Callers cannot tell the backends apart | `capture_demo` returns the same keys and semantics; full suite green except pre-existing failures |

The default flips (Task 12) only after G1–G4 **and** the user's explicit go. A run that fails any gate leaves `wolfcam` the default.

## Known limits, stated up front

- **Pre-roll replaces seeking.** Deltas force the reader to parse from the start of the file, but cgame is only started `PREROLL_MS` (1500) before the window. Effects begun earlier than that (a smoke trail from a rocket fired 2 s before the window) are absent. Wolfcam's `seekclock` has the same property.
- **Looping sounds are out of G3.** Lava hum, powerup loops, the LG beam loop are logged but not mixed in v1; G3 measures one-shot sounds only.
- **Spatial audio is approximate.** Distance attenuation and stereo pan use Q3's constants; room acoustics are not modelled. G3 measures timing, not spatial accuracy.

---

## File Structure

| File | Responsibility |
|---|---|
| **Create** `engine/pantheon_renderer/host/pantheon_demo_feed.c` | `.dm_73` → gamestate + snapshots + server commands, using `msg.c`. Owns the delta rings. Knows nothing about rendering. |
| **Create** `engine/pantheon_renderer/host/pantheon_sound_log.c` | Registered sound names and every start/local sound event → a TSV sidecar. Plays nothing. |
| Modify `engine/pantheon_renderer/host/pantheon_cg_feed.c` | Apply `cs` / `bcs0/1/2` server commands to the stored gamestate, as `CL_ConfigstringModified` does. Carry `serverCommandSequence` in snapshots. |
| Modify `engine/pantheon_renderer/host/pantheon_cg_run.c` | `PANTHEON_CG_Init` takes the recorder's `clientNum` and the command sequence at pre-roll. |
| Modify `engine/pantheon_renderer/host/pantheon_cg_syscall.c` | Sound cases call the logger; `S_RegisterSound` returns real handles. |
| Modify `engine/pantheon_renderer/host/pantheon_frame.c` | `--demo`, `--window` (repeatable), `--fps`, `--dump-snapshots`, `--sound-log`; linear-light blur accumulate. |
| Modify `engine/pantheon_renderer/build_cgame.sh` | Compile the two new files. |
| Modify `engine/pantheon_renderer/build_host.sh` | Stop linking a standalone exe that has not linked since 2026-09-08; build objects only. |
| **Create** `engine/pantheon/pantheon_capture.py` | The backend: argv, permit, run, frames→AVI, mix, return the `capture_demo` dict. |
| **Create** `engine/pantheon/sound_mix.py` | Sound log + pak samples → stereo 48 kHz WAV. Pure function of its inputs. |
| Modify `creative_suite/engine/wolfcam_capture.py` | `capture_demo` dispatches on `PANTHEON_CAPTURE_BACKEND`. |
| Modify `engine/pantheon/backends.py` | Register `PANTHEON_NATIVE`. |
| Modify `engine/pantheon/model_assets.py:28` | Resolve the host through `store`, pointing at the exe that exists. |
| **Create** `creative_suite/tests/test_pantheon_capture.py` | Contract tests (G4), mixer tests, dispatch tests. |
| **Create** `creative_suite/tests/test_pantheon_demo_feed.py` | G1, integration; skips when the corpus or exe is absent. |
| Modify `creative_suite/tests/test_render_permit.py` | Add `engine/pantheon/pantheon_capture.py` to `LAUNCH_SITES`. |
| Modify `creative_suite/tests/test_pantheon_headless_boundary.py` | Classify `pantheon_capture` and `sound_mix` as `BACKEND_ALLOWED`. |

Run all Python tests with: `E:/PersonalAI/venv/Scripts/python.exe -m pytest <path> -q`
Build with: `cd engine/pantheon_renderer && ./build_host.sh && ./build_cgame.sh` (Git Bash).

---

### Task 0: Worktree and baseline

**Files:** none

- [ ] **Step 1: Create an isolated worktree** (@superpowers:using-git-worktrees)

```bash
git worktree add ../QUAKE_LEGACY_WORKTREES/pantheon-capture -b feature/pantheon-production-capture demo-v2-mining
```

- [ ] **Step 2: Record the baseline failures, so later tasks are judged against them and not against zero**

Run: `E:/PersonalAI/venv/Scripts/python.exe -m pytest creative_suite/tests -q -p no:cacheprovider 2>&1 | tail -15 > docs/reference/2026-09-12-capture-baseline.txt`
Expected (2026-09-12): failures only in `test_scene_editor.py` (live frags DB) and `test_tool_root.py::test_no_new_module_finds_its_tools_beside_the_code` (another session's untracked `engine/music/`). Anything else: stop and report.

- [ ] **Step 3: Commit the baseline**

```bash
git add docs/reference/2026-09-12-capture-baseline.txt
git commit -m "docs: test baseline before the PANTHEON capture work"
```

---

### Task 1: One binary, found through the store

The standalone `pantheon_frame.exe` has not linked since 2026-09-08 (`build_host.sh` omits the cgame objects that `pantheon_frame.c` now calls) and no longer exists on disk. `model_assets.py:28` still points at it by a hardcoded `G:/` path (HL-9). `pantheon_cgame.exe` accepts `--dump-model` because it is built from the same `pantheon_frame.c`.

**Files:**
- Modify: `engine/pantheon_renderer/build_host.sh` (the final link line)
- Modify: `engine/pantheon/model_assets.py:28`
- Create: `engine/pantheon/pantheon_capture.py` (only `host_exe()` in this task)
- Test: `creative_suite/tests/test_pantheon_capture.py`

- [ ] **Step 1: Write the failing test**

```python
# creative_suite/tests/test_pantheon_capture.py
from pathlib import Path

from engine.pantheon import store as S


def test_host_exe_is_resolved_through_the_store_not_a_drive_letter():
    from engine.pantheon import pantheon_capture as PC
    exe = PC.host_exe()
    assert exe == S.CODE_ROOT / "engine" / "pantheon_renderer" / "build" / "pantheon_cgame.exe"


def test_model_assets_uses_the_one_binary_that_exists():
    from engine.pantheon import model_assets, pantheon_capture as PC
    assert model_assets.HOST_EXE == PC.host_exe()
    assert "G:/" not in Path(model_assets.__file__).read_text(encoding="utf-8").split("HOST_EXE", 1)[1][:120]
```

- [ ] **Step 2: Run to verify it fails**

Run: `E:/PersonalAI/venv/Scripts/python.exe -m pytest creative_suite/tests/test_pantheon_capture.py -q`
Expected: FAIL — `ModuleNotFoundError: engine.pantheon.pantheon_capture`

- [ ] **Step 3: Implement**

```python
# engine/pantheon/pantheon_capture.py
"""PANTHEON_NATIVE capture backend.

Renders production demo clips with pantheon_cgame.exe: our own binary, the
WolfcamQL 11.3 renderer and cgame linked statically, drawing into its own
framebuffer object. Implements the same return contract as
creative_suite.engine.wolfcam_capture.capture_demo so callers cannot tell the
two backends apart (gate G4).
"""
from __future__ import annotations

from pathlib import Path

from engine.pantheon import store as S


def host_exe() -> Path:
    """The one PANTHEON binary. Resolved from the code root (HL-9), never a
    drive letter: a worktree must run its own build."""
    return S.CODE_ROOT / "engine" / "pantheon_renderer" / "build" / "pantheon_cgame.exe"
```

In `engine/pantheon/model_assets.py` replace line 28:

```python
from engine.pantheon.pantheon_capture import host_exe as _host_exe
HOST_EXE = _host_exe()
```

In `engine/pantheon_renderer/build_host.sh`, replace the final `$CC ... -o "$OUT/pantheon_frame.exe" ...` link command with:

```bash
# The standalone pantheon_frame.exe stopped linking on 2026-09-08, when
# pantheon_frame.c started calling cgame. There is one binary now:
# build_cgame.sh links these objects into pantheon_cgame.exe.
echo "built objects in $OUT (link with ./build_cgame.sh)"
```

- [ ] **Step 4: Run tests and both builds**

Run: `E:/PersonalAI/venv/Scripts/python.exe -m pytest creative_suite/tests/test_pantheon_capture.py -q`
Expected: 2 passed
Run: `cd engine/pantheon_renderer && ./build_host.sh && ./build_cgame.sh`
Expected: both exit 0; `build/pantheon_cgame.exe` exists.

- [ ] **Step 5: Commit**

```bash
git add engine/pantheon/pantheon_capture.py engine/pantheon/model_assets.py engine/pantheon_renderer/build_host.sh creative_suite/tests/test_pantheon_capture.py
git commit -m "fix: one PANTHEON binary, found through the store"
```

---

### Task 2: The demo reader

Mirrors `CL_ReadDemoMessage` (`cl_main.c:1063`), `CL_ParseServerMessage` (`cl_parse.c:1703`), `CL_ParseGamestate` (`:830`), `CL_ParseSnapshot` (`:383`), `CL_ParsePacketEntities` (`:108`) and `CL_DeltaEntity` (`:80`), with the client globals replaced by one `pdemo_t`. Copy logic, not ideas: every branch below has a counterpart in those functions.

**Files:**
- Create: `engine/pantheon_renderer/host/pantheon_demo_feed.c`
- Modify: `engine/pantheon_renderer/build_cgame.sh` (add a compile line next to `pantheon_cg_feed.c`)

- [ ] **Step 1: Write the reader**

```c
/*
 * A .dm_73 BECOMES A SNAPSHOT FEED.
 *
 * Decoded with the engine's own msg.c and huffman.c -- the same functions
 * that fill cl.snapshots inside WolfcamQL -- so a snapshot handed to cgame
 * here is bit-for-bit the one wolfcam would have handed it. Nothing is
 * reinterpreted: this file is cl_parse.c with the client globals replaced by
 * one struct, and every branch has a counterpart there (line numbers in the
 * comments). DM73Parser in Python is the independent cross-check (gate G1).
 */
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/qcommon.h"
#include "../wolfcamql-11.3-src/wolfcamql-src/code/cgame/cg_public.h"

#include <stdio.h>
#include <string.h>

#define PD_MAX_PARSE_ENTITIES 2048          /* as MAX_PARSE_ENTITIES */

typedef struct {
    qboolean      valid;
    int           messageNum, deltaNum, serverTime, snapFlags;
    int           serverCommandNum;
    byte          areamask[MAX_MAP_AREA_BYTES];
    playerState_t ps;
    int           numEntities, parseEntitiesNum;
} pdSnap_t;

typedef struct {
    FILE         *f;
    int           messageSeq;               /* clc.serverMessageSequence */
    int           commandSeq;               /* clc.serverCommandSequence */
    int           clientNum;
    gameState_t   gs;
    entityState_t baselines[MAX_GENTITIES];
    pdSnap_t      snaps[PACKET_BACKUP];
    entityState_t parse[PD_MAX_PARSE_ENTITIES];
    int           parseNum;
    pdSnap_t      latest;                   /* most recent valid snapshot */
    qboolean      haveGamestate, haveLatest;
} pdemo_t;

static pdemo_t pd;

/* feed seam (pantheon_cg_feed.c) */
void PANTHEON_CG_SetGameState(const gameState_t *gs);
void PANTHEON_CG_QueueServerCommandSeq(int seq, const char *text);

/* cl_parse.c:80 */
static void PD_DeltaEntity(msg_t *msg, pdSnap_t *frame, int newnum,
                           entityState_t *old, qboolean unchanged)
{
    entityState_t *state = &pd.parse[pd.parseNum & (PD_MAX_PARSE_ENTITIES - 1)];
    if (unchanged) *state = *old;
    else           MSG_ReadDeltaEntity(msg, old, state, newnum);
    if (state->number == MAX_GENTITIES - 1) return;   /* delta-removed */
    pd.parseNum++;
    frame->numEntities++;
}

#define PD_OLDSTATE(of, i) (&pd.parse[((of)->parseEntitiesNum + (i)) & (PD_MAX_PARSE_ENTITIES - 1)])

/* cl_parse.c:108 */
static void PD_ParsePacketEntities(msg_t *msg, const pdSnap_t *oldframe,
                                   pdSnap_t *newframe)
{
    int newnum, oldindex = 0, oldnum;
    entityState_t *oldstate = NULL;

    newframe->parseEntitiesNum = pd.parseNum;
    newframe->numEntities = 0;
    if (!oldframe || oldframe->numEntities == 0) oldnum = 99999;
    else { oldstate = PD_OLDSTATE(oldframe, 0); oldnum = oldstate->number; }

#define PD_NEXT_OLD() do { oldindex++; \
        if (!oldframe || oldindex >= oldframe->numEntities) oldnum = 99999; \
        else { oldstate = PD_OLDSTATE(oldframe, oldindex); oldnum = oldstate->number; } \
    } while (0)

    for (;;) {
        newnum = MSG_ReadBits(msg, GENTITYNUM_BITS);
        if (newnum == MAX_GENTITIES - 1) break;
        if (msg->readcount > msg->cursize)
            Com_Error(ERR_DROP, "PANTHEON demo: packet entities past end of message");
        while (oldnum < newnum) { PD_DeltaEntity(msg, newframe, oldnum, oldstate, qtrue); PD_NEXT_OLD(); }
        if (oldnum == newnum) { PD_DeltaEntity(msg, newframe, newnum, oldstate, qfalse); PD_NEXT_OLD(); continue; }
        if (oldnum > newnum) PD_DeltaEntity(msg, newframe, newnum, &pd.baselines[newnum], qfalse);
    }
    while (oldnum != 99999) { PD_DeltaEntity(msg, newframe, oldnum, oldstate, qtrue); PD_NEXT_OLD(); }
#undef PD_NEXT_OLD
}

/* cl_parse.c:383 -- demo playback branch only */
static void PD_ParseSnapshot(msg_t *msg)
{
    pdSnap_t ns, *old;
    int deltaNum, len;

    memset(&ns, 0, sizeof(ns));
    ns.serverCommandNum = pd.commandSeq;
    ns.serverTime = MSG_ReadLong(msg);
    ns.messageNum = pd.messageSeq;
    deltaNum = MSG_ReadByte(msg);
    ns.deltaNum = deltaNum ? ns.messageNum - deltaNum : -1;
    ns.snapFlags = MSG_ReadByte(msg);

    if (ns.deltaNum <= 0) { ns.valid = qtrue; old = NULL; }
    else {
        old = &pd.snaps[ns.deltaNum & PACKET_MASK];
        ns.valid = old->valid && old->messageNum == ns.deltaNum;
    }

    len = MSG_ReadByte(msg);
    if (len > (int)sizeof(ns.areamask))
        Com_Error(ERR_DROP, "PANTHEON demo: areamask length %d", len);
    MSG_ReadData(msg, &ns.areamask, len);

    MSG_ReadDeltaPlayerstate(msg, old ? &old->ps : NULL, &ns.ps);
    PD_ParsePacketEntities(msg, old, &ns);

    if (!ns.valid) return;
    pd.snaps[ns.messageNum & PACKET_MASK] = ns;
    pd.latest = ns;
    pd.haveLatest = qtrue;
}

/* cl_parse.c:830 */
static void PD_ParseGamestate(msg_t *msg)
{
    entityState_t nullstate;
    int cmd, i, len, newnum;
    char *s;

    memset(&pd.gs, 0, sizeof(pd.gs));
    memset(pd.baselines, 0, sizeof(pd.baselines));
    memset(pd.snaps, 0, sizeof(pd.snaps));
    pd.commandSeq = MSG_ReadLong(msg);
    pd.gs.dataCount = 1;
    for (;;) {
        cmd = MSG_ReadByte(msg);
        if (cmd == svc_EOF) break;
        if (cmd == svc_configstring) {
            i = MSG_ReadShort(msg);
            if (i < 0 || i >= MAX_CONFIGSTRINGS)
                Com_Error(ERR_DROP, "PANTHEON demo: configstring %d", i);
            s = MSG_ReadBigString(msg);
            len = strlen(s);
            if (len + 1 + pd.gs.dataCount > MAX_GAMESTATE_CHARS)
                Com_Error(ERR_DROP, "PANTHEON demo: MAX_GAMESTATE_CHARS");
            if (i == 0) {
                /* cl_parse.c:862 -- msg.c picks its field tables from this */
                int p = atoi(Info_ValueForKey(s, "protocol"));
                int cp = atoi(Info_ValueForKey(s, "com_protocol"));
                if ((p >= 66 && p <= 71) || (cp >= 66 && cp <= 71))
                    Cvar_Set("protocol", va("%d", PROTOCOL_Q3));
                else if (p == 73 || p == 90) Cvar_Set("protocol", va("%d", p));
                else Cvar_Set("protocol", va("%d", PROTOCOL_QL));
            }
            pd.gs.stringOffsets[i] = pd.gs.dataCount;
            memcpy(pd.gs.stringData + pd.gs.dataCount, s, len + 1);
            pd.gs.dataCount += len + 1;
        } else if (cmd == svc_baseline) {
            newnum = MSG_ReadBits(msg, GENTITYNUM_BITS);
            if (newnum < 0 || newnum >= MAX_GENTITIES)
                Com_Error(ERR_DROP, "PANTHEON demo: baseline %d", newnum);
            memset(&nullstate, 0, sizeof(nullstate));
            MSG_ReadDeltaEntity(msg, &nullstate, &pd.baselines[newnum], newnum);
        } else Com_Error(ERR_DROP, "PANTHEON demo: bad gamestate byte %d", cmd);
    }
    pd.clientNum = MSG_ReadLong(msg);
    (void)MSG_ReadLong(msg);                   /* checksumFeed */
    pd.haveGamestate = qtrue;
    PANTHEON_CG_SetGameState(&pd.gs);
}

/* cl_parse.c:1703 */
static void PD_ParseServerMessage(msg_t *msg)
{
    int cmd, seq;
    char *s;

    MSG_Bitstream(msg);
    (void)MSG_ReadLong(msg);                   /* reliableAcknowledge */
    for (;;) {
        if (msg->readcount > msg->cursize)
            Com_Error(ERR_DROP, "PANTHEON demo: read past end of message");
        cmd = MSG_ReadByte(msg);
        if (cmd == svc_EOF && MSG_LookaheadByte(msg) == svc_extension) {
            MSG_ReadByte(msg);
            cmd = MSG_ReadByte(msg);
            if (cmd == -1) cmd = svc_EOF;
        }
        if (cmd == svc_EOF) break;
        switch (cmd) {
        case svc_nop: break;
        case svc_serverCommand:              /* cl_parse.c:1338 */
            seq = MSG_ReadLong(msg);
            s = MSG_ReadString(msg);
            if (pd.commandSeq >= seq) break;
            pd.commandSeq = seq;
            PANTHEON_CG_QueueServerCommandSeq(seq, s);
            break;
        case svc_gamestate: PD_ParseGamestate(msg); break;
        case svc_snapshot:  PD_ParseSnapshot(msg);  break;
        default:
            Com_Error(ERR_DROP, "PANTHEON demo: unsupported server message %d", cmd);
        }
    }
}

qboolean PANTHEON_Demo_Open(const char *path)
{
    memset(&pd, 0, sizeof(pd));
    pd.f = fopen(path, "rb");
    return pd.f != NULL;
}

/* cl_main.c:1063. Returns qfalse at end of demo. */
qboolean PANTHEON_Demo_ReadMessage(void)
{
    static byte data[MAX_MSGLEN];
    msg_t buf;
    int seq, len;

    if (!pd.f || fread(&seq, 4, 1, pd.f) != 1) return qfalse;
    pd.messageSeq = LittleLong(seq);
    if (fread(&len, 4, 1, pd.f) != 1) return qfalse;
    len = LittleLong(len);
    if (len == -1) return qfalse;
    if (len < 0 || len > MAX_MSGLEN)
        Com_Error(ERR_DROP, "PANTHEON demo: message length %d", len);
    MSG_Init(&buf, data, sizeof(data));
    if ((int)fread(buf.data, 1, len, pd.f) != len) return qfalse;   /* truncated */
    buf.cursize = len;
    buf.readcount = 0;
    PD_ParseServerMessage(&buf);
    return qtrue;
}

/* The newest valid snapshot, as cgame's snapshot_t (cl_cgame.c CL_GetSnapshot). */
qboolean PANTHEON_Demo_Latest(snapshot_t *out, int *messageNum)
{
    int i, n;
    if (!pd.haveLatest) return qfalse;
    memset(out, 0, sizeof(*out));
    out->snapFlags = pd.latest.snapFlags;
    out->serverCommandSequence = pd.latest.serverCommandNum;
    out->serverTime = pd.latest.serverTime;
    memcpy(out->areamask, pd.latest.areamask, sizeof(out->areamask));
    out->ps = pd.latest.ps;
    n = pd.latest.numEntities;
    if (n > MAX_ENTITIES_IN_SNAPSHOT) n = MAX_ENTITIES_IN_SNAPSHOT;
    for (i = 0; i < n; i++)
        out->entities[i] = *PD_OLDSTATE(&pd.latest, i);
    out->numEntities = n;
    *messageNum = pd.latest.messageNum;
    return qtrue;
}

int  PANTHEON_Demo_ClientNum(void)       { return pd.clientNum; }
int  PANTHEON_Demo_CommandSequence(void) { return pd.commandSeq; }
const gameState_t *PANTHEON_Demo_GameState(void) { return &pd.gs; }
void PANTHEON_Demo_Close(void) { if (pd.f) fclose(pd.f); pd.f = NULL; }
```

- [ ] **Step 2: Add the compile line** in `build_cgame.sh`, directly after the `pantheon_cg_feed.c` line:

```bash
$CC $CGFLAGS $INC -c "$HERE/host/pantheon_demo_feed.c" -o "$OBJ/pantheon_demo_feed.o"
```

- [ ] **Step 3: Build**

Run: `cd engine/pantheon_renderer && ./build_cgame.sh`
Expected: exit 0. (It will fail to link until Task 3 adds `PANTHEON_CG_QueueServerCommandSeq`; if so, do Task 3 Step 1 now and rebuild.)

- [ ] **Step 4: Commit**

```bash
git add engine/pantheon_renderer/host/pantheon_demo_feed.c engine/pantheon_renderer/build_cgame.sh
git commit -m "feat: PANTHEON reads .dm_73 with the engine's own decoder"
```

---

### Task 3: Server commands and configstrings, as the client applies them

In the real client, `CL_GetServerCommand` rewrites `cl.gameState` when a `cs` command arrives (`CL_ConfigstringModified`) and joins `bcs0/bcs1/bcs2` big configstrings, *before* cgame reads the command. cgame then calls `trap_GetGameState` to see the new value. Without this, scores, player joins, model changes and the warmup/round clock never update.

**Files:**
- Modify: `engine/pantheon_renderer/host/pantheon_cg_feed.c`

- [ ] **Step 1: Add sequence-numbered queueing and configstring application**

```c
/* Queue with the sequence the SERVER gave it, not our own counter: cgame's
 * snapshot.serverCommandSequence is the server's number, and cgame asks for
 * exactly those. */
void PANTHEON_CG_QueueServerCommandSeq(int seq, const char *text)
{
    if (!text || seq <= 0) return;
    Q_strncpyz(cg_cmds[seq % PANTHEON_CMD_RING], text, BIG_INFO_STRING);
    cg_cmd_num[seq % PANTHEON_CMD_RING] = seq;
    if (seq > cg_cmd_seq) cg_cmd_seq = seq;
}

/* cl_cgame.c CL_ConfigstringModified: rebuild the string pool with one
 * index replaced. */
static void PANTHEON_CG_SetConfigstring(int index, const char *value)
{
    gameState_t old = cg_gs;
    int i, len;

    if (index < 0 || index >= MAX_CONFIGSTRINGS) return;
    memset(&cg_gs, 0, sizeof(cg_gs));
    cg_gs.dataCount = 1;
    for (i = 0; i < MAX_CONFIGSTRINGS; i++) {
        const char *s = (i == index) ? value
                      : (old.stringOffsets[i] ? old.stringData + old.stringOffsets[i] : "");
        if (!s[0]) continue;
        len = strlen(s);
        if (len + 1 + cg_gs.dataCount > MAX_GAMESTATE_CHARS)
            Com_Error(ERR_DROP, "PANTHEON: MAX_GAMESTATE_CHARS applying cs %d", index);
        cg_gs.stringOffsets[i] = cg_gs.dataCount;
        memcpy(cg_gs.stringData + cg_gs.dataCount, s, len + 1);
        cg_gs.dataCount += len + 1;
    }
}
```

Add `static int cg_cmd_num[PANTHEON_CMD_RING];` beside `cg_cmds`, and `static char cg_bigcs[BIG_INFO_STRING];`.

Replace `PANTHEON_CG_GetServerCommand` with:

```c
qboolean PANTHEON_CG_GetServerCommand(int seq)
{
    const char *cmd;
    if (seq <= 0 || seq > cg_cmd_seq) return qfalse;
    if (cg_cmd_num[seq % PANTHEON_CMD_RING] != seq) return qfalse;   /* aged out */
    Cmd_TokenizeString(cg_cmds[seq % PANTHEON_CMD_RING]);
    cmd = Cmd_Argv(0);

    /* cl_cgame.c CL_GetServerCommand: big configstrings arrive in pieces */
    if (!strcmp(cmd, "bcs0")) { Q_strncpyz(cg_bigcs, va("cs %s \"%s", Cmd_Argv(1), Cmd_Argv(2)), sizeof(cg_bigcs)); return qfalse; }
    if (!strcmp(cmd, "bcs1")) { Q_strcat(cg_bigcs, sizeof(cg_bigcs), Cmd_Argv(2)); return qfalse; }
    if (!strcmp(cmd, "bcs2")) {
        Q_strcat(cg_bigcs, sizeof(cg_bigcs), va("%s\"", Cmd_Argv(2)));
        Cmd_TokenizeString(cg_bigcs);
        cmd = Cmd_Argv(0);
    }
    if (!strcmp(cmd, "cs")) {
        PANTHEON_CG_SetConfigstring(atoi(Cmd_Argv(1)), Cmd_ArgsFrom(2));
        Cmd_TokenizeString(cg_cmds[seq % PANTHEON_CMD_RING]);   /* cgame re-reads it */
        if (!strcmp(Cmd_Argv(0), "bcs2")) Cmd_TokenizeString(cg_bigcs);
    }
    return qtrue;
}
```

In `PANTHEON_CG_Reset`, also `memset(cg_cmd_num, 0, sizeof(cg_cmd_num));`.

- [ ] **Step 2: Build**

Run: `cd engine/pantheon_renderer && ./build_cgame.sh`
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
git add engine/pantheon_renderer/host/pantheon_cg_feed.c
git commit -m "feat: configstring changes reach cgame the way the client applies them"
```

---

### Task 4: `--dump-snapshots` and gate G1

The decoder is the one place a subtle bug corrupts every frame downstream. It is proven against the independent Python decoder before anything renders from it.

**Files:**
- Modify: `engine/pantheon_renderer/host/pantheon_frame.c` (argument parsing, and an early-exit mode after `Com_Init`)
- Create: `creative_suite/tests/test_pantheon_demo_feed.py`

- [ ] **Step 1: Add the mode to `pantheon_frame.c`**

Declarations near the other `PANTHEON_CG_*` prototypes:

```c
qboolean PANTHEON_Demo_Open(const char *path);
qboolean PANTHEON_Demo_ReadMessage(void);
qboolean PANTHEON_Demo_Latest(snapshot_t *out, int *messageNum);
int      PANTHEON_Demo_ClientNum(void);
int      PANTHEON_Demo_CommandSequence(void);
void     PANTHEON_Demo_Close(void);
static const char *s_dumpSnapshots;   /* --dump-snapshots <demo>: decode, no render */
```

Argument (beside `--dump-model`):

```c
        else if (!strcmp(argv[i], "--dump-snapshots") && i + 1 < argc)
            s_dumpSnapshots = argv[++i];
```

Immediately after `Com_Init(cmdline);`, before any GL work:

```c
    if (s_dumpSnapshots) {
        /* G1: one TSV line per valid snapshot, compared against DM73Parser.
         * No GL context is created, so this runs anywhere. */
        snapshot_t snap;
        int num, last = -1;
        if (!PANTHEON_Demo_Open(s_dumpSnapshots)) {
            fprintf(stderr, "PANTHEON: cannot open %s\n", s_dumpSnapshots);
            return 2;
        }
        printf("messageNum\tserverTime\tox\toy\toz\tnumEntities\n");
        while (PANTHEON_Demo_ReadMessage())
            if (PANTHEON_Demo_Latest(&snap, &num) && num != last) {
                printf("%d\t%d\t%.1f\t%.1f\t%.1f\t%d\n", num, snap.serverTime,
                       snap.ps.origin[0], snap.ps.origin[1], snap.ps.origin[2],
                       snap.numEntities);
                last = num;
            }
        PANTHEON_Demo_Close();
        return 0;
    }
```

- [ ] **Step 2: Write the G1 test**

```python
# creative_suite/tests/test_pantheon_demo_feed.py
"""G1: the C demo reader and DM73Parser agree on every snapshot.

Integration test: needs the corpus catalogue and a built pantheon_cgame.exe,
skips cleanly without them. Two independent decoders agreeing is the proof;
neither is trusted alone.
"""
from __future__ import annotations

import csv
import io
import sqlite3
import subprocess
from pathlib import Path

import pytest

from engine.pantheon import store as S
from engine.pantheon.pantheon_capture import host_exe

G1_HASHES = ("4db16c445bcaafce",)   # REAL_ACTION_TRACE_PROOF_01's demo; add two more at execution


def _demo(prefix: str) -> Path:
    if not S.FRAGS_DB.exists():
        pytest.skip("no corpus catalogue")
    con = sqlite3.connect(f"file:{S.FRAGS_DB.as_posix()}?mode=ro", uri=True)
    row = con.execute("select path from demos where content_hash like ? limit 1",
                      (prefix + "%",)).fetchone()
    con.close()
    if not row or not Path(row[0]).exists():
        pytest.skip(f"demo {prefix} not on this machine")
    return Path(row[0])


def _c_snapshots(demo: Path) -> list[dict]:
    if not host_exe().exists():
        pytest.skip("pantheon_cgame.exe not built")
    out = subprocess.run([str(host_exe()), "--dump-snapshots", str(demo)],
                         capture_output=True, text=True, timeout=600, check=True).stdout
    return list(csv.DictReader(io.StringIO(out), delimiter="\t"))


@pytest.mark.parametrize("prefix", G1_HASHES)
def test_c_reader_agrees_with_dm73parser_on_every_snapshot(prefix):
    from engine.parser.demo_parse import DM73Parser
    demo = _demo(prefix)
    py = DM73Parser(demo).parse()["snapshots"]
    c = _c_snapshots(demo)
    by_time = {int(r["serverTime"]): r for r in c}
    assert len(by_time) >= 0.99 * len(py), (len(by_time), len(py))
    bad = []
    for s in py:
        r = by_time.get(int(s["server_time_ms"]))
        if r is None:
            bad.append((s["server_time_ms"], "missing in C"))
            continue
        o = s.get("origin") or (s.get("origin[0]"), s.get("origin[1]"), s.get("origin[2]"))
        if any(abs(float(r[k]) - float(v)) > 0.5 for k, v in zip(("ox", "oy", "oz"), o)):
            bad.append((s["server_time_ms"], "origin", o, (r["ox"], r["oy"], r["oz"])))
    assert not bad, bad[:10]
```

Before running: open `engine/parser/demo_parse.py:1169` (`_read_playerstate`) and confirm the key the snapshot dict uses for origin. Adjust the `o = ...` line to that key; do not guess. If `DM73Parser` records no per-snapshot entity count, compare counts only where it does.

- [ ] **Step 3: Build and run**

Run: `cd engine/pantheon_renderer && ./build_cgame.sh && cd ../.. && E:/PersonalAI/venv/Scripts/python.exe -m pytest creative_suite/tests/test_pantheon_demo_feed.py -q`
Expected: PASS (or SKIP with a stated reason). A FAIL is a decoder bug — stop and fix it before Task 5; every later gate depends on this one.

- [ ] **Step 4: Add two more demos to `G1_HASHES`** (different maps, at least one protocol-91), rerun, expect PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/pantheon_renderer/host/pantheon_frame.c creative_suite/tests/test_pantheon_demo_feed.py
git commit -m "test: G1 -- the C demo reader agrees with DM73Parser"
```

---

### Task 5: Render a demo window from the recorder's eyes

**Files:**
- Modify: `engine/pantheon_renderer/host/pantheon_cg_run.c` (`PANTHEON_CG_Init` signature)
- Modify: `engine/pantheon_renderer/host/pantheon_frame.c` (`--demo`, `--window`, `--fps`, and a demo render loop)

- [ ] **Step 1: Let CG_Init start as the recorder, at a known command sequence**

In `pantheon_cg_run.c` change `PANTHEON_CG_Init(void)` to:

```c
void PANTHEON_CG_Init(int clientNum, int serverCommandSequence)
{
    if (!PANTHEON_CG_Ready())
        Com_Error(ERR_FATAL, "PANTHEON: CG_Init before a gamestate and two "
                             "snapshots were fed");
    dllEntry(PANTHEON_CG_Syscall);
    /* serverMessageNum, serverCommandSequence, clientNum, demoPlayback.
     * Commands at or below serverCommandSequence are treated as already
     * executed -- which is true: they happened before the pre-roll. */
    vmMain(CG_INIT, 1, serverCommandSequence, clientNum, qtrue, 0, 0, 0, 0, 0, 0, 0, 0);
    PANTHEON_CG_RegisterAllWeapons();
}
```

Update the two existing call sites in `pantheon_frame.c` to `PANTHEON_CG_Init(0, 0);` (composed shots keep today's behaviour).

- [ ] **Step 2: Add the arguments**

```c
#define PA_MAX_WINDOWS 64
#define PREROLL_MS     1500
typedef struct { char clip[MAX_QPATH]; int start, end; char outdir[MAX_OSPATH]; } paWindow_t;
static const char *s_demoPath;
static paWindow_t  s_windows[PA_MAX_WINDOWS];
static int         s_numWindows;
static int         s_fps = 60;
```

```c
        else if (!strcmp(argv[i], "--demo") && i + 1 < argc)
            s_demoPath = argv[++i];
        else if (!strcmp(argv[i], "--fps") && i + 1 < argc)
            s_fps = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--window") && i + 4 < argc) {
            paWindow_t *w;
            if (s_numWindows >= PA_MAX_WINDOWS) ShotError("more than %d windows", PA_MAX_WINDOWS);
            w = &s_windows[s_numWindows++];
            Q_strncpyz(w->clip, argv[++i], sizeof(w->clip));
            w->start = atoi(argv[++i]);
            w->end   = atoi(argv[++i]);
            Q_strncpyz(w->outdir, argv[++i], sizeof(w->outdir));
            if (w->end <= w->start) ShotError("window %s ends before it starts", w->clip);
        }
```

`--demo` requires `--map`-free startup: the map comes from the demo's `CS_SERVERINFO`. `--demo` with `--shot` is an error.

- [ ] **Step 3: The demo render path**

Windows must be sorted by `start` (enforce: `ShotError` if not). For each window, in one process (the batching win from `ba8925e4`):

```c
/* Feed until the newest snapshot is AT OR PAST t_ms, so cgame always has a
 * nextSnap beyond the frame being drawn. Returns qfalse at end of demo. */
static qboolean PANTHEON_DemoFeedTo(int t_ms, int *pushed)
{
    snapshot_t snap;
    int num;
    for (;;) {
        if (PANTHEON_Demo_Latest(&snap, &num) && num != *pushed) {
            PANTHEON_CG_PushSnapshot(num, &snap);
            *pushed = num;
            if (snap.serverTime > t_ms) return qtrue;
        }
        if (!PANTHEON_Demo_ReadMessage()) return qfalse;
    }
}
```

Per window:
1. Read messages (without pushing) until the latest snapshot's `serverTime >= start - PREROLL_MS`.
2. `PANTHEON_CG_Reset()`; `PANTHEON_CG_SetGameState(PANTHEON_Demo_GameState())`; push the current snapshot, read to the next one and push it (cgame needs a pair).
3. First window only, inside the registration window: `PANTHEON_CG_Init(PANTHEON_Demo_ClientNum(), PANTHEON_Demo_CommandSequence())` then the existing drains. Later windows: `PANTHEON_CG_Shutdown()` then the same `PANTHEON_CG_Init(...)` (as `--shot` takes do today).
4. Pre-roll: for `t = start - PREROLL_MS` step `1000 / s_fps` to `< start`: `PANTHEON_DemoFeedTo(t)`, `BeginFrame`, clear, `PANTHEON_CG_Frame(t)`, `EndFrame`; **no readback** — this only advances trails, marks and local entities to the state they have at `start`.
5. Capture: frame `k = 0 .. floor((end - start) * s_fps / 1000) - 1` at `t = start + (k * 1000 + s_fps / 2) / s_fps` (integer ms, rounded, monotonic), feed, render, read back through the existing path (blur, depth and offscreen checks all apply), write `outdir/<clip>_<k:06d>.tga`.
6. If the demo ends before `end`: finish the frames that exist, print `PANTHEON: window <clip> short: demo ended at <t>`, and continue to the next window. The Python side reports it (`under_sampled`).

Record at the end: `PANTHEON: window <clip> frames=<n> start=<s> end=<e>` — `pantheon_capture.py` parses these lines.

- [ ] **Step 4: Smoke run on the proof demo**

Run (Git Bash; `$DEMO` from `test_pantheon_demo_feed._demo("4db16c445bcaafce")`):
```bash
engine/pantheon_renderer/build/pantheon_cgame.exe --basepath "$PWD/output/demo_v2/_wolfcam_staging" --game baseq3 --cgame --set cg_draw2D 1 --width 1280 --height 720 --fps 60 --demo "$DEMO" --window proof 1197225 1200725 /tmp/pc_proof
```
Expected: exit 0, `frames=210` (3.5 s × 60), 210 TGAs, 1280×720. Open frames 0, 105, 209: first-person view of client 5 with the HUD — the jump-pad rocket from `REAL_ACTION_TRACE_PROOF_01`. Save three PNGs to `docs/visual-record/<date>/pantheon_demo_window_*.png` (VIS-1).

- [ ] **Step 5: Commit**

```bash
git add engine/pantheon_renderer/host/pantheon_frame.c engine/pantheon_renderer/host/pantheon_cg_run.c docs/visual-record/
git commit -m "feat: PANTHEON renders a demo window from the recorder's eyes"
```

---

### Task 6: Gate G2 — frame parity against wolfcam

**Files:**
- Create: `engine/pantheon/capture_parity.py`
- Modify: `creative_suite/tests/test_pantheon_headless_boundary.py` (classify `capture_parity` as `BACKEND_ALLOWED`)

- [ ] **Step 1: Write the harness**

```python
# engine/pantheon/capture_parity.py
"""G2: the same instants, rendered by wolfcam and by PANTHEON, side by side.

For each frag window: capture with each backend, take frames at the SAME
server times (0 %, 50 %, 100 % of the window), and build one review sheet.
The verdict is a human's; this only makes the question impossible to dodge.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.pantheon import review_sheet, store as S

FFMPEG = S.PROJECT_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
FRACTIONS = (0.0, 0.5, 0.999)


def frame_at(avi: Path, fraction: float, dest: Path) -> Path:
    """Extract the frame at `fraction` of the clip's duration."""
    dur = float(subprocess.run(
        [str(FFMPEG.with_name("ffprobe.exe")), "-v", "error", "-show_entries",
         "format=duration", "-of", "default=nw=1:nk=1", str(avi)],
        capture_output=True, text=True, check=True).stdout.strip())
    subprocess.run([str(FFMPEG), "-y", "-loglevel", "error", "-ss", f"{dur * fraction:.3f}",
                    "-i", str(avi), "-frames:v", "1", str(dest)], check=True)
    return dest


def parity_sheet(clip: str, wolfcam_avi: Path, pantheon_avi: Path, work: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    legs = {}
    for f in FRACTIONS:
        tag = f"{int(f * 100):02d}"
        legs[f"wolfcam {tag}%"] = frame_at(wolfcam_avi, f, work / f"w_{tag}.png")
        legs[f"pantheon {tag}%"] = frame_at(pantheon_avi, f, work / f"p_{tag}.png")
    return review_sheet.compare(
        f"parity_{clip}", "Is this the same moment, from the same eyes, with the same HUD and effects?",
        "renderer", legs, note="G2. PASS only if nothing is missing or wrong in PANTHEON's frames.")


def run(windows_by_demo: dict[str, list[dict]], work: Path) -> list[dict]:
    """Capture every window with both backends and return one sheet per clip."""
    from creative_suite.engine import wolfcam_capture as W
    sheets = []
    for demo, windows in windows_by_demo.items():
        results = {}
        for backend in ("wolfcam", "pantheon"):
            os.environ["PANTHEON_CAPTURE_BACKEND"] = backend
            results[backend] = W.capture_demo(demo, windows)
        for w in windows:
            c = w["clip_name"]
            sheets.append(parity_sheet(c, Path(results["wolfcam"]["avis"][c]),
                                       Path(results["pantheon"]["avis"][c]), work / c))
    os.environ.pop("PANTHEON_CAPTURE_BACKEND", None)
    return sheets
```

This task depends on Task 8 (the dispatch). Build the harness now; run Step 2 after Task 8.

- [ ] **Step 2 (after Task 8): Run on 10 frags** chosen by the user (Gate P-3 analogue: include RL, rail, LG, a multi-kill and one frag on each of three maps). Save the sheets to `docs/visual-record/<date>/`, send them to the user, and record each verdict in `docs/reference/<date>-capture-parity-g2.md` as `clip | verdict | note`.

- [ ] **Step 3: Commit**

```bash
git add engine/pantheon/capture_parity.py creative_suite/tests/test_pantheon_headless_boundary.py
git commit -m "feat: G2 parity sheets -- wolfcam and PANTHEON at the same instants"
```

---

### Task 7: Sound, from cgame's own calls

cgame already decides every sound: which sample, which entity, which channel, where, when. Today `pantheon_cg_syscall.c` counts those calls and drops them. Log them instead, with the listener track, and mix offline.

**Files:**
- Create: `engine/pantheon_renderer/host/pantheon_sound_log.c`
- Modify: `engine/pantheon_renderer/host/pantheon_cg_syscall.c` (sound cases)
- Modify: `engine/pantheon_renderer/host/pantheon_frame.c` (`--sound-log <path>`, listener line per captured frame)
- Modify: `engine/pantheon_renderer/build_cgame.sh`

- [ ] **Step 1: The logger**

```c
/*
 * THE SOUNDS CGAME ASKED FOR, IN ORDER, WITH WHERE AND WHEN.
 *
 * Plays nothing. engine/pantheon/sound_mix.py turns this into a WAV, so the
 * audio is a pure function of the log and the pak samples -- rendering the
 * same moment twice gives the same mix. Lines are tab-separated:
 *   S  <time_ms> <entity> <channel> <sfx> <x> <y> <z>   positional start
 *   L  <time_ms> <sfx> <channel>                          local (UI, announcer)
 *   E  <time_ms> <x> <y> <z> <pitch> <yaw> <roll>         listener, per frame
 *   R  <sfx> <name>                                       registration
 */
#include "../wolfcamql-11.3-src/wolfcamql-src/code/qcommon/q_shared.h"
#include <stdio.h>

#define PS_MAX_SFX 1024
static FILE *s_log;
static int   s_numSfx;
static int   s_time;

void PANTHEON_Sound_Open(const char *path) { s_log = fopen(path, "w"); }
void PANTHEON_Sound_Close(void) { if (s_log) fclose(s_log); s_log = NULL; }
void PANTHEON_Sound_SetTime(int t) { s_time = t; }

/* Handle 0 means "no sound" to cgame, so handles start at 1. */
int PANTHEON_Sound_Register(const char *name)
{
    if (s_numSfx + 1 >= PS_MAX_SFX) return 0;
    s_numSfx++;
    if (s_log) fprintf(s_log, "R\t%d\t%s\n", s_numSfx, name);
    return s_numSfx;
}

void PANTHEON_Sound_Start(const float *origin, int ent, int chan, int sfx)
{
    if (!s_log || sfx <= 0) return;
    if (origin) fprintf(s_log, "S\t%d\t%d\t%d\t%d\t%.1f\t%.1f\t%.1f\n",
                        s_time, ent, chan, sfx, origin[0], origin[1], origin[2]);
    else        fprintf(s_log, "S\t%d\t%d\t%d\t%d\t\t\t\n", s_time, ent, chan, sfx);
}

void PANTHEON_Sound_Local(int sfx, int chan)
{
    if (s_log && sfx > 0) fprintf(s_log, "L\t%d\t%d\t%d\n", s_time, sfx, chan);
}

void PANTHEON_Sound_Listener(const float *o, const float *a)
{
    if (s_log) fprintf(s_log, "E\t%d\t%.1f\t%.1f\t%.1f\t%.2f\t%.2f\t%.2f\n",
                       s_time, o[0], o[1], o[2], a[0], a[1], a[2]);
}
```

Registration happens inside `CG_Init`, before the log path is known to matter; open the log **before** the first `PANTHEON_CG_Init` so every `R` line is captured.

- [ ] **Step 2: Route the syscalls** in `pantheon_cg_syscall.c`:

```c
    case CG_S_REGISTERSOUND:    return PANTHEON_Sound_Register(VMA(1));
    case CG_S_STARTSOUND:       PANTHEON_Sound_Start(VMA(1), args[2], args[3], args[4]); return 0;
    case CG_S_STARTLOCALSOUND:  PANTHEON_Sound_Local(args[1], args[2]); return 0;
```

Remove those three from the counted-and-dropped group; keep the rest counted. `PANTHEON_CG_Frame(t)` calls `PANTHEON_Sound_SetTime(t)` before `vmMain`. Pre-roll frames log too — the mixer discards events before the window start but needs nothing else from them.

- [ ] **Step 3: Listener per captured frame** — after each captured `PANTHEON_CG_Frame`, `PANTHEON_Sound_Listener(snap.ps.origin, snap.ps.viewangles)` from the snapshot fed for that time.

- [ ] **Step 4: Build, smoke, commit**

Run the Task 5 smoke command with `--sound-log /tmp/pc_proof/proof.sound.tsv`.
Expected: the TSV has hundreds of `R` lines, `S` lines for the rocket fire and explosion near the proof's server times, and 210 `E` lines.

```bash
git add engine/pantheon_renderer/host/pantheon_sound_log.c engine/pantheon_renderer/host/pantheon_cg_syscall.c engine/pantheon_renderer/host/pantheon_frame.c engine/pantheon_renderer/build_cgame.sh
git commit -m "feat: PANTHEON logs every sound cgame asks for"
```

---

### Task 8: The backend, the mixer, and the switch

**Files:**
- Create: `engine/pantheon/sound_mix.py`
- Modify: `engine/pantheon/pantheon_capture.py` (full backend)
- Modify: `creative_suite/engine/wolfcam_capture.py` (`capture_demo` head)
- Modify: `engine/pantheon/backends.py`, `creative_suite/tests/test_render_permit.py`, `creative_suite/tests/test_pantheon_headless_boundary.py`
- Test: `creative_suite/tests/test_pantheon_capture.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to creative_suite/tests/test_pantheon_capture.py
import numpy as np


def test_the_default_backend_is_still_wolfcam(monkeypatch):
    from creative_suite.engine import wolfcam_capture as W
    monkeypatch.delenv("PANTHEON_CAPTURE_BACKEND", raising=False)
    assert W.capture_backend() == "wolfcam"


def test_an_unknown_backend_is_refused(monkeypatch):
    import pytest
    from creative_suite.engine import wolfcam_capture as W
    monkeypatch.setenv("PANTHEON_CAPTURE_BACKEND", "blender")
    with pytest.raises(ValueError):
        W.capture_backend()


def test_pantheon_result_has_every_key_wolfcam_returns(tmp_path, monkeypatch):
    from engine.pantheon import pantheon_capture as PC
    windows = [{"clip_name": "c1", "start_ms": 1000, "end_ms": 2000}]
    monkeypatch.setattr(PC, "_run_host", lambda argv, timeout: (0, "PANTHEON: window c1 frames=60 start=1000 end=2000\n"))
    monkeypatch.setattr(PC, "_encode", lambda frames_dir, clip, wav, fps, dest: dest.write_bytes(b"avi") or dest)
    monkeypatch.setattr(PC, "_mix", lambda log, windows, out_dir: {"c1": None})
    r = PC.capture(tmp_path / "d.dm_73", windows, out_dir=tmp_path, fps=60)
    for k in ("ok", "returncode", "elapsed_s", "avis", "frames_expected",
              "frames_written", "capture_fps", "played_too_fast_by",
              "retimed", "under_sampled", "error"):
        assert k in r, k
    assert r["ok"] and r["frames_written"] == 60 and r["frames_expected"] == 60
    assert r["played_too_fast_by"] == 1.0 and r["retimed"] == []


def test_a_short_window_is_reported_under_sampled(tmp_path, monkeypatch):
    from engine.pantheon import pantheon_capture as PC
    windows = [{"clip_name": "c1", "start_ms": 1000, "end_ms": 2000}]
    monkeypatch.setattr(PC, "_run_host", lambda argv, timeout: (0, "PANTHEON: window c1 frames=30 start=1000 end=2000\n"))
    monkeypatch.setattr(PC, "_encode", lambda *a: a[-1])
    monkeypatch.setattr(PC, "_mix", lambda *a: {"c1": None})
    r = PC.capture(tmp_path / "d.dm_73", windows, out_dir=tmp_path, fps=60)
    assert r["under_sampled"] is True


def test_the_mix_places_a_sample_at_its_logged_time(tmp_path):
    from engine.pantheon import sound_mix as M
    sr = 48000
    click = np.zeros(480, dtype=np.float32); click[0] = 1.0
    log = tmp_path / "s.tsv"
    log.write_text("R\t1\tsound/test.wav\nE\t1000\t0\t0\t0\t0\t0\t0\n"
                   "L\t1250\t1\t0\n", encoding="utf-8")
    wav = M.mix(log, start_ms=1000, end_ms=2000, samples={"sound/test.wav": click}, sr=sr)
    first = int(np.argmax(np.abs(wav[:, 0]) > 0.5))
    assert abs(first - int(0.250 * sr)) <= 1
```

- [ ] **Step 2: Run, expect failures** (`capture_backend`, `capture`, `mix` undefined).

- [ ] **Step 3: The mixer**

```python
# engine/pantheon/sound_mix.py
"""Sound log + samples -> stereo float32 PCM for one capture window.

A pure function of its inputs: the same log and the same samples always mix
to the same buffer. Positional sounds use Q3's distance attenuation
(snd_dma.c: SOUND_FULLVOLUME 80, SOUND_ATTENUATE 0.0008) and a pan from the
listener's right vector at the moment the sound starts. Looping sounds are
not mixed in v1 (see the plan's known limits).
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

SOUND_FULLVOLUME = 80.0
SOUND_ATTENUATE = 0.0008


def _right(angles) -> np.ndarray:
    yaw = math.radians(angles[1])
    return np.array([math.sin(yaw), -math.cos(yaw), 0.0])


def _gains(origin, listener) -> tuple[float, float]:
    if origin is None or listener is None:
        return 1.0, 1.0
    o, (lo, la) = np.asarray(origin, float), listener
    d = o - np.asarray(lo, float)
    dist = max(0.0, float(np.linalg.norm(d)) - SOUND_FULLVOLUME)
    vol = max(0.0, 1.0 - dist * SOUND_ATTENUATE)
    n = float(np.linalg.norm(d))
    pan = float(np.dot(d / n, _right(la))) if n > 1e-3 else 0.0
    return vol * (1.0 - max(0.0, pan) * 0.5), vol * (1.0 + min(0.0, pan) * 0.5)


def parse(log: Path):
    names, events, listeners = {}, [], []
    for line in Path(log).read_text(encoding="utf-8").splitlines():
        f = line.split("\t")
        if f[0] == "R":
            names[int(f[1])] = f[2]
        elif f[0] == "S":
            org = None if f[5] == "" else tuple(float(x) for x in f[5:8])
            events.append((int(f[1]), int(f[4]), org))
        elif f[0] == "L":
            events.append((int(f[1]), int(f[2]), None))
        elif f[0] == "E":
            listeners.append((int(f[1]), tuple(map(float, f[2:5])), tuple(map(float, f[5:8]))))
    return names, events, listeners


def mix(log: Path, *, start_ms: int, end_ms: int,
        samples: dict[str, np.ndarray], sr: int = 48000) -> np.ndarray:
    names, events, listeners = parse(log)
    out = np.zeros((int((end_ms - start_ms) * sr / 1000), 2), dtype=np.float32)
    for t, sfx, org in events:
        if t < start_ms or t >= end_ms:
            continue
        pcm = samples.get(names.get(sfx, ""))
        if pcm is None:
            continue
        lst = max((l for l in listeners if l[0] <= t), key=lambda l: l[0], default=None)
        gl, gr = _gains(org, (lst[1], lst[2]) if lst else None)
        i = int((t - start_ms) * sr / 1000)
        n = min(len(pcm), len(out) - i)
        if n > 0:
            out[i:i + n, 0] += pcm[:n] * gl
            out[i:i + n, 1] += pcm[:n] * gr
    return np.clip(out, -1.0, 1.0)
```

Sample loading (in `pantheon_capture._mix`): for every registered name, find it in the staging `baseq3/*.pk3` (zip, read-only — ENG-4), try `.wav` then `.ogg`, decode once with `ffmpeg -i - -f f32le -ac 1 -ar 48000 -` into a cache under `S.store_root() / "sfx_cache"`.

- [ ] **Step 4: The backend** (complete `engine/pantheon/pantheon_capture.py`)

```python
import re
import subprocess
import time

import numpy as np

FFMPEG = S.PROJECT_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
_WINDOW = re.compile(r"PANTHEON: window (\S+) frames=(\d+)")
PER_FRAME_S = 0.08          # measured 2026-09-12: 66 frames in ~4-6 s incl. load
LAUNCH_S = 20.0


def _run_host(argv: list[str], timeout: float) -> tuple[int, str]:
    from creative_suite.engine.capture_guard import quiet_startup_info
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                       cwd=str(host_exe().parent), startupinfo=quiet_startup_info())
    return p.returncode, p.stdout + p.stderr


def _encode(frames_dir: Path, clip: str, wav: Path | None, fps: int, dest: Path) -> Path:
    """Lossless AVI (UT Video) + PCM, so nothing downstream sees a new loss."""
    cmd = [str(FFMPEG), "-y", "-loglevel", "error", "-framerate", str(fps),
           "-i", str(frames_dir / f"{clip}_%06d.tga")]
    if wav:
        cmd += ["-i", str(wav), "-c:a", "pcm_s16le", "-shortest"]
    cmd += ["-c:v", "utvideo", "-pix_fmt", "rgb24", str(dest)]
    subprocess.run(cmd, check=True)
    return dest


def _mix(log: Path, windows: list[dict], out_dir: Path) -> dict[str, Path | None]:
    """See sound_mix. Writes <clip>.wav per window; None when a window has no log."""
    ...   # load samples as described in Step 3, call sound_mix.mix, write 48 kHz s16 WAV


def capture(demo: Path, windows: list[dict], *, out_dir: Path, fps: int,
            staging: Path | None = None, profile_sets: list[str] = ()) -> dict:
    from engine.pantheon import render_permit
    render_permit.require(f"pantheon_capture:{Path(demo).name}")
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = out_dir / "_frames"
    frames_dir.mkdir(exist_ok=True)
    log = out_dir / "sound.tsv"
    ws = sorted(windows, key=lambda w: int(w["start_ms"]))
    argv = [str(host_exe()), "--cgame", "--fps", str(fps), "--demo", str(demo),
            "--sound-log", str(log)]
    if staging:
        argv += ["--basepath", str(staging), "--game", "baseq3"]
    argv += list(profile_sets)
    for w in ws:
        argv += ["--window", w["clip_name"], str(int(w["start_ms"])),
                 str(int(w["end_ms"])), str(frames_dir)]
    want = sum(int((int(w["end_ms"]) - int(w["start_ms"])) * fps / 1000) for w in ws)
    try:
        rc, text = _run_host(argv, timeout=LAUNCH_S + want * PER_FRAME_S * 3)
    except subprocess.TimeoutExpired:
        return {"ok": False, "returncode": None, "elapsed_s": time.time() - t0,
                "avis": {}, "frames_expected": want, "frames_written": 0,
                "capture_fps": 0, "played_too_fast_by": 0.0, "retimed": [],
                "under_sampled": True, "error": "TIMEOUT"}
    got = {m.group(1): int(m.group(2)) for m in _WINDOW.finditer(text)}
    wavs = _mix(log, ws, out_dir) if rc == 0 else {}
    avis = {}
    for w in ws:
        c = w["clip_name"]
        if got.get(c):
            avis[c] = _encode(frames_dir, c, wavs.get(c), fps, out_dir / f"{c}.avi")
    written = sum(got.values())
    return {"ok": rc == 0 and len(avis) == len(ws), "returncode": rc,
            "elapsed_s": time.time() - t0, "avis": avis,
            "frames_expected": want, "frames_written": written,
            # Frames are rendered at exact server times, never against a wall
            # clock, so the declared rate IS the true rate: nothing to retime.
            "capture_fps": float(fps) if written else 0,
            "played_too_fast_by": 1.0 if written else 0.0, "retimed": [],
            "under_sampled": want > 0 and written < want,
            "error": None if rc == 0 and len(avis) == len(ws)
            else (text.strip().splitlines() or ["no output"])[-1]}
```

- [ ] **Step 5: The switch** — at the top of `creative_suite/engine/wolfcam_capture.py` add:

```python
BACKENDS = ("wolfcam", "pantheon")


def capture_backend() -> str:
    """One setting, two backends. Default wolfcam until G1-G4 pass and the
    user signs off (docs/superpowers/plans/2026-09-12-pantheon-production-capture.md)."""
    b = os.getenv("PANTHEON_CAPTURE_BACKEND", "wolfcam").strip().lower()
    if b not in BACKENDS:
        raise ValueError(f"PANTHEON_CAPTURE_BACKEND={b!r}; expected one of {BACKENDS}")
    return b
```

and as the first statement of `capture_demo`:

```python
    if capture_backend() == "pantheon" and not os.getenv("CS_CAPTURE_MOCK"):
        from engine.pantheon import pantheon_capture as PC
        videos = staging / "wolfcam-ql" / "videos"
        return PC.capture(staging / "wolfcam-ql" / "demos" / safe_demo, windows,
                          out_dir=videos, fps=profile_fps(profile), staging=staging)
```

The AVIs land in the same `videos` directory, so `publish_avi` and every caller are unchanged. (Profile cvars: pass the profile's `cg_draw*` sets through `profile_sets` in a follow-up once G2 shows which ones matter.)

- [ ] **Step 6: Register and classify**

`engine/pantheon/backends.py`: add a `PantheonNative` class with `name = "PANTHEON_NATIVE"`, `supports = frozenset({BackendUse.REFERENCE_RENDER, BackendUse.FINAL_QUAKE_BEAUTY})`, whose `render` raises `NotImplementedError("ShotSpec rendering goes through --shot; production demo capture goes through pantheon_capture.capture")`, and add it to `BACKENDS`.
`test_render_permit.py`: add `"engine/pantheon/pantheon_capture.py"` to `LAUNCH_SITES`.
`test_pantheon_headless_boundary.py`: add `"pantheon_capture"` and `"sound_mix"` to `BACKEND_ALLOWED` with one-line reasons.

- [ ] **Step 7: Run everything touched**

Run: `E:/PersonalAI/venv/Scripts/python.exe -m pytest creative_suite/tests/test_pantheon_capture.py creative_suite/tests/test_render_permit.py creative_suite/tests/test_pantheon_headless_boundary.py -q`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add engine/pantheon/sound_mix.py engine/pantheon/pantheon_capture.py engine/pantheon/backends.py creative_suite/engine/wolfcam_capture.py creative_suite/tests/test_pantheon_capture.py creative_suite/tests/test_render_permit.py creative_suite/tests/test_pantheon_headless_boundary.py
git commit -m "feat: PANTHEON_NATIVE capture backend behind PANTHEON_CAPTURE_BACKEND"
```

Now run Task 6 Step 2 (G2).

---

### Task 9: Gate G3 — audio parity

**Files:**
- Modify: `engine/pantheon/capture_parity.py`

- [ ] **Step 1: Add the measurement**

```python
def envelope(avi: Path, sr: int = 8000) -> "np.ndarray":
    import numpy as np
    raw = subprocess.run([str(FFMPEG), "-loglevel", "error", "-i", str(avi), "-vn",
                          "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.abs(np.frombuffer(raw, dtype=np.float32))
    k = sr // 100                                   # 10 ms windows
    return x[: len(x) // k * k].reshape(-1, k).mean(axis=1)


def audio_lag_ms(wolfcam_avi: Path, pantheon_avi: Path) -> tuple[float, float]:
    """(lag in ms, peak normalised correlation) of the two 10 ms envelopes."""
    import numpy as np
    a, b = envelope(wolfcam_avi), envelope(pantheon_avi)
    n = min(len(a), len(b))
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    c = np.correlate(a, b, mode="full")
    i = int(np.argmax(c))
    denom = float(np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return (i - (n - 1)) * 10.0, float(c[i]) / denom
```

- [ ] **Step 2: Run on the G2 frags.** Pass per clip: `|lag| <= 40` and `corr >= 0.6`. Record results in the G2 document. A consistent non-zero lag across all clips is a pipeline offset (fix it once); scattered failures are missing sounds (inspect the `S` lines for that clip).

- [ ] **Step 3: Commit**

```bash
git add engine/pantheon/capture_parity.py docs/reference/
git commit -m "test: G3 -- PANTHEON audio lands where wolfcam's does"
```

---

### Task 10: Linear-light accumulation

Averaging display-encoded values darkens edges and mid-tones. The frame is decoded to linear light, averaged, then re-encoded. **The same resolve is required of `codex/capture-supersampling` before it merges** — record that on the branch.

The framebuffer is not clean sRGB: `r_gamma` is baked into textures at upload and overbright is disabled on this host. sRGB is used as the standard decode; Step 3 measures whether it is good enough.

**Files:**
- Modify: `engine/pantheon_renderer/host/pantheon_frame.c` (`PANTHEON_BlurAccumulate`, `PANTHEON_BlurResolve`, the accumulator type)

- [ ] **Step 1: Replace the accumulator**

```c
/* sRGB <-> linear, by table. Averaging ENCODED values averages numbers, not
 * light: a half-covered edge between 255 and 0 averages to 128, which is 22 %
 * of the light, not 50 %. That is the dark fringe. */
static float s_toLinear[256];
static byte  s_toSrgb[4097];

static void PANTHEON_LinearTables(void)
{
    int i;
    for (i = 0; i < 256; i++) {
        float c = i / 255.0f;
        s_toLinear[i] = c <= 0.04045f ? c / 12.92f : powf((c + 0.055f) / 1.055f, 2.4f);
    }
    for (i = 0; i <= 4096; i++) {
        float l = i / 4096.0f, c = l <= 0.0031308f ? l * 12.92f
                                   : 1.055f * powf(l, 1.0f / 2.4f) - 0.055f;
        s_toSrgb[i] = (byte)(c * 255.0f + 0.5f);
    }
}

static void PANTHEON_BlurAccumulate(float *acc, const byte *rgb, int n)
{
    int i;
    for (i = 0; i < n; i++) acc[i] += s_toLinear[rgb[i]];
}

static void PANTHEON_BlurResolve(byte *rgb, const float *acc, int n, int samples)
{
    int i;
    for (i = 0; i < n; i++) {
        float l = acc[i] / samples;
        rgb[i] = s_toSrgb[(int)(l * 4096.0f + 0.5f)];
    }
}
```

Change `unsigned *blurAccum` to `float *blurAccum` (allocation `calloc(np * 3, sizeof(float))`, reset `memset(..., sizeof(float))`), and call `PANTHEON_LinearTables()` once at startup. Add `#include <math.h>`.

- [ ] **Step 2: Prove the identity case is untouched** — `--blur 8 --shutter 0` against `--blur 1` on the Task 5 window: must differ by no more than the known 0.038 % per-call effect region (see `docs/reference/2026-09-08-engine-comparison-and-improvement-scan.md` §6.5) plus ±1 rounding.

- [ ] **Step 3: Measure the fringe fix** — render the Task 5 window at `--blur 8 --shutter 0.7` before and after; build a review sheet cropped on a bright-on-dark moving edge (the rocket's light against the ceiling). The after-leg must not show a dark halo. Save to the visual record.

- [ ] **Step 4: Commit**

```bash
git add engine/pantheon_renderer/host/pantheon_frame.c docs/visual-record/
git commit -m "fix: motion blur averages light, not encoded values"
```

---

### Task 11: Measure whether HDR exists before building it

**This task changes no production behaviour.** It answers one question: do values above 1.0 survive this renderer before the final clamp? If they do not, an FP16 target and EXR output would store 0–1 data in a larger file, and no HDR plan is written.

**Files:**
- Modify (probe only, behind `--probe-hdr`): `wolfcamql-11.3-src/.../renderer/tr_init.c` (scene texture internal format), `host/pantheon_frame.c`
- Create: `docs/reference/<date>-hdr-survival-probe.md`

- [ ] **Step 1: Read, and write down, every clamp on the path** — before any code. At minimum: texture upload (`R_LightScaleTexture`, 8-bit `GL_RGB8`/`GL_RGBA8` internal formats), lightmaps (`R_ColorShiftLightingBytes` in `tr_bsp.c` clamps to 255), vertex colours (bytes), `tr.overbrightBits`/`r_mapOverBrightBits` (disabled on a host with no hardware gamma), shader stage blending into an 8-bit target. List each with file:line in the doc.

- [ ] **Step 2: The probe** — with `--probe-hdr`, create the FBO scene texture as `GL_RGBA16F` instead of `GL_RGB8` (`InitFrameBufferAndRenderBuffer`, `tr_init.c`), render the Task 5 window's frames at 0 %, 50 %, 100 %, read back with `glReadPixels(..., GL_RGB, GL_FLOAT, ...)`, and report per frame: max channel value, and the fraction of pixels with any channel > 1.0.

- [ ] **Step 3: Record the result and the decision**

| Result | Meaning | Decision |
|---|---|---|
| Max ≤ 1.0 on every frame | The range is gone before the target: 8-bit inputs, clamped lightmaps | No FP target, no EXR. An HDR plan must start with lighting and texture inputs, not the framebuffer. |
| Values > 1.0 only in additive effects (explosions, flares) | Some range survives, in blending | A narrow FP16 plan is defensible; scope it to effects. |
| Broad values > 1.0 | Real HDR survives | Write the HDR/EXR plan. |

- [ ] **Step 4: Revert the probe code** unless the decision is "write the HDR plan"; commit the doc either way.

```bash
git add docs/reference/
git commit -m "docs: HDR survival probe -- does range exist before the clamp?"
```

---

### Task 12: Cutover (only with the user's explicit go)

**Precondition:** G1, G2 (all ten human PASS), G3 and G4 recorded as passing in `docs/reference/<date>-capture-parity-g2.md`, the full suite at or better than the Task 0 baseline, and the user says go in chat.

**Files:**
- Modify: `creative_suite/engine/wolfcam_capture.py` (`capture_backend` default)
- Modify: `CLAUDE.md` (HL-2: add PANTHEON_NATIVE as the production renderer; wolfcam's four jobs stand as the oracle's)

- [ ] **Step 1:** Change the default in `capture_backend()` from `"wolfcam"` to `"pantheon"`; update `test_the_default_backend_is_still_wolfcam` to `test_the_default_backend_is_pantheon`.
- [ ] **Step 2:** Run the full suite; compare against the baseline file. Expected: no new failures.
- [ ] **Step 3:** Capture one real frag end to end through the normal pipeline (the mining session's command, not a harness). ffprobe the AVI: duration, frame count, audio stream present. Extract one frame to the visual record.
- [ ] **Step 4:** Commit and push.

```bash
git add creative_suite/engine/wolfcam_capture.py creative_suite/tests/test_pantheon_capture.py CLAUDE.md docs/visual-record/
git commit -m "feat: PANTHEON is the production renderer; wolfcam is the oracle"
git push origin feature/pantheon-production-capture
```

Rollback is one line: `PANTHEON_CAPTURE_BACKEND=wolfcam`.

---

## Explicitly not in this plan

- Windowless GL context (EGL/pbuffer): only if the renderer must run as a service or without an interactive desktop.
- FP16 targets, EXR masters, tonemapping: gated by Task 11.
- Merging `codex/capture-supersampling`: gated by Task 10's resolve being adopted there.
- rend2, Vulkan, IQM, OpenAL Soft, FX-script authoring, texture/asset work.
- Free-camera (FL) angles from demos: PANTHEON renders the recorder's eyes first; FL comes after G2 proves FP parity.
