"""Tests for per-clip beatmatch recommendation endpoint."""
import pytest
from fastapi.testclient import TestClient
from creative_suite.app import create_app


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def test_beat_rec_returns_200(client):
    resp = client.get("/api/studio/part/5/clip_recommendations")
    assert resp.status_code == 200


def test_beat_rec_response_shape(client):
    resp = client.get("/api/studio/part/5/clip_recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert "bpm" in data
    assert "beat_interval_s" in data


def test_beat_rec_items_have_required_fields(client):
    resp = client.get("/api/studio/part/5/clip_recommendations")
    recs = resp.json()["recommendations"]
    for r in recs[:3]:
        assert "clip_id" in r
        assert "clip_path" in r
        assert "suggestion" in r           # 'slowmo' | 'speedup' | 'none'
        assert "beat_offset_s" in r        # float
        assert "recommended_rate" in r     # float


def test_beat_rec_suggestion_values_valid(client):
    resp = client.get("/api/studio/part/5/clip_recommendations")
    recs = resp.json()["recommendations"]
    valid = {"slowmo", "speedup", "none"}
    for r in recs:
        assert r["suggestion"] in valid, f"Bad suggestion: {r['suggestion']}"
