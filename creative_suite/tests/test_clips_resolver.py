from creative_suite.clips.parser import ClipEntry
from creative_suite.clips.resolver import ResolvedClip, resolve_clip


def _entries() -> list[ClipEntry]:
    return [
        ClipEntry(0, "Demo (1) - A.avi", "1", False),
        ClipEntry(1, "Demo (2) - B.avi", "2", False),
        ClipEntry(2, "Demo (3) - C.avi", "3", True),
    ]


def test_pre_content_offset_returns_none() -> None:
    r = resolve_clip(_entries(), [5.0, 5.0, 5.0], mp4_time=7.0, offset=15.0)
    assert r is None


def test_first_clip_boundary() -> None:
    r = resolve_clip(_entries(), [5.0, 5.0, 5.0], mp4_time=15.5, offset=15.0)
    assert isinstance(r, ResolvedClip)
    assert r.clip_index == 0
    assert r.clip_filename == "Demo (1) - A.avi"
    assert r.demo_hint == "1"
    assert abs(r.clip_offset - 0.5) < 1e-6
    assert abs(r.mp4_offset - 15.0) < 1e-6


def test_middle_clip() -> None:
    r = resolve_clip(_entries(), [5.0, 5.0, 5.0], mp4_time=22.0, offset=15.0)
    assert r is not None and r.clip_index == 1 and abs(r.clip_offset - 2.0) < 1e-6


def test_past_end_returns_last() -> None:
    r = resolve_clip(_entries(), [5.0, 5.0, 5.0], mp4_time=999.0, offset=15.0)
    assert r is not None and r.clip_index == 2
