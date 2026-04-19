# Claude tooling upgrade plan — Phase 1 acceleration
*2026-04-18 · scope: Phase 1 beat-match pipeline + demo-phase UI*

Opinionated survey of what Anthropic-official and community Claude tooling can actually move the needle on our specific stack (Python + FFmpeg + librosa + Beat This! + msaf + QL sound templates + Ollama/Qdrant + RTX 5060 Ti). Every item has a concrete day-1 task tied to our repo.

---

## 1. Immediate wins (this week, zero friction)

### 1.1 `frontend-design` plugin — already installed, under-used
**What**: Anthropic-official Claude Code plugin. It's already listed as active in our global `CLAUDE.md`. This IS "Claude Designer" as referenced in our repo context — see §4 below for the Designer clarification.
**Install**: already installed. Invoke via Skill tool: `Skill(skill="frontend-design:frontend-design")`.
**Day-1 task**: scaffold the creative_suite Phase 1 review dashboard (render list + A/B compare + clip preview) with it. Ask it for a "brutalist terminal / Quake console" aesthetic — it's explicitly designed to dodge generic Tailwind-purple defaults.
**URL**: https://claude.com/plugins/frontend-design · https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design
**Risk**: none. Zero install cost.

### 1.2 Video Analyzer skill (ffmpeg + vision fallback)
**What**: Community Claude Code skill that extracts frames from mp4/avi in batches of 15, runs vision analysis, produces timestamped reports. Two solid forks: `ItachiDevv/claude-video-analyzer` (FPS/smoothness checks, frame export) and `fabriqaai/ffmpeg-analyse-video-skill` (vision-summary per-frame).
**Install**: clone into `~/.claude/skills/video-analyzer/`. Needs ffmpeg (we have 8.1) + API key (we have it).
**Day-1 task**: point it at `output/part04_v10.mp4` with prompt *"find every seam where audio drift exceeds 40 ms OR title card has visible letter overlap OR console HUD is visible"*. This automates Rule P1-BB's sync audit and Rule P1-Y v2's title smoke test without watching 10 minutes by hand.
**URL**: https://github.com/ItachiDevv/claude-video-analyzer · https://github.com/fabriqaai/ffmpeg-analyse-video-skill
**Risk**: vision spend — cap at 1 frame/sec for a 10-minute Part = 600 frames ≈ $3-6 per audit. Use Opus 4.7 only for flagged frames, Haiku 4.7 for scan.

### 1.3 `mcp-music-analysis` (librosa-in-MCP)
**What**: MCP server by hugohow that wraps librosa + whisper — beat tracking, MFCC, spectral centroid, onset times — callable as tool calls. PyPI: `mcp-music-analysis`.
**Install**: `uv tool install mcp-music-analysis`, add to `~/.claude.json` MCP config.
**Day-1 task**: ask Claude to calibrate our `phase1/audio_onsets.py` template-matching confidence floor. Feed it 10 clips from each event class (rail/rocket/grenade/player_death), have it run MFCC cross-correlation via the MCP, and report the confidence distribution per class. This is the Rule P1-Z v2 tuning pass that we otherwise do by ear across 111 clips.
**URL**: https://github.com/hugohow/mcp-music-analysis · https://pypi.org/project/mcp-music-analysis/
**Risk**: librosa version pin — they're on 0.10.x, we're on 0.11. Isolate in its own venv.

### 1.4 ffmpeg-quality-metrics + easyVmaf (automated render diffing)
**What**: `ffmpeg-quality-metrics` CLI + `easyVmaf` Python wrapper. VMAF/PSNR/SSIM per frame between two mp4s with automatic sync.
**Install**: `pip install ffmpeg-quality-metrics` + ffmpeg must have `--enable-libvmaf` (ours does — check with `ffmpeg -filters | grep vmaf`).
**Day-1 task**: wire into `phase1/verify.py`. After every render, diff `part04_v{N}.mp4` vs `part04_v{N-1}.mp4`, flag any 1-sec window where VMAF drops > 6 points (= user-visible regression). Stops v10.1→v10.2 "what even changed?" discussions dead.
**URL**: https://pypi.org/project/ffmpeg-quality-metrics/ · https://github.com/gdavila/easyVmaf
**Risk**: false positives on legitimate intentional changes (e.g. new title card) — whitelist the intro range 0–13 s.

---

## 2. Medium-term wins (1-2 hour setup)

