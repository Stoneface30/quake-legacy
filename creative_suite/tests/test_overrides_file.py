# creative_suite/tests/test_overrides_file.py
from __future__ import annotations

from pathlib import Path

from creative_suite.overrides.file_io import (
    ClipOverride, read_overrides, write_overrides,
)


def test_roundtrip_preserves_entries(tmp_path: Path) -> None:
    p = tmp_path / "part04_overrides.txt"
    entries = [
        ClipOverride(chunk="chunk_0014.mp4", slow=0.5, slow_window=1.6,
                     head_trim=None, tail_trim=None, section_role="peak"),
        ClipOverride(chunk="chunk_0088.mp4", slow=None, slow_window=None,
                     head_trim=0.5, tail_trim=None, section_role=None),
    ]
    write_overrides(p, entries)
    back = read_overrides(p)
    assert back == entries


def test_read_missing_returns_empty(tmp_path: Path) -> None:
    assert read_overrides(tmp_path / "nope.txt") == []
