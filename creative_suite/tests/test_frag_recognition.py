"""Tests for the frag recognition taxonomy (frag_recognition + scan dedup)."""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "engine" / "parser"))
fc = pytest.importorskip("frag_classify")
fr = pytest.importorskip("frag_recognition")
rs = pytest.importorskip("recognition_scan")


def _ent(client, t, z=0.0, ground=0, yaw=0.0, x=0.0, y=0.0):
    return {"client_num": client, "server_time_ms": t, "origin_x": x,
            "origin_y": y, "origin_z": z, "vel_x": 0.0, "vel_y": 0.0,
            "vel_z": 0.0, "angle_yaw": yaw, "angle_pitch": 0.0,
            "ground_entity": ground, "airborne": ground == 1023}


def _kill(t, killer=1, victim=2, weapon=fc.W_LIGHTNING, name="LIGHTNING"):
    return {"type": "obituary", "server_time_ms": t, "round": 0,
            "killer_client": killer, "victim_client": victim,
            "weapon": weapon, "weapon_name": name,
            "killer_name": "k", "victim_name": "v",
            "pos_x": 0.0, "pos_y": 0.0, "pos_z": 0.0}


def _rec(events, entities=None, accuracy=None, player=1):
    parsed = {"events": events, "entities": entities or [],
              "accuracy": accuracy or []}
    return fr.recognize(parsed, player=player, demo_name="test.dm_73")


def classes_of(r):
    return {c["name"]: c for c in r.classes}


# ── DIRECT_ROCKET ───────────────────────────────────────────────────────────

def test_direct_rocket_confirmed_from_mod():
    r = _rec([_kill(1000, weapon=fc.W_ROCKET, name="ROCKET")])[0]
    c = classes_of(r)
    assert "DIRECT_ROCKET" in c
    assert c["DIRECT_ROCKET"]["confidence"] == fr.CONFIRMED


def test_rocket_splash_is_not_direct():
    r = _rec([_kill(1000, weapon=fc.W_ROCKET_SPLASH, name="ROCKET_SPLASH")])[0]
    assert "DIRECT_ROCKET" not in classes_of(r)


# ── AIR_ROCKET: trivial hop rejection + height attribute ────────────────────

def _air_victim_ents(height):
    ents = [_ent(2, t, z=0.0, ground=0) for t in range(0, 3000, 100)]
    ents += [_ent(2, 3000, z=height, ground=1023)]
    return ents


def test_air_rocket_trivial_hop_rejected():
    """20u off the floor is a strafe hop, not an airshot."""
    r = _rec([_kill(3000, weapon=fc.W_ROCKET, name="ROCKET")],
             _air_victim_ents(20.0))[0]
    assert "AIR_ROCKET" not in classes_of(r)


def test_air_rocket_meaningful_height():
    r = _rec([_kill(3000, weapon=fc.W_ROCKET, name="ROCKET")],
             _air_victim_ents(150.0))[0]
    c = classes_of(r)
    assert "AIR_ROCKET" in c
    assert "meaningful air" in c["AIR_ROCKET"]["detail"]
    assert r.attributes["victim_air_height"] == pytest.approx(150.0)
    assert r.components["air_score"] > 0
    assert any("air rocket" in x for x in r.reasons)


def test_air_rocket_low_air_scores_less_than_meaningful():
    lo = _rec([_kill(3000, weapon=fc.W_ROCKET, name="ROCKET")],
              _air_victim_ents(60.0))[0]
    hi = _rec([_kill(3000, weapon=fc.W_ROCKET, name="ROCKET")],
              _air_victim_ents(200.0))[0]
    assert "AIR_ROCKET" in classes_of(lo)
    assert hi.components["air_score"] > lo.components["air_score"]


def test_air_grenade_separate_class_and_direct_bonus():
    direct = _rec([_kill(3000, weapon=fc.W_GRENADE, name="GRENADE")],
                  _air_victim_ents(150.0))[0]
    splash = _rec([_kill(3000, weapon=fc.W_GRENADE_SPLASH, name="GRENADE_SPLASH")],
                  _air_victim_ents(150.0))[0]
    assert "AIR_GRENADE" in classes_of(direct)
    assert "AIR_GRENADE" in classes_of(splash)
    assert direct.components["air_score"] > splash.components["air_score"]


