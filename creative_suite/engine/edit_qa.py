"""Bad-edit warnings (directive 12): three explainable checks, no oracle.

Each check answers one question a reviewer would ask, in a form that says
WHY it fired and in what span, so the result can be argued with. None of
them judges taste; together they catch the three ways a cinematic segment
goes wrong mechanically.

    CINEMATIC_HUD_VISIBLE      ERROR  a non-FPV segment captured with HUD
    CINEMATIC_NO_SUBJECT       WARN   >250 ms of camera with nothing to look at
    POST_DEATH_CAMERA_TOO_LONG WARN   >350 ms after the subject is gone

Thresholds are initial editorial values and are recorded on every finding
so a later change to them is visible in old reports.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from creative_suite.engine import presentation

ERROR = "ERROR"
WARN = "WARN"

CINEMATIC_HUD_VISIBLE = "CINEMATIC_HUD_VISIBLE"
CINEMATIC_NO_SUBJECT = "CINEMATIC_NO_SUBJECT"
POST_DEATH_CAMERA_TOO_LONG = "POST_DEATH_CAMERA_TOO_LONG"
UNINTENDED_POST_SLOW_SPEEDUP = "UNINTENDED_POST_SLOW_SPEEDUP"

NO_SUBJECT_MAX_MS = 250.0
POST_DEATH_MAX_MS = 350.0


@dataclass(frozen=True)
class Finding:
    check: str
    severity: str
    start_ms: float
    end_ms: float
    reason: str
    threshold_ms: float | None = None

    @property
    def span_ms(self) -> float:
        return round(self.end_ms - self.start_ms, 1)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["span_ms"] = self.span_ms
        return d


def check_hud(camera_mode: str, profile: str, *,
              frame_hud_detected: bool | None = None) -> list[Finding]:
    """ERROR when a cinematic camera would render, or did render, HUD.

    Two sources of truth, both consulted: the profile the segment was
    captured with (config level) and, when available, what a frame
    inspection actually saw (``frame_hud_detected``). Config alone is not
    enough -- that is the whole lesson of the cvar-leak canary -- but it is
    the check that can run before an engine is launched.
    """
    out: list[Finding] = []
    if presentation.presentation_for(camera_mode) != presentation.CINEMATIC_CLEAN:
        return out
    if presentation.profile_draws_hud(profile):
        out.append(Finding(CINEMATIC_HUD_VISIBLE, ERROR, 0.0, 0.0,
                           f"{camera_mode} segment captured with {profile}, "
                           f"which draws the 2D layer"))
    if frame_hud_detected:
        out.append(Finding(CINEMATIC_HUD_VISIBLE, ERROR, 0.0, 0.0,
                           f"frame inspection found HUD in a {camera_mode} "
                           f"segment (profile {profile})"))
    return out


def check_no_subject(segment_start_ms: float, segment_end_ms: float,
                     subject_spans_ms: list[tuple[float, float]], *,
                     max_gap_ms: float = NO_SUBJECT_MAX_MS) -> list[Finding]:
    """WARN for any stretch of a cinematic segment with no subject on screen.

    ``subject_spans_ms`` are the intervals in which SOMETHING earns the
    camera: a player, a projectile, or geometry the shot is deliberately
    revealing. Gaps between them longer than ``max_gap_ms`` are reported
    with their exact extent.
    """
    out: list[Finding] = []
    cursor = float(segment_start_ms)
    for a, b in sorted(subject_spans_ms):
        a, b = float(a), float(b)
        if a - cursor > max_gap_ms:
            out.append(Finding(CINEMATIC_NO_SUBJECT, WARN, cursor, a,
                               "camera has no player, projectile or "
                               "revealed geometry to justify it",
                               max_gap_ms))
        cursor = max(cursor, b)
    if float(segment_end_ms) - cursor > max_gap_ms:
        out.append(Finding(CINEMATIC_NO_SUBJECT, WARN, cursor,
                           float(segment_end_ms),
                           "camera continues after the last subject",
                           max_gap_ms))
    return out


def check_post_death(subject_end_ms: float, segment_end_ms: float, *,
                     continuation_at_ms: float | None = None,
                     max_ms: float = POST_DEATH_MAX_MS) -> list[Finding]:
    """WARN when the camera outlives its subject without a reason.

    ``continuation_at_ms`` is the moment a transition or a new subject
    takes over, if one does. Without it, anything longer than ``max_ms``
    past the subject's end is the corpse camera the directive forbids.
    """
    stop = (float(segment_end_ms) if continuation_at_ms is None
            else min(float(segment_end_ms), float(continuation_at_ms)))
    tail = stop - float(subject_end_ms)
    if tail > max_ms:
        return [Finding(POST_DEATH_CAMERA_TOO_LONG, WARN,
                        float(subject_end_ms), stop,
                        "camera runs past the subject with no continuation "
                        "or transition", max_ms)]
    return []


def summarize(findings: list[Finding]) -> dict[str, Any]:
    return {
        "errors": [f.to_dict() for f in findings if f.severity == ERROR],
        "warnings": [f.to_dict() for f in findings if f.severity == WARN],
        "passes": not any(f.severity == ERROR for f in findings),
    }


# ── no temporal debt (directive V3E 4-6) ────────────────────────────────────
# SLOW MOTION NEVER CREATES TEMPORAL DEBT. A gameplay interval D shown at
# rate R < 1 occupies D / R of edit time and the movie gets longer. Nothing
# afterwards may run faster than 1.0x to "repay" it unless the editor
# authored that speed-up explicitly. This is the check that would have
# caught it, and it is an ERROR for the editorial canaries.

def check_temporal_debt(pieces: list[dict], *,
                        authored_speedups: set | None = None) -> list[Finding]:
    """ERROR for any implicit rate > 1.0 after a slow piece, or for a piece
    whose output duration is shorter than its source span would allow.

    ``pieces`` are the assembly's own piecewise TimeMap: dicts with
    ``label``, ``src_in_s``, ``src_out_s``, ``rate`` and, when measured,
    ``out_duration_s``. ``authored_speedups`` names pieces whose rate > 1
    was requested on purpose.
    """
    out: list[Finding] = []
    authored = set(authored_speedups or ())
    seen_slow = False
    for pc in pieces:
        rate = float(pc["rate"])
        span = float(pc["src_out_s"]) - float(pc["src_in_s"])
        expected = span / rate if rate > 0 else 0.0
        if rate < 1.0:
            seen_slow = True
        if rate > 1.0 + 1e-9 and pc.get("label") not in authored:
            out.append(Finding(
                UNINTENDED_POST_SLOW_SPEEDUP if seen_slow else UNINTENDED_POST_SLOW_SPEEDUP,
                ERROR, float(pc["src_in_s"]) * 1000.0, float(pc["src_out_s"]) * 1000.0,
                f"{pc.get('label', '?')} runs at {rate:.3f}x without an authored "
                f"speed-up" + (" -- repaying slow-motion time" if seen_slow else ""),
                1.0))
        measured = pc.get("out_duration_s")
        if measured is not None and expected > 0:
            # more than one frame short at 60 fps is compression, not rounding
            if float(measured) < expected - (1.5 / 60.0):
                out.append(Finding(
                    UNINTENDED_POST_SLOW_SPEEDUP, ERROR,
                    float(pc["src_in_s"]) * 1000.0, float(pc["src_out_s"]) * 1000.0,
                    f"{pc.get('label', '?')} delivered {float(measured):.3f}s for "
                    f"{span:.3f}s of source at {rate:.3f}x (expected "
                    f"{expected:.3f}s): source footage was compressed",
                    1.0))
    return out
