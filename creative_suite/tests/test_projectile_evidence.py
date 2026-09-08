"""Projectile evidence contract + the Frag 5979 / Frag 4121 reconciliation.

Two frags on asylum, both ROCKET, both ``DIRECT_CONFIRMED``, from different
demos — easy to conflate, and a mix-up that once looked like the recognition
data contradicting itself:

| frag | server_time | flight | distance |
|------|-------------|--------|----------|
| 5979 |     553 075 |  25 ms |   38.7 u |
| 4121 |     826 600 | 300 ms |  318.6 u |

Frag 4121 is the canonical "#1 direct rocket". Frag 5979 is a point-blank
shot with no arc. Only 4121 can carry a projectile camera; the preview
correctly falls back for 5979. The synthetic tests pin the contract, and
the corpus tests (skip-if-unavailable, mirroring test_camera_paths.py) pin
the real measurements so the reconciliation cannot silently rot.

Frags are addressed by numeric id and resolved to a demo at run time. Demo
filenames embed player nicknames, and this repo is public.
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine.director_preview import (MIN_DISPLACEMENT_U,
                                                    MIN_FLIGHT_MS, MIN_POINTS,
                                                    projectile_evidence)

FRAG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

SNAPSHOT_TICK_MS = 25   # server snapshot resolution; the quantization floor


def _arc(n=24, span_ms=300, length_u=318.6):
    """A straight, well-sampled flight of the given span and length."""
    return [[round(i * span_ms / (n - 1)), i * length_u / (n - 1), 0.0, 0.0]
            for i in range(n)]


# ── the contract, on synthetic paths ────────────────────────────────────────

def test_healthy_arc_is_usable():
    ev = projectile_evidence({"launch": {"t": 0}, "impact": {"t": 300},
                              "points": _arc()})
    assert ev["usable"] and ev["reason"] is None
    assert ev["flight_ms"] == 300
    assert ev["displacement_u"] == pytest.approx(318.6, abs=0.1)


@pytest.mark.parametrize("path,reason", [
    (None, "no_path"),
    ({}, "no_path"),
    ({"points": []}, "too_few_points"),
    ({"points": [[0, 0.0, 0.0, 0.0]]}, "too_few_points"),
    ({"points": _arc(n=4)}, "too_few_points"),
    ({"points": _arc(span_ms=100)}, "flight_too_short"),
    ({"points": _arc(length_u=10.0)}, "displacement_too_small"),
    ({"points": [[0, 0.0, 0.0, 0.0], [0, 500.0, 0.0, 0.0]]},
     "non_positive_flight"),
    ({"points": [[0, "x", 0.0, 0.0], [300, 1.0, 0.0, 0.0]]},
     "malformed_points"),
    ({"points": [[0, float("nan"), 0.0, 0.0]] + _arc()[1:]},
     "non_finite_coords"),
])
def test_rejection_reasons_are_specific(path, reason):
    ev = projectile_evidence(path)
    assert not ev["usable"]
    assert ev["reason"] == reason


def test_thresholds_are_the_documented_ones():
    assert (MIN_FLIGHT_MS, MIN_POINTS, MIN_DISPLACEMENT_U) == (200, 8, 64.0)


def test_flight_is_measured_from_points_not_scalars():
    """The load-bearing property. 256 corpus rows carry
    ``launch.t == impact.t`` purely from snapshot quantization; a rule that
    trusted the scalars would score a real 300 ms arc as zero flight."""
    ev = projectile_evidence({"launch": {"t": 826600},   # equal scalars...
                              "impact": {"t": 826600},
                              "points": _arc()})         # ...real arc
    assert ev["usable"], "series must outrank the scalars"
    assert ev["flight_ms"] == 300
    assert ev["scalar_flight_ms"] == 0   # still reported, for diagnosis


def test_missing_scalars_do_not_prevent_grading():
    ev = projectile_evidence({"points": _arc()})
    assert ev["usable"]
    assert ev["scalar_flight_ms"] is None


# ── the real corpus ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def corpus():
    if not FRAG_DB.exists():
        pytest.skip("frag_recognition.db not present")
    con = sqlite3.connect(f"file:{FRAG_DB.as_posix()}?mode=ro", uri=True)
    try:
        con.execute("SELECT 1 FROM recognition_projectile_paths LIMIT 1")
    except sqlite3.Error as e:
        con.close()
        pytest.skip(f"recognition_projectile_paths unusable: {e}")
    yield con
    con.close()


POINT_BLANK_FRAG = 5979      # asylum, 25 ms, no arc
CANONICAL_FRAG = 4121        # asylum, ~300 ms direct rocket


def _path_for_frag(con, frag_id):
    """Resolve a frag id to its cached projectile path.

    Goes through ``recognized_frags`` rather than hard-coding a demo
    filename, which would put a player nickname in a public repo.
    """
    frag = con.execute(
        "SELECT demo_name, server_time_ms FROM recognized_frags WHERE id = ?",
        (frag_id,)).fetchone()
    if frag is None:
        return None
    row = con.execute(
        "SELECT path FROM recognition_projectile_paths "
        "WHERE demo_name = ? AND server_time_ms = ? ORDER BY version DESC "
        "LIMIT 1", frag).fetchone()
    return json.loads(row[0]) if row else None


def test_frag_5979_is_point_blank_and_unusable(corpus):
    path = _path_for_frag(corpus, POINT_BLANK_FRAG)
    if path is None:
        pytest.skip("frag 5979 path not in this database build")
    ev = projectile_evidence(path)
    assert ev["points"] == 2                            # launch and impact only
    assert ev["flight_ms"] == SNAPSHOT_TICK_MS          # one tick, no arc
    assert ev["displacement_u"] == pytest.approx(38.7, abs=0.5)
    assert not ev["usable"]
    # It fails three criteria at once — too few points, too short a flight,
    # too little displacement. Sampling is checked first, so that is the
    # reason reported; the assertions above pin the other two directly.
    assert ev["reason"] == "too_few_points"
    assert ev["flight_ms"] < MIN_FLIGHT_MS
    assert ev["displacement_u"] < MIN_DISPLACEMENT_U


def test_frag_4121_is_the_canonical_direct_rocket(corpus):
    """The ~300 ms / 318.6 u evidence belongs here, not to Frag 5979."""
    path = _path_for_frag(corpus, CANONICAL_FRAG)
    if path is None:
        pytest.skip("frag 4121 path not in this database build")
    ev = projectile_evidence(path)
    assert ev["flight_ms"] == pytest.approx(300, abs=25)
    assert ev["displacement_u"] == pytest.approx(318.6, abs=5.0)
    assert ev["usable"], "the canonical direct rocket must carry a camera"


def test_the_two_asylum_rockets_are_distinct_events(corpus):
    a = _path_for_frag(corpus, POINT_BLANK_FRAG)
    b = _path_for_frag(corpus, CANONICAL_FRAG)
    if a is None or b is None:
        pytest.skip("both asylum paths required")
    demos = corpus.execute(
        "SELECT id, demo_name FROM recognized_frags WHERE id IN (?, ?)",
        (POINT_BLANK_FRAG, CANONICAL_FRAG)).fetchall()
    assert len({d for _, d in demos}) == 2, "must be two different demos"
    assert projectile_evidence(a)["usable"] is False
    assert projectile_evidence(b)["usable"] is True


def test_equal_launch_impact_scalars_are_quantization_not_corruption(corpus):
    """Audited 2026-09-01. Every row whose launch/impact timestamps are equal
    has a point span of exactly one snapshot tick — the shortest flight the
    server clock can express. None is a long flight with a lost launch time,
    which would be corruption."""
    spans = []
    for (blob,) in corpus.execute(
            "SELECT path FROM recognition_projectile_paths"):
        try:
            j = json.loads(blob)
        except (TypeError, ValueError):
            continue
        pts = j.get("points") or []
        lt = (j.get("launch") or {}).get("t")
        it = (j.get("impact") or {}).get("t")
        if lt is None or it is None or len(pts) < 2 or it != lt:
            continue
        spans.append(int(pts[-1][0]) - int(pts[0][0]))
    if not spans:
        pytest.skip("no equal-scalar rows in this database build")
    assert set(spans) == {SNAPSHOT_TICK_MS}, (
        f"equal-timestamp rows must all be one tick; saw {sorted(set(spans))}")


def test_scalars_and_point_series_never_disagree(corpus):
    """The corroboration check: outside the quantization floor the two
    sources of flight duration agree exactly across the whole corpus."""
    disagreements = []
    for (blob,) in corpus.execute(
            "SELECT path FROM recognition_projectile_paths"):
        try:
            j = json.loads(blob)
        except (TypeError, ValueError):
            continue
        pts = j.get("points") or []
        lt = (j.get("launch") or {}).get("t")
        it = (j.get("impact") or {}).get("t")
        if lt is None or it is None or len(pts) < 2:
            continue
        scalar = int(it) - int(lt)
        series = int(pts[-1][0]) - int(pts[0][0])
        if scalar != 0 and scalar != series:
            disagreements.append((scalar, series))
    assert not disagreements, f"{len(disagreements)} rows disagree"
