# Claude Designer — Liaison Doc
**Date:** 2026-04-19
**From:** Claude Code (G:\QUAKE_LEGACY, `creative-suite-v2-step2` branch)
**To:** Claude Designer (parallel chat)
**Purpose:** Single source of truth for the Phase 1 Cinema Suite ship state. Read this first — everything below is verified on disk and in git.

---

## 1. Where the repo stands right now

**Branch:** `creative-suite-v2-step2` (pushed to `origin` after this doc)
**Base:** `main` (last user-approved)
**Clean?** Cinema Suite implementation + Ghidra sandbox are committed. Unrelated `CLAUDE.md` + `game-dissection/engines/_diffs/` changes are outside this ship and will be handled in a separate commit.

**Commit chain (read bottom-up):**
```
f3b3bbdb  fix(cinema): address final code-review findings           ← HEAD
bdf96d29  feat(ghidra): FT-4 sandbox scaffold + preliminary inventory
9df73746  ship: cinema suite Phase D gate - Tier A draft + Tier B scrub
c1c3ec50  feat(cinema): EngineSupervisor subprocess + stdin seek + BitBlt grab
3aa03fe0  feat(cinema): Panel 7 Tier A DRAFT PREVIEW + SSE + mp4 playback
3e91b361  feat(cinema): POST /preview Tier A job wiring
8d0f1606  feat(cinema): write_preview_cfg with degraded-quality cvars
c73a7d85  feat(cinema): music track swap dropdowns + override file
634c2eaf  feat(cinema): seam-drag onto downbeat → beat_snapped_offsets
a6d73cbd  feat(cinema): per-clip slow/head/tail override endpoints + UI
b2dd3bff  feat(cinema): overrides file I/O (slow/trim/section_role)
f3d7e2d5  feat(cinema): REBUILD button + SSE live log wire-up
```

**Verification:** 132 tests pass · pyright 0 errors on cinema files · all 25 plan tasks shipped + all 4 code-review findings fixed.

---

## 2. What Phase 1 Cinema Suite actually does (end-to-end)

