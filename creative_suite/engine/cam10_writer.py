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

# MAX_CAMERAPOINTS (cg_camera.h:8) — loadcamera reads a whole file into
# this array in one shot. Far larger than FREECAM_SAMPLED's ceiling
# (MAX_AT_COMMANDS=128, camera_compiler_v2.py) since native playback
# doesn't consume the shared "at" command queue at all.
MAX_CAMERAPOINTS = 512
# The usable ceiling is three lower. CG_UpdateCameraInfoExt
# (cg_consolecmds.c:2855) walks `i < cg.numCameraPoints + 3` -- three scratch
# points past the loaded ones -- and the interactive add-point path guards at
# `numCameraPoints >= MAX_CAMERAPOINTS - 3` for exactly that reason. The
# loader itself has no cap, so a file with 512 points loads fine and then
# overflows cameraPoints[] by three on the first update. That overflow
# worked by luck on 2026-09-01 (the verified proof used an 8-point file)
# and crashed the engine with rc=1 on 2026-09-03 with a 512-point one.
CAM10_USABLE_POINTS = MAX_CAMERAPOINTS - 3

BACKEND_NATIVE_CAM10 = "NATIVE_CAM10"

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


# Per-point options the format carries at version 10 and the writer used to
# hardcode. Named here so a caller can reach them without touching the line
# order, which is positional and unforgiving.
CAMERA_ANGLES_ENT = 4          # cg_camera.h:76 -- aim at viewEnt
CAMERA_OFFSET_INTERP = 0       # cg_camera.h:102
# NOT available at version 10: timescale/timescaleInterp are read only under
# `version < 10`, so the path cannot carry its own speed ramp.


def _write_point(origin, angles, cgtime_ms: float, fov: float, *,
                 view_type: int = CAMERA_ANGLES_INTERP,
                 view_ent: int = -1,
                 offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
                 offset_type: int = CAMERA_OFFSET_INTERP,
                 origin_velocity: tuple[float, float] | None = None,
                 angles_velocity: tuple[float, float] | None = None,
                 command: str = "") -> str:
    """One camera point, exact line order per CG_SaveCamera_f
    (cg_consolecmds.c:2226-2331).

    The keyword options are fields the format has always carried and this
    writer used to pin at defaults:

    ``view_ent`` with ``view_type=CAMERA_ANGLES_ENT`` makes the ENGINE aim
    at an entity every frame, so a follow needs no authored angles at all.
    ``offset`` moves the camera relative to what it is tracking, which is a
    follow without an absolute path to collide with. The velocity pairs are
    (initial, final) ease for that channel. ``command`` is a console command
    fired when the point is reached -- a trigger port, not yet a proven sync
    port, because the gap between execution and the delivered frame is
    unmeasured.
    """
    ov = origin_velocity or (0.0, 0.0)
    av = angles_velocity or (0.0, 0.0)
    cmd = command or ""
    lines = [
        "0  camera point number",
        f"{_f3(origin)}  origin",
        f"{_f3(angles)}  angles",
        f"{CAMERA_INTERP}  type",
        f"{int(view_type)}  viewType",
        f"{CAMERA_ROLL_AS_ANGLES}  rollType",
        f"{ALL_FLAGS}  flags",
        f"{float(cgtime_ms):.4f}  cgtime",
        "0  splineType",
        "0  numSplines",
        f"{_f3((0.0, 0.0, 0.0))}  viewPointOrigin",
        "0  viewPointOriginSet",
        f"{int(view_ent)}  viewEnt",
        f"{_f3((0.0, 0.0, 0.0))}  viewEntStartingOrigin",
        "0  viewEntStartingOriginSet",
        f"{int(offset_type)}  offsetType",
        f"{float(offset[0]):.6f}  xoffset",
        f"{float(offset[1]):.6f}  yoffset",
        f"{float(offset[2]):.6f}  zoffset",
        f"{float(fov):.4f}  fov",
        f"{CAMERA_FOV_INTERP}  fovType",
        f"{1 if origin_velocity else 0}  useOriginVelocity",
        f"{float(ov[0]):.6f}  originInitialVelocity",
        f"{float(ov[1]):.6f}  originFinalVelocity",
        f"{1 if angles_velocity else 0}  useAnglesVelocity",
        f"{float(av[0]):.6f}  anglesInitialVelocity",
        f"{float(av[1]):.6f}  anglesFinalVelocity",
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
        f"{len(cmd)}  commandStrLen",
    ]
    # The trailer differs when a command is present, and the difference is
    # exact. CG_LoadCamera_f (cg_consolecmds.c:2573) does NOT read the
    # command as a line: it reads `slen` RAW BYTES with trap_FS_Read, then
    # consumes one line for the newline that follows and one for the
    # separator. So a command is followed by a single newline. With no
    # command nothing is consumed by the read, and the blank line takes the
    # place of the command's own terminator.
    #
    # Emitting the command as an ordinary line, with the usual blank after
    # it, leaves one newline too many: the separator is then read as the
    # next point's "camera point number" and every point after it desyncs.
    # This is the same class of positional bug as the CRLF one.
    sep = "-------------------------------------\n"
    if cmd:
        return "\n".join(lines) + f"\n{cmd}\n" + sep
    return "\n".join(lines) + "\n\n" + sep


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
        # Optional per-point fields ride on the keyframe dict, so a caller
        # that knows nothing about them is byte-identical to before.
        out += _write_point(
            kf["pos"], kf["angles"], cgtime, kf["fov"],
            view_type=kf.get("view_type", CAMERA_ANGLES_INTERP),
            view_ent=kf.get("view_ent", -1),
            offset=kf.get("offset", (0.0, 0.0, 0.0)),
            offset_type=kf.get("offset_type", CAMERA_OFFSET_INTERP),
            origin_velocity=kf.get("origin_velocity"),
            angles_velocity=kf.get("angles_velocity"),
            command=kf.get("command", ""))
    return out


