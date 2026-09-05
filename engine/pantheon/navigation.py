"""NavigationTruth — valid places to stand, mined from real play.

WHY. Two synthetic proofs in a row rendered nothing because the coordinates
were invented, and an invented position is undebuggable: a model inside a wall,
a model off-screen and a model that was never sent all look identical. Every
position a scenario uses now comes from somewhere a real player actually
stood, so "is this in the world" stops being a question.

WHAT IT OFFERS. Positions on a known floor, contiguous walked routes, and --
for the XRAY teaching beat -- pairs that are near each other but were never
observed on the same floor path, which is the shape of a wall between them.

Names never enter this module's output: a position is three numbers.
"""
from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

Vec3 = tuple[float, float, float]

FRAGS_DB = Path("G:/QUAKE_LEGACY/creative_suite/database/frags_rebuilt.db")

# Two samples closer than this are the same spot for placement purposes.
MIN_SEPARATION = 55.0
FLOOR_BAND = 96.0        # one level spans more than one exact z:
                         # crouching, steps and low ledges all sit
                         # inside what a player calls one floor
# A walked run breaks when the player teleports, falls or changes floor.
MAX_STEP = 90.0
FLOOR_TOLERANCE = 2.0


@dataclass(frozen=True)
class Route:
    """A contiguous run a real player walked. Every point is navigable, and
    consecutive points have line of sight because someone travelled them."""
    points: tuple[Vec3, ...]
    floor_z: float

    def __len__(self) -> int:
        return len(self.points)

    def span(self) -> float:
        return math.dist(self.points[0], self.points[-1])

    def thinned(self, min_gap: float = MIN_SEPARATION) -> list[Vec3]:
        out: list[Vec3] = []
        for p in self.points:
            if all(math.dist(p, q) > min_gap for q in out):
                out.append(p)
        return out


