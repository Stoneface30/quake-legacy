"""The HUD is a film surface, the wardrobe is installable, and neither of them
claims a proof it does not have."""
from __future__ import annotations

import zipfile

import pytest

from engine.pantheon import assets as A
from engine.pantheon import asset_library as L
from engine.pantheon import hud
from engine.pantheon import morph as M


# ── the HUD surface ────────────────────────────────────────────────────────

def test_the_identity_effect_is_byte_identical_to_the_shipped_file():
    """HUD_STOCK is the control leg every other treatment is judged against.
    If the writer cannot reproduce the input exactly, every diff it produces
    is contaminated by its own reformatting."""
    text = hud.stock_text()
    out, changed = hud.apply("HUD_STOCK", text)
    assert out == text
    assert changed == []


def test_a_treatment_changes_only_the_families_it_names():
    text = hud.stock_text()
    out, changed = hud.apply("HUD_TELEMETRY_OFF", text)
    assert changed, "the effect changed nothing at all"
    assert set(changed) == {"lagometer", "disconnected"}, \
        "telemetry is exactly those two blocks in the stock file"
    # everything else survives verbatim
    for name in ("gfx/2d/crosshaira", "icons/quad", "medal_accuracy"):
        if f"\n{name}\n" in text:
            assert f"\n{name}\n" in out


def test_hiding_uses_the_idiom_the_shipped_movie_pack_proved():
    """`zzz_zz_moviehud.pk3` hides the netgraph by multiplying the frame by
    zero rather than by supplying blank art. Copy what is known to work."""
    out, _ = hud.apply("HUD_CLEAN")
    assert "map $whiteimage" in out
    assert "blendfunc GL_ZERO GL_ONE" in out


def test_every_effect_declares_whether_it_can_be_cued():
    """A shader wave runs on the engine clock and cannot hit a beat. An effect
    that does not say which kind it is invites somebody to plan a cut on it."""
    for name, e in hud.EFFECTS.items():
        assert e.timing in (hud.FREE_RUNNING, hud.CUEABLE), name


def test_the_pack_carries_the_whole_file_because_that_is_what_gets_replaced(
        tmp_path):
    res = hud.build_pack("HUD_CLEAN", tmp_path)
    pk3 = tmp_path / hud.PACK_NAME
    assert pk3.exists()
    with zipfile.ZipFile(pk3) as z:
        assert z.namelist() == [hud.SHADER_PATH]
        body = z.read(hud.SHADER_PATH).decode("latin-1")
    # a fragment would silently lose every shader it omitted
    assert body.count("\n{") > 200
    assert res["shaders_changed"] > 0


def test_a_built_pack_never_reports_itself_proven(tmp_path):
    res = hud.build_pack("HUD_GHOST", tmp_path)
    assert res["proven"] is False
    assert "look at" in res["how_to_prove"]


def test_the_pack_sorts_after_the_existing_movie_hud_pack():
    """id Tech 3 resolves by load order and the last pack wins."""
    assert hud.PACK_NAME > "zzz_zz_moviehud.pk3"


# ── the wardrobe ───────────────────────────────────────────────────────────

def test_the_database_holds_far_more_than_the_one_family_we_ship():
    fams = L.families()
    assert L.FIDELITY_FAMILY in fams
    styled = {n: f for n, f in fams.items() if n != L.FIDELITY_FAMILY}
    assert len(styled) >= 10, "the wardrobe is the point"
    assert sum(f.renders for f in styled.values()) > 5000, \
        "thousands of finished renders that have never been in a picture"


def test_registering_publishes_looks_without_pretending_packs_exist():
    added = L.register()
    # idempotent: a second call adds nothing
    assert L.register() == []
    for look in added:
        assert look in A.SETS
        s = A.SETS[look]
        assert s.packs, f"{look} declares no pack"
        assert "pixel question" in s.note


def test_a_look_only_counts_images_that_override_something_real():
    """An image only overrides a stock path when it is written AT that path
    with THAT extension. A plan that counted rows would overstate coverage."""
    plan = L.plan("neon", verify_disk=False)
    assert plan.renders > 0
    assert plan.overridable + plan.not_in_pak + plan.missing_on_disk \
        == plan.renders


def test_the_shape_critical_routing_rule_is_reported_not_ignored():
    """Diffusion destroys alpha edges on FX sheets. Whether a family touches
    them is a fact the caller is entitled to before installing it."""
    for name, fam in L.families().items():
        if fam.is_fidelity:
            assert not fam.restyles_fx
        for c in fam.fx_categories:
            assert c in L.FX_CATEGORIES


def test_tiny_sample_families_are_not_offered_as_looks():
    """A family with eleven renders would dress almost nothing and the result
    would be stock with a few odd tiles in it."""
    L.register()
    for name, fam in L.families().items():
        if fam.renders < L.MIN_RENDERS_FOR_A_LOOK:
            assert L.look_name(name) not in A.SETS, name


