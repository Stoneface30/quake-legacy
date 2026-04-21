from pathlib import Path

from creative_suite.clips.parser import parse_clip_list


def test_parses_concat_demuxer_lines(tmp_path: Path) -> None:
    p = tmp_path / "part04.txt"
    p.write_text(
        "# part04 clip list\n"
        "file 'Demo (490)  - 596.avi'\n"
        "file 'Demo (124) - 18.avi'\n"
        "# comment line\n"
        "\n"
        "file 'Demo (3)  - 201_FL_side.avi'\n"
    )
    entries = parse_clip_list(p)
    assert len(entries) == 3
    assert entries[0].filename == "Demo (490)  - 596.avi"
    assert entries[0].demo_hint == "490"
    assert entries[2].demo_hint == "3"
    assert entries[2].is_fl is True
    assert entries[0].is_fl is False
    assert entries[0].index == 0
    assert entries[2].index == 2


def test_empty_file_returns_empty(tmp_path: Path) -> None:
    p = tmp_path / "empty.txt"
    p.write_text("")
    assert parse_clip_list(p) == []


def test_parses_styleb_multi_angle_grammar(tmp_path: Path) -> None:
    # Real phase1 styleb grammar: "FP.avi > FL1.avi > FL2.avi" (Rule P1-K).
    # Only the FP (first segment) is the playable unit; FL angles ride along.
    p = tmp_path / "part04_styleb.txt"
    p.write_text(
        "# Part 4 styleb\n"
        "Demo (37)  -  446.avi > Demo (37FL1).avi\n"
        "Demo (209) - 183.avi > Demo (209FL1).avi > Demo (209FL2).avi\n"
        "Demo (22)  -  195.avi\n"
        "# end\n"
    )
    entries = parse_clip_list(p)
    assert len(entries) == 3
    assert entries[0].filename == "Demo (37)  -  446.avi"
    assert entries[0].demo_hint == "37"
    assert entries[0].is_fl is False       # FP leads every line
    assert entries[0].angles == (
        "Demo (37)  -  446.avi", "Demo (37FL1).avi",
    )
    assert entries[1].angles == (
        "Demo (209) - 183.avi",
        "Demo (209FL1).avi", "Demo (209FL2).avi",
    )
    assert entries[2].filename == "Demo (22)  -  195.avi"
    assert entries[2].angles == ("Demo (22)  -  195.avi",)


def test_strips_effect_flags(tmp_path: Path) -> None:
    p = tmp_path / "flagged.txt"
    p.write_text(
        "Demo (99) - 5.avi [slow] [intro]\n"
        "file 'Demo (100) - 6.avi' [zoom]\n"
    )
    entries = parse_clip_list(p)
    assert len(entries) == 2
    assert entries[0].filename == "Demo (99) - 5.avi"
    assert "slow" in entries[0].flags and "intro" in entries[0].flags
    assert entries[1].filename == "Demo (100) - 6.avi"
    assert "zoom" in entries[1].flags


def test_detects_fl_from_wolfcam_naming(tmp_path: Path) -> None:
    p = tmp_path / "flname.txt"
    p.write_text(
        "Demo (37FL1).avi\n"
        "Demo (37) - 1.avi\n"
    )
    entries = parse_clip_list(p)
    assert entries[0].is_fl is True
    assert entries[1].is_fl is False
