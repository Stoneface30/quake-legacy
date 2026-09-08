"""Some questions are a person's to answer; the engine's job is to make
answering them cheap -- and never to answer them itself."""
from __future__ import annotations

from pathlib import Path

import pytest

from engine.pantheon import review_sheet as R


@pytest.fixture
def frames(tmp_path):
    """Two real images that differ, made without the engine."""
    import subprocess
    out = []
    for i, colour in enumerate(("red", "blue")):
        f = tmp_path / f"{colour}.png"
        subprocess.run([str(R.FFMPEG), "-v", "error", "-y", "-f", "lavfi",
                        "-i", f"color=c={colour}:s=1920x1080", "-frames:v", "1",
                        str(f)], check=True, timeout=180)
        out.append(f)
    return out


def test_a_comparison_needs_two_sides():
    with pytest.raises(ValueError, match="at least two legs"):
        R.Sheet("x", "q", "v", (R.Leg(Path("a.png"), "only"),))


def test_a_missing_leg_is_refused_rather_than_quietly_dropped(tmp_path):
    """A sheet with one side is not a comparison, and showing it invites a
    verdict on nothing."""
    res = R.compare("x", "q", "v",
                    {"a": tmp_path / "gone.png", "b": tmp_path / "also.png"},
                    dest=tmp_path / "out.png")
    assert res["ok"] is False
    assert set(res["missing"]) == {"a", "b"}


def test_it_builds_a_labelled_sheet(frames, tmp_path):
    dest = tmp_path / "sheet.png"
    res = R.compare("t", "Which is red?", "colour",
                    {"leg one": frames[0], "leg two": frames[1]},
                    crop="HUD_BOTTOM_LEFT", dest=dest)
    assert res["ok"], res
    assert dest.exists() and dest.stat().st_size > 1000
    assert res["legs"] == ["leg one", "leg two"]


def test_it_never_reports_a_verdict_of_its_own(frames, tmp_path):
    res = R.compare("t", "q", "v", {"a": frames[0], "b": frames[1]},
                    dest=tmp_path / "s.png")
    assert res["verdict"] == "PENDING_HUMAN"
    assert "look at it" in res["how_to_answer"]


def test_an_unknown_crop_is_refused(frames, tmp_path):
    with pytest.raises(KeyError, match="no such crop"):
        R.compare("t", "q", "v", {"a": frames[0], "b": frames[1]},
                  crop="NOWHERE", dest=tmp_path / "s.png")


def test_wide_crops_stack_vertically_so_neither_leg_becomes_a_stripe():
    wide = R.Sheet("a", "q", "v", (R.Leg(Path("x"), "1"), R.Leg(Path("y"), "2")),
                   crop=R.CROPS["HUD_TOP"])
    tall = R.Sheet("b", "q", "v", (R.Leg(Path("x"), "1"), R.Leg(Path("y"), "2")),
                   crop=R.CROPS["CENTRE"])
    assert wide.direction == "v"
    assert tall.direction == "h"


def test_labels_survive_characters_ffmpeg_would_eat(frames, tmp_path):
    """A cvar label is full of colons and a path is full of backslashes."""
    res = R.compare("t", "q", "v",
                    {"cg_draw:Status 1": frames[0], "50% alpha's off": frames[1]},
                    dest=tmp_path / "s.png")
    assert res["ok"], res


def test_the_named_crops_are_inside_a_1080p_frame():
    for name, (w, h, x, y) in R.CROPS.items():
        assert x + w <= 1920 and y + h <= 1080, name
