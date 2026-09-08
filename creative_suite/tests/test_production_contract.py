"""What the planning layer is allowed to believe, and from whom.

These tests pin the boundary between the reviewer and the film. Every one of
them exists because the opposite behaviour would put a confident falsehood on
screen: a health bar over a moment nobody measured, an accuracy number the
pain stream cannot support, a cameraman's stack shown as the actor's, or --
worst -- the director's own words tidied up on the way to the planner.

Nothing here writes a HUMAN_USER review. The annotations under test are
constructed in memory; the three genuine reviews in the live database are
never read, written or counted by this file.
"""
from __future__ import annotations

import pytest

from creative_suite.engine import production_contract as pc
from creative_suite.engine import scene as sc


# ── fixtures: a scene with a rail, built in memory ──────────────────────────

def _event(event_id, kind, t_ms, offset_ms, label, **kw):
    # A note on a fixture event needs a provenance, exactly as one loaded
    # from storage does. The production boundary drops any note that cannot
    # say who wrote it -- an unattributed string is not the director
    # speaking, and defaulting it to HUMAN here would let these tests pass
    # while production silently dropped every real note.
    if kw.get("annotation") and "annotation_provenance" not in kw:
        kw["annotation_provenance"] = "IMPORTED_LEGACY_HUMAN"
    return sc.SceneEvent(event_id=event_id, kind=kind, t_ms=t_ms,
                         offset_ms=offset_ms, label=label, **kw)


def _scene(events=(), round_no=7):
    return sc.Scene(
        scene_id="SCENE:deadbeef:7", mode=sc.MODE_SCENE,
        content_hash="deadbeef" * 8, round_no=round_no, map_name="asylum",
        start_ms=10_000, end_ms=40_000,
        media_start_ms=7_000, media_end_ms=43_000,
        user_frags=4, total_kills=6, events=list(events),
        reason="4 user frags")


def _four_frag_scene():
    """The example from the brief: F1 F2 JUMP PAD F3 F4."""
    return _scene([
        _event("OCC:101", sc.E_FRAG, 11_000, 1_000, "F1 RAIL",
               occurrence_id=101, is_user=True, frag_index=1),
        _event("OCC:102", sc.E_FRAG, 16_000, 6_000, "F2 ROCKET",
               occurrence_id=102, is_user=True, frag_index=2),
        _event("MOV:55", sc.E_JUMPPAD, 21_000, 11_000, "JUMP PAD · 640 UPS",
               peak_speed=640.0,
               annotation="music buildup here"),
        _event("OCC:103", sc.E_FRAG, 26_000, 16_000, "F3 LG",
               occurrence_id=103, is_user=True, frag_index=3,
               annotation="xray / enemy POV"),
        _event("OCC:104", sc.E_FRAG, 31_000, 21_000, "F4 ROCKET",
               occurrence_id=104, is_user=True, frag_index=4),
    ])


def _truth(item_id="FRAG:101", occurrence_id=101, *, pov=True,
           stack=None, action=None, traits=("AIR_ROCKET",)):
    return {
        "item_id": item_id,
        "available": True,
        "event": {"occurrence_id": occurrence_id, "actor": "tr4sh",
                  "opponent": "someone", "weapon": "ROCKET", "map": "asylum",
                  "round": 7, "is_actor_pov": pov,
                  "camera": "ACTOR OWN POV" if pov else "OBSERVED",
                  "machine_score": 25.0, "career_rank": 12,
                  "career_total": 33_316, "death_cause": "KILLED",
                  "n_observations": 1, "time_in_round_ms": 1_000,
                  "machine_score_version": "recognition-v4"},
        "usage": {"state": "AVAILABLE", "detail": ""},
        "stack": stack if stack is not None else {"available": False},
        "action": action or {"weapon": "ROCKET_LAUNCHER", "shots": 4,
                             "hits_confirmed": 1, "hits_ambiguous": 2,
                             "accuracy_pct": 25.0, "accuracy_upper_pct": 75.0,
                             "confidence": "AMBIGUOUS", "unit": "shots",
                             "note": ""},
        "damage": {"available": False, "lg_dealt_3s": None,
                   "taken_in_fight": None, "lowest_health_in_fight": None,
                   "scope": "lightning-gun engagements only"},
        "geometry": {"distance_units": 311.9, "flick_deg_per_s": 81.6,
                     "target_visible_ms": 11_375},
        "movement": {"speed_at_frag": 384.7, "victim_speed": 734.3,
                     "victim_air_height": 84.0},
        "round": {"round_no": 7, "user_kills": 4, "user_died": False,
                  "alive_curve": [], "alive_provenance": "DERIVED"},
        "timing": {"available": True, "frag_index": 1, "frags_in_scene": 4,
                   "ms_to_next_user_frag": 5_000,
                   "scene_duration_ms": 36_000},
        "scene": {"scene_id": "SCENE:deadbeef:7", "mode": sc.MODE_SCENE,
                  "media_start_ms": 7_000, "media_end_ms": 43_000,
                  "user_frags": 4, "total_kills": 6},
        "traits": list(traits),
    }


