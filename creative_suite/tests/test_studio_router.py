# creative_suite/tests/test_studio_router.py
"""Contract tests for the /api/studio router."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app
from creative_suite.config import Config


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Minimal app with isolated storage; no clip lists or output seeded."""
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    return TestClient(create_app())


@pytest.fixture
def seeded_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """App with a fake clip list directory and output directory."""
    lists_dir = tmp_path / "clip_lists"
    lists_dir.mkdir()
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    # Write a minimal clip list for part 7
    (lists_dir / "part07.txt").write_text(
        "# comment line\n"
        "\n"
        "T1/Part7/frag001.avi\n"
        "T2/Part7/frag_FL_001.avi > T2/Part7/FL/angle.avi\n"
        "T3/Part7/atmosphere.avi\n",
        encoding="utf-8",
    )

    # Write a flow plan (flat layout)
    (out_dir / "part07_flow_plan.json").write_text(
        json.dumps({"clips": [], "seams": [], "notes": "test"}),
        encoding="utf-8",
    )

    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setattr(Config, "phase1_clip_lists", property(lambda _: lists_dir))
    monkeypatch.setattr(Config, "phase1_output_dir", property(lambda _: out_dir))

    return TestClient(create_app())


# ── test: /api/studio/status ──────────────────────────────────────────────────

