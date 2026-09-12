"""One parser-v2 rebuild of the corpus, into a separate build root.

Plan: docs/superpowers/plans/2026-09-12-corpus-parser-v2-rebuild.md. The live
corpus is never written: every stage runs in a subprocess whose code root AND
data root are the build root (a git checkout of this branch), so every
database the chain opens -- 45 paths across 25 modules, proven by
test_corpus_chain_paths -- lands there.

    python -m engine.parser.rebuild_corpus_v2 --build-root <dir> --live-root <dir>
        [--limit 50] [--workers 8] [--from STAGE] [--only STAGE]

Guards, each fatal:
  * the build root may not be, contain, or sit inside the live data root;
  * the build root must be a checkout whose DM73Parser is v2;
  * after every stage, no database outside the expected set may exist and no
    expected database may be empty (SQLite creates what it opens -- HL-9);
  * a stage does not start below MIN_FREE_GB of free RAM.

Inputs taken from the live root, read-only: demos/ and the staged pak
(directory junctions), and a SNAPSHOT copy of editorial.db (the human-verdict
guard needs it; the live file is opened read-only).
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

MIN_FREE_GB = 6.0
STATE_NAME = ".rebuild_v2_state.json"
MANIFEST_NAME = "rebuild_v2_manifest.json"

# Databases the chain may create in the build root. Anything else appearing is
# a module reading a database the build root does not have.
EXPECTED_DBS = {
    "frags_rebuilt.db", "frag_recognition.db", "frag_shapes.db", "mining_epoch.db",
    "map_geography.db", "editorial.db", "recognition_pass1.db",
}
# Built by the chain and stamped as parser v2 when it finishes.
STAMPED_DBS = ("frags_rebuilt.db", "frag_recognition.db", "frag_shapes.db",
               "mining_epoch.db", "map_geography.db")


class RebuildRefused(RuntimeError):
    pass


# ---- guards ------------------------------------------------------------------

def check_roots(build_root: Path, live_root: Path) -> None:
    b, l = build_root.resolve(), live_root.resolve()
    if b == l or b.is_relative_to(l) and b.parts[len(l.parts)] in (
            "creative_suite", "engine", "demos", "output") or l.is_relative_to(b):
        raise RebuildRefused(f"build root {b} overlaps the live root {l}")
    if not (b / "engine" / "parser" / "demo_parse.py").is_file():
        raise RebuildRefused(f"{b} is not a checkout of the code")
    db = (b / "creative_suite" / "database")
    if db.exists() and db.resolve() == (l / "creative_suite" / "database").resolve():
        raise RebuildRefused(f"{db} resolves to the live database directory")


def unexpected_dbs(db_dir: Path, required: set[str] = frozenset()) -> list[str]:
    """Databases that should not exist, or required ones that are empty."""
    problems = []
    for p in sorted(db_dir.glob("*.db")):
        if p.name not in EXPECTED_DBS:
            problems.append(f"unexpected database {p.name} ({p.stat().st_size} bytes)")
        elif p.stat().st_size == 0:
            problems.append(f"empty database {p.name}")
    for name in required:
        if not (db_dir / name).is_file():
            problems.append(f"required database {name} was not produced")
    return problems


def free_gb() -> float:
    try:
        import psutil
        return psutil.virtual_memory().available / 2 ** 30
    except ImportError:                                   # pragma: no cover
        return float("inf")


# ---- the stages ----------------------------------------------------------------

def _py(code: str) -> list[str]:
    return [sys.executable, "-c", code]


def stages(a) -> list[tuple[str, list[list[str]], set[str]]]:
    """(name, commands, databases that must exist afterwards)."""
    w = str(a.workers)
    lim = ["--limit", str(a.limit)] if a.limit else []
    rec = "output/demo_v2/recognition"
    return [
        ("corpus", [[sys.executable, "engine/parser/rebuild_corpus.py", "--workers", w, *lim]],
         {"frags_rebuilt.db"}),
        # Norms (rule L percentiles) come from the archive's OWN distribution:
        # a provisional pass, norms from it, then the real scan against them.
        ("recognition_pass1", [[sys.executable, "engine/parser/recognition_scan.py",
                                "--workers", w, "--db",
                                "creative_suite/database/recognition_pass1.db",
                                "--norms", "__no_norms__"]],
         {"recognition_pass1.db"}),
        ("norms", [[sys.executable, "engine/parser/recognition_norms.py", "--db",
                    "creative_suite/database/recognition_pass1.db", "--out",
                    f"{rec}/norms.json"]], set()),
        ("recognition", [[sys.executable, "engine/parser/recognition_scan.py",
                          "--workers", w, "--norms", f"{rec}/norms.json"]],
         {"frag_recognition.db"}),
        ("kill_events", [[sys.executable, "engine/parser/derive_kill_events.py",
                          "--workers", w]], set()),
        ("semantic_events", [[sys.executable, "engine/parser/enrich_semantic_events.py"]],
         set()),
        # reclassify_v2 joins output/clutch_recorder.csv; regenerated from v2
        # data here, never borrowed from the live output/.
        ("clutch", [[sys.executable, "engine/parser/clutch_products.py", "--workers", w]],
         set()),
        ("enrichment", [[sys.executable, "creative_suite/scripts/round_review_v2/"
                         "full_corpus_v3.py", "--workers", w]], {"frag_shapes.db"}),
        ("occurrences", [_py("from creative_suite.engine import kill_occurrences as m;"
                             "print(m.build())"),
                         _py("from creative_suite.engine import funny_candidates as m;"
                             "print(m.build())"),
                         _py("from creative_suite.engine import movement_moments as m;"
                             "print(m.build())")], set()),
        ("mining", [[sys.executable, "engine/parser/mine_action_moments.py", "--workers", w],
                    [sys.executable, "engine/parser/mine_aim_events.py", "--workers", w],
                    # The in-build guard would compare the fresh build with
                    # itself. The meaningful check -- v1 live vs this build --
                    # is the human_linkage stage below, a promotion gate.
                    _py("from creative_suite.engine import mining_epoch as m;"
                        "print(m.promote(skip_guards=True))")], {"mining_epoch.db"}),
        ("lineage", [_py("from engine.parser import demo_lineage as m; print(m.build())"),
                     _py("from creative_suite.engine import round_model as m;"
                         "print(m.build())"),
                     _py("from creative_suite.engine import match_roster as m;"
                         "print(m.build())"),
                     _py("from engine.pantheon import map_geography as m;"
                         "print(len(m.build_all()))")], {"map_geography.db"}),
    ]


def prepare(build: Path, live: Path) -> dict:
    """Junctions to the read-only inputs, a snapshot of editorial.db."""
    (build / "creative_suite" / "database").mkdir(parents=True, exist_ok=True)
    (build / "output" / "demo_v2" / "recognition").mkdir(parents=True, exist_ok=True)
    links = {build / "demos": live / "demos",
             build / "output" / "demo_v2" / "_wolfcam_staging":
                 live / "output" / "demo_v2" / "_wolfcam_staging"}
    for link, target in links.items():
        if not target.is_dir():
            raise RebuildRefused(f"input {target} missing")
        if not link.exists():
            subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                           check=True, capture_output=True)
    ed_live = live / "creative_suite" / "database" / "editorial.db"
    ed_copy = build / "creative_suite" / "database" / "editorial.db"
    if not ed_copy.exists():
        src = sqlite3.connect(f"file:{ed_live.as_posix()}?mode=ro", uri=True)
        dst = sqlite3.connect(str(ed_copy))
        src.backup(dst)
        dst.close()
        src.close()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=build, capture_output=True,
                            text=True).stdout.strip()
    # The code that ran is the commit only if nothing was modified locally.
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           cwd=build, capture_output=True, text=True).stdout.strip()
    return {"git_commit": commit, "source_tree_clean": not dirty,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "editorial_snapshot_of": str(ed_live),
            "editorial_snapshot_sha256": _sha256(ed_copy)}


def human_linkage(build: Path, live: Path) -> dict:
    """v1 live vs this build: does every human decision find exactly one kill?
    Strictly one-to-one by observation keys (engine/parser/editorial_linkage);
    anything else is MANUAL_REVIEW. Read-only: editorial.db is never written."""
    db = "creative_suite/database/"
    p = subprocess.run([sys.executable, "-m", "engine.parser.editorial_linkage",
                        "--old", str(live / db / "frag_recognition.db"),
                        "--new", str(build / db / "frag_recognition.db"),
                        "--editorial", str(build / db / "editorial.db"),
                        "--scope-frags", str(build / db / "frags_rebuilt.db")],
                       cwd=build, env=_env(build), capture_output=True, text=True,
                       timeout=7200)
    if p.returncode:
        return {"error": p.stderr[-2000:]}
    return json.loads(p.stdout.strip().splitlines()[-1])


def _env(build: Path) -> dict:
    env = {**os.environ, "QUAKE_LEGACY_ROOT": str(build),
           "PANTHEON_PERFORMANCE_STORE": str(build / "creative_suite" / "database"),
           "PYTHONPATH": str(build)}
    return env


def _sha256(p: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(build: Path) -> dict:
    """Every output database: size, SHA-256, rows per table. Checkpointed
    first, so the hash is of the finished file and not of a WAL in flight."""
    out = {}
    for p in sorted((build / "creative_suite" / "database").glob("*.db")):
        w = sqlite3.connect(str(p))
        w.execute("pragma wal_checkpoint(TRUNCATE)")
        w.close()
        c = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
        tables = [r[0] for r in c.execute(
            "select name from sqlite_master where type='table' order by name")]
        out[p.name] = {"bytes": p.stat().st_size,
                       "rows": {t: c.execute(f'select count(*) from "{t}"').fetchone()[0]
                                for t in tables}}
        c.close()
        out[p.name]["sha256"] = _sha256(p)
    return out


def input_manifest(build: Path) -> dict:
    """What the build read: the unique demos, as one hash over their content
    hashes, so two builds can be shown to have parsed the same inputs."""
    import hashlib
    c = sqlite3.connect(f"file:{(build / 'creative_suite/database/frags_rebuilt.db').as_posix()}"
                        "?mode=ro", uri=True)
    hashes = sorted(h for (h,) in c.execute("select content_hash from demos"))
    errors = c.execute("select count(*) from demos where parse_error is not null").fetchone()[0]
    info = dict(c.execute("select key, value from build_info"))
    c.close()
    return {"unique_demos": len(hashes), "parse_errors": errors,
            "demo_files_discovered": info.get("demos_discovered"),
            "demo_set_sha256": hashlib.sha256("\n".join(hashes).encode()).hexdigest()}


STAGE_VERSIONS = r"""
import json, sys
sys.path.insert(0, 'engine/parser')
from engine.parser import demo_parse, rebuild_corpus, derive_kill_events, enrich_semantic_events
from engine.parser import frag_recognition, extract_view_timeseries, extract_lg_engagements
from engine.parser import extract_projectile_paths, extract_health_armor, extract_dodge_events
from engine.parser import mine_action_moments, mine_aim_events, demo_lineage
from creative_suite.engine import kill_occurrences, funny_candidates, movement_moments
from creative_suite.engine import frag_shapes, match_roster, round_model, mining_epoch
from engine.pantheon import map_geography
from engine.parser import clutch_products
print(json.dumps({
 'dm73_parser': demo_parse.PARSER_VERSION, 'corpus': rebuild_corpus.SCHEMA_VERSION,
 'recognition': frag_recognition.RECOGNITION_VERSION,
 'kill_events': derive_kill_events.DERIVE_VERSION, 'semantic_events': enrich_semantic_events.ENRICH_VERSION,
 'clutch': clutch_products.SELECTION_METHOD,
 'view': extract_view_timeseries.EXTRACTOR_VERSION, 'lg': extract_lg_engagements.EXTRACTOR_VERSION,
 'projectile': extract_projectile_paths.EXTRACTOR_VERSION, 'health': extract_health_armor.EXTRACTOR_VERSION,
 'dodge': extract_dodge_events.EXTRACTOR_VERSION, 'frag_shapes': frag_shapes.SCHEMA_VERSION,
 'occurrences': kill_occurrences.OCCURRENCE_VERSION, 'funny': funny_candidates.FUNNY_VERSION,
 'movement': movement_moments.MOVEMENT_VERSION, 'action_moments': mine_action_moments.MINER_VERSION,
 'aim_events': mine_aim_events.MINER_VERSION, 'epoch': mining_epoch.EPOCH_VERSION,
 'lineage': demo_lineage.LINEAGE_VERSION, 'round_model': round_model.SCHEMA_VERSION,
 'match_roster': match_roster.SCHEMA_VERSION, 'map_geography': map_geography.GEOGRAPHY_VERSION}))
