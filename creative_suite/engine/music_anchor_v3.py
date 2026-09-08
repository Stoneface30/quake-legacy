"""Perceptual musical anchors -- Music Intelligence V3 research slice.

WHY THIS EXISTS. V2 answers "where is the nearest onset?". That question is
not the one an editor asks. The timestamp at which a sound mathematically
begins is not the timestamp at which a listener hears the musical event
happen: music perception separates the ACOUSTIC ONSET from the PERCEPTUAL
ATTACK TIME (the "P-center"). For a kick or a hat the two are close, a few
milliseconds apart. For a slow synth or bass swell the perceived hit can sit
tens of milliseconds -- in published examples beyond 100 ms -- after the
waveform starts. Aligning a frag to a raw onset therefore aligns it to the
wrong instant whenever the sound is not sharp.

So a V3 anchor answers a different question: WHAT WOULD A LISTENER CALL THE
MOMENT OF THIS HIT, and how sure are we? Every anchor carries the acoustic
onset AND the perceptual estimate AND the evidence that produced it, so a
later reader can disagree with the estimate without losing the measurement.

WHAT IS ESTIMATED, AND HOW HONESTLY.

    acoustic_onset_us     measured: envelope backtrack from the local peak
    energy_peak_us        measured: local maximum of the amplitude envelope
    attack_rise_us        measured: peak - onset
    perceptual_anchor_us  ESTIMATED by ENVELOPE_HALF_RISE (see below)
    attack_class          derived from attack_rise_us
    component             measured: HPSS percussive/harmonic energy ratio
    band_energy           measured: 4-band filtered RMS over the attack
    metrical_role         derived from the track's own beat/bar grid
    structural_role       derived from energy either side of the anchor

ENVELOPE_HALF_RISE. The perceptual anchor is placed where the smoothed
amplitude envelope first crosses half of the rise from onset level to peak
level. It is a model, not a measurement: it reproduces the published shape
(fast attacks land within a few ms of onset, slow attacks land far later)
without pretending to be ground truth. `pcenter_confidence` falls as the
attack lengthens and as the peak's prominence over the local bed drops,
because those are exactly the cases where listeners disagree too.

NOTHING HERE TOUCHES GAMEPLAY. This module reads audio and emits evidence.
It never moves a contact, a kill, or a frame.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Sequence

import numpy as np

ANALYZER_VERSION = "music-anchor-v3.1.0"

SR = 22050
ENVELOPE_SMOOTH_MS = 2.0        # ~1 period of 500 Hz: removes sample noise only
ONSET_HOP = 128                 # ~5.8 ms, candidate detection only
SLOW_LAG_FRAMES = 16            # ~93 ms: the lag that makes slow swells visible
# The backtrack must be able to reach the START of the attack it measures.
# At 60 ms a 180 ms swell was reported as a sub-millisecond attack, because
# the look-back began already near the peak.
REFINE_PRE_MS = 300.0
REFINE_POST_MS = 260.0          # and forward for the peak: covers slow swells
RISE_FLOOR = 0.10               # onset = envelope back down to 10% of the rise
HALF_RISE = 0.50                # P-center model crossing

# Attack classes. The boundaries are editorial, chosen so that the classes
# mean what the alignment rules need them to mean: FAST is "the P-center is
# within a couple of milliseconds of the onset, trust the onset", SLOW is
# "the onset is not where this is heard, use the estimate".
ATTACK_FAST = "FAST"
ATTACK_MEDIUM = "MEDIUM"
ATTACK_SLOW = "SLOW"
FAST_MAX_MS = 20.0
MEDIUM_MAX_MS = 60.0

COMPONENT_PERCUSSIVE = "PERCUSSIVE"
COMPONENT_HARMONIC = "HARMONIC"
COMPONENT_MIXED = "MIXED"
PERCUSSIVE_MIN = 0.60
HARMONIC_MAX = 0.40

# Four bands. Without stems "which channel" cannot be answered, so this is
# the honest substitute: which part of the spectrum carries the attack.
BANDS: tuple[tuple[str, float, float], ...] = (
    ("SUB_LOW", 20.0, 120.0),      # kick body, sub bass
    ("LOW_MID", 120.0, 800.0),     # bass notes, snare body, low synth
    ("MID_HIGH", 800.0, 4000.0),   # snare/clap crack, vocal, stabs
    ("HIGH", 4000.0, 10000.0),     # hats, cymbals, transient air
)

ROLE_DOWNBEAT = "DOWNBEAT_ESTIMATE"
ROLE_BEAT = "BEAT"
ROLE_SUBDIVISION = "SUBDIVISION"
ROLE_NONE = "NONE"
GRID_TOLERANCE_US = 35_000

STRUCT_DROP_ENTRY = "DROP_ENTRY"
STRUCT_BUILD = "BUILD"
STRUCT_RETURN = "RETURN"
STRUCT_BREAKDOWN = "BREAKDOWN"
STRUCT_PHRASE = "PHRASE"
STRUCT_NONE = "NONE"

# Two sharp events this far apart are heard as two events, not one accent.
# Below it they fuse and the sharper edge carries the perceived time.
SEPARABLE_FAST_MS = 40.0
# A slow attack may still belong to a nearby sharp transient over a wider
# span, because the sharp edge dominates the perceived timing of the pair.
FUSE_SLOW_MS = 120.0


# ── small DSP helpers ───────────────────────────────────────────────────────

def _envelope(y: np.ndarray, sr: int) -> np.ndarray:
    """True amplitude envelope at sample rate, via the analytic signal.

    NOT rectify-and-smooth. Rectifying a waveform leaves the carrier in the
    result: a 60 Hz kick swings between zero and its peak every 8 ms, so a
    short smoothing window leaves an envelope full of troughs and the onset
    backtrack stops at the first one, reporting a long bass swell as a 3 ms
    attack. The Hilbert magnitude is carrier-independent, so a slow attack
    measures slow whatever note it is playing. A light smoothing afterwards
    removes only sample noise.
    """
    if y.size == 0:
        return y
    from scipy.signal import hilbert
    mag = np.abs(hilbert(y.astype(np.float64))).astype(np.float32)
    win = max(1, int(sr * ENVELOPE_SMOOTH_MS / 1000.0))
    kernel = np.ones(win, dtype=np.float32) / float(win)
    return np.convolve(mag, kernel, mode="same")


def _bandpass(y: np.ndarray, sr: int, lo: float, hi: float) -> np.ndarray:
    from scipy.signal import butter, sosfiltfilt
    nyq = sr / 2.0
    hi = min(hi, nyq * 0.98)
    if lo >= hi:
        return np.zeros_like(y)
    sos = butter(4, [lo / nyq, hi / nyq], btype="band", output="sos")
    return sosfiltfilt(sos, y).astype(np.float32)


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x)))) if x.size else 0.0


# ── the anchor ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MusicalAnchorV3:
    """One perceptually characterised musical event, with its evidence."""
    acoustic_onset_us: int
    attack_rise_us: int
    energy_peak_us: int
    perceptual_anchor_us: int
    pcenter_method: str
    pcenter_confidence: float
    attack_class: str
    component: str
    percussive_ratio: float
    band_energy: tuple[tuple[str, float], ...]
    onset_strength: float
    salience: float
    metrical_role: str = ROLE_NONE
    structural_role: str = STRUCT_NONE
    provenance: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.attack_rise_us < 0:
            raise ValueError("attack_rise_us cannot be negative")
        if not 0.0 <= self.pcenter_confidence <= 1.0:
            raise ValueError("pcenter_confidence must be in [0, 1]")
        if self.attack_class not in (ATTACK_FAST, ATTACK_MEDIUM, ATTACK_SLOW):
            raise ValueError(f"unknown attack_class {self.attack_class!r}")
        if self.component not in (COMPONENT_PERCUSSIVE, COMPONENT_HARMONIC,
                                  COMPONENT_MIXED):
            raise ValueError(f"unknown component {self.component!r}")
        # The estimate must lie between the two things it interpolates.
        if not (self.acoustic_onset_us <= self.perceptual_anchor_us
                <= self.energy_peak_us + 1):
            raise ValueError("perceptual anchor must sit between onset and peak")

    @property
    def pcenter_offset_ms(self) -> float:
        """How far the perceived hit sits after the waveform's start."""
        return round((self.perceptual_anchor_us - self.acoustic_onset_us) / 1000.0, 2)

    @property
    def dominant_band(self) -> str:
        return max(self.band_energy, key=lambda kv: kv[1])[0] if self.band_energy else ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["band_energy"] = [list(kv) for kv in self.band_energy]
        d["provenance"] = [list(kv) for kv in self.provenance]
        d["pcenter_offset_ms"] = self.pcenter_offset_ms
        d["dominant_band"] = self.dominant_band
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MusicalAnchorV3":
        return cls(
            acoustic_onset_us=int(d["acoustic_onset_us"]),
            attack_rise_us=int(d["attack_rise_us"]),
            energy_peak_us=int(d["energy_peak_us"]),
            perceptual_anchor_us=int(d["perceptual_anchor_us"]),
            pcenter_method=str(d["pcenter_method"]),
            pcenter_confidence=float(d["pcenter_confidence"]),
            attack_class=str(d["attack_class"]),
            component=str(d["component"]),
            percussive_ratio=float(d["percussive_ratio"]),
            band_energy=tuple((str(k), float(v)) for k, v in d.get("band_energy", [])),
            onset_strength=float(d["onset_strength"]),
            salience=float(d["salience"]),
            metrical_role=str(d.get("metrical_role", ROLE_NONE)),
            structural_role=str(d.get("structural_role", STRUCT_NONE)),
            provenance=tuple((str(k), str(v)) for k, v in d.get("provenance", ())))