def test_status_ok(client: TestClient) -> None:
    r = client.get("/api/studio/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["version"] == "studio/v1"
    assert "mlt_available" in data


# ── test: /api/studio/parts ───────────────────────────────────────────────────

def test_parts_returns_list_when_no_clip_lists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Patching clip_lists to a nonexistent dir guarantees an empty result."""
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setattr(Config, "phase1_clip_lists", property(lambda _: tmp_path / "empty"))
    c = TestClient(create_app())
    r = c.get("/api/studio/parts")
    assert r.status_code == 200
    assert r.json() == []


def test_parts_seeded_returns_correct_part(seeded_client: TestClient) -> None:
    r = seeded_client.get("/api/studio/parts")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 1

    p = data[0]
    assert p["part"] == 7
    assert p["clip_count"] == 3       # 3 non-empty, non-comment lines
    assert p["has_flow_plan"] is True
    assert isinstance(p["has_music"], bool)
    assert p["render_exists"] is False


def test_parts_response_shape(seeded_client: TestClient) -> None:
    """Every item must have all five required keys."""
    r = seeded_client.get("/api/studio/parts")
    assert r.status_code == 200
    for item in r.json():
        for key in ("part", "clip_count", "has_flow_plan", "has_music", "render_exists"):
            assert key in item, f"missing key {key!r} in {item}"


# ── test: /api/studio/part/{n}/clips ─────────────────────────────────────────

def test_clips_404_for_nonexistent_part(client: TestClient) -> None:
    r = client.get("/api/studio/part/99/clips")
    assert r.status_code == 404


def test_clips_seeded_returns_correct_structure(seeded_client: TestClient) -> None:
    r = seeded_client.get("/api/studio/part/7/clips")
    assert r.status_code == 200
    data = r.json()
    assert data["part"] == 7
    clips = data["clips"]
    assert len(clips) == 3

    # First clip: T1, not FL, no pair
    c0 = clips[0]
    assert c0["idx"] == 0
    assert c0["tier"] == "T1"
    assert c0["is_fl"] is False
    assert c0["has_pair"] is False
    assert c0["path"] == "T1/Part7/frag001.avi"

    # Second clip: T2, FL in path, has pair
    c1 = clips[1]
    assert c1["idx"] == 1
    assert c1["tier"] == "T2"
    assert c1["is_fl"] is True
    assert c1["has_pair"] is True
    # path is the left side of >
    assert c1["path"] == "T2/Part7/frag_FL_001.avi"

    # Third clip: T3, not FL, no pair
    c2 = clips[2]
    assert c2["idx"] == 2
    assert c2["tier"] == "T3"
    assert c2["is_fl"] is False
    assert c2["has_pair"] is False


def test_clips_every_item_has_required_keys(seeded_client: TestClient) -> None:
    r = seeded_client.get("/api/studio/part/7/clips")
    assert r.status_code == 200
    for clip in r.json()["clips"]:
        for key in ("idx", "raw", "path", "tier", "is_fl", "has_pair"):
            assert key in clip, f"missing key {key!r} in {clip}"


# ── test: /api/studio/part/{n}/flow ──────────────────────────────────────────

def test_flow_404_for_nonexistent_part(client: TestClient) -> None:
    r = client.get("/api/studio/part/99/flow")
    assert r.status_code == 404


def test_flow_returns_json_content(seeded_client: TestClient) -> None:
    r = seeded_client.get("/api/studio/part/7/flow")
    assert r.status_code == 200
    data = r.json()
    assert data["notes"] == "test"
    assert "clips" in data


# ── test: /api/studio/part/{n}/beats ─────────────────────────────────────────

def test_beats_endpoint_valid_part(client: TestClient) -> None:
    """Valid part with no beats file returns 200 with empty beats array."""
    r = client.get("/api/studio/part/4/beats")
    assert r.status_code == 200
    data = r.json()
    assert "beats" in data
    assert isinstance(data["beats"], list)
    assert data["part"] == 4


def test_beats_endpoint_out_of_range(client: TestClient) -> None:
    """Part number outside 4-12 returns 404."""
    r = client.get("/api/studio/part/99/beats")
    assert r.status_code == 404


def test_beats_returns_empty_for_missing_part_beats(client: TestClient) -> None:
    """Missing beats file → 200 with empty beats and sections arrays."""
    r = client.get("/api/studio/part/7/beats")
    assert r.status_code == 200
    data = r.json()
    assert data["beats"] == []
    assert data["sections"] == []
    assert "note" in data


# ── test: /api/studio/part/{n}/flow ──────────────────────────────────────────

def test_flow_subdir_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """flow_plan.json in output/partNN/ subdir layout is also found."""
    lists_dir = tmp_path / "clip_lists"
    lists_dir.mkdir()
    out_dir = tmp_path / "output"
    (out_dir / "part08").mkdir(parents=True)

    (lists_dir / "part08.txt").write_text("T2/clip.avi\n", encoding="utf-8")
    (out_dir / "part08" / "flow_plan.json").write_text(
        json.dumps({"clips": [], "notes": "subdir"}), encoding="utf-8"
    )

    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setattr(Config, "phase1_clip_lists", property(lambda _: lists_dir))
    monkeypatch.setattr(Config, "phase1_output_dir", property(lambda _: out_dir))

    with TestClient(create_app()) as c:
        r = c.get("/api/studio/part/8/flow")
    assert r.status_code == 200
    assert r.json()["notes"] == "subdir"


# ── test: /api/studio/part/{n}/music ─────────────────────────────────────────

def test_music_endpoint_valid_part(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Valid part with no music files returns 200 with empty tracks list."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setattr(Config, "phase1_music_dir", property(lambda _: music_dir))
    monkeypatch.setattr(Config, "phase1_output_dir", property(lambda _: out_dir))

    c = TestClient(create_app())
    r = c.get("/api/studio/part/4/music")
    assert r.status_code == 200
    data = r.json()
    assert "tracks" in data
    assert isinstance(data["tracks"], list)
    assert data["part"] == 4


def test_music_endpoint_valid_part_with_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Part with a real stub mp3 returns it in the tracks list with correct role."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    # Write a zero-byte placeholder — mutagen will fail gracefully (duration_s=None)
    (music_dir / "part05_music_01.mp3").write_bytes(b"")
    (music_dir / "part05_intro_music.mp3").write_bytes(b"")

    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setattr(Config, "phase1_music_dir", property(lambda _: music_dir))
    monkeypatch.setattr(Config, "phase1_output_dir", property(lambda _: out_dir))

    c = TestClient(create_app())
    r = c.get("/api/studio/part/5/music")
    assert r.status_code == 200
    data = r.json()
    assert data["part"] == 5
    assert len(data["tracks"]) == 2

    roles = {t["filename"]: t["role"] for t in data["tracks"]}
    assert roles["part05_music_01.mp3"] == "main"
    assert roles["part05_intro_music.mp3"] == "intro"


def test_music_endpoint_out_of_range(client: TestClient) -> None:
    """Part number outside 4-12 returns 404."""
    r = client.get("/api/studio/part/99/music")
    assert r.status_code == 404

    r = client.get("/api/studio/part/3/music")
    assert r.status_code == 404


# ── test: /api/studio/music/library ──────────────────────────────────────────

def test_music_library_endpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Library endpoint returns a flat list (possibly empty) with 200."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setattr(Config, "phase1_music_dir", property(lambda _: music_dir))
    monkeypatch.setattr(Config, "phase1_output_dir", property(lambda _: out_dir))

    c = TestClient(create_app())
    r = c.get("/api/studio/music/library")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_music_library_includes_part_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each track in the library response includes a part field."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    # Write stubs for two parts
    (music_dir / "part06_music_01.mp3").write_bytes(b"")
    (music_dir / "part07_music_01.mp3").write_bytes(b"")

    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setattr(Config, "phase1_music_dir", property(lambda _: music_dir))
    monkeypatch.setattr(Config, "phase1_output_dir", property(lambda _: out_dir))

    c = TestClient(create_app())
    r = c.get("/api/studio/music/library")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    parts_seen = {t["part"] for t in data}
    assert parts_seen == {6, 7}
    for track in data:
        assert "part" in track
        assert "filename" in track
        assert "role" in track


# ── test: /api/studio/part/{n}/music_contract ────────────────────────────────

def test_music_contract_valid_part(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Valid part with a flow plan returns 200 with a contract key."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    # Seed a flow plan with body_duration
    (out_dir / "part04_flow_plan.json").write_text(
        json.dumps({"body_duration": 180.0, "clips": []}),
        encoding="utf-8",
    )

    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setattr(Config, "phase1_music_dir", property(lambda _: music_dir))
    monkeypatch.setattr(Config, "phase1_output_dir", property(lambda _: out_dir))

    c = TestClient(create_app())
    r = c.get("/api/studio/part/4/music_contract")
    assert r.status_code == 200
    data = r.json()
    assert data["part"] == 4
    assert "contract" in data
    contract = data["contract"]
    # No music files → not covered, gap == body_duration
    assert contract["covered"] is False
    assert contract["body_duration_s"] == 180.0
    assert "tracks" in contract
    assert "coverage_gap_s" in contract
    assert "full_length_pct" in contract
    assert "warnings" in contract


def test_music_contract_out_of_range(client: TestClient) -> None:
    """Part number outside 4-12 returns 404."""
    r = client.get("/api/studio/part/1/music_contract")
    assert r.status_code == 404

    r = client.get("/api/studio/part/99/music_contract")
    assert r.status_code == 404


def test_music_contract_no_flow_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Part with no flow_plan.json returns 200 with error in contract."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setattr(Config, "phase1_music_dir", property(lambda _: music_dir))
    monkeypatch.setattr(Config, "phase1_output_dir", property(lambda _: out_dir))

    c = TestClient(create_app())
    r = c.get("/api/studio/part/5/music_contract")
    assert r.status_code == 200
    data = r.json()
    assert data["part"] == 5
    assert data["contract"] == {"error": "no flow plan"}
