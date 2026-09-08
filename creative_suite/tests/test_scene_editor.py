"""Scene Editor — projection, three clocks, and identity discipline (§56).

Every test here runs against the REAL committed databases and the three
scenes the directive names, because the properties under test are exactly
the ones a synthetic fixture would let slide:

* #5979   IMPACT_PROJECTILE — the known mapping
          ``553075000 demo_us -> 5250000 edit_us`` must survive.
* #22154  RHYTHMIC_TRACKING — 20 LG contacts grouped into 8 bursts. If this
          ever renders like a projectile scene, the lane is lying.
* #22076  TENSION_RELEASE — a three-stage frag progression.

If the corpus is not on this machine the module skips rather than passing
vacuously; a green run that proved nothing is worse than a red one.
"""
from __future__ import annotations

import copy

import pytest
from fastapi.testclient import TestClient

from creative_suite.api import frags as frags_api
from creative_suite.api import scene_editor as api
from creative_suite.app import create_app
from creative_suite.engine import scene_editor_projection as proj
from creative_suite.engine.music_features_v2 import MusicFeatureStore
from creative_suite.engine.scene_recipe import MusicPlacement

IMPACT_FRAG = 5979
TRACKING_FRAG = 22154
CLUTCH_FRAG = 22076
ALL_FRAGS = (IMPACT_FRAG, TRACKING_FRAG, CLUTCH_FRAG)

# The load-bearing constant from the directive. Right-biased, because the
# impact instant is also the start of a freeze and the RIGHT edge of that
# freeze is where the picture resumes.
IMPACT_DEMO_US = 553_075_000
IMPACT_EDIT_US = 5_250_000


pytestmark = pytest.mark.skipif(
    not (api.FRAG_DB_PATH.exists() and api.DEMO_V2_DB_PATH.exists()),
    reason="recognition corpus not present on this machine",
)


@pytest.fixture(autouse=True)
def _clean_store():
    api.reset_store()
    yield
    api.reset_store()


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


def projection(frag_id: int, **kwargs):
    return proj.build_projection(frag_id, frag_db=api.FRAG_DB_PATH,
                                 demo_v2_db=api.DEMO_V2_DB_PATH,
                                 music_db=api.MUSIC_FEATURE_DB_PATH, **kwargs)


# ===========================================================================
# 1. three-clock mapping
# ===========================================================================

def test_impact_demo_to_edit_mapping_survives():
    """demo -> edit for the right-biased impact, exactly as documented."""
    evidence = proj.SceneEvidence(IMPACT_FRAG, frag_db=api.FRAG_DB_PATH,
                                  demo_v2_db=api.DEMO_V2_DB_PATH)
    time_map = evidence.recipe().time_map_object()
    assert time_map.demo_to_edit(IMPACT_DEMO_US, bias="right") == IMPACT_EDIT_US


def test_impact_anchor_projects_to_the_same_edit_us():
    p = projection(IMPACT_FRAG)
    impact = next(a for a in p["anchors"] if a["anchor_id"] == "impact-0")
    assert impact["resolved_demo_us"] == IMPACT_DEMO_US
    assert impact["edit_us"] == IMPACT_EDIT_US
    event = next(e for e in p["lanes"][proj.LANE_GAME_EVENTS]["events"]
                 if e["kind"] == "PROJECTILE_IMPACT")
    assert event["demo_us"] == IMPACT_DEMO_US
    assert event["edit_us"] == IMPACT_EDIT_US


def test_three_clocks_round_trip_through_both_projections():
    """demo <- edit -> music, with edit_us as the single authority."""
    evidence = proj.SceneEvidence(IMPACT_FRAG, frag_db=api.FRAG_DB_PATH,
                                  demo_v2_db=api.DEMO_V2_DB_PATH)
    time_map = evidence.recipe().time_map_object()
    placement = MusicPlacement("a" * 64, 12_345_000, 0)
    for edit_us in (0, 1_000_000, 4_500_000, 6_000_000, 9_000_000):
        demo_us = time_map.edit_to_demo(edit_us, bias="left")
        assert isinstance(demo_us, int)
        music_us = placement.edit_to_music(edit_us)
        assert proj.music_to_edit(placement, music_us) == edit_us


def test_every_lane_value_is_an_integer_microsecond():
    for frag_id in ALL_FRAGS:
        p = projection(frag_id)
        for event in p["lanes"][proj.LANE_GAME_EVENTS]["events"]:
            assert isinstance(event["edit_us"], int)
            assert isinstance(event["demo_us"], int)
        for segment in p["lanes"][proj.LANE_TIME]["segments"]:
            for key in ("edit_start_us", "edit_end_us", "demo_start_us",
                        "demo_end_us"):
                assert isinstance(segment[key], int), (frag_id, key)


