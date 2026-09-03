"""The machine organises; the user decides. Nothing is hidden or deleted."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import review_corpus as rc


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    """Every test gets its own editorial db: a review is the user's own
    judgement and a test must never write into it."""
    monkeypatch.setattr(rc, "EDITORIAL_DB", tmp_path / "editorial.db")
    yield


# ── provenance: only the user writes creative truth ─────────────────────────

def test_a_test_cannot_write_a_human_verdict():
    """Automated tests drove the live UI during implementation and wrote rows
    that were indistinguishable from real review. That must stay impossible."""
    it = rc.queue(limit=1)[0]
    rc.record(it.item_id, it.item_type, it.source_id, rc.T1_FEATURE_FX,
              provenance=rc.TEST)
    p = rc.progress()
    assert p["reviewed"] == 0, "a TEST row is not the user's judgement"
    assert p["non_human_rows"] == {rc.TEST: 1}
    assert rc.pool(rc.T1_FEATURE_FX) == [], "and it never reaches a pool"


def test_only_human_provenance_counts_towards_progress():
    a, b = rc.queue(limit=2)
    rc.record(a.item_id, a.item_type, a.source_id, rc.T4_KEEP_NORMAL,
              provenance=rc.HUMAN_USER)
    rc.record(b.item_id, b.item_type, b.source_id, rc.T4_KEEP_NORMAL,
              provenance=rc.AI_SUGGESTION)
    p = rc.progress()
    assert p["reviewed"] == 1
    assert p["roles"][rc.T4_KEEP_NORMAL] == 1
    assert [r["item_id"] for r in rc.pool(rc.T4_KEEP_NORMAL)] == [a.item_id]


def test_an_unknown_provenance_is_refused():
    it = rc.queue(limit=1)[0]
    with pytest.raises(ValueError, match="unknown provenance"):
        rc.record(it.item_id, it.item_type, it.source_id, rc.T4_KEEP_NORMAL,
                  provenance="SOMEONE_ELSE")


# ── telefrags: the constant had to be read, not guessed ─────────────────────

def test_telefrag_uses_the_verified_means_of_death():
    """An earlier query used mod=12 and found nothing. 12 is MOD_BFG; the
    vendored enum puts MOD_TELEFRAG at 18."""
    assert rc.MOD_TELEFRAG == 18
    assert rc.count_items(rc.TELEFRAG) == 194
    q = rc.queue(item_type=rc.TELEFRAG, limit=5)
    assert len(q) == 5
    assert all(i.item_id.startswith("TELEFRAG:") for i in q)
    assert all(i.total_items == 194 for i in q)


def test_a_telefrag_gets_the_same_five_questions():
    it = rc.queue(item_type=rc.TELEFRAG, limit=1)[0]
    rc.record(it.item_id, it.item_type, it.source_id, rc.T2_TRANSITION,
              "telefrags are natural scene joins")
    got = rc.item(it.item_id)
    assert got.item_type == rc.TELEFRAG
    assert got.human_role == rc.T2_TRANSITION
    assert rc.progress(rc.TELEFRAG)["total"] == 194


# ── corpora: what is available, and why the rest is not ─────────────────────

def test_my_frags_is_available_and_ptn_is_not_yet():
    mine = rc.corpus_status(rc.MY_FRAGS)
    assert mine["available"] and mine["total"] == 36607
    ptn = rc.corpus_status(rc.PTN_FRAGS)
    assert not ptn["available"]
    assert "carry no killer" in ptn["blocked_by"]
    assert "otherEntityNum2" in ptn["needs"]


def test_the_clan_tag_is_blue_pTn_and_a_yellow_dot():
    """Verified against the vendored colour table, which has eight entries
    and no extension: ^4 is blue and ^3 is yellow. ^2 would be green."""
    assert rc.PTN_TAG == chr(94) + "4pTn" + chr(94) + "3."
    assert rc.PTN_TAG_COLOURS["pTn"][1:] == ("COLOR_BLUE", "3266fe")
    assert rc.PTN_TAG_COLOURS["."][1:] == ("COLOR_YELLOW", "fefe00")


def test_the_tag_is_not_part_of_a_name():
    """/clan sets it and the server prepends it to connect and chat lines.
    player_names_v1 never had it, because the parser reads only `n`."""
    st = rc.corpus_status(rc.PTN_FRAGS)
    assert "NOT in" in st["clan_membership"]
    assert "server_text_v1" in st["clan_membership"]


def test_membership_is_evidence_or_the_users_word_and_says_which():
    """A name is on the roster because it was seen wearing the tag, or
    because the user put it there. Never because 'pTn' matched a string."""
    seen = [k for k, v in rc.PTN_ROSTER.items()
            if v["basis"] == rc.TAG_OBSERVED]
    declared = [k for k, v in rc.PTN_ROSTER.items()
                if v["basis"] == rc.USER_DECLARED]
    assert "NaikoMarie" in seen and "jibyjibs" in seen
    assert declared == ["b3nto"]
    # b3nto is a real player with no tag evidence, and the row says so
    b = rc.PTN_ROSTER["b3nto"]
    assert b["tag_lines"] == 0 and "no tag evidence" in b["note"]
    for k, v in rc.PTN_ROSTER.items():
        if v["basis"] == rc.TAG_OBSERVED:
            assert v["tag_lines"] > 0, k


def test_names_wearing_the_tag_are_surfaced_not_absorbed():
    """Three names wear the tag and are not on the user's list. They are a
    question for the user, not a decision for the code."""
    assert set(rc.PTN_ALIAS_CANDIDATES) == {"Xhipper", "rctmyouen", "Kabuu"}
    assert not (set(rc.PTN_ALIAS_CANDIDATES) & set(rc.PTN_ROSTER))
    for k, v in rc.PTN_ALIAS_CANDIDATES.items():
        assert v["basis"] == rc.ALIAS_CANDIDATE and v["tag_lines"] > 0


# ── the five roles ──────────────────────────────────────────────────────────

def test_there_are_exactly_five_roles_and_they_map_to_the_number_keys():
    assert len(rc.ROLES) == 5
    assert [rc.ROLE_BY_KEY[str(i)] for i in range(1, 6)] == list(rc.ROLES)
    for r in rc.ROLES:
        assert r in rc.ROLE_LABEL and r in rc.ROLE_HINT


def test_an_unknown_role_is_refused():
    with pytest.raises(ValueError, match="unknown role"):
        rc.record("FRAG:1", rc.FRAG, 1, "T9_SOMETHING")


# ── the window ──────────────────────────────────────────────────────────────

def test_the_clip_is_three_seconds_either_side_of_the_moment():
    it = rc.ReviewItem(item_id="FRAG:1", item_type=rc.FRAG, source_id=1,
                       content_hash="h", demo_name="d", server_time_ms=100_000,
                       machine_score=0.0, machine_rank=1, total_items=1)
    assert it.start_ms == 97_000 and it.end_ms == 103_000
    d = it.to_dict()
    assert d["duration_s"] == 6.0 and d["frag_offset_s"] == 3.0


def test_the_window_clamps_at_the_recording_start_rather_than_inventing_time():
    early = rc.ReviewItem(item_id="FRAG:2", item_type=rc.FRAG, source_id=2,
                          content_hash="h", demo_name="d", server_time_ms=900,
                          machine_score=0.0, machine_rank=1, total_items=1)
    assert early.start_ms == 0, "no negative time, and nothing fabricated"
    assert early.end_ms == 3900


# ── nothing is hidden ───────────────────────────────────────────────────────

def test_the_worst_scored_items_come_first_when_asked_for_worst_first():
    q = rc.queue(order=rc.ORDER_WORST_FIRST, limit=20)
    scores = [i.machine_score for i in q]
    assert scores == sorted(scores), "ascending: the user asked for worst first"
    assert q[0].machine_score < 0, "the bottom of the corpus is reachable"


def test_best_first_is_the_same_corpus_from_the_other_end():
    w = rc.queue(order=rc.ORDER_WORST_FIRST, limit=5)
    b = rc.queue(order=rc.ORDER_BEST_FIRST, limit=5)
    assert [i.machine_score for i in b] == sorted(
        [i.machine_score for i in b], reverse=True)
    assert b[0].machine_score > w[0].machine_score


def test_a_low_score_never_removes_an_item_from_the_queue():
    """A score is an order. The machine does not know why a moment is good."""
    q = rc.queue(order=rc.ORDER_WORST_FIRST, limit=100)
    assert len(q) == 100
    assert all(i.source_id for i in q)
    assert all(i.end_ms > i.start_ms for i in q)


def test_the_queue_total_is_the_whole_corpus():
    q = rc.queue(limit=3)
    assert q[0].total_items == rc.count_items(rc.FRAG) > 30_000


# ── verdicts ────────────────────────────────────────────────────────────────

def test_a_verdict_persists_and_is_visible_on_the_item():
    it = rc.queue(limit=1)[0]
    rc.record(it.item_id, it.item_type, it.source_id, rc.T1_FEATURE_FX, "hero")
    again = rc.item(it.item_id)
    assert again.human_role == rc.T1_FEATURE_FX and again.note == "hero"
    assert again.reviewed


def test_changing_a_verdict_keeps_the_note_unless_a_new_one_is_given():
    it = rc.queue(limit=1)[0]
    rc.record(it.item_id, it.item_type, it.source_id, rc.T1_FEATURE_FX, "keep me")
    rc.record(it.item_id, it.item_type, it.source_id, rc.T2_TRANSITION)
    got = rc.item(it.item_id)
    assert got.human_role == rc.T2_TRANSITION and got.note == "keep me"


def test_a_note_can_be_saved_without_choosing_a_role():
    """Writing down a thought must not force a decision."""
    it = rc.queue(limit=1)[0]
    rc.annotate(it.item_id, "maybe xray the wall")
    got = rc.item(it.item_id)
    assert got.note == "maybe xray the wall"
    assert got.human_role is None and not got.reviewed


def test_the_last_verdict_can_be_undone():
    a, b = rc.queue(limit=2)
    rc.record(a.item_id, a.item_type, a.source_id, rc.T4_KEEP_NORMAL)
    rc.record(b.item_id, b.item_type, b.source_id, rc.T5_PASS_FILLER)
    assert rc.undo_last()["undone"] == b.item_id
    assert rc.item(b.item_id).human_role is None
    assert rc.item(a.item_id).human_role == rc.T4_KEEP_NORMAL


def test_progress_counts_every_role_separately():
    q = rc.queue(limit=3)
    rc.record(q[0].item_id, q[0].item_type, q[0].source_id, rc.T1_FEATURE_FX)
    rc.record(q[1].item_id, q[1].item_type, q[1].source_id, rc.T3_RHYTHM_MONTAGE)
    p = rc.progress()
    assert p["reviewed"] == 2
    assert p["roles"][rc.T1_FEATURE_FX] == 1
    assert p["roles"][rc.T3_RHYTHM_MONTAGE] == 1
    assert p["unreviewed"] == p["total"] - 2


# ── pools: what makes the review worth doing ────────────────────────────────

def test_a_role_becomes_a_queryable_pool():
    """Ten rails in a row should be a query, not a memory."""
    q = rc.queue(limit=6)
    for it in q[:3]:
        rc.record(it.item_id, it.item_type, it.source_id, rc.T3_RHYTHM_MONTAGE)
    rc.record(q[3].item_id, q[3].item_type, q[3].source_id, rc.T1_FEATURE_FX)
    assert len(rc.pool(rc.T3_RHYTHM_MONTAGE)) == 3
    assert len(rc.pool(rc.T1_FEATURE_FX)) == 1
    assert rc.pool(rc.T2_TRANSITION) == []


def test_a_pool_can_be_narrowed_by_weapon():
    q = rc.queue(limit=8)
    for it in q:
        rc.record(it.item_id, it.item_type, it.source_id, rc.T3_RHYTHM_MONTAGE)
    weapons = {i.weapon for i in q}
    for w in weapons:
        got = rc.pool(rc.T3_RHYTHM_MONTAGE, weapon=w)
        assert len(got) == sum(1 for i in q if i.weapon == w), w


def test_notes_are_searchable():
    it = rc.queue(limit=1)[0]
    rc.record(it.item_id, it.item_type, it.source_id, rc.T1_FEATURE_FX,
              "maybe xray the wall here")
    assert [r["item_id"] for r in rc.search_notes("xray")] == [it.item_id]
    assert rc.search_notes("nothing-like-this") == []


# ── the rules that keep the corpus whole ────────────────────────────────────

def test_pass_is_a_role_not_a_deletion():
    """PASS means 'not primary'. It stays in the corpus for the two-frame
    flash nobody has thought of yet."""
    it = rc.queue(limit=1)[0]
    rc.record(it.item_id, it.item_type, it.source_id, rc.T5_PASS_FILLER)
    assert rc.item(it.item_id) is not None
    assert rc.pool(rc.T5_PASS_FILLER)[0]["item_id"] == it.item_id
    assert rc.queue(limit=1)[0].item_id == it.item_id, "still in the queue"


def test_reviewing_does_not_consume_the_moment():
    """A verdict says what a moment is FOR. It does not spend it."""
    it = rc.queue(limit=1)[0]
    rc.record(it.item_id, it.item_type, it.source_id, rc.T1_FEATURE_FX)
    got = rc.item(it.item_id)
    assert got.reviewed
    assert not hasattr(got, "consumed") and not hasattr(got, "used")


def test_unreviewed_only_hides_answered_items_without_deleting_them():
    first = rc.queue(limit=1)[0]
    rc.record(first.item_id, first.item_type, first.source_id, rc.T4_KEEP_NORMAL)
    remaining = rc.queue(limit=5, unreviewed_only=True)
    assert first.item_id not in [i.item_id for i in remaining]
    assert first.item_id in [i.item_id for i in rc.queue(limit=5)]


def test_the_item_type_is_generic_from_the_start():
    """A telefrag, a death and a jump-pad dodge get the same five questions,
    because the system already knows what the event IS."""
    assert rc.FRAG in rc.ITEM_TYPES and len(rc.ITEM_TYPES) > 1
    for t in rc.ITEM_TYPES:
        assert isinstance(t, str) and t.isupper()
    assert rc.queue(item_type=rc.DEATH) == [], "not wired yet, and says so"
