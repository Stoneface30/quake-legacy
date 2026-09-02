"""Corpus event taxonomy, round and team truth, and truncation at a contact."""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "engine" / "parser"))

from creative_suite.engine import demo_truth as dt, projectile_reconstruction as pr

REC_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
DEMOS = REPO_ROOT / "demos"


def _demo_for(frag_id: int) -> Path | None:
    if not REC_DB.exists():
        return None
    name = sqlite3.connect(REC_DB).execute(
        "SELECT demo_name FROM recognized_frags WHERE id=?", (frag_id,)).fetchone()
    if not name:
        return None
    p = DEMOS / name[0]
    return p if p.exists() else None


# ── round outcomes are derived, not invented ────────────────────────────────

def _rows(*items):
    return [tuple(i) for i in items]


def test_the_winner_is_the_side_whose_score_rose():
    rows = _rows((1000, 6, "0"), (1000, 7, "0"),
                 (5000, 662, "-1"), (5001, 6, "1"),
                 (9000, 662, "-1"), (9001, 7, "1"))
    out = dt.round_outcomes(rows, recorder_team="RED")
    assert [o.winner_team for o in out] == ["RED", "BLUE"]
    assert [o.result for o in out] == [dt.ROUND_WIN, dt.ROUND_LOSS]


def test_a_round_where_no_score_moved_is_unknown_not_a_draw():
    rows = _rows((1000, 6, "2"), (1000, 7, "2"), (5000, 662, "-1"))
    out = dt.round_outcomes(rows, recorder_team="RED")
    assert out[0].winner_team == dt.ROUND_UNKNOWN
    assert out[0].result == dt.ROUND_UNKNOWN


def test_both_scores_moving_at_once_is_also_unknown():
    rows = _rows((1000, 6, "0"), (1000, 7, "0"), (4000, 6, "1"), (4000, 7, "1"),
                 (5000, 662, "-1"))
    assert dt.round_outcomes(rows, recorder_team="BLUE")[0].winner_team == dt.ROUND_UNKNOWN


def test_an_unknown_recorder_team_cannot_yield_a_result():
    rows = _rows((1000, 6, "0"), (5000, 662, "-1"), (5001, 6, "1"))
    o = dt.round_outcomes(rows, recorder_team="")[0]
    assert o.winner_team == "RED" and o.result == dt.ROUND_UNKNOWN


def test_round_outcomes_are_event_constrained_derivations():
    rows = _rows((1000, 6, "0"), (5000, 662, "-1"), (5001, 6, "1"))
    assert dt.round_outcomes(rows, recorder_team="RED")[0].evidence == dt.EVENT_CONSTRAINED


def test_a_moment_maps_to_the_round_that_ends_after_it():
    rows = _rows((1000, 6, "0"), (5000, 662, "-1"), (5001, 6, "1"),
                 (9000, 662, "-1"), (9001, 6, "2"))
    out = dt.round_outcomes(rows, recorder_team="RED")
    assert dt.outcome_at(out, 3_000_000).round_index == 1
    assert dt.outcome_at(out, 7_000_000).round_index == 2
    assert dt.outcome_at(out, 20_000_000) is None


# ── the enrichment reads, when present ──────────────────────────────────────

def test_unenriched_demos_yield_no_outcomes_rather_than_an_error(tmp_path):
    db = tmp_path / "empty.db"
    sqlite3.connect(db).close()
    assert dt.load_round_outcomes("x" * 64, 0, db_path=db) == ()


# ── taxonomy on a real demo ─────────────────────────────────────────────────

@pytest.mark.skipif(_demo_for(2340) is None, reason="demo corpus not on this machine")
def test_the_parser_now_yields_movement_chat_rounds_and_missiles():
    from demo_parse import DM73Parser
    out = DM73Parser(_demo_for(2340), track_missiles=True).parse()
    types = {e["type"] for e in out["events"]}
    assert {"jump", "jump_pad", "teleport_in", "teleport_out"} <= types
    assert out["rounds"], "round tracking must survive the round-state capture"
    kinds = {t["kind"] for t in out["server_text"]}
    assert "chat" in kinds
    cs = {r["cs"] for r in out["round_results"]}
    assert {6, 7, 661, 662} <= cs
    assert any(m["removed"] for m in out["missiles"])
    assert any(not m["removed"] and m.get("other") is not None for m in out["missiles"])


