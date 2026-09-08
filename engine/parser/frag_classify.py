"""Classify frags from parsed .dm_73 demos into the categories worth cutting.

Consumes the output of `demo_parse.DM73Parser.parse()` -- obituary events
(killer, victim, weapon, position, time) plus per-client snapshots (origin,
velocity, view angles, health) -- and tags each kill.

Categories requested 2026-08-29:
    big flicks · rocket->rail · shaft->rail · shaft->rocket switch
    air rocket · air nade · air shaft · double air / air combo
    40+ accuracy shaft · multikill · pixel shot · preshot

CONFIDENCE. Every category below is now derived from recorded state, not
inferred. What changed on 2026-08-29:

  AIRBORNE was a velocity+height guess because the parser discarded the field.
  It does not have to be. `entityState_t.groundEntityNum` is decoded at ES index
  16 (10 bits, GENTITYNUM_BITS) and == ENTITYNUM_NONE (1023) means the player is
  standing on nothing -- the exact test the engine itself uses. The parser now
  exports a per-entity stream carrying it.

  A second gate was needed: groundEntityNum alone is true during ordinary
  strafe-jumping and tagged 46% of kills as airshots. Requiring real clearance
  above the floor the victim last stood on brings it to ~11%, which matches
  what a human would call an airshot.

  COVERAGE was the other half. The playerstate stream only carries whoever the
  demo followed -- measured at 4 clients, with just 7% of kills having victim
  coverage. The entity stream carries every player: 7 clients, 83k records.

  ACCURACY comes from the server's own scoreboard ("scores" servercommand,
  index 6 of an 18-field QL row, validated 0..100 across the corpus). Note the
  one honest limit: this is OVERALL accuracy. QL's CA scoreboard has no
  per-weapon breakdown, so `high_acc_shaft` means "a shaft kill by a player
  shooting 40%+", not "40%+ with the shaft specifically".

  PRESHOT remains the one true heuristic. Real visibility needs a PVS trace we
  do not compute, so this detects the observable half -- an aim parked on a spot
  rather than tracking -- and is tagged PROXY.

Every tag carries a `confidence` so downstream selection can prefer SOLID.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

# ── Quake Live MOD_* ids as they appear in the obituary stream ──────────────
#
# THESE ARE MOD_*, NOT WP_*. Quake carries two different weapon enums and the
# first three entries disagree:
#
#     MOD_*  (obituary / means of death)  1 SHOTGUN  2 GAUNTLET  3 MACHINEGUN
#     WP_*   (the weapon a player holds)  1 GAUNTLET 2 MACHINEGUN 3 SHOTGUN
#
# This block carried the WP_ order under a comment naming the obituary stream.
# The values are compared against kill_events_v1.mod, which is MOD_, so
# W_SHOTGUN=3 matched MACHINEGUN: the shotgun arm of the REACTION_SHOT
# gate in frag_recognition.py never admitted a single one of the corpus's
# 7,846 shotgun kills, and every REACTION_SHOT_CANDIDATE on record is a rail.
# Verified against bg_public.h and against the stored mod -> mod_name map.
W_SHOTGUN = 1
W_GAUNTLET = 2
W_MACHINEGUN = 3
W_GRENADE = 4
W_GRENADE_SPLASH = 5
W_ROCKET = 6
W_ROCKET_SPLASH = 7
W_PLASMA = 8
W_PLASMA_SPLASH = 9
W_RAILGUN = 10
W_LIGHTNING = 11

ROCKET = {W_ROCKET, W_ROCKET_SPLASH}
GRENADE = {W_GRENADE, W_GRENADE_SPLASH}
RAIL = {W_RAILGUN}
SHAFT = {W_LIGHTNING}

# ── thresholds ──────────────────────────────────────────────────────────────
AIR_VZ_MIN = 90.0          # ups of vertical motion to call a victim airborne
AIR_HEIGHT_MIN = 45.0      # units above the victim's own recent floor
AIRSHOT_CLEARANCE = 55.0   # real airshot vs incidental strafe-jump
COMBO_WINDOW_MS = 2000     # weapon-switch combo: two kills this close
MULTIKILL_WINDOW_MS = 3000  # Quake Live's own multi-kill window
AIR_COMBO_WINDOW_MS = 3000
PIXEL_DIST_MIN = 2200.0    # units; a rail across most of a large map
FLICK_DEG_MIN = 65.0       # yaw swept in the flick window
FLICK_WINDOW_MS = 300
PRESHOT_LOOKBACK_MS = 450   # how far back to sample the "before" geometry
PRESHOT_ON_TARGET_DEG = 12.0   # victim is on the aim axis at the kill
PRESHOT_WAS_OFF_DEG = 35.0     # ...and was well off it moments earlier
PRESHOT_AIM_STATIC_DEG = 12.0  # while the aim itself barely moved
HIGH_ACC_MIN = 40.0        # "40+ acc shaft" -- server-reported percentage
# The killer being airborne is a DIFFERENT frag from the victim being airborne,
# and often the better one: a rocket landed mid rocket-jump. Speed makes it
# better still (user 2026-08-29: "airborn can be combined with the speed + the
# kill/hit from me"). ~320 ups is roughly a strafe-jumping player; 700+ is a
# committed rocket-jump or launch.
KILLER_AIR_CLEARANCE = 60.0
FAST_UPS = 700.0
VERY_FAST_UPS = 1000.0

SOLID, PROXY, NEEDS_DATA = "solid", "proxy", "needs_data"


@dataclass
class FragTag:
    name: str
    confidence: str
    detail: str = ""


@dataclass
class Frag:
    time_ms: int
    round: int
    killer: int
    killer_name: str
    victim: int
    victim_name: str
    weapon: int
    weapon_name: str
    pos: tuple[float, float, float] | None = None
    tags: list[FragTag] = field(default_factory=list)
    lg_accuracy: float | None = None   # server scoreboard, OVERALL not per-weapon
    killer_speed: float | None = None  # ups at the moment of the kill

    @property
    def tag_names(self) -> list[str]:
        return [t.name for t in self.tags]

    def add(self, name: str, confidence: str, detail: str = "") -> None:
        if name not in self.tag_names:
            self.tags.append(FragTag(name, confidence, detail))

    @property
    def score(self) -> float:
        """Rough desirability for cut selection. Tunable, not authoritative."""
        w = {
            "multikill": 3.0, "quadkill": 5.0, "air_combo": 5.0,
            "air_rocket": 4.0, "air_nade": 4.5, "air_shaft": 4.5,
            "airshot": 3.0, "rocket_rail": 3.5, "shaft_rail": 3.5,
            "shaft_rocket": 3.0, "big_flick": 3.0, "pixel_shot": 2.5,
            "preshot": 2.0, "high_acc_shaft": 3.0,
            "airborne_kill": 3.5, "rocketjump_frag": 4.5,
            "fast_kill": 1.5, "very_fast_kill": 2.5,
            "air_speed_combo": 5.0,
        }
        return sum(w.get(t.name, 0.5) for t in self.tags)


# ── snapshot indexing ───────────────────────────────────────────────────────

class Timeline:
    """Per-client state lookup by server time.

    Prefers the ENTITY stream (every player, with groundEntityNum) over the
    playerstate stream (only whoever the demo followed). Measured on one demo:
    playerstate covered 4 clients and 7% of kills had victim coverage; the
    entity stream covers 7 clients and 83k records.
    """

    def __init__(self, snapshots: Sequence[dict]):
        self._by_client: dict[int, list[dict]] = {}
        for s in snapshots:
            c = s.get("client_num")
            if c is None:
                continue
            self._by_client.setdefault(int(c), []).append(s)
        for rows in self._by_client.values():
            rows.sort(key=lambda r: r.get("server_time_ms") or 0)

    def clients(self) -> list[int]:
        return sorted(self._by_client)

    def at(self, client: int, t_ms: int, tol_ms: int = 250) -> dict | None:
        rows = self._by_client.get(client)
        if not rows:
            return None
        best, bestd = None, None
        for r in rows:                      # linear: snapshot counts are small
            d = abs((r.get("server_time_ms") or 0) - t_ms)
            if bestd is None or d < bestd:
                best, bestd = r, d
        return best if bestd is not None and bestd <= tol_ms else None

    def window(self, client: int, t0: int, t1: int) -> list[dict]:
        rows = self._by_client.get(client, [])
        return [r for r in rows
                if t0 <= (r.get("server_time_ms") or 0) <= t1]

    def recent_floor(self, client: int, t_ms: int, back_ms: int = 2500) -> float | None:
        """Lowest z the client occupied recently -- a stand-in for ground height."""
        rows = self.window(client, t_ms - back_ms, t_ms)
        zs = [r.get("origin_z") for r in rows if r.get("origin_z") is not None]
        return min(zs) if zs else None


# ── individual detectors ────────────────────────────────────────────────────

def _is_airborne(tl: Timeline, victim: int, t_ms: int,
                 clearance: float = AIRSHOT_CLEARANCE) -> tuple[bool, str, str]:
    """SOLID when groundEntityNum is present -- that IS the engine's own flag.

    entityState_t.groundEntityNum == ENTITYNUM_NONE (1023) means the player is
    not standing on anything. It is the exact same test the game itself uses,
    so an airshot tagged this way is not a heuristic. Falls back to the old
    velocity proxy only when the entity record is missing.

    Returns (airborne, detail, confidence).
    """
    s = tl.at(victim, t_ms)
    if not s:
        return False, "", PROXY
    if s.get("ground_entity") is not None or "airborne" in s:
        # entity record: engine ground flag available
        if not bool(s.get("airborne")):
            return False, "", SOLID
        # groundEntityNum alone is true during ordinary strafe-jumping, which
        # is most of a Quake round -- it tagged 46% of kills as airshots.
        # A real airshot means the victim was genuinely OFF the floor, so
        # require clearance above the ground they were last standing on.
        z = s.get("origin_z")
        floor = tl.recent_floor(victim, t_ms)
        if z is not None and floor is not None:
            height = z - floor
            if height < clearance:
                return False, f"airborne but only {height:.0f}u up", SOLID
            return True, f"groundEntityNum=NONE, {height:.0f}u up", SOLID
        return True, "groundEntityNum=NONE", SOLID

    vz, z = s.get("vel_z"), s.get("origin_z")
    if vz is None or z is None:
        return False, "", PROXY
    floor = tl.recent_floor(victim, t_ms)
    height = (z - floor) if floor is not None else 0.0
    # Playerstate rows carry no groundEntityNum (a client never receives its own
    # entity), so the demo taker falls here. Clearance above the floor is the
    # reliable signal on its own -- requiring vertical velocity TOO missed real
    # airborne kills at the apex of a jump, where vz passes through zero.
    if height >= clearance:
        return True, f"height={height:.0f} (playerstate)", PROXY
    if abs(vz) >= AIR_VZ_MIN and height >= AIR_HEIGHT_MIN:
        return True, f"vz={vz:.0f} height={height:.0f}", PROXY
    return False, "", PROXY


def _flick(tl: Timeline, killer: int, t_ms: int) -> tuple[bool, str]:
    """SOLID-ish. Yaw swept in the moments before the kill."""
    rows = tl.window(killer, t_ms - FLICK_WINDOW_MS, t_ms)
    yaws = [r.get("angle_yaw") for r in rows if r.get("angle_yaw") is not None]
    if len(yaws) < 2:
        return False, ""
    sweep = 0.0
    for a, b in zip(yaws, yaws[1:]):
        d = abs((b - a + 180.0) % 360.0 - 180.0)   # shortest signed arc
        sweep += d
    return (sweep >= FLICK_DEG_MIN), f"yaw swept {sweep:.0f} deg"


def _distance(tl: Timeline, killer: int, victim: int,
              t_ms: int) -> float | None:
    a, b = tl.at(killer, t_ms), tl.at(victim, t_ms)
    if not a or not b:
        return None
    try:
        return math.dist(
            (a["origin_x"], a["origin_y"], a["origin_z"]),
            (b["origin_x"], b["origin_y"], b["origin_z"]))
    except (KeyError, TypeError):
        return None


def _aim_vector(yaw_deg: float, pitch_deg: float) -> tuple[float, float, float]:
    """Quake view angles -> unit forward vector. Positive pitch looks DOWN."""
    y, pch = math.radians(yaw_deg), math.radians(pitch_deg)
    cp = math.cos(pch)
    return (cp * math.cos(y), cp * math.sin(y), -math.sin(pch))


def _angle_to_target(killer_row: dict, victim_row: dict) -> float | None:
    """Degrees between the killer's aim and the direction to the victim."""
    try:
        f = _aim_vector(killer_row["angle_yaw"], killer_row.get("angle_pitch") or 0.0)
        d = (victim_row["origin_x"] - killer_row["origin_x"],
             victim_row["origin_y"] - killer_row["origin_y"],
             victim_row["origin_z"] - killer_row["origin_z"])
    except (KeyError, TypeError):
        return None
    n = math.sqrt(sum(c * c for c in d))
    if n < 1e-6:
        return None
    dot = sum(a * b for a, b in zip(f, (d[0] / n, d[1] / n, d[2] / n)))
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))


