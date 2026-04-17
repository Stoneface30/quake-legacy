# quake3e — Quirks and Gotchas

## Build quirks

- CMake version 3.10+ required; some 3.8 systems fail on target_compile_features
- Vulkan build requires Vulkan SDK (LunarG) installed and `VULKAN_SDK` env var
- ffmpeg-pipe capture requires ffmpeg in PATH at runtime (not bundled)

## Runtime quirks

- `vid_restart` after changing `cl_renderer` sometimes crashes on Windows; workaround
  is to set the cvar in autoexec and full-restart the engine
- Vulkan renderer initially loads slower than GL (pipeline cache building); second
  launch is fast
- Some QL-era maps (loaded via zzz_*.pk3 packs) have shader stages that confuse
  Vulkan renderer — workaround: render those in GL

## Capture quirks

- ffmpeg-pipe approach means capture errors (disk full, codec missing) cause ffmpeg
  to close the pipe; the engine keeps rendering but nothing is written. Check stderr.
- `cl_aviCodec` cvar change mid-capture is ignored; must stop/restart capture
- Audio is NOT captured via the pipe — need separate `s_captureWav` approach
  (same as q3mme's separate-audio workflow)

## Protocol / demo quirks

- Proto-68 / proto-66 only. Playing a `.dm_73` shows a clear error message (unlike
  q3mme which silently fails).
- Demo cut functionality: NOT present in quake3e (q3mme has it; quake3e is more
  "engine modernization" than "movie tools")

## Things quake3e does NOT have (that we need)

- Camera path scripting (must come from q3mme)
- Motion blur (q3mme has it via GL; quake3e's Vulkan renderer doesn't yet)
- DOF (q3mme has it via GL; quake3e doesn't)
- Demo cut / virtual demos (q3mme has it)
- Proto-73 support (wolfcam has it)

## Upstreaming considerations

quake3e is **actively maintained**. If we improve the renderer or capture pipeline,
there's a real path to upstreaming. q3mme is more dormant — changes there stay
local unless we pick up maintenance.

## See also

- `_docs/q3mme/QUIRKS.md` — target engine
- `_docs/wolfcamql-src/QUIRKS.md` — proto-73 source
