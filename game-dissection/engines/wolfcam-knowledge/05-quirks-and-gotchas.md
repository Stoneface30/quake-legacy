# 05 — Quirks & Gotchas (wolfcamql)

Surprising behavior discovered in wolfcamql source. Selective list — 200
FIXMEs is noise, these are the ones that change how you write automation or
port code. Each entry: what it is, why it matters, where to find it.

---

## Platform-specific code paths

### Windows client: stdin is UNUSABLE for IPC
**File:** `code/sys/sys_win32.c:922-928`
**Behavior:** In non-DEDICATED (client) builds on Windows, `Sys_Sleep()`
falls through to a plain `Sleep(msec)` and refuses negative-msec blocking.
Source literally says `// Client Sys_Sleep doesn't support waiting on stdin`.
Dedicated-server builds use `WaitForSingleObject(GetStdHandle(
STD_INPUT_HANDLE), ...)` at lines 917-921, but wolfcamql ships client.
**Why it matters:** No pipe-to-stdin automation on Windows. Any external
controller must drive via command-line args + cfg files (see 03-ipc-commands).

### Windows: console auto-attach to parent process, with a twist
**File:** `code/sys/sys_win32.c:1050-1056`
**Behavior:** On launch, wolfcamql calls `AttachConsole(ATTACH_PARENT_PROCESS)`
and `freopen`s stdin/stdout/stderr to `conin$`/`conout$`. If launched from a
terminal (or the Python batch scripts), wolfcam prints to that parent
console. If double-clicked it allocates its own.
**Why it matters:** Headless automation can capture wolfcam stderr/stdout by
creating the child process with inherited pipes — the wolfcamql side will
cooperate. This is the ONLY observation channel for a batch driver short of
polling disk for the output AVI.

### Linux/macOS: `vid_restart` makes playback choppy
**File:** FIXME line 39 — *"vid_restart makes playback choppy -- sdl linux
only certain modes"*
**Why it matters:** Any port trying to change resolution mid-session on
Linux is walking into a known regression. Pre-set `r_mode`/`r_customwidth`
on the command line, never via mid-run `vid_restart`.

### altivec cvar defaults ON even on non-PowerPC
**File:** `code/qcommon/common.c:3076` — `com_altivec = Cvar_Get(...,"1",...)`;
`common.c:2904-2913` — runtime check, disables with log if CPU lacks altivec.
**Why it matters:** On first launch the cvar is persisted as `1` to
q3config. A user migrating the cfg to a fresh install on an Apple Silicon /
ARM / x86 box will see "Altivec support is disabled" once; harmless noise
but confusing. Scrub altivec from any shipped default cfg.

### Windows 64-bit required `-D_FILE_OFFSET_BITS=64`
**Source:** `CREDITS-wolfcam.txt:23` em92 fix
**Why it matters:** Pre-fix, AVI files > 2 GB silently corrupted on Windows
builds. If you rebuild from an older wolfcam-src checkout, verify this
compile flag survives. `cl_aviAllowLargeFiles` cvar exists to work around
but is gated on this flag.

---

## Hardcoded limits

