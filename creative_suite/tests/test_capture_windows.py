"""Task 3 — recorder capture windows (charter §5, §9, §17, §6)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine" / "parser"))

import capture_windows as cw


def _kill(t, score=5.0, **kw):
    base = dict(demo="d1.dm_73", map_name="overkill", server_time_ms=t,
                clock="1:00", round=1, weapon_name="ROCKET", tags="", rank_score=score)
    base.update(kw)
    return base


def test_merge_within_gap():
    wins = cw.build_windows([_kill(10000), _kill(14000), _kill(30000)])
    assert len(wins) == 2
    assert wins[0]["n_kills"] == 2
    assert wins[0]["capture_start_ms"] == 10000 - cw.PRE_MS
    assert wins[0]["capture_end_ms"] == 14000 + cw.POST_MS + 1000  # <3 kills: +1s post


def test_start_clamped_at_zero():
    wins = cw.build_windows([_kill(2000)])
    assert wins[0]["capture_start_ms"] == 0
    # offsets stay relative to the clamped start
    assert json.loads(wins[0]["frag_offsets_ms"]) == [2000]


def test_offsets_preserved_for_multikill():
    wins = cw.build_windows([_kill(20000), _kill(21500), _kill(24000)])
    offs = json.loads(wins[0]["frag_offsets_ms"])
    pre = cw.PRE_MS + 1000  # 3+ kills get extended setup context
    assert offs == [pre, pre + 1500, pre + 4000]


def test_primary_fields_from_best_kill():
    wins = cw.build_windows([_kill(20000, score=3.0, round=2, weapon_name="GAUNTLET"),
                             _kill(23000, score=9.0, round=3, weapon_name="RAILGUN")])
    w = wins[0]
    assert w["server_time_ms"] == 23000
    assert w["round"] == 3
    assert w["weapon"] == "RAILGUN"


def test_clutch_extension_and_remerge():
    # two chains separated by 8s (> CHAIN_GAP_MS) but inside one clutch
    kills = [_kill(100000), _kill(112000)]
    clutch = {"canonical_demo_hash": "H1", "round": 1, "clutch_start_ms": 95000,
              "clutch_end_ms": 115000, "enemies_alive_at_start": 3,
              "kills_during_clutch": 2, "weapons": "ROCKET,RAILGUN",
              "outcome": "WIN", "rank_score": 20.0}
    wins = cw.build_windows(kills, clutches=[clutch], demo_hash="H1")
    assert len(wins) == 1, "clutch windows must re-merge into one"
    w = wins[0]
    assert w["capture_start_ms"] == 95000 - cw.PRE_MS
    assert w["capture_end_ms"] == 115000 + cw.POST_CLUTCH_MS
    assert json.loads(w["clutch_context"])["enemies_alive_at_start"] == 3
    assert w["n_kills"] == 2


def test_score_monotone_in_kills():
    solo = cw.build_windows([_kill(10000, score=8.0)])[0]["score"]
    duo = cw.build_windows([_kill(10000, score=8.0), _kill(12000, score=4.0)])[0]["score"]
    assert duo > solo


def test_clutch_bonus_applied():
    kills = [_kill(100000, score=8.0)]
    clutch = {"canonical_demo_hash": "H1", "round": 1, "clutch_start_ms": 98000,
              "clutch_end_ms": 103000, "enemies_alive_at_start": 4,
              "kills_during_clutch": 1, "weapons": "ROCKET", "outcome": "WIN",
              "rank_score": 15.0}
    plain = cw.build_windows(kills)[0]["score"]
    clutched = cw.build_windows(kills, clutches=[clutch], demo_hash="H1")[0]["score"]
    assert clutched == plain + 2.0 * 4


def _win(demo, start, offsets, score=10.0):
    return {"demo": demo, "map": "overkill", "capture_start_ms": start,
            "server_time_ms": start + offsets[0], "n_kills": len(offsets),
            "frag_offsets_ms": json.dumps(offsets), "score": score}


def test_match_groups_by_shared_kill_tuples():
    groups = cw.build_match_groups({
        "a.dm_73": [("q", 1000, 1, 2, 7), ("q", 2000, 1, 3, 7), ("q", 3000, 2, 1, 6)],
        "b.dm_73": [("q", 1000, 1, 2, 7), ("q", 2000, 1, 3, 7), ("q", 3000, 2, 1, 6),
                    ("q", 9000, 4, 5, 1)],
        "c.dm_73": [("q", 1000, 9, 9, 7)],
    })
    assert groups["a.dm_73"] == groups["b.dm_73"]
    assert groups["c.dm_73"] != groups["a.dm_73"]


def test_match_groups_need_min_shared():
    # 2 shared tuples < MIN_SHARED_TUPLES: same map+serverTime coincidence
    groups = cw.build_match_groups({
        "a.dm_73": [("q", 1000, 1, 2, 7), ("q", 2000, 1, 3, 7)],
        "b.dm_73": [("q", 1000, 1, 2, 7), ("q", 2000, 1, 3, 7)],
    })
    assert groups["a.dm_73"] != groups["b.dm_73"]


def test_dedupe_same_match_shared_kill_collapses():
    w1 = _win("Demo (788) - 341;.dm_73", 380000, [5000], score=40.0)
    w2 = _win("CA-Gr0str4sh-overkill.dm_73", 379000, [6000], score=46.0)  # same kill @385000
    groups = {"Demo (788) - 341;.dm_73": 7, "CA-Gr0str4sh-overkill.dm_73": 7}
    out = cw.dedupe_windows([w1, w2], groups)
    assert len(out) == 1
    assert out[0]["demo"].startswith("CA-")  # higher score wins


def test_dedupe_unrelated_matches_never_merge():
    # identical map, serverTime, offsets — but different match groups
    w1 = _win("a.dm_73", 380000, [5000])
    w2 = _win("b.dm_73", 380000, [5000])
    out = cw.dedupe_windows([w1, w2], {"a.dm_73": 1, "b.dm_73": 2})
    assert len(out) == 2


def test_dedupe_same_match_different_moments_kept():
    w1 = _win("a.dm_73", 100000, [5000])
    w2 = _win("b.dm_73", 200000, [5000])
    out = cw.dedupe_windows([w1, w2], {"a.dm_73": 3, "b.dm_73": 3})
    assert len(out) == 2


def test_dedupe_clutches_by_signature():
    c = {"canonical_demo_hash": "H1", "round": 3, "clutch_start_ms": 1000,
         "clutch_end_ms": 2000, "enemies_alive_at_start": 2,
         "kills_during_clutch": 1, "weapons": "ROCKET", "outcome": "WIN",
         "rank_score": 10.0}
    assert len(cw.dedupe_clutches([c, dict(c), dict(c, demo="othername")])) == 1
