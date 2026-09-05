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
FFMPEG = Path("G:/QUAKE_LEGACY/creative_suite/tools/ffmpeg/ffmpeg.exe")


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
    role="PANTHEON_GUIDE", native_speaker="CRASH", tts_voice="bm_george",
    pitch_semitones=0.0, highpass_hz=110, lowpass_hz=10500, room_amount=0.10)

KEEL = CharacterVoiceProfile(
    role="ENEMY_KEEL", native_speaker="KEEL", tts_voice="bm_george",
    pitch_semitones=-4.5, highpass_hz=70, lowpass_hz=8000, room_amount=0.16)

PROFILES = {"GUIDE": GUIDE, "KEEL": KEEL}
