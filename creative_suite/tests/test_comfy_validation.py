"""Spec §11.3 — workflow drift mitigation.

Asserts:
  - validate_workflow_file returns True for the shipped img2img_sdxl.json
  - validate_workflow_file returns False (not raise) when a workflow is
    missing a required placeholder — e.g. a hypothetical ComfyUI update that
    renamed the input-image node.
  - The boot-time call from app.create_app is wired and non-fatal on drift.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from creative_suite.comfy.client import (
    REQUIRED_PLACEHOLDERS,
    validate_workflow_file,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SHIPPED = (
    REPO_ROOT / "creative_suite" / "comfy" / "workflows" / "img2img_sdxl.json"
)


def test_shipped_workflow_has_all_required_placeholders() -> None:
    assert validate_workflow_file(SHIPPED) is True


def test_required_placeholders_are_documented() -> None:
    # Lock the contract so a silent change draws a failing test.
    assert REQUIRED_PLACEHOLDERS == ("{{input_image}}", "{{prompt}}", "{{seed}}")


def test_validate_reports_false_when_placeholder_missing(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # Forge a drifted workflow — ComfyUI renamed {{input_image}} to
    # {{source_image}}. Our check must flag it without raising.
    bad = json.loads(SHIPPED.read_text(encoding="utf-8"))
    bad["2"]["inputs"]["image"] = "{{source_image}}"
    # _placeholders is documentation; strip so the token truly disappears.
    bad.pop("_placeholders", None)
    drifted = tmp_path / "drifted.json"
    drifted.write_text(json.dumps(bad), encoding="utf-8")

    with caplog.at_level(logging.WARNING, logger="creative_suite.comfy"):
        assert validate_workflow_file(drifted) is False
    assert any("input_image" in r.message for r in caplog.records)


def test_validate_handles_missing_file(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    ghost = tmp_path / "does_not_exist.json"
    with caplog.at_level(logging.WARNING, logger="creative_suite.comfy"):
        assert validate_workflow_file(ghost) is False
    assert any("missing" in r.message for r in caplog.records)


def test_boot_check_does_not_crash_app_on_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prove the boot path swallows drift — app.create_app must still return."""
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path / "storage"))
    # Patch validator to simulate a drifted workflow at boot.
    import creative_suite.app as app_mod
    import creative_suite.comfy.client as client_mod

    calls: list[Path] = []

    def fake_validator(path: Path) -> bool:
        calls.append(path)
        return False  # drift — must NOT raise

    monkeypatch.setattr(client_mod, "validate_workflow_file", fake_validator)
    # `app.py` imports the symbol lazily inside create_app, so the monkeypatch
    # on client_mod is the one create_app's local import resolves.
    _ = app_mod.create_app()
    assert calls, "boot check should invoke validate_workflow_file"
    assert calls[0].name == "img2img_sdxl.json"
