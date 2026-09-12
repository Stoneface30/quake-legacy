"""Frag SHAPES -- what a kill looked like, beyond what the recogniser scored.

The existing recogniser measures what the SHOOTER did: flicks, speed,
multikills, low HP. A survey of Quake community sources against it found the
blind spots are what happened to the VICTIM (1 of 11 shapes detected) and what
happened AFTER (0 of 10). Those are the shapes that read on screen with no
explanation -- a body punted into a pit, a rocket that lands after its owner is
already dead, two rockets crossing with only one arriving.

This module detects those, from tables that already exist. No demo re-scan.

PROVENANCE. Every shape here is RECORDED or DERIVED, never invented:

  * positions are DELTA-COMPRESSED in the wire format -- a coordinate is only
    sent when it changes -- so a single event row often has a null y or z.
    `_Positions` forward-fills per client, which is reconstruction, not
    observation. Any shape whose evidence depends on a forward-filled
    coordinate says so in its `basis` field.
  * damage attribution splits by weapon. Rocket, grenade and plasma carry
    their owner on the missile entity (`other` = otherEntityNum). Lightning,
    rail, machinegun and shotgun carry nothing, so attributing those is
    inference and is labelled `INFERRED`.
  * enemy health comes from pain events carrying health-AFTER. Where the
    recorder lost sight there are no pain events, and the shape is simply not
    emitted rather than estimated.

Nothing here writes to an existing table. Shapes land in `frag_shapes_v1`.
"""
from __future__ import annotations

import collections
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store (rule HL-9).
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
RECOGNITION_DB = REPO_ROOT / "creative_suite/database/frag_recognition.db"

SCHEMA_VERSION = 1

# bg_public.h. Splash radii are the values g_missile.c passes to
# G_RadiusDamage, not guesses.
WEAPON_GAUNTLET, WEAPON_MACHINEGUN, WEAPON_SHOTGUN = 1, 2, 3
WEAPON_GRENADE, WEAPON_ROCKET, WEAPON_LIGHTNING = 4, 5, 6
WEAPON_RAILGUN, WEAPON_PLASMA, WEAPON_BFG = 7, 8, 9

SPLASH_RADIUS = {WEAPON_ROCKET: 120.0, WEAPON_GRENADE: 150.0,
                 WEAPON_PLASMA: 20.0, WEAPON_BFG: 120.0}
GRENADE_FUSE_MS = 2500

# One snapshot is 25 ms; "the same tick" has to tolerate one of them.
TICK_MS = 25


@dataclass
class Shape:
    """One detected shape on one kill or moment."""

    content_hash: str
    server_time_ms: int
    round_no: int | None
    shape: str
    actor: int | None                 # client slot, never a name
    victim: int | None
    basis: str                        # RECORDED | DERIVED | INFERRED
    evidence: dict[str, Any] = field(default_factory=dict)

    def row(self):
        return (self.content_hash, self.server_time_ms, self.round_no,
                self.shape, self.actor, self.victim, self.basis,
                json.dumps(self.evidence, sort_keys=True), SCHEMA_VERSION)


DDL = """
CREATE TABLE IF NOT EXISTS frag_shapes_v1 (
    content_hash   TEXT NOT NULL,
    server_time_ms INTEGER NOT NULL,
    round_no       INTEGER,
    shape          TEXT NOT NULL,
    actor          INTEGER,
    victim         INTEGER,
    basis          TEXT NOT NULL,
    evidence       TEXT,
    version        INTEGER NOT NULL,
    PRIMARY KEY (content_hash, server_time_ms, shape, actor, victim)
);
CREATE INDEX IF NOT EXISTS ix_shapes_shape ON frag_shapes_v1(shape);
CREATE INDEX IF NOT EXISTS ix_shapes_hash ON frag_shapes_v1(content_hash);
"""


