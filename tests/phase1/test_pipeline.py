import pytest, json
from pathlib import Path
from phase1.pipeline import build_filter_complex, GradePreset, assemble_part

def test_grade_preset_loads():
    # S4 fix: absolute path so test works from any working directory
    preset_path = Path(__file__).parent.parent.parent / "phase1" / "presets" / "grade_tribute.json"
    preset = GradePreset.from_file(preset_path)
    assert preset.contrast == 1.4
    assert preset.bloom_sigma == 18
    assert preset.bloom_opacity == 0.3  # must match spec

def test_build_filter_complex_returns_string(tmp_clip, cfg):
    from phase1.pipeline import build_filter_complex, GradePreset
    preset = GradePreset()
    durations = [1.0]
    fc = build_filter_complex([tmp_clip], durations, preset, cfg)
    assert isinstance(fc, str)
    assert "eq=" in fc          # color grade
    assert "gblur" in fc        # bloom
    assert "blend" in fc        # bloom screen blend
    assert "[vout]" in fc       # output label

def test_assemble_produces_output(tmp_clip, cfg, tmp_path):
    output = tmp_path / "test_output.mp4"
    assemble_part(
        clips=[tmp_clip],
        output_path=output,
        music_path=None,
        cfg=cfg,
        preview_seconds=None
    )
    assert output.exists()
    assert output.stat().st_size > 10_000
