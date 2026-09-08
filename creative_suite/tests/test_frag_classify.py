"""Tests for .dm_73 frag classification."""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "engine" / "parser"))
fc = pytest.importorskip("frag_classify")


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


def test_airborne_uses_groundentitynum_not_velocity():
    """The engine's own flag, so the tag is SOLID."""
    ents = [_ent(2, t, z=0.0, ground=0) for t in range(0, 3000, 100)]
    ents += [_ent(2, 3000, z=120.0, ground=1023)]
    frags = fc.classify({"events": [_kill(3000)], "entities": ents})
    tags = {t.name: t for t in frags[0].tags}
    assert "airshot" in tags
    assert tags["airshot"].confidence == fc.SOLID
    assert "air_shaft" in tags


def test_strafe_jump_is_not_an_airshot():
    """Airborne but barely off the floor must NOT count."""
    ents = [_ent(2, t, z=0.0, ground=0) for t in range(0, 3000, 100)]
    ents += [_ent(2, 3000, z=20.0, ground=1023)]     # only 20u up
    frags = fc.classify({"events": [_kill(3000)], "entities": ents})
    assert "airshot" not in frags[0].tag_names


def test_grounded_victim_never_airshot():
    ents = [_ent(2, t, z=0.0, ground=0) for t in range(0, 3100, 100)]
    frags = fc.classify({"events": [_kill(3000)], "entities": ents})
    assert "airshot" not in frags[0].tag_names


def test_air_weapon_variants():
    for weapon, name, tag in ((fc.W_ROCKET, "ROCKET", "air_rocket"),
                              (fc.W_GRENADE, "GRENADE", "air_nade"),
                              (fc.W_LIGHTNING, "LIGHTNING", "air_shaft")):
        ents = [_ent(2, t, z=0.0, ground=0) for t in range(0, 3000, 100)]
        ents += [_ent(2, 3000, z=150.0, ground=1023)]
        f = fc.classify({"events": [_kill(3000, weapon=weapon, name=name)],
                         "entities": ents})[0]
        assert tag in f.tag_names, f"{name} -> {tag}"


def test_weapon_switch_combo():
    ev = [_kill(1000, weapon=fc.W_ROCKET, name="ROCKET"),
          _kill(1800, weapon=fc.W_RAILGUN, name="RAILGUN")]
    frags = fc.classify({"events": ev, "entities": []})
    assert "rocket_rail" in frags[1].tag_names


def test_combo_window_is_respected():
    ev = [_kill(1000, weapon=fc.W_ROCKET, name="ROCKET"),
          _kill(9000, weapon=fc.W_RAILGUN, name="RAILGUN")]
    frags = fc.classify({"events": ev, "entities": []})
    assert "rocket_rail" not in frags[1].tag_names


def test_multikill_and_quadkill():
    ev = [_kill(1000, victim=2), _kill(1500, victim=3), _kill(2000, victim=4)]
    frags = fc.classify({"events": ev, "entities": []})
    assert "multikill" in frags[-1].tag_names
    ev.append(_kill(2500, victim=5))
    frags = fc.classify({"events": ev, "entities": []})
    assert "quadkill" in frags[-1].tag_names


def test_suicide_is_not_a_frag():
    frags = fc.classify({"events": [_kill(1000, killer=3, victim=3)],
                         "entities": []})
    assert frags == []


def test_high_acc_shaft_uses_server_scoreboard():
    acc = [{"server_time_ms": 500, "client_num": 1, "accuracy": 55, "score": 3}]
    f = fc.classify({"events": [_kill(1000)], "entities": [], "accuracy": acc})[0]
    tags = {t.name: t for t in f.tags}
    assert "high_acc_shaft" in tags
    assert tags["high_acc_shaft"].confidence == fc.SOLID
    assert f.lg_accuracy == 55


def test_low_accuracy_not_tagged():
    acc = [{"server_time_ms": 500, "client_num": 1, "accuracy": 22, "score": 3}]
    f = fc.classify({"events": [_kill(1000)], "entities": [], "accuracy": acc})[0]
    assert "high_acc_shaft" not in f.tag_names


def test_big_flick_from_view_angles():
    ents = [_ent(1, 900, yaw=0.0), _ent(1, 950, yaw=45.0), _ent(1, 1000, yaw=95.0)]
    f = fc.classify({"events": [_kill(1000)], "entities": ents})[0]
    assert "big_flick" in f.tag_names


