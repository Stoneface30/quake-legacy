# Next Session Handoff — 2026-04-20 → next

**Previous session ended abandoned.** User: *"went to shit on this one."* Fresh session should start HERE, not where the last one was.

## What the user actually wants (direct quote, repeated)

*"focus on the ui and having the preview of all the clips you sent deep agent but didnt implemented anything so please do it"*

→ **First concrete deliverable: media-bin UI (Tier 2 editor Step 5).** A panel that lists all source AVI clips for the selected Part, with thumbnails + wavesurfer audio preview. Wired to a real `/api/editor/media-bin` endpoint. Shipped and committed in the first session.

Research stack proposed but NOT implemented (use these, pick the one that matches the panel):
- WebCodecs + `mp4box.js` — frame-accurate HTML playback of source AVIs (needs re-mux to mp4 if AVI doesn't decode natively)
- `wavesurfer.js` v7 (BSD-3, ~60 KB, zero deps, importmap/CDN-compatible) — per-clip audio preview
- `wavesurfer-multitrack` — only if we need a timeline; start with single-track per clip
- LiteGraph (jagenjo upstream MIT, NOT @comfyorg) — defer
- Theatre.js (Apache-2.0 core) — defer
- Tweakpane v4 — inspector panel, can come with Step 5

## Disk reality (as of 2026-04-20 afternoon)

- `output/Part4_v12_pathB_2026-04-19_2108.mp4` — 8.8 GB, **already reviewed by user** (do NOT re-ask for review on this file — see rule `WORKFLOW/rule-no-reviewing-already-reviewed-work.md`)
- `output/Part05_v1_PREVIEW_freshstems.mp4` — 2.0 GB
- Part 6 mp4 — **not on disk**
- All Parts 4-12: `chunks/` and `proxies/` empty — user nuked ~99 GB earlier.
- Source AVIs intact: T1 ~29-31/part, T2 ~36-40/part, T3 ~11-12/part — ~720 clips across Parts 4-12. **These are what the media-bin UI reads.**

## Do NOT do this session

1. **Do NOT re-run `scripts/batch_preview_4_to_12.sh`.** User has not re-approved it. Chunks are deliberately absent.
2. **Do NOT ask the user to review `output/Part4_v12_pathB_2026-04-19_2108.mp4`.** Already reviewed.
3. **Do NOT file another plan/spec/audit doc without shipping code first.** See `WORKFLOW/rule-research-is-not-shipping.md`.
4. **Do NOT assume state without checking.** Before any batch, run pre-flight inventory. See `WORKFLOW/rule-verify-disk-reality-before-batch.md`.

## What IS ready to pick up

### Tier 2 editor so far
- Step 4: `/editor` route + three-pane shell — commit `2448ab5c`
- Step 4b: Missing-chunks banner — commit `6086318a`
- Step 9: Render versions pane — commit `89ac47ea`
- **Step 5 (media-bin): NOT STARTED. This is your entry point.**

### Backend fix landed this session
- `phase1/normalize.py` — L154 atomic writes + L156 `-f mp4` on `.partial` + P1-Q v2 natural-speed audio. Commit `8c39aa54`. Already tested against a real Part 4 ffmpeg invocation before kill.

### Branch
`chore/learning-memory-curation-2026-04-19` — do NOT merge to main. User reviews PRs to protected branches; this branch has uncommitted docs/exploratory work and the Tier 2 editor commits are clean but not yet approved.

## Lessons to load at session start

New this session (read them before the first action):
- **L156** — ffmpeg + `.partial` → `-f mp4` (`Vault/rules/PLATFORM_QUIRK/rule-ffmpeg-partial-muxer-hint.md`)
- **L157** — no re-reviewing reviewed work (`Vault/rules/WORKFLOW/rule-no-reviewing-already-reviewed-work.md`)
- **L158** — research ≠ shipping (`Vault/rules/WORKFLOW/rule-research-is-not-shipping.md`)
- **L159** — verify disk before batch (`Vault/rules/WORKFLOW/rule-verify-disk-reality-before-batch.md`)

Project-specific feedback: `projects/G--QUAKE-LEGACY/memory/feedback_2026_04_20_session_collapse.md`.

Session note: `Vault/sessions/2026-04-20.md`.

## First action for the new session

1. Read the four rules above.
2. Read `docs/superpowers/specs/2026-04-20-editor-design.md` §Step 5 (media-bin).
3. Enumerate source clips: `ls "G:/QUAKE_LEGACY/QUAKE VIDEO/T{1,2,3}/Part04/"*.avi | wc -l` — prove the corpus is still there.
4. Brainstorm the media-bin UI ONLY IF the user asks; otherwise implement directly (`superpowers:brainstorming` is mandatory for *new* features — media-bin is already spec'd).
5. Ship a vertical slice in one commit: endpoint + panel + wavesurfer wiring + one working preview on Part 4. Commit it.
6. Show the user the panel rendering. THEN ask for feedback.
