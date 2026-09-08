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

def test_every_corpus_is_now_served_by_real_killer_attribution():
    """PTN_FRAGS was blocked because the cached death rows named no killer.
    The obituary derivation supplies one, so the block is gone -- and each
    corpus reports which table answers it."""
    mine = rc.corpus_status(rc.MY_FRAGS)
    assert mine["available"] and mine["total"] == 36607
    assert mine["item_type"] == rc.FRAG and mine["scored"] is True
    for name in (rc.PTN_FRAGS, rc.MY_AND_PTN, rc.ALL_PLAYERS):
        st = rc.corpus_status(name)
        assert st["available"], st.get("blocked_by")
        assert st["total"] > 0
        assert st["item_type"] in rc.KILL_BACKED


def test_a_corpus_says_out_loud_that_foreign_frags_are_unscored():
    """Not a footnote. The user asked for this explicitly: do not pretend
    scores are comparable when the features behind them are not available."""
    st = rc.corpus_status(rc.PTN_FRAGS)
    assert "unscored, not scored zero" in st["scoring"]
    assert "recorder" in st["scoring"]


def test_the_roster_matches_confirmed_names_not_the_substring_pTn():
    """A tag is a costume. Membership is the CONFIRMED roster, normalized --
    never a LIKE on 'pTn' appearing somewhere in a name, and never everything
    the tag evidence turned up."""
    norms = rc.roster_norms()
    assert {"naikomarie", "sereke", "s73rn", "jibyjibs", "b3nto",
            "tr4sh"} <= norms
    where, params = rc._kill_where(rc.CLAN_FRAG)
    assert "killer_name_norm IN" in where
    assert "LIKE" not in where.upper()
    # The clan queue excludes the user, who is separately a member.
    assert set(params) == norms - rc.user_norms()


def test_an_unconfirmed_identity_set_selects_nothing(monkeypatch):
    """An unanswered identity question is not permission to guess. An empty
    confirmed set must match zero rows, never every row."""
    monkeypatch.setattr(rc, "user_norms", set)
    where, params = rc._kill_where(rc.USER_FRAG)
    assert params == [] and "IN (NULL)" in where
    assert rc.count_items(rc.USER_FRAG) == 0


def test_a_clan_frag_is_the_clanmates_kill_not_a_camera_accident():
    """Membership is by identity, so a clanmate's frag belongs to them
    whichever camera recorded it. The old rule keyed on "the killer held the
    camera", which is a statement about recording, not about who made the
    kill."""
    where, params = rc._kill_where(rc.CLAN_FRAG)
    assert "is_recorder_killer" not in where
    assert "killer_name_norm IN" in where
    assert "tr4sh" not in params, "the user is served by USER_FRAGS"


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
    # b3nto is a real player with no tag evidence, and the row explains why
    # rather than leaving it looking like a hole in the data: he joined late
    # and sometimes played untagged.
    b = rc.PTN_ROSTER["b3nto"]
    assert b["tag_lines"] == 0
    assert "joined later" in b["note"] and "untagged" in b["note"]
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
    # DEATH is wired now, off the same obituary truth as the frags, and it
    # asks the same five questions.
    deaths = rc.queue(item_type=rc.DEATH, limit=3)
    assert deaths and all(d.item_type == rc.DEATH for d in deaths)
    where, _ = rc._kill_where(rc.DEATH)
    assert "victim_name_norm IN" in where, "the user's own deaths, by identity"


def test_a_dodge_is_a_feature_of_a_frag_not_a_moment_of_its_own():
    """36,586 dodge rows against 36,607 frags looks like one per frag. It is
    a coincidence: the rows carry kill_anchor_ms and collapse to 19,877
    distinct anchors, every one of them a frag already reviewable in
    MY_FRAGS, up to eight rows per frag. Offering it as a queue would show
    the same frag eight times and call each showing a different moment."""
    assert rc.DODGE in rc.NOT_A_REVIEW_MOMENT
    why = rc.NOT_A_REVIEW_MOMENT[rc.DODGE]
    assert "19,877" in why and "per-frag feature" in why
    assert rc.queue(item_type=rc.DODGE) == []


def test_the_teleport_queue_is_the_recorders_own_confirmed_transits():
    """Only the recorder's transits, and only the ones attribution actually
    confirmed. An UNKNOWN or AMBIGUOUS outcome is a transit we could not
    attribute, and offering it as 'your teleport' would assert what the
    attribution declined to."""
    n = rc.count_items(rc.TELEPORT)
    assert 0 < n < 53503, "the recorder's own subset, not every transit"
    q = rc.queue(item_type=rc.TELEPORT, limit=3)
    assert q and all(i.item_type == rc.TELEPORT for i in q)
    assert all(i.scored is False for i in q), "a transit never had a score"
    assert rc.TELEPORT_CONFIRMED == "TELEPORT_PLAYER_CONFIRMED"


