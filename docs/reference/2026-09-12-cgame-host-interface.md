# The cgame host interface — every symbol classified (2026-09-12)

Task 1 of `docs/superpowers/plans/2026-09-12-pantheon-production-capture.md`.
The standalone `pantheon_frame.exe` stopped linking on 2026-09-08. The link
reported 25 undefined references to 13 `PANTHEON_CG_*` symbols, because
`host/pantheon_frame.c` had grown cgame calls that only `build_cgame.sh`
links. Rather than add a stub or wrapper just to satisfy the linker, every
call site was traced and classified, and the host now reaches cgame through
one narrow header.

## The interface

`engine/pantheon_renderer/host/pantheon_cgame.h` — the only cgame surface the
production path (demo → our parser → our cgame → our renderer → our FBO → our
frames) may call:

| Function | Replaces | Contract |
|---|---|---|
| `BindRenderer(re, cfg)` | — | once per process |
| `LoadGameState(gs, clientNum)` | `Reset` + `SetGameState` | a new game; clears every snapshot, command and demo bound fed before |
| `ApplyServerCommand(seq, text)` | `QueueServerCommand` (still present, as a wrapper at `seq+1`) | stored at the demo's own sequence number; `seq <= 0` or `NULL` is fatal |
| `SetSnapshot(n, snap)` | `PushSnapshot` | `NULL` is fatal (was silently ignored) |
| `SetDemoInfo(...)` | — | optional, after `LoadGameState` |
| `Init(clientNum, messageNum, commandSequence)` | `Init(void)` with hardcoded `1, 0, 0` | `clientNum` must equal the one given to `LoadGameState`, else fatal |
| `DrawActiveFrame(serverTime, firstFrame)` | `Frame` | unchanged body |
| `Shutdown()` | — | ends a take |

## Every former call site in `host/pantheon_frame.c`

| Symbol | Call sites (pre-change line) | Class | Now |
|---|---|---|---|
| `BindRenderer` | 788 | required runtime API | `pantheon_cgame.h` |
| `SetGameState` | 795, 932 | required runtime API | `LoadGameState(&gs, 0)`; `SetGameState` is `static` in the feed |
| `Reset` | 927 | wrong boundary (host managing feed internals) | folded into `LoadGameState`; `static` in the feed |
| `PushSnapshot` | 226, 831 | required runtime API | `SetSnapshot` |
| `Init` | 833, 935 | required runtime API | `Init(0, 1, 0)` — the same values CG_INIT received before |
| `Frame` | 1023 | required runtime API | `DrawActiveFrame` |
| `Shutdown` | 926 | required runtime API | unchanged |
| `BuildGameState` | 789, 928 | obsolete experiment (composed gamestate) | `pantheon_cg_compose.h`; a demo carries its own |
| `AddPlayerInfo` | 793, 930 | obsolete experiment (.shot cast) | `pantheon_cg_compose.h` |
| `ComposeSnapshot` | 193, 819 | obsolete experiment (.shot bridge, CLI still camera) | `pantheon_cg_compose.h` |
| `AddPlayer` | 207 | obsolete experiment (.shot actors) | `pantheon_cg_compose.h` |
| `AddRocket` | 222, 823 | obsolete experiment (`--rocket`, .shot projectiles) | `pantheon_cg_compose.h` |
| `AddExplosion` | 830 | obsolete experiment (`--explosion`) | `pantheon_cg_compose.h` |
| `Report` | declared only; never called | obsolete diagnostic | `pantheon_cg_compose.h` |

The composing helpers stay because the FrameTruth `.shot` bridge and the CLI
proofs still use them. They are declared apart from the interface so that the
demo reader (Task 2) has nothing to reach for but `pantheon_cgame.h`.

## Seam internals, not part of any interface

`pantheon_cg_syscall.c` answers cgame's traps from the feed through
`GetGameState`, `GetCurrentSnapshotNumber`, `GetSnapshot`,
`GetServerCommand`, `ServerCommandSequence` and `DemoInfo`, and exposes
`Syscall`, `LoadedWorld` and `SoundCallCount`. `pantheon_cg_run.c` uses
`Ready`, `LoadedClientNum`, `ProbePrint` and `RegisterAllWeapons`. The host
never calls these.

## Enforcement

Our own `host/*.c` compile with `-Werror=implicit-function-declaration` in both
`build_host.sh` and `build_cgame.sh`, so calling cgame without going through a
header fails the build. The vendored tree is exempt because it would not build.

## Behaviour

Unchanged by construction: the same CG_INIT arguments, the same snapshots in
the same order, the same frame calls. **Proven 2026-09-12:** the Task 1 build
rendered `v2.shot` (66 frames, 1280×720) with

```
pantheon_cgame.exe --basepath G:/QUAKE_LEGACY/output/demo_v2/_wolfcam_staging \
    --game baseq3 --cgame --set cg_draw2D 0 --shot <v2.shot with outputs redirected>
```

and **66 of 66 TGA MD5s equal** `docs/reference/2026-09-12-v2shot-reference.md5`.
A control run of the pre-change binary with the same command also matched 66
of 66, so the command reproduces the reference.

Side finding: the same command without `--game baseq3` fails
`Z_Malloc: failed on allocation of 16777240 bytes from the main zone` and
exits 1 with no frames. It fails loudly, not silently; the capture backend
(Task 7) must always pass `--game`.
