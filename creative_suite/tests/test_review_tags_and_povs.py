"""Purpose kept apart from quality, and every camera kept visible.

These exist because of one observation about the months ahead: the biggest
remaining risk is no longer extraction accuracy, it is throwing information
away during review that the editor will wish had been captured. `T4` on its
own tells an editor almost nothing; `T4 + PREDICTION + ROCKET + CLEAN_POV`
tells them where the clip belongs.

Nothing here writes a HUMAN_USER row. Every tag is written with TEST
provenance into a throwaway database.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import pov_cluster as pv
from creative_suite.engine import review_corpus as rc
from creative_suite.engine import review_tags as rt

RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"


def _corpus() -> bool:
    try:
        with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
            return bool(c.execute(
                "SELECT 1 FROM kill_occurrences_v1 LIMIT 1").fetchone())
    except sqlite3.Error:
        return False


@pytest.fixture()
def tagdb(tmp_path, monkeypatch):
    monkeypatch.setattr(rt, "EDITORIAL_DB", tmp_path / "editorial.db")
    return tmp_path


# ── the vocabulary is frozen ────────────────────────────────────────────────

def test_the_vocabulary_is_exactly_what_was_agreed():
    """Frozen so a judgement made in review one thousand means what it meant
    in review one. Adding a tag later is safe; changing what one MEANS is not.
    """
    assert set(rt.TAGS) == {
        "RAIL", "LG", "ROCKET", "GRENADE",
        "AIM", "PREDICTION", "MOVEMENT", "TEAMPLAY",
        "CLUTCH", "MULTIKILL", "FUNNY", "VOICE",
        "LEGACY", "ICONIC_PLAYER",
        "CLEAN_POV", "ALT_POV",
        "KEEP_CONTEXT", "GOLDEN",
    }
    assert len(set(rt.TAGS)) == len(rt.TAGS), "a tag is listed twice"


def test_a_tag_outside_the_vocabulary_is_refused(tagdb):
    with pytest.raises(rt.UnknownTag):
        rt.set_tag(1, "SICK_FRAG", provenance=rt.TEST)


def test_machine_traits_are_refused_as_human_tags(tagdb):
    """AIR_ROCKET is already measured on every occurrence.

    A human tag saying the same thing could disagree with the measurement,
    and then nobody could say which one the film should believe.
    """
    for t in ("AIR_ROCKET", "MID_AIR", "CAMERA_GOOD", "LEGACY_VALUE"):
        with pytest.raises(rt.UnknownTag):
            rt.set_tag(1, t, provenance=rt.TEST)


# ── purpose does not touch quality ──────────────────────────────────────────

def test_tags_are_orthogonal_to_the_verdict(tagdb):
    """A T3 can be the most useful clip in the film.

    Tagging must never write, imply or alter a T1-T5 role -- the two answer
    different questions and collapsing them loses the sentence.
    """
    rt.set_tag(4242, "PREDICTION", provenance=rt.TEST)
    rt.set_tag(4242, "ROCKET", provenance=rt.TEST)
    assert rt.tags_for(4242) == ["PREDICTION", "ROCKET"]

    with rt.conn() as c:
        tables = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "human_reviews" not in tables or not list(
        rt.conn().execute("SELECT 1 FROM human_reviews LIMIT 1")), \
        "tagging wrote something into the verdict table"


def test_a_tag_toggles_both_ways_and_is_idempotent(tagdb):
    rt.set_tag(7, "FUNNY", True, provenance=rt.TEST)
    rt.set_tag(7, "FUNNY", True, provenance=rt.TEST)
    assert rt.tags_for(7) == ["FUNNY"]
    rt.set_tag(7, "FUNNY", False, provenance=rt.TEST)
    rt.set_tag(7, "FUNNY", False, provenance=rt.TEST)
    assert rt.tags_for(7) == []


def test_golden_is_not_a_verdict_band(tagdb):
    """It is an instruction, not a score.

    T5 already means "filler, kept forever". GOLDEN means "no ranking,
    sampling or downselect may ever hide this", which is a different kind of
    statement and must be readable on its own.
    """
    assert rt.GOLDEN not in ("T1_FEATURE_FX", "T2_TRANSITION",
                             "T3_RHYTHM_MONTAGE", "T4_KEEP_NORMAL",
                             "T5_PASS_FILLER")
    rt.set_tag(11, rt.GOLDEN, provenance="IMPORTED_LEGACY_HUMAN")
    assert 11 in rt.golden_occurrence_ids()


def test_a_machine_written_golden_is_not_a_documentary_anchor(tagdb):
    """Only a human may mark one.

    `golden_occurrence_ids` is what protects a clip from being sampled away,
    so a TEST or suggestion row appearing there would give machine output the
    power to override the director's own ranking.
    """
    rt.set_tag(12, rt.GOLDEN, provenance=rt.TEST)
    assert rt.tags_for(12) == [rt.GOLDEN]        # stored, and visible
    assert 12 not in rt.golden_occurrence_ids()  # but never authoritative


def test_keep_context_survives_as_its_own_statement(tagdb):
    """The frag is not always the unit.

    A mediocre kill can sit inside an extraordinary fifteen seconds, and the
    editor has to be told which -- the verdict cannot carry that.
    """
    rt.set_tag(13, rt.KEEP_CONTEXT, provenance=rt.TEST)
    assert rt.KEEP_CONTEXT in rt.tags_for(13)


def test_counts_are_the_calibration_instrument(tagdb):
    for oid in (1, 2, 3):
        rt.set_tag(oid, "RAIL", provenance="IMPORTED_LEGACY_HUMAN")
    rt.set_tag(1, "CLUTCH", provenance="IMPORTED_LEGACY_HUMAN")
    assert rt.counts() == {"RAIL": 3, "CLUTCH": 1}


# ── cameras ─────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not _corpus(), reason="needs the local corpus")
def test_every_camera_on_a_moment_is_reported():
    """One kill happened once; several people may have recorded it.

    The occurrence layer merges them so the frag is judged once. This is what
    tells the reviewer the alternatives exist -- the "wrong" recorder for the
    kill is often the right camera for the film.
    """
    with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
        row = c.execute("SELECT occurrence_id, n_observations FROM "
                        "kill_occurrences_v1 WHERE n_observations > 1 "
                        "LIMIT 1").fetchone()
    if row is None:
        pytest.skip("no multi-POV occurrence in this corpus")
    oid, n = int(row[0]), int(row[1])
    d = pv.povs_for(oid)
    assert d["available"] and d["n_povs"] == n
    assert d["has_alternative"] is True
    assert "POVs available" in d["summary"]
    assert all(p["pov"] in pv.POV_LABEL for p in d["povs"])


def test_pov_classification_reads_the_demo_not_a_guess():
    """Killer and victim are stated facts; teammate is derived.

    When team data is missing this must say OTHER rather than guessing --
    "a stranger filmed it" and "your teammate filmed it" lead a director to
    different decisions.
    """
    def row(**kw):
        base = {"is_recorder_killer": 0, "is_recorder_victim": 0,
                "recorder_client": 5, "killer_client": 9}
        return {**base, **kw}

    assert pv.classify(row(is_recorder_killer=1), {}) == pv.SELF_POV
    assert pv.classify(row(is_recorder_victim=1), {}) == pv.VICTIM_POV
    assert pv.classify(row(), {5: "RED", 9: "RED"}) == pv.TEAM_POV
    assert pv.classify(row(), {5: "RED", 9: "BLUE"}) == pv.OTHER_POV
    assert pv.classify(row(), {5: "RED"}) == pv.OTHER_POV      # unknown != team
    assert pv.classify(row(), {}) == pv.OTHER_POV


def test_pov_never_leaks_demo_identity():
    """Demo filenames embed player aliases; content hashes are provenance.

    Neither belongs in a payload the browser receives.
    """
    import inspect
    src = inspect.getsource(pv.povs_for)
    assert '"content_hash"' not in src.split("return")[-1]
    d = pv.povs_for(1)
    for p in d.get("povs", []):
        assert "content_hash" not in p and "demo_name" not in p


# ── telefrags stay reachable ────────────────────────────────────────────────

@pytest.mark.skipif(not _corpus(), reason="needs the local corpus")
def test_telefrags_leave_the_normal_queue_but_stay_reachable():
    """Excluded because the map decided them, kept because teleporters are
    part of what Quake looks like and the documentary wants real ones."""
    doc = rc.count_items(rc.ALL_KILL, corpus=rc.TELEFRAG_DOC)
    assert doc > 0, "the documentary corpus is empty"
    q = rc.queue(limit=5, item_type=rc.ALL_KILL, corpus=rc.TELEFRAG_DOC)
    assert q and all(i.weapon == "TELEFRAG" for i in q)

    normal = {i.item_id for i in rc.queue(limit=200, item_type=rc.ALL_KILL,
                                          corpus=rc.ALL_PLAYERS)}
    assert not normal & {i.item_id for i in q}, \
        "a telefrag reached the normal queue"


# ── deletion is guarded, not blocked ────────────────────────────────────────

@pytest.mark.skipif(not _corpus(), reason="needs the local corpus")
def test_deleting_a_multi_camera_moment_warns_first():
    """A deletion hides every angle, including the one nobody has watched."""
    with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
        row = c.execute("SELECT occurrence_id FROM kill_occurrences_v1 "
                        "WHERE n_observations > 1 LIMIT 1").fetchone()
    if row is None:
        pytest.skip("no multi-POV occurrence")
    risk = rc.dismiss_risk(f"ALL_KILL:{int(row[0])}")
    assert risk["safe"] is False
    assert any("camera angles" in r for r in risk["reasons"])


@pytest.mark.skipif(not _corpus(), reason="needs the local corpus")
def test_the_guard_warns_and_never_refuses():
    """The reviewer is the authority. They just should not find out after."""
    risk = rc.dismiss_risk("ALL_KILL:495")
    assert set(risk) == {"item_id", "occurrence_id", "safe", "reasons"}
    assert isinstance(risk["reasons"], list)


# ── unfilmed moments go to the workshop ─────────────────────────────────────

@pytest.fixture()
def workshopdb(tmp_path, monkeypatch):
    from creative_suite.engine import reconstruction_queue as rq
    monkeypatch.setattr(rq, "EDITORIAL_DB", tmp_path / "editorial.db")
    return rq


def test_a_reconstruction_request_is_not_a_verdict(workshopdb):
    """Three different answers, three different tables.

    T1-T5 judges a clip. A deletion hides a moment. This says the moment is
    worth having and no footage of it exists -- the obituary is a server
    fact whether or not any camera was pointed at it.
    """
    rq = workshopdb
    rq.request(4242, "ALL_KILL:4242", rq.OFF_SCREEN, provenance=rq.TEST)
    got = rq.get(4242)
    assert got["state"] == rq.QUEUED and got["reason"] == rq.OFF_SCREEN
    with rq.conn() as c:
        tables = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "human_reviews" not in tables
    assert "dismissed_occurrences" not in tables


def test_the_workshop_never_builds_on_a_machine_request(workshopdb):
    """A reconstruction costs real work; only a human may order one."""
    rq = workshopdb
    rq.request(1, "ALL_KILL:1", rq.NO_CAMERA, provenance=rq.TEST)
    rq.request(2, "ALL_KILL:2", rq.NO_CAMERA,
               provenance="IMPORTED_LEGACY_HUMAN")
    ids = [r["occurrence_id"] for r in rq.pending()]
    assert ids == [2]
    assert len(rq.pending(human_only=False)) == 2


def test_a_reason_outside_the_vocabulary_is_refused(workshopdb):
    rq = workshopdb
    with pytest.raises(rq.UnknownReason):
        rq.request(1, "ALL_KILL:1", "LOOKED_BORING", provenance=rq.TEST)


def test_a_request_is_idempotent_and_withdrawable(workshopdb):
    rq = workshopdb
    rq.request(9, "ALL_KILL:9", rq.BAD_ANGLE, provenance=rq.TEST)
    rq.request(9, "ALL_KILL:9", rq.OBSCURED, provenance=rq.TEST)
    assert rq.get(9)["reason"] == rq.OBSCURED
    assert len(rq.pending(human_only=False)) == 1
    assert rq.withdraw(9) is True
    assert rq.get(9) is None
    assert rq.withdraw(9) is False


def test_only_the_workshop_moves_a_request_past_queued(workshopdb):
    rq = workshopdb
    rq.request(3, "ALL_KILL:3", provenance=rq.TEST)
    assert rq.set_state(3, rq.ACCEPTED)["state"] == rq.ACCEPTED
    assert not [r for r in rq.pending(human_only=False)
                if r["occurrence_id"] == 3]
    with pytest.raises(ValueError):
        rq.set_state(3, "MAYBE")


# ── named situations ────────────────────────────────────────────────────────

@pytest.mark.skipif(not _corpus(), reason="needs the local corpus")
def test_the_gauntlet_jumppad_is_findable():
    """Asked for by name: "the gauntlet jumpad is really funny".

    A weapon filter alone gives 293 of the user's gauntlet frags; the
    combination gives the 31 that came off a pad.
    """
    pad = rc.count_items(rc.USER_FRAG, corpus=rc.USER_FRAGS,
                         filters={"situation": "GAUNTLET_JUMPPAD"})
    plain = rc.count_items(rc.USER_FRAG, corpus=rc.USER_FRAGS,
                           filters={"situation": "GAUNTLET"})
    assert 0 < pad < plain, f"{pad} pad frags of {plain} gauntlet frags"
    q = rc.queue(limit=5, item_type=rc.USER_FRAG, corpus=rc.USER_FRAGS,
                 filters={"situation": "GAUNTLET_JUMPPAD"})
    assert q and all("GAUNT" in (i.weapon or "") for i in q)


@pytest.mark.skipif(not _corpus(), reason="needs the local corpus")
def test_a_situation_filter_uses_an_index():
    """Ranged on start_ms, because that is the indexed column.

    Filtering the movement table on peak_ms instead turned this into a scan
    of 40,342 rows for each of 201,876 candidates and the query never
    returned at all.
    """
    import time
    t0 = time.time()
    rc.count_items(rc.USER_FRAG, corpus=rc.USER_FRAGS,
                   filters={"situation": "GAUNTLET_JUMPPAD"})
    assert time.time() - t0 < 15, "the situation filter is scanning"


def test_an_unknown_situation_is_refused_not_ignored():
    with pytest.raises(ValueError):
        rc._situation_sql("ANYTHING_GOES")


# ── the isolation that failed once ──────────────────────────────────────────

def test_the_test_instance_redirects_every_human_writing_module():
    """A list that goes out of date silently is how live rows get written.

    The tag and workshop modules were added AFTER `review_test_instance.py`
    and were not redirected, so an automated 390x844 run wrote three tags and
    a reconstruction request into the user's live database, stamped
    HUMAN_USER. They were removed by hand.

    This asserts the launcher knows about every module that can write a human
    row, so the next one added fails here rather than in the user's data.
    """
    import importlib
    import inspect
    import sys
    from pathlib import Path

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    inst = importlib.import_module("review_test_instance")
    guarded = {name for name, _attr in inst.LIVE_MODULE_ATTRS}

    # Every engine module that owns an EDITORIAL_DB constant writes human
    # rows by definition -- that database holds nothing else.
    engine = REPO_ROOT / "creative_suite" / "engine"
    writers = set()
    for py in engine.glob("*.py"):
        src = py.read_text(encoding="utf-8", errors="replace").upper()
        if "EDITORIAL_DB" not in src:
            continue
        # Naming the database is not writing to it. Only a module that
        # actually mutates rows needs redirecting.
        if any(v in src for v in ("INSERT ", "UPDATE ", "DELETE ")):
            writers.add(f"creative_suite.engine.{py.stem}")

    missing = {m for m in writers if m not in guarded}
    # review_proxy holds its path under a differently named constant and is
    # guarded explicitly by that name.
    # review_proxy holds its path under a differently named constant and is
    # guarded by that name; director_preview resolves through review_proxy at
    # call time rather than owning a constant, so redirecting review_proxy
    # covers it.
    missing -= {"creative_suite.engine.review_proxy",
                "creative_suite.engine.director_preview"}
    assert not missing, (
        "these modules can write to the editorial database but the test "
        f"instance does not redirect them: {sorted(missing)}")


def test_the_test_instance_refuses_to_start_when_not_isolated(tmp_path):
    """Failing to start beats finding out afterwards which rows were written."""
    import importlib
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    inst = importlib.import_module("review_test_instance")
    with pytest.raises(SystemExit):
        inst.assert_isolated(tmp_path / "definitely-not-where-they-point.db")
