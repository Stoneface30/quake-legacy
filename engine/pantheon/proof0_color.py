"""PROOF 0 -- what colour string does this binary actually accept?

THE CONTRADICTION THIS SETTLES. `SC_ParseColorFromStr` rejects any character
that is not a digit or a space, so `cg_whColor` takes `"40 255 40"` -- proven
on frames. The rail path instead goes `SC_Vec3ColorFromCvar` ->
`SC_RedFromCvar`, which reads `cvar->integer`; `Cvar_Set` computes that with
plain `atoi`, and `atoi("0x2a8000")` is 0. Yet `"0x2a8000"` is the shipped
default of `cg_enemyLegsColor`. Those three facts cannot all describe one code
path, and reading further source to choose between them is the move that has
been wrong three times on this project.

So: four values, one cvar, one rail, one camera, one timestamp. Pixels decide.

    0x2a8000     hex, the shipped-default form
    2752512      the same colour as a decimal integer
    "42 128 0"   the same colour as a decimal triple
    (unset)      the shooter's own c1, i.e. the baseline

0x2a8000 and 2752512 are the SAME number written two ways. If hex parses they
render identically; if `atoi` is plain, hex collapses to 0 and they diverge.
That single relationship carries most of the answer.

    python -m engine.pantheon.proof0_color --build
    python -m engine.pantheon.proof0_color --film
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from engine.pantheon.ab_scene import ConfigScene, CvarInventory, Variant
from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.navigation import NavigationTruth
from engine.pantheon.scenario import RoundScenario, Team, Weapon
from engine.pantheon.shot import VisualProfile

SCENE_ID = "PROOF0_COLOR"
# Campgrounds is too constricted for this: a 900-unit beam runs into
# architecture and the room never reads. Overkill's top floor is 304 walked
# points across a 668-unit span at z=936 -- open, high, and every point is
# somewhere a real player stood.
MAP = "overkill"
NAV_CACHE = Path(f".tmp/nav_{MAP}.json")

# The cvar under test. Chosen because its rendering path is registered in the
# 11.3 runtime inventory AND it applies to a TEAMMATE's rail, which the POV
# client resolves without depending on the unproven freecam team semantics.
CVAR = "cg_teamRailColor1"

# One colour, written several ways. 0x2a8000 == 2785280 == (42, 128, 0).
#
# `decimal_int_wrong` is kept deliberately. The first run of this proof used
# 2752512, which is 0x2A0000 -- an arithmetic slip of mine, not the engine's.
# It rendered a dim dark red, and that is EVIDENCE: a wrong number producing
# exactly the colour the 0xRRGGBB model predicts for it is a second, independent
# confirmation of how the string is read. Removing it would throw that away.
FORMS = [
    ("hex", "0x2a8000"),                # 0x2a8000        -> expect (42,128,0)
    ("decimal_int", "2785280"),         # 0x2a8000        -> expect (42,128,0)
    ("decimal_int_wrong", "2752512"),   # 0x2a0000        -> expect (42,0,0)
    ("decimal_triple", '"42 128 0"'),   # atoi -> 42 = 0x00002a -> expect (0,0,42)
    ("unset", '""'),                    # the shooter's own c1
]
EXPECT_RGB = (42, 128, 0)
BASELINE_C1 = "1"        # the shooter's own rail colour, deliberately chosen
                         # to sit far from EXPECT_RGB so "the form worked" and
                         # "nothing happened" cannot look the same

DURATION = 4.5
FIRE_T = 2.0            # when the rail is fired, scenario seconds
SHOT_START, SHOT_END = 1.2, 3.6
BASELINE_OFFSET = 0.3   # seconds into the shot: before the rail exists
RAIL_OFFSET = 0.9       # seconds into the shot: trail is up (600ms lifetime)


def build(out_dir: Path):
    """One shooter, one teammate camera, one rail across open space."""
    nav = NavigationTruth.for_map(MAP, cache=NAV_CACHE)
    leg = nav.high_route().thinned()   # the highest regroup

    # The first take aimed the camera at the SHOOTER, so the beam receded down
    # the view axis and covered about sixty pixels. A colour measurement needs
    # the beam BROADSIDE: camera perpendicular to the shot line, looking at the
    # middle of it, close enough that the trail spans the frame.
    shooter_at, impact, camera = _broadside(leg)

    scn = RoundScenario.clan_arena(map_name=MAP,
                                   hostname="PANTHEON COLOUR PROOF")
    mid = tuple((a + b) / 2 for a, b in zip(shooter_at, impact))
    scn.observer(camera, yaw=_yaw(camera, mid))

    # BOTH on RED. The POV client is a red player, so the shooter's rail is a
    # TEAMMATE rail and cg_teamRailColor1 is the branch that applies.
    # c1 is the shooter's OWN rail colour, which is what the `unset` variant
    # renders. The first take used c1 "6" and came out green-yellow -- the same
    # family as the (42,128,0) test colour, which would have made "this form
    # worked" and "nothing happened" look alike. A far-away baseline is the
    # whole point of having one.
    shooter = scn.actor("SHOOTER", Team.RED).appearance("sarge", "default",
                                                        c1=BASELINE_C1,
                                                        c2=BASELINE_C1)
    # Spawn HOLDING the railgun. The first take spawned with the default
    # rocket launcher, so the shooter swapped weapons on the same frame he
    # fired -- visible, and nothing to do with what is being measured.
    shooter.spawn(shooter_at, yaw=_yaw(shooter_at, impact), t=0.0,
                  weapon=Weapon.RAIL)
    shooter.fire(Weapon.RAIL, impact=impact, t=FIRE_T)
    shooter.stand(until=DURATION - 0.2)

    out_dir.mkdir(parents=True, exist_ok=True)
    demo = scn.compile(duration=DURATION).save(out_dir / f"{SCENE_ID}.dm_73")
    truth = FrameTruth.from_scenario(scn, duration=DURATION)
    truth.save(out_dir / f"{SCENE_ID}.frametruth.json")
    geometry = {"map": MAP, "camera": list(camera),
                "shooter": list(shooter_at), "impact": list(impact),
                "beam_len_units": round(math.dist(shooter_at, impact), 1),
                "camera_offaxis_units": round(
                    _off_axis(shooter_at, impact, camera), 1),
                "fire_t": FIRE_T, "duration_s": DURATION}
    (out_dir / f"{SCENE_ID}.geometry.json").write_text(
        json.dumps(geometry, indent=1), encoding="utf-8")
    return demo, geometry


def scene(demo: Path, out_dir: Path) -> ConfigScene:
    return ConfigScene(
        scene_id=SCENE_ID, source=demo.resolve(),
        start_s=SHOT_START, end_s=SHOT_END,
        # Everything else is held by the profile; only CVAR varies. The base
        # must not pin CVAR, or it would be constant and variable at once.
        base=VisualProfile(name="PROOF0", extra={
            # The measurement is of ONE beam. Anything else that emits light
            # into the frame is noise in the mask.
            "cg_railUseOwnColors": 0,
            "cg_railTrailTime": 600,
            "cg_railFromMuzzle": 1,
            "cg_marks": 0,
            "cg_muzzleFlash": 0,
            "cg_simpleItems": 1,
            "r_fastsky": 1,
        }),
        variants=[Variant(label=name, cvars={CVAR: value},
                          on_screen=f"{CVAR} {value}",
                          note=f"expects {EXPECT_RGB} if this form parses")
                  for name, value in FORMS],
        truth_reference=out_dir / f"{SCENE_ID}.frametruth.json")


def _broadside(leg):
    """Pick (shooter, impact, camera) so the beam crosses the frame sideways.

    All three come from NavigationTruth -- positions real players actually
    walked -- so nothing is standing inside geometry.
    """
    best = None
    for i, a in enumerate(leg):
        for b in leg[i + 1:]:
            span = math.dist(a, b)
            if not 380 < span < 900:
                continue
            m = tuple((x + y) / 2 for x, y in zip(a, b))
            for c in leg:
                off = _off_axis(a, b, c)
                near = math.dist(c, m)
                if not 180 < near < 480:
                    continue
                # want the camera nearly perpendicular to the beam: the
                # off-axis distance should be most of the distance to the mid
                score = off / max(near, 1e-6)
                if best is None or score > best[0]:
                    best = (score, a, b, c)
    if best is None:                      # pragma: no cover - map-dependent
        raise RuntimeError("no broadside camera exists on this route")
    return best[1], best[2], best[3]


def _yaw(a, b) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360


def _off_axis(a, b, p) -> float:
    """Perpendicular distance from p to the line a->b, in map units."""
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    px, py = p[0], p[1]
    den = math.dist((ax, ay), (bx, by)) or 1.0
    return abs((bx - ax) * (ay - py) - (ax - px) * (by - ay)) / den


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path(".tmp/synthetic"))
    ap.add_argument("--shots", type=Path, default=Path(".tmp/shots/proof0"))
    ap.add_argument("--film", action="store_true")
    args = ap.parse_args()

    demo, geom = build(args.out)
    print(f"demo     : {demo}  ({demo.stat().st_size:,} bytes)")
    for k, v in geom.items():
        print(f"  {k:22s} {v}")
    sc = scene(demo, args.out)
    rep = sc.validate(CvarInventory.load())
    print(f"\nvalidated: varying={rep['varying']} "
          f"latched={rep['latched']} "
          f"separate_captures={rep['requires_separate_capture']}")
    for v in rep["variants"]:
        print(f"  {v['label']:16s} {v['cvars']}")
    if args.film:
        made = sc.film(args.shots)
        for m in made:
            print(f"filmed   : {m}  ({m.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
