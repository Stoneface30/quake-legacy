"""Deterministic effect timeline for the programmable fragmovie system.

A :class:`Timeline` is an ordered list of effect steps anchored to demo time
(milliseconds relative to the shot window).  Steps are pure data; the same
builder calls always produce byte-identical steps, curves, JSON and wolfcam
scripts.

Step types
----------
    slow_to       ramp demo timescale to ``rate`` over ``ramp_ms``
    freeze        cl_freezeDemo 1 for ``hold_ms`` then cl_freezeDemo 0
    resume        ramp timescale back to 1.0
    cut_to_camera hard cut to a named camera (playq3mmecamera)
    zoom          ramp fov to ``fov_to`` over ``ramp_ms``
    impact_hold   composite: slow into the impact, freeze, resume
    reverse       POST-PRODUCTION ONLY — wolfcam cannot play a demo
                  backwards, so reverse is modelled as a post step applied
                  to the captured frames; it emits no wolfcam commands.

Script emission (:func:`to_wolfcam_script`) produces ``at <servertime> ...``
timing lines. Camera PATHS are compiled to a real ``.cam10`` file via
:mod:`creative_suite.engine.cam10_writer` and executed here through the
FREECAM_SAMPLED backend (``freecam`` + one ``at <t> freecamsetpos`` per
sample) — see docs/reference/cam10_runtime_contract.md for why the
original ``camera add``/``playq3mmecamera`` emission was a silent no-op
on the engine we run (2026-09-01 camera-pipeline-recovery finding). The
native ``loadcamera``/``playcamera`` sequence also works and is the
default in :mod:`creative_suite.engine.camera_compiler_v2`; this module
stays on the sampled backend because the project's backend contract
requires keeping an independent fallback. Every token passes CS-5
validation via
:func:`creative_suite.engine.wolfcam_capture._validate_cfg_token`.

NOTE: the ``cut_to_camera`` step still emits ``playq3mmecamera <name>`` and
has NOT been runtime-verified — it is a different feature (a hard cut to a
separately-named camera mid-timeline) from the single-path compilation this
module fixes, and is flagged here rather than silently left looking
equally trustworthy.
"""
from __future__ import annotations

import json
from pathlib import Path

from creative_suite.engine import cam10_writer
from creative_suite.engine.wolfcam_capture import (SEEK_SETTLE_MS,
                                                   _validate_cfg_token)

EASINGS = ("linear", "ease_in", "ease_out", "smoothstep")

CURVE_SAMPLE_MS = 50          # ramp sampling interval for emitted curves
_TS_FMT = "{:.4f}"            # timescale value formatting (byte stable)
_FOV_FMT = "{:.2f}"           # fov value formatting
_POS_FMT = "{:.3f}"           # camera keyframe position/angle formatting


def ease(name: str, u: float) -> float:
    """Easing value for progress u in [0,1]. Deterministic pure math."""
    u = max(0.0, min(1.0, float(u)))
    if name == "linear":
        return u
    if name == "ease_in":
        return u * u
    if name == "ease_out":
        return u * (2.0 - u)
    if name == "smoothstep":
        return u * u * (3.0 - 2.0 * u)
    raise ValueError(f"unknown easing {name!r} (choose from {EASINGS})")


def _check_easing(name: str) -> str:
    if name not in EASINGS:
        raise ValueError(f"unknown easing {name!r} (choose from {EASINGS})")
    return name


def _t(t_ms) -> int:
    t = int(round(float(t_ms)))
    if t < 0:
        raise ValueError(f"t_ms must be >= 0, got {t_ms}")
    return t