# ── the morph plans ────────────────────────────────────────────────────────

def test_a_plan_needs_more_than_one_take():
    with pytest.raises(ValueError, match="two takes"):
        M.MorphPlan("X", "", (M.Take("STOCK"),))


def test_a_blend_is_never_reported_ready_while_alignment_is_unproven():
    """Two runs of the engine do not start on the same tick. A cut survives
    that and a dissolve does not, so the ladder must not flatten."""
    for name, plan in M.RECIPES.items():
        if plan.join == M.CUT:
            assert plan.ready, name
            assert not plan.alignment_required, name
        else:
            assert not plan.ready, name
            assert plan.alignment_required, name
            assert plan.blockers, name
        assert plan.alignment_proven is False, name


def test_a_cut_has_no_duration_and_a_blend_must_have_one():
    with pytest.raises(ValueError, match="no duration"):
        M.MorphPlan("X", "", (M.Take("A"), M.Take("B")), join=M.CUT,
                    join_ms=400)
    with pytest.raises(ValueError, match="duration in ms"):
        M.MorphPlan("X", "", (M.Take("A"), M.Take("B")), join=M.DISSOLVE)


def test_the_capture_list_is_the_whole_interface_to_the_render_side():
    caps = M.captures_for("ERA_LADDER")
    assert [c["index"] for c in caps] == [0, 1, 2, 3]
    assert [c["look"] for c in caps] == ["STOCK", "UHD", "PAINTERLY", "NEON"]
    assert all("hud" in c for c in caps)


def test_a_plan_is_validated_against_what_actually_exists():
    L.register()
    ok = M.validate("WORLD_FLIP", list(A.SETS), list(hud.EFFECTS))
    assert ok["ok"] and not ok["missing_looks"]

    bad = M.validate("WORLD_FLIP", ["STOCK"], list(hud.EFFECTS))
    assert not bad["ok"] and bad["missing_looks"] == ["NEON"]


def test_every_take_names_a_look_and_a_hud_effect_that_could_exist():
    """A plan that names a look nobody can build is a wish, not a plan."""
    L.register()
    for name, plan in M.RECIPES.items():
        for take in plan.takes:
            assert take.hud in hud.EFFECTS, f"{name}: {take.hud}"
            assert take.look in A.SETS, f"{name}: {take.look}"


# ── the offline answer to DLSS, and the verdict floor ──────────────────────

def test_the_supersampling_field_is_finally_read_by_something():
    """`internal_scale` described a technique for months and no code consumed
    it, so every master render silently shipped at 1x."""
    from creative_suite.engine import render_profile as R
    m = R.PROFILES["MASTER_RASTER"]
    geo = R.capture_geometry(m)
    assert geo["supersampled"]
    assert geo["capture_width"] > geo["deliver_width"]
    assert geo["downsample_required"]
    assert geo["downsample_filter"], "a downsample nobody performs is a bug"


def test_a_profile_that_does_not_supersample_asks_for_no_downsample():
    from creative_suite.engine import render_profile as R
    geo = R.capture_geometry(R.PROFILES["REVIEW"])
    assert not geo["supersampled"]
    assert geo["downsample_filter"] is None
    assert R.supersample_blockers(R.PROFILES["REVIEW"]) == []


def test_an_unverified_supersampled_profile_names_its_blockers():
    """It has never been captured at that size. Say so rather than let
    somebody discover it during an overnight run."""
    from creative_suite.engine import render_profile as R
    blockers = R.supersample_blockers(R.PROFILES["MASTER_RASTER"])
    assert blockers
    assert any("never been captured" in b for b in blockers)


def test_a_lossy_intermediate_is_flagged_when_supersampling():
    from creative_suite.engine import render_profile as R
    import dataclasses
    lossy = dataclasses.replace(R.PROFILES["MASTER_RASTER"],
                                intermediate="mjpeg")
    assert any("lossy intermediate" in b
               for b in R.supersample_blockers(lossy))


def test_writing_a_verdict_asks_the_smallest_disk_threshold(monkeypatch,
                                                            tmp_path):
    """The one carried item that was a missing call rather than a missing
    judgement: `review_db_write_safe` existed with no caller."""
    from creative_suite.engine import review_proxy as rp
    from engine.pantheon import disk_policy

    monkeypatch.setattr(rp, "EDITORIAL_DB_PATH", tmp_path / "editorial.db")
    asked = []

    def full(path):
        asked.append(str(path))
        return disk_policy.DiskVerdict("REVIEW_DB_WRITE", str(path), 1, 10**9,
                                       False)

    monkeypatch.setattr(disk_policy, "review_db_write_safe", full)
    with pytest.raises(RuntimeError, match="refusing to write a verdict"):
        rp.put_review(1, verdict="LOVE")
    assert asked, "put_review did not ask the disk policy at all"