class _Positions:
    """Forward-filled positions per client.

    The wire format only sends a coordinate when it changes, so most event
    rows carry a partial position. Filling forward from the last known value
    is a RECONSTRUCTION: it is right while a player is standing still and
    increasingly wrong the longer since the last update. Every consumer here
    records `stale_ms` so a shape built on an old fix can be judged.
    """

    __slots__ = ("_last",)

    def __init__(self):
        self._last: dict[int, tuple[int, float, float, float]] = {}

    def feed(self, client, t_ms, x, y, z):
        if client is None:
            return
        prev = self._last.get(client)
        px, py, pz = (prev[1], prev[2], prev[3]) if prev else (None, None, None)
        nx = x if x is not None else px
        ny = y if y is not None else py
        nz = z if z is not None else pz
        if nx is None or ny is None or nz is None:
            return
        self._last[client] = (t_ms, float(nx), float(ny), float(nz))

    def at(self, client, t_ms):
        """(x, y, z, stale_ms) or None if this client was never located."""
        p = self._last.get(client)
        if not p:
            return None
        return p[1], p[2], p[3], t_ms - p[0]


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def _connect(db=None):
    c = sqlite3.connect("file:%s?mode=ro" % (db or RECOGNITION_DB), uri=True,
                        timeout=60)
    c.row_factory = sqlite3.Row
    return c


# ── shapes ─────────────────────────────────────────────────────────────────

def ring_out(c, ch) -> list[Shape]:
    """The kill IS the push: knockback throws them into a pit, lava or slime.

    The obituary credits the WORLD, so every obituary-driven detector drops
    these silently. Credit goes to whoever last hurt them, and only when a
    real hit is there to point at -- otherwise it was their own mistake and
    nobody gets it.
    """
    out = []
    env = c.execute(
        "SELECT server_time_ms, round, victim_client, mod_name FROM "
        "kill_events_v1 WHERE content_hash=? AND death_cause='ENVIRONMENT' "
        "AND is_best_observation=1 ORDER BY server_time_ms", (ch,)).fetchall()
    if not env:
        return out
    for k in env:
        t, vic = k["server_time_ms"], k["victim_client"]
        # Their last observed pain before falling, and who owned the missile.
        pains = c.execute(
            "SELECT server_time_ms, parm FROM semantic_events_v1 WHERE "
            "content_hash=? AND type='pain' AND client_num=? AND "
            "server_time_ms BETWEEN ? AND ? ORDER BY server_time_ms DESC "
            "LIMIT 1", (ch, vic, t - 3000, t)).fetchall()
        if not pains:
            continue                       # walked in by themselves
        hit_ms = pains[0]["server_time_ms"]
        pusher = c.execute(
            "SELECT m.other AS owner, m.weapon FROM missile_samples_v1 m WHERE "
            "m.content_hash=? AND m.other IS NOT NULL AND m.server_time_ms "
            "BETWEEN ? AND ? ORDER BY m.server_time_ms DESC LIMIT 1",
            (ch, hit_ms - 400, hit_ms + 100)).fetchone()
        out.append(Shape(
            ch, t, k["round"], "RING_OUT",
            pusher["owner"] if pusher else None, vic,
            "DERIVED" if pusher else "RECORDED",
            {"death_mod": k["mod_name"], "last_hit_ms": hit_ms,
             "hit_to_death_ms": t - hit_ms,
             "push_weapon": pusher["weapon"] if pusher else None,
             "note": ("the obituary credits the world; the pusher is derived "
                      "from the last hit before the fall")}))
    return out


