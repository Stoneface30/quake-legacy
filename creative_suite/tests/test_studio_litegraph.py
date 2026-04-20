"""Content-assertion tests for studio-litegraph.js and studio.css.

Static-analysis tests: verify that the JS source file contains the expected
identifiers, API surface, and patterns.  Behavioural browser testing is covered
by separate Playwright tests.

Rules enforced:
  UI-1: no innerHTML with untrusted data
  UI-2: shared store is single source of truth (subscribe present)
"""
from __future__ import annotations

from pathlib import Path

FRONTEND      = Path(__file__).parent.parent / "frontend"
LITEGRAPH_JS  = FRONTEND / "studio-litegraph.js"
STUDIO_CSS    = FRONTEND / "studio.css"


# ── File existence ─────────────────────────────────────────────────────────────

class TestStudioLitegraphExists:
    def test_file_exists(self) -> None:
        assert LITEGRAPH_JS.exists(), f"Missing: {LITEGRAPH_JS}"

    def test_css_file_exists(self) -> None:
        assert STUDIO_CSS.exists(), f"Missing: {STUDIO_CSS}"


# ── window.StudioEffects export ────────────────────────────────────────────────

class TestStudioEffectsExport:
    def _src(self) -> str:
        return LITEGRAPH_JS.read_text(encoding="utf-8")

    def test_window_studio_effects_defined(self) -> None:
        assert "window.StudioEffects" in self._src()

    def test_method_mount(self) -> None:
        assert "mount" in self._src()

    def test_method_unmount(self) -> None:
        assert "unmount" in self._src()

    def test_method_load_graph(self) -> None:
        assert "loadGraph" in self._src()

    def test_method_save_graph(self) -> None:
        assert "saveGraph" in self._src()

    def test_method_clear_graph(self) -> None:
        assert "clearGraph" in self._src()

    def test_method_get_effect_chain(self) -> None:
        assert "getEffectChain" in self._src()


# ── Custom node types ──────────────────────────────────────────────────────────

class TestNodeTypeRegistration:
    def _src(self) -> str:
        return LITEGRAPH_JS.read_text(encoding="utf-8")

    def test_register_node_type_called(self) -> None:
        """LiteGraph.registerNodeType must be present."""
        assert "LiteGraph.registerNodeType" in self._src()

    def test_node_type_input_clip(self) -> None:
        assert "quake/input_clip" in self._src()

    def test_node_type_slow_motion(self) -> None:
        assert "quake/slow_motion" in self._src()

    def test_node_type_speed_up(self) -> None:
        assert "quake/speed_up" in self._src()

    def test_node_type_zoom(self) -> None:
        assert "quake/zoom" in self._src()

    def test_node_type_output_render(self) -> None:
        assert "quake/output_render" in self._src()


# ── LiteGraph availability check ───────────────────────────────────────────────

class TestLitegraphAvailabilityCheck:
    def _src(self) -> str:
        return LITEGRAPH_JS.read_text(encoding="utf-8")

    def test_typeof_litegraph_check_present(self) -> None:
        """Must guard against LiteGraph being absent at runtime."""
        assert "typeof LiteGraph" in self._src()


# ── Security / DOM safety ─────────────────────────────────────────────────────

class TestStudioLitegraphDomSafety:
    def _src(self) -> str:
        return LITEGRAPH_JS.read_text(encoding="utf-8")

    def test_no_inner_html(self) -> None:
        """Must not use innerHTML (Rule UI-1)."""
        assert "innerHTML" not in self._src()

    def test_uses_create_element(self) -> None:
        """DOM must be built with createElement, not innerHTML."""
        assert "createElement" in self._src()

    def test_uses_text_content(self) -> None:
        """Dynamic text must go through textContent."""
        assert "textContent" in self._src()


# ── Store subscription ─────────────────────────────────────────────────────────

class TestStudioLitegraphStoreIntegration:
    def _src(self) -> str:
        return LITEGRAPH_JS.read_text(encoding="utf-8")

    def test_store_subscribe_present(self) -> None:
        """Panel must subscribe to StudioStore (Rule UI-2)."""
        assert "StudioStore.subscribe" in self._src()

    def test_store_dispatch_present(self) -> None:
        """APPLY button must dispatch SET_STATUS_MSG to StudioStore."""
        assert "StudioStore.dispatch" in self._src()
        assert "SET_STATUS_MSG" in self._src()


# ── CSS rules ─────────────────────────────────────────────────────────────────

class TestStudioLitegraphCss:
    def _css(self) -> str:
        return STUDIO_CSS.read_text(encoding="utf-8")

    def test_effects_panel_rule(self) -> None:
        assert ".effects-panel" in self._css()

    def test_effects_canvas_wrap_rule(self) -> None:
        assert ".effects-canvas-wrap" in self._css()

    def test_effects_toolbar_rule(self) -> None:
        assert ".effects-toolbar" in self._css()

    def test_effects_status_rule(self) -> None:
        assert ".effects-status" in self._css()

    def test_ef_btn_rule(self) -> None:
        assert ".ef-btn" in self._css()
