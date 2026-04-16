# QUAKE LEGACY — AI Fragmovie Production System
## Design Specification v1.0 — 2026-04-16

---

## Vision

Transform 10 years of Quake Live competitive gameplay recordings into a fully automated, AI-powered fragmovie production engine. The human remains the creative director and quality judge. The AI handles parsing, pattern recognition, camera selection, rendering, and assembly.

> "The Q3 engine is open source. Every demo is a perfect binary record of every game event. With AI pattern matching on that data, you can find frags that you never knew were perfect."

---

## Project Structure

```
quake-legacy/
  README.md                   ← vision, quickstart, phase roadmap
  docs/
    specs/                    ← design documents (this file)
    research/                 ← technical reference documents
  phase1/                     ← FFmpeg assembly pipeline
    assembler.py              ← main Phase 1 orchestrator
    clip_lists/               ← per-Part clip order files
    presets/                  ← color grade, effect presets
  phase2/
    parser/                   ← demo parsing (UberDemoTools wrapper)
    renderer/                 ← WolfcamQL batch automation
    database/                 ← SQLite frag DB + schema
    review/                   ← human review dashboard
  phase3/
    patterns/                 ← LG accuracy, multi-kill, aerial detection
    cinematics/               ← auto camera selection system
    events/                   ← full game event ingestion
    graph/                    ← knowledge graph (graphify)
  tools/
    ffmpeg/                   ← FFmpeg binary (latest)
    uberdemotools/            ← UDT binary + docs
    qldemo-python/            ← Python demo parser
    blur/                     ← f0e/blur motion blur tool
    wolfcamql/                ← WolfcamQL latest build
    ghidra/                   ← Ghidra for WolfWhisperer RE
  wolfcam-configs/
    cameras/                  ← per-map camera spline files
    cfgs/                     ← recording config presets
  database/
    schema.sql                ← frag DB schema
    frags.db                  ← populated frag database (gitignored)
```

---

## Phase 1 — Tribute Completion

### Goal
Assemble Parts 4-12 as finished YouTube-ready MP4 videos using existing AVI clips.

### Input
- `G:\QUAKE_LEGACY\QUAKE VIDEO\T1\Part4-12\` — AVI clips (top tier)
- Clip order lists per Part (human-curated or alphabetical as baseline)
- Music tracks (user-selected per Part)

### Output
- `output/Part4.mp4` through `output/Part12.mp4`
- YouTube-ready: H.264 High Profile, 1080p60, AAC 320k

### Pipeline

```
Phase 1 Pipeline:
  1. Load clip list for Part N
  2. Normalize all AVIs → CFR 60fps 1920x1080
  3. Concat all clips
  4. Apply color grade:
     - contrast: 1.4, saturation: 1.7, brightness: 0.0
     - bloom: gblur(sigma=18) + screen blend (opacity 0.3)
     - optional: warm LUT
  5. Add transitions (cross-fade 0.3s between clips)
  6. Mix music track (fade in 2s, fade out 3s)
  7. Add intro sequence (reuse IntroPart2.mp4 style)
  8. Export: CRF 17, preset slow, pix_fmt yuv420p, movflags +faststart
  9. Human review → approve or request adjustments
  10. Final export to YouTube upload queue
```

### Tools Required
- FFmpeg (latest) — primary video engine
- ffmpeg-python — Python API for filter_complex chains
- moviepy — per-clip effects (slow-mo inserts, fade in/out)

### Human Review Gates
- Gate 1: Approve clip order before render
- Gate 2: Approve rendered rough cut (no music)
- Gate 3: Approve final with music and effects

---

## Phase 2 — Demo Intelligence Engine

### Goal
Parse all 2,253 `.dm_73` demos, build a complete frag database, batch-render new AVI clips via WolfcamQL automation.

### 2A — Demo Parser

#### Input
2,253 `.dm_73` files in `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\demos\`

#### Extraction Targets
| Field | Source | Description |
|---|---|---|
| map_name | CS_SERVERINFO configstring | Map |
| game_type | CS_SERVERINFO | FFA/CA/CTF/Duel |
| demo_duration_ms | last snapshot.server_time | Total demo length |
| player_names | CS_PLAYERS configstrings | All players by slot |
| frag_time_ms | EV_OBITUARY entity server_time | Exact kill timestamp |
| killer_slot | EV_OBITUARY otherEntityNum2 | Killer client number |
| victim_slot | EV_OBITUARY otherEntityNum | Victim client number |
| weapon | EV_OBITUARY eventParm (MOD_*) | Means of death |
| kill_streak | sequence analysis | Kills within 3s |
| victim_airborne | victim Z-velocity at frag time | Air shot flag |

#### Tools
- `UberDemoTools` — production C++ parser, extracts frags to JSON/CSV
- `qldemo-python` — Python parser for custom event extraction
- SQLite database for all extracted data

#### Database Schema (frags.db)
```sql
CREATE TABLE demos (
  id INTEGER PRIMARY KEY,
  filename TEXT NOT NULL,
  map_name TEXT,
  game_type INTEGER,
  duration_ms INTEGER,
  parsed_at TIMESTAMP
);

