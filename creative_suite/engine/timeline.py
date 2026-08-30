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
lines plus ``camera add`` keyframe lines; every token passes CS-5 validation
via :func:`creative_suite.engine.wolfcam_capture._validate_cfg_token`.
"""
from __future__ import annotations

import json

from creative_suite.engine.wolfcam_capture import _validate_cfg_token

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
                      base_servertime: int) -> str:
    """Emit a wolfcam cfg for one shot.

    ``camera add`` lines carry the keyframe path (servertime pos angles fov),
    followed by the timed ``at <servertime> ...`` command stream sorted by
    servertime (stable on emission order for ties).  Post-production steps
    (reverse) emit comments only — they never reach the engine.
    """
    base = int(base_servertime)
    header = ["// auto-generated by creative_suite.engine.timeline",
              "// post-production steps below are comments, not commands"]
    cam_lines: list[str] = []
    for kf in keyframes:
        p = kf["pos"]
        a = kf["angles"]
        cam_lines.append(
            "camera add {} {} {} {} {} {} {} {}".format(
                base + int(kf["t_ms"]),
                _POS_FMT.format(p[0]), _POS_FMT.format(p[1]),
                _POS_FMT.format(p[2]),
                _POS_FMT.format(a[0]), _POS_FMT.format(a[1]),
                _POS_FMT.format(a[2]),
                _FOV_FMT.format(kf["fov"])))
    for line in cam_lines:
        _validate_cfg_token(line)

    timed: list[tuple[int, int, str]] = []
    order = 0

    def at(t_ms: int, cmd: str) -> None:
        nonlocal order
        _emit(timed, base + t_ms, order, f"at {base + t_ms} {cmd}")
        order += 1

    if keyframes:
        at(int(keyframes[0]["t_ms"]), "playq3mmecamera")

    post_comments: list[str] = []
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
