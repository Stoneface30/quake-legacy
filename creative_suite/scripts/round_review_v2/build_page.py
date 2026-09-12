"""Round review page: one card per round, grouped gametype -> weapon lane -> score.

A round appears ONCE however many traits fired in it; every trait is shown on
the card as evidence. Captured samples play inline; rounds not yet captured
show their window and why they ranked. Answers go through the same /save
endpoint as the calibration page, keyed `rw_`/`rv_` + round id so they can
never collide with per-clip calibration answers.
"""
from __future__ import annotations

import collections
import hashlib
import html
import json
from pathlib import Path

HERE = Path("G:/QUAKE_LEGACY/output/demo_v2/round_review_v2")
PER_LANE = 25

rounds = json.loads((HERE / "rounds_ranked.json").read_text(encoding="utf-8"))
summary = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
samples = {}
sp = HERE / "samples" / "samples.json"
if sp.exists():
    for s in json.loads(sp.read_text(encoding="utf-8")):
        if s.get("mp4") and s.get("duration_ok"):
            # Exact identity when the sample recorded it; otherwise the window
            # PLUS the round's trait set. (map, round, window) alone collided
            # across different demos -- 33 cards showed a video for 12 samples,
            # i.e. some cards played footage of a different round.
            if s.get("content_hash") and s.get("start_ms") is not None:
                samples[("id", s["content_hash"], s["start_ms"])] = s
            else:
                samples[(s["map"], s["round"], round(s["window_s"], 1),
                         tuple(sorted(s.get("traits") or ())))] = s


def rid(u):
    return hashlib.sha1(("%s|%s|%s" % (u["content_hash"], u["round"], u["start_ms"]))
                        .encode()).hexdigest()[:12]


