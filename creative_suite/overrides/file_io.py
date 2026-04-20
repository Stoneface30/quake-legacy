# creative_suite/overrides/file_io.py
"""part{NN}_overrides.txt — one line per clip override.

Format: `chunk=<name> slow=<f> slow_window=<f> head_trim=<f> tail_trim=<f> section_role=<s> [removed=true]`
Missing fields are omitted; readers get None for missing fields.
`removed=true` excludes the clip from the render entirely (Tier 1 clip-removal).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClipOverride:
    chunk: str
    slow: float | None = None
    slow_window: float | None = None
    head_trim: float | None = None
    tail_trim: float | None = None
    section_role: str | None = None
    removed: bool = False


def read_overrides(path: Path) -> list[ClipOverride]:
    if not path.exists():
        return []
    entries: list[ClipOverride] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        kv: dict[str, str] = {}
        for tok in line.split():
            if "=" in tok:
                k, _, v = tok.partition("=")
                kv[k] = v
        chunk = kv.get("chunk")
        if not chunk:
            continue
        entries.append(ClipOverride(
            chunk=chunk,
            slow=_f(kv.get("slow")),
            slow_window=_f(kv.get("slow_window")),
            head_trim=_f(kv.get("head_trim")),
            tail_trim=_f(kv.get("tail_trim")),
            section_role=kv.get("section_role"),
            removed=_bool(kv.get("removed")),
        ))
    return entries


def write_overrides(path: Path, entries: list[ClipOverride]) -> None:
    lines: list[str] = ["# part overrides — edited by cinema suite"]
    for e in entries:
        toks = [f"chunk={e.chunk}"]
        for k in ("slow", "slow_window", "head_trim", "tail_trim"):
            v = getattr(e, k)
            if v is not None:
                toks.append(f"{k}={v}")
        if e.section_role:
            toks.append(f"section_role={e.section_role}")
        if e.removed:
            toks.append("removed=true")
        lines.append(" ".join(toks))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _bool(s: str | None) -> bool:
    return s is not None and s.lower() in ("1", "true", "yes", "on")


def _f(s: str | None) -> float | None:
    if s is None or s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None
