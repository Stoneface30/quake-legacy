"""Edge-guarded action-peak detection.

`audio_onsets.find_action_peak()` returns the loudest onset in a clip. On this
corpus the loudest onset is very often the clip's OWN edge: the hard cut in and
out of a wolfcam capture produces a bigger transient than any weapon. Measured
across Part 4 T1 frags:

    Demo (104) - 8      8.00 s  -> peak 0.02 s   (0%)   first frame
    Demo (288) - 318    6.00 s  -> peak 0.02 s   (0%)   first frame
    Demo (875) - 1112  18.00 s  -> peak 17.59 s (98%)   last frame
    Demo (625) - 780   20.00 s  -> peak 19.29 s (96%)   last frame

Centring an edit window on those values cuts the actual frag out of the clip,
which is exactly what the user reported: "all the frag are skipped", "the cuts
are from the end of clips that need to be cut off", and POV/third-person angles
that read as different frags because each landed on a different bogus moment.

Two guards:

  HEAD  The Quake console is drawn over the first moment of every capture (user,
        2026-08-28: "no console it always show"). Rule P1-L already trims 1.0 s
        off FL clips for this; here it applies to every clip, and the peak
        search additionally never looks inside it.

  TAIL  A capture runs past the kill into round-end fanfare and angle falloff
        (P1-L trims 2.0 s off FL for this). The search excludes that region so a
        round-end sting can't masquerade as the frag.
"""
from __future__ import annotations

import numpy as np

# Console overlay + cut-in transient.
HEAD_GUARD_S = 1.20
# Round-end fanfare, angle falloff, cut-out transient.
TAIL_GUARD_S = 1.80
# Guards may never eat more than this share of a clip, or short frags would
# have no searchable interior left.
MAX_GUARD_FRACTION = 0.60
# Where to place the peak when there is nothing to measure.
FALLBACK_FRACTION = 0.62


def guard_bounds(duration: float) -> tuple[float, float]:
    """Return the (lo, hi) search window for a clip of `duration` seconds."""
    if duration <= 0:
        return (0.0, 0.0)
    head, tail = HEAD_GUARD_S, TAIL_GUARD_S
    budget = duration * MAX_GUARD_FRACTION
    if head + tail > budget:                 # short clip: shrink proportionally
        scale = budget / (head + tail)
        head, tail = head * scale, tail * scale
    lo = min(head, duration)
    hi = max(lo, duration - tail)
    return (lo, hi)


def peak_from_envelope(envelope: np.ndarray, duration: float) -> float:
    """Time of the strongest point of `envelope`, ignoring the guarded edges.

    `envelope` is any per-frame loudness/onset series spanning the whole clip.
    """
    n = int(getattr(envelope, "size", 0) or 0)
    if n == 0 or duration <= 0:
        return duration * FALLBACK_FRACTION

    lo, hi = guard_bounds(duration)
    i_lo = max(0, min(n - 1, int(round(lo / duration * n))))
    i_hi = max(i_lo + 1, min(n, int(round(hi / duration * n))))

    window = envelope[i_lo:i_hi]
    if window.size == 0:
        return duration * FALLBACK_FRACTION
    idx = i_lo + int(np.argmax(window))
    return float(idx) / n * duration


def clamp_peak(peak: float | None, duration: float) -> float:
    """Force any externally-supplied peak into the guarded region.

    Used to sanitise `audio_onsets.find_action_peak()` output rather than
    replacing it -- when it is right it is useful, and when it lands on an edge
    this pulls it back inside.
    """
    if duration <= 0:
        return 0.0
    lo, hi = guard_bounds(duration)
    if peak is None:
        return duration * FALLBACK_FRACTION
    return float(min(max(float(peak), lo), hi))


