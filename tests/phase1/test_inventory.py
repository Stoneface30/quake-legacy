import pytest
from phase1.inventory import scan_part, ClipInfo, scan_all_parts

def test_scan_part_returns_clip_list(cfg):
    clips = scan_part(4, cfg)
    assert isinstance(clips, list)
    assert len(clips) > 0

def test_scan_part_clip_has_required_fields(cfg):
    clips = scan_part(4, cfg)
    clip = clips[0]
    assert isinstance(clip, ClipInfo)
    assert clip.path.exists()
    assert clip.path.suffix.lower() == ".avi"
    assert clip.size_mb > 0
    assert clip.part == 4

def test_scan_part_sorted_alphabetically(cfg):
    clips = scan_part(4, cfg)
    names = [c.path.name for c in clips]
    assert names == sorted(names)

def test_scan_all_parts_returns_dict(cfg):
    result = scan_all_parts(cfg)
    assert isinstance(result, dict)
    for part in range(4, 13):
        assert part in result
        assert isinstance(result[part], list)

def test_inventory_report_prints(cfg, capsys):
    from phase1.inventory import print_inventory_report
    print_inventory_report(cfg)
    captured = capsys.readouterr()
    assert "Part4" in captured.out
    assert "AVI" in captured.out
