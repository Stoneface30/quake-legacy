"""Runtime baseline contract — the cvar-leak guard.

Regression coverage for the failure documented in
docs/reference/free_wins_proof.md: CVAR_ARCHIVE state persisted into
q3config.cfg leaked between capture sessions with no error, warning, or
non-zero exit, and was caught only by inspecting frames.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import pantheon_runtime as pr


def test_baseline_includes_the_two_cvars_that_actually_leaked():
    """cg_fxfile leaked from the ghost-trail proof into the colour-grade
    proof; mme_saveDepth would have added a depth stream to every later
    capture. Both must be in the baseline with neutral values."""
    assert pr.RUNTIME_BASELINE["cg_fxfile"] == ""
    assert pr.RUNTIME_BASELINE["mme_saveDepth"] == "0"


def test_baseline_lines_emit_every_cvar():
    lines = pr.baseline_lines()
    body = [ln for ln in lines if not ln.startswith("//")]
    assert len(body) == len(pr.RUNTIME_BASELINE)
    for name in pr.RUNTIME_BASELINE:
        assert any(ln.startswith(f"seta {name} ") for ln in body), name


def test_empty_valued_cvar_is_quoted():
    """seta cg_fxfile with a bare empty value would be a parse error /
    no-op; it has to be written as an explicit empty string."""
    lines = pr.baseline_lines()
    assert 'seta cg_fxfile ""' in lines


def test_baseline_lines_are_deterministic_and_sorted():
    a, b = pr.baseline_lines(), pr.baseline_lines()
    assert a == b
    body = [ln for ln in a if not ln.startswith("//")]
    names = [ln.split()[1] for ln in body]
    assert names == sorted(names)


def test_override_applies():
    lines = pr.baseline_lines({"timescale": "0.5"})
    assert "seta timescale 0.5" in lines
    assert "seta timescale 1.0" not in lines


def test_unknown_cvar_override_raises():
    """A cvar absent from the baseline is exactly how the leak happened:
    it gets set by one capture and never reset by the next."""
    with pytest.raises(pr.UnknownCvarError):
        pr.baseline_lines({"cg_totallyNewThing": "1"})


def test_structural_cvar_is_not_overridable():
    with pytest.raises(pr.UnknownCvarError):
        pr.baseline_lines({"cl_noprint": "0"})


def test_baseline_hash_changes_with_overrides():
    assert pr.baseline_hash() != pr.baseline_hash({"timescale": "0.5"})
    assert pr.baseline_hash({"timescale": "0.5"}) == \
        pr.baseline_hash({"timescale": "0.5"})


def test_runtime_manifest_shape_is_stable_with_missing_inputs():
    m = pr.runtime_manifest()
    for key in ("baseline_version", "cvar_baseline_hash", "runtime_exe_sha256",
                "cfg_sha256", "camera_artifact_hash", "asset_packs",
                "fx_scripts", "grade_pack"):
        assert key in m
    assert m["runtime_exe_sha256"] is None
    assert m["cfg_sha256"] is None


def test_runtime_manifest_hashes_cfg_text():
    m = pr.runtime_manifest(cfg_text="seta timescale 1.0\n")
    assert m["cfg_sha256"] is not None
    m2 = pr.runtime_manifest(cfg_text="seta timescale 0.5\n")
    assert m["cfg_sha256"] != m2["cfg_sha256"]


def test_baseline_lines_are_pure_ascii():
    """Capture cfgs are written with encoding="ascii" (the engine tokenizer
    is byte-oriented). A non-ASCII char anywhere in the baseline raises
    UnicodeEncodeError at write time, so these lines could never reach a
    real capture cfg. That was true of the original em-dash header until
    2026-09-01 — this test is why it cannot regress."""
    for line in pr.baseline_lines():
        line.encode("ascii")
    for line in pr.baseline_lines({"timescale": "0.5"}):
        line.encode("ascii")
