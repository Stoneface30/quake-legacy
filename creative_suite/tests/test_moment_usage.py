"""Project-scoped moment consumption.

A moment is consumed only by VALIDATED / ASSIGNED / USED -- never by a
technical proof, a shortlist or a creative rejection -- and identity is
the gameplay moment, not the file it was saved in.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import moment_usage as mu


# ── moment consumption ──────────────────────────────────────────────────────

def _key(t=291_650, map_name="quarantine"):
    return mu.moment_key(map_name=map_name, server_time_ms=t,
                         weapon="ROCKET", victim_client=3)


@pytest.fixture
def db(tmp_path):
    return tmp_path / "editorial.db"


def test_identity_is_the_moment_not_the_file():
    a = mu.moment_key(map_name="quarantine", server_time_ms=291_650,
                      weapon="ROCKET", victim_client=3)
    b = mu.moment_key(map_name="qUARanTINe", server_time_ms=291_650,
                      weapon="rocket", victim_client=3)
    assert a == b
    assert a != mu.moment_key(map_name="quarantine", server_time_ms=291_675,
                              weapon="ROCKET", victim_client=3)


def test_technical_proof_does_not_consume(db):
    mu.record_technical_proof(db, _key(), note="canary render")
    assert _key() not in mu.excluded_keys(db)
    assert mu.get(db, _key()) is None            # no state created at all


def test_shortlist_does_not_consume(db):
    mu.shortlist(db, _key())
    assert mu.get(db, _key()).state == mu.SHORTLISTED
    assert _key() not in mu.excluded_keys(db)


def test_rejection_does_not_consume(db):
    mu.reject(db, _key(), note="creative")
    assert _key() not in mu.excluded_keys(db)


def test_validated_is_excluded_from_discovery(db):
    mu.validate(db, _key(), note="user approved")
    assert _key() in mu.excluded_keys(db)


def test_same_moment_under_another_filename_is_still_excluded(db):
    mu.validate(db, _key())
    cands = [{"map": "quarantine", "server_time_ms": 291_650,
              "weapon": "ROCKET", "victim_client": 3,
              "demo_name": "CA-<player>-quarantine.dm_73"},
             {"map": "Quarantine", "server_time_ms": 291_650,
              "weapon": "rocket", "victim_client": 3,
              "demo_name": "Demo (51) - 230;.dm_73"},        # a re-saved copy
             {"map": "asylum", "server_time_ms": 826_600,
              "weapon": "ROCKET", "victim_client": 1}]
    kept = mu.filter_available(db, cands)
    assert len(kept) == 1 and kept[0]["map"] == "asylum"


def test_release_restores_discovery(db):
    mu.assign(db, _key(), destination="MICRO_SEQUENCE_V2")
    assert _key() in mu.excluded_keys(db)
    mu.release(db, _key())
    assert _key() not in mu.excluded_keys(db)


def test_used_cannot_be_silently_released(db):
    mu.mark_used(db, _key(), destination="PART01")
    with pytest.raises(ValueError, match="cannot release"):
        mu.release(db, _key())
    assert _key() in mu.excluded_keys(db)


def test_shortlisting_or_rejecting_never_demotes_a_reservation(db):
    mu.validate(db, _key())
    mu.shortlist(db, _key())
    mu.reject(db, _key(), note="a later proof was rejected")
    assert mu.get(db, _key()).state == mu.VALIDATED


def test_assigned_records_its_destination(db):
    with pytest.raises(ValueError):
        mu.assign(db, _key(), destination="")
    s = mu.assign(db, _key(), destination="EDITORIAL_CANARY_V3_IMPACT")
    assert s.destination == "EDITORIAL_CANARY_V3_IMPACT"


def test_projects_are_scoped(db):
    mu.validate(db, _key(), project="other_project")
    assert _key() not in mu.excluded_keys(db)        # default project untouched


def test_history_is_kept(db):
    mu.shortlist(db, _key())
    mu.record_technical_proof(db, _key(), note="render")
    mu.validate(db, _key())
    h = mu.history(db, _key())
    assert [x["to_state"] for x in h] == [mu.SHORTLISTED, mu.SHORTLISTED,
                                          mu.VALIDATED]
    assert h[1]["note"].startswith("TECHNICAL_PROOF")


def test_the_project_literal_lives_in_one_place():
    src_dir = REPO_ROOT / "creative_suite" / "engine"
    hits = [p.name for p in src_dir.glob("*.py")
            if "quake_legacy_main_movie" in p.read_text(encoding="utf-8")]
    assert hits == ["moment_usage.py"]
