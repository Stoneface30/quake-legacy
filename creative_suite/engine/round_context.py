"""Round, team and 1vX truth for a moment, as numbers, with gates.

WHAT A COMPOSER MAY ASSUME. A triumphant treatment -- LAST_MAN_STANDING,
CLUTCH, the map disassembling into a victory -- may only fire when the
round was actually WON. A brilliant 1v3 that ended in a loss is still
brilliant and still usable; it is not a triumph, and presenting it as one is
a lie the viewer can check against the scoreboard. So every gate here is
strict: UNKNOWN never satisfies a requirement, and a round the demo never
said was won is not won.

WHERE THE NUMBERS COME FROM. Round outcomes are derived from the team-score
configstrings (`demo_truth.round_outcomes`); team membership from the
per-client team timeline; alive counts from death and gib events per client
within the round. None of it comes from names or audio. Identity is always
(content_hash, server_time): the same map replayed produces identical-looking
times that are different kills.

DUPLICATES. A re-saved demo is the same match twice. Corpus statistics
collapse demos whose full kill signature is identical; a mere coincidence of
map and time is never collapsed.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
from typing import Any, Sequence

from creative_suite.engine import demo_truth as dt

ROUND_CONTEXT_VERSION = "round-context-v1.0.0"

RECOGNITION_DB = dt.RECOGNITION_DB

# ── 1vX ─────────────────────────────────────────────────────────────────────

ONE_V_ONE = "ONE_V_ONE"
ONE_V_TWO = "ONE_V_TWO"
ONE_V_THREE = "ONE_V_THREE"
ONE_V_FOUR = "ONE_V_FOUR"
ONE_V_MANY = "ONE_V_MANY"
NOT_ONE_V_X = "NOT_ONE_V_X"


def one_v_x_class(my_alive: int, enemy_alive: int) -> str:
    if my_alive != 1 or enemy_alive < 1:
        return NOT_ONE_V_X
    return {1: ONE_V_ONE, 2: ONE_V_TWO, 3: ONE_V_THREE,
            4: ONE_V_FOUR}.get(enemy_alive, ONE_V_MANY)


@dataclass(frozen=True)
class AliveState:
    """Who is standing on each side at one instant, from death events."""
    demo_us: int
    my_alive: int
    enemy_alive: int
    me_alive: bool

    @property
    def one_v_x(self) -> str:
        return one_v_x_class(self.my_alive, self.enemy_alive) if self.me_alive \
            else NOT_ONE_V_X

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["one_v_x"] = self.one_v_x
        return d


@dataclass(frozen=True)
class RoundContext:
    """Everything the composer may know about the round around a moment."""
    round_index: int | None
    round_start_us: int | None
    round_end_us: int | None
    winner_team: str
    recorder_team: str
    result: str                       # WIN | LOSS | UNKNOWN
    teammates: int | None
    opponents: int | None
    alive_at_hero: AliveState | None
    eliminations: tuple[int, ...] = ()      # demo_us of enemy deaths in the round
    teammate_deaths: tuple[int, ...] = ()
    evidence: str = dt.EVENT_CONSTRAINED

    @property
    def one_v_x_at_hero(self) -> str:
        return self.alive_at_hero.one_v_x if self.alive_at_hero else NOT_ONE_V_X

    @property
    def is_team_round(self) -> bool:
        return (self.teammates or 0) >= 1 and (self.opponents or 0) >= 2

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["alive_at_hero"] = self.alive_at_hero.to_dict() if self.alive_at_hero else None
        d["one_v_x_at_hero"] = self.one_v_x_at_hero
        d["is_team_round"] = self.is_team_round
        return d


# ── gates ───────────────────────────────────────────────────────────────────

GATE_1VX_WIN = "1VX_WIN"
GATE_TEAM_ROUND = "TEAM_ROUND"
GATE_PROJECTILE_REPLAY = "PROJECTILE_REPLAY"
GATE_TRIUMPH = "TRIUMPH"

PRESENTABLE_RECONSTRUCTION = ("EXACT_DETERMINISTIC",
                              "DETERMINISTIC_UNTIL_UNOBSERVED_DYNAMIC_CONTACT",
                              "EVENT_CONSTRAINED")


@dataclass(frozen=True)
class GateResult:
    gate: str
    passed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def gate_triumph(ctx: RoundContext | None) -> GateResult:
    """Victory presentation requires a round the demo says was WON."""
    if ctx is None or ctx.result != dt.ROUND_WIN:
        got = "no round context" if ctx is None else ctx.result
        return GateResult(GATE_TRIUMPH, False,
                          f"triumph treatment needs result WIN; have {got}")
    return GateResult(GATE_TRIUMPH, True, "round result WIN from team scores")


def gate_one_v_x_win(ctx: RoundContext | None) -> GateResult:
    if ctx is None or ctx.one_v_x_at_hero == NOT_ONE_V_X:
        return GateResult(GATE_1VX_WIN, False, "no 1vX evidence at the hero moment")
    t = gate_triumph(ctx)
    if not t.passed:
        return GateResult(GATE_1VX_WIN, False,
                          f"{ctx.one_v_x_at_hero} but {t.reason}")
    return GateResult(GATE_1VX_WIN, True,
                      f"{ctx.one_v_x_at_hero} in a round the recorder's side won")


def gate_team_round(ctx: RoundContext | None) -> GateResult:
    if ctx is None or not ctx.is_team_round:
        return GateResult(GATE_TEAM_ROUND, False,
                          "team-round narrative needs >=1 teammate and >=2 opponents "
                          "from team-state evidence")
    return GateResult(GATE_TEAM_ROUND, True,
                      f"{ctx.teammates} teammates vs {ctx.opponents} opponents")


def gate_projectile_replay(candidate: Any) -> GateResult:
    ok = (getattr(candidate, "reconstruction_available", False)
          and getattr(candidate, "reconstruction_confidence", "")
          in PRESENTABLE_RECONSTRUCTION)
    if not ok:
        return GateResult(GATE_PROJECTILE_REPLAY, False,
                          "projectile replay needs a reconstruction at or above "
                          "the presentation threshold; UNKNOWN does not qualify")
    return GateResult(GATE_PROJECTILE_REPLAY, True,
                      f"path {getattr(candidate, 'reconstruction_confidence', '')}")


# ── building context from the enrichment tables ─────────────────────────────

def _team_at(changes: Sequence[tuple[int, int, str]], client: int, t_ms: int,
             fallback: str) -> str:
    """The client's team at a time, from the timeline; last change wins."""
    team = fallback
    for ct, cc, tm in sorted(changes):
        if cc != client:
            continue
        if ct <= t_ms:
            team = tm
        else:
            break
    return team if team in ("RED", "BLUE") else dt.ROUND_UNKNOWN


