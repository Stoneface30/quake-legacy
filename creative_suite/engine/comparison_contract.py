"""One experiment, one variable. Above all: stop changing the volume.

A timing A/B/C whose members also differ in gain is not a timing test. The
louder one wins for reasons that have nothing to do with where the beat sat,
and the conclusion is unrecoverable afterwards because the contamination is
baked into the files. The previous LG comparison level-matched its variants;
that made it a mix test wearing a timing test's name.

So every comparison declares its EXPERIMENT_VARIABLE, and everything else
must be byte-identical in intent. `check` reads the members' manifests and
reports:

    COMPARISON_MIX_DRIFT        ERROR  levels differ and MIX is not the variable
    COMPARISON_MULTI_VARIABLE   ERROR  something else moved too
    COMPARISON_VARIABLE_STATIC  ERROR  the declared variable never changed

Loudness is MEASURED and REPORTED. It is not adjusted. Measuring is how you
learn the timing shift also changed the level; adjusting is how you destroy
the experiment.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Sequence

from creative_suite.engine.review_manifest import ReviewManifest

MUSIC_OFFSET = "MUSIC_OFFSET"
MUSIC_TRACK = "MUSIC_TRACK"
SLOW_RATE = "SLOW_RATE"
CAMERA_MODE = "CAMERA_MODE"
EFFECT_TIMING = "EFFECT_TIMING"
MIX = "MIX"
EXPERIMENT_VARIABLES = (MUSIC_OFFSET, MUSIC_TRACK, SLOW_RATE, CAMERA_MODE,
                        EFFECT_TIMING, MIX)

COMPARISON_MIX_DRIFT = "COMPARISON_MIX_DRIFT"
COMPARISON_MULTI_VARIABLE = "COMPARISON_MULTI_VARIABLE"
COMPARISON_VARIABLE_STATIC = "COMPARISON_VARIABLE_STATIC"

# Manifest fields that each experiment is ALLOWED to move.
VARIABLE_FIELDS: dict[str, tuple[str, ...]] = {
    MUSIC_OFFSET: ("music_source_start_us", "music_source_end_us"),
    MUSIC_TRACK: ("music_track_sha256", "music_source_start_us",
                  "music_source_end_us"),
    SLOW_RATE: ("requested_rate", "timemap_hash"),
    CAMERA_MODE: ("camera_compilation", "visual_capture_key",
                  "preview_assembly_key"),
    EFFECT_TIMING: ("timemap_hash",),
    MIX: ("music_gain_db", "game_gain", "limiter_ceiling", "mix_trim",
          "mix_state"),
}

# Level-deciding fields. Frozen unless MIX is the experiment.
MIX_FIELDS = ("music_gain_db", "game_gain", "limiter_ceiling", "mix_trim",
              "codec")

# Fields that must never differ inside one comparison, whatever the variable.
ALWAYS_IDENTICAL = ("frag_id", "scene_start_us", "scene_end_us",
                    "hero_event_kind", "hero_event_edit_us")


@dataclass(frozen=True)
class ComparisonFinding:
    check: str
    severity: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Comparison:
    """A set of review artifacts that differ in exactly one declared way."""
    name: str
    experiment_variable: str
    members: tuple[ReviewManifest, ...]

    def __post_init__(self) -> None:
        if self.experiment_variable not in EXPERIMENT_VARIABLES:
            raise ValueError(
                f"unknown experiment variable {self.experiment_variable!r}")
        if len(self.members) < 2:
            raise ValueError("a comparison needs at least two members")

    def check(self) -> list[ComparisonFinding]:
        out: list[ComparisonFinding] = []
        allowed = set(VARIABLE_FIELDS[self.experiment_variable])

        # 1. Levels must be frozen unless mixing IS the experiment.
        if self.experiment_variable != MIX:
            for fld in MIX_FIELDS:
                values = {getattr(m, fld) for m in self.members}
                if len(values) > 1:
                    out.append(ComparisonFinding(
                        COMPARISON_MIX_DRIFT, "ERROR",
                        f"{fld} differs across the comparison "
                        f"({sorted(map(str, values))}) while the experiment "
                        f"variable is {self.experiment_variable}: a level "
                        f"difference invalidates a timing result"))

        # 2. Nothing else may move.
        for fld in ReviewManifest.__dataclass_fields__:
            if fld in ("artifact", "variant_name", "output_sha256",
                       "matcher_recommendation", "user_correction"):
                continue
            if fld in allowed or fld in MIX_FIELDS:
                continue
            values = {str(getattr(m, fld)) for m in self.members}
            if len(values) > 1:
                out.append(ComparisonFinding(
                    COMPARISON_MULTI_VARIABLE, "ERROR",
                    f"{fld} differs but is not part of a "
                    f"{self.experiment_variable} experiment"))

        # 3. The declared variable must actually vary, or nothing is compared.
        if not any(len({str(getattr(m, f)) for m in self.members}) > 1
                   for f in allowed):
            out.append(ComparisonFinding(
                COMPARISON_VARIABLE_STATIC, "ERROR",
                f"no member differs in {self.experiment_variable}"))

        # 4. Invariants that hold for every experiment.
        for fld in ALWAYS_IDENTICAL:
            if len({str(getattr(m, fld)) for m in self.members}) > 1:
                out.append(ComparisonFinding(
                    COMPARISON_MULTI_VARIABLE, "ERROR",
                    f"{fld} must be identical across any comparison"))
        return out

    @property
    def valid(self) -> bool:
        return not any(f.severity == "ERROR" for f in self.check())

    def raise_if_invalid(self) -> None:
        errors = [f for f in self.check() if f.severity == "ERROR"]
        if errors:
            raise ComparisonContractError(
                f"{self.name}: " + "; ".join(f.detail for f in errors))

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name,
                "experiment_variable": self.experiment_variable,
                "members": [m.variant_name for m in self.members],
                "valid": self.valid,
                "findings": [f.to_dict() for f in self.check()],
                "frozen_mix": {f: getattr(self.members[0], f)
                               for f in MIX_FIELDS}}


class ComparisonContractError(RuntimeError):
    pass


def measured_levels(report_rows: Sequence[tuple[str, float, float]]
                    ) -> dict[str, Any]:
    """Record LUFS and true peak per member. Reporting only.

    Deliberately returns no correction and no target: there is nothing here
    to feed back into a mix, because for a timing experiment the levels are
    an observation, not a knob.
    """
    return {"members": [{"variant": n, "lufs": i, "dbtp": tp}
                        for n, i, tp in report_rows],
            "note": "levels are measured and reported, never adjusted"}
