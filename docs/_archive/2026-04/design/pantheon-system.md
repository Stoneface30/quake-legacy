# PANTHEON Design System
**Version:** 1.1 (corrected — Nauru flag palette)
**Date:** 2026-04-19
**Author:** Claude Designer (design/phase1-pantheon-system branch)
**Status:** Active — Review Console v2 + Cinema Suite target

---

## 1. Brand Identity

### Clan history (the canonical source of truth)

**Pantheon / pTn** was a Quake Live competitive clan. The name was chosen deliberately — the Roman Pantheon as a metaphor for the team: a gathering of the formidable, built with precision and weight. The colors were **always yellow/gold and blue**, and the explicit visual reference was the **Nauru island flag**:

```
  ┌──────────────────────────────────────────────────────────────┐
  │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  ← deep royal blue  #002B7F
  │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  ← yellow stripe    #FFC61E
  │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
  │  ✦  ← white 12-pointed star  #FFFFFF                        │
  └──────────────────────────────────────────────────────────────┘
```

The **temple metaphor** applies to *form* — rectilinear, no rounded corners, every element earns its place, deliberate weight in spacing and type. But the *color* belongs entirely to the clan's competitive identity.

> **Design correction note (L142):** An earlier draft of this doc used cold silver + Quake-red, derived from word-association with "Roman temple" and generic console aesthetics. This was wrong. The actual source is the Nauru flag. All tools should check L142 in `Vault/learnings.md` before assigning brand colors to any named team or project.

---

## 2. Color Tokens

All tokens live in `creative_suite/frontend/pantheon.css` as CSS custom properties.

### 2.1 Flag Source Values (reference — do not change)

| Name | Hex | Flag element |
|---|---|---|
| `--nauru-blue` | `#002B7F` | Flag field (background) |
| `--nauru-gold` | `#FFC61E` | Yellow horizontal stripe |
| `--nauru-white` | `#FFFFFF` | 12-pointed star |

### 2.2 Background Layers (blue-tinted void)

| Token | Value | Usage |
|---|---|---|
| `--bg` | `#040610` | Outermost void — deep space black-blue |
| `--surface` | `#090c18` | Panel body fill |
| `--surface2` | `#0d1228` | Raised surfaces (panel bars, inputs) |
| `--border` | `#151d3a` | Structural borders |
| `--border-hot` | `#1e2a50` | Hover/active borders |

### 2.3 pTn Blue (structural, cool depth)

| Token | Value | Usage |
|---|---|---|
| `--blue` | `#1a3e9a` | Screen-adapted Nauru blue |
| `--blue-bright` | `#2a5acc` | Hover / active / link blue |
| `--blue-dim` | `#0d2060` | **Panel bar background** |
| `--blue-deep` | `#081540` | Deep wells, footer, button text on gold |
| `--blue-mute` | `#0a1440` | Disabled backgrounds |
| `--blue-glo` | `rgba(26,62,154,.22)` | Blue aura |

### 2.4 pTn Gold (primary accent, glory, action)

| Token | Value | Usage |
|---|---|---|
| `--gold` | `#f5c518` | **Primary accent** — Nauru stripe, adapted |
| `--gold-bright` | `#ffd740` | Hover / active gold |
| `--gold-dim` | `#c99a10` | Dimmed gold |
| `--gold-pale` | `#ffe580` | Very light tint for subtle highlights |
| `--gold-glo` | `rgba(245,197,24,.20)` | Gold aura |
| `--gold-glo2` | `rgba(245,197,24,.08)` | Soft gold background hover |

> **Compat shim:** `--orange` maps to `--gold` so `style.css` references (scrub-fill, logo glow, panel bar, etc.) inherit the clan gold automatically. No edits to `style.css` required.

### 2.5 Flag Star White (text hierarchy)

| Token | Value | Usage |
|---|---|---|
| `--star` | `#e8eef8` | Primary body text |
| `--star-dim` | `#8090b8` | Secondary labels, metadata |
| `--star-mute` | `#2a3060` | Placeholder, disabled |

### 2.6 Tier Colors

