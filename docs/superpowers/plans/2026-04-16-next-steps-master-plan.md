# QUAKE LEGACY — Master Plan & Research Roadmap
**Date:** 2026-04-16  
**Status:** Active  

---

## Immediate Actions (this session / next session)

### 1. Drop Music File for Part 4
Place music in `phase1/music/part04_music.mp3`  
**Suggested:** "Bucky Don Gun" by SHFTR (5:46) — escalating energy, fits cinematic + punchy  
**Alternative:** "Jump Up Quickly - Zero Remix" (4:20) for faster cut pace  

Then re-run: `python phase1/render_part4.py --version 1`

### 2. Review Part 4 V2 (After Fix)
All fixes applied. Run V1 again with music to confirm:
- [ ] PANTHEON intro present (7s)
- [ ] Music audible
- [ ] Game audio at 55% (clearly audible under music)
- [ ] Hard cuts between clips (no cross-dissolve glitch)
- [ ] Colors punchy (contrast 1.55, sat 1.65)
- [ ] Intro uses all FL angles from Demo (101) folder

---

## Phase 1 — Remaining Work

### Part 4 All Versions
- [ ] V1 Cinematic re-render with fixes  
- [ ] V2 Punchy re-render with fixes  
- [ ] V3 Zoom Power re-render with fixes  
- [ ] V4 Hybrid Flow re-render with fixes  
- [ ] User reviews → select winning version or hybrid  
- [ ] Full 3-4 minute render (not 60s preview)  

### Parts 5-12
Same pipeline. For each:
1. Drop `part{N:02d}_music.mp3` in `phase1/music/`
2. Run `python phase1/render_part4.py --part N --version 1`
3. Human gate review → approve or adjust clip list

### Multi-Angle Stitch — All Parts
Every folder without `.avi` extension = multi-angle clip.  
`all_angles()` now handles unlimited FL clips.  
Need to verify other folders have same naming pattern:
- `Demo (194) - 150` → `Demo (194) - 150.avi` + `Demo (194FL1).avi`  
- `Demo (253) - 247` → same pattern  
Pattern confirmed working. Extend to all Parts.

---

## Phase 2 — Demo Extraction Engine

### Gate P3-0: Highlight Criteria Session (REQUIRED FIRST)
Before any demo parsing:
- [ ] User + Claude session to define: minimum airshot height, multi-kill window, weapon priority weights
- [ ] Document in `docs/specs/highlight-criteria.md`
- [ ] This gates ALL Phase 2 demo parsing

### Phase 2 Implementation Plan

**Step A: WolfcamQL cgame extension (~200 lines C)**
Files to modify:
- `wolfcam_consolecmds.c` — add `wolfcam_extract_frags <clientNum>` command
- Uses: `trap_GetGameStartTime()` → loop `trap_GetNextKiller()` → enumerate all kills
- Output: write frag JSON to a cvar, read from Python side

**Step B: Recording windows (CONFIRMED from v1 review)**
```
Pre-roll:  killTime - 8000ms  (8s before kill)
Post-roll: killTime + 5000ms  (5s after kill)
```
Critical: original 3s/2s was too short — clips were cut mid-action.

**Step C: trap_AddAt auto-schedule**
```c
trap_AddAt(killTime - 8000, NULL, va("video avi name :frag_%03d", idx));
trap_AddAt(killTime + 5000, NULL, "video avi stop");
```

**Step D: Python launcher (`phase2/extract_frags.py`)**
- Launch WolfcamQL with custom cfg
- Wait for completion, read JSON output
- Write to `database/frags.db`

**Step E: Multi-angle support**
For CA frags: record FP view first, then re-run demo with FL angles:
- FL1: slightly elevated, offset right
- FL2: from opposite team position  
- FL3: cinematic wide angle
These create the multi-angle folders that Phase 1 stitches together.

---

## Phase 3 — AI Cinematography

### Frag Scoring Formula (confirmed architecture)
```
frag_score = weapon_weight[mod]
           + 0.2 * is_airshot(killTime)
           + 0.3 * multi_kill_bonus(killTime, window=3000ms)
           + 0.1 * low_health_attacker(killTime)
           + 0.4 * ca_round_bonus(roundNumber, numKillsInRound)
```

