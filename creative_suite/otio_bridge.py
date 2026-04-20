# creative_suite/otio_bridge.py
"""PANTHEON render → OpenTimelineIO bridge.

Converts a Part's clip list + flow_plan.json into an `.otio` file that can
be imported into DaVinci Resolve, Final Cut Pro, or any NLE that speaks
OpenTimelineIO.

Usage (standalone):
    from pathlib import Path
    from creative_suite.otio_bridge import write_otio_for_part
    otio_path = write_otio_for_part(4, Path("G:/QUAKE_LEGACY/output/part04"))

Usage (from rebuild pipeline):
    otio_path = write_otio_for_part(part, output_dir)

opentimelineio is a runtime dependency (pip install opentimelineio).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import opentimelineio as otio
from opentimelineio import opentime, schema

log = logging.getLogger(__name__)

FPS = 60  # Quake Legacy fragmovies are always 60fps (Rule P1-J)
DEFAULT_CLIP_DURATION_S = 3.0  # fallback when flow_plan has no duration info


def _rt(seconds: float) -> opentime.RationalTime:
    """Convert seconds to RationalTime at FPS."""
    return opentime.RationalTime(round(seconds * FPS), FPS)


def _tier_from_path(path: str) -> str:
    """Infer clip tier (T1/T2/T3) from the path string."""
    p = path.replace("\\", "/")
    for tier in ("T1", "T2", "T3"):
        if f"/{tier}/" in p:
            return tier
    return "?"


def _is_fl(path: str) -> bool:
    """Return True if the clip filename looks like a freelook (FL) angle."""
    name = Path(path).stem.upper()
    return "FL" in name


def build_otio_timeline(
    part: int,
    clips: list[dict[str, Any]],
    flow_plan: dict[str, Any] | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Build an OTIO timeline from render data.

    Parameters
    ----------
    part:
        Part number (1-based integer, e.g. 4 → "Part 04").
    clips:
        List of clip dicts. Each dict must have at least ``path`` (str).
        Optional keys: ``duration`` (float, seconds), ``tier`` (str),
        ``is_fl`` (bool), ``slow`` (bool), ``intro`` (bool).
    flow_plan:
        Parsed contents of ``partNN_flow_plan.json``.  When provided the
        bridge reads ``body_seam_offsets`` to compute actual timeline start
        positions for each clip.
    output_path:
        When set, the timeline is serialised to this path as a ``.otio``
        JSON file.

    Returns
    -------
    dict
        The OTIO Timeline serialised to a plain Python dict (JSON-friendly).
        Also writes the file when *output_path* is given.
    """
    # ── Build OTIO objects ────────────────────────────────────────────────────
    timeline = schema.Timeline(name=f"Part {part:02d}")
    timeline.metadata["pantheon"] = {
        "part": part,
        "generated_by": "pantheon-otio-bridge/1.0",
    }

    video_track = schema.Track(name="V1", kind=schema.TrackKind.Video)
    timeline.tracks.append(video_track)

    # Resolve seam offsets from flow_plan if available (Rule CS-6)
    seam_offsets: list[float] = []
    if flow_plan is not None:
        raw = flow_plan.get("body_seam_offsets", [])
        if isinstance(raw, list):
            seam_offsets = [float(x) for x in raw if isinstance(x, (int, float))]

    cursor_s = 0.0

    for idx, clip_dict in enumerate(clips):
        path_str: str = clip_dict.get("path", "")
        duration_s: float = float(clip_dict.get("duration", DEFAULT_CLIP_DURATION_S))
        tier: str = clip_dict.get("tier") or _tier_from_path(path_str)
        is_fl: bool = bool(clip_dict.get("is_fl", _is_fl(path_str)))
        slow: bool = bool(clip_dict.get("slow", False))
        intro: bool = bool(clip_dict.get("intro", False))

        # Override timeline cursor with seam offset when available
        if idx < len(seam_offsets):
            cursor_s = seam_offsets[idx]

        clip_name = Path(path_str).stem if path_str else f"frag{idx:03d}"

        media_ref = schema.ExternalReference(
            target_url=path_str,
            available_range=opentime.TimeRange(
                start_time=opentime.RationalTime(0, FPS),
                duration=_rt(duration_s),
            ),
        )
        otio_clip = schema.Clip(
            name=clip_name,
            media_reference=media_ref,
            source_range=opentime.TimeRange(
                start_time=opentime.RationalTime(0, FPS),
                duration=_rt(duration_s),
            ),
        )
        otio_clip.metadata["pantheon"] = {
            "tier": tier,
            "is_fl": is_fl,
            "slow": slow,
            "intro": intro,
            "timeline_offset_s": cursor_s,
        }

        if slow:
            otio_clip.effects.append(schema.LinearTimeWarp(time_scalar=0.5))

        video_track.append(otio_clip)
        cursor_s += duration_s

    # ── Serialise to dict ─────────────────────────────────────────────────────
    timeline_dict: dict[str, Any] = json.loads(
        otio.adapters.write_to_string(timeline, adapter_name="otio_json")
    )

    # ── Write file if requested ───────────────────────────────────────────────
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(timeline_dict, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log.info("OTIO artifact written: %s", output_path)

    return timeline_dict


# ── Convenience: read render outputs and write .otio ─────────────────────────

def _read_json_or_none(p: Path) -> dict[str, Any] | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _clips_from_flow_plan(flow_plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract clip dicts from a flow_plan.json structure."""
    result: list[dict[str, Any]] = []
    for c in flow_plan.get("clips", []):
        path = str(c.get("chunk", c.get("path", "")))
        result.append({
            "path": path,
            "duration": float(c.get("duration", DEFAULT_CLIP_DURATION_S)),
            "tier": str(c.get("tier", _tier_from_path(path))),
            "is_fl": _is_fl(path),
            "slow": bool(c.get("slow", False)),
            "intro": bool(c.get("intro", False)),
        })
    return result


def write_otio_for_part(part: int, output_dir: Path) -> Path | None:
    """Read clip list and flow_plan from *output_dir*, build OTIO, write
    ``partNN.otio`` to the same directory.

    Returns the written path on success, or ``None`` when required data is
    absent.

    This is the function called by the rebuild pipeline hook.
    """
    flow_plan = _read_json_or_none(output_dir / f"part{part:02d}_flow_plan.json")
    if flow_plan is None:
        log.warning(
            "otio_bridge: part%02d flow_plan not found in %s — skipping .otio",
            part, output_dir,
        )
        return None

    clips = _clips_from_flow_plan(flow_plan)
    if not clips:
        log.warning(
            "otio_bridge: part%02d flow_plan has no clips — skipping .otio",
            part,
        )
        return None

    otio_path = output_dir / f"part{part:02d}.otio"
    build_otio_timeline(
        part=part,
        clips=clips,
        flow_plan=flow_plan,
        output_path=otio_path,
    )
    return otio_path
