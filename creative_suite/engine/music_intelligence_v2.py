"""Gameplay-semantic music profiles and structure-aware region scoring."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Iterable, Mapping, Sequence

from creative_suite.engine.music_features_v2 import (
    MusicEventV2,
    MusicFeatureV2,
    MusicRegionV2,
)

__all__ = ["MusicEventV2", "SceneMusicProfile", "RegionScore",
           "derive_scene_music_profile", "energy_shape_fit", "score_region",
           "select_diverse_matches", "match_catalog", "top10_overlap"]


@dataclass(frozen=True)
class SceneMusicProfile:
    dominant_type: str
    scene_type_weights: tuple[tuple[str, float], ...]
    duration_us: int
    hero_anchor_us: int
    secondary_anchor_us: tuple[int, ...]
    hit_cadence_us: tuple[int, ...]
    frag_cadence_us: tuple[int, ...]
    projectile_flights_us: tuple[int, ...]
    hit_bursts: tuple[tuple[int, int, int], ...]
    clutch_progression_us: tuple[int, ...]
    round_win_us: int | None
    desired_energy_shape: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RegionScore:
    total: float
    components: tuple[tuple[str, float], ...]
    music_anchor_us: int
    signed_delta_us: int

    def component_dict(self) -> dict[str, float]:
        return dict(self.components)


def _bursts(times: Sequence[int], gap_us: int = 250_000) -> tuple[tuple[int, int, int], ...]:
    if not times:
        return ()
    ordered = sorted(set(int(x) for x in times))
    groups: list[list[int]] = [[ordered[0]]]
    for value in ordered[1:]:
        if value - groups[-1][-1] > gap_us:
            groups.append([])
        groups[-1].append(value)
    return tuple((group[0], group[-1], len(group)) for group in groups)


def _gaps(values: Iterable[int]) -> tuple[int, ...]:
    ordered = sorted(set(values))
    return tuple(b - a for a, b in zip(ordered, ordered[1:]))


def derive_scene_music_profile(evidence: Mapping[str, Any]) -> SceneMusicProfile:
    duration = int(evidence.get("duration_us") or 0)
    excluded_types = set(evidence.get("excluded_event_types") or ())
    excluded_ranges = [tuple(map(int, x)) for x in evidence.get("excluded_edit_ranges") or ()]
    anchors = []
    for raw in evidence.get("anchors") or ():
        kind, value = str(raw.get("kind", "")), int(raw["edit_us"])
        if kind in excluded_types or any(start <= value < end for start, end in excluded_ranges):
            continue
        anchors.append((kind, value))
    classes = set(evidence.get("classes") or ())
    weapon = str(evidence.get("weapon") or "")
    projectile = bool(evidence.get("projectile_flights_us")) or weapon in {
        "ROCKET", "ROCKET_SPLASH", "GRENADE", "GRENADE_SPLASH"}
    tracking = weapon == "LIGHTNING" or any(name.startswith("LG_") for name in classes)
    clutch = any(name.startswith("CLUTCH_") or name in {"LAST_MAN_SEQUENCE", "ROUND_SAVE"}
                 for name in classes)
    weights = {
        "IMPACT_PROJECTILE": .78 if projectile else .08,
        "RHYTHMIC_TRACKING": .88 if tracking else .08,
        "TENSION_RELEASE": .95 if clutch else .08,
    }
    dominant = max(weights, key=weights.get)
    if dominant == "TENSION_RELEASE":
        desired = (.25, .5, .8, 1.0, .35)
    elif dominant == "RHYTHMIC_TRACKING":
        desired = (.75, .85, .85, .9, .8)
    else:
        desired = (.25, .35, .55, 1.0, .45)
    round_wins = [value for kind, value in anchors if kind == "ROUND_WIN"]
    if round_wins:
        hero = round_wins[-1]
    else:
        preferred = [value for kind, value in anchors if kind in {"PROJECTILE_IMPACT", "FRAG"}]
        hero = preferred[-1] if preferred else (anchors[-1][1] if anchors else duration // 2)
    secondary = tuple(value for kind, value in anchors
                      if value != hero and kind not in {"PROJECTILE_LAUNCH"})
    frags = [value for kind, value in anchors if kind == "FRAG"]
    contacts = tuple(map(int, evidence.get("contact_times_us") or ()))
    return SceneMusicProfile(
        dominant, tuple(sorted(weights.items())), duration, hero, secondary,
        _gaps(contacts), _gaps(frags),
        tuple(map(int, evidence.get("projectile_flights_us") or ())),
        _bursts(contacts), tuple(frags), round_wins[-1] if round_wins else None,
        desired,
    )


def _resample(values: Sequence[float], count: int) -> tuple[float, ...]:
    if not values:
        return (0.0,) * count
    if len(values) == 1:
        return (float(values[0]),) * count
    out = []
    for i in range(count):
        pos = i * (len(values) - 1) / max(1, count - 1)
        lo, hi = int(math.floor(pos)), int(math.ceil(pos))
        frac = pos - lo
        out.append(float(values[lo]) * (1 - frac) + float(values[hi]) * frac)
    return tuple(out)


def energy_shape_fit(scene_shape: Sequence[float], music_shape: Sequence[float]) -> float:
    if not scene_shape or not music_shape:
        return 0.0
    a, b = _resample(scene_shape, 9), _resample(music_shape, 9)
    def normalize(x: Sequence[float]) -> tuple[float, ...]:
        lo, hi = min(x), max(x)
        if hi - lo < 1e-9:
            return (0.5,) * len(x)
        return tuple((v - lo) / (hi - lo) for v in x)
    na, nb = normalize(a), normalize(b)
    error = sum(abs(x - y) for x, y in zip(na, nb)) / len(na)
    if max(b) - min(b) < .05 and max(a) - min(a) >= .2:
        error = max(error, .55)
    return round(max(0.0, 1.0 - error), 6)


def _curve_values(curve: Sequence[tuple[int, float]], start: int, end: int) -> tuple[float, ...]:
    return tuple(float(value) for clock, value in curve if start <= clock <= end)


def _nearest_event(feature: MusicFeatureV2, target: int,
                   allowed: set[str]) -> MusicEventV2 | None:
    events = [event for event in feature.salient_events if event.event_type in allowed]
    return min(events, key=lambda event: abs(event.music_us - target)) if events else None


def _cadence_fit(game_gaps: Sequence[int], music_events: Sequence[MusicEventV2]) -> float:
    if not game_gaps or len(music_events) < 2:
        return .5 if not game_gaps else 0.0
    music_gaps = _gaps(event.music_us for event in music_events)
    n = min(len(game_gaps), len(music_gaps))
    if not n:
        return 0.0
    g, m = game_gaps[:n], music_gaps[:n]
    scale = sum(g) / max(1, sum(m))
    error = sum(abs(a - b * scale) / max(1, a) for a, b in zip(g, m)) / n
    return max(0.0, 1.0 - error)


def score_region(profile: SceneMusicProfile, feature: MusicFeatureV2,
                 region: MusicRegionV2) -> RegionScore:
    region_duration = region.end_us - region.start_us
    relative_hero = profile.hero_anchor_us / max(1, profile.duration_us)
    target = region.start_us + round(region_duration * relative_hero)
    event = _nearest_event(feature, target, {"ACCENT", "STAB", "BELL", "VOCAL_ENTRY",
                                             "DROP_CANDIDATE", "BEAT"})
    music_anchor = event.music_us if event else target
    delta = music_anchor - target
    accent = 0.0 if event is None else max(0.0, event.strength) * (event.confidence or .5)
    phrase_clocks = (*feature.phrase_boundary_estimates_us,
                     *feature.section_boundary_estimates_us)
    phrase = 0.0 if not phrase_clocks else max(
        0.0, 1.0 - min(abs(region.start_us - x) for x in phrase_clocks) / 4_000_000)
    energy = _curve_values(feature.energy_curve, region.start_us, region.end_us)
    shape = energy_shape_fit(profile.desired_energy_shape, energy)
    onset = _curve_values(feature.onset_curve, region.start_us, region.end_us)
    rhythm = min(1.0, len([x for x in onset if x >= .5]) / max(1, region_duration / 1_000_000 * 2))
    sustain = 0.0 if not energy else max(0.0, 1.0 - (max(energy) - min(energy)))
    cadence = _cadence_fit(profile.hit_cadence_us or profile.frag_cadence_us,
                            [x for x in feature.salient_events if region.start_us <= x.music_us <= region.end_us])
    kind = region.kind
    structure = {
        "IMPACT_PROJECTILE": 1.0 if kind in {"BUILD_CANDIDATE", "DROP_CANDIDATE"} else .15,
        "RHYTHMIC_TRACKING": 1.0 if kind == "HIGH_ENERGY_REGION" else .25,
        "TENSION_RELEASE": 1.0 if kind in {"BUILD_CANDIDATE", "BREAKDOWN_CANDIDATE",
                                             "DROP_CANDIDATE"} else .2,
    }[profile.dominant_type]
    duration_fit = min(region_duration, profile.duration_us) / max(
        1, max(region_duration, profile.duration_us))
    anchor_fit = max(0.0, 1.0 - abs(delta) / 2_000_000)
    components = {
        "anchor_fit": anchor_fit,
        "rhythm_fit": rhythm,
        "cadence_fit": cadence,
        "energy_shape_fit": shape,
        "phrase_fit": phrase,
        "structure_fit": structure,
        "duration_fit": duration_fit,
        "diversity_adjustment": 0.0,
        "alignment_cost": 0.0,
    }
    if profile.dominant_type == "IMPACT_PROJECTILE":
        total = (.29*anchor_fit + .08*rhythm + .04*cadence + .22*shape +
                 .10*phrase + .18*structure + .09*duration_fit)
    elif profile.dominant_type == "RHYTHMIC_TRACKING":
        total = (.12*anchor_fit + .25*rhythm + .24*cadence + .16*sustain +
                 .05*phrase + .11*structure + .07*duration_fit)
    else:
        total = (.18*anchor_fit + .06*rhythm + .14*cadence + .25*shape +
                 .12*phrase + .17*structure + .08*duration_fit)
    return RegionScore(round(total, 6), tuple((k, round(v, 6)) for k, v in components.items()),
                       music_anchor, delta)


def select_diverse_matches(matches: Sequence[Mapping[str, Any]], *, limit: int = 3,
                           tolerance: float = .06) -> list[Mapping[str, Any]]:
    ordered = sorted(matches, key=lambda row: (-float(row["total"]),
                                               str(row["track_hash"]),
                                               int(row["region_start_us"])))
    if not ordered:
        return []
    selected, used = [ordered[0]], {ordered[0]["track_hash"]}
    floor = float(ordered[0]["total"]) - tolerance
    for row in ordered[1:]:
        if len(selected) >= limit:
            break
        if row["track_hash"] not in used and float(row["total"]) >= floor:
            selected.append(row); used.add(row["track_hash"])
    for row in ordered[1:]:
        if len(selected) >= limit:
            break
        if row not in selected:
            selected.append(row)
    return selected


def match_catalog(profile: SceneMusicProfile, features: Sequence[MusicFeatureV2],
                  *, top_n: int = 20) -> list[dict[str, Any]]:
    max_alignment_us = 750_000
    rows: list[dict[str, Any]] = []
    for feature in features:
        for region in feature.regions:
            result = score_region(profile, feature, region)
            # A region is the natural editorial start. We may nudge it only
            # within a small, explicit budget; residual error remains visible.
            desired_shift = result.music_anchor_us - profile.hero_anchor_us - region.start_us
            alignment_shift = max(-max_alignment_us,
                                  min(max_alignment_us, desired_shift))
            source_start = region.start_us + alignment_shift
            if source_start < 0 or source_start + profile.duration_us > feature.duration_us:
                continue
            aligned_delta = (result.music_anchor_us - source_start) - profile.hero_anchor_us
            alignment_cost = abs(alignment_shift) / max_alignment_us
            components = result.component_dict()
            components["anchor_fit"] = round(
                max(0.0, 1.0 - abs(aligned_delta) / 2_000_000), 6)
            components["alignment_cost"] = round(alignment_cost, 6)
            total = max(0.0, result.total - .08 * alignment_cost)
            rows.append({
                "track_hash": feature.track_hash, "track_path": feature.path,
                "profile_type": profile.dominant_type, "region_kind": region.kind,
                "region_start_us": region.start_us, "region_end_us": region.end_us,
                "music_anchor_us": result.music_anchor_us,
                "music_source_start_us": source_start,
                "hero_edit_us": profile.hero_anchor_us,
                "intrinsic_event_delta_us": result.signed_delta_us,
                "alignment_shift_us": alignment_shift,
                "alignment_cost": round(alignment_cost, 6),
                "aligned_delta_us": aligned_delta, "total": round(total, 6),
                "components": components,
            })
    rows.sort(key=lambda row: (-row["total"], row["track_hash"], row["region_start_us"]))
    return rows[:top_n]


def top10_overlap(result_sets: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    tracks = {name: {str(row["track_hash"]) for row in rows[:10]}
              for name, rows in result_sets.items()}
    names = sorted(tracks)
    pairs = {f"{a}__{b}": len(tracks[a] & tracks[b])
             for i, a in enumerate(names) for b in names[i+1:]}
    all_common = len(set.intersection(*(tracks[name] for name in names))) if names else 0
    return {"pairwise_track_overlap": pairs, "all_three_track_overlap": all_common}
