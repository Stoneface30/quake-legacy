# Phase 2 Architecture: WolfcamQL Kill-Query API

**Discovery date:** 2026-04-16  
**Status:** GAME CHANGER — no binary .dm_73 parsing needed

---

## The Core Insight

WolfcamQL has a **built-in frag database** populated during demo playback.
It exposes this database through dedicated syscalls that cgame mods can call.

This means Phase 2 does NOT need to:
- Parse raw .dm_73 binary format
- Implement Huffman codec
- Use UberDemoTools as a dependency

Instead Phase 2 needs:
- A WolfcamQL cgame extension script (~100 lines of C)
- Call the kill-query syscalls to enumerate all frags
- Export timestamps as JSON + schedule auto-recording with `trap_AddAt`

---

## Key Data Structs (from cg_public.h)

### demoObit_t — The Frag Record
```c
typedef struct {
    int firstServerTime;  // server time (ms) when kill occurred
    int firstMessageNum;  // network message number
    int lastServerTime;   // last time this obit was seen
    int lastMessageNum;
    int number;           // sequence number (0-based index)
    int killer;           // killer client slot (0-63)
    int victim;           // victim client slot (0-63)
    int mod;              // MOD_* weapon constant (see below)
} demoObit_t;

#define MAX_DEMO_OBITS (1024 * 2)  // up to 2048 kills tracked per demo
```

### obituary_t — The Display Record (cg_local.h:851)
```c
typedef struct {
    char killer[MAX_STRING_CHARS];        // killer display name
    char killerWhiteName[MAX_STRING_CHARS];
    int  killerClientNum;
    int  killerTeam;
    char victim[MAX_STRING_CHARS];        // victim display name
    char victimWhiteName[MAX_STRING_CHARS];
    int  victimClientNum;
    int  victimTeam;
    int  weapon;                          // MOD_* constant
    qhandle_t icon;
    int  time;                            // server time ms
    char q3obitString[MAX_STRING_CHARS];
} obituary_t;
```

### itemPickup_t — Item Pickup Record (cg_public.h)
```c
typedef struct {
    int      clientNum;    // who picked it up
    int      index;        // item type index (MH, RA, YA, etc.)
    vec3_t   origin;       // world position
    int      pickupTime;   // server time ms
    int      specPickupTime;
    int      number;       // sequence number
    qboolean spec;
} itemPickup_t;

#define MAX_ITEM_PICKUPS (1024 * 4)  // up to 4096 item pickups tracked
```

### timeOut_t — Timeout/Timein Record (cg_public.h)
```c
typedef struct {
    int startTime;    // server time ms when timeout started
    int endTime;      // server time ms when timeout ended
    int serverTime;   // time the timeout/timein command was issued
} timeOut_t;

#define MAX_TIMEOUTS 256
#define MAX_DEMO_ROUND_STARTS 256
```

---

## Kill-Query Syscall API (cg_syscalls.h)

### Core Kill Enumeration

```c
// Get next kill where 'us' is the KILLER, starting from serverTime
// Returns qtrue if found. Outputs: killer client slot, exact kill time.
qboolean trap_GetNextKiller(
    int  us,                // target client slot (the killer)
    int  serverTime,        // start searching from this time (ms)
    int  *killer,           // OUTPUT: killer client slot
    int  *foundServerTime,  // OUTPUT: exact server time of kill (ms)
    qboolean onlyOtherClient  // if true, skip self-kills
);

// Get next kill where 'us' is the VICTIM, starting from serverTime
qboolean trap_GetNextVictim(
    int  us,                // target client slot (the victim)
    int  serverTime,
    int  *victim,           // OUTPUT: victim client slot
    int  *foundServerTime,
    qboolean onlyOtherClient
);
```

### Time Boundaries

```c
int trap_GetGameStartTime(void);    // warmup end / match start (ms)
int trap_GetGameEndTime(void);      // match end (ms)
int trap_GetFirstServerTime(void);  // first snapshot time (ms)
int trap_GetLastServerTime(void);   // last snapshot time (ms)
```

### CA-Specific

```c
// Get all round start times (critical for Clan Arena fragmovies)
void trap_GetRoundStartTimes(int *numRoundStarts, int *roundStarts);

// Returns true if client switched teams at/after startTime
qboolean trap_GetTeamSwitchTime(int clientNum, int startTime, int *teamSwitchTime);
```

### Item Pickups (MH/armor timing)

```c
// Get pickup sequence number for items at/after pickupTime
int  trap_GetItemPickupNumber(int pickupTime);

// Get pickup details by sequence number. Returns -1 if no more.
int  trap_GetItemPickup(int pickupNumber, itemPickup_t *ip);
```

### Timeout Detection

```c
// Get all timeouts in the demo
void trap_Get_Demo_Timeouts(int *numTimeouts, timeOut_t *timeOuts);
```

### At-Time Command Scheduling

```c
// Schedule a wolfcamQL console command to fire at exact server time
// clockTime: HH:MM:SS format string (can be NULL)
// command: any wolfcamQL console command
void trap_AddAt(int serverTime, const char *clockTime, const char *command);
```

---

## The Frag Enumeration Pattern

This is the core Phase 2 loop — enumerate ALL kills in a demo:

```c
void Phase2_ExtractAllFrags(int targetClient) {
    int serverTime = trap_GetFirstServerTime();
    int killerClientNum, killTime;
    int fragIndex = 0;
    
    while (trap_GetNextKiller(targetClient, serverTime, &killerClientNum, &killTime, qfalse)) {
        // Record this frag
        frags[fragIndex].time = killTime;
        frags[fragIndex].killer = targetClient;
        frags[fragIndex].killerName = cgs.clientinfo[targetClient].name;
        
        // Advance past this kill to find the next one
        serverTime = killTime + 1;
        fragIndex++;
        
        if (fragIndex >= MAX_FRAGS) break;
    }
}
```

