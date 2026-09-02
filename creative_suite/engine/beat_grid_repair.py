"""Full-length beat grids. The score cannot plan on a grid that stops early.

THE DEFECT THIS REPAIRS. `music_enrichment_v2.enrich_feature` says so in its
own comment: "BPM and beat positions are reused, not recomputed in this pass."
The reused values came from a legacy migration that had analysed only the
opening of each track, so across 396 cached songs the beat grid covers a
median 41% of the audio and never more than 95%. That was harmless while
music sat under finished clips. Now that the song IS the canvas, "no cached
beat here" silently reads as "the song has no beat here", and every slot past
the first minute plans on absent evidence.

WHAT THIS DOES. Recomputes the beat grid over the WHOLE track and records how
much of the track it actually covers, so a partial result can never again be
mistaken for a complete one. Bars remain an ESTIMATE -- librosa gives beats,
not downbeats, and a 4/4 assumption is an assumption; it is labelled as one
and carries lower confidence. Subdivisions are derived midpoints, marked as
derived.

CACHE SAFETY. Grids are keyed by track hash AND analyzer version AND
parameter hash. An old truncated row can never be served as new complete
evidence, because it does not match the new key.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Sequence

import numpy as np

ANALYZER_VERSION = "beat-grid-v1.0.0"
ANALYSIS_SR = 22050
HOP = 512

# Below this, the grid is PARTIAL and must say so.
FULL_COVERAGE = 0.90
# Audio often ends in a fade; the last beat legitimately sits before the very
# end, so coverage is measured against the useful audio, not the container.
TAIL_TOLERANCE_US = 3_000_000

STATUS_FULL = "FULL"
STATUS_PARTIAL = "PARTIAL"
STATUS_FAILED = "FAILED"


def params_hash(**kwargs: Any) -> str:
    payload = json.dumps(kwargs, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


DEFAULT_PARAMS = dict(sr=ANALYSIS_SR, hop=HOP, method="librosa.beat_track",
                      units="time", trim=False)


@dataclass(frozen=True)
class BeatGridV1:
    """A beat grid that knows how much of its own song it covers."""
    track_hash: str
    duration_us: int
    beats_us: tuple[int, ...]
    bars_us: tuple[int, ...]
    bpm: float | None
    status: str
    first_covered_us: int
    last_covered_us: int
    analyzer_version: str = ANALYZER_VERSION
    # A grid with no parameter hash cannot be found again, because lookups
    # are keyed by it. Defaulting to the current parameters keeps a grid
    # addressable instead of silently unreachable.
    params: str = field(default_factory=lambda: params_hash(**DEFAULT_PARAMS))
    source_sha256: str = ""
    beat_confidence: float | None = None
    # Measured from the decoded audio. The cached duration is not always the
    # file's real length, and a score built on a wrong duration produces a
    # movie of the wrong length -- see `duration_mismatch`.
    audio_duration_us: int = 0
    bar_semantics: str = "BAR_GRID_ESTIMATE"
    provenance: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.status not in (STATUS_FULL, STATUS_PARTIAL, STATUS_FAILED):
            raise ValueError(f"unknown grid status {self.status!r}")
        if self.status != STATUS_FAILED and not self.beats_us:
            raise ValueError("a non-failed grid needs beats")

    @property
    def coverage(self) -> float:
        if not self.duration_us or not self.beats_us:
            return 0.0
        return round(self.last_covered_us / self.duration_us, 4)

    @property
    def duration_mismatch_us(self) -> int:
        """How far the cached duration sits from the measured audio."""
        if not self.audio_duration_us:
            # Beats past the cached end are themselves proof of a mismatch.
            return max(0, self.last_covered_us - self.duration_us)
        return self.audio_duration_us - self.duration_us

    @property
    def duration_suspect(self) -> bool:
        return abs(self.duration_mismatch_us) > TAIL_TOLERANCE_US

    @property
    def is_full(self) -> bool:
        return self.status == STATUS_FULL

    def covers(self, us: int) -> bool:
        return bool(self.beats_us) and self.first_covered_us <= us <= (
            self.last_covered_us + TAIL_TOLERANCE_US)

    def subdivisions_us(self) -> tuple[int, ...]:
        """Midpoints between beats. DERIVED, not detected."""
        b = sorted(self.beats_us)
        return tuple((x + y) // 2 for x, y in zip(b, b[1:]))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["beats_us"] = list(self.beats_us)
        d["bars_us"] = list(self.bars_us)
        d["provenance"] = [list(kv) for kv in self.provenance]
        d["coverage"] = self.coverage
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BeatGridV1":
        return cls(
            track_hash=str(d["track_hash"]), duration_us=int(d["duration_us"]),
            beats_us=tuple(int(x) for x in d["beats_us"]),
            bars_us=tuple(int(x) for x in d["bars_us"]),
            bpm=d.get("bpm"), status=str(d["status"]),
            first_covered_us=int(d["first_covered_us"]),
            last_covered_us=int(d["last_covered_us"]),
            analyzer_version=str(d.get("analyzer_version", ANALYZER_VERSION)),
            params=str(d.get("params", "")),
            source_sha256=str(d.get("source_sha256", "")),
            beat_confidence=d.get("beat_confidence"),
            audio_duration_us=int(d.get("audio_duration_us", 0)),
            bar_semantics=str(d.get("bar_semantics", "BAR_GRID_ESTIMATE")),
            provenance=tuple((str(k), str(v))
                             for k, v in d.get("provenance", ())))


def status_for(last_covered_us: int, duration_us: int) -> str:
    if not duration_us or last_covered_us <= 0:
        return STATUS_FAILED
    reach = last_covered_us + TAIL_TOLERANCE_US
    return STATUS_FULL if reach >= duration_us * FULL_COVERAGE else STATUS_PARTIAL


def analyse(audio_path: Path | str, *, track_hash: str, duration_us: int,
            beats_per_bar: int = 4) -> BeatGridV1:
    """Track beats across the ENTIRE file, and say how far they reach."""
    import librosa
    y, sr = librosa.load(str(audio_path), sr=ANALYSIS_SR, mono=True)
    if y.size < sr:
        return BeatGridV1(track_hash, duration_us, (), (), None, STATUS_FAILED,
                          0, 0, params=params_hash(**DEFAULT_PARAMS),
                          provenance=(("reason", "audio too short to track"),))
    tempo, frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=HOP,
                                            units="frames", trim=False)
    times = librosa.frames_to_time(frames, sr=sr, hop_length=HOP)
    beats = tuple(int(round(t * 1e6)) for t in times if t >= 0)
    if not beats:
        return BeatGridV1(track_hash, duration_us, (), (), None, STATUS_FAILED,
                          0, 0, params=params_hash(**DEFAULT_PARAMS),
                          provenance=(("reason", "no beats detected"),))
    bars = tuple(beats[i] for i in range(0, len(beats), beats_per_bar))
    bpm = float(np.atleast_1d(tempo)[0]) if tempo is not None else None
    return BeatGridV1(
        track_hash=track_hash, duration_us=duration_us, beats_us=beats,
        bars_us=bars, bpm=round(bpm, 3) if bpm else None,
        status=status_for(beats[-1], duration_us),
        first_covered_us=beats[0], last_covered_us=beats[-1],
        audio_duration_us=int(round(y.size / sr * 1e6)),
        params=params_hash(**DEFAULT_PARAMS),
        # Not a measured downbeat: librosa gives beats and this assumes 4/4.
        bar_semantics="BAR_GRID_ESTIMATE",
        provenance=(("analyzer", ANALYZER_VERSION),
                    ("method", "librosa.beat.beat_track over the whole file"),
                    ("bars", f"every {beats_per_bar}th beat, 4/4 assumed"),
                    ("subdivisions", "derived midpoints, not detected")))


class BeatGridStore:
    """Repaired grids, versioned so a truncated row cannot masquerade."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS music_beat_grids_v1(
              track_hash TEXT NOT NULL, analyzer_version TEXT NOT NULL,
              params_hash TEXT NOT NULL, canonical_json TEXT NOT NULL,
              PRIMARY KEY(track_hash, analyzer_version, params_hash));
            """)

    def put(self, grid: BeatGridV1) -> None:
        payload = json.dumps(grid.to_dict(), sort_keys=True,
                             separators=(",", ":"))
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO music_beat_grids_v1 VALUES (?,?,?,?)",
                       (grid.track_hash, grid.analyzer_version, grid.params,
                        payload))

    def get(self, track_hash: str, *,
            analyzer_version: str = ANALYZER_VERSION,
            params: str | None = None) -> BeatGridV1 | None:
        ph = params or params_hash(**DEFAULT_PARAMS)
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT canonical_json FROM music_beat_grids_v1 WHERE "
                "track_hash=? AND analyzer_version=? AND params_hash=?",
                (track_hash, analyzer_version, ph)).fetchone()
        return None if row is None else BeatGridV1.from_dict(json.loads(row[0]))

    def all_grids(self) -> list[BeatGridV1]:
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT canonical_json FROM music_beat_grids_v1 "
                              "ORDER BY track_hash").fetchall()
        return [BeatGridV1.from_dict(json.loads(r[0])) for r in rows]

    def coverage_report(self) -> dict[str, Any]:
        grids = self.all_grids()
        if not grids:
            return {"tracks": 0}
        cov = sorted(g.coverage for g in grids)
        return {"tracks": len(grids),
                "full": sum(1 for g in grids if g.is_full),
                "partial": sum(1 for g in grids
                               if g.status == STATUS_PARTIAL),
                "failed": sum(1 for g in grids if g.status == STATUS_FAILED),
                "duration_suspect": sum(1 for g in grids if g.duration_suspect),
                "coverage_median": cov[len(cov) // 2],
                "coverage_min": cov[0], "coverage_max": cov[-1]}


def repair_all(features: Sequence[Any], store: BeatGridStore, *,
               resolve_path, progress=None) -> dict[str, Any]:
    """Repair every eligible track once. Existing good rows are reused."""
    done = failed = reused = 0
    errors: list[str] = []
    for feature in features:
        existing = store.get(feature.track_hash)
        if existing is not None and existing.status != STATUS_FAILED:
            reused += 1
            continue
        try:
            path = resolve_path(feature)
            grid = analyse(path, track_hash=feature.track_hash,
                           duration_us=int(feature.duration_us))
            store.put(grid)
            done += 1
        except Exception as exc:                      # noqa: BLE001
            failed += 1
            errors.append(f"{feature.track_hash[:12]}: {type(exc).__name__}")
        if progress:
            progress(done + failed + reused, len(features))
    return {"repaired": done, "reused": reused, "failed": failed,
            "errors": errors[:10], **store.coverage_report()}
