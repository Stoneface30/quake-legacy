"""Hit-to-beat placement math (§13, §23) and shortlist ranking (§25)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import hit_to_beat as h2b
from creative_suite.engine import music_shortlist as ms


BEATS = [i * 0.5 for i in range(0, 120)]  # 120 BPM grid, 60 s


def test_primary_frag_lands_exactly_on_beat():
    p = h2b.place_clip([5000], 5000, BEATS)
    assert p is not None
    # timeline start + offset must equal the chosen beat exactly
    assert abs((p.timeline_start_s + 5.0) - p.anchor_beat_s) < 1e-9
    assert p.per_kill[0][1] == 0  # zero ms gap to nearest beat


def test_start_never_negative():
    p = h2b.place_clip([30000], 30000, BEATS)
    assert p.timeline_start_s >= 0


def test_multikill_prefers_alignment_of_secondary_kills():
    # kills 500 ms apart == exactly one beat apart at 120 BPM: a grid-aligned
    # anchor scores every kill; kills 730 ms apart cannot all align.
    aligned = h2b.place_clip([5000, 5500, 6000], 6000, BEATS)
    off_grid = h2b.place_clip([5000, 5730, 6210], 6210, BEATS)
    assert aligned.score > off_grid.score


def test_search_window_restricts_anchor():
    p = h2b.place_clip([1000], 1000, BEATS, search_window_s=(20.0, 25.0))
    assert 20.0 <= p.anchor_beat_s <= 25.0


def test_bar_grid_estimate_is_mild_bonus_only():
    bars = BEATS[::4]
    with_bar = h2b.place_clip([5000], 5000, BEATS, bar_grid_estimate_s=bars)
    without = h2b.place_clip([5000], 5000, BEATS)
    assert with_bar.score >= without.score
    assert with_bar.score - without.score <= h2b.PRIMARY_WEIGHT * h2b.BAR_GRID_BONUS + 1e-9


def test_bpm_scoring_sweet_band():
    assert ms.bpm_score(135) == 1.0
    assert ms.bpm_score(67.5) == 1.0     # half-time detection doubles
    assert ms.bpm_score(85) > ms.bpm_score(None)
    assert ms.bpm_score(200) < 0.5


def test_rank_track_prefers_punchy_over_ambient():
    punchy = {"bpm": 140, "onset_rate": 3.2, "rms_mean": 0.18,
              "rms_p90": 0.30, "centroid": 2600, "duration_s": 210}
    ambient = {"bpm": 70, "onset_rate": 0.4, "rms_mean": 0.05,
               "rms_p90": 0.07, "centroid": 900, "duration_s": 400}
    assert ms.rank_track(punchy) > ms.rank_track(ambient) * 2
