"""API contract tests for /api/parts (Task 2, plan step 2.3)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path))
    return TestClient(create_app())


def _with_phase1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, Path, Path]:
    """Build a throw-away app whose phase1 paths live under tmp_path."""
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    lists_dir = tmp_path / "phase1_clip_lists"
    lists_dir.mkdir()

    # Monkeypatch Config properties to point at tmp dirs.
    from creative_suite.config import Config

    monkeypatch.setattr(
        Config, "phase1_output_dir",
        property(lambda _self: out_dir),
    )
    monkeypatch.setattr(
        Config, "phase1_clip_lists",
        property(lambda _self: lists_dir),
    )
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    client = TestClient(create_app())
    return client, out_dir, lists_dir


def test_lists_empty_when_no_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _out, _lists = _with_phase1(tmp_path, monkeypatch)
    r = client.get("/api/parts")
    assert r.status_code == 200
    assert r.json() == []


def test_lists_exact_partN_mp4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, out, _lists = _with_phase1(tmp_path, monkeypatch)
    (out / "Part4.mp4").write_bytes(b"x")
    r = client.get("/api/parts").json()
    assert len(r) == 1
    assert r[0]["part"] == 4
    assert r[0]["mp4_name"] == "Part4.mp4"
    assert r[0]["mp4_url"] == "/media/Part4.mp4"
    assert r[0]["has_manifest"] is False


def test_lists_review_build_when_no_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Part4_v10_3_review.mp4 must surface as part=4 when Part4.mp4 is absent."""
    client, out, _lists = _with_phase1(tmp_path, monkeypatch)
    (out / "Part4_v10_3_review.mp4").write_bytes(b"x")
    r = client.get("/api/parts").json()
    assert len(r) == 1
    assert r[0]["part"] == 4
    assert r[0]["mp4_name"] == "Part4_v10_3_review.mp4"


def test_exact_mp4_wins_over_review_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, out, _lists = _with_phase1(tmp_path, monkeypatch)
    (out / "Part4_v10_3_review.mp4").write_bytes(b"x")
    (out / "Part4.mp4").write_bytes(b"x")
    r = client.get("/api/parts").json()
    assert len(r) == 1 and r[0]["mp4_name"] == "Part4.mp4"


def test_reports_manifest_clip_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, out, _lists = _with_phase1(tmp_path, monkeypatch)
    (out / "Part4.mp4").write_bytes(b"x")
    cl = tmp_path / "custom_clip_list.txt"
    cl.write_text("file 'Demo (1) - 2.avi'\n")
    (out / "Part4.render_manifest.json").write_text(json.dumps({
        "mp4": str(out / "Part4.mp4"),
        "clip_list": str(cl),
    }))
    r = client.get("/api/parts").json()
    assert r[0]["has_manifest"] is True
    assert r[0]["clip_list"] == str(cl)


def test_falls_back_to_styleb_clip_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, out, lists = _with_phase1(tmp_path, monkeypatch)
    (out / "Part4.mp4").write_bytes(b"x")
    styleb = lists / "part04_styleb.txt"
    styleb.write_text("Demo (1) - 2.avi\n")
    r = client.get("/api/parts").json()
    assert r[0]["has_manifest"] is False
    assert r[0]["clip_list"] == str(styleb)
