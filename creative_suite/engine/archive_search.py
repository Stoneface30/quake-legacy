"""The whole archive as searchable material, not just the frags that scored.

WHY THIS EXISTS. Earlier searches ran over the top few thousand scored frags,
which quietly assumed the creative universe is "kills, ranked". It is not. A
score slot may want a jump, a teleport, a rocket flying past the camera, a
chat line, a death worth cutting on, a round that was won after a long grind,
or a projectile the client never saw. Those live all over the corpus, and most
of them are not frags at all.

WHAT A CLASS IS. A name for material a choreography lane can ask for. Each
class says which evidence table answers it and what it needs to be true.
Missing evidence is UNKNOWN -- a class is never claimed by default.

IDENTITY. Every result carries (content_hash, server_time_ms). Two moments on
the same map at the same server time in different recordings are different
occurrences, and results are counted over canonical matches only.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Sequence

from creative_suite.engine import demo_truth as dt

SEARCH_VERSION = "archive-search-v1.0.0"
UNKNOWN = "UNKNOWN"
RECOGNITION_DB = dt.RECOGNITION_DB

# ── searchable classes ──────────────────────────────────────────────────────

HERO_FRAG = "HERO_FRAG"
IMPACT = "IMPACT"
LG_TRACK = "LG_TRACK"
DODGE = "DODGE"
ONE_VX = "1VX"
ONE_VX_WIN = "1VX_WIN"
ONE_VX_LOSS_STRONG = "1VX_LOSS_STRONG_ACTION"
TEAM_ROUND = "TEAM_ROUND"
ASSISTED_ROUND_FINISH = "ASSISTED_ROUND_FINISH"
DAMAGE_SEQUENCE = "DAMAGE_SEQUENCE"
MOVEMENT = "MOVEMENT"
JUMP = "JUMP"
JUMPPAD = "JUMPPAD"
TELEPORT = "TELEPORT"
ROCKET_JUMP = "ROCKET_JUMP"
GRENADE_JUMP = "GRENADE_JUMP"
PLASMA_MOVEMENT = "PLASMA_MOVEMENT"
ITEM_USE = "ITEM_USE"
WEAPON_SWITCH = "WEAPON_SWITCH"
GAUNTLET = "GAUNTLET"
PROJECTILE_CINEMATIC = "PROJECTILE_CINEMATIC"
RECONSTRUCTED_PROJECTILE_CINEMATIC = "RECONSTRUCTED_PROJECTILE_CINEMATIC"
TRANSITION_MATERIAL = "TRANSITION_MATERIAL"
MOTIF_MATERIAL = "MOTIF_MATERIAL"
CHAT_REACTION_CANDIDATE = "CHAT_REACTION_CANDIDATE"
DEATH_MATERIAL = "DEATH_MATERIAL"

CLASSES = (HERO_FRAG, IMPACT, LG_TRACK, DODGE, ONE_VX, ONE_VX_WIN,
           ONE_VX_LOSS_STRONG, TEAM_ROUND, ASSISTED_ROUND_FINISH,
           DAMAGE_SEQUENCE, MOVEMENT, JUMP, JUMPPAD, TELEPORT, ROCKET_JUMP,
           GRENADE_JUMP, PLASMA_MOVEMENT, ITEM_USE, WEAPON_SWITCH, GAUNTLET,
           PROJECTILE_CINEMATIC, RECONSTRUCTED_PROJECTILE_CINEMATIC,
           TRANSITION_MATERIAL, MOTIF_MATERIAL, CHAT_REACTION_CANDIDATE,
           DEATH_MATERIAL)

# What each class reads. A class whose table is absent reports UNKNOWN
# coverage rather than zero -- "we did not look" is not "there is none".
CLASS_EVIDENCE: dict[str, tuple[str, ...]] = {
    HERO_FRAG: ("recognized_frags",),
    IMPACT: ("recognized_frags",),
    LG_TRACK: ("semantic_events_v1",),
    DODGE: ("recognized_frags",),
    ONE_VX: ("round_state_v1", "semantic_events_v1", "player_teams_v1"),
    ONE_VX_WIN: ("round_state_v1", "semantic_events_v1", "player_teams_v1"),
    ONE_VX_LOSS_STRONG: ("round_state_v1", "semantic_events_v1", "player_teams_v1"),
    TEAM_ROUND: ("player_teams_v1", "round_state_v1"),
    ASSISTED_ROUND_FINISH: ("recognized_frags", "player_teams_v1"),
    DAMAGE_SEQUENCE: ("semantic_events_v1",),
    MOVEMENT: ("semantic_events_v1",),
    JUMP: ("semantic_events_v1",),
    JUMPPAD: ("semantic_events_v1",),
    TELEPORT: ("teleport_transits_v1",),
    ROCKET_JUMP: ("semantic_events_v1", "missile_samples_v1"),
    GRENADE_JUMP: ("semantic_events_v1", "missile_samples_v1"),
    PLASMA_MOVEMENT: ("semantic_events_v1",),
    ITEM_USE: ("semantic_events_v1",),
    WEAPON_SWITCH: ("semantic_events_v1",),
    GAUNTLET: ("recognized_frags",),
    PROJECTILE_CINEMATIC: ("missile_samples_v1",),
    RECONSTRUCTED_PROJECTILE_CINEMATIC: ("missile_samples_v1", "recognized_frags"),
    TRANSITION_MATERIAL: ("semantic_events_v1",),
    MOTIF_MATERIAL: ("recognized_frags",),
    CHAT_REACTION_CANDIDATE: ("server_text_v1", "recognized_frags"),
    DEATH_MATERIAL: ("semantic_events_v1",),
}


@dataclass(frozen=True)
class ArchiveMoment:
    """One searchable thing, addressed by recording and time."""
    content_hash: str
    server_time_ms: int
    klass: str
    subject_client: int | None = None
    frag_id: int | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    @property
    def demo_us(self) -> int:
        return self.server_time_ms * 1000

    @property
    def identity(self) -> tuple[str, int, str]:
        """Never map + time: the recording comes first."""
        return (self.content_hash, self.server_time_ms, self.klass)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["demo_us"] = self.demo_us
        return d


def _tables(db: sqlite3.Connection) -> set[str]:
    return {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


# Weapon codes in the WP_ launcher space, as carried by events and samples.
WP_GAUNTLET, WP_GRENADE, WP_ROCKET, WP_LIGHTNING, WP_PLASMA = 1, 4, 5, 6, 8

_QUERIES: dict[str, str] = {
    JUMP: """SELECT content_hash, server_time_ms, client_num FROM semantic_events_v1
             WHERE type='jump' AND source='playerstate'""",
    JUMPPAD: """SELECT content_hash, server_time_ms, client_num FROM semantic_events_v1
                WHERE type='jump_pad' AND source='playerstate'""",
    WEAPON_SWITCH: """SELECT content_hash, server_time_ms, client_num FROM semantic_events_v1
                      WHERE type='change_weapon' AND source='playerstate'""",
    ITEM_USE: """SELECT content_hash, server_time_ms, client_num FROM semantic_events_v1
                 WHERE type IN ('item_pickup','use_item') AND source='playerstate'""",
    DEATH_MATERIAL: """SELECT content_hash, server_time_ms, entity_num FROM semantic_events_v1
                       WHERE type IN ('death','gib_player')""",
    TELEPORT: """SELECT content_hash, server_time_ms, client FROM teleport_transits_v1
                 WHERE outcome='TELEPORT_PLAYER_CONFIRMED'""",
}


def count_by_class(*, db_path: Path | None = None,
                   canonical: Iterable[str] | None = None) -> dict[str, Any]:
    """How much of each class the archive holds.

    A class whose evidence table is missing reports coverage UNKNOWN instead
    of a count of zero, so "not measured" never reads as "not there".
    """
    path = Path(db_path or RECOGNITION_DB)
    keep = set(canonical) if canonical is not None else None
    out: dict[str, Any] = {}
    with sqlite3.connect(path, timeout=60) as db:
        have = _tables(db)
        for klass in CLASSES:
            needed = CLASS_EVIDENCE.get(klass, ())
            if not set(needed) <= have:
                out[klass] = {"coverage": UNKNOWN,
                              "missing_evidence": sorted(set(needed) - have)}
                continue
            sql = _QUERIES.get(klass)
            if sql is None:
                out[klass] = {"coverage": "NOT_INDEXED",
                              "evidence": list(needed)}
                continue
            rows = db.execute(sql).fetchall()
            if keep is not None:
                rows = [r for r in rows if r[0] in keep]
            out[klass] = {"coverage": "INDEXED", "moments": len(rows),
                          "recordings": len({r[0] for r in rows})}
    out["version"] = SEARCH_VERSION
    return out


def find(klass: str, *, limit: int = 50, db_path: Path | None = None,
         canonical: Iterable[str] | None = None,
         content_hash: str | None = None) -> list[ArchiveMoment]:
    """Moments of one class, over the whole archive."""
    if klass not in CLASSES:
        raise ValueError(f"{klass!r} is not a searchable class")
    sql = _QUERIES.get(klass)
    if sql is None:
        return []
    path = Path(db_path or RECOGNITION_DB)
    keep = set(canonical) if canonical is not None else None
    out: list[ArchiveMoment] = []
    with sqlite3.connect(path, timeout=60) as db:
        if not set(CLASS_EVIDENCE.get(klass, ())) <= _tables(db):
            return []
        if content_hash:
            sql += " AND content_hash=?" if "WHERE" in sql else " WHERE content_hash=?"
            rows = db.execute(sql, (content_hash,))
        else:
            rows = db.execute(sql)
        for h, t, who in rows:
            if keep is not None and h not in keep:
                continue
            out.append(ArchiveMoment(h, int(t), klass,
                                     None if who is None else int(who)))
            if len(out) >= limit:
                break
    return out


def dense_windows(klass: str, *, window_ms: int = 5000, top: int = 20,
                  db_path: Path | None = None,
                  canonical: Iterable[str] | None = None
                  ) -> list[tuple[str, int, int]]:
    """Where this class clusters: (content_hash, window start, count).

    Density is what a montage or a movement transition needs -- one jump is
    not material, twenty in five seconds is.
    """
    sql = _QUERIES.get(klass)
    if sql is None:
        return []
    path = Path(db_path or RECOGNITION_DB)
    keep = set(canonical) if canonical is not None else None
    counts: dict[tuple[str, int], int] = {}
    with sqlite3.connect(path, timeout=60) as db:
        if not set(CLASS_EVIDENCE.get(klass, ())) <= _tables(db):
            return []
        for h, t, _who in db.execute(sql):
            if keep is not None and h not in keep:
                continue
            counts[(h, (int(t) // window_ms) * window_ms)] = \
                counts.get((h, (int(t) // window_ms) * window_ms), 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])[:top]
    return [(h, w, n) for (h, w), n in ranked]
