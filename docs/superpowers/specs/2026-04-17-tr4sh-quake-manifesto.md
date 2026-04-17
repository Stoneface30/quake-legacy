# TR4SH QUAKE — The Split-2 Manifesto

**Date:** 2026-04-17
**Status:** Vision spec (supersedes the split between command-center + engine-pivot specs; both fold into this)
**Preconditions:** Split 1 (video pipeline) closed. `SPLIT1_USER_CHECKLIST.md` at zero.
**Scope:** One engine. One interface. One source of truth. Ours.

---

## 1. The Prime Directive

Quake Live stops being the thing we work around. It becomes a CHAPTER of
a thing we own — **TR4SH QUAKE** — an engine + command-center fusion
where:

- `.dm_73` parsing, scene reconstruction, rendering, capture, and style-swap
  all live in ONE codebase
- The interface ISN'T "on top of" the engine — it's fused with it. The
  engine tells the interface what it sees. The interface tells the engine
  what to render.
- Every demo becomes a fully extrapolated scene tree we can query: which
  entities existed at t=42300ms, where was each player looking, what was
  the projectile trajectory, what texture was on which wall.
- We train an agent on the reconstructed scenes — free cam, kill cam,
  image-reading from the framebuffer — so the interface knows what's in
  the demo BEFORE we tell it.
- ComfyUI handles all generative/aesthetic pivots.

"Similar to the truth intended language" — exactly. One engine speaks
for Q3A, QL, and whatever custom protocol we end up with. No more
translating between three projects' idioms.

---

## 2. Architecture (one app, one truth)

```
┌───────────────────────────────────────────────────────────────┐
│                       TR4SH QUAKE                             │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Engine Core (fork of q3mme → our own)                  │  │
│  │  - Protocol 66/68/73 all natively supported             │  │
│  │  - Scene graph exposed as API (not hidden state)        │  │
│  │  - Free camera, time scrub, kill-cam primitives         │  │
│  │  - 4K+ capture, MSAA 8x, FFV1/HuffYUV/HEVC NVENC        │  │
│  └────┬──────────────────────────────────────┬─────────────┘  │
│       │                                      │                │
│  ┌────▼──────────────┐                ┌──────▼─────────────┐  │
│  │ Scene Extrapolator│                │ Frame Capture Bus  │  │
│  │  every snapshot → │                │  engine → disk or  │  │
│  │  queryable graph  │                │  websocket stream  │  │
│  └────┬──────────────┘                └──────┬─────────────┘  │
│       │                                      │                │
│  ┌────▼──────────────────────────────────────▼─────────────┐  │
│  │           Command Center API (in-process)              │  │
│  │  - REST + WebSocket                                    │  │
│  │  - SQLite at data/tr4sh_quake.db (project-local)       │  │
│  │  - Asset library, style packs, pk3 build               │  │
│  │  - ComfyUI client, Ollama vision client                │  │
│  │  - Agent loop (free cam + kill cam + image reader)     │  │
│  └────┬─────────────────────────────────────────────────────┘ │
│       │                                                        │
│  ┌────▼─────────────────────────────────────────────────────┐ │
│  │                   Web UI (Three.js)                      │ │
│  │  Demo hub, asset browser, style packs, render controller │ │
│  │  Agent observability (what does the agent see?)          │ │
│  └──────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
         │                                 │
    ComfyUI (external)              Ollama (external)
```

One executable. One process tree. One SQLite file. The API surface is
exposed IN-process via FastAPI over uvicorn, embedded next to the engine.

---

## 3. Why Fork q3mme Instead of Writing From Scratch

q3mme already gives us: smooth camera interpolation, clean AVI capture,
time-scale commands, full fragmovie DSL. id Tech 3 is legendary-stable.
Rewriting it wastes 25 years of known-good code.

What we ADD on top of q3mme:

1. **Protocol 73 patches** — lifted from wolfcamql-src, ported clean
2. **Scene API** — new C module `cg_scene_export.c` that dumps the client
   game state every frame as a JSON-over-WS message
3. **Embedded FastAPI** — Python subprocess the engine spawns; they share
   a Unix-domain-socket-like named pipe on Windows
4. **ComfyUI hot-swap** — `fs_homepath` dynamically reloaded between
   captures, so per-clip style swaps don't need engine restart
5. **Agent hooks** — three primitives (`free_cam_at`, `kill_cam_of_frag`,
   `read_framebuffer_as_png`) the agent can call via the API

The name "Tr4sH Quake" is literal: it's our fork, with the fragmovie
pipeline baked into the engine, not bolted on. Once this lands, wolfcam
+ standalone q3mme + the Command Center web app all collapse into ONE
shipping binary (plus ComfyUI as external dependency).

---

## 4. Source Unification

Everything currently split lives under one tree:

```
G:\QUAKE_LEGACY\tr4sh-quake\
├─ engine\                   (C, fork of q3mme)
│  ├─ code\
│  │  ├─ cgame\              (+ protocol 73 patches, + scene export)
│  │  ├─ client\             (+ capture bus)
│  │  ├─ renderer\           (baseq3 + renderer2 options)
│  │  └─ game\
│  ├─ build\                 Windows / Linux make targets
│  └─ patches\               our diffs vs upstream q3mme
│
├─ command_center\           (Python, FastAPI, uvicorn)
│  ├─ app\
│  ├─ web\
│  ├─ data\
│  │  └─ tr4sh_quake.db     (SQLite WAL — the one database)
│  └─ generated\             (variants, packs, sprites, renders)
│
├─ agent\                    (demo-reading trainable agent)
│  ├─ free_cam\
│  ├─ kill_cam\
│  ├─ image_reader\          (CLIP / LLaVA / gemma-vision)
│  └─ training\
│
├─ docs\                     (consolidated)
└─ tr4sh_quake.exe           (final shipping binary, spawns Python child)
```

