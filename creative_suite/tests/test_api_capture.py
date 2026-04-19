"""Task 9.3 — /api/capture/gamestart API lifecycle tests."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app
from creative_suite.capture.gamestart import MAX_QUALITY_CVARS
from creative_suite.config import Config


@pytest.fixture
def client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[TestClient, Config]]:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    cfg = Config()
    cfg.ensure_dirs()
    with TestClient(create_app()) as c:
        yield c, cfg


def test_post_gamestart_writes_cfg_with_all_cvars(client: tuple[TestClient, Config]) -> None:
    c, _ = client
    r = c.post(
        "/api/capture/gamestart",
        json={
            "demo_name": "ref_basewall",
            "seek_clock": "8:52",
            "quit_at": "9:05",
            "fp_view": True,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["fp_view"] is True
    cfg_path = Path(body["cfg_path"])
    assert cfg_path.exists()

    text = cfg_path.read_text(encoding="utf-8")
    for cvar in MAX_QUALITY_CVARS:
        assert cvar in text
    assert "cg_drawGun 1" in text
    assert "seekclock 8:52" in text


def test_post_gamestart_rejects_semicolon_injection(
    client: tuple[TestClient, Config],
) -> None:
    c, _ = client
    r = c.post(
        "/api/capture/gamestart",
        json={
            "demo_name": "d",
            "seek_clock": "0:00",
            "quit_at": "0:05; fs_game baseq3",
            "fp_view": True,
        },
    )
    assert r.status_code == 400


def test_post_gamestart_fl_view_writes_draw_gun_0(
    client: tuple[TestClient, Config],
) -> None:
    c, _ = client
    r = c.post(
        "/api/capture/gamestart",
        json={
            "demo_name": "fl_angle",
            "seek_clock": "0:00",
            "quit_at": "0:05",
            "fp_view": False,
        },
    )
    assert r.status_code == 200
    text = Path(r.json()["cfg_path"]).read_text(encoding="utf-8")
    assert "cg_drawGun 0" in text
    assert "cg_drawGun 1" not in text


def test_write_preview_cfg_uses_degraded_cvars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    from creative_suite.capture.gamestart import PREVIEW_CVARS, write_preview_cfg
    cfg = Config()
    cfg.ensure_dirs()
    path = write_preview_cfg(
        cfg=cfg, demo_name="prv_test",
        seek_clock="0:00", quit_at="0:10", fp_view=True,
    )
    text = path.read_text(encoding="utf-8")
    for cv in PREVIEW_CVARS:
        assert cv in text
    assert "r_customwidth 3840" not in text
    assert "r_mode 4" in text
