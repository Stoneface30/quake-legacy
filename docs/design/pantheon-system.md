# PANTHEON Design System
**Version:** 1.0  
**Date:** 2026-04-19  
**Author:** Claude Designer (design/phase1-pantheon-system branch)  
**Status:** Active — Review Console v2 + Cinema Suite target

---

## 1. Brand Identity

PANTHEON is the editing identity for QUAKE LEGACY fragmovie production. The name references the Roman temple of the gods — a place of deliberate craft, architectural weight, and cold stone precision. Visually this translates to:

- **Cold grey/silver** as the primary palette (temple stone, matte titanium)
- **Quake-red `#8a0a0a → #c41515`** for action moments (the arena, the kill, the render job)
- **Approval gold `#d4a04a`** for confirmed, passed, and finalized states (gate passed, render shipped)
- **Void black `#06060a`** as the engine frame (infinite darkness between sessions)

The aesthetic is **brutalist Quake-console** — no rounded corners, no gradients on structural elements, no decoration without meaning. Every visual element earns its place.

---

## 2. Color Tokens

All tokens live in `creative_suite/frontend/pantheon.css` as CSS custom properties.

### 2.1 Background Layers

| Token | Value | Usage |
|---|---|---|
| `--bg` | `#06060a` | Outermost void (body, between panels) |
| `--surface` | `#0d0d12` | Panel body fill |
| `--surface2` | `#12121a` | Raised surfaces (panel bars, inputs, wells) |
| `--border` | `#1e202c` | Structural borders |
| `--border-hot` | `#2e3040` | Hover/active borders, tighter gutters |

### 2.2 Cold Silver Palette (Primary Accent)

| Token | Value | Usage |
|---|---|---|
| `--silver` | `#8a909c` | Primary accent: labels, outlines, fills |
| `--silver-bright` | `#c0c6d0` | Headings, highlighted values |
| `--silver-dim` | `#4a5060` | Secondary labels, dimmed metadata |
| `--silver-mute` | `#252830` | Placeholder, disabled, muted text |
| `--silver-glo` | `rgba(138,144,156,.08)` | Hover background glow |
| `--silver-glo2` | `rgba(138,144,156,.14)` | Active/selected background glow |

> **Compatibility shim:** `--orange` maps to `--silver` so existing `style.css` references inherit the silver palette automatically. No `style.css` edits needed.

### 2.3 Quake-Red (Action / Danger / T1)

| Token | Value | Usage |
|---|---|---|
| `--red` | `#8a0a0a` | Base red: T1 tier, DROP sections, active render job |
| `--red-hot` | `#c41515` | Hot state: hover, active button, seam marker |
| `--red-glo` | `rgba(138,10,10,.22)` | Red aura (logo cross, seam lines) |
| `--red-glo2` | `rgba(196,21,21,.12)` | Subtle body vignette (body::before) |

### 2.4 Approval Gold (Success / Confirm / Highlight)

| Token | Value | Usage |
|---|---|---|
| `--gold` | `#d4a04a` | Gate PASS, status LED OK, rank badge |
| `--gold-dim` | `rgba(212,160,74,.12)` | Gold hover background |
| `--gold-glo` | `rgba(212,160,74,.06)` | Gold tooltip glow |

> **P1-Y v2 source:** warm off-white `#f5e8c8` (stored as `--cream`) + vertical gradient `#8a0a0a → #d4a04a` — these are the title card fill colors; referenced here for consistency.

### 2.5 Tier Colors

| Tier | Token | Value | Meaning |
|---|---|---|---|
| T1 | `--t1` | `var(--red-hot)` | Rarest/elite frags — red heat |
| T2 | `--t2` | `var(--silver)` | Main meal clips — stone silver |
| T3 | `--t3` | `#252830` | Filler/atmospheric — near-invisible |

### 2.6 Section Role Colors

| Role | Token | Value | Usage |
|---|---|---|---|
| DROP | `--drop` | `var(--red-hot)` | Climax / high-energy cut point |
| BUILD | `--build` | `var(--silver)` | Tension build-up |
| BREAK | `--brk` | `#252830` | Rest moment |
| INTRO | `--intro` | `#1a3050` | Cool entrance |
| OUTRO | `--outro` | `#28183a` | Dark curtain close |

---

## 3. Typography

### 3.1 Font Stack

| Role | Family | Source | Usage |
|---|---|---|---|
| **Hero** | Bebas Neue | Google Fonts (OFL) | Logo wordmark `PANTHEON`, large stat numbers, major labels |
| **Heading** | Black Ops One | Google Fonts (OFL) | Panel bar titles (`// RENDER COMPARE`), nav labels, section headers |
| **Data** | IBM Plex Mono | Google Fonts (OFL) | All timecodes, frame numbers, numeric data, code output |

> Both Bebas Neue and Black Ops One are imported via `@import` at the top of `pantheon.css`. No npm required — importmap-safe.

### 3.2 Size / Weight Scale

