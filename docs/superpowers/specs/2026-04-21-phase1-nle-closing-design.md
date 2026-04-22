# Phase 1 NLE Closing — Design Spec
**Date:** 2026-04-21  
**Status:** Approved for implementation  
**Scope:** PANTHEON Studio editor — interactive NLE timeline, FX stack, intelligent randomizer, music beatmatch chain

---

## 1. Overview

This spec closes Phase 1 by turning the PANTHEON Studio editor into a fully interactive NLE. The current state has a 4-panel layout (LIBRARY · VIEWER · INSPECTOR · TIMELINE) with read-only timeline visualization and basic clip reordering in the library. This spec adds:

1. **Interactive horizontal NLE timeline** — drag clips, gap-close on remove, cut/copy/paste/delete
2. **Per-clip FX stack** — Inspector becomes the FX editor for the selected clip
3. **Intelligent randomizer** — T1/T2/T3-aware shuffle with pinned intro/outro and ghost preview
4. **Music beatmatch chain** — ranked recommendations scored against video body AND previous track; fade-over + audio transition FX + frag audio FX
5. **Local SQLite state store** — `studio_nle.db` as the UI nervous system; manifest generated at render time

---

## 2. Architecture Decision

**DB as UI layer, manifest for render.**

- All clip arrangements, FX settings, and music assignments live in `creative_suite/database/studio_nle.db` (SQLite)
- UI reads/writes DB directly → sub-millisecond response, live feeling
- At render time: DB state → `partNN.txt` manifest + `partNN_overrides.txt` → existing render pipeline (untouched)
- StudioStore remains the in-memory reactive layer; DB is the persistence layer below it

---

## 3. Database Schema (`studio_nle.db`)

### `clip_arrangements`
| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| part | INTEGER | 1–12 |
| position | INTEGER | 0-based order in timeline |
| role | TEXT | `intro` · `body` · `outro` (intro/outro = pinned) |
| clip_path | TEXT | absolute path to .avi |
| tier | TEXT | T1 · T2 · T3 |
| is_fl | INTEGER | 0/1 |
| pair_path | TEXT | FL pair path if multi-angle |
| duration_s | REAL | from clip_durations table in frags.db |
| updated_at | REAL | unix timestamp |

### `clip_effects`
| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| arrangement_id | INTEGER FK → clip_arrangements.id | |
| effect_type | TEXT | `slowmo` · `speedup` · `shine_on_kill` · `audio_reverb` · `audio_bass_drop` · `zoom` · `vignette` |
| params | TEXT | JSON blob — effect-specific parameters |
| position | INTEGER | stack order (0 = bottom) |
| enabled | INTEGER | 0/1 |

### `music_assignments`
| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| part | INTEGER | 1–12 |
| role | TEXT | `intro` · `main_{n}` · `outro` |
| track_filename | TEXT | filename in engine/music/library/ |
| artist | TEXT | |
| title | TEXT | |
| bpm | REAL | detected or null |
| duration_s | REAL | |
| transition_in | TEXT | JSON — fade type + duration for entry |
| transition_out | TEXT | JSON — fade type + duration for exit |
| chain_score | REAL | 0.0–1.0, match vs previous track |
| position | INTEGER | playback order |

### `audio_fx`
| column | type | notes |
|---|---|---|
| id | INTEGER PK | |
| part | INTEGER | |
| trigger | TEXT | `song_transition` · `frag_kill` · `frag_railgun` · `frag_rocket` |
| effect_type | TEXT | `sweep_up` · `sweep_down` · `bass_drop` · `reverb_tail` · `filter_open` · `silence_dip` |
| params | TEXT | JSON blob |
| enabled | INTEGER | 0/1 |

---

## 4. Interactive NLE Timeline

**File:** `creative_suite/frontend/studio-timeline-nle.js` (replaces current StudioTimeline)

### 4.1 Rendering
- Custom `<canvas>` — no external library dependency (drops animation-timeline-js)
- Clip blocks rendered as coloured rectangles: T1 = gold `#e8b923`, T2 = blue `#4a9eff`, T3 = grey `#7a7a9a`
- Pinned clips (intro/outro) rendered with a lock icon overlay and muted opacity border
- Time ruler above clips; playhead as a vertical red line
- Audio track row below clip row (read-only waveform from WaveSurfer when loaded)

### 4.2 Interactions
| Action | Gesture |
|---|---|
| Select clip | left-click |
| Deselect | click empty area |
| Move clip | drag left/right (gaps close automatically — remaining clips slide) |
| Multi-select | shift-click or drag-select lasso |
| Cut | Ctrl+X |
| Copy | Ctrl+C |
| Paste | Ctrl+V (inserts at playhead position) |
| Delete | Delete / Backspace — gap closes |
| Duplicate | Ctrl+D |
| Context menu | right-click → Cut / Copy / Delete / Set as Intro / Set as Outro |

