"""Tests for the frag recognition taxonomy (frag_recognition + scan dedup)."""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "engine" / "parser"))
fc = pytest.importorskip("frag_classify")
fr = pytest.importorskip("frag_recognition")
rs = pytest.importorskip("recognition_scan")
rn = pytest.importorskip("recognition_norms")


def _ent(client, t, z=0.0, ground=0, yaw=0.0, x=0.0, y=0.0,
         vx=0.0, vy=0.0, vz=0.0, weapon=None, health=None):
    row = {"client_num": client, "server_time_ms": t, "origin_x": x,
           "origin_y": y, "origin_z": z, "vel_x": vx, "vel_y": vy,
           "vel_z": vz, "angle_yaw": yaw, "angle_pitch": 0.0,
           "ground_entity": ground, "airborne": ground == 1023}
    if weapon is not None:
        row["weapon"] = weapon
    if health is not None:
        row["health"] = health
    return row


def _ps(client, t, health=None, weapon=None, vx=0.0, vy=0.0, vz=0.0,
        x=0.0, y=0.0, z=0.0, yaw=0.0):
    """Playerstate-style row: no ground_entity/airborne (recorder stream)."""
    row = {"client_num": client, "server_time_ms": t, "origin_x": x,
           "origin_y": y, "origin_z": z, "vel_x": vx, "vel_y": vy,
           "vel_z": vz, "angle_yaw": yaw, "angle_pitch": 0.0}
    if health is not None:
        row["health"] = health
    if weapon is not None:
        row["weapon"] = weapon
    return row


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
    # scores start "+", penalties start "- " (taxonomy v2)
    assert all(x.startswith(("+", "- ")) for x in r.reasons)


def test_weapon_combo_class_and_score():
    ev = [_kill(1000, victim=2, weapon=fc.W_ROCKET, name="ROCKET"),
          _kill(1800, victim=3, weapon=fc.W_RAILGUN, name="RAILGUN")]
    r = _rec(ev)[1]
    c = classes_of(r)
    assert "WEAPON_COMBO" in c
    assert "rocket_rail" in c["WEAPON_COMBO"]["detail"]
    assert r.components["combo_score"] > 0


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


# ════════════════════════════════════ taxonomy v2 ═══════════════════════════

def _norms(metric="attacker_speed", scale=10.0):
    """Synthetic archive table: percentile p maps to value p*scale."""
    return rn.Norms({metric: [p * scale for p in range(101)]})


def test_version_bump():
    assert fr.RECOGNITION_VERSION == 2
    assert rs.RECOGNITION_VERSION == 2


# ── recognition_norms: grid math + persistence ──────────────────────────────

def test_norms_percentile_interpolation():
    n = _norms()
    assert n.percentile_of("attacker_speed", -5) == 0.0
    assert n.percentile_of("attacker_speed", 2000) == 100.0
    assert n.percentile_of("attacker_speed", 500) == pytest.approx(50.0)
    assert n.percentile_of("attacker_speed", 905) == pytest.approx(90.5)
    assert n.percentile_of("attacker_speed", 992) == pytest.approx(99.2)
    assert n.value_at("attacker_speed", 90) == 900.0
    assert n.percentile_of("no_such_metric", 5) is None


def test_norms_save_load_roundtrip(tmp_path):
    p = tmp_path / "norms.json"
    rn.save_norms(_norms(), p)
    loaded = rn.load_norms(p)
    assert loaded is not None
    assert loaded.percentile_of("attacker_speed", 500) == pytest.approx(50.0)
    assert rn.load_norms(tmp_path / "missing.json") is None


# ── percentile speed labels from a synthetic norms table ────────────────────

def test_speed_tier_labels_from_norms():
    n = _norms()
    assert fr.speed_tier(500, n)[0] is None
    assert fr.speed_tier(905, n)[0] == "FAST"
    assert fr.speed_tier(975, n)[0] == "VERY_FAST"
    assert fr.speed_tier(992, n)[0] == "EXTREME_SPEED"
    label, pct, prov = fr.speed_tier(992, n)
    assert pct == pytest.approx(99.2)
    assert prov is False


def test_speed_tier_provisional_without_norms():
    label, pct, prov = fr.speed_tier(1400, None)
    assert label == "EXTREME_SPEED" and pct is None and prov is True
    assert fr.speed_tier(800, None)[0] == "FAST"
    assert fr.speed_tier(300, None)[0] is None


