"""Every camera that filmed one moment, and how good each one is.

ONE KILL HAPPENED ONCE; SEVERAL PEOPLE MAY HAVE RECORDED IT. The occurrence
layer already merges those into a single reviewable moment, which is what
stops the same frag being discovered three times and judged three different
ways. What it does not do is tell the reviewer that the alternatives exist.

That matters for filmmaking in a way it does not for scoring:

    A brilliant event from a useless POV and an ordinary event from a
    perfect POV are completely different assets.

The killer's own demo is not automatically the best shot. A teammate
watching from across the map may have the only camera that shows the rocket
travel; the victim's demo is the only one that ever sees the killer's face.
So POV quality is reported as its OWN axis, next to the verdict and never
folded into it -- an insane frag tagged ALT_POV is an instruction to go and
find the better camera, not a lower score.

WHAT IS OBSERVED AND WHAT IS INFERRED. Whether the recorder was the killer
or the victim is a fact the demo states. Whether they were a teammate is
derived from `player_teams_v1`, which is missing for some clients; when it
is missing this says OTHER rather than guessing, because "some stranger
filmed it" and "your teammate filmed it" lead to different decisions.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

# The four cameras a moment can have been filmed from.
SELF_POV = "SELF_POV"            # the recorder IS the killer
VICTIM_POV = "VICTIM_POV"        # the recorder IS the victim
TEAM_POV = "TEAM_POV"            # a teammate of the killer filmed it
OTHER_POV = "OTHER_POV"          # anyone else, or team unknown

POV_LABEL = {
    SELF_POV: "the actor's own camera",
    VICTIM_POV: "the victim's camera -- sees the actor",
    TEAM_POV: "a teammate's camera",
    OTHER_POV: "another player's camera",
}

# Order of usefulness for JUDGING the action. Not for filming it -- a victim
# POV is often the better shot and ranks low here on purpose, because this
# ordering answers "which camera should the reviewer watch first", and the
# reviewer is judging what the actor did.
POV_RANK = {SELF_POV: 0, VICTIM_POV: 1, TEAM_POV: 2, OTHER_POV: 3}


def _conn(db: Path = RECOGNITION_DB) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def classify(row: sqlite3.Row, teams: dict[int, str]) -> str:
    """Which camera this observation is, from what the demo actually said."""
    if row["is_recorder_killer"]:
        return SELF_POV
    if row["is_recorder_victim"]:
        return VICTIM_POV
    rec, killer = row["recorder_client"], row["killer_client"]
    if rec is None or killer is None:
        return OTHER_POV
    rt, kt = teams.get(int(rec)), teams.get(int(killer))
    # Absence is not evidence of a different team. Without both sides this
    # cannot be called TEAM, and saying OTHER is the honest answer.
    if rt and kt and rt == kt:
        return TEAM_POV
    return OTHER_POV


def povs_for(occurrence_id: int, db: Path = RECOGNITION_DB
             ) -> dict[str, Any]:
    """Every recording of one moment, best-for-judging first.

    `content_hash` never leaves this function: demo identity is private
    provenance, and the UI addresses an alternative by observation id.
    """
    with _conn(db) as c:
        obs = c.execute(
            "SELECT kill_event_id, content_hash, recorder_client, "
            "killer_client, victim_client, is_recorder_killer, "
            "is_recorder_victim, is_best_observation "
            "FROM kill_events_v1 WHERE occurrence_id = ?",
            (int(occurrence_id),)).fetchall()
        if not obs:
            return {"occurrence_id": int(occurrence_id), "available": False,
                    "n_povs": 0, "povs": []}
        hashes = {r["content_hash"] for r in obs}
        qs = ",".join("?" * len(hashes))
        teams: dict[str, dict[int, str]] = {}
        for r in c.execute(
                f"SELECT content_hash, client, team FROM player_teams_v1 "
                f"WHERE content_hash IN ({qs})", list(hashes)):
            teams.setdefault(r["content_hash"], {})[int(r["client"])] = r["team"]

    out = []
    for r in obs:
        kind = classify(r, teams.get(r["content_hash"], {}))
        out.append({
            "observation_id": int(r["kill_event_id"]),
            "pov": kind,
            "label": POV_LABEL[kind],
            "is_best": bool(r["is_best_observation"]),
        })
    out.sort(key=lambda d: (POV_RANK[d["pov"]], d["observation_id"]))
    kinds = [d["pov"] for d in out]
    return {
        "occurrence_id": int(occurrence_id),
        "available": True,
        "n_povs": len(out),
        "povs": out,
        # The one line the reviewer actually needs on screen.
        "summary": (f"{len(out)} POVs available" if len(out) > 1
                    else POV_LABEL[kinds[0]]),
        "has_actor_pov": SELF_POV in kinds,
        # An alternative worth going to look at: a camera that is not the one
        # currently being shown.
        "has_alternative": len(out) > 1,
    }


def pov_of_best(occurrence_id: int, db: Path = RECOGNITION_DB) -> str | None:
    d = povs_for(occurrence_id, db=db)
    for p in d["povs"]:
        if p["is_best"]:
            return p["pov"]
    return d["povs"][0]["pov"] if d["povs"] else None
