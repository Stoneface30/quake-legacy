# creative_suite/tests/test_otio_bridge.py
"""Tests for creative_suite.otio_bridge (P3-T4)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("opentimelineio", reason="opentimelineio not installed")

from creative_suite.otio_bridge import build_otio_timeline, write_otio_for_part


# ── helpers ──────────────────────────────────────────────────────────────────

def _clips(n: int) -> list[dict]:
    return [
        {
            "path": f"G:/QUAKE VIDEO/T{(i % 3) + 1}/Part4/frag{i:03d}.avi",
            "duration": 3.0 + i,
            "is_fl": i % 2 == 1,
        }
        for i in range(n)
    ]


# ── tests ────────────────────────────────────────────────────────────────────

def test_build_returns_dict() -> None:
    result = build_otio_timeline(4, [])
    assert isinstance(result, dict)


def test_schema_keys() -> None:
    result = build_otio_timeline(4, [])
    assert result["OTIO_SCHEMA"] == "Timeline.1"
    assert result["tracks"]["OTIO_SCHEMA"] == "Stack.1"


def test_clip_count() -> None:
    result = build_otio_timeline(4, _clips(3))
    # find the video track children
    tracks_children = result["tracks"]["children"]
    # first (and only) child is the V1 video track
    v1_track = tracks_children[0]
    assert v1_track["OTIO_SCHEMA"] == "Track.1"
    assert len(v1_track["children"]) == 3


def test_clip_metadata() -> None:
    clips = _clips(2)
    clips[0]["tier"] = "T1"
    clips[0]["is_fl"] = False
    result = build_otio_timeline(4, clips)
    v1_track = result["tracks"]["children"][0]
    first_clip = v1_track["children"][0]
    meta = first_clip["metadata"]["pantheon"]
    assert "tier" in meta
    assert "is_fl" in meta
    assert meta["tier"] == "T1"
    assert meta["is_fl"] is False


def test_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "part04.otio"
    result = build_otio_timeline(4, _clips(2), output_path=out)
    assert out.exists()
    assert out.stat().st_size > 0
    # must be valid JSON
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    assert loaded["OTIO_SCHEMA"] == "Timeline.1"
    # returned dict must equal what was written
    assert result == loaded


def test_part_name() -> None:
    result = build_otio_timeline(4, [])
    assert result["name"] == "Part 04"


def test_write_otio_for_part_returns_none_when_no_flow_plan(tmp_path: Path) -> None:
    """write_otio_for_part returns None when flow_plan is absent."""
    result = write_otio_for_part(4, tmp_path)
    assert result is None


def test_write_otio_for_part_creates_file(tmp_path: Path) -> None:
    """write_otio_for_part reads flow_plan, writes .otio, returns Path."""
    flow_plan = {
        "clips": [
            {"chunk": "G:/QUAKE VIDEO/T1/Part4/frag000.avi", "duration": 4.0, "tier": "T1"},
            {"chunk": "G:/QUAKE VIDEO/T2/Part4/frag001.avi", "duration": 3.5, "tier": "T2"},
        ],
        "body_seam_offsets": [0.0, 4.0],
    }
    flow_plan_path = tmp_path / "part04_flow_plan.json"
    flow_plan_path.write_text(json.dumps(flow_plan), encoding="utf-8")

    result = write_otio_for_part(4, tmp_path)
    assert result is not None
    assert result.name == "part04.otio"
    assert result.exists()
    data = json.loads(result.read_text(encoding="utf-8"))
    assert data["OTIO_SCHEMA"] == "Timeline.1"
    v1_track = data["tracks"]["children"][0]
    assert len(v1_track["children"]) == 2


def test_seam_offsets_in_clip_metadata(tmp_path: Path) -> None:
    """timeline_offset_s in clip metadata reflects body_seam_offsets."""
    flow_plan = {
        "clips": [
            {"chunk": "a.avi", "duration": 5.0},
            {"chunk": "b.avi", "duration": 4.0},
        ],
        "body_seam_offsets": [0.0, 5.0],
    }
    fp = tmp_path / "part04_flow_plan.json"
    fp.write_text(json.dumps(flow_plan), encoding="utf-8")
    write_otio_for_part(4, tmp_path)
    otio_path = tmp_path / "part04.otio"
    data = json.loads(otio_path.read_text(encoding="utf-8"))
    children = data["tracks"]["children"][0]["children"]
    assert children[0]["metadata"]["pantheon"]["timeline_offset_s"] == 0.0
    assert children[1]["metadata"]["pantheon"]["timeline_offset_s"] == 5.0


def test_slow_clip_emits_linear_timewarp() -> None:
    """A clip with slow=True gets a LinearTimeWarp effect."""
    clips = [{"path": "a.avi", "duration": 3.0, "slow": True}]
    result = build_otio_timeline(4, clips)
    v1_track = result["tracks"]["children"][0]
    clip = v1_track["children"][0]
    effects = clip.get("effects", [])
    timewarp_schemas = [e["OTIO_SCHEMA"] for e in effects if "LinearTimeWarp" in e.get("OTIO_SCHEMA", "")]
    assert len(timewarp_schemas) == 1


def test_tier_inferred_from_path() -> None:
    """Tier is correctly inferred from T1/T2/T3 in the path when not supplied."""
    clips = [{"path": "G:/QUAKE VIDEO/T3/Part4/frag.avi", "duration": 2.0}]
    result = build_otio_timeline(4, clips)
    meta = result["tracks"]["children"][0]["children"][0]["metadata"]["pantheon"]
    assert meta["tier"] == "T3"


def test_is_fl_inferred_from_filename() -> None:
    """is_fl is True when 'FL' appears in the clip filename stem."""
    clips = [{"path": "Demo (104FL1).avi", "duration": 2.0}]
    result = build_otio_timeline(4, clips)
    meta = result["tracks"]["children"][0]["children"][0]["metadata"]["pantheon"]
    assert meta["is_fl"] is True
