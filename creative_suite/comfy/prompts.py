"""Photoreal prompt seed + negative prompt shared across img2img jobs.

Kept in one place so both the API ({final_prompt} column) and the browser
textarea (readonly) render the same string. Change here -> change everywhere.
"""
from __future__ import annotations

PHOTOREAL_SEED_PROMPT = (
    "photorealistic PBR material, 8k ultra detailed, physically based rendering, "
    "real-world surface texture, subsurface scattering, micro detail, "
    "sharp focus, high dynamic range, professional product photography"
)

PHOTOREAL_NEGATIVE_PROMPT = (
    "stylized, cartoon, anime, flat shading, low poly, low-resolution, "
    "blurry, jpeg artifacts, text, watermark, signature, "
    "painting, illustration, drawing, render, CGI, 3D render, video game"
)


def build_final_prompt(user_suffix: str) -> str:
    """Combine seed + user suffix. Returns the exact text sent to ComfyUI."""
    suffix = (user_suffix or "").strip()
    if not suffix:
        return PHOTOREAL_SEED_PROMPT
    return f"{PHOTOREAL_SEED_PROMPT} {suffix}"
