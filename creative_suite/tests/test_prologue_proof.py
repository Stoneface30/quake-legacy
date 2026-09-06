"""Tests for PROLOGUE_PROOF_01 -- the first moving proof.

The unit tests here guard the two things that would make the proof dishonest
or unsafe, and neither needs the render to exist:

  1. a player's name reaching the screen,
  2. a number on screen that is not the number in the ledger.

The integration tests check the finished file when there is one, and skip
cleanly when there is not, so this suite is useful on a machine that has
never built the proof.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from creative_suite.prologue import facts, motion, name_guard

REPO = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("QL_PROOF_OUT", REPO / "output/prologue"))
MASTER = OUT / "PROLOGUE_PROOF_01.mp4"
REVIEW = OUT / "PROLOGUE_PROOF_01_review.mp4"
MANIFEST = OUT / "PROLOGUE_PROOF_01_manifest.json"
FFMPEG = Path(os.environ.get(
    "QL_FFMPEG", REPO / "creative_suite/tools/ffmpeg/ffmpeg.exe"))

needs_render = pytest.mark.skipif(
    not MANIFEST.exists(), reason="proof not built in this checkout")


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


# ── the name guard ──────────────────────────────────────────────────────────

def _frame(fill: int = 20) -> np.ndarray:
    return np.full((1080, 1920, 3), fill, dtype=np.uint8)


def test_guard_sees_text_shaped_marks_in_the_band():
    """White glyph-sized marks on a dark scene are what an obituary is."""
    f = _frame(30)
    y = (name_guard.BAND_TOP + name_guard.BAND_BOTTOM) // 2
    for n in range(40):                       # 40 thin white strokes
        x = 700 + n * 12
        f[y - 9:y + 9, x:x + 3] = 255
    assert name_guard.glyph_pixels(f) >= name_guard.MIN_GLYPH_PIXELS
    assert name_guard.has_burned_text(f)


def test_guard_ignores_a_smooth_blown_out_wall():
    """Game geometry can be just as bright as a glyph -- but it is smooth.

    A sunlit wall ramps into shadow over tens of pixels; a glyph goes from
    white to scene in one or two. Without that distinction the guard would
    reject every bright frame on campgrounds and there would be no footage
    left to cut with.
    """
    f = _frame(30)
    band = slice(name_guard.BAND_TOP, name_guard.BAND_BOTTOM)
    # up and back down, so there is no hard edge anywhere -- a lit wall, not
    # a lit wall against a doorway
    up = np.linspace(30, 252, 550)
    ramp = np.concatenate([up, up[::-1]]).astype(np.uint8)
    f[band, 400:1500] = ramp[None, :, None]
    assert not name_guard.has_burned_text(f)


def test_guard_ignores_an_explosion_core():
    """The only thing that ever fooled it: white-hot, hard-edged -- but warm.

    An orange-tinted core is exactly as bright and exactly as sharp as a
    glyph, which is why neutrality is part of the test and not an
    afterthought.
    """
    f = _frame(25)
    y = (name_guard.BAND_TOP + name_guard.BAND_BOTTOM) // 2
    for n in range(60):
        x = 800 + n * 6
        f[y - 20:y + 20, x:x + 4] = (255, 236, 205)    # warm, not neutral
    assert not name_guard.has_burned_text(f)


def test_guard_ignores_a_brief_spike_but_not_a_held_line():
    """A centerprint holds for seconds. Five frames is never text."""
    assert name_guard.MIN_TEXT_FRAMES >= 12
    assert name_guard.PICK_MAX_GLYPH < name_guard.MIN_GLYPH_PIXELS


def test_the_band_covers_where_quake_actually_draws_it():
    """Measured at y 210-265 in the V2 proxies; the band must contain it with
    room on both sides for a different font size."""
    assert name_guard.BAND_TOP <= 205
    assert name_guard.BAND_BOTTOM >= 275


# ── on-screen numbers ───────────────────────────────────────────────────────

def test_speed_bands_match_the_engine():
    assert [t for t, _ in motion.SPEED_BANDS] == [320, 420, 520, 620, 720, 820]
    assert motion.BASE_RUN_UPS == 320


def test_the_counter_lands_exactly_on_its_value_and_holds():
    """Two separate bugs lived here.

    It truncated instead of rounding, so a counter spent its last frames one
    short -- 4,291 for 4,292. And its progress only reached 1.0 on the final
    frame, so the shot cut while the number was still moving and the audience
    never saw the figure it was counting to. Both are checked: the value is
    exact at full progress, and full progress arrives with time to spare.
    """
    for value in (4292, 78730, 203536):
        assert round(value * motion.ease_out(1.0)) == value

    # the shot-local mapping used by the demo counter: reaches 1.0 at t=0.87
    def progress(t: float) -> float:
        return motion.clamp01((t - 0.55) / 0.32)

    assert progress(0.90) >= 1.0, "counter must finish before the cut"
    assert progress(0.70) < 1.0, "and it must still be counting before that"
    # the figure then holds for the last tenth of the shot, which at 2.6 s is
    # about a quarter of a second -- long enough to read a five-digit number
    assert (1.0 - 0.90) * 2.6 > 0.2


@needs_render
def test_manifest_copy_is_the_ledger_copy():
    """Anything the film says about the archive must be a permitted wording."""
    permitted = set(facts.screen_copy().values())
    for row in _manifest()["facts_used"]:
        assert row["on_screen"] in permitted, row


@needs_render
def test_hours_are_never_stated_precisely_on_screen():
    """453.1 is a LOWER bound -- warmup and the tail after the last kill sit
    outside it -- so an exact figure would be the one untrue thing on screen."""
    texts = " ".join(s["text"] for s in _manifest()["shots"])
    assert "OVER 450 HOURS" in texts
    for forbidden in ("453", "452", "453.1"):
        assert forbidden not in texts


@needs_render
def test_the_retired_round_total_never_appears():
    texts = " ".join(s["text"] for s in _manifest()["shots"])
    assert "138,301" not in texts
    assert "78,730 ROUNDS" in texts


# ── provenance and slots ────────────────────────────────────────────────────

@needs_render
def test_every_gameplay_shot_is_temporary_and_carries_a_slot():
    """Human review has not ruled on any of this footage. Nothing may be
    assigned, and every placeholder must name the slot it is holding."""
    for s in _manifest()["shots"]:
        if s["source"] == "V2_REVIEW_PROXY":
            assert s["temporary"] is True, s
            assert s["slot"], s
            assert s["provenance"] == "HISTORICAL_UNREVIEWED_TEMP", s


@needs_render
def test_no_v1_material_anywhere():
    for s in _manifest()["shots"]:
        assert s["source"] in ("SYNTHETIC_GRAPHIC", "V2_REVIEW_PROXY"), s


@needs_render
def test_synthetic_shots_never_claim_historical_provenance():
    for s in _manifest()["shots"]:
        if s["source"] == "SYNTHETIC_GRAPHIC":
            assert s["provenance"] == "SYNTHETIC_EXPLAINER", s


@needs_render
def test_the_speed_graphic_cites_a_real_measured_moment():
    src = _manifest()["speed_source"]
    assert src["moment_id"] == 43000
    assert src["peak_speed"] > src["entry_speed"]
    assert "ENDS_IN_FRAG" in (src["traits"] or "")


# ── the finished file ───────────────────────────────────────────────────────

@needs_render
def test_master_is_the_requested_format():
    mf = _manifest()
    assert mf["resolution"] == "1920x1080"
    assert mf["fps"] == 60
    assert 30.0 <= mf["duration_s"] <= 45.0, mf["duration_s"]


@needs_render
def test_a_review_copy_exists_beside_the_master():
    assert MASTER.exists() and REVIEW.exists()
    assert REVIEW.stat().st_size < MASTER.stat().st_size


@needs_render
@pytest.mark.skipif(not FFMPEG.exists(), reason="ffmpeg absent")
def test_no_player_name_survives_anywhere_in_the_master():
    """The whole point. Every frame, not a sample.

    The first build of this proof put four real opponent handles on screen;
    this is the check that stops that shipping again.
    """
    result = name_guard.audit_video(MASTER, FFMPEG)
    assert result["clean"], (
        f"burned-in text found: {result['text_runs']} "
        f"(frame, length, peak); worst pixel score {result['worst']}")
