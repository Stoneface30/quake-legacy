"""Who is who: user identity and clan membership, both by provenance.

TWO CORPUS-WIDE MISTAKES THIS EXISTS TO PREVENT.

The first is already made and is being corrected here. `recognized_frags` was
built on "the killer recorded this demo", and that was read as "the user made
this kill". It is not the same claim. The archive holds 172 demos recorded by
other people, so about 1,888 of the 36,628 recorder-own kills belong to
somebody else entirely. Presenting those as the user's frags asks them to
curate a corpus we have labelled wrongly.

The second would be made by fixing the first carelessly: merging identities
because they look similar. `stoneface` is very probably the user, and
`probably` is not provenance. Same machine, same archive, same clan, similar
spelling -- none of those is evidence that two names are one person.

SO IDENTITY IS ANSWERED BY THE USER, AND THE CODE ONLY ASSEMBLES EVIDENCE.
Every non-primary identity starts UNRESOLVED. Nothing is merged, expanded or
promoted automatically, and a decision records who made it.

TWO INDEPENDENT QUESTIONS. "Is this me?" and "Is this pTn?" are not the same
question and are stored separately. A person can be both, and the user can
answer one without implying the other.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
DB_DIR = REPO_ROOT / "creative_suite" / "database"
RECOGNITION_DB = DB_DIR / "frag_recognition.db"
# Decisions are editorial truth and live beside the human reviews, never in
# the recognition caches (project rule: recognition databases are read-only
# to editorial code).
EDITORIAL_DB = DB_DIR / "editorial.db"

IDENTITY_VERSION = "identity-v1"

# "Is this me?"
USER_CONFIRMED = "CONFIRMED_USER"
USER_NOT = "NOT_USER"
USER_UNRESOLVED = "UNRESOLVED"
USER_STATES = (USER_CONFIRMED, USER_NOT, USER_UNRESOLVED)

# "Is this pTn?"
PTN_MEMBER = "PTN_CONFIRMED_MEMBER"
PTN_CANDIDATE = "PTN_CANDIDATE"
PTN_NOT = "NOT_PTN"
PTN_UNKNOWN = "PTN_UNKNOWN"
PTN_STATES = (PTN_MEMBER, PTN_CANDIDATE, PTN_NOT, PTN_UNKNOWN)

# Who decided. Only a human answer is a human answer.
BY_USER = "HUMAN_USER"
BY_SEED = "PROJECT_SEED"        # asserted in the project's own instructions
BY_TEST = "TEST"
HUMAN_DECIDED = (BY_USER, BY_SEED)

# The one identity the project itself asserts: the recorder of 3,825 of the
# 3,997 demos that contain a recorder kill, and the wearer of the clan tag on
# 15,940 cached text lines. Everything else is a question.
PRIMARY_USER = "tr4sh"

# The clan roster the USER supplied. This list does not grow on its own.
# b3nto is here because the user named him, not because evidence found him --
# he appears in ZERO pTn-tagged lines, which the user explained: he joined
# later and sometimes played untagged.
USER_SUPPLIED_PTN = ("naikomarie", "sereke", "s73rn", "jibyjibs", "b3nto")

# A user-supplied identity relation, kept because the user stated it and not
# because a second spelling was observed. "s7ern" has no independent presence
# in the caches; the relation is the provenance.
USER_DEFINED_ALIASES = {"s7ern": "s73rn"}

# Colour is a caret plus ONE DIGIT. See quake_names -- the wider pattern
# also eats caret+letter, which is part of a name, not markup.
from creative_suite.engine.quake_names import COLOR_CODE as _COLOR
_DATE = re.compile(r"(20\d\d)[_-](\d\d)[_-](\d\d)")
_TOKEN = re.compile(r"[0-9a-z]+")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS identity_decisions (
    name_norm     TEXT PRIMARY KEY,
    user_state    TEXT NOT NULL DEFAULT 'UNRESOLVED',
    ptn_state     TEXT NOT NULL DEFAULT 'PTN_UNKNOWN',
    alias_of      TEXT,
    note          TEXT NOT NULL DEFAULT '',
    decided_by    TEXT NOT NULL DEFAULT 'HUMAN_USER',
    decided_at    TEXT NOT NULL,
    version       TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_id_user ON identity_decisions(user_state);
CREATE INDEX IF NOT EXISTS ix_id_ptn ON identity_decisions(ptn_state);
"""