def attack_class_for(rise_ms: float) -> str:
    if rise_ms <= FAST_MAX_MS:
        return ATTACK_FAST
    if rise_ms <= MEDIUM_MAX_MS:
        return ATTACK_MEDIUM
    return ATTACK_SLOW


def component_for(percussive_ratio: float) -> str:
    if percussive_ratio >= PERCUSSIVE_MIN:
        return COMPONENT_PERCUSSIVE
    if percussive_ratio <= HARMONIC_MAX:
        return COMPONENT_HARMONIC
    return COMPONENT_MIXED


def estimate_pcenter(env: np.ndarray, sr: int, onset_i: int, peak_i: int
                     ) -> tuple[int, float]:
    """ENVELOPE_HALF_RISE: index of the half-rise crossing, and confidence.

    Returns the sample index at which the envelope first reaches half of the
    rise from the onset level to the peak level, plus a confidence that
    falls as the attack lengthens -- long attacks are exactly the sounds
    whose perceived timing listeners disagree about.
    """
    if peak_i <= onset_i:
        return onset_i, 0.5
    lo, hi = float(env[onset_i]), float(env[peak_i])
    if hi <= lo:
        return onset_i, 0.4
    target = lo + HALF_RISE * (hi - lo)
    seg = env[onset_i:peak_i + 1]
    idx = int(np.argmax(seg >= target))
    p = onset_i + idx
    rise_ms = (peak_i - onset_i) * 1000.0 / sr
    # Sharp attacks: the crossing is unambiguous. Slow attacks: it is a model.
    conf = 0.95 if rise_ms <= FAST_MAX_MS else (
        0.75 if rise_ms <= MEDIUM_MAX_MS else 0.5)
    prominence = (hi - lo) / hi if hi > 0 else 0.0
    conf *= float(np.clip(0.4 + 0.6 * prominence, 0.0, 1.0))
    return p, round(float(np.clip(conf, 0.0, 1.0)), 3)


