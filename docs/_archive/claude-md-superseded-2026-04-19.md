# CLAUDE.md — Superseded P1-* Rule Blocks (archived 2026-04-19)

These rule versions were live in `G:/QUAKE_LEGACY/CLAUDE.md` before the 2026-04-19 curation pass. They were superseded by later revisions and archived here so every historical rule-ID stays grep-able with its full original content.

## Supersedor index

| Archived rule | Superseded by | Live rule location |
|---|---|---|
| P1-G v3 (music 0.30 layered everywhere) | P1-G v5 | `CLAUDE.md` §AUDIO |
| P1-G (legacy — Part 4 2026-04-17 mix) | P1-G v5 | `CLAUDE.md` §AUDIO |
| P1-H (NO TRANSITIONS, Part 4 2026-04-17) | P1-H v4 | `CLAUDE.md` §TRANSITIONS |
| P1-H v3 (0.15s xfade) | P1-H v4 | `CLAUDE.md` §TRANSITIONS |
| P1-L (Clip Trim 1s/2s, Part 4 2026-04-17) | P1-L v4 | `CLAUDE.md` §TRIMMING |
| P1-L v2 (FP/FL differentiated head) | P1-L v4 | `CLAUDE.md` §TRIMMING |
| P1-L v3 (tail 2.5 + protection floor) | P1-L v4 | `CLAUDE.md` §TRIMMING |
| P1-Y (Bebas Neue title card v1) | P1-Y v2 | `CLAUDE.md` §TITLE CARD |
| P1-Z v1 (loudest onset) | P1-Z v2 | `CLAUDE.md` §BEAT SYNC |
| P1-AA v1 (full-track queue + afade xfade) | P1-AA v2 | `CLAUDE.md` §MUSIC STRUCTURE |
| P1-CC v1 (downbeat/phrase/drop strict tier) | P1-CC v2 | `CLAUDE.md` §BEAT SYNC |

---

### Rule P1-G v3: Music at 30%, Layered Over ENTIRE Output (REVISED Part 5 v7 review 2026-04-18)
**Music drops from 0.50 → 0.30 AND layers across PANTHEON + title + body, not body only.**
User verdict: *"music is ONCE AGAIN too loud compared to game sound"* + *"intro sound NEED to be kept"*.
- `cfg.music_volume = 0.30` (was 0.50)
- `cfg.game_audio_volume = 1.00` unchanged
- `final_render()` filter_complex builds a 3-part foreground track (PANTHEON audio + silent title + body game) and amix'es music ACROSS the whole thing. Previously music only played under the body; intro was music-silent.
- PANTHEON audio preserved at full volume; intro music sits under it at 0.30.

---

### Rule P1-H v3: Short Seam Xfades ARE Allowed (REVISED Part 5 v7 review 2026-04-18)
**0.15s xfade between every body chunk. Distinct from the banned 1s dramatic fade.**
User verdict: *"the transition are still non existant"* + *"for the clip is to have space for transition"*.
- `cfg.seam_xfade_duration = 0.15` (was 0.0)
- `assemble_body_with_xfades()` in `render_part_v6.py` builds the body as one mp4 with xfade chain across all chunks (`xfade=transition=fade:duration=0.15` + `acrossfade d=0.15`).
- The 2s tail-trim from Rule P1-L is now officially "transition space".
- Still banned: 1s fade-to-black, dip-to-white, cross-dissolve > 0.3s, any intro/outro dramatic fade.
- Legacy `xfade_duration=0` stays; only `seam_xfade_duration` is active. Supersedes "HARD_CUT unconditionally" in TransitionPlanner.

---

### Rule P1-L v2: FP/FL-Differentiated Head Trim (REVISED Part 5 v7 review 2026-04-18)
**FP clips trim 1s off head; FL clips trim 2s to kill the console/loading view.**
User verdict: *"head is 1 or 2 there are difference in the FL clips as you need to cut the console 2sec in"*.
- `cfg.clip_head_trim_fp = 1.0` (FP — unchanged)
- `cfg.clip_head_trim_fl = 2.0` (FL — new)
- `cfg.clip_tail_trim   = 2.0` (unchanged; reclassified as "transition space" per P1-H v3)
- `build_body_chunks()` detects FL via filename token (`"FL" in src.stem.upper().split("_")`).

---

### Rule P1-L v3 (SUPERSEDED by v4 — kept for history): Tail Trim 2.5 s + Short-Clip Protection Floor (REVISED Part 6 v8 draft review 2026-04-18)
**Tail trim bumps 2.0 → 2.5 s. Clips whose post-trim body would fall below 2.0 s are SKIPPED, not squeezed.**
User verdict: *"09Sec : we can see the console need to cut clip 0.5 shorter in the end"* + *"149-77 is cut we can't see anything review and ensure we don't cut clip that are already too short"*.
- `cfg.clip_tail_trim = 2.5` (was 2.0 — kills console reappearance at clip end).
- `cfg.clip_head_trim_fp` and `clip_head_trim_fl` unchanged (1.0 / 2.0).
- `cfg.min_playable_duration_s = 2.0` — NEW. `build_body_chunks()` computes `clip_dur - head_trim - tail_trim`; if < 2.0 s, log `SKIP_TOO_SHORT` and drop the clip from the Part. No compression, no magic stretching.
- Short-T1 auto-slowmo (from previous session) still applies BEFORE the trim check, giving short T1 frags a legitimate way to stay in the render.

