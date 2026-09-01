"""PANTHEON grade + FX script generators.

The two failure modes these defend against are both SILENT-until-fatal:

* A grade shader that declares one of ``RB_ColorCorrect``'s four uniforms
  but never READS it compiles fine, gets the uniform stripped by the GLSL
  compiler, and then kills the engine with ``ri.Error(ERR_FATAL)`` at
  renderer init (free_wins_proof.md proof 3).
* An ``.fx`` file that models a trail as a one-shot ``runfx`` cue emits a
  single puff at the muzzle, which looks enough like a working trail to be
  reported as one. ``weapon/rocket/trail`` is a per-frame ENGINE HOOK
  (cg_fx_scripts.c:7147) and must be defined, never fired.
"""
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import pantheon_fx as pfx, pantheon_grade as pg
from creative_suite.engine.pantheon_scene import (INTENSITY_HERO,
                                                  INTENSITY_OFF,
                                                  INTENSITY_SUBTLE)


# --- grade ----------------------------------------------------------------

@pytest.mark.parametrize("grade", pg.GRADES)
def test_every_grade_consumes_all_four_uniforms(grade):
    """The ERR_FATAL guard — this is the one that takes the engine down."""
    source = pg.shader_source(grade)
    pg.assert_consumes_all_uniforms(source)
    for name in pg.REQUIRED_UNIFORMS:
        assert source.count(name) >= 2, name


def test_uniform_guard_actually_catches_a_stripped_uniform():
    bad = pg.shader_source(pg.GRADE_ORIGINAL).replace(
        "mix( avgLuminance, gammaColor, p_contrast )", "gammaColor")
    with pytest.raises(ValueError, match="ERR_FATAL"):
        pg.assert_consumes_all_uniforms(bad)


def test_original_grade_reproduces_the_stock_math():
    """GRADE_ORIGINAL is a REAL variant, not 'ship no pk3' — so an A/B/C
    look comparison runs all three through the identical override path and
    the only difference between frames is colour maths."""
    source = pg.shader_source(pg.GRADE_ORIGINAL)
    assert "mix( avgLuminance, gammaColor, p_contrast )" in source
    for absent in ("saturation", "vignette", "coolShadow"):
        assert absent not in source


def test_pantheon_grades_are_one_look_at_two_strengths():
    subtle = pg.shader_source(pg.GRADE_PANTHEON_SUBTLE)
    hero = pg.shader_source(pg.GRADE_PANTHEON_HERO)
    # same operations, in the same order
    for op in ("shadowLift", "smoothstep", "lumaWeights", "coolShadow",
               "warmHigh", "vignette"):
        assert op in subtle and op in hero
    assert subtle != hero


def test_grade_is_not_orange_and_teal_and_protects_visibility():
    """Restraint is a requirement, not taste: shadows are LIFTED before the
    curve and the vignette is capped, so nothing gameplay-relevant is lost."""
    for grade in (pg.GRADE_PANTHEON_SUBTLE, pg.GRADE_PANTHEON_HERO):
        look = pg._LOOK[grade]
        assert 0.80 <= look["saturation"] <= 1.0     # desaturate, never boost
        assert look["shadow_lift"] > 0               # lift, never crush
        assert look["vignette"] <= 0.35
        assert max(abs(v) for v in look["cool_shadow"]) <= 0.05
        assert max(abs(v) for v in look["warm_high"]) <= 0.05


def test_shadow_lift_precedes_the_contrast_curve():
    src = pg.shader_source(pg.GRADE_PANTHEON_HERO)
    assert src.index("shadowLift + color") < src.index("smoothstep(0.0, 1.0")


def test_unknown_grade_is_refused():
    with pytest.raises(ValueError):
        pg.shader_source("GRADE_TEAL_ORANGE")


