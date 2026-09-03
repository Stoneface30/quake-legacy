"""Choreography: what the music asks for, and what may answer it.

THE ARCHITECTURAL CORRECTION. A score slot does not ask "which frag goes
here". It asks "what should HAPPEN here", and the answer is a set of
synchronised lanes: gameplay, narrative, camera, time, transition, effects,
model, material, world, animation, information, picture-in-picture, text,
sound design, and the response to the musical gesture itself. A frag is one
possible answer among many. A musical attack may equally be answered by a
skin flash, a wall dissolving, a damage number ticking, an enemy appearing,
a camera cut, or a single stuttered frame.

WHAT THIS MODULE IS. The vocabulary and the plan object -- not the renderer.
Every element declares WHEN it happens (start, peak, end in edit time), WHAT
triggered it, HOW it relates to the music, and WHY it exists. An element
without a purpose is refused: EFFECT_FOR_EFFECTS_SAKE is not a purpose.

WHAT IT REFUSES. Choreography never edits demo truth -- it plans a
presentation of it. An element that claims a truth (a round won, a damage
figure, a scoreboard, an enemy count) must name the evidence that supports
it, and a triumphant treatment is refused outright when the round was not
actually won. Effects the pipeline cannot yet render are still plannable,
but they carry their capability and cost so a song is never ranked as
fillable on the strength of fifteen effects that do not exist.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
import hashlib
import json
from typing import Any, Iterable, Sequence

CHOREOGRAPHY_VERSION = "choreography-v1.0.0"
UNKNOWN = "UNKNOWN"

# ── lanes ───────────────────────────────────────────────────────────────────
# One slot carries several of these at once; they are synchronised, not
# alternatives.

LANE_GAMEPLAY = "GAMEPLAY"
LANE_NARRATIVE = "NARRATIVE"
LANE_CAMERA = "CAMERA"
LANE_TIME = "TIME"
LANE_TRANSITION = "TRANSITION"
LANE_FX = "FX"
LANE_MODEL = "MODEL_SKIN"
LANE_MATERIAL = "MATERIAL_TEXTURE"
LANE_WORLD = "WORLD"
LANE_ANIMATION = "ANIMATION"
LANE_INFORMATION = "INFORMATION"
LANE_PIP = "PIP"
LANE_TEXT = "TEXT_CHAT"
LANE_SOUND = "SOUND_DESIGN"
LANE_GESTURE = "MUSIC_GESTURE_RESPONSE"

LANES = (LANE_GAMEPLAY, LANE_NARRATIVE, LANE_CAMERA, LANE_TIME, LANE_TRANSITION,
         LANE_FX, LANE_MODEL, LANE_MATERIAL, LANE_WORLD, LANE_ANIMATION,
         LANE_INFORMATION, LANE_PIP, LANE_TEXT, LANE_SOUND, LANE_GESTURE)

# Lanes whose content is a claim about what happened, not a look. These may
# not be planned without evidence.
TRUTH_BEARING_LANES = (LANE_GAMEPLAY, LANE_INFORMATION, LANE_NARRATIVE)

# ── purpose ─────────────────────────────────────────────────────────────────

PURPOSES = (
    "REVEAL_SKILL", "EXPLAIN_GEOMETRY", "EXPLAIN_CA", "BUILD_TENSION",
    "REVEAL_TEAM", "SHOW_DAMAGE", "SHOW_THREAT", "MUSICAL_PUNCTUATION",
    "COMEDIC_RELEASE", "ROUND_PAYOFF", "TRANSITION", "IDENTITY", "TRIBUTE",
)
BANNED_PURPOSES = ("EFFECT_FOR_EFFECTS_SAKE", "COOL", "FILLER", "")

# ── capability and cost ─────────────────────────────────────────────────────
# What the pipeline can actually do today. A plan may use anything; ranking
# must know the difference.

PROVEN_RUNTIME = "PROVEN_RUNTIME"        # shipped and rendered before
PROTOTYPE = "PROTOTYPE"                  # built once, not production
DESIGNABLE = "DESIGNABLE"                # buildable with known techniques
REQUIRES_NEW_TECH = "REQUIRES_NEW_TECH"  # needs engine or tooling we lack
CREATIVE_SEED = "CREATIVE_SEED"          # an idea, not yet a design
CAPABILITIES = (PROVEN_RUNTIME, PROTOTYPE, DESIGNABLE, REQUIRES_NEW_TECH,
                CREATIVE_SEED)
# Ranked best to worst, for "can the archive actually perform this song".
CAPABILITY_RANK = {PROVEN_RUNTIME: 1.0, PROTOTYPE: 0.7, DESIGNABLE: 0.45,
                   REQUIRES_NEW_TECH: 0.15, CREATIVE_SEED: 0.05}

COST_CHEAP = "CHEAP"
COST_MODERATE = "MODERATE"
COST_EXPENSIVE = "EXPENSIVE"
COST_RND = "R&D"
COSTS = (COST_CHEAP, COST_MODERATE, COST_EXPENSIVE, COST_RND)

# ── density ─────────────────────────────────────────────────────────────────

RESTRAINT, NORMAL, HERO, SPECTACLE = "RESTRAINT", "NORMAL", "HERO", "SPECTACLE"
INTENSITIES = (RESTRAINT, NORMAL, HERO, SPECTACLE)

# ── evidence ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EvidenceRef:
    """What real, recorded thing supports this element.

    `kind` names the evidence class (a frag, a round result, a damage total,
    a reconstructed projectile path, a chat line). `provenance` is the demo
    truth class it came from. Nothing here is invented for presentation; an
    element whose evidence is synthetic must say so in its own lane.
    """
    kind: str
    provenance: str
    ref: str = ""                 # frag id, content hash + time, path id …
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── one element on one lane ─────────────────────────────────────────────────

@dataclass(frozen=True)
class ChoreographyElement:
    """Something that happens, on one lane, at an exact time.

    Times are EDIT microseconds -- the score axis. `peak_us` is the instant
    the element is meant to land against the music; a reveal peaks when the
    enemy becomes visible, not when the fade began.
    """
    lane: str
    action: str                       # a name from the creative corpus
    start_us: int
    end_us: int
    purpose: str
    peak_us: int | None = None
    trigger: str = ""                 # what fires it: a music anchor, a frag …
    musical_relation: str = ""        # ON_ATTACK, IN_NEGATIVE_SPACE, ON_DROP …
    evidence: tuple[EvidenceRef, ...] = ()
    capability: str = DESIGNABLE
    cost: str = COST_MODERATE
    intensity: str = NORMAL
    notes: str = ""

    def __post_init__(self) -> None:
        if self.lane not in LANES:
            raise ValueError(f"unknown lane {self.lane!r}")
        if self.purpose in BANNED_PURPOSES or self.purpose not in PURPOSES:
            raise ValueError(
                f"{self.action}: {self.purpose!r} is not a purpose. Every element "
                f"must say why it exists; decoration is not a reason.")
        if self.end_us < self.start_us:
            raise ValueError(f"{self.action}: element ends before it starts")
        if self.peak_us is not None and not (self.start_us <= self.peak_us <= self.end_us):
            raise ValueError(f"{self.action}: peak lies outside the element")
        if self.capability not in CAPABILITIES:
            raise ValueError(f"unknown capability {self.capability!r}")
        if self.cost not in COSTS:
            raise ValueError(f"unknown cost {self.cost!r}")
        if self.intensity not in INTENSITIES:
            raise ValueError(f"unknown intensity {self.intensity!r}")
        if self.lane in TRUTH_BEARING_LANES and not self.evidence:
            raise ValueError(
                f"{self.action}: the {self.lane} lane states something about what "
                f"happened, so it needs evidence")

    @property
    def duration_us(self) -> int:
        return self.end_us - self.start_us

    @property
    def anchor_us(self) -> int:
        return self.peak_us if self.peak_us is not None else self.start_us

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["evidence"] = [e.to_dict() for e in self.evidence]
        d["duration_us"] = self.duration_us
        d["anchor_us"] = self.anchor_us
        return d


# ── the plan ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ChoreographyPlan:
    """Everything that happens across one score interval, on every lane.

    This is what a score slot resolves to. It is a PLAN: nothing here marks a
    moment as used, and nothing here is a render.
    """
    slot_id: str
    start_us: int
    end_us: int
    musical_role: str                     # BUILD, NEGATIVE_SPACE, DROP, OUTRO …
    narrative: str = ""
    elements: tuple[ChoreographyElement, ...] = ()
    intensity: str = NORMAL
    round_result_required: str = ""       # "WIN" gates triumphant treatments
    round_result_evidence: str = UNKNOWN  # what the demo actually said
    version: str = CHOREOGRAPHY_VERSION

    def __post_init__(self) -> None:
        for e in self.elements:
            if e.start_us < self.start_us or e.end_us > self.end_us:
                raise ValueError(
                    f"{e.action} runs {e.start_us}..{e.end_us}, outside the slot "
                    f"{self.start_us}..{self.end_us}")
        if self.round_result_required:
            if self.round_result_required != self.round_result_evidence:
                raise ValueError(
                    f"this choreography needs round result "
                    f"{self.round_result_required}; the demo says "
                    f"{self.round_result_evidence}. A victory treatment over a "
                    f"round that was not won is a lie the viewer can check.")

    @property
    def duration_us(self) -> int:
        return self.end_us - self.start_us

    def lane(self, name: str) -> tuple[ChoreographyElement, ...]:
        return tuple(e for e in self.elements if e.lane == name)

    @property
    def lanes_used(self) -> tuple[str, ...]:
        return tuple(l for l in LANES if any(e.lane == l for e in self.elements))

    @property
    def weakest_capability(self) -> str:
        """The least deliverable thing in the plan. A plan is only as
        renderable as its hardest element."""
        if not self.elements:
            return PROVEN_RUNTIME
        return min((e.capability for e in self.elements),
                   key=lambda c: CAPABILITY_RANK[c])

    @property
    def capability_score(self) -> float:
        if not self.elements:
            return 0.0
        return round(sum(CAPABILITY_RANK[e.capability] for e in self.elements)
                     / len(self.elements), 4)

    @property
    def cost_profile(self) -> dict[str, int]:
        out = {c: 0 for c in COSTS}
        for e in self.elements:
            out[e.cost] += 1
        return out

    def density(self) -> dict[str, float]:
        """Visual events per second, and the same for the lanes that change
        the world rather than the cut. Spectacle everywhere is not spectacle."""
        secs = max(self.duration_us / 1_000_000, 1e-6)
        transform = (LANE_MODEL, LANE_MATERIAL, LANE_WORLD, LANE_ANIMATION)
        return {
            "visual_events_per_s": round(len(self.elements) / secs, 3),
            "effect_events_per_s": round(len(self.lane(LANE_FX)) / secs, 3),
            "transition_events_per_s": round(len(self.lane(LANE_TRANSITION)) / secs, 3),
            "transformation_events_per_s": round(
                sum(len(self.lane(l)) for l in transform) / secs, 3),
        }

    def gesture_responses(self, trigger: str) -> tuple[ChoreographyElement, ...]:
        """Every element answering one musical gesture. A three-attack figure
        may be answered by three different lanes, not three kills."""
        return tuple(e for e in self.elements if e.trigger == trigger)

    def to_dict(self) -> dict[str, Any]:
        return {"slot_id": self.slot_id, "start_us": self.start_us,
                "end_us": self.end_us, "duration_us": self.duration_us,
                "musical_role": self.musical_role, "narrative": self.narrative,
                "intensity": self.intensity,
                "round_result_required": self.round_result_required,
                "round_result_evidence": self.round_result_evidence,
                "lanes_used": list(self.lanes_used),
                "weakest_capability": self.weakest_capability,
                "capability_score": self.capability_score,
                "cost_profile": self.cost_profile,
                "density": self.density(),
                "elements": [e.to_dict() for e in self.elements],
                "version": self.version}

    @property
    def plan_hash(self) -> str:
        """Same plan, same hash -- so a score can be compared and rebuilt."""
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True).encode()).hexdigest()[:24]


# ── fit dimensions ──────────────────────────────────────────────────────────
# What must be true for a real archive moment to perform this choreography.

FIT_DIMENSIONS = (
    "GAMEPLAY_FIT", "CAMERA_FIT", "RETIME_FIT", "TRANSITION_FIT", "FX_FIT",
    "MODEL_FIT", "MATERIAL_FIT", "INFORMATION_FIT", "ANIMATION_FIT",
    "MUSICAL_GESTURE_FIT", "NARRATIVE_FIT", "RESULT_TRUTH_FIT",
)

# Dimensions that are gates, not weights: failing one refuses the candidate
# rather than scoring it lower.
GATE_DIMENSIONS = ("RESULT_TRUTH_FIT", "INFORMATION_FIT")


@dataclass(frozen=True)
class ChoreographyFit:
    """How well one real candidate can perform one planned choreography."""
    plan_hash: str
    candidate_ref: str
    components: dict[str, float]
    blocked: str = ""

    @property
    def eligible(self) -> bool:
        return not self.blocked

    @property
    def weakest(self) -> tuple[str, float]:
        if not self.components:
            return (UNKNOWN, 0.0)
        k = min(self.components, key=lambda k: self.components[k])
        return (k, self.components[k])

    @property
    def score(self) -> float:
        """The weakest REQUIRED dimension governs. One spectacular lane does
        not compensate for a slot with nothing to cut to."""
        if not self.eligible or not self.components:
            return 0.0
        return round(min(self.components.values()), 4)

    def to_dict(self) -> dict[str, Any]:
        return {"plan_hash": self.plan_hash, "candidate_ref": self.candidate_ref,
                "components": dict(self.components), "blocked": self.blocked,
                "eligible": self.eligible, "score": self.score,
                "weakest": list(self.weakest)}


def temporal_effect_fillability() -> dict[str, Any]:
    """Can the effect vocabulary actually answer a song's demands, with
    timings we have measured rather than guessed?

    Separate from gameplay fillability (are the moments there) and from
    choreography fillability (can the effects be rendered at all). A song
    full of rhythmic figures is only a good choice if the effects that would
    answer them have envelopes somebody has looked at.
    """
    from creative_suite.engine import effect_templates as et
    rows = et.atlas_rows()
    measured = [r for r in rows if r["measured"]]
    by_power = {p: sum(1 for r in rows if r["power"] == p) for p in et.POWERS}
    measured_power = {p: sum(1 for r in measured if r["power"] == p)
                      for p in et.POWERS}
    # A usable vocabulary needs measured tools at more than one scale: micro
    # accents cannot close a two-second gap and a montage cannot close 120 ms.
    scales_covered = sum(1 for p, n in measured_power.items() if n)
    return {"templates": len(rows), "measured": len(measured),
            "measured_share": round(len(measured) / max(len(rows), 1), 4),
            "by_power": by_power, "measured_by_power": measured_power,
            "measured_scales": scales_covered,
            "human_approved": sum(1 for r in rows
                                  if r["provenance"] == et.HUMAN_APPROVED)}


def fillability(plans: Sequence[ChoreographyPlan],
                fits: Sequence[ChoreographyFit]) -> dict[str, Any]:
    """Can the archive actually perform this score?

    Reported in two independent halves. GAMEPLAY fillability asks whether
    real recorded moments exist. CHOREOGRAPHY fillability asks whether the
    effects those plans want can be rendered at all. A song that wants
    fifteen effects we cannot build is not fillable because the gameplay
    happens to be there.
    """
    by_plan: dict[str, list[ChoreographyFit]] = {}
    for f in fits:
        by_plan.setdefault(f.plan_hash, []).append(f)
    depth = {"exceptional": 0, "strong": 0, "weak": 0, "empty": 0}
    for p in plans:
        good = [f for f in by_plan.get(p.plan_hash, ()) if f.eligible]
        best = max((f.score for f in good), default=0.0)
        if not good:
            depth["empty"] += 1
        elif best >= 0.75:
            depth["exceptional"] += 1
        elif best >= 0.5:
            depth["strong"] += 1
        else:
            depth["weak"] += 1
    caps = [p.capability_score for p in plans] or [0.0]
    proven = sum(1 for p in plans if p.weakest_capability == PROVEN_RUNTIME)
    return {
        "slots": len(plans),
        "gameplay_fillability": round(
            (depth["exceptional"] + depth["strong"]) / max(len(plans), 1), 4),
        "choreography_fillability": round(sum(caps) / len(caps), 4),
        "slots_renderable_today": proven,
        "candidate_depth": depth,
        "weakest_capabilities": sorted({p.weakest_capability for p in plans}),
    }


# ── readiness ───────────────────────────────────────────────────────────────

SHORTLIST_BLOCKED = "SONG_SHORTLIST_BLOCKED"
SHORTLIST_READY = "SONG_SHORTLIST_READY"


@dataclass(frozen=True)
class ComposerReadiness:
    """Whether the composer may rank songs yet.

    Ranking songs on gameplay fit alone is the old mistake in a better suit: a
    song is only a good choice if the archive can perform its WHOLE visual
    performance. So the shortlist stays shut until the composer can score
    choreography, not just find frags.
    """
    corpus_entries: int
    lanes_covered: int
    proofs_built: int
    gameplay_truth_ready: bool
    music_library_ready: bool
    choreography_scoring_ready: bool
    temporal_solver_ready: bool = False
    effect_library_ready: bool = False
    blockers: tuple[str, ...] = ()

    @property
    def state(self) -> str:
        return SHORTLIST_READY if not self.blockers else SHORTLIST_BLOCKED

    @property
    def may_shortlist_songs(self) -> bool:
        return not self.blockers

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(state=self.state, may_shortlist_songs=self.may_shortlist_songs)
        return d


def assess_readiness(*, corpus_entries: int, lanes_covered: int,
                     proofs_built: int, gameplay_truth_ready: bool,
                     music_library_ready: bool,
                     temporal_proofs_built: int = 0,
                     measured_templates: int = 0,
                     measured_scales: int = 0,
                     min_proofs: int = 10,
                     min_temporal_proofs: int = 5,
                     min_measured_templates: int = 6,
                     min_measured_scales: int = 3) -> ComposerReadiness:
    """Every condition is named, and a missing one is a blocker, not a warning."""
    blockers: list[str] = []
    if corpus_entries <= 0:
        blockers.append("the creative corpus is empty")
    if lanes_covered < len(LANES):
        blockers.append(f"only {lanes_covered}/{len(LANES)} lanes have vocabulary")
    if proofs_built < min_proofs:
        blockers.append(f"{proofs_built}/{min_proofs} choreography proofs exist")
    if not gameplay_truth_ready:
        blockers.append("gameplay truth closure is incomplete")
    if temporal_proofs_built < min_temporal_proofs:
        blockers.append(f"{temporal_proofs_built}/{min_temporal_proofs} temporal "
                        f"solver proofs exist: without them the composer can find "
                        f"material but cannot fit it to a fixed song")
    if measured_templates < min_measured_templates:
        blockers.append(f"only {measured_templates}/{min_measured_templates} effect "
                        f"templates have swept timing: ranking songs on estimated "
                        f"envelopes would be false precision")
    if measured_scales < min_measured_scales:
        blockers.append(f"measured effects cover {measured_scales}/"
                        f"{min_measured_scales} temporal scales: without tools at "
                        f"several scales the solver cannot close both a 120 ms and "
                        f"a two-second gap")
    if not music_library_ready:
        blockers.append("the music library has unresolved source or duration defects")
    creative = [b for b in blockers if "corpus" in b or "lanes" in b
                or "choreography proofs" in b]
    temporal_ready = temporal_proofs_built >= min_temporal_proofs
    library_ready = (measured_templates >= min_measured_templates
                     and measured_scales >= min_measured_scales)
    return ComposerReadiness(
        corpus_entries=corpus_entries, lanes_covered=lanes_covered,
        proofs_built=proofs_built, gameplay_truth_ready=gameplay_truth_ready,
        music_library_ready=music_library_ready,
        choreography_scoring_ready=not creative,
        temporal_solver_ready=temporal_ready,
        effect_library_ready=library_ready, blockers=tuple(blockers))


def elements_from_temporal(plan: Any, lane_of: dict[str, str] | None = None,
                           purpose_of: dict[str, str] | None = None
                           ) -> tuple[ChoreographyElement, ...]:
    """Turn a solved temporal plan into choreography elements.

    The times come from the COMPOSED timeline, so an element's peak is where
    it actually lands once every freeze, replay and overlap has been counted --
    not where the raw source would have put it.
    """
    lanes = dict(lane_of or {})
    purposes = dict(purpose_of or {})
    default_lane = {"RETIME": LANE_TIME, "REPLAY": LANE_CAMERA,
                    "FREEZE": LANE_TIME, "STUTTER": LANE_FX,
                    "REPEAT": LANE_FX, "INSERT": LANE_TRANSITION,
                    "SYNTHETIC_INSERT": LANE_ANIMATION,
                    "OVERLAP": LANE_TRANSITION, "TRIM": LANE_TIME,
                    "REPLACE": LANE_PIP}
    out: list[ChoreographyElement] = []
    for row, choice in zip(plan.timeline(), plan.choices):
        op = choice.operator
        if row["end_us"] <= row["start_us"]:
            continue                       # an overlap occupies no span of its own
        out.append(ChoreographyElement(
            lane=lanes.get(op.label, default_lane.get(op.kind, LANE_FX)),
            action=op.label, start_us=row["start_us"], end_us=row["end_us"],
            purpose=purposes.get(op.label, op.purpose or "MUSICAL_PUNCTUATION"),
            peak_us=row["peak_us"], trigger=op.anchor_kind,
            musical_relation=op.anchor_kind, capability=op.capability,
            notes=op.notes))
    return tuple(out)
