from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app


@pytest.fixture
def tmp_demos(tmp_path, monkeypatch):
    """Point the forge router at a temp directory with 2 fake demos."""
    import creative_suite.api.forge as forge_mod
    d = tmp_path / "demos"
    d.mkdir()
    (d / "CA-player1-asylum-2024_01_01-12_00_00.dm_73").write_bytes(b"\x00" * 1024)
    (d / "CA-player2-campgrounds-2024_01_02-13_00_00.dm_73").write_bytes(b"\x00" * 2048)
    monkeypatch.setattr(forge_mod, "_DEMOS_DIR", d)
    return d


def test_forge_demos_returns_list(tmp_demos):
    client = TestClient(create_app())
    r = client.get("/api/forge/demos")
    assert r.status_code == 200
    data = r.json()
    assert "demos" in data
    assert len(data["demos"]) == 2


def test_forge_demos_item_shape(tmp_demos):
    client = TestClient(create_app())
    r = client.get("/api/forge/demos")
    assert r.status_code == 200
    items = r.json()["demos"]
    item = items[0]
    assert "name" in item
    assert "size_mb" in item
    assert "map" in item
    assert "state" in item
    assert isinstance(item["size_mb"], float)


def test_forge_demos_empty_dir(monkeypatch, tmp_path):
    import creative_suite.api.forge as forge_mod
    empty = tmp_path / "empty_demos"
    empty.mkdir()
    monkeypatch.setattr(forge_mod, "_DEMOS_DIR", empty)
    client = TestClient(create_app())
    r = client.get("/api/forge/demos")
    assert r.status_code == 200
    assert r.json() == {"demos": []}
