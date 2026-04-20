import pytest
from pathlib import Path
from creative_suite.engine.clip_list import load_clip_list, generate_default_list, save_clip_list

def test_clip_list_loads_from_file(tmp_path, cfg):
    # Write a test clip list
    test_file = tmp_path / "part04.txt"
    test_file.write_text("# Part 4 clip list\nDemo (100).avi\nDemo (200).avi\n")
    result = load_clip_list(test_file)
    assert len(result) == 2
    assert result[0] == "Demo (100).avi"

def test_clip_list_skips_comments_and_blanks(tmp_path):
    f = tmp_path / "list.txt"
    f.write_text("# comment\n\nDemo (1).avi\n\n# another\nDemo (2).avi\n")
    result = load_clip_list(f)
    assert result == ["Demo (1).avi", "Demo (2).avi"]

def test_generate_default_list_creates_alphabetical(cfg, tmp_path):
    list_path = tmp_path / "part04.txt"
    generate_default_list(4, cfg, output_path=list_path)
    result = load_clip_list(list_path)
    assert len(result) > 0
    assert result == sorted(result)

def test_clip_list_validate_warns_missing(cfg, tmp_path, capsys):
    f = tmp_path / "list.txt"
    f.write_text("NonExistent_Demo.avi\n")
    from creative_suite.engine.clip_list import validate_clip_list
    missing = validate_clip_list(4, load_clip_list(f), cfg)
    assert len(missing) == 1

def test_save_and_reload(tmp_path):
    clips = ["Demo (1).avi", "Demo (2).avi", "Demo (3).avi"]
    path = tmp_path / "test.txt"
    save_clip_list(clips, path, header="# Test")
    loaded = load_clip_list(path)
    assert loaded == clips
