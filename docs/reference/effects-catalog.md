# QUAKE LEGACY — Effects & Capabilities Catalog

> What can be done, when, and with what tool. Phase-gated.
> Updated: 2026-04-16

---

## Phase 1 — FFmpeg Assembly (NOW)
*Works on existing AVI clip files. No WolfcamQL re-render needed.*

### Clip-Level Effects

| Effect | Flag | FFmpeg Filter | Notes |
|--------|------|---------------|-------|
| Slow-motion | `[slow]` | `setpts=2.0*PTS`, `atempo=0.5` | FP clips only — FL clips already slow from recording |
| Speed-up | `[speedup]` | `setpts=PTS/1.5`, `atempo=1.5` | 1.5x playback — good for T3 filler/transition |
| Zoom | `[zoom]` | `crop=iw/1.15:ih/1.15,scale=1920:1080:flags=lanczos` | 15% center crop, smooth zoom-in effect |
| Camera cut | `>` separator | Segment concatenation | Cut between FP and FL clips of same frag |

### Assembly Effects

| Effect | How | Notes |
|--------|-----|-------|
| Hard cut | default | Primary edit language — chain quality first |
| Flash cut | `xfade=offset=N:duration=0.08` | Near-invisible, use as default between clips |
| Section xfade | `xfade=offset=N:duration=0.5` | Only at major section breaks (T2→T1 climax) |
| Fade to black | `fade=t=out:st=N:d=0.5` | Outro only |
| PANTHEON intro | `prepend_intro()` | Trim IntroPart2.mp4 to 7s, concat. ALL parts. |

### Color Grade (grade_tribute preset)

```
contrast=1.3, saturation=1.25, brightness=0.0
gamma_r=1.0, gamma_b=0.97        ← kills reddish tint
bloom_sigma=16, bloom_opacity=0.22
sharpen_amount=0.5
```

### Audio

| Layer | Volume | Notes |
|-------|--------|-------|
| Game audio | 0.30 | MANDATORY — grenade hits, rail cracks, rocket booms |
| Music | 1.0 (faded ±5s) | `afade` in/out at part boundaries |
| Mix | `amix=inputs=2:duration=first:normalize=0` | Never discard game audio |

### Text Overlays

| Use | Filter | Notes |
|-----|--------|-------|
| Clip name (preview only) | `drawtext=fontsize=18:x=20:y=H-30` | Bottom-left, preview renders only |
| Part title | `drawtext=fontsize=48:x=(W-tw)/2:y=(H-th)/2` | Over T3 intro clip |
| Video title | Composite over T3 FL angle + white background | Per PANTHEON style ref |

### What Phase 1 CANNOT Do

- New camera angles (rocket cam, orbit cam, bullet follow)
- Change POV mid-frag to a different position not already captured
- Stabilization of shaky handheld-style motion (footage is fixed game capture)
- Any re-timing that requires knowing exact frag timestamp in demo

---

## Phase 2 — WolfcamQL Re-Render
*Requires demo re-rendering through WolfcamQL engine. New angles, new timing.*

### Capabilities

| Effect | How | Notes |
|--------|-----|-------|
| Follow-cam (rocket) | `cl_followrocket 1` cvar | Camera follows rocket projectile |
| Follow-cam (rail) | `cl_followrail 1` cvar | Camera follows railgun slug |
| Orbit / free cam | `wolfcam_specpos`, `wolfcam_specangles` | Full 6DOF camera placement |
| Slow-mo re-render | `timescale 0.1-0.5` | Capture at game engine level — cleaner than post |
| Freeze frame | `timescale 0.001` | Near-freeze for key moments |
| Custom FOV | `cg_fov 90-140` | Wider FOV for dramatic angles |
| First person replay | Default WolfcamQL | Re-render from player POV with clean HUD-off |
| Kill cam angle | Position cam at kill location | Witness kill from weapon impact point |
| Bullet time | Combined `timescale 0.05` + orbit camera | Full Matrix-style effect |

### Trigger Criteria (Phase 2 candidates from Phase 1 review)

Flag these in review MD files with `PHASE2:follow` or `PHASE2:orbit`:
- Rocket direct hit (direct = follow-cam candidate)
- Rail through-wall (orbital camera at kill point)
- Multi-kill in tight space (overhead view candidate)
- Long-range airshot (follow-cam + slow-mo combo)

### Command Reference

```
seekservertime <ms>          ← maps directly from Phase 3 frag timestamps
video avi name <filename>    ← start capture
cl_followrocket 1            ← enable rocket follow
timescale 0.25               ← 25% speed (cleaner than post slowmo)
quit                         ← stop capture when done
```

---

## Phase 3 — AI Cinematography Engine
*Automated frag scoring, camera decision making, clip selection.*

### AI-Scored Features

