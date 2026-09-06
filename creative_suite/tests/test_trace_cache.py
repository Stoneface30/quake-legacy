"""A cache that keeps everything is how ninety-four gigabytes happened."""
from __future__ import annotations

import sqlite3

import pytest

from engine.pantheon import performance_index as PI
from engine.pantheon import trace_cache as TC


@pytest.fixture
def cache(tmp_path, monkeypatch):
    """A private cache database, and reconstruct() stubbed so no demo is read."""
    db = tmp_path / "trace_cache.db"
    monkeypatch.setattr(TC.S, "trace_cache_db", lambda: db)
    monkeypatch.setattr(PI.S, "trace_cache_db", lambda: db)
    built: list[str] = []

    class FakeTrace:
        def __init__(self, loc):
            self.loc = loc
            self.demo_hash, c, s, e = loc.split(":")[1:5] if loc.count(":") >= 4 \
                else ("h", "0", "0", "1")
            self.client, self.start_ms, self.end_ms = int(c), int(s), int(e)
            self.transform = [0] * 10

        def as_dict(self):
            return {"loc": self.loc, "pad": "x" * 4096}

    monkeypatch.setattr(PI, "reconstruct", lambda loc: (built.append(loc),
                                                        FakeTrace(loc))[1])
    monkeypatch.setattr(PI.PerformanceTrace, "from_dict",
                        staticmethod(lambda d: FakeTrace(d["loc"])), raising=False)
    return db, built


def _loc(i: int) -> str:
    return PI.locator(f"hash{i:04d}", 1, 10000, 12300)


def _rows(db):
    con = sqlite3.connect(db)
    try:
        return con.execute("select locator, reason, length(blob) from traces").fetchall()
    finally:
        con.close()


# -- what earns a copy ------------------------------------------------------

def test_one_fetch_does_not_earn_a_stored_copy(cache):
    db, built = cache
    TC.trace(_loc(1))
    assert _rows(db) == [], "a trace fetched once was stored anyway"
    assert built == [_loc(1)]


def test_a_locator_rebuilt_often_enough_earns_one(cache):
    db, built = cache
    for _ in range(TC.FREQUENT_AFTER):
        TC.trace(_loc(1))
    rows = _rows(db)
    assert len(rows) == 1 and rows[0][1] == "FREQUENT"
    assert len(built) == TC.FREQUENT_AFTER


def test_a_stored_copy_stops_the_rebuilding(cache):
    db, built = cache
    TC.keep(_loc(1), TC.Reason.GOLDEN)
    before = len(built)
    for _ in range(5):
        TC.trace(_loc(1))
    assert len(built) == before, "the cache was consulted but the trace was rebuilt"


def test_a_caller_can_name_the_reason(cache):
    db, _ = cache
    TC.trace(_loc(1), reason=TC.Reason.SELECTED)
    assert _rows(db)[0][1] == "SELECTED"


def test_use_is_counted_per_locator(cache):
    TC.trace(_loc(1))
    TC.trace(_loc(1))
    TC.trace(_loc(2))
    assert TC.uses(_loc(1)) == 2 and TC.uses(_loc(2)) == 1
    assert TC.uses(_loc(3)) == 0


# -- what eviction may touch ------------------------------------------------

def test_eviction_never_drops_a_deliberate_copy(cache):
    db, _ = cache
    for i, reason in enumerate(TC.DURABLE):
        TC.keep(_loc(i), reason)
    for i in range(10, 20):
        TC.keep(_loc(i), TC.Reason.FREQUENT)
    ev = TC.evict(budget=1)                     # a budget nothing can meet
    kept = {r[1] for r in _rows(db)}
    assert kept == {d.value for d in TC.DURABLE}
    assert ev.dropped == 10
    assert ev.after_bytes > 1, "durable copies were dropped to meet the budget"


def test_eviction_stops_once_it_is_under_budget(cache):
    db, _ = cache
    for i in range(10):
        TC.keep(_loc(i), TC.Reason.FREQUENT)
    rows = _rows(db)
    one = rows[0][2]
    ev = TC.evict(budget=one * 6)
    assert 0 < ev.dropped < 10 and ev.after_bytes <= one * 6


def test_the_least_used_goes_first(cache):
    db, _ = cache
    for i in range(4):
        TC.keep(_loc(i), TC.Reason.FREQUENT)
    for _ in range(9):
        TC.note_use(_loc(3))                    # this one is worth keeping
    TC.evict(budget=_rows(db)[0][2] * 2)
    kept = {r[0] for r in _rows(db)}
    assert _loc(3) in kept


def test_a_budget_that_durable_copies_alone_exceed_is_reported_not_forced(cache):
    db, _ = cache
    for i in range(5):
        TC.keep(_loc(i), TC.Reason.TEMPLATE)
    ev = TC.evict(budget=10)
    assert ev.dropped == 0 and ev.after_bytes == ev.before_bytes
    assert ev.kept_durable == ev.after_bytes


# -- warming from the things that already chose -----------------------------

def test_templates_are_warmed_by_their_own_segments(cache, tmp_path, monkeypatch):
    db, _ = cache
    tpl_db = tmp_path / "templates.db"
    con = sqlite3.connect(tpl_db)
    con.executescript(
        "create table templates (id text primary key, grp text, demo_hash text,"
        " client integer, map text, start_ms integer, end_ms integer);")
    for i in range(3):
        con.execute("insert into templates values(?,?,?,?,?,?,?)",
                    (f"TPL:{i}", "RUN", f"hash{i:04d}", 1, "asylum", 10000, 12300))
    con.commit()
    con.close()
    monkeypatch.setattr(TC.S, "template_db", lambda: tpl_db)
    out = TC.warm_templates()
    assert out == {"templates": 3, "cached": 3, "unavailable": 0}
    assert {r[1] for r in _rows(db)} == {"TEMPLATE"}


def test_a_demo_that_has_gone_is_counted_not_raised(cache, tmp_path, monkeypatch):
    tpl_db = tmp_path / "templates.db"
    con = sqlite3.connect(tpl_db)
    con.executescript(
        "create table templates (id text primary key, grp text, demo_hash text,"
        " client integer, map text, start_ms integer, end_ms integer);")
    con.execute("insert into templates values('TPL:0','RUN','gone',1,'m',1,2)")
    con.commit()
    con.close()
    monkeypatch.setattr(TC.S, "template_db", lambda: tpl_db)

    def boom(loc):
        raise FileNotFoundError("demo missing")

    monkeypatch.setattr(PI, "reconstruct", boom)
    assert TC.warm_templates()["unavailable"] == 1


def test_the_report_says_what_is_kept_and_why(cache):
    TC.keep(_loc(1), TC.Reason.GOLDEN)
    TC.keep(_loc(2), TC.Reason.FREQUENT)
    TC.note_use(_loc(2))
    rep = TC.report()
    assert rep["traces"] == 2 and rep["bytes"] > 0
    assert set(rep["by_reason"]) == {"GOLDEN", "FREQUENT"}
    assert rep["budget_bytes"] == TC.BUDGET_BYTES
    assert rep["most_rebuilt"][0]["locator"] == _loc(2)
