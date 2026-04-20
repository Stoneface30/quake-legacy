from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# creative_suite/ sub-dirs (moved here from repo root in Plan 1 Task 4)
CS_ROOT = Path(__file__).resolve().parent
TOOLS_ROOT = CS_ROOT / "tools"
DATABASE_ROOT = CS_ROOT / "database"


@dataclass(frozen=True)
class Config:
    port: int = 8765
    md3viewer_port: int = 8766
    comfyui_url: str = "http://127.0.0.1:8188"
    ollama_url: str = "http://127.0.0.1:11434"
    pre_content_offset_s: float = 15.0  # Rule P1-N: PANTHEON 7s + title card 8s

    @property
    def storage_root(self) -> Path:
        return Path(os.environ.get("CS_STORAGE_ROOT", str(CS_ROOT / "storage")))

    @property
    def db_path(self) -> Path:
        return self.storage_root / "creative_suite.db"

    @property
    def annotations_dir(self) -> Path:
        return self.storage_root / "annotations"

    @property
    def variants_dir(self) -> Path:
        return self.storage_root / "variants"

    @property
    def thumbnails_dir(self) -> Path:
        return self.storage_root / "thumbnails"

    @property
    def packs_dir(self) -> Path:
        return self.storage_root / "packs"

    @property
    def wolfcam_capture_dir(self) -> Path:
        return self.storage_root / "wolfcam_capture"

    @property
    def phase1_clip_lists(self) -> Path:
        return REPO_ROOT / "creative_suite" / "engine" / "clip_lists"

    @property
    def phase1_output_dir(self) -> Path:
        override = os.getenv("CS_PHASE1_OUTPUT_DIR")
        if override:
            return Path(override)
        return REPO_ROOT / "output"

    @property
    def full_catalog_json(self) -> Path:
        return TOOLS_ROOT / "game-assets" / "FULL_CATALOG.json"

    @property
    def wolfcam_baseq3(self) -> Path:
        return TOOLS_ROOT / "wolfcamql" / "baseq3"

    def ensure_dirs(self) -> None:
        for p in (
            self.storage_root,
            self.annotations_dir,
            self.variants_dir,
            self.thumbnails_dir,
            self.packs_dir,
            self.wolfcam_capture_dir,
        ):
            p.mkdir(parents=True, exist_ok=True)