def ms(t):
    return "%d:%06.3f" % (t // 60000, (t % 60000) / 1000.0)


by_lane = collections.defaultdict(list)
for u in rounds:
    if u["kills"]:
        by_lane[u["lane"]].append(u)
lanes = sorted(by_lane, key=lambda l: -len(by_lane[l]))

ROLE_COL = {"HERO_ROUND": "#e8c07d", "STRONG_ROUND": "#a3be8c",
            "FILLER_ROUND": "#88c0d0", "TRANSITION_OR_BLOOPER": "#b48ead",
            "LOW_VALUE": "#6f7a86"}
L = []
w = L.append
w("<!doctype html><meta charset='utf-8'><title>Round review V2</title>")
w("""<style>
body{background:#14161a;color:#dfe3e8;font:14px/1.5 system-ui,sans-serif;margin:0;padding:20px}
h1{font-size:20px;margin:0}.sub{color:#8a94a0;margin:4px 0 14px}
.bar{position:sticky;top:0;background:#14161a;padding:9px 0;border-bottom:1px solid #2a2f37;z-index:9}
button{background:#2d5b8a;color:#fff;border:0;border-radius:4px;padding:6px 12px;cursor:pointer}
.lane{margin:18px 0}.lane h2{font-size:16px;color:#e8c07d;margin:0 0 8px}
.grid{display:flex;flex-wrap:wrap;gap:12px}
.card{width:360px;background:#1e222a;border:1px solid #2a2f37;border-radius:6px;padding:9px}
.card.done{border-color:#3f6b4a;background:#1b241d}
.role{font-size:11px;font-weight:700;letter-spacing:.4px}
video{width:100%;border-radius:4px;background:#000;margin:5px 0}
.nov{background:#191c21;border:1px dashed #333a44;color:#6f7a86;font-size:11px;padding:18px;text-align:center;margin:5px 0;border-radius:4px}
.meta{font-size:11px;color:#8a94a0}.why{font-size:11px;color:#9aa7b4;margin:3px 0}
.chip{display:inline-block;background:#232830;border:1px solid #333a44;color:#9aa7b4;border-radius:3px;padding:0 5px;margin:0 3px 3px 0;font-size:10px}
.mom{font-size:11px;color:#9aa7b4;margin:2px 0}
select,textarea{width:100%;background:#14161a;color:#dfe3e8;border:1px solid #333a44;border-radius:4px;padding:5px;font:12px system-ui;margin-top:5px}
.act{display:flex;gap:8px;align-items:center;margin-top:6px}.st{font-size:11px;color:#8a94a0}.st.ok{color:#a3be8c}.st.bad{color:#e06c75}
</style>""")
w("<div class='bar'><span id='n' class='st'></span></div>")
w("<h1>Round review V2</h1>")
w("<div class='sub'>%s rounds from %s CA demos (only %s quarantined). Each clip "
  "runs from 5 s before the fight to your death, the round end or the demo end "
  "&mdash; never into the next round. Top %d per weapon lane shown. "
  "<b>WORTH</b>: GOLDEN / HIGH / MED / LOW / DROP / DISCOUNT.</div>"
  % (f"{summary['rounds_built']:,}", f"{summary['demos_in_scope']:,}",
     sum(summary["quarantined"].values()), PER_LANE))

def skey(u):
    """The key this round's sample is filed under, or None if it has none."""
    exact = ("id", u["content_hash"], u["start_ms"])
    if exact in samples:
        return exact
    fallback = (u["map"], u["round"], round((u["end_ms"] - u["start_ms"]) / 1000.0, 1),
                tuple(sorted(u["traits"])))
    return fallback if fallback in samples else None


# Captured rounds first, whatever their current rank: they exist to check the
# boundaries by eye, and rescoring can push them out of a lane's top 25.
sampled = [u for u in rounds if skey(u) in samples]
sections = [("CAPTURED SAMPLES &mdash; check the boundaries", sampled, len(sampled))]
sections += [(html.escape(l), by_lane[l][:PER_LANE], len(by_lane[l])) for l in lanes]

for title, us, total in sections:
    w("<div class='lane'><h2>%s <span class='meta'>(%d rounds)</span></h2>"
      "<div class='grid'>" % (title, total))
    for u in us:
        k = rid(u)
        s = samples.get(skey(u))
        w("<div class='card' data-id='%s'>" % k)
        w("<div class='role' style='color:%s'>%s &middot; %.0f</div>"
          % (ROLE_COL.get(u["role"], "#8a94a0"), u["role"].replace("_", " "), u["score"]))
        if s:
            rel = "samples/" + Path(s["mp4"]).name
            w("<video controls preload='metadata' src='%s'></video>" % html.escape(rel))
        else:
            w("<div class='nov'>not captured yet &mdash; window %s &rarr; %s (%.1fs)</div>"
              % (ms(u["start_ms"]), ms(u["end_ms"]), (u["end_ms"] - u["start_ms"]) / 1000))
        w("<div class='meta'>%s &middot; round %s &middot; %d kills &middot; ends: %s</div>"
          % (html.escape(u["map"] or "?"), u["round"], u["kills"], u["end_reason"]))
        for m in u["moments"]:
            w("<div class='mom'>+%.1fs %s &middot; %.0f pts%s</div>"
              % ((m["t"] - u["fight_ms"]) / 1000, html.escape(m["weapon"] or "?"),
                 m["value"], " &middot; HERO" if m["hero"] else ""))
        w("<div class='why'>%s</div>" % "".join(
            "<span class='chip'>%s</span>" % html.escape(t) for t in u["traits"]))
        w("<select id='rw_%s'><option value=''>WORTH&hellip;</option>%s</select>"
          % (k, "".join("<option>%s</option>" % v for v in
                        ("GOLDEN", "HIGH", "MED", "LOW", "DROP", "DISCOUNT"))))
        w("<textarea id='rv_%s' placeholder='Is this round good? Right boundaries? "
          "Which moment carries it?'></textarea>" % k)
        w("<div class='act'><button onclick=\"sub('%s')\">Submit</button>"
          "<span class='st' id='s_%s'></span></div></div>" % (k, k))
    w("</div></div>")

w("""<script>
let S={};
function st(t){document.getElementById('n').textContent=t;}
fetch('/answers').then(r=>r.json()).then(j=>{S=j||{};
 document.querySelectorAll('select,textarea').forEach(el=>{if(S[el.id])el.value=S[el.id];});
 document.querySelectorAll('.card').forEach(c=>{const i=c.dataset.id;
  if(S['rw_'+i]||S['rv_'+i])c.classList.add('done');});
 st(Object.keys(S).filter(k=>k.startsWith('r')).length+' round answers on server');
}).catch(()=>st('offline'));
async function sub(id){const s=document.getElementById('s_'+id);
 const w=document.getElementById('rw_'+id).value, v=document.getElementById('rv_'+id).value;
 if(!w&&!v.trim()){s.className='st bad';s.textContent='pick a WORTH or write';return;}
 const body={}; body['rw_'+id]=w; body['rv_'+id]=v;
 try{const r=await fetch('/save',{method:'POST',credentials:'same-origin',
   headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const ct=r.headers.get('content-type')||'';
  if(!r.ok||ct.indexOf('application/json')<0)throw new Error('sign-in expired?');
  const a=await(await fetch('/answers',{credentials:'same-origin'})).json();
  if(a['rw_'+id]===w||a['rv_'+id]===v){s.className='st ok';s.textContent='\\u2713 saved';
   document.querySelector('[data-id=\"'+id+'\"]').classList.add('done');}
  else throw new Error('not on server');
 }catch(e){s.className='st bad';s.textContent='NOT saved: '+e.message;}}
</script>""")
(HERE / "round_review.html").write_text("\n".join(L), encoding="utf-8")
print("wrote round_review.html: %d lanes, %d cards, %d with video"
      % (len(lanes), sum(min(len(by_lane[l]), PER_LANE) for l in lanes), len(samples)))
