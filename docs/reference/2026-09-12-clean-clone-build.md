# Clean-clone build proof (2026-09-12)

Task 0.5 Step 6 of `docs/superpowers/plans/2026-09-12-pantheon-production-capture.md`.
The question: can a fresh clone, with no WolfcamQL archive on the machine and no
download cache, build PANTHEON and render the same frames?

## Setup

- Clone: `git clone --depth 1 --branch feature/pantheon-production-capture file:///G:/QUAKE_LEGACY G:/QUAKE_LEGACY_WORKTREES/_cleanclone`
  at commit `56f6479` ("fix: one PANTHEON binary, found through the store").
- `WOLFCAMQL_ARCHIVE` unset. No `.cache/`. No `engine/pantheon_renderer/wolfcamql-11.3-src/`.
- Commands: `cd engine/pantheon_renderer && ./build_host.sh && ./build_cgame.sh`.

## Result

| Step | Outcome |
|---|---|
| bootstrap | pinned archive unreachable → upstream `codeload.github.com/brugal/wolfcamql/tar.gz/73e2d707…` → extracted to staging → **all 929 pinned files matched `TREE.sha256`**; the 8 packaging extras dropped → stamp `source: upstream:73e2d707e5dd1fb0fc50d4ad9f00940909c4b3ec` |
| `build_host.sh` | exit 0 — engine and host objects |
| `build_cgame.sh` | exit 0 — `build/pantheon_cgame.exe`, 2,364,844 bytes |
| total | 62 s including download and verification |
| render | `v2.shot`, 66 frames, `--basepath <stock staging> --game baseq3 --cgame --set cg_draw2D 0` → rc 0 |
| **frames** | **66 / 66 TGA MD5s equal** `docs/reference/2026-09-12-v2shot-reference.md5` |

So no project mirror is needed: upstream by commit, verified file by file, is
immutable enough. `mirrors` stays empty and no GitHub Release was published.
Step 1's fallback order still applies if upstream ever disappears: the local
archive (`WOLFCAMQL_ARCHIVE`, SHA-256 pinned), then the cache, then an ask
before publishing a Release.

## What the first attempt found

The first clean clone (commit `15b6b62`) failed, and both failures were real:

1. **The bootstrap refused upstream.** `macwolfcambuild` is a plain file
   upstream, but `upstream_extras_ignored` listed it as `macwolfcambuild/`,
   so it read as an unpinned file. Refusing it was correct; the listing was
   wrong. Fixed in `86f8195` with a regression test.
2. **The build was order-dependent.** `build_cgame.sh` links the objects
   `build_host.sh` compiles, and `build_host.sh` then failed its own link of the
   standalone `pantheon_frame.exe` (dead since 2026-09-08). The main
   checkout and the worktree had only built because old objects were already
   on disk. Fixed by Task 1 (`56f6479`): one binary, one link.

The scratch clone was deleted after the run.
