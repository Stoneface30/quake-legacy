"""Quake name handling: colour is presentation, never identity.

ONE RULE, AND IT IS NARROWER THAN IT LOOKS. A Quake Live colour code is a
caret followed by a SINGLE DIGIT. `^1` is red. `^x` is not a colour code at
all -- it is a caret and the letter x, both of which are part of the name.

Four places in this codebase stripped `\\^[0-9a-zA-Z]`, which also eats
caret+letter. Measured across all 4,902 distinct names in the corpus, the two
patterns currently agree on every one, so nothing on disk is wrong today.
That is luck, not correctness: the first player named `Player^name` would
have been silently renamed to `Playername` and quietly merged with anyone
already called that. Identity merges are the one thing this project refuses
to do by accident, so the rule is fixed and pinned rather than left to hold.

FOUR NAMES FOR ONE PLAYER, KEPT APART.

    raw_name         exactly what the server sent, colour codes and all
    display_name     what a human should see -- colours removed, case kept
    color_stripped   the same string, for anything that must not carry markup
    normalized       lowercased, for MATCHING only

Stripping colour is formatting. It is NOT identity resolution: two players
whose normalized names collide are still two people until someone says
otherwise. `identity_id` is the answer to that question and it comes from
`identity.py`, where a human writes it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Caret plus ONE DIGIT. Nothing else. `\^.` and `\^[0-9a-zA-Z]` are both
# wrong: they consume letters that belong to the name.
COLOR_CODE = re.compile(r"\^[0-9]")


def strip_colors(name: str | None) -> str:
    """Remove colour codes and nothing else. `abc^xdef` survives intact."""
    if not name:
        return ""
    return COLOR_CODE.sub("", name)


def display_name(name: str | None) -> str:
    """What a person should read. Case preserved -- `Tr4sH` is how they
    wrote it, and flattening that loses something real."""
    return strip_colors(name).strip()


def normalize(name: str | None) -> str | None:
    """The matching key. Lowercased, colours gone, whitespace trimmed.

    Returns None for a name that is only colour codes, because that is an
    absence rather than an empty player.
    """
    v = display_name(name).lower()
    return v or None


@dataclass(frozen=True)
class QuakeName:
    """One observed name, in every form the system needs at once.

    Carried together so no caller has to remember which variant a given
    field holds -- the mix-up that turns a display concern into an identity
    claim.
    """
    raw_name: str
    display_name: str
    color_stripped_name: str
    normalized_identity_name: str | None
    identity_id: str | None = None      # only a human fills this in

    @classmethod
    def of(cls, raw: str | None, identity_id: str | None = None) -> "QuakeName":
        stripped = strip_colors(raw)
        return cls(raw_name=raw or "", display_name=stripped.strip(),
                   color_stripped_name=stripped,
                   normalized_identity_name=normalize(raw),
                   identity_id=identity_id)
