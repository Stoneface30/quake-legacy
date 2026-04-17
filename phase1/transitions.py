"""
Minimal transitions module — Rule P1-H: HARD CUTS ONLY.

This file was expected by pipeline.py but was removed during a cleanup pass.
Recreating with the minimum surface that pipeline.py needs. Per Rule P1-H,
all cuts are HARD_CUT in Phase 1 — the other kinds are retained only so
that legacy call sites still construct valid objects.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class TransitionKind(Enum):
    HARD_CUT    = "hard_cut"
    FLASH_CUT   = "flash_cut"
    XFADE       = "xfade"
    SECTION     = "section"
    FADE_BLACK  = "fade_black"
    WHITE_FLASH = "white_flash"


@dataclass
class Transition:
    """A single inter-clip transition. Rule P1-H: kind is always HARD_CUT in Phase 1."""
    kind: TransitionKind = TransitionKind.HARD_CUT
    duration: float = 0.0     # seconds; ignored for HARD_CUT
    offset: float = 0.0       # seconds; where within the outgoing clip the transition centers
