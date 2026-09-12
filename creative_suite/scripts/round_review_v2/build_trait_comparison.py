"""Old vs new trait comparison page, for the recorder to validate.

Reads the old state (traits_ranked.csv: calibration policy, weight, corpus
round counts), every calibration note, and trait_rules_v3.py, and writes
samples/trait_comparison.html (under samples/ so the existing tunnel route
serves it). Per-trait Approve / Change answers POST to /save as
tc_ok_<TRAIT> and tc_note_<TRAIT>.
"""
from __future__ import annotations

import collections
import csv
import html
import json
from pathlib import Path

HERE = Path("G:/QUAKE_LEGACY/output/demo_v2/round_review_v2")
DEMO = HERE.parent
import sys
sys.path.insert(0, str(HERE))
from trait_rules_v3 import GLOBAL, R                     # noqa: E402

old = {r["trait"]: r for r in csv.DictReader(
    open(HERE / "traits_ranked.csv", encoding="utf-8"))}

notes = collections.defaultdict(list)
rows = {}
for f in ("calibration_answers.json", "answers_archive_prev_selection.json"):
    p = DEMO / f
    if p.exists():
        for k, v in json.loads(p.read_text(encoding="utf-8")).items():
            rows.setdefault(k, v)
per = collections.defaultdict(dict)
for k, v in rows.items():
    if k[:2] in ("w_", "v_") and "__" in k:
        t, clip = k[2:].rsplit("__", 1)
        per[t].setdefault(clip, {})["w" if k[0] == "w" else "n"] = str(v).strip()
for t, clips in per.items():
    for d in clips.values():
        if d.get("w") or d.get("n"):
            notes[t].append((d.get("w", ""), d.get("n", "")))

small = json.loads((HERE / "small_demos.json").read_text(encoding="utf-8"))

missing = sorted(set(notes) - set(R))
assert not missing, "traits with notes but no v3 rule: %s" % missing

WCOL = {"GOLDEN": "#e8c07d", "HIGH": "#a3be8c", "MED": "#88c0d0",
        "LOW": "#8a94a0", "DROP": "#e06c75", "DISCOUNT": "#b48ead"}
PCOL = {"HERO": "#e8c07d", "SUPPORT": "#88c0d0", "BASE": "#8a94a0",
        "RETIRE": "#e06c75"}


def pcol(p):
    for k, c in PCOL.items():
        if p.startswith(k):
            return c
    return "#b48ead"                                      # lanes


def change(t, newp):
    o = (old.get(t, {}).get("policy") or "none").upper()
    n = newp.split()[0].split(":")[0]
    o = {"RETIRED": "RETIRE"}.get(o, o)
    if t not in old:
        return "NEW"
    if n == o:
        return "SAME POLICY, RULE FIXED" if "Unchanged" not in R[t][2] else "UNCHANGED"
    return "%s &rarr; %s" % (o, n)


e = html.escape
L = []
w = L.append
w("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
  "<title>Trait rules v3</title>")
