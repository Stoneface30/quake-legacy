"""WHAT THE DIRECTOR SAID, KEPT AS THEY SAID IT.

The user writes ideas in their own words, and those words are the record. This
module never rewrites a note, never replaces it with a recipe id, and never
decides that an idea "is really" something already implemented. It reads the
note ADDITIVELY: alongside the untouched text it records which kinds of intent
appear in it, and whether the engine has a route.

    EffectIntent          something should look different
    CameraIntent          the eye should be somewhere or move somehow
    TimingIntent          time should stretch, compress, hold or repeat
    TransitionIntent      how one shot becomes the next
    AudioIntent           what is heard, or not heard
    CharacterIntent       who is on screen and what they do
    ReconstructionIntent  something not recorded should be rebuilt

When nothing in the grammar matches, the honest answer is not "unsupported":
it is CREATIVE_REQUEST_EXISTS with IMPLEMENTATION_ROUTE_UNKNOWN. The idea is
real, and the gap is ours.

An idea repeated often enough is a candidate to become an EffectRecipe -- but
only once its requirements are understood. One note is not architecture.
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum

from engine.pantheon import store as S

INTENT_DB = "creative_intents.db"

SCHEMA = """
create table if not exists notes (
  note_id text primary key,
  subject text,
  text text not null,
  intents text not null,
  matched_recipes text not null,
  route text not null,
  written_at real);
create index if not exists ix_notes_subject on notes(subject, written_at);
"""


class Kind(str, Enum):
    EFFECT = "EffectIntent"
    CAMERA = "CameraIntent"
    TIMING = "TimingIntent"
    TRANSITION = "TransitionIntent"
    AUDIO = "AudioIntent"
    CHARACTER = "CharacterIntent"
    RECONSTRUCTION = "ReconstructionIntent"


class Route(str, Enum):
    RECIPE_EXISTS = "RECIPE_EXISTS"
    IMPLEMENTATION_ROUTE_UNKNOWN = "IMPLEMENTATION_ROUTE_UNKNOWN"


# Words the project already uses for these things. Deliberately small: a
# guesser that matches everything tells the reviewer nothing, and the note
# itself remains the authority either way.
_CUES: dict[Kind, tuple[str, ...]] = {
    Kind.EFFECT: ("xray", "x-ray", "wallhack", "wireframe", "glow", "outline",
                  "silhouette", "colour", "color", "shader", "morph", "trail",
                  "invisible", "transparent", "highlight"),
    Kind.CAMERA: ("camera", "angle", "pov", "point of view", "follow", "chase",
                  "orbit", "fly", "flythrough", "zoom", "pan", "shot", "framing",
                  "behind", "overhead", "top down", "first person", "third person"),
    Kind.TIMING: ("slow", "slowmo", "slow-mo", "speed", "fast", "freeze",
                  "hold", "stutter", "retime", "ramp", "pause", "loop", "repeat"),
    Kind.TRANSITION: ("cut", "transition", "fade", "wipe", "seam", "into",
                      "crossfade", "dissolve"),
    Kind.AUDIO: ("sound", "audio", "music", "beat", "drop", "silence", "voice",
                 "hit sound", "quiet"),
    Kind.CHARACTER: ("keel", "anarki", "visor", "xaero", "presenter", "actor",
                     "character", "model", "skin", "narrator", "pointing"),
    Kind.RECONSTRUCTION: ("rebuild", "reconstruct", "recreate", "synthetic",
                          "re-enact", "reenact", "simulate", "what if"),
}


@dataclass
class Note:
    note_id: str
    text: str                              # verbatim, never edited
    subject: str | None = None             # a performance id, a round, a part
    intents: tuple[str, ...] = ()
    matched_recipes: tuple[str, ...] = ()
    route: Route = Route.IMPLEMENTATION_ROUTE_UNKNOWN
    written_at: float = 0.0

    def as_dict(self) -> dict:
        return {"note_id": self.note_id, "subject": self.subject,
                "text": self.text, "intents": list(self.intents),
                "matched_recipes": list(self.matched_recipes),
                "route": self.route.value, "written_at": self.written_at}


def read(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(intent kinds, recipes the note plausibly names). Additive only."""
    from engine.pantheon import effect_recipes as ER
    low = f" {text.lower()} "
    kinds = tuple(k.value for k, cues in _CUES.items()
                  if any(re.search(rf"\b{re.escape(c)}", low) for c in cues))
    named = tuple(r.id for r in ER.RECIPES
                  if r.id.lower().replace("_", " ") in low or r.id.lower() in low)
    return kinds, named


def capture(text: str, *, subject: str | None = None,
            note_id: str | None = None) -> Note:
    """Keep an idea. The text is stored exactly as written."""
    kinds, named = read(text)
    n = Note(note_id=note_id or f"NOTE:{int(time.time() * 1000)}",
             text=text, subject=subject, intents=kinds, matched_recipes=named,
             route=Route.RECIPE_EXISTS if named else Route.IMPLEMENTATION_ROUTE_UNKNOWN,
             written_at=time.time())
    con = _open()
    try:
        con.execute("insert or replace into notes values(?,?,?,?,?,?,?)",
                    (n.note_id, n.subject, n.text, json.dumps(list(n.intents)),
                     json.dumps(list(n.matched_recipes)), n.route.value,
                     n.written_at))
        con.commit()
    finally:
        con.close()
    return n


def _open() -> sqlite3.Connection:
    p = S.store_root() / INTENT_DB
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p, timeout=60)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def notes(subject: str | None = None) -> list[Note]:
    con = _open()
    try:
        rows = (con.execute("select * from notes where subject=? order by written_at",
                            (subject,)).fetchall() if subject else
                con.execute("select * from notes order by written_at").fetchall())
    finally:
        con.close()
    return [Note(r["note_id"], r["text"], r["subject"],
                 tuple(json.loads(r["intents"])),
                 tuple(json.loads(r["matched_recipes"])),
                 Route(r["route"]), r["written_at"]) for r in rows]


def unrouted() -> list[Note]:
    """Ideas the engine has no route for. This list is the honest backlog."""
    return [n for n in notes() if n.route is Route.IMPLEMENTATION_ROUTE_UNKNOWN]


def recurring(*, at_least: int = 3) -> list[dict]:
    """Intent shapes the director keeps asking for and nothing implements.

    A candidate for promotion into an EffectRecipe -- once someone understands
    what it would require. Promotion is never automatic: one repeated phrase
    is not a semantic contract.
    """
    counts: dict[tuple[str, ...], list[str]] = {}
    for n in unrouted():
        if not n.intents:
            continue
        counts.setdefault(tuple(sorted(n.intents)), []).append(n.note_id)
    return [{"intents": list(k), "notes": v, "count": len(v),
             "status": "CANDIDATE_FOR_RECIPE"}
            for k, v in counts.items() if len(v) >= at_least]


def report() -> dict:
    all_notes = notes()
    return {"db": str(S.store_root() / INTENT_DB), "notes": len(all_notes),
            "unrouted": len(unrouted()),
            "recurring_candidates": recurring()}
