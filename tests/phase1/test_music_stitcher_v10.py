"""v10 stitcher plan tests (no ffmpeg render, no fixtures)."""
from __future__ import annotations

import pytest

from phase1.music_stitcher import plan_stitch, resolve_main_pool


def test_resolve_main_pool_part4_has_multi_track():
    pool = resolve_main_pool(4)
    # Part 4 music/ has at least partNN_music_01.mp3
    assert len(pool) >= 1


def test_plan_stitch_part4_full_tracks_no_truncation():
    plan = plan_stitch(4, required_duration_s=600.0)
    # Ship gate — every track duration equals full_duration.
    for t in plan["tracks"]:
        assert abs(t["duration"] - t["full_duration"]) < 0.1, (
            f"track {t['path']} truncated"
        )
    assert plan["covered_s"] >= plan["main_needed_s"]


def test_plan_stitch_seams_all_4_to_6s():
    plan = plan_stitch(4, required_duration_s=400.0)
    for s in plan["seams"]:
        if s["kind"] == "main_to_main":
            assert 4.0 <= s["crossfade_s"] <= 6.0 + 0.01
