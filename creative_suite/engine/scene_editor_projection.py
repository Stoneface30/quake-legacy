"""Read-only projection that feeds the Scene Editor's unified timeline.

THREE CLOCKS, NEVER COLLAPSED (§19-20)
======================================

    demo_us  --TimeMap-->  edit_us  --MusicPlacement-->  music_us

``edit_us`` is the ONE authoritative playhead and it is signed integer
microseconds everywhere in this module. Float seconds exist only in the
browser, for drawing. Nothing here rounds to milliseconds except where an
engine command genuinely needs milliseconds, and that conversion is done at
the point of use, never stored back.

Each lane originates in exactly one clock and is projected onto ``edit_us``:

* GAME EVENTS originate in ``demo_us``  (recognition evidence).
* TIME / CAMERA / FX / LOOK operate in ``edit_us`` (they *are* the edit).
* MUSIC WAVEFORM / EVENTS / STRUCTURE originate in ``music_us``.

Because every projection is a pure function of (TimeMap, MusicPlacement),
dragging music moves ONLY the music lanes — gameplay timing is bit-identical
(§29, §35). That property is what makes A/B/C switching honest (§38).

HONESTY (§31)
=============
``beats[::4]`` is a BAR_GRID_ESTIMATE, not a measured downbeat, and it keeps
the ``_ESTIMATE`` suffix here and in the browser. ``bpm_confidence`` and
``beat_confidence`` are ``None`` for every migrated track in the catalog;
they are surfaced as ``None`` and rendered as "unavailable". This module
never substitutes a default so a gauge can look full.

NOTHING IS RECALCULATED HERE
============================
Region scores come from the matcher's own output
(``semantic-region-matcher@2.0.0``, persisted in the audition manifest).
The waveform envelope is downsampled from the ALREADY CACHED
``energy_curve`` — no audio is decoded, in Python or in the browser.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Sequence

from creative_suite.engine.music_features_v2 import (MusicFeatureStore,
                                                     MusicFeatureV2)
from creative_suite.engine.pantheon_scene import (CameraIntent, FxCue,
                                                  PantheonScene,
                                                  resolve_anchor)
from creative_suite.engine.scene_recipe import (MusicPlacement, SceneRecipeV2,
                                                TimeMap,
                                                build_frag_scene_recipe)

PROJECTION_VERSION = "scene-editor-projection@1.0.0"

# --- lane ids (the browser draws one row per entry, in this order) ---------
LANE_GAME_EVENTS = "GAME_EVENTS"
LANE_TIME = "TIME"
LANE_CAMERA = "CAMERA"
LANE_FX = "FX"
LANE_LOOK = "LOOK"
LANE_MUSIC_WAVEFORM = "MUSIC_WAVEFORM"
LANE_MUSIC_EVENTS = "MUSIC_EVENTS"
LANE_MUSIC_STRUCTURE = "MUSIC_STRUCTURE"
LANE_ORDER = (LANE_GAME_EVENTS, LANE_TIME, LANE_CAMERA, LANE_FX, LANE_LOOK,
              LANE_MUSIC_WAVEFORM, LANE_MUSIC_EVENTS, LANE_MUSIC_STRUCTURE)

# Game-event kinds the lane can show. Each one names the evidence that
# produces it; a kind with no evidence in this scene is reported as
# ``present: False`` rather than invented (§31).
GAME_EVENT_KINDS: tuple[tuple[str, str], ...] = (
    ("FIRE", "recognition_lg_engagements.series.my_fire"),
    ("PROJECTILE_LAUNCH", "recognized_frags.attributes.projectile_launch_t"),
    ("PROJECTILE_IMPACT", "recognized_frags.attributes.projectile_impact_t"),
    ("FRAG", "recognized_frags.server_time_ms"),
    ("LG_CONTACT", "recognition_lg_engagements.series.dealt"),
    ("LG_BURST", "recognition_lg_engagements.series.dealt (grouped)"),
    ("MULTIKILL", "recognized_frags (>=2 in window)"),
    ("DODGE_HERO", "recognition_dodge_events + DODGE_HERO class"),
    ("NEAR_MISS", "recognition_dodge_events.closest_time_ms"),
    ("ROUND_WIN", "recognized_frags.classes (round-win family)"),
    ("MOVEMENT_PEAK", "recognition_view_timeseries angular-rate peak"),
)
# Micro-events: real, but there can be dozens per scene. Off by default so
# the lane reads as an edit, not a log file.
DEFAULT_HIDDEN_EVENT_KINDS = ("LG_CONTACT", "FIRE")

_ROUND_WIN_CLASSES = frozenset({
    "ROUND_WIN", "OUTNUMBERED_ROUND_WIN", "ROUND_SAVE", "ROUND_COMEBACK",
    "LAST_MAN_SEQUENCE", "TEAM_WIPE",
})
_MULTIKILL_PREFIXES = ("MULTIKILL_", "RAPID_MULTIKILL", "HIGH_SPEED_MULTIKILL",
                       "HIGH_DENSITY_MULTIKILL")

# --- music-lane vocabulary. The ``_ESTIMATE`` / ``_CANDIDATE`` suffixes are
# load-bearing and must survive into the UI unchanged (§31).
MUSIC_EVENT_KINDS = ("BEAT", "BAR_GRID_ESTIMATE", "ACCENT", "BUILD_CANDIDATE",
                     "DROP_CANDIDATE", "PHRASE_BOUNDARY_ESTIMATE",
                     "SECTION_BOUNDARY_ESTIMATE")
SNAP_TARGET_KINDS = ("ACCENT", "BEAT", "BAR_GRID_ESTIMATE",
                     "PHRASE_BOUNDARY_ESTIMATE", "DROP_CANDIDATE")

# --- semantic guide pairs (§34). Deliberately short: guides connect HERO
# contacts and BURSTS, never every LG tick, or the panel becomes spaghetti.
GUIDE_PAIRS: tuple[tuple[str, str], ...] = (
    ("PROJECTILE_IMPACT", "ACCENT"),
    ("FRAG", "DROP_CANDIDATE"),
    ("ROUND_WIN", "PHRASE_BOUNDARY_ESTIMATE"),
    ("LG_BURST", "ACCENT"),
    ("DODGE_HERO", "BUILD_CANDIDATE"),
)
MAX_GUIDES = 12

# --- UI state vs recipe state (§52) ---------------------------------------
# Anything in UI_STATE_KEYS is view furniture. It is stored on the draft so a
# reload restores the workspace, and it is PROVABLY absent from both hashes
# (see recipe_state / production_state below, and the hash-exclusion test).
UI_STATE_KEYS = ("zoom", "scroll_us", "expanded_lanes", "panel_widths",
                 "hidden_event_kinds", "snap_enabled", "selected_lane",
                 "selected_item_id", "playhead_us")
RECIPE_STATE_KEYS = ("time_map", "music_placement", "camera_intent",
                     "fx_stack", "visual_look", "transition")


# ===========================================================================
# clock helpers
# ===========================================================================

def music_to_edit(placement: MusicPlacement, music_us: int) -> int:
    """Inverse of ``MusicPlacement.edit_to_music`` — exact, no rounding."""
    if isinstance(music_us, bool) or not isinstance(music_us, int):
        raise TypeError("music_us must be a signed integer microsecond value")
    return placement.program_edit_start_us + music_us - placement.source_start_us


def demo_to_edit_clamped(time_map: TimeMap, demo_us: int, *,
                         bias: str = "left") -> int | None:
    """``demo_us`` -> ``edit_us``, or ``None`` when it is outside the window.

    Bias is ALWAYS explicit: a freeze makes one demo instant map to a whole
    edit interval, and ``TimeMap.demo_to_edit`` refuses to guess.
    """
    try:
        return time_map.demo_to_edit(int(demo_us), bias=bias)
    except ValueError:
        return None


def edit_span_of_demo_span(time_map: TimeMap, demo_start_us: int,
                           demo_end_us: int) -> tuple[int, int] | None:
    """Project a demo interval onto edit time, entering left / leaving right."""
    start = demo_to_edit_clamped(time_map, demo_start_us, bias="left")
    end = demo_to_edit_clamped(time_map, demo_end_us, bias="right")
    if start is None or end is None:
        return None
    return start, max(start, end)


# ===========================================================================
# waveform envelope — downsampled from the CACHED curve, never from audio
# ===========================================================================

# key: (track_hash, extractor_version, buckets) -> envelope
_ENVELOPE_CACHE: dict[tuple[str, str, int], list[list[float]]] = {}
DEFAULT_ENVELOPE_BUCKETS = 900
MAX_ENVELOPE_BUCKETS = 4000


def waveform_envelope(feature: MusicFeatureV2,
                      buckets: int = DEFAULT_ENVELOPE_BUCKETS,
                      *, music_start_us: int | None = None,
                      music_end_us: int | None = None) -> list[list[float]]:
    """Browser-sized ``[min, max]`` envelope built from ``energy_curve``.

    The catalog's cached ``energy_curve`` is already a low-rate summary of
    the decoded audio (~702 points per track). Downsampling it is cheap and
    deterministic; DECODING the mp3 again — here or in the browser — would
    be a second analyzer, which the architecture forbids. The values are the
    energy curve's own units, normalized to 0..1 across the track so the
    lane draws consistently; the raw curve stays authoritative for scoring.

    ``music_start_us`` / ``music_end_us`` restrict the envelope to the slice
    of track that is actually under the picture, at FULL bucket resolution —
    a nine-second scene of a three-minute track deserves nine seconds of
    detail, not nine seconds' share of the whole track's buckets.

    Cached on ``(track_hash, extractor_version, buckets, window)`` so a
    re-extracted track under a new feature version never serves a stale
    envelope.
    """
    if buckets < 1 or buckets > MAX_ENVELOPE_BUCKETS:
        raise ValueError(
            f"buckets must be in 1..{MAX_ENVELOPE_BUCKETS}, got {buckets}")
    start_us = 0 if music_start_us is None else int(music_start_us)
    end_us = feature.duration_us if music_end_us is None else int(music_end_us)
    key = (feature.track_hash, feature.extractor_version, buckets,
           start_us, end_us)
    cached = _ENVELOPE_CACHE.get(key)
    if cached is not None:
        return cached
    curve = feature.energy_curve or feature.loudness_curve
    if not curve or end_us <= start_us:
        result: list[list[float]] = []
        _ENVELOPE_CACHE[key] = result
        return result
    # Normalize against the WHOLE track, so a quiet scene reads as quiet
    # instead of being stretched to fill the lane.
    all_values = [float(v) for _clock, v in curve]
    lo, hi = min(all_values), max(all_values)
    span = hi - lo
    window = [(int(clock), float(v)) for clock, v in curve
              if start_us <= int(clock) <= end_us]
    if not window:
        # Sub-sample-rate window: hold the nearest value rather than
        # returning an empty lane the browser cannot distinguish from
        # "track not analyzed".
        nearest = min(curve, key=lambda cv: abs(int(cv[0]) - start_us))
        window = [(int(nearest[0]), float(nearest[1]))]
    normalized = ([0.0] * len(window) if span < 1e-12
                  else [(v - lo) / span for _clock, v in window])
    out: list[list[float]] = []
    n = len(normalized)
    for i in range(buckets):
        chunk_start = i * n // buckets
        chunk_end = max(chunk_start + 1, (i + 1) * n // buckets)
        chunk = normalized[chunk_start:min(chunk_end, n)] or [normalized[-1]]
        # (min, max) pair — the browser mirrors it around the lane centre.
        out.append([round(min(chunk), 5), round(max(chunk), 5)])
    _ENVELOPE_CACHE[key] = out
    return out


def clear_envelope_cache() -> None:
    """Test hook."""
    _ENVELOPE_CACHE.clear()


# ===========================================================================
# music lanes
# ===========================================================================

def music_events(feature: MusicFeatureV2) -> list[dict[str, Any]]:
    """Every music-clock event, in ``music_us``, with honest kind names."""
    events: list[dict[str, Any]] = []
    for clock in feature.beats_us:
        events.append({"kind": "BEAT", "music_us": int(clock),
                       "strength": None, "confidence": feature.beat_confidence})
    for clock in feature.bar_grid_estimate_us:
        # NOT a measured downbeat. beats[::4] under a constant-tempo
        # assumption; the name says exactly that and must not be shortened.
        events.append({"kind": "BAR_GRID_ESTIMATE", "music_us": int(clock),
                       "strength": None, "confidence": None})
    for event in feature.salient_events:
        kind = event.event_type if event.event_type in MUSIC_EVENT_KINDS \
            else "ACCENT"
        events.append({"kind": kind, "music_us": int(event.music_us),
                       "strength": event.strength,
                       "confidence": event.confidence})
    for clock in feature.phrase_boundary_estimates_us:
        events.append({"kind": "PHRASE_BOUNDARY_ESTIMATE",
                       "music_us": int(clock), "strength": None,
                       "confidence": None})
    for clock in feature.section_boundary_estimates_us:
        events.append({"kind": "SECTION_BOUNDARY_ESTIMATE",
                       "music_us": int(clock), "strength": None,
                       "confidence": None})
    events.sort(key=lambda e: (e["music_us"], e["kind"]))
    return events


def project_music_lane(feature: MusicFeatureV2, placement: MusicPlacement,
                       scene_duration_us: int, *,
                       envelope_buckets: int = DEFAULT_ENVELOPE_BUCKETS
                       ) -> dict[str, Any]:
    """The three music lanes, projected onto ``edit_us``.

    Only rows whose projected ``edit_us`` lands inside ``[0, duration]`` are
    returned — the lane shows what is actually under the picture.
    """
    window_start_music = placement.edit_to_music(0)
    window_end_music = placement.edit_to_music(scene_duration_us)
    # The envelope covers exactly the music under the picture, at full
    # resolution — bucket i spans [start + i*span/n, start + (i+1)*span/n).
    visible = waveform_envelope(feature, envelope_buckets,
                                music_start_us=window_start_music,
                                music_end_us=window_end_music)

    projected_events = []
    for event in music_events(feature):
        edit_us = music_to_edit(placement, event["music_us"])
        if 0 <= edit_us <= scene_duration_us:
            projected_events.append({**event, "edit_us": edit_us})
    structure = []
    for region in feature.regions:
        start = music_to_edit(placement, region.start_us)
        end = music_to_edit(placement, region.end_us)
        if end < 0 or start > scene_duration_us:
            continue
        structure.append({
            "kind": region.kind, "confidence": region.confidence,
            "music_start_us": region.start_us, "music_end_us": region.end_us,
            "edit_start_us": start, "edit_end_us": end,
            "clipped": start < 0 or end > scene_duration_us,
        })
    return {
        "track_hash": feature.track_hash,
        "track_label": Path(feature.path).stem,
        "track_duration_us": feature.duration_us,
        "extractor_version": feature.extractor_version,
        "status": feature.status,
        "bpm": feature.bpm,
        # Not available for migrated tracks. Rendered as "unavailable" —
        # never defaulted to 1.0 so a confidence pill can look healthy.
        "bpm_confidence": feature.bpm_confidence,
        "beat_confidence": feature.beat_confidence,
        "analysis_provenance": [list(x) for x in feature.analysis_provenance],
        "window_music_start_us": window_start_music,
        "window_music_end_us": window_end_music,
        "envelope": visible,
        "envelope_buckets": len(visible),
        "envelope_music_start_us": window_start_music,
        "envelope_music_end_us": window_end_music,
        "envelope_edit_start_us": 0,
        "envelope_edit_end_us": scene_duration_us,
        "events": projected_events,
        "structure": structure,
    }


def snap_targets(music_lane: dict[str, Any]) -> list[dict[str, Any]]:
    """Optional snap candidates (§36) — ALWAYS optional, never enforced.

    Forced alignment is what made 32 tracks saturate at max score in the
    previous matcher. The editor offers these; it does not apply them.
    """
    return [e for e in music_lane["events"] if e["kind"] in SNAP_TARGET_KINDS]


def guide_lines(game_events: Sequence[dict[str, Any]],
                music_lane: dict[str, Any], *,
                limit: int = MAX_GUIDES) -> list[dict[str, Any]]:
    """Semantic connection guides with SIGNED deltas (§34).

    A guide says "this rocket impact sits 18 ms AFTER that accent", which is
    a fact about two projections, not a score. Restricted to hero contacts
    and bursts so an LG scene draws a handful of lines, not two hundred.
    """
    by_kind: dict[str, list[dict[str, Any]]] = {}
    for event in music_lane["events"]:
        by_kind.setdefault(event["kind"], []).append(event)
    guides: list[dict[str, Any]] = []
    for game_kind, music_kind in GUIDE_PAIRS:
        candidates = by_kind.get(music_kind) or []
        if not candidates:
            continue
        for game_event in game_events:
            if game_event["kind"] != game_kind:
                continue
            anchor_edit = game_event["edit_us"]
            nearest = min(candidates,
                          key=lambda e: abs(e["edit_us"] - anchor_edit))
            guides.append({
                "game_kind": game_kind, "music_kind": music_kind,
                "game_edit_us": anchor_edit,
                "music_edit_us": nearest["edit_us"],
                # Signed: positive = the game beat lands AFTER the music one.
                "delta_us": anchor_edit - nearest["edit_us"],
                "game_event_id": game_event["id"],
            })
    guides.sort(key=lambda g: abs(g["delta_us"]))
    return guides[:limit]


# ===========================================================================
# game-event lane — read-only over mined recognition evidence
# ===========================================================================

def _json(value: Any, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def _class_names(raw: Any) -> list[str]:
    return [x.get("name") if isinstance(x, dict) else str(x)
            for x in _json(raw, []) if x]


def _bursts(times: Sequence[int], gap_us: int = 250_000
            ) -> list[tuple[int, int, int]]:
    if not times:
        return []
    ordered = sorted(set(int(x) for x in times))
    groups: list[list[int]] = [[ordered[0]]]
    for value in ordered[1:]:
        if value - groups[-1][-1] > gap_us:
            groups.append([])
        groups[-1].append(value)
    return [(g[0], g[-1], len(g)) for g in groups]


class SceneEvidence:
    """Everything the editor needs about one frag, read once, read-only.

    Both databases are opened ``mode=ro``. This class never writes.
    """

    def __init__(self, frag_id: int, *, frag_db: Path, demo_v2_db: Path):
        self.frag_id = int(frag_id)
        with sqlite3.connect(f"file:{Path(frag_db).as_posix()}?mode=ro",
                             uri=True) as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM recognized_frags WHERE id=?",
                             (self.frag_id,)).fetchone()
            if row is None:
                raise KeyError(f"unknown frag {frag_id}")
            frag = dict(row)
            frag["classes"] = _class_names(frag.get("classes"))
            frag["attributes"] = _json(frag.get("attributes"), {})
            self.frag = frag
            demo_name, t_ms = frag["demo_name"], int(frag["server_time_ms"])
            with sqlite3.connect(
                    f"file:{Path(demo_v2_db).as_posix()}?mode=ro",
                    uri=True) as clips:
                clips.row_factory = sqlite3.Row
                master = clips.execute(
                    "SELECT * FROM generated_clips WHERE demo_name=? AND ? "
                    "BETWEEN capture_start_ms AND capture_end_ms "
                    "ORDER BY generated_clip_id LIMIT 1",
                    (demo_name, t_ms)).fetchone()
            if master:
                self.window_ms = (int(master["capture_start_ms"]),
                                  int(master["capture_end_ms"]))
            else:
                self.window_ms = (t_ms - 4000, t_ms + 3000)
            start_ms, end_ms = self.window_ms
            self.related = [dict(r) for r in db.execute(
                "SELECT id,server_time_ms,weapon_name,classes FROM "
                "recognized_frags WHERE demo_name=? AND server_time_ms "
                "BETWEEN ? AND ? ORDER BY server_time_ms",
                (demo_name, start_ms, end_ms))]
            lg = db.execute(
                "SELECT series FROM recognition_lg_engagements WHERE "
                "demo_name=? AND server_time_ms=?", (demo_name, t_ms)).fetchone()
            self.lg_series = _json(lg[0], {}) if lg else {}
            self.dodges = [dict(r) for r in db.execute(
                "SELECT * FROM recognition_dodge_events WHERE demo_name=? AND "
                "closest_time_ms BETWEEN ? AND ? ORDER BY closest_time_ms",
                (demo_name, start_ms, end_ms))]
            view = db.execute(
                "SELECT samples FROM recognition_view_timeseries WHERE "
                "demo_name=? AND server_time_ms=?", (demo_name, t_ms)).fetchone()
            self.view_samples = _json(view[0], []) if view else []

    def recipe(self) -> SceneRecipeV2:
        payload = dict(self.frag)
        payload["window"] = {"start_ms": self.window_ms[0],
                             "end_ms": self.window_ms[1]}
        return build_frag_scene_recipe(payload)


def game_event_lane(evidence: SceneEvidence, time_map: TimeMap
                    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(events, kind_index). Every event carries its own evidence pointer."""
    frag = evidence.frag
    attrs = frag["attributes"]
    t_ms = int(frag["server_time_ms"])
    events: list[dict[str, Any]] = []
    seen_kinds: set[str] = set()

    def add(kind: str, demo_us: int, *, bias: str = "left",
            end_demo_us: int | None = None, label: str = "",
            detail: dict[str, Any] | None = None,
            source: str = "") -> None:
        edit_us = demo_to_edit_clamped(time_map, demo_us, bias=bias)
        if edit_us is None:
            return
        item: dict[str, Any] = {
            "id": f"{kind.lower()}-{len(events)}", "kind": kind,
            "demo_us": int(demo_us), "edit_us": edit_us,
            "label": label or kind.replace("_", " ").title(),
            "evidence_source": source, "detail": detail or {},
        }
        if end_demo_us is not None:
            span = edit_span_of_demo_span(time_map, demo_us, end_demo_us)
            if span is not None:
                item["edit_end_us"] = span[1]
                item["demo_end_us"] = int(end_demo_us)
        events.append(item)
        seen_kinds.add(kind)

    # --- projectile ------------------------------------------------------
    launch_ms, impact_ms = (attrs.get("projectile_launch_t"),
                            attrs.get("projectile_impact_t"))
    if launch_ms is not None and impact_ms is not None:
        flight_ms = int(attrs.get("projectile_flight_ms") or 0)
        if int(launch_ms) >= int(impact_ms) and flight_ms > 0:
            launch_ms = int(impact_ms) - flight_ms
        add("PROJECTILE_LAUNCH", int(launch_ms) * 1000, bias="left",
            label="Launch", source="attributes.projectile_launch_t",
            detail={"kind": attrs.get("projectile_kind"),
                    "confidence": attrs.get("projectile_path_confidence")})
        add("PROJECTILE_IMPACT", int(impact_ms) * 1000, bias="right",
            label="Impact", source="attributes.projectile_impact_t",
            detail={"status": attrs.get("projectile_status"),
                    "event": attrs.get("projectile_impact_event"),
                    "confidence": attrs.get("projectile_path_confidence")})

    # --- frags in the window --------------------------------------------
    for item in evidence.related:
        is_self = int(item["id"]) == evidence.frag_id
        add("FRAG", int(item["server_time_ms"]) * 1000,
            bias="right" if is_self else "left",
            label=f"Frag · {item['weapon_name'] or '?'}",
            source="recognized_frags.server_time_ms",
            detail={"frag_id": int(item["id"]), "primary": is_self,
                    "weapon": item["weapon_name"]})
    if len(evidence.related) >= 2 or any(
            n.startswith(_MULTIKILL_PREFIXES) for n in frag["classes"]):
        times = sorted(int(x["server_time_ms"]) * 1000
                       for x in evidence.related) or [t_ms * 1000]
        add("MULTIKILL", times[0], bias="left", end_demo_us=times[-1],
            label=f"Multikill ×{len(evidence.related)}",
            source="recognized_frags (>=2 in window)",
            detail={"count": len(evidence.related)})

    # --- LG contacts and bursts -----------------------------------------
    contacts_demo = [(t_ms + int(offset)) * 1000
                     for offset, _dmg in evidence.lg_series.get("dealt", [])]
    for demo_us in contacts_demo:
        add("LG_CONTACT", demo_us, bias="left", label="LG hit",
            source="lg_engagements.series.dealt")
    for start, end, count in _bursts(contacts_demo):
        add("LG_BURST", start, bias="left", end_demo_us=end,
            label=f"LG burst ×{count}",
            source="lg_engagements.series.dealt (grouped @250ms)",
            detail={"contacts": count})
    for offset in evidence.lg_series.get("my_fire", []):
        add("FIRE", (t_ms + int(offset)) * 1000, bias="left", label="Fire",
            source="lg_engagements.series.my_fire")

    # --- dodge / near miss ----------------------------------------------
    hero = "DODGE_HERO" in frag["classes"]
    for dodge in evidence.dodges:
        closest = dodge.get("closest_time_ms")
        if closest is None:
            continue
        detail = {"threat": dodge.get("threat_type"),
                  "closest_units": dodge.get("closest_approach_units"),
                  "velocity_change": dodge.get("recorder_velocity_change"),
                  "method": dodge.get("method")}
        add("NEAR_MISS", int(closest) * 1000, bias="left",
            label=f"Near miss · {dodge.get('threat_type') or '?'}",
            source="recognition_dodge_events.closest_time_ms", detail=detail)
        if hero:
            add("DODGE_HERO", int(closest) * 1000, bias="left",
                label="Dodge (hero)",
                source="recognition_dodge_events + DODGE_HERO class",
                detail={**detail,
                        "quality_score": attrs.get("dodge_quality_score")})

    # --- round win -------------------------------------------------------
    round_win_classes = [n for n in frag["classes"] if n in _ROUND_WIN_CLASSES]
    if round_win_classes:
        add("ROUND_WIN", t_ms * 1000, bias="right", label="Round win",
            source="recognized_frags.classes",
            detail={"classes": round_win_classes})

    # --- movement peak ---------------------------------------------------
    # Derived from the view time series' angular rate. ONE peak, not a
    # per-sample flood, and the detail says exactly what was measured so
    # nobody reads it as a measured player-velocity peak.
    peak = _view_angular_peak(evidence.view_samples)
    if peak is not None:
        offset_ms, rate = peak
        add("MOVEMENT_PEAK", (t_ms + offset_ms) * 1000, bias="left",
            label="Movement peak",
            source="recognition_view_timeseries angular-rate peak",
            detail={"metric": "view_angular_rate_deg_per_s",
                    "value": round(rate, 1)})

    events.sort(key=lambda e: (e["edit_us"], e["kind"]))
    for index, event in enumerate(events):
        event["id"] = f"{event['kind'].lower()}-{index}"
    kind_index = [{"kind": kind, "source": source,
                   "present": kind in seen_kinds,
                   "count": sum(1 for e in events if e["kind"] == kind),
                   "hidden_by_default": kind in DEFAULT_HIDDEN_EVENT_KINDS}
                  for kind, source in GAME_EVENT_KINDS]
    return events, kind_index


