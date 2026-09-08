"""Where gameplay numbers meet music numbers. Arithmetic, not listening.

Once the demo has produced exact gameplay times and the music analysis has
produced exact musical times, matching them is a constraint problem with a
closed-form answer. There is nothing to detect and nothing to hear:

    the frag is at 91.500000 s
    the director wants the music to lead by 15 ms
    therefore the musical anchor must land at 91.485000 s
    the nearest qualifying anchor is at 91.483000 s
    the placement error is -2.0 ms, which is TARGET

and for a replay:

    the rocket flew 1,125,000 us
    seven beats at 161.5 BPM span 2,600,619 us
    therefore the rate is exactly 1125000/2600619 = 0.4326x
    which lies inside the envelope the footage can carry

Every number here is exact. Rates are Fractions so that a requested 1/1 can
never drift into 0.995, and every solution reports the residual error rather
than rounding it away. Human ears are still required -- but for whether
-15 ms feels better than 0, not for finding out where the kill was.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from fractions import Fraction
from typing import Any, Sequence

from creative_suite.engine import editorial_sync_bias as eb
from creative_suite.engine import sync_contract

MATCH_VERSION = "numeric-match-v1.0.0"


# ── anchoring a hero event ──────────────────────────────────────────────────

@dataclass(frozen=True)
class AnchorSolution:
    """Where the music must sit for one gameplay event, and how well it fits."""
    game_us: int
    target_music_us: int
    chosen_music_us: int
    bias_ms: float
    event_class: str
    absolute_tier: str
    direction_grade: str
    anchor_index: int | None = None
    note: str = ""

    @property
    def delivered_delta_ms(self) -> float:
        """Music minus gameplay, the project's convention throughout."""
        return round((self.chosen_music_us - self.game_us) / 1000.0, 3)

    @property
    def error_ms(self) -> float:
        """How far the chosen anchor sits from the one we asked for."""
        return round((self.chosen_music_us - self.target_music_us) / 1000.0, 3)

    @property
    def music_placement_shift_us(self) -> int:
        """How far the music must move so the anchor lands on the target."""
        return self.target_music_us - self.chosen_music_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(delivered_delta_ms=self.delivered_delta_ms,
                 error_ms=self.error_ms,
                 music_placement_shift_us=self.music_placement_shift_us)
        return d


def target_anchor_us(game_us: int, event_class: str, *,
                     profile: eb.BiasProfile = eb.DEFAULT_PROFILE) -> int | None:
    """The exact musical instant this event class wants. None = no preference."""
    return eb.target_music_us(game_us, event_class, profile=profile)


def solve_anchor(game_us: int, anchors_us: Sequence[int], event_class: str, *,
                 profile: eb.BiasProfile = eb.DEFAULT_PROFILE,
                 max_search_us: int = 750_000) -> AnchorSolution | None:
    """Pick the musical anchor that best serves one gameplay event.

    ``anchors_us`` are PERCEPTUAL anchors -- where the music is heard to hit,
    not where its waveform starts. Feeding raw onsets here reintroduces the
    error the anchor model exists to remove.
    """
    if not anchors_us:
        return None
    target = target_anchor_us(game_us, event_class, profile=profile)
    if target is None:
        # No hard-sync preference for this class: nearest anchor, reported
        # honestly, with no pretence that a target was met.
        idx = min(range(len(anchors_us)),
                  key=lambda i: abs(anchors_us[i] - game_us))
        chosen = int(anchors_us[idx])
        assessment = eb.assess((chosen - game_us) / 1000.0, event_class,
                               profile=profile)
        return AnchorSolution(
            game_us=int(game_us), target_music_us=int(game_us),
            chosen_music_us=chosen, bias_ms=0.0, event_class=event_class,
            absolute_tier=assessment.absolute_tier,
            direction_grade=assessment.direction_grade, anchor_index=idx,
            note="no hard-sync preference for this class; nearest anchor")

    within = [(i, us) for i, us in enumerate(anchors_us)
              if abs(us - target) <= max_search_us]
    if not within:
        return None
    idx, chosen = min(within, key=lambda pair: abs(pair[1] - target))
    bias = profile.bias_for(event_class)
    assessment = eb.assess((chosen - game_us) / 1000.0, event_class,
                           profile=profile)
    return AnchorSolution(
        game_us=int(game_us), target_music_us=int(target),
        chosen_music_us=int(chosen),
        bias_ms=float(bias.preferred_delta_ms or 0.0),
        event_class=event_class, absolute_tier=assessment.absolute_tier,
        direction_grade=assessment.direction_grade, anchor_index=idx,
        note=assessment.explanation)


