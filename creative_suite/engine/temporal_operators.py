"""Effects are time. Every choreography element is an edit-time operator.

THE CORRECTION. A freeze is not an annotation at timestamp X -- it IS 300 ms
of the song. A replay is not a camera tag -- it inserts its own duration. A
stutter is not three markers -- its dwell and count decide how long the shot
lasts. A transition overlap does not add time, it REMOVES net time. Once a
song is chosen the music is an immutable ruler, and these operators are the
variables that let a 2.9 s moment become an excellent 5.85 s sequence that
lands on the ruler exactly.

THE EQUATION.

    final = Σ retimed source spans
          + freezes + replay insertions + repeats + synthetic inserts + holds
          - trims - transition overlaps

    subject to   final == score slot duration    (exactly, on the quantum)

SYNC IS A PROPERTY OF THE FINISHED CHOREOGRAPHY. Not of the raw frag, not of
the scene before effects. Anything inserted before the hero moves it, so the
hero's alignment can only be measured after every operator is resolved.
`ComposedTimeMap` is what makes that measurable, and it refuses to be read
until the plan is complete.

SOURCE TRUTH DOES NOT MOVE. demo_us stays exactly what the demo recorded.
What these operators change is how source time maps into final edit time.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field, replace
from fractions import Fraction
import hashlib
import json
from typing import Any, Iterable, Sequence

TEMPORAL_VERSION = "temporal-operators-v1.0.0"

# The edit grid. Durations are exact multiples of this, so "exactly the score
# slot" is a statement that can be checked rather than approached.
QUANTUM_US = 1000          # 1 ms
DEFAULT_FPS = 60


def quantise(us: int, quantum: int = QUANTUM_US) -> int:
    return int(round(us / quantum)) * quantum


# ── operator kinds ──────────────────────────────────────────────────────────

TRIM = "TRIM"                          # removes source, removes edit time
RETIME = "RETIME"                      # source at a rate: occupies src/rate
FREEZE = "FREEZE"                      # holds one frame: pure added time
INSERT = "INSERT"                      # authored material inserted whole
REPLAY = "REPLAY"                      # the same source shown again
REPEAT = "REPEAT"                      # a span repeated n times
STUTTER = "STUTTER"                    # n held frames, each of some dwell
OVERLAP = "OVERLAP"                    # two scenes share time: NEGATIVE
REPLACE = "REPLACE"                    # presentation swapped, duration kept
SYNTHETIC_INSERT = "SYNTHETIC_INSERT"  # authored animation, no source at all

KINDS = (TRIM, RETIME, FREEZE, INSERT, REPLAY, REPEAT, STUTTER, OVERLAP,
         REPLACE, SYNTHETIC_INSERT)

# Kinds that consume recorded source time.
SOURCE_CONSUMING = (TRIM, RETIME, REPLAY, REPEAT, REPLACE)
# Kinds whose edit contribution is negative.
SUBTRACTIVE = (TRIM, OVERLAP)
# Kinds that occupy no time of their own (they run under other material).
CONCURRENT = (REPLACE,)


# ── sync bias ───────────────────────────────────────────────────────────────
# Two axes, never one. `sync_contract` grades ACCURACY: how far the delivered
# moment sits from the intended one. This grades DIRECTION: which side of the
# gameplay event the music lands on, against a stated human preference.
#
#     delta = music_anchor - gameplay_event        (the project's convention)
#
# A NEGATIVE delta means the music arrives first and the gameplay lands into
# it. For hero payoffs the director prefers that -- the beat drives into the
# frag rather than appearing to react to it -- so the preferred hero delta is
# about -15 ms, with an acceptable band of -20..0. The values mirror
# editorial_sync_bias.DIRECTOR_2026_09, which is the profile of record.

PREFERRED_DELTA_US: dict[str, int] = {
    "HERO": -15_000,          # music leads; the frag lands into it
    "STUTTER_ATTACK": 0,      # a held frame reads on the attack itself
    "FREEZE_RELEASE": 0,
    "CAMERA_CUT": 0,
    "MATERIAL_FLASH": 0,
    "MORPH_PEAK": 0,          # aligns to the energy peak, not the onset
    "TRANSITION_HANDOFF": 0,
}
# Acceptable direction band per class, as (low_us, high_us) on the delta.
DELTA_BAND_US: dict[str, tuple[int, int]] = {
    "HERO": (-20_000, 0),
}
# Kept for readers of older code; the delta is the thing that matters.
BIAS_US = PREFERRED_DELTA_US

PREFERRED, ACCEPTABLE, WRONG_SIDE, NO_PREFERENCE = (
    "PREFERRED", "ACCEPTABLE", "WRONG_SIDE", "NO_PREFERENCE")
PREFERRED_WINDOW_US = 8_000       # how close to the preference still reads as it


@dataclass(frozen=True)
class AnchorConstraint:
    """A visual event that must land in a stated relationship to the music.

    `anchor_us` is the fixed musical instant. The event is NOT meant to land
    on it: for a hero it is meant to land `preferred_delta` AFTER it, so the
    music leads into the action. Accuracy and direction are reported
    separately, because +1 ms and -14 ms can be equally accurate while only
    one of them is what the director asked for.
    """
    event: str                 # the operator label whose peak this is
    anchor_us: int             # fixed music time, inside the slot
    kind: str = "HERO"
    tolerance_us: int = 40_000
    required: bool = True

    @property
    def preferred_delta_us(self) -> int:
        return PREFERRED_DELTA_US.get(self.kind, 0)

    @property
    def band_us(self) -> tuple[int, int] | None:
        return DELTA_BAND_US.get(self.kind)

    @property
    def target_us(self) -> int:
        """When the event should happen. delta = anchor - event, so an event
        that sits `preferred_delta` behind the anchor lands at anchor minus
        that (negative) delta -- i.e. AFTER it."""
        return self.anchor_us - self.preferred_delta_us

    def delta_us(self, actual_us: int) -> int:
        """music minus gameplay, the project's convention."""
        return self.anchor_us - actual_us

    def residual_us(self, actual_us: int) -> int:
        """How far the event is from where it was meant to be."""
        return actual_us - self.target_us

    def satisfied(self, actual_us: int) -> bool:
        return abs(self.residual_us(actual_us)) <= self.tolerance_us

    def direction_grade(self, actual_us: int) -> str:
        """Which side of the preference the delta fell on."""
        band = self.band_us
        if band is None:
            return NO_PREFERENCE
        d = self.delta_us(actual_us)
        if abs(d - self.preferred_delta_us) <= PREFERRED_WINDOW_US:
            return PREFERRED
        return ACCEPTABLE if band[0] <= d <= band[1] else WRONG_SIDE

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(preferred_delta_us=self.preferred_delta_us,
                 target_us=self.target_us, band_us=self.band_us)
        return d