# ── FLICK: attribute math + smooth-tracking rejection ───────────────────────

def test_flick_attributes_math():
    ents = [_ent(1, 900, yaw=0.0), _ent(1, 1000, yaw=90.0)]
    r = _rec([_kill(1000)], ents)[0]
    c = classes_of(r)
    assert "FLICK_SHOT" in c
    assert r.attributes["flick_degrees"] == pytest.approx(90.0)
    assert r.attributes["flick_duration_ms"] == 100
    assert r.attributes["deg_per_sec"] == pytest.approx(900.0)


def test_slow_sweep_is_tracking_not_flick():
    """Same total degrees over a long window = smooth tracking, no class."""
    tl = fc.Timeline([_ent(1, 0, yaw=0.0), _ent(1, 500, yaw=45.0),
                      _ent(1, 1000, yaw=90.0)])
    fl = fr.flick_attributes(tl, 1, 1000)
    # 90 deg over ~300ms window slice -> below FLICK_MIN_DPS check happens
    # in recognize(); verify the gate directly with a synthetic low rate
    assert fl is None or fl["deg_per_sec"] < 1e6  # attributes computable
    ents = [_ent(1, t, yaw=t * 0.05) for t in range(0, 1100, 100)]
    r = _rec([_kill(1000)], ents)[0]
    assert "FLICK_SHOT" not in classes_of(r)


# ── MULTIKILL chains: never merged across downtime ──────────────────────────

def test_multikill_chain_counts_and_attrs():
    ev = [_kill(1000, victim=2), _kill(2500, victim=3), _kill(4000, victim=4)]
    recs = _rec(ev)
    last = recs[-1]
    c = classes_of(last)
    assert "MULTIKILL_TRIPLE" in c
    mk = last.attributes["multikill"]
    assert mk["count"] == 3
    assert mk["duration_ms"] == 3000
    assert mk["victims"] == [2, 3, 4]
    assert max(mk["gaps_ms"]) == 1500
    assert any("3 kills" in x for x in last.reasons)


def test_multikill_not_merged_across_downtime():
    """Two doubles separated by 10s must never become a quad."""
    ev = [_kill(1000, victim=2), _kill(2000, victim=3),
          _kill(12000, victim=4), _kill(13000, victim=5)]
    recs = _rec(ev)
    names = [n for r in recs for n in r.class_names]
    assert "MULTIKILL_QUAD" not in names
    assert names.count("MULTIKILL_DOUBLE") == 2


def test_sliding_window_edge_is_not_a_triple():
    """Third kill within 3s of the first but >3s after the second: chain broken."""
    ev = [_kill(1000, victim=2), _kill(1500, victim=3), _kill(6000, victim=4)]
    recs = _rec(ev)
    assert "MULTIKILL_TRIPLE" not in [n for r in recs for n in r.class_names]


def test_replayed_obituary_burst_is_one_kill():
    """Real corpus artifact: one victim 'killed' 10x at 25ms intervals.

    A player cannot die twice inside respawn time -- the burst is the same
    kill replayed, and must collapse before multikill counting.
    """
    ev = [_kill(1000 + i * 25, victim=8, weapon=fc.W_RAILGUN, name="RAILGUN")
          for i in range(10)]
    recs = _rec(ev)
    assert len(recs) == 1
    names = [n for r in recs for n in r.class_names]
    assert "RAIL_CONSECUTIVE" not in names
    assert not any(n.startswith("MULTIKILL") for n in names)


def test_distinct_victims_close_together_still_count():
    """Fast real multikills (different victims) must NOT be collapsed."""
    ev = [_kill(1000, victim=2), _kill(1400, victim=3), _kill(1900, victim=4)]
    recs = _rec(ev)
    assert len(recs) == 3
    assert "MULTIKILL_TRIPLE" in recs[-1].class_names


# ── component score composition + reasons ───────────────────────────────────

