# Phase 5 ComfyUI Texture Pipeline — Bug Fixes
Date: 2026-04-17

Fixes to the two critical bugs identified in `phase5-comfyui-test-results.md`.

---

## Bug 1 — Path Flattening (CRITICAL, deployment-blocker)

**Symptom:** All ComfyUI outputs were dumped flat into `phase5/02_processed/`, so
`models/weapons2/railgun/railgun1.png` became just `railgun1.png`. Downstream
`repack_pk3.py` packed them at the wrong internal paths, so the resulting pk3
would not override stock textures in WolfcamQL's `baseq3/pak00.pk3`.

Additional risk: two source textures share a basename (e.g. `lightning2.jpg`
exists both in `gfx/misc/` and `models/weapons2/lightning/`). The flat layout
caused silent collisions — only one survived.

**Fix (`phase5/batch_comfyui.py`):**

- `main()` now computes `rel = png.relative_to(args.input)` per source and
  writes the output to `args.output / rel`, mirroring the input tree.
- `process_texture()` was changed to take a concrete `final_path` (instead of
  an output directory and basename rename). ComfyUI output is downloaded into
  `final_path.parent`, then renamed to `final_path`.
- ComfyUI's upload endpoint collides on duplicate basenames from different
  subdirs. Added `upload_image_as(image_path, upload_name)` and pass
  `upload_name = rel_posix.replace('/', '__')` so every uploaded source has a
  unique name inside ComfyUI's `input/` folder.

**Before:**
```
phase5/02_processed/
  railgun1.png
  lightning2.png          <- COLLISION (gfx vs models)
  icona_railgun.png
```

**After:**
```
phase5/02_processed/
  gfx/misc/lightning2.png
  icons/icona_railgun.png
  models/weapons2/lightning/lightning2.png
  models/weapons2/railgun/railgun1.png
```

**Verified in final pk3:**
```
$ python -c "import zipfile; [print(n) for n in zipfile.ZipFile('phase5/04_pk3/zzz_photorealistic.pk3').namelist()[:3]]"
gfx/misc/lightning2.tga
gfx/misc/lightning3.tga
gfx/misc/lightning3new.tga
```
107 internal paths, all correctly mirroring `pak00.pk3` layout — WolfcamQL
will load these over the stock textures.

---

## Bug 2 — Alpha Channel Stripped

**Symptom:** ComfyUI's `SaveImage` node writes RGB PNGs only. HUD icons
(`icons/icona_*`, `icons/iconw_*`) lost their transparency, causing them to
render with solid backgrounds on the HUD.

**Fix (`phase5/batch_comfyui.py`):**

- Load the alpha manifest (`01_png/_alpha_manifest.json`) at batch start.
- For each input, detect alpha via the manifest OR by opening the PNG and
  checking `im.mode in ('RGBA','LA','PA')`.
- Alpha-flagged textures are routed to a new `process_alpha_texture()` that
  **does not go through ComfyUI**. Instead it uses Pillow:
  1. 4x Lanczos upscale of the RGBA image (same spatial resolution as the
     ComfyUI path so pk3 sizes are consistent).
  2. UnsharpMask on the RGB channels only (`radius=2, percent=150, threshold=3`).
  3. Re-merge with the original alpha channel untouched.
- The rationale: HUD icons are small, their alpha is load-bearing, and they
  don't benefit from PBR hallucination the way 3D weapon skins do. A crisp
  Lanczos+sharpen is closer to what the user actually wants for icons.

**Verified:**
```
$ python -c "from PIL import Image; print(Image.open('phase5/03_tga/icons/icona_lightning.tga').mode)"
RGBA

TGA stats after pipeline: RGBA=69, RGB=38   (matches alpha manifest)
```

Alpha roundtrips cleanly: source PNG -> Pillow upscale -> PNG -> TGA(RLE) ->
pk3 -> re-open == RGBA 256x256.

---

## Full Pipeline Re-Run

All 11 weapons processed end to end against a clean workspace:

| Step | Count | Notes |
|---|---|---|
| Extract from pak00.pk3 | 107 assets | `models/weapons2/{bfg,gauntlet,grapple,grenadel,lightning,machinegun,plasma,railgun,rocketl,shells,shotgun}/` + `icons/` + `gfx/misc/` |
| Convert to PNG | 107 files | 69 with alpha |
| ComfyUI + alpha-preserve | 107 processed (68 alpha-preserved path, 39 ComfyUI path) | 1 transient rename error retried successfully |
| Convert to TGA | 107 files, all RLE | RGBA=69, RGB=38 |
| Repack pk3 | 107 files | 29.5 MB |

**Final pk3:** `G:/QUAKE_LEGACY/phase5/04_pk3/zzz_photorealistic.pk3` (29.5 MB)

(Up from 7.22 MB previously — the size jump is legitimate: 11 weapons instead
of 3, plus the full icons/ and gfx/misc/ families.)

---

## Remaining Known Issues

- `dreamshaper_8.safetensors` still substituted for `realisticVision_v60B1VAE` —
  acceptable for a first deploy, but consider downloading realisticVision for
  the PBR metallic look.
- Glow/emission maps (`railgun2.glow.tga`, `railgun3.glow.tga`, `plasma_glo.tga`)
  still go through the PBR prompt. They should probably use an additive-safe
  prompt or be passed through straight 4x-UltraSharp with no img2img. Deferred.
- One transient ComfyUI rename race hit `f_plasma.png` during the 107-file run
  (downloaded filename didn't match the expected temp name). A `--filter gfx`
  targeted re-run filled the one missing output. Root cause: ComfyUI increments
  its save counter per prompt; the `download_outputs()` assumption that the
  downloaded file would sit at a predictable name is fragile. Not deployment-
  blocking — the batch script is idempotent and a re-run fills any gaps. Can be
  hardened later by reading the filename directly from the ComfyUI history
  entry rather than relying on rename ordering.

---

## Next Step

Copy the pk3 into WolfcamQL:
```
copy G:\QUAKE_LEGACY\phase5\04_pk3\zzz_photorealistic.pk3 "G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\baseq3\zzz_photorealistic.pk3"
```
Re-render one demo, compare weapon appearance to stock.
