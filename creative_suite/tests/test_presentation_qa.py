"""Camera-mode -> profile resolver and the three bad-edit checks.

What matters: a cinematic camera can never render with HUD, the capture
path actually consults the resolver, and each QA check fires on exactly
the span it describes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import edit_qa as qa
from creative_suite.engine import master_profile as mp
from creative_suite.engine import presentation as pr


# ── resolver ────────────────────────────────────────────────────────────────

def test_fpv_keeps_the_gameplay_profile():
    assert pr.profile_for("FPV") == mp.PROFILE_NAME
    assert pr.presentation_for("FPV") == pr.FPV_GAMEPLAY


@pytest.mark.parametrize("mode", sorted(pr.CINEMATIC_MODES))
def test_every_cinematic_mode_resolves_to_a_zero_hud_profile(mode):
    profile = pr.profile_for(mode)
    assert pr.presentation_for(mode) == pr.CINEMATIC_CLEAN
    cvars = mp.PROFILES[profile]
    assert cvars["cg_draw2D"] == 0
    assert cvars["cg_drawFragMessageTime"] == 0
    assert cvars["cg_obituaryTime"] == 0
    assert cvars["con_notifytime"] == 0


def test_resolved_profiles_are_real_and_have_cfg_files():
    for p in pr.PROFILE_FOR.values():
        assert p in mp.PROFILES
        assert p in mp._CFG_FILES


def test_non_fpv_under_a_hud_profile_is_rejected():
    with pytest.raises(pr.InvalidPresentation, match="draws the HUD"):
        pr.validate("PROJECTILE", mp.PROFILE_NAME)


def test_fpv_under_a_clean_profile_is_allowed():
    """A clean FPV is a legitimate choice; only the reverse is forbidden."""
    assert pr.validate("FPV", "TR4SH_MASTER_POV_CLEAN") == "TR4SH_MASTER_POV_CLEAN"


def test_unknown_camera_mode_rejected():
    with pytest.raises(pr.InvalidPresentation):
        pr.presentation_for("HANDHELD")


def test_unknown_profile_rejected():
    with pytest.raises(pr.InvalidPresentation):
        pr.validate("FPV", "TR4SH_NOPE")


def test_hud_expectation_names_what_a_frame_may_contain():
    assert pr.hud_expectation("FPV")["hud_allowed"] is True
    assert pr.hud_expectation("PROJECTILE")["hud_allowed"] is False


# ── the resolver is actually consulted by the capture path ──────────────────

def test_capture_cfg_execs_the_camera_modes_profile():
    from creative_suite.engine import director_preview as dp
    src = (REPO_ROOT / "creative_suite" / "engine"
           / "director_preview.py").read_text(encoding="utf-8")
    # the old unconditional exec must be gone
    assert "_CFG_FILES[master_profile.PROFILE_NAME]" not in src
    assert "presentation.validate(plan.camera_mode" in src
    assert "director-preview-v4" == dp.PREVIEW_PIPELINE_VERSION


def test_profile_is_part_of_visual_identity():
    from creative_suite.engine import director_preview as dp
    base = dict(frag_id=1, demo_sha256="a" * 64, demo_name="d.dm_73",
                recipe_id="r", edit_duration_us=8_000_000)

    def key(mode):
        from creative_suite.api import director_draft as dd
        draft = {"camera": {**dd.DEFAULT_CAMERA, "mode": mode}, "fx": {},
                 "look": {"look": "ORIGINAL", "show_depth": False},
                 "music": None}
        return dp.compute_visual_capture_key(draft=draft, **base)

    assert key("FPV") != key("PROJECTILE")


# ── bad-edit checks ─────────────────────────────────────────────────────────

def test_hud_check_errors_on_cinematic_with_gameplay_profile():
    f = qa.check_hud("PROJECTILE", mp.PROFILE_NAME)
    assert f and f[0].check == qa.CINEMATIC_HUD_VISIBLE
    assert f[0].severity == qa.ERROR


def test_hud_check_passes_cinematic_with_clean_profile():
    assert qa.check_hud("PROJECTILE", "TR4SH_MASTER_POV_CLEAN") == []


def test_hud_check_never_fires_for_fpv():
    assert qa.check_hud("FPV", mp.PROFILE_NAME) == []


def test_hud_check_trusts_a_frame_over_the_config():
    """Config said clean, a frame showed HUD: the frame wins."""
    f = qa.check_hud("PROJECTILE", "TR4SH_MASTER_POV_CLEAN",
                     frame_hud_detected=True)
    assert f and "frame inspection" in f[0].reason


def test_no_subject_warns_on_the_exact_gap():
    f = qa.check_no_subject(0.0, 2000.0, [(0.0, 400.0), (900.0, 2000.0)])
    assert len(f) == 1
    assert f[0].check == qa.CINEMATIC_NO_SUBJECT
    assert (f[0].start_ms, f[0].end_ms) == (400.0, 900.0)
    assert f[0].span_ms == 500.0
    assert f[0].threshold_ms == qa.NO_SUBJECT_MAX_MS


def test_no_subject_tolerates_short_gaps():
    assert qa.check_no_subject(0.0, 2000.0, [(0.0, 900.0), (1100.0, 2000.0)]) == []


def test_no_subject_warns_when_camera_outlives_the_last_subject():
    f = qa.check_no_subject(0.0, 2000.0, [(0.0, 1500.0)])
    assert len(f) == 1 and f[0].end_ms == 2000.0


def test_post_death_warns_without_continuation():
    f = qa.check_post_death(4500.0, 5200.0)
    assert len(f) == 1 and f[0].check == qa.POST_DEATH_CAMERA_TOO_LONG
    assert f[0].span_ms == 700.0


def test_post_death_is_fine_inside_the_allowance():
    assert qa.check_post_death(4500.0, 4800.0) == []


def test_post_death_is_fine_when_a_transition_takes_over():
    assert qa.check_post_death(4500.0, 9000.0, continuation_at_ms=4700.0) == []


def test_summary_passes_only_without_errors():
    assert qa.summarize([qa.check_post_death(0.0, 1000.0)[0]])["passes"]
    assert not qa.summarize(qa.check_hud("ORBIT", mp.PROFILE_NAME))["passes"]