---

### Rule P1-Y: Title Card Font + Kerning Quality Gate (NEW Part 6 v8 draft review 2026-04-18)
**Title card uses Bebas Neue (vendored OFL TTF), growing-substring typewriter with fixed left-anchor x, glow-blend integration with FL backdrop, and a 2 px sine drift to kill the "pasted sticker" look.**
User verdict: *"text Quake Tribute got a space like TRI BUTE and the fonts is horrible... it is also not correcting melting with the clip please lookup how agent do in 2026 and fix"*.
- Font: `phase1/assets/fonts/BebasNeue-Regular.ttf` (Google Fonts OFL build, 61 KB, verified magic `\x00\x01\x00\x00`). Impact is retired — its letter widths vary 0.35–0.75 × fontsize, which broke the v6 per-char x estimator.
- **Typewriter rule:** render with a single `drawtext` per reveal step using `text=QUAKE%{if(gte(t,1.2),\ TRIBUTE,)}` style growing-substring — NEVER per-character concatenation with computed x. The v6 "TRI BUTE" bug was per-prefix centering; the v8 bug was Impact's variable advance widths. Bebas Neue is a monospaced-cap display face that fixes both.
- Fixed left-anchor x: compute `x = (W - final_text_w) / 2` ONCE using the FINAL full string width (ffprobe it from the font), then hold that x constant across all reveal steps. No `x=(w-text_w)/2` per-frame (that was the v6 jitter).
- **Integration with backdrop** (no more black rectangle feel): filter chain is `[backdrop][text]overlay` where `[text]` is `split=2[a][b]; [a]gblur=sigma=18[glow]; [glow][b]blend=all_mode=screen`. Gives the halo ("melting into clip"). Plus `y=H*0.55 + sin(t*2)*3` for a 2 px sine drift so text doesn't look pasted.
- Border stays (`borderw=4:bordercolor=black@0.9`) for legibility on bright FL frames.
- Implementation: `phase1/title_card.py` rewritten in v9; smoke test renders a 2-frame grab (t=0.3 and t=2.5) into `docs/visual-record/YYYY-MM-DD/title_card_smoke_partNN.png` per Rule VIS-1.

---

### Rule P1-Z v1 (SUPERSEDED — kept for history): Beat-Sync Runs on GAME Audio Onsets, Not Seam Timing
**Alignment target = each clip's LOUDEST action transient (rocket hit, rail crack, LG kill pop) lands on the nearest music downbeat. The seam between clips is *derived* from this, not the other way around.**
User verdict: *"please review how beat making work with the AUDIO of the game clip and match with this, DO NOT base on the clip length or video ... when you watch the video there is no beat at all attached to the action rhythm"*.
- `phase1/audio_onsets.py` (new): `find_action_peaks_per_clip()` — librosa onset detection on game audio with `backtrack=True`, pre-emphasis HPF (kills LG hum), `pre/post_max=20`, `delta=0.3`, `wait=30`, peak = loudest onset not first. Accuracy ~5 ms at hop=256.
- `phase1/beat_sync.py` rewrite: input = (clips with peaks, music downbeat grid), output = per-seam trim adjustments so each clip's action_peak lands on nearest music downbeat.
- **Shift absorbed by trims**, never by speed changes: `head_trim[i] += min(shift, 0.4)` or `tail_trim[i-1] += min(-shift, 0.4)`, bounded by `min_playable_duration_s = 2.0` (P1-L v3).
- Max shift: ±400 ms. Beyond that → tag `WEAK_ALIGN` in `output/partNN_beats.json` and use nearest half-beat instead.
- Logs `partNN_beats.json`: `[{clip, action_peak, target_downbeat, shift, tag: TIGHT|WEAK_ALIGN|SKIP_ALIGN}]`.
- Research source: `docs/research/audio-montage-2026-04-18.md` §B, §C.

---

### Rule P1-AA v1 (SUPERSEDED — kept for history): Full-Track Music Queue + Explicit-afade Crossfades
**Every music seam is a beat-matched long crossfade (4–6 s), computed per track pair with explicit `afade` filters. `acrossfade` chains are BANNED — they compound drift.**
User verdict: *"why you use 15sec of a full song and swap to another with no fade no transition no mix in and no mix out this is bad ... Also regarding the music it looks like the song are cutting shortly we could save some usage same issue as intro"*.
- `phase1/music_stitcher.py` rewrite: queue N full tracks whose combined duration ≥ body + fade budget. Each track plays to its natural end minus 6 s; next track enters on its first downbeat at the 6 s mark. 4–6 s crossfade exposes both tracks' downbeats simultaneously.
- Filter graph per pair (from §E of research brief):
  ```
  [A]afade=t=out:st={fadeout_start}:d={xfade}[Afaded];
  [B]atrim=start={B_first_downbeat},asetpts=PTS-STARTPTS,
     afade=t=in:st=0:d={xfade},adelay={fadeout_ms}|{fadeout_ms}[Bfaded];
  [Afaded][Bfaded]amix=inputs=2:duration=longest
  ```