class NavigationTruth:
    """Valid placement for one map, derived from observed play."""

    def __init__(self, map_name: str, routes: Sequence[Route]) -> None:
        self.map_name = map_name
        self.routes = list(routes)
        if not self.routes:
            raise ValueError(f"no navigable routes found for {map_name}")

    # -- construction --------------------------------------------------
    @classmethod
    def from_demo(cls, map_name: str, demo_path: Path) -> "NavigationTruth":
        from engine.parser.demo_parse import DM73Parser
        out = DM73Parser(demo_path).parse()
        samples = [(s["origin_x"], s["origin_y"], s["origin_z"])
                   for s in out["snapshots"]
                   if s["origin_x"] is not None and s["origin_z"] is not None
                   and s.get("airborne") is False]
        return cls(map_name, _split_runs(samples))

    @classmethod
    def for_map(cls, map_name: str, *, cache: Path | None = None
                ) -> "NavigationTruth":
        """Mine the corpus for a demo on this map and derive routes from it."""
        if cache and cache.exists():
            data = json.loads(cache.read_text(encoding="utf-8"))
            if data.get("map") == map_name:
                return cls(map_name, [Route(tuple(map(tuple, r["points"])),
                                            r["floor_z"])
                                      for r in data["routes"]])
        con = sqlite3.connect(f"file:{FRAGS_DB.as_posix()}?mode=ro", uri=True)
        rows = con.execute(
            """select path from demos where map_name=? and gametype='CA'
               and accepted_frags > 5 order by size_bytes limit 6""",
            (map_name,)).fetchall()
        con.close()
        # Merge across several demos. One demo yields only the floors that
        # one recorder happened to walk, which is not enough to find two
        # positions with something between them.
        routes: list[Route] = []
        for (path,) in rows:
            try:
                routes.extend(cls.from_demo(map_name, Path(path)).routes)
            except Exception:
                continue
        if not routes:
            raise ValueError(f"no usable demo found for map {map_name!r}")
        nav = cls(map_name, routes)
        if cache:
            nav.save(cache)
        return nav

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "map": self.map_name,
            "routes": [{"floor_z": r.floor_z,
                        "points": [list(p) for p in r.points]}
                       for r in self.routes]}, indent=1), encoding="utf-8")
        return path

    # -- queries a scenario actually makes ------------------------------
    def longest_route(self) -> Route:
        return max(self.routes, key=len)

    def route(self, *, min_points: int = 4, min_span: float = 200.0) -> Route:
        """A walkable route long enough to move along."""
        good = [r for r in self.routes
                if len(r) >= min_points and r.span() >= min_span]
        if not good:
            return self.longest_route()
        return max(good, key=lambda r: r.span())

    def high_route(self, *, min_points: int = 4, min_span: float = 200.0
                   ) -> Route:
        """The best walkable route on the HIGHEST floor players reached.

        Arena maps are stacked, and the top level is where a map reads as a
        place rather than a corridor: long sightlines, the room visible around
        the actors, and a horizon to put a silhouette against. It is also
        where a rail beam has room to be 900 units long without a pillar in
        it. Every point is still a position a real player stood on, so
        collision is inherited rather than assumed.
        """
        good = [r for r in self.routes
                if len(r) >= min_points and r.span() >= min_span]
        if not good:
            return self.longest_route()
        top = max(r.floor_z for r in good)
        # one "floor" is a band, not an exact height: players crouch, step and
        # ride small ledges within a level
        band = [r for r in good if r.floor_z >= top - FLOOR_BAND]
        return max(band, key=lambda r: r.span())

    def floors(self) -> list[float]:
        """Every distinct floor height, low to high."""
        return sorted({round(r.floor_z, 1) for r in self.routes})

    def standing_positions(self, n: int, *, route: Route | None = None
                           ) -> list[Vec3]:
        """`n` well-separated positions on one floor.

        Taken from a single route so they share a floor and, because a player
        walked between them, sightlines.
        """
        r = route or self.longest_route()
        spots = r.thinned()
        if len(spots) < n:
            raise ValueError(
                f"{self.map_name}: only {len(spots)} separated positions on "
                f"the longest route, need {n}")
        stride = max(1, len(spots) // n)
        return [spots[i * stride] for i in range(n)]

    def los_pair(self) -> tuple[Vec3, Vec3]:
        """Two positions a player walked between -- so they see each other."""
        r = self.route()
        spots = r.thinned()
        return spots[0], spots[min(len(spots) - 1, 3)]

    def wall_separated_pair(self, *, max_gap: float = 600.0,
                            min_gap: float = 120.0
                            ) -> tuple[Vec3, Vec3] | None:
        """Two navigable positions that are close but on DIFFERENT routes.

        The XRAY teaching beat needs a wall between two players. This does not
        trace geometry -- it uses the corpus as the oracle: two spots that are
        spatially near, on the same floor height, yet never appeared in one
        contiguous walked run, are very likely separated by something. It is a
        candidate, and the camera proof confirms it visually before use.
        """
        best: tuple[float, Vec3, Vec3] | None = None
        for i, ra in enumerate(self.routes):
            for rb in self.routes[i + 1:]:
                if abs(ra.floor_z - rb.floor_z) > FLOOR_TOLERANCE:
                    continue
                for pa in ra.thinned(120.0):
                    for pb in rb.thinned(120.0):
                        gap = math.dist(pa, pb)
                        if min_gap <= gap <= max_gap:
                            if best is None or gap < best[0]:
                                best = (gap, pa, pb)
        return None if best is None else (best[1], best[2])

    def summary(self) -> dict:
        return {"map": self.map_name, "routes": len(self.routes),
                "longest_route_points": len(self.longest_route()),
                "floors": sorted({round(r.floor_z, 1) for r in self.routes})[:8]}


def _split_runs(samples: Sequence[Vec3]) -> list[Route]:
    """Break a position stream into contiguous same-floor walked runs."""
    runs: list[list[Vec3]] = []
    cur: list[Vec3] = []
    for p in samples:
        if cur:
            prev = cur[-1]
            if math.dist(prev, p) > MAX_STEP or \
                    abs(prev[2] - p[2]) > FLOOR_TOLERANCE:
                if len(cur) >= 4:
                    runs.append(cur)
                cur = []
        cur.append(p)
    if len(cur) >= 4:
        runs.append(cur)
    return [Route(tuple(r), r[0][2]) for r in runs]
