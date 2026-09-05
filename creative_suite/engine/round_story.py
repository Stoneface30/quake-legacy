"""A round is the context a frag lives in, and sometimes a scene of its own.

THE FEAR THIS ADDRESSES. The user should never finish reviewing and then
discover that three of the moments they judged separately were the same
thirty seconds of one teamfight. In Clan Arena a round IS the fight -- 4v4
down to 4v2 down to a win -- and a frag torn out of it loses the reason it
mattered. So every review item now knows its round, what else happened in it,
and whether any of that has already been judged or used.

WHAT IS NOT DONE HERE. The round does not replace the frag. The +/-3s clip
stays the fast review unit, because the director is answering "what is this
FOR", not "what happened". The round is offered -- related events, a
timeline, a WATCH FULL ROUND button -- and never forced.

ALIVE COUNTS ARE DERIVED, AND SAY SO. Clan Arena gives one life per round, so
a team's alive count is its size minus the deaths so far. That is arithmetic
over observed obituaries, not a value the server sent, and it is only as
complete as the demo's observation coverage. It is labelled DERIVED
throughout; a round we saw partially yields a partial count, not a wrong one
presented confidently.

A ROUND STORY CANDIDATE IS A MACHINE TAG. It says this round may deserve
contextual review. It is not a sixth verdict button and it does not decide
anything -- the five buttons remain the only human truth.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

from creative_suite.engine.quake_names import display_name

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

DERIVED = "DERIVED"
OBSERVED = "OBSERVED"

# What makes a round worth watching whole rather than as one clip. Each is a
# reason a viewer would need the surrounding fight to understand the moment.
STORY_MIN_USER_KILLS = 2          # the user did more than one thing
STORY_MIN_TOTAL_KILLS = 4         # a fight, not a pick
STORY_MIN_TEAM_KILLS = 2          # the clan fought it together


@dataclass(frozen=True)
class RoundEvent:
    """One thing that happened, placed on the round's clock."""
    t_ms: int
    # From the ROUND's start, not from the first death. Measuring from the
    # first kill made every round's opening event read "+0.0s" -- which,
    # beside a round header that now states a real duration, said the frag
    # happened at the instant the round began.
    offset_ms: int
    kind: str                      # FRAG / DEATH / TELEPORT / JUMPPAD ...
    actor: str | None = None
    victim: str | None = None
    weapon: str | None = None
    occurrence_id: int | None = None
    is_user: bool = False
    is_team: bool = False
    human_role: str | None = None
    usage_state: str | None = None
    provenance: str = OBSERVED


@dataclass(frozen=True)
class RoundContext:
    content_hash: str
    round_no: int
    map_name: str | None
    start_ms: int
    end_ms: int
    # The interval the round is now believed to occupy, and where that belief
    # comes from. It is NOT the span between the first and last observed
    # kill: a round with one kill has a zero-length kill span, and 51.2% of
    # rounds in this corpus have exactly one.
    duration_ms: int | None
    duration_provenance: str = "KILL_SPAN"
    duration_credible: bool = True
    duration_note: str = ""
    events: list[RoundEvent] = field(default_factory=list)
    user_kills: int = 0
    team_kills: int = 0
    enemy_kills: int = 0
    user_died: bool = False
    team_size: dict[str, int] = field(default_factory=dict)
    alive_curve: list[dict[str, Any]] = field(default_factory=list)
    alive_provenance: str = DERIVED
    is_story_candidate: bool = False
    story_reasons: list[str] = field(default_factory=list)
    coverage_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["events"] = [asdict(e) for e in self.events]
        return d


def _conn(db: Path = RECOGNITION_DB) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def _reviews_and_usage(occ_ids: list[int]) -> dict[int, dict[str, Any]]:
    """What the user has already said about these occurrences, and whether
    any are spoken for. This is the duplicate-safety answer: a moment already
    judged is shown as judged, never asked again as if it were new."""
    if not occ_ids:
        return {}
    from creative_suite.engine import review_corpus as rc
    from creative_suite.engine import production_usage as pu
    out: dict[int, dict[str, Any]] = {}
    for kind in ("USER_FRAG", "CLAN_FRAG", "ALL_KILL", "DEATH"):
        got = rc.reviews([f"{kind}:{i}" for i in occ_ids])
        for iid, rv in got.items():
            oid = int(iid.split(":", 1)[1])
            out.setdefault(oid, {})["human_role"] = rv.get("human_role")
            out[oid]["note"] = rv.get("note") or ""
    for oid, st in pu.states(occ_ids).items():
        out.setdefault(oid, {})["usage_state"] = st.get("state")
        out[oid]["usage_detail"] = st.get("detail")
    return out


