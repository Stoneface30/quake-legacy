"""ActionGraph — the smallest semantic reading of a PerformanceTrace.

A PerformanceTrace is continuous state: positions, angles, animation numbers,
missile samples, server events, all on serverTime. "He takes the jump pad and
hits a sick rocket" is a SENTENCE about that state:

    JUMP_PAD -> AIRBORNE -> FLICK -> FIRE(ROCKET) -> PROJECTILE -> IMPACT -> KILL

This module produces that sentence, and nothing more abstract. Every node and
every edge carries EVIDENCE that names where it came from:

    OBSERVED_EVENT     the server said so (an EV_* in the demo)
    STATE_TRANSITION   two consecutive samples changed state (airborne ->
                       grounded, weapon 5 -> 7, a position discontinuity)
    DERIVED            a relation PANTHEON computed from the above, stated as
                       such (this fire produced that missile; this impact
                       preceded that obituary)

NO NODE FROM A LABEL ALONE. An event that the transform contradicts is not an
action: a jump_pad event without a launch is recorded under `rejected`, with
the reason, and never becomes a node. The same principle applies wherever
the trace can corroborate an event: TELEPORT needs a discontinuity, LAND
needs airborne -> grounded, JUMP needs to leave the ground.

WEAPONS ON THEIR OWN TERMS. Rockets, grenades and plasma are missile
entities and get PROJECTILE nodes with spawn, flight, bounces and impact.
Rail is instantaneous: FIRE + RAIL_TRAIL (geometry from the trail event) +
hit evidence, never a fake missile. Lightning is continuous: LG_ATTACK spans
built from the run of fire events, with the view relation, never a
trajectory.

Machine interpretation (tiering, style, mood) lives elsewhere; this graph is
the evidence layer it must cite.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Sequence

from engine.pantheon.performance import PerformanceTrace, ProjectileSample

Vec3 = tuple[float, float, float]

# ── thresholds, in the game's own units ─────────────────────────────────────
LAUNCH_VZ = 200.0            # a jump pad throws you at least this fast (index rule)
LAUNCH_WINDOW_MS = 150
JUMP_VZ = 150.0
TELEPORT_JUMP_U = 300.0      # a body does not move this far in one snapshot
RUN_SPEED = 50.0
FLICK_RATE_DPS = 360.0       # peak yaw rate that reads as a flick
FLICK_MIN_DEG = 30.0
FLICK_MAX_MS = 250
TURN_MIN_DEG = 45.0
TURN_MAX_MS = 600
ACCEL_MIN_UPS = 150.0        # speed gained over the accel window
ACCEL_WINDOW_MS = 300
FIRE_TO_SPAWN_MS = 60
IMPACT_AFTER_LAST_SAMPLE_MS = 100
IMPACT_TO_KILL_MS = 150
LG_FIRE_GAP_MS = 120         # LG fires every 50ms; a wider gap ends the attack
WEAPON_KIND = {4: "GRENADE", 5: "ROCKET", 8: "PLASMA", 7: "RAIL", 6: "LIGHTNING",
               1: "GAUNTLET", 2: "MACHINEGUN", 3: "SHOTGUN"}
MISSILE_WEAPONS = {4, 5, 8}


@dataclass
class Evidence:
    kind: str                   # OBSERVED_EVENT | STATE_TRANSITION | DERIVED
    t: int                      # serverTime ms
    ref: str                    # e.g. "event:jump_pad", "transform:airborne->grounded"
    detail: dict = field(default_factory=dict)


@dataclass
class ActionNode:
    id: str
    kind: str
    t_start: int
    t_end: int
    evidence: list[Evidence] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        return self.t_end - self.t_start

    def as_dict(self) -> dict:
        d = asdict(self)
        d["attrs"] = {k: v for k, v in d["attrs"].items() if not k.startswith("_")}
        d["duration_ms"] = self.duration_ms
        return d


@dataclass
class ActionEdge:
    src: str
    dst: str
    relation: str               # then | launches | fires | lands_as | flies_to | causes | evidenced_by
    basis: str                  # OBSERVED_EVENT | STATE_TRANSITION | DERIVED
    detail: dict = field(default_factory=dict)


@dataclass
class ActionGraph:
    demo_hash: str
    client: int
    map: str
    start_ms: int
    end_ms: int
    nodes: list[ActionNode] = field(default_factory=list)
    edges: list[ActionEdge] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)

    # -- queries -------------------------------------------------------
    def of_kind(self, kind: str) -> list[ActionNode]:
        return [n for n in self.nodes if n.kind == kind]

    def node(self, node_id: str) -> ActionNode:
        for n in self.nodes:
            if n.id == node_id:
                return n
        raise KeyError(node_id)

    def successors(self, node_id: str, relation: str | None = None) -> list[ActionNode]:
        return [self.node(e.dst) for e in self.edges
                if e.src == node_id and (relation is None or e.relation == relation)]

    def chain(self, *kinds: str) -> list[list[ActionNode]]:
        """Every path whose node kinds are exactly `kinds`, in order, joined
        by causal (non-`then`) edges."""
        out: list[list[ActionNode]] = []

        def walk(path: list[ActionNode]):
            if len(path) == len(kinds):
                out.append(path)
                return
            for e in self.edges:
                if e.src == path[-1].id and e.relation != "then":
                    n = self.node(e.dst)
                    if n.kind == kinds[len(path)]:
                        walk(path + [n])

        for n in self.of_kind(kinds[0]):
            walk([n])
        return out

    def sentence(self) -> str:
        """The causal spine, as words: what a director would say happened."""
        causal = [e for e in self.edges if e.relation != "then"]
        if not causal:
            return " -> ".join(n.kind for n in sorted(self.nodes, key=lambda n: n.t_start)[:6])
        starts = {e.src for e in causal} - {e.dst for e in causal}
        best: list[str] = []

        def longest(cur: str, seen: frozenset) -> list[str]:
            paths = [longest(e.dst, seen | {e.dst}) for e in causal
                     if e.src == cur and e.dst not in seen]
            tail = max(paths, key=len) if paths else []
            return [cur] + tail

        for s in sorted(starts, key=lambda i: self.node(i).t_start):
            path = longest(s, frozenset({s}))
            if len(path) > len(best):
                best = path
        return " -> ".join(self.node(i).kind for i in best)

    def as_dict(self) -> dict:
        return {"demo_hash": self.demo_hash, "client": self.client, "map": self.map,
                "start_ms": self.start_ms, "end_ms": self.end_ms,
                "sentence": self.sentence(),
                "categories": sorted(categories(self)),
                "nodes": [n.as_dict() for n in self.nodes],
                "edges": [asdict(e) for e in self.edges],
                "rejected": self.rejected}

    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.as_dict(), indent=1), encoding="utf-8")
        return path


# ── projectile tracks ──────────────────────────────────────────────────────

@dataclass
class ProjectileTrack:
    """One missile entity's observed life, in order."""
    entity: int
    weapon: int
    samples: list[ProjectileSample]

    @property
    def spawn(self) -> ProjectileSample:
        return self.samples[0]

    @property
    def last(self) -> ProjectileSample:
        return self.samples[-1]

    @property
    def lifetime_ms(self) -> int:
        return self.last.t - self.spawn.t

    def speed(self) -> float:
        v = self.spawn.velocity
        return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)

    def bounces(self) -> list[int]:
        """Times where the velocity reversed on an axis: a grenade hitting
        the world. Measured on the samples, never assumed from the weapon."""
        out = []
        for a, b in zip(self.samples, self.samples[1:]):
            for i in range(3):
                if a.velocity[i] * b.velocity[i] < 0 and abs(a.velocity[i] - b.velocity[i]) > 100:
                    out.append(b.t)
                    break
        return out

    def path(self) -> list[Vec3]:
        return [s.origin for s in self.samples]