def test_every_family_uses_the_same_six_second_window():
    """One window, so a verdict means the same thing whatever was reviewed."""
    for t in (rc.FRAG, rc.TELEFRAG, rc.DEATH, rc.CLAN_FRAG, rc.TELEPORT):
        it = rc.queue(item_type=t, limit=1)
        if not it:
            continue
        assert it[0].end_ms - it[0].start_ms <= rc.PRE_MS + rc.POST_MS


def test_the_combined_corpus_does_not_report_all_player_progress():
    """MY_AND_PTN and ALL_PLAYERS share an item type but not a total -- the
    combined corpus is narrowed by the roster in SQL. Counting without the
    corpus would measure progress against the wrong denominator."""
    both = rc.progress(rc.ALL_KILL, corpus=rc.MY_AND_PTN)["total"]
    everyone = rc.progress(rc.ALL_KILL, corpus=rc.ALL_PLAYERS)["total"]
    assert 0 < both < everyone


def test_my_frags_says_when_the_recorder_was_not_the_user():
    """is_recorder_killer means the killer recorded THAT demo. The archive
    holds 172 demos recorded by other people, so a slice of MY_FRAGS is
    somebody else's kill in their own demo. That is surfaced, not silently
    filtered -- narrowing it needs the user to confirm which recorder
    identities are theirs."""
    sp = rc.recorder_identity_spread()
    assert sp["available"]
    assert sp["confirmed_user"] > 0
    assert sp["not_the_user"] > 0, "the corpus is not all one recorder"
    assert sp["distinct_recorder_identities"] > 1
    assert sp["confirmed_user"] + sp["not_the_user"] == sp["total_recorder_kills"]
    # A likely alias is a candidate, never merged.
    assert "stoneface" in sp["candidates"]
    assert "stoneface" not in rc.USER_RECORDER_NAMES
    assert rc.corpus_status(rc.MY_FRAGS)["recorder_identity"]["available"]


def test_the_anchor_test_is_applied_to_every_special_family():
    """DODGE was caught this way; PROJECTILE, LG and VIEW are the same shape.
    Take one row and ask what it attaches to -- all three land on a frag the
    user already reviews, 100% of the time. Offering them as queues would
    have added 31,550 items that re-describe frags already in USER_FRAGS."""
    for fam in (rc.DODGE, rc.PROJECTILE, rc.LG_TRACKING):
        assert fam in rc.NOT_A_REVIEW_MOMENT, fam
        why = rc.NOT_A_REVIEW_MOMENT[fam]
        assert "per-frag feature" in why
        assert rc.queue(item_type=fam) == []
    # And they survive as filters, which is what that data is for.
    traits = {t["trait"] for t in rc.trait_vocabulary(limit=40)}
    assert {"LG_TRACKING", "NEAR_MISS_ROCKET", "DIRECT_CONFIRMED_GEO"} <= traits


def test_filters_are_a_whitelist_not_a_query_language():
    """Nothing the browser sends reaches SQL as text."""
    import pytest as _p
    with _p.raises(ValueError, match="unknown filter"):
        rc._filter_sql({"; DROP TABLE": "1"})
    where, params = rc._filter_sql({"weapon": "railgun"})
    assert where == " AND o.mod_name = ?" and params == ["RAILGUN"]


def test_a_filter_narrows_without_discarding():
    """Machine score orders; it never removes. A filtered queue is a view of
    the same corpus, and clearing the filter restores it."""
    everything = rc.count_items(rc.USER_FRAG, corpus=rc.USER_FRAGS)
    rails = rc.count_items(rc.USER_FRAG, corpus=rc.USER_FRAGS,
                           filters={"weapon": "RAILGUN"})
    assert 0 < rails < everything


# ── movement and funny ──────────────────────────────────────────────────────

def test_a_movement_moment_keeps_its_own_duration():
    """A frag is an instant and uses the +/-3s window. A run is an action
    with a shape, and truncating it to six seconds would cut off the thing
    the user is being asked to judge."""
    frag = rc.queue(item_type=rc.USER_FRAG, limit=1)[0]
    assert frag.end_ms - frag.start_ms == rc.PRE_MS + rc.POST_MS
    assert frag.window_start_ms is None
    for t in rc.MOVEMENT_BACKED:
        got = rc.queue(item_type=t, order=rc.ORDER_BEST_FIRST, limit=4)
        assert got, t
        assert any(i.end_ms - i.start_ms != rc.PRE_MS + rc.POST_MS
                   for i in got), "movement windows should vary with the action"
        for i in got:
            assert i.window_start_ms is not None


