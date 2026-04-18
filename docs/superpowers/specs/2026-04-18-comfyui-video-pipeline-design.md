# ComfyUI Video Pipeline Module — Design Spec

**Date:** 2026-04-18
**Status:** Design draft — NOT scheduled until Phase 2 demo-parsing lands.
**Author:** Tr4sH + Claude (Sonnet 4.6)
**Parent:** Creative Suite v2 (`2026-04-17-creative-suite-v2-design.md`)
**Engine context:** Engine Pivot (`2026-04-17-engine-pivot-design.md`)

---

## 1. Purpose

Turn the Phase 1 render pipeline into a general-purpose **AI video-making
module** that slots into the same review loop we built for the asset
creative suite:

> **Demo → pattern-extracted frags → ComfyUI-assisted shot building →
> render draft → user review → final render.**

Phase 1 today assembles existing AVIs into Parts. Phase 2 will extract
frags directly from `.dm_73` demos (via WolfcamQL automation or the FT-1
custom parser) with known patterns + effects tags. Once we have that
pattern metadata, ComfyUI can enhance each frag BEFORE render:

- Upscale low-res AVIs to 4K (RealESRGAN / SwinIR).
- Generate bespoke per-frag intro cards (prompt ← frag metadata).
- Style-transfer slow-mo replay frames (AnimateDiff).
- Hallucinate alternate POVs (Stable Video Diffusion img2vid on a key frame).
- Generate filler / transition clips when the pipeline needs atmosphere
  and no AVI fits.

The goal is **one unified review-loop**:

```
pick frag(s) → choose pattern/effect → ComfyUI enhance (optional) →
assemble draft → user review → finetune → render final
```

Same shape as the asset flow in `2026-04-17-creative-suite-v2-design.md`.

---

## 2. Out of scope for v1

- **Live/real-time generation.** Every ComfyUI call is async + cached.
- **Multi-demo splicing across Parts.** One Part = one timeline.
- **Voice synthesis / narration.** Audio mixing stays as today (game +
  music + optional outro).
- **Full diffusion of gameplay.** We enhance real frames; we do not
  hallucinate entire matches.
- **Streaming API.** ComfyUI speaks HTTP; that's what we consume.

---

## 3. Architecture

```
phase1/                 existing — stays the render authority
phase2/                 demo parser + frag metadata (FT-1)
phase3/                 AI cinematography scoring
creative_suite/
  ├─ api/               FastAPI + SQLite WAL (unchanged)
  ├─ web/               importmap + Three.js (unchanged)
  ├─ comfy/             NEW — ComfyUI video module
  │    ├─ client.py           HTTP client for 127.0.0.1:8188
  │    ├─ workflows/          JSON workflow templates
  │    │   ├─ upscale_4k.json
  │    │   ├─ animatediff_slowmo.json
  │    │   ├─ svd_img2vid.json
  │    │   └─ sd3_intro_card.json
  │    ├─ jobs.py             job queue (SQLite-backed)
  │    ├─ cache.py            content-hash → output path
  │    └─ integration.py      ClipEntry → Job resolver
  └─ tests/
```

The key insight: **a ComfyUI workflow is a function from
(input_media, params) → output_media.** We hash the tuple, cache the
output on disk, and re-run the render pipeline with the cached output
swapped in for the original AVI.

---

## 4. Data model

Extend `ClipEntry` with an optional `comfy_spec`:

```python
@dataclass
class ComfySpec:
    workflow: str          # "upscale_4k" | "animatediff_slowmo" | ...
    params: dict[str, Any] # workflow-specific knobs
    cache_key: str         # content hash (src + workflow + params)

@dataclass
class ClipEntry:
    ...existing fields...
    comfy_spec: Optional[ComfySpec] = None
```

The renderer checks `entry.comfy_spec`:
- If present → resolve cache (hit = use cached mp4; miss = enqueue
  ComfyUI job, block until done, cache result).
- If absent → today's behavior (direct AVI use).

`cache_key = sha256(src_mtime + src_size + workflow + sorted(params))`.
Cached outputs live in `creative_suite/comfy/cache/<cache_key>.mp4`.

---

## 5. Workflow catalog (v1)

| Workflow | Trigger | Input | Output | Model | Use case |
|---|---|---|---|---|---|
| `upscale_4k` | Manual `[comfy=upscale]` | 1080p AVI | 4K mp4 | RealESRGAN x2 | YouTube final |
| `animatediff_slowmo` | `[comfy=slowmo_ai]` | 1080p AVI | 0.25× slow mp4 | AnimateDiff + motion LoRA | T1 peak replay |
| `svd_img2vid` | `[comfy=svd]` | Frame grab | 4s mp4 | SVD 1.1 | Hallucinated angle |
| `sd3_intro_card` | `[comfy=intro]` | Prompt text | 3s mp4 | SD3 + Ken Burns | Per-frag title |
| `controlnet_restyle` | `[comfy=restyle]` | AVI | Restyled mp4 | SDXL + ControlNet Tile | Q1 noir pack |

Each workflow is a ComfyUI `.json` committed to `creative_suite/comfy/workflows/`.
Params are passed via the ComfyUI API's prompt-slot injection.

---

## 6. Integration with existing pipeline

### 6.1 Clip-list syntax extension

```
# current
Demo (121) - 38.avi
Demo (209) - 183.avi [slow]

# new
Demo (121) - 38.avi [comfy=upscale_4k]
Demo (209) - 183.avi [comfy=animatediff_slowmo:strength=0.7]
```

`phase1/clip_list.py::parse_clip_entry` gains a `comfy=` flag parser.
Unknown workflows raise; params are `key=val` comma-separated.

### 6.2 normalize_and_expand

