"""REAL_ACTION_TRACE_PROOF_01 — a real jump-pad rocket kill, reproduced.

THE ACTION (campgrounds, demo 4db16c445bcaafce, client 5, serverTime
1198725): the player runs onto a jump pad, launches at 990 u/s vertical, is
airborne for 2.85 s, fires a rocket 675 ms into the flight while his legs are
in LEGS_JUMP, and the obituary lands 675 ms later on client 1. Every number
above was read off the demo; none was typed.

WHAT THIS PROVES. perform(trace) compiles the shooter, the victim and the
missile back into a synthetic demo on the same map at the same world
positions, and the synthetic demo parses back to the same tracks. The
differential below is the evidence, per track.

HEADLESS FIRST (Rule HL-3): extract -> compile -> compare runs in seconds and
renders nothing. The visual A/B is a separate step gated on this passing.

    python -m engine.pantheon.real_action_proof
"""
from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path

from engine.parser.demo_parse import DM73Parser
from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.performance import (PerformanceTrace, _parse_with_anims,
                                         extract_performance)
from engine.pantheon.scenario import RoundScenario, Team

INDEX_DB = Path("G:/QUAKE_LEGACY/creative_suite/database/performance_index.db")
DEMO_HASH = "4db16c445bcaafce"
SHOOTER, VICTIM = 5, 1
PAD_MS = 1198725
PRE_MS, POST_MS = 1500, 2800
T0 = 0.6                        # synthetic seconds before the window opens
OUT = Path(".tmp/synthetic")
SCENE_ID = "REAL_ACTION_TRACE_PROOF_01"

TOL = {"position_u": 1.0, "yaw_deg": 0.5, "pitch_deg": 0.5,
       "velocity_u": 1.0, "time_ms": 0}


def source_path() -> Path:
    con = sqlite3.connect(f"file:{INDEX_DB.as_posix()}?mode=ro", uri=True)
    (p,) = con.execute("select path from demos where demo_hash=?",
                       (DEMO_HASH,)).fetchone()
    con.close()
    return Path(p)


def build():
    demo = source_path()
    parsed = _parse_with_anims(demo)
    out, _ = parsed
    lo, hi = PAD_MS - PRE_MS, PAD_MS + POST_MS
    shooter = extract_performance(demo, lo, hi, SHOOTER, parsed=parsed)
    victim = extract_performance(demo, lo, hi, VICTIM, parsed=parsed)
    shooter.save(OUT / f"{SCENE_ID}.shooter.trace.json")
    victim.save(OUT / f"{SCENE_ID}.victim.trace.json")

    # EXACT_WORLD: same map, same coordinates, same timing.
    scn = RoundScenario.clan_arena(map_name=shooter.map, hostname="PANTHEON REAL ACTION")
    s0 = shooter.transform[0].origin
    scn.observer((s0[0] - 260, s0[1] - 260, s0[2] + 60),
                 yaw=math.degrees(math.atan2(260, 260)) % 360, team=Team.BLUE,
                 name="POV")
    a = scn.actor("SHOOTER", Team.RED).appearance("sarge", "default")
    a.perform(shooter, t0=T0)
    v = scn.actor("VICTIM", Team.BLUE).appearance("visor", "default")
    v.perform(victim, t0=T0)
    ob = [e for e in out["events"] if e["type"] == "obituary"
          and e.get("killer_client") == SHOOTER and lo <= e["server_time_ms"] <= hi]
    if ob:
        from engine.pantheon.scenario import Weapon
        a.kill(v, mod=Weapon.ROCKET, t=T0 + (ob[0]["server_time_ms"] - lo) / 1000.0)

    duration = T0 + (hi - lo) / 1000.0 + 0.3
    OUT.mkdir(parents=True, exist_ok=True)
    synth = scn.compile(duration=duration).save(OUT / f"{SCENE_ID}.dm_73")
    FrameTruth.from_scenario(scn, duration=duration).save(
        OUT / f"{SCENE_ID}.frametruth.json")
    return demo, shooter, victim, scn, a, v, synth, out, ob


