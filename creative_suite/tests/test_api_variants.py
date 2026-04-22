"""Task 6 — variant approve / reject / reroll lifecycle tests.

Uses the same MockTransport ComfyClient + sync-runner harness as the Task 5
api/comfy smoke. Exercises the spec §7 smoke:
    Generate 3 variants on basewall01b.tga, approve 1, reject 1, reroll 1
    → SELECT status, COUNT(*) FROM variants GROUP BY status;
    → 1 approved, 1 rejected, ≥1 pending
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest

pytest.importorskip("PIL")

from PIL import Image  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from creative_suite.app import create_app  # noqa: E402
from creative_suite.comfy.client import ComfyClient  # noqa: E402
from creative_suite.config import Config  # noqa: E402
from creative_suite.db.migrate import connect, migrate  # noqa: E402
from creative_suite.inventory.catalog import build_catalog  # noqa: E402
from creative_suite.inventory.ingest import ingest  # noqa: E402


FAKE_OUTPUT_PNG = io.BytesIO()
Image.new("RGB", (1024, 1024), (80, 120, 200)).save(FAKE_OUTPUT_PNG, format="PNG")
FAKE_OUTPUT_BYTES = FAKE_OUTPUT_PNG.getvalue()


def _make_ref_pk3(path: Path) -> Path:
    img = Image.new("RGB", (128, 128), (90, 90, 90))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        z.writestr("textures/base_wall/basewall01b.tga", buf.getvalue())
    return path


def _mock_comfy_handler() -> httpx.MockTransport:
    counter = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/upload/image":
            return httpx.Response(200, json={"name": "ref_in.png"})
        if path == "/prompt":
            counter["n"] += 1
            return httpx.Response(200, json={"prompt_id": f"job-{counter['n']}"})
        if path.startswith("/history/"):
            # /history/job-N — return an output for any job_id.
            job = path.rsplit("/", 1)[-1]
            return httpx.Response(
                200,
                json={
                    job: {
                        "outputs": {
                            "8": {
                                "images": [
                                    {
                                        "filename": f"variant_{job}_.png",
                                        "subfolder": "creative_suite",
                                        "type": "output",
                                    }
                                ]
                            }
                        }
                    }
                },
            )
        if path == "/view":
            return httpx.Response(200, content=FAKE_OUTPUT_BYTES)
        raise AssertionError(f"unexpected {request.method} {path}")

    return httpx.MockTransport(handler)


@pytest.fixture
def app_with_asset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    cfg = Config()
    cfg.ensure_dirs()
    migrate(cfg)
    pk3 = _make_ref_pk3(tmp_path / "ref.pk3")
    ingest(cfg, build_catalog([pk3]))

    app = create_app()
    app.state.comfy_client = ComfyClient(transport=_mock_comfy_handler())
    app.state.comfy_run_sync = True

    with connect(cfg) as con:
        row = con.execute(
            "SELECT id FROM assets WHERE internal_path = "
            "'textures/base_wall/basewall01b.tga'"
        ).fetchone()
    assert row is not None
    asset_id = int(row["id"])

    with TestClient(app) as client:
        yield client, cfg, asset_id


# ---------------------------------------------------------------------- #
# Individual endpoint tests
# ---------------------------------------------------------------------- #


def test_approve_sets_status_and_stamps_timestamp(app_with_asset) -> None:  # type: ignore[no-untyped-def]
    client, cfg, asset_id = app_with_asset
    queued = client.post(
        "/api/comfy/queue", json={"asset_id": asset_id, "seed": 111}
    ).json()
    vid = queued["variant_id"]

    r = client.post(f"/api/variants/{vid}/approve")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "approved"
    assert body["approved_at"] is not None

    with connect(cfg) as con:
        row = con.execute(
            "SELECT status, approved_at FROM variants WHERE id = ?", (vid,),
        ).fetchone()
    assert row["status"] == "approved"
    assert row["approved_at"]


def test_reject_sets_status_and_clears_approved_at(app_with_asset) -> None:  # type: ignore[no-untyped-def]
    client, cfg, asset_id = app_with_asset
    vid = client.post(
        "/api/comfy/queue", json={"asset_id": asset_id, "seed": 222}
    ).json()["variant_id"]
    # Approve then reject — approved_at must be cleared on reject.
    client.post(f"/api/variants/{vid}/approve")
    r = client.post(f"/api/variants/{vid}/reject")
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    with connect(cfg) as con:
        row = con.execute(
            "SELECT status, approved_at FROM variants WHERE id = ?", (vid,),
        ).fetchone()
    assert row["status"] == "rejected"
    assert row["approved_at"] is None


def test_reroll_queues_new_pending_variant(app_with_asset) -> None:  # type: ignore[no-untyped-def]
    client, cfg, asset_id = app_with_asset
    original = client.post(
        "/api/comfy/queue",
        json={"asset_id": asset_id, "user_prompt": "heavy wet concrete", "seed": 42},
    ).json()

    r = client.post(f"/api/variants/{original['variant_id']}/reroll")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source_variant_id"] == original["variant_id"]
    assert body["new_variant_id"] != original["variant_id"]
    assert body["asset_id"] == asset_id
    # Same prompt, fresh seed — the seed may coincidentally match but the
    # final_prompt must be identical content (photoreal suffix preserved).
    assert "heavy wet concrete" in body["final_prompt"]

    # Both rows exist.
    with connect(cfg) as con:
        rows = con.execute(
            "SELECT id, seed, user_prompt FROM variants "
            "WHERE asset_id = ? ORDER BY id",
            (asset_id,),
        ).fetchall()
    assert len(rows) == 2
    assert rows[0]["user_prompt"] == rows[1]["user_prompt"]


def test_approve_404_on_missing(app_with_asset) -> None:  # type: ignore[no-untyped-def]
    client, _, _ = app_with_asset
    assert client.post("/api/variants/9999/approve").status_code == 404
    assert client.post("/api/variants/9999/reject").status_code == 404
    assert client.post("/api/variants/9999/reroll").status_code == 404


def test_list_variants_can_filter_by_status_without_asset_id(app_with_asset) -> None:  # type: ignore[no-untyped-def]
    client, _, asset_id = app_with_asset
    client.post("/api/comfy/queue", json={"asset_id": asset_id, "seed": 111})
    approved = client.post(
        "/api/comfy/queue", json={"asset_id": asset_id, "seed": 222}
    ).json()["variant_id"]
    client.post(f"/api/variants/{approved}/approve")

    r = client.get("/api/variants?status=pending&limit=10")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "variants" in body
    assert len(body["variants"]) == 1
    row = body["variants"][0]
    assert row["status"] == "pending"
    assert row["asset_id"] == asset_id
    assert row["category"] == "surface"
    assert row["png_url"] is not None


# ---------------------------------------------------------------------- #
# Feed endpoint (shell-oriented queue panel)
# ---------------------------------------------------------------------- #


def test_variants_feed_returns_recent_items(app_with_asset) -> None:  # type: ignore[no-untyped-def]
    """GET /api/variants/feed must return a flat variants list."""
    client, _, asset_id = app_with_asset
    # Queue two variants so there is something to return.
    client.post("/api/comfy/queue", json={"asset_id": asset_id, "seed": 1})
    client.post("/api/comfy/queue", json={"asset_id": asset_id, "seed": 2})

    r = client.get("/api/variants/feed")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "variants" in body
    assert isinstance(body["variants"], list)
    assert len(body["variants"]) == 2
    first = body["variants"][0]
    assert "id" in first
    assert "status" in first
    assert "category" in first


def test_variants_feed_empty_when_no_variants(app_with_asset) -> None:  # type: ignore[no-untyped-def]
    """GET /api/variants/feed must return empty list when no variants exist."""
    client, _, _ = app_with_asset
    r = client.get("/api/variants/feed")
    assert r.status_code == 200
    assert r.json()["variants"] == []


# ---------------------------------------------------------------------- #
# End-to-end spec §7 smoke: 3 variants → approve 1, reject 1, reroll 1
# ---------------------------------------------------------------------- #


def test_full_approval_loop_leaves_one_of_each_status(app_with_asset) -> None:  # type: ignore[no-untyped-def]
    client, cfg, asset_id = app_with_asset
    ids = []
    for seed in (11, 22, 33):
        r = client.post(
            "/api/comfy/queue", json={"asset_id": asset_id, "seed": seed}
        )
        ids.append(r.json()["variant_id"])

    # 1 approved, 1 rejected, 1 rerolled (→ new pending tile).
    client.post(f"/api/variants/{ids[0]}/approve")
    client.post(f"/api/variants/{ids[1]}/reject")
    reroll = client.post(f"/api/variants/{ids[2]}/reroll").json()
    assert "new_variant_id" in reroll

    with connect(cfg) as con:
        counts = dict(
            (r["status"], r["c"])
            for r in con.execute(
                "SELECT status, COUNT(*) AS c FROM variants "
                "WHERE asset_id = ? GROUP BY status",
                (asset_id,),
            )
        )
    assert counts.get("approved", 0) == 1
    assert counts.get("rejected", 0) == 1
    # The original third variant is still 'pending' (runner kept it there)
    # and the reroll inserted a new pending row. So ≥ 2 pending.
    assert counts.get("pending", 0) >= 1


# Silence the flake8-unused-import complaint on json — imported for
# symmetry with sibling tests even if not all branches use it here.
_ = json