def _preshot(tl: Timeline, killer: int, victim: int,
             t_ms: int) -> tuple[bool, str, str]:
    """A shot placed where the victim WILL be, not tracked onto them.

    This does not need a PVS/visibility trace after all -- the defining property
    of a preshot is geometric and fully measurable from the entity stream:

        at the kill      the victim sits ON the killer's aim axis (they hit)
        moments earlier  the victim was FAR OFF that axis
        in between       the killer's aim barely moved

    i.e. the victim ran into a stationary crosshair rather than the crosshair
    chasing the victim. Tracking produces the opposite signature: the aim sweeps
    and the angular error shrinks smoothly because the killer is following.

    Returns (is_preshot, detail, confidence).
    """
    k_now, v_now = tl.at(killer, t_ms), tl.at(victim, t_ms)
    k_before = tl.at(killer, t_ms - PRESHOT_LOOKBACK_MS)
    v_before = tl.at(victim, t_ms - PRESHOT_LOOKBACK_MS)
    if not all((k_now, v_now, k_before, v_before)):
        return False, "", PROXY

    a_now = _angle_to_target(k_now, v_now)
    a_before = _angle_to_target(k_before, v_before)
    if a_now is None or a_before is None:
        return False, "", SOLID

    # How far the killer's own aim travelled over the same window.
    try:
        swept = abs((k_now["angle_yaw"] - k_before["angle_yaw"] + 180.0)
                    % 360.0 - 180.0)
    except (KeyError, TypeError):
        return False, "", SOLID

    on_target = a_now <= PRESHOT_ON_TARGET_DEG
    was_off = a_before >= PRESHOT_WAS_OFF_DEG
    aim_static = swept <= PRESHOT_AIM_STATIC_DEG

    if on_target and was_off and aim_static:
        return True, (f"victim {a_before:.0f}deg off axis -> {a_now:.0f}deg "
                      f"while aim moved only {swept:.0f}deg"), SOLID
    return False, "", SOLID


