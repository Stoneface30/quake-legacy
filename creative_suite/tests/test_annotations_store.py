import json
from pathlib import Path

from creative_suite.annotations.store import AnnotationInput, AnnotationStore
from creative_suite.config import Config
from creative_suite.db.migrate import connect, migrate


def _store(tmp_path: Path, monkeypatch) -> AnnotationStore:
    monkeypatch.setenv("CS_STORAGE_ROOT", str(tmp_path))
    cfg = Config()
    migrate(cfg)
    return AnnotationStore(cfg)


def test_create_writes_jsonl_and_sqlite(tmp_path: Path, monkeypatch) -> None:
    s = _store(tmp_path, monkeypatch)
    rec = s.create(AnnotationInput(
        part=4, mp4_time=17.5,
        description="test", avi_effect="slowmo",
        dream_effect="killcam", tags=["peak"],
        clip_index=0, clip_filename="Demo (1) - A.avi", demo_hint="1",
    ))
    assert rec.id.startswith("20")
    jsonl = s.cfg.annotations_dir / "part04.jsonl"
    lines = jsonl.read_text().splitlines()
    assert len(lines) == 1
    loaded = json.loads(lines[0])
    assert loaded["description"] == "test"
    rows = s.list_for_part(4)
    assert len(rows) == 1 and rows[0].id == rec.id


def test_update_appends_new_jsonl_record(tmp_path: Path, monkeypatch) -> None:
    s = _store(tmp_path, monkeypatch)
    rec = s.create(AnnotationInput(
        part=4, mp4_time=17.5, description="orig", avi_effect=None,
        dream_effect=None, tags=[],
        clip_index=0, clip_filename="a.avi", demo_hint=None,
    ))
    s.update(rec.id, description="updated")
    rows = s.list_for_part(4)
    assert len(rows) == 1 and rows[0].description == "updated"


def test_delete_tombstones(tmp_path: Path, monkeypatch) -> None:
    s = _store(tmp_path, monkeypatch)
    rec = s.create(AnnotationInput(
        part=4, mp4_time=17.5, description="x", avi_effect=None,
        dream_effect=None, tags=[],
        clip_index=0, clip_filename="a.avi", demo_hint=None,
    ))
    s.delete(rec.id)
    assert s.list_for_part(4) == []


def test_rebuild_sqlite_from_jsonl(tmp_path: Path, monkeypatch) -> None:
    s = _store(tmp_path, monkeypatch)
    rec = s.create(AnnotationInput(
        part=4, mp4_time=1.0, description="a", avi_effect=None,
        dream_effect=None, tags=["peak"],
        clip_index=0, clip_filename="x.avi", demo_hint=None,
    ))
    con = connect(s.cfg)
    try:
        con.execute("DELETE FROM annotations")
    finally:
        con.close()
    s.rebuild_sqlite_from_jsonl()
    rows = s.list_for_part(4)
    assert len(rows) == 1 and rows[0].id == rec.id
