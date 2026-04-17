# Encoder Recommendation — 2026-04-17

**Recommendation: `av1_nvenc -preset p7 -tune uhq -rc vbr -cq 18 -b:v 0` with full Blackwell UHQ flag stack (multipass fullres, AQ, lookahead 32, b_ref middle, bf 4, tf_level 4, highbitdepth 1, 10-bit output).**

This is the current config plus two Blackwell-specific refinements (`-tune uhq`, `-highbitdepth 1 -pix_fmt p010le`). The benchmark winner hasn't changed — it was already right — but the RTX 5060 Ti's ninth-gen NVENC supports AV1 UHQ mode which NVIDIA claims gives +5% compression at equal quality, and 10-bit internal processing costs nothing on Blackwell while noticeably reducing banding on bloom/fade grades. Stay on the current codec, enable the two flags.

---

## Why

- **The benchmark already picked this codec and it beat every alternative.** `av1_nvenc p7 CQ18` scored VMAF **96.78 mean / 95.11 min** on our 30s fragmovie reference — highest of every encoder tested, including x265 CRF16 veryslow (95.75/93.22) at 60× the speed. See `docs/research/encoder-benchmark-2026-04-17.md` §"Winner — Updated 2026-04-17". Nothing in the 2026 research contradicts this; NVIDIA's own Blackwell numbers confirm AV1 UHQ is now within ~3× of SVT-AV1 software quality, and we don't even have SVT-AV1 compiled in our ffmpeg build.
- **High-motion fragmovie content is AV1's strongest suit.** Rocket/LG/rail bitrate spikes are exactly what AV1's directional intra prediction and larger block sizes were designed for. The min-VMAF 95.11 (worst frame in the 30s reference — almost certainly a rocket impact) is higher than x265 veryslow's min (93.22). HEVC NVENC at QP15 also beats x265 here (94.31 min) but trails AV1.
- **HUD/frag-text chromatic artifacting is a CRF/QP problem, not a codec problem.** The known failure mode (x264/x265 CRF ≥18 on thin-edged text) shows up at lower bitrates. At ~50 Mbps / CQ18, AV1 NVENC delivers SSIM 0.9994 — effectively transparent to text edges. The 10-bit output (`-pix_fmt p010le`) further suppresses any chroma ringing around the HUD's cyan/green accents.
- **YouTube transcode-friendliness favours AV1 upload.** Per 2026 YouTube guidance, they transcode everything — but uploading an AV1 master minimizes format-conversion generation loss when the video eventually rides the VP9/AV1 playback ladder. H.264 upload would re-encode 1:1 to H.264 playback for low view counts, but any content crossing into the AV1 playback tier takes a second AV1 hop from an H.264 source = more artifacts. AV1 → AV1 is cleaner than H.264 → AV1.
- **Encode speed is already fine.** 1.5× realtime on 30s clip = a full 2-minute Part renders in ~80 seconds. Parts 4-12 × ~2 min = ~18 min total final-pass encode time. x265 CRF15 slow would be 4-5 hours per Part; x265 CRF17 slow would still be ~1 hour per Part. Not worth it.

---

## Rejected alternatives

| Candidate | Why not |
|---|---|
| x264 CRF15 preset slow | Beaten on both mean and min VMAF by av1_nvenc, larger files at lower quality, 50× slower. H.264 has no headroom left on Blackwell NVENC era. |
| x265 CRF17 preset slow | VMAF 94.88 / 90.81 in the benchmark — below av1_nvenc by ~2 points. ~1 hour per Part for no visible gain. |
| x265 CRF16 veryslow (old winner) | Superseded. VMAF 95.75/93.22, takes ~4-5 hours per Part, loses to av1_nvenc on both mean AND min. Keep only as the CPU-only Phase-4 fallback. |
| hevc_nvenc QP15 constqp | Runner-up at VMAF 96.18 / 94.31 — solid backup if a player chokes on AV1, but YouTube and all modern browsers/VLC handle AV1 fine in 2026. 0.6 VMAF mean / 0.8 min below av1. |
| h264_nvenc CQ17 tuned | VMAF 96.43 / 93.82 — decent but 1.3 min below AV1 and H.264 upload gives up the AV1-to-AV1 transcode advantage. |
| SVT-AV1 preset 4 CRF 23 | Not compiled into our ffmpeg build and encode time would be measured in hours per Part (CPU-only). NVIDIA's Blackwell AV1 UHQ is within ~3× quality of SVT-AV1 preset 4 per NVIDIA's own benchmarks — not worth rebuilding ffmpeg. |
| libaom-av1 | Disqualified on encode time in the April benchmark — 6-10 hours per Part projected. Dead. |
| AV1 with film-grain synthesis | Fragmovies are clean, low-noise content (id tech 3 flat shading + our grade). Grain synthesis has nothing to work with. Skip. |

