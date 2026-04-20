"""/editor route serves the editor shell."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app


def test_editor_route_serves_html(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(tmp_path / "output"))
    (tmp_path / "output").mkdir()
    with TestClient(create_app()) as c:
        r = c.get("/editor")
        assert r.status_code == 200
        body = r.text
        # Three-pane layout markers
        assert 'id="pane-left"' in body
        assert 'id="pane-center"' in body
        assert 'id="pane-right"' in body
        # Timeline wiring
        assert 'id="track-video-strip"' in body
        assert 'id="monitor-video"' in body
        # Render buttons
        assert 'id="render-preview"' in body
        assert 'id="render-ship"' in body
        # Source-missing banner (hidden by default)
        assert 'id="source-banner"' in body
        assert 'id="source-banner-prepare"' in body
        # Versions list (render history)
        assert 'id="versions-list"' in body


def test_editor_static_js_served(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(tmp_path / "output"))
    (tmp_path / "output").mkdir()
    with TestClient(create_app()) as c:
        for name in ("editor-app.js", "editor-api.js",
                     "editor-timeline.js", "editor-inspector.js",
                     "editor.css"):
            r = c.get(f"/cinema-static/{name}")
            assert r.status_code == 200, name
