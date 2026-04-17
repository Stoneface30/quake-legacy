from __future__ import annotations

from dataclasses import dataclass

from creative_suite.clips.parser import ClipEntry


@dataclass(frozen=True)
class ResolvedClip:
    clip_index: int
    clip_filename: str
    demo_hint: str | None
    mp4_offset: float   # mp4 timestamp where this clip begins
    clip_offset: float  # seconds into the clip at mp4_time


def resolve_clip(
    entries: list[ClipEntry],
    durations: list[float],
    mp4_time: float,
    offset: float,
) -> ResolvedClip | None:
    if mp4_time < offset:
        return None
    if not entries:
        return None
    t = mp4_time - offset
    cursor = 0.0
    for entry, dur in zip(entries, durations):
        if t < cursor + dur:
            return ResolvedClip(
                clip_index=entry.index,
                clip_filename=entry.filename,
                demo_hint=entry.demo_hint,
                mp4_offset=offset + cursor,
                clip_offset=t - cursor,
            )
        cursor += dur
    last = entries[-1]
    last_dur = durations[-1] if durations else 0.0
    return ResolvedClip(
        clip_index=last.index,
        clip_filename=last.filename,
        demo_hint=last.demo_hint,
        mp4_offset=offset + cursor - last_dur,
        clip_offset=last_dur,
    )