### Usage in actual wolfcamQL source (cg_snapshot.c:1268):
```c
// Check if player is alive this round (CA scoreboard)
if (trap_GetNextKiller(i, roundStartTime, &killerClientNum, &killTime, qfalse)) {
    if (killTime <= cg.time) {
        wclients[i].aliveThisRound = qfalse;
    }
}
```

---

## Phase 2 Architecture: Auto-Highlight Extractor

### Step 1: Enumerate all frags for target player

```c
// In a wolfcamQL cgame extension (C code):
int gameStart = trap_GetGameStartTime();
int serverTime = gameStart;
int killer, killTime;

while (trap_GetNextKiller(TARGET_CLIENT, serverTime, &killer, &killTime, qfalse)) {
    // Output: JSON line with kill metadata
    trap_Cvar_Set("phase2_json_out", va("{ \"time\": %d, \"killer\": %d }", killTime, killer));
    serverTime = killTime + 1;
}
```

### Step 2: Schedule auto-recording with trap_AddAt

```c
// For each kill at timestamp T:
//   - Start capture 8 seconds BEFORE the kill (approach, setup, game context)
//   - Stop capture 5 seconds AFTER the kill (aftermath, reaction, death cam)
//
// CRITICAL LESSON (confirmed from v1 clip review):
//   The original 3s pre / 2s post windows were too SHORT.
//   Action started before capture began. Kill aftermath cut off mid-animation.
//   Clips must have generous margins — editors trim down, they cannot add frames.
//
// Pre-roll 8s: enough for the attack sequence, movement, aim phase
// Post-roll 5s: death animation, corpse, CA round consequence
int captureStart = killTime - 8000;  // 8s before — generous pre-roll
int captureEnd   = killTime + 5000;  // 5s after  — full aftermath

trap_AddAt(captureStart, NULL, va("video avi name :frag_%03d", fragIndex));
trap_AddAt(captureEnd,   NULL, "video avi stop");
```

### Step 3: CA round boundary clipping

```c
int numRounds;
int roundStarts[MAX_DEMO_ROUND_STARTS];
trap_GetRoundStartTimes(&numRounds, roundStarts);

// Find which round this kill belongs to
for (int r = 0; r < numRounds; r++) {
    if (killTime >= roundStarts[r] && (r == numRounds-1 || killTime < roundStarts[r+1])) {
        fragData.roundNumber = r + 1;
        fragData.roundStartTime = roundStarts[r];
        fragData.timeIntoRound = killTime - roundStarts[r];
        break;
    }
}
```

---

## MOD_* Weapon Constants

From wolfcam/game/bg_public.h (Phase 2 must map these to weapon names):

| MOD constant | Weapon | Phase 2 priority |
|---|---|---|
| MOD_ROCKET | Rocket Launcher | HIGH (airshots) |
| MOD_ROCKET_SPLASH | Rocket (splash) | HIGH |
| MOD_RAILGUN | Railgun | HIGH (instant-kill aesthetic) |
| MOD_LIGHTNING | Lightning Gun (shaft) | HIGH (CA specialist weapon) |
| MOD_PLASMA | Plasma Gun | MED |
| MOD_GRENADE | Grenade Launcher | MED (airshots) |
| MOD_GRENADE_SPLASH | Grenade (splash) | MED |
| MOD_BFG | BFG | LOW |
| MOD_TELEFRAG | Telefrag | HIGH (cinematics) |
| MOD_FALLING | Falling | LOW |

---

## Highlight Scoring Formula (Gate P3-0 inputs)

Once kills are enumerated via kill-query API, Phase 3 scores them:

```
frag_score = weapon_weight[mod]
           + 0.2 * is_airshot(killTime, targetClient, killerPos, victimPos)
           + 0.3 * multi_kill_bonus(killTime, window=3000ms)
           + 0.1 * low_health_attacker(killTime)
           + 0.4 * ca_ca_bonus(roundNumber, numKillsInRound)
```

The **airshot detection** requires checking victim height above ground at killTime
→ `trap_GetSnapshot(snapNum)` + entity position from snapshot

---

## Implementation Path

Phase 2 requires building a **wolfcamQL cgame plugin** (not a Python script):

1. Add new console command to `wolfcam_consolecmds.c`:
   `wolfcam_extract_frags <clientNum>` → calls kill-query API → writes JSON

2. Or: use the `trap_AddAt` system with a `.cfg` script that:
   - Seeks to game start
   - Calls the extraction command
   - Reads output from a cvar

3. Python wrapper (`phase2/extract_frags.py`) launches WolfcamQL with the
   custom config, waits for completion, reads output JSON

**Estimated LOC:** ~200 C (cgame extension) + ~150 Python (launcher/parser)

---

## Files to Modify for Phase 2

| File | Change |
|---|---|
| `wolfcam_consolecmds.c` | Add `wolfcam_extract_frags` command |
| `wolfcam_consolecmds.h` | Export new command |
| `cg_syscalls.h` | Already has all needed syscalls |
| NEW: `phase2/extract_frags.py` | Python launcher + JSON parser |
| NEW: `phase2/frag_scorer.py` | Phase 3-0 scoring formula |
| NEW: `database/frags.db` | SQLite frag database (schema TBD) |
