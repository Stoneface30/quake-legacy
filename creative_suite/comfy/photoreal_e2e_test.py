"""E2E validation — one sample per category, three pipelines.

Pipelines tested per image:
  A) 4x-UltraSharp upscale only      (no diffusion, pure CNN)
  B) Upscale + ControlNet-Tile 0.15  (dreamshaper8 SD1.5, low change)
  C) Upscale + ControlNet-Tile 0.30  (dreamshaper8 SD1.5, medium change)

Output: creative_suite/comfy/photoreal/e2e/index.html

Run:
  E:\PersonalAI\venv\Scripts\python.exe -u ^
    G:\QUAKE_LEGACY\creative_suite\comfy\photoreal_e2e_test.py
"""
from __future__ import annotations

import random
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from creative_suite.comfy.client import ComfyClient, load_workflow
from creative_suite.comfy.prompts import PHOTOREAL_NEGATIVE_PROMPT, build_final_prompt

PHOTOREAL = Path(__file__).parent / "photoreal"
ASSETS    = PHOTOREAL / "assets"
PAK00     = ASSETS / "pak00"
E2E_DIR   = PHOTOREAL / "e2e"

WF_UPSCALE    = Path(__file__).parent / "workflows" / "upscale_only.json"
WF_TILE_SD15  = Path(__file__).parent / "workflows" / "tile_controlnet_sd15.json"
WF_TILE_SDXL  = Path(__file__).parent / "workflows" / "tile_controlnet_sdxl.json"
SDXL_CONTROLNET = Path(r"E:\PersonalAI\ComfyUI\models\controlnet\TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors")

TIMEOUT = 300.0

# If SDXL controlnet is available use JuggernautXL, otherwise fall back to SD1.5
_WF_TILE = WF_TILE_SDXL if SDXL_CONTROLNET.exists() else WF_TILE_SD15

PIPELINES = [
    ("upscale_only",  WF_UPSCALE, None),   # pure CNN, no diffusion
    ("tile_d35",      _WF_TILE,   0.35),   # structural + moderate photorealism
    ("tile_d50",      _WF_TILE,   0.50),   # target photorealism
]

CATEGORIES = [
    ("player_face",  PAK00 / "models/players/anarki/anarki_h.png"),
    ("player_uv",    PAK00 / "models/players/anarki/anarki.png"),
    ("mapobject",    PAK00 / "models/mapobjects/eagleban.png"),
    ("powerup",      PAK00 / "models/powerups/ammo2.png"),
    ("weapon_uv",    PAK00 / "models/weapons2/bfg/bfg.png"),
    ("weaphit",      PAK00 / "models/weaphits/bfg01.png"),
    ("icon",         PAK00 / "icons/ammo_chaingun.png"),
    ("sprite",       PAK00 / "sprites/balloon4.png"),
    ("gfx",          PAK00 / "gfx/2d/backtile.png"),
    ("phase5_weapon",ASSETS / "phase5_png/gfx/misc/lightning2.png"),
]


def _pick_wall() -> Path:
    for p in sorted((PAK00 / "textures").rglob("*.png")):
        if p.stat().st_size > 20_000 and not any(
            x in p.stem.lower() for x in ("ad", "logo", "sign", "banner")
        ):
            return p
    return next((PAK00 / "textures").rglob("*.png"))


def _wait(comfy: ComfyClient, job_id: str) -> list[dict]:
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        out = comfy.output_filenames(job_id)
        if out:
            return out
        time.sleep(1.0)
    raise TimeoutError(f"job {job_id} timed out after {TIMEOUT}s")


def run_e2e() -> None:
    categories = CATEGORIES + [("texture_wall", _pick_wall())]

    print("=" * 64)
    print("QUAKE LEGACY — Photoreal E2E Validation")
    print(f"  {len(categories)} categories × {len(PIPELINES)} pipelines")
    print("=" * 64)

    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=5).read()
        print("ComfyUI: connected\n")
    except Exception as exc:
        print(f"ERROR: ComfyUI unreachable — {exc}\n  Start: E:\\PersonalAI\\run_comfyui_api.bat")
        sys.exit(1)

    prompt = build_final_prompt("")
    E2E_DIR.mkdir(parents=True, exist_ok=True)

    workflows = {name: load_workflow(wf) for name, wf, _ in PIPELINES}

    results: list[dict] = []
    total = sum(1 for _, src in categories if src.exists()) * len(PIPELINES)
    n = 0

    with ComfyClient(base_url="http://127.0.0.1:8188", timeout=90.0) as comfy:
        for cat, src in categories:
            if not src.exists():
                print(f"  SKIP (missing): {cat}  {src}")
                continue
            print(f"\n-- {cat}  ({src.name})")

            for pipe_name, wf_path, denoise in PIPELINES:
                n += 1
                dst = E2E_DIR / cat / f"{pipe_name}.png"
                dst.parent.mkdir(parents=True, exist_ok=True)

                if dst.exists():
                    print(f"  [{n}/{total}] SKIP (exists): {pipe_name}")
                    results.append({"cat": cat, "src": src, "pipe": pipe_name, "dst": dst})
                    continue

                wf = workflows[pipe_name]
                try:
                    kwargs: dict = dict(
                        prompt=prompt,
                        seed=random.randint(0, 2**32 - 1),
                        negative_prompt=PHOTOREAL_NEGATIVE_PROMPT,
                    )
                    if denoise is not None:
                        kwargs["denoise"] = denoise
                    else:
                        kwargs["denoise"] = 1.0  # not used by upscale_only wf

                    job_id = comfy.submit_img2img(wf, src, **kwargs)
                    out    = _wait(comfy, job_id)
                    first  = out[0]
                    png    = comfy.fetch_output(
                        first["filename"],
                        subfolder=first.get("subfolder", ""),
                        type_=first.get("type_", "output"),
                    )
                    dst.write_bytes(png)
                    print(f"  [{n}/{total}] OK: {pipe_name}")
                    results.append({"cat": cat, "src": src, "pipe": pipe_name, "dst": dst})
                except Exception as exc:
                    print(f"  [{n}/{total}] ERR: {pipe_name}: {exc}")

    _build_html(results, [c for c, _ in categories] + ["texture_wall"])
    print(f"\nGallery: {E2E_DIR / 'index.html'}")


