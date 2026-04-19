# QUAKE LEGACY — Master Documentation Index
**Last Updated:** 2026-04-18 (session 3)
**Status:** Rule P1-R (three-track music: intro + main playlist + outro) and P1-S (beat-sync on transitions, never clip duration) added tonight. Music playlists dropped for Parts 4-12. Dual Part 4 v6 + Part 5 v6 render running in background as the new-rules baseline. Creative Suite v2 Step 2 still shipped · Engine PR #1 still open · Proto-73 port blueprint committed.
**Gates pending:** **ANN-1** (annotation stress test), **PR #1 review** (engine consolidation), **Part 4 v6 + Part 5 v6 watch-through** (replaces v5).

---

## START HERE

| What | File | Purpose |
|------|------|---------|
| **TOMORROW** | [sessions/2026-04-17-wrapup-TOMORROW.md](sessions/2026-04-17-wrapup-TOMORROW.md) | **Single-doc briefing: three gates, file-path cheatsheet, ingestion commands.** Read this first tomorrow morning. |
| **Awaiting-user decisions** | [`/HUMAN-QUESTIONS.md`](../HUMAN-QUESTIONS.md) | Source of truth for everything blocking on human input. |
| Creative Suite v2 plan | [superpowers/plans/2026-04-17-creative-suite-v2-plan.md](superpowers/plans/2026-04-17-creative-suite-v2-plan.md) | 9-step build plan · Steps 1-2 shipped · Gate ANN-1 pending |
| Proto-73 port review | [research/proto73-port-review-2026-04-17.md](research/proto73-port-review-2026-04-17.md) | Blueprint for Phase 3.5 Track A — port protocol 73 into q3mme |
| State review doc | [reviews/2026-04-17-phase1-2-3-5-state-for-user-review.md](reviews/2026-04-17-phase1-2-3-5-state-for-user-review.md) | Prior consolidated state report |
| Deep plan — current tracks | [superpowers/plans/2026-04-17-deep-plan-focus-and-tracks.md](superpowers/plans/2026-04-17-deep-plan-focus-and-tracks.md) | Active work tracks A-E |

---

## Canonical Design & Plan Docs

| What | File | Status |
|------|------|--------|
| Full system design | [specs/2026-04-16-quake-legacy-design.md](specs/2026-04-16-quake-legacy-design.md) | Current (user-updated 2026-04-17) |
| **Full phase plan (authoritative)** | [superpowers/plans/2026-04-16-full-phase-plan.md](superpowers/plans/2026-04-16-full-phase-plan.md) | Current (user-updated 2026-04-17 with inline comments) |
| Master plan + next steps | [superpowers/plans/2026-04-16-next-steps-master-plan.md](superpowers/plans/2026-04-16-next-steps-master-plan.md) | Reference |
| Phase 1 tribute completion plan | [superpowers/plans/2026-04-16-phase1-tribute-completion.md](superpowers/plans/2026-04-16-phase1-tribute-completion.md) | Reference |
| Phase 2 demo intelligence plan | [superpowers/plans/2026-04-16-phase2-demo-intelligence.md](superpowers/plans/2026-04-16-phase2-demo-intelligence.md) | Reference |
| Highlight criteria v1 (Gate P3-0 draft) | [specs/highlight-criteria-v1.md](specs/highlight-criteria-v1.md) | **Awaiting user answers in HUMAN-QUESTIONS §2** |

---

## Engine Research

| What | File |
|------|------|
| .dm_73 format deep dive | [reference/dm73-format-deep-dive.md](reference/dm73-format-deep-dive.md) *(in progress — agent running 2026-04-17)* |
| WolfcamQL command inventory | [reference/wolfcam-commands.md](reference/wolfcam-commands.md) |
| Phase 5 ComfyUI bugs/fixes | [reference/phase5-bugs-fixed.md](reference/phase5-bugs-fixed.md) |
| Frag scoring features | [research/frag-scoring-features.md](research/frag-scoring-features.md) |
| Phase 3 AI approaches | [research/phase3-ai-approaches.md](research/phase3-ai-approaches.md) |
| AI montage tool landscape 2026 | [research/ai-montage-tools-landscape-2026.md](research/ai-montage-tools-landscape-2026.md) |
| Project structure proposal v2 | [reference/project-structure-v2.md](reference/project-structure-v2.md) *(in progress — agent running 2026-04-17)* |

