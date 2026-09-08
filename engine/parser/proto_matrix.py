"""realProto / build matrix across the demo corpus.

Answers section G of the 2026-08-29 brief: is there a deterministic protocol or
build value that separates the demos whose obituaries we can extract from the
ones we cannot? A `.dm_73` extension is not proof that the internal schema was
unchanged across Quake Live's lifetime.

Prints, per demo: protocol, version/build strings from CS_SERVERINFO, the demo's
own date, and the current decoded kill count.

    python engine/parser/proto_matrix.py [--limit 12] [--min-bytes 700000]
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

import demo_parse as D  # noqa: E402
import frag_classify as fc  # noqa: E402

# Keys worth pulling out of the serverinfo / systeminfo configstrings.
KEYS = ("protocol", "version", "gamename", "gamedate", "sv_protocol",
        "com_protocol", "gt_realm", "sv_pure", "fs_game")


def field(blob: str, key: str) -> str:
    m = re.search(re.escape("\\") + key + re.escape("\\") + r"([^\\]*)",
                  blob, re.I)
    return m.group(1) if m else "-"


def unique_demos(min_bytes: int, limit: int) -> list[Path]:
    """Largest-first, content-deduplicated. The corpus holds many exact copies."""
    seen: set[str] = set()
    out: list[Path] = []
    for q in sorted((ROOT / "demos").glob("*.dm_73"),
                    key=lambda z: -z.stat().st_size):
        if q.stat().st_size < min_bytes:
            continue
        try:
            h = hashlib.md5(q.read_bytes()).hexdigest()
        except OSError:
            continue
        if h in seen:
            continue
        seen.add(h)
        out.append(q)
        if len(out) >= limit:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--min-bytes", type=int, default=700_000)
    a = ap.parse_args()

    D._get_huff()
    rows = unique_demos(a.min_bytes, a.limit)
    print(f"{'demo':40} {'proto':>6} {'version':>24} {'kills':>6} {'obit71':>7}")
    print("-" * 88)

    for q in rows:
        try:
            p = D.DM73Parser(q)
            parsed = p.parse()
            kills = len(fc.classify(parsed))
            blob = " ".join(p._cs.values())
        except Exception as exc:
            print(f"{q.name[:40]:40} ERROR {type(exc).__name__}: {exc}")
            continue

        # Count obituary event entities directly, independent of classify().
        obit = sum(1 for e in parsed.get("events", [])
                   if e.get("type") == "obituary")

        print(f"{q.name[:40]:40} {field(blob, 'protocol'):>6} "
              f"{field(blob, 'version')[:24]:>24} {kills:>6} {obit:>7}")

    print("\nfull key dump for the first demo of each distinct protocol value:")
    seen_proto: set[str] = set()
    for q in rows:
        try:
            p = D.DM73Parser(q)
            p.parse()
            blob = " ".join(p._cs.values())
        except Exception:
            continue
        proto = field(blob, "protocol")
        if proto in seen_proto:
            continue
        seen_proto.add(proto)
        print(f"\n  {q.name}")
        for k in KEYS:
            v = field(blob, k)
            if v != "-":
                print(f"    {k:14} = {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