w("""<style>
body{background:#14161a;color:#dfe3e8;font:14px/1.5 system-ui,sans-serif;margin:0;padding:16px;max-width:1500px}
h1{font-size:20px;margin:0}h2{font-size:16px;color:#e8c07d;margin:22px 0 8px}
.sub{color:#8a94a0;margin:4px 0 12px}.box{background:#1e222a;border:1px solid #2a2f37;border-radius:6px;padding:10px 12px;margin:8px 0}
.g{display:grid;grid-template-columns:230px 1fr 1fr;gap:6px 14px;font-size:13px}
.g b{color:#e8c07d}.q{color:#9aa7b4;font-style:italic}
.bar{position:sticky;top:0;background:#14161a;padding:8px 0;border-bottom:1px solid #2a2f37;z-index:9;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
button{background:#2d5b8a;color:#fff;border:0;border-radius:4px;padding:5px 10px;cursor:pointer;font-size:12px}
button.ch{background:#6b4a2d}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:1100px}
td,th{border-bottom:1px solid #2a2f37;padding:7px 6px;vertical-align:top;font-size:12.5px;text-align:left}
th{color:#8a94a0;font-weight:600;position:sticky;top:44px;background:#14161a}
tr.done{background:#1b241d}.t{font-weight:700;font-size:13px}.grp{color:#6f7a86;font-size:11px}
.pol{font-weight:700;font-size:11px;letter-spacing:.3px}.chg{font-size:11px;color:#b48ead}
.n{margin:2px 0}.wv{display:inline-block;min-width:58px;font-weight:700;font-size:11px}
textarea{width:100%;min-height:34px;background:#14161a;color:#dfe3e8;border:1px solid #333a44;border-radius:4px;font:12px system-ui}
.st{font-size:11px;color:#8a94a0}.st.ok{color:#a3be8c}.st.bad{color:#e06c75}
select{background:#14161a;color:#dfe3e8;border:1px solid #333a44;border-radius:4px;padding:4px}
</style>""")
w("<div class='bar'><b>Trait rules v3</b><span class='st' id='cnt'></span>"
  "<select id='flt' onchange='flt()'><option value=''>all traits</option>"
  "<option>HERO</option><option>SUPPORT</option><option>LANE</option>"
  "<option>RETIRE</option><option>BASE</option><option value='todo'>not yet validated</option></select></div>")
w("<h1>Old vs new, every trait, from your %d ratings and %d written notes</h1>"
  % (sum(1 for v in notes.values() for x in v if x[0]),
     sum(1 for v in notes.values() for x in v if x[1])))
w("<div class='sub'>Nothing changes in the detectors until you validate. Approve a trait, or "
  "press Change and write what you want instead. When every trait is validated, the "
  "full rescan of all demos runs with these rules.</div>")

w("<h2>1. Rules applied to every trait</h2><div class='box g'>"
  "<div class='grp'>RULE</div><div class='grp'>WHAT IT DOES</div><div class='grp'>FROM YOUR NOTES</div>")
for name, what, why in GLOBAL:
    w("<b>%s</b><div>%s</div><div class='q'>%s</div>" % (e(name), e(what), e(why)))
w("</div>")

w("<h2>2. The small demos</h2><div class='box'>"
  "<b>%d</b> demos under 512 KB. <b>%d</b> are cuts of a full match: they share their kills "
  "with one of <b>%d</b> full demos, and <b>%d</b> of them contain <b>your own frag</b>. "
  "They are moments you saved yourself. They are not scanned again as separate "
  "rounds. The full match holds the whole round; the saved moment inside it gets "
  "<b>SAVED_BY_RECORDER</b>. Your ratings validate the traits; these 1,301 saves "
  "give a second, independent check on whether the detectors find what you "
  "thought was worth keeping. <b>%d</b> moments exist <b>only</b> in a small demo (their full "
  "match is missing): these are scanned as single-action units. <b>%d</b> contain no kill "
  "and <b>%d</b> cuts hold only someone else's frag. Both stay out.</div>"
  % (small["small_total"], small["cut_from_full_demo"], small["parent_full_demos"],
     small["saved_moment_has_my_frag"], small["unique_moment"], small["no_kills"],
     small["saved_moment_no_my_frag"]))

w("<h2>3. Known problems your notes raised that are not traits</h2><div class='box'>"
  "<b>Sound broken / horrible</b> in 9 notes. That is the review capture, not the "
  "detection. Not fixed yet: it gets investigated before the fragmovie renders.<br>"
  "<b>'seen' / 'same clip again'</b>: one moment was shown once per trait. The round "
  "units already fix this. Each round appears once, with all its traits.</div>")

w("<h2>4. Every trait</h2><div class='tw'><table><tr><th>Trait</th><th>Your ratings &amp; notes</th>"
  "<th>OLD</th><th>NEW</th><th>Validate</th></tr>")
