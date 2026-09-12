"""Round review page for the v3 mining: gametype -> weapon lane -> score.

Same card and answer keys as build_page.py (rw_/rv_ + round identity), so
answers already given carry over. Written under samples/ so the existing
tunnel route serves it; sample videos sit next to it.
"""
from __future__ import annotations

import collections
import hashlib
import html
import json
from pathlib import Path

HERE = Path("G:/QUAKE_LEGACY/output/demo_v2/round_review_v2")
V3 = HERE / "v3"
PER_LANE = 20
rounds = json.loads((V3 / "rounds_ranked.json").read_text(encoding="utf-8"))
summary = json.loads((V3 / "summary.json").read_text(encoding="utf-8"))
samples = {}
sp = HERE / "samples" / "samples.json"
if sp.exists():
    for s in json.loads(sp.read_text(encoding="utf-8")):
        if s.get("mp4") and s.get("duration_ok") and s.get("content_hash"):
            samples[(s["content_hash"], s["start_ms"])] = s


def rid(u):
    return hashlib.sha1(("%s|%s|%s" % (u["content_hash"], u["round"], u["start_ms"]))
                        .encode()).hexdigest()[:12]


def ms(t):
    return "%d:%06.3f" % (t // 60000, (t % 60000) / 1000.0)


e = html.escape
GT_ORDER = ["CA", "CTF_INSTAGIB", "DUEL", "CTF", "TEAM", "FFA"]
by = collections.defaultdict(lambda: collections.defaultdict(list))
for u in rounds:
    if u["kills"]:
        by[u["gametype"]][u["lane"]].append(u)
gts = sorted(by, key=lambda g: (GT_ORDER.index(g) if g in GT_ORDER else 99, g))
ROLE = {"HERO_ROUND": "#e8c07d", "STRONG_ROUND": "#a3be8c", "FILLER_ROUND": "#88c0d0",
        "TRANSITION_OR_BLOOPER": "#b48ead"}
TAG = {"TELEFRAG": "#d08770", "BLOOPER": "#b48ead", "TRANSITION": "#5e81ac",
       "EFFECT": "#ebcb8b"}

L = []
w = L.append
w("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
  "<title>Round review v3</title>")
w("""<style>
body{background:#14161a;color:#dfe3e8;font:14px/1.5 system-ui,sans-serif;margin:0;padding:16px}
h1{font-size:20px;margin:0}.sub{color:#8a94a0;margin:4px 0 12px}
.bar{position:sticky;top:0;background:#14161a;padding:8px 0;border-bottom:1px solid #2a2f37;z-index:9;display:flex;gap:8px;flex-wrap:wrap}
.bar a{color:#88c0d0;font-size:12px;text-decoration:none;border:1px solid #333a44;border-radius:3px;padding:1px 6px}
h2{font-size:18px;color:#e8c07d;margin:26px 0 4px;border-bottom:1px solid #2a2f37}
h3{font-size:14px;color:#9aa7b4;margin:14px 0 6px}
.grid{display:flex;flex-wrap:wrap;gap:10px}
.card{width:340px;background:#1e222a;border:1px solid #2a2f37;border-radius:6px;padding:9px}
.card.done{border-color:#3f6b4a;background:#1b241d}
.role{font-size:11px;font-weight:700}video{width:100%;border-radius:4px;background:#000;margin:5px 0}
.nov{background:#191c21;border:1px dashed #333a44;color:#6f7a86;font-size:11px;padding:14px;text-align:center;margin:5px 0;border-radius:4px}
.meta,.mom{font-size:11px;color:#9aa7b4}.chip{display:inline-block;background:#232830;border:1px solid #333a44;color:#9aa7b4;border-radius:3px;padding:0 5px;margin:0 3px 3px 0;font-size:10px}
.tag{display:inline-block;border-radius:3px;padding:0 5px;margin:0 3px 3px 0;font-size:10px;color:#14161a;font-weight:700}
select,textarea{width:100%;background:#14161a;color:#dfe3e8;border:1px solid #333a44;border-radius:4px;padding:5px;font:12px system-ui;margin-top:5px}
button{background:#2d5b8a;color:#fff;border:0;border-radius:4px;padding:5px 11px;cursor:pointer}
.st{font-size:11px;color:#8a94a0}.st.ok{color:#a3be8c}.st.bad{color:#e06c75}
</style>""")
w("<div class='bar'><span id='n' class='st'></span>%s</div>"
  % "".join("<a href='#gt_%s'>%s</a>" % (g, g) for g in gts))
w("<h1>Round review v3 &mdash; trait rules from your notes</h1>")
w("<div class='sub'>%s units from %s demos. CA = whole rounds (countdown &rarr; your death / "
  "round end). Other gametypes = your kill chains (&le;6 s gaps), each gametype ranked "
  "on its own; TDM/FFA count half. <b>SAVED</b> = you saved this moment as its own demo. "
  "Top %d per weapon lane.</div>" % (f"{summary['units']:,}", f"{summary['demos_in_scope']:,}", PER_LANE))

for g in gts:
    n = sum(len(v) for v in by[g].values())
    w("<h2 id='gt_%s'>%s <span class='meta'>(%d units with your kills)</span></h2>" % (g, e(g), n))
    for lane in sorted(by[g], key=lambda l: -len(by[g][l])):
        us = by[g][lane]
        w("<h3>%s &middot; %d</h3><div class='grid'>" % (e(lane), len(us)))
        for u in us[:PER_LANE]:
            k = rid(u)
            s = samples.get((u["content_hash"], u["start_ms"]))
            w("<div class='card' data-id='%s'>" % k)
            w("<div class='role' style='color:%s'>%s &middot; %.0f%s</div>"
              % (ROLE.get(u["role"], "#8a94a0"), u["role"].replace("_", " "), u["score"],
                 " &middot; SAVED" if u.get("saved_by_recorder") else ""))
            if s:
                w("<video controls preload='metadata' src='%s'></video>" % e(Path(s["mp4"]).name))
            else:
                w("<div class='nov'>not captured yet &mdash; %s &rarr; %s (%.1fs)</div>"
                  % (ms(u["start_ms"]), ms(u["end_ms"]), (u["end_ms"] - u["start_ms"]) / 1000))
            w("<div class='meta'>%s &middot; #%s &middot; %d kills &middot; %s</div>"
              % (e(u["map"] or "?"), u["round"], u["kills"], u["end_reason"]))
            w("<div>%s</div>" % "".join("<span class='tag' style='background:%s'>%s</span>"
                                        % (TAG.get(t, "#8a94a0"), e(t)) for t in u["tags"]))
            for m in u["moments"]:
                w("<div class='mom'>+%.1fs %s &middot; %.0f%s%s</div>"
                  % ((m["t"] - u["fight_ms"]) / 1000, e(m["weapon"] or "?"), m["value"],
                     " &middot; HERO" if m["hero"] else "",
                     " &middot; chain x%d" % m["chain"] if m.get("chain", 1) > 1 else ""))
            w("<div>%s</div>" % "".join("<span class='chip'>%s</span>" % e(t) for t in u["traits"]))
            w("<select id='rw_%s'><option value=''>WORTH&hellip;</option>%s</select>"
              % (k, "".join("<option>%s</option>" % v for v in
                            ("GOLDEN", "HIGH", "MED", "LOW", "DROP", "DISCOUNT"))))
            w("<textarea id='rv_%s' placeholder='good round? right boundaries? which moment?'></textarea>" % k)
            w("<button onclick=\"sub('%s')\">Submit</button> <span class='st' id='s_%s'></span></div>" % (k, k))
        w("</div>")

w("""<script>
let S={};function st(t){document.getElementById('n').textContent=t;}
fetch('/answers',{credentials:'same-origin'}).then(r=>r.json()).then(j=>{S=j||{};
 document.querySelectorAll('select,textarea').forEach(el=>{if(S[el.id])el.value=S[el.id];});
 document.querySelectorAll('.card').forEach(c=>{const i=c.dataset.id;if(S['rw_'+i]||S['rv_'+i])c.classList.add('done');});
 st(Object.keys(S).filter(k=>/^r[wv]_/.test(k)).length+' round answers on server');}).catch(()=>st('offline'));
async function sub(id){const s=document.getElementById('s_'+id);
 const w=document.getElementById('rw_'+id).value,v=document.getElementById('rv_'+id).value;
 if(!w&&!v.trim()){s.className='st bad';s.textContent='pick a WORTH or write';return;}
 const b={};b['rw_'+id]=w;b['rv_'+id]=v;
 try{const r=await fetch('/save',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});
  if(!r.ok||(r.headers.get('content-type')||'').indexOf('application/json')<0)throw new Error('sign-in expired?');
  const a=await(await fetch('/answers',{credentials:'same-origin'})).json();
  if(a['rw_'+id]!==w&&a['rv_'+id]!==v)throw new Error('not on server');
  s.className='st ok';s.textContent='\\u2713 saved';document.querySelector('[data-id=\"'+id+'\"]').classList.add('done');
 }catch(e){s.className='st bad';s.textContent='NOT saved: '+e.message;}}
</script>""")
(HERE / "samples" / "round_review_v3.html").write_text("\n".join(L), encoding="utf-8")
print("wrote round_review_v3.html: %d gametypes, %d cards"
      % (len(gts), sum(min(len(v), PER_LANE) for g in gts for v in by[g].values())))
