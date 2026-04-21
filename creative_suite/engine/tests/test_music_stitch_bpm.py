"""Tests for Rule P1-AA v2 music_stitcher plan_stitch_v2 + ship gate."""
from __future__ import annotations

import pytest

from creative_suite.engine import music_stitcher as ms


def test_classify_seam_overlap_8bar_when_bpm_close():
    strategy, delta = ms._classify_seam_strategy(140.0, 142.0)
    assert strategy == "overlap_8bar"
    assert delta == pytest.approx(2.0)


def test_classify_seam_bpm_stretch_when_close_enough_to_match():
    strategy, delta = ms._classify_seam_strategy(140.0, 146.0)
    assert strategy == "bpm_stretch"


def test_classify_seam_afade_when_bpm_gap_wide():
    strategy, delta = ms._classify_seam_strategy(140.0, 170.0)
    assert strategy == "afade_fallback"


def test_classify_seam_afade_when_bpm_unknown():
    strategy, delta = ms._classify_seam_strategy(0.0, 140.0)
    assert strategy == "afade_fallback"


def test_phrase_truncate_keeps_full_when_target_exceeds():
    dur, bt = ms._phrase_truncate(full_dur=120.0, target_dur=130.0,
                                   phrase_boundaries=[30.0, 60.0, 90.0])
    assert dur == 120.0
    assert bt == "natural"


def test_phrase_truncate_snaps_down_to_phrase_boundary():
    dur, bt = ms._phrase_truncate(full_dur=180.0, target_dur=100.0,
                                   phrase_boundaries=[30.0, 60.0, 90.0, 135.0])
    assert dur == 90.0
    assert bt == "phrase"


def test_phrase_truncate_no_boundaries_keeps_full():
    dur, bt = ms._phrase_truncate(full_dur=180.0, target_dur=100.0,
                                   phrase_boundaries=[])
    assert dur == 180.0
    assert bt == "natural"


def test_plan_stitch_v2_skeleton_via_mock(monkeypatch, tmp_path):
    """Validate plan_stitch_v2 end-to-end via mocked file resolution + probes."""
    # Create fake files (need to exist on disk for resolve_main_pool paths).
    fake_main = [tmp_path / f"fake_main_{i}.mp3" for i in (1, 2, 3)]
    for p in fake_main:
        p.write_bytes(b"fake")
    fake_intro = tmp_path / "fake_intro.mp3"; fake_intro.write_bytes(b"fake")
    fake_outro = tmp_path / "fake_outro.mp3"; fake_outro.write_bytes(b"fake")

    # Durations: 200, 200, 150 (last = target to force truncation + phrase snap)
    durations = {
        str(fake_main[0]): 200.0,
        str(fake_main[1]): 200.0,
        str(fake_main[2]): 150.0,
        str(fake_intro):   15.0,
        str(fake_outro):   30.0,
    }
    bpms = {
        str(fake_main[0]): 140.0,
        str(fake_main[1]): 141.0,   # → overlap_8bar with track 0
        str(fake_main[2]): 148.0,   # → bpm_stretch with track 1 (delta=7)
        str(fake_intro):   0.0,
        str(fake_outro):   0.0,
    }
    phrases = {
        str(fake_main[2]): [30.0, 60.0, 90.0, 120.0, 135.0, 148.0],
    }
    monkeypatch.setattr(ms, "resolve_main_pool", lambda part: fake_main)
    monkeypatch.setattr(ms, "resolve_intro_outro",
                        lambda part, kind: fake_intro if kind == "intro" else fake_outro)
    monkeypatch.setattr(ms, "probe_duration", lambda p: durations[str(p)])
    monkeypatch.setattr(ms, "_bpm_for_track", lambda p: bpms[str(p)])
    monkeypatch.setattr(ms, "_downbeats_for_track",
                        lambda p: [i * 2.0 for i in range(5)])
    monkeypatch.setattr(ms, "_phrase_boundaries_for_track",
                        lambda p: phrases.get(str(p), []))

    body = 8 * 60.0  # 8 minutes of body
    plan = ms.plan_stitch_v2(part=4, body_duration_s=body,
                              crossfade_budget=6.0,
                              intro_xfade=1.5, outro_xfade=2.0,
                              outro_duration_s=30.0)
    # Expect: intro + track0 (full 200) + track1 (full 200) + track2 (truncated to a phrase boundary) + outro
    main_tracks = [t for t in plan["tracks"] if t["role"] == "main"]
    assert len(main_tracks) == 3
    assert main_tracks[0]["duration"] == 200.0
    assert main_tracks[1]["duration"] == 200.0
    # Last main truncated at phrase boundary
    last = main_tracks[-1]
    assert last["duration"] < last["full_duration"]
    assert last["truncation_boundary"] == "phrase"
    # Seam strategies: there are 4 seams total (intro_to_main, main0_main1, main1_main2, main2_to_outro)
    strategies = [s["seam_strategy"] for s in plan["seams"]]
    assert "overlap_8bar" in strategies
    assert "bpm_stretch" in strategies


def test_ship_gate_allows_phrase_truncation_on_last_main(tmp_path):
    plan = {
        "part": 4,
        "tracks": [
            {"path": "intro.mp3", "full_duration": 15.0, "duration": 15.0,
             "role": "intro", "truncation_boundary": "natural"},
            {"path": "main1.mp3", "full_duration": 200.0, "duration": 200.0,
             "role": "main", "truncation_boundary": "natural"},
            {"path": "main2.mp3", "full_duration": 150.0, "duration": 90.0,
             "role": "main", "truncation_boundary": "phrase"},
            {"path": "outro.mp3", "full_duration": 30.0, "duration": 30.0,
             "role": "outro", "truncation_boundary": "natural"},
        ],
    }
    # Must not raise
    out = ms.write_music_plan_json(part=4, plan=plan, out_dir=tmp_path)
    assert out.exists()


def test_ship_gate_rejects_mid_bar_truncation(tmp_path):
    plan = {
        "part": 4,
        "tracks": [
            {"path": "main1.mp3", "full_duration": 200.0, "duration": 150.0,
             "role": "main", "truncation_boundary": "natural"},
            {"path": "main2.mp3", "full_duration": 150.0, "duration": 150.0,
             "role": "main", "truncation_boundary": "natural"},
        ],
    }
    with pytest.raises(RuntimeError):
        ms.write_music_plan_json(part=4, plan=plan, out_dir=tmp_path)