def test_build_pack_writes_one_deterministic_pk3(tmp_path):
    a = pg.build_pack(pg.GRADE_PANTHEON_SUBTLE, tmp_path)
    first = a.read_bytes()
    b = pg.build_pack(pg.GRADE_PANTHEON_SUBTLE, tmp_path)
    assert b.read_bytes() == first, "pk3 must be byte-stable across builds"
    assert a.name == pg.PK3_NAME and a.name.startswith("zzz_")  # ENG-2 order
    with zipfile.ZipFile(a) as zf:
        assert zf.namelist() == [pg.SHADER_PATH]


def test_remove_pack_is_idempotent(tmp_path):
    pg.build_pack(pg.GRADE_ORIGINAL, tmp_path)
    pg.remove_pack(tmp_path)
    pg.remove_pack(tmp_path)
    assert not (tmp_path / pg.PK3_NAME).exists()


def test_grade_hashes_differ_per_grade():
    assert len({pg.grade_hash(g) for g in pg.GRADES}) == len(pg.GRADES)


# --- fx -------------------------------------------------------------------

def test_off_level_defines_no_effects_but_is_still_a_real_file():
    src = pfx.script_source(INTENSITY_OFF)
    assert pfx.FX_ROCKET_TRAIL not in src and pfx.FX_IMPACT not in src
    assert src.strip(), "OFF must still be loadable so cg_fxfile is exercised"


@pytest.mark.parametrize("level", [INTENSITY_SUBTLE, INTENSITY_HERO])
def test_both_effects_are_defined_with_balanced_braces(level):
    src = pfx.script_source(level)
    assert f"{pfx.FX_ROCKET_TRAIL} {{" in src
    assert f"{pfx.FX_IMPACT} {{" in src
    assert src.count("{") == src.count("}")


def test_trail_uses_the_engine_hook_name_not_an_invented_one():
    """cg_fx_scripts.c:7147 binds this exact string; a custom name would
    define an effect nothing ever calls."""
    assert pfx.FX_ROCKET_TRAIL == "weapon/rocket/trail"


def test_trail_is_distance_emitted_not_a_one_shot():
    """A one-shot cannot make a trail. `distance N {}` also keeps trail
    density framerate-independent, which is why the shipped script uses it."""
    src = pfx.script_source(INTENSITY_SUBTLE)
    trail = src[src.index(pfx.FX_ROCKET_TRAIL):src.index(pfx.FX_IMPACT)]
    assert "distance " in trail and "emitter " in trail


@pytest.mark.parametrize("level", [INTENSITY_SUBTLE, INTENSITY_HERO])
def test_only_ql_shipped_shaders_are_referenced(level):
    """Proof 2: Q3 asset names (e.g. sprites/balloon3) are absent from QL's
    pak00 and render as blue placeholder quads."""
    allowed = {"smokePuff", "flareShader", "rocketExplosion"}
    used = {ln.split()[1] for ln in pfx.script_source(level).splitlines()
            if ln.strip().startswith("shader\t")
            or ln.strip().startswith("shader ")}
    assert used <= allowed, used - allowed


def test_subtle_is_genuinely_restrained_against_hero():
    s, h = pfx._LEVEL["SUBTLE"], pfx._LEVEL["HERO"]
    assert s["trail_life"] < h["trail_life"]
    assert s["trail_alpha"] < h["trail_alpha"]
    assert s["burst_count"] < h["burst_count"]
    # both keep a light (omitting one DELETES the stock rocket glow);
    # HERO's is brighter and cooler
    assert s["trail_light"] is not None and h["trail_light"] is not None
    assert h["trail_light"][1] > s["trail_light"][1] * 0.9
    assert s["bloom"] is None and h["bloom"] is not None


def test_write_script_uses_lf_only(tmp_path):
    """Same discipline the .cam10 CRLF bug earned every generated asset."""
    path = pfx.write_script(INTENSITY_HERO, tmp_path)
    assert b"\r\n" not in path.read_bytes()
    assert path.name.endswith(".fx")


def test_unknown_level_is_refused():
    with pytest.raises(ValueError):
        pfx.script_source("MEDIUM")


def test_script_hashes_differ_per_level():
    levels = [INTENSITY_OFF, INTENSITY_SUBTLE, INTENSITY_HERO]
    assert len({pfx.script_hash(x) for x in levels}) == 3
