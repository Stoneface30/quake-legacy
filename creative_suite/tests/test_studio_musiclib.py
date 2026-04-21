# creative_suite/tests/test_studio_musiclib.py
"""Static contract tests for studio-musiclib.js — file structure, API surface,
CSS rules, and safety invariants (no raw innerHTML)."""
from __future__ import annotations

import re
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
JS_PATH = FRONTEND_DIR / "studio-musiclib.js"
CSS_PATH = FRONTEND_DIR / "studio.css"


# ── file existence ────────────────────────────────────────────────────────────

def test_js_file_exists() -> None:
    assert JS_PATH.exists(), f"studio-musiclib.js not found at {JS_PATH}"


def test_css_file_exists() -> None:
    assert CSS_PATH.exists(), f"studio.css not found at {CSS_PATH}"


# ── window.StudioMusicLib API surface ────────────────────────────────────────

def test_window_studiomusiclib_exposed() -> None:
    src = JS_PATH.read_text(encoding="utf-8")
    assert "window.StudioMusicLib" in src or "global.StudioMusicLib" in src


def test_method_mount() -> None:
    src = JS_PATH.read_text(encoding="utf-8")
    assert "mount:" in src or "mount :" in src


def test_method_unmount() -> None:
    src = JS_PATH.read_text(encoding="utf-8")
    assert "unmount:" in src or "unmount :" in src


def test_method_load_tracks() -> None:
    src = JS_PATH.read_text(encoding="utf-8")
    assert "loadTracks:" in src or "loadTracks :" in src


def test_method_get_selected_track() -> None:
    src = JS_PATH.read_text(encoding="utf-8")
    assert "getSelectedTrack:" in src or "getSelectedTrack :" in src


# ── fetches /api/studio/part/ URL ─────────────────────────────────────────────

def test_fetches_music_endpoint() -> None:
    src = JS_PATH.read_text(encoding="utf-8")
    assert "/api/studio/part/" in src and "/music" in src


# ── CSS rules present in studio.css ──────────────────────────────────────────

def test_css_musiclib_panel() -> None:
    css = CSS_PATH.read_text(encoding="utf-8")
    assert ".musiclib-panel" in css


def test_css_ml_list() -> None:
    css = CSS_PATH.read_text(encoding="utf-8")
    assert ".ml-list" in css


def test_css_ml_track() -> None:
    css = CSS_PATH.read_text(encoding="utf-8")
    assert ".ml-track" in css


# ── safety: no innerHTML with untrusted data (Rule UI-1) ─────────────────────

def test_no_raw_innerhtml() -> None:
    src = JS_PATH.read_text(encoding="utf-8")
    # innerHTML is banned; textContent/createElement must be used instead.
    # Strip both line comments (// …) and block comments (/* … */) before
    # checking, so that a mention in a docstring doesn't trigger a false positive.
    stripped = re.sub(r"//[^\n]*", "", src)              # line comments
    stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL)  # block comments
    assert "innerHTML" not in stripped, (
        "studio-musiclib.js must not use innerHTML (Rule UI-1)"
    )