def differential(shooter: PerformanceTrace, victim: PerformanceTrace,
                 synth: Path, a_client: int, v_client: int, ob: list) -> dict:
    """Real trace vs the synthetic demo parsed back, per track."""
    back = DM73Parser(synth, track_missiles=True).parse()
    rows = {c: {} for c in (a_client, v_client)}
    for e in back["entities"]:
        if e["client_num"] in rows:
            rows[e["client_num"]][e["server_time_ms"]] = e
    anims = {}
    # re-read anims from the synthetic demo the same way the extractor does
    from engine.pantheon.performance import _parse_with_anims as _pwa
    _, synth_anims = _pwa(synth)
    for x in synth_anims:
        anims[(x["client"], x["t"])] = x

    def track(tr: PerformanceTrace, client: int) -> dict:
        base = 1000 + int(T0 * 1000)
        pos, vel, yaw, pitch, anim_mm, matched = [], [], [], [], 0, 0
        aim_by_t = {x.t: x for x in tr.aim}
        an_by_t = {x.t: x for x in tr.animation}
        # observation gaps: stretches where the recorder had no sample of this
        # player. The synthetic holds the last known state there, and nothing
        # about it is compared, because there is nothing to compare against.
        ts_list = [x.t for x in tr.transform]
        gaps = [(a - tr.start_ms, b - tr.start_ms) for a, b in zip(ts_list, ts_list[1:])
                if b - a > 50]
        for s in tr.transform:
            am, an = aim_by_t.get(s.t), an_by_t.get(s.t)
            ts = base + (s.t - tr.start_ms)
            e = rows[client].get(ts)
            if e is None or am is None:
                continue
            matched += 1
            pos.append(math.dist(s.origin, (e["origin_x"], e["origin_y"], e["origin_z"])))
            vel.append(math.dist(s.velocity, (e["vel_x"] or 0, e["vel_y"] or 0, e["vel_z"] or 0)))
            yaw.append(abs(((e["angle_yaw"] or 0.0) - am.yaw + 180) % 360 - 180))
            pitch.append(abs((e["angle_pitch"] or 0.0) - am.pitch))
            sa = anims.get((client, ts))
            if an is not None and (sa is None or sa["legs"] != an.legs
                                   or sa["torso"] != an.torso):
                anim_mm += 1
        n = len(tr.transform)
        d = {"samples_real": n, "samples_matched": matched,
             "position_max_u": round(max(pos), 3) if pos else None,
             "velocity_max_u": round(max(vel), 3) if vel else None,
             "yaw_max_deg": round(max(yaw), 3) if yaw else None,
             "pitch_max_deg": round(max(pitch), 3) if pitch else None,
             "animation_mismatches": anim_mm,
             "unobserved_gaps_ms": gaps}
        ok = (matched == n and (d["position_max_u"] or 0) <= TOL["position_u"]
              and (d["yaw_max_deg"] or 0) <= TOL["yaw_deg"]
              and (d["pitch_max_deg"] or 0) <= TOL["pitch_deg"]
              and (d["velocity_max_u"] or 0) <= TOL["velocity_u"] and anim_mm == 0)
        d["verdict"] = "MATCHED" if ok else "TOLERANCE_DIFFERENCE"
        return d

    # projectiles: every real sample must come back at the same time/place
    real_pj = {(p.t - shooter.start_ms): p for p in shooter.projectiles}
    synth_pj = {}
    for m in back["missiles"]:
        synth_pj.setdefault(m["server_time_ms"] - 1000 - int(T0 * 1000), m)
    pj_err = []
    for dt, p in real_pj.items():
        m = synth_pj.get(dt)
        if m is None:
            continue
        pj_err.append(math.dist(p.origin, (m["origin_x"], m["origin_y"], m["origin_z"])))
    pj = {"samples_real": len(real_pj), "samples_matched": len(pj_err),
          "position_max_u": round(max(pj_err), 3) if pj_err else None,
          "verdict": ("MATCHED" if pj_err and len(pj_err) == len(real_pj)
                      and max(pj_err) <= TOL["position_u"] else
                      "MISSING" if not pj_err else "TOLERANCE_DIFFERENCE")}

    # events: fire, jump pad, obituary
    real_ev = sorted((e.t - shooter.start_ms, e.kind) for e in shooter.events
                     if e.kind in ("fire_weapon", "jump_pad"))
    synth_ob = [e for e in back["events"] if e["type"] == "obituary"]
    ev = {"real_fire_and_pad": real_ev,
          "synthetic_obituary": [(e["server_time_ms"] - 1000 - int(T0 * 1000),
                                  e.get("weapon_name"), e.get("victim_client"))
                                 for e in synth_ob],
          "real_obituary": [(o["server_time_ms"] - shooter.start_ms,
                             o.get("weapon_name"), o.get("victim_client")) for o in ob],
          "verdict": "INTENTIONAL_DIFFERENCE"}
    ev["note"] = ("fire_weapon and jump_pad are EVENTS on the player entity; the "
                  "compiler does not yet emit them, so the synthetic demo carries "
                  "the ANIMATION and the MISSILE of the shot but not the event "
                  "codes. The obituary is authored from the real one.")
    return {"shooter": track(shooter, a_client), "victim": track(victim, v_client),
            "projectiles": pj, "events": ev,
            "packet_errors": back["packet_errors"], "tolerances": TOL}


def main() -> int:
    demo, shooter, victim, scn, a, v, synth, out, ob = build()
    diff = differential(shooter, victim, synth, a.client, v.client, ob)
    report = {
        "scene_id": SCENE_ID, "demo_hash": DEMO_HASH, "map": shooter.map,
        "server_time_range_ms": [shooter.start_ms, shooter.end_ms],
        "shooter_client": SHOOTER, "victim_client": VICTIM, "pov": shooter.pov,
        "jump_pad_ms": PAD_MS,
        "speed": shooter.speed_profile(),
        "anim_sequence": shooter.anim_sequence(),
        "rocket_fires_ms_rel_pad": [e.t - PAD_MS for e in shooter.events
                                    if e.kind == "fire_weapon" and e.weapon == 5],
        "obituary": [(o["server_time_ms"] - PAD_MS, o.get("weapon_name"),
                      o.get("victim_client")) for o in ob],
        "max_yaw_rate": max(abs(x.yaw_rate) for x in shooter.aim),
        "projectile_samples": len(shooter.projectiles),
        "retarget": "EXACT_WORLD",
        "synthetic_demo": str(synth),
        "differential": diff,
    }
    (OUT / f"{SCENE_ID}.report.json").write_text(json.dumps(report, indent=1))
    print(f"real   : {shooter.map} client {SHOOTER} -> {VICTIM}, "
          f"{shooter.duration_ms()}ms, {len(shooter.transform)} samples, "
          f"airborne {shooter.speed_profile()['airborne_ms']}ms, "
          f"rocket at {report['rocket_fires_ms_rel_pad']} ms after pad, "
          f"kill at {report['obituary']}")
    print(f"synth  : {synth} ({synth.stat().st_size:,} bytes)  packet_errors="
          f"{diff['packet_errors']}")
    for k in ("shooter", "victim", "projectiles"):
        print(f"  {k:12s} {diff[k]}")
    print(f"  events       {diff['events']['verdict']}: {diff['events']['note'][:90]}...")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