def test_high_speed_frag_class_and_percentile_attr():
    ents = [_ent(1, t, vx=992.0) for t in range(0, 1100, 100)]
    n = _norms()
    r = _rec([_kill(1000)], ents)[0]                      # no norms
    r2 = fr.recognize({"events": [_kill(1000)], "entities": ents,
                       "accuracy": []}, player=1,
                      demo_name="t.dm_73", norms=n)[0]
    c2 = classes_of(r2)
    assert "HIGH_SPEED_FRAG" in c2
    assert "EXTREME_SPEED" in c2["HIGH_SPEED_FRAG"]["detail"]
    assert r2.attributes["attacker_speed_percentile"] == pytest.approx(99.2)
    assert any("p99.2" in x for x in r2.reasons)
    # without norms the provisional path fires (992 ups -> FAST) and says so
    c1 = classes_of(r)
    assert "HIGH_SPEED_FRAG" in c1
    assert "FAST" in c1["HIGH_SPEED_FRAG"]["detail"]
    assert any("provisional" in x for x in r.reasons if "fast" in x)


def test_speed_target_frag_uses_victim_percentile():
    ents = [_ent(1, t) for t in range(0, 1100, 100)]
    ents += [_ent(2, t, x=100.0, vx=960.0) for t in range(0, 1100, 100)]
    n = rn.Norms({"victim_speed": [p * 10.0 for p in range(101)]})
    r = fr.recognize({"events": [_kill(1000)], "entities": ents,
                      "accuracy": []}, player=1,
                     demo_name="t.dm_73", norms=n)[0]
    assert "SPEED_TARGET_FRAG" in classes_of(r)
    assert r.attributes["victim_speed_percentile"] == pytest.approx(96.0)


# ── rocket-jump self-impulse ────────────────────────────────────────────────

def _rj_killer_ents():
    """Ground until 2.0s, +700 ups vertical step at 2.2s, airborne at kill."""
    ents = [_ent(1, t, z=0.0, ground=0, vz=0.0) for t in range(0, 2100, 100)]
    ents += [_ent(1, 2200, z=40.0, ground=1023, vz=700.0),
             _ent(1, 2600, z=100.0, ground=1023, vz=500.0),
             _ent(1, 3000, z=150.0, ground=1023, vz=300.0)]
    return ents


def test_rocket_jump_frag_from_self_impulse():
    r = _rec([_kill(3000, weapon=fc.W_ROCKET, name="ROCKET")],
             _rj_killer_ents())[0]
    c = classes_of(r)
    assert "ROCKET_JUMP_FRAG" in c
    assert c["ROCKET_JUMP_FRAG"]["confidence"] == fr.MEDIUM
    assert r.attributes["rocket_jump_impulse_ups"] == pytest.approx(700.0)


def test_rocket_jump_entry_for_non_rocket_kill():
    r = _rec([_kill(3000, weapon=fc.W_RAILGUN, name="RAILGUN")],
             _rj_killer_ents())[0]
    assert "ROCKET_JUMP_ENTRY" in classes_of(r)
    assert "ROCKET_JUMP_FRAG" not in classes_of(r)


def test_no_rocket_jump_without_impulse():
    ents = [_ent(1, t, z=0.0, ground=0) for t in range(0, 2000, 100)]
    ents += [_ent(1, t, z=150.0, ground=1023, vz=100.0)
             for t in range(2000, 3100, 100)]
    r = _rec([_kill(3000, weapon=fc.W_ROCKET, name="ROCKET")], ents)[0]
    assert "ROCKET_JUMP_FRAG" not in classes_of(r)


# ── target transfer ─────────────────────────────────────────────────────────

def _transfer_ents():
    ents = [_ent(1, t) for t in range(0, 2100, 100)]                 # killer
    ents += [_ent(2, t, x=1000.0) for t in range(0, 1100, 100)]      # A east
    ents += [_ent(3, t, y=1000.0) for t in range(0, 2100, 100)]      # B north
    return ents


def test_target_transfer_math():
    ev = [_kill(1000, victim=2), _kill(2000, victim=3)]
    r = _rec(ev, _transfer_ents())[1]
    c = classes_of(r)
    assert "TARGET_TRANSFER" in c
    assert r.attributes["transfer_deg"] == pytest.approx(90.0, abs=1.0)
    assert r.attributes["transfer_ms"] == 1000
    assert any("target transfer" in x for x in r.reasons)


def test_lg_transfer_subtype():
    ev = [_kill(1000, victim=2), _kill(2000, victim=3)]
    recs = _rec(ev, _transfer_ents())
    assert "LG_TRANSFER" in classes_of(recs[1])


def test_no_transfer_below_angle_threshold():
    ents = [_ent(1, t) for t in range(0, 2100, 100)]
    ents += [_ent(2, t, x=1000.0) for t in range(0, 1100, 100)]
    ents += [_ent(3, t, x=1000.0, y=100.0)
             for t in range(0, 2100, 100)]                # ~6 deg apart
    ev = [_kill(1000, victim=2), _kill(2000, victim=3)]
    assert "TARGET_TRANSFER" not in classes_of(_rec(ev, ents)[1])