def round_context(content_hash: str, round_no: int,
                  user_names: set[str] | None = None,
                  team_names: set[str] | None = None,
                  db: Path = RECOGNITION_DB) -> RoundContext | None:
    """Everything known about one round, on one clock."""
    from creative_suite.engine import review_corpus as rc
    users = user_names if user_names is not None else rc.user_norms()
    team = team_names if team_names is not None else (rc.roster_norms() - users)

    with _conn(db) as c:
        occ = c.execute(
            "SELECT o.occurrence_id, o.server_time_ms, o.killer_name_norm, "
            "o.victim_name_norm, o.mod_name, o.death_cause, o.killer_class, "
            "k.killer_name_raw, k.victim_name_raw, o.map "
            "FROM kill_occurrences_v1 o "
            "JOIN kill_events_v1 k ON k.kill_event_id = o.best_observation_id "
            "WHERE k.content_hash = ? AND o.round = ? "
            "ORDER BY o.server_time_ms", (content_hash, round_no)).fetchall()
        if not occ:
            return None
        teams = {r["client"]: r["team"] for r in c.execute(
            "SELECT client, team FROM player_teams_v1 WHERE content_hash=?",
            (content_hash,))}
        tp = c.execute(
            "SELECT server_time_ms, client FROM teleport_transits_v1 "
            "WHERE content_hash=? AND outcome='TELEPORT_PLAYER_CONFIRMED' "
            "AND server_time_ms BETWEEN ? AND ? ORDER BY 1",
            (content_hash, occ[0]["server_time_ms"] - 30000,
             occ[-1]["server_time_ms"] + 15000)).fetchall()

    ids = [int(r["occurrence_id"]) for r in occ]
    meta = _reviews_and_usage(ids)
    t0 = int(occ[0]["server_time_ms"])
    t1 = int(occ[-1]["server_time_ms"])
    from creative_suite.engine import round_bounds as rbm
    b = rbm.bounds_for(content_hash, round_no, db=db)
    # Offsets are measured from the round's start where one is known.
    t0 = b.start_ms if b.start_ms is not None else t0

    events: list[RoundEvent] = []
    user_kills = team_kills = enemy_kills = 0
    user_died = False
    for r in occ:
        kn, vn = r["killer_name_norm"], r["victim_name_norm"]
        is_user = kn in users
        is_team = kn in team
        if r["killer_class"] == "PLAYER":
            if is_user:
                user_kills += 1
            elif is_team:
                team_kills += 1
            else:
                enemy_kills += 1
        if vn in users:
            user_died = True
        m = meta.get(int(r["occurrence_id"]), {})
        t = int(r["server_time_ms"])
        events.append(RoundEvent(
            t_ms=t, offset_ms=t - t0,
            kind="FRAG" if r["killer_class"] == "PLAYER" else r["death_cause"],
            actor=display_name(r["killer_name_raw"]) or None,
            victim=display_name(r["victim_name_raw"]) or None,
            weapon=r["mod_name"], occurrence_id=int(r["occurrence_id"]),
            is_user=is_user, is_team=is_team,
            human_role=m.get("human_role"), usage_state=m.get("usage_state")))
    for r in tp:
        t = int(r["server_time_ms"])
        if t0 - 30000 <= t <= t1 + 15000:
            events.append(RoundEvent(t_ms=t, offset_ms=t - t0, kind="TELEPORT"))
    events.sort(key=lambda e: e.t_ms)

    # Team sizes, and the alive curve that follows from them. One life per
    # round in Clan Arena, so each observed death costs its team one.
    size: dict[str, int] = {}
    for cl, tm in teams.items():
        if tm in ("RED", "BLUE"):
            size[tm] = size.get(tm, 0) + 1
    alive = dict(size)
    curve = [{"offset_ms": 0, **alive}]
    with _conn(db) as c:
        vteam = {r["client"]: teams.get(r["client"]) for r in c.execute(
            "SELECT client FROM player_teams_v1 WHERE content_hash=?",
            (content_hash,))}
    for r in occ:
        vt = vteam.get(r["victim_name_norm"])      # by slot is unavailable here
        del vt
    with _conn(db) as c:
        deaths = c.execute(
            "SELECT o.server_time_ms, o.victim_client FROM kill_occurrences_v1 o "
            "JOIN kill_events_v1 k ON k.kill_event_id=o.best_observation_id "
            "WHERE k.content_hash=? AND o.round=? ORDER BY 1",
            (content_hash, round_no)).fetchall()
    for d in deaths:
        tm = teams.get(d["victim_client"])
        if tm in alive and alive[tm] > 0:
            alive[tm] -= 1
            curve.append({"offset_ms": int(d["server_time_ms"]) - t0, **alive})

    reasons = []
    if user_kills >= STORY_MIN_USER_KILLS:
        reasons.append(f"{user_kills} user frags")
    if team_kills >= STORY_MIN_TEAM_KILLS:
        reasons.append(f"{team_kills} clan frags")
    if len(occ) >= STORY_MIN_TOTAL_KILLS:
        reasons.append(f"{len(occ)} kills in the round")
    if size:
        reasons.append(" v ".join(str(v) for v in size.values()) + " start")
    if user_died:
        reasons.append("user died")
    story = bool(user_kills >= STORY_MIN_USER_KILLS
                 or (user_kills >= 1 and team_kills >= STORY_MIN_TEAM_KILLS)
                 or len(occ) >= STORY_MIN_TOTAL_KILLS + 2)

    return RoundContext(
        content_hash=content_hash, round_no=round_no,
        map_name=occ[0]["map"], start_ms=b.start_ms if b.start_ms is not None
        else t0, end_ms=b.end_ms if b.end_ms is not None else t1,
        duration_ms=b.duration_ms, duration_provenance=b.provenance,
        duration_credible=b.credible, duration_note=b.note,
        events=events, user_kills=user_kills,
        team_kills=team_kills, enemy_kills=enemy_kills, user_died=user_died,
        team_size=size, alive_curve=curve, alive_provenance=DERIVED,
        is_story_candidate=story, story_reasons=reasons,
        coverage_note=("events are what THIS demo observed. A kill absent "
                       "here is not proof it did not happen"))


def round_window(ctx: RoundContext, pre_ms: int = 4000,
                 post_ms: int = 4000) -> tuple[int, int]:
    """Media bounds for WATCH FULL ROUND. Padded, and clamped at zero."""
    return max(0, ctx.start_ms - pre_ms), ctx.end_ms + post_ms
