"""Archive percentile tables for the recognition taxonomy (rule L).

Speed, distance, flick-rate, visibility and chain-rate labels must come from
the ARCHIVE's own distribution, never from hardcoded numbers. This module
computes quantile grids from a completed stage-1 recognition scan database
(READ-ONLY) and caches them to output/demo_v2/recognition/norms.json.

frag_recognition consumes a Norms object when one is available; without one
it falls back to built-in provisional thresholds and says "provisional" in
every reason that used them.

Metrics (only what stage-1 actually records -- nothing is fabricated):
    attacker_speed   killer_speed attribute (ups, recorder playerstate)
    victim_speed     victim_speed attribute (ups, entity stream)
    distance         killer->victim distance at the kill (units)
    flick_dps        deg_per_sec of the pre-kill sweep
    visibility_ms    victim entity-stream presence before the kill
    chain_kps        kills-per-second inside a multikill chain

Projectile travel time is listed in the taxonomy but stage-1 records no
projectile entities, so no table is built for it -- consumers must treat the
metric as absent, not zero.

    python -u engine/parser/recognition_norms.py                 # default db
    python -u engine/parser/recognition_norms.py --db pilot.db --out norms.json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from bisect import bisect_left
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

DEFAULT_DB = REPO / "creative_suite" / "database" / "frag_recognition.db"
DEFAULT_OUT = REPO / "output" / "demo_v2" / "recognition" / "norms.json"

MIN_SAMPLES = 200        # below this a percentile table is noise, not a norm
GRID_POINTS = 101        # quantiles at integer percentiles 0..100

METRICS = ("attacker_speed", "victim_speed", "distance", "flick_dps",
           "visibility_ms", "chain_kps")


class Norms:
    """Quantile-grid percentile lookup for archive metrics."""

    def __init__(self, tables: dict[str, list[float]],
                 counts: dict[str, int] | None = None,
                 meta: dict | None = None):
        self.tables = {k: list(v) for k, v in tables.items()
                       if len(v) == GRID_POINTS}
        self.counts = dict(counts or {})
        self.meta = dict(meta or {})

    def has(self, metric: str) -> bool:
        return metric in self.tables

    def percentile_of(self, metric: str, value: float) -> float | None:
        """Value -> archive percentile 0..100 (linear between grid points)."""
        grid = self.tables.get(metric)
        if grid is None or value is None:
            return None
        if value <= grid[0]:
            return 0.0
        if value >= grid[-1]:
            return 100.0
        i = bisect_left(grid, value)
        lo, hi = grid[i - 1], grid[i]
        frac = 0.0 if hi <= lo else (value - lo) / (hi - lo)
        return round((i - 1) + frac, 1)

    def value_at(self, metric: str, pct: int) -> float | None:
        grid = self.tables.get(metric)
        if grid is None:
            return None
        return grid[max(0, min(100, int(pct)))]


def _quantile_grid(values: list[float]) -> list[float]:
    values = sorted(values)
    n = len(values)
    return [values[min(n - 1, round(p / 100.0 * (n - 1)))]
            for p in range(GRID_POINTS)]


def compute_norms(db_path: str | Path) -> Norms:
    """Build percentile tables from a stage-1 scan db (opened READ-ONLY)."""
    samples: dict[str, list[float]] = {m: [] for m in METRICS}
    con = sqlite3.connect(f"file:{Path(db_path)}?mode=ro", uri=True)
    try:
        for (attrs_json,) in con.execute(
                "SELECT attributes FROM recognized_frags"):
            try:
                a = json.loads(attrs_json)
            except (TypeError, ValueError):
                continue
            if a.get("killer_speed") is not None:
                samples["attacker_speed"].append(float(a["killer_speed"]))
            if a.get("victim_speed") is not None:
                samples["victim_speed"].append(float(a["victim_speed"]))
            if a.get("distance") is not None:
                samples["distance"].append(float(a["distance"]))
            if a.get("deg_per_sec") is not None:
                samples["flick_dps"].append(float(a["deg_per_sec"]))
            if a.get("visibility_ms") is not None:
                samples["visibility_ms"].append(float(a["visibility_ms"]))
            mk = a.get("multikill")
            if isinstance(mk, dict):
                kps = mk.get("kills_per_second")
                if kps is None and mk.get("duration_ms"):
                    kps = mk["count"] / (mk["duration_ms"] / 1000.0)
                if kps is not None:
                    samples["chain_kps"].append(float(kps))
    finally:
        con.close()

    tables = {m: _quantile_grid(v) for m, v in samples.items()
              if len(v) >= MIN_SAMPLES}
    counts = {m: len(v) for m, v in samples.items()}
    meta = {"source_db": str(db_path),
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "min_samples": MIN_SAMPLES}
    return Norms(tables, counts, meta)


def save_norms(norms: Norms, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"tables": norms.tables, "counts": norms.counts,
                             "meta": norms.meta}, indent=1),
                 encoding="utf-8")


def load_norms(path: str | Path = DEFAULT_OUT) -> Norms | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return Norms(d.get("tables", {}), d.get("counts"), d.get("meta"))
    except (ValueError, OSError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args()
    norms = compute_norms(a.db)
    save_norms(norms, a.out)
    print(f"[norms] from {a.db}")
    for m in METRICS:
        n = norms.counts.get(m, 0)
        if norms.has(m):
            print(f"  {m:15s} n={n:7d}  p50={norms.value_at(m,50):.1f}"
                  f"  p90={norms.value_at(m,90):.1f}"
                  f"  p99={norms.value_at(m,99):.1f}")
        else:
            print(f"  {m:15s} n={n:7d}  INSUFFICIENT (<{MIN_SAMPLES})")
    print(f"[norms] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
