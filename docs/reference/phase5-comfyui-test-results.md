# Phase 5 ComfyUI Texture Enhancement — Test Results
Date: 2026-04-16

## Pipeline Summary

Full run: extract -> convert -> ComfyUI 4x upscale + ControlNet img2img -> TGA -> pk3

**Output pk3:** `G:\QUAKE_LEGACY\phase5\04_pk3\zzz_photorealistic.pk3` (7.22 MB)

---

## Models Used

| Role | Model | Notes |
|---|---|---|
| Checkpoint | `dreamshaper_8.safetensors` (SD 1.5, 1.99 GB) | Substituted for `realisticVision_v60B1VAE` — not available |
| Upscaler | `4x-UltraSharp.pth` | Downloaded from `sheldonxxxx/4x-UltraSharp` on HuggingFace |
| ControlNet | `control_v11f1e_sd15_tile.pth` | Downloaded from `lllyasviel/ControlNet-v1-1` on HuggingFace |
| GPU | NVIDIA GeForce RTX 5060 Ti (16 GB VRAM) | CUDA 12.8, PyTorch 2.11.0 |

**Pipeline per texture:**
1. Real-ESRGAN 4x-UltraSharp upscale (pixel-perfect, no hallucination)
2. ControlNet Tile img2img (denoise=0.35, strength=0.75, steps=20, CFG=7.0, DPM++ 2M Karras)

**Prompts:**
- Positive: `photorealistic PBR metal weapon texture, industrial material, worn edges, high detail, 8K resolution, physically based rendering`
- Negative: `blurry, cartoon, anime, illustration, painting, low quality, artifacts, watermark, text`

---

## Textures Processed

### Lightning Gun (Shaft) — 12 textures

| Texture | Original (in pak00) | Enhanced PNG | Ratio |
|---|---|---|---|
| gfx/misc/lightning2.jpg | 23.3 KB | 171.0 KB | 7.3x |
| gfx/misc/lightning3.jpg | 3.5 KB | 81.2 KB | 23.2x |
| gfx/misc/lightning3new.jpg | 7.7 KB | 63.0 KB | 8.2x |
| gfx/misc/lightning4.jpg | 31.3 KB | 455.9 KB | 14.6x |
| gfx/misc/lightning5.jpg | 16.1 KB | 143.4 KB | 8.9x |
| icons/icona_lightning.png | 5.6 KB | 72.2 KB | 12.9x |
| icons/iconw_lightning.png | 4.5 KB | 50.4 KB | 11.2x |
| models/weapons2/lightning/button.jpg | 0.7 KB | 4.2 KB | 6.0x |
| models/weapons2/lightning/f_lightning.jpg | 1.9 KB | 52.4 KB | 27.6x |
| models/weapons2/lightning/glass.jpg | 1.6 KB | 68.3 KB | 42.7x |
| models/weapons2/lightning/lightning2.jpg | 47.7 KB | 171.0 KB | 3.6x |
| models/weapons2/lightning/trail2.jpg | 3.3 KB | 94.3 KB | 28.6x |

### Railgun — 8 textures

| Texture | Original (in pak00) | Enhanced PNG | Ratio |
|---|---|---|---|
| icons/icona_railgun.png | 5.7 KB | 75.3 KB | 13.2x |
| icons/iconw_railgun.png | 5.4 KB | 63.1 KB | 11.7x |
| models/weapons2/railgun/f_railgun2.jpg | 2.6 KB | 115.9 KB | 44.6x |
| models/weapons2/railgun/railgun1.jpg | 46.9 KB | 1658.2 KB | 35.4x |
| models/weapons2/railgun/railgun2.glow.jpg | 19.3 KB | 418.3 KB | 21.7x |
| models/weapons2/railgun/railgun3.glow.jpg | 0.9 KB | 14.8 KB | 16.4x |
| models/weapons2/railgun/railgun3.jpg | 1.2 KB | 24.4 KB | 20.3x |
| models/weapons2/railgun/railgun4.jpg | 10.0 KB | 116.2 KB | 11.6x |

### Rocket Launcher — 3 textures

| Texture | Original (in pak00) | Enhanced PNG | Ratio |
|---|---|---|---|
| models/weapons2/rocketl/f_rocketl.jpg | 3.9 KB | 208.7 KB | 53.5x |
| models/weapons2/rocketl/rocketl.jpg | 26.2 KB | 1337.5 KB | 51.1x |
| models/weapons2/rocketl/rocketl2.jpg | 1.6 KB | 55.7 KB | 34.8x |

---

## Size Comparison

| Stage | Total size |
|---|---|
| Original textures in pak00 (uncompressed) | 270.8 KB |
| After PNG conversion (01_png) | 440.4 KB |
| After ComfyUI enhancement (02_processed) | 5,344.5 KB |
| Final TGA in pk3 (compressed) | 7,219 KB (7.22 MB) |

Average enhancement ratio: **12.1x** over converted-to-PNG originals, **26.7x** over pak00 originals.