def collateral_and_split(c, ch) -> list[Shape]:
    """Two deaths at once.

    COLLATERAL_DAMAGE is one splash killing two. SPLIT_TICK_DOUBLE is two
    SEPARATE shots landing within a couple of snapshots -- a different and
    arguably harder thing, so they are not merged.
    """
    out = []
    kills = c.execute(
        "SELECT server_time_ms, round, killer_client, victim_client, mod_name "
        "FROM kill_events_v1 WHERE content_hash=? AND death_cause="
        "'PLAYER_KILL' AND is_best_observation=1 ORDER BY server_time_ms",
        (ch,)).fetchall()
    by_killer = collections.defaultdict(list)
    for k in kills:
        by_killer[k["killer_client"]].append(k)

    for killer, ks in by_killer.items():
        for i in range(len(ks) - 1):
            a, b = ks[i], ks[i + 1]
            gap = b["server_time_ms"] - a["server_time_ms"]
            if gap > 150 or a["victim_client"] == b["victim_client"]:
                continue
            splash = {"ROCKET_SPLASH", "GRENADE_SPLASH", "PLASMA_SPLASH"}
            same_splash = (a["mod_name"] == b["mod_name"]
                           and a["mod_name"] in splash and gap <= TICK_MS * 2)
            out.append(Shape(
                ch, a["server_time_ms"], a["round"],
                "COLLATERAL_DAMAGE" if same_splash else "SPLIT_TICK_DOUBLE",
                killer, a["victim_client"], "RECORDED",
                {"second_victim": b["victim_client"], "gap_ms": gap,
                 "mod": a["mod_name"], "second_mod": b["mod_name"]}))
    return out


def from_the_grave(c, ch) -> list[Shape]:
    """Your rocket was already in the air when you died, and it still killed.

    Both halves are recorded: the missile carries its owner, and both deaths
    are obituaries. Nothing is inferred except that the missile which killed
    is the one we tracked, which the entity number settles.
    """
    out = []
    deaths = {}
    for r in c.execute("SELECT server_time_ms, client_num FROM "
                       "semantic_events_v1 WHERE content_hash=? AND "
                       "type IN ('death','gib_player') AND client_num IS NOT NULL",
                       (ch,)):
        deaths.setdefault(r["client_num"], []).append(r["server_time_ms"])

    kills = c.execute(
        "SELECT server_time_ms, round, killer_client, victim_client, mod_name "
        "FROM kill_events_v1 WHERE content_hash=? AND death_cause="
        "'PLAYER_KILL' AND is_best_observation=1 AND mod_name IN ('ROCKET','ROCKET_SPLASH','GRENADE',"
        "'GRENADE_SPLASH','PLASMA','PLASMA_SPLASH') ORDER BY server_time_ms",
        (ch,)).fetchall()
    for k in kills:
        killer, t = k["killer_client"], k["server_time_ms"]
        own = [d for d in deaths.get(killer, []) if d < t]
        if not own:
            continue
        killer_died = max(own)
        if not (0 < t - killer_died <= 3000):
            continue
        # The missile has to predate the death, or this is just a fast respawn.
        spawn = c.execute(
            "SELECT MIN(server_time_ms) s FROM missile_samples_v1 WHERE "
            "content_hash=? AND other=? AND server_time_ms BETWEEN ? AND ?",
            (ch, killer, killer_died - 4000, killer_died)).fetchone()
        if not spawn or spawn["s"] is None:
            continue
        out.append(Shape(
            ch, t, k["round"], "FROM_THE_GRAVE", killer, k["victim_client"],
            "RECORDED",
            {"killer_died_ms": killer_died, "missile_spawn_ms": spawn["s"],
             "kill_after_death_ms": t - killer_died, "mod": k["mod_name"]}))
    return out


