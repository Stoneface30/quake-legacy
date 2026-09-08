"""Incrementally fill missing high-value MusicFeatureV2 structure.

This is a consolidation adapter around the established librosa algorithms in
``music_structure.py``. It decodes each stale track once and never recomputes
the trustworthy migrated BPM/beat grid.
"""
from __future__ import annotations

from dataclasses import replace
import time
from pathlib import Path
from typing import Any

from creative_suite.engine.music_features_v2 import (
    MusicEventV2, MusicFeatureStore, MusicFeatureV2, MusicRegionV2,
)

EXTRACTOR_VERSION = "music-structure-consolidated@2.0.0"
CURVE_HOP = 5512  # ~250 ms at 22050 Hz


def needs_enrichment(feature: MusicFeatureV2) -> bool:
    return not (feature.energy_curve and feature.onset_curve and
                feature.section_boundary_estimates_us and
                feature.phrase_boundary_estimates_us and feature.regions and
                feature.sample_rate and feature.channels and
                feature.salient_events)


def _normalized(values: Any) -> Any:
    import numpy as np
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return values
    lo, hi = float(values.min()), float(values.max())
    return np.zeros_like(values) if hi - lo < 1e-12 else (values - lo) / (hi - lo)


def _points(values: Any, sr: int, hop: int) -> tuple[tuple[int, float], ...]:
    return tuple((round(i * hop / sr * 1_000_000), round(float(value), 6))
                 for i, value in enumerate(values))


def _section_boundaries(y: Any, sr: int, duration_s: float) -> tuple[int, ...]:
    """Same librosa-agglomerative fallback family used by music_structure."""
    import librosa
    import numpy as np
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
    count = max(3, min(12, round(duration_s / 25.0)))
    try:
        frames = librosa.segment.agglomerative(chroma, count)
        clocks = librosa.frames_to_time(frames, sr=sr, hop_length=512)
    except Exception:
        clocks = np.linspace(0, duration_s, count, endpoint=False)
    return tuple(sorted({round(float(x) * 1_000_000) for x in clocks
                         if 0 < float(x) < duration_s}))


def _phrase_boundaries(feature: MusicFeatureV2,
                       sections: tuple[int, ...]) -> tuple[int, ...]:
    # Eight estimated bars is a phrase hypothesis, never ground truth.
    bars = feature.bar_grid_estimate_us
    phrases = tuple(bars[i] for i in range(0, len(bars), 8)) if bars else ()
    return tuple(sorted(set((*phrases, *sections))))


def _regions(duration_us: int, sections: tuple[int, ...], energy: Any,
             onset: Any, sr: int) -> tuple[MusicRegionV2, ...]:
    import numpy as np
    edges = (0, *sections, duration_us)
    out: list[MusicRegionV2] = []
    global_mean = float(np.mean(energy)) if len(energy) else 0.0
    for start, end in zip(edges, edges[1:]):
        lo = max(0, round(start / 1_000_000 * sr / CURVE_HOP))
        hi = min(len(energy), max(lo + 1, round(end / 1_000_000 * sr / CURVE_HOP)))
        values = energy[lo:hi]
        if len(values) == 0:
            continue
        mean, rise = float(np.mean(values)), float(values[-1] - values[0])
        confidence = min(1.0, .55 + abs(mean-global_mean) + abs(rise))
        if rise >= .18:
            out.append(MusicRegionV2("BUILD_CANDIDATE", start, end, confidence))
        if mean >= global_mean + .08:
            out.append(MusicRegionV2("HIGH_ENERGY_REGION", start, end, confidence))
        elif mean <= global_mean - .08:
            out.append(MusicRegionV2("LOW_ENERGY_REGION", start, end, confidence))
        if rise <= -.18:
            out.append(MusicRegionV2("BREAKDOWN_CANDIDATE", start, end, confidence))
    for boundary in sections:
        idx = min(len(onset)-1, max(0, round(boundary/1_000_000*sr/CURVE_HOP)))
        strength = float(onset[idx]) if len(onset) else 0.0
        if strength >= .65:
            start, end = max(0, boundary-4_000_000), min(duration_us, boundary+8_000_000)
            out.append(MusicRegionV2("DROP_CANDIDATE", start, end, strength))
    return tuple(sorted(out, key=lambda x: (x.start_us, x.kind, x.end_us)))


