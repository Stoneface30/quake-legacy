"""The parser-v2 rebuild cannot touch the live corpus, and notices a module
that reached for a database the build root does not have."""
import argparse
import sqlite3
from pathlib import Path

import pytest

from engine.parser import rebuild_corpus_v2 as R


def _checkout(p: Path) -> Path:
    (p / "engine" / "parser").mkdir(parents=True)
    (p / "engine" / "parser" / "demo_parse.py").write_text("")
    return p


def test_the_live_root_is_refused(tmp_path):
    live = _checkout(tmp_path / "live")
    with pytest.raises(R.RebuildRefused):
        R.check_roots(live, live)


def test_a_build_root_inside_the_live_data_is_refused(tmp_path):
    live = _checkout(tmp_path / "live")
    inside = _checkout(live / "creative_suite" / "build")
    with pytest.raises(R.RebuildRefused):
        R.check_roots(inside, live)


def test_a_build_root_that_is_not_a_checkout_is_refused(tmp_path):
    live = _checkout(tmp_path / "live")
    (tmp_path / "empty").mkdir()
    with pytest.raises(R.RebuildRefused):
        R.check_roots(tmp_path / "empty", live)


def test_a_separate_checkout_is_accepted(tmp_path):
    R.check_roots(_checkout(tmp_path / "build"), _checkout(tmp_path / "live"))


def test_an_unexpected_or_empty_database_fails_the_stage(tmp_path):
    ok = tmp_path / "frags_rebuilt.db"
    sqlite3.connect(str(ok)).execute("create table t (x)").connection.commit()
    assert R.unexpected_dbs(tmp_path) == []
    (tmp_path / "editorial.db").write_bytes(b"")                 # empty: HL-9
    (tmp_path / "music_features_v2.db").write_bytes(b"x" * 10)  # not ours
    problems = R.unexpected_dbs(tmp_path, {"frag_recognition.db"})
    assert any("empty database editorial.db" in p for p in problems)
    assert any("unexpected database music_features_v2.db" in p for p in problems)
    assert any("frag_recognition.db was not produced" in p for p in problems)


def test_stages_run_in_the_documented_dependency_order():
    a = argparse.Namespace(workers=2, limit=None)
    names = [n for n, _c, _r in R.stages(a)]
    assert names == ["corpus", "recognition_pass1", "norms", "recognition",
                     "kill_events", "semantic_events", "enrichment", "occurrences",
                     "mining", "lineage"]


def test_the_enrichment_stage_never_clears_tables():
    a = argparse.Namespace(workers=2, limit=None)
    cmds = dict((n, c) for n, c, _r in R.stages(a))["enrichment"]
    assert all("--clear" not in cmd for cmd in cmds)
