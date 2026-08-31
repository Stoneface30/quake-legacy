"""Both branding paths: configured original asset, and procedural fallback."""
import os
from pathlib import Path

import pytest

from creative_suite.engine import pantheon_intro as pi


def test_no_env_uses_procedural_fallback(monkeypatch):
    monkeypatch.delenv(pi.INTRO_ASSET_ENV, raising=False)
    assert pi.original_intro_asset() is None


def test_env_pointing_at_real_file_is_used(monkeypatch, tmp_path):
    asset = tmp_path / "IntroPart2.mp4"
    asset.write_bytes(b"\0" * 64)
    monkeypatch.setenv(pi.INTRO_ASSET_ENV, str(asset))
    assert pi.original_intro_asset() == asset


def test_env_pointing_at_missing_file_falls_back(monkeypatch, tmp_path):
    """A stale path must not break rendering -- fall back, don't crash."""
    monkeypatch.setenv(pi.INTRO_ASSET_ENV, str(tmp_path / "gone.mp4"))
    assert pi.original_intro_asset() is None


def test_env_pointing_at_a_directory_falls_back(monkeypatch, tmp_path):
    monkeypatch.setenv(pi.INTRO_ASSET_ENV, str(tmp_path))
    assert pi.original_intro_asset() is None


def test_blank_env_is_ignored(monkeypatch):
    monkeypatch.setenv(pi.INTRO_ASSET_ENV, "   ")
    assert pi.original_intro_asset() is None
