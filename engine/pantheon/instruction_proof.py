"""INSTRUCTION_LAYER_PROOF_01 — the fight stops and the shooter explains it.

WHAT THIS PROVES, and deliberately nothing more: that the presentation
mechanism works. A real engine event plays, history stops, one participant
steps out of the frozen scene, walks to the camera, a derived tactical fact is
drawn behind him, he walks back, and the historical state resumes with no
displacement, no re-angling and no lost time.

It teaches no tactic. The concept-mining that finds an exceptional real
jump-pad punishment is a separate job, and building it before the mechanism
works would mean debugging two unknowns at once.

THE EVENT IS REAL ENGINE OUTPUT. The rail is an EV_RAILTRAIL the engine draws
and colours itself. The distance is computed from FrameTruth, never typed.

    python -m engine.pantheon.instruction_proof            # report only
    python -m engine.pantheon.instruction_proof --film
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.instruction import (AnalysisBreak, Graphic,
                                         InstructionScene, Layer)
from engine.pantheon.navigation import NavigationTruth
from engine.pantheon.scenario import RoundScenario, Team, Weapon
from engine.pantheon.shot import PassKind, ShotSpec, SourceKind, VisualProfile, render

SCENE_ID = "INSTRUCTION_LAYER_PROOF_01"
MAP = "overkill"
NAV_CACHE = Path(f".tmp/nav_{MAP}.json")

SHOOTER, TARGET = "KEEL", "CRASH"
SHOOTER_MODEL, SHOOTER_SKIN = ("keel", "bright")
TARGET_MODEL, TARGET_SKIN = ("crash", "trainer")

HISTORICAL_DURATION = 7.0
FIRE_T = 4.2                 # the rail leaves the barrel
FREEZE_T = 4.0               # history stops just BEFORE it does
HOLD_S = 7.0                 # how long the analysis lasts, in edit seconds


def build(out_dir: Path):
    nav = NavigationTruth.for_map(MAP, cache=NAV_CACHE)
    leg = nav.high_route().thinned()          # the highest regroup

    shooter_at, target_at, camera = _stage(leg)

    scn = RoundScenario.clan_arena(map_name=MAP,
                                   hostname="PANTHEON ANALYSIS MODE")
    scn.observer(camera, yaw=_yaw(camera, _mid(shooter_at, target_at)),
                 team=Team.BLUE, name="POV")

    # The shooter is BLUE with the POV, so his rail is a teammate rail and the
    # colour family PROOF 0 measured is the one in play.
    keel = scn.actor(SHOOTER, Team.BLUE).appearance(
        SHOOTER_MODEL, SHOOTER_SKIN, c1="2", c2="2")
    crash = scn.actor(TARGET, Team.RED).appearance(
        TARGET_MODEL, TARGET_SKIN, c1="1", c2="1")

    keel.spawn(shooter_at, yaw=_yaw(shooter_at, target_at), t=0.0,
               weapon=Weapon.RAIL)
    crash.spawn(target_at, yaw=_yaw(target_at, shooter_at), t=0.0,
                weapon=Weapon.ROCKET)
    keel.stand(until=FIRE_T - 0.1)
    keel.fire(Weapon.RAIL, impact=target_at, t=FIRE_T)
    keel.stand(until=HISTORICAL_DURATION - 0.2)
    crash.stand(until=HISTORICAL_DURATION - 0.2)

    # ── the break ────────────────────────────────────────────────────────
    # He walks toward the camera along the route real players walked, so the
    # path is navigable by construction rather than by assertion.
    frozen = keel._at(FREEZE_T).origin
    stand_spot = min((p for p in leg if 170 < math.dist(p, camera) < 330),
                     key=lambda p: math.dist(p, camera), default=leg[0])
    route = _walk_route(leg, frozen, stand_spot)

    scene = InstructionScene(scn, duration=HISTORICAL_DURATION)
    scene.add_break(AnalysisBreak(
        at_t=FREEZE_T, hold_s=HOLD_S, presenter=SHOOTER,
        walk_to=stand_spot, face=camera, route_out=route,
        graphic=Graphic.SHOOTER_TO_TARGET,
        graphic_from=SHOOTER, graphic_to=TARGET, walk_s=1.9))

    built, report = scene.build()
    restoration = scene.verify_restoration(built)

    out_dir.mkdir(parents=True, exist_ok=True)
    demo = built.compile(duration=scene.edit_duration).save(
        out_dir / f"{SCENE_ID}.dm_73")
    truth = FrameTruth.from_scenario(built, duration=scene.edit_duration)
    truth.save(out_dir / f"{SCENE_ID}.frametruth.json")

    report["scene_id"] = SCENE_ID
    report["map"] = MAP
    report["camera"] = {"origin": [round(c, 2) for c in camera],
                        "yaw": round(_yaw(camera, _mid(shooter_at, target_at)), 2),
                        "moves": False,
                        "collision": "STATIC — the camera never leaves the "
                                     "walked position it starts on, so no BSP "
                                     "path needs validating for this proof"}
    report["navigation_source"] = {
        "map": MAP, "route": "high_route (highest floor band)",
        "floor_z": round(nav.high_route().floor_z, 1),
        "walked_points": len(leg),
        "collision": "INHERITED — every authored position is an on-ground "
                     "origin a real player occupied in a mined demo"}
    report["restoration"] = restoration
    (out_dir / f"{SCENE_ID}.report.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")
    return demo, scene, built, report


def _stage(leg):
    """Shooter, target and a broadside camera, all on walked ground."""
    best = None
    for i, a in enumerate(leg):
        for b in leg[i + 1:]:
            span = math.dist(a, b)
            if not 380 < span < 820:
                continue
            m = _mid(a, b)
            for c in leg:
                near = math.dist(c, m)
                if not 260 < near < 520:
                    continue
                score = _off_axis(a, b, c) / max(near, 1e-6)
                if best is None or score > best[0]:
                    best = (score, a, b, c)
    if best is None:                          # pragma: no cover - map-dependent
        raise RuntimeError(f"{MAP}: no broadside staging on the high route")
    return best[1], best[2], best[3]


def _walk_route(leg, start, end):
    """A path from the frozen position to the mark, through walked points.

    Not a straight line: a straight line between two navigable points is not
    itself navigable. Intermediate points are chosen so each step is short
    enough to have been walked, and every point is one somebody stood on.
    """
    route, here = [tuple(start)], tuple(start)
    for _ in range(6):
        if math.dist(here, end) < 180:
            break
        step = min((p for p in leg
                    if 90 < math.dist(here, p) < 240
                    and math.dist(p, end) < math.dist(here, end) - 40),
                   key=lambda p: math.dist(p, end), default=None)
        if step is None:
            break
        route.append(step)
        here = step
    route.append(tuple(end))
    return route


def _mid(a, b):
    return tuple((x + y) / 2 for x, y in zip(a, b))


def _yaw(a, b) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360


def _off_axis(a, b, p) -> float:
    den = math.dist((a[0], a[1]), (b[0], b[1])) or 1.0
    return abs((b[0] - a[0]) * (a[1] - p[1])
               - (a[0] - p[0]) * (b[1] - a[1])) / den


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path(".tmp/synthetic"))
    ap.add_argument("--shots", type=Path, default=Path(".tmp/shots"))
    ap.add_argument("--film", action="store_true")
    args = ap.parse_args()

    demo, scene, built, rep = build(args.out)
    b = rep["breaks"][0]
    print(f"demo            : {demo}  ({demo.stat().st_size:,} bytes)")
    print(f"map / route     : {rep['map']}  {rep['navigation_source']['route']}"
          f"  z={rep['navigation_source']['floor_z']}"
          f"  ({rep['navigation_source']['walked_points']} walked points)")
    print(f"historical      : {rep['historical_duration_s']}s"
          f"   edit: {rep['edit_duration_s']}s")
    print(f"freeze          : historical t={b['historical_t_s']}s  ->  edit "
          f"{b['edit_freeze_start_s']}..{b['edit_freeze_end_s']}s")
    print(f"historical actor: {b['historical_actor']} [{b['historical_actor_layer']}] "
          f"{b['historical_frozen_state']}")
    print(f"analysis actor  : {b['analysis_actor']} [{b['analysis_actor_layer']}]")
    print(f"walk route      : {len(b['walk_route'])} walked points, "
          f"{b['walk_len_units']} units")
    if "graphic" in b:
        f = b["graphic"]["fact"]
        print(f"graphic         : {b['graphic']['kind']} "
              f"[{b['graphic']['layer']}]  {f['label']} = "
              f"{f['value']} {f['units']}")
        print(f"  derivation    : {f['derivation']}")
    r = rep["restoration"]
    print(f"restoration     : all_restored={r['all_restored']}")
    for row in r["breaks"]:
        for name, st in row["actors"].items():
            print(f"  {name:10s} identical={st['identical']} "
                  f"d_origin={st['origin_delta']} d_yaw={st['yaw_delta']} "
                  f"{st['weapon']} hp={st['health']}")

    if args.film:
        spec = ShotSpec(
            shot_id=SCENE_ID, source=demo.resolve(),
            source_kind=SourceKind.SYNTHETIC,
            start_s=0.8, end_s=rep["edit_duration_s"] - 0.3,
            visual=VisualProfile(name="INSTRUCTION", extra={
                "cg_railUseOwnColors": 0,
                "cg_teamRailColor1": '"0x28c8ff"',   # PROOF 0 format
                "cg_teamRailColor2": '"0x28c8ff"',
            }),
            passes=(PassKind.BEAUTY,),
            truth_reference=args.out / f"{SCENE_ID}.frametruth.json",
            provenance="INSTRUCTION_LAYER_PROOF")
        avi = render(spec, args.shots)
        print(f"\nfilmed          : {avi}  ({avi.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
