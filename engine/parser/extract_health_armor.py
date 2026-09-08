"""Targeted extractor: recorder health/armor at candidate frags.

Architecture rule: the DB is the cache; raw demos are opened once per missing
atomic feature, for the candidate subset only. Candidates = frags in CA
clutches or MAIN_CA rows with highlight_score >= 10 (2,705 events / 1,251
demos measured 2026-08-30). Resumable via the health_extracted table.

Persists into recognized_frags.attributes:
  health_at_frag, armor_at_frag, engagement_start_health(-10s),
  engagement_start_armor, min_health_10s, min_armor_10s, biggest_drop_10s,
  health_recovered (min -> frag)
plus extractor bookkeeping in health_extracted(content_hash, version).

Usage: python -u engine/parser/extract_health_armor.py [--limit N] [--workers N]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
#
# The repo root has to be ON sys.path first. Python puts the SCRIPT's own
# directory there, not the working directory, so running this as
# `python engine/parser/extract_health_armor.py` raised
# ModuleNotFoundError: No module named 'engine' -- the module imported fine
# and the command line did not.
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"

# Bumped to 2 when --all widened the candidate set.
#
# The resume is keyed by DEMO, not by frag: a demo present in
# health_extracted is skipped entirely. That is correct while the candidate
# set is fixed, and wrong the moment it widens -- the 1,251 demos from the
# narrow run were skipped by the --all pass, so only their high-scoring frags
# ever got a value. Measured: narrow-run demos sit at 17.1% health coverage
# while demos the widened pass actually processed reach 45.3%.
#
# A version bump is the honest way to say "the question changed", and it
# re-opens exactly those demos without discarding the values already stored
# (candidate_map still skips any frag that has health).
# 3: the recognition rescan of 2026-09-08 REWROTE recognized_frags.attributes
# and wiped every health key out of it, while health_extracted still recorded
# those demos as done at version 2 -- so this pass skipped all of them and
# health coverage fell from 51% of frags to 3%. The bookkeeping was right
# about having run; it could not know its output had been overwritten
# downstream. A version bump re-opens exactly those demos, which is the
# mechanism this module already documents for the same class of problem.
EXTRACTOR_VERSION = 3
PRE_WINDOW_MS = 10_000
MIN_SCORE = 10.0
# Default for direct import; main() overwrites it from --all.
ALL_FRAGS = False


def candidate_map() -> dict[str, list[int]]:
    """demo_name -> [server_time_ms...] needing health."""
    c = sqlite3.connect(f"file:{RECOG_DB}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    out: dict[str, list[int]] = {}
    for r in c.execute("SELECT demo_name, server_time_ms, classes,"
                       " highlight_score, attributes FROM recognized_frags"):
        a = json.loads(r["attributes"] or "{}")
        if a.get("health_at_frag") is not None:
            continue    # cache hit
        # --all means ALL. The flag was assigned into globals() by main() and
        # then never read here, so it has silently done nothing: every run was
        # the narrow clutch-or-score-10 set regardless of what was asked for.
        #
        # Health is basic telemetry, not an editorial reward. Gating it behind
        # highlight_score also closes a loop -- a frag can need health evidence
        # to earn the context score that would have qualified it for health.
        if ALL_FRAGS:
            out.setdefault(r["demo_name"], []).append(r["server_time_ms"])
            continue

        cl = {x["name"] if isinstance(x, dict) else x
              for x in json.loads(r["classes"] or "[]")}
        if ((cl & {"CLUTCH_1V2", "CLUTCH_1V3", "CLUTCH_1V4_PLUS"})
                or (a.get("mode_pool") == "MAIN_CA"
                    and (r["highlight_score"] or 0) >= MIN_SCORE)):
            out.setdefault(r["demo_name"], []).append(r["server_time_ms"])
    c.close()
    return out


def _snap_time(s: dict) -> int | None:
    for k in ("server_time", "server_time_ms", "serverTime", "t_ms", "t"):
        if k in s and s[k] is not None:
            return int(s[k])
    return None


def extract_one(demo_path: str, frag_times: list[int]) -> dict[int, dict]:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from demo_parse import DM73Parser
    parsed = DM73Parser(Path(demo_path)).parse()
    # KEEP THE SUBJECT. A playerstate belongs to one client, and in Clan
    # Arena the recorder spectates, so the subject changes mid-demo. Building
    # one series across all of them silently mixes players together.
    series = []
    for s in parsed.get("snapshots", []):
        t = _snap_time(s)
        if t is None or s.get("health") is None:
            continue
        series.append((t, int(s["health"]), int(s.get("armor") or 0),
                       s.get("client_num"), s.get("damage_count")))
    series.sort()
    out: dict[int, dict] = {}
    if not series:
        return out
    for ft in frag_times:
        window = [row for row in series if ft - PRE_WINDOW_MS <= row[0] <= ft]
        if not window:
            continue

        # The subject at the frag is the one that counts. Anything earlier in
        # the window belonging to a DIFFERENT client is a different player's
        # health and is dropped rather than averaged in -- a POV change is a
        # discontinuity, not a data gap.
        subject = window[-1][3]
        pre = [row for row in window if row[3] == subject]
        if not pre:
            continue
        pov_changed = len(pre) != len(window)

        h_frag = pre[-1][1]
        a_frag = pre[-1][2]
        h_start, a_start = pre[0][1], pre[0][2]
        h_min = min(r[1] for r in pre)
        a_min = min(r[2] for r in pre)
        drops = [pre[i - 1][1] - pre[i][1] for i in range(1, len(pre))]

        # How stale is the reading? A value sampled 4 seconds before the kill
        # is not the health at the kill, and the consumer has to be able to
        # tell. Damage taken in the window comes from ps.damageCount, which is
        # the engine's own aggregated number rather than a health difference.
        sample_age_ms = ft - pre[-1][0]
        dmg = [r[4] for r in pre if r[4]]
        provenance = {
            "health_subject_client": subject,
            "health_sample_ms": pre[-1][0],
            "health_sample_age_ms": sample_age_ms,
            "health_samples_in_window": len(pre),
            "health_pov_changed_in_window": pov_changed,
            "health_method": "PLAYERSTATE_STAT_HEALTH",
            "damage_taken_max_in_window": max(dmg) if dmg else None,
        }
        out[ft] = {
            **provenance,
            "health_at_frag": h_frag,
            "armor_at_frag": a_frag,
            "engagement_start_health": h_start,
            "engagement_start_armor": a_start,
            "min_health_10s": h_min,
            "min_armor_10s": a_min,
            "biggest_drop_10s": max(drops) if drops else 0,
            "health_recovered": h_frag - h_min,
        }
    return out


def run(limit: int | None = None, workers: int = 8) -> dict:
    conn = sqlite3.connect(RECOG_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS health_extracted ("
                 " content_hash TEXT PRIMARY KEY, demo_name TEXT,"
                 " version INTEGER, events INTEGER, status TEXT,"
                 " extracted_at TEXT DEFAULT (datetime('now')))")
    conn.commit()

    fconn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    meta = {n: (p, dup or h) for n, p, h, dup in fconn.execute(
        "SELECT name, path, content_hash, duplicate_of FROM demos")}
    fconn.close()

    done = {r[0] for r in conn.execute(
        "SELECT content_hash FROM health_extracted WHERE version=? AND"
        " status='ok'", (EXTRACTOR_VERSION,))}

    cands = candidate_map()
    todo = []
    for demo, times in cands.items():
        path, h = meta.get(demo, (None, None))
        if path and h not in done:
            todo.append((demo, path, h, times))
    if limit:
        todo = todo[:limit]

    stats = {"eligible_events": sum(len(t) for t in cands.values()),
             "demos_to_open": len(todo), "events_updated": 0, "failed": 0}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(extract_one, path, times): (demo, h, times)
                for demo, path, h, times in todo}
        n = 0
        for fut in as_completed(futs):
            demo, h, times = futs[fut]
            n += 1
            try:
                res = fut.result()
            except Exception as e:   # noqa: BLE001 - per-demo isolation
                conn.execute("INSERT OR REPLACE INTO health_extracted"
                             " (content_hash, demo_name, version, events,"
                             " status) VALUES (?,?,?,?,?)",
                             (h, demo, EXTRACTOR_VERSION, 0,
                              f"fail: {type(e).__name__}"))
                conn.commit()
                stats["failed"] += 1
                continue
            for ft, feats in res.items():
                row = conn.execute(
                    "SELECT id, attributes FROM recognized_frags WHERE"
                    " demo_name=? AND server_time_ms=?", (demo, ft)).fetchone()
                if row is None:
                    continue
                a = json.loads(row[1] or "{}")
                a.update(feats)
                conn.execute("UPDATE recognized_frags SET attributes=?"
                             " WHERE id=?", (json.dumps(a), row[0]))
                stats["events_updated"] += 1
            conn.execute("INSERT OR REPLACE INTO health_extracted"
                         " (content_hash, demo_name, version, events, status)"
                         " VALUES (?,?,?,?, 'ok')",
                         (h, demo, EXTRACTOR_VERSION, len(res)))
            conn.commit()
            if n % 100 == 0:
                print(f"[health] {n}/{len(todo)} demos,"
                      f" {stats['events_updated']} events,"
                      f" {time.time()-t0:.0f}s", flush=True)
    stats["wall_s"] = round(time.time() - t0, 1)
    conn.close()
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--all", action="store_true",
                    help="every frag, not just clutches and high scores")
    args = ap.parse_args()
    ALL_FRAGS = args.all
    globals()["ALL_FRAGS"] = ALL_FRAGS
    print(json.dumps(run(args.limit, args.workers), indent=1))
