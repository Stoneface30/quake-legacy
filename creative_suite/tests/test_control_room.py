"""The semantic layer: proofs that are banked, a grammar that cannot lie about
its own status, and a director's list nothing is allowed to quietly edit."""
from __future__ import annotations

import pytest

from engine.pantheon import backend_planner as BP
from engine.pantheon import creative_intent as CI
from engine.pantheon import defaults as D
from engine.pantheon import director_notes as DN
from engine.pantheon import effect_recipes as ER
from engine.pantheon import ideas as ID
from engine.pantheon import visual_proof as VP


@pytest.fixture
def registry(tmp_path, monkeypatch):
    """A private proof registry, so a test never judges the real one."""
    monkeypatch.setattr(VP.S, "store_root", lambda: tmp_path)
    return tmp_path


def _proof(**kw):
    base = dict(capability="CAP", proof_id="CAP/test",
                semantic_expectation="the thing looks like the thing",
                backend="PANTHEON_QUAKE_OFFSCREEN", profile="REVIEW",
                engine_version="wolfcamql-11.3")
    return VP.VisualProof(**{**base, **kw})


# -- a proof is banked, and stops being valid when its inputs move ----------

def test_an_automated_result_never_promotes_itself(registry):
    VP.record(_proof(status=VP.Status.AUTOMATED_PASS,
                     automated_results={"green_pixels": 49509}))
    assert VP.status("CAP") is VP.Status.AUTOMATED_PASS
    assert not VP.proven("CAP")
    with pytest.raises(VP.ProofUnavailable):
        VP.require("CAP")


def test_only_a_person_makes_it_proven(registry):
    VP.record(_proof(status=VP.Status.NEEDS_VISUAL_CONFIRMATION))
    VP.judge("CAP/test", verdict="yes", note="looks right")
    p = VP.require("CAP")
    assert p.status is VP.Status.VISUALLY_PROVEN
    assert p.human_verdict == "YES" and p.human_note == "looks right"
    assert p.judged_at


def test_a_rejection_is_recorded_as_one(registry):
    VP.record(_proof(status=VP.Status.NEEDS_VISUAL_CONFIRMATION))
    VP.judge("CAP/test", verdict="no", note="wrong guy")
    assert VP.status("CAP") is VP.Status.VISUALLY_REJECTED
    assert VP.get("CAP/test").human_note == "wrong guy"


def test_a_banked_proof_is_consumed_not_re_run(registry):
    """The whole point: five A/B renders of the same fact is a loop nobody
    chose."""
    VP.record(_proof(status=VP.Status.VISUALLY_PROVEN, human_verdict="YES"))
    for _ in range(5):
        assert VP.proven("CAP", backend="PANTHEON_QUAKE_OFFSCREEN",
                         profile="REVIEW", engine_version="wolfcamql-11.3")


def test_a_changed_input_reopens_the_question(registry):
    VP.record(_proof(status=VP.Status.VISUALLY_PROVEN, human_verdict="YES"))
    assert VP.status("CAP", profile="REVIEW") is VP.Status.VISUALLY_PROVEN
    assert VP.status("CAP", profile="ANALYSIS") is VP.Status.REGRESSION
    assert VP.status("CAP", engine_version="wolfcamql-12.7") is VP.Status.REGRESSION


def test_an_unknown_capability_is_untested_not_false(registry):
    assert VP.status("NEVER_ASKED") is VP.Status.UNTESTED


def test_the_seeded_registry_is_conservative(registry):
    VP.seed()
    green = VP.status("GREEN_KEEL_REVIEW", backend="PANTHEON_QUAKE_OFFSCREEN",
                      profile="REVIEW", engine_version="wolfcamql-11.3")
    assert green is VP.Status.VISUALLY_PROVEN
    # filmed under the old window backend, so it is NOT proven for the new one
    assert VP.status("XRAY_PLAYER") is VP.Status.NEEDS_VISUAL_CONFIRMATION
    assert any(p.capability == "OFFSCREEN_POINTER_FREE"
               for p in VP.awaiting_human())


# -- the grammar reports its own status honestly ----------------------------

def test_no_recipe_declares_its_own_status():
    src = (ER.__file__ and open(ER.__file__, encoding="utf-8").read())
    assert "status=Status.PRODUCTION_READY" not in src
    assert "status=Status.VISUALLY_PROVEN" not in src


def test_every_recipe_asks_for_truth_the_engine_can_name():
    for r in ER.RECIPES:
        unknown = [t for t in r.required_truth if t not in ER.TRUTH]
        assert not unknown, f"{r.id} needs truth nobody defined: {unknown}"


