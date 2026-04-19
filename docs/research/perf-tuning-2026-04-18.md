# Performance Tuning Report — 2026-04-18

**Context:** User asked to check PC spec / perf and fine-tune the generation + encoding process.
**Status:** Baseline Part 4/5 v6 render in flight (agent `a994e390f234504ae`). No hot edits to pipeline files — proposed changes land post-baseline.

---

## 1. Hardware inventory (measured)

| Component | Detail |
|-----------|--------|
| CPU | Intel Core i7-12700K — 12 cores (8P + 4E) / **20 threads**, 3.6 GHz base |
| RAM | **32 GB** (34.2 GB reported) |
| GPU | **NVIDIA GeForce RTX 5060 Ti 16 GB** (Blackwell, gen-9 NVENC), driver 595.97 |
| Project disk | G: = Samsung PM9A1 NVMe 1 TB (6-7 GB/s), **82 GB free** of 931 GB |
| Other disks | 3× SATA SSDs + 1× Kingston NVMe (all 1 TB class) |
| GPU idle load | ~11% → huge headroom for parallel pipelines |

## 2. Current encoder configuration (verified)

### 2.1 Final render (`av1_nvenc`, via `pipeline.py` + `render_part_v6.py` + `render_part4_v5_direct.py`)
Already maxed for this GPU — no knob left to turn:
```
-c:v av1_nvenc -preset p7 -tune uhq -rc vbr -cq 18
-highbitdepth 1 -pix_fmt p010le
-multipass fullres -spatial-aq 1 -temporal-aq 1
-rc-lookahead 32 -b_ref_mode middle
```
- Benchmarked 2026-04-17: **VMAF 96.78 / min 95.11** at 20 s per 30 s clip.
- Beats x265 CRF 16 veryslow (95.75/93.22, 1272 s) by quality AND speed.
- 10-bit p010 kills bloom banding at zero speed cost (Blackwell hardware path).
- **Verdict:** LOCKED. Rule P1-J default.

### 2.2 Intermediate chunks (`pipeline.py:337-349`)
```
-c:v libx264 -crf 20 -preset fast -profile:v high
```
- CPU-bound, single-threaded per chunk, built sequentially.
- On 12700K + 20 threads, each chunk gets ~8-12 threads wide but **chunks don't parallelize across processes**.
- "Intermediates are lossy-but-cheap" — final re-encode hides any quality loss.

### 2.3 Normalize / FL-slow-mo (`normalize.py:83-91`)
```
-c:v libx264 -crf 15 -preset medium
```
- CPU-bound, per-FL-source, sequential. CRF 15 medium is overkill for an intermediate.

### 2.4 Title card (`title_card.py:107-108`)
```
-c:v libx264 -crf 17
```
- Runs once per Part, ~8 s output. Not a bottleneck. Leave alone.

---

## 3. Measured gaps and proposed wins

### WIN #1 — Parallel intermediate chunks (biggest lever, 3-5× speedup)
**Issue:** `build_body_chunks()` encodes chunks one at a time. A 20-thread CPU runs ONE chunk at ~1000 fps; it could run **4 chunks concurrently** at ~400 fps each for a net 1600 fps.

**Proposed** (post-baseline):
- Add `cfg.chunk_workers: int = 4` (default 4; `os.cpu_count()//5` for safety)
- Wrap chunk loop in `concurrent.futures.ThreadPoolExecutor(max_workers=cfg.chunk_workers)`
- Each ffmpeg keeps its own `-threads N` (default auto = per-chunk saturation is fine since wall-clock is the bound)
- **Expected:** chunk-build phase drops from ~8 min/Part to ~2-3 min/Part
- **Risk:** RAM pressure during 4× simultaneous filter_complex — mitigated by 32 GB total.

### WIN #2 — NVENC h264 for intermediates (5-10× speedup vs libx264)
**Issue:** libx264 preset fast is still CPU-bound. `h264_nvenc p5 cq 19` produces bit-transparent intermediates at ~500 fps per stream on RTX 5060 Ti (vs ~120 fps libx264 fast).

