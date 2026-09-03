"""Fit a choreography to an immutable song by varying what the effects cost.

THE QUESTION IT ANSWERS. Not "does this frag fit 5.85 seconds" but "can we
build an excellent version of this moment whose finished choreography
occupies exactly 5.85 seconds and whose important events land on the song's
anchors". Those are different questions and only the second one is useful.

HOW. A deterministic bounded search, not an exotic optimiser -- being able to
read why a solution was chosen matters more than squeezing the last
millisecond. Each operator offers a small set of candidate durations drawn
from its visually preferred band and its hard limits. A dynamic pass over the
reachable totals finds combinations, and one designated absorber closes the
remainder exactly. Then every surviving solution is measured against the
musical anchors, and the objective components are reported separately rather
than collapsed into one number.

WHAT IT WILL NOT DO. It will not stretch an effect past what still looks
good because the arithmetic would close: hard limits are hard. It will not
accelerate anything later to repay time a freeze or a slow replay spent --
that time was spent deliberately. And it will not move the music.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from fractions import Fraction
from typing import Any, Iterable, Sequence

from creative_suite.engine import temporal_operators as tops

SOLVER_VERSION = "temporal-solver-v1.0.0"

# How many candidate durations each operator offers the search.
CANDIDATES_PER_OPERATOR = 9
# How many duration-feasible solutions get measured against the anchors.
# Duration cost and anchor alignment are different objectives, so ranking by
# the first and truncating hides solutions that satisfy the second. Measure
# every candidate up to this cap.
MEASURE_TOP = 4000


@dataclass(frozen=True)
class Objective:
    """Why one solution was preferred, kept in pieces.

    A single score hides the trade the solver made. These stay separate so a
    director can see that a solution is 3 ms off the hero but sits outside
    the preferred replay rate, and disagree.
    """
    hero_residual_us: int = 0
    gesture_residual_us: int = 0
    unsatisfied_anchors: int = 0
    preferred_deviation: float = 0.0
    rate_deviation: float = 0.0        # distance from the rate that looks right
    effect_density: float = 0.0
    complexity: int = 0

    @property
    def total(self) -> float:
        """A ranking number, never a verdict."""
        return round(abs(self.hero_residual_us) / 1000.0
                     + abs(self.gesture_residual_us) / 2000.0
                     + self.unsatisfied_anchors * 500.0
                     + self.preferred_deviation * 40.0
                     + self.rate_deviation * 60.0
                     + self.effect_density * 2.0
                     + self.complexity * 0.5, 4)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["total"] = self.total
        return d


@dataclass(frozen=True)
class Solution:
    plan: tops.TemporalPlan
    objective: Objective

    def to_dict(self) -> dict[str, Any]:
        return {"objective": self.objective.to_dict(), "plan": self.plan.to_dict(),
                "plan_hash": self.plan.plan_hash}


@dataclass(frozen=True)
class SolveReport:
    """Everything needed to understand the fit, or why there wasn't one."""
    slot_id: str
    slot_us: int
    feasible: bool
    reason: str
    elasticity: tops.TemporalElasticity
    solutions: tuple[Solution, ...] = ()
    considered: int = 0
    anchors_reachable: bool = True
    version: str = SOLVER_VERSION

    @property
    def best(self) -> Solution | None:
        return self.solutions[0] if self.solutions else None

    def to_dict(self) -> dict[str, Any]:
        return {"slot_id": self.slot_id, "slot_us": self.slot_us,
                "feasible": self.feasible, "reason": self.reason,
                "anchors_reachable": self.anchors_reachable,
                "elasticity": self.elasticity.to_dict(),
                "considered": self.considered,
                "solutions": [s.to_dict() for s in self.solutions],
                "version": self.version}


def _candidates(op: tops.TemporalOperator, quantum: int) -> list[int]:
    """Durations this operator offers the search, preferred band first."""
    lo, hi = op.hard_min_us, op.hard_max_us
    plo, phi = op.preferred_band
    points = {lo, hi, plo, phi}
    if op.preferred_us is not None:
        points.add(op.preferred_us)
    n = max(CANDIDATES_PER_OPERATOR - len(points), 0)
    if n and phi > plo:
        step = (phi - plo) / (n + 1)
        points.update(int(plo + step * (i + 1)) for i in range(n))
    elif n and hi > lo:
        step = (hi - lo) / (n + 1)
        points.update(int(lo + step * (i + 1)) for i in range(n))
    out = sorted({tops.quantise(p, quantum) for p in points})
    return [d for d in out if op.allows(d)]


