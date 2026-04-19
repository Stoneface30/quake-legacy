"""Tests for the /api/md3/{id} endpoint (Task 4)."""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app
from creative_suite.config import Config
from creative_suite.db.migrate import connect, migrate

MD3_SAMPLE_BYTES = b"IDP3" + b"\x00" * 120  # magic + filler (not a valid mesh — bytes are all we need)


def _insert_asset(
    cfg: Config,
    *,
    category: str,
    internal_path: str,
    source_pk3: str = "",
    extracted_path: str | None = None,
) -> int:
    checksum = hashlib.sha1(internal_path.encode()).hexdigest()
    with connect(cfg) as con:
        cur = con.execute(
            "INSERT INTO assets (category, subcategory, source_pk3, internal_path, "
            "checksum, extracted_path) VALUES (?, ?, ?, ?, ?, ?)",
            (category, None, source_pk3, internal_path, checksum, extracted_path),
        )
        last_id = cur.lastrowid
        assert last_id is not None
        return int(last_id)


def _cfg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path))
    cfg = Config()
    migrate(cfg)
    return cfg


def test_md3_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg(tmp_path, monkeypatch)
    md3_file = tmp_path / "rocketl.md3"
    md3_file.write_bytes(MD3_SAMPLE_BYTES)
    asset_id = _insert_asset(
        cfg,
        category="model",
        internal_path="models/weapons2/rocketl/rocketl.md3",
        extracted_path=str(md3_file),
    )

    c = TestClient(create_app())
    r = c.get(f"/api/md3/{asset_id}")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/octet-stream")
    assert r.content == MD3_SAMPLE_BYTES


def test_md3_ok_from_pk3_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When extracted_path is missing, fall back to pk3 zip read."""
    cfg = _cfg(tmp_path, monkeypatch)
    pk3 = tmp_path / "fake.pk3"
    internal = "models/weapons2/rocketl/rocketl.md3"
    with zipfile.ZipFile(pk3, "w") as z:
        z.writestr(internal, MD3_SAMPLE_BYTES)
    asset_id = _insert_asset(
        cfg,
        category="model",
        internal_path=internal,
        source_pk3=str(pk3),
        extracted_path=None,
    )

    c = TestClient(create_app())
    r = c.get(f"/api/md3/{asset_id}")
    assert r.status_code == 200, r.text
    assert r.content == MD3_SAMPLE_BYTES


def test_md3_wrong_type_404(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg(tmp_path, monkeypatch)
    asset_id = _insert_asset(
        cfg,
        category="texture",
        internal_path="textures/base_wall/basewall01bit.tga",
        extracted_path=None,
    )

    c = TestClient(create_app())
    r = c.get(f"/api/md3/{asset_id}")
    assert r.status_code == 404


def test_md3_missing_file_404(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg(tmp_path, monkeypatch)
    asset_id = _insert_asset(
        cfg,
        category="model",
        internal_path="models/weapons2/rocketl/rocketl.md3",
        source_pk3=str(tmp_path / "nope.pk3"),  # does not exist
        extracted_path=str(tmp_path / "also_nope.md3"),  # does not exist
    )

    c = TestClient(create_app())
    r = c.get(f"/api/md3/{asset_id}")
    assert r.status_code == 404


def test_md3_unknown_asset_404(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _cfg(tmp_path, monkeypatch)
    c = TestClient(create_app())
    r = c.get("/api/md3/999999")
    assert r.status_code == 404
