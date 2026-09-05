"""Performance templates are real segments chosen by measured facts."""
from __future__ import annotations

from pathlib import Path

from creative_suite.tests.pantheon_fixtures import jumppad_rocket_trace
from engine.pantheon import performance_templates as PT


def test_templates_are_derived_from_the_graph_with_stable_ids():
    tpls = PT.derive(jumppad_rocket_trace())
    groups = {t.grp for t in tpls}
    assert {"JUMP_PAD", "JUMP_PAD_ROCKET", "LAND"} <= groups, groups
    for t in tpls:
        assert t.id == f"TPL:{t.grp}:{t.demo_hash}:{t.client}:{t.start_ms}"
        assert t.duration_ms == t.end_ms - t.start_ms > 0
        assert t.ending_stance in ("IDLE", "RUN", "AIRBORNE")
        assert "name" not in t.as_dict()


def test_find_ranks_by_closeness_to_the_request(tmp_path):
    db = tmp_path / "tpl.db"
    con = PT._open(db)
    import json
    rows = []
    for i, dist in enumerate((150.0, 260.0, 340.0, 900.0)):
        t = PT.PerformanceTemplate("RUN_IN", f"h{i}", 3, "campgrounds", 1000 * i, 1000 * i + 800,
                                   800, dist, 10.0 * i, "IDLE", "ROCKET", 0, 1.0, {})
        rows.append(t)
        con.execute("insert into templates values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (t.id, t.grp, t.demo_hash, t.client, t.map, t.start_ms, t.end_ms, t.duration_ms,
                     t.distance_u, t.heading_delta_deg, t.ending_stance, t.weapon, t.airborne_ms,
                     t.grounded_fraction, json.dumps(t.features)))
    con.commit(); con.close()
    got = PT.find("RUN_IN", distance=(200.0, 350.0), db=db)
    assert [t.distance_u for t in got] == [260.0, 340.0]      # 150 and 900 filtered out
    assert got[0].distance_u == 260.0                         # nearest the middle first
    assert PT.find("RUN_IN", ending_stance="RUN", db=db) == []
    assert PT.counts(db) == {"RUN_IN": 4}
