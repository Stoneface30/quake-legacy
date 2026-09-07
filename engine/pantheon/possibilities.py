"""WHAT COULD WE DO WITH THIS MOMENT, AND WHY DO WE THINK SO.

Given one indexed moment, this says which pieces of the film grammar it can
carry -- and cites the fact behind every answer. It renders nothing, launches
nothing and decides nothing: a compatibility is DERIVED from evidence, a
recommendation is a MACHINE_SUGGESTION, and the choice is HUMAN. Those three
never merge, because a machine's preference dressed as a fact is how a
reviewer stops reading the reasons.

An answer of "no" is as useful as a yes when it names what is missing: the
truth the demo does not contain, or the capability no backend has proven.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum

from engine.pantheon import effect_recipes as ER
from engine.pantheon import performance_index as PI


class Provenance(str, Enum):
    DERIVED = "DERIVED"                    # follows from evidence
    MACHINE_SUGGESTION = "MACHINE_SUGGESTION"   # a preference, not a fact
    HUMAN = "HUMAN"                        # the director said so


@dataclass
class Fact:
    """One piece of evidence, in the form the reviewer can check."""
    name: str
    value: object
    source: str

    def as_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "source": self.source}


@dataclass
class Possibility:
    recipe: str
    compatible: bool
    status: str
    reasons: tuple[str, ...] = ()
    missing_truth: tuple[str, ...] = ()
    missing_capabilities: tuple[str, ...] = ()
    provenance: Provenance = Provenance.DERIVED

    def as_dict(self) -> dict:
        return {"recipe": self.recipe, "compatible": self.compatible,
                "status": self.status, "reasons": list(self.reasons),
                "missing_truth": list(self.missing_truth),
                "missing_capabilities": list(self.missing_capabilities),
                "provenance": self.provenance.value}


@dataclass
class MomentPossibilities:
    performance_id: str
    facts: list[Fact] = field(default_factory=list)
    truth_available: tuple[str, ...] = ()
    possibilities: list[Possibility] = field(default_factory=list)
    suggestions: list[dict] = field(default_factory=list)

    @property
    def compatible(self) -> list[Possibility]:
        return [p for p in self.possibilities if p.compatible]

    def as_dict(self) -> dict:
        return {"performance_id": self.performance_id,
                "facts": [f.as_dict() for f in self.facts],
                "truth_available": list(self.truth_available),
                "possibilities": [p.as_dict() for p in self.possibilities],
                "suggestions": self.suggestions}


# -- what the evidence supports --------------------------------------------

_ROW_COLUMNS = ("performance_id", "demo_hash", "client", "is_pov", "kind", "t_ms",
                "start_ms", "end_ms", "weapon", "map", "outcome", "outcome_ms",
                "victim", "samples", "gap_ms", "airborne_ms", "distance_u",
                "projectile_n", "projectile_samples", "projectile_weapon",
                "events_json", "max_speed")


def moment(performance_id: str) -> dict | None:
    """The indexed row, plus what its demo says about the cast."""
    con = PI._ro()
    row = con.execute(
        f"select {', '.join(_ROW_COLUMNS)} from actions where performance_id = ?",
        (performance_id,)).fetchone()
    if row is None:
        return None
    got = dict(zip(_ROW_COLUMNS, row))
    d = con.execute("select clients, recorder_client, gametype, seconds, path "
                    "from demos where demo_hash = ?", (got["demo_hash"],)).fetchone()
    if d:
        got.update(zip(("clients", "recorder_client", "gametype",
                        "demo_seconds", "demo_path"), d))
    return got


def facts_for(m: dict) -> list[Fact]:
    """Only what the row actually holds. Nothing inferred, nothing rounded."""
    src = "performance index row"
    out = [
        Fact("kind", m["kind"], src),
        Fact("map", m["map"], src),
        Fact("server_time_ms", m["t_ms"], src),
        Fact("window_ms", [m["start_ms"], m["end_ms"]], src),
        Fact("is_recorder_pov", bool(m["is_pov"]), src),
        Fact("transform_samples", m["samples"], src),
        Fact("largest_observation_gap_ms", m["gap_ms"], src),
    ]
    if m.get("weapon"):
        out.append(Fact("weapon", m["weapon"], src))
    if m.get("outcome"):
        out.append(Fact("outcome", m["outcome"], src))
    if m.get("victim") is not None:
        out.append(Fact("victim_client_slot", m["victim"], src))
    if m.get("projectile_samples"):
        out.append(Fact("observed_projectile_samples", m["projectile_samples"], src))
        out.append(Fact("projectile_weapon", m.get("projectile_weapon"), src))
    if m.get("airborne_ms"):
        out.append(Fact("airborne_ms", m["airborne_ms"], src))
    if m.get("max_speed") is not None:
        out.append(Fact("max_speed_ups", round(float(m["max_speed"] or 0), 1), src))
    if m.get("clients") is not None:
        out.append(Fact("clients_in_demo", m["clients"], "demos table"))
    events = json.loads(m.get("events_json") or "[]")
    if events:
        out.append(Fact("event_chain", [e[1] for e in events][:12], src))
    return out


def truth_for(m: dict) -> tuple[set[str], dict[str, str]]:
    """Which named truths this moment can supply, and why each one holds.

    Absence is a real answer. A moment on a map with no learned geography does
    not get MAP_GEOGRAPHY just because the map has a name.
    """
    from engine.pantheon import geography as GEO

    have: set[str] = set()
    why: dict[str, str] = {}

    def add(name: str, reason: str) -> None:
        have.add(name)
        why[name] = reason

    if m.get("samples"):
        add("TRANSFORM", f"{m['samples']} observed transform samples")
        add("AIM", "aim travels with the transform track")
    if m.get("events_json") and json.loads(m["events_json"]):
        add("EVENTS", "the recorded event chain is on the row")
    if m.get("kind"):
        add("ACTION", f"the index read this as {m['kind']}")
    if m.get("projectile_samples"):
        add("PROJECTILE_PATH",
            f"{m['projectile_samples']} OBSERVED missile samples, not extended")
    if m.get("weapon") or m["kind"].startswith("FIRE_"):
        add("WEAPON_STATE", "the weapon is on the row")
    # Another POV exists only if the demo observed more than the recorder.
    clients = m.get("clients") or 0
    if clients > 1:
        add("OTHER_POV", f"the demo carries {clients} clients")
        if m.get("victim") is not None and m["victim"] != m.get("recorder_client"):
            add("ENEMY_POV", f"the victim is client slot {m['victim']}, "
                             f"not the recorder")
    try:
        if m.get("map") and GEO.coverage(m["map"]):
            add("MAP_GEOGRAPHY", f"{m['map']} has a learned geography")
    except Exception:
        pass
    return have, why


# Truths the index alone cannot answer. Named so a "no" is honest about being
# "not from here" rather than "not in the demo".
NEEDS_ANOTHER_SOURCE = {
    "ROUND": "the round is in the review corpus, not the performance index",
    "HEALTH": "health over the window comes from the trace, not the index row",
    "SCOREBOARD": "match state is not carried on an action row",
    "ROSTER": "who performs is chosen at compile time, never recorded",
}


def for_moment(performance_id: str, *, backend: str = "PANTHEON_QUAKE_OFFSCREEN",
               profile: str = "REVIEW") -> MomentPossibilities:
    m = moment(performance_id)
    if m is None:
        raise KeyError(f"no indexed moment {performance_id}")
    facts = facts_for(m)
    have, why = truth_for(m)

    out = MomentPossibilities(performance_id, facts, tuple(sorted(have)))
    for r in ER.RECIPES:
        gap = r.truth_gap(have)
        missing_caps = ER.missing_capabilities(r.id)
        st = ER.status(r.id, backend=backend, profile=profile)
        reasons: list[str] = []
        for t in r.required_truth:
            if t in why:
                reasons.append(f"{t}: {why[t]}")
        for t in gap:
            reasons.append(f"{t} MISSING: " + NEEDS_ANOTHER_SOURCE.get(
                t, "this moment does not carry it"))
        if missing_caps:
            reasons.append("no proven backend for " + ", ".join(missing_caps))
        out.possibilities.append(Possibility(
            recipe=r.id, compatible=not gap and not missing_caps,
            status=st.value, reasons=tuple(reasons), missing_truth=gap,
            missing_capabilities=missing_caps))

    out.suggestions = _suggest(m, have)
    return out


def _suggest(m: dict, have: set[str]) -> list[dict]:
    """A preference, labelled as one. Every entry says what about the moment
    prompted it, so a reviewer can disagree with the reason rather than the
    machine."""
    s: list[dict] = []

    def say(recipe: str, because: str) -> None:
        s.append({"recipe": recipe, "because": because,
                  "provenance": Provenance.MACHINE_SUGGESTION.value})

    if m.get("projectile_samples", 0) and (m.get("projectile_samples") or 0) >= 6:
        say("PROJECTILE_FOLLOW",
            f"{m['projectile_samples']} observed missile samples: the flight "
            f"is long enough to ride")
    if (m.get("airborne_ms") or 0) >= 600:
        say("HIGH_SPEED_RETIME",
            f"{m['airborne_ms']} ms airborne: there is a hang to stretch")
    if m.get("outcome") == "KILL" and "ENEMY_POV" in have:
        say("ENEMY_POV_REPLAY",
            "the victim is a different client the demo observed")
    if (m.get("clients") or 0) >= 8 and m.get("outcome") == "KILL":
        say("XRAY_ACTOR",
            f"{m['clients']} players: bodies are likely hidden from the camera")
    if (m.get("gap_ms") or 0) > 300:
        s.append({"recipe": None,
                  "because": f"a {m['gap_ms']} ms observation gap sits in this "
                             f"window; anything that follows a body across it "
                             f"would be inventing the middle",
                  "provenance": Provenance.MACHINE_SUGGESTION.value})
    return s


def main() -> int:                                           # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description="what could we do with this moment")
    ap.add_argument("performance_id")
    a = ap.parse_args()
    print(json.dumps(for_moment(a.performance_id).as_dict(), indent=1))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