def find_peak_guarded(clip_path, duration: float) -> float:
    """Best action moment inside the guarded region of `clip_path`.

    Prefers a real search of the loudness envelope restricted to the guarded
    interior. Clamping alone is not enough: a raw peak of 0.02 s clamps to the
    guard boundary (1.20 s), which is still not where the frag is. Falls back to
    clamping the plain detector, then to a fixed fraction.
    """
    try:
        from creative_suite.engine.audio_onsets import _compute_envelope

        env = _compute_envelope(clip_path)
        if env is not None and getattr(env, "size", 0):
            return peak_from_envelope(env, duration)
    except Exception:
        pass

    try:
        from creative_suite.engine.audio_onsets import find_action_peak

        return clamp_peak(find_action_peak(clip_path), duration)
    except Exception:
        return duration * FALLBACK_FRACTION


# Approach context before the first shot and settle after the last.
SPAN_LEAD_PAD_S = 1.6
SPAN_TAIL_PAD_S = 1.0


def find_action_span(clip_path, duration: float,
                     rel_threshold: float = 0.20,
                     max_len: float | None = None) -> tuple[float, float]:
    """Span covering EVERY significant action in a clip, not just the loudest.

    A capture often contains a multi-kill: several frags seconds apart. Centring
    a fixed window on the single loudest onset shows one of them and cuts the
    rest, which is what the user reported ("it only show 1 frag on scene with
    multiple frags").

    It also caused the POV/third-person mismatch: FP and FL of the same frag have
    DIFFERENT durations (measured: 4.00 vs 6.30 s; 7.00 vs 4.27 vs 8.90 s), so
    they are not time-aligned. Peak-picking each independently landed them on
    different kills of the same fight. Spanning all action in both makes them
    show the same fight regardless of offset.

    Returns (start, end) inside the guarded region.
    """
    lo, hi = guard_bounds(duration)
    try:
        from creative_suite.engine.audio_onsets import _compute_envelope

        env = _compute_envelope(clip_path)
    except Exception:
        env = None

    if env is None or getattr(env, "size", 0) == 0:
        return (lo, hi)

    n = env.size
    i_lo = max(0, min(n - 1, int(round(lo / duration * n))))
    i_hi = max(i_lo + 1, min(n, int(round(hi / duration * n))))
    window = env[i_lo:i_hi]
    if window.size == 0:
        return (lo, hi)

    peak = float(np.max(window))
    floor = float(np.median(window))
    if peak <= floor:
        return (lo, hi)

    # Every sample that stands well clear of the clip's own noise floor.
    thresh = floor + (peak - floor) * rel_threshold
    hits = np.flatnonzero(window >= thresh)
    if hits.size == 0:
        return (lo, hi)

    first = (i_lo + int(hits[0])) / n * duration
    last = (i_lo + int(hits[-1])) / n * duration
    # A kill needs approach context and a moment to settle.
    first = max(lo, first - SPAN_LEAD_PAD_S)
    last = min(hi, max(last + SPAN_TAIL_PAD_S, first + 1.0))

    if max_len is not None and (last - first) > max_len:
        # The span ran long -- on a busy capture the onsets can cover almost the
        # whole clip. The action is NEVER sped up (user 2026-08-29: "the frags
        # should NEVER be sped up"), so it must be TRIMMED instead: slide a
        # window of max_len and keep the one carrying the most onset energy.
        w = max(1, int(round(max_len / duration * n)))
        i_a = max(0, min(n - 1, int(round(first / duration * n))))
        i_b = max(i_a + 1, min(n, int(round(last / duration * n))))
        seg = env[i_a:i_b]
        if seg.size > w:
            csum = np.concatenate(([0.0], np.cumsum(seg)))
            sums = csum[w:] - csum[:-w]
            best = int(np.argmax(sums))
            first = (i_a + best) / n * duration
            last = first + max_len
        else:
            last = first + max_len
        first, last = max(lo, first), min(hi, last)

    return (first, last)


def is_edge_artifact(peak: float | None, duration: float) -> bool:
    """True if `peak` fell in a guarded edge, i.e. it is not a real frag moment."""
    if peak is None or duration <= 0:
        return True
    lo, hi = guard_bounds(duration)
    return not (lo <= float(peak) <= hi)
