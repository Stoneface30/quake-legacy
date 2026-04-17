# ComfyUI Photorealistic Texture Pipeline — Technical Reference

> Research date: 2026-04-16 | Source: 3-agent parallel research
> Full pipeline: pk3 → TGA → PNG → ComfyUI → TGA → pk3

## Quick Start

```bash
# 1. Extract weapon textures from QL pak00.pk3
python -m phase5.extract_textures --pk3 "C:\...\Quake Live\baseq3\pak00.pk3" --filter models/weapons2 --out phase5/00_extracted

# 2. TGA → PNG (alpha audit included)
python -m phase5.convert_tga_png --input phase5/00_extracted --output phase5/01_png

# 3. ComfyUI batch (make sure ComfyUI running on 127.0.0.1:8188)
python -m phase5.batch_comfyui --input phase5/01_png --output phase5/02_processed

# 4. PNG → TGA
python -m phase5.convert_png_tga --input phase5/02_processed --output phase5/03_tga

# 5. Repack → zzz_photorealistic.pk3
python -m phase5.repack_pk3 --tga-dir phase5/03_tga --output "G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\baseq3\zzz_photorealistic.pk3"

# 6. WolfcamQL picks it up automatically — re-render any demo
```

## Critical Parameters

| Setting | Value | Why |
|---------|-------|-----|
| Denoise | 0.35 | UV layout preserved. >0.5 = shape drift, UV breaks |
| ControlNet | Tile, weight 0.75 | Preserves UV regions tile-by-tile |
| ESRGAN model | 4x-UltraSharp | Best for photorealistic hard-surface game textures |
| SD model | Realistic Vision v6 | Best for metal, worn surfaces, weapons |
| PoT requirement | Always | Q3 engine requires power-of-2 dimensions |
| pk3 naming | zzz_*.pk3 | Loads last = highest priority, wins over stock |

## Alpha Channel Pitfalls

Quake 3 weapon textures use alpha for:
- Specular/gloss (encoded in diffuse alpha)
- Team-color masks
- Transparency (scope glass, muzzle flash sprites)

**Never strip alpha.** Check `img.mode` before saving. Force RGBA if source was RGBA.

## Engine Constraints

```
r_picmip 0          — full resolution (required to see your upscaled textures)
+set com_hunkMegs 256 +set com_zoneMegs 128   — launch flags for hi-res textures
```

Quake Live locks r_picmip ≥ 1 in competitive. Test with ioquake3 for quality verification.

## pk3 Load Order

```
pak00.pk3           ← QL stock (lowest priority)
ql_4x_textures.pk3
q3plus_hd.pk3
cz45_weapons.pk3
zzz_photorealistic.pk3  ← YOUR FILE (wins everything)
```

## Models Needed in ComfyUI

```
ComfyUI/models/
  upscale_models/
    4x-UltraSharp.pth           ← https://openmodeldb.info/models/4x-UltraSharp
  checkpoints/
    realisticVision_v60B1VAE.safetensors
  controlnet/
    control_v11f1e_sd15_tile.pth   ← Tile ControlNet for UV preservation
```

## Blender MD3 Reference

Importer: https://github.com/neumond/blender-md3
- Import MD3 → UV editor → Export UV Layout → verify alignment after ComfyUI

## UV Verification

After processing, overlay the UV layout PNG on the processed texture to verify:
- No UV-critical regions shifted
- Barrel/stock boundary preserved
- Seams still in correct positions

If seams drifted: lower denoise to 0.25 and increase Tile weight to 0.85.
