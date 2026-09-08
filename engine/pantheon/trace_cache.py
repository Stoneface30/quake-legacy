"""WHICH TRACES EARN A STORED COPY.

The compact index keeps discovery rows and a locator; a trace is rebuilt from
the demo on demand, which is why the whole corpus fits in a database instead
of ninety-four gigabytes of stored traces. Rebuilding costs a demo parse, so a
few traces are worth keeping -- and the question this module answers is WHICH,
because "cache what we touched" is how the ninety-four gigabytes happened.

Four reasons earn a copy, and only these:

    TEMPLATE   a reusable motion the template library points at
    GOLDEN     a regression fixture: a proof depends on it not changing
    SELECTED   a human or a director chose this moment for the film
    FREQUENT   reconstructed often enough that rebuilding it is the waste

The first three are DURABLE: they were chosen deliberately, and eviction never
touches them. FREQUENT is earned by use and lost the same way, so the cache
cannot grow without bound and cannot quietly evict a proof's fixture.

Use is counted where traces are actually fetched, not where they are
mentioned, so "frequent" means frequently REBUILT rather than frequently
named.
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from enum import Enum

from engine.pantheon import performance_index as PI
from engine.pantheon import store as S

# A trace of a two-second action compresses to a few tens of kilobytes; the
# budget is what the durable reasons need plus room for the working set.
BUDGET_BYTES = 512 * 1024 * 1024
FREQUENT_AFTER = 3            # rebuilds before a locator earns a copy

USE_SCHEMA = """
create table if not exists uses (
  locator text primary key, n integer not null default 0,
  first_at real, last_at real);