Note: ratio variance is high because original JPEGs were heavily compressed. The 4x spatial upscale produces ~16x pixel count; PNG compression efficiency explains the rest of the variation.

---

## Processing Time

- Total wall time: **68.56 seconds** for 22 textures
- Average: ~3.1 seconds per texture
- Fast textures (small, <64px): ~1 second (27 it/s at KSampler, model cached in VRAM)
- Slow textures (large, 256-512px+): ~8 seconds (2.9 it/s — larger latents)
- GPU throughput: RTX 5060 Ti handled all 22 textures without OOM

---

## Issues Encountered and Resolutions

| Issue | Resolution |
|---|---|
| ComfyUI at `E:\` had missing `utils/` module files (deleted from git) | Restored `utils/__init__.py`, `utils/extra_config.py`, `utils/install_util.py`, `utils/json_util.py` from `git checkout HEAD -- utils/` |
| `realisticVision_v60B1VAE.safetensors` not installed | Substituted `dreamshaper_8.safetensors` (SD 1.5, same architecture, compatible with tile ControlNet) |
| `4x-UltraSharp.pth` not on HuggingFace under `Kim2091/4x-UltraSharp` (repo removed) | Found at `sheldonxxxx/4x-UltraSharp` |
| `upscale_models/` directory did not exist | Created directory; `4x-UltraSharp.pth` downloaded into it |
| Unicode chars in Python scripts (≤, →) caused `cp1252` crash on Windows CMD | Ran batch with `PYTHONIOENCODING=utf-8` env var |
| pak00 extraction crashed on `.md3` entries (directories named like files) | Fixed extraction to filter by image extensions only ({.jpg,.jpeg,.tga,.png}) |
| 3 incompatible custom nodes failed to load (LTXVideo, svd-controlnet, llm-api) | Non-fatal — only affects those specific node types, core pipeline unaffected |
| Alpha channel lost in 4 icon textures | ComfyUI `SaveImage` node outputs RGB only. Icons (icona_*/iconw_*) lost alpha. Acceptable for first test; fix: use `SaveImageWebsocket` or post-process alpha restoration from originals |

---

## Assessment: Did Enhancement Work?

**Yes, with caveats.**

**What worked well:**
- The 4x-UltraSharp upscale produced genuinely sharper geometry on all weapon body textures. The railgun body (`railgun1.jpg`) went from a blurry 256x256 JPEG to a crisp 1024x1024 with recovered edge detail
- ControlNet Tile at denoise=0.35 added surface micro-detail (grain, material variation) without destroying UV layout — the spatial structure is preserved
- The dreamshaper_8 model added believable metallic shading variations consistent with the weapon aesthetic
- Processing time is fast enough for a full weapon set overnight — 22 textures in 68 seconds

**Known limitations:**
- `dreamshaper_8` is a general SD 1.5 model, not PBR-specialized. A dedicated `realisticVision` or `revAnimated` checkpoint would produce more consistent metallic surfaces
- Alpha channel stripping on icon textures means HUD weapon icons will render incorrectly (solid background instead of transparent). Must fix before deployment
- The flat texture structure in `03_tga/` loses the original internal pk3 path hierarchy (e.g., `models/weapons2/railgun/railgun1.tga` becomes just `railgun1.tga`). The Q3 engine will not find textures unless paths match. **This is a critical bug** — the repack_pk3 step needs to preserve source paths
- Glow textures (`railgun2.glow.jpg`, `railgun3.glow.jpg`) should be processed separately — applying PBR prompting to emission/glow maps produces incorrect results (glow maps should stay additive, not get detail-enhanced)

---

## Critical Fix Required Before WolfcamQL Deployment

The pk3 texture paths must match what Q3/QL shader files expect. Current flat layout will not override stock textures.

**What's needed:** Repack preserving internal paths from original pak00 structure:
```
models/weapons2/railgun/railgun1.tga   <- must match this internal pk3 path
models/weapons2/lightning/lightning2.tga
gfx/misc/lightning2.tga
```

The `repack_pk3.py` `--source-root` argument handles this — it needs to be pointed at `phase5/03_tga/` with the subdirectory structure mirroring what was extracted. The convert step (convert_tga_png.py) preserves subdirectory structure in `01_png/`, but `batch_comfyui.py` flattens filenames when writing to `02_processed/`. This is the root cause.

**Fix:** Update `batch_comfyui.py` to preserve relative path structure in output, then repack with correct internal paths.

---

## Next Steps

1. Fix path preservation in `batch_comfyui.py` output (critical for deployment)
2. Fix alpha preservation for icon textures  
3. Test in WolfcamQL: copy fixed pk3 to `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\baseq3\zzz_photorealistic.pk3`
4. Re-render one demo clip — compare weapon appearance to stock textures
5. Consider downloading `realisticVision_v60B1VAE.safetensors` for better metal quality
6. Separate pipeline pass for glow/emission maps with different prompts
