"""The v1 -> v2 migration report counts like with like, matches frags by
identity, tolerates missing tables, and never carries a name."""
import json
import sqlite3

from engine.parser import corpus_migration_report as M

NAME = "SomePlayerName"


def _corpus(d, demos, frags, events=()):
    d.mkdir()
    c = sqlite3.connect(str(d / "frags_rebuilt.db"))
    c.executescript("""
        create table demos (demo_id integer primary key, content_hash text,
                            parse_error text, recorder_name text);
        create table frags (frag_id integer primary key, demo_id int, server_time_ms int,
                            victim_client int, attacker_client int, attacker_name text,
                            victim_name text, mod int, by_recorder int, tags text, score real);""")
    for i, h in enumerate(demos, 1):
        c.execute("insert into demos values (?,?,null,?)", (i, h, NAME))
    for demo_i, t, v, a, mod, br, tags, sc in frags:
        c.execute("insert into frags (demo_id, server_time_ms, victim_client, "
                  "attacker_client, attacker_name, victim_name, mod, by_recorder, "
                  "tags, score) values (?,?,?,?,?,?,?,?,?,?)",
                  (demo_i, t, v, a, NAME, NAME, mod, br, tags, sc))
    c.commit()
    c.close()
    r = sqlite3.connect(str(d / "frag_recognition.db"))
    r.execute("create table semantic_events_v1 (content_hash text, type text)")
    r.executemany("insert into semantic_events_v1 values (?,?)", events)
    r.commit()
    r.close()


def test_frags_are_matched_by_identity_and_scoped_to_the_build(tmp_path):
    # v1 holds demos A and B; the (limited) v2 build holds only A.
    _corpus(tmp_path / "old", ["A", "B"],
            [(1, 1000, 3, 5, 7, 1, "air", 1.0), (1, 2000, 4, 5, 7, 1, "", 1.0),
             (2, 1000, 3, 6, 7, 0, "", 1.0)],
            [("A", "jump"), ("A", "jump"), ("B", "jump")])
    _corpus(tmp_path / "new", ["A"],
            [(1, 1000, 3, 5, 7, 0, "air,multi", 1.5), (1, 3000, 2, 5, 7, 1, "", 1.0)],
            [("A", "jump")])
    r = M.report(tmp_path / "old", tmp_path / "new")
    f = r["frags"]
    assert r["scope_demos"] == 1
    assert (f["old"], f["new"], f["kept"], f["added"], f["removed"]) == (2, 2, 1, 1, 1)
    assert f["changed_in_kept"] == {"tags": 1}
    assert f["by_recorder_flips"] == {"from_recorder": 1}
    ev = r["tables"]["frag_recognition.db:semantic_events_v1 by type"]
    assert ev["by"]["jump"] == {"old": 2, "new": 1, "delta": -1}   # B out of scope


def test_highlight_overlap_is_measured_by_identity(tmp_path):
    for side, rows in (("old", [("A", 1000, 3, 9.0), ("A", 2000, 4, 8.0)]),
                       ("new", [("A", 1000, 3, 7.0), ("A", 3000, 2, 9.5)])):
        _corpus(tmp_path / side, ["A"], [])
        c = sqlite3.connect(str(tmp_path / side / "frag_recognition.db"))
        c.execute("create table recognized_frags (content_hash text, server_time_ms int,"
                  " victim_client int, highlight_score real)")
        c.executemany("insert into recognized_frags values (?,?,?,?)", rows)
        c.commit()
        c.close()
    h = M.report(tmp_path / "old", tmp_path / "new")["highlights"]["top50"]
    assert (h["old"], h["new"], h["overlap"]) == (2, 2, 1)
    assert h["jaccard"] == round(1 / 3, 3)


def test_missing_tables_are_reported_not_fatal(tmp_path):
    _corpus(tmp_path / "old", ["A"], [])
    _corpus(tmp_path / "new", ["A"], [])
    r = M.report(tmp_path / "old", tmp_path / "new")
    assert r["tables"]["frag_recognition.db:kill_occurrences_v1"]["old"] is None


def test_no_name_ever_reaches_the_report(tmp_path):
    _corpus(tmp_path / "old", ["A"], [(1, 1000, 3, 5, 7, 1, "", 1.0)])
    _corpus(tmp_path / "new", ["A"], [(1, 1000, 3, 5, 7, 1, "", 1.0)])
    r = M.report(tmp_path / "old", tmp_path / "new")
    text = json.dumps(r) + M.markdown(r)
    assert NAME not in text