order = {"HERO": 0, "SUPPORT": 1, "LANE": 2, "BASE": 3, "RETIRE": 4}
traits = sorted(R, key=lambda t: (order.get(R[t][1].split()[0].split(":")[0], 2), R[t][0], t))
for t in traits:
    grp, newp, rule, why = R[t]
    o = old.get(t)
    kind = newp.split()[0].split(":")[0]
    w("<tr data-id='%s' data-k='%s'>" % (t, kind))
    w("<td><div class='t'>%s</div><div class='grp'>%s</div></td>" % (e(t), grp))
    w("<td>")
    for wv, n in notes.get(t, []):
        w("<div class='n'><span class='wv' style='color:%s'>%s</span>%s</div>"
          % (WCOL.get(wv, "#6f7a86"), e(wv or "-"), e(n)))
    if not notes.get(t):
        w("<div class='n q'>no note</div>")
    w("</td>")
    if o:
        w("<td><span class='pol' style='color:%s'>%s</span> &middot; weight %s<br>"
          "<span class='grp'>%s rated &middot; mean %s/5 &middot; in %s rounds</span></td>"
          % (pcol(o["policy"].upper()), e(o["policy"].upper()), e(o["weight"]),
             e(o["rated_n"]), e(o["raw_mean"]), e(o["rounds_with_trait"] or "0")))
    else:
        w("<td class='q'>did not exist</td>")
    w("<td><span class='pol' style='color:%s'>%s</span> <span class='chg'>%s</span>"
      "<div>%s</div><div class='q'>%s</div></td>"
      % (pcol(newp), e(newp), change(t, newp), e(rule), e(why)))
    w("<td style='min-width:170px'><button onclick=\"ok('%s')\">Approve</button> "
      "<button class='ch' onclick=\"chg('%s')\">Change</button>"
      "<textarea id='tn_%s' placeholder='what should it be instead?'></textarea>"
      "<span class='st' id='s_%s'></span></td></tr>" % (t, t, t, t))
w("</table></div>")

w("""<script>
let S={};const N=%d;
function cnt(){const d=document.querySelectorAll('tr.done').length;
 document.getElementById('cnt').textContent=d+' / '+N+' validated';}
function flt(){const f=document.getElementById('flt').value;
 document.querySelectorAll('tr[data-id]').forEach(r=>{
  r.hidden=f==='todo'?r.classList.contains('done'):(f&&r.dataset.k!==f&&!(f==='LANE'&&r.dataset.k.startsWith('LANE')));});}
fetch('/answers',{credentials:'same-origin'}).then(r=>r.json()).then(j=>{S=j||{};
 document.querySelectorAll('tr[data-id]').forEach(r=>{const t=r.dataset.id;
  if(S['tc_note_'+t])document.getElementById('tn_'+t).value=S['tc_note_'+t];
  if(S['tc_ok_'+t]){r.classList.add('done');
   document.getElementById('s_'+t).textContent=S['tc_ok_'+t]==='APPROVE'?'\\u2713 approved':'\\u270e change asked';}});
 cnt();}).catch(()=>{document.getElementById('cnt').textContent='offline - answers not loaded';});
async function save(t,v){const s=document.getElementById('s_'+t);
 const n=document.getElementById('tn_'+t).value;
 if(v==='CHANGE'&&!n.trim()){s.className='st bad';s.textContent='write what you want first';return;}
 const b={};b['tc_ok_'+t]=v;b['tc_note_'+t]=n;
 try{const r=await fetch('/save',{method:'POST',credentials:'same-origin',
   headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});
  if(!r.ok||(r.headers.get('content-type')||'').indexOf('application/json')<0)throw new Error('sign-in expired?');
  const a=await(await fetch('/answers',{credentials:'same-origin'})).json();
  if(a['tc_ok_'+t]!==v)throw new Error('not on server');
  s.className='st ok';s.textContent=v==='APPROVE'?'\\u2713 approved':'\\u270e change saved';
  document.querySelector('tr[data-id=\"'+t+'\"]').classList.add('done');cnt();
 }catch(e){s.className='st bad';s.textContent='NOT saved: '+e.message;}}
function ok(t){save(t,'APPROVE');}function chg(t){save(t,'CHANGE');}
</script>""" % len(traits))

out = HERE / "samples" / "trait_comparison.html"
out.write_text("\n".join(L), encoding="utf-8")
kinds = collections.Counter(R[t][1].split()[0].split(":")[0] for t in R)
print("wrote %s: %d traits %s; notes cover %d traits" % (out, len(R), dict(kinds), len(notes)))