def test_movement_is_not_a_re_description_of_a_frag():
    """These are independent actions: most do not end in a kill at all, and
    the ones that do LINK to the canonical occurrence rather than inventing a
    second historical event."""
    import sqlite3 as _s
    c = _s.connect(f"file:{rc.RECOGNITION_DB}?mode=ro", uri=True)
    total = c.execute("SELECT COUNT(*) FROM movement_moments_v1").fetchone()[0]
    linked = c.execute("SELECT COUNT(*) FROM movement_moments_v1 WHERE "
                       "related_occurrence_id IS NOT NULL").fetchone()[0]
    assert 0 < linked < total, "some link to a frag, most do not"


def test_an_implausible_speed_is_not_recorded_as_a_speed():
    """Displacement over airtime is only a flight speed when the next jump is
    the landing. An early build ranked jump pads by a 7,015 ups 'peak', which
    is not a speed anyone has moved at."""
    import sqlite3 as _s
    from creative_suite.engine import movement_moments as mm
    c = _s.connect(f"file:{rc.RECOGNITION_DB}?mode=ro", uri=True)
    mx = c.execute("SELECT MAX(peak_speed) FROM movement_moments_v1").fetchone()[0]
    assert mx is not None and mx <= mm.IMPLAUSIBLE_UPS
    unrecorded = c.execute("SELECT COUNT(*) FROM movement_moments_v1 WHERE "
                           "kind='JUMPPAD_ACTION' AND peak_speed IS NULL"
                           ).fetchone()[0]
    assert unrecorded > 0, "implausible figures are dropped, not clamped"


def test_funny_is_a_tag_on_an_occurrence_not_a_new_item():
    """A moment with five interesting properties must stay ONE thing to
    judge. Funny/weird narrows the existing queues; it adds no items."""
    assert "FUNNY" not in rc.ITEM_TYPES and "WEIRD" not in rc.ITEM_TYPES
    where, params = rc._filter_sql({"funny": "GAUNTLET_KILL"})
    assert "funny_candidates_v1" in where and "occurrence_id" in where
    n_all = rc.count_items(rc.USER_FRAG, corpus=rc.USER_FRAGS)
    n_fun = rc.count_items(rc.USER_FRAG, corpus=rc.USER_FRAGS,
                           filters={"funny": True})
    assert 0 < n_fun < n_all


def test_funny_does_not_downgrade_anything():
    """A discovery label, not a quality class. Nothing in the corpus code may
    treat a funny candidate as lesser -- it has no role, no score penalty and
    no separate verdict."""
    from creative_suite.engine import funny_candidates as fc
    assert set(fc.WEIGHTS) and all(w > 0 for w in fc.WEIGHTS.values())
    assert fc.WEIGHTS[fc.CHAT_REACTION] == min(fc.WEIGHTS.values()), \
        "chat is the weakest signal and never establishes comedy"
    assert "not a quality class" in fc.summary()["note"]


# -- every declared corpus must be able to describe itself -----------------
#
# NO_KILL_ACTIONS was in CORPORA, had an item type, a WHERE clause, an item
# builder and a working count -- and corpus_status had no branch for it, so it
# fell through to "unknown corpus" and the reviewer never offered the lane.
# The queue existed and nobody could reach it. This is the guard.

def _require_derived_tables():
    """This checkout may carry a stub recognition database. The guard below is
    about the SHAPE of the answer, not the data, so skip rather than fail --
    but skip on the absence of the tables, never on an exception, or a real
    breakage would look like a missing database."""
    import sqlite3
    from creative_suite.engine import review_corpus as rc
    if not Path(rc.RECOGNITION_DB).exists():
        pytest.skip("no recognition database in this checkout")
    c = sqlite3.connect("file:%s?mode=ro" % rc.RECOGNITION_DB, uri=True)
    have = {r[0] for r in c.execute(
        "select name from sqlite_master where type='table'")}
    c.close()
    missing = {"kill_events_v1", "kill_occurrences_v1"} - have
    if missing:
        pytest.skip("recognition database is a stub, missing %s" % sorted(missing))


def test_every_declared_corpus_answers_status():
    from creative_suite.engine import review_corpus as rc
    _require_derived_tables()
    unknown = []
    for corpus in rc.CORPORA:
        st = rc.corpus_status(corpus)
        assert st.get("corpus") == corpus
        assert "available" in st, corpus
        if st.get("blocked_by") == "unknown corpus":
            unknown.append(corpus)
        if not st["available"]:
            # Unavailable is allowed -- this machine may not have the derived
            # tables -- but it must say WHY, or the reviewer cannot act on it.
            assert st.get("blocked_by"), corpus
    assert not unknown, (
        "declared in CORPORA but corpus_status cannot describe: %s" % unknown)


def test_action_status_never_reports_a_machine_score():
    """An action was never scored. Reporting `scored: True` would let the UI
    sort actions against frags, which are not comparable."""
    from creative_suite.engine import review_corpus as rc
    _require_derived_tables()
    st = rc.corpus_status(rc.NO_KILL_ACTIONS)
    assert st.get("scored") is False
    assert st["item_type"] == rc.ACTION
