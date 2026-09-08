# Review defects — carried to Session 2

User review of the AVI series, 2026-08-31. Recorded verbatim in intent, with
whatever measurement I could attach today. None of these were fixed in the AVI
session; that run was scoped to finishing coverage.

---

## 1. Game audio too quiet · ACTIONABLE, PARTIALLY BLOCKED

> "we need to x2 in game volume"

Current mix: `GAME_VOLUME = 1.45`, `MUSIC_VOLUME = 1.24`. Doubling game means
2.90.

**Cannot be applied to the finished Parts.** The mp4 carries ONE aac stream
where game and music are already summed, then passed through `loudnorm` in
dynamic mode — time-varying gain, so the mix cannot be reliably inverted.
Spectral subtraction of the known music is not dependable for the same reason.
Every `body.mov` (video + game audio, before music) was reclaimed after commit.

**Fixed going forward:** `hl_series.preserve_game_stem()` now saves the game
audio as FLAC to `D:\QUAKE_LEGACY_OUTPUT\stems\PartNN_game.flac` before the work
directory is reclaimed. A few tens of MB per Part instead of the ~700 MB
intermediate, lossless.

**Tool:** `remix_audio.py --parts N --game 2.90`. With a stem present this is a
stream-copy of the finished video plus a fresh mix — seconds. Parts rendered
before stem preservation report `NO GAME STEM` and need a re-render.

**Decision needed:** re-render the top 10 at 2.90, or apply it only to V2.

## 2. Audio/video sync drift · CONFIRMED, ROOT CAUSE UNKNOWN

> "sometime game sound is delayed with video ( late sound )"

Measured on finished Parts:

| Part | v start | a start | v duration | a duration | drift |
|---|---:|---:|---:|---:|---:|
| 01 | 0.000 s | 0.000 s | 364.22 s | 364.10 s | −118 ms |
| 20 | 0.000 s | 0.000 s | 283.22 s | 283.00 s | −217 ms |

Container start offset is clean; the streams diverge in LENGTH, audio ending
short. That is consistent with accumulating per-segment error rather than a
fixed offset, and it grows with Part length.

Prime suspects, in order:
1. per-clip audio trim in `render_frag` not matching the video trim exactly
2. the `xfade` video chain and the separate audio concat computing slightly
   different segment boundaries (P1-BB split the graphs precisely because they
   drift when coupled — the split may not be perfectly aligned)
3. slow-mo: `setpts` on video and `atempo` on audio are not guaranteed to
   produce identical durations at arbitrary rates

**Not diagnosed.** Needs a per-segment audit: for each seg, compare its video
and audio durations and accumulate. That is the first thing to do in Session 2,
because hit-to-beat is meaningless if the hit is 200 ms from where the edit
thinks it is.

## 3. Music selection is wrong for the material · CONFIRMED BY DATA

> "you used same musics", "one is a promo only", "some are too horrible ( too
> much bpm )"

**Repeated tracks — diagnosed, and my first guess was wrong.** I assumed
orchestrator restarts were reseeding the claim set and causing repeats within
the run. Measured, that is false: the series used 108 slots and 108 DISTINCT
tracks, and the V1 archive used 134 slots and 134 distinct tracks. Neither run
repeats itself.

The actual fault is between the runs. **All 108 series tracks were already used
in the V1 archive — 100% overlap.** `hl_series` seeds its claimed set from
`committed()`, which reads only `output/_series_manifests`; it never looks at
V1's `output/_hl_manifests`. So every track V1 had already spent looked unused,
and the series re-picked the same 108. Reviewing V1 and the series together,
that is exactly "you used same musics".

Fix: seed the claimed set from BOTH manifest directories (and any future series
directory), and persist it, so track identity is global to the project rather
than per-run.

**Tempo:** measured across the series — BPM min 86, median 123, max 172, and
**48 of 108 tracks (44%) sit at 160 BPM or above**. That is the "too much bpm"
complaint, quantified.

Cause: the beatmatch scorer rewards BAR FIT, and a 172 BPM hardtek track fits a
13.9 s clip almost perfectly (bar_fit 0.954), so it wins on the metric. Bar fit
is a good tie-breaker and a terrible primary criterion — it has no notion of
whether a track is pleasant or suits a fragmovie. The tempo "sanity band" is
90-180 BPM, far too wide, and the library is heavy with hardtek.

**Non-music files:** the library contains promos and spoken-word items. Nothing
filters them. Needs a spoken-word / low-musicality reject (spectral flatness,
speech-band energy, or a simple curated allow-list).

**Recommendation for V2:** curate a shortlist by hand — a few dozen tracks you
actually want in a fragmovie — and let the scorer choose *within* it. Automatic
selection from 1,483 unvetted files was the wrong shape of problem.

## 4. Beat sync barely present · KNOWN LIMITATION, BY DESIGN

> "the beat sync / song match is mostly absent it match nut some delay happen"

The current pipeline snaps CUTS to a beat grid derived from the music. It does
NOT align the frag IMPACT to a beat, because the impact time inside each
hand-cut AVI is not known. That is exactly the gap `hit_anchors` was built to
close: 530 of 1,075 V1 sources (49.3%) now carry a HIGH_AV anchor.

Combined with defect 2, even the cut-level snapping is compromised — a grid is
useless if audio and video disagree by 200 ms.

**Order of work for V2:** fix sync first, then anchors, then beat alignment.
Doing them in any other order produces a confident-looking edit that is wrong.

---

## Priority for Session 2

1. **A/V sync audit** — per-segment, accumulate, find the leak. Blocks everything.
2. **Music curation** — hand-picked shortlist; persist claims across restarts;
   narrow the tempo band; reject non-music.
3. **Game volume 2.90** as the new default, with stems preserved so it stays cheap.
4. **Hit-to-beat** once 1 and 2 are done, using demo-derived exact frag timing
   rather than audio anchors where provenance allows.
