# Learning-Memory Curation Plan — 2026-04-19

**Goal (user quote):** *"Try to reread and reorder learning memory so we have the best base for everything and not only overinformation that is never used."*

**Mode:** READ-ONLY analysis. No file edits performed. All claims cite `file:line`.

**Scope (strict):** only `G:/QUAKE_LEGACY/CLAUDE.md` HARD RULES section, `C:/Users/Stoneface/.claude/Vault/learnings.md`, `C:/Users/Stoneface/.claude/Vault/rules/`, `C:/Users/Stoneface/.claude/projects/G--QUAKE-LEGACY/memory/*.md`.

---

## 1. Current state — measure the bloat

### 1.1 File-level line counts

| File | Lines | Source |
|---|---:|---|
| `G:/QUAKE_LEGACY/CLAUDE.md` (whole) | 761 | `wc -l` |
| `G:/QUAKE_LEGACY/CLAUDE.md` HARD RULES P1 block | 453 | lines 41–494 |
| `Vault/learnings.md` | 593 | `wc -l` |
| `Vault/rules/*.md` (7 files) | ~9.2 KB total | `ls` |
| `projects/G--QUAKE-LEGACY/memory/*.md` (18 files) | ~49 KB total | `ls` |

### 1.2 CLAUDE.md P1-* rule inventory (42 headings)

Enumerated via `grep -nE "^### Rule P1-"` on `G:/QUAKE_LEGACY/CLAUDE.md`. Raw count: **42 P1 headings** — but only **27 distinct rule letters** (A–DD). Dead weight = 42 − 27 = **15 superseded/legacy versions still in the hot file.**

Headings explicitly marked SUPERSEDED / legacy / kept-for-history (lines from grep):

| Heading | Line | Marker |
|---|---:|---|
| `P1-L v3` | 158 | `SUPERSEDED by v4 — kept for history` |
| `P1-Z v1` | 250 | `SUPERSEDED — kept for history` |
| `P1-AA v1` | 291 | `SUPERSEDED — kept for history` |
| `P1-CC v1` | 319 | `SUPERSEDED — kept for history` |
| `P1-G (legacy)` | 345 | `legacy — superseded by P1-G v4` |

That is **5 explicit dead entries, 155+ lines**. The remaining 10 "dead" versions hide behind naked `P1-G v3`, `P1-H v3`, `P1-L v2`, `P1-Y`, `P1-Z v2`, `P1-AA v2` etc. — they are not flagged as superseded in their heading even though a later vN explicitly supersedes them.

### 1.3 Vault/learnings.md L-rule inventory

Latest numbered: **L145** (`learnings.md:590`). BUT the file re-uses numbers under different date blocks:
- `L18` appears three times (`:69`, `:187`, `:230`), `L19` three times (`:73`, `:188`, `:307`), `L20` twice (`:47`, `:138`), `L22` twice (`:55`, `:144`), `L23` twice (`:59`, `:147`), `L24` twice (`:63`, `:150`), `L25` twice (`:183`, elsewhere), `L26` (`:180`), `L27` (`:177`), `L28` (`:153`), `L29` (`:159`), `L30` (`:156`), `L48`–`L50` reused twice across different sessions (`:245/303`, `:250/307`, `:255/311`), `L51`–`L57` once plus echo, `L52` reused (`:261`, `:298`).

Counted distinct **substantive entries**: **~111 unique L-rules** (numbering collisions above are a data-quality bug, not more rules). Of those:

| Bucket | Count | Examples |
|---|---:|---|
| QUAKE LEGACY live (enduring) | ~30 | L82–L85, L86–L89, L90–L95, L101–L128, L129–L133, L134–L141 |
| Polymarket / StonyClaw / other-project (not QL) | ~65 | L1–L80, L15–L81 except the QL range |
| Superseded within file (explicit "revises" / "supersedes") | ~14 | L119 revises P1-CC → supersedes L114 cut-mapping; L120 revises P1-Z → supersedes L111 onset method; L121/L122 revise P1-AA → supersede L112; L127 revises P1-Q; L128 supersedes prior L-L trim rules; L103/L104/L105/L106/L108/L109/L110 all superseded-in-fact by Part-4-v9 and beat-maker revisions |
| One-shot observations, non-reusable | ~15 | L116 ("clip list was styleb.txt" — Part-4-specific trivia), L141 ("demo corpus fully on disk" — status announcement), L143 ("README merge conflict resolution Apr 19" — one-shot) |

### 1.4 Vault/rules/ (extracted hard rules)

7 files, all NON-QL: `rule-forensic-before-reroute`, `rule-ha-entity-deletion`, `rule-n8n-node-compatibility`, `rule-nest-google-migration`, `rule-paper-mode-parity`, `rule-stonyclaw-event-transport`, `rule-windows-python-binary`. **Zero rules extracted for QL** even though QL patterns (audio-mix, music-full-tracks, title-card-contract) have repeated 3+ times and qualify under the Sovereign OS rule-extraction policy.

### 1.5 projects/G--QUAKE-LEGACY/memory/ — 18 files, fully absorbed status