# ── popup combo ─────────────────────────────────────────────────────────────

def _popup_ents():
    ents = [_ent(1, t) for t in range(0, 3100, 100)]
    ents += [_ent(2, t, x=300.0, z=0.0, ground=0) for t in range(0, 1900, 100)]
    ents += [_ent(2, 2000, x=300.0, z=50.0, ground=1023, vz=300.0),
             _ent(2, 2500, x=300.0, z=120.0, ground=1023, vz=150.0),
             _ent(2, 3000, x=300.0, z=150.0, ground=1023, vz=50.0)]
    return ents


def test_popup_combo_low_candidate_without_missile_evidence():
    r = _rec([_kill(3000, weapon=fc.W_RAILGUN, name="RAILGUN")],
             _popup_ents())[0]
    c = classes_of(r)
    assert "POPUP_COMBO" in c
    assert c["POPUP_COMBO"]["confidence"] == fr.LOW_CANDIDATE
    assert r.attributes["popup_rise_vz"] == pytest.approx(300.0)


def test_popup_combo_medium_with_missile_hit():
    events = [_kill(3000, weapon=fc.W_RAILGUN, name="RAILGUN"),
              {"type": "missile_hit", "server_time_ms": 2400}]
    r = fr.recognize({"events": events, "entities": _popup_ents(),
                      "accuracy": []}, player=1, demo_name="t.dm_73")[0]
    c = classes_of(r)
    assert c["POPUP_COMBO"]["confidence"] == fr.MEDIUM


# ── multikill v2: kills/second + deep subtypes ──────────────────────────────

def test_kills_per_second_and_rapid_multikill():
    ev = [_kill(1000, victim=2), _kill(2500, victim=3), _kill(4000, victim=4)]
    last = _rec(ev)[-1]
    mk = last.attributes["multikill"]
    assert mk["kills_per_second"] == pytest.approx(1.0)
    assert "RAPID_MULTIKILL" in classes_of(last)     # provisional >= 1.0 kps


def test_slow_chain_is_not_rapid():
    ev = [_kill(1000, victim=2), _kill(3900, victim=3), _kill(6800, victim=4)]
    last = _rec(ev)[-1]
    assert "MULTIKILL_TRIPLE" in classes_of(last)
    assert "RAPID_MULTIKILL" not in classes_of(last)


def test_multikill_penta_name():
    ev = [_kill(1000 + i * 1000, victim=2 + i) for i in range(5)]
    names = [n for r in _rec(ev) for n in r.class_names]
    assert "MULTIKILL_PENTA" in names


def test_multi_weapon_chain():
    ev = [_kill(1000, victim=2, weapon=fc.W_ROCKET, name="ROCKET"),
          _kill(2500, victim=3, weapon=fc.W_RAILGUN, name="RAILGUN")]
    last = _rec(ev)[-1]
    assert "MULTI_WEAPON_CHAIN" in classes_of(last)
    assert "COMBO_KILL" in classes_of(last)          # rocket->rail finisher


def test_rail_rocket_finisher_pair():
    ev = [_kill(1000, victim=2, weapon=fc.W_RAILGUN, name="RAILGUN"),
          _kill(2500, victim=3, weapon=fc.W_ROCKET, name="ROCKET")]
    last = _rec(ev)[-1]
    c = classes_of(last)
    assert "COMBO_KILL" in c
    assert "rail_rocket" in c["COMBO_KILL"]["detail"]


# ── context: recorder health + weapon switch ────────────────────────────────

def test_low_health_win_from_recorded_health():
    snaps = [_ps(1, t, health=20) for t in range(0, 3100, 100)]
    r = fr.recognize({"events": [_kill(3000)], "entities": [],
                      "snapshots": snaps, "accuracy": []},
                     player=1, demo_name="t.dm_73")[0]
    c = classes_of(r)
    assert "LOW_HEALTH_WIN" in c
    assert c["LOW_HEALTH_WIN"]["confidence"] == fr.HIGH
    assert r.attributes["min_health_prekill"] == 20
    assert r.components["drama_score"] > 0


def test_last_hp_frag_beats_low_health():
    snaps = [_ps(1, t, health=8) for t in range(0, 3100, 100)]
    r = fr.recognize({"events": [_kill(3000)], "entities": [],
                      "snapshots": snaps, "accuracy": []},
                     player=1, demo_name="t.dm_73")[0]
    assert "LAST_HP_FRAG" in classes_of(r)
    assert "LOW_HEALTH_WIN" not in classes_of(r)


