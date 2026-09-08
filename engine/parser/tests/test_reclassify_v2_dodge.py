"""Idempotency test for the NEAR_MISS_*/DODGE_STRAFE/DODGE_TO_KILL labels
added to engine/parser/reclassify_v2.py for the dodge/near-miss signal.

Builds a throwaway sqlite DB (never touches the real project databases —
reclassify_v2's module-level DB path constants are monkeypatched) with a
handful of synthetic recognized_frags rows carrying the attributes
extract_dodge_events.py would have written, then runs reclassify_v2.run()
twice and asserts the row state is byte-identical the second time (the
same convention this module's own docstring already commits to for every
other label group: "running twice must not double scores").

Run directly (this test dir is not in pyproject.toml's testpaths, same as
every other engine/parser extractor):

    python -m pytest engine/parser/tests/test_reclassify_v2_dodge.py -v
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import reclassify_v2  # noqa: E402

RECOGNIZED_FRAGS_DDL = """
CREATE TABLE recognized_frags (
  id INTEGER PRIMARY KEY, demo_name TEXT, content_hash TEXT,
  server_time_ms INTEGER, round INTEGER, mod INTEGER, weapon_name TEXT,
  victim_client INTEGER, classes TEXT, attributes TEXT,
  multikill_score REAL DEFAULT 0, air_score REAL DEFAULT 0,
  accuracy_score REAL DEFAULT 0, flick_score REAL DEFAULT 0,
  distance_score REAL DEFAULT 0, visibility_difficulty REAL DEFAULT 0,
  weapon_combo_score REAL DEFAULT 0, prediction_score REAL DEFAULT 0,
  movement_score REAL DEFAULT 0, highlight_score REAL DEFAULT 0,
  reasons TEXT, recognition_version INTEGER DEFAULT 1,
  speed_score REAL DEFAULT 0, precision_score REAL DEFAULT 0,
  visibility_score REAL DEFAULT 0, tracking_score REAL DEFAULT 0,
  combo_score REAL DEFAULT 0, clutch_score REAL DEFAULT 0,
  drama_score REAL DEFAULT 0, penalty_score REAL DEFAULT 0
);
"""


def _make_recog_db(path: Path):
    conn = sqlite3.connect(path)
    conn.executescript(RECOGNIZED_FRAGS_DDL)
    rows = []
    # 10 rows spread across a velocity-change range so the top-decile
    # DODGE_STRAFE percentile threshold has something real to bite on.
    for i in range(10):
        vchange = float((i + 1) * 10)   # 10..100
        attrs = {"dodge_scanned": 1, "dodge_near_miss_count": 0,
                 "dodge_max_velocity_change": vchange}
        if i == 9:
            # the row of interest: a tight rail near-miss 1200ms before the
            # kill (inside DODGE_TO_KILL_WINDOW_MS) plus the top-decile
            # velocity swing -> should earn NEAR_MISS_RAIL, DODGE_STRAFE
            # AND the DODGE_TO_KILL composite.
            attrs.update({
                "dodge_near_miss_count": 1,
                "dodge_best_threat_type": "RAIL",
                "dodge_min_closest_approach_units": 15.0,
                "dodge_to_kill_gap_ms": 1200,
            })
        rows.append((i, f"demo_{i}.dm_73", f"hash_{i}", 100000 + i * 10, 1,
                    10, "RAILGUN", 5, "[]", json.dumps(attrs), "[]"))
    conn.executemany(
        "INSERT INTO recognized_frags (id, demo_name, content_hash,"
        " server_time_ms, round, mod, weapon_name, victim_client, classes,"
        " attributes, reasons) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


def _make_frags_db(path: Path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE demos (name TEXT, gametype TEXT,"
                 " content_hash TEXT, duplicate_of TEXT)")
    conn.executemany("INSERT INTO demos VALUES (?,?,?,?)",
                     [(f"demo_{i}.dm_73", "CA", f"hash_{i}", None)
                      for i in range(10)])
    conn.commit()
    conn.close()


def _dump_rows(db_path: Path):
    conn = sqlite3.connect(db_path)
    rows = list(conn.execute(
        "SELECT id, classes, attributes, reasons, highlight_score,"
        " movement_score, drama_score FROM recognized_frags ORDER BY id"))
    conn.close()
    return rows


def test_dodge_labels_idempotent_across_two_runs(tmp_path, monkeypatch):
    recog_db = tmp_path / "frag_recognition.db"
    frags_db = tmp_path / "frags_rebuilt.db"
    clutch_csv = tmp_path / "clutch_recorder.csv"
    out_dir = tmp_path / "recognition_out"

    _make_recog_db(recog_db)
    _make_frags_db(frags_db)
    clutch_csv.write_text(
        "canonical_demo_hash,clutch_start_ms,clutch_end_ms,"
        "enemies_alive_at_start,outcome\n", encoding="utf-8")

    monkeypatch.setattr(reclassify_v2, "RECOG_DB", recog_db)
    monkeypatch.setattr(reclassify_v2, "FRAGS_DB", frags_db)
    monkeypatch.setattr(reclassify_v2, "CLUTCH_CSV", clutch_csv)
    monkeypatch.setattr(reclassify_v2, "OUT_DIR", out_dir)

    reclassify_v2.run()
    after_first = _dump_rows(recog_db)

    reclassify_v2.run()
    after_second = _dump_rows(recog_db)

    assert after_first == after_second

    target = next(r for r in after_second if r[0] == 9)
    classes = {c["name"] for c in json.loads(target[1])}
    assert "NEAR_MISS_RAIL" in classes
    assert "DODGE_STRAFE" in classes
    assert "DODGE_TO_KILL" in classes

    # a row with zero near-misses and a low (non-top-decile) velocity swing
    # must earn none of the new labels.
    quiet = next(r for r in after_second if r[0] == 0)
    quiet_classes = {c["name"] for c in json.loads(quiet[1])}
    assert not quiet_classes & {"NEAR_MISS_RAIL", "NEAR_MISS_ROCKET",
                                "NEAR_MISS_GRENADE", "DODGE_STRAFE",
                                "DODGE_TO_KILL"}


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
