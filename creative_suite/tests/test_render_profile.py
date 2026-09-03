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


def test_timing_authoritative_profiles_keep_sixty_distinct_frames():
    """A proxy is cheaper in pixels and lighting, never in time. A contact
    sheet is not a proxy and may say so."""
    with pytest.raises(ValueError, match="never in time"):
        rp.RenderProfile(rp.PREVIEW_FAST, rp.BACKEND_WOLFCAM, 960, 540, fps=30)
    sheet = rp.RenderProfile(rp.PREVIEW_FAST, rp.BACKEND_WOLFCAM, 960, 540,
                             fps=15, timing_authoritative=False)
    assert sheet.fps == 15
    assert all(p.fps == 60 for p in rp.PROFILES.values()
               if p.timing_authoritative)


def test_six_k_is_a_candidate_until_a_canary_runs():
    m = rp.PROFILES[rp.MASTER_RASTER]
    assert not m.verified and "CANDIDATE" in m.notes
    assert rp.MASTER_RASTER in rp.available_profiles()
    assert rp.MASTER_RASTER not in rp.proven_profiles()
    assert rp.PREVIEW_FAST in rp.proven_profiles()


def test_master_oversamples_then_downsamples():
    m = rp.PROFILES[rp.MASTER_RASTER]
    assert m.internal_size[0] > m.width and m.internal_scale > 1
    assert m.intermediate != "mjpeg", "a master does not go through jpeg"


# ── controls ────────────────────────────────────────────────────────────────

def test_a_control_available_now_names_its_binding():
    with pytest.raises(ValueError, match="hope, not a capability"):
        rp.RenderControl("x", rp.AVAILABLE_NOW, "", liveness=rp.LIVE_DISCRETE)
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

def test_schedulable_is_not_animatable():
    """`at` will execute any cvar. r_picmip is CVAR_LATCH in the vendored
    source and takes effect on vid_restart, so a scheduled staircase would
    run every line and change nothing."""
    assert rp.CONTROLS["picmip"].usable_now
    assert not rp.CONTROLS["picmip"].animatable
    assert rp.CONTROLS["picmip"].liveness == rp.LATCHED
    assert rp.CONTROLS["picmip"].liveness_provenance == rp.FROM_SOURCE
    assert rp.CONTROLS["gamma"].animatable
    assert rp.CONTROLS["gamma"].liveness == rp.LIVE_CONTINUOUS


def test_a_bound_control_must_say_what_happens_when_the_value_lands():
    with pytest.raises(ValueError, match="schedulable is not animatable"):
        rp.RenderControl("x", rp.AVAILABLE_NOW, "r_x")


