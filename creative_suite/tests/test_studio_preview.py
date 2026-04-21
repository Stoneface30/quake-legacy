"""Content-assertion tests for studio-preview.js and its CSS additions.

These are static-analysis (file-content) tests — no browser runtime required.
Behavioural / rendering tests require a browser and are out of scope here.
"""
from __future__ import annotations

from pathlib import Path

import pytest

FRONTEND   = Path(__file__).parent.parent / "frontend"
PREVIEW_JS = FRONTEND / "studio-preview.js"
STUDIO_CSS = FRONTEND / "studio.css"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _js() -> str:
    return PREVIEW_JS.read_text(encoding="utf-8")


def _css() -> str:
    return STUDIO_CSS.read_text(encoding="utf-8")


# ── 1. File exists ─────────────────────────────────────────────────────────────

class TestFileExists:
    def test_studio_preview_js_exists(self) -> None:
        assert PREVIEW_JS.exists(), f"Missing file: {PREVIEW_JS}"

    def test_studio_css_exists(self) -> None:
        assert STUDIO_CSS.exists(), f"Missing file: {STUDIO_CSS}"


# ── 2. window.StudioPreview exported ──────────────────────────────────────────

class TestExport:
    def test_window_studio_preview_defined(self) -> None:
        assert "window.StudioPreview" in _js(), (
            "window.StudioPreview must be assigned in studio-preview.js"
        )


# ── 3. All 6 API methods present ──────────────────────────────────────────────

class TestAPIMethods:
    @pytest.mark.parametrize("method", [
        "mount",
        "unmount",
        "loadPart",
        "seek",
        "play",
        "pause",
        "getState",
    ])
    def test_api_method_present(self, method: str) -> None:
        assert method in _js(), f"API method missing from StudioPreview: {method!r}"


# ── 4. _formatTimecode helper present ─────────────────────────────────────────

class TestFormatTimecode:
    def test_format_timecode_helper_present(self) -> None:
        assert "_formatTimecode" in _js(), (
            "_formatTimecode helper must be defined in studio-preview.js"
        )


# ── 5. Backend clip URL TODO placeholder present ──────────────────────────────

class TestTODOPlaceholder:
    def test_todo_wire_backend_clip_url(self) -> None:
        assert "TODO: wire backend clip URL" in _js(), (
            "Placeholder comment '// TODO: wire backend clip URL' must appear in "
            "studio-preview.js to mark the fetch point for clip files"
        )


# ── 6. VideoDecoder graceful degradation ──────────────────────────────────────

class TestWebCodecsDegradation:
    def test_video_decoder_availability_check(self) -> None:
        """VideoDecoder must be checked before use — graceful degradation."""
        src = _js()
        assert "VideoDecoder" in src, (
            "VideoDecoder must be referenced in studio-preview.js"
        )

    def test_graceful_degradation_message_or_comment(self) -> None:
        """A degradation message or comment must be present for unsupported browsers."""
        src = _js()
        # Accept either a user-visible message string or a descriptive comment.
        has_comment  = "VideoDecoder not available" in src
        has_ui_msg   = "VideoDecoder not supported" in src
        assert has_comment or has_ui_msg, (
            "A graceful degradation message or comment for missing VideoDecoder "
            "must appear in studio-preview.js"
        )


# ── 7. CSS additions present in studio.css ────────────────────────────────────

class TestCSSAdditions:
    def test_preview_panel_class(self) -> None:
        assert ".preview-panel" in _css(), (
            ".preview-panel CSS rule missing from studio.css"
        )

    def test_preview_canvas_id(self) -> None:
        assert "#preview-canvas" in _css(), (
            "#preview-canvas CSS rule missing from studio.css"
        )

    def test_preview_overlay_class(self) -> None:
        assert ".preview-overlay" in _css(), (
            ".preview-overlay CSS rule missing from studio.css"
        )

    def test_preview_controls_class(self) -> None:
        assert ".preview-controls" in _css(), (
            ".preview-controls CSS rule missing from studio.css"
        )

    def test_preview_info_class(self) -> None:
        assert ".preview-info" in _css(), (
            ".preview-info CSS rule missing from studio.css"
        )

    def test_preview_scrubbar_range(self) -> None:
        assert ".preview-scrubbar" in _css(), (
            ".preview-scrubbar CSS rule missing from studio.css"
        )

    def test_preview_viewport_class(self) -> None:
        assert ".preview-viewport" in _css(), (
            ".preview-viewport CSS rule missing from studio.css"
        )


# ── Bonus: Rule UI-1 — no innerHTML with untrusted data ───────────────────────

class TestUIRuleCompliance:
    def test_no_inner_html(self) -> None:
        """preview panel must not use innerHTML (Rule UI-1)."""
        assert "innerHTML" not in _js(), (
            "studio-preview.js must not use innerHTML (Rule UI-1). "
            "Use textContent or createElement instead."
        )

    def test_uses_create_element(self) -> None:
        """DOM nodes must be built with createElement (Rule UI-1)."""
        assert "createElement" in _js(), (
            "studio-preview.js must use createElement to build DOM nodes (Rule UI-1)"
        )

    def test_uses_text_content(self) -> None:
        """Dynamic text must use textContent (Rule UI-1)."""
        assert "textContent" in _js(), (
            "studio-preview.js must use textContent for dynamic text (Rule UI-1)"
        )