# ── window analysis ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class WindowAnalysis:
    """Everything V3 knows about one stretch of one track."""
    track_hash: str
    start_us: int
    end_us: int
    analyzer_version: str
    params_hash: str
    anchors: tuple[MusicalAnchorV3, ...]
    provenance: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"track_hash": self.track_hash, "start_us": self.start_us,
                "end_us": self.end_us, "analyzer_version": self.analyzer_version,
                "params_hash": self.params_hash,
                "anchors": [a.to_dict() for a in self.anchors],
                "provenance": [list(kv) for kv in self.provenance]}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WindowAnalysis":
        return cls(track_hash=str(d["track_hash"]), start_us=int(d["start_us"]),
                   end_us=int(d["end_us"]),
                   analyzer_version=str(d["analyzer_version"]),
                   params_hash=str(d["params_hash"]),
                   anchors=tuple(MusicalAnchorV3.from_dict(a) for a in d["anchors"]),
                   provenance=tuple((str(k), str(v)) for k, v in d.get("provenance", ())))


def params_hash(**kwargs: Any) -> str:
    payload = json.dumps(kwargs, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


DEFAULT_PARAMS = dict(sr=SR, hop=ONSET_HOP, smooth_ms=ENVELOPE_SMOOTH_MS,
                      rise_floor=RISE_FLOOR, half_rise=HALF_RISE,
                      bands=[b[0] for b in BANDS])


def analyse_samples(y: np.ndarray, sr: int, *, offset_us: int = 0,
                    max_anchors: int = 64,
                    delta: float = 0.20) -> list[MusicalAnchorV3]:
    """Find and characterise the salient musical events in decoded audio.

    ``offset_us`` is where the decoded window begins in the track, so every
    timestamp returned is in track time, not window time.
    """
    import librosa
    if y.size < sr // 50:
        return []
    env_full = _envelope(y, sr)
    strength = librosa.onset.onset_strength(y=y, sr=sr, hop_length=ONSET_HOP)
    if strength.size == 0 or float(np.max(strength)) <= 0:
        return []
    norm = strength / float(np.max(strength))
    peaks = librosa.util.peak_pick(norm, pre_max=6, post_max=6, pre_avg=20,
                                   post_avg=20, delta=delta, wait=4)

    # SLOW ATTACKS NEED A SECOND DETECTOR. Spectral flux compares adjacent
    # frames, so a swell that takes 180 ms to arrive produces almost no flux
    # at any single frame and goes undetected entirely -- which would leave
    # the module blind to exactly the sounds whose P-center matters most.
    # A larger comparison lag responds to that slower rise.
    slow = librosa.onset.onset_strength(y=y, sr=sr, hop_length=ONSET_HOP,
                                        lag=SLOW_LAG_FRAMES)
    if slow.size and float(np.max(slow)) > 0:
        slow_norm = slow / float(np.max(slow))
        slow_peaks = librosa.util.peak_pick(
            slow_norm, pre_max=12, post_max=12, pre_avg=30, post_avg=30,
            delta=delta, wait=SLOW_LAG_FRAMES)
        if slow_peaks.size:
            peaks = np.unique(np.concatenate([peaks, slow_peaks]))
            norm = np.maximum(norm, slow_norm[:norm.size]
                              if slow_norm.size >= norm.size
                              else np.pad(slow_norm, (0, norm.size - slow_norm.size)))
    if peaks.size == 0:
        return []
    order = np.argsort(norm[peaks])[::-1][:max_anchors]
    picked = np.sort(peaks[order])

    # HPSS once per window: percussive/harmonic split for component labels.
    harm, perc = librosa.effects.hpss(y)
    band_signals = {name: _bandpass(y, sr, lo, hi) for name, lo, hi in BANDS}

    pre = int(sr * REFINE_PRE_MS / 1000.0)
    post = int(sr * REFINE_POST_MS / 1000.0)
    out: list[MusicalAnchorV3] = []
    for frame in picked:
        centre = int(librosa.frames_to_samples(int(frame), hop_length=ONSET_HOP))
        a, b = max(0, centre - pre), min(y.size, centre + post)
        if b - a < sr // 200:
            continue
        seg = env_full[a:b]
        peak_i = a + int(np.argmax(seg))
        # Backtrack: walk down from the peak to where the rise begins. The
        # look-back is measured from the PEAK, not from the detected frame:
        # the slow detector reports its candidate about a lag late, and
        # anchoring the window on that candidate started it after the attack
        # had already begun, which measured a 180 ms swell as 31 ms.
        back = max(0, peak_i - pre)
        peak_v = float(env_full[peak_i])
        floor_v = (float(np.percentile(env_full[back:peak_i + 1], 10))
                   if peak_i > back else 0.0)
        threshold = floor_v + RISE_FLOOR * max(0.0, peak_v - floor_v)
        onset_i = peak_i
        while onset_i > back and env_full[onset_i] > threshold:
            onset_i -= 1
        p_i, conf = estimate_pcenter(env_full, sr, onset_i, peak_i)
        rise_ms = (peak_i - onset_i) * 1000.0 / sr

        # Attack span used for the timbral measurements.
        s0, s1 = onset_i, min(y.size, max(peak_i + 1, onset_i + int(sr * 0.05)))
        pr = _rms(perc[s0:s1])
        hr = _rms(harm[s0:s1])
        ratio = pr / (pr + hr) if (pr + hr) > 0 else 0.0
        raw_bands = {n: _rms(band_signals[n][s0:s1]) for n, _, _ in BANDS}
        total = sum(raw_bands.values()) or 1.0
        bands = tuple((n, round(raw_bands[n] / total, 4)) for n, _, _ in BANDS)

        strength_v = float(norm[frame])
        local = float(np.median(norm)) or 1e-6
        salience = float(np.clip(strength_v / max(local * 4.0, 1e-6), 0.0, 1.0))

        out.append(MusicalAnchorV3(
            acoustic_onset_us=offset_us + int(onset_i * 1e6 / sr),
            attack_rise_us=int((peak_i - onset_i) * 1e6 / sr),
            energy_peak_us=offset_us + int(peak_i * 1e6 / sr),
            perceptual_anchor_us=offset_us + int(p_i * 1e6 / sr),
            pcenter_method="ENVELOPE_HALF_RISE",
            pcenter_confidence=conf,
            attack_class=attack_class_for(rise_ms),
            component=component_for(ratio),
            percussive_ratio=round(ratio, 4),
            band_energy=bands,
            onset_strength=round(strength_v, 4),
            salience=round(salience, 4),
            provenance=(("detector", "librosa.onset_strength+peak_pick"),
                        ("refiner", "envelope backtrack from local peak"),
                        ("hpss", "librosa.effects.hpss"),
                        ("analyzer", ANALYZER_VERSION))))
    # Deduplicate anchors that refined onto the same onset.
    seen: dict[int, MusicalAnchorV3] = {}
    for a in out:
        key = a.acoustic_onset_us // 5000       # 5 ms bucket
        if key not in seen or a.salience > seen[key].salience:
            seen[key] = a
    return sorted(seen.values(), key=lambda a: a.acoustic_onset_us)


def analyse_window(path: Path | str, track_hash: str, start_us: int,
                   end_us: int, *, sr: int = SR, **kwargs: Any) -> WindowAnalysis:
    """Decode one window of one track and characterise its anchors."""
    from creative_suite.engine import delivered_sync
    y = delivered_sync.decode_window(path, start_us, end_us, sr=sr)
    anchors = analyse_samples(y, sr, offset_us=int(start_us), **kwargs)
    return WindowAnalysis(
        track_hash=track_hash, start_us=int(start_us), end_us=int(end_us),
        analyzer_version=ANALYZER_VERSION,
        params_hash=params_hash(**DEFAULT_PARAMS),
        anchors=tuple(anchors),
        provenance=(("source", "decoded window, one time"),
                    ("sr", str(sr))))


# ── metrical and structural roles ───────────────────────────────────────────

def metrical_role(anchor_us: int, *, beats_us: Sequence[int],
                  bars_us: Sequence[int] = (),
                  tolerance_us: int = GRID_TOLERANCE_US) -> str:
    """Where the anchor sits on the track's own grid. Never invents a grid."""
    def near(grid: Sequence[int]) -> bool:
        return bool(grid) and min(abs(int(g) - anchor_us) for g in grid) <= tolerance_us
    if near(bars_us):
        return ROLE_DOWNBEAT
    if near(beats_us):
        return ROLE_BEAT
    if len(beats_us) >= 2:
        beats = sorted(int(b) for b in beats_us)
        subs = [(a + b) // 2 for a, b in zip(beats, beats[1:])]
        if near(subs):
            return ROLE_SUBDIVISION
    return ROLE_NONE


def structural_role(anchor_us: int, energy_curve: Sequence[tuple[int, float]], *,
                    boundaries_us: Sequence[int] = (),
                    span_us: int = 2_000_000,
                    rise: float = 1.35, fall: float = 0.75) -> str:
    """Read the shape around the anchor. Labels only what the energy shows."""
    if not energy_curve:
        return STRUCT_NONE
    pts = sorted((int(t), float(v)) for t, v in energy_curve)
    before = [v for t, v in pts if anchor_us - span_us <= t < anchor_us]
    after = [v for t, v in pts if anchor_us <= t <= anchor_us + span_us]
    if not before or not after:
        return STRUCT_NONE
    b, a = float(np.mean(before)), float(np.mean(after))
    at_boundary = bool(boundaries_us) and min(
        abs(int(x) - anchor_us) for x in boundaries_us) <= 1_000_000
    if b <= 0:
        return STRUCT_DROP_ENTRY if a > 0 and at_boundary else STRUCT_RETURN
    ratio = a / b
    if ratio >= rise:
        return STRUCT_DROP_ENTRY if at_boundary else STRUCT_RETURN
    if ratio <= fall:
        return STRUCT_BREAKDOWN
    if at_boundary:
        return STRUCT_PHRASE
    # A rising ramp INTO the anchor is a build even when the step is small.
    first, last = float(np.mean(before[:max(1, len(before) // 3)])), float(
        np.mean(before[-max(1, len(before) // 3):]))
    if first > 0 and last / first >= rise:
        return STRUCT_BUILD
    return STRUCT_NONE


def with_roles(anchor: MusicalAnchorV3, *, beats_us: Sequence[int] = (),
               bars_us: Sequence[int] = (),
               energy_curve: Sequence[tuple[int, float]] = (),
               boundaries_us: Sequence[int] = ()) -> MusicalAnchorV3:
    """Return a copy carrying its grid and structure labels."""
    from dataclasses import replace
    return replace(
        anchor,
        metrical_role=metrical_role(anchor.perceptual_anchor_us,
                                    beats_us=beats_us, bars_us=bars_us),
        structural_role=structural_role(anchor.perceptual_anchor_us,
                                        energy_curve,
                                        boundaries_us=boundaries_us),
        provenance=anchor.provenance + (("roles", "track grid + energy curve"),))


# ── compound accents ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CompoundAccent:
    """Several instrument events heard as ONE musical hit.

    The constituents are preserved: a compound accent never destroys the
    events it is made of, and its timing anchor is one of them rather than
    an average, because averaging a kick with a bass swell produces an
    instant at which nothing actually happens.
    """
    constituents: tuple[MusicalAnchorV3, ...]
    dominant_index: int
    spread_us: int
    reason: str

    @property
    def dominant(self) -> MusicalAnchorV3:
        return self.constituents[self.dominant_index]

    @property
    def perceptual_anchor_us(self) -> int:
        return self.dominant.perceptual_anchor_us

    @property
    def is_compound(self) -> bool:
        return len(self.constituents) > 1

    def to_dict(self) -> dict[str, Any]:
        return {"constituents": [a.to_dict() for a in self.constituents],
                "dominant_index": self.dominant_index,
                "spread_us": self.spread_us, "reason": self.reason,
                "perceptual_anchor_us": self.perceptual_anchor_us,
                "is_compound": self.is_compound}


def _may_fuse(a: MusicalAnchorV3, b: MusicalAnchorV3) -> tuple[bool, str]:
    """Attack-aware fusion test -- not one fixed window for everything."""
    gap_ms = abs(b.acoustic_onset_us - a.acoustic_onset_us) / 1000.0
    both_fast = a.attack_class == ATTACK_FAST and b.attack_class == ATTACK_FAST
    if both_fast:
        if gap_ms >= SEPARABLE_FAST_MS:
            return False, (f"two fast attacks {gap_ms:.0f} ms apart are heard "
                           f"separately (>= {SEPARABLE_FAST_MS:.0f} ms)")
        return True, f"two fast attacks fuse at {gap_ms:.0f} ms"
    if gap_ms <= FUSE_SLOW_MS:
        return True, (f"{a.attack_class}+{b.attack_class} at {gap_ms:.0f} ms: "
                      f"the sharper edge carries the perceived time")
    return False, f"{gap_ms:.0f} ms exceeds the {FUSE_SLOW_MS:.0f} ms fusion span"


def cluster_accents(anchors: Sequence[MusicalAnchorV3]) -> list[CompoundAccent]:
    """Group anchors into perceived accents, keeping every constituent."""
    ordered = sorted(anchors, key=lambda a: a.acoustic_onset_us)
    out: list[CompoundAccent] = []
    group: list[MusicalAnchorV3] = []
    reasons: list[str] = []
    for a in ordered:
        if not group:
            group, reasons = [a], []
            continue
        ok, why = _may_fuse(group[-1], a)
        if ok:
            group.append(a)
            reasons.append(why)
        else:
            out.append(_finish(group, reasons))
            group, reasons = [a], []
    if group:
        out.append(_finish(group, reasons))
    return out


def _finish(group: list[MusicalAnchorV3], reasons: list[str]) -> CompoundAccent:
    # The dominant edge: sharpest attack class first, then salience. This is
    # the finding that a fast transient mixed with a slow one dictates the
    # perceived timing of the pair.
    rank = {ATTACK_FAST: 0, ATTACK_MEDIUM: 1, ATTACK_SLOW: 2}
    idx = min(range(len(group)),
              key=lambda i: (rank[group[i].attack_class], -group[i].salience))
    spread = (group[-1].acoustic_onset_us - group[0].acoustic_onset_us)
    reason = ("single event" if len(group) == 1 else
              "; ".join(reasons) + f"; anchored on the {group[idx].attack_class} "
              f"{group[idx].component.lower()} edge")
    return CompoundAccent(tuple(group), idx, int(spread), reason)


# ── negative space ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NegativeSpace:
    """What the music STOPS doing before the hit. First-class evidence.

    MEASURE THE DRUMS, NOT THE LEVEL. The first version of this check asked
    whether total energy fell across the breath, and it answered "no" for
    the very track whose breath works: across Frag 2340's 875 ms the
    percussion falls about 21 dB to nothing while the sustained layer rises
    about 6 dB, so the TOTAL is flat and the SHAPE is dramatic. Judging on
    total RMS would have thrown away the best evidence in the canary.

    So the fields separate the two layers. ``percussive_drop_db`` is the hole
    the hits leave; ``harmonic_change_db`` says whether something holds the
    space open while they are gone; ``percussive_return_db`` is the slam.
    """
    window_us: tuple[int, int]
    pre_event_onset_density: float
    baseline_onset_density: float
    energy_drop: float
    percussive_drop_db: float
    harmonic_change_db: float
    percussive_return_db: float
    spectral_thinning: float
    return_strength: float
    provenance: tuple[tuple[str, str], ...] = ()

    @property
    def is_negative_space(self) -> bool:
        """True when the HITS get out of the way and come back.

        Stated in decibels of percussive energy, because that is the layer a
        listener hears stop. A sustained pad that holds through the gap does
        not disqualify the shape -- it is part of it.
        """
        return (self.percussive_drop_db <= -6.0
                and self.percussive_return_db >= 6.0)

    @property
    def shape(self) -> str:
        """Plain description of what the music does across the gap."""
        if not self.is_negative_space:
            return "NO_HOLE"
        if self.harmonic_change_db >= 3.0:
            return "DRUMS_STOP_PAD_SWELLS"
        if self.harmonic_change_db <= -3.0:
            return "EVERYTHING_THINS"
        return "DRUMS_STOP_BED_HOLDS"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["window_us"] = list(self.window_us)
        d["provenance"] = [list(kv) for kv in self.provenance]
        d["is_negative_space"] = self.is_negative_space
        d["shape"] = self.shape
        return d


def _db(x: np.ndarray) -> float:
    return 20.0 * float(np.log10(max(_rms(x), 1e-9)))


def negative_space(y: np.ndarray, sr: int, *, offset_us: int, event_us: int,
                   pre_us: int = 875_000, baseline_us: int = 3_000_000,
                   post_us: int = 500_000) -> NegativeSpace:
    """Measure the hole before ``event_us`` and the return after it.

    HPSS runs ONCE over the whole window and the spans are cut from the
    result. Separating each short span on its own gave unstable ratios --
    median filtering has almost nothing to work with inside 875 ms -- and
    that instability is what reported a 21 dB percussive hole as 0.02.
    """
    import librosa
    harm, perc = librosa.effects.hpss(y) if y.size >= sr // 10 else (y, y)

    def cut(sig: np.ndarray, a_us: int, b_us: int) -> np.ndarray:
        a = int(max(0, (a_us - offset_us) * sr / 1e6))
        b = int(min(sig.size, (b_us - offset_us) * sr / 1e6))
        return sig[a:b] if b > a else np.zeros(0, dtype=np.float32)

    pre_a, pre_b = event_us - pre_us, event_us
    base_a, base_b = event_us - pre_us - baseline_us, event_us - pre_us
    post_a, post_b = event_us, event_us + post_us

    pre, base, post = (cut(y, pre_a, pre_b), cut(y, base_a, base_b),
                       cut(y, post_a, post_b))

    # ONE normalisation for the whole window, then count peaks per span.
    # Normalising each span by its own maximum makes a quiet stretch look as
    # busy as a loud one -- and, read the other way, made a sustained pad
    # read as total silence. Densities are only comparable on a shared scale.
    env_all = librosa.onset.onset_strength(y=y, sr=sr, hop_length=ONSET_HOP)
    if env_all.size and float(np.max(env_all)) > 0:
        env_all = env_all / float(np.max(env_all))
        peak_frames = librosa.util.peak_pick(env_all, pre_max=6, post_max=6,
                                             pre_avg=20, post_avg=20,
                                             delta=0.25, wait=4)
        peak_us = offset_us + (librosa.frames_to_time(
            peak_frames, sr=sr, hop_length=ONSET_HOP) * 1e6)
    else:
        peak_us = np.zeros(0)

    def density(a_us: int, b_us: int) -> float:
        span_s = (b_us - a_us) / 1e6
        if span_s <= 0 or peak_us.size == 0:
            return 0.0
        n = int(np.sum((peak_us >= a_us) & (peak_us < b_us)))
        return round(n / span_s, 3)

    def high_share(x: np.ndarray) -> float:
        if x.size < sr // 20:
            return 0.0
        total = _rms(x) or 1e-9
        return _rms(_bandpass(x, sr, 800.0, 10000.0)) / total

    pre_e, base_e, post_e = _rms(pre), _rms(base), _rms(post)
    p_base, p_pre, p_post = (_db(cut(perc, base_a, base_b)),
                             _db(cut(perc, pre_a, pre_b)),
                             _db(cut(perc, post_a, post_b)))
    h_base, h_pre = _db(cut(harm, base_a, base_b)), _db(cut(harm, pre_a, pre_b))
    return NegativeSpace(
        window_us=(pre_a, pre_b),
        pre_event_onset_density=density(pre_a, pre_b),
        baseline_onset_density=density(base_a, base_b),
        energy_drop=round(1.0 - (pre_e / base_e), 3) if base_e > 0 else 0.0,
        percussive_drop_db=round(p_pre - p_base, 2),
        harmonic_change_db=round(h_pre - h_base, 2),
        percussive_return_db=round(p_post - p_pre, 2),
        spectral_thinning=round(high_share(base) - high_share(pre), 3),
        return_strength=round(post_e / pre_e, 3) if pre_e > 0 else 0.0,
        provenance=(("method", "one HPSS over the window, three spans cut from it"),
                    ("levels", "dB RMS of the percussive and harmonic parts"),
                    ("analyzer", ANALYZER_VERSION)))


# ── cache ───────────────────────────────────────────────────────────────────

class AnchorCacheStore:
    """Additive table beside the V2 features. Never re-decodes a whole library.

    Keyed by track hash AND analyzer version AND parameter hash AND window,
    so a change to any of them produces a new row instead of silently
    serving evidence that was computed under different rules.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS music_anchors_v3(
              track_hash TEXT NOT NULL, analyzer_version TEXT NOT NULL,
              params_hash TEXT NOT NULL, start_us INTEGER NOT NULL,
              end_us INTEGER NOT NULL, canonical_json TEXT NOT NULL,
              PRIMARY KEY(track_hash, analyzer_version, params_hash,
                          start_us, end_us));
            """)

    def put(self, analysis: WindowAnalysis) -> None:
        payload = json.dumps(analysis.to_dict(), sort_keys=True,
                             separators=(",", ":"))
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO music_anchors_v3 VALUES (?,?,?,?,?,?)",
                       (analysis.track_hash, analysis.analyzer_version,
                        analysis.params_hash, analysis.start_us,
                        analysis.end_us, payload))

    def get(self, track_hash: str, start_us: int, end_us: int, *,
            analyzer_version: str = ANALYZER_VERSION,
            params: str | None = None) -> WindowAnalysis | None:
        ph = params or params_hash(**DEFAULT_PARAMS)
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT canonical_json FROM music_anchors_v3 WHERE track_hash=? "
                "AND analyzer_version=? AND params_hash=? AND start_us=? AND end_us=?",
                (track_hash, analyzer_version, ph, int(start_us), int(end_us))
            ).fetchone()
        return None if row is None else WindowAnalysis.from_dict(json.loads(row[0]))

    def get_or_compute(self, path: Path | str, track_hash: str, start_us: int,
                       end_us: int, **kwargs: Any) -> WindowAnalysis:
        hit = self.get(track_hash, start_us, end_us)
        if hit is not None:
            return hit
        analysis = analyse_window(path, track_hash, start_us, end_us, **kwargs)
        self.put(analysis)
        return analysis
