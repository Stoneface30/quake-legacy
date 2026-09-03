"""Edit fast, lock the movie, then render the big boy. Timing never moves."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import render_profile as rp

MS = 1000


# ── profiles ────────────────────────────────────────────────────────────────

def test_only_the_current_backend_exists_today():
    assert rp.CURRENT_BACKEND == "wolfcamql-11.3"
    for name in rp.available_profiles():
        assert rp.PROFILES[name].backend == rp.BACKEND_WOLFCAM
    assert rp.PREVIEW_FAST in rp.available_profiles()
    assert rp.MASTER_PATH_TRACE not in rp.available_profiles()


def test_a_profile_cannot_claim_a_backend_we_do_not_have():
    with pytest.raises(ValueError, match="do not have"):
        rp.RenderProfile(rp.MASTER_HERO, rp.BACKEND_PATH_TRACED, 1920, 1080,
                         exists_today=True)


def test_every_profile_keeps_sixty_distinct_frames():
    """A proxy is cheaper in pixels and lighting, never in time."""
    with pytest.raises(ValueError, match="never in time"):
        rp.RenderProfile(rp.PREVIEW_FAST, rp.BACKEND_WOLFCAM, 960, 540, fps=30)
    assert all(p.fps == 60 for p in rp.PROFILES.values())


def test_master_oversamples_then_downsamples():
    m = rp.PROFILES[rp.MASTER_RASTER]
    assert m.internal_size[0] > m.width and m.internal_scale > 1
    assert m.intermediate != "mjpeg", "a master does not go through jpeg"


# ── controls ────────────────────────────────────────────────────────────────

def test_a_control_available_now_names_its_binding():
    with pytest.raises(ValueError, match="hope, not a capability"):
        rp.RenderControl("x", rp.AVAILABLE_NOW, "")
    for c in rp.CONTROLS.values():
        if c.capability == rp.AVAILABLE_NOW:
            assert c.backend_binding, c.name


def test_future_controls_are_not_pretended_available():
    for name in ("bloom", "exposure", "shadow_maps", "path_tracing"):
        assert not rp.CONTROLS[name].usable_now, name
    for name in ("picmip", "motion_blur", "fullbright", "depth_pass"):
        assert rp.CONTROLS[name].usable_now, name


def test_the_capability_split_is_honest():
    split = rp.controls_by_capability()
    assert len(split[rp.AVAILABLE_NOW]) >= 15
    assert len(split[rp.FUTURE_BACKEND]) >= 8
    assert "color_grade" in split[rp.AVAILABLE_VIA_ASSETS]


# ── looks ───────────────────────────────────────────────────────────────────

def test_a_look_says_what_it_wants_that_it_cannot_have():
    assert rp.look_unmet(rp.QL_CLEAN) == []
    assert "bloom" in rp.look_unmet(rp.PANTHEON_HERO)
    assert "path_tracing" in rp.look_unmet(rp.PATH_TRACED_HERO)


def test_looks_only_set_controls_that_exist():
    for look, state in rp.LOOK_STATE.items():
        for c in state:
            assert c in rp.CONTROLS, (look, c)


# ── treatment through time ──────────────────────────────────────────────────

def _reveal():
    """clean -> picmip ramp -> world stripped -> hero -> restored."""
    return rp.RenderTreatment("scene@1", rp.QL_CLEAN, (
        rp.Keyframe(0, {"picmip": 0.0}),
        rp.Keyframe(240 * MS, {"picmip": 0.6, "fullbright": 1.0}, "SMOOTH"),
        rp.Keyframe(800 * MS, {"picmip": 0.6, "fullbright": 1.0}, "HOLD"),
        rp.Keyframe(1_350 * MS, {"picmip": 0.0, "fullbright": 0.0}),
    ))


def test_a_treatment_is_animatable_on_edit_us():
    t = _reveal()
    assert t.state_at(0)["picmip"] == 0.0
    mid = t.state_at(120 * MS)["picmip"]
    assert 0.0 < mid < 0.6, "half way into the ramp"
    assert t.state_at(500 * MS)["picmip"] == pytest.approx(0.6)
    assert t.state_at(1_350 * MS)["picmip"] == pytest.approx(0.0)


def test_hold_holds_and_smooth_eases():
    t = _reveal()
    assert t.state_at(1_000 * MS)["picmip"] == pytest.approx(0.6), "HOLD"
    lin = rp.RenderTreatment("s", rp.QL_CLEAN, (
        rp.Keyframe(0, {"picmip": 0.0}), rp.Keyframe(1_000 * MS, {"picmip": 1.0})))
    smooth = rp.RenderTreatment("s", rp.QL_CLEAN, (
        rp.Keyframe(0, {"picmip": 0.0}, "SMOOTH"),
        rp.Keyframe(1_000 * MS, {"picmip": 1.0})))
    assert lin.state_at(250 * MS)["picmip"] == pytest.approx(0.25)
    assert smooth.state_at(250 * MS)["picmip"] < 0.25, "eases in slower"


def test_keyframes_must_name_real_controls_in_order():
    with pytest.raises(ValueError, match="unknown render control"):
        rp.Keyframe(0, {"lens_flare": 1.0})
    with pytest.raises(ValueError, match="time order"):
        rp.RenderTreatment("s", rp.QL_CLEAN, (
            rp.Keyframe(500, {"picmip": 0.0}), rp.Keyframe(0, {"picmip": 1.0})))


def test_a_treatment_reports_what_the_current_backend_cannot_honour():
    t = rp.RenderTreatment("s", rp.PANTHEON_HERO, (
        rp.Keyframe(0, {"bloom": 0.0}), rp.Keyframe(500 * MS, {"bloom": 1.0})))
    assert "bloom" in t.unmet()
    assert "picmip" not in t.unmet()


# ── skill protection ────────────────────────────────────────────────────────

def test_the_master_may_not_blind_a_protected_skill():
    t = rp.RenderTreatment("s", rp.PANTHEON_HERO, (
        rp.Keyframe(0, {"motion_blur": 0.5, "depth_of_field": 0.5}),),
        protected=((1_000 * MS, 3_000 * MS),))
    v = rp.readability_violations(t)
    assert v, "blur and dof inside the tracking must be refused"
    assert {x.control for x in v} == {"motion_blur", "depth_of_field"}
    assert all(1_000 * MS <= x.at_us < 3_000 * MS for x in v)


def test_the_clamp_is_scoped_to_the_interval():
    """The reveal before and the payoff after keep their look."""
    t = rp.RenderTreatment("s", rp.QL_CLEAN, (
        rp.Keyframe(0, {"picmip": 0.6, "motion_blur": 0.5}),),
        protected=((1_000 * MS, 3_000 * MS),))
    c = rp.clamp_for_protection(t)
    assert rp.readability_violations(c) == []
    assert c.state_at(500 * MS)["picmip"] == pytest.approx(0.6), "before"
    assert c.state_at(2_000 * MS)["picmip"] == pytest.approx(0.0), "during"
    assert c.state_at(3_500 * MS)["picmip"] == pytest.approx(0.6), "after"


def test_an_unprotected_treatment_is_returned_unchanged():
    t = _reveal()
    assert rp.clamp_for_protection(t) is t


# ── determinism across fidelity ─────────────────────────────────────────────

def test_the_editorial_identity_is_the_same_at_every_fidelity():
    t = _reveal()
    keys = {rp.render_key(scene_hash="s", camera_hash="c",
                          choreography_hash="h", treatment=t,
                          profile=rp.PROFILES[p], asset_hash="a")
            for p in (rp.PREVIEW_FAST, rp.REVIEW, rp.MASTER_RASTER)}
    assert len(keys) == 3, "each profile is its own render"
    e = rp.editorial_key(scene_hash="s", camera_hash="c",
                         choreography_hash="h", treatment=t)
    assert e == rp.editorial_key(scene_hash="s", camera_hash="c",
                                 choreography_hash="h", treatment=t)


def test_a_timing_change_changes_the_editorial_key():
    a = _reveal()
    b = rp.RenderTreatment(a.scene_ref, a.look,
                           a.keyframes[:-1] + (rp.Keyframe(
                               1_400 * MS, {"picmip": 0.0, "fullbright": 0.0}),))
    ka = rp.editorial_key(scene_hash="s", camera_hash="c",
                          choreography_hash="h", treatment=a)
    kb = rp.editorial_key(scene_hash="s", camera_hash="c",
                          choreography_hash="h", treatment=b)
    assert ka != kb


# ── the backend seam ────────────────────────────────────────────────────────

def test_compile_emits_scheduled_cvars_the_engine_understands():
    lines, unmet = rp.compile_wolfcam(_reveal(), lambda us: us // 1000)
    assert lines and all(l.line().startswith("at ") for l in lines)
    picmip = [l for l in lines if l.cvar == "r_picmip"]
    assert picmip and picmip[0].value == "0"
    assert any(int(l.value) > 0 for l in picmip), "the ramp happens"
    assert unmet == []


def test_compile_reports_what_it_could_not_express():
    t = rp.RenderTreatment("s", rp.PANTHEON_HERO, (
        rp.Keyframe(0, {"bloom": 0.0, "picmip": 0.0}),
        rp.Keyframe(500 * MS, {"bloom": 1.0})))
    lines, unmet = rp.compile_wolfcam(t, lambda us: us // 1000)
    assert "bloom" in unmet
    assert not any("bloom" in l.cvar for l in lines)


def test_the_director_never_sees_a_cvar():
    """A treatment is written in controls; only compile_* knows the engine."""
    t = _reveal()
    assert "r_picmip" not in str(t.to_dict())
    rep = rp.separation_report()
    assert "compile_<backend>()" in rep["minimum_seam"]
    assert any("pantheon_scene.py" in e for e in rep["entanglements"])


def test_integer_cvars_are_never_sent_fractions():
    """A ramp on an integer cvar is a staircase; the engine truncates
    anything else silently."""
    lines, _ = rp.compile_wolfcam(_reveal(), lambda us: us // 1000)
    for l in lines:
        if l.cvar in ("r_picmip", "r_fullbright", "cg_shadows", "mme_blurFrames"):
            assert "." not in l.value, (l.cvar, l.value)
    assert rp.CONTROLS["gamma"].integer is False
