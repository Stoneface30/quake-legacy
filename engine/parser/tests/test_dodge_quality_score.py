"""Tests for the DODGE QUALITY SCORE / hero tier added to
engine/parser/reclassify_v2.py (DODGE_HERO / RAIL_DODGE_HERO /
PROJECTILE_DODGE_HERO).

Two layers, matching the convention already used by
test_extract_dodge_events.py (pure geometry) and
test_reclassify_v2_dodge.py (throwaway-DB integration):

  1. `score_dodge_event` is pure — exercised directly against explicit
     percentile pools, so every threshold assertion is arithmetic, not a
     snapshot of whatever the corpus happened to contain today.
  2. `load_dodge_quality` + `run()` are exercised against a throwaway
     sqlite DB (module-level DB path constants monkeypatched; the real
     project databases are never opened).

The point of the tier is SEPARATION: the broad NEAR_MISS_*/DODGE_TO_KILL
labels fire on ~38% of recognized frags, so these tests are written around
the discriminations that justify a hero label at all — evasion vs
coincidence, measured geometry vs simulated, dodgeable vs point-blank.

Run directly (this test dir is not in pyproject.toml's testpaths, same as
every other engine/parser extractor):

    python -m pytest engine/parser/tests/test_dodge_quality_score.py -v
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import reclassify_v2  # noqa: E402
from reclassify_v2 import score_dodge_event  # noqa: E402

# Explicit, uniform pools: 200 values 0..199, so pctile(v) == v/2 exactly.
PROX_POOLS = {"RAIL": [float(i) for i in range(200)],
              "ROCKET": [float(i) for i in range(200)],
              "GRENADE": [float(i) for i in range(200)]}
VEL_POOL = [float(i) for i in range(200)]


def ev(**kw) -> dict:
    """A near-miss row with sane defaults; override what the test is about."""
    base = {"demo_name": "d.dm_73", "server_time_ms": 100000,
            "kill_anchor_ms": 100500, "closest_time_ms": 100000,
            "threat_type": "RAIL", "method": "segment",
            "closest_approach_units": 20.0, "recorder_velocity_change": 180.0,
            "survived": 1}
    base.update(kw)
    return base


# ── 1. the discrimination the tier exists for ────────────────────────────────

def test_evasion_separates_real_dodge_from_coincidental_proximity():
    """Same weapon, same distance, same timing — only the trajectory change
    differs. The player who broke trajectory must outscore the one who was
    already travelling in an unrelated direction, and only the former may
    pass the gate. This is the exact false positive the tier removes."""
    dodged = score_dodge_event(ev(recorder_velocity_change=190.0),
                               PROX_POOLS, VEL_POOL)
    coincidence = score_dodge_event(ev(recorder_velocity_change=20.0),
                                    PROX_POOLS, VEL_POOL)
    assert dodged["score"] > coincidence["score"]
    assert dodged["gated"] is True
    assert coincidence["gated"] is False   # evasion pctile 10 < gate 60


def test_wide_miss_is_gated_out_even_with_violent_movement():
    """A player juking wildly while a shot passes 190u away is not dodging
    that shot. Proximity and evasion are a conjunction, not an either/or."""
    wide = score_dodge_event(
        ev(closest_approach_units=190.0, recorder_velocity_change=199.0),
        PROX_POOLS, VEL_POOL)
    assert wide["proximity_pctile"] < reclassify_v2.DODGE_GATE_PROXIMITY_PCTILE
    assert wide["gated"] is False


def test_point_blank_projectile_is_gated_out_but_rail_is_not():
    """A rocket whose closest approach is at the muzzle had no flight time
    to be dodged in. Rail is hitscan (flight always 0) and is dodged
    pre-emptively, so the same rule must NOT be applied to it."""
    rocket = score_dodge_event(
        ev(threat_type="ROCKET", method="sim_straight",
           closest_time_ms=100000), PROX_POOLS, VEL_POOL)   # flight 0ms
    assert rocket["flight_ms"] == 0
    assert rocket["gated"] is False

    flying = score_dodge_event(
        ev(threat_type="ROCKET", method="sim_straight",
           closest_time_ms=100400, kill_anchor_ms=100900),
        PROX_POOLS, VEL_POOL)                                # flight 400ms
    assert flying["gated"] is True

    rail = score_dodge_event(ev(), PROX_POOLS, VEL_POOL)     # flight 0ms
    assert rail["flight_ms"] == 0
    assert rail["gated"] is True


def test_dead_recorder_is_never_a_dodge():
    assert score_dodge_event(ev(survived=0), PROX_POOLS, VEL_POOL)["gated"] \
        is False


# ── 2. geometric honesty ─────────────────────────────────────────────────────

def test_measured_rail_beam_outranks_simulated_projectile_paths():
    """Identical evidence, different provenance. A measured fire-origin ->
    railtrail-endpoint beam must score above a forward-simulated rocket,
    which must score above a gravity-only grenade with unmodelled bounces."""
    common = dict(closest_approach_units=20.0, recorder_velocity_change=180.0)
    rail = score_dodge_event(ev(method="segment", **common),
                             PROX_POOLS, VEL_POOL)
    rocket = score_dodge_event(ev(threat_type="ROCKET", method="sim_straight",
                                  **common), PROX_POOLS, VEL_POOL)
    grenade = score_dodge_event(ev(threat_type="GRENADE",
                                   method="sim_ballistic", **common),
                                PROX_POOLS, VEL_POOL)
    assert rail["score"] > rocket["score"] > grenade["score"]
    assert rail["geom_confidence"] == 1.0


def test_reconstructed_rail_ray_scores_below_measured_beam():
    measured = score_dodge_event(ev(method="segment"), PROX_POOLS, VEL_POOL)
    inferred = score_dodge_event(ev(method="ray_angle"), PROX_POOLS, VEL_POOL)
    assert inferred["score"] < measured["score"]


def test_unknown_method_scores_conservatively():
    """A method this module has never seen must not inherit full confidence."""
    unknown = score_dodge_event(ev(method="something_new"),
                                PROX_POOLS, VEL_POOL)
    assert unknown["geom_confidence"] == \
        reclassify_v2.DODGE_UNKNOWN_METHOD_CONFIDENCE


def test_components_are_reported_not_hidden():
    """The score must carry its own evidence — the manual-validation pass
    and /frags both read these fields."""
    s = score_dodge_event(ev(), PROX_POOLS, VEL_POOL)
    assert s["proximity_pctile"] == 90.0    # dist 20 -> pctile 10 -> 100-10
    assert s["evasion_pctile"] == 90.0      # vc 180 -> pctile 90
    for k in ("score", "immediacy", "flight_ms", "geom_confidence", "gated"):
        assert k in s


def test_immediacy_rewards_dodge_that_leads_into_the_kill():
    """The cinematic brief is "dodge a rail and kill something after"; a
    near-miss AFTER the kill contributes no immediacy at all."""
    tight = score_dodge_event(ev(kill_anchor_ms=100100), PROX_POOLS, VEL_POOL)
    loose = score_dodge_event(ev(kill_anchor_ms=101900), PROX_POOLS, VEL_POOL)
    after = score_dodge_event(ev(kill_anchor_ms=99000), PROX_POOLS, VEL_POOL)
    assert tight["immediacy"] > loose["immediacy"] > 0
    assert after["immediacy"] == 0.0


def test_missing_velocity_sample_cannot_earn_a_hero_label():
    """~30 corpus rows have no velocity sample. Absent evidence is not
    evidence: they must fail the gate rather than default to plausible."""
    s = score_dodge_event(ev(recorder_velocity_change=None),
                          PROX_POOLS, VEL_POOL)
    assert s["evasion_pctile"] == 0.0
    assert s["gated"] is False


# ── 3. throwaway-DB integration ──────────────────────────────────────────────

RECOGNIZED_FRAGS_DDL = """
CREATE TABLE recognized_frags (
  id INTEGER PRIMARY KEY, demo_name TEXT, content_hash TEXT,
  server_time_ms INTEGER, round INTEGER, mod INTEGER, weapon_name TEXT,
  victim_client INTEGER, classes TEXT, attributes TEXT,
  multikill_score REAL DEFAULT 0, air_score REAL DEFAULT 0,
  accuracy_score REAL DEFAULT 0, flick_score REAL DEFAULT 0,
  distance_score REAL DEFAULT 0, visibility_difficulty REAL DEFAULT 0,
  weapon_combo_score REAL DEFAULT 0, prediction_score REAL DEFAULT 0,
  movement_score REAL DEFAULT 0, highlight_score REAL DEFAULT 0,
  reasons TEXT, recognition_version INTEGER DEFAULT 1,
  speed_score REAL DEFAULT 0, precision_score REAL DEFAULT 0,
  visibility_score REAL DEFAULT 0, tracking_score REAL DEFAULT 0,
  combo_score REAL DEFAULT 0, clutch_score REAL DEFAULT 0,
  drama_score REAL DEFAULT 0, penalty_score REAL DEFAULT 0
);
"""
DODGE_EVENTS_DDL = """
CREATE TABLE recognition_dodge_events (
  demo_name TEXT, server_time_ms INTEGER, version INTEGER,
  kill_anchor_ms INTEGER, threat_type TEXT, shooter_client INTEGER,
  closest_approach_units REAL, closest_time_ms INTEGER,
  recorder_velocity_change REAL, survived INTEGER, method TEXT
);
"""

N_ROWS = 40


def _build_dbs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    recog, frags = tmp_path / "recog.db", tmp_path / "frags.db"
    clutch, out = tmp_path / "clutch.csv", tmp_path / "out"

    conn = sqlite3.connect(recog)
    conn.executescript(RECOGNIZED_FRAGS_DDL)
    conn.executescript(DODGE_EVENTS_DDL)

    frag_rows, event_rows = [], []
    for i in range(N_ROWS):
        anchor = 100000 + i * 5000
        # spread quality across the pool so percentile cuts have something
        # real to bite on: row 0 is the worst dodge, row N-1 the best.
        dist = 115.0 - i * 2.5           # 115u down to 17.5u
        vchange = 20.0 + i * 15.0        # 20 up to 605
        attrs = {"dodge_scanned": 1, "dodge_near_miss_count": 1,
                 "dodge_best_threat_type": "RAIL",
                 "dodge_min_closest_approach_units": dist,
                 "dodge_max_velocity_change": vchange,
                 "dodge_to_kill_gap_ms": 500}
        frag_rows.append((i, f"demo_{i}.dm_73", f"hash_{i}", anchor, 1, 10,
                          "RAILGUN", 5, "[]", json.dumps(attrs), "[]"))
        event_rows.append((f"demo_{i}.dm_73", anchor - 500, 1, anchor, "RAIL",
                           3, dist, anchor - 500, vchange, 1, "segment"))

    # one deliberately COINCIDENTAL row: the shot was as close as the very
    # best dodge, but the recorder barely changed trajectory. It must never
    # reach the hero tier no matter how the cuts land.
    coincident_anchor = 900000
    frag_rows.append((N_ROWS, "coincidence.dm_73", "hash_c", coincident_anchor,
                      1, 10, "RAILGUN", 5, "[]",
                      json.dumps({"dodge_scanned": 1,
                                  "dodge_near_miss_count": 1,
                                  "dodge_best_threat_type": "RAIL",
                                  "dodge_min_closest_approach_units": 8.0,
                                  "dodge_max_velocity_change": 5.0,
                                  "dodge_to_kill_gap_ms": 500}), "[]"))
    event_rows.append(("coincidence.dm_73", coincident_anchor - 500, 1,
                       coincident_anchor, "RAIL", 3, 8.0,
                       coincident_anchor - 500, 5.0, 1, "segment"))

    conn.executemany(
        "INSERT INTO recognized_frags (id, demo_name, content_hash,"
        " server_time_ms, round, mod, weapon_name, victim_client, classes,"
        " attributes, reasons) VALUES (?,?,?,?,?,?,?,?,?,?,?)", frag_rows)
    conn.executemany("INSERT INTO recognition_dodge_events"
                     " VALUES (?,?,?,?,?,?,?,?,?,?,?)", event_rows)
    conn.commit()
    conn.close()

    fconn = sqlite3.connect(frags)
    fconn.execute("CREATE TABLE demos (name TEXT, gametype TEXT,"
                  " content_hash TEXT, duplicate_of TEXT)")
    fconn.executemany(
        "INSERT INTO demos VALUES (?,?,?,?)",
        [(r[1], "CA", r[2], None) for r in frag_rows])
    fconn.commit()
    fconn.close()

    clutch.write_text("canonical_demo_hash,clutch_start_ms,clutch_end_ms,"
                      "enemies_alive_at_start,outcome\n", encoding="utf-8")
    return recog, frags, clutch, out


def _patch(monkeypatch, recog, frags, clutch, out):
    monkeypatch.setattr(reclassify_v2, "RECOG_DB", recog)
    monkeypatch.setattr(reclassify_v2, "FRAGS_DB", frags)
    monkeypatch.setattr(reclassify_v2, "CLUTCH_CSV", clutch)
    monkeypatch.setattr(reclassify_v2, "OUT_DIR", out)


def _classes(recog: Path) -> dict[str, set[str]]:
    conn = sqlite3.connect(recog)
    out = {demo: {c["name"] for c in json.loads(cl or "[]")}
           for demo, cl in conn.execute(
               "SELECT demo_name, classes FROM recognized_frags")}
    conn.close()
    return out


def _dump(recog: Path):
    conn = sqlite3.connect(recog)
    rows = list(conn.execute(
        "SELECT id, classes, attributes, reasons, highlight_score,"
        " movement_score, drama_score FROM recognized_frags ORDER BY id"))
    conn.close()
    return rows


def test_hero_tier_is_rare_and_obeys_the_subset_contract(tmp_path, monkeypatch):
    recog, frags, clutch, out = _build_dbs(tmp_path)
    _patch(monkeypatch, recog, frags, clutch, out)
    stats = reclassify_v2.run()

    by_demo = _classes(recog)
    hero = {d for d, c in by_demo.items() if "DODGE_HERO" in c}
    rail_hero = {d for d, c in by_demo.items() if "RAIL_DODGE_HERO" in c}
    broad = {d for d, c in by_demo.items() if "NEAR_MISS_RAIL" in c}

    # the whole point: a hero tier that is a small fraction of the broad
    # evidence, not a rename of it.
    assert rail_hero, "expected at least one hero-tier row"
    assert len(rail_hero) < len(broad) / 2
    # DODGE_HERO is a strict subset of the weapon-specific labels.
    assert hero <= rail_hero
    assert stats["rail_dodge_hero"] == len(rail_hero)
    assert stats["dodge_hero"] == len(hero)


def test_coincidental_proximity_never_reaches_the_hero_tier(tmp_path,
                                                            monkeypatch):
    """The closest near-miss in the whole synthetic corpus, with almost no
    trajectory change. Proximity alone must not buy a hero label."""
    recog, frags, clutch, out = _build_dbs(tmp_path)
    _patch(monkeypatch, recog, frags, clutch, out)
    reclassify_v2.run()

    coincidence = _classes(recog)["coincidence.dm_73"]
    assert not coincidence & {"DODGE_HERO", "RAIL_DODGE_HERO",
                              "PROJECTILE_DODGE_HERO"}


def test_hero_labels_are_idempotent_across_two_runs(tmp_path, monkeypatch):
    recog, frags, clutch, out = _build_dbs(tmp_path)
    _patch(monkeypatch, recog, frags, clutch, out)
    reclassify_v2.run()
    first = _dump(recog)
    reclassify_v2.run()
    assert _dump(recog) == first


def test_quality_evidence_is_persisted_on_the_anchor_row(tmp_path,
                                                         monkeypatch):
    recog, frags, clutch, out = _build_dbs(tmp_path)
    _patch(monkeypatch, recog, frags, clutch, out)
    reclassify_v2.run()

    conn = sqlite3.connect(recog)
    attrs = json.loads(conn.execute(
        "SELECT attributes FROM recognized_frags WHERE demo_name=?",
        (f"demo_{N_ROWS - 1}.dm_73",)).fetchone()[0])
    conn.close()
    for k in ("dodge_quality_score", "dodge_quality_threat",
              "dodge_quality_method", "dodge_proximity_pctile",
              "dodge_evasion_pctile", "dodge_geom_confidence"):
        assert k in attrs, k


def test_missing_events_table_degrades_to_no_hero_labels(tmp_path,
                                                         monkeypatch):
    """reclassify_v2 must still run against a DB built before the dodge
    extractor existed — same tolerance stage2_visibility already gets."""
    recog, frags, clutch, out = _build_dbs(tmp_path)
    conn = sqlite3.connect(recog)
    conn.execute("DROP TABLE recognition_dodge_events")
    conn.commit()
    conn.close()

    _patch(monkeypatch, recog, frags, clutch, out)
    stats = reclassify_v2.run()
    assert stats["dodge_hero"] == 0
    assert stats["rail_dodge_hero"] == 0
    assert not any(c & {"DODGE_HERO", "RAIL_DODGE_HERO",
                        "PROJECTILE_DODGE_HERO"}
                   for c in _classes(recog).values())


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
