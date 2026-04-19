# Render Approval Flow — UX Spec
**Version:** 1.0  
**Date:** 2026-04-19  
**Author:** Claude Designer (design/phase1-pantheon-system)  
**Prototype:** `creative_suite/frontend/prototypes/review/index.html`

---

## 1. Purpose

The Render Approval Flow gives the user (creative director / quality judge) a structured, single-screen interface for reviewing two versions of a Part render side-by-side, understanding exactly what changed between them, recording a decision, and tagging the approved version for archival.

---

## 2. Screen Layout

```
┌─ PANTHEON // RENDER APPROVAL CONSOLE ─────────────── PART 04 ─────┐
│                                                                      │
│ ● AWAITING REVIEW · Comparing v9 → v10 · 8 parameter changes       │
│                                                                      │
│ // RENDER COMPARE                          [⇌ SYNC]                 │
│ ┌───────────────────────────┐  ┌───────────────────────────────┐    │
│ │ VERSION A  [v9 · 2026-04] │  │ VERSION B  [v10 · 2026-04]   │    │
│ │                           │  │                               │    │
│ │  [⊞ DROP v9 MP4]          │  │  [⊞ DROP v10 MP4]            │    │
│ │                           │  │                               │    │
│ └───────────────────────────┘  └───────────────────────────────┘    │
│ 0:00 ─────────────────────────────────────── 8:12  [▶ PLAY BOTH]   │
│                                                                      │
│ // CHANGES v9 → v10                        [8 CHANGES]             │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ DOMAIN  RULE     FIELD              v9 (OLD)    v10 (NEW)  IMPACT│ │
│ │ AUDIO   P1-G v4  music_volume       0.30 ~~     0.20       ↓ QT │ │
│ │ AUDIO   P1-G v4  music_fadein_s     0.0         2.0        FADE │ │
│ │ VIDEO   P1-H v4  seam_xfade_dur     0.15s ~~    0.40s      VISB │ │
│ │ TRIM    P1-L v4  clip_head_trim_fp  1.0s ~~     0.0s       FREE │ │
│ │ TRIM    P1-L v4  clip_tail_trim_fp  2.5s ~~     0.0s       FREE │ │
│ │ TRIM    P1-L v4  clip_head_trim_fl  2.0s ~~     1.0s       −1s  │ │
│ │ INTRO   P1-X     intro_clip_duration 7.0s ~~    5.0s       −2s  │ │
│ │ CLIPS   P1-U     clip_count         24          22         −2   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ REVIEW NOTES                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ (textarea)                                                       │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ PENDING REVIEW  [version tag input]  [↩ REVISE] [✕ REJECT] [✓ APPROVE →→]│
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Specs

### 3.1 Status Bar

Single-line across the top. Three states:

| State | LED | Text | Notes |
|---|---|---|---|
| `pending` | ● Silver blinking | `AWAITING REVIEW · Comparing vN → vM · K changes` | Default on page load |
| `approved` | ● Gold solid | `APPROVED · vM ships as [tag]` | After APPROVE action |
| `rejected` | ● Red solid | `REJECTED · vN stays` | After REJECT action |

The status bar writes `Notes: <reviewer text>` in the sub-line after verdict.

### 3.2 Video Compare

Two `<video>` elements in a 1:1 grid. Each accepts drag-and-drop or file browse.

**SYNC toggle** (`⇌ SYNC` button, red when active):
- When ON: `vid-b.currentTime = vid-a.currentTime` whenever A's `timeupdate` fires with >100ms drift.
- When OFF: videos play independently.

**PLAY BOTH** button: toggles both videos simultaneously.

**Shared scrub track**: scrubbing seeks both videos (respects SYNC state).

**Version overlay stamps**: when verdict is set, a rotated stamp appears over the relevant video:
- `APPROVED` in gold (V10 overlay) 
- `SUPERSEDED` in red (V9 overlay, appears after approval)
- `REJECTED` in red (V10 overlay)

### 3.3 Changelist

Auto-populated from `flow_plan.json` git diff (backend) or inline mock data (prototype).

**Columns:**
| Column | Width | Content |
|---|---|---|
| DOMAIN | 90px | `AUDIO`, `VIDEO`, `TRIM`, `INTRO`, `CLIPS` — Black Ops One, muted |
| RULE | 60px | Rule ID (e.g. `P1-G v4`) — 8px, very muted |
| FIELD | 160px | Parameter name from `Config` class |
| v9 (OLD) | 160px | Old value in red strikethrough |
| v10 (NEW) | 120px | New value — gold if positive, red-hot if worse, silver if neutral |
| IMPACT | flex | Human-readable change summary, hover shows full note |

**Impact types:**
- `positive` — gold text (improvement per hard rules)
- `negative` — red-hot text (regression, needs justification)
- `neutral` — silver text (structural change, neither better nor worse)

Row hover: silver-glo background.

### 3.4 Notes Field

Plain `<textarea>` with PANTHEON styling. Content is included in the verdict payload (backend: `POST /approvals` with `{version, verdict, notes, tag}`).

### 3.5 Approval Bar

Four elements right-to-left:
1. **APPROVE v10 →→** — gold outline button, requires version tag to be non-empty
2. **✕ REJECT — KEEP v9** — ghost button, turns red on hover
3. **↩ REQUEST REVISE** — neutral ghost button, sends revision request back to pipeline
4. **version tag input** — required before APPROVE; validates pattern `[a-zA-Z0-9._-]+` (matches `_git_flow.py` refname validator)

**Verdict label** (left side) updates:
- `PENDING REVIEW` → silver-dim
- `APPROVED — v10 SHIPS` → gold  
- `REJECTED — v9 STAYS` → red-hot
- `REVISION REQUESTED` → silver-dim

---

## 4. Data Model

### 4.1 Frontend → Backend payload (future wiring)

```json
{
  "part": 4,
  "version_old": "v9",
  "version_new": "v10",
  "verdict": "approved",
  "tag": "v10.1-approved",
  "notes": "Music finally sits under game audio. Transitions visible at 0.4s. FP clips full-length is a major improvement.",
  "timestamp": "2026-04-19T15:40:00Z",
  "changes": [...]
}
```

### 4.2 Diff source

In production, the diff is computed by `_git_flow.py` comparing `output/.git` tags:
```bash
git diff part04/v9..part04/v10 -- part04_flow_plan.json
```
The frontend receives it as `GET /parts/4/diff?from=v9&to=v10` returning the change array.

---

## 5. Keyboard Shortcuts

| Key | Action |
|---|---|
| `Space` | Play/pause both videos |
| `←` `→` | Seek ±1 frame |
| `Shift ←/→` | Seek ±1 second |
| `A` | Focus version A |
| `B` | Focus version B |
| `Enter` | Submit verdict (when tag is filled) |

---

## 6. States & Transitions

```
LOAD → [drop v9 + v10 videos] → COMPARE
COMPARE → [scroll changelist, play, scrub] → JUDGE
JUDGE → [fill notes + tag] → (APPROVE | REJECT | REVISE)

APPROVE → status=approved, B stamp="APPROVED", A stamp="SUPERSEDED"
           → backend: git tag part04/v10.1-approved, copy to deliverables
REJECT  → status=rejected, B stamp="REJECTED"
           → backend: no action, v9 remains HEAD
REVISE  → status=pending, note appended to pipeline queue
           → backend: POST /rebuild with revision notes
```

---

## 7. Future Enhancements (Phase 2 inputs)

Once Phase 2 frag data is available:
- **Frag heatmap diff**: show which frags were added/removed between versions
- **Per-seam VMAF delta**: score each seam point for quality regression
- **Event diversity delta**: compare event type distribution between versions
- **Auto-annotation**: highlight which rule changes are responsible for each clip-level diff

---

## 8. Implementation Notes

- **CS-3 compliance**: the approval writes via `_git_flow.py`'s `save_and_tag()` — never direct git commands
- **No direct mp4 serving from `output/`**: the backend serves via `GET /parts/{n}/render/{tag}` for security
- **VIS-1**: Playwright captures both video states (before/after verdict) at session close
- **Branch**: prototype lives on `design/phase1-pantheon-system`; production wiring in `creative-suite-v2-step3`
