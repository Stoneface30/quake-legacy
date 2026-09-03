"""The whole career, reviewable. The machine organises; the user decides.

WHY THIS EXISTS. There is no shortage of information any more -- 4,292
demos, 36,607 canonical frags, 34.3M semantic events. What was missing is a
way to sit down and go through it. This is that: one item at a time, five
buttons, one answer, an optional note, and the next one starts playing.

THREE RULES THE CODE ENFORCES.

Nothing is hidden. A machine score is an ORDER, never a filter. The
lowest-scoring frag in the corpus is as reachable as the highest, because
the machine does not know why a moment is good -- it knows how it looked to
a scorer written months ago.

Nothing is thrown away. PASS means "not wanted as primary gameplay
material", and a passed moment stays in the corpus for the two-frame flash,
the background plate, the death motif, the thing nobody thought of yet.

Reviewed is not consumed. A verdict says what a moment is FOR. It does not
spend it. Consumption still happens only when a moment is placed in an
actual production under the existing no-reuse rules.

GENERIC BY CONSTRUCTION. A frag is one item type. A telefrag, a jump-pad
dodge, a death, a teleport and a movement moment are others, and every one
of them gets the same five questions, because the system already knows WHAT
the event is. What it cannot know is what the event is FOR.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite/database/frag_recognition.db"
EDITORIAL_DB = REPO_ROOT / "creative_suite/database/editorial.db"

REVIEW_VERSION = "review-corpus-v1"

# ── the five roles ──────────────────────────────────────────────────────────
# One click, one answer. Not a tag cloud: the machine already knows what the
# event IS, and the only thing it cannot infer is what the event is FOR.

T1_FEATURE_FX = "T1_FEATURE_FX"          # deserves special treatment
T2_TRANSITION = "T2_TRANSITION"          # connects scenes
T3_RHYTHM_MONTAGE = "T3_RHYTHM_MONTAGE"  # belongs in a repeated sequence
T4_KEEP_NORMAL = "T4_KEEP_NORMAL"        # good, plain gameplay
T5_PASS_FILLER = "T5_PASS_FILLER"        # not primary -- and never deleted
ROLES = (T1_FEATURE_FX, T2_TRANSITION, T3_RHYTHM_MONTAGE, T4_KEEP_NORMAL,
         T5_PASS_FILLER)

ROLE_LABEL = {
    T1_FEATURE_FX: "FEATURE / FX",
    T2_TRANSITION: "TRANSITION",
    T3_RHYTHM_MONTAGE: "RHYTHM / MONTAGE",
    T4_KEEP_NORMAL: "KEEP / NORMAL",
    T5_PASS_FILLER: "PASS / FILLER",
}
ROLE_HINT = {
    T1_FEATURE_FX: "hero shot, cinematic replay, big effect",
    T2_TRANSITION: "teleport, flyby, death, jump, weapon switch",
    T3_RHYTHM_MONTAGE: "one of many, cut to the music",
    T4_KEEP_NORMAL: "clean gameplay, no special treatment",
    T5_PASS_FILLER: "kept forever: flashes, plates, motifs",
}
ROLE_BY_KEY = {str(i + 1): r for i, r in enumerate(ROLES)}

# ── item types ──────────────────────────────────────────────────────────────
# Only families that exist in the caches today. Inventing a type to pad the
# list would put the user in front of an empty queue.

FRAG = "FRAG"
TELEFRAG = "TELEFRAG"
DEATH = "DEATH"
TELEPORT = "TELEPORT"
DODGE = "DODGE"
LG_TRACKING = "LG_TRACKING"
PROJECTILE = "PROJECTILE"
ITEM_TYPES = (FRAG, TELEFRAG, DEATH, TELEPORT, DODGE, LG_TRACKING, PROJECTILE)

# The review window. Three seconds of run-up, the moment, three seconds of
# consequence -- clamped honestly at the recording's own edges rather than
# padded with something that was never recorded.
PRE_MS = 3000
POST_MS = 3000


@dataclass(frozen=True)
class ReviewItem:
    """One reviewable moment, of any family."""
    item_id: str                  # "FRAG:24326"
    item_type: str
    source_id: int
    content_hash: str
    demo_name: str
    server_time_ms: int
    machine_score: float
    machine_rank: int
    total_items: int
    weapon: str = ""
    map_name: str = ""
    victim: int | None = None
    round_no: int | None = None
    why: str = ""
    human_role: str | None = None
    note: str = ""

    @property
    def start_ms(self) -> int:
        return max(0, self.server_time_ms - PRE_MS)

    @property
    def end_ms(self) -> int:
        return self.server_time_ms + POST_MS

    @property
    def reviewed(self) -> bool:
        return self.human_role is not None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(start_ms=self.start_ms, end_ms=self.end_ms,
                 reviewed=self.reviewed,
                 frag_offset_s=(self.server_time_ms - self.start_ms) / 1000.0,
                 duration_s=(self.end_ms - self.start_ms) / 1000.0)
        return d


# ── persistence ─────────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS human_reviews (
    item_id        TEXT PRIMARY KEY,
    item_type      TEXT NOT NULL,
    source_id      INTEGER NOT NULL,
    human_role     TEXT NOT NULL,
    note           TEXT NOT NULL DEFAULT '',
    reviewed_at    TEXT NOT NULL,
    review_version TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_hr_role ON human_reviews(human_role);
CREATE INDEX IF NOT EXISTS ix_hr_type ON human_reviews(item_type, human_role);
CREATE TABLE IF NOT EXISTS human_review_log (
    rowid_         INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id        TEXT NOT NULL,
    human_role     TEXT,
    note           TEXT,
    at             TEXT NOT NULL
);
"""


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(EDITORIAL_DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(_SCHEMA)
    return c


def _rec() -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=30000")
    return c


def record(item_id: str, item_type: str, source_id: int, role: str,
           note: str | None = None) -> dict[str, Any]:
    """Save a verdict. Immediate, and appended to a log so a mistake is
    recoverable rather than merely regretted."""
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}")
    with conn() as c:
        prev = c.execute("SELECT note FROM human_reviews WHERE item_id=?",
                         (item_id,)).fetchone()
        keep = prev["note"] if (prev and note is None) else (note or "")
        c.execute(
            "INSERT INTO human_reviews(item_id,item_type,source_id,human_role,"
            "note,reviewed_at,review_version) "
            "VALUES(?,?,?,?,?,datetime('now'),?) "
            "ON CONFLICT(item_id) DO UPDATE SET human_role=excluded.human_role,"
            "note=excluded.note, reviewed_at=excluded.reviewed_at",
            (item_id, item_type, source_id, role, keep, REVIEW_VERSION))
        c.execute("INSERT INTO human_review_log(item_id,human_role,note,at) "
                  "VALUES(?,?,?,datetime('now'))", (item_id, role, keep))
    return {"item_id": item_id, "human_role": role, "note": keep}