def projectile_tracks(trace: PerformanceTrace) -> list[ProjectileTrack]:
    by_entity: dict[int, list[ProjectileSample]] = {}
    for p in trace.projectiles:
        by_entity.setdefault(p.entity, []).append(p)
    out = []
    for ent, samples in by_entity.items():
        samples.sort(key=lambda s: s.t)
        # one entity slot can be reused for a later missile. A sampling gap
        # alone is not a new missile (the recorder loses sight of a rocket
        # like it loses sight of a player); a new missile is one whose next
        # sample is NOT where the flight would have carried the old one.
        run: list[ProjectileSample] = []
        for s in samples:
            if run:
                prev = run[-1]
                dt = (s.t - prev.t) / 1000.0
                v = prev.velocity
                expected = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) * dt
                actual = math.dist(prev.origin, s.origin)
                if s.weapon != prev.weapon or actual > expected * 1.5 + 64.0                         or (dt > 0.2 and actual < expected * 0.5):
                    out.append(ProjectileTrack(ent, run[0].weapon, run))
                    run = []
            run.append(s)
        if run:
            out.append(ProjectileTrack(ent, run[0].weapon, run))
    return sorted(out, key=lambda tr: tr.spawn.t)


# ── the builder ────────────────────────────────────────────────────────────