def _view_angular_peak(samples: Sequence[Sequence[float]]
                       ) -> tuple[int, float] | None:
    if len(samples) < 2:
        return None
    best: tuple[int, float] | None = None
    for (t0, yaw0, pitch0), (t1, yaw1, pitch1) in zip(samples, samples[1:]):
        dt = (float(t1) - float(t0)) / 1000.0
        if dt <= 0:
            continue
        dyaw = abs((float(yaw1) - float(yaw0) + 180.0) % 360.0 - 180.0)
        dpitch = abs(float(pitch1) - float(pitch0))
        rate = (dyaw * dyaw + dpitch * dpitch) ** 0.5 / dt
        if best is None or rate > best[1]:
            best = (int(t1), rate)
    return best


# ===========================================================================
# time / camera / fx / look lanes
# ===========================================================================

def time_lane(recipe: SceneRecipeV2) -> list[dict[str, Any]]:
    """The ACTUAL TimeMap, as rows the timeline can draw and edit.

    A freeze has ZERO demo duration and POSITIVE edit duration. That is not
    a rendering quirk to work around — it is the whole reason a freeze is
    visible at all, and the lane must show it at its true edit width.
    """
    rows: list[dict[str, Any]] = []
    for index, segment in enumerate(recipe.time_map):
        edit_duration = segment.edit_end_us - segment.edit_start_us
        demo_duration = segment.demo_end_us - segment.demo_start_us
        rows.append({
            "index": index, "kind": segment.kind,
            "demo_start_us": segment.demo_start_us,
            "demo_end_us": segment.demo_end_us,
            "edit_start_us": segment.edit_start_us,
            "edit_end_us": segment.edit_end_us,
            "edit_duration_us": edit_duration,
            "demo_duration_us": demo_duration,
            "rate_num": segment.rate_num, "rate_den": segment.rate_den,
            "rate_label": ("FREEZE" if segment.kind == "freeze"
                           else f"{segment.rate_num}/{segment.rate_den}"),
            "rate_float": (0.0 if segment.rate_den == 0 or segment.kind == "freeze"
                           else segment.rate_num / segment.rate_den),
            # Explicit, so the browser never has to infer it from a ratio.
            "occupies_edit_time": edit_duration > 0,
            "consumes_demo_time": demo_duration > 0,
        })
    return rows


