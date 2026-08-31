"""Event-localized speed effects (Rules P1-Q / P1-E).

CLAUDE.md has cited this module as the `WHERE` for P1-Q and P1-E since those
rules were written, but the file never existed and `render_part_v6.py` never
called it. Every Part therefore shipped with clips butted end to end -- no
slow-mo, no speed ramp, no zoom. This implements it.

Design (user direction, 2026-08-28):
  - SLOW the frag around its action peak; SPEED UP the dead time before it.
  - Never time-stretch the music -- the video bends to the beat grid, so the
    music keeps its original pitch and tempo.

A frag becomes three sub-segments in one ffmpeg pass:

    [0 .. peak-pre]        speed-up   (approach / dead time)
    [peak-pre .. peak+post] slow-mo   (the money shot)
    [peak+post .. end]      normal    (settle)

`setpts=PTS/rate` -- rate > 1 is faster, rate < 1 is slower. Audio follows with
`atempo` so game sound stays locked to picture (ffmpeg's atempo accepts
0.5..100, which bounds how slow a single stage can go).
"""
from __future__ import annotations

from dataclasses import dataclass


# Rule P1-Q defaults.
SLOW_RATE = 0.45          # money-shot playback rate
SPEEDUP_RATE = 1.75       # dead-time compression
SLOW_PRE_S = 0.70         # slow window opens this far before the peak
SLOW_POST_S = 0.90        # ...and closes this far after
MIN_SPEEDUP_SRC_S = 0.60  # below this there is no dead time worth compressing
ATEMPO_MIN = 0.5          # ffmpeg atempo lower bound

# How far the slow rate may be pushed to make a cut land on the music. The
# user asked for a RANGE rather than one fixed rate: "we are allowed here to
# change the strength of the slowmo to match ... like 30% / 60%".
#
# 0.30 is about as slow as this footage takes before motion interpolation
# starts inventing visible artefacts (30 fps source held ~6.7 output frames);
# 0.62 is barely slower than real time and stops reading as an accent at all.
# Inside that band the strength is free, so the segment can be stretched or
# tightened until its END lands on a beat.
SLOW_RATE_MIN = 0.30
SLOW_RATE_MAX = 0.62

# The source captures are 30 fps and the reel is 60 fps, so a 0.45x slow window
# holds each source frame for ~4.4 output frames -- visible judder, which is what
# the user meant by "slowmo are not smooth". setpts alone only restamps existing
# frames; it cannot invent the intermediate ones. minterpolate synthesises them
# with motion compensation. It is expensive, so it is applied ONLY to the slow
# stage, which is a couple of seconds per accented frag.
SMOOTH_SLOWMO = True
MINTERP = ("minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:"
           "me_mode=bidir:vsbmc=1")


@dataclass(frozen=True)
class SpeedPlan:
    """A three-stage speed ramp over one source clip."""
    src_start: float
    peak_t: float
    src_end: float
    slow_rate: float = SLOW_RATE
    speedup_rate: float = SPEEDUP_RATE

    @property
    def a(self) -> float:
        """End of the sped-up approach (== start of the slow window)."""
        return max(self.src_start, self.peak_t - SLOW_PRE_S)

    @property
    def b(self) -> float:
        """End of the slow window."""
        return min(self.src_end, self.peak_t + SLOW_POST_S)

    @property
    def has_speedup(self) -> bool:
        return (self.a - self.src_start) >= MIN_SPEEDUP_SRC_S

    @property
    def has_tail(self) -> bool:
        return (self.src_end - self.b) > 0.05

    def output_duration(self) -> float:
        """Playback seconds this plan produces."""
        d = 0.0
        if self.has_speedup:
            d += (self.a - self.src_start) / self.speedup_rate
        d += max(0.0, self.b - self.a) / self.slow_rate
        if self.has_tail:
            d += self.src_end - self.b
        return d

    def with_speedup(self, rate: float) -> "SpeedPlan":
        return SpeedPlan(self.src_start, self.peak_t, self.src_end,
                         self.slow_rate, rate)

    def with_slow_rate(self, rate: float) -> "SpeedPlan":
        return SpeedPlan(self.src_start, self.peak_t, self.src_end,
                         rate, self.speedup_rate)

    def rate_for_output(self, target_out_s: float) -> float | None:
        """The slow rate that would make this plan last `target_out_s`.

        Everything except the slow window is fixed, so the window absorbs the
        difference:

            target = speedup_part + (b - a) / rate + tail
            rate   = (b - a) / (target - speedup_part - tail)

        Returns None when the target cannot be reached at any rate.
        """
        fixed = 0.0
        if self.has_speedup:
            fixed += (self.a - self.src_start) / self.speedup_rate
        if self.has_tail:
            fixed += self.src_end - self.b
        window = max(0.0, self.b - self.a)
        room = target_out_s - fixed
        if window <= 1e-3 or room <= 1e-3:
            return None
        return window / room


