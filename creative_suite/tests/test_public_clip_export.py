"""The export seam: what crosses to THE_PANTHEON, and what must not.

These tests are mostly about refusal. The export is a small amount of code
whose entire job is to be narrow, so what is worth pinning is the narrowness:
the window is ten seconds and not six, no local path escapes, no overlay is
added, publication is off by default, and a batch cannot become a corpus.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from creative_suite.engine import public_clip_export as px   # noqa: E402
from creative_suite.engine import review_corpus as rc        # noqa: E402


@pytest.fixture
def kill_db(tmp_path: Path) -> Path:
    """A tiny corpus: one recorder frag, one clanmate frag seen from outside."""
    db = tmp_path / "k.db"
    c = sqlite3.connect(db)
    c.executescript("""
      CREATE TABLE kill_events_v1(
        kill_event_id INTEGER PRIMARY KEY, content_hash TEXT, server_time_ms INT,
        demo_us INT, round INT, map TEXT, killer_client INT, victim_client INT,
        mod INT, mod_name TEXT, killer_class TEXT, death_cause TEXT,
        recorder_client INT, is_recorder_killer INT, is_recorder_victim INT,
        killer_name_raw TEXT, killer_name_norm TEXT, victim_name_raw TEXT,
        victim_name_norm TEXT, killer_identity_id TEXT, victim_identity_id TEXT,
        kill_fingerprint TEXT, observation_provenance TEXT, event_provenance TEXT);
      CREATE TABLE scanned_demos(content_hash TEXT PRIMARY KEY, demo_name TEXT,
        recorder_client INT, n_frags INT, error TEXT, scanned_at TEXT,
        recognition_version INT);
      CREATE TABLE recognized_frags(id INTEGER PRIMARY KEY, content_hash TEXT,
        server_time_ms INT, highlight_score REAL, recognition_version INT);
    """)
    c.execute("INSERT INTO scanned_demos VALUES ('h1','somebody_alias_2019',3,2,NULL,'',4)")
    c.execute("INSERT INTO kill_events_v1 VALUES (1,'h1',60000,60000000,1,'campgrounds',"
              "3,5,6,'ROCKET','PLAYER','PLAYER_KILL',3,1,0,'^1Tr4sH','tr4sh','vic','vic',"
              "NULL,NULL,'fp1','RECORDED_OBSERVED','DEMO_EV_OBITUARY')")
    c.execute("INSERT INTO kill_events_v1 VALUES (2,'h1',90000,90000000,1,'campgrounds',"
              "7,5,10,'RAILGUN','PLAYER','PLAYER_KILL',3,0,0,'NaikoMarie','naikomarie',"
              "'vic','vic',NULL,NULL,'fp2','RECORDED_OBSERVED','DEMO_EV_OBITUARY')")
    c.execute("INSERT INTO recognized_frags VALUES (1,'h1',60000,7.5,4)")
    c.commit(); c.close()
    return db


@pytest.fixture
def mock_capture(monkeypatch):
    monkeypatch.setenv("CS_EXPORT_MOCK", "1")
    yield


# ── the two windows are different on purpose ────────────────────────────────

def test_the_public_window_is_ten_seconds_and_review_stays_six():
    """A director judging their own moment needs six seconds. A stranger
    scoring a play they have never seen needs run-up. Unifying these would
    quietly damage one of them."""
    assert px.PUBLIC_PRE_MS == 5000 and px.PUBLIC_POST_MS == 5000
    assert px.PUBLIC_DURATION_MS == 10000
    assert rc.PRE_MS == 3000 and rc.POST_MS == 3000


def test_the_event_offset_reports_where_the_event_really_landed(
        kill_db, mock_capture, tmp_path):
    """When the demo does not reach five seconds before the event the clip is
    short, and saying 5000 anyway would put the play in the wrong place for
    every downstream consumer."""
    cands = px.candidates_from_kill_events(limit=2, db=kill_db)
    early = type(cands[0])(**{**cands[0].__dict__, "event_time_ms": 2000})
    out = px.export([early], root=tmp_path / "x")
    assert out["written"] == 1
    assert out["rows"][0]["event_offset_ms"] == 2000    # not 5000


# ── nothing local, nothing added ────────────────────────────────────────────

def test_no_local_path_and_no_demo_filename_reaches_the_manifest(
        kill_db, mock_capture, tmp_path):
    """Demo filenames embed player aliases, so the demo is referenced by
    content hash. The clip path is relative to the export root."""
    cands = px.candidates_from_kill_events(limit=2, db=kill_db)
    out = px.export(cands, root=tmp_path / "x")
    blob = json.dumps(out["rows"])
    assert "somebody_alias_2019" not in blob
    assert "G:" not in blob and str(tmp_path) not in blob
    for row in out["rows"]:
        assert row["source_demo_ref"] == "h1"
        assert row["clip_path"].startswith("clips/")
        assert not Path(row["clip_path"]).is_absolute()


def test_the_export_adds_no_overlay_of_its_own(kill_db, mock_capture, tmp_path):
    """A clip that shows you whose play it is has voted for you."""
    out = px.export(px.candidates_from_kill_events(limit=1, db=kill_db),
                    root=tmp_path / "x")
    assert out["rows"][0]["overlays_added"] == []


def test_the_external_id_is_opaque_and_stable():
    a = px.external_id("abc", 1000, 3, 5)
    assert a == px.external_id("abc", 1000, 3, 5)
    assert a != px.external_id("abc", 1001, 3, 5)
    assert a.startswith("ql_") and "abc" not in a


# ── disclosure and eligibility ──────────────────────────────────────────────

def test_publication_is_off_until_the_user_says_otherwise(
        kill_db, mock_capture, tmp_path):
    """Ten years of archive footage was not recorded with the internet in
    mind. An importer that ignores this field still cannot publish by
    accident."""
    out = px.export(px.candidates_from_kill_events(limit=2, db=kill_db),
                    root=tmp_path / "x")
    assert all(r["public_eligible"] is False for r in out["rows"])
    assert all(r["identity_visibility"] == "AFTER_VOTE" for r in out["rows"])


def test_identity_travels_as_a_field_so_it_can_be_withheld(
        kill_db, mock_capture, tmp_path):
    """Pixels cannot be un-shown; a field can be. The name is in the manifest
    precisely so it is NOT in the video."""
    out = px.export(px.candidates_from_kill_events(limit=1, db=kill_db),
                    root=tmp_path / "x")
    assert out["rows"][0]["actor_display_name"] == "Tr4sH"    # colours stripped


# ── actor is not recorder ───────────────────────────────────────────────────

def test_a_clanmates_frag_is_not_sold_as_their_first_person_view(kill_db):
    """Row 2 is NaikoMarie's frag inside a demo recorded by client 3. It is
    that frag observed from a foreign camera, and is_actor_pov says so."""
    cands = px.candidates_from_kill_events(limit=2, db=kill_db)
    mine, theirs = cands[0], cands[1]
    assert mine.is_actor_pov is True
    assert theirs.is_actor_pov is False
    assert theirs.actor_display_name == "NaikoMarie"


def test_a_score_is_only_attached_where_it_means_the_same_thing(kill_db):
    """Every feature behind the recogniser's score came from the recorder's
    own player state. Attaching it to a foreign-camera frag would produce a
    number that is not comparable to the ones beside it."""
    cands = px.attach_machine_scores(
        px.candidates_from_kill_events(limit=2, db=kill_db), db=kill_db)
    assert cands[0].machine_score == 7.5
    assert cands[0].machine_score_version == "recognition-v4"
    assert cands[1].machine_score is None
    assert cands[1].machine_score_version is None


# ── a batch cannot become a corpus ──────────────────────────────────────────

def test_an_oversized_batch_is_refused_not_trimmed(kill_db, mock_capture, tmp_path):
    """Trimming silently is how you find out weeks later that half the export
    never happened."""
    one = px.candidates_from_kill_events(limit=1, db=kill_db)
    with pytest.raises(px.ExportRefused, match="MAX_BATCH"):
        px.export(one * (px.MAX_BATCH + 1), root=tmp_path / "x")


def test_an_empty_request_is_refused(tmp_path):
    with pytest.raises(px.ExportRefused, match="nothing to export"):
        px.export([], root=tmp_path / "x")


def test_re_export_skips_what_is_already_there(kill_db, mock_capture, tmp_path):
    root = tmp_path / "x"
    cands = px.candidates_from_kill_events(limit=2, db=kill_db)
    first = px.export(cands, root=root)
    second = px.export(cands, root=root)
    assert first["written"] == 2 and second["written"] == 0
    assert second["skipped"] == 2
    assert len((root / px.MANIFEST_NAME).read_text().strip().splitlines()) == 2


def test_a_failure_is_named_and_the_rest_still_ship(kill_db, mock_capture,
                                                    tmp_path, monkeypatch):
    cands = px.candidates_from_kill_events(limit=2, db=kill_db)
    real = px._capture
    calls = {"n": 0}

    def flaky(cand, s, e, dest):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("wolfcam said no")
        return real(cand, s, e, dest)

    monkeypatch.setattr(px, "_capture", flaky)
    out = px.export(cands, root=tmp_path / "x")
    assert out["written"] == 1 and out["failed"] == 1
    assert "wolfcam said no" in out["failures"][0]["error"]


def test_summary_reads_the_manifest_back(kill_db, mock_capture, tmp_path):
    root = tmp_path / "x"
    assert px.export_summary(root)["exists"] is False
    px.export(px.candidates_from_kill_events(limit=2, db=kill_db), root=root)
    s = px.export_summary(root)
    assert s["clips"] == 2 and s["public_eligible"] == 0
    assert s["actor_pov"] == 1 and s["observed_not_pov"] == 1


# ── the command line offers no way to export everything ─────────────────────

def test_the_cli_has_no_all_switch():
    """Every attributed kill is queryable. That is a different thing from
    having exported the media for it, and the CLI keeps them different."""
    from creative_suite.engine import export_cli
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), pytest.raises(SystemExit):
        export_cli.main(["query", "--help"])
    help_text = buf.getvalue()
    assert "--all" not in help_text
    assert "--dry-run" in help_text and "--limit" in help_text


def test_dry_run_captures_nothing(tmp_path, monkeypatch, capsys):
    """Reads the real corpus deliberately -- the point is that selecting from
    it captures no frame and creates no export directory. `_capture` raising
    is the assertion; a fixture database would only prove the fixture."""
    from creative_suite.engine import export_cli
    monkeypatch.setattr(px, "EXPORT_ROOT", tmp_path / "x")

    def refuse(*a, **k):
        raise AssertionError("--dry-run must not capture")

    monkeypatch.setattr(px, "_capture", refuse)
    assert export_cli.main(["query", "--limit", "2", "--dry-run"]) == 0
    assert "nothing captured" in capsys.readouterr().out
    assert not (tmp_path / "x").exists()


def test_the_export_waits_for_the_shared_capture_lock(monkeypatch, tmp_path,
                                                      kill_db):
    """WolfcamQL is one-at-a-time and the review proxy worker drives it too.
    Two engines launched at once would fight over the same staging directory
    and demo file locks."""
    monkeypatch.delenv("CS_EXPORT_MOCK", raising=False)
    from creative_suite.engine import review_proxy as rp
    monkeypatch.setattr(rp, "_try_acquire_lock", lambda: False)
    monkeypatch.setattr(px, "LOCK_WAIT_S", 0.0)
    cands = px.candidates_from_kill_events(limit=1, db=kill_db)
    out = px.export(cands, root=tmp_path / "x")
    assert out["written"] == 0 and out["failed"] == 1
    assert "_capture.lock" in out["failures"][0]["error"]


def test_the_lock_is_released_even_when_capture_fails(monkeypatch, tmp_path,
                                                      kill_db):
    monkeypatch.delenv("CS_EXPORT_MOCK", raising=False)
    from creative_suite.engine import review_proxy as rp
    released = {"n": 0}
    monkeypatch.setattr(rp, "_try_acquire_lock", lambda: True)
    monkeypatch.setattr(rp, "_release_lock",
                        lambda: released.__setitem__("n", released["n"] + 1))
    monkeypatch.setattr(px, "_capture_locked",
                        lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))
    px.export(px.candidates_from_kill_events(limit=1, db=kill_db),
              root=tmp_path / "x")
    assert released["n"] == 1


# ── stats ───────────────────────────────────────────────────────────────────

def test_measurements_and_machine_opinions_are_separate_blocks():
    """distance_units is a fact. accuracy_score is the recogniser's opinion on
    its own scale. Merging them would invite a voter to read a 7.5 as a
    percentage."""
    from creative_suite.engine import clip_stats
    b = clip_stats.for_clip("nope", 0, 3, 1, is_actor_pov=True)
    assert set(b) == {"stats", "machine_subscores", "stats_availability",
                      "stats_note"}
    assert "not percentages" in b["stats_note"]


def test_an_observed_clip_gets_universal_stats_and_says_what_is_missing():
    """Everything derived from aim, health, speed or view comes from the
    RECORDER's player state. When the actor is not the recorder there is no
    such state -- and a shorter dictionary that looks complete is worse than
    one that states the limit."""
    from creative_suite.engine import clip_stats
    b = clip_stats.for_clip("nope", 0, 3, 1, is_actor_pov=False)
    assert b["stats_availability"] == clip_stats.OBSERVED
    assert b["machine_subscores"] == {}
    assert "unmeasurable here, not zero" in b["stats_note"]
    # No recorder-derived measurement may appear on an observed clip.
    for out, _ in clip_stats.MEASURED.values():
        assert out not in b["stats"]


def test_universal_stats_hold_for_any_actor(kill_db):
    """An obituary is a server fact, not an observation of one player, so a
    multi-kill is countable even for a frag seen from another camera."""
    from creative_suite.engine import clip_stats
    s = clip_stats.universal_stats("h1", 60000, 3, 1, db=kill_db)
    assert s["round"] == 1 and s["multikill_size"] == 1
    assert s["actor_kills_this_round"] == 1
    assert s["ms_since_actors_prev_kill"] is None
    assert s["ms_to_actors_next_kill"] is None      # client 3 kills once


def test_a_broken_attribute_blob_costs_the_stats_not_the_clip(
        kill_db, mock_capture, tmp_path, monkeypatch):
    """An unreadable stats source is not a reason to lose a captured clip."""
    from creative_suite.engine import clip_stats
    monkeypatch.setattr(clip_stats, "for_clip",
                        lambda *a, **k: (_ for _ in ()).throw(ValueError("bad")))
    out = px.export(px.candidates_from_kill_events(limit=1, db=kill_db),
                    root=tmp_path / "x")
    assert out["written"] == 1
    assert out["rows"][0]["stats_availability"] == "UNAVAILABLE"


def test_refresh_rebuilds_metadata_without_recapturing(kill_db, mock_capture,
                                                       tmp_path, monkeypatch):
    """Metadata improves; captured media does not. Attaching a new stat must
    not cost forty seconds of wolfcam per clip."""
    root = tmp_path / "x"
    px.export(px.candidates_from_kill_events(limit=2, db=kill_db), root=root)
    monkeypatch.setattr(px, "_capture",
                        lambda *a: (_ for _ in ()).throw(
                            AssertionError("refresh must not capture")))
    out = px.refresh_manifest(root, db=kill_db)
    assert out == {"refreshed": 2, "dropped": 0}


def test_refresh_drops_a_row_whose_clip_is_gone(kill_db, mock_capture, tmp_path):
    """A manifest entry without its media is not a handoff."""
    root = tmp_path / "x"
    px.export(px.candidates_from_kill_events(limit=2, db=kill_db), root=root)
    next(iter((root / px.CLIP_DIR_NAME).glob("*.mp4"))).unlink()
    assert px.refresh_manifest(root, db=kill_db)["dropped"] == 1
