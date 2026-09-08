"""Bounded feasibility probe: action worth watching that ends in NO kill.

One demo. Read-only. Writes nothing. The question is only whether the
already-extracted caches can find these moments at all, before anyone
commits to a corpus-wide pass.
"""
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, r"G:\QUAKE_LEGACY")

DB = 'creative_suite/database/frag_recognition.db'
c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
c.row_factory = sqlite3.Row

# A demo the user recorded, with plenty of action.
H = "022936b4669da860db3d236370b6505b1ec886b8f673eee46aeb8899da1673e1"

kills = {int(r["server_time_ms"]) for r in c.execute(
    "select server_time_ms from kill_events_v1 where content_hash=?", (H,))}
print(f"kills in this demo: {len(kills)}")

# The recorder's own trigger pulls.
shots = [int(r["server_time_ms"]) for r in c.execute(
    "select server_time_ms from semantic_events_v1 where content_hash=? "
    "and type='fire_weapon' and source='playerstate' order by 1", (H,))]
# Pain landing on somebody, with a victim id.
pains = [(int(r["server_time_ms"]), r["client_num"]) for r in c.execute(
    "select server_time_ms, client_num from semantic_events_v1 "
    "where content_hash=? and type='pain' and client_num is not null "
    "order by 1", (H,))]
print(f"recorder shots: {len(shots)}   pain events: {len(pains)}")

WINDOW = 3000          # a burst is what happens inside three seconds
MIN_PAIN = 4           # measured below; a real burst, not one poke

# Slide a window over pain events and keep those the recorder was shooting into.
shots_sorted = shots
import bisect
bursts = []
for i, (t, victim) in enumerate(pains):
    j = bisect.bisect_left(pains, (t + WINDOW, 0), lo=i)
    group = pains[i:j]
    if len(group) < MIN_PAIN:
        continue
    lo = bisect.bisect_left(shots_sorted, t - 500)
    hi = bisect.bisect_right(shots_sorted, t + WINDOW)
    my_shots = hi - lo
    if my_shots < 3:
        continue                       # somebody else's fight
    victims = {v for _, v in group}
    bursts.append({"t": t, "pain": len(group), "victims": len(victims),
                   "shots": my_shots,
                   "ends_in_kill": any(abs(k - t) < WINDOW + 1500
                                       for k in kills)})

# Collapse overlapping windows to one moment each.
merged = []
for b in sorted(bursts, key=lambda d: d["t"]):
    if merged and b["t"] - merged[-1]["t"] < WINDOW:
        if b["pain"] > merged[-1]["pain"]:
            merged[-1] = b
        continue
    merged.append(b)

nokill = [b for b in merged if not b["ends_in_kill"]]
print()
print(f"damage bursts found: {len(merged)}")
print(f"  of which end in a kill : {len(merged) - len(nokill)}")
print(f"  of which end in NOTHING: {len(nokill)}   <- currently invisible")
print()
for b in nokill[:8]:
    print(f"   t={b['t']:>8}  {b['pain']:2} pain on {b['victims']} enemy(s), "
          f"{b['shots']:3} of my shots, no kill")
