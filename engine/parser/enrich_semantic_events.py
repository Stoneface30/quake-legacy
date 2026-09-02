"""One-time corpus enrichment: the atomic events the caches never held.

WHAT THIS IS NOT. It is not a re-mine. Frag recognition, aim, LG contacts,
projectile paths, dodge geometry and scene scores are not recomputed. This
decodes only the streams `demo_parse` was already able to see but never
kept -- movement events, item and weapon events, chat and server text,
round state configstrings, missile entity samples -- and writes them once,
keyed by the demo's content hash so they join `recognized_frags` without a
filename anywhere in the new tables.

WHY BY CONTENT HASH. Demo filenames embed player aliases. Every table here
joins on `content_hash`, which `recognized_frags` already indexes, so the
composer never needs a name to reach an event.

PRIVACY. `server_text_v1` holds raw chat and print lines, which carry sender
names inside the text. It is an internal analysis table: anything that
exports from it must redact. The other tables hold slots, codes and numbers.

RESUMABLE. A demo already present under the current enrichment version is
skipped, so the job can be stopped and restarted without losing work.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from demo_parse import DM73Parser  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "creative_suite" / "database" / "frag_recognition.db"
DEMOS = ROOT / "demos"
ENRICH_VERSION = "semantic-events-v1.0.2"

# Everything demo_parse emits that the corpus caches did not already hold.
KEEP_EVENTS = ("jump", "jump_pad", "teleport_in", "teleport_out",
               "item_pickup", "use_item", "change_weapon", "drop_weapon",
               "fire_weapon", "noammo", "pain", "gib_player", "death",
               "drown", "taunt", "missile_hit", "missile_miss", "railtrail")

SCHEMA = """
CREATE TABLE IF NOT EXISTS enrichment_runs_v1(
  content_hash TEXT PRIMARY KEY, version TEXT NOT NULL,
  parsed_at TEXT NOT NULL, parse_ms INTEGER, events INTEGER,
  missiles INTEGER, text_lines INTEGER, round_rows INTEGER,
  packet_errors INTEGER);
CREATE TABLE IF NOT EXISTS semantic_events_v1(
  content_hash TEXT NOT NULL, server_time_ms INTEGER NOT NULL,
  round INTEGER, type TEXT NOT NULL, entity_num INTEGER, client_num INTEGER,
  victim INTEGER, weapon INTEGER, x REAL, y REAL, z REAL, parm INTEGER);
