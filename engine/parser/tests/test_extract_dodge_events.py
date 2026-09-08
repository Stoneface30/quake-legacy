"""Unit tests for engine/parser/extract_dodge_events.py.

Run directly (this test dir is NOT in pyproject.toml's pytest testpaths,
which only cover creative_suite/tests — same as every other engine/parser
extractor, none of which have tests wired into the root pytest run either):

    python -m pytest engine/parser/tests/test_extract_dodge_events.py -v
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from extract_dodge_events import (   # noqa: E402
    analyze_dodges, nearest, segment_perp, straight_line_samples,
)
from extract_projectile_paths import angles_to_dir, simulate_grenade  # noqa: E402

ROCKET_SPEED = 1000.0
RECORDER = 0
SHOOTER = 1


# ── pure geometry helpers ────────────────────────────────────────────────────

def test_segment_perp_point_beside_midpoint():
    dist, t = segment_perp((0, 0, 0), (1000, 0, 0), (500, 50, 0))
    assert math.isclose(dist, 50.0, abs_tol=1e-6)
    assert math.isclose(t, 0.5, abs_tol=1e-6)


def test_segment_perp_clamps_past_endpoint():
    # point is "beyond" the segment end — distance must be to the endpoint,
    # not the infinite-line extrapolation (this is the whole reason
    # segment_perp exists instead of reusing the infinite-ray helper).
    dist, t = segment_perp((0, 0, 0), (1000, 0, 0), (1200, 0, 0))
    assert math.isclose(dist, 200.0, abs_tol=1e-6)
    assert t > 1.0


def test_segment_perp_none_safe():
    dist, t = segment_perp((0, 0, 0), (1000, 0, None), (500, 50, 0))
    assert dist == math.inf


def test_straight_line_samples_endpoints():
    pts = straight_line_samples((0, 0, 0), (1, 0, 0), 1000.0, 1000, sample_ms=250)
    assert pts[0] == (0, (0.0, 0.0, 0.0))
    last_t, last_pos = pts[-1]
    assert last_t == 1000
    assert math.isclose(last_pos[0], 1000.0, abs_tol=1e-6)


def test_nearest_respects_tolerance():
    series = [(100, "a"), (500, "b")]
    assert nearest(series, 120, 50) == (100, "a")
    assert nearest(series, 300, 50) is None


# ── synthetic demo builder ───────────────────────────────────────────────────

def _recorder_snaps(entries):
    """entries: [(t, (x,y,z), (vx,vy))]"""
    return [{"server_time_ms": t, "client_num": RECORDER,
             "origin_x": p[0], "origin_y": p[1], "origin_z": p[2],
             "vel_x": v[0], "vel_y": v[1]} for t, p, v in entries]


def _shooter_entities(entries, client=SHOOTER):
    return [{"server_time_ms": t, "client_num": client,
             "origin_x": p[0], "origin_y": p[1], "origin_z": p[2],
             "angle_yaw": yaw, "angle_pitch": pitch}
            for t, p, yaw, pitch in entries]


def test_rail_near_miss_survived_uses_segment_method():
    # shooter fires rail along +x from origin; railtrail (endpoint) lands
    # far down that line; recorder sits 50u off the beam at the midpoint
    # and takes no damage -> should surface as a RAIL near-miss via the
    # segment method (no angle reconstruction needed).
    parsed = {
        "snapshots": _recorder_snaps([
            (550, (500, 50, 0), (0, 0)),
            (1000, (500, 50, 0), (0, 0)),
            (1450, (500, 50, 0), (10, 0)),
        ]),
        "entities": [],
        "events": [
            {"type": "fire_weapon", "server_time_ms": 1000,
             "client_num": SHOOTER, "weapon": 7,
             "pos_x": 0, "pos_y": 0, "pos_z": 0},
            {"type": "railtrail", "server_time_ms": 1000,
             "client_num": SHOOTER, "pos_x": 1000, "pos_y": 0, "pos_z": 0},
        ],
    }
    out = analyze_dodges(parsed, [2000], RECORDER, angles_to_dir,
                         simulate_grenade, ROCKET_SPEED)
    assert out[2000]["summary"]["dodge_near_miss_count"] == 1
    ev = out[2000]["events"][0]
    assert ev["threat_type"] == "RAIL"
    assert ev["method"] == "segment"
    assert math.isclose(ev["closest_approach_units"], 50.0, abs_tol=0.5)
    assert ev["survived"] == 1
    assert ev["recorder_velocity_change"] == 10.0


def test_rail_hit_is_excluded_not_recorded():
    # identical geometry to the near-miss case, but the recorder actually
    # dies to the same shooter shortly after the shot -> must NOT be
    # recorded as a dodge (task: only survived windows are near-misses).
    parsed = {
        "snapshots": _recorder_snaps([
            (1000, (500, 50, 0), (0, 0)),
        ]),
        "entities": [],
        "events": [
            {"type": "fire_weapon", "server_time_ms": 1000,
             "client_num": SHOOTER, "weapon": 7,
             "pos_x": 0, "pos_y": 0, "pos_z": 0},
            {"type": "railtrail", "server_time_ms": 1000,
             "client_num": SHOOTER, "pos_x": 1000, "pos_y": 0, "pos_z": 0},
            {"type": "obituary", "server_time_ms": 1050,
             "victim_client": RECORDER, "killer_client": SHOOTER},
        ],
    }
    out = analyze_dodges(parsed, [2000], RECORDER, angles_to_dir,
                         simulate_grenade, ROCKET_SPEED)
    assert out[2000]["summary"]["dodge_near_miss_count"] == 0
    assert out[2000]["events"] == []


def test_rail_falls_back_to_angle_ray_without_railtrail():
    # no railtrail event at all -> must reconstruct via the shooter's own
    # view angles from the entity track instead of silently dropping it.
    parsed = {
        "snapshots": _recorder_snaps([(1000, (500, 50, 0), (0, 0))]),
        "entities": _shooter_entities([(990, (0, 0, 0), 0.0, 0.0)]),
        "events": [
            {"type": "fire_weapon", "server_time_ms": 1000,
             "client_num": SHOOTER, "weapon": 7,
             "pos_x": 0, "pos_y": 0, "pos_z": 0},
        ],
    }
    out = analyze_dodges(parsed, [2000], RECORDER, angles_to_dir,
                         simulate_grenade, ROCKET_SPEED)
    assert out[2000]["summary"]["dodge_near_miss_count"] == 1
    ev = out[2000]["events"][0]
    assert ev["method"] == "ray_angle"
    assert math.isclose(ev["closest_approach_units"], 50.0, abs_tol=1.0)


def test_rocket_forward_simulation_near_miss():
    # rocket fired along +x from the origin; recorder sits fixed 30u off
    # the flight line where the rocket passes ~500ms after launch.
    recorder_entries = [(t, (500, 30, 0), (0, 0) if t < 2450 else (200, 0))
                        for t in range(1550, 3001, 50)]
    parsed = {
        "snapshots": _recorder_snaps(recorder_entries),
        "entities": _shooter_entities([(1990, (0, 0, 0), 0.0, 0.0)]),
        "events": [
            {"type": "fire_weapon", "server_time_ms": 2000,
             "client_num": SHOOTER, "weapon": 5,
             "pos_x": None, "pos_y": None, "pos_z": None},
        ],
    }
    out = analyze_dodges(parsed, [4000], RECORDER, angles_to_dir,
                         simulate_grenade, ROCKET_SPEED)
    assert out[4000]["summary"]["dodge_near_miss_count"] == 1
    ev = out[4000]["events"][0]
    assert ev["threat_type"] == "ROCKET"
    assert ev["method"] == "sim_straight"
    assert math.isclose(ev["closest_approach_units"], 30.0, abs_tol=1.0)
    assert math.isclose(ev["closest_time_ms"], 2500, abs_tol=50)
    assert ev["recorder_velocity_change"] == 200.0


def test_far_shot_is_not_recorded():
    # shooter fires rail in a direction that never comes close to the
    # recorder -> no event, no false positive.
    parsed = {
        "snapshots": _recorder_snaps([(1000, (0, 5000, 0), (0, 0))]),
        "entities": [],
        "events": [
            {"type": "fire_weapon", "server_time_ms": 1000,
             "client_num": SHOOTER, "weapon": 7,
             "pos_x": 0, "pos_y": 0, "pos_z": 0},
            {"type": "railtrail", "server_time_ms": 1000,
             "client_num": SHOOTER, "pos_x": 1000, "pos_y": 0, "pos_z": 0},
        ],
    }
    out = analyze_dodges(parsed, [2000], RECORDER, angles_to_dir,
                         simulate_grenade, ROCKET_SPEED)
    assert out[2000]["summary"]["dodge_near_miss_count"] == 0


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
