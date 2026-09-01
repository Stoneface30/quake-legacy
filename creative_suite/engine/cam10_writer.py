"""Deterministic `.cam10` compiler — the ONLY correct way to give wolfcamql
a camera path. See docs/reference/cam10_runtime_contract.md for the full
source-verified grammar and playback semantics; this module is a direct,
line-for-line implementation of it.

Do not hand-edit the line order in ``_write_point`` — the reader
(``CG_LoadCamera_f``, cg_consolecmds.c:2401) parses every field by LINE
POSITION, not by the trailing comment text. A reordered or dropped line
desyncs every field after it, silently.

SceneRecipeV2 boundary (per the 2026-09-01 camera-pipeline-recovery
directive): a shot's KEYFRAMES/TIMING are editorial intent, tracked by
``shot_plan.py`` and hashed into ``plan_id``. This module's output (the
``.cam10`` file + its hash) is a compiled EXECUTION ARTIFACT, tracked
separately in ``camera_compilations`` — compiling, or recompiling under a
newer ``CAMERA_COMPILER_VERSION``, never changes a plan's identity.
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

CAM_VERSION = 10  # WOLFCAM_CAMERA_VERSION, cg_camera.h:7
CAMERA_COMPILER_VERSION = "cam10-v1"
CAMERA_RUNTIME_BACKEND = "wolfcamql-cam10"

# type (cg_camera.h:61-69) — CAMERA_INTERP: plain linear interpolation
# directly between two points' raw origins (cg_view.c:3137-3178), visits
# every keyframe exactly at its cgtime. The CAMERA_SPLINE* variants are
# deliberately not used — posBezier is a non-interpolating B-spline
# approximation (see cam10_runtime_contract.md).
CAMERA_INTERP = 1
# viewType (cg_camera.h:71-82) — same linear-between-keyframes behavior
# for angles (cg_view.c:3453).
CAMERA_ANGLES_INTERP = 0
# rollType (cg_camera.h:84-90) — roll taken directly from angles[2], no
# cross-point matching.
CAMERA_ROLL_AS_ANGLES = 3
# fovType (cg_camera.h:92-99) — linear-between-keyframes FOV (cg_view.c:4004).
CAMERA_FOV_INTERP = 1
# flags (cg_camera.h:13-16) — every point is its own anchor for all three
# data channels; none of the forward/backward gap-filling logic ever fires.
CAM_ORIGIN, CAM_ANGLES, CAM_FOV, CAM_TIME = 0x001, 0x002, 0x004, 0x100
ALL_FLAGS = CAM_ORIGIN | CAM_ANGLES | CAM_FOV | CAM_TIME


def _f3(v) -> str:
    return "{:.6f} {:.6f} {:.6f}".format(*v)


def _write_point(origin, angles, cgtime_ms: float, fov: float) -> str:
    """One camera point, exact line order per CG_SaveCamera_f
    (cg_consolecmds.c:2226-2331). commandStrLen is always 0 — we never
    attach a per-point console command."""
    lines = [
        "0  camera point number",
        f"{_f3(origin)}  origin",
        f"{_f3(angles)}  angles",
        f"{CAMERA_INTERP}  type",
        f"{CAMERA_ANGLES_INTERP}  viewType",
        f"{CAMERA_ROLL_AS_ANGLES}  rollType",
        f"{ALL_FLAGS}  flags",
        f"{float(cgtime_ms):.4f}  cgtime",
        "0  splineType",
        "0  numSplines",
        f"{_f3((0.0, 0.0, 0.0))}  viewPointOrigin",
        "0  viewPointOriginSet",
        "-1  viewEnt",
        f"{_f3((0.0, 0.0, 0.0))}  viewEntStartingOrigin",
        "0  viewEntStartingOriginSet",
        "0  offsetType",
        "0.000000  xoffset",
        "0.000000  yoffset",
        "0.000000  zoffset",
        f"{float(fov):.4f}  fov",
        f"{CAMERA_FOV_INTERP}  fovType",
        "0  useOriginVelocity",
        "0.000000  originInitialVelocity",
        "0.000000  originFinalVelocity",
        "0  useAnglesVelocity",
        "0.000000  anglesInitialVelocity",
        "0.000000  anglesFinalVelocity",
        "0  useXoffsetVelocity",
        "0.000000  xoffsetInitialVelocity",
        "0.000000  xoffsetFinalVelocity",
        "0  useYoffsetVelocity",
        "0.000000  yoffsetInitialVelocity",
        "0.000000  yoffsetFinalVelocity",
        "0  useZoffsetVelocity",
        "0.000000  zoffsetInitialVelocity",
        "0.000000  zoffsetFinalVelocity",
        "0  useFovVelocity",
        "0.000000  fovInitialVelocity",
        "0.000000  fovFinalVelocity",
        "0  useRollVelocity",
        "0.000000  rollInitialVelocity",
        "0.000000  rollFinalVelocity",
        "0  commandStrLen",
    ]
    return "\n".join(lines) + "\n\n-------------------------------------\n"


def write_cam10(keyframes: list[dict], base_servertime: int) -> str:
    """Compile keyframes (camera_paths._kf shape: t_ms/pos/angles/fov,
    t_ms shot-relative) into the exact byte contract CG_LoadCamera_f
    expects. Deterministic: same input always produces the same bytes.

    Requires >= 2 keyframes — CG_LoadCamera_f / CG_PlayCamera_f both
    refuse to play a path with fewer than 2 points (cg_consolecmds.c:2192,
    2241).
    """
    if len(keyframes) < 2:
        raise ValueError(
            f"a .cam10 path needs >= 2 keyframes, got {len(keyframes)}")
    base = int(base_servertime)
    # Each _write_point() block already ends in its own trailing newline
    # (matching CG_SaveCamera_f's unconditional per-point trailer) — points
    # must be concatenated directly, NOT joined with an extra "\n", or the
    # line-positional reader (CG_LoadCamera_f) desyncs by one line on every
    # point after the first.
    out = f"WolfcamCamera {CAM_VERSION}\n"
    for kf in sorted(keyframes, key=lambda k: k["t_ms"]):
        cgtime = base + float(kf["t_ms"])
        out += _write_point(kf["pos"], kf["angles"], cgtime, kf["fov"])
    return out


def cam10_hash(content: str) -> str:
    return hashlib.sha256(content.encode("ascii")).hexdigest()


def compile_camera(keyframes: list[dict], base_servertime: int,
                   gamedir: Path, camera_name: str) -> dict:
    """Write <gamedir>/cameras/<camera_name>.cam10 and return its hash +
    the exact cfg lines needed to load and play it. Overwrites any
    existing file of the same name (compilation is deterministic, so an
    identical input reproduces identical bytes)."""
    content = write_cam10(keyframes, base_servertime)
    cameras_dir = Path(gamedir) / "cameras"
    cameras_dir.mkdir(parents=True, exist_ok=True)
    path = cameras_dir / f"{camera_name}.cam{CAM_VERSION}"
    path.write_text(content, encoding="ascii")
    return {
        "path": path,
        "file_hash": cam10_hash(content),
        "compiler_version": CAMERA_COMPILER_VERSION,
        "runtime_backend": CAMERA_RUNTIME_BACKEND,
        "cfg_lines": [
            "freecam",
            f"loadcamera {camera_name}",
            "playcamera",
        ],
    }


# ---------------------------------------------------------------------------
# Compilation ledger — separate from shot_plans (cinematic.db), so a
# recompile never mutates a SceneRecipe's identity hash.
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS camera_compilations (
    plan_id          TEXT NOT NULL,
    compiler_version TEXT NOT NULL,
    file_hash        TEXT NOT NULL,
    runtime_backend  TEXT NOT NULL,
    compiled_utc     TEXT NOT NULL,
    PRIMARY KEY (plan_id, compiler_version)
)
"""


