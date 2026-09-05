"""The public clip must not carry a player's name in its pixels.

The export module always promised this in its docstring and its manifest said
`overlays_added: []`, which was true and beside the point: the export drew no
overlay, and the ENGINE drew the name one layer below it. capture_demo() was
called without a profile argument, so it filmed with the batch profile, which
sets cg_drawFragMessageTokens "You fragged %v".

Measured on the review proxies captured with that same profile id
(091901df0daf): the victim's handle, centred, around y210-265 of a 1920x1080
frame. Reproduced in a fresh capture of one demo window, and absent from the
same window captured with the public profile -- the difference is one run of
113 frames, the length of cg_drawFragMessageTime 2000.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from creative_suite.engine import master_profile as mp        # noqa: E402
from creative_suite.engine import public_clip_export as px    # noqa: E402


def test_the_public_profile_draws_no_name_bearing_element():
    """Every channel that can put a handle on screen is off."""
    profile = mp.PROFILES[mp.PUBLIC_EXPORT_PROFILE_NAME]
    live = {k: profile.get(k) for k in px.NAME_BEARING_CVARS
            if profile.get(k) not in (0, "0")}
    assert live == {}, f"public profile would burn names: {live}"


def test_the_two_that_were_leaking_are_time_gates_held_at_zero():
    """cg_drawFragMessage / cg_obituary do not exist -- the gates are times."""
    profile = mp.PROFILES[mp.PUBLIC_EXPORT_PROFILE_NAME]
    assert profile["cg_drawFragMessageTime"] == 0    # "You fragged %v"
    assert profile["cg_obituaryTime"] == 0           # "%k %i %v"


def test_the_gameplay_master_keeps_its_frag_message():
    """The user's own film is a different audience, and it is not changed.

    "You fragged <name>" is a deliberate old-school beat where the names are
    the point. Suppressing it everywhere would have been the easy fix and the
    wrong one -- the defect was one profile filming for the wrong audience.
    """
    master = mp.PROFILES["TR4SH_GAMEPLAY_MASTER_V2"]
    assert master["cg_drawFragMessageTokens"] == "You fragged %v"
    assert master["cg_drawFragMessageTime"] == 2000


def test_changing_the_public_profile_back_is_refused_before_any_capture():
    """The gate reads the configuration, so a regression cannot reach film."""
    profile = mp.PROFILES[mp.PUBLIC_EXPORT_PROFILE_NAME]
    original = profile["cg_drawFragMessageTime"]
    profile["cg_drawFragMessageTime"] = 2000
    try:
        with pytest.raises(px.ExportRefused, match="burn player names"):
            px.assert_capture_profile_is_nameless()
    finally:
        profile["cg_drawFragMessageTime"] = original
    assert px.assert_capture_profile_is_nameless()


def test_the_export_names_its_capture_profile_instead_of_taking_the_default():
    """The bug was a DEFAULT, so the absence of an argument is the defect.

    capture_demo(profile=None) means PROFILE_NAME, the batch profile -- not
    "no profile". This pins that the export passes its own.
    """
    src = (Path(__file__).resolve().parents[1]
           / "engine" / "public_clip_export.py").read_text(encoding="utf-8")
    assert "profile=PUBLIC_EXPORT_PROFILE_NAME" in src


def test_the_public_profile_is_not_the_batch_profile():
    """Two audiences, two profiles, two cache identities."""
    assert mp.PUBLIC_EXPORT_PROFILE_NAME != mp.PROFILE_NAME
    assert (mp.profile_id(mp.PUBLIC_EXPORT_PROFILE_NAME)
            != mp.profile_id(mp.PROFILE_NAME))


def test_existing_profile_ids_are_unchanged_so_no_cached_clip_is_orphaned():
    """profile_id is part of the proxy cache key; adding a profile must not move it."""
    assert mp.profile_id("TR4SH_GAMEPLAY_MASTER_V2") == "091901df0daf"
    assert mp.profile_id("TR4SH_REVIEW_V2") == "d69e91d2b326"


def test_the_manifest_records_which_profile_filmed_the_clip(
        tmp_path, monkeypatch):
    """`overlays_added: []` described this module; this describes the engine."""
    monkeypatch.setenv("CS_EXPORT_MOCK", "1")
    from creative_suite.tests.test_public_clip_export import kill_db  # noqa: F401
    import sqlite3
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
    c.execute("INSERT INTO scanned_demos VALUES ('h1','somebody_alias_2019',3,1,NULL,'',4)")
    c.execute("INSERT INTO kill_events_v1 VALUES (1,'h1',60000,60000000,1,'campgrounds',"
              "3,5,6,'ROCKET','PLAYER','PLAYER_KILL',3,1,0,'^1Tr4sH','tr4sh','vic','vic',"
              "NULL,NULL,'fp1','RECORDED_OBSERVED','DEMO_EV_OBITUARY')")
    c.commit(); c.close()

    out = px.export(px.candidates_from_kill_events(limit=1, db=db),
                    root=tmp_path / "x")
    row = out["rows"][0]
    assert "capture_profile_id" in row
    # CS_EXPORT_MOCK ran no engine, so nothing filmed this and the field says
    # so. A mock fixture claiming a real capture profile would be exactly the
    # untrue-but-plausible provenance this field was added to end.
    assert row["capture_profile_id"] is None


def test_a_real_capture_records_the_profile_that_filmed_it():
    """The id written is the public profile's, resolved at capture time."""
    src = (Path(__file__).resolve().parents[1]
           / "engine" / "public_clip_export.py").read_text(encoding="utf-8")
    assert "return _mp.profile_id(PUBLIC_EXPORT_PROFILE_NAME)" in src