# ── the operator ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TemporalOperator:
    """One elastic contribution to the final edit duration.

    The ranges are aesthetic, not arithmetic. `hard_min_us` / `hard_max_us`
    are what still looks acceptable; `preferred_us` is what looks best. The
    solver may use the whole hard range but is penalised for leaving the
    preferred one, so nothing is ever stretched merely because the maths
    would close.
    """
    kind: str
    label: str
    hard_min_us: int
    hard_max_us: int
    preferred_us: int | None = None
    preferred_min_us: int | None = None
    preferred_max_us: int | None = None
    src_in_us: int | None = None          # demo/source interval, when it has one
    src_out_us: int | None = None
    rate_min: Fraction | None = None      # RETIME / REPLAY
    rate_max: Fraction | None = None
    rate_preferred: Fraction | None = None
    repeats_min: int | None = None        # REPEAT / STUTTER
    repeats_max: int | None = None
    dwell_min_us: int | None = None       # STUTTER
    dwell_max_us: int | None = None
    peak_ratio: float = 0.0               # where the visual peak sits, 0..1
    anchor_kind: str = "HERO"
    capability: str = "DESIGNABLE"
    purpose: str = ""
    temporal_purpose: str = ""            # e.g. FILL_PRE_DROP -- never a reason alone
    notes: str = ""

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown temporal operator {self.kind!r}")
        if self.hard_min_us > self.hard_max_us:
            raise ValueError(f"{self.label}: hard range is inverted")
        if self.hard_min_us < 0 or self.hard_max_us < 0:
            raise ValueError(f"{self.label}: a duration range is never negative; "
                             f"sign comes from the operator kind")
        for v in (self.preferred_us, self.preferred_min_us, self.preferred_max_us):
            if v is not None and not (self.hard_min_us <= v <= self.hard_max_us):
                raise ValueError(f"{self.label}: preferred duration lies outside "
                                 f"the hard range")
        if self.kind in SOURCE_CONSUMING and self.kind != TRIM:
            if self.src_in_us is None or self.src_out_us is None:
                raise ValueError(f"{self.label}: {self.kind} needs a source interval")
            if self.src_out_us <= self.src_in_us:
                raise ValueError(f"{self.label}: source interval is empty")
        if self.kind in (RETIME, REPLAY) and (self.rate_min is None or self.rate_max is None):
            raise ValueError(f"{self.label}: {self.kind} needs a rate range")
        if self.kind == STUTTER and (self.repeats_min is None or self.dwell_min_us is None):
            raise ValueError(f"{self.label}: a stutter needs a count and a dwell")

    @property
    def src_span_us(self) -> int:
        if self.src_in_us is None or self.src_out_us is None:
            return 0
        return self.src_out_us - self.src_in_us

    @property
    def sign(self) -> int:
        return -1 if self.kind in SUBTRACTIVE else 0 if self.kind in CONCURRENT else 1

    @property
    def range_us(self) -> tuple[int, int]:
        """Signed contribution range: (lowest, highest) effect on final time."""
        lo, hi = self.hard_min_us, self.hard_max_us
        if self.sign < 0:
            return (-hi, -lo)
        if self.sign == 0:
            return (0, 0)
        return (lo, hi)

    @property
    def preferred_band(self) -> tuple[int, int]:
        lo = self.preferred_min_us if self.preferred_min_us is not None else (
            self.preferred_us if self.preferred_us is not None else self.hard_min_us)
        hi = self.preferred_max_us if self.preferred_max_us is not None else (
            self.preferred_us if self.preferred_us is not None else self.hard_max_us)
        return (min(lo, hi), max(lo, hi))

    def rate_for(self, duration_us: int) -> Fraction | None:
        """The exact rate that makes this source occupy `duration_us`."""
        if self.kind not in (RETIME, REPLAY) or not self.src_span_us or duration_us <= 0:
            return None
        return Fraction(self.src_span_us, duration_us)

    def duration_for_rate(self, rate: Fraction) -> int:
        """Source span at a rate occupies span / rate of edit time."""
        if not self.src_span_us or rate <= 0:
            return 0
        return int(round(self.src_span_us / float(rate)))

    def allows(self, duration_us: int) -> bool:
        if not (self.hard_min_us <= duration_us <= self.hard_max_us):
            return False
        if self.kind in (RETIME, REPLAY):
            r = self.rate_for(duration_us)
            if r is None or not (self.rate_min <= r <= self.rate_max):
                return False
        return True

    def deviation(self, duration_us: int) -> float:
        """How far outside the visually preferred band, as a fraction of the
        hard range. Zero inside the band."""
        lo, hi = self.preferred_band
        if lo <= duration_us <= hi:
            return 0.0
        span = max(self.hard_max_us - self.hard_min_us, 1)
        return (lo - duration_us if duration_us < lo else duration_us - hi) / span

    def rate_penalty(self, duration_us: int) -> float:
        """How far this duration puts the playback rate from the one that
        looks right. Zero when no rate is preferred."""
        if self.rate_preferred is None:
            return 0.0
        r = self.rate_for(duration_us)
        return 0.0 if r is None else abs(float(r) - float(self.rate_preferred))

    def soft_cost(self, duration_us: int, rate_weight: float = 1.5) -> float:
        """The aesthetic price of this duration: distance from the preferred
        band plus distance from the preferred rate. The search and the final
        ranking must use the SAME cost, or the search discards solutions the
        ranking would have preferred."""
        return self.deviation(duration_us) + rate_weight * self.rate_penalty(duration_us)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for k in ("rate_min", "rate_max", "rate_preferred"):
            if d[k] is not None:
                d[k] = str(d[k])
        d.update(sign=self.sign, range_us=list(self.range_us),
                 preferred_band=list(self.preferred_band),
                 src_span_us=self.src_span_us)
        return d


