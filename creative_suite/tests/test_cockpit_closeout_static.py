from __future__ import annotations

from pathlib import Path


FRONTEND = Path(__file__).parent.parent / "frontend"
QUEUE_JS = FRONTEND / "creative-queue.js"
PACKS_JS = FRONTEND / "creative-packs.js"
EDIT_JS = FRONTEND / "studio-edit.js"
TIMELINE_NLE_JS = FRONTEND / "studio-timeline-nle.js"
FORGE_JS = FRONTEND / "lab-forge.js"
EXTRACTION_JS = FRONTEND / "lab-extraction.js"
PAGES_JS = FRONTEND / "studio-pages.js"


def test_creative_queue_uses_variants_list_and_action_endpoints() -> None:
    src = QUEUE_JS.read_text(encoding="utf-8")
    assert "/api/variants/feed" in src
    assert "/approve" in src
    assert "/reject" in src
    assert "PATCH" not in src


def test_creative_packs_reads_gate_from_packs_status() -> None:
    src = PACKS_JS.read_text(encoding="utf-8")
    assert "/api/packs/status" in src


def test_studio_edit_retains_and_releases_play_button_subscription() -> None:
    src = EDIT_JS.read_text(encoding="utf-8")
    assert "_playBtnUnsub" in src
    assert "if (_playBtnUnsub)" in src


def test_timeline_nle_disconnects_resize_observer_on_unmount() -> None:
    src = TIMELINE_NLE_JS.read_text(encoding="utf-8")
    assert "ResizeObserver" in src
    assert ".disconnect()" in src


def test_lab_forge_reads_ready_stub_shape_instead_of_missing_status_key() -> None:
    src = FORGE_JS.read_text(encoding="utf-8")
    assert "d.ready" in src
    assert "d.status || 'idle'" not in src


def test_lab_extraction_logs_stub_job_id_instead_of_fake_fragment_counts() -> None:
    src = EXTRACTION_JS.read_text(encoding="utf-8")
    assert "job_id" in src
    assert "fragments" not in src


def test_studio_pages_sync_url_rebuilds_query_from_mode_and_page_only() -> None:
    src = PAGES_JS.read_text(encoding="utf-8")
    assert "window.location.origin + window.location.pathname" in src
