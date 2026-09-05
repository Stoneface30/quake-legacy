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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("proof", choices=["round_state"])
    ap.add_argument("--out", type=Path, default=Path(".tmp/synthetic"))
    args = ap.parse_args()
    path, scn = round_state_proof(args.out)
    print(f"wrote {path}  ({path.stat().st_size:,} bytes)")
    for row in scn.timeline():
        print(f"   t={row['t']:6.2f}  {row['feature']:16s} "
              f"{ {k: v for k, v in row.items() if k not in ('t', 'feature')} }")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
