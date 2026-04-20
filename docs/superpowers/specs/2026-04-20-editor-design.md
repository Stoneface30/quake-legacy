# QUAKE LEGACY — Local Editor (Tier 2) Design Spec

**Date:** 2026-04-20
**Status:** Draft, pending user review
**Supersedes:** nothing yet — net-new spec
**Relates to:** CS-1..CS-6 (Cinema Suite rules), P1-A..P1-DD (Phase 1 rules),
Rule P1-J v2 (preview-first), and the Tier 1 clip-removal work landed
2026-04-20 (`feat(cinema): Tier 1 clip-removal UI + API wiring`).

---

## 1. Goal

Give the user a **local, free, open-source, Premiere/AE-class editor**
tailored exactly to the QUAKE LEGACY fragmovie workflow. They already
have a render pipeline (Phase 1 `render_part_v6`) and a review shell
(Cinema Suite). What's missing is a **live editing surface** — one
where they can see the assembled body, scrub on a timeline, view the
music structure, reorder/trim/remove clips, tag slow-mo windows, preview
node-graph effects, and keyframe parameters — all before committing to
a final render.

**What this is not:** a replacement for Premiere/AE for everything.
It's a **fragmovie-specific** editor that hard-codes the tier semantics,
beat-snap rules, PANTHEON intro + title card, and music stitcher. It will
never do motion graphics from scratch — but it will beat Premiere for
*this specific* job because every affordance matches the P1 rules.

## 2. Scope (what ships, what stays out)

**Ships:**
- Timeline with multi-row tracks: video (clips + multi-angle), game audio,
  music (3-track: intro/main/outro), keyframes, annotations.
- Live playback of the assembled body via WebCodecs from proxy mp4s —
  frame-accurate scrub, JKL transport, hotkey trims.
- Node-graph compositor for effects (slow-mo window, zoom, color grade,
  title-card style) — lives in a separate "Effects" tab, reusable across
  clips via node templates.
- Keyframe editor for any node parameter, bezier curves, linked params.
- Parameter inspector (Tweakpane-style) for the selected clip / node.
- MLT backend: serialize the timeline to MLT XML, render via
  `mlt-consumer avformat` to the P1 quality ceiling (CRF 15-17 x264 slow
  or av1_nvenc cq=18, per Rule P1-J v2).
- OTIO interchange: `POST /api/editor/timeline/otio` dumps the current
  state as OpenTimelineIO JSON, so the user can re-open in Kdenlive,
  DaVinci, or any OTIO-capable tool. Symmetric load.
- Three-pane layout: timeline (bottom), preview (top left), inspector
  (top right). Resizable via split panes.
- Persistent project file (`output/part{NN}_editor_state.json`), auto-saved
  on every mutation (same pattern as `flow_plan.json`).

**Stays out** (Phase 4+, explicit non-goals):
- Multi-project / library management (one Part at a time is fine).
- Realtime effects at 60fps on 1080p source (proxies handle scrubbing;
  final render is the only place quality matters — Rule P1-J).
