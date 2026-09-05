# The public export burned player names into the picture

**Found** 2026-09-04. **Fixed** on `fix/public-export-name-burnin`.

## What was wrong

`creative_suite/engine/public_clip_export.py` exists to hand ten-second clips to
THE_PANTHEON for blind voting. Its docstring is explicit:

> WHAT IS NOT BURNED IN. No name, no rank, no score, no director tag...
> IDENTITY TRAVELS AS DATA, NOT AS PIXELS.

The module kept that promise. The engine did not. `_capture_locked` called

```python
wc.capture_demo(safe, [...])          # no profile argument
```

and `capture_demo(profile=None)` does not mean "no profile" — it means
`master_profile.PROFILE_NAME`, the batch profile `TR4SH_GAMEPLAY_MASTER_V2`
(id `091901df0daf`), which deliberately sets:

```
cg_drawFragMessageTokens  "You fragged %v"     # %v = victim's name
cg_drawFragMessageTime    2000
cg_drawFragMessageSeparate 1                    # drawn at X 320 / Y 110 virtual
```

At 1920x1080 that lands the victim's handle centred at y≈247, for two seconds
after every kill the recorder makes.

**It was not the obituary centerprint.** `cg_drawCenterPrint` is already 0 in
every V2 profile. Suppressing it would have changed nothing. The string comes
from `cg_drawFragMessageTokens`, and its gate is a TIME cvar — there is no
`cg_drawFragMessage` boolean to switch off.

A second channel was configured and is closed by the same fix:
`cg_obituaryTokens "%k %i %v"` draws the top-left killfeed with **both** the
killer's and the victim's name, gated by `cg_obituaryTime 2500`.

## Evidence

Same demo, same window (`asylum`, 548575–557075 ms), captured twice, differing
only in profile. Full-frame scan of the name band:

| capture profile | text runs found |
|---|---|
| `TR4SH_GAMEPLAY_MASTER_V2` (what the export used) | 41 frames (geometry, see below) **+ 113 frames** |
| `TR4SH_PUBLIC_EXPORT` (the fix) | 41 frames (geometry) |

113 frames at 60 fps = 1.88 s — `cg_drawFragMessageTime 2000`. Frame grabs in
`docs/visual-record/2026-09-04/` (the victim's handle is redacted there, because
that directory is in the public repo and this document is about not leaking it).

**Clips already exported carry it.** All 12 rows in `exchange/pantheon/` predate
the fix. The 6 with `is_actor_pov: true` — the recorder's own frags, the only
ones where this message draws — show centred burned-in text for 3.4–4.9 s of
their 10 s. Two handles were read straight off the frame. All 12 are
`public_eligible: false` and nothing has been published, but **they should be
recaptured, not shipped.**

## The fix

`TR4SH_PUBLIC_EXPORT` — a profile whose only job is filming for strangers. It
inherits the gameplay master's look and holds every name-bearing cvar at 0.

`TR4SH_GAMEPLAY_MASTER_V2` is deliberately **unchanged**. "You fragged \<name\>"
is an old-school fragmovie beat in the user's own film, where the names are the
point. The defect was one profile filming for the wrong audience, not the cvar
existing. Existing profile ids are byte-identical, so no cached review proxy is
orphaned.

The gate is `public_clip_export.assert_capture_profile_is_nameless()`, which
runs once per batch **before any capture** and refuses if any cvar in
`NAME_BEARING_CVARS` is live. It checks the configuration, not the pixels,
because the failure was a silent default and the regression path is somebody
editing a value in `master_profile`. Both are visible there deterministically.
Each manifest row now records `capture_profile_id`, so a clip's provenance is
answerable later — `overlays_added: []` only ever described what the export drew
on top, and the engine drew the name one layer below it.

## Why the pixel detector is not the gate

`creative_suite/prologue/name_guard.py` audits frames for burned-in text and was
the obvious ship gate. Measured on the two captures above, it reports a
**41-frame run present in both clips that is not text**: a blown-out barred
window in `asylum`, scoring **2903** against the real name's **1991**. Bright
light through dark bars is near-white, colour-neutral and hard-edged — the
entire signature. Adding a shape test (strike out columns whose vertical run is
taller than a glyph: text measured 20 px tall and 7.5 set px per column, the
window 88 px and 34.7) cuts it to 1205 — still twenty times the threshold,
because the bars chop the white into runs exactly a glyph's height.

That is a false alarm, not a leak, so it is not dangerous — but a blocking gate
that rejects clean exports teaches whoever hits it to switch the gate off.
Separating the two needs a calibration set across many maps, not a constant
fitted to one clean sample.

`creative_suite/engine/burned_name_guard.py` keeps the measurement as a
**diagnostic** — used against a control, it is what proved this fix — and is
deliberately not wired into the export path.

**This applies to `prologue/name_guard.py` too**: same heuristic, and its picker
demands a score under 20, which a barred window in frame makes unreachable.
Flagged for that workstream; that file was not modified.
