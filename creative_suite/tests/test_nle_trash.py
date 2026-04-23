"""Tests for soft-delete (trash) feature on clip arrangements."""
import pytest
from pathlib import Path
from creative_suite.database import nle_db


@pytest.fixture
def db_path(tmp_path):
    p = tmp_path / "test_nle.db"
    nle_db.init_db(p)
    # Insert two clips for part 99
    clips = [
        {"role": "body", "clip_path": "/clips/a.avi", "tier": "T2",
         "is_fl": False, "pair_path": None, "duration_s": 4.0},
        {"role": "body", "clip_path": "/clips/b.avi", "tier": "T1",
         "is_fl": False, "pair_path": None, "duration_s": 3.5},
    ]
    nle_db.bulk_replace_arrangement(p, 99, clips)
    return p


def test_trash_clip_hides_from_arrangement(db_path):
    rows = nle_db.get_arrangement(db_path, 99)
    assert len(rows) == 2
    clip_id = rows[0]["id"]
    nle_db.trash_clip(db_path, clip_id)
    active = nle_db.get_arrangement(db_path, 99)
    assert len(active) == 1
    assert active[0]["id"] != clip_id


def test_trash_clip_kept_in_db(db_path):
    rows = nle_db.get_arrangement(db_path, 99)
    clip_id = rows[0]["id"]
    nle_db.trash_clip(db_path, clip_id)
    all_rows = nle_db.get_arrangement_all(db_path, 99)
    assert any(r["id"] == clip_id and r["trashed"] == 1 for r in all_rows)


def test_restore_clip(db_path):
    rows = nle_db.get_arrangement(db_path, 99)
    clip_id = rows[0]["id"]
    nle_db.trash_clip(db_path, clip_id)
    nle_db.restore_clip(db_path, clip_id)
    active = nle_db.get_arrangement(db_path, 99)
    assert len(active) == 2