def test_a_recipe_without_a_proven_capability_is_not_backend_supported():
    st = ER.status("WALL_REMOVE_XRAY")
    assert st is ER.Status.SEMANTICALLY_SUPPORTED
    assert "WALL_REMOVAL" in ER.missing_capabilities("WALL_REMOVE_XRAY")


def test_nothing_is_production_ready_yet():
    """PRODUCTION_READY needs a run through the pipeline, not a registry."""
    assert all(ER.status(r.id) is not ER.Status.PRODUCTION_READY
               for r in ER.RECIPES)


def test_a_recipe_spells_no_cvar():
    src = open(ER.__file__, encoding="utf-8").read()
    for token in ("cg_", "r_mode", "cl_avi", "cvarinterp", "remapshader"):
        assert token not in src, f"{token} leaked into the film grammar"


# -- the director's list -----------------------------------------------------

def test_the_master_list_is_all_there():
    assert len(ID.IDEAS) == 306
    assert [i.n for i in ID.IDEAS] == list(range(1, 307))


def test_no_idea_stores_a_status():
    """Statuses are derived. A stored one goes stale the moment a capability
    moves, and 306 stale rows is worse than none."""
    src = open(ID.__file__, encoding="utf-8").read()
    for token in ("PRODUCTION_READY", "VISUALLY_PROVEN\","):
        assert token not in src.split("def row(")[0]


def test_an_idea_row_derives_its_columns():
    row = ID.row(62)                      # true X-ray keeps the wall
    assert row["recipe"] == "XRAY_ACTOR"
    assert "TRANSFORM" in row["required_truth"]
    assert row["status"] in {s.value for s in ER.Status}
    assert row["production_priority"] == "HUMAN_FIELD"


def test_an_idea_with_no_recipe_says_so_rather_than_pretending():
    row = ID.row(29)                      # fly the camera into an eye
    assert row["recipe"] is None and row["status"] == "NO_RECIPE_YET"
    assert len(ID.unimplemented()) > 100, "the backlog is long, and honest"


def test_every_recipe_traces_back_to_an_idea_or_is_flagged():
    """A recipe nobody asked for is one I invented. That is allowed, but it
    should be visible."""
    invented = [r.id for r in ER.RECIPES if not ID.by_recipe(r.id)]
    assert invented == [], f"recipes with no idea behind them: {invented}"


# -- the original notes ------------------------------------------------------

def test_the_original_notes_are_verbatim():
    """Including the typos. A cleaned-up note is a different note."""
    n = DN.get("N11")
    assert "reallllllly" in n.text
    assert DN.get("N01").text.startswith("When we have clips from a teamfight")


def test_the_notes_carry_requirements_the_numbered_list_lost():
    names = {r["requirement"] for r in DN.NEW_REQUIREMENTS}
    for expected in ("RAIL_BUILD_SLOWMO", "SCOREBOARD_IN_AD_SPACE",
                     "DAMAGE_OVER_HEAD", "OUTSHAFT_STAT"):
        assert expected in names
    assert len(DN.uncarried()) >= 10


def test_a_requirement_that_could_lie_carries_a_caution():
    by_name = {r["requirement"]: r for r in DN.NEW_REQUIREMENTS}
    assert "hitscan" in by_name["RAIL_BUILD_SLOWMO"]["caution"]
    assert "NOT_DERIVABLE" in by_name["DAMAGE_OVER_HEAD"]["caution"]


# -- a free-form idea is kept as written ------------------------------------

def test_a_note_is_stored_exactly_as_written(tmp_path, monkeypatch):
    monkeypatch.setattr(CI.S, "store_root", lambda: tmp_path)
    text = "freeze on the rail, then fly INTO the rocket, hit the beat"
    n = CI.capture(text, subject="PERF:X")
    assert n.text == text
    assert CI.notes("PERF:X")[0].text == text


def test_an_idea_with_no_route_says_the_gap_is_ours(tmp_path, monkeypatch):
    monkeypatch.setattr(CI.S, "store_root", lambda: tmp_path)
    n = CI.capture("make the whole map breathe like it is alive")
    assert n.route is CI.Route.IMPLEMENTATION_ROUTE_UNKNOWN
    assert CI.unrouted()


def test_intents_are_read_additively(tmp_path, monkeypatch):
    monkeypatch.setattr(CI.S, "store_root", lambda: tmp_path)
    n = CI.capture("slow it down and follow the rocket with the camera")
    assert CI.Kind.TIMING.value in n.intents
    assert CI.Kind.CAMERA.value in n.intents
    assert n.text.startswith("slow it down")


# -- the backend planner -----------------------------------------------------

