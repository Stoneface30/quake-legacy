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
        self.xfade_duration:    float = 0.0   # HARD CUTS ONLY — no cross-fade
        self.intro_fade_in:     float = 0.0   # no fade-in from black (title card handles it)
        self.outro_fade_out:    float = 0.0   # no fade-out (outro credits module will handle)

        # ── Intro clip ────────────────────────────────────────
        # IntroPart2.mp4 = 25.77s total. First 7s = PANTHEON logo animation only.
        # The rest is in-game CA Tribute billboard scene (not used for Parts).
        self.intro_clip_duration: float = 7.0  # seconds to use from IntroPart2.mp4

        # ── Audio mix ─────────────────────────────────────────
        # HARD RULE (Part 4 review, 2026-04-17): music -50%, game sound kept.
        # User verdict: "lower music by 50% keep game sound."
        # Net effect: game audio is FOREGROUND, music is atmosphere underneath.
        # Supersedes Rule P1-G (which had game audio under music at 0.85).
        # History: v1 0.30 / v2 0.55 / v3 0.75 / v4 0.85 (music@1.0) / NOW game@1.0 music@0.5.
        self.game_audio_volume:  float = 1.0   # game sound full volume — foreground
        self.music_volume:       float = 0.5   # music halved — background atmosphere
        # Rule P1-O: music must cover end-of-title-card → start-of-outro continuously.
        # If a single track is shorter than Part runtime, pipeline queues a second
        # track or loops with a beat-matched stitch. Silence gaps are a failure.
        self.music_loop_if_short: bool = True
        self.music_crossfade_on_loop: float = 0.5  # seconds of crossfade when looping/queuing

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
        self.clip_head_trim: float = 1.0        # strip 1s off head of EVERY clip
        self.clip_tail_trim: float = 2.0        # strip 2s off tail of EVERY clip
        self.transition_envelope: float = 0.0   # no transitions → no envelope

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
        """Auto-detect music file for this Part. Returns None if not found."""
        music_dir = ROOT / "phase1" / "music"
        for ext in [".mp3", ".ogg", ".wav", ".flac"]:
            candidate = music_dir / f"part{part:02d}_music{ext}"
            if candidate.exists():
                return candidate
        return None
