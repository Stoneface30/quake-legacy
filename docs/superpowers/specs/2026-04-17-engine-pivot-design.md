# Engine Pivot — Design Spec

**Date:** 2026-04-17
**Status:** Draft (companion to `2026-04-17-command-center-design.md`)
**Scope:** Replace wolfcamql as the first-class render engine with a
modern open-source stack (quake3e + q3mme) backed by authoritative
Steam game data, while keeping wolfcamql available for the one thing
only it can do today: play `.dm_73` (Quake Live protocol 73) demos.
**Out of scope:** Sprint 10 (4K master + YouTube mastering) — separate spec.

---

## 1. Why Pivot

Wolfcam's value was: it's the ONLY renderer that plays QL `.dm_73`
demos and we needed to see frags. Its costs are: 2012-era codebase,
no active maintenance, fragmovie-unfriendly API, assumes hard-coded
asset layout, impossible to build modern features into.

Three things changed in 2026:
1. We now have the `dm73parser` (FT-1) that understands the wire
   format completely. We are not dependent on wolfcam to read demos.
2. We have **authoritative game data** on disk via Steam —
   `pak00.pk3` (QL, 962 MB) and `pak0.pk3` + `pak1-8` (Q3A, 496 MB).
   Wolfcam's extracted subset is no longer a ceiling.
3. The Q3 engine source is MIT/GPL — we have `quake3e`, `q3mme`,
   `ioquake3`, `openarena-engine` forks on disk already.

