"""Parser v1 corpus vs parser v2 build: what changed, quantified.

Plan: docs/superpowers/plans/2026-09-12-corpus-parser-v2-rebuild.md, task 5.
Both corpora are opened read-only. The v1 side is restricted to the demos
(content_hash) the v2 build holds, so a limited build compares like with like.
AGGREGATES ONLY: no name column is ever selected (public repo).

    python -m engine.parser.corpus_migration_report --old <db dir> --new <db dir>
        --out docs/reference/<date>-corpus-v2-migration [--manifest <build>/rebuild_v2_manifest.json]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path


def _ro(db: Path) -> sqlite3.Connection | None:
    if not db.is_file():
        return None
    c = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=120)
    c.execute("attach database ':memory:' as s")
    c.execute("create table s.scope (h text primary key)")
    return c


def _tables(c) -> set[str]:
    return {r[0] for r in c.execute("select name from sqlite_master where type='table'")}


def _cols(c, t) -> set[str]:
    return {r[1] for r in c.execute(f'pragma table_info("{t}")')}


def _scope(c, hashes) -> None:
    c.execute("delete from s.scope")
    c.executemany("insert or ignore into s.scope values (?)", [(h,) for h in hashes])


def _count(c, t, by=None):
    """Rows (optionally grouped), scoped to the build's demos where the table
    carries content_hash. Returns (value, scoped?)."""
    if c is None or t not in _tables(c):
        return None, False
    scoped = "content_hash" in _cols(c, t)
    where = " where content_hash in (select h from s.scope)" if scoped else ""
    if by and by in _cols(c, t):
        return dict(Counter({str(k): n for k, n in c.execute(
            f'select "{by}", count(*) from "{t}"{where} group by "{by}"')})), scoped
    return c.execute(f'select count(*) from "{t}"{where}').fetchone()[0], scoped


def _frags(c) -> dict[tuple, tuple]:
    """(content_hash, server_time_ms, victim) -> (attacker, mod, by_recorder, tags, score)."""
    if c is None or "frags" not in _tables(c):
        return {}
    rows = c.execute("""
        select d.content_hash, f.server_time_ms, f.victim_client, f.attacker_client,
               f.mod, f.by_recorder, f.tags, f.score
        from frags f join demos d on d.demo_id = f.demo_id
        where d.content_hash in (select h from s.scope)""")
    return {(h, t, v): (a, m, br, tags or "", sc) for h, t, v, a, m, br, tags, sc in rows}


def _dist(values: list[int]) -> dict:
    if not values:
        return {"n": 0}
    v = sorted(values)
    q = lambda p: v[min(len(v) - 1, int(p * (len(v) - 1) + 0.5))]
    return {"n": len(v), "min": v[0], "p5": q(0.05), "median": q(0.5),
            "p95": q(0.95), "max": v[-1], "nonzero": sum(1 for x in v if x)}


def _delta(old, new) -> dict:
    """Per-key old/new/delta for two count dicts (or two scalars)."""
    if isinstance(old, dict) or isinstance(new, dict):
        old, new = old or {}, new or {}
        return {k: {"old": old.get(k, 0), "new": new.get(k, 0),
                    "delta": new.get(k, 0) - old.get(k, 0)}
                for k in sorted(set(old) | set(new))}
    return {"old": old, "new": new,
            "delta": (new - old) if old is not None and new is not None else None}


# Attribute keys whose value comes from the ENTITY stream (the part parser v1
# got wrong); everything else in recognized_frags.attributes is the recorder's
# playerstate or derived from the kill events themselves.
_ENTITY_ATTR_HINTS = ("victim", "visib", "distance", "missile", "projectile", "enemy",
                      "target", "presence", "los", "geo")


def _attr_side(key: str) -> str:
    k = key.lower()
    return "entity" if any(h in k for h in _ENTITY_ATTR_HINTS) else "playerstate_or_event"


def _recognized_diff(oc, nc) -> dict:
    """Changed attributes (by key, split entity vs playerstate side) and changed
    classification, on recognized frags matched by identity."""
    def load(c):
        if c is None or "recognized_frags" not in _tables(c):
            return {}
        if not {"classes", "attributes"} <= _cols(c, "recognized_frags"):
            return {}                    # an older/partial table: nothing to compare
        return {(h, t, v): (cl or "[]", at or "{}") for h, t, v, cl, at in c.execute(
            "select content_hash, server_time_ms, victim_client, classes, attributes "
            "from recognized_frags where content_hash in (select h from s.scope)")}
    o, n = load(oc), load(nc)
    names = lambda cl: {x["name"] if isinstance(x, dict) else x for x in json.loads(cl)}
    attr_changed, sides, cls_changed = Counter(), Counter(), 0
    gained, lost = Counter(), Counter()
    for k in set(o) & set(n):
        (co, ao), (cn, an) = o[k], n[k]
        a, b = json.loads(ao), json.loads(an)
        keys = {x for x in set(a) | set(b) if not x.startswith("_") and a.get(x) != b.get(x)}
        for x in keys:
            attr_changed[x] += 1
        for side in {_attr_side(x) for x in keys}:
            sides[side] += 1
        so, sn = names(co), names(cn)
        if so != sn:
            cls_changed += 1
            gained.update(sn - so)
            lost.update(so - sn)
    return {"recognized_matched": len(set(o) & set(n)),
            "changed_attributes": {"frags_by_side": dict(sides),
                                   "by_key_top25": dict(attr_changed.most_common(25))},
            "changed_classification": {"frags": cls_changed,
                                       "labels_gained_top15": dict(gained.most_common(15)),
                                       "labels_lost_top15": dict(lost.most_common(15))}}


def _clutch_diff(old_db_dir: Path, new_db_dir: Path, scope: set[str]) -> dict:
    """Clutch membership, v1 output/ vs v2 output/, keyed without names."""
    import csv
    def load(db_dir, name):
        p = db_dir.parent.parent / "output" / name
        if not p.is_file():
            return None
        with p.open(newline="", encoding="utf-8") as f:
            return {(r["canonical_demo_hash"], int(r["round"]), int(r["player_client"]))
                    for r in csv.DictReader(f) if r["canonical_demo_hash"] in scope}
    out = {}
    for name in ("clutch_all_players.csv", "clutch_recorder.csv"):
        a, b = load(old_db_dir, name), load(new_db_dir, name)
        out[name] = (None if a is None or b is None else
                     {"old": len(a), "new": len(b), "kept": len(a & b),
                      "added": len(b - a), "removed": len(a - b)})
    return out


GROUPED = [  # (db, table, group-by column or None)
    ("frags_rebuilt.db", "demos", None),
    ("frag_recognition.db", "scanned_demos", None),
    ("frag_recognition.db", "recognized_frags", None),
    ("frag_recognition.db", "kill_events_v1", "death_cause"),
    ("frag_recognition.db", "kill_events_v1", "mod_name"),
    ("frag_recognition.db", "semantic_events_v1", "type"),
    ("frag_recognition.db", "missile_samples_v1", None),
    ("frag_recognition.db", "teleport_transits_v1", "outcome"),
    ("frag_recognition.db", "server_text_v1", "kind"),
    ("frag_recognition.db", "round_state_v1", None),
    ("frag_recognition.db", "team_changes_v1", None),
    ("frag_recognition.db", "kill_occurrences_v1", None),
    ("frag_recognition.db", "action_moments_v1", "activity_label"),
    ("mining_epoch.db", "action_moments_v1", "activity_label"),
    ("mining_epoch.db", "aim_events_v1", None),
    ("frag_shapes.db", "frag_shapes_v1", None),
]


def report(old_dir: Path, new_dir: Path, manifest: Path | None = None) -> dict:
    new_f = _ro(new_dir / "frags_rebuilt.db")
    if new_f is None:
        raise SystemExit(f"no v2 frags_rebuilt.db in {new_dir}")
    scope = [r[0] for r in new_f.execute(
        "select content_hash from demos where parse_error is null")]
    out: dict = {"scope_demos": len(scope), "tables": {}}

    conns = {}
    for side, d in (("old", old_dir), ("new", new_dir)):
        for name in {db for db, _t, _b in GROUPED}:
            c = _ro(d / name)
            if c is not None:
                _scope(c, scope)
            conns[side, name] = c

    for db, t, by in GROUPED:
        o, so = _count(conns["old", db], t, by)
        n, sn = _count(conns["new", db], t, by)
        key = f"{db}:{t}" + (f" by {by}" if by else "")
        if by and (o is not None or n is not None):
            out["tables"][key] = {"scoped": so or sn, "by": _delta(o or {}, n or {})}
        else:                                   # ungrouped, or absent on both sides
            out["tables"][key] = {"scoped": so or sn, **_delta(o, n)}

    # ---- frags, matched by identity ------------------------------------------
    of, nf = _frags(conns["old", "frags_rebuilt.db"]), _frags(conns["new", "frags_rebuilt.db"])
    common = set(of) & set(nf)
    changed = Counter()
    flips = Counter()
    score_d = []
    for k in common:
        a, b = of[k], nf[k]
        if a[0] != b[0]: changed["attacker"] += 1
        if a[1] != b[1]: changed["mod"] += 1
        if a[3] != b[3]: changed["tags"] += 1
        if a[2] != b[2]: flips["to_recorder" if b[2] else "from_recorder"] += 1
        if a[4] is not None and b[4] is not None:
            score_d.append(round(b[4] - a[4], 4))
    per_old = Counter(k[0] for k in of)
    per_new = Counter(k[0] for k in nf)
    tag_old = Counter(t for v in of.values() for t in v[3].split(",") if t)
    tag_new = Counter(t for v in nf.values() for t in v[3].split(",") if t)
    out["frags"] = {
        "old": len(of), "new": len(nf), "kept": len(common),
        "added": len(set(nf) - set(of)), "removed": len(set(of) - set(nf)),
        "changed_in_kept": dict(changed), "by_recorder_flips": dict(flips),
        "score_delta": ({"mean": round(statistics.fmean(score_d), 4),
                         "changed": sum(1 for x in score_d if x)} if score_d else {}),
        "per_demo_count_delta": _dist([per_new.get(h, 0) - per_old.get(h, 0)
                                       for h in scope]),
        "tags": _delta(dict(tag_old), dict(tag_new)),
    }
    # ---- WHY it changed: the buckets parser v1's defects should explain ------------
    added, removed = set(nf) - set(of), set(of) - set(nf)
    by_act = defaultdict(list)                  # (hash, victim, attacker, mod) -> times
    for k in added:
        by_act[(k[0], k[2], nf[k][0], nf[k][1])].append(k[1])
    shifted = []
    for k in removed:
        ts = by_act.get((k[0], k[2], of[k][0], of[k][1]), [])
        near = [t for t in ts if abs(t - k[1]) <= 1000]
        if near:
            shifted.append(min(near, key=lambda t: abs(t - k[1])) - k[1])
    out["buckets"] = {
        "recovered_kills": len(added) - len(shifted),
        "lost_or_invalid_old_kills": len(removed) - len(shifted),
        "shifted_timestamps": {"n": len(shifted), "ms": _dist(shifted)},
    }
    out["buckets"].update(_recognized_diff(conns["old", "frag_recognition.db"],
                                           conns["new", "frag_recognition.db"]))
    out["buckets"]["clutch_membership"] = _clutch_diff(old_dir, new_dir, set(scope))

    # ---- highlights: does the top of the ranking survive? ------------------------
    def _top(c, n):
        if c is None or "recognized_frags" not in _tables(c):
            return []
        return [tuple(r) for r in c.execute(
            "select content_hash, server_time_ms, victim_client from recognized_frags "
            "where content_hash in (select h from s.scope) "
            "order by highlight_score desc, content_hash, server_time_ms limit ?", (n,))]
    out["highlights"] = {}
    for n in (50, 100, 500):
        a = set(_top(conns["old", "frag_recognition.db"], n))
        b = set(_top(conns["new", "frag_recognition.db"], n))
        out["highlights"][f"top{n}"] = {
            "old": len(a), "new": len(b), "overlap": len(a & b),
            "jaccard": round(len(a & b) / len(a | b), 3) if a | b else None}

    if manifest and manifest.is_file():
        m = json.loads(manifest.read_text(encoding="utf-8"))
        out["human_linkage"] = m.get("human_linkage")
        out["build"] = {"git_commit": m.get("prepare", {}).get("git_commit"),
                        "stage_wall_s": {k: v.get("wall_s") for k, v in m.items()
                                         if isinstance(v, dict) and "wall_s" in v}}
    for c in conns.values():
        if c is not None:
            c.close()
    new_f.close()
    return out


def markdown(r: dict) -> str:
    L = ["# Corpus migration: parser v1 → parser v2", "",
         f"Scope: **{r['scope_demos']} demos** held by the v2 build; v1 rows are "
         "restricted to the same demos where the table carries `content_hash`. "
         "Aggregates only.", "", "## Frags (matched by content hash, server time, victim)", "",
         "| | count |", "|---|---:|"]
    f = r["frags"]
    for k in ("old", "new", "kept", "added", "removed"):
        L.append(f"| {k} | {f[k]} |")
    L += ["", f"Changed among kept: `{f['changed_in_kept']}` · by_recorder flips: "
          f"`{f['by_recorder_flips']}` · score: `{f['score_delta']}`", "",
          f"Per-demo frag-count delta (v2 − v1): `{f['per_demo_count_delta']}`", "",
          "## Why it changed", "",
          "Parser v1 was wrong (`STALE_PRE_PARSER_V2`), so differences are expected; "
          "each bucket names what moved.", "",
          f"```\n{json.dumps(r.get('buckets', {}), indent=1)}\n```", "",
          "## Highlights (top-N by highlight_score, matched by identity)", "",
          "| | v1 | v2 | overlap | jaccard |", "|---|---:|---:|---:|---:|"]
    for k, h in r.get("highlights", {}).items():
        L.append(f"| {k} | {h['old']} | {h['new']} | {h['overlap']} | {h['jaccard']} |")
    L += ["", "## Tables", "", "| table | v1 | v2 | Δ |", "|---|---:|---:|---:|"]
    for name, t in r["tables"].items():
        # A table without content_hash cannot be restricted to the build's
        # demos: its v1 count is the whole corpus. Say so on the row.
        tag = "" if t.get("scoped") else " *(unscoped: whole-DB counts)*"
        if "by" in t:
            for k, v in t["by"].items():
                L.append(f"| {name} = {k}{tag} | {v['old']} | {v['new']} | {v['delta']:+d} |")
        else:
            d = t["delta"]
            L.append(f"| {name}{tag} | {t['old']} | {t['new']} | "
                     f"{'' if d is None else f'{d:+d}'} |")
    if r.get("human_linkage") is not None:
        L += ["", "## Human linkage (v1 live → v2 build)", "",
              f"```\n{json.dumps(r['human_linkage'], indent=1)}\n```"]
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--old", type=Path, required=True)
    ap.add_argument("--new", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="path stem (.md and .json)")
    ap.add_argument("--manifest", type=Path)
    a = ap.parse_args()
    r = report(a.old, a.new, a.manifest)
    a.out.with_suffix(".json").write_text(json.dumps(r, indent=1), encoding="utf-8")
    a.out.with_suffix(".md").write_text(markdown(r), encoding="utf-8")
    # A Windows console is cp1252; the files above are already written as
    # UTF-8, and a summary that cannot print must not look like a failure.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(markdown(r)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
