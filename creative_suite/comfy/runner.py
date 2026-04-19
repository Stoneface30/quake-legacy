"""Background ComfyUI job runner.

Given a variants row with status='pending', this runner:
  1. Pulls the source asset bytes from its pk3.
  2. Decodes TGA/JPG/PNG via Pillow, re-saves as PNG for ComfyUI's LoadImage.
  3. Calls ComfyClient.submit_img2img with the photoreal workflow.
  4. Polls /history until the job completes.
  5. Fetches the output PNG and writes it to
     storage/variants/{asset_id}/{variant_id}.png.
  6. Updates the variants row (png_path, width, height, keeps status='pending'
     until user approves/rejects in Task 6).

No asyncio — this is fire-and-forget on a thread pool. Tests call run_job()
synchronously with a mock-transport ComfyClient.
"""
from __future__ import annotations

import io
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from creative_suite.comfy.client import (
    ComfyClient,
    load_workflow,
)
from creative_suite.config import Config


@dataclass(frozen=True)
class JobSpec:
    variant_id: int
    asset_id: int
    source_pk3: str
    internal_path: str
    final_prompt: str
    seed: int
    denoise: float


WORKFLOW_PATH = (
    Path(__file__).parent / "workflows" / "img2img_sdxl.json"
)


def extract_asset_to_png(
    source_pk3: str, internal_path: str, out_png: Path
) -> tuple[int, int]:
    """Pull asset bytes from pk3, decode, write PNG. Returns (w, h)."""
    from PIL import Image  # late import so pytest.importorskip can gate

    with zipfile.ZipFile(source_pk3) as z:
        raw = z.read(internal_path)
    img = Image.open(io.BytesIO(raw))
    img = img.convert("RGBA") if img.mode in ("P", "LA") else img.convert("RGB")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png, format="PNG")
    return img.width, img.height


def run_job(
    spec: JobSpec,
    cfg: Config,
    *,
    comfy: ComfyClient,
    update_variant: Callable[[int, dict[str, Any]], None],
    poll_interval: float = 0.5,
    timeout: float = 300.0,
) -> Path:
    """Runs a single ComfyUI job synchronously. Returns the output PNG path.

    Arguments:
      spec           — variant row snapshot (no live DB handle passed in).
      cfg            — paths + URLs.
      comfy          — pre-built ComfyClient (real or MockTransport).
      update_variant — callback that writes partial state back to SQLite.
                       Called as update_variant(variant_id, {"png_path": ..., ...}).
      poll_interval  — history poll delay (s).
      timeout        — total wait cap (s).

    Raises:
      TimeoutError if ComfyUI never reports output within timeout.
      RuntimeError if the job errors out.
    """
    workflow = load_workflow(WORKFLOW_PATH)

    # Step 1: extract source asset to a PNG ComfyUI can upload.
    input_dir = cfg.variants_dir / str(spec.asset_id) / "_input"
    input_dir.mkdir(parents=True, exist_ok=True)
    input_png = input_dir / f"{spec.variant_id}_in.png"
    in_w, in_h = extract_asset_to_png(spec.source_pk3, spec.internal_path, input_png)

    update_variant(
        spec.variant_id,
        {"width": in_w, "height": in_h},  # seed width/height from source
    )

    # Step 2: submit.
    job_id = comfy.submit_img2img(
        workflow,
        input_png,
        prompt=spec.final_prompt,
        seed=spec.seed,
        denoise=spec.denoise,
    )
    update_variant(spec.variant_id, {"comfy_job_id": job_id})

    # Step 3: poll /history.
    deadline = time.monotonic() + timeout
    outputs: list[dict[str, str]] = []
    while time.monotonic() < deadline:
        outputs = comfy.output_filenames(job_id)
        if outputs:
            break
        time.sleep(poll_interval)
    else:
        raise TimeoutError(f"ComfyUI job {job_id} timed out after {timeout}s")

    # Step 4: fetch PNG, write to storage.
    first = outputs[0]
    png_bytes = comfy.fetch_output(
        first["filename"],
        subfolder=first.get("subfolder", ""),
        type_=first.get("type_", "output"),
    )
    out_png = cfg.variants_dir / str(spec.asset_id) / f"{spec.variant_id}.png"
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out_png.write_bytes(png_bytes)

    # Step 5: decode dimensions of OUTPUT (SDXL produces ~1024^2 regardless
    # of source), update row. status stays 'pending' until Task 6 approval.
    try:
        from PIL import Image
        with Image.open(io.BytesIO(png_bytes)) as out_img:
            out_w, out_h = out_img.width, out_img.height
    except Exception:
        out_w, out_h = in_w, in_h

    update_variant(
        spec.variant_id,
        {
            "png_path": str(out_png),
            "width": out_w,
            "height": out_h,
        },
    )
    return out_png
