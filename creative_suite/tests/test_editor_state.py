"""Unit tests for editor state schema + disk persistence."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from creative_suite.editor import state as editor_state
from creative_suite.editor.state import (
    EditorClip,
    EditorState,
    apply_jsonpatch,
    from_flow_plan,
    load_state,
    save_state,
    state_from_dict,
    state_to_dict,
)


@pytest.fixture
def sample_flow_plan() -> dict[str, object]:
    return {
        "part": 5,
        "clips": [
            {
                "chunk": "G:\\QUAKE_LEGACY\\output\\_part05_v6_body_chunks\\chunk_0000.mp4",
                "tier": "T1",
                "section_role": "drop",
                "duration": 4.5,
                "top_event": "rocket_impact",
                "event_count": 2,
            },
            {
                "chunk": "chunk_0001.mp4",
                "tier": "T2",
                "section_role": "build",
                "duration": 6.1,
                "top_event": None,
                "event_count": 0,
            },
        ],
    }


def test_from_flow_plan_hydrates_clips(sample_flow_plan: dict[str, object]) -> None:
    state = from_flow_plan(sample_flow_plan, part=5)

    assert state.part == 5
    assert state.version == editor_state.SCHEMA_VERSION
    assert len(state.clips) == 2
    c0 = state.clips[0]
    assert c0.chunk == "chunk_0000.mp4"  # basename-normalized
    assert c0.tier == "T1"
    assert c0.section_role == "drop"
    assert c0.duration == 4.5
    assert c0.in_s == 0.0
    assert c0.out_s == 4.5
    assert c0.removed is False
    assert c0.slow is None


def test_state_to_dict_roundtrip() -> None:
    state = EditorState(
        part=4,
        clips=[EditorClip(chunk="a.mp4", duration=2.0, out_s=2.0, slow=0.5)],
    )
    d = state_to_dict(state)
    assert d["part"] == 4
    assert d["clips"][0]["slow"] == 0.5
    back = state_from_dict(d)
    assert back == state


def test_save_and_load_state_atomic(tmp_path: Path) -> None:
    state = EditorState(
        part=7,
        clips=[
            EditorClip(chunk="c0.mp4", duration=3.0, out_s=3.0),
            EditorClip(chunk="c1.mp4", duration=5.0, out_s=5.0, removed=True),
        ],
    )
    path = save_state(tmp_path, state)
    assert path.exists()
    loaded = load_state(tmp_path, 7)
    assert loaded == state


def test_load_state_falls_back_to_flow_plan(
    tmp_path: Path, sample_flow_plan: dict[str, object]
) -> None:
    fp = tmp_path / "part05_flow_plan.json"
    fp.write_text(json.dumps(sample_flow_plan), encoding="utf-8")
    state = load_state(tmp_path, 5)
    assert len(state.clips) == 2
    assert state.clips[0].chunk == "chunk_0000.mp4"


def test_load_state_blank_when_no_files(tmp_path: Path) -> None:
    state = load_state(tmp_path, 12)
    assert state.part == 12
    assert state.clips == []


def test_apply_jsonpatch_sets_removed() -> None:
    state = EditorState(
        part=4,
        clips=[EditorClip(chunk="x.mp4", duration=1.0, out_s=1.0)],
    )
    patched = apply_jsonpatch(
        state,
        [{"op": "replace", "path": "/clips/0/removed", "value": True}],
    )
    assert patched.clips[0].removed is True
    assert state.clips[0].removed is False  # original untouched


def test_apply_jsonpatch_reorders_clips() -> None:
    state = EditorState(
        part=4,
        clips=[
            EditorClip(chunk="a.mp4"),
            EditorClip(chunk="b.mp4"),
            EditorClip(chunk="c.mp4"),
        ],
    )
    patched = apply_jsonpatch(
        state,
        [
            {"op": "move", "from": "/clips/2", "path": "/clips/0"},
        ],
    )
    assert [c.chunk for c in patched.clips] == ["c.mp4", "a.mp4", "b.mp4"]


def test_save_state_atomic_leaves_no_partial_on_success(tmp_path: Path) -> None:
    state = EditorState(part=4)
    save_state(tmp_path, state)
    partials = list(tmp_path.glob("*.partial"))
    assert partials == []
