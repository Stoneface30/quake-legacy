"""What an episode is FOR, and which songs can carry that story.

EPISODE 1 IS NOT PART 1. It is an initiation: someone who has never watched
Quake should finish it knowing what this project is, that the play is worth
respecting, roughly how Clan Arena works, why coordinated team rounds are
different, and that the whole thing is a tribute. A highlight reel does none
of that, and no amount of frag quality substitutes for it.

WHY THIS AFFECTS SONG CHOICE. A story with six beats needs a song with room
for six beats: space to open in, an early payoff so the viewer stays, a
calmer stretch where something can be explained, a rebuild, a climax and an
ending that resolves rather than stops. A technically excellent song with no
breathing room cannot carry an explainer, however good its drops are. So the
episode's intent is an input to song selection, not a decoration applied
afterwards.

SONG PROFILES KEEP THEIR COMPONENTS. A profile says what a song offers --
intro space, hero potential, montage potential, outro -- as separate readings
with the evidence behind them. The single number exists only to sort.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Sequence

from creative_suite.engine import score_timeline as st
from creative_suite.engine import opportunity_graph as og

EPISODE_VERSION = "episode-intent-v1.0.0"

# ── narrative beats ─────────────────────────────────────────────────────────

PROJECT_INTRO = "PROJECT_INTRO"
ACTION_PROOF = "ACTION_PROOF"
CA_EXPLAINER = "CA_EXPLAINER"
TEAMPLAY = "TEAMPLAY"
HERO = "HERO"
QUAKE_TRIBUTE = "QUAKE_TRIBUTE"

NARRATIVE_BEATS = (PROJECT_INTRO, ACTION_PROOF, CA_EXPLAINER, TEAMPLAY, HERO,
                   QUAKE_TRIBUTE)

# What kind of gameplay each beat wants, and what musical shape suits it.
BEAT_WANTS: dict[str, tuple[str, ...]] = {
    PROJECT_INTRO: (og.KIND_MOVEMENT,),
    ACTION_PROOF: (og.KIND_ROCKET_IMPACT, og.KIND_RAIL_HIT, og.KIND_MULTIKILL),
    CA_EXPLAINER: (og.KIND_TEAM_ROUND, og.KIND_ONE_V_X, og.KIND_LG_TRACKING),
    TEAMPLAY: (og.KIND_TEAM_ROUND,),
    HERO: (og.KIND_MULTIKILL, og.KIND_ONE_V_X, og.KIND_ROCKET_IMPACT),
    QUAKE_TRIBUTE: (og.KIND_MOVEMENT, og.KIND_TEAM_ROUND),
}

BEAT_SLOT_ROLES: dict[str, tuple[str, ...]] = {
    PROJECT_INTRO: (st.SLOT_INTRO,),
    ACTION_PROOF: (st.SLOT_HERO, st.SLOT_CLIMAX, st.SLOT_MOVEMENT),
    CA_EXPLAINER: (st.SLOT_BREATH, st.SLOT_TRACKING, st.SLOT_SETUP),
    TEAMPLAY: (st.SLOT_BUILD, st.SLOT_MOVEMENT, st.SLOT_TRACKING),
    HERO: (st.SLOT_CLIMAX, st.SLOT_HERO, st.SLOT_MULTIKILL),
    QUAKE_TRIBUTE: (st.SLOT_OUTRO,),
}


@dataclass(frozen=True)
class NarrativeBeatPlacement:
    """One story beat, occupying a real interval of the score."""
    beat: str
    score_start_us: int
    score_end_us: int
    wants: tuple[str, ...] = ()
    why: str = ""

    def __post_init__(self) -> None:
        if self.beat not in NARRATIVE_BEATS:
            raise ValueError(f"unknown narrative beat {self.beat!r}")
        if self.score_end_us <= self.score_start_us:
            raise ValueError("a narrative beat needs positive duration")

    @property
    def duration_us(self) -> int:
        return self.score_end_us - self.score_start_us

    def contains(self, us: int) -> bool:
        return self.score_start_us <= us < self.score_end_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["wants"] = list(self.wants)
        d["duration_us"] = self.duration_us
        return d


@dataclass(frozen=True)
class EpisodeIntent:
    """What this episode is trying to do to the person watching it."""
    name: str
    purpose: str
    beats: tuple[str, ...]
    notes: str = ""
    version: str = EPISODE_VERSION

    def __post_init__(self) -> None:
        for b in self.beats:
            if b not in NARRATIVE_BEATS:
                raise ValueError(f"unknown narrative beat {b!r}")
        if not self.beats:
            raise ValueError("an episode needs at least one narrative beat")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["beats"] = list(self.beats)
        return d


EPISODE_1_INITIATION = EpisodeIntent(
    name="EPISODE_1_INITIATION",
    purpose="initiate a spectator who may never have watched Quake: establish "
            "the project, prove the play is worth respecting, teach just "
            "enough Clan Arena to make the skill legible, show why "
            "coordinated team rounds are different, let PANTHEON show what it "
            "can do, and resolve on the reason any of it exists: a tribute "
            "to Quake",
    beats=(PROJECT_INTRO, ACTION_PROOF, CA_EXPLAINER, TEAMPLAY, HERO,
           QUAKE_TRIBUTE),
    notes="not Part 1. The explainer must teach through compelling gameplay, "
          "never become a tutorial. The ending resolves on the tribute.")


def project_narrative(intent: EpisodeIntent, timeline: st.ScoreTimelineV1,
                      slots: Sequence[st.ScoreSlot]
                      ) -> tuple[NarrativeBeatPlacement, ...]:
    """Lay the story's beats across the song, in order, using its own shape.

    Each beat claims the next stretch of score, preferring slots whose role
    suits it. A beat never runs backwards and the last one always reaches the
    end, because the film ends when the song does.
    """
    if not slots:
        return ()
    out: list[NarrativeBeatPlacement] = []
    cursor = 0
    remaining = list(intent.beats)
    for i, beat in enumerate(remaining):
        last = i == len(remaining) - 1
        wanted_roles = BEAT_SLOT_ROLES.get(beat, ())
        candidates = [s for s in slots
                      if s.start_us >= cursor and s.role in wanted_roles]
        if last:
            end = timeline.duration_us
            start = (candidates[0].start_us if candidates else
                     max(cursor, timeline.duration_us -
                         max(1, timeline.duration_us // len(remaining))))
            start = min(start, end - 1)
        elif candidates:
            slot = candidates[0]
            start, end = max(cursor, slot.start_us), slot.end_us
        else:
            span = max(1, (timeline.duration_us - cursor) //
                       max(1, len(remaining) - i))
            start, end = cursor, min(timeline.duration_us, cursor + span)
        if end <= start:
            continue
        why = (f"placed on the next {'/'.join(wanted_roles).lower()} slot"
               if candidates else
               "no slot of the preferred kind was free; placed in order")
        out.append(NarrativeBeatPlacement(beat, start, end,
                                          BEAT_WANTS.get(beat, ()), why))
        cursor = end
    return tuple(out)


# ── song profiles ───────────────────────────────────────────────────────────

PROFILE_DIMENSIONS = ("INTRO_POTENTIAL", "HERO_POTENTIAL", "LG_POTENTIAL",
                      "DODGE_POTENTIAL", "MOVEMENT_POTENTIAL",
                      "MONTAGE_POTENTIAL", "TRANSITION_POTENTIAL",
                      "MOTIF_GESTURE_POTENTIAL", "SPECTACLE_POTENTIAL",
                      "OUTRO_POTENTIAL")


@dataclass(frozen=True)
class SongScoreProfileV1:
    """What creative opportunities a song actually offers."""
    track_hash: str
    duration_us: int
    dimensions: tuple[tuple[str, float], ...]
    episode_fit: tuple[tuple[str, float], ...] = ()
    grid_status: str = "UNKNOWN"
    notes: str = ""

    def value(self, name: str) -> float:
        return dict(self.dimensions).get(name, 0.0)

    def fit_for(self, episode_name: str) -> float:
        return dict(self.episode_fit).get(episode_name, 0.0)

    @property
    def headline(self) -> str:
        """The single strongest thing this song offers."""
        if not self.dimensions:
            return "no readings"
        name, value = max(self.dimensions, key=lambda kv: kv[1])
        return f"{name} {value:.2f}"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dimensions"] = {k: v for k, v in self.dimensions}
        d["episode_fit"] = {k: v for k, v in self.episode_fit}
        d["headline"] = self.headline
        return d


def _clip(x: float) -> float:
    return round(min(1.0, max(0.0, float(x))), 4)


def profile_song(timeline: st.ScoreTimelineV1, slots: Sequence[st.ScoreSlot],
                 *, gestures: Sequence[Any] = (),
                 grid_status: str = "UNKNOWN") -> SongScoreProfileV1:
    """Read a song's creative offer from its own structure."""
    total = max(1, timeline.duration_us)

    def share(roles: Sequence[str]) -> float:
        return sum(s.duration_us for s in slots if s.role in roles) / total

    hard = sum(s.evidence.hard_anchor_count for s in slots)
    quiet = [s for s in slots if s.evidence.mean_energy <= 0.35]
    dense = [s for s in slots if s.evidence.percussive_density_per_s >= 1.5]
    first = slots[0] if slots else None
    last = slots[-1] if slots else None

    dims = {
        "INTRO_POTENTIAL": _clip(
            (first.duration_us / 20_000_000 if first else 0.0) *
            (1.2 - min(1.0, first.evidence.mean_energy) if first else 0.0)),
        "HERO_POTENTIAL": _clip(hard / 12.0),
        "LG_POTENTIAL": _clip(sum(s.duration_us for s in quiet) / total * 3.0),
        "DODGE_POTENTIAL": _clip(share((st.SLOT_BUILD,)) * 4.0),
        "MOVEMENT_POTENTIAL": _clip(share((st.SLOT_MOVEMENT,)) * 2.5),
        "MONTAGE_POTENTIAL": _clip(len(dense) / 4.0),
        "TRANSITION_POTENTIAL": _clip(len(slots) / 12.0),
        "MOTIF_GESTURE_POTENTIAL": _clip(len(gestures) / 8.0),
        "SPECTACLE_POTENTIAL": _clip(
            share((st.SLOT_CLIMAX, st.SLOT_HERO)) * 3.0),
        "OUTRO_POTENTIAL": _clip(
            (last.duration_us / 25_000_000 if last else 0.0)),
    }
    # Episode 1 needs ALL of its beats to have somewhere to live, so its fit
    # is the weakest link rather than the average: a song with a huge climax
    # and no breathing room cannot carry an explainer.
    needed = (dims["INTRO_POTENTIAL"], dims["HERO_POTENTIAL"],
              dims["LG_POTENTIAL"], dims["SPECTACLE_POTENTIAL"],
              dims["OUTRO_POTENTIAL"])
    fit = _clip(min(needed))
    return SongScoreProfileV1(
        track_hash=timeline.track_hash, duration_us=timeline.duration_us,
        dimensions=tuple(sorted(dims.items())),
        episode_fit=((EPISODE_1_INITIATION.name, fit),),
        grid_status=grid_status,
        notes="episode fit is the weakest required dimension, not an average: "
              "every narrative beat needs somewhere to live")
