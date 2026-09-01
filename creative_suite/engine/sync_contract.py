"""Millisecond sync contract: search tolerance is NOT edit tolerance.

V1's lesson, stated as code: ~50 ms turns a great sync into a visibly weak
one. The matcher may hunt across +/-750 ms because DISCOVERY is a different
problem from PLACEMENT. Once a candidate is chosen, "approximately on the
beat" stops being an acceptable answer.

So this module never reports MATCHED. It reports a SIGNED DELTA in
milliseconds, plus the tier that delta earns, plus the sync class that
decided which thresholds applied.

WHY THE CLASS MATTERS. A phrase boundary is a region you arrive in; a
rocket impact is a frame that either lands on the transient or does not.
Holding both to +/-15 ms would reject usable structural placements, and
holding both to +/-500 ms would let a 49 ms miss on a hero impact be
described as placed. Both failures have happened in this project, so the
thresholds are per class and the class is recorded in the result.

WHAT IS AUTHORITATIVE. Gameplay evidence. Music moves, gameplay does not.
Nothing here can shift a HIT, FRAG, DODGE or LG contact to manufacture a
match -- the API only ever returns a music-side adjustment.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from typing import Any

SYNC_SCHEMA_VERSION = 1

# ── sync classes ────────────────────────────────────────────────────────────
# HARD: a specific frame must land on a specific transient.
# PHRASE: arrival inside a musical region; a region has width, a frame does not.
CLASS_HARD = "HARD_SYNC"
CLASS_PHRASE = "PHRASE_PLACEMENT"
SYNC_CLASSES = (CLASS_HARD, CLASS_PHRASE)

# ── tiers (directive C) ─────────────────────────────────────────────────────
# Editorial starting thresholds, not physical laws. The user may override
# any of them after watching; that override is recorded, not argued with.
TIER_TARGET = "TARGET"
TIER_GOOD = "GOOD"
TIER_REVIEW = "REVIEW"
TIER_BAD = "BAD"
TIERS = (TIER_TARGET, TIER_GOOD, TIER_REVIEW, TIER_BAD)

HARD_THRESHOLDS_MS = ((15.0, TIER_TARGET), (25.0, TIER_GOOD),
                      (40.0, TIER_REVIEW))
# A phrase is arrived in, not struck. One bar at 128 BPM is ~1875 ms, so a
# quarter-bar is the tightest claim a BAR_GRID_ESTIMATE actually supports.
PHRASE_THRESHOLDS_MS = ((120.0, TIER_TARGET), (250.0, TIER_GOOD),
                        (500.0, TIER_REVIEW))

# ── event priority (directive F) ────────────────────────────────────────────
# PRIMARY events deserve the musical punch. Weapon FIRE deliberately is not
# one of them: the shot leaving the barrel is not the moment the viewer feels.
PRIMARY_EVENTS = ("FRAG", "DIRECT_HIT", "RAIL_HIT", "PROJECTILE_IMPACT",
                  "ROCKET_IMPACT", "DODGE_CLOSEST_APPROACH", "COUNTERFRAG",
                  "CLUTCH_PAYOFF", "ROUND_WIN", "MULTIKILL_PAYOFF",
                  "LG_BURST", "LG_HERO_CONTACT")
SECONDARY_EVENTS = ("MOVEMENT_PEAK", "PROJECTILE_LAUNCH", "WEAPON_FIRE",
                    "CAMERA_TRANSITION")

# The matcher's discovery budget. Kept deliberately wide and deliberately
# separate from the tiers above (directive P).
SEARCH_TOLERANCE_MS = 750.0


def classify_delta(delta_ms: float, sync_class: str = CLASS_HARD) -> str:
    """Tier for a signed delta. Sign is irrelevant to the tier, not to the fix."""
    if sync_class not in SYNC_CLASSES:
        raise ValueError("unknown sync class: " + str(sync_class))
    table = (HARD_THRESHOLDS_MS if sync_class == CLASS_HARD
             else PHRASE_THRESHOLDS_MS)
    magnitude = abs(float(delta_ms))
    for limit, tier in table:
        if magnitude <= limit:
            return tier
    return TIER_BAD


def is_primary(event_type: str) -> bool:
    return str(event_type).upper() in PRIMARY_EVENTS


@dataclass(frozen=True)
class SyncMeasurement:
    """One game event measured against one musical event.

    Every field the directive asks to be stored and displayed, and no
    field that merely says "matched".
    """
    game_event: str
    music_event: str
    game_edit_us: int
    music_us: int
    resolved_edit_us: int      # where the music event lands on the edit clock
    sync_class: str = CLASS_HARD
    stage: str = "PLAN"        # PLAN | RENDERED | POST_ENCODE

    def __post_init__(self) -> None:
        if self.sync_class not in SYNC_CLASSES:
            raise ValueError("unknown sync class: " + str(self.sync_class))
        for name in ("game_edit_us", "music_us", "resolved_edit_us"):
            v = getattr(self, name)
            if not isinstance(v, int) or isinstance(v, bool):
                raise ValueError(name + " must be an int (microseconds)")

    @property
    def signed_delta_us(self) -> int:
        """Positive means the MUSIC lands after the game event."""
        return self.resolved_edit_us - self.game_edit_us

    @property
    def signed_delta_ms(self) -> float:
        return round(self.signed_delta_us / 1000.0, 2)

    @property
    def tier(self) -> str:
        return classify_delta(self.signed_delta_ms, self.sync_class)

    @property
    def acceptable(self) -> bool:
        return self.tier in (TIER_TARGET, TIER_GOOD)

    @property
    def primary(self) -> bool:
        return is_primary(self.game_event)

    def describe(self) -> str:
        """One line a human can read without decoding a score."""
        sign = "+" if self.signed_delta_us >= 0 else ""
        return (f"{self.game_event} <-> {self.music_event}  "
                f"{sign}{self.signed_delta_ms} ms  [{self.tier}]"
                f"{'' if self.primary else '  (secondary)'}")

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(signed_delta_us=self.signed_delta_us,
                 signed_delta_ms=self.signed_delta_ms,
                 tier=self.tier, primary=self.primary,
                 acceptable=self.acceptable)
        return d


@dataclass(frozen=True)
class SyncPayoff:
    """What the musical payoff actually IS (directive M).

    A hero treatment that cannot name its payoff is not finished, so the
    text is required rather than optional. "scene matched score 0.82" is
    not a payoff and this type cannot express one.
    """
    payoff: str
    measurement: SyncMeasurement

    def __post_init__(self) -> None:
        text = str(self.payoff).strip()
        if len(text) < 12:
            raise ValueError(
                "name the musical payoff concretely -- 'rocket impact lands "
                "on the snare transient', not a score")
        if "score" in text.lower() and "0." in text:
            raise ValueError("a score is not a payoff")


@dataclass(frozen=True)
class SyncCorrection:
    """Algorithm suggestion vs human-approved placement (directive P, Q).

    The matcher's recommendation is NEVER mutated. Both are kept so the
    difference can be learned from later; nothing here retrains anything.
    """
    event_type: str
    music_event_type: str
    track_hash: str
    region_start_us: int
    matcher_placement_us: int
    editorial_placement_us: int
    original_delta_ms: float
    final_delta_ms: float
    scene_profile: str = ""
    sync_class: str = CLASS_HARD

    @property
    def manual_adjustment_us(self) -> int:
        return self.editorial_placement_us - self.matcher_placement_us

    @property
    def manual_adjustment_ms(self) -> float:
        return round(self.manual_adjustment_us / 1000.0, 2)

    @property
    def improved(self) -> bool:
        return abs(self.final_delta_ms) < abs(self.original_delta_ms)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(manual_adjustment_us=self.manual_adjustment_us,
                 manual_adjustment_ms=self.manual_adjustment_ms,
                 improved=self.improved,
                 original_tier=classify_delta(self.original_delta_ms,
                                              self.sync_class),
                 final_tier=classify_delta(self.final_delta_ms,
                                           self.sync_class))
        return d


# ── nudge (directive L) ─────────────────────────────────────────────────────
# The steps the editor exposes. Fine enough to walk 42 ms down to 12 ms
# without fighting the UI.
NUDGE_STEPS_MS = (-10, -5, -1, 1, 5, 10)


def nudge_placement(placement, delta_ms: int):
    """Move the music by whole milliseconds, gameplay untouched.

    ``delta_ms`` is expressed in the SAME SIGN as the reported delta: +10
    makes the musical event arrive 10 ms LATER on the edit clock. So a
    measurement reading "+9 ms" is corrected by clicking -10, which is what
    a person reading the number expects. Internally that means moving the
    source window the other way, and getting this backwards is precisely
    the kind of thing that makes an editor feel like it is fighting you
    (directive L).

    Returns a NEW MusicPlacement. Only the music side can move: there is
    deliberately no equivalent that shifts a game event (directive E).
    """
    if not isinstance(delta_ms, int) or isinstance(delta_ms, bool):
        raise ValueError("nudge is in whole milliseconds")
    from creative_suite.engine.scene_recipe import MusicPlacement
    shift = -delta_ms * 1000
    return MusicPlacement(
        track_id=placement.track_id,
        source_start_us=placement.source_start_us + shift,
        program_edit_start_us=placement.program_edit_start_us,
        source_end_us=(None if placement.source_end_us is None
                       else placement.source_end_us + shift))


def measure_against_placement(*, game_event: str, game_edit_us: int,
                              music_event: str, music_us: int,
                              placement, sync_class: str = CLASS_HARD,
                              stage: str = "PLAN") -> SyncMeasurement:
    """Where a musical event lands on the edit clock, and by how much it misses.

    Inverts ``MusicPlacement.edit_to_music`` rather than re-deriving it, so
    this can never disagree with the mapping the renderer uses.
    """
    resolved = (music_us - placement.source_start_us
                + placement.program_edit_start_us)
    return SyncMeasurement(game_event=game_event, music_event=music_event,
                           game_edit_us=int(game_edit_us),
                           music_us=int(music_us),
                           resolved_edit_us=int(resolved),
                           sync_class=sync_class, stage=stage)


def best_nudge(measurement: SyncMeasurement, placement,
               steps_ms=NUDGE_STEPS_MS) -> int:
    """The step that most reduces |delta|, or 0 when none helps.

    Only whole-millisecond steps the editor actually offers are considered,
    so the suggestion is always something the user can reproduce by clicking.
    """
    best, best_abs = 0, abs(measurement.signed_delta_ms)
    for step in steps_ms:
        moved = nudge_placement(placement, step)
        candidate = measure_against_placement(
            game_event=measurement.game_event,
            game_edit_us=measurement.game_edit_us,
            music_event=measurement.music_event,
            music_us=measurement.music_us, placement=moved,
            sync_class=measurement.sync_class, stage=measurement.stage)
        if abs(candidate.signed_delta_ms) < best_abs:
            best, best_abs = step, abs(candidate.signed_delta_ms)
    return best


def fine_align(placement, *, game_edit_us: int, music_events,
               max_shift_us: int = 750_000):
    """Shift the MUSIC so the nearest musical event lands ON the game event.

    This is the PLACEMENT half of directive P: the matcher searched broadly
    to find the region, and this puts the chosen moment where it belongs.
    Only the music moves (directive E), and the shift is bounded by the same
    budget the search used, so fine alignment can never smuggle in a
    different region.

    Returns ``(new_placement, shift_us)``; shift 0 when nothing is close
    enough to reach without leaving the region.
    """
    if not music_events:
        return placement, 0
    target_music = placement.edit_to_music(int(game_edit_us))
    nearest = min(music_events, key=lambda m: abs(int(m) - target_music))
    shift = int(nearest) - target_music     # move source window by this much
    if abs(shift) > max_shift_us:
        return placement, 0
    # +shift, not -shift. We want edit_to_music(game_edit_us) to equal the
    # chosen musical event, and edit_to_music is source_start + edit -
    # program_edit_start, so source_start must MOVE TOWARDS the event. The
    # inverted sign lands roughly half a beat out and still reports a
    # plausible-looking REVIEW tier, which is how it hides.
    from creative_suite.engine.scene_recipe import MusicPlacement
    return MusicPlacement(
        track_id=placement.track_id,
        source_start_us=placement.source_start_us + shift,
        program_edit_start_us=placement.program_edit_start_us,
        source_end_us=(None if placement.source_end_us is None
                       else placement.source_end_us + shift)), shift


def report(measurements) -> dict[str, Any]:
    """A summary that refuses to hide a bad primary sync in an average."""
    ms = list(measurements)
    primaries = [m for m in ms if m.primary]
    worst_primary = max(primaries, key=lambda m: abs(m.signed_delta_ms),
                        default=None)
    return {
        "count": len(ms),
        "primary_count": len(primaries),
        "tiers": {t: sum(1 for m in ms if m.tier == t) for t in TIERS},
        "worst_primary_ms": (None if worst_primary is None
                             else worst_primary.signed_delta_ms),
        "worst_primary": (None if worst_primary is None
                          else worst_primary.describe()),
        "all_primary_acceptable": all(m.acceptable for m in primaries),
        "lines": [m.describe() for m in ms],
    }
