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
    notes: str = ""

    def __post_init__(self) -> None:
        if self.name not in PROFILE_NAMES:
            raise ValueError(f"unknown render profile {self.name!r}")
        if self.backend not in BACKENDS:
            raise ValueError(f"unknown backend {self.backend!r}")
        if self.fps != 60:
            raise ValueError(
                "every profile delivers 60 distinct frames; a proxy is cheaper "
                "in pixels and lighting, never in time, or its timing would "
                "not be the master's timing")
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
                  notes="fast deterministic proxy; same edit_us as the master"),
    RenderProfile(REVIEW, BACKEND_WOLFCAM, 2560, 1440,
                  aa_samples=4, motion_blur_frames=8, texture_quality="UHD",
                  notes="near-final look for sign-off"),
    RenderProfile(MASTER_RASTER, BACKEND_WOLFCAM, 3840, 2160,
                  internal_scale=1.5, aa_samples=4, motion_blur_frames=16,
                  texture_quality="PANTHEON", intermediate="huffyuv",
                  notes="current engine pushed as far as it goes: oversample "
                        "and downsample, lossless intermediate"),
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

    def __post_init__(self) -> None:
        if self.capability not in CAPABILITIES:
            raise ValueError(f"{self.name}: unknown capability")
        if self.capability == AVAILABLE_NOW and not self.backend_binding:
            raise ValueError(
                f"{self.name}: claims to be available now but names no cvar "
                f"or command; that is a hope, not a capability")
        if self.readability_risk not in ("LOW", "MEDIUM", "HIGH"):
            raise ValueError(f"{self.name}: unknown readability risk")

    @property
    def usable_now(self) -> bool:
        return self.capability != FUTURE_BACKEND

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["usable_now"] = self.usable_now
        return d


# Every binding below was read from the master profile or the scene
# compiler, not assumed. The values are unitless 0..1 in a treatment and
# the backend adapter maps them onto the cvar's real range.
CONTROLS: dict[str, RenderControl] = {c.name: c for c in (
    RenderControl("picmip", AVAILABLE_NOW, "r_picmip", 0, 16, "HIGH",
                  "texture resolution stripping; the world-reveal primitive"),
    RenderControl("texture_filtering", AVAILABLE_NOW, "r_textureMode", 0, 1,
                  "MEDIUM", "GL_NEAREST through trilinear"),
    RenderControl("anisotropy", AVAILABLE_NOW, "r_ext_max_anisotropy", 1, 16),
    RenderControl("lod_bias", AVAILABLE_NOW, "r_lodbias", -2, 2, "MEDIUM"),
    RenderControl("dynamic_lights", AVAILABLE_NOW, "r_dynamiclight", 0, 1,
                  "LOW", "weapon and projectile light contribution"),
    RenderControl("player_shadows", AVAILABLE_NOW, "cg_shadows", 0, 3, "LOW"),
    RenderControl("impact_marks", AVAILABLE_NOW, "cg_marks", 0, 1),
    RenderControl("rail_trail_time", AVAILABLE_NOW, "cg_railTrailTime",
                  0, 3000, "LOW"),
    RenderControl("motion_blur", AVAILABLE_NOW, "mme_blurFrames", 0, 64,
                  "HIGH", "temporal supersampling; blinds a tracking duel"),
    RenderControl("depth_of_field", AVAILABLE_NOW, "mme_dofFrames", 0, 64,
                  "HIGH"),
    RenderControl("anti_alias", AVAILABLE_NOW, "r_fboAntiAlias", 0, 8),
    RenderControl("gamma", AVAILABLE_NOW, "r_gamma", 0.5, 3.0, "MEDIUM",
                  integer=False),
    RenderControl("overbright", AVAILABLE_NOW, "r_overBrightBits", 0, 2,
                  "MEDIUM"),
    RenderControl("map_brightness", AVAILABLE_NOW, "r_mapOverBrightBits",
                  0, 3, "MEDIUM"),
    RenderControl("fullbright", AVAILABLE_NOW, "r_fullbright", 0, 1,
                  "MEDIUM", "flattens all lighting; a treatment, not a look"),
    RenderControl("fov", AVAILABLE_NOW, "cg_fov", 60, 140, "MEDIUM"),
    RenderControl("weapon_draw", AVAILABLE_NOW, "cg_drawGun", 0, 1),
    RenderControl("depth_pass", AVAILABLE_NOW, "mme_saveDepth", 0, 1, "LOW",
                  "a depth buffer per frame, for outlines and fog in post"),
    RenderControl("fx_cue", AVAILABLE_NOW, "at <t> runfx <name>", 0, 1,
                  "MEDIUM", "any authored .fx script at an instant"),
    RenderControl("texture_pack", AVAILABLE_VIA_ASSETS, "zzz_uhd_*.pk3", 0, 1,
                  "LOW", "UHD textures; changes what is on the walls"),
    RenderControl("color_grade", AVAILABLE_VIA_ASSETS,
                  "zzz_zz_pantheon_grade.pk3 (colorcorrect.fs)", 0, 1, "LOW",
                  "post grade; per-scene variants need one pk3 each"),
    RenderControl("material_swap", AVAILABLE_VIA_ASSETS, "zzz_*.pk3 shader",
                  0, 1, "MEDIUM", "the material-transform primitive"),
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
    """One backend-specific instruction the current engine understands."""
    at_ms: int
    cvar: str
    value: str

    def line(self) -> str:
        return f"at {self.at_ms} {self.cvar} {self.value}"


def _to_engine_value(ctrl: RenderControl, unit: float) -> str:
    v = ctrl.lo + (ctrl.hi - ctrl.lo) * max(0.0, min(1.0, unit))
    if ctrl.name == "texture_filtering":
        return ("GL_LINEAR_MIPMAP_LINEAR" if unit >= 0.5 else "GL_NEAREST")
    if ctrl.integer:
        # A ramp on an integer cvar is a staircase. The treatment may ask for
        # 0.417 of fullbright; the engine has 0 and 1, and pretending
        # otherwise would schedule a value it silently truncates.
        return str(int(round(v)))
    return f"{v:.3f}"


def compile_wolfcam(t: RenderTreatment, edit_to_demo_ms, step_us: int = 100_000
                    ) -> tuple[list[ScheduledCvar], list[str]]:
    """Turn a treatment into `at <t> <cvar> <value>` lines for the current
    engine, and say what it could not express.

    This is the only place that knows the backend. A future rasteriser gets
    its own compile_* and the treatment does not change.
    """
    lines: list[ScheduledCvar] = []
    unmet = t.unmet()
    if not t.keyframes:
        st = t.base()
        for name, unit in st.items():
            c = CONTROLS[name]
            if c.capability == AVAILABLE_NOW and c.name != "fx_cue":
                lines.append(ScheduledCvar(int(edit_to_demo_ms(0)),
                                           c.backend_binding,
                                           _to_engine_value(c, unit)))
        return lines, unmet
    start, end = t.keyframes[0].at_us, t.keyframes[-1].at_us
    at = start
    last: dict[str, str] = {}
    while at <= end:
        st = t.state_at(at)
        for name, unit in st.items():
            c = CONTROLS[name]
            if c.capability != AVAILABLE_NOW or c.name == "fx_cue":
                continue
            val = _to_engine_value(c, unit)
            if last.get(name) != val:
                lines.append(ScheduledCvar(int(edit_to_demo_ms(at)),
                                           c.backend_binding, val))
                last[name] = val
        at += step_us
    return lines, unmet


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
    }
