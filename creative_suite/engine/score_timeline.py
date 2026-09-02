"""The song is the score: a fixed musical canvas the movie is composed into.

THE INVERSION. Until now a Part had a target length and music was found that
could survive inside it. That is backwards, and it is the reason so much
effort went into making a song "fit". Here the song is chosen first, its
duration IS the movie's duration, and every scene, camera, retime, transition
and effect is cast into the musical opportunities that already exist.

A 3:47.328 song makes a 3:47.328 movie. Not five minutes because a Part
template said so. The only eligibility rule is a sane maximum length.

THE CLOCKS ARE NOT REPLACED. SceneRecipeV2's chain is untouched:

    demo_us --TimeMap--> edit_us --MusicPlacement--> music_us

This module adds ONE axis above them, at sequence level: the score. For a
song-locked sequence the score and the edit playhead run 1:1 --
`score_us == edit_us` -- because the movie starts when the song starts and
ends when it ends. `edit_us` remains the canonical render playhead; the score
is the PLANNING axis. Two names for one line, kept explicit so nobody has to
guess which one a number belongs to.

WHAT A SLOT IS, AND IS NOT. A ScoreSlot is a projection: an interval of music
that could accept a certain kind of material, with the evidence that made us
think so. It is editorial planning, never musical ground truth, and it never
collapses to a single score -- a slot says its duration, its energy shape,
its onset and percussive density, its negative space and its hard anchors, so
a human can disagree with the label while keeping the measurements.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import hashlib
import json
from typing import Any, Sequence

import numpy as np

SCORE_SCHEMA_VERSION = 1
SCORE_TIMELINE_VERSION = "score-timeline-v1.0.0"

# Eligibility. Long songs make long movies that lose the room; this is a
# configurable ceiling, not a law of music.
DEFAULT_MAX_SONG_US = 6 * 60 * 1_000_000
DEFAULT_MIN_SONG_US = 60 * 1_000_000

# ── slot roles ──────────────────────────────────────────────────────────────

SLOT_INTRO = "INTRO"
SLOT_BREATH = "BREATH"
SLOT_SETUP = "SETUP"
SLOT_TRACKING = "TRACKING"
SLOT_MOVEMENT = "MOVEMENT"
SLOT_BUILD = "BUILD"
SLOT_HERO = "HERO"
SLOT_MULTIKILL = "MULTIKILL"
SLOT_MONTAGE = "MONTAGE"
SLOT_CLIMAX = "CLIMAX"
SLOT_TRANSITION = "TRANSITION"
SLOT_OUTRO = "OUTRO"

SLOT_ROLES = (SLOT_INTRO, SLOT_BREATH, SLOT_SETUP, SLOT_TRACKING,
              SLOT_MOVEMENT, SLOT_BUILD, SLOT_HERO, SLOT_MULTIKILL,
              SLOT_MONTAGE, SLOT_CLIMAX, SLOT_TRANSITION, SLOT_OUTRO)

# ── editorial intensity ─────────────────────────────────────────────────────
# Nonstop spectacle is the fastest way to make spectacle ordinary. The curve
# exists so the extraordinary moments have something to be extraordinary
# against.

INTENSITY_RESTRAINT = "RESTRAINT"
INTENSITY_NORMAL = "NORMAL"
INTENSITY_HERO = "HERO"
INTENSITY_SPECTACLE = "SPECTACLE"
INTENSITIES = (INTENSITY_RESTRAINT, INTENSITY_NORMAL, INTENSITY_HERO,
               INTENSITY_SPECTACLE)
INTENSITY_RANK = {name: i for i, name in enumerate(INTENSITIES)}

SPECTACLE_SATURATION = "SPECTACLE_SATURATION"
# Consecutive high-attention slots before contrast is missing.
SATURATION_RUN = 3


class SongNotEligible(ValueError):
    pass


# ── eligibility ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SongEligibility:
    """Whether a track may be used as a score, and why."""
    track_hash: str
    duration_us: int
    eligible: bool
    reasons: tuple[str, ...]
    # Non-blocking facts a planner must know. The cached V2 beat grids are
    # truncated across this library (median coverage ~0.41), so a slot's beat
    # count is meaningless past the end of the grid and must not be read as
    # "this section has no beats".
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def raise_if_ineligible(self) -> None:
        if not self.eligible:
            raise SongNotEligible("; ".join(self.reasons))


def check_eligibility(feature: Any, *, max_us: int = DEFAULT_MAX_SONG_US,
                      min_us: int = DEFAULT_MIN_SONG_US) -> SongEligibility:
    """A score needs a known length and real analysis behind it."""
    reasons: list[str] = []
    dur = int(getattr(feature, "duration_us", 0) or 0)
    if dur <= 0:
        reasons.append("duration unknown")
    if dur > max_us:
        reasons.append(f"{dur / 6e7:.2f} min exceeds the {max_us / 6e7:.0f} "
                       f"minute ceiling")
    if 0 < dur < min_us:
        reasons.append(f"{dur / 1e6:.1f}s is too short to score a movie")
    if len(getattr(feature, "beats_us", ()) or ()) < 32:
        reasons.append("no usable beat grid")
    if not getattr(feature, "extractor_version", ""):
        reasons.append("no analysis provenance")
    if not getattr(feature, "regions", ()) and not getattr(
            feature, "section_boundary_estimates_us", ()):
        reasons.append("no usable musical structure")
    warnings: list[str] = []
    beats = tuple(getattr(feature, "beats_us", ()) or ())
    if beats and dur:
        coverage = max(beats) / dur
        if coverage < 0.9:
            warnings.append(
                f"beat grid covers only {coverage:.0%} of the track; beat and "
                f"subdivision evidence is absent past {max(beats) / 1e6:.0f}s")
    return SongEligibility(str(getattr(feature, "track_hash", "")), dur,
                           not reasons, tuple(reasons), tuple(warnings))


# ── the score axis ──────────────────────────────────────────────────────────

def _squash(name: str) -> str:
    """Letters and digits only, lowercased. Punctuation is not identity."""
    return "".join(c for c in str(name).lower() if c.isalnum())


def resolve_track_path(feature: Any, library_root: Any) -> Any:
    """Find the real file for a cached feature. Name matching alone is a trap.

    The cache stores a normalised slug ("240_kmh__ven_pa_ca.mp3"); the file on
    disk is "240_KM_H__VEN_PA'_CA.mp3". They differ in case, punctuation AND
    underscore placement, so an exact-name lookup silently finds nothing --
    which reads downstream as "this song contains no musical events at all",
    the most dangerous kind of empty result.

    Three attempts, most trustworthy first, and the caller is told which one
    succeeded so a weak match is never mistaken for a strong one:

        EXACT_PATH     the recorded name exists
        CONTENT_HASH   a file whose SHA-256 is the track hash
        SQUASHED_NAME  letters and digits agree, uniquely
    """
    from pathlib import Path as _Path
    from creative_suite.engine.music_features_v2 import MusicFeatureStore
    root = _Path(library_root)
    want_hash = str(getattr(feature, "track_hash", ""))
    recorded = _Path(str(getattr(feature, "path", ""))).name

    exact = root / recorded
    if exact.exists():
        return exact

    files = sorted(root.rglob("*.mp3"))
    for candidate in files:
        try:
            if MusicFeatureStore.full_content_hash(candidate) == want_hash:
                return candidate
        except OSError:
            continue

    target = _squash(_Path(recorded).stem)
    matches = [f for f in files if _squash(f.stem) == target]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise FileNotFoundError(
            f"{recorded!r} matches {len(matches)} library files by name; "
            f"refusing to guess")
    raise FileNotFoundError(
        f"no file in {root} matches {recorded!r} by path, content hash "
        f"({want_hash[:12]}) or normalised name")


def resolution_method(feature: Any, library_root: Any) -> str:
    """Which of the three lookups found the file. Provenance, not decoration."""
    from pathlib import Path as _Path
    from creative_suite.engine.music_features_v2 import MusicFeatureStore
    root = _Path(library_root)
    recorded = _Path(str(getattr(feature, "path", ""))).name
    if (root / recorded).exists():
        return "EXACT_PATH"
    resolved = resolve_track_path(feature, library_root)
    try:
        if MusicFeatureStore.full_content_hash(resolved) == str(
                getattr(feature, "track_hash", "")):
            return "CONTENT_HASH"
    except OSError:
        pass
    return "SQUASHED_NAME"


def score_to_edit(score_us: int) -> int:
    """Score and edit run 1:1 for a song-locked sequence.

    Written out rather than implied so that a future non-1:1 case (a movie
    that does not start on the first sample of the song) has one place to
    change, and so no reader has to guess which axis a number is on.
    """
    return int(score_us)


def edit_to_score(edit_us: int) -> int:
    return int(edit_us)


@dataclass(frozen=True)
class NegativeSpaceInterval:
    """A stretch where the music makes room."""
    start_us: int
    end_us: int
    percussive_drop_db: float
    return_db: float
    shape: str

    @property
    def duration_us(self) -> int:
        return self.end_us - self.start_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["duration_us"] = self.duration_us
        return d


@dataclass(frozen=True)
class ScoreTimelineV1:
    """One song, projected into the immutable canvas of a movie."""
    track_hash: str
    track_path: str
    duration_us: int
    bpm: float | None
    beats_us: tuple[int, ...]
    bars_us: tuple[int, ...]
    phrases_us: tuple[int, ...]
    sections_us: tuple[int, ...]
    energy_curve: tuple[tuple[int, float], ...]
    anchors: tuple[Any, ...] = ()               # MusicalAnchorV3
    negative_space: tuple[NegativeSpaceInterval, ...] = ()
    schema_version: int = SCORE_SCHEMA_VERSION
    timeline_version: str = SCORE_TIMELINE_VERSION
    provenance: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.duration_us <= 0:
            raise ValueError("a score needs a real duration")
        if self.schema_version != SCORE_SCHEMA_VERSION:
            raise ValueError("unsupported score schema")

    @property
    def duration_s(self) -> float:
        return self.duration_us / 1e6

    @property
    def timecode(self) -> str:
        s = self.duration_s
        return f"{int(s // 60)}:{s % 60:06.3f}"

    @property
    def beat_grid_coverage(self) -> float:
        """How much of the song the cached beat grid actually spans."""
        if not self.beats_us or not self.duration_us:
            return 0.0
        return round(max(self.beats_us) / self.duration_us, 4)

    def grid_covers(self, us: int) -> bool:
        return bool(self.beats_us) and us <= max(self.beats_us)

    def subdivisions_us(self) -> tuple[int, ...]:
        """Midpoints between beats. Only where a beat grid exists."""
        b = sorted(self.beats_us)
        return tuple((x + y) // 2 for x, y in zip(b, b[1:]))

    def energy_at(self, us: int) -> float:
        if not self.energy_curve:
            return 0.0
        pts = sorted(self.energy_curve)
        best = min(pts, key=lambda p: abs(p[0] - us))
        return float(best[1])

    def mean_energy(self, a_us: int, b_us: int) -> float:
        vals = [v for t, v in self.energy_curve if a_us <= t < b_us]
        return float(np.mean(vals)) if vals else 0.0

    def anchors_in(self, a_us: int, b_us: int) -> list[Any]:
        return [x for x in self.anchors
                if a_us <= x.perceptual_anchor_us < b_us]

    def hard_anchors_in(self, a_us: int, b_us: int) -> list[Any]:
        """Anchors sharp enough to carry a hero payoff."""
        return [x for x in self.anchors_in(a_us, b_us)
                if x.attack_class == "FAST" and x.pcenter_confidence >= 0.6]

    def to_dict(self) -> dict[str, Any]:
        return {"track_hash": self.track_hash, "track_path": self.track_path,
                "duration_us": self.duration_us, "bpm": self.bpm,
                "beats": len(self.beats_us), "bars": len(self.bars_us),
                "phrases": len(self.phrases_us),
                "sections": len(self.sections_us),
                "anchors": len(self.anchors),
                "beat_grid_coverage": self.beat_grid_coverage,
                "negative_space": [n.to_dict() for n in self.negative_space],
                "schema_version": self.schema_version,
                "timeline_version": self.timeline_version,
                "provenance": [list(kv) for kv in self.provenance]}


def build_timeline(feature: Any, *, anchors: Sequence[Any] = (),
                   negative_space: Sequence[NegativeSpaceInterval] = (),
                   grid: Any = None,
                   max_us: int = DEFAULT_MAX_SONG_US) -> ScoreTimelineV1:
    """Project a cached V2 feature (plus V3 anchors) into a score.

    A repaired ``grid`` supersedes the cached beats entirely. It also
    supersedes the cached DURATION when it measured the audio and found the
    cached value wrong -- a score built on a wrong duration produces a movie
    of the wrong length, which is the one thing this architecture cannot get
    away with.
    """
    check_eligibility(feature, max_us=max_us).raise_if_ineligible()
    beats = tuple(int(b) for b in feature.beats_us)
    bars = tuple(int(b) for b in feature.bar_grid_estimate_us)
    duration_us = int(feature.duration_us)
    bpm = feature.bpm
    prov_extra: tuple[tuple[str, str], ...] = ()
    if grid is not None:
        beats = tuple(int(b) for b in grid.beats_us) or beats
        bars = tuple(int(b) for b in grid.bars_us) or bars
        bpm = grid.bpm or bpm
        prov_extra = (("beat_grid", grid.analyzer_version),
                      ("beat_grid_status", grid.status))
        measured = int(getattr(grid, "audio_duration_us", 0) or 0)
        if measured and getattr(grid, "duration_suspect", False):
            prov_extra += (("duration_source",
                            f"measured audio {measured} us supersedes cached "
                            f"{duration_us} us"),)
            duration_us = measured
    return ScoreTimelineV1(
        track_hash=feature.track_hash, track_path=feature.path,
        duration_us=duration_us, bpm=bpm,
        beats_us=beats,
        bars_us=bars,
        phrases_us=tuple(int(b) for b in feature.phrase_boundary_estimates_us),
        sections_us=tuple(int(b) for b in feature.section_boundary_estimates_us),
        energy_curve=tuple((int(t), float(v)) for t, v in feature.energy_curve),
        anchors=tuple(anchors), negative_space=tuple(negative_space),
        provenance=(("features", feature.extractor_version),
                    ("timeline", SCORE_TIMELINE_VERSION)) + prov_extra)


# ── slots ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SlotEvidence:
    """Why a slot is the kind of slot it claims to be.

    Never reduced to one number: a planner that only sees a score cannot
    explain itself, and an editor cannot argue with it.
    """
    duration_us: int
    mean_energy: float
    energy_shape: str                # RISING | FALLING | FLAT
    onset_density_per_s: float
    percussive_density_per_s: float
    hard_anchor_count: int
    negative_space_us: int
    beat_count: int
    beat_grid_covered: bool
    structural_role: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScoreSlot:
    """An interval of music that could accept material, and why."""
    start_us: int
    end_us: int
    role: str
    evidence: SlotEvidence
    intensity: str = INTENSITY_NORMAL
    desired_event_count: int | None = None      # MONTAGE only
    cadence_us: int | None = None               # MONTAGE only
    note: str = ""

    def __post_init__(self) -> None:
        if self.role not in SLOT_ROLES:
            raise ValueError(f"unknown slot role {self.role!r}")
        if self.intensity not in INTENSITIES:
            raise ValueError(f"unknown intensity {self.intensity!r}")
        if self.end_us <= self.start_us:
            raise ValueError("a slot must have positive duration")

    @property
    def duration_us(self) -> int:
        return self.end_us - self.start_us

    def contains(self, us: int) -> bool:
        return self.start_us <= us < self.end_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["evidence"] = self.evidence.to_dict()
        d["duration_us"] = self.duration_us
        return d


def _energy_shape(timeline: ScoreTimelineV1, a: int, b: int) -> str:
    pts = [v for t, v in timeline.energy_curve if a <= t < b]
    if len(pts) < 3:
        return "FLAT"
    third = max(1, len(pts) // 3)
    head, tail = float(np.mean(pts[:third])), float(np.mean(pts[-third:]))
    if head <= 0:
        return "RISING" if tail > 0 else "FLAT"
    ratio = tail / head
    return "RISING" if ratio >= 1.25 else "FALLING" if ratio <= 0.8 else "FLAT"


def slot_evidence(timeline: ScoreTimelineV1, a: int, b: int, *,
                  structural_role: str = "NONE") -> SlotEvidence:
    span_s = max(1e-6, (b - a) / 1e6)
    anchors = timeline.anchors_in(a, b)
    perc = [x for x in anchors if x.component == "PERCUSSIVE"]
    ns = sum(n.duration_us for n in timeline.negative_space
             if n.start_us >= a and n.end_us <= b)
    return SlotEvidence(
        duration_us=b - a,
        mean_energy=round(timeline.mean_energy(a, b), 4),
        energy_shape=_energy_shape(timeline, a, b),
        onset_density_per_s=round(len(anchors) / span_s, 3),
        percussive_density_per_s=round(len(perc) / span_s, 3),
        hard_anchor_count=len(timeline.hard_anchors_in(a, b)),
        negative_space_us=ns,
        beat_count=sum(1 for x in timeline.beats_us if a <= x < b),
        beat_grid_covered=timeline.grid_covers(b),
        structural_role=structural_role)


def _role_for(ev: SlotEvidence, *, is_first: bool, is_last: bool) -> str:
    """Label a section by what it offers, not by where it sits.

    Deliberately simple and explainable. The planner is allowed to be wrong
    here -- the evidence travels with the slot so a human can relabel it.
    """
    if is_first:
        return SLOT_INTRO
    if is_last:
        return SLOT_OUTRO
    dur_s = ev.duration_us / 1e6
    if ev.mean_energy <= 0.18 and ev.onset_density_per_s < 1.5:
        return SLOT_BREATH
    if ev.energy_shape == "RISING":
        return SLOT_BUILD
    if ev.percussive_density_per_s >= 3.0 and dur_s <= 6.0:
        return SLOT_MONTAGE
    if ev.hard_anchor_count >= 2 and ev.mean_energy >= 0.45:
        return SLOT_HERO
    if ev.mean_energy >= 0.45:
        return SLOT_MOVEMENT
    if dur_s >= 8.0 and ev.onset_density_per_s < 3.0:
        return SLOT_TRACKING
    return SLOT_SETUP


def _intensity_for(role: str, ev: SlotEvidence) -> str:
    if role in (SLOT_BREATH, SLOT_INTRO, SLOT_OUTRO):
        return INTENSITY_RESTRAINT
    if role == SLOT_CLIMAX:
        return INTENSITY_SPECTACLE
    if role in (SLOT_HERO, SLOT_MULTIKILL):
        return INTENSITY_HERO
    if role == SLOT_BUILD and ev.energy_shape == "RISING":
        return INTENSITY_NORMAL
    return INTENSITY_NORMAL


def derive_slots(timeline: ScoreTimelineV1, *,
                 min_slot_us: int = 2_000_000) -> tuple[ScoreSlot, ...]:
    """Cut the score at its own section boundaries and describe each piece."""
    bounds = sorted({0, *[int(x) for x in timeline.sections_us
                          if 0 < x < timeline.duration_us],
                     timeline.duration_us})
    if len(bounds) < 2:
        bounds = [0, timeline.duration_us]
    slots: list[ScoreSlot] = []
    for i, (a, b) in enumerate(zip(bounds, bounds[1:])):
        if b - a < min_slot_us:
            continue
        ev = slot_evidence(timeline, a, b, structural_role="SECTION")
        role = _role_for(ev, is_first=(i == 0),
                         is_last=(b >= timeline.duration_us))
        slot = ScoreSlot(a, b, role, ev, intensity=_intensity_for(role, ev))
        if role == SLOT_MONTAGE:
            beats = [x for x in timeline.beats_us if a <= x < b]
            cadence = (int(np.median(np.diff(beats))) if len(beats) > 2
                       else None)
            slot = ScoreSlot(a, b, role, ev, intensity=slot.intensity,
                             desired_event_count=min(16, max(4, len(beats))),
                             cadence_us=cadence,
                             note="distinct short moments sharing a motif")
        slots.append(slot)
    # The loudest hero slot becomes the climax: the film needs one peak.
    heroes = [s for s in slots if s.role == SLOT_HERO]
    if heroes:
        top = max(heroes, key=lambda s: s.evidence.mean_energy)
        slots = [ScoreSlot(s.start_us, s.end_us, SLOT_CLIMAX, s.evidence,
                           INTENSITY_SPECTACLE, s.desired_event_count,
                           s.cadence_us, "highest-energy hero section")
                 if s is top else s for s in slots]
    return tuple(slots)


# ── intensity curve ─────────────────────────────────────────────────────────

def intensity_curve(slots: Sequence[ScoreSlot]) -> tuple[tuple[int, str], ...]:
    """The advisory shape of the film: where to hold back and where to hit."""
    return tuple((s.start_us, s.intensity) for s in slots)


def spectacle_saturation(slots: Sequence[ScoreSlot], *,
                         run: int = SATURATION_RUN) -> list[dict[str, Any]]:
    """Warn where nothing is ordinary enough to make the peaks land.

    Advisory, never a hard rule: a deliberate climax is allowed to be a run
    of spectacle, and only a human can say whether this one is deliberate.
    """
    out: list[dict[str, Any]] = []
    streak: list[ScoreSlot] = []
    for s in list(slots) + [None]:                     # type: ignore[list-item]
        high = s is not None and s.intensity in (INTENSITY_HERO,
                                                 INTENSITY_SPECTACLE)
        if high:
            streak.append(s)                            # type: ignore[arg-type]
            continue
        if len(streak) >= run:
            out.append({"check": SPECTACLE_SATURATION, "severity": "WARN",
                        "start_us": streak[0].start_us,
                        "end_us": streak[-1].end_us,
                        "detail": f"{len(streak)} consecutive high-intensity "
                                  f"slots with no contrast between them"})
        streak = []
    return out