def test_latched_controls_reach_launch_or_are_reported_not_applied():
    """r_picmip rides +set at launch (case A) and is shot configuration.
    r_fullbright is never set by the pipeline; a cfg line for it would
    execute after the renderer initialised and change nothing (case C)."""
    job = rp.compile_wolfcam(_reveal(), lambda us: us // 1000)
    sched = {c.cvar for c in job.scheduled}
    assert "r_picmip" in job.launch_sets
    assert "r_fullbright" not in job.launch_sets
    assert "fullbright" in job.latched_not_applied
    assert "r_picmip" not in sched and "r_fullbright" not in sched
    assert "picmip" in job.not_animatable and "fullbright" in job.not_animatable
    assert job.unmet == ()


def test_set_stage_is_read_from_the_pipeline_not_asserted():
    assert rp.CONTROLS["picmip"].set_stage == rp.LAUNCH_SET
    assert rp.CONTROLS["picmip"].application == "SHOT_SETUP_ONLY"
    assert rp.CONTROLS["fullbright"].set_stage == rp.NOT_SET
    assert rp.CONTROLS["fullbright"].application == rp.LATCHED_NOT_APPLIED
    assert rp.CONTROLS["gamma"].application == "LIVE"


def test_source_flags_are_not_capture_truth():
    """Every bound control starts at SOURCE_DECLARED. Only a captured frame
    moves it. Exactly one has been moved, by the runtime-truth canary."""
    promoted = [c.name for c in rp.CONTROLS.values()
                if c.capability == rp.AVAILABLE_NOW
                and c.truth != rp.SOURCE_DECLARED]
    assert promoted == ["gamma"]
    g = rp.CONTROLS["gamma"]
    assert g.truth == rp.CAPTURE_VISIBLE and g.liveness_provenance == rp.MEASURED
    assert g.truth != rp.TIMING_MEASURED, "capture-visible is not timed"
    rows = rp.application_report()
    assert any(r["application"] == rp.LATCHED_NOT_APPLIED for r in rows)
    assert any(r["application"] == "SHOT_SETUP_ONLY" for r in rows)


def test_a_live_ramp_does_schedule():
    t = rp.RenderTreatment("s", rp.QL_CLEAN, (
        rp.Keyframe(0, {"gamma": 0.2}), rp.Keyframe(1_000 * MS, {"gamma": 0.8})))
    job = rp.compile_wolfcam(t, lambda us: us // 1000)
    gam = [c for c in job.scheduled if c.cvar == "r_gamma"]
    assert len(gam) > 2, "a continuous control ramps across the interval"
    assert gam[0].value != gam[-1].value
    assert job.not_animatable == ()


def test_the_quantisation_is_on_record():
    """Requested, compiled, delivered: three values, kept apart."""
    t = rp.RenderTreatment("s", rp.QL_CLEAN, (
        rp.Keyframe(0, {"motion_blur": 0.0}),
        rp.Keyframe(1_000 * MS, {"motion_blur": 0.1})))
    job = rp.compile_wolfcam(t, lambda us: us // 1000)
    blur = [c for c in job.scheduled if c.cvar == "mme_blurFrames"]
    assert blur
    mid = blur[len(blur) // 2]
    assert mid.control == "motion_blur"
    assert mid.requested_unit is not None and mid.compiled_value is not None
    assert "." not in mid.value, "an integer cvar gets an integer"
    assert mid.quantisation_error is not None and abs(mid.quantisation_error) <= 0.5
    assert mid.delivered is None, "nothing has been measured yet"


def test_compile_reports_what_it_could_not_express():
    t = rp.RenderTreatment("s", rp.PANTHEON_HERO, (
        rp.Keyframe(0, {"bloom": 0.0, "picmip": 0.0}),
        rp.Keyframe(500 * MS, {"bloom": 1.0})))
    job = rp.compile_wolfcam(t, lambda us: us // 1000)
    assert "bloom" in job.unmet
    assert not any("bloom" in c.cvar for c in job.scheduled)


def test_the_director_never_sees_a_cvar():
    """A treatment is written in controls; only compile_* knows the engine."""
    t = _reveal()
    assert "r_picmip" not in str(t.to_dict())
    rep = rp.separation_report()
    assert "compile_<backend>()" in rep["minimum_seam"]
    assert rep["modern_raster_estimate"] == rp.REQUIRES_INTEGRATION_SPIKE


# ── creative concept vs implementation ──────────────────────────────────────

def test_a_creative_idea_is_not_its_cheapest_implementation():
    """A picmip staircase is a stylised stand-in for WORLD_REVEAL, not the
    idea itself, and it does not count as having it."""
    routes = rp.routes_for("WORLD_REVEAL")
    assert any(r.means.startswith("r_picmip") and r.coverage == "STYLISED"
               for r in routes)
    best = rp.best_route_now("WORLD_REVEAL")
    assert best is not None and best.coverage == "PARTIAL"
    assert best.layer == rp.CAPTURE_PASS, "depth compositing, not picmip"
    assert rp.best_route_now("GEOMETRY_REBUILD") is None
    assert rp.best_route_now("MAP_CONSTRUCTION") is None


def test_compositor_native_effects_are_full_today():
    for name in ("RHYTHMIC_IMAGE_STUTTER", "POV_PIP", "INFORMATION_REVEAL",
                 "MOSAIC_TILE_STEP"):
        best = rp.best_route_now(name)
        assert best is not None and best.layer == rp.COMPOSITOR, name
        assert best.coverage == "FULL", name


def test_passes_do_not_invent_what_the_engine_cannot_write():
    assert rp.PASSES["depth"]["capability"] == rp.AVAILABLE_NOW
    assert rp.PASSES["object_id"]["capability"] == rp.FUTURE_BACKEND
    assert rp.PASSES["stencil"].get("verified") is False


def test_a_backend_is_judged_by_the_ideas_it_unlocks():
    ev = rp.BACKEND_EVALUATIONS[rp.BACKEND_MODERN_RASTER]
    assert ev.creative_ideas_unlocked and ev.existing_protocols_improved
    assert ev.implementation_cost == rp.REQUIRES_INTEGRATION_SPIKE
    pt = rp.BACKEND_EVALUATIONS[rp.BACKEND_PATH_TRACED]
    assert pt.creative_ideas_unlocked == (), "spectacle, not vocabulary"
    assert "parked" in pt.notes


def test_integer_cvars_are_never_sent_fractions():
    """A ramp on an integer cvar is a staircase; the engine truncates
    anything else silently."""
    t = rp.RenderTreatment("s", rp.QL_CLEAN, (
        rp.Keyframe(0, {"motion_blur": 0.0, "player_shadows": 0.0}),
        rp.Keyframe(1_000 * MS, {"motion_blur": 0.3, "player_shadows": 1.0})))
    job = rp.compile_wolfcam(t, lambda us: us // 1000)
    for c in job.scheduled:
        if c.cvar in ("mme_blurFrames", "cg_shadows"):
            assert "." not in c.value, (c.cvar, c.value)
    assert rp.CONTROLS["gamma"].integer is False


# ── commands the model did not know the engine had ──────────────────────────

def test_material_transform_is_a_runtime_primitive_not_an_asset_reload():
    """remapshader replaces a shader while the demo runs. Filing it as a pk3
    swap put the primitive behind a rebuild it does not need."""
    c = rp.CONTROLS["material_swap"]
    assert c.capability == rp.AVAILABLE_NOW and c.animatable
    assert c.backend_binding == "remapshader"
    assert c.liveness_provenance == rp.FROM_SOURCE
    best = rp.best_route_now("MATERIAL_PULSE")
    assert best.layer == rp.ENGINE and best.coverage == "FULL"


def test_a_live_continuous_control_is_ramped_not_stepped():
    """cvarinterp hands the engine a start, an end and a duration. A
    staircase of scheduled sets is what you emit when you don't have it."""
    assert rp.can_ramp("gamma") and rp.can_ramp("timescale")
    assert not rp.can_ramp("picmip"), "latched: written and ignored"
    assert not rp.can_ramp("player_shadows"), "discrete: has no in-between"
    c = rp.ScheduledCvar(1000, "r_gamma", "1.0", "gamma",
                         ramp_to="1.8", ramp_ms=400)
    assert c.line() == "at 1000 cvarinterp r_gamma 1.0 1.8 0.400"
    assert rp.ScheduledCvar(1000, "r_gamma", "1.0").line() == "at 1000 r_gamma 1.0"


def test_the_speed_ramp_can_happen_before_capture():
    """timescale ramped in the engine means particles and blur follow the
    ramp, instead of a finished frame being resampled afterwards."""
    best = rp.best_route_now("SPEED_RAMP")
    assert best.layer == rp.ENGINE and best.coverage == "FULL"
    assert "cvarinterp timescale" in best.means
    post = [r for r in rp.routes_for("SPEED_RAMP") if r.layer == rp.COMPOSITOR]
    assert post and post[0].coverage == "PARTIAL"


def test_entity_strip_is_not_world_reveal():
    """entityfilter hides entities. It does not touch BSP geometry, and the
    two must not be conflated."""
    strip = rp.best_route_now("ENTITY_STRIP")
    assert strip.layer == rp.ENGINE and strip.coverage == "FULL"
    assert "never BSP" in strip.notes
    assert rp.best_route_now("GEOMETRY_REBUILD") is None


def test_a_single_entity_can_be_frozen_while_the_world_runs():
    c = rp.CONTROLS["entity_freeze"]
    assert c.backend_binding == "entityfreeze" and c.animatable
    assert rp.best_route_now("SELECTIVE_FREEZE").layer == rp.ENGINE


# ── the corpus route matrix ─────────────────────────────────────────────────

def test_every_corpus_idea_has_a_route_recorded():
    from creative_suite.engine import creative_routes as cr
    assert cr.unmapped() == [], "an unexamined idea is not a blocked one"
    m = rp.capability_matrix()
    assert m["mapped"] == 60 and m["unmapped"] == 0


def test_routes_are_kept_apart_not_collapsed():
    """A chase and a spline are different primitives with different failure
    modes; one entry each."""
    r = rp.routes_for("PROJECTILE_CINEMATIC")
    means = [x.means for x in r]
    assert any("chase" in m for m in means)
    assert any("viewEnt" in m for m in means)
    assert any("authored angles" in m for m in means)
    assert len(r) >= 3


def test_a_stylised_stand_in_never_counts_as_the_idea():
    strip = rp.routes_for("WORLD_STRIP")
    assert any(x.coverage == "STYLISED" and "picmip" in x.means for x in strip)
    assert rp.idea_status("WORLD_STRIP") == rp.PARTIAL_ROUTE
    assert rp.idea_status("WORLD_REBUILD") == rp.NEEDS_NEW_TECH


def test_material_routes_are_not_called_morphs():
    team = rp.routes_for("TEAM_IDENTITY_MORPH")
    shader = next(x for x in team if "remapshader" in x.means)
    assert shader.coverage == "PARTIAL"
    assert "Not a model morph" in shader.notes


def test_the_cam10_format_carries_more_than_we_write():
    unused = rp.cam_point_unused()
    for f in ("viewEnt", "commandStr", "timescale / timescaleInterp"):
        assert f in unused, f
    assert rp.CAM_POINT_FIELDS["type"]["used"] is True
    assert len(unused) >= 8