def test_the_beauty_pass_goes_to_the_offscreen_backend():
    plan = BP.plan(recipes=("XRAY_ACTOR",))
    assert plan.passes[0].name == "BEAUTY"
    assert plan.passes[0].backend == BP.QUAKE
    assert plan.passes[-1].backend == BP.FFMPEG


def test_a_pass_nothing_can_deliver_is_carried_not_dropped():
    plan = BP.plan(recipes=("WALL_REMOVE_XRAY",))
    unsupported = plan.unsupported
    assert unsupported and any("WALL_REMOVAL" in p.capabilities
                               for p in unsupported)
    assert not plan.deliverable
    assert all(p.because for p in plan.passes), "every pass says why"


# -- versioned defaults ------------------------------------------------------

def test_review_is_720p30_and_film_is_1080p60():
    assert (D.REVIEW_V1.width, D.REVIEW_V1.height, D.REVIEW_V1.fps) == (1280, 720, 30)
    assert (D.FPV_FILM_V1.width, D.FPV_FILM_V1.height, D.FPV_FILM_V1.fps) == (1920, 1080, 60)


def test_a_profile_id_changes_when_the_profile_does():
    before = D.REVIEW_V1.id
    changed = D.FilmProfile(**{**D.REVIEW_V1.__dict__, "fps": 60})
    assert changed.id != before


def test_the_public_profile_cannot_show_a_name():
    p = D.get("PUBLIC_EXPORT_V1")
    assert p.hud == "NONE"
    assert any("name" in n for n in p.notes)


# -- the first recipe, and what filming it taught ---------------------------

def test_the_reveal_needs_the_body_on_screen_not_only_hidden():
    """The first render of this recipe showed an empty frame: the plan had
    chosen the longest OCCLUDED span, and through all of it the body sat 56 to
    64 degrees off the centre of view. Occluded and on-screen are two
    questions."""
    from engine.pantheon import choreography as CH
    rows = [
        {"t": 1000, "state": CH.Visibility.OCCLUDED_OFF_SCREEN.value},
        {"t": 1025, "state": CH.Visibility.OCCLUDED_OFF_SCREEN.value},
        {"t": 1050, "state": CH.Visibility.OCCLUDED_OFF_SCREEN.value},
        {"t": 2000, "state": CH.Visibility.OCCLUDED_IN_FRAME.value},
        {"t": 2400, "state": CH.Visibility.OCCLUDED_IN_FRAME.value},
    ]
    spans = CH.occluded_spans(rows, min_ms=250)
    assert len(spans) == 1
    assert spans[0]["start_ms"] == 2000, "an off-screen span was offered as a reveal"


def test_the_frustum_test_agrees_with_the_measured_failure():
    """The numbers from the render that failed: 62 degrees off yaw is out."""
    from engine.pantheon import choreography as CH
    eye = (0.0, 0.0, 26.0)
    ahead = (1000.0, 0.0, 26.0)
    inside, yaw, _pitch = CH._in_frame(eye, 0.0, 0.0, ahead)
    assert inside and abs(yaw) < 1
    beside = (0.0, 1000.0, 26.0)          # 90 degrees to the left
    outside, yaw2, _ = CH._in_frame(eye, 0.0, 0.0, beside)
    assert not outside and abs(yaw2) > 45


def test_the_overlay_alpha_is_the_engines_scale_not_a_fraction():
    """Written as 0.55 it drew nothing at all. The engine registers these with
    a default of 30, and the proof that put the capability in the registry
    used 190."""
    from engine.pantheon import visual_profile as VP
    c = VP.profile("REVIEW_XRAY").resolve()
    for name in ("cg_whAlpha", "cg_whEnemyAlpha"):
        assert isinstance(c[name], int) and c[name] > 1, \
            f"{name}={c[name]!r} reads as transparent"


def test_the_overlay_colour_uses_its_own_familys_syntax():
    """The rail family takes packed hex; this one does not. Writing the wrong
    form is a silent no-op."""
    from engine.pantheon import color_format as CF
    from engine.pantheon import visual_profile as VP
    c = VP.profile("REVIEW_XRAY").resolve()
    assert c["cg_whColor"] == CF.format_for("cg_whColor", VP.PANTHEON_GREEN)
    assert "0x" not in str(c["cg_whColor"])


def test_a_plan_carries_the_beat_it_cannot_film():
    """The freeze the grammar wants has no proven capability, so it is
    deferred in writing rather than dropped."""
    from engine.pantheon import choreography as CH
    plan = CH.ChoreographyPlan("XRAY_ACTOR", "PERF:X", CH.TimeMap(0, 1000),
                               CH.CameraPlan("RECORDED_POV", 1))
    plan.deferred.append("FREEZE: capability only SOURCE_REGISTERED")
    assert plan.deferred and plan.deliverable
