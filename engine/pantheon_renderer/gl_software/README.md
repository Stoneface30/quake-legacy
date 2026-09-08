# Application-local software OpenGL for PANTHEON

**This is a bring-up tool, not the production renderer.** It exists because the
NVIDIA ICD on this machine crashes on `glColor*` / `glNormal*` (see
`docs/reference/2026-09-07-nvidia-32bit-immediate-mode-blocker/`), which the Q3
fixed-function renderer cannot avoid. Software rasterisation let the host be
proven correct without waiting on that.

`softpipe` is *slow*. It is fine for a frame; it is not an answer for a
33,000-clip campaign. Production still needs the hardware GL path resolved, and
that is a separate question from whether PANTHEON's renderer is correct.

## What is here

`bin/` holds Mesa 24.3.3 (i686) plus its complete dependency closure, staged
beside the executable. Windows resolves `opengl32.dll` from the executable's own
directory first, so a binary run from `bin/` gets Mesa and a binary run from
anywhere else gets the system driver. Nothing in `System32` or `SysWOW64` was
touched, no `OpenGLDrivers` registry key was written, and the NVIDIA driver was
not modified.

Provenance and SHA-256 for every package: `PROVENANCE.md`.

## Verifying which GL is actually live

Do not assume. `glwho.exe` prints the **full path** of the loaded `opengl32.dll`
and `libgallium_wgl.dll` before anything else, precisely so that a Mesa that
failed to load and silently fell back to the NVIDIA driver cannot be reported as
a successful Mesa run.

```
cd engine/pantheon_renderer/gl_software/bin
./glwho.exe
```

Expected: `GL_VENDOR Mesa`, `GL_RENDERER softpipe`, and an `opengl32.dll` path
inside this directory.

`llvmpipe` is **not** available in this i686 build — `GALLIUM_DRIVER=llvmpipe`
fails outright and `softpipe` is the fallback that works. If speed ever matters
here, the x86_64 Mesa package (26.x) does carry llvmpipe, but that requires the
x64 host.

## Rendering a frame

```
cd engine/pantheon_renderer/gl_software/bin
./pantheon_frame.exe \
    --basepath "C:/Program Files (x86)/Steam/steamapps/common/Quake Live" \
    --home <writable dir> \
    --map bloodrun --origin -640 -848 448 --angles 0 90 0 \
    --actor-model models/players/sarge/upper.md3 \
    --actor-skin  models/players/sarge/upper_default.skin \
    --actor-origin -640 -698 424 --actor-angles 0 270 0 \
    --out frame.tga
```

`--no-world` renders entities only, with no world model. That is how the actor
path was isolated when the actor turned out to be occluded rather than broken —
worth remembering as the first check when an entity does not appear.

The camera and the actor placement above came from a real
`info_player_deathmatch` in the BSP, chosen because spawn points are guaranteed
to be in open space. **They are still hand-supplied inputs, not FrameTruth.**

## Converting the output

```
ffmpeg -i frame.tga frame.png
ffmpeg -framerate 30 -i seq_%05d.tga -c:v libx264 -crf 18 -pix_fmt yuv420p out.mp4
```

**Do NOT add `-vf vflip`.** `glReadPixels` returns rows bottom-to-top and the
TGA header written by the host leaves the image-descriptor origin bit clear,
which already means bottom-left origin. The file is correct on disk; ffmpeg
reads it correctly. Adding a flip "to correct for OpenGL" turns every frame
upside down, and it is not obvious in a Quake corridor -- a ceiling and a floor
look plausible either way. The tells are torch flames and whether a player
model stands on his feet.

## Pin the Gallium driver

```bash
export GALLIUM_DRIVER=softpipe
```

Without it Mesa probes Zink (Vulkan) first. That probe used to fail gracefully
with `vkCreateDevice failed` and fall back; it later began **crashing the
process during R_Init instead**, which looks exactly like a renderer bug and is
not one. Pinning the driver removes the probe, is deterministic, and keeps the
NVIDIA ICD out of the process entirely (`glwho.exe` then reports
`nvoglv32.dll NOT LOADED`).
