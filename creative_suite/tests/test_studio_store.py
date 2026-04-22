"""Content-assertion tests for studio-store.js and studio-app.js.

These are static-analysis tests: they verify that the JS source files contain
the expected identifiers, API surface, and URL strings.  Behavioural testing of
browser JS requires a browser (covered by future Playwright tests).
"""
from __future__ import annotations

from pathlib import Path

import pytest

FRONTEND = Path(__file__).parent.parent / "frontend"
STORE_JS = FRONTEND / "studio-store.js"
APP_JS   = FRONTEND / "studio-app.js"


# ── studio-store.js ───────────────────────────────────────────────────────────

class TestStudioStore:
    @pytest.fixture(autouse=True)
    def source(self) -> str:
        assert STORE_JS.exists(), f"Missing file: {STORE_JS}"
        return STORE_JS.read_text(encoding="utf-8")

    @pytest.fixture
    def source(self) -> str:  # type: ignore[override]
        return STORE_JS.read_text(encoding="utf-8")

    def _src(self) -> str:
        return STORE_JS.read_text(encoding="utf-8")

    def test_file_exists(self) -> None:
        assert STORE_JS.exists()

    def test_window_studio_store_exported(self) -> None:
        assert "window.StudioStore" in self._src()

    def test_get_state_exported(self) -> None:
        assert "getState" in self._src()

    def test_set_state_exported(self) -> None:
        assert "setState" in self._src()

    def test_subscribe_exported(self) -> None:
        assert "subscribe" in self._src()

    def test_dispatch_exported(self) -> None:
        assert "dispatch" in self._src()

    # ── All eight action types present ──────────────────────────────────────

    @pytest.mark.parametrize("action_type", [
        "SET_ACTIVE_PAGE",
        "SET_ACTIVE_PART",
        "SET_PARTS",
        "SET_CLIPS",
        "SET_PLAYING",
        "SET_CURRENT_TIME",
        "SET_BUILD_STATUS",
        "SET_STATUS_MSG",
    ])
    def test_action_type_present(self, action_type: str) -> None:
        assert action_type in self._src(), f"Action type missing: {action_type!r}"

    def test_clips_fetch_url_template(self) -> None:
        """Store must build the /api/studio/part/{n}/clips URL."""
        src = self._src()
        assert "/api/studio/part/" in src
        assert "/clips" in src

    def test_initial_state_keys(self) -> None:
        """All INITIAL_STATE keys must appear in the store."""
        src = self._src()
        for key in ("activePage", "activePart", "parts", "clips", "isPlaying",
                    "currentTime", "buildStatus", "statusMessage"):
            assert key in src, f"Initial state key missing: {key!r}"

    def test_no_inner_html(self) -> None:
        """Store must not use innerHTML (Rule UI-1)."""
        assert "innerHTML" not in self._src()


# ── studio-app.js ─────────────────────────────────────────────────────────────

class TestStudioApp:
    def _src(self) -> str:
        return APP_JS.read_text(encoding="utf-8")

    def test_file_exists(self) -> None:
        assert APP_JS.exists(), f"Missing file: {APP_JS}"

    def test_dom_content_loaded_listener(self) -> None:
        assert "DOMContentLoaded" in self._src()

    def test_parts_fetch_url(self) -> None:
        assert "/api/studio/parts" in self._src()

    def test_rebuild_fetch_url(self) -> None:
        src = self._src()
        assert "/api/phase1/parts/" in src
        assert "/rebuild" in src

    def test_dispatches_set_parts(self) -> None:
        assert "SET_PARTS" in self._src()

    def test_dispatches_set_active_part(self) -> None:
        assert "SET_ACTIVE_PART" in self._src()

    def test_dispatches_set_active_page(self) -> None:
        assert "SET_ACTIVE_PAGE" in self._src()

    def test_dispatches_set_playing(self) -> None:
        assert "SET_PLAYING" in self._src()

    def test_dispatches_set_current_time(self) -> None:
        assert "SET_CURRENT_TIME" in self._src()

    def test_dispatches_set_build_status(self) -> None:
        assert "SET_BUILD_STATUS" in self._src()

    def test_dispatches_set_status_msg(self) -> None:
        assert "SET_STATUS_MSG" in self._src()

    def test_wires_part_select(self) -> None:
        assert "part-select" in self._src()

    def test_wires_btn_play(self) -> None:
        assert "btn-play" in self._src()

    def test_wires_btn_rew(self) -> None:
        assert "btn-rew" in self._src()

    def test_wires_btn_fwd(self) -> None:
        assert "btn-fwd" in self._src()

    def test_wires_btn_rebuild(self) -> None:
        assert "btn-rebuild" in self._src()

    def test_wires_status_text(self) -> None:
        assert "status-text" in self._src()

    def test_no_inner_html(self) -> None:
        """App must not use innerHTML (Rule UI-1)."""
        assert "innerHTML" not in self._src()

    def test_uses_text_content_not_inner_html(self) -> None:
        """textContent must be used for dynamic text (Rule UI-1)."""
        assert "textContent" in self._src()

    def test_uses_create_element_for_options(self) -> None:
        """Options must be built with createElement, not innerHTML."""
        assert "createElement" in self._src()
