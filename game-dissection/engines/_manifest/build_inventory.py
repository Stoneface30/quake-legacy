#!/usr/bin/env python3
"""Phase A0 inventory — walk every engine tree, hash every file, classify useless files.

Non-destructive. Writes:
  inventory.json        — all files with sha256, size, mtime, tree, rel_path
  duplicates.json       — sha256 groups where file appears in >1 tree (exact dup)
  near_duplicates.json  — same rel_path across trees with different sha256
  useless.json          — junk files flagged for deletion (.git, build artifacts, OS cruft)
  DIFFS_TODO.md         — markdown checklist of near-dup files worth diffing
  summary.md            — human-readable stats
"""
from __future__ import annotations
import hashlib, json, os, sys, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"G:/QUAKE_LEGACY/tools/quake-source")
OUT  = Path(r"G:/QUAKE_LEGACY/game-dissection/engines/_manifest")
OUT.mkdir(parents=True, exist_ok=True)

TREES = [
    "quake1-source", "quake2-source", "quake3-source",
    "ioquake3", "quake3e", "q3mme",
    "wolfcamql-src", "wolfcamql-local-src",
    "darkplaces", "yamagi-quake2",
    "openarena-engine", "openarena-gamecode",
    "wolfet-source", "demodumper", "qldemo-python",
    "q3vm", "gtkradiant", "uberdemotools",
]

# Useless-file classification
USELESS_DIRS = {".git", ".svn", ".hg", "__pycache__", ".vs", ".idea",
                "node_modules", ".pytest_cache", ".mypy_cache"}
# Build-artifact dirs (only at top level or under build/)
BUILD_DIR_NAMES = {"build", "Build", "out", "Debug", "Release",
                   "x64", "Win32", "obj", "objs", "bin"}
# But NEVER treat the shipped tools/*/bin or executables as useless
OS_CRUFT = {"Thumbs.db", ".DS_Store", "desktop.ini", "ehthumbs.db"}
USELESS_EXT = {".o", ".obj", ".a", ".lib", ".pdb", ".ilk", ".exp",
               ".suo", ".user", ".ncb", ".sdf", ".opensdf", ".tlog",
               ".pyc", ".pyo", ".class",
               ".orig", ".rej", ".bak", ".swp", ".tmp"}
EDITOR_BACKUP_RE = re.compile(r".*~$")
ZIP_EXT = {".zip", ".tar", ".tgz", ".tar.gz", ".7z", ".rar"}

def classify_useless(rel: Path, size: int) -> str | None:
    parts = rel.parts
    name  = rel.name
    # Any path component is a useless dir?
    for p in parts[:-1]:
        if p in USELESS_DIRS:
            return f"vcs_or_cache_dir:{p}"
        if p in BUILD_DIR_NAMES:
            return f"build_artifact_dir:{p}"
    if name in OS_CRUFT:
        return "os_cruft"
    ext = rel.suffix.lower()
    if ext in USELESS_EXT:
        return f"build_artifact_ext:{ext}"
    if EDITOR_BACKUP_RE.match(name):
        return "editor_backup"
    if ext in ZIP_EXT and size > 1_000_000:
        return f"archive:{ext}"
    return None

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def walk_tree(tree: str):
    base = ROOT / tree
    if not base.exists():
        print(f"  SKIP missing: {tree}", file=sys.stderr)
        return
    n = 0
    for dirpath, dirnames, filenames in os.walk(base):
        # prune useless dirs in-place so we don't descend into them for HASHING,
        # but we still record them as useless via a cheap listing pass below
        dp = Path(dirpath)
        # record useless directories' contents without hashing (too wasteful)
        pruned_here = []
        keep = []
        for d in dirnames:
            if d in USELESS_DIRS:
                pruned_here.append(d)
            else:
                keep.append(d)
        dirnames[:] = keep
        # record the pruned dirs as a single 'useless_dir' entry
        for d in pruned_here:
            yield {
                "tree": tree,
                "rel_path": str((dp / d).relative_to(base)).replace("\\", "/"),
                "sha256": None,
                "size": None,
                "mtime": None,
                "useless": f"vcs_or_cache_dir:{d}",
                "is_dir": True,
            }
        for fn in filenames:
            p = dp / fn
            try:
                st = p.stat()
            except OSError:
                continue
            rel = p.relative_to(base)
            useless = classify_useless(rel, st.st_size)
            # Skip hashing for build artifacts and archives >50MB to save time
            if useless and useless.startswith(("build_artifact", "archive")) and st.st_size > 50_000_000:
                digest = None
            else:
                try:
                    digest = sha256_of(p)
                except OSError:
                    digest = None
            yield {
                "tree": tree,
                "rel_path": str(rel).replace("\\", "/"),
                "sha256": digest,
                "size": st.st_size,
                "mtime": int(st.st_mtime),
                "useless": useless,
                "is_dir": False,
            }
            n += 1
            if n % 2000 == 0:
                print(f"  {tree}: {n} files...", file=sys.stderr)
    print(f"  {tree}: {n} files done", file=sys.stderr)

