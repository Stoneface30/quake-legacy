# QUAKE LEGACY — Curated Music Picks (Parts 4-12)
**Date:** 2026-04-17
**Source pool:** `phase1/music/spotify_urls.txt` (1,057 URLs), `spotify_meta_cache.json` (949 resolved)
**Criteria:** absolute-best match per Part, current 2024-2026 hype trends, fragmovie-fit energy curve

---

## Selection Logic

2024-2026 fragmovie trend landscape:
- **HYPERTECHNO / TECHNO-VERSION edits** — dominant YT gaming sound 2024-25 (BASSTON, BENNETT, KETNO)
- **Hardtekk / Tekkno** — German scene that crossed over globally (TEKKNO, FoxTune)
- **Phonk** — peak 2023-24, still the Quake/movement-shooter default
- **D&B / Jungle** — classic Quake fit, never dated
- **Rave edits of pop vocals** — viral template (MAKEBA, Vois sur ton chemin, SPRINTER)

Narrative arc across Parts 4-12:
```
4  HOOK         →  5 BURST       →  6 BREATHE    (first act)
7  MID-PEAK     →  8 MOMENTUM    →  9 GROOVE     (second act)
10 CHAOS        →  11 EPIC BUILD →  12 FINALE    (third act)
```

---

## Per-Part Picks

### PART 4 — HOOK (currently: Bucky Don Gun, rendered)
**PICK:** `MAKEBA - (TECHNO)` — BASSTON, STRÖBE
https://open.spotify.com/track/6b8DQCyVfqRwyGBP2A84db
- Why: viral 2023-24 hook, massive pre-drop build, instrumental-dominant. One of the most recognizable current-trend techno flips. A fragmovie opener people hit replay on.
- Current file: `part04_music.mp3` = Bucky Don Gun (great track, less hype trend). **Keep-or-swap decision pending Part 4 review.** If you feel Part 4's opening wants more immediate punch, swap to MAKEBA and re-render.

### PART 5 — BURST (currently: Jump Up Quickly Zero Remix, rendered)
**PICK:** `Phonky Tribu` — Funk Tribu
https://open.spotify.com/track/7aIb17DMLcOhLJIc9vF6Aa
- Why: THE phonk anthem. 140 BPM in-the-pocket cowbell groove = perfect for tight rail/rocket sequences. Universal fragmovie language 2023-25. Jump Up Quickly is strong but more niche reggae-step; Phonky Tribu is the bigger flag-plant.

### PART 6 — BREATHE (currently: Nothing by HNNY, rendered)
**PICK:** `Past Lives - Hardtekk` — FoxTune
https://open.spotify.com/track/4YULjpe4q71CrqgXIwoe77
- Why: emotional hardtek — melodic top-line + 150 BPM underneath. Lets slow-mo / FL cinematics breathe without losing forward momentum. `Nothing` is beautiful but flat; `Past Lives` is current AND has a floor. Hero candidate for Part 6's T3 cinematic openers.

### PART 7 — MID-PEAK (currently: SPERENZIEN)
**PICK:** `SPRINTER - (TECHNO SPED UP)` — FAST BASSTON
https://open.spotify.com/track/4cU7BrdaOpKLJWdTZr8GEE
- Why: Central Cee's SPRINTER is the most-played global track of 2023; the techno-sped flip is the current fragmovie translation. Dense 160+ BPM, punches on every second beat — hits dead-center for dense multi-kill sequences.

### PART 8 — MOMENTUM (currently: Moxy Edits 010)
**PICK:** `bulletproof tekkno` — TEKKNO
https://open.spotify.com/track/4qRdS6InvlnugJxfOIh0CP
- Why: named for fraggable energy. Tekkno scene anchor artist. Continuous driving pulse with no big breakdowns — ideal for mid-series momentum where we don't want peaks yet.

### PART 9 — GROOVE (currently: Take 2 DJ SWISHERMAN)
**PICK:** `Zoo - Rave Edit` — Vladimir Cauchemar, Kaaris, AIROD
https://open.spotify.com/track/2KPEjEtjSdOOzcSliuXjna
- Why: dark groove rave edit. Hip-hop + techno fusion aesthetic that's peaking 2024-26. AIROD is a current-scene producer. Gives Part 9 a distinct identity vs 7/8's pure-tekkno.

