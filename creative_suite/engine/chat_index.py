"""Timed chat as searchable editorial evidence, without leaking who said it.

The enrichment keeps every chat and server line raw, and raw lines carry
sender names. This index is the only door: it searches by substring, time,
round and proximity to a frag, and returns the sender's client SLOT and the
line with colour codes stripped and the sender's own name removed. No
sentiment model, no classification -- a human searching for "gg", "lol" or
a rage word is the whole feature, and it is enough.

The raw table stays internal. Nothing here is an export surface.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import re
import sqlite3
from typing import Any, Sequence

from creative_suite.engine import demo_truth as dt

CHAT_INDEX_VERSION = "chat-index-v1.1.0"

# How confidently a line was attributed to a client slot.
RESOLVED = "RESOLVED"
AMBIGUOUS = "AMBIGUOUS"
UNRESOLVED = "UNKNOWN"
RECOGNITION_DB = dt.RECOGNITION_DB

_COLOR = re.compile(r"\^[0-9a-zA-Z]")
# Quake Live wraps the sender in control characters and servers prepend clan
# tags and slot numbers, so the raw prefix is rarely the bare name.
_CONTROL = re.compile(chr(91) + chr(0) + chr(45) + chr(31) + chr(127) + chr(93))
# Quake Live chat lines arrive as `<name>^7: <text>` (team chat as `(name): text`).
_SENDER = re.compile(r"^\(?(?P<name>[^:()]{1,64}?)\)?\s*:\s*(?P<text>.*)$")


@dataclass(frozen=True)
class ChatHit:
    """One matching line, sender reduced to a slot, text scrubbed."""
    content_hash: str
    server_time_ms: int
    round_index: int | None
    kind: str                       # chat | tchat | print | cp
    sender_client: int | None
    text: str
    sender_state: str = UNRESOLVED
    nearest_frag_id: int | None = None
    ms_to_nearest_frag: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def scrub(raw: str, known_names: dict[str, int] | None = None
          ) -> tuple[int | None, str]:
    """Strip colour codes, split off the sender, map the sender to a slot.

    The sender's display name never leaves this function: it is replaced by
    the client slot when the name is known and by None when it is not.
    """
    plain = _COLOR.sub("", raw).strip().strip('"')
    m = _SENDER.match(plain)
    if not m:
        return None, plain
    name, text = m.group("name").strip(), m.group("text").strip()
    slot = (known_names or {}).get(name.lower())
    return slot, text


def name_timeline(db: sqlite3.Connection, content_hash: str
                  ) -> list[tuple[int, int, str]]:
    """(server_time_ms, client, normalised name) from the demo's own
    configstrings, in order. Internal only."""
    try:
        rows = db.execute(
            "SELECT server_time_ms, client, name FROM player_names_v1 "
            "WHERE content_hash=? ORDER BY server_time_ms", (content_hash,)).fetchall()
    except sqlite3.OperationalError:
        return []
    return [(int(t), int(c), normalise(str(n))) for t, c, n in rows]


def normalise(name: str) -> str:
    """Colour codes and control characters stripped, case folded, spaces
    squashed. Two players whose names differ only by colour are the same
    display identity."""
    return " ".join(_CONTROL.sub("", _COLOR.sub("", name)).split()).strip().lower()


def slot_at(timeline: Sequence[tuple[int, int, str]], name: str, t_ms: int
            ) -> tuple[int | None, str]:
    """Which client held this display name at this instant.

    Names change mid-match: renames, reconnects, a freed slot taken by
    somebody else. A single static map for a whole demo would credit a line
    to whoever holds the slot LAST, so the lookup is time-aware: for each
    client, the last name set at or before `t_ms` is the name it held. When
    two clients held the same name at once the answer is AMBIGUOUS, never a
    coin toss.
    """
    key = normalise(name)
    if not key:
        return None, UNRESOLVED
    held: dict[int, str] = {}
    for t, client, n in timeline:
        if t > t_ms:
            break
        held[client] = n
    matches = sorted(c for c, n in held.items() if n == key)
    if not matches:
        # The prefix carries clan tags, a slot number and control characters
        # around the name. Fall back to finding which registered name the
        # prefix CONTAINS -- and only when exactly one does, because a name
        # that is a substring of another would otherwise be a coin toss.
        matches = sorted(c for c, n in held.items()
                         if n and len(n) >= 3 and n in key)
        if len(matches) > 1:
            longest = max(len(held[c]) for c in matches)
            best = [c for c in matches if len(held[c]) == longest]
            matches = best if len(best) == 1 else matches
    if len(matches) == 1:
        return matches[0], RESOLVED
    if len(matches) > 1:
        return None, AMBIGUOUS
    return None, UNRESOLVED


def search(query: str, *, content_hash: str | None = None,
           kinds: Sequence[str] = ("chat", "tchat"),
           limit: int = 50, db_path: Path | None = None) -> list[ChatHit]:
    """Substring search over chat, scrubbed on the way out."""
    path = Path(db_path or RECOGNITION_DB)
    q = f"%{query.lower()}%"
    hits: list[ChatHit] = []
    with sqlite3.connect(path, timeout=30) as db:
        sql = ("SELECT content_hash, server_time_ms, round, kind, text FROM "
               "server_text_v1 WHERE lower(text) LIKE ? AND kind IN (%s)"
               % ",".join("?" * len(kinds)))
        args: list[Any] = [q, *kinds]
        if content_hash:
            sql += " AND content_hash=?"
            args.append(content_hash)
        sql += " ORDER BY content_hash, server_time_ms LIMIT ?"
        args.append(int(limit))
        try:
            rows = db.execute(sql, args).fetchall()
        except sqlite3.OperationalError:
            return []
        timelines: dict[str, list[tuple[int, int, str]]] = {}
        for h, t, rnd, kind, text in rows:
            raw_name = _sender_name(text)
            tl = timelines.setdefault(h, name_timeline(db, h))
            slot, state = slot_at(tl, raw_name, int(t)) if raw_name else (None, UNRESOLVED)
            _, clean = scrub(text)
            frag = db.execute(
                "SELECT id, server_time_ms FROM recognized_frags WHERE content_hash=? "
                "ORDER BY ABS(server_time_ms-?) LIMIT 1", (h, t)).fetchone()
            hits.append(ChatHit(h, int(t), rnd, kind, slot, clean, state,
                                frag[0] if frag else None,
                                (int(t) - frag[1]) if frag else None))
    return hits


def near_frag(frag_id: int, *, window_ms: int = 15_000,
              db_path: Path | None = None) -> list[ChatHit]:
    """Chat around one frag: reactions, gg, complaints."""
    path = Path(db_path or RECOGNITION_DB)
    with sqlite3.connect(path, timeout=30) as db:
        row = db.execute("SELECT content_hash, server_time_ms FROM recognized_frags "
                         "WHERE id=?", (frag_id,)).fetchone()
        if not row:
            return []
        h, t = row
        try:
            rows = db.execute(
                "SELECT server_time_ms, round, kind, text FROM server_text_v1 WHERE "
                "content_hash=? AND kind IN ('chat','tchat') AND server_time_ms "
                "BETWEEN ? AND ? ORDER BY server_time_ms",
                (h, t - window_ms, t + window_ms)).fetchall()
        except sqlite3.OperationalError:
            return []
    out: list[ChatHit] = []
    with sqlite3.connect(path, timeout=30) as db:
        tl = name_timeline(db, h)
    for ct, rnd, kind, text in rows:
        raw_name = _sender_name(text)
        slot, state = slot_at(tl, raw_name, int(ct)) if raw_name else (None, UNRESOLVED)
        out.append(ChatHit(h, int(ct), rnd, kind, slot, scrub(text)[1], state,
                           frag_id, int(ct) - t))
    return out


def _sender_name(raw: str) -> str:
    """The sender's display name as written, for slot lookup only. It never
    leaves this module."""
    plain = _COLOR.sub("", raw).strip().strip(chr(34))
    m = _SENDER.match(plain)
    return m.group("name").strip() if m else ""


def contains_name(hit: ChatHit, names: Sequence[str]) -> bool:
    """Guard for export paths: refuse a hit whose text still carries a name."""
    low = hit.text.lower()
    return any(n and n.lower() in low for n in names)