| Symbol | Value | Defined at | Why it matters |
|--------|-------|------------|----------------|
| `MAX_CLIENTS` | 64 | `qcommon/q_shared.h:1179` | "absolute limit" — 64 slots, `clientNum` in events is 0..63. QL demos with >64 player slots would corrupt. |
| `MAX_GENTITIES` | 1024 (1<<10 GENTITYNUM_BITS) | `q_shared.h:1183` | Entity IDs 0..1023. Freecam crash workaround *forces* `MAX_GENTITIES-1` (=1023) when encountering bad entitynum -1 (see FIXME line 37 "freecam crash loop bad entitynum -1"). Ghost-entity artifact risk. |
| `ENTITYNUM_NONE` | 1023 | `q_shared.h:1188` | Same slot as the freecam-crash-workaround uses. Confusion-prone. |
| `ENTITYNUM_WORLD` | 1022 | `q_shared.h:1189` | Reserved; do not collide. |
| `MAX_CONFIGSTRINGS` | 1024 | `q_shared.h:1198` | Total game config-string slots. QL pushes this with sv_altEntDir + bots; dm_73 parsing that exceeds will corrupt. |
| `MAX_MSGLEN` | 32768 (16384 * 2) | `qcommon.h:176` | Max single message length. Wolfcam doubled from stock 16384 to handle QL's larger snapshots. If porting another engine, match this. |
| `MAX_QPATH` | 64 | `q_shared.h:276` | Game-path filename limit. Longer demo paths get truncated silently. |
| `MAX_OSPATH` | 256 (win32) / PATH_MAX (posix) | `q_shared.h:278-280` | Asymmetric across platforms — a path that works on Linux can overflow on Windows. |
| `MAX_SAY_TEXT` | 150 | `q_shared.h:286` | Chat line limit, relevant if scraping chat for automation triggers. |
| `MAX_AT_COMMANDS` | queue depth for `at` | `cg_consolecmds.c:6838` (loop bound) | The deferred-command scheduler is a fixed-size ring — over-queueing silently drops commands. Matters for long batch renders with many timed cuts. |
| `r_fboAntiAlias` cap | note *"MSAA"* in cfg | observed default `4` in q3config | Higher values may silently cap; verify against `glconfig`. FIXME line 97: *"ResampleTexture and scale uses 2048 get from glconfig"* — hardcoded 2048 for texture scaling even if GPU supports more. |
| FreeType "giant/big/small/tiny" font data | missing | FIXME line 9 | These sizes have no backing font data; falls back to default. Custom title-card fonts at these slots will render wrong. |
| opengl2 `animmap` limit | was 8, patched to 2048 | `CREDITS-wolfcam.txt:31` em92 fix | Stock ioq3 opengl2 renderer caps at 8 animmap frames. Shaders with more (QL weapons) break silently on older wolfcam builds. |
| `ri.Printf` buffer | 1024 chars | `renderergl1/tr_init.c:1615`, `renderergl2/tr_init.c:1714` | Printf calls truncate silently at 1024 chars — both renderers have an explicit workaround noting this. |

---

## QuakeLive / minqlx server-bug workarounds baked into wolfcam

These are not wolfcam bugs — they are wolfcam compensating for QL server bugs.
Porting code that talks to live QL must know about them.

1. **Config-string team updates are unreliable (minqlx bug).** When QL or
   minqlx does not update player config strings correctly after a team
   change, wolfcam falls back to **scraping scoreboard score entries** for
   team membership.
   - `cgame/cg_servercmds.c:4453` (`//FIXME 2017-06-03 ql/minqlx config
     string fix needed?`)
   - `cgame/cg_servercmds.c:4614, 4749, 5036, 5394` — "hack to grab them
     from scores"
   - `cgame/cg_players.c:6850` "hack for ql/minqlx bug that doesn't update
     configs strings correctly. Spectator team might not be valid."
   **Impact on dm_73 parser:** do NOT trust team membership from configstrings
   alone during live games — cross-check with scoreboard state.

2. **QL sends `20/40/60/80` instead of real health values in protocol 90+.**
   Health is quantized server-side.
   - `cgame/cg_draw.c:3411`, `cg_event.c:1096`, `cg_newdraw.c:885, 1659`,
     `game/g_team.c:1136`
   **Impact:** any damage-calculation logic off health delta is WRONG on
   protocol 90/91 demos. Only `dm_73` (older QL) has real health.

3. **QL widescreen stretching bug (`cg_wideScreen == 7`).** ~40 sites
   explicitly branch on `cg_wideScreen.integer == 7` for "ql bug
   compatibility." This is deliberately preserving a QL visual bug.
   - `cg_newdraw.c` lines 4472, 5264, 8036, 8048, 8056, 8063, 8070, 8164,
     8283, 8455, 8469, 8479, 8597, 8623, 9312, 9336, 9357, 9374, 9381,
     9410, 9436, 9462, 9470, 9554, 9577, 9598, 9614, 9621, 9649, 9675,
     9700, 9708, 9939.
   **Impact:** Pixel-accurate HUD reproduction requires this whole block
   preserved in any fork. Dropping "compat" branches will silently shift
   HUD elements.

4. **QL sometimes starts sending different scores structure (minqlx?).**
   `cgame/cg_servercmds.c:6038` — *"2016-08-05 might be a ql or minqlx
   bug, sometimes server starts sending this instead of ca scores."*
   Wolfcam parses both shapes. Any CA scoreboard scraping must handle both.

