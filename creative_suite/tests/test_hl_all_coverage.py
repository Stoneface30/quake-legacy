"""Episode continuation must count T1 AND T2.

The original rule counted only T1, so a Part stopped generating episodes the
moment its T1 ran out -- silently stranding every remaining T2 clip. Across the
corpus that was 568 of 1076 selectable clips, over half, lost with no error.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

hl_all = importlib.import_module("hl_all")


class _F:
    def __init__(self, tier, fp):
        self.tier = tier
        self.fp = fp


def _frags(n_t1, n_t2):
    return ([_F("T1", f"t1_{i}.avi") for i in range(n_t1)]
            + [_F("T2", f"t2_{i}.avi") for i in range(n_t2)])


def test_counts_both_tiers(monkeypatch):
    monkeypatch.setattr(hl_all, "collect_frags", lambda p, c: _frags(3, 7))
    monkeypatch.setattr(hl_all.L, "remaining", lambda p, f, root=None: f)
    assert hl_all.clips_left(1, None) == (3, 7)
    assert hl_all.t1_left(1, None) == 10


def test_part_with_no_t1_but_spare_t2_still_qualifies(monkeypatch):
    """The exact regression: T1 exhausted, T2 left. Must NOT be zero."""
    monkeypatch.setattr(hl_all, "collect_frags", lambda p, c: _frags(0, 41))
    monkeypatch.setattr(hl_all.L, "remaining", lambda p, f, root=None: f)

    assert hl_all.clips_left(1, None) == (0, 41)
    assert hl_all.t1_left(1, None) == 41
    assert hl_all.t1_left(1, None) >= hl_all.MIN_CLIPS_FOR_EXTRA


def test_fully_spent_part_stops(monkeypatch):
    monkeypatch.setattr(hl_all, "collect_frags", lambda p, c: _frags(0, 0))
    monkeypatch.setattr(hl_all.L, "remaining", lambda p, f, root=None: f)
    assert hl_all.t1_left(1, None) == 0
    assert hl_all.t1_left(1, None) < hl_all.MIN_CLIPS_FOR_EXTRA


def test_single_leftover_clip_still_ships(monkeypatch):
    """One clip left is still a clip that must ship."""
    monkeypatch.setattr(hl_all, "collect_frags", lambda p, c: _frags(0, 1))
    monkeypatch.setattr(hl_all.L, "remaining", lambda p, f, root=None: f)
    assert hl_all.t1_left(1, None) >= hl_all.MIN_CLIPS_FOR_EXTRA
