"""What the director already sees in their head.

THE VERDICT SAYS WHERE A MOMENT BELONGS. THE ANNOTATION SAYS WHAT TO DO WITH
IT. "freeze before impact, xray wall, enemy POV after" is not metadata about
a frag -- it is a shot already designed, written down at the only moment when
the person had it in mind. Losing it, or paraphrasing it, throws away the
most expensive thing in the pipeline: attention that has already been spent.

THE RAW TEXT IS THE TRUTH AND IS NEVER REWRITTEN. Not summarised, not
normalised, not replaced by what a parser thought it meant. Everything below
is additive: `parse_intent` produces SUGGESTIONS that sit beside the words
and can be wrong without costing anything, because the words are still there.

A REQUEST FOR SOMETHING THAT DOES NOT EXIST IS STILL VALID. "xray the wall
then enemy POV" may have no implementation route today. That is a fact about
the toolkit, not about the idea, and the annotation is kept as
CREATIVE_REQUEST_EXISTS / IMPLEMENTATION_ROUTE_UNKNOWN rather than discarded
for being ahead of the code.

TWO SCOPES. A note can belong to the moment ("enemy POV second pass") or to
the whole round ("ClanWar story -- start top map, 4v4 count, pTn morph,
finish on the win"). They are different objects and are stored separately;
neither is required.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Sequence
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
EDITORIAL_DB = REPO_ROOT / "creative_suite" / "database" / "editorial.db"

ANNOTATION_VERSION = "annotation-v1"

# Provenance, matching the review rules: only a person writes creative truth.
HUMAN_USER = "HUMAN_USER"
AI_SUGGESTION = "AI_SUGGESTION"
TEST = "TEST"

# When a note asks for something the toolkit cannot do yet.
CREATIVE_REQUEST_EXISTS = "CREATIVE_REQUEST_EXISTS"
IMPLEMENTATION_ROUTE_UNKNOWN = "IMPLEMENTATION_ROUTE_UNKNOWN"

# The vocabulary the annotation field suggests. NOT a list of buttons and not
# a closed set -- typing stays freeform, and a word that is not here is not
# wrong. It exists so the common ideas spell themselves the same way twice,
# which is what makes them searchable later.
VOCABULARY = (
    "XRAY", "GHOST", "FREEZE", "SLOWMO", "REPLAY", "REWIND", "STUTTER",
    "ENEMY_POV", "PROJECTILE_CAM", "FIXED_IMPACT_CAM", "TOP_MAP",
    "FULL_ROUND", "CLANWAR", "PTN_MORPH", "TEXTURE_MORPH", "WORLD_TRANSFORM",
    "TELEPORT_TRANSITION", "ROCKET_TRANSITION", "GRENADE_DOUBLE_VIEW",
    "CLEAN_FPV", "PIP", "CHAT", "ROUND_COUNTER", "DAMAGE_COUNTER",
)

# Dimensions a note can speak to. A note usually speaks to several.
EFFECT_INTENT = "EFFECT_INTENT"
CAMERA_INTENT = "CAMERA_INTENT"
TIMING_INTENT = "TIMING_INTENT"
TRANSITION_INTENT = "TRANSITION_INTENT"
REPLAY_INTENT = "REPLAY_INTENT"
ROUND_INTENT = "ROUND_INTENT"
AUDIO_INTENT = "AUDIO_INTENT"
INFORMATION_INTENT = "INFORMATION_INTENT"

# Phrases that reliably mean one of those. Deliberately shallow: a shallow
# reader that is obviously incomplete is safer than a clever one that quietly
# decides it understood. Anything unmatched simply stays in the raw text,
# where the user can still find it by searching for their own words.
_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (EFFECT_INTENT, "XRAY", r"\bx-?ray\b|\bsee through\b|\bthrough the wall\b"),
    (EFFECT_INTENT, "GHOST", r"\bghost\b"),
    (EFFECT_INTENT, "WORLD_TRANSFORM", r"\bmorph\b|\bworld transform\b|\btexture morph\b"),
    (EFFECT_INTENT, "PTN_MORPH", r"\bptn morph\b|\bclan morph\b"),
    (TIMING_INTENT, "FREEZE", r"\bfreeze\b|\bhold on\b|\bpause on\b"),
    (TIMING_INTENT, "SLOW_MOTION", r"\bslow ?mo\b|\bslow motion\b|\bslow\b"),
    (TIMING_INTENT, "SPEED_UP", r"\bspeed ?up\b|\bfast forward\b"),
    (TIMING_INTENT, "STUTTER", r"\bstutter\b"),
    (CAMERA_INTENT, "ENEMY_POV", r"\benemy pov\b|\btheir pov\b|\bvictim pov\b"),
    (CAMERA_INTENT, "PROJECTILE_CAM", r"\brocket cam\b|\bprojectile cam\b|\bfollow the rocket\b"),
    (CAMERA_INTENT, "FIXED_IMPACT_CAM", r"\bimpact cam\b|\bfixed cam\b"),
    (CAMERA_INTENT, "TOP_MAP", r"\btop map\b|\babove the map\b|\btop down\b"),
    (CAMERA_INTENT, "CLEAN_FPV", r"\bclean fpv\b|\bfpv only\b"),
    (REPLAY_INTENT, "SECOND_VIEW", r"\bsecond view\b|\bdouble view\b|\breplay\b|\bagain from\b"),
    (REPLAY_INTENT, "REWIND", r"\brewind\b"),
    (TRANSITION_INTENT, "TRANSITION", r"\btransition\b|\binto the next\b|\bcut to\b"),
    (TRANSITION_INTENT, "TELEPORT_TRANSITION", r"\bteleport transition\b"),
    (TRANSITION_INTENT, "ROCKET_TRANSITION", r"\brocket transition\b|\bthrough the doorway\b"),
    (ROUND_INTENT, "FULL_ROUND", r"\bfull round\b|\bwhole round\b|\bround story\b"),
    (ROUND_INTENT, "CLANWAR", r"\bclanwar\b|\bclan war\b|\bteamfight\b|\bteam fight\b"),
    (AUDIO_INTENT, "MUSIC_SYNC", r"\bon the beat\b|\bbeat\b|\bdrop\b|\bwith the music\b"),
    (INFORMATION_INTENT, "ROUND_COUNTER", r"\bround counter\b|\balive count\b|\b\dv\d\b"),
    (INFORMATION_INTENT, "DAMAGE_COUNTER", r"\bdamage counter\b|\bdamage number\b"),
    (INFORMATION_INTENT, "CHAT", r"\bchat\b"),
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS round_annotations (
    round_key   TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    round        INTEGER NOT NULL,
    annotation   TEXT NOT NULL,
    provenance   TEXT NOT NULL DEFAULT 'HUMAN_USER',
    written_at   TEXT NOT NULL,
    version      TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_ra_hash ON round_annotations(content_hash, round);
CREATE TABLE IF NOT EXISTS scene_event_notes (
    event_id    TEXT PRIMARY KEY,
    annotation  TEXT NOT NULL,
    provenance  TEXT NOT NULL DEFAULT 'HUMAN_USER',
    written_at  TEXT NOT NULL);
"""


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(EDITORIAL_DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(_SCHEMA)
    return c


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_intent(text: str | None) -> dict[str, Any]:
    """Read structured suggestions out of a note. Never authoritative.

    The raw wording remains the truth. This exists so a later query can ask
    "what did the director want an XRAY on" without the user having had to
    phrase it in any particular way -- and when it misreads something, the
    words are still there to search directly.
    """
    raw = text or ""
    found: dict[str, list[str]] = {}
    for dim, value, pattern in _PATTERNS:
        if re.search(pattern, raw, re.I):
            found.setdefault(dim, [])
            if value not in found[dim]:
                found[dim].append(value)
    return {
        "human_annotation_raw": raw,
        "suggested_intent": found,
        "provenance": AI_SUGGESTION,
        "note": ("suggestions read from the director's own words. The raw "
                 "text is the truth; these can be wrong without costing "
                 "anything"),
    }


def vocabulary_hits(text: str | None) -> list[str]:
    """Which vocabulary terms the note actually used."""
    raw = (text or "").upper()
    return [v for v in VOCABULARY if v.replace("_", " ") in raw or v in raw]


def round_key(content_hash: str, round_no: int) -> str:
    return f"{content_hash}:{round_no}"


def set_round_annotation(content_hash: str, round_no: int, annotation: str,
                         provenance: str = HUMAN_USER) -> dict[str, Any]:
    """A note about the whole round, kept apart from the moment's own note."""
    key = round_key(content_hash, int(round_no))
    now = _now()
    with conn() as c:
        c.execute(
            "INSERT INTO round_annotations(round_key, content_hash, round, "
            "annotation, provenance, written_at, version) "
            "VALUES (?,?,?,?,?,?,?) ON CONFLICT(round_key) DO UPDATE SET "
            "annotation=excluded.annotation, provenance=excluded.provenance, "
            "written_at=excluded.written_at",
            (key, content_hash, int(round_no), annotation, provenance, now,
             ANNOTATION_VERSION))
    return {"round_key": key, "annotation": annotation, "written_at": now,
            "provenance": provenance}


def get_round_annotation(content_hash: str, round_no: int
                         ) -> dict[str, Any] | None:
    with conn() as c:
        r = c.execute("SELECT * FROM round_annotations WHERE round_key=?",
                      (round_key(content_hash, int(round_no)),)).fetchone()
    return dict(r) if r else None


# -- scene EVENT notes -------------------------------------------------------
#
# A note on a moment that carries no verdict. A jump pad can say "music
# builds here" without becoming a reviewable frag and without demanding a
# T1-T5 role.
#
# THIS LIVED IN THE HTTP ROUTER, and that was the defect. The router created
# the table on demand, so the only way to read a note was to make a web
# request -- and `scene.build_scene`, which is what production reads, never
# did. The director's words were being stored and then never loaded by
# anything except the page that wrote them. Storage belongs next to the
# other annotations, where the scene builder can reach it.


def set_event_annotation(event_id: str, annotation: str,
                         provenance: str = HUMAN_USER) -> dict[str, Any]:
    """A directing note on one scene-rail event, addressed by `event_id`."""
    now = _now()
    with conn() as c:
        c.execute(
            "INSERT INTO scene_event_notes(event_id, annotation, provenance, "
            "written_at) VALUES (?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET "
            "annotation=excluded.annotation, provenance=excluded.provenance, "
            "written_at=excluded.written_at",
            (event_id, annotation, provenance, now))
    return {"event_id": event_id, "annotation": annotation,
            "provenance": provenance, "written_at": now}


def get_event_annotation(event_id: str) -> dict[str, Any] | None:
    with conn() as c:
        r = c.execute("SELECT * FROM scene_event_notes WHERE event_id=?",
                      (event_id,)).fetchone()
    return dict(r) if r else None


def event_annotations(event_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
    """Every note for a set of rail events, in one query.

    `build_scene` calls this once per scene rather than once per event: a
    scene can carry thirty movement runs and none of them is worth a round
    trip of its own.
    """
    ids = list(event_ids)
    if not ids:
        return {}
    out: dict[str, dict[str, Any]] = {}
    with conn() as c:
        for i in range(0, len(ids), 500):       # SQLite variable limit
            chunk = ids[i:i + 500]
            qs = ",".join("?" * len(chunk))
            for r in c.execute(
                    f"SELECT * FROM scene_event_notes WHERE event_id IN ({qs})",
                    chunk):
                out[r["event_id"]] = dict(r)
    return out


def search(text: str, role: str | None = None, item_type: str | None = None,
           limit: int = 200) -> dict[str, Any]:
    """Find annotations by the director's own words, combined with role.

    Substring, case-insensitive, over the raw text -- so searching for
    "xray" finds it however it was written, and searching for a phrase
    nobody anticipated still works.
    """
    from creative_suite.engine import review_corpus as rc
    sql = ["SELECT * FROM human_reviews WHERE note LIKE ? AND note <> ''"]
    params: list[Any] = [f"%{text}%"]
    if role:
        if role not in rc.ROLES:
            raise ValueError(f"unknown role {role!r}")
        sql.append("AND human_role = ?")
        params.append(role)
    if item_type:
        sql.append("AND item_type = ?")
        params.append(item_type)
    # Only a human's own words are creative truth.
    qs = ",".join("?" * len(rc.HUMAN_PROVENANCE))
    sql.append(f"AND provenance IN ({qs})")
    params.extend(rc.HUMAN_PROVENANCE)
    sql.append("ORDER BY reviewed_at DESC LIMIT ?")
    params.append(int(limit))
    with conn() as c:
        rows = [dict(r) for r in c.execute(" ".join(sql), params)]
    for r in rows:
        r["human_annotation_raw"] = r.get("note", "")
        r["suggested_intent"] = parse_intent(r.get("note"))["suggested_intent"]
    with conn() as c:
        rounds = [dict(r) for r in c.execute(
            "SELECT * FROM round_annotations WHERE annotation LIKE ? "
            "ORDER BY written_at DESC LIMIT ?", (f"%{text}%", int(limit)))]
    return {"query": text, "role": role, "moments": rows, "rounds": rounds,
            "total": len(rows) + len(rounds)}


def status() -> dict[str, Any]:
    """How much creative intent has been written down so far."""
    from creative_suite.engine import review_corpus as rc
    with conn() as c:
        qs = ",".join("?" * len(rc.HUMAN_PROVENANCE))
        moments = c.execute(
            f"SELECT COUNT(*) FROM human_reviews WHERE note <> '' "
            f"AND provenance IN ({qs})", rc.HUMAN_PROVENANCE).fetchone()[0]
        rounds = c.execute("SELECT COUNT(*) FROM round_annotations "
                           "WHERE provenance=?", (HUMAN_USER,)).fetchone()[0]
        texts = [r[0] for r in c.execute(
            f"SELECT note FROM human_reviews WHERE note <> '' "
            f"AND provenance IN ({qs})", rc.HUMAN_PROVENANCE)]
    dims: dict[str, int] = {}
    for t in texts:
        for dim in parse_intent(t)["suggested_intent"]:
            dims[dim] = dims.get(dim, 0) + 1
    return {"moment_annotations": moments, "round_annotations": rounds,
            "intent_dimensions_seen": dims,
            "vocabulary_size": len(VOCABULARY),
            "rule": ("the raw wording is the truth; parsed intent is a "
                     "suggestion and never replaces it")}