def orphaned_projectile(c, ch) -> list[Shape]:
    """They died with their own shot still in the air.

    In a Clan Arena teamfight somebody dies mid-rocket constantly, so the bare
    fact is NOT interesting and is not called a denial. What separates the two
    is where the orphaned missile was going: if it was travelling at the
    person who killed them, the kill genuinely took the shot off the board.
    That is `SHOT_DENIED`; everything else stays the plain observation.
    """
    out = []
    kills = c.execute(
        "SELECT server_time_ms, round, killer_client, victim_client FROM "
        "kill_events_v1 WHERE content_hash=? AND death_cause='PLAYER_KILL' "
        "AND is_best_observation=1 "
        "ORDER BY server_time_ms", (ch,)).fetchall()
    if not kills:
        return out
    pos = _Positions()
    _cursor = 0
    events = c.execute(
        "SELECT server_time_ms, client_num, x, y, z FROM semantic_events_v1 "
        "WHERE content_hash=? AND x IS NOT NULL ORDER BY server_time_ms",
        (ch,)).fetchall()
    for k in kills:
        while _cursor < len(events) and                 events[_cursor]["server_time_ms"] <= k["server_time_ms"]:
            e = events[_cursor]
            pos.feed(e["client_num"], e["server_time_ms"], e["x"], e["y"], e["z"])
            _cursor += 1
        vic, t = k["victim_client"], k["server_time_ms"]
        live = c.execute(
            "SELECT entity_num, MIN(server_time_ms) spawn, MAX(server_time_ms) "
            "last, weapon FROM missile_samples_v1 WHERE content_hash=? AND "
            "other=? AND server_time_ms BETWEEN ? AND ? GROUP BY entity_num",
            (ch, vic, t - 3000, t + 3000)).fetchall()
        for m in live:
            if not (m["spawn"] < t < m["last"]):
                continue
            if m["last"] - t < 200:
                continue          # it was landing anyway; nothing was denied
            if t - m["spawn"] > 2500:
                continue          # too long in the air: a recycled entity num
            # It must not already have hit something before the kill.
            spent = c.execute(
                "SELECT 1 FROM semantic_events_v1 WHERE content_hash=? AND "
                "type='missile_hit' AND entity_num=? AND server_time_ms "
                "BETWEEN ? AND ? LIMIT 1", (ch, m["entity_num"], m["spawn"], t)
            ).fetchone()
            if spent:
                continue
            # Was it flying AT the person who killed them?
            aimed, cos_a = None, None
            samp = c.execute(
                "SELECT x,y,z,vx,vy,vz FROM missile_samples_v1 WHERE "
                "content_hash=? AND entity_num=? AND server_time_ms<=? AND "
                "x IS NOT NULL AND y IS NOT NULL AND z IS NOT NULL AND vx IS NOT "
                "NULL AND vy IS NOT NULL AND vz IS NOT NULL ORDER BY "
                "server_time_ms DESC "
                "LIMIT 1", (ch, m["entity_num"], t)).fetchone()
            kp = pos.at(k["killer_client"], t) if pos else None
            usable = samp and None not in (
                samp["x"], samp["y"], samp["z"], samp["vx"], samp["vy"],
                samp["vz"])
            if usable and kp and kp[3] <= 500:
                to = (kp[0] - samp["x"], kp[1] - samp["y"], kp[2] - samp["z"])
                v = (samp["vx"], samp["vy"], samp["vz"])
                nt = sum(q * q for q in to) ** 0.5
                nv = sum(q * q for q in v) ** 0.5
                if nt > 1 and nv > 1:
                    cos_a = sum(to[i] * v[i] for i in range(3)) / (nt * nv)
                    aimed = cos_a > 0.87          # within ~30 degrees
            out.append(Shape(
                ch, t, k["round"],
                "SHOT_DENIED" if aimed else "DIED_WITH_SHOT_IN_FLIGHT",
                k["killer_client"], vic,
                "DERIVED" if aimed is not None else "RECORDED",
                {"their_missile_spawn_ms": m["spawn"],
                 "their_missile_last_ms": m["last"],
                 "weapon": m["weapon"],
                 "flight_left_ms": m["last"] - t,
                 "aimed_at_killer": aimed,
                 "cos_to_killer": round(cos_a, 3) if cos_a is not None else None,
                 "note": ("aim is judged from the missile velocity against a "
                          "forward-filled killer position; null means the "
                          "killer was not locatable and no claim is made")}))
            break
    return out


