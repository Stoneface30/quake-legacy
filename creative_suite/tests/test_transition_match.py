"""PROJECTILE_BRIDGE Scene B shortlisting."""
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import transition_match as tm

RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"


def mkpath(duration_ms=2000, speed=200.0, pitch=0.0, n=20, kind="rocket"):
    """Synthetic straight-line flight with a given speed and vertical slope."""
    pts = []
    for i in range(n):
        t = duration_ms * i / (n - 1)
        dist = speed * (t / 1000.0)
        pts.append([t, dist, 0.0, dist * pitch])
    return {"kind": kind, "points": pts, "confidence": "CONFIRMED",
            "launch": {"t": 100000, "pos": pts[0][1:], "dir": None},
            "impact": {"t": 100000 + duration_ms, "pos": pts[-1][1:]}}


def scene(map_name="a", demo="d1.dm_73", score=30.0, **kw):
    m = tm.path_metrics(mkpath(**kw))
    return {"frag_id": 1, "demo_name": demo, "server_time_ms": 1000,
            "map": map_name, "highlight_score": score, "classes": [], **m}


# ── path_metrics ─────────────────────────────────────────────────────────────

def test_path_metrics_speed_and_duration():
    m = tm.path_metrics(mkpath(duration_ms=2000, speed=200.0))
    assert m["duration_ms"] == 2000
    assert m["speed_ups"] == pytest.approx(200.0, abs=1.0)


def test_path_metrics_rejects_too_short_flight():
    assert tm.path_metrics(mkpath(duration_ms=100)) is None
    assert tm.path_metrics({"points": []}) is None


def test_path_metrics_pitch_sign():
    level = tm.path_metrics(mkpath(pitch=0.0))
    dive = tm.path_metrics(mkpath(pitch=-1.0))
    assert abs(level["launch_pitch"]) < 0.1
    assert dive["launch_pitch"] < -0.5


# ── scoring ──────────────────────────────────────────────────────────────────

def test_speed_match_is_scale_free_ratio():
    a = scene(speed=200.0)
    same = scene(speed=200.0, demo="d2.dm_73")
    half = scene(speed=100.0, demo="d2.dm_73")
    assert tm.score_pair(a, same)["speed_match"] == pytest.approx(1.0, abs=0.01)
    assert tm.score_pair(a, half)["speed_match"] == pytest.approx(0.5, abs=0.05)


def test_pitch_mismatch_lowers_score():
    a = scene(pitch=0.0)
    level = scene(pitch=0.0, demo="d2.dm_73")
    dive = scene(pitch=-1.0, demo="d2.dm_73")
    assert (tm.score_pair(a, level)["pitch_match"]
            > tm.score_pair(a, dive)["pitch_match"])


def test_payoff_rewards_higher_scoring_scene_b():
    a = scene()
    lo = scene(score=5.0, demo="d2.dm_73")
    hi = scene(score=50.0, demo="d2.dm_73")
    assert tm.score_pair(a, hi)["total"] > tm.score_pair(a, lo)["total"]


def test_different_map_bonus_is_configurable_not_hardcoded():
    a = scene(map_name="trinity")
    same = scene(map_name="trinity", demo="d2.dm_73")
    diff = scene(map_name="asylum", demo="d2.dm_73")
    with_bonus = (tm.score_pair(a, diff, prefer_different_map=0.15)["total"]
                  - tm.score_pair(a, same, prefer_different_map=0.15)["total"])
    assert with_bonus == pytest.approx(0.15, abs=1e-6)
    no_bonus = (tm.score_pair(a, diff, prefer_different_map=0.0)["total"]
                - tm.score_pair(a, same, prefer_different_map=0.0)["total"])
    assert no_bonus == pytest.approx(0.0, abs=1e-6)


# ── shortlisting ─────────────────────────────────────────────────────────────

def test_shortlist_excludes_same_demo():
    """Cutting within one demo is a jump cut, not a bridge."""
    a = scene(demo="same.dm_73")
    cands = [scene(demo="same.dm_73"), scene(demo="other.dm_73")]
    out = tm.shortlist_scene_b(a, cands)
    assert all(c["demo_name"] != "same.dm_73" for c in out)


def test_shortlist_excludes_insufficient_runway():
    a = scene()
    short_b = scene(demo="d2.dm_73", duration_ms=500)
    assert tm.shortlist_scene_b(a, [short_b]) == []


def test_shortlist_is_sorted_descending():
    a = scene()
    cands = [scene(demo=f"d{i}.dm_73", score=s)
             for i, s in enumerate([5.0, 50.0, 25.0], start=2)]
    out = tm.shortlist_scene_b(a, cands)
    totals = [c["match"]["total"] for c in out]
    assert totals == sorted(totals, reverse=True)


# ── real-data guards ─────────────────────────────────────────────────────────

@pytest.mark.skipif(not RECOG_DB.exists(), reason="frag_recognition.db absent")
def test_map_names_never_parsed_from_filename():
    """Regression: a positional filename split misread demos shaped
    CA-<map>-<date> (no player field) as a map named e.g. '2011_07_18'.
    Map names must come from the authoritative demos table."""
    cands = tm.load_candidates()
    if not cands:
        pytest.skip("no cached projectile paths")
    bad = [c for c in cands if c["map"][:2].isdigit()]
    assert not bad, f"{len(bad)} candidates have date-like map names"


@pytest.mark.skipif(not RECOG_DB.exists(), reason="frag_recognition.db absent")
def test_real_shortlist_produces_manageable_list():
    cands = tm.load_candidates()
    if len(cands) < 10:
        pytest.skip("not enough cached paths")
    a = tm.pick_scene_a(cands)
    assert a is not None
    out = tm.shortlist_scene_b(a, cands, top_n=20)
    assert 0 < len(out) <= 20
