"""Rendering fidelity as a separate axis from editorial decisions.

WHY THIS EXISTS. PANTHEON is an offline movie system. Nobody is waiting on
an interactive frame rate, so the final master may take a night or a week,
and editing should not. Those are two different questions and they must
not share a knob:

    EDITING SPEED      how fast can a director see a choice
    FINAL IMAGE        how good can the locked film look

The film is locked in edit_us. The camera, the choreography, the sync ports
and every timing decision are the same object whether it renders in four
minutes as a proxy or four days as a master. Only the fidelity changes.

    EDIT FAST.  LOCK THE MOVIE.  THEN RENDER THE BIG BOY.

WHAT THIS IS NOT. It is not a renderer. The frame generator today is
wolfcamql-11.3, driven by creative_suite/engine/wolfcam_capture.py, and
nothing here pretends otherwise. This module gives the director a way to
say what the image should do through time, in terms a future backend can
also honour, and it says plainly which of those terms the current backend
can act on.

TWO CONCEPTS, KEPT APART.

    RenderProfile     global fidelity tier chosen once per render job
                      (proxy, review, master...)

    RenderTreatment   scene-specific look, animatable over edit_us
                      (bloom rising into a drop, picmip stripping a world,
                      exposure peaking on the hero)

A treatment is choreography. It has keyframes on the same clock as a freeze
or a camera move, and it is subject to the same visual-focus rules: nothing
in it may make a protected skill harder to read, however expensive the
master is allowed to be.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable, Sequence

RENDER_PROFILE_VERSION = "render-profile-v1.0.0"
MS = 1000

# ── the frame generator we actually have ────────────────────────────────────

CURRENT_BACKEND = "wolfcamql-11.3"
BACKEND_WOLFCAM = "WOLFCAM"
BACKEND_MODERN_RASTER = "MODERN_RASTER"        # future: HDR / shadows / materials
BACKEND_PATH_TRACED = "PATH_TRACED"            # future: selective spectacle
BACKENDS = (BACKEND_WOLFCAM, BACKEND_MODERN_RASTER, BACKEND_PATH_TRACED)

# Where a control's availability claim comes from. A control the current
# engine exposes as a cvar is a fact; a control a future backend would offer
# is a design intent, and the two must never look alike in a plan.
AVAILABLE_NOW = "AVAILABLE_NOW"                # wolfcam cvar or command, verified
AVAILABLE_VIA_ASSETS = "AVAILABLE_VIA_ASSETS"  # needs a pk3 (texture pack, grade)
FUTURE_BACKEND = "FUTURE_BACKEND"              # needs a renderer we do not have
CAPABILITIES = (AVAILABLE_NOW, AVAILABLE_VIA_ASSETS, FUTURE_BACKEND)

# `at <t> <cvar> <value>` will execute for any cvar. That says nothing about
# what the engine does when the value lands. r_picmip is CVAR_LATCH in the
# vendored source: it takes effect on the next vid_restart, so a scheduled
# staircase would execute every line and change nothing on screen. Every
# control must say how it actually behaves once set.
# `cvarinterp <cvar> <from> <to> <seconds> ['real'|'game']`
# (cg_consolecmds.c:7244) ramps a cvar in the ENGINE, on either the real
# clock or the game clock. The model previously assumed the only way to
# vary a control was a staircase of scheduled `at` sets; a live cvar can
# instead be handed a start, an end and a duration once. The source's own
# examples are `cvarinterp s_volume 0 0.7 2.0` and
# `cvarinterp timescale 0.0001 1.0 6.0 real`.
CVARINTERP = "cvarinterp"
LIVE_CONTINUOUS = "LIVE_CONTINUOUS"      # any value, takes effect next frame
LIVE_DISCRETE = "LIVE_DISCRETE"          # a few values, takes effect next frame
LIVE_STEP_ONLY = "LIVE_STEP_ONLY"        # live, but visibly a staircase
LATCHED = "LATCHED"                      # CVAR_LATCH: needs vid_restart
RELOAD_REQUIRED = "RELOAD_REQUIRED"      # needs the map / assets reloaded
RESTART_REQUIRED = "RESTART_REQUIRED"    # needs the engine relaunched
UNSUPPORTED = "UNSUPPORTED"              # no runtime path at all
UNKNOWN = "UNKNOWN"                      # not yet read from source or measured
LIVENESS = (LIVE_CONTINUOUS, LIVE_DISCRETE, LIVE_STEP_ONLY, LATCHED,
            RELOAD_REQUIRED, RESTART_REQUIRED, UNSUPPORTED, UNKNOWN)
ANIMATABLE = (LIVE_CONTINUOUS, LIVE_DISCRETE, LIVE_STEP_ONLY)

# Where a liveness claim comes from. Reading CVAR_LATCH off the source is a
# fact about the source; whether wolfcam's build changed it is a separate
# fact that only a canary can supply.
FROM_SOURCE = "FROM_SOURCE"
MEASURED = "MEASURED"
ASSUMED = "ASSUMED"

# How far a control's claim has been carried. Source flags establish what
# the engine means to do; only a captured frame establishes that the movie
# changed. Nothing is production-capable on the strength of the source.
SOURCE_DECLARED = "SOURCE_DECLARED"
ENGINE_APPLIED = "ENGINE_APPLIED"
CAPTURE_VISIBLE = "CAPTURE_VISIBLE"
TIMING_MEASURED = "TIMING_MEASURED"
VISUALLY_APPROVED = "VISUALLY_APPROVED"
TRUTH_LADDER = (SOURCE_DECLARED, ENGINE_APPLIED, CAPTURE_VISIBLE,
                TIMING_MEASURED, VISUALLY_APPROVED)

# Where, in the capture lifecycle, a latched value is actually set. Read off
# creative_suite/engine/master_profile.LAUNCH_SETS and wolfcam_capture:
#   LAUNCH_SET     +set on the command line, before the renderer starts  (A)
#   POSTINIT_CFG   only in a cfg exec'd via cgamepostinit.cfg, after     (C)
#   NOT_SET        never set by the pipeline; engine default             (C)
# Only A is usable shot-level configuration. C is LATCHED_NOT_APPLIED: the
# line executes and the picture does not change.
LAUNCH_SET = "LAUNCH_SET"
POSTINIT_CFG = "POSTINIT_CFG"
NOT_SET = "NOT_SET"
LATCHED_NOT_APPLIED = "LATCHED_NOT_APPLIED"


# ── profiles: how much the machine may spend ────────────────────────────────

PREVIEW_FAST = "PREVIEW_FAST"
REVIEW = "REVIEW"
MASTER_RASTER = "MASTER_RASTER"
MASTER_HERO = "MASTER_HERO"
MASTER_PATH_TRACE = "MASTER_PATH_TRACE"
PROFILE_NAMES = (PREVIEW_FAST, REVIEW, MASTER_RASTER, MASTER_HERO,
                 MASTER_PATH_TRACE)


@dataclass(frozen=True)
class RenderProfile:
    """One fidelity tier. Chosen per render job, never per shot."""
    name: str
    backend: str
    width: int
    height: int
    fps: int = 60
    internal_scale: float = 1.0        # >1 renders larger then downsamples
    aa_samples: int = 1                # r_fboAntiAlias on wolfcam
    motion_blur_frames: int = 0        # mme_blurFrames on wolfcam
    texture_quality: str = "STOCK"     # STOCK / UHD / PANTHEON packs
    intermediate: str = "mjpeg"        # capture codec before the encoder
    exists_today: bool = True
    timing_authoritative: bool = True  # may an editorial decision rest on it
    verified: bool = False             # has one end-to-end canary run at this size
    notes: str = ""

    def __post_init__(self) -> None:
        if self.name not in PROFILE_NAMES:
            raise ValueError(f"unknown render profile {self.name!r}")
        if self.backend not in BACKENDS:
            raise ValueError(f"unknown backend {self.backend!r}")
        if self.timing_authoritative and self.fps != 60:
            raise ValueError(
                "a profile that editorial decisions rest on delivers 60 "
                "distinct frames; a proxy is cheaper in pixels and lighting, "
                "never in time. Thumbnails and contact sheets may be cheaper, "
                "and they say so by not being timing-authoritative")
        if self.exists_today and self.backend != BACKEND_WOLFCAM:
            raise ValueError(
                f"{self.name}: claims to exist today on a backend we do not "
                f"have; the only frame generator is {CURRENT_BACKEND}")

    @property
    def internal_size(self) -> tuple[int, int]:
        return (int(self.width * self.internal_scale),
                int(self.height * self.internal_scale))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["internal_size"] = list(self.internal_size)
        return d


# The tiers. Two exist on the current backend; the rest are declared so the
# plan has a place for them, and say so.
PROFILES: dict[str, RenderProfile] = {p.name: p for p in (
    RenderProfile(PREVIEW_FAST, BACKEND_WOLFCAM, 1920, 1080,
                  aa_samples=0, motion_blur_frames=0, texture_quality="STOCK",
                  verified=True,
                  notes="fast deterministic proxy; same edit_us as the master. "
                        "1080p60 MJPEG is what the bench captures are"),
    RenderProfile(REVIEW, BACKEND_WOLFCAM, 2560, 1440,
                  aa_samples=4, motion_blur_frames=8, texture_quality="UHD",
                  verified=True,
                  notes="near-final look for sign-off; q90_1440.avi exists"),
    RenderProfile(MASTER_RASTER, BACKEND_WOLFCAM, 3840, 2160,
                  internal_scale=1.5, aa_samples=4, motion_blur_frames=16,
                  texture_quality="PANTHEON", intermediate="huffyuv",
                  verified=False,
                  notes="CANDIDATE. 6K internal has not been captured end to "
                        "end; framebuffer, depth resolution, stability and "
                        "disk throughput are unproven until one canary runs"),
    RenderProfile(MASTER_HERO, BACKEND_MODERN_RASTER, 3840, 2160,
                  internal_scale=2.0, aa_samples=8, motion_blur_frames=32,
                  texture_quality="PANTHEON", intermediate="huffyuv",
                  exists_today=False,
                  notes="needs a backend with HDR, shadow maps and material "
                        "response; declared, not available"),
    RenderProfile(MASTER_PATH_TRACE, BACKEND_PATH_TRACED, 3840, 2160,
                  internal_scale=1.0, aa_samples=1, texture_quality="PANTHEON",
                  intermediate="exr", exists_today=False,
                  notes="selective spectacle only; declared, not available"),
)}


def available_profiles() -> list[str]:
    return [n for n, p in PROFILES.items() if p.exists_today]


def proven_profiles() -> list[str]:
    """Exists AND has been captured end to end at its stated size."""
    return [n for n, p in PROFILES.items() if p.exists_today and p.verified]


# ── controls: what the image can be told to do ──────────────────────────────

@dataclass(frozen=True)
class RenderControl:
    """One thing the look can vary, and whether we can vary it today."""
    name: str
    capability: str
    backend_binding: str = ""      # the cvar / command on the current backend
    lo: float = 0.0
    hi: float = 1.0
    readability_risk: str = "LOW"  # LOW / MEDIUM / HIGH: how it hurts a skill
    notes: str = ""
    integer: bool = True           # most cvars are; the engine truncates floats
    liveness: str = UNKNOWN
    liveness_provenance: str = ASSUMED
    truth: str = SOURCE_DECLARED

    def __post_init__(self) -> None:
        if self.truth not in TRUTH_LADDER:
            raise ValueError(f"{self.name}: unknown truth rung {self.truth!r}")
        if self.capability not in CAPABILITIES:
            raise ValueError(f"{self.name}: unknown capability")
        if self.liveness not in LIVENESS:
            raise ValueError(f"{self.name}: unknown liveness {self.liveness!r}")
        if self.liveness_provenance not in (FROM_SOURCE, MEASURED, ASSUMED):
            raise ValueError(f"{self.name}: unknown liveness provenance")
        if self.capability == AVAILABLE_NOW and self.liveness == UNKNOWN:
            raise ValueError(
                f"{self.name}: bound to a cvar but does not say what happens "
                f"when the value lands; schedulable is not animatable")
        if self.capability == AVAILABLE_NOW and not self.backend_binding:
            raise ValueError(
                f"{self.name}: claims to be available now but names no cvar "
                f"or command; that is a hope, not a capability")
        if self.readability_risk not in ("LOW", "MEDIUM", "HIGH"):
            raise ValueError(f"{self.name}: unknown readability risk")

    @property
    def usable_now(self) -> bool:
        return self.capability != FUTURE_BACKEND

    @property
    def animatable(self) -> bool:
        """Whether a keyframe on this control changes the picture while the
        engine is running. A latched cvar is usable per shot and not per
        frame."""
        return self.usable_now and self.liveness in ANIMATABLE

    @property
    def set_stage(self) -> str:
        """Where the current pipeline sets this cvar, from the code itself."""
        if self.liveness != LATCHED:
            return LAUNCH_SET if self.backend_binding in _launch_sets() else NOT_SET
        if self.backend_binding in _launch_sets():
            return LAUNCH_SET
        if self.backend_binding in _postinit_cvars():
            return POSTINIT_CFG
        return NOT_SET

    @property
    def shot_setup_usable(self) -> bool:
        """A latched control is shot configuration only if it reaches the
        engine before the renderer initialises."""
        return self.liveness == LATCHED and self.set_stage == LAUNCH_SET

    @property
    def application(self) -> str:
        if self.liveness != LATCHED:
            return "LIVE" if self.animatable else self.liveness
        return "SHOT_SETUP_ONLY" if self.shot_setup_usable else LATCHED_NOT_APPLIED

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(usable_now=self.usable_now, animatable=self.animatable)
        return d


def _launch_sets() -> dict:
    try:
        from creative_suite.engine import master_profile
        return dict(master_profile.LAUNCH_SETS)
    except Exception:            # pragma: no cover - import environment
        return {}


def _postinit_cvars() -> set:
    """Cvars that only ever reach the engine through a cfg exec'd after
    cgame init. Read from the master profile's cfg dictionaries."""
    try:
        from creative_suite.engine import master_profile
        out: set = set()
        for prof in getattr(master_profile, "PROFILES", {}).values():
            out.update(prof.keys() if isinstance(prof, dict) else ())
        return out - set(_launch_sets())
    except Exception:            # pragma: no cover
        return set()


