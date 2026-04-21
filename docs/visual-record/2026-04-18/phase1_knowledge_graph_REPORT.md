# Graph Report - G:/QUAKE_LEGACY/_graphify_corpus  (2026-04-18)

## Corpus Check
- Corpus is ~46,537 words - fits in a single context window. You may not need a graph.

## Summary
- 128 nodes · 125 edges · 31 communities detected
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 20 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `Part 4 v9 Audio Foundation Review` - 14 edges
2. `Feedback: Part 4 Review 2026-04-17` - 9 edges
3. `Rule P1-Z Game-Audio Beat Sync` - 8 edges
4. `QUAKE LEGACY Memory Index` - 7 edges
5. `P1-Z v2 Recognized Game Event Peak` - 6 edges
6. `phase1/render_part_v6.py` - 6 edges
7. `Feedback: Gate 1 Review` - 6 edges
8. `Installed Tooling Inventory 2026-04-18` - 6 edges
9. `Feedback: Command Center + Engine Pivot` - 5 edges
10. `P1-L v1 Trim 1s head / 2s tail` - 4 edges

## Surprising Connections (you probably didn't know these)
- `Perf Tuning 2026-04-18` --conceptually_related_to--> `phase1/render_part_v6.py`  [INFERRED]
  _graphify_corpus/perf-tuning-2026-04-18.md → phase1/render_part_v6.py
- `P1-L v2 FP/FL-Differentiated Head Trim` --defined_in--> `phase1/render_part_v6.py`  [EXTRACTED]
  _graphify_corpus/00_CLAUDE.md → phase1/render_part_v6.py
- `P1-U Tier Interleave for Pacing` --defined_in--> `phase1/render_part_v6.py`  [EXTRACTED]
  _graphify_corpus/00_CLAUDE.md → phase1/render_part_v6.py
- `P1-BB Split Graphs + PCM WAV Intermediates` --defined_in--> `phase1/render_part_v6.py`  [EXTRACTED]
  _graphify_corpus/00_CLAUDE.md → phase1/render_part_v6.py
- `P1-EE Event-Localized Speed Effects` --defined_in--> `phase1/render_part_v6.py`  [EXTRACTED]
  _graphify_corpus/00_CLAUDE.md → phase1/render_part_v6.py

## Communities

### Community 0 - "Project Charter + Feedback Spine"
Cohesion: 0.12
Nodes (18): QUAKE LEGACY CLAUDE.md, Feedback: Command Center + Engine Pivot, Feedback: Concat-Demuxer Render Path, Feedback: Editing Style Preference, Feedback: Gate 1 Review, Feedback: Part 4 V1 Review Fixes, Vault learnings.md L-rules Ledger, QUAKE LEGACY Memory Index (+10 more)

### Community 1 - "Game Event Recognition"
Cohesion: 0.16
Nodes (17): Event grenade_explode, Event lg_hit, Event player_death, Event rail_fire, Event rocket_impact, phase1/audio_onsets.py, phase1/beat_sync.py, phase1/music_structure.py (+9 more)

### Community 2 - "Transitions + Trim Rules"
Cohesion: 0.18
Nodes (14): Feedback: Part 4 Review 2026-04-17, phase1/effects.py, P1-H v1 No Transitions Hard Cuts, P1-H v3 Short 0.15s Seam Xfades, P1-H v4 Visible 0.4s Transitions, P1-L v1 Trim 1s head / 2s tail, P1-L v2 FP/FL-Differentiated Head Trim, P1-L v3 Tail 2.5s + Short-Clip Floor (+6 more)

### Community 3 - "Music Stitching + Beat Sync"
Cohesion: 0.21
Nodes (13): phase1/music_stitcher.py, phase1/render_part_v6.py, phase1/sidechain.py, Perf Tuning 2026-04-18, Audio Montage Research 2026-04-18, Rule P1-AA Full-Track Queue, Rule P1-BB Split Graphs PCM WAV CFR, P1-AA v1 Full-Track Queue + afade (+5 more)

### Community 4 - "v10 Audio Foundation Learnings"
Cohesion: 0.2
Nodes (10): L111, L112, L113, L114, L115, L116, L117, L118 (+2 more)

