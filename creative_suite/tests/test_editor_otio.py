"""OTIO round-trip tests for editor state."""
from __future__ import annotations

from pathlib import Path

from creative_suite.editor.otio_bridge import (
    otio_to_state,
    read_otio,
    state_to_otio,
    write_otio,
)
from creative_suite.editor.state import EditorClip, EditorState


def _state() -> EditorState:
    return EditorState(
        part=4,
        clips=[
            EditorClip(chunk="c0.mp4", tier="T1", section_role="drop",
                       duration=3.0, in_s=0.5, out_s=2.5),
            EditorClip(chunk="c1.mp4", tier="T2", duration=4.0,
                       in_s=0.0, out_s=4.0, removed=True),
            EditorClip(chunk="c2.mp4", tier="T3", duration=5.0,
                       in_s=0.0, out_s=5.0, slow=0.5, slow_window_s=1.0),
        ],
    )


def test_state_to_otio_builds_timeline_with_one_track() -> None:
    s = _state()
    tl = state_to_otio(s)
    assert tl.name == "part04"
    assert len(tl.tracks) == 1
    track = tl.tracks[0]
    # 3 editor clips → 3 OTIO items (Clip, Gap, Clip)
    assert len(list(track)) == 3


def test_otio_roundtrip_preserves_core_fields() -> None:
    s = _state()
    tl = state_to_otio(s)
    back = otio_to_state(tl)
    assert back.part == s.part
    assert len(back.clips) == len(s.clips)
    for a, b in zip(s.clips, back.clips):
        assert a.chunk == b.chunk
        assert a.tier == b.tier
        assert a.section_role == b.section_role
        assert a.removed == b.removed
        assert a.in_s == b.in_s
        assert a.out_s == b.out_s
        assert a.slow == b.slow


def test_write_and_read_otio_file(tmp_path: Path) -> None:
    s = _state()
    out = tmp_path / "roundtrip.otio"
    write_otio(s, out)
    assert out.exists() and out.stat().st_size > 0
    back = read_otio(out)
    assert back.part == s.part
    assert len(back.clips) == 3
    assert back.clips[1].removed is True
    assert back.clips[2].slow == 0.5


def test_slow_clip_emits_linear_timewarp() -> None:
    from opentimelineio import schema

    s = EditorState(
        part=4,
        clips=[EditorClip(chunk="c.mp4", duration=2.0, out_s=2.0, slow=0.5)],
    )
    tl = state_to_otio(s)
    track = tl.tracks[0]
    clip = list(track)[0]
    assert isinstance(clip, schema.Clip)
    effs = [e for e in clip.effects if isinstance(e, schema.LinearTimeWarp)]
    assert len(effs) == 1
    assert effs[0].time_scalar == 0.5
