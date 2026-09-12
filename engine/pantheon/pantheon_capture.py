"""PANTHEON_NATIVE capture backend.

Renders production demo clips with pantheon_cgame.exe: our own binary, the
WolfcamQL 11.3 renderer and cgame linked statically, drawing into its own
framebuffer object. Matches creative_suite.engine.wolfcam_capture.capture_demo's
return contract so callers cannot tell the two backends apart (gate G4).
"""
from __future__ import annotations

from pathlib import Path

from engine.pantheon import store as S


def host_exe() -> Path:
    """The one PANTHEON binary, from the code root (HL-9): a worktree runs its
    own build, never the main checkout's."""
    return S.CODE_ROOT / "engine" / "pantheon_renderer" / "build" / "pantheon_cgame.exe"
