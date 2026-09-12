"""Run a pytest suite one file per process, and stop before the machine starves.

WHY. `pytest creative_suite/tests` as a single process grows to ~12.6 GB.
On this workstation's normal background load that took free RAM to 4.3 GB,
Windows began compressing memory, and new processes failed to start
(`0xc0000142`, 2026-09-12). One process per file returns its memory to the
OS after every file, and a free-RAM guard stops the run instead of the
desktop.

    python scripts/run_tests_chunked.py creative_suite/tests --out baseline.txt
    python scripts/run_tests_chunked.py creative_suite/tests -k test_pantheon

Exit code: 0 all passed; 1 failures; 2 stopped by the RAM guard or a timeout.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    import psutil
except ImportError:                                   # pragma: no cover
    psutil = None

_SUMMARY = re.compile(r"(\d+) (passed|failed|skipped|error|errors|xfailed|xpassed)")


def free_gb() -> float:
    return psutil.virtual_memory().available / 2**30 if psutil else float("inf")


def run(root: Path, *, out: Path | None, min_free_gb: float, timeout: int,
        match: str | None) -> int:
    files = sorted(root.rglob("test_*.py"))
    if match:
        files = [f for f in files if match in f.name]
    totals: dict[str, int] = {}
    failed_files: list[str] = []
    lines: list[str] = []
    t0 = time.time()
    code = 0
    for i, f in enumerate(files, 1):
        if free_gb() < min_free_gb:
            lines.append(f"STOPPED before {f}: free RAM {free_gb():.1f} GB < {min_free_gb} GB")
            code = 2
            break
        try:
            p = subprocess.run([sys.executable, "-m", "pytest", str(f), "-q",
                                "-p", "no:cacheprovider"],
                               capture_output=True, text=True, timeout=timeout)
            tail = (p.stdout.strip().splitlines() or ["(no output)"])[-1]
        except subprocess.TimeoutExpired:
            tail = f"TIMEOUT after {timeout}s"
            code = 2
        counts = {k: int(n) for n, k in _SUMMARY.findall(tail)}
        for k, n in counts.items():
            totals[k] = totals.get(k, 0) + n
        bad = counts.get("failed", 0) + counts.get("error", 0) + counts.get("errors", 0)
        if bad or "TIMEOUT" in tail:
            failed_files.append(f"{f}: {tail}")
            code = max(code, 1)
        print(f"[{i}/{len(files)}] {f.name}: {tail}  (free {free_gb():.1f} GB)", flush=True)
    summary = ", ".join(f"{n} {k}" for k, n in sorted(totals.items()))
    lines = [f"chunked run of {root}: {summary} in {time.time() - t0:.0f}s",
             *(["files with failures:"] + [f"  {x}" for x in failed_files] if failed_files else []),
             *lines]
    text = "\n".join(lines) + "\n"
    print(text)
    if out:
        out.write_text(text, encoding="utf-8")
    return code


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--min-free-gb", type=float, default=6.0)
    ap.add_argument("--timeout", type=int, default=900, help="per file, seconds")
    ap.add_argument("-k", dest="match", help="only files whose name contains this")
    a = ap.parse_args()
    sys.exit(run(a.root, out=a.out, min_free_gb=a.min_free_gb,
                 timeout=a.timeout, match=a.match))
