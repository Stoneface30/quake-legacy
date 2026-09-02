"""Every review file must be rebuildable from what we wrote down.

WHY THIS IS A BLOCKER, NOT A NICETY. A shipped LG canary contained music
from 30.328 s while its recorded placement said 22.234 s. Everything argued
from that file -- which musical event landed on the kill, how the breath
behaved, whether the director's pick was the right one -- was argued about a
file the system could not reproduce. A recipe that does not rebuild its own
artifact is not a recipe, it is a note.

So a review artifact ships with a manifest naming every input that decides
its content, and `verify` REBUILDS the relationship and measures it rather
than trusting the fields. The music source position is checked by
correlating the delivered audio against the canonical track, because that is
the exact check the defect above would have failed.

PROVENANCE_REPRODUCIBILITY_ERROR blocks sync claims, creative comparisons
and review requests. If provenance is wrong, it is fixed first.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import hashlib
import json
from pathlib import Path
from typing import Any

PROVENANCE_REPRODUCIBILITY_ERROR = "PROVENANCE_REPRODUCIBILITY_ERROR"
MANIFEST_VERSION = "review-manifest-v1.0.0"

# How far the measured music source start may sit from the recorded one.
# Generous enough for decoder granularity, far too tight for the 8.09 s
# discrepancy this check exists to catch.
MUSIC_START_TOLERANCE_US = 25_000


@dataclass(frozen=True)
class ReviewManifest:
    """Everything that decided what is inside one review artifact."""
    artifact: str
    experiment_variable: str
    variant_name: str
    frag_id: int
    scene_recipe_id: str
    visual_capture_key: str
    preview_assembly_key: str
    demo_source_hash: str
    timemap_hash: str
    requested_rate: str
    music_track_sha256: str
    music_source_start_us: int
    music_source_end_us: int
    music_gain_db: float
    game_gain: float
    limiter_ceiling: float
    mix_trim: float
    codec: str
    scene_start_us: int
    scene_end_us: int
    # The artifact may be an EXTRACT of the scene. Without these the music
    # position check compares the scene's start against the extract's and
    # reports a mismatch that is really just the trim.
    artifact_trim_start_us: int = 0
    artifact_duration_us: int = 0
    hero_event_kind: str = ""
    hero_event_edit_us: int = 0
    matcher_recommendation: str = ""
    user_correction: str = ""
    mix_state: str = ""
    camera_compilation: str = ""
    analyzer_versions: tuple[tuple[str, str], ...] = ()
    output_sha256: str = ""
    manifest_version: str = MANIFEST_VERSION

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["analyzer_versions"] = [list(kv) for kv in self.analyzer_versions]
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ReviewManifest":
        d = dict(d)
        d["analyzer_versions"] = tuple(
            (str(k), str(v)) for k, v in d.get("analyzer_versions", ()))
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})

    @property
    def sidecar_path(self) -> Path:
        return Path(self.artifact).with_suffix(".manifest.json")

    def write(self, path: Path | None = None) -> Path:
        dst = Path(path) if path else self.sidecar_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(self.to_dict(), indent=1, sort_keys=True),
                       encoding="utf-8")
        return dst

    @classmethod
    def load(cls, path: Path | str) -> "ReviewManifest":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def mix_fields(self) -> dict[str, Any]:
        """The knobs that change LEVEL rather than timing."""
        return {"music_gain_db": self.music_gain_db,
                "game_gain": self.game_gain,
                "limiter_ceiling": self.limiter_ceiling,
                "mix_trim": self.mix_trim, "codec": self.codec}


def file_sha256(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class ProvenanceFinding:
    check: str
    severity: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProvenanceReport:
    artifact: str
    findings: tuple[ProvenanceFinding, ...]
    measured_music_start_us: int | None = None

    @property
    def reproducible(self) -> bool:
        return not any(f.severity == "ERROR" for f in self.findings)

    def raise_if_broken(self) -> None:
        if not self.reproducible:
            detail = "; ".join(f.detail for f in self.findings
                               if f.severity == "ERROR")
            raise ProvenanceError(
                f"{PROVENANCE_REPRODUCIBILITY_ERROR}: {self.artifact}: {detail}")

    def to_dict(self) -> dict[str, Any]:
        return {"artifact": self.artifact,
                "reproducible": self.reproducible,
                "measured_music_start_us": self.measured_music_start_us,
                "findings": [f.to_dict() for f in self.findings]}


class ProvenanceError(RuntimeError):
    """Raised when delivered media does not match its recorded recipe."""


def measure_music_start_us(media: Path | str, track: Path | str, *,
                           search_lo_us: int = 0,
                           search_hi_us: int | None = None,
                           duration_us: int | None = None,
                           sr: int = 22050) -> tuple[int, float]:
    """Where in ``track`` the music inside ``media`` actually starts.

    Cross-correlates the delivered audio against the canonical track. Game
    audio in the mix is uncorrelated with the music and behaves as noise, so
    the peak still lands on the true offset; the returned ratio of peak to
    median says how much to believe it.
    """
    import numpy as np
    from scipy.signal import fftconvolve
    from creative_suite.engine import delivered_sync as ds

    y = ds.decode_window(media, 0, duration_us or 30_000_000, sr=sr)
    if y.size == 0:
        raise ProvenanceError(f"could not decode {media}")
    y = y - y.mean()
    hi = search_hi_us if search_hi_us is not None else search_lo_us + 120_000_000
    ref = ds.decode_window(track, search_lo_us, hi, sr=sr)
    if ref.size <= y.size:
        raise ProvenanceError("search window shorter than the media")
    ref = ref - ref.mean()
    corr = np.abs(fftconvolve(ref, y[::-1], mode="valid"))
    peak = int(np.argmax(corr))
    ratio = float(corr[peak] / (np.median(corr) or 1e-9))
    return search_lo_us + int(peak * 1e6 / sr), ratio


def verify(manifest: ReviewManifest, *, track_path: Path | str,
           check_music: bool = True,
           tolerance_us: int = MUSIC_START_TOLERANCE_US) -> ProvenanceReport:
    """Prove the artifact matches its manifest, or say exactly how it does not."""
    findings: list[ProvenanceFinding] = []
    art = Path(manifest.artifact)
    if not art.exists():
        return ProvenanceReport(str(art), (ProvenanceFinding(
            PROVENANCE_REPRODUCIBILITY_ERROR, "ERROR",
            "the artifact named by the manifest does not exist"),))

    if manifest.output_sha256:
        actual = file_sha256(art)
        if actual != manifest.output_sha256:
            findings.append(ProvenanceFinding(
                PROVENANCE_REPRODUCIBILITY_ERROR, "ERROR",
                f"file hash {actual[:12]} does not match the recorded "
                f"{manifest.output_sha256[:12]}: the artifact changed after "
                f"its manifest was written"))
    else:
        findings.append(ProvenanceFinding(
            "MANIFEST_INCOMPLETE", "WARN", "no output hash was recorded"))

    measured: int | None = None
    if check_music and manifest.music_track_sha256:
        span = (manifest.artifact_duration_us or
                manifest.scene_end_us - manifest.scene_start_us)
        expected = (manifest.music_source_start_us +
                    manifest.artifact_trim_start_us)
        lo = max(0, expected - 90_000_000)
        measured, ratio = measure_music_start_us(
            art, track_path, search_lo_us=lo,
            search_hi_us=expected + 90_000_000, duration_us=span)
        delta = measured - expected
        if ratio < 5.0:
            findings.append(ProvenanceFinding(
                "MUSIC_MATCH_WEAK", "WARN",
                f"music correlation peak only {ratio:.1f}x the median; the "
                f"measured start is not trustworthy"))
        elif abs(delta) > tolerance_us:
            findings.append(ProvenanceFinding(
                PROVENANCE_REPRODUCIBILITY_ERROR, "ERROR",
                f"the artifact contains music from "
                f"{measured / 1e6:.3f}s but the manifest implies "
                f"{expected / 1e6:.3f}s "
                f"({delta / 1000:+.0f} ms): the recipe does not reproduce "
                f"this file"))
    return ProvenanceReport(str(art), tuple(findings), measured)


def blocks_review(report: ProvenanceReport) -> bool:
    """A broken manifest blocks the review request, not just the claim."""
    return not report.reproducible
