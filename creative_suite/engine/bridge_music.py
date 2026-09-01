"""Music strategy for a scene transition (directive 1-7).

CONSUMES Music Intelligence V2 and analyses nothing. No matcher, no
feature extractor, no cache is built here: ``music_features_v2.db``
(396 tracks, ``semantic-region-matcher@2.0.0``) is read, and
``music_intelligence_v2.match_catalog`` does the scoring exactly as it
does for a single scene.

THE QUESTION THIS MODULE ANSWERS. A transition spans two scenes, so the
music can either run straight through it (CONTINUOUS) or change at it
(STRUCTURED). Those are different editorial claims and they need
different evidence, so both are computed and reported side by side. This
module deliberately does NOT say which is better -- it has no ears. The
numbers are for a human to listen against.

THE THREE CLOCKS ARE UNCHANGED. A bridge is scored in the SEQUENCE edit
clock: Scene A's own ``edit_us`` up to the cut, then Scene B's own
``edit_us`` offset by the cut. ``MusicPlacement.edit_to_music`` remains
the only edit->music mapping. Nothing here introduces a fourth clock.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from creative_suite.engine.music_features_v2 import (MusicFeatureV2,
                                                     MusicFeatureStore)
from creative_suite.engine.music_intelligence_v2 import (
    derive_scene_music_profile, match_catalog)
from creative_suite.engine.scene_recipe import MusicPlacement
from creative_suite.engine import transition_recipe as tr

REPO_ROOT = Path(__file__).resolve().parents[2]
MUSIC_DB = REPO_ROOT / "creative_suite" / "database" / "music_features_v2.db"

# How close a music change has to land to a phrase/section estimate before
# it counts as structurally placed rather than arbitrary. One bar at a
# typical 128 BPM is ~1.875 s; half a bar is the tightest claim the
# BAR_GRID_ESTIMATE provenance actually supports, so 500 ms is a
# deliberately conservative "on the boundary" bar.
STRUCTURAL_TOLERANCE_US = 500_000


@dataclass(frozen=True)
class BridgeSegment:
    """One scene's contribution to the bridge, in sequence edit time."""
    label: str
    seq_start_us: int
    seq_end_us: int
    launch_us: int          # sequence clock
    impact_us: int          # sequence clock

    @property
    def duration_us(self) -> int:
        return self.seq_end_us - self.seq_start_us


def bridge_segments(transition: tr.SceneTransition, *,
                    scene_a_track, scene_b_track,
                    a_lead_us: int, b_tail_us: int) -> tuple[BridgeSegment,
                                                             BridgeSegment]:
    """Lay the two scenes onto one sequence clock across the cut.

    Scene A contributes ``a_lead_us`` of run-up ending exactly on its
    impact (the cut). Scene B starts at its own launch and runs
    ``b_tail_us`` past its impact.
    """
    a_anchors = tr.resolve_projectile_anchors(scene_a_track)
    b_anchors = tr.resolve_projectile_anchors(scene_b_track)
    if not a_anchors or not b_anchors:
        raise ValueError("both scenes need a usable projectile track")
    a_impact = a_anchors[tr.A_IMPACT]
    a_start = max(0, a_impact - a_lead_us)
    cut_seq = a_impact - a_start                      # cut in sequence time
    b_launch, b_impact = b_anchors[tr.B_LAUNCH], b_anchors[tr.B_HERO]
    b_len = (b_impact - b_launch) + b_tail_us
    a = BridgeSegment("SCENE_A", 0, cut_seq,
                      launch_us=max(0, a_anchors[tr.A_LAUNCH] - a_start),
                      impact_us=cut_seq)
    b = BridgeSegment("SCENE_B", cut_seq, cut_seq + b_len,
                      launch_us=cut_seq,
                      impact_us=cut_seq + (b_impact - b_launch))
    return a, b


def _evidence(duration_us: int, anchors: list[tuple[str, int]],
              flights_us: tuple[int, ...], weapon: str = "ROCKET") -> dict:
    return {"duration_us": duration_us, "weapon": weapon,
            "classes": ["DIRECT_ROCKET"],
            "projectile_flights_us": list(flights_us),
            "anchors": [{"kind": k, "edit_us": v} for k, v in anchors]}


def _nearest(values, target: int) -> int | None:
    """Signed delta to the nearest value, or None when there are none."""
    if not values:
        return None
    best = min(values, key=lambda v: abs(v - target))
    return best - target


def _energy_at(feature: MusicFeatureV2, music_us: int) -> float | None:
    if not feature.energy_curve:
        return None
    return min(feature.energy_curve, key=lambda p: abs(p[0] - music_us))[1]


def _accent_delta(feature: MusicFeatureV2, music_us: int) -> int | None:
    accents = [e.music_us for e in feature.salient_events
               if e.event_type in {"ACCENT", "STAB", "DROP_CANDIDATE",
                                   "BELL", "VOCAL_ENTRY"}]
    return _nearest(accents, music_us)