# Every binding below was read from the master profile or the scene
# compiler, not assumed. The values are unitless 0..1 in a treatment and
# the backend adapter maps them onto the cvar's real range.
CONTROLS: dict[str, RenderControl] = {c.name: c for c in (
    # Latched in the vendored source (CVAR_ARCHIVE | CVAR_LATCH). Set per
    # shot before vid_restart; a keyframe on any of these does nothing.
    RenderControl("picmip", AVAILABLE_NOW, "r_picmip", 0, 16, "HIGH",
                  "texture resolution stripping, per shot only; NOT a live "
                  "reveal primitive", liveness=LATCHED,
                  liveness_provenance=FROM_SOURCE),
    RenderControl("anisotropy", AVAILABLE_NOW, "r_ext_max_anisotropy", 1, 16,
                  liveness=LATCHED, liveness_provenance=FROM_SOURCE),
    RenderControl("anti_alias", AVAILABLE_NOW, "r_fboAntiAlias", 0, 8,
                  liveness=LATCHED, liveness_provenance=FROM_SOURCE),
    RenderControl("overbright", AVAILABLE_NOW, "r_overBrightBits", 0, 2,
                  "MEDIUM", liveness=LATCHED, liveness_provenance=FROM_SOURCE),
    RenderControl("map_brightness", AVAILABLE_NOW, "r_mapOverBrightBits",
                  0, 3, "MEDIUM", liveness=LATCHED,
                  liveness_provenance=FROM_SOURCE),
    RenderControl("fullbright", AVAILABLE_NOW, "r_fullbright", 0, 1,
                  "MEDIUM", "flattens all lighting, per shot only",
                  liveness=LATCHED, liveness_provenance=FROM_SOURCE),
    # Live in the source (CVAR_ARCHIVE only). Wolfcam's own additions are
    # believed live and marked ASSUMED until a canary says so.
    RenderControl("texture_filtering", AVAILABLE_NOW, "r_textureMode", 0, 1,
                  "MEDIUM", "GL_NEAREST through trilinear",
                  liveness=LIVE_DISCRETE, liveness_provenance=FROM_SOURCE),
    RenderControl("lod_bias", AVAILABLE_NOW, "r_lodbias", -2, 2, "MEDIUM",
                  liveness=LIVE_STEP_ONLY, liveness_provenance=FROM_SOURCE),
    RenderControl("dynamic_lights", AVAILABLE_NOW, "r_dynamiclight", 0, 1,
                  "LOW", "weapon and projectile light contribution",
                  liveness=LIVE_DISCRETE, liveness_provenance=FROM_SOURCE),
    # The one control carried past the source: two captures of the same
    # 8.5 s window at r_gamma 1.0 and 1.8 differed by 88.8 mean grey levels
    # with rank correlation 0.956 (docs/reference/runtime_truth_canary.json).
    # The gamma table is rebuilt on modification (tr_cmds.c:461) and applied
    # to the video buffer in software under r_ignorehwgamma 1.
    RenderControl("gamma", AVAILABLE_NOW, "r_gamma", 0.5, 3.0, "MEDIUM",
                  "the only render control proven to reach the captured "
                  "frame; timing still unswept",
                  integer=False, liveness=LIVE_CONTINUOUS,
                  liveness_provenance=MEASURED, truth=CAPTURE_VISIBLE),
    RenderControl("player_shadows", AVAILABLE_NOW, "cg_shadows", 0, 3, "LOW",
                  liveness=LIVE_DISCRETE, liveness_provenance=ASSUMED),
    RenderControl("impact_marks", AVAILABLE_NOW, "cg_marks", 0, 1,
                  liveness=LIVE_DISCRETE, liveness_provenance=ASSUMED),
    RenderControl("rail_trail_time", AVAILABLE_NOW, "cg_railTrailTime",
                  0, 3000, "LOW", liveness=LIVE_STEP_ONLY,
                  liveness_provenance=ASSUMED),
    RenderControl("motion_blur", AVAILABLE_NOW, "mme_blurFrames", 0, 64,
                  "HIGH", "temporal supersampling; blinds a tracking duel",
                  liveness=LIVE_STEP_ONLY, liveness_provenance=ASSUMED),
    RenderControl("depth_of_field", AVAILABLE_NOW, "mme_dofFrames", 0, 64,
                  "HIGH", liveness=LIVE_STEP_ONLY, liveness_provenance=ASSUMED),
    RenderControl("fov", AVAILABLE_NOW, "cg_fov", 60, 140, "MEDIUM",
                  liveness=LIVE_STEP_ONLY, liveness_provenance=ASSUMED),
    RenderControl("weapon_draw", AVAILABLE_NOW, "cg_drawGun", 0, 1,
                  liveness=LIVE_DISCRETE, liveness_provenance=ASSUMED),
    RenderControl("depth_pass", AVAILABLE_NOW, "mme_saveDepth", 0, 1, "LOW",
                  "a depth buffer per frame, for outlines and fog in post",
                  liveness=LIVE_DISCRETE, liveness_provenance=ASSUMED),
    RenderControl("fx_cue", AVAILABLE_NOW, "at <t> runfx <name>", 0, 1,
                  "MEDIUM", "any authored .fx script at an instant",
                  liveness=LIVE_DISCRETE, liveness_provenance=MEASURED),
    RenderControl("texture_pack", AVAILABLE_VIA_ASSETS, "zzz_uhd_*.pk3", 0, 1,
                  "LOW", "UHD textures; changes what is on the walls",
                  liveness=RELOAD_REQUIRED, liveness_provenance=FROM_SOURCE),
    RenderControl("color_grade", AVAILABLE_VIA_ASSETS,
                  "zzz_zz_pantheon_grade.pk3 (colorcorrect.fs)", 0, 1, "LOW",
                  "post grade; per-scene variants need one pk3 each",
                  liveness=RELOAD_REQUIRED, liveness_provenance=ASSUMED),
    # `remapshader <original> <new> [time offset] [keep lightmap]`
    # (cg_consolecmds.c:7437) replaces a shader while the demo runs, and
    # `clearremappedshader` puts it back. This was filed as an asset swap
    # needing a reload, which put the material-transform primitive behind a
    # pk3 rebuild it does not need.
    RenderControl("material_swap", AVAILABLE_NOW, "remapshader", 0, 1,
                  "MEDIUM", "live shader replacement; the material-transform "
                  "primitive, revertible with clearremappedshader",
                  liveness=LIVE_DISCRETE, liveness_provenance=FROM_SOURCE),
    RenderControl("entity_freeze", AVAILABLE_NOW, "entityfreeze", 0, 1, "LOW",
                  "freeze ONE entity by number while the world runs on; a "
                  "selective freeze the ffmpeg-side operator cannot express",
                  liveness=LIVE_DISCRETE, liveness_provenance=FROM_SOURCE),
    RenderControl("entity_hide", AVAILABLE_NOW, "entityfilter", 0, 1, "MEDIUM",
                  "show only chosen entities, by type or number; a world "
                  "strip for ENTITIES, not for BSP geometry",
                  liveness=LIVE_DISCRETE, liveness_provenance=FROM_SOURCE),
    RenderControl("timescale", AVAILABLE_NOW, "timescale", 0.05, 4.0, "HIGH",
                  "engine-side speed, rampable with cvarinterp on the real "
                  "clock; a speed ramp that happens before capture rather "
                  "than in post",
                  integer=False, liveness=LIVE_CONTINUOUS,
                  liveness_provenance=FROM_SOURCE),
    RenderControl("information_text", AVAILABLE_NOW, "centerprint", 0, 1,
                  "MEDIUM", "engine-drawn centre text; an information reveal "
                  "that lands on a gameplay frame rather than over it",
                  liveness=LIVE_DISCRETE, liveness_provenance=FROM_SOURCE),
    RenderControl("bloom", FUTURE_BACKEND, "", 0, 1, "HIGH"),
    RenderControl("exposure", FUTURE_BACKEND, "", -4, 4, "MEDIUM"),
    RenderControl("tone_response", FUTURE_BACKEND, "", 0, 1, "MEDIUM"),
    RenderControl("shadow_maps", FUTURE_BACKEND, "", 0, 1, "LOW"),
    RenderControl("ambient_occlusion", FUTURE_BACKEND, "", 0, 1, "LOW"),
    RenderControl("material_response", FUTURE_BACKEND, "", 0, 1, "LOW",
                  "normal, specular, parallax"),
    RenderControl("rim_light", FUTURE_BACKEND, "", 0, 1, "LOW"),
    RenderControl("outline", FUTURE_BACKEND, "", 0, 1, "MEDIUM",
                  "derivable now from the depth pass in post"),
    RenderControl("volumetric_fog", FUTURE_BACKEND, "", 0, 1, "HIGH"),
    RenderControl("projectile_glow", FUTURE_BACKEND, "", 0, 1, "LOW"),
    RenderControl("particle_density", FUTURE_BACKEND, "", 0, 1, "MEDIUM"),
    RenderControl("path_tracing", FUTURE_BACKEND, "", 0, 1, "HIGH"),
)}


