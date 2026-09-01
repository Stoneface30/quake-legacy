"""EDITORIAL_CANARY_V3_IMPACT: the impact editorial clock (directive 7-11).

One scene, one rocket, one impact. Everything is expressed relative to
T = the impact, resolved from recognition evidence, so the clock survives a
change in the underlying data and can be re-rendered identically.

THE SHAPE, and why each point is where it is:

    T-2.50   scene begins, FPV            the player's own aim is the setup
    T-1.125  rocket launch                 SECONDARY -- fire is only support
    T-1.05   cinematic insert may begin    only if the trajectory earns it
    T-0.50   DRAMATIC ATTENTION BEGINS     the viewer must anticipate, so the
                                           treatment starts BEFORE the kill
    T-0.15   return to FPV                 the original aim owns the impact
    T        IMPACT                        PRIMARY head-nod event; gets the music
    T+0.30   cut                           no corpse camera, no debris orbit

CAMERA AND TIME ARE SEPARATE (directive 8). The insert is a camera choice
and may start earlier to show geometry; the slow/emphasis treatment is a
time choice and starts at T-500 by default. Both resolve onto the same
edit clock and neither moves the gameplay.

A native cam10 cannot express first person, so an FPV -> insert -> FPV
scene is TWO captures under TWO profiles (FPV_GAMEPLAY, CINEMATIC_CLEAN)
composited on this clock. That is stated here rather than hidden in the
assembly, because it is the reason the insert has its own profile check.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from fractions import Fraction
import hashlib
import json
from typing import Any

from creative_suite.engine import presentation, edit_qa, sync_contract as sc

CANARY_SCHEMA_VERSION = 3
CANARY_NAME = "EDITORIAL_CANARY_V3_IMPACT"
ORDERINGS = ("FPV_THEN_REPLAY", "REPLAY_THEN_FPV", "BOTH")


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


@dataclass(frozen=True)
class ImpactClock:
    """All offsets in microseconds RELATIVE TO IMPACT (negative = before)."""
    scene_start_us: int = -2_500_000
    launch_us: int = -1_125_000            # resolved from the projectile track
    insert_start_us: int | None = -1_050_000
    attention_us: int = -500_000            # dramatic treatment begins
    fpv_return_us: int = -150_000
    tail_us: int = 300_000
    slow_rate: Fraction = Fraction(1, 2)
    # The slow span is EXPLICIT. By default it is attention..fpv_return (the
    # V3 canary). Review feedback asked for the whole flight slowed with the
    # rate decided by the music, so a clock may instead set it to
    # launch..impact and derive slow_rate with beat_locked_rate().
    slow_start_us: int | None = None
    slow_end_us: int | None = None
    # FPV_THEN_REPLAY / REPLAY_THEN_FPV / BOTH -- decided at lock-in, not a rule
    ordering: str = "FPV_THEN_REPLAY"
    insert_camera: str = "PROJECTILE"
    insert_distance: float = 60.0
    insert_height: float = 16.0

    def __post_init__(self) -> None:
        for name in ("scene_start_us", "launch_us", "attention_us",
                     "fpv_return_us", "tail_us"):
            v = getattr(self, name)
            if not isinstance(v, int) or isinstance(v, bool):
                raise ValueError(name + " must be an int (microseconds)")
        if self.insert_start_us is not None and not isinstance(
                self.insert_start_us, int):
            raise ValueError("insert_start_us must be an int or None")
        if not (self.scene_start_us < self.launch_us < 0):
            raise ValueError("launch must sit between scene start and impact")
        if self.insert_start_us is not None:
            if not (self.launch_us <= self.insert_start_us < self.fpv_return_us):
                raise ValueError(
                    "the insert must start at or after launch and end before "
                    "the FPV return -- the original aim owns the impact")
        # Attention MUST begin before impact. Starting the treatment after the
        # kill is the specific mistake the directive forbids.
        if not (self.attention_us < 0):
            raise ValueError("dramatic attention must begin BEFORE impact")
        if not (self.attention_us < self.fpv_return_us <= 0):
            raise ValueError("FPV return must follow attention and precede impact")
        if self.tail_us < 0:
            raise ValueError("tail must be non-negative")
        if not (0 < self.slow_rate <= 1):
            raise ValueError("slow_rate must be in (0, 1]")
        if presentation.presentation_for(self.insert_camera) != presentation.CINEMATIC_CLEAN:
            raise ValueError("the insert must be a cinematic camera")
        if self.ordering not in ORDERINGS:
            raise ValueError("unknown ordering: " + str(self.ordering))
        s, e = self.slow_span_us
        if not (self.scene_start_us <= s < e <= self.tail_us):
            raise ValueError("slow span must lie inside the scene")

    @property
    def slow_span_us(self) -> tuple[int, int]:
        s = self.attention_us if self.slow_start_us is None else self.slow_start_us
        e = self.fpv_return_us if self.slow_end_us is None else self.slow_end_us
        return int(s), int(e)

    # -- resolution onto the edit clock (0 = scene start) -------------------
    @property
    def impact_edit_us(self) -> int:
        return -self.scene_start_us

    def edit(self, rel_us: int) -> int:
        return rel_us - self.scene_start_us

    @property
    def duration_us(self) -> int:
        return self.edit(self.tail_us)

    @property
    def has_insert(self) -> bool:
        return self.insert_start_us is not None

    def segments(self) -> list[dict[str, Any]]:
        """The programme as (camera, presentation, rate) spans on the edit clock.

        The slow treatment is a TIME span and the insert is a CAMERA span;
        they overlap by design and are reported as separate facts.
        """
        out = []
        if self.has_insert:
            out.append({"kind": "camera", "camera": "FPV",
                        "presentation": presentation.FPV_GAMEPLAY,
                        "start_us": 0, "end_us": self.edit(self.insert_start_us)})
            out.append({"kind": "camera", "camera": self.insert_camera,
                        "presentation": presentation.CINEMATIC_CLEAN,
                        "start_us": self.edit(self.insert_start_us),
                        "end_us": self.edit(self.fpv_return_us)})
            out.append({"kind": "camera", "camera": "FPV",
                        "presentation": presentation.FPV_GAMEPLAY,
                        "start_us": self.edit(self.fpv_return_us),
                        "end_us": self.duration_us})
        else:
            out.append({"kind": "camera", "camera": "FPV",
                        "presentation": presentation.FPV_GAMEPLAY,
                        "start_us": 0, "end_us": self.duration_us})
        s, e = self.slow_span_us
        out.append({"kind": "time", "rate": str(self.slow_rate),
                    "start_us": self.edit(s), "end_us": self.edit(e)})
        return out

    def sync_events(self) -> list[tuple[str, int, bool]]:
        """(event, edit_us, primary). Impact gets the music; fire is support."""
        return [("ROCKET_IMPACT", self.impact_edit_us, True),
                ("PROJECTILE_LAUNCH", self.edit(self.launch_us), False)]

    def canonical(self) -> dict[str, Any]:
        d = asdict(self)
        d["slow_rate"] = str(self.slow_rate)
        d["schema_version"] = CANARY_SCHEMA_VERSION
        return d

    @property
    def clock_id(self) -> str:
        return hashlib.sha256(
            canonical_json(self.canonical()).encode("utf-8")).hexdigest()


def from_projectile_track(track, *, insert: bool = True,
                          **overrides) -> ImpactClock:
    """Resolve launch relative to impact from the cached projectile track."""
    if not track or len(track) < 2:
        raise ValueError("a usable projectile track is required")
    launch_ms, impact_ms = track[0][0], track[-1][0]
    flight_us = int(round((impact_ms - launch_ms) * 1000))
    if flight_us <= 0:
        raise ValueError("impact must follow launch")
    kw = dict(launch_us=-flight_us)
    if not insert:
        kw["insert_start_us"] = None
    kw.update(overrides)
    return ImpactClock(**kw)


def qa(clock: ImpactClock, *, subject_end_rel_us: int = 0) -> dict[str, Any]:
    """The three bad-edit checks applied to this clock's programme.

    ``subject_end_rel_us`` is when the victim stops being a subject,
    relative to impact; 0 means the impact frame itself.
    """
    findings = []
    for seg in clock.segments():
        if seg["kind"] != "camera":
            continue
        profile = presentation.profile_for(seg["camera"])
        findings += edit_qa.check_hud(seg["camera"], profile)
    if clock.has_insert:
        ins = next(s for s in clock.segments()
                   if s["kind"] == "camera" and s["camera"] != "FPV")
        # the projectile itself is the subject for the whole insert
        findings += edit_qa.check_no_subject(
            ins["start_us"] / 1000.0, ins["end_us"] / 1000.0,
            [(ins["start_us"] / 1000.0, ins["end_us"] / 1000.0)])
    # The corpse-camera check is about a CINEMATIC camera outliving its
    # subject. An FPV tail always has one -- the live player -- so it only
    # applies when the programme ends on a cinematic segment. Review asked
    # for a 2 s FPV tail so the music can resolve; that is not a corpse cam.
    last = [s for s in clock.segments() if s["kind"] == "camera"][-1]
    if last["presentation"] == presentation.CINEMATIC_CLEAN:
        findings += edit_qa.check_post_death(
            clock.edit(subject_end_rel_us) / 1000.0,
            clock.duration_us / 1000.0)
    return edit_qa.summarize(findings)


def beat_locked_rate(flight_us: int, bpm: float, *, want: float = 0.5,
                     lo: float = 0.25, hi: float = 1.0) -> tuple[Fraction, int]:
    """The slow rate that makes the flight span a whole number of beats.

    MUSIC DECIDES THE SLOW. For a beat period P and flight F, rate r = F /
    (k * P) stretches the flight to exactly k beats, so launch and impact
    land on the grid BECAUSE of the slow rather than despite it. ``want``
    picks which k: the one whose rate is nearest the slowness asked for.
    Returns (rate, k). The rate is an exact Fraction in microseconds so the
    TimeMap contract's integer arithmetic holds.
    """
    if flight_us <= 0 or bpm <= 0:
        raise ValueError("flight and bpm must be positive")
    period_us = Fraction(60_000_000) / Fraction(bpm).limit_denominator(10_000)
    best = None
    for k in range(1, 64):
        r = Fraction(flight_us) / (k * period_us)
        if not (lo <= r <= hi):
            continue
        if best is None or abs(float(r) - want) < abs(float(best[0]) - want):
            best = (r.limit_denominator(10_000), k)
    if best is None:
        raise ValueError("no whole-beat slow rate in range")
    return best
