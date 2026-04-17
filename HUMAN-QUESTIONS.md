# QUAKE LEGACY — Awaiting-Human Decisions
*The single source of truth for anything blocking on your input.*

**Last updated:** 2026-04-17
**How to use this file:** read top-to-bottom. Answer questions inline (replace `[ ]` with `[x]`, fill blanks). Anything marked `BLOCKING` means autonomous work cannot progress past it. Everything else is nice-to-have.

Claude will re-read this file on every session start and act on anything answered since last time.

---

## 1. BLOCKING — Part 3 Style Lock

Three full-length 5:07 renders produced:

- [ ] **Style A (Cinematic, 874 MB)** — `output/previews/Part3_styleA_preview.mp4` — T1 anchored, slower rhythm
- [ ] **Style B (Punchy, 989 MB)** — `output/previews/Part3_styleB_preview.mp4` — **current default V2 baseline**
- [ ] **Style C (Showcase, 867 MB)** — `output/previews/Part3_styleC_preview.mp4` — all-angle rotation
- [ ] **None — V5 is a new hybrid. Notes:** _______________________________________

**Style lock is the unblocker for Parts 4-12 full renders.** Nothing downstream moves without this.

Feedback prompt (optional, per style picked):
- Pacing: [ ] too slow [ ] good [ ] too fast [ ] uneven
- Grade (contrast 1.4 / sat 1.7): [ ] right [ ] too much [ ] too little
- Game audio at 55% under music: [ ] right [ ] louder [ ] quieter → target: _____%
- Xfade 0.08s micro-flash: [ ] invisible (good) [ ] still too soft [ ] want full hard cut 0s
- PANTHEON intro 7s: [ ] right length [ ] too short [ ] too long — target: _____ s

---

## 2. BLOCKING — Gate P3-0 Highlight Criteria

Cannot parse the 2,277-demo corpus until these are defined. Read `docs/specs/highlight-criteria-v1.md` and `docs/research/frag-scoring-features.md` first.

### 2.1 Airshot rules
- Minimum victim air time for an "airshot" to count: _______ ms
- Minimum victim vertical velocity magnitude: _______ u/s
- Weapon whitelist for airshots: [ ] rocket only [ ] rocket+rail [ ] rocket+rail+grenade [ ] any
- Airshot at apex (|vz| < 50) — weight multiplier: _______× (default 1.5)

### 2.2 Multi-kill window
- Time window to count as a multi-kill: [ ] 2s [ ] 3s [ ] 5s [ ] other: _____
- Double kill: weight _______
- Triple kill: weight _______
- Quad+: weight _______
- Spawn-frags count as multi-kill? [ ] yes [ ] no [ ] only if ≥3

### 2.3 Weapon weights (baseline score multipliers)
Default v1 in `highlight-criteria-v1.md`. Override if you disagree:
- Rail frag (direct): _______ (default 1.8)
- LG frag: _______ (default 1.3)
- Direct rocket (non-splash): _______ (default 1.5)
- Grenade direct: _______ (default 2.0)
- Gauntlet: _______ (default 3.0, humiliation factor)
- Telefrag: _______ (default 1.5, intentional)
- Plasma spam: _______ (default 1.0)
- Shotgun: _______ (default 1.1)
- MG: _______ (default 0.8)

### 2.4 Distance thresholds
- Long range (rail): > _______ units (default 1000)
- Extreme range (rail): > _______ units (default 2000)

### 2.5 LG sustained accuracy
- Minimum accuracy % to count as "precision LG frag": _______ (default 60)
- Window size: _______ s (default 3)

### 2.6 LMS / Clutch context
- Is "last man standing" a separate tag? [ ] yes [ ] no
- Clutch (1 vs 2+) multiplier: _______× (default 1.4)

### 2.7 Minimum threshold
- Ignore any frag with final score below: _______ (default 0.25)
- T1 threshold (peak): ≥ _______ (default 0.70)
- T2 threshold (main meal): ≥ _______ (default 0.45)
- T3 threshold (filler): ≥ _______ (default 0.25)