### Community 5 - "Engine + Demo Parser"
Cohesion: 0.2
Nodes (10): Installed Tooling Inventory 2026-04-18, MCP Setup Notes 2026-04-18, phase2/dm73parser, Protocol-73 Port Review 2026-04-17, FT-1 Custom dm73 Parser, FFmpeg, Ghidra, q3mme (+2 more)

### Community 6 - "Audio Mix Levels (P1-G evolution)"
Cohesion: 0.29
Nodes (7): Feedback: Audio and Transitions, phase1/audio_levels.py, P1-G v1 Game Audio 55% Under Music, P1-G v2 Music Halved Game Full, P1-G v3 Music 0.30 Layered Entire Output, P1-G v4 Music 0.20 + ebur128 Gate, P1-G v5 Music After PANTHEON + Fade-In

### Community 7 - "Title Card Design"
Cohesion: 0.47
Nodes (6): phase1/title_card.py, Rule P1-Y v2 Quake Title Card, P1-T FL-Backdropped Title Card, P1-Y v1 Bebas Neue Title Card, P1-Y v2 Quake-Style Title Card, VIS-1 Always Capture Visual Records

### Community 8 - "Render Quality Ceiling"
Cohesion: 0.67
Nodes (3): Encoder Recommendation 2026-04-17, FT-6 FFmpeg Encoder Benchmark, P1-J Final Render Quality Ceiling

### Community 9 - "Phase 3.5 AI Intros"
Cohesion: 0.67
Nodes (3): Phase 3 AI Approaches, FT-3 Phase 3.5 3D Intro Lab, ComfyUI

### Community 10 - "Steam Pak Asset Truth"
Cohesion: 0.67
Nodes (3): Project Asset Vision, Rule ENG-1 Steam Paks Source of Truth, Steam Pak Inventory 2026-04-17

### Community 11 - "Phase 2 Demo Recording"
Cohesion: 0.67
Nodes (3): Phase 2 Recording Windows Feedback, Project Editing Pattern, Project Quake Legacy Context

### Community 12 - "Highlight Scoring"
Cohesion: 1.0
Nodes (2): Frag Scoring Features, FT-2 Highlight Criteria v2

### Community 13 - "Visual Documentation"
Cohesion: 1.0
Nodes (2): Visual Documentation Rule, Rule VIS-1 Visual Documentation

### Community 14 - "Music Catalog"
Cohesion: 1.0
Nodes (1): P1-F Music Catalog

### Community 15 - "Golden Rule"
Cohesion: 1.0
Nodes (1): P1-I Golden Rule Frag+Effect+Music

### Community 16 - "Three-Track Music"
Cohesion: 1.0
Nodes (1): P1-R Three-Track Music Structure

### Community 17 - "Beat Snap + Silence (deferred)"
Cohesion: 1.0
Nodes (1): P1-V Beat-Snap + Silence-Detect (Deferred)

### Community 18 - "PANTHEON Intro Timing"
Cohesion: 1.0
Nodes (1): P1-X PANTHEON Intro 5s

### Community 19 - "Highlight Criteria Gate"
Cohesion: 1.0
Nodes (1): P3-A Own Highlight Criteria Before Extraction

### Community 20 - "WolfcamQL Command Inventory"
Cohesion: 1.0
Nodes (1): P3-B WolfcamQL Command Inventory

### Community 21 - "FT-1 dm_73 Parser"
Cohesion: 1.0
Nodes (1): FT-1 Custom C++ dm_73 Parser

### Community 22 - "FT-2 Criteria v2"
Cohesion: 1.0
Nodes (1): FT-2 Highlight Criteria v2

### Community 23 - "FT-3 3D Intro Lab"
Cohesion: 1.0
Nodes (1): FT-3 Phase 3.5 3D Intro Lab

### Community 24 - "FT-4 Ghidra Pass"
Cohesion: 1.0
Nodes (1): FT-4 Ghidra Every Executable

### Community 25 - "FT-5 Nickname Dict"
Cohesion: 1.0
Nodes (1): FT-5 Nickname Dictionary