def _atempo_chain(rate: float) -> str:
    """atempo only accepts 0.5..100 per stage; chain for anything lower."""
    if rate >= ATEMPO_MIN:
        return f"atempo={rate:.4f}"
    stages, r = [], rate
    while r < ATEMPO_MIN:
        stages.append(ATEMPO_MIN)
        r /= ATEMPO_MIN
    stages.append(max(r, ATEMPO_MIN))
    return ",".join(f"atempo={s:.4f}" for s in stages)


def build_filter(plan: SpeedPlan, *, vin: str = "0:v", ain: str | None = "0:a",
                 vout: str = "vout", aout: str = "aout",
                 out_fps: int = 60) -> str:
    """Return an ffmpeg filter_complex implementing `plan`.

    Emits [vout] always and [aout] when `ain` is given.
    """
    vparts: list[str] = []
    aparts: list[str] = []
    vlabels: list[str] = []
    alabels: list[str] = []
    n = 0

    def stage(t0: float, t1: float, rate: float) -> None:
        nonlocal n
        if t1 - t0 <= 0.01:
            return
        vl = f"sv{n}"
        chain = f"trim={t0:.4f}:{t1:.4f},setpts=(PTS-STARTPTS)/{rate:.6f}"
        if SMOOTH_SLOWMO and rate < 1.0:
            # Motion-compensated interpolation, slow stage only.
            chain += "," + MINTERP.format(fps=out_fps)
        vparts.append(f"[{vin}]{chain}[{vl}]")
        vlabels.append(f"[{vl}]")
        if ain:
            al = f"sa{n}"
            aparts.append(
                f"[{ain}]atrim={t0:.4f}:{t1:.4f},asetpts=PTS-STARTPTS,"
                f"{_atempo_chain(rate)}[{al}]"
            )
            alabels.append(f"[{al}]")
        n += 1

    if plan.has_speedup:
        stage(plan.src_start, plan.a, plan.speedup_rate)
    stage(plan.a, plan.b, plan.slow_rate)
    if plan.has_tail:
        stage(plan.b, plan.src_end, 1.0)

    chain = ";".join(vparts)
    chain += f";{''.join(vlabels)}concat=n={len(vlabels)}:v=1:a=0[{vout}]"
    if ain and alabels:
        chain += ";" + ";".join(aparts)
        chain += f";{''.join(alabels)}concat=n={len(alabels)}:v=0:a=1[{aout}]"
    return chain


def fit_to_duration(plan: SpeedPlan, target_s: float,
                    max_speedup: float = 3.2,
                    min_speedup: float = 1.0) -> SpeedPlan:
    """Bend the dead-time speed-up so the frag lands on `target_s`.

    The slow window is never touched -- the money shot keeps its chosen rate.
    Only the approach is compressed or relaxed, which is what makes a frag land
    on a beat without altering the music.
    """
    if not plan.has_speedup or target_s <= 0:
        return plan
    fixed = 0.0
    fixed += max(0.0, plan.b - plan.a) / plan.slow_rate
    if plan.has_tail:
        fixed += plan.src_end - plan.b
    approach_src = plan.a - plan.src_start
    remaining = target_s - fixed
    if remaining <= 0.05:
        return plan.with_speedup(max_speedup)
    rate = approach_src / remaining
    return plan.with_speedup(max(min_speedup, min(max_speedup, rate)))