### 2.8 Context tags wanted (for overlay info in Phase 1/2)
- [ ] Tag official pracc matches (show team names as overlay context)
- [ ] Tag map in corner of clip
- [ ] Tag round number in CA
- [ ] Other: ___________________________________________

### 2.9 Weapon-combo sequences worth highlighting
- [ ] Rail + rocket within _____ ms
- [ ] LG → rail sequence within _____ ms
- [ ] Grenade + rocket within _____ ms
- [ ] Preshot (rocket fired before visual): _____ ms prediction window
- [ ] Pixel rail (hit through corner of texture): weight _______
- [ ] Other signature combos: ___________________________________________

---

## 3. BLOCKING — Phase 2 Parser Path

Current state: qldemo-python works for metadata + configstring mining, but `parse_snapshot` entity extraction is **stubbed**. All 222 sample frags are `is_approx_time=True`, which collapses multi-kill detection.

**Now we also have:** `docs/reference/dm73-format-deep-dive.md` — 1,337-line complete spec of the format with source citations. Enough to implement a parser from scratch. This changes the calculus.

Two paths forward, **pick one**:

- [ ] **Path A — Build UDT_json.exe from sources** (≈1 day). `premake5.exe` is on disk at `tools/quake-source/uberdemotools/UDT_DLL/premake/`. Known path, lower risk. Use existing C++ codebase.
- [ ] **Path B — Write our own .cpp parser** (≈1-2 weeks). User said "we will explode uberdemotool with our own custom made one that fit EXACTLY our need". Deep-dive agent has scaffolded a concrete plan (see §3.1 below). Higher effort, but we own the whole stack.
- [ ] **Path C — Finish `parse_snapshot` entity parsing in qldemo-python** (≈3-5 days, ~400 LOC). Pure-Python, keeps the toolchain simple.

**Recommendation from Claude:** Given the deep-dive doc is this thorough, Path B is now much lower risk than originally estimated. If you want to end up with a custom parser anyway, doing it now saves a throwaway step. If you want Parts 4-12 rendering NEXT WEEK, Path A unblocks faster.

### 3.1 Custom parser scaffold decisions (only if you pick Path B)

From the deep-dive agent — confirm each so Claude can lay down code:

**3.1.1 Language / build system**
- [ ] **C++17 + CMake** (recommended — matches UDT, Windows+Linux buildable)
- [ ] Plain C11 (closer to wolfcam source, less glue)
- [ ] Rust (memory-safety win but diverges from vendored sources — harder to pull in upstream fixes)

**3.1.2 Location in repo**
- [ ] `phase2/dm73parser/` — standalone subproject with own CMakeLists, builds static lib + CLI `dm73dump` emitting JSON lines
- [ ] Other: ___________________________________________

**3.1.3 Scope of v1 (minimum viable parser)**
- [ ] **Approve as stated:** container + Huffman + svc_op dispatch → gamestate (configstrings + baselines) → snapshots far enough to extract entity events → JSON output (`obit`, `round_start`, `player`). Defer full playerstate decode to v2.
- [ ] Add to v1: ___________________________________________
- [ ] Remove from v1: ___________________________________________

**3.1.4 Vendoring policy**
- [ ] **Approve:** copy `msg.c`, `huffman.c`, `common.c`, `q_shared.h`, `bg_public.h` verbatim from `tools/quake-source/wolfcamql-src/code/` into `phase2/dm73parser/vendor/`. Keep GPLv2 license headers. `SOURCES.md` notes upstream commit and any modifications.
- [ ] Different vendoring plan: ___________________________________________

**3.1.5 Test fixture**
- [ ] **Approve:** pick 3 demos from `WOLF WHISPERER/wolfcam-ql/demos/`, hand-verify obit counts against `UDT_json.exe` as golden reference before trusting parser.
- [ ] Different test plan: ___________________________________________

---

## 4. Music — Track Confirmations

9 tracks auto-downloaded from YouTube per `phase1/music/MUSIC_SUGGESTIONS.txt`. Current lineup:

