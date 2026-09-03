"""Physics extends what was recorded; provenance never upgrades; synthetic
state never enters history."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (cinematic_synthetic as cs, demo_truth as dt,
                                   projectile_reconstruction as pr)
from engine.parser import bsp_geometry as bg


# ── a hand-built map: one solid floor slab, nothing else ────────────────────

class _FloorMap:
    """A single axis-aligned solid brush z in [-16, 0], 4096 wide.

    Six planes, one brush, one leaf, one trivial node whose plane sits far
    away so both children resolve to the same leaf. Enough for a projectile
    to fly, fall, hit the floor and bounce.
    """

    def __init__(self, floor_z: float = 0.0, thickness: float = 16.0,
                 half: float = 4096.0):
        self.planes = [
            (0.0, 0.0, 1.0, floor_z),            # top of the slab (normal +z)
            (0.0, 0.0, -1.0, thickness - floor_z),  # bottom
            (1.0, 0.0, 0.0, half), (-1.0, 0.0, 0.0, half),
            (0.0, 1.0, 0.0, half), (0.0, -1.0, 0.0, half),
            (0.0, 0.0, 1.0, -1_000_000.0),       # node plane: everything is in front
        ]
        self.brushsides = [0, 1, 2, 3, 4, 5]
        self.brushes = [(0, 6, bg.CONTENTS_SOLID)]
        self.leafbrushes = [0]
        self.leafs = [(0, 1)]
        self.nodes = [(6, -1, -1)]
        self.patch_cells = []
        self.world_brush_range = (0, 1)


FLOOR = _FloorMap()


def _rocket(pos=(0.0, 0.0, 200.0), direction=(1.0, 0.0, 0.0), t=1_000_000,
            evidence=dt.ENTITY_OBSERVED, speed=pr.ROCKET_SPEED_QL):
    return pr.LaunchState(pr.KIND_ROCKET, t, pos, direction, evidence, speed)


def _grenade(pos=(0.0, 0.0, 200.0), direction=(1.0, 0.0, 0.3), t=1_000_000):
    return pr.LaunchState(pr.KIND_GRENADE, t, pos, direction, dt.ENTITY_OBSERVED)


# ── contact with the world ──────────────────────────────────────────────────

def test_the_tracer_returns_the_plane_it_entered_through():
    hit = pr.first_contact(FLOOR, (0.0, 0.0, 100.0), (0.0, 0.0, -100.0))
    assert hit is not None
    assert hit.normal == (0.0, 0.0, 1.0)
    assert abs(hit.point[2]) < 1e-6
    assert 0.49 < hit.fraction < 0.51


def test_a_segment_in_open_air_has_no_contact():
    assert pr.first_contact(FLOOR, (0.0, 0.0, 100.0), (500.0, 0.0, 100.0)) is None


# ── rockets ─────────────────────────────────────────────────────────────────

def test_a_rocket_flies_straight_at_the_configured_speed():
    cont = pr.propagate(_rocket(), FLOOR)
    # 200 ms in: 0.2 s * 1000 u/s = 200 units along +x, no drop
    at = next(p for p in cont.points if p.t_us >= 1_200_000)
    assert abs(at.pos[0] - 200.0) < 12.0
    assert abs(at.pos[2] - 200.0) < 1e-6


def test_a_rocket_pointed_at_the_floor_impacts_and_stops():
    cont = pr.propagate(_rocket(direction=(0.0, 0.0, -1.0)), FLOOR)
    assert cont.end_reason == "IMPACT"
    assert abs(cont.end_pos[2]) < 1e-3
    # 200 u at 1000 u/s = 200 ms
    assert abs(cont.flight_us - 200_000) <= pr.STEP_MS * 1000


def test_a_rocket_that_never_lands_dies_at_its_lifetime():
    cont = pr.propagate(_rocket(direction=(0.0, 0.0, 1.0)), FLOOR)
    assert cont.end_reason == "LIFETIME"
    assert cont.flight_us == pr.ROCKET_LIFE_MS * 1000


def test_rocket_speed_is_a_recorded_parameter_not_an_assumption():
    slow = pr.propagate(_rocket(speed=pr.ROCKET_SPEED_DEFAULT,
                                direction=(0.0, 0.0, -1.0)), FLOOR)
    fast = pr.propagate(_rocket(speed=pr.ROCKET_SPEED_QL,
                                direction=(0.0, 0.0, -1.0)), FLOOR)
    assert slow.flight_us > fast.flight_us
    assert dict(slow.params)["rocket_speed"] == "900.0"
    assert dict(fast.params)["rocket_speed"] == "1000.0"


# ── grenades ────────────────────────────────────────────────────────────────

def test_a_grenade_falls_under_gravity():
    cont = pr.propagate(_grenade(direction=(1.0, 0.0, 0.0)), FLOOR)
    at = next(p for p in cont.points if p.t_us >= 1_200_000)
    # z = 200 - 0.5 * 800 * 0.2^2 = 184
    assert abs(at.pos[2] - 184.0) < 3.0


def test_a_grenade_bounces_off_the_floor_and_is_damped():
    cont = pr.propagate(_grenade(direction=(0.3, 0.0, -1.0)), FLOOR)
    assert cont.bounces, "expected at least one bounce"
    b = cont.bounces[0]
    assert b.normal == (0.0, 0.0, 1.0)
    assert b.speed_after == pytest.approx(b.speed_before * pr.BOUNCE_DAMPING, rel=1e-6)
    # the reflected vertical velocity points up
    after = next(p for p in cont.points if p.t_us > b.t_us)
    assert after.vel[2] > 0


def test_a_grenade_explodes_at_its_fuse():
    cont = pr.propagate(_grenade(), FLOOR)
    assert cont.end_reason in ("FUSE", "REST")
    assert cont.flight_us <= pr.GRENADE_FUSE_MS * 1000


def test_a_slow_grenade_on_a_flat_surface_comes_to_rest():
    # dropped almost straight down from very low, bounces die out fast
    cont = pr.propagate(pr.LaunchState(pr.KIND_GRENADE, 0, (0.0, 0.0, 2.0),
                                       (0.0, 0.0, -1.0), dt.ENTITY_OBSERVED),
                        FLOOR)
    assert cont.end_reason in ("REST", "FUSE")


# ── observed → reconstructed boundary ───────────────────────────────────────

def test_recorded_samples_stay_recorded_and_the_continuation_is_marked():
    observed = (pr.PathPoint(1_000_000, (0.0, 0.0, 200.0), (1000.0, 0.0, 0.0),
                             dt.ENTITY_OBSERVED),
                pr.PathPoint(1_025_000, (25.0, 0.0, 200.0), (1000.0, 0.0, 0.0),
                             dt.ENTITY_OBSERVED))
    cont = pr.propagate(_rocket(), FLOOR, observed=observed)
    assert cont.points[0].evidence == dt.ENTITY_OBSERVED
    assert cont.points[1].evidence == dt.ENTITY_OBSERVED
    assert all(p.evidence == dt.PHYSICS_RECONSTRUCTED for p in cont.points[2:])
    # continuity: the first reconstructed point is one step past the last sample
    assert cont.points[2].t_us == 1_025_000 + pr.STEP_MS * 1000
    assert abs(cont.points[2].pos[0] - 35.0) < 0.5
    assert any("resumed from the last RECORDED sample" in n for n in cont.notes)


# ── constraints never move physics ──────────────────────────────────────────

def test_a_compatible_later_event_constrains_without_moving_the_path():
    cont = pr.propagate(_rocket(direction=(0.0, 0.0, -1.0)), FLOOR)
    before = cont.end_pos
    res = pr.check_against_event(cont, event_kind="ROCKET_IMPACT",
                                 event_t_us=cont.end_t_us + 10_000,
                                 event_pos=(30.0, 0.0, 0.0))
    assert res.compatible
    out = pr.constrain(cont, res)
    assert out.end_pos == before
    assert out.confidence == pr.EVENT_CONSTRAINED
    assert all(p.evidence in (dt.EVENT_CONSTRAINED, dt.ENTITY_OBSERVED)
               for p in out.points)


def test_an_incompatible_event_is_reported_not_fitted():
    cont = pr.propagate(_rocket(direction=(0.0, 0.0, -1.0)), FLOOR)
    before = (cont.end_pos, cont.end_t_us)
    res = pr.check_against_event(cont, event_kind="FRAG",
                                 event_t_us=cont.end_t_us + 900_000,
                                 event_pos=(2000.0, 0.0, 0.0))
    assert not res.compatible
    assert "physics and evidence disagree" in res.explanation
    assert "unobserved dynamic body" in res.explanation
    out = pr.constrain(cont, res)
    assert (out.end_pos, out.end_t_us) == before
    assert out.confidence == pr.AMBIGUOUS


def test_a_time_residual_alone_is_enough_to_disagree():
    cont = pr.propagate(_rocket(direction=(0.0, 0.0, -1.0)), FLOOR)
    res = pr.check_against_event(cont, event_kind="FRAG",
                                 event_t_us=cont.end_t_us + 500_000,
                                 event_pos=cont.end_pos)
    assert not res.compatible
    assert res.time_residual_us == -500_000


# ── provenance ladder ───────────────────────────────────────────────────────

def test_reconstructed_points_can_never_become_recorded():
    assert not dt.may_relabel(dt.PHYSICS_RECONSTRUCTED, dt.ENTITY_OBSERVED)
    assert not dt.may_relabel(dt.EVENT_CONSTRAINED, dt.POV_AUTHORITATIVE)
    assert dt.may_relabel(dt.ENTITY_OBSERVED, dt.PHYSICS_RECONSTRUCTED)
    assert dt.may_relabel(dt.PHYSICS_RECONSTRUCTED, dt.PHYSICS_RECONSTRUCTED)


def test_the_cached_projectile_paths_are_not_recorded():
    """The extractor inferred them; the timeline must say so."""
    tl = dt.load(24326)
    assert tl.projectile is not None
    assert tl.projectile.evidence == dt.EVENT_CONSTRAINED
    assert not dt.is_recorded(tl.projectile.evidence)


def test_a_path_only_attaches_to_a_frag_of_its_own_weapon():
    assert dt.load(2340).projectile is None


def test_cache_identity_changes_with_physics_and_algorithm():
    a = pr.cache_key("h" * 64, 5, 1_000_000, "bsp1")
    b = pr.cache_key("h" * 64, 5, 1_000_000, "bsp1",
                     rocket_speed=pr.ROCKET_SPEED_DEFAULT)
    c = pr.cache_key("h" * 64, 5, 1_000_000, "bsp2")
    assert len({a, b, c}) == 3
    assert a == pr.cache_key("h" * 64, 5, 1_000_000, "bsp1")


# ── observation gaps ────────────────────────────────────────────────────────

def test_gaps_are_found_where_samples_go_quiet():
    samples = [(0, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
               (50_000, (50.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
               (900_000, (900.0, 0.0, 0.0), (1.0, 0.0, 0.0))]
    gaps = pr.gaps_from_samples(7, pr.KIND_ROCKET, samples)
    closed = [g for g in gaps if g.closed]
    assert len(closed) == 1 and closed[0].duration_us == 850_000
    open_ = [g for g in gaps if not g.closed]
    assert len(open_) == 1 and open_[0].last_seen_t_us == 900_000


# ── synthetic state ─────────────────────────────────────────────────────────

def test_a_synthetic_element_must_live_in_an_allowed_context():
    el = cs.SyntheticElement("headbutt", cs.DOMAIN_ANIMATION, cs.CONTEXT_MEME,
                             0, 500_000, "COMEDIC_RELEASE")
    assert el.evidence == dt.CINEMATIC_SYNTHETIC
    with pytest.raises(ValueError):
        cs.SyntheticElement("x", cs.DOMAIN_ANIMATION, "GAMEPLAY_REPLAY",
                            0, 500_000, "COMEDIC_RELEASE")


def test_a_synthetic_element_cannot_claim_another_evidence_class():
    with pytest.raises(ValueError):
        cs.SyntheticElement("x", cs.DOMAIN_CAMERA, cs.CONTEXT_INTRO, 0, 1,
                            "ESTABLISH_SUBJECT", evidence=dt.ENTITY_OBSERVED)


def test_a_synthetic_element_needs_a_real_purpose():
    with pytest.raises(ValueError):
        cs.SyntheticElement("x", cs.DOMAIN_CAMERA, cs.CONTEXT_INTRO, 0, 1,
                            "EFFECT_FOR_EFFECTS_SAKE")


def test_synthetic_state_cannot_enter_the_demo_truth_timeline():
    el = cs.SyntheticElement("eye portal", cs.DOMAIN_CAMERA,
                             cs.CONTEXT_TRANSITION, 0, 1_000_000,
                             "TRANSITION_TO_NEXT_SCENE")
    ev = cs.as_demo_event(el)
    with pytest.raises(ValueError):
        dt.DemoTruthTimeline(1, 0, "MY_FRAG", "ROCKET", None, None,
                             events=(ev,))


def test_the_three_provenance_kinds_stay_distinct_on_the_lane():
    lane = cs.provenance_lane([(0, 10)], [(10, 20)], [(20, 30)])
    assert [d["label"] for d in lane] == ["RECORDED", "RECONSTRUCTED", "SYNTHETIC"]


def test_synthetic_identity_is_deterministic():
    a = cs.SyntheticElement("x", cs.DOMAIN_MODEL, cs.CONTEXT_OUTRO, 0, 1, "ROUND_PAYOFF")
    b = cs.SyntheticElement("x", cs.DOMAIN_MODEL, cs.CONTEXT_OUTRO, 0, 1, "ROUND_PAYOFF")
    assert a.element_id == b.element_id


# ── curved surfaces give a plane (v1.1.0) ──────────────────────────────────

def test_triangle_entry_returns_the_face_normal_facing_the_shot():
    a, b, c = (0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 10.0, 0.0)   # z=0 floor
    hit = pr._triangle_entry((2.0, 2.0, 5.0), (2.0, 2.0, -5.0), a, b, c)
    assert hit is not None
    assert abs(hit.fraction - 0.5) < 1e-9
    assert hit.normal == pytest.approx((0.0, 0.0, 1.0))      # faces the origin above
    down = pr._triangle_entry((2.0, 2.0, -5.0), (2.0, 2.0, 5.0), a, b, c)
    assert down.normal == pytest.approx((0.0, 0.0, -1.0))    # and from below


def test_triangle_entry_misses_outside_the_triangle_and_the_segment():
    a, b, c = (0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 10.0, 0.0)
    assert pr._triangle_entry((8.0, 8.0, 5.0), (8.0, 8.0, -5.0), a, b, c) is None   # past the hypotenuse
    assert pr._triangle_entry((2.0, 2.0, 5.0), (2.0, 2.0, 1.0), a, b, c) is None     # stops short
    assert pr._triangle_entry((2.0, 2.0, 5.0), (6.0, 2.0, 5.0), a, b, c) is None     # parallel


def test_an_event_at_the_simulated_end_confirms_it_rather_than_cutting_it():
    """A recorded explosion within two frames of the fuse, on the path, is
    EXACT_DETERMINISTIC with the world-only reason kept."""
    from dataclasses import replace
    pts = tuple(pr.PathPoint(t * 25_000, (float(t), 0.0, 0.0), (40.0, 0.0, 0.0),
                             dt.PHYSICS_RECONSTRUCTED) for t in range(0, 101))
    launch = pr.LaunchState(pr.KIND_GRENADE, 0, pts[0].pos, pts[0].vel, dt.ENTITY_OBSERVED)
    cont = pr.Continuation(pr.KIND_GRENADE, launch, pts, pts[-1].t_us, "FUSE",
                           pts[-1].pos)
    final, res = pr.truncate_at_event(cont, event_kind="missile_miss",
                                      event_t_us=pts[-1].t_us - 25_000,
                                      event_pos=(99.0, 3.0, 0.0))
    assert res.compatible and final.end_reason == "FUSE"
    assert final.confidence == pr.EXACT_DETERMINISTIC
    assert "confirms" in res.explanation
    # well before the end it is still a dynamic contact
    cut, _ = pr.truncate_at_event(cont, event_kind="missile_hit",
                                  event_t_us=pts[40].t_us, event_pos=(40.0, 2.0, 0.0))
    assert cut.end_reason == "DYNAMIC_CONTACT"


# ── segmented provenance and camera eligibility ────────────────────────────

def _mixed_cont():
    pts = tuple(pr.PathPoint(t * 25_000, (float(t), 0.0, 0.0), (40.0, 0.0, 0.0),
                             dt.ENTITY_OBSERVED if t < 4 else dt.PHYSICS_RECONSTRUCTED)
                for t in range(0, 41))
    launch = pr.LaunchState(pr.KIND_ROCKET, 0, pts[0].pos, pts[0].vel, dt.ENTITY_OBSERVED)
    return pr.Continuation(pr.KIND_ROCKET, launch, pts, pts[-1].t_us, "IMPACT", pts[-1].pos)


def test_segments_tile_the_flight_and_carry_their_own_evidence():
    segs = pr.provenance_segments(_mixed_cont())
    assert [s.evidence for s in segs] == [dt.ENTITY_OBSERVED, dt.PHYSICS_RECONSTRUCTED]
    assert segs[0].start_us == 0 and segs[0].end_us == segs[1].start_us == 75_000   # last recorded sample
    assert segs[-1].end_us == 1_000_000
    assert abs(pr.recorded_fraction(_mixed_cont()) - 0.075) < 1e-9


def test_camera_eligibility_is_derived_and_refuses_ambiguous():
    from dataclasses import replace
    good = pr.camera_eligibility(_mixed_cont())
    assert good.projectile_path_available and good.eligible
    assert good.reconstruction_class == dt.PHYSICS_RECONSTRUCTED
    assert abs(good.recorded_fraction - 0.075) < 1e-9
    assert "8% recorded" in good.reason
    bad = pr.camera_eligibility(replace(_mixed_cont(), confidence=pr.AMBIGUOUS))
    assert bad.projectile_path_available and not bad.eligible
    assert pr.camera_eligibility(None).projectile_path_available is False