def point_blank_and_range(c, ch) -> list[Shape]:
    """Range at the moment of the kill: contact-range, and the far end.

    Range is DERIVED -- both endpoints come from forward-filled positions, and
    `stale_ms` says how old the fixes were. A shape built on a 2-second-old
    position is not evidence, so those are dropped.
    """
    out = []
    pos = _Positions()
    kills = {}
    for k in c.execute("SELECT server_time_ms, round, killer_client, "
                       "victim_client, mod_name FROM kill_events_v1 WHERE "
                       "content_hash=? AND death_cause='PLAYER_KILL' AND is_best_observation=1", (ch,)):
        kills.setdefault(k["server_time_ms"], []).append(k)

    for e in c.execute("SELECT server_time_ms, type, client_num, x, y, z FROM "
                       "semantic_events_v1 WHERE content_hash=? AND x IS NOT NULL "
                       "ORDER BY server_time_ms", (ch,)):
        pos.feed(e["client_num"], e["server_time_ms"], e["x"], e["y"], e["z"])
        for k in kills.pop(e["server_time_ms"], []):
            a = pos.at(k["killer_client"], e["server_time_ms"])
            b = pos.at(k["victim_client"], e["server_time_ms"])
            if not a or not b:
                continue
            stale = max(a[3], b[3])
            if stale > 500:               # too old to call it a position
                continue
            d = _dist(a[:3], b[:3])
            mod = k["mod_name"]
            shape = None
            if d < 150 and mod in ("ROCKET", "SHOTGUN", "ROCKET_SPLASH"):
                shape = "POINT_BLANK"
            elif mod == "SHOTGUN" and d > 1200:
                shape = "SHOTGUN_SNIPE"
            elif abs(a[2] - b[2]) > 400 and abs(a[2] - b[2]) > 0.8 * d:
                shape = "PLUNGE_KILL" if a[2] > b[2] else "UPSHOT_KILL"
            if shape:
                out.append(Shape(
                    ch, k["server_time_ms"], k["round"], shape,
                    k["killer_client"], k["victim_client"], "DERIVED",
                    {"range_u": round(d, 1), "dz": round(a[2] - b[2], 1),
                     "mod": mod, "position_stale_ms": stale}))
    return out


def gauntlet_interrupt(c, ch) -> list[Shape]:
    """Melee on someone who was actively shooting -- walking into a live
    weapon and winning. The loudest insult in the game."""
    out = []
    for k in c.execute(
            "SELECT server_time_ms, round, killer_client, victim_client FROM "
            "kill_events_v1 WHERE content_hash=? AND mod_name='GAUNTLET' "
            "AND is_best_observation=1",
            (ch,)):
        t, vic = k["server_time_ms"], k["victim_client"]
        fired = c.execute(
            "SELECT COUNT(*) n FROM semantic_events_v1 WHERE content_hash=? AND "
            "type='fire_weapon' AND client_num=? AND server_time_ms BETWEEN ? "
            "AND ?", (ch, vic, t - 700, t)).fetchone()["n"]
        hurt_me = c.execute(
            "SELECT COUNT(*) n FROM semantic_events_v1 WHERE content_hash=? AND "
            "type='pain' AND client_num=? AND server_time_ms BETWEEN ? AND ?",
            (ch, k["killer_client"], t - 700, t)).fetchone()["n"]
        if fired:
            out.append(Shape(
                ch, t, k["round"], "GAUNTLET_INTERRUPT", k["killer_client"],
                vic, "RECORDED",
                {"their_shots_before": fired, "damage_taken_events": hurt_me}))
    return out