# ── retiming a span to fit the music ────────────────────────────────────────

@dataclass(frozen=True)
class RateSolution:
    """An exact replay rate that makes a gameplay span fill musical time."""
    source_span_us: int
    beats: int
    beat_us: int
    rate: Fraction
    edit_span_us: int
    within_preferred: bool
    within_hard: bool

    @property
    def rate_float(self) -> float:
        return round(float(self.rate), 6)

    @property
    def residual_us(self) -> int:
        """Rounding left over after the rate is applied. Reported, not hidden."""
        return self.edit_span_us - self.beats * self.beat_us

    def to_dict(self) -> dict[str, Any]:
        return {"source_span_us": self.source_span_us, "beats": self.beats,
                "beat_us": self.beat_us, "rate": str(self.rate),
                "rate_float": self.rate_float,
                "edit_span_us": self.edit_span_us,
                "residual_us": self.residual_us,
                "within_preferred": self.within_preferred,
                "within_hard": self.within_hard}


def beat_us_for(bpm: float) -> int:
    if bpm <= 0:
        raise ValueError("bpm must be positive")
    return int(round(60_000_000 / float(bpm)))


def solve_rate(source_span_us: int, bpm: float, envelope: Any, *,
               beat_range: Sequence[int] = tuple(range(1, 17))
               ) -> list[RateSolution]:
    """Every whole-beat span the footage can legally be stretched across.

    Returns the legal options rather than one answer, because which of them
    is beautiful is a human decision. The arithmetic only says which are
    possible.
    """
    if source_span_us <= 0:
        raise ValueError("source span must be positive")
    beat = beat_us_for(bpm)
    out: list[RateSolution] = []
    for k in beat_range:
        if k <= 0:
            continue
        target = beat * k
        rate = Fraction(int(source_span_us), int(target))
        if not envelope.allows(float(rate)):
            continue
        edit_span = int(round(source_span_us / float(rate)))
        out.append(RateSolution(
            source_span_us=int(source_span_us), beats=int(k), beat_us=beat,
            rate=rate, edit_span_us=edit_span,
            within_preferred=envelope.prefers(float(rate)),
            within_hard=True))
    return out


def best_rate(source_span_us: int, bpm: float, envelope: Any, *,
              prefer_beats: int | None = None,
              beat_range: Sequence[int] = tuple(range(1, 17))
              ) -> RateSolution | None:
    """The slowest legal rate the footage prefers, or a named beat span."""
    options = solve_rate(source_span_us, bpm, envelope, beat_range=beat_range)
    if not options:
        return None
    if prefer_beats is not None:
        for o in options:
            if o.beats == prefer_beats:
                return o
    preferred = [o for o in options if o.within_preferred]
    pool = preferred or options
    return min(pool, key=lambda o: float(o.rate))


# ── scheduling everything else around the payoff ────────────────────────────

@dataclass(frozen=True)
class ScheduledElement:
    """One visual element's exact position on the edit clock."""
    name: str
    start_us: int
    peak_us: int
    end_us: int
    trigger: str
    purpose: str

    @property
    def lead_us(self) -> int:
        return self.peak_us - self.start_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["lead_us"] = self.lead_us
        return d


def schedule_around(hero_edit_us: int,
                    elements: Sequence[tuple[str, Any, str, str]]
                    ) -> list[ScheduledElement]:
    """Place footprints so each element's peak lands where it belongs.

    ``elements`` are ``(name, footprint, trigger, purpose)``. Each footprint
    positions itself around the hero moment; nothing is nudged afterwards,
    because a footprint that has to be adjusted by hand was the wrong
    footprint.
    """
    out: list[ScheduledElement] = []
    for name, footprint, trigger, purpose in elements:
        at = footprint.place_at_peak(hero_edit_us)
        out.append(ScheduledElement(
            name=name, start_us=at["start_us"], peak_us=at["peak_us"],
            end_us=at["end_us"], trigger=trigger, purpose=purpose))
    return sorted(out, key=lambda e: e.start_us)


def numeric_timeline(entries: Sequence[tuple[int, str]]) -> list[str]:
    """The whole edit as a printable ledger of times and events.

    Deliberately plain text. A ledger like this is what a reader checks a
    diagnostic sheet AGAINST -- the graph displays these numbers, it is never
    where they come from.
    """
    return [f"{us / 1e6:12.6f}   {label}"
            for us, label in sorted(entries, key=lambda x: x[0])]