**Asset source of truth stays Steam** for Q3A and QL baseq3 (Rule ENG-1).
Our own generated overrides live in `command_center/generated/packs/`
as `zzz_*.pk3`. No change there — just a cleaner home.

---

## 5. The Agent — What "Knows Before We Do" Actually Means

Three capabilities user called out:

1. **Free view** — given a demo + a time, position a camera anywhere in
   the map and render what the engine sees. Engine-native, not a hack.
2. **Kill cam** — given a frag event, replay the 2 seconds leading up
   to it from any of: FP attacker, FP victim, third-person attacker,
   "cinematic" angle chosen by agent. Agent picks based on what's visible.
3. **Image reading** — agent consumes the framebuffer in near-real-time
   via gemma3:4b-vision or LLaVA, emits captions: "rocket in flight toward
   RA platform," "LG beam hitting victim midair." These become tags in
   our frag database alongside the mechanical detection.

Training target: a sequence model that predicts "this is a highlight-worthy
frag" from raw scene features (projectile trajectories, LOS breaks,
damage events, air time) BEFORE the image reader confirms it. Image
reader is the ground-truth labeler.

Output: a frag is auto-tagged with `mechanical_highlight_score`,
`visual_highlight_score`, and their disagreement is the interesting
signal — "the agent thinks this is a peak, the stats don't" usually
means a hype moment we'd miss on numbers alone.

---

## 6. What Supersedes / Merges From Prior Specs

| Prior spec | Fate |
|---|---|
| `2026-04-17-creative-suite-design-v1-superseded.md` | Dead, keep for history |
| `2026-04-17-command-center-design.md` | MERGES IN — becomes the `command_center/` subtree |
| `2026-04-17-engine-pivot-design.md` | MERGES IN — its q3mme-fork decision IS Tr4sH Quake's starting fork |

One spec, one repo tree, one binary. Rename the two specs with
`-merged-into-tr4sh-quake-manifesto` suffix next commit.

---

## 7. Sprint Plan (~60 build-days, 3 parallel tracks)

**Track A — Engine Fork** (~25 days)
1. Fork q3mme into `tr4sh-quake/engine/`, build clean
2. Port wolfcamql protocol 73 patches into `cg_servercmds.c` + `msg.c`
3. Validate .dm_73 playback vs wolfcam on 3 golden demos
4. Add scene export module, JSON-over-pipe to embedded Python
5. Add capture-bus hooks, confirm 4K HuffYUV + MSAA 8x still works

**Track B — Command Center** (~25 days, parallel)
All 10 sprints from the original Command Center spec, now relocated.
Only difference: the engine-abstraction layer (old Sprint 8) vanishes
because we OWN the engine.

**Track C — Agent** (~20 days, starts after Track A sprint 4)
1. Scene-graph consumer (reads engine WS stream)
2. Free-cam positioner (given demo+time → render PNG)
3. Kill-cam replay planner (given frag → choose angle, render clip)
4. Image reader loop (framebuffer → gemma3:4b-vision → caption)
5. Trainable scoring head (scene features → highlight score)

---

## 8. Gates

- **Gate T1:** Engine fork builds clean, runs one Q3A demo. (end of Track A sprint 1)
- **Gate T2:** Engine plays one .dm_73 demo correctly vs wolfcam reference. (end of Track A sprint 3)
- **Gate T3:** Command center in-process with engine, shared SQLite, one style pack compiled and applied to one clip render. (end of Track B sprint 7)
- **Gate T4:** Agent captions a frag in under 5s from demo time-index. (end of Track C)
- **Gate T5:** One Part 4 clip re-rendered end-to-end through Tr4sH Quake alone. Wolfcam untouched. (end of all tracks)

---

## 9. What Split 2 Is NOT (yet)

- NOT a replacement for the ioquake3 community. We're a specialized fork for fragmovie production.
- NOT a Quake Live server or client. It plays demos, renders, and composes videos. No live netplay.
- NOT a general-purpose game engine. It's purpose-built for our workflow.
- NOT a YouTube upload tool. Sprint 10 (4K master → YT mastering) stays its own spec, runs on Tr4sH Quake's capture output.

---

## 10. What It IS

The thing that lets us say: `tr4sh_quake ingest G:\demos\*.dm_73 --auto` and
walk away for a week, returning to a full fragmovie corpus tagged by
mechanical + visual agent + user-preference signals, ready to edit.

The thing wolfcam was never designed to be, q3mme wasn't specialized
enough to become, and QL was never going to open source. Our own.

---

## Next Steps

After Split 1 closes, I:

1. Rename prior specs with `-merged-into-tr4sh-quake-manifesto` suffix
2. Invoke `writing-plans` skill on this manifesto
3. Split the plan into per-track sub-plans for parallel execution
4. Launch Track A sprint 1 (fork q3mme, build clean)

You: ship Split 1, then review the plan.
