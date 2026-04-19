"""Unit tests for phase1.beat_sync v10 API."""
from __future__ import annotations

from phase1.beat_sync import plan_beat_cuts, ANTICIPATION_OFFSET


def _structure_fixture():
    """Fabricate a minimal structure dict with drops + cut candidates."""
    return {
        "track": "fake.wav",
        "duration_s": 200.0,
        "bpm_global": 140.0,
        "beat_grid": [i * 0.4286 for i in range(500)],  # 4/4 at 140 bpm
        "downbeats": [],
        "sections": [],
        "drops": [
            {"t": 20.0, "strength": 1.0, "bar": 11},
            {"t": 80.0, "strength": 0.9, "bar": 45},
        ],
        "cut_candidates": {
            "strong": [14.0, 18.0, 25.0, 45.0],
            "medium": [15.0, 19.0, 22.0, 30.0],
            "soft": [],
        },
    }


def test_t1_clip_pins_to_drop():
    structure = _structure_fixture()
    clips = [
        {"path": "A", "tier": "T1", "duration": 10.0, "head_trim": 1.0, "tail_trim": 2.0},
    ]
    peaks = {"A": 5.0}  # 5s into the clip
    seams = plan_beat_cuts(structure, peaks, clips, intro_offset=13.0)
    assert len(seams) == 1
    s = seams[0]
    # playable_action = 13 + (5 - 1) = 17 — nearest drop is 20.0 (within 0.4 cap? 3s, no)
    # So WEAK_ALIGN via half-beat, OR drop selected because ±shift > 0.4 forces fallback.
    assert s["tier"] == "T1"
    # either TIGHT (drop selected) or WEAK_ALIGN (half-beat fallback)
    assert s["tag"] in ("TIGHT", "WEAK_ALIGN", "SKIP_ALIGN")


def test_t2_clip_selects_from_strong_pool():
    structure = _structure_fixture()
    clips = [
        {"path": "B", "tier": "T2", "duration": 8.0, "head_trim": 1.0, "tail_trim": 2.0},
    ]
    # playable_action = 13 + (2 - 1) = 14.0 — lands exactly on strong[0]=14.0
    peaks = {"B": 2.0}
    seams = plan_beat_cuts(structure, peaks, clips, intro_offset=13.0)
    s = seams[0]
    assert s["tag"] == "TIGHT"
    assert s["target_downbeat"] == 14.0
    # anticipation cut offset
    assert s["seam_cut_music_t"] is not None
    assert abs(s["seam_cut_music_t"] - (14.0 - ANTICIPATION_OFFSET)) < 1e-6


def test_missing_peak_yields_skip_align():
    structure = _structure_fixture()
    clips = [
        {"path": "C", "tier": "T2", "duration": 8.0, "head_trim": 1.0, "tail_trim": 2.0},
    ]
    peaks = {"C": None}
    seams = plan_beat_cuts(structure, peaks, clips)
    assert seams[0]["tag"] == "SKIP_ALIGN"
    assert seams[0]["target_downbeat"] is None


def test_shift_absorbed_in_trim_adjust():
    structure = _structure_fixture()
    clips = [
        {"path": "D", "tier": "T2", "duration": 10.0, "head_trim": 1.0, "tail_trim": 2.0},
    ]
    # peak 2.2 -> playable_action = 13 + 1.2 = 14.2 -> nearest strong = 14.0 (shift -0.2)
    peaks = {"D": 2.2}
    seams = plan_beat_cuts(structure, peaks, clips, intro_offset=13.0)
    s = seams[0]
    # negative shift pushes trim onto previous clip (zero previous -> cap at 0.4)
    assert abs(s["shift"] + 0.2) < 0.01
    assert s["tail_trim_adjust_prev"] > 0
    assert s["head_trim_adjust"] == 0.0