| Part | Track | Duration | Status |
|---|---|---|---|
| 4 | SHFTR — Bucky Don Gun | 5:46 | downloaded |
| 5 | Mungo's Hi Fi — Jump Up Quickly (Zero Remix) | 4:20 | downloaded |
| 6 | HNNY — Nothing | 5:12 | downloaded |
| 7 | Dom Valentino + Alfie T — Young Folks | 4:09 | downloaded (primary pick per suggestions) |
| 8 | Darius Syrossian — Moxy Edits 010 | 5:45 | downloaded |
| 9 | Machromel — BAILA | 3:41 | downloaded |
| 10 | ORBi — BADBIE | 3:42 | downloaded |
| 11 | KT-KLIZM — Our World | 6:44 | downloaded |
| 12 | Trüby Trio — A Festa | 6:48 | downloaded |

- [ ] All tracks approved as-is → proceed
- [ ] Swap Part ___ for: ___________________________________________
- [ ] Swap Part ___ for: ___________________________________________

All 10 beat grids (Parts 3-12) already generated in `phase1/music/*.beats.json`.

---

## 5. Phase 1 Effects — Hard Rules Wanted

User's Updated Plan introduced a few principles I want confirmed so I can codify them:

### 5.1 Audio mix level
Previous sessions bounced between 30% / 45% / 55% for game-audio-under-music. User's Updated Plan says **"game audio rides underneath at 30% volume"** but also **"mix = music (100%) + game audio (45%)"** in the same doc. **Pick one:**
- [ ] 30% (current doc top)
- [ ] 45% (current doc detail)
- [ ] 55% (current pipeline — what Part 3 renders used)
- [ ] Other: _____ %

### 5.2 Golden Rule codification
User's Updated Plan: *"the style need to match the music / beat the frag + effect + music is the golden rule of a good video ! please add as hard rule"*.

Proposed as new Rule P1-I in CLAUDE.md:
> **Rule P1-I (Golden Rule): Frag + Effect + Music must align.** The chosen effect (slow-mo, zoom, fast-forward, hard cut) must match both the frag type AND the music beat/section. A T1 peak without matching musical weight, or a slow-mo without a corresponding bass drop, is a miss. Beat-sync is mandatory from Part 4 onward.

- [ ] Approve as worded
- [ ] Reword: ___________________________________________

### 5.3 Extended pre-roll for Phase 2 captures
User wrote: *"we need time for the montage so we can add effect and all"*. Current: 8s pre-roll / 5s post-roll. Extend?
- [ ] Keep 8s / 5s
- [ ] Extend to 12s / 8s
- [ ] Extend to 15s / 10s
- [ ] Other: _____ / _____ s

### 5.4 Render quality for final output
User: *"CRF 17, preset slow — send research agent to look the BEST renderer to have the fucking WOW factor quality, file size DOES NOT MATTER"*.
- [ ] Proceed with research — Claude dispatches an agent to compare FFmpeg CRF 15 vs x265 CRF 18 vs SVT-AV1 vs NVENC HEVC on a test clip
- [ ] Just use FFmpeg x264 CRF 15 preset veryslow and move on
- [ ] Use x265 at CRF 17 preset slow
- [ ] Other: ___________________________________________

---

## 6. Phase 2 — Nickname Dictionary Schema

User wants: *"we can save all the different nicknames a user uses in all the video so we can just rawdog the demo to extract the frag not even look at it, we need to generate the .dem decoder so the demo speak YOUR Language while the image is MY language"*.

Proposed schema (SQLite in `database/frags.db`):

```sql
CREATE TABLE players (
    canonical_id TEXT PRIMARY KEY,          -- our stable ID (SHA256 of first Steam GUID seen)
    steam_guid_hash_prefix TEXT,            -- first 16 hex of GUID hash (never full)
    first_seen_demo INTEGER,                -- FK to demos table
    last_seen_demo INTEGER,
    total_demos INTEGER,
    total_kills INTEGER,
    total_deaths INTEGER,
    is_local_player INTEGER                 -- 1 if this is the recorder (POV owner)
);

CREATE TABLE player_aliases (
    id INTEGER PRIMARY KEY,
    canonical_id TEXT REFERENCES players(canonical_id),
    alias TEXT,                             -- raw nickname as seen in demo (NOT committed to repo)
    first_seen_demo INTEGER,
    last_seen_demo INTEGER,
    seen_count INTEGER
);
```