| Signal | How Measured | Use |
|--------|-------------|-----|
| Airshot detection | Victim Z-velocity at frag time | T1 candidate flag |
| Multi-kill window | N frags within M seconds | Climax candidate |
| Weapon rarity | MOD_ROCKET vs MOD_MACHINEGUN | Weight scorer |
| Angle novelty | FP vs FL ratio per part | Balance tracker |
| Energy arc | BPM beat grid + clip duration | Auto-assign to beat windows |

### AI-Assisted Tools Available

| Tool | Status | Use |
|------|--------|-----|
| Real-ESRGAN | Running (ComfyUI) | Upscale captured footage 2x-4x |
| RIFE | Running (ComfyUI) | Frame interpolation 60→120→240fps |
| Beat detection (librosa) | Installed | Assign clips to music energy windows |
| ComfyUI img2img | Running | Stylize individual frames (Phase 5 mostly) |

---

## Phase 5 — Asset Regeneration (VISION)
*Photorealistic weapon/texture replacement. Assets swap before WolfcamQL re-render.*

### Pipeline

```
pk3 archive (zip)
  └── models/weapons/lightning/lightning.md3    ← 3D mesh
  └── models/weapons/lightning/skin.tga         ← 256x256 diffuse texture
  └── models/weapons/lightning/skin_s.tga       ← specular map

Step 1: Extract pk3 → raw assets
  python -c "import zipfile; zipfile.ZipFile('pak0.pk3').extractall('extracted/')"

Step 2: Convert TGA → PNG
  Pillow: Image.open('skin.tga').save('skin.png')

Step 3: ComfyUI img2img
  - Model: Realistic Vision v5 or SDXL
  - ControlNet: Tile (structure preserve) + Canny edges
  - Prompt: "photorealistic metal weapon, industrial, high detail, 4K PBR texture"
  - Denoising strength: 0.55-0.70 (preserve UV layout, add photorealism)
  - Resolution: 4x upscale via Real-ESRGAN first, then img2img

Step 4: PNG → TGA repack
  Pillow: Image.open('skin_enhanced.png').save('skin.tga')

Step 5: Repack pk3
  zipfile.ZipFile('custom_photorealistic.pk3', 'w').write('skin.tga', ...)

Step 6: WolfcamQL loads custom pk3
  Place in: %USERPROFILE%/Quake Live/baseq3/
  QL loads highest-priority pk3 last (alphabetical — name zzz_photorealistic.pk3)
```

### Key Weapons (Priority Order)

| Weapon | File | Why |
|--------|------|-----|
| Lightning Gun | `models/weapons/lightning/` | The shaft — most used in CA, most screen time |
| Rocket Launcher | `models/weapons/rocketlauncher/` | Follow-cam candidate, explosion effects |
| Rail Gun | `models/weapons/railgun/` | Most cinematic — instant hit, beam visual |
| Plasma Gun | `models/weapons/plasma/` | Fast fire, good for multi-kill sequences |

### ComfyUI Workflow Node Graph (planned)

```
LoadImage → Real-ESRGAN 4x → ControlNet(Tile) → KSampler(img2img, dn=0.6)
                                    ↑
                          ControlNet(Canny, dn=0.4)
                          
Prompt: "photorealistic PBR weapon texture, metal scratches, industrial"
Neg:    "cartoon, anime, painted, illustration, blurry"
```

### Engine Texture Limits

- Q3/QL engine supports textures up to 2048x2048 (power of 2 required)
- Original textures: 64x64 to 256x256 → after 4x upscale: 256x1024
- Must stay power-of-2: 256x256 → 1024x1024 (pad or crop)
- `.shader` files reference texture paths — no change needed if filenames match

---

## Effects Decision Tree

```
Got a clip → What effect?

Is it T1 (rare, peak)?
  YES → Climax position. FL angle if available. No speedup.
        Consider PHASE2:follow for rockets/rails.
  NO  ↓

Is it T2 (main meal)?
  YES → FP default. Hard cut to chain. [zoom] optional on best moments.
        [slow] on key impact frames only.
  NO  ↓

Is it T3 (filler/cinematic)?
  YES → Intro/outro. FL preferred. [speedup] for boring sections.
        Cut short — these are breathers, not features.
```

---

## Music Sync Reference

| Energy Level | Beat Map | Clip Type |
|-------------|----------|-----------|
| HIGH (chorus/drop) | `assign_clips_to_beats()` HIGH window | T1 — place peak frags here |
| MID (verse) | MID window | T2 main body |
| LOW (breakdown/intro) | LOW window | T3 atmospheric, FL cinematic |

Tool: `python -m phase1.tools.music_frag_matcher --music part04_music.mp3 --part 4`

---

## Review → Phase Gate Flow

```
Phase 1 review MD  →  feedback_processor.py
  → consolidated.md
  → PHASE2:follow flags → Phase 2 render queue
  → PHASE3:airshot flags → Phase 3 scoring training
  → PHASE5:texture flags → Asset regeneration queue
```

All phase-crossing intelligence flows through the review MDs. Fill them thoroughly.
