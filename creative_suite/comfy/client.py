"""ComfyUI HTTP client — thin wrapper over /prompt, /upload, /view, /history.

Design notes:
- Workflow JSON has `{{placeholder}}` string tokens. `substitute_placeholders`
  walks the graph and replaces them, casting numeric placeholders like
  `{{seed}}` / `{{denoise}}` to int / float so ComfyUI's validator is happy.
- `queue_prompt` uploads the input image, substitutes, POSTs /prompt.
- `fetch_output` pulls the PNG bytes from /view.
- All HTTP lives behind httpx.Client so tests can swap the transport.
"""
from __future__ import annotations

import copy
import json
import uuid
from pathlib import Path
from typing import Any, Mapping

import httpx

DEFAULT_NEGATIVE = (
    "stylized, cartoon, anime, flat shading, low poly, low-resolution, "
    "blurry, jpeg artifacts, text, watermark, signature"
)


def _coerce(key: str, raw: str) -> Any:
    """Numeric placeholders -> int/float; rest stay as str."""
    if key == "seed":
        return int(raw)
    if key in ("denoise", "cfg"):
        return float(raw)
    if key == "steps":
        return int(raw)
    return raw


def substitute_placeholders(
    workflow: Mapping[str, Any], values: Mapping[str, Any]
) -> dict[str, Any]:
    """Recursively replace {{key}} tokens. Returns a new dict."""
    def walk(node: Any) -> Any:
        if isinstance(node, str):
            for key, val in values.items():
                token = f"{{{{{key}}}}}"
                if node == token:
                    return val  # full-replace keeps numeric type
                if token in node:
                    node = node.replace(token, str(val))
            return node
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(x) for x in node]
        return node

    graph = copy.deepcopy(dict(workflow))
    # Strip all template-only keys (anything starting with _) before send
    for key in list(graph.keys()):
        if key.startswith("_"):
            graph.pop(key)
    return walk(graph)  # type: ignore[no-any-return]


class ComfyClient:
    """Blocking httpx client. Each creative_suite worker owns one."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())
        kwargs: dict[str, Any] = {"base_url": self.base_url, "timeout": timeout}
        if transport is not None:
            kwargs["transport"] = transport
        self._http = httpx.Client(**kwargs)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> ComfyClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ------------------------------------------------------------------ #
    # Low-level HTTP
    # ------------------------------------------------------------------ #

    def upload_image(self, path: Path, *, overwrite: bool = True) -> str:
        """POST /upload/image -> returns ComfyUI filename."""
        with path.open("rb") as fh:
            files = {"image": (path.name, fh, "image/png")}
            data = {"overwrite": "true" if overwrite else "false"}
            r = self._http.post("/upload/image", files=files, data=data)
        r.raise_for_status()
        return str(r.json()["name"])

    def queue_prompt(self, graph: Mapping[str, Any]) -> str:
        """POST /prompt -> returns prompt_id (job id)."""
        payload = {"prompt": dict(graph), "client_id": self.client_id}
        r = self._http.post("/prompt", json=payload)
        r.raise_for_status()
        return str(r.json()["prompt_id"])

    def history(self, prompt_id: str) -> dict[str, Any]:
        """GET /history/{id} -> {prompt_id: {outputs: {...}, status: {...}}}"""
        r = self._http.get(f"/history/{prompt_id}")
        r.raise_for_status()
        return dict(r.json())

    def fetch_output(
        self, filename: str, *, subfolder: str = "", type_: str = "output"
    ) -> bytes:
        """GET /view?filename=... -> raw PNG bytes."""
        params = {"filename": filename, "subfolder": subfolder, "type": type_}
        r = self._http.get("/view", params=params)
        r.raise_for_status()
        return r.content

    # ------------------------------------------------------------------ #
    # High-level convenience
    # ------------------------------------------------------------------ #

    def submit_img2img(
        self,
        workflow: Mapping[str, Any],
        input_image_path: Path,
        prompt: str,
        *,
        seed: int,
        denoise: float = 0.35,
        negative_prompt: str = DEFAULT_NEGATIVE,
        extra: Mapping[str, Any] | None = None,
    ) -> str:
        """Upload image, substitute placeholders, queue prompt. Returns job_id.

        Pass `extra` for workflow-specific tokens such as lora_name / lora_strength.
        """
        uploaded_name = self.upload_image(input_image_path)
        placeholders: dict[str, Any] = {
            "input_image": uploaded_name,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": _coerce("seed", str(seed)),
            "denoise": _coerce("denoise", str(denoise)),
        }
        if extra:
            placeholders.update(extra)
        graph = substitute_placeholders(workflow, placeholders)
        return self.queue_prompt(graph)

    def output_filenames(self, prompt_id: str) -> list[dict[str, str]]:
        """Walk history outputs and return each saved image's view params."""
        hist = self.history(prompt_id)
        entry = hist.get(prompt_id, {})
        outputs = entry.get("outputs", {})
        results: list[dict[str, str]] = []
        for _node_id, node_out in outputs.items():
            for image in node_out.get("images", []):
                results.append(
                    {
                        "filename": image.get("filename", ""),
                        "subfolder": image.get("subfolder", ""),
                        "type_": image.get("type", "output"),
                    }
                )
        return results


def load_workflow(path: Path) -> dict[str, Any]:
    """Small helper — load workflow JSON from disk."""
    return dict(json.loads(path.read_text(encoding="utf-8")))


# Required placeholders for every img2img workflow variant. If a future
# ComfyUI update renames node keys and these go missing, we want the app to
# BOOT (so the annotation UI stays alive) and log loudly — never crash.
REQUIRED_PLACEHOLDERS = ("{{input_image}}", "{{prompt}}", "{{seed}}")


def validate_workflow_file(path: Path) -> bool:
    """Spec §11.3 drift mitigation.

    Returns True if the workflow JSON at `path` contains every required
    placeholder token; returns False and logs a warning otherwise. Never
    raises — a missing placeholder should surface at generation time (where
    the failure is actionable), not at boot.
    """
    import logging

    log = logging.getLogger("creative_suite.comfy")
    if not path.exists():
        log.warning("comfy workflow file missing: %s", path)
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("comfy workflow unreadable (%s): %s", path, exc)
        return False
    missing = [tok for tok in REQUIRED_PLACEHOLDERS if tok not in text]
    if missing:
        log.warning(
            "comfy workflow %s missing placeholders: %s — ComfyUI update may "
            "have renamed nodes. Generation will fail until this is fixed.",
            path.name,
            ", ".join(missing),
        )
        return False
    return True
