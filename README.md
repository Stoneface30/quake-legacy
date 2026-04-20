# QUAKE LEGACY

AI-powered Quake Live fragmovie production system. 10+ years of `.dm_73` demo recordings → automated fragmovie pipeline.

## What it is

A single unified web app that IS the GUI for the CLI engine underneath. One interface for everything: video assembly, demo extraction, texture generation, 3D intro lab, engine dissection.

**Brand:** PANTHEON (gold + deep blue)
**Format:** Quake Live `.dm_73` demos → rendered fragmovie parts

## Quick Start

```bash
# Install
pip install -r requirements.txt
npm install && node build.js

# Start
cd creative_suite && uvicorn app:app --port 8765 --reload

# Open
http://localhost:8765/studio
```

## Structure

```
creative_suite/   ← The whole app (API + frontend + render engine)
  engine/         ← Render pipeline (ffmpeg assembly, beat sync, music)
  tools/          ← ffmpeg, ghidra, comfyui
  database/       ← MusicLibrary.json, frags.db
  frontend/       ← /studio (Premiere-class editor)
  api/            ← FastAPI routers
engine/           ← Quake engine source trees + RE + parser
  engines/        ← ioquake3, wolfcamql, q3mme (SHA-256 deduped)
  wolfcam/        ← WolfcamQL binary + demo staging
  parser/         ← dm73 C++17 parser (FT-1)
demos/            ← 6,465 .dm_73 files (13.19 GB, not committed)
QUAKE VIDEO/      ← T1/T2/T3 source AVIs (not committed)
output/           ← Render output (not committed)
```

## Key Rules

- Never commit `.dm_73`, `.avi`, `.mp4`, player names, Steam IDs
- All P1-* render rules in `CLAUDE.md`
- All paths relative to repo root (`G:/QUAKE_LEGACY`)

## Status

Parts 4-12 in render pipeline. `/studio` editor in active development.
