"""Tests for tolerant clip-path resolution on /api/studio/clip-* endpoints.

Regression: the frontend preview passes a bare basename (e.g. "Demo (123)  - 40.avi")
while _resolve_clip_path required an absolute path -> HTTP 400 "Path must be absolute".
"""
import pytest
from fastapi import HTTPException

from creative_suite.api import studio as studio_api


class _Cfg:
    def __init__(self, root):
        self.quake_video_dir = root


@pytest.fixture
def video_root(tmp_path):
    root = tmp_path / "QUAKE VIDEO"
    (root / "T1" / "Part4").mkdir(parents=True)
    (root / "T2" / "Part4").mkdir(parents=True)
    (root / "T1" / "Part4" / "Demo (123)  - 40.avi").write_bytes(b"x")
    (root / "T2" / "Part4" / "other.avi").write_bytes(b"x")
    studio_api._clear_clip_index_cache()
    return root


def test_absolute_path_still_resolves(video_root):
    p = video_root / "T1" / "Part4" / "Demo (123)  - 40.avi"
    assert studio_api._resolve_clip_path(str(p), _Cfg(video_root)) == p


def test_bare_basename_resolves_under_video_root(video_root):
    """The regression: a bare filename must resolve, not 400."""
    got = studio_api._resolve_clip_path("Demo (123)  - 40.avi", _Cfg(video_root))
    assert got == video_root / "T1" / "Part4" / "Demo (123)  - 40.avi"


def test_bare_basename_with_spaces_preserved(video_root):
    got = studio_api._resolve_clip_path("other.avi", _Cfg(video_root))
    assert got.name == "other.avi"


def test_unknown_basename_404s(video_root):
    with pytest.raises(HTTPException) as e:
        studio_api._resolve_clip_path("nope.avi", _Cfg(video_root))
    assert e.value.status_code == 404


def test_traversal_rejected(video_root):
    with pytest.raises(HTTPException) as e:
        studio_api._resolve_clip_path("../../../etc/passwd.avi", _Cfg(video_root))
    assert e.value.status_code in (403, 404)


def test_bad_extension_rejected(video_root):
    with pytest.raises(HTTPException) as e:
        studio_api._resolve_clip_path("Demo (123)  - 40.exe", _Cfg(video_root))
    assert e.value.status_code == 400
