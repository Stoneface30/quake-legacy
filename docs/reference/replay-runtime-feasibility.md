# PANTHEON Live Replay Runtime — feasibility findings (2026-08-31)

Written in response to the Phase-2 architecture pivot proposal (live,
browser-directed Quake replay runtime superseding the proxy-clip workflow).
This documents what our own engine research already proves about
feasibility, and what already exists in the codebase to build on — before
committing engineering time in one direction or another.

## The decisive fact: wolfcamql has no IPC surface

Fully documented in [`engine/engines/wolfcam-knowledge/03-ipc-commands.md`](../../engine/engines/wolfcam-knowledge/03-ipc-commands.md)
from earlier RE work. Summary:

- **No sockets, no named pipes, no RCON, no file-watcher.** Searched and
  ruled out in the win32 client source (`sys_win32.c`, `sys_main.c`,
  `sv_ccmds.c`). `Sys_ConsoleInput` exists but is wired to the allocated
  console window on Windows, not a piped stdin — confirmed dead end for a
  parent process to inject commands into an already-running client.
- **All control is two mechanisms**: (1) command-line `+set`/`+exec`/`+demo`
  tokens applied once at process start, and (2) on-disk cfg files that only
  get re-`exec`'d at fixed engine lifecycle points (`cgamepostinit.cfg`,
  `roundstart.cfg`, `roundend.cfg`, the `at <serverTime> <cmd>` scheduler).
  Nothing re-reads a cfg file on arbitrary demand from outside the process.
- **`at`** is the most powerful primitive (queue a command at a future demo
  serverTime, gated by `cg_enableAtCommands`) — but it is scheduled at
  launch, not injectable mid-session.

**What this means concretely:** a browser backend cannot open a WebSocket to
an already-running wolfcamql process and say "switch to third-person now" or
"orbit here" and see it react instantly. That specific shape of "live
remote control" does not exist in the stock engine.

**What still works today, live, for a human:** once wolfcamql is running
with `freecam` active, a person physically at the keyboard gets full
real-time WASD + mouse-look control — that's ordinary input handling, not
IPC, and it already works with zero new engineering. The gap is specifically
*remote* control from a browser over the network while nobody is at the
keyboard.

## What already exists and is directly reusable

Earlier phases already built the "scene recipe" concept this pivot asks
for — it just isn't wired to a live loop yet:

| Module | Status | Covers |
|---|---|---|
| `creative_suite/engine/camera_paths.py` (567 lines) | done | 10 camera rigs (orbit, vertical_orbit, follow_entity, side_track, chase, top_down, projectile_follow, bullet_time_arc), BSP collision (`BspTracer`, `validate_path`, `adjust_path`), candidate scoring (`score_path`, `generate_candidates`) |
| `creative_suite/engine/timeline.py` (292 lines) | done | `Timeline` class (slow_to/freeze/impact_hold), `timescale_curve`, `fov_curve`, deterministic `to_wolfcam_script()` — a timeline compiles straight to a wolfcam cfg |
| `creative_suite/engine/shot_plan.py` (137 lines) | done | `assemble_shot_plan()`, deterministic `scene_recipe_id` via `hash_demo()` + `canonical_json()`, `persist_shot_plan`/`load_shot_plan`/`list_shot_plans` |
| `creative_suite/engine/cinematic.db` | done | 17 effects, 17 recipes, 10 cameras, 8 audio treatments, hero-gated recommender |

This is real: "scene recipe is the source of truth," "deterministic
reproducibility from a hash," and "camera rig system" are not greenfield —
they're built. What's missing is the live control loop and streaming
transport connecting `/frags` to a running engine instance.

## Three honest paths forward