def build(trace: PerformanceTrace, *, others: Sequence[PerformanceTrace] = ()
          ) -> ActionGraph:
    """Read the sentence off the trace. `others` are traces of other players
    in the same window, used only for cross-actor evidence (their pain at
    an impact, their death at an obituary)."""
    g = ActionGraph(trace.demo_hash, trace.client, trace.map,
                    trace.start_ms, trace.end_ms)
    n_id = [0]

    def add(kind: str, t0: int, t1: int, ev: list[Evidence], **attrs) -> ActionNode:
        n_id[0] += 1
        node = ActionNode(f"{kind.lower()}_{n_id[0]}", kind, t0, t1, ev, attrs)
        g.nodes.append(node)
        return node

    def link(a: ActionNode, b: ActionNode, relation: str, basis: str, **detail):
        g.edges.append(ActionEdge(a.id, b.id, relation, basis, detail))

    tf = trace.transform
    by_t = {s.t: s for s in tf}

    def sample_near(t: int, window: int = LAUNCH_WINDOW_MS):
        return [s for s in tf if abs(s.t - t) <= window]

    # -- movement spans from the transform ------------------------------
    airborne_nodes: list[ActionNode] = []
    run_nodes: list[ActionNode] = []
    i = 0
    while i < len(tf):
        s = tf[i]
        j = i
        while j + 1 < len(tf) and tf[j + 1].airborne == s.airborne and tf[j + 1].t - tf[j].t <= 50:
            j += 1
        if s.airborne:
            node = add("AIRBORNE", s.t, tf[j].t,
                       [Evidence("STATE_TRANSITION", s.t, "transform:airborne",
                                 {"samples": j - i + 1})],
                       apex_z=max(x.origin[2] for x in tf[i:j + 1]),
                       apex_t=max(tf[i:j + 1], key=lambda x: x.origin[2]).t)
            airborne_nodes.append(node)
            if j + 1 < len(tf) and not tf[j + 1].airborne:
                land = add("LAND", tf[j + 1].t, tf[j + 1].t,
                           [Evidence("STATE_TRANSITION", tf[j + 1].t,
                                     "transform:airborne->grounded",
                                     {"z": tf[j + 1].origin[2]})],
                           position=tf[j + 1].origin)
                link(node, land, "lands_as", "STATE_TRANSITION")
        else:
            moving = [x for x in tf[i:j + 1] if x.speed > RUN_SPEED]
            if len(moving) >= 2:
                node = add("RUN", moving[0].t, moving[-1].t,
                           [Evidence("STATE_TRANSITION", moving[0].t,
                                     "transform:speed>run", {"samples": len(moving)})],
                           max_speed=round(max(x.speed for x in moving), 1),
                           mean_speed=round(sum(x.speed for x in moving) / len(moving), 1))
                run_nodes.append(node)
        i = j + 1

    # -- ACCELERATE: speed gained over a short window --------------------
    for a in tf:
        later = [b for b in tf if 0 < b.t - a.t <= ACCEL_WINDOW_MS]
        if later and max(b.speed for b in later) - a.speed >= ACCEL_MIN_UPS and a.speed < RUN_SPEED * 3:
            b = max(later, key=lambda x: x.speed)
            add("ACCELERATE", a.t, b.t,
                [Evidence("STATE_TRANSITION", a.t, "transform:speed_gain",
                          {"from": round(a.speed, 1), "to": round(b.speed, 1)})])
            break            # one per trace is the useful reading

    # -- aim: FLICK and TURN from the yaw series --------------------------
    aim = trace.aim
    k = 0
    while k < len(aim):
        if abs(aim[k].yaw_rate) >= FLICK_RATE_DPS:
            m = k
            while m + 1 < len(aim) and abs(aim[m + 1].yaw_rate) >= FLICK_RATE_DPS / 2:
                m += 1
            start = aim[max(0, k - 1)]
            disp = abs((aim[m].yaw - start.yaw + 180) % 360 - 180)
            span = aim[m].t - start.t
            if disp >= FLICK_MIN_DEG and span <= FLICK_MAX_MS:
                add("FLICK", start.t, aim[m].t,
                    [Evidence("STATE_TRANSITION", start.t, "aim:yaw_rate_peak",
                              {"peak_dps": round(max(abs(x.yaw_rate) for x in aim[k:m + 1]), 1)})],
                    degrees=round(disp, 1), peak_dps=round(max(abs(x.yaw_rate) for x in aim[k:m + 1]), 1),
                    pitch_delta=round(aim[m].pitch - start.pitch, 1))
            k = m + 1
        else:
            k += 1
    # TURN: a sustained heading change that was not a flick
    flick_spans = [(n.t_start, n.t_end) for n in g.of_kind("FLICK")]
    for a in aim:
        if any(s <= a.t <= e for s, e in flick_spans):
            continue
        later = [b for b in aim if 0 < b.t - a.t <= TURN_MAX_MS
                 and not any(s <= b.t <= e for s, e in flick_spans)]
        if not later:
            continue
        b = max(later, key=lambda x: abs((x.yaw - a.yaw + 180) % 360 - 180))
        disp = abs((b.yaw - a.yaw + 180) % 360 - 180)
        if disp >= TURN_MIN_DEG:
            add("TURN", a.t, b.t,
                [Evidence("STATE_TRANSITION", a.t, "aim:heading_change",
                          {"from": round(a.yaw, 1), "to": round(b.yaw, 1)})],
                degrees=round(disp, 1))
            break

    # -- weapon switches -------------------------------------------------
    for w0, w1 in zip(trace.weapon, trace.weapon[1:]):
        add("WEAPON_SWITCH", w1.t, w1.t,
            [Evidence("STATE_TRANSITION", w1.t, "weapon:change",
                      {"from": w0.weapon, "to": w1.weapon})],
            from_weapon=WEAPON_KIND.get(w0.weapon, w0.weapon),
            to_weapon=WEAPON_KIND.get(w1.weapon, w1.weapon))

    # -- events with transform validation ---------------------------------
    pads: list[ActionNode] = []
    for ev in trace.of_kind("jump_pad"):
        launch = [s for s in sample_near(ev.t) if s.velocity[2] > LAUNCH_VZ]
        if not launch:
            g.rejected.append({"event": "jump_pad", "t": ev.t,
                               "reason": f"no launch: vel_z never exceeded {LAUNCH_VZ} "
                                         f"within {LAUNCH_WINDOW_MS}ms of the event"})
            continue
        node = add("JUMP_PAD", ev.t, ev.t,
                   [Evidence("OBSERVED_EVENT", ev.t, "event:jump_pad"),
                    Evidence("STATE_TRANSITION", launch[0].t, "transform:launch",
                             {"vel_z": launch[0].velocity[2]})],
                   position=ev.position, launch_vz=launch[0].velocity[2])
        pads.append(node)
        air = [a for a in airborne_nodes if a.t_start - 100 <= ev.t <= a.t_end]
        if air:
            link(node, air[0], "launches", "STATE_TRANSITION",
                 airborne_ms=air[0].duration_ms)

    for ev in trace.of_kind("jump"):
        leave = [s for s in sample_near(ev.t, 100) if s.airborne or s.velocity[2] > JUMP_VZ]
        if not leave:
            g.rejected.append({"event": "jump", "t": ev.t,
                               "reason": "the body never left the ground"})
            continue
        node = add("JUMP", ev.t, ev.t,
                   [Evidence("OBSERVED_EVENT", ev.t, "event:jump"),
                    Evidence("STATE_TRANSITION", leave[0].t, "transform:leaves_ground")])
        air = [a for a in airborne_nodes if a.t_start - 100 <= ev.t <= a.t_end]
        if air:
            link(node, air[0], "launches", "STATE_TRANSITION")

    tele_events = trace.of_kind("teleport_in") + trace.of_kind("teleport_out")
    for ev in sorted(tele_events, key=lambda e: e.t):
        jump = None
        for a, b in zip(tf, tf[1:]):
            if abs(b.t - ev.t) <= 100 or abs(a.t - ev.t) <= 100:
                if math.dist(a.origin, b.origin) > TELEPORT_JUMP_U:
                    jump = (a, b)
                    break
        if jump is None:
            g.rejected.append({"event": ev.kind, "t": ev.t,
                               "reason": "no position discontinuity near the event"})
            continue
        if ev.kind == "teleport_out" and any(n.kind == "TELEPORT" and abs(n.t_start - ev.t) <= 100
                                             for n in g.nodes):
            continue                              # the pair is one action
        add("TELEPORT", jump[0].t, jump[1].t,
            [Evidence("OBSERVED_EVENT", ev.t, f"event:{ev.kind}"),
             Evidence("STATE_TRANSITION", jump[1].t, "transform:discontinuity",
                      {"distance": round(math.dist(jump[0].origin, jump[1].origin), 1)})],
            from_position=jump[0].origin, to_position=jump[1].origin)

    # -- fire, by weapon family --------------------------------------------
    fires = sorted(trace.of_kind("fire_weapon"), key=lambda e: e.t)
    fire_nodes: list[ActionNode] = []
    lg_run: list = []

    def flush_lg():
        if lg_run:
            node = add("LG_ATTACK", lg_run[0].t, lg_run[-1].t,
                       [Evidence("OBSERVED_EVENT", e.t, "event:fire_weapon") for e in lg_run],
                       shots=len(lg_run),
                       view_yaw_range=_yaw_range(aim, lg_run[0].t, lg_run[-1].t))
            fire_nodes.append(node)
            lg_run.clear()

    for ev in fires:
        if ev.weapon == 6:
            if lg_run and ev.t - lg_run[-1].t > LG_FIRE_GAP_MS:
                flush_lg()
            lg_run.append(ev)
            continue
        flush_lg()
        node = add("FIRE", ev.t, ev.t,
                   [Evidence("OBSERVED_EVENT", ev.t, "event:fire_weapon", {"weapon": ev.weapon})],
                   weapon=WEAPON_KIND.get(ev.weapon, ev.weapon), weapon_num=ev.weapon,
                   position=ev.position,
                   airborne=(by_t.get(ev.t).airborne if by_t.get(ev.t) else None))
        fire_nodes.append(node)
        air = [a for a in airborne_nodes if a.t_start <= ev.t <= a.t_end]
        if air:
            link(air[0], node, "fires", "STATE_TRANSITION", airborne=True)
        fl = [f for f in g.of_kind("FLICK") if 0 <= ev.t - f.t_end <= 300 or f.t_start <= ev.t <= f.t_end]
        if fl:
            link(fl[-1], node, "fires", "DERIVED", flick_to_fire_ms=ev.t - fl[-1].t_end)
    flush_lg()

    # -- rail: trail geometry, not a missile --------------------------------
    for trail in trace.of_kind("railtrail"):
        f = [n for n in fire_nodes if n.kind == "FIRE" and n.attrs.get("weapon_num") == 7
             and abs(n.t_start - trail.t) <= 50]
        node = add("RAIL_TRAIL", trail.t, trail.t,
                   [Evidence("OBSERVED_EVENT", trail.t, "event:railtrail")],
                   end=trail.position)
        if f:
            link(f[0], node, "traces", "OBSERVED_EVENT")

    # -- projectiles ---------------------------------------------------------
    impacts = sorted(trace.of_kind("missile_hit") + trace.of_kind("missile_miss"),
                     key=lambda e: e.t)
    impact_nodes: dict[int, ActionNode] = {}
    for ev in impacts:
        node = add("IMPACT", ev.t, ev.t,
                   [Evidence("OBSERVED_EVENT", ev.t, f"event:{ev.kind}", {"weapon": ev.weapon})],
                   hit_player=(ev.kind == "missile_hit"), weapon=WEAPON_KIND.get(ev.weapon, ev.weapon),
                   position=ev.position)
        impact_nodes[ev.t] = node

    for pt in projectile_tracks(trace):
        node = add("PROJECTILE", pt.spawn.t, pt.last.t,
                   [Evidence("OBSERVED_EVENT", pt.spawn.t, "missile:entity",
                             {"entity": pt.entity, "samples": len(pt.samples)})],
                   weapon=WEAPON_KIND.get(pt.weapon, pt.weapon), weapon_num=pt.weapon,
                   spawn=pt.spawn.origin, spawn_velocity=pt.spawn.velocity,
                   speed=round(pt.speed(), 1), lifetime_ms=pt.lifetime_ms,
                   bounces=pt.bounces(), path=pt.path())
        f = [n for n in fire_nodes if n.kind == "FIRE" and n.attrs.get("weapon_num") == pt.weapon
             and 0 <= pt.spawn.t - n.t_start <= FIRE_TO_SPAWN_MS]
        if f:
            link(f[-1], node, "spawns", "DERIVED", fire_to_spawn_ms=pt.spawn.t - f[-1].t_start)
        imp = [n for t, n in impact_nodes.items()
               if 0 <= t - pt.last.t <= IMPACT_AFTER_LAST_SAMPLE_MS
               and n.attrs.get("weapon") == node.attrs["weapon"]]
        if imp:
            link(node, imp[0], "flies_to", "DERIVED",
                 last_sample_to_impact_ms=imp[0].t_start - pt.last.t,
                 location_error_u=(round(math.dist(pt.last.origin, imp[0].attrs["position"]), 1)
                                   if imp[0].attrs.get("position") else None))
        node.attrs["_last_t"] = pt.last.t

    # -- kills and deaths -----------------------------------------------------
    for ev in trace.of_kind("obituary"):
        if ev.other_client is not None and ev.other_client != trace.client:
            node = add("KILL", ev.t, ev.t,
                       [Evidence("OBSERVED_EVENT", ev.t, "event:obituary",
                                 {"mod": ev.weapon, "victim": ev.other_client})],
                       victim=ev.other_client, mod=ev.weapon, position=ev.position)
            imp = [n for t, n in impact_nodes.items() if 0 <= ev.t - t <= IMPACT_TO_KILL_MS]
            pj = [n for n in g.of_kind("PROJECTILE")
                  if 0 <= ev.t - n.attrs.get("_last_t", -10**9) <= IMPACT_TO_KILL_MS
                  and _mod_matches(ev.weapon, n.attrs.get("weapon"))]
            if imp:
                link(imp[-1], node, "causes", "DERIVED", impact_to_kill_ms=ev.t - imp[-1].t_start)
            elif pj:
                # the impact event was not observed, but the missile's last
                # sample sits on the obituary: the missile is the cause
                link(pj[-1], node, "causes", "DERIVED",
                     last_sample_to_kill_ms=ev.t - pj[-1].attrs["_last_t"],
                     impact_observed=False)
            else:
                # hitscan or splash without a missile event: the fire is the cause
                f = [n for n in fire_nodes if 0 <= ev.t - n.t_start <= 2500]
                if f:
                    link(f[-1], node, "causes", "DERIVED", fire_to_kill_ms=ev.t - f[-1].t_start)
        else:
            add("DEATH", ev.t, ev.t,
                [Evidence("OBSERVED_EVENT", ev.t, "event:obituary", {"mod": ev.weapon})],
                mod=ev.weapon)
    for ev in trace.of_kind("death"):
        if not g.of_kind("DEATH"):
            add("DEATH", ev.t, ev.t, [Evidence("OBSERVED_EVENT", ev.t, "event:death")])

    # -- cross-actor hit evidence ----------------------------------------------
    for other in others:
        for p in other.of_kind("pain"):
            imp = [n for t, n in impact_nodes.items() if abs(p.t - t) <= 50]
            if imp:
                node = add("HIT_EVIDENCE", p.t, p.t,
                           [Evidence("OBSERVED_EVENT", p.t, "event:pain",
                                     {"client": other.client, "health": p.parm})],
                           client=other.client)
                link(imp[0], node, "evidenced_by", "OBSERVED_EVENT")

    # -- relation to other bodies: APPROACH / WITHDRAW ---------------------------
    # Needs the other players' positions, so only when `others` is given.
    for other in others:
        o_by_t = {s.t: s for s in other.transform}
        dist = [(s.t, math.dist(s.origin, o_by_t[s.t].origin))
                for s in tf if s.t in o_by_t and s.speed > RUN_SPEED]
        if len(dist) < 8:
            continue
        # longest monotone stretch (with slack) of closing / opening distance
        for sign, kind in ((-1, "APPROACH"), (1, "WITHDRAW")):
            best = (0, 0)
            i = 0
            while i < len(dist):
                j = i
                while j + 1 < len(dist) and sign * (dist[j + 1][1] - dist[j][1]) >= -5.0:
                    j += 1
                if dist[j][0] - dist[i][0] > best[1] - best[0]:
                    best = (dist[i][0], dist[j][0])
                i = j + 1
            if kind == "WITHDRAW":
                span = [s for s in tf if best[0] <= s.t <= best[1]]
                grounded = sum(1 for s in span if not s.airborne)
                firing = any(best[0] <= f.t <= best[1] for f in trace.of_kind("fire_weapon"))
                if not span or grounded < 0.7 * len(span) or firing:
                    continue
            if best[1] - best[0] >= 500 and abs(dict(dist)[best[1]] - dict(dist)[best[0]]) >= 150:
                add(kind, best[0], best[1],
                    [Evidence("DERIVED", best[0], "transform:distance_to_other",
                              {"client": other.client,
                               "from_u": round(dict(dist)[best[0]], 1),
                               "to_u": round(dict(dist)[best[1]], 1)})],
                    other_client=other.client)

    # -- chronology --------------------------------------------------------------
    ordered = sorted(g.nodes, key=lambda n: (n.t_start, n.t_end))
    for a, b in zip(ordered, ordered[1:]):
        if a.t_end <= b.t_start:
            link(a, b, "then", "STATE_TRANSITION")
    return g


