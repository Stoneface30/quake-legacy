"""Task 9.1 — /api/ollama/suggest API lifecycle tests.

Uses MockTransport OllamaClient seeded onto ``app.state.ollama_client``
so no real 11434 traffic. Covers:
  - happy path → 200 with 3 suggestions
  - unknown asset → 404
  - asset without image on disk → 409
  - Ollama down → 503 with {"error":"unavailable"}
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any, Iterator

import httpx
import pytest

pytest.importorskip("PIL")

from PIL import Image  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from creative_suite.app import create_app  # noqa: E402
from creative_suite.config import Config  # noqa: E402
from creative_suite.db.migrate import connect, migrate  # noqa: E402
from creative_suite.inventory.catalog import build_catalog  # noqa: E402
from creative_suite.inventory.ingest import ingest  # noqa: E402
from creative_suite.ollama.client import OllamaClient  # noqa: E402


def _make_ref_pk3(path: Path) -> Path:
    img = Image.new("RGB", (128, 128), (90, 90, 90))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        z.writestr("textures/base_wall/basewall01b.tga", buf.getvalue())
    return path


def _seed_asset_thumbnail(cfg: Config) -> int:
    """Ingest creates the assets row; we fake a thumbnail file on disk
    so _read_asset_bytes has something to hand to Ollama."""
    with connect(cfg) as con:
        row = con.execute(
            "SELECT id FROM assets WHERE internal_path = "
            "'textures/base_wall/basewall01b.tga'"
        ).fetchone()
        assert row is not None
        asset_id = int(row["id"])
        thumb = cfg.thumbnails_dir / f"{asset_id}.png"
        Image.new("RGB", (64, 64), (120, 120, 120)).save(thumb, format="PNG")
        con.execute(
            "UPDATE assets SET thumbnail_path = ? WHERE id = ?",
            (str(thumb), asset_id),
        )
    return asset_id


@pytest.fixture
def app_with_asset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[TestClient, Config, int]]:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    cfg = Config()
    cfg.ensure_dirs()
    migrate(cfg)
    pk3 = _make_ref_pk3(tmp_path / "ref.pk3")
    ingest(cfg, build_catalog([pk3]))
    asset_id = _seed_asset_thumbnail(cfg)

    app = create_app()

    with TestClient(app) as client:
        yield client, cfg, asset_id


def _set_mock_ollama(client: TestClient, handler: Any) -> None:
    client.app.state.ollama_client = OllamaClient(  # type: ignore[attr-defined]
        transport=httpx.MockTransport(handler)
    )


def test_suggest_returns_three_chips(app_with_asset: Any) -> None:
    client, _, asset_id = app_with_asset

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "response": json.dumps(
                    ["wet concrete", "industrial panel", "weathered steel"]
                ),
                "done": True,
            },
        )

    _set_mock_ollama(client, handler)

    r = client.post("/api/ollama/suggest", json={"asset_id": asset_id})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["asset_id"] == asset_id
    assert body["category"] == "surface"
    assert len(body["suggestions"]) == 3


def test_suggest_returns_503_when_ollama_down(app_with_asset: Any) -> None:
    client, _, asset_id = app_with_asset

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("ollama not running", request=request)

    _set_mock_ollama(client, handler)

    r = client.post("/api/ollama/suggest", json={"asset_id": asset_id})
    assert r.status_code == 503
    assert r.json()["detail"]["error"] == "unavailable"


def test_suggest_404_on_missing_asset(app_with_asset: Any) -> None:
    client, _, _ = app_with_asset

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "[]", "done": True})

    _set_mock_ollama(client, handler)
    r = client.post("/api/ollama/suggest", json={"asset_id": 999999})
    assert r.status_code == 404


def test_suggest_409_when_asset_has_no_image_on_disk(app_with_asset: Any) -> None:
    client, cfg, asset_id = app_with_asset
    # Blank the thumbnail path so _read_asset_bytes has no file to read.
    with connect(cfg) as con:
        con.execute(
            "UPDATE assets SET thumbnail_path = NULL, extracted_path = NULL "
            "WHERE id = ?",
            (asset_id,),
        )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "[]", "done": True})

    _set_mock_ollama(client, handler)
    r = client.post("/api/ollama/suggest", json={"asset_id": asset_id})
    assert r.status_code == 409
