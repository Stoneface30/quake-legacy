"""Frozen master film capture profile for pTn.Tr4sH V2 masters.

One deliberate moviemaking profile (wolfcam_tr4sh_master_capture.cfg) +
machine-readable master_capture_profile.json. Every generated master AVI
records capture_profile_id = sha256(cfg)[:12] so per-session drift is
impossible. Values are evidence-based (see output/demo_v2/_bench).

LATCH cvars (renderer restart required) must be +set on the command line —
they are exposed as LAUNCH_SETS. Everything else lives in the cfg.

MME capability audit (source: wolfcam-knowledge 01/04 docs, this build):
  motion blur          SUPPORTED (mme_blurFrames, cl_aviFrameRateDivider) — OFF for masters
  depth of field       SUPPORTED (mme_dofFrames/Radius, q3mme dof cmds)   — OFF for masters
  camera paths         SUPPORTED (q3mme camera, freecam)                  — later cinematic pass
  timescale capture    SUPPORTED (AVI clock is timescale-aware)
  supersampling        SUPPORTED_DIFFERENT_NAME (r_useFbo + r_fboAntiAlias MSAA)
  HQ frame output      SUPPORTED (video tga/png sequences)
  depth/mask passes    SUPPORTED (mme_saveDepth)
  freecam / FOV        SUPPORTED (freecam, cg_fov)
  velocity effects     NOT_NEEDED_FOR_GAMEPLAY_MASTER
Masters stay clean: faithful action, no baked-in blur/DoF; cinematic effects
belong to later alternate passes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PROFILE_NAME = "tr4sh_master_v1"
WOLFCAM_VERSION = "wolfcamql-11.3"

# ── frozen values (benchmark-decided 2026-08-30) ────────────────────────────
RESOLUTION = (1920, 1080)
FPS = 60
CODEC = "mjpeg"
JPEG_QUALITY = 90

# LATCH cvars → command line +set (renderer reads them once at startup).
LAUNCH_SETS = {
    "r_picmip": 0,                 # full-resolution textures (gl1 default 0)
    "r_texturebits": 32,
    "r_colorbits": 32,
    "r_ext_max_anisotropy": 16,    # default 2 is visibly soft at grazing angles
    "r_ext_compressed_textures": 0,
    "r_detailtextures": 1,
    "r_useFbo": 1,                 # capture from offscreen FBO
    "r_fboAntiAlias": 4,           # MSAA in the FBO (closest to supersampling)
    "sv_pure": 0,                  # required for zzz_* override paks (ENG-3)
}

# Session cvars → wolfcam_tr4sh_master_capture.cfg
CFG_SETS = {
    # capture
    "cl_aviFrameRate": FPS,
    "cl_aviCodec": CODEC,
    "r_jpegCompressionQuality": JPEG_QUALITY,
    "cl_aviAllowLargeFiles": 1,
    # geometry / model detail
    "r_lodbias": -2,
    "r_lodCurveError": 10000,      # no curve LOD pop on high-poly geometry
    "r_subdivisions": 1,           # max curve tessellation
    "r_vertexLight": 0,            # lightmaps, never vertex light
    "r_dynamiclight": 1,
    # texture filtering
    "r_textureMode": "GL_LINEAR_MIPMAP_LINEAR",
    # effects fidelity
    "cg_shadows": 1,
    "cg_marks": 1,
    "cg_smokeRadius_RL": 8,        # keep stock projectile visibility
    # clean frame contract: no wolfcam overlays; HUD stays (killfeed = context)
    "cg_drawFPS": 0,
    "cg_drawSpeed": 0,
    "cg_drawItemPickups": 0,
    "cl_noprint": 1,
    # audio
    "s_volume": 1.0,
}

# Human-readable reason per important setting (§5 of the mandate).
REASONS = {
    "r_picmip": "0 = no texture downsampling; UHD packs pointless otherwise",
    "r_ext_max_anisotropy": "16x aniso: floor/wall detail at grazing angles",
    "r_useFbo": "offscreen render target: overlay-free frames, res decoupled "
                "from window",
    "r_fboAntiAlias": "4x MSAA — only supersampling-like option this build has",
    "r_lodbias": "-2 highest model detail at all distances",
    "r_subdivisions": "1 = max curve tessellation (jumppads, arches)",
    "r_lodCurveError": "10000 disables curve LOD switching mid-shot",
    "r_vertexLight": "lightmapped lighting is the authentic QL look",
    "cl_aviCodec": "mjpeg: intra-only, edit-friendly, matches historical "
                   "sources; huffyuv lossless rejected on size (see bench)",
    "r_jpegCompressionQuality": "q90: no visible artefacts on LG beam/rail "
                                "gradients in bench frames; masters deserve it",
    "cg_drawFPS": "wolfcam's own fps/ups overlays contaminated canary frames",
    "sv_pure": "0 required so zzz_uhd_* override paks load (ENG-3)",
}


def cfg_text() -> str:
    lines = [f"// {PROFILE_NAME} - frozen master capture profile",
             f"// wolfcam: {WOLFCAM_VERSION}  resolution: "
             f"{RESOLUTION[0]}x{RESOLUTION[1]}@{FPS}"]
    for k, v in CFG_SETS.items():
        lines.append(f"seta {k} {v}" if not isinstance(v, str)
                     else f'seta {k} "{v}"')
    return "\n".join(lines) + "\n"


def profile_id() -> str:
    payload = cfg_text() + json.dumps(LAUNCH_SETS, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def write(staging_gamedir: Path) -> str:
    """Write the cfg into the staging game dir + the JSON record; returns
    capture_profile_id."""
    (staging_gamedir / "wolfcam_tr4sh_master_capture.cfg").write_text(
        cfg_text(), encoding="ascii")
    pid = profile_id()
    record = {
        "profile_name": PROFILE_NAME,
        "capture_profile_id": pid,
        "wolfcam_version": WOLFCAM_VERSION,
        "resolution": f"{RESOLUTION[0]}x{RESOLUTION[1]}",
        "fps": FPS,
        "codec": CODEC,
        "jpeg_quality": JPEG_QUALITY,
        "launch_sets": LAUNCH_SETS,
        "cfg_sets": CFG_SETS,
        "reasons": REASONS,
        "cfg_sha256_12": pid,
    }
    out = REPO_ROOT / "output" / "demo_v2" / "master_capture_profile.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=1), encoding="utf-8")
    return pid