CREATE INDEX IF NOT EXISTS ix_sem_hash_t ON semantic_events_v1(content_hash, server_time_ms);
CREATE INDEX IF NOT EXISTS ix_sem_type ON semantic_events_v1(type);
CREATE TABLE IF NOT EXISTS round_state_v1(
  content_hash TEXT NOT NULL, server_time_ms INTEGER NOT NULL,
  round INTEGER, cs INTEGER NOT NULL, value TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_round_hash ON round_state_v1(content_hash);
CREATE TABLE IF NOT EXISTS server_text_v1(
  content_hash TEXT NOT NULL, server_time_ms INTEGER NOT NULL,
  round INTEGER, kind TEXT NOT NULL, text TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_text_hash ON server_text_v1(content_hash);
CREATE TABLE IF NOT EXISTS missile_samples_v1(
  content_hash TEXT NOT NULL, server_time_ms INTEGER NOT NULL,
  entity_num INTEGER NOT NULL, owner INTEGER, other INTEGER, weapon INTEGER,
  x REAL, y REAL, z REAL, vx REAL, vy REAL, vz REAL, eflags INTEGER,
  removed INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS ix_missile_hash_t ON missile_samples_v1(content_hash, server_time_ms);
CREATE TABLE IF NOT EXISTS player_teams_v1(
  content_hash TEXT NOT NULL, client INTEGER NOT NULL, team TEXT NOT NULL,
  PRIMARY KEY(content_hash, client));
"""


def content_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve(demo_name: str) -> Path | None:
    for cand in (DEMOS / demo_name, DEMOS / f"{demo_name}.dm_73"):
        if cand.exists():
            return cand
    return None


def enrich_one(con: sqlite3.Connection, chash: str, path: Path) -> dict:
    t0 = time.monotonic()
    out = DM73Parser(path, track_missiles=True).parse()
    parse_ms = int((time.monotonic() - t0) * 1000)
    ev_rows = []
    for e in out["events"]:
        if e.get("type") not in KEEP_EVENTS:
            continue
        ev_rows.append((chash, e.get("server_time_ms"), e.get("round_num"),
                        e["type"], e.get("entity_num"), e.get("client_num"),
                        e.get("victim"), e.get("weapon"),
                        e.get("pos_x", e.get("origin_x")),
                        e.get("pos_y", e.get("origin_y")),
                        e.get("pos_z", e.get("origin_z")), e.get("event_parm")))
    rs_rows = [(chash, r["server_time_ms"], r["round"], r["cs"], r["value"])
               for r in out["round_results"]]
    tx_rows = [(chash, t["server_time_ms"], t["round"], t["kind"], t["text"])
               for t in out["server_text"]]
    # Slot -> team only. Names stay out of every enrichment table.
    team_rows = [(chash, int(client), str(info.get("team") or "UNKNOWN"))
                 for client, info in (out.get("players") or {}).items()]
    ms_rows = [(chash, m["server_time_ms"], m["entity_num"], m.get("owner"),
                m.get("other"), m.get("weapon"), m.get("origin_x"), m.get("origin_y"),
                m.get("origin_z"), m.get("vel_x"), m.get("vel_y"),
                m.get("vel_z"), m.get("eflags"), 1 if m["removed"] else 0)
               for m in out["missiles"]]
    with con:
        for table in ("semantic_events_v1", "round_state_v1", "server_text_v1",
                      "missile_samples_v1", "player_teams_v1"):
            con.execute(f"DELETE FROM {table} WHERE content_hash=?", (chash,))
        con.executemany("INSERT INTO semantic_events_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ev_rows)
        con.executemany("INSERT INTO round_state_v1 VALUES (?,?,?,?,?)", rs_rows)
        con.executemany("INSERT INTO server_text_v1 VALUES (?,?,?,?,?)", tx_rows)
        con.executemany("INSERT INTO missile_samples_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ms_rows)
        con.executemany("INSERT OR REPLACE INTO player_teams_v1 VALUES (?,?,?)", team_rows)
        con.execute("INSERT OR REPLACE INTO enrichment_runs_v1 VALUES (?,?,datetime('now'),?,?,?,?,?,?)",
                    (chash, ENRICH_VERSION, parse_ms, len(ev_rows), len(ms_rows),
                     len(tx_rows), len(rs_rows), out.get("packet_errors", 0)))
    return {"parse_ms": parse_ms, "events": len(ev_rows), "missiles": len(ms_rows),
            "text": len(tx_rows), "rounds": len(rs_rows)}


def main(limit: int | None = None, verify_hash: bool = False) -> int:
    con = sqlite3.connect(DB)
    cols = [r[1] for r in con.execute("PRAGMA table_info(missile_samples_v1)")]
    if cols and "other" not in cols:
        # Dry-run rows from v1.0.0 lack the owner field; rebuild them.
        con.executescript("DROP TABLE missile_samples_v1; DELETE FROM enrichment_runs_v1;")
    con.executescript(SCHEMA)
    done = {r[0] for r in con.execute(
        "SELECT content_hash FROM enrichment_runs_v1 WHERE version=?", (ENRICH_VERSION,))}
    todo = [(h, n) for h, n in con.execute(
        "SELECT content_hash, demo_name FROM scanned_demos WHERE error IS NULL")
        if h not in done]
    if limit:
        todo = todo[:limit]
    print(f"enrichment {ENRICH_VERSION}: {len(done)} done, {len(todo)} to go", flush=True)
    t0 = time.monotonic()
    ok = missing = failed = 0
    for i, (chash, name) in enumerate(todo, 1):
        path = resolve(name)
        if path is None:
            missing += 1
            continue
        if verify_hash and content_hash(path) != chash:
            failed += 1
            continue
        try:
            enrich_one(con, chash, path)
            ok += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAILED {chash[:12]}: {type(exc).__name__}", flush=True)
        if i % 50 == 0:
            el = time.monotonic() - t0
            print(f"  {i}/{len(todo)}  ok {ok} missing {missing} failed {failed}  "
                  f"{el/60:.1f} min  ({el/i:.1f} s/demo)", flush=True)
    print(f"DONE ok {ok} missing {missing} failed {failed} in {(time.monotonic()-t0)/60:.1f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    raise SystemExit(main(lim, verify_hash="--verify" in sys.argv))
