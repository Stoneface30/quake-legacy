"""What the review queue refuses to offer, and in what order.

All of this came from one real phone session:

  "first clip that loaded is a warmup clip - remove all warmup countdown
   clip (not round countdown)"
  "movement / other people telefrag or useless things are out of the
   picture too"
  "default to my frag keep other people frag for last (ptn member frags are
   kept!)"
  "AND the option to delete too"

None of it is about quality. Every one of these is a moment that cannot be
judged at all -- and each costs forty seconds of wolfcam to film before the
reviewer can even skip it.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import review_corpus as rc

RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"


def _corpus_available() -> bool:
    try:
        with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
            return bool(c.execute(
                "SELECT 1 FROM kill_occurrences_v1 LIMIT 1").fetchone())
    except sqlite3.Error:
        return False


pytestmark = pytest.mark.skipif(
    not _corpus_available(), reason="needs the local corpus")


@pytest.fixture()
def isolated(tmp_path, monkeypatch):
    """Deletions and verdicts go to a throwaway database.

    The user's three genuine reviews live in the real one.
    """
    db = tmp_path / "editorial.db"
    monkeypatch.setattr(rc, "EDITORIAL_DB", db, raising=False)
    return db


# ── the SQL says what it means ──────────────────────────────────────────────

def test_the_warmup_rule_needs_the_demo_to_have_rounds():
    """Round 0 means two different things, and the demo decides which.

    In a Clan Arena demo the counter starts at 1 when the match goes live, so
    a kill still on round 0 is pre-match warmup. In a demo with no round
    system EVERY kill is round 0 and none of them is warmup. Excluding round
    0 unconditionally would delete every duel and every TDM frag in the
    archive.
    """
    sql, _ = rc.junk_sql()
    assert "o.round = 0" in sql
    assert "round_kills_v1" in sql and "rk.round >= 1" in sql


def test_telefrags_are_excluded_by_means_of_death_not_by_name():
    sql, _ = rc.junk_sql()
    assert rc.MOD_TELEFRAG == 18
    assert "o.mod <> 18" in sql


def test_the_round_countdown_survives():
    """The countdown is not warmup, and the user said so explicitly.

    The server announces the next round about seven seconds before it starts,
    so a kill during that countdown already carries its round number. A rule
    written against the announced START TIME instead of the round number
    would have eaten 955 real kills.
    """
    with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
        countdown_kills = c.execute(
            "SELECT COUNT(*) FROM kill_occurrences_v1 WHERE round >= 1"
        ).fetchone()[0]
    assert countdown_kills > 0
    sql, _ = rc.junk_sql()
    # The exclusion is scoped to round 0 only; nothing with a round number
    # can match it.
    assert "o.round = 0" in sql and "o.round >= 1" not in sql


# ── measured against the real corpus ────────────────────────────────────────

def test_warmup_and_telefrag_actually_leave_the_queue():
    ids = {it.item_id for it in rc.queue(limit=400, item_type=rc.ALL_KILL,
                                         corpus=rc.ALL_PLAYERS)}
    occ = [int(i.split(":")[1]) for i in ids]
    if not occ:
        pytest.skip("empty queue")
    marks = ",".join("?" * len(occ))
    with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
        bad = c.execute(
            f"SELECT COUNT(*) FROM kill_occurrences_v1 o WHERE "
            f"o.occurrence_id IN ({marks}) AND o.mod = ?", (*occ, 18)
        ).fetchone()[0]
    assert bad == 0, "a telefrag reached the queue"


def test_mine_first_then_the_clan_then_everyone_else():
    """Ordering, not filtering.

    Nothing is hidden: a queue that runs out of the user's own frags
    continues into the clan's rather than ending.
    """
    users = rc.user_norms()
    clan = rc.roster_norms() - users
    seen = []
    for it in rc.queue(limit=300, item_type=rc.ALL_KILL,
                       corpus=rc.ALL_PLAYERS):
        a = (it.actor_name or "").lower()
        seen.append(rc.ACTOR_USER if a in users
                    else rc.ACTOR_PTN if a in clan else rc.ACTOR_OTHER)
    assert seen, "empty queue"
    assert seen == sorted(seen), "actor priority is not monotonic"
    assert seen[0] == rc.ACTOR_USER, "the user's own frags are not first"


def test_a_verdict_follows_the_occurrence_across_families():
    """One kill happened once.

    The same occurrence is `USER_FRAG:495` in the user's own queue and
    `ALL_KILL:495` in the combined one. A lookup keyed on the current family
    alone would show a moment the user already judged as untouched, and ask
    them to judge it again just because the queue was widened.
    """
    judged = rc.occurrence_reviews([495, 1080, 18858])
    if not judged:
        pytest.skip("no reviews in this database")
    for occ, rv in judged.items():
        assert rv.get("human_role")


# ── delete is not a verdict ─────────────────────────────────────────────────

def test_delete_removes_from_the_queue_and_restore_puts_it_back(isolated):
    q = rc.queue(limit=3, item_type=rc.ALL_KILL, corpus=rc.ALL_PLAYERS)
    if not q:
        pytest.skip("empty queue")
    victim = q[0].item_id
    before = rc.count_items(rc.ALL_KILL, corpus=rc.ALL_PLAYERS)

    rc.dismiss(victim, "useless", provenance=rc.TEST)
    assert rc.count_items(rc.ALL_KILL, corpus=rc.ALL_PLAYERS) == before - 1
    assert victim not in {i.item_id for i in
                          rc.queue(limit=5, item_type=rc.ALL_KILL,
                                   corpus=rc.ALL_PLAYERS)}

    assert rc.restore(victim)
    assert rc.count_items(rc.ALL_KILL, corpus=rc.ALL_PLAYERS) == before
    assert rc.restore(victim) is None          # already restored


def test_a_deletion_is_never_creative_truth(isolated):
    """T5_PASS_FILLER and DELETE are different statements.

    "I watched it and it is filler" is a judgement the film may read.
    "Stop offering me this" is housekeeping the film must never see. Storing
    them together would quietly turn one into the other.
    """
    q = rc.queue(limit=2, item_type=rc.ALL_KILL, corpus=rc.ALL_PLAYERS)
    if not q:
        pytest.skip("empty queue")
    rc.dismiss(q[0].item_id, provenance=rc.TEST)

    with rc.conn() as c:
        rows = c.execute("SELECT COUNT(*) FROM human_reviews").fetchone()[0]
    assert rows == 0, "a deletion was written as a verdict"

    pr = rc.progress(rc.ALL_KILL, corpus=rc.ALL_PLAYERS)
    assert sum(pr["roles"].values()) == 0
    assert rc.dismissed(), "the deletion was not recorded anywhere"


def test_deleting_something_that_does_not_exist_is_refused(isolated):
    with pytest.raises(ValueError):
        rc.dismiss("ALL_KILL:999999999", provenance=rc.TEST)


def test_a_broken_deletion_store_does_not_empty_the_queue(monkeypatch):
    """Failing closed here would be the wrong way round.

    Showing a moment the user deleted is a far smaller failure than showing
    them nothing at all.
    """
    def boom():
        raise sqlite3.OperationalError("no such table")
    monkeypatch.setattr(rc, "conn", boom)
    assert rc.dismissed_occurrence_ids() == []
