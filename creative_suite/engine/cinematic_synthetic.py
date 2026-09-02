"""Authored presentation that is allowed to be impossible -- and says so.

Two kinds of thing look like "reconstructed state" and must never be
confused. Historical reconstruction extends what the demo recorded using
only evidence and physics, and it is graded by how much of it is known.
Cinematic synthesis is the opposite: a headbutted grenade, a camera that
flies through an eye, a map that disassembles on a downbeat, a player pose
that never happened. It is not history and does not pretend to be. It is
where PANTHEON is allowed to go completely insane -- intros, outros, memes,
transitions, effects -- precisely because it is labelled.

THE ONE RULE. Synthetic state lives in the recipe and Pandora domain. It
cannot be written into the DemoTruthTimeline, the recognition tables or any
canonical gameplay evidence, and `demo_truth` refuses it at construction.
This module is the place such state is allowed to exist, and every record
here carries CINEMATIC_SYNTHETIC on its face so the diagnostic sheet can draw
RECORDED, RECONSTRUCTED and SYNTHETIC intervals as three different things.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
from typing import Any, Sequence

from creative_suite.engine import demo_truth as dt

SYNTHETIC_VERSION = "cinematic-synthetic-v1.0.0"

# What may be fabricated. Anything not on this list is not a presentation
# element and has no business being synthetic.
DOMAIN_ANIMATION = "PLAYER_ANIMATION"
DOMAIN_CAMERA = "CAMERA"
DOMAIN_MODEL = "MODEL_MORPH"
DOMAIN_WORLD = "WORLD_GEOMETRY"
DOMAIN_MATERIAL = "MATERIAL"
DOMAIN_POSE = "PLAYER_POSE"
DOMAIN_TRANSITION = "TRANSITION_MOTION"
DOMAIN_CHOREOGRAPHY = "INTRO_OUTRO_CHOREOGRAPHY"
DOMAINS = (DOMAIN_ANIMATION, DOMAIN_CAMERA, DOMAIN_MODEL, DOMAIN_WORLD,
           DOMAIN_MATERIAL, DOMAIN_POSE, DOMAIN_TRANSITION,
           DOMAIN_CHOREOGRAPHY)

# Where a synthetic element is allowed to be used. A gameplay scene presented
# as replay is NOT on this list; there, only recorded and reconstructed state
# may drive what the viewer sees.
CONTEXT_INTRO = "INTRO"
CONTEXT_OUTRO = "OUTRO"
CONTEXT_MEME = "MEME"
CONTEXT_TRANSITION = "TRANSITION"
CONTEXT_EFFECT = "EFFECT"
CONTEXTS = (CONTEXT_INTRO, CONTEXT_OUTRO, CONTEXT_MEME, CONTEXT_TRANSITION,
            CONTEXT_EFFECT)


@dataclass(frozen=True)
class SyntheticElement:
    """One authored, non-historical presentation element on the score."""
    name: str
    domain: str
    context: str
    score_start_us: int
    score_end_us: int
    purpose: str
    uses_real_assets: tuple[str, ...] = ()      # models, maps, scene state borrowed
    author: str = "director"
    notes: str = ""
    evidence: str = dt.CINEMATIC_SYNTHETIC

    def __post_init__(self) -> None:
        if self.domain not in DOMAINS:
            raise ValueError(f"unknown synthetic domain {self.domain!r}")
        if self.context not in CONTEXTS:
            raise ValueError(f"synthetic elements are not allowed in "
                             f"{self.context!r}; only in {CONTEXTS}")
        if self.score_end_us <= self.score_start_us:
            raise ValueError("a synthetic element needs positive duration")
        if self.evidence != dt.CINEMATIC_SYNTHETIC:
            raise ValueError("a synthetic element cannot claim any other "
                             "evidence class")
        if not self.purpose or self.purpose in ("NONE", "EFFECT_FOR_EFFECTS_SAKE"):
            raise ValueError("a synthetic element must say why it exists")

    @property
    def duration_us(self) -> int:
        return self.score_end_us - self.score_start_us

    @property
    def element_id(self) -> str:
        payload = json.dumps(self.canonical(), sort_keys=True,
                             separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def canonical(self) -> dict[str, Any]:
        d = asdict(self)
        d["uses_real_assets"] = list(self.uses_real_assets)
        return d

    def to_dict(self) -> dict[str, Any]:
        d = self.canonical()
        d.update(element_id=self.element_id, duration_us=self.duration_us,
                 version=SYNTHETIC_VERSION)
        return d


def as_demo_event(element: SyntheticElement) -> dt.DemoEvent:
    """Deliberately produce the event the timeline will REFUSE.

    Exists so a test can prove the guard, and so nobody writes a helper that
    quietly converts synthetic state into a gameplay event with a nicer
    class. The only DemoEvent a synthetic element can become is one carrying
    CINEMATIC_SYNTHETIC, and DemoTruthTimeline rejects that.
    """
    return dt.DemoEvent(demo_us=element.score_start_us, kind="OTHER_GAME_SOUND",
                        owner="WORLD", evidence=dt.CINEMATIC_SYNTHETIC,
                        source=f"synthetic:{element.name}")


def provenance_lane(recorded: Sequence[tuple[int, int]],
                    reconstructed: Sequence[tuple[int, int]],
                    synthetic: Sequence[tuple[int, int]]) -> list[dict[str, Any]]:
    """Three kinds of interval for the diagnostic sheet, never merged."""
    out: list[dict[str, Any]] = []
    for label, spans in (("RECORDED", recorded),
                         ("RECONSTRUCTED", reconstructed),
                         ("SYNTHETIC", synthetic)):
        for a, b in spans:
            out.append({"start_us": int(a), "end_us": int(b), "label": label})
    return sorted(out, key=lambda d: d["start_us"])