# ── the classification itself ───────────────────────────────────────────────

def test_every_planner_field_is_classified():
    """A field a planner can read must have a decided trust level.

    The table is the decision. If PLANNER_FIELDS grows and the table does
    not, this fails here rather than in a film six months later.
    """
    for path in pc.PLANNER_FIELDS:
        assert pc.classify(path) in pc.CLASSES


def test_an_unclassified_field_is_refused_not_guessed():
    with pytest.raises(pc.UnclassifiedField):
        pc.classify("event.something_nobody_decided_about")


def test_the_machine_score_is_never_factual():
    """It is an opinion on its own unbounded scale.

    It may order the queue. It may not be the reason the film says a thing
    happened, and `is_factual` is how a planner asks.
    """
    t = _truth()
    assert pc.provenance_of(t, "event.machine_score") == pc.MACHINE_SUGGESTION
    assert not pc.is_factual(t, "event.machine_score")
    assert not pc.is_factual(t, "traits")
    assert pc.is_factual(t, "event.weapon")


def test_the_alive_curve_is_derived_and_says_so():
    """Team size minus observed deaths, not a count of living players."""
    assert pc.classify("round.alive_curve") == pc.DERIVED
    assert pc.classify("round.user_kills") == pc.OBSERVED


# ── UNKNOWN stays UNKNOWN ───────────────────────────────────────────────────

def test_unknown_health_is_unavailable_and_never_zero():
    """50.6% of this corpus has no playerstate at the moment of the frag.

    The wrong answer is 0, which reads as "died with nothing left" and is a
    statement the demo never made.
    """
    t = _truth(stack={"available": False,
                      "reason": "no playerstate at that moment"})
    ref = pc.action_truth_ref(t)
    assert ref.get("stack.at_frag.health") is None
    assert ref.provenance["stack.at_frag.health"] == pc.UNAVAILABLE
    assert not ref.factual("stack.at_frag.health")
    # and it did not become a zero anywhere on the way through
    assert 0 not in (ref.get("stack.at_frag.health"),
                     ref.get("stack.at_frag.armor"))


def test_observed_health_is_observed():
    t = _truth(stack={"available": True, "at_frag": {"health": 156,
                                                     "armor": 14},
                      "min": {"health": 156, "armor": 14},
                      "provenance": "OBSERVED — recorder playerstate"})
    ref = pc.action_truth_ref(t)
    assert ref.get("stack.at_frag.health") == 156
    assert ref.provenance["stack.at_frag.health"] == pc.OBSERVED
    assert ref.factual("stack.at_frag.health")


def test_foreign_camera_health_never_becomes_actor_health():
    """On an observed frag the health in the demo is the CAMERAMAN's.

    `action_truth._stack` withholds it entirely rather than labelling it, and
    the contract must not resurrect it from anywhere else.
    """
    t = _truth(pov=False, stack={
        "available": False,
        "reason": "health belongs to whoever held the camera, and that was "
                  "not the actor"})
    ref = pc.action_truth_ref(t)
    assert ref.is_actor_pov is False
    for path in ("stack.at_frag.health", "stack.at_frag.armor",
                 "stack.min.health"):
        assert ref.get(path) is None
        assert ref.provenance[path] == pc.UNAVAILABLE