### Path A — Human-at-keyboard live director (near-zero new engineering)
`/frags` becomes a **launcher/picker**, not a remote controller. Clicking a
frag/scene relaunches wolfcam seeked to that moment with `freecam` armed
(reuses `wolfcam_capture.py` as-is, minus the auto-quit). The user flies the
camera live, for real, at the keyboard — genuine interactivity, because it's
local input. A small glue script samples freecam origin/angles/fov once per
frame to a log file; hitting a bound key ("mark keyframe") appends a
keyframe that already matches `camera_paths.py`'s keyframe dict shape, so it
drops straight into the existing `Timeline`/`shot_plan` pipeline. Cost:
one cfg + one small Python watcher. Available essentially immediately.
Limit: the "live" part happens in the wolfcam window, not inside the
browser — `/frags` shows the resulting recipe/preview afterward, not a
live video feed.

### Path B — Relaunch-per-edit remote preview ("near-live")
Browser changes a parameter (POV/camera/timescale) → backend kills and
relaunches wolfcam seeked to the same point with the new cfg → grabs a
handful of frames → pushes them to `/frags` as a fast-refreshing preview
(not a full rendered clip). No engine source changes. Removes "render 30s,
watch, reject, render again" for full clips, but each change still pays the
seek+launch cost we've already measured empirically (tens of seconds;
worse deep into a long demo, since wolfcam fast-parses forward at roughly
25–50x realtime to reach a seek point). This is meaningfully better than
today's proxy workflow, but it is not sub-second interactive.

### Path C — True live remote control (native engineering project)
Add an actual control socket + a frame-streaming path (WebRTC or an MJPEG
bridge) directly into the wolfcamql C++ source, then rebuild the client.
This is the only path that delivers what the pivot describes literally
(drag a camera in the browser, see the native engine react in real time).
It requires a working build toolchain for the Q3 codebase — our RE work so
far (Ghidra decompilation of `wolfcamql-11.3.exe`, binary patching for LAA,
pk3/cfg overrides) has never included compiling wolfcamql from source, so
step zero is standing up that toolchain before any control-socket code can
be written. Realistic scope: a multi-day engineering project, not a single
session — closer to a funded research track (FT-1/FT-4 scale) than an
afternoon's work.

## Path C — quick build-toolchain recon (2026-08-31, light pass only)

Per the user's "keep the deep dive for later" instruction, this is a scoped
recon, not an attempt to actually build anything.

**Better news than assumed:** the repo already carries usable Windows build
projects for the Q3 family — `engine/engines/_forks/q3mme/trunk/code/
quake3.sln` is a VS2010-format solution (`quake3mme` + `cgame`/`game`/
`q3_ui` `.vcxproj` projects) that modern Visual Studio can open and
auto-upgrade. `_canonical/code/win32/{msvc2005,msvc2017}/quake3e.sln` and
`_canonical/misc/{msvc,msvc10}/ioq3.sln` exist too. q3mme is specifically
the fork that carries the camera-spline/MME features we'd want a control
socket to expose, so this is a real head start for Path C if/when it's
picked up.

**The gap:** our actual capture engine — `wolfcamql-src` (the `brugal/
wolfcamql` fork, `engine/engines/_canonical/wolfcamql-src/`) — has a
`misc/msvc/` directory but it's **empty**. All four engine source repos are
shallow clones (history-truncated, confirmed via `REPOS.md` — not a
missing-files artifact), so this looks like an upstream gap in that repo
rather than something our clone process dropped. Building wolfcamql itself
(vs. q3mme) would need either finding/reconstructing its build files or
retargeting the control-socket work onto q3mme instead of wolfcamql — worth
a decision when Path C is actually scheduled.

**Net effect on the estimate:** Path C is somewhat less "start from zero"
than the original write-up suggested (a real, openable solution exists for
the closest sibling engine), but the specific binary we run today still
needs its own build path sorted out first. Scope estimate (multi-day,
funded-research-track shaped) stands.

## Recommendation

Path A costs almost nothing and is compatible with everything already
built — it can start today and directly produces `shot_plan` rows through
the existing pipeline. Path C is the only way to get the literally-live
browser-driven experience described in the pivot, but it's a scoped
research track, not a quick add-on. Path B sits in between and mostly
matters if Path C turns out not to be worth the investment.

## Path C build audit (2026-08-31, second pass)