### PART 10 — CHAOS (currently: B.A.I.L.A)
**PICK:** `ANXIETY (HYPERTECHNO)` — Kroniqa, HYPERAVE
https://open.spotify.com/track/5mN7unZnLDSVPmn0qYw9Fq
- Why: hypertechno is THE 2024-25 breakout sub-genre. 170+ BPM, literal anxiety energy. Perfect for the most chaotic T1 concentration of the series. Name is on-the-nose in a good way.

### PART 11 — EPIC BUILD (currently: Our World KT-KLIZM)
**PICK:** `Timewarp - Dimension Remix` — Sub Focus, Dimension
https://open.spotify.com/track/2utAuZWOq0Staky6RgtfLE
- Why: drum-and-bass anthem by two top-tier UK producers. 174 BPM, the speed Quake movement naturally wants. Epic orchestral build into d&b drop = perfect penultimate-part escalation into the finale.

### PART 12 — FINALE (currently: A Festa Trüby Trio)
**PICK:** `Vois sur ton chemin - Techno Mix` — BENNETT
https://open.spotify.com/track/31nfdEooLEq7dn3UMcIeB5
- Why: **the** biggest techno cross-over of 2024 — French choral sample over pounding techno, went #1 in multiple EU markets, massive on gaming content. Emotionally huge, universally recognizable, massive drop = series finale that people screenshot. A Festa is a solid samba-house track but this is GOAT-tier finale material.

---

## Action Plan

**If you approve the picks:** I run this to replace all 9 tracks and regenerate beat caches:
```bash
python phase1/music/download_tracks.py --replace \
  part04=https://open.spotify.com/track/6b8DQCyVfqRwyGBP2A84db \
  part05=https://open.spotify.com/track/7aIb17DMLcOhLJIc9vF6Aa \
  part06=https://open.spotify.com/track/4YULjpe4q71CrqgXIwoe77 \
  part07=https://open.spotify.com/track/4cU7BrdaOpKLJWdTZr8GEE \
  part08=https://open.spotify.com/track/4qRdS6InvlnugJxfOIh0CP \
  part09=https://open.spotify.com/track/2KPEjEtjSdOOzcSliuXjna \
  part10=https://open.spotify.com/track/5mN7unZnLDSVPmn0qYw9Fq \
  part11=https://open.spotify.com/track/2utAuZWOq0Staky6RgtfLE \
  part12=https://open.spotify.com/track/31nfdEooLEq7dn3UMcIeB5
python phase1/music/analyze_all_tracks.py  # regenerates .beats.json for all
```

**Cost:**
- Parts 7-12: zero re-render cost (they haven't rendered yet — batch will use new tracks automatically)
- Parts 4, 5, 6: changing their music = re-render each (45-60 min/part on NVENC av1 p7 = ~3h total).
  - **Cheaper path:** keep current 4/5/6 music (rendered, you're reviewing them now) and only apply new picks to Parts 7-12.

**Recommend:** you pick *per Part* from the list below which are must-swap vs acceptable-as-is.

## Your Approval Checklist
Copy-paste back with each line marked `keep` / `swap` / `other:<url>`:
```
Part 4  (current: Bucky Don Gun)         → proposed: MAKEBA TECHNO            [ ]
Part 5  (current: Jump Up Quickly)       → proposed: Phonky Tribu             [ ]
Part 6  (current: Nothing HNNY)          → proposed: Past Lives Hardtekk      [ ]
Part 7  (current: SPERENZIEN)            → proposed: SPRINTER TECHNO SPED UP  [ ]
Part 8  (current: Moxy Edits 010)        → proposed: bulletproof tekkno       [ ]
Part 9  (current: Take 2 SWISHERMAN)     → proposed: Zoo Rave Edit            [ ]
Part 10 (current: B.A.I.L.A)             → proposed: ANXIETY HYPERTECHNO      [ ]
Part 11 (current: Our World)             → proposed: Timewarp Dimension Rmx   [ ]
Part 12 (current: A Festa)               → proposed: Vois sur ton chemin TM   [ ]
```
