"""Authoritative clip-folder rescan for Parts 4-7.

For each Part:
  1. Enumerate every *.avi on disk across T1/T2/T3, including FL files in subdirs.
  2. Group files by "frag key":
       - "Demo (107)  - 13.avi"   -> frag_key = "107"   (FP)
       - "Demo (107FL1).avi"      -> frag_key = "107"   (FL angle of 107)
     The demo number before "FL" or before ")" is the bond.
  3. For each frag key, list the FP file + FL files and flag mismatches
     (e.g. FL1 in T2/Part6 but FP is "Demo (107) - 13.avi" which is in T1/Part6 —
      that's two DIFFERENT frags sharing a demo number across tiers, which
      MUST be treated as independent).
  4. Cross-check against current partNN_styleb.txt — report orphans (AVIs on
     disk NOT referenced in styleb) and ghosts (styleb references not on disk).
  5. Output a proposed styleb rebuild per Part (FP > FL grammar for every
     multi-angle frag, singles listed separately, tier-grouped).

Run:  PYTHONPATH=. python scripts/rescan_clips.py
Writes: output/clip_audit_partNN.json + output/clip_audit_summary.txt
Side effect (opt-in via --apply): rewrites phase1/clip_lists/partNN_styleb.txt
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from phase1.config import Config
from phase1.clip_list import parse_clip_entry

# frag_key extractor: pulls the demo number out of a stem.
#   "Demo (107)  - 13"   -> "107"
#   "Demo (107FL1)"      -> "107"
#   "Demo (107FL2)"      -> "107"
#   "Demo (128) - 44;-FINALSCENE" -> "128"
#   "Demo (722)-001"     -> "722"
FRAG_KEY_RE = re.compile(r"Demo\s*\(\s*(\d+)(?:FL\d+)?\s*\)", re.IGNORECASE)
FL_RE = re.compile(r"Demo\s*\(\s*(\d+)FL(\d+)\s*\)", re.IGNORECASE)


def frag_key(stem: str) -> str | None:
    m = FRAG_KEY_RE.search(stem)
    return m.group(1) if m else None


def is_fl(stem: str) -> bool:
    return bool(FL_RE.search(stem))


def fl_index(stem: str) -> int:
    m = FL_RE.search(stem)
    return int(m.group(2)) if m else 0


def scan_part(part: int, root: Path) -> Dict[str, Dict]:
    """Return {tier: {unique_key: {fp: Path|None, fls: [Path sorted]}}}.

    unique_key = the FP file's stem for singles, and for multi-angle groups
    the FP stem of the subdirectory FP (FLs live in subdirs next to their FP).
    This separates e.g. Demo (868) - 1095 (root single) from Demo (868) - 1096
    (subdir with FLs) — both share demo number 868 but are distinct frags.
    """
    result: Dict[str, Dict[str, Dict]] = {"T1": {}, "T2": {}, "T3": {}}
    for tier in ("T1", "T2", "T3"):
        part_root = root / tier / f"Part{part}"
        if not part_root.exists():
            continue
        # Pass 1: find FP files. Root-level AVIs are singles. Subdir AVIs
        # that are NOT FL are the FP for that subdir (one per subdir).
        subdir_fp: Dict[Path, Path] = {}   # subdir -> FP file
        for avi in part_root.rglob("*.avi"):
            if is_fl(avi.stem):
                continue
            if avi.parent == part_root:
                # root single
                result[tier][avi.stem] = {"fp": avi, "fls": []}
            else:
                # subdir FP (should be unique per subdir)
                if avi.parent not in subdir_fp:
                    subdir_fp[avi.parent] = avi
                    result[tier][avi.stem] = {"fp": avi, "fls": []}
        # Pass 2: attach FLs to their subdir's FP.
        for avi in part_root.rglob("*.avi"):
            if not is_fl(avi.stem):
                continue
            fp = subdir_fp.get(avi.parent)
            if fp is None:
                # FL with no FP in the same dir — orphan, record under synthesized key
                result[tier].setdefault(f"__fl_orphan__/{avi.stem}",
                                        {"fp": None, "fls": []})["fls"].append(avi)
            else:
                result[tier][fp.stem]["fls"].append(avi)
        # sort FL lists by FL index
        for v in result[tier].values():
            v["fls"].sort(key=lambda p: fl_index(p.stem))
    return result


def styleb_refs(part: int, cfg: Config) -> set[str]:
    p = cfg.clip_lists_dir / f"part{part:02d}_styleb.txt"
    if not p.exists():
        return set()
    out: set[str] = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        entry = parse_clip_entry(line)
        for seg in entry.segments:
            out.add(seg.strip().lower())
    return out


def build_proposed(part_tiers: Dict[str, Dict[str, Dict]]) -> str:
    lines: List[str] = []
    lines.append(f"# Part clip list — rebuilt from disk scan (FP > FL grammar)")
    lines.append(f"# Rule P1-K: FL follows FP in same entry so renderer treats")
    lines.append(f"# them as ONE frag with FL as slow-contrast replay angle.")
    lines.append(f"# Rule P1-U tier-interleave handles pacing at render time.")
    lines.append("")
    for tier in ("T1", "T2", "T3"):
        fragments = part_tiers.get(tier, {})
        if not fragments:
            continue
        multi = sum(1 for v in fragments.values() if v["fls"])
        singles = len(fragments) - multi
        lines.append(f"# --- {tier} ({len(fragments)} frags: {multi} multi-angle + {singles} singles) ---")
        # multi-angle first, then singles (within each group stable by demo number)
        def sort_key(kv):
            k, v = kv
            dn = frag_key(k) or "9999"
            dn_int = int(dn) if dn.isdigit() else 9999
            return (0 if v["fls"] else 1, dn_int)
        for key, v in sorted(fragments.items(), key=sort_key):
            fp = v["fp"]
            fls = v["fls"]
            if fp is None:
                lines.append(f"# ORPHAN: frag {key} has FL angles but no FP: "
                             + ", ".join(p.name for p in fls))
                continue
            if fls:
                lines.append(" > ".join([fp.name] + [p.name for p in fls]))
            else:
                lines.append(fp.name)
        lines.append("")
    return "\n".join(lines) + "\n"


def audit_part(part: int, cfg: Config, root: Path) -> Dict:
    tiers = scan_part(part, root)
    refs = styleb_refs(part, cfg)
    total_frags = sum(len(t) for t in tiers.values())
    total_files = 0
    missing_fp = []
    orphans_on_disk: List[str] = []     # file on disk NOT referenced in styleb
    ghosts_in_styleb: List[str] = set(refs)  # start with all refs then remove matches
    ghosts_in_styleb = set(refs)
    fl_mismatches = []

    for tier, frags in tiers.items():
        for key, v in frags.items():
            files = ([v["fp"]] if v["fp"] else []) + v["fls"]
            total_files += len(files)
            if v["fls"] and v["fp"] is None:
                missing_fp.append(f"{tier} frag {key}")
            for f in files:
                nm = f.name.strip().lower()
                if nm in ghosts_in_styleb:
                    ghosts_in_styleb.discard(nm)
                else:
                    orphans_on_disk.append(f"{tier}/{f.name}")
            # FL ordering check
            if v["fls"]:
                idxs = [fl_index(p.stem) for p in v["fls"]]
                if idxs != sorted(idxs):
                    fl_mismatches.append(
                        f"{tier} frag {key}: FL indices out of order {idxs}"
                    )

    return {
        "part": part,
        "total_frags": total_frags,
        "total_files": total_files,
        "by_tier": {t: {"frags": len(v), "multi": sum(1 for x in v.values() if x["fls"])}
                    for t, v in tiers.items()},
        "missing_fp": missing_fp,
        "orphans_on_disk": sorted(orphans_on_disk),
        "ghosts_in_styleb": sorted(ghosts_in_styleb),
        "fl_mismatches": fl_mismatches,
        "proposed": build_proposed(tiers),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Overwrite partNN_styleb.txt with rebuilt list")
    ap.add_argument("--parts", nargs="+", type=int, default=[4, 5, 6, 7])
    args = ap.parse_args()

    cfg = Config()
    quake_root = cfg.clips_root
    out_dir = cfg.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    summary: List[str] = []
    for part in args.parts:
        audit = audit_part(part, cfg, quake_root)
        # snapshot without the big proposed string for JSON compactness
        snap = {k: v for k, v in audit.items() if k != "proposed"}
        (out_dir / f"clip_audit_part{part:02d}.json").write_text(
            json.dumps(snap, indent=2), encoding="utf-8"
        )
        (out_dir / f"clip_audit_part{part:02d}_proposed.txt").write_text(
            audit["proposed"], encoding="utf-8"
        )
        s = (
            f"Part {part}: {audit['total_frags']} frags, {audit['total_files']} files | "
            f"T1={audit['by_tier']['T1']['frags']}({audit['by_tier']['T1']['multi']}ma) "
            f"T2={audit['by_tier']['T2']['frags']}({audit['by_tier']['T2']['multi']}ma) "
            f"T3={audit['by_tier']['T3']['frags']}({audit['by_tier']['T3']['multi']}ma) | "
            f"orphans_on_disk={len(audit['orphans_on_disk'])} "
            f"ghosts_in_styleb={len(audit['ghosts_in_styleb'])} "
            f"fl_mismatches={len(audit['fl_mismatches'])} "
            f"missing_fp={len(audit['missing_fp'])}"
        )
        print(s)
        summary.append(s)
        if audit["orphans_on_disk"]:
            for o in audit["orphans_on_disk"][:5]:
                print(f"   ORPHAN: {o}")
        if audit["ghosts_in_styleb"]:
            for g in audit["ghosts_in_styleb"][:5]:
                print(f"   GHOST:  {g}")
        if audit["fl_mismatches"]:
            for m in audit["fl_mismatches"]:
                print(f"   {m}")

        if args.apply:
            target = cfg.clip_lists_dir / f"part{part:02d}_styleb.txt"
            target.write_text(audit["proposed"], encoding="utf-8")
            print(f"   WROTE {target}")

    (out_dir / "clip_audit_summary.txt").write_text(
        "\n".join(summary) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
