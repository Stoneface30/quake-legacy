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

import json
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


SCHEMA = """
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
"""


@pytest.fixture
def kill_db(tmp_path):
    """One recorder frag. The demo name is an alias, so it must never travel."""
    import sqlite3
    db = tmp_path / "k.db"
    c = sqlite3.connect(db)
    c.executescript(SCHEMA)
    c.execute("INSERT INTO scanned_demos VALUES ('h1','somebody_alias_2019',3,1,NULL,'',4)")
    c.execute("INSERT INTO kill_events_v1 VALUES (1,'h1',60000,60000000,1,'campgrounds',"
              "3,5,6,'ROCKET','PLAYER','PLAYER_KILL',3,1,0,'^1Tr4sH','tr4sh','vic','vic',"
              "NULL,NULL,'fp1','RECORDED_OBSERVED','DEMO_EV_OBITUARY')")
    c.commit(); c.close()
    return db


@pytest.fixture
def public_profile(monkeypatch):
    """A COPY of the public profile, swapped in for the duration of a test.

    Mutating the real dict in place is not safe here: profile_id hashes
    cfg_text, which iterates the dict, so popping and reinserting a key
    silently changes the id every other test asserts on.
    """
    copy = dict(mp.PROFILES[mp.PUBLIC_EXPORT_PROFILE_NAME])
    monkeypatch.setitem(mp.PROFILES, mp.PUBLIC_EXPORT_PROFILE_NAME, copy)
    return copy


@pytest.mark.parametrize("cvar", px.IDENTITY_CVARS_MUST_BE_ZERO)
def test_no_identity_cvar_can_regress_to_a_live_value(public_profile, cvar):
    """Every route, one at a time -- reopening any of them refuses the batch."""
    public_profile[cvar] = 1
    with pytest.raises(px.ExportRefused, match="burn player names"):
        px.assert_capture_profile_is_nameless()


@pytest.mark.parametrize("cvar", px.IDENTITY_CVARS_MUST_BE_ZERO)
def test_an_unpinned_identity_cvar_fails_closed(public_profile, cvar):
    """Deleting a pin must refuse, not pass. A missing key is not a zero."""
    del public_profile[cvar]
    with pytest.raises(px.ExportRefused, match="MISSING"):
        px.assert_capture_profile_is_nameless()


@pytest.mark.parametrize("token_cvar,gate_cvar", sorted(px.TOKEN_GATES.items()))
def test_a_name_token_with_an_open_gate_is_refused(
        public_profile, token_cvar, gate_cvar):
    """Tokens are only harmless while their TIME gate is shut.

    Blanking a token is not safety -- wolfcam falls back to a built-in
    default. The invariant is the pair.
    """
    public_profile[token_cvar] = "%k fragged %v"
    public_profile[gate_cvar] = 2500
    with pytest.raises(px.ExportRefused, match=token_cvar):
        px.assert_capture_profile_is_nameless()


def test_the_killfeed_is_covered_not_just_the_frag_message():
    """The +/-5s public window is wider than review's, so it catches more kills."""
    assert "cg_obituaryTime" in px.IDENTITY_CVARS_MUST_BE_ZERO
    assert px.TOKEN_GATES["cg_obituaryTokens"] == "cg_obituaryTime"
    assert mp.PROFILES[mp.PUBLIC_EXPORT_PROFILE_NAME]["cg_obituaryTime"] == 0


def test_the_scoreboard_is_covered_because_it_shows_itself():
    """A scoreboard is a list of names and it pops on death and round end."""
    for cvar in ("cg_scoreBoardWhenDead", "cg_roundScoreBoard",
                 "cg_scoreBoardAtIntermission", "cg_scoreBoardWarmup"):
        assert cvar in px.IDENTITY_CVARS_MUST_BE_ZERO


def test_export_refuses_before_capturing_anything(tmp_path, monkeypatch,
                                                  public_profile, kill_db):
    """The gate runs before the first capture, not after the last."""
    monkeypatch.setenv("CS_EXPORT_MOCK", "1")
    calls = []
    monkeypatch.setattr(px, "_capture",
                        lambda *a, **k: calls.append(a) or None)
    public_profile["cg_drawFragMessageTime"] = 2000
    with pytest.raises(px.ExportRefused):
        px.export(px.candidates_from_kill_events(limit=1, db=kill_db),
                  root=tmp_path / "x")
    assert calls == [], "a clip was captured despite the gate refusing"


