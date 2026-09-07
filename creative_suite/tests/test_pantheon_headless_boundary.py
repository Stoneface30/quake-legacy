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
    "performance_index",  # corpus-wide discovery index (lightweight rows, no trace copies)
    "store",            # where derived performance data lives (configurable root)
    "disk_policy",      # three write thresholds; shutil only
    "real_action_proof",  # extract -> compile -> compare, headless
    "headless",         # the loop: extract / compile / reextract / compare / run
    "retarget",         # EXACT_WORLD / LOCAL_FRAME rigid transform + map validity
    "compare",          # PerformanceDiff
    "action_graph",     # semantic reading of a trace, with evidence
    "map_spatial_index",  # behavioural geography from real play
    "performance_library",  # anonymous PERF: references over the index
    "headless_bench",   # loop timings, no render
    "performance_templates",  # reusable real motion, chosen by measured facts
    "trace_cache",      # which rebuilt traces earn a stored copy, and why
    "visual_proof",     # what a person judged on screen; reads a db, films nothing
    "effect_recipes",   # the film grammar as semantics; no backend detail
    "possibilities",    # which recipes a moment can carry, and why
    "ideas",            # the director's 306-item master list, verbatim
    "director_notes",   # the original free-form notes it came from
    "creative_intent",  # a human note, kept as written
    "review_moment",    # the one object the reviewer reads
    "backend_planner",  # which backend does which pass; plans, never launches
    "defaults",         # versioned project profiles; values, not behaviour
    "maturity",         # how finished each subsystem is, by measurement
    "choreography",     # recipe + moment -> plan; traces the map, films nothing
    "map_geography",    # height layers, watershed regions, route graph (review authority, adopted)
    "map_context",      # place / approach words for a moment, over map_geography
    "geography",        # the one API over map_geography + map_spatial_index
    "presenter_performance_proof",  # Crash enters via a real recording, headless first
    "frame_truth",      # FrameTruth
    # The renderer's input DTO. Headless by construction: it projects one
    # instant of FrameTruth and imports nothing that can launch a game.
    "render_frame",
    # writes MD3 geometry files. Pure format arithmetic: no game, no backend.
    "md3_writer",
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
    "offscreen",        # hosts the renderer on a hidden desktop; spawns processes
    "render_permit",    # the one gate every launch asks; reads the process list
    "shot",             # WOLFCAM_REFERENCE implementation
    "cvar_probe",       # RUNTIME_CAPABILITY_PROOF
    "measure",          # pixel measurement of a delivered AVI (ffmpeg)
    "voice",            # TTS / ffmpeg audio, not a game backend
    "dialogue_mix",     # ffmpeg audio mux, not a game backend
    "presenter_film",   # films a presenter proof
    "presenter_camera_film",  # films PRESENTER_CAMERA_DIALOGUE_PROOF_02
    "ab_scene",         # A/B capture harness
    "first_recipe_proof",  # the one end-to-end run: it films
    "engine_census",    # asks the running binary what it has; one session
    "engine_inventory", # the raw inventory and its grades; reads files only
    "conformance",      # the 10-case backend A/B: it films both legs
    "cast_proof", "presenter_proof", "instruction_proof", "proofs",
    "proof0_color", "proof_b_identity", "proof_c_rails",
    "ca_explainer",     # end-to-end explainer, may render
    "color_format",     # a fact about the Wolfcam cvar format, decided on pixels
    "capabilities",     # what a backend can do and how we know; names cvars as backend detail
    "visual_profile",   # the one translator from film words to backend values
    "doctor",           # the self-test: it REPLACES Popen to prove nothing spawns,
                        # and reads the permit to report it -- launches nothing
}

# A THIRD CLASS, because two were not enough.
#
# These modules choose between backends, or record which one a proof was taken
# against, or quote the director naming one. They must still never IMPORT a
# backend and never launch anything -- what they may do is say the name. A
# planner that cannot name what it is planning for is not a planner, and a
# proof that cannot say what it was filmed on is not evidence.
NAMES_BACKENDS_AS_DATA = {
    "backend_planner",  # its whole job is choosing one
    "effect_recipes",   # each recipe says which backend would suit it
    "visual_proof",     # a proof is only valid for the backend it was taken on
    "ideas",            # the director's own words, and they name backends
    "director_notes",   # likewise, verbatim
    "defaults",         # a profile names the engine cfg it expects
    "maturity",         # it reports per backend, so it names them
    "engine_inventory", # its subject IS the raw names; it launches nothing
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


# ── the audit goes past imports: no backend vocabulary in game truth ────────

# Words that belong below the boundary. Found as an identifier or a string
# literal in a HEADLESS module, they mean a renderer concern leaked upward.
# Comments and docstrings are exempt: explaining WHY the boundary exists is
# allowed; depending on what is behind it is not.
BACKEND_TOKENS = ("wolfcam", "capture.cfg", "cvar", ".avi", "cam10", "Popen",
                  "subprocess", "r_mode", "cg_", "+set", "fs_homepath")
# `cvar` is what cvar_probe asks the RUNNING engine about; a headless module
# has no engine to ask.


def _code_tokens(path: Path) -> list[tuple[int, str]]:
    """Identifiers, attribute names and string literals -- not comments, not
    docstrings."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    doc_nodes: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)                     and isinstance(body[0].value.value, str):
                doc_nodes.add(id(body[0].value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            out.append((node.lineno, node.id))
        elif isinstance(node, ast.Attribute):
            out.append((node.lineno, node.attr))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in doc_nodes:
            out.append((node.lineno, node.value))
    return out


def _vocabulary_modules() -> list[Path]:
    return [p for p in _headless_modules() if p.stem not in NAMES_BACKENDS_AS_DATA]


@pytest.mark.parametrize("path", _vocabulary_modules(), ids=lambda p: p.stem)
def test_headless_module_speaks_no_backend_vocabulary(path: Path):
    hits = [(ln, tok) for ln, tok in _code_tokens(path)
            for word in BACKEND_TOKENS if word.lower() in tok.lower()]
    assert not hits, (f"{path.name} carries backend vocabulary in code: {hits[:5]}. "
                      "CameraPlan may state intent; a cvar, a capture cfg, an AVI or "
                      "a process is a backend's business (HL-1).")


@pytest.mark.parametrize(
    "path", sorted(PANTHEON / f"{m}.py" for m in NAMES_BACKENDS_AS_DATA
                   if (PANTHEON / f"{m}.py").exists()),
    ids=lambda p: p.stem)
def test_a_module_that_names_a_backend_still_never_reaches_one(path: Path):
    """Naming is allowed here; importing and launching are not."""
    hit = sorted(i for i in _imports(path)
                 if i in FORBIDDEN_IMPORTS
                 or i.startswith("creative_suite.engine.wolfcam_capture"))
    assert not hit, f"{path.name} imports a backend: {hit}"
    src = path.read_text(encoding="utf-8")
    for word in ("Popen", "CreateProcess", "os.system", "capture_demo("):
        assert word not in src, f"{path.name} can start a process ({word})"
