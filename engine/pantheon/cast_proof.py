"""PANTHEON_CAST_PROOF_01 — the roster, on the same mark, one after another.

WHY ONE DEMO AND NOT EIGHT. The point of a cast sheet is that only the
character changes. Putting every candidate on the SAME walked mark, in front
of the SAME camera, inside ONE compiled demo, makes the comparison exact by
construction and costs one engine launch instead of eight. Each character gets
a six-second slot: stand facing camera, gesture, walk to a second walked mark,
leave. The stills come out of one AVI at known times.

Casting decisions are made from these pixels, not from model names.

    python -m engine.pantheon.cast_proof --film
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.navigation import NavigationTruth
from engine.pantheon.roster import PresenterProfile, load_inventory
from engine.pantheon.scenario import RoundScenario, Team, Weapon
from engine.pantheon.shot import PassKind, ShotSpec, SourceKind, VisualProfile, render

SCENE_ID = "PANTHEON_CAST_PROOF_01"
MAP = "overkill"
NAV_CACHE = Path(f".tmp/nav_{MAP}.json")
FFMPEG = Path("G:/QUAKE_LEGACY/creative_suite/tools/ffmpeg/ffmpeg.exe")

# (model, skin) -- the iconic set plus enough of the rest to choose from.
ROSTER = [("crash", "trainer"), ("keel", "bright"), ("anarki", "default"),
          ("slash", "default"), ("orbb", "default"), ("sarge", "default"),
          ("ranger", "default"), ("xaero", "default"), ("visor", "default"),
          ("hunter", "default"), ("doom", "default"), ("bones", "default")]

SLOT_S = 6.0
IDLE_AT, GESTURE_AT, WALK = 0.8, 1.3, (3.0, 4.8)


def build(out_dir: Path):
    nav = NavigationTruth.for_map(MAP, cache=NAV_CACHE)
    leg = nav.high_route().thinned()
    mark, walk_to, camera = _stage(leg)
    inv = load_inventory()

    scn = RoundScenario.clan_arena(map_name=MAP, hostname="PANTHEON CAST")
    scn.observer(camera, yaw=_yaw(camera, mark), team=Team.BLUE, name="POV")

    slots = []
    for i, (model, skin) in enumerate(ROSTER):
        PresenterProfile(f"CAST_{i}", model, skin).resolve(inv)   # must exist
        t0 = i * SLOT_S
        # RED, so nobody is the POV's teammate and no team tint applies; the
        # enemy colour family is cleared in the profile below for the same
        # reason. The sheet shows what the skin IS.
        a = scn.actor(f"{model}_{skin}", Team.RED).appearance(model, skin)
        a.counts_toward_roster = False
        a.spawn(mark, yaw=_yaw(mark, camera), t=t0, weapon=Weapon.RAIL)
        a.stand(until=t0 + GESTURE_AT)
        a.gesture(t=t0 + GESTURE_AT)
        a.stand(until=t0 + WALK[0])
        a.move_to([mark, walk_to], during=(t0 + WALK[0], t0 + WALK[1]))
        a.look_at_point(camera, t=t0 + WALK[1] + 0.3)
        a.stand(until=t0 + SLOT_S - 0.25)
        a.despawn(t=t0 + SLOT_S - 0.2)
        slots.append({"model": model, "skin": skin, "t0": t0,
                      "gesture_frames": inv[model].gesture_frames,
                      "can_gesture": inv[model].can_gesture})

    duration = len(ROSTER) * SLOT_S + 0.5
    out_dir.mkdir(parents=True, exist_ok=True)
    demo = scn.compile(duration=duration).save(out_dir / f"{SCENE_ID}.dm_73")
    FrameTruth.from_scenario(scn, duration=duration).save(
        out_dir / f"{SCENE_ID}.frametruth.json")
    meta = {"scene_id": SCENE_ID, "map": MAP, "mark": list(mark),
            "walk_to": list(walk_to), "camera": list(camera),
            "duration_s": duration, "slot_s": SLOT_S, "slots": slots}
    (out_dir / f"{SCENE_ID}.cast.json").write_text(json.dumps(meta, indent=1),
                                                  encoding="utf-8")
    return demo, meta


def _stage(leg):
    """Mark, a second mark to walk to, and a camera 250-400 units off."""
    best = None
    for m in leg:
        for c in leg:
            d = math.dist(m, c)
            if not 250 < d < 400:
                continue
            walk = min((p for p in leg
                        if 110 < math.dist(m, p) < 220
                        and abs(math.dist(c, p) - d) < 90), default=None,
                       key=lambda p: abs(math.dist(m, p) - 160))
            if walk is None:
                continue
            score = -abs(d - 320)
            if best is None or score > best[0]:
                best = (score, m, walk, c)
    if best is None:                          # pragma: no cover - map-dependent
        raise RuntimeError(f"{MAP}: no cast mark on the high route")
    return best[1], best[2], best[3]


def _yaw(a, b) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360


def stills_and_sheet(avi: Path, meta: dict, out_dir: Path, *,
                     shot_start: float) -> Path:
    """Three stills per character and one labelled contact sheet."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tiles = []
    for s in meta["slots"]:
        base = s["t0"] - shot_start
        for tag, dt in (("idle", IDLE_AT), ("gesture", GESTURE_AT + 0.7),
                        ("walk", WALK[0] + 0.9)):
            dest = out_dir / f"{s['model']}_{s['skin']}_{tag}.png"
            subprocess.run([str(FFMPEG), "-v", "error", "-y",
                            "-ss", f"{base + dt:.3f}", "-i", str(avi),
                            "-frames:v", "1", str(dest)], check=True)
        label = f"{s['model']}/{s['skin']}" + ("" if s["can_gesture"]
                                               else "  (no gesture)")
        tiles.append((out_dir / f"{s['model']}_{s['skin']}_gesture.png", label))

    # one 4-wide contact sheet of the gesture frames, labelled
    n = len(tiles)
    cols, rows = 4, math.ceil(n / 4)
    inputs, chains = [], []
    for i, (p, label) in enumerate(tiles):
        inputs += ["-i", str(p)]
        chains.append(
            f"[{i}:v]scale=480:270,"
            f"drawtext=text='{label}':x=10:y=236:fontsize=22:"
            f"fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=6[t{i}]")
    layout = "|".join(f"{(i % cols) * 480}_{(i // cols) * 270}" for i in range(n))
    graph = (";".join(chains) + ";" + "".join(f"[t{i}]" for i in range(n))
             + f"xstack=inputs={n}:layout={layout}:fill=black[out]")
    sheet = out_dir / f"{SCENE_ID}_sheet.png"
    subprocess.run([str(FFMPEG), "-v", "error", "-y", *inputs,
                    "-filter_complex", graph, "-map", "[out]", str(sheet)],
                   check=True)
    return sheet


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path(".tmp/synthetic"))
    ap.add_argument("--shots", type=Path, default=Path(".tmp/shots"))
    ap.add_argument("--film", action="store_true")
    args = ap.parse_args()

    demo, meta = build(args.out)
    print(f"demo   : {demo}  ({demo.stat().st_size:,} bytes)")
    print(f"mark   : {meta['mark']}  walk_to {meta['walk_to']}  "
          f"camera {meta['camera']}")
    for s in meta["slots"]:
        print(f"  t={s['t0']:5.1f}s  {s['model']}/{s['skin']:8s} "
              f"gesture_frames={s['gesture_frames']}")
    if args.film:
        start = 0.8
        spec = ShotSpec(
            shot_id=SCENE_ID, source=demo.resolve(),
            source_kind=SourceKind.SYNTHETIC,
            start_s=start, end_s=meta["duration_s"] - 0.3,
            visual=VisualProfile(name="CAST", extra={
                # every override off: the sheet shows what the skin IS
                "cg_enemyLegsColor": '""', "cg_enemyTorsoColor": '""',
                "cg_enemyHeadColor": '""', "cg_teamLegsColor": '""',
                "cg_teamTorsoColor": '""', "cg_teamHeadColor": '""',
                "r_mapOverBrightBits": 2, "r_gamma": 1.2, "cg_shadows": 0,
            }),
            passes=(PassKind.BEAUTY,), provenance="CAST_SHEET")
        avi = render(spec, args.shots)
        print(f"filmed : {avi}  ({avi.stat().st_size/1e6:.1f} MB)")
        sheet = stills_and_sheet(
            avi, meta, Path("G:/QUAKE_LEGACY/docs/visual-record/2026-09-05/cast"),
            shot_start=start)
        print(f"sheet  : {sheet}")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
