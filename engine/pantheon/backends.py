"""Render backends — the ONLY door through which PANTHEON reaches a renderer.

PANTHEON is the engine. It parses .dm_73, builds canonical game state,
PerformanceTrace, FrameTruth, Scene/TimeMap/RoundScenario, a ChoreographyPlan
and finally a ShotSpec, and every one of those steps runs without launching a
game. A backend receives a finished ShotSpec (and, for validation, a finished
.dm_73) and hands back pixels or a verdict. It decides NOTHING about where a
player was, when a rocket fired, or what the camera intends.

WHY A CLOSED LIST OF USES. Every Wolfcam launch costs minutes and has, in
past sessions, leaked state back into the next one (latched cvars, archived
q3config, renderer profiles moving cached IDs). A launch must therefore name
its purpose, and there are exactly four legitimate ones. A caller that cannot
pick one of them has no business launching the client.

    REFERENCE_RENDER          film a ShotSpec as the Quake-faithful reference
    EXTERNAL_DM73_VALIDATION  prove a synthetic demo plays in a real client
    RUNTIME_CAPABILITY_PROOF  ask the running binary what it can actually do
    FINAL_QUAKE_BEAUTY        the delivered beauty pass for the film

Wolfcam may NOT participate in PerformanceTrace extraction, action
compilation, semantic validation, movement retargeting, aim reproduction,
projectile reproduction or FrameTruth generation. The import graph enforces
that in creative_suite/tests/test_pantheon_headless_boundary.py.

ADDING A BACKEND. Implement `RenderBackend`, register it in `BACKENDS`. The
Blender backend (object IDs, Cryptomatte, depth, normals, arbitrary cameras)
and an offscreen Quake renderer are the two planned entries; Wolfcam stays as
the visual oracle they are compared against.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from engine.pantheon.shot import ShotSpec


class BackendUse(Enum):
    REFERENCE_RENDER = "reference_render"
    EXTERNAL_DM73_VALIDATION = "external_dm73_validation"
    RUNTIME_CAPABILITY_PROOF = "runtime_capability_proof"
    FINAL_QUAKE_BEAUTY = "final_quake_beauty"


class RenderBackend(Protocol):
    name: str
    supports: frozenset[BackendUse]

    def render(self, shot: "ShotSpec", out_dir: Path, *, base_ms: int) -> Path:
        """Produce media for one ShotSpec. Never mutates the spec."""
        ...


def _wolfcam_render(spec: "ShotSpec", out_dir: Path, *, base_ms: int = 1000) -> Path:
    # Imported lazily so that importing this module does not import the
    # capture path; the headless layers may import `backends` for the enum.
    from engine.pantheon.shot import render
    return render(spec, out_dir, base_ms=base_ms)


class WolfcamReference:
    """WolfcamQL 11.3 as a Quake rasterizer. Nothing more."""
    name = "WOLFCAM_REFERENCE"
    supports = frozenset({
        BackendUse.REFERENCE_RENDER,
        BackendUse.EXTERNAL_DM73_VALIDATION,
        BackendUse.RUNTIME_CAPABILITY_PROOF,
        BackendUse.FINAL_QUAKE_BEAUTY,
    })

    def render(self, shot: "ShotSpec", out_dir: Path, *, base_ms: int = 1000) -> Path:
        return _wolfcam_render(shot, out_dir, base_ms=base_ms)


BACKENDS: dict[str, RenderBackend] = {
    WolfcamReference.name: WolfcamReference(),
}


def render(backend: str, *, shot: "ShotSpec", out_dir: Path, use: BackendUse,
           base_ms: int = 1000) -> Path:
    """Dispatch one ShotSpec to a named backend for a declared purpose.

    Raises KeyError for an unknown backend and ValueError when the backend
    does not support the declared use. `use` is keyword-only and has no
    default on purpose.
    """
    be = BACKENDS[backend]
    if use not in be.supports:
        raise ValueError(f"{backend} does not support {use.name}")
    return be.render(shot, out_dir, base_ms=base_ms)
