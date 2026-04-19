from pathlib import Path

import pytest

from creative_suite.config import Config


def test_config_has_required_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path))
    cfg = Config()
    assert cfg.storage_root == tmp_path
    assert cfg.db_path == tmp_path / "creative_suite.db"
    assert cfg.annotations_dir == tmp_path / "annotations"
    assert cfg.variants_dir == tmp_path / "variants"
    assert cfg.packs_dir == tmp_path / "packs"
    assert cfg.pre_content_offset_s == 15.0
    assert cfg.port == 8765
    assert cfg.md3viewer_port == 8766
    assert cfg.comfyui_url == "http://127.0.0.1:8188"
    assert cfg.ollama_url == "http://127.0.0.1:11434"
    assert cfg.phase1_output_dir.name == "output"
    assert cfg.phase1_clip_lists.name == "clip_lists"
    assert cfg.full_catalog_json.name == "FULL_CATALOG.json"


def test_phase1_output_dir_honors_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    custom = tmp_path / "custom_output"
    custom.mkdir()
    monkeypatch.setenv("CS_PHASE1_OUTPUT_DIR", str(custom))
    from creative_suite.config import Config
    cfg = Config()
    assert cfg.phase1_output_dir == custom