# ===========================================================================
# 2. freeze visualization — positive edit duration, zero demo duration
# ===========================================================================

def test_freeze_occupies_edit_time_while_consuming_no_demo_time():
    for frag_id in ALL_FRAGS:
        segments = projection(frag_id)["lanes"][proj.LANE_TIME]["segments"]
        freezes = [s for s in segments if s["kind"] == "freeze"]
        assert freezes, f"frag {frag_id} has no freeze to draw"
        for freeze in freezes:
            assert freeze["demo_duration_us"] == 0
            assert freeze["edit_duration_us"] > 0
            assert freeze["occupies_edit_time"] is True
            assert freeze["consumes_demo_time"] is False
            # The lane must be able to draw a width, so the edit interval is
            # genuinely non-degenerate, not merely flagged as such.
            assert freeze["edit_end_us"] > freeze["edit_start_us"]


def test_freeze_neighbours_stay_contiguous_in_both_clocks():
    segments = projection(IMPACT_FRAG)["lanes"][proj.LANE_TIME]["segments"]
    for before, after in zip(segments, segments[1:]):
        assert before["edit_end_us"] == after["edit_start_us"]
        assert before["demo_end_us"] == after["demo_start_us"]


def test_editing_the_freeze_hold_changes_only_the_edit_clock():
    evidence = proj.SceneEvidence(IMPACT_FRAG, frag_db=api.FRAG_DB_PATH,
                                  demo_v2_db=api.DEMO_V2_DB_PATH)
    specs = proj.segment_specs(evidence.recipe().time_map)
    index = next(i for i, s in enumerate(specs) if s["kind"] == "freeze")
    before = proj.rebuild_time_map(specs)
    after = proj.rebuild_time_map(proj.set_freeze_hold(specs, index, 750_000))
    assert after[index].edit_end_us - after[index].edit_start_us == 750_000
    assert after[index].demo_end_us == after[index].demo_start_us
    # Total demo span is untouched; total edit span grew by the difference.
    assert after[-1].demo_end_us == before[-1].demo_end_us
    assert after[-1].edit_end_us - before[-1].edit_end_us == \
        750_000 - (before[index].edit_end_us - before[index].edit_start_us)


def test_retiming_the_draft_propagates_to_every_lane(client):
    """A retimed draft must not leave other lanes on the OLD edit clock.

    Regression: the projection was rebuilt from evidence while only the TIME
    lane was patched from the draft, so a lengthened freeze changed the
    hatched block and nothing else — the music, the events and the reported
    duration all stayed on the pre-edit map.
    """
    before = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()["projection"]
    segments = before["lanes"][proj.LANE_TIME]["segments"]
    index = next(s["index"] for s in segments if s["kind"] == "freeze")
    old_hold = segments[index]["edit_duration_us"]
    specs = client.get(f"/api/scene-editor/{IMPACT_FRAG}/draft").json()["time_map"]
    specs[index] = dict(specs[index], freeze_us=old_hold + 500_000)
    client.put(f"/api/scene-editor/{IMPACT_FRAG}/draft", json={"time_map": specs})

    after = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()["projection"]
    assert after["duration_us"] == before["duration_us"] + 500_000
    assert after["lanes"][proj.LANE_TIME]["segments"][index]["edit_duration_us"] \
        == old_hold + 500_000
    # Everything downstream of the freeze slid by the same amount, on every
    # lane, because they all read one TimeMap.
    def edit_of(payload, kind):
        return next(e["edit_us"] for e in payload["lanes"][proj.LANE_GAME_EVENTS]["events"]
                    if e["kind"] == kind)
    # The launch sits BEFORE the freeze and does not move…
    assert edit_of(after, "PROJECTILE_LAUNCH") == edit_of(before, "PROJECTILE_LAUNCH")
    # …while the impact is pinned to the freeze's right edge and slides with it.
    assert edit_of(after, "PROJECTILE_IMPACT") == \
        edit_of(before, "PROJECTILE_IMPACT") + 500_000
    tail_before = before["lanes"][proj.LANE_TIME]["segments"][-1]
    tail_after = after["lanes"][proj.LANE_TIME]["segments"][-1]
    assert tail_after["edit_start_us"] == tail_before["edit_start_us"] + 500_000
    assert tail_after["demo_start_us"] == tail_before["demo_start_us"]
    assert after["lanes"][proj.LANE_MUSIC_WAVEFORM]["window_music_end_us"] == \
        before["lanes"][proj.LANE_MUSIC_WAVEFORM]["window_music_end_us"] + 500_000


def test_the_rate_menu_never_offers_reverse():
    assert all(num > 0 and den > 0 for num, den in proj.ALLOWED_RATES)


# ===========================================================================
# 3. music waveform projection
# ===========================================================================

