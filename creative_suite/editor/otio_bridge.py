"""EditorState ↔ OpenTimelineIO round-trip.

OTIO is our interchange format. This module never modifies state — it
maps clips onto an OTIO `Timeline` with a single video track. Removed
clips become OTIO `Gap`s so frame counts stay honest. Speed changes
become a `LinearTimeWarp` effect on the clip.

Round-trip target: `otio_to_state(state_to_otio(s)) == s` for any `s`
using only the fields OTIO can represent (chunk, in_s, out_s, removed,
slow). `notes` / `tier` / `section_role` ride along on the clip's
`metadata["quake"]` dict.
"""
from __future__ import annotations

from pathlib import Path
from typing import cast, Any

try:
    import opentimelineio as otio
    from opentimelineio import opentime, schema
    _OTIO_AVAILABLE = True
except ModuleNotFoundError:
    otio = None  # type: ignore[assignment]
    opentime = schema = None  # type: ignore[assignment]
    _OTIO_AVAILABLE = False

from creative_suite.editor.state import EditorClip, EditorState

FPS = 60  # QUAKE fragmovies are 60fps — Rule P1-J
META_NS = "quake"


def _require_otio() -> None:
    if not _OTIO_AVAILABLE:
        raise RuntimeError(
            "opentimelineio is not installed. "
            "Run: pip install opentimelineio"
        )


def _rt(seconds: float) -> "opentime.RationalTime":
    return opentime.RationalTime(round(seconds * FPS), FPS)  # type: ignore[union-attr]


def state_to_otio(state: EditorState, chunk_dir: Path | None = None) -> "schema.Timeline":  # type: ignore[name-defined]
    """Convert editor state to an OTIO `Timeline`.

    The single video track interleaves Clips and Gaps: removed editor
    clips become Gaps so playhead timing stays aligned with what a
    live-play-with-gaps preview would show.
    """
    _require_otio()
    timeline = schema.Timeline(name=f"part{state.part:02d}")
    track = schema.Track(name="body", kind=schema.TrackKind.Video)
    timeline.tracks.append(track)

    for c in state.clips:
        duration = max(c.out_s - c.in_s, 0.0)
        if duration <= 0:
            continue
        if c.removed:
            gap = schema.Gap(source_range=opentime.TimeRange(
                start_time=opentime.RationalTime(0, FPS),
                duration=_rt(duration),
            ))
            gap.metadata[META_NS] = {
                "chunk": c.chunk,
                "tier": c.tier,
                "section_role": c.section_role,
                "removed": True,
                "duration": c.duration,
                "notes": c.notes,
            }
            track.append(gap)
            continue

        target_url = ""
        if chunk_dir is not None:
            target_url = (chunk_dir / c.chunk).as_uri()
        media_ref: schema.MediaReference = schema.ExternalReference(
            target_url=target_url,
            available_range=opentime.TimeRange(
                start_time=opentime.RationalTime(0, FPS),
                duration=_rt(c.duration),
            ),
        )
        clip = schema.Clip(
            name=c.chunk,
            media_reference=media_ref,
            source_range=opentime.TimeRange(
                start_time=_rt(c.in_s),
                duration=_rt(duration),
            ),
        )
        clip.metadata[META_NS] = {
            "chunk": c.chunk,
            "tier": c.tier,
            "section_role": c.section_role,
            "removed": False,
            "duration": c.duration,
            "notes": c.notes,
        }
        if c.slow is not None:
            clip.effects.append(schema.LinearTimeWarp(time_scalar=c.slow))
            clip.metadata[META_NS]["slow"] = c.slow
            clip.metadata[META_NS]["slow_window_s"] = c.slow_window_s
        track.append(clip)
    timeline.metadata[META_NS] = {
        "version": state.version,
        "part": state.part,
        "meta": state.meta,
    }
    return timeline


def otio_to_state(timeline: schema.Timeline) -> EditorState:
    """Inverse of `state_to_otio`. Loses global `effects[]` / `keyframes[]`;
    those live outside the OTIO schema and are carried in editor_state.json
    directly.
    """
    tl_meta = cast(dict[str, Any], timeline.metadata.get(META_NS, {}))
    part = int(tl_meta.get("part", 0))
    version = int(tl_meta.get("version", 1))
    clips: list[EditorClip] = []
    if timeline.tracks:
        track = timeline.tracks[0]
        for child in track:
            meta = cast(dict[str, Any], child.metadata.get(META_NS, {}))
            if isinstance(child, schema.Gap):
                sr = child.source_range
                dur_s = 0.0 if sr is None else sr.duration.value / sr.duration.rate
                clips.append(EditorClip(
                    chunk=meta.get("chunk", ""),
                    tier=meta.get("tier", "?"),
                    section_role=meta.get("section_role"),
                    duration=float(meta.get("duration", dur_s)),
                    in_s=0.0,
                    out_s=dur_s,
                    removed=True,
                    notes=meta.get("notes", ""),
                ))
            elif isinstance(child, schema.Clip):
                sr = child.source_range
                in_s = 0.0 if sr is None else sr.start_time.value / sr.start_time.rate
                dur_s = 0.0 if sr is None else sr.duration.value / sr.duration.rate
                slow: float | None = None
                for eff in child.effects:
                    if isinstance(eff, schema.LinearTimeWarp):
                        slow = float(eff.time_scalar)
                        break
                clips.append(EditorClip(
                    chunk=meta.get("chunk", child.name or ""),
                    tier=meta.get("tier", "?"),
                    section_role=meta.get("section_role"),
                    duration=float(meta.get("duration", in_s + dur_s)),
                    in_s=in_s,
                    out_s=in_s + dur_s,
                    removed=False,
                    slow=slow if slow is not None else meta.get("slow"),
                    slow_window_s=meta.get("slow_window_s"),
                    notes=meta.get("notes", ""),
                ))
    return EditorState(
        part=part,
        version=version,
        clips=clips,
        meta=cast(dict[str, Any], tl_meta.get("meta", {})),
    )


def write_otio(state: EditorState, out_path: Path, chunk_dir: Path | None = None) -> Path:
    timeline = state_to_otio(state, chunk_dir)
    otio.adapters.write_to_file(timeline, str(out_path))
    return out_path


def read_otio(in_path: Path) -> EditorState:
    timeline = cast(schema.Timeline, otio.adapters.read_from_file(str(in_path)))
    return otio_to_state(timeline)