### Community 26 - "FT-7 Audio Mix 55%"
Cohesion: 1.0
Nodes (1): FT-7 Game Audio Mix 55%

### Community 27 - "Experiment Module"
Cohesion: 1.0
Nodes (1): phase1/experiment.py

### Community 28 - "Claude Tooling Upgrade"
Cohesion: 1.0
Nodes (1): Claude Tooling Phase1 Upgrade 2026-04-18

### Community 29 - "Demo Dedup"
Cohesion: 1.0
Nodes (1): Demo Dedup Report 2026-04-17

### Community 30 - "Tier Hierarchy Correction"
Cohesion: 1.0
Nodes (1): Tier Hierarchy Correction

## Knowledge Gaps
- **68 isolated node(s):** `P1-B Intro/Outro Clip Selection`, `P1-D Preserve Clip Names in Previews`, `P1-E Phase 1 Effects Scope`, `P1-F Music Catalog`, `P1-G v5 Music After PANTHEON + Fade-In` (+63 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Highlight Scoring`** (2 nodes): `Frag Scoring Features`, `FT-2 Highlight Criteria v2`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Visual Documentation`** (2 nodes): `Visual Documentation Rule`, `Rule VIS-1 Visual Documentation`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Music Catalog`** (1 nodes): `P1-F Music Catalog`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Golden Rule`** (1 nodes): `P1-I Golden Rule Frag+Effect+Music`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Three-Track Music`** (1 nodes): `P1-R Three-Track Music Structure`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Beat Snap + Silence (deferred)`** (1 nodes): `P1-V Beat-Snap + Silence-Detect (Deferred)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PANTHEON Intro Timing`** (1 nodes): `P1-X PANTHEON Intro 5s`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Highlight Criteria Gate`** (1 nodes): `P3-A Own Highlight Criteria Before Extraction`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `WolfcamQL Command Inventory`** (1 nodes): `P3-B WolfcamQL Command Inventory`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `FT-1 dm_73 Parser`** (1 nodes): `FT-1 Custom C++ dm_73 Parser`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `FT-2 Criteria v2`** (1 nodes): `FT-2 Highlight Criteria v2`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `FT-3 3D Intro Lab`** (1 nodes): `FT-3 Phase 3.5 3D Intro Lab`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `FT-4 Ghidra Pass`** (1 nodes): `FT-4 Ghidra Every Executable`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `FT-5 Nickname Dict`** (1 nodes): `FT-5 Nickname Dictionary`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `FT-7 Audio Mix 55%`** (1 nodes): `FT-7 Game Audio Mix 55%`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Experiment Module`** (1 nodes): `phase1/experiment.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Claude Tooling Upgrade`** (1 nodes): `Claude Tooling Phase1 Upgrade 2026-04-18`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Demo Dedup`** (1 nodes): `Demo Dedup Report 2026-04-17`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Tier Hierarchy Correction`** (1 nodes): `Tier Hierarchy Correction`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `phase1/render_part_v6.py` connect `Music Stitching + Beat Sync` to `Transitions + Trim Rules`?**
  _High betweenness centrality (0.238) - this node is a cross-community bridge._
- **Why does `P1-L v2 FP/FL-Differentiated Head Trim` connect `Transitions + Trim Rules` to `Music Stitching + Beat Sync`?**
  _High betweenness centrality (0.227) - this node is a cross-community bridge._
- **Why does `Feedback: Part 4 Review 2026-04-17` connect `Transitions + Trim Rules` to `Project Charter + Feedback Spine`, `Audio Mix Levels (P1-G evolution)`?**
  _High betweenness centrality (0.222) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `P1-Z v2 Recognized Game Event Peak` (e.g. with `P1-CC v2 Flow-Driven Cut Placement` and `Beatmaker Research 2026-04-18`) actually correct?**
  _`P1-Z v2 Recognized Game Event Peak` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `P1-B Intro/Outro Clip Selection`, `P1-D Preserve Clip Names in Previews`, `P1-E Phase 1 Effects Scope` to the rest of the system?**
  _68 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Project Charter + Feedback Spine` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._