Endgame: q3mme (movie-maker's-edition) is the render engine, wolfcam
becomes reference-only, and eventually we port protocol 73 into
q3mme and wolfcam goes away entirely.

---

## 2. Authoritative Asset Sources (NEW — canonical paths)

Both Steam installs confirmed present 2026-04-17:

| Source | Path | Use |
|---|---|---|
| **Quake Live** | `C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\` | Canonical QL assets. `pak00.pk3` (962 MB) is the 2026-era truth. |
| **Quake 3 Arena** | `C:\Program Files (x86)\Steam\steamapps\common\Quake 3 Arena\baseq3\` | Canonical Q3A assets (1999 id era). `pak0.pk3` 479 MB + expansion paks. |
| Q3 engine source | `G:\QUAKE_LEGACY\tools\quake-source\quake3-source\` | id's original GPL release. |
| q3mme source | `G:\QUAKE_LEGACY\tools\quake-source\q3mme\` | Movie Maker's Edition — our target. |
| quake3e source | `G:\QUAKE_LEGACY\tools\quake-source\quake3e\` | Modern fork. |
| ioquake3 source | `G:\QUAKE_LEGACY\tools\quake-source\ioquake3\` | Foundational fork. |
| wolfcamql source | `G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\` | Reference for protocol 73 patches. |
| UDT source | `G:\QUAKE_LEGACY\tools\quake-source\uberdemotools\` | C++ .dm_73 + .dm_68 parser. |
| our dm73parser | `G:\QUAKE_LEGACY\phase2\dm73parser\` | Full-control parser (FT-1). |

**NEW RULE — Asset Source of Truth:** When extracting ANY baseq3 asset
for the command center's inventory, read from the Steam paks above.
Wolfcam-extracted dumps become reference-only. This kills an entire
class of "which version of this texture is actually in the game" bugs.

---

## 3. The One Blocker — `.dm_73` Playback

Quake Live demos are protocol 73. Every open-source Q3 engine on disk
speaks protocol 66 (vanilla Q3) or 68 (Q3 1.32). Only **wolfcamql**
speaks 73 today.

### Three paths, pick one (need user input):

**Path A — Wolfcam for demos, q3mme for everything else (RECOMMENDED v1)**
- Wolfcam stays as the demo-playback engine for clip re-capture.
- Everything else (map browsing, sprite preview in-engine, pack
  compile tests, any rendering not tied to a `.dm_73` file) runs on
  q3mme against Steam paks.
- Pros: ships this month. Low risk. Reuses 4 years of our wolfcam
  scripts. We get the command-center win immediately.
- Cons: wolfcam still in the critical path. Two engines to keep
  configured.

**Path B — Port protocol 73 into q3mme (RECOMMENDED endgame)**
- Copy wolfcamql's `msg.c` protocol 73 changes + `cg_servercmds.c`
  snapshot delta changes into q3mme. Compile. Test against 3 known
  demos vs UDT golden output.
- Estimate: 2-4 weeks of focused work. Our dm73parser work (FT-1)
  gives us the map of every byte we need to touch.
- Pros: single engine. q3mme's movie-friendly features (smooth
  camera interpolation, clean AVI capture, time-scale commands)
  applied to QL demos — wolfcam can't do half of that.
- Cons: not ready this month.

**Path C — Convert `.dm_73` → `.dm_68`**
- Use dm73parser to re-pack as Q3 protocol 68. Play in any engine.
- Pros: no engine modification.
- Cons: lossy (QL events not in Q3), complex, we don't need it if
  we have Path B as endgame.

### My call: **A now, B as Phase 3.5 research track.**

Path B becomes a research sprint in `phase35/` alongside the 3D intro
work. Meanwhile the command center launches against Path A and ships
the creative-suite value in weeks, not months.

**Blocker for user:** approve A-now / B-eventual or name a different mix.

---

## 4. Engine Roles After Pivot

| Task | v1 Engine | v2 (post-protocol-73 port) |
|---|---|---|
| `.dm_73` demo playback + re-capture | wolfcamql | q3mme |
| `.dm_68` demo playback | q3mme | q3mme |
| Map browsing / walkthrough capture | q3mme (native Q3A Steam paks) | q3mme |
| Pack texture validation (load `zzz_*.pk3`, fly around a map) | q3mme | q3mme |
| Sprite in-engine preview (projectile trails, muzzle flash) | q3mme | q3mme |
| 4K/HuffYUV/MSAA capture (FT-6 quality ceiling) | q3mme | q3mme |
| Reference for protocol 73 patches | wolfcamql source | — |

q3mme is the answer for EVERYTHING except that one row. Which is why
the pivot is worth it even in v1.

---

## 5. pk3 Load Order (critical for style packs)

Quake 3 engines load pk3 files in **alphabetical order**, later
wins. To make our style packs override baseq3 without touching
Valve's files:

```
<steam QL baseq3>\pak00.pk3                    (base, loaded first)
G:\QUAKE_LEGACY\creative_suite\generated\packs\zzz_<slug>.pk3  (override)
```

Engine invocation:
```
q3mme.exe +set fs_basepath "C:\Program Files (x86)\Steam\steamapps\common\Quake Live" \
          +set fs_game baseq3 \
          +set fs_homepath "G:\QUAKE_LEGACY\creative_suite\generated\packs" \
          +set sv_pure 0 \
          +demo <clip.dm_73>
```

`sv_pure 0` required so the engine accepts non-signed pk3s. `zzz_`
prefix guarantees alphabetical override of `pak00.pk3`.

**Per-clip style switching** (Command Center sprint 8) swaps which
`zzz_*.pk3` is in `fs_homepath` between clip captures. Simple rename
or symlink dance, not a full engine relaunch if q3mme has a
`vid_restart` + `fs_restart` it honors (it does — confirmed in source).

---

## 6. Sprint Plan (~20 build-days, 6 sprints, parallelizable with command center)

| # | Sprint | Deliverable |
|---|---|---|
| 1 | Inventory Steam paks | Script extracts full file list from QL pak00 + Q3A pak0-8, generates `FULL_CATALOG.json` supplement |
| 2 | Build q3mme from source | Working `q3mme.exe` on disk, runs against Steam Q3A paks, renders one demo |
| 3 | pk3 load-order test | Build minimal `zzz_test.pk3` with one recolored texture, verify override works |
| 4 | Capture-pipeline port | Move WolfWhisperer.exe's AVI-capture command script to q3mme equivalents (seekclock, video avi, quit) |
| 5 | Engine-abstraction layer | `phase2/engine.py` wraps "play demo, capture clip" behind one interface, dispatches to wolfcam for .dm_73 / q3mme for everything else |
| 6 | Wolfcam replacement in Phase 1 | Clip re-render path in Command Center calls engine abstraction; wolfcam only fires when demo extension is `.dm_73` |

Parallel Phase 3.5 track (research, no timeline):
- Port protocol 73 msg.c patches from wolfcamql → q3mme
- Validate against UDT golden demos
- Publish as a patch set to community (part of FT-4 give-back)

---

## 7. Rules added

- **Rule ENG-1:** Asset source of truth is Steam baseq3 paks. Wolfcam
  extracts are reference only. All new `/api/assets` rows cite
  `source_pk3` with full Steam path.
- **Rule ENG-2:** Style pack pk3s MUST be `zzz_*.pk3` for alphabetical
  override. No exceptions.
- **Rule ENG-3:** `sv_pure 0` required for any pack testing. Documented
  in Command Center render-args builder.
- **Rule ENG-4:** Never modify the Steam pak files. Read-only.

---

## 8. Gates

- **Gate ENG-1:** User approves Path A-now / B-eventual for .dm_73.
- **Gate ENG-2:** After sprint 2, user views one rendered demo via
  q3mme + Steam Q3A paks, confirms quality matches wolfcam.
- **Gate ENG-3:** After sprint 3, user confirms pack override visibly
  changes a texture in q3mme.

---

## 9. Open questions for user

1. **Protocol-73 path**: Approve Path A-now / B-eventual? (my rec yes.)
2. **Wolfcam fully removed or kept as fallback forever?** My rec: kept
   until B lands, then deleted.
3. **q3mme vs quake3e** for v1: q3mme is fragmovie-focused, quake3e is
   more modernized generally. My rec: **q3mme** — its time-scale /
   camera-smoothing features are literally what we're building around.

Non-blocking otherwise. Command Center sprints 1-7 don't need the
engine decision locked.
