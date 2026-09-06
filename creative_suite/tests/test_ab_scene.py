"""The scene-per-command contract.

These tests guard claims, not code paths. Every one of them corresponds to a
way a configuration scene could film successfully and still lie.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from engine.pantheon.ab_scene import (ConfigScene, CvarInventory,  # noqa: E402
                                      Variant)
from engine.pantheon.shot import VisualProfile  # noqa: E402

SRC = Path(".tmp/synthetic/does_not_need_to_exist.dm_73")


@pytest.fixture(scope="module")
def inv() -> CvarInventory:
    return CvarInventory.load(REPO / "docs/reference/engine_cvarlist_11_3.json")


def _scene(variants, **kw) -> ConfigScene:
    return ConfigScene(scene_id="T", source=SRC, start_s=1.0, end_s=5.0,
                       variants=variants, **kw)


def test_inventory_is_the_filmed_binary_not_the_source_tree(inv):
    # cg_useCustomRedBlueRail is fully implemented in the 12.7test49 source and
    # absent from the 11.3 binary. Naming it on screen would be a false claim.
    assert inv.get("cg_useCustomRedBlueRail") is None
    assert inv.get("cg_redTeamRailColor1") is None
    # The route that DOES exist:
    assert inv.check("cg_teamRailColor1")
    assert inv.check("cg_enemyRailColor1")


def test_user_created_cvar_is_refused(inv):
    # Accepted by the console, registered by nothing -- a silent no-op.
    with pytest.raises(ValueError, match="USER_CREATED"):
        inv.check("cg_useCustomRedBlueModels")


def test_unregistered_cvar_is_refused(inv):
    with pytest.raises(KeyError, match="not registered"):
        inv.check("cg_forceEnemyModel")   # the plausible name that isn't real


def test_picmip_is_latched_so_variants_need_separate_captures(inv):
    scene = _scene([Variant("r_picmip 0", {"r_picmip": 0}),
                    Variant("r_picmip 8", {"r_picmip": 8})])
    rep = scene.validate(inv)
    assert rep["latched"] == ["r_picmip"]
    assert rep["requires_separate_capture"] is True


def test_live_cvar_does_not_demand_separate_captures(inv):
    scene = _scene([Variant("own colours", {"cg_railUseOwnColors": 0}),
                    Variant("team colours", {"cg_railUseOwnColors": 2})])
    rep = scene.validate(inv)
    assert rep["varying"] == ["cg_railUseOwnColors"]
    assert rep["requires_separate_capture"] is False


def test_unpinning_lets_the_base_profile_step_aside(inv):
    # The drawgun scene: the profile pins cg_drawGun for every other shot, and
    # must explicitly release it for the one scene that demonstrates it.
    base = VisualProfile(name="B").without("cg_drawGun")
    assert "cg_drawGun" not in base.cvars()
    scene = _scene([Variant("gun on", {"cg_drawGun": 1}),
                    Variant("gun off", {"cg_drawGun": 0})], base=base)
    assert scene.validate(inv)["varying"] == ["cg_drawGun"]


def test_variants_must_differ_in_values_not_in_which_cvars_they_set(inv):
    # This is the "more than one moving part" failure: the second variant also
    # turns the gun off, so the film would not isolate picmip.
    scene = _scene([Variant("a", {"r_picmip": 0}),
                    Variant("b", {"r_picmip": 8, "cg_drawGun": 0})])
    with pytest.raises(ValueError, match="more than one moving part"):
        scene.validate(inv)


def test_a_scene_that_changes_nothing_is_refused(inv):
    scene = _scene([Variant("a", {"r_picmip": 8}),
                    Variant("b", {"r_picmip": 8})])
    with pytest.raises(ValueError, match="no cvar actually differs"):
        scene.validate(inv)


def test_base_profile_may_not_also_move(inv):
    # cg_drawGun is pinned by every VisualProfile, so a scene demonstrating it
    # must be told, not silently fight the constant.
    scene = _scene([Variant("on", {"cg_drawGun": 1}),
                    Variant("off", {"cg_drawGun": 0})],
                   base=VisualProfile(name="B"))
    with pytest.raises(ValueError, match="constant and variable"):
        scene.validate(inv)


def test_one_variant_is_not_a_comparison(inv):
    with pytest.raises(ValueError, match="2\\+ variants"):
        _scene([Variant("only", {"r_picmip": 0})]).validate(inv)


def test_specs_share_everything_except_the_variant_cvars(inv):
    scene = _scene([Variant("r_picmip 0", {"r_picmip": 0}),
                    Variant("r_picmip 8", {"r_picmip": 8})])
    a, b = scene.specs()
    assert (a.source, a.start_s, a.end_s) == (b.source, b.start_s, b.end_s)
    assert a.shot_id != b.shot_id
    ca, cb = a.visual.cvars(), b.visual.cvars()
    differing = {k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k)}
    assert differing == {"r_picmip"}


# ── DOCUMENTARY_COLOR_FORMAT (PROOF 0) ────────────────────────────────

def test_rail_colours_are_packed_ints_not_triples():
    from engine.pantheon.color_format import format_for
    # 0x2a8000 rendered green on frames; "42 128 0" collapsed the beam.
    assert format_for("cg_teamRailColor1", (42, 128, 0)) == '"0x2a8000"'
    assert format_for("cg_enemyRailColor2", (255, 40, 40)) == '"0xff2828"'


def test_wallhack_colours_are_triples_not_packed_ints():
    from engine.pantheon.color_format import format_for
    # The OTHER syntax, in the same cgame. SC_ParseColorFromStr rejects hex.
    assert format_for("cg_whEnemyColor", (40, 255, 40)) == '"40 255 40"'


def test_an_unmeasured_colour_cvar_is_refused():
    from engine.pantheon.color_format import format_for
    with pytest.raises(KeyError, match="no MEASURED colour syntax"):
        format_for("cg_someFutureColor", (1, 2, 3))


def test_no_colour_family_is_left_inferred():
    from engine.pantheon.color_format import is_inferred
    # PROOF B filmed the model colour family, so nothing is inferred now.
    assert not is_inferred("cg_enemyLegsColor")   # measured by PROOF B
    assert not is_inferred("cg_teamRailColor1")