CREATE TABLE frags (
  id INTEGER PRIMARY KEY,
  demo_id INTEGER REFERENCES demos(id),
  frag_time_ms INTEGER,   -- absolute server time
  pre_roll_ms INTEGER DEFAULT 5000,  -- ms before frag to start clip
  post_roll_ms INTEGER DEFAULT 2000, -- ms after frag to end clip
  killer_name TEXT,
  victim_name TEXT,
  weapon TEXT,            -- MOD_* constant name
  is_airshot BOOLEAN,
  is_multikill BOOLEAN,
  kill_streak INTEGER,
  tier INTEGER,           -- 1/2/3, human-assigned
  reviewed BOOLEAN DEFAULT FALSE,
  approved BOOLEAN DEFAULT FALSE,
  notes TEXT
);

CREATE TABLE rendered_clips (
  id INTEGER PRIMARY KEY,
  frag_id INTEGER REFERENCES frags(id),
  avi_path TEXT,
  camera_type TEXT,       -- firstperson/freelook/spline
  rendered_at TIMESTAMP
);
```

### 2B — WolfcamQL Batch Renderer

#### Automation Pattern
For each approved frag in the database:

```python
# Per-frag render job
start_time = frag_time_ms - pre_roll_ms
end_time   = frag_time_ms + post_roll_ms

# Write gamestart.cfg
gamestart_cfg = f"""
seekclock {ms_to_clock(start_time)}
video avi name {clip_name}
at {ms_to_clock(end_time)} quit
"""

# Launch wolfcamql
subprocess.Popen([
    wolfcamql_exe,
    "+set", "fs_homepath", output_dir,
    "+exec", "cap.cfg",
    "+demo", demo_path
])
```

#### Recording Config (cap.cfg)
```cfg
r_fullscreen 0
cl_aviFrameRate 60
cl_aviCodec uncompressed
cl_aviAllowLargeFiles 1
cg_draw2d 0
r_useFbo 1
r_customWidth 1920
r_customHeight 1080
s_useopenal 0
s_sdlWindowsForceDirectSound 1
mme_blurFrames 4
com_timescalesafe 1
```

### 2C — WolfWhisperer Reverse Engineering

#### Tools
- **Ghidra** (NSA open source, free) — primary disassembler
- Binary: `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfWhisperer.exe` (839KB)

#### Goals
1. Map all IPC signals between WolfWhisperer.exe and wolfcamql.exe
2. Understand the `fragforward` scan algorithm in source
3. Extract the frag detection logic → port to Python
4. Identify all GUI state written to options.ini

#### fragforward in wolfcamql source (github.com/brugal/wolfcamql)
The wolfcamql source is available — fragforward is implemented in cgame C code. Study `code/cgame/` for the implementation. WolfWhisperer's fragforward button just sends the console command `fragforward 8 5`.

### Human Review Gates
- Gate 1: Review parser output for 10 sample demos before full run
- Gate 2: Browse frag database, rate/approve frags (web dashboard)
- Gate 3: Review 10 rendered clips before full batch render

---

## Phase 3 — AI Cinematography Engine

### Goal
Build pattern recognition on raw demo data to auto-detect extraordinary frags, auto-select best camera angles, and produce cinematically perfect clips without human intervention per-clip.

### 3A — Pattern Recognition

All patterns detected directly from demo binary, no engine needed:

| Pattern | Detection Method |
|---|---|
| LG shaft frag | `MOD_LIGHTNING` + victim health delta over time (sustained damage) |
| Accuracy frag | Track damage events over window, calculate hit% |
| Air shot | `victim.velocity[2] > 200` at frag timestamp |
| Multi-kill | 2+ EV_OBITUARY from same killer within 3000ms |
| Weapon combo | Killer switches weapon (weapon field change) within 2s of kill |
| Through-geometry | Raycast check: origin vector vs BSP planes |
| Jump-kill | Killer `EF_JUMPING` flag at moment of kill |
| Telefrag | `MOD_TELEFRAG` |
| Long-range rail | Reconstruct rail vector, measure killer-victim distance |

### 3B — Trajectory & Vector Analysis

```python
# Rocket tracking
def trace_rocket(entity, snapshots):
    # entity.pos.trType == TR_GRAVITY
    # position = trBase + trDelta * t - 0.5 * gravity * t^2
    trajectory = []
    for snap in snapshots:
        t = (snap.server_time - entity.pos.trTime) / 1000.0
        x = entity.pos.trBase[0] + entity.pos.trDelta[0] * t
        y = entity.pos.trBase[1] + entity.pos.trDelta[1] * t
        z = entity.pos.trBase[2] + entity.pos.trDelta[2] * t - 0.5 * 800 * t*t
        trajectory.append((x, y, z, snap.server_time))
    return trajectory

# Rail beam reconstruction  
def reconstruct_rail(killer_state, frag_time):
    # viewangles[0] = pitch, viewangles[1] = yaw
    yaw   = math.radians(killer_state.viewangles[1])
    pitch = math.radians(killer_state.viewangles[0])
    direction = (
        math.cos(pitch) * math.sin(yaw),
        math.cos(pitch) * math.cos(yaw),
        -math.sin(pitch)
    )
    return killer_state.origin, direction