"""


class Reason(str, Enum):
    TEMPLATE = "TEMPLATE"
    GOLDEN = "GOLDEN"
    SELECTED = "SELECTED"
    FREQUENT = "FREQUENT"


DURABLE = (Reason.TEMPLATE, Reason.GOLDEN, Reason.SELECTED)


def _open() -> sqlite3.Connection:
    con = sqlite3.connect(S.trace_cache_db(), timeout=120)
    con.executescript(PI.CACHE_SCHEMA)
    con.executescript(USE_SCHEMA)
    return con


# -- counting use -----------------------------------------------------------

def note_use(locator: str) -> int:
    """One rebuild of this locator. Returns the running count."""
    now = time.time()
    con = _open()
    try:
        con.execute(
            "insert into uses(locator, n, first_at, last_at) values(?,1,?,?) "
            "on conflict(locator) do update set n = n + 1, last_at = excluded.last_at",
            (locator, now, now))
        con.commit()
        (n,) = con.execute("select n from uses where locator=?", (locator,)).fetchone()
    finally:
        con.close()
    return int(n)


def uses(locator: str) -> int:
    con = _open()
    try:
        row = con.execute("select n from uses where locator=?", (locator,)).fetchone()
    finally:
        con.close()
    return int(row[0]) if row else 0


def trace(locator: str, *, reason: Reason | None = None):
    """The one entry point a caller should use to get a trace.

    Counts the fetch, serves a stored copy when there is one, and stores the
    result when a reason says so -- either the caller's, or FREQUENT once the
    locator has been rebuilt often enough to make rebuilding the waste.
    """
    n = note_use(locator)
    have = PI.cached(locator)
    if have is not None:
        return have
    tr = PI.reconstruct(locator)
    if reason is not None:
        PI.cache_trace(tr, reason=reason.value)
    elif n >= FREQUENT_AFTER:
        PI.cache_trace(tr, reason=Reason.FREQUENT.value)
    return tr


def keep(locator: str, reason: Reason):
    """Store this trace deliberately. Durable reasons survive eviction."""
    tr = PI.cached(locator) or PI.reconstruct(locator)
    PI.cache_trace(tr, reason=reason.value)
    return tr


# -- filling the cache from the things that already chose ------------------

def warm_templates(*, limit: int | None = None) -> dict:
    """Every template's source segment. A template IS a claim that this motion
    will be reused, so it is the clearest case for a stored copy."""
    from engine.pantheon import performance_templates as PT
    con = sqlite3.connect(f"file:{S.template_db().as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "select demo_hash, client, start_ms, end_ms from templates"
            + (f" limit {int(limit)}" if limit else "")).fetchall()
    finally:
        con.close()
    done, failed = 0, 0
    for demo_hash, client, start_ms, end_ms in rows:
        loc = PI.locator(demo_hash, client, start_ms, end_ms)
        try:
            keep(loc, Reason.TEMPLATE)
            done += 1
        except Exception:
            failed += 1                     # a demo that has moved or gone
    return {"templates": len(rows), "cached": done, "unavailable": failed}


def warm(locators: dict[str, Reason]) -> dict:
    """Store a named set: {locator: reason}. Used for golden fixtures and for
    whatever the director has selected."""
    done, failed = 0, 0
    for loc, reason in locators.items():
        try:
            keep(loc, reason)
            done += 1
        except Exception:
            failed += 1
    return {"asked": len(locators), "cached": done, "unavailable": failed}


def normalise_reasons() -> dict:
    """Bring free-text reasons written before the vocabulary existed into it.

    The cache held 10,710 traces labelled "template" -- a real reason, spelt
    before there was a list of them. Anything that maps by name is renamed;
    anything else is left alone and reported, because silently relabelling a
    reason nobody recognises would hide exactly what this check is for.
    """
    known = {r.value: r for r in Reason}
    con = _open()
    try:
        rows = con.execute("select distinct reason from traces").fetchall()
        renamed, unknown = {}, []
        for (raw,) in rows:
            if raw in known:
                continue
            up = str(raw or "").strip().upper()
            if up in known:
                n = con.execute("update traces set reason=? where reason=?",
                                (up, raw)).rowcount
                renamed[f"{raw} -> {up}"] = n
            else:
                unknown.append(raw)
        con.commit()
    finally:
        con.close()
    return {"renamed": renamed, "unrecognised": unknown}


# -- keeping it bounded -----------------------------------------------------

@dataclass
class Eviction:
    before_bytes: int
    after_bytes: int
    dropped: int
    kept_durable: int

    def as_dict(self) -> dict:
        return {"before_bytes": self.before_bytes, "after_bytes": self.after_bytes,
                "dropped": self.dropped, "kept_durable": self.kept_durable}


def evict(*, budget: int = BUDGET_BYTES) -> Eviction:
    """Bring the cache under budget by dropping FREQUENT entries only.

    A deliberate copy is never dropped to make room for an earned one: a
    regression fixture that vanishes because the working set grew is a proof
    that quietly stopped proving anything. If the durable copies alone exceed
    the budget, the cache stays over and the caller is told.
    """
    con = _open()
    try:
        rows = con.execute(
            "select t.content_key, t.locator, length(t.blob), t.reason, "
            "       coalesce(u.n, 0), coalesce(u.last_at, t.created_at) "
            "from traces t left join uses u on u.locator = t.locator").fetchall()
        total = sum(r[2] for r in rows)
        durable = sum(r[2] for r in rows if r[3] in {d.value for d in DURABLE})
        before, dropped = total, 0
        # least used first, then least recently used
        droppable = sorted((r for r in rows if r[3] not in {d.value for d in DURABLE}),
                           key=lambda r: (r[4], r[5]))
        for key, _loc, size, _reason, _n, _at in droppable:
            if total <= budget:
                break
            con.execute("delete from traces where content_key=?", (key,))
            total -= size
            dropped += 1
        con.commit()
    finally:
        con.close()
    return Eviction(before, total, dropped, durable)


def report() -> dict:
    con = _open()
    try:
        by_reason = {r[0]: {"traces": r[1], "bytes": r[2]} for r in con.execute(
            "select reason, count(*), sum(length(blob)) from traces group by reason")}
        total = con.execute("select count(*), coalesce(sum(length(blob)), 0) "
                            "from traces").fetchone()
        hot = con.execute("select locator, n from uses order by n desc limit 5").fetchall()
        tracked = con.execute("select count(*) from uses").fetchone()[0]
    finally:
        con.close()
    return {"db": str(S.trace_cache_db()), "traces": total[0], "bytes": total[1],
            "budget_bytes": BUDGET_BYTES, "by_reason": by_reason,
            "locators_seen": tracked,
            "most_rebuilt": [{"locator": l, "uses": n} for l, n in hot],
            "frequent_after": FREQUENT_AFTER}


def main() -> int:                                           # pragma: no cover
    import argparse
    import json
    ap = argparse.ArgumentParser(description="the trace cache: what is kept and why")
    ap.add_argument("--warm-templates", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--evict", action="store_true")
    ap.add_argument("--normalise", action="store_true")
    a = ap.parse_args()
    out = {}
    if a.warm_templates:
        out["warm_templates"] = warm_templates(limit=a.limit)
    if a.normalise:
        out["normalise"] = normalise_reasons()
    if a.evict:
        out["evict"] = evict().as_dict()
    out["report"] = report()
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