def _connect(db_path) -> sqlite3.Connection:
    from creative_suite.engine.shot_plan import DEFAULT_DB
    path = Path(db_path) if db_path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute(_SCHEMA)
    return con


def record_compilation(plan_id: str, file_hash: str, db_path=None,
                       compiler_version: str = CAMERA_COMPILER_VERSION,
                       runtime_backend: str = CAMERA_RUNTIME_BACKEND) -> None:
    con = _connect(db_path)
    try:
        con.execute(
            "INSERT OR REPLACE INTO camera_compilations "
            "(plan_id, compiler_version, file_hash, runtime_backend, "
            " compiled_utc) VALUES (?,?,?,?,?)",
            (plan_id, compiler_version, file_hash, runtime_backend,
             datetime.now(timezone.utc).isoformat(timespec="seconds")))
        con.commit()
    finally:
        con.close()


def get_compilation(plan_id: str, db_path=None,
                    compiler_version: str = CAMERA_COMPILER_VERSION
                    ) -> dict | None:
    con = _connect(db_path)
    try:
        row = con.execute(
            "SELECT file_hash, runtime_backend, compiled_utc "
            "FROM camera_compilations WHERE plan_id=? AND compiler_version=?",
            (plan_id, compiler_version)).fetchone()
    finally:
        con.close()
    if not row:
        return None
    return {"plan_id": plan_id, "compiler_version": compiler_version,
            "file_hash": row[0], "runtime_backend": row[1],
            "compiled_utc": row[2]}