def annotate(item_id: str, note: str) -> dict[str, Any]:
    """A note without a verdict. Saving a thought must never force a
    decision."""
    with conn() as c:
        row = c.execute("SELECT human_role, item_type, source_id "
                        "FROM human_reviews WHERE item_id=?",
                        (item_id,)).fetchone()
        if row:
            c.execute("UPDATE human_reviews SET note=?, reviewed_at="
                      "datetime('now') WHERE item_id=?", (note, item_id))
        else:
            kind, _, sid = item_id.partition(":")
            c.execute(
                "INSERT INTO human_reviews(item_id,item_type,source_id,"
                "human_role,note,reviewed_at,review_version) "
                "VALUES(?,?,?,'',?,datetime('now'),?)",
                (item_id, kind, int(sid or 0), note, REVIEW_VERSION))
        c.execute("INSERT INTO human_review_log(item_id,human_role,note,at) "
                  "VALUES(?,NULL,?,datetime('now'))", (item_id, note))
    return {"item_id": item_id, "note": note}


def undo_last() -> dict[str, Any] | None:
    """Take back the most recent verdict. Reviewing thousands of items means
    mis-clicking some of them."""
    with conn() as c:
        row = c.execute("SELECT item_id FROM human_review_log "
                        "ORDER BY rowid_ DESC LIMIT 1").fetchone()
        if not row:
            return None
        item = row["item_id"]
        c.execute("DELETE FROM human_reviews WHERE item_id=?", (item,))
        c.execute("DELETE FROM human_review_log WHERE rowid_ = "
                  "(SELECT MAX(rowid_) FROM human_review_log)")
    return {"undone": item}


