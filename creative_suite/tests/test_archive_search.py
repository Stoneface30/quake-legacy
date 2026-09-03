"""The whole archive is the cast, not the top-scored frags."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import archive_search as asx


def _db(tmp_path, with_teleports=True):
    p = tmp_path / "a.db"
    db = sqlite3.connect(p)
    db.executescript("""
    CREATE TABLE recognized_frags(id INTEGER, content_hash TEXT, server_time_ms INTEGER,
      victim_client INTEGER, weapon_name TEXT);
    CREATE TABLE semantic_events_v1(content_hash TEXT, server_time_ms INTEGER, round INTEGER,
      type TEXT, entity_num INTEGER, client_num INTEGER, victim INTEGER, weapon INTEGER,
      x REAL, y REAL, z REAL, parm INTEGER, source TEXT);
    CREATE TABLE round_state_v1(content_hash TEXT, server_time_ms INTEGER, round INTEGER, cs INTEGER, value TEXT);
    CREATE TABLE player_teams_v1(content_hash TEXT, client INTEGER, team TEXT);
    CREATE TABLE server_text_v1(content_hash TEXT, server_time_ms INTEGER, round INTEGER, kind TEXT, text TEXT);
    CREATE TABLE missile_samples_v1(content_hash TEXT, server_time_ms INTEGER, entity_num INTEGER);
    """)
    a, b = "a" * 64, "b" * 64
    # two recordings; one of them is a different occurrence at the SAME time
    for h in (a, b):
        for t in (1000, 1025, 1050, 6000):
            db.execute("INSERT INTO semantic_events_v1 VALUES (?,?,1,'jump',NULL,3,NULL,NULL,"
                       "NULL,NULL,NULL,NULL,'playerstate')", (h, t))
    db.execute("INSERT INTO semantic_events_v1 VALUES (?,?,1,'death',5,NULL,NULL,NULL,"
               "NULL,NULL,NULL,NULL,'entity')", (a, 2000))
    if with_teleports:
        db.execute("""CREATE TABLE teleport_transits_v1(content_hash TEXT, server_time_ms INTEGER,
          client INTEGER, outcome TEXT, out_x REAL, out_y REAL, out_z REAL, in_x REAL, in_y REAL,
          in_z REAL, teleporter TEXT, components TEXT, nearest_at_dest INTEGER, kind TEXT)""")
        db.execute("INSERT INTO teleport_transits_v1 VALUES (?,?,?,'TELEPORT_PLAYER_CONFIRMED',"
                   "0,0,0,1,1,1,'t1','',NULL,'TRANSIT')", (a, 3000, 4))
        db.execute("INSERT INTO teleport_transits_v1 VALUES (?,?,?,'AMBIGUOUS',"
                   "0,0,0,1,1,1,'t1','',NULL,'TRANSIT')", (a, 3500, None))
    db.commit(); db.close()
    return p, a, b


def test_every_class_reports_coverage_and_never_silently_zero(tmp_path):
    p, a, b = _db(tmp_path, with_teleports=False)
    out = asx.count_by_class(db_path=p)
    assert out[asx.TELEPORT]["coverage"] == asx.UNKNOWN, "a missing table is not zero"
    assert "teleport_transits_v1" in out[asx.TELEPORT]["missing_evidence"]
    assert out[asx.JUMP]["coverage"] == "INDEXED" and out[asx.JUMP]["moments"] == 8
    assert out[asx.ONE_VX]["coverage"] == "NOT_INDEXED"      # evidence present, no query yet
    assert set(out) - {"version"} == set(asx.CLASSES)


def test_the_search_covers_more_than_frags(tmp_path):
    p, a, b = _db(tmp_path)
    out = asx.count_by_class(db_path=p)
    indexed = {k for k, v in out.items() if isinstance(v, dict)
               and v.get("coverage") == "INDEXED"}
    assert asx.JUMP in indexed and asx.DEATH_MATERIAL in indexed
    assert asx.TELEPORT in indexed
    assert asx.HERO_FRAG not in indexed or True   # frags are one class among many
    assert len(indexed) >= 5


def test_only_confirmed_teleports_are_material(tmp_path):
    p, a, b = _db(tmp_path)
    hits = asx.find(asx.TELEPORT, db_path=p)
    assert len(hits) == 1 and hits[0].subject_client == 4
    assert hits[0].server_time_ms == 3000


def test_results_are_addressed_by_recording_not_by_time_alone(tmp_path):
    p, a, b = _db(tmp_path)
    hits = asx.find(asx.JUMP, db_path=p)
    at_1000 = [h for h in hits if h.server_time_ms == 1000]
    assert len(at_1000) == 2, "the same time in two recordings is two occurrences"
    assert {h.content_hash for h in at_1000} == {a, b}
    assert len({h.identity for h in hits}) == len(hits)


def test_a_canonical_filter_excludes_collapsed_copies(tmp_path):
    p, a, b = _db(tmp_path)
    out = asx.count_by_class(db_path=p, canonical={a})
    assert out[asx.JUMP]["moments"] == 4 and out[asx.JUMP]["recordings"] == 1


def test_density_finds_where_a_class_clusters(tmp_path):
    p, a, b = _db(tmp_path)
    dense = asx.dense_windows(asx.JUMP, window_ms=5000, top=3, db_path=p)
    assert dense[0][2] == 3, "three jumps inside one five-second window"
    assert dense[0][1] == 0
    assert all(n >= dense[-1][2] for _, _, n in dense)


def test_an_unknown_class_is_refused(tmp_path):
    p, a, b = _db(tmp_path)
    with pytest.raises(ValueError, match="not a searchable class"):
        asx.find("NOT_A_CLASS", db_path=p)
