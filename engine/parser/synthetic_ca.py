"""Build the synthetic Clan Arena demos, starting with the playback proof.

WHY A SEPARATE MODULE. `dm73_write` knows the wire format and nothing about
Quake. This knows about Clan Arena -- who is on which team, where they stand,
what a round looks like -- and nothing about bits. The explainer's
choreography will grow here without the encoder ever changing.

PROVENANCE. Everything this produces is SYNTHETIC_EXPLAINER. It teaches the
rules; it is never career history, never enters a review queue, and never
counts toward a frag total.

    python -m engine.parser.synthetic_ca --out <dir>
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from pathlib import Path

from engine.parser import dm73_write as W

PROVENANCE = "SYNTHETIC_EXPLAINER"

# Configstring indices this file sets. From the format deep dive §3, which is
# the project's authority; not restated as a table anywhere else.
CS_MUSIC = 2
CS_MESSAGE = 3
CS_MOTD = 4
CS_WARMUP = 5
CS_SCORES1, CS_SCORES2 = 6, 7
CS_GAME_VERSION = 12
CS_LEVEL_START_TIME = 13
CS_INTERMISSION = 14
CS_ITEMS = 15
CS_MODELS = 17
CS_SOUNDS = 274
CS_ROUND_STATUS = 661
CS_ROUND_TIME = 662
CS_RED_PLAYERS_LEFT = 663
CS_BLUE_PLAYERS_LEFT = 664

TEAM_RED, TEAM_BLUE = 1, 2

# 20 Hz is what a QL server actually sent; matching it means playback timing,
# interpolation and any later camera work all behave the way they do on a real
# demo rather than on something only this file understands.
SNAPSHOT_HZ = 20
SNAPSHOT_MS = 1000 // SNAPSHOT_HZ


@dataclass
class Player:
    client: int
    name: str
    team: int
    origin: tuple[float, float, float]
    yaw: float = 0.0
    health: int = 200
    armor: int = 100
    weapon: int = 7                    # WP_ROCKET_LAUNCHER
    alive: bool = True

    def state(self) -> dict[int, float]:
        """The packet-entity fields for this player this frame."""
        x, y, z = self.origin
        return {
            W.ES_ETYPE: W.ET_PLAYER,
            W.ES_CLIENTNUM: self.client,
            W.ES_POS_X: x, W.ES_POS_Y: y, W.ES_POS_Z: z,
            W.ES_APOS_YAW: self.yaw,
            W.ES_MODELINDEX: 0,
        }


# Campgrounds is a real CA map in the shipped pool, so the engine has geometry
# to load. The coordinates below are a legible spread around the map centre
# rather than surveyed spawn points: this proof is about whether the engine
# accepts and renders the stream, and a wrong-but-open position proves that
# just as well as a right one. Real spawns come with the teaching round.
#
# OBSERVED positions, not invented ones. These are real on-ground playerstate
# origins parsed out of a campgrounds demo in the corpus (`Demo (334) - 197`),
# all on the same upper floor at z=538, so they are guaranteed to be in open,
# collision-valid space.
#
# The first attempt guessed coordinates and stood the teams 1,800 units apart
# at z=200. Nothing rendered, and an absent model looks exactly like one
# embedded in a wall or standing off-screen -- which is why the guess could
# not be debugged. A position the engine has already walked a player through
# removes the whole question.
FLOOR_Z = 538.1
RED_START = [(-1602.4, 360.9, FLOOR_Z), (-1460.9, 397.8, FLOOR_Z),
             (-1430.1, 420.7, FLOOR_Z), (-1328.3, 347.1, FLOOR_Z)]
BLUE_START = [(-1240.0, 400.0, FLOOR_Z), (-1164.4, 364.8, FLOOR_Z),
              (-1100.0, 410.0, FLOOR_Z), (-1040.0, 350.0, FLOOR_Z)]

# The camera stands east of the line and looks west along it, so every other
# player is in front of it from the first frame.
CAMERA_START = (-820.0, 380.0, FLOOR_Z)
CAMERA_YAW = 180.0                     # 0=+X, 90=+Y, 180=-X, 270=-Y


def make_players() -> list[Player]:
    out: list[Player] = []
    for i, pos in enumerate(RED_START):
        out.append(Player(i, f"RED_{i + 1}", TEAM_RED, pos, yaw=270.0))
    for i, pos in enumerate(BLUE_START):
        out.append(Player(4 + i, f"BLUE_{i + 1}", TEAM_BLUE, pos, yaw=90.0))
    return out


def configstrings(players: list[Player], *, mapname: str,
                  level_start_ms: int) -> dict[int, str]:
    cs: dict[int, str] = {
        W.CS_SERVERINFO: W.serverinfo(
            mapname, gametype=4, hostname="PANTHEON SYNTHETIC EXPLAINER",
            maxclients=16),
        W.CS_SYSTEMINFO: W.systeminfo(pure=0),
        CS_MESSAGE: "PANTHEON synthetic Clan Arena explainer",
        CS_MOTD: PROVENANCE,
        CS_WARMUP: "0",
        CS_SCORES1: "0",
        CS_SCORES2: "0",
        CS_GAME_VERSION: "baseq3-1",
        CS_LEVEL_START_TIME: str(level_start_ms),
        CS_INTERMISSION: "0",
        CS_ITEMS: "0" * 64,
        CS_ROUND_STATUS: "",
        CS_ROUND_TIME: "0",
        CS_RED_PLAYERS_LEFT: "4",
        CS_BLUE_PLAYERS_LEFT: "4",
    }
    for p in players:
        cs[W.CS_PLAYERS + p.client] = W.player_configstring(
            p.name, team=p.team, model="sarge")
    return cs


def build_playback_proof(out_dir: Path, *, mapname: str = "campgrounds",
                         seconds: float = 8.0,
                         follow: int = 0) -> Path:
    """SYNTHETIC_DEMO_PLAYBACK_PROOF_01.

    Eight players on correct teams, a real serverTime progression at 20 Hz,
    and one player walking a straight line so that movement is unambiguous
    when the engine renders it. No combat: this proof answers whether Wolfcam
    opens the file, advances its timeline and draws players, and nothing else.
    """
    players = make_players()
    level_start = 0
    # The followed client is the camera. It starts east of the line looking
    # west, so all eight bodies are in frame from the first snapshot.
    cam = players[0]
    cam.origin = CAMERA_START
    cam.yaw = CAMERA_YAW
    d = W.DemoWriter(client_num=follow)
    d.write_gamestate(configstrings(players, mapname=mapname,
                                    level_start_ms=level_start))
    d.write_server_command(1, 'print "PANTHEON SYNTHETIC CA EXPLAINER\n"')

    frames = int(seconds * SNAPSHOT_HZ)
    mover = players[follow]
    x0, y0, z0 = mover.origin
    for f in range(frames):
        t = 1000 + f * SNAPSHOT_MS
        # a straight walk WEST at the engine's base run speed, so the distance
        # covered on screen is a number we can actually check: 320 u/s
        dx = -320.0 * (f * SNAPSHOT_MS / 1000.0)
        mover.origin = (x0 + dx, y0, z0)
        ps = {
            W.PS_CLIENTNUM: mover.client,
            W.PS_ORIGIN_X: mover.origin[0],
            W.PS_ORIGIN_Y: mover.origin[1],
            W.PS_ORIGIN_Z: mover.origin[2],
            W.PS_VEL_X: -320.0, W.PS_VEL_Y: 0.0, W.PS_VEL_Z: 0.0,
            W.PS_YAW: mover.yaw, W.PS_PITCH: 0.0,
            W.PS_WEAPON: mover.weapon,
            W.PS_GROUND: 0,
        }
        ents = {p.client: p.state() for p in players}
        d.write_snapshot(t, ps, ents,
                         stats={W.STAT_HEALTH: mover.health,
                                W.STAT_ARMOR: mover.armor})

    out_dir.mkdir(parents=True, exist_ok=True)
    return d.save(out_dir / "SYNTHETIC_DEMO_PLAYBACK_PROOF_01.dm_73")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("output/synthetic"))
    ap.add_argument("--map", default="campgrounds")
    ap.add_argument("--seconds", type=float, default=8.0)
    args = ap.parse_args()
    path = build_playback_proof(args.out, mapname=args.map,
                                seconds=args.seconds)
    print(f"wrote {path}  ({path.stat().st_size:,} bytes)")

    from engine.parser.demo_parse import DM73Parser
    out = DM73Parser(path).parse()
    print(f"  parsed : map={out['map']} gametype={out['gametype']} "
          f"players={len(out['players'])} snapshots={out['snapshot_count']} "
          f"errors={out['packet_errors']}")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
