"""PANTHEON runtime baseline — explicit cvar reset + reproducibility manifest.

Directive §18-19. Two of the six free-win proofs (see
docs/reference/free_wins_proof.md) were silently contaminated by
`CVAR_ARCHIVE` state that wolfcam had persisted into `q3config.cfg` from
a PREVIOUS capture session: `cg_fxfile` leaked from the ghost-trail proof
into the colour-grade proof's baseline, and `mme_saveDepth` would have
added a depth stream to every later capture. Neither produced an error, a
warning, or a non-zero exit code. Both were caught only by looking at
frames.

That failure mode is unacceptable for a reproducibility-driven pipeline,
so every diagnostic / preview / master capture now begins by explicitly
writing a known value for each cinematic cvar we depend on, rather than
inheriting whatever the last run happened to save.

The baseline is deliberately EXPLICIT rather than clever: a flat
name→value mapping that is written verbatim into the capture cfg. Adding
a cvar to any capture path means adding it here too — a cvar that is set
by some capture but absent from the baseline is exactly the leak this
module exists to prevent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

BASELINE_VERSION = "pantheon-baseline-v1"

# Every cvar any PANTHEON capture path is known to touch, with the value
# that means "off / neutral". Grouped by the feature that introduced it so
# a future reader can tell why each entry exists.
RUNTIME_BASELINE: dict[str, str] = {
    # --- time control (timewarp_measurement.md) ---
    "timescale": "1.0",
    "cl_freezeDemo": "0",
    # --- FX DSL (free_wins_proof.md proof 1-2) ---
    # cg_fxfile is THE cvar that leaked between proofs. An empty value
    # means "no custom fx script", which is the neutral state.
    "cg_fxfile": "",
    # --- depth / aux passes (proof 6) ---
    # mme_saveDepth silently adds a second output stream to EVERY capture
    # once set; it must be explicitly cleared, not assumed off.
    "mme_saveDepth": "0",
    "mme_saveStencil": "0",
    "mme_blurFrames": "0",
    "mme_dofFrames": "0",
    # --- camera (cam10_runtime_contract.md) ---
    # cg_cameraQue/RewindTime alter playcamera's internal seek behaviour;
    # both are CVAR_ARCHIVE and both were implicated during the camera
    # investigation before the real (CRLF) cause was found.
    "cg_cameraQue": "1",
    "cg_cameraRewindTime": "0",
    "cg_enableAtCommands": "1",   # the whole `at` scheduler depends on it
    "debug_camera": "0",
    # --- capture output ---
    "cl_aviFrameRate": "60",
    "cl_aviCodec": "mjpeg",
    "r_jpegCompressionQuality": "90",
    # --- console hygiene (must never appear in a master frame) ---
    "con_notifytime": "0",
    "cl_noprint": "1",
    "logfile": "0",
}

# Cvars a caller is ALLOWED to override per-capture (everything else in
# the baseline is considered structural). Kept explicit so an override
# typo fails loudly instead of silently doing nothing.
OVERRIDABLE = frozenset({
    "timescale", "cg_fxfile", "mme_saveDepth", "mme_blurFrames",
    "mme_dofFrames", "cl_aviFrameRate", "r_jpegCompressionQuality",
    "debug_camera", "logfile", "cl_freezeDemo",
})


class UnknownCvarError(ValueError):
    """Raised when a caller overrides a cvar the baseline does not know.

    This is intentionally strict: an unknown cvar is either a typo, or a
    new capture feature whose neutral value has not been added to
    RUNTIME_BASELINE — and the latter is precisely how the leak happened.
    """


def baseline_lines(overrides: dict[str, str] | None = None) -> list[str]:
    """The cfg lines that reset the runtime to a known state.

    Emitted FIRST in every capture cfg, before any capture-specific
    command, so nothing inherited from `q3config.cfg` survives.
    """
    overrides = overrides or {}
    for name in overrides:
        if name not in RUNTIME_BASELINE:
            raise UnknownCvarError(
                f"{name!r} is not in RUNTIME_BASELINE — add it there (with its "
                "neutral value) before overriding it, otherwise it can leak "
                "into later captures via q3config.cfg")
        if name not in OVERRIDABLE:
            raise UnknownCvarError(
                f"{name!r} is a structural baseline cvar and is not overridable")
    merged = dict(RUNTIME_BASELINE)
    merged.update(overrides)
    lines = [f"// {BASELINE_VERSION} — explicit reset, do not rely on q3config"]
    for name in sorted(merged):
        value = merged[name]
        lines.append(f'seta {name} "{value}"' if value == "" else
                     f"seta {name} {value}")
    return lines


def baseline_hash(overrides: dict[str, str] | None = None) -> str:
    """Deterministic hash of the effective baseline, for the manifest."""
    payload = json.dumps(
        {"version": BASELINE_VERSION,
         "cvars": {**RUNTIME_BASELINE, **(overrides or {})}},
        sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def runtime_manifest(*, exe_path: Path | None = None,
                     cfg_text: str | None = None,
                     asset_pack_paths: list[Path] | None = None,
                     camera_artifact_hash: str | None = None,
                     fx_script_paths: list[Path] | None = None,
                     grade_pack_path: Path | None = None,
                     overrides: dict[str, str] | None = None) -> dict:
    """Everything needed to reproduce one capture's visual output (§19).

    Missing inputs are recorded as None rather than omitted, so a manifest
    always has the same shape and a reader can tell "not applicable" from
    "forgot to record it".
    """
    return {
        "baseline_version": BASELINE_VERSION,
        "cvar_baseline_hash": baseline_hash(overrides),
        "cvar_overrides": dict(overrides or {}),
        "runtime_exe_sha256": _file_sha256(exe_path) if exe_path else None,
        "cfg_sha256": (hashlib.sha256(cfg_text.encode("utf-8")).hexdigest()
                       if cfg_text is not None else None),
        "camera_artifact_hash": camera_artifact_hash,
        "asset_packs": sorted(
            {p.name: _file_sha256(p) for p in (asset_pack_paths or [])}.items()
        ),
        "fx_scripts": sorted(
            {p.name: _file_sha256(p) for p in (fx_script_paths or [])}.items()
        ),
        "grade_pack": ({grade_pack_path.name: _file_sha256(grade_pack_path)}
                       if grade_pack_path else None),
    }
