# TR4SH QUAKE — Phase 1 Cockpit (Frontend Skeleton)

Pre-stage static shell for the Phase 1 Cockpit UI. No build tooling, no npm, no backend wiring yet — plain HTML + CSS + ES modules with an importmap for a future Three.js dependency. Three panels: A/B render compare (scrub-synced `<video>` pair labeled v10.1 / v10.2), flow-plan timeline (SVG, clips colored by tier with event ticks, downbeat lines, and seam cuts), and event diversity bar chart (SVG, reads `output/part04_event_diversity.json` with fallback to an inline mock). Brutalist Quake-console styling: `#0a0a0a` background, `#d4a04a` gold foreground, `#8a0a0a` red accent, Black Ops One header + Share Tech Mono body, thick borders, 90° corners, no shadows.

## Run it

```bash
cd G:/QUAKE_LEGACY/creative_suite/frontend
python -m http.server 8000
# open http://localhost:8000
```

The event-diversity fetch walks a few relative paths so it works both from the frontend dir and (later) from a repo-root server; if none resolve it falls back to an inline mock so the shell always renders.

## Next (Designer session)

- Hook videos to real `v10.1` / `v10.2` renders and wire a shared scrubber bar.
- Replace mock `flow_plan.json` with the live planner output from `phase1/`.
- Add section shading (build / drop / break) on the timeline from `partNN_music_structure.json`.
- Tighten the Quake-console type scale, add CRT scanline overlay, plasma-hover states on tiers.
- Thread in Three.js (via the importmap already present) for a map-thumbnail strip above the timeline.
