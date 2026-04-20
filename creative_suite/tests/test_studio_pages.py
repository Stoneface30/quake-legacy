# creative_suite/tests/test_studio_pages.py
"""Contract tests for studio-pages.js — the 5-panel page router."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creative_suite.app import create_app

# ── Shared path ───────────────────────────────────────────────────────────────

PAGES_JS = Path("G:/QUAKE_LEGACY/creative_suite/frontend/studio-pages.js")
STUDIO_HTML = Path("G:/QUAKE_LEGACY/creative_suite/frontend/studio.html")
STUDIO_CSS = Path("G:/QUAKE_LEGACY/creative_suite/frontend/studio.css")


# ── 1. File existence ─────────────────────────────────────────────────────────

def test_studio_pages_js_exists() -> None:
    """studio-pages.js must exist in the frontend directory."""
    assert PAGES_JS.exists(), f"Missing file: {PAGES_JS}"


# ── 2. Public API surface ─────────────────────────────────────────────────────

def test_window_studio_pages_assigned() -> None:
    """StudioPages must be assigned to window.StudioPages (global)."""
    src = PAGES_JS.read_text(encoding="utf-8")
    assert "StudioPages" in src, "global StudioPages not found in studio-pages.js"


def test_init_method_present() -> None:
    """The init() method must be exposed on the StudioPages object."""
    src = PAGES_JS.read_text(encoding="utf-8")
    assert "init" in src, "init method not found in studio-pages.js"


def test_get_active_page_method_present() -> None:
    """The getActivePage() method must be exposed on the StudioPages object."""
    src = PAGES_JS.read_text(encoding="utf-8")
    assert "getActivePage" in src, "getActivePage method not found in studio-pages.js"


# ── 3. PAGE_MAP / all 5 pages ─────────────────────────────────────────────────

def test_page_map_has_all_five_pages() -> None:
    """PAGE_MAP or equivalent must map all 5 page names."""
    src = PAGES_JS.read_text(encoding="utf-8")
    for page in ("preview", "timeline", "audio", "effects", "inspector"):
        assert page in src, f"Page key {page!r} not found in studio-pages.js"


# ── 4. All 5 module references ────────────────────────────────────────────────

def test_all_panel_module_names_referenced() -> None:
    """All 5 panel globals must appear in the source."""
    src = PAGES_JS.read_text(encoding="utf-8")
    for module in (
        "StudioPreview",
        "StudioTimeline",
        "StudioAudio",
        "StudioEffects",
        "StudioInspector",
    ):
        assert module in src, f"Panel module {module!r} not referenced in studio-pages.js"


# ── 5. No innerHTML, uses replaceChildren ─────────────────────────────────────

def test_no_inner_html_used() -> None:
    """Rule UI-1: innerHTML must not be used with dynamic content (no assignment to innerHTML)."""
    src = PAGES_JS.read_text(encoding="utf-8")
    # Allow reading innerHTML but not assigning it
    # Check that there's no `innerHTML =` or `innerHTML=`
    import re
    assert not re.search(r'innerHTML\s*=', src), \
        "innerHTML assignment found in studio-pages.js — Rule UI-1 violation"


def test_replace_children_used() -> None:
    """replaceChildren() must be used to clear the panel slot (DOM-safe clearing)."""
    src = PAGES_JS.read_text(encoding="utf-8")
    assert "replaceChildren" in src, "replaceChildren() not found in studio-pages.js"


# ── 6. Store subscription ─────────────────────────────────────────────────────

def test_store_subscription_present() -> None:
    """The router must subscribe to StudioStore for state changes."""
    src = PAGES_JS.read_text(encoding="utf-8")
    assert "subscribe" in src, "store.subscribe() not found in studio-pages.js"


def test_store_get_state_used() -> None:
    """getState() must be used to read activePage from the store."""
    src = PAGES_JS.read_text(encoding="utf-8")
    assert "getState" in src, "getState() not found in studio-pages.js"


# ── 7. studio.html includes studio-pages.js script tag ───────────────────────

def test_studio_html_loads_studio_pages_js() -> None:
    """studio.html must include a <script> tag for studio-pages.js."""
    html = STUDIO_HTML.read_text(encoding="utf-8")
    assert "studio-pages.js" in html, "studio-pages.js script tag missing from studio.html"


def test_studio_pages_js_loaded_after_app_js() -> None:
    """studio-pages.js must be declared after studio-app.js in the HTML."""
    html = STUDIO_HTML.read_text(encoding="utf-8")
    pos_app   = html.find("studio-app.js")
    pos_pages = html.find("studio-pages.js")
    assert pos_app != -1,  "studio-app.js not found in studio.html"
    assert pos_pages != -1, "studio-pages.js not found in studio.html"
    assert pos_pages > pos_app, (
        "studio-pages.js must come after studio-app.js in load order"
    )


# ── 8. CSS: .panel-not-loaded rule ───────────────────────────────────────────

def test_css_panel_not_loaded_rule_exists() -> None:
    """studio.css must define a .panel-not-loaded rule."""
    css = STUDIO_CSS.read_text(encoding="utf-8")
    assert ".panel-not-loaded" in css, ".panel-not-loaded CSS rule missing from studio.css"


# ── 9. HTTP route still serves studio.html ───────────────────────────────────

@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    return TestClient(create_app())


def test_studio_html_served_with_pages_script(client: TestClient) -> None:
    """GET /studio must include the studio-pages.js script reference."""
    r = client.get("/studio")
    assert r.status_code == 200
    assert "studio-pages.js" in r.text, "studio-pages.js not in served /studio HTML"


def test_studio_html_served_with_all_panel_scripts(client: TestClient) -> None:
    """GET /studio must include script tags for all 5 panel modules."""
    r = client.get("/studio")
    assert r.status_code == 200
    for script in (
        "studio-preview.js",
        "studio-timeline.js",
        "studio-audio.js",
        "studio-litegraph.js",
        "studio-inspector.js",
    ):
        assert script in r.text, f"Panel script {script!r} missing from served /studio HTML"
