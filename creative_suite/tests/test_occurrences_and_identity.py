"""Two truths the corpus was missing: what a kill IS, and who a name IS.

A kill happened once and several demos may have recorded it. A name is a
string until a human says whose it is. Both were previously assumed, and both
assumptions inflated or mislabelled the corpus the user was about to spend
hours curating.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from creative_suite.engine import identity as idn            # noqa: E402
from creative_suite.engine import kill_occurrences as ko     # noqa: E402


def _row(**kw):
    base = dict(kill_event_id=1, content_hash="h1", kill_fingerprint="fp",
                map="campgrounds", server_time_ms=1000, round=1,
                killer_client=3, victim_client=5, mod=6, mod_name="ROCKET",
                killer_class="PLAYER", death_cause="PLAYER_KILL",
                killer_name_norm="a", victim_name_norm="b",
                is_recorder_killer=0, is_recorder_victim=0)
    base.update(kw)
    return base


# ── occurrence vs observation ───────────────────────────────────────────────

def test_one_demo_is_never_a_merge_decision():
    conf, ev = ko.classify_group([_row()], __import__("collections").Counter())
    assert conf == ko.SINGLE and "one demo" in ev


def test_a_lone_shared_fingerprint_with_different_names_is_a_collision():
    """Server times recur across matches and slots are reused. Two unrelated
    kills CAN line up on (map, time, slots, mod). Collapsing them would
    delete a real historical event, so they stay apart."""
    import collections
    rows = [_row(content_hash="h1", killer_name_norm="alice"),
            _row(kill_event_id=2, content_hash="h2", killer_name_norm="bob")]
    pair = collections.Counter({("h1", "h2"): 1})
    conf, ev = ko.classify_group(rows, pair)
    assert conf == ko.DISTINCT
    assert "names_agree=False" in ev


def test_two_signals_agreeing_is_what_licenses_a_merge():
    """Neither signal alone is enough. Shared-match evidence AND the same
    people at both ends."""
    import collections
    rows = [_row(content_hash="h1"), _row(kill_event_id=2, content_hash="h2")]
    pair = collections.Counter({("h1", "h2"): 12})
    conf, _ = ko.classify_group(rows, pair)
    assert conf == ko.HIGH


def test_conflicting_signals_are_not_resolved_by_lowering_the_count():
    """Agreement with no match evidence, or match evidence with disagreeing
    names, is ambiguity -- and ambiguity keeps the observations separate."""
    import collections
    same_names_no_match = [_row(content_hash="h1"),
                           _row(kill_event_id=2, content_hash="h2")]
    assert ko.classify_group(same_names_no_match,
                             collections.Counter({("h1", "h2"): 1}))[0] == ko.AMBIGUOUS
    diff_names_strong = [_row(content_hash="h1", killer_name_norm="alice"),
                         _row(kill_event_id=2, content_hash="h2",
                              killer_name_norm="bob")]
    assert ko.classify_group(diff_names_strong,
                             collections.Counter({("h1", "h2"): 30}))[0] == ko.AMBIGUOUS


def test_the_actors_own_camera_is_preferred_and_the_choice_is_stable():
    rows = [_row(kill_event_id=9, is_recorder_killer=0),
            _row(kill_event_id=4, is_recorder_killer=1),
            _row(kill_event_id=7, is_recorder_victim=1)]
    assert ko.pick_best(rows) == (4, ko.POV_ACTOR)
    # Same input, same answer -- a wandering choice would re-render media.
    assert ko.pick_best(list(reversed(rows))) == (4, ko.POV_ACTOR)


def test_a_death_is_watched_from_the_camera_of_the_player_who_died():
    rows = [_row(kill_event_id=4, is_recorder_killer=1),
            _row(kill_event_id=7, is_recorder_victim=1)]
    assert ko.pick_best(rows)[0] == 4        # the frag queue wants the killer
    assert ko.pick_victim_pov(rows) == 7     # the death queue wants the victim
    assert ko.pick_victim_pov([_row(kill_event_id=4)]) is None


def test_the_built_layer_loses_no_observation():
    """Nothing is deleted. Every observation belongs to exactly one
    occurrence, and every occurrence names one observation to show."""
    s = ko.summary()
    if not s.get("built"):
        pytest.skip("occurrence layer not built in this environment")
    con = sqlite3.connect(f"file:{ko.RECOGNITION_DB}?mode=ro", uri=True)
    unlinked = con.execute("SELECT COUNT(*) FROM kill_events_v1 "
                           "WHERE occurrence_id IS NULL").fetchone()[0]
    best = con.execute("SELECT COUNT(*) FROM kill_events_v1 "
                       "WHERE is_best_observation=1").fetchone()[0]
    occ = con.execute("SELECT COUNT(*) FROM kill_occurrences_v1").fetchone()[0]
    assert unlinked == 0
    assert best == occ, "one shown observation per occurrence"
    assert s["occurrences"] < s["observations"], "duplicates were collapsed"


# ── identity ────────────────────────────────────────────────────────────────

def test_the_project_asserts_the_primary_identity_and_nothing_else():
    """The project seeds exactly one identity and leaves the rest as
    questions. This checks the RULE, not the current contents -- the
    confirmed set is live user data and a test that pins it would either
    break whenever the user answers something or, worse, quietly encode
    their answers as expectations."""
    st = idn.status()
    assert idn.PRIMARY_USER in st["user_confirmed"]
    seeded = [n for n, d in idn.decisions().items()
              if d["decided_by"] == idn.BY_SEED
              and d["user_state"] == idn.USER_CONFIRMED]
    assert seeded == [], "the seed asserts membership, never user identity, "                          "beyond the primary written at first run"
    assert st["unanswered"] > 0, "108 identities remain unanswered"


def test_every_confirmed_identity_carries_who_decided_it():
    """A confirmed identity without provenance is indistinguishable from a
    guess that got written down."""
    for name, d in idn.decisions().items():
        if d["user_state"] == idn.USER_CONFIRMED:
            assert d["decided_by"] in idn.HUMAN_DECIDED, name
            assert d["decided_at"], name


def test_the_roster_the_user_supplied_is_seeded_and_does_not_grow():
    """Tag evidence surfaces candidates; it does not add members."""
    ptn = idn.confirmed_ptn_identities()
    assert set(idn.USER_SUPPLIED_PTN) <= ptn
    assert idn.PRIMARY_USER in ptn
    cands = {c["name_norm"] for c in idn.ptn_candidates(min_lines=100)}
    unconfirmed = cands - ptn
    assert unconfirmed, "candidates exist and are NOT members"


def test_a_user_supplied_alias_survives_without_its_own_observation():
    """S7ern was never seen as its own spelling. The user stated the
    relation, and the user's statement IS the provenance."""
    assert idn.USER_DEFINED_ALIASES["s7ern"] == "s73rn"
    assert "s7ern" in idn.confirmed_ptn_identities()


