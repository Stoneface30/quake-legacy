"""What each effect costs in time, and how sure we are of that number.

WHY THIS LAYER EXISTS. The solver knows that a freeze adds its duration. It
does not know that a 120 ms freeze reads as a dropped frame and a 900 ms one
drags unless a musical rise is carrying it. Those are different kinds of
knowledge: one is arithmetic, the other is a judgement somebody has to make
by looking. Until an envelope has been looked at, the solver is working from
my estimate, and it must say so rather than lend it false precision.

THE LADDER.

    DESIGN_ESTIMATE    -- reasoned from the material. Not evidence.
    SYNTHETIC_TEST     -- swept on generated footage; delivery is real,
                          the aesthetic verdict is not.
    RUNTIME_MEASURED   -- swept through the real pipeline.
    HUMAN_APPROVED     -- the director looked and said which range is right.

A template may be used at any rung, but `solver_trusted` is only true from
SYNTHETIC_TEST upward, and a plan built on estimates reports that it was.

DELIVERY IS MEASURABLE NOW; TASTE IS NOT. Frame quantisation, the shortest
freeze the encoder can actually hold, whether unequal stutter intervals
survive the frame grid -- those are facts a canary settles today. Whether
275 ms looks good is a question for a person, and it stays open until asked.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from fractions import Fraction
from typing import Any, Iterable, Sequence

from creative_suite.engine import temporal_operators as t

TEMPLATE_VERSION = "effect-templates-v1.0.0"
MS = 1000

# ── timing provenance ───────────────────────────────────────────────────────

DESIGN_ESTIMATE = "DESIGN_ESTIMATE"
SYNTHETIC_TEST = "SYNTHETIC_TEST"
RUNTIME_MEASURED = "RUNTIME_MEASURED"
HUMAN_APPROVED = "HUMAN_APPROVED"
PROVENANCE = (DESIGN_ESTIMATE, SYNTHETIC_TEST, RUNTIME_MEASURED, HUMAN_APPROVED)
PROVENANCE_RANK = {p: i for i, p in enumerate(PROVENANCE)}
# Below this the numbers are reasoning, not measurement.
SOLVER_TRUSTED_FROM = SYNTHETIC_TEST

# ── feasibility states ──────────────────────────────────────────────────────

MATHEMATICALLY_FEASIBLE = "MATHEMATICALLY_FEASIBLE"   # the arithmetic closes
VISUALLY_FEASIBLE = "VISUALLY_FEASIBLE"               # inside a tested envelope
DIRECTOR_APPROVED = "HUMAN_APPROVED"                  # somebody said yes

# ── temporal power ──────────────────────────────────────────────────────────
# How much time an effect can move. Keeps the solver from reaching for a
# four-second death montage to close a 120 ms deficit.

MICRO = "MICRO"          # tens of ms
SMALL = "SMALL"          # ~100-500 ms
MEDIUM = "MEDIUM"        # ~0.5-2 s
LARGE = "LARGE"          # seconds
SEQUENCE = "SEQUENCE"    # reshapes a whole phrase
POWERS = (MICRO, SMALL, MEDIUM, LARGE, SEQUENCE)
POWER_CEILING_US = {MICRO: 300 * MS, SMALL: 1_000 * MS, MEDIUM: 3_000 * MS,
                    LARGE: 8_000 * MS, SEQUENCE: 60_000 * MS}

# ── families ────────────────────────────────────────────────────────────────

F_CUTTING = "TEMPORAL_CUTTING"
F_RETIME = "RETIME"
F_REPLAY = "REPLAY"
F_TRANSITION = "TRANSITION_OVERLAP"
F_RHYTHM = "RHYTHMIC_RESPONSE"
F_WORLD = "WORLD_MATERIAL"
F_MODEL = "MODEL_SKIN"
F_INFORMATION = "INFORMATION"
F_MOVEMENT = "MOVEMENT"
F_PROJECTILE = "PROJECTILE"
F_DEATH = "DEATH"
F_TEAM = "TEAM_1VX"
F_POV = "POV_PIP"
F_CHAT = "CHAT_MEME"
F_FRAMING = "INTRO_OUTRO"
FAMILIES = (F_CUTTING, F_RETIME, F_REPLAY, F_TRANSITION, F_RHYTHM, F_WORLD,
            F_MODEL, F_INFORMATION, F_MOVEMENT, F_PROJECTILE, F_DEATH,
            F_TEAM, F_POV, F_CHAT, F_FRAMING)

# ── combination relations ───────────────────────────────────────────────────

GOOD_WITH = "GOOD_WITH"
BAD_WITH = "BAD_WITH"
REQUIRES = "REQUIRES"
MUST_PRECEDE = "MUST_PRECEDE"
MUST_FOLLOW = "MUST_FOLLOW"
CAN_OVERLAP = "CAN_OVERLAP"
MUST_SERIALIZE = "MUST_SERIALIZE"


@dataclass(frozen=True)
class DurationEnvelope:
    """What durations are allowed, what looks best, and who says so."""
    hard_min_us: int
    preferred_min_us: int
    preferred_max_us: int
    hard_max_us: int
    provenance: str = DESIGN_ESTIMATE
    swept_points_us: tuple[int, ...] = ()      # what a canary actually rendered
    quantisation_us: int | None = None         # measured delivery grid
    delivery_bias_us: int = 0                  # measured request -> delivered offset
    calibration: Any = None                    # the configuration it was measured under
    aesthetic_reviewed: bool = False           # has anybody actually looked
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.provenance not in PROVENANCE:
            raise ValueError(f"unknown timing provenance {self.provenance!r}")
        if not (self.hard_min_us <= self.preferred_min_us
                <= self.preferred_max_us <= self.hard_max_us):
            raise ValueError("envelope bounds must nest: hard <= preferred "
                             "<= preferred <= hard")
        if self.provenance in (SYNTHETIC_TEST, RUNTIME_MEASURED) and not self.swept_points_us:
            raise ValueError(f"{self.provenance} claims measurement but no "
                             f"durations were swept")

    @property
    def solver_trusted(self) -> bool:
        return PROVENANCE_RANK[self.provenance] >= PROVENANCE_RANK[SOLVER_TRUSTED_FROM]

    @property
    def preferred_us(self) -> int:
        return (self.preferred_min_us + self.preferred_max_us) // 2

    def request_for(self, wanted_us: int, *, calibration: Any = None) -> int:
        """What to ASK the pipeline for so it delivers `wanted_us`.

        A freeze comes back one frame long every time; asking for the number
        you want and accepting what arrives is how a composition drifts. The
        compensation is refused when the render configuration is not the one
        it was measured under, because a 60 fps frame is not a 120 fps frame.
        """
        if self.delivery_bias_us and self.calibration is not None:
            target = calibration or self.calibration
            if not self.calibration.applies_to(target):
                raise StaleCalibration(
                    f"the {self.delivery_bias_us} us compensation was measured on "
                    f"{self.calibration.key} and does not apply to {target.key}; "
                    f"re-measure before trusting it")
        return wanted_us - self.delivery_bias_us

    @property
    def desired_vs_requested(self) -> str:
        """The three durations that must never be conflated."""
        return ("desired = what the choreography wants; requested = what the "
                "pipeline is asked for; delivered = what came back")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(preferred_us=self.preferred_us, solver_trusted=self.solver_trusted)
        return d


@dataclass(frozen=True)
class TemporalEffectTemplate:
    """One effect, as the solver may actually use it."""
    id: str
    family: str
    corpus_entries: tuple[str, ...]        # what creative ideas this serves
    operator: str                          # a temporal_operators kind
    envelope: DurationEnvelope
    temporal_power: str
    capability: str = "DESIGNABLE"
    lane: str = ""
    purpose: str = ""
    peak_ratio: float = 0.5
    anchor_kind: str = "HERO"
    music_targets: tuple[str, ...] = ()
    rate_min: Fraction | None = None
    rate_max: Fraction | None = None
    rate_preferred: Fraction | None = None
    repeats_min: int | None = None
    repeats_max: int | None = None
    dwell_min_us: int | None = None
    dwell_max_us: int | None = None
    evidence_required: tuple[str, ...] = ()
    requirements: tuple[str, ...] = ()     # camera / model / bsp / depth needs
    good_with: tuple[str, ...] = ()
    bad_with: tuple[str, ...] = ()
    must_precede: tuple[str, ...] = ()
    must_follow: tuple[str, ...] = ()
    can_overlap: bool = False
    render_cost: str = "MODERATE"
    needs_canary: bool = True
    notes: str = ""

    def __post_init__(self) -> None:
        if self.family not in FAMILIES:
            raise ValueError(f"{self.id}: unknown family {self.family!r}")
        if self.operator not in t.KINDS:
            raise ValueError(f"{self.id}: unknown operator {self.operator!r}")
        if self.temporal_power not in POWERS:
            raise ValueError(f"{self.id}: unknown temporal power")
        ceiling = POWER_CEILING_US[self.temporal_power]
        if self.envelope.hard_max_us > ceiling:
            raise ValueError(
                f"{self.id}: {self.temporal_power} tops out at {ceiling} us but "
                f"the envelope reaches {self.envelope.hard_max_us}. Either the "
                f"power class or the envelope is wrong.")

    @property
    def sign(self) -> int:
        return (-1 if self.operator in t.SUBTRACTIVE
                else 0 if self.operator in t.CONCURRENT else 1)

    @property
    def measured(self) -> bool:
        return self.envelope.solver_trusted

    def nominal_source_us(self) -> int:
        """A representative source span, for planning before a real moment is
        chosen. Sized so the preferred duration sits at the preferred rate --
        the point is to ask "how long could this be", not to pretend a
        particular clip exists."""
        rate = self.rate_preferred or self.rate_max or Fraction(1, 1)
        return max(int(self.envelope.preferred_us * float(rate)), MS)

    def operator_for(self, label: str | None = None, *,
                     src_in_us: int | None = None, src_out_us: int | None = None,
                     ) -> t.TemporalOperator:
        """The solver-facing operator, with THIS template's real envelope.

        A source-consuming operator with no source given gets a nominal one,
        so elasticity and combination questions can be asked before a moment
        has been chosen.
        """
        e = self.envelope
        if self.operator in t.SOURCE_CONSUMING and self.operator != t.TRIM:
            if src_in_us is None or src_out_us is None:
                src_in_us, src_out_us = 0, self.nominal_source_us()
        dwell_lo = self.dwell_min_us
        dwell_hi = self.dwell_max_us
        if self.operator == t.STUTTER and dwell_lo is None:
            dwell_lo, dwell_hi = 2 * 16_667, 8 * 16_667
        return t.TemporalOperator(
            kind=self.operator, label=label or self.id,
            hard_min_us=e.hard_min_us, hard_max_us=e.hard_max_us,
            preferred_min_us=e.preferred_min_us, preferred_max_us=e.preferred_max_us,
            src_in_us=src_in_us, src_out_us=src_out_us,
            rate_min=self.rate_min, rate_max=self.rate_max,
            rate_preferred=self.rate_preferred,
            repeats_min=self.repeats_min, repeats_max=self.repeats_max,
            dwell_min_us=dwell_lo, dwell_max_us=dwell_hi,
            peak_ratio=self.peak_ratio, anchor_kind=self.anchor_kind,
            capability=self.capability, purpose=self.purpose,
            notes=f"{self.id} [{e.provenance}] {self.notes}")

    def feasibility(self, duration_us: int) -> str:
        """Three different questions, kept apart."""
        if not (self.envelope.hard_min_us <= duration_us <= self.envelope.hard_max_us):
            return "INFEASIBLE"
        if self.envelope.provenance == HUMAN_APPROVED and \
                self.envelope.preferred_min_us <= duration_us <= self.envelope.preferred_max_us:
            return DIRECTOR_APPROVED
        if self.envelope.solver_trusted:
            return VISUALLY_FEASIBLE
        return MATHEMATICALLY_FEASIBLE

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["envelope"] = self.envelope.to_dict()
        for k in ("rate_min", "rate_max", "rate_preferred"):
            if d[k] is not None:
                d[k] = str(d[k])
        d.update(sign=self.sign, measured=self.measured)
        return d


class StaleCalibration(RuntimeError):
    """Raised when a compensation is used outside the configuration that
    produced it."""


def _env(hmin, pmin, pmax, hmax, prov=DESIGN_ESTIMATE, why="", swept=(),
         quant=None, bias=0, cal=None, **kw):
    return DurationEnvelope(hmin * MS, pmin * MS, pmax * MS, hmax * MS, prov,
                            tuple(v * MS for v in swept), quant, bias,
                            cal if cal is not None else
                            (CALIBRATION_60_X264 if prov in
                             (SYNTHETIC_TEST, RUNTIME_MEASURED) else None),
                            rationale=why, **kw)


# ── delivery calibration ────────────────────────────────────────────────────
# A measured compensation belongs to the pipeline that produced it. The
# +16.6 ms freeze offset is exactly one frame at 60 fps; at 120 fps it would
# be wrong, and a different encoder or filter graph could change it again.
# So calibration is keyed, and a template that carries one records which
# configuration it was measured under.

@dataclass(frozen=True)
class DeliveryCalibration:
    """What a given render configuration actually does to a request."""
    fps: int
    encoder: str
    pipeline: str                 # which script/graph produced the measurement
    timebase: str = "AVTB"
    measured_on: str = ""
    notes: str = ""

    @property
    def frame_us(self) -> int:
        return int(round(1_000_000 / self.fps))

    @property
    def key(self) -> str:
        return (f"{self.fps}fps/{self.encoder}/{self.timebase}/{self.pipeline}")

    def applies_to(self, other: "DeliveryCalibration") -> bool:
        """A calibration is only valid for the configuration it came from."""
        return (self.fps == other.fps and self.encoder == other.encoder
                and self.timebase == other.timebase)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(frame_us=self.frame_us, key=self.key)
        return d


CALIBRATION_60_X264 = DeliveryCalibration(
    fps=60, encoder="libx264", pipeline="scratchpad/effect_canaries.py",
    timebase="AVTB", measured_on="2026-09-03",
    notes="freeze returns one frame long; overlap exact; rates 3/10, 2/5 and "
          "1/1 land exactly while 1/2 and 55/100 lose a frame")

# Measured under CALIBRATION_60_X264. One frame is 16 667 us there.
FRAME_US = CALIBRATION_60_X264.frame_us
FREEZE_SWEEP = (50, 100, 133, 150, 200, 250, 300, 400, 500, 650, 900)
STUTTER_SWEEP = (33, 45, 60, 90, 110, 120, 150, 170, 180, 230)
RATE_SWEEP_EXACT = ("3/10", "2/5", "1/1")     # land on the frame grid exactly
OVERLAP_SWEEP = (50, 100, 150, 200, 250, 300, 400, 500)
PIP_SWEEP = (600, 900, 1200, 1800, 2400)
REWIND_SWEEP = (300, 600, 900, 1200, 1800, 2400)   # delivered cost, not slice
# A rewind runs the slice backwards and then forwards again, so it costs
# TWICE the slice it rewinds. Measured exact at every point.
REWIND_COST_FACTOR = 2


_T = TemporalEffectTemplate

# ── the library ─────────────────────────────────────────────────────────────
# Every envelope below is a DESIGN_ESTIMATE unless a canary has swept it.
# The rationale says what the number is reasoned from.

TEMPLATES: tuple[TemporalEffectTemplate, ...] = (

    # ── family 1: temporal cutting ──────────────────────────────────────────
    _T("FREEZE_HOLD", F_CUTTING, (), t.FREEZE,
       _env(100,200,500,900, SYNTHETIC_TEST,
       why="swept 50-900 ms: delivery is exact to the frame but always one frame long, so the request is compensated. The aesthetic range is still the director's to set",
       swept=FREEZE_SWEEP, quant=FRAME_US, bias=FRAME_US),
       SMALL, "PROVEN_RUNTIME", "TIME", "BUILD_TENSION", peak_ratio=1.0,
       anchor_kind="FREEZE_RELEASE", music_targets=("BEAT", "NEGATIVE_SPACE", "PRE_DROP"),
       good_with=("WORLD_STRIP", "ENEMY_REVEAL_STEP", "DAMAGE_LEDGER_TICK"),
       bad_with=("MOSAIC_TILE_STEP",), render_cost="CHEAP"),
    _T("FRAME_REPEAT", F_CUTTING, ("FRAME_ECHO",), t.REPEAT,
       _env(33,50,110,200, SYNTHETIC_TEST,
       why='swept 33-230 ms holds: a 33 ms hold survives (two frames); shorter cannot exist at 60 fps',
       swept=STUTTER_SWEEP, quant=FRAME_US, bias=0),
       MICRO, "PROTOTYPE", "FX", "MUSICAL_PUNCTUATION", peak_ratio=0.0,
       anchor_kind="STUTTER_ATTACK", music_targets=("SUBDIVISION", "GESTURE"),
       render_cost="CHEAP"),
    _T("MICRO_REWIND", F_CUTTING, (), t.INSERT,
       _env(120,200,450,800, SYNTHETIC_TEST,
       why='shares the reverse primitive: exact delivery, and twice the slice',
       swept=REWIND_SWEEP, quant=FRAME_US, bias=0),
       SMALL, "PROTOTYPE", "TIME", "MUSICAL_PUNCTUATION", peak_ratio=0.0,
       anchor_kind="TRANSITION_HANDOFF", music_targets=("BEAT", "GESTURE")),
    _T("TIME_ECHO", F_CUTTING, ("FRAME_ECHO", "MULTI_EXPOSURE"), t.REPEAT,
       _env(60, 100, 300, 600, why="offset repeats need to be distinguishable "
            "from motion blur"),
       SMALL, "PROTOTYPE", "FX", "REVEAL_SKILL", peak_ratio=0.5,
       anchor_kind="STUTTER_ATTACK", can_overlap=True),
    _T("FREEZE_DECOMPOSITION", F_CUTTING, ("TEMPORAL_DECOMPOSITION",), t.FREEZE,
       _env(400, 700, 1_600, 2_400, why="taking a frozen instant apart needs "
            "time to read; it is a set piece, not a punctuation"),
       MEDIUM, "DESIGNABLE", "FX", "REVEAL_SKILL", peak_ratio=0.6,
       anchor_kind="MORPH_PEAK", music_targets=("RISE", "NEGATIVE_SPACE")),

    # ── family 2: retime ────────────────────────────────────────────────────
    _T("SLOW_MOTION", F_RETIME, ("SPEED_SCALED_SLOWMO", "VELOCITY_SIGNATURE"), t.RETIME,
       _env(300,800,4_000,8_000, SYNTHETIC_TEST,
       why='rate sweep 0.20-1.0: 3/10, 2/5 and 1/1 land exactly; 1/4, 1/2, 55/100 and 7/10 lose one frame and deliver a slightly faster effective rate',
       swept=(300, 800, 4000, 8000), quant=FRAME_US, bias=0),
       LARGE, "PROVEN_RUNTIME", "TIME", "REVEAL_SKILL", peak_ratio=0.5,
       anchor_kind="HERO", rate_min=Fraction(1, 5), rate_max=Fraction(1, 1),
       rate_preferred=Fraction(2, 5),
       music_targets=("P_CENTER", "DROP", "PHRASE"),
       good_with=("FREEZE_HOLD", "SIDE_REPLAY"), render_cost="CHEAP",
       notes="0.20x is the floor before motion stops reading as motion"),
    _T("SPEED_RAMP", F_RETIME, (), t.RETIME,
       _env(200, 400, 1_200, 2_400, why="a ramp needs long enough to feel like "
            "a change of pace rather than a glitch"),
       MEDIUM, "PROVEN_RUNTIME", "TIME", "BUILD_TENSION", peak_ratio=1.0,
       anchor_kind="CAMERA_CUT", rate_min=Fraction(1, 4), rate_max=Fraction(2, 1),
       rate_preferred=Fraction(1, 1), music_targets=("RISE", "BEAT")),

    # ── family 3: replay ────────────────────────────────────────────────────
    _T("SIDE_REPLAY", F_REPLAY, ("PROJECTILE_CINEMATIC",), t.REPLAY,
       _env(1_200, 2_000, 3_200, 5_000, why="the original skill plays first; a "
            "replay under ~1.2 s reads as a stutter, over ~3.5 s it outstays"),
       LARGE, "PROTOTYPE", "CAMERA", "REVEAL_SKILL", peak_ratio=0.62,
       anchor_kind="HERO", rate_min=Fraction(3, 10), rate_max=Fraction(55, 100),
       rate_preferred=Fraction(2, 5), music_targets=("P_CENTER", "DROP"),
       must_follow=("FREEZE_HOLD",), good_with=("MODEL_MORPH", "FREEZE_HOLD"),
       evidence_required=("frag",), requirements=("clean_camera",)),
    _T("PROJECTILE_REPLAY", F_REPLAY,
       ("PROJECTILE_CINEMATIC", "RECONSTRUCTED_PROJECTILE_CINEMATIC",
        "GRENADE_ARC_FOLLOW"), t.REPLAY,
       _env(800, 1_400, 3_000, 5_000, why="a projectile replay is bounded by "
            "the flight it actually has"),
       LARGE, "PROTOTYPE", "CAMERA", "REVEAL_SKILL", peak_ratio=0.85,
       anchor_kind="HERO", rate_min=Fraction(1, 4), rate_max=Fraction(1, 1),
       rate_preferred=Fraction(2, 5),
       evidence_required=("projectile_path",), requirements=("camera_path",)),
    _T("ENEMY_POV_INSERT", F_REPLAY,
       ("ENEMY_POV_REAL", "ENEMY_POV_RECONSTRUCTED", "ENEMY_POV_SYNTHETIC"), t.INSERT,
       _env(600,1_000,2_400,4_000, SYNTHETIC_TEST,
       why='swept 600-2400 ms as a cut: adds exactly its own duration at every point, the counterpart to the PIP measurement',
       swept=PIP_SWEEP, quant=FRAME_US, bias=0),
       LARGE, "DESIGNABLE", "CAMERA", "REVEAL_SKILL", peak_ratio=0.7,
       anchor_kind="HERO", evidence_required=("enemy_state",),
       notes="SEQUENTIAL: this adds its whole duration. The PIP form does not."),

    # ── family 4: transition overlap ────────────────────────────────────────
    _T("MATCH_CUT_OVERLAP", F_TRANSITION, ("IDENTITY_MATCH_CUT",), t.OVERLAP,
       _env(0,100,300,500, SYNTHETIC_TEST,
       why='swept 50-500 ms: the overlap removes exactly the time requested, 0.0 ms error at every point',
       swept=OVERLAP_SWEEP, quant=FRAME_US, bias=0),
       SMALL, "PROTOTYPE", "TRANSITION", "TRANSITION", peak_ratio=0.5,
       anchor_kind="TRANSITION_HANDOFF", music_targets=("BEAT", "PHRASE"),
       can_overlap=True, render_cost="CHEAP",
       evidence_required=("pose",), notes="removes net sequence time"),
    _T("DEATH_EXPLOSION_MATCH", F_TRANSITION, ("DEATH_AS_TRANSITION",), t.OVERLAP,
       _env(80,150,350,600, SYNTHETIC_TEST,
       why='shares the crossfade primitive swept 50-500 ms: exact net removal',
       swept=OVERLAP_SWEEP, quant=FRAME_US, bias=0),
       SMALL, "PROVEN_RUNTIME", "TRANSITION", "TRANSITION", peak_ratio=0.4,
       anchor_kind="TRANSITION_HANDOFF", music_targets=("TRANSIENT", "BEAT"),
       can_overlap=True, evidence_required=("death",), render_cost="CHEAP"),
    _T("ROCKET_FLYBY_BRIDGE", F_TRANSITION, ("ROCKET_FLYBY_AUDIO_ANCHOR",), t.OVERLAP,
       _env(150, 350, 650, 900, why="the whoosh needs its approach and its "
            "departure; the handoff is the closest pass"),
       MEDIUM, "PROTOTYPE", "TRANSITION", "TRANSITION", peak_ratio=0.5,
       anchor_kind="TRANSITION_HANDOFF",
       music_targets=("RISE", "TRANSIENT", "PHRASE"),
       can_overlap=True, evidence_required=("projectile_path",),
       notes="can remove ~350-650 ms of net sequence time"),
    _T("MOVEMENT_MATCH_OVERLAP", F_TRANSITION,
       ("STRAFE_JUMP_AUDIO_MATCH", "MOVEMENT_TRANSITION", "TELEPORTER_WORLD_PASS"),
       t.OVERLAP,
       _env(60,120,300,500, SYNTHETIC_TEST,
       why='shares the crossfade primitive swept 50-500 ms: exact net removal',
       swept=OVERLAP_SWEEP, quant=FRAME_US, bias=0),
       SMALL, "PROTOTYPE", "TRANSITION", "TRANSITION", peak_ratio=0.5,
       anchor_kind="TRANSITION_HANDOFF", music_targets=("BEAT", "SUBDIVISION"),
       can_overlap=True, evidence_required=("movement",), render_cost="CHEAP"),
    _T("WORLD_MORPH_BRIDGE", F_TRANSITION,
       ("WORLD_MORPH_TO_NEXT_SCENE", "PROJECTILE_MORPH_BRIDGE", "FLY_INTO_OBJECT"),
       t.OVERLAP,
       _env(300, 600, 1_400, 2_200, why="a world becoming another world is a "
            "set piece and needs room to be understood"),
       MEDIUM, "REQUIRES_NEW_TECH", "TRANSITION", "TRANSITION", peak_ratio=0.5,
       anchor_kind="MORPH_PEAK", music_targets=("RISE", "DROP"),
       can_overlap=True, render_cost="R&D"),

    # ── family 5: rhythmic response ─────────────────────────────────────────
    _T("RHYTHMIC_IMAGE_STUTTER", F_RHYTHM, ("RHYTHMIC_IMAGE_STUTTER",), t.STUTTER,
       _env(120,200,900,2_000, SYNTHETIC_TEST,
       why="swept equal and unequal figures: 110/230/170 ms delivered within 6.7 ms, so a gesture's own spacing survives and is never forced onto an even grid",
       swept=STUTTER_SWEEP, quant=FRAME_US, bias=0),
       MEDIUM, "PROTOTYPE", "FX", "MUSICAL_PUNCTUATION", peak_ratio=0.0,
       anchor_kind="STUTTER_ATTACK", dwell_min_us=33 * MS, dwell_max_us=200 * MS,
       repeats_min=2, repeats_max=12,
       music_targets=("GESTURE", "SUBDIVISION"), render_cost="CHEAP",
       good_with=("MODEL_PULSE", "MATERIAL_FLASH"),
       bad_with=("MOSAIC_TILE_STEP",),
       notes="duration is derived from the gesture, not chosen"),
    _T("MOSAIC_TILE_STEP", F_RHYTHM, ("MOSAIC_TILE_INTERPOLATION",), t.STUTTER,
       _env(200, 400, 1_200, 2_400, why="tiles catching up independently need "
            "long enough for the eye to find the pattern"),
       MEDIUM, "DESIGNABLE", "FX", "MUSICAL_PUNCTUATION", peak_ratio=0.5,
       anchor_kind="STUTTER_ATTACK", dwell_min_us=60 * MS, dwell_max_us=400 * MS,
       repeats_min=2, repeats_max=16,
       music_targets=("GESTURE",), render_cost="EXPENSIVE",
       bad_with=("RHYTHMIC_IMAGE_STUTTER", "MODEL_MORPH", "WORLD_STRIP")),
    _T("MODEL_PULSE", F_RHYTHM, (), t.REPLACE,
       _env(40, 60, 180, 300, why="a pulse on the model reads at a frame or two "
            "either side of the attack"),
       MICRO, "DESIGNABLE", "MODEL_SKIN", "MUSICAL_PUNCTUATION", peak_ratio=0.3,
       anchor_kind="MATERIAL_FLASH", music_targets=("SUBDIVISION", "GESTURE"),
       can_overlap=True, render_cost="MODERATE",
       notes="concurrent: costs no sequence time"),
    _T("MATERIAL_FLASH", F_RHYTHM, ("MUSIC_REACTIVE_MATERIAL",), t.REPLACE,
       _env(33, 50, 160, 300, why="shorter than a pulse; it is a hit, not a state"),
       MICRO, "DESIGNABLE", "MATERIAL_TEXTURE", "MUSICAL_PUNCTUATION",
       peak_ratio=0.2, anchor_kind="MATERIAL_FLASH",
       music_targets=("SUBDIVISION", "TRANSIENT"), can_overlap=True),
    _T("CAMERA_JOLT", F_RHYTHM, (), t.REPLACE,
       _env(40, 80, 220, 400, why="a jolt is felt, not seen; too long and it is "
            "a camera move"),
       SMALL, "PROTOTYPE", "CAMERA", "MUSICAL_PUNCTUATION", peak_ratio=0.25,
       anchor_kind="CAMERA_CUT", can_overlap=True, render_cost="CHEAP"),
    _T("ENEMY_REVEAL_STEP", F_RHYTHM, ("ONE_V_X_ENEMY_REVEAL",), t.INSERT,
       _env(120, 250, 600, 1_000, why="one enemy appearing per attack; each "
            "needs to land before the next"),
       SMALL, "DESIGNABLE", "FX", "SHOW_THREAT", peak_ratio=0.35,
       anchor_kind="STUTTER_ATTACK", music_targets=("GESTURE", "SUBDIVISION"),
       evidence_required=("alive_state",), good_with=("WORLD_STRIP", "FREEZE_HOLD"),
       render_cost="EXPENSIVE"),

    # ── family 6: world and material ────────────────────────────────────────
    _T("WORLD_STRIP", F_WORLD, ("WORLD_STRIP",), t.FREEZE,
       _env(250, 500, 1_200, 2_000, why="under ~350 ms the geometry vanishing "
            "is not perceived; past ~1.2 s it wants a musical swell"),
       MEDIUM, "DESIGNABLE", "WORLD", "SHOW_THREAT", peak_ratio=0.7,
       anchor_kind="MORPH_PEAK", music_targets=("RISE", "NEGATIVE_SPACE"),
       good_with=("ENEMY_REVEAL_STEP", "ENEMY_COUNT_TICK", "FREEZE_HOLD"),
       bad_with=("MOSAIC_TILE_STEP", "MODEL_MORPH"),
       must_precede=("WORLD_REBUILD",), render_cost="EXPENSIVE"),
    _T("WORLD_REBUILD", F_WORLD, ("WORLD_REBUILD",), t.INSERT,
       _env(200, 350, 900, 1_600, why="coming back should be faster than going "
            "away; it usually lands on the drop"),
       MEDIUM, "DESIGNABLE", "WORLD", "TRANSITION", peak_ratio=1.0,
       anchor_kind="MORPH_PEAK", music_targets=("DROP", "BEAT"),
       must_follow=("WORLD_STRIP",), render_cost="EXPENSIVE"),
    _T("WALL_XRAY", F_WORLD, ("WALL_XRAY_REBUILD",), t.INSERT,
       _env(400, 700, 1_800, 3_000, why="the viewer has to find the hidden "
            "geometry, follow the line, and understand it"),
       MEDIUM, "DESIGNABLE", "WORLD", "EXPLAIN_GEOMETRY", peak_ratio=0.5,
       anchor_kind="MORPH_PEAK", music_targets=("NEGATIVE_SPACE", "RISE"),
       evidence_required=("map_geometry",), requirements=("bsp", "depth"),
       good_with=("FREEZE_HOLD", "PROJECTILE_REPLAY"), render_cost="EXPENSIVE"),
    _T("MAP_CONSTRUCTION", F_WORLD, ("MAP_CONSTRUCTION_INTRO",), t.SYNTHETIC_INSERT,
       _env(2_000, 4_000, 12_000, 20_000, why="wireframe to geometry to texture "
            "to detail is an opening title, not an effect"),
       SEQUENCE, "DESIGNABLE", "WORLD", "EXPLAIN_GEOMETRY", peak_ratio=0.8,
       anchor_kind="MORPH_PEAK", music_targets=("PHRASE", "RISE"),
       requirements=("bsp",), render_cost="R&D"),
    _T("LOW_HP_WORLD", F_WORLD, ("LOW_HP_REACTIVE_WORLD",), t.REPLACE,
       _env(200, 500, 2_000, 2_500, why="a state, not an event: it runs under "
            "whatever else is happening"),
       MEDIUM, "DESIGNABLE", "MATERIAL_TEXTURE", "BUILD_TENSION", peak_ratio=0.5,
       anchor_kind="MATERIAL_FLASH", can_overlap=True,
       evidence_required=("player_health",), render_cost="MODERATE"),
    _T("TEXTURE_TEXT_REVEAL", F_WORLD,
       ("TEXTURE_COUNTDOWN_TEXT", "DIEGETIC_SCOREBOARD", "PIP_WORLD_SURFACE"),
       t.REPLACE,
       _env(300, 600, 2_000, 2_500, why="text on a wall has to be found and "
            "read; that is about a second at minimum"),
       MEDIUM, "DESIGNABLE", "MATERIAL_TEXTURE", "EXPLAIN_CA", peak_ratio=0.4,
       anchor_kind="MATERIAL_FLASH", can_overlap=True,
       evidence_required=("score_state",), render_cost="EXPENSIVE"),

    # ── family 7: model and skin ────────────────────────────────────────────
    _T("MODEL_MORPH", F_MODEL,
       ("TEAM_IDENTITY_MORPH", "POST_WIN_TEAMMATE_MODEL_REVEAL"), t.SYNTHETIC_INSERT,
       _env(180, 250, 700, 1_200, why="180 ms is abrupt, beyond ~700 ms it "
            "drags unless a musical rise is carrying it"),
       MEDIUM, "DESIGNABLE", "MODEL_SKIN", "IDENTITY", peak_ratio=0.65,
       anchor_kind="MORPH_PEAK", music_targets=("RISE", "PHRASE"),
       evidence_required=("team_state",), bad_with=("MOSAIC_TILE_STEP", "WORLD_STRIP"),
       render_cost="EXPENSIVE"),
    _T("PLAYER_FREEZE_POSE", F_MODEL, ("DANGER_CROSS_SIGN",), t.SYNTHETIC_INSERT,
       _env(300, 500, 1_200, 2_000, why="a gag needs to be seen and understood"),
       MEDIUM, "CREATIVE_SEED", "ANIMATION", "COMEDIC_RELEASE", peak_ratio=0.5,
       anchor_kind="MORPH_PEAK", requirements=("custom_animation",),
       render_cost="R&D"),
    _T("GRENADE_GAG", F_MODEL, ("GRENADE_FOOTBALL_GAG",), t.SYNTHETIC_INSERT,
       _env(600, 1_000, 2_200, 2_500, why="chest control and a headbutt is a "
            "little piece of theatre"),
       MEDIUM, "CREATIVE_SEED", "ANIMATION", "COMEDIC_RELEASE", peak_ratio=0.6,
       anchor_kind="MORPH_PEAK", requirements=("custom_animation",),
       render_cost="R&D"),

    # ── family 8: information ───────────────────────────────────────────────
    _T("DAMAGE_LEDGER_TICK", F_INFORMATION, ("DAMAGE_LEDGER_OVER_TARGET",), t.REPLACE,
       _env(60, 120, 400, 700, why="a number changing reads in a few frames; "
            "holding it longer is a different decision"),
       SMALL, "DESIGNABLE", "INFORMATION", "SHOW_DAMAGE", peak_ratio=0.2,
       anchor_kind="MATERIAL_FLASH", music_targets=("SUBDIVISION", "BEAT"),
       can_overlap=True, evidence_required=("damage_ledger",)),
    _T("ROUND_DAMAGE_TOTAL", F_INFORMATION, ("ROUND_DAMAGE_COUNTER",), t.REPLACE,
       _env(400, 700, 2_000, 2_500, why="a total is read once, not tracked"),
       MEDIUM, "DESIGNABLE", "INFORMATION", "SHOW_DAMAGE", peak_ratio=0.3,
       anchor_kind="MATERIAL_FLASH", can_overlap=True,
       evidence_required=("damage_ledger", "round_context")),
    _T("ENEMY_COUNT_TICK", F_INFORMATION, ("ONE_V_X_COUNT_DISPLAY",), t.REPLACE,
       _env(80, 150, 500, 800, why="the decrement must land on the death that "
            "caused it"),
       SMALL, "PROTOTYPE", "INFORMATION", "SHOW_THREAT", peak_ratio=0.15,
       anchor_kind="MATERIAL_FLASH", can_overlap=True,
       evidence_required=("alive_state",), good_with=("ENEMY_REVEAL_STEP",)),
    _T("RAIL_COOLDOWN_BAR", F_INFORMATION, ("RAIL_COOLDOWN_TELEGRAPH",), t.REPLACE,
       _env(300, 600, 1_800, 2_500, why="the cooldown itself is 1.5 s; the "
            "telegraph should track it"),
       MEDIUM, "DESIGNABLE", "INFORMATION", "EXPLAIN_CA", peak_ratio=1.0,
       anchor_kind="MATERIAL_FLASH", can_overlap=True,
       evidence_required=("weapon_state",)),
    _T("CA_EXPLAINER_CARD", F_INFORMATION, ("CA_EXPLAINER", "SEMANTIC_COMPRESSION"),
       t.SYNTHETIC_INSERT,
       _env(1_200, 2_000, 5_000, 8_000, why="teaching a rule needs a phrase, "
            "not a beat"),
       LARGE, "DESIGNABLE", "INFORMATION", "EXPLAIN_CA", peak_ratio=0.5,
       anchor_kind="MORPH_PEAK", music_targets=("PHRASE", "NEGATIVE_SPACE"),
       evidence_required=("round_context",)),
    _T("SHAFT_STAT_REVEAL", F_INFORMATION, ("SHAFT_DUEL_STAT",), t.REPLACE,
       _env(400, 800, 2_000, 2_500, why="a percentage climbing is a small story"),
       MEDIUM, "CREATIVE_SEED", "INFORMATION", "REVEAL_SKILL", peak_ratio=0.8,
       anchor_kind="MATERIAL_FLASH", can_overlap=True,
       evidence_required=("lg_engagement",), render_cost="R&D"),

    # ── family 9: movement ──────────────────────────────────────────────────
    _T("MOVEMENT_ACCENT", F_MOVEMENT,
       ("MICRO_ACTION_ACCENT", "VELOCITY_SIGNATURE"), t.REPLACE,
       _env(40, 80, 200, 300, why="a jump or a pickup is a tick, not a moment"),
       MICRO, "PROVEN_RUNTIME", "FX", "MUSICAL_PUNCTUATION", peak_ratio=0.2,
       anchor_kind="MATERIAL_FLASH", music_targets=("SUBDIVISION",),
       can_overlap=True, evidence_required=("movement",), render_cost="CHEAP"),
    _T("HIGH_SPEED_HOLD", F_MOVEMENT, ("SPEED_SCALED_SLOWMO",), t.RETIME,
       _env(500, 900, 2_400, 4_000, why="speed is what widens the slow-motion "
            "envelope; the music still picks the rate inside it"),
       LARGE, "PROVEN_RUNTIME", "TIME", "REVEAL_SKILL", peak_ratio=0.5,
       anchor_kind="HERO", rate_min=Fraction(1, 4), rate_max=Fraction(1, 1),
       rate_preferred=Fraction(1, 2), evidence_required=("movement",)),

    # ── family 10: projectiles ──────────────────────────────────────────────
    _T("PROJECTILE_FOLLOW", F_PROJECTILE,
       ("PROJECTILE_CINEMATIC", "RECONSTRUCTED_PROJECTILE_CINEMATIC"), t.REPLAY,
       _env(700, 1_200, 3_000, 5_000, why="bounded by the flight; a rocket at "
            "999 u/s crosses most rooms in under a second"),
       LARGE, "PROTOTYPE", "CAMERA", "REVEAL_SKILL", peak_ratio=0.9,
       anchor_kind="HERO", rate_min=Fraction(1, 5), rate_max=Fraction(1, 1),
       rate_preferred=Fraction(1, 3), evidence_required=("projectile_path",),
       requirements=("camera_path",)),
    _T("GRENADE_ARC", F_PROJECTILE, ("GRENADE_ARC_FOLLOW",), t.REPLAY,
       _env(900, 1_500, 3_500, 5_000, why="a grenade's whole life is 2.5 s; the "
            "bounces are the story"),
       LARGE, "PROTOTYPE", "CAMERA", "REVEAL_SKILL", peak_ratio=0.85,
       anchor_kind="HERO", rate_min=Fraction(1, 4), rate_max=Fraction(1, 1),
       rate_preferred=Fraction(2, 5), evidence_required=("projectile_path",)),

    # ── family 11: death ────────────────────────────────────────────────────
    _T("DEATH_FREEZE", F_DEATH, ("HERO_THEN_DEATH_REWIND",), t.FREEZE,
       _env(120, 200, 500, 800, why="long enough to register the death, short "
            "enough that it does not become the point"),
       SMALL, "PROVEN_RUNTIME", "TIME", "TRANSITION", peak_ratio=1.0,
       anchor_kind="FREEZE_RELEASE", evidence_required=("death",),
       render_cost="CHEAP"),
    _T("DEATH_FLASH_MONTAGE", F_DEATH, ("DEATH_MOTIF_BANK",), t.REPEAT,
       _env(200,320,900,1_600, SYNTHETIC_TEST,
       why='shares the frame-repeat primitive; three or four frames per flash is 50-67 ms, which the sweep delivers exactly',
       swept=STUTTER_SWEEP, quant=FRAME_US, bias=0),
       MEDIUM, "PROVEN_RUNTIME", "TRANSITION", "MUSICAL_PUNCTUATION",
       peak_ratio=0.5, anchor_kind="STUTTER_ATTACK", dwell_min_us=50 * MS, dwell_max_us=200 * MS,
       repeats_min=3, repeats_max=12,
       music_targets=("SUBDIVISION", "GESTURE"),
       evidence_required=("death", "motif_group"), render_cost="CHEAP"),
    _T("DEATH_REWIND", F_DEATH, ("HERO_THEN_DEATH_REWIND",), t.INSERT,
       _env(300,450,1_100,2_000, SYNTHETIC_TEST,
       why='swept 150-1200 ms slices: a rewind runs the slice backwards then forwards, so it costs exactly twice the slice. The envelope here is the delivered cost, not the slice length',
       swept=REWIND_SWEEP, quant=FRAME_US, bias=0),
       MEDIUM, "PROTOTYPE", "TIME", "TRANSITION", peak_ratio=1.0,
       anchor_kind="TRANSITION_HANDOFF", music_targets=("PHRASE", "BEAT"),
       must_precede=("SIDE_REPLAY",), evidence_required=("death",)),

    # ── family 12: team and 1vX ─────────────────────────────────────────────
    _T("ROUND_WIN_RELEASE", F_TEAM,
       ("ROUND_WIN_PAYOFF", "POST_WIN_TEAMMATE_MODEL_REVEAL",
        "ASSISTED_ROUND_FINISH", "COMMIT_1VX"), t.INSERT,
       _env(800, 1_400, 3_500, 6_000, why="a payoff needs room to be a payoff"),
       LARGE, "PROVEN_RUNTIME", "NARRATIVE", "ROUND_PAYOFF", peak_ratio=0.3,
       anchor_kind="MORPH_PEAK", music_targets=("DROP", "PHRASE"),
       evidence_required=("round_result",),
       notes="refused unless the round was actually won"),
    _T("NOPE_BEAT", F_TEAM, ("NOPE_RETREAT",), t.INSERT,
       _env(150, 250, 700, 1_200, why="a beat of hesitation; any longer and the "
            "joke explains itself"),
       MEDIUM, "DESIGNABLE", "FX", "COMEDIC_RELEASE", peak_ratio=0.4,
       anchor_kind="MATERIAL_FLASH", evidence_required=("alive_state",),
       render_cost="CHEAP"),

    # ── family 13: POV and PIP ──────────────────────────────────────────────
    _T("POV_PIP", F_POV, ("ENEMY_POV_RECONSTRUCTED", "PIP_WORLD_SURFACE",
                          "DAMAGE_CHASE_ASSIST"), t.REPLACE,
       _env(500,900,2_400,2_500, SYNTHETIC_TEST,
       why='swept 600-2400 ms as an overlay: adds exactly 0.0 ms of sequence time at every point, which is what makes it different from cutting to it',
       swept=PIP_SWEEP, quant=FRAME_US, bias=0),
       MEDIUM, "DESIGNABLE", "PIP", "REVEAL_SKILL", peak_ratio=0.6,
       anchor_kind="CAMERA_CUT", can_overlap=True, render_cost="EXPENSIVE",
       notes="SIMULTANEOUS: costs no sequence time, unlike ENEMY_POV_INSERT"),

    # ── family 14: chat and meme ────────────────────────────────────────────
    _T("CHAT_BUBBLE", F_CHAT, ("CHAT_REACTION",), t.REPLACE,
       _env(400, 700, 2_000, 2_500, why="long enough to read a short line"),
       MEDIUM, "PROTOTYPE", "TEXT_CHAT", "COMEDIC_RELEASE", peak_ratio=0.2,
       anchor_kind="MATERIAL_FLASH", can_overlap=True,
       evidence_required=("chat",), render_cost="CHEAP"),
    _T("GLITCH_INSERT", F_CHAT, ("LAG_TELEPORT_STYLIZATION",), t.STUTTER,
       _env(80, 150, 500, 900, why="a glitch that lasts is a broken render, not "
            "a joke"),
       SMALL, "DESIGNABLE", "FX", "COMEDIC_RELEASE", peak_ratio=0.3,
       anchor_kind="STUTTER_ATTACK", dwell_min_us=33 * MS, dwell_max_us=200 * MS,
       repeats_min=2, repeats_max=8,
       evidence_required=("netcode_anomaly",), render_cost="MODERATE"),

    # ── family 15: intro and outro ──────────────────────────────────────────
    _T("PROJECT_IDENTITY", F_FRAMING, ("PROJECT_INTRO",), t.SYNTHETIC_INSERT,
       _env(2_000, 3_000, 8_000, 15_000, why="the series signature; it is "
            "authored to the music from the start"),
       SEQUENCE, "PROVEN_RUNTIME", "NARRATIVE", "TRIBUTE", peak_ratio=0.7,
       anchor_kind="MORPH_PEAK", music_targets=("PHRASE",), render_cost="MODERATE"),
    _T("TRIBUTE_OUTRO", F_FRAMING, ("QUAKE_TRIBUTE_OUTRO",), t.SYNTHETIC_INSERT,
       _env(3_000, 6_000, 20_000, 40_000, why="a cooldown, authored to whatever "
            "the song does at the end"),
       SEQUENCE, "PROVEN_RUNTIME", "NARRATIVE", "TRIBUTE", peak_ratio=0.2,
       anchor_kind="MORPH_PEAK", music_targets=("PHRASE", "NEGATIVE_SPACE")),
)

BY_ID: dict[str, TemporalEffectTemplate] = {t_.id: t_ for t_ in TEMPLATES}

# Creative ideas that are selections or narrative framings rather than timed
# effects. Each says why it needs no envelope of its own.
NO_TEMPLATE_REQUIRED: dict[str, str] = {
    "TEAM_ROUND_STORY": "a way of choosing and ordering material, not an effect "
                        "with a duration of its own",
    "ROUND_LOSS_CONTINUATION": "the absence of a payoff; it spends no time",
    "MOVEMENT_TRANSITION": "covered by MOVEMENT_MATCH_OVERLAP, which carries "
                           "the timing",
    "IDENTITY_MATCH_CUT": "covered by MATCH_CUT_OVERLAP",
    "RHYTHMIC_MOTIF_MONTAGE": "a sequence of whole moments; its timing is the "
                              "sum of its members, not a template envelope",
    "DEATH_AS_TRANSITION": "covered by DEATH_EXPLOSION_MATCH",
    "TELEFRAG_GRAMMAR": "a selection rule for which frags qualify",
    "GAUNTLET_GRAMMAR": "a selection rule for which frags qualify",
    "MULTI_EXPOSURE": "covered by TIME_ECHO, which carries the offset-repeat "
                      "timing this needs",
    "TEMPORAL_DECOMPOSITION": "covered by FREEZE_DECOMPOSITION",
    "FRAME_ECHO": "covered by FRAME_REPEAT and TIME_ECHO between them",
    "MUSIC_REACTIVE_MATERIAL": "covered by MATERIAL_FLASH",
    "ENEMY_POV_REAL": "covered by ENEMY_POV_INSERT and POV_PIP; provenance is "
                      "a property of the source, not of the timing",
    "ENEMY_POV_SYNTHETIC": "covered by ENEMY_POV_INSERT and POV_PIP",
    "SEMANTIC_COMPRESSION": "covered by CA_EXPLAINER_CARD plus ordinary cutting",
    "DAMAGE_CHASE_ASSIST": "covered by POV_PIP and ROUND_WIN_RELEASE",
    "ONE_V_X_ENEMY_REVEAL": "covered by ENEMY_REVEAL_STEP, one step per attack",
}


def get(template_id: str) -> TemporalEffectTemplate:
    if template_id not in BY_ID:
        raise KeyError(f"{template_id!r} is not a temporal effect template")
    return BY_ID[template_id]


def for_corpus_entry(name: str) -> tuple[TemporalEffectTemplate, ...]:
    return tuple(t_ for t_ in TEMPLATES if name in t_.corpus_entries)


def coverage(corpus_names: Iterable[str]) -> dict[str, Any]:
    """Which creative ideas have timing, of what quality, and which do not."""
    covered: dict[str, list[str]] = {}
    exempt: dict[str, str] = {}
    missing: list[str] = []
    for name in corpus_names:
        hits = [t_.id for t_ in for_corpus_entry(name)]
        if hits:
            covered[name] = hits
        elif name in NO_TEMPLATE_REQUIRED:
            exempt[name] = NO_TEMPLATE_REQUIRED[name]
        else:
            missing.append(name)
    by_prov = {p: sum(1 for t_ in TEMPLATES if t_.envelope.provenance == p)
               for p in PROVENANCE}
    return {"templates": len(TEMPLATES), "covered": len(covered),
            "exempt": len(exempt), "missing": sorted(missing),
            "by_provenance": by_prov,
            "measured_share": round(
                sum(1 for t_ in TEMPLATES if t_.measured) / max(len(TEMPLATES), 1), 4),
            "by_family": {f: sum(1 for t_ in TEMPLATES if t_.family == f)
                          for f in FAMILIES},
            "by_power": {p: sum(1 for t_ in TEMPLATES if t_.temporal_power == p)
                         for p in POWERS},
            "version": TEMPLATE_VERSION}


# ── combinations ────────────────────────────────────────────────────────────

def check_combination(ids: Sequence[str]) -> list[str]:
    """Complaints about a set of effects used together, in order."""
    out: list[str] = []
    chosen = [get(i) for i in ids]
    present = set(ids)
    for i, t_ in enumerate(chosen):
        for bad in t_.bad_with:
            if bad in present:
                out.append(f"{t_.id} and {bad} compete for the same attention")
        for need in t_.must_follow:
            if need in present and ids.index(need) > i:
                out.append(f"{t_.id} must come after {need}")
        for lead in t_.must_precede:
            if lead in present and ids.index(lead) < i:
                out.append(f"{t_.id} must come before {lead}")
    return out


def combined_envelope(ids: Sequence[str]) -> t.TemporalElasticity:
    """What a whole choreography can occupy, from the templates' own numbers."""
    return t.elasticity([get(i).operator_for() for i in ids])


