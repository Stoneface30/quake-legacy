# Foundation: Folder Restructure + Cleanup + Rules Wash

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the multi-phase folder tree into one minimal structure, eliminate dead code, and rewrite all rules/docs to match the new layout.

**Architecture:** Git-mv everything into `creative_suite/` (app code) and `engine/` (Quake engine work). Fix all broken imports. Rewrite CLAUDE.md, Vault/learnings.md, memory files, and README from extracted knowledge. Delete all session-artifact .md files and the entire old docs/ tree after extraction.

**Tech Stack:** bash (git mv, rm), Python import fixes, Markdown rewrites.

**IMPORTANT — do these tasks in order.** Each task assumes the previous completed and tests pass.

---

## File Map

```
CREATED
  creative_suite/engine/          ← git mv phase1/ here
  creative_suite/tools/           ← git mv tools/ here
  creative_suite/database/        ← git mv database/ here
  creative_suite/scripts/         ← git mv scripts/ here
  creative_suite/storage/         ← git mv storage/ here
  creative_suite/tests/phase1/    ← git mv tests/ here (merges with existing creative_suite/tests/)
  engine/                         ← git mv game-dissection/ + WOLF WHISPERER content
  engine/wolfcam/                 ← WolfcamQL fully ingested
  docs/reference/                 ← new minimal docs (5 files, replaces ~120)
  CLAUDE.md                       ← full rewrite
  README.md                       ← full rewrite

DELETED
  phase35/
  WOLF WHISPERER/ (whole folder after ingestion)
  phase5/02_processed/ 03_tga/ 04_pk3/
  docs/ (entire tree, after extraction)
  HUMAN-QUESTIONS.md, NEXT_SESSION.md, OVERNIGHT_REPORT.md, SPLIT1_USER_CHECKLIST.md
  game-dissection/ (renamed to engine/)

MODIFIED
  creative_suite/config.py               ← update PHASE1_ROOT path
  creative_suite/api/phase1.py           ← update subprocess path
  creative_suite/engine/config.py        ← update self-referencing paths
  creative_suite/engine/clip_list.py     ← DRY: import from creative_suite.clips.parser
  creative_suite/engine/render_part_v6.py ← update relative import paths
  Vault/learnings.md                     ← full wash
  .claude/projects/G--QUAKE-LEGACY/memory/ ← full rewrite
```

---

## Task 1: Extract knowledge before any deletion

**Files:**
- Create: `docs/reference/dm73-format.md`
- Create: `docs/reference/wolfcam-commands.md` (copy, keep as-is)
- Create: `docs/reference/highlight-criteria.md`
- Create: `docs/reference/audio-rules.md`
- Create: `docs/reference/open-items.md`

- [ ] **Step 1: Distill dm73 format spec**

Read `docs/reference/dm73-format-deep-dive.md` and extract only the binary format tables, packet types, and snapshot structure. Strip all session notes, investigation logs, and "TODO" sections. Write to `docs/reference/dm73-format.md`. Target: under 300 lines.

- [ ] **Step 2: Copy wolfcam-commands.md as-is**

```bash
cp "G:/QUAKE_LEGACY/docs/reference/wolfcam-commands.md" \
   "G:/QUAKE_LEGACY/docs/reference/wolfcam-commands-new.md"
```

It's a clean cvar/command inventory — keep it. Rename to `wolfcam-commands.md` in the final docs/.

- [ ] **Step 3: Distill highlight criteria**

Read `docs/specs/highlight-criteria-v2.md`. Copy the locked v2 criteria table (weapon weights, multi-kill window, airshot definition) into `docs/reference/highlight-criteria.md`. Strip planning notes. Target: under 100 lines.

- [ ] **Step 4: Distill audio rules**

Extract P1-G, P1-R, P1-AA, P1-Z, P1-Z from `CLAUDE.md` into `docs/reference/audio-rules.md`:

