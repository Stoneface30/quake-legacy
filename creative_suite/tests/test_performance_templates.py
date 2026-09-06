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


def _run_stop_turn(discontinuity: bool = False, airborne_end: bool = False):
    """A continuous grounded run that decelerates to a stop and turns 90."""
    from engine.pantheon.performance import (AimSample, AnimSample, PerformanceTrace,
                                             TransformSample, WeaponSample)
    tr = PerformanceTrace("f", "campgrounds", "CA", 3, 1000, 1000 + 25 * 59)
    x, speed = 0.0, 320.0
    for i in range(60):
        t = 1000 + 25 * i
        if i >= 30:
            speed = max(0.0, speed - 40.0)
        x += speed * 0.025
        if discontinuity and i == 20:
            x += 1294.0
        air = airborne_end and i >= 55
        tr.transform.append(TransformSample(t, (x, 0.0, 24.0), (speed, 0.0, 0.0), speed,
                                            air, 1023 if air else 1022))
        yaw = 0.0 if i < 40 else min(90.0, (i - 40) * 12.0)
        tr.aim.append(AimSample(t, yaw, 0.0, 0.0, 0.0))
        tr.animation.append(AnimSample(t, 15 if speed > 50 else 22, 11, False, False))
    tr.weapon.append(WeaponSample(1000, 5))
    return tr


def test_run_in_stop_turn_requires_physical_continuity():
    good = PT.derive(_run_stop_turn())
    assert any(t.grp == "RUN_IN_STOP_TURN" for t in good), [t.grp for t in good]
    assert all(t.ending_stance != "AIRBORNE" for t in good if t.grp == "RUN_IN_STOP_TURN")
    bad = PT.derive(_run_stop_turn(discontinuity=True))
    assert not any(t.grp in ("RUN_IN", "RUN_STOP", "RUN_IN_STOP_TURN") for t in bad), \
        [t.grp for t in bad]
    tr = _run_stop_turn()
    assert PT.admissible(tr, tr.start_ms, tr.end_ms, "RUN_IN_STOP_TURN") is None
    assert "discontinuity" in PT.admissible(_run_stop_turn(discontinuity=True), 1000, 1000 + 25 * 59,
                                            "RUN_IN")
    assert PT.admissible(_run_stop_turn(airborne_end=True), 1000, 1000 + 25 * 59,
                         "RUN_IN_STOP_TURN") == "ends airborne"
    # a jump-pad flight is not a grounded run
    assert PT.admissible(jumppad_rocket_trace(), 500_000, 500_000 + 25 * 59, "RUN_IN") is not None


def test_a_template_is_a_reference_to_a_real_trace_never_an_average():
    """The library indexes REAL segments. A synthesized median curve would
    give every character the same robotic motion; a reference keeps one
    person's timing."""
    import ast
    from pathlib import Path
    # CODE only: the docstring is allowed to say why averaging is wrong.
    tree = ast.parse(Path(PT.__file__).read_text(encoding="utf-8"))
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", "")
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for word in ("mean", "median", "average", "fmean", "interp", "smooth", "resample"):
        assert word not in called, f"the template library calls {word}()"
    t = PT.derive(jumppad_rocket_trace())[0]
    row = set(t.as_dict())
    # a template row names a window; it carries no sample series of its own
    assert {"demo_hash", "client", "start_ms", "end_ms"} <= row
    assert not (row & {"transform", "aim", "animation", "samples", "path"})
    # and loading one returns the recorded samples, unmodified
    seg = PT._segment(jumppad_rocket_trace(), t.start_ms, t.end_ms)
    original = {s.t: s.origin for s in jumppad_rocket_trace().transform}
    assert seg.transform and all(s.origin == original[s.t] for s in seg.transform)