def strip_colors(s: str | None) -> str:
    return _COLOR.sub("", s or "")


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(EDITORIAL_DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(_SCHEMA)
    _seed(c)
    return c


def _rec() -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def _seed(c: sqlite3.Connection) -> None:
    """Write only what the project itself asserts, and only if absent.

    Seeding never overwrites a human answer -- if the user has said something
    about a name, that stands.
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = [(PRIMARY_USER, USER_CONFIRMED, PTN_MEMBER, None,
             "primary user identity; wears the clan tag on 15,940 lines")]
    rows += [(n, USER_UNRESOLVED, PTN_MEMBER, None, "user-supplied roster")
             for n in USER_SUPPLIED_PTN]
    with c:
        for n, us, ps, al, note in rows:
            c.execute(
                "INSERT INTO identity_decisions(name_norm, user_state, "
                "ptn_state, alias_of, note, decided_by, decided_at, version) "
                "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(name_norm) DO NOTHING",
                (n, us, ps, al, note, BY_SEED, now, IDENTITY_VERSION))


def decisions() -> dict[str, dict[str, Any]]:
    with conn() as c:
        return {r["name_norm"]: dict(r)
                for r in c.execute("SELECT * FROM identity_decisions")}


def confirmed_user_identities() -> set[str]:
    """Every name the user has confirmed as themselves. Never inferred."""
    with conn() as c:
        return {r[0] for r in c.execute(
            "SELECT name_norm FROM identity_decisions WHERE user_state=? "
            "AND decided_by IN (?,?)",
            (USER_CONFIRMED, BY_USER, BY_SEED))}


def confirmed_ptn_identities() -> set[str]:
    """The user-supplied roster plus anything the user has since confirmed.

    Candidates found by tag evidence are NOT in here. A tag is a costume.
    """
    with conn() as c:
        names = {r[0] for r in c.execute(
            "SELECT name_norm FROM identity_decisions WHERE ptn_state=? "
            "AND decided_by IN (?,?)", (PTN_MEMBER, BY_USER, BY_SEED))}
    # The user's stated alias relation travels with the identity it names.
    for alias, target in USER_DEFINED_ALIASES.items():
        if target in names:
            names.add(alias)
    return names


def decide(name_norm: str, user_state: str | None = None,
           ptn_state: str | None = None, alias_of: str | None = None,
           note: str | None = None, decided_by: str = BY_USER
           ) -> dict[str, Any]:
    """Record a human answer. Two questions, either or both."""
    if user_state is not None and user_state not in USER_STATES:
        raise ValueError(f"unknown user_state {user_state!r}")
    if ptn_state is not None and ptn_state not in PTN_STATES:
        raise ValueError(f"unknown ptn_state {ptn_state!r}")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with conn() as c:
        cur = c.execute("SELECT * FROM identity_decisions WHERE name_norm=?",
                        (name_norm,)).fetchone()
        us = user_state or (cur["user_state"] if cur else USER_UNRESOLVED)
        ps = ptn_state or (cur["ptn_state"] if cur else PTN_UNKNOWN)
        al = alias_of if alias_of is not None else (cur["alias_of"] if cur else None)
        nt = note if note is not None else (cur["note"] if cur else "")
        c.execute(
            "INSERT INTO identity_decisions(name_norm, user_state, ptn_state, "
            "alias_of, note, decided_by, decided_at, version) "
            "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(name_norm) DO UPDATE SET "
            "user_state=excluded.user_state, ptn_state=excluded.ptn_state, "
            "alias_of=excluded.alias_of, note=excluded.note, "
            "decided_by=excluded.decided_by, decided_at=excluded.decided_at",
            (name_norm, us, ps, al, nt, decided_by, now, IDENTITY_VERSION))
        return dict(c.execute("SELECT * FROM identity_decisions WHERE "
                              "name_norm=?", (name_norm,)).fetchone())


# ── evidence ────────────────────────────────────────────────────────────────

_TAG_CACHE: dict[str, int] | None = None


def tag_line_counts(refresh: bool = False) -> dict[str, int]:
    """How many tagged text lines mention each name, counted in ONE pass.

    The obvious implementation is a LIKE per candidate, which is a full scan
    of 256,651 text rows per name and took seven minutes for a page the user
    is supposed to click through. Every tagged line is fetched once instead,
    and the names are matched in memory.
    """
    global _TAG_CACHE
    if _TAG_CACHE is not None and not refresh:
        return _TAG_CACHE
    counts: dict[str, int] = {}
    with _rec() as c:
        lines = [r[0] for r in c.execute(
            "SELECT text FROM server_text_v1 WHERE text LIKE ?", ("%pTn%",))]
        names = {strip_colors(r[0]).strip().lower()
                 for r in c.execute("SELECT DISTINCT name FROM player_names_v1")}
    names = {n for n in names if len(n) >= 3}
    plain = [strip_colors(t).lower() for t in lines]
    # WHOLE NAMES ONLY. A substring test reported "mar" on 6,329 tagged lines
    # and "tere" on 3,330 -- both of which are simply the middle of
    # "naikomarie" and "hiddenfortress". Counting those as tag evidence put
    # two non-existent people at the top of the clan candidate list.
    #
    # Done by INVERTING the scan: tokenise each line once and count tokens,
    # rather than running a boundary regex per name across every line. The
    # regex version was correct and took 162 seconds; this is the same answer
    # in about one, which is the difference between a page and a wait.
    import collections as _c
    tok_lines: _c.Counter = _c.Counter()
    for t in plain:
        tok_lines.update(set(_TOKEN.findall(t)))
    multi = [n for n in names if _TOKEN.fullmatch(n) is None]
    for n in names:
        if n not in multi:
            counts[n] = tok_lines.get(n, 0)
    # Names that are not a single token (spaces, punctuation) still need the
    # boundary regex, but there are only a handful of them.
    for n in multi:
        pat = re.compile(r"(?<![0-9a-z])" + re.escape(n) + r"(?![0-9a-z])")
        counts[n] = sum(1 for t in plain if pat.search(t))
    _TAG_CACHE = {k: v for k, v in counts.items() if v}
    return _TAG_CACHE

def _dates(names: list[str]) -> tuple[str | None, str | None]:
    """First and last play date, read from demo filenames.

    The filename itself never leaves this function -- it embeds aliases. Only
    the dates come out, and a date is the single most useful thing for "was
    this me": the user knows when they played.
    """
    found = sorted(f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                   for n in names for m in [_DATE.search(n or "")] if m)
    return (found[0], found[-1]) if found else (None, None)


def recorder_candidates(limit: int = 200) -> list[dict[str, Any]]:
    """Every identity that recorded a demo, with the evidence to judge it.

    Ordered by how much of the corpus each one accounts for, because that is
    the order in which answering matters.
    """
    dec = decisions()
    tags = tag_line_counts()
    out: list[dict[str, Any]] = []
    with _rec() as c:
        rows = c.execute(
            "SELECT killer_name_norm n, COUNT(DISTINCT content_hash) demos, "
            "COUNT(*) kills FROM kill_events_v1 WHERE is_recorder_killer=1 "
            "AND killer_name_norm IS NOT NULL "
            "GROUP BY 1 ORDER BY demos DESC, kills DESC LIMIT ?",
            (limit,)).fetchall()
        for r in rows:
            n = r["n"]
            det = c.execute(
                "SELECT DISTINCT killer_name_raw FROM kill_events_v1 "
                "WHERE killer_name_norm=? AND is_recorder_killer=1 LIMIT 8",
                (n,)).fetchall()
            maps = c.execute(
                "SELECT map, COUNT(*) k FROM kill_events_v1 WHERE "
                "killer_name_norm=? AND is_recorder_killer=1 GROUP BY 1 "
                "ORDER BY k DESC LIMIT 5", (n,)).fetchall()
            demos = c.execute(
                "SELECT DISTINCT s.demo_name FROM kill_events_v1 k JOIN "
                "scanned_demos s ON s.content_hash=k.content_hash WHERE "
                "k.killer_name_norm=? AND k.is_recorder_killer=1 LIMIT 60",
                (n,)).fetchall()
            first, last = _dates([d["demo_name"] for d in demos])
            tag = tags.get(n, 0)
            d = dec.get(n, {})
            out.append({
                "name_norm": n,
                "raw_spellings": [x["killer_name_raw"] for x in det],
                "demos_recorded": r["demos"], "recorder_own_kills": r["kills"],
                "first_played": first, "last_played": last,
                "maps": [m["map"] for m in maps],
                "ptn_tag_lines": tag,
                "user_state": d.get("user_state", USER_UNRESOLVED),
                "ptn_state": d.get("ptn_state", PTN_UNKNOWN),
                "decided_by": d.get("decided_by"),
                "note": d.get("note", ""),
                "is_primary": n == PRIMARY_USER,
            })
    return out


def ptn_candidates(min_lines: int = 20) -> list[dict[str, Any]]:
    """Names seen wearing the clan tag, with the evidence to judge them.

    Surfaced, never added. Appearing next to `pTn.` in a chat line is a
    costume, not membership, and the roster is the user's to grow.
    """
    dec = decisions()
    confirmed = confirmed_ptn_identities()
    tags = tag_line_counts()
    out = []
    with _rec() as c:
        rows = c.execute(
            "SELECT name, COUNT(*) n FROM player_names_v1 GROUP BY 1"
        ).fetchall()
        seen: dict[str, int] = {}
        for r in rows:
            nn = strip_colors(r["name"]).strip().lower()
            if nn:
                seen[nn] = seen.get(nn, 0) + r["n"]
        # One grouped query instead of two per candidate.
        kd = {r["n"]: (r["k"], r["d"]) for r in c.execute(
            "SELECT killer_name_norm n, COUNT(*) k, "
            "COUNT(DISTINCT content_hash) d FROM kill_events_v1 "
            "WHERE killer_name_norm IS NOT NULL GROUP BY 1")}
        for nn in sorted(seen, key=lambda x: -seen[x]):
            lines = tags.get(nn, 0)
            if lines < min_lines:
                continue
            kills, demos = kd.get(nn, (0, 0))
            d = dec.get(nn, {})
            out.append({
                "name_norm": nn, "ptn_tag_lines": lines,
                "name_rows": seen[nn], "kills": kills, "demos": demos,
                "ptn_state": d.get("ptn_state",
                                   PTN_MEMBER if nn in confirmed
                                   else PTN_CANDIDATE),
                "user_supplied": nn in USER_SUPPLIED_PTN or nn == PRIMARY_USER,
                "decided_by": d.get("decided_by"),
            })
    return sorted(out, key=lambda x: -x["ptn_tag_lines"])


def status() -> dict[str, Any]:
    """Where identity resolution stands."""
    dec = decisions()
    by_user = {s: sum(1 for d in dec.values() if d["user_state"] == s)
               for s in USER_STATES}
    with _rec() as c:
        total = c.execute(
            "SELECT COUNT(DISTINCT killer_name_norm) FROM kill_events_v1 "
            "WHERE is_recorder_killer=1 AND killer_name_norm IS NOT NULL"
        ).fetchone()[0]
    answered = sum(1 for d in dec.values()
                   if d["user_state"] != USER_UNRESOLVED
                   and d["decided_by"] in HUMAN_DECIDED)
    return {
        "version": IDENTITY_VERSION,
        "recorder_identities_total": total,
        "user_confirmed": sorted(confirmed_user_identities()),
        "ptn_confirmed": sorted(confirmed_ptn_identities()),
        "user_states": by_user,
        "answered": answered,
        "unanswered": total - answered,
        "primary": PRIMARY_USER,
        "user_defined_aliases": USER_DEFINED_ALIASES,
        "rule": ("identity is the user's answer. Nothing is merged because "
                 "of a similar spelling, a shared machine, a shared archive "
                 "or a shared clan"),
    }
