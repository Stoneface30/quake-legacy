"""Editorial direction is a second axis and never rewrites accuracy."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import editorial_sync_bias as eb, sync_contract


# ── the two axes stay independent ───────────────────────────────────────────

def test_equal_accuracy_can_carry_opposite_direction_grades():
    early = eb.assess(-15.0, eb.HERO_KILL)
    late = eb.assess(+15.0, eb.HERO_KILL)
    assert early.absolute_tier == late.absolute_tier == sync_contract.TIER_TARGET
    assert early.direction_grade == eb.PREFERRED
    assert late.direction_grade == eb.WRONG_SIDE


def test_absolute_tier_is_the_sync_contracts_answer_untouched():
    for delta in (-60.0, -30.0, -20.0, -5.0, 0.0, 12.0, 90.0):
        a = eb.assess(delta, eb.HERO_KILL)
        assert a.absolute_tier == sync_contract.classify_delta(delta,
                                                               sync_contract.CLASS_HARD)


def test_a_wrong_side_hit_can_still_be_mathematically_excellent():
    a = eb.assess(11.5, eb.LG_FINAL_KILL)
    assert a.absolute_tier == sync_contract.TIER_TARGET
    assert a.direction_grade == eb.WRONG_SIDE
    assert not a.is_editorially_preferred


def test_a_preferred_hit_can_still_be_mathematically_poor():
    a = eb.assess(-15.0, eb.HERO_KILL, sync_class=sync_contract.CLASS_HARD)
    assert a.direction_grade == eb.PREFERRED
    far = eb.assess(-200.0, eb.HERO_KILL)
    assert far.absolute_tier == sync_contract.TIER_BAD
    assert far.direction_grade == eb.FAR_FROM_PREFERENCE


# ── the preference itself ───────────────────────────────────────────────────

def test_the_hero_preference_is_a_lead_of_about_one_frame():
    bias = eb.DEFAULT_PROFILE.bias_for(eb.HERO_KILL)
    assert bias.preferred_delta_ms == -15.0
    assert bias.acceptable_low_ms <= -15.0 <= bias.acceptable_high_ms


def test_the_preference_lives_in_a_named_profile_not_a_global_constant():
    assert eb.DEFAULT_PROFILE.name == "director-2026-09"
    assert eb.DEFAULT_PROFILE.author and eb.DEFAULT_PROFILE.stated_on
    other = eb.BiasProfile(
        name="test", author="t", stated_on="2026-01-01",
        classes=(eb.ClassBias(eb.HERO_KILL, +20.0, 0.0, 30.0, "trailing taste"),))
    assert eb.assess(+20.0, eb.HERO_KILL, profile=other).direction_grade == eb.PREFERRED
    assert eb.assess(+20.0, eb.HERO_KILL).direction_grade == eb.WRONG_SIDE


def test_different_event_classes_carry_different_preferences():
    assert eb.assess(+5.0, eb.DODGE_NEAR_MISS).direction_grade == eb.PREFERRED
    assert eb.assess(+5.0, eb.HERO_KILL).direction_grade == eb.WRONG_SIDE


def test_a_class_may_have_no_hard_sync_preference_at_all():
    a = eb.assess(+123.0, eb.LG_CONTACT)
    assert a.direction_grade == eb.NO_PREFERENCE
    assert a.preferred_delta_ms is None
    assert a.is_editorially_preferred
    assert eb.target_music_us(1_000_000, eb.LG_CONTACT) is None


def test_the_acceptable_band_sits_between_preferred_and_wrong_side():
    a = eb.assess(-2.0, eb.HERO_KILL)      # inside [-20, 0], not within 8 of -15
    assert a.direction_grade == eb.ACCEPTABLE
    assert a.offset_from_preference_ms == 13.0


def test_target_music_time_uses_the_preference_and_the_sign_is_a_lead():
    t = eb.target_music_us(10_000_000, eb.HERO_KILL)
    assert t == 10_000_000 - 15_000


def test_every_assessment_explains_itself_and_names_its_profile():
    for cls in eb.EVENT_CLASSES:
        a = eb.assess(-3.0, cls)
        assert a.explanation
        assert a.profile == eb.DEFAULT_PROFILE.name
        assert a.direction_grade in eb.DIRECTION_GRADES


# ── the profile cannot be quietly incoherent ────────────────────────────────

def test_a_preference_outside_its_own_band_is_rejected():
    with pytest.raises(ValueError):
        eb.ClassBias(eb.HERO_KILL, -50.0, -20.0, 0.0, "impossible")


def test_a_stated_preference_requires_a_band():
    with pytest.raises(ValueError):
        eb.ClassBias(eb.HERO_KILL, -15.0, None, None, "no band")


def test_an_unknown_event_class_is_an_error_not_a_default():
    with pytest.raises(KeyError):
        eb.assess(0.0, "NOT_A_CLASS")


def test_assessments_are_immutable():
    a = eb.assess(-15.0, eb.HERO_KILL)
    with pytest.raises((AttributeError, TypeError)):
        a.direction_grade = eb.PREFERRED      # type: ignore[misc]