def reviews(item_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
    if not item_ids:
        return {}
    with conn() as c:
        qs = ",".join("?" * len(item_ids))
        return {r["item_id"]: dict(r) for r in c.execute(
            f"SELECT * FROM human_reviews WHERE item_id IN ({qs})",
            list(item_ids))}


# ── the queue ───────────────────────────────────────────────────────────────

ORDER_WORST_FIRST = "WORST_FIRST"
ORDER_BEST_FIRST = "BEST_FIRST"
ORDERS = (ORDER_WORST_FIRST, ORDER_BEST_FIRST)


def _frag_rows(order: str, limit: int, offset: int,
               unreviewed_only: bool) -> list[sqlite3.Row]:
    direction = "ASC" if order == ORDER_WORST_FIRST else "DESC"
    sql = ("SELECT id, content_hash, demo_name, server_time_ms, round, "
           "weapon_name, victim_client, highlight_score, classes, reasons "
           "FROM recognized_frags "
           f"ORDER BY highlight_score {direction}, id ASC "
           "LIMIT ? OFFSET ?")
    with _rec() as c:
        rows = c.execute(sql, (limit, offset)).fetchall()
    if not unreviewed_only:
        return rows
    got = reviews([f"{FRAG}:{r['id']}" for r in rows])
    return [r for r in rows if f"{FRAG}:{r['id']}" not in got]


def _why(row: sqlite3.Row) -> str:
    """One line saying what the machine noticed. Not a justification -- the
    user is about to disagree with it regularly, and should be able to see
    exactly what it thought."""
    import json
    try:
        cls = [c.get("name") for c in json.loads(row["classes"] or "[]")]
    except Exception:
        cls = []
    if cls:
        return ", ".join(cls[:4])
    return f"{row['weapon_name'] or 'kill'}, no class detected"


def queue(order: str = ORDER_WORST_FIRST, limit: int = 50, offset: int = 0,
          item_type: str = FRAG, unreviewed_only: bool = False
          ) -> list[ReviewItem]:
    """A slice of the corpus in the requested order.

    The default is WORST FIRST because that is what was asked for, and it is
    also the honest direction: the bottom of a machine ranking is exactly
    where the machine is most likely to be wrong.
    """
    if order not in ORDERS:
        raise ValueError(f"unknown order {order!r}")
    if item_type != FRAG:
        return []                       # other families wire in next
    total = count_items(item_type)
    rows = _frag_rows(order, limit, offset, unreviewed_only)
    ids = [f"{FRAG}:{r['id']}" for r in rows]
    got = reviews(ids)
    out: list[ReviewItem] = []
    for i, r in enumerate(rows):
        iid = f"{FRAG}:{r['id']}"
        rv = got.get(iid) or {}
        rank = offset + i + 1
        out.append(ReviewItem(
            item_id=iid, item_type=FRAG, source_id=int(r["id"]),
            content_hash=r["content_hash"] or "", demo_name=r["demo_name"] or "",
            server_time_ms=int(r["server_time_ms"]),
            machine_score=float(r["highlight_score"]),
            machine_rank=rank, total_items=total,
            weapon=r["weapon_name"] or "", victim=r["victim_client"],
            round_no=r["round"], why=_why(r),
            human_role=(rv.get("human_role") or None) or None,
            note=rv.get("note") or ""))
    return out


def count_items(item_type: str = FRAG) -> int:
    if item_type != FRAG:
        return 0
    with _rec() as c:
        return int(c.execute("SELECT COUNT(*) FROM recognized_frags")
                   .fetchone()[0])


def item(item_id: str) -> ReviewItem | None:
    kind, _, sid = item_id.partition(":")
    if kind != FRAG:
        return None
    with _rec() as c:
        r = c.execute(
            "SELECT id, content_hash, demo_name, server_time_ms, round, "
            "weapon_name, victim_client, highlight_score, classes, reasons "
            "FROM recognized_frags WHERE id=?", (int(sid),)).fetchone()
        if not r:
            return None
        rank = int(c.execute(
            "SELECT COUNT(*) FROM recognized_frags WHERE highlight_score < ? "
            "OR (highlight_score = ? AND id <= ?)",
            (r["highlight_score"], r["highlight_score"], r["id"])).fetchone()[0])
    rv = reviews([item_id]).get(item_id) or {}
    return ReviewItem(
        item_id=item_id, item_type=FRAG, source_id=int(r["id"]),
        content_hash=r["content_hash"] or "", demo_name=r["demo_name"] or "",
        server_time_ms=int(r["server_time_ms"]),
        machine_score=float(r["highlight_score"]), machine_rank=rank,
        total_items=count_items(), weapon=r["weapon_name"] or "",
        victim=r["victim_client"], round_no=r["round"], why=_why(r),
        human_role=(rv.get("human_role") or None) or None,
        note=rv.get("note") or "")


# ── progress and pools ──────────────────────────────────────────────────────

def progress(item_type: str = FRAG) -> dict[str, Any]:
    total = count_items(item_type)
    with conn() as c:
        counts = {r["human_role"]: r["n"] for r in c.execute(
            "SELECT human_role, COUNT(*) n FROM human_reviews "
            "WHERE item_type=? AND human_role<>'' GROUP BY 1", (item_type,))}
    reviewed = sum(counts.values())
    return {"item_type": item_type, "total": total, "reviewed": reviewed,
            "unreviewed": total - reviewed,
            "roles": {r: counts.get(r, 0) for r in ROLES},
            "labels": ROLE_LABEL}


def pool(role: str, item_type: str | None = None, weapon: str | None = None,
         limit: int = 200) -> list[dict[str, Any]]:
    """Everything the user gave one role. This is what makes the review
    worth doing: ten rails in a row is a query, not a memory."""
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}")
    with conn() as c:
        sql = "SELECT * FROM human_reviews WHERE human_role=?"
        args: list[Any] = [role]
        if item_type:
            sql += " AND item_type=?"
            args.append(item_type)
        sql += " ORDER BY reviewed_at DESC LIMIT ?"
        args.append(limit)
        rows = [dict(r) for r in c.execute(sql, args)]
    if not weapon:
        return rows
    ids = [int(r["source_id"]) for r in rows if r["item_type"] == FRAG]
    if not ids:
        return []
    with _rec() as c:
        qs = ",".join("?" * len(ids))
        keep = {r[0] for r in c.execute(
            f"SELECT id FROM recognized_frags WHERE id IN ({qs}) "
            "AND weapon_name = ?", ids + [weapon])}
    return [r for r in rows if int(r["source_id"]) in keep]