```markdown
# Audio Rules Reference

## Music Volume (P1-G v5)
- music_volume = 0.20
- fadein_s = 1.5
- ebur128 gate: music ≤ −12 LU below game peak → else FAILED_LEVEL_GATE

## Three-Track Contract (P1-R v2)
- Every Part: intro_music + main_music + outro_music
- Continuous coverage mandatory — silence gaps = render failure
- All tracks play FULL; last may truncate at phrase boundary only

## Music Stitcher (P1-AA v2)
- Video body length is truth
- Queue N full tracks until sum(duration) ≥ body_duration
- Last track truncates at PHRASE boundary (never mid-bar)
- Seams = DJ beat+phrase match at 8/16-bar boundaries
- Sidechain-duck music ~6 dB on recognized game events

## Action Peak Recognition (P1-Z v2)
- Events: player_death, rocket_impact, rail_fire, grenade_explode, LG_hit
- Template match against creative_suite/engine/sound_templates/
- Minimum confidence 0.55 to trigger effect
- Fallback: loudest onset + tag RECOGNITION_FAILED
```

- [ ] **Step 5: Extract open items from root .md files**

Read `HUMAN-QUESTIONS.md`, `NEXT_SESSION.md`, `OVERNIGHT_REPORT.md`, `SPLIT1_USER_CHECKLIST.md`. Write still-blocking items to `docs/reference/open-items.md`:

```markdown
# Open Items (extracted 2026-04-20)

## Blocking for batch render
- Part 3 style lock: A/B/C/V5 hybrid — user decision needed before Parts 4-12 full batch
- Game audio level: 0.55 vs 0.75 A/B test on next render pass (Config.game_audio_volume)

## Parts review status
- Parts 4/5/6 rendered, user review pending (6-axis: chain flow, beat, game audio, multi-angle, intro, grade)
- Parts 7-12 full renders unlock after Part 4 approved
- Parts 6/7 crash root cause: normalize cache corruption — fix before next batch
- Parts 8-12: clip_lists/partNN_styleb.txt missing — need creation

## Demo corpus
- 6,465 .dm_73 files in demos/ (13.19 GB)
- 948 in engine/wolfcam/wolfcam-ql/demos/ (some <150KB action-extracts)
```

- [ ] **Step 6: Commit extracted docs**

```bash
cd G:/QUAKE_LEGACY
git add docs/reference/
git commit -m "docs: extract reference knowledge before cleanup

Distilled dm73 format spec, wolfcam commands, highlight criteria,
audio rules, and open items from the old docs tree before deletion.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Move phase1/ → creative_suite/engine/

**Files:**
- Move: `phase1/` → `creative_suite/engine/`
- Modify: `creative_suite/config.py`
- Modify: `creative_suite/api/phase1.py`

- [ ] **Step 1: Git move the directory**

```bash
cd G:/QUAKE_LEGACY
git mv phase1 creative_suite/engine
```

- [ ] **Step 2: Update PHASE1_ROOT in creative_suite/config.py**

Find the line in `creative_suite/config.py` that sets the phase1 root path. Change it:

```python
# Before
PHASE1_ROOT = Path(__file__).parent.parent / "phase1"

# After
PHASE1_ROOT = Path(__file__).parent / "engine"
```

If it's defined differently (e.g., hardcoded string), update to:
```python
PHASE1_ROOT = Path("G:/QUAKE_LEGACY/creative_suite/engine")
```

- [ ] **Step 3: Update subprocess call in creative_suite/api/phase1.py**

Find any line that calls `render_part_v6.py` as a subprocess. Update the path:

```python
# Before (example pattern)
cmd = [sys.executable, "phase1/render_part_v6.py", ...]

# After
cmd = [sys.executable, "creative_suite/engine/render_part_v6.py", ...]
```

Also update any other references to `phase1/` paths in this file (clip_lists, music, sound_templates):
```python
# Before
clip_lists_dir = Path("phase1/clip_lists")
music_dir = Path("phase1/music")

# After
clip_lists_dir = Path("creative_suite/engine/clip_lists")
music_dir = Path("creative_suite/engine/music")
```

- [ ] **Step 4: Update internal paths in creative_suite/engine/config.py**

Open `creative_suite/engine/config.py`. Find any `Path("phase1/...")` references and update:

```python
# Pattern to find and fix:
# "phase1/" → "creative_suite/engine/"
# Path(__file__).parent → already correct (file is now in creative_suite/engine/)
```

The `Path(__file__).parent` references will automatically resolve correctly after the move. Fix only hardcoded string paths.

- [ ] **Step 5: Run tests to check nothing broke**

```bash
cd G:/QUAKE_LEGACY
python -m pytest creative_suite/tests/ -x -q 2>&1 | head -50
```

Expected: same pass count as before (132 tests). If failures appear, read the error and fix the import path.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: move phase1/ into creative_suite/engine/

Phase 1 render pipeline moves inside the app package. All paths
updated. DRY fix for clip parser import in next task.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: DRY fix — single clip parser

**Files:**
- Modify: `creative_suite/engine/clip_list.py`

- [ ] **Step 1: Check both parsers are identical**

```bash
python3 -c "
import ast, sys

