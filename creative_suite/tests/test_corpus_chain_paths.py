"""Every module in the parser-v2 rebuild chain writes where QUAKE_LEGACY_ROOT
points -- never into the live corpus behind its back.

The rebuild runs in a separate build root (plan 2026-09-12-corpus-parser-v2-
rebuild). A module that resolves its database from the code root or a drive
letter would read or write the live corpus from inside that build. Each module
is imported in a fresh interpreter with QUAKE_LEGACY_ROOT set to a temp
directory, and every .db path and demo directory it exposes must lie under it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]

CHAIN = [
    "engine.parser.rebuild_corpus", "engine.parser.recognition_scan",
    "engine.parser.derive_kill_events", "engine.parser.enrich_semantic_events",
    "engine.parser.stage2_visibility", "engine.parser.extract_view_timeseries",
    "engine.parser.extract_lg_engagements", "engine.parser.extract_projectile_paths",
    "engine.parser.extract_health_armor", "engine.parser.extract_dodge_events",
    "engine.parser.refine_view_metrics", "engine.parser.reclassify_v2",
    "engine.parser.mine_action_moments", "engine.parser.mine_aim_events",
    "engine.parser.demo_lineage", "engine.parser.ca_reference",
    "engine.parser.clutch_products",
    "creative_suite.engine.kill_occurrences", "creative_suite.engine.funny_candidates",
    "creative_suite.engine.movement_moments", "creative_suite.engine.frag_shapes",
    "creative_suite.engine.match_roster", "creative_suite.engine.round_model",
    "engine.pantheon.map_geography", "creative_suite.engine.mining_epoch",
]
SCRIPT = CODE / "creative_suite" / "scripts" / "round_review_v2" / "full_corpus_v3.py"

_PROBE = r"""
import importlib, importlib.util, json, sys
from pathlib import Path
sys.path[:0] = [CODE, CODE + "/engine/parser"]
out = {}
def scan(label, mod):
    for k, v in vars(mod).items():
        if isinstance(v, Path) and (v.suffix == ".db" or k in ("DEMOS", "DEMO_ROOT")):
            out[label + "." + k] = str(v)
for name in CHAIN:
    scan(name, importlib.import_module(name))
spec = importlib.util.spec_from_file_location("full_corpus_v3", SCRIPT)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
scan("full_corpus_v3", m)
print(json.dumps(out))
"""


def test_every_chain_database_follows_the_data_root(tmp_path):
    root = tmp_path / "build_root"
    (root / "creative_suite" / "database").mkdir(parents=True)
    env = {**os.environ, "QUAKE_LEGACY_ROOT": str(root)}
    code = (f"CODE = {str(CODE)!r}\nCHAIN = {CHAIN!r}\nSCRIPT = {str(SCRIPT)!r}\n"
            + _PROBE)
    r = subprocess.run([sys.executable, "-c", code], cwd=str(CODE), env=env,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr[-3000:]
    paths = json.loads(r.stdout.strip().splitlines()[-1])
    assert paths, "no database paths found -- the probe is blind"
    outside = {k: v for k, v in paths.items()
               if not Path(v).resolve().is_relative_to(root.resolve())
               and "F:/QL_BACKUP" not in v.replace("\\", "/")}
    assert not outside, outside