def teleport_denial(c, ch) -> list[Shape]:
    """Killed within a heartbeat of arriving, before they had control."""
    out = []
    # NOT semantic_events teleport_in: those are temp entities and carry no
    # clientNum -- 10 rows in 263,210 have one. teleport_transits_v1 pairs the
    # out/in ends and confirms the player, which is the only honest source.
    arrivals = c.execute(
        "SELECT server_time_ms, client AS client_num FROM teleport_transits_v1 "
        "WHERE content_hash=? AND outcome='TELEPORT_PLAYER_CONFIRMED'",
        (ch,)).fetchall()
    if not arrivals:
        return out
    by_client = collections.defaultdict(list)
    for a in arrivals:
        by_client[a["client_num"]].append(a["server_time_ms"])
    for k in c.execute(
            "SELECT server_time_ms, round, killer_client, victim_client FROM "
            "kill_events_v1 WHERE content_hash=? AND death_cause="
            "'PLAYER_KILL' AND is_best_observation=1", (ch,)):
        for t_in in by_client.get(k["victim_client"], []):
            gap = k["server_time_ms"] - t_in
            if 0 <= gap <= 500:
                out.append(Shape(
                    ch, k["server_time_ms"], k["round"], "MID_TELEPORT_DENIAL",
                    k["killer_client"], k["victim_client"], "RECORDED",
                    {"arrived_ms": t_in, "dead_after_ms": gap}))
                break
    return out


def weapon_triptych(c, ch) -> list[Shape]:
    """Three kills in one burst with three different weapons."""
    out = []
    by_killer = collections.defaultdict(list)
    for k in c.execute(
            "SELECT server_time_ms, round, killer_client, victim_client, "
            "mod_name FROM kill_events_v1 WHERE content_hash=? AND "
            "death_cause='PLAYER_KILL' AND is_best_observation=1 "
            "ORDER BY server_time_ms", (ch,)):
        # best observation only: without it one kill seen by several copies
        # of the demo counted as several kills ("its the same clip").
        by_killer[k["killer_client"]].append(k)
    for killer, ks in by_killer.items():
        for i in range(len(ks) - 2):
            w = ks[i:i + 3]
            span = w[-1]["server_time_ms"] - w[0]["server_time_ms"]
            mods = {x["mod_name"] for x in w}
            if span <= 4000 and len(mods) == 3:
                out.append(Shape(
                    ch, w[0]["server_time_ms"], w[0]["round"],
                    "WEAPON_TRIPTYCH", killer, w[0]["victim_client"],
                    "RECORDED", {"span_ms": span, "mods": sorted(mods)}))
    return out


def refrag(c, ch) -> list[Shape]:
    """You killed whoever just killed your teammate. Matters more in Clan
    Arena than anywhere else, because nobody comes back."""
    out = []
    teams = {r["client"]: r["team"] for r in c.execute(
        "SELECT client, team FROM player_teams_v1 WHERE content_hash=?", (ch,))}
    if not teams:
        return out
    kills = c.execute(
        "SELECT server_time_ms, round, killer_client, victim_client FROM "
        "kill_events_v1 WHERE content_hash=? AND death_cause="
        "'PLAYER_KILL' ORDER BY server_time_ms", (ch,)).fetchall()
    for i, k in enumerate(kills):
        me, them = k["killer_client"], k["victim_client"]
        my_team = teams.get(me)
        # No team on record, or they are my own team-mate: not a refrag.
        if my_team is None or teams.get(them) == my_team:
            continue
        for j in range(i - 1, -1, -1):
            p = kills[j]
            if k["server_time_ms"] - p["server_time_ms"] > 3000:
                break
            if p["killer_client"] != them:
                continue
            if teams.get(p["victim_client"]) == teams.get(me) \
                    and p["victim_client"] != me:
                out.append(Shape(
                    ch, k["server_time_ms"], k["round"], "REFRAG", me, them,
                    "RECORDED",
                    {"they_killed_teammate": p["victim_client"],
                     "avenged_after_ms": k["server_time_ms"] - p["server_time_ms"]}))
                break
    return out


