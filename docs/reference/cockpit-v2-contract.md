# Cockpit v2 Contract

Last updated: 2026-04-21

This is the live UI contract for `/studio`.

## Top-Level Modes

- `STUDIO`
- `LAB`
- `CREATIVE`

URL state keeps only `mode` and `page`:

- `/studio?mode=studio&page=clips`
- `/studio?mode=lab&page=forge`
- `/studio?mode=creative&page=packs`

## STUDIO

`STUDIO` has exactly two rows in the sidebar:

- `CLIPS`
- `EDIT`

### CLIPS

- Part browser and clip intake live here.
- Selecting a part sets `activePart` and drops into `EDIT`.

### EDIT

`EDIT` is the integrated NLE workspace in [studio-edit.js](/mnt/g/QUAKE_LEGACY/creative_suite/frontend/studio-edit.js).

It embeds these existing panels inside one canvas/workspace instead of exposing them as separate left-nav rows:

- Preview
- Timeline
- Audio
- FX graph
- Inspector

## LAB

Current LAB pages in [studio-pages.js](/mnt/g/QUAKE_LEGACY/creative_suite/frontend/studio-pages.js):

- `demos`
- `extraction`
- `patterns`
- `annotate`
- `flags`
- `forge`
- `engine`

Current stub behavior:

- `FORGE` status is honest about `ready` vs stub mode.
- Demo extraction is currently a queued stub response, so the UI logs `job_id` and message instead of fake fragment counts.

## CREATIVE

Current CREATIVE pages in [studio-pages.js](/mnt/g/QUAKE_LEGACY/creative_suite/frontend/studio-pages.js):

- `textures`
- `sprites`
- `skins`
- `maps`
- `md3`
- `prompts`
- `queue`
- `packs`

Current backend contracts:

- Asset browsers use `GET /api/assets?kind={maps|skins|sprites}` (shell-level grouping) and receive `{ kind, assets[], total }`.
- Queue panel uses `GET /api/variants/feed` (flat recent list) + `POST /api/variants/{id}/approve|reject`.
- Packs gate reads `GET /api/packs/status`.

### Kind → DB Category Mapping

| Shell kind | DB categories (catalog.py) |
|---|---|
| `maps` | `surface` (textures/*) |
| `skins` | `skin` (models/players/*) |
| `sprites` | `effect` (sprites/*, env/*) |

## Visual Records

Current 2026-04-21 cockpit screenshots:

- [studio_clips_page.png](/mnt/g/QUAKE_LEGACY/docs/visual-record/2026-04-21/studio_clips_page.png)
- [studio_edit_page.png](/mnt/g/QUAKE_LEGACY/docs/visual-record/2026-04-21/studio_edit_page.png)
- [cockpit-v2-lab-mode-stubs.png](/mnt/g/QUAKE_LEGACY/docs/visual-record/2026-04-21/cockpit-v2-lab-mode-stubs.png)
- [cockpit-v2-creative-mode.png](/mnt/g/QUAKE_LEGACY/docs/visual-record/2026-04-21/cockpit-v2-creative-mode.png)

Archived misleading smoke from the retired shell:

- [archive/cockpit-v2-phase1-smoke.png](/mnt/g/QUAKE_LEGACY/docs/visual-record/2026-04-21/archive/cockpit-v2-phase1-smoke.png)
