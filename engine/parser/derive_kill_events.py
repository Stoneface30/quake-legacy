"""Canonical kill events: who killed whom, from EV_OBITUARY.

WHY THIS EXISTS. The corpus could answer "which of MY kills was good" and
nothing else. `recognized_frags` is the recorder's own killer-attributed set,
so every frag in it is a frag the recorder made. Everyone else's kills --
including the clan's -- were invisible, and the cached `death` rows could not
supply them: a death row carries the victim in `client_num` and nothing about
who did it. That was not a tuning problem, it was a missing field.

WHERE THE KILLER ACTUALLY IS. `demo_parse` has always decoded EV_OBITUARY with
both ends (demo_parse.py:969) -- `otherEntityNum` is the victim,
`otherEntityNum2` the attacker. The enrichment pass simply never listed
"obituary" in KEEP_EVENTS, so the one event that names the killer was parsed
and then dropped, 4,292 times. This pass keeps it.

WHY A REPARSE. The brief says not to reparse blindly if the data is cached.
It is not cached. Every other stream in `semantic_events_v1` was checked
first and none of them carries an attacker. So this parses, but it parses for
one thing only -- `track_missiles=False`, obituaries kept, everything else
discarded -- and it is resumable by content hash.

WHAT IT REFUSES TO DO. It does not force every obituary into "player A killed
player B". A demo is an observer's record, and the world kills people too:
falling, lava, the void, and one's own rocket. `killer_class` says who the
attacker slot refers to, `death_cause` says how the victim died, and neither
is inferred from the other.

ACTOR IS NOT RECORDER. `recorder_client` and `killer_client` are separate
columns for a reason. A frag by a clanmate seen in someone else's demo is
that clanmate's frag observed from a foreign camera -- it is not their
first-person view, and `is_recorder_killer` is the flag that keeps the two
apart.

    python engine/parser/derive_kill_events.py [--workers N] [--limit N]
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import re
import sqlite3
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "creative_suite" / "database" / "frag_recognition.db"
DEMOS = ROOT / "demos"
DERIVE_VERSION = "kill-events-v1.0.0"

# Entity-number space. Slots below MAX_CLIENTS are players; ENTITYNUM_WORLD is
# what the server names as the attacker when nobody killed you.
MAX_CLIENTS = 64
ENTITYNUM_WORLD = 1022
ENTITYNUM_NONE = 1023

# killer_class -- who, structurally, the attacker slot refers to.
KILLER_PLAYER = "PLAYER"                  # another client, not the victim
KILLER_SELF = "SELF"                      # attacker slot == victim slot
KILLER_WORLD = "WORLD"                    # ENTITYNUM_WORLD / NONE
KILLER_NON_PLAYER = "NON_PLAYER_ENTITY"   # a real entity that is not a client
KILLER_UNKNOWN = "UNKNOWN"

# death_cause -- how they died, read from the means of death and NOT inferred
# from the attacker slot. The two genuinely disagree: a telefrag has a player
# attacker, and a rocket suicide has a player attacker who is the victim.
MOD_TELEFRAG = 18
MOD_SUICIDE = 20
ENVIRONMENT_MODS = {14: "WATER", 15: "SLIME", 16: "LAVA", 17: "CRUSH",
                    19: "FALLING", 22: "TRIGGER_HURT"}

CAUSE_PLAYER_KILL = "PLAYER_KILL"
CAUSE_SUICIDE = "SUICIDE"
CAUSE_ENVIRONMENT = "ENVIRONMENT"
CAUSE_TELEFRAG = "TELEFRAG"
CAUSE_UNKNOWN = "UNKNOWN"

OBSERVED = "RECORDED_OBSERVED"       # seen in a demo we hold
EV_OBITUARY_PROV = "DEMO_EV_OBITUARY"

# Caret plus ONE DIGIT. A caret followed by a letter is part of the name.
_COLOR = re.compile(r"\^[0-9]")

SCHEMA = """
CREATE TABLE IF NOT EXISTS kill_events_v1(
  kill_event_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  content_hash      TEXT    NOT NULL,
  server_time_ms    INTEGER NOT NULL,
  demo_us           INTEGER NOT NULL,
  round             INTEGER,
  map               TEXT,
  killer_client     INTEGER,
  victim_client     INTEGER,
  mod               INTEGER,
  mod_name          TEXT,
  killer_class      TEXT    NOT NULL,
  death_cause       TEXT    NOT NULL,
  recorder_client   INTEGER,
  is_recorder_killer INTEGER NOT NULL DEFAULT 0,
  is_recorder_victim INTEGER NOT NULL DEFAULT 0,
  killer_name_raw   TEXT,
  killer_name_norm  TEXT,
  victim_name_raw   TEXT,
  victim_name_norm  TEXT,
  killer_identity_id TEXT,
  victim_identity_id TEXT,
  kill_fingerprint  TEXT,
  observation_provenance TEXT NOT NULL,
  event_provenance  TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_kill_hash_t ON kill_events_v1(content_hash, server_time_ms);
CREATE INDEX IF NOT EXISTS ix_kill_killer ON kill_events_v1(killer_name_norm);
CREATE INDEX IF NOT EXISTS ix_kill_victim ON kill_events_v1(victim_name_norm);
CREATE INDEX IF NOT EXISTS ix_kill_class ON kill_events_v1(killer_class);
CREATE INDEX IF NOT EXISTS ix_kill_fp ON kill_events_v1(kill_fingerprint);
CREATE TABLE IF NOT EXISTS kill_event_runs_v1(
  content_hash TEXT PRIMARY KEY, version TEXT NOT NULL, derived_at TEXT NOT NULL,
  parse_ms INTEGER, obituaries INTEGER, error TEXT);
"""


def normalize(name: str | None) -> str | None:
    """Strip Quake colour codes and case. The raw name is kept beside this --
    a name is evidence, and stripping it is a convenience, not a replacement."""
    if not name:
        return None
    return _COLOR.sub("", name).strip().lower() or None


def classify(killer: int | None, victim: int | None, mod: int | None
             ) -> tuple[str, str]:
    """Return (killer_class, death_cause). Two questions, answered separately."""
    if killer is None:
        kcls = KILLER_UNKNOWN
    elif killer in (ENTITYNUM_WORLD, ENTITYNUM_NONE):
        kcls = KILLER_WORLD
    elif victim is not None and killer == victim:
        kcls = KILLER_SELF
    elif killer < MAX_CLIENTS:
        kcls = KILLER_PLAYER
    else:
        kcls = KILLER_NON_PLAYER

    if mod == MOD_TELEFRAG:
        cause = CAUSE_TELEFRAG
    elif mod in ENVIRONMENT_MODS:
        cause = CAUSE_ENVIRONMENT
    elif mod == MOD_SUICIDE or kcls == KILLER_SELF:
        cause = CAUSE_SUICIDE
    elif kcls == KILLER_PLAYER:
        cause = CAUSE_PLAYER_KILL
    elif kcls == KILLER_WORLD:
        cause = CAUSE_ENVIRONMENT
    else:
        cause = CAUSE_UNKNOWN
    return kcls, cause


def fingerprint(map_name: str | None, t_ms: int, killer: int | None,
                victim: int | None, mod: int | None) -> str:
    """Identity of the historical kill, not of this observation of it.

    Two players in the same match record two demos that both see the same
    kill at the same server time. This is what lets those be recognised as
    one event later without asserting it here -- observations keep their own
    rows, and collapsing them is a separate, evidenced decision.
    """
    return f"{(map_name or '?').lower()}|{t_ms}|{killer}|{victim}|{mod}"


def _demo_path(name: str) -> Path | None:
    for cand in (DEMOS / name, DEMOS / f"{name}.dm_73"):
        if cand.exists():
            return cand
    return None


def derive_one(job: tuple[str, str, int | None]) -> dict:
    """Worker: parse one demo, keep obituaries, return rows. No DB here."""
    chash, demo_name, recorder = job
    path = _demo_path(demo_name)
    if path is None:
        return {"hash": chash, "error": "MISSING_DEMO", "rows": [], "parse_ms": 0}
    from demo_parse import DM73Parser
    t0 = time.monotonic()
    try:
        out = DM73Parser(path, track_missiles=False).parse()
    except Exception as exc:                                   # noqa: BLE001
        return {"hash": chash, "error": f"{type(exc).__name__}: {exc}",
                "rows": [], "parse_ms": int((time.monotonic() - t0) * 1000)}
    parse_ms = int((time.monotonic() - t0) * 1000)
    map_name = out.get("map")
    rows = []
    for e in out["events"]:
        if e.get("type") != "obituary":
            continue
        killer = e.get("killer_client")
        victim = e.get("victim_client")
        mod = e.get("weapon")
        kcls, cause = classify(killer, victim, mod)
        t_ms = int(e.get("server_time_ms") or 0)
        # Names as the parser held them AT THIS POINT IN THE STREAM -- the
        # configstring state when the obituary arrived, never a name lifted
        # from elsewhere in the demo. A slot that is not a player has no name,
        # and the parser's CLIENT_n placeholder is not one either.
        kname = e.get("killer_name") if kcls in (KILLER_PLAYER, KILLER_SELF) else None
        vname = e.get("victim_name") if victim is not None and victim < MAX_CLIENTS else None
        if kname and kname.startswith("CLIENT_"):
            kname = None
        if vname and vname.startswith("CLIENT_"):
            vname = None
        rows.append((
            chash, t_ms, t_ms * 1000, e.get("round"), map_name,
            killer, victim, mod, e.get("weapon_name"), kcls, cause,
            recorder,
            1 if (recorder is not None and killer == recorder
                  and kcls == KILLER_PLAYER) else 0,
            1 if (recorder is not None and victim == recorder) else 0,
            kname, normalize(kname), vname, normalize(vname),
            None, None,
            fingerprint(map_name, t_ms, killer, victim, mod),
            OBSERVED, EV_OBITUARY_PROV))
    return {"hash": chash, "error": None, "rows": rows, "parse_ms": parse_ms}


_INSERT = """INSERT INTO kill_events_v1(
  content_hash, server_time_ms, demo_us, round, map, killer_client,
  victim_client, mod, mod_name, killer_class, death_cause, recorder_client,
  is_recorder_killer, is_recorder_victim, killer_name_raw, killer_name_norm,
  victim_name_raw, victim_name_norm, killer_identity_id, victim_identity_id,
  kill_fingerprint, observation_provenance, event_provenance)
  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""


def main(workers: int = 8, limit: int | None = None) -> int:
    con = sqlite3.connect(DB, timeout=180)
    con.executescript(SCHEMA)
    done = {r[0] for r in con.execute(
        "SELECT content_hash FROM kill_event_runs_v1 WHERE version=? AND error IS NULL",
        (DERIVE_VERSION,))}
    todo = [(h, n, r) for h, n, r in con.execute(
        "SELECT content_hash, demo_name, recorder_client FROM scanned_demos "
        "WHERE error IS NULL") if h not in done]
    if limit:
        todo = todo[:limit]
    print(f"{DERIVE_VERSION}: {len(done)} done, {len(todo)} to go, "
          f"{workers} workers", flush=True)
    if not todo:
        return 0
    t0 = time.monotonic()
    ok = failed = missing = total_rows = 0
    with mp.Pool(workers) as pool:
        for i, res in enumerate(pool.imap_unordered(derive_one, todo, chunksize=1), 1):
            err = res["error"]
            if err == "MISSING_DEMO":
                missing += 1
            elif err:
                failed += 1
                print(f"  FAILED {res['hash'][:12]}: {err}", flush=True)
            else:
                ok += 1
                total_rows += len(res["rows"])
            with con:
                con.execute("DELETE FROM kill_events_v1 WHERE content_hash=?",
                            (res["hash"],))
                con.executemany(_INSERT, res["rows"])
                con.execute(
                    "INSERT OR REPLACE INTO kill_event_runs_v1 VALUES (?,?,datetime('now'),?,?,?)",
                    (res["hash"], DERIVE_VERSION, res["parse_ms"],
                     len(res["rows"]), err))
            if i % 100 == 0:
                el = time.monotonic() - t0
                rate = i / el
                print(f"  {i}/{len(todo)}  ok {ok} missing {missing} failed {failed}"
                      f"  kills {total_rows}  {el/60:.1f} min"
                      f"  eta {(len(todo)-i)/rate/60:.0f} min", flush=True)
    print(f"DONE ok {ok} missing {missing} failed {failed} kills {total_rows} "
          f"in {(time.monotonic()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    raise SystemExit(main(a.workers, a.limit))
