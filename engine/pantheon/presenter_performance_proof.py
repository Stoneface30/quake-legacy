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
    python -m engine.pantheon.presenter_performance_proof --film
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.instruction import (AnalysisBreak, Graphic, InstructionScene,
                                         Mode, place_entrance, validate_placement)
from engine.pantheon.navigation import NavigationTruth
from engine.pantheon.performance_templates import load_template
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
    tried, placement, validity, stand = 0, None, None, None
    for cand in sorted(cands, key=lambda p: abs(math.dist(p, camera) - 230)):
        pl = place_entrance(template, stop_at=cand, face=camera)
        va = validate_placement(template, pl, nav)
        tried += 1
        if va["verdict"] == "VALID":
            stand, placement, validity = cand, pl, va
            break
        if placement is None or va["off_walked_ground"] < validity["off_walked_ground"]:
            stand, placement, validity = cand, pl, va
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
        "placement": {k: (list(v) if isinstance(v, tuple) else v)
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
    ap.add_argument("--film", action="store_true")
    ap.add_argument("--shots", type=Path, default=Path(".tmp/shots"))
    args = ap.parse_args()
    demo, scene, built, rep = build()
    b = rep["breaks"][0]
    print(f"demo       : {demo} ({demo.stat().st_size:,} bytes)")
    print(f"template   : {rep['template']} from {rep['template_source']}")
    print(f"presenter  : {rep['presenter']}  entrance={b['entrance']}")
    pl = rep["placement"]
    print(f"placement  : {pl['mode']} yaw_offset={pl['yaw_offset']} start={[round(c) for c in pl['start_world']]} "
          f"stop={[round(c) for c in pl['stop_world']]} stop@{pl['stop_rel_s']}s turned@{pl['turned_rel_s']}s")
    print(f"validity   : {rep['placement_validity']}")
    print(f"motion     : {rep['motion_quality']}")
    print(f"freeze     : t={b['historical_t_s']}s -> edit {b['edit_freeze_start_s']}..{b['edit_freeze_end_s']}s")
    print(f"restoration: all_restored={rep['restoration']['all_restored']}")
    if args.film:
        from engine.pantheon.backends import BackendUse, render
        from engine.pantheon.shot import PassKind, ShotSpec, SourceKind, VisualProfile
        spec = ShotSpec(shot_id=SCENE_ID, source=demo.resolve(),
                        source_kind=SourceKind.SYNTHETIC, start_s=0.8,
                        end_s=rep["edit_duration_s"] - 0.3,
                        visual=VisualProfile(name="PRESENTER_PERF", extra={
                            "cg_railUseOwnColors": 0,
                            "cg_teamRailColor1": '"0x28c8ff"', "cg_teamRailColor2": '"0x28c8ff"',
                            "cg_enemyLegsColor": '""', "cg_enemyTorsoColor": '""',
                            "cg_enemyHeadColor": '""', "cg_teamLegsColor": '""',
                            "cg_teamTorsoColor": '""', "cg_teamHeadColor": '""',
                            "r_mapOverBrightBits": 2, "r_gamma": 1.2, "cg_shadows": 0}),
                        passes=(PassKind.BEAUTY,), provenance="PRESENTER_PERFORMANCE_PROOF")
        avi = render("WOLFCAM_REFERENCE", shot=spec, out_dir=args.shots,
                     use=BackendUse.REFERENCE_RENDER)
        print(f"filmed     : {avi} ({avi.stat().st_size/1e6:.1f} MB)  manifest={spec.manifest['BEAUTY']['duration_s']}s")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