class Timeline:
    """Ordered, deterministic effect step list. All builders return self."""

    def __init__(self) -> None:
        self.steps: list[dict] = []

    # ── builders ────────────────────────────────────────────────────────────

    def _add(self, step: dict) -> "Timeline":
        step["seq"] = len(self.steps)
        self.steps.append(step)
        return self

    def slow_to(self, t_ms, rate: float, ramp_ms: float = 0.0,
                easing: str = "linear") -> "Timeline":
        if not (0.0 < rate <= 10.0):
            raise ValueError(f"rate out of range (0, 10]: {rate}")
        return self._add({"type": "slow_to", "t_ms": _t(t_ms),
                          "rate": float(rate), "ramp_ms": int(round(ramp_ms)),
                          "easing": _check_easing(easing)})

    def freeze(self, t_ms, hold_ms: float) -> "Timeline":
        if hold_ms <= 0:
            raise ValueError(f"hold_ms must be > 0, got {hold_ms}")
        return self._add({"type": "freeze", "t_ms": _t(t_ms),
                          "hold_ms": int(round(hold_ms))})

    def resume(self, t_ms, ramp_ms: float = 0.0,
               easing: str = "linear") -> "Timeline":
        return self._add({"type": "resume", "t_ms": _t(t_ms),
                          "ramp_ms": int(round(ramp_ms)),
                          "easing": _check_easing(easing)})

    def cut_to_camera(self, t_ms, camera: str = "q3mme") -> "Timeline":
        return self._add({"type": "cut_to_camera", "t_ms": _t(t_ms),
                          "camera": _validate_cfg_token(str(camera))})

    def zoom(self, t_ms, fov_to: float, ramp_ms: float = 0.0,
             easing: str = "linear") -> "Timeline":
        if not (1.0 <= fov_to <= 170.0):
            raise ValueError(f"fov_to out of range [1, 170]: {fov_to}")
        return self._add({"type": "zoom", "t_ms": _t(t_ms),
                          "fov_to": float(fov_to),
                          "ramp_ms": int(round(ramp_ms)),
                          "easing": _check_easing(easing)})

    def impact_hold(self, t_ms, hold_ms: float, pre_rate: float = 0.3,
                    ramp_ms: float = 120.0,
                    easing: str = "smoothstep") -> "Timeline":
        """Slow into the impact, freeze on it, then snap back to 1.0."""
        if hold_ms <= 0:
            raise ValueError(f"hold_ms must be > 0, got {hold_ms}")
        if not (0.0 < pre_rate <= 1.0):
            raise ValueError(f"pre_rate out of range (0, 1]: {pre_rate}")
        return self._add({"type": "impact_hold", "t_ms": _t(t_ms),
                          "hold_ms": int(round(hold_ms)),
                          "pre_rate": float(pre_rate),
                          "ramp_ms": int(round(ramp_ms)),
                          "easing": _check_easing(easing)})

    def reverse(self, t_ms, duration_ms: float,
                post_production: bool = True) -> "Timeline":
        """Reverse playback of a captured window.  POST-PRODUCTION ONLY.

        wolfcam cannot play a demo backwards — a reverse can only exist as a
        post step on already-captured frames, so post_production=False is
        rejected outright.
        """
        if not post_production:
            raise ValueError(
                "reverse cannot run in-engine: wolfcam has no backwards "
                "playback — model it as a post-production step")
        if duration_ms <= 0:
            raise ValueError(f"duration_ms must be > 0, got {duration_ms}")
        return self._add({"type": "reverse", "t_ms": _t(t_ms),
                          "duration_ms": int(round(duration_ms)),
                          "post_production": True})

    # ── serialization ───────────────────────────────────────────────────────

    def to_json(self) -> str:
        """Byte-stable canonical JSON of the step list."""
        return json.dumps(self.steps, sort_keys=True,
                          separators=(",", ":"), ensure_ascii=True)

    @classmethod
    def from_json(cls, blob: str) -> "Timeline":
        tl = cls()
        tl.steps = json.loads(blob)
        return tl


# ── curves ───────────────────────────────────────────────────────────────────

