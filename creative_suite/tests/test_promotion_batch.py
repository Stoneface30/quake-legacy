"""Capture-phase batch builder tests: tiers, diversity, clutch overlap."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine" / "parser"))

import promotion_batch as pb


def _w(score=10.0, n_kills=1, tags="", weapons="ROCKET", weapon="ROCKET",
       clutch=None, demo="a.dm_73", h="H", start=0, end=10000, **kw):
    d = {"score": score, "n_kills": n_kills, "tags": tags, "weapons": weapons,
         "weapon": weapon, "map": "overkill", "demo": demo,
         "canonical_demo_hash": h, "capture_start_ms": start,
         "capture_end_ms": end, "class": "NORMAL",
         "clutch_context": json.dumps(clutch) if clutch else None}
    d.update(kw)
    return d


def test_tier_s_1v4():
    w = _w(clutch={"enemies_alive_at_start": 4, "kills_during_clutch": 4,
                   "weapons": "ROCKET", "outcome": "WIN"})
    assert pb.assign_tier(w) == "S"


def test_tier_s_big_multikill():
    assert pb.assign_tier(_w(n_kills=4)) == "S"


def test_tier_s_air_rocket_high_score():
    assert pb.assign_tier(_w(score=26, tags="air_rocket")) == "S"


def test_tier_a_1v2():
    w = _w(clutch={"enemies_alive_at_start": 2, "kills_during_clutch": 2,
                   "weapons": "ROCKET", "outcome": "WIN"})
    assert pb.assign_tier(w) == "A"


def test_tier_a_rail_run():
    assert pb.assign_tier(_w(n_kills=2, weapons="RAILGUN")) == "A"


def test_tier_b_plain():
    assert pb.assign_tier(_w(score=5.0)) == "B"


def test_alt_angle_only_s():
    assert pb.alt_angle_worthy(_w(score=26, tags="air_rocket")) is True
    assert pb.alt_angle_worthy(_w(score=5.0, tags="air_rocket")) is False


def test_diversity_breaks_near_ties_only():
    # w_hi is clearly better and must be first despite duplicating the map
    windows = [_w(score=30, demo="x1", map="campgrounds"),
               _w(score=29.9, demo="x2", map="campgrounds"),
               _w(score=29.5, weapon="RAILGUN", demo="x3", map="asylum"),
               _w(score=10, demo="x4")]
    picked = pb.select_diverse(windows, n=3)
    assert picked[0]["demo"] == "x1"
    # near-tie band: asylum/railgun should jump ahead of second campgrounds
    assert picked[1]["demo"] == "x3"
    assert picked[2]["demo"] == "x2"


def test_diversity_never_demotes_clear_winner():
    windows = [_w(score=40, demo="best", map="m1"),
               _w(score=20, demo="other", map="m2")]
    assert pb.select_diverse(windows, n=1)[0]["demo"] == "best"


def test_clutch_supplement_skips_covered():
    picked = [_w(h="H1", start=90000, end=120000)]
    clutch_cov = {"canonical_demo_hash": "H1", "clutch_start_ms": "95000",
                  "clutch_end_ms": "115000", "rank_score": "20", "round": "1"}
    clutch_new = {"canonical_demo_hash": "H2", "clutch_start_ms": "10000",
                  "clutch_end_ms": "30000", "rank_score": "18", "round": "2"}
    all_windows = picked + [_w(h="H2", start=5000, end=35000, score=15)]
    extra = pb.clutch_supplement(picked, all_windows, [clutch_cov, clutch_new])
    assert len(extra) == 1
    assert extra[0]["canonical_demo_hash"] == "H2"
