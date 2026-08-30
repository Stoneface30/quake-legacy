"""Candidate review package for Gate P-2 sign-off (charter §26 stage 2).

Renders a single self-contained HTML page (no external assets) with the
top-100 capture windows, top-50 clutches, and the small-demo classification
summary. Local-only: lives under output/ (gitignored), player names allowed.

Usage:
    python -u engine/parser/review_package.py
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "output" / "demo_v2"
REVIEW_HTML = OUT_DIR / "review" / "candidate_review.html"

CSS = """
body{background:#111214;color:#c9cdd4;font:14px/1.5 'Segoe UI',sans-serif;margin:0;padding:24px}
h1,h2{color:#e8eaf0;font-weight:600;letter-spacing:.06em}
h1{border-bottom:2px solid #8a8f99;padding-bottom:8px}
.badge{display:inline-block;background:#2a2d33;border:1px solid #4a4f59;border-radius:4px;
  padding:2px 10px;margin:2px 6px 2px 0;color:#aeb4bf}
table{border-collapse:collapse;width:100%;margin:12px 0 32px;font-size:12.5px}
th,td{border:1px solid #2c2f36;padding:4px 8px;text-align:left;vertical-align:top}
th{background:#1c1e23;color:#dfe2e8;cursor:pointer;position:sticky;top:0}
tr:nth-child(even){background:#17181c}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.t1{color:#f0d060}.t2{color:#9fc4ff}.cl{color:#ff9f7a}.ap{color:#9fe0a0}
.small{color:#7d828c;font-size:11.5px}
"""

JS = """
function sortTable(t,i,num){const tb=t.tBodies[0];const r=[...tb.rows];
const d=t.dataset['s'+i]!=='1';t.dataset['s'+i]=d?'1':'0';
r.sort((a,b)=>{let x=a.cells[i].innerText,y=b.cells[i].innerText;
if(num){x=parseFloat(x)||0;y=parseFloat(y)||0;return d?y-x:x-y}
return d?y.localeCompare(x):x.localeCompare(y)});r.forEach(x=>tb.appendChild(x));}
"""

CLASS_SPAN = {"T1_NEW": "t1", "T2_NEW": "t2", "CLUTCH_PREMIUM": "cl",
              "ACTION_PREMIUM": "ap"}


def _table(tid: str, rows: list[dict], cols: list[tuple[str, str, bool]]) -> str:
    head = "".join(
        f"<th onclick=\"sortTable(document.getElementById('{tid}'),{i},{str(num).lower()})\">{html.escape(label)}</th>"
        for i, (label, _, num) in enumerate(cols))
    body = []
    for r in rows:
        tds = []
        for label, key, num in cols:
            v = r.get(key, "")
            v = "" if v is None else str(v)
            cls = []
            if num:
                cls.append("num")
            if key == "class" and v in CLASS_SPAN:
                cls.append(CLASS_SPAN[v])
            attr = f' class="{" ".join(cls)}"' if cls else ""
            tds.append(f"<td{attr}>{html.escape(v)}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return (f"<table id='{tid}'><thead><tr>{head}</tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table>")


def build() -> Path:
    with open(OUT_DIR / "capture_windows_top100.csv", newline="", encoding="utf-8") as f:
        top100 = list(csv.DictReader(f))
    with open(REPO_ROOT / "output" / "clutch_recorder.csv", newline="", encoding="utf-8") as f:
        clutches = sorted(csv.DictReader(f), key=lambda c: -float(c["rank_score"]))[:50]
    small = json.loads((OUT_DIR / "small_demo_classification.json").read_text(encoding="utf-8"))
    full_counts: dict = {}
    with open(OUT_DIR / "capture_windows_full.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = r["class"] or "UNCLASSED"
            full_counts[k] = full_counts.get(k, 0) + 1

    badges = "".join(f"<span class='badge'>{html.escape(k)}: {v}</span>"
                     for k, v in sorted(full_counts.items(), key=lambda kv: -kv[1]))
    small_badges = "".join(f"<span class='badge'>{html.escape(k)}: {v}</span>"
                           for k, v in small["class_counts"].items())

    win_cols = [("#", "_i", True), ("class", "class", False), ("score", "score", True),
                ("demo", "demo", False), ("map", "map", False), ("round", "round", True),
                ("clock", "clock_start", False), ("dur s", "duration_s", True),
                ("kills", "n_kills", True), ("weapons", "weapons", False),
                ("tags", "tags", False), ("clutch", "clutch_context", False)]
    for i, r in enumerate(top100, 1):
        r["_i"] = i
    cl_cols = [("score", "rank_score", True), ("demo", "demo", False),
               ("map", "map", False), ("round", "round", True),
               ("1vN", "enemies_alive_at_start", True),
               ("kills", "kills_during_clutch", True), ("weapons", "weapons", False),
               ("dur ms", "duration_ms", True), ("outcome", "outcome", False)]

    page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>pTn.Tr4sH — V2 candidate review — Gate P-2</title>
<style>{CSS}</style><script>{JS}</script></head><body>
<h1>PANTHEON · V2 DEMO MINING — CANDIDATE REVIEW</h1>
<p class="small">Generated from certified corpus (frags_rebuilt.db, parser 5a1f08dd).
Click headers to sort. This page is local-only (output/ is gitignored).</p>
<h2>Capture window classes (full set)</h2><p>{badges}</p>
<h2>Top 100 capture windows</h2>
{_table('wins', top100, win_cols)}
<h2>Top 50 recorder clutches</h2>
{_table('clutch', clutches, cl_cols)}
<h2>Small demos (&lt;800 KB): {small['unique_small_demos']} unique</h2>
<p>{small_badges}</p>
<p class="small">Valuable tiny demos (recorder frag score ≥ 10): {len(small['valuable_small_demos'])} — see small_demo_classification.json</p>
</body></html>"""

    REVIEW_HTML.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_HTML.write_text(page, encoding="utf-8")
    return REVIEW_HTML


if __name__ == "__main__":
    p = build()
    print(f"review package: {p} ({p.stat().st_size:,} bytes)")
