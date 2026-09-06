"""A round with several actions is a scene, not several unrelated clips."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from creative_suite.engine import scene as sc          # noqa: E402
from creative_suite.engine import review_corpus as rc   # noqa: E402


def test_round_zero_is_not_a_round():
    """Round 0 is the sentinel for a demo with no round system. Grouping by
    it produced a 'round' with 105 user frags spanning a whole match, which
    as a scene would be a twenty-minute video."""
    mode, why = sc.decide_mode(user_frags=105, round_no=0)
    assert mode == sc.MODE_FRAG
    assert "sentinel" in why


def test_two_user_frags_is_a_scene():
    """The user was explicit: one frag out of a sequence is useless for
    directing."""
    mode, why = sc.decide_mode(user_frags=2, round_no=11)
    assert mode == sc.MODE_SCENE and "2 user frags" in why


def test_one_frag_with_connective_action_is_still_a_scene():
    mode, why = sc.decide_mode(user_frags=1, round_no=7,
                               traits={"HIGH_SPEED_MOVEMENT"})
    assert mode == sc.MODE_SCENE and "connective" in why


def test_one_isolated_frag_stays_fast():
    mode, why = sc.decide_mode(user_frags=1, round_no=7, traits=set())
    assert mode == sc.MODE_FRAG and "isolated" in why


def test_a_scene_never_duplicates_canonical_truth():
    """F1/F2/F3 keep their own occurrence ids. The scene is a container."""
    s = _real_scene()
    frags = [e for e in s.events if e.kind == sc.E_FRAG]
    assert len(frags) >= 3
    ids = [e.occurrence_id for e in frags]
    assert len(set(ids)) == len(ids), "no duplicated occurrence"
    assert [e.frag_index for e in frags] == list(range(1, len(frags) + 1))


def test_derived_events_take_notes_but_not_verdicts():
    """Making every micro-event demand a T1-T5 would turn review into data
    entry. A movement run gets an annotation and no classification."""
    s = _real_scene(with_movement=True)
    derived = [e for e in s.events if e.kind in (sc.E_MOVEMENT, sc.E_JUMPPAD)]
    if not derived:
        pytest.skip("no movement in the sampled scene")
    for e in derived:
        assert not e.takes_verdict
        assert e.occurrence_id is None
        assert e.event_id.startswith("MOV:")
    for e in (x for x in s.events if x.kind == sc.E_FRAG):
        assert e.takes_verdict and e.event_id.startswith("OCC:")


def test_the_scene_spans_all_user_frags():
    """Never show F2 in isolation while F1 and F3 stay hidden."""
    s = _real_scene()
    frags = [e for e in s.events if e.kind == sc.E_FRAG]
    assert s.media_start_ms <= frags[0].t_ms
    assert s.media_end_ms >= frags[-1].t_ms


def test_no_content_hash_reaches_the_ui():
    assert "content_hash" not in _real_scene().to_dict()


# ── helpers ─────────────────────────────────────────────────────────────────

def _real_scene(with_movement: bool = False):
    users = sorted(rc.user_norms())
    marks = ",".join("?" * len(users))
    c = sqlite3.connect(f"file:{sc.RECOGNITION_DB}?mode=ro", uri=True)
    extra = ("AND EXISTS(SELECT 1 FROM movement_moments_v1 m "
             "WHERE m.content_hash=k.content_hash AND m.round=o.round)"
             if with_movement else "")
    row = c.execute(
        f"""SELECT k.content_hash h, o.round r FROM kill_occurrences_v1 o
            JOIN kill_events_v1 k ON k.kill_event_id=o.best_observation_id
            WHERE o.killer_class='PLAYER' AND o.killer_name_norm IN ({marks})
            AND o.round>0 {extra}
            GROUP BY 1,2 HAVING COUNT(*)>=3 LIMIT 1""", users).fetchone()
    if row is None:
        pytest.skip("no multi-frag round available")
    s = sc.build_scene(row[0], row[1])
    assert s is not None
    return s