def test_being_the_user_and_being_in_the_clan_are_separate_questions():
    """A person can be both. Answering one must not answer the other."""
    before = idn.decisions().get("zzz_probe", {})
    assert not before
    idn.decide("zzz_probe", user_state=idn.USER_NOT, decided_by=idn.BY_TEST)
    row = idn.decisions()["zzz_probe"]
    assert row["user_state"] == idn.USER_NOT
    assert row["ptn_state"] == idn.PTN_UNKNOWN, "clan question untouched"
    idn.decide("zzz_probe", ptn_state=idn.PTN_MEMBER, decided_by=idn.BY_TEST)
    row = idn.decisions()["zzz_probe"]
    assert row["user_state"] == idn.USER_NOT, "user answer untouched"
    with idn.conn() as c:
        c.execute("DELETE FROM identity_decisions WHERE name_norm='zzz_probe'")


def test_a_test_decision_never_counts_as_a_human_answer():
    """The same rule the creative review already enforces: only a human
    writes human truth."""
    idn.decide("zzz_probe2", user_state=idn.USER_CONFIRMED,
               decided_by=idn.BY_TEST)
    assert "zzz_probe2" not in idn.confirmed_user_identities()
    with idn.conn() as c:
        c.execute("DELETE FROM identity_decisions WHERE name_norm='zzz_probe2'")


def test_an_unknown_state_is_refused():
    with pytest.raises(ValueError, match="user_state"):
        idn.decide("x", user_state="MAYBE_ME")
    with pytest.raises(ValueError, match="ptn_state"):
        idn.decide("x", ptn_state="SORT_OF")


def test_the_evidence_carries_dates_but_never_a_demo_filename():
    """A date range is the most useful thing for "was this me". The filename
    it came from embeds aliases and must not travel with it."""
    cands = idn.recorder_candidates(limit=3)
    assert cands and cands[0]["name_norm"] == idn.PRIMARY_USER
    for c in cands:
        assert "demo_name" not in c and "demos" not in c
        assert set(c) >= {"demos_recorded", "recorder_own_kills", "maps",
                          "first_played", "last_played", "ptn_tag_lines"}
        assert ".dm_73" not in repr(c)