def animatable_controls() -> list[str]:
    return [c.name for c in CONTROLS.values() if c.animatable]


# ── where an effect is realised ─────────────────────────────────────────────
# The director asks for WORLD_REVEAL. Which layer delivers it is the
# backend's business, and a picmip staircase is one candidate among several,
# not the meaning of the idea. Keeping the creative concept apart from its
# implementation is what lets the same treatment survive a renderer change.

ENGINE = "ENGINE"                  # a cvar or command while capturing
CAPTURE_PASS = "CAPTURE_PASS"      # an extra pass the engine can write
COMPOSITOR = "COMPOSITOR"          # ffmpeg / offline post on delivered frames
SYNTHETIC = "SYNTHETIC"            # authored animation or external 3D
LAYERS = (ENGINE, CAPTURE_PASS, COMPOSITOR, SYNTHETIC)


@dataclass(frozen=True)
class Implementation:
    """One way a creative treatment could be realised, and how much of the
    idea it actually delivers."""
    layer: str
    means: str
    coverage: str            # FULL / PARTIAL / STYLISED
    capability: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.layer not in LAYERS:
            raise ValueError(f"unknown layer {self.layer!r}")
        if self.coverage not in ("FULL", "PARTIAL", "STYLISED"):
            raise ValueError(f"unknown coverage {self.coverage!r}")
        if self.capability not in CAPABILITIES:
            raise ValueError(f"unknown capability {self.capability!r}")


