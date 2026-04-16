# QUAKE LEGACY — Project Instructions for Claude

This file is loaded automatically every Claude Code session for this project.

## What This Project Is

AI-powered Quake Live fragmovie production system. 3 active phases + Phase 4 (public tool).
10+ years of `.dm_73` Quake Live demo recordings → automated fragmovie pipeline.

**GitHub:** https://github.com/Stoneface30/quake-legacy (PUBLIC repo)
**Local root:** G:\QUAKE_LEGACY
**User role:** Creative director, quality judge — approves everything before batch runs.

## CRITICAL: Public Repo Rules

- **NEVER commit** player names, nicknames, personal identifiers, Steam IDs
- **NEVER commit** .dm_73, .avi, .mp4, .db, .env files
- Demo player names are anonymized in all code and docs
- All gameplay analysis is statistical — no player profiles

## Source Material Locations

```
G:\QUAKE_LEGACY\
  QUAKE VIDEO\T1\Part1-12\   ← AVI clips (top tier, Parts 1-3 done)
  QUAKE VIDEO\T2\Part1-12\   ← AVI clips (tier 2)
  QUAKE VIDEO\T3\Part1-12\   ← AVI clips (tier 3)
  WOLF WHISPERER\             ← WolfWhisperer.exe + WolfcamQL + Python scripts
  FRAGMOVIE VIDEOS\           ← 3 finished tribute videos (reference quality)
  tools\                      ← all downloaded dependencies
  phase1\                     ← FFmpeg assembly pipeline
  phase2\                     ← demo parser + batch renderer
  phase3\                     ← AI cinematography engine
  database\                   ← SQLite frag database schema
  docs\                       ← design specs, research, plans
```

## Phase Status

| Phase | Status | Current Task |
|---|---|---|
| Phase 1 | 🚧 In Progress | Tool setup → clip assembly → Parts 4-12 |
| Phase 2 | 📋 Planned | Demo parsing → frag DB → WolfcamQL batch |
| Phase 3 | 🔬 Research | Pattern recognition, AI cameras, graphify |
| Phase 4 | 🌐 Vision | Public CLI tool for anyone with demos |

## Key Technical Facts (memorize these)

### WolfcamQL Automation Pattern
```
Write gamestart.cfg:
  seekclock 8:52; video avi name :demoname; at 9:05 quit
Launch: wolfcamql.exe +set fs_homepath <out_dir> +exec cap.cfg +demo demo.dm_73
```

### Frag Detection in .dm_73
```python
# In each snapshot, scan entities for:
entity.event & ~0x300 == EV_OBITUARY   # (0x300 masks the toggle bits)
# Then:
killer = entity.otherEntityNum2   # client slot 0-63
victim = entity.otherEntityNum    # client slot 0-63
weapon = entity.eventParm         # MOD_* constant
time   = snapshot.server_time     # milliseconds
```

### Key Tools
- FFmpeg binary: `G:\QUAKE_LEGACY\tools\ffmpeg\ffmpeg.exe`
- WolfcamQL: `G:\QUAKE_LEGACY\tools\wolfcamql\wolfcamql.exe` (also in WOLF WHISPERER\)
- UberDemoTools: `G:\QUAKE_LEGACY\tools\uberdemotools\UDT_json.exe`
- WolfWhisperer binary (for RE): `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfWhisperer.exe`

### Cross-Phase Learning Store
All phases write learnings to: `G:\QUAKE_LEGACY\database\knowledge.db`

## Human Review Gates (NEVER skip these)

1. **Gate P1-1:** Review clip lists before rendering (edit phase1/clip_lists/partXX.txt)
2. **Gate P1-2:** Watch 30s preview before full render
3. **Gate P1-3:** Watch full Part render before moving to next
4. **Gate P2-1:** Review parser output on 10 sample demos before full parse
5. **Gate P2-2:** Rate frags in dashboard before batch WolfcamQL render
6. **Gate P2-3:** Review 10 rendered clips before full batch
7. **Gate P3-1:** Review AI-selected frags vs human-selected — measure agreement rate

## When Starting a Session

1. Read `docs/specs/2026-04-16-quake-legacy-design.md` for full architecture
2. Check `database/knowledge.db` for cross-phase learnings (if exists)
3. Check current phase plan in `docs/superpowers/plans/`
4. Never run batch operations without human confirming at review gate
5. Never commit personal data

## Phase 4 Vision

Once the system works for this project, it becomes a public CLI:
`pip install quake-legacy` → give it demos → get a fragmovie.

Document EVERYTHING as we go. All RE findings, all binary format work, all camera math.
The community will build on this. The Q3 engine is open source — this is the gift back.
