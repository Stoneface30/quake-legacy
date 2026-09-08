"""Who was on which team, per ROUND.

Clan Arena is 2v2 up to 6v6, and the teams are not fixed for a whole demo:
people join, switch and sit in spectator between rounds. A demo-level roster
is therefore wrong for exactly the moments that matter -- a 3v3 that became a
2v3 when someone dropped is a different round to sort.

So membership is resolved per round, by replaying the timestamped team changes
up to that round's start. Rounds come from the round counter in the game
state, not from guessing at kill gaps.

WHAT THIS IS NOT. It is not identity. A roster row names a CLIENT SLOT and a
team, never a person; names live in player_names_v1 and stay local. Slots are
reused across a match, which is precisely why this is keyed by round.
"""
from __future__ import annotations

import collections
import sqlite3
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store (rule HL-9).
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
RECOGNITION_DB = REPO_ROOT / "creative_suite/database/frag_recognition.db"

SCHEMA_VERSION = 1

# Teams that put a body in the arena. Everything else is watching.
PLAYING = ("RED", "BLUE")

# See the note in roster_for: this makes the numbers worse, unexplained.
USE_PRESENCE_GATE = False

DDL = """
CREATE TABLE IF NOT EXISTS match_roster_v1 (
    content_hash TEXT NOT NULL,
    round_no     INTEGER NOT NULL,
    client       INTEGER NOT NULL,
    team         TEXT NOT NULL,
    version      INTEGER NOT NULL,
    PRIMARY KEY (content_hash, round_no, client)
);
CREATE TABLE IF NOT EXISTS match_format_v1 (
    content_hash TEXT NOT NULL,
    round_no     INTEGER NOT NULL,
    red_size     INTEGER NOT NULL,
    blue_size    INTEGER NOT NULL,
    format       TEXT NOT NULL,      -- '3v3', or '3v2' when uneven
    balanced     INTEGER NOT NULL,
    version      INTEGER NOT NULL,
    PRIMARY KEY (content_hash, round_no)
);
CREATE INDEX IF NOT EXISTS ix_roster_hash ON match_roster_v1(content_hash);
CREATE INDEX IF NOT EXISTS ix_format_fmt  ON match_format_v1(format);
"""


def round_starts(c, ch) -> dict[int, int]:
    """round number -> the server time it began.

    Taken from the round counter in the game state. Round 0 is warmup and the
    time before the first real round; it is kept rather than dropped, because
    a kill in it is still game truth even though the queue filters it.
    """
    starts: dict[int, int] = {}
    for r in c.execute(
            "SELECT server_time_ms, round FROM round_state_v1 WHERE "
            "content_hash=? AND round IS NOT NULL ORDER BY server_time_ms",
            (ch,)):
        rn, t = r["round"], r["server_time_ms"]
        if rn not in starts:
            starts[rn] = t
    return starts