with open('creative_suite/engine/clip_list.py') as f:
    engine_src = f.read()
with open('creative_suite/clips/parser.py') as f:
    clips_src = f.read()

# Find parse_clip_entry in each
for name, src in [('engine', engine_src), ('clips', clips_src)]:
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'parse_clip_entry':
            print(f'{name}: parse_clip_entry found at line {node.lineno}')
"
```

- [ ] **Step 2: Remove the duplicate definition from engine/clip_list.py**

In `creative_suite/engine/clip_list.py`, find the `parse_clip_entry` function definition. Remove it and add an import at the top:

```python
# Add at top of creative_suite/engine/clip_list.py
from creative_suite.clips.parser import parse_clip_entry  # single source of truth
```

Remove the local `def parse_clip_entry(...)` block entirely.

- [ ] **Step 3: Verify import resolves**

```bash
cd G:/QUAKE_LEGACY
python3 -c "from creative_suite.engine.clip_list import parse_clip_entry; print('OK')"
```

Expected output: `OK`

- [ ] **Step 4: Run tests**

```bash
python -m pytest creative_suite/tests/ -x -q -k "clip" 2>&1 | head -30
```

Expected: all clip-related tests pass.

- [ ] **Step 5: Commit**

```bash
git add creative_suite/engine/clip_list.py
git commit -m "refactor: DRY clip parser — engine imports from clips.parser

Removes duplicate parse_clip_entry from engine/clip_list.py.
creative_suite/clips/parser.py is now the single source of truth.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Move tools/, database/, scripts/, storage/, tests/

**Files:**
- Move: `tools/` → `creative_suite/tools/`
- Move: `database/` → `creative_suite/database/`
- Move: `scripts/` → `creative_suite/scripts/`
- Move: `storage/` → `creative_suite/storage/`
- Move: `tests/` phase1 subfolder → merge into `creative_suite/tests/phase1/`

- [ ] **Step 1: Move all four data/utility folders**

```bash
cd G:/QUAKE_LEGACY
git mv tools creative_suite/tools
git mv database creative_suite/database
git mv scripts creative_suite/scripts
git mv storage creative_suite/storage
```

