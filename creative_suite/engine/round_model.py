"""What a ROUND actually is in Clan Arena, and who won it.

The `round` column carried on events is not the round anybody watches. Two
things in the game state made that confusing, and both are settled here from
the engine's own configstring contract (bg_public.h):

    CS_SCORES1        6    red score
    CS_SCORES2        7    blue score
    CS_ROUND_STATUS   661  "" means the round STARTED; otherwise it is the
                           pre-round countdown carrying \\time\\..\\round\\N
    CS_ROUND_TIME     662  > 0 the round is running, < 0 the round is OVER
    CS_ROUND_WINNERS  705  space-separated CLIENT NUMBERS of the winners

So 661 is written TWICE per fight -- once to announce the next round and once
to start it -- which is why a naive round counter appears to increment twice
per fight, and why grouping on it silently mixes fights with the gaps between
them.

THE ROUND is the span from 662 going positive to 662 going negative.

THE WINNER is not read from 705: Quake Live servers rarely send it (5 rows in
this whole corpus). It is the team whose SCORE RISES on the tick the round
ends, which is exact, always present, and needs no inference. Where no score
moves -- a draw, a timelimit, a server hiccup -- the winner is recorded as
None rather than guessed at.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite/database/frag_recognition.db"

SCHEMA_VERSION = 1

CS_SCORES1, CS_SCORES2 = 6, 7
CS_ROUND_STATUS, CS_ROUND_TIME, CS_ROUND_WINNERS = 661, 662, 705

DDL = """
CREATE TABLE IF NOT EXISTS round_outcome_v1 (
    content_hash  TEXT NOT NULL,
    round_index   INTEGER NOT NULL,   -- 1-based, in play order
    start_ms      INTEGER NOT NULL,
    end_ms        INTEGER,
    duration_ms   INTEGER,
    winner        TEXT,               -- RED | BLUE | NULL when nothing moved
    red_score     INTEGER,
    blue_score    INTEGER,
    winners_cs    TEXT,               -- CS_ROUND_WINNERS verbatim, if sent
    basis         TEXT NOT NULL,      -- SCORE_DELTA | CS_ROUND_WINNERS | NONE
    version       INTEGER NOT NULL,
    PRIMARY KEY (content_hash, round_index)
);
CREATE INDEX IF NOT EXISTS ix_round_outcome_hash
    ON round_outcome_v1(content_hash);
"""


def _clean(v) -> str:
    return (v or "").strip().strip('"').strip()


def rounds_for(c, ch) -> list[tuple]:
    rows = c.execute(
        "SELECT server_time_ms, cs, value FROM round_state_v1 WHERE "
        "content_hash=? ORDER BY server_time_ms, cs", (ch,)).fetchall()
    if not rows:
        return []

    out = []
    red = blue = 0
    open_start = None
    idx = 0
    pending_winners = None

    # Group by tick: a score change and the round ending are written at the
    # SAME server time, and the order between them is not guaranteed.
    by_t: dict[int, list] = {}
    for r in rows:
        by_t.setdefault(r["server_time_ms"], []).append(r)

    for t in sorted(by_t):
        red_before, blue_before = red, blue
        ends = False
        starts_at = None
        for r in by_t[t]:
            cs, v = r["cs"], _clean(r["value"])
            if cs == CS_SCORES1 and v.lstrip("-").isdigit():
                red = int(v)
            elif cs == CS_SCORES2 and v.lstrip("-").isdigit():
                blue = int(v)
            elif cs == CS_ROUND_TIME:
                head = v.split()[0] if v else ""
                if head.startswith("-"):
                    ends = True
                elif head.lstrip("-").isdigit() and int(head) > 0:
                    starts_at = int(head)
            elif cs == CS_ROUND_WINNERS and v:
                pending_winners = v

        if ends and open_start is not None:
            idx += 1
            if red > red_before:
                winner, basis = "RED", "SCORE_DELTA"
            elif blue > blue_before:
                winner, basis = "BLUE", "SCORE_DELTA"
            elif pending_winners:
                winner, basis = None, "CS_ROUND_WINNERS"
            else:
                winner, basis = None, "NONE"
            # A round that ends before it began is a recording that STARTED
            # mid-round: 662 carries the real round start, which predates the
            # first frame we have. The round is real and its winner is real,
            # so both are kept -- the duration is not, and is left null
            # rather than reported as negative. One demo in 39,247.
            dur = t - open_start
            out.append((ch, idx, open_start, t, dur if dur >= 0 else None,
                        winner, red, blue, pending_winners, basis,
                        SCHEMA_VERSION))
            open_start = None
            pending_winners = None

        if starts_at is not None:
            open_start = starts_at

    # A round still running when the recording stops is real and is kept, with
    # no end and no winner, rather than dropped or invented.
    if open_start is not None:
        idx += 1
        out.append((ch, idx, open_start, None, None, None, red, blue, None,
                    "NONE", SCHEMA_VERSION))
    return out


def build(out_db=None, db=None, limit=None, progress=None):
    src = sqlite3.connect("file:%s?mode=ro" % (db or RECOGNITION_DB), uri=True,
                          timeout=60)
    src.row_factory = sqlite3.Row
    hashes = [r[0] for r in src.execute(
        "SELECT DISTINCT content_hash FROM round_state_v1")]
    if limit:
        hashes = hashes[:limit]

    dest = sqlite3.connect(str(out_db or RECOGNITION_DB), timeout=120)
    dest.executescript(DDL)
    n = 0
    for i, ch in enumerate(hashes, 1):
        rows = rounds_for(src, ch)
        dest.execute("DELETE FROM round_outcome_v1 WHERE content_hash=?", (ch,))
        if rows:
            dest.executemany(
                "INSERT INTO round_outcome_v1 (content_hash,round_index,"
                "start_ms,end_ms,duration_ms,winner,red_score,blue_score,"
                "winners_cs,basis,version) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                rows)
            n += len(rows)
        if i % 200 == 0:
            dest.commit()
            if progress:
                progress(i, len(hashes), n)
    dest.commit()
    dest.close()
    return n
