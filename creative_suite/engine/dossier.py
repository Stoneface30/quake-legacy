"""Review-facing shape of ActionTruth.

A thin adapter, deliberately. The semantics live in `action_truth`, which the
effect planner and choreographer will read from too; if this module started
computing anything of its own, the reviewer and production would eventually
disagree about the same moment and nobody could say which was right.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from creative_suite.engine.action_truth import (  # noqa: F401
    CRITICAL_HP, LOW_HP, LOW_STACK, RECOGNITION_DB, UNKNOWN, _stack,
)
from creative_suite.engine import action_truth


def build(item_id: str, db: Path = RECOGNITION_DB) -> dict[str, Any] | None:
    """The dossier for one review item: ActionTruth, unmodified."""
    return action_truth.for_item(item_id, db=db)