def test_highlight_score_is_sum_of_components():
    r = _rec([_kill(3000, weapon=fc.W_ROCKET, name="ROCKET")],
             _air_victim_ents(150.0))[0]
    assert r.highlight_score == pytest.approx(sum(r.components.values()))
    assert len(r.reasons) >= len(r.components)
    assert all(x.startswith("+") for x in r.reasons)


def test_weapon_combo_class_and_score():
    ev = [_kill(1000, victim=2, weapon=fc.W_ROCKET, name="ROCKET"),
          _kill(1800, victim=3, weapon=fc.W_RAILGUN, name="RAILGUN")]
    r = _rec(ev)[1]
    c = classes_of(r)
    assert "WEAPON_COMBO" in c
    assert "rocket_rail" in c["WEAPON_COMBO"]["detail"]
    assert r.components["weapon_combo_score"] > 0


# ── confidence mapping ──────────────────────────────────────────────────────

def test_confidence_mapping():
    assert fr.map_confidence(fc.SOLID) == fr.HIGH
    assert fr.map_confidence(fc.PROXY) == fr.MEDIUM
    assert fr.map_confidence(fc.NEEDS_DATA) == fr.LOW_CANDIDATE
    assert fr.map_confidence("garbage") == fr.LOW_CANDIDATE


def test_lg_high_accuracy_says_overall():
    acc = [{"server_time_ms": 500, "client_num": 1, "accuracy": 55}]
    r = _rec([_kill(1000)], accuracy=acc)[0]
    c = classes_of(r)
    assert "LG_HIGH_ACCURACY" in c
    assert "OVERALL" in c["LG_HIGH_ACCURACY"]["detail"]


def test_pixel_shot_stays_candidate():
    ents = [_ent(1, t, x=0.0) for t in range(0, 3100, 100)]
    ents += [_ent(2, t, x=3000.0) for t in range(0, 3100, 100)]
    r = _rec([_kill(3000, weapon=fc.W_RAILGUN, name="RAILGUN")], ents)[0]
    c = classes_of(r)
    assert "PIXEL_SHOT_CANDIDATE" in c
    assert c["PIXEL_SHOT_CANDIDATE"]["confidence"] == fr.LOW_CANDIDATE
    assert r.attributes["distance"] == pytest.approx(3000.0)
    assert "visibility_ms" in r.attributes


def test_visibility_ms_measures_presence_run():
    # victim present 400ms before the kill, after a 2s gap
    ents = [_ent(2, 100), _ent(2, 2600), _ent(2, 2800), _ent(2, 3000)]
    tl = fc.Timeline(ents)
    assert fr.visibility_ms(tl, 2, 3000) == 400


# ── dedup of the same moment across two demo names ──────────────────────────

def _row(demo, t=5000, victim=2, mod=6, score=3.0):
    return {"demo_name": demo, "content_hash": "h_" + demo,
            "server_time_ms": t, "round": 0, "mod": mod,
            "weapon_name": "ROCKET", "victim_client": victim,
            "classes": [{"name": "DIRECT_ROCKET", "confidence": "CONFIRMED",
                         "detail": ""}],
            "attributes": {}, "highlight_score": score, "reasons": []}


def test_dedupe_same_moment_across_demos():
    match_group = {"a.dm_73": 0, "b.dm_73": 0}
    rows = [_row("a.dm_73", score=3.0), _row("b.dm_73", score=5.0)]
    out = rs.dedupe_rows(rows, match_group)
    assert len(out) == 1
    assert out[0]["demo_name"] == "b.dm_73"       # higher score kept
    assert out[0]["aliases"] == ["a.dm_73"]


def test_dedupe_never_merges_unrelated_matches():
    match_group = {"a.dm_73": 0, "b.dm_73": 1}    # different matches
    rows = [_row("a.dm_73"), _row("b.dm_73")]
    assert len(rs.dedupe_rows(rows, match_group)) == 2


def test_dedupe_keeps_different_moments_same_match():
    match_group = {"a.dm_73": 0}
    rows = [_row("a.dm_73", t=5000), _row("a.dm_73", t=9000)]
    assert len(rs.dedupe_rows(rows, match_group)) == 2
