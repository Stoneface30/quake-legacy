"""How long a round actually lasted, and when it is honest to say so.

THE DEFECT THIS EXISTS TO FIX. Round duration was the span between the first
and last observed KILL in that round. A round with one observed kill
therefore has a duration of zero -- and **51.2% of all rounds in the corpus
(41,472 of 80,922) contain exactly one kill**. Half the archive was
advertising a real Clan Arena round as lasting 0.0 seconds, and the reviewer
offered to render it.

A KILL SPAN IS NOT A ROUND. The round began before the first death and ended
after the last one; both edges are invisible to a list of obituaries. The
observed span is a LOWER BOUND on the round, never its length, and calling
it the length was the whole mistake.

WHERE A REAL BOUND COMES FROM. Wolfcam's Clan Arena configstring 661 carries
`\\time\\<start>\\round\\<n>`: the server announcing when round n begins.
Where that exists the start is OBSERVED. The end is the next round's start,
or -- for the last round -- the last event seen. Where 661 is absent or
sparse, the round can still be BOUNDED by its neighbours: it cannot have
begun before the previous round's last kill, and cannot have ended after the
next round's first.

If neither gives a positive interval, the answer is UNKNOWN. It is never 0.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

# `\time\<ms>\round\<n>` inside configstring 661.
_CS_ROUND = re.compile(r"\\time\\(-?\d+)\\round\\(\d+)")
from engine.parser.protocol import ConfigString as _CS

CS_ROUND_INDEX = int(_CS.ROUND_STATUS)

OBSERVED = "OBSERVED"        # the server announced this round's start
BOUNDED = "BOUNDED"          # constrained by the neighbouring rounds
KILL_SPAN = "KILL_SPAN"      # only the deaths are known: a LOWER BOUND
UNKNOWN = "UNKNOWN"

# A Clan Arena round that produced a kill lasted longer than this. Anything
# shorter is an artefact of the derivation, not a round, and must not be
# presented as a duration at all.
MIN_CREDIBLE_MS = 1500


@dataclass(frozen=True)
class RoundBounds:
    round_no: int
    start_ms: int | None
    end_ms: int | None
    duration_ms: int | None
    provenance: str
    note: str = ""

    @property
    def credible(self) -> bool:
        """May this be shown as a round length, and rendered as one?"""
        return (self.duration_ms is not None
                and self.duration_ms >= MIN_CREDIBLE_MS)

    def to_dict(self) -> dict[str, Any]:
        return {"round_no": self.round_no, "start_ms": self.start_ms,
                "end_ms": self.end_ms, "duration_ms": self.duration_ms,
                "duration_provenance": self.provenance,
                "duration_credible": self.credible, "note": self.note}


def _conn(db: Path = RECOGNITION_DB) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def announced_starts(content_hash: str, db: Path = RECOGNITION_DB
                     ) -> dict[int, int]:
    """round number -> the server-announced start time, where stated."""
    out: dict[int, int] = {}
    with _conn(db) as c:
        for r in c.execute(
                "SELECT server_time_ms, value FROM round_state_v1 WHERE "
                "content_hash=? AND cs=? ORDER BY server_time_ms",
                (content_hash, CS_ROUND_INDEX)):
            m = _CS_ROUND.search(r["value"] or "")
            if not m:
                continue
            start, rn = int(m.group(1)), int(m.group(2))
            if rn >= 1 and start > 0 and rn not in out:
                out[rn] = start
    return out


def kill_spans(content_hash: str, db: Path = RECOGNITION_DB
               ) -> dict[int, tuple[int, int]]:
    with _conn(db) as c:
        return {int(r["round"]): (int(r["a"]), int(r["b"])) for r in c.execute(
            "SELECT round, MIN(server_time_ms) a, MAX(server_time_ms) b "
            "FROM kill_events_v1 WHERE content_hash=? AND round>=1 "
            "GROUP BY round", (content_hash,))}


def bounds_for(content_hash: str, round_no: int, db: Path = RECOGNITION_DB
               ) -> RoundBounds:
    """The best honest interval for one round."""
    rn = int(round_no)
    starts = announced_starts(content_hash, db)
    spans = kill_spans(content_hash, db)
    span = spans.get(rn)

    if rn in starts:
        start = starts[rn]
        # The end is the next announced start; failing that, the last thing
        # seen in this round.
        nxt = starts.get(rn + 1)
        end = nxt if nxt and nxt > start else (span[1] if span else None)
        if end and end > start:
            return RoundBounds(rn, start, end, end - start, OBSERVED,
                               "start announced by the server")

    # No announcement: squeeze the round between its neighbours.
    if span:
        prev = spans.get(rn - 1)
        nxt = spans.get(rn + 1)
        lo = prev[1] if prev and prev[1] < span[0] else None
        hi = nxt[0] if nxt and nxt[0] > span[1] else None
        if lo is not None and hi is not None:
            return RoundBounds(rn, lo, hi, hi - lo, BOUNDED,
                               "bounded by the neighbouring rounds; the true "
                               "round lies inside this interval")
        observed = span[1] - span[0]
        if observed >= MIN_CREDIBLE_MS:
            return RoundBounds(rn, span[0], span[1], observed, KILL_SPAN,
                               "the span between the first and last observed "
                               "death -- a LOWER BOUND on the round")
        # One kill, or several within a moment. The round certainly lasted
        # longer than this, and how much longer is not observable.
        return RoundBounds(rn, span[0], span[1], None, UNKNOWN,
                           f"{'one death' if span[0] == span[1] else 'all deaths'} "
                           f"observed at effectively one instant; the round "
                           f"was longer and by how much is not observable")
    return RoundBounds(rn, None, None, None, UNKNOWN, "no events in this round")


def summary(db: Path = RECOGNITION_DB, limit: int | None = None
            ) -> dict[str, Any]:
    """How the corpus divides across the four provenances."""
    with _conn(db) as c:
        rounds = c.execute(
            "SELECT content_hash, round FROM kill_events_v1 WHERE round>=1 "
            "GROUP BY 1,2" + (f" LIMIT {int(limit)}" if limit else "")
        ).fetchall()
    counts: dict[str, int] = {}
    credible = 0
    cache: dict[str, tuple[dict[int, int], dict[int, tuple[int, int]]]] = {}
    for r in rounds:
        h = r["content_hash"]
        if h not in cache:
            cache[h] = (announced_starts(h, db), kill_spans(h, db))
        starts, spans = cache[h]
        b = _bounds_from(starts, spans, int(r["round"]))
        counts[b.provenance] = counts.get(b.provenance, 0) + 1
        credible += int(b.credible)
    return {"rounds": len(rounds), "by_provenance": counts,
            "credible_duration": credible,
            "not_credible": len(rounds) - credible}


def _bounds_from(starts: dict[int, int], spans: dict[int, tuple[int, int]],
                 rn: int) -> RoundBounds:
    """The same rule as `bounds_for`, on pre-loaded tables."""
    span = spans.get(rn)
    if rn in starts:
        start = starts[rn]
        nxt = starts.get(rn + 1)
        end = nxt if nxt and nxt > start else (span[1] if span else None)
        if end and end > start:
            return RoundBounds(rn, start, end, end - start, OBSERVED)
    if span:
        prev, nxt = spans.get(rn - 1), spans.get(rn + 1)
        lo = prev[1] if prev and prev[1] < span[0] else None
        hi = nxt[0] if nxt and nxt[0] > span[1] else None
        if lo is not None and hi is not None:
            return RoundBounds(rn, lo, hi, hi - lo, BOUNDED)
        observed = span[1] - span[0]
        if observed >= MIN_CREDIBLE_MS:
            return RoundBounds(rn, span[0], span[1], observed, KILL_SPAN)
        return RoundBounds(rn, span[0], span[1], None, UNKNOWN)
    return RoundBounds(rn, None, None, None, UNKNOWN)
