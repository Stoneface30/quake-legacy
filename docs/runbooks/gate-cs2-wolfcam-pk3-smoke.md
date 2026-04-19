# Gate CS-2 — Wolfcam pk3 Load Smoke Test

**Purpose:** Verify `zzz_photorealistic.pk3` is actually loaded by wolfcamql
and overrides at least one baseq3 texture — before we trust it on the full
fragmovie batch.

**Prerequisites:**

- Gate CS-1 passed (`POST /api/packs/build` returned 200)
- `POST /api/packs/install` returned 200 with `alpha_sort_ok=true`
- Know the `baseq3` path your wolfcam install uses (override via env
  `WOLFCAM_BASEQ3_DIR` in the install API, otherwise config default
  `tools/wolfcamql/baseq3`)

## The smoke recipe

### 1. Pick a reference demo

Any `.dm_73` that shows a wall or skin for >3 seconds works. A clean
choice:

```
G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\wolfcam-ql\demos\<any short demo>.dm_73
```

### 2. Record a 5s WITHOUT-pack baseline

Rename (or move) the pk3 out of baseq3 temporarily:

```bash
mv "<wolfcam_baseq3>/zzz_photorealistic.pk3" "<wolfcam_baseq3>/zzz_photorealistic.pk3.OFF"
```

Launch wolfcam with `sv_pure 0` (ENG-3) on the demo:

```bash
wolfcamql.exe +set fs_homepath G:/QUAKE_LEGACY/storage/wolfcam_capture \
  +set sv_pure 0 +demo <demoname>
```

Inside the demo, seek to a moment that shows `textures/base_wall/basewall01b.tga`
(the reference asset — spec §3) and take a screenshot:

```
/screenshot cs2_baseline.tga
```

Screenshot lands under `storage/wolfcam_capture/wolfcam-ql/screenshots/`.

### 3. Record a 5s WITH-pack test

Restore the pk3:

```bash
mv "<wolfcam_baseq3>/zzz_photorealistic.pk3.OFF" "<wolfcam_baseq3>/zzz_photorealistic.pk3"
```

Launch again (same flags), seek to the same moment, screenshot:

```
/screenshot cs2_withpack.tga
```

### 4. Visual diff + console check

**Visual:** open both TGAs side-by-side. The textures must differ — our
photoreal variant has to look clearly different from the vanilla Quake
texture. If they're identical, the pk3 was not loaded (alpha-sort wrong,
or wolfcam picked a different baseq3).

**Console:** check the wolfcam console log for:

```
GOOD:  ... zzz_photorealistic.pk3 (NN files)
BAD:   Couldn't load textures/base_wall/basewall01b.tga
BAD:   WARNING: could not find image ...
```

Any `Couldn't load` or `WARNING: could not find` line for a texture that
IS in our pk3 = Gate CS-2 FAILED.

## Pass / Fail

| Check                                            | Result    |
| ------------------------------------------------ | --------- |
| Screenshots visibly differ                       | pass/fail |
| Console lists `zzz_photorealistic.pk3` on load   | pass/fail |
| No `Couldn't load` for our included textures     | pass/fail |
| No crash / no sv_pure refusal                    | pass/fail |

All four must pass. One fail → Gate CS-2 FAILED, do NOT run the batch
wolfcam re-render on all demos.

## If Gate CS-2 fails

Common causes (in order of likelihood):

1. **`sv_pure 1`** is on — engine ignores non-reference pk3s. Add
   `+set sv_pure 0` to the launch command.
2. **Alpha-sort wrong** — check `/api/packs/install` `baseq3_pk3s` list.
   If `pak00.pk3` sorts AFTER our pack, rename our pack with more `z`s
   (this should already be handled by `zzz_` prefix — if it's not, check
   whether there's a `zzzzz_*.pk3` from another mod that shadows us).
3. **Path casing mismatch** — Linux wolfcam is case-sensitive. Our
   `zip_pk3` preserves casing from `assets.internal_path`; compare against
   what shaders reference. (Windows wolfcam is case-insensitive and won't
   surface this.)
4. **PNG corrupt / TGA conversion mangled alpha** — re-run
   `pytest creative_suite/tests/test_png_to_tga.py` and open a few TGAs
   inside the pk3 in an image viewer.
5. **Asset not in our pack** — check `/api/packs/status` `variant_count`
   and that the specific `internal_path` you expected is an approved
   variant.

Document the failure mode in `Vault/learnings.md` as an L-rule and
capture via the `capture-lesson` skill.
