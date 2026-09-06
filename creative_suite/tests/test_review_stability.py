"""The user is reviewing WHILE this is being built. Nothing may move.

Section 18, verbatim: do not reorder current USER_FRAGS, change verdict
semantics, reset filters, invalidate media cache, or change profile
unnecessarily. Metadata enrichment is allowed.

That is a hard constraint on a live session, not a preference: a queue that
renumbers itself under someone mid-review loses their place, and a cache key
that shifts turns every clip they have already waited for back into a
spinner.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import review_corpus as rc

RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"


def _corpus() -> bool:
    try:
        with sqlite3.connect(f"file:{RECOG_DB.as_posix()}?mode=ro",
                             uri=True) as c:
            return bool(c.execute(
                "SELECT 1 FROM kill_occurrences_v1 LIMIT 1").fetchone())
    except sqlite3.Error:
        return False


live = pytest.mark.skipif(not _corpus(), reason="needs the local corpus")


# ── the queue does not move ─────────────────────────────────────────────────

@live
def test_the_queue_order_is_the_same_twice():
    a = [i.item_id for i in rc.queue(limit=40, corpus="USER_FRAGS")]
    b = [i.item_id for i in rc.queue(limit=40, corpus="USER_FRAGS")]
    assert a == b and a, "the queue reordered itself between two reads"


@live
def test_map_enrichment_does_not_touch_the_queue():
    """Geography is metadata ABOUT moments; it is not allowed to be an
    input to which moment comes next."""
    before = [i.item_id for i in rc.queue(limit=40, corpus="USER_FRAGS")]
    from engine.pantheon import map_context as mc
    mc.clear_cache()
    for it in rc.queue(limit=10, corpus="USER_FRAGS"):
        try:
            mc.context_for_kill(int(it.source_id))
        except Exception:                                      # noqa: BLE001
            pass
    after = [i.item_id for i in rc.queue(limit=40, corpus="USER_FRAGS")]
    assert before == after


def test_the_ordering_rule_still_puts_the_user_first():
    """"default to my frag keep other people frag for last (ptn member frags
    are kept!)" -- the rule the user asked for, unchanged."""
    src = (REPO_ROOT / "creative_suite" / "engine"
           / "review_corpus.py").read_text(encoding="utf-8")
    assert "def actor_priority_sql" in src


def test_verdict_semantics_are_untouched():
    assert rc.ROLES == ("T1_FEATURE_FX", "T2_TRANSITION", "T3_RHYTHM_MONTAGE",
                        "T4_KEEP_NORMAL", "T5_PASS_FILLER")


# ── human work survives ─────────────────────────────────────────────────────

@live
def test_no_human_review_was_lost():
    """The count only ever goes up, and only the user moves it."""
    p = rc.progress("USER_FRAG")
    assert p["reviewed"] >= 3, \
        f"human reviews went backwards: {p['reviewed']}"


@live
def test_the_first_three_verdicts_are_still_theirs():
    from creative_suite.engine import review_corpus as r
    rows = r.occurrence_reviews([495, 1080, 18858])
    for occ in (495, 1080, 18858):
        assert occ in rows, f"the verdict on {occ} disappeared"
        assert rows[occ]["provenance"] in (r.HUMAN_USER,
                                           "IMPORTED_LEGACY_HUMAN")


# ── the media cache key does not shift ──────────────────────────────────────

def test_the_frag_proxy_key_does_not_depend_on_geography():
    """A clip already rendered must not turn back into a spinner because
    this sprint taught the system where it happened."""
    from creative_suite.engine import review_proxy as rp
    import inspect
    src = inspect.getsource(rp.proxy_key)
    for word in ("region", "map_", "geograph", "location"):
        assert word not in src.lower(), f"proxy key now depends on {word}"


@live
def test_the_source_ladder_is_stable_for_the_reviewed_items():
    """FRAGMENT SOURCE PREFERENCE STABLE. These three already have human
    verdicts on them; the recording their round is read from must not start
    flip-flopping."""
    from engine.parser import demo_lineage as dl
    for occ in (495, 1080, 18858):
        a = dl.canonical_source_for(occ)
        b = dl.canonical_source_for(occ)
        assert a == b, f"the source for {occ} is not deterministic"
        assert a is not None
        assert a.reason in (dl.UNCHANGED, dl.COMPLETE_SOURCE, dl.BEST_POV,
                            dl.ONLY_FRAGMENT)


@live
def test_a_fragment_is_preferred_only_when_nothing_fuller_saw_the_moment():
    from engine.parser import demo_lineage as dl
    with sqlite3.connect(f"file:{RECOG_DB.as_posix()}?mode=ro",
                         uri=True) as c:
        c.row_factory = sqlite3.Row
        occs = [r["occurrence_id"] for r in c.execute(
            "SELECT occurrence_id FROM kill_occurrences_v1 LIMIT 300")]
    reasons = {}
    for occ in occs:
        s = dl.canonical_source_for(int(occ))
        if s is not None:
            reasons[s.reason] = reasons.get(s.reason, 0) + 1
    assert reasons, "the ladder answered for nothing at all"
    # A fragment is a legitimate answer; it is never DELETED, only never
    # asked to describe boundaries it cannot see.
    for r in reasons:
        assert r in (dl.UNCHANGED, dl.COMPLETE_SOURCE, dl.BEST_POV,
                     dl.ONLY_FRAGMENT)


def test_legacy_fragments_are_never_deleted():
    src = (REPO_ROOT / "engine" / "parser"
           / "demo_lineage.py").read_text(encoding="utf-8")
    assert "DELETE FROM kill_events_v1" not in src
    assert "DELETE FROM kill_occurrences_v1" not in src


# ── the fifty-review checkpoint ─────────────────────────────────────────────

@live
def test_the_checkpoint_is_a_reading_and_never_a_rule():
    """Section 20: produce a curation analysis, do not change the queue.

    Both halves. A system that reads a few dozen human decisions and then
    reorders the queue to match stops showing the user anything that would
    change their mind.
    """
    from creative_suite.engine import curation_checkpoint as cc
    before = [i.item_id for i in rc.queue(limit=40, corpus="USER_FRAGS")]
    report = cc.analyse().to_dict()
    after = [i.item_id for i in rc.queue(limit=40, corpus="USER_FRAGS")]
    assert before == after, "the checkpoint moved the queue"
    assert report["checkpoint_at"] == 50
    assert report["due"] is (report["reviewed"] >= 50)


def test_the_checkpoint_module_cannot_write():
    """No writer, and no argument that could become one."""
    import inspect
    from creative_suite.engine import curation_checkpoint as cc
    src = inspect.getsource(cc)
    for word in ("INSERT", "UPDATE ", "DELETE", "commit()", "record("):
        assert word not in src, f"the checkpoint can {word}"


@live
def test_the_checkpoint_counts_only_the_user_s_own_verdicts():
    from creative_suite.engine import curation_checkpoint as cc
    ids = cc.human_reviewed_occurrence_ids()
    assert set((495, 1080, 18858)).issubset(set(ids))
