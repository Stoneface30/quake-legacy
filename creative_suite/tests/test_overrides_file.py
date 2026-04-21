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


def test_removed_flag_roundtrips(tmp_path: Path) -> None:
    """Tier 1 clip-removal: `removed=true` must survive write -> read."""
    p = tmp_path / "part04_overrides.txt"
    entries = [
        ClipOverride(chunk="chunk_0014.mp4", removed=True),
        ClipOverride(chunk="chunk_0088.mp4", removed=False, slow=0.5),
        ClipOverride(chunk="chunk_0099.mp4"),  # default False
    ]
    write_overrides(p, entries)
    back = read_overrides(p)
    assert back[0].removed is True
    assert back[0].chunk == "chunk_0014.mp4"
    assert back[1].removed is False
    assert back[1].slow == 0.5
    assert back[2].removed is False


def test_removed_only_written_when_true(tmp_path: Path) -> None:
    """Don't pollute old overrides.txt files with redundant `removed=false`."""
    p = tmp_path / "part04_overrides.txt"
    write_overrides(p, [ClipOverride(chunk="chunk_0001.mp4", slow=0.5)])
    text = p.read_text(encoding="utf-8")
    assert "removed=" not in text


def test_removed_absent_in_file_reads_false(tmp_path: Path) -> None:
    """Legacy overrides files (no `removed=` token) must read as removed=False."""
    p = tmp_path / "part04_overrides.txt"
    p.write_text("chunk=chunk_0001.mp4 slow=0.5\n", encoding="utf-8")
    entries = read_overrides(p)
    assert entries[0].removed is False