| Level | Family | Size | Weight | Letter-spacing | Color |
|---|---|---|---|---|---|
| Logo wordmark | Bebas Neue | 18px | 400 | 0.32em | `--silver-bright` |
| Panel bar title | Black Ops One | 10px | 400 | 0.22em | `--silver-bright` |
| Nav label | Black Ops One | 7px | 400 | 0.30em | `--silver-dim` |
| Data / timecode | IBM Plex Mono | 9–12px | 400–500 | 0.05–0.12em | `--text` |
| Caption / hint | IBM Plex Mono | 7–8px | 400 | 0.08–0.14em | `--silver-dim` |

---

## 4. Iconography & Glyphs

PANTHEON uses Unicode glyphs, not icon fonts or SVG sprites (importmap-safe, zero deps):

| Glyph | Meaning | Context |
|---|---|---|
| `⊕` | PANTHEON logo cross | Header wordmark prefix, red with glow |
| `//` | Code separator | Panel title prefix (`// RENDER COMPARE`) |
| `▶ ▌▌` | Playback controls | Video panel |
| `⇌` | Sync | Sync toggle button |
| `⊞` | Load/drop | File picker buttons |
| `▲ ▼` | Sort direction | Event panel sort toggle |
| `■` | Section color swatch | Flow legend |
| `▌` | Tier bar swatch | Flow legend |
| `│` | Separator | Legend divider |

---

## 5. Component Patterns

### 5.1 Buttons

Three semantic types, all using `font-family: var(--font-head)` for label text:

```
pth-btn-action   — Red fill  → HOT RED hover + red glow
                  Use: RENDER, APPROVE run, destructive actions

pth-btn-confirm  — Gold outline → gold fill hover
                  Use: APPROVE, SHIP, TAG version

pth-btn-ghost    — Silver-dim outline → silver hover
                  Use: LOAD, CANCEL, secondary actions
```

All buttons: no border-radius. Quake console is rectilinear.

### 5.2 Badges / Pills

```
pth-badge       — base: surface2 bg + border-hot outline + silver-dim text
pth-badge.t1    — red border + red-hot text
pth-badge.t2    — silver-mute border + silver text  
pth-badge.t3    — border-only, muted
pth-badge.drop  — red (= t1, same energy)
pth-badge.intro — blue-dark border + dim-blue text
pth-badge.outro — purple-dark border + dim-purple text
```

### 5.3 Data Values

Use `.pth-val` for monospace numbers:
```
.pth-val         — silver-bright (default)
.pth-val.gold    — gold (metric passes gate)
.pth-val.red     — red-hot (metric fails gate)
.pth-val.mute    — silver-dim (secondary stat)
```

### 5.4 Dividers

`.pth-divider` — gradient rule: transparent → border-hot → silver-mute → border-hot → transparent  
Creates "temple column" separators between content sections.

---

## 6. Structural Patterns

### 6.1 Panel Bar Anatomy

```
┌──────────────────────────────────────────────────────────────┐  ← surface2 bg
│ // PANEL TITLE          [DATA PILL] [− ZOOM] [+ ZOOM]       │  ← 26px bar-h
└──────────────────────────────────────────────────────────────┘  ← 1px border-hot
│                                                              │
│              panel body (surface bg)                        │
│                                                              │
```

- Title: Black Ops One, 10px, 0.22em spacing, silver-bright
- Pills: surface bg + border + silver-dim text (not filled)
- Buttons: ghost style inside bar

### 6.2 Header Anatomy

```
[⊕ PANTHEON // REVIEW CONSOLE v2]   [PART: 04 05 06]   [⊞ FLOW] [⊞ EVENT]   [● LIVE]
 ↑ Bebas Neue + red cross glow        ↑ Black Ops One     ↑ ghost btns         ↑ gold LED
```

Background: Three.js particle field (grey particles, 0.7 opacity) + subtle red-left body vignette.  
Bottom border: `1px border-hot` + `box-shadow: 0 4px 40px red-glo-8%`.

### 6.3 Temple Vignette

`body::before` applies:
1. Left ellipse: subtle red glow (arena entrance)
2. Right gradient: deep purple-black (studio darkness)

This matches IntroPart2.mp4 visual feel — the PANTHEON logo appears against dark stone with warm red-left atmospheric light.

---

## 7. Prototype Panel Scaffolding

`pantheon.css` ships scaffolding classes for the three prototype panels:

### Panel 7 — Tier A Preview (`.proto-*` + `.thumb-strip` + `.seam-marker`)

```
┌─ // TIER A PREVIEW ──────────────────── [0.25×] [0.5×] [1×] [2×] ─┐
│ [thumbnail strip — 48px — frames at 1s intervals with seam marks]   │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│                     <video> — 16:9                                  │
│                                                                     │
│ ─── scrub track ──────────────────── ⦿────────────────── 0:45 ─── │
│                ║        ║                  ║                        │
│                S1       S2                 S3       ← seam markers  │
├─ hotkeys ───────────────────────────────────────────────────────── ┤
│ [SPACE] play  [←][→] ±1s  [J][K] seam jump  [S] scrub-snap        │
└──────────────────────────────────────────────────────────────────── ┘
```