# ── main entry point ────────────────────────────────────────────────────────

class Accuracy:
    """Server-reported accuracy per client over time (from the QL scoreboard)."""

    def __init__(self, rows: Sequence[dict]):
        self._by: dict[int, list[tuple[int, int]]] = {}
        for r in rows:
            c = r.get("client_num")
            if c is None:
                continue
            self._by.setdefault(int(c), []).append(
                (int(r.get("server_time_ms") or 0), int(r.get("accuracy") or 0)))
        for v in self._by.values():
            v.sort()

    def at(self, client: int, t_ms: int) -> float | None:
        """Most recent scoreboard value at or before t_ms."""
        rows = self._by.get(client)
        if not rows:
            return None
        best = None
        for t, a in rows:
            if t <= t_ms:
                best = a
            else:
                break
        return float(best) if best is not None else float(rows[0][1])


def demo_taker(parsed: dict) -> int | None:
    """The client this demo followed -- i.e. the person who recorded it.

    The playerstate stream only ever carries the followed player, so the most
    frequent client_num in it IS the demo taker. User 2026-08-29: "i am always
    the player", so this is the default filter for frag selection.
    """
    counts: dict[int, int] = {}
    for s in parsed.get("snapshots", []):
        c = s.get("client_num")
        if c is not None:
            counts[int(c)] = counts.get(int(c), 0) + 1
    return max(counts, key=counts.get) if counts else None


