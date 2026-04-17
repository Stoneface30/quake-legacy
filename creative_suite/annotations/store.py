from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from creative_suite.config import Config
from creative_suite.db.migrate import connect


@dataclass(frozen=True)
class AnnotationInput:
    part: int
    mp4_time: float
    description: str
    avi_effect: str | None
    dream_effect: str | None
    tags: list[str]
    clip_index: int | None
    clip_filename: str | None
    demo_hint: str | None


@dataclass(frozen=True)
class Annotation:
    id: str
    part: int
    mp4_time: float
    description: str
    avi_effect: str | None
    dream_effect: str | None
    tags: list[str]
    clip_index: int | None
    clip_filename: str | None
    demo_hint: str | None
    demo_file: str | None
    servertime_ms: int | None
    created_at: str
    deleted: bool = False


class AnnotationStore:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        cfg.annotations_dir.mkdir(parents=True, exist_ok=True)

    # ---------- public API ----------
    def create(self, inp: AnnotationInput) -> Annotation:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ann = Annotation(
            id=f"{today}-part{inp.part:02d}-{uuid.uuid4().hex[:8]}",
            part=inp.part, mp4_time=inp.mp4_time,
            description=inp.description,
            avi_effect=inp.avi_effect, dream_effect=inp.dream_effect,
            tags=list(inp.tags),
            clip_index=inp.clip_index, clip_filename=inp.clip_filename,
            demo_hint=inp.demo_hint, demo_file=None, servertime_ms=None,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._append_jsonl(ann)
        self._upsert_sqlite(ann)
        return ann

    def update(self, ann_id: str, **changes: Any) -> Annotation:
        existing = self._load_latest(ann_id)
        if existing is None:
            raise KeyError(ann_id)
        merged = Annotation(**{**asdict(existing), **changes})
        self._append_jsonl(merged)
        self._upsert_sqlite(merged)
        return merged

    def delete(self, ann_id: str) -> None:
        existing = self._load_latest(ann_id)
        if existing is None:
            raise KeyError(ann_id)
        tomb = Annotation(**{**asdict(existing), "deleted": True})
        self._append_jsonl(tomb)
        con = connect(self.cfg)
        try:
            con.execute("DELETE FROM annotations WHERE id = ?", (ann_id,))
        finally:
            con.close()

    def list_for_part(self, part: int) -> list[Annotation]:
        con = connect(self.cfg)
        try:
            rows = con.execute(
                "SELECT * FROM annotations WHERE part = ? "
                "ORDER BY mp4_time ASC",
                (part,),
            ).fetchall()
        finally:
            con.close()
        return [self._row_to_annotation(dict(r)) for r in rows]

    def rebuild_sqlite_from_jsonl(self) -> None:
        con = connect(self.cfg)
        try:
            con.execute("DELETE FROM annotations")
        finally:
            con.close()
        by_id: dict[str, Annotation] = {}
        for path in sorted(self.cfg.annotations_dir.glob("part*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                obj = json.loads(line)
                ann = Annotation(**obj)
                by_id[ann.id] = ann
        for ann in by_id.values():
            if not ann.deleted:
                self._upsert_sqlite(ann)

    # ---------- internals ----------
    def _jsonl_path(self, part: int) -> Path:
        return self.cfg.annotations_dir / f"part{part:02d}.jsonl"

    def _append_jsonl(self, ann: Annotation) -> None:
        p = self._jsonl_path(ann.part)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(ann)) + "\n")

    def _upsert_sqlite(self, ann: Annotation) -> None:
        con = connect(self.cfg)
        try:
            con.execute(
                """
                INSERT OR REPLACE INTO annotations(
                  id, part, mp4_time, description, avi_effect, dream_effect,
                  tags, clip_index, clip_filename, demo_hint,
                  demo_file, servertime_ms, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    ann.id, ann.part, ann.mp4_time, ann.description,
                    ann.avi_effect, ann.dream_effect,
                    json.dumps(ann.tags),
                    ann.clip_index, ann.clip_filename, ann.demo_hint,
                    ann.demo_file, ann.servertime_ms, ann.created_at,
                ),
            )
        finally:
            con.close()

    def _load_latest(self, ann_id: str) -> Annotation | None:
        con = connect(self.cfg)
        try:
            row = con.execute(
                "SELECT * FROM annotations WHERE id = ?", (ann_id,),
            ).fetchone()
        finally:
            con.close()
        return self._row_to_annotation(dict(row)) if row else None

    def _row_to_annotation(self, row: dict[str, Any]) -> Annotation:
        return Annotation(
            id=row["id"], part=row["part"], mp4_time=row["mp4_time"],
            description=row["description"],
            avi_effect=row["avi_effect"], dream_effect=row["dream_effect"],
            tags=json.loads(row["tags"] or "[]"),
            clip_index=row["clip_index"], clip_filename=row["clip_filename"],
            demo_hint=row["demo_hint"], demo_file=row["demo_file"],
            servertime_ms=row["servertime_ms"],
            created_at=row["created_at"], deleted=False,
        )
