"""The annotation is production input, not incidental metadata.

"freeze before impact, xray wall, enemy POV after" is a shot already
designed, written at the only moment the person had it in mind. These tests
protect the words themselves.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from creative_suite.engine import creative_annotation as ca   # noqa: E402
from creative_suite.engine import media_provenance as mp      # noqa: E402

NOTE = ("freeze just before rocket connects, remove wall/xray, "
        "enemy POV for impact, slow second view")


def test_the_raw_wording_is_returned_untouched():
    """Never summarised, never normalised, never replaced by what a parser
    thought it meant."""
    out = ca.parse_intent(NOTE)
    assert out["human_annotation_raw"] == NOTE
    assert out["provenance"] == ca.AI_SUGGESTION


def test_intent_is_read_from_the_directors_own_words():
    got = ca.parse_intent(NOTE)["suggested_intent"]
    assert "XRAY" in got[ca.EFFECT_INTENT]
    assert set(got[ca.TIMING_INTENT]) >= {"FREEZE", "SLOW_MOTION"}
    assert "ENEMY_POV" in got[ca.CAMERA_INTENT]
    assert "SECOND_VIEW" in got[ca.REPLAY_INTENT]


def test_a_round_note_is_read_as_a_round_note():
    got = ca.parse_intent(
        "whole round - top map, 4v4 count, pTn morph, ClanWar"
    )["suggested_intent"]
    assert "FULL_ROUND" in got[ca.ROUND_INTENT]
    assert "CLANWAR" in got[ca.ROUND_INTENT]
    assert "TOP_MAP" in got[ca.CAMERA_INTENT]
    assert "PTN_MORPH" in got[ca.EFFECT_INTENT]


def test_an_unparseable_note_loses_nothing():
    """A shallow reader that is obviously incomplete beats a clever one that
    quietly decides it understood. Unmatched words stay searchable."""
    odd = "make it feel like the corridor is breathing"
    out = ca.parse_intent(odd)
    assert out["suggested_intent"] == {}
    assert out["human_annotation_raw"] == odd


def test_intent_never_claims_to_be_human_truth():
    assert ca.parse_intent(NOTE)["provenance"] != ca.HUMAN_USER
    assert "suggestion" in ca.status()["rule"]


def test_the_vocabulary_is_a_suggestion_not_a_closed_set():
    assert "XRAY" in ca.VOCABULARY and "GRENADE_DOUBLE_VIEW" in ca.VOCABULARY
    # A term outside the list is still detected from plain language.
    assert ca.parse_intent("rocket cam please")["suggested_intent"]
    assert ca.vocabulary_hits("use GRENADE_DOUBLE_VIEW then clean fpv") == \
        ["GRENADE_DOUBLE_VIEW", "CLEAN_FPV"]


def test_a_request_for_something_that_does_not_exist_is_still_kept():
    """The toolkit lacking a route is a fact about the toolkit, not about
    the idea."""
    assert ca.CREATIVE_REQUEST_EXISTS and ca.IMPLEMENTATION_ROUTE_UNKNOWN
    weird = "xray the wall then enemy POV through the floor"
    assert ca.parse_intent(weird)["human_annotation_raw"] == weird


def test_moment_and_round_notes_are_separate_objects():
    key = ca.round_key("hash_test_only", 7)
    ca.set_round_annotation("hash_test_only", 7,
                            "ClanWar story - top map opening",
                            provenance=ca.TEST)
    got = ca.get_round_annotation("hash_test_only", 7)
    assert got["annotation"] == "ClanWar story - top map opening"
    assert got["round"] == 7 and got["round_key"] == key
    with ca.conn() as c:
        c.execute("DELETE FROM round_annotations WHERE round_key=?", (key,))


def test_search_only_returns_human_words():
    """A TEST row must never surface as the director's intent."""
    out = ca.search("xray")
    assert set(out) >= {"query", "moments", "rounds", "total"}
    for m in out["moments"]:
        assert m["provenance"] in ("HUMAN_USER", "IMPORTED_LEGACY_HUMAN")


def test_search_refuses_an_unknown_role():
    with pytest.raises(ValueError, match="unknown role"):
        ca.search("xray", role="T9_NONSENSE")


# ── media provenance of the phone copy ──────────────────────────────────────

def test_the_delivery_derivative_is_not_master_grade():
    """A lossy 720p copy for looking at must never be mistaken for the
    master when something later wants the best available pixels."""
    assert mp.V2_REVIEW_DELIVERY_DERIVATIVE in mp.AUTHORITATIVE
    assert mp.V2_REVIEW_DELIVERY_DERIVATIVE not in mp.MASTER_GRADE
    assert mp.RAW_DEMO_CAPTURE in mp.MASTER_GRADE


def test_the_page_offers_suggestions_without_adding_buttons():
    s = (Path(__file__).resolve().parents[1] / "frontend" / "review.html"
         ).read_text(encoding="utf-8")
    assert 'list="vocab"' in s and '<datalist id="vocab">' in s
    assert 'id="rnote"' in s, "the round gets its own note"
    # Still exactly five verdict controls.
    assert s.count("data-role=") == 5