- Asset generation in-editor (that's the Creative Suite ComfyUI loop).
- Collaboration / multi-user / cloud sync.
- Mobile / touch / tablet (desktop only, 1440p+ assumed).
- Plug-in SDK (all effects are hard-coded nodes in MLT + custom JS).

## 3. Architecture

### 3.1 Runtime split

```
Browser (Chromium, http://127.0.0.1:8800/editor)
  ├─ Playback: WebCodecs + mp4box.js (decode) + <canvas> (paint)
  ├─ Timeline: animation-timeline-control (ievgennaida)
  ├─ Audio rows: wavesurfer.js v7 + wavesurfer-multitrack
  ├─ Node graph: LiteGraph.js (jagenjo upstream)
  ├─ Keyframes: Theatre.js @theatre/browser-bundles UMD
  ├─ Inspector: Tweakpane v4
  └─ State sync: fetch + SSE, one-shot PUTs per mutation

FastAPI (Python, same uvicorn as Cinema Suite, new /api/editor prefix)
  ├─ MLT: Python SWIG bindings — Profile / Producer / Tractor / Consumer
  ├─ OTIO: opentimelineio.schema round-trip via mlt-otio adapter
  ├─ Proxy: ffmpeg -c:v libx264 -g 1 -x264-params keyint=1 scale=960:540
  │   Writes to output/_proxies/part{NN}/chunk_NNNN_proxy.mp4
  ├─ Render: MLT Consumer avformat → quality-ceiling mp4 per Rule P1-J
  ├─ Timeline state: output/part{NN}_editor_state.json (atomic writes)
  └─ Shared: reuse Cinema Suite's JobQueue for proxy + render jobs (CS-1)
```

### 3.2 Why MLT as the backend

- **Proven:** backs Kdenlive, Shotcut, Flowblade. Decade-plus of
  production hardening.
- **Python-native:** `import mlt` works with our existing Python stack.
  No node shelling out, no ffmpeg graph string hell.
- **MLT XML is serializable:** every timeline state round-trips to
  a text file that survives version control and agent inspection.
- **Consumer: avformat:** one knob to render anything ffmpeg can render.
  Rule P1-J knobs map 1:1 (`vcodec=libx264 crf=15 preset=slow` etc).
- **LGPL-2.1:** compatible with all our existing GPL-2.0 code
  (wolfcamql, vendored msg.c/huffman.c/common.c).

### 3.3 Why OpenTimelineIO as interchange

- **Apache-2.0, Pixar-backed, ASWF-adopted** — industry standard.
- **Symmetric with every serious DAW-adjacent NLE** including Kdenlive,
  DaVinci, Premiere (via FCPXML), Flowblade, Blender VSE.
- **Pure data model** — `opentime.RationalTime` keeps frame precision
  through all transforms. No drift.
- **Fits our mental model:** a Part is a `Timeline`; tracks are
  `video_track` + `audio_track`; clips are `Clip` with `media_reference:
  ExternalReference(target_url=normalized_chunk.mp4)`. Linear speed
  effects map directly to `LinearTimeWarp(time_scalar=0.5)`.

### 3.4 Why WebCodecs for playback

- **Frame-accurate** decode on the GPU. Chromium + mp4box.js = what
  Mux Video Player and CapCut Web use.
- **No plugin:** just `<canvas>`. Works on any reasonably modern browser.
- **Proxies keep it smooth:** 960×540 all-intra H.264 is trivial to
  decode at 60fps. Full-quality source is only touched at render time.
- **Fallback:** if the user's browser doesn't have WebCodecs (~5%), the
  timeline renders a plain `<video>` element with `requestVideoFrameCallback`
  (rVFC) for scrub — still usable, just less smooth.

### 3.5 Why LiteGraph + Theatre + Tweakpane (and not ComfyUI's own stack)

ComfyUI forked LiteGraph and archived their fork. The **upstream
jagenjo/litegraph.js** is still active and MIT-licensed. We use upstream
directly — no ComfyUI coupling for this editor.

- **LiteGraph:** node graph canvas, subgraphs (for templated effects),
  pin-based connection model, built-in undo.
- **Theatre.js:** bezier keyframe editing studio — *just the studio UI*.
  Keyframe data serializes to a JSON blob stored inline in our editor
  state JSON. Core library is Apache-2.0; studio is AGPL-3.0, which is
  acceptable because the editor is local-only (no service distribution).
- **Tweakpane:** minimalist param inspector. Binds to JS objects.
  Lightweight (~45 KB), MIT.

## 4. User Flow

### 4.1 First-open (Part already rendered at v99)

1. User navigates to `http://127.0.0.1:8800/editor?part=4`.
2. Editor reads `output/part04_flow_plan.json` + `output/part04_overrides.txt`
   + `output/part04_music_plan.json` + `output/part04_beats.json`.
3. For any chunk lacking a proxy, editor enqueues a proxy-gen job to the
   shared `JobQueue` (depth 1 per CS-1). Shows a progress strip.
4. Timeline populates: video row (127 clips), FL inserts as a sub-row,
   game-audio row, three music rows, downbeat tick marks from
   `music_structure.sections[]`.
5. Playback element loads the first proxy, ready to scrub.

### 4.2 Editing session

- User scrubs timeline, marks slow-mo windows (click+drag on a clip,
  attaches a `LinearTimeWarp(0.5)` to a `seam_offset` window).
- User clicks × REMOVE on clips they want gone. Tier 1's
  `output/part{NN}_overrides.txt` mechanism handles it — same data path.
- User keyframes title-card font scale via Theatre — serialized to
  `part{NN}_editor_state.json.theatre_data`.
- User edits the node graph for color grade — updates to a clip's
  `nodes[]` array.
- Every mutation: one-shot PUT to backend, atomic file write, SSE
  broadcast back to the session for multi-tab sync.

### 4.3 Rendering

- User clicks RENDER. Backend serializes current state to MLT XML, writes
  to `output/part{NN}_editor.mlt`, then runs
  `mlt-melt output/part04_editor.mlt -consumer avformat:target=... crf=15
  preset=slow vcodec=libx264 acodec=aac`.
- Progress SSE stream from `JobQueue`. CS-1 enforces depth 1.
- Output drops at `output/Part4_v{N}_editor.mp4`. Version row written
  to `render_versions` SQLite table, flow_plan auto-tagged as
  `part04/v{N}-editor` in `output/.git` per CS-3.
- Rule P1-J v2: preview-quality (CRF 23 veryfast) is the default knob
  for scrub export; only explicit "Ship It" clicks use the full quality
  ceiling.

### 4.4 Export to Kdenlive / DaVinci

- User clicks "Export OTIO." Backend runs `otio.adapters.write_to_file`
  on the current timeline, emits `output/part{NN}.otio`.
- File is drag-and-droppable into Kdenlive (native OTIO adapter) and
  DaVinci Resolve (via FCPXML bridge). Round-trip tested on Part 5.

## 5. Data Model

### 5.1 `output/part{NN}_editor_state.json`

```json
{
  "part": 5,
  "schema_version": 1,
  "timeline": {
    "duration_s": 1738.86,
    "fps": 60,
    "tracks": [
      {
        "kind": "video",
        "name": "body",
        "clips": [
          {
            "id": "clip_0000",
            "chunk": "chunk_0000.mp4",
            "in_s": 0.0,
            "out_s": 29.011,
            "start_s": 13.0,
            "time_warp": null,
            "nodes": [],
            "removed": false
          }
        ]
      },
      {
        "kind": "audio",
        "name": "game",
        "source": "game_stem.wav",
        "gain_db": 0.0
      },
      {
        "kind": "audio",
        "name": "music_main",
        "sources": [
          {"path": "part05_music_01.mp3", "start_s": 13.0, "dur_s": 351.5}
        ]
      }
    ],
    "keyframes": { "_theatre_data": "...opaque blob..." }
  },
  "nodes_library": [ ... ],
  "saved_at": "2026-04-20T10:23:00Z"
}
```

### 5.2 MLT XML generated from the above

```xml
<mlt profile="atsc_1080p_60">
  <producer id="chunk_0000" in="00:00:00.000" out="00:00:29.011">
    <property name="resource">output/_part05_v6_body_chunks/chunk_0000.mp4</property>
  </producer>
  <!-- ... -->
  <playlist id="body">
    <entry producer="chunk_0000" in="..." out="..."/>
  </playlist>
  <tractor id="main">
    <track producer="body"/>
    <track producer="music_main"/>
    <filter mlt_service="audiomix"/>
  </tractor>
</mlt>
```

### 5.3 OTIO JSON generated symmetrically

```json
{
  "OTIO_SCHEMA": "Timeline.1",
  "name": "Part 5",
  "tracks": {
    "OTIO_SCHEMA": "Stack.1",
    "children": [
      {
        "OTIO_SCHEMA": "Track.1",
        "kind": "Video",
        "children": [
          {
            "OTIO_SCHEMA": "Clip.1",
            "name": "chunk_0000",
            "source_range": {
              "start_time": {"rate": 60, "value": 0},
              "duration": {"rate": 60, "value": 1740}
            },
            "media_reference": {
              "OTIO_SCHEMA": "ExternalReference.1",
              "target_url": "file:///G:/QUAKE_LEGACY/output/_part05_v6_body_chunks/chunk_0000.mp4"
            }
          }
        ]
      }
    ]
  }
}
```

## 6. API Surface

All under `/api/editor` prefix (new router, sibling of `/api/phase1`):

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/editor/parts/{n}/state` | Fetch editor_state.json |
| PUT | `/api/editor/parts/{n}/state` | Full state replace, atomic write |
| PATCH | `/api/editor/parts/{n}/state` | JSON Patch for single mutations |
| POST | `/api/editor/parts/{n}/proxies` | Trigger proxy generation job |
| GET | `/api/editor/parts/{n}/proxies/status` | {ready, pending, failed} |
| POST | `/api/editor/parts/{n}/render` | Render via MLT (Rule P1-J profile) |
| POST | `/api/editor/parts/{n}/export/otio` | Write .otio file |
| POST | `/api/editor/parts/{n}/export/mlt` | Write .mlt file |
| GET | `/api/editor/jobs/{job_id}/events` | SSE job stream (reuses JobQueue) |
| WS | `/api/editor/parts/{n}/sync` | Broadcast mutations to other tabs |

Reuses existing `JobQueue` (Cinema Suite `_render_worker.py`) — CS-1 applies.

## 7. Gates

- **G-T2-1** (proxy gate): All 127 chunks of a Part must have working
  proxies before the editor opens. Missing proxies are auto-generated
  but the UI shows a blocker banner until they're ready.
- **G-T2-2** (OTIO round-trip): Export a timeline to .otio, re-import it,
  verify the re-imported state matches the original bit-for-bit (modulo
  float rounding < 1ms on all time values).
- **G-T2-3** (MLT render parity): For Part 5, a no-edit render via MLT
  must produce an mp4 within 1% duration of `Part05_v1_PREVIEW_freshstems.mp4`
  and pass ebur128 level gate (Rule P1-G).
- **G-T2-4** (Rule P1-J compliance): Default render profile is preview
  (CRF 23 veryfast). Only explicit "Ship It" toggle unlocks the quality
  ceiling. Regression test: spawn render with `mode=scrub`, inspect
  the MLT consumer props, assert `crf=23 preset=veryfast`.
- **G-T2-5** (CS-1 compliance): Second simultaneous render submit
  returns 409, not queues. Test against `JobQueue`.
- **G-T2-6** (Part 4/5/6 smoke): After Tier 2 ships, re-edit Part 5 in
  the new editor, make a 3-cut trim + 1 slow-mo window + 1 clip removal,
  render. Resulting mp4 plays, passes level gate, shorter body is
  reflected in music_plan (music stitcher re-ran with new body_dur).

## 8. Dependencies (all OSS, all pass CS npm-allowance policy)

| Name | License | Role | Notes |
|---|---|---|---|
| MLT | LGPL-2.1 | Backend NLE engine | `pip install mlt` |
| OpenTimelineIO | Apache-2.0 | Interchange | `pip install opentimelineio` |
| ffmpeg (existing) | GPL / LGPL | Proxy + consumer | Already at tools/ffmpeg/ |
| wavesurfer.js v7 | BSD-3 | Audio rows | CDN importmap |
| wavesurfer-multitrack | BSD-3 | Multi-track audio | CDN importmap |
| animation-timeline-control | MIT | Canvas timeline | CDN importmap |
| mp4box.js | BSD-3 | WebCodecs container demux | CDN importmap |
| LiteGraph.js (upstream) | MIT | Node graph | CDN importmap |
| Theatre.js | Apache-2.0 (core), AGPL-3.0 (studio) | Keyframes | Browser bundle UMD |
| Tweakpane v4 | MIT | Param inspector | CDN importmap |

Zero npm packages installed yet — everything rides on the existing
importmap + ffmpeg + Python/pip machinery. No build step added.

## 9. Rules Introduced

- **EDT-1** (editor project file is source of truth): `output/part{NN}_editor_state.json`
  is canonical. Regenerate `flow_plan.json` from it via a derivation
  function; never edit flow_plan directly once Tier 2 is live.
- **EDT-2** (MLT XML is generated, never hand-edited): The MLT file is
  a build artifact. Any tweak happens in the editor UI or the JSON.
- **EDT-3** (Proxies live in `output/_proxies/`, one dir per part):
  Cleanable, regenerable. Watchdog from render_supervisor.sh applies —
  if disk drops below 10GB, proxies get wiped first.
- **EDT-4** (Render always goes through JobQueue): Even export-to-otio
  goes through the queue, so CS-1 depth-1 rule applies uniformly.
- **EDT-5** (Preview-first Rule P1-J v2 still rules): Default render
  profile is `preview`. `final` requires the user typing the literal
  word "ship" in the render dialog.

## 10. Risks / Unknowns

- **MLT Python bindings on Windows**: pip install `mlt` may not ship
  a Windows wheel. Fallback: build MLT from source under MSYS2, or use
  WSL2 with the Windows ffmpeg for file I/O. **Action:** dispatch a
  research agent to verify `pip install mlt` on Windows 11 during
  Step 1 of the plan — if it fails, fall back to WSL2 bridge.
- **Theatre.js AGPL**: Only the studio UI is AGPL-3.0. As long as the
  editor is a local tool and doesn't get distributed as a service, we're
  compliant. If we ever decide to distribute, we swap the studio for a
  custom UI (core is Apache-2.0). Document in NOTICE.md.
- **WebCodecs on older Chromium**: Chromium 94+ has it; Firefox 130+.
  If user's browser is behind, fall back to `<video>` + rVFC. Acceptable
  degradation.
- **Proxy generation cost**: 127 chunks × ~29s each × 10fps proxy gen
  speed ≈ 6 minutes first-open. Mitigated by running proxies in
  background during UI boot; user can still browse inspectors until the
  proxies catch up.

## 11. Scope Decomposition (→ plan)

Tier 2 is too big for one spec. The implementation plan decomposes it
into 9 build-steps:

| Step | Deliverable | Days | Gate |
|---|---|---|---|
| 1 | MLT + OTIO Python harness, smoke render | 1 | G-T2-3 |
| 2 | Proxy generator + `/proxies` endpoint | 0.5 | G-T2-1 |
| 3 | Editor state schema + GET/PUT/PATCH endpoints | 0.5 | — |
| 4 | Static `/editor` route + three-pane layout | 0.5 | — |
| 5 | Timeline row 1 (video + playback) via WebCodecs | 1.5 | — |
| 6 | Audio rows (game + 3 music) via wavesurfer | 1 | — |
| 7 | LiteGraph node panel + clip-to-node binding | 1 | — |
| 8 | Theatre keyframes + Tweakpane inspector | 1 | G-T2-2 |
| 9 | Render button + MLT consumer + render_versions row | 1 | G-T2-3..6 |

Total: **8 build-days** (~1.5 calendar weeks with review cycles).

Out of scope for this plan (deferred to a future spec):
- Import from Premiere .prproj / .xml
- Auto-cut ML model (Phase 3 territory)
- Node-graph marketplace / sharing
- Mobile review UI

---

*End of spec. See companion plan at
`docs/superpowers/plans/2026-04-20-editor-plan.md`.*
