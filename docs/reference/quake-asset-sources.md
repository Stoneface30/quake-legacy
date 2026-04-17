# Quake Asset Sources — Phase 5 Reference

> Existing HD asset packs for Q3/QL. Download these for immediate visual upgrade
> before running ComfyUI pipeline. Stack multiple pk3s for best results.
> Updated: 2026-04-16

---

## How pk3 Loading Works (Engine)

- pk3 = ZIP file. Rename to `.zip`, open with 7-Zip. No special tool needed.
- Engine loads pk3s in **alphabetical order** — later-letter files win.
- Custom pack naming: `zzz_photorealistic.pk3` → always wins over stock assets.
- Weapon models path: `models/weapons2/<weaponname>/<name>.md3` + `<name>.tga`
- WolfcamQL uses same baseq3 asset loading — drop pk3 in WolfcamQL's baseq3 and it loads automatically at render time.

## Priority Download List (for immediate fragmovie use)

### 1. CZ45 Q3A Weapon Model Remake v1.0 ⭐ START HERE
- URL: https://www.moddb.com/mods/cz45modbundle/addons/cz45-q3a-weapon-model-remake-v10
- ALL weapons: Lightning Gun, Railgun, RL, Plasma, Gauntlet, BFG
- New geometry + retextured. 3D muzzle flashes. Updated shaders.
- Drop pk3 in WolfcamQL's baseq3/. Done.
- Updated April 2025. Actively maintained.

### 2. Q3Plus HD Weapon Skins + Effects ⭐ FRAGMOVIE ESSENTIAL
- URL: https://www.moddb.com/mods/q3plus
- HD weapon skins + controllable LG beam styles (sx_lightningStyle 0/1/2/3)
- Railgun trail styles (sx_rgStyle 0/1/2)
- The photorealistic shaft — THIS is what you want for cinematic LG shots
- HD explosions, projectiles, smoke effects too
- High-res QL Textures addon: https://www.moddb.com/mods/q3plus/addons/high-resolution-ql-textures

### 3. Quake Live 4x Textures for Q3
- URL: https://www.moddb.com/mods/toodlesa51/downloads/quake-live-4x-textures-for-quake-iii-arena
- QL textures (matches your source demos) upscaled 4x
- Most contextually appropriate — your demos ARE QL, so QL textures = correct

### 4. Neural Upscale — Object Textures
- URL: https://www.moddb.com/mods/quake-3-neural-upscale/addons/object-textures
- Weapons, pickups, lamps, skulls — neural upscaled
- Modular — stacks with CZ45 models (textures separate from models)
- Requires ioquake3 or quake3e (base engine errors on high-res)

### 5. ioquake3 Kpax CC Pack (CC Licensed ← Phase 4 safe)
- URL: https://ioquake3.org/extras/replacement_content/
- Only CC-licensed Q3 replacement pack
- Map textures, not weapons — but safe to bundle in Phase 4 public tool
- File: xcsv_hires.zip → extract to baseq3

### 6. Black HD Weapon Skins (Steam Workshop)
- URL: https://steamcommunity.com/sharedfiles/filedetails/?id=1284357549
- All key weapons: LG, RG, RL, Plasma, Gauntlet, MG, SG, GL
- Clean black finish — high contrast, reads well in video

## Stacking Strategy for Best Result

```
baseq3/
  pak00.pk3            ← QL stock (lowest priority)
  quake-live-4x.pk3    ← QL textures 4x upscaled
  neural-objects.pk3   ← neural upscaled weapon object textures
  q3plus-hd.pk3        ← HD weapon skins (overrides above)
  cz45-weapons.pk3     ← new weapon geometry (overrides textures)
  zzz_photorealistic.pk3  ← your ComfyUI-regenerated textures (WINS ALL)
```

## Tools Needed

| Tool | Purpose | URL |
|------|---------|-----|
| 7-Zip | Open/repack pk3 files | Standard install |
| PakScape | GUI pk3 explorer | https://gamebanana.com/tools/2548 |
| Noesis | MD3 → OBJ/FBX conversion | https://www.richwhitehouse.com |
| QLMM | QL mod manager, pk3 scanner | https://github.com/bonkmaykrQ/QLMM |

## Phase 5 Pipeline — ComfyUI Enhancement

For each weapon in `models/weapons2/`:

```
1. Unpack pk3 → extract <weapon>.tga (256x256 typical)
2. Pillow: TGA → PNG
3. Real-ESRGAN 4x → 1024x1024 PNG
4. ComfyUI img2img:
   - ControlNet: Tile (preserve UV layout)
   - Model: Realistic Vision v5
   - Prompt: "photorealistic PBR metal weapon, industrial, scratched, 4K"
   - Denoising: 0.55-0.70
5. PNG → TGA (Pillow, preserve alpha)
6. Repack into zzz_photorealistic.pk3
7. Drop in WolfcamQL baseq3/
8. Re-render frag clips → photorealistic weapons in footage
```

## Weapon Model Paths (Q3/QL)

```
models/weapons2/
  lightning/          ← SHAFT (most important for CA fragmovie)
    lightning.md3
    lightning_ring.md3
  railgun/
    railgun.md3
  rocketl/
    rocketl.md3
  plasma/
    plasma.md3
  machinegun/
    machinegun.md3
  gauntlet/
    gauntlet.md3
  grenadel/
    grenadel.md3
  shotgun/
    shotgun.md3
```

## The Photorealistic Shaft Vision

What you did in Blender (manual reskin) → automate via ComfyUI:
1. Extract `lightning.md3` + `lightning.tga` from WolfcamQL's pak00.pk3
2. Blender render of MD3 → orthographic UV reference images (user does this)
3. ComfyUI img2img on each texture face → photorealistic metal/carbon fiber
4. Repack → place in WolfcamQL baseq3/ as `zzz_shaft_photorealistic.pk3`
5. Every WolfcamQL re-render now has the photorealistic shaft in-game

This means the weapon detail exists IN THE ACTUAL FOOTAGE — not a post-process composite. Every slow-mo CA frag clip from Phase 2 re-renders has it automatically.
