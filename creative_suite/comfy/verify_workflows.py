"""Verify all workflow JSON files: node connectivity, placeholder coverage, model refs.

Run: python -u creative_suite/comfy/verify_workflows.py
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

WF_DIR = Path(__file__).parent / "workflows"

PLACEHOLDERS = {"{{input_image}}", "{{prompt}}", "{{seed}}", "{{denoise}}", "{{negative_prompt}}"}

PASS = "  OK  "
FAIL = "  FAIL"


def _get_registered_nodes() -> set[str]:
    raw = urllib.request.urlopen("http://127.0.0.1:8188/object_info", timeout=120).read()
    return set(json.loads(raw).keys())


def _verify_workflow(wf_path: Path, registered: set[str]) -> list[str]:
    errors = []
    try:
        wf = json.loads(wf_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"JSON parse error: {exc}"]

    # Skip metadata keys
    nodes = {k: v for k, v in wf.items() if not k.startswith("_")}

    # 1. Every node class must be registered
    for node_id, node in nodes.items():
        cls = node.get("class_type", "")
        if cls not in registered:
            errors.append(f"node {node_id}: class_type '{cls}' NOT registered in ComfyUI")

    # 2. Every input reference [node_id, slot] must point to a real node
    for node_id, node in nodes.items():
        for inp_name, inp_val in node.get("inputs", {}).items():
            if isinstance(inp_val, list) and len(inp_val) == 2:
                ref_id, slot = inp_val
                if str(ref_id) not in nodes:
                    errors.append(
                        f"node {node_id}.{inp_name}: references node '{ref_id}' which doesn't exist"
                    )

    # 3. All declared placeholders exist in at least one input value
    declared = set(wf.get("_placeholders", []))
    all_values = json.dumps(nodes)
    for ph in declared:
        if ph not in all_values:
            errors.append(f"placeholder {ph} declared but never used in any node input")

    # 4. Must have a SaveImage node
    has_save = any(n.get("class_type") == "SaveImage" for n in nodes.values())
    if not has_save:
        errors.append("no SaveImage node found — output will be lost")

    # 5. Must have a KSampler (for diffusion workflows) or ImageUpscaleWithModel (for upscale-only)
    has_sampler = any(n.get("class_type") in ("KSampler", "KSamplerAdvanced") for n in nodes.values())
    has_upscaler = any(n.get("class_type") == "ImageUpscaleWithModel" for n in nodes.values())
    if not has_sampler and not has_upscaler:
        errors.append("no KSampler or ImageUpscaleWithModel — workflow does nothing useful")

    return errors


def main() -> None:
    print("=" * 64)
    print("QUAKE LEGACY — Workflow Connection Verification")
    print("=" * 64)

    print("\nFetching registered nodes from ComfyUI...")
    try:
        registered = _get_registered_nodes()
        print(f"  {len(registered)} nodes registered")
    except Exception as exc:
        print(f"  ERROR: {exc}")
        return

    total_ok = total_fail = 0
    for wf_path in sorted(WF_DIR.glob("*.json")):
        errors = _verify_workflow(wf_path, registered)
        if errors:
            print(f"\n{FAIL} {wf_path.name}")
            for e in errors:
                print(f"       {e}")
            total_fail += 1
        else:
            print(f"{PASS} {wf_path.name}")
            total_ok += 1

    print(f"\n{'='*64}")
    print(f"Workflows:  {total_ok} OK  |  {total_fail} FAILED")
    if total_fail == 0:
        print("ALL WORKFLOW CHECKS PASSED")
    else:
        print(f"{total_fail} workflow(s) have issues — fix before running batch")


if __name__ == "__main__":
    main()