Privacy stance:
- `alias` strings are stored in the **local** DB only
- `database/frags.db` stays **gitignored** (already is)
- Public-repo exports use `canonical_id` only (opaque hash, no reverse lookup possible)
- The recorder's own POV is flagged `is_local_player=1` so the pipeline can pull their kills separately

- [ ] Approve schema as-is
- [ ] Changes: ___________________________________________

---

## 7. Phase 3 — 3D Intro Lab ("Phase 3.5")

User wrote: *"could provide the intro lab too so we can experiment with the new AI capability with full 3d"*, and *"having some 3d knowledge would be so fucking cool on this engine for full 3d intro, but this is more phase3.5"*.

What this would be:
- A sandbox for AI-assisted 3D intros using the Q3 engine's BSP map format, model (MD3/MDR) loaders, and possibly ComfyUI + AnimateDiff for generative transitions
- Lives alongside Phase 3 but separately — not on the critical path to Parts 4-12

- [ ] Fund Phase 3.5 now (parallel research track)
- [ ] Defer until Parts 4-12 shipped
- [ ] Kill the idea

---

## 8. Parts 1-3 Remaster + Morph Intro

User wrote: *"the dream would be able to take footage from the old video and morph / transform to the new one you know like the live reskin"*.

This is a stretch goal. Planning intent:
- Tools: probably Runway Gen-3 video2video or Stable Video Diffusion with ControlNet
- Inputs: original Part 1/2/3 MP4 + new Part 1/2/3 renders
- Output: a morph sequence showing evolution

- [ ] Research tools now (agent dispatch)
- [ ] Defer to Phase 3.5
- [ ] Kill

---

## 9. Infrastructure — Small Approvals

### 9.1 `.gitignore` additions Claude wants to make
- `output/normalized/` — huge intermediate files, regenerable
- `output/*.log` — session logs
- `phase1/music/*.beats.json` — regenerable from music files (< 1 min each)
- `phase5/01_backup/`, `phase5/02_extracted/`, `phase5/03_processed/` — pipeline artifacts
- [ ] Approve all
- [ ] Pick subset: ___________________________________________

### 9.2 Folder reorg — risky moves awaiting your sign-off
Full detail + justifications in `docs/reference/project-structure-v2.md` §5. Safe moves already executed (pycache consolidation, log consolidation, docs/review → docs/reviews/part04 merge, 55 loose JPGs organized, `docs/superpowers/plans/` → `docs/plans/`, `.gitignore` extended).

