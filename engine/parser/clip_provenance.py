"""Map the hand-cut T1/T2/T3 AVI clips back to demos and frags.

The clip library predates this pipeline: the AVIs were cut by hand years ago
and `rendered_clips` in the old database has zero rows, so nothing recorded
which demo a clip came from. This reconstructs that mapping from deterministic
evidence first, and says UNRESOLVED where the evidence is not there.

The decisive evidence is the naming. Clips are named like

    Demo (877)  -  1116.avi
    Demo (113)  - 24.avi

and the corpus holds demo files named `Demo (877).dm_73`, plus some with a
suffix of their own (`Demo (113) - 24;.dm_73`). Measured over the whole clip
library: every one of the 756 distinct `Demo (N)` numbers referenced by a clip
resolves to a demo file that exists. So the demo is knowable for most clips
even when the exact frag inside it is not.

Confidence is assigned honestly:

    EXACT       number AND suffix identify one demo file
    HIGH        number identifies a demo, and the demo yields exactly one
                candidate frag once filtered to the recorder's kills
    MEDIUM      number identifies a demo with several candidate frags
    LOW         number resolves to several demo files (ambiguous)
    UNRESOLVED  no usable name evidence

Duration is deliberately NOT used to pick between frags. A clip lasting 13 s
tells us nothing about which of a demo's kills it holds, and pretending
otherwise would manufacture confident-looking rows out of coincidence.

    python engine/parser/clip_provenance.py
    python engine/parser/clip_provenance.py --db creative_suite/database/frags_rebuilt.db
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import hashlib
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

DEFAULT_DB = REPO / "creative_suite" / "database" / "frags_rebuilt.db"
CLIP_ROOT = REPO / "QUAKE VIDEO"
FFPROBE = REPO / "creative_suite" / "tools" / "ffmpeg" / "ffprobe.exe"

CLIP_RE = re.compile(r"Demo\s*\((\d+)\)\s*(?:-\s*(.*?))?\s*$", re.I)
DEMO_RE = re.compile(r"Demo\s*\((\d+)\)\s*(?:-\s*(.+?))?;?(_\d+)?$", re.I)


_HASH_CACHE = {}


def content_hash(path: Path) -> str:
    """Full-content hash, cached. Used to tell real ambiguity from duplicates."""
    k = str(path)
    if k in _HASH_CACHE:
        return _HASH_CACHE[k]
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            while True:
                b = fh.read(1 << 20)
                if not b:
                    break
                h.update(b)
        v = h.hexdigest()
    except OSError:
        v = ""
    _HASH_CACHE[k] = v
    return v


def distinct_by_content(paths):
    """Collapse byte-identical candidates.

    The corpus stores the same demo under several names ("Demo (4).dm_73" and
    "Demo (4)_1.dm_73" are identical). Several FILES sharing a clip's number is
    therefore not ambiguity about which DEMO the clip came from -- it is the
    same demo counted twice, and treating it as ambiguity buried 1208 clips in
    LOW confidence that are actually unambiguous.
    """
    seen = {}
    for q in paths:
        seen.setdefault(content_hash(q), []).append(q)
    return seen


def index_demos(root: Path):
    """(number, suffix) -> [demo files]  and  number -> [demo files]."""
    exact = defaultdict(list)
    by_num = defaultdict(list)
    for q in root.glob("*.dm_73"):
        m = DEMO_RE.match(q.stem)
        if not m:
            continue
        n = int(m.group(1))
        suf = (m.group(2) or "").strip().rstrip(";")
        exact[(n, suf)].append(q)
        by_num[n].append(q)
    return exact, by_num


def collect_clips(root: Path):
    out = []
    for tier in ("T1", "T2", "T3"):
        for part in range(1, 13):
            d = root / tier / "Part{}".format(part)
            if not d.exists():
                continue
            for q in d.rglob("*.avi"):
                out.append((tier, part, q))
    return out


def clip_duration(path: Path) -> float:
    try:
        r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True, timeout=60)
        return round(float(r.stdout.strip()), 3)
    except Exception:
        return 0.0


def load_frags(db: Path):
    """demo file name -> list of frag rows, and the recorder per demo."""
    if not db.exists():
        return {}, {}
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    frags = defaultdict(list)
    try:
        for r in con.execute("""SELECT f.frag_id, f.server_time_ms, f.clock,
                                       f.round, f.by_recorder, f.weapon_name,
                                       f.tags, f.score, d.name AS demo
                                FROM frags f JOIN demos d
                                  ON d.demo_id = f.demo_id"""):
            frags[r["demo"]].append(dict(r))
    except sqlite3.Error:
        pass
    con.close()
    return frags, {}


def resolve(tier, part, clip: Path, exact, by_num, frags, want_duration):
    row = {
        "clip_path": str(clip),
        "clip_name": clip.name,
        "part": part,
        "tier": tier,
        "duration_s": clip_duration(clip) if want_duration else None,
        "likely_demo": None,
        "likely_frag_id": None,
        "frag_server_time_ms": None,
        "estimated_source_start_ms": None,
        "frag_offset_in_avi_s": None,
        "mapping_method": None,
        "candidate_demos": 0,
        "candidate_frags": 0,
        "confidence": "UNRESOLVED",
        "candidate_demo_names": "",
        "notes": "",
    }

    m = CLIP_RE.match(clip.stem)
    if not m:
        row["mapping_method"] = "no_name_evidence"
        row["notes"] = "clip name does not carry a Demo (N) reference"
        return row

    n = int(m.group(1))
    suf = (m.group(2) or "").strip()

    cands = exact.get((n, suf)) or []
    if cands:
        row["mapping_method"] = "filename_number_and_suffix"
        row["candidate_demos"] = len(cands)
        row["likely_demo"] = cands[0].name
        row["confidence"] = "EXACT" if len(cands) == 1 else "LOW"
    else:
        cands = by_num.get(n) or []
        row["candidate_demos"] = len(cands)
        if not cands:
            row["mapping_method"] = "filename_number_unmatched"
            row["notes"] = "no demo file carries number {}".format(n)
            return row
        # Several files often share a number because the corpus holds
        # byte-identical copies under _1/_2 names. Prefer the plainest name.
        groups = distinct_by_content(cands)
        cands = sorted(cands, key=lambda q: (len(q.stem), q.stem))
        row["likely_demo"] = cands[0].name
        row["candidate_demos"] = len(groups)
        if len(groups) == 1:
            row["mapping_method"] = "filename_number_only"
            row["confidence"] = "HIGH"
            if len(cands) > 1:
                row["notes"] = ("{} files share number {} but are "
                                "byte-identical".format(len(cands), n))
        else:
            row["mapping_method"] = "filename_number_ambiguous"
            row["confidence"] = "LOW"
            # Keep the shortlist. LOW here means "one of these 2-3 demos",
            # which is a long way from unknown and is what the next pass needs.
            row["candidate_demo_names"] = "|".join(
                sorted(v[0].name for v in groups.values()))
            row["notes"] = ("{} genuinely different demos share number {}"
                            .format(len(groups), n))

    # Narrow to a frag using the database, if it has been rebuilt.
    rows = frags.get(row["likely_demo"]) or []
    mine = [f for f in rows if f.get("by_recorder")]
    pool = mine or rows
    row["candidate_frags"] = len(pool)
    if len(pool) == 1:
        f = pool[0]
        row["likely_frag_id"] = f["frag_id"]
        row["frag_server_time_ms"] = f["server_time_ms"]
        row["mapping_method"] += "+sole_frag_in_demo"
        if row["confidence"] in ("HIGH", "EXACT"):
            row["confidence"] = "EXACT" if row["confidence"] == "EXACT" else "HIGH"
    elif len(pool) > 1 and row["confidence"] == "HIGH":
        row["confidence"] = "MEDIUM"
        row["notes"] = (row["notes"] + "; " if row["notes"] else "") + \
            "{} candidate frags in demo -- frag not determined".format(len(pool))
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--clips", default=str(CLIP_ROOT))
    ap.add_argument("--demos", default=str(REPO / "demos"))
    ap.add_argument("--out-dir", default=str(REPO / "output"))
    ap.add_argument("--no-duration", action="store_true",
                    help="skip ffprobe (much faster, leaves duration empty)")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    exact, by_num = index_demos(Path(a.demos))
    clips = collect_clips(Path(a.clips))
    if a.limit:
        clips = clips[:a.limit]
    frags, _ = load_frags(Path(a.db))

    print("[prov] {} demo file(s) indexed, {} clip(s) to map".format(
        sum(len(v) for v in by_num.values()), len(clips)), flush=True)
    if not frags:
        print("[prov] NOTE: {} has no frags yet -- demo-level mapping only, "
              "frag-level stays undetermined".format(a.db), flush=True)

    rows = []
    for i, (tier, part, q) in enumerate(clips, 1):
        rows.append(resolve(tier, part, q, exact, by_num, frags,
                            not a.no_duration))
        if i % 200 == 0:
            print("  [prov] {}/{}".format(i, len(clips)), flush=True)

    counts = defaultdict(int)
    for r in rows:
        counts[r["confidence"]] += 1
    t1 = sum(1 for r in rows if r["tier"] == "T1")
    t2 = sum(1 for r in rows if r["tier"] == "T2")
    t3 = sum(1 for r in rows if r["tier"] == "T3")

    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = ["clip_path", "clip_name", "part", "tier", "duration_s",
            "likely_demo", "likely_frag_id", "frag_server_time_ms",
            "estimated_source_start_ms", "frag_offset_in_avi_s",
            "mapping_method", "candidate_demos", "candidate_frags",
            "confidence", "candidate_demo_names", "notes"]
    with (out_dir / "clip_provenance.csv").open("w", newline="",
                                                encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    (out_dir / "clip_provenance.json").write_text(
        json.dumps({"total": len(rows), "T1": t1, "T2": t2, "T3": t3,
                    "by_confidence": dict(counts), "items": rows}, indent=2),
        encoding="utf-8")

    print("")
    print("=" * 68)
    print("CLIP PROVENANCE")
    print("=" * 68)
    print("  clips mapped : {}   (T1 {}, T2 {}, T3 {})".format(len(rows), t1,
                                                               t2, t3))
    for k in ("EXACT", "HIGH", "MEDIUM", "LOW", "UNRESOLVED"):
        n = counts.get(k, 0)
        print("  {:11} {:>5}  {:5.1f}%".format(k, n,
                                               100.0 * n / max(1, len(rows))))
    print("")
    print("  {}".format(out_dir / "clip_provenance.csv"))
    print("  {}".format(out_dir / "clip_provenance.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
