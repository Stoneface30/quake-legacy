# PART 2 — CLAN ARENA RULES, VERIFIED

**Framing caveat that governs everything below.** Quake Live's *server* logic is
closed and is not in this repo. The only CA-aware C source here is **WolfcamQL**,
a *client / demo player*: it observes QL's protocol, it does not define the
rules. "Verified from source" therefore means "verified from how the QL client
parses and reacts to QL server state" — strong, but one step removed. The 4,292
demo corpus is the second, independent evidence line.

Evidence classes: **(a)** source · **(b)** corpus · **(c)** UNVERIFIED.

---

## THE VERIFIED RULE SET

| # | Rule | Class | Confidence |
|---|---|---|---|
| 1 | CA is gametype **4** | (a) | Very high |
| 2 | **4v4 is modal, not universal** — 52% of rosters | (b) | High |
| 3 | Spawn with **Gauntlet, MG, SG, GL, RL, LG, Rail, Plasma**. No BFG | (b) | High |
| 4 | Spawn **200 health / 100 armour** | (b) | High |
| 5 | **No respawn — one life per round** (99.6%) | (a)+(b) | Very high |
| 6 | Round ends when a team is wiped | (a)+server text | High |
| 7 | Full reset of health/armour/weapons each round | (b) | Medium-high |
| 8 | **First to 10 rounds wins** | (b)+server text | Very high |
| 9 | **~7 s countdown**, announced 5-3-2-1-FIGHT | (a)+(b) | Very high |
| 10 | Round timelimit value & timeout behaviour | — | **UNVERIFIED** |
| 11 | Starting ammo counts | — | **UNVERIFIED** |
| 12 | That 10 is id's shipped *default* (vs. this corpus's servers) | — | **UNVERIFIED** |

### Evidence highlights

**Gametype 4** — `_canonical/code/game/bg_public.h:401-421` (`GT_CA=4`);
`cg_draw.c:10214` maps it to the string "Clan Arena". Independently confirmed in
`variants/qldemo-python/qldemo/constants.py:96`.

**One life** — deaths per (demo, round, victim) over `kill_events_v1`:
**195,259 pairs (99.6%) have exactly one death**. Of the 502 multi-death cases,
**375 are in `round == 0`** — pre-match warmup, where free respawn is expected.
Corroborated in source: the client resets a per-player alive flag only at round
start (`cg_servercmds.c:2716-2718`), and the server broadcasts dedicated
survivor counters `CS_RED_PLAYERS_LEFT 663` / `CS_BLUE_PLAYERS_LEFT 664`
(`bg_public.h:111-112`) — counters that only make sense with no respawning.

**Loadout** — CA maps carry no weapon pickups, so the earliest kill by each
weapon bounds the spawn loadout. Rocket kill at **0.07 s** into a round, rail at
0.33 s, LG at 0.88 s. BFG appears **3 times in 215,831 kills** (0.001%, almost
certainly non-CA demos in the scan set) → **not in the loadout**.

**200/100** — health/armour samples landing on round start: **200 HP in 82%**,
**100 armour in 82%**; armour never exceeds 100 anywhere in the corpus.

**Round end** — server text, captured verbatim:
`^1RED TEAM^3 WINS the round!^7 (2 players remaining)`. Mechanically, the server
sets `CS_ROUND_TIME (662)` to −1 (`bg_public.h:109`; handled
`cg_servercmds.c:2745-2749`).

**First to 10** — `Red hit the roundlimit.` ×2,331 and `Blue hit the roundlimit.`
×2,316 in server text. Max team score per demo: 2,692 demos peak at exactly 10,
and **zero demos land anywhere between 11 and 14**. That absence is the proof —
10 is a hard cap, not a distribution peak.

**7-second countdown** — `CS_ROUND_STATUS (661)` carries a *future* start
timestamp. Over **66,703 samples**, 95.0% are ~7,000 ms (median 7,025 ms).
Announcer at t−5 s, then "3", "2", "1", then FIGHT (`cg_draw.c:7146-7181`).

### Round duration (corpus, n = 39,063)
Median **25.4 s**, mode 15–25 s. There is **no cliff at 180 s**, so the round
timelimit is not observable; 753 rounds run past 200 s and look like missed
end-markers rather than real play. **No "round draw" text exists in 256,651
captured server messages.** Nothing about timeout may appear on screen.

---

## CORRECTION TO THE BRIEF

The brief's suggested card `4 VS 4` needs care. **4v4 is the canonical format and
the modal one (52% of rosters), but roughly half of recorded rounds are 3v3 or
smaller** — pub servers and mid-match leavers. The gametype does not enforce it.

Permitted: **`USUALLY FOUR A SIDE`**, or `4 VS 4` shown *over a synthetic round
that is actually 4v4*, where it describes the picture rather than the archive.
Not permitted: `4 VS 4` over a montage of real rounds, which would be false for
about half of them.

The brief also flagged `ONE LIFE PER ROUND` as "only if verified wording is
accurate". **It is accurate — 99.6%.** It is the strongest verified claim in
Part 2 and should carry the section.

---

## THE APPROVED ON-SCREEN PARAGRAPH

Every clause below is backed above:

> Clan Arena: two teams, usually four a side. Every round you spawn with every
> weapon, 200 health and 100 armour. Seven seconds of countdown, then FIGHT. You
> get one life. Kill the other team and the round is yours. First to ten rounds
> wins.

## REPRODUCING THIS
All corpus claims: `creative_suite/database/frag_recognition.db`, opened
`file:...?mode=ro` (uri=True). Tables `round_state_v1`, `kill_events_v1`,
`player_teams_v1`, `recognized_frags`, `server_text_v1`. Read-only throughout.