def enrich_feature(feature: MusicFeatureV2, audio_path: Path) -> MusicFeatureV2:
    """Decode once; preserve migrated beat/BPM facts and fill missing fields."""
    if not needs_enrichment(feature):
        return feature
    import librosa
    import numpy as np
    import soundfile as sf
    info = sf.info(str(audio_path))
    y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
    duration_s = len(y) / sr
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=CURVE_HOP)[0]
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=CURVE_HOP)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr,
                                                 hop_length=CURVE_HOP)[0]
    energy, onset_n, spectral = _normalized(rms), _normalized(onset), _normalized(centroid)
    loudness = 20 * np.log10(np.maximum(rms, 1e-9))
    loudness = np.clip((loudness + 60.0) / 60.0, 0.0, 1.0)
    sections = _section_boundaries(y, sr, duration_s)
    phrases = _phrase_boundaries(feature, sections)
    regions = _regions(feature.duration_us, sections, energy, onset_n, sr)
    peak_frames = librosa.util.peak_pick(onset_n, pre_max=2, post_max=2,
                                         pre_avg=8, post_avg=8, delta=.12, wait=2)
    events = [MusicEventV2("ACCENT", round(int(frame)*CURVE_HOP/sr*1_000_000),
                           round(float(onset_n[frame]), 6), .72)
              for frame in peak_frames if onset_n[frame] >= .55]
    events.extend(MusicEventV2("DROP_CANDIDATE", region.start_us,
                               region.confidence or .5, region.confidence)
                  for region in regions if region.kind == "DROP_CANDIDATE")
    return replace(
        feature, sample_rate=int(info.samplerate), channels=int(info.channels),
        extractor_version=EXTRACTOR_VERSION, status="ENRICHED_V2",
        # BPM and beat positions are reused, not recomputed in this pass.
        # Their confidence therefore remains exactly as sourced; absence is
        # evidence too and must never be replaced with an invented value.
        bpm_confidence=feature.bpm_confidence,
        beat_confidence=feature.beat_confidence,
        onset_curve=_points(onset_n, sr, CURVE_HOP),
        energy_curve=_points(energy, sr, CURVE_HOP),
        loudness_curve=_points(loudness, sr, CURVE_HOP),
        spectral_curve=_points(spectral, sr, CURVE_HOP),
        section_boundary_estimates_us=sections,
        phrase_boundary_estimates_us=phrases, regions=regions,
        salient_events=tuple(sorted(events, key=lambda x: (x.music_us, x.event_type))),
        analysis_provenance=(("extractor", EXTRACTOR_VERSION),
                             ("structure", "music_structure.librosa-agglomerative"),
                             ("bar_grid_semantics", "BAR_GRID_ESTIMATE")),
    )


def enrich_canonical_library(store: MusicFeatureStore, canonical_root: Path,
                             *, limit: int | None = None) -> dict[str, Any]:
    started = time.monotonic(); reused = decoded = failed = 0
    failures: list[dict[str, str]] = []
    candidates = store.all_features()
    if limit is not None:
        candidates = candidates[:limit]
    for feature in candidates:
        if not needs_enrichment(feature):
            reused += 1; continue
        path = Path(canonical_root) / feature.path
        try:
            store.put(enrich_feature(feature, path)); decoded += 1
        except Exception as exc:  # preserve partial progress and exact evidence
            failed += 1; failures.append({"track_hash": feature.track_hash,
                                          "error": f"{type(exc).__name__}: {exc}"})
    return {"total": len(candidates), "decoded": decoded, "reused": reused,
            "failed": failed, "wall_time_s": round(time.monotonic()-started, 3),
            "extractor_version": EXTRACTOR_VERSION, "failures": failures}