# The creative corpus is the spec of record. These are candidate routes to
# a few of its ideas; an idea with no FULL route today is not "done" because
# a stylised approximation exists.
IMPLEMENTATIONS: dict[str, tuple[Implementation, ...]] = {
    "WORLD_REVEAL": (
        Implementation(ENGINE, "r_picmip per shot", "STYLISED", AVAILABLE_NOW,
                       "texture reduction, latched; not a live reveal"),
        Implementation(CAPTURE_PASS, "mme_saveDepth + depth compositing",
                       "PARTIAL", AVAILABLE_NOW,
                       "geometry emerges from depth; textures do not fade"),
        Implementation(ENGINE, "shader replacement pack", "PARTIAL",
                       AVAILABLE_VIA_ASSETS, "per shot, reload required"),
        Implementation(ENGINE, "geometry suppression per frame", "FULL",
                       FUTURE_BACKEND, "the world-transform primitive"),
    ),
    "WALL_XRAY": (
        Implementation(CAPTURE_PASS, "depth pass + mask compositing",
                       "PARTIAL", AVAILABLE_NOW),
        Implementation(ENGINE, "surface suppression", "FULL", FUTURE_BACKEND),
    ),
    "MAP_CONSTRUCTION": (
        Implementation(SYNTHETIC, "authored build animation", "FULL",
                       FUTURE_BACKEND, "author-defined duration"),
    ),
    "GEOMETRY_REBUILD": (
        Implementation(ENGINE, "geometry suppression per frame", "FULL",
                       FUTURE_BACKEND),
    ),
    "MATERIAL_PULSE": (
        Implementation(ENGINE, "remapshader + clearremappedshader", "FULL",
                       AVAILABLE_NOW,
                       "live shader swap and revert; timing unswept"),
        Implementation(ENGINE, "cvarinterp r_gamma", "STYLISED", AVAILABLE_NOW,
                       "whole-frame, engine-ramped"),
        Implementation(COMPOSITOR, "selective grade on delivered frames",
                       "PARTIAL", AVAILABLE_NOW),
    ),
    "SPEED_RAMP": (
        Implementation(ENGINE, "cvarinterp timescale ... real", "FULL",
                       AVAILABLE_NOW,
                       "ramped by the engine before capture, so motion blur "
                       "and particles follow the ramp instead of being "
                       "resampled after the fact"),
        Implementation(COMPOSITOR, "setpts on delivered frames", "PARTIAL",
                       AVAILABLE_NOW, "measured; cannot recover sub-frame "
                       "detail the capture never had"),
    ),
    "SELECTIVE_FREEZE": (
        Implementation(ENGINE, "entityfreeze <entity>", "FULL", AVAILABLE_NOW,
                       "one entity holds while the world runs on"),
    ),
    "RHYTHMIC_IMAGE_STUTTER": (
        Implementation(COMPOSITOR, "frame hold / repeat on delivered frames",
                       "FULL", AVAILABLE_NOW, "measured; the stutter primitive"),
    ),
    "TIME_ECHO": (
        Implementation(COMPOSITOR, "frame blend on delivered frames", "FULL",
                       AVAILABLE_NOW),
    ),
    "MOSAIC_TILE_STEP": (
        Implementation(COMPOSITOR, "tile region stepping", "FULL",
                       AVAILABLE_NOW, "driven by unequal gesture IOIs"),
    ),
    "POV_PIP": (
        Implementation(COMPOSITOR, "overlay of a second capture", "FULL",
                       AVAILABLE_NOW, "measured: adds exactly zero time"),
    ),
    "INFORMATION_REVEAL": (
        Implementation(COMPOSITOR, "text / number overlays", "FULL",
                       AVAILABLE_NOW, "post-compositor exists, unswept"),
        Implementation(ENGINE, "centerprint / echopopup", "PARTIAL",
                       AVAILABLE_NOW,
                       "engine-drawn, so it is lit and compressed with the "
                       "frame; less control over type than the compositor"),
    ),
    "ENTITY_STRIP": (
        Implementation(ENGINE, "entityfilter <type|number>", "FULL",
                       AVAILABLE_NOW,
                       "hides entities, never BSP geometry -- this is not "
                       "WORLD_REVEAL and must not be sold as it"),
    ),
}


