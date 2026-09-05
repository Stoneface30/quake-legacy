"""The dossier explains the action. Partial truth is fine; false certainty is not."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from creative_suite.engine import action_stats as ast    # noqa: E402
from creative_suite.engine import dossier                # noqa: E402


def test_lg_accuracy_is_not_derivable_and_says_so():
    """Pain events are throttled -- median 925 ms apart, never under 100 ms.
    A weapon firing every 50 ms cannot have hits counted by a signal that
    arrives three times a second. An early version divided 3 pain events by
    23 attack ticks and reported 13% for a good kill."""
    assert 6 not in ast.ATTRIBUTABLE, "lightning cannot be attributed"
    assert 6 in ast.CONTINUOUS
    for wp in (8, 2):                       # plasma, machinegun: same problem
        assert wp not in ast.ATTRIBUTABLE


def test_only_weapons_slower_than_the_pain_throttle_get_accuracy():
    assert ast.ATTRIBUTABLE == {3, 4, 5, 7}     # shotgun, grenade, rocket, rail


def test_the_kill_itself_is_a_confirmed_hit():
    """The obituary names this weapon and this victim, so at least one shot
    landed. Without it a one-shot rail kill reported zero hits."""
    import inspect
    src = inspect.getsource(ast.for_action)
    assert "max(1, min(hits, shots))" in src


def test_a_foreign_camera_yields_no_accuracy():
    """fire_weapon from playerstate is the RECORDER's trigger. On somebody
    else's camera those shots are the cameraman's."""
    s = ast.for_action("nope", 1000, 10, 3, is_actor_pov=False)
    assert s.confidence == ast.CONF_UNKNOWN
    assert s.shots is None and "did not hold the camera" in s.note


def test_unknown_is_never_zero():
    assert dossier.UNKNOWN is None


def test_health_is_withheld_on_a_foreign_camera():
    out = dossier._stack({"health_at_frag": 50}, is_actor_pov=False)
    assert out["available"] is False and "held the camera" in out["reason"]


def test_missing_health_is_absent_not_zero():
    out = dossier._stack({}, is_actor_pov=True)
    assert out["available"] is False
    assert "health" not in out or out.get("at_frag") is None


def test_low_hp_tags_are_context_not_quality():
    out = dossier._stack({"health_at_frag": 15, "armor_at_frag": 0,
                          "min_health_10s": 15}, is_actor_pov=True)
    assert "CRITICAL_HP_ACTION" in out["tags"]
    assert "LOW_STACK_ACTION" in out["tags"]
    # No score, no role, no ranking implication.
    assert "score" not in out and "role" not in out


def test_the_first_item_dossier_is_truthful():
    d = dossier.build("USER_FRAG:495")
    if d is None:
        pytest.skip("corpus not present")
    assert d["available"]
    assert d["event"]["weapon"] == "LIGHTNING"
    assert d["event"]["is_actor_pov"] is True
    # LG: shots measured, accuracy honestly absent.
    assert d["action"]["shots"] and d["action"]["unit"] == "attack ticks"
    assert d["action"]["accuracy_pct"] is None
    assert d["action"]["confidence"] == "NOT_DERIVABLE"