def strategy_continuous(a: BridgeSegment, b: BridgeSegment,
                        features: list[MusicFeatureV2], *,
                        top_n: int = 5) -> list[dict[str, Any]]:
    """One region carries Scene A, the cut and Scene B (directive 3).

    The bridge is profiled as a single scene whose hero anchor is Scene
    B's impact -- the payoff the whole transition is travelling towards.
    """
    total = b.seq_end_us
    anchors = [("PROJECTILE_LAUNCH", a.launch_us),
               ("PROJECTILE_IMPACT", a.impact_us),
               ("PROJECTILE_LAUNCH", b.launch_us),
               ("PROJECTILE_IMPACT", b.impact_us)]
    flights = (a.impact_us - a.launch_us, b.impact_us - b.launch_us)
    profile = derive_scene_music_profile(_evidence(total, anchors, flights))
    return match_catalog(profile, features, top_n=top_n)


def strategy_structured(a: BridgeSegment, b: BridgeSegment,
                        features: list[MusicFeatureV2], *,
                        top_n: int = 5) -> dict[str, Any]:
    """Region A carries Scene A; a different region takes over at the cut.

    Both halves are matched independently, then the Scene B candidates
    are re-ranked by how close their region start sits to a phrase or
    section boundary estimate -- structure first, so the change reads as
    musical rather than as a crossfade dropped on top of a cut.
    """
    a_profile = derive_scene_music_profile(_evidence(
        a.duration_us, [("PROJECTILE_LAUNCH", a.launch_us),
                        ("PROJECTILE_IMPACT", a.impact_us)],
        (a.impact_us - a.launch_us,)))
    b_local_launch = b.launch_us - b.seq_start_us
    b_local_impact = b.impact_us - b.seq_start_us
    b_profile = derive_scene_music_profile(_evidence(
        b.duration_us, [("PROJECTILE_LAUNCH", b_local_launch),
                        ("PROJECTILE_IMPACT", b_local_impact)],
        (b_local_impact - b_local_launch,)))
    a_rows = match_catalog(a_profile, features, top_n=top_n)
    b_rows = match_catalog(b_profile, features, top_n=top_n * 4)
    by_hash = {f.track_hash: f for f in features}
    for row in b_rows:
        feature = by_hash[row["track_hash"]]
        clocks = (*feature.phrase_boundary_estimates_us,
                  *feature.section_boundary_estimates_us)
        delta = _nearest(clocks, int(row["music_source_start_us"]))
        row["phrase_boundary_delta_us"] = delta
        row["structurally_placed"] = (
            delta is not None and abs(delta) <= STRUCTURAL_TOLERANCE_US)
    b_rows.sort(key=lambda r: (not r["structurally_placed"],
                               abs(r.get("phrase_boundary_delta_us") or 10**9),
                               -r["total"]))
    return {"scene_a": a_rows, "scene_b": b_rows[:top_n]}


def placement_for(row: dict[str, Any], program_edit_start_us: int,
                  duration_us: int) -> MusicPlacement:
    """A MusicPlacement for a matcher row, in the caller's edit clock."""
    start = int(row["music_source_start_us"])
    return MusicPlacement(track_id=str(row["track_hash"]),
                          source_start_us=start,
                          program_edit_start_us=int(program_edit_start_us),
                          source_end_us=start + int(duration_us))


def evidence_report(a: BridgeSegment, b: BridgeSegment,
                    row: dict[str, Any], feature: MusicFeatureV2, *,
                    program_edit_start_us: int = 0) -> dict[str, Any]:
    """Objective, listen-against numbers for one candidate (directive 6).

    Deliberately contains no judgement. BPM is reported with its
    confidence because the migrated catalog carries BAR_GRID_ESTIMATE
    provenance rather than measured beats for most tracks.
    """
    duration = b.seq_end_us - a.seq_start_us
    place = placement_for(row, program_edit_start_us, duration)
    cut_music_us = place.edit_to_music(a.impact_us)
    hero_music_us = place.edit_to_music(b.impact_us)
    clocks = (*feature.phrase_boundary_estimates_us,
              *feature.section_boundary_estimates_us)
    return {
        "track_hash": row["track_hash"][:16],
        "region_kind": row["region_kind"],
        "region_us": [int(row["region_start_us"]), int(row["region_end_us"])],
        "music_source_start_us": int(row["music_source_start_us"]),
        "music_us_at_cut": cut_music_us,
        "music_us_at_hero": hero_music_us,
        "cut_accent_delta_us": _accent_delta(feature, cut_music_us),
        "hero_accent_delta_us": _accent_delta(feature, hero_music_us),
        "cut_phrase_delta_us": _nearest(clocks, cut_music_us),
        "energy_before_cut": _energy_at(feature, cut_music_us - 500_000),
        "energy_after_cut": _energy_at(feature, cut_music_us + 500_000),
        "energy_at_hero": _energy_at(feature, hero_music_us),
        "bpm": feature.bpm,
        "bpm_confidence": feature.bpm_confidence,
        "aligned_delta_us": int(row["aligned_delta_us"]),
        "alignment_shift_us": int(row["alignment_shift_us"]),
        "total": row["total"],
        "components": row["components"],
    }


def load_features(db_path: Path | None = None) -> list[MusicFeatureV2]:
    """The catalog, read-only. Raises if the store is missing."""
    path = Path(db_path or MUSIC_DB)
    if not path.exists():
        raise FileNotFoundError(f"music feature store not found: {path}")
    return MusicFeatureStore(path).all_features()