### 4.3 Gap-close logic
When a clip is removed: all clips with `position > removed.position` shift left by 1. DB updated in a single transaction. Store dispatches `SET_CLIPS` with new order.

### 4.4 Pinned clips
Intro and outro rows are visually separated (top/bottom strips). Pinned clips cannot be dragged into the body zone. The randomizer never touches them.

---

## 5. Inspector FX Stack

**File:** `creative_suite/frontend/studio-inspector.js` (extend existing v2)

When a clip is selected, the Inspector body renders:

```
CLIP INFO   (read-only: name, tier, duration, weapon, map)
OVERRIDES   (sliders: head_trim, tail_trim, slow_rate — saved to clip_arrangements)
FX STACK    (collapsible cards, one per effect in clip_effects for this clip)
  ┌─ SLOW MOTION ──────────────────── [enabled] [✕]
  │  rate: [====●====] 0.5×  window: [====●====] ±0.8s
  └─────────────────────────────────────────────────
  ┌─ SHINE ON KILL ────────────────── [enabled] [✕]
  │  intensity: [======●==] 0.8  color: [gold ▼]
  └─────────────────────────────────────────────────
  [+ ADD EFFECT ▼]   (dropdown: slowmo / speedup / shine / zoom / reverb / bass drop / ...)
[APPLY]
```

Each effect card:
- Title bar with enable toggle + remove button
- Parameter rows using the existing `.insp-range-wrap` / `.insp-select` DOM controls
- Changes save to `clip_effects` table on every slider `change` event (not `input`, to avoid DB thrash)
- APPLY button regenerates the manifest entry for this clip only (fast partial update)

### 5.1 Effect Catalogue (Phase 1 scope)

**Video effects:**
| Effect | Params |
|---|---|
| `slowmo` | rate (0.1–1.0), window_s (0.2–3.0) |
| `speedup` | rate (1.1–4.0), window_s (0.2–2.0) |
| `zoom` | scale (1.1–2.0), center_x, center_y |
| `vignette` | intensity (0–1) |
| `shine_on_kill` | intensity (0–1), color (gold/white/red) |

**Audio effects (per-clip):**
| Effect | Params |
|---|---|
| `bass_drop` | delay_ms (offset from kill event), intensity (0–1) |
| `reverb_tail` | decay_s (0.2–2.0), mix (0–1) |
| `audio_silence_dip` | window_s, depth_db |

---

## 6. Intelligent Randomizer

**Backend:** `creative_suite/api/studio.py` — new `POST /api/studio/part/{n}/randomize`

### 6.1 Algorithm
1. Load all body clips for the part (role = `body`, sorted by position)
2. Separate by tier: T1_pool, T2_pool, T3_pool
3. Target mix: T2 = 60% of slots, T1 = 25%, T3 = 15% (configurable via config)
4. Assign slots in round-robin by music section shape (reuse existing `beat_sync.py::plan_flow_cuts_v2`): `drop` slots → T1, `build` slots → T3, `verse/break` → T2
5. Fill remaining slots to meet ratio targets; shuffle within each tier group
6. Return new ordering as JSON — **do not write to DB yet**

**Frontend:** `studio-edit.js`
- RANDOMIZE button dispatches `POST /api/studio/part/{n}/randomize`
- Renders ghost state on timeline (clips shown at 60% opacity in new order)
- "ACCEPT" button writes new order to `clip_arrangements` DB + dispatches `SET_CLIPS`
- "TRY AGAIN" re-calls the endpoint
- Intro/outro clips never appear in the response (excluded server-side)

---

## 7. Music Beatmatch Chain

**Backend:** `creative_suite/api/studio.py` — new `GET /api/studio/part/{n}/music_recommend`

### 7.1 Scoring
For each track in `engine/music/library/`:
- **BPM match** (40% weight): `1 - |bpm_track - bpm_video| / bpm_video`
- **Duration coverage** (30% weight): existing `music_match.py::compute_match`
- **Chain score** (30% weight, only for tracks 2+): spectral/energy similarity to tail of previous track — implemented as tempo proximity + key compatibility lookup from `MusicLibrary.json` metadata

Returns top 10 ranked tracks per role slot (intro/main/outro).

