"""The four reproductions an independent checker found, each now failing safe.

Every test here is a bug that was real, shipped, and would have corrupted
either the user's review data or the meaning of a number they were shown.
They are kept as reproductions rather than rewritten as unit tests, because
the value is in the exact shape of what went wrong.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from creative_suite.engine import human_migration as hm
from creative_suite.engine import mining_epoch as me
from creative_suite.engine import review_corpus as rc

RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"


def _corpus() -> bool:
    try:
        with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
            return bool(c.execute(
                "SELECT 1 FROM kill_occurrences_v1 LIMIT 1").fetchone())
    except sqlite3.Error:
        return False


live = pytest.mark.skipif(not _corpus(), reason="needs the local corpus")


# ── 1. a changed fingerprint at the same id must BLOCK ──────────────────────

def test_a_changed_fingerprint_at_the_same_id_blocks_promotion(monkeypatch):
    """The id matching is not evidence that the event is the same.

    The first guard had a status called CHANGED_ID_SAME_EVENT and treated it
    as safe -- asserting "same event" on the strength of the integer, which
    is precisely what a renumbering breaks. A verdict left pointing at a
    moved id is a judgement about a moment nobody judged.
    """
    monkeypatch.setattr(hm, "human_targets",
                        lambda db=None: {"human_reviews": [495]})
    calls = {"n": 0}

    def moved(ids, db=None):
        calls["n"] += 1
        return {495: "FINGERPRINT_BEFORE" if calls["n"] == 1
                else "FINGERPRINT_AFTER"}

    monkeypatch.setattr(hm, "fingerprints", moved)
    out = hm.check()
    assert out["blocked"] is True
    assert out["by_status"] == {hm.FINGERPRINT_CHANGED: 1}
    assert hm.FINGERPRINT_CHANGED not in hm.SAFE


def test_only_a_proven_mapping_makes_a_move_safe(monkeypatch):
    monkeypatch.setattr(hm, "human_targets",
                        lambda db=None: {"human_reviews": [495]})
    # BEFORE and AFTER must be different databases, or the test proves
    # nothing about a move.
    before = {495: "SAME"}
    after = {495: "SAME", 900: "SAME"}

    def fake(ids, db=None):
        table = before if db == hm.RECOGNITION_DB else after
        return {i: table[i] for i in ids if i in table}

    monkeypatch.setattr(hm, "fingerprints", fake)
    other = Path("after.db")
    # Unchanged: EXACT.
    assert hm.check(after_db=other)["by_status"] == {hm.EXACT: 1}
    # Moved, with a mapping to an id carrying the SAME fingerprint: accepted.
    after[495] = "MOVED"
    out = hm.check(after_db=other, mapping={495: 900})
    assert out["by_status"] == {hm.MAPPED: 1} and not out["blocked"]
    # Moved, mapped to something that is NOT the same event: refused.
    after[900] = "DIFFERENT"
    assert hm.check(after_db=other, mapping={495: 900})["blocked"] is True
    # Moved with no mapping at all: refused.
    assert hm.check(after_db=other)["blocked"] is True


def test_production_usage_is_protected():
    """SHORTLISTED / ASSIGNED / USED is the director's decision.

    It looks like machine state. Losing it loses real editorial work with
    nothing to show that it happened.
    """
    assert any(t == "production_usage" for t, _c, _l in hm.HUMAN_TABLES)


# ── 2. repeat promotion must not renumber ───────────────────────────────────

def test_promoting_the_same_staging_twice_is_idempotent(tmp_path):
    """It used to hand the same action id 1, then 2.

    Every human review of that action would have silently re-pointed at a
    different moment on the second promotion.
    """
    epoch = tmp_path / "epoch.db"
    target = tmp_path / "recognition.db"
    with sqlite3.connect(epoch) as c:
        c.execute("CREATE TABLE action_moments_v1 (action_key TEXT PRIMARY "
                  "KEY, content_hash TEXT, observed_pain INT, version TEXT)")
        c.executemany(
            "INSERT INTO action_moments_v1 VALUES (?,?,?,?)",
            [("ACT:aaa", "h1", 5, "v1"), ("ACT:bbb", "h2", 7, "v1")])

    first = me.promote(recognition=target, epoch=epoch, skip_guards=True)
    second = me.promote(recognition=target, epoch=epoch, skip_guards=True)
    assert first["status"] == second["status"] == "ACTIVE"

    with sqlite3.connect(f"file:{target}?mode=ro", uri=True) as c:
        rows = c.execute("SELECT action_key, observed_pain FROM "
                         "action_moments_v1 ORDER BY action_key").fetchall()
    assert rows == [("ACT:aaa", 5), ("ACT:bbb", 7)], \
        "repeat promotion duplicated or renumbered rows"


def test_promotion_refuses_a_table_with_no_stable_key(tmp_path):
    """A rowid is a property of insertion order, not of the moment."""
    epoch = tmp_path / "epoch.db"
    target = tmp_path / "recognition.db"
    with sqlite3.connect(epoch) as c:
        c.execute("CREATE TABLE action_moments_v1 (action_id INTEGER "
                  "PRIMARY KEY AUTOINCREMENT, content_hash TEXT, "
                  "version TEXT)")
        c.execute("INSERT INTO action_moments_v1(content_hash, version) "
                  "VALUES ('h1','v1')")
    out = me.promote(recognition=target, epoch=epoch, skip_guards=True)
    assert out["tables"]["action_moments_v1"]["status"] == "REFUSED"


def test_promotion_is_atomic_and_guarded(tmp_path, monkeypatch):
    """One transaction, and the human guard runs as part of cutover.

    The first version committed each table separately and ran the guard
    beside promotion rather than inside it, so a failure halfway left the
    authority holding one new layer and one old one.
    """
    epoch = tmp_path / "epoch.db"
    target = tmp_path / "recognition.db"
    with sqlite3.connect(epoch) as c:
        c.execute("CREATE TABLE action_moments_v1 (action_key TEXT PRIMARY "
                  "KEY, content_hash TEXT, version TEXT)")
        c.execute("INSERT INTO action_moments_v1 VALUES ('ACT:a','h','v1')")

    monkeypatch.setattr(hm, "check", lambda *a, **k: {
        "blocked": True, "by_status": {hm.MISSING: 1}, "human_targets": 1,
        "blockers": [{"table": "human_reviews", "key": 1,
                      "status": hm.MISSING, "detail": "gone"}]})
    with pytest.raises(me.PromotionBlocked):
        me.promote(recognition=target, epoch=epoch)
    assert not target.exists() or not sqlite3.connect(
        f"file:{target}?mode=ro", uri=True).execute(
        "SELECT name FROM sqlite_master WHERE name='action_moments_v1'"
    ).fetchone(), "a blocked promotion still wrote"


# ── 3. an ACTION id must never be read as an occurrence id ──────────────────

@live
def test_an_action_never_receives_a_frags_truth():
    """`ACTION:41` was served the truth of kill 41.

    Nothing errored: 41 is a perfectly good occurrence id, so the reviewer
    was shown another player's health, weapon and opponent as though they
    described the action.
    """
    from creative_suite.engine import action_truth as at
    q = rc.queue(limit=1, item_type=rc.ACTION, corpus=rc.NO_KILL_ACTIONS)
    if not q:
        pytest.skip("no reviewable actions")
    item = q[0]
    assert item.item_id.startswith("ACTION:ACT:"), item.item_id
    assert item.source_id == rc.NOT_AN_OCCURRENCE

    truth = at.for_item(item.item_id)
    assert truth is not None
    assert truth["available"] is False, "an ACTION was served kill truth"
    assert truth["target_type"] == rc.ACTION
    assert "not an occurrence-backed family" in truth["reason"]


@live
def test_a_colliding_integer_cannot_cross_namespaces():
    """The heart of the bug: 41 means nothing without a namespace."""
    from creative_suite.engine import action_truth as at
    frag = at.for_item("USER_FRAG:495")
    assert frag and frag["available"] is True
    for bogus in ("ACTION:495", "ACTION:ACT:495"):
        out = at.for_item(bogus)
        assert out is None or out["available"] is False


# ── 4. the test launcher must refuse the live database ──────────────────────

def test_the_launcher_refuses_the_live_database():
    """`--db` was taken on trust.

    The launcher called itself isolated because every module pointed at the
    SAME file -- which is equally true when that file is the user's real
    database. Isolation means "not live", not "consistent".
    """
    import review_test_instance as ti
    live = REPO_ROOT / "creative_suite" / "database" / "editorial.db"
    for candidate in (live,
                      live.with_name("EDITORIAL.DB"),
                      live.with_name("editorial.db-wal"),
                      live.parent / "anything.db"):
        with pytest.raises(SystemExit):
            ti.reject_if_live(candidate)


def test_a_temporary_database_is_accepted():
    import review_test_instance as ti
    ti.reject_if_live(Path(tempfile.gettempdir()) / "rt" / "editorial.db")


def test_the_launcher_copies_with_the_backup_api(tmp_path):
    """Three separate file copies are three reads at three instants.

    In WAL mode recent commits live in `-wal` until a checkpoint, so a
    hand-rolled copy can hold a half-applied transaction or miss commits --
    and it opens without complaint either way.
    """
    import review_test_instance as ti
    src = tmp_path / "src.db"
    with sqlite3.connect(src) as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("CREATE TABLE t (x INT)")
        c.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(50)])
    dest = tmp_path / "copy.db"
    ti.backup_copy(src, dest)
    with sqlite3.connect(f"file:{dest}?mode=ro", uri=True) as c:
        assert c.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 50
    import inspect
    assert ".backup(" in inspect.getsource(ti.backup_copy)


# ── policy is not truth ─────────────────────────────────────────────────────

@live
def test_a_telefrag_is_still_a_kill():
    """SPECIAL QUEUES DO NOT REDEFINE GAME TRUTH.

    Excluding telefrags from the review queue silently moved the project's
    authoritative statistic from 33,316 confirmed user frags to 33,102, as
    though 214 kills had stopped existing. They had not; they had stopped
    being offered.
    """
    canonical = rc.canonical_count(rc.USER_FRAG, corpus=rc.USER_FRAGS)
    queue = rc.count_items(rc.USER_FRAG, corpus=rc.USER_FRAGS)
    assert canonical > queue, "queue policy is not being applied at all"

    with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
        tele = c.execute(
            "SELECT COUNT(*) FROM kill_occurrences_v1 WHERE mod = 18 AND "
            "killer_class='PLAYER' AND killer_name_norm IN "
            "('tr4sh','stoneface','. stoneface')").fetchone()[0]
    assert tele > 0
    # Still counted as the user's kills.
    assert canonical >= queue + tele


@live
def test_progress_reports_both_denominators():
    """A queue denominator must never be mistaken for the statistic."""
    pr = rc.progress(rc.USER_FRAG, corpus=rc.USER_FRAGS)
    assert pr["canonical_total"] > pr["total"]
    assert pr["queue_excluded"] == pr["canonical_total"] - pr["total"]
    assert "canonical" in pr["denominator_note"]


# ── attribution language ────────────────────────────────────────────────────

@live
def test_activity_share_is_never_called_attribution():
    """Shot share proves the recorder was shooting, not that they hit.

    In a five-a-side fight most of the shooting is not yours; a pain event
    proves damage and not whose.
    """
    q = rc.queue(limit=1, item_type=rc.ACTION, corpus=rc.NO_KILL_ACTIONS)
    if not q:
        pytest.skip("no reviewable actions")
    d = rc.action_detail(q[0].item_id)
    assert "recorder_activity_share" in d
    assert "confidence" not in d, "a share is being presented as confidence"
    assert not any("damage" in k.lower() for k in d)
    assert "NOT proof" in d["what_this_is_not"]


@live
def test_no_kill_claims_are_scoped_honestly():
    """"No user kill here" and "nobody died here" are different claims."""
    with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
        no_user = c.execute(
            "SELECT COUNT(*) FROM action_moments_v1 WHERE "
            "user_kill_in_window = 0").fetchone()[0]
        no_obit = c.execute(
            "SELECT COUNT(*) FROM action_moments_v1 WHERE "
            "any_obituary_in_window = 0").fetchone()[0]
        wrong = c.execute(
            "SELECT COUNT(*) FROM action_moments_v1 WHERE classes LIKE "
            "'%NO_OBITUARY_IN_WINDOW%' AND any_obituary_in_window = 1"
        ).fetchone()[0]
    assert no_obit < no_user, (
        "every window without a user kill also had no death at all, which "
        "would mean the wider claim was never actually checked")
    assert wrong == 0


def test_missing_team_is_not_an_enemy():
    """Absence of team data is an unknown relation, never enmity.

    The previous version returned `client != recorder` when the recorder's
    own team was unknown, treating the whole server as opponents -- the
    opposite of what its own comment said.
    """
    import inspect
    from engine.parser import mine_action_moments as ma
    src = inspect.getsource(ma.mine_demo)
    assert "if my_team is None or client == recorder:" in src
    assert "return client != recorder" not in src
