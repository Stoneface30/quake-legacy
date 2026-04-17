#!/usr/bin/env python3
"""Phase A1 — build canonical engine tree from inventory.

Writes to game-dissection/engines/:
  _canonical/<rel_path>         — one copy per unique file (from authority-ordered tree)
  <tree>/<rel_path>             — only near-duplicate variants (same path, different sha)
  _diffs/<rel_path>.diff.md     — DIFFS.md entries for near-dup C/H/CPP/PY files
  _manifest/canonical_map.json  — {rel_path: {canonical_sha, canonical_tree, variants: [...]}}
  _manifest/DELETE_READY.md     — checkpoint listing bytes to free before deletion

Authority order for picking canonical copy when multiple trees have same sha:
  wolfcamql-src > quake3e > q3mme > ioquake3 > quake3-source > others
"""
from __future__ import annotations
import json, shutil, subprocess, sys, os
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"G:/QUAKE_LEGACY/tools/quake-source")
OUT  = Path(r"G:/QUAKE_LEGACY/game-dissection/engines")
MAN  = OUT / "_manifest"

AUTHORITY = [
    "wolfcamql-src", "quake3e", "q3mme", "ioquake3", "quake3-source",
    "wolfcamql-local-src", "openarena-engine", "openarena-gamecode",
    "ioquake3", "q3vm", "demodumper", "uberdemotools",
    "quake1-source", "quake2-source", "yamagi-quake2", "darkplaces",
    "wolfet-source", "qldemo-python", "gtkradiant",
]
AUTH_RANK = {t: i for i, t in enumerate(AUTHORITY)}

def pick_canonical(entries):
    """Pick one entry from a list of same-sha entries using authority order."""
    return min(entries, key=lambda e: AUTH_RANK.get(e["tree"], 999))