# ── a resolved choice ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class OperatorChoice:
    """One operator with its variables settled."""
    operator: TemporalOperator
    duration_us: int
    repeats: int | None = None
    dwell_us: int | None = None

    def __post_init__(self) -> None:
        if not self.operator.allows(self.duration_us):
            raise ValueError(
                f"{self.operator.label}: {self.duration_us} us is outside what "
                f"this operator may do ({self.operator.hard_min_us}.."
                f"{self.operator.hard_max_us})")

    @property
    def edit_us(self) -> int:
        """Signed contribution to the final sequence duration."""
        return self.operator.sign * self.duration_us

    @property
    def rate(self) -> Fraction | None:
        return self.operator.rate_for(self.duration_us)

    @property
    def peak_offset_us(self) -> int:
        return int(round(self.duration_us * self.operator.peak_ratio))

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.operator.label, "kind": self.operator.kind,
                "duration_us": self.duration_us, "edit_us": self.edit_us,
                "rate": str(self.rate) if self.rate is not None else None,
                "repeats": self.repeats, "dwell_us": self.dwell_us,
                "peak_offset_us": self.peak_offset_us,
                "deviation": round(self.operator.deviation(self.duration_us), 4)}


# ── elasticity ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TemporalElasticity:
    """The range of final durations a candidate can honestly produce.

    This is what a score-slot search should ask about. Raw source duration is
    the wrong question: a 2.9 s moment with a freeze, a slowed replay and a
    transition overlap available can occupy anywhere between its floor and
    its ceiling, and the slot only has to land inside that window.
    """
    min_us: int
    max_us: int
    preferred_min_us: int
    preferred_max_us: int
    operators: int

    def fits(self, slot_us: int) -> bool:
        return self.min_us <= slot_us <= self.max_us

    def comfortable(self, slot_us: int) -> bool:
        return self.preferred_min_us <= slot_us <= self.preferred_max_us

    @property
    def span_us(self) -> int:
        return self.max_us - self.min_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["span_us"] = self.span_us
        return d


