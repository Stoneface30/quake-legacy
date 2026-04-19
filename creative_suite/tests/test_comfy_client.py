"""Task 5 — ComfyUI client unit tests (httpx MockTransport).

Covers:
- Placeholder substitution (numeric coercion + nested lists).
- upload_image returns server's filename.
- queue_prompt returns prompt_id.
- submit_img2img end-to-end sequence.
- fetch_output returns raw bytes.
- output_filenames parses /history payload.

Reference smoke asset: textures/base_wall/basewall01b.tga — we only test the
placeholder wiring here, not a live ComfyUI. Live smoke is Step 5.4 (manual).
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from creative_suite.comfy.client import (
    ComfyClient,
    load_workflow,
    substitute_placeholders,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / "creative_suite" / "comfy" / "workflows" / "img2img_sdxl.json"


# ---------------------------------------------------------------------- #
# Placeholder substitution
# ---------------------------------------------------------------------- #

def test_substitute_coerces_seed_to_int() -> None:
    wf = load_workflow(WORKFLOW_PATH)
    graph = substitute_placeholders(
        wf,
        {
            "input_image": "ref.png",
            "prompt": "wet concrete",
            "negative_prompt": "blurry",
            "seed": 12345,
            "denoise": 0.35,
        },
    )
    # KSampler is node "6"
    ks = graph["6"]["inputs"]
    assert ks["seed"] == 12345
    assert isinstance(ks["seed"], int)
    assert ks["denoise"] == 0.35
    assert isinstance(ks["denoise"], float)
    # Template-only keys stripped
    assert "_template_version" not in graph
    assert "_placeholders" not in graph


def test_substitute_writes_prompt_and_image() -> None:
    wf = load_workflow(WORKFLOW_PATH)
    graph = substitute_placeholders(
        wf,
        {
            "input_image": "basewall01b.png",
            "prompt": "heavy wet concrete",
            "negative_prompt": "stylized",
            "seed": 42,
            "denoise": 0.35,
        },
    )
    assert graph["2"]["inputs"]["image"] == "basewall01b.png"
    assert graph["4"]["inputs"]["text"] == "heavy wet concrete"
    assert graph["5"]["inputs"]["text"] == "stylized"


def test_substitute_leaves_non_placeholder_strings_alone() -> None:
    wf = load_workflow(WORKFLOW_PATH)
    graph = substitute_placeholders(
        wf,
        {
            "input_image": "x.png",
            "prompt": "p",
            "negative_prompt": "n",
            "seed": 1,
            "denoise": 0.3,
        },
    )
    # sampler_name / scheduler must survive untouched
    assert graph["6"]["inputs"]["sampler_name"] == "dpmpp_2m_sde_gpu"
    assert graph["6"]["inputs"]["scheduler"] == "karras"


# ---------------------------------------------------------------------- #
# ComfyClient via MockTransport
# ---------------------------------------------------------------------- #

def _make_transport(handler):  # type: ignore[no-untyped-def]
    return httpx.MockTransport(handler)


def test_upload_image_returns_server_name(tmp_path: Path) -> None:
    ref = tmp_path / "basewall01b.png"
    ref.write_bytes(b"\x89PNG\r\n\x1a\nfakepng")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/upload/image"
        assert request.method == "POST"
        return httpx.Response(200, json={"name": "basewall01b.png", "subfolder": "", "type": "input"})

    with ComfyClient(transport=_make_transport(handler)) as client:
        assert client.upload_image(ref) == "basewall01b.png"


def test_queue_prompt_returns_job_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/prompt"
        payload = json.loads(request.content.decode())
        assert "prompt" in payload and "client_id" in payload
        return httpx.Response(200, json={"prompt_id": "job-abc-123"})

    with ComfyClient(transport=_make_transport(handler)) as client:
        assert client.queue_prompt({"1": {}}) == "job-abc-123"


def test_submit_img2img_full_sequence(tmp_path: Path) -> None:
    ref = tmp_path / "basewall01b.png"
    ref.write_bytes(b"fakepng")
    wf = load_workflow(WORKFLOW_PATH)

    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/upload/image":
            return httpx.Response(200, json={"name": "basewall01b.png"})
        if request.url.path == "/prompt":
            body = json.loads(request.content.decode())
            assert body["prompt"]["2"]["inputs"]["image"] == "basewall01b.png"
            assert body["prompt"]["6"]["inputs"]["seed"] == 777
            return httpx.Response(200, json={"prompt_id": "job-xyz"})
        raise AssertionError(f"unexpected path {request.url.path}")

    with ComfyClient(transport=_make_transport(handler)) as client:
        job_id = client.submit_img2img(
            wf, ref, prompt="heavy wet concrete", seed=777, denoise=0.35
        )
    assert job_id == "job-xyz"
    assert calls == ["/upload/image", "/prompt"]


def test_fetch_output_returns_raw_bytes() -> None:
    png_bytes = b"\x89PNG\r\n\x1a\nfakedata"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/view"
        assert request.url.params["filename"] == "variant_00001_.png"
        return httpx.Response(200, content=png_bytes)

    with ComfyClient(transport=_make_transport(handler)) as client:
        assert client.fetch_output("variant_00001_.png") == png_bytes


def test_output_filenames_parses_history() -> None:
    hist_payload = {
        "job-xyz": {
            "outputs": {
                "8": {
                    "images": [
                        {
                            "filename": "variant_00001_.png",
                            "subfolder": "creative_suite",
                            "type": "output",
                        }
                    ]
                }
            }
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/history/job-xyz"
        return httpx.Response(200, json=hist_payload)

    with ComfyClient(transport=_make_transport(handler)) as client:
        rows = client.output_filenames("job-xyz")
    assert rows == [
        {
            "filename": "variant_00001_.png",
            "subfolder": "creative_suite",
            "type_": "output",
        }
    ]


def test_workflow_placeholders_enumerated() -> None:
    """Sanity: workflow JSON declares its own placeholder list, matches reality."""
    wf = load_workflow(WORKFLOW_PATH)
    declared = set(wf.get("_placeholders", []))
    flat = json.dumps(wf)
    for token in declared:
        assert token in flat, f"placeholder {token} declared but missing in graph"