- [ ] **R1:** Supersede root `PROJECT_STRUCTURE.md` with new `docs/reference/project-structure-v2.md`
- [ ] **R2:** Resolve `docs/archive/2026-04-17-user-updated-docs-incoming/` vs live docs (spec is identical, plan differs — needs manual diff + merge or delete)
- [ ] **R3:** Rename `Part3_styleA_preview.mp4` → `part03_stylea_preview.mp4` for casing consistency (will break any hardcoded paths — low risk, recommended)
- [ ] **R4:** Move `output/previews/_intro_trim_7s.mp4` out of `previews/` (it's an input asset, not an output). Target: `phase1/assets/intro_trim_7s.mp4`
- [ ] **R5:** (auto-grouped above with R4)
- [ ] **R6:** Permanently delete `_staging_cleanup/` after 1-2 week observation window (contains archived pycache + exploratory probes, reversible until deletion)
- [ ] **R7:** Reclaim **~22 GB** by purging `output/normalized/` once Phase 1 style is locked — these are regenerable
- [ ] **R8:** (covered above)
- [ ] **R9:** Group `tools/*-src/` and similar vendored trees into `tools/vendored-src/`
- [ ] **R10:** Decide keep-or-delete for empty `wolfcam-configs/{cameras,cfgs}/` dirs (Phase 2 may populate; defer = keep)

Blanket approval: [ ] approve ALL · [ ] pick subset (tick individual boxes above) · [ ] discuss

### 9.3 Knowledge graph refresh cadence
Currently: manual. Proposed: auto-rebuild weekly via scheduled task as new source is cracked.
- [ ] Set up weekly cron
- [ ] Keep manual
- [ ] Trigger on git hook instead

---

## 9.4 GitHub README — follow-up decisions

README shipped in commit `93979f7` at https://github.com/Stoneface30/quake-legacy. Agent caught player-handle PII (in-world nameplates) on every render frame-grab and **deleted them before staging** — nothing unsafe was pushed. A few items need your call:

### 9.4.1 Texture hero selections (currently shown on README)
- railgun → `railgun2.glow`
- lightning → `lightning2`
- rocket → `rocketl`
- plasma → `plasma`
- shotgun → `shotgun`

Alternatives offered by the agent:
- [ ] Keep current five
- [ ] Swap railgun → `railgun3` (punchier single-hero)
- [ ] Add BFG pair (spectacular but off-brand for CA)
- [ ] Other: ___________________________________________

### 9.4.2 Render visuals on the GitHub page (currently: none, text-only)
The agent could not safely ship gameplay frames because HUD + in-world nameplates identify players. Options:
- [ ] **(a)** Render a synthetic HUD-less intro card (clean, no gameplay)
- [ ] **(b)** Take a capture with `cg_draw2d 0` + `cg_drawFriend 0` + `cg_drawNames 0` to hide HUD + nameplates — gameplay visible, no PII
- [ ] **(c)** Use PANTHEON intro card only (no gameplay, cheapest)
- [ ] Leave render section text-only for now
- [ ] Other: ___________________________________________

**Recommendation:** (b) for authenticity — Claude can produce a re-render with the draw flags stripped via WolfcamQL on a known-clean moment (no teammates visible). Needs you to pick one frag time from a Part 3 demo.

### 9.4.3 LICENSE file
No `LICENSE` exists at repo root. README claims GPL-derived. Agent recommends adding explicit `LICENSE` file with GPL-2.0 text (matches ioquake3/wolfcamql upstream).
- [ ] Add GPL-2.0 LICENSE file
- [ ] Add MIT LICENSE file (conflicts with GPL upstream — not recommended)
- [ ] Add GPL-3.0 LICENSE file
- [ ] Other: ___________________________________________

### 9.4.4 Broken doc link in README
~~README links `docs/reference/dm73-format-deep-dive.md` which is still being written by the parallel agent. Link 404s until it lands.~~ **RESOLVED 2026-04-17 09:39** — deep-dive doc landed at 1,337 lines. README link now valid. Claude will commit the new doc to GitHub in a follow-up push.

---

## 10. Things User Has Said But Not Yet Codified

These were in conversation or the Updated Plan but need to become concrete hard rules. Confirm each:

- [ ] **"T1 as filler is FORBIDDEN."** — already in CLAUDE.md ✓
- [ ] **"FL cuts are earned, not default."** — in memory ✓
- [ ] **"Frag + Effect + Music is the Golden Rule."** — proposed Rule P1-I above
- [ ] **"Every Part must extend PANTHEON intro lab outputs eventually"** — Phase 3.5 gate
- [ ] **"Full 3D intro is the endgame"** — Phase 3.5 gate
- [ ] **"We ghidra the WolfWhisperer binary"** — queued in `docs/superpowers/plans/*-deep-plan-focus-and-tracks.md` Track E
- [ ] **"Build our own .cpp demo parser"** — see §3 above, Path B

---

## 11. Things Claude Doesn't Need From You

Documented here so you know what's safe to ignore. Claude will handle autonomously:
- Parts 4-12 full renders once §1 + §5.1 + §5.2 answered
- Beat-sync integration into render pipeline
- .dm_73 format deep-dive doc (research agent running)
- Folder organization safe-moves (agent running)
- GitHub README tech-showcase + push (agent running)
- Phase 2 parser implementation (once §3 answered)
- Nickname dictionary implementation (once §6 approved)
- All 5 knowledge graph rebuilds as new source is explored
- Visual-record screenshots for every render (Rule VIS-1)

---

## How to answer this file

Edit this file directly. When Claude next reads it, any `[x]` checkbox or filled blank is treated as authoritative. If you want to discuss something first rather than commit, leave a `DISCUSS:` line under the question.
