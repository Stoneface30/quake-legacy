"""Content-assertion tests for studio-audio.js and studio.css.

Static-analysis tests: verify that the JS source file contains the expected
identifiers, API surface, and patterns.  Behavioural browser testing is covered
by separate Playwright tests.

Rules enforced:
  UI-1: no innerHTML with untrusted data
  UI-2: shared store is single source of truth (subscribe present)
"""
from __future__ import annotations

from pathlib import Path

FRONTEND  = Path(__file__).parent.parent / "frontend"
AUDIO_JS  = FRONTEND / "studio-audio.js"
STUDIO_CSS = FRONTEND / "studio.css"


# ── File existence ─────────────────────────────────────────────────────────────

class TestStudioAudioExists:
    def test_js_file_exists(self) -> None:
        assert AUDIO_JS.exists(), f"Missing: {AUDIO_JS}"

    def test_css_file_exists(self) -> None:
        assert STUDIO_CSS.exists(), f"Missing: {STUDIO_CSS}"


# ── window.StudioAudio export ──────────────────────────────────────────────────

class TestStudioAudioExport:
    def _src(self) -> str:
        return AUDIO_JS.read_text(encoding="utf-8")

    def test_window_studio_audio_defined(self) -> None:
        assert "window.StudioAudio" in self._src()

    def test_method_mount(self) -> None:
        assert "mount" in self._src()

    def test_method_unmount(self) -> None:
        assert "unmount" in self._src()

    def test_method_load_audio(self) -> None:
        assert "loadAudio" in self._src()

    def test_method_set_playhead(self) -> None:
        assert "setPlayhead" in self._src()

    def test_method_get_zoom(self) -> None:
        assert "getZoom" in self._src()

    def test_method_set_zoom(self) -> None:
        assert "setZoom" in self._src()


# ── Store subscription ─────────────────────────────────────────────────────────

class TestStudioAudioStoreIntegration:
    def _src(self) -> str:
        return AUDIO_JS.read_text(encoding="utf-8")

    def test_store_subscribe_present(self) -> None:
        """Panel must subscribe to StudioStore (Rule UI-2)."""
        assert "StudioStore.subscribe" in self._src()

    def test_listens_to_is_playing(self) -> None:
        """Must react to isPlaying state changes."""
        assert "isPlaying" in self._src()

    def test_listens_to_current_time(self) -> None:
        """Must react to currentTime state changes."""
        assert "currentTime" in self._src()


# ── Security / DOM safety ──────────────────────────────────────────────────────

class TestStudioAudioDomSafety:
    def _src(self) -> str:
        return AUDIO_JS.read_text(encoding="utf-8")

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

class TestStudioAudioCss:
    def _css(self) -> str:
        return STUDIO_CSS.read_text(encoding="utf-8")

    def test_audio_panel_rule(self) -> None:
        assert ".audio-panel" in self._css()

    def test_audio_tracks_wrap_rule(self) -> None:
        assert ".audio-tracks-wrap" in self._css()

    def test_audio_toolbar_rule(self) -> None:
        assert ".audio-toolbar" in self._css()

    def test_audio_no_support_rule(self) -> None:
        assert ".audio-no-support" in self._css()


# ── Branding ──────────────────────────────────────────────────────────────────

class TestStudioAudioBranding:
    def _src(self) -> str:
        return AUDIO_JS.read_text(encoding="utf-8")

    def test_pantheon_gold_cursor(self) -> None:
        """cursorColor must use PANTHEON gold #C9A84C."""
        assert "#C9A84C" in self._src()


# ── Graceful degradation ──────────────────────────────────────────────────────

class TestStudioAudioGracefulDegradation:
    def _src(self) -> str:
        return AUDIO_JS.read_text(encoding="utf-8")

    def test_multitrack_availability_check(self) -> None:
        """Must guard against Multitrack being unavailable."""
        assert "typeof" in self._src()
        assert "Multitrack" in self._src()
