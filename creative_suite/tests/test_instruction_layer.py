"""The analysis layer may not contaminate history.

Every test here is an acceptance requirement from the brief, not a code path.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from engine.pantheon.instruction import (AnalysisBreak, Graphic,  # noqa: E402
                                         InstructionScene)
from engine.pantheon.scenario import Layer, RoundScenario, Team, Weapon  # noqa: E402

A = (100.0, 100.0, 0.0)
B = (500.0, 100.0, 0.0)
CAM = (300.0, 400.0, 0.0)


def _scene(hold=5.0, walk=1.6):
    scn = RoundScenario.clan_arena(map_name="overkill", hostname="T")
    scn.observer(CAM, yaw=90.0, team=Team.BLUE)
    k = scn.actor("KEEL", Team.BLUE).appearance("keel", "bright")
    c = scn.actor("CRASH", Team.RED).appearance("crash", "trainer")
    k.spawn(A, yaw=0.0, t=0.0, weapon=Weapon.RAIL)
    c.spawn(B, yaw=180.0, t=0.0, weapon=Weapon.ROCKET)
    k.stand(until=6.8)
    c.stand(until=6.8)
    s = InstructionScene(scn, duration=7.0)
    s.add_break(AnalysisBreak(at_t=4.0, hold_s=hold, presenter="KEEL",
                              walk_to=(250.0, 300.0, 0.0), face=CAM,
                              graphic=Graphic.SHOOTER_TO_TARGET,
                              graphic_from="KEEL", graphic_to="CRASH",
                              walk_s=walk))
    return s


def test_history_resumes_byte_identical():
    s = _scene()
    built, _ = s.build()
    r = s.verify_restoration(built)
    assert r["all_restored"]
    for row in r["breaks"]:
        for st in row["actors"].values():
            assert st["origin_delta"] == [0.0, 0.0, 0.0]
            assert st["yaw_delta"] == 0.0


def test_the_freeze_costs_edit_time_and_no_historical_time():
    s = _scene(hold=5.0)
    s.build()
    assert s.edit_duration == pytest.approx(7.0 + 5.0)
    # history does not advance across the hold
    assert s.historical_at_edit(4.0) == pytest.approx(4.0)
    assert s.historical_at_edit(8.9) == pytest.approx(4.0)
    assert s.historical_at_edit(10.0) == pytest.approx(5.0)


def test_the_walk_out_is_a_separate_client_not_the_historical_actor():
    s = _scene()
    built, rep = s.build()
    assert built.actors["KEEL"].layer is Layer.HISTORICAL
    assert built.actors["KEEL~ANALYSIS"].layer is Layer.ANALYSIS
    # different client slots: the demo can never be read as one man moving
    assert built.actors["KEEL"].client != built.actors["KEEL~ANALYSIS"].client
    assert rep["breaks"][0]["analysis_actor_layer"] == "ANALYSIS"


def test_the_analysis_body_is_not_in_the_round():
    s = _scene()
    built, _ = s.build()
    # BLUE has exactly one fighter; the explaining body must not be counted
    assert built._alive[Team.BLUE] == 1


def test_the_analysis_body_is_gone_before_history_resumes():
    s = _scene(hold=5.0)
    built, _ = s.build()
    ghost = built.actors["KEEL~ANALYSIS"]
    assert ghost._at(9.0).alive is False       # freeze ends at edit 9.0


def test_the_distance_is_derived_not_typed():
    s = _scene()
    _, rep = s.build()
    fact = rep["breaks"][0]["graphic"]["fact"]
    assert fact["value"] == pytest.approx(400.0)      # |A - B|
    assert "FrameTruth" in fact["derivation"]
    assert fact["layer"] == "ANALYSIS"


def test_the_tactical_line_is_labelled_a_reconstruction():
    s = _scene()
    _, rep = s.build()
    g = rep["breaks"][0]["graphic"]
    assert g["reconstruction"] is True
    assert g["nobody_fired_this"] is True
    assert g["layer"] == "ANALYSIS"


def test_a_hold_too_short_to_explain_in_is_refused():
    with pytest.raises(ValueError, match="no time to explain"):
        AnalysisBreak(at_t=1.0, hold_s=2.0, presenter="KEEL",
                      walk_to=A, face=CAM, walk_s=1.6)


def test_two_breaks_at_the_same_instant_are_refused():
    s = _scene()
    with pytest.raises(ValueError, match="same instant"):
        s.add_break(AnalysisBreak(at_t=4.2, hold_s=5.0, presenter="KEEL",
                                  walk_to=A, face=CAM))


def test_the_source_scenario_is_never_mutated():
    s = _scene()
    before = len(s.historical.actors)
    s.build()
    assert len(s.historical.actors) == before       # no ~ANALYSIS added
    assert "KEEL~ANALYSIS" not in s.historical.actors


# ── the analysis look (PROOF B) ───────────────────────────────────────

def test_the_analysis_body_wears_the_only_tintable_skin():
    # PROOF B: the colour family reaches `bright` and not `sarge/default`.
    # Giving the analysis body the bright skin is therefore what makes the
    # tint land on it alone.
    from engine.pantheon.instruction import ANALYSIS_SKIN
    s = _scene()
    built, rep = s.build()
    ghost = built.actors["KEEL~ANALYSIS"]
    assert ghost.skin == ANALYSIS_SKIN
    assert ghost.model == built.actors["KEEL"].model      # same character
    assert rep["breaks"][0]["analysis_appearance"]["skin"] == ANALYSIS_SKIN


def test_the_historical_actor_keeps_the_skin_the_demo_authored():
    s = _scene()
    built, _ = s.build()
    assert built.actors["CRASH"].skin == "trainer"        # untouched
    assert built.actors["KEEL"].skin == "bright"          # as authored


def test_the_analysis_tint_is_written_in_the_measured_format():
    from engine.pantheon.instruction import analysis_visual_cvars
    team = analysis_visual_cvars(same_team_as_pov=True)
    enemy = analysis_visual_cvars(same_team_as_pov=False)
    # 0xRRGGBB, the form PROOF 0 and PROOF B both measured
    assert all(v.startswith('"0x') for v in team.values())
    # the engine classifies by team relation, so only one half is written
    assert set(team) & set(enemy) == set()
    assert len(team) == 3
