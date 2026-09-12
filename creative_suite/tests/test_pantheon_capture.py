from pathlib import Path

from engine.pantheon import store as S


def test_host_exe_is_resolved_through_the_store_not_a_drive_letter():
    from engine.pantheon import pantheon_capture as PC
    assert PC.host_exe() == S.CODE_ROOT / "engine" / "pantheon_renderer" / "build" / "pantheon_cgame.exe"


def test_model_assets_uses_the_one_binary_that_exists():
    from engine.pantheon import model_assets, pantheon_capture as PC
    assert model_assets.HOST_EXE == PC.host_exe()
