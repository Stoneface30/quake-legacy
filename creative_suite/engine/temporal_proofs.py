"""Five planning-only proofs that effects are how the picture fits the song.

Each returns the operators, the fixed slot, the musical anchors, and the
solved composition with its numbers: raw source, time added, time removed,
final duration, and every residual measured on the finished thing.

Nothing here renders and nothing is consumed.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from creative_suite.engine import temporal_operators as t
from creative_suite.engine import temporal_solver as ts

PROOFS_VERSION = "temporal-proofs-v1.0.0"
MS = 1000


# 1 ── the double air rocket ────────────────────────────────────────────────

def double_air_rocket() -> ts.SolveReport:
    """2.9 s of raw source becomes an exact 5.85 s sequence.

    First-person original, a held breath, a slowed side replay, a morph, and
    a transition that overlaps into the next scene. The replay's own peak is
    what has to land on the music, because by then it is the payoff the
    viewer is watching.
    """
    ops = [
        t.TemporalOperator(
            t.RETIME, "fpv", 1_800 * MS, 2_300 * MS,
            preferred_min_us=1_950 * MS, preferred_max_us=2_200 * MS,
            src_in_us=0, src_out_us=2_150 * MS,
            rate_min=Fraction(1, 2), rate_max=Fraction(3, 2),
            peak_ratio=0.81, anchor_kind="HERO", capability="PROVEN_RUNTIME",
            purpose="REVEAL_SKILL", notes="the original skill, first"),
        t.TemporalOperator(
            t.FREEZE, "freeze", 100 * MS, 500 * MS,
            preferred_min_us=200 * MS, preferred_max_us=350 * MS,
            anchor_kind="FREEZE_RELEASE", capability="PROVEN_RUNTIME",
            purpose="BUILD_TENSION",
            temporal_purpose="HOLD_INTO_THE_PHRASE",
            notes="a freeze spends real song time, deliberately"),
        t.TemporalOperator(
            t.REPLAY, "side_replay", 2_045 * MS, 3_750 * MS,
            preferred_min_us=2_500 * MS, preferred_max_us=3_040 * MS,
            src_in_us=1_025 * MS, src_out_us=2_150 * MS,
            rate_min=Fraction(3, 10), rate_max=Fraction(55, 100),
            peak_ratio=0.62, anchor_kind="HERO", capability="PROTOTYPE",
            purpose="REVEAL_SKILL",
            notes="1.125 s of source at 0.30-0.55x: the rate is a variable"),
        t.TemporalOperator(
            t.SYNTHETIC_INSERT, "morph", 250 * MS, 800 * MS,
            preferred_min_us=350 * MS, preferred_max_us=600 * MS,
            peak_ratio=0.65, anchor_kind="MORPH_PEAK", capability="DESIGNABLE",
            purpose="TRANSITION", notes="authored, so its duration is free"),
        t.TemporalOperator(
            t.OVERLAP, "transition_overlap", 0, 500 * MS,
            preferred_min_us=150 * MS, preferred_max_us=300 * MS,
            anchor_kind="TRANSITION_HANDOFF", capability="PROVEN_RUNTIME",
            purpose="TRANSITION",
            notes="the only operator here that REMOVES net sequence time"),
    ]
    anchors = (t.AnchorConstraint("side_replay", 4_540 * MS, "HERO", 40 * MS),)
    return ts.solve("DOUBLE_AIR_ROCKET", 5_850 * MS, ops, anchors=anchors, top=3)


# 2 ── stutter whose duration the music decides ─────────────────────────────

GESTURE_ATTACKS = (0, 180 * MS, 360 * MS, 540 * MS)


def rhythmic_stutter() -> ts.SolveReport:
    """The figure sets the effect's length, not the other way round.

    Four attacks 180 ms apart. The stutter spans the figure and releases at
    the next accent, so its duration is derived: 720 ms, no choice involved.
    The surrounding material flexes around it.
    """
    stutter = ts.stutter_from_gesture("stutter", GESTURE_ATTACKS,
                                      release_us=720 * MS)
    ops = [
        t.TemporalOperator(
            t.RETIME, "run_in", 600 * MS, 1_600 * MS,
            preferred_min_us=800 * MS, preferred_max_us=1_200 * MS,
            src_in_us=0, src_out_us=1_000 * MS,
            rate_min=Fraction(1, 2), rate_max=Fraction(2, 1),
            peak_ratio=1.0, anchor_kind="CAMERA_CUT",
            capability="PROVEN_RUNTIME", purpose="BUILD_TENSION"),
        stutter,
        t.TemporalOperator(
            t.RETIME, "run_out", 400 * MS, 1_400 * MS,
            preferred_min_us=600 * MS, preferred_max_us=1_000 * MS,
            src_in_us=1_000 * MS, src_out_us=1_800 * MS,
            rate_min=Fraction(1, 2), rate_max=Fraction(2, 1),
            peak_ratio=0.0, anchor_kind="CAMERA_CUT",
            capability="PROVEN_RUNTIME", purpose="TRANSITION"),
    ]
    return ts.solve("RHYTHMIC_IMAGE_STUTTER", 2_600 * MS, ops, top=3)


# 3 ── freeze, go, frag ─────────────────────────────────────────────────────

def freeze_go_frag() -> ts.SolveReport:
    """The freeze's length is chosen so that what follows lands right.

    A hold before the commit, release on the beat, and the frag itself
    arriving 15 ms before its transient because that is what reads as
    together.
    """
    ops = [
        t.TemporalOperator(
            t.RETIME, "approach", 900 * MS, 1_800 * MS,
            preferred_min_us=1_000 * MS, preferred_max_us=1_500 * MS,
            src_in_us=0, src_out_us=1_400 * MS,
            rate_min=Fraction(1, 2), rate_max=Fraction(3, 2),
            peak_ratio=1.0, anchor_kind="CAMERA_CUT",
            capability="PROVEN_RUNTIME", purpose="BUILD_TENSION"),
        t.TemporalOperator(
            t.FREEZE, "hold", 120 * MS, 900 * MS,
            preferred_min_us=250 * MS, preferred_max_us=600 * MS,
            peak_ratio=1.0, anchor_kind="FREEZE_RELEASE",
            capability="PROVEN_RUNTIME", purpose="BUILD_TENSION",
            temporal_purpose="RELEASE_ON_THE_BEAT"),
        t.TemporalOperator(
            t.RETIME, "commit_and_frag", 1_200 * MS, 2_600 * MS,
            preferred_min_us=1_400 * MS, preferred_max_us=2_100 * MS,
            src_in_us=1_400 * MS, src_out_us=3_100 * MS,
            rate_min=Fraction(2, 5), rate_max=Fraction(3, 2),
            peak_ratio=0.78, anchor_kind="HERO",
            capability="PROVEN_RUNTIME", purpose="REVEAL_SKILL"),
    ]
    # Reachable by construction: with the slot fixed at 4.0 s the frag's peak
    # can only fall between 3.428 s and 3.736 s, so an anchor outside that is
    # not a target, it is a refusal waiting to happen.
    anchors = (
        t.AnchorConstraint("hold", 1_750 * MS, "FREEZE_RELEASE", 30 * MS),
        t.AnchorConstraint("commit_and_frag", 3_490 * MS, "HERO", 25 * MS),
    )
    return ts.solve("FREEZE_GO_FRAG", 4_000 * MS, ops, anchors=anchors, top=3)


# 4 ── hero, death, flashes, rewind, replay ─────────────────────────────────

def hero_then_death_rewind() -> ts.SolveReport:
    """A whole musical phrase built out of a death that would have been a
    failure. Flashes, a rewind and a clean replay each spend real time; the
    number of flashes comes from the rhythm."""
    ops = [
        t.TemporalOperator(
            t.RETIME, "hero_action", 1_400 * MS, 2_400 * MS,
            preferred_min_us=1_600 * MS, preferred_max_us=2_100 * MS,
            src_in_us=0, src_out_us=2_000 * MS,
            rate_min=Fraction(1, 2), rate_max=Fraction(3, 2),
            peak_ratio=0.85, anchor_kind="HERO",
            capability="PROVEN_RUNTIME", purpose="REVEAL_SKILL"),
        t.TemporalOperator(
            t.FREEZE, "death_freeze", 150 * MS, 600 * MS,
            preferred_min_us=200 * MS, preferred_max_us=400 * MS,
            anchor_kind="FREEZE_RELEASE", capability="PROVEN_RUNTIME",
            purpose="TRANSITION"),
        t.TemporalOperator(
            t.REPEAT, "death_flashes", 240 * MS, 960 * MS,
            preferred_min_us=320 * MS, preferred_max_us=640 * MS,
            src_in_us=2_000 * MS, src_out_us=2_240 * MS,
            repeats_min=3, repeats_max=12,
            peak_ratio=0.5, anchor_kind="STUTTER_ATTACK",
            capability="PROVEN_RUNTIME", purpose="MUSICAL_PUNCTUATION",
            notes="three to four frames each, counted off the subdivision"),
        t.TemporalOperator(
            t.INSERT, "rewind", 300 * MS, 1_100 * MS,
            preferred_min_us=450 * MS, preferred_max_us=800 * MS,
            peak_ratio=1.0, anchor_kind="TRANSITION_HANDOFF",
            capability="PROTOTYPE", purpose="TRANSITION",
            temporal_purpose="SPAN_TO_THE_NEXT_PHRASE"),
        t.TemporalOperator(
            t.REPLAY, "clean_replay", 1_600 * MS, 3_200 * MS,
            preferred_min_us=1_900 * MS, preferred_max_us=2_700 * MS,
            src_in_us=1_100 * MS, src_out_us=2_000 * MS,
            rate_min=Fraction(28, 100), rate_max=Fraction(56, 100),
            peak_ratio=0.8, anchor_kind="HERO",
            capability="PROTOTYPE", purpose="REVEAL_SKILL"),
    ]
    anchors = (t.AnchorConstraint("clean_replay", 6_665 * MS, "HERO", 40 * MS),)
    return ts.solve("HERO_THEN_DEATH_REWIND", 7_200 * MS, ops, anchors=anchors, top=3)


# 5 ── the overlap that saves the phrase ────────────────────────────────────

def transition_overlap() -> ts.SolveReport:
    """Two scenes that are 150 ms too long together, solved by sharing time
    rather than by speeding either of them up."""
    ops = [
        t.TemporalOperator(
            t.RETIME, "scene_a", 1_900 * MS, 2_100 * MS,
            preferred_min_us=1_980 * MS, preferred_max_us=2_020 * MS,
            src_in_us=0, src_out_us=2_000 * MS,
            rate_min=Fraction(9, 10), rate_max=Fraction(11, 10),
            rate_preferred=Fraction(1, 1),
            peak_ratio=0.5, anchor_kind="CAMERA_CUT",
            capability="PROVEN_RUNTIME", purpose="TRANSITION"),
        t.TemporalOperator(
            t.RETIME, "scene_b", 1_900 * MS, 2_100 * MS,
            preferred_min_us=1_980 * MS, preferred_max_us=2_020 * MS,
            src_in_us=0, src_out_us=2_000 * MS,
            rate_min=Fraction(9, 10), rate_max=Fraction(11, 10),
            rate_preferred=Fraction(1, 1),
            peak_ratio=0.5, anchor_kind="CAMERA_CUT",
            capability="PROVEN_RUNTIME", purpose="TRANSITION"),
        t.TemporalOperator(
            t.OVERLAP, "overlap", 0, 400 * MS,
            preferred_min_us=100 * MS, preferred_max_us=300 * MS,
            anchor_kind="TRANSITION_HANDOFF", capability="PROVEN_RUNTIME",
            purpose="TRANSITION",
            temporal_purpose="RECOVER_150MS_WITHOUT_ACCELERATING"),
    ]
    return ts.solve("TRANSITION_OVERLAP", 3_850 * MS, ops, top=3)


PROOFS = (double_air_rocket, rhythmic_stutter, freeze_go_frag,
          hero_then_death_rewind, transition_overlap)


def all_reports() -> tuple[ts.SolveReport, ...]:
    return tuple(f() for f in PROOFS)


def summary() -> dict[str, Any]:
    """The numbers, for a report or a test."""
    out = []
    for rep in all_reports():
        best = rep.best
        row: dict[str, Any] = {
            "slot": rep.slot_id, "slot_ms": rep.slot_us // MS,
            "feasible": rep.feasible,
            "elasticity_ms": [rep.elasticity.min_us // MS, rep.elasticity.max_us // MS],
            "compositions": rep.considered,
        }
        if best:
            d = best.plan.to_dict()
            row.update({
                "hero_delta_ms": (None if best.objective.hero_delta_us == 0
                                  else round(best.objective.hero_delta_us / 1000, 1)),
                "hero_direction": best.objective.hero_direction,
                "raw_source_ms": d["source_us"] // MS,
                "final_ms": d["total_us"] // MS,
                "exact": d["exact"],
                "added_ms": {k: v // MS for k, v in d["added_us"].items()},
                "removed_ms": {k: v // MS for k, v in d["removed_us"].items()},
                "anchors": [{"event": a["event"], "kind": a["kind"],
                             "delta_ms": None if a.get("delta_us") is None
                             else round(a["delta_us"] / 1000, 1),
                             "residual_ms": None if a["residual_us"] is None
                             else round(a["residual_us"] / 1000, 1),
                             "direction": a.get("direction"),
                             "satisfied": a["satisfied"]} for a in d["anchors"]],
                "preferred_deviation": d["deviation"],
                "rates": {c["label"]: c["rate"] for c in d["choices"] if c["rate"]},
            })
        out.append(row)
    return {"version": PROOFS_VERSION, "proofs": out}