def safe_copy(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def main():
    inv = json.loads((MAN / "inventory.json").read_text())
    print(f"loaded {len(inv)} entries", file=sys.stderr)

    # Index: drop dirs, drop useless, drop entries without sha
    files = [e for e in inv if not e.get("is_dir") and e["sha256"] and not e["useless"]]

    # Group by rel_path
    by_path = defaultdict(list)
    for e in files:
        by_path[e["rel_path"]].append(e)

    # Canonical directory
    canon_dir = OUT / "_canonical"
    if canon_dir.exists():
        print("removing old _canonical/", file=sys.stderr)
        shutil.rmtree(canon_dir)
    canon_dir.mkdir(parents=True)

    # Near-dup variant dirs — clear old per-tree dirs we manage
    # (only clear the ones we'll populate; don't touch unrelated)
    trees_with_variants = set()

    canonical_map = {}
    near_dup_paths = []

    n_canonical = 0
    n_variants  = 0

    for rel, entries in by_path.items():
        shas = {e["sha256"] for e in entries}
        if len(shas) == 1:
            # All copies identical — pick canonical by authority, copy once
            canon = pick_canonical(entries)
            src = ROOT / canon["tree"] / rel
            dst = canon_dir / rel
            try:
                safe_copy(src, dst)
                n_canonical += 1
            except OSError as e:
                print(f"  copy fail: {src} -> {dst}: {e}", file=sys.stderr)
                continue
            canonical_map[rel] = {
                "canonical_sha": canon["sha256"],
                "canonical_tree": canon["tree"],
                "size": canon["size"],
                "also_in": sorted({e["tree"] for e in entries if e["tree"] != canon["tree"]}),
                "variants": [],
            }
        else:
            # Near-dup: keep each unique sha as a per-tree variant
            # Pick canonical = the variant from highest-authority tree
            by_sha = defaultdict(list)
            for e in entries:
                by_sha[e["sha256"]].append(e)
            # canonical variant = the sha whose highest-authority tree is earliest
            best_sha = min(
                by_sha.keys(),
                key=lambda s: min(AUTH_RANK.get(e["tree"], 999) for e in by_sha[s])
            )
            canon = pick_canonical(by_sha[best_sha])
            src = ROOT / canon["tree"] / rel
            dst = canon_dir / rel
            try:
                safe_copy(src, dst)
                n_canonical += 1
            except OSError as e:
                print(f"  copy fail: {src}: {e}", file=sys.stderr)
                continue

            variants = []
            for sha, sha_entries in by_sha.items():
                if sha == best_sha:
                    continue
                v = pick_canonical(sha_entries)
                vsrc = ROOT / v["tree"] / rel
                vdst = OUT / v["tree"] / rel
                try:
                    safe_copy(vsrc, vdst)
                    n_variants += 1
                    trees_with_variants.add(v["tree"])
                except OSError as e:
                    print(f"  variant copy fail: {vsrc}: {e}", file=sys.stderr)
                    continue
                variants.append({
                    "tree": v["tree"],
                    "sha256": sha,
                    "size": v["size"],
                    "also_in": sorted({e["tree"] for e in sha_entries if e["tree"] != v["tree"]}),
                })

            canonical_map[rel] = {
                "canonical_sha": best_sha,
                "canonical_tree": canon["tree"],
                "size": canon["size"],
                "also_in": sorted({e["tree"] for e in by_sha[best_sha] if e["tree"] != canon["tree"]}),
                "variants": variants,
            }
            near_dup_paths.append(rel)

    (MAN / "canonical_map.json").write_text(json.dumps(canonical_map, indent=1))
    print(f"canonical files: {n_canonical}, variant copies: {n_variants}, near-dup paths: {len(near_dup_paths)}", file=sys.stderr)

    # ----- DIFFS.md per near-dup source file (C/H/CPP/PY) -----
    diffs_dir = OUT / "_diffs"
    if diffs_dir.exists():
        shutil.rmtree(diffs_dir)
    diffs_dir.mkdir()

    generated_diffs = 0
    for rel in near_dup_paths:
        if not rel.lower().endswith((".c", ".h", ".cpp", ".hpp", ".py")):
            continue
        entry = canonical_map[rel]
        if not entry["variants"]:
            continue
        # Build diff doc: canonical vs each variant via `diff --stat`
        canon_tree = entry["canonical_tree"]
        canon_src = ROOT / canon_tree / rel
        md_path = diffs_dir / (rel + ".diff.md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"# Diff: `{rel}`\n"]
        lines.append(f"**Canonical:** `{canon_tree}` (sha256 `{entry['canonical_sha'][:12]}...`, {entry['size']} bytes)\n")
        if entry["also_in"]:
            lines.append(f"Also identical in: {', '.join(entry['also_in'])}\n")
        lines.append("\n## Variants\n")
        for v in entry["variants"]:
            vtree = v["tree"]
            vsrc  = ROOT / vtree / rel
            lines.append(f"\n### `{vtree}`  — sha256 `{v['sha256'][:12]}...`, {v['size']} bytes\n")
            if v["also_in"]:
                lines.append(f"Also identical in: {', '.join(v['also_in'])}\n")
            # diff --stat
            try:
                res = subprocess.run(
                    ["diff", "-u", str(canon_src), str(vsrc)],
                    capture_output=True, text=True, timeout=30,
                    encoding="utf-8", errors="replace",
                )
                out = res.stdout or ""
                # Count changed lines for a quick stat line
                added   = sum(1 for l in out.splitlines() if l.startswith("+") and not l.startswith("+++"))
                removed = sum(1 for l in out.splitlines() if l.startswith("-") and not l.startswith("---"))
                lines.append(f"\n_Diff stat: +{added} / -{removed} lines_\n")
                # Only embed the diff if it's small (avoid giant files)
                if len(out) < 20000:
                    lines.append("\n```diff\n")
                    lines.append(out)
                    lines.append("\n```\n")
                else:
                    lines.append(f"\n_(full diff is {len(out)} bytes — see files directly)_\n")
            except Exception as e:
                lines.append(f"\n_(diff failed: {e})_\n")
        md_path.write_text("".join(lines), encoding="utf-8")
        generated_diffs += 1
        if generated_diffs % 50 == 0:
            print(f"  diffs: {generated_diffs}", file=sys.stderr)
    print(f"generated {generated_diffs} diff docs", file=sys.stderr)

    # ----- DELETE_READY.md checkpoint -----
    # Sum up the bytes currently in tools/quake-source/
    total_src_bytes = sum(e["size"] or 0 for e in inv if not e.get("is_dir"))
    canonical_bytes = sum(m["size"] or 0 for m in canonical_map.values())
    variant_bytes   = sum(v["size"] or 0 for m in canonical_map.values() for v in m["variants"])
    new_tree_bytes  = canonical_bytes + variant_bytes
    freed = total_src_bytes - new_tree_bytes

    with (MAN / "DELETE_READY.md").open("w", encoding="utf-8") as f:
        f.write("# Phase A1 Canonical Tree — Ready for Deletion Checkpoint\n\n")
        f.write("Canonical tree is built at `game-dissection/engines/_canonical/` plus\n")
        f.write("per-tree variant dirs at `game-dissection/engines/<tree>/`.\n\n")
        f.write("## Statistics\n\n")
        f.write(f"- Source trees size: **{total_src_bytes:,}** bytes ({total_src_bytes/1e6:.1f} MB)\n")
        f.write(f"- New canonical size: **{canonical_bytes:,}** bytes ({canonical_bytes/1e6:.1f} MB)\n")
        f.write(f"- Variant files size: **{variant_bytes:,}** bytes ({variant_bytes/1e6:.1f} MB)\n")
        f.write(f"- New tree total: **{new_tree_bytes:,}** bytes ({new_tree_bytes/1e6:.1f} MB)\n")
        f.write(f"- **Bytes freed by deletion: {freed:,} ({freed/1e6:.1f} MB)**\n\n")
        f.write("## To complete deletion (user must approve)\n\n")
        f.write("```bash\n")
        f.write("# Verify canonical tree is good first:\n")
        f.write("ls G:/QUAKE_LEGACY/game-dissection/engines/_canonical/\n")
        f.write("# Then, after approval:\n")
        for t in sorted({e['tree'] for e in inv}):
            f.write(f"rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/{t}'\n")
        f.write("```\n\n")
        f.write("## Trees preserved as variants (near-dup cases)\n\n")
        for t in sorted(trees_with_variants):
            f.write(f"- `{t}`\n")
        f.write(f"\nNear-dup paths: {len(near_dup_paths)}\n")
        f.write(f"DIFFS docs generated: {generated_diffs}\n")

    print("done", file=sys.stderr)

if __name__ == "__main__":
    main()
