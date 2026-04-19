# Task 9 — Reference-Asset Capture Smoke (4K @ 125 fps)

**Purpose:** End-to-end proof that the Task 9 slice (Ollama-assisted prompting
+ max-quality `gamestart.cfg` writer + `/api/capture/gamestart`) produces a
wolfcamql AVI capture at full spec §4.4 quality (3840×2160 @ 125 fps) that
shows the **approved photoreal variant** of `textures/base_wall/basewall01b.tga`
from `zzz_photorealistic.pk3`.

This is the capture-side twin of Gate CS-2 (which only proved the pack loads).
Here we prove the capture *actually runs at max quality* with the override
textures visible in the output AVI.

**Prerequisites:**

- Gate CS-1 passed (≥5 approved, ≥1 surface, ≥1 skin) and
  `zzz_photorealistic.pk3` built.
- Gate CS-2 passed (pack installed into baseq3, alpha-sort OK, smoke
  baseline/restore comparison shows override on-screen).
- A reference demo in
  `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\wolfcam-ql\demos\` that spends
  >3s near a wall rendered with `textures/base_wall/basewall01b`. If you
  don't have a known-good demo, use any CA round on a stock Q3 map — the
  shader is widely used.
- Backend running: `uvicorn creative_suite.app:create_app --factory` on :8000.
- wolfcamql binary at `G:\QUAKE_LEGACY\tools\wolfcamql\wolfcamql.exe`.

## The smoke recipe

### 1. Pick demo + timestamps

Scrub the demo in wolfcam first (`wolfcamql.exe +demo <name>.dm_73`), find a
window where `basewall01b` is onscreen for ≥3 seconds. Note:

- `seek_clock` — 3 seconds before the wall is framed (e.g. `"8:52"`)
- `quit_at`    — 3 seconds after (e.g. `"9:05"`)

Keep `quit_at - seek_clock` ≥ 10s so the engine has time to finish loading +
seek before capture starts.

### 2. Request a max-quality cfg via the API

```bash
curl -sS -X POST http://127.0.0.1:8000/api/capture/gamestart \
  -H "Content-Type: application/json" \
  -d '{
    "demo_name": "ref_basewall",
    "seek_clock": "8:52",
    "quit_at": "9:05",
    "fp_view": true
  }'
```

Expected response:

```json
{
  "cfg_path": "G:\\QUAKE_LEGACY\\creative_suite\\generated\\wolfcam_capture\\gamestart_ref_basewall.cfg",
  "fp_view": true
}
```

Open the written cfg and confirm it matches spec §4.4 verbatim. Every line
in `creative_suite/capture/gamestart.py::MAX_QUALITY_CVARS` must be present
in order, followed by `cg_drawGun 1` and the oneliner:

```
seekclock 8:52; video avi name :ref_basewall; at 9:05 quit
```

### 3. Launch wolfcamql with the cfg

```bash
"G:\QUAKE_LEGACY\tools\wolfcamql\wolfcamql.exe" \
  +set fs_homepath "G:\QUAKE_LEGACY\creative_suite\generated\wolfcam_capture" \
  +exec gamestart_ref_basewall.cfg \
  +demo <your-demo>.dm_73
```

The engine will:

1. Apply every max-quality cvar (r_mode -1, 3840×2160, aniso 16, etc.).
2. Load the demo.
3. `seekclock` to 8:52.
4. Start AVI recording as `ref_basewall.avi`.
5. Run until 9:05 — then `quit`.

Expected: wolfcam exits by itself; no manual console input. The AVI lands
under wolfcam's movie output dir (typically `<fs_homepath>/baseq3/wolfcam/`
— check `con_log.txt` for the exact path if unsure).

### 4. Verify the AVI dimensions + framerate

```bash
G:\QUAKE_LEGACY\tools\ffmpeg\ffmpeg.exe -i ref_basewall.avi 2>&1 | \
  grep -E "Stream|Duration"
```

Must show:

- `3840x2160` resolution (not 1920×1080 — that means `r_mode -1` was
  dropped).
- `125 fps` (not 60/90 — that means `com_maxfps` was dropped).
- Duration close to `quit_at - seek_clock + seekclock warmup` (~13–15s
  typical).

### 5. Confirm the photoreal texture is visible

Extract a frame around mid-capture:

```bash
G:\QUAKE_LEGACY\tools\ffmpeg\ffmpeg.exe -ss 00:00:05 -i ref_basewall.avi \
  -frames:v 1 -q:v 2 \
  docs/visual-record/$(date +%Y-%m-%d)/task9_capture_ref_basewall.png
```

Open the frame. The wall should be the **photoreal variant** from the pack,
NOT the stock Q3 texture — side-by-side comparison with Gate CS-2's baseline
screenshot confirms it.

If the wall looks stock: the cfg was applied but the pack wasn't loaded for
this run. Check `fs_homepath/baseq3/` contains `zzz_photorealistic.pk3`
(install API defaults may target a different baseq3 than wolfcam's homepath
— verify `WOLFCAM_BASEQ3_DIR` was set to the right one).

### 6. Downsample sanity check (optional but recommended)

For quick YouTube-comparable preview:

```bash
G:\QUAKE_LEGACY\tools\ffmpeg\ffmpeg.exe -i ref_basewall.avi \
  -vf scale=1920:1080:flags=lanczos -c:v libx264 -crf 17 -preset slow \
  ref_basewall_1080p.mp4
```

The 4K→1080p downsample looks visibly sharper than a native 1080p wolfcam
capture on the same shader — that's the anisotropy + negative-lodbias +
r_picmip 0 doing their job.

## Ship gate

Task 9 is considered "smoke-green" when all of these hold on one real demo:

- [ ] `POST /api/capture/gamestart` returned 200 and wrote a cfg on disk.
- [ ] Wolfcam launched with `+exec` that cfg, captured an AVI, and quit by
      itself (no human intervention).
- [ ] `ffmpeg -i ref_basewall.avi` reports **3840×2160 @ 125 fps**.
- [ ] A frame-grab shows the approved photoreal variant of
      `textures/base_wall/basewall01b.tga`, not stock.
- [ ] Frame-grab saved under `docs/visual-record/YYYY-MM-DD/` per Rule VIS-1.

## Troubleshooting

**AVI is 1920×1080, not 4K** — `r_mode -1` dropped. Some wolfcam builds need
`vid_restart` after `r_customwidth/height`; add `vid_restart` on its own line
before the oneliner if this recurs.

**AVI is 60 fps, not 125** — `com_maxfps 125` dropped. Usually a cfg ordering
bug; confirm the cvar lands before `video avi` in the on-disk cfg.

**Wolfcam never quits** — the `at X quit` trigger didn't fire. Check
seek/quit clock format matches the demo's timescale (some demos use
`mins:secs`, some `secs.millis`). Match the in-demo HUD clock format.

**Photoreal texture not visible** — see Gate CS-2 troubleshooting (§sv_pure,
alpha-sort, path casing). The capture side is working; the pack side is the
suspect.

**Console reappears mid-capture** — `cg_draw2D 0` dropped or wolfcam HUD
override fired. Add explicit `set ui_recordSPDemo 0` before the oneliner if
this recurs.
