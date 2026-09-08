"""Re-attach review clips to frags after a re-derivation renumbered them.

`recognized_frags.id` is an auto-assigned rowid and the recognition scan
deletes and reinserts a demo's rows, so every rescanned demo gets NEW frag
ids. Review proxies are keyed on `frag_id`. That combination does not orphan a
clip -- it silently points it at a DIFFERENT frag, which is worse, because the
review looks fine and is wrong.

The defence is an identity that survives renumbering. A kill is identified by
its demo (content hash), the server time it happened, and who died; none of
those change when the row is rewritten. `frag_identity_map.json` is written
BEFORE a rescan and consumed here after it.

This only ever rewrites `review_proxies.frag_id`. It does not touch
HUMAN_USER review state, and it refuses to guess: a frag whose identity no
longer resolves is reported, not reassigned to something nearby.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REC_DB = REPO_ROOT / "creative_suite/database/frag_recognition.db"
ED_DB = REPO_ROOT / "creative_suite/database/editorial.db"
MAP = REPO_ROOT / "creative_suite/database/frag_identity_map.json"

# A kill can shift by a snapshot between derivations; more than this and it is
# a different moment, not the same one renumbered.
TIME_TOLERANCE_MS = 400


def load_map(path=None) -> list[dict]:
    with open(path or MAP, encoding="utf-8") as f:
        return json.load(f)["frags"]


def resolve(rec, entry) -> int | None:
    """The current frag id for a frozen identity, or None if it is gone."""
    row = rec.execute(
        "SELECT id FROM recognized_frags WHERE content_hash=? AND "
        "ABS(server_time_ms-?)<=? AND victim_client IS ? "
        "ORDER BY ABS(server_time_ms-?) LIMIT 1",
        (entry["content_hash"], entry["server_time_ms"], TIME_TOLERANCE_MS,
         entry["victim_client"], entry["server_time_ms"])).fetchone()
    if row:
        return row[0]
    # Victim may be recorded differently after a taxonomy change; fall back to
    # demo + time alone, which is still specific to one kill.
    row = rec.execute(
        "SELECT id FROM recognized_frags WHERE content_hash=? AND "
        "ABS(server_time_ms-?)<=? ORDER BY ABS(server_time_ms-?) LIMIT 1",
        (entry["content_hash"], entry["server_time_ms"], TIME_TOLERANCE_MS,
         entry["server_time_ms"])).fetchone()
    return row[0] if row else None


def relink(dry_run=True, rec_db=None, ed_db=None, map_path=None):
    rec = sqlite3.connect("file:%s?mode=ro" % (rec_db or REC_DB), uri=True,
                          timeout=60)
    ed = sqlite3.connect(str(ed_db or ED_DB), timeout=60)

    entries = load_map(map_path)
    unchanged = moved = lost = 0
    changes, missing = [], []
    for e in entries:
        now = resolve(rec, e)
        if now is None:
            lost += 1
            missing.append(e)
            continue
        if now == e["frag_id"]:
            unchanged += 1
            continue
        moved += 1
        changes.append((e["frag_id"], now, e["mp4_path"]))

    if not dry_run:
        for old, new, path in changes:
            # Move only the proxy row that owns this clip file. Matching on
            # the path as well as the id stops a re-run from dragging along
            # some other proxy that happens to share the old id.
            ed.execute("UPDATE review_proxies SET frag_id=? WHERE frag_id=? "
                       "AND mp4_path=?", (new, old, path))
        ed.commit()
    ed.close()
    return {"total": len(entries), "unchanged": unchanged, "moved": moved,
            "lost": lost, "changes": changes, "missing": missing,
            "applied": not dry_run}


if __name__ == "__main__":
    import sys
    dry = "--apply" not in sys.argv
    r = relink(dry_run=dry)
    print("%s: %d frags -- %d unchanged, %d renumbered, %d unresolvable"
          % ("DRY RUN" if dry else "APPLIED", r["total"], r["unchanged"],
             r["moved"], r["lost"]))
    for old, new, _p in r["changes"][:15]:
        print("   FRAG:%s -> FRAG:%s" % (old, new))
    for e in r["missing"][:10]:
        print("   LOST  %s t=%s (clip kept on disk)"
              % (e["content_hash"][:12], e["server_time_ms"]))