### 2.1 Video Editor MCP (`Kush36Agrawal/Video_Editor_MCP`) — FFmpeg-as-tool-calls
**What**: Claude tells ffmpeg what to do in natural language instead of us hand-crafting filter graphs. Bitscorp's `mcp-ffmpeg` is the alternative.
**Why for us**: filter-graph debugging (Rule P1-BB's xfade+concat audio drift hunt) is 60% of our bug time. Letting Claude iterate on filter graphs via tool calls cuts that loop from "edit → render 3 min → check" to "tool call → diff → tool call".
**Day-1 task**: reproduce the v10 title-card `[backdrop][text]overlay → [glow][b]blend=screen` chain via the MCP and diff against our hand-written version. If output matches, keep the MCP as our filter-graph scratchpad.
**URL**: https://github.com/Kush36Agrawal/Video_Editor_MCP · https://github.com/beambuilder/ffmpeg-mcp-server
**Risk**: MCP wrappers sometimes strip complex options (`geq`, `sendcmd`). Verify before betting on it.

### 2.2 Comfy-Pilot MCP (ConstantineB6) — ComfyUI as live workflow
**What**: MCP server + ComfyUI custom node. Claude can *see* the current graph, create/connect nodes, run the workflow, view outputs, download models from HF/Civitai. v1.0.24 as of March 2026.
**Why for us**: explicit plan in creative_suite to use ComfyUI for texture/asset upgrades + title card backdrops. Comfy-Pilot makes Claude a graph co-pilot, not a `curl` client.
**Install**: ComfyUI Registry install → `Claude Code MCP` tab. Needs local ComfyUI running (we're planning this anyway).
**Day-1 task** (after ComfyUI is up): generate a PANTHEON-style alternate intro backdrop (Rule P1-C "future: alternate PANTHEON intro versions") using a SDXL + AnimateDiff workflow — have Claude build the graph live.
**URL**: https://github.com/ConstantineB6/Comfy-Pilot
**Alternative**: `artokun/comfyui-mcp` (also Claude-Code-native, 31 tools).
**Risk**: first-run model downloads can be 10-30 GB. Preflight disk.

### 2.3 `visual-regression-tester` plugin (Percy/Chromatic/BackstopJS)
**What**: Claude Code plugin for UI visual regression. More relevant once creative_suite frontend exists.
**Day-1 task**: park until creative_suite has a UI. Then wire BackstopJS against the dashboard pages so Phase 2 UI iterations don't silently break the review gate flow.
**URL**: https://claudecodeplugins.io/plugins/visual-regression-tester/
**Risk**: overkill pre-UI.

---

## 3. Strategic bets (demo phase / UI / Phase 2)

### 3.1 Claude Code Video skill + Opus 4.7 high-res vision
**What**: Opus 4.7 accepts images up to 2,576 px long-edge — >3× previous limit. Combined with the Video skill's frame extraction, a single vision call can ingest a 1920×1080 60fps frame at native resolution.
**Use in Phase 2**: feed UDT-extracted demo frames directly to vision for highlight scoring. This is the FT-2 "highlight criteria v2" feedback loop — Claude looks at the frag, not just the entity stream.
**Risk**: latency + cost. Keep to flagged frags only (weight ≥ 0.90).

### 3.2 Computer Use (Q1 2026 restructured batching)
**What**: rolling visual context window, half the action latency. Useful for WolfcamQL automation (Phase 2) where the game window is the only source of truth.
**Day-1 task**: park until Phase 2 / FT-4 (Ghidra pass) completes. Then use Computer Use as a fallback for WolfcamQL commands that have no `.cfg` entry point.

### 3.3 Ollama + gemma3:4b-vision local tier
**What**: our own local vision model, already installed.
**Why now**: $0 per frame = viable for full-render sweeps (600+ frames). Use as tier-0 scan, promote to Claude vision on flagged frames.
**Day-1 task**: prompt-engineer gemma3:4b against 20 known-bad frames (console-visible, title-overlap, audio-drift artifacts). Measure recall vs Claude vision; if > 0.7, use as default scanner.

---

## 4. Claude Designer — WHAT IT IS, HOW TO START

The name is ambiguous. Two distinct things both get called this:

### 4a. `frontend-design` plugin (what our CLAUDE.md actually means)
- **This is the one in our plugin list.** Claude Code plugin, already installed globally.
- **How to start**: in any Claude Code session, invoke via the Skill tool:
  `Skill(skill="frontend-design:frontend-design")`
  or simply say *"use frontend-design to build X"* — the skill auto-activates on frontend work.
- **First task for us**: scaffold creative_suite Phase 1 review dashboard. Brief: *"Brutalist Quake-console aesthetic. Monospace (IBM Plex Mono or JetBrains Mono), ember-orange accent `#d4621a`, grid-breaking asymmetric layout. Pages: render list, A/B compare (two `<video>` tags synced to same timestamp), clip burn-in preview (per Rule P1-D)."*
- **URL**: https://claude.com/plugins/frontend-design

### 4b. Claude Design (the product, launched 2026-04-17)
- **Different thing.** Web product at claude.com, Opus 4.7-powered, for slides/prototypes/one-pagers. Research preview for Pro/Max/Team/Enterprise.
- **How to start**: log into claude.com on Pro+, Design appears in the product nav (new-product rollout — may need to toggle "research previews" in settings).
- **Relevance to us**: useful for pitch/marketing deliverables around Phase 4 public release (quake-legacy pip package announcement one-pager, PANTHEON brand sheet). NOT useful for the render pipeline itself.
- **URL**: https://techcrunch.com/2026/04/17/anthropic-launches-claude-design-a-new-product-for-creating-quick-visuals/

**Recommendation**: when our CLAUDE.md says "Claude Designer", treat it as the **plugin (4a)**. The **product (4b)** is a separate marketing-surface tool for later.

---

## 5. What we already have and are under-using

- **superpowers:brainstorming** — we skip this before 60% of feature sessions despite it being MANDATORY per global CLAUDE.md. Fix: one-line re-read at each session start.
- **context7 MCP** — underused for ffmpeg filter docs. Every filter-graph session should start with `resolve-library-id ffmpeg` → `query-docs xfade`. This catches deprecated flags faster than web search.
- **Playwright MCP** — we have it but don't use it for visual record capture (Rule VIS-1). Should be auto-capturing the render dashboard after each Part renders.
- **n8n webhooks** — we pipe file changes to Qdrant but don't pipe `output/partNN_sync_audit.json` to Telegram. One n8n workflow = "ship gate failed" alerts without checking logs.
- **Qdrant RAG** — zero Phase 1 rendering knowledge indexed. The Rule P1-* ledger in CLAUDE.md should live in Qdrant for semantic lookup ("what rule covers music volume?").

---

## 6. NOT worth it (explicitly ruled out)

- **Premiere Pro MCP** (`toonyai-premiere-mcp`) — we don't use Premiere. Our whole pipeline is scripted ffmpeg. Skip.
- **ComfyUI Cloud MCP (official)** — cloud GPUs at $ per run. We have an RTX 5060 Ti. Use Comfy-Pilot (local) instead.
- **Building a custom ffmpeg MCP ourselves** — three working ones already exist (Kush, beambuilder, bitscorp). Fork, don't rebuild.
- **Impeccable / other designer-adjacent skill packs** — they're fine but `frontend-design` already covers our Phase 1.5 UI scope.
- **Video Editor MCP for the final render path** — we have hand-tuned filter graphs under strict rules (P1-BB, P1-Y v2, P1-EE). An MCP is a *scratchpad* for experimentation, NOT the ship pipeline. Do NOT swap out `render_part_v6.py` for tool calls.

---

## Recommended order of operations

1. Day 1 morning: install `mcp-music-analysis` + run confidence-floor calibration on our QL template library → Rule P1-Z v2 gets objective thresholds.
2. Day 1 afternoon: install `claude-video-analyzer` skill + run it against latest Part 4 v10 render → automates P1-BB sync audit.
3. Day 2: wire `ffmpeg-quality-metrics` into `phase1/verify.py` → every future v{N} render auto-diffs vs v{N-1}.
4. Day 3: invoke `frontend-design` plugin to scaffold creative_suite dashboard.
5. Week 2: stand up local ComfyUI + Comfy-Pilot → alternate PANTHEON intro backdrop generation.

Budget impact: ~$20-40/week in Claude vision calls once video analyzer is live. Offset by 2-4 hours saved per render iteration.

---

## Sources

- https://claude.com/plugins/frontend-design
- https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design
- https://techcrunch.com/2026/04/17/anthropic-launches-claude-design-a-new-product-for-creating-quick-visuals/
- https://github.com/ItachiDevv/claude-video-analyzer
- https://github.com/fabriqaai/ffmpeg-analyse-video-skill
- https://github.com/hugohow/mcp-music-analysis
- https://pypi.org/project/mcp-music-analysis/
- https://pypi.org/project/ffmpeg-quality-metrics/
- https://github.com/gdavila/easyVmaf
- https://github.com/Kush36Agrawal/Video_Editor_MCP
- https://github.com/beambuilder/ffmpeg-mcp-server
- https://github.com/ConstantineB6/Comfy-Pilot
- https://github.com/artokun/comfyui-mcp
- https://claudecodeplugins.io/plugins/visual-regression-tester/
- https://vizzly.dev/blog/claude-code-ai-visual-testing/
- https://code.claude.com/docs/en/desktop
