"""A round with several actions is a SCENE, not several unrelated clips.

The first real review proved the isolated-frag model insufficient. If the
user strafes in, frags, flicks, frags again, drops to 18 HP and finishes the
round, showing them the middle kill alone as six seconds of footage throws
away the reason it mattered. 5,275 rounds in this corpus have two or more
confirmed user frags and 837 have three or more; those are scenes.

WHAT A SCENE IS NOT. It is not a new frag. F1, F2 and F3 keep their own
canonical occurrence ids, their own T1-T5 verdicts, their own annotations and
their own production usage. The scene is a CONTAINER and a relationship. It
never duplicates canonical truth.

ROUND 0 IS NOT A ROUND. It is the sentinel for "no round system" -- a
deathmatch, a warmup, a duel -- and grouping by it produced a "round" with
105 user frags spanning a whole match. Scene mode requires round > 0.

TWO KINDS OF EVENT LIVE ON THE RAIL. Canonical occurrences (frags, deaths)
carry verdicts. Derived scene events (a movement run, a low-HP moment, a
jump pad) carry only annotations -- the director may want the music to build
on the strafe without being asked to file it under one of five roles. Making
every micro-event demand a verdict would turn a review into data entry.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

MODE_FRAG = "FRAG_MODE"
MODE_SCENE = "SCENE_MODE"

# Round 0 means the demo had no round system. See the module docstring.
NO_ROUND = 0

# Scene mode is the default from two confirmed user frags. The user was
# explicit: one frag out of a sequence is useless for directing.
SCENE_MIN_USER_FRAGS = 2

# A single frag still becomes a scene when the round carries connective
# material worth seeing -- these are the traits that make the space between
# events part of the story.
SCENE_TRIGGER_TRAITS = ("HIGH_SPEED_MOVEMENT", "JUMPPAD_ACTION",
                        "LOW_HP_ACTION", "CLUTCH_1V2", "CLUTCH_1V3")

# Media padding around the whole scene.
LEAD_MS = 3000
TAIL_MS = 3000
MAX_SCENE_MS = 90_000

# Event kinds on the rail.
E_FRAG = "USER_FRAG"
E_OTHER_KILL = "KILL"
E_DEATH = "DEATH"
E_MOVEMENT = "MOVEMENT"
E_JUMPPAD = "JUMPPAD"

# Which rail events are canonical occurrences (they carry a T1-T5 verdict)
# and which are derived scene events (annotation only).
VERDICT_BEARING = (E_FRAG, E_OTHER_KILL, E_DEATH)


@dataclass(frozen=True)
class SceneEvent:
    """One thing on the rail.

    `event_id` is stable and addressable so an annotation can be attached to
    a movement run without that run becoming a reviewable frag.
    """
    event_id: str
    kind: str
    t_ms: int
    offset_ms: int
    label: str
    occurrence_id: int | None = None
    actor: str | None = None
    victim: str | None = None
    weapon: str | None = None
    is_user: bool = False
    is_team: bool = False
    frag_index: int | None = None        # F1 / F2 / F3 within the scene
    peak_speed: float | None = None
    human_role: str | None = None
    usage_state: str | None = None
    annotation: str = ""

    @property
    def takes_verdict(self) -> bool:
        return self.kind in VERDICT_BEARING and self.occurrence_id is not None


@dataclass(frozen=True)
class Scene:
    scene_id: str
    mode: str
    content_hash: str
    round_no: int
    map_name: str | None
    start_ms: int
    end_ms: int
    media_start_ms: int
    media_end_ms: int
    user_frags: int
    total_kills: int
    events: list[SceneEvent] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["events"] = [{**asdict(e), "takes_verdict": e.takes_verdict}
                       for e in self.events]
        d.pop("content_hash", None)       # private provenance, never to the UI
        return d


def _conn(db: Path = RECOGNITION_DB) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def scene_id(content_hash: str, round_no: int) -> str:
    return f"SCENE:{content_hash[:12]}:{round_no}"


def decide_mode(user_frags: int, round_no: int | None,
                traits: set[str] | None = None) -> tuple[str, str]:
    """FRAG or SCENE, with the reason stated.

    Returns (mode, reason). The reason is shown to the user so the choice is
    never mysterious -- and so a wrong one is reportable.
    """
    if round_no is None or round_no <= NO_ROUND:
        return MODE_FRAG, ("no round system in this demo -- round 0 is a "
                           "sentinel, not a round")
    if user_frags >= SCENE_MIN_USER_FRAGS:
        return MODE_SCENE, f"{user_frags} user frags in this round"
    hit = sorted((traits or set()) & set(SCENE_TRIGGER_TRAITS))
    if hit:
        return MODE_SCENE, "one frag plus connective action: " + ", ".join(hit)
    return MODE_FRAG, "a single isolated action in this round"


def build_scene(content_hash: str, round_no: int,
                user_names: set[str] | None = None,
                team_names: set[str] | None = None,
                db: Path = RECOGNITION_DB) -> Scene | None:
    """Assemble the scene for one round: every event on one clock."""
    from creative_suite.engine import review_corpus as rc
    from creative_suite.engine import production_usage as pu
    from creative_suite.engine.quake_names import display_name

    users = user_names if user_names is not None else rc.user_norms()
    team = team_names if team_names is not None else (rc.roster_norms() - users)

    with _conn(db) as c:
        kills = c.execute(
            "SELECT o.occurrence_id, o.server_time_ms, o.killer_name_norm, "
            "o.victim_name_norm, o.mod_name, o.map, o.killer_class, "
            "k.killer_name_raw, k.victim_name_raw "
            "FROM kill_occurrences_v1 o JOIN kill_events_v1 k "
            "ON k.kill_event_id = o.best_observation_id "
            "WHERE k.content_hash=? AND o.round=? ORDER BY o.server_time_ms",
            (content_hash, round_no)).fetchall()
        if not kills:
            return None
        t0 = int(kills[0]["server_time_ms"])
        t1 = int(kills[-1]["server_time_ms"])
        moves = c.execute(
            "SELECT moment_id, kind, start_ms, peak_ms, end_ms, peak_speed "
            "FROM movement_moments_v1 WHERE content_hash=? "
            "AND peak_ms BETWEEN ? AND ? ORDER BY peak_ms",
            (content_hash, t0 - LEAD_MS, t1 + TAIL_MS)).fetchall()

    events: list[SceneEvent] = []
    occ_ids: list[int] = []
    frag_n = 0
    user_frags = 0
    for r in kills:
        oid = int(r["occurrence_id"])
        occ_ids.append(oid)
        kn, vn = r["killer_name_norm"], r["victim_name_norm"]
        is_user = kn in users and r["killer_class"] == "PLAYER"
        victim_is_user = vn in users
        if is_user:
            user_frags += 1
            frag_n += 1
            kind, idx = E_FRAG, frag_n
        elif victim_is_user:
            kind, idx = E_DEATH, None
        else:
            kind, idx = E_OTHER_KILL, None
        t = int(r["server_time_ms"])
        actor = display_name(r["killer_name_raw"]) or None
        victim = display_name(r["victim_name_raw"]) or None
        label = (f"F{idx} · {r['mod_name']} · {victim}" if kind == E_FRAG
                 else f"{'DEATH' if kind == E_DEATH else 'KILL'} · "
                      f"{actor} → {victim}")
        events.append(SceneEvent(
            event_id=f"OCC:{oid}", kind=kind, t_ms=t, offset_ms=t - t0,
            label=label, occurrence_id=oid, actor=actor, victim=victim,
            weapon=r["mod_name"], is_user=is_user,
            is_team=(kn in team), frag_index=idx))

    for m in moves:
        t = int(m["peak_ms"])
        kind = E_JUMPPAD if m["kind"] == "JUMPPAD_ACTION" else E_MOVEMENT
        sp = m["peak_speed"]
        label = (f"{sp:.0f} UPS" if sp else "JUMP PAD") if kind == E_MOVEMENT \
            else ("JUMP PAD" + (f" · {sp:.0f} UPS" if sp else ""))
        events.append(SceneEvent(
            event_id=f"MOV:{int(m['moment_id'])}", kind=kind, t_ms=t,
            offset_ms=t - t0, label=label, peak_speed=sp, is_user=True))

    events.sort(key=lambda e: e.t_ms)

    # Verdicts and usage, for the canonical events only.
    got = rc.reviews([f"USER_FRAG:{i}" for i in occ_ids]) | \
        rc.reviews([f"ALL_KILL:{i}" for i in occ_ids]) | \
        rc.reviews([f"DEATH:{i}" for i in occ_ids])
    usage = pu.states(occ_ids)
    merged: list[SceneEvent] = []
    for e in events:
        if e.occurrence_id is None:
            merged.append(e)
            continue
        rv = (got.get(f"USER_FRAG:{e.occurrence_id}")
              or got.get(f"ALL_KILL:{e.occurrence_id}")
              or got.get(f"DEATH:{e.occurrence_id}") or {})
        st = usage.get(e.occurrence_id, {})
        merged.append(SceneEvent(**{
            **asdict(e),
            "human_role": rv.get("human_role") or None,
            "usage_state": st.get("state"),
        }))

    traits = {m["kind"] for m in moves}
    mode, reason = decide_mode(user_frags, round_no, traits)
    ms = max(0, t0 - LEAD_MS)
    me = min(t1 + TAIL_MS, ms + MAX_SCENE_MS)
    return Scene(
        scene_id=scene_id(content_hash, round_no), mode=mode,
        content_hash=content_hash, round_no=round_no,
        map_name=kills[0]["map"], start_ms=t0, end_ms=t1,
        media_start_ms=ms, media_end_ms=me,
        user_frags=user_frags, total_kills=len(kills),
        events=merged, reason=reason)


def scene_for_item(item_id: str, db: Path = RECOGNITION_DB) -> Scene | None:
    """The scene a review item belongs to, if it belongs to one."""
    from creative_suite.engine import review_corpus as rc
    it = rc.item(item_id)
    if it is None or it.round_no is None:
        return None
    return build_scene(it.content_hash, it.round_no, db=db)
