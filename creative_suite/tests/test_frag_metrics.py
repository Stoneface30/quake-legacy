"""Named frag metrics -- never one field called "kills".

The old late-2012 regression recorded "117 raw / 63 filtered" against a single
overloaded notion of a kill. That pair does not reproduce. The archaeology (2026-08-30): six demos yield
exactly 117 raw obituaries, and every one of them accepts 117 too. 63 is not the
recorder subset of the named fixture either -- that is 20 -- and no demo in the
corpus reports 117 raw with 63 accepted.

The only filter that exists now drops suicides (killer == victim), which is
0.63%% corpus-wide and could never turn 117 into 63. Whatever the 63 measured
was a stronger filter that no longer exists; FT-2 forbids a quality gate --
"every frag enters the corpus; tiering is for ordering, not filtering."

These tests pin the three quantities apart so the ambiguity cannot recur:

    raw_obituary_entities   every obituary event the parser emits, 215,831
    match_kills             player-vs-player kills, suicides excluded, 214,466
    recorder_kills          kills whose attacker is the demo's recorder, 36,607

The gap between the first two is suicides and world deaths (killer == victim),
1,365 rows or 0.63%. That is the ONE filtering stage in the pipeline, and it is
definitional rather than a quality gate.

They are deliberately about the RELATIONSHIPS between the metrics, not about
one fixture's magic numbers, so they stay meaningful as the corpus grows.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DB = REPO / "creative_suite" / "database" / "frags_rebuilt.db"

pytestmark = pytest.mark.skipif(
    not DB.exists(), reason="frags_rebuilt.db not built in this environment")


@pytest.fixture(scope="module")
def con():
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def test_match_kills_is_raw_obituaries_minus_suicides(con):
    """There is exactly ONE filter, and it is suicides.

    `frag_classify.classify()` drops obituaries where killer == victim: a
    player killing themselves, or dying to the world, is not a frag. Nothing
    else is dropped. Corpus-wide that gap is 1,365 of 215,831 (0.63%).

    This is the honest answer to "did the definition of an accepted kill
    change?" -- yes, and this is the whole of the change. FT-2 forbids a
    QUALITY filter (no minimum threshold, tiering orders rather than filters);
    excluding self-inflicted deaths is a definitional boundary, not a quality
    gate.
    """
    raw = con.execute("SELECT SUM(raw_obituaries) FROM demos").fetchone()[0]
    acc = con.execute("SELECT SUM(accepted_frags) FROM demos").fetchone()[0]
    assert acc <= raw, "match_kills cannot exceed raw_obituary_entities"
    gap = (raw - acc) / float(raw)
    assert gap < 0.05, (
        "{:.2%} of obituaries are being dropped -- far more than suicides "
        "account for; a quality filter may have crept in".format(gap))
    # and no demo may go the other way
    bad = con.execute("""SELECT COUNT(*) FROM demos
                         WHERE accepted_frags > raw_obituaries""").fetchone()[0]
    assert bad == 0


def test_recorder_kills_are_a_strict_subset_of_match_kills(con):
    """recorder_kills <= match_kills, always, per demo."""
    row = con.execute("""SELECT COUNT(*) FROM (
        SELECT f.demo_id, SUM(f.by_recorder) rec, COUNT(*) total
        FROM frags f GROUP BY f.demo_id HAVING rec > total)""").fetchone()[0]
    assert row == 0, "recorder_kills exceeded match_kills on {} demo(s)".format(row)


def test_the_three_metrics_are_distinct_quantities(con):
    """They must not be silently interchangeable.

    If recorder_kills happened to equal match_kills corpus-wide, the split
    would be meaningless and the personal seek list would just be the whole
    corpus again.
    """
    total = con.execute("SELECT COUNT(*) FROM frags").fetchone()[0]
    rec = con.execute("SELECT COUNT(*) FROM frags WHERE by_recorder=1").fetchone()[0]
    assert total > 0
    assert 0 < rec < total, (
        "recorder_kills ({}) must be a proper subset of match_kills ({})"
        .format(rec, total))


def test_dedup_never_invents_kills(con):
    """frags_dedup collapses repeats; it can never produce MORE rows."""
    raw = con.execute("SELECT COUNT(*) FROM frags").fetchone()[0]
    dd = con.execute("SELECT COUNT(*) FROM frags_dedup").fetchone()[0]
    assert dd <= raw
    assert dd > 0


def test_snapshot_repeat_rate_stays_small(con):
    """The known snapshot-repeat defect is bounded.

    One kill can be re-emitted once per snapshot its event entity survives.
    Measured 2026-08-30: 282 of 214,466 rows (0.13%). This test does not assert
    the defect is gone -- it is not -- it asserts it has not grown into
    something that would distort multi-kill ranking.
    """
    raw = con.execute("SELECT COUNT(*) FROM frags").fetchone()[0]
    dd = con.execute("SELECT COUNT(*) FROM frags_dedup").fetchone()[0]
    rate = (raw - dd) / float(raw)
    assert rate < 0.02, (
        "snapshot-repeat rate {:.2%} has grown beyond the known 0.13%".format(rate))


def test_no_demo_reports_both_117_raw_and_63_accepted(con):
    """The historical pair is impossible under current semantics.

    Kept as an executable record of the archaeology, so a future reader does
    not spend the investigation again.
    """
    n = con.execute("""SELECT COUNT(*) FROM demos
                       WHERE raw_obituaries=117 AND accepted_frags=63"""
                    ).fetchone()[0]
    assert n == 0
    # ...while 117 raw on its own is perfectly ordinary
    n117 = con.execute("SELECT COUNT(*) FROM demos WHERE raw_obituaries=117"
                       ).fetchone()[0]
    assert n117 > 0, "expected some demos to yield 117 raw obituaries"
