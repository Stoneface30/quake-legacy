"""Was the corpus on disk built with the parser gate G1 proved?

DM73Parser v2 (2026-09-12) agrees with the engine's own decoder on every field
(docs/reference/2026-09-12-corpus-parser-v2-status.md). Data derived from its
entity state -- which includes every obituary, so every frag -- built by an
earlier parser is STALE_PRE_PARSER_V2 until the corpus is rebuilt.

A database is CURRENT only if it carries a `corpus_build` row
`dm73_parser_version` >= ENTITY_DATA_MIN_PARSER. Nothing built before
2026-09-12 has one, so the whole existing corpus reads as stale -- without a
byte being written to it. This module only ever OPENS existing databases
read-only; `stamp()` is for databases a v2 rebuild has just created.

    python -m engine.parser.corpus_status            # report
    python -m engine.parser.corpus_status --write    # + CORPUS_STATUS.json beside them
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

ENTITY_DATA_MIN_PARSER = 2
STAMP_TABLE = "corpus_build"
CURRENT, STALE, MISSING = "CURRENT", "STALE_PRE_PARSER_V2", "MISSING"

# database -> the tables in it derived from DM73Parser entity state
# (docs/reference/2026-09-12-corpus-entity-derived-map.md).
CORPUS_DBS: dict[str, tuple[str, ...]] = {
    "frags_rebuilt.db": ("frags", "demos.raw_obituaries", "demos.accepted_frags"),
    "frag_recognition.db": (
        "recognized_frags", "scanned_demos", "kill_events_v1", "semantic_events_v1",
        "missile_samples_v1", "teleport_transits_v1", "stage2_visibility",
        "dodge_extracted", "recognition_dodge_events", "projectile_extracted",
        "recognition_projectile_paths", "lg_extracted", "recognition_lg_engagements",
        "view_extracted", "recognition_view_timeseries", "health_extracted",
        "kill_occurrences_v1", "funny_candidates_v1", "movement_moments_v1",
        "match_roster_v1", "match_format_v1", "action_moments_v1",
        # command/configstring tables: v1 applied resent commands twice and
        # lost split configstrings, so they change as well
        "round_state_v1", "server_text_v1", "team_changes_v1", "player_names_v1",
        "player_teams_v1", "round_outcome_v1"),
    "frag_shapes.db": ("frag_shapes_v1",),
    "mining_epoch.db": ("action_moments_v1", "demo_lineage_v1"),
    "map_geography.db": ("map_*_v1",),
    "match_roster.db": ("match_roster_v1", "match_format_v1"),
    "performance_index_v2.db": ("demos", "actions"),
    "performance_traces.db": ("traces", "uses"),
    "performance_templates.db": ("templates",),
}


class StaleCorpus(RuntimeError):
    """Entity-derived data was requested from a pre-parser-v2 database."""


def parser_stamp(db: Path) -> int | None:
    """The parser version a database was stamped with, or None. Read-only:
    a missing file is never created (SQLite would, if opened normally)."""
    if not db.is_file():
        return None
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        names = {r[0] for r in con.execute(
            "select name from sqlite_master where type='table'")}
        if STAMP_TABLE not in names:
            return None
        row = con.execute(f"select value from {STAMP_TABLE} "
                          "where key='dm73_parser_version'").fetchone()
        return int(row[0]) if row else None
    finally:
        con.close()


def db_status(db: Path) -> str:
    if not db.is_file():
        return MISSING
    v = parser_stamp(db)
    return CURRENT if v is not None and v >= ENTITY_DATA_MIN_PARSER else STALE


def status(db_dir: Path) -> dict:
    out = {}
    for name, tables in CORPUS_DBS.items():
        db = db_dir / name
        out[name] = {"status": db_status(db), "parser_version": parser_stamp(db),
                     "entity_derived_tables": list(tables)}
    return out


def require_current(db: Path) -> None:
    """Fail closed for code that must not consume pre-v2 entity data."""
    s = db_status(db)
    if s != CURRENT:
        raise StaleCorpus(f"{db} is {s}: entity-derived data predates DM73Parser "
                          f"v{ENTITY_DATA_MIN_PARSER}; rebuild the corpus")


def stamp(db: Path, parser_version: int, **extra: str) -> None:
    """Record how a NEWLY BUILT database was made. Never call this on the
    pre-v2 corpus: stamping is a claim that the data was built by this parser."""
    con = sqlite3.connect(str(db))
    try:
        con.execute(f"create table if not exists {STAMP_TABLE} "
                    "(key text primary key, value text)")
        rows = {"dm73_parser_version": str(parser_version),
                "stamped_at": time.strftime("%Y-%m-%dT%H:%M:%S"), **extra}
        con.executemany(f"insert or replace into {STAMP_TABLE} values (?, ?)",
                        list(rows.items()))
        con.commit()
    finally:
        con.close()


def main() -> int:
    from engine.pantheon import store as S
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db-dir", type=Path, default=None)
    ap.add_argument("--write", action="store_true",
                    help="write CORPUS_STATUS.json into the database directory")
    a = ap.parse_args()
    db_dir = a.db_dir or S.require_database_dir()
    report = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "db_dir": str(db_dir), "entity_data_min_parser": ENTITY_DATA_MIN_PARSER,
              "databases": status(db_dir)}
    for name, r in report["databases"].items():
        print(f"{r['status']:<22} {name}")
    if a.write:
        (db_dir / "CORPUS_STATUS.json").write_text(json.dumps(report, indent=2),
                                                   encoding="utf-8")
        print(f"wrote {db_dir / 'CORPUS_STATUS.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
