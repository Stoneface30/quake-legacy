# quake3e — Architecture

**Upstream:** https://github.com/ec-/Quake3e (shallow clone, 79 MB)
**Role:** Modern Q3 fork with Vulkan renderer + ffmpeg capture. Fallback for 4K/HDR.

## What it is

An actively-maintained Q3 engine that tracks ioquake3's baseline but adds:
- **Vulkan renderer** alongside OpenGL (selectable at runtime)
- **ffmpeg integration for capture** — pipes raw frames to an ffmpeg child process
- **64-bit native support** — modernized VM and native module loading
- **CMake build system** — first-class cross-platform
- Misc quality-of-life: better high-DPI support, improved menu scaling, etc.

## Module map

Same top-level as ioquake3 but in-tree organization differs slightly:

```
code/
├── qcommon/
├── client/
├── server/
├── cgame/, game/, ui/
├── renderer/        — original OpenGL renderer
├── renderervk/      — VULKAN renderer (NEW vs ioquake3)
├── sdl/
└── (platform dirs)
```

## What makes it interesting for our project

### Capture pipeline
- `code/client/cl_avi.c` replaced with ffmpeg-pipe approach
- No 4GB RIFF limit, encoding offloaded to ffmpeg
- Output format controlled by ffmpeg CLI args — mp4, mkv, webm, anything ffmpeg supports

### Vulkan renderer
- `code/renderervk/` — complete parallel implementation
- Enables modern features (HDR, MSAA beyond 8x, tessellation)
- Currently OpenGL-compat-profile limits at 8-bit color; Vulkan breaks through

### CMake build
- `CMakeLists.txt` at top level + per-module
- Much easier to integrate into our build automation than the Makefile forests in
  wolfcam/q3mme

## Role in Tr4sH Quake

quake3e is **not** the primary port target — q3mme is. But:
- Its ffmpeg-capture code is the template for upgrading q3mme's capture pipeline
- Its Vulkan renderer is the eventual replacement for q3mme's accumulation-buffer path
- Its CMake build is what we'd migrate q3mme to when we integrate everything

Think of it as a "modernization reservoir" — we pull features from it as needed.

## Entry points

Standard Q3: `sys_main.c` → `Com_Init` → `CL_Main` loop. Same as ioquake3 baseline.

## Build

```
cmake -B build -S .
cmake --build build
```

Outputs `build/quake3e.x86_64` (or `.exe`). Much less pain than wolfcam/q3mme.

## Known limitations

- No motion blur / DOF in Vulkan renderer yet (OpenGL renderer has them via standard
  accumulation — same as ioquake3)
- Demo format is vanilla Q3 proto-68 / proto-66 (same as q3mme — needs port for dm_73)
- No movie-maker features (camera splines, HUD scripting) — those live in q3mme

## See also

- `_docs/q3mme/ARCHITECTURE.md` — port target
- `_diffs/` — per-file deltas vs ioquake3 (renderer is nearly 100% novel)