A FastAPI + vanilla-JS web UI at `creative_suite/` that lets the user drive the Phase 1 fragmovie pipeline without editing text files.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Browser (importmap + Three.js CDN)            │
│                                                                  │
│   Panel 1  Part picker        Panel 5  Seam drag→downbeat       │
│   Panel 2  Clip sequence      Panel 6  Music track swap         │
│   Panel 3  Per-clip overrides Panel 7  Tier-A mp4 preview       │
│   Panel 4  Waveform + flow    Panel 8  Tier-B engine scrub      │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP + SSE + WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI (uvicorn 127.0.0.1:8001)   creative_suite/api/phase1.py │
│                                                                  │
│   GET  /parts, /parts/{n}/artifacts, /flow-plan, /waveform       │
│   PUT  /flow-plan, /overrides, /music-override                   │
│   POST /rebuild     → JobQueue (depth=1, 409 on busy)            │
│   POST /preview     → JobQueue  (Tier A wolfcam+ffmpeg)          │
│   GET  /jobs/{id}/events  (SSE, auto-close on done/failed)       │
│   WS   /parts/{n}/engine  (Tier B live scrub, JPEG frames)       │
└─────────────────────────────────────────────────────────────────┘
                              │ subprocess
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  phase1/render_part_v6.py    (the existing full-quality render)  │
│  wolfcamql.exe               (preview + engine supervisor)       │
│  ffmpeg.exe                  (AVI→mp4 transcode)                 │
│  output/.git                 (flow_plan.json version history)    │
└─────────────────────────────────────────────────────────────────┘
```

**Spec §11.1 hook** (the one-line addition that closes the loop):
`render_part_v6.py` reads `part{NN}_flow_plan.json` → extracts `beat_snapped_offsets[]` → overrides `body_seam_offsets[i]` before `assemble_body_with_xfades`. Bounds-checked (negative seam_idx filtered), applied-count logged, byte-identical render when override list is empty.

---

## 3. Key architectural decisions (so you don't re-relitigate them)

| Decision | Choice | Why |
|---|---|---|
| **Stack** | FastAPI + uvicorn + SQLite (WAL) | Matches existing Phase 1 Python, no new language runtime |
| **Frontend deps** | importmap + Three.js CDN, no npm (YET) | Ship velocity. User unlocked npm 2026-04-19 — see §6 |
| **Job concurrency** | Single-worker `asyncio.Queue`, depth=1, `RuntimeError → HTTP 409` | User never runs two renders at once; simplicity > queueing |
| **Preview tier split** | Tier A = wolfcam+ffmpeg mp4 draft (~45s). Tier B = live engine scrub via WebSocket | Tier A = "show me the cut", Tier B = "let me scrub to the frame" |
| **Engine capture** | `PIL.ImageGrab` BitBlt @ 4 Hz, `asyncio.Queue(maxsize=4)` evict-oldest | No engine patching needed; window grab is good enough for scrub |
| **Version history** | Git sub-repo at `output/.git`, tags `part{NN}/{tag}` | Human-readable diffs, no custom storage layer |
| **Mock gates** | `CS_REBUILD_MOCK`, `CS_PREVIEW_MOCK`, `CS_ENGINE_MOCK` env vars | Tests run without wolfcam/ffmpeg binaries |
| **Subprocess safety** | `terminate() → wait_for(3s) → kill()` on CancelledError/shutdown | Wolfcam is a GUI — orphan processes would hang the box |

---

## 4. Files you should know about

**API layer** (`creative_suite/api/`):
- `phase1.py` — all routes + WebSocket handler
- `_render_worker.py` — `JobQueue` (async single-worker) + SSE buffer
- `_rebuild_job.py` — spawns `render_part_v6.py` subprocess, tails stdout
- `_preview_job.py` — Tier A orchestrator (wolfcam+ffmpeg)
- `_git_flow.py` — `save_and_tag()` with refname validation
- `_waveform.py` — peaks computation for scrub bar

**Engine layer** (`creative_suite/engine/`):
- `supervisor.py` — `EngineSupervisor` class (start/stop/seek/next_frame)

**Overrides** (`creative_suite/overrides/`):
- `file_io.py` — reads/writes `partNN_overrides.txt` (slow, head_trim, tail_trim, section_role)

**Capture** (`creative_suite/capture/`):
- `gamestart.py` — both `write_gamestart_cfg` (ship) and `write_preview_cfg` (Tier A). Injection-hardened: rejects `;` and `\n` in demo_name / seek_clock / quit_at.

**Frontend** (`creative_suite/frontend/`):
- `index.html` — importmap + panel layout
- `app-cinema.js` — wires up panels, WebSocket, SSE
- `panel-preview.js` — Tier A SSE subscriber + Tier B WebSocket scrub
- `md3viewer/` — three.js MD3 model viewer (used for Panel 8 hover preview)

**Modified outside cinema_suite** (minimal):
- `phase1/render_part_v6.py` — §11.1 hook (15 lines, additive, guarded)

---

## 5. What ships "live" vs "mock"

| Component | Live path | Mock path | How to flip |
|---|---|---|---|
| Rebuild | Spawns `render_part_v6.py` | Emits fake SSE events | `CS_REBUILD_MOCK=1` |
| Tier A preview | wolfcam → AVI → ffmpeg mp4 | Writes 8-byte ftyp stub | `CS_PREVIEW_MOCK=1` |
| Tier B engine | wolfcam subprocess + BitBlt grab | Returns `b"\xff\xd8\xff\xe0mockjpeg"` | `CS_ENGINE_MOCK=1` |

**Ship Gate D is tested via mocks**; real-engine latency validation (scrub→frame ≤300ms, Tier A mp4 ≤45s) is a user hands-on check that was scoped out of automated tests.

---

## 6. npm allowance policy (NEW — 2026-04-19)

User unlocked npm packages. Did NOT apply mid-Phase-D to preserve ship velocity. **Vetting checklist for any future npm dep:**

1. ✅ License is OSS-approved (MIT, BSD-2/3, Apache-2.0, ISC) — reject AGPL, unknown
2. ✅ `npm audit` clean at install time (no high/critical)
3. ✅ Snyk advisory-DB lookup clean
4. ✅ Pinned version (no `^` or `~`)
5. ✅ Source on GitHub + >1k stars OR >3 years maintained
6. ✅ No network calls at build-time (pure lib only)

**First candidate queued:** `wavesurfer.js` v7 (BSD-3, ~60KB gzipped, zero deps) for Panel 4 waveform upgrade. To be introduced in a dedicated follow-up commit, not mixed with Phase-D.

---

## 7. Demo corpus status (unblocks Phase 2)

User extracted the 7z archive 2026-04-19. **6,465 `.dm_73` files · 13.19 GB · 11 anonymized players** now on disk at the primary corpus path. FT-1 (custom C++ parser) and FT-5 (nickname regex dictionary) are no longer blocked.

Secondary corpus (`G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\wolfcam-ql\demos\`, 948 demos) stays as smoke-test set.

---

## 8. Ghidra FT-4 findings so far (background agent, 2026-04-19)

Committed in `bdf96d29` under `game-dissection/ghidra/`:
- ✅ Binary inventory (`reports/_binary-inventory.md`) — 7 targets identified
- ✅ Preliminary PE probe (`scripts/pe_probe.py` — runs today, no Ghidra required)
- ✅ `qagamex86.dll` has DWARF + STABS debug info — **not stripped**, symbol-rich
- ✅ MOD_* enum seed (34 entries, confirmed protocol-73 via MOD_HMG + MOD_RAILGUN_HEADSHOT)
- ✅ EV_* enum seed (103 entries)
- ✅ WolfcamQL capture cvar seed (r_mode, com_maxfps, video avi, seekclock, ...)

**Blockers for full dissection (user actions):**
- Install Ghidra 11.3 + JDK 21
- Extract `WOLF WHISPERER/Wolf Whisperer.rar` (currently zipped, contains main binary)
- Decision: build or drop UDT_json (UberDemoTools) and q3mme reverse targets

---

## 9. Where to pick up (Designer, this is for you)

### Things you can start on TODAY without waiting for me

**A. Visual design system for the Cinema Suite UI**
- Current: vanilla HTML, zero theming, functional not pretty
- Needed: PANTHEON brand alignment — grey/silver temple aesthetic per `FRAGMOVIE VIDEOS/IntroPart2.mp4`
- Files to touch: `creative_suite/frontend/index.html` + create `creative_suite/frontend/pantheon.css`
- Constraint: stay on importmap+CDN until wavesurfer.js follow-up commit

**B. Panel 7/8 UX polish**
- Tier A preview player: currently bare `<video>`. Needs: scrub thumbnails, seam markers overlay, "jump to next seam" hotkeys.
- Tier B engine scrub: currently raw base64 `<img>`. Needs: frame counter, time ruler, scrub-by-drag on the frame.

**C. Storyboard mockups for Part 4/5/6 final render approval flow**
- User is the judge; we need a "here's the v10 render + diff against v9" UI.
- Inputs: `output/partNN_renders/` mp4 files + `output/partNN_flow_plan.json` git diff.

### Things that need me to ship first

- **wavesurfer.js integration** — I'll land this in a follow-up, then you can design the waveform panel properly
- **Phase 2 FT-1 parser output** — once C++ parser ships, dashboard gets real frag data (not mock fixtures)
- **Ghidra finds** — when `qagame` enums are fully mapped, Phase 2 scoring model unblocks

### Things that need the user (neither of us)

- Ship Gate D real-engine hands-on (scrub→frame latency)
- Ghidra install + `.rar` extraction (blocks FT-4 beyond preliminary)
- Final review of Parts 4/5/6 v10 renders (blocks Parts 7-12)

---

## 10. Ground rules for our collaboration

1. **Read this doc + `CLAUDE.md` before making changes.** Both of us are rebuilt fresh each session; this file is how we stay coordinated.
2. **Never commit to `main` or `master`.** Only the user merges. We push to feature branches only.
3. **Never commit player names, Steam IDs, `.dm_73`/`.avi`/`.mp4`/`.db`/`.env`.** Public repo — user checks `.gitignore` on every push.
4. **Hard rules live in `CLAUDE.md`.** If you see a rule ID (P1-G v5, ENG-1, etc.) — that's non-negotiable. Check `CLAUDE.md` before overriding anything.
5. **Visual record per VIS-1:** every significant output gets screenshotted to `docs/visual-record/YYYY-MM-DD/`. Applies to you too.
6. **If you find me wrong, capture-lesson it.** Global skill, writes to `Vault/learnings.md` + project memory. Don't just fix silently.

---

## 11. Quick-start for you

```bash
# Get the branch
cd G:/QUAKE_LEGACY
git fetch origin creative-suite-v2-step2
git checkout creative-suite-v2-step2

# Sanity test
python -m pytest creative_suite/ -x --tb=short
# Expected: 132 passed

# Launch the suite
cd creative_suite
python -m uvicorn main:app --reload --port 8001
# Open http://127.0.0.1:8001

# Mock mode (no wolfcam/ffmpeg needed)
set CS_REBUILD_MOCK=1
set CS_PREVIEW_MOCK=1
set CS_ENGINE_MOCK=1
python -m uvicorn main:app --reload --port 8001
```

---

**End of liaison doc.** Questions → drop them in your chat and the user will relay, OR append a section at the bottom of this file and push to the same branch. Don't edit above the "End of liaison doc" line without me seeing it first.