def _build_html(results: list[dict], cat_order: list[str]) -> None:
    by_cat: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in results:
        by_cat[r["cat"]][r["pipe"]] = r

    pipe_labels = {
        "upscale_only": "4x-UltraSharp<br><small>(no diffusion)</small>",
        "tile_d35":     "JuggernautXL + TTPLanet<br><small>denoise=0.35</small>",
        "tile_d50":     "JuggernautXL + TTPLanet<br><small>denoise=0.50</small>",
    }
    pipe_names = [p for p, _, _ in PIPELINES]

    def img(path: Path, base: Path, caption: str, color: str = "#aaa") -> str:
        rel = path.relative_to(base).as_posix()
        return (
            f"<div style='text-align:center'>"
            f"<img src='{rel}' style='max-width:200px;max-height:200px;"
            f"image-rendering:pixelated;display:block;margin:0 auto 4px'>"
            f"<span style='font-size:10px;color:{color}'>{caption}</span></div>"
        )

    rows = []
    for cat in cat_order:
        if cat not in by_cat:
            continue
        cat_data = by_cat[cat]
        any_r    = next(iter(cat_data.values()))
        src      = any_r["src"]
        orig_rel = "../assets/" + src.relative_to(ASSETS).as_posix()
        orig_td  = (
            f"<td style='padding:4px'>"
            f"<div style='text-align:center'>"
            f"<img src='{orig_rel}' style='max-width:200px;max-height:200px;"
            f"image-rendering:pixelated;display:block;margin:0 auto 4px'>"
            f"<span style='font-size:10px;color:#4af'>ORIGINAL</span></div></td>"
        )
        result_tds = ""
        for pipe in pipe_names:
            if pipe in cat_data:
                r = cat_data[pipe]
                result_tds += f"<td style='padding:4px'>{img(r['dst'], E2E_DIR, pipe_labels[pipe].replace('<br><small>', ' ').replace('</small>', ''))}</td>"
            else:
                result_tds += "<td style='padding:4px;color:#555'>ERR</td>"

        rows.append(
            f"<tr>"
            f"<td style='padding:10px;vertical-align:top;white-space:nowrap'>"
            f"<b style='color:#c8a850'>{cat}</b><br>"
            f"<span style='font-size:10px;color:#666'>{src.name}</span></td>"
            f"{orig_td}{result_tds}</tr>"
        )

    pipe_headers = "".join(
        f"<th>{pipe_labels[p]}</th>" for p in pipe_names
    )

    html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
<title>QUAKE LEGACY — Photoreal E2E Validation</title>
<style>
  body{{background:#111;color:#eee;font-family:monospace;margin:0;padding:16px}}
  h1{{color:#c8a850}}p{{color:#888;font-size:13px}}
  table{{border-collapse:collapse;width:100%}}
  th{{background:#222;padding:8px;color:#c8a850;text-align:center;font-size:12px}}
  td{{border:1px solid #2a2a2a;vertical-align:middle}}
</style></head><body>
<h1>QUAKE LEGACY — Photoreal E2E Validation</h1>
<p>
  Pipeline A: <b style='color:#fff'>4x-UltraSharp upscale only</b> — pure CNN, zero hallucination risk.<br>
  Pipeline B: <b style='color:#fff'>ControlNet-Tile denoise=0.15</b> — dreamshaper8 SD1.5, subtle detail add.<br>
  Pipeline C: <b style='color:#fff'>ControlNet-Tile denoise=0.30</b> — dreamshaper8 SD1.5, more detail change.<br>
  <br>Judge each row. UV sheets should survive B/C without layout destruction.
  If B/C destroy a category, that category gets A only.
</p>
<table>
<tr>
  <th style='text-align:left'>Category</th>
  <th><span style='color:#4af'>ORIGINAL</span></th>
  {pipe_headers}
</tr>
{"".join(rows)}
</table></body></html>"""

    (E2E_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"  Gallery written: {E2E_DIR / 'index.html'}")


if __name__ == "__main__":
    run_e2e()
