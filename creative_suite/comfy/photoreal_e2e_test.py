"""E2E validation — one sample per category, all pipelines + LoRA variants.

Pipelines:
  upscale_only         — 4x-UltraSharp CNN, zero diffusion
  tile_d35/d50         — JuggernautXL + TTPLanet Tile (production range)
  tile_d60/d70/d80     — WILD: experimental high-denoise (fun, not for batch)
  tile_d35_photoreal   — LoRA: Photorealistic Slider (strength 0.7)
  tile_d35_cel_shade   — LoRA: Neonify cel shading (strength 0.65)
  tile_d35_ultra_det   — LoRA: Extremely Detailed ntc-ai (strength 1.5)

Output: creative_suite/comfy/photoreal/e2e/{category}/{pipeline}.png
        creative_suite/comfy/photoreal/gallery.html  (before/after/wild view)

Run:
  E:\\PersonalAI\\venv\\Scripts\\python.exe -u ^
    G:\\QUAKE_LEGACY\\creative_suite\\comfy\\photoreal_e2e_test.py

Skip existing outputs — safe to re-run after adding new LoRAs.
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from creative_suite.comfy.client import ComfyClient, load_workflow
from creative_suite.comfy.prompts import PHOTOREAL_NEGATIVE_PROMPT, build_final_prompt

PHOTOREAL = Path(__file__).parent / "photoreal"
ASSETS    = PHOTOREAL / "assets"
PAK00     = ASSETS / "pak00"
E2E_DIR   = PHOTOREAL / "e2e"
WF_DIR    = Path(__file__).parent / "workflows"

WF_UPSCALE    = WF_DIR / "upscale_only.json"
WF_TILE_SDXL  = WF_DIR / "tile_controlnet_sdxl.json"
WF_TILE_LORA  = WF_DIR / "tile_sdxl_lora.json"

SDXL_CONTROLNET = Path(
    r"E:\PersonalAI\ComfyUI\models\controlnet"
    r"\TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors"
)
_WF_TILE = WF_TILE_SDXL if SDXL_CONTROLNET.exists() else WF_DIR / "tile_controlnet_sd15.json"

TIMEOUT = 300.0

# Each entry: (pipeline_name, workflow_path, denoise_or_None, extra_placeholders)
PIPELINES: list[tuple[str, Path, float | None, dict[str, Any]]] = [
    # ── Production ──────────────────────────────────────────────────────
    ("upscale_only",       WF_UPSCALE,  None, {}),
    ("tile_d35",           _WF_TILE,    0.35, {}),
    ("tile_d50",           _WF_TILE,    0.50, {}),
    # ── Wild / experimental ─────────────────────────────────────────────
    ("tile_d60",           _WF_TILE,    0.60, {}),
    ("tile_d70",           _WF_TILE,    0.70, {}),
    ("tile_d80",           _WF_TILE,    0.80, {}),
    # ── LoRA style variants ─────────────────────────────────────────────
    ("tile_d35_photoreal", WF_TILE_LORA, 0.35, {
        "lora_name":     "sdxl_photorealistic_slider_v1-0.safetensors",
        "lora_strength": 0.7,
    }),
    ("tile_d35_cel_shade", WF_TILE_LORA, 0.35, {
        "lora_name":     "NeonifyV2-4Extreme.safetensors",
        "lora_strength": 0.65,
    }),
    ("tile_d35_ultra_det", WF_TILE_LORA, 0.35, {
        "lora_name":     "extremely detailed.safetensors",
        "lora_strength": 1.5,
    }),
]

CATEGORIES = [
    ("player_face",   PAK00 / "models/players/anarki/anarki_h.png"),
    ("player_uv",     PAK00 / "models/players/anarki/anarki.png"),
    ("mapobject",     PAK00 / "models/mapobjects/eagleban.png"),
    ("powerup",       PAK00 / "models/powerups/ammo2.png"),
    ("weapon_uv",     PAK00 / "models/weapons2/bfg/bfg.png"),
    ("weaphit",       PAK00 / "models/weaphits/bfg01.png"),
    ("icon",          PAK00 / "icons/ammo_chaingun.png"),
    ("sprite",        PAK00 / "sprites/balloon4.png"),
    ("gfx",           PAK00 / "gfx/2d/backtile.png"),
    ("phase5_weapon", ASSETS / "phase5_png/gfx/misc/lightning2.png"),
]


def _pick_wall() -> Path:
    for p in sorted((PAK00 / "textures").rglob("*.png")):
        if p.stat().st_size > 20_000 and not any(
            x in p.stem.lower() for x in ("ad", "logo", "sign", "banner", "authors", "readme")
        ):
            return p
    return next((PAK00 / "textures").rglob("*.png"))


def _wait(comfy: ComfyClient, job_id: str) -> list[dict]:  # type: ignore[type-arg]
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        out = comfy.output_filenames(job_id)
        if out:
            return out
        time.sleep(1.0)
    raise TimeoutError(f"job {job_id} timed out after {TIMEOUT}s")


def run_e2e() -> None:
    wall  = _pick_wall()
    categories = CATEGORIES + [("texture_wall", wall)]

    # Copy original (before) images into e2e for gallery reference
    import shutil
    for cat, src in categories:
        if src.exists():
            dst = E2E_DIR / cat / "original.png"
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(src, dst)

    print("=" * 72)
    print("QUAKE LEGACY — Photoreal E2E Validation")
    print(f"  {len(categories)} categories × {len(PIPELINES)} pipelines "
          f"= {len(categories) * len(PIPELINES)} renders")
    print("=" * 72)

    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=5).read()
        print("ComfyUI: connected\n")
    except Exception as exc:
        print(f"ERROR: ComfyUI unreachable — {exc}")
        print("  Start: Start-Process E:\\PersonalAI\\run_comfyui_api.bat "
              "-WorkingDirectory E:\\PersonalAI")
        sys.exit(1)

    prompt = build_final_prompt("")
    E2E_DIR.mkdir(parents=True, exist_ok=True)

    workflows = {name: load_workflow(wf) for name, wf, _, _ in PIPELINES}

    results: list[dict] = []  # type: ignore[type-arg]
    total = sum(1 for _, src in categories if src.exists()) * len(PIPELINES)
    n = 0

    with ComfyClient(base_url="http://127.0.0.1:8188", timeout=90.0) as comfy:
        for cat, src in categories:
            if not src.exists():
                print(f"  SKIP (missing): {cat}  {src}")
                continue
            print(f"\n-- {cat}  ({src.name})")

            for pipe_name, _wf_path, denoise, extra in PIPELINES:
                n += 1
                dst = E2E_DIR / cat / f"{pipe_name}.png"
                dst.parent.mkdir(parents=True, exist_ok=True)

                if dst.exists():
                    print(f"  [{n}/{total}] SKIP (exists): {pipe_name}")
                    results.append({"cat": cat, "src": src, "pipe": pipe_name, "dst": dst})
                    continue

                wf = workflows[pipe_name]
                try:
                    job_id = comfy.submit_img2img(
                        wf, src, prompt,
                        seed=random.randint(0, 2**32 - 1),
                        negative_prompt=PHOTOREAL_NEGATIVE_PROMPT,
                        denoise=denoise if denoise is not None else 1.0,
                        extra=extra or None,
                    )
                    out   = _wait(comfy, job_id)
                    first = out[0]
                    png   = comfy.fetch_output(
                        first["filename"],
                        subfolder=first.get("subfolder", ""),
                        type_=first.get("type_", "output"),
                    )
                    dst.write_bytes(png)
                    print(f"  [{n}/{total}] OK: {pipe_name}")
                    results.append({"cat": cat, "src": src, "pipe": pipe_name, "dst": dst})
                except Exception as exc:
                    print(f"  [{n}/{total}] ERR: {pipe_name}: {exc}")

    print(f"\nGallery: {PHOTOREAL / 'gallery.html'}")
    print("  Open in browser — before/after/wild all in one view.")


if __name__ == "__main__":
    run_e2e()
