"""
Game-audio event recognition per Rule P1-Z v2 + Rule P1-DD.

v2 REWRITE: action peak is the strongest *recognized* QL game event
(rail fire, rocket impact, player death, grenade explode, etc.) matched
against the QL sound template library at ``phase1/sound_templates/``.
Loudness alone is no longer trusted.

Matcher algorithm (summary, full notes in docs/research/audio-montage-2026-04-18.md):
    1. Load all templates from ``phase1/sound_templates/manifest.json`` once
       into a module-level ``SoundLibrary`` cache. Each template gets:
         * PCM at 22 050 Hz mono (librosa.load, ``sr=22050``)
         * log-mel spectrogram (``n_fft=2048``, ``hop_length=512``, 64 mels)
         * mel-band envelope (sum along frequency axis, L2-normalized)
    2. For each target clip:
         * Same PCM + log-mel + envelope.
         * For every template, cross-correlate the two envelopes via
           ``scipy.signal.correlate(mode='valid')`` → one score curve per
           template per clip. Peak of each curve gives (t, confidence).
         * Cross-correlation of unit-norm envelopes is a cosine-style
           similarity in [-1, 1]; we clip negatives to 0 for threshold logic.
         * Confidence threshold = 0.72 default (tunable via cfg.event_confidence).
    3. Deduplicate: same event_type within 50 ms → keep highest confidence.
    4. Apply event-weight table (P1-Z v2 §Weights).
    5. Grenade 3-s fuse: if ``grenade_fire`` at t_a AND ``grenade_explode``
       at t_a+(2.5..3.5)s co-occur, fold into one synthetic
       ``grenade_direct`` at t_explode with weight=0.90.
    6. Return sorted by ``weight × confidence`` descending.

Why cross-correlation of mel envelopes and not raw MFCC matrix matching:
    Matrix-wide cosine sim across 465 templates × clip frames was >5 s per
    5 s clip in the prototype. Mel envelope cross-correlation via FFT is
    20-50× faster, gives effectively the same transient locator, and the
    template fingerprint remains discriminative (rail crack ≠ rocket launch
    ≠ player gasp, they have distinct mel-envelope shapes at hop=512).

Public API (v2):
    recognize_game_events(clip_path, cfg=None, use_templates=True)
        -> list[GameEvent]
    find_action_peak_v2(clip_path, cfg=None) -> tuple[float|None, str]
        # returns (peak_time_or_None, tag ∈ {'TIGHT','WEAK','RECOGNITION_FAILED','NONE'})

Legacy (v1) API kept for regression:
    find_action_peak(clip_path, sr=48000) -> float | None
    find_action_peaks_per_clip(clip_paths) -> dict[str, float|None]
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, NamedTuple, Optional

import numpy as np

try:  # librosa is optional at import time for type-check environments
    import librosa
except Exception:  # pragma: no cover
    librosa = None  # type: ignore[assignment]

try:
    from scipy.signal import correlate as _scipy_correlate  # type: ignore
except Exception:  # pragma: no cover
    _scipy_correlate = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Constants + canonical event-type table
# ---------------------------------------------------------------------------

TEMPLATE_SR = 22050
TEMPLATE_HOP = 512
TEMPLATE_NFFT = 2048
TEMPLATE_NMELS = 64
DEFAULT_CONF_THRESHOLD = 0.72
DEFAULT_FALLBACK_CONF = 0.40
DEDUP_WINDOW_S = 0.050
GRENADE_FUSE_MIN_S = 2.5
GRENADE_FUSE_MAX_S = 3.5

# Canonical event_type name (how the rest of the pipeline refers to this
# event) mapped from the manifest's ``event_type`` field. Everything not in
# this table keeps its manifest name.
CANONICAL_ALIAS: dict[str, str] = {
    "railgun_fire": "rail_fire",
    "death": "player_death",
    "lightning_impact": "lg_hit",
    "grenade_fire": "grenade_throw",
    "grenade_hgrenb1a": "grenade_explode",
    "grenade_hgrenb2a": "grenade_explode",
    "rocklx1a": "rocket_impact",   # safety
}

# Weight table per Rule P1-Z v2. Anything not listed → 0.30.
EVENT_WEIGHTS: dict[str, float] = {
    "player_death": 1.00,
    "rocket_impact": 0.95,
    "rail_fire": 0.90,
    "grenade_explode": 0.90,
    "grenade_direct": 0.90,  # synthetic throw+explode compound
    "rocket_fire": 0.70,
    "lg_hit": 0.60,
    "plasma_hit": 0.55,
    "plasma_impact": 0.55,
    "shotgun_fire": 0.50,
    "grenade_throw": 0.40,
    "grenade_fire": 0.40,
}

# Only these categories/event_types are eligible matchers. The ``world``,
# ``player_taunt``, ``player_pain`` etc. categories generate false positives
# (map ambience, taunts) against gameplay audio.
ELIGIBLE_CATEGORIES = {
    "feedback",
    "player_death",
    "weapon_fire",
    "weapon_impact",
    "weapon_other",   # contains grenade explode hgrenb*
}

# Per-event-type cap on how many template variants we load (memory + speed).
# Player death has 156 variants across 40 models — we cap to 12 to keep
# correlation per clip under 2 s on a single core.
VARIANT_CAP: dict[str, int] = {
    "player_death": 12,
    "rail_fire": 4,
    "rocket_fire": 4,
    "rocket_impact": 4,
    "grenade_throw": 4,
    "grenade_explode": 4,
    "lg_hit": 4,
}
DEFAULT_VARIANT_CAP = 4


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


class GameEvent(NamedTuple):
    """A single recognized game-audio event in clip-relative time."""

    t: float
    event_type: str
    confidence: float
    weight: float

    @property
    def score(self) -> float:
        """Ranking score used across the pipeline."""
        return float(self.weight) * float(self.confidence)


@dataclass
class _Template:
    event_type: str          # canonical (alias applied)
    path: str
    duration_s: float
    envelope: np.ndarray     # L2-normalized 1-D mel-envelope, hop=512


# ---------------------------------------------------------------------------
# SoundLibrary — module-level cache (loaded lazily, thread-safe)
# ---------------------------------------------------------------------------


class SoundLibrary:
    """Lazy-loaded template cache (process-wide).

    Use ``get()`` to fetch the singleton. First call pre-computes envelopes
    for every eligible template (typically ~60 templates after capping,
    ~100 ms each on a single core → <10 s one-time cost).
    """

    _instance: Optional["SoundLibrary"] = None
    _lock = threading.Lock()

    def __init__(self, templates: list[_Template]):
        self.templates = templates

    @classmethod
    def get(cls, manifest_path: Optional[Path] = None) -> "SoundLibrary":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls._load(manifest_path)
            return cls._instance

    @classmethod
    def _load(cls, manifest_path: Optional[Path]) -> "SoundLibrary":
        if librosa is None:
            return cls([])
        if manifest_path is None:
            manifest_path = Path(__file__).resolve().parent / "sound_templates" / "manifest.json"
        if not manifest_path.exists():
            return cls([])
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return cls([])
        root = Path(manifest.get("root") or manifest_path.parent / "raw")
        categories = manifest.get("categories", {}) or {}

        # Group by canonical event_type so we can apply per-type variant caps.
        grouped: dict[str, list[dict[str, Any]]] = {}
        for cat, items in categories.items():
            if cat not in ELIGIBLE_CATEGORIES:
                continue
            for entry in items:
                raw_evt = str(entry.get("event_type", ""))
                canonical = CANONICAL_ALIAS.get(raw_evt, raw_evt)
                if canonical not in EVENT_WEIGHTS:
                    # Unknown events get filtered unless we have an explicit
                    # weight — keeps the library tight (no taunts, no amb).
                    continue
                grouped.setdefault(canonical, []).append(entry)

        templates: list[_Template] = []
        for canonical, entries in grouped.items():
            cap = VARIANT_CAP.get(canonical, DEFAULT_VARIANT_CAP)
            # Prefer shorter variants (tighter transient) by default.
            entries = sorted(entries, key=lambda e: float(e.get("duration_s", 99.0)))
            for entry in entries[:cap]:
                rel = entry.get("path", "")
                tpath = root / rel
                if not tpath.exists():
                    continue
                env = _compute_envelope(tpath)
                if env is None or env.size < 4:
                    continue
                templates.append(
                    _Template(
                        event_type=canonical,
                        path=str(tpath),
                        duration_s=float(entry.get("duration_s", 0.0)),
                        envelope=env,
                    )
                )
        return cls(templates)


def _compute_envelope(path: Path) -> Optional[np.ndarray]:
    """Load a WAV → log-mel → sum-along-freq → L2 normalize → 1-D envelope."""
    if librosa is None:
        return None
    try:
        y, _ = librosa.load(str(path), sr=TEMPLATE_SR, mono=True)
    except Exception:
        return None
    if y.size < TEMPLATE_NFFT:
        # pad too-short templates so melspectrogram returns ≥1 frame
        y = np.pad(y, (0, TEMPLATE_NFFT - y.size))
    try:
        S = librosa.feature.melspectrogram(
            y=y, sr=TEMPLATE_SR,
            n_fft=TEMPLATE_NFFT, hop_length=TEMPLATE_HOP, n_mels=TEMPLATE_NMELS,
            power=2.0,
        )
    except Exception:
        return None
    # Log-compress for numerical stability, sum mel bands to 1-D envelope.
    logS = np.log1p(S.astype(np.float32))
    env = logS.sum(axis=0)
    n = np.linalg.norm(env)
    if n < 1e-9:
        return None
    return (env / n).astype(np.float32)


# ---------------------------------------------------------------------------
# v2 recognition
# ---------------------------------------------------------------------------


def _match_template(clip_env: np.ndarray, tpl: _Template) -> tuple[float, float]:
    """Return (best_time_s, confidence ∈ [0,1]) for one template vs clip."""
    if tpl.envelope.size > clip_env.size:
        # clip shorter than template → no match
        return 0.0, 0.0
    if _scipy_correlate is not None:
        corr = _scipy_correlate(clip_env, tpl.envelope, mode="valid")
    else:
        # Numpy fallback (slower for long inputs but correct).
        corr = np.correlate(clip_env, tpl.envelope, mode="valid")
    if corr.size == 0:
        return 0.0, 0.0
    # Normalize by local template-length energy of the clip envelope
    # → keeps score in roughly [-1, 1] and stops long-duration clips from
    # dominating via raw dot-product magnitude.
    tpl_len = tpl.envelope.size
    # Rolling L2 norm of clip_env over windows of length tpl_len.
    sq = clip_env.astype(np.float64) ** 2
    cumsum = np.concatenate(([0.0], np.cumsum(sq)))
    window_energy = cumsum[tpl_len:] - cumsum[:-tpl_len]
    local_norm = np.sqrt(window_energy[: corr.size])
    local_norm = np.maximum(local_norm, 1e-6)
    score = corr / local_norm
    best_idx = int(np.argmax(score))
    conf = float(max(0.0, min(1.0, score[best_idx])))
    # Report the time at the CENTER of the matched window (transient
    # typically sits mid-template), converted from frame index to seconds.
    center_frame = best_idx + tpl_len // 2
    t = float(center_frame * TEMPLATE_HOP / TEMPLATE_SR)
    return t, conf


def _compute_clip_envelope(clip_path: Path) -> Optional[np.ndarray]:
    return _compute_envelope(clip_path)


def _apply_grenade_fuse(events: list[GameEvent]) -> list[GameEvent]:
    """Fold grenade_throw + grenade_explode within 2.5..3.5s into grenade_direct."""
    throws = [e for e in events if e.event_type == "grenade_throw"]
    explodes = [e for e in events if e.event_type == "grenade_explode"]
    if not throws or not explodes:
        return events
    consumed_throw: set[int] = set()
    consumed_explode: set[int] = set()
    compounds: list[GameEvent] = []
    for ti, thr in enumerate(throws):
        for ei, exp in enumerate(explodes):
            if ei in consumed_explode:
                continue
            dt = exp.t - thr.t
            if GRENADE_FUSE_MIN_S <= dt <= GRENADE_FUSE_MAX_S:
                conf = float(min(1.0, 0.5 * (thr.confidence + exp.confidence) + 0.1))
                compounds.append(
                    GameEvent(
                        t=exp.t,
                        event_type="grenade_direct",
                        confidence=conf,
                        weight=EVENT_WEIGHTS["grenade_direct"],
                    )
                )
                consumed_throw.add(ti)
                consumed_explode.add(ei)
                break
    if not compounds:
        return events
    keep: list[GameEvent] = []
    ti = ei = 0
    throw_ids = {id(e): i for i, e in enumerate(throws)}
    explode_ids = {id(e): i for i, e in enumerate(explodes)}
    for e in events:
        if e.event_type == "grenade_throw" and throw_ids.get(id(e), -1) in consumed_throw:
            continue
        if e.event_type == "grenade_explode" and explode_ids.get(id(e), -1) in consumed_explode:
            continue
        keep.append(e)
    keep.extend(compounds)
    return keep


def _dedupe(events: list[GameEvent]) -> list[GameEvent]:
    """Within ±DEDUP_WINDOW_S of the same event_type, keep highest confidence."""
    by_type: dict[str, list[GameEvent]] = {}
    for e in events:
        by_type.setdefault(e.event_type, []).append(e)
    out: list[GameEvent] = []
    for etype, group in by_type.items():
        group = sorted(group, key=lambda e: e.t)
        kept: list[GameEvent] = []
        for e in group:
            if kept and (e.t - kept[-1].t) <= DEDUP_WINDOW_S:
                if e.confidence > kept[-1].confidence:
                    kept[-1] = e
                continue
            kept.append(e)
        out.extend(kept)
    return out


def recognize_game_events(
    clip_path: Path | str,
    cfg: Any = None,
    use_templates: bool = True,
    manifest_path: Optional[Path] = None,
) -> list[GameEvent]:
    """Return recognized events in clip_path, sorted by score descending.

    If use_templates=False, degrade to v1 loudest-onset behavior (returns
    at most one synthetic GameEvent with event_type='loudest_onset').
    If no events clear the fallback threshold (0.40), the returned list
    is empty AND tagged RECOGNITION_FAILED at the call-site (find_action_peak_v2).
    """
    path = Path(clip_path)
    if not use_templates:
        t = find_action_peak(path)
        if t is None:
            return []
        return [GameEvent(t=float(t), event_type="loudest_onset",
                          confidence=1.0, weight=0.30)]

    if librosa is None:
        return []
    conf_threshold = DEFAULT_CONF_THRESHOLD
    if cfg is not None:
        conf_threshold = float(getattr(cfg, "event_confidence", DEFAULT_CONF_THRESHOLD))

    lib = SoundLibrary.get(manifest_path)
    if not lib.templates:
        return []

    clip_env = _compute_clip_envelope(path)
    if clip_env is None or clip_env.size < 4:
        return []

    # Match every template, keep best-per-template result above threshold.
    hits: list[GameEvent] = []
    for tpl in lib.templates:
        t, conf = _match_template(clip_env, tpl)
        if conf < conf_threshold:
            continue
        w = EVENT_WEIGHTS.get(tpl.event_type, 0.30)
        hits.append(GameEvent(t=t, event_type=tpl.event_type,
                              confidence=conf, weight=w))

    hits = _dedupe(hits)
    hits = _apply_grenade_fuse(hits)
    hits.sort(key=lambda e: e.score, reverse=True)
    return hits


def find_action_peak_v2(
    clip_path: Path | str,
    cfg: Any = None,
    manifest_path: Optional[Path] = None,
) -> tuple[Optional[float], str]:
    """v2 peak finder: template recognition → (peak_t, tag).

    Tags:
        TIGHT                - recognized event, conf ≥ DEFAULT_CONF_THRESHOLD
        WEAK                 - recognized event in fallback band [0.40, 0.72)
        RECOGNITION_FAILED   - nothing ≥ 0.40, falling back to loudest onset
        NONE                 - no usable signal (silence / decode failure)
    """
    events = recognize_game_events(clip_path, cfg=cfg, manifest_path=manifest_path)
    if events:
        top = events[0]
        tag = "TIGHT" if top.confidence >= DEFAULT_CONF_THRESHOLD else "WEAK"
        return float(top.t), tag
    # Fallback: run with a lower threshold to see if anything at all exists.
    class _Cfg: pass
    low = _Cfg()
    low.event_confidence = DEFAULT_FALLBACK_CONF  # type: ignore[attr-defined]
    weak = recognize_game_events(clip_path, cfg=low, manifest_path=manifest_path)
    if weak:
        top = weak[0]
        return float(top.t), "WEAK"
    # No recognition at all → legacy loudest-onset fallback.
    t = find_action_peak(clip_path)
    if t is None:
        return None, "NONE"
    return float(t), "RECOGNITION_FAILED"


# ---------------------------------------------------------------------------
# v1 API (legacy — kept intact so existing callers and regression tests still work)
# ---------------------------------------------------------------------------


def find_action_peak(clip_path: Path | str, sr: int = 48000) -> float | None:
    """Return the time (seconds, clip-relative) of the loudest transient.

    Returns None if no onset crosses the detection threshold (e.g. pure-silence
    clip or analysis failure).
    """
    if librosa is None:
        raise RuntimeError("librosa is required for find_action_peak")
    path = str(clip_path)
    try:
        y, sr_out = librosa.load(path, sr=sr, mono=True)
    except Exception:
        return None
    if y.size == 0:
        return None

    y = librosa.effects.preemphasis(y, coef=0.97)

    oenv = librosa.onset.onset_strength(
        y=y, sr=sr_out, hop_length=256, aggregate=np.median,
        fmax=8000, n_mels=128,
    )
    onsets = librosa.onset.onset_detect(
        onset_envelope=oenv, sr=sr_out, hop_length=256,
        backtrack=True, pre_max=20, post_max=20,
        pre_avg=50, post_avg=50, delta=0.3, wait=30, units="time",
    )
    if len(onsets) == 0:
        return None
    frames = librosa.time_to_frames(onsets, sr=sr_out, hop_length=256)
    frames = np.clip(frames, 0, len(oenv) - 1)
    peak_idx = int(np.argmax(oenv[frames]))
    return float(onsets[peak_idx])


def find_action_peaks_per_clip(
    clip_paths: Iterable[Path | str],
    sr: int = 48000,
) -> dict[str, float | None]:
    """Batch wrapper — returns {str(path): peak_time_or_None}."""
    return {str(p): find_action_peak(p, sr=sr) for p in clip_paths}


__all__ = [
    "GameEvent",
    "SoundLibrary",
    "recognize_game_events",
    "find_action_peak_v2",
    "find_action_peak",
    "find_action_peaks_per_clip",
    "EVENT_WEIGHTS",
    "DEFAULT_CONF_THRESHOLD",
]


if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) < 2:
        print("usage: python -m phase1.audio_onsets <clip_path>", file=sys.stderr)
        sys.exit(2)
    events = recognize_game_events(sys.argv[1])
    for e in events[:10]:
        print(f"  t={e.t:6.3f}s  type={e.event_type:<18s}  "
              f"conf={e.confidence:.3f}  w={e.weight:.2f}  score={e.score:.3f}")
    peak, tag = find_action_peak_v2(sys.argv[1])
    print(f"peak_v2={peak}  tag={tag}")