def default_camera_intent(recipe: SceneRecipeV2) -> CameraIntent:
    """A modest, valid starting intent anchored to THIS recipe's anchors.

    Semantic only — no raw milliseconds, and no ``.cam10`` anywhere near it.
    The compiled camera file is an execution artifact the editor never
    shows and never names (§: backend is an implementation detail).
    """
    anchor_ids = [a.anchor_id for a in recipe.anchors
                  if a.status == "resolved" and a.resolved_demo_us is not None]
    if not anchor_ids:
        return CameraIntent(mode="FPV", stages=(), params={"fov": 90.0})
    first = anchor_ids[0]
    last = anchor_ids[-1]
    window = recipe.demo.window_end_us - recipe.demo.window_start_us
    lead = min(3_000_000, max(500_000, window // 3))
    tail = min(2_000_000, max(500_000, window // 4))
    stages = (
        {"stage": "FPV", "start_anchor": first, "start_offset_us": -lead,
         "end_anchor": first, "end_offset_us": -200_000, "params": {"fov": 90.0}},
        {"stage": "IMPACT_HOLD", "start_anchor": first,
         "start_offset_us": -200_000, "end_anchor": last,
         "end_offset_us": tail, "params": {"fov": 85.0}},
    )
    return CameraIntent(mode="FPV", stages=stages, subject_anchor=first,
                        params={"fov": 90.0})


def camera_lane(intent: CameraIntent, recipe: SceneRecipeV2,
                time_map: TimeMap) -> list[dict[str, Any]]:
    """Camera stages projected onto edit time.

    Stages are anchored semantically, so a re-run of recognition that moves
    the impact by 25 ms moves the camera with it — automatically. That is
    why the lane resolves anchors here instead of storing edit times.
    """
    rows: list[dict[str, Any]] = []
    for index, entry in enumerate(intent.stages):
        try:
            demo_start, demo_end = intent.resolve_stage_window_us(recipe, entry)
        except Exception as exc:          # AnchorResolutionError and friends
            rows.append({"index": index, "stage": entry.get("stage"),
                         "error": str(exc), "resolved": False})
            continue
        span = edit_span_of_demo_span(time_map, demo_start, demo_end)
        if span is None:
            # Clamp to the window rather than dropping the stage silently.
            clamped_start = max(demo_start, recipe.demo.window_start_us)
            clamped_end = min(demo_end, recipe.demo.window_end_us)
            span = edit_span_of_demo_span(time_map, clamped_start, clamped_end)
        if span is None:
            rows.append({"index": index, "stage": entry.get("stage"),
                         "error": "stage falls entirely outside the window",
                         "resolved": False})
            continue
        rows.append({
            "index": index, "stage": entry["stage"], "resolved": True,
            "start_anchor": entry["start_anchor"],
            "start_offset_us": int(entry.get("start_offset_us", 0)),
            "end_anchor": entry["end_anchor"],
            "end_offset_us": int(entry.get("end_offset_us", 0)),
            "demo_start_us": demo_start, "demo_end_us": demo_end,
            "edit_start_us": span[0], "edit_end_us": span[1],
            "params": dict(entry.get("params") or {}),
        })
    return rows


def fx_lane(cues: Sequence[FxCue], recipe: SceneRecipeV2,
            time_map: TimeMap) -> list[dict[str, Any]]:
    """Semantic FX cues projected onto edit time.

    A cue's ``duration_us`` is engine time, so a cue that straddles a slow
    segment renders WIDER on the timeline than its authored duration. That
    is correct and deliberate: the lane shows what the viewer will see, and
    the three clocks stay visibly distinct.
    """
    rows: list[dict[str, Any]] = []
    for index, cue in enumerate(cues):
        try:
            demo_start = resolve_anchor(recipe, cue.semantic_anchor,
                                        cue.offset_us)
        except Exception as exc:
            rows.append({"index": index, "effect_type": cue.effect_type,
                         "error": str(exc), "resolved": False})
            continue
        demo_end = demo_start + max(0, cue.duration_us)
        start_edit = demo_to_edit_clamped(time_map, demo_start, bias="left")
        if start_edit is None:
            rows.append({"index": index, "effect_type": cue.effect_type,
                         "error": "cue falls outside the scene window",
                         "resolved": False})
            continue
        end_edit = demo_to_edit_clamped(time_map, demo_end, bias="right")
        if end_edit is None:
            end_edit = recipe.time_map[-1].edit_end_us
        rows.append({
            "index": index, "effect_type": cue.effect_type, "resolved": True,
            "semantic_anchor": cue.semantic_anchor, "offset_us": cue.offset_us,
            "duration_us": cue.duration_us,
            "intensity_level": cue.intensity_level, "binding": cue.binding,
            "demo_start_us": demo_start, "demo_end_us": demo_end,
            "edit_start_us": start_edit, "edit_end_us": max(start_edit, end_edit),
        })
    return rows


# ===========================================================================
# bounded TimeMap editing
# ===========================================================================

# The editable rate menu. No reverse — ``TimeSegment`` rejects it at the
# schema level, and this list never offers it.
ALLOWED_RATES: tuple[tuple[int, int], ...] = ((1, 1), (3, 4), (1, 2))
MIN_FREEZE_US = 40_000
MAX_FREEZE_US = 4_000_000
MIN_PLAYBACK_DEMO_US = 50_000


def segment_specs(segments: Sequence[Any]) -> list[dict[str, Any]]:
    """Reduce a TimeMap to its EDITABLE degrees of freedom.

    Edit times are omitted deliberately: they are derived, never authored.
    Everything the editor may change lives here — kind, the demo boundary,
    the rate, and (for a freeze) how long it holds the picture.
    """
    out: list[dict[str, Any]] = []
    for segment in segments:
        out.append({
            "kind": segment.kind,
            "demo_start_us": segment.demo_start_us,
            "demo_end_us": segment.demo_end_us,
            "rate_num": segment.rate_num, "rate_den": segment.rate_den,
            "freeze_us": (segment.edit_end_us - segment.edit_start_us
                          if segment.kind == "freeze" else 0),
        })
    return out


def rebuild_time_map(specs: Sequence[dict[str, Any]]) -> tuple:
    """Recompute every edit clock from the demo boundaries and rates.

    Edit time is a CONSEQUENCE of the demo boundaries and the rates, so it
    is always recomputed from zero rather than patched in place — that is
    what stops an edited segment from leaving a one-microsecond hole three
    segments later.

    A freeze contributes ``freeze_us`` of EDIT duration while consuming ZERO
    demo time. Both facts are enforced by ``TimeSegment``; this function
    just has to feed it consistent numbers.
    """
    from creative_suite.engine.scene_recipe import TimeSegment
    segments: list[Any] = []
    cursor = 0
    for index, spec in enumerate(specs):
        kind = spec["kind"]
        demo_start, demo_end = int(spec["demo_start_us"]), int(spec["demo_end_us"])
        if kind == "freeze":
            hold = int(spec.get("freeze_us") or 0)
            if not (MIN_FREEZE_US <= hold <= MAX_FREEZE_US):
                raise ValueError(
                    f"segment {index}: freeze must hold "
                    f"{MIN_FREEZE_US}..{MAX_FREEZE_US} us, got {hold}")
            if demo_end != demo_start:
                raise ValueError(f"segment {index}: a freeze consumes no demo time")
            segments.append(TimeSegment("freeze", demo_start, demo_start,
                                        cursor, cursor + hold, 0, 1))
            cursor += hold
            continue
        num, den = int(spec["rate_num"]), int(spec["rate_den"])
        if (num, den) not in ALLOWED_RATES:
            raise ValueError(
                f"segment {index}: rate {num}/{den} is not offered; "
                f"allowed rates are {['%d/%d' % r for r in ALLOWED_RATES]}")
        demo_span = demo_end - demo_start
        if demo_span < MIN_PLAYBACK_DEMO_US:
            raise ValueError(
                f"segment {index}: playback needs at least "
                f"{MIN_PLAYBACK_DEMO_US} us of demo, got {demo_span}")
        if (demo_span * den) % num:
            raise ValueError(
                f"segment {index}: {demo_span} us at rate {num}/{den} is not a "
                f"whole number of edit microseconds — move the boundary by "
                f"{(demo_span * den) % num} us")
        edit_span = demo_span * den // num
        segments.append(TimeSegment(
            "normal" if (num, den) == (1, 1) else "slow",
            demo_start, demo_end, cursor, cursor + edit_span, num, den))
        cursor += edit_span
    return tuple(segments)


def set_segment_rate(specs: Sequence[dict[str, Any]], index: int,
                     rate_num: int, rate_den: int) -> list[dict[str, Any]]:
    """Change one playback segment's rate, moving the boundary if needed.

    A rate of 3/4 only lands on whole microseconds when the demo span is a
    multiple of 3. Rather than refusing, the boundary is nudged by at most
    two microseconds and the remainder handed to the NEXT segment, which
    keeps the demo timeline contiguous and the total window intact.
    """
    out = [dict(s) for s in specs]
    if not 0 <= index < len(out):
        raise ValueError(f"no segment at index {index}")
    if out[index]["kind"] == "freeze":
        raise ValueError("a freeze has no playback rate — set its hold instead")
    if (rate_num, rate_den) not in ALLOWED_RATES:
        raise ValueError(f"rate {rate_num}/{rate_den} is not offered")
    spec = out[index]
    span = spec["demo_end_us"] - spec["demo_start_us"]
    remainder = (span * rate_den) % rate_num
    if remainder:
        shift = remainder  # give these microseconds to the neighbour
        if index + 1 < len(out) and out[index + 1]["kind"] != "freeze":
            spec["demo_end_us"] -= shift
            out[index + 1]["demo_start_us"] -= shift
        else:
            raise ValueError(
                f"rate {rate_num}/{rate_den} needs the boundary moved by "
                f"{shift} us but there is no adjacent playback segment")
    spec["rate_num"], spec["rate_den"] = rate_num, rate_den
    spec["kind"] = "normal" if (rate_num, rate_den) == (1, 1) else "slow"
    return out


def set_freeze_hold(specs: Sequence[dict[str, Any]], index: int,
                    freeze_us: int) -> list[dict[str, Any]]:
    out = [dict(s) for s in specs]
    if not 0 <= index < len(out) or out[index]["kind"] != "freeze":
        raise ValueError(f"segment {index} is not a freeze")
    out[index]["freeze_us"] = int(freeze_us)
    return out


def set_boundary(specs: Sequence[dict[str, Any]], index: int,
                 demo_us: int) -> list[dict[str, Any]]:
    """Move the demo boundary BETWEEN segment ``index`` and ``index+1``."""
    out = [dict(s) for s in specs]
    if not 0 <= index < len(out) - 1:
        raise ValueError(f"no boundary after segment {index}")
    # A freeze pins BOTH its clocks to one demo instant, so moving a
    # boundary next to one would silently drag the frozen moment itself.
    # Refused rather than guessed: move the freeze's neighbours instead.
    if out[index]["kind"] == "freeze" or out[index + 1]["kind"] == "freeze":
        raise ValueError(
            "this boundary pins a freeze to its demo instant — change the "
            "freeze hold, or the rate of an adjacent playback segment")
    value = int(demo_us)
    out[index]["demo_end_us"] = value
    out[index + 1]["demo_start_us"] = value
    return out


# ===========================================================================
# recipe state vs UI state (§52)
# ===========================================================================

def recipe_state(draft: dict[str, Any]) -> dict[str, Any]:
    """The subset of a draft that is allowed to influence identity."""
    return {key: draft[key] for key in RECIPE_STATE_KEYS if key in draft}


def ui_state(draft: dict[str, Any]) -> dict[str, Any]:
    return {key: draft[key] for key in UI_STATE_KEYS if key in draft}


def apply_placement(recipe: SceneRecipeV2,
                    placement: MusicPlacement | None) -> SceneRecipeV2:
    """Swap ONLY the music placement (§29, §35).

    Everything else — demo window, TimeMap, anchors, exclusions, camera,
    effects, transition — is carried through by reference. This is the
    single function A/B/C switching goes through, which is what makes the
    "same edit, different music" claim testable instead of aspirational.
    """
    return replace(recipe, music=placement)


def review_identity(*, frag_id: int, track_hash: str, region_start_us: int,
                    scene_recipe_id: str, matcher_version: str) -> str:
    """(scene, track hash, region, matcher version) — never a letter (§39).

    A/B/C are display order for one ranking run. The same track+region
    reviewed tomorrow under the same matcher is the SAME review, even if it
    happens to rank second that day.
    """
    return (f"{int(frag_id)}:{track_hash}:{int(region_start_us)}:"
            f"{scene_recipe_id}:{matcher_version}")


# ===========================================================================
# the whole projection
# ===========================================================================

def build_projection(
    frag_id: int, *, frag_db: Path, demo_v2_db: Path,
    music_db: Path | None = None,
    recipe: SceneRecipeV2 | None = None,
    placement: MusicPlacement | None = None,
    time_map: Sequence[Any] | None = None,
    camera_intent: CameraIntent | None = None,
    fx_cues: Sequence[FxCue] = (),
    visual_look: str = "ORIGINAL",
    envelope_buckets: int = DEFAULT_ENVELOPE_BUCKETS,
) -> dict[str, Any]:
    """Every lane for one scene, all projected onto ``edit_us``.

    Pass ``recipe`` to project the DRAFT's recipe rather than the evidence
    default — the API does, so ``recipe_id`` here is the same hash the
    editor shows and saves. ``time_map`` / ``placement`` are the narrower
    overrides used by tests and by the pure layer. Any of them has to be
    applied HERE rather than patched onto the result, because every other
    lane's edit clock is a function of the TimeMap: a retimed scene whose
    music lane still used the old map would be quietly wrong.
    """
    evidence = SceneEvidence(frag_id, frag_db=frag_db, demo_v2_db=demo_v2_db)
    if recipe is None:
        recipe = evidence.recipe()
    if time_map is not None:
        recipe = replace(recipe, time_map=tuple(time_map))
    if placement is not None:
        recipe = apply_placement(recipe, placement)
    time_map = recipe.time_map_object()
    duration_us = recipe.time_map[-1].edit_end_us
    events, kind_index = game_event_lane(evidence, time_map)
    intent = camera_intent or default_camera_intent(recipe)
    scene = PantheonScene(recipe_id=recipe.recipe_id, camera_intent=intent,
                          fx_stack=tuple(fx_cues), visual_look=visual_look)

    music: dict[str, Any] | None = None
    guides: list[dict[str, Any]] = []
    if recipe.music is not None and music_db is not None:
        feature = MusicFeatureStore(Path(music_db)).get(recipe.music.track_id)
        if feature is not None:
            music = project_music_lane(feature, recipe.music, duration_us,
                                       envelope_buckets=envelope_buckets)
            guides = guide_lines(events, music)

    return {
        "projection_version": PROJECTION_VERSION,
        "frag_id": evidence.frag_id,
        "recipe_id": recipe.recipe_id,
        "scene_id": scene.scene_id,
        "recipe": recipe.to_dict(),
        "demo": {"name": recipe.demo.name, "sha256": recipe.demo.sha256,
                 "window_start_us": recipe.demo.window_start_us,
                 "window_end_us": recipe.demo.window_end_us},
        "duration_us": duration_us,
        "weapon": evidence.frag.get("weapon_name"),
        "classes": evidence.frag["classes"],
        "lane_order": list(LANE_ORDER),
        "lanes": {
            LANE_GAME_EVENTS: {"events": events, "kinds": kind_index},
            LANE_TIME: {"segments": time_lane(recipe)},
            LANE_CAMERA: {"mode": intent.mode,
                          "subject_anchor": intent.subject_anchor,
                          "stages": camera_lane(intent, recipe, time_map)},
            LANE_FX: {"cues": fx_lane(scene.fx_stack, recipe, time_map)},
            LANE_LOOK: {"visual_look": visual_look},
            LANE_MUSIC_WAVEFORM: music,
            LANE_MUSIC_EVENTS: None if music is None else music["events"],
            LANE_MUSIC_STRUCTURE: None if music is None else music["structure"],
        },
        "anchors": [{"anchor_id": a.anchor_id, "event_type": a.event_type,
                     "resolved_demo_us": a.resolved_demo_us,
                     "edit_us": (None if a.resolved_demo_us is None else
                                 demo_to_edit_clamped(time_map,
                                                      a.resolved_demo_us,
                                                      bias="right")),
                     "confidence": a.confidence, "status": a.status}
                    for a in recipe.anchors],
        "guides": guides,
        "snap_targets": [] if music is None else snap_targets(music),
    }
