"""
WOLF WHISPERER / WolfcamQL inventory scanner.

Scans the WolfcamQL install directory and produces a structured inventory
of what's available: demos, configs, scripts, and the wolfcamql binary.

Default root searched:
  G:/QUAKE_LEGACY/WOLF WHISPERER/WolfcamQL
  G:/QUAKE_LEGACY/WOLF WHISPERER/WolfcamQL/wolfcam-ql  (inner layout)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class WolfcamInventory:
    wolfcam_root: Path
    binary_path: Optional[Path]
    demo_paths: list[Path] = field(default_factory=list)
    cfg_paths: list[Path] = field(default_factory=list)
    script_paths: list[Path] = field(default_factory=list)

    @property
    def demo_count(self) -> int:
        return len(self.demo_paths)

    @property
    def is_usable(self) -> bool:
        return self.binary_path is not None and self.binary_path.exists()

    def to_dict(self) -> dict:
        return {
            "wolfcam_root": str(self.wolfcam_root),
            "binary_path": str(self.binary_path) if self.binary_path else None,
            "binary_exists": self.is_usable,
            "demo_count": self.demo_count,
            "cfg_count": len(self.cfg_paths),
            "script_count": len(self.script_paths),
        }


# Candidate roots in priority order: the inner wolfcam-ql dir is preferred
# when it exists because that's where the exe lives in a full WolfcamQL build.
_DEFAULT_CANDIDATES: list[Path] = [
    Path("G:/QUAKE_LEGACY/WOLF WHISPERER/WolfcamQL/wolfcam-ql"),
    Path("G:/QUAKE_LEGACY/WOLF WHISPERER/WolfcamQL"),
]

_EXE_NAMES = ("wolfcamql.exe", "WolfcamQL.exe")


def _find_binary(root: Path) -> Optional[Path]:
    """Search *root* and its direct wolfcam-ql subdirectory for the exe."""
    search_dirs = [root]
    inner = root / "wolfcam-ql"
    if inner.is_dir():
        search_dirs.append(inner)

    for d in search_dirs:
        for name in _EXE_NAMES:
            candidate = d / name
            if candidate.exists():
                return candidate
    return None


def scan_wolfcam(wolfcam_root: Optional[Path] = None) -> WolfcamInventory:
    """Scan the WolfcamQL directory and return a WolfcamInventory.

    Parameters
    ----------
    wolfcam_root:
        Explicit root to scan.  When *None* the function walks
        ``_DEFAULT_CANDIDATES`` and uses the first one that exists on disk
        (falling back to the first candidate if none exist).
    """
    if wolfcam_root is None:
        wolfcam_root = next(
            (p for p in _DEFAULT_CANDIDATES if p.exists()),
            _DEFAULT_CANDIDATES[0],
        )

    binary = _find_binary(wolfcam_root)

    demos: list[Path] = []
    cfgs: list[Path] = []
    scripts: list[Path] = []

    if wolfcam_root.exists():
        demos = sorted(wolfcam_root.rglob("*.dm_73"))
        cfgs = sorted(wolfcam_root.rglob("*.cfg"))
        scripts = (
            sorted(wolfcam_root.rglob("*.sh"))
            + sorted(wolfcam_root.rglob("*.bat"))
            + sorted(wolfcam_root.rglob("*.py"))
        )

    return WolfcamInventory(
        wolfcam_root=wolfcam_root,
        binary_path=binary,
        demo_paths=demos,
        cfg_paths=cfgs,
        script_paths=scripts,
    )