def main():
    inventory = []
    for tree in TREES:
        print(f"==> {tree}", file=sys.stderr)
        for entry in walk_tree(tree):
            inventory.append(entry)

    (OUT / "inventory.json").write_text(json.dumps(inventory, indent=1))
    print(f"wrote inventory.json ({len(inventory)} entries)", file=sys.stderr)

    # Exact duplicates across trees (same sha, different tree)
    by_sha = defaultdict(list)
    for e in inventory:
        if e.get("is_dir"): continue
        if not e["sha256"]: continue
        if e["useless"]: continue  # don't bother dedup-ing junk
        by_sha[e["sha256"]].append(e)
    dup_groups = {sha: entries for sha, entries in by_sha.items()
                  if len({e["tree"] for e in entries}) > 1}
    (OUT / "duplicates.json").write_text(json.dumps(dup_groups, indent=1))

    # Near-duplicates: same rel_path, different sha, across >=2 trees
    by_path = defaultdict(list)
    for e in inventory:
        if e.get("is_dir"): continue
        if not e["sha256"]: continue
        if e["useless"]: continue
        by_path[e["rel_path"]].append(e)
    near_dups = {}
    for rel, entries in by_path.items():
        shas = {e["sha256"] for e in entries}
        trees = {e["tree"] for e in entries}
        if len(shas) > 1 and len(trees) > 1:
            near_dups[rel] = entries
    (OUT / "near_duplicates.json").write_text(json.dumps(near_dups, indent=1))

    # Useless flagged
    useless = [e for e in inventory if e["useless"]]
    (OUT / "useless.json").write_text(json.dumps(useless, indent=1))

    # DIFFS_TODO.md — interesting near-dup files (C/H sources only)
    interesting = []
    for rel, entries in near_dups.items():
        if rel.lower().endswith((".c", ".h", ".cpp", ".hpp", ".py")):
            interesting.append((rel, entries))
    interesting.sort()
    with (OUT / "DIFFS_TODO.md").open("w", encoding="utf-8") as f:
        f.write("# Near-Duplicate Files — Diff Targets\n\n")
        f.write(f"Total near-duplicate files: **{len(near_dups)}**\n")
        f.write(f"Interesting (C/H/CPP/PY): **{len(interesting)}**\n\n")
        f.write("These files exist at the same relative path in multiple trees but have different\n")
        f.write("contents — they are the INTERESTING files to document in DIFFS.md.\n\n")
        for rel, entries in interesting[:500]:
            trees = sorted({e["tree"] for e in entries})
            f.write(f"- `{rel}` — {', '.join(trees)}\n")
        if len(interesting) > 500:
            f.write(f"\n_(truncated: {len(interesting)-500} more)_\n")

    # Summary
    total_bytes = sum(e["size"] or 0 for e in inventory if not e.get("is_dir"))
    useless_bytes = sum(e["size"] or 0 for e in useless if not e.get("is_dir"))
    dup_bytes = 0
    for entries in dup_groups.values():
        # We can free (N-1) * size per exact-dup group (keep canonical)
        size = entries[0]["size"] or 0
        dup_bytes += size * (len(entries) - 1)

    with (OUT / "summary.md").open("w", encoding="utf-8") as f:
        f.write("# Engine Consolidation — Phase A0 Inventory Summary\n\n")
        f.write(f"Generated from `build_inventory.py` on {sorted({e['tree'] for e in inventory})[0]}...\n\n")
        f.write(f"- Trees scanned: **{len(TREES)}**\n")
        f.write(f"- Total files: **{sum(1 for e in inventory if not e.get('is_dir'))}**\n")
        f.write(f"- Total bytes: **{total_bytes:,}** ({total_bytes/1e9:.2f} GB)\n")
        f.write(f"- Unique sha256 (non-useless): **{len({e['sha256'] for e in inventory if e['sha256'] and not e['useless']})}**\n")
        f.write(f"- Exact-duplicate groups across trees: **{len(dup_groups)}**\n")
        f.write(f"- Bytes reclaimable via exact-dup dedup: **{dup_bytes:,}** ({dup_bytes/1e6:.1f} MB)\n")
        f.write(f"- Near-duplicate paths (interesting diffs): **{len(near_dups)}**\n")
        f.write(f"- Useless entries flagged: **{len(useless)}**\n")
        f.write(f"- Bytes reclaimable from useless files: **{useless_bytes:,}** ({useless_bytes/1e6:.1f} MB)\n\n")
        f.write("## Per-tree sizes\n\n")
        per_tree = defaultdict(lambda: [0, 0])  # [count, bytes]
        for e in inventory:
            if e.get("is_dir"): continue
            per_tree[e["tree"]][0] += 1
            per_tree[e["tree"]][1] += e["size"] or 0
        for tree, (cnt, b) in sorted(per_tree.items()):
            f.write(f"- `{tree}`: {cnt} files, {b/1e6:.1f} MB\n")

    print("done", file=sys.stderr)

if __name__ == "__main__":
    main()