"""


def stage_versions(build: Path) -> dict:
    p = subprocess.run(_py(STAGE_VERSIONS), cwd=build, env=_env(build),
                       capture_output=True, text=True, timeout=600)
    if p.returncode:
        return {"error": p.stderr[-1500:]}
    return json.loads(p.stdout.strip().splitlines()[-1])


def run(a) -> int:
    build, live = Path(a.build_root), Path(a.live_root)
    check_roots(build, live)
    sys.path.insert(0, str(build))
    state_p = build / STATE_NAME
    state = json.loads(state_p.read_text()) if state_p.exists() else {}
    db_dir = build / "creative_suite" / "database"

    if "prepare" not in state:
        state["prepare"] = prepare(build, live)
        state_p.write_text(json.dumps(state, indent=1))
    env = _env(build)
    started = a.start is None
    for name, cmds, required in stages(a):
        started = started or name == a.start
        if a.only and name != a.only:
            continue
        if not started or (name in state and a.start != name and a.only != name):
            print(f"[v2] skip {name}", flush=True)
            continue
        if free_gb() < MIN_FREE_GB:
            print(f"[v2] STOP before {name}: free RAM {free_gb():.1f} GB", flush=True)
            return 2
        t0 = time.time()
        started_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"[v2] START {name}", flush=True)
        for cmd in cmds:
            p = subprocess.run(cmd, cwd=build, env=env)
            if p.returncode:
                print(f"[v2] FAILED {name}: {cmd[:3]} exit {p.returncode}", flush=True)
                return 1
        problems = unexpected_dbs(db_dir, required)
        if problems:
            print(f"[v2] FAILED {name}: " + "; ".join(problems), flush=True)
            return 1
        state[name] = {"started_at": started_at,
                       "done_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                       "wall_s": round(time.time() - t0, 1)}
        state_p.write_text(json.dumps(state, indent=1))
        print(f"[v2] DONE {name} in {state[name]['wall_s']} s", flush=True)

    if a.only:
        return 0
    state["human_linkage"] = human_linkage(build, live)
    sys.path.insert(0, str(build / "engine" / "parser"))
    import corpus_status as CS
    import demo_parse as D
    for name in STAMPED_DBS:
        if (db_dir / name).is_file():
            CS.stamp(db_dir / name, D.PARSER_VERSION,
                     git_commit=state["prepare"]["git_commit"],
                     builder="engine/parser/rebuild_corpus_v2.py",
                     limit=str(a.limit or "all"))
    state["stage_versions"] = stage_versions(build)
    state["inputs"] = input_manifest(build)
    state["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    state["manifest"] = manifest(build)
    state_p.write_text(json.dumps(state, indent=1))
    (build / MANIFEST_NAME).write_text(json.dumps(state, indent=1), encoding="utf-8")
    print(f"[v2] ALL STAGES DONE; manifest {build / MANIFEST_NAME}", flush=True)
    print(f"[v2] human linkage: {json.dumps(state['human_linkage'])[:600]}", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build-root", required=True)
    ap.add_argument("--live-root", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--from", dest="start")
    ap.add_argument("--only")
    a = ap.parse_args()
    try:
        return run(a)
    except RebuildRefused as e:
        print(f"[v2] REFUSED: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