def _absorber(operators: Sequence[tops.TemporalOperator]) -> int:
    """The most elastic operator closes the remainder. Widest hard range
    wins; ties go to the later one so a tail absorbs before a trim."""
    best, best_span = 0, -1
    for i, op in enumerate(operators):
        span = op.hard_max_us - op.hard_min_us
        if span >= best_span:
            best, best_span = i, span
    return best


def solve(slot_id: str, slot_us: int, operators: Sequence[tops.TemporalOperator],
          *, anchors: Sequence[tops.AnchorConstraint] = (),
          quantum: int = tops.QUANTUM_US, top: int = 5,
          absorber: int | None = None) -> SolveReport:
    """Find compositions that occupy the slot exactly and land on the music."""
    ops = list(operators)
    el = tops.elasticity(ops)
    if not ops:
        return SolveReport(slot_id, slot_us, False, "no operators to vary", el)
    if not el.fits(slot_us):
        return SolveReport(
            slot_id, slot_us, False,
            f"the slot is {slot_us} us but this choreography can only occupy "
            f"{el.min_us}..{el.max_us} us. Nothing here can be stretched further "
            f"without leaving what still looks acceptable.", el)

    idx = _absorber(ops) if absorber is None else absorber
    ab = ops[idx]
    fixed = [i for i in range(len(ops)) if i != idx]
    lo_sum = sum(ops[i].range_us[0] for i in fixed)
    target = slot_us - lo_sum          # the signed contribution still to be found
    # The absorber may SUBTRACT time (an overlap), in which case the fixed
    # operators are allowed to overshoot the target and the overlap pulls the
    # total back. Pruning at the target alone would discard every valid state.
    ab_lo, ab_hi = ab.range_us
    ceiling = target - ab_lo

    # Reachable partial sums of the non-absorber operators, cheapest first.
    reach: dict[int, tuple[float, tuple[int, ...]]] = {0: (0.0, ())}
    for i in fixed:
        op = ops[i]
        lo_i = op.range_us[0]
        nxt: dict[int, tuple[float, tuple[int, ...]]] = {}
        for total, (cost, picks) in reach.items():
            for d in _candidates(op, quantum):
                signed = op.sign * d
                t2 = total + (signed - lo_i)
                if t2 > ceiling:
                    continue
                c2 = cost + op.soft_cost(d)
                cur = nxt.get(t2)
                if cur is None or c2 < cur[0]:
                    nxt[t2] = (c2, picks + (d,))
        reach = nxt
        if not reach:
            break
    if not reach:
        return SolveReport(slot_id, slot_us, False,
                           "no combination of the fixed operators stays inside "
                           "their limits", el)

    candidates: list[tuple[float, tops.TemporalPlan]] = []
    for total, (cost, picks) in reach.items():
        need = target - total                     # signed contribution wanted
        dur = ab.sign * need if ab.sign else 0
        if ab.sign == 0:
            dur = ab.preferred_band[0]
            if need != 0:
                continue
        if dur <= 0 or not ab.allows(dur):
            continue
        durations: list[int] = []
        it = iter(picks)
        for i in range(len(ops)):
            durations.append(dur if i == idx else next(it))
        choices = tuple(tops.OperatorChoice(ops[i], durations[i])
                        for i in range(len(ops)))
        plan = tops.TemporalPlan(slot_id, slot_us, choices, tuple(anchors), quantum)
        if not plan.exact:
            continue
        candidates.append((cost + ab.soft_cost(dur), plan))

    if not candidates:
        return SolveReport(
            slot_id, slot_us, False,
            f"durations can be combined but none lands exactly on {slot_us} us "
            f"with '{ab.label}' absorbing the remainder inside its limits", el,
            considered=len(reach))

    candidates.sort(key=lambda kv: kv[0])
    measured: list[Solution] = []
    for _cost, plan in candidates[:MEASURE_TOP]:
        measured.append(Solution(plan, _measure(plan)))
    measured.sort(key=lambda s: s.objective.total)
    aligned = [s for s in measured if s.objective.unsatisfied_anchors == 0]
    if anchors and not aligned:
        best = measured[0].objective
        reason = (f"{len(candidates)} compositions occupy the slot exactly, but "
                  f"none lands every required anchor: the closest misses by "
                  f"{abs(best.hero_residual_us)/1000:.0f} ms. The duration fits; "
                  f"the musical relationship does not, and stretching an effect "
                  f"past its limits to reach it is not on offer.")
    else:
        reason = f"{len(candidates)} compositions occupy the slot exactly"
    return SolveReport(slot_id, slot_us, True, reason, el,
                       tuple(measured[:top]), considered=len(candidates),
                       anchors_reachable=bool(aligned) or not anchors)


