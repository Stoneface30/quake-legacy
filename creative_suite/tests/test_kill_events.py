"""Kill-event derivation: who killed whom, and who merely watched.

The derivation itself is a parse, so these tests pin the two things that are
judgement rather than decoding: how an attacker slot is classified, and the
refusal to collapse an observation into the historical event it observed.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine" / "parser"))
import derive_kill_events as dk   # noqa: E402


# ── two questions, answered separately ──────────────────────────────────────

def test_who_the_attacker_is_and_how_they_died_are_different_questions():
    """A telefrag has a player attacker. A rocket suicide has a player
    attacker who is the victim. Deriving either answer from the other loses
    a real distinction."""
    assert dk.classify(3, 5, 6) == (dk.KILLER_PLAYER, dk.CAUSE_PLAYER_KILL)
    assert dk.classify(3, 5, 18) == (dk.KILLER_PLAYER, dk.CAUSE_TELEFRAG)
    assert dk.classify(5, 5, 7) == (dk.KILLER_SELF, dk.CAUSE_SUICIDE)
    assert dk.classify(1022, 5, 19) == (dk.KILLER_WORLD, dk.CAUSE_ENVIRONMENT)


def test_the_world_is_not_a_player():
    """ENTITYNUM_WORLD is what the server names when nobody killed you.
    Forcing it into 'player A killed player B' invents an attacker."""
    for world in (dk.ENTITYNUM_WORLD, dk.ENTITYNUM_NONE):
        cls, _ = dk.classify(world, 5, 16)
        assert cls == dk.KILLER_WORLD


def test_falling_into_the_void_is_environment_not_a_frag():
    for mod in dk.ENVIRONMENT_MODS:
        assert dk.classify(1022, 5, mod)[1] == dk.CAUSE_ENVIRONMENT


def test_telefrag_uses_the_means_of_death_not_a_weapon_id():
    """MOD_TELEFRAG is 18. MOD_BFG is 12. These are different namespaces and
    reading one as the other returned zero telefrags for a corpus that has
    them."""
    assert dk.MOD_TELEFRAG == 18
    assert dk.classify(3, 5, 12)[1] == dk.CAUSE_PLAYER_KILL     # BFG, not telefrag
    assert dk.classify(3, 5, 18)[1] == dk.CAUSE_TELEFRAG


def test_an_unknown_attacker_stays_unknown():
    assert dk.classify(None, 5, 6)[0] == dk.KILLER_UNKNOWN
    assert dk.classify(500, 5, None) == (dk.KILLER_NON_PLAYER, dk.CAUSE_UNKNOWN)


# ── an observation is not the event ─────────────────────────────────────────

def test_the_same_kill_seen_from_two_demos_shares_one_fingerprint():
    """Two players in one match record two demos. Both see the same kill at
    the same server time. The fingerprint recognises that; it does not act
    on it -- each observation keeps its own row."""
    a = dk.fingerprint("campgrounds", 60000, 3, 5, 6)
    b = dk.fingerprint("Campgrounds", 60000, 3, 5, 6)
    assert a == b
    assert a != dk.fingerprint("campgrounds", 60001, 3, 5, 6)
    assert a != dk.fingerprint("bloodrun", 60000, 3, 5, 6)


# ── names ───────────────────────────────────────────────────────────────────

def test_normalize_strips_colours_and_keeps_the_raw_name_a_separate_concern():
    assert dk.normalize("^4pTn^3.^7 NaikoMarie") == "ptn. naikomarie"
    assert dk.normalize("^1Tr4sH") == "tr4sh"
    assert dk.normalize(None) is None
    assert dk.normalize("^1^2^3") is None      # colours only is not a name