---

## Phase 1 — FFmpeg Assembly Pipeline

### Render Reviews
| File | Part | Verdict |
|------|------|---------|
| [Part 4 V1 Cinematic Review](review/part04_v1_cinematic_review.md) | Part 4 | FAILED — 6 issues fixed |
| [Part 4 V2 Punchy Review](review/part04_v2_punchy_review.md) | Part 4 | Pending re-render |
| [Part 4 V3 Zoom Review](review/part04_v3_zoom_review.md) | Part 4 | Pending re-render |
| [Part 4 V4 Hybrid Review](review/part04_v4_hybrid_review.md) | Part 4 | Pending re-render |
| [Review Index](review/INDEX.md) | All Parts | Running |

### Current Render Status
```
output/previews/
  part03_stylea_preview.mp4  ✓ 5:07 rendered (Cinematic) — user review pending re-render
  part03_styleb_preview.mp4  ✓ 5:07 rendered (Punchy) — user review pending re-render
  part03_stylec_preview.mp4  ✓ 5:07 rendered (Showcase) — user review pending re-render
  Part4_styleA_preview.mp4   ✓ Done
  Part4_styleB_preview.mp4   ✓ Done
  Part4_styleC_preview.mp4   ✓ Done
  Part4_v1_preview.mp4       ✓ Done (original — 6 failures fixed in code)
  Part4_v2_preview.mp4       ✓ Done
  Part4_v3_preview.mp4       ✓ Done
  Part4_v4_preview.mp4       ✓ Done
  Part5_styleA_preview.mp4   ✓ Done
  Part5_styleB_preview.mp4   ✓ Done
  Part5_styleC_preview.mp4   ✓ Done
```

### Fixes Applied (Part4 v1 → v2)
| Issue | Fix | File |
|-------|-----|------|
| No PANTHEON intro | `prepend_intro()` called after every assemble | `phase1/render_part4.py` |
| No music | Music auto-detect + warning | `phase1/render_part4.py` |
| Game audio 30% → 55% | `game_audio_volume = 0.55` | `phase1/config.py` |
| xfade glitches | Replaced with `concat` filter (hard cuts) | `phase1/pipeline.py` |
| Colors too pastel | contrast 1.3→1.55, sat 1.25→1.65 | `phase1/presets/grade_tribute.json` |
| Single FL angle | `all_angles()` uses ALL FL clips | `phase1/render_part4.py` |

---

## Phase 2 — Demo Extraction Engine (Architecture Complete)

| Document | Purpose |
|----------|---------|
| [Phase 2 Kill-Query Architecture](reference/phase2-kill-query-architecture.md) | WolfcamQL API, structs, recording windows |
| [WolfcamQL Command Reference](reference/wolfcam-commands.md) | All console commands + cvars |
| [WolfcamQL Kill-Query API](reference/wolfcam-kill-query-api.md) | Detailed syscall docs |

**Key decisions confirmed:**
- Recording windows: **8s pre-roll / 5s post-roll** (corrected from 3s/2s — too short)
- WolfcamQL has BUILT-IN frag database — no .dm_73 binary parsing needed
- Gate P3-0 required: define highlight criteria WITH user before any demo extraction
- **`trap_AddAt` is DISABLED** (`#if 0` in cg_syscalls.c) — use `at <servertime_float> <cmd>` in cap.cfg instead
- **Kill-query syscalls do NOT expose weapon** — get weapon via EV_OBITUARY snapshot events or UDT_json cross-reference
- `trap_GetRoundStartTimes()` → all CA round boundaries free in one call (max 256 rounds)

---

## Phase 3 — AI Cinematography Research

| Document | Purpose |
|----------|---------|
| [AI Approaches Survey](research/phase3-ai-approaches.md) | Scoring models, RL vs heuristic |
| [Frag Scoring Features](research/frag-scoring-features.md) | Feature engineering for highlight detection |

**Frag score formula:**
```
frag_score = weapon_weight[mod]
           + 0.2 * is_airshot(killTime)
           + 0.3 * multi_kill_bonus(killTime, window=3000ms)
           + 0.1 * low_health_attacker(killTime)
           + 0.4 * ca_round_bonus(roundNumber, numKillsInRound)
```

---

## Phase 5 — ComfyUI Texture Pipeline

