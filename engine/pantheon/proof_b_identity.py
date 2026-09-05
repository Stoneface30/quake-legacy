"""PROOF B — who decides what a player looks like, measured on pixels.

THE QUESTION. In INSTRUCTION_LAYER_PROOF_01 a `keel/bright` actor rendered
WHITE. The project's standing lesson is that three separate source-derived
explanations of exactly this have been wrong, so this proof does not read any
more C. It puts six actors in one frame and measures them.

THE VARIABLES ARE SEPARATED. Model, skin, and team are varied per ACTOR inside
one capture, so camera, lighting, position and time are shared by construction
rather than by care. Only the client-side colour cvars, which are global, vary
BETWEEN captures.

    A1 keel/bright   BLUE (the POV's own team -> "teammate")
    A2 keel/bright   RED  (the POV's opponent -> "enemy")
    A3 keel/default  BLUE
    A4 keel/default  RED
    A5 sarge/default BLUE      silhouette control
    A6 sarge/default RED

    capture 1  every client override cleared -> demo-authored truth
    capture 2  cg_team*Color = 0x00ff00, cg_enemy*Color = 0xff00ff
    capture 3  cg_forceModel 1 + cg_enemyModel "keel/bright"

Actors are located in the frame by projecting their FrameTruth origin through
the camera, not by eye: the sample box follows the actor, so a measurement
cannot silently drift onto a wall.

    python -m engine.pantheon.proof_b_identity --film
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from engine.pantheon.ab_scene import ConfigScene, CvarInventory, Variant
from engine.pantheon.color_format import format_for
from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.navigation import NavigationTruth
from engine.pantheon.scenario import RoundScenario, Team, Weapon
from engine.pantheon.shot import VisualProfile

SCENE_ID = "PROOF_B_IDENTITY"
MAP = "overkill"
NAV_CACHE = Path(f".tmp/nav_{MAP}.json")

# (name, model, skin, team) -- the POV is BLUE, so BLUE actors are teammates.
# Four cells, not six. A real arena's top floor does not offer six walked
# positions that are broadside to one camera AND mutually unoccluded, and
# inventing positions to get six would throw away the whole point of mining
# them. These four answer the question: does TEAM RELATION change the tint,
# and does it reach a skin other than `bright`?
CAST = [
    ("A1_keel_bright_team",   "keel",  "bright",  Team.BLUE),
    ("A2_keel_bright_enemy",  "keel",  "bright",  Team.RED),
    ("A3_sarge_team",         "sarge", "default", Team.BLUE),
    ("A4_sarge_enemy",        "sarge", "default", Team.RED),
]

DURATION = 4.0
SHOT_START, SHOT_END = 0.8, 3.0
SAMPLE_T = 1.4          # seconds into the shot

TEAM_TEST = (0, 255, 0)        # what cg_team*Color is set to in capture 2
ENEMY_TEST = (255, 0, 255)     # what cg_enemy*Color is set to in capture 2

FOV_X = 110.0           # cg_fov, read from the runtime inventory
W, H = 1920, 1080


def build(out_dir: Path):
    """Six actors on ONE walked route, with the camera on that route too.

    The first staging picked the camera by widest screen spread and got a spot
    against a wall: four of the six actors were behind geometry and the frame
    proved nothing. Points on a single mined route are positions one player
    walked BETWEEN, so a sightline along the route is inherited rather than
    hoped for. The camera stands at one end and looks down it.
    """
    nav = NavigationTruth.for_map(MAP, cache=NAV_CACHE)
    route = nav.high_route()
    from engine.pantheon.navigation import FLOOR_BAND
    spots = sorted({tuple(round(c, 1) for c in pt)
                    for r in nav.routes if r.floor_z >= route.floor_z - FLOOR_BAND
                    for pt in r.points})
    if len(spots) < len(CAST) + 3:
        raise RuntimeError(f"{MAP}: high band has only {len(spots)} spots")

    # Down-the-corridor staging put all six on nearly the same screen column,
    # where they occlude one another. What is needed is BROADSIDE: a stretch of
    # the route seen side-on, which is the geometry PROOF 0 already showed
    # works. Camera and actors still all come from this one walked route.
    camera, line = _broadside_line(spots, len(CAST))
    mid = tuple(sum(p[i] for p in line) / len(line) for i in range(3))

    scn = RoundScenario.clan_arena(map_name=MAP, hostname="PANTHEON IDENTITY")
    scn.observer(camera, yaw=_yaw(camera, mid), team=Team.BLUE, name="POV")

    for (name, model, skin, team), spot in zip(CAST, line):
        a = scn.actor(name, team).appearance(model, skin, c1="7", c2="7")
        a.spawn(spot, yaw=_yaw(spot, camera), t=0.0, weapon=Weapon.RAIL)
        a.stand(until=DURATION - 0.2)

    out_dir.mkdir(parents=True, exist_ok=True)
    demo = scn.compile(duration=DURATION).save(out_dir / f"{SCENE_ID}.dm_73")
    truth = FrameTruth.from_scenario(scn, duration=DURATION)
    truth.save(out_dir / f"{SCENE_ID}.frametruth.json")

    geom = {"map": MAP, "camera": [round(c, 2) for c in camera],
            "camera_yaw": round(_yaw(camera, mid), 2), "fov_x": FOV_X,
            "route_floor_z": round(route.floor_z, 1),
            "sightline": "INHERITED -- camera and all six actors are points on "
                         "one mined route, which one player walked end to end",
            "cast": [{"name": n, "model": m, "skin": s, "team": t.name,
                      "origin": [round(c, 2) for c in p],
                      "range_units": round(math.dist(camera, p), 1)}
                     for (n, m, s, t), p in zip(CAST, line)]}
    (out_dir / f"{SCENE_ID}.geometry.json").write_text(
        json.dumps(geom, indent=1), encoding="utf-8")
    return demo, geom, camera


def scene(demo: Path, out_dir: Path) -> ConfigScene:
    """Three captures. Only the client colour/force cvars differ."""
    team_c = {f"cg_team{p}Color": format_for(f"cg_team{p}Color", TEAM_TEST)
              for p in ("Legs", "Torso", "Head")}
    enemy_c = {f"cg_enemy{p}Color": format_for(f"cg_enemy{p}Color", ENEMY_TEST)
               for p in ("Legs", "Torso", "Head")}
    cleared = {k: '""' for k in (*team_c, *enemy_c)}
    force_off = {"cg_forceModel": 0, "cg_enemyModel": '""'}
    force_on = {"cg_forceModel": 1, "cg_enemyModel": '"keel/bright"'}

    # Every variant must set the SAME cvar names and differ only in values,
    # or the comparison has more than one moving part.
    keys = {**cleared, **force_off}
    return ConfigScene(
        scene_id=SCENE_ID, source=demo.resolve(),
        start_s=SHOT_START, end_s=SHOT_END,
        base=VisualProfile(name="PROOF_B", extra={
            "r_fastsky": 1,
            # Overkill's top floor is nearly black, and a colour
            # cannot be read off an unlit body. These are LATCHED
            # and identical in every variant, so they raise the
            # exposure without touching the comparison.
            "r_mapOverBrightBits": 2,
            "r_gamma": 1.35,
            "cg_shadows": 0,
        }).without(
            "cg_forceModel", "cg_enemyModel"),
        variants=[
            Variant(label="authored",
                    cvars={**keys},
                    note="every client override cleared: demo-authored truth"),
            Variant(label="client_colours",
                    cvars={**cleared, **team_c, **enemy_c, **force_off},
                    note="team green, enemy magenta -- does the tint follow?"),
            Variant(label="forced_model",
                    cvars={**cleared, **force_on},
                    note="cg_forceModel 1 + cg_enemyModel keel/bright"),
        ],
        truth_reference=out_dir / f"{SCENE_ID}.frametruth.json")


# ── staging ────────────────────────────────────────────────────────────────

def _broadside_line(spots, n: int):
    """A camera, and `n` walked spots CLUSTERED tightly in front of it.

    Spreading the cast across a wide stretch of route kept putting some of them
    behind architecture: two points a player walked between are connected by a
    path, which is not the same as seeing each other. A tight cluster is the
    honest fix -- if the camera can see the middle of it, it can see all of it,
    and the actors still land in separate screen columns at this range.
    """
    step = max(1, len(spots) // 70)
    pool = spots[::step]
    best = None
    for c in pool:
        near = [p for p in pool if 280 < math.dist(c, p) < 560]
        if len(near) < n:
            continue
        mid = tuple(sum(p[i] for p in near) / len(near) for i in range(3))
        yaw = _yaw(c, mid)
        cols = []
        for p in near:
            if math.dist(p, mid) > 340:       # a cluster, not a line
                continue
            x = _screen_x(c, yaw, p)
            if x is None or not 300 < x < W - 300:
                continue
            cols.append((x, p))
        cols.sort()
        picked, last = [], -1e9
        for x, p in cols:
            if x - last >= 170:
                picked.append(p)
                last = x
        if len(picked) >= n:
            spread = (_screen_x(c, yaw, picked[n - 1])
                      - _screen_x(c, yaw, picked[0]))
            if best is None or spread > best[0]:
                best = (spread, c, picked[:n])
    if best is None:                          # pragma: no cover - map-dependent
        raise RuntimeError(f"{MAP}: no camera sees a cluster of {n}")
    return best[1], best[2]


def _off_axis(a, b, p) -> float:
    den = math.dist((a[0], a[1]), (b[0], b[1])) or 1.0
    return abs((b[0] - a[0]) * (a[1] - p[1])
               - (a[0] - p[0]) * (b[1] - a[1])) / den


def _lineup(leg, n: int):
    """`n` walked spots spread across one view, plus a camera that sees them.

    Every spot is a position a real player occupied, so nobody is standing in
    geometry; the camera is the walked point from which the spread is widest.
    """
    best = None
    for c in leg:
        seen = [p for p in leg if 300 < math.dist(c, p) < 1800]
        if len(seen) < n:
            continue
        mid = tuple(sum(p[i] for p in seen) / len(seen) for i in range(3))
        yaw = _yaw(c, mid)
        # keep only what is actually in front of the camera and spread it out
        cols = []
        for p in seen:
            x = _screen_x(c, yaw, p)
            if x is None or not 140 < x < W - 140:
                continue
            cols.append((x, p))
        cols.sort()
        picked, last = [], -1e9
        for x, p in cols:
            if x - last >= 190:
                picked.append(p)
                last = x
        if len(picked) >= n:
            spread = _screen_x(c, yaw, picked[n - 1]) - _screen_x(c, yaw, picked[0])
            if best is None or spread > best[0]:
                best = (spread, picked[:n], c)
    if best is None:                          # pragma: no cover - map-dependent
        raise RuntimeError(f"{MAP}: no camera sees {n} separated walked spots")
    return best[1], best[2]


def _screen_x(camera, yaw_deg: float, point) -> float | None:
    """Horizontal pixel of `point`, through a pinhole at `camera`.

    Enough for placing a sample box on a body; this is not a renderer and does
    not claim to be one.
    """
    dx, dy = point[0] - camera[0], point[1] - camera[1]
    a = math.radians(yaw_deg)
    forward = dx * math.cos(a) + dy * math.sin(a)
    right = -dx * math.sin(a) + dy * math.cos(a)
    if forward <= 40:
        return None
    half = math.tan(math.radians(FOV_X / 2))
    return W / 2 - (right / forward) / half * (W / 2)


def _screen_y(camera, point, *, eye_up: float = 46.0) -> float:
    """Vertical pixel of a standing body's chest at `point`."""
    dz = (point[2] + eye_up) - (camera[2] + eye_up)
    dist = math.dist((camera[0], camera[1]), (point[0], point[1])) or 1.0
    half_y = math.tan(math.radians(FOV_X / 2)) * (H / W)
    return H / 2 - (dz / dist) / half_y * (H / 2)


def _yaw(a, b) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path(".tmp/synthetic"))
    ap.add_argument("--shots", type=Path, default=Path(".tmp/shots/proofb"))
    ap.add_argument("--film", action="store_true")
    args = ap.parse_args()

    demo, geom, camera = build(args.out)
    print(f"demo   : {demo}  ({demo.stat().st_size:,} bytes)")
    print(f"camera : {geom['camera']} yaw={geom['camera_yaw']} fov={FOV_X}")
    for c in geom["cast"]:
        x = _screen_x(camera, geom["camera_yaw"], c["origin"])
        print(f"  {c['name']:24s} {c['model']}/{c['skin']:8s} {c['team']:5s} "
              f"range={c['range_units']:7.1f}  screen_x={x:7.1f}")
    sc = scene(demo, args.out)
    rep = sc.validate(CvarInventory.load())
    print(f"\nvalidated: {len(rep['varying'])} cvars vary, "
          f"latched={rep['latched']}")
    if args.film:
        for m in sc.film(args.shots):
            print(f"filmed : {m}  ({m.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
