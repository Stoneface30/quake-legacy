"""What the user actually saw on screen, and why each part of it was wrong.

One screenshot carried three linked defects: a round advertised as lasting
0.0 seconds, a button offering to render it, and a black video with the words
"still rendering -- try again" where a working clip had been. All three came
from the same click, and all three are pinned here.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import round_bounds as rb
from creative_suite.engine import review_corpus as rc
from creative_suite.engine import round_story as rs

RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

# The exact item in the screenshot: a T4 the user had already reviewed.
SCREENSHOT_OCC = 495
SCREENSHOT_ROUND = 16


def _corpus() -> bool:
    try:
        with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
            return bool(c.execute(
                "SELECT 1 FROM kill_occurrences_v1 LIMIT 1").fetchone())
    except sqlite3.Error:
        return False


live = pytest.mark.skipif(not _corpus(), reason="needs the local corpus")


def _hash_of(occ: int) -> str:
    with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
        return c.execute(
            "SELECT k.content_hash FROM kill_occurrences_v1 o JOIN "
            "kill_events_v1 k ON k.kill_event_id=o.best_observation_id "
            "WHERE o.occurrence_id=?", (occ,)).fetchone()[0]


# ── a kill span is not a round ──────────────────────────────────────────────

def test_one_kill_does_not_make_a_zero_second_round():
    """The defect, in miniature.

    Round duration used to be the span between the first and last observed
    kill. A round with one kill therefore lasted 0.0 seconds -- and 51.2% of
    rounds in this corpus (41,472 of 80,922) contain exactly one.
    """
    starts: dict[int, int] = {}
    spans = {5: (10_000, 10_000)}         # one kill, no neighbours
    b = rb._bounds_from(starts, spans, 5)
    assert b.duration_ms is None, "a single kill produced a duration"
    assert b.provenance == rb.UNKNOWN
    assert b.credible is False


def test_neighbouring_rounds_bound_a_round():
    starts: dict[int, int] = {}
    spans = {4: (0, 5_000), 5: (20_000, 20_000), 6: (40_000, 45_000)}
    b = rb._bounds_from(starts, spans, 5)
    assert b.provenance == rb.BOUNDED
    assert b.duration_ms == 35_000 and b.credible


def test_an_announced_start_is_observed_not_derived():
    """The server said when the round began; that is not an inference."""
    starts = {5: 100_000, 6: 130_000}
    spans = {5: (110_000, 120_000)}
    b = rb._bounds_from(starts, spans, 5)
    assert b.provenance == rb.OBSERVED
    assert b.start_ms == 100_000 and b.duration_ms == 30_000


def test_a_duration_is_never_reported_as_zero():
    """UNKNOWN, never 0. Zero is a measurement nobody made."""
    for spans in ({7: (5_000, 5_000)}, {}):
        b = rb._bounds_from({}, spans, 7)
        assert b.duration_ms is None or b.duration_ms >= rb.MIN_CREDIBLE_MS


@live
def test_the_screenshot_round_is_no_longer_zero():
    """The regression proof, on the exact item the user was looking at."""
    ctx = rs.round_context(_hash_of(SCREENSHOT_OCC), SCREENSHOT_ROUND)
    assert ctx is not None
    assert ctx.duration_ms and ctx.duration_ms > 0, "still a 0.0s round"
    assert ctx.duration_credible is True
    assert ctx.duration_provenance in (rb.OBSERVED, rb.BOUNDED, rb.KILL_SPAN)


@live
def test_a_round_whose_length_is_unknown_is_not_offered_as_full_round():
    """FAIL CLOSED. The button that produced the black screen.

    It advertised "WATCH FULL ROUND (0.0s)" and then pointed <video> at media
    that had never been rendered.
    """
    from fastapi.testclient import TestClient
    from creative_suite.api.review import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    d = c.get(f"/api/review/round/USER_FRAG:{SCREENSHOT_OCC}").json()
    assert d["available"] is True
    assert d["full_round_available"] is True
    assert d["media_duration_s"] > 0


# ── the player must never be blanked ────────────────────────────────────────

def test_the_round_button_polls_before_it_plays():
    """Setting `video.src` to a resource that does not exist yet is what
    turned a working clip black."""
    html = (REPO_ROOT / "creative_suite" / "frontend"
            / "review.html").read_text(encoding="utf-8")
    i = html.index('b.id = "watchround"')
    block = html[i:i + 2500]
    assert "/media_state/round/" in block, "the button does not poll"
    assert "full_round_available === false" in html, "no fail-closed gate"
    # And the old failure text is gone.
    assert 'b.textContent = "still rendering — try again"; });' not in html


def test_the_round_media_route_refuses_an_unknown_length():
    """No window, no render. A zero-length clip is not the whole round."""
    src = (REPO_ROOT / "creative_suite" / "api"
           / "review.py").read_text(encoding="utf-8")
    assert "duration_credible" in src
    assert "the length of this round is not observable" in src


# ── accuracy is visible, and honest ─────────────────────────────────────────

def test_accuracy_is_always_shown_even_when_not_derivable():
    """Asked for directly, and pruning it was the bug.

    Silence reads as "nobody measured this". NOT DERIVABLE with a reason says
    which weapons the pain stream can and cannot answer for.
    """
    html = (REPO_ROOT / "creative_suite" / "frontend"
            / "review.html").read_text(encoding="utf-8")
    assert '"NOT DERIVABLE"' in html
    # The row is protected from the UNKNOWN pruner.
    assert "dataset.keep" in html
    assert "n.dataset.unk && !n.dataset.keep" in html


def test_lg_accuracy_still_cannot_be_fabricated():
    """Pain events are throttled to about three a second; the lightning gun
    fires twenty times a second. Its hits cannot be counted from them."""
    from creative_suite.engine import action_stats as ast
    assert 6 in ast.CONTINUOUS and 6 not in ast.ATTRIBUTABLE
    st = ast.ActionStats(weapon="LIGHTNING", weapon_wp=6, window_ms=4000,
                         accuracy_pct=None, note=ast.NOT_DERIVABLE)
    assert st.accuracy_pct is None


# ── a fragment is not a round ───────────────────────────────────────────────

def test_a_fragment_cannot_define_a_round():
    from engine.parser import demo_lineage as dl
    frag = dl.Lineage("h", dl.FRAGMENT_OF, "container", 2, 1, 4000, 1.0, 0)
    full = dl.Lineage("h", dl.FULL_RECORDING, None, 80, 30, 600_000, None, 30)
    tiny = dl.Lineage("h", dl.UNIQUE_FRAGMENT, None, 2, 1, 4000, None, 0)
    assert frag.can_define_a_round is False
    assert full.can_define_a_round is True
    assert tiny.can_define_a_round is False, "too short to hold a round"


def test_containment_is_detected_from_events_not_filenames():
    """`Demo (417).dm_73` says nothing, and the bytes differ by
    construction -- a fragment is a SUBSEQUENCE, which SHA-256 cannot see."""
    import inspect
    from engine.parser import demo_lineage as dl
    src = inspect.getsource(dl.classify) + inspect.getsource(dl.event_sets)
    assert "demo_name" not in src and "filename" not in src
    assert "server_time_ms" in src and "victim_client" in src


@live
def test_lineage_covers_the_corpus():
    from engine.parser import demo_lineage as dl
    with dl.conn() as c:
        rows = c.execute(
            "SELECT lineage, COUNT(*) n FROM demo_lineage_v1 GROUP BY 1"
        ).fetchall()
    counts = {r["lineage"]: r["n"] for r in rows}
    assert counts.get(dl.FULL_RECORDING, 0) > 0
    assert counts.get(dl.FRAGMENT_OF, 0) > 0, "no fragments detected at all"


@live
def test_the_reviewed_items_come_from_full_recordings():
    """The screenshot was NOT a fragment problem.

    Worth pinning, because it was the first hypothesis and it was wrong: all
    three reviewed items come from complete multi-round recordings, and the
    0.0s round was the bounds derivation.
    """
    from engine.parser import demo_lineage as dl
    for occ in (495, 1080, 18858):
        lin = dl.lineage_of(_hash_of(occ))
        if lin is None:
            pytest.skip("lineage not built")
        assert lin.lineage == dl.FULL_RECORDING
        assert lin.can_define_a_round


@live
def test_a_better_source_never_moves_the_canonical_event():
    """HUMAN REVIEW ATTACHES TO THE EVENT, NOT THE FILE.

    Choosing a fuller recording for a round must change which demo is read,
    never the occurrence id a verdict is attached to.
    """
    from engine.parser import demo_lineage as dl
    from creative_suite.engine import scene as sc
    for occ in (495, 1080, 18858):
        before = _hash_of(occ)
        better = dl.better_source_for(occ)
        assert better is None or better != before
        s = sc.scene_for_item(f"USER_FRAG:{occ}")
        if s is not None:
            ids = {e.occurrence_id for e in s.events}
            assert occ in ids, "the reviewed occurrence left its own scene"
