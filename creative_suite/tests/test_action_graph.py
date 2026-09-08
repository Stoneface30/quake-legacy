"""ActionGraph: the sentence read off a PerformanceTrace, with evidence."""
from __future__ import annotations

from creative_suite.tests.pantheon_fixtures import (STEP, START, jumppad_rocket_trace,
                                                     victim_trace)
from engine.pantheon import action_graph as AG
from engine.pantheon.performance import (ActionEvent, PerformanceTrace,
                                         ProjectileSample, TransformSample)


def test_the_jump_pad_rocket_reads_as_the_sentence_it_is():
    g = AG.build(jumppad_rocket_trace())
    kinds = {n.kind for n in g.nodes}
    assert {"RUN", "JUMP_PAD", "AIRBORNE", "LAND", "FLICK", "FIRE", "PROJECTILE",
            "IMPACT", "KILL"} <= kinds
    chains = g.chain("JUMP_PAD", "AIRBORNE", "FIRE")
    assert chains, [ (e.src, e.relation, e.dst) for e in g.edges if e.relation != "then"]
    assert g.chain("FIRE", "PROJECTILE", "IMPACT", "KILL")
    assert g.sentence().startswith("JUMP_PAD -> AIRBORNE -> FIRE -> PROJECTILE -> IMPACT -> KILL") \
        or g.sentence() == "FLICK -> FIRE -> PROJECTILE -> IMPACT -> KILL"


def test_every_node_cites_its_evidence():
    g = AG.build(jumppad_rocket_trace())
    for n in g.nodes:
        assert n.evidence, n.kind
        assert all(e.kind in ("OBSERVED_EVENT", "STATE_TRANSITION", "DERIVED") for e in n.evidence)
    pad = g.of_kind("JUMP_PAD")[0]
    assert {e.kind for e in pad.evidence} == {"OBSERVED_EVENT", "STATE_TRANSITION"}
    assert all(e.basis in ("OBSERVED_EVENT", "STATE_TRANSITION", "DERIVED") for e in g.edges)


def test_a_jump_pad_event_without_a_launch_is_rejected_not_believed():
    tr = jumppad_rocket_trace()
    for s in tr.transform:
        s.velocity = (s.velocity[0], s.velocity[1], 0.0)     # the body never launched
    g = AG.build(tr)
    assert not g.of_kind("JUMP_PAD")
    assert g.rejected and g.rejected[0]["event"] == "jump_pad"
    assert "JUMP_PAD" not in AG.categories(g)


def test_teleport_needs_a_discontinuity():
    tr = victim_trace(gap=(0, 0))
    t = START + STEP * 30
    tr.events.append(ActionEvent(t, "teleport_in", None, tr.transform[30].origin, None, None))
    assert not AG.build(tr).of_kind("TELEPORT")
    for s in tr.transform[30:]:
        s.origin = (s.origin[0] + 1500.0, s.origin[1], s.origin[2])
    g = AG.build(tr)
    tele = g.of_kind("TELEPORT")
    assert tele and tele[0].evidence[1].detail["distance"] > AG.TELEPORT_JUMP_U


def test_categories_come_from_structure():
    g = AG.build(jumppad_rocket_trace())
    cats = AG.categories(g)
    assert {"JUMP_PAD", "JUMP_PAD_ROCKET", "JUMP_PAD_KILL", "ROCKET_AIR_ACTION",
            "TURN_AND_FIRE"} <= cats
    assert cats <= set(AG.CATEGORIES)


def test_projectile_tracks_carry_spawn_flight_bounce_and_lifetime():
    tr = PerformanceTrace("f", "campgrounds", "CA", 5, START, START + 1000)
    for i in range(20):
        t = START + STEP * i
        vz = -300.0 if i < 8 else 250.0                      # a grenade bouncing at i=8
        tr.projectiles.append(ProjectileSample(t, 300, 4, (10.0 * i, 0.0, 100.0 - 5 * i),
                                               (700.0, 0.0, vz)))
    (pt,) = AG.projectile_tracks(tr)
    assert pt.weapon == 4 and pt.lifetime_ms == STEP * 19
    assert pt.bounces() == [START + STEP * 8]
    assert abs(pt.speed() - (700 ** 2 + 300 ** 2) ** 0.5) < 1e-6


def test_rail_is_fire_plus_trail_and_lightning_is_a_span():
    tr = victim_trace(gap=(0, 0))
    t = START + STEP * 10
    tr.events += [ActionEvent(t, "fire_weapon", 7, tr.transform[10].origin, None, None),
                  ActionEvent(t, "railtrail", 7, (2000.0, 40.0, 60.0), None, 255)]
    for i in range(20, 30):
        tr.events.append(ActionEvent(START + STEP * i, "fire_weapon", 6,
                                     tr.transform[i].origin, None, None))
    g = AG.build(tr)
    assert not g.of_kind("PROJECTILE")
    assert g.chain("FIRE", "RAIL_TRAIL")
    lg = g.of_kind("LG_ATTACK")
    assert len(lg) == 1 and lg[0].attrs["shots"] == 10 and lg[0].duration_ms == STEP * 9


def test_cross_actor_pain_becomes_hit_evidence_and_saves():
    shooter, victim = jumppad_rocket_trace(), victim_trace()
    g = AG.build(shooter, others=[victim])
    assert g.of_kind("HIT_EVIDENCE")
    assert any(e.relation == "evidenced_by" for e in g.edges)
    d = g.as_dict()
    assert d["sentence"] and "categories" in d and d["rejected"] == []