def _mod_matches(mod: int | None, weapon: str | None) -> bool:
    from engine.parser.demo_parse import _MOD_NAMES
    name = _MOD_NAMES.get(mod or -1, "")
    return bool(weapon) and name.startswith(weapon)


def _yaw_range(aim, t0: int, t1: int) -> float:
    ys = [a.yaw for a in aim if t0 <= a.t <= t1]
    if len(ys) < 2:
        return 0.0
    return round(max(abs((y - ys[0] + 180) % 360 - 180) for y in ys), 1)


# ── semantic categories (a closed list) ────────────────────────────────────

CATEGORIES = ("JUMP_PAD", "JUMP_PAD_KILL", "JUMP_PAD_ROCKET", "ROCKET_AIR_ACTION",
              "RAIL_FLICK", "ROCKET_PREDICTION", "TELEPORT_ATTACK", "COMBAT_STRAFE",
              "RETREAT", "CHASE", "HIGH_SPEED", "TURN_AND_FIRE", "WEAPON_SWITCH_ATTACK")


def categories(g: ActionGraph) -> set[str]:
    """Which of the closed category list this graph belongs to. Every rule
    reads nodes and edges, never a label on its own."""
    out: set[str] = set()
    pads = g.of_kind("JUMP_PAD")
    fires = g.of_kind("FIRE")
    kills = g.of_kind("KILL")
    if pads:
        out.add("JUMP_PAD")
        air = [a for p in pads for a in g.successors(p.id, "launches")]
        air_span = [(a.t_start, a.t_end) for a in air]
        in_air = lambda t: any(s <= t <= e for s, e in air_span)
        if any(f.attrs.get("weapon") == "ROCKET" and in_air(f.t_start) for f in fires):
            out.add("JUMP_PAD_ROCKET")
        if any(in_air(k.t_start) or any(e <= k.t_start <= e + 2500 for _, e in air_span)
               for k in kills):
            out.add("JUMP_PAD_KILL")
    if any(f.attrs.get("weapon") == "ROCKET" and f.attrs.get("airborne") for f in fires):
        out.add("ROCKET_AIR_ACTION")
    if any(e.src.startswith("flick") and g.node(e.dst).attrs.get("weapon") == "RAIL"
           for e in g.edges if e.relation == "fires"):
        out.add("RAIL_FLICK")
    if any(g.node(e.dst).attrs.get("weapon") == "ROCKET"
           for e in g.edges if e.relation == "causes"
           and g.node(e.src).kind == "IMPACT" and not g.node(e.src).attrs.get("hit_player")):
        out.add("ROCKET_PREDICTION")          # a splash kill: the rocket met the floor first
    tele = g.of_kind("TELEPORT")
    if tele and any(0 <= f.t_start - t.t_end <= 1500 for t in tele for f in fires):
        out.add("TELEPORT_ATTACK")
    runs = g.of_kind("RUN")
    if fires and runs and any(r.t_start <= f.t_start <= r.t_end for r in runs for f in fires):
        out.add("COMBAT_STRAFE")
    if any(r.attrs.get("max_speed", 0) >= 600 for r in runs) or \
            any(a.attrs.get("apex_z", 0) - _ground_z(g) > 400 for a in g.of_kind("AIRBORNE")):
        out.add("HIGH_SPEED")
    if any(g.node(e.dst).kind == "FIRE" for e in g.edges
           if e.relation == "fires" and g.node(e.src).kind == "FLICK") or \
            any(0 <= f.t_start - t.t_end <= 400 for t in g.of_kind("TURN") for f in fires):
        out.add("TURN_AND_FIRE")
    if any(0 <= f.t_start - w.t_start <= 500 for w in g.of_kind("WEAPON_SWITCH") for f in fires):
        out.add("WEAPON_SWITCH_ATTACK")
    # CHASE / RETREAT need another body in the window (build(..., others=))
    if any(a.t_start <= f.t_start <= a.t_end + 500 for a in g.of_kind("APPROACH") for f in fires):
        out.add("CHASE")
    if g.of_kind("WITHDRAW"):
        out.add("RETREAT")
    return out


def _ground_z(g: ActionGraph) -> float:
    lands = g.of_kind("LAND")
    if lands:
        return min(n.attrs["position"][2] for n in lands)
    return 0.0
