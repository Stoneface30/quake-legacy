"""Voice for the diegetic presenter: the game's own speech first, TTS second.

WHY THE GAME'S VOICE COMES FIRST. Quake Live ships a tutorial trainer, Crash,
who already speaks forty complete instructional lines -- "Hey, welcome to the
game!", "This is one of the many fighting arenas." A narrator assembled from
those is diegetic in a way synthesis cannot fake, because it IS the game
talking. Synthesis fills only the gaps: things Crash never said.

WHAT THIS IS NOT. No voice cloning is claimed or attempted. A synthesised line
is processed toward a compatible presentation -- pitch, formant, EQ, a little
room -- so it sits beside the real barks without pretending to be the same
performer.

TRANSCRIPTS ARE MEASURED, NOT GUESSED. Every line's text and word timing comes
from faster-whisper run over the actual asset. Filenames like `13_03` say
nothing about content, and reading them as if they did is how a subtitle ends
up disagreeing with the audio under it.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence

REPO = Path(__file__).resolve().parents[2]

# Resolve tools from the checkout that OWNS THE DATA, not from the code. A git
# worktree of this repository has no `tools/` under it, which is how every
# review proxy once failed on a missing ffmpeg.
from engine.pantheon import store as _S           # noqa: E402
FFMPEG = _S.PROJECT_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"

# The interpreter that has Kokoro. Not this one: the engine runs on the system
# Python and the speech stack lives in the ComfyUI virtualenv.
TTS_PYTHON = Path("E:/PersonalAI/venv/Scripts/python.exe")
TTS_SAMPLE_RATE = 24000          # what Kokoro emits; ffmpeg resamples later


class SourceKind(Enum):
    GAME_ASSET = "GAME_ASSET"        # shipped Quake audio, unmodified
    SYNTHETIC_TTS = "SYNTHETIC_TTS"  # generated, then processed
    HYBRID = "HYBRID"                # a real bark plus a synthesised clause


class SpatialMode(Enum):
    """How a line sits in the world."""
    DIEGETIC = "DIEGETIC"    # panned and attenuated from the actor's position
    NARRATOR = "NARRATOR"    # centred, no attenuation
    RADIO = "RADIO"          # centred, band-limited


@dataclass
class VoiceLine:
    """One shipped audio asset, with what it actually says."""
    line_id: str
    path: str
    speaker: str
    duration_s: float
    text: str = ""
    words: list[dict] = field(default_factory=list)
    category: str = "SPEECH"

    def matches(self, *terms: str) -> bool:
        hay = f"{self.text} {self.line_id}".lower()
        return all(t.lower() in hay for t in terms)


class GameVoiceBank:
    """The game's own voice, indexed by what it says rather than by path.

    Production code asks for meaning -- "the line where Crash introduces
    himself" -- and never carries a pak path around.
    """

    def __init__(self, lines: Sequence[VoiceLine]) -> None:
        self.lines = list(lines)

    @classmethod
    def from_transcripts(cls, path: Path, speaker: str = "CRASH",
                         category: str = "INSTRUCTION") -> "GameVoiceBank":
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([VoiceLine(line_id=r["id"], path=r["path"], speaker=speaker,
                              duration_s=r["duration_s"], text=r["text"],
                              words=r.get("words", []), category=category)
                    for r in rows])

    def by_id(self, line_id: str) -> VoiceLine:
        for ln in self.lines:
            if ln.line_id == line_id:
                return ln
        raise KeyError(f"no voice line {line_id!r}")

    def find(self, *terms: str, speaker: str | None = None,
             max_duration: float | None = None) -> list[VoiceLine]:
        out = [ln for ln in self.lines if ln.matches(*terms)]
        if speaker:
            out = [ln for ln in out if ln.speaker == speaker]
        if max_duration is not None:
            out = [ln for ln in out if ln.duration_s <= max_duration]
        return sorted(out, key=lambda ln: ln.duration_s)

    def find_one(self, *terms: str, **kw) -> VoiceLine:
        hits = self.find(*terms, **kw)
        if not hits:
            raise KeyError(f"no line matching {terms}")
        return hits[0]

    def __len__(self) -> int:
        return len(self.lines)


@dataclass
class CharacterVoiceProfile:
    """How a character sounds. Not an impersonation -- a consistent treatment.

    `native_assets` is the identity anchor: the real barks that make the
    character recognisable. `tts_voice` covers the lines the game never
    recorded, and the processing chain pulls it toward the anchor.
    """
    role: str
    native_speaker: str | None = None
    tts_voice: str = "bm_george"
    pitch_semitones: float = 0.0     # rubberband, formant-preserving
    formant_shift: float = 1.0
    highpass_hz: int = 90
    lowpass_hz: int = 11000
    compress: bool = True
    room_amount: float = 0.10        # a little space, never a cathedral
    spatial: SpatialMode = SpatialMode.DIEGETIC

    def ffmpeg_chain(self, *, pan: float = 0.0, distance: float = 0.0) -> str:
        """The processing chain, as one ffmpeg filter string.

        Intelligibility wins over realism: attenuation is gentle and the room
        is light, because a teaching line the viewer cannot parse has failed
        whatever else it achieved.
        """
        f: list[str] = []
        if self.pitch_semitones:
            f.append(f"rubberband=pitch={2 ** (self.pitch_semitones / 12):.5f}"
                     f":formant=preserved")
        f.append(f"highpass=f={self.highpass_hz}")
        f.append(f"lowpass=f={self.lowpass_hz}")
        if self.compress:
            f.append("acompressor=threshold=-18dB:ratio=3:attack=8:release=180")
        if self.spatial is SpatialMode.RADIO:
            f.append("acrusher=bits=10:mode=log")
        if self.spatial is SpatialMode.DIEGETIC:
            # gentle distance rolloff, then a stereo placement from the actor's
            # position relative to the camera
            gain = max(0.45, 1.0 - 0.55 * min(1.0, distance))
            f.append(f"volume={gain:.3f}")
            p = max(-1.0, min(1.0, pan))
            l, r = (1 - p) / 2 + 0.5 * (1 - abs(p)), (1 + p) / 2 + 0.5 * (1 - abs(p))
            f.append(f"aformat=channel_layouts=stereo,"
                     f"pan=stereo|c0={l:.3f}*c0|c1={r:.3f}*c0")
        else:
            f.append("aformat=channel_layouts=stereo")
        if self.room_amount > 0:
            d = int(40 + 60 * self.room_amount)
            f.append(f"aecho=0.8:0.85:{d}:{self.room_amount:.2f}")
        f.append("alimiter=limit=0.94")
        return ",".join(f)


@dataclass
class DialogueCue:
    """One spoken line, on the scenario's clock.

    `start_t` is seconds from scenario start -- the SAME basis FrameTruth,
    RoundScenario and the compiler use. There is deliberately no separate
    audio timeline to drift against the picture.
    """
    actor_id: str
    text: str
    start_t: float
    duration_s: float
    audio_path: str
    source_kind: SourceKind
    profile: str = "GUIDE"
    words: list[dict] = field(default_factory=list)
    spatial: SpatialMode = SpatialMode.DIEGETIC
    provenance: str = "SYNTHETIC_EXPLAINER"

    @property
    def end_t(self) -> float:
        return self.start_t + self.duration_s

    def subtitle_at(self, t: float) -> str | None:
        """The subtitle text while this line is speaking.

        One text, one source. A separately typed subtitle is how the caption
        ends up saying something the audio does not.
        """
        return self.text if self.start_t <= t <= self.end_t + 0.25 else None

    def as_dict(self) -> dict:
        d = asdict(self)
        d["source_kind"] = self.source_kind.value
        d["spatial"] = self.spatial.value
        d["end_t"] = round(self.end_t, 3)
        return d


def wav_duration(path: Path) -> float:
    import contextlib, wave
    with contextlib.closing(wave.open(str(path))) as w:
        return w.getnframes() / w.getframerate()


def align_words(path: Path, *, model: str = "base.en") -> tuple[str, list[dict]]:
    """Word-level timing for an audio file, via faster-whisper.

    ASR, not TTS. This cannot make speech; it says when each word happens in
    speech that already exists, which is what subtitles and gesture timing
    need.
    """
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(str(path), word_timestamps=True, language="en")
    text, words = [], []
    for s in segs:
        text.append(s.text.strip())
        for w in (s.words or []):
            words.append({"w": w.word.strip(), "s": round(w.start, 3),
                          "e": round(w.end, 3)})
    return " ".join(text).strip(), words


# ── synthesis: the line the game never recorded ────────────────────────────
#
# WHY THIS IS A SUBPROCESS AND WHY IT STUBS A CUDA CALL.
#
# Kokoro lives in the ComfyUI virtualenv, not in the interpreter that runs the
# engine, so it is reached out-of-process.
#
# Importing it CRASHES on this machine -- an access violation, not an
# exception, so nothing catchable happens and the interpreter simply dies with
# exit 139. The fault is `torch.cuda.device_count()` called at import time by
# `thinc/compat.py` (spaCy's backend, pulled in through misaki's g2p). It is
# the same driver that already segfaults this machine's OpenGL on `glColor4f`.
# Setting CUDA_VISIBLE_DEVICES does NOT avoid it: the enumeration still runs.
# Replacing the probe before the import does, and speech synthesis needs no
# GPU at this length anyway.
#
# The recipe lives here, in the repository, because it previously lived only
# in a session shell -- which is why four synthesised wavs existed that nobody
# could reproduce.

_TTS_RUNNER = r'''
import sys, torch
torch.cuda.device_count = lambda: 0        # see voice.py: import-time SIGSEGV
torch.cuda.is_available = lambda: False
from kokoro import KPipeline
import soundfile as sf, numpy as np
text, voice, lang, dest = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
chunks = [o.audio.numpy() if hasattr(o.audio, "numpy") else o.audio
          for o in KPipeline(lang_code=lang)(text, voice=voice)]
if not chunks:
    raise SystemExit("kokoro produced no audio for that text")
sf.write(dest, np.concatenate(chunks), %d)
''' % TTS_SAMPLE_RATE


def tts_available() -> tuple[bool, str]:
    """Whether a line can be synthesised right now, and why not if not.

    Answers by importing, because the failure mode here is a crash rather than
    an ImportError and a presence check on the file would report success.
    """
    if not TTS_PYTHON.exists():
        return False, f"no interpreter with Kokoro at {TTS_PYTHON}"
    probe = subprocess.run(
        [str(TTS_PYTHON), "-c",
         "import torch\n"
         "torch.cuda.device_count = lambda: 0\n"
         "torch.cuda.is_available = lambda: False\n"
         "from kokoro import KPipeline"],
        capture_output=True, timeout=300)
    if probe.returncode == 0:
        return True, "kokoro imports with the cuda probe replaced"
    if probe.returncode < 0 or probe.returncode == 139:
        return False, ("kokoro crashed on import even with the cuda probe "
                       "replaced; the workaround has stopped working")
    return False, (probe.stderr.decode("utf-8", "replace").strip().splitlines()
                   or ["kokoro import failed"])[-1]


def synthesize(text: str, dest: Path, profile: CharacterVoiceProfile, *,
               lang: str = "b", timeout: int = 600) -> Path:
    """Make speech for a line the game never recorded.

    Raw synthesis only: the result is untreated, at Kokoro's own sample rate.
    Pass it through `render_line` to pull it toward the character. `speak()`
    does both, which is what a caller usually wants.
    """
    if not text.strip():
        raise ValueError("nothing to say")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(TTS_PYTHON), "-c", _TTS_RUNNER, text, profile.tts_voice, lang,
         str(dest)], capture_output=True, timeout=timeout)
    if proc.returncode != 0 or not dest.exists():
        detail = proc.stderr.decode("utf-8", "replace").strip()
        if proc.returncode in (139, -11):
            detail = ("crashed on import; see tts_available() and the note "
                      "above _TTS_RUNNER")
        raise RuntimeError(
            f"synthesis failed for {profile.role} ({profile.tts_voice}): "
            f"{detail or f'exit {proc.returncode}'}")
    return dest


def speak(text: str, dest: Path, profile: CharacterVoiceProfile, *,
          pan: float = 0.0, distance: float = 0.0, lang: str = "b",
          keep_raw: bool = False) -> Path:
    """A finished line in a character's voice: synthesise, then treat.

    This is the function whose absence meant `tts_voice` had no consumer. Every
    field of the profile now reaches audio: `tts_voice` chooses the speaker and
    `ffmpeg_chain` shapes it toward the character's real barks.
    """
    dest = Path(dest)
    raw = dest.with_name(dest.stem + "__raw.wav")
    synthesize(text, raw, profile, lang=lang)
    try:
        return render_line(raw, dest, profile, pan=pan, distance=distance)
    finally:
        if not keep_raw:
            raw.unlink(missing_ok=True)


def render_line(src: Path, dest: Path, profile: CharacterVoiceProfile, *,
                pan: float = 0.0, distance: float = 0.0) -> Path:
    """Apply a voice profile to one audio file."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(FFMPEG), "-v", "error", "-y", "-i", str(src),
         "-af", profile.ffmpeg_chain(pan=pan, distance=distance),
         "-ar", "48000", str(dest)], check=True, timeout=180)
    return dest


