"""
Music structure analysis per Rule P1-CC.

Analyze a stitched music track and emit `output/partNN_music_structure.json`
with the beat grid, downbeats, phrase sections, drops, and per-downbeat
salience scores. Downstream `beat_sync.py` uses this file to assign T1/T2/T3
clips to musically meaningful cut candidates.

Schema: docs/research/beatmaker-2026-04-18.md §G.

Detection pipeline (with graceful fallbacks):
    Downbeats:  Beat This! (ISMIR 2024)  -> madmom DBN  -> librosa naive 4/4
    Sections:   msaf scluster             -> librosa.segment.agglomerative
    Drops:      custom low-band novelty  (librosa-only, always runs)
    Salience:   onset_env * kick_energy   (librosa-only, always runs)

Public API:
    analyze_music(wav_path, out_json_path=None) -> dict

A __main__ CLI: `python -m phase1.music_structure --music <wav> --part <N>`.
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np

try:
    import librosa
except Exception:  # pragma: no cover
    librosa = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Downbeat detectors (primary -> fallbacks)
# ---------------------------------------------------------------------------

def _beats_downbeats_beatthis(wav: Path) -> tuple[np.ndarray, np.ndarray, float] | None:
    """Primary: Beat This! transformer (ISMIR 2024).

    Returns (beat_times, downbeat_times, bpm_global) or None if unavailable.
    """
    try:
        from beat_this.inference import File2Beats
    except Exception:
        return None
    try:
        # Prefer CPU if CUDA not available; the library auto-handles.
        f2b = File2Beats(checkpoint_path="final0", dbn=False, device="cpu")
        beats, downbeats = f2b(str(wav))
        beats = np.asarray(beats, dtype=float)
        downbeats = np.asarray(downbeats, dtype=float)
        if len(beats) < 4:
            return None
        diffs = np.diff(beats)
        bpm = float(60.0 / np.median(diffs)) if len(diffs) else 0.0
        return beats, downbeats, bpm
    except Exception as e:  # pragma: no cover
        warnings.warn(f"beat_this failed: {e}")
        return None


def _beats_downbeats_madmom(wav: Path) -> tuple[np.ndarray, np.ndarray, float] | None:
    """Fallback 1: madmom DBN tracker."""
    try:
        from madmom.features.downbeats import (  # type: ignore[import-not-found]
            RNNDownBeatProcessor,
            DBNDownBeatTrackingProcessor,
        )
    except Exception:
        return None
    try:
        act = RNNDownBeatProcessor()(str(wav))
        proc = DBNDownBeatTrackingProcessor(beats_per_bar=[4], fps=100)
        result = proc(act)  # (N, 2) -> [time_s, beat_pos]
        beats = np.asarray(result[:, 0], dtype=float)
        downbeats = np.asarray(result[result[:, 1] == 1, 0], dtype=float)
        diffs = np.diff(beats)
        bpm = float(60.0 / np.median(diffs)) if len(diffs) else 0.0
        return beats, downbeats, bpm
    except Exception as e:  # pragma: no cover
        warnings.warn(f"madmom failed: {e}")
        return None


def _beats_downbeats_librosa(wav: Path) -> tuple[np.ndarray, np.ndarray, float]:
    """Final fallback: librosa beat_track + naive 4/4 downbeat assumption."""
    assert librosa is not None
    y, sr = librosa.load(str(wav), sr=44100, mono=True)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
    beats = librosa.frames_to_time(beat_frames, sr=sr, hop_length=512)
    beats = np.asarray(beats, dtype=float)
    # Naive 4/4: every 4th beat is a downbeat, starting with the first beat.
    downbeats = beats[::4]
    bpm = float(tempo) if np.isscalar(tempo) else float(np.atleast_1d(tempo)[0])
    return beats, downbeats, bpm


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def _sections_msaf(wav: Path) -> list[dict[str, Any]] | None:
    """msaf phrase segmentation; returns None if msaf unavailable or fails."""
    try:
        import msaf  # type: ignore[import-not-found]
    except Exception:
        return None
    try:
        boundaries, labels = msaf.process(
            str(wav),
            boundaries_id="scluster",
            labels_id="scluster",
            feature="pcp",
        )
        boundaries = np.asarray(boundaries, dtype=float)
        sections: list[dict[str, Any]] = []
        for i in range(len(boundaries) - 1):
            lbl = str(labels[i]) if i < len(labels) else f"seg_{i}"
            sections.append(
                {
                    "label": lbl,
                    "start": float(boundaries[i]),
                    "end": float(boundaries[i + 1]),
                    "bars": None,
                }
            )
        return sections
    except Exception as e:  # pragma: no cover
        warnings.warn(f"msaf failed: {e}")
        return None


def _sections_librosa_fallback(wav: Path, n_segments: int = 6) -> list[dict[str, Any]]:
    """Librosa agglomerative fallback — good enough for sectioning when msaf absent."""
    assert librosa is not None
    y, sr = librosa.load(str(wav), sr=22050, mono=True)
    duration = float(len(y) / sr)
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=1024)
        bounds = librosa.segment.agglomerative(chroma, n_segments)
        bound_times = librosa.frames_to_time(bounds, sr=sr, hop_length=1024)
        bound_times = np.concatenate([[0.0], bound_times, [duration]])
        bound_times = np.unique(np.sort(bound_times))
    except Exception:
        # uniform fallback
        bound_times = np.linspace(0.0, duration, n_segments + 1)
    sections: list[dict[str, Any]] = []
    for i in range(len(bound_times) - 1):
        sections.append(
            {
                "label": f"seg_{i}",
                "start": float(bound_times[i]),
                "end": float(bound_times[i + 1]),
                "bars": None,
            }
        )
    return sections


# ---------------------------------------------------------------------------
# Drops
# ---------------------------------------------------------------------------

def _drops_lowband_novelty(y: np.ndarray, sr: int) -> list[dict[str, Any]]:
    """Detect drops: spikes in sub-200 Hz RMS novelty after a monotonic build."""
    assert librosa is not None
    y_low = librosa.effects.preemphasis(y, coef=-0.97)
    S = np.abs(librosa.stft(y_low, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    low_band = S[freqs < 200].sum(axis=0)
    if low_band.max() <= 0:
        return []
    low_rms = librosa.util.normalize(low_band)
    novelty = np.maximum(0, np.diff(low_rms))
    try:
        peaks = librosa.util.peak_pick(
            novelty,
            pre_max=50,
            post_max=50,
            pre_avg=100,
            post_avg=100,
            delta=0.3,
            wait=200,
        )
    except Exception:
        return []
    hop = 512
    drops: list[dict[str, Any]] = []
    for p in peaks:
        t = float(p * hop / sr)
        # Validate: preceding 4 bars (~8 s at 120+ BPM) should show rising trend.
        win = int(8 * sr / hop)
        prior = low_rms[max(0, p - win) : p + 1]
        strength = float(novelty[p])
        if len(prior) >= 10:
            trend_ok = prior[-1] > prior[0] + 0.05
        else:
            trend_ok = True
        if trend_ok:
            drops.append({"t": t, "strength": strength, "bar": None})
    # Normalize strengths to 0..1
    if drops:
        mx = max(d["strength"] for d in drops)
        if mx > 0:
            for d in drops:
                d["strength"] = float(d["strength"] / mx)
    return drops


# ---------------------------------------------------------------------------
# Salience
# ---------------------------------------------------------------------------

def _salience_per_downbeat(
    downbeats: np.ndarray,
    onset_env: np.ndarray,
    low_rms: np.ndarray,
    sr: int,
    hop: int = 512,
) -> np.ndarray:
    """Per-downbeat salience = max(onset_env[±50ms]) * (0.5 + 0.5 * kick_energy)."""
    times = librosa.times_like(onset_env, sr=sr, hop_length=hop) if librosa else None
    scores = np.zeros(len(downbeats), dtype=float)
    for i, t in enumerate(downbeats):
        if times is not None:
            mask = (times >= t - 0.05) & (times <= t + 0.05)
            onset_score = float(onset_env[mask].max()) if mask.any() else 0.0
        else:
            onset_score = 0.0
        t_idx = int(t * sr / hop)
        lo = max(0, t_idx - 2)
        hi = min(len(low_rms), t_idx + 3)
        kick = float(low_rms[lo:hi].max()) if hi > lo else 0.0
        scores[i] = onset_score * (0.5 + 0.5 * kick)
    mx = scores.max()
    if mx > 0:
        scores = scores / mx
    return scores


# ---------------------------------------------------------------------------
# Main analyze
# ---------------------------------------------------------------------------

def analyze_music(
    wav_path: Path | str,
    out_json_path: Path | str | None = None,
) -> dict[str, Any]:
    """Run the full structure pipeline and (optionally) write JSON.

    Returns the structure dict conforming to the §G schema.
    """
    if librosa is None:
        raise RuntimeError("librosa required for analyze_music")
    wav = Path(wav_path)
    if not wav.exists():
        raise FileNotFoundError(wav)

    # --- Beats + downbeats ---
    generator_parts = ["librosa@" + librosa.__version__]
    result = _beats_downbeats_beatthis(wav)
    if result is not None:
        generator_parts.insert(0, "beat_this")
    else:
        result = _beats_downbeats_madmom(wav)
        if result is not None:
            generator_parts.insert(0, "madmom")
        else:
            result = _beats_downbeats_librosa(wav)
            generator_parts.insert(0, "librosa-fallback")
    beats, downbeats, bpm_global = result

    # --- Sections ---
    sections = _sections_msaf(wav)
    if sections is not None:
        generator_parts.append("msaf")
    else:
        sections = _sections_librosa_fallback(wav)
        generator_parts.append("librosa-segments")

    # --- Load audio once for drops + salience ---
    y, sr = librosa.load(str(wav), sr=44100, mono=True)
    duration_s = float(len(y) / sr)

    # low-band RMS envelope for drops + salience
    y_low = librosa.effects.preemphasis(y, coef=-0.97)
    S = np.abs(librosa.stft(y_low, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    low_band = S[freqs < 200].sum(axis=0)
    low_rms = librosa.util.normalize(low_band) if low_band.max() > 0 else low_band

    drops = _drops_lowband_novelty(y, sr)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    salience = _salience_per_downbeat(downbeats, onset_env, low_rms, sr, hop=512)

    # --- Section lookup per downbeat ---
    def section_for(t: float) -> str:
        for s in sections:
            if s["start"] <= t < s["end"]:
                return s["label"]
        return sections[-1]["label"] if sections else "unknown"

    downbeats_out = [
        {
            "t": float(t),
            "bar": i,
            "salience": float(salience[i]) if i < len(salience) else 0.0,
            "section": section_for(float(t)),
        }
        for i, t in enumerate(downbeats)
    ]

    # --- Cut candidates by salience threshold ---
    strong: list[float] = []
    medium: list[float] = []
    soft: list[float] = []
    for d in downbeats_out:
        if d["salience"] >= 0.80:
            strong.append(d["t"])
        elif d["salience"] >= 0.55:
            medium.append(d["t"])
        else:
            soft.append(d["t"])

    structure: dict[str, Any] = {
        "track": wav.name,
        "duration_s": duration_s,
        "bpm_global": bpm_global,
        "bpm_confidence": 0.9 if "beat_this" in generator_parts or "madmom" in generator_parts else 0.6,
        "beat_grid": [float(b) for b in beats],
        "downbeats": downbeats_out,
        "sections": sections,
        "drops": drops,
        "cut_candidates": {"strong": strong, "medium": medium, "soft": soft},
        "generator": "+".join(generator_parts),
    }

    if out_json_path is not None:
        out = Path(out_json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(structure, indent=2))
    return structure


def _main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--music", required=True, help="path to stitched music WAV/MP3")
    ap.add_argument("--part", type=int, required=True)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    music = Path(args.music)
    out_dir = Path(args.out_dir) if args.out_dir else (Path(__file__).resolve().parent.parent / "output")
    out_json = out_dir / f"part{args.part:02d}_music_structure.json"

    s = analyze_music(music, out_json)
    print(f"wrote {out_json}")
    print(
        f"  bpm={s['bpm_global']:.1f}  downbeats={len(s['downbeats'])}  "
        f"drops={len(s['drops'])}  sections={len(s['sections'])}  "
        f"generator={s['generator']}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
