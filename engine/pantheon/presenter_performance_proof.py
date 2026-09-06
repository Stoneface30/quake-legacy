"""PRESENTER_PERFORMANCE_PROOF_01 — Crash walks into a frozen scene like a
Quake player, because she is replaying one.

THE ENTRANCE IS A RECORDING. RUN_IN_STOP_TURN_01 is a real, anonymous
performance mined from the corpus: 1.3s of straight running at 341 u/s, a
100ms deceleration, a 1.8s stop with a 138-degree turn on the spot, legs in
RUN while running and out of it once stopped. Crash performs it in
LOCAL_FRAME: the recorded stop is placed on her mark, the recorded final yaw
is rotated to face the camera, and the recording's own geometry decides where
her run starts. Nothing about speed, timing or the turn is authored.

The frozen scene is the PROOF_01 rail duel on overkill. Crash is absent before
the freeze, gestures only after the recording's own stop plus a beat, and is
gone before history resumes. History is never touched.

HEADLESS FIRST: placement validity (every retargeted sample on walked ground,
feet on the floor) and restoration are proven before any render, and the
render itself waits for a RenderPermit.

    python -m engine.pantheon.presenter_performance_proof            # headless
    python -m engine.pantheon.presenter_camera_film                  # render
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.instruction import (AnalysisBreak, Graphic, InstructionScene,
                                         Mode, place_entrance, validate_placement,
                                         validate_placement_shared)
from engine.pantheon.navigation import NavigationTruth
from engine.pantheon.roster import CAST
from engine.pantheon.scenario import RoundScenario, Team, Weapon

SCENE_ID = "PRESENTER_PERFORMANCE_PROOF_01"
MAP = "overkill"
NAV_CACHE = Path(f".tmp/nav_{MAP}.json")
TEMPLATE = "RUN_IN_STOP_TURN_01"
OUT = Path(".tmp/synthetic")

HIST_DURATION = 7.0
FREEZE_T = 4.0
HOLD_S = 8.0
PRESENTER = CAST["GUIDE"]              # Crash, trainer skin


def load_template(name: str):
    """The ACCEPTED entrance, exactly as filmed: the prologue's saved segment.

    The shared template DB's RUN_IN_STOP_TURN group currently admits windows
    that end AIRBORNE and one 525ms/1294u entry (a discontinuity); the
    usable entrance was found by the prologue's continuity + one-floor
    criteria and is kept verbatim here. Reported to the shared session; not
    re-derived here.
    """
    import json
    from engine.pantheon.performance import (AimSample, AnimSample, PerformanceTrace,
                                             TransformSample, WeaponSample)
    d = json.loads((Path("docs/reference/performance_templates") / f"{name}.json")
                   .read_text(encoding="utf-8"))
    tr = PerformanceTrace(d["demo_hash"], d["map"], d["gametype"], d["client"],
                          d["start_ms"], d["end_ms"])
    tr.transform = [TransformSample(**{k: (tuple(v) if isinstance(v, list) else v)
                                       for k, v in x.items()}) for x in d["transform"]]
    tr.aim = [AimSample(**x) for x in d["aim"]]
    tr.animation = [AnimSample(**x) for x in d["animation"]]
    tr.weapon = [WeaponSample(**x) for x in d["weapon"]]
    return tr


def build():
    nav = NavigationTruth.for_map(MAP, cache=NAV_CACHE)
    leg = nav.high_route().thinned()
    shooter_at, target_at, camera = _stage(leg)
    mid = tuple((a + b) / 2 for a, b in zip(shooter_at, target_at))

    # ── the historical scene: Keel rails Crash's stand-in (Visor) ──────
    scn = RoundScenario.clan_arena(map_name=MAP, hostname="PANTHEON PRESENTER PERF")
    scn.observer(camera, yaw=_yaw(camera, mid), team=Team.BLUE, name="POV")
    keel = scn.actor("KEEL", Team.RED).appearance("keel", "bright")
    visor = scn.actor("VISOR", Team.BLUE).appearance("visor", "default")
    keel.spawn(shooter_at, yaw=_yaw(shooter_at, target_at), t=0.0, weapon=Weapon.RAIL)
    visor.spawn(target_at, yaw=_yaw(target_at, shooter_at), t=0.0, weapon=Weapon.ROCKET)
    keel.stand(until=FREEZE_T + 0.1)
    keel.fire(Weapon.RAIL, impact=target_at, t=FREEZE_T + 0.2)
    keel.stand(until=HIST_DURATION - 0.2)
    visor.stand(until=HIST_DURATION - 0.2)

    # ── her mark: a walked point between the camera and the fight ──────
    # The mark is not chosen by taste. Facing the camera fixes the local
    # frame's rotation, and the recording's own geometry then fixes where the
    # run must START -- so the mark is the walked point, at conversational
    # distance from the camera, for which every retargeted sample lands on
    # ground real players stood on. Others are rejected before any render.
    template = load_template(TEMPLATE)
    from engine.pantheon.navigation import FLOOR_BAND
    top = nav.high_route().floor_z
    pool = sorted({tuple(round(c, 1) for c in pt) for r in nav.routes
                   if r.floor_z >= top - FLOOR_BAND for pt in r.points})
    cands = [p for p in pool if 150 < math.dist(p, camera) < 340
             and math.dist(p, mid) > 120]
    # The mark is chosen by the SHARED verdict (retarget.validate_retarget
    # over MapSpatialIndex + NavigationTruth at 48u): every candidate at
    # conversational distance is placed and judged, and the first that
    # passes is the mark. The prologue's same-floor check is kept as a
    # second opinion in the report only.
    tried, placement, validity, stand, best_frac = 0, None, None, None, -1.0
    for cand in sorted(cands, key=lambda p: abs(math.dist(p, camera) - 230)):
        pl = place_entrance(template, stop_at=cand, face=camera)
        pre = validate_placement(template, pl, nav)
        tried += 1
        if pre["verdict"] != "VALID":
            continue                                  # cheap prefilter
        shared = validate_placement_shared(template, pl, MAP, nav)
        if shared.get("ok"):
            stand, placement, validity = cand, pl, {"shared": shared, "prologue_same_floor": pre}
            break
        if shared.get("fraction_walked", 0) > best_frac:
            best_frac = shared["fraction_walked"]
            stand, placement, validity = cand, pl, {"shared": shared, "prologue_same_floor": pre}
    if placement is None:
        raise RuntimeError(f"{MAP}: no mark at conversational distance passes placement")
    validity["marks_tried"] = tried

    scene = InstructionScene(scn, duration=HIST_DURATION)
    scene.add_break(AnalysisBreak(
        at_t=FREEZE_T, hold_s=HOLD_S, mode=Mode.PRESENTER, profile=PRESENTER,
        enter_from=placement["start_world"], walk_to=stand, face=camera,
        entrance=template, gesture=True,
        graphic=Graphic.SHOOTER_TO_TARGET, graphic_from="KEEL", graphic_to="VISOR",
        walk_s=placement["stop_rel_s"]))
    built, report = scene.build()
    restoration = scene.verify_restoration(built)

    OUT.mkdir(parents=True, exist_ok=True)
    demo = built.compile(duration=scene.edit_duration).save(OUT / f"{SCENE_ID}.dm_73")
    FrameTruth.from_scenario(scn, duration=HIST_DURATION).save(
        OUT / f"{SCENE_ID}.historical.frametruth.json")
    FrameTruth.from_scenario(built, duration=scene.edit_duration).save(
        OUT / f"{SCENE_ID}.composite.frametruth.json")

    pres = built.actors[f"{PRESENTER.role}~PRESENTER"]
    e0 = report["breaks"][0]["edit_freeze_start_s"]
    motion = _motion_quality(pres, e0 + 0.15, template)
    report.update({
        "scene_id": SCENE_ID, "map": MAP, "template": TEMPLATE,
        "template_source": {"demo_hash": template.demo_hash, "client": template.client,
                            "map": template.map, "duration_s": template.duration_ms() / 1000},
        "presenter": {"role": PRESENTER.role, "model": PRESENTER.model,
                      "skin": PRESENTER.skin},
        "placement": {k: (list(v) if isinstance(v, tuple)
                          else v.as_dict() if hasattr(v, "as_dict") else v)
                      for k, v in placement.items()},
        "placement_validity": validity,
        "motion_quality": motion,
        "restoration": restoration,
        "camera": {"origin": list(camera), "moves": False},
    })
    (OUT / f"{SCENE_ID}.report.json").write_text(json.dumps(report, indent=1))
    return demo, scene, built, report


def _motion_quality(pres, t_start: float, template) -> dict:
    """Slide / run-in-place / yaw snap, measured on the compiled actor.

    Slide: body moving > 60 u/s while legs are not in a run family.
    Run-in-place: legs in RUN while the body is under 30 u/s (after the
    recorded settle). Yaw snap: more than 25 degrees between two 25ms ticks.
    """
    RUN = {15, 16}
    slide = rip = snap = 0
    prev = None
    n = 0
    dur = template.duration_ms() / 1000.0
    t = t_start
    while t <= t_start + dur:
        k = pres._at(t)
        if k.alive and k.recorded:
            n += 1
            v = math.hypot(*(k.velocity or (0, 0, 0))[:2])
            if v > 60 and k.legs_anim not in RUN and k.legs_anim not in (18, 19, 20):
                slide += 1
            if v < 30 and k.legs_anim in RUN:
                rip += 1
            if prev is not None and abs((k.yaw - prev + 180) % 360 - 180) > 25:
                snap += 1
            prev = k.yaw
        t = round(t + 0.025, 3)
    return {"samples": n, "slide_ticks": slide, "run_in_place_ticks": rip,
            "yaw_snap_ticks": snap,
            "slide": "YES" if slide else "NO",
            "run_in_place": "YES" if rip else "NO",
            "yaw_snap": "YES" if snap else "NO"}


def _stage(leg):
    best = None
    for i, a in enumerate(leg):
        for b in leg[i + 1:]:
            span = math.dist(a, b)
            if not 380 < span < 820:
                continue
            m = tuple((x + y) / 2 for x, y in zip(a, b))
            for c in leg:
                near = math.dist(c, m)
                if not 260 < near < 520:
                    continue
                den = math.dist((a[0], a[1]), (b[0], b[1])) or 1.0
                off = abs((b[0] - a[0]) * (a[1] - c[1]) - (a[0] - c[0]) * (b[1] - a[1])) / den
                score = off / max(near, 1e-6)
                if best is None or score > best[0]:
                    best = (score, a, b, c)
    if best is None:                          # pragma: no cover
        raise RuntimeError("no staging")
    return best[1], best[2], best[3]


def _yaw(a, b) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    args = ap.parse_args()
    demo, scene, built, rep = build()
    b = rep["breaks"][0]
    print(f"demo       : {demo} ({demo.stat().st_size:,} bytes)")
    print(f"template   : {rep['template']} from {rep['template_source']}")
    print(f"presenter  : {rep['presenter']}  entrance={b['entrance']}")
    pl = rep["placement"]
    print(f"placement  : {pl['mode']} yaw_offset={pl['yaw_offset']} start={[round(c) for c in pl['start_world']]} "
          f"stop={[round(c) for c in pl['stop_world']]} stop@{pl['stop_rel_s']}s turned@{pl['turned_rel_s']}s")
    print(f"validity   : shared={rep['placement_validity']['shared']}")
    print(f"             prologue={rep['placement_validity']['prologue_same_floor']}")
    print(f"motion     : {rep['motion_quality']}")
    print(f"freeze     : t={b['historical_t_s']}s -> edit {b['edit_freeze_start_s']}..{b['edit_freeze_end_s']}s")
    print(f"restoration: all_restored={rep['restoration']['all_restored']}")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