- `music_plan.json` (ship gate): every entry must have `duration == track.full_duration ± 0.1 s`. Truncated tails = hard fail.
- **Sidechain ducking** on top: music stream ducks ~6 dB under every game transient via `sidechaincompress=threshold=0.05:ratio=8:attack=5:release=250`. See `phase1/sidechain.py` (new).
- Pool naming: `phase1/music/partNN_main_{1,2,…}.mp3` for multi-main, intro/outro unchanged.
- Research source: `docs/research/audio-montage-2026-04-18.md` §D, §E.

---

### Rule P1-CC v1 (SUPERSEDED — kept for history): Downbeat + Phrase + Drop-Aware Cut Placement
**Beat-sync consumes structural music analysis, not raw beat grid. T1 frags pin to drops, T2 to strong downbeats, T3 fillers to medium. Cuts are anticipation-offset −33 ms (2 frames @ 60 fps) so the visual peak lands ON the beat, not the cut.**
User verdict: *"also review beatmaker and update knowledge for best results"*.
- `phase1/music_structure.py` (new): runs Beat This! (ISMIR 2024 SOTA, `pip install beat_this`) on the stitched music WAV to get beats + downbeats; madmom DBN as CPU fallback. Plus `msaf` for phrase segmentation (intro/build/drop/break/outro), custom sub-200 Hz RMS novelty for drop detection, per-downbeat salience ranking `max(onset_env[±50ms]) × (0.5 + 0.5 × kick_energy)`.
- Output artifact: `output/partNN_music_structure.json` with `bpm_global`, `beat_grid`, `downbeats[].salience`, `sections[]`, `drops[].strength`, `cut_candidates.{strong,medium,soft}`.
- `phase1/beat_sync.py` consumer rewrite: tier → candidate pool mapping:
  - **T1 frags** pin to `drops[]` (salience ≥ 0.80 or explicit drop), one per drop max.
  - **T2 frags** to `cut_candidates.strong` (salience ≥ 0.55).
  - **T3 fillers** to `cut_candidates.medium` (salience ≥ 0.30).
- **Anticipation cut** at seam-render time: `seam_cut_time = target_downbeat - 0.033` (60 fps). Logged per seam as `offset_ms: -33` in `partNN_beats.json`.
- **Ghost downbeats** (sidechain duck moments on game explosions) use hit-on-beat (0 offset) — already visually sync'd by the duck itself.
- Visual record: `docs/visual-record/YYYY-MM-DD/partNN_music_structure.png` = waveform + beat grid + downbeats + drops overlay.
- Research source: `docs/research/beatmaker-2026-04-18.md` §B–§F.

---

### Rule P1-G (legacy — superseded by P1-G v4): Audio Mix — Game Foreground, Music Halved (REVISED Part 4 review 2026-04-17)
**Kept for history. See P1-G v3 above.**
- `game_audio_volume = 1.0` (full — grenade hits, rail cracks, rocket impacts)
- `music_volume      = 0.5` (halved — sits behind game audio)
- User verdict: *"lower music by 50% keep game sound"*
- History: v1 30% / v2 55% / v3 75% / v4 85% (all game-under-music) → v5 music halved, game full
- `assemble_part()` must always use `amix` when music present — never discard game audio
- See `docs/reviews/part4-review-2026-04-17.md` §1

---

### Rule P1-L: Clip Trim — 1s Head / 2s Tail, Full-Length Between (REVISED Part 4 review 2026-04-17)
**User verdict:** *"we can just cut the first second and the 2 last second for the transition effects."*
- `clip_head_trim = 1.0s` (was 2.0s envelope)
- `clip_tail_trim = 2.0s` (was 1.5s + 1.0s envelope)
- `transition_envelope = 0.0s` (no transitions means no envelope)
- Beat-sync may NO LONGER truncate clips. If beat doesn't land, use Rule P1-Q
  (REPLAY_SPEED_CONTRAST) to stretch via slow/normal replay instead of cutting.

---

### Rule P1-H: NO TRANSITIONS (REVISED Part 4 review 2026-04-17)
**All inter-clip joins are hard cuts in Phase 1.** User verdict: *"no fucking transition
not even a fading to the next image or anything."*
- `xfade_duration = 0.0`
- `TransitionPlanner.plan()` returns HARD_CUT unconditionally (all other kinds dead code)
- No section fades, white flash, dip-to-black, cross-dissolve
- Transition palette design is DEFERRED to Phase 2 pattern-database work
