"""Editor state — the JSON schema the frontend edits.

Hydrated from `output/part{NN}_flow_plan.json` on first read; persisted
to `output/part{NN}_editor_state.json` via atomic `.partial → os.replace`
(Rule L154).

Schema v1 is intentionally minimal and forward-compatible:
  * `version` (int) — schema revision; bumped on breaking changes
  * `part` (int)
  * `clips[]` — one per chunk, in display order:
      - `chunk` (str, basename)  — the body-chunk file
      - `tier`  (str, "T1"|"T2"|"T3"|"?")
      - `section_role` (str|None, music-section hint)
      - `duration` (float, seconds, read-only mirror of source)
      - `in_s`  (float, head trim from the clip's 0)
      - `out_s` (float, tail trim — i.e. clip plays [in_s, out_s])
      - `removed` (bool)  — Tier 1 REMOVE flag, drops from render
      - `slow` (float|None)  — speed multiplier, e.g. 0.5 = half-speed
      - `slow_window_s` (float|None)  — window around recognized peak
      - `notes` (str)
  * `effects[]` — global timeline-level effects (title card, grade)
  * `keyframes[]` — animated parameters (Step 8 lands this)

The frontend PATCHes this doc via RFC 6902 jsonpatch. The render pipeline
reads it back and projects onto `flow_plan.clips[]` + `overrides.txt`.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


@dataclass
class EditorClip:
    chunk: str
    tier: str = "?"
    section_role: str | None = None
    duration: float = 0.0
    in_s: float = 0.0
    out_s: float = 0.0
    removed: bool = False
    slow: float | None = None
    slow_window_s: float | None = None
    notes: str = ""


@dataclass
class EditorState:
    part: int
    version: int = SCHEMA_VERSION
    clips: list[EditorClip] = field(default_factory=list)
    effects: list[dict[str, Any]] = field(default_factory=list)
    keyframes: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


def _basename(p: str | Path) -> str:
    return Path(str(p).replace("\\", "/")).name


def from_flow_plan(flow_plan: dict[str, Any], part: int) -> EditorState:
    """Hydrate an EditorState from a flow_plan.json dict."""
    clips: list[EditorClip] = []
    for c in flow_plan.get("clips", []):
        duration = float(c.get("duration", 0.0))
        clips.append(
            EditorClip(
                chunk=_basename(c.get("chunk", "")),
                tier=str(c.get("tier", "?")),
                section_role=c.get("section_role"),
                duration=duration,
                in_s=0.0,
                out_s=duration,
                removed=False,
                slow=None,
                slow_window_s=None,
                notes="",
            )
        )
    return EditorState(part=part, clips=clips)


def state_to_dict(state: EditorState) -> dict[str, Any]:
    d = asdict(state)
    return d


def state_from_dict(d: dict[str, Any]) -> EditorState:
    clips = [EditorClip(**c) for c in d.get("clips", [])]
    return EditorState(
        part=int(d["part"]),
        version=int(d.get("version", SCHEMA_VERSION)),
        clips=clips,
        effects=list(d.get("effects", [])),
        keyframes=list(d.get("keyframes", [])),
        meta=dict(d.get("meta", {})),
    )


def state_path(output_dir: Path, part: int) -> Path:
    return output_dir / f"part{part:02d}_editor_state.json"


def flow_plan_path(output_dir: Path, part: int) -> Path:
    return output_dir / f"part{part:02d}_flow_plan.json"


def load_state(output_dir: Path, part: int) -> EditorState:
    """Read editor state for a part. Auto-hydrates from flow_plan.json
    if no editor_state.json exists yet.
    """
    sp = state_path(output_dir, part)
    if sp.exists():
        with sp.open("r", encoding="utf-8") as f:
            return state_from_dict(json.load(f))
    fp = flow_plan_path(output_dir, part)
    if fp.exists():
        with fp.open("r", encoding="utf-8") as f:
            return from_flow_plan(json.load(f), part)
    # Neither file — return a blank state. API layer decides how to react.
    return EditorState(part=part)


def save_state(output_dir: Path, state: EditorState) -> Path:
    """Atomic write: .partial → os.replace. Survives crashes mid-write
    (Rule L154). Returns the canonical path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    sp = state_path(output_dir, state.part)
    # Write to a sibling .partial in the same filesystem, then rename.
    fd, tmp_name = tempfile.mkstemp(
        prefix=sp.name + ".",
        suffix=".partial",
        dir=str(output_dir),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state_to_dict(state), f, indent=2, ensure_ascii=False)
        os.replace(tmp_name, sp)
    except BaseException:
        # Best-effort cleanup; don't mask the original error.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return sp


def apply_jsonpatch(
    state: EditorState, patch: list[dict[str, Any]]
) -> EditorState:
    """Apply RFC 6902 patch ops and return a new EditorState. Never
    mutates the input.
    """
    import jsonpatch  # local import — jsonpatch is a thin C-less lib

    doc = state_to_dict(state)
    patched = jsonpatch.apply_patch(doc, patch, in_place=False)
    return state_from_dict(patched)
