# QUAKE LEGACY — Video Production Tools Manifest

Generated: 2026-04-16

---

## Binary Tools

| Tool | Version | Location | Purpose | Status |
|---|---|---|---|---|
| FFmpeg | 8.1-essentials (gyan.dev) | `tools/ffmpeg/ffmpeg.exe` | Video encode/decode/filter — core Phase 1 & 2 engine | WORKING |
| ffprobe | 8.1-essentials | `tools/ffmpeg/ffprobe.exe` | Media inspection, clip metadata | WORKING |
| ffplay | 8.1-essentials | `tools/ffmpeg/ffplay.exe` | Playback preview | WORKING |

### FFmpeg Build Flags (notable)
- `--enable-avisynth` — AviSynth frame server integration
- `--enable-libx264`, `--enable-libx265` — H.264/H.265 encoding
- `--enable-libvpx` — VP8/VP9 encoding
- `--enable-nvenc`, `--enable-cuda-llvm` — NVIDIA GPU encoding
- `--enable-libvidstab` — Video stabilization
- `--enable-libzimg` — zscale (high-quality resize/colorspace)
- `--enable-librubberband` — Time-stretching / pitch correction

---

## Source Repos (git clones)

| Tool | Tag / Commit | Location | Purpose | Status |
|---|---|---|---|---|
| f0e/blur | v2.44 (commit 22f3247) | `tools/blur/` | Cinematic motion blur — Phase 3 | NEEDS-SETUP |
| AviSynth+ | commit 23f0e3f | `tools/avisynth-src/` | Frame-level video processing (source build) | NEEDS-BUILD |
| VapourSynth | commit 4a1400f | `tools/vapoursynth-src/` | Required by f0e/blur (source build) | NEEDS-BUILD |
| VirtualDub2 | v17 (commit 942a73a) | `tools/virtualdub2-src/` | Video editing / AVI handling | NEEDS-BUILD |
| ffmpeg-python | 0.2.0 (commit df129c7) | `tools/ffmpeg-python-src/` | Python API wrapper source reference | SOURCE-ONLY |
| moviepy | v2.2.1 (commit 7ffa4f0) | `tools/moviepy-src/` | Python video editing library source reference | SOURCE-ONLY |

---

## Python Packages (pip-installed, system-wide)

| Package | Version | Purpose | Status |
|---|---|---|---|
| ffmpeg-python | 0.2.0 | Python FFmpeg API — Phase 1 pipeline | WORKING |
| moviepy | 2.2.1 | High-level video editing API — Phase 1/2 | WORKING |
| streamlit | 1.48.0 | Web UI for preview/control dashboard | WORKING |
| requests | 2.32.5 | HTTP downloads, API calls | WORKING |
| tqdm | 4.67.1 | Progress bars | WORKING |
| numpy | 1.26.4 | Array operations for color/motion math | WORKING |
| Pillow | 10.4.0 | Image manipulation, thumbnails | WORKING |
| opencv-python | 4.10.0.84 | Computer vision, frame analysis | WORKING |

---

## Manual Steps Required

### f0e/blur (Phase 3 — motion blur)
1. Download and install VapourSynth binary installer from:
   `https://github.com/vapoursynth/vapoursynth/releases/latest`
   (Choose the `.exe` installer for Windows)
2. After VapourSynth is installed, download the blur release binary from:
   `https://github.com/f0e/blur/releases/latest`
   (Get `blur.exe` — the pre-built Windows binary, not the source)
3. Place `blur.exe` at `tools/blur/blur.exe`
4. Install required VapourSynth plugins (see blur README for plugin list)

### AviSynth+ (Phase 3 — frame-level processing)
- Option A (recommended): Download the pre-built installer from:
  `https://github.com/AviSynth/AviSynthPlus/releases/latest`
  Install system-wide. This is all that's needed for FFmpeg's AviSynth integration.
- Option B: Build from source in `tools/avisynth-src/` (requires CMake + MSVC)
  ```
  cd tools/avisynth-src
  cmake -B build -DCMAKE_BUILD_TYPE=Release
  cmake --build build --config Release
  ```

### VapourSynth (required for blur)
- Download the installer (not the source) from:
  `https://github.com/vapoursynth/vapoursynth/releases/latest`
- The source clone in `tools/vapoursynth-src/` is for reference only.
- After installing: `python -c "import vapoursynth; print(vapoursynth.__version__)"`

### VirtualDub2 (Phase 2 — AVI handling)
- The source in `tools/virtualdub2-src/` requires Visual Studio 2019+ to build.
- Pre-built binaries are available from:
  `https://sourceforge.net/projects/vdfiltermod/files/`
  Download the latest `VirtualDub2_*.zip`, extract to `tools/virtualdub2/`
- Source repo: `https://github.com/shekh/VirtualDub2` (v17, mirrored)

---

## Paths Summary (for pipeline config)

```
FFMPEG_BIN     = G:/QUAKE_LEGACY/tools/ffmpeg/ffmpeg.exe
FFPROBE_BIN    = G:/QUAKE_LEGACY/tools/ffmpeg/ffprobe.exe
BLUR_BIN       = G:/QUAKE_LEGACY/tools/blur/blur.exe          # after manual install
TOOLS_ROOT     = G:/QUAKE_LEGACY/tools/
```

---

## Verification Commands

```bash
# FFmpeg (working now)
G:/QUAKE_LEGACY/tools/ffmpeg/ffmpeg.exe -version

# Python packages (working now)
python -c "import ffmpeg, moviepy, streamlit, cv2, numpy; print('All OK')"

# blur (after manual VapourSynth + blur.exe install)
G:/QUAKE_LEGACY/tools/blur/blur.exe --help

# VapourSynth (after installer)
python -c "import vapoursynth; print(vapoursynth.__version__)"
```