| File | Status | Absorbed where |
|---|---|---|
| `MEMORY.md` | index (curate, don't archive) | n/a |
| `feedback_gate1_review.md` | absorbed | CLAUDE.md P1-A, P1-B, P1-C, P1-D, P1-E |
| `feedback_tier_hierarchy.md` | absorbed | CLAUDE.md P1-A + `project_quake_legacy.md` |
| `feedback_audio_transitions.md` | superseded | CLAUDE.md P1-G v4 + P1-H v4 |
| `feedback_editing_style.md` | absorbed | CLAUDE.md P1-K (Part 4 review) |
| `feedback_part4_v1_review.md` | superseded | Part 4 v10 + P1-G v5 + P1-T |
| `feedback_phase2_recording_windows.md` | live | not in CLAUDE.md (phase2 spec)  — KEEP |
| `feedback_visual_documentation.md` | absorbed | CLAUDE.md Rule VIS-1 |
| `feedback_part4_2026_04_17_review.md` | absorbed | CLAUDE.md P1-N/O/P/Q (see file:393–408) |
| `feedback_concat_demuxer_path.md` | absorbed | Vault/learnings.md L82–L85 |
| `feedback_command_center_engine_pivot.md` | absorbed | CLAUDE.md "Engine Rules" ENG-1..ENG-4 + L86–L89 |
| `feedback_part4_v9_audio_foundation.md` | absorbed | CLAUDE.md P1-Y v2, P1-G v5, P1-Z v2, P1-AA v2, P1-BB, P1-CC v2 |
| `feedback_clip_list_rescan.md` | absorbed | Vault/learnings.md L129–L133 |
| `feedback_design_to_main_merge.md` | one-shot / archive-eligible | Vault/learnings.md L143–L145 |
| `feedback_pantheon_brand_colors.md` | live (creative identity) | Vault/learnings.md L142 — KEEP |
| `project_quake_legacy.md` | live (canonical project context) | KEEP |
| `project_editing_pattern.md` | live (creative reference) | KEEP |
| `project_asset_vision.md` | live (Phase 5 vision) | KEEP |

**Redundancy rate: 11 of 18 files (61%) are fully absorbed** — their information has migrated into CLAUDE.md or learnings.md. They are now **third copies**.

---

## 2. Deduplication map

Rule-by-rule. Only QL-side rules covered (other-project L-rules listed in aggregate).

### 2.1 CLAUDE.md P1-* rules

| Rule ID | File:line | Status | Supersedor | Action | New location |
|---|---|---|---|---|---|
| P1-A (three-tier combining) | CLAUDE.md:43 | LIVE | — | KEEP | Tier A · `CLAUDE.md` §MULTI-ANGLE |
| P1-B (intro/outro clip pool) | CLAUDE.md:54 | LIVE | — | KEEP | Tier A · `CLAUDE.md` §INTRO |
| P1-C (PANTHEON prepend) | CLAUDE.md:62 | LIVE (but see P1-X on duration) | — | KEEP | Tier A · `CLAUDE.md` §INTRO |
| P1-D (preview clip names) | CLAUDE.md:69 | LIVE | — | KEEP | Tier A · `CLAUDE.md` §PREVIEW |
| P1-E (effects scope — in P1 vs not) | CLAUDE.md:75 | LIVE | — | KEEP | Tier A · `CLAUDE.md` §EFFECTS |
| P1-F (music catalog pointer) | CLAUDE.md:489 | LIVE · orphan position | — | MERGE-INTO | Tier A · §MUSIC STRUCTURE (co-locate with P1-R) |
| P1-G v3 (music 0.30 layered everywhere) | CLAUDE.md:90 | SUPERSEDED-BY v4+v5 | P1-G v4 / v5 | ARCHIVE | Tier C · `docs/_archive/claude-md-superseded.md` |
| P1-G v4 (music 0.20 + ebur128 gate) | CLAUDE.md:128 | LIVE | — | KEEP | Tier A · §AUDIO |
| P1-G v5 (music starts after PANTHEON, 1.5s fade-in) | CLAUDE.md:206 | LIVE | — | KEEP | Tier A · §AUDIO |
| P1-G legacy (Part 4 2026-04-17 mix) | CLAUDE.md:345 | SUPERSEDED-BY v4 | P1-G v4 | DELETE (labeled kept-for-history) | Tier C |
| P1-H (NO TRANSITIONS, hard cuts) | CLAUDE.md:376 | SUPERSEDED-BY v3/v4 | P1-H v4 | ARCHIVE | Tier C |
| P1-H v3 (0.15s xfade) | CLAUDE.md:98 | SUPERSEDED-BY v4 | P1-H v4 | ARCHIVE | Tier C |
| P1-H v4 (0.4s xfade + audio-drift fix) | CLAUDE.md:137 | LIVE | — | KEEP | Tier A · §TRANSITIONS |
| P1-I (golden rule frag+effect+music) | CLAUDE.md:475 | LIVE | — | KEEP | Tier A · §BEAT SYNC (header bullet) |
| P1-J (quality ceiling, CRF 15-17) | CLAUDE.md:483 | LIVE | — | KEEP | Tier A · §RENDER PIPELINE |
| P1-K (FP backbone + one FL) | CLAUDE.md:354 | LIVE (revised by L107/P1-CC v2 semantics) | — | KEEP | Tier A · §MULTI-ANGLE |
| P1-L (1s/2s blanket — Part 4 2026-04-17) | CLAUDE.md:368 | SUPERSEDED-BY v4 | P1-L v4 | ARCHIVE | Tier C |
| P1-L v2 (FP/FL differentiated head) | CLAUDE.md:107 | SUPERSEDED-BY v4 | P1-L v4 | ARCHIVE | Tier C |
| P1-L v3 (tail 2.5 + protection floor) | CLAUDE.md:158 | SUPERSEDED-BY v4 (explicit) | P1-L v4 | ARCHIVE | Tier C |
| P1-L v4 (FL-ONLY trim) | CLAUDE.md:145 | LIVE | — | KEEP | Tier A · §TRIMMING |
| P1-M (mentioned in MEMORY.md index, not in CLAUDE.md grep) | — | DANGLING REFERENCE | — | VERIFY/DELETE | n/a — cite orphan in MEMORY.md |
| P1-N (title card contract) | CLAUDE.md:394 | LIVE (timing revised by P1-X) | — | KEEP (merge P1-X offsets) | Tier A · §TITLE CARD |
| P1-O (music coverage continuity) | CLAUDE.md:408 | LIVE | — | KEEP | Tier A · §MUSIC STRUCTURE |
| P1-P (full-length clip contract) | CLAUDE.md:416 | LIVE | — | KEEP | Tier A · §FULL-LENGTH CLIP CONTRACT |
| P1-Q (replay-speed contrast) | CLAUDE.md:426 | LIVE (revised by P1-EE) | — | KEEP-MERGE with P1-EE | Tier A · §FULL-LENGTH CLIP CONTRACT |
| P1-R (three-track music structure) | CLAUDE.md:455 | LIVE | — | KEEP | Tier A · §MUSIC STRUCTURE |
| P1-S (beat-sync governs seams only) | CLAUDE.md:435 | LIVE | — | KEEP | Tier A · §BEAT SYNC |
| P1-T (title-card FL backdrop) | CLAUDE.md:384 | LIVE (revised by P1-Y v2) | — | MERGE-INTO P1-Y v2 | Tier A · §TITLE CARD (one unified entry) |
| P1-U (tier interleave) | CLAUDE.md:115 | LIVE (but revised by L119 → flow over tier) | P1-CC v2 implicitly | MERGE-INTO §BEAT SYNC flow planner | Tier A |
| P1-V (beat-snap + silence-detect) | CLAUDE.md:122 | DEFERRED (not shipped) | — | KEEP as TODO | Tier B · warm tickets |
| P1-W (music full tracks only) | CLAUDE.md:166 | LIVE | — | KEEP | Tier A · §MUSIC STRUCTURE |
| P1-X (PANTHEON intro 5s) | CLAUDE.md:174 | LIVE | — | MERGE-INTO P1-C | Tier A · §INTRO |
| P1-Y (title card font v1) | CLAUDE.md:181 | SUPERSEDED-BY v2 | P1-Y v2 | ARCHIVE | Tier C |
| P1-Y v2 (Quake-style title card) | CLAUDE.md:191 | LIVE | — | KEEP | Tier A · §TITLE CARD |
| P1-Z v1 (loudest onset) | CLAUDE.md:250 | SUPERSEDED-BY v2 (explicit) | P1-Z v2 | ARCHIVE | Tier C |
| P1-Z v2 (recognized game events) | CLAUDE.md:214 | LIVE | — | KEEP | Tier A · §BEAT SYNC |
| P1-AA v1 (full-track queue + afade xfade) | CLAUDE.md:291 | SUPERSEDED-BY v2 (explicit) | P1-AA v2 | ARCHIVE | Tier C |
| P1-AA v2 (video=truth, DJ beat-match) | CLAUDE.md:260 | LIVE | — | KEEP | Tier A · §MUSIC STRUCTURE |
| P1-BB (split video/audio graphs, PCM WAV, CFR) | CLAUDE.md:333 | LIVE | — | KEEP | Tier A · §RENDER PIPELINE |
| P1-CC v1 (downbeat/phrase/drop → strict tier) | CLAUDE.md:319 | SUPERSEDED-BY v2 (explicit) | P1-CC v2 | ARCHIVE | Tier C |
| P1-CC v2 (flow-driven cut placement) | CLAUDE.md:307 | LIVE | — | KEEP | Tier A · §BEAT SYNC |
| P1-DD (QL sound template library) | CLAUDE.md:237 | LIVE | — | KEEP | Tier A · §BEAT SYNC |
| P1-EE (event-localized speed FX) | CLAUDE.md:276 | LIVE | — | KEEP | Tier A · §FULL-LENGTH CLIP CONTRACT |

**Count:** 42 entries scanned · **28 KEEP** (some merged, reducing final count to ~22) · **11 ARCHIVE** · **1 VERIFY orphan (P1-M)** · **1 DEFERRED TODO (P1-V)**.

### 2.2 CLAUDE.md P3-* and CS-* (post-P1 sections)

All live, all small, none have revision stacks — leave in place.

| Rule ID | File:line | Action |
|---|---|---|
| P3-A (highlight criteria first) | CLAUDE.md:497 | KEEP |
| P3-B (WolfcamQL command inventory) | CLAUDE.md:505 | KEEP |
| CS-1..CS-6 (Cinema Suite) | CLAUDE.md:554–591 | KEEP |
| ENG-1..ENG-4 | inline in §Engine Rules | KEEP |

### 2.3 Vault/learnings.md L-rules (QL-only)

| L-rule | File:line | Status | Action |
|---|---|---|---|
| L82 (ffmpeg >40-input ceiling) | :29 | LIVE (platform quirk) | EXTRACT → `Vault/rules/rule-ffmpeg-concat-limit.md` (repeated 3+ parts) |
| L83 (disk preflight) | :33 | LIVE | EXTRACT → `Vault/rules/rule-disk-preflight.md` |
| L84 (intermediate CRF 20 fast) | :37 | LIVE | KEEP inline |
| L85 (rim-light exponent) | :41 | LIVE (graphics one-shot) | KEEP inline |
| L86 (Steam paks authoritative) | :9 | LIVE — already ENG-1 | MERGE + DELETE redundant |
| L87 (decouple parser from renderer) | :13 | LIVE | KEEP inline |
| L88 (project-local data dirs) | :17 | LIVE (architecture rule) | EXTRACT → rules/ |
| L89 (graphify-scannable trees) | :21 | LIVE | KEEP inline |
| L90 (no transitions, hard cuts) | :394 | SUPERSEDED-BY L104 + P1-H v4 | ARCHIVE |
| L91 (multi-angle ping-pong) | :397 | LIVE → P1-K | MERGE into P1-K canonical |
| L92 (filler = full length) | :400 | LIVE → P1-P | MERGE + DELETE |
| L93 (music coverage mandatory) | :403 | LIVE → P1-O | MERGE + DELETE |
| L94 (extract knowledge before retiring) | :406 | LIVE (meta-rule) | EXTRACT → rules/rule-extraction-before-retire.md |
| L95 (title card is mandatory) | :409 | LIVE → P1-N | MERGE + DELETE |
| L96 (engine dedup + DIFFS.md) | :414 | LIVE (one-shot, engine-unification) | KEEP inline |
| L97 (UTF-8 on Windows reports) | :417 | LIVE | EXTRACT → rules/rule-windows-utf8-reports.md (repeats w/ L144) |
| L98 (inline > session spawning) | :420 | LIVE (workflow) | EXTRACT → rules/rule-no-session-spawn-default.md |
| L99 (git branch drift prevention) | :423 | LIVE (workflow) | EXTRACT → rules/rule-git-branch-verify-every-turn.md |
| L100 (copy-verify before delete) | :426 | LIVE | EXTRACT → rules/rule-copy-verify-before-delete.md |
| L101 (three-track music) | :429 | LIVE → P1-R | MERGE + DELETE |
| L102 (beat-sync at seams only) | :432 | LIVE → P1-S | MERGE + DELETE |
| L103 (music volume → objective ebur128) | :437 | LIVE → P1-G v4 | MERGE + DELETE |
| L104 (transitions = visible xfade) | :440 | LIVE → P1-H v4 | MERGE + DELETE |
| L105 (music stitcher full tracks) | :443 | LIVE → P1-W | MERGE + DELETE |
| L106 (min-playable floor) | :446 | LIVE → P1-L v3/v4 | MERGE + DELETE |
| L107 (FL as effect not frag) | :449 | LIVE → P1-K revision | MERGE + DELETE |
| L108 (PANTHEON 5s) | :452 | LIVE → P1-X | MERGE + DELETE |
| L109 (Impact font kerning) | :455 | SUPERSEDED-BY P1-Y v2 (Bebas + Quake-style) | ARCHIVE |
| L110 (audio drift resampling) | :458 | LIVE → P1-BB | MERGE + DELETE |
| L111 (GAME-audio onset beat) | :465 | SUPERSEDED-BY L120 (event recognition) | ARCHIVE |
| L112 (full-track music queue) | :468 | LIVE → P1-W | MERGE + DELETE |
| L113 (PANTHEON own-audio, music after) | :471 | LIVE → P1-G v5 | MERGE + DELETE |
| L114 (downbeat phrase drop) | :474 | SUPERSEDED-BY L119 (flow, not strict tier gate) | ARCHIVE |
| L115 (split graph + PCM WAV + CFR) | :477 | LIVE → P1-BB | MERGE + DELETE |
| L116 (part04_styleb.txt default) | :480 | ONE-SHOT (project trivia) | DELETE outright |
| L117 (per-clip override grammar) | :483 | LIVE (architecture) | KEEP inline |
| L118 (parallel-session discipline) | :486 | LIVE (workflow) | EXTRACT → rules/rule-parallel-session-scope.md |
| L119 (tier is ordering hint, not gate) | :492 | LIVE → P1-CC v2 | MERGE + DELETE |
| L120 (action peak = recognized event) | :495 | LIVE → P1-Z v2 | MERGE + DELETE |
| L121 (video = source of truth) | :498 | LIVE → P1-AA v2 | MERGE + DELETE |
| L122 (DJ beat-match song seams) | :501 | LIVE → P1-AA v2 | MERGE + DELETE |
| L123 (intro music with title card) | :504 | LIVE → P1-G v5 | MERGE + DELETE |
| L124 (QL sound extraction) | :507 | LIVE → P1-DD | MERGE + DELETE |
| L125 (multi-frag patterns per clip) | :510 | LIVE (creative, not enforced yet) | KEEP inline (Tier B) |
| L126 (cross-part learning) | :513 | LIVE (workflow) | EXTRACT → rules/rule-cross-part-learning.md |
| L127 (event-localized slowmo) | :516 | LIVE → P1-EE | MERGE + DELETE |
| L128 (FP trim = 0) | :521 | LIVE → P1-L v4 | MERGE + DELETE |
| L129 (naive body-sum broken by beat-snap) | :526 | LIVE (architecture) | KEEP inline (Tier B) |
| L130 (orphan filtergraph labels) | :529 | LIVE | EXTRACT → rules/rule-filtergraph-orphan-labels.md |
| L131 (frag_key = tier+subdir) | :532 | LIVE (architecture) | KEEP inline |
| L132 (P1-K activates on `>` grammar) | :535 | LIVE | MERGE into P1-K canonical |
| L133 (pre-flight validators mandatory) | :538 | LIVE | EXTRACT → rules/rule-preflight-validators.md |
| L134 (haiku for mechanical, Sonnet for judgment) | :544 | LIVE (workflow) | KEEP inline |
| L135 (JobQueue depth=1 + 409) | :547 | LIVE → CS-1 | MERGE + DELETE |
| L136 (SSE auto-close on terminal) | :550 | LIVE | KEEP inline (Tier B) |
| L137 (security-lint regex bypass) | :553 | LIVE | KEEP inline (Tier B) |
| L138 (env-gated mock paths) | :556 | LIVE → CS-2 | MERGE + DELETE |
| L139 (security-focused code review mandatory) | :559 | LIVE (workflow) | EXTRACT → rules/rule-security-review-final-pass.md |
| L140 (git sub-repo for version history) | :568 | LIVE → CS-3 | MERGE + DELETE |
| L141 (demo corpus inventory) | :571 | STATUS UPDATE (not a rule) | DELETE (belongs in CLAUDE.md corpus table) |
| L142 (brand colors — Nauru) | :576 | LIVE (creative) | KEEP inline |
| L143 (README merge — prefer full-rewrite side) | :582 | LIVE (workflow) | KEEP inline |
| L144 (graphify UTF-8 env) | :586 | LIVE | MERGE with L97 into one rule |
| L145 (pre-existing-error diff before blaming merge) | :590 | LIVE (workflow) | EXTRACT → rules/rule-diff-base-before-blame-merge.md |

**QL L-rule count:** ~60 entries (L82 onward). **MERGE + DELETE:** 25 · **ARCHIVE:** 5 · **EXTRACT to Vault/rules/:** 13 · **KEEP inline:** 17 · **DELETE outright:** 2.

### 2.4 projects/G--QUAKE-LEGACY/memory/ feedback files — dedup actions

| File | Action | Reason |
|---|---|---|
| `feedback_gate1_review.md` | DELETE | Fully absorbed (P1-A..E) |
| `feedback_tier_hierarchy.md` | DELETE | Fully absorbed (P1-A + project_quake_legacy) |
| `feedback_audio_transitions.md` | DELETE | Superseded by P1-G v4 + P1-H v4 |
| `feedback_editing_style.md` | DELETE | Absorbed into P1-K |
| `feedback_part4_v1_review.md` | ARCHIVE | Superseded (v10 shipped, 4-version-old review) |
| `feedback_phase2_recording_windows.md` | KEEP | Not yet in CLAUDE.md, Phase 2 pre-work |
| `feedback_visual_documentation.md` | DELETE | Absorbed → Rule VIS-1 in CLAUDE.md |
| `feedback_part4_2026_04_17_review.md` | ARCHIVE | Absorbed into P1-N/O/P/Q |
| `feedback_concat_demuxer_path.md` | DELETE | Absorbed into L82–L85 |
| `feedback_command_center_engine_pivot.md` | DELETE | Absorbed into ENG-1..4 + L86–L89 |
| `feedback_part4_v9_audio_foundation.md` | ARCHIVE | Absorbed into L111–L118 + multiple P1 rules |
| `feedback_clip_list_rescan.md` | ARCHIVE | Absorbed into L129–L133 |
| `feedback_design_to_main_merge.md` | ARCHIVE | One-shot, absorbed into L143–L145 |
| `feedback_pantheon_brand_colors.md` | CONSOLIDATE-INTO new `memory/DOMAIN_brand.md` | Creative identity worth keeping |
| `project_quake_legacy.md` | KEEP | Canonical project context |
| `project_editing_pattern.md` | KEEP | Canonical creative reference |
| `project_asset_vision.md` | KEEP | Phase 5 vision, still forward-looking |
| `MEMORY.md` | REWRITE | Index to point at new Tier A/B/C layout |

---

## 3. Proposed curated base layout

### 3.1 Tier A — HOT (always in context, <500 lines total)

**Target total:** `CLAUDE.md` (HARD RULES section shrinks from 453 → ~180 lines) + `Vault/learnings.md` (shrinks from 593 → ~200 lines) = **~380 hot-tier lines**. Budget met.

**Layout:**

| Path | Purpose | Target size |
|---|---|---|
| `G:/QUAKE_LEGACY/CLAUDE.md` | HARD RULES §1–§10 (domain-grouped, live versions only) | ~180 lines |
| `C:/Users/Stoneface/.claude/Vault/learnings.md` | L-ledger, live QL + cross-project rules only, archived L-rules removed | ~200 lines |
| `C:/Users/Stoneface/.claude/Vault/rules/` | Category subfolders; each rule = one file, 15–30 lines | ~13 new QL rule files |

**New `Vault/rules/` subfolder structure:**

```
Vault/rules/
  AUDIO/
    rule-music-ebur128-gate.md          ← from L103 + P1-G v4
    rule-music-full-tracks.md           ← from L105/L112 + P1-W
  ARCHITECTURE/
    rule-copy-verify-before-delete.md   ← from L100
    rule-cross-part-learning.md         ← from L126
    rule-decouple-parser-from-renderer.md  ← from L87
    rule-project-local-data.md          ← from L88
  PLATFORM_QUIRK/
    rule-ffmpeg-concat-limit.md         ← from L82
    rule-windows-utf8-reports.md        ← from L97 + L144
    rule-windows-python-binary.md       (exists)
  TEST_DESIGN/
    rule-preflight-validators.md        ← from L133
    rule-security-review-final-pass.md  ← from L139
    rule-diff-base-before-blame-merge.md ← from L145
    rule-filtergraph-orphan-labels.md   ← from L130
  WORKFLOW/
    rule-git-branch-verify-every-turn.md ← from L99
    rule-parallel-session-scope.md      ← from L118
    rule-no-session-spawn-default.md    ← from L98
    rule-extraction-before-retire.md    ← from L94
    rule-disk-preflight.md              ← from L83
  (existing non-QL rules stay where they are)
```

### 3.2 Tier B — WARM (loaded on demand)

**Path:** `C:/Users/Stoneface/.claude/projects/G--QUAKE-LEGACY/memory/`

Current: 18 files, session-chronological, 61% absorbed. Proposed: 6 files, domain-organized, 0% duplicated.

```
memory/
  MEMORY.md                    ← rewritten as Tier-A/B/C index + domain TOC
  DOMAIN_phase1_pipeline.md    ← merges feedback_clip_list_rescan + feedback_concat_demuxer + L116/L117/L125/L129/L131/L136/L137
  DOMAIN_brand_identity.md     ← merges feedback_pantheon_brand_colors + L142 + PANTHEON intro facts
  DOMAIN_phase2_phase3.md      ← merges feedback_phase2_recording_windows + FT-1/FT-2 status
  DOMAIN_engine_stack.md       ← ENG-1..4 facts + wolfcam/q3mme split (summary of feedback_command_center_engine_pivot)
  project_context.md           ← merges project_quake_legacy + project_editing_pattern + project_asset_vision
```

**Line target:** 6 files × ~60 lines = ~360 warm-tier lines (down from ~1500 across 18 files).

### 3.3 Tier C — COLD (archive, grep-able, never auto-loaded)

| Path | What lives here | Retrieval |
|---|---|---|
| `G:/QUAKE_LEGACY/docs/_archive/claude-md-superseded-2026-04-19.md` | Every SUPERSEDED P1-* version verbatim (P1-G v3, P1-H/v3, P1-L/v2/v3, P1-Y, P1-Z v1, P1-AA v1, P1-CC v1, P1-G legacy) | grep by rule ID |
| `C:/Users/Stoneface/.claude/Vault/_archive/2026-Q2/learnings-superseded.md` | Archived L-rules L90, L109, L111, L114 (superseded-in-fact) | grep |
| `C:/Users/Stoneface/.claude/projects/G--QUAKE-LEGACY/memory/_archive/` | Session-specific feedback_*.md files marked ARCHIVE in §2.4 (5 files) | grep |

**Archive rule:** every archived entry keeps its original rule-ID. Tier A `learnings.md` and `CLAUDE.md` include a "Superseded index" footer: one line per archived ID pointing at the archive file + its supersedor. Zero broken references.

---

## 4. Rule canonicalization — before/after for the 10 heaviest-bloat rules

Format: **WHAT / WHERE / WHY**, each ≤ 3 lines. Applied to the rules with the most stacked versions.

### 4.1 P1-G (Music mix)

**Before (current state):** 4 entries — P1-G v3 (`:90`), v4 (`:128`), v5 (`:206`), legacy (`:345`). Total ~55 lines.

**After (canonical, Tier A):**
```
### P1-G (Music mix) [v5, 2026-04-18]
WHAT   Music volume 0.20. PANTHEON = own audio only; music fades in 0→0.20 over 1.5s at title-card start;
       body = game 1.0 + music 0.20 sidechain-ducked. Final render MUST pass ebur128 gate: music ≤ -12 LU
       below game peak, else render is FAILED_LEVEL_GATE and not shipped.
WHERE  cfg.music_volume=0.20, cfg.music_fadein_s=1.5 · render_part_v6.py::final_render audio graph
       (3-segment concat) · phase1/audio_levels.py::measure_music_vs_game · output/partNN_levels.json
WHY    Subjective complaints about music loudness repeat every review (v1/v2/v3/v4). Objective gate ends it.
```

### 4.2 P1-H (Transitions)

**Before:** 3 entries — P1-H (`:376`) "NO TRANSITIONS", v3 (`:98`) "0.15s xfade", v4 (`:137`) "0.4s xfade". ~40 lines.

**After:**
```
### P1-H (Transitions) [v4, 2026-04-18]
WHAT   0.40s seam xfade between every body chunk. Banned: ≥0.8s, fade-to-black, dip-to-white.
WHERE  cfg.seam_xfade_duration=0.40 · render_part_v6.py::assemble_body_with_xfades · every chunk
       audio enters with asetpts=PTS-STARTPTS,aresample=async=1:first_pts=0 (drift fix per P1-BB)
WHY    User asked for visible transitions 4 times; v1's "hard cuts only" was rejecting 1s drama fades,
       not short bleeds. 0.4s is the minimum perceptible.
```

### 4.3 P1-L (Trimming)

**Before:** 4 entries — P1-L (`:368`), v2 (`:107`), v3 (`:158`), v4 (`:145`). ~48 lines.

**After:**
```
### P1-L (Head/tail trim) [v4, 2026-04-18]
WHAT   FP clips: head=0, tail=0 (frags are clean start-to-end). FL clips: head=1.0s (console), tail=2.0s
       (angle falloff). Skip any clip whose post-trim body < 2.0s (min_playable). No speed-stretch.
WHERE  cfg.clip_head_trim_fp=0.0, _fl=1.0 · clip_tail_trim_fp=0.0, _fl=2.0 · min_playable=2.0 ·
       render_part_v6.py::build_body_chunks · per-clip overrides in partNN_overrides.txt win
WHY    Trimming FP was always wrong; only FL needs edges cleaned. Short-clip protection prevents 1s blurs.
```

### 4.4 P1-Y (Title card)

**Before:** 3 entries — P1-Y v1 (`:181`), v2 (`:191`), plus P1-T backdrop (`:384`). ~50 lines.

**After (merged with P1-T):**
```
### P1-Y (Title card) [v2 + P1-T merged, 2026-04-18]
WHAT   Quake-style hero (OFL display font TBD from {Black Ops One, Russo One, Bungee Inline}) + Bebas Neue
       subtitle. Metallic red→gold fill, triple-layer 3D, scanlines, chromatic aberration on reveal,
       scale-punch per char, final flash. Renders over desaturated FL gameplay backdrop (hue=s=0.25,
       brightness=-0.22, gblur=σ=4, vignette). Duration 8s. NEVER over black.
WHERE  phase1/title_card.py::render_title_card · pick_intro_backdrop_fls walks T3→T2→T1 FL files
WHY    Tier B font kerning disaster (L109) + v6 black-void readability (L95) both fixed at once.
       Smoke test per VIS-1.
```

### 4.5 P1-Z (Beat-sync action peak detection)

**Before:** 2 entries — v1 (`:250`, SUPERSEDED), v2 (`:214`). ~35 lines.

**After:**
```
### P1-Z (Action peak = recognized game event) [v2, 2026-04-18]
WHAT   Detect player_death / rocket_impact / rail_fire / grenade_explode / LG_hit in clip audio via
       template match against phase1/sound_templates/ (P1-DD). Peak = argmax(weight × confidence).
       Grenade throw+3s+explode = compound "grenade_direct", peak at explosion. Player_death wins over
       weapon events. Fallback: loudest onset + tag RECOGNITION_FAILED (confidence<0.4).
WHERE  phase1/audio_onsets.py::recognize_game_events · logs output/partNN_beats.json
WHY    Loudest onset mislabeled 30%+ of clips; recognized events are correct by construction.
```

### 4.6 P1-AA (Music stitcher)

**Before:** 2 entries — v1 (`:291`, SUPERSEDED), v2 (`:260`). ~60 lines (largest single bloat).

**After:**
```
### P1-AA (Music stitcher — video is truth) [v2, 2026-04-18]
WHAT   Video body length rules. Queue N full tracks until sum ≥ body_duration; last track may truncate
       at a PHRASE boundary (never mid-bar). Seams = DJ beat+phrase match at 8/16-bar boundaries,
       time-stretch B to BPM_A via rubberband if Δ≤8 BPM, else afade fallback flagged BPM_MISMATCH.
       Sidechain-duck music ~6dB on recognized game events. Ship gate: music_plan.json phrase-boundary
       check on any truncation.
WHERE  phase1/music_stitcher.py · phase1/sidechain.py · output/partNN_music_plan.json
WHY    Mid-song cuts + looped tails rejected twice by user. Beat-matched DJ mix is what listeners expect.
```

### 4.7 P1-CC (Flow-driven cut placement)

**Before:** 2 entries — v1 (`:319`, SUPERSEDED), v2 (`:307`). ~30 lines.

**After:**
```
### P1-CC (Flow-driven cut placement) [v2, 2026-04-18]
WHAT   Flow planner walks music sections[] and picks clips by SECTION SHAPE, not tier. build→T3 atmos;
       drop→clip with player_death / rocket_impact nearest the drop timestamp; break→longest downtime clip;
       outro→tail frags. Tier is sort-key tiebreaker (T1>T2>T3), never a hard gate.
WHERE  phase1/beat_sync.py::plan_flow_cuts_v2 · phase1/music_structure.py produces sections[]
WHY    "Perfect drop on a T3 action becomes T1 to the watcher" (L119). Tier-as-gate was too rigid.
```

### 4.8 P1-Q + P1-EE (Speed effects)

**Before:** P1-Q (`:426`) defined whole-clip replay-speed contrast; P1-EE (`:276`) revised to window-based. Overlap.

**After (merged):**
```
### P1-Q (Speed effects) [v2, 2026-04-18; merges P1-EE]
WHAT   Effects apply to a WINDOW around recognized event peak (default ±0.8s), NEVER whole clip. Ramps
       in/out over 100ms. Audio: Option B default (atempo=2.0 counters 0.5x video → natural-speed
       audio). Option A mute for heavy-reverb events. Option C 60% volume for multi-kills. Requires
       P1-Z confidence ≥0.55 — no peak = no effect. REPLAY_SPEED_CONTRAST for short T1 clips stays.
WHERE  phase1/effects.py · render_part_v6.py::build_body_chunks · partNN_overrides.txt slow_window=<s>
WHY    Whole-clip slowmo stutters audio (user flagged); event-localized = velocity feel.
```

### 4.9 P1-N + P1-T + P1-X (Intro sequence)

**Before:** 3 separate rules for a single sequence. ~25 lines.

**After (merged):**
```
### P1-N (Intro sequence) [v3, 2026-04-18; merges P1-T + P1-X]
WHAT   Every Part opens with [PANTHEON 5s] + [Title card 8s] + [Content]. PANTHEON = IntroPart2.mp4
       first 5s. Title card = P1-Y v2 (Quake-style, FL backdrop). Pre-content offset = 13s. Hard cut
       into first clip (no fade per P1-H).
WHERE  cfg.intro_clip_duration=5.0 · render_part_v6.py::build_intro · title_card.py
WHY    Series identity is structural, not polish (L95). 5s drops 2s of dead PANTHEON hold (L108).
```

### 4.10 P1-W + P1-O + P1-R (Music structure)

**Before:** 3 rules (`:166`, `:408`, `:455`) that describe ONE contract. ~35 lines.

**After (unified):**
```
### P1-R (Music structure) [v2, 2026-04-18; merges P1-O + P1-W]
WHAT   Every Part = 3 tracks (intro + main + outro). Intro under PANTHEON+title (Cinema - Sped Up default).
       Main = per-Part hype pick. Outro = ~30s cooldown (Eple - Badger default). Continuous coverage
       mandatory — silence gaps = render failure. All tracks play FULL; last may truncate at phrase
       boundary only (P1-AA). Mid-song cuts banned.
WHERE  Config.intro_music_path(part) / music_path / outro_music_path · phase1/music_stitcher.py
WHY    Single-track renders rejected by user; mid-song swaps rejected twice.
```

---

## 5. Rule-grouping proposal for CLAUDE.md §HARD RULES

Proposed TOC (replacing the 453-line wall of revisions):

```
## HARD RULES — Phase 1 (domain-grouped, live versions only)

1. AUDIO
   - P1-G v5     Music mix (0.20, ebur128 gate, PANTHEON-silent, fade-in at title)
   - (ebur128 gate fixture: output/partNN_levels.json)

2. TRIMMING
   - P1-L v4     FL-only head/tail; FP untouched; min_playable floor
   - P1-D        Preview burn-in of clip names

3. TRANSITIONS
   - P1-H v4     0.40s seam xfade; ban list; drift fix (PTS-STARTPTS)

4. MUSIC STRUCTURE
   - P1-R        Three-track contract (merges P1-O + P1-W)
   - P1-AA v2    Stitcher + DJ beat-match seams + phrase-boundary truncation
   - P1-F        Track catalog pointer

5. TITLE CARD
   - P1-Y v2     Quake-style card (merges P1-T backdrop)

6. BEAT SYNC & GAME AUDIO
   - P1-Z v2     Recognized event detection
   - P1-DD       QL sound template library
   - P1-CC v2    Flow-driven cut placement
   - P1-S        Seams only, never truncate content
   - P1-I        Golden rule (frag + effect + music)

7. MULTI-ANGLE
   - P1-A        Three-tier combining (T1/T2/T3 semantics)
   - P1-B        Intro/outro pool (lower-tier FL preference)
   - P1-K        FP backbone + one FL; `>` grammar activates
   - (L107 semantics: FL is an effect on FP, not a standalone frag)

8. FULL-LENGTH CLIP CONTRACT
   - P1-P        No sub-clip fragments
   - P1-Q v2     Event-localized speed effects (merges P1-EE)

9. RENDER PIPELINE
   - P1-BB       Split video/audio graphs, PCM WAV, CFR, sync audit
   - P1-J        Quality ceiling (CRF 15-17 preset slow)
   - P1-E        Phase 1 effect scope (what's in P1 vs P2/3/4)

10. INTRO
   - P1-C        PANTHEON prepend
   - P1-N v3     5s+8s contract (merges P1-T + P1-X)
```

Under each: 1 live rule block in the WHAT/WHERE/WHY format from §4. No history. Archive link footer at bottom of CLAUDE.md: *"Superseded versions archived at `docs/_archive/claude-md-superseded-2026-04-19.md`."*

**Target size:** 10 sections × ~15 lines = ~150 lines (vs 453 currently). **Shrinkage: 67%.**

---

## 6. Dead weight to delete outright

Distinct from archive — these have zero historical value.

| Item | Location | Reason |
|---|---|---|
| `P1-V` (deferred stub with no implementation) | CLAUDE.md:122 | If not implemented, it's a backlog ticket, not a rule. Move to `HUMAN-QUESTIONS.md` or a TODO file. |
| `L116` ("active clip list is styleb.txt not partNN.txt") | learnings.md:480 | Project-trivia discovered during one session. Not a pattern. The renderer's argument parser is self-documenting. |
| `L141` ("demo corpus fully on disk — 6465 demos") | learnings.md:571 | Status announcement, not a rule. Already duplicated in CLAUDE.md "Demo Corpus Inventory" table. |
| `L90` text "TransitionPlanner with 6 kinds is noise" | learnings.md:394 | Obsolete — TransitionPlanner deprecation is complete, reminding about the deleted class confuses. |
| `L109` ("Impact 0.55×fontsize is wrong") | learnings.md:455 | Solved by font switch to Bebas/Quake-style (P1-Y v2). The lesson never recurs because Impact is banned. |
| `feedback_gate1_review.md` | memory/ | Full content is P1-A..E, verbatim. Third copy. |
| `feedback_audio_transitions.md` | memory/ | Contradicts current P1-G v5 + P1-H v4 (says 55% game audio vs current 100%). Wrong AND duplicate. |
| `feedback_visual_documentation.md` | memory/ | Rule VIS-1 is the canonical version. |
| `feedback_concat_demuxer_path.md` | memory/ | Full content is L82–L85. Third copy. |
| `feedback_command_center_engine_pivot.md` | memory/ | Full content is ENG-1..4 + L86–L89. Third copy. |

---

## 7. Execution order (atomic steps, rollback per step)

Each step is a single commit, reversible by `git revert <sha>` on `G:/QUAKE_LEGACY` or direct restore in `~/.claude/Vault/`.

### Step 1 — snapshot current state
Copy (don't move) all curated-scope files into a tagged snapshot dir.
- Change: `cp -r` to `_archive/2026-04-19-snapshot/`
- Verify: `diff -r` snapshot vs live = zero
- Rollback: delete snapshot

### Step 2 — create Tier-C archive files
Move superseded P1-* blocks (P1-G v3, P1-G legacy, P1-H, P1-H v3, P1-L v1/v2/v3, P1-Y v1, P1-Z v1, P1-AA v1, P1-CC v1 — 11 blocks) out of CLAUDE.md into `docs/_archive/claude-md-superseded-2026-04-19.md`. Same for learnings.md L90/L109/L111/L114 into `Vault/_archive/2026-Q2/learnings-superseded.md`.
- Verify: `grep -c "SUPERSEDED\|kept for history"` in CLAUDE.md == 0. Archive file contains all 11 rule IDs (grep for each).
- Rollback: restore from Step 1 snapshot.

### Step 3 — collapse merge-candidate L-rules into their P1 supersedors
For each L-rule marked MERGE+DELETE in §2.3 (25 entries), delete the L-rule entry AFTER confirming the target P1 rule in CLAUDE.md contains the same claim. Add a one-line "superseded by [P1-X]" breadcrumb in `Vault/_archive/2026-Q2/learnings-superseded.md`.
- Verify: `grep -c "^\*\*L[0-9]"` in learnings.md drops by ~25. Every deleted L-ID appears in the archive breadcrumb file.
- Rollback: Step 1 snapshot.

### Step 4 — rewrite CLAUDE.md HARD RULES section with §5 TOC
Replace lines 41–494 with the §5 TOC + canonical WHAT/WHERE/WHY blocks for each live rule. Append "Archive" footer pointing to `docs/_archive/claude-md-superseded-2026-04-19.md`.
- Verify: `wc -l` on CLAUDE.md drops from 761 to ~480. Every live rule ID (P1-A, B, C, D, E, F, G v5, H v4, I, J, K, L v4, N v3, P, Q v2, R, S, W, Y v2, Z v2, AA v2, BB, CC v2, DD, plus P3-A/B and CS-1..6, ENG-1..4, VIS-1) is grep-present exactly once.
- Rollback: `git checkout HEAD~1 -- G:/QUAKE_LEGACY/CLAUDE.md`

### Step 5 — extract 13 cross-project rules to `Vault/rules/<category>/`
One file per rule (§3.1 list). Each file: 15–30 lines with WHAT/WHERE/WHY + example.
- Verify: 13 new files created. Each file has `category:` frontmatter. Originating L-rule in learnings.md now has a trailing line `→ extracted to Vault/rules/<path>`.
- Rollback: rm the 13 files.

### Step 6 — consolidate 18 memory/ feedback files into 6 DOMAIN files
Per §3.2 layout. Move archived files to `memory/_archive/`. Delete the 5 files in §6 dead-weight list.
- Verify: `ls memory/*.md | wc -l` == 6 (plus MEMORY.md = 7). `ls memory/_archive/*.md` == 5. No information loss: grep each deleted file's unique sentences against the new DOMAIN files — must appear.
- Rollback: Step 1 snapshot.

### Step 7 — rewrite MEMORY.md index
Point at new Tier A/B/C structure. Remove links to deleted/archived files.
- Verify: every MEMORY.md link resolves (no 404). Includes Tier-C archive pointers.
- Rollback: Step 1 snapshot.

### Step 8 — ship-gate validation
Run:
```
# Line count dropped by ≥40%
$(wc -l CLAUDE.md learnings.md memory/*.md) now vs snapshot → delta ≥ 40%

# No orphan rule references
grep -rE "P1-[A-Z]" G:/QUAKE_LEGACY/CLAUDE.md ~/.claude/Vault/ ~/.claude/projects/G--QUAKE-LEGACY/
  | awk '{ ... }' → every ID either LIVE in Tier A OR in archive redirect map

# Every archived ID has a reachable redirect
for id in $(archived_ids); do grep -q "$id" docs/_archive/claude-md-superseded-2026-04-19.md || FAIL; done
```
- Verify: above checks all pass.
- Rollback: Step 1 snapshot.

### Step 9 — single commit with full curation, co-authored tag
One commit encompassing steps 2–7. Message: `docs(memory): curate learning-memory corpus — dedup L-rules, archive superseded P1 versions`.
- Verify: `git diff --stat HEAD~1` shows expected line deltas. CI (if any) green.
- Rollback: `git revert` with `--no-edit`.

**Ship gate (global):** total lines across `CLAUDE.md` + `learnings.md` + `memory/*.md` drop by ≥40%. Snapshot shows every archived rule ID reachable via a one-line redirect from its original location in Tier A or via archive index. Zero live information lost (verified by §6.2 grep of unique-sentence fingerprints).

---

## 8. TL;DR (10 bullets)

1. **Target shrinkage: 45–50%** on hot-tier corpus. `CLAUDE.md` HARD RULES: 453 → ~150 lines (67% cut). `learnings.md`: 593 → ~220 lines (63% cut). `memory/` files: 18 → 7 (61% dedup).
2. **11 superseded P1-* blocks** in `CLAUDE.md` (P1-G v3/legacy, P1-H/v3, P1-L/v2/v3, P1-Y v1, P1-Z v1, P1-AA v1, P1-CC v1) move to `docs/_archive/claude-md-superseded-2026-04-19.md`. Each has a one-line redirect in its ID's canonical spot.
3. **25 L-rules** that re-stated what a P1 rule already says are merged + deleted. 5 superseded-in-fact L-rules (L90, L109, L111, L114) archive. Numbering collisions (L18/L19/L20/L48/L49/L50/L52 appearing multiple times) are flagged as data-quality bugs.
4. **13 cross-project rules** (disk preflight, ffmpeg concat ceiling, Windows UTF-8, git branch drift verification, etc.) get promoted into categorized `Vault/rules/<CATEGORY>/rule-*.md` files. They qualify under the "pattern repeated 3+ times" policy.
5. **18 feedback_*.md files** consolidate into 6 DOMAIN_*.md files organized by topic, not by session date. Session-specific reviews that are fully absorbed become archive entries.
6. **Rule canonicalization:** every LIVE rule is rewritten in WHAT/WHERE/WHY format, ≤3 lines each. §4 shows 10 before/after examples.
7. **CLAUDE.md §HARD RULES gets a clean TOC** — 10 domain sections (AUDIO, TRIMMING, TRANSITIONS, MUSIC STRUCTURE, TITLE CARD, BEAT SYNC, MULTI-ANGLE, FULL-LENGTH CLIP CONTRACT, RENDER PIPELINE, INTRO) — each containing only live rules.
8. **Tier B warm memory** reorganizes by domain (phase1_pipeline, brand_identity, phase2_phase3, engine_stack, project_context) — one file = one topic. Loaded on demand, not session-chronological.
9. **Tier C archive** is grep-able cold storage at 3 paths (`docs/_archive/`, `Vault/_archive/2026-Q2/`, `memory/_archive/`). Every archived rule keeps its ID. Zero live information lost; nothing forgotten, just moved.
10. **User experience at session start:** instead of 1354 lines of stacked revisions, user+Claude read ~400 lines of clean, current rules grouped by domain. Archive exists but is never auto-loaded. Single source of truth per rule. Faster session warm-up, fewer contradictions, immediate "what is the current contract?" answerability.

---

## Summary

Current corpus is 1354 live-tier lines (CLAUDE.md HARD RULES 453 + learnings.md 593 + memory/ ~300 curated), of which roughly 50% is stacked revisions, triple copies of the same rule, or one-shot observations that never became rules. The curation plan moves superseded P1-* blocks + absorbed L-rules to a grep-able cold archive (with zero information loss — every archived ID keeps a one-line redirect), merges 25 L-rules into their P1 supersedors, extracts 13 cross-project patterns into categorized Vault/rules/ files, and consolidates 18 session-dated memory/ feedbacks into 6 domain files. The hot tier shrinks by ~50% while gaining a domain-grouped TOC and a uniform WHAT/WHERE/WHY rule format. Executed via 9 atomic commits with a snapshot at step 1 and a ship-gate at step 8. No files edited by this task; plan only.
