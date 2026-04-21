"""Content-assertion tests for studio-timeline.js and studio.css.

Static-analysis tests: verify that the JS source file contains the expected
identifiers, API surface, and patterns.  Behavioural browser testing is covered
by separate Playwright tests.

Rules enforced:
  UI-1: no innerHTML with untrusted data
  UI-2: shared store is single source of truth (subscribe present)
"""
from __future__ import annotations

from pathlib import Path

FRONTEND = Path(__file__).parent.parent / "frontend"
TIMELINE_JS = FRONTEND / "studio-timeline.js"
STUDIO_CSS  = FRONTEND / "studio.css"


# ── File existence ─────────────────────────────────────────────────────────────

class TestStudioTimelineExists:
    def test_file_exists(self) -> None:
        assert TIMELINE_JS.exists(), f"Missing: {TIMELINE_JS}"

    def test_css_file_exists(self) -> None:
        assert STUDIO_CSS.exists(), f"Missing: {STUDIO_CSS}"


# ── window.StudioTimeline export ───────────────────────────────────────────────

class TestStudioTimelineExport:
    def _src(self) -> str:
        return TIMELINE_JS.read_text(encoding="utf-8")

    def test_window_studio_timeline_defined(self) -> None:
        assert "window.StudioTimeline" in self._src()

    def test_method_mount(self) -> None:
        assert "mount" in self._src()

    def test_method_unmount(self) -> None:
        assert "unmount" in self._src()

    def test_method_load_clips(self) -> None:
        assert "loadClips" in self._src()

    def test_method_get_selected_clip(self) -> None:
        assert "getSelectedClip" in self._src()

    def test_method_set_playhead(self) -> None:
        assert "setPlayhead" in self._src()


# ── Store subscription ─────────────────────────────────────────────────────────

class TestStudioTimelineStoreIntegration:
    def _src(self) -> str:
        return TIMELINE_JS.read_text(encoding="utf-8")

    def test_store_subscribe_present(self) -> None:
        """Panel must subscribe to StudioStore (Rule UI-2)."""
        assert "StudioStore.subscribe" in self._src()

    def test_listens_to_clips_change(self) -> None:
        """Must react to clips state changes."""
        assert "loadClips" in self._src()
        assert "clips" in self._src()

    def test_listens_to_current_time_change(self) -> None:
        """Must react to currentTime changes."""
        assert "currentTime" in self._src()
        assert "setPlayhead" in self._src()


# ── Security / DOM safety ─────────────────────────────────────────────────────

class TestStudioTimelineDomSafety:
    def _src(self) -> str:
        return TIMELINE_JS.read_text(encoding="utf-8")

    def test_no_inner_html(self) -> None:
        """Must not use innerHTML (Rule UI-1)."""
        assert "innerHTML" not in self._src()

    def test_uses_create_element(self) -> None:
        """DOM must be built with createElement, not innerHTML."""
        assert "createElement" in self._src()

    def test_uses_text_content(self) -> None:
        """Dynamic text must go through textContent."""
        assert "textContent" in self._src()


# ── CSS rules ─────────────────────────────────────────────────────────────────

class TestStudioTimelineCss:
    def _css(self) -> str:
        return STUDIO_CSS.read_text(encoding="utf-8")

    def test_timeline_panel_rule(self) -> None:
        assert ".timeline-panel" in self._css()

    def test_timeline_canvas_wrap_rule(self) -> None:
        assert ".timeline-canvas-wrap" in self._css()

    def test_timeline_toolbar_rule(self) -> None:
        assert ".timeline-toolbar" in self._css()

    def test_timeline_footer_rule(self) -> None:
        assert ".timeline-footer" in self._css()

    def test_tl_btn_rule(self) -> None:
        assert ".tl-btn" in self._css()