### 7.2 Frontend — Generate Panel
Clicking GENERATE opens an inline panel below the timeline toolbar:
```
BEATMATCH RECOMMENDATIONS — Part 4 · body 4:32
────────────────────────────────────────────────
ROLE: MAIN TRACK
  98%  Tribal War Drums — Rhythm X     128 BPM  4:18  [SELECT]
  91%  Bass Protocol — Neonix           140 BPM  5:02  [SELECT]
  85%  Voltage Rush — Current           136 BPM  3:55  [SELECT]

  [CHAIN → next track recommendations shown after selecting main]
────────────────────────────────────────────────
```
Selecting a track writes to `music_assignments`. The panel updates to show chain recommendations for the next slot.

### 7.3 Fade-over & Audio Transition FX
Each `music_assignments` row carries `transition_out` JSON:
```json
{"type": "xfade", "duration_s": 4.0, "effect": "sweep_up"}
```
Supported transition types: `xfade` · `filter_close_open` · `bass_riser` · `silence_gap` · `instant_cut`  
At render time, `music_stitcher.py` reads these fields and applies the corresponding ffmpeg audio graph segment.

### 7.4 Audio FX on Frags
The `audio_fx` table drives per-event audio processing in the render pipeline.  
`creative_suite/engine/effects.py` extended with:
- `bass_drop(event_peak_t, intensity)` → sub-bass boost + brief silence pre-event
- `reverb_tail(event_peak_t, decay_s)` → convolution reverb on post-event tail
- `filter_open(event_peak_t)` → high-pass sweep opening into the kill

---

## 8. Manifest Generation at Render Time

New function: `creative_suite/engine/manifest_generator.py::generate_manifest(part)`

1. Read `clip_arrangements` for the part (ordered by position)
2. For each clip, read its `clip_effects` rows
3. Emit manifest line: `clip_path [slow=0.5 window=0.8] [zoom=1.2]` (extended manifest grammar)
4. Write `creative_suite/engine/clip_lists/partNN.txt`
5. Read `music_assignments` for the part, write `partNN_overrides.txt` music fields
6. Render pipeline reads these files as before — zero changes to render code

---

## 9. New API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/studio/part/{n}/arrangement` | Load clip_arrangements for part |
| PUT | `/api/studio/part/{n}/arrangement` | Save full arrangement (bulk upsert) |
| POST | `/api/studio/part/{n}/arrangement/{id}/fx` | Add effect to clip |
| PUT | `/api/studio/part/{n}/arrangement/{id}/fx/{fx_id}` | Update effect params |
| DELETE | `/api/studio/part/{n}/arrangement/{id}/fx/{fx_id}` | Remove effect |
| POST | `/api/studio/part/{n}/randomize` | Get randomized body order (no write) |
| GET | `/api/studio/part/{n}/music_recommend` | Ranked track recommendations |
| GET | `/api/studio/audio_fx` | List all audio_fx presets |
| PUT | `/api/studio/audio_fx/{id}` | Update audio_fx params |

---

## 10. Files to Create / Modify

| File | Action | Notes |
|---|---|---|
| `creative_suite/database/studio_nle.db` | CREATE | New SQLite DB |
| `creative_suite/database/nle_schema.sql` | CREATE | Schema + indexes |
| `creative_suite/database/nle_db.py` | CREATE | DB access layer (connection pool, CRUD helpers) |
| `creative_suite/frontend/studio-timeline-nle.js` | CREATE | Custom canvas NLE timeline |
| `creative_suite/frontend/studio-inspector.js` | MODIFY | Add FX stack to existing v2 |
| `creative_suite/frontend/studio-edit.js` | MODIFY | Randomize button, Generate panel, wire new timeline |
| `creative_suite/frontend/studio.css` | MODIFY | NLE timeline canvas styles, FX card styles |
| `creative_suite/api/studio.py` | MODIFY | 9 new endpoints |
| `creative_suite/engine/manifest_generator.py` | CREATE | DB → manifest serializer |
| `creative_suite/engine/music_chain.py` | CREATE | Chain scoring logic |
| `creative_suite/engine/effects.py` | MODIFY | bass_drop, reverb_tail, filter_open |
| `creative_suite/engine/music_stitcher.py` | MODIFY | Read transition JSON from DB |

---

## 11. Implementation Order

1. **DB foundation** — schema, `nle_db.py`, init script
2. **Arrangement API** — GET/PUT arrangement endpoints, import existing clip lists into DB
3. **NLE timeline canvas** — `studio-timeline-nle.js` with render, select, drag
4. **Gap-close + edit operations** — delete, cut/copy/paste on timeline
5. **Inspector FX stack** — effect cards, params, DB save
6. **Randomizer** — backend algorithm + frontend ghost preview
7. **Music recommend + chain** — scoring, panel UI
8. **Audio FX** — bass drop, reverb, transition effects
9. **Manifest generator** — DB → render pipeline bridge
10. **End-to-end test** — Part 4: randomize → assign music → render → verify output
