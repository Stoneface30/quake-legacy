"""Does every human decision find exactly one kill in the rebuilt corpus?

Human verdicts, tags, dismissals, workshop requests and production marks in
editorial.db point at an OCCURRENCE ID, and a rebuild renumbers every one. So
a migration needs an old -> new mapping, and it must be STRICTLY ONE-TO-ONE or
it must not happen.

An occurrence is identified by its observations: kill_events_v1 rows keyed by
(content_hash, server_time_ms, killer_client, victim_client, mod) -- the
canonical demo, the time, the attacker, the victim and the means of death. An
old occurrence maps to a new one only when

  * its observation keys lead to exactly ONE new occurrence,
  * no other old occurrence leads to that same new one, and
  * the two kill fingerprints are equal.

Anything else -- no candidate, several, a shared one, a different fingerprint
-- goes to MANUAL_REVIEW. Nothing is guessed. This module READS ONLY: it never
writes editorial.db or either corpus.

    python -m engine.parser.editorial_linkage --old <v1 recog db> --new <v2 recog db>
        --editorial <editorial.db> [--scope-frags <v2 frags_rebuilt.db>]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ONE_TO_ONE = "ONE_TO_ONE"
UNMATCHED = "UNMATCHED"
AMBIGUOUS_MANY_NEW = "AMBIGUOUS_MANY_NEW"
AMBIGUOUS_SHARED = "AMBIGUOUS_SHARED"
FINGERPRINT_DIFFERS = "FINGERPRINT_DIFFERS"
OUT_OF_SCOPE = "OUT_OF_SCOPE"
NO_OLD_OCCURRENCE = "NO_OLD_OCCURRENCE"
SAFE = (ONE_TO_ONE,)


def _ro(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True, timeout=120)


def observations(db: Path) -> tuple[dict[int, set[tuple]], dict[int, str]]:
    """occurrence_id -> {observation keys}, occurrence_id -> kill fingerprint."""
    obs: dict[int, set[tuple]] = defaultdict(set)
    fp: dict[int, str] = {}
    with _ro(db) as c:
        for h, t, k, v, m, occ, f in c.execute(
                "select content_hash, server_time_ms, killer_client, victim_client, mod, "
                "occurrence_id, kill_fingerprint from kill_events_v1 "
                "where occurrence_id is not null"):
            obs[int(occ)].add((h, t, k, v, m))
            fp[int(occ)] = f
    return dict(obs), fp


def map_one_to_one(old_obs, old_fp, new_obs, new_fp, ids=None) -> dict[int, tuple[str, int | None]]:
    """old occurrence id -> (status, new id or None). Pure; unit-tested."""
    index: dict[tuple, set[int]] = defaultdict(set)
    for occ, keys in new_obs.items():
        for k in keys:
            index[k].add(occ)
    wanted = old_obs.keys() if ids is None else [i for i in ids if i in old_obs]
    cand = {i: set().union(*(index.get(k, set()) for k in old_obs[i])) for i in wanted}
    claims = Counter(next(iter(c)) for c in cand.values() if len(c) == 1)
    out: dict[int, tuple[str, int | None]] = {}
    for i, c in cand.items():
        if not c:
            out[i] = (UNMATCHED, None)
        elif len(c) > 1:
            out[i] = (AMBIGUOUS_MANY_NEW, None)
        else:
            n = next(iter(c))
            if claims[n] > 1:
                out[i] = (AMBIGUOUS_SHARED, None)
            elif old_fp.get(i) != new_fp.get(n):
                out[i] = (FINGERPRINT_DIFFERS, None)
            else:
                out[i] = (ONE_TO_ONE, n)
    return out


def linkage(old_db: Path, new_db: Path, editorial: Path,
            scope: set[str] | None = None) -> dict:
    from creative_suite.engine import human_migration as hm
    targets = hm.human_targets(editorial)                    # table -> [occurrence ids]
    ids = sorted({i for v in targets.values() for i in v})
    old_obs, old_fp = observations(old_db)
    new_obs, new_fp = observations(new_db)
    mapped = map_one_to_one(old_obs, old_fp, new_obs, new_fp, ids)
    rows, by_status = [], Counter()
    for table, tids in targets.items():
        for i in tids:
            if i not in old_obs:
                st, n = NO_OLD_OCCURRENCE, None
            elif scope is not None and not {k[0] for k in old_obs[i]} & scope:
                st, n = OUT_OF_SCOPE, None
            else:
                st, n = mapped[i]
            by_status[st] += 1
            rows.append({"table": table, "old_occurrence_id": i, "status": st,
                         "new_occurrence_id": n})
    manual = [r for r in rows if r["status"] not in SAFE + (OUT_OF_SCOPE,)]
    return {"human_targets": len(rows), "by_status": dict(by_status),
            "one_to_one": by_status[ONE_TO_ONE], "manual_review": manual,
            "migratable_without_review": not manual, "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--old", type=Path, required=True)
    ap.add_argument("--new", type=Path, required=True)
    ap.add_argument("--editorial", type=Path, required=True)
    ap.add_argument("--scope-frags", type=Path)
    a = ap.parse_args()
    scope = None
    if a.scope_frags:
        with _ro(a.scope_frags) as c:
            scope = {h for (h,) in c.execute("select content_hash from demos")}
    r = linkage(a.old, a.new, a.editorial, scope)
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
