"""Content-assertion tests for studio-beatmarkers.js and studio.css.

Static-analysis tests: verify that the JS source file contains the expected
identifiers, API surface, and patterns. Behavioural browser testing is
covered by separate Playwright tests.

Rules enforced:
  UI-1: no innerHTML with untrusted data
  UI-2: shared store is single source of truth (subscribe present)
"""
from __future__ import annotations

from pathlib import Path

FRONTEND       = Path(__file__).parent.parent / "frontend"
BEATMARKERS_JS = FRONTEND / "studio-beatmarkers.js"
STUDIO_CSS     = FRONTEND / "studio.css"


# ── File existence ─────────────────────────────────────────────────────────────

class TestStudioBeatMarkersExists:
    def test_file_exists(self) -> None:
        assert BEATMARKERS_JS.exists(), f"Missing: {BEATMARKERS_JS}"

    def test_css_file_exists(self) -> None:
        assert STUDIO_CSS.exists(), f"Missing: {STUDIO_CSS}"


# ── window.StudioBeatMarkers export ───────────────────────────────────────────

class TestStudioBeatMarkersExport:
    def _src(self) -> str:
        return BEATMARKERS_JS.read_text(encoding="utf-8")

    def test_window_studio_beat_markers_defined(self) -> None:
        assert "window.StudioBeatMarkers" in self._src()

    def test_method_mount(self) -> None:
        assert "mount" in self._src()

    def test_method_unmount(self) -> None:
        assert "unmount" in self._src()

    def test_method_load_beats(self) -> None:
        assert "loadBeats" in self._src()

    def test_method_set_playhead(self) -> None:
        assert "setPlayhead" in self._src()

    def test_method_sync_width(self) -> None:
        assert "syncWidth" in self._src()


# ── API surface (all 5 methods present in the exported object) ────────────────

class TestStudioBeatMarkersApiSurface:
    def _src(self) -> str:
        return BEATMARKERS_JS.read_text(encoding="utf-8")

    def test_all_five_methods_exported(self) -> None:
        src = self._src()
        for method in ("mount", "unmount", "loadBeats", "setPlayhead", "syncWidth"):
            assert method in src, f"Method {method!r} not found in exports"


# ── API endpoint fetch ────────────────────────────────────────────────────────

class TestStudioBeatMarkersFetch:
    def _src(self) -> str:
        return BEATMARKERS_JS.read_text(encoding="utf-8")

    def test_fetches_beats_api_url(self) -> None:
        """Must call /api/studio/part/ for beat data."""
        assert "/api/studio/part/" in self._src()

    def test_fetches_beats_endpoint(self) -> None:
        """Must reference /beats endpoint."""
        assert "/beats" in self._src()


# ── Store subscription (UI-2) ─────────────────────────────────────────────────

class TestStudioBeatMarkersStoreIntegration:
    def _src(self) -> str:
        return BEATMARKERS_JS.read_text(encoding="utf-8")

    def test_store_subscribe_present(self) -> None:
        """Panel must subscribe to StudioStore (Rule UI-2)."""
        assert "StudioStore.subscribe" in self._src()

    def test_listens_to_active_part_change(self) -> None:
        assert "activePart" in self._src()

    def test_listens_to_current_time_change(self) -> None:
        assert "currentTime" in self._src()


# ── Security / DOM safety (UI-1) ──────────────────────────────────────────────

class TestStudioBeatMarkersDomSafety:
    def _src(self) -> str:
        return BEATMARKERS_JS.read_text(encoding="utf-8")

    def test_no_inner_html(self) -> None:
        """Must not use innerHTML (Rule UI-1)."""
        assert "innerHTML" not in self._src()

    def test_uses_create_element(self) -> None:
        """DOM must be built with createElement."""
        assert "createElement" in self._src()

    def test_uses_text_content(self) -> None:
        """Dynamic text must go through textContent."""
        assert "textContent" in self._src()


# ── CSS rules ─────────────────────────────────────────────────────────────────

class TestStudioBeatMarkersCss:
    def _css(self) -> str:
        return STUDIO_CSS.read_text(encoding="utf-8")

    def test_beatmarkers_panel_rule(self) -> None:
        assert ".beatmarkers-panel" in self._css()

    def test_bm_canvas_wrap_rule(self) -> None:
        assert ".bm-canvas-wrap" in self._css()

    def test_bm_header_rule(self) -> None:
        assert ".bm-header" in self._css()
