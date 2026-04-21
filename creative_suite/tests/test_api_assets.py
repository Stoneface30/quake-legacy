from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("PIL")

from PIL import Image  # noqa: E402

from creative_suite.app import create_app  # noqa: E402
from creative_suite.config import Config  # noqa: E402
from creative_suite.db.migrate import migrate  # noqa: E402
from creative_suite.inventory.catalog import build_catalog  # noqa: E402
from creative_suite.inventory.ingest import ingest  # noqa: E402


def _make_ref_pk3(path: Path) -> Path:
    img = Image.new("RGB", (128, 128), (90, 90, 90))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    body = buf.getvalue()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        z.writestr("textures/base_wall/basewall01b.tga", body)
        z.writestr("models/players/visor/lower.tga", body)
        z.writestr("sprites/teleporter01.tga", body)
    return path


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    cfg = Config()
    cfg.ensure_dirs()
    migrate(cfg)
    pk3 = _make_ref_pk3(tmp_path / "ref.pk3")
    ingest(cfg, build_catalog([pk3]))
    return TestClient(create_app())


def test_assets_list_tree_still_returns_categories(client: TestClient) -> None:
    r = client.get("/api/assets")
    assert r.status_code == 200
    body = r.json()
    assert "categories" in body
    assert body["total"] == 3


def test_assets_can_be_filtered_to_flat_category_list(client: TestClient) -> None:
    r = client.get("/api/assets?category=surface")
    assert r.status_code == 200
    body = r.json()
    assert body["category"] == "surface"
    assert len(body["assets"]) == 1
    assert body["assets"][0]["internal_path"] == "textures/base_wall/basewall01b.tga"


def test_assets_support_effect_category_for_sprite_browser(client: TestClient) -> None:
    r = client.get("/api/assets?category=effect")
    assert r.status_code == 200
    body = r.json()
    assert body["category"] == "effect"
    assert len(body["assets"]) == 1
    assert body["assets"][0]["internal_path"] == "sprites/teleporter01.tga"


# ── kind filter (shell-level grouping) ────────────────────────────────────────

def test_assets_kind_filter_returns_flat_assets(client: TestClient) -> None:
    """kind=skins must return the shell-level flat asset list."""
    r = client.get("/api/assets?kind=skins")
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "skins"
    assert isinstance(body["assets"], list)
    assert len(body["assets"]) == 1
    assert body["assets"][0]["internal_path"] == "models/players/visor/lower.tga"


def test_assets_kind_filter_uses_expected_categories(client: TestClient) -> None:
    """kind=sprites must only return effect-category assets from the DB."""
    r = client.get("/api/assets?kind=sprites")
    assert r.status_code == 200
    allowed = {"effect"}  # sprites/* → effect in catalog.py
    for asset in r.json()["assets"][:25]:
        assert asset["category"] in allowed


def test_assets_kind_filter_maps_returns_surface_assets(client: TestClient) -> None:
    """kind=maps must return surface-category (textures/*) assets."""
    r = client.get("/api/assets?kind=maps")
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "maps"
    assert len(body["assets"]) == 1
    assert body["assets"][0]["internal_path"] == "textures/base_wall/basewall01b.tga"


def test_assets_kind_filter_unknown_kind_returns_422(client: TestClient) -> None:
    """Unknown kind must return 422 Unprocessable Entity."""
    r = client.get("/api/assets?kind=bogus")
    assert r.status_code == 422