def test_player_filter_restricts_to_one_killer():
    ev = [_kill(1000, killer=1), _kill(2000, killer=7)]
    assert len(fc.classify({"events": ev, "entities": []}, player=1)) == 1


def test_score_ranks_rarer_frags_higher():
    ents = [_ent(2, t, z=0.0, ground=0) for t in range(0, 3000, 100)]
    ents += [_ent(2, 3000, z=150.0, ground=1023)]
    air = fc.classify({"events": [_kill(3000, weapon=fc.W_ROCKET,
                                        name="ROCKET")], "entities": ents})[0]
    plain = fc.classify({"events": [_kill(3000)], "entities": []})[0]
    assert air.score > plain.score


# ── preshot: geometric, not a proxy ─────────────────────────────────────────

def _row(client, t, x=0.0, y=0.0, z=0.0, yaw=0.0, pitch=0.0):
    return {"client_num": client, "server_time_ms": t, "origin_x": x,
            "origin_y": y, "origin_z": z, "vel_x": 0.0, "vel_y": 0.0,
            "vel_z": 0.0, "angle_yaw": yaw, "angle_pitch": pitch,
            "ground_entity": 0, "airborne": False}


def _preshot_case(before_victim_xy, now_victim_xy, killer_yaw_before,
                  killer_yaw_now):
    """Killer at origin aiming down +X; victim moves into the crosshair."""
    t = 2000
    ents = []
    for tt in range(0, t + 100, 50):
        ents.append(_row(1, tt, 0, 0, 0, yaw=killer_yaw_before))
    ents.append(_row(1, t - fc.PRESHOT_LOOKBACK_MS, 0, 0, 0,
                     yaw=killer_yaw_before))
    ents.append(_row(1, t, 0, 0, 0, yaw=killer_yaw_now))
    ents.append(_row(2, t - fc.PRESHOT_LOOKBACK_MS, *before_victim_xy, 0))
    ents.append(_row(2, t, *now_victim_xy, 0))
    ev = [_kill(t, weapon=fc.W_RAILGUN, name="RAILGUN")]
    return fc.classify({"events": ev, "entities": ents})[0]


def test_preshot_victim_runs_into_a_static_crosshair():
    """Aim parked down +X; victim was off to the side, then arrives on axis."""
    f = _preshot_case(before_victim_xy=(500, 700), now_victim_xy=(1000, 0),
                      killer_yaw_before=0.0, killer_yaw_now=0.0)
    tags = {t.name: t for t in f.tags}
    assert "preshot" in tags
    assert tags["preshot"].confidence == fc.SOLID


def test_tracking_a_target_is_not_a_preshot():
    """Aim swept onto the victim -- the killer followed them. Not a preshot."""
    f = _preshot_case(before_victim_xy=(500, 700), now_victim_xy=(1000, 0),
                      killer_yaw_before=54.0, killer_yaw_now=0.0)
    assert "preshot" not in f.tag_names


def test_victim_already_on_axis_is_not_a_preshot():
    """Target was in front the whole time -- ordinary aim, nothing predicted."""
    f = _preshot_case(before_victim_xy=(900, 0), now_victim_xy=(1000, 0),
                      killer_yaw_before=0.0, killer_yaw_now=0.0)
    assert "preshot" not in f.tag_names


def test_aim_vector_points_down_x_at_zero_yaw():
    v = fc._aim_vector(0.0, 0.0)
    assert v[0] == pytest.approx(1.0)
    assert v[1] == pytest.approx(0.0, abs=1e-9)


def test_positive_pitch_looks_down():
    """Quake convention: positive pitch is downward."""
    assert fc._aim_vector(0.0, 45.0)[2] < 0


def test_angle_to_target_is_zero_when_aimed_at_them():
    k = _row(1, 0, 0, 0, 0, yaw=0.0)
    v = _row(2, 0, 1000, 0, 0)
    assert fc._angle_to_target(k, v) == pytest.approx(0.0, abs=0.5)


def test_angle_to_target_ninety_degrees():
    k = _row(1, 0, 0, 0, 0, yaw=0.0)
    v = _row(2, 0, 0, 1000, 0)
    assert fc._angle_to_target(k, v) == pytest.approx(90.0, abs=0.5)
