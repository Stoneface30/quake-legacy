"""The rebuild, and the human data it is not allowed to disturb.

MACHINE-DERIVED DATA MAY BE REBUILT. HUMAN DATA MAY NOT. The two live in
different databases, but the reviewer reads them together: a verdict is
addressed by an OCCURRENCE ID, and occurrence ids are machine-derived. A
rebuild that renumbered them would leave every human row intact, still
saying `T4_KEEP_NORMAL`, now describing a different kill -- and nothing would
error, no count would change, and the reviewer would look fine.

These tests are what stands between that and a promotion.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

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


# ── enumeration ─────────────────────────────────────────────────────────────

def test_synthetic_demos_are_not_corpus():
    """The prologue worktree writes .dm_73 files as test fixtures.

    Mining one would put invented gameplay into the historical record, which
    is the single worst thing a rebuild could do.
    """
    assert not me.is_corpus(Path(".claude/worktrees/x/.tmp/fake.dm_73"))
    assert not me.is_corpus(Path("output/demo_v2/scratch.dm_73"))
    assert me.is_corpus(Path("demos/CA-something-2012.dm_73"))


@live
def test_the_corpus_is_enumerated_by_content_not_by_name():
    """Quake Live names demos `Demo (417).dm_73`.

    2,153 of the 6,445 files on disk have no row in the frag database, which
    looks like a third of the archive was never mined. Every one of them is a
    byte-identical re-save of a demo that WAS mined. A filename inventory
    would have ordered a pointless 33% re-parse; a content-hash inventory
    said the corpus was already complete.
    """
    st = me.status()
    assert st["distinct_demos"] > 0
    assert st["never_mined"] == 0, (
        f"{st['never_mined']} distinct demos have never been mined")


# ── human data is untouched ─────────────────────────────────────────────────

@live
def test_every_human_target_still_points_at_the_same_event():
    """The gate. Promotion is blocked unless this is clean.

    Identity is the kill fingerprint -- map, time, killer, victim, means of
    death -- not the id, because the id is the thing under suspicion.
    """
    out = hm.check()
    assert out["blocked"] is False, out["blockers"]
    assert set(out["by_status"]) <= {hm.EXACT}, out["by_status"]


@live
def test_the_migration_check_can_actually_fail(monkeypatch):
    """Guard the guard.

    A check that returns EXACT because it looked at nothing would pass every
    promotion for ever.
    """
    monkeypatch.setattr(hm, "fingerprints",
                        lambda ids, db=None: {} if ids else {})
    out = hm.check()
    if out["human_targets"]:
        assert out["blocked"] is True
        assert out["by_status"].get(hm.MISSING)


@live
def test_promotion_is_additive_and_reversible():
    """Nothing existing is dropped, renamed or renumbered.

    That is precisely why the migration check comes out EXACT: the layer
    every verdict is addressed by is not touched at all.
    """
    with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
        names = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    for core in ("kill_events_v1", "kill_occurrences_v1", "semantic_events_v1",
                 "recognized_frags", "movement_moments_v1"):
        assert core in names, f"{core} disappeared in the rebuild"
    assert set(me.PROMOTED_TABLES) <= names


# ── actions are not frags ───────────────────────────────────────────────────

@live
def test_an_action_is_never_a_frag():
    """Separate namespace, separate denominator.

    `ACTION:41` and `USER_FRAG:41` are different moments and the id says
    which. An action that leaked into a frag queue would inflate a frag count
    with something nobody was killed by.
    """
    frags = {i.item_id for i in rc.queue(limit=200, item_type=rc.USER_FRAG,
                                         corpus=rc.USER_FRAGS)}
    actions = {i.item_id for i in rc.queue(limit=200, item_type=rc.ACTION,
                                           corpus=rc.NO_KILL_ACTIONS)}
    assert actions, "no reviewable actions"
    assert not (frags & actions)
    assert all(i.startswith("ACTION:") for i in actions)
    assert rc.count_items(rc.USER_FRAG, corpus=rc.USER_FRAGS) != \
        rc.count_items(rc.ACTION, corpus=rc.NO_KILL_ACTIONS)


@live
def test_a_no_kill_action_contains_no_kill():
    """The whole point of the family.

    A burst that ends in a frag is FRAG_BUILDUP_CONTEXT and belongs to that
    frag's story; it must not also be offered as an action in its own right,
    or one moment becomes two review targets.
    """
    with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
        bad = c.execute(
            "SELECT COUNT(*) FROM action_moments_v1 WHERE ends_in_kill = 1 "
            "AND classes LIKE '%TRUE_NO_KILL_ACTION%'").fetchone()[0]
    assert bad == 0
    for it in rc.queue(limit=50, item_type=rc.ACTION,
                       corpus=rc.NO_KILL_ACTIONS):
        d = rc.action_detail(it.source_id)
        assert d["ends_in_kill"] == 0


@live
def test_an_action_never_claims_damage():
    """Pain is throttled and proves damage, not whose.

    Quake Live demos carry no damage figure for another player, so no field
    may be called damage and every count must be labelled as observed.
    """
    d = rc.action_detail(
        rc.queue(limit=1, item_type=rc.ACTION,
                 corpus=rc.NO_KILL_ACTIONS)[0].source_id)
    assert "observed_pain" in d
    assert not any("damage" in k.lower() for k in d)
    assert "LOWER BOUND" in d["note"]
    assert d["confidence"] in ("HIGH", "AMBIGUOUS")


@live
def test_only_confident_actions_are_offered():
    """At the median the actor fired 18% of the shots in the window.

    Offering AMBIGUOUS bursts would be showing the reviewer other people's
    fights and calling them theirs.
    """
    for it in rc.queue(limit=40, item_type=rc.ACTION,
                       corpus=rc.NO_KILL_ACTIONS):
        assert rc.action_detail(it.source_id)["confidence"] == "HIGH"


@live
def test_warmup_stays_out_of_the_action_queue_too():
    with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
        for it in rc.queue(limit=60, item_type=rc.ACTION,
                           corpus=rc.NO_KILL_ACTIONS):
            r = c.execute("SELECT round FROM action_moments_v1 WHERE "
                          "action_id=?", (it.source_id,)).fetchone()
            assert r[0] != 0 or r[0] is None


# ── aim ─────────────────────────────────────────────────────────────────────

@live
def test_a_flick_is_rare_by_construction():
    """DO NOT CALL EVERYTHING A FLICK.

    The first thresholds were FLICK at 400 deg/s -- the MEDIAN gesture -- and
    would have labelled half of all mouse movement in the archive a flick. A
    tag that fires on the median carries no information.
    """
    from engine.parser import mine_aim_events as ae
    with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
        total = c.execute("SELECT COUNT(*) FROM aim_events_v1").fetchone()[0]
        flicks = c.execute(
            "SELECT COUNT(*) FROM aim_events_v1 WHERE classes LIKE "
            "'%FLICK%'").fetchone()[0]
    assert total > 0
    assert flicks / total < 0.10, (
        f"{flicks}/{total} gestures called a flick -- the threshold is too low")
    assert ae.FLICK_DPS > 1000 and ae.HIGH_FLICK_DPS > ae.FLICK_DPS


def test_a_view_snap_is_not_a_flick():
    """Respawning and spectating move the camera instantly.

    Without excluding them the measured peak was 14,000 deg/s -- no hand
    moves a mouse that fast, and every demo became one gesture.
    """
    from engine.parser import mine_aim_events as ae
    series = [(0, 0.0, 0.0), (40, 20.0, 0.0), (80, 40.0, 0.0),
              (120, 200.0, 0.0),          # a 160-degree snap in one frame
              (160, 220.0, 0.0), (200, 240.0, 0.0), (240, 260.0, 0.0)]
    for g in ae.gestures(series):
        assert g["peak_dps"] < 5000, "a view snap became a gesture peak"


def test_a_gesture_ends_when_the_aim_goes_quiet():
    from engine.parser import mine_aim_events as ae
    moving = [(t, t * 1.5, 0.0) for t in range(0, 400, 40)]
    still = [(t, 600.0, 0.0) for t in range(400, 900, 40)]
    again = [(t, 600.0 + (t - 900) * 1.5, 0.0) for t in range(900, 1300, 40)]
    g = ae.gestures(moving + still + again)
    assert len(g) == 2, f"expected two gestures, got {len(g)}"
