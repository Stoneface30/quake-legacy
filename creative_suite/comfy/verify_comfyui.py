"""ComfyUI readiness verification — nodes, models, workflow JSON validity.
Run: python -u creative_suite/comfy/verify_comfyui.py
"""
from __future__ import annotations
import ast
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_NODES = [
    "TTPlanet_TileGF_Preprocessor",
    "ControlNetApplyAdvanced",
    "ControlNetLoader",
    "LoraLoader",
    "KSampler",
    "VAEEncode",
    "VAEDecode",
    "ImageUpscaleWithModel",
    "UpscaleModelLoader",
    "ImageScaleBy",
    "CheckpointLoaderSimple",
    "SaveImage",
    "LoadImage",
    "CLIPTextEncode",
]

REQUIRED_MODELS = {
    "JuggernautXL checkpoint":
        Path(r"E:\PersonalAI\ComfyUI\models\checkpoints\juggernautXL_ragnarokBy.safetensors"),
    "4x-UltraSharp upscaler":
        Path(r"E:\PersonalAI\ComfyUI\models\upscale_models\4x-UltraSharp.pth"),
    "TTPLanet SDXL Tile ControlNet":
        Path(r"E:\PersonalAI\ComfyUI\models\controlnet\TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors"),
    "Photorealistic Slider LoRA":
        Path(r"E:\PersonalAI\ComfyUI\models\loras\sdxl_photorealistic_slider_v1-0.safetensors"),
    "Neonify SDXL LoRA":
        Path(r"E:\PersonalAI\ComfyUI\models\loras\NeonifyV2-4Extreme.safetensors"),
}

WORKFLOW_DIR = Path(__file__).parent / "workflows"
PYTHON_SCRIPTS = [
    Path(__file__).parent / "full_overnight.py",
    Path(__file__).parent / "download_loras.py",
    Path(__file__).parent / "photoreal_e2e_test.py",
    Path(__file__).parent / "download_controlnet.py",
]

PASS = "  OK  "
FAIL = "  FAIL"

def check_comfyui() -> bool:
    try:
        urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=5).read()
        print(f"{PASS} ComfyUI reachable at http://127.0.0.1:8188")
        return True
    except Exception as exc:
        print(f"{FAIL} ComfyUI unreachable: {exc}")
        return False

def check_nodes() -> tuple[int, int]:
    ok = fail = 0
    try:
        raw = urllib.request.urlopen(
            "http://127.0.0.1:8188/object_info", timeout=120
        ).read()
        registered = set(json.loads(raw).keys())
        for node in REQUIRED_NODES:
            if node in registered:
                print(f"{PASS} node: {node}")
                ok += 1
            else:
                print(f"{FAIL} node MISSING: {node}")
                fail += 1
    except Exception as exc:
        print(f"{FAIL} Could not query object_info: {exc}")
        fail = len(REQUIRED_NODES)
    return ok, fail

def check_models() -> tuple[int, int]:
    ok = fail = 0
    for name, path in REQUIRED_MODELS.items():
        if path.exists():
            size_mb = path.stat().st_size // (1024 * 1024)
            print(f"{PASS} model ({size_mb:,} MB): {name}")
            ok += 1
        else:
            print(f"{FAIL} model MISSING: {name}  [{path}]")
            fail += 1
    return ok, fail

def check_workflows() -> tuple[int, int]:
    ok = fail = 0
    for wf in sorted(WORKFLOW_DIR.glob("*.json")):
        try:
            json.loads(wf.read_text(encoding="utf-8"))
            print(f"{PASS} workflow JSON: {wf.name}")
            ok += 1
        except Exception as exc:
            print(f"{FAIL} workflow JSON: {wf.name}  ({exc})")
            fail += 1
    return ok, fail

def check_scripts() -> tuple[int, int]:
    ok = fail = 0
    for script in PYTHON_SCRIPTS:
        try:
            ast.parse(script.read_text(encoding="utf-8"))
            print(f"{PASS} syntax: {script.name}")
            ok += 1
        except SyntaxError as exc:
            print(f"{FAIL} syntax: {script.name}  ({exc})")
            fail += 1
    return ok, fail

def main() -> None:
    print("=" * 60)
    print("QUAKE LEGACY — ComfyUI Readiness Check")
    print("=" * 60)

    comfy_ok = check_comfyui()
    print()

    if comfy_ok:
        print("--- Nodes ---")
        n_ok, n_fail = check_nodes()
        print()
    else:
        n_ok, n_fail = 0, len(REQUIRED_NODES)

    print("--- Models ---")
    m_ok, m_fail = check_models()
    print()

    print("--- Workflows ---")
    w_ok, w_fail = check_workflows()
    print()

    print("--- Python Scripts ---")
    s_ok, s_fail = check_scripts()
    print()

    total_fail = n_fail + m_fail + w_fail + s_fail
    print("=" * 60)
    print(f"Nodes:     {n_ok}/{n_ok+n_fail}")
    print(f"Models:    {m_ok}/{m_ok+m_fail}")
    print(f"Workflows: {w_ok}/{w_ok+w_fail}")
    print(f"Scripts:   {s_ok}/{s_ok+s_fail}")
    print("=" * 60)

    if total_fail == 0:
        print("ALL CHECKS PASSED — ComfyUI is ready.")
        sys.exit(0)
    else:
        print(f"FAILED: {total_fail} issue(s) need fixing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