def cam10_hash(content: str) -> str:
    return hashlib.sha256(content.encode("ascii")).hexdigest()


def compile_camera(keyframes: list[dict], base_servertime: int,
                   gamedir: Path, camera_name: str,
                   backend: str = "FREECAM_SAMPLED") -> dict:
    """Write <gamedir>/cameras/<camera_name>.cam10 (the archival, portable
    representation of this path — correct and unit-tested, see
    test_cam10_writer.py) and return its hash + the cfg lines that
    actually EXECUTE the path at capture time, for whichever ``backend``
    is requested: ``"FREECAM_SAMPLED"`` (default) or ``"NATIVE_CAM10"``.

    CORRECTED DIAGNOSIS (2026-09-01, superseding the original "known
    engine bug" write-up in cam10_runtime_contract.md — read that file's
    "Corrected 2026-09-01" section for the full story): the original
    ``loadcamera``/``playcamera`` failures were NOT an engine defect.
    ``Path.write_text()``'s default universal-newline translation turned
    every ``\\n`` into ``\\r\\n`` on Windows, corrupting the byte-exact,
    line-positional grammar ``CG_LoadCamera_f`` expects. Every ``.cam10``
    this module wrote before the ``newline=""`` fix below was silently
    malformed. Once written correctly, ``loadcamera``+``playcamera``
    RUNTIME-PROVEN 2026-09-01 on the STOCK, UNMODIFIED wolfcamql 11.3
    binary: zero ``couldn't get nextsnap`` occurrences, a captured frame
    showed wolfcam's own ``debug_camera`` overlay confirming every loaded
    field (origin/angles/fov/flags/interp-type) matched the compiled file
    exactly, and a second frame showed a completely different, correctly
    rotated view consistent with the orbit. NATIVE_CAM10 also has a much
    higher capacity than FREECAM_SAMPLED — ``loadcamera`` reads up to
    ``MAX_CAMERAPOINTS`` (512) points from one file in a single command,
    entirely bypassing the ``MAX_AT_COMMANDS`` (128) ceiling that forces
    FREECAM_SAMPLED to clamp density (camera_compiler_v2.py).

    FREECAM_SAMPLED stays the default per the project directive ("do not
    revert the working freecamsetpos backend... it is valuable even after
    native playcamera is repaired... an independent fallback when engine
    camera code misbehaves") — both backends are real, tested, and
    intentionally kept side by side; SceneRecipe camera intent does not
    care which one renders it.
    """
    content = write_cam10(keyframes, base_servertime)
    cameras_dir = Path(gamedir) / "cameras"
    cameras_dir.mkdir(parents=True, exist_ok=True)
    path = cameras_dir / f"{camera_name}.cam{CAM_VERSION}"
    # newline="" is load-bearing: Path.write_text()'s default universal-
    # newline translation turns every \n into \r\n on Windows, corrupting
    # the byte-exact, line-positional grammar CG_LoadCamera_f expects.
    path.write_text(content, encoding="ascii", newline="")
    if backend == BACKEND_NATIVE_CAM10:
        cfg_lines = native_cam10_cfg_lines(camera_name)
    else:
        cfg_lines = to_freecamsetpos_lines(keyframes, base_servertime)
    return {
        "path": path,
        "file_hash": cam10_hash(content),
        "compiler_version": CAMERA_COMPILER_VERSION,
        "runtime_backend": backend,
        "cfg_lines": cfg_lines,
    }


def native_cam10_cfg_lines(camera_name: str) -> list[str]:
    """The NATIVE_CAM10 execution sequence — runtime-proven 2026-09-01 on
    the stock 11.3 binary once the file is written with pure LF (see
    compile_camera's docstring). ``freecam`` is required for the same
    reason FREECAM_SAMPLED needs it: cg_view.c:3092-3094 gates the whole
    camera-path-sampling block on cg.freecam being active."""
    return ["freecam", f"loadcamera {camera_name}", "playcamera"]


def to_freecamsetpos_lines(keyframes: list[dict], base_servertime: int
                           ) -> list[str]:
    """The FREECAM_SAMPLED execution primitive: one ``at <t> freecamsetpos
    x y z pitch yaw roll`` per keyframe (plus an initial ``freecam``).
    Runtime-proven, and retained as an independent fallback backend --
    NOT because playcamera is broken (that reading was our own CRLF bug;
    see compile_camera's CORRECTED DIAGNOSIS). Sorted by time;
    duplicate/out-of-order input is normalized the same way write_cam10
    is, so both artifacts always agree on ordering."""
    base = int(base_servertime)
    lines = ["freecam"]
    for kf in sorted(keyframes, key=lambda k: k["t_ms"]):
        t = base + int(kf["t_ms"])
        p, a = kf["pos"], kf["angles"]
        lines.append(
            "at {} freecamsetpos {:.2f} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f}"
            .format(t, p[0], p[1], p[2], a[0], a[1], a[2]))
    return lines


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