```

### 3C — Automatic Camera System

#### Per-Map Camera Library
Pre-built spline paths stored as wolfcam camera files, organized by:
- Map name
- Camera type: `overview` / `follow_killer` / `follow_victim` / `bullet_cam`
- Trigger zone: which area of the map the path covers

#### Auto-Selection Logic
```python
def select_camera(frag, map_name, available_cameras):
    # Rule 1: air shot → wide angle showing the arc
    if frag.is_airshot:
        return find_camera(map_name, "wide_angle", frag.position)
    # Rule 2: multi-kill → pull back to show all victims
    if frag.kill_streak >= 3:
        return find_camera(map_name, "overview", frag.position)
    # Rule 3: rail → reconstruct beam, find angle that shows full length
    if frag.weapon == "MOD_RAILGUN":
        return find_camera(map_name, "rail_reveal", frag.position)
    # Default: follow killer first person
    return "firstperson"
```

#### Slow-Mo Trigger
```
at {frag_time_ms - 500} timescale 0.3
at {frag_time_ms + 1000} timescale 1.0
```

### 3D — Full Event Ingestion + Knowledge Graph

Every entity event ingested:
- Item pickups (quad, armor, health — timing matters for fragmovie context)
- Jump pad launches (exciting rocket trajectories start here)
- Teleport events (telefrag setup)
- Sound events (for syncing to music in Phase 1)

Graph nodes: `Demo → Player → Frag → Weapon → Map → Camera_Path`
Query examples:
- "All railgun frags where distance > 1000 units, victim airborne, on campgrounds"
- "All multi-kills with 3+ in 2 seconds on any map"

### Human Review Dashboard
- Web app (FastAPI + simple HTML or Streamlit)
- Browse frags by tier, map, weapon, pattern tag
- Watch rendered clip in browser
- Approve / Reject / Request re-render with different camera
- Bulk operations: "approve all railgun air shots tier 1"

---

## Tools & Dependencies

### Download Targets (store in G:\QUAKE_LEGACY\tools\)

| Tool | Source | Purpose |
|---|---|---|
| FFmpeg latest | ffmpeg.org/download.html | Video encode/decode |
| UberDemoTools | github.com/mightycow/uberdemotools | Demo parsing |
| qldemo-python | github.com/Quakecon/qldemo-python | Python demo parser |
| f0e/blur | github.com/f0e/blur | Cinematic motion blur |
| WolfcamQL 12.7test49 | github.com/brugal/wolfcamql | Demo renderer |
| Ghidra | github.com/NationalSecurityAgency/ghidra | Binary RE |
| 7-Zip | 7-zip.org | Archive extraction |
| Python 3.11+ | python.org | Runtime |
| ffmpeg-python | pip install ffmpeg-python | FFmpeg Python API |
| moviepy | pip install moviepy | High-level video effects |
| SQLite3 | stdlib | Frag database |
| Streamlit | pip install streamlit | Review dashboard |

### Python Environment
```
requirements.txt:
  ffmpeg-python>=0.2.0
  moviepy>=2.0.0
  streamlit>=1.30.0
  sqlite3 (stdlib)
  requests>=2.31.0
  tqdm>=4.66.0
  pyhuffman (compile from qldemo-python)
```

---

## Key Technical References

- WolfcamQL source: github.com/brugal/wolfcamql
- WolfcamQL docs: README-wolfcam.txt (3240 lines)
- Q3 source: github.com/id-Software/Quake-III-Arena
- UberDemoTools: github.com/mightycow/uberdemotools
- dm_73 protocol: jfedor.org/quake3 (byte-level spec)
- EV_OBITUARY detection: `entity.event & ~0x300 == EV_OBITUARY` (mask event bits)
- Frag fields: `otherEntityNum` = victim, `otherEntityNum2` = killer, `eventParm` = MOD_*
- WolfcamQL batch pattern: write gamestart.cfg → launch wolfcamql → at T quit
- FFmpeg pipe: `cl_aviPipeCommand` + `/video pipe` → no intermediate AVI

---

## Phase Milestones

| Milestone | Phase | Deliverable |
|---|---|---|
| M1 | 1 | Tools downloaded, documented, tested |
| M2 | 1 | Part 4 assembled and reviewed |
| M3 | 1 | Parts 4-12 all complete, uploaded |
| M4 | 2 | 10 demos parsed, database schema validated |
| M5 | 2 | All 2,253 demos parsed, frag DB populated |
| M6 | 2 | Human review dashboard operational |
| M7 | 2 | First batch render complete (100 clips) |
| M8 | 2 | WolfWhisperer RE documented |
| M9 | 3 | Pattern detection on 10 demos validated |
| M10 | 3 | Camera auto-selection on 10 frags reviewed |
| M11 | 3 | Full AI pipeline end-to-end on 1 Part |
| M12 | 3 | Production system complete |
