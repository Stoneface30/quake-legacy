# Look development with ComfyUI — and its hard limit

## The limit first

ComfyUI decides **nothing** about the world. Not where a rocket was, not where
an enemy stood, not whether a player died, not camera collision, not geometry.
Truth stays deterministic and upstream. Diffusion output enters only as
**reference for a human decision** or as a **controlled pass over a
deterministic render**.

## What is installed

Server: `E:/PersonalAI/ComfyUI` — **not running right now** (port 8188 does not
answer). Launch per CLAUDE.md: run `main.py` directly and wait for the real
bind, then `python -u creative_suite/comfy/verify_comfyui.py`.

| asset | where |
|---|---|
| 20 workflow JSONs | `creative_suite/comfy/workflows/` |
| checkpoints | `dreamshaper_8` (SD1.5) · `juggernautXL_ragnarokBy` (SDXL) · `RealVisXL_V5` · `sd3.5_large_fp8` · `SUPIR-v0Q` |
| ControlNet | `control_v11f1e_sd15_tile` |
| upscaler | `4x-UltraSharp` |
| LoRAs | `NeonifyV2-4Extreme`, `SDXL_style_DoodleRedmond`, doodle/world styles, Wan2.2 video LoRAs |
| pak00 source PNGs | `creative_suite/comfy/assets/` (6,190 files) |

## Workflows worth reusing for the Temple

| workflow | use here |
|---|---|
| `concept_art_sdxl.json` | concept boards: hall silhouette, door ornament, banner layouts |
| `style_depth_realism.json`, `style_zavy_depth.json` | depth-guided variants of a **rendered native frame** — the geometry stays ours |
| `tile_controlnet_sd15.json` + `4x-UltraSharp` | stone/metal texture studies at the PH5-1 quality bar |
| `style_chromatic.json`, `style_edge_chrome.json` | `^4`/`^7` emissive and metal studies for the doors |
| `ink_etching_sdxl.json` | glyph and pediment ornament exploration |

PH5 rules still apply: upscale + ControlNet-Tile, never plain img2img above
denoise 0.10; UV sheets tile_d35 max; FX/shape-critical categories upscaler
only.

## The three legitimate uses in this session

1. **Concept boards** before any modelling — cheap, disposable, decided by the
   director.
2. **Material studies** — what PANTHEON blue on wet stone looks like, as a
   reference for a Quake shader, not as the shader.
3. **Controlled stylisation of a deterministic pass** — a native frame, plus
   its depth, restyled with the geometry pinned. Only when the look is agreed,
   and always labelled in the provenance table.

Anything that looks like ComfyUI inventing a place, a pose or an event is out
of bounds.
