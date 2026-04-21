"""Tests for P3-T5: MLT verification gates.

Three checks:
1. The decision record doc exists.
2. The doc contains a Verdict line with a valid decision.
3. The /api/studio/status endpoint exposes an mlt_available bool field.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# ── Gate 1: doc exists ────────────────────────────────────────────────────────

_MLT_DOC = Path(__file__).parents[2] / "docs" / "reference" / "mlt-verification.md"


def test_mlt_doc_exists() -> None:
    """docs/reference/mlt-verification.md must exist."""
    assert _MLT_DOC.exists(), f"MLT verification doc not found at {_MLT_DOC}"


# ── Gate 2: doc has a valid verdict ──────────────────────────────────────────

_VALID_VERDICTS = {"ADOPT", "DEFER", "REJECT"}


def test_mlt_doc_has_verdict() -> None:
    """The doc must contain 'Verdict:' and one of ADOPT / DEFER / REJECT."""
    assert _MLT_DOC.exists(), "MLT verification doc missing — run test_mlt_doc_exists first"
    text = _MLT_DOC.read_text(encoding="utf-8")
    assert "Verdict:" in text, "Doc does not contain a 'Verdict:' line"
    found = any(v in text for v in _VALID_VERDICTS)
    assert found, f"Doc contains 'Verdict:' but no valid verdict word ({_VALID_VERDICTS})"


# ── Gate 3: status endpoint exposes mlt_available ────────────────────────────

def test_status_endpoint_has_mlt_field(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/studio/status must return JSON with an mlt_available bool key."""
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path))

    from creative_suite.app import create_app

    app = create_app()
    client = TestClient(app)
    r = client.get("/api/studio/status")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    body = r.json()
    assert "mlt_available" in body, f"'mlt_available' key missing from status response: {body}"
    assert isinstance(body["mlt_available"], bool), (
        f"'mlt_available' must be a bool, got {type(body['mlt_available'])}: {body}"
    )