def snap_to_beat(t: float, beats: list[float], *,
                 min_gap: float = 0.0) -> float:
    """Nearest beat at or after `t + min_gap`; falls back to `t`."""
    if not beats:
        return t
    floor = t + min_gap
    later = [b for b in beats if b >= floor]
    return later[0] if later else t


def _pick_landing(rate_for, natural_end, timeline_t, beats,
                  downbeats=None, drops=None,
                  lo: float = SLOW_RATE_MIN, hi: float = SLOW_RATE_MAX,
                  allowed_kinds=("drop", "downbeat", "beat")):
    """Choose the musical moment this segment should END on.

    `rate_for(target_out_s)` returns the slow rate needed to make the segment
    last that long, or None if it is unreachable. Landing points are preferred
    in the order a listener notices them -- a drop, then a downbeat, then any
    beat -- and a candidate is only accepted when the rate it needs falls
    inside the allowed strength band. Among equally strong landings the one
    closest to where the shot would naturally have ended wins, so the picture
    is disturbed as little as possible.

    Returns (rate, landing_time, kind) or None.
    """
    if not beats:
        return None
    drops = set(round(x, 2) for x in (drops or []))
    downs = set(round(x, 2) for x in (downbeats or []))

    best = None
    for b in beats:
        if b <= timeline_t + 0.5:
            continue
        r = rate_for(b - timeline_t)
        if r is None or not (lo <= r <= hi):
            continue
        rb = round(b, 2)
        kind = "drop" if rb in drops else ("downbeat" if rb in downs else "beat")
        if kind not in allowed_kinds:
            continue
        rank = {"drop": 0, "downbeat": 1, "beat": 2}[kind]
        cost = (rank, abs(b - natural_end))
        if best is None or cost < best[0]:
            best = (cost, r, b, kind)
    if best is None:
        return None
    return best[1], best[2], best[3]


def accent_rate_for_landing(w0: float, a: float, b: float, w1: float,
                            timeline_t: float, beats, downbeats=None,
                            drops=None, default_rate: float = SLOW_RATE,
                            lo: float = SLOW_RATE_MIN,
                            hi: float = SLOW_RATE_MAX,
                            allowed_kinds=("drop", "downbeat", "beat")):
    """Beat-lock an accent expressed as literal segment boundaries.

    The renderer builds its accent as three concatenated pieces -- w0->a at
    natural speed, a->b slowed, b->w1 at natural speed -- so the duration model
    here is that form exactly, rather than a SpeedPlan's (which carries a
    speed-up stage the renderer deliberately does not have, and a different
    post-peak window). Modelling it any other way predicts a length the render
    will not produce, and the segment lands off the grid it was solved for.

        out(rate) = (a - w0) + (b - a) / rate + (w1 - b)

    Returns (rate, landing_time, kind) or None.
    """
    window = max(0.0, b - a)
    fixed = max(0.0, a - w0) + max(0.0, w1 - b)
    if window <= 1e-3:
        return None

    def rate_for(target):
        room = target - fixed
        if room <= 1e-3:
            return None
        return window / room

    natural_end = timeline_t + fixed + window / default_rate
    return _pick_landing(rate_for, natural_end, timeline_t, beats,
                         downbeats, drops, lo, hi, allowed_kinds)


def beat_locked_slow_rate(plan: "SpeedPlan", timeline_t: float, beats,
                          downbeats=None, drops=None,
                          lo: float = SLOW_RATE_MIN,
                          hi: float = SLOW_RATE_MAX):
    """Pick the slow-mo strength that makes this SpeedPlan END on the music.

    A fixed 0.45x accent ends wherever it happens to end, so the cut after a
    slow-motion moment lands off the grid and the edit stops agreeing with the
    track. Because the slow window is the only elastic part of the plan, the
    rate can be solved for instead of assumed: choose the musical landing point
    first, then set the strength that reaches it. If nothing fits the allowed
    strength band, None is returned and the caller keeps the default rate
    rather than distorting the shot to chase the grid.

    Returns (rate, landing_time, kind) or None.
    """
    return _pick_landing(plan.rate_for_output,
                         timeline_t + plan.output_duration(),
                         timeline_t, beats, downbeats, drops, lo, hi)