| Tier | Token | Color | Meaning |
|---|---|---|---|
| T1 | `--t1` | `var(--gold)` | Rarest/elite — **flag yellow** (the clan's gold) |
| T2 | `--t2` | `var(--blue-bright)` | Main meal — **flag blue** (the clan's field) |
| T3 | `--t3` | `#0d1228` | Filler — near-invisible dark |

### 2.7 Section Role Colors

| Role | Token | Value |
|---|---|---|
| DROP | `--drop` | `var(--gold)` — climax = clan gold |
| BUILD | `--build` | `var(--blue-bright)` — drive = clan blue |
| BREAK | `--brk` | `#1a2050` — rest = dim blue |
| INTRO | `--intro` | `#0d2060` — deep entrance |
| OUTRO | `--outro` | `#0a1840` — darker curtain |

---

## 3. Typography

### 3.1 Font Stack

| Role | Family | Source | Usage |
|---|---|---|---|
| **Hero** | Bebas Neue | Google Fonts (OFL) | Logo `PANTHEON` wordmark, large stat numbers |
| **Heading** | Black Ops One | Google Fonts (OFL) | Panel bar titles (`// RENDER COMPARE`), nav labels |
| **Data** | IBM Plex Mono | Google Fonts (OFL) | Timecodes, frame counts, numeric data |

Both decorative fonts are `@import`ed at the top of `pantheon.css`. No npm, no build step.

### 3.2 Size / Weight Scale

| Level | Family | Size | Letter-spacing | Color |
|---|---|---|---|---|
| Logo wordmark | Bebas Neue | 19px | 0.32em | `--gold` |
| Panel bar title | Black Ops One | 10px | 0.22em | `--gold` |
| Nav label | Black Ops One | 7px | 0.30em | `--star-dim` |
| Data / timecode | IBM Plex Mono | 9–12px | 0.05–0.12em | `--star` |
| Caption / hint | IBM Plex Mono | 7–8px | 0.08–0.14em | `--star-dim` |

---

## 4. Structural Patterns

### 4.1 Panel Bar Anatomy

```
┌──────────────────────────────────────────────────────────────┐  ← --blue-dim bg
│ [gold ⊕] // PANEL TITLE          [PILL] [BUTTON] [BUTTON]   │  ← gold title text
└──────────────────────────────────────────────────────────────┘  ← 1px --gold border
│                                                              │
│              panel body (--surface bg)                       │
```

### 4.2 Header Anatomy

```
[⊕ PANTHEON // REVIEW CONSOLE v2]    [PART: 04 05]   [⊞ FLOW]   [● LIVE]
 gold cross + gold wordmark           gold active btn   ghost btn   gold LED
```
Header background: `--blue-deep` + `border-bottom: 2px solid --gold` (flag stripe at the top).
Body vignette (`body::before`): gold-left radial (flag stripe light source) + blue-right depth.

### 4.3 Flag Stripe Reference Line

The 2px gold `border-bottom` on the header is a direct visual echo of the Nauru flag stripe — it appears as a bright gold line separating the deep blue header from the dark body, exactly as the yellow stripe bisects the blue flag.

---

## 5. Component Patterns

### 5.1 Buttons

```
pth-btn-action  — Gold fill + blue-deep text (flag colors: stripe on field)
                  Use: APPROVE, RENDER, primary calls-to-action
                  Hover: gold-bright + gold glow

pth-btn-confirm — Blue outline + blue text
                  Use: CONFIRM, secondary ok actions
                  Hover: blue-glo bg + star text

pth-btn-ghost   — dim border + star-dim text
                  Use: CANCEL, LOAD, minor actions
                  Hover: gold border + gold text
```

### 5.2 Badges / Pills

```
pth-badge.t1    — gold border + gold text    (elite = flag gold)
pth-badge.t2    — blue border + blue text    (main = flag blue)
pth-badge.drop  — gold border + gold text    (same energy as T1)
pth-badge.build — blue border + blue text
pth-badge.intro — dark-blue border + dim-blue text
```

### 5.3 Divider

`.pth-divider` — gradient: transparent → border-hot → **gold-dim** peak → border-hot → transparent
The gold peak at 50% references the Nauru flag stripe crossing the full width.

---

## 6. Before/After Summary

| Element | v1.0 (WRONG — silver+red) | v1.1 (CORRECT — Nauru flag) |
|---|---|---|
| Brand reference | Roman temple vibe | **Nauru island flag** |
| Primary accent | `#8a909c` cold silver | `#f5c518` flag gold |
| Panel bars | Dark surface2 + silver title | **Deep blue `#0d2060`** + **gold title** |
| Header border | `1px silver` | **`2px gold`** (flag stripe) |
| T1 tier | red-hot | **gold** (clan's color for the best) |
| T2 tier | silver | **blue** (clan's field color) |
| Logo cross `⊕` | red glow | **gold glow** |
| Active button | red fill | **gold fill + blue-deep text** |
| Gate PASS LED | gold | **gold** (unchanged — correct both times) |
| Body vignette | red-left (wrong) | **gold-left (flag stripe atmosphere)** |
| Background tint | neutral near-black | **blue-tinted near-black** |

---

## 7. Rules Compliance

| Rule | Compliance |
|---|---|
| L142 | Brand colors now sourced from Nauru flag — never infer from name alone |
| P1-Y v2 | `--cream` / `--gold` title card colors still tokenized (gold is now correct) |
| VIS-1 | Before/after screenshots to `docs/visual-record/2026-04-19/` |
| CS-3 | No `output/.git` modifications |
| Public repo | No player names, no .dm_73, no .env |
| No npm | Google Fonts `@import` only |
| Branch discipline | `design/phase1-pantheon-system`, never `main` |

---

## 8. File Index

```
creative_suite/frontend/
  style.css        — Layout skeleton (do not modify)
  pantheon.css     — PANTHEON/pTn brand (this system, v1.1)
  index.html       — Link order: style.css → pantheon.css
  prototypes/
    panel7/        — Tier A preview UX prototype (gold seam markers)
    panel8/        — Tier B engine scrub prototype (gold playhead)
    review/        — Render approval flow (gold APPROVE button)

docs/design/
  pantheon-system.md       — This document
  render-review-flow.md    — UX spec for the approval flow
```