def test_the_export_passes_the_public_profile_to_the_engine(tmp_path,
                                                            monkeypatch):
    """The bug was a DEFAULT, so this asserts the argument actually arrives.

    capture_demo(profile=None) means PROFILE_NAME, the batch profile -- not
    "no profile". Intercepting the real call is the only way to prove the
    export no longer relies on that fallback.
    """
    from creative_suite.engine import wolfcam_capture as wc
    from creative_suite.engine import media_provenance as mprov
    seen = {}

    def fake_capture_demo(safe, windows, staging=None, profile=None):
        seen["profile"] = profile
        avi = tmp_path / "x.avi"
        avi.write_bytes(b"stub")
        return {"ok": True, "avis": {windows[0]["clip_name"]: avi}}

    demo = tmp_path / "demos" / "d.dm_73"
    demo.parent.mkdir(parents=True, exist_ok=True)
    demo.write_bytes(b"stub")
    monkeypatch.setattr(px, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(wc, "ensure_install", lambda: None)
    monkeypatch.setattr(wc, "stage_demo", lambda p: "safe")
    monkeypatch.setattr(wc, "capture_demo", fake_capture_demo)
    monkeypatch.setattr(mprov, "assert_demo_source", lambda *a, **k: None)
    monkeypatch.setattr(px.subprocess, "run",
                        lambda *a, **k: type("R", (), {"returncode": 0})())

    cand = px.ExportCandidate(
        external_source_id="ql_" + "0" * 20, content_hash="h", event_time_ms=1,
        event_type="FRAG", mod=6, weapon="ROCKET", map_name="m",
        actor_display_name="x", actor_identity_id=None,
        recorder_display_name=None, is_actor_pov=True, machine_score=None,
        machine_score_version=None, demo_name="d")
    got = px._capture_locked(cand, 0, 1000, tmp_path / "out.mp4")

    assert seen["profile"] == mp.PUBLIC_EXPORT_PROFILE_NAME
    assert seen["profile"] != mp.PROFILE_NAME, "fell back to the batch profile"
    assert got == mp.profile_id(mp.PUBLIC_EXPORT_PROFILE_NAME)


def test_no_v1_render_can_be_the_media_source(tmp_path, monkeypatch, kill_db):
    """Public pixels are always a capture made now, from a raw demo."""
    monkeypatch.setenv("CS_EXPORT_MOCK", "1")
    out = px.export(px.candidates_from_kill_events(limit=1, db=kill_db),
                    root=tmp_path / "x")
    assert out["rows"][0]["media_provenance"] == "RAW_DEMO_CAPTURE"


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
        tmp_path, monkeypatch, kill_db):
    """`overlays_added: []` described this module; this describes the engine."""
    monkeypatch.setenv("CS_EXPORT_MOCK", "1")
    out = px.export(px.candidates_from_kill_events(limit=1, db=kill_db),
                    root=tmp_path / "x")
    row = out["rows"][0]
    assert "capture_profile_id" in row
    # CS_EXPORT_MOCK ran no engine, so nothing filmed this and the field says
    # so. A mock fixture claiming a real capture profile would be exactly the
    # untrue-but-plausible provenance this field was added to end.
    assert row["capture_profile_id"] is None


def test_the_manifest_leaks_no_identity_or_local_path(tmp_path, monkeypatch,
                                                      kill_db):
    """Blind-visible metadata must not carry a handle, a path or a filename."""
    monkeypatch.setenv("CS_EXPORT_MOCK", "1")
    out = px.export(px.candidates_from_kill_events(limit=1, db=kill_db),
                    root=tmp_path / "x")
    blob = json.dumps(out["rows"][0])
    assert "somebody_alias_2019" not in blob      # the demo filename is an alias
    assert "G:\\" not in blob and "/QUAKE_LEGACY/" not in blob
    assert out["rows"][0]["identity_visibility"] == "AFTER_VOTE"
    assert out["rows"][0]["public_eligible"] is False



