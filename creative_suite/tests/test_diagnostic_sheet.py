"""The diagnostic sheet: generic lanes, readable findings, honest latency."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import diagnostic_sheet as dsheet, event_truth as et


def _sheet(**kw) -> dsheet.DiagnosticSheet:
    base = dict(title="t", scene_start_us=0, scene_end_us=10_000_000,
                hero_us=8_875_000)
    base.update(kw)
    return dsheet.DiagnosticSheet(**base)


# ── the four primitives cover every lane ────────────────────────────────────

def test_each_lane_knows_which_primitive_it_is():
    assert dsheet.Lane("a", dsheet.CAT_GAMEPLAY,
                       instants=(dsheet.Instant(1),)).kind == "instant"
    assert dsheet.Lane("b", dsheet.CAT_FX,
                       intervals=(dsheet.Interval(0, 1),)).kind == "interval"
    assert dsheet.Lane("c", dsheet.CAT_MUSIC, curve=((0, 1.0),)).kind == "curve"
    assert dsheet.Lane("d", dsheet.CAT_GAME_AUDIO,
                       waveform=np.zeros(10), waveform_sr=100).kind == "waveform"


def test_lanes_are_drawn_in_a_fixed_category_order():
    s = _sheet()
    s.add(dsheet.Lane("sync", dsheet.CAT_SYNC))
    s.add(dsheet.Lane("music", dsheet.CAT_MUSIC))
    s.add(dsheet.Lane("game", dsheet.CAT_GAMEPLAY))
    assert [l.name for l in s.ordered()] == ["game", "music", "sync"]


# ── future effect lanes need no new drawing code ────────────────────────────

@pytest.mark.parametrize("category", [
    dsheet.CAT_FX, dsheet.CAT_TRANSITION, dsheet.CAT_MATERIAL,
    dsheet.CAT_MODEL, dsheet.CAT_CAMERA, dsheet.CAT_SEMANTIC])
def test_every_future_lane_is_just_an_interval_lane(category):
    lane = dsheet.effect_lane("x", [dsheet.Interval(
        0, 1_000_000, "thing", purpose="REVEAL_TRAJECTORY")],
        category=category)
    assert lane.kind == "interval"
    assert lane.category == category


def test_an_effect_may_declare_why_it_exists():
    iv = dsheet.Interval(0, 1, "world strip", purpose="SHOW_1VX_THREATS")
    assert iv.purpose in dsheet.PURPOSES


def test_an_effect_that_starts_late_reports_its_latency():
    iv = dsheet.Interval(1_000_000, 2_000_000, "flash",
                         trigger_us=920_000)
    assert iv.latency_ms == 80.0


def test_a_delivered_start_overrides_the_intended_one():
    iv = dsheet.Interval(1_000_000, 2_000_000, "flash", trigger_us=1_000_000,
                         delivered_start_us=1_080_000)
    assert iv.latency_ms == 80.0


def test_an_untriggered_interval_claims_no_latency():
    assert dsheet.Interval(0, 1).latency_ms is None


# ── findings are readable without an image ──────────────────────────────────

def test_a_sync_marker_reports_signed_delta_and_error():
    m = dsheet.SyncMarker("frag", 8_875_000, 8_860_000, -15.0)
    assert m.delta_ms == -15.0
    assert m.error_ms == 0.0
    late = dsheet.SyncMarker("frag", 8_875_000, 8_890_000, -15.0)
    assert late.delta_ms == 15.0
    assert late.error_ms == 30.0


def test_the_sheet_states_its_findings_in_words():
    s = _sheet(sync_markers=(dsheet.SyncMarker("frag", 8_875_000,
                                               8_860_000, -15.0),))
    s.add(dsheet.effect_lane("FX", [dsheet.Interval(
        1_080_000, 2_000_000, "flash", trigger_us=1_000_000)]))
    text = " ".join(s.findings())
    assert "-15.0 ms" in text
    assert "+80.0 ms" in text and "flash" in text


def test_findings_need_no_rendering():
    s = _sheet(sync_markers=(dsheet.SyncMarker("f", 1000, 900, None),))
    assert s.findings()          # no matplotlib involved


# ── gameplay lanes come from events ─────────────────────────────────────────

def test_a_gameplay_lane_is_built_from_authoritative_events():
    events = [et.GameEvent(kind=et.MY_LG_CONTACT, owner=et.OWNER_ME,
                           layer=et.GAME_EVENT_TRUTH, edit_us=us)
              for us in (1_000_000, 2_000_000)]
    lane = dsheet.gameplay_lane(events)
    assert len(lane.instants) == 2
    assert lane.category == dsheet.CAT_GAMEPLAY


def test_a_gameplay_lane_can_select_kinds():
    events = [
        et.GameEvent(kind=et.MY_LG_CONTACT, owner=et.OWNER_ME,
                     layer=et.GAME_EVENT_TRUTH, edit_us=1_000_000),
        et.GameEvent(kind=et.ENEMY_WEAPON_FIRE, owner=et.OWNER_ENEMY,
                     layer=et.GAME_EVENT_TRUTH, edit_us=2_000_000)]
    assert len(dsheet.gameplay_lane(events, kinds=[et.MY_LG_CONTACT]).instants) == 1


def test_a_rate_lane_is_a_step_curve():
    lane = dsheet.rate_lane([{"edit_in_us": 0, "edit_out_us": 1_000_000,
                              "rate": 0.5},
                             {"edit_in_us": 1_000_000,
                              "edit_out_us": 2_000_000, "rate": 1.0}])
    assert lane.kind == "curve"
    assert [v for _, v in lane.curve] == [0.5, 0.5, 1.0, 1.0]


# ── rendering ───────────────────────────────────────────────────────────────

def test_a_sheet_renders_a_file(tmp_path):
    s = _sheet()
    s.add(dsheet.Lane("events", dsheet.CAT_GAMEPLAY,
                      instants=(dsheet.Instant(1_000_000, "a"),
                                dsheet.Instant(2_000_000, "b"))))
    s.add(dsheet.waveform_lane("audio", np.random.default_rng(0).normal(
        0, 0.1, 22050).astype(np.float32), 22050))
    s.add(dsheet.effect_lane("fx", [dsheet.Interval(0, 500_000, "x")]))
    out = s.render(tmp_path / "sheet.png")
    assert out.exists() and out.stat().st_size > 5_000


def test_an_empty_sheet_is_an_error(tmp_path):
    with pytest.raises(ValueError):
        _sheet().render(tmp_path / "s.png")


def test_a_lane_may_zoom_to_the_milliseconds_it_is_about():
    lane = dsheet.Lane("sync", dsheet.CAT_SYNC, zoom_us=300_000,
                       instants=(dsheet.Instant(8_875_000, "truth"),))
    assert lane.zoom_us == 300_000


def test_the_sheet_serialises_its_structure_and_findings():
    s = _sheet(sync_markers=(dsheet.SyncMarker("f", 1000, 900, -0.1),))
    s.add(dsheet.effect_lane("fx", [dsheet.Interval(0, 1, "x",
                                                    purpose="NONE")]))
    d = s.to_dict()
    assert d["sheet_version"] == dsheet.SHEET_VERSION
    assert d["lanes"][0]["intervals"][0]["purpose"] == "NONE"
    assert d["sync"][0]["delta_ms"] == -0.1
    assert d["findings"]