| Document | Purpose |
|----------|---------|
| [ComfyUI Texture Pipeline](reference/comfyui-texture-pipeline.md) | Full pipeline: pk3 → upscale → img2img → pk3 |

**Status:** End-to-end test PASSED (22 textures, 68s, RTX 5060 Ti). pk3 at `phase5/04_pk3/zzz_photorealistic.pk3`. Two bugs to fix before deployment:
- **Path flattening** — `batch_comfyui.py` loses subdirectory structure → wrong pk3 internal paths, won't override stock textures
- **Alpha stripped** — `SaveImage` node outputs RGB only → HUD icon transparency lost (`icona_*`, `iconw_*`)
Both models auto-downloaded: `4x-UltraSharp.pth` + `control_v11f1e_sd15_tile.pth` ✓

---

## Game Asset Reference

| Document | Purpose |
|----------|---------|
| [Game Asset Catalog](reference/game-asset-catalog.md) | QL + Q3A pk3 contents — 9,290 QL files + 4,073 Q3A files cataloged |
| [Quake Asset Sources](reference/quake-asset-sources.md) | Where to find all game assets |
| [Map Catalog](reference/map-catalog.md) | 149 QL maps + 36 Q3A maps — **59 CA pool maps** for demo validation |
| [Weapon Models Catalog](reference/weapon-models-catalog.md) | All 11 weapons per game, every file + texture format |
| [Effects Catalog](reference/effects-catalog.md) | Particle/shader effects inventory |

---

## Source Repository Library (18 repos, ~1.17 GB)

`tools/quake-source/` — see [REPOS.md](../tools/quake-source/REPOS.md) for full docs

| Repo | Relevance |
|------|-----------|
| `wolfcamql-local-src` | Primary target — Phase 2/3 cgame extension |
| `wolfcamql-src` | Upstream reference |
| `quake3-source` | Q3A base engine — all engine syscall origins |
| `quake3e` | Modern Q3 engine — compat reference |
| `q3mme` | Movie-maker engine — FL camera inspiration |
| `q3vm` | QVM assembler/disassembler — inspect cgame.qvm directly |
| `wolfet-source` | wolfcam has ET origins — explains undocumented behaviors |
| `uberdemotools` | .dm_73 demo parsing reference |
| `qldemo-python` | Python demo parser |
| `ioquake3` | Open-source Q3 engine |
| `darkplaces` | Quake 1 engine (idtech1 reference) |
| `quake1-source` | Original Q1 source |
| `quake2-source` | Original Q2 source |
| `yamagi-quake2` | Annotated Q2 protocol — clarifies Q3 demo format decisions |
| `openarena-engine` | OA engine — Q3 variant |
| `openarena-gamecode` | OA gamecode — Q3 game logic reference |
| `gtkradiant` | Map editor — BSP/shader format docs |
| `demodumper` | Demo utilities |

**Engine lineage:** idtech1 (Q1) → idtech2 (Q2) → idtech3 (Q3/QL/wolfcam) — full chain present.

---

## Knowledge Graphs (graphify)

| Corpus | Nodes | Edges | Communities | HTML |
|--------|-------|-------|-------------|------|
| wolfcam/cgame | 1,691 | 3,112 | 70 | `game-dissection/graphify-out/graph.html` |
| wolfcam/game | 1,075 | 2,046 | 27 | `tools/quake-source/wolfcamql-local-src/code/game/graphify-out/graph.html` |
| q3mme/cgame | Done | 28 communities | 28 | `game-dissection/q3mme-cgame/graphify-out/graph.html` |
| q3mme/game | 1,204 | 2,274 | 29 | `game-dissection/q3mme-game/graphify-out/graph.html` |
| ioquake3/client | 647 | 1,184 | 18 | `game-dissection/ioquake3-client/graphify-out/graph.html` |
| q3a/game | 1,187 | 2,250 | 27 | `game-dissection/q3a-game/graphify-out/graph.html` |
| q3a/engine-core | 1,536 | 2,738 | 49 | `game-dissection/q3a-engine-core/graphify-out/graph.html` |
| qldemo-python | 145 | 208 | 12 | `game-dissection/qldemo-python/graphify-out/graph.html` |
| WolfWhisperer scripts | 10 | 5 | 5 | `game-dissection/wolfwhisperer-scripts/graphify-out/graph.html` |
| uberdemotools | 1,997 | 4,218 | 33 | `game-dissection/uberdemotools/graphify-out/graph.html` |
| **canonical engine tree** (2026-04-17) | 43,423 | 81,362 | 332 | `game-dissection/graphify-out/_canonical-2026-04-17/graphify-out/graph_top500_hubs.html` — 9,895 source files / 520 MB deduped by SHA-256 across 18 repos. Top hub: `HandleCommand()` in `radiant/mainframe.cpp` (deg 280). Full GraphRAG JSON (47 MB) at `graph.json`; interactive HTML is top-400-hub + 1-hop subgraph (graphify blocks HTML >5k nodes). |

