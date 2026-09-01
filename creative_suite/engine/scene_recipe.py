"""Canonical Phase-2 scene contract with explicit demo/edit/music clocks.

``SceneRecipeV2`` is the authority.  ShotPlan and the older editor/NLE/flow
formats are projections of this data, never alternate sources of truth.
All clocks are signed integer microseconds.  Playback rates are exact
rationals expressed as ``rate_num / rate_den`` where the rate is demo-time
progress per edit-time progress (therefore 1/2 is half-speed playback).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from math import gcd
from pathlib import Path
from typing import Any, Literal, Sequence

from creative_suite.engine import shot_plan
from creative_suite.engine.timeline import Timeline

BoundaryBias = Literal["left", "right"]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def _as_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be a signed integer microsecond value")
    return value


def _round_fraction(value: Fraction) -> int:
    """Deterministic nearest-integer conversion, halves away from zero."""
    numerator, denominator = value.numerator, value.denominator
    sign = -1 if numerator < 0 else 1
    numerator = abs(numerator)
    quotient, remainder = divmod(numerator, denominator)
    if remainder * 2 >= denominator:
        quotient += 1
    return sign * quotient


@dataclass(frozen=True)
class DemoRef:
    sha256: str
    name: str
    window_start_us: int
    window_end_us: int

    def __post_init__(self) -> None:
        _as_int(self.window_start_us, "window_start_us")
        _as_int(self.window_end_us, "window_end_us")
        if self.window_end_us <= self.window_start_us:
            raise ValueError("demo window must have positive duration")


@dataclass(frozen=True)
class EvidenceRef:
    dataset: str
    record_id: str
    version: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EventAnchor:
    anchor_id: str
    event_type: str
    ordinal: int
    actor_scope: str
    resolved_demo_us: int | None
    evidence: EvidenceRef
    confidence: str
    status: str = "resolved"

    def __post_init__(self) -> None:
        if self.resolved_demo_us is not None:
            _as_int(self.resolved_demo_us, "resolved_demo_us")
        if self.status not in {"resolved", "missing", "ambiguous"}:
            raise ValueError(f"unsupported anchor status: {self.status}")


@dataclass(frozen=True)
class ExclusionRange:
    demo_start_us: int
    demo_end_us: int
    reason: str

    def __post_init__(self) -> None:
        _as_int(self.demo_start_us, "demo_start_us")
        _as_int(self.demo_end_us, "demo_end_us")
        if self.demo_end_us <= self.demo_start_us:
            raise ValueError("exclusion range must have positive duration")


@dataclass(frozen=True)
class ExclusionPolicy:
    event_types: tuple[str, ...] = ()
    ranges: tuple[ExclusionRange, ...] = ()


@dataclass(frozen=True)
class MusicPlacement:
    """Independent affine placement from program edit time to track time."""
    track_id: str
    source_start_us: int
    program_edit_start_us: int
    source_end_us: int | None = None

    def __post_init__(self) -> None:
        _as_int(self.source_start_us, "source_start_us")
        _as_int(self.program_edit_start_us, "program_edit_start_us")
        if self.source_end_us is not None:
            _as_int(self.source_end_us, "source_end_us")
            if self.source_end_us <= self.source_start_us:
                raise ValueError("music source region must have positive duration")

    def edit_to_music(self, edit_us: int) -> int:
        _as_int(edit_us, "edit_us")
        return self.source_start_us + edit_us - self.program_edit_start_us


@dataclass(frozen=True)
class TimeSegment:
    kind: str
    demo_start_us: int
    demo_end_us: int
    edit_start_us: int
    edit_end_us: int
    rate_num: int
    rate_den: int

    def __post_init__(self) -> None:
        for name in ("demo_start_us", "demo_end_us", "edit_start_us",
                     "edit_end_us", "rate_num", "rate_den"):
            _as_int(getattr(self, name), name)
        if self.kind == "reverse" or self.rate_num < 0:
            raise ValueError("reverse rates are reserved for a later schema slice")
        if self.kind not in {"normal", "slow", "freeze"}:
            raise ValueError(f"unsupported time segment kind: {self.kind}")
        if self.rate_den <= 0:
            raise ValueError("rate_den must be positive")
        edit_span = self.edit_end_us - self.edit_start_us
        demo_span = self.demo_end_us - self.demo_start_us
        if edit_span <= 0:
            raise ValueError("time segment edit span must be positive")
        if self.kind == "freeze":
            if demo_span != 0 or self.rate_num != 0:
                raise ValueError("freeze requires zero demo span and rate_num=0")
            return
        if demo_span <= 0 or self.rate_num <= 0:
            raise ValueError("playback segment demo span and rate must be positive")
        if edit_span * self.rate_num != demo_span * self.rate_den:
            raise ValueError("segment spans do not match exact rational rate")
        if self.kind == "normal" and (self.rate_num, self.rate_den) != (1, 1):
            raise ValueError("normal segment requires rate 1/1")
        if self.kind == "slow" and self.rate_num >= self.rate_den:
            raise ValueError("slow segment rate must be below 1/1")
        if gcd(self.rate_num, self.rate_den) != 1:
            raise ValueError("rate numerator/denominator must be in lowest terms")


class TimeMap:
    def __init__(self, segments: Sequence[TimeSegment]) -> None:
        self.segments = tuple(segments)
        if not self.segments:
            raise ValueError("time map requires at least one segment")
        for previous, current in zip(self.segments, self.segments[1:]):
            if previous.edit_end_us != current.edit_start_us:
                raise ValueError("time-map edit segments must be contiguous")
            if previous.demo_end_us != current.demo_start_us:
                raise ValueError("time-map demo segments must be contiguous")

    @staticmethod
    def _bias(bias: BoundaryBias | None) -> BoundaryBias | None:
        if bias is None:
            return None
        if bias not in ("left", "right"):
            raise ValueError("bias must be 'left' or 'right'")
        return bias

    @staticmethod
    def _resolve_candidates(candidates: list[int], bias: BoundaryBias | None,
                            source: str) -> int:
        if not candidates:
            raise ValueError(f"{source} is outside the time map")
        distinct = sorted(set(candidates))
        if len(distinct) > 1 and bias is None:
            raise ValueError(
                f"ambiguous {source}; pass bias='left' or bias='right' explicitly"
            )
        if bias == "left":
            return distinct[0]
        return distinct[-1]

    def demo_to_edit(self, demo_us: int,
                     bias: BoundaryBias | None = None) -> int:
        _as_int(demo_us, "demo_us")
        bias = self._bias(bias)
        candidates: list[int] = []
        for segment in self.segments:
            if segment.kind == "freeze":
                if demo_us == segment.demo_start_us:
                    candidates.extend((segment.edit_start_us, segment.edit_end_us))
                continue
            if segment.demo_start_us <= demo_us <= segment.demo_end_us:
                delta = Fraction(
                    (demo_us - segment.demo_start_us) * segment.rate_den,
                    segment.rate_num,
                )
                candidates.append(segment.edit_start_us + _round_fraction(delta))
        return self._resolve_candidates(candidates, bias, f"demo_us {demo_us}")

    def edit_to_demo(self, edit_us: int,
                     bias: BoundaryBias | None = None) -> int:
        _as_int(edit_us, "edit_us")
        bias = self._bias(bias)
        candidates: list[int] = []
        for segment in self.segments:
            if segment.edit_start_us <= edit_us <= segment.edit_end_us:
                if segment.kind == "freeze":
                    candidates.append(segment.demo_start_us)
                else:
                    delta = Fraction(
                        (edit_us - segment.edit_start_us) * segment.rate_num,
                        segment.rate_den,
                    )
                    candidates.append(segment.demo_start_us + _round_fraction(delta))
        return self._resolve_candidates(candidates, bias, f"edit_us {edit_us}")


def resolve_time_map(segments: Sequence[TimeSegment]) -> TimeMap:
    return TimeMap(segments)


@dataclass(frozen=True)
class SceneRecipeV2:
    demo: DemoRef
    time_map: tuple[TimeSegment, ...]
    anchors: tuple[EventAnchor, ...] = ()
    exclusions: ExclusionPolicy = field(default_factory=ExclusionPolicy)
    music: MusicPlacement | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    pov: dict[str, Any] = field(default_factory=dict)
    camera: dict[str, Any] = field(default_factory=dict)
    effects: tuple[dict[str, Any], ...] = ()
    objects_3d: tuple[dict[str, Any], ...] = ()
    game_audio: dict[str, Any] = field(default_factory=dict)
    cinematic_audio: dict[str, Any] = field(default_factory=dict)
    transition: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 2

    def __post_init__(self) -> None:
        if self.schema_version != 2:
            raise ValueError("SceneRecipeV2 requires schema_version=2")
        resolve_time_map(self.time_map)

    def to_dict(self) -> dict[str, Any]:
        # Return the actual public JSON shape (lists, never Python tuples),
        # so callers inspect the same structure that is hashed and persisted.
        return json.loads(_canonical_json(asdict(self)))

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    @property
    def recipe_id(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def time_map_object(self) -> TimeMap:
        return resolve_time_map(self.time_map)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SceneRecipeV2":
        anchors = tuple(EventAnchor(
            anchor_id=a["anchor_id"], event_type=a["event_type"],
            ordinal=int(a["ordinal"]), actor_scope=a["actor_scope"],
            resolved_demo_us=a.get("resolved_demo_us"),
            evidence=EvidenceRef(**a["evidence"]),
            confidence=a["confidence"], status=a.get("status", "resolved"),
        ) for a in value.get("anchors", []))
        exclusion_raw = value.get("exclusions") or {}
        exclusions = ExclusionPolicy(
            event_types=tuple(exclusion_raw.get("event_types", [])),
            ranges=tuple(ExclusionRange(**r) for r in exclusion_raw.get("ranges", [])),
        )
        music_raw = value.get("music")
        music = MusicPlacement(**music_raw) if music_raw else None
        return cls(
            demo=DemoRef(**value["demo"]),
            time_map=tuple(TimeSegment(**s) for s in value["time_map"]),
            anchors=anchors, exclusions=exclusions, music=music,
            filters=dict(value.get("filters") or {}),
            pov=dict(value.get("pov") or {}),
            camera=dict(value.get("camera") or {}),
            effects=tuple(value.get("effects") or ()),
            objects_3d=tuple(value.get("objects_3d") or ()),
            game_audio=dict(value.get("game_audio") or {}),
            cinematic_audio=dict(value.get("cinematic_audio") or {}),
            transition=dict(value.get("transition") or {}),
            schema_version=int(value.get("schema_version", 2)),
        )

    @classmethod
    def from_json(cls, blob: str) -> "SceneRecipeV2":
        return cls.from_dict(json.loads(blob))


_SCHEMA = """
CREATE TABLE IF NOT EXISTS scene_recipes_v2 (
    recipe_id TEXT PRIMARY KEY,
    demo_sha256 TEXT NOT NULL,
    recipe_json TEXT NOT NULL
)
"""


def _connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(_SCHEMA)
    return connection


def persist_scene_recipe(recipe: SceneRecipeV2, db_path: str | Path) -> str:
    connection = _connect(db_path)
    try:
        connection.execute(
            "INSERT OR REPLACE INTO scene_recipes_v2 "
            "(recipe_id, demo_sha256, recipe_json) VALUES (?,?,?)",
            (recipe.recipe_id, recipe.demo.sha256, recipe.canonical_json()),
        )
        connection.commit()
    finally:
        connection.close()
    return recipe.recipe_id


def load_scene_recipe(recipe_id: str, db_path: str | Path) -> SceneRecipeV2 | None:
    connection = _connect(db_path)
    try:
        row = connection.execute(
            "SELECT recipe_json FROM scene_recipes_v2 WHERE recipe_id = ?",
            (recipe_id,),
        ).fetchone()
    finally:
        connection.close()
    return SceneRecipeV2.from_json(row[0]) if row else None


def build_frag_scene_recipe(
    frag: dict[str, Any],
    *,
    slow_pre_us: int = 500_000,
    freeze_us: int = 250_000,
) -> SceneRecipeV2:
    """Build an unsaved canonical draft from a real ``/api/frags`` record.

    The recognized frag and projectile evidence stay independently named
    anchors even when they resolve to the same demo instant.  This preserves
    semantic identity for later music/camera relationships.
    """
    _as_int(slow_pre_us, "slow_pre_us")
    _as_int(freeze_us, "freeze_us")
    if slow_pre_us <= 0 or freeze_us <= 0:
        raise ValueError("slow_pre_us and freeze_us must be positive")
    window = frag.get("window") or {}
    window_start_us = int(window["start_ms"]) * 1000
    window_end_us = int(window["end_ms"]) * 1000
    frag_us = int(frag["server_time_ms"]) * 1000
    attributes = dict(frag.get("attributes") or {})
    impact_ms = attributes.get("projectile_impact_t")
    impact_us = int(impact_ms) * 1000 if impact_ms is not None else frag_us
    if not (window_start_us < impact_us < window_end_us):
        raise ValueError("resolved impact must fall inside the scene window")
    slow_start_us = max(window_start_us, impact_us - slow_pre_us)

    normal_duration = slow_start_us - window_start_us
    slow_demo_duration = impact_us - slow_start_us
    slow_edit_duration = slow_demo_duration * 2
    edit_cursor = 0
    segments: list[TimeSegment] = []
    if normal_duration:
        segments.append(TimeSegment(
            "normal", window_start_us, slow_start_us,
            edit_cursor, edit_cursor + normal_duration, 1, 1,
        ))
        edit_cursor += normal_duration
    segments.append(TimeSegment(
        "slow", slow_start_us, impact_us,
        edit_cursor, edit_cursor + slow_edit_duration, 1, 2,
    ))
    edit_cursor += slow_edit_duration
    segments.append(TimeSegment(
        "freeze", impact_us, impact_us,
        edit_cursor, edit_cursor + freeze_us, 0, 1,
    ))
    edit_cursor += freeze_us
    tail_duration = window_end_us - impact_us
    segments.append(TimeSegment(
        "normal", impact_us, window_end_us,
        edit_cursor, edit_cursor + tail_duration, 1, 1,
    ))

    record_id = str(frag["id"])
    recognition_version = f"recognition-v{int(frag.get('recognition_version') or 0)}"
    common_evidence = {
        "dataset": "recognized_frags",
        "record_id": record_id,
        "version": recognition_version,
    }
    impact_evidence = EvidenceRef(
        **common_evidence,
        detail={
            "projectile_status": attributes.get("projectile_status"),
            "projectile_confidence": attributes.get("projectile_path_confidence"),
            "projectile_impact_event": attributes.get("projectile_impact_event"),
        },
    )
    frag_evidence = EvidenceRef(
        **common_evidence,
        detail={"weapon_name": frag.get("weapon_name")},
    )
    anchors = (
        EventAnchor(
            anchor_id="impact-0", event_type=(
                f"{str(frag.get('weapon_name') or 'PROJECTILE').upper()}_IMPACT"
            ), ordinal=0, actor_scope="recorder",
            resolved_demo_us=impact_us, evidence=impact_evidence,
            confidence=str(attributes.get("projectile_path_confidence") or "UNKNOWN"),
        ),
        EventAnchor(
            anchor_id="frag-0", event_type="FRAG", ordinal=0,
            actor_scope="recorder", resolved_demo_us=frag_us,
            evidence=frag_evidence, confidence="CONFIRMED",
        ),
    )
    return SceneRecipeV2(
        demo=DemoRef(
            sha256=str(frag["content_hash"]), name=str(frag["demo_name"]),
            window_start_us=window_start_us, window_end_us=window_end_us,
        ),
        time_map=tuple(segments), anchors=anchors,
        exclusions=ExclusionPolicy(
            event_types=("DEATH", "player_death"), ranges=(),
        ),
        filters={"source_frag_id": int(frag["id"])},
        effects=({"type": "impact_freeze", "anchor_id": "impact-0",
                  "duration_us": freeze_us},),
    )


def _legacy_timeline(recipe: SceneRecipeV2) -> Timeline:
    timeline = Timeline()
    current_rate = Fraction(1, 1)
    origin = recipe.demo.window_start_us
    for segment in recipe.time_map:
        relative_ms = (segment.demo_start_us - origin) // 1000
        if segment.kind == "freeze":
            hold_us = segment.edit_end_us - segment.edit_start_us
            # Legacy Timeline is millisecond-based. Round positive canonical
            # microsecond holds upward so a valid freeze never disappears.
            timeline.freeze(relative_ms, max(1, (hold_us + 999) // 1000))
            continue
        rate = Fraction(segment.rate_num, segment.rate_den)
        if rate != current_rate:
            if rate == 1:
                timeline.resume(relative_ms)
            else:
                timeline.slow_to(relative_ms, float(rate))
            current_rate = rate
    return timeline


def project_to_shot_plan(
    recipe: SceneRecipeV2,
    *,
    profile_id: str,
    camera: dict[str, Any],
    keyframes: list[dict[str, Any]],
    effect_ids: list[str] | None = None,
    asset_pack_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Compatibility projection; the embedded recipe id remains authoritative."""
    primary = next((a for a in recipe.anchors
                    if a.status == "resolved" and a.resolved_demo_us is not None), None)
    event = {
        "type": primary.event_type if primary else "scene",
        "t_ms": (primary.resolved_demo_us // 1000) if primary else 0,
        "scene_recipe_id": recipe.recipe_id,
        "scene_recipe_version": recipe.schema_version,
    }
    return shot_plan.assemble_shot_plan(
        demo_sha256=recipe.demo.sha256,
        event=event,
        profile_id=profile_id,
        camera=camera,
        keyframes=keyframes,
        timeline=_legacy_timeline(recipe),
        effect_ids=effect_ids,
        asset_pack_ids=asset_pack_ids,
    )