def round_context_for(content_hash: str, hero_ms: int, recorder_client: int, *,
                      db_path: Path | None = None) -> RoundContext | None:
    """The round around one moment, from enrichment tables only."""
    path = Path(db_path or RECOGNITION_DB)
    with sqlite3.connect(path, timeout=30) as db:
        try:
            outcomes = dt.load_round_outcomes(content_hash, recorder_client,
                                              db_path=path)
            teams = db.execute("SELECT client, team FROM player_teams_v1 WHERE "
                               "content_hash=?", (content_hash,)).fetchall()
            changes = db.execute("SELECT server_time_ms, client, team FROM "
                                 "team_changes_v1 WHERE content_hash=?",
                                 (content_hash,)).fetchall()
            starts = db.execute("SELECT server_time_ms, value FROM round_state_v1 "
                                "WHERE content_hash=? AND cs=661 ORDER BY 1",
                                (content_hash,)).fetchall()
            deaths = db.execute("SELECT server_time_ms, entity_num, client_num, source "
                                "FROM semantic_events_v1 WHERE content_hash=? AND "
                                "type IN ('death','gib_player') ORDER BY 1",
                                (content_hash,)).fetchall()
        except sqlite3.OperationalError:
            return None
    if not outcomes:
        return None
    outcome = dt.outcome_at(outcomes, hero_ms * 1000)
    if outcome is None:
        return None
    # round start: the last 661 round-info string before the hero
    start_ms = None
    for t, v in starts:
        if t <= hero_ms and v.strip().strip('"'):
            start_ms = t
    end_ms = outcome.end_us // 1000
    team_of = {int(c): (t if t in ("RED", "BLUE") else dt.ROUND_UNKNOWN)
               for c, t in teams}
    my_team = _team_at(changes, recorder_client, hero_ms,
                       team_of.get(recorder_client, dt.ROUND_UNKNOWN))
    if my_team == dt.ROUND_UNKNOWN:
        mates = opps = None
    else:
        sides = {c: _team_at(changes, c, hero_ms, tm) for c, tm in team_of.items()}
        mates = sum(1 for c, tm in sides.items() if tm == my_team and c != recorder_client)
        opps = sum(1 for tm in sides.values()
                   if tm in ("RED", "BLUE") and tm != my_team)
    # alive counts: each client dies at most once per round; deaths before the
    # hero and after the round start remove them.
    dead: set[int] = set()
    elim: list[int] = []
    mate_deaths: list[int] = []
    lo = start_ms if start_ms is not None else -1
    for t, ent, cl, src in deaths:
        who = cl if src == "playerstate" else ent
        if who is None or not (lo <= t <= hero_ms):
            continue
        who = int(who)
        if who in dead:
            continue
        dead.add(who)
        side = _team_at(changes, who, t, team_of.get(who, dt.ROUND_UNKNOWN))
        if my_team != dt.ROUND_UNKNOWN and side == my_team and who != recorder_client:
            mate_deaths.append(t * 1000)
        elif my_team != dt.ROUND_UNKNOWN and side in ("RED", "BLUE"):
            elim.append(t * 1000)
    alive = None
    if mates is not None and opps is not None:
        alive = AliveState(hero_ms * 1000,
                           my_alive=max(0, mates + 1 - len(mate_deaths)
                                        - (1 if recorder_client in dead else 0)),
                           enemy_alive=max(0, opps - len(elim)),
                           me_alive=recorder_client not in dead)
    return RoundContext(
        round_index=outcome.round_index, round_start_us=(start_ms * 1000
                                                         if start_ms else None),
        round_end_us=outcome.end_us, winner_team=outcome.winner_team,
        recorder_team=my_team, result=(outcome.result if my_team ==
                                       outcome.recorder_team else
                                       (dt.ROUND_WIN if outcome.winner_team == my_team
                                        else dt.ROUND_LOSS if outcome.winner_team in
                                        ("RED", "BLUE") else dt.ROUND_UNKNOWN)),
        teammates=mates, opponents=opps, alive_at_hero=alive,
        eliminations=tuple(elim), teammate_deaths=tuple(mate_deaths))


