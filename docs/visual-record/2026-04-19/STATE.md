# Current State — 2026-04-19

**Snapshot:** post-four-commit housekeeping PR (#4). Rendering Part 4 v12 path-B in background.

## Where Things Stand

### Phase 1 — video pipeline

| Part | v11 render (2026-04-19) | v12 path-B (in progress) |
|---|---|---|
| 4 | **FAILED_LEVEL_GATE** (delta=-22.7 LU with buggy measurement, -9 LU with honest measurement). 8,395 MB, 26.2 min. Rendered at 20:26. | Running bg `bvyat8cyh`. Predicted delta=+12.4 LU (PASS). ETA ~57 min from kick. |
| 5 | **rc=127 crash** at 20:38. No output. Inherited same audio bug. | queued after Part 4 passes |
| 6 | not attempted | queued after Part 5 passes |

**What worked in v11:**

- Sync drift: 10.7 ms (Rule P1-BB split-graph — under 40 ms ship gate) ✅
- Music plan: 10 tracks stitched, 9 seams, full-song queue (Rule P1-AA v2) ✅
- Event recognition: 120/121 chunks (Rule P1-Z v2) ✅
- Beat-snapped cut offsets: 120/120 seams ✅
- Flow planner v2: 36/120 event-anchored seams ✅

**What failed:**

- P1-G v5 level gate: delta=-9 LU (music 9 LU louder than game). Root cause: both sides of the gate measurement were reading raw stems instead of the rendered mix. Bugs caught in the audit, path-B fix in flight.

### Cinema Suite (shipped 2026-04-19)

- 132/132 pytest pass on main
- 8 panels live (clip list, annotation, flow planner, audio viz, rebuild trigger, style pack, tier-A preview, git flow)
- 4 code-review findings fixed (CS-1..CS-6 hard rules all enforced)
- **User is testing the UI now** — blockers logged to chat, fixed in priority order

### Engine dissection

- 17 engines under `game-dissection/engines/dissection/` with ARCHITECTURE / EXTENSION_POINTS / QUIRKS triads
- Proto-73 port: 6 of 8 patches generated (GPL-2.0 headers preserved)
- q3mme fork staged at `engines/_forks/q3mme/` with upstream `.git/`
- `tools/quake-source/` retired (1.2 GB reclaimed)

### Memory system

- 3-tier live: A (CLAUDE.md 470 lines + learnings.md 301 lines + Vault/rules/), B (6 DOMAIN docs), C (_archive/)
- 40 P1-* rules canonicalized to WHAT/WHERE/WHY format; 11 superseded blocks archived verbatim

## Screenshots (this session)

| File | What it shows |
|---|---|
| `part4_v11_title_card.png` | Title card at t=13s (PANTHEON 5s + title 8s into body) — first-frame visual sanity |
| `part4_v11_body_5min.png` | Mid-body frame (5 min in) — confirms tier interleave + FL cut visible |
| `part4_v11_body_15min.png` | Deep body frame (15 min in) — mid-song transition region |

## Where to find things

| Asset | Path |
|---|---|
| v11 FAILED render (for listen-test) | `output/Part4_v11_2026-04-19_1929_FAILED_LEVEL_GATE.mp4` |
| v12 path-B log (live) | `/tmp/regen_p4_v12.log` |
| v12 master log | `/tmp/regen_p4_master.log` |
| Honest level gate prediction | math in commit `347776db` body |
| PR #4 | https://github.com/Stoneface30/quake-legacy/pull/4 |
| Creative Suite entry | `python -m creative_suite` |
| UI review channel | this chat session |

## Follow-up debt (carried into next session)

- `docs/INDEX.md` broken links from B3 archive moves
- `docs/visual-record/README.md` never authored
- ~18 markdown files still cite retired `tools/quake-source/` paths
- Patch 0008 `shipped-binary-deltas.patch` pending `wolfcamql-local-src` clone
- 1,427 pre-existing pyright errors (baseline, not merge-introduced)
- C track kickoff (Split 2 / ENG-1 Path A, q3mme fork + proto-73 port) queued