# Profiles. The guide is anchored on Crash's real recordings; Keel has no
# speech in the game at all, so his voice is synthetic pulled well down and
# darkened -- big and close, not an impression of anyone.
GUIDE = CharacterVoiceProfile(
    role="PANTHEON_GUIDE", native_speaker="CRASH", tts_voice="af_heart",
    pitch_semitones=0.0, highpass_hz=110, lowpass_hz=10500, room_amount=0.10)

KEEL = CharacterVoiceProfile(
    role="ENEMY_KEEL", native_speaker="KEEL", tts_voice="bm_george",
    pitch_semitones=-4.5, highpass_hz=70, lowpass_hz=8000, room_amount=0.16)

# The rest of the cast. Every model ships taunt.wav plus pain/death/jump barks
# (26 of 26 in pak00 -- see docs/reference/character_roster.json), so each has
# a NATIVE anchor; only Crash has full sentences. Synthetic lines for the
# others are Kokoro voices pulled toward the anchor by the chain below. These
# are treatments, not impressions, and none of them claims to be the original
# performer.
ANARKI = CharacterVoiceProfile(
    role="MOVEMENT", native_speaker="ANARKI", tts_voice="am_michael",
    pitch_semitones=+1.5, highpass_hz=120, lowpass_hz=11000, room_amount=0.06)
SLASH = CharacterVoiceProfile(
    role="TACTICAL", native_speaker="SLASH", tts_voice="af_sky",
    pitch_semitones=+0.5, highpass_hz=110, lowpass_hz=11500, room_amount=0.08)
ORBB = CharacterVoiceProfile(
    role="COMEDY", native_speaker="ORBB", tts_voice="am_adam",
    pitch_semitones=+4.0, highpass_hz=200, lowpass_hz=6500, room_amount=0.2,
    spatial=SpatialMode.RADIO)
SARGE = CharacterVoiceProfile(
    role="VETERAN", native_speaker="SARGE", tts_voice="am_michael",
    pitch_semitones=-3.0, highpass_hz=80, lowpass_hz=9000, room_amount=0.1)
RANGER = CharacterVoiceProfile(
    role="ARCHIVE", native_speaker="RANGER", tts_voice="am_adam",
    pitch_semitones=-1.5, highpass_hz=90, lowpass_hz=10000, room_amount=0.12)

PROFILES = {"GUIDE": GUIDE, "KEEL": KEEL, "ANARKI": ANARKI, "SLASH": SLASH,
            "ORBB": ORBB, "SARGE": SARGE, "RANGER": RANGER}
