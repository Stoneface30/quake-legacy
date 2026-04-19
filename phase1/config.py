"""Central configuration for Phase 1 — all paths and constants."""
from pathlib import Path
from typing import Optional, List

# Project root is one level up from phase1/
ROOT = Path(__file__).parent.parent


class Config:
    """All paths and pipeline constants. Uses explicit __init__ — no shared class-level mutables."""

    def __init__(self):
        # ── Binaries ──────────────────────────────────────────
        self.ffmpeg_bin:    Path = ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"
        self.ffprobe_bin:   Path = ROOT / "tools" / "ffmpeg" / "ffprobe.exe"

        # ── Source clips — three-tier structure ───────────────────
        # HARD RULE: ALL clips for a Part come from T1+T2+T3 combined.
        # T1 = top tier (main frags), T2 = second tier, T3 = lower tier.
        # T3 multi-angle subdirs = priority intro/outro candidates.
        # T2 multi-angle subdirs = secondary intro/outro candidates.
        # T1 clips = backbone of every Part.
        self.clips_root:    Path = ROOT / "QUAKE VIDEO"   # parent of T1/T2/T3
        self.tier_roots: dict = {
            1: ROOT / "QUAKE VIDEO" / "T1",
            2: ROOT / "QUAKE VIDEO" / "T2",
            3: ROOT / "QUAKE VIDEO" / "T3",
        }
        self.intro_source:  Path = ROOT / "FRAGMOVIE VIDEOS" / "IntroPart2.mp4"
        # PANTHEON intro: 25.77s, grey/silver logo → in-game CA Tribute billboard.
        # Prepended to EVERY Part automatically. Never skip.

        # ── Clip lists ────────────────────────────────────────
        self.clip_lists_dir: Path = ROOT / "phase1" / "clip_lists"

        # ── Output ────────────────────────────────────────────
        self.output_dir:    Path = ROOT / "output"
        self.preview_dir:   Path = ROOT / "output" / "previews"

        # ── Encoding ──────────────────────────────────────────
        self.target_fps:    int  = 60
        self.target_width:  int  = 1920
        self.target_height: int  = 1080
        self.crf:           int  = 17
        self.preset:        str  = "slow"
        self.audio_bitrate: str  = "320k"

        # ── Final-render encoder (used when --final-quality is set) ───
        # Chosen via encoder-benchmark-2026-04-17.md: x265 CRF 16 veryslow
        # had the highest VMAF of all tested encoders for final-render use.
        # Preview encoder above (libx264 CRF 23 veryfast) is unchanged.
        # File size is not a constraint for final renders — quality is everything.
        self.final_render_codec:  str = "libx265"
        self.final_render_crf:    int = 16
        self.final_render_preset: str = "veryslow"

        # ── NVENC fast-path encoder (used when --nvenc flag is set) ───
        # Benchmarked 2026-04-17 (nvenc-tuning-2026.md) on RTX 5060 Ti:
        #   av1_nvenc p7 CQ18  → VMAF 96.78 / min 95.11 in 20s per 30s clip
        #   (beats x265 CRF 16 veryslow 95.75/93.22 which took 1272s)
        #   hevc_nvenc p7 QP15 → VMAF 96.18 / min 94.31 in 11s (max-compat fallback)
        # Rule P1-J (quality ceiling) + "encoding speed is secondary but ~2-3x realtime
        # is acceptable": AV1 NVENC is the default NVENC codec.
        # Important quirk: NVENC -rc vbr -cq N was observed to cap bitrate regardless
        # of -cq value in this ffmpeg build. Use -rc constqp -qp N for HEVC (reliable).
        # AV1 NVENC's -rc vbr -cq does work correctly.
        # 2026-04-17 research agent update (docs/research/encoder-recommendation-2026-04-17.md):
        # Blackwell NVENC gen-9 supports AV1 UHQ mode (+5% compression at equal quality per
        # NVIDIA) AND 10-bit internal (`-highbitdepth 1 -pix_fmt p010le`) at zero speed cost.
        # UHQ + 10-bit kills the minor banding on bloom/fade sections. Locked as Rule P1-J default.
        self.final_render_nvenc_codec:       str  = "av1_nvenc"   # or "hevc_nvenc" for compat
        self.final_render_nvenc_cq:          int  = 18            # used for av1_nvenc
        self.final_render_nvenc_qp:          int  = 15            # used for hevc_nvenc constqp
        self.final_render_nvenc_preset:      str  = "p7"
        self.final_render_nvenc_tune:        str  = "uhq"         # Blackwell UHQ mode (gen-9 NVENC)
        self.final_render_nvenc_highbitdepth:bool = True          # 10-bit internal, kills bloom banding
        self.final_render_nvenc_pix_fmt:     str  = "p010le"      # 10-bit 4:2:0 output

        # ── Color grade (Tribute series style) ────────────────
        self.grade_contrast:    float = 1.4
        self.grade_saturation:  float = 1.7
        self.grade_brightness:  float = 0.0
        self.bloom_sigma:       int   = 18
        self.bloom_opacity:     float = 0.3   # matches spec

        # ── Transitions ───────────────────────────────────────
        # HARD RULE (Part 4 review, 2026-04-17, docs/reviews/part4-review-2026-04-17.md):
        # Phase 1 ships with NO TRANSITIONS. Every cut is a plain concat join.
        # User verdict: "no fucking transition not even a fading to the next image."
        # Transition palette design deferred to Phase 2 pattern-database work.
        # Supersedes Rule P1-H. TransitionPlanner.plan() returns HARD_CUT unconditionally.
        self.xfade_duration:    float = 0.0   # HARD CUTS ONLY — no cross-fade (legacy)
        self.intro_fade_in:     float = 0.0   # no fade-in from black (title card handles it)
        self.outro_fade_out:    float = 0.0   # no fade-out (outro credits module will handle)
        # Rule P1-H v3 (Part 5 v7 review 2026-04-18): short seam xfades ARE allowed,
        # distinct from the banned "1s fade-to-black". A 0.15s xfade bridges the seam
        # and eats the last 2s tail-trim as transition space (user verdict: "for the
        # clip is to have space for transition"). This is NOT a crossfade between full
        # clips — it's a seam-level bleed of 150ms.
        # Rule P1-H v4 (Part 6 v8 draft review 2026-04-18): bump 0.15 → 0.40.
        # User verdict (fourth time asking): "ive been asking for transition since
        # the first prompt but it was never made". 0.15 s was a subliminal bleed.
        # 0.40 s is a visible transition. Tail-trim (P1-L v3 = 2.5 s) leaves ~2.1 s
        # of clean content + 0.4 s fade = no content loss.
        self.seam_xfade_duration: float = 0.40  # xfade length on every chunk seam

        # ── Intro clip ────────────────────────────────────────
        # IntroPart2.mp4 = 25.77s total. First 5s = PANTHEON logo animation.
        # Rule P1-X (Part 6 v8 draft review 2026-04-18): user verdict "5second only
        # intro sound". Drops 7 → 5; the extra 2 s was dead air past the logo beat.
        # Total pre-content offset: 5 (PANTHEON) + 8 (title card) = 13 s.
        self.intro_clip_duration: float = 5.0  # seconds to use from IntroPart2.mp4

        # ── Audio mix ─────────────────────────────────────────
        # HARD RULE (Part 4 review, 2026-04-17): music -50%, game sound kept.
        # User verdict: "lower music by 50% keep game sound."
        # Net effect: game audio is FOREGROUND, music is atmosphere underneath.
        # Supersedes Rule P1-G (which had game audio under music at 0.85).
        # History: v1 0.30 / v2 0.55 / v3 0.75 / v4 0.85 (music@1.0) / NOW game@1.0 music@0.5.
        self.game_audio_volume:  float = 1.0   # game sound full volume — foreground
        # Rule P1-G v4 (Part 6 v8 draft review 2026-04-18): third complaint in a row.
        # Dropping 0.30 → 0.20 AND adding an objective ebur128 2-channel gate
        # (phase1/audio_levels.py) that BLOCKS render ship if music integrated
        # loudness is < 12 LU below game peak. Subjective mixing is over — numbers
        # decide from here. User: "please use 2 channel and check level".
        # Rule P1-G v5+fix (Part 4 v11 gate honesty pass 2026-04-19): once the
        # measurement bug in extract_music_stem was fixed (was measuring RAW
        # source, not the 0.20-scaled mix), the gate failed honestly at
        # delta=-9 LU. Further audit showed render applies loudnorm I=-18 on
        # game stream — so real mix = game@-18, music@source-14dB. With
        # source music at ~-8.5 LUFS, music_volume must be ≤ 0.08 for music
        # final ≤ -30 LUFS, giving delta ≥ +12 LU. 0.20 → 0.08 path-B fix.
        self.music_volume:       float = 0.08  # music at 8% — gate-compliant (prediction +12.4 LU margin)
        self.music_fadein_s:     float = 2.0   # fade music up over 2 s under PANTHEON
        self.music_fadeout_s:    float = 2.5   # matches outro closeout
        self.music_level_gate_lu: float = 12.0 # music integrated must be ≥12 LU below game peak

        # ── plan_flow_cuts_v2 (event-driven ordering + seam placement) ─────
        # Rule P1-CC v2 + P1-Z v2: event recognition must DRIVE clip order
        # and seam placement, not be a post-render log artifact.
        #   anticipation_ms: cut fires this many ms BEFORE the downbeat so the
        #                    visual peak lands ON the beat (2 frames @ 60 fps).
        #   flow_event_weight_floor: (weight*confidence) floor below which an
        #                    event isn't considered "high-weight" (i.e. clip
        #                    won't compete for a drop slot).
        self.anticipation_ms: int = 33
        self.flow_event_weight_floor: float = 0.55
        # Rule P1-O: music must cover end-of-title-card → start-of-outro continuously.
        # If a single track is shorter than Part runtime, pipeline queues a second
        # track or loops with a beat-matched stitch. Silence gaps are a failure.
        self.music_loop_if_short: bool = True
        self.music_crossfade_on_loop: float = 0.5  # seconds of crossfade when looping/queuing

        # ── Rule P1-R: Three-track music structure (NEW 2026-04-18 review) ──
        # User verdict: "we need multiple audio track for the whole video
        #               we need intro and outro!"
        # Every Part ships with THREE music tracks, crossfaded on beat:
        #   [1] INTRO music — plays under PANTHEON logo + title card
        #       (≈15 s window: 7 s logo + 8 s title card). Atmospheric build.
        #   [2] MAIN  music — the hype/energy track for the body of the Part
        #       (partNN_music.mp3). Covers from title-card-end to outro-start.
        #   [3] OUTRO music — cooldown/closer under the fade-out card
        #       (≈30 s at the tail). Atmospheric, matches intro in tone.
        # Fallback order for intro/outro: per-Part override
        # (partNN_intro_music.* / partNN_outro_music.*) → series-wide
        # (pantheon_intro_music.* / pantheon_outro_music.*).
        # Crossfades between tracks are BEAT-LOCKED (librosa onset snap), not time-locked.
        self.intro_music_crossfade: float = 1.5   # beat-aligned crossfade intro→main
        self.outro_music_crossfade: float = 2.0   # beat-aligned crossfade main→outro
        self.outro_music_duration:  float = 30.0  # seconds of outro track at tail

        # ── Clip-trim convention (Rule P1-L REVISED, Part 4 review 2026-04-17) ──
        # User verdict: "cut the first second and the 2 last second."
        # Every Phase 1 AVI clip has ~2s pre-action + ~3s post-action padding.
        # New trim: 1s off head, 2s off tail. Everything between plays full-length.
        # Rule P1-P (Full-Length Clip Contract): no sub-clip fragments. A clip
        # that enters a Part plays its full post-trim duration. No 0.5s cutaways.
        # Beat-sync can no longer shorten clips — if beat doesn't land on the
        # clip edge, use REPLAY_SPEED_CONTRAST (Rule P1-Q) to stretch with a
        # slow/normal replay of the same clip instead of truncating action.
        self.clip_pad_head: float = 2.0         # original pre-roll length (reference)
        self.clip_pad_tail: float = 3.0         # original post-roll length (reference)
        # Rule P1-L v4 (Part 4 v10 review 2026-04-18): trimming is FL-ONLY.
        # User verdict: "the 1 second before 2 second in the end rule was only
        # for the FL views". FP clips are the frag itself — trimming head/tail
        # was cutting real content. Only FL (free-look) clips show the console/
        # loading overlay that needs cropping; FP is clean start to clean end.
        self.clip_head_trim_fp: float = 0.0     # FP: NO head trim (full frag)
        self.clip_head_trim_fl: float = 1.0     # FL: 1s head (original rule)
        self.clip_head_trim: float = 0.0        # legacy — default to FP (no trim)
        self.clip_tail_trim_fp: float = 0.0     # FP: NO tail trim (full frag)
        self.clip_tail_trim_fl: float = 2.0     # FL: 2s tail (original rule)
        self.clip_tail_trim: float = 0.0        # legacy mirror of FP default
        # Tail-trim no longer carries the xfade budget — xfade overlap is taken
        # from the fade-in of the NEXT clip (xfade naturally consumes half from
        # each side), and we accept the 0.4s visual blend. If this eats real
        # content on FP clips user will escalate; for now, full frags.
        # Rule P1-L v3 short-clip protection floor: if clip_dur - head - tail < this,
        # SKIP the clip from the Part (do not stretch, do not compress, just drop).
        # User verdict: "149-77 is cut we can't see anything ensure we don't cut
        # clips that are already too short".
        self.min_playable_duration_s: float = 2.0
        self.transition_envelope: float = 0.0   # legacy — no envelope

        # ── Rule P1-Z v2 / P1-EE event-localized speed + template conf ─
        # confidence threshold for recognize_game_events() — lower = more
        # matches, higher = pickier. 0.55 default (v2.1 real-clip calibration
        # — demo-vs-clean-pak00 cosine band is 0.45-0.65; the v2 0.72 was
        # clean-on-clean and under-selected on Wolfcam body chunks).
        self.event_confidence: float = 0.55
        # Enables Rule P1-EE event-localized slow (supersedes whole-clip
        # setpts from v10). When False, the legacy whole-clip slow path
        # is used (regression-safe).
        self.event_localized_slow: bool = True
        # Half-width of the event-localized slow window in seconds.
        # Full window is 2 * this. Overridable per-clip via overrides
        # grammar: `slow_window=0.6`.
        self.slow_window_default: float = 0.8
        # Default slow rate when only `slow=True` is set (no explicit rate).
        self.slow_rate_default: float = 0.5
        # Rule P1-AA v2 / P1-CC v2: body-duration-first flow. When True,
        # body duration is computed BEFORE music stitch so the stitcher
        # can right-size the queue (middle tracks full, last truncated at
        # phrase boundary). When False, v10 behavior (music-first) kept.
        self.body_duration_first: bool = True

        # ── Review watermark (Rule P1-D) ──────────────────────
        # User verdict (Part 5 v8 review 2026-04-18): "there are no video/clip
        # name/watermark in the video so i can only tell you. at the moment i
        # can only tell you the time of the final video for the change i want
        # on a specific clip, this will create real bad results."
        # Solution: burn src clip stem in bottom-left of every body chunk so
        # user can reference clips by name during review. Disable for final
        # public renders by flipping review_burn_clip_name = False.
        self.review_burn_clip_name: bool = True
        self.review_watermark_fontsize: int = 22
        self.review_watermark_opacity: float = 0.85   # 0..1 text alpha

        # ── Review / draft mode (fast feedback loop) ──────────
        # User verdict 2026-04-18: "reduce global quality during review as we
        # need quick exchange together so we can finetune everything ...
        # generate the reference one low quality in 5 min i review and we
        # finetune until i say go and you run the big boy that will be updated
        # on youtube".
        # When review_mode is True the pipeline uses draft-speed encoders at
        # every stage (chunks + body xfade + final). Watermark stays ON.
        self.review_mode: bool = False
        # Draft-mode encoding targets (fast, watchable, clearly not final):
        self.review_chunk_crf: int = 28
        self.review_chunk_preset: str = "ultrafast"
        self.review_body_crf: int = 26
        self.review_body_preset: str = "veryfast"
        self.review_final_crf: int = 24
        self.review_final_preset: str = "veryfast"
        # Skip the silencedetect probe (it costs ~0.5-1s per clip × 120 clips
        # = 1-2 min just to analyze). Review iterations should not pay this.
        self.review_skip_silence_detect: bool = True

        # ── Rule P1-Q (short-clip auto-slowmo) ─────────────────
        # User verdict 2026-04-18: "check for t1 auto slowmo when the clip
        # is short". A very-short post-trim T1 (<3s) is a peak-moment blip;
        # slowing it to 0.5× gives the crowd time to register. Applied in
        # normalize_and_expand only to T1-tier entries without prior speed flag.
        self.short_t1_slowmo_threshold: float = 3.0   # post-trim seconds

        # ── Rule P1-Y v2: Per-Part Quake-style hero font ──────
        # User verdict 2026-04-18: "do 4 5 6 using one of each font".
        # Subtitle always Bebas Neue; hero word ("QUAKE TRIBUTE") uses
        # the per-Part display face below.
        self.hero_font_by_part: dict = {
            4: ROOT / "phase1" / "assets" / "fonts" / "BlackOpsOne-Regular.ttf",
            5: ROOT / "phase1" / "assets" / "fonts" / "RussoOne-Regular.ttf",
            6: ROOT / "phase1" / "assets" / "fonts" / "BungeeInline-Regular.ttf",
        }
        self.subtitle_font: Path = ROOT / "phase1" / "assets" / "fonts" / "BebasNeue-Regular.ttf"

        # ── Parts ─────────────────────────────────────────────
        self.parts: List[int] = list(range(4, 13))  # instance attribute, not class-level

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        self.clip_lists_dir.mkdir(parents=True, exist_ok=True)

    def part_dir(self, part: int, tier: int = 1) -> Path:
        """Return the Part directory for a given tier (1=T1, 2=T2, 3=T3)."""
        return self.tier_roots[tier] / f"Part{part}"

    def all_tier_part_dirs(self, part: int) -> list:
        """Return all three tier Part directories that exist."""
        return [d for d in [self.tier_roots[t] / f"Part{part}" for t in (1, 2, 3)] if d.exists()]

    def clip_list_path(self, part: int) -> Path:
        return self.clip_lists_dir / f"part{part:02d}.txt"

    def output_path(self, part: int) -> Path:
        return self.output_dir / f"Part{part}.mp4"

    def preview_path(self, part: int) -> Path:
        return self.preview_dir / f"Part{part}_preview.mp4"

    def normalize_path(self, avi_path: Path) -> Path:
        """CFR-normalized version of an AVI clip."""
        norm_dir = self.output_dir / "normalized"
        norm_dir.mkdir(exist_ok=True)
        return norm_dir / (avi_path.stem + "_cfr60.mp4")

    def music_path(self, part: int) -> Optional[Path]:
        """Auto-detect MAIN music file for this Part. Returns None if not found."""
        music_dir = ROOT / "phase1" / "music"
        for ext in [".mp3", ".ogg", ".wav", ".flac"]:
            candidate = music_dir / f"part{part:02d}_music{ext}"
            if candidate.exists():
                return candidate
        return None

    def intro_music_path(self, part: int) -> Optional[Path]:
        """Rule P1-R: intro music — per-Part override, fallback to pantheon_intro_music."""
        music_dir = ROOT / "phase1" / "music"
        for stem in (f"part{part:02d}_intro_music", "pantheon_intro_music"):
            for ext in (".mp3", ".ogg", ".wav", ".flac"):
                candidate = music_dir / f"{stem}{ext}"
                if candidate.exists():
                    return candidate
        return None

    def outro_music_path(self, part: int) -> Optional[Path]:
        """Rule P1-R: outro music — per-Part override, fallback to pantheon_outro_music."""
        music_dir = ROOT / "phase1" / "music"
        for stem in (f"part{part:02d}_outro_music", "pantheon_outro_music"):
            for ext in (".mp3", ".ogg", ".wav", ".flac"):
                candidate = music_dir / f"{stem}{ext}"
                if candidate.exists():
                    return candidate
        return None