- [ ] **Step 2: Merge root tests/ into creative_suite/tests/**

```bash
# Move phase1 test files into creative_suite/tests/phase1/
mkdir -p creative_suite/tests/phase1
git mv tests/phase1/* creative_suite/tests/phase1/ 2>/dev/null || git mv tests/* creative_suite/tests/phase1/
# Remove now-empty root tests/
rmdir tests 2>/dev/null || git rm -r tests/
```

- [ ] **Step 3: Update tools path in creative_suite/config.py**

```python
# Before
FFMPEG_BIN = Path("tools/ffmpeg/ffmpeg.exe")
FFPROBE_BIN = Path("tools/ffmpeg/ffprobe.exe")

# After
FFMPEG_BIN = Path("creative_suite/tools/ffmpeg/ffmpeg.exe")
FFPROBE_BIN = Path("creative_suite/tools/ffmpeg/ffprobe.exe")
```

- [ ] **Step 4: Update database path in creative_suite/db/migrate.py**

```python
# Before
SCHEMA_PATH = Path(__file__).parent.parent.parent / "database" / "schema.sql"

# After
SCHEMA_PATH = Path(__file__).parent.parent.parent / "creative_suite" / "database" / "schema.sql"
```

Or more robustly:
```python
SCHEMA_PATH = Path(__file__).parent.parent / "database" / "schema.sql"
# (since migrate.py is in creative_suite/db/, parent.parent = creative_suite/)
```

- [ ] **Step 5: Update storage path in creative_suite/config.py**

```python
# Before
STORAGE_ROOT = Path("storage")

# After
STORAGE_ROOT = Path("creative_suite/storage")
```

- [ ] **Step 6: Update conftest.py in creative_suite/tests/phase1/ if needed**

Open `creative_suite/tests/phase1/conftest.py`. Fix any `Path("phase1/...")` references:
```python
# Before
PHASE1_DIR = Path("phase1")

# After
PHASE1_DIR = Path("creative_suite/engine")
```

- [ ] **Step 7: Run full test suite**

```bash
cd G:/QUAKE_LEGACY
python -m pytest creative_suite/tests/ -x -q 2>&1 | tail -20
```

Expected: 132 tests pass. Fix any path errors before continuing.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor: move tools/ database/ scripts/ storage/ tests/ into creative_suite/

All utility and data folders now live inside the app package.
Path references updated throughout config and db/migrate.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Rename game-dissection/ → engine/ + ingest WOLF WHISPERER

**Files:**
- Rename: `game-dissection/` → `engine/`
- Move: `WOLF WHISPERER/WolfcamQL/` → `engine/wolfcam/`
- Delete: `WOLF WHISPERER/Backup/`, `WOLF WHISPERER/*.rar`, `WOLF WHISPERER/*.7z`
- Delete: entire `WOLF WHISPERER/` folder after ingestion

- [ ] **Step 1: Rename game-dissection to engine**

```bash
cd G:/QUAKE_LEGACY
git mv game-dissection engine
```

- [ ] **Step 2: Move WolfcamQL into engine/wolfcam/**

```bash
mkdir -p engine/wolfcam
git mv "WOLF WHISPERER/WolfcamQL" engine/wolfcam/wolfcam-ql
```

- [ ] **Step 3: Delete archives and backups (irreversible — confirm first)**

```bash
# Verify what we're about to delete
ls "WOLF WHISPERER/"

# Delete backup folders and archives
rm -rf "WOLF WHISPERER/Backup"
find "WOLF WHISPERER/" -name "*.rar" -delete
find "WOLF WHISPERER/" -name "*.7z" -delete

# Stage deletions
git add -A "WOLF WHISPERER/"
```

- [ ] **Step 4: Remove now-empty WOLF WHISPERER folder**

```bash
# Check nothing important remains
ls -la "WOLF WHISPERER/"
# If empty or only git-tracked deletions:
git rm -rf "WOLF WHISPERER/"
rmdir "WOLF WHISPERER/" 2>/dev/null
```

- [ ] **Step 5: Update wolfcam binary path in creative_suite/capture/gamestart.py**

```python
# Before
WOLFCAM_EXE = Path("WOLF WHISPERER/WolfcamQL/wolfcam-ql/wolfcamql.exe")

# After
WOLFCAM_EXE = Path("engine/wolfcam/wolfcam-ql/wolfcamql.exe")
```

Also update in `creative_suite/api/capture.py` if referenced there.

- [ ] **Step 6: Verify wolfcam path resolves**

```bash
python3 -c "
from pathlib import Path
p = Path('engine/wolfcam/wolfcam-ql/wolfcamql.exe')
print('exists:', p.exists())
print('path:', p.resolve())
"
```

Expected: path exists (the exe is there).

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: rename game-dissection/ to engine/, ingest WOLF WHISPERER

WolfcamQL fully ingested into engine/wolfcam/. Backup archives deleted.
Wolfcam binary path updated in capture module.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Delete dead folders + move phase5 assets

**Files:**
- Delete: `phase35/`
- Delete: `phase5/02_processed/`, `phase5/03_tga/`, `phase5/04_pk3/`
- Move: `phase5/01_png/` → `creative_suite/comfy/assets/phase5_png/`
- Delete: `phase5/` (now empty)

- [ ] **Step 1: Delete phase35 (empty blueprint)**

```bash
cd G:/QUAKE_LEGACY
git rm -rf phase35/
```

- [ ] **Step 2: Move phase5 PNG assets**

```bash
mkdir -p creative_suite/comfy/assets/phase5_png
git mv phase5/01_png/* creative_suite/comfy/assets/phase5_png/ 2>/dev/null || \
  cp -r phase5/01_png/. creative_suite/comfy/assets/phase5_png/
```

- [ ] **Step 3: Delete empty phase5 pipeline dirs**

```bash
git rm -rf phase5/02_processed phase5/03_tga phase5/04_pk3
rmdir phase5/ 2>/dev/null || git rm -rf phase5/
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "cleanup: delete phase35/, phase5/ empty dirs, move PNG assets to comfy

phase35 was an empty blueprint with no code.
phase5 pipeline dirs were empty; PNG source assets preserved in comfy/assets/.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Delete old docs/ tree

- [ ] **Step 1: Verify reference docs were extracted (Task 1)**

```bash
ls docs/reference/
# Expected: dm73-format.md, wolfcam-commands.md, highlight-criteria.md,
#           audio-rules.md, open-items.md
```

- [ ] **Step 2: Delete everything in docs/ except reference/ and superpowers/**

```bash
cd G:/QUAKE_LEGACY/docs
# Keep: reference/, superpowers/plans/, superpowers/specs/
# Delete: design/, handoff/, research/, reviews/, _archive/, visual-record/, INDEX.md
git rm -rf design/ handoff/ research/ reviews/ _archive/ visual-record/ INDEX.md 2>/dev/null
```

- [ ] **Step 3: Delete root-level session artifact .md files**

```bash
cd G:/QUAKE_LEGACY
git rm HUMAN-QUESTIONS.md NEXT_SESSION.md OVERNIGHT_REPORT.md SPLIT1_USER_CHECKLIST.md
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "cleanup: delete old docs/ tree and session artifact .md files

Useful knowledge extracted to docs/reference/ (5 files).
Specs and plans in docs/superpowers/ preserved.
Session artifacts (HUMAN-QUESTIONS, NEXT_SESSION, etc.) deleted.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Rewrite CLAUDE.md

**Files:**
- Rewrite: `CLAUDE.md`

- [ ] **Step 1: Write the new CLAUDE.md**

Replace the entire file with the following (update all paths to new structure):

```markdown
# QUAKE LEGACY — Project Rules

**Project:** AI-powered Quake Live fragmovie production. One interface: web app IS the GUI.
**Brand:** PANTHEON (clan/aesthetic). **Repo:** https://github.com/Stoneface30/quake-legacy
**Root:** G:\QUAKE_LEGACY  |  **App:** creative_suite/  |  **Engine work:** engine/

---

## Structure

\`\`\`
creative_suite/          ← The whole app (FastAPI + web UI)
  engine/                ← Render pipeline (formerly phase1/)
  tools/                 ← FFmpeg, ComfyUI, Ghidra binaries
  database/              ← SQLite schema + MusicLibrary.json
  scripts/               ← QA batch utilities
  storage/               ← Editor SQLite + thumbnails
  tests/                 ← All test suites
engine/                  ← Quake engine work + RE (formerly game-dissection/)
  wolfcam/               ← WolfcamQL fully ingested
  engines/               ← Source trees (ioquake3, q3mme, etc.)
  parser/                ← dm73 parser (C++17)
demos/                   ← 13GB .dm_73 corpus
QUAKE VIDEO/             ← T1/T2/T3 source AVIs
output/                  ← Render output
Vault/                   ← Obsidian memory
\`\`\`

---

## Human Review Gates (NEVER skip)

1. Watch 30s preview before full render
2. Watch full Part render before moving to next
3. User approves all Parts before batch continues
4. Parts 4/5/6 review pending — Parts 7-12 unlock after Part 4 approved

---

## Audio Rules

**P1-G** Music volume 0.20. Fadein 1.5s. ebur128 gate: music ≤ −12 LU below game peak.
**P1-L** FP clips: head=0, tail=0. FL clips: head=1.0s, tail=2.0s. Min playable: 2.0s.
**P1-H** 0.40s seam xfades between body chunks. No fades ≥0.8s.
**P1-R** Three tracks per Part: intro + main + outro. Continuous coverage mandatory.
**P1-AA** Video body length = truth. Beat+phrase-matched DJ mix. No mid-song cuts.
**P1-Z** Action peak = recognized game event (confidence ≥0.55). Template: engine/sound_templates/.
**P1-CC** Flow planner uses SECTION SHAPE to pick clips, not tier alone.
**P1-S** Beat-sync shifts cut TIMING only, never clip duration.
**P1-I** Golden rule: frag + effect + music must align.

---

## Clip + Tier Rules

**P1-A** Every Part combines T1+T2+T3. T1=elite peaks (save for climax). T2=main meal (≥70%). T3=filler/cinematic.
**P1-K** FP is spine. At most ONE FL slow-motion contrast (0.5×) per frag. Window: FP 0-40% | FL 40-65% | FP 65-100%.
**P1-P** Clips play full post-trim duration. No sub-clip fragments.
**P1-Q** Speed effects apply to ±0.8s window around action peak only. Never whole clip.

---

## Render Pipeline Rules

**P1-BB** Split video/audio graphs. Intermediate audio = PCM WAV. CFR ingest (-vsync cfr -r 60).
  Ship gate: `output/partNN_sync_audit.json` max_drift_ms ≤ 40.
**P1-J** Final render: CRF 15-17, preset slow/veryslow, x264 High Profile 1920×1080 60fps.
**P1-N** Every Part opens: [PANTHEON 5s] + [Title card 8s] + [Content]. Hard cut in.
**P1-C** PANTHEON intro = `FRAGMOVIE VIDEOS/IntroPart2.mp4` first 5s, always prepend.

---

## Cinema Suite Rules

**CS-1** Render queue depth=1. Second submit → HTTP 409. No parallel renders.
**CS-2** Mock env vars: CS_REBUILD_MOCK=1, CS_PREVIEW_MOCK=1, CS_ENGINE_MOCK=1.
**CS-3** output/.git is auto-managed by _git_flow.py. User never commits there.
**CS-4** Every subprocess (wolfcam, ffmpeg) wrapped: terminate→wait(3s)→kill→wait.
**CS-5** Cfg injection guard: reject `;` and `\n` in demo_name, seek_clock, quit_at.
**CS-6** Render hook seam offsets are bounds-checked. Never mutate clip durations.

---

## Engine Rules

**ENG-1** Asset source of truth = Steam paks (C:\Program Files (x86)\Steam\...\pak00.pk3).
**ENG-2** Style pack pk3s MUST be named `zzz_*.pk3`.
**ENG-3** Pack testing requires `+set sv_pure 0`.
**ENG-4** Steam pak files are read-only. Never modify.

---

## npm / Dependency Security

Every npm install requires ALL: License ∈ {MIT,BSD-2,BSD-3,Apache-2.0,ISC} · npm audit clean ·
Snyk clean · pinned exact version · no network at build time · >1k stars or >3 years maintained.
**History:** Near-miss with vercel + litellm supply chain. Non-negotiable.

---

## Open Items (blocking)

- Part 3 style lock: A/B/C/V5 hybrid — needed before Parts 4-12 batch render
- Game audio level: Config.game_audio_volume A/B test (0.55 vs 0.75)
- Parts 6/7 crash: normalize cache corruption — fix before next batch
- Parts 8-12: create clip_lists/partNN_styleb.txt

---

## Key Paths

\`\`\`
FFmpeg:      creative_suite/tools/ffmpeg/ffmpeg.exe
WolfcamQL:  engine/wolfcam/wolfcam-ql/wolfcamql.exe
PANTHEON:   FRAGMOVIE VIDEOS/IntroPart2.mp4
Render:     creative_suite/engine/render_part_v6.py
Schema:     creative_suite/database/schema.sql
Music:      creative_suite/engine/music/
Clip lists: creative_suite/engine/clip_lists/
Sound tmpl: creative_suite/engine/sound_templates/
Design spec: docs/superpowers/specs/2026-04-20-quake-legacy-unified-design.md
\`\`\`
```

- [ ] **Step 2: Commit**

```bash
cd G:/QUAKE_LEGACY
git add CLAUDE.md
git commit -m "docs: rewrite CLAUDE.md for unified structure

No phase numbers. All paths updated to new layout.
Rules preserved (P1-*, CS-*, ENG-*). Session artifacts removed.
Open blocking items retained.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 9: Rewrite README.md

**Files:**
- Rewrite: `README.md`

- [ ] **Step 1: Write new README**

```markdown
# QUAKE LEGACY

AI-powered Quake Live fragmovie production system.
10+ years of `.dm_73` recordings → automated fragmovie pipeline.

**One interface:** the web app IS the control surface. No manual CLI needed.

## Quick Start

\`\`\`bash
cd creative_suite
pip install -r requirements.txt
python -m creative_suite
# Open http://localhost:8765
\`\`\`

## Structure

\`\`\`
creative_suite/    Web app + render engine (FastAPI, Python)
  engine/          FFmpeg pipeline (Parts 1-12 assembly)
  tools/           FFmpeg, ComfyUI, Ghidra binaries
  database/        SQLite schema + music library
  storage/         Editor state + thumbnails
  tests/           All test suites (132 tests)
engine/            Quake engine work + reverse engineering
  wolfcam/         WolfcamQL demo renderer (ingested)
  engines/         Source trees for engine assimilation
  parser/          .dm_73 binary parser (C++17)
demos/             6,465 .dm_73 demo files (13 GB)
QUAKE VIDEO/       T1/T2/T3 source AVI clips
output/            Render output
\`\`\`

## Web Routes

| Route | Purpose |
|---|---|
| `/studio` | Main editor — timeline, preview, beat match, effects |
| `/annotate` | Mark moments in clips for AI training |
| `/creative` | Texture factory (ComfyUI + pk3 builder) |

## Source Material

- **6,465** `.dm_73` demo files (13.19 GB)
- **~720** source AVI clips across T1/T2/T3 tiers, Parts 4-12
- **1,206** music tracks in library
- **PANTHEON** intro: `FRAGMOVIE VIDEOS/IntroPart2.mp4` (first 5s)

## License

Private — QUAKE LEGACY fragmovie system by Tr4sH.
Engine work references GPL-2.0 ioquake3 source.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README for unified interface vision

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 10: Wash Vault/learnings.md + rewrite memory files

**Files:**
- Rewrite: `Vault/learnings.md`
- Rewrite: `.claude/projects/G--QUAKE-LEGACY/memory/MEMORY.md`
- Rewrite: `.claude/projects/G--QUAKE-LEGACY/memory/project_context.md`
- Rewrite: `.claude/projects/G--QUAKE-LEGACY/memory/DOMAIN_phase1_pipeline.md`
  → rename to `DOMAIN_render_engine.md`

- [ ] **Step 1: Read current Vault/learnings.md and identify stale L-rules**

Open `Vault/learnings.md`. For each L-rule, classify:
- **KEEP** if it describes a reusable pattern (MOCK_ISOLATION, API_CONTRACT, PLATFORM_QUIRK, ASYNC_LIFECYCLE)
- **WASH** if it describes a fixed bug, a session observation, or a path that no longer exists

Rules to wash (patterns that referenced old paths or fixed bugs):
- Any L-rule referencing `phase1/` path directly (path changed)
- Any L-rule about a specific ffmpeg crash that was one-time (fixed)
- Any L-rule duplicated by another (same pattern caught twice)

- [ ] **Step 2: Rewrite Vault/learnings.md**

Keep only reusable, path-agnostic rules. Format:

```markdown
# QUAKE LEGACY — Learnings

*Append-only ledger. Washed 2026-04-20 — removed session-specific and path-specific rules.*

## PLATFORM_QUIRK

### L-rule: ffmpeg partial muxer hint (L156)
**Rule:** When writing to .partial files, always pass `-f mp4` explicitly.
**Why:** ffmpeg infers container from extension; `.partial` has no extension mapping.
**How:** `ffmpeg ... -f mp4 output.partial && mv output.partial output.mp4`

### L-rule: atomic writes prevent corruption (L154)
**Rule:** Write renders to `.partial` then `os.replace()` to final path.
**Why:** Interrupted writes leave corrupt files that appear complete.
**Apply:** Any file write that takes >1s should use partial→replace pattern.

## WORKFLOW

### L-rule: verify disk reality before batch (L159)
**Rule:** Before any batch operation, verify actual files on disk match expectations.
**Why:** References to files from previous sessions may no longer exist.
**Apply:** Run `ls output/` or equivalent before scheduling batch renders.

### L-rule: research is not shipping (L158)
**Rule:** A research spike does not count as progress toward a deliverable.
**Why:** Sessions can fill with research and produce zero shipped code.
**Apply:** At session start, identify ONE thing to ship. Research serves shipping.

### L-rule: no re-reviewing already-reviewed work (L157)
**Rule:** If user confirmed work is done, do not re-examine it in a new session.
**Why:** Wastes session budget on settled decisions.
**Apply:** Read NEXT_SESSION.md / handoff notes before doing anything.

## API_CONTRACT

### L-rule: CFR ingest prevents timeline drift (P1-BB)
**Rule:** Always force CFR on AVI ingest: `-vsync cfr -r 60` before any filter.
**Why:** VFR input + xfade chain compounds into seconds of AV drift over 30+ chunks.
**Apply:** Every ffmpeg command that ingests source AVIs must include these flags.

### L-rule: PCM WAV intermediate prevents AAC priming delay
**Rule:** Intermediate chunk audio must be PCM WAV, not AAC.
**Why:** AAC encoding adds ~1024-sample priming delay per chunk; 30 chunks = ~700ms drift.
**Apply:** `-acodec pcm_s16le` on all intermediate files; AAC only on final output.
```

- [ ] **Step 3: Rewrite project_context.md memory file**

Open `.claude/projects/G--QUAKE-LEGACY/memory/project_context.md` and rewrite with new structure:

```markdown
---
name: Project Context
description: Paths, corpus sizes, tool locations, phase status for QUAKE LEGACY
type: project
---

## Structure (2026-04-20 post-restructure)

- App: G:\QUAKE_LEGACY\creative_suite\
- Render engine: G:\QUAKE_LEGACY\creative_suite\engine\ (formerly phase1/)
- Quake engine work: G:\QUAKE_LEGACY\engine\ (formerly game-dissection/)
- Demos: G:\QUAKE_LEGACY\demos\ (6,465 files, 13.19 GB)
- Source AVIs: G:\QUAKE_LEGACY\QUAKE VIDEO\ (T1/T2/T3, Parts 4-12)
- Output: G:\QUAKE_LEGACY\output\ (empty — cleared 2026-04-20)

## Tool Paths (post-move)
- FFmpeg: creative_suite/tools/ffmpeg/ffmpeg.exe
- WolfcamQL: engine/wolfcam/wolfcam-ql/wolfcamql.exe
- ComfyUI: creative_suite/tools/comfyui/

## Status
- Parts 4/5 rendered and reviewed. Part 6 crashed.
- /studio UI wiring in progress (Plan 2).
- Engine assimilation in progress (Plan 3).
- All phases collapsed into one interface.

**Why:** Project restructured 2026-04-20 from 5 phases to single unified interface.
**How to apply:** Use these paths in all code. No references to old phase1/, game-dissection/.
```

- [ ] **Step 4: Rename DOMAIN_phase1_pipeline.md → DOMAIN_render_engine.md**

```bash
cd "C:/Users/Stoneface/.claude/projects/G--QUAKE-LEGACY/memory"
mv DOMAIN_phase1_pipeline.md DOMAIN_render_engine.md
```

Update its frontmatter name field and all references to "phase1/" → "creative_suite/engine/".

- [ ] **Step 5: Update MEMORY.md index**

Open `.claude/projects/G--QUAKE-LEGACY/memory/MEMORY.md`. Update all file references:
- `DOMAIN_phase1_pipeline.md` → `DOMAIN_render_engine.md`
- Any path references: `phase1/` → `creative_suite/engine/`
- Remove Tier A+ "LATEST LESSONS" section (those L-rules are now in learnings.md)
- Update "Updated:" date to 2026-04-20

- [ ] **Step 6: Run full test suite to confirm clean state**

```bash
cd G:/QUAKE_LEGACY
python -m pytest creative_suite/tests/ -q 2>&1 | tail -10
```

Expected: 132 tests pass. Zero failures.

- [ ] **Step 7: Final commit**

```bash
cd G:/QUAKE_LEGACY
git add -A
git commit -m "chore: restructure complete — unified folder layout

All utility folders inside creative_suite/. game-dissection renamed
to engine/. WOLF WHISPERER ingested. Dead folders deleted.
CLAUDE.md, README, learnings.md, memory files all rewritten.
132 tests passing.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Verification

After all tasks complete, the root should look like:

```
QUAKE_LEGACY/
  creative_suite/   engine/   demos/   QUAKE VIDEO/
  output/   Vault/   docs/   CLAUDE.md   README.md
  .claude/   .git/   .gitignore
```

Run:
```bash
ls G:/QUAKE_LEGACY/
# Should NOT see: phase1/ phase35/ phase5/ tools/ database/ scripts/
#                 storage/ tests/ game-dissection/ WOLF WHISPERER/
python -m pytest creative_suite/tests/ -q
# Should see: 132 passed
```
