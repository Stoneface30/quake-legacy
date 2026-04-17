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
