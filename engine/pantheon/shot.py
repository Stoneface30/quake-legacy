"""ShotSpec — the render contract. What to film, from where, with what on.

WHY THIS EXISTS RATHER THAN ANOTHER FFMPEG SCRIPT. Every proof so far grew its
own capture code, and each one re-derived the staging layout, the lock
protocol and the cvar set. A ShotSpec names the source, the time range, the
visual treatment and the passes; the runner turns that into the project's
EXISTING capture path (`wolfcam_capture.stage_demo` / `write_capture_cfg` /
`wolfcam_cmd`) rather than around it.

PASSES. A pass is declared as intent and graded by what the backend can
actually deliver, so a plan can ask for something the engine cannot do and be
told, rather than silently getting a duplicate of the beauty pass.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Sequence

MAIN = Path("G:/QUAKE_LEGACY")
sys.path.insert(0, str(MAIN))


class SourceKind(Enum):
    HISTORICAL = "HISTORICAL"
    RECONSTRUCTED = "RECONSTRUCTED"
    SYNTHETIC = "SYNTHETIC"


class PassKind(Enum):
    BEAUTY = "BEAUTY"
    ACTOR_XRAY = "ACTOR_XRAY"        # cg_wh silhouette through geometry
    DEPTH = "DEPTH"
    ACTOR_ID = "ACTOR_ID"
    ENEMY_MASK = "ENEMY_MASK"
    NORMAL = "NORMAL"
    MOTION = "MOTION"


# What the WolfcamQL 11.3 backend can actually deliver, graded by evidence.
# Nothing is listed PROVEN on the strength of source code: the source tree is
# 12.7test49 and the binary is 11.3.
BACKEND_SUPPORT = {
    PassKind.BEAUTY: "PROVEN",
    PassKind.ACTOR_XRAY: "PROVEN",        # cg_wh, overlay + colour on frames
    PassKind.DEPTH: "SUPPORTED_UNPROVEN",  # mme_saveDepth writes a 2nd AVI the
                                           # collector never picks up
    PassKind.ACTOR_ID: "UNSUPPORTED",      # mme_saveStencil commented out in
                                           # wolfcam; q3mme-only
    PassKind.ENEMY_MASK: "UNSUPPORTED",
    PassKind.NORMAL: "UNSUPPORTED",
    PassKind.MOTION: "UNSUPPORTED",
}


@dataclass
class VisualProfile:
    """Runtime look. Values proven on frames, not read off a wiki."""
    name: str = "PANTHEON_PRESENTER"
    xray: bool = False
    xray_enemy_color: str = "40 255 40"   # space-separated decimal RGB --
                                          # SC_ParseColorFromStr rejects hex
    xray_enemy_alpha: int = 190
    extra: dict = field(default_factory=dict)
    unpin: tuple = ()          # cvars this profile deliberately
                               # leaves to a ConfigScene variant

    def cvars(self) -> dict:
        c = {
            "cg_draw2D": 1,
            # The presenter camera is a watcher, not a combatant: a viewmodel
            # in the corner says the audience is holding a rocket launcher.
            "cg_drawGun": 0,
            # IDENTITY MUST COME FROM THE DEMO. The master capture profile
            # clears cg_enemyModel / cg_teamModel, but wolfcam ALSO archives a
            # per-part override set, and a stale q3config.cfg here still held
            # cg_enemyHeadModel "keel/bright" plus bright legs/torso/head
            # skins. That is why Crash and Keel both rendered as the same flat
            # green figure: the client was overriding the skins the demo
            # authored. Clearing the whole family is the only way the character
            # on screen is the character in the file.
            "cg_forceModel": 0,
            "cg_enemyModel": '""',
            "cg_enemyHeadModel": '""',
            "cg_enemyLegsSkin": '""',
            "cg_enemyTorsoSkin": '""',
            "cg_enemyHeadSkin": '""',
            "cg_teamModel": '""',
            "cg_teamHeadModel": '""',
            "cg_teamLegsSkin": '""',
            "cg_teamTorsoSkin": '""',
            "cg_teamHeadSkin": '""',
            "cg_drawFPS": 0,
            "cg_drawSpeed": 0,
            # names must never burn in: these are duration cvars, not booleans
            "cg_obituaryTime": 0,
            "cg_drawFragMessageTime": 0,
            "cg_drawCrosshairNames": 0,
            "cg_drawPlayerNames": 0,
            "cg_drawTeamOverlay": 0,
            "cg_scoreBoardWhenDead": 0,
            "cg_wh": 1 if self.xray else 0,
        }
        if self.xray:
            c["cg_whEnemyColor"] = f'"{self.xray_enemy_color}"'
            c["cg_whEnemyAlpha"] = self.xray_enemy_alpha
            c["cg_whColor"] = f'"{self.xray_enemy_color}"'
            c["cg_whAlpha"] = self.xray_enemy_alpha
        c.update(self.extra)
        for name in self.unpin:
            c.pop(name, None)
        return c

    def without(self, *names: str) -> "VisualProfile":
        """A copy that stops pinning `names`, so a scene can demonstrate them.

        The profile exists to hold everything still. A scene about cg_drawGun
        cannot use a profile that pins cg_drawGun, and silently letting the
        variant win would mean the constant is not constant.
        """
        return replace(self, name=f"{self.name}_nopin",
                       unpin=tuple(sorted({*self.unpin, *names})))


@dataclass
class ShotSpec:
    """One filmed range of one source."""
    shot_id: str
    source: Path
    source_kind: SourceKind
    start_s: float
    end_s: float
    visual: VisualProfile
    passes: Sequence[PassKind] = (PassKind.BEAUTY,)
    truth_reference: Path | None = None
    provenance: str = "SYNTHETIC_EXPLAINER"
    # Console commands run once the demo is seeked and before recording:
    # `follow 5`, `cg_thirdPerson 1`. Commands, not cvars -- they have no
    # place on the launch line and no cvar equivalent.
    pre_commands: tuple = ()
    # (edit_ms_from_shot_start, "command") pairs run by the engine's own `at`
    # scheduler. This is how an analysis graphic gets its own colour: the
    # rail-colour family is switched to ANALYSIS_GRAPHIC for exactly the
    # freeze window and restored after, so no historical rail before or
    # after the freeze ever wears it, and the graphic never inherits a
    # historical team/enemy colour.
    timed_commands: tuple = ()

    def unsupported_passes(self) -> list[str]:
        return [p.value for p in self.passes
                if BACKEND_SUPPORT.get(p) == "UNSUPPORTED"]

    def as_dict(self) -> dict:
        return {"shot_id": self.shot_id, "source": str(self.source),
                "source_kind": self.source_kind.value,
                "start_s": self.start_s, "end_s": self.end_s,
                "visual": self.visual.name, "xray": self.visual.xray,
                "passes": [p.value for p in self.passes],
                "pass_support": {p.value: BACKEND_SUPPORT.get(p, "UNKNOWN")
                                 for p in self.passes},
                "truth_reference": (str(self.truth_reference)
                                    if self.truth_reference else None),
                "provenance": self.provenance}


def analysis_graphic_commands(freeze_ms: int, resume_ms: int,
                              rgb=(255, 204, 64)) -> list[tuple[int, str]]:
    """Timed cvar sets that colour the analysis rail, and only it."""
    from engine.pantheon.color_format import format_for
    on = [(freeze_ms, f"set {k} {format_for(k, rgb)}")
          for k in ("cg_teamRailColor1", "cg_teamRailColor2",
                    "cg_enemyRailColor1", "cg_enemyRailColor2")]
    off = [(resume_ms, f'set {k} ""')
           for k in ("cg_teamRailColor1", "cg_teamRailColor2",
                     "cg_enemyRailColor1", "cg_enemyRailColor2")]
    return on + off




MAX_CONSOLE_LINES = 32   # qcommon/common.c -- Com_ParseCommandLine silently
                         # STOPS parsing once this many `+` groups exist, so an
                         # over-long launch line drops the trailing `+demo` and
                         # the engine boots to the menu and exits rc=0.


def render(spec: ShotSpec, out_dir: Path, *, base_ms: int = 1000) -> Path:
    """Film one ShotSpec through the project's own capture path.

    Uses `wolfcam_capture`'s staging, cfg writer and launch command rather
    than reimplementing them, so a change to the capture contract reaches this
    automatically.
    """
    from creative_suite.engine import wolfcam_capture as wc

    bad = spec.unsupported_passes()
    if bad:
        raise ValueError(f"{spec.shot_id}: backend cannot deliver {bad}")
    launched_at = time.time()

    # The capture cfg seeks to `start - SEEK_SETTLE_MS`, so a shot that begins
    # too near the head of the demo seeks to a serverTime BEFORE the first
    # snapshot and the engine sits there until the timeout. Synthetic demos
    # start at base_ms, so the shot must leave that much settle room.
    earliest = wc.SEEK_SETTLE_MS / 1000.0
    if spec.start_s < earliest:
        raise ValueError(
            f"{spec.shot_id}: starts at {spec.start_s}s but the capture seeks "
            f"{wc.SEEK_SETTLE_MS}ms earlier, which is before the demo begins. "
            f"Start at >= {earliest}s.")

    safe = wc.stage_demo(spec.source)
    windows = [{
        "clip_name": spec.shot_id,
        "start_ms": base_ms + int(spec.start_s * 1000),
        "end_ms": base_ms + int(spec.end_s * 1000),
    }]
    # The look goes in the CFG, not on the command line. Q3 parses at most
    # MAX_CONSOLE_LINES `+` groups and then stops WITHOUT a word: pushing a
    # dozen shot cvars past the master profile's fourteen pushed `+demo` off
    # the end, and the engine sat in the menu and exited 0 with no AVI. A cfg
    # exec'd from cgamepostinit has no such ceiling.
    # A LATCHED cvar set from capture.cfg does nothing to THIS capture. It is
    # stored, archived to q3config.cfg, and read at the NEXT startup -- so run
    # N films at the old value and run N+1 films at the new one. That is worse
    # than no effect: it makes consecutive captures differ by a variable nobody
    # declared, which is exactly what a controlled A/B cannot survive. (Caught
    # on PROOF B: capture 1 came out visibly darker than captures 2 and 3,
    # which had inherited the exposure the first run had only stored.)
    # Latched cvars therefore go on the command line, where Com_StartupVariable
    # applies them before the renderer initialises.
    from engine.pantheon.ab_scene import CvarInventory
    inv = CvarInventory.load()
    latched, live = {}, {}
    for k, v in spec.visual.cvars().items():
        c = inv.get(str(k))
        (latched if (c and c["latched"]) else live)[k] = v

    cfg = wc.write_capture_cfg(windows, wc.STAGING, None)
    head, *rest = cfg.splitlines()          # head is `exec <master>.cfg`
    look = [f"set {k} {v}" for k, v in live.items()]
    # pre_commands go right after the seek, so `follow` acts on the loaded
    # demo and before the first `at` fires
    seek, *timed = rest
    pre = [str(c) for c in spec.pre_commands]
    start_ms = base_ms + int(spec.start_s * 1000)
    extra_at = [f"at {start_ms + int(ms)} {cmd}" for ms, cmd in spec.timed_commands]
    wc.write_engine_file(wc.STAGING / "wolfcam-ql" / "capture.cfg",
                         "".join(f"{ln}\n" for ln in
                                 [head, *look, seek, *pre, *extra_at, *timed]))

    videos = wc.STAGING / "wolfcam-ql" / "videos"
    videos.mkdir(parents=True, exist_ok=True)
    for old in videos.glob(f"{spec.shot_id}*.avi"):
        old.unlink()

    cmd = wc.wolfcam_cmd(safe, wc.STAGING,
                         extra_sets={k: str(v).strip('"')
                                     for k, v in latched.items()})
    groups = sum(1 for a in cmd if a.startswith("+"))
    if groups > MAX_CONSOLE_LINES:
        raise RuntimeError(
            f"{spec.shot_id}: launch line has {groups} `+` groups, over the "
            f"engine's {MAX_CONSOLE_LINES}; the trailing +demo would be "
            f"dropped silently. Move cvars into capture.cfg.")
    span = spec.end_s - spec.start_s
    # Measured: a 15s synthetic demo took 297s against a 280s budget. The
    # engine renders every frame at 60fps for AVI, so ~20x realtime is the
    # honest rate, plus the seek.
    timeout = 240 + span * 22 + spec.start_s * 2
    t0 = time.time()
    # SDL's default video driver probe fails on this machine ("No available
    # video device"), and wolfcam answers by reverting to SAFE VALUES -- which
    # silently drops r_mode -1 / 1920x1080 down to mode 11, 856x480. Naming the
    # driver makes the first attempt succeed, so the shot is filmed at the
    # resolution it asked for instead of a quarter of it.
    env = dict(os.environ, SDL_VIDEODRIVER="windib")
    from engine.pantheon import render_permit
    render_permit.require(f"reference_render:{spec.shot_id}")
    proc = subprocess.Popen(cmd, cwd=wc.STAGING, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        rc = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.terminate()                      # CS-4: never orphan a GUI proc
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        rc = "TIMEOUT"
    elapsed = round(time.time() - t0, 1)

    made = sorted(videos.glob(f"{spec.shot_id}*.avi"))
    if not made:
        raise RuntimeError(f"{spec.shot_id}: no AVI produced (rc={rc}, "
                           f"{elapsed}s)")
    # RENDER-JOB VALIDATION. A stale artefact from an earlier run once passed
    # for a fresh one because nobody checked. Every claim below is verified
    # against THIS launch: the file is newer than the launch, the engine
    # exited cleanly, and it probes to the duration that was asked for.
    if made[0].stat().st_mtime < launched_at:
        raise RuntimeError(f"{spec.shot_id}: STALE_ARTIFACT -- {made[0].name} "
                           f"predates this launch")
    if rc != 0 and rc != "TIMEOUT":
        raise RuntimeError(f"{spec.shot_id}: engine exit {rc}")
    # A TIMEOUT after `stopvideo` leaves a complete AVI; the duration probe
    # below is what decides whether the capture finished, not the exit.
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{spec.shot_id}.avi"
    shutil.move(str(made[0]), dest)
    want = spec.end_s - spec.start_s
    got = _probe(dest, spec, elapsed, rc).get("duration_s")
    if got is None or abs(float(got) - want) > 0.2:
        raise RuntimeError(f"{spec.shot_id}: DURATION_MISMATCH -- asked "
                           f"{want:.2f}s, probed {got}s")

    # THE PASS CONTRACT. Accepting a pass enum is not producing its artifact.
    # The collector enumerates the beauty AVI and nothing else, so any other
    # requested pass is PASS_NOT_PRODUCED -- explicitly, not by handing back
    # the beauty file under another name. Every produced pass is probed.
    manifest = {"BEAUTY": _probe(dest, spec, elapsed, rc)}
    missing = [p.value for p in spec.passes if p is not PassKind.BEAUTY]
    if missing:
        raise RuntimeError(
            f"PASS_NOT_PRODUCED {spec.shot_id}: {missing} requested; the "
            f"backend collector only produces BEAUTY. Manifest: {manifest}")
    spec.manifest = manifest
    return dest


def _probe(avi: Path, spec: "ShotSpec", elapsed: float, rc=0) -> dict:
    """What was actually produced, measured, not assumed."""
    out = subprocess.run(
        [str(Path(MAIN, "creative_suite/tools/ffmpeg/ffprobe.exe")), "-v", "error",
         "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate,nb_frames,duration",
         "-of", "json", str(avi)], capture_output=True, text=True).stdout
    import json as _json
    st = (_json.loads(out).get("streams") or [{}])[0] if out else {}
    return {"pass": "BEAUTY", "file": str(avi),
            "width": st.get("width"), "height": st.get("height"),
            "fps": st.get("r_frame_rate"), "frames": st.get("nb_frames"),
            "duration_s": st.get("duration"),
            "requested_s": round(spec.end_s - spec.start_s, 3),
            "backend": "wolfcamql-11.3", "elapsed_s": elapsed,
            "engine_exit": rc,
            "source": str(spec.source), "source_kind": spec.source_kind.value,
            "profile": spec.visual.name, "provenance": spec.provenance,
            "artifact_mtime": avi.stat().st_mtime,
            "settings": spec.visual.cvars()}
