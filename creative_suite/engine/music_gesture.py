"""Repeated musical figures as editable objects, and what they may drive.

WHY BEATS AND DROPS ARE NOT ENOUGH. A repeated three-hit figure -- the
"tu-tu-tu" of a horn stab, a snare triplet, a stabbed chord -- is one musical
gesture, not three unrelated onsets. Cut against it hit-for-hit and you get
frame stutters, stepped tiles, repeated freeze slices or model pulses that
feel authored. Search each of its hits independently and you destroy the
internal rhythm that made it a figure in the first place.

WHAT IS DETECTED, AND WHAT IS NOT. This module finds REPEATED ATTACK GROUPS:
runs of anchors with similar spacing and similar timbre. That is a real,
checkable claim. It does NOT claim to know the instrument. Automatic
instrument recognition on a finished mix is not reliable, and a wrong
confident label is worse than no label, so a gesture reports what it measured
(percussive or harmonic, band emphasis, attack class) and offers a slot for a
human tag. A human tag is authoritative creative evidence -- if the director
says TRUMPET_STUTTER, that is what it is, and the provenance records that a
person said so rather than a detector.

PATTERN-LEVEL SYNC. A gesture is aligned as a WHOLE. Its inter-onset
intervals are preserved exactly, and the visual response inherits them; the
only free parameter is where the pattern starts and a per-class timing bias.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
from typing import Any, Sequence

import numpy as np

GESTURE_VERSION = "music-gesture-v1.0.0"

# A figure is a run of closely spaced attacks whose spacing is regular.
MIN_ATTACKS = 3
MAX_ATTACKS = 12
MAX_IOI_US = 700_000          # beyond this the attacks stop grouping
IOI_REGULARITY = 0.28         # max relative spread of the intervals

# ── what a gesture may drive ────────────────────────────────────────────────

FRAME_STUTTER = "FRAME_STUTTER"
IMAGE_STROBE = "IMAGE_STROBE"
TILE_STEPPING = "TILE_STEPPING"
MULTI_EXPOSURE = "MULTI_EXPOSURE"
FRAME_ECHO = "FRAME_ECHO"
MODEL_PULSE = "MODEL_PULSE"
MATERIAL_PULSE = "MATERIAL_PULSE"
CAMERA_JOLT = "CAMERA_JOLT"
TEXTURE_FLASH = "TEXTURE_FLASH"

RESPONSE_PATTERNS = (FRAME_STUTTER, IMAGE_STROBE, TILE_STEPPING,
                     MULTI_EXPOSURE, FRAME_ECHO, MODEL_PULSE, MATERIAL_PULSE,
                     CAMERA_JOLT, TEXTURE_FLASH)

# Timing bias PER RESPONSE CLASS. The director's -15 ms hero-payoff lead is
# not a universal constant: a stutter driven directly by an attack wants to
# land ON the attack, because the viewer reads them as the same event.
RESPONSE_BIAS_MS: dict[str, float] = {
    FRAME_STUTTER: 0.0, IMAGE_STROBE: 0.0, TILE_STEPPING: 0.0,
    MULTI_EXPOSURE: 0.0, FRAME_ECHO: 0.0, MODEL_PULSE: -5.0,
    MATERIAL_PULSE: -5.0, CAMERA_JOLT: -8.0, TEXTURE_FLASH: 0.0,
}

TAG_SOURCE_DETECTED = "DETECTED"
TAG_SOURCE_USER = "USER"


@dataclass(frozen=True)
class MusicalGesture:
    """A repeated musical figure, with its measured shape and no guesses."""
    start_us: int
    end_us: int
    anchors_us: tuple[int, ...]
    iois_us: tuple[int, ...]
    component: str                    # PERCUSSIVE | HARMONIC | MIXED
    attack_class: str                 # FAST | MEDIUM | SLOW
    dominant_band: str
    regularity: float                 # 1.0 = perfectly even spacing
    confidence: float
    user_tag: str = ""
    tag_source: str = TAG_SOURCE_DETECTED
    provenance: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if len(self.anchors_us) < MIN_ATTACKS:
            raise ValueError(f"a gesture needs at least {MIN_ATTACKS} attacks")
        if tuple(sorted(self.anchors_us)) != tuple(self.anchors_us):
            raise ValueError("gesture attacks must be in order")
        if len(self.iois_us) != len(self.anchors_us) - 1:
            raise ValueError("one interval between each pair of attacks")

    @property
    def attack_count(self) -> int:
        return len(self.anchors_us)

    @property
    def duration_us(self) -> int:
        return self.end_us - self.start_us

    @property
    def label(self) -> str:
        """What to call it: the human's word if there is one."""
        if self.user_tag:
            return self.user_tag
        return f"{self.attack_count}x {self.component.lower()} figure"

    @property
    def gesture_id(self) -> str:
        """Identity from the shape, so the same figure hashes the same."""
        payload = json.dumps({"iois": list(self.iois_us),
                              "component": self.component,
                              "attacks": self.attack_count,
                              "start": self.start_us},
                             sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def tagged(self, tag: str, *, by: str = "director") -> "MusicalGesture":
        """A human names it. That is evidence, and it says who said so."""
        from dataclasses import replace
        return replace(self, user_tag=tag, tag_source=TAG_SOURCE_USER,
                       provenance=self.provenance + (("tagged_by", by),))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["anchors_us"] = list(self.anchors_us)
        d["iois_us"] = list(self.iois_us)
        d["provenance"] = [list(kv) for kv in self.provenance]
        d.update(gesture_id=self.gesture_id, attack_count=self.attack_count,
                 duration_us=self.duration_us, label=self.label)
        return d


def detect_gestures(anchors: Sequence[Any], *, min_attacks: int = MIN_ATTACKS,
                    max_ioi_us: int = MAX_IOI_US,
                    regularity: float = IOI_REGULARITY
                    ) -> list[MusicalGesture]:
    """Find runs of evenly spaced, similar attacks.

    Similar means: same component and same attack class. That keeps a kick
    train from absorbing the hi-hat between its hits, which is what turns a
    clean three-hit figure into a meaningless six.
    """
    ordered = sorted(anchors, key=lambda a: a.perceptual_anchor_us)
    out: list[MusicalGesture] = []
    run: list[Any] = []

    def flush() -> None:
        if len(run) < min_attacks:
            return
        times = [a.perceptual_anchor_us for a in run[:MAX_ATTACKS]]
        group = run[:MAX_ATTACKS]
        iois = [b - a for a, b in zip(times, times[1:])]
        if not iois:
            return
        spread = float(np.std(iois) / max(1.0, np.mean(iois)))
        if spread > regularity:
            return
        bands: dict[str, float] = {}
        for a in group:
            for name, value in a.band_energy:
                bands[name] = bands.get(name, 0.0) + value
        out.append(MusicalGesture(
            start_us=times[0], end_us=times[-1], anchors_us=tuple(times),
            iois_us=tuple(iois), component=group[0].component,
            attack_class=group[0].attack_class,
            dominant_band=(max(bands, key=bands.get) if bands else ""),
            regularity=round(1.0 - min(1.0, spread / regularity), 3),
            confidence=round(float(np.mean(
                [a.pcenter_confidence for a in group])), 3),
            provenance=(("detector", "even-spacing run over V3 anchors"),
                        ("version", GESTURE_VERSION),
                        ("instrument", "NOT identified: timbre is measured, "
                                       "the instrument is not claimed"))))

    for a in ordered:
        if not run:
            run = [a]
            continue
        prev = run[-1]
        same = (a.component == prev.component
                and a.attack_class == prev.attack_class)
        gap = a.perceptual_anchor_us - prev.perceptual_anchor_us
        if same and 0 < gap <= max_ioi_us:
            run.append(a)
        else:
            flush()
            run = [a]
    flush()
    return out


# ── the visual answer ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class VisualResponse:
    """One visual event answering one attack of a gesture."""
    index: int
    at_us: int
    source_anchor_us: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualResponsePattern:
    """A whole gesture's worth of visual events, rhythm intact."""
    pattern: str
    gesture_id: str
    responses: tuple[VisualResponse, ...]
    bias_ms: float
    purpose: str = "MUSICAL_PUNCTUATION"

    def __post_init__(self) -> None:
        if self.pattern not in RESPONSE_PATTERNS:
            raise ValueError(f"unknown response pattern {self.pattern!r}")

    @property
    def iois_us(self) -> tuple[int, ...]:
        t = [r.at_us for r in self.responses]
        return tuple(b - a for a, b in zip(t, t[1:]))

    @property
    def start_us(self) -> int:
        return self.responses[0].at_us

    @property
    def end_us(self) -> int:
        return self.responses[-1].at_us

    def to_dict(self) -> dict[str, Any]:
        return {"pattern": self.pattern, "gesture_id": self.gesture_id,
                "bias_ms": self.bias_ms, "purpose": self.purpose,
                "responses": [r.to_dict() for r in self.responses],
                "iois_us": list(self.iois_us)}


def respond(gesture: MusicalGesture, pattern: str, *,
            bias_ms: float | None = None,
            purpose: str = "MUSICAL_PUNCTUATION") -> VisualResponsePattern:
    """Build the visual answer to a gesture, ALIGNED AS A PATTERN.

    Every response carries the same offset, so the figure's own intervals
    survive exactly. Aligning each hit independently would let the visual
    rhythm drift away from the musical one it is supposed to be quoting.
    """
    if pattern not in RESPONSE_PATTERNS:
        raise ValueError(f"unknown response pattern {pattern!r}")
    offset = int(round((RESPONSE_BIAS_MS[pattern] if bias_ms is None
                        else bias_ms) * 1000.0))
    responses = tuple(VisualResponse(i, us + offset, us)
                      for i, us in enumerate(gesture.anchors_us))
    return VisualResponsePattern(
        pattern=pattern, gesture_id=gesture.gesture_id, responses=responses,
        bias_ms=round(offset / 1000.0, 2), purpose=purpose)


def preserves_rhythm(gesture: MusicalGesture,
                     response: VisualResponsePattern) -> bool:
    """The response must quote the figure, not approximate it."""
    return gesture.iois_us == response.iois_us
