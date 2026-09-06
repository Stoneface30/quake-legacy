"""Tests for the prologue workstream.

These do not test that the film is good. They test the three things that
would quietly make it dishonest:

  1. a number reaching the screen that nobody derived,
  2. synthetic teaching material being counted as career history,
  3. this workstream reaching into the corpus and spending a hero frag that
     human review has not yet ruled on.

Every test here runs without the 10 GB caches. Tests that need them are
marked and skip cleanly, so this file stays useful in CI and on a machine
that does not have the archive.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest

from creative_suite.prologue import facts, primitives as p, slots

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs/prologue"
HAVE_CACHES = facts.RECOGNITION_DB.exists() and facts.REBUILT_DB.exists()
needs_caches = pytest.mark.skipif(not HAVE_CACHES, reason="archive caches absent")


# ── the ledger is the only source of on-screen numbers ──────────────────────

def test_every_ledger_entry_has_a_derivation_and_a_note():
    for key, fn, expected, _on_screen, note in facts.LEDGER:
        assert callable(fn), f"{key} has no derivation"
        assert expected, f"{key} has no expected value"
        assert note.strip(), f"{key} has no note explaining its denominator"


def test_recorder_own_archive_is_never_showable():
    """36,607 means "the killer recorded this demo", not "the user's frags".

    It is often somebody else's kill seen from this recorder's camera, so a
    caption calling it the user's would be false. It must have no permitted
    wording at all.
    """
    assert 36607 not in {v for _k, _f, v, _s, _n in facts.LEDGER}
    for _k, _f, _v, on_screen, _n in facts.LEDGER:
        assert on_screen is None or "36,607" not in on_screen


def test_the_counter_inflated_round_total_is_never_permitted():
    """138,301 is sum(demos.rounds) and 26 demos with a broken counter own
    56,349 of it. The canonical figure is round_kills_v1."""
    for _k, _f, _v, on_screen, _n in facts.LEDGER:
        assert on_screen is None or "138,301" not in on_screen
    rounds = dict((k, v) for k, _f, v, _s, _n in facts.LEDGER)["canonical_rounds"]
    assert rounds == 78730


def test_hours_are_never_stated_precisely():
    """The hours figure is a lower bound, so an exact number would overclaim."""
    copy = facts.screen_copy()["recording_hours"]
    assert copy == "OVER 450 HOURS"
    assert "452" not in copy and "453" not in copy


def test_screen_copy_covers_every_showable_fact():
    showable = {k for k, _f, _v, s, _n in facts.LEDGER if s}
    assert set(facts.screen_copy()) == showable


@needs_caches
def test_every_ledger_fact_still_verifies_against_the_live_caches():
    bad = [r for r in facts.verify() if not r["ok"]]
    assert not bad, f"facts drifted from the caches: {bad}"


# ── synthetic material must never become career history ─────────────────────

@needs_caches
def test_synthetic_explainer_material_is_absent_from_every_corpus_count():
    """The Part 2 explainer is recorded and derived like any demo, so without
    a provenance guard its kills would inflate the archive totals the film
    puts on screen."""
    with sqlite3.connect(
            f"file:{facts.RECOGNITION_DB.as_posix()}?mode=ro", uri=True) as c:
        cols = {r[1] for r in c.execute("PRAGMA table_info(kill_events_v1)")}
        assert "event_provenance" in cols
        leaked = c.execute(
            "select count(*) from kill_events_v1 where event_provenance = ?",
            (facts.SYNTHETIC_EXPLAINER,)).fetchone()[0]
    assert leaked == 0, (
        f"{leaked} SYNTHETIC_EXPLAINER kills are inside the canonical corpus; "
        "career totals shown in Part 3 would be overstated")


def test_synthetic_provenance_is_not_a_corpus_name():
    """If it were selectable as a corpus it could be reviewed and then
    placed, which is exactly what it must never be."""
    from creative_suite.engine import review_corpus as rc
    assert facts.SYNTHETIC_EXPLAINER not in rc.CORPORA
    assert facts.SYNTHETIC_EXPLAINER not in rc.PROVENANCES


# ── nothing is spent before human review says so ────────────────────────────

def test_no_slot_is_pre_filled():
    """A slot states a requirement and counts a pool. It never names a clip."""
    for s in slots.SLOTS:
        assert s.status in ("OPEN", "NO POOL"), s
        assert s.requirement.strip()


def test_slots_never_accept_passed_material():
    """T5_PASS means "not primary gameplay material", and the opening of the
    film is the most primary place there is."""
    assert "T5_PASS_FILLER" not in slots.ACCEPTS_ROLES
    assert "T4_KEEP_NORMAL" not in slots.ACCEPTS_ROLES


def test_intro_hint_matches_the_phrases_the_user_actually_writes():
    for note in ("good first shot", "use for INTRO", "explain quake here",
                 "CA explanation", "opener maybe", "prologue candidate"):
        assert slots.INTRO_HINTS.search(note), note
    for note in ("nice rail", "clean frag", "", "introspective"):
        assert not slots.INTRO_HINTS.search(note), note


@needs_caches
def test_a_renamed_review_table_fails_loudly_rather_than_returning_nothing():
    """A first draft guessed the table name, found nothing, and returned an
    empty list that was indistinguishable from "the user has annotated
    nothing yet". That silence would have made the prologue permanently deaf
    to human review."""
    db = facts.DB_ROOT / "editorial.db"
    if not db.exists():
        pytest.skip("editorial store absent")
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as c:
        tables = {r[0] for r in c.execute(
            "select name from sqlite_master where type='table'")}
    assert slots.VERDICT_TABLE in tables, (
        f"{slots.VERDICT_TABLE} is gone; slots.py must be updated, and the "
        "guard in intro_candidates() should have raised")


@needs_caches
def test_only_human_provenance_counts_as_a_decision():
    """TEST-provenance rows exist in the editorial store today. If they were
    treated as the user's judgement, an automated run could quietly cast the
    film."""
    assert "TEST" not in slots.HUMAN_PROVENANCE
    assert "SYSTEM" not in slots.HUMAN_PROVENANCE
    assert "AI_SUGGESTION" not in slots.HUMAN_PROVENANCE
    from creative_suite.engine import review_corpus as rc
    assert set(slots.HUMAN_PROVENANCE) == set(rc.HUMAN_PROVENANCE)


# ── the speed graphic agrees with the engine ────────────────────────────────

def test_speed_bands_are_the_engine_thresholds():
    """cg_draw.c:844-857. Our readout must colour a speed the way Quake
    would, or the graphic is inventing a scale."""
    assert [t for t, _ in p.SPEED_BANDS] == [320, 420, 520, 620, 720, 820]
    assert p.BASE_RUN_UPS == 320             # g_main.c:152


def test_band_selection_is_monotonic():
    seen, last = [], None
    for ups in range(0, 1000, 10):
        c = p.band_for(ups)
        if c != last:
            seen.append(c)
            last = c
    assert seen == [c for _, c in p.SPEED_BANDS]


# ── primitives render, and say what they are told to say ────────────────────

@pytest.mark.parametrize("svg", [
    p.alive_counter(4, 3),
    p.speed_readout(672.1),
    p.archive_counter(33316, "confirmed user frags"),
    p.role_tiles("T1"),
    p.round_grid(78730, cols=12, rows=6),
    p.weapon_row([("lightning", 77688), ("gauntlet", 904)]),
    p.map_constellation([p.MapWeight("campgrounds", 1089),
                         p.MapWeight("hearth", 9)]),
])
def test_primitive_is_well_formed_svg(svg: str):
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    import xml.etree.ElementTree as ET
    ET.fromstring(svg)                        # raises on malformed output


def test_alive_counter_greys_the_dead_and_keeps_them_grey():
    """Four pips a side; a dead one is DEAD-coloured and never comes back."""
    assert p.alive_counter(4, 4).count(p.DEAD) == 0
    assert p.alive_counter(1, 0).count(f'fill="{p.DEAD}"') == 7


def test_round_grid_states_its_own_sample_size():
    """The frame holds fewer cells than the archive has rounds; the caption
    must say so rather than implying the grid is complete."""
    svg = p.round_grid(78730, cols=48, rows=18)
    assert "864 OF 78,730 ROUNDS" in svg


def test_archive_counter_carries_the_denominator_in_its_caption():
    svg = p.archive_counter(203536, "player kills")
    assert "203,536" in svg and "PLAYER KILLS" in svg


def test_primitives_escape_text():
    svg = p.archive_counter("x", '<script>&"')
    assert "<script>" not in svg and "&lt;" in svg


# ── the treatments may not contain unverified copy ──────────────────────────

# Each banned figure, and the correct one that must accompany any mention of
# it. A treatment is allowed to name a wrong number -- it has to, to forbid it
# -- but never on its own. The rule is: wherever the wrong figure appears, the
# right one appears beside it, or the line explicitly forbids it. That is
# stricter than looking for scolding words and it cannot be satisfied by
# accident.
BANNED_ON_SCREEN = (
    ("452 hours", "450", "unsourced; duration_ms is NULL for all 4,292 demos"),
    ("138,301", "78,730", "counter-inflated by 26 demos"),
    ("cg_drawSpeedometer", "cg_drawSpeed", "q3mme cvar, not WolfcamQL's"),
)
FORBIDS = re.compile(
    r"never|not permitted|banned|do not|unsourced|inflated|wrong|nonexistent|"
    r"broken|no-op|does not have|retired", re.I)


@pytest.mark.parametrize("phrase,correction,why", BANNED_ON_SCREEN)
def test_a_wrong_figure_never_appears_without_its_correction(
        phrase: str, correction: str, why: str):
    if not DOCS.exists():
        pytest.skip("treatments not present")
    offences = []
    for doc in sorted(DOCS.glob("*.md")):
        for i, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            if phrase.lower() not in line.lower():
                continue
            if correction.lower() in line.lower() or FORBIDS.search(line):
                continue
            offences.append(f"{doc.name}:{i}: {line.strip()}")
    assert not offences, (
        f"{phrase!r} appears without {correction!r} beside it and without "
        f"being forbidden ({why}):\n" + "\n".join(offences))
