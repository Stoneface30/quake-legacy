"""Headless benchmark — how long the loop takes, with no render anywhere.

Measures, per stage and repeated: parse a demo once; extract one ~5 s action;
retarget it; compile it to a synthetic demo; write it; read it back; compare.
Reports medians. The parse is reported separately because it is paid once
per demo and cached across every action in it; the loop that a developer
iterates on is everything after it.

    python -m engine.pantheon.headless_bench [--repeat 5] [--ref PERF:...]
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from engine.pantheon import headless as H
from engine.pantheon.compare import compare
from engine.pantheon.retarget import Retarget

OUT = Path("G:/QUAKE_LEGACY/creative_suite/generated/pantheon/bench")
DEFAULT = ("4db16c445bcaafce", 5, 1198725)      # REAL_ACTION_TRACE_PROOF_01


def bench(demo: Path, client: int, t_ms: int, *, pre_ms: int = 1500, post_ms: int = 3500,
          repeat: int = 5, out_dir: Path = OUT) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    lo, hi = t_ms - pre_ms, t_ms + post_ms
    t = time.perf_counter()
    parsed = H.parse(demo)
    parse_ms = (time.perf_counter() - t) * 1000

    stages = {k: [] for k in ("extract", "retarget", "compile", "write", "reextract",
                              "compare", "loop")}
    for i in range(repeat):
        t0 = time.perf_counter()
        t = time.perf_counter()
        tr = H.extract_performance(demo, client, lo, hi, parsed=parsed)
        stages["extract"].append((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        rt = Retarget.local_frame(tr, to=tr.transform[0].origin, yaw=tr.aim[0].yaw) \
            if i % 2 else Retarget.exact_world()
        stages["retarget"].append((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        compiled = H.compile_performance(tr, retarget=rt)
        stages["compile"].append((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        compiled.save(out_dir / f"bench_{i}.dm_73")
        stages["write"].append((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        back = H.reextract(compiled)
        stages["reextract"].append((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        d = compare(tr, back["PERF"], retarget=rt, intentional=compiled.intentional)
        stages["compare"].append((time.perf_counter() - t) * 1000)
        stages["loop"].append((time.perf_counter() - t0) * 1000)
        assert d.semantic_fidelity == "PASS", d.summary()

    report = {
        "demo": demo.name[:12] + "...", "client": client, "window_ms": [lo, hi],
        "action_samples": len(tr.transform), "repeat": repeat,
        "parse_once_ms": round(parse_ms, 1),
        "median_ms": {k: round(statistics.median(v), 2) for k, v in stages.items()},
        "max_ms": {k: round(max(v), 2) for k, v in stages.items()},
        "interactive": statistics.median(stages["loop"]) < 1000.0,
        "render_launched": False,
    }
    (out_dir / "bench.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--ref", help="PERF:<cat>:<hash>:<client>:<t_ms>")
    a = ap.parse_args()
    if a.ref:
        from engine.pantheon.performance_library import PerformanceRef, demo_path
        r = PerformanceRef.parse(a.ref)
        demo, client, t_ms = demo_path(r.demo_hash), r.client, r.t_ms
    else:
        from engine.pantheon.performance_library import demo_path
        demo, client, t_ms = demo_path(DEFAULT[0]), DEFAULT[1], DEFAULT[2]
    rep = bench(demo, client, t_ms, repeat=a.repeat)
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
