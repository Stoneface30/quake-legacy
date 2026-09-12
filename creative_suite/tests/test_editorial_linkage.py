"""Human decisions migrate only one-to-one; everything else waits for a person."""
import sqlite3

from engine.parser import editorial_linkage as L


def _k(h, t, k=1, v=2, m=7):
    return (h, t, k, v, m)


def test_each_bucket():
    old_obs = {1: {_k("A", 100)},                  # clean one-to-one
               2: {_k("A", 200)},                  # gone in v2
               3: {_k("A", 300), _k("B", 300)},    # observations now in 2 occurrences
               4: {_k("A", 400)}, 5: {_k("B", 400)},  # both lead to one new occurrence
               6: {_k("A", 500)}}                  # fingerprint changed
    old_fp = {1: "f1", 2: "f2", 3: "f3", 4: "f4", 5: "f4", 6: "f6"}
    new_obs = {10: {_k("A", 100)}, 11: {_k("A", 300)}, 12: {_k("B", 300)},
               13: {_k("A", 400), _k("B", 400)}, 14: {_k("A", 500)}}
    new_fp = {10: "f1", 11: "f3", 12: "f3", 13: "f4", 14: "f6-new"}
    m = L.map_one_to_one(old_obs, old_fp, new_obs, new_fp)
    assert m[1] == (L.ONE_TO_ONE, 10)
    assert m[2] == (L.UNMATCHED, None)
    assert m[3] == (L.AMBIGUOUS_MANY_NEW, None)
    assert m[4] == m[5] == (L.AMBIGUOUS_SHARED, None)
    assert m[6] == (L.FINGERPRINT_DIFFERS, None)


def _recog(p, rows):
    c = sqlite3.connect(str(p))
    c.execute("create table kill_events_v1 (content_hash text, server_time_ms int, "
              "killer_client int, victim_client int, mod int, occurrence_id int, "
              "kill_fingerprint text)")
    c.executemany("insert into kill_events_v1 values (?,?,?,?,?,?,?)", rows)
    c.commit()
    c.close()


def test_linkage_reports_scope_and_never_guesses(tmp_path):
    _recog(tmp_path / "old.db", [("A", 100, 1, 2, 7, 1, "f1"), ("Z", 9, 1, 2, 7, 2, "f2")])
    _recog(tmp_path / "new.db", [("A", 100, 1, 2, 7, 50, "f1")])
    ed = tmp_path / "editorial.db"
    c = sqlite3.connect(str(ed))
    c.execute("create table human_reviews (source_id int)")
    c.executemany("insert into human_reviews values (?)", [(1,), (2,), (999,)])
    c.commit()
    c.close()
    before = ed.read_bytes()
    r = L.linkage(tmp_path / "old.db", tmp_path / "new.db", ed, scope={"A"})
    assert r["by_status"] == {L.ONE_TO_ONE: 1, L.OUT_OF_SCOPE: 1, L.NO_OLD_OCCURRENCE: 1}
    assert [x["old_occurrence_id"] for x in r["manual_review"]] == [999]
    assert not r["migratable_without_review"]
    assert ed.read_bytes() == before                     # read-only