def elasticity(operators: Sequence[TemporalOperator]) -> TemporalElasticity:
    lo = sum(o.range_us[0] for o in operators)
    hi = sum(o.range_us[1] for o in operators)
    plo = sum((o.sign * o.preferred_band[1] if o.sign < 0 else
               o.sign * o.preferred_band[0]) for o in operators)
    phi = sum((o.sign * o.preferred_band[0] if o.sign < 0 else
               o.sign * o.preferred_band[1]) for o in operators)
    return TemporalElasticity(lo, hi, min(plo, phi), max(plo, phi), len(operators))


# ── the composed plan ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class TemporalPlan:
    """Every operator resolved, so the final duration is a fact."""
    slot_id: str
    slot_us: int
    choices: tuple[OperatorChoice, ...]
    anchors: tuple[AnchorConstraint, ...] = ()
    quantum_us: int = QUANTUM_US

    @property
    def total_us(self) -> int:
        return sum(c.edit_us for c in self.choices)

    @property
    def exact(self) -> bool:
        return self.total_us == self.slot_us

    @property
    def residual_us(self) -> int:
        return self.total_us - self.slot_us

    def added_us(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.choices:
            if c.edit_us > 0:
                out[c.operator.kind] = out.get(c.operator.kind, 0) + c.edit_us
        return out

    def removed_us(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.choices:
            if c.edit_us < 0:
                out[c.operator.kind] = out.get(c.operator.kind, 0) - c.edit_us
        return out

    @property
    def source_us(self) -> int:
        """How much recorded source the plan actually uses."""
        return sum(c.operator.src_span_us for c in self.choices
                   if c.operator.kind in SOURCE_CONSUMING and c.operator.kind != TRIM)

    def timeline(self) -> list[dict[str, Any]]:
        """Where each operator sits in final edit time, in order.

        Concurrent operators (REPLACE) and overlaps do not advance the
        playhead; an overlap pulls it back, which is exactly how it saves
        time.
        """
        out: list[dict[str, Any]] = []
        t = 0
        for c in self.choices:
            if c.operator.sign < 0:
                t += c.edit_us                 # negative: pull the playhead back
                out.append({"label": c.operator.label, "kind": c.operator.kind,
                            "start_us": t, "end_us": t, "peak_us": t,
                            "edit_us": c.edit_us})
                continue
            start = t
            end = t + c.duration_us if c.operator.sign > 0 else t
            out.append({"label": c.operator.label, "kind": c.operator.kind,
                        "start_us": start, "end_us": end,
                        "peak_us": start + c.peak_offset_us,
                        "edit_us": c.edit_us})
            t = end
        return out

    def event_us(self, label: str) -> int | None:
        for row in self.timeline():
            if row["label"] == label:
                return row["peak_us"]
        return None

    def anchor_report(self) -> list[dict[str, Any]]:
        """Every musical relationship, measured on the FINISHED composition."""
        out = []
        for a in self.anchors:
            actual = self.event_us(a.event)
            out.append({"event": a.event, "kind": a.kind,
                        "anchor_us": a.anchor_us, "target_us": a.target_us,
                        "preferred_delta_us": a.preferred_delta_us,
                        "actual_us": actual,
                        "delta_us": None if actual is None else a.delta_us(actual),
                        "residual_us": None if actual is None else a.residual_us(actual),
                        "direction": (NO_PREFERENCE if actual is None
                                      else a.direction_grade(actual)),
                        "satisfied": False if actual is None else a.satisfied(actual),
                        "required": a.required, "tolerance_us": a.tolerance_us})
        return out

    @property
    def anchors_satisfied(self) -> bool:
        return all(r["satisfied"] for r in self.anchor_report() if r["required"])

    def deviation(self) -> float:
        if not self.choices:
            return 0.0
        return round(sum(c.operator.deviation(c.duration_us)
                         for c in self.choices) / len(self.choices), 4)

    def to_dict(self) -> dict[str, Any]:
        return {"slot_id": self.slot_id, "slot_us": self.slot_us,
                "total_us": self.total_us, "exact": self.exact,
                "residual_us": self.residual_us, "source_us": self.source_us,
                "added_us": self.added_us(), "removed_us": self.removed_us(),
                "deviation": self.deviation(),
                "anchors_satisfied": self.anchors_satisfied,
                "choices": [c.to_dict() for c in self.choices],
                "timeline": self.timeline(), "anchors": self.anchor_report(),
                "version": TEMPORAL_VERSION}

    @property
    def plan_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()[:24]


# ── composed time map ───────────────────────────────────────────────────────

SOURCE_TRUTH = "SOURCE_TRUTH"
PRESENTATION = "PRESENTATION"
AUTHORED = "AUTHORED"


@dataclass(frozen=True)
class ComposedSpan:
    """One stretch of final edit time and what it is made of."""
    edit_start_us: int
    edit_end_us: int
    kind: str
    origin: str                      # SOURCE_TRUTH | PRESENTATION | AUTHORED
    src_in_us: int | None = None
    src_out_us: int | None = None
    rate: Fraction | None = None
    label: str = ""

    @property
    def edit_span_us(self) -> int:
        return self.edit_end_us - self.edit_start_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["rate"] = str(self.rate) if self.rate is not None else None
        d["edit_span_us"] = self.edit_span_us
        return d


@dataclass(frozen=True)
class ComposedTimeMap:
    """source/demo time -> presentation -> operators -> final edit_us.

    The authoritative movie playhead is final edit_us, and in song-locked mode
    that axis is the song's own. Demo time is never rewritten: a span records
    which source interval it shows and at what rate, and a freeze or an
    authored insert records that it shows no new source at all.
    """
    spans: tuple[ComposedSpan, ...]
    slot_us: int
    song_locked: bool = True

    @property
    def total_us(self) -> int:
        return max((s.edit_end_us for s in self.spans), default=0)

    def demo_at(self, edit_us: int) -> tuple[int | None, str]:
        """What source instant is on screen at this point of the movie."""
        for s in self.spans:
            if s.edit_start_us <= edit_us < s.edit_end_us:
                if s.src_in_us is None or s.rate is None:
                    return (s.src_in_us, s.origin)
                offset = edit_us - s.edit_start_us
                return (s.src_in_us + int(round(offset * float(s.rate))), s.origin)
        return (None, "")

    def to_dict(self) -> dict[str, Any]:
        return {"slot_us": self.slot_us, "total_us": self.total_us,
                "song_locked": self.song_locked,
                "spans": [s.to_dict() for s in self.spans]}


def compose(plan: TemporalPlan) -> ComposedTimeMap:
    """Compile a resolved plan into the final mapping.

    Refuses an unresolved plan: sync is a property of the FINISHED
    choreography, so a map that does not occupy its slot exactly cannot be
    used to measure anything.
    """
    if not plan.exact:
        raise ValueError(
            f"{plan.slot_id}: the composition occupies {plan.total_us} us but the "
            f"score slot is {plan.slot_us} us ({plan.residual_us:+d}). Sync is a "
            f"property of the finished choreography; resolve the operators first.")
    spans: list[ComposedSpan] = []
    for row, c in zip(plan.timeline(), plan.choices):
        op = c.operator
        if op.sign <= 0:
            continue                      # overlaps and concurrent runs add no span
        origin = (SOURCE_TRUTH if op.kind in SOURCE_CONSUMING
                  else AUTHORED if op.kind in (SYNTHETIC_INSERT, INSERT)
                  else PRESENTATION)
        spans.append(ComposedSpan(
            row["start_us"], row["end_us"], op.kind, origin,
            op.src_in_us, op.src_out_us, c.rate, op.label))
    return ComposedTimeMap(tuple(spans), plan.slot_us)


# ── song-locked mode ────────────────────────────────────────────────────────

class SongMoved(RuntimeError):
    """Raised when something tries to move the music to fit the picture."""


@dataclass(frozen=True)
class SongLock:
    """The chosen song, and the fact that it does not move.

    In song-locked mode the sequence duration IS the song duration -- a
    4:18.000 track means exactly 258.000 s of movie, and the visual timeline
    is what bends. Slots are carved out of that fixed ruler and must tile it
    without gap or overlap, because a gap is silence nobody authored and an
    overlap is two things claiming the same instant.
    """
    track_hash: str
    duration_us: int
    title: str = ""

    def __post_init__(self) -> None:
        if self.duration_us <= 0:
            raise ValueError("a song with no duration cannot be a ruler")

    def slot(self, start_us: int, end_us: int) -> tuple[int, int]:
        if not (0 <= start_us < end_us <= self.duration_us):
            raise SongMoved(
                f"a slot {start_us}..{end_us} does not fit inside the song "
                f"(0..{self.duration_us}). The picture bends, the song does not.")
        return (start_us, end_us)

    def check_tiling(self, slots: Sequence[tuple[int, int]]) -> list[str]:
        """Every complaint about how the slots cover the song."""
        out: list[str] = []
        ordered = sorted(slots)
        if not ordered:
            return [f"nothing covers the song's {self.duration_us} us"]
        if ordered[0][0] != 0:
            out.append(f"the song starts at 0 but the first slot starts at "
                       f"{ordered[0][0]}")
        for a, b in zip(ordered, ordered[1:]):
            if b[0] > a[1]:
                out.append(f"gap of {b[0] - a[1]} us between {a[1]} and {b[0]}")
            elif b[0] < a[1]:
                out.append(f"slots overlap by {a[1] - b[0]} us at {b[0]}")
        if ordered[-1][1] != self.duration_us:
            out.append(f"the song ends at {self.duration_us} but the last slot "
                       f"ends at {ordered[-1][1]}")
        return out

    def retimed(self, new_duration_us: int) -> "SongLock":
        raise SongMoved(
            f"the song is {self.duration_us} us and stays {self.duration_us} us. "
            f"Fitting the picture is what the temporal operators are for.")

    def to_dict(self) -> dict[str, Any]:
        return {"track_hash": self.track_hash, "duration_us": self.duration_us,
                "title": self.title, "song_locked": True}


def verify_song_locked(lock: SongLock, plans: Sequence[TemporalPlan]) -> list[str]:
    """Every plan occupies its slot exactly and the slots tile the song."""
    problems: list[str] = []
    cursor = 0
    slots: list[tuple[int, int]] = []
    for p in plans:
        if not p.exact:
            problems.append(f"{p.slot_id} occupies {p.total_us} us of a "
                            f"{p.slot_us} us slot ({p.residual_us:+d})")
        slots.append((cursor, cursor + p.slot_us))
        cursor += p.slot_us
    return problems + lock.check_tiling(slots)