def routes_for(treatment: str) -> tuple[Implementation, ...]:
    return IMPLEMENTATIONS.get(treatment, ())


def best_route_now(treatment: str) -> Implementation | None:
    """The most complete implementation available today, if any. Returns
    None rather than a stylised stand-in when nothing reaches PARTIAL."""
    order = {"FULL": 0, "PARTIAL": 1, "STYLISED": 2}
    now = [r for r in routes_for(treatment) if r.capability != FUTURE_BACKEND]
    now.sort(key=lambda r: order[r.coverage])
    return now[0] if now and now[0].coverage != "STYLISED" else None


# ── capture passes the engine can write ─────────────────────────────────────

PASSES: dict[str, dict[str, Any]] = {
    "beauty": {"capability": AVAILABLE_NOW, "binding": "video avi",
               "notes": "the frame itself"},
    "depth": {"capability": AVAILABLE_NOW, "binding": "mme_saveDepth",
              "notes": "per-frame depth; outlines, haze and masks in post"},
    "stencil": {"capability": AVAILABLE_NOW, "binding": "mme_saveStencil",
                "notes": "present in the mme lineage; unverified on this build",
                "verified": False},
    "object_id": {"capability": FUTURE_BACKEND, "binding": "",
                  "notes": "per-pixel entity id; no runtime path"},
    "isolated_subject": {"capability": FUTURE_BACKEND, "binding": "",
                         "notes": "player or weapon alone; would need id masks "
                                  "or a second capture with the world hidden"},
}


# ── how a backend earns its place ───────────────────────────────────────────

@dataclass(frozen=True)
class BackendEvaluation:
    """A future renderer is judged by what it does for the creative corpus,
    not by its feature list."""
    backend: str
    creative_ideas_unlocked: tuple[str, ...]
    existing_protocols_improved: tuple[str, ...]
    image_quality_gain: str          # LOW / MEDIUM / HIGH
    implementation_cost: str         # REQUIRES_INTEGRATION_SPIKE until proven
    pipeline_risk: str
    determinism: str
    multipass_support: str
    offline_render_value: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


REQUIRES_INTEGRATION_SPIKE = "REQUIRES_INTEGRATION_SPIKE"

