"""Task 3 — catalog + ingest + tree API tests.

Uses a hand-built tiny pk3 fixture so tests don't depend on a Steam install.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app
from creative_suite.config import Config
from creative_suite.inventory.catalog import (
    _classify,  # pyright: ignore[reportPrivateUsage]
    build_catalog,
    load_or_build_catalog,
    walk_pk3,
)
from creative_suite.inventory.ingest import ingest


def _make_fixture_pk3(path: Path) -> Path:
    """Create a pk3 with 4 minimal assets covering all four categories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        z.writestr("textures/base_wall/basewall01bit.tga", b"\x00" * 64)
        z.writestr("models/weapons2/rocketl/rocketl.md3", b"IDP3" + b"\x00" * 60)
        z.writestr("models/players/keel/upper.md3", b"IDP3" + b"\x00" * 60)
        z.writestr("gfx/2d/backtile.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 60)
        z.writestr("sound/weapons/rocket/rocklf1a.wav", b"RIFF" + b"\x00" * 60)  # ignored
    return path


def test_classify_surfaces() -> None:
    cat, sub = _classify("textures/base_wall/basewall01bit.tga")
    assert cat == "surface"
    assert sub == "base_wall"


def test_classify_weapon() -> None:
    cat, sub = _classify("models/weapons2/rocketl/rocketl.md3")
    assert cat == "weapon"
    assert sub == "rocketl"


def test_classify_skin() -> None:
    cat, sub = _classify("models/players/keel/upper.md3")
    assert cat == "skin"
    assert sub == "keel"


def test_classify_gfx_and_effect() -> None:
    assert _classify("gfx/2d/backtile.jpg")[0] == "gfx"
    assert _classify("sprites/smoke.tga")[0] == "effect"
    assert _classify("env/foo/ft.jpg")[0] == "effect"


def test_walk_pk3_skips_sounds(tmp_path: Path) -> None:
    pk3 = _make_fixture_pk3(tmp_path / "fixture.pk3")
    entries = list(walk_pk3(pk3))
    # 4 allowed extensions, sound file excluded
    assert len(entries) == 4
    paths = {e.internal_path for e in entries}
    assert "sound/weapons/rocket/rocklf1a.wav" not in paths


def test_ref_asset_visible_in_catalog(tmp_path: Path) -> None:
    pk3 = _make_fixture_pk3(tmp_path / "fixture.pk3")
    entries = build_catalog([pk3])
    hits = [e for e in entries if "basewall01bit" in e.internal_path]
    assert len(hits) == 1
    assert hits[0].category == "surface"
    assert hits[0].subcategory == "base_wall"


def test_ingest_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    cfg = Config()
    cfg.ensure_dirs()
    # Migrate the DB
    from creative_suite.db.migrate import migrate
    migrate(cfg)

    pk3 = _make_fixture_pk3(tmp_path / "fixture.pk3")
    entries = build_catalog([pk3])

    first = ingest(cfg, entries)
    assert first == 4  # four new
    second = ingest(cfg, entries)
    assert second == 0  # all dupes


def test_load_or_build_honors_json(tmp_path: Path) -> None:
    pk3 = _make_fixture_pk3(tmp_path / "fixture.pk3")
    # Write a FULL_CATALOG.json with just 1 entry
    j = tmp_path / "cat.json"
    j.write_text(json.dumps({
        "entries": [
            {"category": "surface", "subcategory": "base_wall",
             "source_pk3": str(pk3), "internal_path": "textures/base_wall/basewall01bit.tga",
             "checksum": "abc", "size": 64},
        ]
    }), encoding="utf-8")
    entries = load_or_build_catalog(j, [pk3])
    assert len(entries) == 1  # JSON wins over pk3


def test_tree_api_exposes_ref_asset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    cfg = Config()
    cfg.ensure_dirs()
    from creative_suite.db.migrate import migrate
    migrate(cfg)

    pk3 = _make_fixture_pk3(tmp_path / "fixture.pk3")
    entries = build_catalog([pk3])
    ingest(cfg, entries)

    client = TestClient(create_app())
    r = client.get("/api/assets")
    assert r.status_code == 200
    tree = r.json()
    assert tree["total"] == 4
    # ref asset is reachable
    paths = [
        a["internal_path"]
        for c in tree["categories"]
        for s in c["subcategories"]
        for a in s["assets"]
    ]
    assert "textures/base_wall/basewall01bit.tga" in paths


def test_raw_endpoint_returns_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    cfg = Config()
    cfg.ensure_dirs()
    from creative_suite.db.migrate import migrate
    migrate(cfg)

    pk3 = _make_fixture_pk3(tmp_path / "fixture.pk3")
    ingest(cfg, build_catalog([pk3]))

    client = TestClient(create_app())
    # find id of the ref asset
    tree = client.get("/api/assets").json()
    ref_id = next(
        a["id"]
        for c in tree["categories"]
        for s in c["subcategories"]
        for a in s["assets"]
        if a["internal_path"] == "textures/base_wall/basewall01bit.tga"
    )
    r = client.get(f"/api/assets/{ref_id}/raw")
    assert r.status_code == 200
    assert len(r.content) == 64  # fixture wrote 64 bytes
