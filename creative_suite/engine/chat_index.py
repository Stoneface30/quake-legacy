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

CHAT_INDEX_VERSION = "chat-index-v1.0.0"
RECOGNITION_DB = dt.RECOGNITION_DB

_COLOR = re.compile(r"\^[0-9a-zA-Z]")
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


def _names_for(db: sqlite3.Connection, content_hash: str) -> dict[str, int]:
    """Lower-cased display name -> client slot, from the demo's own
    configstrings, resolved through the recognition scan's player table when
    present. Used only to turn a name back into a number."""
    out: dict[str, int] = {}
    try:
        for name, client in db.execute(
                "SELECT lower(player_name), client_num FROM demo_player_stats "
                "WHERE demo_id IN (SELECT id FROM demos WHERE filename=?)",
                (content_hash,)):
            out[str(name)] = int(client)
    except sqlite3.OperationalError:
        pass
    return out


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
        for h, t, rnd, kind, text in rows:
            slot, clean = scrub(text)
            frag = db.execute(
                "SELECT id, server_time_ms FROM recognized_frags WHERE content_hash=? "
                "ORDER BY ABS(server_time_ms-?) LIMIT 1", (h, t)).fetchone()
            hits.append(ChatHit(h, int(t), rnd, kind, slot, clean,
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
    return [ChatHit(h, int(ct), rnd, kind, *scrub(text), frag_id, int(ct) - t)
            for ct, rnd, kind, text in rows]


def contains_name(hit: ChatHit, names: Sequence[str]) -> bool:
    """Guard for export paths: refuse a hit whose text still carries a name."""
    low = hit.text.lower()
    return any(n and n.lower() in low for n in names)
