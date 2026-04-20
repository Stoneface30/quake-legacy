"""Content-assertion tests for studio-inspector.js and studio.css.

Static-analysis tests: verify that the JS source file contains the expected
identifiers, API surface, and patterns.  Behavioural browser testing is
covered by separate Playwright tests.

Rules enforced:
  UI-1: no innerHTML with untrusted data
  UI-2: shared store is single source of truth (subscribe present)

Vendor API findings (read from vendor files):
  - tweakpane.js 4.0.5: ES-module file, exports { Pane } via `export {}`
    at EOF — no automatic window global when loaded as a classic <script>.
    Inspector checks window.Tweakpane.Pane and window.Pane as fallbacks.
  - theatre-core-studio.js: IIFE, sets window.Theatre = { core, studio }.
    Inspector uses Theatre.core only (Apache-2.0).
"""
from __future__ import annotations

from pathlib import Path

FRONTEND     = Path(__file__).parent.parent / "frontend"
INSPECTOR_JS = FRONTEND / "studio-inspector.js"
STUDIO_CSS   = FRONTEND / "studio.css"


# ── File existence ─────────────────────────────────────────────────────────────

class TestStudioInspectorExists:
    def test_inspector_js_exists(self) -> None:
        assert INSPECTOR_JS.exists(), f"Missing: {INSPECTOR_JS}"

    def test_css_file_exists(self) -> None:
        assert STUDIO_CSS.exists(), f"Missing: {STUDIO_CSS}"


# ── window.StudioInspector export ─────────────────────────────────────────────

class TestStudioInspectorExport:
    def _src(self) -> str:
        return INSPECTOR_JS.read_text(encoding="utf-8")

    def test_window_studio_inspector_defined(self) -> None:
        assert "window.StudioInspector" in self._src()

    def test_method_mount(self) -> None:
        assert "mount" in self._src()

    def test_method_unmount(self) -> None:
        assert "unmount" in self._src()

    def test_method_inspect_clip(self) -> None:
        assert "inspectClip" in self._src()

    def test_method_inspect_effects(self) -> None:
        assert "inspectEffects" in self._src()

    def test_method_get_values(self) -> None:
        assert "getValues" in self._src()


# ── Store subscription ─────────────────────────────────────────────────────────

class TestStudioInspectorStoreIntegration:
    def _src(self) -> str:
        return INSPECTOR_JS.read_text(encoding="utf-8")

    def test_store_subscribe_present(self) -> None:
        """Panel must subscribe to StudioStore (Rule UI-2)."""
        assert "StudioStore.subscribe" in self._src()

    def test_reacts_to_clips_change(self) -> None:
        """Must react to clips state changes."""
        assert "state.clips" in self._src()


# ── Tweakpane availability check ───────────────────────────────────────────────

class TestTweakpaneAvailabilityCheck:
    def _src(self) -> str:
        return INSPECTOR_JS.read_text(encoding="utf-8")

    def test_tweakpane_availability_guard_present(self) -> None:
        """Inspector must check for Tweakpane before attempting to use it."""
        src = self._src()
        # Must check whether Tweakpane / Pane is available rather than
        # assuming it — any one of these patterns satisfies the requirement.
        has_guard = (
            "typeof" in src and (
                "Tweakpane" in src or
                "Pane" in src
            )
        )
        assert has_guard, "No Tweakpane availability guard found in inspector JS"

    def test_placeholder_when_unavailable(self) -> None:
        """When Tweakpane is absent, a fallback / placeholder path must exist."""
        src = self._src()
        assert "not available" in src or "placeholder" in src.lower()


# ── Tweakpane folder names ─────────────────────────────────────────────────────

class TestTweakpaneFolderNames:
    def _src(self) -> str:
        return INSPECTOR_JS.read_text(encoding="utf-8")

    def test_clip_info_folder(self) -> None:
        assert "CLIP INFO" in self._src()

    def test_overrides_folder(self) -> None:
        assert "OVERRIDES" in self._src()


# ── Override property names ────────────────────────────────────────────────────

class TestOverrideProperties:
    def _src(self) -> str:
        return INSPECTOR_JS.read_text(encoding="utf-8")

    def test_head_trim_property(self) -> None:
        assert "head_trim" in self._src()

    def test_tail_trim_property(self) -> None:
        assert "tail_trim" in self._src()

    def test_slow_rate_property(self) -> None:
        assert "slow_rate" in self._src()


# ── CSS rules ─────────────────────────────────────────────────────────────────

class TestStudioInspectorCss:
    def _css(self) -> str:
        return STUDIO_CSS.read_text(encoding="utf-8")

    def test_inspector_panel_rule(self) -> None:
        assert ".inspector-panel" in self._css()

    def test_inspector_pane_wrap_rule(self) -> None:
        assert ".inspector-pane-wrap" in self._css()

    def test_inspector_toolbar_rule(self) -> None:
        assert ".inspector-toolbar" in self._css()


# ── Security / DOM safety ──────────────────────────────────────────────────────

class TestStudioInspectorDomSafety:
    def _src(self) -> str:
        return INSPECTOR_JS.read_text(encoding="utf-8")

    def test_no_inner_html(self) -> None:
        """Must not use innerHTML (Rule UI-1)."""
        assert "innerHTML" not in self._src()

    def test_uses_create_element(self) -> None:
        """DOM must be built with createElement, not innerHTML."""
        assert "createElement" in self._src()

    def test_uses_text_content(self) -> None:
        """Dynamic text must go through textContent."""
        assert "textContent" in self._src()