**Querying:** Open any `graphify-out/graph.html` in browser → search nodes → click to explore communities.

---

## Visual Record — Screenshots

All captures in [`docs/visual-record/2026-04-16/`](visual-record/2026-04-16/)

| Screenshot | Description |
|------------|-------------|
| [cgame Knowledge Graph](visual-record/2026-04-16/01_cgame_knowledge_graph.png) | wolfcam/cgame — 1,535 nodes, 9 communities |
| [cgame Graph Zoomed](visual-record/2026-04-16/01b_cgame_graph_zoomed.png) | Close-up: node clusters, community bridges |
| [wolfcam/game Graph](visual-record/2026-04-16/02_wolfcam_game_graph.png) | wolfcam/game — 1,075 nodes, 27 communities |
| [Color Grade Before/After](visual-record/2026-04-16/03_color_grade_before_after.png) | Pastel v1 vs Punchy v2 grade comparison |
| [Project Structure](visual-record/2026-04-16/04_project_structure.png) | Full folder tree screenshot |
| [Milestone Card](visual-record/2026-04-16/05_milestone_card.png) | PANTHEON milestone: 2,277 demos · 1,535+ nodes · 12 parts |
| [Color Grade Comparison](visual-record/2026-04-16/color_grade_comparison.png) | Side-by-side grade values |

---

## Full Log Deep Dive

For in-depth review of any session, the full JSONL conversation logs are at:
```
C:\Users\Stoneface\.claude\projects\G--QUAKE-LEGACY\*.jsonl
```

Vault session notes (human-readable):
```
C:\Users\Stoneface\.claude\Vault\sessions\2026-04-16-quake-legacy-phase1-fixes.md
```

Graphify GRAPH_REPORT files (per-corpus analysis):
```
game-dissection/graphify-out/GRAPH_REPORT.md        ← wolfcam/cgame
tools/quake-source/.../game/graphify-out/GRAPH_REPORT.md  ← wolfcam/game
```

---

## Human Review Gates (Never Skip)

| Gate | Description | Status |
|------|-------------|--------|
| **P3-0** | Define highlight criteria WITH user before demo extraction | Pending |
| **P1-1** | Review clip lists before rendering | Active |
| **P1-2** | Watch 30s preview before full render | Active |
| **P1-3** | Watch full Part render before next Part | Active |
| **P2-1** | Review parser output on 10 sample demos | Planned |
| **P2-2** | Rate frags in dashboard before batch render | Planned |
| **P2-3** | Review 10 rendered clips before full batch | Planned |
| **P3-1** | AI-selected vs human-selected — measure agreement rate | Planned |

---

## Next Actions (Prioritized — 2026-04-17 session 2)

1. **Gate ANN-1** — Creative Suite v2: `uvicorn creative_suite.app:create_app --factory --port 8765` → open `/annotate` → mark 10 moments on Part 4 → confirm JSONL + SQLite agree
2. **Review PR #1** — engine consolidation: 9,895 source files / 520 MB canonical tree, SHA-256 dedup with authority order
3. **Watch Part 4 v5** full render (`output/full/part04_v5_*.mp4`) → approve title card · music mix · hard cuts · FP+FL contrast · full-length clips
4. **Proto-73 port decision** — read [proto73-port-review](research/proto73-port-review-2026-04-17.md), choose Path A (wolfcam-only until port) / B (port now) / C (hybrid)
5. **Creative Suite Steps 3-9** — queued: clip-picker, render queue, ComfyUI bridge, pack compiler (pending Step 2 merge)
6. **Gate P3-0** — highlight criteria session (remains open from prior sessions)

*Generated: 2026-04-17 session 2 | QUAKE LEGACY — AI Fragmovie Pipeline*