Classes: `.thumb-strip`, `.thumb-frame`, `.thumb-frame.seam-here`, `.seam-marker`, `.rate-toggle`, `.rate-btn`, `.hotkey-legend`, `.hk-pair`, `.hk-key`

### Panel 8 — Tier B Engine Scrub (`.ruler-row` + `.frame-counter`)

```
┌─ // TIER B ENGINE SCRUB ─────────────────────── [FRAME 1248/2400] ─┐
│ ─── ruler ────────────────────────────────────────────────────── │
│ 0s          10s          20s          30s          40s            │
│ ⌃            ⌃            ⌃            ⌃            ⌃              │
│ ─────────────────────────────────────────────────────────────── │
│                                                                   │
│                    <img id="engine-frame">                        │
│                    (JPEG from WebSocket, 4 Hz)                    │
│                                                                   │
│ ─── drag scrub ─────────── 8:52.4 ──────────────────────────── │
└──────────────────────────────────────────────────────────────── ┘
```

Classes: `.ruler-row`, `.ruler-tick`, `.ruler-tick.major`, `.ruler-tick.minor`, `.ruler-label`, `.frame-counter`

### Review Flow (`.diff-*` + `.approval-bar`)

```
┌─ // RENDER APPROVAL — PART 04 ──────────────────────────────────────┐
│ VERSION A (v9)                    VERSION B (v10)                   │
│ [                               ] [                               ] │
│       <video>                             <video>                   │
├─ CHANGES v9 → v10 ──────────────────────────────────────────────── │
│ music_volume     0.20 (old) →  0.30 (new)       LOUDER             │
│ seam_xfade       0.15s       →  0.40s            VISIBLE           │
│ clip_count       24          →  22                −2 CLIPS          │
├─ VERDICT ───────────────────────────────────────────────────────── │
│  [APPROVE v10 →→]   [REJECT — KEEP v9]   [REVISE: open notes]      │
└────────────────────────────────────────────────────────────────── ┘
```

Classes: `.diff-list`, `.diff-row`, `.diff-field`, `.diff-old`, `.diff-new`, `.diff-neutral`, `.approval-bar`, `.approval-verdict`, `.ver-input`

---

## 8. Motion & Interaction

- **Transition duration:** 120ms (fast — console tools, not consumer apps)
- **Easing:** linear (no ease-in-out — Quake is sharp)
- **Glow on focus:** border shifts from `--border-hot` to `--silver`, box-shadow adds `--silver-glo2`
- **Button active state:** fills with `--red` immediately (no fade-in on action)
- **LED blink:** `blink-g` (gold OK LED) = 3s cycle, `blink-s` (silver busy) = 1s cycle
- **Scanlines:** `repeating-linear-gradient` — 3px stripe, 6% opacity — minimal, never distracting

---

## 9. Before/After Summary (Review Console v2)

| Element | Before (style.css) | After (+ pantheon.css) |
|---|---|---|
| Primary accent | `#f5a623` ember-orange | `#8a909c` cold silver |
| Panel bar | Filled orange | Dark surface2 + silver-bright title |
| Logo | Orange glow | Bebas Neue, silver-bright + red ⊕ cross |
| T1 tier blocks | Orange | Red-hot (`#c41515`) |
| Seam markers | — | Red lines + glow |
| Buttons (active) | Black fill + orange text | Red fill + white text |
| Gate PASS LED | Green | Gold |
| Clip confidence bar | White 60% | Gold 50% |
| Body vignette | None | Subtle red-left temple atmosphere |

---

## 10. File Index

```
creative_suite/frontend/
  style.css        — Layout / structure skeleton (don't modify)
  pantheon.css     — PANTHEON brand override (this system)
  index.html       — Link both: style.css first, pantheon.css second
  prototypes/
    panel7/index.html     — Tier A preview UX prototype
    panel8/index.html     — Tier B engine scrub UX prototype
    review/index.html     — Render approval flow prototype

docs/design/
  pantheon-system.md   — This document
  render-review-flow.md — Detailed UX spec for the approval flow
```

---

## 11. Rules Compliance

| Rule | Compliance |
|---|---|
| P1-Y v2 | Title card colours `--cream` / `--red` / `--gold` are defined as tokens |
| VIS-1 | Before/after screenshots to be captured at `docs/visual-record/2026-04-19/` |
| CS-3 | No modification of `output/.git` — design files only |
| ENG-2 | No `zzz_*.pk3` changes — CSS only |
| Public repo | No player names, no .dm_73, no .env in any design file |
| No npm | All fonts via Google Fonts `@import` in CSS — no build step |
| Branch discipline | All work on `design/phase1-pantheon-system`, never committed to `main` |
