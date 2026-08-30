"""Frozen capture/analysis profiles for pTn.Tr4sH V2 masters.

Four deliberate profiles (definitive-master mandate B1-B4), one cfg each,
written into the staging game dir. Every generated AVI records
capture_profile_id = sha256(cfg + launch sets)[:12] — no session drift.

Evidence base (output/demo_v2/_bench + docs/reference/moviemaking-feature-
matrix.md, 2026-08-30):
  codec  : MJPEG q90 (q80 smears floor speckle; huffyuv 196MB/s and raw
           376MB/s rejected on size; ffmpeg FFV1 pipe is documented working
           in source but the bench attempt silently fell back to the AVI
           writer — deferred, not used for masters)
  AA     : r_useFbo + 4x MSAA; ALSO structurally removes external overlay
           contamination (NVIDIA toast present in window-framebuffer capture,
           absent in FBO capture of the same scene)
  FOV    : 90/105/115/122 benchmarked on the same fight; 115 frozen — best
           speed/context gain with targets still clearly readable.
           cg_useDemoFov is a protocol>=91 no-op on our .dm_73 corpus.
  clean  : cg_drawGun 0 preserves the LG beam explicitly
           (cg_weapons.c:2800-2811); killfeed/frag-message have TIME gates
           (cg_obituaryTime / cg_drawFragMessageTime), not booleans; follow
           text needs cg_drawFollowing AND wolfcam_drawFollowing.
  memory : LAA flag on staged exe + com_zoneMegs 96 / com_hunkMegs 256
           (UHD set Z_Malloc crash at defaults; VM_Create fail at hunk 512
           without LAA)
  renderer: gl1 (cl_renderer default) — mature FBO+mme path, faithful QL look.

MME capability audit: motion blur SUPPORTED (mme_blurFrames accumulation;
cl_aviFrameRateDivider is DECIMATION, leave 1); DoF SUPPORTED (mme_dof* +
keyframed dof cmd); q3mme camera paths SUPPORTED (catmullrom/bezier smoothing,
quaternion angles, CAM_FOV channel); depth passes SUPPORTED (mme_saveDepth);
supersampling = MSAA-in-FBO only. Gameplay masters stay clean — no baked
blur/DoF; those belong to TR4SH_CINEMATIC_REPLAY.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

WOLFCAM_VERSION = "wolfcamql-11.3+laa"
RESOLUTION = (1920, 1080)
FPS = 60
CODEC = "mjpeg"
JPEG_QUALITY = 90
MASTER_POV_FOV = 115

# LATCH cvars -> command line +set (renderer reads them once at startup).
LAUNCH_SETS = {
    "r_picmip": 0,
    "r_texturebits": 32,
    "r_colorbits": 32,
    "r_ext_max_anisotropy": 16,
    "r_ext_compressed_textures": 0,
    "r_detailtextures": 1,
    "r_simpleMipMaps": 0,
    "r_roundImagesDown": 0,
    "r_ignorehwgamma": 1,
    "r_useFbo": 1,
    "r_fboAntiAlias": 4,
    "sv_pure": 0,
    "com_zoneMegs": 96,
    "com_hunkMegs": 256,
}

_QUALITY = {
    "cl_aviFrameRate": FPS,
    "cl_aviCodec": CODEC,
    "r_jpegCompressionQuality": JPEG_QUALITY,
    "cl_aviAllowLargeFiles": 1,
    "r_lodbias": -2,
    "r_lodCurveError": 10000,
    "r_subdivisions": 1,
    "r_vertexLight": 0,
    "r_dynamiclight": 1,
    "r_finish": 1,
    "r_textureMode": "GL_LINEAR_MIPMAP_LINEAR",
    "cg_shadows": 1,
    "cg_marks": 1,
    "cg_railQL": 1,
    "cl_noprint": 1,
    "s_volume": 1.0,
}

# B1 - the clean-frame contract: every 2D element and the gun model off,
# every world effect on (beams, trails, projectiles, explosions, models).
# Proven by bench frames pf_clean_pov / pf_clean_72.
_CLEAN_POV = {
    "cg_draw2D": 0,
    "cg_drawGun": 0,
    "cg_drawCrosshair": 0,
    "cg_drawStatus": 0,
    "cg_drawScores": 0,
    "cg_drawTimer": 0,
    "cg_drawVote": 0,
    "cg_drawTeamVote": 0,
    "cg_drawFollowing": 0,
    "wolfcam_drawFollowing": 0,
    "cg_drawSpecMessages": 0,
    "cg_drawItemPickups": 0,
    "cg_drawFragMessageTime": 0,   # frag message gate is a TIME cvar
    "cg_obituaryTime": 0,          # killfeed gate is a TIME cvar
    "cg_chatTime": 0,
    "cg_chatLines": 0,
    "con_notifytime": 0,
    "cg_drawFPS": 0,
    "cg_drawSpeed": 0,
    "cg_fov": MASTER_POV_FOV,
}

# 2A - the MAIN frag footage: HUD clutter gone, but the frag feed and a
# tuned frag confirmation stay — gameplay must not feel empty (mandate 2A/3/4).
# Feed/message styling via wolfcam's per-element cvars (cg_main.c:2253-2272).
_GAMEPLAY_MASTER = {
    **_CLEAN_POV,
    # restore the information layer, tuned
    "cg_draw2D": 1,
    "cg_obituaryTime": 2500,            # killfeed on, brisk
    "cg_drawFragMessageTime": 1800,     # confirmation on, short
    "cg_drawFragMessageScale": 0.22,    # subtle, not arcade
    "cg_drawFragMessageFadeTime": 250,
    "cg_drawFragMessageTokens": "You fragged %v",
    # keep the clutter suppressed even with draw2D on
    "cg_drawStatus": 0,
    "cg_drawScores": 0,
    "cg_drawTimer": 0,
    "cg_drawAmmoWarning": 0,
    "cg_lagometer": 0,
    "cg_drawAttacker": 0,
    "cg_drawRewards": 0,
    "cg_drawPickupItem": 0,
}

# B2 - verification profile: enough HUD to prove POV/frag/health on screen.
_REFERENCE_POV = {
    "cg_draw2D": 1,
    "cg_drawGun": 1,
    "cg_drawStatus": 1,
    "cg_drawFPS": 0,
    "cg_drawSpeed": 0,
    "cg_drawItemPickups": 0,
    "cg_fov": MASTER_POV_FOV,
}

# B3 - later premium alternate-angle pass; documented, not used by the batch.
_CINEMATIC_REPLAY = {
    **_CLEAN_POV,
    "mme_blurFrames": 8,           # accumulation sub-frames per output frame
    "mme_blurType": "gaussian",
    "cl_aviFrameRateDivider": 1,   # divider is DECIMATION - keep 1 with blur
    "mme_dofFrames": 0,            # enable per shot with the dof command
    "cg_railTrailTime": 1200,      # longer cinematic rail persistence
}

# B4 - archive-wide analysis rendering: speed over beauty; projection math
# (fov) must match masters so screen-space measurements transfer.
_ANALYSIS_HEADLESS = {
    "cg_draw2D": 0,
    "cg_drawGun": 0,
    "cg_fov": MASTER_POV_FOV,
    "s_volume": 0.0,
    "cg_shadows": 0,
    "cg_marks": 0,
    "r_dynamiclight": 0,
    "cl_aviFrameRate": 30,
    "cl_aviCodec": "mjpeg",
    "r_jpegCompressionQuality": 60,
}

PROFILES = {
    "TR4SH_GAMEPLAY_MASTER": {**_QUALITY, **_GAMEPLAY_MASTER},
    "TR4SH_MASTER_POV_CLEAN": {**_QUALITY, **_CLEAN_POV},
    "TR4SH_REFERENCE_POV": {**_QUALITY, **_REFERENCE_POV},
    "TR4SH_CINEMATIC_REPLAY": {**_QUALITY, **_CINEMATIC_REPLAY},
    "TR4SH_ANALYSIS_HEADLESS": {**_QUALITY, **_ANALYSIS_HEADLESS},
}

_CFG_FILES = {
    "TR4SH_GAMEPLAY_MASTER": "wolfcam_tr4sh_master_capture.cfg",
    "TR4SH_MASTER_POV_CLEAN": "wolfcam_tr4sh_cinematic_clean.cfg",
    "TR4SH_REFERENCE_POV": "wolfcam_tr4sh_reference.cfg",
    "TR4SH_CINEMATIC_REPLAY": "wolfcam_tr4sh_cinematic.cfg",
    "TR4SH_ANALYSIS_HEADLESS": "wolfcam_tr4sh_analysis.cfg",
}

PROFILE_NAME = "TR4SH_GAMEPLAY_MASTER"   # the MAIN frag footage (mandate 2A)


def cfg_text(profile: str = PROFILE_NAME) -> str:
    lines = [f"// {profile} - frozen profile ({WOLFCAM_VERSION})"]
    for k, v in PROFILES[profile].items():
        lines.append(f"seta {k} {v}" if not isinstance(v, str)
                     else f'seta {k} "{v}"')
    return "\n".join(lines) + "\n"


def profile_id(profile: str = PROFILE_NAME) -> str:
    payload = cfg_text(profile) + json.dumps(LAUNCH_SETS, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def write(staging_gamedir: Path) -> str:
    """Write all four cfgs + the JSON record; returns the master profile id."""
    for profile, fname in _CFG_FILES.items():
        (staging_gamedir / fname).write_text(cfg_text(profile),
                                             encoding="ascii")
    record = {
        "wolfcam_version": WOLFCAM_VERSION,
        "resolution": f"{RESOLUTION[0]}x{RESOLUTION[1]}",
        "fps": FPS, "codec": CODEC, "jpeg_quality": JPEG_QUALITY,
        "master_pov_fov": MASTER_POV_FOV,
        "launch_sets": LAUNCH_SETS,
        "profiles": {p: {"cfg_file": _CFG_FILES[p],
                         "capture_profile_id": profile_id(p),
                         "cvars": PROFILES[p]} for p in PROFILES},
        "batch_profile": PROFILE_NAME,
    }
    out = REPO_ROOT / "output" / "demo_v2" / "master_capture_profile.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=1), encoding="utf-8")
    return profile_id()
