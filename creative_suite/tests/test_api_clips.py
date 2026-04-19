"""API contract tests for /api/clips/resolve (Task 2, plan step 2.4)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app


def _client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, Path, Path]:
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    lists_dir = tmp_path / "phase1_clip_lists"
    lists_dir.mkdir()

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


def _stub_durations(
    monkeypatch: pytest.MonkeyPatch,
    durations_by_filename: dict[str, float],
) -> None:
    """Short-circuit ffprobe for tests — filename → fixed duration."""
    from creative_suite.api import clips as clips_api

    def _fake_find(filename: str, _search_roots: list[Path]) -> Path | None:
        # Return a Path in current dir. probe_duration is also stubbed out.
        return Path(filename)

    def _fake_probe(_cfg: object, path: Path) -> float:
        return durations_by_filename.get(path.name, 0.0)

    monkeypatch.setattr(clips_api, "_find_avi", _fake_find)
    monkeypatch.setattr(clips_api, "probe_duration", _fake_probe)


def test_returns_404_when_no_mp4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _out, _lists = _client(tmp_path, monkeypatch)
    r = client.get("/api/clips/resolve?part=4&time=30")
    assert r.status_code == 404


def test_returns_404_when_no_clip_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, out, _lists = _client(tmp_path, monkeypatch)
    (out / "Part4.mp4").write_bytes(b"x")
    r = client.get("/api/clips/resolve?part=4&time=30")
    assert r.status_code == 404


def test_returns_null_within_pre_content_offset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, out, lists = _client(tmp_path, monkeypatch)
    (out / "Part4.mp4").write_bytes(b"x")
    (lists / "part04_styleb.txt").write_text("Demo (1) - 2.avi\n")
    _stub_durations(monkeypatch, {"Demo (1) - 2.avi": 10.0})
    r = client.get("/api/clips/resolve?part=4&time=5")
    assert r.status_code == 200
    body = r.json()
    assert body["clip_index"] is None
    assert "PANTHEON" in body.get("note", "")


def test_resolves_to_covering_clip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, out, lists = _client(tmp_path, monkeypatch)
    (out / "Part4.mp4").write_bytes(b"x")
    (lists / "part04_styleb.txt").write_text(
        "Demo (37) - 446.avi > Demo (37FL1).avi\n"
        "Demo (22) - 195.avi\n"
        "Demo (46) - 565.avi\n"
    )
    _stub_durations(monkeypatch, {
        "Demo (37) - 446.avi": 8.0,
        "Demo (22) - 195.avi": 5.0,
        "Demo (46) - 565.avi": 7.0,
    })
    # offset=15s + first clip 8s ends at 23s → time=20s is inside clip 0.
    b = client.get("/api/clips/resolve?part=4&time=20").json()
    assert b["clip_index"] == 0
    assert b["clip_filename"] == "Demo (37) - 446.avi"
    assert b["demo_hint"] == "37"
    assert abs(b["clip_offset"] - 5.0) < 1e-6  # 20 - 15 - 0

    # time=25s is 10s into content = 2s into clip 1 (after clip 0's 8s).
    b = client.get("/api/clips/resolve?part=4&time=25").json()
    assert b["clip_index"] == 1
    assert b["clip_filename"] == "Demo (22) - 195.avi"
    assert abs(b["clip_offset"] - 2.0) < 1e-6


def test_uses_manifest_over_styleb(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, out, lists = _client(tmp_path, monkeypatch)
    (out / "Part4.mp4").write_bytes(b"x")
    # styleb says "A", manifest points at a different clip list that says "B".
    (lists / "part04_styleb.txt").write_text("Demo (A) - 1.avi\n")
    other_cl = tmp_path / "other_cl.txt"
    other_cl.write_text("Demo (B) - 2.avi\n")
    (out / "Part4.render_manifest.json").write_text(json.dumps({
        "mp4": str(out / "Part4.mp4"), "clip_list": str(other_cl),
    }))
    _stub_durations(monkeypatch, {
        "Demo (A) - 1.avi": 10.0, "Demo (B) - 2.avi": 10.0,
    })
    b = client.get("/api/clips/resolve?part=4&time=20").json()
    assert b["clip_filename"] == "Demo (B) - 2.avi"
