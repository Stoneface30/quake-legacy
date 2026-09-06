"""Where PANTHEON's derived performance data lives.

One root, configurable, never a drive letter inside engine code:

    PANTHEON_PERFORMANCE_STORE=<dir>      (default: creative_suite/database)

The first performance index filled a drive because every action row carried
its whole trace. The compact index, the trace cache and the template library
all live under this root so a machine with a full project drive can point
them somewhere else without touching a module. The source databases the
engine READS (the demo corpus catalogue, the semantic event store) stay where
the parser put them; only what PANTHEON derives moves.
"""
from __future__ import annotations

import os
from pathlib import Path

ENV_ROOT = "QUAKE_LEGACY_ROOT"
ENV_STORE = "PANTHEON_PERFORMANCE_STORE"


def _project_root() -> Path:
    """The checkout that owns the databases.

    A git worktree under `.claude/worktrees/<name>/` shares the project's
    corpus catalogue and event store with the main checkout (they are
    gitignored, so they exist once); the root is therefore the directory
    above `.claude`, not the worktree. QUAKE_LEGACY_ROOT overrides.
    """
    raw = os.getenv(ENV_ROOT, "").strip()
    if raw:
        return Path(raw)
    here = Path(__file__).resolve().parents[2]
    parts = here.parts
    if ".claude" in parts and "worktrees" in parts:
        return Path(*parts[:parts.index(".claude")])
    return here


REPO_ROOT = Path(__file__).resolve().parents[2]      # the code being run
PROJECT_ROOT = _project_root()                       # the data it reads
DEFAULT_STORE = PROJECT_ROOT / "creative_suite" / "database"

# Read-only sources, produced by the parser and the mining passes.
FRAGS_DB = PROJECT_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"
RECOG_DB = PROJECT_ROOT / "creative_suite" / "database" / "frag_recognition.db"


def store_root() -> Path:
    raw = os.getenv(ENV_STORE, "").strip()
    root = Path(raw) if raw else DEFAULT_STORE
    root.mkdir(parents=True, exist_ok=True)
    return root


def index_db() -> Path:
    return store_root() / "performance_index_v2.db"


def trace_cache_db() -> Path:
    return store_root() / "performance_traces.db"


def template_db() -> Path:
    return store_root() / "performance_templates.db"


def map_spatial_dir() -> Path:
    d = store_root() / "map_spatial"
    d.mkdir(parents=True, exist_ok=True)
    return d


def legacy_index_db() -> Path:
    """The 94 GB first-generation index. Evidence, not a source."""
    return PROJECT_ROOT / "creative_suite" / "database" / "performance_index.db"