BACKEND_EVALUATIONS: dict[str, BackendEvaluation] = {
    BACKEND_MODERN_RASTER: BackendEvaluation(
        BACKEND_MODERN_RASTER,
        creative_ideas_unlocked=("WORLD_REVEAL", "GEOMETRY_REBUILD",
                                 "WALL_XRAY", "LOW_HP_WORLD"),
        existing_protocols_improved=("MATERIAL_PULSE", "MODEL_PULSE",
                                     "ROUND_WIN_RELEASE", "PROJECTILE_FOLLOW"),
        image_quality_gain="HIGH", implementation_cost=REQUIRES_INTEGRATION_SPIKE,
        pipeline_risk="MEDIUM", determinism="EXPECTED_DETERMINISTIC",
        multipass_support="LIKELY", offline_render_value="HIGH",
        notes="no calendar estimate until a spike proves the cgame seam"),
    BACKEND_PATH_TRACED: BackendEvaluation(
        BACKEND_PATH_TRACED,
        creative_ideas_unlocked=(),
        existing_protocols_improved=("PROJECTILE_REPLAY", "MAP_CONSTRUCTION"),
        image_quality_gain="HIGH", implementation_cost=REQUIRES_INTEGRATION_SPIKE,
        pipeline_risk="HIGH", determinism="SEED_DEPENDENT",
        multipass_support="UNKNOWN", offline_render_value="SELECTIVE",
        notes="parked; rare hero shots only"),
}


def controls_by_capability() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {c: [] for c in CAPABILITIES}
    for c in CONTROLS.values():
        out[c.capability].append(c.name)
    return out


# ── semantic looks: what the director asks for by name ──────────────────────

QL_CLEAN = "QL_CLEAN"
QL_CINEMATIC = "QL_CINEMATIC"
PANTHEON_HERO = "PANTHEON_HERO"
PANTHEON_SURREAL = "PANTHEON_SURREAL"
PATH_TRACED_HERO = "PATH_TRACED_HERO"
LOOKS = (QL_CLEAN, QL_CINEMATIC, PANTHEON_HERO, PANTHEON_SURREAL,
         PATH_TRACED_HERO)

# What each look sets, in 0..1 control space. Only controls that exist are
# named here; a look that wanted bloom says so through `wants`, and the
# planner reports it as unmet rather than silently dropping it.
LOOK_STATE: dict[str, dict[str, float]] = {
    QL_CLEAN: {"picmip": 0.0, "motion_blur": 0.0, "depth_of_field": 0.0,
               "dynamic_lights": 1.0, "player_shadows": 0.33,
               "fullbright": 0.0, "anti_alias": 0.5},
    QL_CINEMATIC: {"picmip": 0.0, "motion_blur": 0.125, "depth_of_field": 0.0,
                   "dynamic_lights": 1.0, "player_shadows": 1.0,
                   "impact_marks": 1.0, "anti_alias": 1.0},
    PANTHEON_HERO: {"picmip": 0.0, "motion_blur": 0.25, "dynamic_lights": 1.0,
                    "player_shadows": 1.0, "rail_trail_time": 0.6,
                    "anti_alias": 1.0, "overbright": 0.5},
    PANTHEON_SURREAL: {"picmip": 0.6, "fullbright": 1.0, "dynamic_lights": 0.0,
                       "player_shadows": 0.0, "depth_pass": 1.0},
    PATH_TRACED_HERO: {"anti_alias": 1.0, "player_shadows": 1.0},
}
LOOK_WANTS: dict[str, tuple[str, ...]] = {
    QL_CLEAN: (),
    QL_CINEMATIC: ("bloom", "tone_response"),
    PANTHEON_HERO: ("bloom", "exposure", "shadow_maps", "material_response",
                    "projectile_glow"),
    PANTHEON_SURREAL: ("outline", "material_response"),
    PATH_TRACED_HERO: ("path_tracing", "bloom", "exposure", "shadow_maps"),
}


def look_unmet(look: str) -> list[str]:
    """What this look asks for that the current backend cannot give."""
    return [c for c in LOOK_WANTS.get(look, ()) if not CONTROLS[c].usable_now]


# ── treatment: the look through time ────────────────────────────────────────

@dataclass(frozen=True)
class Keyframe:
    at_us: int
    values: dict[str, float]
    ease: str = "LINEAR"           # LINEAR / HOLD / SMOOTH

    def __post_init__(self) -> None:
        for k in self.values:
            if k not in CONTROLS:
                raise ValueError(f"unknown render control {k!r}")
        if self.ease not in ("LINEAR", "HOLD", "SMOOTH"):
            raise ValueError(f"unknown ease {self.ease!r}")


@dataclass(frozen=True)
class RenderTreatment:
    """A scene's look as keyframes on edit_us.

    This is choreography. A picmip ramp is on the same clock as a freeze,
    and a bloom rise lands on the same musical anchor a camera move would.
    """
    scene_ref: str
    look: str
    keyframes: tuple[Keyframe, ...] = ()
    protected: tuple[tuple[int, int], ...] = ()    # skill intervals in edit_us

    def __post_init__(self) -> None:
        if self.look not in LOOKS:
            raise ValueError(f"unknown look {self.look!r}")
        ts = [k.at_us for k in self.keyframes]
        if ts != sorted(ts):
            raise ValueError("keyframes must be in time order")

    def base(self) -> dict[str, float]:
        return dict(LOOK_STATE[self.look])

    def state_at(self, at_us: int) -> dict[str, float]:
        """The full control state at one instant of edit time."""
        state = self.base()
        if not self.keyframes:
            return state
        prev = None
        for k in self.keyframes:
            if k.at_us <= at_us:
                prev = k
            else:
                nxt = k
                break
        else:
            nxt = None
        if prev is None:
            return state
        state.update(prev.values)
        if nxt is None or prev.ease == "HOLD" or nxt.at_us == prev.at_us:
            return state
        f = (at_us - prev.at_us) / (nxt.at_us - prev.at_us)
        if prev.ease == "SMOOTH":
            f = f * f * (3 - 2 * f)
        for key, target in nxt.values.items():
            start = state.get(key, LOOK_STATE[self.look].get(key, 0.0))
            state[key] = start + (target - start) * f
        return state

    def in_protected(self, at_us: int) -> bool:
        return any(a <= at_us < b for a, b in self.protected)

    def unmet(self) -> list[str]:
        """Controls this treatment touches that no current backend honours."""
        used = set(LOOK_WANTS.get(self.look, ()))
        for k in self.keyframes:
            used.update(k.values)
        return sorted(c for c in used if not CONTROLS[c].usable_now)

    def to_dict(self) -> dict[str, Any]:
        return {"scene_ref": self.scene_ref, "look": self.look,
                "keyframes": [asdict(k) for k in self.keyframes],
                "protected": [list(p) for p in self.protected],
                "unmet_on_current_backend": self.unmet(),
                "version": RENDER_PROFILE_VERSION}


