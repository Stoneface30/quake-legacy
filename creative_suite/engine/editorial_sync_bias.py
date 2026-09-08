"""Editorial timing preference: a SECOND axis, beside mathematical sync.

Two hits, one at +5 ms and one at -5 ms, are equally accurate. They are not
equally good. `sync_contract` grades ACCURACY -- how far the delivered
moment sits from the intended one -- and that grading is not touched here.
This module grades DIRECTION: which side of the gameplay event the music
lands on, against a stated human preference.

    delta_ms = music_anchor - game_anchor        (the project's convention)

A negative delta means the music arrives FIRST and the gameplay lands into
it. For hero payoffs the director prefers that: the beat drives into the
frag instead of appearing to react to it. The current preference is about
-15 ms, which at 60 fps is very close to one video frame of lead.

THIS IS A PREFERENCE, NOT A LAW. Perceptual research explains why a small
musical lead can feel strong -- a sharp transient's perceptual attack sits
slightly after its onset, so a lead of a frame puts the PERCEIVED hit on top
of the action -- but it does not establish a universal constant, and the
right value depends on the attack shape and the viewer. So the number lives
in a named profile that a human can change, never as a global constant, and
different event classes carry different preferences.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from creative_suite.engine import sync_contract

# Event classes. A class exists when its editorial timing differs, not for
# every kind of thing that can happen in a demo.
HERO_KILL = "HERO_KILL"
DIRECT_HIT = "DIRECT_HIT"
RAIL_HIT = "RAIL_HIT"
FRAG = "FRAG"
LG_FINAL_KILL = "LG_FINAL_KILL"
DODGE_NEAR_MISS = "DODGE_NEAR_MISS"
LG_CONTACT = "LG_CONTACT"
INTRO_LOGO = "INTRO_LOGO"

EVENT_CLASSES = (HERO_KILL, DIRECT_HIT, RAIL_HIT, FRAG, LG_FINAL_KILL,
                 DODGE_NEAR_MISS, LG_CONTACT, INTRO_LOGO)

PREFERRED = "PREFERRED"
ACCEPTABLE = "ACCEPTABLE"
WRONG_SIDE = "WRONG_SIDE"
FAR_FROM_PREFERENCE = "FAR_FROM_PREFERENCE"
NO_PREFERENCE = "NO_PREFERENCE"
DIRECTION_GRADES = (PREFERRED, ACCEPTABLE, WRONG_SIDE, FAR_FROM_PREFERENCE,
                    NO_PREFERENCE)

# Half a frame at 60 fps: below this the direction is not the thing to argue
# about, and calling it a miss would be false precision.
PREFERRED_WINDOW_MS = 8.0


@dataclass(frozen=True)
class ClassBias:
    """The preference for one class of gameplay event."""
    event_class: str
    preferred_delta_ms: float | None      # None = timing is not a hard sync
    acceptable_low_ms: float | None
    acceptable_high_ms: float | None
    rationale: str

    def __post_init__(self) -> None:
        if self.preferred_delta_ms is None:
            return
        if None in (self.acceptable_low_ms, self.acceptable_high_ms):
            raise ValueError("a stated preference needs an acceptable band")
        if not (self.acceptable_low_ms <= self.preferred_delta_ms
                <= self.acceptable_high_ms):
            raise ValueError("preferred delta must lie inside its own band")


@dataclass(frozen=True)
class BiasProfile:
    """One human's timing taste, named and dated so it can be argued with."""
    name: str
    author: str
    stated_on: str
    classes: tuple[ClassBias, ...]

    def bias_for(self, event_class: str) -> ClassBias:
        for c in self.classes:
            if c.event_class == event_class:
                return c
        raise KeyError(f"no editorial bias recorded for {event_class!r}")

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "author": self.author,
                "stated_on": self.stated_on,
                "classes": [asdict(c) for c in self.classes]}


_LEAD = ("the director prefers the music to arrive first so the beat drives "
         "into the frag; about one 60 fps frame of lead")

