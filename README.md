# QUAKE LEGACY
### AI-Powered Fragmovie Production System

> *Ten years of Quake Live gameplay. One AI pipeline to turn it all into cinema.*

---

## What Is This?

This project transforms a decade of competitive Quake Live demo recordings into a fully automated fragmovie production engine. The human is the creative director. The AI handles parsing, pattern recognition, camera selection, rendering, and assembly.

The Quake 3 engine is [open source](https://github.com/id-Software/Quake-III-Arena). Every `.dm_73` demo file is a perfect binary record of every game event — every kill, every rocket trajectory, every player position at 30Hz. With modern tooling and AI pattern analysis, we can find frags that no human reviewer scanning 2,000+ demos could find manually.

---

## The Vision

```
Raw .dm_73 demos
       ↓
  Demo Parser (UberDemoTools + qldemo-python)
       ↓
  Frag Database (SQLite — every kill, every weapon, every timestamp)
       ↓
  AI Pattern Engine (air shots, multi-kills, shaft accuracy, combos)
       ↓
  Camera Auto-Selector (per-map spline library, trajectory analysis)
       ↓
  WolfcamQL Batch Renderer (headless, automated, parallel)
       ↓
  FFmpeg Assembly (concat + color grade + bloom + music + slow-mo)
       ↓
  Human Review Dashboard (you are the judge)
       ↓
  YouTube-Ready Fragmovie
```

---

## Phases

### Phase 1 — Tribute Completion *(in progress)*
Complete a 12-part Quake Live Clan Arena fragmovie series using existing sorted clips.
- FFmpeg assembly pipeline: concat, color grade, bloom, music, transitions
- Human reviews each part before final export
- Output: Parts 4-12 finished and uploaded

### Phase 2 — Demo Intelligence Engine *(planned)*
Parse all demos, build a frag database, automate rendering with [WolfcamQL](https://github.com/brugal/wolfcamql).
- Parse 2,000+ `.dm_73` demo files
- Extract every kill event (`EV_OBITUARY`) with millisecond accuracy
- SQLite frag database: weapon, map, players, timestamps, kill streaks
- Batch WolfcamQL rendering: headless demo → AVI pipeline
- Human review dashboard for frag approval
- WolfWhisperer.exe reverse engineering ([Ghidra](https://github.com/NationalSecurityAgency/ghidra))

### Phase 3 — AI Cinematography Engine *(research)*
Pattern recognition on raw demo binary data. No game engine needed.
- **Air shot detection**: victim Z-velocity > threshold at frag moment
- **LG shaft tracking**: sustained lightning damage → accuracy calculation
- **Multi-kill detection**: 2+ kills within 3 seconds
- **Weapon combo chains**: weapon swap events before kill
- **Trajectory analysis**: reconstruct rocket paths, railgun beams from demo vectors
- **Auto camera selection**: per-map spline library, drama-maximizing angle picker
- **Bullet cam**: follow projectile entity through the demo
- **Slow-mo trigger**: automatic timescale 0.3 at kill moment
- **Full event ingestion**: every `svc_serverCommand`, entity event, item pickup, sound

---

## Technical Stack

| Layer | Tool |
|---|---|
| Demo parsing | [UberDemoTools](https://github.com/mightycow/uberdemotools), [qldemo-python](https://github.com/Quakecon/qldemo-python) |
| Demo rendering | [WolfcamQL](https://github.com/brugal/wolfcamql) |
| Video pipeline | [FFmpeg](https://ffmpeg.org), [ffmpeg-python](https://github.com/kkroening/ffmpeg-python), [moviepy](https://github.com/Zulko/moviepy) |
| Motion blur | [f0e/blur](https://github.com/f0e/blur) |
| Binary RE | [Ghidra](https://github.com/NationalSecurityAgency/ghidra) |
| Database | SQLite |
| Review UI | Streamlit |
| Q3 Reference | [id-Software/Quake-III-Arena](https://github.com/id-Software/Quake-III-Arena) |

---

## Demo Format — .dm_73

Quake Live protocol 73 demos. Binary packet stream:
- Huffman-compressed server-to-client messages
- `svc_gamestate`: map, player names, configstrings
- `svc_snapshot`: world state at 30Hz — positions, velocities, events
- `EV_OBITUARY` entity event = a frag. Contains killer, victim, weapon.
- Player positions as `(x, y, z)` floats every 33ms
- No game engine required to extract all of this

See `docs/research/dm73-format.md` for the full binary specification.

---

## Repository Structure

```
quake-legacy/
  phase1/          FFmpeg assembly pipeline
  phase2/          Demo parser + WolfcamQL batch renderer + review dashboard
  phase3/          AI pattern engine + auto cinematics
  tools/           All dependencies (downloaded, documented, versioned)
  wolfcam-configs/ Per-map camera spline files + recording presets
  database/        SQLite schema + migrations
  docs/
    specs/         Design documents
    research/      Technical reference (wolfcamql, dm_73, ffmpeg, Q3 engine)
```

---

## Getting Started

```bash
# Clone
git clone https://github.com/Stoneface30/quake-legacy
cd quake-legacy

# Install Python deps
pip install -r requirements.txt

# Download tools
python tools/download_tools.py

# Phase 1: assemble a Part
python phase1/assembler.py --part 4 --preview

# Phase 2: parse demos
python phase2/parser/parse_demos.py --demo-dir /path/to/demos --output database/frags.db

# Phase 2: review frags
streamlit run phase2/review/dashboard.py

# Phase 2: batch render approved frags
python phase2/renderer/batch_render.py --wolfcamql tools/wolfcamql/wolfcamql.exe
```

---

## Documentation

| Document | Description |
|---|---|
| [Design Spec](docs/specs/2026-04-16-quake-legacy-design.md) | Full 3-phase system design |
| [WolfcamQL Reference](docs/research/wolfcamql.md) | Complete cvar/command documentation |
| [dm_73 Format](docs/research/dm73-format.md) | Binary protocol specification |
| [FFmpeg Pipeline](docs/research/ffmpeg-pipeline.md) | All video production commands |
| [Q3 Engine](docs/research/q3-engine.md) | id Tech 3 architecture reference |
| [Tools](tools/README.md) | All tools, versions, sources |

---

## Philosophy

The goal is not to replace the human eye — it's to give it 10,000x more material to work with. The AI finds the candidates. The human makes the art.

---

*Built on [id Tech 3](https://github.com/id-Software/Quake-III-Arena) — open source since 2005.*