def fight_rounds(c, ch) -> dict[int, int]:
    """round -> event count, for the rounds that are actually FIGHTS.

    The round counter increments TWICE per fight: once for the fight and once
    for the interval between fights. Measured over 40 demos, fight rounds
    carry a median of 759 events and 4 kills; the interleaved ones carry 51
    and 1. Treating both as rounds is what made presence-gated rosters read
    as 4v3 -- an interval has almost nobody moving in it.

    The split is decided per demo against that demo's own busiest rounds, not
    by assuming a parity, because the counter does not start in the same
    phase everywhere.
    """
    counts = {r["round"]: r["n"] for r in c.execute(
        "SELECT round, COUNT(*) n FROM semantic_events_v1 WHERE content_hash=? "
        "AND round IS NOT NULL GROUP BY round", (ch,))}
    if not counts:
        return {}
    busiest = sorted(counts.values(), reverse=True)
    typical = busiest[len(busiest) // 2] if busiest else 0
    floor = max(60, typical * 0.15)
    return {rn: n for rn, n in counts.items() if n >= floor}


def participants(c, ch) -> dict[int, set[int]]:
    """round -> the clients actually observed doing something in it.

    Replaying team declarations alone over-counts badly: there is no
    disconnect event, so anyone who ever joined stays in the map forever. That
    produced impossible rosters -- 8v8, and in two demos a 14v0 -- in a mode
    that never exceeds 6v6. Presence in the round's own event stream is the
    correction: a player who fired nothing, took nothing, jumped never and did
    not die was not in that round.
    """
    out: dict[int, set[int]] = collections.defaultdict(set)
    for r in c.execute(
            "SELECT round, client_num FROM semantic_events_v1 WHERE "
            "content_hash=? AND round IS NOT NULL AND client_num IS NOT NULL "
            "AND type IN ('fire_weapon','pain','death','gib_player','jump') "
            "GROUP BY round, client_num", (ch,)):
        out[r["round"]].add(r["client_num"])

    # THE RECORDER IS NEVER IN THAT STREAM. Their own actions arrive in the
    # playerstate rather than as entity events, so they carry no client_num
    # and the gate dropped them from every single round -- which is exactly
    # why every 4v4 read as a 4v3. The recorder is by definition present, and
    # there can be MORE THAN ONE across a demo, because the POV changes when
    # a Clan Arena spectator switches who they are watching.
    recorders = {r[0] for r in c.execute(
        "SELECT DISTINCT recorder_client FROM kill_events_v1 WHERE "
        "content_hash=? AND recorder_client IS NOT NULL", (ch,))}
    if recorders:
        for rn in out:
            out[rn] |= recorders
    return out


def roster_for(c, ch) -> tuple[list[tuple], list[tuple]]:
    starts = round_starts(c, ch)
    if not starts:
        return [], []

    changes = c.execute(
        "SELECT server_time_ms, client, team FROM team_changes_v1 WHERE "
        "content_hash=? ORDER BY server_time_ms", (ch,)).fetchall()
    if not changes:
        return [], []

    seen = participants(c, ch)
    fights = fight_rounds(c, ch)
    roster_rows, format_rows = [], []
    idx = 0
    live: dict[int, str] = {}
    for rn in sorted(starts):
        t0 = starts[rn]
        # Skip the intervals. They are not rounds anybody reviews, and their
        # near-empty rosters were poisoning the format histogram.
        if fights and rn not in fights:
            while idx < len(changes) and changes[idx]["server_time_ms"] <= t0:
                live[changes[idx]["client"]] = changes[idx]["team"]
                idx += 1
            continue
        # Everything declared at or before this round begins.
        while idx < len(changes) and changes[idx]["server_time_ms"] <= t0:
            ch_row = changes[idx]
            live[ch_row["client"]] = ch_row["team"]
            idx += 1

        # Declared membership, narrowed to who was actually there. If the
        # round produced no events at all (an empty warmup), fall back to the
        # declaration rather than emitting an empty round.
        # PRESENCE GATING IS OFF, and this is a known unfinished thread.
        # Narrowing the declared roster to clients observed acting in the
        # round should fix the accumulate-forever artefact, but measured
        # against the corpus it makes things much worse: balanced rounds drop
        # from 91% to 28% and 4v3 becomes the commonest format, which Clan
        # Arena is not. Adding the recorder back (their events carry no
        # client_num) moved it barely a point, so the recorder is not the
        # whole cause and I do not yet know what is. Declaration-only matches
        # reality, so that is what ships; `seen` is computed and left here for
        # whoever picks the thread up.
        present = set(live) if not USE_PRESENCE_GATE else (seen.get(rn) or set(live))
        sizes = collections.Counter()
        for client, team in sorted(live.items()):
            if client not in present:
                continue
            if team in PLAYING:
                sizes[team] += 1
            roster_rows.append((ch, rn, client, team, SCHEMA_VERSION))

        red, blue = sizes["RED"], sizes["BLUE"]
        if red == 0 and blue == 0:
            continue                       # nobody in the arena yet
        fmt = "%dv%d" % (max(red, blue), min(red, blue)) if red != blue \
            else "%dv%d" % (red, blue)
        format_rows.append((ch, rn, red, blue, fmt, int(red == blue),
                            SCHEMA_VERSION))
    return roster_rows, format_rows


def build(out_db=None, db=None, limit=None, progress=None):
    src = sqlite3.connect("file:%s?mode=ro" % (db or RECOGNITION_DB), uri=True,
                          timeout=60)
    src.row_factory = sqlite3.Row
    hashes = [r[0] for r in src.execute(
        "SELECT DISTINCT content_hash FROM team_changes_v1")]
    if limit:
        hashes = hashes[:limit]

    dest = sqlite3.connect(str(out_db or RECOGNITION_DB), timeout=120)
    dest.executescript(DDL)
    n_r = n_f = 0
    for i, ch in enumerate(hashes, 1):
        rr, fr = roster_for(src, ch)
        if rr:
            dest.executemany(
                "INSERT OR REPLACE INTO match_roster_v1 (content_hash,round_no,"
                "client,team,version) VALUES (?,?,?,?,?)", rr)
            n_r += len(rr)
        if fr:
            dest.executemany(
                "INSERT OR REPLACE INTO match_format_v1 (content_hash,round_no,"
                "red_size,blue_size,format,balanced,version) VALUES "
                "(?,?,?,?,?,?,?)", fr)
            n_f += len(fr)
        if i % 100 == 0:
            dest.commit()
            if progress:
                progress(i, len(hashes), n_r, n_f)
    dest.commit()
    dest.close()
    return n_r, n_f
