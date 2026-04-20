# phase1/tests/test_clip_filter.py
from __future__ import annotations

from pathlib import Path

from phase1.clip_filter import filter_chunks, load_removed_chunks


def test_filter_chunks_drops_removed_preserves_order(tmp_path: Path) -> None:
    chunks = [
        tmp_path / "chunk_0001.mp4",
        tmp_path / "chunk_0002.mp4",
        tmp_path / "chunk_0003.mp4",
        tmp_path / "chunk_0004.mp4",
    ]
    removed = {"chunk_0002.mp4", "chunk_0004.mp4"}
    out = filter_chunks(chunks, removed)
    assert [p.name for p in out] == ["chunk_0001.mp4", "chunk_0003.mp4"]


def test_filter_chunks_empty_removed_is_identity(tmp_path: Path) -> None:
    chunks = [tmp_path / f"chunk_{i:04d}.mp4" for i in range(3)]
    out = filter_chunks(chunks, set())
    assert out == chunks


def test_load_removed_chunks_missing_file_returns_empty(tmp_path: Path) -> None:
    assert load_removed_chunks(part=99, output_dir=tmp_path) == set()


def test_load_removed_chunks_reads_removed_flag(tmp_path: Path) -> None:
    from creative_suite.overrides.file_io import ClipOverride, write_overrides
    p = tmp_path / "part05_overrides.txt"
    write_overrides(p, [
        ClipOverride(chunk="chunk_0001.mp4", removed=True),
        ClipOverride(chunk="chunk_0002.mp4", slow=0.5),
        ClipOverride(chunk="chunk_0003.mp4", removed=True),
    ])
    assert load_removed_chunks(part=5, output_dir=tmp_path) == {
        "chunk_0001.mp4", "chunk_0003.mp4",
    }