# ── skill protection: the master may not blind the viewer ───────────────────

# During a protected skill interval, controls that hurt readability are
# capped regardless of profile. The numbers are the director's to move; the
# rule that they exist is not.
PROTECTED_CAPS: dict[str, float] = {
    "motion_blur": 0.125,       # ~8 frames at most
    "depth_of_field": 0.0,
    "picmip": 0.0,
    "bloom": 0.2,
    "volumetric_fog": 0.0,
    "fullbright": 0.0,
}


@dataclass(frozen=True)
class Violation:
    at_us: int
    control: str
    value: float
    cap: float
    reason: str


def readability_violations(t: RenderTreatment, step_us: int = 16_667
                           ) -> list[Violation]:
    """Every instant inside a protected interval where the look would make
    the skill harder to read."""
    out: list[Violation] = []
    for a, b in t.protected:
        at = a
        while at < b:
            st = t.state_at(at)
            for ctrl, cap in PROTECTED_CAPS.items():
                v = st.get(ctrl)
                if v is not None and v > cap + 1e-9:
                    why = CONTROLS[ctrl].notes or "this hurts readability"
                    out.append(Violation(
                        at, ctrl, round(v, 4), cap,
                        f"{ctrl} at {v:.2f} exceeds the protected-skill cap "
                        f"of {cap:.2f}; {why}"))
            at += step_us
    return out


def clamp_for_protection(t: RenderTreatment) -> RenderTreatment:
    """The same treatment with protected intervals forced legal.

    Keeps every keyframe outside the intervals untouched and inserts HOLD
    keyframes at the interval edges so the clamp cannot leak into the
    reveal before or the payoff after.
    """
    if not t.protected:
        return t
    frames = list(t.keyframes)
    for a, b in t.protected:
        entry = dict(t.state_at(a))
        capped = {k: min(v, PROTECTED_CAPS[k]) for k, v in entry.items()
                  if k in PROTECTED_CAPS}
        exit_state = dict(t.state_at(b))
        # Pin the look just before the interval, or the keyframe before it
        # would interpolate toward the clamp and the reveal would fade
        # early. The clamp begins at the interval, not on approach to it.
        frames.append(Keyframe(a - 1, entry, "HOLD"))
        frames.append(Keyframe(a, {**entry, **capped}, "HOLD"))
        frames.append(Keyframe(b, exit_state, "LINEAR"))
    frames.sort(key=lambda k: k.at_us)
    # a keyframe inside a protected interval must obey the caps too
    fixed = []
    for k in frames:
        if t.in_protected(k.at_us):
            vals = {c: (min(v, PROTECTED_CAPS[c]) if c in PROTECTED_CAPS else v)
                    for c, v in k.values.items()}
            fixed.append(Keyframe(k.at_us, vals, "HOLD"))
        else:
            fixed.append(k)
    return RenderTreatment(t.scene_ref, t.look, tuple(fixed), t.protected)


# ── determinism: the same film at every fidelity ────────────────────────────