@pytest.mark.skipif(_demo_for(2340) is None, reason="demo corpus not on this machine")
def test_default_parser_output_carries_no_new_side_effects():
    """Without the flag the missile track stays empty; nothing else moves."""
    from demo_parse import DM73Parser
    out = DM73Parser(_demo_for(2340)).parse()
    assert out["missiles"] == []
    assert out["rounds"]


# ── truncation at an authoritative contact ──────────────────────────────────

class _Floor:
    def __init__(self):
        from engine.parser import bsp_geometry as bg
        self.planes = [(0.0, 0.0, 1.0, 0.0), (0.0, 0.0, -1.0, 16.0),
                       (1.0, 0.0, 0.0, 4096.0), (-1.0, 0.0, 0.0, 4096.0),
                       (0.0, 1.0, 0.0, 4096.0), (0.0, -1.0, 0.0, 4096.0),
                       (0.0, 0.0, 1.0, -1_000_000.0)]
        self.brushsides = [0, 1, 2, 3, 4, 5]
        self.brushes = [(0, 6, bg.CONTENTS_SOLID)]
        self.leafbrushes = [0]
        self.leafs = [(0, 1)]
        self.nodes = [(6, -1, -1)]
        self.patch_cells = []
        self.world_brush_range = (0, 1)


def _level_rocket():
    return pr.propagate(pr.LaunchState(pr.KIND_ROCKET, 0, (0.0, 0.0, 100.0),
                                       (1.0, 0.0, 0.0), dt.ENTITY_OBSERVED),
                        _Floor())


def test_a_hit_on_the_line_cuts_the_path_without_moving_it():
    cont = _level_rocket()
    before = pr.path_point_at(cont, 500_000).pos
    cut, res = pr.truncate_at_event(cont, event_kind="missile_hit",
                                    event_t_us=500_000, event_pos=(500.0, 0.0, 100.0))
    assert res.compatible
    assert cut.end_reason == "DYNAMIC_CONTACT"
    assert cut.end_t_us == 500_000
    assert cut.end_pos == pytest.approx(before, abs=1e-6)
    assert cut.confidence == pr.DETERMINISTIC_UNTIL_UNOBSERVED_DYNAMIC_CONTACT
    assert all(p.t_us <= 500_000 for p in cut.points)
    assert cut.points[-1].evidence == dt.EVENT_CONSTRAINED


def test_a_hit_off_the_line_is_reported_and_the_path_is_left_alone():
    cont = _level_rocket()
    cut, res = pr.truncate_at_event(cont, event_kind="missile_hit",
                                    event_t_us=500_000, event_pos=(500.0, 900.0, 100.0))
    assert not res.compatible
    assert cut.end_t_us == cont.end_t_us and cut.end_pos == cont.end_pos
    assert cut.confidence == pr.AMBIGUOUS
    assert "disagree" in res.explanation


def test_an_event_outside_the_propagated_interval_is_ambiguous():
    cont = _level_rocket()
    cut, res = pr.truncate_at_event(cont, event_kind="FRAG",
                                    event_t_us=cont.end_t_us + 5_000_000,
                                    event_pos=None)
    assert not res.compatible and cut.confidence == pr.AMBIGUOUS


def test_truncation_never_promotes_provenance():
    cont = _level_rocket()
    cut, _ = pr.truncate_at_event(cont, event_kind="missile_hit",
                                  event_t_us=500_000, event_pos=(500.0, 0.0, 100.0))
    assert not any(dt.is_recorded(p.evidence) for p in cut.points[1:])
    assert cut.points[0].evidence == dt.ENTITY_OBSERVED     # the launch stays recorded