def test_lg_pain_cannot_become_action_accuracy():
    """Pain events are throttled -- median gap 925 ms, never under 100 ms.

    A weapon firing every 50 ms cannot have its hits counted by that signal,
    so `action_stats` returns NOT_DERIVABLE and the contract must carry the
    absence rather than a number.
    """
    from creative_suite.engine import action_stats as ast
    assert 6 in ast.CONTINUOUS            # lightning
    assert 6 not in ast.ATTRIBUTABLE      # and therefore not counted
    t = _truth(action={"weapon": "LIGHTNING", "shots": 23,
                       "hits_confirmed": None, "hits_ambiguous": 0,
                       "accuracy_pct": None, "accuracy_upper_pct": None,
                       "confidence": "UNKNOWN", "unit": "attack ticks",
                       "note": ast.NOT_DERIVABLE})
    ref = pc.action_truth_ref(t)
    assert ref.get("action.accuracy_pct") is None
    assert ref.provenance["action.accuracy_pct"] == pc.UNAVAILABLE
    # the tick count is still honest, and labelled as ticks
    assert ref.get("action.shots") == 23
    assert ref.get("action.unit") == "attack ticks"


# ── Scene references, never copies ──────────────────────────────────────────

def test_scene_carries_occurrence_references_not_copies():
    """One kill, one canonical record.

    A SceneRef event holds an id and a time. It must not carry health, aim,
    damage or score: two copies of a moment eventually disagree, and nobody
    can say which one the film used.
    """
    ref = pc.scene_ref(_four_frag_scene())
    assert ref.occurrence_ids == (101, 102, 103, 104)
    banned = {"health", "armor", "distance", "accuracy", "machine_score",
              "flick_degrees", "speed_at_frag", "damage"}
    for e in ref.events:
        assert not (banned & set(e.to_dict())), \
            f"{e.event_id} duplicates moment data the occurrence already owns"


def test_a_movement_run_never_takes_a_verdict():
    """A jump pad is context, not a frag.

    It is addressable so a note can hang on it, and `takes_verdict` is false
    so it can never enter the review corpus as a rateable moment.
    """
    ref = pc.scene_ref(_four_frag_scene())
    pad = next(e for e in ref.events if e.event_id == "MOV:55")
    assert pad.occurrence_id is None
    assert pad.takes_verdict is False
    assert all(e.takes_verdict for e in ref.events
               if e.occurrence_id is not None)


def test_round_zero_is_not_a_scene():
    """Round 0 is the no-round-system sentinel, not a round.

    Grouping by it once produced a "round" of 105 user frags spanning a whole
    match.
    """
    mode, reason = sc.decide_mode(9, sc.NO_ROUND, ())
    assert mode == sc.MODE_FRAG
    assert reason


# ── the bridge: the director's words survive ────────────────────────────────

def test_human_notes_survive_conversion_verbatim():
    """The example from the brief, end to end.

    JUMP PAD: "music buildup here" · F3: "xray / enemy POV" ·
    ROUND: "big finish on F4."

    Each must arrive at the planning layer as the exact string the director
    typed, attached to the exact event they typed it on. Paraphrasing a note
    turns the director's instruction into somebody else's.
    """
    scene = _four_frag_scene()
    note = {"annotation": "big finish on F4.", "provenance": "HUMAN_USER"}
    ci = pc.choreography_input(scene, [_truth()], note)

    texts = {(n.scope, n.target): n.text for n in ci.direction}
    assert texts[("SCENE", "SCENE:deadbeef:7")] == "big finish on F4."
    assert texts[("EVENT", "MOV:55")] == "music buildup here"
    assert texts[("EVENT", "OCC:103")] == "xray / enemy POV"
    assert len(ci.direction) == 3


def test_notes_are_not_normalised_in_any_way():
    """Whitespace, case, punctuation, slashes and typos all survive.

    A note is an instruction. `parse_intent` may READ it; nothing may
    REWRITE it.
    """
    raw = "  XRAY!! on the 2nd one -- slow it WAY down (like 0.25x)\n"
    scene = _scene([_event("OCC:9", sc.E_FRAG, 12_000, 2_000, "F1",
                           occurrence_id=9, is_user=True, annotation=raw)])
    ci = pc.choreography_input(scene, [])
    assert ci.notes_for("OCC:9")[0].text == raw


