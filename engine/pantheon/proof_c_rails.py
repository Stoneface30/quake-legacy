"""INSTRUCTION_LAYER_PROOF_C — a 3v3 rail fight, seen from inside it, and
a cast character walks in to explain it.

WHAT IS NEW OVER PROOF 01, and only this:
  * six historical actors, not two, and they move;
  * the point of view is a PARTICIPANT -- first person of one blue fighter --
    not a spectator standing to the side;
  * the freeze detaches the camera from that participant, orbits the frozen
    fight, and returns to the exact same eye before history resumes;
  * the explainer is not a copy of anyone in the fight. Crash, the game's own
    trainer, walks in from off-scene, gestures, and speaks one line on the
    edit clock;
  * the alive counters, score and obituaries never learn she was there.

Everything else is the machinery PROOF 01 proved: TimeMap freeze, separate
client, immutable history, derived distance, labelled reconstruction line.

    python -m engine.pantheon.proof_c_rails --film
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from engine.pantheon.dialogue_mix import build_dialogue_stem, mux
from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.instruction import (AnalysisBreak, Graphic, InstructionScene,
                                         Line, Mode)
from engine.pantheon.navigation import FLOOR_BAND, NavigationTruth
from engine.pantheon.roster import CAST
from engine.pantheon.scenario import RoundScenario, Team, Weapon
from engine.pantheon.shot import PassKind, ShotSpec, SourceKind, VisualProfile, render

SCENE_ID = "INSTRUCTION_LAYER_PROOF_C"
MAP = "overkill"
NAV_CACHE = Path(f".tmp/nav_{MAP}.json")
TTS = Path(".tmp/voice/tts")

# Six fighters. Distinct models on purpose: the roster is part of the film,
# and a 3v3 where everyone is Sarge would say nothing about it.
BLUE = [("VISOR", "visor", "default"), ("DOOM", "doom", "default"),
        ("RANGER", "ranger", "default")]
RED = [("KEEL", "keel", "bright"), ("XAERO", "xaero", "default"),
       ("BONES", "bones", "default")]
POV = "VISOR"                       # first person of this blue fighter
SHOOTER, TARGET = "KEEL", "VISOR"   # the decisive rail: Keel shoots the POV

HIST_DURATION = 9.0
FREEZE_T = 5.3                      # just before Keel's rail leaves
HOLD_S = 9.5

PRESENTER = CAST["GUIDE"]           # Crash, trainer skin
LINE = Line(text="Watch this.", audio=TTS / "crash_watch_this.wav",
            source_kind="SYNTHETIC_TTS", voice_profile="GUIDE")


def build(out_dir: Path):
    nav = NavigationTruth.for_map(MAP, cache=NAV_CACHE)
    top = nav.high_route().floor_z
    pool = sorted({tuple(round(c, 1) for c in pt)
                   for r in nav.routes if r.floor_z >= top - FLOOR_BAND
                   for pt in r.points})
    blue_spots, red_spots, mid = _two_lines(pool)

    scn = RoundScenario.clan_arena(map_name=MAP, hostname="PANTHEON PROOF C")

    actors = {}
    for (name, model, skin), spot in zip(BLUE, blue_spots):
        a = scn.actor(name, Team.BLUE).appearance(model, skin)
        a.spawn(spot, yaw=_yaw(spot, mid), t=0.0, weapon=Weapon.RAIL)
        actors[name] = (a, spot)
    for (name, model, skin), spot in zip(RED, red_spots):
        a = scn.actor(name, Team.RED).appearance(model, skin)
        a.spawn(spot, yaw=_yaw(spot, mid), t=0.0, weapon=Weapon.RAIL)
        actors[name] = (a, spot)

    # movement: everyone shifts one walked step so the fight is not a tableau
    for name, (a, spot) in actors.items():
        step = _near(pool, spot, 90, 200)
        a.stand(until=1.0)
        a.move_to([spot, step], start=1.0)
        a.look_at_point(mid, t=a._last().t + 0.3)
        a.stand(until=HIST_DURATION - 0.2)

    # rails: two exchanges before the freeze, Keel's decisive shot after it
    a, _ = actors["DOOM"];   a.fire(Weapon.RAIL, at=actors["XAERO"][0], t=3.2)
    a, _ = actors["BONES"];  a.fire(Weapon.RAIL, at=actors["RANGER"][0], t=4.1)
    a, _ = actors[SHOOTER];  a.fire(Weapon.RAIL, at=actors[TARGET][0], t=5.6)
    a, _ = actors["RANGER"]; a.fire(Weapon.RAIL, at=actors["BONES"][0], t=7.0)

    # POV: first person of VISOR, for the whole historical span
    pov, _ = actors[POV]
    scn.observer(pov._at(0.0).origin, yaw=pov._at(0.0).yaw, team=Team.BLUE,
                 name=POV)
    scn._camera_path = []
    scn.follow(pov, t0=0.0, t1=HIST_DURATION)

    # the break: Crash walks in from a walked point outside the fight, stands
    # where the camera will settle to look at her, and speaks
    eye = scn.camera_at(FREEZE_T).origin
    stand = _near(pool, mid, 120, 260)
    enter = _near(pool, stand, 220, 420)
    orbit = _orbit(pool, mid, eye, n=4)
    settle = orbit[-1]

    scene = InstructionScene(scn, duration=HIST_DURATION)
    scene.add_break(AnalysisBreak(
        at_t=FREEZE_T, hold_s=HOLD_S, mode=Mode.PRESENTER,
        profile=PRESENTER, enter_from=enter, walk_to=stand, face=settle,
        route_out=[enter, stand], graphic=Graphic.SHOOTER_TO_TARGET,
        graphic_from=SHOOTER, graphic_to=TARGET, walk_s=1.8,
        line=LINE, gesture=True, orbit=orbit, orbit_look_at=mid))

    built, report = scene.build()
    restoration = scene.verify_restoration(built)

    out_dir.mkdir(parents=True, exist_ok=True)
    demo = built.compile(duration=scene.edit_duration).save(
        out_dir / f"{SCENE_ID}.dm_73")
    FrameTruth.from_scenario(scn, duration=HIST_DURATION).save(
        out_dir / f"{SCENE_ID}.historical.frametruth.json")
    FrameTruth.from_scenario(built, duration=scene.edit_duration).save(
        out_dir / f"{SCENE_ID}.composite.frametruth.json")
    cues = [c.as_dict() for c in scene.cues]
    (out_dir / f"{SCENE_ID}.dialogue.json").write_text(
        json.dumps({"duration_s": scene.edit_duration, "cues": cues},
                   indent=1), encoding="utf-8")

    report.update({
        "scene_id": SCENE_ID, "map": MAP,
        "historical_actors": {n: {"team": a.team.name, "model": a.model,
                                  "skin": a.skin} for n, (a, _) in actors.items()},
        "pov": {"actor": POV, "mode": "FIRST_PERSON_FOLLOW"},
        "camera": {"orbit_points": [list(p) for p in orbit],
                   "collision": "every orbit point is a walked position from "
                                "the high floor band; segments between them "
                                "are interpolated and NOT BSP-traced"},
        "presenter": {"role": PRESENTER.role, "model": PRESENTER.model,
                      "skin": PRESENTER.skin, "enter_from": list(enter),
                      "stand": list(stand)},
        "alive_counters": {t.name: v for t, v in built._alive.items()},
        "restoration": restoration,
    })
    (out_dir / f"{SCENE_ID}.report.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")
    return demo, scene, built, report


# ── staging ────────────────────────────────────────────────────────────────

def _two_lines(pool):
    """Two facing clusters of three, ~500 units apart, on walked ground."""
    best = None
    step = max(1, len(pool) // 80)
    p = pool[::step]
    for a in p:
        for b in p:
            d = math.dist(a, b)
            if not 420 < d < 700:
                continue
            ca = [q for q in p if math.dist(q, a) < 150]
            cb = [q for q in p if math.dist(q, b) < 150]
            if len(ca) >= 3 and len(cb) >= 3:
                score = -abs(d - 540)
                if best is None or score > best[0]:
                    best = (score, ca[:3], cb[:3], a, b)
    if best is None:                          # pragma: no cover - map-dependent
        raise RuntimeError(f"{MAP}: no two facing clusters on the high band")
    _, ca, cb, a, b = best
    mid = tuple((x + y) / 2 for x, y in zip(a, b))
    return ca, cb, mid


def _near(pool, origin, lo, hi):
    c = [q for q in pool if lo < math.dist(q, origin) < hi]
    if not c:
        raise RuntimeError(f"no walked point {lo}-{hi} units from {origin}")
    return min(c, key=lambda q: math.dist(q, origin))


def _orbit(pool, centre, start, n):
    """`n` walked points sweeping around `centre`, starting near `start`."""
    r = max(220.0, math.dist((start[0], start[1]), (centre[0], centre[1])))
    a0 = math.atan2(start[1] - centre[1], start[0] - centre[0])
    pts = []
    for i in range(1, n + 1):
        ang = a0 + (math.pi * 0.9) * i / n
        ideal = (centre[0] + r * math.cos(ang), centre[1] + r * math.sin(ang))
        best = min(pool, key=lambda q: math.dist((q[0], q[1]), ideal))
        if not pts or math.dist(best, pts[-1]) > 40:
            pts.append(best)
    return pts


def _yaw(a, b) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path(".tmp/synthetic"))
    ap.add_argument("--shots", type=Path, default=Path(".tmp/shots"))
    ap.add_argument("--film", action="store_true")
    args = ap.parse_args()

    demo, scene, built, rep = build(args.out)
    b = rep["breaks"][0]
    print(f"demo         : {demo}  ({demo.stat().st_size:,} bytes)")
    print(f"cast         : " + ", ".join(f"{n}={v['model']}/{v['skin']}({v['team'][0]})"
                                      for n, v in rep["historical_actors"].items()))
    print(f"pov          : {rep['pov']}")
    print(f"historical   : {rep['historical_duration_s']}s  edit: {rep['edit_duration_s']}s")
    print(f"freeze       : t={b['historical_t_s']}s -> edit {b['edit_freeze_start_s']}..{b['edit_freeze_end_s']}s")
    print(f"explainer    : {b['explainer']} [{b['explainer_layer']}] {b['explainer_appearance']}")
    print(f"line         : {b['line']}")
    print(f"orbit        : {b['camera_orbit_points']} walked points")
    print(f"alive        : {rep['alive_counters']}  (presenter excluded)")
    if "graphic" in b:
        f = b["graphic"]["fact"]
        print(f"graphic      : {f['label']} = {f['value']} {f['units']}  [{b['graphic']['layer']}]")
    r = rep["restoration"]
    print(f"restoration  : all_restored={r['all_restored']}")
    for name, st in r["breaks"][0]["actors"].items():
        print(f"  {name:8s} identical={st['identical']} d_origin={st['origin_delta']} d_yaw={st['yaw_delta']}")

    if args.film:
        start = 0.8
        spec = ShotSpec(
            shot_id=SCENE_ID, source=demo.resolve(),
            source_kind=SourceKind.SYNTHETIC,
            start_s=start, end_s=rep["edit_duration_s"] - 0.3,
            visual=VisualProfile(name="PROOF_C", extra={
                "cg_railUseOwnColors": 0,
                "cg_teamRailColor1": '"0x28c8ff"',
                "cg_teamRailColor2": '"0x28c8ff"',
                "cg_enemyRailColor1": '"0xff3c3c"',
                "cg_enemyRailColor2": '"0xff3c3c"',
                # every model keeps its own look
                "cg_enemyLegsColor": '""', "cg_enemyTorsoColor": '""',
                "cg_enemyHeadColor": '""', "cg_teamLegsColor": '""',
                "cg_teamTorsoColor": '""', "cg_teamHeadColor": '""',
                "r_mapOverBrightBits": 2, "r_gamma": 1.2, "cg_shadows": 0,
            }),
            passes=(PassKind.BEAUTY,),
            truth_reference=args.out / f"{SCENE_ID}.composite.frametruth.json",
            provenance="INSTRUCTION_LAYER_PROOF_C")
        avi = render(spec, args.shots)
        stem = build_dialogue_stem(args.out / f"{SCENE_ID}.dialogue.json",
                                   args.shots / f"{SCENE_ID}_dialogue.wav",
                                   shot_start_s=start,
                                   duration_s=rep["edit_duration_s"] - 0.3 - start)
        out = mux(avi, stem, args.shots / f"{SCENE_ID}.mp4")
        print(f"\nfilmed       : {avi}  ({avi.stat().st_size/1e6:.1f} MB)")
        print(f"delivered    : {out}  ({out.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
