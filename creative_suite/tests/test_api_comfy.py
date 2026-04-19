"""Task 5 — /api/comfy/queue + /api/variants integration tests.

Smoke: queue a variant for the reference surface texture, drive the runner
synchronously with a MockTransport ComfyClient, then verify:
  - variants row persisted with final_prompt, seed, png_path
  - /api/comfy/status/{variant_id} returns status + png_url
  - /api/variants?asset_id=... lists the variant
  - /api/variants/{id}/png serves raw bytes
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest

pytest.importorskip("PIL")

from PIL import Image  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from creative_suite.app import create_app  # noqa: E402
from creative_suite.comfy.client import ComfyClient  # noqa: E402
from creative_suite.config import Config  # noqa: E402
from creative_suite.db.migrate import connect, migrate  # noqa: E402
from creative_suite.inventory.catalog import build_catalog  # noqa: E402
from creative_suite.inventory.ingest import ingest  # noqa: E402


# ---------------------------------------------------------------------- #
# Fixtures
# ---------------------------------------------------------------------- #

FAKE_OUTPUT_PNG = io.BytesIO()
Image.new("RGB", (1024, 1024), (200, 120, 80)).save(FAKE_OUTPUT_PNG, format="PNG")
FAKE_OUTPUT_BYTES = FAKE_OUTPUT_PNG.getvalue()


def _make_ref_pk3(path: Path) -> Path:
    """Mini pk3 with textures/base_wall/basewall01b.tga (the spec's ref asset)."""
    img = Image.new("RGB", (128, 128), (90, 90, 90))
    buf = io.BytesIO()
    img.save(buf, format="PNG")  # LoadImage accepts any pillow-decodable
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        z.writestr("textures/base_wall/basewall01b.tga", buf.getvalue())
    return path


def _mock_comfy_handler() -> httpx.MockTransport:
    """Pretends to be ComfyUI: upload echoes filename, /prompt returns id,
    /history returns one output, /view returns the fake PNG bytes."""
    state: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/upload/image":
            return httpx.Response(200, json={"name": "ref_in.png"})
        if path == "/prompt":
            body = json.loads(request.content.decode())
            state["job"] = "job-smoke-1"
            state["seed_seen"] = str(body["prompt"]["6"]["inputs"]["seed"])
            return httpx.Response(200, json={"prompt_id": "job-smoke-1"})
        if path.startswith("/history/"):
            return httpx.Response(
                200,
                json={
                    "job-smoke-1": {
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
                },
            )
        if path == "/view":
            return httpx.Response(200, content=FAKE_OUTPUT_BYTES)
        raise AssertionError(f"unexpected {request.method} {path}")

    return httpx.MockTransport(handler)


@pytest.fixture
def configured_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """FastAPI app with isolated storage + one reference asset ingested."""
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    cfg = Config()
    cfg.ensure_dirs()
    migrate(cfg)

    pk3 = _make_ref_pk3(tmp_path / "ref.pk3")
    ingest(cfg, build_catalog([pk3]))

    app = create_app()
    # Inject mock ComfyClient + force runner to run inline in the request.
    app.state.comfy_client = ComfyClient(transport=_mock_comfy_handler())
    app.state.comfy_run_sync = True

    with connect(cfg) as con:
        row = con.execute(
            "SELECT id FROM assets WHERE internal_path = "
            "'textures/base_wall/basewall01b.tga'"
        ).fetchone()
    assert row is not None, "reference asset should be ingested"
    asset_id = int(row["id"])

    with TestClient(app) as client:
        yield client, cfg, asset_id


# ---------------------------------------------------------------------- #
# Tests
# ---------------------------------------------------------------------- #

def test_queue_creates_variant_and_writes_png(configured_app) -> None:  # type: ignore[no-untyped-def]
    client, cfg, asset_id = configured_app
    r = client.post(
        "/api/comfy/queue",
        json={"asset_id": asset_id, "user_prompt": "heavy wet concrete", "seed": 777},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["asset_id"] == asset_id
    assert body["seed"] == 777
    assert "photorealistic" in body["final_prompt"]
    assert "heavy wet concrete" in body["final_prompt"]
    variant_id = body["variant_id"]

    # Output PNG written
    out_png = cfg.variants_dir / str(asset_id) / f"{variant_id}.png"
    assert out_png.exists()
    assert out_png.read_bytes() == FAKE_OUTPUT_BYTES


def test_queue_rejects_missing_asset(configured_app) -> None:  # type: ignore[no-untyped-def]
    client, _cfg, _aid = configured_app
    r = client.post(
        "/api/comfy/queue", json={"asset_id": 999999, "user_prompt": "x", "seed": 1}
    )
    assert r.status_code == 404


def test_status_returns_variant_after_completion(configured_app) -> None:  # type: ignore[no-untyped-def]
    client, _cfg, asset_id = configured_app
    r = client.post(
        "/api/comfy/queue", json={"asset_id": asset_id, "user_prompt": "", "seed": 42}
    )
    vid = r.json()["variant_id"]

    s = client.get(f"/api/comfy/status/{vid}")
    assert s.status_code == 200
    data = s.json()
    assert data["id"] == vid
    assert data["status"] == "pending"
    assert data["png_url"] == f"/api/variants/{vid}/png"
    assert data["width"] == 1024  # from fake output
    assert data["comfy_job_id"] == "job-smoke-1"


def test_list_variants_by_asset(configured_app) -> None:  # type: ignore[no-untyped-def]
    client, _cfg, asset_id = configured_app
    client.post(
        "/api/comfy/queue", json={"asset_id": asset_id, "user_prompt": "a", "seed": 1}
    )
    client.post(
        "/api/comfy/queue", json={"asset_id": asset_id, "user_prompt": "b", "seed": 2}
    )
    r = client.get(f"/api/variants?asset_id={asset_id}")
    assert r.status_code == 200
    rows = r.json()["variants"]
    assert len(rows) == 2
    assert rows[0]["seed"] in (1, 2)
    assert rows[0]["png_url"] is not None


def test_variant_png_served(configured_app) -> None:  # type: ignore[no-untyped-def]
    client, _cfg, asset_id = configured_app
    r = client.post(
        "/api/comfy/queue", json={"asset_id": asset_id, "user_prompt": "", "seed": 9}
    )
    vid = r.json()["variant_id"]
    p = client.get(f"/api/variants/{vid}/png")
    assert p.status_code == 200
    assert p.headers["content-type"] == "image/png"
    assert p.content == FAKE_OUTPUT_BYTES


def test_seed_prompt_contains_photoreal_keywords(configured_app) -> None:  # type: ignore[no-untyped-def]
    client, _cfg, asset_id = configured_app
    r = client.post(
        "/api/comfy/queue",
        json={"asset_id": asset_id, "user_prompt": "rusted steel plating", "seed": 3},
    )
    fp = r.json()["final_prompt"]
    assert "photorealistic PBR material" in fp
    assert "rusted steel plating" in fp
