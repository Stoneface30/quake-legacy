"""PANTHEON scene production layer — identity, anchoring, FX primitives.

The three properties these tests defend, in priority order:

1. A scene NEVER stores a raw time. Every camera stage and every fx cue is
   anchored to a named recipe anchor + an offset, so re-running recognition
   moves camera and effects together instead of leaving hand-copied
   constants to drift (§12/§16).
2. The compiled FX lines never use the broken ``runfxat``-from-init form
   whose origin snapshot is taken at parse time (§17,
   free_wins_proof.md proof 1).
3. save -> load -> re-hash is byte-identical, and the scene layer's identity
   is independent of both the recipe's and the camera artifact's (§30/§48).
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import cam10_writer, pantheon_scene as ps
from creative_suite.engine.scene_recipe import (DemoRef, EventAnchor,
                                                EvidenceRef, SceneRecipeV2,
                                                TimeSegment)

EVIDENCE = EvidenceRef(dataset="recognized_frags", record_id="24326",
                       version="recognition-v2")


def make_recipe(launch_us=290_525_000, impact_us=291_650_000):
    """A minimal but REAL-shaped recipe: launch and impact are separate
    anchors even though a naive reading would collapse them."""
    return SceneRecipeV2(
        demo=DemoRef(sha256="a" * 64, name="hero.dm_73",
                     window_start_us=289_000_000,
                     window_end_us=294_000_000),
        time_map=(TimeSegment("normal", 289_000_000, 294_000_000,
                              0, 5_000_000, 1, 1),),
        anchors=(
            EventAnchor("launch-0", "PROJECTILE_LAUNCH", 0, "recorder",
                        launch_us, EVIDENCE, "CONFIRMED"),
            EventAnchor("impact-0", "ROCKET_IMPACT", 0, "recorder",
                        impact_us, EVIDENCE, "CONFIRMED"),
            EventAnchor("frag-0", "FRAG", 0, "recorder",
                        impact_us, EVIDENCE, "CONFIRMED"),
            EventAnchor("ghost-0", "ROCKET_IMPACT", 1, "recorder",
                        None, EVIDENCE, "UNKNOWN", status="missing"),
        ),
    )


def make_intent():
    return ps.CameraIntent(
        mode="PROJECTILE_HERO",
        subject_anchor="impact-0",
        stages=(
            {"stage": ps.STAGE_PROJECTILE_FOLLOW, "start_anchor": "launch-0",
             "start_offset_us": 0, "end_anchor": "impact-0",
             "end_offset_us": -200_000, "params": {"trail_dist": 120.0}},
            {"stage": ps.STAGE_IMPACT_ORBIT, "start_anchor": "impact-0",
             "start_offset_us": -200_000, "end_anchor": "impact-0",
             "end_offset_us": 600_000, "params": {"radius": 220.0}},
        ),
    )


def make_scene(**kw):
    defaults = dict(
        recipe_id="r" * 64,
        camera_intent=make_intent(),
        fx_stack=(
            ps.FxCue("projectile_trail", "launch-0", 0, 1_125_000,
                     ps.INTENSITY_SUBTLE, {"fx_name": "pantheon/trail"}),
            ps.FxCue("impact_flash", "impact-0", 0, 400_000,
                     ps.INTENSITY_SUBTLE,
                     {"fx_name": "pantheon/impact",
                      "world_pos": [-68.0, 731.0, 576.0]}),
        ),
        visual_look=ps.LOOK_PANTHEON,
        runtime_baseline_hash="b" * 64,
        music_anchor_slots=("drop", "release"),
    )
    defaults.update(kw)
    return ps.PantheonScene(**defaults)


# --- anchor resolution ----------------------------------------------------

def test_resolve_anchor_applies_offset():
    recipe = make_recipe()
    assert ps.resolve_anchor(recipe, "impact-0") == 291_650_000
    assert ps.resolve_anchor(recipe, "impact-0", -200_000) == 291_450_000
    assert ps.resolve_anchor(recipe, "launch-0", 120_000) == 290_645_000


def test_resolve_anchor_ms_rounds_half_away_from_zero():
    """A cue authored AT an anchor must land ON the anchor's ms, not one
    before it — truncation would silently fire every effect early."""
    recipe = make_recipe(impact_us=291_650_500)
    assert ps.resolve_anchor_ms(recipe, "impact-0") == 291_651
    recipe = make_recipe(impact_us=291_650_499)
    assert ps.resolve_anchor_ms(recipe, "impact-0") == 291_650


def test_unknown_anchor_raises_and_lists_known_ids():
    recipe = make_recipe()
    with pytest.raises(ps.AnchorResolutionError) as err:
        ps.resolve_anchor(recipe, "impact-9")
    assert "launch-0" in str(err.value)


def test_unresolved_anchor_is_refused_not_silently_zero():
    recipe = make_recipe()
    with pytest.raises(ps.AnchorResolutionError):
        ps.resolve_anchor(recipe, "ghost-0")


def test_resolution_works_against_a_recipe_dict():
    """Scenes must resolve against a recipe loaded from the DB as JSON
    without reconstructing the dataclass."""
    recipe = make_recipe()
    assert (ps.resolve_anchor(recipe.to_dict(), "impact-0")
            == ps.resolve_anchor(recipe, "impact-0"))


def test_anchor_move_moves_camera_and_fx_together():
    """The whole point of §16: one evidence change, both consumers move."""
    scene = make_scene()
    early, late = make_recipe(), make_recipe(impact_us=291_675_000)
    cam_early = scene.camera_intent.resolve_window_us(early)
    cam_late = scene.camera_intent.resolve_window_us(late)
    fx_early = ps.compile_fx_cfg_lines(scene, early)
    fx_late = ps.compile_fx_cfg_lines(scene, late)
    assert cam_late[1] - cam_early[1] == 25_000
    assert fx_early != fx_late
    assert "at 291675 runfx" in fx_late[1]


# --- camera intent validation --------------------------------------------

def test_stage_must_be_a_known_stage():
    with pytest.raises(ValueError):
        ps.CameraIntent(mode="x", stages=(
            {"stage": "DOLLY_ZOOM", "start_anchor": "a", "end_anchor": "b"},))


def test_stage_without_anchor_is_refused():
    """Guards the core rule: no stage may be placed by raw time."""
    with pytest.raises(ValueError, match="anchored semantically"):
        ps.CameraIntent(mode="x", stages=(
            {"stage": ps.STAGE_FPV, "end_anchor": "b"},))


def test_stage_resolving_backwards_is_refused():
    intent = ps.CameraIntent(mode="x", stages=(
        {"stage": ps.STAGE_FPV, "start_anchor": "impact-0",
         "end_anchor": "launch-0"},))
    with pytest.raises(ps.AnchorResolutionError, match="non-positive"):
        intent.resolve_window_us(make_recipe())


def test_resolve_window_spans_all_stages():
    assert make_intent().resolve_window_us(make_recipe()) == (290_525_000,
                                                              292_250_000)


# --- FX compilation -------------------------------------------------------

def test_fx_never_emits_runfxat():
    """§17: the parse-time-snapshot primitive must be unreachable."""
    lines = ps.compile_fx_cfg_lines(make_scene(), make_recipe())
    assert lines and all("runfxat" not in ln for ln in lines)
    assert all(ln.startswith("at ") for ln in lines)


def test_fx_without_world_pos_uses_live_origin_form():
    lines = ps.compile_fx_cfg_lines(make_scene(), make_recipe())
    assert lines[0] == "at 290525 runfx pantheon/trail"


def test_fx_with_world_pos_bakes_explicit_coordinates():
    lines = ps.compile_fx_cfg_lines(make_scene(), make_recipe())
    assert lines[1] == "at 291650 runfx pantheon/impact -68.00 731.00 576.00"


def test_world_dir_requires_world_pos_because_args_are_positional():
    scene = make_scene(fx_stack=(
        ps.FxCue("impact_flash", "impact-0", parameters={
            "fx_name": "pantheon/impact", "world_dir": [0, 0, 1]}),))
    with pytest.raises(ps.FxCompileError, match="requires origin first"):
        ps.compile_fx_cfg_lines(scene, make_recipe())


def test_off_cues_emit_nothing_but_still_validate_anchors():
    off = make_scene().at_intensity(ps.INTENSITY_OFF)
    assert ps.compile_fx_cfg_lines(off, make_recipe()) == []
    broken = make_scene(fx_stack=(
        ps.FxCue("x", "nope-0", parameters={"fx_name": "a"}),)
    ).at_intensity(ps.INTENSITY_OFF)
    with pytest.raises(ps.AnchorResolutionError):
        ps.compile_fx_cfg_lines(broken, make_recipe())


def test_fx_name_injection_is_refused():
    """CS-5: fx names reach a cfg oneliner."""
    scene = make_scene(fx_stack=(
        ps.FxCue("x", "impact-0", parameters={"fx_name": "a; quit"}),))
    with pytest.raises(ps.FxCompileError):
        ps.compile_fx_cfg_lines(scene, make_recipe())


def test_missing_fx_name_is_refused():
    scene = make_scene(fx_stack=(ps.FxCue("x", "impact-0"),))
    with pytest.raises(ps.FxCompileError, match="fx_name"):
        ps.compile_fx_cfg_lines(scene, make_recipe())


def test_bad_intensity_level_is_refused():
    with pytest.raises(ValueError):
        ps.FxCue("x", "impact-0", intensity_level="MEDIUM")


# --- intensity variants ---------------------------------------------------

def test_at_intensity_changes_only_the_level():
    base = make_scene()
    hero = base.at_intensity(ps.INTENSITY_HERO)
    assert [c.intensity_level for c in hero.fx_stack] == ["HERO", "HERO"]
    # everything else about the two scenes is identical
    strip = lambda s: [{k: v for k, v in c.items()
                        if k != "intensity_level"} for c in s.to_dict()["fx_stack"]]
    assert strip(base) == strip(hero)
    assert base.to_dict()["camera_intent"] == hero.to_dict()["camera_intent"]
    assert base.scene_id != hero.scene_id


# --- identity + persistence ----------------------------------------------

def test_scene_id_is_deterministic():
    assert make_scene().scene_id == make_scene().scene_id


def test_scene_id_ignores_nothing_that_changes_the_picture():
    base = make_scene()
    assert make_scene(visual_look=ps.LOOK_ORIGINAL).scene_id != base.scene_id
    assert make_scene(hud_policy="OTHER").scene_id != base.scene_id
    assert make_scene(
        output_passes=ps.OutputPasses(beauty=True, depth=True)
    ).scene_id != base.scene_id


def test_roundtrip_is_byte_identical(tmp_path):
    """§30/§48: save -> reload -> re-hash must match exactly."""
    db = tmp_path / "cinematic.db"
    scene = make_scene(camera_compilation=ps.CameraCompilation(
        backend=cam10_writer.BACKEND_NATIVE_CAM10,
        compiler_version=cam10_writer.CAMERA_COMPILER_VERSION,
        artifact_hash="c" * 64, runtime_version="wolfcamql-11.3",
        camera_name="hero", effective_hz=60.0, sample_count=104,
        collision_status="VALID"))
    scene_id = ps.persist_scene(scene, db)
    loaded = ps.load_scene(scene_id, db)
    assert loaded == scene
    assert loaded.scene_id == scene_id
    assert loaded.canonical_json() == scene.canonical_json()


def test_persist_is_idempotent(tmp_path):
    db = tmp_path / "cinematic.db"
    ps.persist_scene(make_scene(), db)
    ps.persist_scene(make_scene(), db)
    assert len(ps.list_scenes(db)) == 1


def test_scene_identity_is_independent_of_camera_recompilation(tmp_path):
    """A recompile under a new compiler must not change scene identity's
    dependence on anything the DIRECTOR chose. It DOES change scene_id
    (the pointer moved) — but the recipe_id and the camera intent are
    untouched, which is the separation that matters."""
    comp_a = ps.CameraCompilation(
        cam10_writer.BACKEND_NATIVE_CAM10, "cam10-v1", "a" * 64,
        "wolfcamql-11.3", "hero", 60.0, 104, "VALID")
    comp_b = ps.CameraCompilation(
        cam10_writer.BACKEND_NATIVE_CAM10, "cam10-v2", "b" * 64,
        "wolfcamql-11.3", "hero", 60.0, 104, "VALID")
    a, b = make_scene(camera_compilation=comp_a), make_scene(
        camera_compilation=comp_b)
    assert a.recipe_id == b.recipe_id
    assert a.camera_intent == b.camera_intent
    assert a.scene_id != b.scene_id


def test_bad_visual_look_is_refused():
    with pytest.raises(ValueError):
        make_scene(visual_look="TEAL_ORANGE")


def test_scene_requires_at_least_one_output_pass():
    with pytest.raises(ValueError):
        ps.OutputPasses(beauty=False, depth=False)


# --- hook vs cue binding --------------------------------------------------

def test_hook_effects_emit_no_console_line():
    """A per-frame engine hook is armed by DEFINING its script name; there
    is no console command, and inventing one would be worse than nothing."""
    scene = make_scene(fx_stack=(
        ps.FxCue("projectile_trail", "launch-0", parameters={
            "fx_name": "weapon/rocket/trail", "binding": ps.BINDING_HOOK}),
        ps.FxCue("impact_flash", "impact-0", parameters={
            "fx_name": "pantheon/impact"}),))
    assert ps.compile_fx_cfg_lines(scene, make_recipe()) == [
        "at 291650 runfx pantheon/impact"]


def test_hook_binding_still_validates_its_anchor():
    scene = make_scene(fx_stack=(
        ps.FxCue("x", "nope-0", parameters={
            "fx_name": "weapon/rocket/trail", "binding": ps.BINDING_HOOK}),))
    with pytest.raises(ps.AnchorResolutionError):
        ps.compile_fx_cfg_lines(scene, make_recipe())


def test_hook_with_world_pos_is_refused():
    """The engine feeds a hook the hooked entity's own origin every frame;
    a caller-supplied position would be silently ignored."""
    with pytest.raises(ValueError, match="HOOK effect cannot take world_pos"):
        ps.FxCue("x", "launch-0", parameters={
            "fx_name": "weapon/rocket/trail", "binding": ps.BINDING_HOOK,
            "world_pos": [0, 0, 0]})


def test_unknown_binding_is_refused():
    with pytest.raises(ValueError):
        ps.FxCue("x", "launch-0", parameters={"binding": "MAGIC"})


def test_default_binding_is_cue():
    assert ps.FxCue("x", "launch-0").binding == ps.BINDING_CUE