def render_key(*, scene_hash: str, camera_hash: str, choreography_hash: str,
               treatment: RenderTreatment, profile: RenderProfile,
               asset_hash: str) -> str:
    """The cache identity of one rendered shot.

    Two renders with the same key are the same shot. A change to the
    profile changes the key and nothing else, which is what lets a failed
    shot 117 be re-rendered alone and dropped back into the same edit_us.
    """
    payload = {
        "scene": scene_hash, "camera": camera_hash,
        "choreography": choreography_hash,
        "treatment": treatment.to_dict(), "profile": profile.to_dict(),
        "assets": asset_hash, "version": RENDER_PROFILE_VERSION,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def editorial_key(*, scene_hash: str, camera_hash: str,
                  choreography_hash: str, treatment: RenderTreatment) -> str:
    """Everything about the shot EXCEPT fidelity. Must be identical across
    every profile, or the proxy was not a proxy of the master."""
    payload = {"scene": scene_hash, "camera": camera_hash,
               "choreography": choreography_hash,
               "treatment": treatment.to_dict()}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


# ── the backend seam ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ScheduledCvar:
    """One backend-specific instruction, with its quantisation on record.

    The director asked for a semantic value; the engine got an integer; the
    picture did whatever it did. All three are kept so a mismatch between
    intent and delivery is visible rather than absorbed.
    """
    at_ms: int
    cvar: str
    value: str                       # what the engine is told
    control: str = ""
    # a ramp is one command; a staircase is one command per step
    requested_unit: float | None = None   # 0..1 semantic value from the plan
    compiled_value: float | None = None   # after range mapping, before rounding
    delivered: str | None = None          # what a canary observed, if any

    ramp_to: str | None = None        # cvarinterp target
    ramp_ms: int | None = None

    def line(self) -> str:
        if self.ramp_to is not None and self.ramp_ms:
            return (f"at {self.at_ms} {CVARINTERP} {self.cvar} {self.value} "
                    f"{self.ramp_to} {self.ramp_ms / 1000.0:.3f}")
        return f"at {self.at_ms} {self.cvar} {self.value}"

    @property
    def quantisation_error(self) -> float | None:
        if self.compiled_value is None:
            return None
        try:
            return float(self.value) - self.compiled_value
        except ValueError:
            return None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["quantisation_error"] = self.quantisation_error
        return d


def _to_engine_value(ctrl: RenderControl, unit: float) -> tuple[str, float]:
    """Engine string and the unrounded value it came from."""
    v = ctrl.lo + (ctrl.hi - ctrl.lo) * max(0.0, min(1.0, unit))
    if ctrl.name == "texture_filtering":
        return (("GL_LINEAR_MIPMAP_LINEAR" if unit >= 0.5 else "GL_NEAREST"), v)
    if ctrl.integer:
        # A ramp on an integer cvar is a staircase. The treatment may ask for
        # 0.417 of fullbright; the engine has 0 and 1, and pretending
        # otherwise would schedule a value it silently truncates.
        return (str(int(round(v))), v)
    return (f"{v:.3f}", v)


@dataclass(frozen=True)
class WolfcamJob:
    """What the current engine will actually be told, and what it will not.

    `launch_sets` are latched cvars that reach the engine as `+set` before
    the renderer starts -- the only way a latched value takes effect. Only
    `scheduled` animates. `not_animatable` lists every control the treatment
    keyframed that the engine cannot change while running, and
    `latched_not_applied` lists latched controls the pipeline has no launch
    route for, so a director learns both here and not from a flat render.
    """
    launch_sets: dict[str, str]
    scheduled: tuple[ScheduledCvar, ...]
    not_animatable: tuple[str, ...]
    latched_not_applied: tuple[str, ...]
    unmet: tuple[str, ...]

    def lines(self) -> list[str]:
        return [c.line() for c in self.scheduled]

    def to_dict(self) -> dict[str, Any]:
        return {"launch_sets": dict(self.launch_sets),
                "scheduled": [c.to_dict() for c in self.scheduled],
                "not_animatable": list(self.not_animatable),
                "latched_not_applied": list(self.latched_not_applied),
                "unmet": list(self.unmet)}


def compile_wolfcam(t: RenderTreatment, edit_to_demo_ms, step_us: int = 100_000
                    ) -> WolfcamJob:
    """Turn a treatment into what the current engine can honour.

    This is the only place that knows the backend. A future rasteriser gets
    its own compile_* and the treatment does not change.

    A cvar the source marks CVAR_LATCH is set once at shot setup from the
    treatment's FIRST state and never scheduled: `at` would execute the line
    and the picture would not change. The keyframes that asked for it are
    reported in `not_animatable`.
    """
    unmet = tuple(t.unmet())
    keyed: set[str] = set()
    for k in t.keyframes:
        keyed.update(k.values)
    not_anim = tuple(sorted(
        n for n in keyed
        if n in CONTROLS and CONTROLS[n].usable_now
        and not CONTROLS[n].animatable))

    def make(name: str, unit: float, at_ms: int) -> ScheduledCvar:
        c = CONTROLS[name]
        val, raw = _to_engine_value(c, unit)
        return ScheduledCvar(at_ms, c.backend_binding, val, name, unit, raw)

    first_state = t.state_at(t.keyframes[0].at_us) if t.keyframes else t.base()
    t0 = int(edit_to_demo_ms(t.keyframes[0].at_us if t.keyframes else 0))
    # Latched values go to the command line or nowhere. A cfg line for one
    # would execute and change nothing, which is worse than refusing.
    launch: dict[str, str] = {}
    not_applied: list[str] = []
    for n, u in first_state.items():
        c = CONTROLS.get(n)
        if c is None or c.capability != AVAILABLE_NOW or c.liveness != LATCHED:
            continue
        if c.shot_setup_usable:
            launch[c.backend_binding] = _to_engine_value(c, u)[0]
        else:
            not_applied.append(n)

    lines: list[ScheduledCvar] = []
    if not t.keyframes:
        for n, u in first_state.items():
            c = CONTROLS[n]
            if c.animatable and c.name != "fx_cue":
                lines.append(make(n, u, t0))
        return WolfcamJob(launch, tuple(lines), not_anim,
                          tuple(sorted(not_applied)), unmet)

    start, end = t.keyframes[0].at_us, t.keyframes[-1].at_us
    at = start
    last: dict[str, str] = {}
    while at <= end:
        st = t.state_at(at)
        for n, u in st.items():
            c = CONTROLS[n]
            if not c.animatable or c.name == "fx_cue":
                continue
            sc = make(n, u, int(edit_to_demo_ms(at)))
            if last.get(n) != sc.value:
                lines.append(sc)
                last[n] = sc.value
        at += step_us
    return WolfcamJob(launch, tuple(lines), not_anim,
                      tuple(sorted(not_applied)), unmet)


def application_report() -> list[dict[str, Any]]:
    """For every control bound to the current engine: how it is applied,
    where the pipeline sets it, and how far its claim has been carried."""
    out = []
    for c in CONTROLS.values():
        if c.capability != AVAILABLE_NOW:
            continue
        out.append({"control": c.name, "cvar": c.backend_binding,
                    "liveness": c.liveness, "set_stage": c.set_stage,
                    "application": c.application, "truth": c.truth,
                    "liveness_provenance": c.liveness_provenance})
    return out


def can_ramp(control: str) -> bool:
    """Whether this control can be handed to cvarinterp instead of stepped.

    Only a live continuous cvar: cvarinterp writes a cvar every frame, so a
    latched one would be written and ignored, and a discrete one would be
    driven through values it does not have.
    """
    c = CONTROLS.get(control)
    return bool(c and c.capability == AVAILABLE_NOW
                and c.liveness == LIVE_CONTINUOUS and not c.integer)


def separation_report() -> dict[str, Any]:
    """Which layers are cleanly apart today, and where the seam is thin."""
    return {
        "layers": {
            "demo_truth": "engine/parser caches, creative_suite/engine/demo_truth.py",
            "choreography": "creative_suite/engine/choreography.py, temporal_*.py",
            "camera": "creative_suite/engine/camera_compiler_v2.py, camera_paths.py",
            "render_treatment": "creative_suite/engine/render_profile.py (this)",
            "frame_generation": "creative_suite/engine/wolfcam_capture.py -> "
                                + CURRENT_BACKEND,
        },
        "entanglements": [
            "pantheon_scene.py compiles the fx stack straight to wolfcam "
            "console lines; the scene knows the backend's command syntax",
            "VISUAL_LOOKS in pantheon_scene.py (ORIGINAL/UHD/PANTHEON) are "
            "pk3 names, which is a wolfcam asset mechanism rather than a look",
            "camera_compiler_v2 emits engine camera commands; a second "
            "backend would need its own emitter behind the same plan",
        ],
        "minimum_seam": (
            "one compile_<backend>() per frame generator, each consuming the "
            "same RenderTreatment, camera plan and edit_us map, and returning "
            "backend instructions plus the list of controls it could not "
            "honour. The director never sees a cvar"),
        "fx_emission": (
            "compile_fx_cfg_lines in pantheon_scene.py is already one isolated "
            "function with only test callers; relocating it is cosmetic and "
            "was not done"),
        "modern_raster_estimate": REQUIRES_INTEGRATION_SPIKE,
    }