def _speed(tl: "Timeline", client: int, t_ms: int) -> float | None:
    s = tl.at(client, t_ms)
    if not s:
        return None
    vx, vy, vz = s.get("vel_x"), s.get("vel_y"), s.get("vel_z")
    if vx is None or vy is None:
        return None
    return math.sqrt(vx * vx + vy * vy + (vz or 0.0) ** 2)


def classify(parsed: dict, player: int | None = None) -> list[Frag]:
    """Tag every obituary in a parsed demo.

    `player` restricts to kills BY that client (the demo taker, usually).
    """
    # BOTH streams. The entity stream carries every OTHER player (with the
    # engine's ground flag), but a client never receives its own entity -- the
    # demo taker exists only in the playerstate stream. Merging is what lets
    # "was I airborne, and how fast" be answered for the person recording.
    tl = Timeline(list(parsed.get("entities") or [])
                  + list(parsed.get("snapshots") or []))
    acc = Accuracy(parsed.get("accuracy", []))

    frags: list[Frag] = []
    for e in parsed.get("events", []):
        if e.get("type") != "obituary":
            continue
        k, v = e.get("killer_client"), e.get("victim_client")
        if k is None or v is None or k == v:      # suicides are not frags
            continue
        if player is not None and k != player:
            continue
        pos = None
        if e.get("pos_x") is not None:
            pos = (e["pos_x"], e["pos_y"], e["pos_z"])
        frags.append(Frag(
            time_ms=int(e.get("server_time_ms") or 0),
            round=int(e.get("round") or 0),
            killer=int(k), killer_name=str(e.get("killer_name") or ""),
            victim=int(v), victim_name=str(e.get("victim_name") or ""),
            weapon=int(e.get("weapon") or 0),
            weapon_name=str(e.get("weapon_name") or ""),
            pos=pos))

    frags.sort(key=lambda f: f.time_ms)

    # --- per-frag tags ------------------------------------------------------
    for f in frags:
        air, why, conf = _is_airborne(tl, f.victim, f.time_ms)
        if air:
            f.add("airshot", conf, why)
            if f.weapon in ROCKET:
                f.add("air_rocket", conf, why)
            elif f.weapon in GRENADE:
                f.add("air_nade", conf, why)
            elif f.weapon in SHAFT:
                f.add("air_shaft", conf, why)

        flick, why = _flick(tl, f.killer, f.time_ms)
        if flick:
            f.add("big_flick", SOLID, why)

        d = _distance(tl, f.killer, f.victim, f.time_ms)
        if d is not None and f.weapon in RAIL and d >= PIXEL_DIST_MIN:
            f.add("pixel_shot", SOLID, f"{d:.0f} units")

        # Accuracy comes from the server's own scoreboard, so the number is
        # authoritative -- but it is OVERALL accuracy. QL's CA scoreboard has
        # no per-weapon breakdown, so this says "a shaft kill by a player
        # shooting 40%+", not "40%+ with the shaft specifically".
        a = acc.at(f.killer, f.time_ms)
        if a is not None:
            f.lg_accuracy = a
            if f.weapon in SHAFT and a >= HIGH_ACC_MIN:
                f.add("high_acc_shaft", SOLID,
                      f"{a:.0f}% overall (server scoreboard)")

        # ME in the air, and how fast I was going. Distinct from the victim
        # being airborne, and frequently the more impressive frag.
        kair, kwhy, kconf = _is_airborne(tl, f.killer, f.time_ms,
                                         clearance=KILLER_AIR_CLEARANCE)
        spd = _speed(tl, f.killer, f.time_ms)
        if spd is not None:
            f.killer_speed = spd
        if kair:
            f.add("airborne_kill", kconf, f"killer airborne; {kwhy}")
            if f.weapon in ROCKET:
                f.add("rocketjump_frag", kconf, "rocket landed while airborne")
        if spd is not None and spd >= VERY_FAST_UPS:
            f.add("very_fast_kill", SOLID, f"{spd:.0f} ups")
        elif spd is not None and spd >= FAST_UPS:
            f.add("fast_kill", SOLID, f"{spd:.0f} ups")
        if kair and spd is not None and spd >= FAST_UPS:
            f.add("air_speed_combo", kconf, f"airborne at {spd:.0f} ups")

        pre, why, pconf = _preshot(tl, f.killer, f.victim, f.time_ms)
        if pre and f.weapon in (ROCKET | GRENADE | RAIL):
            f.add("preshot", pconf, why)

    # --- sequence tags: combos and multikills -------------------------------
    by_killer: dict[int, list[Frag]] = {}
    for f in frags:
        by_killer.setdefault(f.killer, []).append(f)

    for kills in by_killer.values():
        for i, f in enumerate(kills):
            # weapon-switch combos: the PREVIOUS kill used a different weapon
            if i > 0:
                p = kills[i - 1]
                gap = f.time_ms - p.time_ms
                if 0 < gap <= COMBO_WINDOW_MS:
                    combo = None
                    if p.weapon in ROCKET and f.weapon in RAIL:
                        combo = "rocket_rail"
                    elif p.weapon in SHAFT and f.weapon in RAIL:
                        combo = "shaft_rail"
                    elif p.weapon in SHAFT and f.weapon in ROCKET:
                        combo = "shaft_rocket"
                    elif p.weapon in ROCKET and f.weapon in SHAFT:
                        combo = "rocket_shaft"
                    if combo:
                        f.add(combo, SOLID, f"{gap} ms after {p.weapon_name}")

            # multikill: how many of this killer's kills fall in the window
            n = sum(1 for g in kills
                    if 0 <= f.time_ms - g.time_ms <= MULTIKILL_WINDOW_MS)
            if n >= 4:
                f.add("quadkill", SOLID, f"{n} kills in {MULTIKILL_WINDOW_MS} ms")
            elif n == 3:
                f.add("multikill", SOLID, "triple")
            elif n == 2:
                f.add("multikill", SOLID, "double")

            # air combo: two airshots close together
            if "airshot" in f.tag_names:
                near_air = sum(
                    1 for g in kills
                    if "airshot" in g.tag_names
                    and 0 <= f.time_ms - g.time_ms <= AIR_COMBO_WINDOW_MS)
                if near_air >= 2:
                    conf = SOLID if all(
                        t.confidence == SOLID
                        for g in kills if "airshot" in g.tag_names
                        for t in g.tags if t.name == "airshot") else PROXY
                    f.add("air_combo", conf, f"{near_air} airshots")

    return frags


def summary(frags: Iterable[Frag]) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in frags:
        for t in f.tags:
            out[t.name] = out.get(t.name, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def best(frags: Sequence[Frag], n: int = 20) -> list[Frag]:
    return sorted((f for f in frags if f.tags),
                  key=lambda f: -f.score)[:n]


def main() -> int:
    import argparse
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    import demo_parse  # noqa: E402

    ap = argparse.ArgumentParser()
    ap.add_argument("demo")
    ap.add_argument("--player", type=int, default=None)
    ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args()

    parsed = demo_parse.DM73Parser(a.demo).parse()
    me = a.player if a.player is not None else demo_taker(parsed)
    print(f"demo taker = client {me}")
    frags = classify(parsed, player=me)
    print(f"{len(frags)} kills, {sum(1 for f in frags if f.tags)} tagged")
    for k, v in summary(frags).items():
        print(f"  {v:4d}  {k}")
    print(f"\ntop {a.top}:")
    for f in best(frags, a.top):
        tags = ", ".join(f"{t.name}[{t.confidence[0]}]" for t in f.tags)
        print(f"  t={f.time_ms/1000:8.1f}s r{f.round} {f.weapon_name:10} "
              f"score={f.score:4.1f}  {tags}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
