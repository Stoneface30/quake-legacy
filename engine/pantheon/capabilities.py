"""CapabilityRegistry — what a render backend can actually do, and how we know.

A director asks for FORCE_ENEMY_MODEL. It never asks for `cg_enemyModel`.
The spelling of a cvar, whether it is latched, whether the shipped binary
even registers it — all of that is backend detail, and this registry is
where a semantic request meets it.

EVIDENCE IS PART OF THE ANSWER. This project has concluded "the enemy is
green" from source three times and been wrong on pixels three times, so a
capability is not a boolean. It carries the strongest evidence anyone has
produced for it:

    DOCUMENTED         somebody wrote it down
    SOURCE_REGISTERED  a Cvar_Get for it exists in engine source
    BINARY_REGISTERED  the shipped binary names it
    EXECUTION_PROVEN   the RUNNING binary listed it (cvarlist), so it is
                       registered and not a silent no-op
    VISUALLY_PROVEN    a controlled A/B produced the expected pixels

UNKNOWN is a real answer. `cg_forceTeamModel` is named in the wider Quake
Live ecosystem, is absent from the canonical 12.7 source, and was never
covered by the 11.3 runtime probe (which asked `cg_team*` and the exact name
`cg_forcemodel`, neither of which matches it). Absence from the binary
strings proves nothing either: `cg_enemyModel` is missing from that dump too
and the runtime proves it exists. So the honest state is UNKNOWN, with the
exact probe that would settle it recorded here.

THE 12.7 TRAP. `docs/reference/2026-09-05-engine-registrations.csv` is
harvested from 12.7test49 source. The binary we film with is 11.3. A cvar in
that CSV is SOURCE_REGISTERED for a version we do not run; the engine
accepts an unknown cvar silently and does nothing with it, which is how a
capture came out looking unchanged while every log line said success.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path

from engine.pantheon import store as S

# TRACKED repo file, unlike the gitignored databases: it resolves against the
# checkout that owns this code, so a worktree reads its own branch's capture.
RUNTIME_CVARLIST = (S.REPO_ROOT / "docs" / "reference" / "engine_cvarlist_11_3.json")


class Evidence(IntEnum):
    """Ordered: a higher level supersedes a lower one."""
    UNKNOWN = 0
    DOCUMENTED = 1
    SOURCE_REGISTERED = 2
    BINARY_REGISTERED = 3
    EXECUTION_PROVEN = 4
    VISUALLY_PROVEN = 5


@dataclass(frozen=True)
class Capability:
    name: str
    evidence: Evidence
    how: str                              # what produced that evidence
    cvars: tuple[str, ...] = ()           # backend detail; callers never see it
    note: str = ""
    probe: str = ""                       # what would raise the evidence level
    # HOW THE EVIDENCE WAS OBTAINED, when it was not the cvarlist.
    #
    # A cvarlist line proves the engine REGISTERS a name. A measured change in
    # behaviour proves the engine ACTS on it, which is stronger and is the
    # only evidence available for a family the probe never asked about --
    # `in_*` was never probed, so its absence from the capture says nothing.
    # Naming the measurement here keeps the audit honest instead of widening
    # it: a capability with this field set must say what was measured.
    measured: str = ""

    @property
    def usable(self) -> bool:
        """Good enough to ask a backend for. EXECUTION_PROVEN means the
        runtime registers it; anything lower may be a silent no-op."""
        return self.evidence >= Evidence.EXECUTION_PROVEN

    def as_dict(self) -> dict:
        return {"name": self.name, "evidence": self.evidence.name, "how": self.how,
                "cvars": list(self.cvars), "note": self.note, "probe": self.probe,
                "measured": self.measured, "usable": self.usable}


# ── WolfcamQL 11.3, the binary we film with ────────────────────────────────
# Every EXECUTION_PROVEN line below was listed by `cvarlist <wildcard>` in the
# running 11.3 client; the capture is docs/reference/engine_cvarlist_11_3.json.

_PROBE_11_3 = "cvarlist against the running WolfcamQL 11.3 client"

WOLFCAM_11_3: dict[str, Capability] = {c.name: c for c in (
    Capability(
        "FORCE_ENEMY_MODEL", Evidence.EXECUTION_PROVEN, _PROBE_11_3,
        ("cg_enemyModel", "cg_enemyHeadModel"),
        "replaces the model of every player the POV reads as an enemy"),
    Capability(
        "FORCE_ENEMY_SKIN", Evidence.EXECUTION_PROVEN, _PROBE_11_3,
        ("cg_enemyHeadSkin", "cg_enemyTorsoSkin", "cg_enemyLegsSkin")),
    Capability(
        "FORCE_ENEMY_COLOUR", Evidence.EXECUTION_PROVEN, _PROBE_11_3,
        ("cg_enemyHeadColor", "cg_enemyTorsoColor", "cg_enemyLegsColor"),
        "colour is read as one 0xRRGGBB integer -- PROOF 0 measured it on "
        "pixels; a space-separated triple is read as its first number"),
    Capability(
        "FORCE_TEAM_MODEL", Evidence.EXECUTION_PROVEN, _PROBE_11_3,
        ("cg_teamModel", "cg_teamHeadModel"),
        "the TEAMMATE family: separate cvars from the enemy family, so the "
        "two can be set independently"),
    Capability(
        "FORCE_TEAM_SKIN", Evidence.EXECUTION_PROVEN, _PROBE_11_3,
        ("cg_teamHeadSkin", "cg_teamTorsoSkin", "cg_teamLegsSkin")),
    Capability(
        "FORCE_TEAM_COLOUR", Evidence.EXECUTION_PROVEN, _PROBE_11_3,
        ("cg_teamHeadColor", "cg_teamTorsoColor", "cg_teamLegsColor")),
    Capability(
        "FORCE_ALL_MODELS", Evidence.EXECUTION_PROVEN, _PROBE_11_3,
        ("cg_forceModel",),
        "the stock Q3 switch: force EVERY player to one model. It cannot "
        "distinguish enemy from teammate, so it is not the review mechanism"),
    Capability(
        "PLAYER_RAIL_COLOUR", Evidence.VISUALLY_PROVEN,
        "PROOF 0: measured beam core RGB per format on captured frames",
        ("cg_enemyRailColor1", "cg_enemyRailColor2",
         "cg_teamRailColor1", "cg_teamRailColor2")),
    Capability(
        "XRAY_PLAYER", Evidence.VISUALLY_PROVEN,
        "shipped engine feature, proven on grabbed frames",
        ("cg_wh", "cg_whEnemyColor", "cg_whEnemyAlpha", "cg_whColor", "cg_whAlpha"),
        "director code asks for XRAY_ACTOR; cg_wh never appears above the backend"),
    Capability(
        "CAMERA_FREE", Evidence.EXECUTION_PROVEN, _PROBE_11_3,
        ("cg_freecam_noclip", "cg_freecam_speed", "cg_freecam_sensitivity",
         "cg_freecam_yaw", "cg_freecam_pitch", "cg_freecam_unlockPitch"),
        "there is NO cvar called cg_freecam: the runtime registers only the "
        "cg_freecam_* settings, and free camera is entered by a console "
        "command. Assuming the bare name from the family would have written "
        "a cvar the engine discards in silence"),
    Capability(
        "CAMERA_FOLLOW", Evidence.EXECUTION_PROVEN, _PROBE_11_3, (),
        "follow/chase POV is the demo's own; no cvar needed"),
    Capability(
        "CAMERA_PATH", Evidence.EXECUTION_PROVEN,
        "cam10 camera files, exercised by the camera canaries", (),
        "wolfcam camera scripting"),
    Capability(
        "NATIVE_EFFECTS", Evidence.VISUALLY_PROVEN,
        "explosions, rail trails, jump pads and teleports render from the "
        "event codes the compiler emits; REAL_ACTION_TRACE_PROOF_01",
        ()),
    Capability(
        "PROJECTILE_RENDER", Evidence.VISUALLY_PROVEN,
        "missile entities replayed from the trace render as rockets", ()),
    Capability(
        "AUDIO_CAPTURE", Evidence.EXECUTION_PROVEN,
        "cl_avi* family registered; the synthetic AVI carried an audio track "
        "with the fire and the impact",
        ("cl_aviFrameRate", "cl_aviCodec", "cl_aviNoAudioHWOutput"),
        "11.3 selects the codec with cl_aviCodec; there is no "
        "cl_aviMotionJpeg in this build"),
    Capability(
        "FORCE_SELF_APPEARANCE", Evidence.UNKNOWN,
        "cg_own* and cg_self* were both probed and returned NOTHING: 11.3 "
        "registers no self-appearance family",
        (),
        "the recorder's own body cannot be forced, which is why REVIEW leaves "
        "self AUTHENTIC -- that is a property of the engine, not a choice",
        probe="a source audit of cgame's own-player model path"),
    Capability(
        "BEAUTY_PASS", Evidence.VISUALLY_PROVEN, "every capture to date", ()),
    # ── not established ────────────────────────────────────────────────
    Capability(
        "FORCE_TEAM_MODEL_SWITCH", Evidence.UNKNOWN,
        "named in the wider Quake Live ecosystem; NOT in the canonical 12.7 "
        "source; never covered by the 11.3 runtime probe",
        ("cg_forceTeamModel",),
        "do not use until proven: an unregistered cvar is accepted silently "
        "and does nothing",
        probe="cvarlist cg_force* against the running 11.3 client"),
    Capability(
        "DEPTH_CAPTURE", Evidence.UNKNOWN, "no route identified in 11.3", (),
        "a depth pass needs a renderer change or a different backend",
        probe="source audit of the capture path, or a Blender backend"),
    Capability(
        "ACTOR_ID_PASS", Evidence.UNKNOWN, "no route identified in 11.3", (),
        "object ids / Cryptomatte are why the Blender backend is planned",
        probe="Blender backend"),
    Capability(
        "PLAYER_MASK", Evidence.UNKNOWN, "no route identified in 11.3", (),
        probe="Blender backend, or an ACTOR_ID pass"),
    Capability(
        "NORMAL_PASS", Evidence.UNKNOWN, "no route identified in 11.3", (),
        probe="Blender backend"),
    Capability(
        "MOTION_PASS", Evidence.UNKNOWN, "no route identified in 11.3", (),
        probe="Blender backend"),
    Capability(
        "HIDDEN_OFFSCREEN_CONTEXT", Evidence.UNKNOWN,
        "the interactive client creates a visible window; PANTHEON_QUAKE_OFFSCREEN "
        "runs it on a separate Windows desktop instead, which is unproven here",
        (),
        "SW_SHOWMINNOACTIVE is defence in depth, NOT this capability: a "
        "minimised window is still on the user's desktop and taskbar",
        probe="engine.pantheon.offscreen.probe_isolation() with a harmless GUI process"),

    # ── from the 2026-09-06 command research, source-backed ───────────────
    # docs/reference/2026-09-06-capture-effects-command-reference.md gives the
    # file and line for each. SOURCE_REGISTERED means the handler is in the
    # canonical tree and nothing has run it here yet; that is below the bar
    # for `usable`, and deliberately so.
    Capability(
        "FREEZE_ENTITY", Evidence.SOURCE_REGISTERED,
        "entityfreeze handler in the canonical wolfcam tree (W:7055-7095)",
        (), "Holds ONE selected entity while the rest of the scene runs. "
            "Repeating the command unfreezes it. This is not a scene freeze "
            "and not a particle freeze.",
        probe="run entityfreeze on a known entity in a capture and look"),
    Capability(
        "TIME_SCALE", Evidence.SOURCE_REGISTERED,
        "timescale is registered CHEAT/SYSTEMINFO in common.c:3089",
        (), "Changes engine time, so it changes the simulation, not a "
            "finished video's rate. Demo-playback permission and what happens "
            "to audio both need proof.",
        probe="capture the same window at 1.0 and 0.5 and compare frame count"),
    Capability(
        "SHADER_REMAP", Evidence.SOURCE_REGISTERED,
        "remapshader / clearremappedshader handlers (W:7437-7476)",
        (), "Substitutes one existing shader for another; it cannot invent a "
            "material. Whether a usable wireframe or hidden-world shader "
            "exists in the QL asset set is a separate question.",
        probe="remap a known world shader and grab a frame"),
    Capability(
        "CHASE_ENTITY", Evidence.SOURCE_REGISTERED,
        "chase / view handlers (W:1024-1125)",
        (), "Follows or aims at an entity number. Entity numbers are reused, "
            "so the projectile's lifetime has to come from the trace, not "
            "from the slot.",
        probe="chase a rocket entity resolved from a real trace"),
    Capability(
        "CVAR_RAMP", Evidence.SOURCE_REGISTERED,
        "cvarinterp / clearcvarinterp handlers (W:7244-7298)",
        (), "Continuous ramp of any cvar. The default clock is game time; the "
            "`real` clock is wall time and is not deterministic for a capture.",
        probe="ramp cg_fov over a captured window and measure the frames"),
    Capability(
        "SCENE_FX", Evidence.SOURCE_REGISTERED,
        "fxload / runfx / runfxat handlers (W:6136, W:7661-7845)",
        (), "Invokes an authored FX definition. runfxat captures omitted "
            "coordinates when the command is PROCESSED, so pre-seek setup can "
            "bind the wrong origin; prefer explicit coordinates.",
        probe="load an fx library and run one at a known position"),
    Capability(
        "DEPTH_OF_FIELD", Evidence.DOCUMENTED,
        "native q3mme dof keypoints (cg_demos_dof.c:581-590); wolfcam has a "
        "similarly named imported handler that is a separate proof",
        (), "q3mme grammar, not Wolfcam's. Registering it does not mean the "
            "binary we film with can do it.",
        probe="run the q3mme build, or prove wolfcam's imported handler"),
    Capability(
        "SYNTHETIC_PERFORMANCE", Evidence.EXECUTION_PROVEN,
        "PANTHEON compiles a .dm_73 that the same extractor reads back and "
        "compare() passes on every track; the doctor does it on every run",
        (),
        "This is OUR capability, not the client's: the engine authors the "
        "demo and the client only plays it. What is unproven is whether a "
        "given authored PERFORMANCE reads as intended, which is a visual "
        "question and belongs to the proof registry.",
        probe="already measured; COMPILE / PARSE_BACK / COMPARE in the doctor",
        measured="a compiled scenario round-trips: 9,969 bytes of .dm_73, 92 "
                 "transform samples read back, PASS on 11 tracks, and the "
                 "event chain matches the source"),
    Capability(
        "POINTER_NOT_GRABBED", Evidence.EXECUTION_PROVEN,
        "measured on a real capture 2026-09-06: as shipped GetClipCursor "
        "returned the render window's rectangle for the whole run",
        ("in_nograb", "in_mouse"),
        "The operator reported the mouse boxed into the invisible window. "
        "in_nograb 1 and in_mouse 0 each released it and each still filmed; "
        "the offscreen launch sets both.",
        probe="already measured; the watcher samples GetClipCursor every run",
        measured="GetClipCursor sampled throughout three real captures: as "
                 "shipped (107,130,2027,1210) on a (0,0,3000,1440) desktop, "
                 "then unconfined with in_nograb 1, and again with in_mouse 0. "
                 "The 11.3 cvarlist capture never probed an in_* family, so "
                 "its silence about these names is not evidence."),
)}

# The offscreen backend drives the SAME binary, so it inherits every
# capability and differs only in how the process is hosted -- and in the one
# entry the hosting IS: a hardware GL context on a desktop nobody is viewing,
# which the interactive client cannot claim and this one measured.
_OFFSCREEN = dict(WOLFCAM_11_3)
_OFFSCREEN["HIDDEN_OFFSCREEN_CONTEXT"] = Capability(
    "HIDDEN_OFFSCREEN_CONTEXT", Evidence.EXECUTION_PROVEN,
    "CreateDesktopW + STARTUPINFOW.lpDesktop; the client initialised "
    "GL_RENDERER 'NVIDIA GeForce RTX 5060 Ti/PCIe/SSE2' there and filmed "
    "1920x1080 with no visible window and no stolen foreground",
    (),
    "SW_SHOWMINNOACTIVE is defence in depth, NOT this capability: a minimised "
    "window is still on the user's desktop and taskbar.",
    probe="already measured; doctor re-probes the mechanism every run")

# ── backends that do not exist yet, named honestly ────────────────────────
#
# Registering a future backend is not the same as building one. Every entry
# below is UNKNOWN and therefore not usable; what they buy is that a recipe
# can say WHICH backend would have to grow before it could be filmed, instead
# of the whole idea sitting in a chat log.

def _unknown(name: str, how: str, probe: str, note: str = "") -> Capability:
    return Capability(name, Evidence.UNKNOWN, how, (), note, probe=probe)


BLENDER: dict[str, Capability] = {c.name: c for c in (
    _unknown("CUSTOM_CHARACTER_POSE", "Blender can pose an armature; nothing "
             "here imports a QL character rig yet",
             "import one MD3 with its animation and pose it"),
    _unknown("CUSTOM_POINTING", "a presenter pointing at a named place is an "
             "authored pose, not a recorded one",
             "pose an actor pointing at a map position from MapGeography"),
    _unknown("OBJECT_ID", "per-object ids for masking",
             "render a frame with an object-index pass"),
    _unknown("CRYPTOMATTE", "coverage-accurate mattes",
             "render a cryptomatte pass and pull one actor"),
    _unknown("DEPTH", "a real depth pass, not a re-shaded approximation",
             "render Z and check it against known geometry distances"),
    _unknown("NORMAL", "a normal pass", "render normals on known geometry"),
    _unknown("WORLD_TRANSFORM", "moving the world rather than the camera",
             "transform a loaded BSP and keep the actors registered to it"),
    _unknown("WALL_REMOVAL", "deleting geometry, which no shader remap can do",
             "hide one brush group and keep the room lit"),
    _unknown("CUSTOM_GEOMETRY", "objects the game does not have",
             "place authored geometry in map coordinates"),
    _unknown("IMPOSSIBLE_CAMERA", "a camera the engine could not hold",
             "fly through a wall and keep the actors correct"),
)}

# What PANTHEON itself can do to finished frames. These are OURS, so the
# evidence ladder is about our code, not a game binary.
PANTHEON_COMPOSITOR: dict[str, Capability] = {c.name: c for c in (
    _unknown("ANALYSIS_OVERLAY", "graphics drawn over a finished frame from "
             "FrameTruth", "draw one annotated frame from a real moment"),
    _unknown("PICTURE_IN_PICTURE", "a second angle inside the frame",
             "composite two captures of the same serverTime window"),
    _unknown("MAP_DIAGRAM", "a diagram of the round from MapGeography",
             "draw one round's routes from the spatial index"),
    _unknown("HELD_FRAME", "a whole-scene hold, which entityfreeze is not",
             "hold a finished frame and ramp back into motion"),
)}

BACKENDS: dict[str, dict[str, Capability]] = {
    "WOLFCAM_REFERENCE": WOLFCAM_11_3,
    "PANTHEON_QUAKE_OFFSCREEN": _OFFSCREEN,
    "BLENDER": BLENDER,
    "PANTHEON_COMPOSITOR": PANTHEON_COMPOSITOR,
}


class CapabilityUnavailable(RuntimeError):
    def __init__(self, cap: Capability, backend: str) -> None:
        super().__init__(
            f"{backend} cannot be asked for {cap.name}: evidence is "
            f"{cap.evidence.name} ({cap.how}). {cap.note or ''} "
            f"To raise it: {cap.probe or 'no probe recorded'}".strip())
        self.capability = cap


def get(name: str, backend: str = "WOLFCAM_REFERENCE") -> Capability:
    caps = BACKENDS.get(backend)
    if caps is None:
        raise KeyError(f"unknown backend {backend!r}")
    cap = caps.get(name)
    if cap is None:
        raise KeyError(f"{backend} has no capability named {name!r}; "
                       f"known: {sorted(caps)}")
    return cap


def require(name: str, backend: str = "WOLFCAM_REFERENCE") -> Capability:
    """Use before relying on a capability. Raises rather than letting an
    unregistered cvar be written and silently ignored."""
    cap = get(name, backend)
    if not cap.usable:
        raise CapabilityUnavailable(cap, backend)
    return cap


def supports(name: str, backend: str = "WOLFCAM_REFERENCE") -> bool:
    try:
        return get(name, backend).usable
    except KeyError:
        return False


def report(backend: str = "WOLFCAM_REFERENCE") -> dict:
    caps = BACKENDS[backend]
    return {"backend": backend,
            "usable": sorted(n for n, c in caps.items() if c.usable),
            "not_established": {n: c.evidence.name for n, c in caps.items()
                                if not c.usable},
            "capabilities": {n: c.as_dict() for n, c in sorted(caps.items())}}


# ── keeping the registry tied to the runtime capture ───────────────────────

def runtime_registered_cvars(path: Path | None = None) -> set[str]:
    """Every cvar the running 11.3 client listed, from the probe capture."""
    p = path or RUNTIME_CVARLIST
    data = json.loads(p.read_text(encoding="utf-8"))
    out: set[str] = set()
    for entries in data.values():
        for e in entries:
            out.add(e["name"])
    return out


def probed_families(path: Path | None = None) -> set[str]:
    p = path or RUNTIME_CVARLIST
    return set(json.loads(p.read_text(encoding="utf-8")))
