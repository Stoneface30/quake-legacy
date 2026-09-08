"""Task 1 — demo_v2 scaffold + generated_clips provenance DB."""
import json
import sqlite3

import pytest

from creative_suite.database import demo_v2_db


@pytest.fixture()
def conn(tmp_path):
    c = demo_v2_db.connect(tmp_path / "demo_v2.db")
    yield c
    c.close()


def test_connect_creates_generated_clips_table(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='generated_clips'"
    ).fetchall()
    assert rows, "generated_clips table missing"


def test_insert_candidate_round_trip(conn):
    row = {
        "demo_name": "CA-test-2011.dm_73",
        "canonical_demo_hash": "ab" * 32,
        "server_time_ms": 203275,
        "round": 5,
        "capture_start_ms": 198275,
        "capture_end_ms": 208275,
        "frag_offsets_ms": json.dumps([5000, 7225]),
        "recorder_client": 7,
        "weapon": "ROCKET_SPLASH",
        "tags": "airshot,multikill",
        "rank_score": 26.5,
        "class": "T1_NEW",
        "clutch_context": None,
        "source_size_bytes": 1943489,
    }
    clip_id = demo_v2_db.insert_candidate(conn, row)
    got = conn.execute(
        "SELECT demo_name, class, promotion_status, qa_status, avi_path "
        "FROM generated_clips WHERE generated_clip_id=?", (clip_id,)
    ).fetchone()
    assert got == ("CA-test-2011.dm_73", "T1_NEW", "CANDIDATE", "PENDING", None)


def test_insert_candidate_rejects_unknown_keys(conn):
    with pytest.raises(ValueError):
        demo_v2_db.insert_candidate(conn, {"demo_name": "x", "server_time_ms": 0,
                                           "capture_start_ms": 0, "capture_end_ms": 1,
                                           "frag_offsets_ms": "[]", "class": "T1_NEW",
                                           "nonsense_column": 1})


def test_ensure_output_tree(tmp_path):
    root = demo_v2_db.ensure_output_tree(tmp_path)
    for sub in ("review", "generated_clips", "parts"):
        assert (root / sub).is_dir()
    # idempotent
    assert demo_v2_db.ensure_output_tree(tmp_path) == root
