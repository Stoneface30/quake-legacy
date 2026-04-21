# QUAKE LEGACY — Style LoRA Suite

Base model: `juggernautXL_ragnarokBy.safetensors`  
LoRA workflow: `creative_suite/comfy/workflows/tile_sdxl_lora.json`  
Manifest: `creative_suite/comfy/loras/manifest.json`

## How It Works

All style LoRAs slot into the same `tile_sdxl_lora.json` workflow — a `LoraLoader` node sits between the checkpoint and the rest of the graph. The TTPLanet Tile ControlNet keeps the structure locked; the LoRA bends the paintbrush style without blowing up UVs.

```
ORIGINAL → 4x-UltraSharp → TTPlanet_TileGF_Preprocessor
              ↓                      ↓
         JuggernautXL           ControlNet conditioning
              ↓                      ↓
         LoraLoader (style)   → KSampler → VAEDecode → RESULT
```

## Styles Available

| Style | LoRA | Strength | Best for |
|---|---|---|---|
| photoreal_boost | Photorealistic Slider SDXL | 0.7 | All surface textures |
| cel_shade | Neonify SDXL v2.3 | 0.65 | Players, mapobjects |
| cartoon | Cel Shading Style (CGI Anime) | 0.85 | Player skins, weapons |
| photoreal_touch | PhotorealTouch SDXL v3 | 0.7 | player_face only |
| retro_quake | *needs training* | 0.7 | Everything |
| painterly | *search civitai* | 0.6 | Textures, mapobjects |
| anime | *search civitai* | 0.75 | Players, weapons |

## Download Priority

1. **Neonify SDXL** — https://civitai.com/models/124201 (cel shade + neon)
2. **Photorealistic Slider SDXL** — https://civitai.com/models/117060 (PBR boost)
3. **PhotorealTouch v3** — https://tensor.art/models/859370668192443725 (faces)

Save all `.safetensors` to: `E:\PersonalAI\ComfyUI\models\loras\`

## Running a Style Pass

```bash
# Edit full_overnight.py to use tile_sdxl_lora.json + set lora_name in submit_img2img
# OR run the standalone style batch (coming soon):

python -u creative_suite/comfy/style_batch.py \
  --style cel_shade \
  --categories players weapons2 \
  --denoise 0.45
```

## Database

Every render is logged to `photoreal/assets.db`:
```sql
SELECT a.rel_path, r.pipeline, r.style, r.output_path
FROM renders r JOIN assets a ON a.id = r.asset_id
WHERE r.style = 'cel_shade'
ORDER BY a.category;
```

## UI Integration Vision

The Studio UI can expose a "Style" dropdown on the asset inspector panel:
- Choose original / photoreal / cel_shade / cartoon / anime
- Preview updates live by serving from `photoreal/pipelines/{style}/`
- Apply to intro/outro/transition overlays for creative variation