---

## Exact `Config.final_render_*` values (paste into `phase1/config.py`)

Replace the existing NVENC block around lines 57–71:

```python
# ── NVENC fast-path encoder (used when --nvenc flag is set) ───
# Final recommendation per encoder-recommendation-2026-04-17.md:
#   av1_nvenc p7 CQ18 with Blackwell UHQ tuning.
# Benchmark (30s 1080p60 fragmovie clip, RTX 5060 Ti):
#   av1_nvenc p7 CQ18             → VMAF 96.78 / min 95.11, 1.5× realtime  ← WINNER
#   hevc_nvenc p7 QP15 constqp    → VMAF 96.18 / min 94.31, 2.7× realtime  (backup)
#   x265 CRF16 veryslow (CPU)     → VMAF 95.75 / min 93.22, 0.024× realtime (archival)
# Blackwell additions vs April baseline:
#   -tune uhq         → AV1 Ultra-High-Quality mode (RTX 50 / SDK 13.0 only)
#   -highbitdepth 1   → 10-bit internal processing, suppresses bloom/fade banding
#   -pix_fmt p010le   → 10-bit 4:2:0 output (YouTube-compatible, better grade retention)
# HEVC-NVENC VBR-CQ is broken in this ffmpeg build — use -rc constqp -qp N if falling back.
self.final_render_nvenc_codec:   str = "av1_nvenc"   # primary
self.final_render_nvenc_cq:      int = 18            # AV1 CQ target
self.final_render_nvenc_qp:      int = 15            # HEVC fallback QP (constqp only)
self.final_render_nvenc_preset:  str = "p7"          # slowest = best quality
self.final_render_nvenc_tune:    str = "uhq"         # Blackwell UHQ — keep "hq" on Ada/older
self.final_render_nvenc_bf:      int = 4             # B-frames (5 if tune=uhq and HEVC)
self.final_render_nvenc_lookahead: int = 32          # rc-lookahead frames
self.final_render_nvenc_multipass: str = "fullres"   # two full-res analysis passes
self.final_render_nvenc_b_ref_mode: str = "middle"   # key quality lever on Blackwell
self.final_render_nvenc_spatial_aq: int = 1
self.final_render_nvenc_temporal_aq: int = 1
self.final_render_nvenc_aq_strength: int = 8
self.final_render_nvenc_tf_level: int = 4            # Blackwell temporal filter
self.final_render_nvenc_highbitdepth: int = 1        # 10-bit internal
self.final_render_nvenc_pix_fmt: str = "p010le"      # 10-bit 4:2:0 output
self.final_render_nvenc_gop:     int = 120           # 2s GOP at 60fps (YouTube-safe)
self.final_render_nvenc_surfaces: int = 48           # encoder throughput
self.final_render_nvenc_split_encode_mode: str = "auto"  # Blackwell split-frame

# CPU archival fallback (Phase-4 public CLI / no-GPU machines) — unchanged
self.final_render_codec:  str = "libx265"
self.final_render_crf:    int = 16
self.final_render_preset: str = "veryslow"
```

The full ffmpeg invocation `phase1/pipeline.py:assemble_part()` should emit (codec=`av1_nvenc`):

```bash
-c:v av1_nvenc -preset p7 -tune uhq -rc vbr -cq 18 -b:v 0 \
  -multipass fullres -spatial-aq 1 -temporal-aq 1 -aq-strength 8 \
  -rc-lookahead 32 -b_ref_mode middle -bf 4 -tf_level 4 \
  -highbitdepth 1 -pix_fmt p010le \
  -g 120 -surfaces 48 -split_encode_mode auto \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 384k -ar 48000 -movflags +faststart
```

Audio upgrade: bump AAC from 320k to **384k** to match YouTube's upload recommendation (they accept up to 384k AAC-LC stereo; cost is 16 KB/sec = negligible in a quality-first pipeline).

---

## Upload pipeline note

**Ship a single 1440p60 master to YouTube per Part.** Two-master archive (4K upload + 1080p archive) is not worth the encode time.

Reasoning:

- **Source is 1080p60.** WolfcamQL captures at `r_customwidth 1920 r_customheight 1080` in the current phase-1 AVI pipeline (grep of `phase1/config.py`: `target_width 1920, target_height 1080, target_fps 60`). Rendering natively at 4K requires the FT-3 engine-rerender track (4K WolfcamQL re-capture via HuffYUV + 8× MSAA) which is not on the Parts 4-12 critical path.
- **1440p60 is the sweet spot upscale target.** Per `engine-rerender-youtube-maxquality-2026-04-17.md` §"The 4K upload trick": 1440p gets ~12–16 Mbps VP9 playback vs 5–8 Mbps for native 1080p — the ~2× bitrate uplift is the main win. 2160p gets 18–25 Mbps but the 1.33× upscale from 1080p to 1440p Lanczos is cleaner than the 2× jump to 2160p (edge halos around HUD text and rail trails become visible at 2160p from 1080p source). At 2× the lanczos filter starts ringing; at 1.33× it doesn't.
- **The master IS the archive.** Because the pipeline's final render is already at CQ18 AV1 (~50 Mbps, VMAF 96.78), the 1440p upscaled master is simultaneously:
  - the YouTube upload, and
  - the archival copy.

  Keeping a separate "1080p archive" adds disk cost (~4 GB/Part × 12 Parts = 48 GB) for zero recovery value — you can always re-derive 1080p from the 1440p master losslessly via downscale, and the source AVIs are already kept on disk.
- **Upscale in a separate pass**, not chained in the final render filtergraph. The final assembly produces `partNN_final.mp4` at 1080p60 AV1. A second pass upscales to 1440p AV1 for upload:

  ```bash
  ffmpeg -i partNN_final.mp4 \
    -vf "scale=2560:1440:flags=lanczos" \
    -c:v av1_nvenc -preset p7 -tune uhq -rc vbr -cq 18 -b:v 0 \
    -multipass fullres -spatial-aq 1 -temporal-aq 1 -rc-lookahead 32 \
    -b_ref_mode middle -bf 4 -tf_level 4 -highbitdepth 1 -pix_fmt p010le \
    -c:a copy -movflags +faststart partNN_youtube_1440p60.mp4
  ```

  Cost: ~90 seconds extra on RTX 5060 Ti. Quality: clean Lanczos 1.33× + AV1 CQ18 re-encode = imperceptible quality loss vs the 1080p master.
- **Do NOT transcode to H.264 for upload.** YouTube accepts AV1 uploads directly in 2026. H.264 would give up the AV1-to-AV1 transcode generation-loss advantage for no reason (no meaningful compatibility benefit — YouTube isn't a decoder compatibility issue).
- **If AV1 upload ever throws an ingestion error** (historically rare but reported in 2024-2025 for non-standard AV1 flavors), fall back to **HEVC `hevc_nvenc -preset p7 -tune uhq -rc constqp -qp 17`** for the 1440p upload pass. Don't fall back to H.264 — YouTube specifically accepts HEVC for "higher quality" source material.

**Summary of what ships per Part:**

1. `partNN_final.mp4` — 1080p60 AV1 CQ18, the canonical master. Keep forever.
2. `partNN_youtube_1440p60.mp4` — 1440p60 AV1 CQ18, upload to YouTube. Can delete after upload succeeds.

No 4K master, no H.264 fallback, no 1080p archive copy.

---

## Sources (2026-04-17 research pass)

- [NVIDIA Video Codec SDK 13.0 — Blackwell AV1 UHQ mode](https://developer.nvidia.com/video-codec-sdk)
- [RTX 50 Series: 4:2:2, MV-HEVC, AV1 Ultra Quality (GameGPU)](https://en.gamegpu.com/iron/nvidia-geforce-rtx-50-support-4-2-2-mv-hevc-i-av1-ultra-quality) — confirms AV1 UHQ +5% compression at equal quality on Blackwell
- [Puget Systems — RTX 50-series for content creators (Jan 2025)](https://www.pugetsystems.com/blog/2025/01/21/nvidia-geforce-rtx-50-series-features-for-content-creators/)
- [Streaming Learning Center — Which codecs does YouTube use?](https://streaminglearningcenter.com/codecs/which-codecs-does-youtube-use.html) — YouTube AV1 transcode trigger is view count, not upload codec
- [Stream Guides — YouTube upload quality investigation](https://streamguides.gg/2024/03/youtube-upload-quality-investigation-does-source-codec-matter/)
- [Codec Wiki — SVT-AV1 preset deep dive](https://wiki.x266.mov/blog/svt-av1-fourth-deep-dive-p1) — confirms preset 4-6 is the 2025-2026 quality target; also confirms SVT-AV1 is CPU-bound hours-per-Part range
- Prior in-project research:
  - `docs/research/encoder-benchmark-2026-04-17.md` — base benchmark with av1_nvenc winner
  - `docs/research/nvenc-tuning-2026.md` — Blackwell flag stack derivation
  - `docs/research/engine-rerender-youtube-maxquality-2026-04-17.md` — YouTube upload bitrate ladder & 4K upscale trick