def _measure(plan: tops.TemporalPlan) -> Objective:
    """Score a resolved plan against the music. Every number is measured on
    the FINISHED composition, never on the raw source."""
    hero = gesture = 0
    unsatisfied = 0
    for row in plan.anchor_report():
        if row["actual_us"] is None:
            if row["required"]:
                unsatisfied += 1
            continue
        if not row["satisfied"] and row["required"]:
            unsatisfied += 1
        if row["kind"] == "HERO":
            if abs(row["residual_us"]) > abs(hero):
                hero = row["residual_us"]        # the worst hero miss, signed
        else:
            gesture += abs(row["residual_us"])
    secs = max(plan.slot_us / 1_000_000, 1e-6)
    # Distance from the rate the director wants. A scene whose natural speed
    # is right should not be nudged 1% off just because the arithmetic closes
    # either way.
    rate_dev = 0.0
    for c in plan.choices:
        want = c.operator.rate_preferred
        if want is not None and c.rate is not None:
            rate_dev += abs(float(c.rate) - float(want))
    return Objective(hero_residual_us=hero, gesture_residual_us=gesture,
                     unsatisfied_anchors=unsatisfied,
                     preferred_deviation=plan.deviation(),
                     rate_deviation=round(rate_dev, 6),
                     effect_density=round(len(plan.choices) / secs, 3),
                     complexity=len(plan.choices))


# ── gesture-derived effect timing ───────────────────────────────────────────

def stutter_from_gesture(label: str, attack_us: Sequence[int], *,
                         dwell_min_us: int = 25_000, dwell_max_us: int = 120_000,
                         release_us: int | None = None,
                         capability: str = "PROTOTYPE") -> tops.TemporalOperator:
    """Build a stutter whose duration the MUSIC decides.

    Given the attacks of a real musical figure, the effect spans the figure:
    a frame is held at each attack and released at the next accent. The
    duration is therefore derived from the gesture, not chosen and then
    placed near it.
    """
    if len(attack_us) < 2:
        raise ValueError("a stutter needs at least two attacks to derive from")
    spans = [b - a for a, b in zip(attack_us, attack_us[1:])]
    end = release_us if release_us is not None else attack_us[-1] + spans[-1]
    total = end - attack_us[0]
    dwell = max(min(min(spans), dwell_max_us), dwell_min_us)
    return tops.TemporalOperator(
        kind=tops.STUTTER, label=label,
        hard_min_us=total, hard_max_us=total, preferred_us=total,
        repeats_min=len(attack_us), repeats_max=len(attack_us),
        dwell_min_us=dwell, dwell_max_us=dwell,
        peak_ratio=0.0, anchor_kind="STUTTER_ATTACK", capability=capability,
        purpose="MUSICAL_PUNCTUATION",
        notes=(f"{len(attack_us)} held frames across {total/1000:.0f} ms, "
               f"spacing {[s//1000 for s in spans]} ms: the figure sets the "
               f"duration"))


def gesture_anchors(label: str, attack_us: Sequence[int],
                    tolerance_us: int = 20_000) -> tuple[tops.AnchorConstraint, ...]:
    """One constraint per attack, each wanting the attack itself (no hero
    bias -- a held frame reads where it lands)."""
    return tuple(tops.AnchorConstraint(f"{label}#{i+1}", t, "STUTTER_ATTACK",
                                       tolerance_us, required=True)
                 for i, t in enumerate(attack_us))
