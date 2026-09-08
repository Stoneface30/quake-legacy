"""How many milliseconds a slot is short, and what may honestly close it.

THE QUESTION. A score interval is 8.400 s. The choreography as it stands
occupies 7.830 s. Something must supply 570 ms. This module says which
operators could, how much each can move, and how sure we are of those
numbers -- and then refuses the ones that have no business being there.

THE RULE THAT MATTERS. An effect may close a gap only when it also belongs.
"We need 412 ms, so put something there" is how a film fills with decoration
that means nothing. A double air rocket that is 500 ms short should extend
its cinematic replay, because the trajectory deserves examination. It should
not display a damage counter for 500 ms because the arithmetic works out.

So every candidate operator must pass three independent gates:

    TEMPORAL_FIT           it can actually move this many milliseconds
    CREATIVE_JUSTIFICATION its purpose fits this gameplay and this narrative
    VISUAL_FIT             the duration needed sits in a range we trust

If nothing passes all three, the honest answer is that this moment does not
fit this slot -- not that we found something to pad it with.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Iterable, Sequence

from creative_suite.engine import effect_templates as et
from creative_suite.engine import temporal_operators as t

BUDGET_VERSION = "temporal-budget-v1.0.0"
MS = 1000

TEMPORAL_FIT = "TEMPORAL_FIT"
CREATIVE_JUSTIFICATION = "CREATIVE_JUSTIFICATION"
VISUAL_FIT = "VISUAL_FIT"
GATES = (TEMPORAL_FIT, CREATIVE_JUSTIFICATION, VISUAL_FIT)


@dataclass(frozen=True)
class Justification:
    """Why an effect belongs in THIS moment, stated by whoever proposes it.

    `evidence_present` are the recorded facts the moment actually has. An
    effect whose template needs a projectile path cannot be justified in a
    moment that has none, whatever the arithmetic says.
    """
    narrative: str                      # what the slot is doing
    gameplay_kind: str                  # what the moment is
    evidence_present: tuple[str, ...] = ()
    director_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Option:
    """One operator that could move time here, with its three verdicts."""
    template_id: str
    min_us: int                         # signed: an overlap subtracts
    preferred_min_us: int
    preferred_max_us: int
    max_us: int
    provenance: str
    temporal_power: str
    gates_passed: tuple[str, ...]
    refused_because: str = ""

    @property
    def eligible(self) -> bool:
        return len(self.gates_passed) == len(GATES)

    @property
    def adds_time(self) -> bool:
        return self.max_us > 0

    def can_move(self, needed_us: int) -> bool:
        """Whether this operator alone could cover the gap."""
        lo, hi = min(self.min_us, self.max_us), max(self.min_us, self.max_us)
        return lo <= needed_us <= hi

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(eligible=self.eligible, adds_time=self.adds_time)
        return d


@dataclass(frozen=True)
class Solution:
    """A set of operators that together close the gap."""
    options: tuple[str, ...]
    contributions_us: tuple[int, ...]
    total_us: int
    weakest_provenance: str
    powers: tuple[str, ...]

    @property
    def closes(self) -> bool:
        return True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TemporalBudget:
    """What the slot needs and what may honestly supply it."""
    slot_id: str
    slot_us: int
    raw_gameplay_us: int
    composed_us: int
    justification: Justification
    options: tuple[Option, ...] = ()
    solutions: tuple[Solution, ...] = ()

    @property
    def delta_us(self) -> int:
        """Positive means the slot needs more; negative means too much."""
        return self.slot_us - self.composed_us

    @property
    def needs_more(self) -> bool:
        return self.delta_us > 0

    @property
    def balanced(self) -> bool:
        return self.delta_us == 0

    @property
    def eligible_options(self) -> tuple[Option, ...]:
        return tuple(o for o in self.options if o.eligible)

    @property
    def verdict(self) -> str:
        if self.balanced:
            return "BALANCED"
        if self.solutions:
            return "SOLVABLE"
        return "DOES_NOT_FIT"

    def explain(self) -> str:
        if self.balanced:
            return f"{self.slot_id} is already exact"
        if self.solutions:
            return (f"{self.slot_id} needs {self.delta_us/1000:+.0f} ms and "
                    f"{len(self.solutions)} combinations of justified effects "
                    f"can supply it")
        refused = [o for o in self.options if not o.eligible]
        why = "; ".join(f"{o.template_id}: {o.refused_because}"
                        for o in refused[:3]) or "no operators were offered"
        return (f"{self.slot_id} needs {self.delta_us/1000:+.0f} ms and nothing "
                f"that belongs here can supply it. This moment does not fit "
                f"this slot. ({why})")

    def to_dict(self) -> dict[str, Any]:
        return {"slot_id": self.slot_id, "slot_us": self.slot_us,
                "raw_gameplay_us": self.raw_gameplay_us,
                "composed_us": self.composed_us, "delta_us": self.delta_us,
                "verdict": self.verdict, "explanation": self.explain(),
                "options": [o.to_dict() for o in self.options],
                "solutions": [s.to_dict() for s in self.solutions],
                "justification": self.justification.to_dict(),
                "version": BUDGET_VERSION}


# Which narratives an effect's purpose serves. An effect whose purpose is
# nowhere near what the slot is doing has no business closing its gap.
PURPOSE_FOR_NARRATIVE: dict[str, tuple[str, ...]] = {
    "REVEAL_SKILL": ("hero", "escalation", "duel", "movement", "projectile"),
    "BUILD_TENSION": ("hero", "escalation", "approach", "duel", "threat"),
    "SHOW_THREAT": ("threat", "escalation", "1vx"),
    "SHOW_DAMAGE": ("duel", "damage", "assist", "threat"),
    "ROUND_PAYOFF": ("victory", "round_end", "team"),
    "REVEAL_TEAM": ("team", "victory"),
    "EXPLAIN_CA": ("explainer", "intro", "team"),
    "EXPLAIN_GEOMETRY": ("explainer", "geometry", "projectile"),
    "MUSICAL_PUNCTUATION": ("montage", "gesture", "transition", "hero",
                            "escalation", "movement"),
    "TRANSITION": ("transition", "montage", "round_end", "hero", "movement"),
    "COMEDIC_RELEASE": ("comedy", "release", "threat"),
    "IDENTITY": ("team", "intro", "identity"),
    "TRIBUTE": ("intro", "outro", "tribute"),
}


def _justified(tpl: et.TemporalEffectTemplate, j: Justification) -> str:
    """Empty string when the effect belongs; otherwise why it does not."""
    missing = [e for e in tpl.evidence_required if e not in j.evidence_present]
    if missing:
        return (f"needs {', '.join(missing)} and this moment has none of it")
    fits = PURPOSE_FOR_NARRATIVE.get(tpl.purpose, ())
    if fits and j.narrative not in fits and j.gameplay_kind not in fits:
        return (f"its purpose is {tpl.purpose}, which does not serve a "
                f"{j.narrative} slot over {j.gameplay_kind} gameplay")
    return ""


class NoOpportunity(ValueError):
    """Raised when a budget is asked to search for effects rather than
    evaluate the ones the action already earned."""


def build(slot_id: str, slot_us: int, raw_gameplay_us: int, composed_us: int,
          justification: Justification, *,
          opportunities: Sequence[Any] | None = None,
          candidates: Sequence[str] | None = None,
          trusted_only: bool = False, max_effects: int = 2) -> TemporalBudget:
    """Evaluate the treatments this action earned against this slot.

    THE INVARIANT: a budget never discovers an effect. It receives the
    creative opportunities the gameplay generated and asks which of THOSE can
    also satisfy the timing. Passing neither `opportunities` nor an explicit
    `candidates` list would mean searching the whole library for something
    worth 570 ms, which is the padding machine this exists to prevent.
    """
    need = slot_us - composed_us
    if opportunities is not None:
        from creative_suite.engine import creative_opportunity as co
        ids = list(co.allowed_templates(opportunities))
        if not ids:
            return TemporalBudget(slot_id, slot_us, raw_gameplay_us, composed_us,
                                  justification, (), ())
    elif candidates is not None:
        ids = list(candidates)
    else:
        raise NoOpportunity(
            "a temporal budget needs the creative opportunities the action "
            "earned. Searching the whole effect library for something that "
            "fills the gap is how a film fills with decoration that means "
            "nothing; if the action earns no treatment, the moment does not "
            "belong in this slot.")
    options: list[Option] = []
    for tid in ids:
        tpl = et.get(tid)
        e = tpl.envelope
        sign = tpl.sign
        lo, hi = sign * e.hard_min_us, sign * e.hard_max_us
        plo, phi = sign * e.preferred_min_us, sign * e.preferred_max_us
        if sign < 0:
            lo, hi = hi, lo
            plo, phi = phi, plo
        prov = et.template_provenance(tid)
        passed: list[str] = []
        refused = ""
        # 1. can it move this kind of time at all
        if sign != 0 and min(lo, hi) <= need <= max(lo, hi):
            passed.append(TEMPORAL_FIT)
        else:
            refused = (f"can move {lo/1000:+.0f}..{hi/1000:+.0f} ms, which does "
                       f"not cover {need/1000:+.0f} ms")
        # 2. does it belong here
        why_not = _justified(tpl, justification)
        if not why_not:
            passed.append(CREATIVE_JUSTIFICATION)
        elif not refused:
            refused = why_not
        # 3. do we trust the duration it would need
        trusted = prov in (et.SYNTHETIC_TEST, et.RUNTIME_MEASURED,
                           et.HUMAN_APPROVED)
        if trusted or (not trusted_only and prov == et.PARTIALLY_MEASURED):
            passed.append(VISUAL_FIT)
        elif not refused:
            refused = (f"its timing is {prov}; a gap should not be closed with "
                       f"a duration nobody has measured")
        options.append(Option(tid, lo, plo, phi, hi, prov, tpl.temporal_power,
                              tuple(passed), refused))

    eligible = [o for o in options if o.eligible]
    solutions: list[Solution] = []
    for o in eligible:                       # one effect closes it
        if o.can_move(need):
            solutions.append(Solution((o.template_id,), (need,), need,
                                      o.provenance, (o.temporal_power,)))
    if max_effects >= 2:                     # two together
        for i, a in enumerate(eligible):
            for b in eligible[i + 1:]:
                lo = min(a.min_us, a.max_us) + min(b.min_us, b.max_us)
                hi = max(a.min_us, a.max_us) + max(b.min_us, b.max_us)
                if lo <= need <= hi and not any(
                        len(s.options) == 1 and s.options[0] in
                        (a.template_id, b.template_id) for s in solutions):
                    share = need // 2
                    solutions.append(Solution(
                        (a.template_id, b.template_id), (share, need - share),
                        need,
                        min((a.provenance, b.provenance),
                            key=lambda p: et.PROVENANCE_RANK[p]),
                        (a.temporal_power, b.temporal_power)))
    # Prefer trusted timing, then the smallest tool that does the job.
    order = {et.HUMAN_APPROVED: 0, et.RUNTIME_MEASURED: 1, et.SYNTHETIC_TEST: 2,
             et.PARTIALLY_MEASURED: 3, et.DESIGN_ESTIMATE: 4}
    power = {et.MICRO: 0, et.SMALL: 1, et.MEDIUM: 2, et.LARGE: 3, et.SEQUENCE: 4}
    solutions.sort(key=lambda s: (order.get(s.weakest_provenance, 9),
                                  max(power.get(p, 9) for p in s.powers),
                                  len(s.options)))
    # An effect that is spent by being used twice should not be reached for
    # casually; the heaviest tool sorts last among equals.
    from creative_suite.engine import creative_opportunity as _co
    heft = {_co.MICRO: 0, _co.SUPPORT: 1, _co.FEATURE: 2, _co.HERO: 3,
            _co.SIGNATURE: 4}
    solutions.sort(key=lambda s: max(
        heft.get(_co.editorial_weight(i)[0], 1) for i in s.options))
    return TemporalBudget(slot_id, slot_us, raw_gameplay_us, composed_us,
                          justification, tuple(options), tuple(solutions[:8]))
