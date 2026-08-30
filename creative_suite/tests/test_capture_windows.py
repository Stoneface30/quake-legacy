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
    assert wins[0]["capture_end_ms"] == 14000 + cw.POST_MS


def test_start_clamped_at_zero():
    wins = cw.build_windows([_kill(2000)])
    assert wins[0]["capture_start_ms"] == 0
    # offsets stay relative to the clamped start
    assert json.loads(wins[0]["frag_offsets_ms"]) == [2000]


def test_offsets_preserved_for_multikill():
    wins = cw.build_windows([_kill(20000), _kill(21500), _kill(24000)])
    offs = json.loads(wins[0]["frag_offsets_ms"])
    assert offs == [cw.PRE_MS, cw.PRE_MS + 1500, cw.PRE_MS + 4000]


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


def test_dedupe_windows_prefers_named_demo():
    w1 = {"demo": "Demo (788) - 341;.dm_73", "map": "overkill", "round": 2,
          "server_time_ms": 383575, "n_kills": 4, "frag_offsets_ms": "[1, 2]",
          "score": 46.0}
    w2 = {"demo": "CA-Gr0str4sh-overkill-2013_01_08.dm_73", "map": "overkill",
          "round": 15, "server_time_ms": 383575, "n_kills": 4,
          "frag_offsets_ms": "[1, 2]", "score": 46.0}
    out = cw.dedupe_windows([w1, w2])
    assert len(out) == 1
    assert out[0]["demo"].startswith("CA-")


def test_dedupe_windows_keeps_distinct():
    w1 = {"demo": "a.dm_73", "map": "overkill", "round": 1,
          "server_time_ms": 100, "n_kills": 1, "frag_offsets_ms": "[5]", "score": 9.0}
    w2 = {"demo": "b.dm_73", "map": "overkill", "round": 1,
          "server_time_ms": 200, "n_kills": 1, "frag_offsets_ms": "[5]", "score": 9.0}
    assert len(cw.dedupe_windows([w1, w2])) == 2


def test_dedupe_clutches_by_signature():
    c = {"canonical_demo_hash": "H1", "round": 3, "clutch_start_ms": 1000,
         "clutch_end_ms": 2000, "enemies_alive_at_start": 2,
         "kills_during_clutch": 1, "weapons": "ROCKET", "outcome": "WIN",
         "rank_score": 10.0}
    assert len(cw.dedupe_clutches([c, dict(c), dict(c, demo="othername")])) == 1
