"""Diagnostic audio built FROM the truth, not detected from the mix.

Two kinds of reference track, for two different questions.

EVENT_REFERENCE answers "where does the engine say this happened?". It is a
deterministic impulse placed at each authoritative timestamp: unmistakable
to a detector, trivially alignable, and completely artificial. It exists so
that pipeline offsets can be measured against a known baseline even when the
Quake mix is acoustically impossible to pick apart. IT MUST NEVER SHIP -- a
click track in a fragmovie is a defect, so every file this module writes
carries the DIAGNOSTIC_PREFIX and `is_diagnostic_only` refuses to lie about it.

SELECTIVE_GAME_AUDIO answers "what does this event actually sound like?". It
places the real pak00 asset for the event's own category at the same
authoritative timestamps, with everything else left out. That gives a clean
LG-hits-only or frag-only stem without asking a detector to separate them
from a continuous beam hum and three other weapons.

Neither is the movie mix. Both are analysis tools, and both are reconstructions
from semantic events -- so both carry provenance saying exactly which events,
which assets and which renderer version produced them.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Iterable, Sequence

import numpy as np

from creative_suite.engine import event_truth as et

RENDERER_VERSION = "event-reference-v1.0.0"
DIAGNOSTIC_PREFIX = "DIAG_"

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = REPO_ROOT / "creative_suite" / "engine" / "sound_templates"
TEMPLATE_MANIFEST = TEMPLATE_ROOT / "manifest.json"
TEMPLATE_AUDIO_ROOT = TEMPLATE_ROOT / "raw"
FFMPEG = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"

SR = 48000

# Which pak00 sound stands in for which semantic event. Chosen by event
# meaning, not by what a detector happens to find: an LG contact is the
# lightning impact, a frag is the hit feedback plus the victim's death.
EVENT_SOUND = {
    et.MY_LG_CONTACT: ("sound/weapons/lightning/lg_hit.wav",),
    et.MY_HIT: ("sound/feedback/hit.wav",),
    et.MY_DAMAGE_TO_ENEMY: ("sound/feedback/hit.wav",),
    et.MY_FRAG: ("sound/feedback/hit.wav",),
    et.ENEMY_DEATH: ("sound/feedback/hit.wav",),
    et.MY_DAMAGE_RECEIVED: ("sound/feedback/hit0.wav",),
    et.ENEMY_WEAPON_FIRE: ("sound/weapons/lightning/lg_fire.wav",),
}

# Named diagnostic stems: which events each one keeps.
STEM_DEFINITIONS: dict[str, tuple[str, ...]] = {
    "MY_HITS_ONLY": (et.MY_LG_CONTACT, et.MY_HIT, et.MY_DAMAGE_TO_ENEMY),
    "MY_FRAGS_ONLY": (et.MY_FRAG, et.ENEMY_DEATH),
    "MY_WEAPON_ONLY": (et.MY_WEAPON_FIRE,),
    "MY_COMBAT_ONLY": (et.MY_WEAPON_FIRE, et.MY_LG_CONTACT, et.MY_HIT,
                       et.MY_DAMAGE_TO_ENEMY, et.MY_FRAG),
    "DAMAGE_RECEIVED_ONLY": (et.MY_DAMAGE_RECEIVED,),
    "ENEMY_WEAPONS_ONLY": (et.ENEMY_WEAPON_FIRE,),
    "OTHER_PLAYERS_ONLY": (et.OTHER_PLAYER_WEAPON_FIRE,
                           et.TEAMMATE_WEAPON_FIRE),
}


class DiagnosticAudioError(RuntimeError):
    pass


# ── provenance for any derived stem ─────────────────────────────────────────

@dataclass(frozen=True)
class StemProvenance:
    """What a derived stem is, and what it was made from.

    A stem without this cannot be used for a sync claim. That rule exists
    because an 'isolated music' artifact of unknown origin reported a 21 dB
    hole and a hit 34 ms from the kill, and the source track had neither.
    """
    stem_name: str
    method: str
    source_kind: str                     # RECONSTRUCTED | EXTRACTED | RENDERED
    source_artifact: str
    source_span_us: tuple[int, int]
    event_kinds: tuple[str, ...]
    event_count: int
    events_hash: str
    asset_hash: str
    renderer_version: str
    output_sha256: str = ""

    @property
    def usable_for_sync_claims(self) -> bool:
        """Reconstructions from authoritative events are trustworthy.

        A stem SEPARATED out of a finished mix is not: source separation
        invents and removes content, and its artefacts look exactly like
        musical events.
        """
        return self.source_kind in ("RECONSTRUCTED", "RENDERED")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["source_span_us"] = list(self.source_span_us)
        d["event_kinds"] = list(self.event_kinds)
        d["usable_for_sync_claims"] = self.usable_for_sync_claims
        return d


def is_diagnostic_only(path: Path | str) -> bool:
    """True only for files this module marks as never-ship."""
    return Path(path).name.startswith(DIAGNOSTIC_PREFIX)


def assert_never_shipped(path: Path | str) -> None:
    if not is_diagnostic_only(path):
        raise DiagnosticAudioError(
            f"{Path(path).name} is a diagnostic track and must carry the "
            f"{DIAGNOSTIC_PREFIX} prefix so it cannot reach a movie mix")


# ── hashing ─────────────────────────────────────────────────────────────────

def events_hash(events: Sequence[et.GameEvent]) -> str:
    payload = json.dumps([[e.kind, e.owner, e.edit_us] for e in events],
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def file_sha256(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def assets_hash(paths: Iterable[str]) -> str:
    h = hashlib.sha256()
    for rel in sorted(paths):
        f = TEMPLATE_AUDIO_ROOT / rel
        h.update(rel.encode("utf-8"))
        if f.exists():
            h.update(file_sha256(f).encode("ascii"))
    return h.hexdigest()[:16]


# ── the impulse baseline ────────────────────────────────────────────────────

def _impulse(sr: int = SR, freq: float = 2000.0,
             length_ms: float = 12.0) -> np.ndarray:
    """A short, sharp, identical click. Its onset IS its timestamp."""
    n = int(sr * length_ms / 1000.0)
    t = np.arange(n) / sr
    return (np.sin(2 * np.pi * freq * t) *
            np.exp(-t / (length_ms / 4000.0))).astype(np.float32)


def render_event_reference(events: Sequence[et.GameEvent], duration_us: int,
                           dst: Path, *, sr: int = SR,
                           kinds: Sequence[str] | None = None
                           ) -> tuple[Path, StemProvenance]:
    """A click at every authoritative timestamp. Machine baseline only.

    Only GAME_EVENT_TRUTH events are accepted: placing a click at a time
    that was itself measured from audio would make the baseline circular.
    """
    dst = Path(dst)
    if not dst.name.startswith(DIAGNOSTIC_PREFIX):
        dst = dst.with_name(DIAGNOSTIC_PREFIX + dst.name)
    picked = [e for e in events
              if e.layer == et.GAME_EVENT_TRUTH
              and (kinds is None or e.kind in set(kinds))]
    if not picked:
        raise DiagnosticAudioError("no authoritative events to reference")
    y = np.zeros(int(sr * duration_us / 1e6) + sr, dtype=np.float32)
    click = _impulse(sr)
    for e in picked:
        i = int(e.edit_us * sr / 1e6)
        if 0 <= i < y.size - click.size:
            y[i:i + click.size] += click
    peak = float(np.max(np.abs(y))) or 1.0
    y = (y / peak * 0.7).astype(np.float32)
    _write_wav(y, sr, dst)
    prov = StemProvenance(
        stem_name="EVENT_REFERENCE", method="deterministic impulse per event",
        source_kind="RECONSTRUCTED", source_artifact="recognition evidence",
        source_span_us=(0, int(duration_us)),
        event_kinds=tuple(sorted({e.kind for e in picked})),
        event_count=len(picked), events_hash=events_hash(picked),
        asset_hash="none", renderer_version=RENDERER_VERSION,
        output_sha256=file_sha256(dst))
    return dst, prov


# ── selective real game audio ───────────────────────────────────────────────

def _load_template(rel: str, sr: int) -> np.ndarray:
    src = TEMPLATE_AUDIO_ROOT / rel
    if not src.exists():
        raise DiagnosticAudioError(f"sound template missing: {rel}")
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "t.wav"
        proc = subprocess.run(
            [str(FFMPEG), "-v", "error", "-y", "-i", str(src), "-ac", "1",
             "-ar", str(sr), "-c:a", "pcm_f32le", str(wav)],
            capture_output=True, text=True)
        if proc.returncode != 0:
            raise DiagnosticAudioError(f"could not decode {rel}")
        import soundfile as sf
        data, _ = sf.read(str(wav), dtype="float32", always_2d=False)
    return np.asarray(data, dtype=np.float32)


def render_selective_reference(events: Sequence[et.GameEvent],
                               duration_us: int, dst: Path, *,
                               stem_name: str = "MY_HITS_ONLY",
                               sr: int = SR) -> tuple[Path, StemProvenance]:
    """The real Quake sound for chosen events, and nothing else.

    Reconstruction, not extraction: the assets are the game's own, placed at
    the engine's own timestamps. It sounds like Quake and it is unambiguous,
    which the finished mix is not.
    """
    dst = Path(dst)
    if not dst.name.startswith(DIAGNOSTIC_PREFIX):
        dst = dst.with_name(DIAGNOSTIC_PREFIX + dst.name)
    kinds = STEM_DEFINITIONS.get(stem_name)
    if kinds is None:
        raise DiagnosticAudioError(f"unknown stem {stem_name!r}")
    picked = [e for e in events
              if e.layer == et.GAME_EVENT_TRUTH and e.kind in set(kinds)]
    if not picked:
        raise DiagnosticAudioError(f"no authoritative events for {stem_name}")

    used: set[str] = set()
    cache: dict[str, np.ndarray] = {}
    y = np.zeros(int(sr * duration_us / 1e6) + 2 * sr, dtype=np.float32)
    for e in picked:
        rels = EVENT_SOUND.get(e.kind)
        if not rels:
            continue
        rel = rels[0]
        if rel not in cache:
            cache[rel] = _load_template(rel, sr)
        used.add(rel)
        clip = cache[rel]
        i = int(e.edit_us * sr / 1e6)
        if i < 0 or i >= y.size:
            continue
        n = min(clip.size, y.size - i)
        y[i:i + n] += clip[:n]
    peak = float(np.max(np.abs(y)))
    if peak > 0.9:
        y = (y / peak * 0.9).astype(np.float32)
    _write_wav(y, sr, dst)
    prov = StemProvenance(
        stem_name=stem_name,
        method="pak00 assets placed at authoritative event times",
        source_kind="RECONSTRUCTED",
        source_artifact="recognition evidence + pak00 sound templates",
        source_span_us=(0, int(duration_us)),
        event_kinds=tuple(sorted({e.kind for e in picked})),
        event_count=len(picked), events_hash=events_hash(picked),
        asset_hash=assets_hash(used), renderer_version=RENDERER_VERSION,
        output_sha256=file_sha256(dst))
    return dst, prov


def _write_wav(y: np.ndarray, sr: int, dst: Path) -> None:
    import soundfile as sf
    dst.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(dst), y, sr, subtype="PCM_16")


# ── cache ───────────────────────────────────────────────────────────────────

class DiagnosticAudioCache:
    """Keyed by the events, the assets and the renderer version."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def key(self, stem_name: str, events: Sequence[et.GameEvent],
            asset_hash: str) -> str:
        return (f"{DIAGNOSTIC_PREFIX}{stem_name}_{events_hash(events)}_"
                f"{asset_hash}_{RENDERER_VERSION.replace('.', '-')}")

    def path_for(self, stem_name: str, events: Sequence[et.GameEvent],
                 asset_hash: str = "none") -> Path:
        return self.root / (self.key(stem_name, events, asset_hash) + ".wav")

    def get_or_render(self, stem_name: str, events: Sequence[et.GameEvent],
                      duration_us: int) -> tuple[Path, StemProvenance | None]:
        rels = {EVENT_SOUND[e.kind][0] for e in events
                if e.kind in EVENT_SOUND and e.kind in
                set(STEM_DEFINITIONS.get(stem_name, ()))}
        ah = assets_hash(rels) if rels else "none"
        dst = self.path_for(stem_name, events, ah)
        if dst.exists():
            return dst, None
        if stem_name == "EVENT_REFERENCE":
            return render_event_reference(events, duration_us, dst)
        return render_selective_reference(events, duration_us, dst,
                                          stem_name=stem_name)
