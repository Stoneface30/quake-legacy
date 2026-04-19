"""Task 8 — pk3 build + install API lifecycle tests.

Shared harness with Task 5/6: MockTransport ComfyClient + sync-runner so
POST /api/comfy/queue finishes inline.

Covers:
  - Gate CS-1 denies build if <5 approved variants       → 409
  - Gate CS-1 denies build if no approved surface        → 409
  - Gate CS-1 denies build if no approved skin           → 409
  - Gate CS-1 passes: 5 approved incl. surface + skin    → 200 + pk3 on disk
  - Install: copies pk3, reports alpha-sort ok vs pak00  → 200
  - Install: 404 when no pk3 built yet
  - Install: 500 when WOLFCAM_BASEQ3_DIR points nowhere
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any, Iterator

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
Image.new("RGBA", (256, 256), (80, 120, 200, 255)).save(FAKE_OUTPUT_PNG, format="PNG")
FAKE_OUTPUT_BYTES = FAKE_OUTPUT_PNG.getvalue()


def _make_mixed_pk3(path: Path) -> Path:
    """pk3 with one surface AND one skin so Gate CS-1 category reqs are
    satisfiable. Skins live under models/players/<slug>/<file>.tga per
    inventory/catalog.py classifier."""
    img = Image.new("RGB", (128, 128), (90, 90, 90))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    body = buf.getvalue()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        z.writestr("textures/base_wall/basewall01b.tga", body)  # surface
        z.writestr("textures/base_wall/basewall02.tga",  body)  # surface
        z.writestr("textures/base_wall/basewall03.tga",  body)  # surface
        z.writestr("models/players/visor/lower.tga",     body)  # skin
        z.writestr("models/players/visor/upper.tga",     body)  # skin
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
def app_with_assets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[TestClient, Config, dict[str, list[int]]]]:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    cfg = Config()
    cfg.ensure_dirs()
    migrate(cfg)
    pk3 = _make_mixed_pk3(tmp_path / "ref.pk3")
    ingest(cfg, build_catalog([pk3]))

    app = create_app()
    app.state.comfy_client = ComfyClient(transport=_mock_comfy_handler())
    app.state.comfy_run_sync = True

    with connect(cfg) as con:
        rows = con.execute(
            "SELECT id, category FROM assets ORDER BY id"
        ).fetchall()
    ids_by_cat: dict[str, list[int]] = {}
    for r in rows:
        ids_by_cat.setdefault(r["category"], []).append(int(r["id"]))

    with TestClient(app) as client:
        yield client, cfg, ids_by_cat


def _queue(client: TestClient, asset_id: int, seed: int) -> int:
    r = client.post("/api/comfy/queue", json={"asset_id": asset_id, "seed": seed})
    assert r.status_code == 200, r.text
    return int(r.json()["variant_id"])


# ---------------------------------------------------------------------- #
# Gate CS-1 negative tests
# ---------------------------------------------------------------------- #


def test_build_denied_with_fewer_than_5_approved(app_with_assets: Any) -> None:
    client, _, ids = app_with_assets
    # Approve only 2 (not enough).
    v1 = _queue(client, ids["surface"][0], 1)
    v2 = _queue(client, ids["skin"][0], 2)
    client.post(f"/api/variants/{v1}/approve")
    client.post(f"/api/variants/{v2}/approve")

    r = client.post("/api/packs/build")
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["approved"] == 2
    assert detail["min_required"] == 5
    assert "Gate CS-1" in detail["error"]


def test_build_denied_without_approved_surface(app_with_assets: Any) -> None:
    client, _, ids = app_with_assets
    # 5 approved, but ALL skins — surface missing.
    # Our fixture only has 2 skins; top up with surfaces but only reject those.
    for i, aid in enumerate(ids["surface"][:3]):
        vid = _queue(client, aid, 100 + i)
        client.post(f"/api/variants/{vid}/reject")
    for i, aid in enumerate(ids["skin"][:2]):
        vid = _queue(client, aid, 200 + i)
        client.post(f"/api/variants/{vid}/approve")
    # Need 3 more approved from somewhere — reuse skins (same asset, new variants).
    for i in range(3):
        vid = _queue(client, ids["skin"][0], 300 + i)
        client.post(f"/api/variants/{vid}/approve")

    r = client.post("/api/packs/build")
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert "surface" in detail["missing_categories"]


def test_build_denied_without_approved_skin(app_with_assets: Any) -> None:
    client, _, ids = app_with_assets
    # 5 approved surfaces, 0 skins.
    for i in range(5):
        aid = ids["surface"][i % len(ids["surface"])]
        vid = _queue(client, aid, 400 + i)
        client.post(f"/api/variants/{vid}/approve")

    r = client.post("/api/packs/build")
    assert r.status_code == 409
    assert "skin" in r.json()["detail"]["missing_categories"]


# ---------------------------------------------------------------------- #
# Gate CS-1 positive + build
# ---------------------------------------------------------------------- #


def _approve_minimum_mix(client: TestClient, ids: dict[str, list[int]]) -> None:
    """5 approved total: 3 surface + 2 skin."""
    for i in range(3):
        aid = ids["surface"][i % len(ids["surface"])]
        vid = _queue(client, aid, 500 + i)
        r = client.post(f"/api/variants/{vid}/approve")
        assert r.status_code == 200
    for i in range(2):
        aid = ids["skin"][i % len(ids["skin"])]
        vid = _queue(client, aid, 600 + i)
        r = client.post(f"/api/variants/{vid}/approve")
        assert r.status_code == 200


def test_build_succeeds_and_writes_pk3(app_with_assets: Any) -> None:
    client, cfg, ids = app_with_assets
    _approve_minimum_mix(client, ids)

    r = client.post("/api/packs/build")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pack_slug"] == "zzz_photorealistic"
    assert body["variant_count"] == 5
    assert len(body["sha256"]) == 64

    pk3 = Path(body["pk3_path"])
    assert pk3.exists()
    assert pk3.name == "zzz_photorealistic.pk3"

    # pk3 opens, has 5 members, and every entry is a .tga.
    with zipfile.ZipFile(pk3) as z:
        names = z.namelist()
    assert len(names) == 5
    assert all(n.endswith(".tga") for n in names), names

    # pack_builds row was inserted.
    with connect(cfg) as con:
        row = con.execute(
            "SELECT pack_slug, variant_count, sha256 FROM pack_builds"
        ).fetchone()
    assert row["pack_slug"] == "zzz_photorealistic"
    assert row["variant_count"] == 5
    assert row["sha256"] == body["sha256"]


def test_pack_status_reports_gate_state(app_with_assets: Any) -> None:
    client, _, ids = app_with_assets
    # Before any approvals — gate closed.
    r = client.get("/api/packs/status")
    assert r.status_code == 200
    state = r.json()
    assert state["gate_cs1"]["ok"] is False
    assert state["last_build"] is None

    _approve_minimum_mix(client, ids)
    r2 = client.get("/api/packs/status")
    assert r2.json()["gate_cs1"]["ok"] is True


# ---------------------------------------------------------------------- #
# Install hook + alpha-sort
# ---------------------------------------------------------------------- #


def test_install_404_when_no_pk3_built(app_with_assets: Any) -> None:
    client, _, _ = app_with_assets
    r = client.post("/api/packs/install")
    assert r.status_code == 404


def test_install_500_when_baseq3_dir_missing(
    app_with_assets: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, _, ids = app_with_assets
    _approve_minimum_mix(client, ids)
    client.post("/api/packs/build")

    monkeypatch.setenv("WOLFCAM_BASEQ3_DIR", str(tmp_path / "nowhere"))
    r = client.post("/api/packs/install")
    assert r.status_code == 500
    assert "wolfcam baseq3" in r.json()["detail"]["error"]


def test_install_copies_pk3_and_reports_alpha_sort(
    app_with_assets: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, _, ids = app_with_assets
    _approve_minimum_mix(client, ids)
    client.post("/api/packs/build")

    baseq3 = tmp_path / "fake_wolfcam" / "baseq3"
    baseq3.mkdir(parents=True)
    # Drop a placeholder pak00 so the alpha-sort assertion is meaningful.
    (baseq3 / "pak00.pk3").write_bytes(b"stub")

    monkeypatch.setenv("WOLFCAM_BASEQ3_DIR", str(baseq3))
    r = client.post("/api/packs/install")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["alpha_sort_ok"] is True
    assert "zzz_photorealistic.pk3" in body["baseq3_pk3s"]
    assert (baseq3 / "zzz_photorealistic.pk3").exists()
    # Reminder string present so ops docs stay in sync with ENG-3.
    assert "sv_pure 0" in body["reminder_sv_pure"]
