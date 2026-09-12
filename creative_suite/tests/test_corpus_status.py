"""The corpus says which parser built it; pre-v2 entity data reads as stale
without anything being written to the old databases."""
import sqlite3

import pytest

from engine.parser import corpus_status as CS


def _db(path, stamp=None):
    con = sqlite3.connect(str(path))
    con.execute("create table frags (x int)")
    con.commit()
    con.close()
    if stamp is not None:
        CS.stamp(path, stamp, git_commit="test")


def test_an_unstamped_database_is_stale(tmp_path):
    _db(tmp_path / "frags_rebuilt.db")
    assert CS.db_status(tmp_path / "frags_rebuilt.db") == CS.STALE


def test_a_v1_stamp_is_stale_and_a_v2_stamp_is_current(tmp_path):
    _db(tmp_path / "a.db", stamp=1)
    _db(tmp_path / "b.db", stamp=2)
    assert CS.db_status(tmp_path / "a.db") == CS.STALE
    assert CS.db_status(tmp_path / "b.db") == CS.CURRENT


def test_checking_never_creates_or_writes_a_database(tmp_path):
    assert CS.db_status(tmp_path / "frag_recognition.db") == CS.MISSING
    assert not (tmp_path / "frag_recognition.db").exists()
    _db(tmp_path / "frags_rebuilt.db")
    before = (tmp_path / "frags_rebuilt.db").read_bytes()
    CS.status(tmp_path)
    assert (tmp_path / "frags_rebuilt.db").read_bytes() == before


def test_require_current_fails_closed_on_stale_data(tmp_path):
    _db(tmp_path / "frags_rebuilt.db")
    with pytest.raises(CS.StaleCorpus):
        CS.require_current(tmp_path / "frags_rebuilt.db")


def test_the_parser_declares_the_version_the_gate_proved():
    from engine.parser import demo_parse
    assert demo_parse.PARSER_VERSION == CS.ENTITY_DATA_MIN_PARSER == 2