@pytest.fixture(scope="module")
def feature():
    store = MusicFeatureStore(api.MUSIC_FEATURE_DB_PATH)
    features = store.all_features()
    if not features:
        pytest.skip("music feature catalog is empty")
    return next((f for f in features if f.energy_curve), features[0])


def test_envelope_comes_from_the_cached_curve_and_is_bounded(feature):
    envelope = proj.waveform_envelope(feature, 256)
    assert len(envelope) == 256
    for lo, hi in envelope:
        assert 0.0 <= lo <= hi <= 1.0


def test_envelope_is_cached_per_track_version_and_window(feature):
    proj.clear_envelope_cache()
    first = proj.waveform_envelope(feature, 128)
    second = proj.waveform_envelope(feature, 128)
    assert first is second, "the envelope must be served from cache"
    other = proj.waveform_envelope(feature, 128, music_start_us=0,
                                   music_end_us=feature.duration_us // 4)
    assert other is not first, "a different window must not reuse the cache"


def test_music_lane_projects_music_us_onto_edit_us(feature):
    placement = MusicPlacement(feature.track_hash, 4_000_000, 0)
    lane = proj.project_music_lane(feature, placement, 9_250_000)
    assert lane["window_music_start_us"] == 4_000_000
    assert lane["window_music_end_us"] == 13_250_000
    for event in lane["events"]:
        assert 0 <= event["edit_us"] <= 9_250_000
        # The projection is exactly the placement's affine map, inverted.
        assert proj.music_to_edit(placement, event["music_us"]) == event["edit_us"]


def test_migrated_confidences_are_reported_as_unavailable_not_faked(feature):
    lane = proj.project_music_lane(
        feature, MusicPlacement(feature.track_hash, 0, 0), 5_000_000)
    assert lane["bpm_confidence"] is None
    assert lane["beat_confidence"] is None


def test_bar_grid_keeps_its_estimate_suffix(feature):
    kinds = {e["kind"] for e in proj.music_events(feature)}
    assert "BAR_GRID_ESTIMATE" in kinds or not feature.bar_grid_estimate_us
    assert "DOWNBEAT" not in kinds
    assert all(not k.startswith("DOWNBEAT") for k in kinds)


def test_snapping_is_offered_but_never_applied(feature):
    placement = MusicPlacement(feature.track_hash, 0, 0)
    lane = proj.project_music_lane(feature, placement, 9_000_000)
    targets = proj.snap_targets(lane)
    assert all(t["kind"] in proj.SNAP_TARGET_KINDS for t in targets)
    # The projection is unchanged by asking for snap targets: nothing in the
    # pipeline moves an event onto a grid.
    again = proj.project_music_lane(feature, placement, 9_000_000)
    assert [e["edit_us"] for e in again["events"]] == \
           [e["edit_us"] for e in lane["events"]]


# ===========================================================================
# 4. A/B/C switching changes MusicPlacement and NOTHING else (§38)
# ===========================================================================

def test_abc_switching_touches_only_music_placement(client):
    state = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()
    auditions = state["auditions"]
    if len(auditions) < 2:
        pytest.skip("this scene has fewer than two ranked auditions")
    baseline = state["projection"]
    slots = [a["display_slot"] for a in auditions]
    seen_tracks = set()
    for slot in slots:
        res = client.post(f"/api/scene-editor/{IMPACT_FRAG}/music/select",
                          json={"display_slot": slot})
        assert res.status_code == 200
        after = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()["projection"]
        # Gameplay side: byte-identical.
        assert after["lanes"][proj.LANE_TIME] == baseline["lanes"][proj.LANE_TIME]
        assert after["lanes"][proj.LANE_GAME_EVENTS] == \
            baseline["lanes"][proj.LANE_GAME_EVENTS]
        assert after["lanes"][proj.LANE_CAMERA] == baseline["lanes"][proj.LANE_CAMERA]
        assert after["lanes"][proj.LANE_FX] == baseline["lanes"][proj.LANE_FX]
        assert after["lanes"][proj.LANE_LOOK] == baseline["lanes"][proj.LANE_LOOK]
        assert after["demo"] == baseline["demo"]
        assert after["duration_us"] == baseline["duration_us"]
        seen_tracks.add(after["lanes"][proj.LANE_MUSIC_WAVEFORM]["track_hash"])
    assert len(seen_tracks) > 1, "A/B/C must actually change the music"


def test_placement_swap_leaves_the_time_map_identical_in_the_pure_layer():
    """The property, proven without the API in the way."""
    base = projection(IMPACT_FRAG)
    moved = projection(IMPACT_FRAG,
                       placement=MusicPlacement("b" * 64, 1_000_000, 0))
    assert moved["lanes"][proj.LANE_TIME] == base["lanes"][proj.LANE_TIME]
    assert moved["lanes"][proj.LANE_GAME_EVENTS] == base["lanes"][proj.LANE_GAME_EVENTS]


# ===========================================================================
# 5. review identity is never a letter (§39)
# ===========================================================================

def test_review_identity_is_scene_track_region_matcher(client):
    rows = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()["auditions"]
    if not rows:
        pytest.skip("no auditions on disk")
    for row in rows:
        identity = row["review_identity"]
        parts = identity.split(":")
        assert len(parts) == 5
        assert int(parts[0]) == IMPACT_FRAG
        assert parts[1] == row["track_hash"]
        assert int(parts[2]) == row["region_start_us"]
        assert parts[4] == row["matcher_version"]
        # The display letter must not appear as a component of identity.
        assert row["display_slot"] not in parts


def test_review_identity_is_stable_under_reordering():
    a = proj.review_identity(frag_id=1, track_hash="f" * 64, region_start_us=7,
                             scene_recipe_id="abc", matcher_version="m@2")
    b = proj.review_identity(frag_id=1, track_hash="f" * 64, region_start_us=7,
                             scene_recipe_id="abc", matcher_version="m@2")
    assert a == b


def test_reason_tags_attach_to_the_identity_not_the_slot(client):
    rows = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()["auditions"]
    if not rows:
        pytest.skip("no auditions on disk")
    identity = rows[0]["review_identity"]
    res = client.put(f"/api/scene-editor/{IMPACT_FRAG}/reason-tags",
                     json={"review_identity": identity,
                           "tags": ["GREAT_IMPACT", "TOO_BUSY"]})
    assert res.status_code == 200
    assert res.json()["tags"] == ["GREAT_IMPACT", "TOO_BUSY"]
    again = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()["auditions"]
    tagged = next(r for r in again if r["review_identity"] == identity)
    assert set(tagged["reason_tags"]) == {"GREAT_IMPACT", "TOO_BUSY"}
    # Clean up so a rerun starts from the same place.
    client.put(f"/api/scene-editor/{IMPACT_FRAG}/reason-tags",
               json={"review_identity": identity, "tags": []})


def test_reason_tags_reject_vocabulary_outside_the_list(client):
    rows = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()["auditions"]
    if not rows:
        pytest.skip("no auditions on disk")
    res = client.put(f"/api/scene-editor/{IMPACT_FRAG}/reason-tags",
                     json={"review_identity": rows[0]["review_identity"],
                           "tags": ["MADE_UP_TAG"]})
    assert res.status_code == 422


def test_the_existing_review_store_is_reused_not_duplicated(client):
    """LOVE/KEEP/MAYBE/DROP still lives in the /frags review endpoint."""
    res = client.put(f"/api/frags/{IMPACT_FRAG}/review", json={"verdict": "KEEP"})
    assert res.status_code == 200
    assert client.get(f"/api/frags/{IMPACT_FRAG}/review").json()["verdict"] == "KEEP"
    # And the Scene Editor router defines NO competing verdict endpoint —
    # its only review-adjacent route stores reason tags, which answer "why",
    # not "how good".
    paths = {getattr(r, "path", "") for r in create_app().routes}
    editor_paths = {p for p in paths if p.startswith("/api/scene-editor")}
    assert not [p for p in editor_paths if p.endswith("/review")]
    assert "/api/scene-editor/{frag_id}/reason-tags" in editor_paths
    # The tags table is keyed on the music review identity, not on frag_id,
    # so it cannot shadow editorial_reviews even by accident.
    assert "review_identity" in api._TAG_SCHEMA and "verdict" not in api._TAG_SCHEMA


# ===========================================================================
# 6. recommended vs overridden placement (§6)
# ===========================================================================

def test_recommended_and_override_are_both_kept(client):
    draft = client.get(f"/api/scene-editor/{IMPACT_FRAG}/draft").json()
    if not draft["music_placement"]:
        pytest.skip("no recommended placement for this scene")
    assert draft["music_placement_source"] == "RECOMMENDED"
    recommended = copy.deepcopy(draft["music_placement_recommended"])
    moved = dict(draft["music_placement"])
    moved["source_start_us"] += 250_000
    after = client.put(f"/api/scene-editor/{IMPACT_FRAG}/music/placement",
                       json={"placement": moved}).json()
    assert after["music_placement_source"] == "USER_OVERRIDDEN"
    assert after["music_placement_recommended"] == recommended
    assert after["music_placement"]["source_start_us"] == moved["source_start_us"]
    # Returning to the matcher's numbers flips the flag back — the override
    # is a fact about the values, not a sticky mode.
    back = client.put(f"/api/scene-editor/{IMPACT_FRAG}/music/placement",
                      json={"placement": recommended}).json()
    assert back["music_placement_source"] == "RECOMMENDED"


def test_moving_music_never_moves_gameplay(client):
    before = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()["projection"]
    placement = dict(before["recipe"]["music"] or {})
    if not placement:
        pytest.skip("no placement to move")
    placement["source_start_us"] += 1_500_000
    client.put(f"/api/scene-editor/{IMPACT_FRAG}/music/placement",
               json={"placement": placement})
    after = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()["projection"]
    assert after["lanes"][proj.LANE_TIME] == before["lanes"][proj.LANE_TIME]
    assert after["lanes"][proj.LANE_GAME_EVENTS] == before["lanes"][proj.LANE_GAME_EVENTS]
    # ...and the music genuinely did move.
    assert after["lanes"][proj.LANE_MUSIC_WAVEFORM]["window_music_start_us"] == \
        before["lanes"][proj.LANE_MUSIC_WAVEFORM]["window_music_start_us"] + 1_500_000


# ===========================================================================
# 7. camera + FX projection
# ===========================================================================

def test_camera_stages_resolve_semantically_onto_edit_time():
    p = projection(IMPACT_FRAG)
    stages = p["lanes"][proj.LANE_CAMERA]["stages"]
    assert stages, "the default intent must produce drawable stages"
    anchor_ids = {a["anchor_id"] for a in p["anchors"]}
    for stage in stages:
        assert stage["resolved"] is True
        assert stage["start_anchor"] in anchor_ids
        assert stage["end_anchor"] in anchor_ids
        assert stage["edit_end_us"] > stage["edit_start_us"]


def test_camera_lane_never_leaks_the_compiled_backend():
    """`.cam10` is an execution artifact; the workspace must not name it."""
    payload = repr(projection(IMPACT_FRAG))
    assert "cam10" not in payload.lower()
    source = (proj.__file__, api.__file__)
    for path in source:
        with open(path, "r", encoding="utf-8") as handle:
            body = handle.read()
        # It may be *discussed* in a docstring, but never emitted to the UI.
        assert "\"cam10" not in body and "'cam10" not in body


def test_fx_cue_projects_through_the_time_map_not_around_it():
    from creative_suite.engine.pantheon_scene import FxCue
    cue = FxCue(effect_type="IMPACT_ACCENT", semantic_anchor="impact-0",
                offset_us=-600_000, duration_us=400_000,
                intensity_level="HERO", parameters={"fx_name": "impact"})
    p = projection(IMPACT_FRAG, fx_cues=(cue,))
    row = p["lanes"][proj.LANE_FX]["cues"][0]
    assert row["resolved"] is True
    assert row["demo_start_us"] == IMPACT_DEMO_US - 600_000
    # The cue starts inside the 1/2-rate segment, so 400 ms of engine time
    # draws WIDER than 400 ms on the edit timeline. That is the point.
    assert row["edit_end_us"] - row["edit_start_us"] > cue.duration_us


def test_fx_intensity_off_is_a_real_level_not_an_absence():
    from creative_suite.engine.pantheon_scene import FxCue
    cue = FxCue(effect_type="GHOST_TRAIL", semantic_anchor="frag-0",
                duration_us=200_000, intensity_level="OFF",
                parameters={"fx_name": "ghost"})
    row = projection(IMPACT_FRAG, fx_cues=(cue,))["lanes"][proj.LANE_FX]["cues"]
    assert len(row) == 1 and row[0]["intensity_level"] == "OFF"


# ===========================================================================
# 8. save / reload and the UI-state exclusion (§52)
# ===========================================================================

def test_ui_state_is_excluded_from_both_hashes(client):
    before = client.get(f"/api/scene-editor/{IMPACT_FRAG}/draft").json()
    patch = {"zoom": 7.5, "scroll_us": 1_234_567,
             "expanded_lanes": ["TIME"], "panel_widths": {"inspector": 999},
             "hidden_event_kinds": [], "snap_enabled": True,
             "selected_lane": "FX", "selected_item_id": "frag-0",
             "playhead_us": 3_000_000}
    after = client.put(f"/api/scene-editor/{IMPACT_FRAG}/draft", json=patch).json()
    assert after["recipe_id"] == before["recipe_id"]
    assert after["scene_id"] == before["scene_id"]
    # ...and it did not dirty the draft either.
    assert after["status"] == before["status"] == "CLEAN"
    assert after["zoom"] == 7.5 and after["snap_enabled"] is True


def test_recipe_state_does_move_the_hash(client):
    before = client.get(f"/api/scene-editor/{IMPACT_FRAG}/draft").json()
    after = client.put(f"/api/scene-editor/{IMPACT_FRAG}/draft",
                       json={"visual_look": "PANTHEON"}).json()
    # Look is PRODUCTION state: it moves scene_id, and deliberately leaves
    # recipe_id alone — a re-light does not re-identify the moment.
    assert after["scene_id"] != before["scene_id"]
    assert after["recipe_id"] == before["recipe_id"]
    assert after["status"] == "UNSAVED"

    moved = dict(after["music_placement"] or {})
    if moved:
        moved["source_start_us"] += 111_000
        with_music = client.put(f"/api/scene-editor/{IMPACT_FRAG}/draft",
                                json={"music_placement": moved}).json()
        assert with_music["recipe_id"] != after["recipe_id"]


def test_a_partial_recipe_patch_is_normalized_not_stored_raw(client):
    """Regression: a partial patch must never leave the draft unusable.

    ``PUT {"camera_intent": {"mode": "ORBIT"}}`` is a perfectly reasonable
    request. Storing that body verbatim left the draft without ``stages``,
    and the very next hash computation raised KeyError — a 500 for a valid
    request.
    """
    after = client.put(f"/api/scene-editor/{IMPACT_FRAG}/draft",
                       json={"camera_intent": {"mode": "ORBIT"}})
    assert after.status_code == 200
    draft = after.json()
    assert draft["camera_intent"]["mode"] == "ORBIT"
    assert set(draft["camera_intent"]) == {"mode", "stages", "subject_anchor",
                                           "params"}
    # And the draft still round-trips through every derived value.
    assert client.get(f"/api/scene-editor/{IMPACT_FRAG}").status_code == 200
    assert client.post(f"/api/scene-editor/{IMPACT_FRAG}/draft/undo").status_code == 200


@pytest.mark.parametrize("patch", [
    {"camera_intent": "ORBIT"},
    {"camera_intent": {"mode": "ORBIT", "stages": [{"stage": "NOT_A_STAGE"}]}},
    {"transition": "fade"},
    {"transition": 5},
    {"time_map": "not a list"},
    {"time_map": [{"kind": "normal"}]},
    {"fx_stack": {"not": "a list"}},
    {"music_placement": {"track_id": "x", "source_start_us": None}},
    {"visual_look": "NEON"},
])
def test_malformed_recipe_patches_are_rejected_cleanly(client, patch):
    """Every bad body is a 422 with a reason — never an unhandled 500."""
    res = client.put(f"/api/scene-editor/{IMPACT_FRAG}/draft", json=patch)
    assert res.status_code == 422, (patch, res.status_code)
    assert res.json()["detail"]
    # The draft is untouched, so a rejected patch cannot half-apply.
    assert client.get(f"/api/scene-editor/{IMPACT_FRAG}/draft").status_code == 200


def test_a_placement_outside_the_track_is_refused(client):
    """Dragging far enough left produced a negative source start — a scene
    that opens on audio which does not exist. The schema accepts any int, so
    the bound has to live here."""
    state = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()
    placement = state["projection"]["recipe"]["music"]
    if not placement:
        pytest.skip("no placement to move")
    track_us = state["projection"]["lanes"][proj.LANE_MUSIC_WAVEFORM]["track_duration_us"]

    before = client.get(f"/api/scene-editor/{IMPACT_FRAG}/draft").json()
    too_early = dict(placement, source_start_us=-1)
    res = client.put(f"/api/scene-editor/{IMPACT_FRAG}/music/placement",
                     json={"placement": too_early})
    assert res.status_code == 422 and "outside the track" in res.json()["detail"]

    too_late = dict(placement, source_start_us=track_us - 1000)
    assert client.put(f"/api/scene-editor/{IMPACT_FRAG}/music/placement",
                      json={"placement": too_late}).status_code == 422

    # A legal move is still accepted, and the rejected ones left no trace.
    after = client.get(f"/api/scene-editor/{IMPACT_FRAG}/draft").json()
    assert after["music_placement"] == before["music_placement"]
    legal = dict(placement, source_start_us=placement["source_start_us"] + 1000)
    assert client.put(f"/api/scene-editor/{IMPACT_FRAG}/music/placement",
                      json={"placement": legal}).status_code == 200


def test_a_null_placement_field_is_refused(client):
    res = client.put(f"/api/scene-editor/{IMPACT_FRAG}/music/placement",
                     json={"placement": {"track_id": "a" * 64,
                                         "source_start_us": None}})
    assert res.status_code == 422


def test_the_state_partition_is_disjoint_and_complete():
    assert not set(proj.RECIPE_STATE_KEYS) & set(proj.UI_STATE_KEYS)
    draft = api._default_draft(IMPACT_FRAG)
    for key in proj.RECIPE_STATE_KEYS + proj.UI_STATE_KEYS:
        assert key in draft, f"draft is missing declared key {key}"


def test_save_then_reload_reproduces_the_same_recipe_hash(client, tmp_path):
    api.SCENE_RECIPE_DB_PATH = tmp_path / "scene_recipes.db"
    api.CINEMATIC_DB_PATH = tmp_path / "cinematic.db"
    try:
        client.put(f"/api/scene-editor/{IMPACT_FRAG}/draft",
                   json={"visual_look": "UHD"})
        saved = client.post(f"/api/scene-editor/{IMPACT_FRAG}/draft/save").json()
        assert saved["status"] == "CLEAN"
        assert saved["saved_recipe_id"] == saved["recipe_id"]
        assert saved["saved_scene_id"] == saved["scene_id"]

        from creative_suite.engine.scene_recipe import load_scene_recipe
        reloaded = load_scene_recipe(saved["recipe_id"], api.SCENE_RECIPE_DB_PATH)
        assert reloaded is not None
        assert reloaded.recipe_id == saved["recipe_id"]

        from creative_suite.engine.pantheon_scene import load_scene
        scene = load_scene(saved["scene_id"], api.CINEMATIC_DB_PATH)
        assert scene is not None and scene.scene_id == saved["scene_id"]
        assert scene.visual_look == "UHD"
        assert scene.recipe_id == saved["recipe_id"]

        resolved = client.get(
            f"/api/scene-editor/resolve/recipe-{saved['recipe_id']}").json()
        assert resolved["frag_id"] == IMPACT_FRAG
    finally:
        api.SCENE_RECIPE_DB_PATH = api._DB_DIR / "cinematic.db"
        api.CINEMATIC_DB_PATH = None


def test_undo_restores_recipe_state_and_leaves_ui_state_alone(client):
    client.put(f"/api/scene-editor/{IMPACT_FRAG}/draft", json={"zoom": 4.0})
    before = client.get(f"/api/scene-editor/{IMPACT_FRAG}/draft").json()
    client.put(f"/api/scene-editor/{IMPACT_FRAG}/draft",
               json={"visual_look": "PANTHEON"})
    undone = client.post(f"/api/scene-editor/{IMPACT_FRAG}/draft/undo").json()
    assert undone["visual_look"] == before["visual_look"]
    assert undone["scene_id"] == before["scene_id"]
    assert undone["zoom"] == 4.0, "undo must not roll back the workspace view"


def test_preview_never_auto_saves(client):
    """§53 — nothing in this router persists except SAVE RECIPE."""
    routes = [r for r in create_app().routes
              if getattr(r, "path", "").startswith("/api/scene-editor")]
    persisting = {"/api/scene-editor/{frag_id}/draft/save",
                  "/api/scene-editor/{frag_id}/reason-tags"}
    for route in routes:
        methods = getattr(route, "methods", set())
        if methods & {"POST", "PUT", "DELETE"}:
            assert route.path in persisting or "draft" in route.path or \
                "music" in route.path, route.path


# ===========================================================================
# 9. the three scenes are materially different
# ===========================================================================

def test_the_three_scenes_produce_materially_different_timelines():
    shapes = {}
    for frag_id in ALL_FRAGS:
        p = projection(frag_id)
        counts: dict[str, int] = {}
        for event in p["lanes"][proj.LANE_GAME_EVENTS]["events"]:
            counts[event["kind"]] = counts.get(event["kind"], 0) + 1
        shapes[frag_id] = (p["duration_us"], counts)
    assert len({s[0] for s in shapes.values()}) == 3, "all three lengths differ"
    assert shapes[IMPACT_FRAG][1] != shapes[TRACKING_FRAG][1]
    assert shapes[TRACKING_FRAG][1] != shapes[CLUTCH_FRAG][1]


def test_tracking_scene_reads_as_rhythm_not_as_a_projectile_scene():
    counts: dict[str, int] = {}
    p = projection(TRACKING_FRAG)
    for event in p["lanes"][proj.LANE_GAME_EVENTS]["events"]:
        counts[event["kind"]] = counts.get(event["kind"], 0) + 1
    assert counts.get("LG_CONTACT") == 20
    assert counts.get("LG_BURST") == 8
    assert "PROJECTILE_LAUNCH" not in counts
    assert "PROJECTILE_IMPACT" not in counts
    for event in p["lanes"][proj.LANE_GAME_EVENTS]["events"]:
        if event["kind"] == "LG_BURST":
            assert event["edit_end_us"] >= event["edit_us"]


def test_micro_events_are_hidden_by_default_so_the_lane_stays_readable():
    kinds = {k["kind"]: k for k in
             projection(TRACKING_FRAG)["lanes"][proj.LANE_GAME_EVENTS]["kinds"]}
    assert kinds["LG_CONTACT"]["hidden_by_default"] is True
    assert kinds["LG_BURST"]["hidden_by_default"] is False
    default_hidden = api._default_draft(TRACKING_FRAG)["hidden_event_kinds"]
    assert "LG_CONTACT" in default_hidden


def test_clutch_scene_shows_its_frag_progression():
    p = projection(CLUTCH_FRAG)
    frags = [e for e in p["lanes"][proj.LANE_GAME_EVENTS]["events"]
             if e["kind"] == "FRAG"]
    assert len(frags) >= 3, "the clutch is a progression, not a single kill"
    assert frags == sorted(frags, key=lambda e: e["edit_us"])
    multikill = [e for e in p["lanes"][proj.LANE_GAME_EVENTS]["events"]
                 if e["kind"] == "MULTIKILL"]
    assert multikill and multikill[0]["edit_end_us"] > multikill[0]["edit_us"]


def test_each_scene_gets_the_profile_its_evidence_implies(client):
    expected = {IMPACT_FRAG: "IMPACT_PROJECTILE",
                TRACKING_FRAG: "RHYTHMIC_TRACKING",
                CLUTCH_FRAG: "TENSION_RELEASE"}
    for frag_id, profile_type in expected.items():
        why = client.get(f"/api/scene-editor/{frag_id}").json()["why_this_matches"]
        if not why["available"]:
            pytest.skip(f"no ranked auditions for {frag_id}")
        assert why["profile_type"] == profile_type


# ===========================================================================
# 10. §33 — the backend is the only authority on scores
# ===========================================================================

def test_component_scores_are_passed_through_verbatim(client):
    import json
    manifest = json.loads(
        (api.MUSIC_AUDITION_DIR / "manifest.json").read_text(encoding="utf-8"))
    rows = {(x["frag_id"], x["audition_id"]): x for x in manifest["items"]}
    served = client.get(f"/api/scene-editor/{IMPACT_FRAG}").json()["auditions"]
    for row in served:
        source = rows[(IMPACT_FRAG, row["display_slot"])]
        assert row["components"] == source["components"]
        assert row["score"] == source["score"]
        assert row["matcher_version"] == source["matcher_version"]


def test_headline_components_differ_per_profile(client):
    seen = {}
    for frag_id in ALL_FRAGS:
        why = client.get(f"/api/scene-editor/{frag_id}").json()["why_this_matches"]
        if why["available"]:
            seen[why["profile_type"]] = tuple(why["headline_components"])
    assert len(set(seen.values())) == len(seen) > 1


# ===========================================================================
# 11. guides (§34)
# ===========================================================================

def test_guides_carry_signed_deltas_and_stay_few(client):
    for frag_id in ALL_FRAGS:
        guides = client.get(f"/api/scene-editor/{frag_id}").json()["projection"]["guides"]
        assert guides, f"frag {frag_id} produced no guides at all"
        assert len(guides) <= proj.MAX_GUIDES
        for guide in guides:
            assert guide["delta_us"] == \
                guide["game_edit_us"] - guide["music_edit_us"]
            assert (guide["game_kind"], guide["music_kind"]) in proj.GUIDE_PAIRS


def test_lg_scene_guides_use_bursts_not_every_contact(client):
    # Guides need a placed track, so go through the API, which seeds the
    # draft with the matcher's own recommendation.
    p = client.get(f"/api/scene-editor/{TRACKING_FRAG}").json()["projection"]
    guides = p["guides"]
    assert guides, "an LG scene should still get guides"
    assert all(g["game_kind"] != "LG_CONTACT" for g in guides)
    assert any(g["game_kind"] == "LG_BURST" for g in guides)
    # 20 contacts must not become 20 lines.
    assert len(guides) <= proj.MAX_GUIDES


# ===========================================================================
# 12. routes and page wiring
# ===========================================================================

def test_scene_editor_page_and_assets_are_served(client):
    assert client.get("/scene-editor/frag-5979").status_code == 200
    body = client.get("/static/scene-editor.js").text
    assert "MusicPlacement" in body
    assert ".innerHTML" not in body, "UI-1: no innerHTML anywhere"


def test_frags_page_offers_open_in_editor():
    from pathlib import Path
    js = Path(__file__).parents[1] / "frontend" / "frags.js"
    body = js.read_text(encoding="utf-8")
    assert "OPEN IN EDITOR" in body
    assert "/scene-editor/frag-" in body


def test_schema_declares_the_honest_confidence_story(client):
    schema = client.get("/api/scene-editor/schema").json()
    assert schema["confidence_availability"]["bpm_confidence"] == \
        "UNAVAILABLE_FOR_MIGRATED_TRACKS"
    assert "BAR_GRID_ESTIMATE" in schema["music_event_kinds"]
    assert "DOWNBEAT" not in schema["music_event_kinds"]
    assert set(schema["state_partition"]["recipe"]) == set(proj.RECIPE_STATE_KEYS)


def test_unknown_frag_is_a_404(client):
    assert client.get("/api/scene-editor/99999999").status_code == 404
