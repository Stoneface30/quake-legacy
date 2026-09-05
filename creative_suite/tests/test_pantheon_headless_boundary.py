"""HL-1: PANTHEON is headless-first. Wolfcam is a backend, never the engine.

The boundary is enforced statically, on the import graph, because that is the
one place a violation cannot hide behind a mock: a headless module that
imports `wolfcam_capture`, spawns a process, or reaches for a render backend
has put the running Quake client back in charge of game truth.

Backend contamination that has already cost sessions (latched cvars applying a
launch late, cvars that never registered, archived q3config settings leaking
between experiments, SDL falling back to 856x480, +demo dropped past 32 `+`
groups) must be unable to touch performance truth, scene truth, timing truth,
camera intent or synthetic action. The only way to make that impossible is to
keep every one of those layers free of the process that produces it.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from engine.pantheon import backends

PANTHEON = Path(__file__).resolve().parents[2] / "engine" / "pantheon"

# Modules that ARE the engine. None of them may know a renderer exists.
HEADLESS = {
    "performance",      # PerformanceTrace extraction
    "performance_index",  # corpus-wide PerformanceTrace index (SQLite)
    "frame_truth",      # FrameTruth
    "scenario",         # RoundScenario authoring
    "compiler",         # intent -> .dm_73 grammar
    "navigation",       # NavigationTruth
    "motion_reference", # movement statistics from real demos
    "instruction",      # instruction layer
    "roster",           # cast inventory
    "presenter",        # PresenterProfile
}

# Modules that are allowed to touch a backend or spawn a process, and why.
BACKEND_ALLOWED = {
    "backends",         # the interface itself
    "shot",             # WOLFCAM_REFERENCE implementation
    "cvar_probe",       # RUNTIME_CAPABILITY_PROOF
    "measure",          # pixel measurement of a delivered AVI (ffmpeg)
    "voice",            # TTS / ffmpeg audio, not a game backend
    "dialogue_mix",     # ffmpeg audio mux, not a game backend
    "presenter_film",   # films a presenter proof
    "ab_scene",         # A/B capture harness
    "cast_proof", "presenter_proof", "instruction_proof", "proofs",
    "proof0_color", "proof_b_identity", "proof_c_rails",
    "ca_explainer",     # end-to-end explainer, may render
    "color_format",     # a fact about the Wolfcam cvar format, decided on pixels
}

FORBIDDEN_IMPORTS = {
    "subprocess",
    "creative_suite.engine.wolfcam_capture",
    "engine.pantheon.shot",
    "engine.pantheon.backends",
    "engine.pantheon.cvar_probe",
    "engine.pantheon.ab_scene",
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
            out.update(f"{node.module}.{a.name}" for a in node.names)
    return out


def _headless_modules() -> list[Path]:
    return sorted(PANTHEON / f"{m}.py" for m in HEADLESS if (PANTHEON / f"{m}.py").exists())


@pytest.mark.parametrize("path", _headless_modules(), ids=lambda p: p.stem)
def test_headless_module_never_imports_a_backend(path: Path):
    hit = sorted(i for i in _imports(path)
                 if i in FORBIDDEN_IMPORTS
                 or i.startswith("creative_suite.engine.wolfcam_capture"))
    assert not hit, (
        f"{path.name} imports {hit}. HL-1: PerformanceTrace extraction, "
        "action compilation, semantic validation, retargeting, aim and "
        "projectile reproduction and FrameTruth generation run without a "
        "renderer. Move the backend call behind engine.pantheon.backends.")


def test_every_pantheon_module_is_classified():
    """A new module must declare which side of the line it lives on."""
    names = {p.stem for p in PANTHEON.glob("*.py")} - {"__init__"}
    unclassified = sorted(names - HEADLESS - BACKEND_ALLOWED)
    assert not unclassified, (
        f"classify {unclassified} as HEADLESS or BACKEND_ALLOWED in "
        f"{Path(__file__).name}")


def test_backend_use_is_the_closed_list():
    """Wolfcam is allowed exactly four jobs. Nothing else is a valid reason
    to launch it."""
    assert {u.name for u in backends.BackendUse} == {
        "REFERENCE_RENDER",
        "EXTERNAL_DM73_VALIDATION",
        "RUNTIME_CAPABILITY_PROOF",
        "FINAL_QUAKE_BEAUTY",
    }


def test_render_refuses_an_unknown_backend(tmp_path: Path):
    with pytest.raises(KeyError):
        backends.render("BLENDER_VFX", shot=None, out_dir=tmp_path,
                        use=backends.BackendUse.REFERENCE_RENDER)


def test_render_requires_a_declared_use(tmp_path: Path):
    """Launching a backend without saying why is the pattern that put Wolfcam
    in charge. The dispatcher does not accept it."""
    with pytest.raises(TypeError):
        backends.render("WOLFCAM_REFERENCE", shot=None, out_dir=tmp_path)  # type: ignore[call-arg]


def test_wolfcam_backend_delegates_to_shot_render(monkeypatch, tmp_path: Path):
    calls: list[tuple] = []

    def fake_render(spec, out_dir, *, base_ms=1000):
        calls.append((spec, out_dir, base_ms))
        return out_dir / "x.avi"

    monkeypatch.setattr(backends, "_wolfcam_render", fake_render)
    sentinel = object()
    out = backends.render("WOLFCAM_REFERENCE", shot=sentinel, out_dir=tmp_path,
                          use=backends.BackendUse.REFERENCE_RENDER)
    assert out == tmp_path / "x.avi"
    assert calls == [(sentinel, tmp_path, 1000)]
