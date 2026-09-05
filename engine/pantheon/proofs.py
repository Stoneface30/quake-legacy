"""Protocol proofs, authored through RoundScenario.

Each one answers a single question about whether the engine accepts what the
compiler emits. They are fixtures, not films.

    python -m engine.pantheon.proofs round_state --out <dir>
"""
from __future__ import annotations

import argparse
from pathlib import Path

from engine.pantheon.navigation import NavigationTruth
from engine.pantheon.scenario import RoundScenario, Team, Weapon

NAV_CACHE = Path(".tmp/nav_campgrounds.json")


def round_state_proof(out_dir: Path, *, map_name: str = "campgrounds"):
    """SYNTHETIC_ROUND_STATE_PROOF_04.

    4v4, the countdown, the alive ramp to 4/4, four deaths decrementing the
    counters, a round win and a reset that rebuilds the ramp. No choreography
    beyond what the round state needs -- this exists to prove the HUD.
    """
    import math
    nav = NavigationTruth.for_map(map_name, cache=NAV_CACHE)
    route = nav.route()
    spots = nav.standing_positions(9, route=route)

    scn = RoundScenario.clan_arena(map_name=map_name,
                                   hostname="PANTHEON ROUND STATE PROOF")
    # The observer looks at the actors. A viewpoint with an arbitrary yaw
    # renders a wall, and a wall proves nothing about whether the round state
    # reached the HUD.
    eye = spots[0]
    cx = sum(p[0] for p in spots[1:9]) / 8
    cy = sum(p[1] for p in spots[1:9]) / 8
    scn.observer(eye, yaw=math.degrees(math.atan2(cy - eye[1], cx - eye[0])) % 360)

    reds, blues = [], []
    for i in range(4):
        a = scn.actor(f"RED_{i + 1}", Team.RED)
        a.spawn(spots[1 + i], yaw=90.0, weapon=Weapon.ROCKET)
        reds.append(a)
    for i in range(4):
        a = scn.actor(f"BLUE_{i + 1}", Team.BLUE)
        a.spawn(spots[5 + i], yaw=270.0, weapon=Weapon.RAIL)
        blues.append(a)

    scn.begin_round(at=2.0, countdown=2.0)

    # four deaths, alternating, so both counters visibly move
    reds[0].kill(blues[0], mod=Weapon.ROCKET, t=5.0)     # 4-3
    blues[1].kill(reds[1], mod=Weapon.RAIL, t=7.0)       # 3-3
    reds[2].kill(blues[1], mod=Weapon.ROCKET, t=9.0)     # 3-2
    reds[2].kill(blues[2], mod=Weapon.ROCKET, t=11.0)    # 3-1
    reds[3].kill(blues[3], mod=Weapon.RAIL, t=13.0)      # 3-0

    scn.round_win(Team.RED, t=13.5)
    scn.reset_round(t=16.0)

    for a in list(scn.actors.values()):
        if a.alive:
            a.stand(until=19.0)

    writer = scn.compile(duration=21.0)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = writer.save(out_dir / "SYNTHETIC_ROUND_STATE_PROOF_04.dm_73")
    return path, scn


def animation_proof(out_dir: Path, *, map_name: str = "campgrounds"):
    """SYNTHETIC_ANIMATION_PROOF_05 -- one actor, alone, at a readable distance.

    The earlier attempt put the actor among seven others on the same route, so
    the bodies overlapped and nothing could be judged. Here there is exactly
    one actor, the camera stands back along the same walked route, and the
    beats are long enough that consecutive frames land inside one phase.

        0.0-2.0  IDLE
        2.0-6.0  RUN along a real route
        6.0-7.5  IDLE (stopped)
        7.5-9.0  ATTACK
        9.0-10.5 IDLE
    """
    import math
    nav = NavigationTruth.for_map(map_name, cache=NAV_CACHE)
    route = nav.route()
    leg = route.thinned()

    scn = RoundScenario.clan_arena(map_name=map_name,
                                   hostname="PANTHEON ANIMATION PROOF")
    # The first attempt used the two ends of a 966-unit route, which put the
    # actor about 900 units away -- a speck. Pick a viewpoint roughly 260
    # units from where the actor will be: close enough that legs and torso
    # read, far enough that the whole body stays in frame.
    start = leg[2]
    ideal = 260.0
    eye = min((p for p in leg if math.dist(p, start) > 120.0),
              key=lambda p: abs(math.dist(p, start) - ideal), default=leg[-1])
    scn.observer(eye, yaw=math.degrees(
        math.atan2(start[1] - eye[1], start[0] - eye[0])) % 360)

    actor = scn.actor("RED_1", Team.RED)
    actor.spawn(start, yaw=math.degrees(
        math.atan2(eye[1] - start[1], eye[0] - start[0])) % 360,
        weapon=Weapon.ROCKET)
    actor.stand(until=2.0)
    # a short run, so the actor stays near the camera through the whole cycle
    run_leg = [p for p in leg if math.dist(p, start) < 300.0][:4] or leg[2:5]
    actor.move_to(run_leg, start=2.0)
    actor.stand(until=7.5)
    actor.fire(Weapon.ROCKET, t=7.5)
    actor.stand(until=10.5)

    writer = scn.compile(duration=11.0)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = writer.save(out_dir / "SYNTHETIC_ANIMATION_PROOF_05.dm_73")
    return path, scn


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("proof", choices=["round_state", "animation"])
    ap.add_argument("--out", type=Path, default=Path(".tmp/synthetic"))
    args = ap.parse_args()
    path, scn = (round_state_proof(args.out) if args.proof == "round_state"
                 else animation_proof(args.out))
    print(f"wrote {path}  ({path.stat().st_size:,} bytes)")
    for row in scn.timeline():
        print(f"   t={row['t']:6.2f}  {row['feature']:16s} "
              f"{ {k: v for k, v in row.items() if k not in ('t', 'feature')} }")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
