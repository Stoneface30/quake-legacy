"""Beatmatch scoring must reward bar alignment, not tempo popularity.

The selection objective is that a cut lands on a DOWNBEAT: the episode's mean
clip length should span close to a whole number of bars. A scorer that merely
liked "around 128 BPM" would pick tracks the edit drifts against within two
cuts.
"""
from __future__ import annotations

import pytest

from creative_suite.engine import music_beatmatch as MB


def test_whole_bars_scores_one():
    # 120 BPM -> 2 s per beat -> 8 s is exactly 4 bars.
    assert MB.bar_fit(120.0, 8.0) == pytest.approx(1.0, abs=1e-6)


def test_half_bar_offset_scores_zero():
    # 120 BPM, 4 beats/bar -> one bar is 2 s. 9 s = 4.5 bars: worst case.
    assert MB.bar_fit(120.0, 9.0) == pytest.approx(0.0, abs=1e-6)


def test_fit_is_symmetric_around_a_bar_line():
    early = MB.bar_fit(120.0, 7.8)
    late = MB.bar_fit(120.0, 8.2)
    assert early == pytest.approx(late, abs=1e-6)


def test_zero_and_negative_inputs_are_safe():
    assert MB.bar_fit(0.0, 10.0) == 0.0
    assert MB.bar_fit(120.0, 0.0) == 0.0
    assert MB.bar_fit(-5.0, 10.0) == 0.0
    assert MB.bar_fit(None, 10.0) == 0.0


def test_a_track_too_short_for_its_stretch_is_disqualified():
    song = {"bpm": 120.0, "duration_s": 60.0, "rms_p90": 0.12}
    assert MB.score_song(song, mean_clip_s=8.0, min_duration_s=150.0,
                         want_energy=0.12) < 0


def test_absurd_tempo_cannot_win_on_bar_fit_alone():
    """A doubled/halved tempo estimate can fit the grid perfectly by accident."""
    sane = {"bpm": 120.0, "duration_s": 300.0, "rms_p90": 0.12}
    absurd = {"bpm": 240.0, "duration_s": 300.0, "rms_p90": 0.12}
    # both land on whole bars for this clip length
    assert MB.bar_fit(120.0, 8.0) == pytest.approx(1.0, abs=1e-6)
    assert MB.bar_fit(240.0, 8.0) == pytest.approx(1.0, abs=1e-6)
    assert (MB.score_song(sane, 8.0, 150.0, 0.12)
            > MB.score_song(absurd, 8.0, 150.0, 0.12))


def test_better_bar_fit_beats_worse_at_equal_tempo_and_energy():
    good = {"bpm": 120.0, "duration_s": 300.0, "rms_p90": 0.12}
    bad = {"bpm": 121.5, "duration_s": 300.0, "rms_p90": 0.12}
    assert (MB.score_song(good, 8.0, 150.0, 0.12)
            >= MB.score_song(bad, 8.0, 150.0, 0.12))


def test_content_id_is_stable_and_content_keyed(tmp_path):
    """Identity must follow bytes, not names -- the library repeats songs."""
    a = tmp_path / "one.mp3"
    b = tmp_path / "two.mp3"
    a.write_bytes(b"same bytes")
    b.write_bytes(b"same bytes")
    c = tmp_path / "three.mp3"
    c.write_bytes(b"different bytes!")
    assert MB.content_id(a) == MB.content_id(b)
    assert MB.content_id(a) != MB.content_id(c)
    assert MB.content_id(a) == MB.content_id(a)


def test_missing_file_yields_empty_id_rather_than_raising(tmp_path):
    assert MB.content_id(tmp_path / "nope.mp3") == ""
