"""Whole-corpus enrichment for trait rules v3.

The Sep-8 v4 recognition rewrite left every one of its 34,047 frags without
the enrichment attributes (view/flick, LG, projectile, health, dodge,
visibility), so the v2 detectors -- the recorder's best-rated traits --
never fired outside 2,560 old rows. This re-runs every enrichment stage on
every demo, with the score gates lifted so ALL recorder frags are measured,
then reclassifies and rebuilds the shape table.

Resumable: each stage keeps its own done-table; stage markers in
full_corpus_v3.state.json skip finished stages on restart. Pure parsing --
no game process is launched.

    python -u full_corpus_v3.py [--workers 14] [--from STAGE]
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path("G:/QUAKE_LEGACY")
PARSER = ROOT / "engine" / "parser"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PARSER))
DB = ROOT / "creative_suite" / "database" / "frag_recognition.db"
BACKUP = Path("F:/QL_BACKUP/frag_recognition.before_v3_rescan.db")
STATE = Path(__file__).with_name("full_corpus_v3.state.json")
MARKERS = ("view_extracted", "lg_extracted", "projectile_extracted",
           "health_extracted", "dodge_extracted")


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def mark(stage, result):
    s = state()
    s[stage] = {"done_at": time.strftime("%Y-%m-%d %H:%M:%S"), "result": result}
    STATE.write_text(json.dumps(s, indent=1, default=str))


# ── stages ─────────────────────────────────────────────────────────────────
def s_clear(workers):
    assert BACKUP.exists() and BACKUP.stat().st_size == DB.stat().st_size, \
        "backup missing or incomplete: %s" % BACKUP
    c = sqlite3.connect(DB, timeout=120)
    out = {}
    for t in MARKERS:
        out[t] = c.execute("DELETE FROM %s" % t).rowcount
    c.commit()
    c.close()
    return out


def s_view(workers):
    import extract_view_timeseries as m

    def all_frags():                      # every frag, not just aim classes
        c = sqlite3.connect(f"file:{m.RECOG_DB}?mode=ro", uri=True)
        out = {}
        for d, t, a in c.execute("SELECT demo_name, server_time_ms, attributes"
                                 " FROM recognized_frags"):
            if json.loads(a or "{}").get("view_samples") is None:
                out.setdefault(d, []).append(t)
        c.close()
        return out
    m.candidate_map = all_frags
    return m.run(None, workers)


def s_refine(workers):
    import refine_view_metrics as m
    return m.run()


def s_lg(workers):
    import extract_lg_engagements as m
    return m.run(None, workers)


def s_projectile(workers):
    import extract_projectile_paths as m
    m.MIN_SCORE = 0.0                     # every rocket/grenade frag
    return m.run(None, max(4, workers // 2))


def s_health(workers):
    import extract_health_armor as m
    m.ALL_FRAGS = True
    return m.run(None, workers)


def s_dodge(workers):
    import extract_dodge_events as m
    return m.run(None, workers)


def _s2_chunk(cands, tmp):
    sys.path.insert(0, str(PARSER))
    import stage2_visibility as s2
    rows = s2.run(cands, Path(tmp), verbose=False)
    return tmp, sum(1 for r in rows if not r.get("error")), len(rows)


def s_stage2(workers):
    import stage2_visibility as s2
    cands = [c for c in s2.pick_candidates(10 ** 7) if c.get("path")]
    by_demo = {}
    for c in cands:
        by_demo.setdefault(c["path"], []).append(c)
    groups = list(by_demo.values())
    chunks = [[] for _ in range(workers * 4)]
    for i, g in enumerate(sorted(groups, key=len, reverse=True)):
        chunks[i % len(chunks)].extend(g)     # a demo stays in one chunk
    tmpdir = Path(tempfile.mkdtemp(prefix="s2_", dir=str(STATE.parent)))
    log("stage2: %d candidates in %d demos, %d chunks"
        % (len(cands), len(groups), sum(1 for c in chunks if c)))
    ok = total = 0
    main = sqlite3.connect(DB, timeout=120)
    main.execute(s2.DDL)
    cols = None
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_s2_chunk, ch, str(tmpdir / ("c%03d.db" % i)))
                for i, ch in enumerate(chunks) if ch]
        for n, f in enumerate(as_completed(futs), 1):
            tmp, k, t = f.result()
            ok += k
            total += t
            src = sqlite3.connect(tmp)
            cur = src.execute("SELECT * FROM stage2_visibility")
            cols = cols or [d[0] for d in cur.description]
            main.executemany("INSERT OR REPLACE INTO stage2_visibility (%s) VALUES (%s)"
                             % (",".join(cols), ",".join("?" * len(cols))), cur.fetchall())
            main.commit()
            src.close()
            os.remove(tmp)
            log("stage2 chunk %d/%d: %d/%d computed so far" % (n, len(futs), ok, total))
    main.close()
    return {"candidates": len(cands), "computed": ok, "rows": total}


def s_reclassify(workers):
    import reclassify_v2 as m
    return m.run()


def s_shapes(workers):
    from creative_suite.engine import frag_shapes as m
    # build_rounds reads frag_shapes.db; build()'s default target is the
    # recognition DB, which nothing downstream reads.
    return {"shapes": m.build(out_db=ROOT / "creative_suite/database/frag_shapes.db")}


def s_projectile_retry(workers):
    # first pass crashed on undecoded victim origins (fixed); retry only the
    # demos that failed -- their frags carry no projectile_path yet
    c = sqlite3.connect(DB, timeout=120)
    n = c.execute("DELETE FROM projectile_extracted WHERE status LIKE 'fail%'").rowcount
    c.commit()
    c.close()
    return {"retried_demos": n, **s_projectile(workers)}


# reclassify_pre runs before stage2 because stage2 picks its candidates from
# flick classes (CLEAN_FLICK, EXTREME_FLICK) that only reclassify writes.
STAGES = [("clear", s_clear), ("view", s_view), ("refine", s_refine),
          ("lg", s_lg), ("projectile", s_projectile), ("health", s_health),
          ("dodge", s_dodge), ("projectile_retry", s_projectile_retry),
          ("reclassify_pre", s_reclassify), ("stage2", s_stage2),
          ("reclassify", s_reclassify), ("shapes", s_shapes)]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--from", dest="start")
    a = ap.parse_args()
    done = state()
    started = a.start is None
    for name, fn in STAGES:
        started = started or name == a.start
        if not started or (name in done and a.start != name):
            log("skip", name)
            continue
        log("START", name)
        t0 = time.time()
        res = fn(a.workers)
        res = res if isinstance(res, dict) else {"result": str(res)[:500]}
        res["stage_wall_s"] = round(time.time() - t0, 1)
        mark(name, res)
        log("DONE", name, json.dumps(res, default=str)[:600])
    log("ALL STAGES DONE")
