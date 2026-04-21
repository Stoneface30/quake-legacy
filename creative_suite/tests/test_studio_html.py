# creative_suite/tests/test_studio_html.py
"""Smoke tests for the /studio HTML shell route."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Minimal isolated app instance."""
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    return TestClient(create_app())


def test_studio_html_served(client: TestClient) -> None:
    """GET /studio must return 200 with HTML content-type."""
    r = client.get("/studio")
    assert r.status_code == 200
    ct = r.headers.get("content-type", "")
    assert "text/html" in ct, f"Expected text/html, got: {ct!r}"


def test_studio_html_contains_app_grid(client: TestClient) -> None:
    """The shell must include the #app-grid container."""
    r = client.get("/studio")
    assert r.status_code == 200
    assert 'id="app-grid"' in r.text


def test_studio_html_contains_headerbar(client: TestClient) -> None:
    """The shell must include the headerbar with logo, part-select, and rebuild button."""
    r = client.get("/studio")
    assert r.status_code == 200
    assert 'id="headerbar"' in r.text
    assert 'id="logo-text"' in r.text
    assert 'id="part-select"' in r.text
    assert 'id="btn-rebuild"' in r.text


def test_studio_html_contains_mode_switch_and_dynamic_nav(client: TestClient) -> None:
    """The shell must expose the 3-mode switch and the dynamic nav host."""
    r = client.get("/studio")
    assert r.status_code == 200
    for mode in ("studio", "lab", "creative"):
        assert f'data-mode="{mode}"' in r.text, f"Missing mode button for {mode!r}"
    assert 'id="nav-list"' in r.text


def test_studio_html_contains_panel_slot(client: TestClient) -> None:
    """The main area panel slot must be present."""
    r = client.get("/studio")
    assert r.status_code == 200
    assert 'id="panel-slot"' in r.text


def test_studio_html_contains_statusbar(client: TestClient) -> None:
    """The statusbar must be present with a status-text span."""
    r = client.get("/studio")
    assert r.status_code == 200
    assert 'id="statusbar"' in r.text
    assert 'id="status-text"' in r.text


def test_studio_html_loads_vendor_scripts(client: TestClient) -> None:
    """All vendor script tags must be present."""
    r = client.get("/studio")
    assert r.status_code == 200
    for script in (
        "wavesurfer.js",
        "wavesurfer-multitrack.js",
        "animation-timeline.js",
        "litegraph.js",
        "tweakpane.js",
        "mp4box.js",
        "theatre-core-studio.js",
    ):
        assert script in r.text, f"Missing vendor script: {script!r}"


def test_studio_html_loads_app_scripts(client: TestClient) -> None:
    """App JS files (store + app) must be referenced."""
    r = client.get("/studio")
    assert r.status_code == 200
    assert "studio-store.js" in r.text
    assert "studio-app.js" in r.text
    assert "studio-clips.js" in r.text
    assert "studio-edit.js" in r.text
    assert "lab-demos.js" in r.text
    assert "creative-packs.js" in r.text


def test_studio_html_references_css(client: TestClient) -> None:
    """The stylesheet link must be present."""
    r = client.get("/studio")
    assert r.status_code == 200
    assert "studio.css" in r.text
