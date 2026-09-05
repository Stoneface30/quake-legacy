"""ca_explainer_v1 — a Clan Arena round built to teach the mode.

THIS IS NOT A SIMULATION OF A MATCH. It is a round designed so the camera can
explain it: engagements happen one at a time, in places the camera can see,
with enough space between them to read. That is the whole advantage of
synthesis over a recorded round, and it would be wasted on random combat.

WHAT IT TEACHES, IN ORDER
  countdown             -> a round is announced before it starts
  team establishment    -> two teams, four a side IN THIS EXAMPLE
  movement into position-> players take routes, they do not spawn in place
  wall-separated pair   -> two players near each other with no sight of each
                           other; the XRAY teaching beat
  first line of sight   -> the wall stops mattering
  first damage          -> health and armour change
  first kill            -> a body is gone and stays gone
  alive counter         -> 4-3
  team rotation         -> the survivors move
  second engagement     -> 3-3, then 3-2
  numbers advantage     -> 3-1
  final engagement      -> 3-0
  round win             -> the round resolves
  reset                 -> counters rebuild, and it happens again

FOUR A SIDE IS THE EXAMPLE, NOT THE RULE. Real Clan Arena is 4v4 only about
half the time (52% of rosters in this corpus). Any narration over this round
must say "usually four a side", never "Clan Arena is 4v4".

EVERY POSITION IS REAL. Coordinates come from NavigationTruth, which mines
on-ground playerstate origins out of the corpus. Nothing here is a literal.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.navigation import NavigationTruth
from engine.pantheon.scenario import RoundScenario, Team, Weapon

NAV_CACHE = Path(".tmp/nav_campgrounds.json")

# Beats, in seconds. Spaced so a camera can travel between them and a viewer
# can read each one. Nothing here is tight -- a teaching round that needs
# slow-motion to be legible has been authored wrong.
T_ROUND = 6.0            # FIGHT
T_APPROACH = (7.0, 12.0)  # both teams move into position
T_WALL = 12.0            # the wall-separated pair are in place
T_LOS = 14.0             # they step into sight of each other
T_DAMAGE = 15.0
T_KILL_1 = 16.5          # 4-3
T_ROTATE = (17.5, 21.0)
T_KILL_2 = 22.0          # 3-3  (BLUE trades)
T_KILL_3 = 25.0          # 3-2
T_KILL_4 = 28.5          # 3-1
T_KILL_5 = 32.0          # 3-0
T_WIN = 33.0
T_RESET = 36.0
T_END = 40.0


def build(out_dir: Path, *, map_name: str = "campgrounds"
          ) -> tuple[Path, Path, RoundScenario, FrameTruth]:
    nav = NavigationTruth.for_map(map_name, cache=NAV_CACHE)
    route = nav.route()
    spots = nav.standing_positions(9, route=route)
    wall = nav.wall_separated_pair()

    scn = RoundScenario.clan_arena(map_name=map_name,
                                   hostname="PANTHEON CA EXPLAINER v1")

    # The observer watches the middle of the action. A real demo always has a
    # viewpoint; the cinematic camera comes later and replaces what it sees,
    # not what the round is.
    eye = spots[0]
    focus = spots[4]
    scn.observer(eye, yaw=math.degrees(
        math.atan2(focus[1] - eye[1], focus[0] - eye[0])) % 360)

    # -- teams -------------------------------------------------------------
    reds = [scn.actor(f"RED_{i + 1}", Team.RED) for i in range(4)]
    blues = [scn.actor(f"BLUE_{i + 1}", Team.BLUE) for i in range(4)]

    # RED_1 and BLUE_1 are the wall pair when navigation found one; otherwise
    # they take ordinary spots and the XRAY beat is simply not staged. The
    # round still teaches everything else -- a missing candidate must not
    # silently produce a fake one.
    red_start = list(spots[1:5])
    blue_start = list(spots[5:9])
    staged_wall = wall is not None
    if staged_wall:
        red_start[0], blue_start[0] = wall[0], wall[1]

    for a, p in zip(reds, red_start):
        a.spawn(p, yaw=0.0, weapon=Weapon.ROCKET)
    for a, p in zip(blues, blue_start):
        a.spawn(p, yaw=180.0, weapon=Weapon.RAIL)

    scn.begin_round(at=T_ROUND, countdown=6.0)

    # -- movement into position -------------------------------------------
    # Real routes, walked at a readable pace. Sub-routes are taken from the
    # same navigable run so nobody walks through geometry.
    leg = route.thinned()
    if len(leg) >= 6:
        reds[1].move_to(leg[0:4], during=T_APPROACH)
        blues[1].move_to(list(reversed(leg[-4:])), during=T_APPROACH)
        reds[2].move_to(leg[1:5], during=(T_APPROACH[0] + 0.5,
                                          T_APPROACH[1] + 0.5))

    # -- the wall pair, then line of sight ---------------------------------
    reds[0].stand(until=T_WALL)
    blues[0].stand(until=T_WALL)
    if staged_wall and len(leg) >= 3:
        # RED_1 steps out from behind the geometry into BLUE_1's sight
        reds[0].move_to([wall[0], leg[1]], during=(T_WALL, T_LOS))
    reds[0].look_at(blues[0], t=T_LOS + 0.2)
    blues[0].look_at(reds[0], t=T_LOS + 0.2)

    # -- first exchange ----------------------------------------------------
    reds[0].fire(Weapon.ROCKET, at=blues[0], t=T_DAMAGE - 0.4)
    blues[0].take_damage(90, source=reds[0], t=T_DAMAGE)
    reds[0].fire(Weapon.ROCKET, at=blues[0], t=T_KILL_1 - 0.4)
    reds[0].kill(blues[0], mod=Weapon.ROCKET, t=T_KILL_1)          # 4-3

    # -- rotation ----------------------------------------------------------
    if len(leg) >= 6:
        reds[3].move_to(leg[2:6], during=T_ROTATE)
        blues[2].move_to(list(reversed(leg[2:6])), during=T_ROTATE)

    # -- second engagement: BLUE trades ------------------------------------
    blues[1].fire(Weapon.RAIL, at=reds[1], t=T_KILL_2 - 0.4)
    blues[1].kill(reds[1], mod=Weapon.RAIL, t=T_KILL_2)            # 3-3

    reds[2].fire(Weapon.ROCKET, at=blues[1], t=T_KILL_3 - 0.4)
    reds[2].kill(blues[1], mod=Weapon.ROCKET, t=T_KILL_3)          # 3-2

    # -- numbers advantage -------------------------------------------------
    reds[3].fire(Weapon.ROCKET, at=blues[2], t=T_KILL_4 - 0.4)
    reds[3].kill(blues[2], mod=Weapon.ROCKET, t=T_KILL_4)          # 3-1

    # -- final engagement --------------------------------------------------
    blues[3].take_damage(60, source=reds[0], t=T_KILL_5 - 1.5)
    reds[0].fire(Weapon.ROCKET, at=blues[3], t=T_KILL_5 - 0.4)
    reds[0].kill(blues[3], mod=Weapon.ROCKET, t=T_KILL_5)          # 3-0

    scn.round_win(Team.RED, t=T_WIN)
    scn.reset_round(t=T_RESET)
    for a in scn.actors.values():
        if a.alive:
            a.stand(until=T_END - 1.0)

    out_dir.mkdir(parents=True, exist_ok=True)
    demo = scn.compile(duration=T_END).save(out_dir / "ca_explainer_v1.dm_73")
    truth = FrameTruth.from_scenario(scn, duration=T_END)
    truth_path = truth.save(out_dir / "ca_explainer_v1.frametruth.json")
    return demo, truth_path, scn, truth


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("output/synthetic"))
    args = ap.parse_args()
    demo, truth_path, scn, truth = build(args.out)
    print(f"demo   : {demo}  ({demo.stat().st_size:,} bytes)")
    print(f"truth  : {truth_path}  ({len(truth.frames)} frames, "
          f"{truth.duration:.1f}s)")
    print("\nteaching timeline:")
    for row in scn.timeline():
        extra = {k: v for k, v in row.items() if k not in ("t", "feature")}
        print(f"  t={row['t']:6.2f}  {row['feature']:15s} {extra}")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