### Weapon Priority Table
| Weapon | Weight | Reason |
|--------|--------|--------|
| MOD_RAILGUN | 0.90 | Instant kill, cinematic rail crack |
| MOD_ROCKET | 0.85 | Airshot potential, splash drama |
| MOD_LIGHTNING | 0.80 | CA specialist weapon, shaft beam |
| MOD_ROCKET_SPLASH | 0.70 | Splash kills still impressive |
| MOD_GRENADE | 0.65 | Airshot potential |
| MOD_PLASMA | 0.50 | Fast fire, multi-kill weapon |
| MOD_TELEFRAG | 1.00 | Cinematics — always a highlight |

---

## Research Roadmap (parallel with production)

### 1. Graphify Knowledge Graphs — Status
Runs already dispatched (background):
- [x] wolfcam/cgame — 1,494 nodes, 2,862 edges, 25 communities
- [x] wolfcam/game — 1,075 nodes, 2,046 edges, 27 communities
- [ ] q3a/game — collecting
- [ ] q3a/engine-core — collecting
- [ ] q3mme/cgame — collecting
- [ ] q3mme/game — collecting
- [ ] uberdemotools — collecting
- [ ] qldemo-python + WolfWhisperer — collecting

**Next batch (queue when above complete):**
- wolfcam/qcommon (44 files)
- quake3e (509 files — split by module)
- q3vm (63 files)

### 2. Q3A Asset Extraction
Q3A source code: `tools/quake-source/quake3-source/` — FULLY PRESENT  
Quake Live: `C:\Program Files (x86)\Steam\steamapps\common\Quake Live\` — INSTALLED  
Assets (pak00.pk3): at QL path — extractable for Phase 5 texture work  

Q3A game assets (pak0.pk3 from original Q3A):
- Different from QL's pak files
- Needed for original weapon models / maps
- Purchase/install separately if needed for comparison

### 3. Phase 5 — ComfyUI Texture Pipeline
ComfyUI: `E:/PersonalAI/ComfyUI/`  
Missing models:
- `4x-UltraSharp.pth` → `models/upscale_models/` (Real-ESRGAN upscaler)
- `control_v11f1e_sd15_tile.pth` → `models/controlnet/` (SD1.5 ControlNet Tile)

Pipeline: pak00.pk3 → TGA → PNG → 4x upscale → ControlNet img2img (denoise=0.35) → TGA → pk3  
Status: scripts written, models not yet downloaded.

### 4. WolfWhisperer Reverse Engineering
Binary: `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfWhisperer.exe`  
Tool: Ghidra (need to install / configure)  
Goal: map IPC commands WolfWhisperer sends to WolfcamQL  
Why: WolfWhisperer may have additional control surface we haven't found yet

### 5. Cross-Module Kill Chain Query
Target: trace the COMPLETE kill event path:
```
snapshot received → entity state change → EV_OBITUARY → CG_Obituary() 
→ frag database update → trap_GetNextKiller available
```
Requires: wolfcam/cgame graph + q3a/qcommon graph merged  
Status: waiting for all graphify runs to complete

---

## Knowledge Database Status

`database/frags.db` schema needed:
```sql
CREATE TABLE frags (
    id INTEGER PRIMARY KEY,
    demo_path TEXT NOT NULL,
    kill_time_ms INTEGER NOT NULL,
    killer_client INTEGER NOT NULL,
    victim_client INTEGER NOT NULL,
    weapon_mod INTEGER NOT NULL,
    round_number INTEGER,
    time_into_round_ms INTEGER,
    frag_score REAL,
    is_airshot BOOLEAN DEFAULT 0,
    is_multikill BOOLEAN DEFAULT 0,
    clip_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Files Modified This Session

| File | Change |
|------|--------|
| `phase1/presets/grade_tribute.json` | contrast 1.3→1.55, sat 1.25→1.65, punchy grade |
| `phase1/config.py` | game_audio_volume 0.30→0.55 |
| `phase1/pipeline.py` | Replaced xfade chain with concat (hard cuts) |
| `phase1/render_part4.py` | Added prepend_intro() call, all_angles() helper, music warning |
| `docs/reference/phase2-kill-query-architecture.md` | Recording windows: 3s/2s→8s/5s |

---

## GitHub Sync Checklist
- [ ] Commit all phase1 fixes with message: "fix: Part4 v1 review — intro, audio, grade, transitions, multi-angle"
- [ ] Update docs/reference/ with kill-query architecture  
- [ ] Push to origin (public repo — verify no player names in commits)
- [ ] Tag milestone: `v0.1-phase1-fixes`