def solver_confidence(ids: Sequence[str]) -> dict[str, Any]:
    """How much of this choreography's timing is measured rather than guessed."""
    chosen = [get(i) for i in ids]
    measured = [t_.id for t_ in chosen if t_.measured]
    estimated = [t_.id for t_ in chosen if not t_.measured]
    weakest = min((t_.envelope.provenance for t_ in chosen),
                  key=lambda p: PROVENANCE_RANK[p], default=DESIGN_ESTIMATE)
    return {"measured": measured, "estimated": estimated,
            "weakest_provenance": weakest,
            "trusted": not estimated,
            "note": ("every envelope here has been swept" if not estimated else
                     f"{len(estimated)} of {len(chosen)} envelopes are reasoning, "
                     f"not measurement")}


# ── the atlas ───────────────────────────────────────────────────────────────

def atlas_rows() -> list[dict[str, Any]]:
    """Every template as one row: what it does, how long, how sure we are."""
    out = []
    for t_ in sorted(TEMPLATES, key=lambda x: (x.family, x.id)):
        e = t_.envelope
        out.append({
            "id": t_.id, "family": t_.family, "operator": t_.operator,
            "sign": t_.sign, "power": t_.temporal_power,
            "capability": t_.capability, "cost": t_.render_cost,
            "hard_ms": [e.hard_min_us // MS, e.hard_max_us // MS],
            "preferred_ms": [e.preferred_min_us // MS, e.preferred_max_us // MS],
            "provenance": e.provenance, "measured": t_.measured,
            "quantisation_us": e.quantisation_us,
            "delivery_bias_us": e.delivery_bias_us,
            "music_targets": list(t_.music_targets),
            "anchor_kind": t_.anchor_kind,
            "corpus_entries": list(t_.corpus_entries),
            "rationale": e.rationale,
        })
    return out


def render_atlas(dst: Any, *, dpi: int = 120, width: float = 16.0) -> Any:
    """The EFFECT TEMPORAL ATLAS: every effect's usable duration range, with
    measured envelopes drawn solid and estimates drawn hollow."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from pathlib import Path

    rows = atlas_rows()
    fam_color = {F_CUTTING: "#ffd24d", F_RETIME: "#c792ea", F_REPLAY: "#7fb3ff",
                 F_TRANSITION: "#ff8c42", F_RHYTHM: "#ff4d6d", F_WORLD: "#48b0a0",
                 F_MODEL: "#7ee787", F_INFORMATION: "#e6e6e6", F_MOVEMENT: "#56d4c4",
                 F_PROJECTILE: "#9ad0ff", F_DEATH: "#ff6b6b", F_TEAM: "#f2c14e",
                 F_POV: "#bdbdbd", F_CHAT: "#8fa1b3", F_FRAMING: "#a5d6a7"}
    fig, ax = plt.subplots(figsize=(width, 0.30 * len(rows) + 2.4),
                           facecolor="#101010")
    ax.set_facecolor("#101010")
    for i, r in enumerate(rows):
        y = len(rows) - i - 1
        c = fam_color.get(r["family"], "#888")
        hlo, hhi = r["hard_ms"][0] * MS, r["hard_ms"][1] * MS
        plo, phi = r["preferred_ms"][0] * MS, r["preferred_ms"][1] * MS
        ax.plot([hlo, hhi], [y, y], color=c, lw=1.0, alpha=0.45)
        ax.add_patch(Rectangle((plo, y - 0.30), max(phi - plo, MS), 0.60,
                               facecolor=c if r["measured"] else "none",
                               edgecolor=c, lw=1.2,
                               alpha=0.95 if r["measured"] else 0.8,
                               hatch=None if r["measured"] else "///"))
        ax.plot([hlo, hlo], [y - 0.22, y + 0.22], color=c, lw=1.0)
        ax.plot([hhi, hhi], [y - 0.22, y + 0.22], color=c, lw=1.0)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{r['id']}  ·{r['power'][:3]}" for r in reversed(rows)],
                       color="#e6e6e6", fontsize=7)
    ax.set_xscale("symlog", linthresh=100 * MS)
    ax.set_xlim(0, 45_000 * MS)
    ax.set_xticks([0, 100 * MS, 300 * MS, 1_000 * MS, 3_000 * MS,
                   8_000 * MS, 20_000 * MS, 40_000 * MS])
    ax.set_xticklabels(["0", "100 ms", "300 ms", "1 s", "3 s", "8 s", "20 s", "40 s"],
                       color="#9a9a9a")
    ax.set_xlabel("usable duration (log)", color="#9a9a9a")
    ax.tick_params(colors="#9a9a9a", labelsize=7)
    for s_ in ax.spines.values():
        s_.set_color("#2a2a2a")
    ax.grid(axis="x", color="#222", lw=0.6)
    n_meas = sum(1 for r in rows if r["measured"])
    fig.suptitle("PANTHEON effect temporal atlas", color="#e6e6e6", fontsize=13,
                 x=0.008, y=0.995, ha="left", weight="bold")
    fig.text(0.008, 0.975,
             f"{len(rows)} templates · solid = swept on real footage ({n_meas}) · "
             f"hatched = design estimate ({len(rows)-n_meas}) · bars are the "
             f"preferred band, whiskers the hard limits",
             color="#9a9a9a", fontsize=8, ha="left")
    fig.text(0.008, 0.004, f"PLANNING ONLY · {TEMPLATE_VERSION}",
             color="#666", fontsize=7)
    fig.tight_layout(rect=(0, 0.01, 1, 0.965))
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dst, dpi=dpi, facecolor="#101010")
    plt.close(fig)
    return dst


# ── solving from templates ──────────────────────────────────────────────────

def solve_from_templates(slot_id: str, slot_us: int,
                         spec: Sequence[dict[str, Any]], *,
                         anchors: Sequence[Any] = (), top: int = 3) -> Any:
    """Solve a slot using the templates' OWN envelopes.

    `spec` is a list of {"template": id, "label": ..., "src_in_us": ...,
    "src_out_us": ...}. Nothing here invents a duration range: every bound
    comes from the library, and the report says how much of it was measured.
    """
    from creative_suite.engine import temporal_solver as ts
    ops, ids = [], []
    for item in spec:
        tpl = get(item["template"])
        ids.append(tpl.id)
        ops.append(tpl.operator_for(item.get("label", tpl.id),
                                    src_in_us=item.get("src_in_us"),
                                    src_out_us=item.get("src_out_us")))
    report = ts.solve(slot_id, slot_us, ops, anchors=anchors, top=top)
    return report, solver_confidence(ids), check_combination(ids)


def slot_verdict(slot_us: int, spec: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Can this choreography occupy this slot, and how comfortably?

    Answers the question a score search should ask: not "is the source long
    enough" but "does the slot fall inside what these effects can honestly
    produce".
    """
    ids = [i["template"] for i in spec]
    ops = [get(i["template"]).operator_for(i.get("label"),
                                           src_in_us=i.get("src_in_us"),
                                           src_out_us=i.get("src_out_us"))
           for i in spec]
    el = t.elasticity(ops)
    if not el.fits(slot_us):
        verdict = "INFEASIBLE"
    elif el.comfortable(slot_us):
        verdict = "PREFERRED_FEASIBLE"
    else:
        verdict = "HARD_FEASIBLE"
    conf = solver_confidence(ids)
    return {"slot_us": slot_us, "verdict": verdict,
            "hard_ms": [el.min_us // MS, el.max_us // MS],
            "preferred_ms": [el.preferred_min_us // MS, el.preferred_max_us // MS],
            "timing_confidence": conf,
            "combination_problems": check_combination(ids)}


# ── temporal primitives ─────────────────────────────────────────────────────
# The small set of things the pipeline actually DOES. Measure each once; the
# semantic effects that compose them inherit that truth. "12 of 50 templates"
# was the wrong denominator, because most of those 50 reuse the same machinery.

P_FREEZE = "FREEZE"
P_RETIME = "RETIME"
P_FRAME_REPEAT = "FRAME_REPEAT"
P_STUTTER = "STUTTER"
P_REVERSE = "REVERSE"
P_REPLAY = "REPLAY"
P_SEQUENTIAL_INSERT = "SEQUENTIAL_INSERT"
P_SIMULTANEOUS_OVERLAY = "SIMULTANEOUS_OVERLAY"
P_OVERLAP = "OVERLAP"
P_MORPH = "MORPH"
P_CAMERA_HANDOFF = "CAMERA_HANDOFF"
P_MATERIAL_TRANSFORM = "MATERIAL_TRANSFORM"
P_WORLD_TRANSFORM = "WORLD_TRANSFORM"
P_INFORMATION_REVEAL = "INFORMATION_REVEAL"
P_SYNTHETIC_ANIMATION = "SYNTHETIC_ANIMATION_INSERT"

PARTIALLY_MEASURED = "PARTIALLY_MEASURED"
# Sits between a pure estimate and a swept envelope: some components are
# measured, so it is worth more than a guess and less than a measurement.
PROVENANCE_RANK[PARTIALLY_MEASURED] = 0.5


# What stands between a primitive and a measurement. An unmeasured timing is
# not merely weak; it is unmeasured FOR A REASON, and the reason decides what
# would have to happen next. "No runtime" is a build task. "Needs a creative
# seed" is a decision nobody has made yet. Collapsing the two into one number
# hides which effects are days away and which are months.
MEASURED = "MEASURED"
RUNTIME_EXISTS_UNSWEPT = "RUNTIME_EXISTS_UNSWEPT"
RUNTIME_MISSING = "RUNTIME_MISSING"
REQUIRES_NEW_TECH = "REQUIRES_NEW_TECH"
REQUIRES_CREATIVE_SEED = "REQUIRES_CREATIVE_SEED"
CAPABILITIES = (MEASURED, RUNTIME_EXISTS_UNSWEPT, RUNTIME_MISSING,
                REQUIRES_NEW_TECH, REQUIRES_CREATIVE_SEED)

# How far each state is from a number the solver may trust. Ordering only.
CAPABILITY_DISTANCE = {MEASURED: 0, RUNTIME_EXISTS_UNSWEPT: 1,
                       RUNTIME_MISSING: 2, REQUIRES_NEW_TECH: 3,
                       REQUIRES_CREATIVE_SEED: 3}


@dataclass(frozen=True)
class PrimitiveTiming:
    """One thing the pipeline does, and how well its timing is known."""
    name: str
    provenance: str
    calibration: Any = None
    swept_points_us: tuple[int, ...] = ()
    quantisation_us: int | None = None
    delivery_bias_us: int = 0
    finding: str = ""
    capability: str = MEASURED
    blocked_by: str = ""        # what is missing, in one phrase
    measurable_when: str = ""   # the concrete thing that unblocks a sweep

    def __post_init__(self) -> None:
        if self.provenance not in PROVENANCE:
            raise ValueError(f"{self.name}: unknown provenance")
        if self.provenance in (SYNTHETIC_TEST, RUNTIME_MEASURED) and not self.swept_points_us:
            raise ValueError(f"{self.name}: claims measurement without a sweep")
        if self.capability not in CAPABILITIES:
            raise ValueError(f"{self.name}: unknown capability {self.capability!r}")
        if self.capability == MEASURED and not self.measured:
            raise ValueError(
                f"{self.name}: claims to be measured but its timing provenance "
                f"is {self.provenance}")
        if self.capability != MEASURED and not (self.blocked_by
                                                and self.measurable_when):
            raise ValueError(
                f"{self.name}: an unmeasured primitive must say what blocks it "
                f"and what would unblock it, or it is just a shrug")

    @property
    def distance(self) -> int:
        return CAPABILITY_DISTANCE[self.capability]

    @property
    def measured(self) -> bool:
        return PROVENANCE_RANK[self.provenance] >= PROVENANCE_RANK[SOLVER_TRUSTED_FROM]

    @property
    def approved(self) -> bool:
        return self.provenance == HUMAN_APPROVED

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["calibration"] = self.calibration.to_dict() if self.calibration else None
        d.update(measured=self.measured, approved=self.approved,
                 distance=self.distance)
        return d


def _p(name, prov, swept=(), quant=None, bias=0, finding="", cal=None,
       capability=MEASURED, blocked_by="", measurable_when=""):
    return PrimitiveTiming(name, prov, cal if cal is not None else
                           (CALIBRATION_60_X264 if prov in
                            (SYNTHETIC_TEST, RUNTIME_MEASURED) else None),
                           tuple(v * MS for v in swept), quant, bias, finding,
                           capability, blocked_by, measurable_when)


PRIMITIVES: dict[str, PrimitiveTiming] = {p.name: p for p in (
    _p(P_FREEZE, SYNTHETIC_TEST, FREEZE_SWEEP, FRAME_US, FRAME_US,
       "delivery is exact to the frame but always one frame long, at every "
       "point from 50 to 900 ms; the request is compensated"),
    _p(P_RETIME, SYNTHETIC_TEST, (300, 800, 4_000, 8_000), FRAME_US, 0,
       "rates 3/10, 2/5 and 1/1 land exactly; 1/4, 1/2, 55/100 and 7/10 lose "
       "one frame and deliver a slightly faster effective rate"),
    _p(P_FRAME_REPEAT, SYNTHETIC_TEST, STUTTER_SWEEP, FRAME_US, 0,
       "a 33 ms hold survives (two frames); shorter cannot exist at 60 fps"),
    _p(P_STUTTER, SYNTHETIC_TEST, STUTTER_SWEEP, FRAME_US, 0,
       "unequal figures survive: 110/230/170 ms within 6.7 ms and "
       "60/90/45/120 within 1.7 ms; nothing is forced onto an even grid"),
    _p(P_REVERSE, SYNTHETIC_TEST, REWIND_SWEEP, FRAME_US, 0,
       "reverse plus forward replay costs exactly twice the slice, with "
       "0.0 ms error at every point"),
    _p(P_REPLAY, SYNTHETIC_TEST, (300, 800, 4_000, 8_000), FRAME_US, 0,
       "shares the retime primitive; the insertion itself is exact"),
    _p(P_SEQUENTIAL_INSERT, SYNTHETIC_TEST, PIP_SWEEP, FRAME_US, 0,
       "adds exactly its own duration at every point from 600 to 2400 ms"),
    _p(P_SIMULTANEOUS_OVERLAY, SYNTHETIC_TEST, PIP_SWEEP, FRAME_US, 0,
       "adds exactly 0.0 ms at every point; this is what separates a "
       "picture-in-picture from a cut"),
    _p(P_OVERLAP, SYNTHETIC_TEST, OVERLAP_SWEEP, FRAME_US, 0,
       "removes exactly the time requested, 0.0 ms error across 50-500 ms"),
    _p(P_MORPH, DESIGN_ESTIMATE, capability=REQUIRES_NEW_TECH,
       finding="no runtime yet: interpolated model and world morphs are not "
       "implemented",
       blocked_by="there is no vertex correspondence between two MD3 models, "
       "so nothing knows which point becomes which",
       measurable_when="a correspondence solver exists and can emit an "
       "interpolated frame sequence; then sweep the transition duration"),
    _p(P_CAMERA_HANDOFF, DESIGN_ESTIMATE, capability=RUNTIME_EXISTS_UNSWEPT,
       finding="a cut is trivially exact; interpolated handoffs are unmeasured",
       blocked_by="q3mme can already move a camera along a spline, but no "
       "sweep has measured what an interpolated handoff costs in delivered time",
       measurable_when="a handoff sweep runs on real captures at 200, 400, 600 "
       "and 900 ms and the delivered durations are read back from the file"),
    _p(P_MATERIAL_TRANSFORM, DESIGN_ESTIMATE, capability=RUNTIME_EXISTS_UNSWEPT,
       finding="shader and texture replacement exist in the asset system but "
       "their timing is unswept",
       blocked_by="the photoreal pipeline can already swap a texture, but a "
       "swap has never been timed against a delivered frame",
       measurable_when="a zzz_ style pack drives a timed swap during a capture "
       "and the frame it lands on is read back"),
    _p(P_WORLD_TRANSFORM, DESIGN_ESTIMATE, capability=RUNTIME_MISSING,
       finding="geometry strip and rebuild have no runtime",
       blocked_by="nothing can currently hide or restore BSP geometry on a "
       "schedule; the geometry is read but never driven",
       measurable_when="a renderer path can suppress surfaces per frame; the "
       "sweep is then the same shape as the material one"),
    _p(P_INFORMATION_REVEAL, DESIGN_ESTIMATE, capability=RUNTIME_MISSING,
       finding="reveal, update and hide timing is unswept",
       blocked_by="overlays are composited by ffmpeg after the capture, so "
       "their appearance has never been timed against gameplay frames",
       measurable_when="an overlay is composited at a stated timestamp and the "
       "frame it first appears on is read back from the delivered file"),
    _p(P_SYNTHETIC_ANIMATION, DESIGN_ESTIMATE, capability=REQUIRES_CREATIVE_SEED,
       finding="authored animation: the duration is free but nothing has been "
       "built",
       blocked_by="the duration is whatever the animation is authored to be, "
       "so there is nothing to measure until something is authored",
       measurable_when="an actual piece exists; its duration is then a fact "
       "about that piece and not a property of the primitive"),
)}

# Which primitives each semantic template composes. A template with no entry
# falls back to the primitive its operator implies.
_OPERATOR_PRIMITIVE = {
    t.FREEZE: P_FREEZE, t.RETIME: P_RETIME, t.REPEAT: P_FRAME_REPEAT,
    t.STUTTER: P_STUTTER, t.REPLAY: P_REPLAY, t.OVERLAP: P_OVERLAP,
    t.INSERT: P_SEQUENTIAL_INSERT, t.REPLACE: P_SIMULTANEOUS_OVERLAY,
    t.SYNTHETIC_INSERT: P_SYNTHETIC_ANIMATION, t.TRIM: P_RETIME,
}

COMPONENTS: dict[str, tuple[str, ...]] = {
    "PLAYER_FREEZE_POSE": (P_FREEZE, P_SYNTHETIC_ANIMATION, P_CAMERA_HANDOFF),
    "GRENADE_GAG": (P_SYNTHETIC_ANIMATION, P_CAMERA_HANDOFF),
    "MODEL_MORPH": (P_MORPH, P_MATERIAL_TRANSFORM),
    "WORLD_STRIP": (P_WORLD_TRANSFORM, P_FREEZE),
    "WORLD_REBUILD": (P_WORLD_TRANSFORM,),
    "WALL_XRAY": (P_WORLD_TRANSFORM, P_FREEZE, P_CAMERA_HANDOFF),
    "MAP_CONSTRUCTION": (P_WORLD_TRANSFORM, P_MATERIAL_TRANSFORM, P_SYNTHETIC_ANIMATION),
    "LOW_HP_WORLD": (P_MATERIAL_TRANSFORM,),
    "TEXTURE_TEXT_REVEAL": (P_MATERIAL_TRANSFORM, P_INFORMATION_REVEAL),
    "DAMAGE_LEDGER_TICK": (P_INFORMATION_REVEAL,),
    "ROUND_DAMAGE_TOTAL": (P_INFORMATION_REVEAL,),
    "ENEMY_COUNT_TICK": (P_INFORMATION_REVEAL,),
    "RAIL_COOLDOWN_BAR": (P_INFORMATION_REVEAL,),
    "CA_EXPLAINER_CARD": (P_INFORMATION_REVEAL, P_SYNTHETIC_ANIMATION),
    "SHAFT_STAT_REVEAL": (P_INFORMATION_REVEAL,),
    "ENEMY_REVEAL_STEP": (P_INFORMATION_REVEAL, P_WORLD_TRANSFORM),
    "MOSAIC_TILE_STEP": (P_STUTTER, P_MATERIAL_TRANSFORM),
    "MODEL_PULSE": (P_SIMULTANEOUS_OVERLAY, P_MATERIAL_TRANSFORM),
    "MATERIAL_FLASH": (P_SIMULTANEOUS_OVERLAY, P_MATERIAL_TRANSFORM),
    "CAMERA_JOLT": (P_SIMULTANEOUS_OVERLAY, P_CAMERA_HANDOFF),
    "SIDE_REPLAY": (P_REPLAY, P_RETIME, P_CAMERA_HANDOFF),
    "PROJECTILE_REPLAY": (P_REPLAY, P_RETIME, P_CAMERA_HANDOFF),
    "PROJECTILE_FOLLOW": (P_REPLAY, P_RETIME, P_CAMERA_HANDOFF),
    "GRENADE_ARC": (P_REPLAY, P_RETIME, P_CAMERA_HANDOFF),
    "ENEMY_POV_INSERT": (P_SEQUENTIAL_INSERT, P_CAMERA_HANDOFF),
    "POV_PIP": (P_SIMULTANEOUS_OVERLAY,),
    "DEATH_REWIND": (P_REVERSE, P_REPLAY),
    "MICRO_REWIND": (P_REVERSE,),
    "DEATH_FLASH_MONTAGE": (P_FRAME_REPEAT,),
    "TIME_ECHO": (P_FRAME_REPEAT, P_SIMULTANEOUS_OVERLAY),
    "FREEZE_DECOMPOSITION": (P_FREEZE, P_SIMULTANEOUS_OVERLAY),
    "ROCKET_FLYBY_BRIDGE": (P_OVERLAP, P_CAMERA_HANDOFF),
    "WORLD_MORPH_BRIDGE": (P_OVERLAP, P_MORPH, P_WORLD_TRANSFORM),
    "ROUND_WIN_RELEASE": (P_SEQUENTIAL_INSERT, P_SYNTHETIC_ANIMATION),
    "PROJECT_IDENTITY": (P_SYNTHETIC_ANIMATION,),
    "TRIBUTE_OUTRO": (P_SYNTHETIC_ANIMATION,),
    "CHAT_BUBBLE": (P_SIMULTANEOUS_OVERLAY, P_INFORMATION_REVEAL),
    "GLITCH_INSERT": (P_STUTTER, P_MATERIAL_TRANSFORM),
    "NOPE_BEAT": (P_SEQUENTIAL_INSERT, P_INFORMATION_REVEAL),
    "HIGH_SPEED_HOLD": (P_RETIME,),
    "MOVEMENT_ACCENT": (P_SIMULTANEOUS_OVERLAY,),
}


def capability_report() -> dict[str, Any]:
    """What each unmeasured primitive costs, in semantic effects.

    A gap is only worth closing in proportion to what it unlocks. This says
    which templates are waiting on each one, so the next sweep is chosen by
    what it buys rather than by what is easiest.
    """
    blocked: dict[str, list[str]] = {}
    for tpl in TEMPLATES:
        tid = tpl.id if hasattr(tpl, "id") else tpl
        for p in components_of(tid):
            prim = PRIMITIVES.get(p)
            if prim is not None and not prim.measured:
                blocked.setdefault(p, []).append(tid)
    rows = []
    for name, prim in PRIMITIVES.items():
        if prim.measured:
            continue
        waiting = sorted(set(blocked.get(name, [])))
        rows.append({"primitive": name, "capability": prim.capability,
                     "distance": prim.distance, "blocked_by": prim.blocked_by,
                     "measurable_when": prim.measurable_when,
                     "templates_waiting": waiting,
                     "templates_waiting_count": len(waiting)})
    rows.sort(key=lambda r: (r["distance"], -r["templates_waiting_count"]))
    return {"version": TEMPLATE_VERSION, "unmeasured": rows,
            "measured": sorted(n for n, p in PRIMITIVES.items() if p.measured)}


def components_of(template_id: str) -> tuple[str, ...]:
    tpl = get(template_id)
    return COMPONENTS.get(template_id,
                          (_OPERATOR_PRIMITIVE.get(tpl.operator, P_RETIME),))


def component_provenance(template_id: str) -> dict[str, str]:
    """Per component, not one coarse label for the whole effect."""
    return {c: PRIMITIVES[c].provenance for c in components_of(template_id)}


def template_provenance(template_id: str) -> str:
    """Derived from the components.

    A composite whose freeze is measured and whose custom animation is not is
    PARTIALLY_MEASURED, which is far more useful than calling the whole effect
    an estimate and far more honest than calling it measured.
    """
    provs = component_provenance(template_id)
    if not provs:
        return DESIGN_ESTIMATE
    ranks = [PROVENANCE_RANK[p] for p in provs.values()]
    trusted = PROVENANCE_RANK[SOLVER_TRUSTED_FROM]
    if all(r >= PROVENANCE_RANK[HUMAN_APPROVED] for r in ranks):
        return HUMAN_APPROVED
    if all(r >= trusted for r in ranks):
        return (RUNTIME_MEASURED
                if all(p == RUNTIME_MEASURED for p in provs.values())
                else SYNTHETIC_TEST)
    if any(r >= trusted for r in ranks):
        return PARTIALLY_MEASURED
    return DESIGN_ESTIMATE


def coverage_split() -> dict[str, Any]:
    """Two denominators, each named.

    Reporting a bare percentage without saying what it is a percentage OF is
    how a number stops meaning anything.
    """
    prim = {"total": len(PRIMITIVES),
            "measured": sorted(n for n, p in PRIMITIVES.items() if p.measured),
            "human_approved": sorted(n for n, p in PRIMITIVES.items() if p.approved),
            "unmeasured": sorted(n for n, p in PRIMITIVES.items() if not p.measured)}
    buckets: dict[str, list[str]] = {SYNTHETIC_TEST: [], RUNTIME_MEASURED: [],
                                     HUMAN_APPROVED: [], PARTIALLY_MEASURED: [],
                                     DESIGN_ESTIMATE: []}
    new_tech: list[str] = []
    for tpl in TEMPLATES:
        buckets[template_provenance(tpl.id)].append(tpl.id)
        if tpl.capability in ("REQUIRES_NEW_TECH", "CREATIVE_SEED"):
            new_tech.append(tpl.id)
    fully = sorted(buckets[SYNTHETIC_TEST] + buckets[RUNTIME_MEASURED]
                   + buckets[HUMAN_APPROVED])
    return {
        "primitives": {**prim, "measured_share": round(
            len(prim["measured"]) / len(PRIMITIVES), 4)},
        "semantic_templates": {
            "total": len(TEMPLATES),
            "fully_measured": fully,
            "partially_measured": sorted(buckets[PARTIALLY_MEASURED]),
            "design_only": sorted(buckets[DESIGN_ESTIMATE]),
            "requires_new_tech_or_seed": sorted(new_tech),
            "fully_measured_share": round(len(fully) / len(TEMPLATES), 4),
            "any_measured_share": round(
                (len(fully) + len(buckets[PARTIALLY_MEASURED])) / len(TEMPLATES), 4)},
        "version": TEMPLATE_VERSION}


def measured_only_envelope(template_id: str) -> dict[str, Any]:
    """What this effect can do TODAY versus what it is designed to do.

    An effect whose morph is unbuilt still has a usable range from the parts
    that exist. Reporting only the full design range would let future R&D
    contaminate today's solver.
    """
    tpl = get(template_id)
    e = tpl.envelope
    provs = component_provenance(template_id)
    measured = [c for c, p in provs.items()
                if PROVENANCE_RANK[p] >= PROVENANCE_RANK[SOLVER_TRUSTED_FROM]]
    return {"template": template_id,
            "provenance": template_provenance(template_id),
            "components": provs,
            "measured_components": sorted(measured),
            "full_design_range_ms": [e.hard_min_us // MS, e.hard_max_us // MS],
            "measured_only_range_ms": (
                [e.hard_min_us // MS, e.hard_max_us // MS] if len(measured) == len(provs)
                else None),
            "note": ("every component is measured" if len(measured) == len(provs)
                     else f"{len(provs) - len(measured)} of {len(provs)} components "
                          f"are unmeasured, so the design range is not a promise")}