# The current profile. Stated by the director on 2026-09-02 after reviewing
# LG Canary A, whose kill landed at +11.5 ms -- accurate, wrong side.
DIRECTOR_2026_09 = BiasProfile(
    name="director-2026-09",
    author="director",
    stated_on="2026-09-02",
    classes=(
        ClassBias(HERO_KILL, -15.0, -20.0, 0.0, _LEAD),
        ClassBias(LG_FINAL_KILL, -15.0, -20.0, 0.0, _LEAD),
        ClassBias(DIRECT_HIT, -15.0, -20.0, 0.0, _LEAD),
        ClassBias(RAIL_HIT, -15.0, -20.0, 0.0, _LEAD),
        ClassBias(FRAG, -15.0, -20.0, 0.0, _LEAD),
        ClassBias(DODGE_NEAR_MISS, 5.0, 0.0, 10.0,
                  "a reaction may follow the danger it reacts to"),
        ClassBias(INTRO_LOGO, 0.0, -10.0, 10.0,
                  "the logo lands with the music, neither leading nor trailing"),
        ClassBias(LG_CONTACT, None, None, None,
                  "contact texture is a pattern relationship, not a hard sync; "
                  "no per-contact offset is preferred or enforced"),
    ))

DEFAULT_PROFILE = DIRECTOR_2026_09


@dataclass(frozen=True)
class BiasAssessment:
    """Accuracy and direction, reported side by side and never merged."""
    event_class: str
    delta_ms: float
    absolute_tier: str                 # from sync_contract: how CLOSE
    direction_grade: str               # from this module: which SIDE
    preferred_delta_ms: float | None
    offset_from_preference_ms: float | None
    profile: str
    explanation: str

    @property
    def is_editorially_preferred(self) -> bool:
        return self.direction_grade in (PREFERRED, NO_PREFERENCE)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["is_editorially_preferred"] = self.is_editorially_preferred
        return d


def assess(delta_ms: float, event_class: str, *,
           profile: BiasProfile = DEFAULT_PROFILE,
           sync_class: str = sync_contract.CLASS_HARD) -> BiasAssessment:
    """Grade one measured delta on BOTH axes.

    ``delta_ms`` is music minus gameplay, measured in the delivered file.
    ``sync_class`` selects the accuracy thresholds already defined by the
    sync contract; this function never redefines them.
    """
    bias = profile.bias_for(event_class)
    tier = sync_contract.classify_delta(float(delta_ms), sync_class)
    if bias.preferred_delta_ms is None:
        return BiasAssessment(
            event_class=event_class, delta_ms=round(float(delta_ms), 2),
            absolute_tier=tier, direction_grade=NO_PREFERENCE,
            preferred_delta_ms=None, offset_from_preference_ms=None,
            profile=profile.name,
            explanation=f"{event_class}: {bias.rationale}")

    offset = round(float(delta_ms) - bias.preferred_delta_ms, 2)
    if abs(offset) <= PREFERRED_WINDOW_MS:
        grade = PREFERRED
        why = (f"{delta_ms:+.1f} ms is within {PREFERRED_WINDOW_MS:.0f} ms of the "
               f"preferred {bias.preferred_delta_ms:+.0f} ms")
    elif bias.acceptable_low_ms <= delta_ms <= bias.acceptable_high_ms:
        grade = ACCEPTABLE
        why = (f"{delta_ms:+.1f} ms is inside the acceptable band "
               f"[{bias.acceptable_low_ms:+.0f}, {bias.acceptable_high_ms:+.0f}] "
               f"but {offset:+.1f} ms from the preference")
    elif (bias.preferred_delta_ms < 0 <= delta_ms) or (
            bias.preferred_delta_ms > 0 and delta_ms <= 0):
        grade = WRONG_SIDE
        lead = "lead" if bias.preferred_delta_ms < 0 else "trail"
        why = (f"{delta_ms:+.1f} ms is on the wrong side: the preference is for "
               f"the music to {lead} by {abs(bias.preferred_delta_ms):.0f} ms")
    else:
        grade = FAR_FROM_PREFERENCE
        why = (f"{delta_ms:+.1f} ms is {abs(offset):.1f} ms from the preferred "
               f"{bias.preferred_delta_ms:+.0f} ms, outside the acceptable band")
    return BiasAssessment(
        event_class=event_class, delta_ms=round(float(delta_ms), 2),
        absolute_tier=tier, direction_grade=grade,
        preferred_delta_ms=bias.preferred_delta_ms,
        offset_from_preference_ms=offset, profile=profile.name,
        explanation=why)


def target_music_us(game_anchor_us: int, event_class: str, *,
                    profile: BiasProfile = DEFAULT_PROFILE) -> int | None:
    """Where the PERCEPTUAL musical anchor should land for this event class.

    Returns None where the class has no hard-sync preference. The caller
    aligns the anchor's ``perceptual_anchor_us``, never its raw onset.
    """
    bias = profile.bias_for(event_class)
    if bias.preferred_delta_ms is None:
        return None
    return int(round(game_anchor_us + bias.preferred_delta_ms * 1000.0))
