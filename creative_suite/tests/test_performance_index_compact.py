"""The compact index: discovery rows only, truth reconstructed, safe on a
constrained disk."""
from __future__ import annotations

import json
import sqlite3
import zlib
from pathlib import Path

import pytest

from creative_suite.tests.pantheon_fixtures import jumppad_rocket_trace
from engine.pantheon import performance_index as PI
from engine.pantheon import store as S


def test_index_rows_never_carry_a_sample_series():
    """The 94 GB failure mode: a serialized sample array inside an action row.
    The schema has no such column and the guard reads the schema itself."""
    cols = [line for line in PI.SCHEMA.splitlines() if "create table" in line or "  " in line]
    schema = "\n".join(cols)
    for word in ("trace_json", "transform_json", "samples_json", "aim_json", "blob_json"):
        assert word not in schema
    # a row is small: the summary fields plus packed cells and a short event list
    tr = jumppad_rocket_trace()
    sm = PI.summarize(tr, tr.start_ms + 250)
    row_bytes = len(json.dumps({k: v for k, v in sm.items() if k != "path_cells"})) + len(sm["path_cells"])
    assert row_bytes < 4000, row_bytes
    assert "transform" not in sm and "aim" not in sm


def test_packed_cells_round_trip_and_dedupe():
    cells = [(1, 2, 3), (1, 2, 3), (2, 2, 3), (1, 2, 3), (-5, 7, 0)]
    blob = PI.pack_cells(cells)
    assert PI.unpack_cells(blob) == [(1, 2, 3), (2, 2, 3), (-5, 7, 0)]
    assert PI.unpack_cells(None) == [] and PI.unpack_cells(b"") == []


def test_identity_is_semantic_and_the_locator_names_the_truth():
    assert PI.performance_id("JUMP_PAD", "4db16c445bcaafce", 5, 1198725) == \
        "PERF:JUMP_PAD:4db16c445bcaafce:5:1198725"
    loc = PI.locator("4db16c445bcaafce", 5, 1197225, 1200725)
    assert PI.parse_locator(loc) == ("4db16c445bcaafce", 5, 1197225, 1200725)
    with pytest.raises(ValueError):
        PI.parse_locator("PERF:x:y:z:w")


def test_trace_cache_stores_one_copy_per_content(tmp_path, monkeypatch):
    monkeypatch.setenv(S.ENV_STORE, str(tmp_path))
    tr = jumppad_rocket_trace()
    k1 = PI.cache_trace(tr, reason="test")
    k2 = PI.cache_trace(tr, reason="test again")
    assert k1 == k2
    con = sqlite3.connect(tmp_path / "performance_traces.db")
    n, raw, comp = con.execute("select count(*), sum(raw_bytes), sum(length(blob)) from traces").fetchone()
    con.close()
    assert n == 1 and comp < raw / 3          # compressed, and stored once
    back = PI.cached(PI.locator(tr.demo_hash, tr.client, tr.start_ms, tr.end_ms))
    assert back is not None and len(back.transform) == len(tr.transform)
    assert back.events[0].code == tr.events[0].code


def test_store_root_is_configurable_and_never_a_drive_letter_in_code(tmp_path, monkeypatch):
    monkeypatch.setenv(S.ENV_STORE, str(tmp_path))
    assert S.store_root() == tmp_path
    assert S.index_db().parent == tmp_path
    src = Path(PI.__file__).read_text(encoding="utf-8") + Path(S.__file__).read_text(encoding="utf-8")
    import re
    assert not re.search(r"[\"'][A-Z]:[/\\\\]", src), "a drive letter is hardcoded in engine code"


def test_the_corpus_has_no_gametype_filter():
    src = Path(PI.__file__).read_text(encoding="utf-8")
    i = src.index("def corpus(")
    j = src.index("con.close()", i)
    sql = src[src.index("con.execute(", i):j]
    assert "gametype" not in sql.lower()