Before the current slow/zoom/fast branching, check `entry.comfy_spec`.
If set:
1. Look up cache. If hit, rewrite src to the cached mp4 and fall through.
2. If miss, enqueue a `ComfyJob` (creates ComfyUI HTTP request via
   `comfy/client.py`), block on completion, write output to cache,
   rewrite src.

The cache bypass means re-renders are free (same as today's
`normalized/` mp4 cache).

### 6.3 Review-mode interaction

Review-mode (`--review`) **skips** any `comfy_spec` that would cost more
than a fast CPU second. Upscales, AnimateDiff, SVD are all gated off.
Draft renders show the raw AVI with a "comfy pending" flag burned in
(top-right watermark) so the user sees which clips would be enhanced in
final.

This mirrors how review-mode already skips silence-detect probing: draft
speed is the priority; heavy ops move to final.

### 6.4 CLI

```bash
# Build drafts (no comfy, watermark on, fast encoder)
python -m phase1.render_part_v6 --part 6 --review

# Final with all comfy enhancements (no watermark, AV1 NVENC UHQ)
python -m phase1.render_part_v6 --part 6 --no-watermark

# Force re-run of specific comfy cache entries
python -m creative_suite.comfy.cache invalidate --workflow upscale_4k
```

---

## 7. Phase plan

### Phase 2A (unlocked by FT-1 demo parser)
- [ ] `creative_suite/comfy/client.py`: bare HTTP client (queue, poll,
      download) against 127.0.0.1:8188.
- [ ] `creative_suite/comfy/cache.py`: content-hash cache with atomic
      writes.
- [ ] `creative_suite/comfy/jobs.py`: SQLite-backed queue (WAL, reuses
      creative_suite DB).
- [ ] Clip-list `[comfy=...]` parser in `phase1/clip_list.py`.
- [ ] `normalize_and_expand` gains the comfy-resolve step.
- [ ] First workflow: `upscale_4k.json` (safest — no creative output).
- [ ] Review-mode bypass wiring.

### Phase 2B
- [ ] `animatediff_slowmo.json` — the creative big one. LoRA chooser in
      the review UI.
- [ ] `svd_img2vid.json` — hallucinated angle. Gate behind Gate CS-3
      (user approves per-clip before final).
- [ ] Review UI in `creative_suite/web/` shows comfy-before-vs-after
      side-by-side in md3viewer (same pattern as asset review).

### Phase 2C
- [ ] `sd3_intro_card.json` — per-frag title cards when the frag carries
      a notable-player tag (FT-5) or rare-weapon combo (FT-2).
- [ ] `controlnet_restyle.json` — bulk restyle for style-pack Parts
      ("Q1 noir", "unreal tournament neon"). Ties to Engine Pivot's
      `zzz_*.pk3` naming.

---

## 8. Gates

| Gate | Condition | Who |
|---|---|---|
| **CV-1** | ComfyUI 127.0.0.1:8188 healthcheck + 1 round-trip pass | Claude |
| **CV-2** | `upscale_4k` on reference clip `basewall01b.tga`-adjacent AVI matches the asset-flow reference | User |
| **CV-3** | AnimateDiff slow-mo preserves weapon accuracy colors (no rail-pink) | User |
| **CV-4** | SVD hallucinated angle approved per-clip (never batched) | User |
| **CV-5** | Full Part 6 review-loop with 1 upscale + 1 slowmo_ai under 5 min draft | Claude |

Each gate gets a visual before/after in `docs/visual-record/YYYY-MM-DD/`
per Rule VIS-1.

---

## 9. Risks

- **ComfyUI GPU contention with WolfcamQL render capture.** Phase 2 demo
  captures hammer the GPU. Solution: comfy jobs go on a separate queue
  that pauses while WolfcamQL is capturing; serial-only for v1.
- **Model drift:** an AnimateDiff output that looked great last week may
  look wrong after a LoRA update. Mitigation: cache key includes
  model_hash + lora_hash; updates force re-generation.
- **Cost of hallucinated angles** (SVD): easy to over-use and lose
  authenticity. Mitigation: per-clip Gate CV-4, never batched.
- **Ollama gemma3:4b-vision style-match conflicts with ComfyUI output:**
  the vision model critiques style matches; we may end up with ComfyUI
  generating something that vision rejects. Mitigation: vision score is
  advisory until Phase 2B.

---

## 10. Open questions

1. Does ComfyUI run on the same box as render, or on a separate rig? If
   separate, we need a network cache layer (SMB mount probably cheapest
   on the Windows setup).
2. Do we want per-frag "hero shot" generation (SDXL → md3-skinned
   character holding the weapon that killed them), or is that Phase 3?
3. Should the creative-suite web UI show a comfy-enhanced preview at
   asset-pick time, or only at Part-assemble time?
4. Is the hash-based cache good enough, or do we want proper
   content-addressable storage (git-lfs-style)?

These get answered during Phase 2A brainstorming — not in v1.

---

## 11. Relationship to Creative Suite v2

The asset creative suite (v2 spec) is the **asset-level** ComfyUI
integration: "enhance `basewall01b.tga` via ComfyUI, review, commit to
pk3." This spec is the **video-level** ComfyUI integration: "enhance a
whole frag or filler clip via ComfyUI, review, commit to the Part."

Same review-loop shape, same gate discipline, same cache pattern, same
Ollama gemma3:4b vision model scoring outputs. The two suites share:

- FastAPI + SQLite WAL server.
- ComfyUI HTTP client (`comfy/client.py`).
- Job queue (`comfy/jobs.py`).
- Cache (`comfy/cache.py`).
- gemma3:4b vision scoring.

Only the input type changes (image → video). This is why both suites
should live under `creative_suite/comfy/` as a single module.