# ── duplicate demos ─────────────────────────────────────────────────────────

def kill_list(db: sqlite3.Connection, content_hash: str
              ) -> tuple[tuple[int, int, str], ...]:
    """A match's ordered (server_time_ms, victim_client, weapon) kills."""
    return tuple((int(t), int(v) if v is not None else -1, str(w)) for t, v, w in
                 db.execute("SELECT server_time_ms, victim_client, weapon_name FROM "
                            "recognized_frags WHERE content_hash=? ORDER BY 1",
                            (content_hash,)).fetchall())


def kill_signature(db: sqlite3.Connection, content_hash: str) -> str:
    """A match's identity: its full ordered kill list. Not map, not time."""
    import hashlib
    rows = kill_list(db, content_hash)
    return hashlib.sha256(repr(rows).encode()).hexdigest() if rows else ""


def _map_of(db: sqlite3.Connection, content_hash: str) -> str:
    for sql in ("SELECT map FROM scanned_demos WHERE content_hash=?",
                "SELECT map_name FROM scanned_demos WHERE content_hash=?"):
        try:
            row = db.execute(sql, (content_hash,)).fetchone()
            if row and row[0]:
                return str(row[0])
        except sqlite3.OperationalError:
            continue
    return ""


COLLAPSE_EXACT = "EXACT_SIGNATURE"      # byte-different file, identical kill list
COLLAPSE_CUT = "CUT_COPY"               # a trimmed save of a longer recording, world-confirmed
REFUSED_CUT = "CUT_CANDIDATE_REFUSED"   # kills contained but the world does not agree
WORLD_AGREEMENT_MIN = 0.95              # share of the short demo's missile samples found
                                        # verbatim (tick, entity, x, y, z) in the long one


