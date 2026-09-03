"""Colour codes are presentation. A caret and a letter are part of the name.

The distinction matters because getting it wrong renames people. `Player^name`
stripped with the wider pattern becomes `Playername`, which then matches
anyone actually called that -- an identity merge performed by a regex, which
is the one thing this project refuses to do by accident.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from creative_suite.engine import quake_names as qn        # noqa: E402

CARET = chr(94)


def test_a_colour_code_is_a_caret_and_one_digit():
    assert qn.COLOR_CODE.pattern == r"\^[0-9]"
    assert qn.strip_colors(f"{CARET}1Tr4{CARET}7sH") == "Tr4sH"
    assert qn.strip_colors(f"{CARET}7sere{CARET}4k{CARET}7e") == "sereke"
    assert qn.strip_colors(f"abc{CARET}3def") == "abcdef"


def test_a_caret_and_a_letter_is_part_of_the_name():
    r"""The bug this file exists to prevent. Four modules used
    \^[0-9a-zA-Z], which eats the x AND the caret."""
    assert qn.strip_colors(f"abc{CARET}xdef") == f"abc{CARET}xdef"
    assert qn.strip_colors(f"Player{CARET}name") == f"Player{CARET}name"
    assert qn.normalize(f"Player{CARET}name") == f"player{CARET}name"


def test_a_plain_name_is_untouched():
    assert qn.strip_colors("plainname") == "plainname"
    assert qn.normalize("plainname") == "plainname"


def test_case_survives_display_and_dies_only_in_the_matching_key():
    """`Tr4sH` is how they wrote it. Flattening that for display loses
    something real; flattening it for MATCHING is the whole point."""
    assert qn.display_name(f"{CARET}1Tr4{CARET}7sH") == "Tr4sH"
    assert qn.normalize(f"{CARET}1Tr4{CARET}7sH") == "tr4sh"


def test_a_name_that_is_only_colour_is_an_absence():
    assert qn.normalize(f"{CARET}1{CARET}2{CARET}3") is None
    assert qn.normalize("") is None
    assert qn.normalize(None) is None


def test_the_four_forms_travel_together_and_identity_is_not_one_of_them():
    """Stripping colour is formatting. It is not identity resolution, so
    identity_id stays empty until a human fills it in."""
    n = qn.QuakeName.of(f"{CARET}4pTn{CARET}3. {CARET}7NaikoMarie")
    assert n.raw_name == f"{CARET}4pTn{CARET}3. {CARET}7NaikoMarie"
    assert n.display_name == "pTn. NaikoMarie"
    assert n.normalized_identity_name == "ptn. naikomarie"
    assert n.identity_id is None


def test_every_module_shares_the_one_rule():
    """Four separate strippers existed. A rule copied four times is a rule
    that will diverge."""
    from creative_suite.engine import identity, review_corpus, public_clip_export
    for mod, attr in ((identity, "_COLOR"), (review_corpus, "_COLOR_RE"),
                      (public_clip_export, "_COLOR")):
        assert getattr(mod, attr) is qn.COLOR_CODE, mod.__name__


def test_the_derivation_uses_the_same_rule():
    """derive_kill_events runs as a script with its own import path, so it
    carries its own copy -- which must still be the same pattern."""
    src = (Path(__file__).resolve().parents[2] / "engine" / "parser"
           / "derive_kill_events.py").read_text(encoding="utf-8")
    assert r'_COLOR = re.compile(r"\^[0-9]")' in src
    assert "0-9a-zA-Z" not in src