5. **QL 1FCTF might itself be a QL bug.** FIXME-in-code at
   `cg_newdraw.c:8602` — *"2018-07-17 is GT_1FCTF a ql bug?"*. Gametype 9
   (1FCTF) handling is defensive.

6. **QL protocol 43 is a different universe.** Scattered `// protocol 43
   doesn't have this` comments show many packet fields are absent in the
   oldest QL demos:
   - `cl_cgame.c:414`, `cl_main.c:853, 1073, 2454, 3015`, `cl_parse.c:2104,
     2137, 2257`, `cg_event.c:1321, 1339`
   **Impact on parser:** a dm_73 that is actually protocol 43 (pre-2010 QL)
   has fewer fields. Detect protocol FIRST, branch parse logic.

7. **Protocol 91 QCON demos have no team-name configstring.**
   `cg_servercmds.c:1686` — *"2015-08-13 qcon protocol 91 demos don't have
   cs for team name."* Parser must synthesize a default.

8. **Older dm_73 may have empty string where newer has data.**
   `cg_servercmds.c:2714` — *"older ql demos dm_73"* has str[0] == '\0'.
   Empty-string sentinel means "field not sent" not "field empty."

---

## Undocumented-but-load-bearing wolfcam features

### `fs_homepath` override is the only clean way to isolate batch renders
**File:** `qcommon/files.c:3638-3645`, `4456`, `4477`
**Behavior:** If `fs_homepath` is set on the command line (via
`Com_StartupVariable`), it overrides every other path logic — data,
config, and state all redirect to it.
**Why it matters:** Documented only as a TODO in FIXME:101 (*"doc
fs_homepath"*). The entire batch-rendering strategy relies on this — give
each render job a unique `fs_homepath` and AVIs land in predictable
per-job directories without polluting the user's wolfcam install.

### `nextdemo` is NOT "the next demo to play"
**File:** `client/cl_main.c:3406-3419`
**Behavior:** Despite the name, `nextdemo` is a **console command string**
executed at demo-end, not a filename. `playdemolist.py:34-36` documents
this trap directly: *"This isn't the name of the next demo to play it is
the command to execute after a demo has completed."*
**Why it matters:** Classic footgun. Anyone grepping "nextdemo" expecting
a demo-chain feature gets confused.

### `cg_enableAtCommands` is ON by default but scoped to cgame
**File:** `cgame/cg_main.c:2460` (CVAR_ARCHIVE, default `"1"`);
executor `cgame/cg_view.c:5273 CG_CheckAtCommands()`, called from
`cg_view.c:5813`.
**Why it matters:** The `at` command is the backbone of every batch
automation recipe. If anyone ships a cfg that sets
`cg_enableAtCommands 0`, ALL queued commands silently no-op. Check on
session start.

### `compiler bug workaround` static storage for `demoName`
**File:** `client/cl_main.c:761` — `static char demoName[MAX_QPATH]; //
compiler bug workaround`
**Why it matters:** Undocumented which compiler. Moving this to stack
locals may miscompile on some MinGW versions. Leave it alone when porting.

### Packet buffer: snap interpolation is fragile at low timescale
**FIXME:209** — *"devmap and low timescale CL_GetSnapshot cl.snap.messageNum
- snapshotNumber >= PACKET_BACKUP"*
**FIXME:226** — *"timescale 0.001 seeking caused players to teleport to
positions -- need to clear wcsnapshots ?"*
**Why it matters:** If the automation pipeline uses `timescale 0.1`
extensively for slow-mo captures combined with `seekclock`, expect
occasional teleport artifacts. Avoid `timescale < 0.1` during seeks; set
timescale AFTER seeking completes.

### `fragforward` is broken by seeking
**FIXME:314** — *"fragforward broken by seeking."*
**Why it matters:** Do not combine `fragforward` mode with `seekclock` in
the same automation session. Either-or.

### `vid_restart` after demo load may desync audio/video capture
**FIXME:39** on Linux; additionally `CREDITS-wolfcam.txt:27` (em92) — *"bug
fix: renderer shader times incorrect when recording videos."* Indicates
shader timing is delicate during video record.
**Why it matters:** Do NOT change renderer settings (`r_fullscreen`,
`r_mode`, `r_fboAntiAlias`) mid-capture. Set everything pre-launch.

### Overtime clock stuck at 0 for non-standard gametypes (pre-em92)
**CREDITS-wolfcam.txt:25** — *"bug fix: overtime clock stayed at zero for
game types besides duel, tdm, ca, and ft."*
**Why it matters:** If parsing overtime timing from older wolfcam AVIs or
scoreboard scrapes on CTF/FFA overtime, values were zero. Post-em92
builds only.

### `r_fullscreen 1` had fit issues (pre-em92 patch)
**CREDITS-wolfcam.txt:26** — *"bug fix: r_fullscreen 1 wouldn't fit game
screen correctly (via ioquake3 patch)."*
**Why it matters:** Windowed capture (`r_fullscreen 0`) is the safer
default for automation, especially on multi-monitor systems. Fullscreen
capture has historical edge cases.

### Freeze-tag thaws used to count as kills (fragforward)
**CREDITS-wolfcam.txt:18** — em92 fix — *"bug fix: fragforward treated
freeze tag thaws as kills."*
**Why it matters for dm_73 parser:** If extracting frag events from FT
demos, pre-em92 wolfcam exports include thaws as kills. Our parser must
distinguish `EV_OBITUARY` with MOD=thaw/freeze from real kills.

### `EV_JUICED` and `EV_LIGHTNINGBOLT` event indices were WRONG for a long time
**CREDITS-wolfcam.txt:61** — yumirak fix: *"fix EV_JUICED and
EV_LIGHTNINGBOLT index."*
**Why it matters for dm_73 parser:** If we hand-roll event constants (we
do — `phase2/dm73parser/`), USE THE FIXED INDICES from current wolfcam-src,
not older forks.

### Invulnerability sphere leaks on rewind
**CREDITS-wolfcam.txt:15** — em92 fix: *"invalid invulnerability sphere
would appear after rewinding."*
**Why it matters:** If pipeline uses `rewind` during capture (we do for
replay-speed-contrast, Rule P1-Q), stale powerup visuals may appear.
Prefer `seekclock` over `rewind` when going backward > 3s.

### "Out of ammo" sound on death (em92 fix)
**CREDITS-wolfcam.txt:20** — *"'out of ammo' sound played when player
dies."*
**Why it matters:** Old audio captures may have this false positive sound
— do not train any ML on it as an "out of ammo" signal.

### Unfixed: keel sound triggered on wolfcam switch
**FIXME:16** — *"wolfcam sometimes keel sound is being used -- because the
sound was triggered before the switch."*
**Why it matters:** Audio anomaly during first-person-switch transitions.
Phase 1 audio mix may need a notch filter or silence-gate around the
switch event.

### Unfixed: switching from wolfcam can trigger reward sounds
**FIXME:17** — *"switching from wolfcam can trigger reward sounds."*
**Why it matters:** False "Excellent!" / "Impressive!" audio events in
wolfcam captures. Beat-sync ML could mistake these for real rewards.

### Unfixed: freecam "ups meter" builds speed while stuck
**FIXME:210** — *"freecam getting stuck when entering and ups meter showing
that you are building speed."*
**Why it matters:** Velocity overlay scraping is unreliable in freecam.
Drop velocity-on-HUD as a signal source.

### `/video` time reporting can report negative delta
**FIXME:232-237** — Recorded case:
```
videos/1286538323-0000.avi closed
video time: 72790200 -> 72789448  total -752 (-0.752000)
```
Noted "took out for now." Means the AVI metadata can report a negative
duration in edge cases.
**Why it matters:** When parsing `ffprobe` on wolfcam-captured AVIs, sanity
check `duration > 0`. Our ffmpeg assembly pipeline should refuse negative
durations explicitly.

### Grenade missile-owner tracking is approximate
**FIXME:73-74** — *"newer ql grenade clientNum for logging missile hits -
also for missile hits just try and keep track of owner based on when missile
first appears, origin and trTime should id."*
**Why it matters:** Our dm_73 parser assigns grenade kills via entity
snapshots — if the owner is not explicit in the state, we are making an
educated guess (matches what wolfcam does). Mark grenade-direct kills
with a confidence flag in the frag DB.

### `MAX_DEMOS` may be defined twice
**FIXME:144** — *"MAX_DEMOS defined twice i think."*
**Why it matters:** If code is rebuilt with conflicting values, silent
truncation of the demo-list UI. Grep the constant in any fork.

### "max parse entities error" is a real crash
**FIXME:384** — *"max parse entities error."*
**Why it matters:** Some QL demos (particularly crowded CA rounds) can
exceed the parse-entity ring buffer. Wolfcam has no graceful handling.
Our parser MUST handle this without crashing the whole batch job.

---

## TOCTOU / racy file patterns

### cfg write + spawn is not atomic
The canonical automation recipe writes `commandsRecord.cfg` then spawns
wolfcamql. Between those two steps another process could read the cfg. In
a single-threaded Python loop this is fine. In a parallel batch driver
(e.g. Tr4sH command-center spawning N workers) **each worker MUST write to
a unique cfg filename** and exec that specific name — do not share
`commandsRecord.cfg` across parallel jobs.

### cfg delete-after-spawn is racy
`TRIMMING.py:52` removes the cfg right after the spawn call returns. The
spawn call is blocking (effectively — the shell invocation does not return
until wolfcamql exits), so this is safe in sequential mode. A
non-blocking launcher MUST NOT remove the cfg until after wolfcamql has
actually exec'd it. Safer pattern: append jobid to the cfg filename and
clean up after confirmed process exit.

### `q3config.cfg` is rewritten on clean shutdown
Governed by `com_autoWriteConfig` (default `2` in observed q3config).
Crash-exits do NOT rewrite. Use `at <time> quit` (clean quit), not kill
signals, or your cfg edits for the next run get overwritten unpredictably.

---

## Deprecated-but-loadbearing paths

### `/record aaa` on demo load
**File:** `WOLF WHISPERER/WolfcamQL/wolfcam-ql/cgamepostinit.cfg:1`
**Observation:** The shipped `cgamepostinit.cfg` starts with `/record aaa`
— records a DEMO named "aaa" on every load. This is almost certainly a
leftover debug artifact, but WolfWhisperer ships it so removing it may
break assumptions further up the pipeline (WolfWhisperer might look for
"aaa.dm_73" to confirm engine liveness). Do not delete without testing.

### `cl_aviCodec "mjpeg"` and `"huffyuv"` are the ONLY strings matched
**File:** `client/cl_avi.c:811-813`
**Behavior:** Codec selection is exact string match. Any other value
silently falls back to... nothing obvious. Verify behavior before setting
custom codec strings.

### `cl_aviFetchMode` must be `gl_bgr` / `gl_bgra` / `gl_rgb` / `gl_rgba`
**Bind in q3config:** bind i iterates these four. Other values probably
silently fail; no enum validation seen.

### `sv_altEntDir "nohmg"` in default q3config
**File:** observed in `autoexec.cfg`/`q3config.cfg`
**Behavior:** Maps "no heavy machinegun" variant entities for QL tourney
demos that use `nohmg` ruleset. Removing it breaks those demo loads.

---

## The big unfixed one: camera system comments

The FIXME file has ~150 lines (lines 102-150 plus 231-239 etc) of camera
system TODOs, including bluntly honest self-assessment:
*"***** viewpoint stuff is fucked, you need to look ahead to see if it's a
viewpoint or viewent..."* (line 133).

**Why it matters:** The wolfcam cinematic camera system (spline/interp,
cam-points, playcamera) is acknowledged in-source as fragile. Tr4sH Quake
should NOT try to preserve bug-compatibility with it — expect to rewrite
the whole camera subsystem against q3mme's (which is the cleaner codebase
per CREDITS-wolfcam.txt:4: *"CaNaBiS, HMage, auri, ent: q3mme (blur code,
q3mme camera code, dof code, and obviously inspiration)"*).

---

## Summary priorities for Tr4sH Quake port

Rank by porting risk:

1. **Protocol detection first** (quirks #6-#8 above). Any demo parser or
   engine must branch on protocol 43/73/90/91 before touching fields.
2. **Config-string team-scrape fallback** (QL quirk #1). Persistent live
   data bug in minqlx.
3. **`at` command scheduler + `cg_enableAtCommands`** — absolute requirement
   for automation compatibility.
4. **`fs_homepath` override semantics** — the batch render isolation
   mechanism depends on this.
5. **Camera system**: rewrite against q3mme, do not port wolfcam's.
6. **Windows console attach behavior** — replicate if we want to observe
   stdout from the parent launcher.
7. **All em92 bug fixes** — vendor the corresponding patches when forking.
8. **HUD widescreen bug compatibility** — optional but needed for
   pixel-identical captures of old fragmovies.
