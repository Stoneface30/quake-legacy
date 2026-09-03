"""Running the suite must not rewrite committed reference truth.

A canary that writes its measurement into docs/reference on every run makes a
tracked file disagree with itself for reasons nobody can reconstruct: was
that diff a deliberate re-measurement, or did somebody run a script against
whichever AVI was lying around? Reverting after the fact is not a fix, because
by then the question has already been asked.

So the guard is structural: writing committed reference data requires an
explicit flag, and these tests fail if any module goes back to doing it by
default.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CANARIES = REPO_ROOT / "creative_suite" / "engine" / "canaries"
REFERENCE_DIR = REPO_ROOT / "docs" / "reference"


def test_the_cadence_canary_writes_scratch_unless_told_otherwise():
    from creative_suite.engine.canaries import v2_cadence as vc
    sig = inspect.signature(vc.main)
    assert "write_reference" in sig.parameters
    assert sig.parameters["write_reference"].default is False
    assert vc.REFERENCE.name == "v2_frame_cadence.json"
    assert REFERENCE_DIR in vc.REFERENCE.parents


def test_no_canary_hardcodes_a_write_into_docs_reference():
    """A literal path into docs/reference inside a write call is the exact
    shape of the bug: the destination is decided at edit time rather than by
    whoever runs the tool."""
    offenders = []
    for py in CANARIES.glob("*.py"):
        src = py.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            v = node.value.replace("\\", "/")
            if "docs/reference" in v and v.endswith(".json"):
                offenders.append(f"{py.name}: {node.value}")
    assert not offenders, (
        "canaries must reach committed reference data through a named "
        f"constant guarded by an explicit flag: {offenders}")


def test_importing_a_canary_writes_nothing():
    """Import must be inert. A module that measures on import turns every
    collection pass into a side effect."""
    before = {p: p.read_bytes() for p in REFERENCE_DIR.glob("*.json")}
    import importlib
    for name in ("v2_cadence", "cut_identity", "runtime_truth"):
        try:
            importlib.import_module(f"creative_suite.engine.canaries.{name}")
        except ImportError:
            pytest.skip(f"{name} not importable in this environment")
    after = {p: p.read_bytes() for p in REFERENCE_DIR.glob("*.json")}
    changed = [p.name for p in before if before[p] != after.get(p)]
    assert not changed, f"import mutated {changed}"
