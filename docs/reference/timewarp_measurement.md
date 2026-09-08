# Timewarp / A-V drift measurement (2026-09-01)

Directive §7-10. Measured, not assumed. Fixed 2000 ms demo span
(380575→382575) on `CA-<player>-overkill-2013_01_08-21_42_32.dm_73`,
captured at four timescales, then repeated to test reproducibility.

Audio duration is computed as `nb_frames / sample_rate` — ffprobe does
**not** populate `duration` on this PCM stream, and a first measurement
pass that trusted `duration` reported `audio_s = 0.0` everywhere. That
would have been an easy false "no audio / infinite drift" conclusion;
the streams are really `mjpeg` + `pcm_s16le 22050 Hz stereo`.

## Results

| timescale | expected video | video | audio | video err | A/V drift |
|---|---|---|---|---|---|
| 1.00 | 2.000 s | 2.000 s | 2.133 s | 0.0 ms | −133.3 ms |
| 0.75 | 2.667 s | 2.650 s | 2.658 s | −16.7 ms | −8.3 ms |
| 0.50 | 4.000 s | 3.983 s | 3.971 s | −16.7 ms | +12.5 ms |
| 0.35 | 5.714 s | 5.683 s | 5.675 s | −31.0 ms | +8.4 ms |

Reproducibility (same params, repeated runs):

| timescale | run | video | audio | frames | A/V drift |
|---|---|---|---|---|---|
| 1.00 | r1 | 1.983 s | 1.994 s | 119 | −10.4 ms |
| 1.00 | r2 | 1.983 s | 1.996 s | 119 | −12.5 ms |
| 0.50 | r1 | 3.983 s | 4.133 s | 239 | −150.0 ms |
| 0.50 | r2 | 3.967 s | 3.971 s | 238 | −4.1 ms |

## Findings

**1. The predicted linear desync does not exist.** Prior source research
(`q3mme_cinematic_audit.md`) predicted that video sim-step scales with
`com_timescale` while the audio sample budget does not, so "at timescale
0.5 audio runs 2× fast against picture, drifting linearly". Measurement
disproves this for our capture path: at 0.5× the audio is **3.97 s**, not
2.0 s — it stretches with the video. Slow-motion audio is pitch-shifted
and time-stretched together with picture, exactly as a fragmovie wants.
The source reading was of a code path that evidently is not the one the
AVI writer uses.

**2. Video is frame-exact.** Frame counts are exactly
`round(demo_span / timescale × 60)`: 119/120, 159, 239, 341 for 1.0 /
0.75 / 0.5 / 0.35. Video error against the ideal never exceeds 31 ms
(≈2 frames at 60 fps), and most of that is capture-boundary quantization.

**3. The real defect is a non-deterministic audio TAIL, and it is not
timescale-related.** Drift across all seven runs ranges −150.0 ms to
+12.5 ms with no correlation to timescale — 1.0× produced both −133.3 ms
and −10.4 ms; 0.5× produced both −150.0 ms and −4.1 ms. It is always
audio being *longer* (or equal), never progressively diverging inside a
clip, which is the signature of a trailing buffer flush at `stopvideo`
that sometimes catches one extra chunk (the 0.5× pair differ by 3584
samples = 162 ms). Video also varies by ±1 frame at the boundary.

## Chosen strategy: (A) native timescale, with a mandatory trim contract

Native timescale is **accepted** for slow motion — option A of the
directive's four. It gives frame-exact, correctly-stretched video and
audio with no retiming machinery, and options B/C/D would add real
complexity to solve a problem that measurement shows does not exist.

But native timescale is accepted **only together with this rule**:

> Capture boundaries carry ±1 frame of video and up to ~150 ms of
> non-deterministic trailing audio. A captured clip's raw length is
> therefore NOT authoritative. Every clip must be trimmed at assembly to
> the exact duration derived from the SceneRecipe TimeMap
> (`edit_end_us − edit_start_us`), with a capture guard margin on both
> ends so the trim never runs past real content.

This keeps the canonical chain intact per §8 — `demo_us → TimeMap →
edit_us` stays authoritative, and runtime timescale remains purely an
execution method whose sloppy edges are corrected deterministically in
post rather than trusted.

**Not rejected, just unnecessary here:** high-FPS capture + deterministic
retiming (option B) remains the better answer if we ever want a slow-mo
rate that native timescale renders poorly (e.g. extreme <0.2× where
60 fps source frames would be visibly duplicated). Nothing in this
measurement rules it out; it simply is not needed for the 0.35–1.0 range
this project's effect presets actually use.

## Cost

Wall-clock per 2 s capture: 24 s at 1.0×, 60 s at 0.75×, 82 s at 0.5×,
110 s at 0.35× — cost scales with output frame count, roughly 0.3 s of
wall time per output frame. Relevant for the performance budget: slow
motion is the single most expensive knob in a preview loop.