def test_a_machine_reading_never_replaces_the_words():
    """`intent` sits alongside the text and is advisory.

    When the parser misreads a note -- and it will -- the wording is still
    there to be re-read by a human.
    """
    scene = _scene([_event("OCC:9", sc.E_FRAG, 12_000, 2_000, "F1",
                           occurrence_id=9, is_user=True,
                           annotation="xray / enemy POV")])
    ci = pc.choreography_input(scene, [])
    n = ci.notes_for("OCC:9")[0]
    assert n.text == "xray / enemy POV"
    assert isinstance(n.intent, dict)      # a reading, in its own field
    assert n.provenance == pc.HUMAN


def test_only_human_provenance_reaches_the_planner_as_direction():
    """An AI suggestion is not direction, and neither is a test fixture.

    ONLY THE USER WRITES HUMAN CREATIVE TRUTH -- a round note carrying any
    other provenance must not arrive at the planning layer as an
    instruction.
    """
    scene = _four_frag_scene()
    for prov in ("AI_SUGGESTION", "TEST", "SYSTEM"):
        ci = pc.choreography_input(
            scene, [], {"annotation": "make it epic", "provenance": prov})
        assert not ci.scene_notes, f"{prov} reached the planner as direction"
    ci = pc.choreography_input(
        scene, [], {"annotation": "make it epic", "provenance": "HUMAN_USER"})
    assert [n.text for n in ci.scene_notes] == ["make it epic"]


def test_the_bridge_keeps_the_three_inputs_apart():
    """Scene, ActionTruth and direction are separate fields, on purpose.

    A planner must be able to tell story context from game truth from what
    the director asked for. Flattening them is how a machine trait ends up
    outranking a human note.
    """
    ci = pc.choreography_input(
        _four_frag_scene(), [_truth()],
        {"annotation": "big finish on F4.", "provenance": "HUMAN_USER"})
    assert isinstance(ci.scene, pc.SceneRef)
    assert all(isinstance(a, pc.ActionTruthRef) for a in ci.actions)
    assert all(isinstance(n, pc.DirectionNote) for n in ci.direction)
    assert ci.action_for(101) is not None
    assert ci.action_for(999) is None
    d = ci.to_dict()
    assert set(d) == {"scene", "actions", "direction", "contract_version"}


def test_the_bridge_does_not_plan():
    """It is a boundary, not a planner.

    The moment this module starts choosing lanes, effects or cameras, the
    thing it was built to keep separable stops being separable.
    """
    import inspect
    src = inspect.getsource(pc)
    for word in ("LANE_", "ChoreographyPlan(", "ChoreographyElement("):
        assert word not in src, f"{word} means this boundary started planning"


def test_an_event_note_with_no_provenance_is_not_direction():
    """An unattributed note cannot be the director speaking.

    `SceneEvent.annotation_provenance` is empty when nothing was written --
    and would also be empty if a future loader forgot to carry it. Both must
    read the same way at this boundary: not direction.
    """
    scene = _scene([_event("MOV:1", sc.E_JUMPPAD, 12_000, 2_000, "PAD",
                           annotation="music buildup here",
                           annotation_provenance="")])
    ci = pc.choreography_input(scene, [])
    assert not ci.direction

    for prov in ("TEST", "AI_SUGGESTION", "SYSTEM"):
        scene = _scene([_event("MOV:1", sc.E_JUMPPAD, 12_000, 2_000, "PAD",
                               annotation="music buildup here",
                               annotation_provenance=prov)])
        assert not pc.choreography_input(scene, []).direction, prov

    scene = _scene([_event("MOV:1", sc.E_JUMPPAD, 12_000, 2_000, "PAD",
                           annotation="music buildup here",
                           annotation_provenance="HUMAN_USER")])
    ci = pc.choreography_input(scene, [])
    assert [n.text for n in ci.direction] == ["music buildup here"]