Trigger for this pass: the light-pass recon above assumed "stand up a
toolchain" was step zero for Path C. It isn't — this machine already has
VS2022 Build Tools with MSVC 14.44.35207 (x86 + x64 host/target), Windows
10 and 8.1 SDKs, and `VsDevCmd.bat`. This pass re-audits the four candidate
solutions against that actual toolchain, file-by-file, still without
attempting a build. It also corrects one claim from the light pass: the
empty third-party stub folders in `wolfcamql-src` are **not** a shallow-git-
clone artifact — `engine/engines/_canonical/` (all of it) is wholesale
`.gitignore`d in this repo, so nothing under it is git-tracked at all. The
emptiness is a property of however that source drop was originally
extracted onto disk, not a clone-depth issue.

### Per-engine table

| Engine | Solution | Toolset declared | Target arch | 3rd-party libs | Retarget difficulty |
|---|---|---|---|---|---|
| **q3mme** | `_forks/q3mme/trunk/code/quake3.sln` (4 projects: quake3mme/cgame/game/q3_ui) | `.sln` header says "Visual Studio 2010" (Format 11.00), but all 4 `.vcxproj` are already `ToolsVersion="15.0"` with `PlatformToolset` `v141` (Release Interop) / `v141_xp` (Debug, Release) — someone already bumped this off VS2010 once. v141 isn't installed here (only v143). `WindowsTargetPlatformVersion` 8.1 everywhere. | Win32 only, 3 configs (Debug/Release/Release Interop) | **Present as prebuilt**: `freetype.lib`, `libcurl.lib` (`code/libs/win32/lib/`) + full matching headers (`code/libs/win32/include/{curl,freetype,mad.h}`); `libmad.lib`, `libpng.lib`, `zlib.lib` also prebuilt (`code/libs/win32/`). **Present as source**: `jpeg-6` (own README), `renderer/zlib`, `renderer/libpng` (full vendored source, compiled in-tree per the `.vcxproj`'s `ClCompile` list). **No SDL anywhere** — Windows build uses native win32 windowing (`win32/glw_win.h`, `win32/win_local.h`), not SDL1.2/2. Nothing missing. | **Low-medium.** Toolset bump (v141→v143, or install the VS2017 v141 optional component) is a known mechanical edit across 3 configs × 4 projects. One wrinkle: `quake3.vcxproj`'s Release config hardcodes `C:\Program Files (x86)\Microsoft SDKs\Windows\v7.1A\...` in include/lib/exe paths — that SDK almost certainly isn't installed; looks like dead vestigial config since `WindowsTargetPlatformVersion=8.1` already covers it, should just delete those lines. Real unknown: the prebuilt libs (freetype 2.4.10-era, an old libcurl static build) were compiled with a pre-2015 MSVC runtime; the project already has defensive `/nodefaultlib:libcmtd.lib /NODEFAULTLIB:msvcrt.lib` linker flags, implying this CRT fight already happened once — expect to revisit it. |
| **wolfcamql-src** | none — `misc/msvc/` confirmed **empty** (0 items), no `.sln`/`.vcxproj`/`.vcproj` anywhere in the tree | N/A | N/A (id-tech3 code present is Win32-only in spirit, same as siblings) | **All 9 stub folders confirmed genuinely empty** — swept every one of `AL`, `SDL12`, `freetype2`, `jpeg-6b`, `libcurl`, `libspeex`, `pthread-win32`, `vorbis`, `zlib` for `.c/.cpp/.h/.lib/.dll/.a` files: **0 files in every single one.** Not headers-only — fully empty. **But**: a sibling tree, `_canonical/code/thirdparty/`, holds full modern source for nearly the same list — `curl-8.15.0`, `freetype-2.14.3`, `jpeg-9f` (with a `wolfcamql-changes.diff` whose own diff header reads `wolfcamql/code/jpeg-9f`, i.e. this cache was assembled *for* a wolfcamql build), `libogg-1.3.6`, `libspeex-1.2.0`+`libspeexdsp-1.2rc3`, `libvorbis-1.3.7`, `openal-soft-1.24.3`, `pthread-win32-2.9.1.0`, three SDL2 versions, `zlib-1.3.1`. `_canonical/code/{AL,SDL12,libspeex,zlib,jpeg-8c,libcurl}` (the ioq3-flavored copies, real files: 7–103 each) also overlap. Missing prebuilt Windows `.lib`s for freetype/curl/pthread/speex/vorbis/AL/SDL12 anywhere in-repo except by reusing q3mme's freetype.lib/libcurl.lib. | **Medium-high.** This is not "no dependency source exists anywhere" — it's "the source exists, just not inside the empty stub folders this specific tree needs it in." Reconstruction path: take ioq3's or quake3e's msvc10/msvc2017 project family as a scaffold (closest structural match — same cgame/game/q3_ui/quake3/ui split), repoint every `ClCompile`/`ClInclude` at wolfcamql-src's actual `code/client`, `code/cgame`, etc. (which **do** have real source — only the 3rd-party folders are stubbed), and wire include/lib paths at the `thirdparty/` cache instead of the empty local ones. Every file list needs hand-verification against wolfcamql's actual (patched, freecam/multi-angle-added) source — no existing project file drops in unmodified. SDL 1.2 is a specific risk: the thirdparty cache only has SDL2, and if wolfcamql's client code calls SDL1.2 APIs directly (not just via project settings) that's a source-level porting question, not a project-file one — unconfirmed without a deeper source grep than this pass did. Realistically several days of work before a first compile attempt, separate from and before any control-socket code. |
| **quake3e** | `_canonical/code/win32/msvc2017/quake3e.sln` (9 projects: botlib, libjpeg, libogg, libvorbis, quake3e, quake3e-ded, renderer, renderer2, renderervk) | `.sln` format 12.00, "Visual Studio 15" (2017) header — self-consistent, not a stale label. `PlatformToolset` `v141`/`v141_xp`, `WindowsTargetPlatformVersion` `10.0.17763.0`. Same v141-not-installed situation as q3mme. | Win32, x64, **and ARM64** all defined per-project | **Built from source, in-solution**: `libjpeg` (46 `ClCompile` entries), `libogg` (2), `libvorbis` (21) — genuinely self-contained, no external fetch needed. **Headers present, prebuilt lib CONFIRMED MISSING**: `code/libcurl/windows/include/curl/*.h` exists, but the exact static libs the project links (`code/libcurl/windows/vs2017/lib32/libcurl_a.lib`, `lib64`, `_debug` variants) do **not** exist on disk anywhere in the repo — verified by direct listing, not inferred. No SDL dependency at all in the MSVC path (SDL2 is only wired for the mingw/linux/macOS `Makefile` build per `BUILD.md`'s `USE_SDL` flag) — removes SDL entirely as a Windows/MSVC concern. | **Low.** Same toolset action as q3mme (retarget v141→v143 or install the v141 component) across the same handful of projects. The one concrete gap (missing prebuilt libcurl static lib) has a trivial workaround for a smoke test: `USE_CURL`/`CURL_STATICLIB` gate the pak auto-downloader only, not core engine code — disabling that preprocessor define + dropping the `libcurl_a.lib` line from `AdditionalDependencies` is a 2-line project-property edit, no source changes. `BUILD.md` is explicit and authoritative: *"Install Visual Studio Community Edition 2017 or later and compile `quake3e` project from solution `code/win32/msvc2017/quake3e.sln`."* This is the best-documented, most self-contained target of the four. |
| **ioq3** | `_canonical/misc/msvc10/ioq3.sln` (5 projects: cgame, game, q3_ui, quake3, ui) | `.sln` format 11.00, "Visual Studio 2010" header. Unlike q3mme, the `.vcxproj`s here are genuinely unconverted VS2010: `ToolsVersion="4.0"` and **no `<PlatformToolset>` element at all**. (A second, older project family — `_canonical/misc/msvc/*.vcproj`, VS2005-era — sits alongside it; not the one to use.) | Win32 + x64, ×2 configs (base, "TA" Team Arena/mission-pack), 8 total | Per `AdditionalIncludeDirectories`: `code/SDL12`, `code/libcurl`, `code/AL`, `code/libspeex/include`, `code/zlib`, `code/jpeg-8c` (note: this is `_canonical/code/`, a sibling tree to wolfcamql-src, not wolfcamql-src itself). 5 of 6 confirmed populated with real files (SDL12: 42, AL: 7, libspeex: 103, zlib: 14, jpeg-8c: 57). `libcurl`: headers only (14 files) — same prebuilt-lib gap as quake3e, unconfirmed whether it's identical severity. `AdditionalDependencies` wants `SDL.lib`/`SDLmain.lib` (SDL **1.2**, not 2.x) — no prebuilt `.lib` for SDL1.2 was found anywhere in this repo during this pass (only an SDL2.dll under `thirdparty/libs/`, wrong ABI/version for this project). | **Low-medium.** Missing `<PlatformToolset>` is actually the *easiest* case of the four to retarget — opening in VS2022 offers the standard one-click "Retarget Solution" dialog, which inserts `v143` project-wide with no manual XML edits (contrast q3mme/quake3e, which hard-code `v141` and need that value *changed*, not added). Dependency picture is decent but not clean: the SDL1.2 prebuilt-lib gap is real and unresolved by this pass — SDL1.2 is long-abandoned upstream, so worst case means building it from source out of the vendored `code/SDL12` tree as a small side-task. |

### Recommended first smoke-test target: **quake3e**

Reasoning: it has the only engine-authored, version-pinned build doc in the
set (`BUILD.md`); its Windows/MSVC path has zero SDL entanglement; 3 of its
4 third-party needs are compiled from source inside the same solution; and
its single confirmed gap (prebuilt libcurl) is a disable-a-flag workaround,
not a new porting decision. Proving the modern-toolchain-against-this-
vintage-of-vcxproj question here first — cheaply, on code nobody needs to
touch for Path C — de-risks the same retarget operation before it's done on
q3mme, which is the fork that actually matters for the control-socket work.
`ioq3` is a reasonable second smoke test (arguably an even easier toolset
retarget) but carries one unresolved dependency question (SDL1.2 static
lib) that quake3e's Windows path sidesteps by not using SDL at all.

### Updated time estimate — "get something in this family compiling here"

This is scoped narrowly to *a linked, runnable `.exe` from one of these four
solutions on this machine* — it does not include any control-socket work,
which stays the separate, larger estimate the sections above already carry.

- **quake3e smoke test**: ~0.5–1 day. Retarget toolset, disable `USE_CURL`
  for the smoke build, then work through whatever the modern compiler flags
  in code last touched under VS2017-era defaults (old C occasionally trips
  newer `/permissive-`-adjacent strictness — likely a `/permissive` flag or
  a handful of localized fixes, not a rewrite).
- **ioq3 as a second smoke test**: +0.5–1 day, contingent on resolving the
  SDL1.2 static-lib gap (build from the vendored source if no prebuilt can
  be found).
- **q3mme (the fork that actually matters for Path C)**, once the toolchain
  question is proven on the above: ~1–3 days — toolset retarget, strip the
  vestigial v7.1A SDK paths, and absorb whatever the decade-old prebuilt
  libs (freetype 2.4.10 / old libcurl / libmad) throw at the modern CRT
  during linking, plus routine old-C-vs-new-compiler cleanup across the 4
  projects' source.
- **wolfcamql-src** (only relevant if a future decision moves the
  control-socket target off q3mme and onto our actual capture engine):
  reconstructing project files + wiring the `thirdparty/` dependency cache
  in is real, multi-day work — 3–7 days — *before* any first compile
  attempt, let alone control-socket code.

**Net:** getting *some* engine in this family to produce a linked binary on
this machine is now a **1–3 day toolchain-proving exercise**, not a
toolchain-standup project — the compiler question the light pass flagged as
step zero is resolved. The multi-day/funded-research-track estimate for
"then add a control socket + frame streaming" from the sections above is
unchanged and stays a separate, later estimate.