def health_shapes(c, ch) -> list[Shape]:
    """Shapes read off the victim's health chain within a round.

    ECONOMY_KILL   -- dead in the minimum number of hits that weapon allows.
    OVERKILL_BLOW  -- the last hit did far more than was needed. FLAVOUR, not
                      skill, and labelled as such so it never scores as one.
    """
    out = []
    # Health-after per victim per round, in order.
    chains = collections.defaultdict(list)
    for r in c.execute(
            "SELECT server_time_ms, round, client_num, parm FROM "
            "semantic_events_v1 WHERE content_hash=? AND type='pain' AND "
            "client_num IS NOT NULL AND parm IS NOT NULL ORDER BY "
            "server_time_ms", (ch,)):
        chains[(r["round"], r["client_num"])].append(
            (r["server_time_ms"], r["parm"]))

    NOMINAL = {"RAILGUN": 100, "ROCKET": 100, "ROCKET_SPLASH": 100,
               "SHOTGUN": 110, "LIGHTNING": 8, "PLASMA": 20,
               "GRENADE": 100, "MACHINEGUN": 7, "GAUNTLET": 50}
    for k in c.execute(
            "SELECT server_time_ms, round, killer_client, victim_client, "
            "mod_name FROM kill_events_v1 WHERE content_hash=? AND "
            "death_cause='PLAYER_KILL' AND is_best_observation=1", (ch,)):
        chain = chains.get((k["round"], k["victim_client"]), [])
        before = [c2 for c2 in chain if c2[0] <= k["server_time_ms"]]
        if not before:
            continue
        nominal = NOMINAL.get(k["mod_name"])
        hits = len(before)
        last_hp = before[-1][1]
        if nominal and nominal >= 50 and hits <= 2 and before[0][1] >= 60:
            out.append(Shape(
                ch, k["server_time_ms"], k["round"], "ECONOMY_KILL",
                k["killer_client"], k["victim_client"], "DERIVED",
                {"hits_taken": hits, "first_health_after": before[0][1],
                 "mod": k["mod_name"]}))
        if nominal and last_hp < 0.25 * nominal:
            out.append(Shape(
                ch, k["server_time_ms"], k["round"], "OVERKILL_BLOW",
                k["killer_client"], k["victim_client"], "DERIVED",
                {"health_before_fatal": last_hp, "weapon_nominal": nominal,
                 "note": "spectacle, not difficulty -- never score as skill"}))
    return out


DETECTORS = (ring_out, collateral_and_split, from_the_grave,
             orphaned_projectile, point_blank_and_range, gauntlet_interrupt,
             teleport_denial, weapon_triptych, refrag, health_shapes)


def detect_demo(c, content_hash) -> list[Shape]:
    out = []
    for fn in DETECTORS:
        try:
            out.extend(fn(c, content_hash))
        except Exception as e:                                 # noqa: BLE001
            # One bad demo must not lose the other nine detectors' findings.
            out.append(Shape(content_hash, 0, None, "DETECTOR_ERROR", None,
                             None, "DERIVED",
                             {"detector": fn.__name__, "error": str(e)[:200]}))
    return out


def build(limit=None, db=None, out_db=None, progress=None):
    """Scan the corpus and write frag_shapes_v1. Read-only on every source."""
    src = _connect(db)
    hashes = [r[0] for r in src.execute(
        "SELECT DISTINCT content_hash FROM kill_events_v1")]
    if limit:
        hashes = hashes[:limit]

    dest = sqlite3.connect(str(out_db or RECOGNITION_DB), timeout=120)
    dest.executescript(DDL)
    n = 0
    for i, ch in enumerate(hashes, 1):
        rows = [s.row() for s in detect_demo(src, ch)]
        # A rescan must REPLACE this demo's findings, not merge with them.
        # INSERT OR REPLACE alone leaves behind every row the new pass no
        # longer produces -- which is how 40 DETECTOR_ERROR rows survived a
        # scan that had already fixed the crash that caused them.
        dest.execute("DELETE FROM frag_shapes_v1 WHERE content_hash=?", (ch,))
        if rows:
            dest.executemany(
                "INSERT OR REPLACE INTO frag_shapes_v1 (content_hash,"
                "server_time_ms,round_no,shape,actor,victim,basis,evidence,"
                "version) VALUES (?,?,?,?,?,?,?,?,?)", rows)
            n += len(rows)
        if i % 25 == 0:
            dest.commit()
            if progress:
                progress(i, len(hashes), n)
    dest.commit()
    dest.close()
    return n