def search_notes(text: str, limit: int = 100) -> list[dict[str, Any]]:
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM human_reviews WHERE note LIKE ? "
            "ORDER BY reviewed_at DESC LIMIT ?", (f"%{text}%", limit))]


def import_legacy() -> dict[str, Any]:
    """Bring forward verdicts from the older editorial_reviews table.

    Only where the mapping is unambiguous. A guess here would put words in
    the user's mouth about their own career.
    """
    mapping = {"FEATURE": T1_FEATURE_FX, "TRANSITION": T2_TRANSITION,
               "RHYTHM": T3_RHYTHM_MONTAGE, "KEEP": T4_KEEP_NORMAL,
               "PASS": T5_PASS_FILLER}
    moved, skipped = 0, []
    with conn() as c:
        try:
            rows = c.execute("SELECT frag_id, verdict, notes FROM "
                             "editorial_reviews").fetchall()
        except sqlite3.OperationalError:
            return {"imported": 0, "skipped": [], "note": "no legacy table"}
    for r in rows:
        role = mapping.get((r["verdict"] or "").upper())
        if not role:
            skipped.append({"frag_id": r["frag_id"], "verdict": r["verdict"]})
            continue
        record(f"{FRAG}:{r['frag_id']}", FRAG, int(r["frag_id"]), role,
               r["notes"] or "")
        moved += 1
    return {"imported": moved, "skipped": skipped}