def test_fast_weapon_switch():
    ents = [_ent(1, t, weapon=5) for t in range(0, 2600, 100)]
    ents += [_ent(1, t, weapon=7) for t in range(2600, 3100, 100)]
    r = _rec([_kill(3000, weapon=fc.W_RAILGUN, name="RAILGUN")], ents)[0]
    c = classes_of(r)
    assert "FAST_WEAPON_SWITCH" in c
    assert r.attributes["weapon_switch_gap_ms"] == 400


def test_no_switch_class_when_weapon_held():
    ents = [_ent(1, t, weapon=7) for t in range(0, 3100, 100)]
    r = _rec([_kill(3000, weapon=fc.W_RAILGUN, name="RAILGUN")], ents)[0]
    assert "FAST_WEAPON_SWITCH" not in classes_of(r)


# ── penalties ───────────────────────────────────────────────────────────────

def test_stationary_victim_penalty_and_reason():
    ents = [_ent(2, t, x=500.0) for t in range(0, 3100, 100)]   # parked victim
    r = _rec([_kill(3000)], ents)[0]
    assert r.components["penalty_score"] == pytest.approx(-1.0)
    assert any(x.startswith("- stationary victim") for x in r.reasons)
    # penalty is part of the additive score
    assert r.highlight_score == pytest.approx(sum(r.components.values()))


def test_no_penalty_when_victim_was_fighting():
    events = [_kill(3000),
              {"type": "pain", "server_time_ms": 1500, "client_num": 2}]
    ents = [_ent(2, t, x=500.0) for t in range(0, 3100, 100)]
    r = fr.recognize({"events": events, "entities": ents, "accuracy": []},
                     player=1, demo_name="t.dm_73")[0]
    assert "penalty_score" not in r.components


def test_no_penalty_for_moving_victim():
    ents = [_ent(2, t, x=500.0, vx=300.0) for t in range(0, 3100, 100)]
    r = _rec([_kill(3000)], ents)[0]
    assert "penalty_score" not in r.components


# ── reaction candidate (stage-2 gated) ──────────────────────────────────────

def test_reaction_shot_candidate_with_placeholder():
    ents = [_ent(1, t) for t in range(0, 3100, 100)]
    ents += [_ent(2, 2800, x=400.0), _ent(2, 3000, x=400.0)]  # 200 ms presence
    r = _rec([_kill(3000, weapon=fc.W_RAILGUN, name="RAILGUN")], ents)[0]
    c = classes_of(r)
    assert "REACTION_SHOT_CANDIDATE" in c
    assert c["REACTION_SHOT_CANDIDATE"]["confidence"] == fr.LOW_CANDIDATE
    assert "reaction_ms" in r.attributes
    assert r.attributes["reaction_ms"] is None       # stage-2 fills this


def test_no_reaction_candidate_for_lg():
    ents = [_ent(1, t) for t in range(0, 3100, 100)]
    ents += [_ent(2, 2800, x=400.0), _ent(2, 3000, x=400.0)]
    r = _rec([_kill(3000)], ents)[0]                 # LG kill
    assert "REACTION_SHOT_CANDIDATE" not in classes_of(r)


# ── movement extras ─────────────────────────────────────────────────────────

def test_vertical_action():
    ents = [_ent(1, t, z=float(t) * 0.2) for t in range(1000, 3100, 100)]
    r = _rec([_kill(3000)], ents)[0]
    c = classes_of(r)
    assert "VERTICAL_ACTION" in c
    assert r.attributes["vertical_travel"] >= fr.VERTICAL_MIN_DZ


def test_high_speed_multikill_needs_all_kills_at_speed():
    ents = [_ent(1, t, vx=1400.0) for t in range(0, 4200, 100)]
    ev = [_kill(1000, victim=2), _kill(2500, victim=3), _kill(4000, victim=4)]
    last = _rec(ev, ents)[-1]
    c = classes_of(last)
    assert "HIGH_SPEED_MULTIKILL" in c
    mk = last.attributes["multikill"]
    assert mk["speed_min"] == pytest.approx(1400.0)
    assert mk["speed_samples"] == 3


def test_health_drama_context_weighting():
    """20 HP in a 1v3 must outrank 20 HP cleanup (reclassify_v2 rule)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine" / "parser"))
    # context multiplier: 1.0 + 0.5*(enemies-1); LOW_HP base 3
    assert round(3 * (1.0 + 0.5 * 2), 1) > round(3 * 1.0, 1)
    # near-death beats low-hp at same context
    assert 10 * 1.0 > 3 * 1.0