def world_agreement(db: sqlite3.Connection, short: str, long: str) -> float | None:
    """How much of the shorter demo's recorded world the longer one contains,
    measured on missile samples at shared ticks. Identical recordings agree
    ~1.0; a different match on the same map agrees ~0.0. None = no evidence."""
    lo_hi = db.execute("SELECT MIN(server_time_ms), MAX(server_time_ms) FROM "
                       "missile_samples_v1 WHERE content_hash=?", (short,)).fetchone()
    if not lo_hi or lo_hi[0] is None:
        return None
    sql = ("SELECT server_time_ms, entity_num, x, y, z FROM missile_samples_v1 "
           "WHERE content_hash=? AND x IS NOT NULL AND server_time_ms BETWEEN ? AND ?")
    a = set(db.execute(sql, (short, *lo_hi)).fetchall())
    if not a:
        return None
    b = set(db.execute(sql, (long, *lo_hi)).fetchall())
    return len(a & b) / len(a)


def canonical_demos(db_path: Path | None = None, *, cut_copies: bool = True,
                    reasons: dict[str, str] | None = None) -> dict[str, str]:
    """content_hash -> the representative hash for its match.

    Collapses, each reported separately through `reasons`:
    EXACT_SIGNATURE -- identical full kill lists.
    CUT_COPY -- every kill of the shorter demo (same server_time, victim slot,
    weapon) appears in the longer one AND the recorded world agrees at shared
    ticks (`world_agreement` >= WORLD_AGREEMENT_MIN). Kill containment alone
    is not identity: the same map replayed on the same server produces
    identical-looking times that are different kills, and a one-kill demo can
    fit inside a stranger by coincidence. Such candidates are refused and
    tagged CUT_CANDIDATE_REFUSED; they stay canonical.
    """
    path = Path(db_path or RECOGNITION_DB)
    rep: dict[str, str] = {}
    first: dict[str, str] = {}
    lists: dict[str, tuple[tuple[int, int, str], ...]] = {}
    with sqlite3.connect(path, timeout=30) as db:
        for (h,) in db.execute("SELECT content_hash FROM scanned_demos WHERE "
                               "error IS NULL ORDER BY content_hash"):
            kl = kill_list(db, h)
            if not kl:
                rep[h] = h
                continue
            lists[h] = kl
            r = first.setdefault(kill_signature(db, h), h)
            rep[h] = r
            if r != h and reasons is not None:
                reasons[h] = COLLAPSE_EXACT
        if not cut_copies:
            return rep
        by_kill: dict[tuple[int, int, str], list[str]] = {}
        for h, kl in lists.items():
            if rep[h] == h:
                for k in kl:
                    by_kill.setdefault(k, []).append(h)
        try:
            db.execute("SELECT 1 FROM missile_samples_v1 LIMIT 1")
            have_world = True
        except sqlite3.OperationalError:
            have_world = False
        for h in sorted((h for h in lists if rep[h] == h), key=lambda h: len(lists[h])):
            kl = lists[h]
            for other in by_kill.get(kl[0], ()):
                if other == h or rep[other] != other or len(lists[other]) <= len(kl):
                    continue
                if not set(kl) <= set(lists[other]):
                    continue
                agree = world_agreement(db, h, other) if have_world else None
                if agree is None or agree < WORLD_AGREEMENT_MIN:
                    if reasons is not None:
                        reasons[h] = REFUSED_CUT
                    continue
                for x, r in list(rep.items()):        # move h and its exact twins
                    if r == h:
                        rep[x] = other
                if reasons is not None:
                    reasons[h] = COLLAPSE_CUT
                break
    return rep
