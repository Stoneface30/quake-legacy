# q3mme — Quirks and Gotchas

## Build quirks

- `trunk/Makefile` assumes bundled q3lcc/q3asm — don't delete `bin/` even if building
  native cgame
- MinGW build needs `USE_LOCAL_HEADERS=1` to avoid SDL2 path conflicts
- Some `#include` paths assume case-sensitive filesystems; Windows usually fine but
  cross-compilation from Linux to Windows has hit this before
- Output binary named `q3mme.exe` on Windows, `q3mme.x86_64` on Linux (not `mme`)

## Runtime quirks

- **First time entering demo-edit mode is slow** — q3mme rebuilds the world geometry
  cache for edit-mode hover/pick. 2-5 seconds. Subsequent entries fast.
- **Free-cam doesn't collide with world.** `noclip` is always on in edit mode.
- **Time slider scrubbing rebuilds snapshot state.** Scrubbing backward is slower
  than forward because the engine re-plays from nearest keyframe.
- **`/devmap` + `/demos`** conflict — you can't record AND edit a demo in the same
  session. Record first, quit, re-open in edit mode.

## Capture quirks

- **`capture start` before `camera add 0`** → captures from first-person, not camera
  path. Easy mistake.
- **Motion blur at frame t samples BACKWARD in time** (from t-shutter to t). If you
  want forward-in-time blur, set `mme_blurShutter` negative (not documented).
- **Audio capture starts at the beginning of the demo**, not at capture start time.
  To align, either cut the audio externally in post or record audio separately.
- **Capture stop is sloppy** — last N frames are often lost if not padded. Pad
  capture end by mme_motionBlurFrames / cl_avidemo seconds.

## Camera scripting quirks

- **Splines through 2 points degenerate.** Add at least 3 keyframes for smooth paths.
- **Angle interpolation wraps.** Going from yaw 350° to 10° via spline goes the long
  way (through 180°). Use `camera lock` flag to force shortest-arc.
- **`camera clone` preserves time offsets weirdly.** If you clone a keyframe and
  then move it, the old one's time often shifts too. Workaround: clear and re-add.

## DOF quirks

- **`mme_dofFrames` must be a power of 2** (algorithmically required but not
  validated). 8, 16, 32. Setting to 10 produces artifacts.
- **DOF focus drifts during motion blur.** If camera moves fast, the focal point
  at subframe 0 is different from subframe N. Usually fine but visible at wide radius.

## Protocol quirks (relevant for port)

- q3mme is **proto-68 only currently** — playing a .dm_73 fails silently (no error,
  just black screen). Must add error message during port.
- q3mme's demo-cut writes proto-68 output regardless of input protocol — obvious
  bug once we add proto-73 support. Fix during port.
- **CS_MAX** is hardcoded to 1024 in q3mme's cl_parse.c. Port must raise this.

## VM quirks

- q3mme's VMs (cgame, game, ui) are compiled from sources in `trunk/code/`. Changes
  to `q_shared.h` require rebuilding ALL three VMs.
- `q3lcc` is picky about C99 constructs — designated initializers are hit-and-miss.
- `q3asm` assumes POSIX paths; use forward slashes.

## Engine-fork-specific quirks

- q3mme uses its own **menu system** for demo editing (`/demos` console commands are
  a CLI overlay on the GUI). The GUI is optional — we can drive everything via
  console commands for automation.
- q3mme ships a **demo browser in the main menu**. Automation bypasses this via
  `/demos play <filename>`.
- **Legacy OpenGL warnings** — q3mme requests a compat-profile context. On macOS
  since ~10.14 this logs "Use of GL compat profile is deprecated" every frame.
  Spam-only, not a bug. Linux + Windows are fine.

## Gotchas we'll hit during the proto-73 port

- **entityState_t size mismatch:** if qcommon/ is patched for proto-73 (64 clients)
  but cgame VM is built from unpatched header (32 clients), reading cl.snap.entities[33]
  returns garbage. MUST rebuild all VMs from the patched header.
- **Virtual demos with proto-73:** cg_demos_cut.c re-writes demo message streams.
  Must port proto-73 awareness to the WRITE path, not just the read path.
- **Save-state format incompatibility:** if we change q_shared.h layouts, any saved
  demo scripts from before the port may load with wrong camera positions.

## See also

- `_docs/wolfcamql-src/QUIRKS.md` — proto-73 runtime quirks
- `_docs/q3mme/PROTOCOL_LAYER.md` — exact files touched by port