def _ramp_points(t0: int, ramp_ms: int, v_from: float, v_to: float,
                 easing: str) -> list[tuple[int, float]]:
    if ramp_ms <= 0:
        return [(t0, v_to)]
    n = max(1, ramp_ms // CURVE_SAMPLE_MS)
    pts = []
    for k in range(n + 1):
        u = k / n
        t = t0 + int(round(u * ramp_ms))
        pts.append((t, v_from + (v_to - v_from) * ease(easing, u)))
    return pts


def timescale_curve(timeline: Timeline) -> list[tuple[int, float]]:
    """(t_ms, timescale) points implied by the timeline (freeze shown as 0)."""
    pts: list[tuple[int, float]] = []
    rate = 1.0
    for step in sorted(timeline.steps, key=lambda s: (s["t_ms"], s["seq"])):
        st = step["type"]
        if st == "slow_to":
            pts += _ramp_points(step["t_ms"], step["ramp_ms"], rate,
                                step["rate"], step["easing"])
            rate = step["rate"]
        elif st == "resume":
            pts += _ramp_points(step["t_ms"], step["ramp_ms"], rate, 1.0,
                                step["easing"])
            rate = 1.0
        elif st == "freeze":
            pts.append((step["t_ms"], 0.0))
            pts.append((step["t_ms"] + step["hold_ms"], rate))
        elif st == "impact_hold":
            pts += _ramp_points(step["t_ms"] - step["ramp_ms"],
                                step["ramp_ms"], rate, step["pre_rate"],
                                step["easing"])
            pts.append((step["t_ms"], 0.0))
            pts.append((step["t_ms"] + step["hold_ms"], 1.0))
            rate = 1.0
        # cut_to_camera / zoom / reverse do not affect timescale
    return pts


def fov_curve(timeline: Timeline, base_fov: float = 90.0
              ) -> list[tuple[int, float]]:
    """(t_ms, fov) points implied by zoom steps."""
    pts: list[tuple[int, float]] = []
    fov = float(base_fov)
    for step in sorted(timeline.steps, key=lambda s: (s["t_ms"], s["seq"])):
        if step["type"] == "zoom":
            pts += _ramp_points(step["t_ms"], step["ramp_ms"], fov,
                                step["fov_to"], step["easing"])
            fov = step["fov_to"]
    return pts


# ── wolfcam script emission ─────────────────────────────────────────────────

def _emit(lines: list[tuple[int, int, str]], t: int, order: int,
          text: str) -> None:
    _validate_cfg_token(text)       # CS-5: whole line, catches \n smuggling
    lines.append((t, order, text))


def to_wolfcam_script(timeline: Timeline, keyframes: list[dict],
                      base_servertime: int, gamedir: Path | None = None,
                      camera_name: str = "scene") -> str:
    """Emit a wolfcam cfg for one shot.

    If ``keyframes`` is non-empty, compiles a real ``.cam10`` archival
    file into ``<gamedir>/cameras/<camera_name>.cam10`` (``gamedir`` is
    then required) AND emits ``seekservertime`` / ``freecam`` / one
    ``at <t> freecamsetpos ...`` per keyframe — the RUNTIME-PROVEN
    execution path (docs/reference/cam10_runtime_contract.md). The
    ``loadcamera``/``playcamera`` sequence also works (proven on the
    stock binary once the file is written LF-only -- the earlier "engine
    bug" reading was our own CRLF bug, see the CORRECTED section of
    cam10_runtime_contract.md). This function stays on FREECAM_SAMPLED
    because it is the independent fallback backend the project's
    backend-contract directive requires be kept; callers wanting the
    native sequence use camera_compiler_v2.compile_dense_camera, which
    defaults to NATIVE_CAM10.

    The remaining timed ``at <servertime> ...`` commands (freeze/
    impact_hold/timescale/fov ramps) are unrelated to this fix — they
    were already real, registered commands. Post-production steps
    (reverse) emit comments only — they never reach the engine.
    """
    base = int(base_servertime)
    header = ["// auto-generated by creative_suite.engine.timeline",
              "// camera backend: {} (compiler {})".format(
                  cam10_writer.CAMERA_RUNTIME_BACKEND,
                  cam10_writer.CAMERA_COMPILER_VERSION),
              "// post-production steps below are comments, not commands"]
    cam_lines: list[str] = []
    compiled = None
    timed: list[tuple[int, int, str]] = []
    order = 0

    def at(t_ms: int, cmd: str) -> None:
        nonlocal order
        _emit(timed, base + t_ms, order, f"at {base + t_ms} {cmd}")
        order += 1

    if keyframes:
        if gamedir is None:
            raise ValueError(
                "gamedir is required to compile a .cam10 camera path")
        compiled = cam10_writer.compile_camera(
            keyframes, base, Path(gamedir), camera_name)
        seek_ms = base + int(keyframes[0]["t_ms"]) - SEEK_SETTLE_MS
        cam_lines.append(f"seekservertime {seek_ms}")
        for line in compiled["cfg_lines"]:
            if line.startswith("at "):
                # already absolute-time "at <t> <cmd...>" from cam10_writer
                _, t_str, cmd = line.split(" ", 2)
                _emit(timed, int(t_str), order, line)
                order += 1
            else:
                cam_lines.append(line)
    for line in cam_lines:
        _validate_cfg_token(line)

    post_comments: list[str] = []
    if compiled is not None:
        post_comments.append(
            "// camera file: {} (sha256 {})".format(
                compiled["path"], compiled["file_hash"]))
    for step in sorted(timeline.steps, key=lambda s: (s["t_ms"], s["seq"])):
        st = step["type"]
        # slow_to / resume timescale lines come from timescale_curve below
        if st == "freeze":
            at(step["t_ms"], "cl_freezeDemo 1")
            at(step["t_ms"] + step["hold_ms"], "cl_freezeDemo 0")
        elif st == "impact_hold":
            at(step["t_ms"], "cl_freezeDemo 1")
            at(step["t_ms"] + step["hold_ms"], "cl_freezeDemo 0")
        elif st == "cut_to_camera":
            at(step["t_ms"],
               f"playq3mmecamera {_validate_cfg_token(str(step['camera']))}")
        elif st == "reverse":
            post_comments.append(
                "// post: reverse t={}ms duration={}ms (applied to captured "
                "frames — wolfcam cannot reverse demos)".format(
                    step["t_ms"], step["duration_ms"]))

    for t, v in timescale_curve(timeline):
        if v <= 0.0:
            continue          # freezes are cl_freezeDemo, not timescale 0
        _emit(timed, base + t, order, "at {} timescale {}".format(
            base + t, _TS_FMT.format(v)))
        order += 1
    for t, v in fov_curve(timeline,
                          keyframes[0]["fov"] if keyframes else 90.0):
        _emit(timed, base + t, order, "at {} cg_fov {}".format(
            base + t, _FOV_FMT.format(v)))
        order += 1

    timed.sort(key=lambda x: (x[0], x[1]))
    out = header + cam_lines + [line for _, _, line in timed] + post_comments
    return "\n".join(out) + "\n"