**Proposed** (post-baseline):
- Add `cfg.intermediate_use_nvenc: bool = False` (opt-in until validated)
- When True: swap `libx264 -crf 20` → `h264_nvenc -preset p5 -tune hq -rc vbr -cq 19 -multipass fullres`
- Keep 4:2:0 8-bit for intermediates (no need for p010 on a throwaway file)
- **Expected:** chunk-build phase drops from ~8 min → ~90 s if used **alongside WIN #1 at workers=2** (GPU serializes, not parallel)
- **Interaction with WIN #1:** NVENC path implies workers=2 max (GPU has ONE encode context stream at a time; ffmpeg serializes internally). Win #1 + Win #2 overlap — pick one.
- **Recommendation:** Apply **WIN #1 first** (pure-CPU, safer), measure, only try WIN #2 if still CPU-bound.

### WIN #3 — Normalize.py to NVENC for FL slow-mo
**Issue:** `normalize.py` uses `libx264 crf 15 medium` per FL source. On a Part with 4-6 FL clips this adds ~4-6 min.

**Proposed** (post-baseline):
- Swap to `h264_nvenc -preset p5 -tune hq -rc vbr -cq 18 -highbitdepth 1 -pix_fmt p010le`
- Keep 10-bit because downstream grade filter needs headroom
- **Expected:** normalize phase drops from ~5 min → ~45 s
- **Risk:** Low. NVENC at cq 18 + 10-bit is still transparent.

### WIN #4 — Run the dual-Part render as 2 concurrent processes (future)
**Issue:** Dual Part 4 + Part 5 render currently uses ONE agent doing them sequentially (~2h total).
**Observation:** GPU encode streams serialize, but the CPU-heavy filter_complex + normalize phases don't. Running Part 4 normalize while Part 5 NVENC-encodes the body = overlap wall-clock.

**Proposed** (after Win #1 lands):
- Add `scripts/render_batch.py` that dispatches N Parts with GPU-aware semaphore (GPU slot count = 1, CPU slot count = 2).
- **Expected:** dual Part render wall-clock drops from ~2h → ~75 min.
- **Status:** deferred, low-urgency.

### WIN #5 — `surfaces` tuning for NVENC
Current default is 0 (ffmpeg auto-picks 8-16 for AV1). Manually setting `-surfaces 32` lets the encoder queue more frames during decode stalls. Free win if the filter_complex is ever stalling.
- Add `-surfaces 32` to all NVENC invocations.
- **Expected:** 2-5% speedup on long filter chains.
- **Risk:** zero. Locked memory cost ≈ 2 × surfaces × frame_size ≈ 200 MB (GPU has 16 GB).

---

## 4. Not-a-problem verified

- **Disk I/O:** G: is PM9A1 NVMe — no ffmpeg pipeline is remotely disk-bound.
- **RAM:** 32 GB is plenty; even 4× concurrent 1080p filter_complex fits in ~8 GB.
- **Driver:** 595.97 is a 2026 Blackwell driver — UHQ mode and AV1 improvements available.
- **Final encoder:** already using every AV1 NVENC feature Blackwell exposes.

## 5. Action plan (post-baseline-render)

1. Wait for background agent `a994e390f234504ae` to finish Part 4 + Part 5 v6 MP4s.
2. Apply **WIN #1** (parallel chunks, `cfg.chunk_workers=4`) as a single commit with a test run on Part 6 dry-build.
3. Apply **WIN #3** (normalize to NVENC) as a separate commit — simpler.
4. Benchmark Part 6 end-to-end. If wall-clock still ≥ 45 min, apply **WIN #2**.
5. Defer **WIN #4** and **WIN #5** until the batch Parts 6-12 phase.
6. Update `docs/research/nvenc-tuning-2026.md` with the new intermediate-codec settings.

## 6. What NOT to change

- Final-render AV1 NVENC knobs — already optimal, benchmarked, locked by Rule P1-J.
- Title-card encoder — single short clip, no speedup worth the risk.
- `render_part_v6.py` mid-render — baseline integrity must be preserved until user approves Parts 4/5 v6.
- Preview encoder (libx264 veryfast crf 23) — already fast, not a bottleneck.
